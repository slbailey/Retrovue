"""
Template management commands for RetroVue infrastructure.
"""
import json
import typer
from typing import Optional
from rich.console import Console
from rich import print as rprint

from ...infra.admin_services import TemplateAdminService

app = typer.Typer(help="Template management operations")
console = Console()


@app.command()
def add(
    name: str = typer.Option(..., "--name", help="Template name"),
    description: Optional[str] = typer.Option(None, "--description", help="Template description"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """Add a new template."""
    try:
        result = TemplateAdminService.create_template(
            name=name,
            description=description
        )
        
        if json_output:
            console.print(json.dumps(result, indent=2))
        else:
            rprint(f"[green]✓ Template '{name}' created successfully[/green]")
            rprint(f"  ID: {result['id']}")
            if result['description']:
                rprint(f"  Description: {result['description']}")
    except ValueError as e:
        rprint(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]✗ Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def block(
    template_id: int = typer.Option(..., "--template-id", help="Template ID"),
    start: str = typer.Option(..., "--start", help="Start time (HH:MM)"),
    end: str = typer.Option(..., "--end", help="End time (HH:MM)"),
    tags: str = typer.Option(..., "--tags", help="Comma-separated tags"),
    episode_policy: str = typer.Option(..., "--episode-policy", help="Episode policy"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON")
):
    """Add a block to a template."""
    try:
        tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        result = TemplateAdminService.add_block(
            template_id=template_id,
            start_time=start,
            end_time=end,
            tags=tags_list,
            episode_policy=episode_policy
        )
        
        if json_output:
            console.print(json.dumps(result, indent=2))
        else:
            rprint(f"[green]✓ Block added to template {template_id}[/green]")
            rprint(f"  ID: {result['id']}")
            rprint(f"  Time: {result['start_time']} - {result['end_time']}")
            rprint(f"  Tags: {tags}")
            rprint(f"  Episode Policy: {episode_policy}")
    except Exception as e:
        rprint(f"[red]✗ Error: {e}[/red]")
        raise typer.Exit(1)
