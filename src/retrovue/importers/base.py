"""
Abstract base classes for all content importers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, Optional
from dataclasses import dataclass
from enum import Enum


class ImporterCapabilities(Enum):
    """Capabilities that importers can support."""
    SUPPORTS_SERVERS = "supports_servers"      # Has server concept (Plex/Jellyfin)
    SUPPORTS_LIBRARIES = "supports_libraries"  # Has library concept
    SUPPORTS_METADATA = "supports_metadata"    # Imports metadata
    SUPPORTS_STREAMING = "supports_streaming"  # Can stream content
    REQUIRES_PATH_MAPPING = "requires_path_mapping"  # Needs path translation


@dataclass
class ContentItem:
    """Standardized content item across all importers."""
    title: str
    kind: str  # 'movie', 'episode', 'season', 'show'
    file_path: str
    duration_ms: Optional[int] = None
    source: str = ""  # Importer source ID
    source_id: str = ""  # External ID
    metadata: Dict[str, Any] = None


class BaseImporter(ABC):
    """Abstract base class for all content importers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name (e.g., 'Plex Media Server')."""
        pass
    
    @property
    @abstractmethod
    def source_id(self) -> str:
        """Unique identifier (e.g., 'plex', 'filesystem', 'jellyfin')."""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[ImporterCapabilities]:
        """What features this importer supports."""
        pass
    
    @abstractmethod
    def discover_libraries(self, server_id: int) -> Generator[Dict[str, Any], None, None]:
        """Discover available libraries/collections."""
        pass
    
    @abstractmethod
    def sync_content(
        self,
        server_id: int,
        library_id: int,
        **kwargs
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Import content from this source.
        Yields progress updates.
        """
        pass
    
    @abstractmethod
    def validate_content(self, content_item: ContentItem) -> bool:
        """Validate that content is accessible and playable."""
        pass
