"""
Assets command group.

Handles asset management operations.
Reuses existing LibraryService, UoW session management, and API schemas.

Repository/Service functions reused:
- LibraryService.list_episodes_by_series() for series-based selection
- LibraryService.list_assets_advanced() for genre-based filtering (TODO: implement genre filtering)
- LibraryService.get_asset_by_uuid() for asset retrieval
"""

from __future__ import annotations

import typer
import json
import random
from typing import Optional
from enum import Enum
from uuid import UUID

from ..uow import session
from ...api.schemas import AssetListResponse, AssetSummary
from ...app.library_service import LibraryService
from ...domain.entities import ProviderRef, EntityType

app = typer.Typer(name="assets", help="Asset management operations")


class AssetStatus(str, Enum):
    """Asset status options."""
    PENDING = "pending"
    CANONICAL = "canonical"
    ALL = "all"


class SelectionMode(str, Enum):
    """Selection mode options."""
    RANDOM = "random"
    SEQUENTIAL = "sequential"


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


@app.command("list-advanced")
def list_assets_advanced(
    kind: Optional[str] = typer.Option(None, "--kind", help="Filter by asset kind (episode, ad, bumper)"),
    series: Optional[str] = typer.Option(None, "--series", help="Filter by series title"),
    season: Optional[int] = typer.Option(None, "--season", help="Filter by season number"),
    q: Optional[str] = typer.Option(None, "--q", help="Search query for title or series"),
    limit: int = typer.Option(50, "--limit", help="Maximum number of results"),
    offset: int = typer.Option(0, "--offset", help="Number of results to skip"),
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    List assets with advanced filtering options.
    
    Examples:
        retrovue assets list-advanced --kind episode --series "Batman TAS"
        retrovue assets list-advanced --season 1 --limit 10
        retrovue assets list-advanced --q "pilot" --json
    """
    with session() as db:
        library_service = LibraryService(db)
        
        try:
            assets = library_service.list_assets_advanced(
                kind=kind, series=series, season=season, q=q, limit=limit, offset=offset
            )
            
            if json:
                # Convert to response format
                asset_summaries = [AssetSummary.from_orm(asset) for asset in assets]
                response = AssetListResponse(
                    assets=asset_summaries,
                    total=len(asset_summaries)
                )
                typer.echo(response.model_dump_json(indent=2))
            else:
                # Print table format
                typer.echo(f"Found {len(assets)} assets")
                typer.echo("UUID\t\tKIND\tDURATION\tSERIES\tS\tE\tTITLE")
                typer.echo("-" * 90)
                
                for asset in assets:
                    # Get series info from ProviderRef
                    provider_ref = db.query(ProviderRef).filter(
                        ProviderRef.asset_id == asset.id,
                        ProviderRef.entity_type == EntityType.ASSET
                    ).first()
                    
                    if provider_ref and provider_ref.raw:
                        raw = provider_ref.raw
                        kind = raw.get('kind', 'episode')
                        series_title = raw.get('grandparentTitle', '')
                        season_num = raw.get('parentIndex', '')
                        episode_num = raw.get('index', '')
                        title = raw.get('title', '')
                        duration = f"{asset.duration_ms // 1000 // 60}m" if asset.duration_ms else "N/A"
                    else:
                        kind = "unknown"
                        series_title = ""
                        season_num = ""
                        episode_num = ""
                        title = ""
                        duration = f"{asset.duration_ms // 1000 // 60}m" if asset.duration_ms else "N/A"
                    
                    # Truncate UUID to first 8 characters for readability
                    uuid_short = str(asset.uuid)[:8]
                    typer.echo(f"{uuid_short}\t\t{kind}\t{duration}\t{series_title}\t{season_num}\t{episode_num}\t{title}")
                    
        except Exception as e:
            typer.echo(f"Error listing assets: {e}", err=True)
            raise typer.Exit(1)


@app.command("get")
def get_asset(
    uuid_arg: Optional[str] = typer.Argument(None, help="Asset UUID (positional)"),
    uuid_opt: Optional[str] = typer.Option(None, "--uuid", help="Asset UUID (flag)"),
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Get detailed information about a specific asset.
    
    You can provide the UUID either as a positional argument or using the --uuid flag.
    
    Examples:
        retrovue assets get 41dc6fd4-a9c1-4686-bec5-1cf7dfd03e4e
        retrovue assets get --uuid 41dc6fd4-a9c1-4686-bec5-1cf7dfd03e4e
        retrovue assets get 41dc6fd4-a9c1-4686-bec5-1cf7dfd03e4e --json
        retrovue assets get --uuid 41dc6fd4-a9c1-4686-bec5-1cf7dfd03e4e --json
    """
    # Validate that exactly one UUID is provided
    if uuid_arg and uuid_opt:
        typer.echo("Error: Provide either positional UUID or --uuid, not both", err=True)
        raise typer.Exit(1)
    
    if not uuid_arg and not uuid_opt:
        typer.echo("Error: You must provide an asset UUID", err=True)
        raise typer.Exit(1)
    
    # Normalize to a single variable
    asset_uuid = uuid_arg or uuid_opt
    with session() as db:
        library_service = LibraryService(db)
        
        try:
            asset_uuid_obj = UUID(asset_uuid)
            asset = library_service.get_asset_by_uuid(asset_uuid_obj)
            
            if not asset:
                typer.echo(f"Asset {asset_uuid} not found", err=True)
                raise typer.Exit(1)
            
            if json:
                asset_summary = AssetSummary.from_orm(asset)
                typer.echo(asset_summary.model_dump_json(indent=2))
            else:
                typer.echo(f"Asset: {asset.id}")
                typer.echo(f"  UUID: {asset.uuid}")
                typer.echo(f"  URI: {asset.uri}")
                typer.echo(f"  Size: {asset.size:,} bytes")
                typer.echo(f"  Duration: {asset.duration_ms // 1000 // 60} minutes" if asset.duration_ms else "  Duration: Unknown")
                typer.echo(f"  Video Codec: {asset.video_codec or 'Unknown'}")
                typer.echo(f"  Audio Codec: {asset.audio_codec or 'Unknown'}")
                typer.echo(f"  Container: {asset.container or 'Unknown'}")
                typer.echo(f"  Hash: {asset.hash_sha256[:16]}..." if asset.hash_sha256 else "  Hash: Not computed")
                typer.echo(f"  Canonical: {asset.canonical}")
                typer.echo(f"  Discovered: {asset.discovered_at}")
                
        except ValueError as e:
            typer.echo(f"Invalid UUID format: {e}", err=True)
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"Error getting asset: {e}", err=True)
            raise typer.Exit(1)


@app.command("select")
def select_asset(
    series_arg: Optional[str] = typer.Argument(None, help="Series name (positional)"),
    series_opt: Optional[str] = typer.Option(None, "--series", help="Series name (flag)"),
    genre: Optional[str] = typer.Option(None, "--genre", help="Filter by genre"),
    mode: SelectionMode = typer.Option(SelectionMode.RANDOM, "--mode", help="Selection mode"),
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Select an asset (returning UUID + lightweight metadata).
    
    You can provide the series name either as a positional argument or using the --series flag.
    Series positional and --series are mutually exclusive.
    
    Examples:
        retrovue assets select "Cheers" --mode random --json
        retrovue assets select --series "Cheers" --mode sequential
        retrovue assets select --genre horror --mode random --json
    """
    # Validate that exactly one series is provided if using series
    if series_arg and series_opt:
        typer.echo("Error: Provide either positional SERIES or --series, not both.", err=True)
        raise typer.Exit(1)
    
    # Normalize to a single variable
    series = series_arg or series_opt
    
    # Validate that at least one filter is provided
    if not series and not genre:
        typer.echo("Error: Selection requires at least one filter: series or genre", err=True)
        raise typer.Exit(1)
    
    with session() as db:
        library_service = LibraryService(db)
        
        try:
            selected_asset = None
            
            if genre:
                # TODO: Implement genre-based filtering
                # For now, return an error
                typer.echo("Error: Genre filtering not yet implemented", err=True)
                raise typer.Exit(1)
            
            elif series:
                # Get episodes for the series
                assets = library_service.list_episodes_by_series(series)
                
                if not assets:
                    typer.echo(f"No episodes found for series '{series}'", err=True)
                    raise typer.Exit(1)
                
                if mode == SelectionMode.RANDOM:
                    # Random selection
                    selected_asset = random.choice(assets)
                elif mode == SelectionMode.SEQUENTIAL:
                    # Sequential selection - for now, pick first episode (S01E01)
                    # TODO: Add per-channel last-played logic
                    selected_asset = assets[0]
            
            if not selected_asset:
                typer.echo("Error: No asset selected", err=True)
                raise typer.Exit(1)
            
            # Get provider reference for metadata
            provider_ref = db.query(ProviderRef).filter(
                ProviderRef.asset_id == selected_asset.id,
                ProviderRef.entity_type == EntityType.ASSET
            ).first()
            
            if json:
                # Build JSON response
                if provider_ref and provider_ref.raw:
                    raw = provider_ref.raw
                    result = {
                        "uuid": str(selected_asset.uuid),
                        "id": selected_asset.id,
                        "title": raw.get('title', ''),
                        "series_title": raw.get('grandparentTitle', ''),
                        "season_number": int(raw.get('parentIndex', 0)),
                        "episode_number": int(raw.get('index', 0)),
                        "kind": raw.get('kind', 'episode'),
                        "selection": {
                            "mode": mode.value,
                            "criteria": {
                                "series": series if series else None,
                                "genre": genre if genre else None
                            }
                        }
                    }
                else:
                    result = {
                        "uuid": str(selected_asset.uuid),
                        "id": selected_asset.id,
                        "title": "",
                        "series_title": "",
                        "season_number": 0,
                        "episode_number": 0,
                        "kind": "episode",
                        "selection": {
                            "mode": mode.value,
                            "criteria": {
                                "series": series if series else None,
                                "genre": genre if genre else None
                            }
                        }
                    }
                
                import json as json_module
                typer.echo(json_module.dumps(result, indent=2))
            else:
                # Human-readable output
                if provider_ref and provider_ref.raw:
                    raw = provider_ref.raw
                    series_title = raw.get('grandparentTitle', '')
                    season_num = int(raw.get('parentIndex', 0))
                    episode_num = int(raw.get('index', 0))
                    title = raw.get('title', '')
                    
                    typer.echo(f"{series_title} S{season_num:02d}E{episode_num:02d} \"{title}\"  {selected_asset.uuid}")
                else:
                    typer.echo(f"Asset {selected_asset.uuid}")
                    
        except Exception as e:
            typer.echo(f"Error selecting asset: {e}", err=True)
            raise typer.Exit(1)


@app.command("series")
def list_series(
    series_arg: Optional[str] = typer.Argument(None, help="Series name (positional)"),
    series_opt: Optional[str] = typer.Option(None, "--series", help="Series name (flag)"),
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    List series or episodes for a specific series.
    
    DEPRECATED: When a series is provided, use 'assets select' to choose an episode.
    
    You can provide the series name either as a positional argument or using the --series flag.
    
    Examples:
        retrovue assets series
        retrovue assets series "Batman TAS"  # DEPRECATED: Use 'assets select "Batman TAS"'
        retrovue assets series --series "Batman TAS"  # DEPRECATED: Use 'assets select --series "Batman TAS"'
    """
    # Validate that exactly one series is provided
    if series_arg and series_opt:
        typer.echo("Error: Provide either positional SERIES or --series, not both.", err=True)
        raise typer.Exit(1)
    
    # Normalize to a single variable
    series = series_arg or series_opt
    with session() as db:
        library_service = LibraryService(db)
        
        try:
            if series:
                # DEPRECATION WARNING: Print to stderr
                typer.echo("DEPRECATION: 'assets series <name>' is deprecated. Use 'assets select <name>' to choose an episode, or 'assets get <uuid>' to fetch details.", err=True)
                
                # Delegate to assets select with random mode
                # Get episodes for the series
                assets = library_service.list_episodes_by_series(series)
                
                if not assets:
                    typer.echo(f"No episodes found for series '{series}'", err=True)
                    raise typer.Exit(1)
                
                # Random selection (default mode for assets select)
                selected_asset = random.choice(assets)
                
                # Get provider reference for metadata
                provider_ref = db.query(ProviderRef).filter(
                    ProviderRef.asset_id == selected_asset.id,
                    ProviderRef.entity_type == EntityType.ASSET
                ).first()
                
                if json:
                    # Return the same JSON format as assets select
                    if provider_ref and provider_ref.raw:
                        raw = provider_ref.raw
                        result = {
                            "uuid": str(selected_asset.uuid),
                            "id": selected_asset.id,
                            "title": raw.get('title', ''),
                            "series_title": raw.get('grandparentTitle', ''),
                            "season_number": int(raw.get('parentIndex', 0)),
                            "episode_number": int(raw.get('index', 0)),
                            "kind": raw.get('kind', 'episode'),
                            "selection": {
                                "mode": "random",
                                "criteria": {
                                    "series": series
                                }
                            }
                        }
                    else:
                        result = {
                            "uuid": str(selected_asset.uuid),
                            "id": selected_asset.id,
                            "title": "",
                            "series_title": "",
                            "season_number": 0,
                            "episode_number": 0,
                            "kind": "episode",
                            "selection": {
                                "mode": "random",
                                "criteria": {
                                    "series": series
                                }
                            }
                        }
                    
                    import json as json_module
                    typer.echo(json_module.dumps(result, indent=2))
                else:
                    # Human-readable output (same format as assets select)
                    if provider_ref and provider_ref.raw:
                        raw = provider_ref.raw
                        series_title = raw.get('grandparentTitle', '')
                        season_num = int(raw.get('parentIndex', 0))
                        episode_num = int(raw.get('index', 0))
                        title = raw.get('title', '')
                        
                        typer.echo(f"{series_title} S{season_num:02d}E{episode_num:02d} \"{title}\"  {selected_asset.uuid}")
                    else:
                        typer.echo(f"Asset {selected_asset.uuid}")
            else:
                # List all series (keep this behavior)
                series_list = library_service.list_series()
                
                if not series_list:
                    typer.echo("No series found", err=True)
                    raise typer.Exit(1)
                
                if json:
                    import json as json_module
                    typer.echo(json_module.dumps({"series": series_list}, indent=2))
                else:
                    typer.echo("Available series:")
                    for series_name in series_list:
                        typer.echo(f"  {series_name}")
                        
        except Exception as e:
            typer.echo(f"Error listing series: {e}", err=True)
            raise typer.Exit(1)


@app.command("delete")
def delete_asset(
    uuid: Optional[str] = typer.Option(None, "--uuid", help="Asset UUID to delete"),
    id: Optional[int] = typer.Option(None, "--id", help="Asset ID to delete"),
    source: Optional[str] = typer.Option(None, "--source", help="Source provider (e.g., plex)"),
    rating_key: Optional[str] = typer.Option(None, "--rating-key", help="Source rating key"),
    hard: bool = typer.Option(False, "--hard", help="Perform hard delete (permanent removal)"),
    force: bool = typer.Option(False, "--force", help="Force hard delete even if referenced"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would happen without making changes"),
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation prompt"),
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Delete an asset (soft delete by default, hard delete with --hard).
    
    Examples:
        retrovue assets delete --uuid a17d9...
        retrovue assets delete --id 42 --dry-run
        retrovue assets delete --source plex --rating-key 12345 --hard
        retrovue assets delete --uuid a17d9... --hard --force
    """
    with session() as db:
        library_service = LibraryService(db)
        
        try:
            # Validate selector arguments
            selector_count = sum(1 for x in [uuid, id, (source and rating_key)] if x)
            if selector_count == 0:
                typer.echo("Error: Must specify one selector: --uuid, --id, or --source + --rating-key", err=True)
                raise typer.Exit(1)
            if selector_count > 1:
                typer.echo("Error: Can only specify one selector", err=True)
                raise typer.Exit(1)
            
            # Find asset
            asset = None
            if uuid:
                try:
                    asset_uuid = UUID(uuid)
                    asset = library_service.get_asset_by_id(asset_uuid, include_deleted=True)
                except ValueError:
                    typer.echo(f"Error: Invalid UUID format: {uuid}", err=True)
                    raise typer.Exit(1)
            elif id:
                asset = library_service.get_asset_by_id(id, include_deleted=True)
            elif source and rating_key:
                if source.lower() != "plex":
                    typer.echo(f"Error: Unsupported source: {source}", err=True)
                    raise typer.Exit(1)
                asset = library_service.get_asset_by_source_rating_key(rating_key)
            
            if not asset:
                typer.echo("Error: Asset not found", err=True)
                raise typer.Exit(1)
            
            # Check if already soft deleted (for soft delete)
            if not hard and asset.is_deleted:
                typer.echo("Asset is already soft-deleted", err=True)
                raise typer.Exit(1)
            
            # Check references for hard delete
            referenced = False
            if hard:
                referenced = library_service.is_asset_referenced_by_episodes(asset.id)
            
            # Prepare result data
            result = {
                "action": "hard_delete" if hard else "soft_delete",
                "uuid": str(asset.uuid),
                "id": str(asset.id),
                "referenced": referenced
            }
            
            # Dry run mode
            if dry_run:
                if json:
                    import json as json_module
                    typer.echo(json_module.dumps(result, indent=2))
                else:
                    action = "hard delete" if hard else "soft delete"
                    typer.echo(f"Would {action} asset {asset.uuid} (id={asset.id})")
                    typer.echo(f"referenced_by_episodes={referenced}")
                return
            
            # Confirmation for hard delete
            if hard and not force and referenced:
                typer.echo(f"Refused hard delete: asset is referenced by episodes. Use --force to override or perform a soft delete.", err=True)
                raise typer.Exit(1)
            
            # Confirmation prompt
            if not yes and not dry_run:
                action = "hard delete" if hard else "soft delete"
                if hard and referenced:
                    typer.echo(f"Warning: Asset is referenced by episodes. This will cascade delete related records.")
                confirm = typer.confirm(f"Are you sure you want to {action} asset {asset.uuid}?")
                if not confirm:
                    typer.echo("Operation cancelled")
                    return
            
            # Perform deletion
            if hard:
                success = library_service.hard_delete_asset_by_uuid(asset.uuid, force=force)
            else:
                success = library_service.soft_delete_asset_by_uuid(asset.uuid)
            
            if success:
                if json:
                    result["status"] = "ok"
                    import json as json_module
                    typer.echo(json_module.dumps(result, indent=2))
                else:
                    action = "hard deleted" if hard else "soft deleted"
                    typer.echo(f"Asset {asset.uuid} {action} successfully")
            else:
                typer.echo("Error: Failed to delete asset", err=True)
                raise typer.Exit(1)
                
        except ValueError as e:
            if "referenced by episodes" in str(e):
                typer.echo(f"Error: {e}", err=True)
                typer.echo("Use --force to override or perform a soft delete instead", err=True)
            else:
                typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"Error deleting asset: {e}", err=True)
            raise typer.Exit(1)


@app.command("restore")
def restore_asset(
    uuid: str = typer.Argument(..., help="Asset UUID to restore"),
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Restore a soft-deleted asset.
    
    Examples:
        retrovue assets restore a17d9...
        retrovue assets restore a17d9... --json
    """
    with session() as db:
        library_service = LibraryService(db)
        
        try:
            asset_uuid = UUID(uuid)
            success = library_service.restore_asset_by_uuid(asset_uuid)
            
            if success:
                if json:
                    result = {
                        "action": "restore",
                        "uuid": uuid,
                        "status": "ok"
                    }
                    import json as json_module
                    typer.echo(json_module.dumps(result, indent=2))
                else:
                    typer.echo(f"Asset {uuid} restored successfully")
            else:
                typer.echo("Error: Asset not found or not soft-deleted", err=True)
                raise typer.Exit(1)
                
        except ValueError as e:
            typer.echo(f"Error: Invalid UUID format: {e}", err=True)
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"Error restoring asset: {e}", err=True)
            raise typer.Exit(1)
