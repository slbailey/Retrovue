"""
Plex Media Server importer implementation.
"""

from typing import List, Dict, Any, Generator
from ..base import BaseImporter, ImporterCapabilities, ContentItem
from .client import PlexClient
from .ingest import IngestOrchestrator
from .db import Db
from ..exceptions import ImporterConnectionError, ImporterValidationError


class PlexImporter(BaseImporter):
    """Plex Media Server importer."""
    
    def __init__(self):
        self.db = Db("./retrovue.db")
    
    @property
    def name(self) -> str:
        return "Plex Media Server"
    
    @property
    def source_id(self) -> str:
        return "plex"
    
    @property
    def capabilities(self) -> List[ImporterCapabilities]:
        return [
            ImporterCapabilities.SUPPORTS_SERVERS,
            ImporterCapabilities.SUPPORTS_LIBRARIES,
            ImporterCapabilities.SUPPORTS_METADATA,
            ImporterCapabilities.REQUIRES_PATH_MAPPING
        ]
    
    def discover_libraries(self, server_id: int) -> Generator[Dict[str, Any], None, None]:
        """Discover available libraries from Plex server."""
        try:
            # Get server info
            server = self.db.get_server(server_id)
            if not server:
                raise ImporterConnectionError(f"Server {server_id} not found")
            
            # Create Plex client
            plex_client = PlexClient(server['base_url'], server['token'])
            
            # Discover libraries
            for library in plex_client.get_libraries():
                yield {
                    "id": library['key'],
                    "name": library['title'],
                    "kind": library['type'],
                    "server_id": server_id,
                    "source": "plex"
                }
                
        except Exception as e:
            raise ImporterConnectionError(f"Failed to discover libraries: {e}")
    
    def sync_content(
        self,
        server_id: int,
        library_id: int,
        **kwargs
    ) -> Generator[Dict[str, Any], None, None]:
        """Import content from Plex server."""
        try:
            # Get server info
            server = self.db.get_server(server_id)
            if not server:
                raise ImporterConnectionError(f"Server {server_id} not found")
            
            # Create ingest orchestrator with required dependencies
            from .pathmap import PathMapper
            from .validation import ContentValidator
            from .error_handling import ErrorHandler
            
            path_mapper = PathMapper(self.db.conn)
            validator = ContentValidator(path_mapper)
            error_handler = ErrorHandler()
            
            ingest_orchestrator = IngestOrchestrator(
                db=self.db,
                plex_client=None,  # Will be created internally
                path_mapper=path_mapper,
                validator=validator,
                error_handler=error_handler
            )
            
            # Use the ingest orchestrator
            yield from ingest_orchestrator.ingest_library_stream(
                server=server,
                library_key=library_id,
                **kwargs
            )
            
        except Exception as e:
            raise ImporterConnectionError(f"Failed to sync content: {e}")
    
    def validate_content(self, content_item: ContentItem) -> bool:
        """Validate that content is accessible and playable."""
        try:
            # Use existing validation logic
            from .validation import MediaValidator
            validator = MediaValidator()
            
            # For now, just check if file exists and is readable
            import os
            if not os.path.exists(content_item.file_path):
                return False
            
            # Try to read first few bytes
            with open(content_item.file_path, 'rb') as f:
                f.read(1024)
            
            return True
            
        except Exception:
            return False
