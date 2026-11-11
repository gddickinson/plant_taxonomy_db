"""
Download one ITIS subtree (e.g. a plant family) into a TaxonomyDatabase.

Walks the tree breadth-first with ITISClient.get_full_hierarchy_from_tsn
(which lists a taxon's direct children after it), stores every taxon with
its classification fields filled from its ancestors, plus its common names
(with language) and synonyms. Used by scripts/build_itis_subset.py.
"""

import time
from collections import deque
from dataclasses import replace
from typing import Callable, List, Optional, Tuple

from api.itis_client import ITISClient
from database.db_manager import TaxonomyDatabase
from models.taxonomy import Taxon
from utils.logger import get_logger

logger = get_logger('plant_taxonomy.api.itis_subset')

NS = {'ax21': 'http://data.itis_service.itis.usgs.gov/xsd'}

# Taxon attribute set from a taxon's own name, by rank
RANK_FIELD = {
    'Kingdom': 'kingdom', 'Division': 'division', 'Phylum': 'division',
    'Class': 'class_name', 'Order': 'order', 'Family': 'family',
    'Genus': 'genus', 'Species': 'species', 'Subspecies': 'subspecies',
    'Variety': 'variety',
}
CLASSIFICATION = ['kingdom', 'division', 'class_name', 'order', 'family',
                  'genus', 'species', 'subspecies', 'variety']
LANGUAGE_CODES = {'English': 'en', 'French': 'fr', 'Spanish': 'es',
                  'German': 'de', 'Portuguese': 'pt', 'Hawaiian': 'haw'}


def _text(item, tag: str) -> Optional[str]:
    elem = item.find(f'ax21:{tag}', NS)
    return elem.text if elem is not None and elem.text else None


def get_common_names_detailed(client: ITISClient, tsn: int) -> List[Tuple[str, str]]:
    """Common names of a TSN as (name, language code) pairs."""
    root = client._parse_response(client._make_request('getCommonNamesFromTSN', {'tsn': tsn}))
    out = []
    for item in root.findall('.//ax21:commonNames', NS):
        name = _text(item, 'commonName')
        if name:
            lang = _text(item, 'language') or 'English'
            out.append((name, LANGUAGE_CODES.get(lang, lang)))
    return out


def get_synonyms(client: ITISClient, tsn: int) -> List[Tuple[int, str, Optional[str]]]:
    """Synonyms of an accepted TSN as (synonym_tsn, name, author)."""
    root = client._parse_response(client._make_request('getSynonymNamesFromTSN', {'tsn': tsn}))
    out = []
    for item in root.findall('.//ax21:synonyms', NS):
        stsn, name = _text(item, 'tsn'), _text(item, 'sciName')
        if stsn and name:
            out.append((int(stsn), name, _text(item, 'author')))
    return out


def with_classification(taxon: Taxon, parent: Optional[Taxon]) -> Taxon:
    """Copy the parent's classification fields and set the taxon's own rank field."""
    fields = {f: getattr(parent, f) for f in CLASSIFICATION} if parent else {}
    own = RANK_FIELD.get(taxon.rank)
    if own == 'species':
        fields[own] = taxon.scientific_name.split()[-1]
    elif own:
        fields[own] = taxon.scientific_name
    return replace(taxon, **fields)


def build_subtree(root_tsn: int, db: TaxonomyDatabase, client: ITISClient,
                  delay: float = 0.2, max_taxa: int = 5000,
                  progress: Callable[[int, Taxon], None] = None) -> int:
    """
    Store the lineage above root_tsn and every taxon below it in db.

    Returns the number of taxa stored. delay is the pause between ITIS
    requests (be polite); max_taxa is a safety cap.
    """
    full = client.get_full_hierarchy_from_tsn(root_tsn)
    lineage, root = client.split_lineage(full, root_tsn)
    if root is None:
        raise ValueError(f"TSN {root_tsn} not found in ITIS")
    parent = None
    for t in lineage[:-1]:  # ancestors: kingdom ... order
        parent = with_classification(t, parent)
        db.insert_taxon(parent.to_dict())
    queue = deque([(root, parent, full)])
    stored = 0
    while queue and stored < max_taxa:
        taxon, parent, hierarchy = queue.popleft()
        if hierarchy is None:
            time.sleep(delay)
            hierarchy = client.get_full_hierarchy_from_tsn(taxon.tsn)
            _, found = client.split_lineage(hierarchy, taxon.tsn)
            taxon = found or taxon  # carries authorship
        taxon = with_classification(taxon, parent)
        db.insert_taxon(taxon.to_dict())
        for name, lang in get_common_names_detailed(client, taxon.tsn):
            db.insert_common_name(taxon.tsn, name, lang)
        for stsn, name, author in get_synonyms(client, taxon.tsn):
            db.insert_synonym(taxon.tsn, stsn, name, author)
        stored += 1
        if progress:
            progress(stored, taxon)
        for child in hierarchy:
            if child.parent_tsn == taxon.tsn and child.tsn != taxon.tsn:
                queue.append((child, taxon, None))
    return stored


def find_tsn(client: ITISClient, name: str) -> int:
    """TSN of an exact scientific-name match (first hit)."""
    for r in client.search_by_scientific_name(name):
        if r['scientific_name'] == name:
            return int(r['tsn'])
    raise ValueError(f"No exact ITIS match for {name!r}")
