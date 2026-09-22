"""
Tox21 Dataset & Bemis-Murcko Scaffold Splitter Module
Downloads and parses Tox21 dataset across 12 bioassay endpoints.
Enforces strict Bemis-Murcko scaffold splitting (80% train, 10% val, 10% test).
"""

import os
import urllib.request
import pandas as pd
import numpy as np
import torch
from typing import List, Tuple, Dict, Optional, Any
from collections import defaultdict
from tqdm import tqdm

from src.featurize import smiles_to_graph

try:
    from rdkit import Chem
    from rdkit.Chem.Scaffolds import MurckoScaffold
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False

try:
    from torch_geometric.data import Dataset, InMemoryDataset, Data
    from torch_geometric.loader import DataLoader
    HAS_PYG = True
except ImportError:
    HAS_PYG = False

# The 12 official Tox21 Bioassay Endpoints
TOX21_TASKS = [
    'NR-AR',
    'NR-AR-LBD',
    'NR-AhR',
    'NR-Aromatase',
    'NR-ER',
    'NR-ER-LBD',
    'NR-PPAR-gamma',
    'SR-ARE',
    'SR-ATAD5',
    'SR-HSE',
    'SR-MMP',
    'SR-p53'
]

TOX21_URL = "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz"


def download_tox21_data(raw_dir: str) -> str:
    """Download Tox21 CSV if it does not already exist."""
    os.makedirs(raw_dir, exist_ok=True)
    csv_path = os.path.join(raw_dir, "tox21.csv")
    gz_path = os.path.join(raw_dir, "tox21.csv.gz")

    if os.path.exists(csv_path):
        return csv_path

    if not os.path.exists(gz_path):
        print(f"Downloading Tox21 dataset from {TOX21_URL}...")
        urllib.request.urlretrieve(TOX21_URL, gz_path)
        print("Download complete.")

    import gzip
    with gzip.open(gz_path, 'rt', encoding='utf-8') as f_in:
        with open(csv_path, 'w', encoding='utf-8') as f_out:
            f_out.write(f_in.read())

    return csv_path


def generate_scaffold(smiles: str, include_chirality: bool = False) -> str:
    """Compute Bemis-Murcko scaffold for a given SMILES string."""
    if not HAS_RDKIT:
        return ""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return ""
    try:
        scaffold = MurckoScaffold.MurckoScaffoldSmiles(mol=mol, includeChirality=include_chirality)
        return scaffold
    except Exception:
        return ""


def scaffold_split(df: pd.DataFrame, smiles_col: str = 'smiles', 
                   frac_train: float = 0.8, frac_val: float = 0.1, frac_test: float = 0.1, 
                   seed: int = 42) -> Tuple[List[int], List[int], List[int]]:
    """
    Perform Bemis-Murcko Scaffold Split on a DataFrame containing SMILES strings.
    Groups molecules by scaffold and assigns whole scaffold groups to splits to avoid leakage.
    Uses `seed` to deterministically shuffle equal-sized scaffold groups.
    """
    import random
    scaffolds = defaultdict(list)
    for idx, smiles in enumerate(df[smiles_col]):
        scaf = generate_scaffold(smiles)
        scaffolds[scaf].append(idx)

    scaffold_sets = list(scaffolds.values())
    
    # Shuffle equal-size scaffold sets with seed for reproducibility / cross-validation
    rng = random.Random(seed)
    by_size = defaultdict(list)
    for scaf_set in scaffold_sets:
        by_size[len(scaf_set)].append(scaf_set)

    sorted_sizes = sorted(by_size.keys(), reverse=True)
    scaffold_sets = []
    for size in sorted_sizes:
        group = by_size[size]
        rng.shuffle(group)
        scaffold_sets.extend(group)

    total_len = len(df)
    train_cutoff = total_len * frac_train
    val_cutoff = total_len * (frac_train + frac_val)

    train_idx, val_idx, test_idx = [], [], []

    for scaf_set in scaffold_sets:
        if len(train_idx) + len(scaf_set) <= train_cutoff:
            train_idx.extend(scaf_set)
        elif len(train_idx) + len(val_idx) + len(scaf_set) <= val_cutoff:
            val_idx.extend(scaf_set)
        else:
            test_idx.extend(scaf_set)

    return train_idx, val_idx, test_idx


class Tox21GraphDataset:
    """
    Dataset wrapper for Tox21 Molecular Graphs.
    Handles graph featurization, label extraction, NaN loss masking, and scaffold splitting.
    """
    def __init__(self, root_dir: str = "data"):
        self.root_dir = root_dir
        self.raw_dir = os.path.join(root_dir, "raw")
        self.processed_dir = os.path.join(root_dir, "processed")
        
        csv_path = download_tox21_data(self.raw_dir)
        self.df = pd.read_csv(csv_path)
        
        # Verify tasks in dataframe
        self.tasks = [t for t in TOX21_TASKS if t in self.df.columns]
        print(f"Loaded Tox21 dataframe with {len(self.df)} molecules and {len(self.tasks)} tasks.")
        
        self.graphs = []
        self.valid_indices = []
        
        self._process()
        
    def _process(self):
        processed_file = os.path.join(self.processed_dir, "tox21_graphs.pt")
        os.makedirs(self.processed_dir, exist_ok=True)
        
        if os.path.exists(processed_file):
            print("Loading pre-processed molecular graphs from cache...")
            cached_data = torch.load(processed_file, weights_only=False)
            graphs = cached_data.get('graphs', [])
            
            # Cache invalidation check: verify feature vector dimension (72)
            if len(graphs) > 0 and hasattr(graphs[0], 'x') and graphs[0].x.size(1) == 72:
                self.graphs = graphs
                self.valid_indices = cached_data['valid_indices']
                print(f"Loaded {len(self.graphs)} valid cached graphs (72-dim node features).")
                return
            else:
                print("Cached graphs are invalid or match outdated feature schema (expected 72-dim). Re-processing dataset...")

        print("Converting SMILES to molecular graphs...")
        for idx, row in tqdm(self.df.iterrows(), total=len(self.df)):
            smiles = row['smiles']
            labels = [float(row[t]) if not pd.isna(row[t]) else np.nan for t in self.tasks]
            
            graph = smiles_to_graph(smiles, y=labels)
            if graph is not None:
                self.graphs.append(graph)
                self.valid_indices.append(idx)
                
        print(f"Successfully processed {len(self.graphs)} / {len(self.df)} molecules.")
        torch.save({'graphs': self.graphs, 'valid_indices': self.valid_indices}, processed_file)

    def get_scaffold_splits(self, frac_train: float = 0.8, frac_val: float = 0.1, frac_test: float = 0.1) -> Tuple[List[Any], List[Any], List[Any]]:
        """Perform Bemis-Murcko scaffold split on the processed dataset."""
        sub_df = self.df.iloc[self.valid_indices].reset_index(drop=True)
        train_idx, val_idx, test_idx = scaffold_split(sub_df, 'smiles', frac_train, frac_val, frac_test)
        
        train_graphs = [self.graphs[i] for i in train_idx]
        val_graphs = [self.graphs[i] for i in val_idx]
        test_graphs = [self.graphs[i] for i in test_idx]
        
        print(f"Scaffold Split Summary -> Train: {len(train_graphs)}, Val: {len(val_graphs)}, Test: {len(test_graphs)}")
        return train_graphs, val_graphs, test_graphs


if __name__ == '__main__':
    # Test loading & scaffold splitting
    dataset = Tox21GraphDataset(root_dir="data")
    train_g, val_g, test_g = dataset.get_scaffold_splits()
    print(f"Sample Graph: {train_g[0]}")
    print("Dataset module test PASSED!")
