"""
RiskProfiler: turn a drug's structure into a "risk fingerprint".

    task='tox21'  ->  12 probabilities, one per Tox21 assay endpoint
    task='cyp'    ->  up to 5 probabilities, one per CYP enzyme inhibition endpoint

Two operating modes
-------------------
crossfit (preferred, honest)
    Uses the K fold models from `python -m src.crossfit`. A drug that appears in the
    labelled training table is profiled ONLY by the fold model that never saw it;
    every other drug gets the mean of all K models. This keeps the features seen
    during DDI training statistically comparable to those of a genuinely new drug.

single_model_leaky (fallback, tox21 only)
    Falls back to the project's existing models/best_{arch}.pt. Drugs that are also in
    the Tox21 training set get overly accurate profiles, which can inflate DDI
    results. The profiler flags this via `.leaky = True` and run_ablation.py prints a
    loud warning and records it in the results file.

torch is imported lazily so the pure selection logic can be unit tested without it.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Sequence

import numpy as np


def select_crossfit_predictions(per_model: np.ndarray, keys: Sequence[Optional[str]],
                                fold_of: Dict[str, int]) -> np.ndarray:
    """
    Pick the right prediction for every molecule.

    per_model : array (K, N, T) -- probabilities from each of K fold models.
    keys      : length-N canonical SMILES keys (None for unparseable molecules).
    fold_of   : canonical key -> fold index of the model that did NOT train on it.

    A molecule found in `fold_of` uses only that fold's model; any other molecule uses
    the mean over all K models. Returns (N, T).
    """
    per_model = np.asarray(per_model, dtype=np.float64)
    k, n, t = per_model.shape
    if len(keys) != n:
        raise ValueError("keys must have one entry per molecule.")
    out = per_model.mean(axis=0)
    for i, key in enumerate(keys):
        if key is not None and key in fold_of:
            f = fold_of[key]
            if not 0 <= f < k:
                raise ValueError(f"fold index {f} out of range for {k} models")
            out[i] = per_model[f, i]
    return out


class RiskProfiler:
    def __init__(self, task: str, models: List, task_names: List[str],
                 fold_of: Optional[Dict[str, int]] = None, device=None, leaky: bool = False):
        self.task = task
        self.models = models
        self.task_names = list(task_names)
        self.fold_of = fold_of or {}
        self.device = device
        self.leaky = leaky
        self.mode = 'single_model_leaky' if leaky else 'crossfit'

    @property
    def dim(self) -> int:
        return len(self.task_names)

    # ------------------------------------------------------------------ construction
    @classmethod
    def load(cls, task: str = 'tox21', arch: str = 'gcn', models_dir: str = 'models',
             allow_leaky_fallback: bool = True) -> 'RiskProfiler':
        import torch
        from src.model import get_model

        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        folds_path = os.path.join(models_dir, f'crossfit_{task}_{arch}_folds.json')
        if os.path.exists(folds_path):
            with open(folds_path) as f:
                meta = json.load(f)
            models = []
            for k in range(int(meta['folds'])):
                ck = torch.load(os.path.join(models_dir, f'crossfit_{task}_{arch}_fold{k}.pt'),
                                map_location=device, weights_only=False)
                cfg = ck['config']
                m = get_model(cfg['arch'], in_dim=cfg['in_dim'], edge_dim=cfg['edge_dim'],
                              hidden_dim=cfg['hidden_dim'], num_tasks=cfg['num_tasks']).to(device)
                m.load_state_dict(ck['state_dict'])
                m.eval()
                models.append(m)
            return cls(task, models, meta['task_names'], meta['fold_of'], device, leaky=False)

        if task != 'tox21' or not allow_leaky_fallback:
            raise FileNotFoundError(
                f"No cross-fitted '{task}' models for {arch} in '{models_dir}'. Train them with: "
                f"python -m src.crossfit --task {task} --arch {arch} --folds 5"
                + (" --cyp_dir data/cyp" if task == 'cyp' else "")
            )

        path = os.path.join(models_dir, f'best_{arch}.pt')
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Neither cross-fitted nor single Tox21 model found for {arch}. Run "
                f"`python -m src.crossfit --task tox21 --arch {arch}` (preferred) or "
                f"`python -m src.train --arch {arch}`."
            )
        ck = torch.load(path, map_location=device, weights_only=False)
        cfg = ck['config']
        m = get_model(cfg.get('arch', arch), in_dim=cfg.get('in_dim', 72), edge_dim=cfg.get('edge_dim', 6),
                      hidden_dim=cfg.get('hidden_dim', 128), num_tasks=12).to(device)
        m.load_state_dict(ck['state_dict'])
        m.eval()
        from src.ddi_features import TOX21_TASKS
        return cls('tox21', [m], list(TOX21_TASKS), None, device, leaky=True)

    # ------------------------------------------------------------------ inference
    def _predict_all(self, graphs: List, batch_size: int) -> np.ndarray:
        """(K, N, T) probabilities for already-featurised graphs."""
        import torch
        from torch_geometric.loader import DataLoader
        from src.model import MPNNModel

        loader = DataLoader(graphs, batch_size=batch_size, shuffle=False)
        outs = []
        with torch.no_grad():
            for model in self.models:
                model.eval()
                chunks = []
                for batch in loader:
                    batch = batch.to(self.device)
                    if isinstance(model, MPNNModel):
                        logits = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
                    else:
                        logits = model(batch.x, batch.edge_index, batch.batch)
                    chunks.append(torch.sigmoid(logits).cpu().numpy())
                outs.append(np.vstack(chunks))
        return np.stack(outs)

    def profile_many(self, smiles_list: Sequence[str], batch_size: int = 128) -> Dict[str, Optional[np.ndarray]]:
        """Map each input SMILES to its profile (None if the SMILES cannot be parsed)."""
        from src.chem_utils import canonical_key
        from src.featurize import smiles_to_graph

        unique = list(dict.fromkeys(smiles_list))
        graphs, ok_smiles = [], []
        for s in unique:
            g = smiles_to_graph(s)
            if g is not None:
                graphs.append(g)
                ok_smiles.append(s)

        result: Dict[str, Optional[np.ndarray]] = {s: None for s in unique}
        if not graphs:
            return result

        per_model = self._predict_all(graphs, batch_size)
        keys = [canonical_key(s) for s in ok_smiles]
        if self.mode == 'crossfit':
            final = select_crossfit_predictions(per_model, keys, self.fold_of)
        else:
            final = per_model.mean(axis=0)
        for s, row in zip(ok_smiles, final):
            result[s] = np.clip(row, 0.0, 1.0).astype(np.float64)
        return result

    def profile(self, smiles: str) -> Optional[np.ndarray]:
        return self.profile_many([smiles])[smiles]

    def in_training_table(self, smiles: str) -> bool:
        """True if this molecule belonged to the labelled table (so a fold model excluded it)."""
        from src.chem_utils import canonical_key
        key = canonical_key(smiles)
        return key is not None and key in self.fold_of
