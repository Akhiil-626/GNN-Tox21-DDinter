"""
Non-GNN baselines for DDI severity prediction.

Why baselines matter
--------------------
A severity model is only interesting if it beats cheap alternatives. Two are
critical:

* DrugMeanBaseline  -- uses NO chemistry at all. It remembers how severe each
  drug's interactions were on average in the training data. If the GNN cannot
  beat this, it has merely learned "this drug is generally dangerous". For a
  brand-new drug (S2) it can only fall back to the class prior, which is exactly
  the point: any gain over it on S1/S2 must come from structure.
* FingerprintForestBaseline -- a classical Morgan-fingerprint random forest on
  order-independent pair features (fa+fb, |fa-fb|).

Both are order-independent and need only numpy/scikit-learn (fingerprint
generation needs RDKit but is isolated in morgan_fingerprint()).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

LEVELS = ('Minor', 'Moderate', 'Major')


def morgan_fingerprint(smiles: str, radius: int = 2, n_bits: int = 1024) -> Optional[np.ndarray]:
    """Morgan (ECFP-like) bit vector. Returns None if RDKit is missing or the SMILES is invalid."""
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
    except ImportError:
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=np.float32)
    for bit in fp.GetOnBits():
        arr[bit] = 1.0
    return arr


def score_predictions(y_true: Sequence[int], y_pred: Sequence[int]) -> Dict[str, float]:
    """Accuracy, macro-F1 and per-class F1 (zero_division=0 so empty classes give 0, not NaN)."""
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    out = {
        'accuracy': float(accuracy_score(y_true, y_pred)) if len(y_true) else float('nan'),
        'macro_f1': float(f1_score(y_true, y_pred, average='macro', labels=[0, 1, 2], zero_division=0))
        if len(y_true) else float('nan'),
    }
    per_class = f1_score(y_true, y_pred, average=None, labels=[0, 1, 2], zero_division=0) \
        if len(y_true) else [float('nan')] * 3
    for name, val in zip(LEVELS, per_class):
        out[f'{name.lower()}_f1'] = float(val)
    return out


class PriorBaseline:
    """Always predicts the most frequent training class. The floor every model must clear."""

    def fit(self, pairs: Sequence[Tuple[str, str, int]]) -> 'PriorBaseline':
        counts = np.bincount([y for _, _, y in pairs], minlength=3)
        self.prior_ = counts / max(counts.sum(), 1)
        self.majority_ = int(np.argmax(counts))
        return self

    def predict_proba(self, pairs: Sequence[Tuple[str, str]]) -> np.ndarray:
        return np.tile(self.prior_, (len(pairs), 1))

    def predict(self, pairs: Sequence[Tuple[str, str]]) -> np.ndarray:
        return np.full(len(pairs), self.majority_, dtype=int)


class DrugMeanBaseline:
    """
    Chemistry-free baseline built from per-drug average severity, with an explicit back-off.

    How a pair is answered depends on how many of its drugs were seen in training:
      both known  -> logistic regression on [mean_a + mean_b, |mean_a - mean_b|]
      one known   -> the SAME model, with the unseen partner imputed as the population-mean drug
      none known  -> the training class prior (no information is available)

    Training uses LEAVE-ONE-PAIR-OUT drug means: a pair's own label is removed from both drugs'
    averages, otherwise the model would see its own answer. Imputing the population mean for an
    unseen partner is a standard missing-value treatment and gave a clearly stronger floor than
    training a separate one-drug model (0.47 vs 0.39 macro-F1 in synthetic checks); a stronger
    floor makes any claim that chemistry adds value more conservative.

    History: an earlier version fed "number of known drugs" to a single model trained almost only
    on both-known pairs. On new drugs (S1/S2) it extrapolated arbitrarily and scored below the
    majority-class floor (e.g. 0.18 accuracy against a 0.73 floor on real DDInter data).

    All features are symmetric, so f(A, B) == f(B, A).
    """

    def __init__(self) -> None:
        self.both_ = None

    def _stats(self, pairs: Sequence[Tuple[str, str, int]]) -> None:
        self.sum_ = defaultdict(float)
        self.cnt_ = defaultdict(int)
        for a, b, y in pairs:
            for d in (a, b):
                self.sum_[d] += y
                self.cnt_[d] += 1
        counts = np.bincount([y for _, _, y in pairs], minlength=3).astype(float)
        self.prior_ = counts / max(counts.sum(), 1.0)
        self.global_mean_ = float(sum(y for _, _, y in pairs) / max(len(pairs), 1))

    def _mean(self, d: str, drop_label: Optional[int] = None) -> Optional[float]:
        """Average severity of drug d (optionally with one pair's label removed); None if unknown."""
        s, c = self.sum_.get(d, 0.0), self.cnt_.get(d, 0)
        if drop_label is not None:
            s, c = s - drop_label, c - 1
        return s / c if c > 0 else None

    def _known_means(self, a: str, b: str, drop_label: Optional[int] = None) -> List[float]:
        return [m for m in (self._mean(a, drop_label), self._mean(b, drop_label)) if m is not None]

    def fit(self, pairs: Sequence[Tuple[str, str, int]]) -> 'DrugMeanBaseline':
        self._stats(pairs)
        X, y_all = [], []
        for a, b, y in pairs:
            ma, mb = self._mean(a, y), self._mean(b, y)       # leave-one-pair-out
            if ma is not None and mb is not None:
                X.append([ma + mb, abs(ma - mb)])
                y_all.append(y)
        self.both_ = None
        if len(set(y_all)) >= 2:                              # otherwise the prior is all we can offer
            self.both_ = LogisticRegression(max_iter=1000, class_weight='balanced').fit(
                np.array(X), np.array(y_all))
        return self

    def predict_proba(self, pairs: Sequence[Tuple[str, str]]) -> np.ndarray:
        out = np.tile(self.prior_, (len(pairs), 1))
        idx, X = [], []
        for i, (a, b) in enumerate(pairs):
            known = self._known_means(a, b)
            if len(known) == 2:
                idx.append(i)
                X.append([known[0] + known[1], abs(known[0] - known[1])])
            elif len(known) == 1:
                idx.append(i)
                m, g = known[0], self.global_mean_
                X.append([m + g, abs(m - g)])
        if idx and self.both_ is not None:
            raw = self.both_.predict_proba(np.array(X))
            full = np.zeros((len(idx), 3))
            for col, cls in enumerate(self.both_.classes_):
                full[:, int(cls)] = raw[:, col]
            out[idx] = full
        return out

    def predict(self, pairs: Sequence[Tuple[str, str]]) -> np.ndarray:
        return self.predict_proba(pairs).argmax(axis=1)


class FingerprintForestBaseline:
    """Random forest on symmetric Morgan-fingerprint pair features [fa + fb, |fa - fb|]."""

    def __init__(self, n_estimators: int = 300, random_state: int = 0) -> None:
        self.rf = RandomForestClassifier(
            n_estimators=n_estimators, class_weight='balanced_subsample',
            n_jobs=-1, random_state=random_state,
        )

    @staticmethod
    def _pair_vec(fa: np.ndarray, fb: np.ndarray) -> np.ndarray:
        return np.concatenate([fa + fb, np.abs(fa - fb)])

    def fit(self, pairs: Sequence[Tuple[str, str, int]], fps: Dict[str, np.ndarray]) -> 'FingerprintForestBaseline':
        X = np.stack([self._pair_vec(fps[a], fps[b]) for a, b, _ in pairs])
        y = np.array([y for _, _, y in pairs])
        self.rf.fit(X, y)
        return self

    def predict_proba(self, pairs: Sequence[Tuple[str, str]], fps: Dict[str, np.ndarray]) -> np.ndarray:
        X = np.stack([self._pair_vec(fps[a], fps[b]) for a, b in pairs])
        raw = self.rf.predict_proba(X)
        full = np.zeros((len(pairs), 3))
        for col, cls in enumerate(self.rf.classes_):
            full[:, int(cls)] = raw[:, col]
        return full

    def predict(self, pairs: Sequence[Tuple[str, str]], fps: Dict[str, np.ndarray]) -> np.ndarray:
        return self.predict_proba(pairs, fps).argmax(axis=1)


class PairFeatureForest:
    """
    Random forest on any precomputed, order-independent pair-feature matrix.

    Used for the fast tabular ablation: fingerprint features alone versus fingerprint
    features plus predicted-toxicity (or shuffled-control) features. Needs no torch,
    so it answers "do the risk fingerprints carry any signal?" in minutes on a CPU.
    """

    def __init__(self, n_estimators: int = 300, random_state: int = 0) -> None:
        self.rf = RandomForestClassifier(
            n_estimators=n_estimators, class_weight='balanced_subsample',
            n_jobs=-1, random_state=random_state, min_samples_leaf=2,
        )

    def fit(self, X: np.ndarray, y: Sequence[int]) -> 'PairFeatureForest':
        self.rf.fit(np.asarray(X), np.asarray(y, dtype=int))
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        raw = self.rf.predict_proba(np.asarray(X))
        full = np.zeros((raw.shape[0], 3))
        for col, cls in enumerate(self.rf.classes_):
            full[:, int(cls)] = raw[:, col]
        return full

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.predict_proba(X).argmax(axis=1)
