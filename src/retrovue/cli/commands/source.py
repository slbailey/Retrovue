"""
Source CLI commands for source and collection management.

Surfaces source and collection management capabilities including listing, configuration, and path mapping.
Calls SourceService under the hood for all source operations.
"""

from __future__ import annotations

import typer
from typing import Optional

from ...infra.uow import session
from ...content_manager.source_service import SourceService
from ...adapters.registry import get_importer, list_importers, get_enricher, list_enrichers, get_importer_help
from ...domain.entities import SourceCollection, PathMapping


def _redact_sensitive_config(config: dict) -> dict:
    """
    Redact sensitive information from configuration dictionaries.
    
    This function identifies and redacts any configuration values that could
    contain sensitive authentication data, tokens, or credentials for any
    type of content source (Plex, filesystem, API, etc.).
    
    Args:
        config: Configuration dictionary that may contain sensitive data
        
    Returns:
        Configuration dictionary with sensitive values redacted
    """
    redacted = config.copy()
    
    # Comprehensive list of sensitive key patterns
    sensitive_patterns = [
        'token', 'password', 'secret', 'key', 'auth', 'credential',
        'api_key', 'access_token', 'refresh_token', 'bearer', 'jwt',
        'private', 'sensitive', 'confidential', 'secure', 'pass',
        'login', 'user', 'username', 'email', 'account'
    ]
    
    # Redact any key that contains sensitive patterns
    for key in redacted:
        key_lower = key.lower()
        if any(pattern in key_lower for pattern in sensitive_patterns):
            redacted[key] = '***REDACTED***'
    
    return redacted

app = typer.Typer(name="source", help="Source and collection management operations using SourceService")


@app.command("list")
def list_sources(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    List all configured sources.
    
    Examples:
        retrovue source list
        retrovue source list --json
    """
    with session() as db:
        source_service = SourceService(db)
        
        try:
            sources = source_service.list_sources()
            
            if json_output:
                import json
                # Redact sensitive information in JSON output
                redacted_sources = []
                for source in sources:
                    source_dict = source.__dict__.copy()
                    if source_dict.get('config'):
                        source_dict['config'] = _redact_sensitive_config(source_dict['config'])
                    redacted_sources.append(source_dict)
                typer.echo(json.dumps(redacted_sources, indent=2))
            else:
                typer.echo(f"Found {len(sources)} configured sources:")
                for source in sources:
                    typer.echo(f"  - {source.name} ({source.kind})")
                    typer.echo(f"    External ID: {source.external_id}")
                    if source.config:
                        # Redact sensitive information like tokens
                        redacted_config = _redact_sensitive_config(source.config)
                        typer.echo(f"    Config: {redacted_config}")
                    typer.echo()
                    
        except Exception as e:
            typer.echo(f"Error listing sources: {e}", err=True)
            raise typer.Exit(1)


# Create a sub-app for asset groups (collections/directories)
asset_groups_app = typer.Typer()
app.add_typer(asset_groups_app, name="assets")

@asset_groups_app.command("list")
def list_asset_groups(
    source_id: str = typer.Argument(..., help="Source ID, name, or external ID"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    List asset groups (collections/directories) from a source.
    
    Examples:
        retrovue source assets list "My Plex Server"
        retrovue source assets list plex-5063d926 --json
    """
    try:
        with session() as db:
            source_service = SourceService(db)
            
            # Get the source
            source = source_service.get_source_by_id(source_id)
            if not source:
                typer.echo(f"Error: Source '{source_id}' not found", err=True)
                raise typer.Exit(1)
            
            # Get the importer for this source
            from ...adapters.registry import get_importer
            
            # Filter out enrichers from config as importers don't need them
            importer_config = {k: v for k, v in source.config.items() if k != 'enrichers'}
            importer = get_importer(source.kind, **importer_config)
            
            # Get asset groups from the importer
            asset_groups = importer.list_asset_groups()
            
            if json_output:
                typer.echo(json.dumps(asset_groups, indent=2))
            else:
                # Display as Rich table
                from rich.console import Console
                from rich.table import Table
                
                console = Console()
                table = Table(title=f"Asset Groups from {source.name}")
                table.add_column("Name", style="green")
                table.add_column("Path", style="blue")
                table.add_column("Type", style="cyan")
                table.add_column("Asset Count", style="yellow")
                table.add_column("Enabled", style="magenta")
                
                for group in asset_groups:
                    table.add_row(
                        group.get("name", "Unknown"),
                        group.get("path", "Unknown"),
                        group.get("type", "Unknown"),
                        str(group.get("asset_count", "Unknown")),
                        "Yes" if group.get("enabled", False) else "No"
                    )
                
                console.print(table)
                
    except Exception as e:
        typer.echo(f"Error listing asset groups: {e}", err=True)
        raise typer.Exit(1)


@app.command("add")
def add_source(
    type: Optional[str] = typer.Option(None, "--type", help="Source type (plex, filesystem, etc.)"),
    name: Optional[str] = typer.Option(None, "--name", help="Friendly name for the source"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Base URL for the source"),
    token: Optional[str] = typer.Option(None, "--token", help="Authentication token"),
    base_path: Optional[str] = typer.Option(None, "--base-path", help="Base filesystem path to scan"),
    enrichers: Optional[str] = typer.Option(None, "--enrichers", help="Comma-separated list of enrichers to use"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    help_type: bool = typer.Option(False, "--help", help="Show help for the specified source type"),
):
    """
    Add a new content source to the repository for content discovery.
    
    This command adds a specific ingest source to the repository. Valid types are:
    
    • Plex - Connect to Plex Media Server instances
    • filesystem - Scan local filesystem directories for media files
    
    For detailed help on parameters for each type, use:
        retrovue source add --type plex --help
        retrovue source add --type filesystem --help
    
    Quick examples:
        retrovue source add --type plex --name "My Plex Server" --base-url "http://192.168.1.100:32400" --token "your-plex-token"
        retrovue source add --type filesystem --name "My Media Library" --base-path "/media/movies"
    """
    try:
        # Handle case where no type is provided
        if not type:
            typer.echo("Error: --type is required")
            typer.echo()
            typer.echo("Available source types:")
            available_importers = list_importers()
            for importer in available_importers:
                typer.echo(f"  • {importer}")
            typer.echo()
            typer.echo("For detailed help on each type, use:")
            for importer in available_importers:
                typer.echo(f"  retrovue source add --type {importer} --help")
            raise typer.Exit(1)
        
        # Get available importers
        available_importers = list_importers()
        if type not in available_importers:
            typer.echo(f"Error: Unknown source type '{type}'. Available types: {', '.join(available_importers)}", err=True)
            raise typer.Exit(1)
        
        # Handle help request for specific type
        if help_type:
            # Get help information for the importer
            help_info = get_importer_help(type)
            
            typer.echo(f"Help for {type} source type:")
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
        
        # Build configuration based on source type
        config = {}
        
        if type == "plex":
            if not base_url:
                typer.echo("Error: --base-url is required for Plex sources", err=True)
                raise typer.Exit(1)
            if not token:
                typer.echo("Error: --token is required for Plex sources", err=True)
                raise typer.Exit(1)
            config.update({
                "servers": [{"base_url": base_url, "token": token}]
            })
        elif type == "filesystem":
            if not base_path:
                typer.echo("Error: --base-path is required for filesystem sources", err=True)
                raise typer.Exit(1)
            config.update({
                "source_name": name,
                "root_paths": [base_path]
            })
        
        # Parse enrichers
        enricher_list = []
        if enrichers:
            available_enrichers = [e.name for e in list_enrichers()]
            enricher_list = [e.strip() for e in enrichers.split(",") if e.strip()]
            for enricher in enricher_list:
                if enricher not in available_enrichers:
                    typer.echo(f"Warning: Unknown enricher '{enricher}'. Available: {', '.join(available_enrichers)}", err=True)
        
        # Create the importer instance to validate configuration
        importer = get_importer(type, **config)
        
        # Now actually create and save the source in the database
        with session() as db:
            source_service = SourceService(db)
            
            # Create the source entity
            import uuid
            from ...domain.entities import Source
            
            external_id = f"{type}-{uuid.uuid4().hex[:8]}"
            
            # Build the database config
            db_config = config.copy()
            if type == "plex":
                # For Plex, store the server configuration
                db_config = {"servers": config.get("servers", [])}
            elif type == "filesystem":
                # For filesystem, store the path configuration
                db_config = {"root_paths": config.get("root_paths", [])}
            
            source = Source(
                external_id=external_id,
                name=name,
                kind=type,
                config=db_config
            )
            
            db.add(source)
            db.commit()
            db.refresh(source)
            
            # For Plex sources, automatically discover and persist collections
            if type == "plex":
                typer.echo("Discovering collections from Plex server...")
                collections = source_service.discover_collections(source.external_id)
                if collections:
                    success = source_service.persist_collections(source.external_id, collections)
                    if success:
                        typer.echo(f"  Discovered and persisted {len(collections)} collections (all disabled by default)")
                    else:
                        typer.echo("  Warning: Failed to persist collections", err=True)
                else:
                    typer.echo("  No collections found on Plex server")
            
            if json_output:
                import json
                result = {
                    "id": str(source.id),
                    "external_id": source.external_id,
                    "name": source.name,
                    "type": source.kind,
                    "config": source.config,
                    "enrichers": enricher_list,
                    "importer_name": importer.name
                }
                typer.echo(json.dumps(result, indent=2))
            else:
                typer.echo(f"Successfully created {type} source: {name}")
                typer.echo(f"  ID: {source.id}")
                typer.echo(f"  External ID: {source.external_id}")
                typer.echo(f"  Type: {type}")
                typer.echo(f"  Importer: {importer.name}")
                if enricher_list:
                    typer.echo(f"  Enrichers: {', '.join(enricher_list)}")
                typer.echo(f"  Configuration: {source.config}")
                
    except Exception as e:
        typer.echo(f"Error adding source: {e}", err=True)
        raise typer.Exit(1)




@app.command("list-types")
def list_source_types(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    List all available source types (importers).
    
    Examples:
        retrovue source list-types
        retrovue source list-types --json
    """
    try:
        available_importers = list_importers()
        available_enrichers = [e.name for e in list_enrichers()]
        
        if json_output:
            import json
            result = {
                "importers": available_importers,
                "enrichers": available_enrichers
            }
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo("Available source types:")
            for importer in available_importers:
                typer.echo(f"  - {importer}")
            
            typer.echo("\nAvailable enrichers:")
            for enricher in available_enrichers:
                typer.echo(f"  - {enricher}")
                
    except Exception as e:
        typer.echo(f"Error listing source types: {e}", err=True)
        raise typer.Exit(1)


@app.command("show")
def show_source(
    source_id: str = typer.Argument(..., help="Source ID, external ID, or name to show"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Show details for a specific source.
    
    Examples:
        retrovue source show "My Plex Server"
        retrovue source show filesystem-4807c63e
        retrovue source show 4b2b05e7-d7d2-414a-a587-3f5df9b53f44 --json
    """
    with session() as db:
        source_service = SourceService(db)
        
        try:
            source = source_service.get_source_by_id(source_id)
            if not source:
                typer.echo(f"Error: Source '{source_id}' not found", err=True)
                raise typer.Exit(1)
            
            if json_output:
                import json
                typer.echo(json.dumps(source.model_dump(), indent=2))
            else:
                typer.echo(f"Source Details:")
                typer.echo(f"  ID: {source.id}")
                typer.echo(f"  External ID: {source.external_id}")
                typer.echo(f"  Name: {source.name}")
                typer.echo(f"  Type: {source.kind}")
                typer.echo(f"  Status: {source.status}")
                if source.base_url:
                    typer.echo(f"  Base URL: {source.base_url}")
                if source.config:
                    typer.echo(f"  Configuration: {source.config}")
                    
        except Exception as e:
            typer.echo(f"Error showing source: {e}", err=True)
            raise typer.Exit(1)


@app.command("update")
def update_source(
    source_id: str = typer.Argument(..., help="Source ID, external ID, or name to update"),
    name: Optional[str] = typer.Option(None, "--name", help="New name for the source"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="New base URL for the source"),
    token: Optional[str] = typer.Option(None, "--token", help="New authentication token"),
    base_path: Optional[str] = typer.Option(None, "--base-path", help="New base filesystem path"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Update a source configuration.
    
    Examples:
        retrovue source update "My Plex Server" --name "Updated Plex Server"
        retrovue source update filesystem-4807c63e --name "Updated Media Library"
        retrovue source update "Test Plex" --base-url "http://new-plex:32400" --token "new-token"
    """
    with session() as db:
        source_service = SourceService(db)
        
        try:
            # Get current source to determine type
            current_source = source_service.get_source_by_id(source_id)
            if not current_source:
                typer.echo(f"Error: Source '{source_id}' not found", err=True)
                raise typer.Exit(1)
            
            # Build update configuration
            updates = {}
            new_config = current_source.config.copy() if current_source.config else {}
            
            if name:
                updates["name"] = name
            
            if current_source.kind == "plex":
                if base_url:
                    new_config["servers"] = [{"base_url": base_url, "token": new_config.get("servers", [{}])[0].get("token", "")}]
                if token:
                    if "servers" not in new_config:
                        new_config["servers"] = [{"base_url": "", "token": ""}]
                    new_config["servers"][0]["token"] = token
                if new_config:
                    updates["config"] = new_config
                    
            elif current_source.kind == "filesystem":
                if base_path:
                    new_config["root_paths"] = [base_path]
                if new_config:
                    updates["config"] = new_config
            
            if not updates:
                typer.echo("No updates provided", err=True)
                raise typer.Exit(1)
            
            # Update the source
            updated_source = source_service.update_source(source_id, **updates)
            if not updated_source:
                typer.echo(f"Error: Failed to update source '{source_id}'", err=True)
                raise typer.Exit(1)
            
            if json_output:
                import json
                typer.echo(json.dumps(updated_source.model_dump(), indent=2))
            else:
                typer.echo(f"Successfully updated source: {updated_source.name}")
                typer.echo(f"  ID: {updated_source.id}")
                typer.echo(f"  Type: {updated_source.kind}")
                if updated_source.base_url:
                    typer.echo(f"  Base URL: {updated_source.base_url}")
                if updated_source.config:
                    typer.echo(f"  Configuration: {updated_source.config}")
                    
        except Exception as e:
            typer.echo(f"Error updating source: {e}", err=True)
            raise typer.Exit(1)


@app.command("delete")
def delete_source(
    source_id: str = typer.Argument(..., help="Source ID, external ID, or name to delete"),
    force: bool = typer.Option(False, "--force", help="Force deletion without confirmation"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Delete a source.
    
    Examples:
        retrovue source delete "My Plex Server"
        retrovue source delete filesystem-4807c63e --force
        retrovue source delete 4b2b05e7-d7d2-414a-a587-3f5df9b53f44
    """
    with session() as db:
        source_service = SourceService(db)
        
        try:
            # Get source details for confirmation
            source = source_service.get_source_by_id(source_id)
            if not source:
                typer.echo(f"Error: Source '{source_id}' not found", err=True)
                raise typer.Exit(1)
            
            if not force:
                # Count related data to show user what will be deleted
                collections_count = db.query(SourceCollection).filter(SourceCollection.source_id == source.id).count()
                path_mappings_count = 0
                for collection in db.query(SourceCollection).filter(SourceCollection.source_id == source.id).all():
                    path_mappings_count += db.query(PathMapping).filter(PathMapping.collection_id == collection.id).count()
                
                typer.echo(f"Are you sure you want to delete source '{source.name}' (ID: {source.id})?")
                typer.echo("This will also delete:")
                typer.echo(f"  - {collections_count} collections")
                typer.echo(f"  - {path_mappings_count} path mappings")
                typer.echo("This action cannot be undone.")
                confirm = typer.prompt("Type 'yes' to confirm", default="no")
                if confirm.lower() != "yes":
                    typer.echo("Deletion cancelled")
                    raise typer.Exit(0)
            
            # Delete the source
            success = source_service.delete_source(source_id)
            if not success:
                typer.echo(f"Error: Failed to delete source '{source_id}'", err=True)
                raise typer.Exit(1)
            
            if json_output:
                import json
                result = {"deleted": True, "source_id": source_id, "name": source.name}
                typer.echo(json.dumps(result, indent=2))
            else:
                typer.echo(f"Successfully deleted source: {source.name}")
                typer.echo(f"  ID: {source.id}")
                typer.echo(f"  Type: {source.kind}")
                    
        except Exception as e:
            typer.echo(f"Error deleting source: {e}", err=True)
            raise typer.Exit(1)


@app.command("discover")
def discover_collections(
    source_id: str = typer.Argument(..., help="Source ID, external ID, or name to discover collections from"),
    persist: bool = typer.Option(False, "--persist", help="Persist discovered collections to database"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Discover collections (libraries) from a source.
    
    This scans the source for available collections/libraries and optionally
    persists them to the database for management.
    
    Examples:
        retrovue source discover "My Plex"
        retrovue source discover plex-5063d926 --persist
        retrovue source discover "My Plex" --persist --json
    """
    with session() as db:
        source_service = SourceService(db)
        
        try:
            # Get the source first to validate it exists
            source = source_service.get_source_by_id(source_id)
            if not source:
                typer.echo(f"Error: Source '{source_id}' not found", err=True)
                raise typer.Exit(1)
            
            # Discover collections from the source
            collections = source_service.discover_collections(source.external_id)
            
            if not collections:
                typer.echo(f"No collections found for source '{source.name}'")
                return
            
            if json_output:
                import json
                result = {
                    "source": {
                        "id": source.id,
                        "name": source.name,
                        "type": source.kind
                    },
                    "collections": [col.model_dump() for col in collections]
                }
                typer.echo(json.dumps(result, indent=2))
            else:
                typer.echo(f"Discovered {len(collections)} collections from '{source.name}':")
                for collection in collections:
                    typer.echo(f"  • {collection.name} (ID: {collection.external_id})")
                    typer.echo(f"    Type: {collection.config.get('type', 'unknown')}")
                    typer.echo(f"    Enabled: {collection.enabled}")
                    typer.echo()
            
            # Persist collections if requested
            if persist:
                typer.echo("Persisting collections to database...")
                success = source_service.persist_collections(source.external_id, collections)
                if success:
                    typer.echo(f"Successfully persisted {len(collections)} collections")
                else:
                    typer.echo("Error persisting collections", err=True)
                    raise typer.Exit(1)
                    
        except Exception as e:
            typer.echo(f"Error discovering collections: {e}", err=True)
            raise typer.Exit(1)


@asset_groups_app.command("enable")
def enable_asset_group(
    source_id: str = typer.Argument(..., help="Source ID, name, or external ID"),
    group_id: str = typer.Argument(..., help="Asset group ID to enable"),
):
    """
    Enable an asset group for content discovery.
    
    Examples:
        retrovue source assets enable "My Plex Server" "Movies"
        retrovue source assets enable plex-5063d926 "TV Shows"
    """
    try:
        with session() as db:
            source_service = SourceService(db)
            
            # Get the source
            source = source_service.get_source_by_id(source_id)
            if not source:
                typer.echo(f"Error: Source '{source_id}' not found", err=True)
                raise typer.Exit(1)
            
            # Get the importer for this source
            from ...adapters.registry import get_importer
            
            # Filter out enrichers from config as importers don't need them
            importer_config = {k: v for k, v in source.config.items() if k != 'enrichers'}
            importer = get_importer(source.kind, **importer_config)
            
            # Enable the asset group
            success = importer.enable_asset_group(group_id)
            
            if success:
                typer.echo(f"Asset group '{group_id}' enabled successfully")
            else:
                typer.echo(f"Error: Failed to enable asset group '{group_id}'", err=True)
                raise typer.Exit(1)
                
    except Exception as e:
        typer.echo(f"Error enabling asset group: {e}", err=True)
        raise typer.Exit(1)


@asset_groups_app.command("disable")
def disable_asset_group(
    source_id: str = typer.Argument(..., help="Source ID, name, or external ID"),
    group_id: str = typer.Argument(..., help="Asset group ID to disable"),
):
    """
    Disable an asset group from content discovery.
    
    Examples:
        retrovue source assets disable "My Plex Server" "Movies"
        retrovue source assets disable plex-5063d926 "TV Shows"
    """
    try:
        with session() as db:
            source_service = SourceService(db)
            
            # Get the source
            source = source_service.get_source_by_id(source_id)
            if not source:
                typer.echo(f"Error: Source '{source_id}' not found", err=True)
                raise typer.Exit(1)
            
            # Get the importer for this source
            from ...adapters.registry import get_importer
            
            # Filter out enrichers from config as importers don't need them
            importer_config = {k: v for k, v in source.config.items() if k != 'enrichers'}
            importer = get_importer(source.kind, **importer_config)
            
            # Disable the asset group
            success = importer.disable_asset_group(group_id)
            
            if success:
                typer.echo(f"Asset group '{group_id}' disabled successfully")
            else:
                typer.echo(f"Error: Failed to disable asset group '{group_id}'", err=True)
                raise typer.Exit(1)
                
    except Exception as e:
        typer.echo(f"Error disabling asset group: {e}", err=True)
        raise typer.Exit(1)


@app.command("enrichers")
def update_enrichers(
    source_id: str = typer.Argument(..., help="Source ID, external ID, or name to update"),
    enrichers: str = typer.Argument(..., help="Comma-separated list of enrichers to use"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Update enrichers for a source.
    
    Examples:
        retrovue source enrichers "My Plex" "ffprobe"
        retrovue source enrichers "My Plex" "ffprobe,metadata"
        retrovue source enrichers plex-5063d926 "ffprobe"
    """
    with session() as db:
        source_service = SourceService(db)
        
        try:
            # Parse enrichers
            enricher_list = [e.strip() for e in enrichers.split(",") if e.strip()]
            
            # Validate enrichers
            available_enrichers = [e.name for e in list_enrichers()]
            for enricher in enricher_list:
                if enricher not in available_enrichers:
                    typer.echo(f"Warning: Unknown enricher '{enricher}'. Available: {', '.join(available_enrichers)}", err=True)
            
            # Update enrichers
            success = source_service.update_source_enrichers(source_id, enricher_list)
            
            if success:
                if json_output:
                    import json
                    result = {
                        "source_id": source_id,
                        "enrichers": enricher_list
                    }
                    typer.echo(json.dumps(result, indent=2))
                else:
                    typer.echo(f"Successfully updated enrichers for source: {source_id}")
                    typer.echo(f"  Enrichers: {', '.join(enricher_list)}")
            else:
                typer.echo("Error updating enrichers", err=True)
                raise typer.Exit(1)
                
        except Exception as e:
            typer.echo(f"Error updating enrichers: {e}", err=True)
            raise typer.Exit(1)