#!/usr/bin/env python3
"""
Demo script for testing the plant taxonomy database foundation.

This script demonstrates:
1. Database creation and schema setup
2. Fetching data from ITIS API
3. Storing taxa in the database
4. Searching and retrieving taxonomy data
5. Displaying taxonomic hierarchies
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import TaxonomyDatabase
from api.itis_client import ITISClient
from models.taxonomy import Taxon
from utils.formatting import print_taxon_info, format_lineage, get_taxon_summary


def demo_database_setup():
    """Demonstrate database creation and schema setup."""
    print("\n" + "="*70)
    print("STEP 1: Database Setup")
    print("="*70)
    
    db = TaxonomyDatabase("demo_plant_taxonomy.db")
    db.connect()
    db.create_schema()
    
    print("✓ Database created: demo_plant_taxonomy.db")
    print("✓ Schema initialized with tables: taxa, common_names, synonyms")
    
    db.close()
    return "demo_plant_taxonomy.db"


def demo_itis_api(search_term: str = "Arabidopsis"):
    """Demonstrate ITIS API queries."""
    print("\n" + "="*70)
    print("STEP 2: ITIS API Queries")
    print("="*70)
    
    client = ITISClient()
    
    print(f"\nSearching ITIS for: '{search_term}'")
    results = client.search_by_scientific_name(search_term)
    
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results[:5], 1):  # Show first 5
        print(f"  {i}. {result['scientific_name']} (TSN: {result['tsn']})")
        if result.get('author'):
            print(f"     Author: {result['author']}")
    
    return results


def demo_fetch_and_store(tsn: int, db_path: str):
    """Demonstrate fetching full record from ITIS and storing it."""
    print("\n" + "="*70)
    print("STEP 3: Fetch Full Record and Store in Database")
    print("="*70)
    
    client = ITISClient()
    
    print(f"\nFetching complete record for TSN: {tsn}")
    taxon = client.get_record(tsn)
    
    if not taxon:
        print("❌ Failed to fetch record")
        return None
    
    print(f"✓ Retrieved: {taxon.scientific_name}")
    print(f"  Rank: {taxon.rank}")
    print(f"  Common names: {', '.join(taxon.common_names) if taxon.common_names else 'None'}")
    
    # Get full lineage
    print(f"\nFetching taxonomic hierarchy...")
    lineage = client.get_full_hierarchy_from_tsn(tsn)
    print(f"✓ Retrieved lineage with {len(lineage)} ranks")
    
    # Store in database
    print(f"\nStoring in database...")
    with TaxonomyDatabase(db_path) as db:
        # Store all taxa in lineage
        for taxon_item in lineage:
            db.insert_taxon(taxon_item.to_dict())
        
        # Store common names for the main taxon
        for common_name in taxon.common_names:
            db.insert_common_name(taxon.tsn, common_name)
    
    print(f"✓ Stored {len(lineage)} taxa in database")
    
    return taxon, lineage


def demo_search_and_retrieve(db_path: str, search_term: str = "Arabidopsis"):
    """Demonstrate searching the local database."""
    print("\n" + "="*70)
    print("STEP 4: Search Local Database")
    print("="*70)
    
    with TaxonomyDatabase(db_path) as db:
        print(f"\nSearching database for: '{search_term}'")
        results = db.search_by_name(search_term)
        
        print(f"Found {len(results)} results:")
        for result in results[:10]:  # Show first 10
            print(f"  • {get_taxon_summary(result)}")
    
    return results


def demo_lineage_display(db_path: str, tsn: int):
    """Demonstrate lineage retrieval and display."""
    print("\n" + "="*70)
    print("STEP 5: Display Taxonomic Lineage")
    print("="*70)
    
    with TaxonomyDatabase(db_path) as db:
        lineage = db.get_lineage(tsn)
        
        if lineage:
            taxon_data = lineage[-1]  # Get the target taxon
            print(f"\nLineage for: {taxon_data['scientific_name']}")
            print("\nCompact format:")
            taxon_objects = [Taxon.from_dict(t) for t in lineage]
            print("  " + format_lineage(taxon_objects, style='compact'))
            
            print("\nFull format:")
            print("  " + format_lineage(taxon_objects, style='full'))
            
            # Get common names
            common_names = db.get_common_names(tsn)
            if common_names:
                print(f"\nCommon names: {', '.join(common_names)}")
        else:
            print(f"❌ No lineage found for TSN: {tsn}")


def demo_statistics(db_path: str):
    """Show database statistics."""
    print("\n" + "="*70)
    print("STEP 6: Database Statistics")
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


def run_full_demo():
    """Run complete demonstration."""
    print("\n" + "🌱"*35)
    print("  PLANT TAXONOMY DATABASE - Foundation Demo")
    print("🌱"*35)
    
    # Step 1: Setup
    db_path = demo_database_setup()
    
    # Step 2: Search ITIS
    results = demo_itis_api("Arabidopsis thaliana")
    
    if results:
        # Step 3: Fetch and store first result
        tsn = int(results[0]['tsn'])
        taxon, lineage = demo_fetch_and_store(tsn, db_path)
        
        # Step 4: Search local database
        demo_search_and_retrieve(db_path, "Arabidopsis")
        
        # Step 5: Display lineage
        demo_lineage_display(db_path, tsn)
        
        # Step 6: Statistics
        demo_statistics(db_path)
        
        # Success message
        print("\n" + "="*70)
        print("✓ Demo Complete!")
        print("="*70)
        print(f"\nDatabase created: {db_path}")
        print("You can now explore the database using:")
        print("  - TaxonomyDatabase class for queries")
        print("  - ITISClient for fetching more data")
        print("\nNext steps:")
        print("  1. Add more plant species to the database")
        print("  2. Implement visualization of taxonomic trees")
        print("  3. Add support for other data sources (USDA, GBIF, etc.)")
        print("  4. Build a GUI for browsing and searching")
    else:
        print("\n❌ No results found. Please check internet connection.")


def interactive_mode(db_path: str = "demo_plant_taxonomy.db"):
    """Interactive mode for testing queries."""
    print("\n" + "="*70)
    print("Interactive Mode - Plant Taxonomy Database")
    print("="*70)
    print("\nCommands:")
    print("  search <name>  - Search ITIS for a plant")
    print("  add <tsn>      - Add taxon by TSN to database")
    print("  find <name>    - Search local database")
    print("  lineage <tsn>  - Show lineage for TSN")
    print("  stats          - Show database statistics")
    print("  quit           - Exit")
    
    client = ITISClient()
    
    while True:
        print("\n" + "-"*70)
        cmd = input("\n> ").strip().lower()
        
        if cmd == 'quit':
            print("Goodbye!")
            break
            
        elif cmd == 'stats':
            demo_statistics(db_path)
            
        elif cmd.startswith('search '):
            search_term = cmd[7:].strip()
            results = client.search_by_scientific_name(search_term)
            print(f"\nFound {len(results)} results:")
            for i, result in enumerate(results[:10], 1):
                print(f"  {i}. {result['scientific_name']} (TSN: {result['tsn']})")
                
        elif cmd.startswith('add '):
            try:
                tsn = int(cmd[4:].strip())
                demo_fetch_and_store(tsn, db_path)
            except ValueError:
                print("Invalid TSN. Please enter a number.")
                
        elif cmd.startswith('find '):
            search_term = cmd[5:].strip()
            demo_search_and_retrieve(db_path, search_term)
            
        elif cmd.startswith('lineage '):
            try:
                tsn = int(cmd[8:].strip())
                demo_lineage_display(db_path, tsn)
            except ValueError:
                print("Invalid TSN. Please enter a number.")
        else:
            print("Unknown command. Type 'quit' to exit.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Plant Taxonomy Database Demo")
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('--db', default='demo_plant_taxonomy.db',
                       help='Database file path')
    
    args = parser.parse_args()
    
    if args.interactive:
        # Setup database if it doesn't exist
        db_file = Path(args.db)
        if not db_file.exists():
            demo_database_setup()
        interactive_mode(args.db)
    else:
        # Run full automated demo
        run_full_demo()
