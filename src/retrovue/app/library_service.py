"""
Library service - single source of truth for content library operations.

This service provides all business operations for managing the content library.
CLI and API must use these services instead of direct database access.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

import structlog
from sqlalchemy.orm import Session

from ..domain.entities import Asset, Episode, EpisodeAsset, ReviewQueue, ReviewStatus

logger = structlog.get_logger(__name__)


class LibraryService:
    """Service for managing the content library."""

    def __init__(self, db: Session):
        """Initialize the library service with a database session."""
        self.db = db

    def register_asset_from_discovery(self, discovered: dict[str, Any]) -> Asset:
        """
        Register a new asset from discovery data.

        Args:
            discovered: Discovery data with keys:
                - path_uri: File path or URI
                - size: File size in bytes
                - hash_sha256: SHA-256 hash
                - provider: Provider name
                - raw_labels: Raw metadata labels
                - last_modified: Last modification timestamp

        Returns:
            The registered Asset entity
        """
        session = self.db

        try:
            # Extract discovery data
            path_uri = discovered["path_uri"]
            size = discovered["size"]
            hash_sha256 = discovered.get("hash_sha256")
            provider = discovered.get("provider", "filesystem")
            raw_labels = discovered.get("raw_labels", {})
            last_modified = discovered.get("last_modified")

            # Create new asset
            asset = Asset(
                uri=path_uri,
                size=size,
                hash_sha256=hash_sha256,
                discovered_at=datetime.fromisoformat(last_modified.replace("Z", "+00:00"))
                if last_modified
                else datetime.utcnow(),
                canonical=False,
            )

            session.add(asset)
            session.flush()  # Get the ID

            # Log the registration
            logger.info(
                "asset_registered",
                asset_id=str(asset.id),
                provider=provider,
                uri=path_uri,
                size=size,
                hash_sha256=hash_sha256,
                raw_labels=raw_labels,
            )

            # Always flush to realize PKs without committing
            session.flush()
            return asset

        except Exception as e:
            # Session rollback handled by get_db() dependency
            logger.error("asset_registration_failed", error=str(e), discovered=discovered)
            raise

    def enrich_asset(self, asset_id: uuid.UUID, enrichment: dict[str, Any]) -> Asset:
        """
        Enrich an asset with additional metadata.

        Args:
            asset_id: ID of the asset to enrich
            enrichment: Enrichment data with keys:
                - duration_ms: Duration in milliseconds
                - video_codec: Video codec
                - audio_codec: Audio codec
                - container: Container format

        Returns:
            The enriched Asset entity
        """
        session = self.db

        try:
            asset = session.get(Asset, asset_id)
            if not asset:
                raise ValueError(f"Asset {asset_id} not found")

            # Apply enrichment data
            if "duration_ms" in enrichment:
                asset.duration_ms = enrichment["duration_ms"]
            if "video_codec" in enrichment:
                asset.video_codec = enrichment["video_codec"]
            if "audio_codec" in enrichment:
                asset.audio_codec = enrichment["audio_codec"]
            if "container" in enrichment:
                asset.container = enrichment["container"]

            # Log the enrichment
            logger.info("asset_enriched", asset_id=str(asset_id), enrichment=enrichment)

            # Always flush to get DB-generated values
            session.flush()
            return asset

        except Exception as e:
            # Session rollback handled by get_db() dependency
            logger.error(
                "asset_enrichment_failed",
                asset_id=str(asset_id),
                error=str(e),
                enrichment=enrichment,
            )
            raise

    def link_asset_to_episode(self, asset_id: uuid.UUID, episode_id: uuid.UUID) -> EpisodeAsset:
        """
        Link an asset to an episode.

        Args:
            asset_id: ID of the asset
            episode_id: ID of the episode

        Returns:
            The EpisodeAsset relationship
        """
        session = self.db

        try:
            # Verify asset exists
            asset = session.get(Asset, asset_id)
            if not asset:
                raise ValueError(f"Asset {asset_id} not found")

            # Verify episode exists
            episode = session.get(Episode, episode_id)
            if not episode:
                raise ValueError(f"Episode {episode_id} not found")

            # Create the relationship
            episode_asset = EpisodeAsset(episode_id=episode_id, asset_id=asset_id)

            session.add(episode_asset)

            # Log the linking
            logger.info("asset_linked", asset_id=str(asset_id), episode_id=str(episode_id))

            # Always flush to get DB-generated values
            session.flush()
            return episode_asset

        except Exception as e:
            # Session rollback handled by get_db() dependency
            logger.error(
                "asset_linking_failed",
                asset_id=str(asset_id),
                episode_id=str(episode_id),
                error=str(e),
            )
            raise

    def mark_asset_canonical(self, asset_id: uuid.UUID) -> Asset:
        """
        Mark an asset as canonical.

        Args:
            asset_id: ID of the asset to mark as canonical

        Returns:
            The updated Asset entity
        """
        session = self.db

        try:
            asset = session.get(Asset, asset_id)
            if not asset:
                raise ValueError(f"Asset {asset_id} not found")

            asset.canonical = True

            # Log the canonicalization
            logger.info("asset_canonicalized", asset_id=str(asset_id))

            # Always flush to get DB-generated values
            session.flush()
            return asset

        except Exception as e:
            # Session rollback handled by get_db() dependency
            logger.error("asset_canonicalization_failed", asset_id=str(asset_id), error=str(e))
            raise

    def enqueue_review(self, asset_id: uuid.UUID, reason: str, confidence: float) -> ReviewQueue:
        """
        Enqueue an asset for review.

        Args:
            asset_id: ID of the asset to review
            reason: Reason for review
            confidence: Confidence score (0.0-1.0)

        Returns:
            The ReviewQueue entry
        """
        session = self.db

        try:
            # Verify asset exists
            asset = session.get(Asset, asset_id)
            if not asset:
                raise ValueError(f"Asset {asset_id} not found")

            # Validate confidence score
            if not 0.0 <= confidence <= 1.0:
                raise ValueError("Confidence must be between 0.0 and 1.0")

            # Create review queue entry
            review = ReviewQueue(
                asset_id=asset_id, reason=reason, confidence=confidence, status=ReviewStatus.PENDING
            )

            session.add(review)

            # Log the review enqueue
            logger.info(
                "review_enqueued", asset_id=str(asset_id), reason=reason, confidence=confidence
            )

            # Always flush to get DB-generated values
            session.flush()
            return review

        except Exception as e:
            # Session rollback handled by get_db() dependency
            logger.error(
                "review_enqueue_failed",
                asset_id=str(asset_id),
                error=str(e),
                reason=reason,
                confidence=confidence,
            )
            raise

    def register_asset_from_discovery(self, discovered_item) -> Asset:
        """
        Register an asset from a discovered item.
        
        Args:
            discovered_item: DiscoveredItem from an importer
            
        Returns:
            Registered Asset
        """
        session = self.db
        try:
            # Create new asset from discovered item
            asset = Asset(
                uri=discovered_item.path_uri,
                size=discovered_item.size or 0,
                hash_sha256=discovered_item.hash_sha256,
                canonical=False
            )
            
            session.add(asset)
            
            # Always flush to realize PKs without committing
            session.flush()
            session.refresh(asset)
            
            logger.debug("register_asset_from_discovery", asset_id=str(asset.id), uri=discovered_item.path_uri)
            return asset
        except Exception as e:
            # Session rollback handled by get_db() dependency
            logger.error("register_asset_from_discovery_failed", error=str(e), uri=discovered_item.path_uri)
            raise
        finally:
            # Session cleanup handled by get_db() dependency
            pass

    def mark_asset_canonical_asset(self, asset: Asset) -> Asset:
        """
        Mark an asset as canonical (overloaded method).
        
        Args:
            asset: Asset to mark as canonical
            
        Returns:
            Updated asset
        """
        return self.mark_asset_canonical(asset.id)

    def enqueue_review(self, asset, reason: str, score: float) -> None:
        """
        Accepts either an Asset instance or a UUID asset_id.
        Enqueues a ReviewQueue row and commits.
        """
        asset_id = asset.id if hasattr(asset, "id") else asset
        if isinstance(asset_id, str):
            asset_id = UUID(asset_id)

        review = ReviewQueue(
            asset_id=asset_id,
            reason=reason,
            score=score,
            status=ReviewStatus.PENDING,
        )
        self.db.add(review)
        self.db.flush()

    def list_assets(self, status: Literal["pending", "canonical"] | None = None) -> list[Asset]:
        """
        List assets with optional status filter.

        Args:
            status: Optional status filter ('pending' or 'canonical')

        Returns:
            List of Asset entities
        """
        session = self.db

        try:
            query = session.query(Asset)

            if status == "pending":
                # Assets that are not canonical
                query = query.filter(Asset.canonical.is_(False))
            elif status == "canonical":
                # Assets that are canonical
                query = query.filter(Asset.canonical.is_(True))

            assets = query.all()

            # Log the listing
            logger.info("assets_listed", count=len(assets), status=status)

            return assets

        except Exception as e:
            logger.error("asset_listing_failed", error=str(e), status=status)
            raise

    def list_canonical_assets(self, query: str | None = None) -> list[Asset]:
        """
        List canonical assets with optional search filter.

        Args:
            query: Optional search query to filter by URI

        Returns:
            List of canonical Asset entities
        """
        session = self.db

        try:
            db_query = session.query(Asset).filter(Asset.canonical.is_(True))

            if query:
                # Filter by URI containing the query string
                db_query = db_query.filter(Asset.uri.ilike(f"%{query}%"))

            # Order by discovered_at (most recent first)
            assets = db_query.order_by(Asset.discovered_at.desc()).all()

            # Log the listing
            logger.info("canonical_assets_listed", count=len(assets), query=query)

            return assets

        except Exception as e:
            logger.error("canonical_assets_listing_failed", error=str(e), query=query)
            raise

    def mark_asset_canonical(self, asset_id: UUID, value: bool) -> Asset:
        """
        Mark an asset as canonical or not.

        Args:
            asset_id: ID of the asset to update
            value: Whether to mark as canonical (True) or not (False)

        Returns:
            The updated Asset entity
        """
        session = self.db

        try:
            asset = session.get(Asset, asset_id)
            if not asset:
                raise ValueError(f"Asset {asset_id} not found")

            asset.canonical = value

            # Log the canonicalization
            logger.info("asset_canonical_updated", asset_id=str(asset_id), canonical=value)

            # Always flush to get DB-generated values
            session.flush()
            return asset

        except Exception as e:
            # Session rollback handled by get_db() dependency
            logger.error("asset_canonical_update_failed", asset_id=str(asset_id), error=str(e))
            raise

    def list_pending_assets(self) -> list[Asset]:
        """
        List pending assets (non-canonical).

        Returns:
            List of pending Asset entities
        """
        return self.list_assets(status="pending")

    def list_review_queue(self) -> list[ReviewQueue]:
        """
        List items in the review queue.

        Returns:
            List of ReviewQueue entities
        """
        session = self.db

        try:
            reviews = session.query(ReviewQueue).filter(
                ReviewQueue.status == ReviewStatus.PENDING
            ).all()

            # Log the listing
            logger.info("review_queue_listed", count=len(reviews))

            return reviews

        except Exception as e:
            logger.error("review_queue_listing_failed", error=str(e))
            raise

    def resolve_review(self, review_id: UUID, episode_id: UUID, notes: str | None = None) -> bool:
        """
        Resolve a review queue item.

        Args:
            review_id: ID of the review to resolve
            episode_id: ID of the episode to associate
            notes: Optional resolution notes

        Returns:
            True if successful, False otherwise
        """
        session = self.db

        try:
            # Get the review
            review = session.get(ReviewQueue, review_id)
            if not review:
                logger.warning("review_not_found", review_id=str(review_id))
                return False

            # Update the review status
            review.status = ReviewStatus.RESOLVED
            review.resolved_at = datetime.utcnow()
            if notes:
                review.notes = notes

            # Link the asset to the episode
            self.link_asset_to_episode(review.asset_id, episode_id)

            # Log the resolution
            logger.info(
                "review_resolved",
                review_id=str(review_id),
                asset_id=str(review.asset_id),
                episode_id=str(episode_id),
                notes=notes
            )

            # Always flush to get DB-generated values
            session.flush()
            return True

        except Exception as e:
            logger.error(
                "review_resolution_failed",
                review_id=str(review_id),
                episode_id=str(episode_id),
                error=str(e)
            )
            raise

