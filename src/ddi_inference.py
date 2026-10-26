"""
Inference-time glue for the dashboard.

* PairRiskExplainer   -- builds the "Why is this pair risky?" payload from the two
                         drugs' predicted Tox21 risk fingerprints.
* SymmetricPredictor  -- loads a trained SymmetricDDI variant (saved by
                         `python -m src.run_ablation --save_models`) together with its
                         conformal calibration, and answers either with a severity or
                         with an honest "uncertain" prediction set.

Everything degrades gracefully: if the new checkpoints or profile models are missing,
the app keeps working with the original DualEncoderDDI model and simply omits the new
panels (the callers treat a None return as "feature unavailable").
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.ddi_conformal import ConformalModel, decide
from src.ddi_features import explain_shared_risk, generic_pair_features, TOX21_TASKS

LABELS = {0: 'Minor', 1: 'Moderate', 2: 'Major'}
# Structure-only 'A' is served by default: the ablation did not show that predicted-toxicity (B) or CYP (C/D)
# features improve severity prediction. DDI_VARIANT=B|C|D overrides this once a variant has earned it.
# B_shuf is a research control and is never served.
APP_VARIANT_PREFERENCE = ('A', 'B', 'D', 'C')


def find_available_variant(arch: str, models_dir: str = 'models') -> Optional[str]:
    """Pick which saved SymmetricDDI variant to serve. DDI_VARIANT env var overrides the default order."""
    forced = os.environ.get('DDI_VARIANT')
    candidates = (forced,) if forced else APP_VARIANT_PREFERENCE
    for v in candidates:
        if v in APP_VARIANT_PREFERENCE and os.path.exists(os.path.join(models_dir, f'ddi_sym_{v}_{arch}.pt')) \
                and os.path.exists(os.path.join(models_dir, f'ddi_sym_{v}_{arch}_conformal.json')):
            return v
    return None


class PairRiskExplainer:
    """Lazy, cached, thread-safe wrapper around the Tox21 RiskProfiler."""

    def __init__(self, arch: str = 'gcn', models_dir: str = 'models'):
        self.arch, self.models_dir = arch, models_dir
        self._profiler = None
        self._failed: Optional[str] = None
        self._cache: Dict[str, np.ndarray] = {}
        self._lock = threading.Lock()

    def _get_profiler(self):
        if self._profiler is None and self._failed is None:
            try:
                from src.risk_profile import RiskProfiler
                self._profiler = RiskProfiler.load('tox21', arch=self.arch, models_dir=self.models_dir)
            except Exception as e:                       # missing checkpoints, etc.
                self._failed = str(e)
        return self._profiler

    @property
    def unavailable_reason(self) -> Optional[str]:
        return self._failed

    @property
    def mode(self) -> Optional[str]:
        p = self._profiler
        return p.mode if p is not None else None

    def profile(self, smiles: str) -> Optional[np.ndarray]:
        with self._lock:
            if smiles in self._cache:
                return self._cache[smiles]
            prof = self._get_profiler()
            if prof is None:
                return None
            vec = prof.profile(smiles)
            if vec is not None:
                self._cache[smiles] = vec
            return vec

    def explain(self, smiles_a: str, smiles_b: str) -> Optional[Dict[str, Any]]:
        pa, pb = self.profile(smiles_a), self.profile(smiles_b)
        if pa is None or pb is None:
            return None
        out = explain_shared_risk(pa, pb)
        out['profiler_mode'] = self.mode
        out['profile_a'] = {t: float(v) for t, v in zip(TOX21_TASKS, pa)}
        out['profile_b'] = {t: float(v) for t, v in zip(TOX21_TASKS, pb)}
        if self.mode == 'single_model_leaky':
            out['caveat'] += (' Note: scores come from a single Tox21 model, so a drug that was in its '
                              'training data may look more certain than a new drug would.')
        return out


class SymmetricPredictor:
    """Serve one trained SymmetricDDI variant with conformal abstention."""

    def __init__(self, variant: str, arch: str, models_dir: str = 'models',
                 explainer: Optional[PairRiskExplainer] = None):
        import torch
        from src.ddi_model import SymmetricDDI

        self.variant, self.arch = variant, arch
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        base = os.path.join(models_dir, f'ddi_sym_{variant}_{arch}')
        ck = torch.load(base + '.pt', map_location=self.device, weights_only=False)
        cfg = ck['config']
        self.model = SymmetricDDI(arch=cfg['arch'], in_dim=cfg['in_dim'], edge_dim=cfg['edge_dim'],
                                  hidden_dim=cfg['hidden_dim'], num_outputs=cfg['num_outputs'],
                                  extra_dim=cfg.get('extra_dim', 0)).to(self.device)
        self.model.load_state_dict(ck['state_dict'])
        self.model.eval()
        with open(base + '_conformal.json') as f:
            self.conformal = ConformalModel.from_dict(json.load(f))

        self.needs_tox = variant in ('B', 'D')
        self.needs_cyp = variant in ('C', 'D')
        profiler_arch = ck.get('profiler_arch', 'gcn')
        self.explainer = explainer or PairRiskExplainer(arch=profiler_arch, models_dir=models_dir)
        self._cyp_profiler = None
        if self.needs_cyp:
            from src.risk_profile import RiskProfiler
            self._cyp_profiler = RiskProfiler.load('cyp', arch=profiler_arch, models_dir=models_dir,
                                                   allow_leaky_fallback=False)

    def _extra(self, smiles_a: str, smiles_b: str) -> Optional[np.ndarray]:
        parts: List[np.ndarray] = []
        if self.needs_tox:
            pa, pb = self.explainer.profile(smiles_a), self.explainer.profile(smiles_b)
            if pa is None or pb is None:
                raise RuntimeError("Toxicity profile unavailable for one of the drugs.")
            parts.append(generic_pair_features(pa, pb))
        if self.needs_cyp:
            ca, cb = self._cyp_profiler.profile(smiles_a), self._cyp_profiler.profile(smiles_b)
            if ca is None or cb is None:
                raise RuntimeError("CYP profile unavailable for one of the drugs.")
            parts.append(generic_pair_features(ca, cb))
        return np.concatenate(parts).astype(np.float32) if parts else None

    def predict(self, smiles_a: str, smiles_b: str) -> Dict[str, Any]:
        import torch
        from torch_geometric.data import Batch
        from src.featurize import smiles_to_graph

        ga, gb = smiles_to_graph(smiles_a), smiles_to_graph(smiles_b)
        if ga is None or gb is None:
            raise ValueError("Could not featurise one of the molecules.")
        extra = self._extra(smiles_a, smiles_b)

        with torch.no_grad():
            ex = torch.tensor(extra, dtype=torch.float, device=self.device).unsqueeze(0) if extra is not None else None
            logits = self.model(Batch.from_data_list([ga]).to(self.device),
                                Batch.from_data_list([gb]).to(self.device), ex)
            probs = torch.softmax(logits, dim=-1)[0].cpu().numpy()

        d = decide(self.conformal, probs[None, :])
        pred_set = [LABELS[k] for k in range(3) if bool(d['sets'][0, k])]
        return {
            'probabilities': [float(p) for p in probs],
            'argmax': int(np.argmax(probs)),
            'answered': bool(d['answered'][0]),
            'prediction_set': pred_set,
            'coverage_target': float(1 - self.conformal.alpha),
            'variant': self.variant,
        }
