"""
Unit tests for src/ddinter_lookup.py using pure in-memory data.
No network calls or heavy disk operations.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator

from src.ddinter_lookup import (
    DDInterData,
    build_analogues,
    canonical_smiles,
    distribution,
    load_ddinter,
    lookup_pair,
    resolve_input,
    similar_drugs,
)


@pytest.fixture
def mock_ddinter_data():
    """Create a self-contained in-memory DDInterData instance."""
    mfpgen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)

    # Chemical structures
    # A: Ethanol (CCO)
    # B: Benzene (c1ccccc1)
    # C: 1-Propanol (CCCO) - similar to Ethanol (~0.55 similarity)
    # D: Toluene (Cc1ccccc1) - similar to Benzene (~0.57 similarity)
    # E: Aspirin (CC(=O)Oc1ccccc1C(=O)O)
    smiles_map = {
        "D001": canonical_smiles("CCO"),
        "D002": canonical_smiles("c1ccccc1"),
        "D003": canonical_smiles("CCCO"),
        "D004": canonical_smiles("Cc1ccccc1"),
        "D005": canonical_smiles("CC(=O)Oc1ccccc1C(=O)O"),
    }

    name_to_id = {
        "ethanol": "D001",
        "benzene": "D002",
        "propanol": "D003",
        "toluene": "D004",
        "aspirin": "D005",
    }
    id_to_name = {
        "D001": "Ethanol",
        "D002": "Benzene",
        "D003": "Propanol",
        "D004": "Toluene",
        "D005": "Aspirin",
    }
    id_to_smiles = smiles_map
    canon_to_id = {s: d_id for d_id, s in smiles_map.items()}

    # Pair interactions:
    # (D001, D002) -> Match: Major, Minor
    # (D003, D002) -> Match: Major, Moderate (Propanol interacts with Benzene)
    # (D001, D004) -> Unknown only
    # Note: (D001, D005) not recorded
    pair_levels = {
        frozenset({"D001", "D002"}): {"Minor", "Major", "Unknown"},
        frozenset({"D003", "D002"}): {"Moderate", "Major"},
        frozenset({"D001", "D004"}): {"Unknown"},
    }

    # Partner levels:
    partner_levels = {
        "D001": {
            "D002": "Major",
            "D004": "Unrated",
        },
        "D002": {
            "D001": "Major",
            "D003": "Major",
        },
        "D003": {
            "D002": "Major",
        },
        "D004": {
            "D001": "Unrated",
        },
        "D005": {},
    }

    fingerprints = {}
    for d_id, sm in smiles_map.items():
        mol = Chem.MolFromSmiles(sm)
        fingerprints[d_id] = mfpgen.GetFingerprint(mol)

    return DDInterData(
        name_to_id=name_to_id,
        id_to_name=id_to_name,
        id_to_smiles=id_to_smiles,
        canon_to_id=canon_to_id,
        pair_levels=pair_levels,
        partner_levels=partner_levels,
        fingerprints=fingerprints,
    )


# ==============================================================================
# 1. canonical_smiles tests
# ==============================================================================


def test_canonical_smiles_empty():
    assert canonical_smiles("") is None
    assert canonical_smiles("   ") is None
    assert canonical_smiles(None) is None


def test_canonical_smiles_invalid():
    assert canonical_smiles("NotAValidSMILES!!!") is None


def test_canonical_smiles_identical_representations():
    aromatic = canonical_smiles("c1ccccc1")
    kekule = canonical_smiles("C1=CC=CC=C1")
    assert aromatic is not None
    assert aromatic == kekule


# ==============================================================================
# 2. lookup_pair tests
# ==============================================================================


def test_lookup_pair_none_data():
    res = lookup_pair(None, "D001", "D002")
    assert res == {
        "status": "unavailable",
        "level": None,
        "all_levels": [],
    }


def test_lookup_pair_not_in_ddinter(mock_ddinter_data):
    # One ID is None
    res1 = lookup_pair(mock_ddinter_data, None, "D002")
    assert res1 == {"status": "not_in_ddinter", "level": None, "all_levels": []}

    # ID not in DDInter
    res2 = lookup_pair(mock_ddinter_data, "NONEXISTENT", "D002")
    assert res2 == {"status": "not_in_ddinter", "level": None, "all_levels": []}


def test_lookup_pair_not_recorded(mock_ddinter_data):
    # D001 (Ethanol) and D005 (Aspirin) have no recorded interaction
    res = lookup_pair(mock_ddinter_data, "D001", "D005")
    assert res == {
        "status": "not_recorded",
        "level": None,
        "all_levels": [],
    }


def test_lookup_pair_order_independence(mock_ddinter_data):
    res_ab = lookup_pair(mock_ddinter_data, "D001", "D002")
    res_ba = lookup_pair(mock_ddinter_data, "D002", "D001")

    assert res_ab == {
        "status": "match",
        "level": "Major",
        "all_levels": ["Minor", "Major"],
    }
    assert res_ab == res_ba


def test_lookup_pair_only_unknown_gives_unknown_severity(mock_ddinter_data):
    # D001 and D004 have only "Unknown" in pair_levels
    res = lookup_pair(mock_ddinter_data, "D001", "D004")
    assert res == {
        "status": "unknown_severity",
        "level": None,
        "all_levels": [],
    }


def test_lookup_pair_several_levels_reported_most_severe_chosen(mock_ddinter_data):
    # D001 and D002 have {"Minor", "Major", "Unknown"}
    res = lookup_pair(mock_ddinter_data, "D001", "D002")
    assert res["status"] == "match"
    assert res["level"] == "Major"
    assert res["all_levels"] == ["Minor", "Major"]

    # D003 and D002 have {"Moderate", "Major"}
    res2 = lookup_pair(mock_ddinter_data, "D003", "D002")
    assert res2["status"] == "match"
    assert res2["level"] == "Major"
    assert res2["all_levels"] == ["Moderate", "Major"]


# ==============================================================================
# 3. resolve_input tests (all four resolved_via outcomes)
# ==============================================================================


def test_resolve_input_ddinter_name(mock_ddinter_data):
    # Outcome 1: ddinter_name (exact case-insensitive match)
    called = []

    def dummy_resolver(name):
        called.append(name)
        return "CCO"

    res = resolve_input(mock_ddinter_data, "EtHaNoL", dummy_resolver)
    assert res == {
        "input": "EtHaNoL",
        "name": "Ethanol",
        "ddinter_id": "D001",
        "smiles": canonical_smiles("CCO"),
        "resolved_via": "ddinter_name",
    }
    assert len(called) == 0  # Resolver not called because matched by name


def test_resolve_input_pubchem_match(mock_ddinter_data):
    # Outcome 2: pubchem_match (name not in DDInter, but resolver SMILES matches DDInter canon_to_id)
    def dummy_resolver(name):
        return "CCO"  # Resolves to Ethanol structure

    res = resolve_input(mock_ddinter_data, "Grain Alcohol", dummy_resolver)
    assert res == {
        "input": "Grain Alcohol",
        "name": "Ethanol",
        "ddinter_id": "D001",
        "smiles": canonical_smiles("CCO"),
        "resolved_via": "pubchem_match",
    }


def test_resolve_input_pubchem_only(mock_ddinter_data):
    # Outcome 3: pubchem_only (resolver provides valid SMILES, but molecule is not in DDInter)
    def dummy_resolver(name):
        return "CC(=O)NO"  # Acetohydroxamic acid (not in our mock data)

    res = resolve_input(mock_ddinter_data, "Unknown Drug", dummy_resolver)
    assert res == {
        "input": "Unknown Drug",
        "name": "Unknown Drug",
        "ddinter_id": None,
        "smiles": canonical_smiles("CC(=O)NO"),
        "resolved_via": "pubchem_only",
    }


def test_resolve_input_unresolved(mock_ddinter_data):
    # Outcome 4: unresolved (resolver fails or returns None/unparseable)
    def dummy_resolver_fail(name):
        raise ValueError("PubChem CID not found")

    res = resolve_input(mock_ddinter_data, "CompletelyMadeUpChemical", dummy_resolver_fail)
    assert res == {
        "input": "CompletelyMadeUpChemical",
        "name": "CompletelyMadeUpChemical",
        "ddinter_id": None,
        "smiles": None,
        "resolved_via": "unresolved",
    }


# ==============================================================================
# 4. distribution tests
# ==============================================================================


def test_distribution_counts(mock_ddinter_data):
    # For D001: partners are D002 (Major) and D004 (Unrated)
    dist1 = distribution(mock_ddinter_data, "D001")
    assert dist1 == {
        "Major": 1,
        "Moderate": 0,
        "Minor": 0,
        "Unrated": 1,
        "total": 2,
    }

    # For D005: 0 partners
    dist5 = distribution(mock_ddinter_data, "D005")
    assert dist5 == {
        "Major": 0,
        "Moderate": 0,
        "Minor": 0,
        "Unrated": 0,
        "total": 0,
    }

    # Null drug ID or null data
    assert distribution(mock_ddinter_data, None) is None
    assert distribution(None, "D001") is None


# ==============================================================================
# 5. similar_drugs tests (exclusion & threshold)
# ==============================================================================


def test_similar_drugs_excludes_drug_and_partner_and_respects_threshold(mock_ddinter_data):
    # D001 is Ethanol. D003 is Propanol (sim ~0.55).
    # Benzene (D002) has sim 0.0 with Ethanol (< 0.35 threshold).
    sims = similar_drugs(mock_ddinter_data, "D001", exclude_ids={"D004"}, min_similarity=0.35)

    ids = [item["id"] for item in sims]
    # D001 itself must be excluded
    assert "D001" not in ids
    # D004 was in exclude_ids, must be excluded
    assert "D004" not in ids
    # Benzene D002 has similarity < 0.35, must be excluded
    assert "D002" not in ids
    # D003 (Propanol) has similarity > 0.35, must be present
    assert "D003" in ids
    assert sims[0]["similarity"] >= 0.35


# ==============================================================================
# 6. build_analogues tests (summary wording)
# ==============================================================================


def test_build_analogues_summary_wording(mock_ddinter_data):
    # Pair: D001 (Ethanol) and D002 (Benzene)
    # Propanol (D003) is similar to Ethanol (D001) and has recorded interaction with Benzene (D002) of level Major.
    analogues = build_analogues(mock_ddinter_data, "D001", "D002")

    assert len(analogues["similar_to_a"]) > 0
    item = analogues["similar_to_a"][0]
    assert item["id"] == "D003"
    assert item["level_with_b"] == "Major"

    # Verify expected summary sentence structure
    assert "drugs structurally similar to Ethanol have a recorded interaction with Benzene (Major)." in analogues["summary"]
    assert "This is inferred from structural similarity and is not a confirmed interaction." in analogues["summary"]


def test_build_analogues_no_similar_drugs_passed_threshold(mock_ddinter_data):
    # D001 and D002 with very high threshold where nothing passes
    analogues = build_analogues(mock_ddinter_data, "D001", "D002")
    # For a drug with no analogues (e.g. Aspirin D005 in our small mock data has no close analogue)
    analogues_d5 = build_analogues(mock_ddinter_data, "D005", "D002")
    assert analogues_d5["summary"] == "No drugs structurally similar to either compound passed the similarity threshold."


# ==============================================================================
# 7. load_ddinter returns None when files are missing
# ==============================================================================


def test_load_ddinter_missing_files():
    res = load_ddinter(raw_dir="nonexistent/directory/path", cache_path="nonexistent/cache.json")
    assert res is None
