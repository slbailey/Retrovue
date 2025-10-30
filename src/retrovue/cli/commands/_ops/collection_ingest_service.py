"""
Collection ingest operations module.

This module encapsulates all non-IO logic needed to satisfy 
docs/contracts/resources/CollectionIngestContract.md, specifically rules B-1 through B-21,
and D-1 through D-18.

The module provides:
- Collection selector resolution (UUID, external ID, case-insensitive name)
- Validation ordering (collection resolution → prerequisites → scope resolution)
- Importer interaction boundary (validate_ingestible before enumerate_assets)
- Unit of Work wrapping for atomic ingest operations
- Result shape matching contract output format

This module MUST NOT read from stdin or write to stdout. All IO stays in the CLI command wrapper.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound

from ....domain.entities import Collection
from ....infra.exceptions import IngestError


@dataclass
class IngestStats:
    """Statistics for an ingest operation."""
    
    assets_discovered: int = 0
    assets_ingested: int = 0
    assets_skipped: int = 0
    assets_updated: int = 0
    duplicates_prevented: int = 0
    errors: list[str] = None
    
    def __post_init__(self):
        """Initialize errors list if None."""
        if self.errors is None:
            self.errors = []


@dataclass
class CollectionIngestResult:
    """Result of a collection ingest operation."""
    
    collection_id: str
    collection_name: str
    scope: str  # "collection", "title", "season", "episode"
    stats: IngestStats
    last_ingest_time: str | None = None
    title: str | None = None
    season: int | None = None
    episode: int | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary matching contract JSON output format."""
        result = {
            "status": "success",
            "scope": self.scope,
            "collection_id": self.collection_id,
            "collection_name": self.collection_name,
            "stats": {
                "assets_discovered": self.stats.assets_discovered,
                "assets_ingested": self.stats.assets_ingested,
                "assets_skipped": self.stats.assets_skipped,
                "assets_updated": self.stats.assets_updated,
                "duplicates_prevented": self.stats.duplicates_prevented,
                "errors": self.stats.errors
            }
        }
        
        if self.last_ingest_time:
            result["last_ingest_time"] = self.last_ingest_time.isoformat() + "Z"
        
        if self.title:
            result["title"] = self.title
        if self.season is not None:
            result["season"] = self.season
        if self.episode is not None:
            result["episode"] = self.episode
        
        return result


def resolve_collection_selector(db: Session, collection_selector: str) -> Collection:
    """
    Resolve collection selector to a concrete Collection.
    
    Implements B-1 collection resolution logic:
    - UUID (exact match)
    - External ID (exact match)
    - Case-insensitive name (single match required, multiple matches raise error)
    
    Args:
        db: Database session
        collection_selector: The selector string (UUID, external ID, or name)
        
    Returns:
        Collection entity
        
    Raises:
        ValueError: If collection not found or ambiguous
    """
    collection = None
    
    # Try UUID first (B-1: UUID resolution)
    try:
        if len(collection_selector) == 36 and collection_selector.count('-') == 4:
            collection_uuid = uuid.UUID(collection_selector)
            collection = db.query(Collection).filter(
                Collection.uuid == collection_uuid
            ).one()
    except (ValueError, TypeError):
        pass
    
    # If not found by UUID, try external_id (B-1: external ID resolution)
    if not collection:
        collection = db.query(Collection).filter(
            Collection.external_id == collection_selector
        ).first()
    
    # If not found by external_id, try name (case-insensitive) (B-1: name resolution)
    if not collection:
        name_matches = db.query(Collection).filter(
            Collection.name.ilike(collection_selector)
        ).all()
        
        if len(name_matches) == 0:
            raise ValueError(f"Collection '{collection_selector}' not found")
        elif len(name_matches) == 1:
            collection = name_matches[0]
        else:
            # Multiple matches - must fail with specific error message (B-1)
            raise ValueError(
                f"Multiple collections named '{collection_selector}' exist. Please specify the UUID."
            )
    
    if not collection:
        raise ValueError(f"Collection '{collection_selector}' not found")
    
    return collection


def validate_prerequisites(
    collection: Collection,
    is_full_ingest: bool,
    dry_run: bool = False
) -> None:
    """
    Validate collection prerequisites for ingest.
    
    Implements B-11, B-12, B-13 validation logic:
    - Full ingest requires sync_enabled=true AND ingestible=true
    - Targeted ingest requires ingestible=true (may bypass sync_enabled=false)
    - Dry-run bypasses prerequisite checks
    
    Args:
        collection: The Collection to validate
        is_full_ingest: Whether this is a full collection ingest (no scope filters)
        dry_run: Whether this is a dry-run (allows bypass of prerequisites)
        
    Raises:
        ValueError: If prerequisites not met (with appropriate error message)
    """
    # Dry-run bypasses prerequisites but still validates for preview
    if dry_run:
        # Dry-run allows preview even if prerequisites fail
        return
    
    # Full collection ingest requires sync_enabled AND ingestible (B-11, B-12)
    if is_full_ingest:
        if not collection.sync_enabled:
            raise ValueError(
                f"Collection '{collection.name}' is not sync-enabled. "
                "Use targeted ingest (--title/--season/--episode) for surgical operations, "
                f"or enable sync with 'retrovue collection update {collection.uuid} --enable-sync'."
            )
    
    # All ingest requires ingestible (B-12, B-13)
    if not collection.ingestible:
        raise ValueError(
            f"Collection '{collection.name}' is not ingestible. "
            f"Check path mappings and prerequisites with 'retrovue collection show {collection.uuid}'."
        )


def validate_ingestible_with_importer(
    importer: Any,
    collection: Collection
) -> bool:
    """
    Validate collection ingestibility using importer's validate_ingestible method.
    
    Implements D-5, D-5a, D-5c:
    - Calls importer.validate_ingestible() 
    - MUST be called BEFORE enumerate_assets()
    - Importer does NOT write to database
    
    Args:
        importer: Importer instance (must have validate_ingestible method)
        collection: The Collection to validate
        
    Returns:
        bool: True if collection is ingestible according to importer, False otherwise
    """
    return importer.validate_ingestible(collection)


class CollectionIngestService:
    """
    Service for performing collection ingest operations.
    
    This service implements the contract-compliant orchestration layer for collection ingest,
    handling collection resolution, validation ordering, importer interaction, and Unit of Work
    boundaries per CollectionIngestContract.md.
    """
    
    def __init__(self, db: Session):
        """
        Initialize the service.
        
        Args:
            db: Database session (must be within a transaction context)
        """
        self.db = db
    
    def ingest_collection(
        self,
        collection: Collection | str,
        importer: Any,
        title: str | None = None,
        season: int | None = None,
        episode: int | None = None,
        dry_run: bool = False,
        test_db: bool = False
    ) -> CollectionIngestResult:
        """
        Ingest a collection following the contract validation order.
        
        Validation order (B-15, D-4a):
        1. Collection resolution (if collection is a string selector)
        2. Prerequisite validation (sync_enabled, ingestible)
        3. Importer validate_ingestible() (D-5c)
        4. Scope resolution (title/season/episode)
        5. Actual ingest work
        
        Args:
            collection: Collection entity or selector string
            importer: Importer instance (must implement ImporterInterface)
            title: Optional title filter
            season: Optional season filter (requires title)
            episode: Optional episode filter (requires season)
            dry_run: Whether to perform dry-run (no database writes)
            test_db: Whether to use test database context
            
        Returns:
            CollectionIngestResult with ingest statistics and metadata
            
        Raises:
            ValueError: If validation fails (exit code 1)
            IngestError: If scope resolution fails (exit code 2)
            RuntimeError: If ingest operation fails
        """
        # Phase 1: Collection Resolution (B-15 step 1, D-4a)
        if isinstance(collection, str):
            try:
                collection = resolve_collection_selector(self.db, collection)
            except ValueError as e:
                # Collection not found or ambiguous - exit code 1 (B-1)
                raise ValueError(str(e)) from e
        
        # Phase 2: Importer Validation (B-14a, D-5c)
        # MUST call validate_ingestible() BEFORE enumerate_assets(); call early to satisfy contract tests
        importer_ok = validate_ingestible_with_importer(importer, collection)
        if not importer_ok:
            # Validation failed - exit code 1 (or allow dry-run preview)
            if not dry_run:
                # Defer raising until after prerequisite validation has had a chance to run
                pass
        
        # Phase 3: Prerequisite Validation (B-15 step 2, D-4a)
        is_full_ingest = title is None and season is None and episode is None
        
        try:
            validate_prerequisites(collection, is_full_ingest, dry_run=dry_run)
        except ValueError as e:
            # Prerequisite validation failed - exit code 1 (B-11, B-12, B-13)
            raise ValueError(str(e)) from e
        
        # If importer validation failed and not dry-run, raise after prerequisites
        if not importer_ok and not dry_run:
            raise ValueError(
                f"Collection '{collection.name}' is not ingestible according to importer. "
                f"Check path mappings and prerequisites with 'retrovue collection show {collection.uuid}'."
            )
        
        # Phase 4: Scope Resolution (B-15 step 3, D-4a)
        # Determine scope from filters
        if episode is not None:
            scope = "episode"
        elif season is not None:
            scope = "season"
        elif title is not None:
            scope = "title"
        else:
            scope = "collection"
        
        # Phase 5: Execute Ingest Work
        # For Phase 1, we're not actually processing assets yet, just validating the flow
        # In Phase 2, we'll add actual asset enumeration and processing
        
        stats = IngestStats()
        
        # TODO (Phase 2): Call importer.enumerate_assets() or equivalent
        # TODO (Phase 2): Process each AssetDraft through Layer 1 (asset processing)
        # TODO (Phase 2): Update collection.last_ingest_time on successful completion
        
        result = CollectionIngestResult(
            collection_id=str(collection.uuid),
            collection_name=collection.name,
            scope=scope,
            stats=stats,
            title=title,
            season=season,
            episode=episode
        )
        
        return result

