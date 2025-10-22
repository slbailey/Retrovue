"""
Plex HTTP client wrapper.

Real Plex HTTP client using requests for fetching libraries and items.
"""

import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, List, Iterator, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger("retrovue.plex")

# Default timeout for requests
DEFAULT_TIMEOUT = 20


@dataclass
class PlexLibrary:
    """Represents a Plex library."""
    key: str
    title: str
    type: str
    agent: str
    scanner: str
    language: str
    updated_at: int
    created_at: int
    scanned_at: int
    content_changed_at: int
    hidden: int
    location: List[Dict[str, str]]


class PlexClient:
    """Real Plex HTTP client using requests."""
    
    def __init__(self, base_url: str, token: str):
        """
        Initialize Plex client.
        
        Args:
            base_url: Plex server base URL (e.g., "http://127.0.0.1:32400")
            token: Plex authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        
        # Set up headers
        self.session.headers.update({
            'Accept': 'application/json',
            'X-Plex-Accept': 'application/json',
            'X-Plex-Product': 'Retrovue',
            'X-Plex-Client-Identifier': 'retrovue-cli',
            'X-Plex-Token': token
        })
        
        # Set up retry strategy
        _retry_kwargs = dict(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        try:
            retry = Retry(allowed_methods=frozenset(["GET", "POST"]), **_retry_kwargs)
        except TypeError:
            # Fallback for older urllib3 versions
            retry = Retry(method_whitelist=frozenset(["GET", "POST"]), **_retry_kwargs)
        
        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def _request(self, path: str, params: Optional[Dict[str, Any]] = None, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
        """
        Make HTTP request to Plex API with proper error handling.
        
        Args:
            path: API endpoint path (without leading slash)
            params: Query parameters
            timeout: Request timeout in seconds
            
        Returns:
            JSON response data
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        
        try:
            response = self.session.get(url, params=params or {}, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Plex API request failed: {e}")
            raise
    
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Legacy method for backward compatibility.
        
        Args:
            endpoint: API endpoint (without leading slash)
            params: Query parameters
            
        Returns:
            JSON response data
            
        Raises:
            requests.RequestException: If request fails
        """
        return self._request(endpoint, params)
    
    def get_libraries(self) -> List[PlexLibrary]:
        """
        Get all libraries from Plex server.
        
        Returns:
            List of PlexLibrary objects
        """
        logger.info("Fetching libraries from Plex server")
        
        data = self._request("/library/sections")
        libraries = []
        
        for section in data.get('MediaContainer', {}).get('Directory', []):
            library = PlexLibrary(
                key=section['key'],
                title=section['title'],
                type=section['type'],
                agent=section.get('agent', ''),
                scanner=section.get('scanner', ''),
                language=section.get('language', ''),
                updated_at=section.get('updatedAt', 0),
                created_at=section.get('createdAt', 0),
                scanned_at=section.get('scannedAt', 0),
                content_changed_at=section.get('contentChangedAt', 0),
                hidden=section.get('hidden', 0),
                location=section.get('Location', [])
            )
            libraries.append(library)
        
        logger.info(f"Found {len(libraries)} libraries")
        return libraries
    
    def get_sections(self) -> Dict[str, str]:
        """
        Get library sections with their types.
        
        Returns:
            Dictionary mapping section_key to section_type
        """
        logger.debug("Fetching library sections")
        
        data = self._request("/library/sections")
        sections = {}
        
        for section in data.get('MediaContainer', {}).get('Directory', []):
            sections[section['key']] = section['type']
        
        logger.debug(f"Found {len(sections)} sections")
        return sections
    
    def iter_items(
        self, 
        library_key: str, 
        kind: str,
        limit: Optional[int] = None,
        offset: int = 0,
        since_epoch: Optional[int] = None
    ) -> Iterator[Dict[str, Any]]:
        """
        Iterate over items in a specific library with proper pagination.
        
        Args:
            library_key: Library key from get_libraries()
            kind: Content kind ("movie" or "episode")
            limit: Number of items per request (None for no limit)
            offset: Starting offset
            since_epoch: Only yield items with updatedAt >= since_epoch
            
        Yields:
            Dictionary containing item data
        """
        logger.debug(f"Fetching {kind} items from library {library_key}")
        if since_epoch:
            logger.debug(f"Filtering for items updated since epoch {since_epoch}")
        
        # Map content types to Plex type codes
        type_map = {
            "movie": "1",
            "episode": "4"
        }
        
        plex_type = type_map.get(kind, "1")
        
        # Use a reasonable default limit if none provided
        request_limit = limit if limit is not None else 50
        
        # When using since_epoch, request sort=updatedAt:desc for better performance
        params = {
            'type': plex_type,
            'X-Plex-Container-Start': offset,
            'X-Plex-Container-Size': request_limit
        }
        
        if since_epoch:
            params['sort'] = 'updatedAt:desc'
        
        items_yielded = 0
        
        while True:
            data = self._request(f"/library/sections/{library_key}/all", params)
            
            items = data.get('MediaContainer', {}).get('Metadata', [])
            if not items:
                break
            
            # Get total size for proper pagination
            total_size = data.get('MediaContainer', {}).get('totalSize', 0)
            
            for item in items:
                # Client-side filtering for since_epoch
                if since_epoch:
                    item_updated_at = item.get('updatedAt')
                    if item_updated_at:
                        try:
                            item_epoch = int(item_updated_at)
                            if item_epoch < since_epoch:
                                continue  # Skip this item
                        except (ValueError, TypeError):
                            # If we can't parse the timestamp, include the item
                            pass
                
                yield item
                items_yielded += 1
                
                # Check if we've hit the limit
                if limit is not None and items_yielded >= limit:
                    return
            
            # Check if we have more items using totalSize
            if offset + len(items) >= total_size or len(items) == 0:
                break
            
            offset += len(items)
            params['X-Plex-Container-Start'] = offset
    
    def get_item_details(self, rating_key: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific item.
        
        Args:
            rating_key: Plex rating key for the item
            
        Returns:
            Dictionary containing detailed item data
        """
        logger.debug(f"Fetching details for item {rating_key}")
        
        data = self._request(f"/library/metadata/{rating_key}")
        return data.get('MediaContainer', {}).get('Metadata', [{}])[0]
    
    def get_show_children(self, show_rating_key: str) -> List[Dict[str, Any]]:
        """
        Get seasons for a TV show.
        
        Args:
            show_rating_key: Plex rating key for the show
            
        Returns:
            List of season dictionaries
        """
        logger.debug(f"Fetching seasons for show {show_rating_key}")
        
        data = self._request(f"/library/metadata/{show_rating_key}/children")
        return data.get('MediaContainer', {}).get('Metadata', [])
    
    def get_season_children(self, season_rating_key: str) -> List[Dict[str, Any]]:
        """
        Get episodes for a season.
        
        Args:
            season_rating_key: Plex rating key for the season
            
        Returns:
            List of episode dictionaries
        """
        logger.debug(f"Fetching episodes for season {season_rating_key}")
        
        data = self._request(f"/library/metadata/{season_rating_key}/children")
        return data.get('MediaContainer', {}).get('Metadata', [])
    
    def test_connection(self) -> bool:
        """
        Test connection to Plex server.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            self._request("/")
            logger.info("Plex connection test successful")
            return True
        except Exception as e:
            logger.error(f"Plex connection test failed: {e}")
            return False
