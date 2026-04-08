#!/usr/bin/env python3
"""
Quick test for comparative visualization functionality.

Tests that lineages are properly converted to dicts.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import TaxonomyDatabase

def test_comparative_viz(db_path):
    """Test comparative visualization data handling."""
    print("\n" + "="*70)
    print("COMPARATIVE VISUALIZATION TEST")
    print("="*70)
    
    # Load database
    print(f"\nLoading database: {db_path}")
    db = TaxonomyDatabase(db_path)
    db.connect()
    
    # Find some species
    print("\nSearching for species...")
    results = db.search_by_name("", limit=100)
    species_list = [r for r in results if r['rank'] == 'Species']
    
    if len(species_list) < 2:
        print("✗ Need at least 2 species in database")
        return False
    
    print(f"Found {len(species_list)} species")
    
    # Test getting lineages
    print("\nTesting lineage retrieval...")
    for i, species in enumerate(species_list[:3], 1):
        print(f"\n[{i}] {species['scientific_name']}")
        
        # Get lineage
        if species.get('tsn'):
            lineage = db.get_lineage(species['tsn'])
        else:
            lineage = db.get_lineage_by_id(species['id'])
        
        if not lineage:
            print("  ✗ No lineage found")
            continue
        
        print(f"  Lineage has {len(lineage)} ranks")
        
        # Test data type conversion
        lineage_dicts = []
        for item in lineage:
            if isinstance(item, dict):
                lineage_dicts.append(item)
            else:
                # Convert to dict
                try:
                    lineage_dicts.append(dict(item))
                except Exception as e:
                    print(f"  ✗ Failed to convert to dict: {e}")
                    return False
        
        # Test accessing dict keys
        for taxon in lineage_dicts:
            try:
                name = taxon['scientific_name']
                rank = taxon['rank']
            except (KeyError, TypeError) as e:
                print(f"  ✗ Failed to access taxon fields: {e}")
                print(f"     Taxon type: {type(taxon)}")
                print(f"     Taxon: {taxon}")
                return False
        
        print(f"  ✓ Lineage data format OK")
        
        # Show lineage
        lineage_str = " → ".join([t['rank'] for t in lineage_dicts])
        print(f"  {lineage_str}")
    
    print("\n" + "="*70)
    print("✓ ALL TESTS PASSED")
    print("="*70)
    print("\nComparative visualization should work!")
    print("Try: python taxonomy_gui.py " + db_path)
    
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_comparative.py <database.db>")
        print("\nExample: python test_comparative.py plants_populated.db")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}")
        sys.exit(1)
    
    success = test_comparative_viz(db_path)
    sys.exit(0 if success else 1)
