"""
Channel management commands for RetroVue infrastructure.
"""
import json
import typer
from rich.console import Console
from rich import print as rprint

from ...infra.db import init_db
from ...infra.admin_services import ChannelAdminService

app = typer.Typer(help="Channel management operations")
console = Console()


@app.command()
def init():
    """Initialize the database."""
    try:
        init_db()
        rprint("[green]✓ Database initialized successfully[/green]")
    except Exception as e:
        rprint(f"[red]✗ Failed to initialize database: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def add(
    name: str = typer.Option(..., "--name", help="Channel name"),
    timezone: str = typer.Option(..., "--timezone", help="Channel timezone"),
    grid_size: int = typer.Option(..., "--grid-size", help="Grid size in minutes"),
    offset: int = typer.Option(..., "--offset", help="Grid offset in minutes"),
    rollover: int = typer.Option(..., "--rollover", help="Rollover in minutes"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """Add a new channel."""
    try:
        result = ChannelAdminService.create_channel(
            name=name,
            timezone=timezone,
            grid_size_minutes=grid_size,
            grid_offset_minutes=offset,
            rollover_minutes=rollover
        )
        
        if json_output:
            console.print(json.dumps(result, indent=2))
        else:
            rprint(f"[green]✓ Channel '{name}' created successfully[/green]")
            rprint(f"  ID: {result['id']}")
            rprint(f"  Timezone: {result['timezone']}")
            rprint(f"  Grid Size: {result['grid_size_minutes']} minutes")
            rprint(f"  Offset: {result['grid_offset_minutes']} minutes")
            rprint(f"  Rollover: {result['rollover_minutes']} minutes")
    except ValueError as e:
        rprint(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]✗ Unexpected error: {e}[/red]")
        raise typer.Exit(1)
