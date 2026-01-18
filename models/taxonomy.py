"""
Data models for taxonomy entities.

Provides clean Python objects for working with taxonomic data.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class Taxon:
    """Represents a taxonomic entity."""
    
    scientific_name: str
    rank: str  # Kingdom, Family, Genus, Species, etc.
    tsn: Optional[int] = None  # Taxonomic Serial Number (ITIS)
    kingdom: Optional[str] = None
    division: Optional[str] = None  # Phylum
    class_name: Optional[str] = None
    order: Optional[str] = None
    family: Optional[str] = None
    genus: Optional[str] = None
    species: Optional[str] = None
    subspecies: Optional[str] = None
    variety: Optional[str] = None
    authorship: Optional[str] = None
    parent_tsn: Optional[int] = None
    taxonomic_status: str = 'accepted'  # accepted, synonym, invalid, etc.
    source: str = 'ITIS'
    common_names: List[str] = field(default_factory=list)
    synonyms: List[str] = field(default_factory=list)
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    
    def __str__(self) -> str:
        """String representation."""
        if self.authorship:
            return f"{self.scientific_name} {self.authorship}"
        return self.scientific_name
    
    def get_binomial(self) -> Optional[str]:
        """Get genus + species binomial name if available."""
        if self.genus and self.species:
            return f"{self.genus} {self.species}"
        return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for database insertion."""
        return {
            'tsn': self.tsn,
            'kingdom': self.kingdom,
            'division': self.division,
            'class': self.class_name,
            'order_name': self.order,
            'family': self.family,
            'genus': self.genus,
            'species': self.species,
            'subspecies': self.subspecies,
            'variety': self.variety,
            'rank': self.rank,
            'scientific_name': self.scientific_name,
            'authorship': self.authorship,
            'parent_tsn': self.parent_tsn,
            'taxonomic_status': self.taxonomic_status,
            'source': self.source
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Taxon':
        """Create Taxon from database row dictionary."""
        return cls(
            tsn=data.get('tsn'),
            kingdom=data.get('kingdom'),
            division=data.get('division'),
            class_name=data.get('class'),
            order=data.get('order_name'),
            family=data.get('family'),
            genus=data.get('genus'),
            species=data.get('species'),
            subspecies=data.get('subspecies'),
            variety=data.get('variety'),
            rank=data.get('rank', ''),
            scientific_name=data.get('scientific_name', ''),
            authorship=data.get('authorship'),
            parent_tsn=data.get('parent_tsn'),
            taxonomic_status=data.get('taxonomic_status', 'accepted'),
            source=data.get('source', 'ITIS'),
            created_date=data.get('created_date'),
            updated_date=data.get('updated_date')
        )


@dataclass
class TaxonomicHierarchy:
    """Represents a complete taxonomic hierarchy from kingdom to species."""
    
    kingdom: Optional[Taxon] = None
    division: Optional[Taxon] = None
    class_taxon: Optional[Taxon] = None
    order: Optional[Taxon] = None
    family: Optional[Taxon] = None
    genus: Optional[Taxon] = None
    species: Optional[Taxon] = None
    subspecies: Optional[Taxon] = None
    
    def get_lineage_list(self) -> List[Taxon]:
        """Get ordered list of taxa from kingdom to lowest rank."""
        lineage = []
        for rank in ['kingdom', 'division', 'class_taxon', 'order', 
                     'family', 'genus', 'species', 'subspecies']:
            taxon = getattr(self, rank)
            if taxon:
                lineage.append(taxon)
        return lineage
    
    def get_lineage_string(self, separator: str = ' > ') -> str:
        """Get formatted lineage string."""
        return separator.join(t.scientific_name for t in self.get_lineage_list())
    
    @classmethod
    def from_lineage_list(cls, lineage: List[Taxon]) -> 'TaxonomicHierarchy':
        """Create hierarchy from ordered list of taxa."""
        hierarchy = cls()
        
        rank_map = {
            'Kingdom': 'kingdom',
            'Division': 'division',
            'Phylum': 'division',  # Alternative to division
            'Class': 'class_taxon',
            'Order': 'order',
            'Family': 'family',
            'Genus': 'genus',
            'Species': 'species',
            'Subspecies': 'subspecies'
        }
        
        for taxon in lineage:
            attr_name = rank_map.get(taxon.rank)
            if attr_name:
                setattr(hierarchy, attr_name, taxon)
                
        return hierarchy


# Rank ordering for taxonomic hierarchy
RANK_ORDER = [
    'Kingdom',
    'Subkingdom',
    'Division',
    'Phylum',  # Alternative to Division
    'Subdivision',
    'Subphylum',
    'Class',
    'Subclass',
    'Order',
    'Suborder',
    'Family',
    'Subfamily',
    'Tribe',
    'Subtribe',
    'Genus',
    'Subgenus',
    'Section',
    'Subsection',
    'Species',
    'Subspecies',
    'Variety',
    'Form'
]


def get_rank_level(rank: str) -> int:
    """
    Get numeric level of a taxonomic rank for comparison.
    
    Args:
        rank: Taxonomic rank name
        
    Returns:
        Numeric level (lower is higher in hierarchy)
    """
    try:
        return RANK_ORDER.index(rank)
    except ValueError:
        return 999  # Unknown rank goes to end
