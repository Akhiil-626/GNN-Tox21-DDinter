"""
Predicted-toxicity "risk fingerprints" and pairwise shared-risk features for DDI.

Idea (the project's headline contribution)
------------------------------------------
Existing mechanism-aware DDI models rely on curated facts about each drug
(known targets, enzymes, pathways) which do not exist for a brand-new drug.
Here every drug is instead summarised by a *risk fingerprint*: the 12 Tox21
assay probabilities predicted from its structure alone by the project's
Tox21 GNN. Two drugs that are both predicted to disturb the same biological
process may interact more severely; this module turns that intuition into
(a) symmetric numeric features for the severity model and (b) a human-readable
"why is this pair risky?" explanation for the dashboard.

Important honesty notes
-----------------------
* Tox21 assays are cell-based screens, mostly on environmental chemicals. They
  are a *proxy* signal for biological stress, not a clinical interaction
  mechanism. Whether the proxy helps severity prediction is an empirical
  question that run_ablation.py tests; it is never assumed.
* Everything here is order-independent: f(a, b) == f(b, a), enforced by tests.

This module depends only on numpy/scipy so it can be unit tested without
torch or RDKit.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np

# Keep in sync with src.dataset.TOX21_TASKS (checked by tests/test_ddi_novelty.py).
TOX21_TASKS: Tuple[str, ...] = (
    'NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-Aromatase', 'NR-ER', 'NR-ER-LBD',
    'NR-PPAR-gamma', 'SR-ARE', 'SR-ATAD5', 'SR-HSE', 'SR-MMP', 'SR-p53',
)
N_TASKS = len(TOX21_TASKS)

# Plain-language labels for the dashboard. These describe what each LAB ASSAY
# measures; they are not claims about a specific clinical interaction.
ENDPOINT_LABELS: Dict[str, str] = {
    'NR-AR': 'Androgen receptor activity',
    'NR-AR-LBD': 'Androgen receptor binding',
    'NR-AhR': 'Aryl hydrocarbon receptor activation (foreign-chemical sensing)',
    'NR-Aromatase': 'Aromatase enzyme inhibition (estrogen production)',
    'NR-ER': 'Estrogen receptor activity',
    'NR-ER-LBD': 'Estrogen receptor binding',
    'NR-PPAR-gamma': 'PPAR-gamma receptor activity (metabolic regulation)',
    'SR-ARE': 'Oxidative stress response',
    'SR-ATAD5': 'Genotoxic (DNA-stress) response',
    'SR-HSE': 'Heat-shock stress response',
    'SR-MMP': 'Mitochondrial stress (membrane potential loss)',
    'SR-p53': 'DNA-damage response (p53 pathway)',
}


def _as_profile(p: Sequence[float]) -> np.ndarray:
    arr = np.asarray(p, dtype=np.float64).reshape(-1)
    if arr.shape[0] != N_TASKS:
        raise ValueError(f"Risk profile must have {N_TASKS} entries, got {arr.shape[0]}.")
    if np.any(arr < -1e-9) or np.any(arr > 1 + 1e-9):
        raise ValueError("Risk profile entries must be probabilities in [0, 1].")
    return np.clip(arr, 0.0, 1.0)


def expected_shared_risk(pa: Sequence[float], pb: Sequence[float]) -> float:
    """
    Expected number of Tox21 endpoints on which BOTH drugs are active, assuming
    the two drugs' predicted activities are independent: sum_k pa_k * pb_k.
    Range [0, 12]. Symmetric by construction.
    """
    a, b = _as_profile(pa), _as_profile(pb)
    return float(np.sum(a * b))


def shared_flagged_count(pa: Sequence[float], pb: Sequence[float], threshold: float = 0.5) -> int:
    """Number of endpoints where both drugs are predicted active (probability >= threshold)."""
    a, b = _as_profile(pa), _as_profile(pb)
    return int(np.sum((a >= threshold) & (b >= threshold)))


def profile_cosine(pa: Sequence[float], pb: Sequence[float]) -> float:
    """Cosine similarity between two risk fingerprints (0 if either is all zeros)."""
    a, b = _as_profile(pa), _as_profile(pb)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def pair_feature_vector(pa: Sequence[float], pb: Sequence[float], threshold: float = 0.5) -> np.ndarray:
    """
    Order-independent feature vector for a drug pair (length 3*12 + 4 = 40):
        [ pa + pb (12) | |pa - pb| (12) | pa * pb (12) |
          expected_shared_risk, shared_flagged_count, cosine, max_endpoint_joint ]
    Swapping the two drugs gives an identical vector.
    """
    a, b = _as_profile(pa), _as_profile(pb)
    joint = a * b
    scalars = np.array([
        float(joint.sum()),
        float(shared_flagged_count(a, b, threshold)),
        profile_cosine(a, b),
        float(joint.max()),
    ])
    return np.concatenate([a + b, np.abs(a - b), joint, scalars]).astype(np.float32)


PAIR_FEATURE_DIM = 3 * N_TASKS + 4


def explain_shared_risk(pa: Sequence[float], pb: Sequence[float], threshold: float = 0.5,
                        top_k: int = 4) -> Dict[str, object]:
    """
    Build the dashboard's "Why is this pair risky?" payload.

    Returns a dict with:
      expected_shared: float            expected number of shared active endpoints
      shared_flagged: int               endpoints where both >= threshold
      level: 'none' | 'low' | 'elevated' | 'high'   coarse summary of overlap
      shared: list[ {task, label, prob_a, prob_b, joint} ]   top shared endpoints
      caveat: str                       standing honesty note
    Only endpoints where BOTH drugs have probability >= 0.3 are listed, so the
    panel never names a "shared risk" that one drug barely shows.
    """
    a, b = _as_profile(pa), _as_profile(pb)
    joint = a * b
    order = np.argsort(-joint)

    shared: List[Dict[str, object]] = []
    for idx in order:
        if len(shared) >= top_k:
            break
        if a[idx] >= 0.3 and b[idx] >= 0.3:
            task = TOX21_TASKS[int(idx)]
            shared.append({
                'task': task,
                'label': ENDPOINT_LABELS[task],
                'prob_a': float(a[idx]),
                'prob_b': float(b[idx]),
                'joint': float(joint[idx]),
            })

    expected = float(joint.sum())
    flagged = shared_flagged_count(a, b, threshold)
    if flagged >= 3 or expected >= 1.5:
        level = 'high'
    elif flagged >= 1 or expected >= 0.75:
        level = 'elevated'
    elif expected >= 0.25:
        level = 'low'
    else:
        level = 'none'

    return {
        'expected_shared': expected,
        'shared_flagged': flagged,
        'level': level,
        'shared': shared,
        'caveat': (
            'Experimental. Based on lab-assay risk scores predicted from structure alone. In our '
            'evaluation these scores did NOT improve severity prediction for new drugs, so treat this '
            'as a descriptive research signal, not a confirmed interaction mechanism or a clinical statement.'
        ),
    }


def spearman_overlap_vs_severity(overlaps: Sequence[float], labels: Sequence[int]) -> Tuple[float, float]:
    """
    Spearman rank correlation between a pair-level overlap score and the severity
    label (0/1/2). Returns (rho, p_value); (nan, nan) if either input is constant.
    """
    from scipy.stats import spearmanr
    o = np.asarray(overlaps, dtype=np.float64)
    y = np.asarray(labels, dtype=np.float64)
    if o.size < 3 or np.ptp(o) < 1e-12 or np.ptp(y) < 1e-12:
        return float('nan'), float('nan')
    rho, p = spearmanr(o, y)
    return float(rho), float(p)


def generic_pair_features(pa: Sequence[float], pb: Sequence[float], threshold: float = 0.5) -> np.ndarray:
    """
    Order-independent pair features for a risk profile of ANY length K (used for the
    5-dimensional CYP profile as well as the 12-dimensional Tox21 profile):
        [ pa + pb (K) | |pa - pb| (K) | pa * pb (K) | sum(pa*pb), n_both_flagged, cosine, max(pa*pb) ]
    Length is 3K + 4. Swapping the drugs gives an identical vector.
    """
    a = np.asarray(pa, dtype=np.float64).reshape(-1)
    b = np.asarray(pb, dtype=np.float64).reshape(-1)
    if a.shape != b.shape:
        raise ValueError("Profiles must have the same length.")
    if np.any(a < -1e-9) or np.any(a > 1 + 1e-9) or np.any(b < -1e-9) or np.any(b > 1 + 1e-9):
        raise ValueError("Profile entries must be probabilities in [0, 1].")
    a, b = np.clip(a, 0, 1), np.clip(b, 0, 1)
    joint = a * b
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    cos = float(np.dot(a, b) / (na * nb)) if na > 1e-12 and nb > 1e-12 else 0.0
    scalars = np.array([float(joint.sum()), float(np.sum((a >= threshold) & (b >= threshold))), cos,
                        float(joint.max()) if joint.size else 0.0])
    return np.concatenate([a + b, np.abs(a - b), joint, scalars]).astype(np.float32)


def generic_feature_dim(k: int) -> int:
    return 3 * k + 4


def partial_spearman(x: Sequence[float], y: Sequence[float], z: Sequence[float]) -> float:
    """
    Spearman correlation between x and y after removing the (rank-)linear effect of z from both.
    Returns nan if any input is constant or there are fewer than 4 observations.
    """
    from scipy.stats import rankdata
    x, y, z = (np.asarray(v, dtype=np.float64) for v in (x, y, z))
    if x.size < 4 or min(np.ptp(x), np.ptp(y), np.ptp(z)) < 1e-12:
        return float('nan')
    rx, ry, rz = rankdata(x), rankdata(y), rankdata(z)
    design = np.column_stack([np.ones_like(rz), rz])

    def resid(r):
        coef, *_ = np.linalg.lstsq(design, r, rcond=None)
        return r - design @ coef

    ex, ey = resid(rx), resid(ry)
    if np.ptp(ex) < 1e-12 or np.ptp(ey) < 1e-12:
        return float('nan')
    return float(np.corrcoef(ex, ey)[0, 1])


def overlap_diagnostics(profiles_a: Sequence[Sequence[float]], profiles_b: Sequence[Sequence[float]],
                        labels: Sequence[int]) -> Dict[str, float]:
    """
    Separates a genuine SHARED-risk signal from a plain "dangerous drugs pair with dangerous drugs" effect.

      rho_overlap   Spearman(expected shared risk, severity)               [pair-specific overlap]
      rho_additive  Spearman(mean risk of A + mean risk of B, severity)    [drug-level danger only]
      rho_partial   overlap vs severity AFTER removing the additive-risk effect

    If rho_partial is near zero, the overlap score adds nothing beyond how risky each drug is on its
    own. Note: pairs share drugs, so standard p-values overstate significance; judge by effect size.
    """
    pa = np.asarray([np.asarray(p, dtype=np.float64) for p in profiles_a])
    pb = np.asarray([np.asarray(p, dtype=np.float64) for p in profiles_b])
    overlap = np.sum(pa * pb, axis=1)
    additive = pa.mean(axis=1) + pb.mean(axis=1)
    rho_o, p_o = spearman_overlap_vs_severity(overlap, labels)
    rho_a, _ = spearman_overlap_vs_severity(additive, labels)
    return {'rho_overlap': rho_o, 'p_value': p_o, 'rho_additive': rho_a,
            'rho_partial': partial_spearman(overlap, labels, additive), 'n': int(len(labels))}
