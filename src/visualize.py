"""
Atom Attribution & Saliency Visualization Module.
Calculates gradient-based atom importance (d(logit)/dx) for GNN model predictions 
and generates molecular graphics highlighting toxicophore substructures.
"""

import os
import io
import base64
import torch
import numpy as np
from typing import Dict, List, Tuple, Optional

from src.featurize import smiles_to_graph
from src.dataset import TOX21_TASKS
from src.model import MPNNModel

try:
    from rdkit import Chem
    from rdkit.Chem import Draw
    from rdkit.Chem.Draw import rdMolDraw2D
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False


def compute_atom_saliency(model: torch.nn.Module, smiles: str, task_idx: int = 0) -> Tuple[Optional[np.ndarray], Optional[float], str]:
    """
    Compute gradient-based atom saliency scores for a given SMILES string and target task index.
    
    Returns:
        Tuple[Optional[np.ndarray], Optional[float], str]: 
        (atom_importance_scores, predicted_probability, task_name)
    """
    model.eval()
    graph = smiles_to_graph(smiles)
    if graph is None:
        return None, None, TOX21_TASKS[task_idx]
        
    x = graph.x.clone().detach().requires_grad_(True)
    edge_index = graph.edge_index
    edge_attr = graph.edge_attr if hasattr(graph, 'edge_attr') else None
    batch = torch.zeros(x.size(0), dtype=torch.long)
    
    if isinstance(model, MPNNModel):
        logits = model(x, edge_index, edge_attr, batch)
    else:
        logits = model(x, edge_index, batch)
        
    target_logit = logits[0, task_idx]
    prob = torch.sigmoid(target_logit).item()
    
    # Backpropagate gradient w.r.t. input atom features
    target_logit.backward()
    
    # Saliency = L2 norm of gradient vector per atom
    grads = x.grad  # shape: [num_atoms, feature_dim]
    atom_saliency = torch.norm(grads, dim=-1).detach().cpu().numpy()
    
    # Normalize between 0 and 1
    if atom_saliency.max() > atom_saliency.min():
        atom_saliency = (atom_saliency - atom_saliency.min()) / (atom_saliency.max() - atom_saliency.min())
    else:
        atom_saliency = np.zeros_like(atom_saliency)
        
    return atom_saliency, prob, TOX21_TASKS[task_idx]


def render_molecule_svg(smiles: str, atom_weights: Optional[np.ndarray] = None, width: int = 400, height: int = 350) -> str:
    """Render 2D molecule with atom color highlights based on saliency weights as SVG string."""
    if not HAS_RDKIT:
        return "<svg><text>RDKit not installed</text></svg>"
        
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return "<svg><text>Invalid SMILES</text></svg>"
        
    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    drawer.drawOptions().clearBackground = False
    
    highlight_atoms = []
    highlight_colors = {}
    
    if atom_weights is not None and len(atom_weights) == mol.GetNumAtoms():
        for idx in range(mol.GetNumAtoms()):
            w = float(atom_weights[idx])
            if w > 0.05:
                highlight_atoms.append(idx)
                # Color gradient: Soft yellow (low) to deep red (high importance)
                r = 1.0
                g = max(0.0, 1.0 - w)
                b = max(0.0, 0.2 - 0.2 * w)
                highlight_colors[idx] = (r, g, b)
                
        drawer.DrawMolecule(mol, highlightAtoms=highlight_atoms, highlightAtomColors=highlight_colors)
    else:
        drawer.DrawMolecule(mol)
        
    drawer.FinishDrawing()
    svg_str = drawer.GetDrawingText()
    return svg_str


def render_molecule_png(smiles: str, atom_weights: Optional[np.ndarray] = None, 
                        output_path: Optional[str] = None, width: int = 500, height: int = 400):
    """Render 2D molecule PNG image with atom saliency highlights and save to disk."""
    if not HAS_RDKIT:
        return
        
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return
        
    drawer = rdMolDraw2D.MolDraw2DCairo(width, height)
    drawer.drawOptions().clearBackground = True
    
    highlight_atoms = []
    highlight_colors = {}
    
    if atom_weights is not None and len(atom_weights) == mol.GetNumAtoms():
        for idx in range(mol.GetNumAtoms()):
            w = float(atom_weights[idx])
            if w > 0.05:
                highlight_atoms.append(idx)
                r = 1.0
                g = max(0.0, 1.0 - w)
                b = max(0.0, 0.2 - 0.2 * w)
                highlight_colors[idx] = (r, g, b)
                
        drawer.DrawMolecule(mol, highlightAtoms=highlight_atoms, highlightAtomColors=highlight_colors)
    else:
        drawer.DrawMolecule(mol)
        
    drawer.FinishDrawing()
    
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(drawer.GetDrawingText())
        print(f"Saved atom saliency figure to {output_path}")


def save_sample_saliency_figures(model: torch.nn.Module, output_dir: str = 'results/figures'):
    """Generate and save sample atom saliency PNG figures to results/figures/."""
    os.makedirs(output_dir, exist_ok=True)
    
    samples = [
        ("CC(=O)OC1=CC=CC=C1C(=O)O", "saliency_aspirin.png"),
        ("O=C1C2=CC=CC=C2C(=O)C3=C1C=CC=C3", "saliency_toxicophore.png")
    ]
    
    for smiles, filename in samples:
        weights, prob, task = compute_atom_saliency(model, smiles, task_idx=0)
        out_path = os.path.join(output_dir, filename)
        render_molecule_png(smiles, weights, output_path=out_path)


if __name__ == '__main__':
    from src.model import GCNModel
    dummy_gcn = GCNModel(in_dim=72, hidden_dim=128, num_tasks=12)
    saliency, prob, task = compute_atom_saliency(dummy_gcn, "CC(=O)OC1=CC=CC=C1C(=O)O", task_idx=0)
    print(f"Sample SMILES Saliency Scores: {saliency}")
    print(f"Predicted Probability for {task}: {prob:.4f}")
    save_sample_saliency_figures(dummy_gcn)
    print("Saliency visualization test PASSED!")
