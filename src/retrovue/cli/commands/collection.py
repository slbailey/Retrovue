"""
Collection CLI commands for collection management.

Surfaces collection management capabilities including listing, configuration, and enricher attachment.
"""

from __future__ import annotations

import typer
from typing import Optional

from ...infra.uow import session

app = typer.Typer(name="collection", help="Collection management operations")


@app.command("list")
def list_collections(
    source: str = typer.Option(..., "--source", help="Source ID to list collections for"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Show Collections for a Source. For each:
    - collection_id
    - display_name
    - source_path
    - local_path (mapped path RetroVue will read)
    - sync_enabled (true/false)
    - ingestable (derived from sync_enabled + path reachability)
    
    Examples:
        retrovue collection list --source "My Plex Server"
        retrovue collection list --source plex-5063d926 --json
    """
    try:
        # TODO: Replace with real collection listing logic
        collections = [
            {
                "collection_id": "collection-movies-1",
                "display_name": "Movies",
                "source_path": "/movies",
                "local_path": "/media/movies",
                "sync_enabled": True,
                "ingestable": True
            },
            {
                "collection_id": "collection-tv-1",
                "display_name": "TV Shows", 
                "source_path": "/tv",
                "local_path": "/media/tv",
                "sync_enabled": False,
                "ingestable": False
            }
        ]
        
        if json_output:
            import json
            typer.echo(json.dumps(collections, indent=2))
        else:
            typer.echo(f"Collections for source '{source}':")
            for collection in collections:
                typer.echo(f"  - {collection['collection_id']}: {collection['display_name']}")
                typer.echo(f"    Source Path: {collection['source_path']}")
                typer.echo(f"    Local Path: {collection['local_path']}")
                typer.echo(f"    Sync Enabled: {collection['sync_enabled']}")
                typer.echo(f"    Ingestable: {collection['ingestable']}")
                typer.echo()
                
    except Exception as e:
        typer.echo(f"Error listing collections: {e}", err=True)
        raise typer.Exit(1)


@app.command("update")
def update_collection(
    collection_id: str = typer.Argument(..., help="Collection ID to update"),
    sync_enabled: Optional[bool] = typer.Option(None, "--sync-enabled", help="Enable or disable collection sync"),
    local_path: Optional[str] = typer.Option(None, "--local-path", help="Override local path mapping"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Enable/disable ingest for that Collection. Configure or change the local path mapping for that Collection.
    
    Parameters:
    - --sync-enabled: Enable or disable collection sync
    - --local-path: Override local path mapping
    
    Examples:
        retrovue collection update collection-movies-1 --sync-enabled true
        retrovue collection update collection-tv-1 --local-path /new/path
    """
    try:
        # TODO: Implement actual collection update logic
        updates = {}
        if sync_enabled is not None:
            updates["sync_enabled"] = sync_enabled
        if local_path is not None:
            updates["local_path"] = local_path
            
        if not updates:
            typer.echo("No updates provided", err=True)
            raise typer.Exit(1)
        
        if json_output:
            import json
            result = {
                "collection_id": collection_id,
                "updates": updates,
                "status": "updated"
            }
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo(f"Successfully updated collection: {collection_id}")
            for key, value in updates.items():
                typer.echo(f"  {key}: {value}")
            typer.echo("TODO: implement actual update logic")
                
    except Exception as e:
        typer.echo(f"Error updating collection: {e}", err=True)
        raise typer.Exit(1)


@app.command("attach-enricher")
def attach_enricher(
    collection_id: str = typer.Argument(..., help="Target collection"),
    enricher_id: str = typer.Argument(..., help="Enricher to attach"),
    priority: int = typer.Option(..., "--priority", help="Priority order (lower numbers run first)"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Attach an ingest-scope enricher to this Collection.
    
    Parameters:
    - collection_id: Target collection
    - enricher_id: Enricher to attach
    - --priority: Priority order (lower numbers run first)
    
    Examples:
        retrovue collection attach-enricher collection-movies-1 enricher-ffprobe-1 --priority 1
    """
    try:
        # TODO: Implement actual enricher attachment logic
        if json_output:
            import json
            result = {
                "collection_id": collection_id,
                "enricher_id": enricher_id,
                "priority": priority,
                "status": "attached"
            }
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo(f"Successfully attached enricher {enricher_id} to collection {collection_id}")
            typer.echo(f"  Priority: {priority}")
            typer.echo("TODO: implement actual attachment logic")
                
    except Exception as e:
        typer.echo(f"Error attaching enricher: {e}", err=True)
        raise typer.Exit(1)


@app.command("detach-enricher")
def detach_enricher(
    collection_id: str = typer.Argument(..., help="Target collection"),
    enricher_id: str = typer.Argument(..., help="Enricher to detach"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Remove enricher from collection.
    
    Examples:
        retrovue collection detach-enricher collection-movies-1 enricher-ffprobe-1
    """
    try:
        # TODO: Implement actual enricher detachment logic
        if json_output:
            import json
            result = {
                "collection_id": collection_id,
                "enricher_id": enricher_id,
                "status": "detached"
            }
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo(f"Successfully detached enricher {enricher_id} from collection {collection_id}")
            typer.echo("TODO: implement actual detachment logic")
                
    except Exception as e:
        typer.echo(f"Error detaching enricher: {e}", err=True)
        raise typer.Exit(1)
