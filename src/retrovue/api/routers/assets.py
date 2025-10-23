"""
Assets API endpoints.

This module provides REST API endpoints for managing assets and review queue.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...api.deps import get_db
from ...api.schemas import (
    AssetDetailResponse,
    AssetListResponse,
    AssetSummary,
    AssetWithReviews,
    ReviewQueueListResponse,
    ReviewQueueSummary,
)
from ...app.library_service import LibraryService
from ...domain.entities import Asset, ReviewQueue

router = APIRouter(prefix="/api/v1", tags=["assets"])


@router.get("/assets", response_model=AssetListResponse)
async def list_assets(
    status: Literal["pending", "canonical"] | None = Query(
        None, description="Filter by asset status"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of assets to return"),
    offset: int = Query(0, ge=0, description="Number of assets to skip"),
    db: Session = Depends(get_db),
) -> AssetListResponse:
    """
    List assets with optional filtering.
    
    Args:
        status: Optional status filter ('pending' or 'canonical')
        limit: Maximum number of assets to return
        offset: Number of assets to skip
        
    Returns:
        List of assets with metadata
    """
    try:
        library_service = LibraryService(db)
        assets = library_service.list_assets(status=status)
        
        # Apply pagination
        total = len(assets)
        paginated_assets = assets[offset:offset + limit]
        
        # Convert to DTOs
        asset_summaries = [AssetSummary.from_orm(asset) for asset in paginated_assets]
        
        return AssetListResponse(
            assets=asset_summaries,
            total=total,
            status_filter=status
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list assets: {str(e)}"
        )


@router.get("/assets/{asset_id}", response_model=AssetDetailResponse)
async def get_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
) -> AssetDetailResponse:
    """
    Get detailed information about a specific asset.
    
    Args:
        asset_id: Asset identifier
        
    Returns:
        Detailed asset information with reviews
    """
    try:
        # Get asset from database
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {asset_id} not found"
            )
        
        # Create response with counts
        asset_with_reviews = AssetWithReviews.from_orm(asset)
        
        return AssetDetailResponse(
            asset=asset_with_reviews,
            episode_count=len(asset.episodes),
            marker_count=len(asset.markers),
            provider_ref_count=len(asset.provider_refs)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get asset: {str(e)}"
        )


@router.get("/review-queue", response_model=ReviewQueueListResponse)
async def list_review_queue(
    status: Literal["pending", "resolved"] | None = Query(
        None, description="Filter by review status"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of reviews to return"),
    offset: int = Query(0, ge=0, description="Number of reviews to skip"),
    db: Session = Depends(get_db),
) -> ReviewQueueListResponse:
    """
    List review queue items with optional filtering.
    
    Args:
        status: Optional status filter ('pending' or 'resolved')
        limit: Maximum number of reviews to return
        offset: Number of reviews to skip
        
    Returns:
        List of review queue items with metadata
    """
    try:
        query = db.query(ReviewQueue)
        
        if status == "pending":
            from ...shared.types import ReviewStatus
            query = query.filter(ReviewQueue.status == ReviewStatus.PENDING)
        elif status == "resolved":
            from ...shared.types import ReviewStatus
            query = query.filter(ReviewQueue.status == ReviewStatus.RESOLVED)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        reviews = query.offset(offset).limit(limit).all()
        
        # Convert to DTOs
        review_summaries = [ReviewQueueSummary.from_orm(review) for review in reviews]
        
        return ReviewQueueListResponse(
            reviews=review_summaries,
            total=total,
            status_filter=status
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list review queue: {str(e)}"
        )


@router.post("/assets/{asset_id}/enqueue-review")
async def enqueue_asset_review(
    asset_id: UUID,
    reason: str,
    confidence: float = 0.5,
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    """
    Enqueue an asset for review.
    
    Args:
        asset_id: Asset identifier
        reason: Reason for review
        confidence: Confidence score (0.0-1.0)
        
    Returns:
        Success status
    """
    try:
        library_service = LibraryService(db)
        library_service.enqueue_review(asset_id, reason, confidence)
        
        return {"success": True}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enqueue review: {str(e)}"
        )
