"""
CatalogAsset domain model.

Represents the stored, durable record of an ingested piece of content after ingest/enrichment.
This is the promoted/stored version of an AssetDraft after ingest finishes.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CatalogAsset:
    """
    Represents a broadcast-approved catalog entry that is eligible for scheduling and playout.
    
    This is the "airable" content that ScheduleService can select and schedule for broadcast.
    """
    
    # Core identification
    uuid: uuid.UUID
    """External stable identifier exposed to API, runtime, and logs"""
    
    title: str
    """Human-readable asset title"""
    
    duration_ms: int
    """Asset duration in milliseconds"""
    
    file_path: str
    """Local file system path to the asset"""
    
    # Metadata
    tags: str | None = None
    """Comma-separated content tags for categorization"""
    
    canonical: bool = True
    """Approval status - only canonical assets are eligible for scheduling"""
    
    # Traceability
    source_ingest_asset_id: int | None = None
    """Reference to Library Domain asset for traceability"""
    
    # Timestamps
    created_at: datetime = None
    """Record creation timestamp"""
    
    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def is_eligible_for_scheduling(self) -> bool:
        """
        Check if this asset is eligible for scheduling.
        
        Returns:
            True if the asset can be scheduled, False otherwise
        """
        return self.canonical and self.duration_ms > 0
    
    def get_tags_list(self) -> list[str]:
        """
        Get tags as a list.
        
        Returns:
            List of individual tags
        """
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
    
    def has_tag(self, tag: str) -> bool:
        """
        Check if this asset has a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            True if the tag exists, False otherwise
        """
        return tag in self.get_tags_list()
    
    def __repr__(self) -> str:
        return f"<CatalogAsset(uuid={self.uuid}, title={self.title}, canonical={self.canonical})>"


