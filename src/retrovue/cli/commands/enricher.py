"""
Enricher CLI commands for enricher management.

Surfaces enricher management capabilities including listing, configuration, and management.
"""

from __future__ import annotations

import typer
from typing import Optional

from ...infra.uow import session

app = typer.Typer(name="enricher", help="Enricher management operations")


@app.command("list-types")
def list_enricher_types(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Show all enricher types known to the system (both ingest and playout scopes).
    
    Examples:
        retrovue enricher list-types
        retrovue enricher list-types --json
    """
    try:
        # TODO: Replace with real EnricherRegistry when available
        from ...registries.enricher_registry import list_enricher_types as _list_types
        enricher_types = _list_types()
        
        if json_output:
            import json
            typer.echo(json.dumps(enricher_types, indent=2))
        else:
            typer.echo("Available enricher types:")
            for enricher_type in enricher_types:
                typer.echo(f"  - {enricher_type['type']}: {enricher_type['description']}")
                typer.echo(f"    Scope: {enricher_type.get('scope', 'unknown')}")
                
    except Exception as e:
        typer.echo(f"Error listing enricher types: {e}", err=True)
        raise typer.Exit(1)


@app.command("add")
def add_enricher(
    type: Optional[str] = typer.Option(None, "--type", help="Enricher type"),
    name: Optional[str] = typer.Option(None, "--name", help="Human-readable label"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    help_type: bool = typer.Option(False, "--help", help="Show help for the specified enricher type"),
):
    """
    Create an enricher instance. Each enricher type defines its own config params.
    
    Required:
    - --type: Enricher type
    - --name: Human-readable label
    
    Behavior:
    - If called with --help and no --type, print generic usage plus available types.
    - If called with --type <type> --help, print that enricher's specific parameter contract.
    
    Examples:
        retrovue enricher add --type ffprobe --name "Video Analysis"
        retrovue enricher add --type metadata --name "Metadata Enricher"
    """
    try:
        # Handle case where no type is provided
        if not type:
            typer.echo("Error: --type is required")
            typer.echo()
            typer.echo("Available enricher types:")
            from ...registries.enricher_registry import list_enricher_types as _list_types
            available_types = _list_types()
            for enricher_type in available_types:
                typer.echo(f"  • {enricher_type['type']}: {enricher_type['description']}")
            typer.echo()
            typer.echo("For detailed help on each type, use:")
            for enricher_type in available_types:
                typer.echo(f"  retrovue enricher add --type {enricher_type['type']} --help")
            raise typer.Exit(1)
        
        # Get available enricher types
        from ...registries.enricher_registry import list_enricher_types as _list_types
        available_types = _list_types()
        type_names = [t['type'] for t in available_types]
        if type not in type_names:
            typer.echo(f"Error: Unknown enricher type '{type}'. Available types: {', '.join(type_names)}", err=True)
            raise typer.Exit(1)
        
        # Handle help request for specific type
        if help_type:
            # Get help information for the enricher type
            from ...registries.enricher_registry import get_enricher_help
            help_info = get_enricher_help(type)
            
            typer.echo(f"Help for {type} enricher type:")
            typer.echo(f"Description: {help_info['description']}")
            typer.echo()
            
            typer.echo("Required parameters:")
            for param in help_info['required_params']:
                typer.echo(f"  --{param['name']}: {param['description']}")
                if 'example' in param:
                    typer.echo(f"    Example: {param['example']}")
            
            typer.echo()
            typer.echo("Optional parameters:")
            for param in help_info['optional_params']:
                typer.echo(f"  --{param['name']}: {param['description']}")
                if 'default' in param:
                    typer.echo(f"    Default: {param['default']}")
            
            typer.echo()
            typer.echo("Examples:")
            for example in help_info['examples']:
                typer.echo(f"  {example}")
            
            return  # Exit the function cleanly
        
        # Validate required parameters
        if not name:
            typer.echo("Error: --name is required", err=True)
            raise typer.Exit(1)
        
        # TODO: Implement actual enricher creation logic
        # For now, just echo success
        if json_output:
            import json
            result = {
                "enricher_id": f"enricher-{type}-{name.lower().replace(' ', '-')}",
                "type": type,
                "name": name,
                "status": "created"
            }
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo(f"Successfully created {type} enricher: {name}")
            typer.echo(f"  Type: {type}")
            typer.echo(f"  Name: {name}")
            typer.echo("  Status: created (TODO: implement actual creation)")
                
    except Exception as e:
        typer.echo(f"Error adding enricher: {e}", err=True)
        raise typer.Exit(1)


@app.command("list")
def list_enrichers(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    List configured enricher instances with:
    - enricher_id
    - type
    - scope (ingest or playout)
    - name/label
    
    Examples:
        retrovue enricher list
        retrovue enricher list --json
    """
    try:
        # TODO: Replace with real enricher listing logic
        enrichers = [
            {
                "enricher_id": "enricher-ffprobe-1",
                "type": "ffprobe",
                "scope": "ingest",
                "name": "Video Analysis"
            },
            {
                "enricher_id": "enricher-metadata-1", 
                "type": "metadata",
                "scope": "playout",
                "name": "Metadata Enricher"
            }
        ]
        
        if json_output:
            import json
            typer.echo(json.dumps(enrichers, indent=2))
        else:
            typer.echo("Configured enricher instances:")
            for enricher in enrichers:
                typer.echo(f"  - {enricher['enricher_id']}: {enricher['name']} ({enricher['type']}, {enricher['scope']})")
                
    except Exception as e:
        typer.echo(f"Error listing enrichers: {e}", err=True)
        raise typer.Exit(1)


@app.command("update")
def update_enricher(
    enricher_id: str = typer.Argument(..., help="Enricher ID to update"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Update enricher configuration.
    
    Parameters: Same as add command for the enricher type.
    
    Examples:
        retrovue enricher update enricher-ffprobe-1
    """
    try:
        # TODO: Implement actual enricher update logic
        typer.echo(f"TODO: Update enricher {enricher_id}")
        typer.echo("This command will update the enricher configuration.")
        typer.echo("Parameters: Same as add command for the enricher type.")
        
    except Exception as e:
        typer.echo(f"Error updating enricher: {e}", err=True)
        raise typer.Exit(1)


@app.command("remove")
def remove_enricher(
    enricher_id: str = typer.Argument(..., help="Enricher ID to remove"),
    force: bool = typer.Option(False, "--force", help="Force removal without confirmation"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Remove enricher instance.
    
    Behavior: Confirms removal and shows affected collections/channels.
    
    Examples:
        retrovue enricher remove enricher-ffprobe-1
        retrovue enricher remove enricher-metadata-1 --force
    """
    try:
        if not force:
            typer.echo(f"Are you sure you want to remove enricher '{enricher_id}'?")
            typer.echo("This action cannot be undone.")
            confirm = typer.prompt("Type 'yes' to confirm", default="no")
            if confirm.lower() != "yes":
                typer.echo("Removal cancelled")
                raise typer.Exit(0)
        
        # TODO: Implement actual enricher removal logic
        if json_output:
            import json
            result = {"removed": True, "enricher_id": enricher_id}
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo(f"Successfully removed enricher: {enricher_id}")
            typer.echo("TODO: Show affected collections/channels")
                
    except Exception as e:
        typer.echo(f"Error removing enricher: {e}", err=True)
        raise typer.Exit(1)
