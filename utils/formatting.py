"""
Utility functions for taxonomy operations.
"""

from typing import List
from models.taxonomy import Taxon, TaxonomicHierarchy


def format_lineage(lineage: List[Taxon], style: str = 'full') -> str:
    """
    Format taxonomic lineage for display.
    
    Args:
        lineage: List of taxa from kingdom to species
        style: 'full', 'compact', or 'binomial'
        
    Returns:
        Formatted lineage string
    """
    if not lineage:
        return "Unknown lineage"
    
    if style == 'binomial' and len(lineage) > 0:
        # Get the lowest rank taxon
        taxon = lineage[-1]
        binomial = taxon.get_binomial()
        if binomial:
            return binomial
        return taxon.scientific_name
        
    elif style == 'compact':
        # Show only major ranks
        major_ranks = ['Kingdom', 'Division', 'Phylum', 'Class', 'Order', 
                      'Family', 'Genus', 'Species']
        filtered = [t for t in lineage if t.rank in major_ranks]
        return ' > '.join(t.scientific_name for t in filtered)
        
    else:  # full
        parts = []
        for taxon in lineage:
            if taxon.authorship:
                parts.append(f"{taxon.scientific_name} ({taxon.rank}) - {taxon.authorship}")
            else:
                parts.append(f"{taxon.scientific_name} ({taxon.rank})")
        return '\n  '.join(parts)


def print_taxon_info(taxon: Taxon, lineage: List[Taxon] = None):
    """
    Pretty print taxon information.
    
    Args:
        taxon: Taxon to display
        lineage: Optional full lineage
    """
    print("\n" + "="*70)
    print(f"Scientific Name: {taxon.scientific_name}")
    if taxon.authorship:
        print(f"Authority: {taxon.authorship}")
    print(f"Rank: {taxon.rank}")
    print(f"TSN: {taxon.tsn}")
    print(f"Status: {taxon.taxonomic_status}")
    
    if taxon.common_names:
        print(f"\nCommon Names:")
        for name in taxon.common_names:
            print(f"  - {name}")
    
    if lineage:
        print(f"\nTaxonomic Lineage:")
        print("  " + format_lineage(lineage, style='full'))
    
    print("="*70)


def build_tree_string(root_tsn: int, db_manager, indent: int = 0, 
                     max_depth: int = 3) -> str:
    """
    Build a tree-style string representation of taxonomic hierarchy.
    
    Args:
        root_tsn: TSN of root taxon
        db_manager: Database manager instance
        indent: Current indentation level
        max_depth: Maximum depth to traverse
        
    Returns:
        Tree string representation
    """
    if indent >= max_depth:
        return ""
        
    taxon_data = db_manager.get_taxon_by_tsn(root_tsn)
    if not taxon_data:
        return ""
    
    # Build this node's string
    prefix = "  " * indent + ("└─ " if indent > 0 else "")
    result = f"{prefix}{taxon_data['scientific_name']} ({taxon_data['rank']})\n"
    
    # Add children
    children = db_manager.get_children(root_tsn)
    for child in children:
        result += build_tree_string(child['tsn'], db_manager, indent + 1, max_depth)
    
    return result


def get_taxon_summary(taxon_data: dict) -> str:
    """
    Get a one-line summary of a taxon.
    
    Args:
        taxon_data: Dictionary from database
        
    Returns:
        Summary string
    """
    name = taxon_data['scientific_name']
    rank = taxon_data['rank']
    tsn = taxon_data['tsn']
    
    # Add family/genus context if available
    context = []
    if taxon_data.get('family'):
        context.append(f"Family: {taxon_data['family']}")
    if taxon_data.get('genus') and rank != 'Genus':
        context.append(f"Genus: {taxon_data['genus']}")
        
    if context:
        return f"{name} ({rank}, TSN: {tsn}) - {', '.join(context)}"
    else:
        return f"{name} ({rank}, TSN: {tsn})"


def validate_taxon_data(taxon: Taxon) -> List[str]:
    """
    Validate taxon data and return list of issues.
    
    Args:
        taxon: Taxon object to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    if not taxon.scientific_name:
        errors.append("Missing scientific name")
        
    if not taxon.rank:
        errors.append("Missing rank")
        
    # Check rank-specific requirements
    if taxon.rank == 'Species' and not taxon.genus:
        errors.append("Species must have genus")
        
    if taxon.rank in ['Subspecies', 'Variety'] and not taxon.species:
        errors.append(f"{taxon.rank} must have species")
    
    return errors
