"""
Plex content source implementation.
"""

from typing import List, Dict, Any, Generator
from ..base import BaseContentSource, ContentSourceCapabilities, ContentItem, ContentSourceConfig
from ..exceptions import ContentSourceConnectionError, ContentSourceValidationError
from .client import PlexClient
from .db import Db
from .ingest import IngestOrchestrator


class PlexContentSource(BaseContentSource):
    """Plex Media Server content source."""
    
    def __init__(self):
        self.db = Db("./retrovue.db")
    
    @property
    def name(self) -> str:
        return "Plex Media Server"
    
    @property
    def source_type(self) -> str:
        return "plex"
    
    @property
    def capabilities(self) -> List[ContentSourceCapabilities]:
        return [
            ContentSourceCapabilities.SUPPORTS_SERVERS,
            ContentSourceCapabilities.SUPPORTS_LIBRARIES,
            ContentSourceCapabilities.SUPPORTS_METADATA,
            ContentSourceCapabilities.REQUIRES_PATH_MAPPING
        ]
    
    def create_config_dialog(self, parent=None, config=None):
        """Create configuration dialog for Plex content source."""
        from .config_dialog import PlexConfigDialog
        return PlexConfigDialog(parent, config)
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, str]:
        """Validate Plex configuration."""
        required_fields = ['name', 'url', 'token']
        for field in required_fields:
            if not config.get(field):
                return False, f"Missing required field: {field}"
        
        # Validate URL format
        url = config.get('url', '')
        if not url.startswith(('http://', 'https://')):
            return False, "URL must start with http:// or https://"
        
        return True, ""
    
    def test_connection(self, config: Dict[str, Any]) -> tuple[bool, str]:
        """Test connection to Plex server."""
        try:
            url = config.get('url')
            token = config.get('token')
            
            if not url or not token:
                return False, "Missing URL or token"
            
            client = PlexClient(url, token)
            if client.test_connection():
                return True, "Connection successful"
            else:
                return False, "Connection failed"
        except Exception as e:
            return False, f"Connection error: {e}"
    
    def discover_libraries(self, config: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Discover available libraries from Plex server."""
        try:
            url = config.get('url')
            token = config.get('token')
            
            if not url or not token:
                raise ContentSourceConnectionError("Missing URL or token")
            
            client = PlexClient(url, token)
            libraries = client.get_libraries()
            
            for library in libraries:
                yield {
                    "id": library.key,
                    "name": library.title,
                    "type": library.type,
                    "agent": library.agent,
                    "scanner": library.scanner
                }
                
        except Exception as e:
            raise ContentSourceConnectionError(f"Failed to discover libraries: {e}")
    
    def sync_content(
        self,
        config: Dict[str, Any],
        library_id: str,
        **kwargs
    ) -> Generator[Dict[str, Any], None, None]:
        """Import content from Plex server."""
        try:
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
                server=config,
                library_key=library_id,
                **kwargs
            )
            
        except Exception as e:
            raise ContentSourceConnectionError(f"Failed to sync content: {e}")
    
    def validate_content(self, content_item: ContentItem) -> bool:
        """Validate that content is accessible and playable."""
        try:
            # Use existing validation logic
            from .validation import ContentValidator
            from .pathmap import PathMapper
            
            path_mapper = PathMapper(self.db.conn)
            validator = ContentValidator(path_mapper)
            
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
