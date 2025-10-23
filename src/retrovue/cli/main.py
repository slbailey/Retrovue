"""
Main CLI application using Typer.

This module provides the command-line interface for Retrovue,
calling application services and outputting JSON when requested.
"""

from __future__ import annotations

import typer
from typing import Optional

from .uow import session
from .commands import ingest, assets, review, plex
# Ensure registry is populated
import retrovue.adapters.importers  # noqa: F401

app = typer.Typer(
    name="retrovue",
    help="Retrovue - Retro IPTV Simulation Project",
    no_args_is_help=True,
)

# Add command groups
app.add_typer(ingest.app, name="ingest", help="Content ingestion operations")
app.add_typer(assets.app, name="assets", help="Asset management operations") 
app.add_typer(review.app, name="review", help="Review queue operations")
app.add_typer(plex.app, name="plex", help="Plex server operations")

# Add play commands directly
from .play import play, play_channel
app.command("play")(play)
app.command("play-channel")(play_channel)


@app.callback()
def main(
    ctx: typer.Context,
    json: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Retrovue CLI - Retro IPTV Simulation Project."""
    # Store JSON flag in context for subcommands to use
    ctx.ensure_object(dict)
    ctx.obj["json"] = json


def cli():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
