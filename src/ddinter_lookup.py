"""
DDInter local drug-drug interaction record lookup module.
Provides pure functions to canonicalize SMILES, load DDInter bulk datasets and SMILES cache,
resolve input names, look up interactions, compute partner severity distributions,
find structurally similar drugs via Morgan fingerprints, and construct structural analogues.
"""

import json
import os
import warnings
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Set

import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
from rdkit import RDLogger

# Suppress minor RDKit parse warnings for cleaner logs
RDLogger.DisableLog("rdApp.*")

ATC_CODES = ["A", "B", "D", "H", "L", "P", "R", "V"]
SEVERITY_ORDER = ["Minor", "Moderate", "Major"]


class DDInterData:
    """Holds indexed DDInter dataset objects for rapid in-memory lookups."""

    def __init__(
        self,
        name_to_id: Dict[str, str],
        id_to_name: Dict[str, str],
        id_to_smiles: Dict[str, Optional[str]],
        canon_to_id: Dict[str, str],
        pair_levels: Dict[frozenset, Set[str]],
        partner_levels: Dict[str, Dict[str, str]],
        fingerprints: Dict[str, Any],
    ):
        self.name_to_id = name_to_id
        self.id_to_name = id_to_name
        self.id_to_smiles = id_to_smiles
        self.canon_to_id = canon_to_id
        self.pair_levels = pair_levels
        self.partner_levels = partner_levels
        self.fingerprints = fingerprints

    def __len__(self) -> int:
        return len(self.pair_levels)


def canonical_smiles(smiles: Optional[str]) -> Optional[str]:
    """
    Canonicalize a SMILES string using RDKit without stereochemistry flags.
    Returns None for empty, whitespace-only, non-string, or unparseable input.
    """
    if not smiles or not isinstance(smiles, str) or not smiles.strip():
        return None
    try:
        mol = Chem.MolFromSmiles(smiles.strip())
        if mol is None:
            return None
        return Chem.MolToSmiles(mol, isomericSmiles=False)
    except Exception:
        return None


def load_ddinter(
    raw_dir: str = "data/raw",
    cache_path: str = "data/raw/ddinter_smiles_cache.json",
) -> Optional[DDInterData]:
    """
    Load DDInter bulk CSVs and SMILES cache into a single DDInterData container.

    Holds:
      - name_to_id: lowercase name -> DDInter ID
      - id_to_name: DDInter ID -> primary name
      - id_to_smiles: DDInter ID -> canonical SMILES or None
      - canon_to_id: canonical SMILES -> DDInter ID
      - pair_levels: frozenset({id_a, id_b}) -> set of Level strings
      - partner_levels: ID -> {partner ID: most severe known level or "Unrated"}
      - fingerprints: ID -> Morgan fingerprint (radius 2, 2048 bits)
    """
    if not os.path.exists(cache_path):
        warnings.warn(f"DDInter SMILES cache not found at '{cache_path}'.")
        return None

    existing_csvs = []
    for code in ATC_CODES:
        csv_path = os.path.join(raw_dir, f"ddinter_downloads_code_{code}.csv")
        if os.path.exists(csv_path):
            existing_csvs.append(csv_path)
        else:
            warnings.warn(f"DDInter CSV missing for ATC code {code}: '{csv_path}'")

    if not existing_csvs:
        warnings.warn(f"No DDInter CSVs found in '{raw_dir}'.")
        return None

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            cache = json.load(f)
    except Exception as e:
        warnings.warn(f"Failed to load DDInter SMILES cache '{cache_path}': {e}")
        return None

    # Canonicalize each unique drug name in cache once
    name_to_canon: Dict[str, Optional[str]] = {}
    for name, raw_smiles in cache.items():
        if raw_smiles:
            name_to_canon[name] = canonical_smiles(raw_smiles)

    name_to_id: Dict[str, str] = {}
    id_to_name: Dict[str, str] = {}
    pair_levels: Dict[frozenset, Set[str]] = defaultdict(set)

    # Use zip over columns as required
    for csv_path in existing_csvs:
        try:
            df = pd.read_csv(csv_path)
            for id_a, drug_a, id_b, drug_b, level in zip(
                df["DDInterID_A"], df["Drug_A"], df["DDInterID_B"], df["Drug_B"], df["Level"]
            ):
                if pd.notna(id_a) and pd.notna(drug_a):
                    id_a_str = str(id_a).strip()
                    name_a_str = str(drug_a).strip()
                    name_to_id[name_a_str.lower()] = id_a_str
                    if id_a_str not in id_to_name:
                        id_to_name[id_a_str] = name_a_str

                if pd.notna(id_b) and pd.notna(drug_b):
                    id_b_str = str(id_b).strip()
                    name_b_str = str(drug_b).strip()
                    name_to_id[name_b_str.lower()] = id_b_str
                    if id_b_str not in id_to_name:
                        id_to_name[id_b_str] = name_b_str

                if pd.notna(id_a) and pd.notna(id_b):
                    id_a_str = str(id_a).strip()
                    id_b_str = str(id_b).strip()
                    if id_a_str != id_b_str:
                        lvl_str = str(level).strip() if pd.notna(level) else "Unknown"
                        pair_levels[frozenset({id_a_str, id_b_str})].add(lvl_str)
        except Exception as e:
            warnings.warn(f"Failed reading DDInter CSV '{csv_path}': {e}")

    # Map ID -> SMILES and canonical SMILES -> ID
    id_to_smiles: Dict[str, Optional[str]] = {}
    canon_to_id: Dict[str, str] = {}
    for d_id, d_name in id_to_name.items():
        canon = name_to_canon.get(d_name)
        id_to_smiles[d_id] = canon
        if canon and canon not in canon_to_id:
            canon_to_id[canon] = d_id

    # Build partner_levels: ID -> {partner ID: most severe level or "Unrated"}
    partner_levels: Dict[str, Dict[str, str]] = {d_id: {} for d_id in id_to_name}
    for pair_key, levels in pair_levels.items():
        if len(pair_key) != 2:
            continue
        id_1, id_2 = list(pair_key)
        known = set(levels) - {"Unknown"}
        known_sorted = [lvl for lvl in SEVERITY_ORDER if lvl in known]
        sev = known_sorted[-1] if known_sorted else "Unrated"

        if id_1 in partner_levels:
            partner_levels[id_1][id_2] = sev
        else:
            partner_levels[id_1] = {id_2: sev}

        if id_2 in partner_levels:
            partner_levels[id_2][id_1] = sev
        else:
            partner_levels[id_2] = {id_1: sev}

    # Generate Morgan fingerprints (radius 2, 2048 bits)
    mfpgen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    fingerprints: Dict[str, Any] = {}
    for d_id, s_smiles in id_to_smiles.items():
        if s_smiles:
            mol = Chem.MolFromSmiles(s_smiles)
            if mol is not None:
                fingerprints[d_id] = mfpgen.GetFingerprint(mol)

    return DDInterData(
        name_to_id=name_to_id,
        id_to_name=id_to_name,
        id_to_smiles=id_to_smiles,
        canon_to_id=canon_to_id,
        pair_levels=dict(pair_levels),
        partner_levels=partner_levels,
        fingerprints=fingerprints,
    )


def build_ddinter_index(
    raw_dir: str = "data/raw",
    cache_path: str = "data/raw/ddinter_smiles_cache.json",
) -> Optional[DDInterData]:
    """Backward-compatible loader alias returning the loaded DDInterData object."""
    return load_ddinter(raw_dir=raw_dir, cache_path=cache_path)


def resolve_input(
    data: Optional[DDInterData],
    name: str,
    resolver: Callable[[str], str],
) -> Dict[str, Any]:
    """
    Resolve an input drug name using DDInter and the provided resolver.

    Resolution order:
      1. Case-insensitive exact match on DDInter name -> 'ddinter_name', SMILES from id_to_smiles.
      2. Call resolver, canonicalize SMILES, look up canon_to_id -> 'pubchem_match'.
      3. Resolver returned SMILES but no DDInter match -> 'pubchem_only'.
      4. Resolver failed -> 'unresolved'.
    Never raises for a bad input.
    """
    raw_input = str(name).strip()
    lower_input = raw_input.lower()

    if data is not None and lower_input in data.name_to_id:
        d_id = data.name_to_id[lower_input]
        d_name = data.id_to_name.get(d_id, raw_input)
        d_smiles = data.id_to_smiles.get(d_id)
        return {
            "input": raw_input,
            "name": d_name,
            "ddinter_id": d_id,
            "smiles": d_smiles,
            "resolved_via": "ddinter_name",
        }

    raw_smiles = None
    try:
        raw_smiles = resolver(raw_input)
    except Exception:
        raw_smiles = None

    if raw_smiles:
        canon = canonical_smiles(raw_smiles)
        if canon:
            d_id = data.canon_to_id.get(canon) if data is not None else None
            if d_id and data is not None:
                d_name = data.id_to_name.get(d_id, raw_input)
                return {
                    "input": raw_input,
                    "name": d_name,
                    "ddinter_id": d_id,
                    "smiles": canon,
                    "resolved_via": "pubchem_match",
                }
            else:
                return {
                    "input": raw_input,
                    "name": raw_input,
                    "ddinter_id": None,
                    "smiles": canon,
                    "resolved_via": "pubchem_only",
                }

    return {
        "input": raw_input,
        "name": raw_input,
        "ddinter_id": None,
        "smiles": None,
        "resolved_via": "unresolved",
    }


def lookup_pair(
    data: Optional[Any],
    id_a: Optional[str],
    id_b: Optional[str],
) -> Dict[str, Any]:
    """
    Look up interaction severity for two drugs.
    Accepts DDInter IDs (or canonical SMILES for backwards compatibility).
    """
    if data is None:
        return {"status": "unavailable", "level": None, "all_levels": []}

    if not id_a or not id_b:
        return {"status": "not_in_ddinter", "level": None, "all_levels": []}

    # Backward compatibility with SMILES passed directly
    if hasattr(data, "id_to_name"):
        if id_a not in data.id_to_name and hasattr(data, "canon_to_id"):
            canon_a = canonical_smiles(id_a)
            id_a = data.canon_to_id.get(canon_a)
        if id_b not in data.id_to_name and hasattr(data, "canon_to_id"):
            canon_b = canonical_smiles(id_b)
            id_b = data.canon_to_id.get(canon_b)

        if not id_a or not id_b:
            return {"status": "not_in_ddinter", "level": None, "all_levels": []}

        pair_levels = data.pair_levels
    elif isinstance(data, dict):
        pair_levels = data
    else:
        return {"status": "unavailable", "level": None, "all_levels": []}

    key = frozenset({id_a, id_b})
    if key not in pair_levels:
        return {"status": "not_recorded", "level": None, "all_levels": []}

    levels = pair_levels[key]
    known_levels = set(levels) - {"Unknown"}
    all_levels = [lvl for lvl in SEVERITY_ORDER if lvl in known_levels]
    if all_levels:
        return {
            "status": "match",
            "level": all_levels[-1],
            "all_levels": all_levels,
        }
    else:
        return {
            "status": "unknown_severity",
            "level": None,
            "all_levels": [],
        }


def distribution(data: Optional[DDInterData], drug_id: Optional[str]) -> Optional[Dict[str, int]]:
    """
    Return severity counts and total interacting partners for a DDInter ID.
    Returns None if data is None or drug_id is null/not found.
    """
    if data is None or not drug_id:
        return None

    if drug_id not in data.partner_levels:
        if drug_id in data.id_to_name:
            return {"Major": 0, "Moderate": 0, "Minor": 0, "Unrated": 0, "total": 0}
        return None

    partners = data.partner_levels[drug_id]
    counts = {"Major": 0, "Moderate": 0, "Minor": 0, "Unrated": 0}
    for sev in partners.values():
        if sev in counts:
            counts[sev] += 1
        else:
            counts["Unrated"] += 1

    counts["total"] = len(partners)
    return counts


def similar_drugs(
    data: Optional[DDInterData],
    drug_id: Optional[str],
    exclude_ids: Optional[Set[str]] = None,
    k: int = 3,
    min_similarity: float = 0.35,
) -> List[Dict[str, Any]]:
    """
    Find top-k structurally similar drugs via Morgan fingerprint Tanimoto similarity.
    Excludes drug_id and exclude_ids. Returns only those >= min_similarity.
    """
    if data is None or not drug_id or drug_id not in data.fingerprints:
        return []

    target_fp = data.fingerprints[drug_id]
    exclude_set = set(exclude_ids) if exclude_ids else set()
    exclude_set.add(drug_id)

    candidates = [cid for cid in data.fingerprints.keys() if cid not in exclude_set]
    if not candidates:
        return []

    cand_fps = [data.fingerprints[cid] for cid in candidates]
    sims = DataStructs.BulkTanimotoSimilarity(target_fp, cand_fps)

    scored = []
    for cid, sim in zip(candidates, sims):
        if sim >= min_similarity:
            scored.append({
                "id": cid,
                "name": data.id_to_name.get(cid, cid),
                "similarity": round(float(sim), 4),
            })

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:k]


def build_analogues(
    data: Optional[DDInterData],
    id_a: Optional[str],
    id_b: Optional[str],
) -> Dict[str, Any]:
    """
    Construct structural analogue interactions for a pair of drugs not recorded in DDInter.
    For drugs similar to A, checks recorded interactions with B.
    For drugs similar to B, checks recorded interactions with A.
    """
    if data is None:
        return {
            "similar_to_a": [],
            "similar_to_b": [],
            "summary": "Analogue lookup unavailable.",
        }

    sim_a = similar_drugs(data, id_a, exclude_ids={id_b} if id_b else set()) if id_a else []
    sim_b = similar_drugs(data, id_b, exclude_ids={id_a} if id_a else set()) if id_b else []

    name_a = data.id_to_name.get(id_a, id_a or "Drug A") if id_a else "Drug A"
    name_b = data.id_to_name.get(id_b, id_b or "Drug B") if id_b else "Drug B"

    # Evaluate level_with_b for each drug similar to A
    analogue_a = []
    for item in sim_a:
        level_with_b = None
        if id_b and data:
            key = frozenset({item["id"], id_b})
            if key in data.pair_levels:
                levels = data.pair_levels[key]
                known = set(levels) - {"Unknown"}
                known_sorted = [lvl for lvl in SEVERITY_ORDER if lvl in known]
                level_with_b = known_sorted[-1] if known_sorted else "Unrated"

        analogue_a.append({
            "id": item["id"],
            "name": item["name"],
            "similarity": item["similarity"],
            "level_with_b": level_with_b,
            "level": level_with_b,
        })

    # Evaluate level_with_a for each drug similar to B
    analogue_b = []
    for item in sim_b:
        level_with_a = None
        if id_a and data:
            key = frozenset({item["id"], id_a})
            if key in data.pair_levels:
                levels = data.pair_levels[key]
                known = set(levels) - {"Unknown"}
                known_sorted = [lvl for lvl in SEVERITY_ORDER if lvl in known]
                level_with_a = known_sorted[-1] if known_sorted else "Unrated"

        analogue_b.append({
            "id": item["id"],
            "name": item["name"],
            "similarity": item["similarity"],
            "level_with_a": level_with_a,
            "level": level_with_a,
        })

    # Compose plain sentence summary
    active_a = [item for item in analogue_a if item["level_with_b"] is not None]
    active_b = [item for item in analogue_b if item["level_with_a"] is not None]

    if not analogue_a and not analogue_b:
        summary = "No drugs structurally similar to either compound passed the similarity threshold."
    elif active_a and (len(active_a) >= len(active_b)):
        levels = [item["level_with_b"] for item in active_a if item["level_with_b"] != "Unrated"]
        levels_unique = [lvl for lvl in reversed(SEVERITY_ORDER) if lvl in levels]
        if not levels_unique and any(item["level_with_b"] == "Unrated" for item in active_a):
            levels_unique = ["Unrated"]
        lvl_text = f" ({', '.join(levels_unique)})" if levels_unique else ""
        summary = (
            f"{len(active_a)} of {len(analogue_a)} drugs structurally similar to {name_a} "
            f"have a recorded interaction with {name_b}{lvl_text}. "
            "This is inferred from structural similarity and is not a confirmed interaction."
        )
    elif active_b:
        levels = [item["level_with_a"] for item in active_b if item["level_with_a"] != "Unrated"]
        levels_unique = [lvl for lvl in reversed(SEVERITY_ORDER) if lvl in levels]
        if not levels_unique and any(item["level_with_a"] == "Unrated" for item in active_b):
            levels_unique = ["Unrated"]
        lvl_text = f" ({', '.join(levels_unique)})" if levels_unique else ""
        summary = (
            f"{len(active_b)} of {len(analogue_b)} drugs structurally similar to {name_b} "
            f"have a recorded interaction with {name_a}{lvl_text}. "
            "This is inferred from structural similarity and is not a confirmed interaction."
        )
    else:
        # Analogues exist, but none have recorded interactions with partner
        target_name = name_a if analogue_a else name_b
        partner_name = name_b if analogue_a else name_a
        total_cand = len(analogue_a) if analogue_a else len(analogue_b)
        summary = (
            f"0 of {total_cand} drugs structurally similar to {target_name} have a recorded "
            f"interaction with {partner_name}. "
            "This is inferred from structural similarity and is not a confirmed interaction."
        )

    return {
        "similar_to_a": analogue_a,
        "similar_to_b": analogue_b,
        "summary": summary,
    }
