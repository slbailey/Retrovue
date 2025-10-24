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
        orchestrator = IngestOrchestrator(db)
        
        try:
            # Run the ingest using the new orchestrator
            report = orchestrator.run_full_ingest(source_id=source)
            
            if json:
                import json
                response = IngestResponse(
                    source=source,
                    library_id=library_id,
                    enrichers=enricher_list,
                    counts=report.to_dict()
                )
                typer.echo(json.dumps(response.model_dump(), indent=2))
            else:
                typer.echo(f"Ingest completed for source: {source}")
                typer.echo(f"Discovered: {report.discovered}")
                typer.echo(f"Registered: {report.registered}")
                typer.echo(f"Enriched: {report.enriched}")
                typer.echo(f"Canonicalized: {report.canonicalized}")
                typer.echo(f"Queued for review: {report.queued_for_review}")
                if report.errors > 0:
                    typer.echo(f"Errors: {report.errors}")
                
        except Exception as e:
            typer.echo(f"Error running ingest: {e}", err=True)
            raise typer.Exit(1)
