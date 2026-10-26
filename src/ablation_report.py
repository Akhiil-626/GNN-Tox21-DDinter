"""
Aggregation and honest reporting for the DDI ablation study.

Everything here is pure pandas / numpy / scipy / matplotlib (no torch), so the
statistics and the wording rules can be unit tested without GPUs or data.

Input "runs" DataFrame, one row per (seed, model, scenario):
    seed, model, scenario, n, accuracy, macro_f1, minor_f1, moderate_f1, major_f1

The verdict wording is rule-based on purpose: the report cannot say "improves"
unless the numbers support it, which keeps the novelty claim honest.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

METRICS = ['accuracy', 'macro_f1', 'minor_f1', 'moderate_f1', 'major_f1']
SCENARIOS = ['S0', 'S1', 'S2']
MIN_SEEDS_FOR_CLAIM = 5

MODEL_DESCRIPTIONS = {
    'Prior': 'Always predicts the most common severity (floor)',
    'DrugMean': "Per-drug average severity, no chemistry (tests 'is this drug just dangerous?')",
    'FPForest': 'Morgan-fingerprint random forest on symmetric pair features',
    'RF_fp': 'Fast tabular ablation: fingerprint forest (no toxicity features)',
    'RF_fp+tox': 'Fast tabular ablation: fingerprint forest + predicted Tox21 risk-fingerprint features',
    'RF_fp+toxshuf': 'CONTROL: fingerprint forest + risk profiles shuffled across drugs',
    'RF_fp+ov': 'Fingerprint forest + only the 4 scalar overlap features (dilution check)',
    'RF_tox': 'Forest on predicted Tox21 pair features ALONE (how much signal do they carry by themselves?)',
    'RF_fp+cyp': 'Fast tabular ablation: fingerprint forest + predicted CYP features',
    'A': 'GNN, structure only (order-independent head)',
    'B': 'A + predicted Tox21 risk-fingerprint features',
    'B_shuf': 'CONTROL: B with risk profiles shuffled across drugs (same capacity, no information)',
    'C': 'A + predicted CYP-inhibition features',
    'D': 'A + Tox21 + CYP features',
}


def summarize(runs: pd.DataFrame) -> pd.DataFrame:
    """Mean, std (ddof=1, 0 when a single seed) and seed count per (model, scenario)."""
    rows = []
    for (model, scen), g in runs.groupby(['model', 'scenario'], sort=False):
        row = {'model': model, 'scenario': scen, 'n_seeds': int(g['seed'].nunique()),
               'n_test_pairs': float(g['n'].mean())}
        for m in METRICS:
            vals = g[m].to_numpy(dtype=float)
            row[f'{m}_mean'] = float(np.nanmean(vals)) if len(vals) else float('nan')
            row[f'{m}_std'] = float(np.nanstd(vals, ddof=1)) if len(vals) > 1 else 0.0
        rows.append(row)
    return pd.DataFrame(rows)


def paired_comparison(runs: pd.DataFrame, model_x: str, model_y: str,
                      metric: str = 'macro_f1') -> pd.DataFrame:
    """
    Per scenario, compare model_x against model_y on the SAME seeds (same splits).
    mean_diff = mean(x - y); wins = seeds where x > y; p_value from a Wilcoxon
    signed-rank test (NaN when fewer than 6 paired seeds -- too few for an exact test
    to ever reach p < 0.05 -- or when all differences are zero).
    """
    from scipy.stats import wilcoxon
    out = []
    for scen in SCENARIOS:
        x = runs[(runs['model'] == model_x) & (runs['scenario'] == scen)].set_index('seed')[metric]
        y = runs[(runs['model'] == model_y) & (runs['scenario'] == scen)].set_index('seed')[metric]
        seeds = sorted(set(x.index) & set(y.index))
        if not seeds:
            continue
        d = np.array([x[s] - y[s] for s in seeds], dtype=float)
        p = float('nan')
        if len(d) >= 6 and np.any(d != 0):
            try:
                p = float(wilcoxon(d).pvalue)
            except ValueError:
                p = float('nan')
        out.append({
            'scenario': scen, 'x': model_x, 'y': model_y, 'metric': metric, 'n_seeds': len(d),
            'mean_diff': float(d.mean()), 'std_diff': float(d.std(ddof=1)) if len(d) > 1 else 0.0,
            'wins': int((d > 0).sum()), 'p_value': p,
        })
    return pd.DataFrame(out)


def verdict(row: pd.Series) -> str:
    """Rule-based wording for one paired-comparison row. Never claims more than the data show."""
    n, md = int(row['n_seeds']), float(row['mean_diff'])
    p = row['p_value']
    name = f"{row['x']} vs {row['y']} on {row['scenario']} ({row['metric']})"
    if n < MIN_SEEDS_FOR_CLAIM:
        return (f"{name}: {md:+.3f} over {n} seed(s) -- INCONCLUSIVE "
                f"(need >= {MIN_SEEDS_FOR_CLAIM} seeds before claiming anything).")
    if np.isnan(p):
        return f"{name}: {md:+.3f}, wins {int(row['wins'])}/{n} -- no reliable difference (test not applicable)."
    if p < 0.05 and md > 0:
        return f"{name}: {md:+.3f}, wins {int(row['wins'])}/{n}, p={p:.3f} -- {row['x']} IMPROVES on {row['y']}."
    if p < 0.05 and md < 0:
        return f"{name}: {md:+.3f}, wins {int(row['wins'])}/{n}, p={p:.3f} -- {row['x']} is WORSE than {row['y']}."
    return f"{name}: {md:+.3f}, wins {int(row['wins'])}/{n}, p={p:.3f} -- no reliable difference."


def key_comparisons(runs: pd.DataFrame) -> pd.DataFrame:
    """The comparisons the project's claims depend on (only those whose models are present)."""
    models = set(runs['model'])
    pairs = [('B', 'A'), ('B', 'B_shuf'), ('C', 'A'), ('D', 'A'), ('D', 'B'),
             ('A', 'DrugMean'), ('A', 'FPForest'), ('B', 'DrugMean'),
             ('RF_fp+tox', 'RF_fp'), ('RF_fp+tox', 'RF_fp+toxshuf'), ('RF_fp+cyp', 'RF_fp'),
             ('RF_fp', 'DrugMean'), ('RF_fp+ov', 'RF_fp'), ('RF_fp', 'RF_tox'), ('RF_tox', 'DrugMean'),
             ('RF_fp', 'Prior'), ('DrugMean', 'Prior')]
    frames = [paired_comparison(runs, x, y) for x, y in pairs if x in models and y in models]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


HEADLINE_PAIRS = [('B', 'A', 'B_shuf'), ('RF_fp+tox', 'RF_fp', 'RF_fp+toxshuf')]


def headline_claim(runs: pd.DataFrame) -> pd.DataFrame:
    """
    Strict check of the project's headline claim, per scenario and model family:

        "Predicted-toxicity features help"  is SUPPORTED only if the model with the
        features beats BOTH the same model without them AND the shuffled-profile control,
        each with a reliable paired improvement (see verdict()).

    Requiring the conjunction means a gain that merely reflects extra input capacity
    (the shuffled control also gains) can never be reported as support.
    Returns columns: family, scenario, status, detail.
    """
    models = set(runs['model'])
    rows = []
    for full, base, shuf in HEADLINE_PAIRS:
        if not {full, base, shuf} <= models:
            continue
        vs_base = paired_comparison(runs, full, base).set_index('scenario')
        vs_shuf = paired_comparison(runs, full, shuf).set_index('scenario')
        for scen in SCENARIOS:
            if scen not in vs_base.index or scen not in vs_shuf.index:
                continue
            v1, v2 = verdict(_row(vs_base, scen)), verdict(_row(vs_shuf, scen))
            ok = ('IMPROVES' in v1) and ('IMPROVES' in v2)
            inconclusive = ('INCONCLUSIVE' in v1) or ('INCONCLUSIVE' in v2)
            status = 'SUPPORTED' if ok else ('INCONCLUSIVE' if inconclusive else 'NOT SUPPORTED')
            rows.append({'family': f'{full} vs {base} and {shuf}', 'scenario': scen, 'status': status,
                         'detail': f'vs no-features: {vs_base.loc[scen, "mean_diff"]:+.3f} '
                                   f'(p={vs_base.loc[scen, "p_value"]:.3f}); '
                                   f'vs shuffled control: {vs_shuf.loc[scen, "mean_diff"]:+.3f} '
                                   f'(p={vs_shuf.loc[scen, "p_value"]:.3f})'})
    return pd.DataFrame(rows)


def _row(comp_indexed: pd.DataFrame, scen: str) -> pd.Series:
    """Rebuild a full verdict()-ready row from a comparison table indexed by scenario."""
    r = comp_indexed.loc[scen].copy()
    r['scenario'] = scen
    return r


def _fmt(mean: float, std: float) -> str:
    return f"{mean:.3f} ± {std:.3f}"


def render_report(runs: pd.DataFrame, meta: Dict[str, object],
                  overlap_corr: Optional[pd.DataFrame] = None,
                  conformal: Optional[pd.DataFrame] = None) -> str:
    """Markdown report. `meta` carries run settings and warnings (e.g. leaky profiler mode)."""
    summ = summarize(runs)
    comp = key_comparisons(runs)
    lines: List[str] = ['# DDI severity ablation report', '']

    lines += ['## Setup', '']
    for k, v in meta.items():
        lines.append(f'- **{k}**: {v}')
    lines.append('')
    if meta.get('profiler_mode') == 'single_model_leaky':
        lines += [
            '> **WARNING - possible feature leakage.** Risk profiles came from a single Tox21 model. '
            'Drugs that also appear in Tox21 were seen during that model\'s training, so their profiles '
            'are unrealistically accurate. Re-run after `python -m src.crossfit --task tox21` for honest numbers.',
            '',
        ]

    lines += ['## Models', '']
    for m in summ['model'].unique():
        lines.append(f"- **{m}** - {MODEL_DESCRIPTIONS.get(m, '')}")
    lines.append('')

    lines += ['## Results (mean ± std across seeds)', '']
    for scen in SCENARIOS:
        sub = summ[summ['scenario'] == scen]
        if sub.empty:
            continue
        n_pairs = int(sub['n_test_pairs'].iloc[0])
        desc = {'S0': 'both drugs seen in training', 'S1': 'one new drug', 'S2': 'both drugs new'}[scen]
        lines += [f'### {scen}: {desc} (~{n_pairs} test pairs)', '',
                  '| Model | Accuracy | Macro-F1 | Minor F1 | Moderate F1 | Major F1 | Seeds |',
                  '|---|---|---|---|---|---|---|']
        for _, r in sub.iterrows():
            lines.append(
                f"| {r['model']} | {_fmt(r['accuracy_mean'], r['accuracy_std'])} | "
                f"{_fmt(r['macro_f1_mean'], r['macro_f1_std'])} | {_fmt(r['minor_f1_mean'], r['minor_f1_std'])} | "
                f"{_fmt(r['moderate_f1_mean'], r['moderate_f1_std'])} | {_fmt(r['major_f1_mean'], r['major_f1_std'])} | "
                f"{int(r['n_seeds'])} |")
        lines.append('')

    claim = headline_claim(runs)
    lines += ['## Headline claim: do predicted-toxicity features help?', '']
    if claim.empty:
        lines.append('_Not evaluated (needs the with-features, without-features and shuffled-control models)._')
    else:
        lines.append('Supported only if the feature model beats BOTH the no-feature model and the shuffled-profile control.')
        lines.append('')
        for _, r in claim.iterrows():
            lines.append(f"- **{r['scenario']}** - {r['status']} ({r['family']}): {r['detail']}")
    lines.append('')

    lines += ['## Key comparisons (paired by seed, macro-F1)', '']
    if comp.empty:
        lines.append('_No comparable model pairs were run._')
    else:
        for _, r in comp.iterrows():
            lines.append(f'- {verdict(r)}')
    lines.append('')

    if overlap_corr is not None and not overlap_corr.empty:
        rho_col = 'rho_overlap' if 'rho_overlap' in overlap_corr.columns else 'rho'
        has_diag = {'rho_additive', 'rho_partial'} <= set(overlap_corr.columns)
        lines += ['## Does shared predicted risk track severity? (model-free check)', '',
                  'Spearman correlations with true severity. "Additive" = each drug\'s own mean risk summed; '
                  '"partial" = overlap after removing that additive effect.', '']
        if has_diag:
            lines += ['| Scenario | rho (overlap) | rho (additive risk) | rho (overlap, given additive) | n pairs |',
                      '|---|---|---|---|---|']
            for _, r in overlap_corr.iterrows():
                lines.append(f"| {r['scenario']} | {r[rho_col]:.3f} | {r['rho_additive']:.3f} | "
                             f"{r['rho_partial']:.3f} | {int(r['n'])} |")
        else:
            lines += ['| Scenario | rho (overlap) | n pairs |', '|---|---|---|']
            for _, r in overlap_corr.iterrows():
                lines.append(f"| {r['scenario']} | {r[rho_col]:.3f} | {int(r['n'])} |")
        lines += ['', 'p-values are omitted on purpose: pairs share drugs, so standard tests badly overstate significance '
                  'with tens of thousands of pairs. Judge by effect size. If the partial correlation is near zero, '
                  'the overlap score adds nothing beyond how risky each drug is on its own.', '']

    if conformal is not None and not conformal.empty:
        lines += ['## Abstain mode (split-conformal, calibrated on validation drugs)', '',
                  '| Model | Scenario | Target coverage | Coverage | Answer rate | Accuracy when answering | Accuracy if forced to answer all |',
                  '|---|---|---|---|---|---|---|']
        agg = conformal.groupby(['model', 'scenario'], sort=False).mean(numeric_only=True).reset_index()
        for _, r in agg.iterrows():
            lines.append(f"| {r['model']} | {r['scenario']} | {r['target_coverage']:.2f} | {r['coverage']:.3f} | "
                         f"{r['answer_rate']:.3f} | {r['answered_accuracy']:.3f} | {r['baseline_accuracy']:.3f} |")
        lines += ['', 'Coverage can fall below target on S1/S2 because new drugs break the exchangeability assumption.', '']

    lines += ['## How to read this honestly', '',
              f'- Claims need at least {MIN_SEEDS_FOR_CLAIM} seeds; fewer is reported as inconclusive.',
              '- Many comparisons are listed; at p < 0.05 roughly 1 in 20 null comparisons will look significant by '
              'chance. Treat isolated single-scenario wins with suspicion and trust the strict headline rule above.',
              '- B beating A only supports the toxicity-fingerprint idea if B also beats **B_shuf** '
              '(same extra capacity, no real information). The same logic applies to RF_fp+tox versus RF_fp+toxshuf.',
              '- A beating **DrugMean** on S1/S2 is what shows the GNN uses chemistry, not just drug identity.',
              '- Numbers here are not comparable to papers reporting binary interaction detection on balanced '
              'positive/negative pairs; this is 3-class severity among known interactions.', '']
    return '\n'.join(lines)


def plot_summary(summary: pd.DataFrame, path: str) -> None:
    """Grouped bar chart of macro-F1 (mean ± std) by model and scenario."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    models = list(dict.fromkeys(summary['model']))
    scens = [s for s in SCENARIOS if s in set(summary['scenario'])]
    width = 0.8 / max(len(models), 1)
    fig, ax = plt.subplots(figsize=(max(7, 1.6 * len(scens) * len(models) / 2), 4.5))
    for i, m in enumerate(models):
        means, stds = [], []
        for s in scens:
            r = summary[(summary['model'] == m) & (summary['scenario'] == s)]
            means.append(float(r['macro_f1_mean'].iloc[0]) if len(r) else 0.0)
            stds.append(float(r['macro_f1_std'].iloc[0]) if len(r) else 0.0)
        ax.bar(np.arange(len(scens)) + i * width, means, width, yerr=stds, capsize=2, label=m)
    ax.set_xticks(np.arange(len(scens)) + width * (len(models) - 1) / 2)
    ax.set_xticklabels([f'{s}' for s in scens])
    ax.set_ylabel('Macro-F1')
    ax.set_title('DDI severity: macro-F1 by model and scenario')
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
