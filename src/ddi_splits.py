"""
Drug-level evaluation splits for DDI severity prediction (S0 / S1 / S2).

Why this exists
---------------
The original cold-start split in ddi_dataset.py keeps only pairs whose two drugs
fall in the *same* bucket, which silently discards every pair that crosses a
bucket boundary. Real use looks different: a clinician usually asks about one
NEW drug paired with a drug the model already knows. This module therefore
evaluates three scenarios, following the S0/S1/S2 convention used in the
cold-start DDI literature:

    S0  both drugs were seen in training            (warm / transductive)
    S1  exactly one drug is unseen                  (new drug + known drug)
    S2  both drugs are unseen                       (two new drugs)

Construction (all by drug identity, never by row):
  1. Drugs are shuffled with a seed and divided into train / val / test drugs.
  2. Training pairs  : both drugs in the train-drug set, minus a held-out slice
                       of pairs (S0 test) taken from the same pool.
  3. S0 test pairs   : pairs between two TRAIN drugs that were withheld from
                       training (the model has seen each drug, never this pair).
  4. S1 test pairs   : one TEST drug + one TRAIN drug.
  5. S2 test pairs   : both drugs are TEST drugs.
  6. Validation uses the analogous S1-style construction with VAL drugs, so
     model selection never touches test drugs.

The module is intentionally free of torch / RDKit so it can be unit tested
anywhere. Pairs are passed in as any sequence of tuples; the caller supplies
accessor functions for the two drug names.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Sequence, Set, Tuple


@dataclass
class DDISplit:
    """Container for one seeded split. Each field is a list of indices into the pair list."""
    seed: int
    train: List[int] = field(default_factory=list)
    val: List[int] = field(default_factory=list)
    test_s0: List[int] = field(default_factory=list)
    test_s1: List[int] = field(default_factory=list)
    test_s2: List[int] = field(default_factory=list)
    train_drugs: Set[str] = field(default_factory=set)
    val_drugs: Set[str] = field(default_factory=set)
    test_drugs: Set[str] = field(default_factory=set)

    def sizes(self) -> Dict[str, int]:
        return {
            'train': len(self.train), 'val': len(self.val),
            'test_s0': len(self.test_s0), 'test_s1': len(self.test_s1),
            'test_s2': len(self.test_s2),
        }

    def test_sets(self) -> Dict[str, List[int]]:
        return {'S0': self.test_s0, 'S1': self.test_s1, 'S2': self.test_s2}


def make_drug_splits(
    pairs: Sequence[Any],
    drug_a: Callable[[Any], str],
    drug_b: Callable[[Any], str],
    seed: int = 42,
    frac_train_drugs: float = 0.7,
    frac_val_drugs: float = 0.1,
    s0_holdout_frac: float = 0.1,
) -> DDISplit:
    """
    Build S0/S1/S2 splits. See module docstring for the exact construction.

    Parameters
    ----------
    pairs : sequence of pair records (any type).
    drug_a, drug_b : functions returning the drug name/ID of each side of a pair.
    seed : controls the drug shuffle and the S0 hold-out draw.
    frac_train_drugs, frac_val_drugs : share of DRUGS (not pairs); the remainder are test drugs.
    s0_holdout_frac : share of train-drug/train-drug pairs withheld as the S0 test set.
    """
    if not 0 < frac_train_drugs < 1 or not 0 <= frac_val_drugs < 1:
        raise ValueError("Drug fractions must lie in (0, 1).")
    if frac_train_drugs + frac_val_drugs >= 1:
        raise ValueError("Train + val drug fractions must leave some drugs for test.")

    all_drugs = sorted({d for p in pairs for d in (drug_a(p), drug_b(p))})
    rng = random.Random(seed)
    rng.shuffle(all_drugs)

    n = len(all_drugs)
    n_train = int(n * frac_train_drugs)
    n_val = int(n * frac_val_drugs)
    train_drugs = set(all_drugs[:n_train])
    val_drugs = set(all_drugs[n_train:n_train + n_val])
    test_drugs = set(all_drugs[n_train + n_val:])

    split = DDISplit(seed=seed, train_drugs=train_drugs, val_drugs=val_drugs, test_drugs=test_drugs)

    train_pool: List[int] = []
    for i, p in enumerate(pairs):
        a, b = drug_a(p), drug_b(p)
        a_tr, b_tr = a in train_drugs, b in train_drugs
        a_te, b_te = a in test_drugs, b in test_drugs
        a_va, b_va = a in val_drugs, b in val_drugs

        if a_tr and b_tr:
            train_pool.append(i)
        elif (a_te and b_tr) or (a_tr and b_te):
            split.test_s1.append(i)
        elif a_te and b_te:
            split.test_s2.append(i)
        elif (a_va and b_tr) or (a_tr and b_va):
            split.val.append(i)
        # Pairs touching val drugs together with test drugs (or val-val) are dropped:
        # keeping them would let model selection see a drug that is also a test drug's partner.

    # Hold out a slice of train-pool pairs as S0 (seen drugs, unseen pair).
    pool = list(train_pool)
    rng.shuffle(pool)
    n_s0 = int(len(pool) * s0_holdout_frac)
    split.test_s0 = sorted(pool[:n_s0])
    split.train = sorted(pool[n_s0:])
    return split


def assert_no_leakage(split: DDISplit, pairs: Sequence[Any],
                      drug_a: Callable[[Any], str], drug_b: Callable[[Any], str]) -> None:
    """Raise AssertionError if any split constraint is violated. Used by the unit tests."""
    train_pair_set = {frozenset((drug_a(pairs[i]), drug_b(pairs[i]))) for i in split.train}
    train_seen_drugs = {d for i in split.train for d in (drug_a(pairs[i]), drug_b(pairs[i]))}

    for i in split.test_s0:
        a, b = drug_a(pairs[i]), drug_b(pairs[i])
        assert frozenset((a, b)) not in train_pair_set, "S0 pair leaked into training"
        assert a in split.train_drugs and b in split.train_drugs, "S0 must use train drugs only"

    for i in split.test_s1:
        a, b = drug_a(pairs[i]), drug_b(pairs[i])
        n_test = (a in split.test_drugs) + (b in split.test_drugs)
        assert n_test == 1, "S1 must contain exactly one test drug"
        assert (a in split.train_drugs) or (b in split.train_drugs), "S1 partner must be a train drug"

    for i in split.test_s2:
        a, b = drug_a(pairs[i]), drug_b(pairs[i])
        assert a in split.test_drugs and b in split.test_drugs, "S2 must contain two test drugs"

    for i in split.train + split.val:
        a, b = drug_a(pairs[i]), drug_b(pairs[i])
        assert a not in split.test_drugs and b not in split.test_drugs, "test drug used in train/val"

    for d in split.test_drugs:
        assert d not in train_seen_drugs, "test drug appears in training pairs"


def dedupe_pairs(
    pairs: Sequence[Any],
    drug_a: Callable[[Any], str],
    drug_b: Callable[[Any], str],
    label: Callable[[Any], int],
) -> Tuple[List[Any], Dict[str, int]]:
    """
    Collapse duplicate UNORDERED drug pairs before splitting.

    DDInter can list the same pair twice (as A,B and B,A, or in two ATC files).
    Without this step one copy could land in training and the other in the S0 test
    set, silently leaking the answer. When copies disagree on severity, the MOST
    SEVERE label is kept (the conservative choice for a safety tool) and the
    disagreement is counted.

    Returns (unique_pairs, stats) where stats has keys:
      n_input, n_unique, n_duplicates_removed, n_conflicting
    Order of first appearance is preserved.
    """
    best: Dict[frozenset, Any] = {}
    order: List[frozenset] = []
    conflicts = 0
    for p in pairs:
        a, b = drug_a(p), drug_b(p)
        if a == b:
            continue  # a drug paired with itself carries no interaction information
        key = frozenset((a, b))
        if key not in best:
            best[key] = p
            order.append(key)
        else:
            old = best[key]
            if label(p) != label(old):
                conflicts += 1
            if label(p) > label(old):
                best[key] = p
    unique = [best[k] for k in order]
    stats = {
        'n_input': len(pairs),
        'n_unique': len(unique),
        'n_duplicates_removed': len(pairs) - len(unique),
        'n_conflicting': conflicts,
    }
    return unique, stats


def merge_pairs_by_identity(
    pairs: Sequence[Any],
    identity_of: Dict[str, str],
    drug_a: Callable[[Any], str],
    drug_b: Callable[[Any], str],
    label: Callable[[Any], int],
) -> Tuple[List[Tuple[str, str, int]], Dict[str, int]]:
    """
    Re-key pairs from drug NAMES to molecule IDENTITIES.

    Different names often denote one molecule ("Brimonidine" and "Brimonidine (ophthalmic)",
    salts, hydrates). Splitting by name would then put the same molecule in both train and
    test, which inflates new-drug (S1/S2) results. Every name is replaced by its identity
    key (e.g. a canonical SMILES) so a molecule can only ever sit on one side of a split.

    Pairs whose two names collapse to one identity are dropped by the caller's
    dedupe_pairs() step (self-pairs). Returns ((id_a, id_b, label) tuples, stats) with stats:
      n_names, n_identities, n_names_merged
    """
    mapped: List[Tuple[str, str, int]] = []
    names = set()
    for p in pairs:
        a, b = drug_a(p), drug_b(p)
        names.update((a, b))
        mapped.append((identity_of[a], identity_of[b], label(p)))
    identities = {identity_of[n] for n in names}
    return mapped, {'n_names': len(names), 'n_identities': len(identities),
                    'n_names_merged': len(names) - len(identities)}
