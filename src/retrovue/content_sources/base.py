"""
Base classes for content sources.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, Optional
from dataclasses import dataclass
from enum import Enum


class ContentSourceCapabilities(Enum):
    """Capabilities that content sources can support."""
    SUPPORTS_SERVERS = "supports_servers"      # Has server concept (Plex/Jellyfin)
    SUPPORTS_LIBRARIES = "supports_libraries"  # Has library concept
    SUPPORTS_METADATA = "supports_metadata"    # Imports metadata
    SUPPORTS_STREAMING = "supports_streaming"  # Can stream content
    REQUIRES_PATH_MAPPING = "requires_path_mapping"  # Needs path translation
    SUPPORTS_DIRECTORY_SCANNING = "supports_directory_scanning"  # Can scan directories


@dataclass
class ContentSourceConfig:
    """Configuration for a content source."""
    name: str
    source_type: str
    config: Dict[str, Any]
    status: str = "inactive"  # 'active', 'inactive', 'error'
    created_at: Optional[int] = None
    updated_at: Optional[int] = None


@dataclass
class ContentItem:
    """Standardized content item across all sources."""
    title: str
    kind: str  # 'movie', 'episode', 'season', 'show'
    file_path: str
    duration_ms: Optional[int] = None
    source_id: int = 0  # ID of the content source
    source_name: str = ""  # Name of the content source
    external_id: str = ""  # External ID from the source
    metadata: Dict[str, Any] = None


class BaseContentSource(ABC):
    """Abstract base class for all content sources."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name (e.g., 'Plex Media Server')."""
        pass
    
    @property
    @abstractmethod
    def source_type(self) -> str:
        """Unique identifier (e.g., 'plex', 'jellyfin', 'filesystem')."""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> List[ContentSourceCapabilities]:
        """What features this content source supports."""
        pass
    
    @abstractmethod
    def create_config_dialog(self, parent=None, config=None):
        """Create configuration dialog for this content source."""
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate configuration.
        
        Returns:
            (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def test_connection(self, config: Dict[str, Any]) -> tuple[bool, str]:
        """
        Test connection to the content source.
        
        Returns:
            (is_connected, error_message)
        """
        pass
    
    @abstractmethod
    def discover_libraries(self, config: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]:
        """Discover available libraries/collections."""
        pass
    
    @abstractmethod
    def sync_content(
        self,
        config: Dict[str, Any],
        library_id: str,
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
