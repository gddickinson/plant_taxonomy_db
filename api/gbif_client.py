"""
GBIF (Global Biodiversity Information Facility) API client.

Provides access to GBIF's species API as a fallback data source.
Documentation: https://www.gbif.org/developer/species
"""

import requests
import time
from typing import Optional, List, Dict, Any
from models.taxonomy import Taxon
from utils.logger import get_logger

logger = get_logger('plant_taxonomy.api.gbif')


class GBIFError(Exception):
    """Base exception for GBIF API errors."""
    pass


class GBIFConnectionError(GBIFError):
    """Raised when connection to GBIF fails."""
    pass


class GBIFClient:
    """Client for GBIF species API."""
    
    BASE_URL = "https://api.gbif.org/v1"
    
    def __init__(self, max_retries=3, retry_delay=1.0, timeout=30):
        """
        Initialize GBIF client.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (seconds)
            timeout: Request timeout (seconds)
        """
        self.session = requests.Session()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        
        logger.info(f"GBIF client initialized (retries={max_retries}, timeout={timeout}s)")
        
    def _make_request(self, endpoint: str, params: dict = None) -> requests.Response:
        """
        Make HTTP request with retry logic.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response object
            
        Raises:
            GBIFConnectionError: If connection fails after retries
        """
        url = f"{self.BASE_URL}/{endpoint}"
        params = params or {}
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Request to {endpoint} (attempt {attempt + 1}/{self.max_retries})")
                
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                logger.debug(f"Request successful ({len(response.content)} bytes)")
                return response
                
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    raise GBIFConnectionError("Request timed out after retries")
                    
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error: {e}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    time.sleep(delay)
                else:
                    raise GBIFConnectionError(
                        "Failed to connect to GBIF. Please check your internet connection."
                    )
                    
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error: {e}")
                raise GBIFConnectionError(f"GBIF request failed: {e}")
                
        raise GBIFConnectionError("Request failed after all retry attempts")
        
    def test_connection(self) -> bool:
        """
        Test connection to GBIF API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info("Testing GBIF connection...")
            self._make_request('species/search', {'q': 'Plantae', 'limit': 1})
            logger.info("✓ GBIF connection successful")
            return True
        except GBIFConnectionError as e:
            logger.error(f"✗ GBIF connection failed: {e}")
            return False
            
    def search_by_scientific_name(self, scientific_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for species by scientific name.
        
        Args:
            scientific_name: Scientific name to search for
            limit: Maximum results
            
        Returns:
            List of matching results
        """
        logger.info(f"Searching GBIF for: '{scientific_name}'")
        
        try:
            response = self._make_request(
                'species/search',
                {
                    'q': scientific_name,
                    'limit': limit,
                    'kingdom': 'Plantae'  # Filter for plants
                }
            )
            
            data = response.json()
            results = []
            
            for item in data.get('results', []):
                result = {
                    'gbif_id': item.get('key'),
                    'scientific_name': item.get('scientificName', item.get('canonicalName')),
                    'author': item.get('authorship'),
                    'rank': item.get('rank'),
                    'kingdom': item.get('kingdom'),
                    'family': item.get('family'),
                    'genus': item.get('genus'),
                    'species': item.get('species')
                }
                results.append(result)
            
            logger.info(f"Found {len(results)} results")
            return results
            
        except GBIFConnectionError as e:
            logger.error(f"Search failed: {e}")
            raise
            
    def get_species_by_id(self, gbif_id: int) -> Optional[Taxon]:
        """
        Get species information by GBIF ID.
        
        Args:
            gbif_id: GBIF species key
            
        Returns:
            Taxon object or None
        """
        logger.info(f"Fetching species for GBIF ID: {gbif_id}")
        
        try:
            response = self._make_request(f'species/{gbif_id}')
            data = response.json()
            
            # Build taxon from GBIF data
            taxon = Taxon(
                scientific_name=data.get('scientificName', data.get('canonicalName')),
                rank=data.get('rank', '').title(),
                authorship=data.get('authorship'),
                kingdom=data.get('kingdom'),
                division=data.get('phylum'),
                class_name=data.get('class'),
                order=data.get('order'),
                family=data.get('family'),
                genus=data.get('genus'),
                species=data.get('species'),
                source='GBIF'
            )
            
            # Try to get vernacular names
            try:
                vern_response = self._make_request(f'species/{gbif_id}/vernacularNames')
                vern_data = vern_response.json()
                common_names = [
                    v['vernacularName'] 
                    for v in vern_data.get('results', [])
                    if v.get('language') == 'eng'
                ][:5]  # Limit to 5 English names
                taxon.common_names = common_names
            except Exception as e:
                logger.debug(f"Could not fetch vernacular names: {e}")
            
            logger.info(f"✓ Retrieved: {taxon.scientific_name}")
            return taxon
            
        except Exception as e:
            logger.error(f"Failed to get species: {e}")
            return None
            
    def get_classification(self, gbif_id: int) -> List[Taxon]:
        """
        Get taxonomic classification/hierarchy for a GBIF species.
        
        Args:
            gbif_id: GBIF species key
            
        Returns:
            List of Taxon objects from kingdom to species
        """
        logger.info(f"Fetching classification for GBIF ID: {gbif_id}")
        
        try:
            response = self._make_request(f'species/{gbif_id}')
            data = response.json()
            
            # Build hierarchy from classification data
            hierarchy = []
            
            # Kingdom
            if data.get('kingdom'):
                hierarchy.append(Taxon(
                    scientific_name=data['kingdom'],
                    rank='Kingdom',
                    kingdom=data['kingdom'],
                    source='GBIF'
                ))
            
            # Phylum/Division
            if data.get('phylum'):
                hierarchy.append(Taxon(
                    scientific_name=data['phylum'],
                    rank='Division',
                    kingdom=data.get('kingdom'),
                    division=data['phylum'],
                    source='GBIF'
                ))
            
            # Class
            if data.get('class'):
                hierarchy.append(Taxon(
                    scientific_name=data['class'],
                    rank='Class',
                    kingdom=data.get('kingdom'),
                    division=data.get('phylum'),
                    class_name=data['class'],
                    source='GBIF'
                ))
            
            # Order
            if data.get('order'):
                hierarchy.append(Taxon(
                    scientific_name=data['order'],
                    rank='Order',
                    kingdom=data.get('kingdom'),
                    division=data.get('phylum'),
                    class_name=data.get('class'),
                    order=data['order'],
                    source='GBIF'
                ))
            
            # Family
            if data.get('family'):
                hierarchy.append(Taxon(
                    scientific_name=data['family'],
                    rank='Family',
                    kingdom=data.get('kingdom'),
                    division=data.get('phylum'),
                    class_name=data.get('class'),
                    order=data.get('order'),
                    family=data['family'],
                    source='GBIF'
                ))
            
            # Genus
            if data.get('genus'):
                hierarchy.append(Taxon(
                    scientific_name=data['genus'],
                    rank='Genus',
                    kingdom=data.get('kingdom'),
                    division=data.get('phylum'),
                    class_name=data.get('class'),
                    order=data.get('order'),
                    family=data.get('family'),
                    genus=data['genus'],
                    source='GBIF'
                ))
            
            # Species
            if data.get('canonicalName'):
                species_epithet = data['canonicalName'].split()[-1] if ' ' in data['canonicalName'] else None
                hierarchy.append(Taxon(
                    scientific_name=data['canonicalName'],
                    rank='Species',
                    authorship=data.get('authorship'),
                    kingdom=data.get('kingdom'),
                    division=data.get('phylum'),
                    class_name=data.get('class'),
                    order=data.get('order'),
                    family=data.get('family'),
                    genus=data.get('genus'),
                    species=species_epithet,
                    source='GBIF'
                ))
            
            logger.info(f"Retrieved classification with {len(hierarchy)} ranks")
            return hierarchy
            
        except Exception as e:
            logger.error(f"Failed to get classification: {e}")
            return []
