"""
Unified API façade for Retrovue core functionality.

This module provides a clean, consistent interface for both GUI and CLI
to interact with Plex servers, libraries, and content synchronization.
"""

from typing import List, Dict, Any, Optional, Generator
from .servers import ServerManager
from .libraries import LibraryManager
from .sync import SyncManager


class RetrovueAPI:
    """
    Main API façade that coordinates between GUI/CLI and core business logic.
    
    This class provides a single entry point for all Retrovue operations,
    ensuring consistent behavior across different interfaces.
    """
    
    def __init__(self):
        """Initialize the API with core managers."""
        self._server_manager = ServerManager()
        self._library_manager = LibraryManager()
        self._sync_manager = SyncManager()
    
    # ========================================================================
    # Server Management
    # ========================================================================
    
    def add_server(self, name: str, url: str, token: str) -> int:
        """
        Add a new Plex server.
        
        Args:
            name: Friendly name for the server
            url: Server URL (e.g., http://localhost:32400)
            token: Plex authentication token
            
        Returns:
            Server ID of the newly created server
            
        Raises:
            Exception: If server cannot be added
        """
        return self._server_manager.add_server(name, url, token)
    
    def list_servers(self) -> List[Dict[str, Any]]:
        """
        List all configured Plex servers.
        
        Returns:
            List of server dictionaries with keys: id, name, url, token, created_at
        """
        return self._server_manager.list_servers()
    
    def get_server(self, server_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific server by ID.
        
        Args:
            server_id: Server ID
            
        Returns:
            Server dictionary or None if not found
        """
        return self._server_manager.get_server(server_id)
    
    def delete_server(self, server_id: int) -> bool:
        """
        Delete a Plex server.
        
        Args:
            server_id: Server ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        return self._server_manager.delete_server(server_id)
    
    # ========================================================================
    # Library Management
    # ========================================================================
    
    def discover_libraries(self, server_id: int) -> Generator[Dict[str, Any], None, None]:
        """
        Discover libraries on a Plex server (async generator).
        
        This is a long-running operation that yields progress updates.
        Should be run in a background thread to avoid blocking the UI.
        
        Args:
            server_id: Server ID to discover libraries from
            
        Yields:
            Progress dictionaries with keys like: stage, msg, library, etc.
            
        Example:
            for progress in api.discover_libraries(server_id):
                print(progress['msg'])
        """
        yield from self._library_manager.discover_libraries(server_id)
    
    def list_libraries(self, server_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all discovered libraries, optionally filtered by server.
        
        Args:
            server_id: Optional server ID to filter by
            
        Returns:
            List of library dictionaries with keys: id, server_id, name, 
            plex_library_key, section_type, sync_enabled, discovered_at
        """
        return self._library_manager.list_libraries(server_id)
    
    def get_library(self, library_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific library by ID.
        
        Args:
            library_id: Library ID
            
        Returns:
            Library dictionary or None if not found
        """
        return self._library_manager.get_library(library_id)
    
    def toggle_library_sync(self, library_id: int, enabled: bool) -> bool:
        """
        Enable or disable sync for a library.
        
        Args:
            library_id: Library ID
            enabled: True to enable sync, False to disable
            
        Returns:
            True if updated successfully, False otherwise
        """
        return self._library_manager.toggle_sync(library_id, enabled)
    
    # ========================================================================
    # Path Mapping Management
    # ========================================================================
    
    def list_path_mappings(
        self, 
        server_id: int, 
        library_id: int
    ) -> List[Dict[str, Any]]:
        """
        List path mappings for a server and library.
        
        Args:
            server_id: Server ID
            library_id: Library ID
            
        Returns:
            List of mapping dictionaries with keys: id, plex_path, local_path
        """
        return self._sync_manager.list_path_mappings(server_id, library_id)
    
    def add_path_mapping(
        self, 
        server_id: int, 
        library_id: int, 
        plex_path: str, 
        local_path: str
    ) -> int:
        """
        Add a new path mapping.
        
        Args:
            server_id: Server ID
            library_id: Library ID
            plex_path: Path as seen on Plex server (e.g., /mnt/media)
            local_path: Local file system path (e.g., D:\\Movies)
            
        Returns:
            Mapping ID of the newly created mapping
        """
        return self._sync_manager.add_path_mapping(server_id, library_id, plex_path, local_path)
    
    def delete_path_mapping(self, mapping_id: int) -> bool:
        """
        Delete a path mapping.
        
        Args:
            mapping_id: Mapping ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        return self._sync_manager.delete_path_mapping(mapping_id)
    
    # ========================================================================
    # Content Synchronization
    # ========================================================================
    
    def sync_content(
        self,
        server_id: int,
        library_keys: List[int],
        kinds: List[str],
        limit: Optional[int] = None,
        dry_run: bool = True
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Synchronize content from Plex to local database (async generator).
        
        This is a long-running operation that yields progress updates.
        Should be run in a background thread to avoid blocking the UI.
        
        Args:
            server_id: Server ID to sync from
            library_keys: List of Plex library keys to sync
            kinds: List of content types (e.g., ['movie', 'episode'])
            limit: Optional limit on number of items to process
            dry_run: If True, preview changes without writing to DB
            
        Yields:
            Progress dictionaries with keys like: stage, msg, stats, etc.
            
        Example:
            for progress in api.sync_content(server_id, [1], ['movie'], dry_run=True):
                print(progress['msg'])
        """
        yield from self._sync_manager.run_sync(
            server_id, 
            library_keys, 
            kinds, 
            limit, 
            dry_run
        )


# Singleton instance for convenience
_api_instance: Optional[RetrovueAPI] = None


def get_api() -> RetrovueAPI:
    """
    Get the singleton API instance.
    
    Returns:
        Shared RetrovueAPI instance
        
    Example:
        from retrovue.core.api import get_api
        
        api = get_api()
        servers = api.list_servers()
    """
    global _api_instance
    if _api_instance is None:
        _api_instance = RetrovueAPI()
    return _api_instance
