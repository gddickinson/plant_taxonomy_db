"""Comparative-visualisation data handling: lineages of several species come back as dicts with name and rank.

pytest version of the root script test_comparative.py (which checks a database you pass it:
python test_comparative.py plants_populated.db). Here it runs on the committed databases, no network:
the ITIS subset (TSN lineages) and myplants.db (GBIF rows without TSNs, lineage by row id).
Run: python -m pytest -q tests/test_comparative.py
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from database.db_manager import TaxonomyDatabase  # noqa: E402


@pytest.mark.parametrize("name", ["data/pinales_itis.db", "test_plant_taxonomy.db", "myplants.db"])
def test_comparative_viz(name):
    with TaxonomyDatabase(str(ROOT / name)) as db:
        species = [r for r in db.search_by_name("", limit=100) if r["rank"] == "Species"]
        assert len(species) >= 2, "comparison needs at least 2 species"
        for sp in species[:3]:
            lineage = db.get_lineage(sp["tsn"]) if sp.get("tsn") else db.get_lineage_by_id(sp["id"])
            assert lineage, sp["scientific_name"]
            assert all(isinstance(t, dict) and t["scientific_name"] and t["rank"] for t in lineage)
            assert lineage[-1]["scientific_name"] == sp["scientific_name"]
