"""
Training Pipeline for GNN Molecular Property Prediction on Tox21.
Handles data loading, masked BCE loss computation, epoch validation, checkpointing, and logging.
"""

import os
import argparse
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.loader import DataLoader
from sklearn.metrics import roc_auc_score, average_precision_score
from tqdm import tqdm
from typing import Dict, List, Tuple, Any, Optional

from src.dataset import Tox21GraphDataset, TOX21_TASKS
from src.model import get_model, MPNNModel


def compute_metrics(y_true: np.ndarray, y_pred_probs: np.ndarray, tasks: List[str] = TOX21_TASKS) -> Dict[str, Any]:
    """
    Compute per-task ROC-AUC and mean ROC-AUC across valid endpoints.
    Handles missing labels (NaNs).
    """
    roc_aucs = {}
    valid_tasks = []
    
    for i, task_name in enumerate(tasks):
        y_t = y_true[:, i]
        y_p = y_pred_probs[:, i]
        
        # Filter NaNs
        valid_mask = ~np.isnan(y_t)
        y_t_valid = y_t[valid_mask]
        y_p_valid = y_p[valid_mask]
        
        # Must have both positive and negative classes to compute ROC-AUC
        if len(y_t_valid) > 0 and len(np.unique(y_t_valid)) == 2:
            try:
                score = roc_auc_score(y_t_valid, y_p_valid)
                roc_aucs[task_name] = score
                valid_tasks.append(score)
            except Exception:
                roc_aucs[task_name] = np.nan
        else:
            roc_aucs[task_name] = np.nan
            
    mean_auc = np.nanmean(valid_tasks) if len(valid_tasks) > 0 else 0.5
    return {'per_task': roc_aucs, 'mean_auc': mean_auc}


def train_epoch(model: nn.Module, loader: DataLoader, optimizer: torch.optim.Optimizer, 
                device: torch.device, pos_weight: Optional[torch.Tensor] = None) -> float:
    """Train for one epoch with class-imbalance weighted masked BCE loss."""
    model.train()
    total_loss = 0.0
    total_samples = 0
    
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        if isinstance(model, MPNNModel):
            logits = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
        else:
            logits = model(batch.x, batch.edge_index, batch.batch)
            
        y_target = batch.y.view(-1, 12)
        mask = ~torch.isnan(y_target)
        
        if mask.sum() == 0:
            continue
            
        if pos_weight is not None:
            # Broadcast pos_weight across batch
            weight_mat = pos_weight.unsqueeze(0).expand_as(y_target)
            loss = F.binary_cross_entropy_with_logits(logits[mask], y_target[mask], pos_weight=weight_mat[mask])
        else:
            loss = F.binary_cross_entropy_with_logits(logits[mask], y_target[mask])
            
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item() * mask.sum().item()
        total_samples += mask.sum().item()
        
    return total_loss / max(total_samples, 1)


@torch.no_grad()
def evaluate_model(model: nn.Module, loader: DataLoader, device: torch.device) -> Tuple[float, Dict[str, Any], np.ndarray, np.ndarray]:
    """Evaluate model on val or test loader."""
    model.eval()
    all_y_true = []
    all_y_probs = []
    
    for batch in loader:
        batch = batch.to(device)
        if isinstance(model, MPNNModel):
            logits = model(batch.x, batch.edge_index, batch.edge_attr, batch.batch)
        else:
            logits = model(batch.x, batch.edge_index, batch.batch)
            
        probs = torch.sigmoid(logits)
        y_target = batch.y.view(-1, 12)
        
        all_y_true.append(y_target.cpu().numpy())
        all_y_probs.append(probs.cpu().numpy())
        
    y_true_mat = np.vstack(all_y_true)
    y_probs_mat = np.vstack(all_y_probs)
    
    metrics = compute_metrics(y_true_mat, y_probs_mat)
    return metrics['mean_auc'], metrics['per_task'], y_true_mat, y_probs_mat


def train_gnn(arch: str = 'gcn', epochs: int = 35, batch_size: int = 64, lr: float = 0.001, 
              hidden_dim: int = 128, save_dir: str = 'models') -> Dict[str, Any]:
    """Run full training procedure for a specific GNN architecture."""
    os.makedirs(save_dir, exist_ok=True)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\n--- Starting Training for {arch.upper()} GNN on {device} ---")
    
    dataset = Tox21GraphDataset(root_dir="data")
    train_graphs, val_graphs, test_graphs = dataset.get_scaffold_splits()
    
    train_loader = DataLoader(train_graphs, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_graphs, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_graphs, batch_size=batch_size, shuffle=False)
    
    # Compute positive class weights to handle Tox21 imbalance (positives range ~3%-16%)
    y_train_mat = torch.vstack([g.y.view(12) for g in train_graphs])
    pos_weights = []
    for t_idx in range(12):
        col_y = y_train_mat[:, t_idx]
        valid_m = ~torch.isnan(col_y)
        n_pos = (col_y[valid_m] == 1.0).sum().item()
        n_neg = (col_y[valid_m] == 0.0).sum().item()
        weight = float(n_neg) / max(float(n_pos), 1.0)
        # Cap weight ratio for numerical stability
        pos_weights.append(min(weight, 10.0))
        
    pos_weight_tensor = torch.tensor(pos_weights, dtype=torch.float, device=device)
    
    in_dim = train_graphs[0].x.size(1)
    edge_dim = train_graphs[0].edge_attr.size(1) if hasattr(train_graphs[0], 'edge_attr') and train_graphs[0].edge_attr is not None else 6
    
    model = get_model(arch, in_dim=in_dim, edge_dim=edge_dim, hidden_dim=hidden_dim, num_tasks=12).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=5)
    
    best_val_auc = 0.0
    best_checkpoint_path = os.path.join(save_dir, f"best_{arch}.pt")
    
    history = {'train_loss': [], 'val_auc': []}
    
    for epoch in range(1, epochs + 1):
        loss = train_epoch(model, train_loader, optimizer, device, pos_weight=pos_weight_tensor)
        val_auc, per_task_val, _, _ = evaluate_model(model, val_loader, device)
        scheduler.step(val_auc)
        
        history['train_loss'].append(loss)
        history['val_auc'].append(val_auc)
        
        if val_auc > best_val_auc:
            best_val_auc = val_auc
            checkpoint = {
                'state_dict': model.state_dict(),
                'config': {
                    'arch': arch,
                    'in_dim': in_dim,
                    'edge_dim': edge_dim,
                    'hidden_dim': hidden_dim,
                    'num_tasks': 12
                }
            }
            torch.save(checkpoint, best_checkpoint_path)
            saved_str = f" [Saved Best Model: {val_auc:.4f}]"
        else:
            saved_str = ""
            
        if epoch % 5 == 0 or epoch == 1 or epoch == epochs:
            print(f"Epoch {epoch:02d}/{epochs:02d} | Loss: {loss:.4f} | Val ROC-AUC: {val_auc:.4f}{saved_str}")
            
    # Load best model for final evaluation on test set
    saved_ckpt = torch.load(best_checkpoint_path, weights_only=False)
    if isinstance(saved_ckpt, dict) and 'state_dict' in saved_ckpt:
        model.load_state_dict(saved_ckpt['state_dict'])
    else:
        model.load_state_dict(saved_ckpt)
        
    test_auc, per_task_test, y_true_test, y_probs_test = evaluate_model(model, test_loader, device)
    
    # Save training curves plot to results/figures/
    fig_dir = os.path.join("results", "figures")
    os.makedirs(fig_dir, exist_ok=True)
    
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    epochs_range = range(1, epochs + 1)
    
    ax1.plot(epochs_range, history['train_loss'], 'b-o', lw=2, label='Train Weighted BCE Loss')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.set_title(f'{arch.upper()} Training Loss Curve')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    ax2.plot(epochs_range, history['val_auc'], 'g-s', lw=2, label='Val Mean ROC-AUC')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('ROC-AUC')
    ax2.set_title(f'{arch.upper()} Validation ROC-AUC Progression')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    curve_path = os.path.join(fig_dir, f'training_curves_{arch}.png')
    plt.savefig(curve_path, dpi=300)
    plt.close()
    print(f"Saved training curves figure to {curve_path}")
    
    print(f"\nFinal Test ROC-AUC for {arch.upper()}: {test_auc:.4f}")
    return {
        'model': model,
        'arch': arch,
        'best_val_auc': best_val_auc,
        'test_auc': test_auc,
        'per_task_test': per_task_test,
        'y_true_test': y_true_test,
        'y_probs_test': y_probs_test,
        'history': history
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Train GNN for Molecular Property Prediction")
    parser.add_argument('--arch', type=str, default='gcn', choices=['gcn', 'gin', 'mpnn'])
    parser.add_argument('--epochs', type=int, default=30)
    parser.add_argument('--batch_size', type=int, default=64)
    parser.add_argument('--lr', type=float, default=0.001)
    args = parser.parse_args()
    
    train_gnn(arch=args.arch, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)
