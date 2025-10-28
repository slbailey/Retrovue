"""
AssetDraft domain model.

Represents a media item during the ingest process before it becomes a CatalogAsset.
This is the intermediate representation that gets enriched and then promoted to the catalog.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .catalog_asset import CatalogAsset


@dataclass
class AssetDraft:
    """
    Represents a media item during the ingest process.
    
    This is the intermediate representation that gets enriched by enrichers
    before being promoted to a CatalogAsset in the broadcast domain.
    """
    
    # Core identification
    uuid: uuid.UUID
    """Unique identifier for this asset draft"""
    
    file_path: str
    """Local file system path to the media file"""
    
    # Basic metadata
    title: str | None = None
    """Human-readable title of the content"""
    
    duration_ms: int | None = None
    """Duration in milliseconds"""
    
    # Series/episode information (for TV shows)
    series_title: str | None = None
    """Series name (for TV episodes)"""
    
    season_number: int | None = None
    """Season number (for TV episodes)"""
    
    episode_number: int | None = None
    """Episode number (for TV episodes)"""
    
    episode_title: str | None = None
    """Episode title (for TV episodes)"""
    
    # Technical metadata
    file_size: int | None = None
    """File size in bytes"""
    
    video_codec: str | None = None
    """Video codec information"""
    
    audio_codec: str | None = None
    """Audio codec information"""
    
    container: str | None = None
    """Container format"""
    
    # Source information
    source_type: str = "unknown"
    """Type of source (plex, filesystem, etc.)"""
    
    source_id: str | None = None
    """Source identifier"""
    
    collection_id: str | None = None
    """Collection identifier within the source"""
    
    # External system references
    external_id: str | None = None
    """External system identifier (e.g., Plex rating key)"""
    
    # Enrichment metadata
    raw_metadata: dict[str, Any] | None = None
    """Raw metadata from the source system"""
    
    # Timestamps
    discovered_at: datetime | None = None
    """When this asset was discovered"""
    
    def __post_init__(self) -> None:
        """Initialize default values after dataclass creation."""
        if self.discovered_at is None:
            self.discovered_at = datetime.utcnow()
        
        if self.raw_metadata is None:
            self.raw_metadata = {}
    
    def to_catalog_asset(self) -> CatalogAsset:
        """
        Convert this AssetDraft to a CatalogAsset for the broadcast domain.
        
        Returns:
            CatalogAsset instance ready for scheduling
        """
        from .catalog_asset import CatalogAsset
        
        return CatalogAsset(
            uuid=self.uuid,
            title=self.title or "Unknown Title",
            duration_ms=self.duration_ms or 0,
            file_path=self.file_path,
            tags=self._generate_tags(),
            canonical=True,  # AssetDrafts that reach this point are considered canonical
            source_ingest_asset_id=None,  # Will be set when linked to Asset
            created_at=datetime.utcnow()
        )
    
    def _generate_tags(self) -> str:
        """Generate comma-separated tags for the catalog asset."""
        tags = []
        
        if self.series_title:
            tags.append(f"series:{self.series_title}")
        
        if self.season_number is not None:
            tags.append(f"season:{self.season_number}")
        
        if self.episode_number is not None:
            tags.append(f"episode:{self.episode_number}")
        
        if self.source_type:
            tags.append(f"source:{self.source_type}")
        
        if self.video_codec:
            tags.append(f"video:{self.video_codec}")
        
        if self.audio_codec:
            tags.append(f"audio:{self.audio_codec}")
        
        return ",".join(tags)
    
    def __repr__(self) -> str:
        return f"<AssetDraft(uuid={self.uuid}, title={self.title}, file_path={self.file_path})>"


