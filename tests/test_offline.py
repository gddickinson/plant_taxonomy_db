"""Offline tests of the database workflow on the sample data in utils/test_data.py (no network).

pytest version of the root script test_offline.py (which stays as a printed walk-through: python test_offline.py).
Each test gets a fresh temporary database filled the same way the script fills it.
Run: python -m pytest -q tests/test_offline.py
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db_manager import TaxonomyDatabase  # noqa: E402
from models.taxonomy import Taxon  # noqa: E402
from utils.formatting import format_lineage, get_taxon_summary  # noqa: E402
from utils.test_data import get_all_test_taxa  # noqa: E402

TOMATO, ARABIDOPSIS, ROSACEAE = 30521, 505310, 24578


@pytest.fixture
def db_path(tmp_path):
    """Temporary database with the sample lineages and their common names."""
    path = tmp_path / "offline.db"
    with TaxonomyDatabase(str(path)) as db:
        db.create_schema()
        for item in get_all_test_taxa():
            for taxon in item["lineage"]:
                db.insert_taxon(taxon.to_dict())
            main = item["lineage"][-1]
            for name in main.common_names:
                db.insert_common_name(main.tsn, name)
    return str(path)


def test_database_creation(tmp_path):
    path = tmp_path / "new.db"
    with TaxonomyDatabase(str(path)) as db:
        db.create_schema()
        db.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in db.cursor.fetchall()}
    assert {"taxa", "common_names", "synonyms"} <= tables


def test_data_insertion(db_path):
    with TaxonomyDatabase(db_path) as db:
        names = {t["scientific_name"] for t in db.search_by_name("", limit=1000)}
    expected = {t.scientific_name for item in get_all_test_taxa() for t in item["lineage"]}
    assert names == expected


def test_search(db_path):
    with TaxonomyDatabase(db_path) as db:
        assert {r["scientific_name"] for r in db.search_by_name("Arabidopsis")} == {"Arabidopsis", "Arabidopsis thaliana"}
        assert [r["tsn"] for r in db.search_by_name("tomato")] == [TOMATO]
        assert any(r["tsn"] == ROSACEAE for r in db.search_by_name("Rosaceae"))
        assert "Arabidopsis thaliana" in get_taxon_summary(db.get_taxon_by_tsn(ARABIDOPSIS))


def test_lineage_retrieval(db_path):
    with TaxonomyDatabase(db_path) as db:
        lineage = db.get_lineage(TOMATO)
        assert [t["rank"] for t in lineage][0] == "Kingdom" and lineage[-1]["tsn"] == TOMATO
        assert [t["scientific_name"] for t in lineage][-3:] == ["Solanaceae", "Solanum", "Solanum lycopersicum"]
        assert db.get_common_names(TOMATO) == ["tomato"]
        text = format_lineage([Taxon.from_dict(t) for t in lineage], style="compact")
        assert "Plantae" in text and "Solanum lycopersicum" in text


def test_hierarchy_navigation(db_path):
    with TaxonomyDatabase(db_path) as db:
        genera = db.get_children(ROSACEAE)
        assert [g["scientific_name"] for g in genera] == ["Rosa"]
        assert [s["scientific_name"] for s in db.get_children(genera[0]["tsn"])] == ["Rosa rugosa"]


def test_statistics(db_path):
    with TaxonomyDatabase(db_path) as db:
        stats = db.get_statistics()
    taxa = {t.tsn for item in get_all_test_taxa() for t in item["lineage"]}
    assert stats["total_taxa"] == len(taxa)
    assert stats["by_rank"]["Species"] == len(get_all_test_taxa())
    assert stats["total_common_names"] == sum(len(i["lineage"][-1].common_names) for i in get_all_test_taxa())


def test_taxon_object(db_path):
    with TaxonomyDatabase(db_path) as db:
        taxon = Taxon.from_dict(db.get_taxon_by_tsn(ARABIDOPSIS))
    assert taxon.scientific_name == "Arabidopsis thaliana" and taxon.rank == "Species"
    assert taxon.to_dict()["tsn"] == ARABIDOPSIS
