"""
DDI Model Evaluation and Comparison Module.
Loads saved checkpoints for each trained architecture, re-evaluates them on
the same held-out test set, and writes a comparison CSV -- mirrors the role
evaluate.py plays for the Tox21 pipeline (results/metrics.csv).

Note: MPNN is intentionally excluded from this comparison. Its edge-conditioned
NNConv layers make it far more compute-heavy per batch than GCN/GIN (each edge
gets its own learned input_dim x hidden_dim transformation matrix), and on
CPU-only hardware a single epoch took roughly 2 hours -- prohibitive for this
project's available compute. This is a deliberate, documented exclusion due to
hardware constraints, not an oversight.
"""

import os
from typing import Dict, Any

import torch
import pandas as pd
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, f1_score, accuracy_score

from src.ddi_dataset import DDInterGraphDataset, LABEL_TO_LEVEL
from src.ddi_model import DualEncoderDDI
from src.train_ddi import DDIPairDataset, ddi_collate, evaluate_model

ARCHITECTURES_TO_EVALUATE = ['gcn', 'gin']  # mpnn excluded -- see module docstring
MODELS_DIR = 'models'
RESULTS_PATH = 'results/ddi_metrics.csv'


def load_ddi_checkpoint(arch: str, device: torch.device) -> torch.nn.Module:
    """Load a trained DualEncoderDDI checkpoint for the given architecture."""
    ckpt_path = os.path.join(MODELS_DIR, f"best_ddi_{arch}.pt")
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(
            f"No checkpoint found at {ckpt_path}. Train it first with: "
            f"python -m src.train_ddi --arch {arch} --epochs 15"
        )
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    cfg = ckpt['config']
    model = DualEncoderDDI(
        arch=cfg['arch'], in_dim=cfg['in_dim'], edge_dim=cfg['edge_dim'],
        hidden_dim=cfg['hidden_dim'], num_outputs=cfg['num_outputs']
    ).to(device)
    model.load_state_dict(ckpt['state_dict'])
    model.eval()
    return model


def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    os.makedirs('results', exist_ok=True)

    print("Loading DDInter dataset and cold-start test split (shared across all models)...")
    dataset = DDInterGraphDataset(root_dir="data")
    _, _, test_pairs = dataset.get_cold_start_splits()
    test_loader = DataLoader(DDIPairDataset(test_pairs), batch_size=64,
                              shuffle=False, collate_fn=ddi_collate)

    rows = []
    for arch in ARCHITECTURES_TO_EVALUATE:
        print(f"\n--- Evaluating {arch.upper()} ---")
        try:
            model = load_ddi_checkpoint(arch, device)
        except FileNotFoundError as e:
            print(str(e))
            continue

        acc, macro_f1, y_true, y_pred = evaluate_model(model, test_loader, device)
        report = classification_report(
            y_true, y_pred, target_names=[LABEL_TO_LEVEL[i] for i in range(3)],
            output_dict=True, zero_division=0
        )

        row = {
            'architecture': arch.upper(),
            'test_accuracy': acc,
            'test_macro_f1': macro_f1,
        }
        for level in ['Minor', 'Moderate', 'Major']:
            row[f'{level}_precision'] = report[level]['precision']
            row[f'{level}_recall'] = report[level]['recall']
            row[f'{level}_f1'] = report[level]['f1-score']
            row[f'{level}_support'] = report[level]['support']

        rows.append(row)
        print(f"{arch.upper()} -> Accuracy: {acc:.4f}, Macro-F1: {macro_f1:.4f}")

    # Explicitly note MPNN's exclusion in the saved results, not just the code comments.
    rows.append({
        'architecture': 'MPNN',
        'test_accuracy': None,
        'test_macro_f1': None,
        'note': 'Excluded: ~2hr/epoch on available CPU hardware, not run to completion.'
    })

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS_PATH, index=False)
    print(f"\nSaved comparison to {RESULTS_PATH}")
    print(df.to_string(index=False))


if __name__ == '__main__':
    main()