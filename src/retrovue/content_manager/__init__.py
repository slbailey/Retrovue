"""
Content Manager package - unified interface for content management operations.

This package provides the public API for content management services including
library operations, source management, and content ingestion.
"""

from .library_service import LibraryService
from .source_service import SourceService, SourceCollectionDTO, ContentSourceDTO, CollectionUpdateDTO
from .ingest_orchestrator import IngestOrchestrator, IngestReport
from .path_service import PathResolverService, PathResolutionError

__all__ = [
    # Services
    "LibraryService",
    "SourceService", 
    "IngestOrchestrator",
    "PathResolverService",
    
    # DTOs
    "SourceCollectionDTO",
    "ContentSourceDTO", 
    "CollectionUpdateDTO",
    "IngestReport",
    
    # Exceptions
    "PathResolutionError",
]
