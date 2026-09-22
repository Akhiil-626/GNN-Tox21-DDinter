"""
Molecular Graph Featurization Module (RDKit -> PyTorch Geometric Data)
Converts SMILES strings into graph structures with rich atom and bond features.
"""

from typing import List, Tuple, Optional, Dict, Any
import torch

try:
    from rdkit import Chem
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False

try:
    from torch_geometric.data import Data
    HAS_PYG = True
except ImportError:
    HAS_PYG = False

# Allowed feature values for one-hot encoding
ALLOWED_ATOMS = ['C', 'N', 'O', 'S', 'F', 'Si', 'P', 'Cl', 'Br', 'Mg', 'Na', 'Ca', 'Fe', 'As', 'Al', 'I', 'B', 'V', 'K', 'Tl', 'Yb', 'Sb', 'Sn', 'Ag', 'Pd', 'Co', 'Se', 'Ti', 'Zn', 'H', 'Li', 'Ge', 'Cu', 'Au', 'Ni', 'Cd', 'In', 'Mn', 'Zr', 'Cr', 'Pt', 'Hg', 'Pb']
ALLOWED_HYBRIDIZATIONS = ['SP', 'SP2', 'SP3', 'SP3D', 'SP3D2', 'OTHER']
ALLOWED_BOND_TYPES = ['SINGLE', 'DOUBLE', 'TRIPLE', 'AROMATIC']


def one_hot_encoding(value: Any, allowed_list: List[Any], include_unknown: bool = True) -> List[float]:
    """Helper function to create a one-hot encoding vector."""
    encoding = [0.0] * (len(allowed_list) + (1 if include_unknown else 0))
    if value in allowed_list:
        encoding[allowed_list.index(value)] = 1.0
    elif include_unknown:
        encoding[-1] = 1.0
    return encoding


def get_atom_features(atom) -> List[float]:
    """
    Extract atom-level feature vector (Length = 44 + 6 + 7 + 6 + 7 + 1 + 1 = 72).
    Features:
    - Atom type (one-hot)
    - Formal charge (integer / one-hot)
    - Degree (one-hot)
    - Total Hydrogens (one-hot)
    - Hybridization (one-hot)
    - Is Aromatic (binary)
    - Is In Ring (binary)
    """
    symbol = atom.GetSymbol()
    atom_type_enc = one_hot_encoding(symbol, ALLOWED_ATOMS, include_unknown=True)
    
    charge = atom.GetFormalCharge()
    charge_enc = one_hot_encoding(charge, [-2, -1, 0, 1, 2], include_unknown=True)
    
    degree = atom.GetDegree()
    degree_enc = one_hot_encoding(degree, [0, 1, 2, 3, 4, 5], include_unknown=True)
    
    total_h = atom.GetTotalNumHs()
    total_h_enc = one_hot_encoding(total_h, [0, 1, 2, 3, 4], include_unknown=True)
    
    hybridization = str(atom.GetHybridization())
    hybridization_enc = one_hot_encoding(hybridization, ALLOWED_HYBRIDIZATIONS, include_unknown=True)
    
    is_aromatic = [1.0 if atom.GetIsAromatic() else 0.0]
    is_in_ring = [1.0 if atom.IsInRing() else 0.0]
    
    return atom_type_enc + charge_enc + degree_enc + total_h_enc + hybridization_enc + is_aromatic + is_in_ring


def get_bond_features(bond) -> List[float]:
    """
    Extract bond-level feature vector (Length = 4 + 1 + 1 = 6).
    Features:
    - Bond type (SINGLE, DOUBLE, TRIPLE, AROMATIC)
    - Is Conjugated (binary)
    - Is In Ring (binary)
    """
    bt = str(bond.GetBondType())
    bond_type_enc = one_hot_encoding(bt, ALLOWED_BOND_TYPES, include_unknown=False)
    is_conjugated = [1.0 if bond.GetIsConjugated() else 0.0]
    is_in_ring = [1.0 if bond.IsInRing() else 0.0]
    return bond_type_enc + is_conjugated + is_in_ring


def smiles_to_graph(smiles: str, y: Optional[List[float]] = None) -> Optional[Any]:
    """
    Convert a SMILES string into a PyTorch Geometric Data graph object.
    
    Parameters:
        smiles (str): Canonical or valid SMILES string.
        y (List[float], optional): Target labels (e.g. 12 Tox21 assays).
        
    Returns:
        torch_geometric.data.Data or PyTorch Data-like dict: The graph data representation.
    """
    if not HAS_RDKIT:
        raise ImportError("RDKit is required for molecular featurization.")
        
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
        
    # Extract Node Features
    node_features = []
    for atom in mol.GetAtoms():
        node_features.append(get_atom_features(atom))
    x = torch.tensor(node_features, dtype=torch.float)
    
    # Extract Edge Indices & Edge Features (Undirected)
    edge_indices = []
    edge_features = []
    
    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        b_feat = get_bond_features(bond)
        
        # Add direction i -> j
        edge_indices.append([i, j])
        edge_features.append(b_feat)
        
        # Add direction j -> i
        edge_indices.append([j, i])
        edge_features.append(b_feat)
        
    if len(edge_indices) == 0:
        # Single atom molecule (e.g. noble gas or isolated ion)
        edge_index = torch.empty((2, 0), dtype=torch.long)
        edge_attr = torch.empty((0, 6), dtype=torch.float)
    else:
        edge_index = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
        edge_attr = torch.tensor(edge_features, dtype=torch.float)
        
    y_tensor = torch.tensor([y], dtype=torch.float) if y is not None else None
    
    if HAS_PYG:
        data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr, y=y_tensor, smiles=smiles)
        data.num_nodes = x.size(0)
        return data
    else:
        # Fallback dict container
        return {
            'x': x,
            'edge_index': edge_index,
            'edge_attr': edge_attr,
            'y': y_tensor,
            'smiles': smiles,
            'num_nodes': x.size(0)
        }


if __name__ == '__main__':
    # Simple self-test
    sample_smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"  # Aspirin
    print(f"Featurizing sample SMILES: {sample_smiles}")
    graph = smiles_to_graph(sample_smiles, y=[0.0] * 12)
    if graph is not None:
        print(f"Graph nodes shape (x): {graph.x.shape}")
        print(f"Graph edge_index shape: {graph.edge_index.shape}")
        print(f"Graph edge_attr shape: {graph.edge_attr.shape}")
        print("Featurizer test PASSED!")
    else:
        print("Featurizer test FAILED!")
