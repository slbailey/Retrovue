"""
Ingest Orchestrator - canonical orchestration of content ingestion.

This module provides the single source of truth for all ingest orchestration
logic, consolidating all ingest operations into a single orchestrator.

TODO: Channel runtime and Producer MUST NOT call ingest_orchestrator. 
This orchestrator is offline/batch. Runtime will only consume canonical assets 
that have already been imported and enriched.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

import structlog
from sqlalchemy.orm import Session

from ..adapters.registry import get_importer, get_enricher
from ..domain.entities import Asset, Source
from .library_service import LibraryService
from .source_service import SourceService, SourceCollectionDTO

logger = structlog.get_logger(__name__)


@dataclass
class IngestReport:
    """Report of ingest operation results."""
    
    discovered: int = 0
    """Number of items discovered"""
    
    registered: int = 0
    """Number of assets registered"""
    
    enriched: int = 0
    """Number of assets enriched"""
    
    canonicalized: int = 0
    """Number of assets marked as canonical"""
    
    queued_for_review: int = 0
    """Number of assets queued for review"""
    
    errors: int = 0
    """Number of processing errors"""
    
    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary format for API responses."""
        return {
            "discovered": self.discovered,
            "registered": self.registered,
            "enriched": self.enriched,
            "canonicalized": self.canonicalized,
            "queued_for_review": self.queued_for_review,
            "errors": self.errors,
        }


class IngestOrchestrator:
    """
    Orchestrator for content ingestion operations.
    
    This orchestrator coordinates the complex multi-step process of content
    ingestion, managing the flow from external sources through discovery,
    enrichment, and final registration in the content library.
    
    **Architectural Role:** Orchestrator
    
    **Coordination Responsibilities:**
    - Coordinates SourceService (where does content live)
    - Coordinates registered Importers (adapters) for content discovery
    - Coordinates Enrichers for metadata enhancement
    - Coordinates LibraryService (which commits state)
    - Manages confidence calculation and canonicalization decisions
    
    **Critical Rule:** All ingest entrypoints (CLI, API) must call this
    orchestrator instead of reimplementing ingest steps. This ensures
    consistent behavior and prevents duplication of ingest logic.
    """
    
    def __init__(self, db: Session):
        """Initialize the orchestrator with a database session."""
        self.db = db
        self.library_service = LibraryService(db)
        self.source_service = SourceService(db)
    
    def run_full_ingest(
        self, 
        *, 
        source_id: str | None = None, 
        collection_id: str | None = None,
        dry_run: bool = False
    ) -> IngestReport:
        """
        Run full ingest operation for enabled collections.
        
        Args:
            source_id: Optional source ID to limit to specific source
            collection_id: Optional collection ID to limit to specific collection
            dry_run: If True, don't actually register/enrich assets
            
        Returns:
            IngestReport with operation results
        """
        report = IngestReport()
        
        try:
            # Step 1: Get collections to scan
            collections = self._get_collections_to_scan(source_id, collection_id)
            logger.info("ingest_started", collections_count=len(collections), dry_run=dry_run)
            
            # Step 2: Process each collection
            for collection in collections:
                try:
                    collection_report = self._process_collection(collection, dry_run)
                    self._merge_reports(report, collection_report)
                except Exception as e:
                    logger.error("collection_processing_failed", 
                               collection_id=collection.external_id, error=str(e))
                    report.errors += 1
                    continue
            
            logger.info("ingest_completed", report=report.to_dict())
            return report
            
        except Exception as e:
            logger.error("ingest_failed", error=str(e))
            raise
    
    def ingest_single_episode(
        self, 
        source_id: str, 
        episode_id: str,
        dry_run: bool = False
    ) -> IngestReport:
        """
        Ingest a single episode from a Plex source.
        
        Args:
            source_id: Source ID (e.g., "plex")
            episode_id: Plex episode rating key
            dry_run: If True, don't actually register/enrich assets
            
        Returns:
            IngestReport with operation results
        """
        report = IngestReport()
        
        try:
            # Get the source
            source = self.db.query(Source).filter(Source.external_id == source_id).first()
            if not source:
                raise ValueError(f"Source {source_id} not found")
            
            # Get importer for the source
            importer = self._get_importer_for_source(source)
            
            # Discover the specific episode
            discovered_items = importer.discover_episode(episode_id)
            report.discovered = len(discovered_items)
            
            # Process each discovered item
            for item in discovered_items:
                try:
                    item_report = self._process_discovered_item(item, dry_run)
                    self._merge_reports(report, item_report)
                except Exception as e:
                    logger.error("episode_processing_failed", 
                               episode_id=episode_id, error=str(e))
                    report.errors += 1
                    continue
            
            logger.info("single_episode_ingest_completed", 
                       episode_id=episode_id, report=report.to_dict())
            return report
            
        except Exception as e:
            logger.error("single_episode_ingest_failed", 
                        episode_id=episode_id, error=str(e))
            raise
    
    def _get_collections_to_scan(
        self, 
        source_id: str | None = None, 
        collection_id: str | None = None
    ) -> list[SourceCollectionDTO]:
        """Get collections to scan based on parameters."""
        collections = []
        
        if source_id and collection_id:
            # Specific source and collection
            collection = self.source_service.get_collection(source_id, collection_id)
            if collection:
                collections = [collection]
        elif source_id:
            # All enabled collections for a source
            collections = self.source_service.list_enabled_collections(source_id)
        else:
            # All enabled collections from all sources
            sources = self.db.query(Source).all()
            for source in sources:
                source_collections = self.source_service.list_enabled_collections(source.external_id)
                collections.extend(source_collections)
        
        return collections
    
    def _process_collection(self, collection: SourceCollectionDTO, dry_run: bool) -> IngestReport:
        """Process a single collection."""
        report = IngestReport()
        
        # Get importer for the collection's source type
        importer = self._get_importer_for_collection(collection)
        
        # Discover items from the collection
        discovered_items = self._discover_from_collection(importer, collection)
        report.discovered = len(discovered_items)
        
        # Process each discovered item
        for item in discovered_items:
            try:
                item_report = self._process_discovered_item(item, dry_run)
                self._merge_reports(report, item_report)
            except Exception as e:
                logger.error("item_processing_failed", 
                           item_uri=item.path_uri, error=str(e))
                report.errors += 1
                continue
        
        return report
    
    def _discover_from_collection(self, importer, collection: SourceCollectionDTO) -> list:
        """Discover items from a collection using the appropriate importer."""
        if collection.source_type == "plex":
            # For Plex, use collection-specific discovery
            return importer.discover_from_collection(
                collection.external_id,
                include_metadata=True
            )
        else:
            # For other sources, use general discovery
            return importer.discover()
    
    def _process_discovered_item(self, item, dry_run: bool) -> IngestReport:
        """Process a single discovered item."""
        report = IngestReport()
        
        if dry_run:
            # In dry run mode, just count as discovered
            report.discovered = 1
            return report
        
        try:
            # Step 1: Register the asset
            asset = self.library_service.register_asset_from_discovery(item)
            report.registered = 1
            
            # Step 2: Apply enrichers
            enrichers = ["ffprobe"]  # Default enrichers
            for enricher_name in enrichers:
                try:
                    enricher = get_enricher(enricher_name)
                    asset = enricher.enrich(asset)
                    report.enriched = 1
                except Exception as e:
                    logger.warning("enricher_failed", 
                                 enricher=enricher_name, error=str(e))
                    continue
            
            # Step 3: Calculate confidence and make canonicalization decision
            confidence = self._calculate_confidence(item, asset)
            
            if confidence >= 0.8:
                self.library_service.mark_asset_canonical(asset.id)
                report.canonicalized = 1
                logger.debug("asset_canonicalized", asset_id=str(asset.id), confidence=confidence)
            else:
                reason = self._get_review_reason(asset, item)
                self.library_service.enqueue_review(asset.id, reason, confidence)
                report.queued_for_review = 1
                logger.debug("asset_queued_for_review", asset_id=str(asset.id), confidence=confidence)
            
            return report
            
        except Exception as e:
            logger.error("item_processing_failed", item_uri=item.path_uri, error=str(e))
            report.errors = 1
            return report
    
    def _get_importer_for_source(self, source: Source):
        """Get importer for a source."""
        if source.kind == "plex":
            # Build server configuration from source
            config = source.config or {}
            servers = [{
                "base_url": config.get("base_url"),
                "token": config.get("token")
            }]
            return get_importer("plex", servers=servers)
        else:
            return get_importer(source.kind)
    
    def _get_importer_for_collection(self, collection: SourceCollectionDTO):
        """Get importer for a collection."""
        if collection.source_type == "plex":
            # Get Plex sources from database
            plex_sources = self.db.query(Source).filter(Source.kind == "plex").all()
            if not plex_sources:
                raise ValueError("No Plex sources configured")
            
            # Build server configuration list
            servers = []
            for plex_source in plex_sources:
                config = plex_source.config or {}
                servers.append({
                    "base_url": config.get("base_url"),
                    "token": config.get("token")
                })
            
            return get_importer("plex", servers=servers)
        else:
            return get_importer(collection.source_type)
    
    def _calculate_confidence(self, discovered_item, asset: Asset) -> float:
        """
        Calculate confidence score for canonicalization decision.
        
        This is the canonical confidence calculation logic.
        """
        confidence = 0.5  # Base confidence
        
        # Handle both DiscoveredItem objects and dicts
        if hasattr(discovered_item, 'raw_labels'):
            raw_labels = discovered_item.raw_labels or {}
        else:
            raw_labels = discovered_item.get("raw_labels", {})
        
        # Ensure raw_labels is a dict
        if isinstance(raw_labels, list):
            # Convert list of strings to dict for processing
            labels_dict = {}
            for label in raw_labels:
                if ":" in label:
                    key, value = label.split(":", 1)
                    labels_dict[key] = value
            raw_labels = labels_dict
        
        # +0.4 for title match (strong indicator) - but only for meaningful titles
        if "title_guess" in raw_labels and raw_labels["title_guess"]:
            title = raw_labels["title_guess"]
            # Only boost confidence for titles that look meaningful (not just random strings)
            if len(title) > 3 and not title.isdigit() and not title.isalnum():
                confidence += 0.4
            elif len(title) > 5:  # Allow longer alphanumeric titles
                confidence += 0.2
        
        # +0.2 for season/episode structured data
        if "season" in raw_labels and "episode" in raw_labels:
            confidence += 0.2
        
        # +0.2 for year data
        if "year" in raw_labels:
            confidence += 0.2
        
        # +0.2 for duration present (if we can detect it from file size or metadata)
        if hasattr(discovered_item, 'size') and discovered_item.size and discovered_item.size > 100 * 1024 * 1024:  # > 100MB
            confidence += 0.2
        
        # +0.2 for codecs present (if we can detect from filename)
        if hasattr(discovered_item, 'path_uri') and discovered_item.path_uri:
            filename = discovered_item.path_uri.split('/')[-1].lower()
            # Check for common codec indicators in filename
            codec_indicators = ['h264', 'h265', 'hevc', 'x264', 'x265', 'avc', 'aac', 'ac3', 'dts']
            if any(codec in filename for codec in codec_indicators):
                confidence += 0.2
        
        # Additional boost for structured content type
        if "type" in raw_labels:
            confidence += 0.1
        
        # Boost confidence for Plex metadata (legacy support)
        if "title" in raw_labels:
            confidence += 0.3  # Plex provides good metadata
        
        # Additional confidence from asset enrichment
        if asset.duration_ms and asset.duration_ms > 0:
            confidence += 0.1
        
        if asset.video_codec or asset.audio_codec:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _get_review_reason(self, asset: Asset, discovered_item) -> str:
        """Get reason for review queue."""
        if asset.hash_sha256 is None:
            return "No hash available"
        if asset.size < 1024 * 1024:
            return "File size too small"
        return "Manual review required"
    
    def _merge_reports(self, target: IngestReport, source: IngestReport):
        """Merge source report into target report."""
        target.discovered += source.discovered
        target.registered += source.registered
        target.enriched += source.enriched
        target.canonicalized += source.canonicalized
        target.queued_for_review += source.queued_for_review
        target.errors += source.errors
