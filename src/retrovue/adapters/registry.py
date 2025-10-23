"""
Plugin registry for importers and enrichers.

This module maintains global registries for all available importers and enrichers.
Plugins self-register when imported, allowing for a modular architecture.
"""

from __future__ import annotations

from typing import Any

from .enrichers.base import Enricher, EnricherNotFoundError
from .importers.base import Importer, ImporterNotFoundError
from .importers.filesystem_importer import FilesystemImporter
from .importers.plex_importer import PlexImporter

# Global registries
_importers: dict[str, Importer] = {}
_enrichers: dict[str, Enricher] = {}

# Importer aliases for better user experience
ALIASES = {
    "fs": "filesystem",
    "filesystem": "filesystem",
    "plex": "plex",
    "plexapi": "plex",
}

# Available importer classes
SOURCES = {
    "filesystem": FilesystemImporter,
    "fs": FilesystemImporter,    # alias
    "plex": PlexImporter,
}


class UnsupportedSource(ValueError):
    """Raised when an unsupported source is requested."""
    pass


def register_importer(importer: Importer) -> None:
    """
    Register an importer with the global registry.
    
    Args:
        importer: The importer to register
        
    Raises:
        ValueError: If importer name is empty or already registered
    """
    if not importer.name:
        raise ValueError("Importer name cannot be empty")
    
    if importer.name in _importers:
        raise ValueError(f"Importer '{importer.name}' is already registered")
    
    _importers[importer.name] = importer


def get_importer(name: str, **kwargs) -> Importer:
    """
    Get an importer by name.
    
    Args:
        name: The name of the importer
        **kwargs: Additional arguments to pass to the importer constructor
        
    Returns:
        The requested importer instance
        
    Raises:
        UnsupportedSource: If the importer is not found
    """
    key = ALIASES.get(name.lower(), name.lower())
    try:
        cls = SOURCES[key]
    except KeyError:
        raise UnsupportedSource(f"Unsupported source: {name}. "
                                f"Available: {', '.join(sorted(SOURCES.keys()))}")
    return cls(**kwargs)


def list_importers() -> list[str]:
    """
    List all available importer names.
    
    Returns:
        List of all available importer names
    """
    return list(SOURCES.keys())


def unregister_importer(name: str) -> None:
    """
    Unregister an importer.
    
    Args:
        name: The name of the importer to unregister
        
    Raises:
        ImporterNotFoundError: If the importer is not found
    """
    if name not in _importers:
        raise ImporterNotFoundError(f"Importer '{name}' not found")
    
    del _importers[name]


def register_enricher(enricher: Enricher) -> None:
    """
    Register an enricher with the global registry.
    
    Args:
        enricher: The enricher to register
        
    Raises:
        ValueError: If enricher name is empty or already registered
    """
    if not enricher.name:
        raise ValueError("Enricher name cannot be empty")
    
    if enricher.name in _enrichers:
        raise ValueError(f"Enricher '{enricher.name}' is already registered")
    
    _enrichers[enricher.name] = enricher


def get_enricher(name: str) -> Enricher:
    """
    Get an enricher by name.
    
    Args:
        name: The name of the enricher
        
    Returns:
        The requested enricher
        
    Raises:
        EnricherNotFoundError: If the enricher is not found
    """
    if name not in _enrichers:
        raise EnricherNotFoundError(f"Enricher '{name}' not found")
    
    return _enrichers[name]


def list_enrichers() -> list[Enricher]:
    """
    List all registered enrichers.
    
    Returns:
        List of all registered enrichers
    """
    return list(_enrichers.values())


def unregister_enricher(name: str) -> None:
    """
    Unregister an enricher.
    
    Args:
        name: The name of the enricher to unregister
        
    Raises:
        EnricherNotFoundError: If the enricher is not found
    """
    if name not in _enrichers:
        raise EnricherNotFoundError(f"Enricher '{name}' not found")
    
    del _enrichers[name]


def clear_registries() -> None:
    """
    Clear all registered importers and enrichers.
    
    This is primarily useful for testing.
    """
    global _importers, _enrichers
    _importers.clear()
    _enrichers.clear()


def get_registry_stats() -> dict[str, Any]:
    """
    Get statistics about the registry.
    
    Returns:
        Dictionary with registry statistics
    """
    return {
        "importers": {
            "count": len(_importers),
            "names": list(_importers.keys())
        },
        "enrichers": {
            "count": len(_enrichers),
            "names": list(_enrichers.keys())
        }
    }