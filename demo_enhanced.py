#!/usr/bin/env python3
"""
Enhanced demo script with logging and fallback data sources.

Demonstrates robust error handling, multiple data sources, and comprehensive logging.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import TaxonomyDatabase
from api.data_source_manager import DataSourceManager
from api.itis_client import ITISConnectionError
from api.gbif_client import GBIFConnectionError
from models.taxonomy import Taxon
from utils.formatting import print_taxon_info, format_lineage, get_taxon_summary
from utils.logger import setup_quick_logging, get_logger

# Setup logging
logger = get_logger('plant_taxonomy.demo')


def demo_connection_test():
    """Test connectivity to all data sources."""
    print("\n" + "🔌"*35)
    print("  CONNECTION TEST - Testing All Data Sources")
    print("🔌"*35)
    
    manager = DataSourceManager()
    results = manager.test_all_connections()
    
    return manager, results


def demo_search_with_fallback(manager: DataSourceManager, search_term: str = "Arabidopsis thaliana"):
    """Demonstrate search with automatic fallback."""
    print("\n" + "="*70)
    print("SEARCH WITH AUTOMATIC FALLBACK")
    print("="*70)
    
    logger.info(f"Searching for: {search_term}")
    print(f"\nSearching for: '{search_term}'")
    print("(Will automatically try fallback sources if primary fails)")
    
    try:
        results, source, msg = manager.search_with_best_source(search_term)
        
        if results:
            print(f"\n✓ {msg}")
            print(f"\nTop results:")
            for i, result in enumerate(results[:5], 1):
                name = result.get('scientific_name', 'Unknown')
                author = result.get('author', '')
                print(f"  {i}. {name} {author if author else ''}")
            return results, source
        else:
            print(f"\n✗ {msg}")
            print("\nPossible reasons:")
            print("  - No internet connection")
            print("  - All data sources are down")
            print("  - Species name not found in any database")
            return None, None
            
    except Exception as e:
        logger.error(f"Search failed: {e}")
        print(f"\n✗ Error during search: {e}")
        return None, None


def demo_fetch_and_store(manager: DataSourceManager, identifier: Any, 
                         source: str, db_path: str):
    """Fetch from appropriate source and store in database."""
    print("\n" + "="*70)
    print("FETCH AND STORE WITH ERROR HANDLING")
    print("="*70)
    
    print(f"\nFetching complete record...")
    print(f"  Source: {source}")
    print(f"  Identifier: {identifier}")
    
    try:
        taxon, lineage, source_used = manager.get_taxon_with_hierarchy(identifier, source)
        
        if not taxon or not lineage:
            print("\n✗ Failed to retrieve taxon data")
            logger.error(f"No data retrieved for {identifier} from {source}")
            return None, None
        
        print(f"\n✓ Retrieved: {taxon.scientific_name}")
        print(f"  Rank: {taxon.rank}")
        print(f"  Source: {source_used}")
        print(f"  Hierarchy length: {len(lineage)} ranks")
        
        if taxon.common_names:
            print(f"  Common names: {', '.join(taxon.common_names[:3])}")
        
        # Store in database
        print(f"\nStoring in database...")
        logger.info(f"Storing {len(lineage)} taxa in database")
        
        with TaxonomyDatabase(db_path) as db:
            # Store all taxa in lineage
            for taxon_item in lineage:
                db.insert_taxon(taxon_item.to_dict())
            
            # Store common names for the main taxon
            for common_name in taxon.common_names:
                db.insert_common_name(taxon.tsn if hasattr(taxon, 'tsn') and taxon.tsn else 0, 
                                     common_name)
        
        print(f"✓ Stored {len(lineage)} taxa in database")
        logger.info("Data stored successfully")
        
        return taxon, lineage
        
    except (ITISConnectionError, GBIFConnectionError) as e:
        print(f"\n✗ Connection error: {e}")
        logger.error(f"Connection error: {e}")
        return None, None
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return None, None


def demo_database_operations(db_path: str):
    """Demonstrate database operations with error handling."""
    print("\n" + "="*70)
    print("DATABASE OPERATIONS")
    print("="*70)
    
    try:
        with TaxonomyDatabase(db_path) as db:
            # Get statistics
            stats = db.get_statistics()
            
            print(f"\nDatabase Statistics:")
            print(f"  Total taxa: {stats['total_taxa']}")
            print(f"  Common names: {stats['total_common_names']}")
            
            if stats['by_rank']:
                print(f"\n  Taxa by rank:")
                for rank, count in sorted(stats['by_rank'].items(), 
                                        key=lambda x: x[1], reverse=True)[:5]:
                    print(f"    {rank:20s}: {count:4d}")
            
            # Search database
            print(f"\n  Searching local database...")
            results = db.search_by_name("Arabidopsis")
            print(f"  Found {len(results)} entries for 'Arabidopsis'")
            
            logger.info("Database operations completed successfully")
            
    except Exception as e:
        print(f"\n✗ Database error: {e}")
        logger.error(f"Database error: {e}", exc_info=True)


def run_enhanced_demo(verbose: bool = False):
    """Run complete enhanced demonstration."""
    
    # Setup logging
    setup_quick_logging(verbose=verbose)
    
    print("\n" + "🌿"*35)
    print("  ENHANCED PLANT TAXONOMY DATABASE DEMO")
    print("  With Logging & Fallback Data Sources")
    print("🌿"*35)
    
    logger.info("Starting enhanced demo")
    
    # Step 1: Create database
    print("\n" + "="*70)
    print("[1] DATABASE SETUP")
    print("="*70)
    db_path = "enhanced_demo.db"
    
    try:
        db = TaxonomyDatabase(db_path)
        db.connect()
        db.create_schema()
        db.close()
        print(f"✓ Database created: {db_path}")
        logger.info(f"Database initialized: {db_path}")
    except Exception as e:
        print(f"✗ Database creation failed: {e}")
        logger.error(f"Database creation failed: {e}")
        return
    
    # Step 2: Test connections
    print("\n" + "="*70)
    print("[2] TESTING DATA SOURCE CONNECTIONS")
    print("="*70)
    manager, conn_results = demo_connection_test()
    
    # Check if any source is available
    if not any(conn_results.values()):
        print("\n" + "⚠"*35)
        print("  WARNING: No data sources available!")
        print("  Cannot proceed with online demo.")
        print("  Try running test_offline.py instead.")
        print("⚠"*35)
        logger.warning("No data sources available, exiting demo")
        return
    
    # Step 3: Search with fallback
    print("\n" + "="*70)
    print("[3] SEARCH WITH AUTOMATIC FALLBACK")
    print("="*70)
    results, source = demo_search_with_fallback(manager, "Arabidopsis thaliana")
    
    if not results:
        print("\nDemo cannot continue without search results.")
        return
    
    # Step 4: Fetch and store
    print("\n" + "="*70)
    print("[4] FETCH AND STORE DATA")
    print("="*70)
    
    # Get appropriate identifier based on source
    if source == 'ITIS':
        identifier = results[0].get('tsn')
    elif source == 'GBIF':
        identifier = results[0].get('gbif_id')
    else:
        print("Unknown source, cannot proceed")
        return
    
    taxon, lineage = demo_fetch_and_store(manager, identifier, source, db_path)
    
    if taxon and lineage:
        # Step 5: Database operations
        print("\n" + "="*70)
        print("[5] DATABASE OPERATIONS")
        print("="*70)
        demo_database_operations(db_path)
        
        # Success summary
        print("\n" + "="*70)
        print("✓ DEMO COMPLETED SUCCESSFULLY!")
        print("="*70)
        print(f"\nDatabase: {db_path}")
        print(f"Primary data source used: {source}")
        print(f"Logs: Check logs/plant_taxonomy_*.log for details")
        
        print("\nFeatures demonstrated:")
        print("  ✓ Connection testing for multiple data sources")
        print("  ✓ Automatic fallback when primary source fails")
        print("  ✓ Comprehensive error handling and logging")
        print("  ✓ Database operations with error recovery")
        
        logger.info("Demo completed successfully")
    else:
        print("\n✗ Demo incomplete due to data fetch failure")
        logger.warning("Demo incomplete")


def interactive_mode_enhanced(db_path: str = "enhanced_demo.db", verbose: bool = False):
    """Enhanced interactive mode with better error messages."""
    
    setup_quick_logging(verbose=verbose)
    
    print("\n" + "="*70)
    print("ENHANCED INTERACTIVE MODE")
    print("="*70)
    print("\nCommands:")
    print("  test           - Test all data source connections")
    print("  search <name>  - Search across all data sources")
    print("  add <id> <src> - Add taxon (id=TSN/GBIF_ID, src=ITIS/GBIF)")
    print("  find <name>    - Search local database")
    print("  stats          - Show database statistics")
    print("  verbose        - Toggle verbose logging")
    print("  quit           - Exit")
    
    manager = DataSourceManager()
    
    # Initial connection test
    print("\nTesting connections...")
    manager.test_all_connections()
    
    verbose_mode = verbose
    
    while True:
        print("\n" + "-"*70)
        cmd = input("\n> ").strip()
        
        if not cmd:
            continue
            
        if cmd == 'quit':
            print("Goodbye!")
            logger.info("Interactive mode ended")
            break
            
        elif cmd == 'test':
            manager.test_all_connections()
            
        elif cmd == 'verbose':
            verbose_mode = not verbose_mode
            level = 'DEBUG' if verbose_mode else 'INFO'
            print(f"Verbose logging: {'ON' if verbose_mode else 'OFF'} (level={level})")
            
        elif cmd.startswith('search '):
            search_term = cmd[7:].strip()
            demo_search_with_fallback(manager, search_term)
            
        elif cmd.startswith('add '):
            parts = cmd[4:].strip().split()
            if len(parts) != 2:
                print("Usage: add <identifier> <source>")
                print("Example: add 505310 ITIS")
                continue
            
            identifier, source = parts
            source = source.upper()
            
            if source not in ['ITIS', 'GBIF']:
                print("Source must be ITIS or GBIF")
                continue
            
            demo_fetch_and_store(manager, identifier, source, db_path)
            
        elif cmd.startswith('find '):
            search_term = cmd[5:].strip()
            try:
                with TaxonomyDatabase(db_path) as db:
                    results = db.search_by_name(search_term)
                    print(f"\nFound {len(results)} results:")
                    for result in results[:10]:
                        print(f"  • {get_taxon_summary(result)}")
            except Exception as e:
                print(f"Error searching database: {e}")
                logger.error(f"Database search error: {e}")
                
        elif cmd == 'stats':
            demo_database_operations(db_path)
            
        else:
            print("Unknown command. Type 'quit' to exit.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enhanced Plant Taxonomy Database Demo"
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive mode'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose (DEBUG) logging'
    )
    parser.add_argument(
        '--db',
        default='enhanced_demo.db',
        help='Database file path'
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode_enhanced(args.db, args.verbose)
    else:
        run_enhanced_demo(args.verbose)
