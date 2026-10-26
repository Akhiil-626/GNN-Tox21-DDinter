"""
src/controlled_overlap_test.py

Controlled association test: shared Tox21-risk ↔ DDI severity.
No model training required. Runs in minutes on CPU.

What it answers
---------------
After controlling for (a) structural fingerprint similarity (Tanimoto) and
(b) ATC drug-class membership, does shared Tox21 risk still correlate with
DDI severity?

We restrict to pairs where BOTH drugs have ACTUAL Tox21 lab measurements
(found in the Tox21 CSV by canonical SMILES matching) so there is zero
prediction noise — just the ground-truth cell-assay readouts.

Regression model
    severity ∈ {0=Minor, 1=Moderate, 2=Major}
    severity_i = β₀ + β₁·tox_overlap_i + β₂·fp_tanimoto_i
                + β₃·same_atc_i + Σ_j γ_j·atc_dummy_j + ε_i

  where:
    tox_overlap   = fraction of jointly-tested Tox21 endpoints where BOTH drugs
                    are positive (using actual lab labels, not GNN predictions)
    fp_tanimoto   = Morgan-fingerprint Tanimoto similarity (structural confound)
    same_atc      = 1 if both drugs share the same first-level ATC class
    atc_dummies   = indicator for which ATC-code file the pair came from
                    (controls for baseline severity differences across drug classes)

Inference
    • Pair-level OLS gives the raw effect size.
    • Drug-level bootstrap (resample drugs, not pairs; 2000 replicates) gives
      honest 95% CIs, because pairs sharing a drug are correlated.
    • Partial Spearman ρ (tox_overlap vs severity, after partialling out Tanimoto
      and same_atc via rank residuals) is reported as a non-parametric check.

Verdict rule (strict)
    SUPPORTED only if β₁ > 0 AND the drug-level 95% bootstrap CI excludes zero.
    Otherwise: NOT SUPPORTED.

Usage
-----
    python -m src.controlled_overlap_test
    python -m src.controlled_overlap_test --n_boot 2000 --out_dir results/controlled_overlap

Outputs (in --out_dir)
-----------------------
    pairs.csv           analysis dataframe (one row per qualifying pair)
    report.md           human-readable verdict with all statistics
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import textwrap
import warnings

# Force UTF-8 stdout so Unicode characters (arrows, Greek letters, em-dashes)
# don't crash on Windows terminals that default to cp1252.
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from tqdm import tqdm

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.chem_utils import canonical_key
from src.dataset import TOX21_TASKS, download_tox21_data
from src.ddi_features import partial_spearman, spearman_overlap_vs_severity

try:
    from rdkit import Chem, DataStructs
    from rdkit.Chem import rdMolDescriptors
    # Silence the "please use MorganGenerator" deprecation flood that clogs stdout
    from rdkit import RDLogger
    RDLogger.DisableLog('rdApp.*')
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False
    warnings.warn("RDKit not available — Tanimoto similarity control will be omitted.")

ATC_CODES = ['A', 'B', 'D', 'H', 'L', 'P', 'R', 'V']
LEVEL_TO_INT = {'Minor': 0, 'Moderate': 1, 'Major': 2}


# ═══════════════════════════════════════════════════════════════════ data loading

def load_tox21_table(data_dir: str = 'data') -> Dict[str, np.ndarray]:
    """
    Load the Tox21 CSV, canonicalise every SMILES.
    Returns dict: canonical_smiles_key -> float array of shape (n_tasks,), NaN for missing.
    """
    csv_path = download_tox21_data(os.path.join(data_dir, 'raw'))
    df = pd.read_csv(csv_path)
    tasks = [t for t in TOX21_TASKS if t in df.columns]
    table: Dict[str, np.ndarray] = {}
    for _, row in df.iterrows():
        smi = str(row.get('smiles', ''))
        key = canonical_key(smi)
        if key is not None and key not in table:
            table[key] = row[tasks].to_numpy(dtype=float)   # NaN where not tested
    print(f"Tox21 table: {len(table)} unique molecules, {len(tasks)} tasks.")
    return table


def load_smiles_cache(cache_path: str) -> Dict[str, Optional[str]]:
    """Load the DDInter SMILES cache built by ddi_dataset.py."""
    if not os.path.exists(cache_path):
        raise FileNotFoundError(
            f"SMILES cache not found at '{cache_path}'.\n"
            "Run `python -m src.ddi_dataset` first to build it."
        )
    with open(cache_path) as f:
        cache = json.load(f)
    resolved = sum(1 for v in cache.values() if v)
    print(f"SMILES cache: {len(cache)} entries, {resolved} resolved.")
    return cache


def load_ddinter_pairs(raw_dir: str) -> Tuple[List[Dict], Dict[str, str]]:
    """
    Read all 8 ATC-code CSVs.  Returns:
        pairs     list of dicts with keys: drug_a, drug_b, severity, atc_source
        drug_atc  drug_name -> primary ATC letter (first time seen as Drug_A)
    """
    pairs: List[Dict] = []
    drug_atc: Dict[str, str] = {}   # drug_name -> ATC letter, from whichever file it first appeared as Drug_A

    for code in ATC_CODES:
        csv_path = os.path.join(raw_dir, f'ddinter_downloads_code_{code}.csv')
        if not os.path.exists(csv_path):
            print(f"  [skip] {csv_path} not found.")
            continue
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            level = str(row.get('Level', '')).strip()
            if level not in LEVEL_TO_INT:
                continue
            da = str(row['Drug_A']).strip()
            db = str(row['Drug_B']).strip()
            if da not in drug_atc:
                drug_atc[da] = code          # Drug_A's ATC is the file's ATC code
            pairs.append({
                'drug_a': da,
                'drug_b': db,
                'severity': LEVEL_TO_INT[level],
                'atc_source': code,
            })

    print(f"DDInter: {len(pairs)} pairs with known severity across {len(ATC_CODES)} ATC files.")
    return pairs, drug_atc


# ═══════════════════════════════════════════════════════════════════ features

def _morgan_bitvect(smiles: str, radius: int = 2, n_bits: int = 2048):
    """Return RDKit Morgan fingerprint bit vector, or None on failure."""
    if not HAS_RDKIT:
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return rdMolDescriptors.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)


def _tanimoto(fp_a, fp_b) -> Optional[float]:
    if fp_a is None or fp_b is None:
        return None
    return float(DataStructs.TanimotoSimilarity(fp_a, fp_b))


def tox_overlap_from_labels(y_a: np.ndarray, y_b: np.ndarray, min_joint: int = 3) -> Optional[float]:
    """
    Fraction of jointly-tested Tox21 endpoints where BOTH drugs have a positive
    label (== 1).  NaN entries are excluded.  Returns None if fewer than
    `min_joint` endpoints have measurements in both drugs.
    """
    mask = ~(np.isnan(y_a) | np.isnan(y_b))
    n_joint = int(mask.sum())
    if n_joint < min_joint:
        return None
    both_positive = float(((y_a[mask] == 1) & (y_b[mask] == 1)).sum())
    return both_positive / n_joint


def mean_tox_from_labels(y: np.ndarray) -> float:
    """Mean activity rate across all non-NaN endpoints of one drug."""
    valid = y[~np.isnan(y)]
    return float(valid.mean()) if len(valid) > 0 else float('nan')


# ═══════════════════════════════════════════════════════════════════ build dataframe

def build_analysis_df(
    pairs: List[Dict],
    tox_table: Dict[str, np.ndarray],
    smiles_cache: Dict[str, Optional[str]],
    drug_atc: Dict[str, str],
) -> pd.DataFrame:
    """
    Build the analysis dataframe restricted to pairs where BOTH drugs appear
    in the Tox21 table (actual lab measurements).

    Fast path: canonicalize each unique drug SMILES once up-front, pre-compute
    fingerprints for qualifying drugs only, then scan pairs with O(1) set lookups.
    """
    # ── Step 1: Canonicalize all unique drug SMILES once (not per pair)
    unique_drugs = sorted({p['drug_a'] for p in pairs} | {p['drug_b'] for p in pairs})
    print(f"Pre-canonicalizing {len(unique_drugs)} unique drug SMILES...")
    drug_key: Dict[str, Optional[str]] = {}   # drug_name -> canonical key or None
    for name in tqdm(unique_drugs, desc="Canonicalizing SMILES"):
        smi = smiles_cache.get(name)
        if smi:
            drug_key[name] = canonical_key(smi)
        else:
            drug_key[name] = None

    # ── Step 2: Identify which drugs are in the Tox21 table
    tox21_drugs = {name for name, key in drug_key.items()
                   if key is not None and key in tox_table}
    print(f"{len(tox21_drugs)} / {len(unique_drugs)} unique DDInter drugs are in the Tox21 table.")

    # ── Step 3: Pre-compute fingerprints for Tox21-qualifying drugs only
    fp_map: Dict[str, any] = {}    # drug_name -> RDKit bitvector or None
    if HAS_RDKIT:
        print(f"Pre-computing Morgan fingerprints for {len(tox21_drugs)} qualifying drugs...")
        for name in tqdm(tox21_drugs, desc="Morgan fingerprints"):
            smi = smiles_cache.get(name)
            fp_map[name] = _morgan_bitvect(smi) if smi else None

    # ── Step 4: Scan pairs — O(1) set lookup first, feature computation only on survivors
    rows = []
    n_no_smiles = n_no_tox = n_no_overlap = 0

    for p in pairs:
        na, nb = p['drug_a'], p['drug_b']

        # Fast rejection: drug not in Tox21
        if na not in tox21_drugs or nb not in tox21_drugs:
            if drug_key.get(na) is None or drug_key.get(nb) is None:
                n_no_smiles += 1
            else:
                n_no_tox += 1
            continue

        key_a = drug_key[na]
        key_b = drug_key[nb]
        y_a = tox_table[key_a]
        y_b = tox_table[key_b]

        # Tox21 overlap (actual lab labels)
        ov = tox_overlap_from_labels(y_a, y_b)
        if ov is None:
            n_no_overlap += 1
            continue

        # Additive danger (controls for "each drug is individually dangerous")
        additive_risk = mean_tox_from_labels(y_a) + mean_tox_from_labels(y_b)

        # Tanimoto fingerprint similarity
        tan = _tanimoto(fp_map.get(na), fp_map.get(nb)) if HAS_RDKIT else None

        # ATC class controls
        atc_a = drug_atc.get(na, '?')
        atc_b = drug_atc.get(nb, '?')
        same_atc = int(atc_a != '?' and atc_b != '?' and atc_a == atc_b)

        rows.append({
            'drug_a': na,
            'drug_b': nb,
            'severity': p['severity'],
            'tox_overlap': ov,
            'additive_risk': additive_risk,
            'fp_tanimoto': tan,
            'same_atc': same_atc,
            'atc_source': p['atc_source'],
            'key_a': key_a,
            'key_b': key_b,
        })

    df = pd.DataFrame(rows)
    print(f"\nAnalysis dataset: {len(df)} pairs qualify")
    print(f"  Dropped — no SMILES in cache : {n_no_smiles}")
    print(f"  Dropped — not in Tox21 table : {n_no_tox}")
    print(f"  Dropped — <3 jointly tested  : {n_no_overlap}")
    if not df.empty:
        sev_dist = df['severity'].value_counts().sort_index().to_dict()
        sev_labels = {0: 'Minor', 1: 'Moderate', 2: 'Major'}
        sev_str = ', '.join(f"{sev_labels[k]}={v}" for k, v in sorted(sev_dist.items()))
        print(f"  Severity distribution       : {sev_str}")
        print(f"  Tox overlap   mean ± std    : {df['tox_overlap'].mean():.4f} ± {df['tox_overlap'].std():.4f}")
        if df['fp_tanimoto'].notna().any():
            print(f"  Tanimoto      mean ± std    : {df['fp_tanimoto'].mean():.4f} ± {df['fp_tanimoto'].std():.4f}")
        print(f"  Same-ATC pairs              : {df['same_atc'].sum()} / {len(df)}")
    return df


# ═══════════════════════════════════════════════════════════════════ statistics

def _build_design_matrix(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Assemble design matrix X and response y for OLS.

    Columns: intercept, tox_overlap, additive_risk, fp_tanimoto (if available),
             same_atc, ATC-source dummies (drop first for reference).
    Returns (X, y, feature_names).
    """
    y = df['severity'].to_numpy(dtype=float)
    feature_names = ['intercept', 'tox_overlap', 'additive_risk']
    cols = [np.ones(len(df)), df['tox_overlap'].values, df['additive_risk'].values]

    if df['fp_tanimoto'].notna().all():
        feature_names.append('fp_tanimoto')
        cols.append(df['fp_tanimoto'].values)

    feature_names.append('same_atc')
    cols.append(df['same_atc'].values.astype(float))

    # ATC source dummies (drop first level = reference)
    present_atc = sorted(df['atc_source'].unique())
    for code in present_atc[1:]:
        feature_names.append(f'atc_{code}')
        cols.append((df['atc_source'] == code).values.astype(float))

    X = np.column_stack(cols)
    return X, y, feature_names


def ols_fit(X: np.ndarray, y: np.ndarray) -> Dict:
    """OLS with t-stats and two-sided p-values."""
    n, p = X.shape
    beta, _, rank, _ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    sigma2 = float((resid ** 2).sum() / max(n - p, 1))
    XtX_inv = np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.maximum(np.diag(XtX_inv) * sigma2, 0.0))
    t_stats = np.where(se > 1e-12, beta / se, 0.0)
    p_vals = 2 * stats.t.sf(np.abs(t_stats), df=max(n - p, 1))
    return {'beta': beta, 'se': se, 't': t_stats, 'p': p_vals, 'sigma2': sigma2, 'n': n, 'rank': rank}


def drug_level_bootstrap(df: pd.DataFrame, n_boot: int = 2000, seed: int = 0) -> Dict:
    """
    Resample DRUGS (not pairs) with replacement; retain pairs where both sampled
    drugs are present. Refit OLS in each replicate; collect the β for tox_overlap.

    This gives honest CIs because pairs sharing a drug are correlated — standard
    pair-level CIs would be anticonservative.
    """
    rng = np.random.default_rng(seed)
    all_drugs = np.array(sorted(set(df['drug_a'].tolist()) | set(df['drug_b'].tolist())))
    n_drugs = len(all_drugs)

    X_full, y_full, feat_names = _build_design_matrix(df)
    tox_idx = feat_names.index('tox_overlap')

    betas: List[float] = []
    for _ in range(n_boot):
        sampled = set(rng.choice(all_drugs, size=n_drugs, replace=True).tolist())
        mask = df['drug_a'].isin(sampled) & df['drug_b'].isin(sampled)
        sub = df[mask]
        if len(sub) < 10:
            continue
        try:
            X_b, y_b, _ = _build_design_matrix(sub)
            res = ols_fit(X_b, y_b)
            betas.append(float(res['beta'][tox_idx]))
        except (np.linalg.LinAlgError, ValueError):
            continue

    betas_arr = np.array(betas)
    return {
        'beta_mean': float(np.mean(betas_arr)) if len(betas_arr) else float('nan'),
        'ci_lo': float(np.percentile(betas_arr, 2.5)) if len(betas_arr) else float('nan'),
        'ci_hi': float(np.percentile(betas_arr, 97.5)) if len(betas_arr) else float('nan'),
        'n_valid_boot': len(betas_arr),
        'n_boot_requested': n_boot,
    }


# ═══════════════════════════════════════════════════════════════════ report

def _fmt_p(p: float) -> str:
    if np.isnan(p):
        return 'n/a'
    if p < 0.001:
        return '<0.001'
    return f'{p:.3f}'


def _verdict(beta_tox: float, ci_lo: float, ci_hi: float) -> str:
    if np.isnan(beta_tox) or np.isnan(ci_lo):
        return 'INCONCLUSIVE (insufficient data)'
    if beta_tox > 0 and ci_lo > 0:
        return 'SUPPORTED — positive effect, 95% bootstrap CI excludes zero'
    if beta_tox < 0 and ci_hi < 0:
        return 'REJECTED — tox overlap *negatively* associated with severity'
    if ci_lo <= 0 <= ci_hi:
        return 'NOT SUPPORTED — bootstrap CI spans zero'
    return 'NOT SUPPORTED'


def write_report(
    df: pd.DataFrame,
    ols_res: Dict,
    boot_res: Dict,
    feat_names: List[str],
    rho_unadjusted: float,
    rho_partial_tan: float,
    rho_partial_add: float,
    rho_partial_full: float,
    args: argparse.Namespace,
) -> str:
    tox_idx = feat_names.index('tox_overlap')
    beta_tox = ols_res['beta'][tox_idx]
    se_tox = ols_res['se'][tox_idx]
    p_tox = ols_res['p'][tox_idx]
    ci_lo, ci_hi = boot_res['ci_lo'], boot_res['ci_hi']
    verdict = _verdict(beta_tox, ci_lo, ci_hi)

    has_tan = 'fp_tanimoto' in feat_names
    n_pairs = len(df)
    n_drugs = len(set(df['drug_a'].tolist()) | set(df['drug_b'].tolist()))

    lines = [
        "# Controlled Tox21-Risk Overlap vs DDI Severity",
        "",
        "## Study design",
        "",
        "**Restriction**: only pairs where BOTH drugs appear in the Tox21 CSV "
        "(actual lab measurements, no GNN predictions).",
        "",
        "**Overlap metric**: fraction of jointly-tested endpoints where both drugs "
        "are positive (lab label == 1). Only endpoints with measurements in both "
        "drugs count.",
        "",
        "**Controls applied**:",
        f"  1. Additive danger (sum of each drug's mean activity rate across all endpoints) "
        f"— separates *shared* risk from *each drug individually being dangerous*.",
    ]
    if has_tan:
        lines.append("  2. Morgan-fingerprint Tanimoto similarity "
                     "(structural similarity confound, radius=2, 2048 bits).")
        lines.append("  3. Same first-level ATC class (pharmacological class confound).")
        lines.append("  4. ATC-source dummy variables (baseline severity differences by drug class).")
    else:
        lines += [
            "  2. Same first-level ATC class (pharmacological class confound).",
            "  3. ATC-source dummy variables (baseline severity differences by drug class).",
            "  ⚠ Tanimoto similarity omitted — RDKit unavailable.",
        ]
    lines += [
        "",
        "**Bootstrap**: drug-level (resample drugs, not pairs) to give honest CIs.",
        "",
        "## Dataset summary",
        "",
        f"| Item | Value |",
        f"|------|-------|",
        f"| Qualifying pairs | {n_pairs} |",
        f"| Unique drugs | {n_drugs} |",
        f"| Bootstrap replicates used | {boot_res['n_valid_boot']} / {boot_res['n_boot_requested']} |",
    ]
    if n_pairs < 30:
        lines += ["", "> ⚠ **Warning**: very few pairs qualify. "
                  "Results are likely underpowered; treat as exploratory only."]

    lines += [
        "",
        "## OLS regression results",
        "",
        f"Dependent variable: severity (0=Minor, 1=Moderate, 2=Major).",
        "",
        "| Feature | β | SE | t | p (pair-level) |",
        "|---------|---|----|---|----------------|",
    ]
    for i, name in enumerate(feat_names):
        if name == 'intercept':
            continue
        b = ols_res['beta'][i]
        s = ols_res['se'][i]
        t = ols_res['t'][i]
        p = ols_res['p'][i]
        marker = ' ← KEY' if name == 'tox_overlap' else ''
        lines.append(f"| {name}{marker} | {b:+.4f} | {s:.4f} | {t:+.3f} | {_fmt_p(p)} |")

    lines += [
        "",
        "## Drug-level bootstrap CI for tox_overlap",
        "",
        f"β (tox_overlap) = **{beta_tox:+.4f}** (SE = {se_tox:.4f}, pair-level p = {_fmt_p(p_tox)})",
        f"95% drug-level bootstrap CI: **[{ci_lo:+.4f}, {ci_hi:+.4f}]**",
        f"(based on {boot_res['n_valid_boot']} valid bootstrap replicates)",
        "",
        "## Partial Spearman correlations (non-parametric check)",
        "",
        "| Metric | ρ |",
        "|--------|---|",
        f"| Unadjusted Spearman(tox_overlap, severity) | {rho_unadjusted:+.4f} |",
        f"| Partial ρ controlling for additive_risk only | {rho_partial_add:+.4f} |",
    ]
    if has_tan:
        lines.append(f"| Partial ρ controlling for Tanimoto only | {rho_partial_tan:+.4f} |")
        lines.append(f"| Partial ρ controlling for Tanimoto + additive_risk | {rho_partial_full:+.4f} |")
    lines += [
        "",
        "> Note: pair-level p-values overstate significance (pairs sharing a drug are correlated).",
        "> The drug-level bootstrap CI above is the primary inferential quantity.",
        "",
        "## ✦ Verdict",
        "",
        f"**{verdict}**",
        "",
    ]
    if 'NOT SUPPORTED' in verdict or 'REJECTED' in verdict:
        lines += [
            "The Tox21-risk-overlap association does not survive controls for structural similarity, ",
            "additive drug danger, and ATC drug class. The toxicity-fingerprint idea is closed on this dataset.",
        ]
    elif 'SUPPORTED' in verdict:
        lines += [
            "The association survives all controls. This is a necessary (not sufficient) condition ",
            "for the toxicity-fingerprint idea to be useful — it should be replicated on held-out data ",
            "before drawing mechanistic conclusions.",
        ]
    else:
        lines.append("Insufficient data to draw a conclusion.")

    lines += [
        "",
        "## Run settings",
        "",
        f"- `--n_boot`: {args.n_boot}",
        f"- `--data_dir`: {args.data_dir}",
        f"- `--min_joint`: {args.min_joint}",
        f"- `--out_dir`: {args.out_dir}",
    ]
    return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════════════ main

def run(args: argparse.Namespace) -> None:
    os.makedirs(args.out_dir, exist_ok=True)

    # ── 1. Load data
    tox_table = load_tox21_table(args.data_dir)
    cache_path = os.path.join(args.data_dir, 'raw', 'ddinter_smiles_cache.json')
    smiles_cache = load_smiles_cache(cache_path)
    pairs, drug_atc = load_ddinter_pairs(os.path.join(args.data_dir, 'raw'))

    # ── 2. Build analysis dataframe
    df = build_analysis_df(pairs, tox_table, smiles_cache, drug_atc)
    if len(df) < 10:
        print(f"\n⚠  Only {len(df)} qualifying pairs — too few for reliable inference.")
        print("   This likely means very few DDInter drugs are also in the Tox21 table.")
        print("   The test is inconclusive; results saved for transparency.")
        if df.empty:
            df = pd.DataFrame(columns=['drug_a', 'drug_b', 'severity', 'tox_overlap',
                                       'additive_risk', 'fp_tanimoto', 'same_atc', 'atc_source'])
        df.to_csv(os.path.join(args.out_dir, 'pairs.csv'), index=False)

        inconclusive = (
            "# Controlled Overlap Test — INCONCLUSIVE\n\n"
            f"Only {len(df)} pairs qualify (both drugs in Tox21 table with ≥{args.min_joint} "
            "jointly-tested endpoints). This is too few for reliable inference.\n\n"
            "**Why so few?** Tox21 is primarily an environmental-chemical screen; most approved "
            "clinical drugs in DDInter are not in the Tox21 table. "
            "Consider running `python -m src.crossfit --task tox21 --arch gcn --folds 5` to get "
            "GNN-predicted profiles for all DDInter drugs, then re-run the ablation.\n"
        )
        with open(os.path.join(args.out_dir, 'report.md'), 'w') as f:
            f.write(inconclusive)
        print(f"\nReport written to {args.out_dir}/report.md")
        return

    # ── 3. Save pairs CSV
    df.to_csv(os.path.join(args.out_dir, 'pairs.csv'), index=False)
    print(f"Pairs CSV saved -> {args.out_dir}/pairs.csv")

    # ── 4. Unadjusted correlation (baseline)
    rho_unadjusted, _ = spearman_overlap_vs_severity(df['tox_overlap'].values, df['severity'].values)

    # ── 5. Partial Spearman checks
    add_risk = df['additive_risk'].values
    sev = df['severity'].values.astype(float)
    tox_ov = df['tox_overlap'].values

    rho_partial_add = partial_spearman(tox_ov, sev, add_risk)

    if HAS_RDKIT and df['fp_tanimoto'].notna().all():
        tan = df['fp_tanimoto'].values
        rho_partial_tan = partial_spearman(tox_ov, sev, tan)
        # Full partial: residualize against both tan and additive; use sequential residuals
        from scipy.stats import rankdata
        rx = rankdata(tox_ov)
        ry = rankdata(sev)
        rz1 = rankdata(tan)
        rz2 = rankdata(add_risk)
        Z = np.column_stack([np.ones(len(rx)), rz1, rz2])

        def _resid(r):
            b, *_ = np.linalg.lstsq(Z, r, rcond=None)
            return r - Z @ b

        ex, ey = _resid(rx), _resid(ry)
        rho_partial_full = float(np.corrcoef(ex, ey)[0, 1]) if (np.ptp(ex) > 1e-12 and np.ptp(ey) > 1e-12) else float('nan')
    else:
        rho_partial_tan = float('nan')
        rho_partial_full = float('nan')

    # ── 6. OLS
    X, y, feat_names = _build_design_matrix(df)
    ols_res = ols_fit(X, y)

    tox_idx = feat_names.index('tox_overlap')
    print(f"\nOLS β(tox_overlap) = {ols_res['beta'][tox_idx]:+.4f} "
          f"(SE={ols_res['se'][tox_idx]:.4f}, p={_fmt_p(ols_res['p'][tox_idx])})")

    # ── 7. Drug-level bootstrap
    print(f"\nRunning drug-level bootstrap ({args.n_boot} replicates)...")
    boot_res = drug_level_bootstrap(df, n_boot=args.n_boot, seed=args.seed)
    print(f"95% CI for β(tox_overlap): [{boot_res['ci_lo']:+.4f}, {boot_res['ci_hi']:+.4f}]")

    # ── 8. Print summary to console
    print(f"\nUnadjusted ρ(tox_overlap, severity)  = {rho_unadjusted:+.4f}")
    print(f"Partial  ρ controlling additive_risk  = {rho_partial_add:+.4f}")
    if not np.isnan(rho_partial_tan):
        print(f"Partial  ρ controlling Tanimoto       = {rho_partial_tan:+.4f}")
        print(f"Partial  ρ controlling both           = {rho_partial_full:+.4f}")

    # ── 9. Write report
    report = write_report(
        df, ols_res, boot_res, feat_names,
        rho_unadjusted, rho_partial_tan, rho_partial_add, rho_partial_full,
        args,
    )
    report_path = os.path.join(args.out_dir, 'report.md')
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"\nReport written -> {report_path}")

    verdict = _verdict(boot_res['ci_lo'], boot_res['ci_lo'], boot_res['ci_hi'])
    beta_tox = ols_res['beta'][tox_idx]
    v = _verdict(beta_tox, boot_res['ci_lo'], boot_res['ci_hi'])
    print(f"\n{'='*60}")
    print(f"VERDICT: {v}")
    print('='*60)


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Controlled Tox21-overlap vs DDI-severity test")
    ap.add_argument('--data_dir', default='data',
                    help='Root data directory (default: data)')
    ap.add_argument('--out_dir', default='results/controlled_overlap',
                    help='Output directory for pairs.csv and report.md')
    ap.add_argument('--n_boot', type=int, default=2000,
                    help='Number of drug-level bootstrap replicates (default: 2000)')
    ap.add_argument('--min_joint', type=int, default=3,
                    help='Minimum jointly-tested endpoints to include a pair (default: 3)')
    ap.add_argument('--seed', type=int, default=0,
                    help='Random seed for bootstrap (default: 0)')
    return ap.parse_args(argv)


if __name__ == '__main__':
    run(parse_args())
