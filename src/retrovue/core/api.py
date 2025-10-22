"""
Unified API façade for Retrovue core functionality.

This module provides a clean, consistent interface for both GUI and CLI
to interact with various content sources through the importer framework.
"""

from typing import List, Dict, Any, Optional, Generator
from .servers import ServerManager
from .libraries import LibraryManager
from .sync import SyncManager
from .content_sources_db import ContentSourcesDB
from ..importers.registry import registry
from ..importers.exceptions import ImporterNotFoundError


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
        self._content_sources_db = ContentSourcesDB()
        self._importers = {}  # Cache for importer instances
    
    # ========================================================================
    # Importer Management
    # ========================================================================
    
    def get_importer(self, source_id: str):
        """Get importer instance by source ID."""
        if source_id not in self._importers:
            try:
                self._importers[source_id] = registry.get_importer(source_id)
            except ImporterNotFoundError:
                raise ImporterNotFoundError(f"Importer '{source_id}' not available")
        return self._importers[source_id]
    
    def list_importers(self) -> List[Dict[str, Any]]:
        """List all available importers."""
        importers = registry.list_importers()
        return [
            {
                "source_id": importer.source_id,
                "name": importer.name,
                "capabilities": [cap.value for cap in importer.capabilities]
            }
            for importer in importers
        ]
    
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
    
    def discover_libraries(self, server_id: int, source_id: str = "plex") -> Generator[Dict[str, Any], None, None]:
        """
        Discover libraries on a server using CLI (async generator).
        
        This is a long-running operation that yields progress updates.
        Should be run in a background thread to avoid blocking the UI.
        
        Args:
            server_id: Server ID to discover libraries from
            source_id: Importer source ID (default: "plex")
            
        Yields:
            Progress dictionaries with keys like: stage, msg, library, etc.
            
        Example:
            for progress in api.discover_libraries(server_id, "plex"):
                print(progress['msg'])
        """
        import subprocess
        import sys
        from pathlib import Path
        
        # Build CLI command
        cli_path = Path(__file__).parent.parent.parent / "cli" / "plex_sync.py"
        cmd = [
            sys.executable, str(cli_path), "libraries", "sync",
            "--server-id", str(server_id),
            "--disable-all"  # Start with all libraries disabled
        ]
        
        yield {"stage": "start", "msg": f"Discovering libraries from server {server_id}..."}
        
        try:
            # Run CLI command and capture output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=Path(__file__).parent.parent.parent
            )
            
            # Stream output line by line
            for line in process.stdout:
                line = line.strip()
                if line:
                    yield {"stage": "progress", "msg": line}
            
            # Wait for completion
            return_code = process.wait()
            
            if return_code == 0:
                yield {"stage": "complete", "msg": "Library discovery completed successfully"}
            else:
                yield {"stage": "error", "msg": f"Library discovery failed with return code {return_code}"}
                
        except Exception as e:
            yield {"stage": "error", "msg": f"Error running library discovery: {e}"}
    
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
        library_id: int,
        source_id: str = "plex",
        **kwargs
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Synchronize content from a source to local database (async generator).
        
        This is a long-running operation that yields progress updates.
        Should be run in a background thread to avoid blocking the UI.
        
        Args:
            server_id: Server ID to sync from
            library_id: Library ID to sync
            source_id: Importer source ID (default: "plex")
            **kwargs: Additional arguments passed to importer
            
        Yields:
            Progress dictionaries with keys like: stage, msg, stats, etc.
            
        Example:
            for progress in api.sync_content(server_id, library_id, "plex", dry_run=True):
                print(progress['msg'])
        """
        importer = self.get_importer(source_id)
        yield from importer.sync_content(server_id, library_id, **kwargs)
    
    # ========================================================================
    # Content Sources Management
    # ========================================================================
    
    def add_content_source(self, name: str, source_type: str, config: Dict[str, Any]) -> int:
        """
        Add a new content source.
        
        Args:
            name: Friendly name for the content source
            source_type: Type of content source (e.g., 'plex', 'jellyfin', 'filesystem')
            config: Configuration dictionary specific to the source type
            
        Returns:
            Content source ID of the newly created source
            
        Raises:
            Exception: If content source cannot be added
        """
        return self._content_sources_db.add_content_source(name, source_type, config)
    
    def list_content_sources(self) -> List[Dict[str, Any]]:
        """
        List all configured content sources.
        
        Returns:
            List of content source dictionaries with keys: id, name, source_type, 
            config, status, created_at, updated_at
        """
        return self._content_sources_db.get_content_sources()
    
    def get_content_source(self, source_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific content source by ID.
        
        Args:
            source_id: Content source ID
            
        Returns:
            Content source dictionary or None if not found
        """
        return self._content_sources_db.get_content_source(source_id)
    
    def update_content_source(self, source_id: int, name: str, config: Dict[str, Any]) -> bool:
        """
        Update a content source.
        
        Args:
            source_id: Content source ID to update
            name: New name for the content source
            config: Updated configuration dictionary
            
        Returns:
            True if updated successfully, False otherwise
        """
        return self._content_sources_db.update_content_source(source_id, name, config)
    
    def delete_content_source(self, source_id: int) -> bool:
        """
        Delete a content source.
        
        Args:
            source_id: Content source ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        return self._content_sources_db.delete_content_source(source_id)
    
    def update_content_source_status(self, source_id: int, status: str) -> bool:
        """
        Update content source status.
        
        Args:
            source_id: Content source ID
            status: New status ('active', 'inactive', 'error')
            
        Returns:
            True if updated successfully, False otherwise
        """
        return self._content_sources_db.update_content_source_status(source_id, status)


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
