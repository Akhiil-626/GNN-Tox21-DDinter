"""
DDInter Drug-Drug Interaction (DDI) Dataset Module.

Downloads DDInter's 8 ATC-code CSVs, resolves drug names to SMILES via
PubChem (reusing name_to_smiles() from app.py, with on-disk caching so each
unique drug name is only looked up once), converts SMILES pairs to graph
pairs using the existing featurize.smiles_to_graph(), and encodes DDInter's
`Level` column as a 3-class severity label (Minor=0, Moderate=1, Major=2).

Framing note: every row in DDInter is a KNOWN positive interaction -- there
are no "these two drugs do not interact" rows in the raw data. Rather than
fabricate negative examples (which would bake in the assumption that any
pair NOT listed is safe, when it may simply be understudied), this module
frames the task as: given two drugs that ARE known to interact, predict
severity. This avoids introducing noisy pseudo-negative labels.

Splitting note: pairs are split by DRUG IDENTITY (cold-start split), not
randomly by row, so evaluation reflects genuinely unseen drugs -- mirroring
the scaffold-split reasoning already used for Tox21 in dataset.py.
"""

import os
import sys
import json
import time
import urllib.request
from typing import List, Tuple, Dict, Any
from collections import Counter

import pandas as pd
import torch
from tqdm import tqdm

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.featurize import smiles_to_graph
from src.app import name_to_smiles

ATC_CODES = ['A', 'B', 'D', 'H', 'L', 'P', 'R', 'V']
DDINTER_URL_TEMPLATE = "https://ddinter.scbdd.com/static/media/download/ddinter_downloads_code_{code}.csv"

LEVEL_TO_LABEL = {'Minor': 0, 'Moderate': 1, 'Major': 2}
LABEL_TO_LEVEL = {v: k for k, v in LEVEL_TO_LABEL.items()}


def download_ddinter_data(raw_dir: str) -> pd.DataFrame:
    """Download all 8 DDInter ATC-code CSVs (skipping ones already on disk) and concatenate them."""
    os.makedirs(raw_dir, exist_ok=True)
    frames = []

    for code in ATC_CODES:
        csv_path = os.path.join(raw_dir, f"ddinter_downloads_code_{code}.csv")
        if not os.path.exists(csv_path):
            url = DDINTER_URL_TEMPLATE.format(code=code)
            print(f"Downloading DDInter code_{code} from {url}...")
            urllib.request.urlretrieve(url, csv_path)
        frames.append(pd.read_csv(csv_path))

    df = pd.concat(frames, ignore_index=True)
    print(f"Loaded {len(df)} total DDI rows across {len(ATC_CODES)} ATC-code files.")
    return df


def build_smiles_cache(drug_names: List[str], cache_path: str, request_delay: float = 0.2) -> Dict[str, str]:
    """
    Resolve each unique drug name to SMILES via PubChem (name_to_smiles from app.py),
    caching to disk so repeated runs don't re-query PubChem. Only queries names not
    already present in the cache.
    """
    cache: Dict[str, str] = {}
    if os.path.exists(cache_path):
        with open(cache_path, 'r') as f:
            cache = json.load(f)
        print(f"Loaded existing SMILES cache with {len(cache)} entries.")

    unresolved = [n for n in drug_names if n not in cache]
    print(f"{len(drug_names)} unique drug names total, {len(unresolved)} need PubChem lookup.")

    failed = 0
    for name in tqdm(unresolved, desc="Resolving drug names via PubChem"):
        try:
            smiles = name_to_smiles(name)
            cache[name] = smiles
        except Exception as e:
            cache[name] = None  # mark as attempted-but-failed, so we don't retry every run
            failed += 1
        time.sleep(request_delay)  # be a considerate citizen of PubChem's free API

    with open(cache_path, 'w') as f:
        json.dump(cache, f, indent=2)

    total_failed = sum(1 for v in cache.values() if v is None)
    print(f"SMILES resolution complete. {total_failed} / {len(cache)} names failed to resolve (all names ever attempted).")
    print(f"This run: {failed} newly failed out of {len(unresolved)} newly attempted.")
    return cache


class DDInterGraphDataset:
    """
    Dataset wrapper for DDInter drug-pair severity classification.
    Handles CSV download/merge, name->SMILES resolution+caching, graph pair
    construction, and drug-identity (cold-start) splitting.
    """
    def __init__(self, root_dir: str = "data"):
        self.root_dir = root_dir
        self.raw_dir = os.path.join(root_dir, "raw")
        self.processed_dir = os.path.join(root_dir, "processed")

        self.df = download_ddinter_data(self.raw_dir)

        cache_path = os.path.join(self.raw_dir, "ddinter_smiles_cache.json")
        unique_names = sorted(set(self.df['Drug_A']) | set(self.df['Drug_B']))
        self.smiles_cache = build_smiles_cache(unique_names, cache_path)

        self._filter_resolved()
        self._encode_labels()

        self.pairs: List[Tuple[Any, Any, int, str, str]] = []  # (graph_a, graph_b, label, name_a, name_b)
        self._process()

    def _filter_resolved(self):
        """Keep only rows where BOTH drugs successfully resolved to a SMILES string."""
        before = len(self.df)
        resolved_mask = self.df['Drug_A'].map(lambda n: self.smiles_cache.get(n) is not None) & \
                        self.df['Drug_B'].map(lambda n: self.smiles_cache.get(n) is not None)
        self.df = self.df[resolved_mask].reset_index(drop=True)
        after = len(self.df)
        print(f"Kept {after} / {before} rows where both drugs resolved to a valid SMILES.")

    def _encode_labels(self):
        """Map the Level column (Minor/Moderate/Major) to integer labels 0/1/2.

        Rows with Level == 'Unknown' are intentionally dropped, not an error:
        per DDInter's own documentation, 'Unknown' means the interaction's
        description was unavailable or incomplete at the time of curation --
        it is not a 4th severity class, just missing severity data.
        """
        known_mask = self.df['Level'].isin(LEVEL_TO_LABEL.keys())
        n_unknown = (~known_mask).sum()
        if n_unknown > 0:
            print(f"Dropping {n_unknown} rows with Level='Unknown' or other unrecognized "
                  f"values (DDInter's 'Unknown' means incomplete curation data, not a real "
                  f"severity class).")
        self.df = self.df[known_mask].reset_index(drop=True)

        self.df['label'] = self.df['Level'].map(LEVEL_TO_LABEL).astype(int)
        print("Label distribution:", dict(Counter(self.df['label'].map(LABEL_TO_LEVEL))))

    def _process(self):
        processed_file = os.path.join(self.processed_dir, "ddi_graphs.pt")
        os.makedirs(self.processed_dir, exist_ok=True)

        if os.path.exists(processed_file):
            print("Loading pre-processed DDI graph pairs from cache...")
            cached = torch.load(processed_file, weights_only=False)
            self.pairs = cached['pairs']
            print(f"Loaded {len(self.pairs)} cached graph pairs.")
            return

        print("Converting drug-name pairs to molecular graph pairs...")
        graph_cache: Dict[str, Any] = {}  # avoid re-featurizing the same drug repeatedly
        skipped = 0

        for _, row in tqdm(self.df.iterrows(), total=len(self.df)):
            name_a, name_b, label = row['Drug_A'], row['Drug_B'], int(row['label'])

            if name_a not in graph_cache:
                graph_cache[name_a] = smiles_to_graph(self.smiles_cache[name_a])
            if name_b not in graph_cache:
                graph_cache[name_b] = smiles_to_graph(self.smiles_cache[name_b])

            graph_a, graph_b = graph_cache[name_a], graph_cache[name_b]
            if graph_a is None or graph_b is None:
                skipped += 1
                continue

            self.pairs.append((graph_a, graph_b, label, name_a, name_b))

        print(f"Successfully built {len(self.pairs)} graph pairs ({skipped} skipped due to featurization failure).")
        torch.save({'pairs': self.pairs}, processed_file)

    def get_cold_start_splits(self, frac_train: float = 0.8, frac_val: float = 0.1,
                               frac_test: float = 0.1, seed: int = 42):
        """
        Split by DRUG IDENTITY, not by row: each drug is assigned to exactly one
        split, and a pair is kept only if BOTH its drugs fall in the same split.
        Pairs straddling two drug-splits are dropped, avoiding leakage between
        train/val/test through shared drugs.
        """
        import random
        all_drugs = sorted(set(n for _, _, _, a, b in self.pairs for n in (a, b)))
        rng = random.Random(seed)
        rng.shuffle(all_drugs)

        n = len(all_drugs)
        train_cut = int(n * frac_train)
        val_cut = int(n * (frac_train + frac_val))

        train_drugs = set(all_drugs[:train_cut])
        val_drugs = set(all_drugs[train_cut:val_cut])
        test_drugs = set(all_drugs[val_cut:])

        train_pairs, val_pairs, test_pairs, dropped = [], [], [], 0
        for graph_a, graph_b, label, name_a, name_b in self.pairs:
            if name_a in train_drugs and name_b in train_drugs:
                train_pairs.append((graph_a, graph_b, label))
            elif name_a in val_drugs and name_b in val_drugs:
                val_pairs.append((graph_a, graph_b, label))
            elif name_a in test_drugs and name_b in test_drugs:
                test_pairs.append((graph_a, graph_b, label))
            else:
                dropped += 1  # pair straddles two different drug-splits

        print(f"Cold-start split -> Train: {len(train_pairs)}, Val: {len(val_pairs)}, "
              f"Test: {len(test_pairs)}, Dropped (cross-split pairs): {dropped}")
        return train_pairs, val_pairs, test_pairs


if __name__ == '__main__':
    dataset = DDInterGraphDataset(root_dir="data")
    train_p, val_p, test_p = dataset.get_cold_start_splits()
    if train_p:
        print(f"Sample pair -> label: {train_p[0][2]}, graph_a: {train_p[0][0]}, graph_b: {train_p[0][1]}")
    print("DDInter dataset module test PASSED!")