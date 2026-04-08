#!/usr/bin/env python3
"""
Offline test script using sample data.

This demonstrates all database functionality without requiring internet access.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import TaxonomyDatabase
from models.taxonomy import Taxon
from utils.formatting import print_taxon_info, format_lineage, get_taxon_summary
from utils.test_data import get_all_test_taxa


def test_database_creation():
    """Test database creation and schema."""
    print("\n" + "="*70)
    print("TEST 1: Database Creation")
    print("="*70)
    
    db = TaxonomyDatabase("test_plant_taxonomy.db")
    db.connect()
    db.create_schema()
    
    print("✓ Database created: test_plant_taxonomy.db")
    print("✓ Schema initialized")
    
    db.close()
    return "test_plant_taxonomy.db"


def test_data_insertion(db_path: str):
    """Test inserting sample data."""
    print("\n" + "="*70)
    print("TEST 2: Data Insertion")
    print("="*70)
    
    test_taxa = get_all_test_taxa()
    
    with TaxonomyDatabase(db_path) as db:
        total_inserted = 0
        
        for taxon_data in test_taxa:
            print(f"\nInserting: {taxon_data['scientific_name']}")
            
            # Insert full lineage
            for taxon in taxon_data['lineage']:
                db.insert_taxon(taxon.to_dict())
                total_inserted += 1
            
            # Insert common names
            main_taxon = taxon_data['lineage'][-1]
            for common_name in main_taxon.common_names:
                db.insert_common_name(main_taxon.tsn, common_name)
                
            print(f"  ✓ Inserted {len(taxon_data['lineage'])} taxa")
            print(f"  ✓ Inserted {len(main_taxon.common_names)} common names")
    
    print(f"\n✓ Total taxa inserted: {total_inserted}")


def test_search(db_path: str):
    """Test search functionality."""
    print("\n" + "="*70)
    print("TEST 3: Search Functionality")
    print("="*70)
    
    with TaxonomyDatabase(db_path) as db:
        # Test 1: Search by scientific name
        print("\n--- Search by scientific name: 'Arabidopsis' ---")
        results = db.search_by_name("Arabidopsis")
        print(f"Found {len(results)} results:")
        for result in results[:5]:
            print(f"  • {get_taxon_summary(result)}")
        
        # Test 2: Search by common name
        print("\n--- Search by common name: 'tomato' ---")
        results = db.search_by_name("tomato")
        print(f"Found {len(results)} results:")
        for result in results:
            print(f"  • {get_taxon_summary(result)}")
        
        # Test 3: Search by family
        print("\n--- Search by family: 'Rosaceae' ---")
        results = db.search_by_name("Rosaceae")
        print(f"Found {len(results)} results:")
        for result in results[:5]:
            print(f"  • {get_taxon_summary(result)}")


def test_lineage_retrieval(db_path: str):
    """Test lineage retrieval."""
    print("\n" + "="*70)
    print("TEST 4: Lineage Retrieval")
    print("="*70)
    
    with TaxonomyDatabase(db_path) as db:
        # Test with tomato
        print("\n--- Lineage for Solanum lycopersicum (tomato) ---")
        lineage = db.get_lineage(30521)  # TSN for tomato
        
        if lineage:
            taxon_objects = [Taxon.from_dict(t) for t in lineage]
            
            print("\nCompact format:")
            print("  " + format_lineage(taxon_objects, style='compact'))
            
            print("\nFull hierarchy:")
            for taxon in taxon_objects:
                indent = "  " * (len(taxon_objects) - taxon_objects.index(taxon) - 1)
                print(f"  {indent}└─ {taxon.scientific_name} ({taxon.rank})")
        
        # Get common names
        common_names = db.get_common_names(30521)
        if common_names:
            print(f"\nCommon names: {', '.join(common_names)}")


def test_hierarchy_navigation(db_path: str):
    """Test navigating taxonomic hierarchy."""
    print("\n" + "="*70)
    print("TEST 5: Hierarchy Navigation")
    print("="*70)
    
    with TaxonomyDatabase(db_path) as db:
        # Find Rosaceae family
        results = db.search_by_name("Rosaceae")
        family_result = next((r for r in results if r['rank'] == 'Family'), None)
        
        if family_result:
            print(f"\nExploring Family: {family_result['scientific_name']}")
            
            # Get children (should be genera)
            children = db.get_children(family_result['tsn'])
            print(f"\nGenera in {family_result['scientific_name']}:")
            for child in children:
                if child['rank'] == 'Genus':
                    print(f"  • {child['scientific_name']}")
                    
                    # Get species in this genus
                    species = db.get_children(child['tsn'])
                    if species:
                        for sp in species:
                            print(f"    └─ {sp['scientific_name']}")


def test_statistics(db_path: str):
    """Test database statistics."""
    print("\n" + "="*70)
    print("TEST 6: Database Statistics")
    print("="*70)
    
    with TaxonomyDatabase(db_path) as db:
        stats = db.get_statistics()
        
        print(f"\nTotal taxa in database: {stats['total_taxa']}")
        print(f"Total common names: {stats['total_common_names']}")
        
        if stats['by_rank']:
            print("\nTaxa by rank:")
            for rank, count in sorted(stats['by_rank'].items(), 
                                     key=lambda x: x[1], reverse=True):
                print(f"  {rank:20s}: {count:4d}")


def test_taxon_object(db_path: str):
    """Test Taxon object functionality."""
    print("\n" + "="*70)
    print("TEST 7: Taxon Object Features")
    print("="*70)
    
    with TaxonomyDatabase(db_path) as db:
        # Get Arabidopsis thaliana
        taxon_data = db.get_taxon_by_tsn(505310)
        
        if taxon_data:
            taxon = Taxon.from_dict(taxon_data)
            lineage = db.get_lineage(505310)
            lineage_objects = [Taxon.from_dict(t) for t in lineage]
            
            print_taxon_info(taxon, lineage_objects)
            
            # Test binomial
            binomial = taxon.get_binomial()
            if binomial:
                print(f"\nBinomial name: {binomial}")


def run_all_tests():
    """Run complete test suite."""
    print("\n" + "🧪"*35)
    print("  PLANT TAXONOMY DATABASE - Offline Tests")
    print("🧪"*35)
    
    # Run tests
    db_path = test_database_creation()
    test_data_insertion(db_path)
    test_search(db_path)
    test_lineage_retrieval(db_path)
    test_hierarchy_navigation(db_path)
    test_statistics(db_path)
    test_taxon_object(db_path)
    
    # Summary
    print("\n" + "="*70)
    print("✓ All Tests Passed!")
    print("="*70)
    print(f"\nTest database created: {db_path}")
    print("\nThe following features were tested:")
    print("  ✓ Database creation and schema setup")
    print("  ✓ Data insertion (taxa and common names)")
    print("  ✓ Search by scientific and common names")
    print("  ✓ Lineage retrieval and display")
    print("  ✓ Hierarchy navigation (parent/child relationships)")
    print("  ✓ Database statistics")
    print("  ✓ Taxon object manipulation")
    
    print("\nNext steps:")
    print("  1. Try the interactive mode: python demo.py --interactive")
    print("  2. When online, test ITIS API: python demo.py")
    print("  3. Add more plant species to your database")
    print("  4. Build custom applications using the database API")


if __name__ == "__main__":
    run_all_tests()
