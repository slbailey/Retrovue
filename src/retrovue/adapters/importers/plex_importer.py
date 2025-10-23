"""
Plex Media Server importer for discovering content from Plex servers.

This importer connects to Plex Media Server instances and discovers content
from their libraries, extracting metadata and file paths.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import DiscoveredItem, Importer, ImporterError

logger = logging.getLogger(__name__)


class PlexClient:
    """Plex HTTP client for fetching libraries and items."""
    
    def __init__(self, base_url: str, token: str):
        """
        Initialize Plex client.
        
        Args:
            base_url: Plex server base URL (e.g., "http://127.0.0.1:32400")
            token: Plex authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def get_libraries(self) -> list[dict[str, Any]]:
        """
        Get all libraries from the Plex server.
        
        Returns:
            List of library information dictionaries
            
        Raises:
            ImporterError: If the request fails
        """
        try:
            url = f"{self.base_url}/library/sections"
            params = {"X-Plex-Token": self.token}
            
            print(f"DEBUG: Making request to {url} with token {'***' if self.token else None}")
            
            response = self.session.get(url, params=params, timeout=20)
            print(f"DEBUG: Response status: {response.status_code}")
            print(f"DEBUG: Response content length: {len(response.content)}")
            
            response.raise_for_status()
            
            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            print(f"DEBUG: XML root tag: {root.tag}")
            print(f"DEBUG: XML root attributes: {root.attrib}")
            
            libraries = []
            sections = root.findall('Directory')
            print(f"DEBUG: Found {len(sections)} Directory elements")
            
            for i, section in enumerate(sections):
                lib_id = section.get('key')
                lib_name = section.get('title')
                lib_type = section.get('type')
                
                print(f"DEBUG: Section {i}: key={lib_id}, title={lib_name}, type={lib_type}")
                
                if lib_id and lib_name:
                    libraries.append({
                        "key": lib_id,
                        "title": lib_name,
                        "type": lib_type
                    })
            
            print(f"DEBUG: Returning {len(libraries)} libraries")
            return libraries
            
        except requests.RequestException as e:
            print(f"DEBUG: Request exception: {e}")
            raise ImporterError(f"Failed to fetch libraries: {e}") from e
        except Exception as e:
            print(f"DEBUG: General exception in get_libraries: {e}")
            raise ImporterError(f"Failed to fetch libraries: {e}") from e
    
    def get_library_items(self, library_key: str) -> list[dict[str, Any]]:
        """
        Get all items from a specific library.
        
        Args:
            library_key: The library key to fetch items from
            
        Returns:
            List of item information dictionaries
            
        Raises:
            ImporterError: If the request fails
        """
        try:
            url = f"{self.base_url}/library/sections/{library_key}/all"
            params = {"X-Plex-Token": self.token}
            
            response = self.session.get(url, params=params, timeout=20)
            response.raise_for_status()
            
            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            items = []
            
            for video in root.findall('Video'):
                rating_key = video.get('ratingKey')
                title = video.get('title')
                year = video.get('year')
                type_attr = video.get('type')
                
                # Get file information
                media = video.find('Media')
                file_path = None
                file_size = None
                
                if media is not None:
                    part = media.find('Part')
                    if part is not None:
                        file_path = part.get('file')
                        file_size = part.get('size')
                
                if rating_key and title:
                    items.append({
                        "ratingKey": rating_key,
                        "title": title,
                        "year": year,
                        "type": type_attr,
                        "file_path": file_path,
                        "fileSize": file_size,
                        "updatedAt": video.get('updatedAt')
                    })
            
            return items
            
        except requests.RequestException as e:
            raise ImporterError(f"Failed to fetch library items: {e}") from e


class PlexImporter:
    """
    Importer for discovering content from Plex Media Server.
    
    This importer connects to Plex servers and discovers content from their
    libraries, extracting metadata and file paths.
    """
    
    name = "plex"
    
    def __init__(
        self,
        servers: list[dict[str, Any]] | None = None,
        include_metadata: bool = True
    ):
        """
        Initialize the Plex importer.
        
        Args:
            servers: List of server configurations with 'base_url' and 'token'
            include_metadata: Whether to include Plex metadata in discovered items
        """
        self.servers = servers or []
        self.include_metadata = include_metadata
    
    def discover(self) -> list[DiscoveredItem]:
        """
        Discover content from all configured Plex servers.
        
        Returns:
            List of discovered content items
            
        Raises:
            ImporterError: If discovery fails
        """
        try:
            discovered_items = []
            
            for server_config in self.servers:
                try:
                    server_items = self._discover_from_server(server_config)
                    discovered_items.extend(server_items)
                except Exception as e:
                    logger.warning(f"Failed to discover from server {server_config.get('base_url', 'unknown')}: {e}")
                    continue
            
            return discovered_items
            
        except Exception as e:
            raise ImporterError(f"Failed to discover content: {str(e)}") from e
    
    def discover_libraries(self) -> list[dict[str, Any]]:
        """
        Discover libraries from all configured Plex servers.
        
        Returns:
            List of library information dictionaries
            
        Raises:
            ImporterError: If discovery fails
        """
        try:
            all_libraries = []
            print(f"DEBUG: PlexImporter.discover_libraries called with {len(self.servers)} servers")
            
            for i, server_config in enumerate(self.servers):
                try:
                    base_url = server_config.get("base_url")
                    token = server_config.get("token")
                    
                    print(f"DEBUG: Server {i}: base_url={base_url}, token={'***' if token else None}")
                    
                    if not base_url or not token:
                        print(f"DEBUG: Server configuration missing base_url or token: {server_config}")
                        logger.warning(f"Server configuration missing base_url or token: {server_config}")
                        continue
                    
                    # Create Plex client
                    plex_client = PlexClient(base_url, token)
                    print(f"DEBUG: Created PlexClient for {base_url}")
                    
                    # Get libraries from this server
                    libraries = plex_client.get_libraries()
                    print(f"DEBUG: Got {len(libraries)} libraries from {base_url}: {libraries}")
                    all_libraries.extend(libraries)
                    
                except Exception as e:
                    print(f"DEBUG: Failed to discover libraries from server {server_config.get('base_url', 'unknown')}: {e}")
                    logger.warning(f"Failed to discover libraries from server {server_config.get('base_url', 'unknown')}: {e}")
                    continue
            
            print(f"DEBUG: Returning {len(all_libraries)} total libraries")
            return all_libraries
            
        except Exception as e:
            print(f"DEBUG: Exception in discover_libraries: {e}")
            raise ImporterError(f"Failed to discover libraries: {str(e)}") from e

    def discover_from_collection(
        self, 
        collection_id: str, 
        include_metadata: bool = True
    ) -> list[DiscoveredItem]:
        """
        Discover content from a specific Plex collection (library).
        
        Args:
            collection_id: Plex library key
            include_metadata: Whether to include Plex metadata
            
        Returns:
            List of discovered content items from the collection
            
        Raises:
            ImporterError: If discovery fails
        """
        try:
            discovered_items = []
            
            for server_config in self.servers:
                try:
                    server_items = self._discover_from_server_collection(
                        server_config, 
                        collection_id, 
                        include_metadata
                    )
                    discovered_items.extend(server_items)
                except Exception as e:
                    logger.warning(f"Failed to discover from server {server_config.get('base_url', 'unknown')} collection {collection_id}: {e}")
                    continue
            
            return discovered_items
            
        except Exception as e:
            raise ImporterError(f"Failed to discover from collection {collection_id}: {str(e)}") from e
    
    def _discover_from_server(self, server_config: dict[str, Any]) -> list[DiscoveredItem]:
        """
        Discover content from a specific Plex server.
        
        Args:
            server_config: Server configuration dictionary
            
        Returns:
            List of discovered items from this server
        """
        base_url = server_config.get("base_url")
        token = server_config.get("token")
        
        if not base_url or not token:
            raise ImporterError("Server configuration missing base_url or token")
        
        # Create Plex client
        plex_client = PlexClient(base_url, token)
        
        # Get all libraries
        libraries = plex_client.get_libraries()
        
        discovered_items = []
        
        for library in libraries:
            try:
                library_items = self._discover_from_library(plex_client, library)
                discovered_items.extend(library_items)
            except Exception as e:
                logger.warning(f"Failed to discover from library {library.get('title', 'unknown')}: {e}")
                continue
        
        return discovered_items
    
    def _discover_from_server_collection(
        self, 
        server_config: dict[str, Any], 
        collection_id: str, 
        include_metadata: bool
    ) -> list[DiscoveredItem]:
        """
        Discover content from a specific collection on a Plex server.
        
        Args:
            server_config: Server configuration dictionary
            collection_id: Plex library key
            include_metadata: Whether to include Plex metadata
            
        Returns:
            List of discovered items from this collection
        """
        base_url = server_config.get("base_url")
        token = server_config.get("token")
        
        if not base_url or not token:
            raise ImporterError("Server configuration missing base_url or token")
        
        # Create Plex client
        plex_client = PlexClient(base_url, token)
        
        # Get items from the specific collection
        items = plex_client.get_library_items(collection_id)
        
        discovered_items = []
        
        for item in items:
            try:
                discovered_item = self._create_discovered_item(item, {"key": collection_id})
                if discovered_item:
                    discovered_items.append(discovered_item)
            except Exception as e:
                logger.warning(f"Failed to process item: {e}")
                continue
        
        return discovered_items
    
    def _discover_from_library(
        self, 
        plex_client: PlexClient, 
        library: dict[str, Any]
    ) -> list[DiscoveredItem]:
        """
        Discover content from a specific library.
        
        Args:
            plex_client: Plex client instance
            library: Library information dictionary
            
        Returns:
            List of discovered items from this library
        """
        library_key = library.get("key")
        if not library_key:
            return []
        
        # Get library items
        items = plex_client.get_library_items(library_key)
        
        discovered_items = []
        
        for item in items:
            try:
                discovered_item = self._create_discovered_item(item, library)
                if discovered_item:
                    discovered_items.append(discovered_item)
            except Exception as e:
                logger.warning(f"Failed to process item: {e}")
                continue
        
        return discovered_items
    
    def _create_discovered_item(
        self, 
        item: dict[str, Any], 
        library: dict[str, Any]
    ) -> DiscoveredItem | None:
        """
        Create a DiscoveredItem from a Plex item.
        
        Args:
            item: Plex item information
            library: Library information
            
        Returns:
            DiscoveredItem or None if creation fails
        """
        try:
            # Extract file path (this would come from Plex item data)
            file_path = item.get("file_path", "")
            if not file_path:
                return None
            
            # Create Plex URI
            rating_key = item.get("ratingKey", "")
            path_uri = f"plex://{rating_key}" if rating_key else f"file://{file_path}"
            
            # Extract metadata
            raw_labels = []
            
            if self.include_metadata:
                # Add title
                if "title" in item:
                    raw_labels.append(f"title:{item['title']}")
                
                # Add year
                if "year" in item:
                    raw_labels.append(f"year:{item['year']}")
                
                # Add genre
                if "genre" in item:
                    raw_labels.append(f"genre:{item['genre']}")
                
                # Add library type
                if "type" in library:
                    raw_labels.append(f"library_type:{library['type']}")
            
            # Get last modified time
            last_modified = None
            if "updatedAt" in item:
                try:
                    # Convert Plex timestamp to datetime
                    timestamp = int(item["updatedAt"])
                    last_modified = datetime.fromtimestamp(timestamp)
                except (ValueError, TypeError):
                    pass
            
            # Get file size
            size = item.get("fileSize")
            if size is not None:
                try:
                    size = int(size)
                except (ValueError, TypeError):
                    size = None
            
            return DiscoveredItem(
                path_uri=path_uri,
                provider_key=rating_key,
                raw_labels=raw_labels if raw_labels else None,
                last_modified=last_modified,
                size=size,
                hash_sha256=None  # Plex doesn't provide file hashes
            )
            
        except Exception as e:
            logger.warning(f"Failed to create discovered item: {e}")
            return None


# Note: PlexImporter requires server configuration, so it should be registered
# manually with proper server configuration when needed
