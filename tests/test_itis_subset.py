"""Offline tests for api/itis_subset.py (the ITIS subtree builder), replaying recorded ITIS responses.

Run: python -m pytest -q tests/test_itis_subset.py
"""
import pytest

pytest.importorskip("requests")
from tests.test_itis_client import _client  # noqa: E402  (fake session serving tests/fixtures/itis/)

from api.itis_subset import get_common_names_detailed, get_synonyms, with_classification  # noqa: E402
from models.taxonomy import Taxon  # noqa: E402


def test_synonyms_parsed():
    c = _client({("getSynonymNamesFromTSN", "183309"): "synonyms_183309.xml"})
    assert get_synonyms(c, 183309) == [(183310, "Pinus sitchensis", "Bong.")]


def test_common_names_with_language():
    c = _client({("getCommonNamesFromTSN", "18030"): "common_18030.xml"})
    assert get_common_names_detailed(c, 18030) == [("pines", "en")]


def test_classification_inherited_from_parent():
    genus = Taxon("Picea", "Genus", tsn=18033, family="Pinaceae", order="Pinales", kingdom="Plantae")
    genus = with_classification(genus, Taxon("Pinaceae", "Family", family="Pinaceae", order="Pinales", kingdom="Plantae"))
    sp = with_classification(Taxon("Picea sitchensis", "Species", tsn=183309, parent_tsn=18033), genus)
    assert (sp.kingdom, sp.order, sp.family, sp.genus, sp.species) == ("Plantae", "Pinales", "Pinaceae", "Picea", "sitchensis")
    var = with_classification(Taxon("Picea glauca var. albertiana", "Variety"), sp)
    assert var.variety == "Picea glauca var. albertiana" and var.genus == "Picea"
