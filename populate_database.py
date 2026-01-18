#!/usr/bin/env python3
"""
Database population script - adds diverse plant species for testing.

Populates database with representative species from major plant families
including trees, flowers, crops, and medicinal plants.
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import TaxonomyDatabase
from api.data_source_manager import DataSourceManager
from utils.logger import setup_quick_logging, get_logger

logger = get_logger('plant_taxonomy.populate')


# Curated list of interesting plant species across diverse families
PLANT_SPECIES = [
    # Trees
    ("Quercus alba", "White oak"),
    ("Acer saccharum", "Sugar maple"),
    ("Pinus ponderosa", "Ponderosa pine"),
    ("Sequoia sempervirens", "Coast redwood"),
    ("Fagus grandifolia", "American beech"),
    
    # Flowers
    ("Rosa rugosa", "Rugosa rose"),
    ("Tulipa gesneriana", "Garden tulip"),
    ("Helianthus annuus", "Sunflower"),
    ("Lavandula angustifolia", "English lavender"),
    ("Iris germanica", "Bearded iris"),
    
    # Crops & Food Plants
    ("Solanum lycopersicum", "Tomato"),
    ("Zea mays", "Corn/Maize"),
    ("Triticum aestivum", "Wheat"),
    ("Oryza sativa", "Rice"),
    ("Glycine max", "Soybean"),
    ("Brassica oleracea", "Cabbage/Broccoli"),
    
    # Model Organisms
    ("Arabidopsis thaliana", "Thale cress"),
    ("Nicotiana tabacum", "Tobacco"),
    ("Medicago truncatula", "Barrel medic"),
    
    # Medicinal & Herbs
    ("Mentha spicata", "Spearmint"),
    ("Salvia officinalis", "Common sage"),
    ("Echinacea purpurea", "Purple coneflower"),
    ("Ginkgo biloba", "Maidenhair tree"),
    
    # Fruits
    ("Malus domestica", "Apple"),
    ("Prunus persica", "Peach"),
    ("Vitis vinifera", "Grape"),
    ("Fragaria × ananassa", "Strawberry"),
    
    # Cacti & Succulents
    ("Opuntia ficus-indica", "Prickly pear"),
    ("Aloe vera", "Aloe"),
    
    # Ferns & Ancient Plants
    ("Ginkgo biloba", "Ginkgo"),
    
    # Grasses & Bamboo
    ("Bambusa vulgaris", "Common bamboo"),
    ("Festuca rubra", "Red fescue"),
]


def populate_database(db_path: str, verbose: bool = False, max_species: int = None):
    """
    Populate database with diverse plant species.
    
    Args:
        db_path: Path to database file
        verbose: Enable verbose logging
        max_species: Maximum species to add (None for all)
    """
    setup_quick_logging(verbose=verbose)
    
    print("\n" + "🌱"*35)
    print("  DATABASE POPULATION - Diverse Plant Species")
    print("🌱"*35)
    
    # Initialize database
    print("\n[1] Setting up database...")
    db = TaxonomyDatabase(db_path)
    db.connect()
    db.create_schema()
    
    initial_stats = db.get_statistics()
    initial_count = initial_stats['total_taxa']
    print(f"    Current taxa in database: {initial_count}")
    
    db.close()
    
    # Initialize data source manager
    print("\n[2] Testing data source connections...")
    manager = DataSourceManager()
    conn_status = manager.test_all_connections()
    
    if not any(conn_status.values()):
        print("\n✗ No data sources available. Cannot populate database.")
        print("  Please check your internet connection and try again.")
        return
    
    # Populate with species
    species_list = PLANT_SPECIES[:max_species] if max_species else PLANT_SPECIES
    print(f"\n[3] Adding {len(species_list)} plant species...")
    print("    (This may take a few minutes)")
    
    successful = 0
    failed = 0
    failed_species = []
    
    for i, (scientific_name, common_name) in enumerate(species_list, 1):
        print(f"\n[{i}/{len(species_list)}] {scientific_name} ({common_name})")
        logger.info(f"Processing: {scientific_name}")
        
        try:
            # Search for species
            results, source, msg = manager.search_with_best_source(scientific_name)
            
            if not results:
                print(f"    ✗ Not found in any database")
                logger.warning(f"Not found: {scientific_name}")
                failed += 1
                failed_species.append((scientific_name, "Not found"))
                continue
            
            # Get identifier based on source
            if source == 'ITIS':
                identifier = results[0].get('tsn')
            elif source == 'GBIF':
                identifier = results[0].get('gbif_id')
            else:
                print(f"    ✗ Unknown source: {source}")
                failed += 1
                failed_species.append((scientific_name, "Unknown source"))
                continue
            
            print(f"    Found in {source} (ID: {identifier})")
            
            # Get full record
            taxon, lineage, source_used = manager.get_taxon_with_hierarchy(
                identifier, source
            )
            
            if not taxon or not lineage:
                print(f"    ✗ Failed to retrieve full record")
                logger.warning(f"Failed to retrieve: {scientific_name}")
                failed += 1
                failed_species.append((scientific_name, "Retrieval failed"))
                continue
            
            # Store in database
            with TaxonomyDatabase(db_path) as db:
                for taxon_item in lineage:
                    db.insert_taxon(taxon_item.to_dict())
                
                # Store common names
                for cn in taxon.common_names:
                    if hasattr(taxon, 'tsn') and taxon.tsn:
                        db.insert_common_name(taxon.tsn, cn)
            
            print(f"    ✓ Stored {len(lineage)} taxa")
            logger.info(f"Success: {scientific_name}")
            successful += 1
            
            # Small delay to be nice to APIs
            if i < len(species_list):
                time.sleep(0.5)
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
            logger.error(f"Error with {scientific_name}: {e}")
            failed += 1
            failed_species.append((scientific_name, str(e)))
            continue
    
    # Final statistics
    print("\n" + "="*70)
    print("POPULATION COMPLETE")
    print("="*70)
    
    with TaxonomyDatabase(db_path) as db:
        final_stats = db.get_statistics()
    
    final_count = final_stats['total_taxa']
    added = final_count - initial_count
    
    print(f"\nResults:")
    print(f"  Successful: {successful}/{len(species_list)}")
    print(f"  Failed: {failed}/{len(species_list)}")
    print(f"\nDatabase:")
    print(f"  Total taxa: {final_count} (+{added})")
    print(f"  Common names: {final_stats['total_common_names']}")
    
    if final_stats.get('by_rank'):
        print(f"\nTaxa by rank:")
        for rank, count in sorted(final_stats['by_rank'].items(), 
                                 key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {rank:20s}: {count:4d}")
    
    if failed_species:
        print(f"\nFailed species ({len(failed_species)}):")
        for name, reason in failed_species[:10]:
            print(f"  ✗ {name}: {reason}")
        if len(failed_species) > 10:
            print(f"  ... and {len(failed_species) - 10} more")
    
    print(f"\nDatabase file: {db_path}")
    print("Ready for GUI exploration!")
    
    logger.info(f"Population complete: {successful} successful, {failed} failed")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Populate plant taxonomy database with diverse species"
    )
    parser.add_argument(
        '--db',
        default='plants_populated.db',
        help='Database file path (default: plants_populated.db)'
    )
    parser.add_argument(
        '--max',
        type=int,
        default=None,
        help='Maximum number of species to add'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    populate_database(args.db, verbose=args.verbose, max_species=args.max)
