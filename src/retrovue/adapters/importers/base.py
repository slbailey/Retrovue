"""
Base protocols for content importers.

This module defines the core interfaces that all importers must implement.
Importers are responsible for discovering content from various sources (Plex, filesystem, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass
class DiscoveredItem:
    """
    Represents a discovered content item from an importer.
    
    This is the standard format that all importers return when discovering content.
    It contains the essential information needed to register an asset in the system.
    """
    
    path_uri: str
    """URI path to the content (e.g., 'file:///path/to/video.mkv', 'plex://server/library/item')"""
    
    provider_key: str | None = None
    """Provider-specific identifier (e.g., Plex rating key, TMDB ID)"""
    
    raw_labels: list[str] | None = None
    """Raw metadata labels extracted from the source"""
    
    last_modified: datetime | None = None
    """Last modification timestamp of the content"""
    
    size: int | None = None
    """File size in bytes"""
    
    hash_sha256: str | None = None
    """SHA-256 hash of the content"""
    
    def __post_init__(self):
        """Validate the discovered item after initialization."""
        if not self.path_uri:
            raise ValueError("path_uri is required")
        
        if self.size is not None and self.size < 0:
            raise ValueError("size must be non-negative")


class Importer(Protocol):
    """
    Protocol for content importers.
    
    Importers are responsible for discovering content from various sources.
    They should be stateless and operate on simple data structures.
    """
    
    name: str
    """Unique name identifier for this importer"""
    
    def discover(self) -> list[DiscoveredItem]:
        """
        Discover content items from the source.
        
        Returns:
            List of discovered content items
            
        Raises:
            ImporterError: If discovery fails
        """
        ...


class ImporterError(Exception):
    """Base exception for importer-related errors."""
    pass


class ImporterNotFoundError(ImporterError):
    """Raised when a requested importer is not found in the registry."""
    pass


class ImporterConfigurationError(ImporterError):
    """Raised when an importer is not properly configured."""
    pass
