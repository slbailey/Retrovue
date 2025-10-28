"""
Asset management commands for RetroVue infrastructure.
"""
import json

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from ...infra.admin_services import AssetAdminService

app = typer.Typer(help="Asset management operations")
console = Console()


@app.command()
def add(
    title: str = typer.Option(..., "--title", help="Asset title"),
    duration: int = typer.Option(..., "--duration", help="Duration in seconds"),
    tags: str = typer.Option(..., "--tags", help="Comma-separated tags"),
    path: str = typer.Option(..., "--path", help="File path"),
    canonical: bool = typer.Option(False, "--canonical", help="Canonical flag"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """Add a new asset."""
    try:
        tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        result = AssetAdminService.add_asset(
            title=title,
            duration_seconds=duration,
            tags=tags_list,
            file_path=path,
            canonical=canonical
        )
        
        if json_output:
            console.print(json.dumps(result, indent=2))
        else:
            rprint(f"[green]✓ Asset '{title}' added successfully[/green]")
            rprint(f"  ID: {result['id']}")
            rprint(f"  Duration: {result['duration_ms']}ms")
            rprint(f"  Tags: {result['tags']}")
            rprint(f"  Canonical: {result['canonical']}")
    except Exception as e:
        rprint(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def update(
    asset_id: int = typer.Option(..., "--id", help="Asset ID"),
    title: str | None = typer.Option(None, "--title", help="Asset title"),
    duration: int | None = typer.Option(None, "--duration", help="Duration in seconds"),
    tags: str | None = typer.Option(None, "--tags", help="Comma-separated tags"),
    path: str | None = typer.Option(None, "--path", help="File path"),
    canonical: bool | None = typer.Option(None, "--canonical", help="Canonical flag"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """Update an existing asset."""
    try:
        # Parse tags if provided
        tags_list = None
        if tags:
            tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        result = AssetAdminService.update_asset(
            asset_id=asset_id,
            title=title,
            duration_seconds=duration,
            tags=tags_list,
            file_path=path,
            canonical=canonical
        )
        
        if json_output:
            console.print(json.dumps(result, indent=2))
        else:
            rprint(f"[green]✓ Asset {asset_id} updated successfully[/green]")
            rprint(f"  Title: {result['title']}")
            rprint(f"  Duration: {result['duration_ms']}ms")
            rprint(f"  Tags: {result['tags']}")
            rprint(f"  Canonical: {result['canonical']}")
    except ValueError as e:
        rprint(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]✗ Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list(
    canonical_only: bool | None = typer.Option(None, "--canonical-only", help="Show only canonical assets"),
    tag_filter: str | None = typer.Option(None, "--tag", help="Filter by tag"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """List assets with optional filtering."""
    try:
        result = AssetAdminService.list_assets(
            canonical_only=canonical_only,
            tag=tag_filter
        )
        
        if json_output:
            console.print(json.dumps(result, indent=2))
        else:
            if result:
                table = Table(title="Assets")
                table.add_column("ID", style="cyan")
                table.add_column("Title", style="magenta")
                table.add_column("Duration (ms)", style="green")
                table.add_column("Tags", style="yellow")
                table.add_column("Canonical", style="red")
                
                for asset in result:
                    table.add_row(
                        str(asset["id"]),
                        asset["title"],
                        str(asset["duration_ms"]),
                        asset["tags"],
                        "✓" if asset["canonical"] else "✗"
                    )
                
                console.print(table)
            else:
                rprint("[yellow]No assets found[/yellow]")
    except Exception as e:
        rprint(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)
