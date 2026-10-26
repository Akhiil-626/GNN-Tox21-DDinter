"""
Run the full DDI severity study: baselines, tabular ablation, GNN ablation, abstain mode.

What it answers
---------------
Do structure-derived "risk fingerprints" (predicted Tox21 profile, optionally predicted
CYP profile) help predict interaction severity, especially for drugs the model has never
seen? Every model is evaluated on three drug-level scenarios (S0 / S1 / S2) over several
seeds with identical splits, and the report only claims what the statistics support.

Models
------
  Prior, DrugMean            chemistry-free floors (DrugMean = "is this drug just dangerous?")
  RF_fp                      fingerprint random forest              (fast, no torch)
  RF_fp+tox, RF_fp+toxshuf   + predicted Tox21 profile / shuffled control
  RF_fp+cyp                  + predicted CYP profile
  A                          GNN, structure only, order-independent head
  B, B_shuf, C, D            GNN + Tox21 / shuffled control / CYP / both

Usage
-----
  # real data (needs data/ from the earlier pipeline, cross-fitted models, RDKit, torch)
  python -m src.run_ablation --seeds 0 1 2 3 4 --variants A B B_shuf --arch gcn

  # tabular-only quick look (no GNN training)
  python -m src.run_ablation --no_gnn --seeds 0 1 2 3 4 5

  # pipeline self-test on fabricated data (NEVER report these numbers)
  python -m src.run_ablation --synthetic --no_gnn --seeds 0 1 2 3 4 5

Outputs go to --out_dir (default results/ablation): runs CSV, summary CSV, markdown report,
figure, conformal and overlap tables, and run metadata.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ablation_report import plot_summary, render_report, summarize
from src.ddi_baselines import (DrugMeanBaseline, PairFeatureForest, PriorBaseline, score_predictions)
from src.ddi_conformal import evaluate_conformal, fit_conformal
from src.ddi_features import generic_pair_features, overlap_diagnostics
from src.ddi_splits import assert_no_leakage, dedupe_pairs, make_drug_splits, merge_pairs_by_identity

TABULAR_MODELS = ['RF_fp', 'RF_fp+tox', 'RF_fp+toxshuf', 'RF_fp+ov', 'RF_tox', 'RF_fp+cyp']
GNN_VARIANTS = ['A', 'B', 'B_shuf', 'C', 'D']


@dataclass
class ExperimentData:
    pairs: List[Tuple[str, str, int]]
    tox: Dict[str, np.ndarray]
    cyp: Optional[Dict[str, np.ndarray]] = None
    fps: Optional[Dict[str, np.ndarray]] = None
    graphs: Optional[Dict[str, Any]] = None          # name -> PyG Data (None => no GNN possible)
    profiler_mode: str = 'crossfit'
    source: str = 'ddinter'
    notes: List[str] = field(default_factory=list)
    in_table: Dict[str, bool] = field(default_factory=dict)          # molecule was in the Tox21 labelled table
    atc_sets: Dict[str, frozenset] = field(default_factory=dict)     # coarse therapeutic-neighbourhood proxy


# ----------------------------------------------------------------------------- data loading
def restrict_to_complete(pairs, available: Sequence[Dict[str, Any]]):
    """Keep only pairs whose BOTH drugs exist in every representation dict (identical data for all models)."""
    ok = lambda n: all(n in d for d in available)
    kept = [p for p in pairs if ok(p[0]) and ok(p[1])]
    return kept, len(pairs) - len(kept)


def load_synthetic(args) -> ExperimentData:
    from src.ddi_synthetic import make_synthetic_experiment
    pairs, tox, cyp, fps = make_synthetic_experiment(
        seed=args.synthetic_seed, tox_signal=args.synthetic_tox_signal,
        tox_from_latent=not args.synthetic_tox_independent)
    return ExperimentData(pairs=pairs, tox=tox, cyp=cyp, fps=fps, graphs=None, profiler_mode='crossfit',
                          source=(f'SYNTHETIC (tox_signal={args.synthetic_tox_signal}, '
                                  f'tox_from_latent={not args.synthetic_tox_independent}) -- NOT REAL RESULTS'),
                          notes=['Fabricated data for pipeline testing only.'])


def load_real(args) -> ExperimentData:
    """Load DDInter pairs, build representations, compute leak-free risk profiles."""
    from src.ddi_dataset import DDInterGraphDataset
    from src.risk_profile import RiskProfiler
    from src.ddi_baselines import morgan_fingerprint

    ds = DDInterGraphDataset(root_dir='data')
    name_graphs: Dict[str, Any] = {}
    for ga, gb, _, na, nb in ds.pairs:
        name_graphs[na], name_graphs[nb] = ga, gb
    name_smiles = {n: ds.smiles_cache[n] for n in name_graphs}

    # Drug identity = canonical molecule, NOT the name. Name cleaning during PubChem lookup maps
    # e.g. "Brimonidine (ophthalmic)" and "Brimonidine" to one molecule; splitting by name would
    # put that molecule in both train and test.
    from src.chem_utils import canonical_key
    identity_of = {n: (canonical_key(name_smiles[n]) or f'name::{n}') for n in sorted(name_graphs)}
    rep_name: Dict[str, str] = {}
    for n in sorted(name_graphs):                       # deterministic representative per molecule
        rep_name.setdefault(identity_of[n], n)
    graphs = {i: name_graphs[n] for i, n in rep_name.items()}
    smiles = {i: name_smiles[n] for i, n in rep_name.items()}

    raw = [(na, nb, int(y)) for (_, _, y, na, nb) in ds.pairs]
    mapped, merge_stats = merge_pairs_by_identity(raw, identity_of, lambda p: p[0], lambda p: p[1], lambda p: p[2])
    pairs, stats = dedupe_pairs(mapped, lambda p: p[0], lambda p: p[1], lambda p: p[2])
    notes = [f"Drug identity by canonical molecule: {merge_stats['n_names']} names -> "
             f"{merge_stats['n_identities']} molecules ({merge_stats['n_names_merged']} names merged).",
             f"De-duplicated {stats['n_duplicates_removed']} duplicate/self pairs "
             f"({stats['n_conflicting']} had conflicting severities; the most severe was kept)."]

    names = sorted(graphs)
    print(f"Loading Tox21 risk profiler ({args.profiler_arch.upper()})...", flush=True)
    tox_profiler = RiskProfiler.load('tox21', arch=args.profiler_arch)
    mode = tox_profiler.mode
    print(f"Computing Tox21 risk profiles for {len(names)} drugs (mode: {mode})...", flush=True)
    tox_map = tox_profiler.profile_many([smiles[n] for n in names])
    tox = {n: tox_map[smiles[n]] for n in names if tox_map[smiles[n]] is not None}
    in_table = {n: bool(tox_profiler.in_training_table(smiles[n])) for n in names}
    n_in_table = sum(in_table.values())
    notes.append(f"Tox21 profiler mode: {mode}; {n_in_table}/{len(names)} molecules also appear in the Tox21 table.")

    cyp = None
    wants_cyp = any(v in args.variants for v in ('C', 'D')) or args.cyp
    if wants_cyp:
        print(f"Loading CYP profiler ({args.profiler_arch.upper()})...", flush=True)
        cyp_profiler = RiskProfiler.load('cyp', arch=args.profiler_arch, allow_leaky_fallback=False)
        print(f"Computing CYP profiles for {len(names)} drugs...", flush=True)
        cmap = cyp_profiler.profile_many([smiles[n] for n in names])
        cyp = {n: cmap[smiles[n]] for n in names if cmap[smiles[n]] is not None}
        notes.append(f"CYP profiler: {cyp_profiler.dim} isoforms ({', '.join(cyp_profiler.task_names)}).")

    print(f"Generating Morgan fingerprints for {len(names)} drugs...", flush=True)
    fps = {}
    for n in names:
        fp = morgan_fingerprint(smiles[n])
        if fp is not None:
            fps[n] = fp

    avail = [graphs, tox, fps] + ([cyp] if cyp is not None else [])
    pairs, dropped = restrict_to_complete(pairs, avail)
    notes.append(f"Dropped {dropped} pairs lacking a graph, profile or fingerprint for one drug "
                 f"(all models therefore see identical pairs).")
    from src.overlap_analysis import load_atc_sets
    atc_sets = load_atc_sets(os.path.join('data', 'raw'), identity_of)
    return ExperimentData(pairs=pairs, tox=tox, cyp=cyp, fps=fps, graphs=graphs,
                          profiler_mode=mode, source='DDInter', notes=notes,
                          in_table=in_table, atc_sets=atc_sets)


# ----------------------------------------------------------------------------- feature matrices
def fp_pair_vec(fps, a, b):
    fa, fb = fps[a], fps[b]
    return np.concatenate([fa + fb, np.abs(fa - fb)])


def shuffle_map(names: Sequence[str], seed: int) -> Dict[str, str]:
    """Random derangement-ish mapping drug -> another drug whose profile it will borrow (control)."""
    rng = random.Random(10_000 + seed)
    perm = list(names)
    for _ in range(20):
        rng.shuffle(perm)
        if all(a != b for a, b in zip(names, perm)):
            break
    return dict(zip(names, perm))


def tabular_matrix(model: str, data: ExperimentData, pairs, shuf: Dict[str, str]) -> np.ndarray:
    """
    Feature matrix for each tabular model:
      RF_fp          fingerprint pair features only
      RF_fp+tox      + 40 predicted-Tox21 pair features
      RF_fp+toxshuf  + the same features computed from profiles shuffled across drugs (control)
      RF_fp+ov       + only the 4 scalar overlap features (tests "too many extra features dilute the forest")
      RF_tox         Tox21 pair features ALONE, no fingerprints (tests how much signal they carry by themselves)
      RF_fp+cyp      + predicted CYP pair features
    """
    rows = []
    for a, b, _ in pairs:
        if model == 'RF_tox':
            parts = [generic_pair_features(data.tox[a], data.tox[b])]
        else:
            parts = [fp_pair_vec(data.fps, a, b)]
            if model == 'RF_fp+tox':
                parts.append(generic_pair_features(data.tox[a], data.tox[b]))
            elif model == 'RF_fp+toxshuf':
                parts.append(generic_pair_features(data.tox[shuf[a]], data.tox[shuf[b]]))
            elif model == 'RF_fp+ov':
                parts.append(generic_pair_features(data.tox[a], data.tox[b])[-4:])
            elif model == 'RF_fp+cyp':
                parts.append(generic_pair_features(data.cyp[a], data.cyp[b]))
        rows.append(np.concatenate(parts))
    return np.stack(rows).astype(np.float32)


# ----------------------------------------------------------------------------- GNN training
def gnn_extra(variant: str, data: ExperimentData, pairs, shuf: Dict[str, str]) -> Optional[np.ndarray]:
    if variant == 'A':
        return None
    rows = []
    for a, b, _ in pairs:
        parts = []
        if variant in ('B', 'D'):
            parts.append(generic_pair_features(data.tox[a], data.tox[b]))
        if variant == 'B_shuf':
            parts.append(generic_pair_features(data.tox[shuf[a]], data.tox[shuf[b]]))
        if variant in ('C', 'D'):
            parts.append(generic_pair_features(data.cyp[a], data.cyp[b]))
        rows.append(np.concatenate(parts))
    return np.stack(rows).astype(np.float32)


def fit_and_predict_gnn(variant, data, pairs, extras, split, args, seed):
    """
    Train one SymmetricDDI variant. Returns (model, val_probs, {scenario: probs}).
    Early stopping on validation macro-F1 (validation uses drugs unseen in training).
    """
    import torch
    import torch.nn.functional as F
    from sklearn.metrics import f1_score
    from torch.utils.data import DataLoader, Dataset
    from torch_geometric.data import Batch
    from src.ddi_model import SymmetricDDI

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

    class PairDS(Dataset):
        def __init__(self, idx):
            self.idx = list(idx)

        def __len__(self):
            return len(self.idx)

        def __getitem__(self, k):
            i = self.idx[k]
            a, b, y = pairs[i]
            return data.graphs[a], data.graphs[b], y, (extras[i] if extras is not None else None)

    def collate(batch):
        ga = Batch.from_data_list([b[0] for b in batch])
        gb = Batch.from_data_list([b[1] for b in batch])
        y = torch.tensor([b[2] for b in batch], dtype=torch.long)
        ex = torch.tensor(np.stack([b[3] for b in batch]), dtype=torch.float) if batch[0][3] is not None else None
        return ga, gb, y, ex

    def loader(idx, shuffle):
        gen = torch.Generator().manual_seed(seed)
        return DataLoader(PairDS(idx), batch_size=args.batch_size, shuffle=shuffle, collate_fn=collate,
                          generator=gen if shuffle else None)

    if not split.val:
        raise RuntimeError("Validation set is empty; cannot do early stopping. Use more drugs/pairs.")

    train_loader, val_loader = loader(split.train, True), loader(split.val, False)
    sample = data.graphs[pairs[split.train[0]][0]]
    in_dim = sample.x.size(1)
    edge_dim = sample.edge_attr.size(1) if getattr(sample, 'edge_attr', None) is not None else 6
    extra_dim = 0 if extras is None else extras.shape[1]

    model = SymmetricDDI(arch=args.arch, in_dim=in_dim, edge_dim=edge_dim, hidden_dim=args.hidden_dim,
                         num_outputs=3, extra_dim=extra_dim).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-5)

    param_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\n  [GNN {variant}] Arch: {args.arch.upper()} | Extra Dim: {extra_dim} | Params: {param_count:,} | Device: {device}", flush=True)
    print(f"  [GNN {variant}] Training: {len(split.train)} pairs ({len(train_loader)} batches) | Max Epochs: {args.epochs} (patience={args.patience})", flush=True)

    counts = np.bincount([pairs[i][2] for i in split.train], minlength=3)
    w = torch.tensor([min(len(split.train) / (3 * max(c, 1)), 10.0) for c in counts], dtype=torch.float, device=device)

    @torch.no_grad()
    def predict(ld, desc=None):
        model.eval()
        outs = []
        iterator = tqdm(ld, desc=f"    {desc}", leave=False, dynamic_ncols=True) if desc else ld
        for ga, gb, _, ex in iterator:
            ga, gb = ga.to(device), gb.to(device)
            ex = ex.to(device) if ex is not None else None
            outs.append(torch.softmax(model(ga, gb, ex), dim=-1).cpu().numpy())
        return np.vstack(outs) if outs else np.zeros((0, 3))

    best_f1, best_state, bad = -1.0, None, 0
    y_val = np.array([pairs[i][2] for i in split.val])
    for epoch in range(1, args.epochs + 1):
        ep_t0 = time.time()
        model.train()
        total_loss, n_batches = 0.0, 0
        pbar = tqdm(train_loader, desc=f"  GNN {variant} Ep {epoch:02d}/{args.epochs:02d}", leave=False, dynamic_ncols=True)
        for ga, gb, y, ex in pbar:
            ga, gb, y = ga.to(device), gb.to(device), y.to(device)
            ex = ex.to(device) if ex is not None else None
            opt.zero_grad()
            loss = F.cross_entropy(model(ga, gb, ex), y, weight=w)
            loss.backward()
            opt.step()
            total_loss += loss.item()
            n_batches += 1
            pbar.set_postfix({'loss': f"{loss.item():.4f}", 'avg': f"{total_loss / n_batches:.4f}"})
        avg_loss = total_loss / max(n_batches, 1)
        vp = predict(val_loader, desc=f"GNN {variant} Val")
        f1 = f1_score(y_val, vp.argmax(1), average='macro', labels=[0, 1, 2], zero_division=0)
        ep_time = time.time() - ep_t0
        if f1 > best_f1:
            best_f1, bad = f1, 0
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            status_str = f" [New Best Val Macro-F1: {best_f1:.4f}]"
        else:
            bad += 1
            status_str = f" (patience: {bad}/{args.patience})"
        print(f"  [GNN {variant}] Ep {epoch:02d}/{args.epochs:02d} | Loss: {avg_loss:.4f} | Val Macro-F1: {f1:.4f} | Time: {ep_time:.1f}s{status_str}", flush=True)
        if bad >= args.patience:
            print(f"  [GNN {variant}] Early stopping triggered at epoch {epoch} (Best Val Macro-F1: {best_f1:.4f})", flush=True)
            break
    model.load_state_dict(best_state)

    val_probs = predict(val_loader, desc=f"GNN {variant} Final Val")
    test_probs = {scen: predict(loader(idx, False), desc=f"GNN {variant} Test {scen}") for scen, idx in split.test_sets().items() if idx}
    return model, val_probs, test_probs, {'in_dim': in_dim, 'edge_dim': edge_dim, 'extra_dim': extra_dim}


def save_gnn_for_app(variant, model, cfg, conformal_model, args) -> None:
    import torch
    os.makedirs('models', exist_ok=True)
    base = f'models/ddi_sym_{variant}_{args.arch}'
    torch.save({'state_dict': model.state_dict(),
                'config': model.config(cfg['in_dim'], cfg['edge_dim'], args.hidden_dim, 3),
                'variant': variant, 'profiler_arch': args.profiler_arch}, base + '.pt')
    with open(base + '_conformal.json', 'w') as f:
        json.dump(conformal_model.to_dict(), f)


# ----------------------------------------------------------------------------- experiment loop
def evaluate_all(model_name, seed, split, pairs, probs_by_scen, val_probs, y_val, args,
                 runs, conf_rows):
    """Score one model's predictions on S0/S1/S2 and record conformal behaviour."""
    cm = None
    if val_probs is not None and len(y_val) > 0:
        cm = fit_conformal(val_probs, y_val, alpha=args.alpha, mondrian=True)
    for scen, idx in split.test_sets().items():
        if not idx or scen not in probs_by_scen:
            continue
        y_true = np.array([pairs[i][2] for i in idx])
        probs = probs_by_scen[scen]
        row = {'seed': seed, 'model': model_name, 'scenario': scen, 'n': len(idx)}
        row.update(score_predictions(y_true, probs.argmax(axis=1)))
        runs.append(row)
        if cm is not None:
            c = evaluate_conformal(cm, probs, y_true)
            c.update({'seed': seed, 'model': model_name, 'scenario': scen})
            conf_rows.append(c)
    return cm


def run_experiment(data: ExperimentData, args) -> Dict[str, Any]:
    pairs = data.pairs
    if args.max_pairs and len(pairs) > args.max_pairs:
        rng = random.Random(0)
        pairs = rng.sample(pairs, args.max_pairs)
    print(f"Source: {data.source} | {len(pairs)} unique pairs, "
          f"{len({d for p in pairs for d in p[:2]})} drugs")

    runs: List[Dict[str, Any]] = []
    conf_rows: List[Dict[str, Any]] = []
    overlap_rows: List[Dict[str, Any]] = []
    tabular = [] if (data.fps is None or args.no_tabular) else [
        m for m in TABULAR_MODELS if m != 'RF_fp+cyp' or data.cyp is not None]
    can_gnn = (not args.no_gnn) and data.graphs is not None
    gnn_variants = [v for v in args.variants if v in GNN_VARIANTS
                    and (v not in ('C', 'D') or data.cyp is not None)] if can_gnn else []
    if not can_gnn and not args.no_gnn:
        print("GNN variants skipped: no molecular graphs in this data source.")

    for seed in args.seeds:
        t0 = time.time()
        split = make_drug_splits(pairs, lambda p: p[0], lambda p: p[1], seed=seed)
        assert_no_leakage(split, pairs, lambda p: p[0], lambda p: p[1])
        print(f"\n=== seed {seed}: {split.sizes()} ===")
        y_val = np.array([pairs[i][2] for i in split.val])
        train_p = [pairs[i] for i in split.train]
        names = sorted({d for p in pairs for d in p[:2]})
        shuf = shuffle_map(names, seed)

        # ---- chemistry-free floors
        prior = PriorBaseline().fit(train_p)
        dm = DrugMeanBaseline().fit(train_p)
        for name, mdl in (('Prior', prior), ('DrugMean', dm)):
            val_pr = mdl.predict_proba([(pairs[i][0], pairs[i][1]) for i in split.val]) if split.val else None
            pr = {s: mdl.predict_proba([(pairs[i][0], pairs[i][1]) for i in idx])
                  for s, idx in split.test_sets().items() if idx}
            evaluate_all(name, seed, split, pairs, pr, val_pr, y_val, args, runs, conf_rows)

        # ---- tabular ablation
        if tabular:
            cap = args.rf_max_train
            tr_idx = split.train if len(split.train) <= cap else random.Random(seed).sample(split.train, cap)
            y_tr = [pairs[i][2] for i in tr_idx]
            for name in tabular:
                t_tab = time.time()
                print(f"  Training Tabular {name} ({args.rf_trees} trees on {len(tr_idx)} pairs)...", flush=True)
                Xtr = tabular_matrix(name, data, [pairs[i] for i in tr_idx], shuf)
                rf = PairFeatureForest(n_estimators=args.rf_trees, random_state=seed).fit(Xtr, y_tr)
                val_pr = rf.predict_proba(tabular_matrix(name, data, [pairs[i] for i in split.val], shuf)) \
                    if split.val else None
                pr = {s: rf.predict_proba(tabular_matrix(name, data, [pairs[i] for i in idx], shuf))
                      for s, idx in split.test_sets().items() if idx}
                evaluate_all(name, seed, split, pairs, pr, val_pr, y_val, args, runs, conf_rows)
                print(f"  [OK] Tabular {name:<14} finished in {time.time() - t_tab:.1f}s", flush=True)

        # ---- GNN ablation
        for variant in gnn_variants:
            t_gnn = time.time()
            extras = gnn_extra(variant, data, pairs, shuf)
            model, val_probs, test_probs, cfg = fit_and_predict_gnn(variant, data, pairs, extras, split, args, seed)
            cm = evaluate_all(variant, seed, split, pairs, test_probs, val_probs, y_val, args, runs, conf_rows)
            print(f"  [OK] GNN Variant {variant:<7} finished in {time.time() - t_gnn:.1f}s", flush=True)
            if seed == args.seeds[0] and args.save_models and cm is not None:
                save_gnn_for_app(variant, model, cfg, cm, args)

        # ---- model-free overlap check on the first seed's split
        if seed == args.seeds[0]:
            sets = dict(split.test_sets())
            sets['ALL'] = list(range(len(pairs)))
            for scen, idx in sets.items():
                if len(idx) < 10:
                    continue
                diag = overlap_diagnostics([data.tox[pairs[i][0]] for i in idx], [data.tox[pairs[i][1]] for i in idx],
                                           [pairs[i][2] for i in idx])
                diag['scenario'] = scen
                overlap_rows.append(diag)
        print(f"  seed {seed} finished in {time.time() - t0:.0f}s")

    return {'runs': pd.DataFrame(runs), 'conformal': pd.DataFrame(conf_rows),
            'overlap': pd.DataFrame(overlap_rows), 'n_pairs': len(pairs)}


def write_outputs(result: Dict[str, Any], data: ExperimentData, args) -> str:
    out = args.out_dir
    os.makedirs(os.path.join(out, 'figures'), exist_ok=True)
    runs, conf, overlap = result['runs'], result['conformal'], result['overlap']
    if runs.empty:
        raise RuntimeError("No results were produced (all scenario test sets empty?).")

    runs.to_csv(os.path.join(out, 'ablation_runs.csv'), index=False)
    summarize(runs).to_csv(os.path.join(out, 'ablation_summary.csv'), index=False)
    if not conf.empty:
        conf.to_csv(os.path.join(out, 'conformal.csv'), index=False)
    if not overlap.empty:
        overlap.to_csv(os.path.join(out, 'overlap_correlation.csv'), index=False)

    meta = {
        'data source': data.source,
        'unique pairs used': result['n_pairs'],
        'seeds': ', '.join(map(str, args.seeds)),
        'GNN architecture': args.arch if not args.no_gnn else 'not run',
        'profiler_mode': data.profiler_mode,
        'conformal alpha': args.alpha,
    }
    for i, note in enumerate(data.notes, 1):
        meta[f'note {i}'] = note
    report = render_report(runs, meta, overlap, conf)
    path = os.path.join(out, 'ablation_report.md')
    with open(path, 'w') as f:
        f.write(report)
    plot_summary(summarize(runs), os.path.join(out, 'figures', 'ablation_macro_f1.png'))
    with open(os.path.join(out, 'run_meta.json'), 'w') as f:
        json.dump({**meta, 'args': {k: v for k, v in vars(args).items()}}, f, indent=2, default=str)
    return path


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="DDI severity ablation study")
    ap.add_argument('--arch', default='gcn', choices=['gcn', 'gin', 'mpnn'])
    ap.add_argument('--profiler_arch', default='gcn', choices=['gcn', 'gin', 'mpnn'],
                    help='architecture of the cross-fitted Tox21/CYP profile models')
    ap.add_argument('--seeds', type=int, nargs='+', default=[0, 1, 2, 3, 4])
    ap.add_argument('--variants', nargs='+', default=['A', 'B', 'B_shuf'], choices=GNN_VARIANTS)
    ap.add_argument('--cyp', action='store_true', help='also run RF_fp+cyp (needs cross-fitted CYP models)')
    ap.add_argument('--epochs', type=int, default=25)
    ap.add_argument('--patience', type=int, default=6)
    ap.add_argument('--batch_size', type=int, default=64)
    ap.add_argument('--lr', type=float, default=1e-3)
    ap.add_argument('--hidden_dim', type=int, default=128)
    ap.add_argument('--alpha', type=float, default=0.1, help='conformal miscoverage level')
    ap.add_argument('--rf_trees', type=int, default=300)
    ap.add_argument('--rf_max_train', type=int, default=60000)
    ap.add_argument('--max_pairs', type=int, default=0, help='subsample pairs for quick smoke runs (0 = all)')
    ap.add_argument('--no_gnn', action='store_true')
    ap.add_argument('--no_tabular', action='store_true')
    ap.add_argument('--save_models', action='store_true', help="save seed-0 GNN checkpoints + conformal params for the app")
    ap.add_argument('--out_dir', default='results/ablation')
    ap.add_argument('--synthetic', action='store_true', help='fabricated data to self-test the pipeline')
    ap.add_argument('--synthetic_seed', type=int, default=0)
    ap.add_argument('--synthetic_tox_signal', type=float, default=0.6)
    ap.add_argument('--synthetic_tox_independent', action='store_true',
                    help='make synthetic toxicity profiles carry NO information (a true null)')
    return ap.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    data = load_synthetic(args) if args.synthetic else load_real(args)
    if data.profiler_mode == 'single_model_leaky':
        print("\n" + "!" * 78 + "\nWARNING: using a single Tox21 model. Drugs that are also in Tox21 get unrealistically "
              "good\nprofiles (feature leakage). For honest results run: python -m src.crossfit --task tox21\n"
              + "!" * 78 + "\n")
    if args.synthetic:
        print("\n*** SYNTHETIC DATA: pipeline self-test only. Do not report these numbers. ***\n")
    result = run_experiment(data, args)
    path = write_outputs(result, data, args)
    print(f"\nReport written to {path}")
    return result


if __name__ == '__main__':
    main()
