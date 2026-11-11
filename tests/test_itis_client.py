"""Offline tests for ITISClient parsing, using ITIS responses recorded on 2026-11-11 (tests/fixtures/itis/).

No network: the client's HTTP session is replaced with one that serves the recorded XML.
Run: python -m pytest -q tests/test_itis_client.py
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

pytest.importorskip("requests")
from api.itis_client import ITISClient  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures" / "itis"


class _Resp:
    def __init__(self, content: bytes):
        self.content = content
        self.status_code = 200

    def raise_for_status(self):
        pass


class _Session:
    """Maps (endpoint, key param) to a recorded XML file."""

    def __init__(self, files):
        self.files = files

    def get(self, url, params=None, timeout=None):
        endpoint = url.rsplit("/", 1)[-1]
        key = str(next(iter(params.values())))
        return _Resp((FIX / self.files[(endpoint, key)]).read_bytes())


def _client(files):
    c = ITISClient(max_retries=1)
    c.session = _Session(files)
    return c


def test_search_by_scientific_name_parses_results():
    c = _client({("searchByScientificName", "Pinus ponderosa"): "search_pinus_ponderosa.xml"})
    results = c.search_by_scientific_name("Pinus ponderosa")
    names = [r["scientific_name"] for r in results]
    assert "Pinus ponderosa" in names
    assert all(r["tsn"].isdigit() for r in results)


def test_hierarchy_includes_ancestors_and_children():
    c = _client({("getFullHierarchyFromTSN", "18030"): "hierarchy_18030.xml"})
    h = c.get_full_hierarchy_from_tsn(18030)
    ranks = {t.scientific_name: t.rank for t in h}
    assert ranks["Plantae"] == "Kingdom" and ranks["Pinaceae"] == "Family" and ranks["Pinus"] == "Genus"


def test_get_record_returns_requested_taxon_not_last_child():
    files = {("getFullHierarchyFromTSN", "18030"): "hierarchy_18030.xml",
             ("getCommonNamesFromTSN", "18030"): "common_18030.xml"}
    rec = _client(files).get_record(18030)
    assert rec.tsn == 18030 and rec.scientific_name == "Pinaceae" and rec.rank == "Family"
    assert rec.order == "Pinales" and rec.class_name == "Pinopsida"
    assert rec.common_names == ["pines"]


def test_data_source_manager_returns_requested_taxon_and_lineage_only():
    from api.data_source_manager import DataSourceManager
    files = {("getFullHierarchyFromTSN", "18030"): "hierarchy_18030.xml",
             ("getCommonNamesFromTSN", "18030"): "common_18030.xml"}
    m = DataSourceManager()
    m.sources = [("ITIS", _client(files))]
    taxon, lineage, source = m.get_taxon_with_hierarchy(18030, "ITIS")
    assert source == "ITIS" and taxon.scientific_name == "Pinaceae" and taxon.common_names == ["pines"]
    assert lineage[0].scientific_name == "Plantae" and lineage[-1] is taxon
    assert "Pinus" not in [t.scientific_name for t in lineage]
