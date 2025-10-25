"""
Ingest command group.

Surfaces content discovery and ingestion capabilities.
Calls IngestOrchestrator under the hood for all ingest operations.
"""

from __future__ import annotations

import typer
from typing import Optional, List

from ...infra.uow import session
from ...content_manager.ingest_orchestrator import IngestOrchestrator
from ...api.schemas import IngestResponse

app = typer.Typer(name="ingest", help="Content discovery and ingestion operations using IngestOrchestrator")


@app.command("run")
def run_ingest(
    collection_id: Optional[str] = typer.Argument(None, help="Collection ID for single-collection ingest"),
    source: Optional[str] = typer.Option(None, "--source", help="Source ID for bulk ingest"),
    enrichers: Optional[str] = typer.Option(None, "--enrichers", help="Comma-separated list of enrichers (e.g., 'ffprobe')"),
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Run content ingestion.
    
    Two modes:
    1. Single collection: retrovue ingest run <collection_id>
    2. Bulk ingest: retrovue ingest run --source <source_id>
    
    Examples:
        retrovue ingest run collection-movies-1
        retrovue ingest run --source "My Plex Server"
    """
    # Validate arguments
    if not collection_id and not source:
        typer.echo("Error: Either collection_id or --source must be provided", err=True)
        raise typer.Exit(1)
    
    if collection_id and source:
        typer.echo("Error: Cannot specify both collection_id and --source", err=True)
        raise typer.Exit(1)
    
    # Parse enrichers
    enricher_list = []
    if enrichers:
        enricher_list = [e.strip() for e in enrichers.split(",") if e.strip()]
    
    with session() as db:
        orchestrator = IngestOrchestrator(db)
        
        try:
            if collection_id:
                # Single collection ingest
                typer.echo(f"TODO: Validate collection {collection_id} is sync_enabled")
                typer.echo(f"TODO: Check local_path is set and reachable")
                typer.echo(f"TODO: Call importer for collection {collection_id}")
                typer.echo(f"TODO: Apply ingest-scope enrichers in priority order")
                typer.echo(f"TODO: Store enriched assets in catalog")
                
                # For now, just echo success
                if json:
                    import json
                    result = {
                        "collection_id": collection_id,
                        "enrichers": enricher_list,
                        "status": "completed",
                        "message": "TODO: implement actual ingest logic"
                    }
                    typer.echo(json.dumps(result, indent=2))
                else:
                    typer.echo(f"Ingest completed for collection: {collection_id}")
                    typer.echo("TODO: Show actual progress and results")
            else:
                # Bulk ingest from source
                typer.echo(f"TODO: Find all collections under source {source} where sync_enabled=true")
                typer.echo(f"TODO: Check local_path is valid/reachable for each collection")
                typer.echo(f"TODO: Run ingest for each valid collection")
                typer.echo(f"TODO: Show progress for each collection and overall summary")
                
                # For now, just echo success
                if json:
                    import json
                    result = {
                        "source": source,
                        "enrichers": enricher_list,
                        "status": "completed",
                        "message": "TODO: implement actual bulk ingest logic"
                    }
                    typer.echo(json.dumps(result, indent=2))
                else:
                    typer.echo(f"Bulk ingest completed for source: {source}")
                    typer.echo("TODO: Show actual progress and results")
                
        except Exception as e:
            typer.echo(f"Error running ingest: {e}", err=True)
            raise typer.Exit(1)
