"""
Retrovue Core Package

This is the main package for the Retrovue IPTV simulation system. It provides
a comprehensive framework for building professional IPTV broadcasting solutions
with content management, scheduling, and streaming capabilities.

Package Structure:
- core: Core functionality including database, Plex integration, and streaming
- ui: PySide6-based desktop user interface
- version: Version information and package metadata

Key Components:
- RetrovueDatabase: SQLite database management for content and metadata
- PlexImporter: Import and sync content from Plex Media Server
- TMMImporter: Import content from TinyMediaManager .nfo files
- RetrovueMainWindow: Main desktop application interface

Usage:
    from retrovue import RetrovueDatabase, PlexImporter
    
    # Initialize database
    db = RetrovueDatabase("retrovue.db")
    
    # Create Plex importer
    importer = PlexImporter(server_url, token, db)
    
    # Import content
    importer.sync_all_libraries()

The package is designed to be modular and extensible, allowing for easy
integration of new content sources and streaming strategies.
"""

from .version import __version__

# Import core components
from .core import (
    RetrovueDatabase,
    PlexImporter,
    create_plex_importer,
    TMMImporter,
    create_tmm_importer
)

# Import UI components
from .ui import RetrovueMainWindow

__all__ = [
    "__version__",
    "RetrovueDatabase",
    "PlexImporter", 
    "create_plex_importer",
    "TMMImporter",
    "create_tmm_importer",
    "RetrovueMainWindow"
]
