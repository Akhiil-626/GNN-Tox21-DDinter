"""
Evaluation and Benchmark Comparison Module.
Computes ROC-AUC, PR-AUC, Sensitivity, Specificity per task across GNN models and Morgan Fingerprints Random Forest baseline.
Generates metrics CSV and high-resolution comparison figures.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Any

import torch
from torch_geometric.loader import DataLoader
from sklearn.metrics import roc_auc_score, average_precision_score, confusion_matrix, roc_curve
from sklearn.ensemble import RandomForestClassifier
from rdkit import Chem
from rdkit.Chem import AllChem

from src.dataset import Tox21GraphDataset, TOX21_TASKS
from src.model import get_model, MPNNModel
from src.train import evaluate_model


def get_morgan_fingerprints(smiles_list: List[str], radius: int = 2, nBits: int = 2048) -> np.ndarray:
    """Generate 2048-bit Radius 2 Morgan Fingerprints for SMILES strings."""
    try:
        from rdkit.Chem import rdFingerprintGenerator
        generator = rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=nBits)
        use_gen = True
    except AttributeError:
        use_gen = False

    fps = []
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles)
        if mol is not None:
            if use_gen:
                fp = generator.GetCountFingerprintAsNumPy(mol)
                fp_binary = (fp > 0).astype(np.float32)
                fps.append(fp_binary)
            else:
                fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=nBits)
                fps.append(np.array(fp, dtype=np.float32))
        else:
            fps.append(np.zeros(nBits, dtype=np.float32))
    return np.vstack(fps)


def train_evaluate_rf_baseline(dataset: Tox21GraphDataset) -> Dict[str, Any]:
    """Train Random Forest multi-task baseline on Morgan Fingerprints and return predicted probability matrix."""
    print("\n--- Training Morgan Fingerprints + Random Forest Baseline ---")
    train_graphs, val_graphs, test_graphs = dataset.get_scaffold_splits()
    
    train_smiles = [g.smiles for g in train_graphs]
    test_smiles = [g.smiles for g in test_graphs]
    
    X_train = get_morgan_fingerprints(train_smiles)
    X_test = get_morgan_fingerprints(test_smiles)
    
    y_train_mat = np.vstack([g.y.numpy().reshape(12) for g in train_graphs])
    y_test_mat = np.vstack([g.y.numpy().reshape(12) for g in test_graphs])
    
    y_probs_mat = np.full_like(y_test_mat, np.nan)
    per_task_auc = {}
    valid_aucs = []
    
    for i, task_name in enumerate(dataset.tasks):
        y_tr = y_train_mat[:, i]
        y_te = y_test_mat[:, i]
        
        train_mask = ~np.isnan(y_tr)
        test_mask = ~np.isnan(y_te)
        
        X_tr, y_tr_valid = X_train[train_mask], y_tr[train_mask]
        X_te, y_te_valid = X_test[test_mask], y_te[test_mask]
        
        if len(np.unique(y_tr_valid)) > 1 and len(np.unique(y_te_valid)) == 2:
            rf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1, class_weight='balanced')
            rf.fit(X_tr, y_tr_valid)
            probs = rf.predict_proba(X_te)[:, 1]
            y_probs_mat[test_mask, i] = probs
            
            auc = roc_auc_score(y_te_valid, probs)
            per_task_auc[task_name] = auc
            valid_aucs.append(auc)
        else:
            per_task_auc[task_name] = np.nan
            
    mean_auc = np.nanmean(valid_aucs)
    print(f"Random Forest + Morgan FP Test Mean ROC-AUC: {mean_auc:.4f}")
    return {'per_task': per_task_auc, 'mean_auc': mean_auc, 'y_probs_test': y_probs_mat, 'y_true_test': y_test_mat}


def compute_detailed_metrics(y_true: np.ndarray, y_probs: np.ndarray, threshold: float = 0.5) -> Dict[str, Any]:
    """Compute ROC-AUC, PR-AUC, Sensitivity, Specificity, and Accuracy per task."""
    task_metrics = []
    
    for i, task_name in enumerate(TOX21_TASKS):
        y_t = y_true[:, i]
        y_p = y_probs[:, i]
        
        mask = ~np.isnan(y_t)
        y_t_val = y_t[mask]
        y_p_val = y_p[mask]
        
        if len(y_t_val) > 0 and len(np.unique(y_t_val)) == 2:
            roc_auc = roc_auc_score(y_t_val, y_p_val)
            pr_auc = average_precision_score(y_t_val, y_p_val)
            
            y_pred = (y_p_val >= threshold).astype(int)
            tn, fp, fn, tp = confusion_matrix(y_t_val, y_pred, labels=[0, 1]).ravel()
            
            sens = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
            acc = (tp + tn) / len(y_t_val)
            
            task_metrics.append({
                'Task': task_name,
                'ROC-AUC': roc_auc,
                'PR-AUC': pr_auc,
                'Sensitivity': sens,
                'Specificity': spec,
                'Accuracy': acc
            })
        else:
            task_metrics.append({
                'Task': task_name,
                'ROC-AUC': np.nan,
                'PR-AUC': np.nan,
                'Sensitivity': np.nan,
                'Specificity': np.nan,
                'Accuracy': np.nan
            })
            
    df_metrics = pd.DataFrame(task_metrics)
    return df_metrics


def generate_plots(y_true: np.ndarray, y_probs_dict: Dict[str, np.ndarray], output_dir: str = 'results/figures'):
    """Generate high-resolution ROC curves and task metric comparison plots."""
    os.makedirs(output_dir, exist_ok=True)
    sns.set_theme(style='darkgrid')
    
    # 1. Multi-Model Macro ROC Curves Plot
    plt.figure(figsize=(9, 7))
    
    for model_name, y_probs in y_probs_dict.items():
        # Aggregate all valid ground truth and predictions across tasks
        y_t_flat = []
        y_p_flat = []
        for i in range(12):
            mask = ~np.isnan(y_true[:, i])
            y_t_flat.extend(y_true[mask, i])
            y_p_flat.extend(y_probs[mask, i])
            
        fpr, tpr, _ = roc_curve(y_t_flat, y_p_flat)
        auc_val = roc_auc_score(y_t_flat, y_p_flat)
        plt.plot(fpr, tpr, lw=2.5, label=f"{model_name} (Macro ROC-AUC = {auc_val:.3f})")
        
    plt.plot([0, 1], [0, 1], 'k--', lw=1.5, label='Random Chance (AUC = 0.500)')
    plt.xlabel('False Positive Rate (1 - Specificity)', fontsize=12)
    plt.ylabel('True Positive Rate (Sensitivity)', fontsize=12)
    plt.title('Tox21 Benchmark ROC Curves (Scaffold Split)', fontsize=14, fontweight='bold')
    plt.legend(loc='lower right', fontsize=11)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'roc_curves.png'), dpi=300)
    plt.close()
    
    print(f"Saved ROC curves plot to {os.path.join(output_dir, 'roc_curves.png')}")


def run_full_evaluation(models_dict: Dict[str, Any], dataset: Tox21GraphDataset, results_dir: str = 'results'):
    """Execute full evaluation pipeline, compute CSV metrics, and save figures."""
    os.makedirs(results_dir, exist_ok=True)
    fig_dir = os.path.join(results_dir, 'figures')
    os.makedirs(fig_dir, exist_ok=True)
    
    _, _, test_graphs = dataset.get_scaffold_splits()
    test_loader = DataLoader(test_graphs, batch_size=64, shuffle=False)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    all_dfs = []
    y_probs_dict = {}
    y_true_test = None
    
    for name, model in models_dict.items():
        if isinstance(model, dict) and 'y_probs_test' in model:
            # Pre-evaluated model result dictionary
            y_probs = model['y_probs_test']
            y_true_test = model['y_true_test']
        else:
            _, _, y_true_test, y_probs = evaluate_model(model, test_loader, device)
            
        y_probs_dict[name] = y_probs
        df_m = compute_detailed_metrics(y_true_test, y_probs)
        df_m['Model'] = name
        all_dfs.append(df_m)
        
    # RF Baseline evaluation with full metrics
    rf_res = train_evaluate_rf_baseline(dataset)
    y_probs_dict['RF (Morgan FP)'] = rf_res['y_probs_test']
    rf_df = compute_detailed_metrics(rf_res['y_true_test'], rf_res['y_probs_test'])
    rf_df['Model'] = 'RF (Morgan FP)'
    all_dfs.append(rf_df)
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    csv_path = os.path.join(results_dir, 'metrics.csv')
    combined_df.to_csv(csv_path, index=False)
    print(f"Saved comprehensive metrics to {csv_path}")
    
    # Generate ROC plots and sample saliency figures
    generate_plots(y_true_test, y_probs_dict, fig_dir)
    
    first_model = list(models_dict.values())[0]
    if isinstance(first_model, torch.nn.Module):
        from src.visualize import save_sample_saliency_figures
        save_sample_saliency_figures(first_model, fig_dir)
        
    return combined_df


if __name__ == '__main__':
    print("--- Running Full Benchmark Evaluation Suite (GCN vs GIN vs MPNN vs RF Baseline) ---")
    dataset = Tox21GraphDataset(root_dir="data")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    models_dict = {}
    
    for arch in ['gcn', 'gin', 'mpnn']:
        model_path = os.path.join("models", f"best_{arch}.pt")
        model_name = arch.upper()
        
        if os.path.exists(model_path):
            print(f"Loading trained {model_name} weights from {model_path}...")
            ckpt = torch.load(model_path, map_location=device, weights_only=False)
            if isinstance(ckpt, dict) and 'config' in ckpt:
                cfg = ckpt['config']
                model = get_model(cfg.get('arch', arch), in_dim=cfg.get('in_dim', 72), 
                                  edge_dim=cfg.get('edge_dim', 6), hidden_dim=cfg.get('hidden_dim', 128), num_tasks=12).to(device)
                model.load_state_dict(ckpt['state_dict'])
            elif isinstance(ckpt, dict) and 'state_dict' in ckpt:
                model = get_model(arch, in_dim=72, edge_dim=6, hidden_dim=128, num_tasks=12).to(device)
                model.load_state_dict(ckpt['state_dict'])
            else:
                model = get_model(arch, in_dim=72, edge_dim=6, hidden_dim=128, num_tasks=12).to(device)
                model.load_state_dict(ckpt)
            models_dict[model_name] = model
        else:
            print(f"Training {model_name} model for benchmark evaluation...")
            from src.train import train_gnn
            res = train_gnn(arch, epochs=25, batch_size=64)
            models_dict[model_name] = res['model']
            
    df_results = run_full_evaluation(models_dict, dataset)
    print("\n--- Benchmark Evaluation Summary Table ---")
    print(df_results.to_string())

