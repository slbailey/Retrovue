"""
Ingest API endpoints.

This module provides REST API endpoints for running the ingest pipeline.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...app.ingest_pipeline import run
from ...api.deps import get_db

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestRequest(BaseModel):
    """Request body for ingest operations."""
    
    library_ids: list[str] | None = Field(
        None, 
        description="Optional list of library IDs to override enabled collections"
    )
    enrichers: list[str] | None = Field(
        None,
        description="Optional list of enricher names to apply"
    )


class IngestResponse(BaseModel):
    """Response for ingest operations."""
    
    success: bool = Field(True, description="Whether the operation was successful")
    discovered: int = Field(..., description="Number of items discovered")
    registered: int = Field(..., description="Number of items registered")
    enriched: int = Field(..., description="Number of items enriched")
    canonicalized: int = Field(..., description="Number of items canonicalized")
    queued_for_review: int = Field(..., description="Number of items queued for review")
    error: str | None = Field(None, description="Error message if operation failed")


@router.post("/run", response_model=IngestResponse)
async def run_ingest(
    source: str = Query(..., description="Source type (plex, filesystem, etc.)"),
    source_id: str | None = Query(None, description="Optional source ID"),
    request: IngestRequest | None = None,
    db: Session = Depends(get_db)
) -> IngestResponse:
    """
    Run the ingest pipeline for a specific source.
    
    Args:
        source: Source type to ingest from
        source_id: Optional source ID
        request: Optional request body with library IDs and enrichers
        
    Returns:
        Ingest response with summary counts
    """
    try:
        # Extract parameters from request body
        library_ids = None
        enrichers = None
        
        if request:
            library_ids = request.library_ids
            enrichers = request.enrichers
        
        # Run the ingest pipeline
        result = run(
            source=source,
            enrichers=enrichers,
            source_id=source_id,
            library_ids=library_ids,
            db=db
        )
        
        # Check if there was an error
        if "error" in result:
            return IngestResponse(
                success=False,
                discovered=0,
                registered=0,
                enriched=0,
                canonicalized=0,
                queued_for_review=0,
                error=result["error"]
            )
        
        # Return success response
        return IngestResponse(
            success=True,
            discovered=result.get("discovered", 0),
            registered=result.get("registered", 0),
            enriched=result.get("enriched", 0),
            canonicalized=result.get("canonicalized", 0),
            queued_for_review=result.get("queued_for_review", 0)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run ingest pipeline: {str(e)}"
        )


@router.get("/sources/{source_id}/collections")
async def get_source_collections(source_id: str) -> dict[str, Any]:
    """
    Get collections for a specific source.
    
    Args:
        source_id: Source identifier
        
    Returns:
        Dictionary with collections and mapping configuration
    """
    try:
        from ...app.source_service import SourceService
        
        source_service = SourceService(db=db)
        collections = source_service.list_enabled_collections(source_id)
        
        return {
            "source_id": source_id,
            "collections": [
                {
                    "external_id": collection.external_id,
                    "name": collection.name,
                    "enabled": collection.enabled,
                    "mapping_pairs": collection.mapping_pairs,
                    "source_type": collection.source_type,
                    "config": collection.config
                }
                for collection in collections
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get source collections: {str(e)}"
        )


@router.put("/sources/{source_id}/collections/{external_id}")
async def update_source_collection(
    source_id: str,
    external_id: str,
    enabled: bool | None = None,
    mapping_pairs: list[tuple[str, str]] | None = None
) -> dict[str, Any]:
    """
    Update a source collection configuration.
    
    Args:
        source_id: Source identifier
        external_id: Collection external ID
        enabled: New enabled status
        mapping_pairs: New mapping pairs
        
    Returns:
        Success status
    """
    try:
        from ...app.source_service import SourceService
        
        source_service = SourceService(db=db)
        
        if enabled is not None:
            success = source_service.update_collection_enabled(source_id, external_id, enabled)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection {external_id} not found"
                )
        
        if mapping_pairs is not None:
            success = source_service.update_collection_mapping(source_id, external_id, mapping_pairs)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection {external_id} not found"
                )
        
        return {"success": True, "message": "Collection updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update collection: {str(e)}"
        )
