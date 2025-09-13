"""
Retrovue Core Components

This module contains the core system components for the Retrovue IPTV simulation system.
It provides the fundamental building blocks for content management, streaming, and
third-party integrations.

Core Components:

1. Streaming Components:
   - ConcatDemuxerStreamer: ErsatzTV-style streaming with seamless transitions
   - SimpleLoopStreamer: Basic looping for single-file continuous playback
   - StreamHandler: HTTP request handler for streaming endpoints
   - GracefulHTTPServer: Enhanced HTTP server with proper shutdown handling

2. Database Components:
   - RetrovueDatabase: SQLite database management with normalized schema
   - Handles media files, shows, episodes, movies, and scheduling metadata
   - Provides CRUD operations and query capabilities

3. Integration Components:
   - PlexImporter: Import and sync content from Plex Media Server
   - TMMImporter: Import content from TinyMediaManager .nfo files
   - Factory functions for easy importer creation

Architecture:
- Modular design with clear separation of concerns
- Database layer provides data persistence and management
- Streaming layer handles video processing and delivery
- Integration layer connects to external content sources

Usage:
    from retrovue.core import RetrovueDatabase, PlexImporter, SimpleLoopStreamer
    
    # Database operations
    db = RetrovueDatabase("retrovue.db")
    
    # Content import
    importer = PlexImporter(server_url, token, db)
    
    # Streaming
    streamer = SimpleLoopStreamer("video.mp4")

This module forms the foundation of the Retrovue system, providing all the
essential functionality needed for IPTV simulation and content management.
"""

from .streaming import (
    ConcatDemuxerStreamer,
    SimpleLoopStreamer,
    StreamHandler,
    GracefulHTTPServer
)

from .database import RetrovueDatabase

from .plex_integration import (
    PlexImporter,
    create_plex_importer
)

from .tmm_integration import (
    TMMImporter,
    create_tmm_importer
)

__all__ = [
    # Streaming components
    "ConcatDemuxerStreamer",
    "SimpleLoopStreamer", 
    "StreamHandler",
    "GracefulHTTPServer",
    
    # Database components
    "RetrovueDatabase",
    
    # Integration components
    "PlexImporter",
    "create_plex_importer",
    "TMMImporter",
    "create_tmm_importer"
]