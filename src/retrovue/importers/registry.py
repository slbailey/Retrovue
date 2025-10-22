"""
Registry for all available importers.
"""

from typing import Dict, Type, List
from .base import BaseImporter
from .exceptions import ImporterNotFoundError


class ImporterRegistry:
    """Registry for all available importers."""
    
    def __init__(self):
        self._importers: Dict[str, Type[BaseImporter]] = {}
        self._register_default_importers()
    
    def _register_default_importers(self):
        """Register built-in importers."""
        # Import here to avoid circular imports
        try:
            from .plex.importer import PlexImporter
            self.register(PlexImporter)
        except ImportError:
            # Plex importer not yet available
            pass
        
        try:
            from .filesystem.importer import FilesystemImporter
            self.register(FilesystemImporter)
        except ImportError:
            # Filesystem importer not yet available
            pass
    
    def register(self, importer_class: Type[BaseImporter]):
        """Register a new importer."""
        instance = importer_class()
        self._importers[instance.source_id] = importer_class
    
    def get_importer(self, source_id: str) -> BaseImporter:
        """Get importer instance by source ID."""
        if source_id not in self._importers:
            raise ImporterNotFoundError(f"Unknown importer: {source_id}")
        return self._importers[source_id]()
    
    def list_importers(self) -> List[BaseImporter]:
        """List all available importers."""
        return [cls() for cls in self._importers.values()]
    
    def get_importer_by_capability(self, capability) -> List[BaseImporter]:
        """Get importers that support a specific capability."""
        return [
            importer for importer in self.list_importers()
            if capability in importer.capabilities
        ]
    
    def is_importer_available(self, source_id: str) -> bool:
        """Check if an importer is available."""
        return source_id in self._importers


# Global registry instance
registry = ImporterRegistry()
