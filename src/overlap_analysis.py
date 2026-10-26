"""
Does the "shared predicted toxicity" score track DDI severity beyond obvious confounders?

Why this exists
---------------
The ablation found that predicted-toxicity features do not improve severity prediction, but a
small model-free association remained: the expected-shared-risk score correlates weakly with
severity (rho about 0.07-0.13) even after removing each drug's own risk. Before believing or
discarding that lead, rule out the boring explanations. The overlap score could be a proxy for:

  * structural similarity of the two drugs   (similar molecules -> similar profiles AND similar interactions)
  * therapeutic-class closeness              (same-class drugs share profiles and interaction patterns)
  * drug popularity                          (well-studied drugs have many, more severe interactions)
  * each drug's own risk level               (dangerous drugs pairing with dangerous drugs)

Method (no model training; minutes on a CPU)
--------------------------------------------
  1. Partial Spearman correlation of overlap vs severity, controlling for ALL of the above.
  2. Drug-level cluster bootstrap CI: resample DRUGS (not pairs), because pairs share drugs and
     treating them as independent makes intervals far too narrow.
  3. Two permutation nulls (shuffle which drug owns which risk profile, recompute the overlap):
       - GLOBAL: shuffle across all drugs. Destroys every link between structure and profile, so it is
         a weak null: any structure-driven association beats it.
       - STRUCTURE-MATCHED: shuffle only among drugs with similar fingerprints (k-means clusters of
         about 6 drugs). Structure-driven signal survives this shuffle, so only a PROFILE-SPECIFIC
         effect can beat it. The verdict uses this stronger null.
     LIMITATION, MEASURED: even the structure-matched null does not rescue the analysis. In stress
     tests where severity depended on nothing but latent structural similarity, and profiles and
     fingerprints were both noisy functions of that hidden structure, the association still beat
     every null and control (even with clusters of 2 drugs). Fingerprints are too noisy a proxy for
     what the profiles encode. So this analysis can RULE OUT an association (it fails for
     drug-risk, popularity and measured-similarity confounders) but it can NOT CONFIRM a
     profile-specific effect. Confirmation needs a predictive test (does the feature improve
     held-out severity prediction?), which is what the ablation provides.
  4. Repeat on subsets (molecules that are / are not in the Tox21 table) because their profiles are
     produced differently (single held-out fold model vs ensemble mean).

Honest limits (printed in every report)
---------------------------------------
  * Controls are imperfect proxies; surviving them does NOT prove a shared-mechanism effect.
  * The "ATC-file co-membership" proxy is coarse and its semantics are unverified.
  * Even a surviving association may be tiny (rho^2 is the share of rank variance explained).
  * Association, not causation, and not a clinical statement.

Usage
-----
  python -m src.overlap_analysis --profiler_arch gcn --n_boot 300 --n_perm 300
  python -m src.overlap_analysis --synthetic        # pipeline self-test on fabricated data
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.stats import rankdata

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

ATC_CODES = ('A', 'B', 'D', 'H', 'L', 'P', 'R', 'V')
CONTROL_NAMES = ('additive_risk', 'tanimoto', 'atc_jaccard', 'log_degree')


# ----------------------------------------------------------------------------- pair-level controls
def tanimoto_pairs(fp: np.ndarray, ia: np.ndarray, ib: np.ndarray, chunk: int = 20000) -> np.ndarray:
    """Tanimoto similarity of binary fingerprints for each (ia[k], ib[k]) pair; 0 when both empty."""
    out = np.zeros(len(ia), dtype=np.float64)
    for s in range(0, len(ia), chunk):
        a = fp[ia[s:s + chunk]] > 0
        b = fp[ib[s:s + chunk]] > 0
        inter = (a & b).sum(axis=1)
        union = (a | b).sum(axis=1)
        out[s:s + chunk] = np.where(union > 0, inter / np.maximum(union, 1), 0.0)
    return out


def jaccard_sets(sets: Sequence[frozenset], ia: np.ndarray, ib: np.ndarray) -> np.ndarray:
    """Jaccard overlap of two drugs' label sets; 0 when both empty."""
    out = np.zeros(len(ia), dtype=np.float64)
    for k, (i, j) in enumerate(zip(ia, ib)):
        a, b = sets[i], sets[j]
        u = len(a | b)
        out[k] = len(a & b) / u if u else 0.0
    return out


def load_atc_sets(raw_dir: str, identity_of: Dict[str, str],
                  codes: Sequence[str] = ATC_CODES) -> Dict[str, frozenset]:
    """
    Per-molecule set of DDInter ATC files in which the drug appears (either column).
    COARSE PROXY for therapeutic neighbourhood: DDInter's per-class downloads list interactions
    involving a class, so a drug also appears in the files of the classes of its partners.
    """
    found: Dict[str, set] = defaultdict(set)
    for code in codes:
        path = os.path.join(raw_dir, f'ddinter_downloads_code_{code}.csv')
        if not os.path.exists(path):
            continue
        df = pd.read_csv(path, usecols=['Drug_A', 'Drug_B'])
        for name in pd.unique(pd.concat([df['Drug_A'], df['Drug_B']])):
            ident = identity_of.get(name)
            if ident is not None:
                found[ident].add(code)
    return {k: frozenset(v) for k, v in found.items()}


# ----------------------------------------------------------------------------- partial correlation
class PartialCorr:
    """
    Reusable partial Spearman correlation: corr(rank(x), rank(y)) after regressing both on the ranks
    of the control columns Z. The y-side work is done once, so evaluating many x vectors (bootstrap,
    permutations) is cheap.
    """

    def __init__(self, y: np.ndarray, Z: np.ndarray):
        y = np.asarray(y, dtype=np.float64)
        Z = np.asarray(Z, dtype=np.float64).reshape(len(y), -1)
        self.n = len(y)
        cols = [np.ones(self.n)] + [rankdata(Z[:, j]) for j in range(Z.shape[1])]
        self.design = np.column_stack(cols)
        self.pinv = np.linalg.pinv(self.design)
        ry = rankdata(y)
        self.ey = ry - self.design @ (self.pinv @ ry)
        self.ey_norm = float(np.linalg.norm(self.ey))

    def corr(self, x: np.ndarray) -> float:
        rx = rankdata(np.asarray(x, dtype=np.float64))
        ex = rx - self.design @ (self.pinv @ rx)
        denom = float(np.linalg.norm(ex)) * self.ey_norm
        return float(ex @ self.ey / denom) if denom > 1e-12 else float('nan')


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx, ry = rankdata(x), rankdata(y)
    if np.ptp(rx) < 1e-12 or np.ptp(ry) < 1e-12:
        return float('nan')
    return float(np.corrcoef(rx, ry)[0, 1])


# ----------------------------------------------------------------------------- the pair table
@dataclass
class PairTable:
    ia: np.ndarray
    ib: np.ndarray
    y: np.ndarray
    overlap: np.ndarray
    controls: Dict[str, np.ndarray]
    both_in_table: np.ndarray
    profiles: np.ndarray          # (n_drugs, K) -- needed for the permutation nulls
    n_drugs: int
    clusters: Optional[np.ndarray] = None   # (n_drugs,) structural cluster id, for the matched null

    def subset(self, mask: np.ndarray) -> 'PairTable':
        return PairTable(self.ia[mask], self.ib[mask], self.y[mask], self.overlap[mask],
                         {k: v[mask] for k, v in self.controls.items()}, self.both_in_table[mask],
                         self.profiles, self.n_drugs, self.clusters)


def structure_clusters(fp: np.ndarray, drugs_per_cluster: int = 6, seed: int = 0) -> np.ndarray:
    """K-means clusters of fingerprints, sized to roughly `drugs_per_cluster` drugs each."""
    from sklearn.cluster import KMeans
    n = fp.shape[0]
    k = int(np.clip(n // max(drugs_per_cluster, 1), 2, n))
    return KMeans(n_clusters=k, n_init=3, random_state=seed).fit_predict(np.asarray(fp, dtype=np.float64))


def build_pair_table(pairs: Sequence[Tuple[str, str, int]], tox: Dict[str, np.ndarray],
                     fps: Dict[str, np.ndarray], in_table: Dict[str, bool],
                     atc_sets: Dict[str, frozenset], drugs_per_cluster: int = 6, seed: int = 0) -> PairTable:
    drugs = sorted({d for a, b, _ in pairs for d in (a, b)})
    index = {d: i for i, d in enumerate(drugs)}
    P = np.stack([np.asarray(tox[d], dtype=np.float64) for d in drugs])
    FP = np.stack([np.asarray(fps[d]) for d in drugs])
    ia = np.array([index[a] for a, _, _ in pairs])
    ib = np.array([index[b] for _, b, _ in pairs])
    y = np.array([lab for _, _, lab in pairs], dtype=int)

    mean_risk = P.mean(axis=1)
    degree = np.bincount(np.concatenate([ia, ib]), minlength=len(drugs))
    sets = [atc_sets.get(d, frozenset()) for d in drugs]
    in_arr = np.array([bool(in_table.get(d, False)) for d in drugs])

    controls = {
        'additive_risk': mean_risk[ia] + mean_risk[ib],
        'tanimoto': tanimoto_pairs(FP, ia, ib),
        'atc_jaccard': jaccard_sets(sets, ia, ib),
        'log_degree': np.log1p(degree)[ia] + np.log1p(degree)[ib],
    }
    return PairTable(ia, ib, y, np.sum(P[ia] * P[ib], axis=1), controls,
                     in_arr[ia] & in_arr[ib], P, len(drugs),
                     structure_clusters(FP, drugs_per_cluster, seed))


# ----------------------------------------------------------------------------- statistics
def _controls_matrix(t: PairTable, names: Sequence[str]) -> np.ndarray:
    return np.column_stack([t.controls[n] for n in names])


def point_estimates(t: PairTable) -> Dict[str, float]:
    """Raw, additive-controlled and fully-controlled partial correlations (plus each control's own rho)."""
    res = {
        'n_pairs': int(len(t.y)),
        'rho_overlap': spearman(t.overlap, t.y),
        'rho_partial_additive': PartialCorr(t.y, _controls_matrix(t, ['additive_risk'])).corr(t.overlap),
        'rho_partial_all': PartialCorr(t.y, _controls_matrix(t, CONTROL_NAMES)).corr(t.overlap),
    }
    for n in CONTROL_NAMES:
        res[f'rho_{n}'] = spearman(t.controls[n], t.y)
    return res


def drug_bootstrap(t: PairTable, n_boot: int, rng: np.random.Generator) -> Dict[str, np.ndarray]:
    """
    Cluster bootstrap over DRUGS. Each replicate draws drugs with replacement; a pair is included
    m_i * m_j times (the multiplicities of its two drugs), so pairs sharing a drug resample together.
    """
    out = {'rho_overlap': [], 'rho_partial_additive': [], 'rho_partial_all': []}
    for _ in range(n_boot):
        m = np.bincount(rng.integers(0, t.n_drugs, t.n_drugs), minlength=t.n_drugs)
        w = m[t.ia] * m[t.ib]
        if w.sum() < 50:
            continue
        idx = np.repeat(np.arange(len(w)), w)
        sub = PairTable(t.ia[idx], t.ib[idx], t.y[idx], t.overlap[idx],
                        {k: v[idx] for k, v in t.controls.items()}, t.both_in_table[idx], t.profiles, t.n_drugs,
                        t.clusters)
        r = point_estimates(sub)
        for k in out:
            out[k].append(r[k])
    return {k: np.array(v) for k, v in out.items()}


def permutation_null(t: PairTable, n_perm: int, rng: np.random.Generator) -> np.ndarray:
    """
    Shuffle which drug owns which risk profile, recompute the overlap score, and take the fully
    controlled partial correlation each time. Shows what chance alone produces given the same
    controls, severity labels and pair structure.
    """
    pc = PartialCorr(t.y, _controls_matrix(t, CONTROL_NAMES))
    null = []
    for _ in range(n_perm):
        perm = rng.permutation(t.n_drugs)
        ov = np.sum(t.profiles[perm[t.ia]] * t.profiles[perm[t.ib]], axis=1)
        null.append(pc.corr(ov))
    return np.array(null)


def matched_permutation(clusters: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Permutation of drug indices that only moves a drug to another position inside its own cluster."""
    perm = np.arange(len(clusters))
    for c in np.unique(clusters):
        members = np.flatnonzero(clusters == c)
        if len(members) > 1:
            perm[members] = rng.permutation(members)
    return perm


def matched_permutation_null(t: PairTable, n_perm: int, rng: np.random.Generator) -> Tuple[np.ndarray, float]:
    """
    STRUCTURE-MATCHED null: shuffle risk profiles only among structurally similar drugs. Anything that
    flows from "similar structure -> similar profile AND similar interactions" is preserved, so only a
    profile-specific effect can exceed it. Also returns `retention`, the rank correlation between the
    real overlap score and a matched-shuffled one (high = the null keeps most of the real signal's
    structure; low = the clusters are too coarse to be a demanding null).
    """
    if t.clusters is None:
        return np.array([]), float('nan')
    pc = PartialCorr(t.y, _controls_matrix(t, CONTROL_NAMES))
    null, kept = [], []
    for _ in range(n_perm):
        perm = matched_permutation(t.clusters, rng)
        ov = np.sum(t.profiles[perm[t.ia]] * t.profiles[perm[t.ib]], axis=1)
        null.append(pc.corr(ov))
        if len(kept) < 5:
            kept.append(spearman(ov, t.overlap))
    return np.array(null), float(np.nanmean(kept)) if kept else float('nan')


def analyze_subset(t: PairTable, n_boot: int, n_perm: int, seed: int = 0) -> Dict[str, Any]:
    rng = np.random.default_rng(seed)
    est = point_estimates(t)
    boot = drug_bootstrap(t, n_boot, rng) if n_boot > 0 else {}
    null = permutation_null(t, n_perm, rng) if n_perm > 0 else np.array([])
    m_null, retention = matched_permutation_null(t, n_perm, rng) if n_perm > 0 else (np.array([]), float('nan'))

    def ci(key):
        v = boot.get(key)
        return (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if v is not None and len(v) >= 20 else (float('nan'),) * 2

    est['ci_overlap'] = ci('rho_overlap')
    est['ci_partial_additive'] = ci('rho_partial_additive')
    est['ci_partial_all'] = ci('rho_partial_all')
    est['n_boot_used'] = int(len(boot.get('rho_partial_all', [])))
    est['null_mean'] = float(np.nanmean(null)) if len(null) else float('nan')
    est['null_p95'] = float(np.nanpercentile(null, 95)) if len(null) else float('nan')
    est['perm_p'] = (float((1 + np.sum(null >= est['rho_partial_all'])) / (1 + len(null)))
                     if len(null) else float('nan'))
    est['matched_null_mean'] = float(np.nanmean(m_null)) if len(m_null) else float('nan')
    est['matched_null_p95'] = float(np.nanpercentile(m_null, 95)) if len(m_null) else float('nan')
    est['matched_perm_p'] = (float((1 + np.sum(m_null >= est['rho_partial_all'])) / (1 + len(m_null)))
                             if len(m_null) else float('nan'))
    est['retention'] = retention
    est['status'] = verdict_status(est)
    return est


def verdict_status(est: Dict[str, Any]) -> str:
    """
    EXPLAINED AWAY                          lower bootstrap bound <= 0, OR observed <= structure-matched
                                            null 95th percentile: the association is not distinguishable
                                            from the controls / null. This verdict is informative.
    NOT EXPLAINED AWAY (UNCONFIRMED)        both criteria pass. This is NOT evidence of a profile-specific
                                            effect: stress tests with purely structural confounding
                                            produce exactly this verdict. Confirm predictively.
    INCONCLUSIVE                            bootstrap or permutation was not run / too few replicates.
    """
    lo = est['ci_partial_all'][0]
    p95 = est['matched_null_p95']
    if np.isnan(lo) or np.isnan(p95):
        return 'INCONCLUSIVE'
    return 'NOT EXPLAINED AWAY (UNCONFIRMED)' if (lo > 0 and est['rho_partial_all'] > p95) else 'EXPLAINED AWAY'


def run_analysis(table: PairTable, n_boot: int, n_perm: int, seed: int = 0) -> Dict[str, Dict[str, Any]]:
    subsets = {
        'ALL': np.ones(len(table.y), dtype=bool),
        'BOTH_IN_TOX21_TABLE': table.both_in_table,
        'AT_LEAST_ONE_OUTSIDE_TABLE': ~table.both_in_table,
    }
    results = {}
    for name, mask in subsets.items():
        if mask.sum() < 200:
            continue
        results[name] = analyze_subset(table.subset(mask), n_boot, n_perm, seed)
    return results


# ----------------------------------------------------------------------------- reporting
def render_report(results: Dict[str, Dict[str, Any]], meta: Dict[str, Any]) -> str:
    L = ['# Overlap-lead analysis', '',
         'Question: does the shared-predicted-toxicity score track DDI severity **beyond** structural '
         'similarity, therapeutic-class closeness, drug popularity and each drug\'s own risk?', '', '## Setup', '']
    for k, v in meta.items():
        L.append(f'- **{k}**: {v}')
    L += ['', '## Results', '',
          '| Subset | Pairs | rho overlap | rho (controlling additive risk) | rho (controlling ALL) | 95% drug-bootstrap CI | Global null p95 | Structure-matched null p95 | Null retention | Status |',
          '|---|---|---|---|---|---|---|---|---|---|']
    for name, r in results.items():
        lo, hi = r['ci_partial_all']
        L.append(f"| {name} | {r['n_pairs']} | {r['rho_overlap']:.3f} | {r['rho_partial_additive']:.3f} | "
                 f"{r['rho_partial_all']:.3f} | [{lo:.3f}, {hi:.3f}] | {r['null_p95']:.3f} | "
                 f"{r['matched_null_p95']:.3f} | {r['retention']:.2f} | **{r['status']}** |")
    L += ['', '### How strongly do the controls themselves track severity? (Spearman rho)', '',
          '| Subset | additive risk | fingerprint similarity | ATC co-membership | log popularity |', '|---|---|---|---|---|']
    for name, r in results.items():
        L.append(f"| {name} | {r['rho_additive_risk']:.3f} | {r['rho_tanimoto']:.3f} | "
                 f"{r['rho_atc_jaccard']:.3f} | {r['rho_log_degree']:.3f} |")

    L += ['', '## Reading this honestly', '']
    all_r = results.get('ALL')
    if all_r:
        share = 100 * all_r['rho_partial_all'] ** 2
        if all_r['status'] == 'EXPLAINED AWAY':
            L.append('- On all pairs the association is EXPLAINED AWAY: it is not distinguishable from similarity, '
                     'class closeness, popularity, own-risk and structure-matched chance. Treat the shared-toxicity '
                     'idea as closed for severity prediction. This verdict is informative.')
        elif all_r['status'] == 'NOT EXPLAINED AWAY (UNCONFIRMED)':
            L.append(f"- On all pairs a small association remains after the controls (partial rho "
                     f"{all_r['rho_partial_all']:.3f}, about {share:.1f}% of rank variance). **This does not confirm a "
                     f"profile-specific effect.** Stress tests show that purely structural confounding produces this "
                     f"same result, because fingerprints are noisy proxies for what the risk profiles encode. Only a "
                     f"predictive test can support the claim: check whether adding the profiles improves held-out "
                     f"severity prediction (the ablation).")
        else:
            L.append(f"- Status on all pairs is {all_r['status']}: bootstrap or permutations were not run.")
    L += ['- "Null retention" is how much of the real overlap score\'s structure the matched shuffle keeps.',
          '- Controls are imperfect proxies. In stress tests a purely structure-driven association still passed every '
          'control and both nulls, so a passing result is unconfirmed, never supportive on its own.',
          '- The ATC co-membership proxy is coarse (a drug also appears in the files of its partners\' classes).',
          '- Pairs share drugs, so intervals come from resampling drugs, not pairs.',
          '- This is association only. It is not a clinical statement and not a causal claim.', '']
    return '\n'.join(L)


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="Overlap-lead analysis with confounder controls")
    ap.add_argument('--profiler_arch', default='gcn', choices=['gcn', 'gin', 'mpnn'])
    ap.add_argument('--n_boot', type=int, default=300)
    ap.add_argument('--n_perm', type=int, default=300)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--out_dir', default='results/overlap_analysis')
    ap.add_argument('--synthetic', action='store_true', help='fabricated data to self-test the pipeline')
    ap.add_argument('--synthetic_tox_signal', type=float, default=0.0)
    ap.add_argument('--synthetic_seed', type=int, default=0)
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    from src import run_ablation as ra

    shim = argparse.Namespace(profiler_arch=args.profiler_arch, variants=[], cyp=False,
                              synthetic_seed=args.synthetic_seed, synthetic_tox_signal=args.synthetic_tox_signal,
                              synthetic_tox_independent=True)
    data = ra.load_synthetic(shim) if args.synthetic else ra.load_real(shim)

    if args.synthetic:                          # fabricate the extra metadata deterministically
        rng = np.random.default_rng(args.synthetic_seed)
        names = sorted({d for a, b, _ in data.pairs for d in (a, b)})
        data.in_table = {n: bool(rng.random() < 0.6) for n in names}
        data.atc_sets = {n: frozenset(rng.choice(list(ATC_CODES), size=rng.integers(1, 4), replace=False)) for n in names}

    table = build_pair_table(data.pairs, data.tox, data.fps, data.in_table, data.atc_sets)
    print(f"{len(table.y)} pairs, {table.n_drugs} molecules. Bootstrap {args.n_boot}, permutations {args.n_perm}...")
    results = run_analysis(table, args.n_boot, args.n_perm, args.seed)

    os.makedirs(args.out_dir, exist_ok=True)
    meta = {'data source': data.source, 'profiler_mode': data.profiler_mode,
            'bootstrap replicates': args.n_boot, 'permutations': args.n_perm,
            'controls': 'additive risk, fingerprint Tanimoto, ATC-file co-membership (proxy), log popularity'}
    meta.update({f'note {i}': n for i, n in enumerate(data.notes, 1)})
    report = render_report(results, meta)
    with open(os.path.join(args.out_dir, 'overlap_analysis.md'), 'w') as f:
        f.write(report)
    pd.DataFrame([{'subset': k, **{kk: (list(vv) if isinstance(vv, tuple) else vv) for kk, vv in v.items()}}
                  for k, v in results.items()]).to_csv(os.path.join(args.out_dir, 'overlap_analysis.csv'), index=False)
    with open(os.path.join(args.out_dir, 'run_meta.json'), 'w') as f:
        json.dump({**meta, 'args': vars(args)}, f, indent=2, default=str)
    print(report)
    return results


if __name__ == '__main__':
    main()
