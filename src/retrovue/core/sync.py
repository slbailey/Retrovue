"""
Content sync/ingest management logic - reusable across GUI and CLI.
"""

from typing import List, Dict, Any, Optional, Generator, Tuple
from pathlib import Path


class SyncManager:
    """
    Manages content synchronization from Plex to local database.
    
    This is a thin facade over the ingest orchestrator and path mapping layers.
    """
    
    def __init__(self, db_path: str = "./retrovue.db"):
        """
        Initialize sync manager.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = str(Path(db_path).resolve())
    
    def _get_db(self):
        """Get database instance. Import lazily to avoid circular deps."""
        from retrovue.plex.db import Db
        return Db(self.db_path)
    
    def list_path_mappings(self, server_id: int, library_id: int) -> List[Dict[str, Any]]:
        """
        List path mappings for a server and library.
        
        Args:
            server_id: Server ID
            library_id: Library ID
            
        Returns:
            List of mapping dictionaries with keys: id, plex_path, local_path
        """
        with self._get_db() as db:
            return db.get_path_mappings(server_id, library_id)
    
    def add_path_mapping(
        self,
        server_id: int,
        library_id: int,
        plex_path: str,
        local_path: str
    ) -> int:
        """
        Add a path mapping.
        
        Args:
            server_id: Server ID
            library_id: Library ID
            plex_path: Plex path prefix
            local_path: Local path prefix
            
        Returns:
            Mapping ID
            
        Raises:
            ValueError: If validation fails
        """
        if not plex_path or not plex_path.strip():
            raise ValueError("Plex path cannot be empty")
        
        if not local_path or not local_path.strip():
            raise ValueError("Local path cannot be empty")
        
        with self._get_db() as db:
            mapping_id = db.insert_path_mapping(
                server_id,
                library_id,
                plex_path.strip(),
                local_path.strip()
            )
            return mapping_id
    
    def delete_path_mapping(self, mapping_id: int) -> bool:
        """
        Delete a path mapping.
        
        Args:
            mapping_id: Mapping ID
            
        Returns:
            True if deleted, False if not found
        """
        with self._get_db() as db:
            cursor = db.execute("DELETE FROM path_mappings WHERE id = ?", (mapping_id,))
            rows_deleted = cursor.rowcount
            db.commit()
            return rows_deleted > 0
    
    def run_sync(
        self,
        server_id: int,
        library_keys: List[int],
        kinds: List[str] = None,
        limit: Optional[int] = None,
        dry_run: bool = True
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Run content sync for specified libraries.
        
        This is a generator that yields progress updates:
        {"stage": "init", "msg": "Initializing sync..."}
        {"stage": "library", "msg": "Processing library 1 (movie)", "library_key": 1, "kind": "movie"}
        {"stage": "item", "msg": "Mapped: Movie Title", "item": {...}}
        {"stage": "complete", "msg": "Sync complete", "stats": {...}}
        
        Args:
            server_id: Server ID
            library_keys: List of library keys to sync
            kinds: List of content kinds to sync (default: ["movie", "episode"])
            limit: Maximum items per library
            dry_run: If True, don't write to database
            
        Yields:
            Progress dictionaries
            
        Raises:
            ValueError: If server not found or no libraries specified
            Exception: On network or database errors
        """
        # Import here to avoid pulling in requests at module level
        from retrovue.plex.client import PlexClient
        from retrovue.plex.ingest import IngestOrchestrator
        from retrovue.plex.pathmap import PathMapper
        
        if not library_keys:
            raise ValueError("No libraries specified for sync")
        
        if kinds is None:
            kinds = ["movie", "episode"]
        
        # Get server credentials
        with self._get_db() as db:
            server = db.get_plex_server_by_id(server_id)
            
            if not server:
                raise ValueError(f"Server ID {server_id} not found")
        
        yield {"stage": "init", "msg": f"Connecting to {server['name']}..."}
        
        # Create Plex client
        client = PlexClient(server['base_url'], server['token'])
        
        # Initialize stats
        total_stats = {
            "scanned": 0, "mapped": 0, "inserted_items": 0, "updated_items": 0,
            "inserted_files": 0, "updated_files": 0, "linked": 0, "skipped": 0, "errors": 0
        }
        
        # Process each library and kind combination
        with self._get_db() as db:
            path_mapper = PathMapper(db.conn)
            orchestrator = IngestOrchestrator(db, client, path_mapper)
            
            for library_key in library_keys:
                for kind in kinds:
                    yield {
                        "stage": "library",
                        "msg": f"Processing library {library_key} ({kind})",
                        "library_key": library_key,
                        "kind": kind
                    }
                    
                    try:
                        # Use streaming ingest for real-time progress updates
                        stats = {key: 0 for key in total_stats}  # Initialize stats
                        
                        for progress in orchestrator.ingest_library_stream(
                            server,
                            library_key,
                            kind,
                            mode='full',
                            limit=limit,
                            dry_run=dry_run,
                            verbose=False,
                            batch_size=50,
                            progress_interval=50  # For dry runs: update every 50 items
                        ):
                            # Forward progress from orchestrator
                            yield progress
                            
                            # Extract stats from progress (they're included in most stages)
                            if "stats" in progress:
                                stats = progress["stats"]
                        
                        # Accumulate stats from this library/kind combo
                        for key in total_stats:
                            total_stats[key] += stats.get(key, 0)
                        
                        yield {
                            "stage": "library_done",
                            "msg": f"Library {library_key} ({kind}): {stats['scanned']} scanned, {stats['mapped']} mapped, {stats['errors']} errors",
                            "library_key": library_key,
                            "kind": kind,
                            "stats": stats
                        }
                        
                    except Exception as e:
                        yield {
                            "stage": "error",
                            "msg": f"Error processing library {library_key} ({kind}): {e}",
                            "library_key": library_key,
                            "kind": kind,
                            "error": str(e)
                        }
                        total_stats["errors"] += 1
        
        # Final summary
        mode_str = "DRY RUN" if dry_run else "COMMIT"
        summary_msg = (
            f"Sync complete [{mode_str}]:\n"
            f"  Scanned: {total_stats['scanned']}\n"
            f"  Mapped: {total_stats['mapped']}\n"
            f"  Inserted: {total_stats['inserted_items']} items, {total_stats['inserted_files']} files\n"
            f"  Errors: {total_stats['errors']}"
        )
        
        if total_stats['errors'] > 0:
            summary_msg += "\n\nNote: Some files failed validation (codec issues, missing files, etc.)\nCheck console output for details."
        
        yield {
            "stage": "complete",
            "msg": summary_msg,
            "stats": total_stats,
            "dry_run": dry_run
        }

