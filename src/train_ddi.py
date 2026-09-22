"""
Training Pipeline for Dual-Encoder GNN DDI Severity Classification on DDInter.
Handles paired-graph batching, class-weighted cross-entropy loss, epoch
validation, checkpointing, and logging -- mirroring train.py's structure,
adapted for two-graph-per-sample inputs and 3-class (Minor/Moderate/Major)
classification instead of Tox21's 12-task multi-label setup.
"""

import os
import time
import argparse
from collections import Counter
from typing import Dict, List, Tuple, Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torch_geometric.data import Batch
from sklearn.metrics import f1_score, accuracy_score, classification_report
from tqdm import tqdm

from src.ddi_dataset import DDInterGraphDataset, LABEL_TO_LEVEL
from src.ddi_model import DualEncoderDDI


class DDIPairDataset(Dataset):
    """
    Thin wrapper turning a list of (graph_a, graph_b, label) tuples into a
    torch Dataset. Actual graph batching happens in ddi_collate() below,
    since PyG's own DataLoader only knows how to batch ONE graph per sample,
    not pairs.
    """
    def __init__(self, pairs: List[Tuple[Any, Any, int]]):
        self.pairs = pairs

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        return self.pairs[idx]


def ddi_collate(batch: List[Tuple[Any, Any, int]]):
    """
    Custom collate function: batches graph_a's and graph_b's separately using
    PyG's Batch.from_data_list, and stacks labels into a single tensor.
    """
    graphs_a = [item[0] for item in batch]
    graphs_b = [item[1] for item in batch]
    labels = torch.tensor([item[2] for item in batch], dtype=torch.long)

    batch_a = Batch.from_data_list(graphs_a)
    batch_b = Batch.from_data_list(graphs_b)
    return batch_a, batch_b, labels


def compute_class_weights(pairs: List[Tuple[Any, Any, int]], num_classes: int = 3,
                          cap: float = 10.0) -> torch.Tensor:
    """
    Compute inverse-frequency class weights from the training split, the same
    spirit as train.py's pos_weight computation for Tox21's imbalanced tasks.
    Capped to avoid extreme weights on very rare classes destabilizing training.
    """
    counts = Counter(label for _, _, label in pairs)
    total = sum(counts.values())
    weights = []
    for c in range(num_classes):
        n_c = counts.get(c, 0)
        weight = total / (num_classes * max(n_c, 1))
        weights.append(min(weight, cap))
    print(f"Class counts: {dict((LABEL_TO_LEVEL[k], v) for k, v in counts.items())}")
    print(f"Class weights (inverse-frequency, capped at {cap}): {weights}")
    return torch.tensor(weights, dtype=torch.float)


def train_epoch(model: nn.Module, loader: DataLoader, optimizer: torch.optim.Optimizer,
                device: torch.device, class_weights: torch.Tensor) -> float:
    """Train for one epoch with class-weighted cross-entropy loss.

    Shows a per-batch progress bar (tqdm) so slow-but-working architectures
    like MPNN (whose edge-conditioned NNConv layers are far more compute-heavy
    per batch than GCN/GIN) are visibly distinguishable from a genuine hang.
    """
    model.train()
    total_loss = 0.0
    total_samples = 0

    progress = tqdm(loader, desc="Training", leave=False)
    for batch_a, batch_b, labels in progress:
        batch_a = batch_a.to(device)
        batch_b = batch_b.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        logits = model(batch_a, batch_b)
        loss = F.cross_entropy(logits, labels, weight=class_weights.to(device))
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * labels.size(0)
        total_samples += labels.size(0)
        progress.set_postfix(loss=f"{loss.item():.4f}")

    return total_loss / max(total_samples, 1)


@torch.no_grad()
def evaluate_model(model: nn.Module, loader: DataLoader, device: torch.device) -> Tuple[float, float, np.ndarray, np.ndarray]:
    """Evaluate model on val or test loader. Returns (accuracy, macro_f1, y_true, y_pred)."""
    model.eval()
    all_labels = []
    all_preds = []

    for batch_a, batch_b, labels in loader:
        batch_a = batch_a.to(device)
        batch_b = batch_b.to(device)

        logits = model(batch_a, batch_b)
        preds = torch.argmax(logits, dim=-1).cpu().numpy()

        all_labels.append(labels.numpy())
        all_preds.append(preds)

    y_true = np.concatenate(all_labels)
    y_pred = np.concatenate(all_preds)

    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
    return acc, macro_f1, y_true, y_pred


def train_ddi(arch: str = 'gin', epochs: int = 30, batch_size: int = 64, lr: float = 0.001,
              hidden_dim: int = 128, save_dir: str = 'models') -> Dict[str, Any]:
    """Run full training procedure for the dual-encoder DDI severity classifier."""
    os.makedirs(save_dir, exist_ok=True)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\n--- Starting DDI Training for {arch.upper()} Dual-Encoder on {device} ---")

    dataset = DDInterGraphDataset(root_dir="data")
    train_pairs, val_pairs, test_pairs = dataset.get_cold_start_splits()

    train_loader = DataLoader(DDIPairDataset(train_pairs), batch_size=batch_size,
                               shuffle=True, collate_fn=ddi_collate)
    val_loader = DataLoader(DDIPairDataset(val_pairs), batch_size=batch_size,
                             shuffle=False, collate_fn=ddi_collate)
    test_loader = DataLoader(DDIPairDataset(test_pairs), batch_size=batch_size,
                              shuffle=False, collate_fn=ddi_collate)

    class_weights = compute_class_weights(train_pairs, num_classes=3)

    sample_graph = train_pairs[0][0]
    in_dim = sample_graph.x.size(1)
    edge_dim = sample_graph.edge_attr.size(1) if hasattr(sample_graph, 'edge_attr') and sample_graph.edge_attr is not None else 6

    model = DualEncoderDDI(arch=arch, in_dim=in_dim, edge_dim=edge_dim,
                            hidden_dim=hidden_dim, num_outputs=3).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=5)

    best_val_f1 = 0.0
    best_checkpoint_path = os.path.join(save_dir, f"best_ddi_{arch}.pt")

    history = {'train_loss': [], 'val_acc': [], 'val_f1': []}

    for epoch in range(1, epochs + 1):
        epoch_start = time.time()
        loss = train_epoch(model, train_loader, optimizer, device, class_weights)
        val_acc, val_f1, _, _ = evaluate_model(model, val_loader, device)
        scheduler.step(val_f1)
        epoch_time = time.time() - epoch_start

        history['train_loss'].append(loss)
        history['val_acc'].append(val_acc)
        history['val_f1'].append(val_f1)

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            checkpoint = {
                'state_dict': model.state_dict(),
                'config': {
                    'arch': arch,
                    'in_dim': in_dim,
                    'edge_dim': edge_dim,
                    'hidden_dim': hidden_dim,
                    'num_outputs': 3
                }
            }
            torch.save(checkpoint, best_checkpoint_path)
            saved_str = f" [Saved Best Model: F1={val_f1:.4f}]"
        else:
            saved_str = ""

        if epoch % 5 == 0 or epoch == 1 or epoch == epochs:
            print(f"Epoch {epoch:02d}/{epochs:02d} | Loss: {loss:.4f} | "
                  f"Val Acc: {val_acc:.4f} | Val Macro-F1: {val_f1:.4f} | "
                  f"Time: {epoch_time:.1f}s{saved_str}")

    # Load best model for final test evaluation
    saved_ckpt = torch.load(best_checkpoint_path, weights_only=False)
    model.load_state_dict(saved_ckpt['state_dict'])

    test_acc, test_f1, y_true_test, y_pred_test = evaluate_model(model, test_loader, device)
    report = classification_report(y_true_test, y_pred_test,
                                    target_names=[LABEL_TO_LEVEL[i] for i in range(3)],
                                    zero_division=0)

    print(f"\nFinal Test Accuracy: {test_acc:.4f} | Test Macro-F1: {test_f1:.4f}")
    print("Per-class report:\n", report)

    return {
        'model': model,
        'arch': arch,
        'best_val_f1': best_val_f1,
        'test_acc': test_acc,
        'test_f1': test_f1,
        'classification_report': report,
        'history': history
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train Dual-Encoder GNN for DDI Severity Classification")
    parser.add_argument('--arch', type=str, default='gin', choices=['gcn', 'gin', 'mpnn'])
    parser.add_argument('--epochs', type=int, default=30)
    parser.add_argument('--batch_size', type=int, default=64)
    parser.add_argument('--lr', type=float, default=0.001)
    args = parser.parse_args()

    train_ddi(arch=args.arch, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)