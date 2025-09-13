# import_worker.py
from PySide6.QtCore import QThread, Signal
from typing import Callable, Dict, Any
from retrovue.core.database import RetrovueDatabase

class ImportWorker(QThread):
    # Legacy signals for backward compatibility (kept for legacy mode)
    library_progress = Signal(int, int, str)  # current, total, library_name
    item_progress = Signal(int, int, str)     # current, total, item_name
    status = Signal(str)
    finished = Signal()
    error = Signal(str)
    
    def __init__(self, db_path: str, ui_bus, mode: str, server_id: int|None=None,
                 library_ref=None, deep: bool=False, dry_run: bool=False,
                 sync_api=None):
        super().__init__()
        self.db_path = db_path
        self.ui_bus = ui_bus
        self.mode = mode
        self.server_id = server_id
        self.library_ref = library_ref
        self.deep = deep
        self.dry_run = dry_run
        self.sync_api = sync_api   # module with your wrapper funcs
        self.db = None  # Will be created in the worker thread

    def _progress(self, event: str, payload: Dict[str, Any]):
        # Emit only through UiBus (single signal path)
        if event == "library_start":
            self.ui_bus.sync_started.emit(payload["server_id"], payload["library_id"])
        elif event == "page_progress":
            p = payload
            self.ui_bus.page_progress.emit(
                p["server_id"], p["library_id"], p["processed"], p["changed"], p["skipped"], p["errors"]
            )
        elif event == "library_done":
            self.ui_bus.sync_completed.emit(payload["server_id"], payload["library_id"], payload["summary"])

    def run(self):
        try:
            # Create database connection in the worker thread
            self.db = RetrovueDatabase(self.db_path)
            
            # Calls your wrappers: sync_selected_across_all_servers / sync_selected_on_server / sync_one_library
            if self.mode == "all_selected":
                self.sync_api.sync_selected_across_all_servers(self.db, deep=self.deep, dry_run=self.dry_run, progress=self._progress)
            elif self.mode == "server_selected":
                self.sync_api.sync_selected_on_server(self.db, server_id=self.server_id, deep=self.deep, dry_run=self.dry_run, progress=self._progress)
            elif self.mode == "one":
                self.sync_api.sync_one_library(self.db, self.library_ref, deep=self.deep, dry_run=self.dry_run, progress=self._progress)
            elif self.mode == "legacy":
                # Legacy mode for backward compatibility
                self._run_legacy_mode()
            else:
                self.error.emit(f"Unknown mode: {self.mode}")
                return
            
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(f"Sync failed: {str(e)}")
        finally:
            # Ensure database connection is closed
            if self.db:
                self.db.close()
                self.db = None
    
    def _run_legacy_mode(self):
        """Legacy mode that mimics the old ImportWorker behavior"""
        try:
            # Get server info
            server = self.db.get_server(self.server_id)
            if not server:
                self.error.emit(f"Server {self.server_id} not found")
                return
            
            self.status.emit(f"Starting sync from server: {server['name']}")
            
            # Import all libraries for this server
            libraries = self.db.get_libraries_for_server(self.server_id)
            total_libraries = len(libraries)
            
            for i, library in enumerate(libraries):
                library_id = library['id']
                library_name = library['name']
                
                self.library_progress.emit(i + 1, total_libraries, library_name)
                self.status.emit(f"Syncing library: {library_name}")
                
                try:
                    # Use the new sync system for individual library
                    self.sync_api.sync_one_library(self.db, library, deep=self.deep, dry_run=self.dry_run, progress=self._progress)
                    
                except Exception as e:
                    self.error.emit(f"Failed to sync library {library_name}: {str(e)}")
                    continue
            
            self.status.emit("Sync completed successfully")
            
        except Exception as e:
            self.error.emit(f"Sync failed: {str(e)}")
