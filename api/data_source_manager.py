"""
Data source manager with fallback logic.

Manages multiple taxonomic data sources (ITIS, GBIF, etc.) and provides
automatic fallback when primary sources fail.
"""

from typing import Optional, List, Dict, Any, Tuple
from models.taxonomy import Taxon
from api.itis_client import ITISClient, ITISConnectionError
from api.gbif_client import GBIFClient, GBIFConnectionError
from utils.logger import get_logger

logger = get_logger('plant_taxonomy.api.manager')


class DataSourceManager:
    """
    Manages multiple data sources with automatic fallback.
    
    Tries data sources in priority order and falls back to alternatives
    when primary sources fail.
    """
    
    def __init__(self, prefer_itis=True):
        """
        Initialize data source manager.
        
        Args:
            prefer_itis: If True, prefer ITIS over GBIF; otherwise reverse
        """
        self.itis = ITISClient()
        self.gbif = GBIFClient()
        
        # Set source priority
        if prefer_itis:
            self.sources = [
                ('ITIS', self.itis),
                ('GBIF', self.gbif)
            ]
        else:
            self.sources = [
                ('GBIF', self.gbif),
                ('ITIS', self.itis)
            ]
        
        logger.info(f"DataSourceManager initialized (primary: {self.sources[0][0]})")
        
    def test_all_connections(self) -> Dict[str, bool]:
        """
        Test connectivity to all data sources.
        
        Returns:
            Dictionary mapping source names to connection status
        """
        logger.info("Testing all data source connections...")
        
        results = {}
        
        print("\n" + "="*70)
        print("DATA SOURCE CONNECTION TEST")
        print("="*70)
        
        # Test ITIS
        print("\n[1] Testing ITIS (itis.gov)...")
        itis_ok = self.itis.test_connection()
        results['ITIS'] = itis_ok
        if itis_ok:
            print("    ✓ ITIS: Connected")
        else:
            print("    ✗ ITIS: Connection failed")
        
        # Test GBIF
        print("\n[2] Testing GBIF (gbif.org)...")
        gbif_ok = self.gbif.test_connection()
        results['GBIF'] = gbif_ok
        if gbif_ok:
            print("    ✓ GBIF: Connected")
        else:
            print("    ✗ GBIF: Connection failed")
        
        print("\n" + "="*70)
        
        # Summary
        available = [name for name, status in results.items() if status]
        if available:
            logger.info(f"Available sources: {', '.join(available)}")
            print(f"\n✓ {len(available)} data source(s) available: {', '.join(available)}")
        else:
            logger.warning("No data sources available!")
            print("\n✗ No data sources available - check internet connection")
        
        return results
        
    def search_by_scientific_name(self, scientific_name: str, limit: int = 20) -> Tuple[List[Dict[str, Any]], str]:
        """
        Search for taxa by scientific name across all sources.
        
        Args:
            scientific_name: Scientific name to search for
            limit: Maximum results
            
        Returns:
            Tuple of (results list, source name)
        """
        logger.info(f"Searching for '{scientific_name}' across data sources")
        
        for source_name, client in self.sources:
            try:
                logger.info(f"Trying {source_name}...")
                results = client.search_by_scientific_name(scientific_name)
                
                if results:
                    logger.info(f"✓ Found {len(results)} results from {source_name}")
                    return results, source_name
                else:
                    logger.info(f"No results from {source_name}, trying next source...")
                    
            except (ITISConnectionError, GBIFConnectionError) as e:
                logger.warning(f"{source_name} failed: {e}")
                logger.info(f"Falling back to next data source...")
                continue
            except Exception as e:
                logger.error(f"Unexpected error with {source_name}: {e}")
                continue
        
        logger.warning("All data sources exhausted, no results found")
        return [], 'None'
        
    def get_taxon_with_hierarchy(self, identifier: Any, source: str = None) -> Tuple[Optional[Taxon], List[Taxon], str]:
        """
        Get taxon and its full hierarchy.
        
        Args:
            identifier: TSN for ITIS or GBIF ID for GBIF
            source: Specific source to use ('ITIS' or 'GBIF'), or None for auto
            
        Returns:
            Tuple of (taxon, hierarchy, source_used)
        """
        # If source specified, try only that source
        if source:
            sources_to_try = [(s, c) for s, c in self.sources if s == source]
        else:
            sources_to_try = self.sources
        
        logger.info(f"Fetching taxon {identifier} with hierarchy")
        
        for source_name, client in sources_to_try:
            try:
                logger.info(f"Trying {source_name}...")
                
                if source_name == 'ITIS':
                    hierarchy = client.get_full_hierarchy_from_tsn(int(identifier))
                    if hierarchy:
                        taxon = hierarchy[-1]
                        # Get common names
                        taxon.common_names = client.get_common_names_from_tsn(int(identifier))
                        logger.info(f"✓ Retrieved from {source_name}: {taxon.scientific_name}")
                        return taxon, hierarchy, source_name
                        
                elif source_name == 'GBIF':
                    hierarchy = client.get_classification(int(identifier))
                    taxon = client.get_species_by_id(int(identifier))
                    if taxon and hierarchy:
                        logger.info(f"✓ Retrieved from {source_name}: {taxon.scientific_name}")
                        return taxon, hierarchy, source_name
                
                logger.info(f"No data from {source_name}, trying next source...")
                
            except (ITISConnectionError, GBIFConnectionError) as e:
                logger.warning(f"{source_name} failed: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error with {source_name}: {e}")
                continue
        
        logger.warning("All data sources exhausted")
        return None, [], 'None'
        
    def search_with_best_source(self, scientific_name: str) -> Tuple[Optional[List[Dict]], str, str]:
        """
        Search and return results with source information and status message.
        
        Args:
            scientific_name: Scientific name to search
            
        Returns:
            Tuple of (results, source_used, status_message)
        """
        results, source = self.search_by_scientific_name(scientific_name)
        
        if results:
            msg = f"Found {len(results)} results from {source}"
            logger.info(msg)
            return results, source, msg
        else:
            msg = "No results found from any data source"
            logger.warning(msg)
            return None, 'None', msg
