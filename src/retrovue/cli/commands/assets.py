"""
Assets command group.

Surfaces Library Domain asset management capabilities including listing, selection, deletion, and promotion.
This is the Library Domain (ingest, QC, source metadata, promotion to broadcast catalog).

For Broadcast Domain operations (approved-for-air catalog used by ScheduleService), use the `catalog` commands.
"""

from __future__ import annotations

import typer
import json
import random
from typing import Optional
from enum import Enum
from uuid import UUID

from ...infra.uow import session
from ...api.schemas import AssetListResponse, AssetSummary
from ...content_manager.library_service import LibraryService
from ...domain.entities import ProviderRef, EntityType
from ...infra.admin_services import AssetAdminService

app = typer.Typer(name="assets", help="Library Domain asset management (ingest, QC, source metadata, promotion)")


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
    canonical_only: bool = typer.Option(False, "--canonical-only", help="Show only canonical (approved) assets"),
    include_pending: bool = typer.Option(False, "--include-pending", help="Include pending (non-canonical) assets"),
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    List assets with optional status filtering.
    
    **Canonical Status:**
    - canonical=True: Asset is approved for use by downstream schedulers and runtime
    - canonical=False: Asset exists in inventory but is not yet approved; may be in review_queue
    
    Examples:
        retrovue assets list
        retrovue assets list --status pending
        retrovue assets list --status canonical --json
        retrovue assets list --canonical-only
        retrovue assets list --include-pending
    """
    with session() as db:
        library_service = LibraryService(db)
        
        try:
            # Handle flag conflicts
            if canonical_only and include_pending:
                typer.echo("Error: --canonical-only and --include-pending are mutually exclusive", err=True)
                raise typer.Exit(1)
            
            # Get assets based on status filter and flags
            if canonical_only:
                assets = library_service.list_canonical_assets()
            elif include_pending:
                assets = library_service.list_pending_assets()
            elif status == AssetStatus.ALL:
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
                canonical_count = sum(1 for asset in asset_summaries if asset.canonical)
                pending_count = len(asset_summaries) - canonical_count
                
                typer.echo(f"Found {len(asset_summaries)} assets")
                typer.echo(f"  Canonical (approved): {canonical_count}")
                typer.echo(f"  Pending (not approved): {pending_count}")
                typer.echo()
                
                for asset in asset_summaries:
                    status_str = "✅ CANONICAL" if asset.canonical else "⏳ PENDING"
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
    canonical_only: bool = typer.Option(False, "--canonical-only", help="Show only canonical (approved) assets"),
    include_pending: bool = typer.Option(False, "--include-pending", help="Include pending (non-canonical) assets"),
    limit: int = typer.Option(50, "--limit", help="Maximum number of results"),
    offset: int = typer.Option(0, "--offset", help="Number of results to skip"),
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    List assets with advanced filtering options.
    
    **Canonical Status:**
    - canonical=True: Asset is approved for use by downstream schedulers and runtime
    - canonical=False: Asset exists in inventory but is not yet approved; may be in review_queue
    
    Examples:
        retrovue assets list-advanced --kind episode --series "Batman TAS"
        retrovue assets list-advanced --season 1 --limit 10
        retrovue assets list-advanced --q "pilot" --json
        retrovue assets list-advanced --canonical-only --series "Batman TAS"
        retrovue assets list-advanced --include-pending --kind episode
    """
    with session() as db:
        library_service = LibraryService(db)
        
        try:
            # Handle flag conflicts
            if canonical_only and include_pending:
                typer.echo("Error: --canonical-only and --include-pending are mutually exclusive", err=True)
                raise typer.Exit(1)
            
            assets = library_service.list_assets_advanced(
                kind=kind, series=series, season=season, q=q, limit=limit, offset=offset
            )
            
            # Apply canonical filtering if requested
            if canonical_only:
                assets = [asset for asset in assets if asset.canonical]
            elif include_pending:
                assets = [asset for asset in assets if not asset.canonical]
            
            if json:
                # Convert to response format
                asset_summaries = [AssetSummary.from_orm(asset) for asset in assets]
                response = AssetListResponse(
                    assets=asset_summaries,
                    total=len(asset_summaries)
                )
                typer.echo(response.model_dump_json(indent=2))
            else:
                # Print table format with canonical status
                canonical_count = sum(1 for asset in assets if asset.canonical)
                pending_count = len(assets) - canonical_count
                
                typer.echo(f"Found {len(assets)} assets")
                typer.echo(f"  Canonical (approved): {canonical_count}")
                typer.echo(f"  Pending (not approved): {pending_count}")
                typer.echo()
                typer.echo("UUID\t\tSTATUS\tKIND\tDURATION\tSERIES\tS\tE\tTITLE")
                typer.echo("-" * 100)
                
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
                    status_icon = "✅" if asset.canonical else "⏳"
                    typer.echo(f"{uuid_short}\t\t{status_icon}\t{kind}\t{duration}\t{series_title}\t{season_num}\t{episode_num}\t{title}")
                    
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
                canonical_status = "✅ CANONICAL (approved for broadcast)" if asset.canonical else "⏳ PENDING (not yet approved)"
                typer.echo(f"  Status: {canonical_status}")
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


@app.command("promote")
def promote_asset(
    uuid: str = typer.Option(..., "--uuid", help="Library asset UUID to promote"),
    title: str = typer.Option(..., "--title", help="Guide-facing title for broadcast catalog"),
    tags: str = typer.Option(..., "--tags", help="Comma-separated tags (e.g., 'sitcom,retro')"),
    canonical: bool = typer.Option(True, "--canonical", help="Whether this asset is canonical (approved for broadcast)"),
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Promote a library asset to the broadcast catalog.
    
    Promotion will fail if the asset is not technically playout-ready.
    Promotion does NOT automatically make it airable; canonical must be true AND scheduling must choose it.
    ScheduleService is forbidden to schedule non-canonical assets.
    
    Examples:
        retrovue assets promote --uuid 41dc6fd4-a9c1-4686-bec5-1cf7dfd03e4e --title "Batman: The Animated Series" --tags "sitcom,retro" --canonical true
        retrovue assets promote --uuid 41dc6fd4-a9c1-4686-bec5-1cf7dfd03e4e --title "Classic Episode" --tags "drama,classic" --canonical false
    """
    try:
        # Parse tags from comma-separated string
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Call the admin service to promote the asset
        result = AssetAdminService.promote_from_library(
            source_asset_uuid=uuid,
            title=title,
            tags=tag_list,
            canonical=canonical
        )
        
        if json:
            import json as json_module
            typer.echo(json_module.dumps(result, indent=2))
        else:
            from rich.console import Console
            from rich import print as rprint
            
            console = Console()
            console.print("✓ Promoted to Broadcast Catalog", style="green")
            console.print(f"  Catalog ID: {result['catalog_id']}")
            console.print(f"  Title: {result['title']}")
            console.print(f"  Canonical: {result['canonical']}")
            console.print(f"  Duration (ms): {result['duration_ms']}")
            console.print(f"  File: {result['file_path']}")
            
    except ValueError as e:
        from rich.console import Console
        console = Console()
        console.print(f"✗ Promotion failed: {e}", style="red")
        raise typer.Exit(1)
    except Exception as e:
        from rich.console import Console
        console = Console()
        console.print(f"✗ Error promoting asset: {e}", style="red")
        raise typer.Exit(1)