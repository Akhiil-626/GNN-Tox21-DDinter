"""
Synthetic stand-in data for exercising the ablation pipeline end to end.

!!  NEVER report results from this module as findings.  !!

Real DDInter / Tox21 data need a network connection and a trained GNN. This module
fabricates drugs with hidden latent properties so the *pipeline* (splits, baselines,
paired statistics, conformal abstention, report) can be tested anywhere in seconds.
Two independent knobs control what is planted:

* `tox_signal`      how much severity depends on SHARED predicted toxicity (the pair effect).
* `tox_from_latent` whether each drug's toxicity profile is derived from the same hidden
                    properties that drive its "dangerousness". When True the profile is an
                    informative (denoised) view of the drug even with tox_signal=0, so a
                    pipeline SHOULD find a benefit. For a genuine NULL (profiles carry no
                    information about severity at all) use tox_from_latent=False and
                    tox_signal=0: a correct pipeline must then not report an improvement.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def make_synthetic_experiment(n_drugs: int = 150, n_pairs: int = 2500, seed: int = 0,
                              tox_signal: float = 0.6, n_bits: int = 256,
                              tox_from_latent: bool = True,
                              class_quantiles=(0.12, 0.70)):
    """
    Returns (pairs, tox, cyp, fps):
      pairs : list of (name_a, name_b, severity_label in {0,1,2}); unique unordered pairs
      tox   : name -> 12-d probability vector
      cyp   : name -> 5-d probability vector (planted with NO relation to severity)
      fps   : name -> binary fingerprint vector (carries structure signal about the latent drug type)
    """
    rng = np.random.default_rng(seed)
    names = [f"syn{i:04d}" for i in range(n_drugs)]
    z = rng.normal(size=(n_drugs, 6))                      # hidden drug properties

    fp_logits = z @ rng.normal(size=(6, n_bits)) + rng.normal(0, 1.5, (n_drugs, n_bits))
    fps = (fp_logits > 1.0).astype(np.float32)

    if tox_from_latent:
        tox_mat = _sigmoid(0.9 * (z @ rng.normal(size=(6, 12))) + rng.normal(0, 0.7, (n_drugs, 12)))
    else:
        tox_mat = _sigmoid(rng.normal(0, 1.0, (n_drugs, 12)))   # unrelated to z -> no information
    cyp_mat = _sigmoid(rng.normal(size=(n_drugs, 5)))      # pure noise w.r.t. severity

    seen, raw = set(), []
    while len(raw) < n_pairs:
        i, j = rng.choice(n_drugs, 2, replace=False)
        key = (min(i, j), max(i, j))
        if key in seen:
            continue
        seen.add(key)
        danger = 0.35 * (z[i, 0] + z[j, 0])
        shared = tox_signal * float(np.sum(tox_mat[i] * tox_mat[j])) / 3.0
        raw.append((i, j, danger + shared + rng.normal(0, 0.5)))

    scores = np.array([r[2] for r in raw])
    lo, hi = np.quantile(scores, list(class_quantiles))   # default ~12% minor, ~58% moderate, ~30% major
    pairs: List[Tuple[str, str, int]] = []
    for (i, j, s) in raw:
        label = 0 if s < lo else (1 if s < hi else 2)
        pairs.append((names[i], names[j], label))

    tox: Dict[str, np.ndarray] = {n: tox_mat[k] for k, n in enumerate(names)}
    cyp: Dict[str, np.ndarray] = {n: cyp_mat[k] for k, n in enumerate(names)}
    fp_dict: Dict[str, np.ndarray] = {n: fps[k] for k, n in enumerate(names)}
    return pairs, tox, cyp, fp_dict
