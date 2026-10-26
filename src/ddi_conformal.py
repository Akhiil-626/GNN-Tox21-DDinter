"""
Split conformal prediction and selective ("I'm not sure") answering for
DDI severity (Minor / Moderate / Major).

What it does
------------
Given softmax probabilities from any severity model and a held-out calibration
set, it produces prediction SETS that contain the true severity with a chosen
probability (e.g. 90 %), and an abstain rule: answer only when the set holds a
single severity, otherwise say "uncertain".

Honest limits (also surfaced in the README)
-------------------------------------------
* The coverage guarantee needs calibration and test pairs to be exchangeable.
  Drug-level (S1/S2) evaluation violates this somewhat because test drugs are
  new; the calibration set is therefore drawn from validation DRUGS (also unseen
  during training) to keep the shift small, and empirical coverage on S0/S1/S2
  is always reported rather than assumed.
* Conformal prediction for DDI exists in the literature; it is included here as
  a safety feature of the checker, not claimed as a novel contribution.

Pure numpy; no torch dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np


@dataclass
class ConformalModel:
    """Calibrated thresholds. `qhat` is per-class when mondrian=True, else all equal."""
    alpha: float
    qhat: np.ndarray            # shape (num_classes,)
    mondrian: bool
    n_calibration: int

    def to_dict(self) -> Dict[str, object]:
        return {'alpha': self.alpha, 'qhat': self.qhat.tolist(),
                'mondrian': self.mondrian, 'n_calibration': self.n_calibration}

    @staticmethod
    def from_dict(d: Dict[str, object]) -> 'ConformalModel':
        return ConformalModel(alpha=float(d['alpha']), qhat=np.asarray(d['qhat'], dtype=np.float64),
                              mondrian=bool(d['mondrian']), n_calibration=int(d['n_calibration']))


def _conformal_quantile(scores: np.ndarray, alpha: float) -> float:
    """Finite-sample-corrected (1 - alpha) quantile of nonconformity scores."""
    n = scores.size
    if n == 0:
        return 1.0  # no calibration data -> include every class
    level = min(1.0, np.ceil((n + 1) * (1 - alpha)) / n)
    return float(np.quantile(scores, level, method='higher'))


def fit_conformal(probs_cal: np.ndarray, y_cal: np.ndarray, alpha: float = 0.1,
                  mondrian: bool = True, num_classes: int = 3) -> ConformalModel:
    """
    Calibrate thresholds with the LAC score s = 1 - p(true class).

    mondrian=True calibrates each TRUE class separately so the rare Minor class
    gets its own coverage guarantee instead of being sacrificed to Moderate.
    """
    probs_cal = np.asarray(probs_cal, dtype=np.float64)
    y_cal = np.asarray(y_cal, dtype=int)
    if probs_cal.ndim != 2 or probs_cal.shape[0] != y_cal.shape[0]:
        raise ValueError("probs_cal must be (n, K) and match y_cal.")
    if not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0, 1).")

    scores = 1.0 - probs_cal[np.arange(len(y_cal)), y_cal]
    if mondrian:
        qhat = np.array([_conformal_quantile(scores[y_cal == k], alpha) for k in range(num_classes)])
    else:
        qhat = np.full(num_classes, _conformal_quantile(scores, alpha))
    return ConformalModel(alpha=alpha, qhat=qhat, mondrian=mondrian, n_calibration=len(y_cal))


def predict_sets(model: ConformalModel, probs: np.ndarray) -> np.ndarray:
    """Boolean (n, K) matrix: class k is in the set when 1 - p_k <= qhat_k."""
    probs = np.asarray(probs, dtype=np.float64)
    return (1.0 - probs) <= model.qhat[None, :]


def decide(model: ConformalModel, probs: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Turn probabilities into answer / abstain decisions.

    Returns arrays:
      sets      (n, K) bool   conformal prediction sets
      answered  (n,)   bool   True when the set holds exactly one class
      label     (n,)   int    the single class when answered, else -1
    Empty sets and multi-class sets both abstain.
    """
    sets = predict_sets(model, probs)
    sizes = sets.sum(axis=1)
    answered = sizes == 1
    label = np.where(answered, sets.argmax(axis=1), -1)
    return {'sets': sets, 'answered': answered, 'label': label}


def evaluate_conformal(model: ConformalModel, probs: np.ndarray, y_true: np.ndarray) -> Dict[str, float]:
    """
    Empirical performance on a test set:
      coverage            share of pairs whose true severity is in the set
      avg_set_size        mean number of severities in the set
      answer_rate         share of pairs answered (single-class set)
      answered_accuracy   accuracy on answered pairs only (nan if none answered)
      baseline_accuracy   plain argmax accuracy on ALL pairs, for comparison
    """
    probs = np.asarray(probs, dtype=np.float64)
    y_true = np.asarray(y_true, dtype=int)
    d = decide(model, probs)
    sets, answered, label = d['sets'], d['answered'], d['label']

    covered = sets[np.arange(len(y_true)), y_true]
    n_answered = int(answered.sum())
    return {
        'n': int(len(y_true)),
        'coverage': float(covered.mean()) if len(y_true) else float('nan'),
        'target_coverage': float(1 - model.alpha),
        'avg_set_size': float(sets.sum(axis=1).mean()) if len(y_true) else float('nan'),
        'answer_rate': float(answered.mean()) if len(y_true) else float('nan'),
        'answered_accuracy': float((label[answered] == y_true[answered]).mean()) if n_answered else float('nan'),
        'baseline_accuracy': float((probs.argmax(axis=1) == y_true).mean()) if len(y_true) else float('nan'),
    }


def confidence_threshold_curve(probs: np.ndarray, y_true: np.ndarray,
                               thresholds: Optional[np.ndarray] = None) -> Dict[str, np.ndarray]:
    """
    Simple selective-prediction curve (no calibration set needed): answer only when
    max probability >= t. Returns arrays of thresholds, coverage (answer rate) and accuracy.
    """
    probs = np.asarray(probs, dtype=np.float64)
    y_true = np.asarray(y_true, dtype=int)
    if thresholds is None:
        thresholds = np.linspace(0.34, 0.95, 25)
    conf = probs.max(axis=1)
    pred = probs.argmax(axis=1)
    cov, acc = [], []
    for t in thresholds:
        keep = conf >= t
        cov.append(float(keep.mean()))
        acc.append(float((pred[keep] == y_true[keep]).mean()) if keep.any() else float('nan'))
    return {'threshold': np.asarray(thresholds), 'coverage': np.asarray(cov), 'accuracy': np.asarray(acc)}
