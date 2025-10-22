"""
Filesystem importer implementation.
"""

from typing import List, Dict, Any, Generator
from pathlib import Path
from ..base import BaseImporter, ImporterCapabilities, ContentItem
from .scanner import FilesystemScanner
from .metadata_reader import MetadataReader
from .validator import FileValidator


class FilesystemImporter(BaseImporter):
    """Filesystem importer for direct file system scanning."""
    
    def __init__(self):
        self.scanner = FilesystemScanner()
        self.metadata_reader = MetadataReader()
        self.validator = FileValidator()
    
    @property
    def name(self) -> str:
        return "Filesystem Scanner"
    
    @property
    def source_id(self) -> str:
        return "filesystem"
    
    @property
    def capabilities(self) -> List[ImporterCapabilities]:
        return [
            ImporterCapabilities.SUPPORTS_METADATA,
            # No servers, no libraries, no path mapping needed
        ]
    
    def discover_libraries(self, server_id: int) -> Generator[Dict[str, Any], None, None]:
        """For filesystem, 'libraries' are just directory paths."""
        # This would return configured scan directories as "libraries"
        # For now, return empty - this will be implemented in Phase 2
        return
        yield  # This line will never be reached, but satisfies the generator requirement
    
    def sync_content(
        self,
        server_id: int,
        library_id: int,
        **kwargs
    ) -> Generator[Dict[str, Any], None, None]:
        """Scan filesystem and import content."""
        # This will be implemented in Phase 2
        yield {
            "stage": "info",
            "msg": "Filesystem importer not yet implemented",
            "stats": {"scanned": 0, "inserted_items": 0, "errors": 0}
        }
    
    def validate_content(self, content_item: ContentItem) -> bool:
        """Validate that content is accessible and playable."""
        return self.validator.validate_file(content_item.file_path)["valid"]
