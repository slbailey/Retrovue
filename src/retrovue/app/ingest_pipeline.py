"""
Provider-agnostic ingest pipeline.

This pipeline coordinates importers and enrichers via the registry to discover,
register, and enrich content from various sources.
"""

from __future__ import annotations

import logging
from typing import Any

from ..adapters.registry import get_importer, get_enricher
from ..app.library_service import LibraryService
from ..app.source_service import SourceCollectionDTO, SourceService
from ..domain.entities import Asset

logger = logging.getLogger(__name__)


def translate_path(path: str, mappings: list[tuple[str, str]]) -> str:
    """
    Translate a path using mapping pairs.
    
    Args:
        path: Original path to translate
        mappings: List of (source_prefix, local_prefix) pairs
        
    Returns:
        Translated path
    """
    for src, dst in mappings:
        if path.startswith(src):
            return path.replace(src, dst, 1)
    return path


def confidence_score(asset: Asset) -> float:
    """
    Calculate confidence score for an asset.
    
    Args:
        asset: Asset to score
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    score = 0.0
    
    # Check for duration (from enrichment)
    if asset.duration_ms and asset.duration_ms > 0:
        score += 0.6
    
    # Check for codecs (from enrichment)
    if asset.video_codec or asset.audio_codec:
        score += 0.2
    
    # Check for episode link (from enrichment)
    # For now, we'll check if the asset has episodes linked
    if asset.episodes and len(asset.episodes) > 0:
        score += 0.2
    
    return min(score, 1.0)


def run(
    source: str,
    enrichers: list[str] = None,
    source_id: str | None = None,
    library_ids: list[str] | None = None,
    db=None
) -> dict[str, int]:
    """
    Run the ingest pipeline for a specific source.
    
    Args:
        source: Source type ("plex", "filesystem", etc.)
        enrichers: List of enricher names to apply
        source_id: Optional domain ContentSource id
        library_ids: Optional collection external_ids to scan
        
    Returns:
        Dictionary with summary counts
    """
    if enrichers is None:
        enrichers = ["ffprobe"]
    
    logger.info(f"Starting ingest pipeline for source: {source}")
    
    # Initialize services with database session
    source_service = SourceService(db=db)
    library_service = LibraryService(session=db)
    
    # Step 0: Resolve which collections to scan
    collections_to_scan = []
    
    if source == "plex":
        if library_ids:
            # Use provided library IDs
            for lib_id in library_ids:
                collection = source_service.get_collection(source_id or "plex", lib_id)
                if collection:
                    collections_to_scan.append(collection)
        else:
            # Load enabled collections for this source
            collections_to_scan = source_service.list_enabled_collections(source_id or "plex")
    
    elif source == "filesystem":
        if source_id:
            collections_to_scan = source_service.list_enabled_collections(source_id)
        else:
            # Use default filesystem collection
            collections_to_scan = [SourceCollectionDTO(
                external_id="default",
                name="Default Filesystem",
                enabled=True,
                mapping_pairs=[],
                source_type="filesystem",
                config={"root_paths": ["."], "glob_patterns": ["**/*.mp4", "**/*.mkv"]}
            )]
    
    logger.info(f"Found {len(collections_to_scan)} collections to scan")
    
    # Step 1: Get importer and discover items
    try:
        importer = get_importer(source)
    except Exception as e:
        logger.error(f"Failed to get importer for source {source}: {e}")
        return {"error": f"Failed to get importer: {e}"}
    
    discovered_items = []
    
    if source == "plex":
        # For Plex, discover from specific collections
        for collection in collections_to_scan:
            try:
                # Call importer with collection-specific parameters
                items = importer.discover_from_collection(
                    collection.external_id,
                    include_metadata=True
                )
                discovered_items.extend(items)
            except Exception as e:
                logger.warning(f"Failed to discover from collection {collection.external_id}: {e}")
                continue
    else:
        # For other sources, use general discover method
        try:
            discovered_items = importer.discover()
        except Exception as e:
            logger.error(f"Failed to discover items: {e}")
            return {"error": f"Failed to discover items: {e}"}
    
    logger.info(f"Discovered {len(discovered_items)} items")
    
    # Step 2: Apply path mapping if needed
    for item in discovered_items:
        for collection in collections_to_scan:
            if collection.mapping_pairs:
                original_uri = item.path_uri
                item.path_uri = translate_path(original_uri, collection.mapping_pairs)
                if original_uri != item.path_uri:
                    logger.debug(f"Translated path: {original_uri} -> {item.path_uri}")
    
    # Step 3: Process each item
    registered_count = 0
    enriched_count = 0
    canonicalized_count = 0
    queued_for_review_count = 0
    
    for item in discovered_items:
        try:
            # Step 3a: Register asset from discovery
            asset = library_service.register_asset_from_discovery(item)
            registered_count += 1
            
            # Step 3b: Apply enrichers
            for enricher_name in enrichers:
                try:
                    enricher = get_enricher(enricher_name)
                    asset = enricher.enrich(asset)
                    enriched_count += 1
                except Exception as e:
                    logger.warning(f"Failed to apply enricher {enricher_name}: {e}")
                    continue
            
            # Step 3c: Calculate confidence score
            score = confidence_score(asset)
            
            # Step 3d: Decide whether to canonicalize or queue for review
            if score < 0.8:
                library_service.enqueue_review(asset, reason="low_conf", score=score)
                queued_for_review_count += 1
                logger.debug(f"Queued asset {asset.id} for review (score: {score})")
            else:
                library_service.mark_asset_canonical_asset(asset)
                canonicalized_count += 1
                logger.debug(f"Canonicalized asset {asset.id} (score: {score})")
                
        except Exception as e:
            logger.error(f"Failed to process item {item.path_uri}: {e}")
            continue
    
    # Step 4: Return summary counts
    summary = {
        "discovered": len(discovered_items),
        "registered": registered_count,
        "enriched": enriched_count,
        "canonicalized": canonicalized_count,
        "queued_for_review": queued_for_review_count
    }
    
    logger.info(f"Ingest pipeline completed: {summary}")
    return summary
