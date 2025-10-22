"""
Registry for all available content sources.
"""

from typing import Dict, Type, List
from .base import BaseContentSource
from .exceptions import ContentSourceNotFoundError


class ContentSourceRegistry:
    """Registry for all available content sources."""
    
    def __init__(self):
        self._sources: Dict[str, Type[BaseContentSource]] = {}
        self._register_default_sources()
    
    def _register_default_sources(self):
        """Register built-in content sources."""
        # Import here to avoid circular imports
        try:
            from .plex.source import PlexContentSource
            self.register(PlexContentSource)
        except ImportError:
            # Plex content source not yet available
            pass
        
        try:
            from .filesystem.source import FilesystemContentSource
            self.register(FilesystemContentSource)
        except ImportError:
            # Filesystem content source not yet available
            pass
        
        try:
            from .jellyfin.source import JellyfinContentSource
            self.register(JellyfinContentSource)
        except ImportError:
            # Jellyfin content source not yet available
            pass
    
    def register(self, source_class: Type[BaseContentSource]):
        """Register a new content source."""
        instance = source_class()
        self._sources[instance.source_type] = source_class
    
    def get_source(self, source_type: str) -> BaseContentSource:
        """Get content source instance by type."""
        if source_type not in self._sources:
            raise ContentSourceNotFoundError(f"Unknown content source: {source_type}")
        return self._sources[source_type]()
    
    def list_sources(self) -> List[BaseContentSource]:
        """List all available content sources."""
        return [cls() for cls in self._sources.values()]
    
    def get_sources_by_capability(self, capability) -> List[BaseContentSource]:
        """Get content sources that support a specific capability."""
        return [
            source for source in self.list_sources()
            if capability in source.capabilities
        ]
    
    def is_source_available(self, source_type: str) -> bool:
        """Check if a content source is available."""
        return source_type in self._sources


# Global registry instance
registry = ContentSourceRegistry()
