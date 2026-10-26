"""
Small chemistry helpers shared by the cross-fitting and risk-profile code.

* canonical_key()        stable molecule identity across datasets (largest fragment,
                         no stereochemistry), so a drug is recognised whether it came
                         from DDInter, Tox21 or a CYP file.
* balanced_group_folds() assigns groups (e.g. Bemis-Murcko scaffolds) to K folds with
                         near-equal sizes. Pure python, unit tested.
* CYP_ISOFORMS           the five CYP enzymes handled by the optional metabolism features.

RDKit is imported lazily so everything except canonical_key() works without it.
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Dict, List, Optional, Sequence

CYP_ISOFORMS = ('CYP1A2', 'CYP2C9', 'CYP2C19', 'CYP2D6', 'CYP3A4')


def canonical_key(smiles: str) -> Optional[str]:
    """
    Identity key for a molecule: canonical, non-stereo SMILES of its largest fragment
    (drops salts / counter-ions). Returns None for invalid SMILES or when RDKit is absent.
    """
    try:
        from rdkit import Chem
    except ImportError:
        return None
    if not isinstance(smiles, str) or not smiles.strip():
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    frags = Chem.GetMolFrags(mol, asMols=True)
    if len(frags) > 1:
        mol = max(frags, key=lambda m: m.GetNumHeavyAtoms())
    return Chem.MolToSmiles(mol, isomericSmiles=False)


def balanced_group_folds(group_ids: Sequence[str], k: int, seed: int = 0) -> List[int]:
    """
    Assign every item to one of k folds so that all items sharing a group id land in
    the SAME fold (no scaffold straddles two folds) while fold sizes stay balanced.

    Greedy: groups are shuffled (seeded), sorted largest-first, and each is placed in
    the currently smallest fold.
    """
    if k < 2:
        raise ValueError("Need at least 2 folds.")
    groups: Dict[str, List[int]] = defaultdict(list)
    for i, g in enumerate(group_ids):
        groups[g].append(i)

    rng = random.Random(seed)
    items = list(groups.values())
    rng.shuffle(items)
    items.sort(key=len, reverse=True)      # stable sort keeps the seeded shuffle among ties

    sizes = [0] * k
    folds = [-1] * len(group_ids)
    for members in items:
        # Smallest fold wins; ties are broken at random (seeded). Always taking the lowest
        # index would put the single largest group in fold 0 every time and bias that fold.
        smallest = min(sizes)
        target = rng.choice([f for f in range(k) if sizes[f] == smallest])
        for i in members:
            folds[i] = target
        sizes[target] += len(members)
    return folds
