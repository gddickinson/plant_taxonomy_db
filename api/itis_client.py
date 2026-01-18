"""
Enhanced ITIS (Integrated Taxonomic Information System) API client.

Provides robust methods to query ITIS web services with retry logic,
error handling, and comprehensive logging.
"""

import requests
import time
from typing import Optional, List, Dict, Any
from xml.etree import ElementTree as ET
from models.taxonomy import Taxon
from utils.logger import get_logger

logger = get_logger('plant_taxonomy.api.itis')


class ITISError(Exception):
    """Base exception for ITIS API errors."""
    pass


class ITISConnectionError(ITISError):
    """Raised when connection to ITIS fails."""
    pass


class ITISDataError(ITISError):
    """Raised when ITIS returns invalid data."""
    pass


class ITISClient:
    """Enhanced client for ITIS web services API with retry logic."""
    
    BASE_URL = "https://www.itis.gov/ITISWebService/services/ITISService"
    
    def __init__(self, max_retries=3, retry_delay=1.0, timeout=30):
        """
        Initialize ITIS client.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (seconds)
            timeout: Request timeout (seconds)
        """
        self.session = requests.Session()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        
        logger.info(f"ITIS client initialized (retries={max_retries}, timeout={timeout}s)")
        
    def _make_request(self, endpoint: str, params: dict) -> requests.Response:
        """
        Make HTTP request with retry logic.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response object
            
        Raises:
            ITISConnectionError: If connection fails after retries
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Request to {endpoint} (attempt {attempt + 1}/{self.max_retries})")
                logger.debug(f"Parameters: {params}")
                
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
                    delay = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    raise ITISConnectionError(
                        f"Request timed out after {self.max_retries} attempts"
                    )
                    
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error: {e} (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)
                else:
                    raise ITISConnectionError(
                        f"Failed to connect to ITIS after {self.max_retries} attempts. "
                        f"Please check your internet connection and try again."
                    )
                    
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error: {e}")
                if response.status_code >= 500:
                    # Server error - retry
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2 ** attempt)
                        logger.info(f"Server error, retrying in {delay:.1f} seconds...")
                        time.sleep(delay)
                    else:
                        raise ITISConnectionError(
                            f"ITIS server error (HTTP {response.status_code}) after {self.max_retries} attempts"
                        )
                else:
                    # Client error - don't retry
                    raise ITISConnectionError(
                        f"ITIS request failed with HTTP {response.status_code}"
                    )
                    
            except Exception as e:
                logger.error(f"Unexpected error: {type(e).__name__}: {e}")
                raise ITISConnectionError(f"Unexpected error connecting to ITIS: {e}")
        
        raise ITISConnectionError("Request failed after all retry attempts")
        
    def _parse_response(self, response: requests.Response) -> ET.Element:
        """
        Parse XML response from ITIS.
        
        Args:
            response: HTTP response
            
        Returns:
            XML root element
            
        Raises:
            ITISDataError: If XML parsing fails
        """
        try:
            root = ET.fromstring(response.content)
            logger.debug("XML parsed successfully")
            return root
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML response: {e}")
            logger.debug(f"Response content: {response.content[:500]}")
            raise ITISDataError(f"Invalid XML response from ITIS: {e}")
            
    def test_connection(self) -> bool:
        """
        Test connection to ITIS API.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info("Testing ITIS connection...")
            # Simple search that should always work
            self._make_request('searchByScientificName', {'srchKey': 'Plantae'})
            logger.info("✓ ITIS connection successful")
            return True
        except ITISConnectionError as e:
            logger.error(f"✗ ITIS connection failed: {e}")
            return False
            
    def search_by_scientific_name(self, scientific_name: str) -> List[Dict[str, Any]]:
        """
        Search for taxa by scientific name.
        
        Args:
            scientific_name: Scientific name to search for
            
        Returns:
            List of matching results with TSN and name info
        """
        logger.info(f"Searching ITIS for: '{scientific_name}'")
        
        try:
            response = self._make_request(
                'searchByScientificName',
                {'srchKey': scientific_name}
            )
            
            root = self._parse_response(response)
            results = []
            
            # Parse XML results
            ns = {'ax21': 'http://data.itis_service.itis.usgs.gov/xsd'}
            for item in root.findall('.//ax21:scientificName', ns):
                result = {}
                
                tsn_elem = item.find('ax21:tsn', ns)
                name_elem = item.find('ax21:combinedName', ns)
                author_elem = item.find('ax21:author', ns)
                
                if tsn_elem is not None and name_elem is not None:
                    result['tsn'] = tsn_elem.text
                    result['scientific_name'] = name_elem.text
                    result['author'] = author_elem.text if author_elem is not None else None
                    results.append(result)
            
            logger.info(f"Found {len(results)} results")
            return results
            
        except ITISConnectionError as e:
            logger.error(f"Search failed: {e}")
            raise
        except ITISDataError as e:
            logger.error(f"Data parsing failed: {e}")
            raise
            
    def get_full_hierarchy_from_tsn(self, tsn: int) -> List[Taxon]:
        """
        Get complete taxonomic hierarchy for a TSN.
        
        Args:
            tsn: Taxonomic Serial Number
            
        Returns:
            List of Taxon objects from kingdom to species
        """
        logger.info(f"Fetching hierarchy for TSN: {tsn}")
        
        try:
            response = self._make_request(
                'getFullHierarchyFromTSN',
                {'tsn': tsn}
            )
            
            root = self._parse_response(response)
            hierarchy = []
            
            ns = {'ax21': 'http://data.itis_service.itis.usgs.gov/xsd'}
            for item in root.findall('.//ax21:hierarchyList', ns):
                taxon_data = {}
                
                # Extract fields
                for field in ['tsn', 'parentTsn', 'rankName', 'taxonName']:
                    elem = item.find(f'ax21:{field}', ns)
                    if elem is not None and elem.text:
                        taxon_data[field] = elem.text
                
                if 'taxonName' in taxon_data and 'rankName' in taxon_data:
                    taxon = Taxon(
                        scientific_name=taxon_data['taxonName'],
                        rank=taxon_data['rankName'],
                        tsn=int(taxon_data.get('tsn', 0)) or None,
                        parent_tsn=int(taxon_data.get('parentTsn', 0)) or None,
                        source='ITIS'
                    )
                    
                    # Assign to hierarchical fields based on rank
                    rank = taxon.rank
                    if rank == 'Kingdom':
                        taxon.kingdom = taxon.scientific_name
                    elif rank in ['Division', 'Phylum']:
                        taxon.division = taxon.scientific_name
                    elif rank == 'Class':
                        taxon.class_name = taxon.scientific_name
                    elif rank == 'Order':
                        taxon.order = taxon.scientific_name
                    elif rank == 'Family':
                        taxon.family = taxon.scientific_name
                    elif rank == 'Genus':
                        taxon.genus = taxon.scientific_name
                    elif rank == 'Species':
                        taxon.species = taxon.scientific_name.split()[-1] if ' ' in taxon.scientific_name else taxon.scientific_name
                    elif rank == 'Subspecies':
                        taxon.subspecies = taxon.scientific_name
                    elif rank == 'Variety':
                        taxon.variety = taxon.scientific_name
                    
                    hierarchy.append(taxon)
            
            logger.info(f"Retrieved hierarchy with {len(hierarchy)} ranks")
            return hierarchy
            
        except ITISConnectionError as e:
            logger.error(f"Failed to get hierarchy: {e}")
            raise
        except ITISDataError as e:
            logger.error(f"Data parsing failed: {e}")
            raise
            
    def get_common_names_from_tsn(self, tsn: int) -> List[str]:
        """
        Get common names for a TSN.
        
        Args:
            tsn: Taxonomic Serial Number
            
        Returns:
            List of common names
        """
        logger.debug(f"Fetching common names for TSN: {tsn}")
        
        try:
            response = self._make_request(
                'getCommonNamesFromTSN',
                {'tsn': tsn}
            )
            
            root = self._parse_response(response)
            common_names = []
            
            ns = {'ax21': 'http://data.itis_service.itis.usgs.gov/xsd'}
            for item in root.findall('.//ax21:commonNames', ns):
                name_elem = item.find('ax21:commonName', ns)
                if name_elem is not None and name_elem.text:
                    common_names.append(name_elem.text)
            
            logger.debug(f"Found {len(common_names)} common names")
            return common_names
            
        except ITISConnectionError as e:
            logger.warning(f"Failed to get common names: {e}")
            return []  # Non-critical - return empty list
            
    def get_record(self, tsn: int) -> Optional[Taxon]:
        """
        Get complete record for a TSN including hierarchy.
        
        Args:
            tsn: Taxonomic Serial Number
            
        Returns:
            Taxon object with complete information
        """
        logger.info(f"Fetching complete record for TSN: {tsn}")
        
        try:
            # Get hierarchy
            hierarchy = self.get_full_hierarchy_from_tsn(tsn)
            if not hierarchy:
                logger.warning(f"No hierarchy found for TSN: {tsn}")
                return None
                
            # The last item in hierarchy should be our target taxon
            taxon = hierarchy[-1]
            
            # Fill in hierarchical fields from complete lineage
            for ancestor in hierarchy:
                rank = ancestor.rank
                if rank == 'Kingdom' and not taxon.kingdom:
                    taxon.kingdom = ancestor.scientific_name
                elif rank in ['Division', 'Phylum'] and not taxon.division:
                    taxon.division = ancestor.scientific_name
                elif rank == 'Class' and not taxon.class_name:
                    taxon.class_name = ancestor.scientific_name
                elif rank == 'Order' and not taxon.order:
                    taxon.order = ancestor.scientific_name
                elif rank == 'Family' and not taxon.family:
                    taxon.family = ancestor.scientific_name
                elif rank == 'Genus' and not taxon.genus:
                    taxon.genus = ancestor.scientific_name
            
            # Get common names
            taxon.common_names = self.get_common_names_from_tsn(tsn)
            
            logger.info(f"✓ Retrieved complete record: {taxon.scientific_name}")
            return taxon
            
        except Exception as e:
            logger.error(f"Failed to get record for TSN {tsn}: {e}")
            raise
            
    def search_plant_kingdom(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for plant taxa only.
        
        Args:
            search_term: Search string
            limit: Maximum results
            
        Returns:
            List of plant taxa matching search
        """
        logger.info(f"Searching for plants: '{search_term}'")
        
        all_results = self.search_by_scientific_name(search_term)
        plant_results = []
        
        # Filter for plants by checking kingdom
        for result in all_results[:limit * 2]:  # Check extra in case we filter many out
            try:
                tsn = int(result['tsn'])
                hierarchy = self.get_full_hierarchy_from_tsn(tsn)
                
                # Check if kingdom is Plantae
                if hierarchy and hierarchy[0].scientific_name == 'Plantae':
                    plant_results.append(result)
                    logger.debug(f"✓ Plant: {result['scientific_name']}")
                else:
                    logger.debug(f"✗ Not a plant: {result['scientific_name']}")
                    
                if len(plant_results) >= limit:
                    break
                    
            except Exception as e:
                logger.warning(f"Error checking kingdom for TSN {result.get('tsn')}: {e}")
                continue
        
        logger.info(f"Found {len(plant_results)} plant results")
        return plant_results
