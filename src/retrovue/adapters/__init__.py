"""
Adapters module for Retrovue.

This module contains adapters for external systems and services,
including importers, enrichers, and their registry.
"""

from .registry import (
    register_importer,
    get_importer,
    list_importers,
    unregister_importer,
    register_enricher,
    get_enricher,
    list_enrichers,
    unregister_enricher,
    clear_registries,
    get_registry_stats,
)

__all__ = [
    "register_importer",
    "get_importer", 
    "list_importers",
    "unregister_importer",
    "register_enricher",
    "get_enricher",
    "list_enrichers",
    "unregister_enricher",
    "clear_registries",
    "get_registry_stats",
]