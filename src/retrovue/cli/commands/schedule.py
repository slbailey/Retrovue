"""
Schedule management commands for RetroVue infrastructure.
"""
import json

import typer
from rich import print as rprint
from rich.console import Console

from ...infra.admin_services import ScheduleAdminService

app = typer.Typer(help="Schedule management operations")
console = Console()


@app.command()
def assign(
    channel: str = typer.Option(..., "--channel", help="Channel name"),
    template: str = typer.Option(..., "--template", help="Template name"),
    day: str = typer.Option(..., "--day", help="Schedule date (YYYY-MM-DD)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """Assign a template to a channel for a specific day."""
    try:
        result = ScheduleAdminService.assign_template_for_day(
            channel_name=channel,
            template_name=template,
            schedule_date=day
        )
        
        if json_output:
            console.print(json.dumps(result, indent=2))
        else:
            rprint(f"[green]✓ Template '{template}' assigned to channel '{channel}' for {day}[/green]")
            rprint(f"  Schedule ID: {result['id']}")
    except ValueError as e:
        rprint(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]✗ Unexpected error: {e}[/red]")
        raise typer.Exit(1)
