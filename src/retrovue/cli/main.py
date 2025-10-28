"""
Main CLI application using Typer.

This module provides the command-line interface for Retrovue,
calling application services and outputting JSON when requested.
"""

from __future__ import annotations

import typer

# Ensure registry is populated
import retrovue.adapters.importers  # noqa: F401

from .commands import (
    asset,
    assets,
    catalog,
    channel,
    collection,
    enricher,
    plex,
    producer,
    review,
    schedule,
    source,
    template,
    test,
)
from .play import play, play_channel

app = typer.Typer(
    help="RetroVue operator CLI"
)

# Add command groups
app.add_typer(assets.app, name="assets")  # assets = ingest world
app.add_typer(catalog.app, name="catalog")  # catalog = broadcast world
app.add_typer(review.app, name="review", help="Review queue operations using LibraryService")
app.add_typer(plex.app, name="plex", help="Plex server operations using SourceService, LibraryService, and IngestOrchestrator")
app.add_typer(source.app, name="source", help="Source and collection management operations using SourceService")
app.add_typer(test.app, name="test", help="Testing operations for runtime components")

# Add bootstrap infrastructure command groups
app.add_typer(channel.app, name="channel", help="Channel management operations for infrastructure bootstrap")
app.add_typer(template.app, name="template", help="Template management operations for infrastructure bootstrap")
app.add_typer(schedule.app, name="schedule", help="Schedule management operations for infrastructure bootstrap")
app.add_typer(asset.app, name="asset", help="Asset management operations for infrastructure bootstrap")

# Add new command groups per CLI contract
app.add_typer(enricher.app, name="enricher", help="Enricher management operations")
app.add_typer(producer.app, name="producer", help="Producer management operations")
app.add_typer(collection.app, name="collection", help="Collection management operations")

# Add play commands directly
app.command("play")(play)
app.command("play-channel")(play_channel)


@app.callback()
def main(
    ctx: typer.Context,
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Retrovue - Retro IPTV Simulation Project."""
    # Store JSON flag in context for subcommands to use
    ctx.ensure_object(dict)
    ctx.obj["json"] = json


def cli():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
