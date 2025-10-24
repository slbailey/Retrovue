"""
Base protocols for content enrichers.

This module defines the core interfaces that all enrichers must implement.
Enrichers are responsible for adding metadata to discovered content.
"""

from __future__ import annotations

from typing import Protocol

from ..importers.base import DiscoveredItem


class Enricher(Protocol):
    """
    Enricher. Adds structured metadata and technical meaning. Does not persist, does not mark canonical.
    
    Enrichers are responsible for adding metadata to discovered content.
    They should be stateless and operate on simple data structures.
    """
    
    name: str
    """Unique name identifier for this enricher"""
    
    def enrich(self, discovered_item: DiscoveredItem) -> DiscoveredItem:
        """
        Enrich a discovered item with additional metadata.
        
        Args:
            discovered_item: The item to enrich
            
        Returns:
            The enriched item (may be the same object or a new one)
            
        Raises:
            EnricherError: If enrichment fails
        """
        ...


class EnricherError(Exception):
    """Base exception for enricher-related errors."""
    pass


class EnricherNotFoundError(EnricherError):
    """Raised when a requested enricher is not found in the registry."""
    pass


class EnricherConfigurationError(EnricherError):
    """Raised when an enricher is not properly configured."""
    pass
