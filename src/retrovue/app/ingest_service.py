"""
Ingest service - handles content discovery and ingestion.

This service orchestrates the discovery and registration of content
from various sources into the content library.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy.orm import Session

from ..adapters.registry import get_importer, get_enricher
from ..domain.entities import Asset, Source
from .library_service import LibraryService
from .source_service import SourceService

logger = structlog.get_logger(__name__)


class IngestService:
    """Service for content discovery and ingestion."""

    def __init__(self, db: Session):
        """Initialize the ingest service with a database session."""
        self.db = db

    def run_ingest(self, source: str) -> dict[str, int]:
        """
        Run ingestion from a source.

        Args:
            source: Source identifier (e.g., "filesystem:/path/to/media")

        Returns:
            Dictionary with counts: discovered, registered, enriched, canonicalized, queued_for_review
        """
        session = self.db
        library_service = LibraryService(session)

        try:
            # Initialize counters
            counts = {
                "discovered": 0,
                "registered": 0,
                "enriched": 0,
                "canonicalized": 0,
                "queued_for_review": 0,
            }

            # Parse source and get appropriate importer
            if source == "fake":
                importer = get_importer("fake")
                discovered_items = importer.discover()
            elif source.startswith("filesystem:"):
                path = source[11:]  # Remove "filesystem:" prefix
                # Use the filesystem importer from registry
                importer = get_importer("filesystem", root_paths=[path])
                discovered_items = importer.discover()
            elif source == "plex":
                # For Plex, get configured servers from the database
                source_service = SourceService(session)
                
                # Get all Plex sources from the database
                plex_sources = session.query(Source).filter(Source.kind == "plex").all()
                
                if not plex_sources:
                    raise ValueError("No Plex sources configured. Please add a Plex server first.")
                
                # Build server configuration list
                servers = []
                for plex_source in plex_sources:
                    config = plex_source.config or {}
                    servers.append({
                        "base_url": config.get("base_url"),
                        "token": config.get("token")
                    })
                
                # Create importer with configured servers
                importer = get_importer("plex", servers=servers)
                discovered_items = importer.discover()
            else:
                # Try to get importer from registry
                try:
                    importer = get_importer(source)
                    discovered_items = importer.discover()
                except Exception as e:
                    raise ValueError(f"Unsupported source: {source}") from e

            counts["discovered"] = len(discovered_items)

            # Process each discovered item
            for discovered in discovered_items:
                try:
                    # Register the asset - use the DiscoveredItem directly
                    asset = library_service.register_asset_from_discovery(discovered)
                    counts["registered"] += 1

                    # Calculate confidence based on raw_labels
                    confidence = self._calculate_confidence(discovered)

                    # Try to enrich with metadata
                    enrichment = self._extract_metadata(discovered)
                    if enrichment:
                        library_service.enrich_asset(asset.id, enrichment)
                        counts["enriched"] += 1

                    # Mark as canonical if confidence is high enough
                    if confidence >= 0.8:
                        library_service.mark_asset_canonical(asset.id, True)
                        counts["canonicalized"] += 1
                    else:
                        # Queue for review if confidence is low
                        reason = self._get_review_reason(asset, discovered)
                        library_service.enqueue_review(asset.id, reason, confidence)
                        counts["queued_for_review"] += 1

                except Exception as e:
                    logger.error(
                        "ingest_item_failed", source=source, discovered=discovered, error=str(e)
                    )
                    continue

            # Log the ingest completion
            logger.info("ingest_completed", source=source, counts=counts)

            # Always flush to get DB-generated values
            session.flush()
            return counts

        except Exception as e:
            # Session rollback handled by get_db() dependency
            logger.error("ingest_failed", source=source, error=str(e))
            raise

    def rescan_asset(self, asset_id: uuid.UUID) -> Asset:
        """
        Rescan an existing asset for updated metadata.

        Args:
            asset_id: ID of the asset to rescan

        Returns:
            The updated Asset entity
        """
        session = self.db
        library_service = LibraryService(session)

        try:
            # Get the asset
            asset = session.get(Asset, asset_id)
            if not asset:
                raise ValueError(f"Asset {asset_id} not found")

            # Extract fresh metadata
            discovered = {
                "path_uri": asset.uri,
                "size": asset.size,
                "hash_sha256": asset.hash_sha256,
                "provider": "filesystem",
            }

            enrichment = self._extract_metadata(discovered)
            if enrichment:
                library_service.enrich_asset(asset_id, enrichment)

            # Log the rescan
            logger.info("asset_rescanned", asset_id=str(asset_id), enrichment=enrichment)

            # Always flush to get DB-generated values
            session.flush()
            return asset

        except Exception as e:
            # Session rollback handled by get_db() dependency
            logger.error("asset_rescan_failed", asset_id=str(asset_id), error=str(e))
            raise

    def _discover_filesystem_content(self, path: str) -> list[dict[str, Any]]:
        """Discover content from filesystem path."""

        discovered: list[dict[str, Any]] = []
        path_obj = Path(path)

        if not path_obj.exists():
            logger.warning("discovery_path_not_found", path=path)
            return discovered

        # Walk through the directory
        for file_path in path_obj.rglob("*"):
            if file_path.is_file() and self._is_media_file(file_path):
                try:
                    # Get file stats
                    stat = file_path.stat()

                    # Calculate hash
                    hash_sha256 = self._calculate_file_hash(file_path)

                    # Extract labels from filename
                    raw_labels = self._extract_filename_labels(file_path.name)

                    discovered.append(
                        {
                            "path_uri": f"file://{file_path.absolute()}",
                            "size": stat.st_size,
                            "hash_sha256": hash_sha256,
                            "provider": "filesystem",
                            "raw_labels": raw_labels,
                            "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                            + "Z",
                        }
                    )

                except Exception as e:
                    logger.warning("file_discovery_failed", file_path=str(file_path), error=str(e))
                    continue

        return discovered

    def _is_media_file(self, file_path: Path) -> bool:
        """Check if file is a media file."""
        media_extensions = {".mp4", ".mkv", ".avi", ".mov", ".m4v", ".wmv", ".flv", ".webm"}
        return file_path.suffix.lower() in media_extensions

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        with open(file_path, "rb") as f:
            return hashlib.file_digest(f, "sha256").hexdigest()

    def _extract_filename_labels(self, filename: str) -> dict[str, Any]:
        """Extract labels from filename."""
        import re

        labels: dict[str, Any] = {}

        # Try to extract season/episode from filename
        # Pattern: Show.S01E01.mkv or Show - S01E01.mkv
        season_episode_pattern = r"[Ss](\d+)[Ee](\d+)"
        match = re.search(season_episode_pattern, filename)
        if match:
            labels["season"] = int(match.group(1))
            labels["episode"] = int(match.group(2))

        # Try to extract title
        # Remove extension and common patterns
        title = filename
        title = re.sub(r"\.(mp4|mkv|avi|mov|m4v|wmv|flv|webm)$", "", title, flags=re.IGNORECASE)
        title = re.sub(r"[Ss]\d+[Ee]\d+", "", title)
        title = re.sub(r"[._-]", " ", title)
        title = title.strip()

        if title:
            labels["title_guess"] = title

        return labels

    def _extract_metadata(self, discovered) -> dict[str, Any]:
        """Extract metadata from discovered content."""
        # This is a placeholder - in a real implementation, you might use
        # ffprobe or other tools to extract media metadata
        enrichment: dict[str, Any] = {}

        # For now, just return empty enrichment
        # In a real implementation, you would:
        # 1. Use ffprobe to get duration, codecs, etc.
        # 2. Use external APIs to get metadata
        # 3. Use machine learning to classify content

        return enrichment

    def _should_be_canonical(self, asset: Asset, discovered: dict[str, Any]) -> bool:
        """Determine if asset should be marked as canonical."""
        # Simple heuristic: if it has a hash and reasonable size, mark as canonical
        return asset.hash_sha256 is not None and asset.size > 1024 * 1024  # > 1MB

    def _needs_review(self, asset: Asset, discovered: dict[str, Any]) -> bool:
        """Determine if asset needs human review."""
        # Simple heuristic: if no hash or very small size, needs review
        return asset.hash_sha256 is None or asset.size < 1024 * 1024  # < 1MB

    def _get_review_reason(self, asset: Asset, discovered) -> str:
        """Get reason for review."""
        if asset.hash_sha256 is None:
            return "No hash available"
        if asset.size < 1024 * 1024:
            return "File size too small"
        return "Manual review required"

    def _get_review_confidence(self, asset: Asset, discovered: dict[str, Any]) -> float:
        """Get confidence score for review."""
        # Simple heuristic based on available metadata
        confidence = 0.5  # Base confidence

        if asset.hash_sha256:
            confidence += 0.3

        if asset.size > 1024 * 1024:
            confidence += 0.2

        return min(confidence, 1.0)

    def _calculate_confidence(self, discovered) -> float:
        """Calculate confidence score based on discovery data."""
        confidence = 0.5  # Base confidence

        # Handle both DiscoveredItem objects and dicts
        if hasattr(discovered, 'raw_labels'):
            raw_labels = discovered.raw_labels or {}
        else:
            raw_labels = discovered.get("raw_labels", {})
        
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
        if hasattr(discovered, 'size') and discovered.size and discovered.size > 100 * 1024 * 1024:  # > 100MB
            confidence += 0.2

        # +0.2 for codecs present (if we can detect from filename)
        if hasattr(discovered, 'path_uri') and discovered.path_uri:
            filename = discovered.path_uri.split('/')[-1].lower()
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

        return min(confidence, 1.0)

