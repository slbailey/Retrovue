"""
Library management logic - reusable across GUI and CLI.
"""

from typing import List, Dict, Any, Optional, Generator
from pathlib import Path


class LibraryManager:
    """
    Manages Plex library discovery and sync configuration.
    
    This is a thin facade over the database and Plex client layers.
    """
    
    def __init__(self, db_path: str = "./retrovue.db"):
        """
        Initialize library manager.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = str(Path(db_path).resolve())
    
    def _get_db(self):
        """Get database instance. Import lazily to avoid circular deps."""
        from retrovue.importers.plex.db import Db
        return Db(self.db_path)
    
    def list_libraries(self, server_id: int) -> List[Dict[str, Any]]:
        """
        List all libraries for a server.
        
        Args:
            server_id: Server ID
            
        Returns:
            List of library dictionaries with keys: id, server_id, plex_library_key,
            title, library_type, sync_enabled, last_full_sync_epoch, plex_path, etc.
        """
        with self._get_db() as db:
            return db.list_libraries(server_id)
    
    def discover_libraries(
        self, 
        server_id: int, 
        enable_all: bool = False
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Discover libraries from Plex server and save to database.
        
        This is a generator that yields progress updates:
        {"stage": "connect", "msg": "Connecting to server..."}
        {"stage": "fetch", "msg": "Fetching libraries..."}
        {"stage": "save", "msg": "Saving library: Movie Library", "library": {...}}
        {"stage": "complete", "msg": "Discovered 3 libraries", "count": 3}
        
        Args:
            server_id: Server ID
            enable_all: If True, enable sync for all discovered libraries
            
        Yields:
            Progress dictionaries
            
        Raises:
            ValueError: If server not found
            Exception: On network or database errors
        """
        # Import here to avoid pulling in requests at module level
        from retrovue.importers.plex.client import PlexClient
        
        # Get server credentials
        with self._get_db() as db:
            server = db.get_plex_server_by_id(server_id)
            
            if not server:
                raise ValueError(f"Server ID {server_id} not found")
        
        # Connect to Plex
        yield {"stage": "connect", "msg": f"Connecting to {server['name']}..."}
        
        client = PlexClient(server['base_url'], server['token'])
        
        # Fetch libraries
        yield {"stage": "fetch", "msg": "Fetching libraries from Plex..."}
        
        plex_libraries = client.get_libraries()
        
        if not plex_libraries:
            yield {"stage": "complete", "msg": "No libraries found", "count": 0}
            return
        
        # Save each library to database
        inserted = 0
        updated = 0
        returned_keys = []
        
        with self._get_db() as db:
            for plex_lib in plex_libraries:
                # Use section type (movie/show) instead of item kind
                library_type = plex_lib.type
                if library_type not in ['movie', 'show']:
                    library_type = 'movie'  # Default fallback
                
                # Extract library path from location data
                plex_path = None
                if plex_lib.location and len(plex_lib.location) > 0:
                    plex_path = plex_lib.location[0].get('path', '')
                
                # Check if library already exists
                existing = db.get_library_by_key(server_id, int(plex_lib.key))
                
                # Upsert library
                library_id = db.upsert_library(
                    server_id,
                    int(plex_lib.key),
                    plex_lib.title,
                    library_type,
                    plex_path
                )
                
                if existing:
                    updated += 1
                    action = "updated"
                else:
                    inserted += 1
                    action = "discovered"
                
                returned_keys.append(int(plex_lib.key))
                
                yield {
                    "stage": "save",
                    "msg": f"{action.capitalize()}: {plex_lib.title} ({library_type})",
                    "library": {
                        "id": library_id,
                        "key": plex_lib.key,
                        "title": plex_lib.title,
                        "type": library_type,
                        "path": plex_path
                    }
                }
            
            # Handle bulk enable/disable if requested
            if enable_all and returned_keys:
                placeholders = ','.join(['?' for _ in returned_keys])
                db.execute(f"""
                    UPDATE libraries 
                    SET sync_enabled = 1, updated_at = datetime('now')
                    WHERE server_id = ? AND plex_library_key IN ({placeholders})
                """, [server_id] + returned_keys)
                db.commit()
                
                yield {"stage": "sync", "msg": f"Enabled sync for all {len(returned_keys)} libraries"}
        
        total = len(plex_libraries)
        unchanged = total - (inserted + updated)
        
        yield {
            "stage": "complete",
            "msg": f"Discovered {total} libraries ({inserted} new, {updated} updated, {unchanged} unchanged)",
            "count": total,
            "inserted": inserted,
            "updated": updated
        }
    
    def toggle_sync(self, library_id: int, enabled: bool) -> bool:
        """
        Enable or disable sync for a library.
        
        Args:
            library_id: Library ID
            enabled: True to enable, False to disable
            
        Returns:
            True if updated, False if not found
        """
        with self._get_db() as db:
            rows_updated = db.set_library_sync(library_id, enabled)
            return rows_updated > 0
    
    def get_library(self, library_id: int) -> Optional[Dict[str, Any]]:
        """
        Get library by ID.
        
        Args:
            library_id: Library ID
            
        Returns:
            Library dictionary or None if not found
        """
        with self._get_db() as db:
            return db.get_library(library_id)
    
    def delete_library(self, library_id: int) -> bool:
        """
        Delete a library.
        
        Args:
            library_id: Library ID
            
        Returns:
            True if deleted, False if not found
        """
        with self._get_db() as db:
            rows_deleted = db.delete_library(library_id)
            return rows_deleted > 0

