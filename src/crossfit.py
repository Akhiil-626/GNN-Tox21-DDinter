"""
Cross-fitted property models: honest "risk fingerprints" for the DDI study.

The leakage problem this solves
-------------------------------
The DDI severity model consumes each drug's predicted Tox21 (and optionally CYP)
profile. Many approved drugs appear in Tox21 itself. If a Tox21 model that was
TRAINED on a drug is asked to profile that same drug, it returns something close
to the true lab result; a genuinely new drug only gets a prediction. The severity
model would then learn from unrealistically good features and look better than it
will be on new drugs.

Cross-fitting removes that mismatch. The labelled molecules are split by scaffold
into K folds; model k is trained on the OTHER folds. A molecule that belongs to
fold k is always profiled by model k (which never saw it); molecules outside the
labelled set are profiled by the average of all K models.

Outputs (per task, per architecture):
    models/crossfit_{task}_{arch}_fold{k}.pt     K checkpoints
    models/crossfit_{task}_{arch}_folds.json     canonical SMILES -> fold index
    results/crossfit_{task}_{arch}.csv           held-out mean ROC-AUC per fold
                                                 (an honest scaffold-style estimate)

Usage:
    python -m src.crossfit --task tox21 --arch gcn --folds 5 --epochs 25
    python -m src.crossfit --task cyp   --arch gcn --folds 5 --epochs 25 --cyp_dir data/cyp

CYP data are NOT downloaded automatically (no network assumptions). Put the five
Therapeutics Data Commons CYP files (Veith et al.) in --cyp_dir, e.g.
CYP3A4_Veith.csv, each with a SMILES column named Drug (or smiles) and a binary
label column Y.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.metrics import roc_auc_score
from torch_geometric.loader import DataLoader
from tqdm import tqdm

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.chem_utils import CYP_ISOFORMS, balanced_group_folds, canonical_key
from src.featurize import smiles_to_graph
from src.model import MPNNModel, get_model


# ----------------------------------------------------------------------------- data
def load_tox21_table(data_dir: str = 'data') -> Tuple[List[str], np.ndarray, List[str]]:
    """Return (smiles, labels[N, 12] with NaN for missing, task_names)."""
    from src.dataset import TOX21_TASKS, download_tox21_data
    csv_path = download_tox21_data(os.path.join(data_dir, 'raw'))
    df = pd.read_csv(csv_path)
    tasks = [t for t in TOX21_TASKS if t in df.columns]
    return df['smiles'].tolist(), df[tasks].to_numpy(dtype=float), tasks


def load_cyp_table(cyp_dir: str) -> Tuple[List[str], np.ndarray, List[str]]:
    """
    Merge per-isoform CSVs (TDC / Veith format) into one multi-label table keyed by
    canonical SMILES. Missing isoform labels are NaN.
    """
    labels_by_key: Dict[str, Dict[str, float]] = {}
    smiles_by_key: Dict[str, str] = {}
    found: List[str] = []

    for iso in CYP_ISOFORMS:
        matches = sorted(glob.glob(os.path.join(cyp_dir, f'{iso}*.csv')))
        if not matches:
            continue
        df = pd.read_csv(matches[0])
        smi_col = next((c for c in ('Drug', 'smiles', 'SMILES', 'Smiles') if c in df.columns), None)
        if smi_col is None or 'Y' not in df.columns:
            raise ValueError(f"{matches[0]} needs a SMILES column (Drug/smiles) and a label column Y.")
        found.append(iso)
        for smi, y in zip(df[smi_col], df['Y']):
            key = canonical_key(smi)
            if key is None or pd.isna(y):
                continue
            smiles_by_key.setdefault(key, smi)
            labels_by_key.setdefault(key, {})[iso] = float(y)

    if len(found) < 2:
        raise FileNotFoundError(
            f"Found {len(found)} CYP files in '{cyp_dir}'. Expected files named like "
            f"CYP3A4_Veith.csv for at least two of {list(CYP_ISOFORMS)}."
        )
    keys = sorted(labels_by_key)
    y = np.full((len(keys), len(found)), np.nan)
    for i, k in enumerate(keys):
        for j, iso in enumerate(found):
            if iso in labels_by_key[k]:
                y[i, j] = labels_by_key[k][iso]
    return [smiles_by_key[k] for k in keys], y, found


def build_graphs(smiles: List[str], labels: np.ndarray) -> Tuple[List, List[int]]:
    """Featurise molecules; returns (graphs, original_indices) for the ones that parsed."""
    graphs, kept = [], []
    for i, (smi, y) in enumerate(zip(smiles, labels)):
        g = smiles_to_graph(smi, y=[float(v) if not np.isnan(v) else float('nan') for v in y])
        if g is not None:
            graphs.append(g)
            kept.append(i)
    return graphs, kept


# ----------------------------------------------------------------------------- training
def _forward(model, batch):
    if isinstance(model, MPNNModel):
        return model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
    return model(batch.x, batch.edge_index, batch.batch)


def _pos_weights(graphs, num_tasks: int, cap: float = 10.0) -> torch.Tensor:
    y = torch.vstack([g.y.view(num_tasks) for g in graphs])
    w = []
    for t in range(num_tasks):
        col = y[:, t]
        ok = ~torch.isnan(col)
        n_pos = float((col[ok] == 1).sum())
        n_neg = float((col[ok] == 0).sum())
        w.append(min(n_neg / max(n_pos, 1.0), cap))
    return torch.tensor(w, dtype=torch.float)


def _train_epoch(model, loader, opt, device, pos_weight, num_tasks,
                 epoch: Optional[int] = None, epochs: Optional[int] = None,
                 fold: Optional[int] = None, total_folds: Optional[int] = None) -> float:
    model.train()
    total, count = 0.0, 0
    fold_str = f"Fold {fold+1}/{total_folds} " if (fold is not None and total_folds is not None) else ""
    ep_str = f"Ep {epoch:02d}/{epochs:02d}" if (epoch is not None and epochs is not None) else "Training"
    desc = f"  {fold_str}{ep_str}"
    pbar = tqdm(loader, desc=desc, leave=False, dynamic_ncols=True)
    for batch in pbar:
        batch = batch.to(device)
        opt.zero_grad()
        logits = _forward(model, batch)
        y = batch.y.view(-1, num_tasks)
        mask = ~torch.isnan(y)
        if mask.sum() == 0:
            continue
        w = pos_weight.unsqueeze(0).expand_as(y)
        loss = F.binary_cross_entropy_with_logits(logits[mask], y[mask], pos_weight=w[mask])
        loss.backward()
        opt.step()
        n_masked = int(mask.sum())
        total += loss.item() * n_masked
        count += n_masked
        pbar.set_postfix({'loss': f"{loss.item():.4f}", 'avg': f"{total / max(count, 1):.4f}"})
    return total / max(count, 1)


@torch.no_grad()
def _mean_auc(model, loader, device, num_tasks, desc: Optional[str] = None) -> float:
    model.eval()
    ys, ps = [], []
    iterator = tqdm(loader, desc=f"  {desc}", leave=False, dynamic_ncols=True) if desc else loader
    for batch in iterator:
        batch = batch.to(device)
        ps.append(torch.sigmoid(_forward(model, batch)).cpu().numpy())
        ys.append(batch.y.view(-1, num_tasks).cpu().numpy())
    y, p = np.vstack(ys), np.vstack(ps)
    aucs = []
    for t in range(num_tasks):
        ok = ~np.isnan(y[:, t])
        if ok.sum() > 0 and len(np.unique(y[ok, t])) == 2:
            aucs.append(roc_auc_score(y[ok, t], p[ok, t]))
    return float(np.mean(aucs)) if aucs else float('nan')


def run_crossfit(task: str, arch: str = 'gcn', folds: int = 5, epochs: int = 25, batch_size: int = 64,
                 lr: float = 1e-3, hidden_dim: int = 128, seed: int = 0, data_dir: str = 'data',
                 cyp_dir: str = 'data/cyp', save_dir: str = 'models') -> pd.DataFrame:
    """Train K fold models for `task` ('tox21' or 'cyp') and write checkpoints + fold map."""
    from src.dataset import generate_scaffold

    if task == 'tox21':
        smiles, labels, task_names = load_tox21_table(data_dir)
    elif task == 'cyp':
        smiles, labels, task_names = load_cyp_table(cyp_dir)
    else:
        raise ValueError("task must be 'tox21' or 'cyp'")
    num_tasks = len(task_names)

    graphs, kept = build_graphs(smiles, labels)
    smiles = [smiles[i] for i in kept]
    print(f"\n=======================================================", flush=True)
    print(f" Starting K-Fold Cross-Fitting: Task [{task.upper()}] with {arch.upper()}", flush=True)
    print(f"=======================================================", flush=True)
    print(f" Device          : {device}", flush=True)
    print(f" Total Folds     : {folds} | Epochs per fold: {epochs} | Batch Size: {batch_size}", flush=True)
    print(f" Molecules       : {len(graphs)} across {num_tasks} tasks: {task_names}", flush=True)
    print(f"=======================================================\n", flush=True)

    rows = []

    for k in range(folds):
        held = [i for i, f in enumerate(fold_of_idx) if f == k]
        rest = [i for i, f in enumerate(fold_of_idx) if f != k]
        # 10% of the remaining scaffolds become the validation set for checkpoint selection.
        sub = balanced_group_folds([scaffolds[i] for i in rest], 10, seed=seed + 1 + k)
        val = [rest[j] for j, f in enumerate(sub) if f == 0]
        train = [rest[j] for j, f in enumerate(sub) if f != 0]

        tr_loader = DataLoader([graphs[i] for i in train], batch_size=batch_size, shuffle=True)
        va_loader = DataLoader([graphs[i] for i in val], batch_size=batch_size)
        ho_loader = DataLoader([graphs[i] for i in held], batch_size=batch_size)

        model = get_model(arch, in_dim=in_dim, edge_dim=edge_dim, hidden_dim=hidden_dim, num_tasks=num_tasks).to(device)
        opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
        pos_w = _pos_weights([graphs[i] for i in train], num_tasks).to(device)

        print(f">>> [Fold {k+1}/{folds}] Train: {len(train)} graphs ({len(tr_loader)} batches) | "
              f"Val: {len(val)} graphs ({len(va_loader)} batches) | "
              f"Held-out: {len(held)} graphs", flush=True)

        ckpt_path = os.path.join(save_dir, f'crossfit_{task}_{arch}_fold{k}.pt')
        best = -1.0
        t0 = time.time()
        for epoch in range(1, epochs + 1):
            ep_t0 = time.time()
            loss = _train_epoch(model, tr_loader, opt, device, pos_w, num_tasks,
                                epoch=epoch, epochs=epochs, fold=k, total_folds=folds)
            val_auc = _mean_auc(model, va_loader, device, num_tasks, desc=f"Fold {k+1} Val")
            ep_time = time.time() - ep_t0
            saved_str = ""
            if not np.isnan(val_auc) and val_auc > best:
                best = val_auc
                torch.save({'state_dict': model.state_dict(),
                            'config': {'arch': arch, 'in_dim': in_dim, 'edge_dim': edge_dim,
                                       'hidden_dim': hidden_dim, 'num_tasks': num_tasks},
                            'task_names': task_names, 'fold': k}, ckpt_path)
                saved_str = f" [New Best Val AUC: {best:.4f}]"
            print(f"  Fold {k+1}/{folds} | Epoch {epoch:02d}/{epochs:02d} | Loss: {loss:.4f} | Val AUC: {val_auc:.4f} | Time: {ep_time:.1f}s{saved_str}", flush=True)

        ck = torch.load(ckpt_path, map_location=device, weights_only=False)
        model.load_state_dict(ck['state_dict'])
        held_auc = _mean_auc(model, ho_loader, device, num_tasks, desc=f"Fold {k+1} Held-out")
        print(f"[OK] [{task.upper()}] Fold {k+1}/{folds} complete: Best Val AUC: {best:.4f} | Held-out AUC: {held_auc:.4f} "
              f"({len(held)} molecules in {time.time() - t0:.1f}s)\n", flush=True)
        rows.append({'task': task, 'arch': arch, 'fold': k, 'n_heldout': len(held),
                     'val_auc': best, 'heldout_auc': held_auc})

    # Fold map: canonical SMILES -> fold index. First occurrence wins on duplicates.
    fold_map: Dict[str, int] = {}
    for idx, smi in enumerate(smiles):
        key = canonical_key(smi)
        if key is not None and key not in fold_map:
            fold_map[key] = int(fold_of_idx[idx])
    with open(os.path.join(save_dir, f'crossfit_{task}_{arch}_folds.json'), 'w') as f:
        json.dump({'task_names': task_names, 'folds': folds, 'fold_of': fold_map}, f)

    df = pd.DataFrame(rows)
    out = os.path.join('results', f'crossfit_{task}_{arch}.csv')
    df.to_csv(out, index=False)
    print(f"\nMean held-out ROC-AUC across folds: {df['heldout_auc'].mean():.4f}  (saved {out})")
    return df


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Cross-fitted Tox21 / CYP models for honest risk profiles")
    ap.add_argument('--task', required=True, choices=['tox21', 'cyp'])
    ap.add_argument('--arch', default='gcn', choices=['gcn', 'gin', 'mpnn'])
    ap.add_argument('--folds', type=int, default=5)
    ap.add_argument('--epochs', type=int, default=25)
    ap.add_argument('--batch_size', type=int, default=64)
    ap.add_argument('--lr', type=float, default=1e-3)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--cyp_dir', default='data/cyp')
    args = ap.parse_args()
    run_crossfit(args.task, args.arch, args.folds, args.epochs, args.batch_size, args.lr,
                 seed=args.seed, cyp_dir=args.cyp_dir)
