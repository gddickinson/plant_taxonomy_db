"""
Smoke tests for TaxonomyDatabase CRUD operations.

Uses an in-memory or temporary database -- no network access needed.
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import TaxonomyDatabase
from models.taxonomy import Taxon


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    tmp.close()
    db_path = tmp.name
    database = TaxonomyDatabase(db_path)
    database.connect()
    database.create_schema()
    yield database
    database.close()
    os.unlink(db_path)


@pytest.fixture
def populated_db(db):
    """Database with sample data inserted."""
    # Insert a simple hierarchy: Kingdom > Family > Genus > Species
    db.insert_taxon({
        'tsn': 202422,
        'scientific_name': 'Plantae',
        'rank': 'Kingdom',
        'kingdom': 'Plantae',
        'source': 'ITIS',
    })
    db.insert_taxon({
        'tsn': 23061,
        'scientific_name': 'Brassicaceae',
        'rank': 'Family',
        'kingdom': 'Plantae',
        'family': 'Brassicaceae',
        'parent_tsn': 202422,
        'source': 'ITIS',
    })
    db.insert_taxon({
        'tsn': 23144,
        'scientific_name': 'Arabidopsis',
        'rank': 'Genus',
        'kingdom': 'Plantae',
        'family': 'Brassicaceae',
        'genus': 'Arabidopsis',
        'parent_tsn': 23061,
        'source': 'ITIS',
    })
    db.insert_taxon({
        'tsn': 505310,
        'scientific_name': 'Arabidopsis thaliana',
        'rank': 'Species',
        'kingdom': 'Plantae',
        'family': 'Brassicaceae',
        'genus': 'Arabidopsis',
        'species': 'thaliana',
        'parent_tsn': 23144,
        'source': 'ITIS',
    })
    db.insert_common_name(505310, 'thale cress')
    db.insert_common_name(505310, 'mouse-ear cress')
    return db


class TestDatabaseCreation:
    """Tests for database setup."""

    def test_schema_creates_tables(self, db):
        """Schema creation succeeds without error."""
        # If we got here, schema was already created in fixture
        stats = db.get_statistics()
        assert stats['total_taxa'] == 0

    def test_insert_and_retrieve(self, db):
        """Can insert and retrieve a taxon."""
        db.insert_taxon({
            'tsn': 1,
            'scientific_name': 'Testus plantus',
            'rank': 'Species',
            'source': 'test',
        })
        result = db.get_taxon_by_tsn(1)
        assert result is not None
        assert result['scientific_name'] == 'Testus plantus'


class TestSearch:
    """Tests for search functionality."""

    def test_search_by_scientific_name(self, populated_db):
        """Can find taxon by scientific name."""
        results = populated_db.search_by_name('Arabidopsis')
        names = [r['scientific_name'] for r in results]
        assert any('Arabidopsis' in n for n in names)

    def test_search_by_common_name(self, populated_db):
        """Can find taxon by common name."""
        results = populated_db.search_by_name('thale cress')
        assert len(results) >= 1

    def test_search_no_results(self, populated_db):
        """Returns empty list for no matches."""
        results = populated_db.search_by_name('xyznonexistent')
        assert results == []


class TestLineage:
    """Tests for lineage retrieval."""

    def test_get_lineage(self, populated_db):
        """Lineage returns kingdom-to-species chain."""
        lineage = populated_db.get_lineage(505310)
        ranks = [t['rank'] for t in lineage]
        assert 'Kingdom' in ranks
        assert 'Species' in ranks
        assert lineage[-1]['scientific_name'] == 'Arabidopsis thaliana'

    def test_get_children(self, populated_db):
        """Children returns direct descendants."""
        children = populated_db.get_children(23061)  # Brassicaceae
        names = [c['scientific_name'] for c in children]
        assert 'Arabidopsis' in names


class TestCommonNames:
    """Tests for common name operations."""

    def test_get_common_names(self, populated_db):
        """Retrieves common names for a TSN."""
        names = populated_db.get_common_names(505310)
        assert 'thale cress' in names
        assert 'mouse-ear cress' in names

    def test_no_common_names(self, populated_db):
        """Returns empty list for taxa without common names."""
        names = populated_db.get_common_names(23061)
        assert names == []


class TestStatistics:
    """Tests for database statistics."""

    def test_statistics(self, populated_db):
        """Statistics returns correct counts."""
        stats = populated_db.get_statistics()
        assert stats['total_taxa'] == 4
        assert stats['total_common_names'] == 2
        assert 'Species' in stats['by_rank']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])


def test_search_lists_each_taxon_once(db):
    """A taxon whose scientific AND common name match must not be returned twice."""
    db.insert_taxon({'tsn': 18035, 'scientific_name': 'Pinus', 'rank': 'Genus', 'source': 'ITIS'})
    db.insert_common_name(18035, 'pine')
    db.insert_common_name(18035, 'pinyon')
    results = db.search_by_name('pin')
    assert [r['tsn'] for r in results] == [18035]
