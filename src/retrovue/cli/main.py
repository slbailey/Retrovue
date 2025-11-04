"""
Main CLI application using Typer.

This module provides the command-line interface for Retrovue,
calling application services and outputting JSON when requested.
"""

from __future__ import annotations

import typer

# Ensure registry is populated
import retrovue.adapters.importers  # noqa: F401

from .commands import asset as asset_cmd
from .commands import channel, collection, enricher, producer, runtime, source

app = typer.Typer(help="RetroVue operator CLI")

# Add command groups
app.add_typer(source.app, name="source", help="Source and collection management operations")

# Add new command groups per CLI contract
app.add_typer(enricher.app, name="enricher", help="Enricher management operations")
app.add_typer(producer.app, name="producer", help="Producer management operations")
app.add_typer(collection.app, name="collection", help="Collection management operations")
app.add_typer(asset_cmd.app, name="asset", help="Asset inspection and review operations")
app.add_typer(channel.app, name="channel", help="Broadcast channel operations")
app.add_typer(runtime.app, name="runtime", help="Runtime diagnostics and validation operations")


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
