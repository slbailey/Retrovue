"""
Metadata reader for filesystem files.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from ..base import ContentItem


class MetadataReader:
    """Read metadata from files and NFO files."""
    
    def read_metadata(self, file_path: str) -> ContentItem:
        """Read metadata for a file."""
        path = Path(file_path)
        
        # Try to read NFO file first
        nfo_path = path.with_suffix('.nfo')
        metadata = {}
        if nfo_path.exists():
            metadata = self._read_nfo_file(nfo_path)
        
        # Extract from filename if no NFO
        if not metadata:
            metadata = self._extract_from_filename(path.name)
        
        # Determine content type
        kind = self._determine_content_type(path, metadata)
        
        return ContentItem(
            title=metadata.get('title', path.stem),
            kind=kind,
            file_path=str(path),
            source='filesystem',
            source_id=f"fs_{path.name}",
            metadata=metadata
        )
    
    def _read_nfo_file(self, nfo_path: Path) -> Dict[str, Any]:
        """Read NFO file (XML format)."""
        # TODO: Implement NFO parsing in Phase 2
        return {}
    
    def _extract_from_filename(self, filename: str) -> Dict[str, Any]:
        """Extract metadata from filename patterns."""
        # TODO: Implement filename parsing in Phase 2
        # Handle patterns like "Movie (2023).mkv", "Show S01E01.mkv"
        return {"title": Path(filename).stem}
    
    def _determine_content_type(self, path: Path, metadata: Dict[str, Any]) -> str:
        """Determine if this is a movie, episode, etc."""
        # TODO: Implement content type detection in Phase 2
        # For now, default to movie
        return "movie"
