"""
Assets command group.

Handles asset management operations.
"""

from __future__ import annotations

import typer
from typing import Optional
from enum import Enum

from ..uow import session
from ...api.schemas import AssetListResponse, AssetSummary
from ...app.library_service import LibraryService

app = typer.Typer(name="assets", help="Asset management operations")


class AssetStatus(str, Enum):
    """Asset status options."""
    PENDING = "pending"
    CANONICAL = "canonical"
    ALL = "all"


@app.command("list")
def list_assets(
    status: AssetStatus = typer.Option(AssetStatus.ALL, "--status", help="Filter by asset status"),
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    List assets with optional status filtering.
    
    Examples:
        retrovue assets list
        retrovue assets list --status pending
        retrovue assets list --status canonical --json
    """
    with session() as db:
        library_service = LibraryService(db)
        
        try:
            # Get assets based on status filter
            if status == AssetStatus.ALL:
                assets = library_service.list_assets()
            elif status == AssetStatus.PENDING:
                assets = library_service.list_pending_assets()
            elif status == AssetStatus.CANONICAL:
                assets = library_service.list_canonical_assets()
            else:
                assets = library_service.list_assets()
            
            # Convert to response models
            asset_summaries = [AssetSummary.from_orm(asset) for asset in assets]
            response = AssetListResponse(
                assets=asset_summaries,
                total=len(asset_summaries),
                status_filter=status.value if status != AssetStatus.ALL else None
            )
            
            if json:
                typer.echo(response.model_dump_json(indent=2))
            else:
                typer.echo(f"Found {len(asset_summaries)} assets")
                for asset in asset_summaries:
                    status_str = "CANONICAL" if asset.canonical else "PENDING"
                    typer.echo(f"  {asset.id} - {asset.uri} ({status_str})")
                    
        except Exception as e:
            typer.echo(f"Error listing assets: {e}", err=True)
            raise typer.Exit(1)
