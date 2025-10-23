"""
Ingest command group.

Handles content discovery and ingestion operations.
"""

from __future__ import annotations

import typer
from typing import Optional, List

from ..uow import session
from ...app.ingest_service import IngestService
from ...api.schemas import IngestResponse

app = typer.Typer(name="ingest", help="Content ingestion operations")


@app.command("run")
def run_ingest(
    source: str = typer.Argument(..., help="Source identifier (e.g., 'plex', 'filesystem:/path')"),
    library_id: Optional[str] = typer.Option(None, "--library-id", help="Library ID to process"),
    enrichers: Optional[str] = typer.Option(None, "--enrichers", help="Comma-separated list of enrichers (e.g., 'ffprobe')"),
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Run content ingestion from a source.
    
    Examples:
        retrovue ingest run --source plex --library-id 1
        retrovue ingest run --source filesystem:/path/to/media --enrichers ffprobe
    """
    # Parse enrichers
    enricher_list = []
    if enrichers:
        enricher_list = [e.strip() for e in enrichers.split(",") if e.strip()]
    
    with session() as db:
        ingest_service = IngestService(db)
        
        try:
            # Run the ingest
            counts = ingest_service.run_ingest(source)
            
            if json:
                import json
                response = IngestResponse(
                    source=source,
                    library_id=library_id,
                    enrichers=enricher_list,
                    counts=counts
                )
                typer.echo(json.dumps(response.model_dump(), indent=2))
            else:
                typer.echo(f"Ingest completed for source: {source}")
                typer.echo(f"Discovered: {counts['discovered']}")
                typer.echo(f"Registered: {counts['registered']}")
                typer.echo(f"Enriched: {counts['enriched']}")
                typer.echo(f"Canonicalized: {counts['canonicalized']}")
                typer.echo(f"Queued for review: {counts['queued_for_review']}")
                
        except Exception as e:
            typer.echo(f"Error running ingest: {e}", err=True)
            raise typer.Exit(1)
