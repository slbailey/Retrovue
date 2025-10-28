"""
Broadcast Catalog command group.

This manages the Scheduling Catalog: the set of airable, canonical-approved
assets that ScheduleService is allowed to schedule on-air.

This is NOT the ingest library. For ingest / metadata / UUID / Plex context,
use `retrovue assets ...`.

Only entries in this catalog (canonical=true) are eligible to be scheduled.
"""

import json

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from ...infra.admin_services import AssetAdminService

app = typer.Typer(
    name="catalog",
    help="Manage the broadcast catalog (airable, approved-for-scheduling assets)"
)

console = Console()


@app.command("add")
def add(
    title: str = typer.Option(..., "--title", help="Catalog title as it should appear on-air / in guide"),
    duration: int = typer.Option(..., "--duration", help="Duration in seconds"),
    tags: str = typer.Option(..., "--tags", help="Comma-separated tags used by scheduling rules (e.g. sitcom,retro)"),
    path: str = typer.Option(..., "--path", help="Playable file path"),
    canonical: bool = typer.Option(False, "--canonical", help="Mark as approved-for-air"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON instead of human text"),
):
    """
    Add a new catalog entry.

    This promotes content into the on-air catalog. Only canonical=true entries
    are eligible for scheduling by ScheduleService.

    Example:
        retrovue catalog add --title "Cheers S01E01" --duration 1440 \\
            --tags "sitcom" --path "/media/cheers01.mkv" --canonical true
    """
    try:
        tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        result = AssetAdminService.add_asset(
            title=title,
            duration_seconds=duration,
            tags=tags_list,
            file_path=path,
            canonical=canonical,
        )

        if json_output:
            console.print(json.dumps(result, indent=2))
        else:
            rprint("[green]✓ Catalog entry created[/green]")
            rprint(f"  ID: {result['id']}")
            rprint(f"  Title: {result['title']}")
            rprint(f"  Duration: {result['duration_ms']}ms")
            rprint(f"  Tags: {result['tags']}")
            rprint(f"  Canonical (approved): {result['canonical']}")

    except Exception as e:
        rprint(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)


@app.command("update")
def update(
    catalog_id: int = typer.Option(..., "--id", help="Catalog ID"),
    title: str | None = typer.Option(None, "--title", help="Updated title"),
    duration: int | None = typer.Option(None, "--duration", help="Updated duration in seconds"),
    tags: str | None = typer.Option(None, "--tags", help="Updated comma-separated tags"),
    path: str | None = typer.Option(None, "--path", help="Updated file path"),
    canonical: bool | None = typer.Option(None, "--canonical", help="Updated canonical status"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """
    Update an existing catalog entry.

    This is how you change approval state (canonical true/false),
    fix metadata, or point to a corrected file path.

    Example:
        retrovue catalog update --id 12 --canonical false
    """
    try:
        tags_list = None
        if tags:
            tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        result = AssetAdminService.update_asset(
            asset_id=catalog_id,
            title=title,
            duration_seconds=duration,
            tags=tags_list,
            file_path=path,
            canonical=canonical,
        )

        if json_output:
            console.print(json.dumps(result, indent=2))
        else:
            rprint(f"[green]✓ Catalog entry {catalog_id} updated[/green]")
            rprint(f"  Title: {result['title']}")
            rprint(f"  Duration: {result['duration_ms']}ms")
            rprint(f"  Tags: {result['tags']}")
            rprint(f"  Canonical (approved): {result['canonical']}")

    except ValueError as e:
        rprint(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]✗ Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_cmd(
    canonical_only: bool | None = typer.Option(
        None,
        "--canonical-only",
        help="Only show assets that are approved for scheduling",
    ),
    tag_filter: str | None = typer.Option(
        None,
        "--tag",
        help="Filter by tag (e.g. sitcom)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output in JSON instead of table format",
    ),
):
    """
    List catalog entries.

    Use this to see what the scheduler is allowed to pull.
    This is NOT the ingest library view. See `retrovue assets ...` for that.

    Examples:
        retrovue catalog list
        retrovue catalog list --canonical-only
        retrovue catalog list --tag sitcom
        retrovue catalog list --json
    """
    try:
        result = AssetAdminService.list_assets(
            canonical_only=canonical_only,
            tag=tag_filter,
        )

        if json_output:
            console.print(json.dumps(result, indent=2))
        else:
            if result:
                table = Table(title="Broadcast Catalog (Airable Assets)")
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
                        "✓" if asset["canonical"] else "✗",
                    )

                console.print(table)
            else:
                rprint("[yellow]No catalog entries found[/yellow]")

    except Exception as e:
        rprint(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)
