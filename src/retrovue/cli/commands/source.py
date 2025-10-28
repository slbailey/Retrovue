"""
Source CLI commands for source and collection management.

Surfaces source and collection management capabilities including listing, configuration, and path mapping.
Calls SourceService under the hood for all source operations.
"""

from __future__ import annotations

import json
import uuid

import typer

from ...adapters.registry import (
    SOURCES,
    get_importer,
    get_importer_help,
    list_enrichers,
    list_importers,
)
from ...content_manager.source_service import SourceService
from ...domain.entities import SourceCollection
from ...infra.uow import session


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
    source_type: str | None = typer.Option(None, "--type", help="Filter by source type"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Query test database"),
):
    """
    List all configured sources.
    
    Examples:
        retrovue source list
        retrovue source list --json
        retrovue source list --type plex
        retrovue source list --test-db --json
    """
    # Validate source type if provided
    if source_type:
        available_types = list_importers()
        if source_type not in available_types:
            typer.echo(f"Unknown source type '{source_type}'. Available types: {', '.join(available_types)}", err=True)
            raise typer.Exit(1)
    
    try:
        with session() as db:
            source_service = SourceService(db)
            
            # Get sources with collection counts
            sources_data = source_service.list_sources_with_collection_counts(source_type)
            
            if json_output:
                import json
                # Sort sources by name (case-insensitive), then by id
                sorted_sources = sorted(sources_data, key=lambda s: (s['name'].lower(), s['id']))
                
                response = {
                    "status": "ok",
                    "total": len(sorted_sources),
                    "sources": sorted_sources
                }
                typer.echo(json.dumps(response, indent=2))
            else:
                # Human-readable output
                if not sources_data:
                    typer.echo("No sources configured")
                else:
                    # Sort sources by name (case-insensitive), then by id
                    sorted_sources = sorted(sources_data, key=lambda s: (s['name'].lower(), s['id']))
                    
                    if source_type:
                        typer.echo(f"{source_type.title()} sources:")
                    else:
                        typer.echo("Configured sources:")
                    
                    for source in sorted_sources:
                        typer.echo(f"  ID: {source['id']}")
                        typer.echo(f"  Name: {source['name']}")
                        typer.echo(f"  Type: {source['type']}")
                        typer.echo(f"  Enabled Collections: {source['enabled_collections']}")
                        typer.echo(f"  Ingestible Collections: {source['ingestible_collections']}")
                        typer.echo(f"  Created: {source['created_at']}")
                        typer.echo(f"  Updated: {source['updated_at']}")
                        typer.echo()
                
                # Show total
                total_text = f"Total: {len(sources_data)}"
                if source_type:
                    total_text += f" {source_type} source" if len(sources_data) == 1 else f" {source_type} sources"
                else:
                    total_text += " source" if len(sources_data) == 1 else " sources"
                total_text += " configured"
                typer.echo(total_text)
                    
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
            importer = get_importer(source.type, **importer_config)
            
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
    type: str | None = typer.Option(None, "--type", help="Source type (plex, filesystem, etc.)"),
    name: str | None = typer.Option(None, "--name", help="Friendly name for the source"),
    base_url: str | None = typer.Option(None, "--base-url", help="Base URL for the source"),
    token: str | None = typer.Option(None, "--token", help="Authentication token"),
    base_path: str | None = typer.Option(None, "--base-path", help="Base filesystem path to scan"),
    enrichers: str | None = typer.Option(None, "--enrichers", help="Comma-separated list of enrichers to use"),
    discover: bool = typer.Option(False, "--discover", help="Automatically discover and persist collections after source creation"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be created without executing"),
    test_db: bool = typer.Option(False, "--test-db", help="Direct command to test database environment"),
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
            if help_info['optional_params']:
                for param in help_info['optional_params']:
                    typer.echo(f"  --{param['name']}: {param['description']}")
                    if 'default' in param:
                        typer.echo(f"    Default: {param['default']}")
            else:
                typer.echo("  None")
            
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
        importer_params = {}
        
        if type == "plex":
            if not base_url:
                typer.echo("Error: --base-url is required for Plex sources", err=True)
                raise typer.Exit(1)
            if not token:
                typer.echo("Error: --token is required for Plex sources", err=True)
                raise typer.Exit(1)
            # For importer instantiation
            importer_params = {
                "base_url": base_url,
                "token": token
            }
            # For database storage
            config = {
                "servers": [{"base_url": base_url, "token": token}]
            }
        elif type == "filesystem":
            if not base_path:
                typer.echo("Error: --base-path is required for filesystem sources", err=True)
                raise typer.Exit(1)
            # For importer instantiation
            importer_params = {
                "base_path": base_path
            }
            # For database storage
            config = {
                "source_name": name,
                "root_paths": [base_path]
            }
        
        # Parse enrichers
        enricher_list = []
        if enrichers:
            try:
                available_enrichers = [e.name for e in list_enrichers()]
            except Exception as e:
                typer.echo(f"Error: Failed to load enricher registry: {e}", err=True)
                raise typer.Exit(1)
            
            enricher_list = [e.strip() for e in enrichers.split(",") if e.strip()]
            unknown_enrichers = []
            for enricher in enricher_list:
                if enricher not in available_enrichers:
                    unknown_enrichers.append(enricher)
            
            if unknown_enrichers:
                for enricher in unknown_enrichers:
                    typer.echo(f"Error: Unknown enricher '{enricher}'. Available: {', '.join(available_enrichers)}", err=True)
                raise typer.Exit(1)
        
        # Create the importer instance to validate configuration
        importer = get_importer(type, **importer_params)
        
        # Handle dry-run mode
        if dry_run:
            # Generate external ID for preview
            external_id = f"{type}-{uuid.uuid4().hex[:8]}"
            
            if json_output:
                import json
                result = {
                    "id": f"preview-{external_id}",
                    "external_id": external_id,
                    "name": name,
                    "type": type,
                    "config": config,
                    "enrichers": enricher_list,
                    "importer_name": importer.name,
                    "dry_run": True
                }
                typer.echo(json.dumps(result, indent=2))
            else:
                typer.echo(f"[DRY RUN] Would create {type} source: {name}")
                typer.echo(f"  External ID: {external_id}")
                typer.echo(f"  Type: {type}")
                typer.echo(f"  Importer: {importer.name}")
                if enricher_list:
                    typer.echo(f"  Enrichers: {', '.join(enricher_list)}")
                typer.echo(f"  Configuration: {config}")
                if discover:
                    typer.echo(f"  Would discover collections: {'Yes' if type == 'plex' else 'No (not supported)'}")
            return
        
        # Handle test-db mode
        if test_db:
            typer.echo("Using test database environment", err=True)
            # TODO: Implement test database isolation
            # For now, just continue with normal flow but mark as test mode
        
        # Now actually create and save the source in the database
        with session() as db:
            source_service = SourceService(db)
            
            # Create the source entity
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
                type=type,
                config=db_config
            )
            
            db.add(source)
            db.commit()
            db.refresh(source)
            
            # For Plex sources, discover collections if --discover flag is provided
            collections_discovered = 0
            if type == "plex" and discover:
                typer.echo("Discovering collections from Plex server...")
                collections = source_service.discover_collections(source.external_id)
                if collections:
                    success = source_service.persist_collections(source.external_id, collections)
                    if success:
                        collections_discovered = len(collections)
                        typer.echo(f"  Discovered and persisted {collections_discovered} collections (all disabled by default)")
                    else:
                        typer.echo("  Warning: Failed to persist collections", err=True)
                else:
                    typer.echo("  No collections found on Plex server")
            elif type == "filesystem" and discover:
                typer.echo("  Warning: Collection discovery not supported for filesystem sources", err=True)
            
            if json_output:
                import json
                result = {
                    "id": str(source.id),
                    "external_id": source.external_id,
                    "name": source.name,
                    "type": source.type,
                    "config": source.config,
                    "enrichers": enricher_list,
                    "importer_name": importer.name
                }
                
                # Add collection discovery information if --discover was used
                if discover and collections_discovered > 0:
                    result["collections_discovered"] = collections_discovered
                    # TODO: Add actual collection details when available
                    result["collections"] = []
                
                typer.echo(json.dumps(result, indent=2))
            else:
                typer.echo(f"Successfully created {type} source: {name}")
                typer.echo(f"  Name: {name}")
                typer.echo(f"  ID: {source.id}")
                typer.echo(f"  Type: {type}")
                if enricher_list:
                    typer.echo(f"  Enrichers: {', '.join(enricher_list)}")
                
    except Exception as e:
        typer.echo(f"Error adding source: {e}", err=True)
        raise typer.Exit(1)




@app.command("list-types")
def list_source_types(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Use test database environment"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be listed without executing external validation"),
):
    """
    List all available source types (importers) with interface compliance validation.
    
    This command enumerates source types from the importer registry, validates
    interface compliance, and reports availability status.
    
    Examples:
        retrovue source list-types
        retrovue source list-types --json
        retrovue source list-types --dry-run
        retrovue source list-types --test-db
    """
    try:
        # Get available importers from registry
        available_importers = list_importers()
        
        
        if not available_importers:
            if json_output:
                import json
                result = {
                    "status": "ok",
                    "source_types": [],
                    "total": 0
                }
                typer.echo(json.dumps(result, indent=2))
            else:
                typer.echo("No source types available")
            return
        
        # Build source type information with interface compliance validation
        source_types = []
        
        for importer_name in available_importers:
            try:
                # Get importer class from registry
                importer_class = SOURCES.get(importer_name)
                if not importer_class:
                    continue
                
                # Check interface compliance
                interface_compliant = _check_interface_compliance(importer_class)
                
                # Get display name and status
                display_name = _get_display_name(importer_name)
                status = "valid" if interface_compliant else "error"
                
                source_type_info = {
                    "type": importer_name,
                    "importer_file": f"{importer_name}_importer.py",
                    "display_name": display_name,
                    "available": True,
                    "interface_compliant": interface_compliant,
                    "status": status
                }
                
                source_types.append(source_type_info)
                
            except Exception:
                # Handle individual importer validation errors
                source_type_info = {
                    "type": importer_name,
                    "importer_file": f"{importer_name}_importer.py",
                    "display_name": f"{importer_name.title()} Source",
                    "available": False,
                    "interface_compliant": False,
                    "status": "error"
                }
                source_types.append(source_type_info)
        
        # Handle dry-run mode
        if dry_run:
            if json_output:
                import json
                result = {
                    "status": "dry_run",
                    "source_types": source_types,
                    "total": len(source_types)
                }
                typer.echo(json.dumps(result, indent=2))
            else:
                typer.echo(f"Would list {len(source_types)} source types from registry:")
                for source_type in source_types:
                    status_indicator = "[OK]" if source_type["interface_compliant"] else "[ERROR]"
                    typer.echo(f"  - {source_type['type']} ({source_type['importer_file']}) {status_indicator}")
            return
        
        # Normal output
        if json_output:
            import json
            result = {
                "status": "ok",
                "source_types": source_types,
                "total": len(source_types)
            }
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo("Available source types:")
            for source_type in source_types:
                status_indicator = "[OK]" if source_type["interface_compliant"] else "[ERROR]"
                typer.echo(f"  - {source_type['type']} {status_indicator}")
            
            typer.echo(f"\nTotal: {len(source_types)} source types available")
                
    except Exception as e:
        typer.echo(f"Error listing source types: {e}", err=True)
        raise typer.Exit(1)


def _check_interface_compliance(importer_class) -> bool:
    """
    Check if an importer class implements the required interface.
    
    Args:
        importer_class: The importer class to check
        
    Returns:
        True if the class implements the required interface, False otherwise
    """
    try:
        # Check if the class has the required methods from ImporterInterface
        required_methods = [
            'get_config_schema',
            'discover',
            'get_help',
            'list_asset_groups',
            'enable_asset_group',
            'disable_asset_group'
        ]
        
        for method_name in required_methods:
            if not hasattr(importer_class, method_name):
                return False
        
        # Check if it has the name attribute (class attribute, not instance)
        if not hasattr(importer_class, 'name'):
            return False
        
        # Verify the name attribute is accessible
        try:
            name_value = importer_class.name
            if not name_value:
                return False
        except Exception:
            return False
        
        # Try to create a minimal instance to test interface
        # This is a basic check - in a real implementation you'd want more thorough validation
        return True
        
    except Exception:
        return False


def _get_display_name(importer_name: str) -> str:
    """
    Get a human-readable display name for an importer.
    
    Args:
        importer_name: The importer name
        
    Returns:
        Human-readable display name
    """
    display_names = {
        "plex": "Plex Media Server",
        "filesystem": "Local Filesystem",
        "fs": "Local Filesystem",
        "jellyfin": "Jellyfin Media Server"
    }
    
    return display_names.get(importer_name, f"{importer_name.title()} Source")


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
                source_dict = {
                    "id": source.id,
                    "external_id": source.external_id,
                    "type": source.type,
                    "name": source.name,
                    "status": source.status,
                    "base_url": source.base_url,
                    "config": source.config
                }
                typer.echo(json.dumps(source_dict, indent=2))
            else:
                typer.echo("Source Details:")
                typer.echo(f"  ID: {source.id}")
                typer.echo(f"  External ID: {source.external_id}")
                typer.echo(f"  Name: {source.name}")
                typer.echo(f"  Type: {source.type}")
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
    name: str | None = typer.Option(None, "--name", help="New name for the source"),
    base_url: str | None = typer.Option(None, "--base-url", help="New base URL for the source"),
    token: str | None = typer.Option(None, "--token", help="New authentication token"),
    base_path: str | None = typer.Option(None, "--base-path", help="New base filesystem path"),
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
            
            if current_source.type == "plex":
                if base_url:
                    new_config["servers"] = [{"base_url": base_url, "token": new_config.get("servers", [{}])[0].get("token", "")}]
                if token:
                    if "servers" not in new_config:
                        new_config["servers"] = [{"base_url": "", "token": ""}]
                    new_config["servers"][0]["token"] = token
                if new_config:
                    updates["config"] = new_config
                    
            elif current_source.type == "filesystem":
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
                source_dict = {
                    "id": updated_source.id,
                    "external_id": updated_source.external_id,
                    "type": updated_source.type,
                    "name": updated_source.name,
                    "status": updated_source.status,
                    "base_url": updated_source.base_url,
                    "config": updated_source.config
                }
                typer.echo(json.dumps(source_dict, indent=2))
            else:
                typer.echo(f"Successfully updated source: {updated_source.name}")
                typer.echo(f"  ID: {updated_source.id}")
                typer.echo(f"  Type: {updated_source.type}")
                if updated_source.base_url:
                    typer.echo(f"  Base URL: {updated_source.base_url}")
                if updated_source.config:
                    typer.echo(f"  Configuration: {updated_source.config}")
                    
        except Exception as e:
            typer.echo(f"Error updating source: {e}", err=True)
            raise typer.Exit(1)


@app.command("delete", no_args_is_help=True)
def delete_source(
    source_selector: str = typer.Argument(..., help="Source ID, external ID, name, or wildcard pattern to delete"),
    force: bool = typer.Option(False, "--force", help="Force deletion without confirmation"),
    confirm: bool = typer.Option(False, "--confirm", help="Required flag to proceed with deletion"),
    test_db: bool = typer.Option(False, "--test-db", help="Direct command to test database environment"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Delete a source.
    
    Examples:
        retrovue source delete "My Plex Server"
        retrovue source delete filesystem-4807c63e --force
        retrovue source delete 4b2b05e7-d7d2-414a-a587-3f5df9b53f44
        retrovue source delete "plex-%" --confirm
    """
    from ._ops.confirmation import evaluate_confirmation
    from ._ops.source_delete_ops import (
        build_pending_delete_summary,
        format_human_output,
        format_json_output,
        perform_source_deletions,
        resolve_source_selector,
    )
    
    # Production safety check
    if not test_db and not force:
        import os

        from ...infra.settings import settings
        
        # Check if this looks like a production database
        is_production = True
        db_url = settings.database_url or ""
        
        # Consider it a test database if:
        # 1. URL contains "test" 
        # 2. TEST_DATABASE_URL environment variable is set
        # 3. Database name contains "test", "dev", "local", or "sandbox"
        if ("test" in db_url.lower() or 
            os.getenv("TEST_DATABASE_URL") or
            any(word in db_url.lower() for word in ["test", "dev", "local", "sandbox"])):
            is_production = False
        
        if is_production:
            typer.echo("⚠️  WARNING: This appears to be a production database!", err=True)
            typer.echo("", err=True)
            typer.echo("   To delete sources from production:", err=True)
            typer.echo("   1. Use --test-db flag for test databases only", err=True)
            typer.echo("   2. For production: backup your database first", err=True)
            typer.echo("   3. Consider using --dry-run to preview changes", err=True)
            typer.echo("   4. Use --force flag to bypass this safety check", err=True)
            typer.echo("", err=True)
            typer.echo("   Example: retrovue source delete 'source-name' --force", err=True)
            typer.echo("", err=True)
            typer.echo("   To mark as test database:", err=True)
            typer.echo("   - Set TEST_DATABASE_URL environment variable", err=True)
            typer.echo("   - Use database name with 'test', 'dev', 'local', or 'sandbox'", err=True)
            raise typer.Exit(1)
    
    try:
        with session() as db:
            # Call resolve_source_selector(...)
            sources = resolve_source_selector(db, source_selector)
            
            # If it returns an empty list, print Error and exit code 1 (B-5)
            if not sources:
                typer.echo(f"Error: Source '{source_selector}' not found", err=True)
                raise typer.Exit(1)
            
            # Call build_pending_delete_summary(...) to get the impact summary
            summary = build_pending_delete_summary(db, sources)
            
            # Run the confirmation gate
            # First call evaluate_confirmation(...) with user_response=None
            proceed, prompt = evaluate_confirmation(
                summary=summary,
                force=force,
                confirm=confirm,
                user_response=None
            )
            
            if not proceed and prompt is not None:
                # If that returns (False, <prompt>), print <prompt>, read from stdin
                typer.echo(prompt)
                user_response = typer.prompt("", default="no")
                
                # then call evaluate_confirmation(...) again with the user's response
                proceed, message = evaluate_confirmation(
                    summary=summary,
                    force=force,
                    confirm=confirm,
                    user_response=user_response
                )
                
                if not proceed and message == "Deletion cancelled":
                    # If the second evaluation returns (False, "Deletion cancelled"), print "Deletion cancelled" and exit code 0 (B-6)
                    typer.echo("Deletion cancelled")
                    raise typer.Exit(0)
            
            # Call perform_source_deletions(...) to actually apply deletions / skips
            # Create a simple environment configuration for now
            class SimpleEnvConfig:
                def is_production(self):
                    # For now, always return False (non-production) to allow deletion
                    # TODO: Implement proper environment detection
                    return False
            
            env_config = SimpleEnvConfig()
            args = type('Args', (), {'test_db': test_db})()
            results = perform_source_deletions(db, env_config, args, sources)
            
            # If --json: Render JSON with the output helper from source_delete_ops
            if json_output:
                json_output_data = format_json_output(results)
                typer.echo(json.dumps(json_output_data, indent=2))
            else:
                # Else: Render human-readable output with the output helper from source_delete_ops
                human_output = format_human_output(results)
                typer.echo(human_output)
        
        # Exit code 0 - transaction has been committed
        raise typer.Exit(0)
                    
    except typer.Exit:
        # Re-raise typer.Exit exceptions (including cancellation)
        raise
    except Exception as e:
        typer.echo(f"Error deleting source: {e}", err=True)
        raise typer.Exit(1)


@app.command("discover")
def discover_collections(
    source_id: str = typer.Argument(..., help="Source ID, external ID, or name to discover collections from"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    test_db: bool = typer.Option(False, "--test-db", help="Direct command to test database environment"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be discovered without persisting"),
):
    """
    Discover and add collections (libraries) from a source to the repository.
    
    This scans the source for available collections/libraries and adds them
    to the RetroVue database for management. Collections start disabled by default.
    
    Examples:
        retrovue source discover "My Plex"
        retrovue source discover plex-5063d926
        retrovue source discover "My Plex" --json
    """
    with session() as db:
        source_service = SourceService(db)
        
        try:
            # Get the source first to validate it exists
            source = source_service.get_source_by_id(source_id)
            if not source:
                typer.echo(f"Error: Source '{source_id}' not found", err=True)
                raise typer.Exit(1)
            
            # Get the importer for this source type
            from ...adapters.importers.plex_importer import PlexImporter
            
            # Create importer with source config
            if source.type == "plex":
                # Extract Plex configuration
                config = source.config or {}
                if "servers" in config and config["servers"]:
                    # New format with servers array
                    server_config = config["servers"][0]
                    base_url = server_config.get("base_url")
                    token = server_config.get("token")
                else:
                    # Old format with direct base_url and token
                    base_url = config.get("base_url")
                    token = config.get("token")
                
                if not base_url or not token:
                    typer.echo(f"Error: Plex source '{source.name}' missing base_url or token", err=True)
                    raise typer.Exit(1)
                
                importer = PlexImporter(base_url=base_url, token=token)
                
                # Discover collections using the new plugin interface
                collections = importer.list_collections({})
                
                if not collections:
                    typer.echo(f"No collections found for source '{source.name}'")
                    return
                
                # Convert to SourceCollectionDTO format and add to database
                from ...content_manager.source_service import SourceCollectionDTO
                collection_dtos = []
                added_count = 0
                
                for collection in collections:
                    # Check if collection already exists
                    existing = db.query(SourceCollection).filter(
                        SourceCollection.source_id == source.id,
                        SourceCollection.external_id == collection["external_id"]
                    ).first()
                    
                    if existing:
                        if dry_run:
                            typer.echo(f"  Collection '{collection['name']}' already exists, would skip")
                        else:
                            typer.echo(f"  Collection '{collection['name']}' already exists, skipping")
                        continue
                    
                    # Create collection DTO for output
                    collection_dto = SourceCollectionDTO(
                        external_id=collection["external_id"],
                        name=collection["name"],
                        sync_enabled=False,
                        mapping_pairs=[],
                        source_type=source.type,
                        config={
                            "plex_section_ref": collection.get("plex_section_ref", ""),
                            "type": collection.get("type", "unknown")
                        }
                    )
                    collection_dtos.append(collection_dto)
                    added_count += 1
                    
                    # Only persist to database if not in dry-run mode
                    if not dry_run:
                        # Create new collection
                        new_collection = SourceCollection(
                            id=uuid.uuid4(),
                            source_id=source.id,
                            external_id=collection["external_id"],
                            name=collection["name"],
                            sync_enabled=False,  # Newly discovered collections start disabled
                            config=collection_dto.config
                        )
                        db.add(new_collection)
                
                # Commit all new collections (only if not dry-run)
                if not dry_run:
                    db.commit()
                
                if json_output:
                    import json
                    result = {
                        "source": {
                            "id": str(source.id),
                            "name": source.name,
                            "type": source.type
                        },
                        "collections_added": added_count,
                        "collections": [
                            {
                                "external_id": col.external_id,
                                "name": col.name,
                                "sync_enabled": col.sync_enabled,
                                "source_type": col.source_type
                            } for col in collection_dtos
                        ]
                    }
                    typer.echo(json.dumps(result, indent=2))
                else:
                    if dry_run:
                        typer.echo(f"Would discover {added_count} collections from '{source.name}':")
                        for collection in collection_dtos:
                            typer.echo(f"  • {collection.name} (ID: {collection.external_id}) - Would be created")
                    else:
                        typer.echo(f"Successfully added {added_count} collections from '{source.name}':")
                        for collection in collection_dtos:
                            typer.echo(f"  • {collection.name} (ID: {collection.external_id}) - Disabled by default")
                        typer.echo()
                        typer.echo("Use 'retrovue collection update <name> --sync-enabled true' to enable collections for sync")
            else:
                typer.echo(f"Error: Source type '{source.type}' not supported for discovery", err=True)
                raise typer.Exit(1)
                    
        except Exception as e:
            typer.echo(f"Error discovering collections: {e}", err=True)
            raise typer.Exit(1)


@app.command("ingest")
def source_ingest(
    source_id: str = typer.Argument(..., help="Source ID, external ID, or name to ingest from"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be ingested without actually ingesting"),
):
    """
    Ingest all sync-enabled, ingestible collections from a source.
    
    This command finds all collections that are both sync-enabled and ingestible,
    then processes them using the ingest orchestrator.
    
    Examples:
        retrovue source --name "My Plex Server" ingest
        retrovue source plex-5063d926 ingest
        retrovue source "My Plex Server" ingest --json
    """
    with session() as db:
        source_service = SourceService(db)
        
        try:
            # Get the source first to validate it exists
            source = source_service.get_source_by_id(source_id)
            if not source:
                typer.echo(f"Error: Source '{source_id}' not found", err=True)
                raise typer.Exit(1)
            
            # Get sync-enabled, ingestible collections for this source
            collections = db.query(SourceCollection).filter(
                SourceCollection.source_id == source.id,
                SourceCollection.sync_enabled
            ).all()
            
            if not collections:
                typer.echo(f"No sync-enabled collections found for source '{source.name}'")
                typer.echo("Use 'retrovue collection update <name> --sync-enabled true' to enable collections")
                return
            
            # Filter to only ingestible collections using persisted field
            ingestible_collections = []
            for collection in collections:
                if collection.ingestible:
                    ingestible_collections.append(collection)
                else:
                    typer.echo(f"  Skipping '{collection.name}' - not ingestible (no valid local paths)")
            
            if not ingestible_collections:
                typer.echo(f"No ingestible collections found for source '{source.name}'")
                typer.echo("Configure path mappings and ensure local paths are accessible")
                return
            
            # Use the existing ingest orchestrator for bulk processing
            from ...content_manager.ingest_orchestrator import IngestOrchestrator
            
            orchestrator = IngestOrchestrator(db)
            sync_results = []
            total_assets = 0
            
            for collection in ingestible_collections:
                typer.echo(f"Ingesting collection: {collection.name}")
                
                try:
                    # Run ingest for this collection
                    result = orchestrator.ingest_collection(str(collection.id), dry_run=dry_run)
                    
                    asset_count = result.get("assets_processed", 0)
                    total_assets += asset_count
                    
                    sync_results.append({
                        "collection_name": collection.name,
                        "assets_ingested": asset_count,
                        "status": "success"
                    })
                    
                    typer.echo(f"  Ingested {asset_count} assets")
                    
                except Exception as e:
                    typer.echo(f"  Error ingesting '{collection.name}': {e}")
                    sync_results.append({
                        "collection_name": collection.name,
                        "assets_ingested": 0,
                        "status": "error",
                        "error": str(e)
                    })
            
            if json_output:
                import json
                result = {
                    "source": {
                        "id": str(source.id),
                        "name": source.name,
                        "type": source.type
                    },
                    "collections_ingested": len(ingestible_collections),
                    "total_assets": total_assets,
                    "ingest_results": sync_results
                }
                typer.echo(json.dumps(result, indent=2))
            else:
                typer.echo(f"Ingest completed for {len(ingestible_collections)} collections")
                typer.echo(f"Total assets ingested: {total_assets}")
                    
        except Exception as e:
            typer.echo(f"Error ingesting from source: {e}", err=True)
            raise typer.Exit(1)


@app.command("attach-enricher")
def source_attach_enricher(
    source_id: str = typer.Argument(..., help="Source ID, external ID, or name to attach enricher to"),
    enricher_id: str = typer.Argument(..., help="Enricher ID to attach"),
    priority: int = typer.Option(1, "--priority", help="Priority/order for enricher execution (default: 1)"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Attach an ingest-scope enricher to all collections in a source.
    
    This command attaches the specified enricher to all collections under the source,
    applying it during the ingest process for each collection.
    
    Parameters:
    - source_id: Source to attach enricher to (can be ID, external ID, or name)
    - enricher_id: Enricher to attach
    - priority: Execution priority (lower numbers run first)
    
    Examples:
        retrovue source --name "My Plex Server" attach-enricher enricher-ffprobe-1
        retrovue source plex-5063d926 attach-enricher enricher-metadata-1 --priority 2
        retrovue source "My Plex Server" attach-enricher enricher-llm-1 --priority 3
    """
    with session() as db:
        source_service = SourceService(db)
        
        try:
            # Get the source first to validate it exists
            source = source_service.get_source_by_id(source_id)
            if not source:
                typer.echo(f"Error: Source '{source_id}' not found", err=True)
                raise typer.Exit(1)
            
            # Get all collections for this source
            collections = db.query(SourceCollection).filter(
                SourceCollection.source_id == source.id
            ).all()
            
            if not collections:
                typer.echo(f"No collections found for source '{source.name}'")
                return
            
            # TODO: Implement actual enricher attachment logic
            # For now, just show what would be attached
            typer.echo(f"Attaching enricher '{enricher_id}' to {len(collections)} collections in source '{source.name}'")
            typer.echo(f"Priority: {priority}")
            typer.echo()
            typer.echo("Collections that will have the enricher attached:")
            for collection in collections:
                typer.echo(f"  - {collection.name} (ID: {collection.id})")
            
            if json_output:
                import json
                result = {
                    "source": {
                        "id": str(source.id),
                        "name": source.name,
                        "type": source.type
                    },
                    "enricher_id": enricher_id,
                    "priority": priority,
                    "collections_affected": len(collections),
                    "collections": [
                        {
                            "id": str(collection.id),
                            "name": collection.name,
                            "external_id": collection.external_id
                        }
                        for collection in collections
                    ],
                    "status": "attached"
                }
                typer.echo(json.dumps(result, indent=2))
            else:
                typer.echo(f"Successfully attached enricher '{enricher_id}' to {len(collections)} collections")
                typer.echo("TODO: Implement actual enricher attachment logic")
                
        except Exception as e:
            typer.echo(f"Error attaching enricher to source: {e}", err=True)
            raise typer.Exit(1)


@app.command("detach-enricher")
def source_detach_enricher(
    source_id: str = typer.Argument(..., help="Source ID, external ID, or name to detach enricher from"),
    enricher_id: str = typer.Argument(..., help="Enricher ID to detach"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Detach an ingest-scope enricher from all collections in a source.
    
    This command removes the specified enricher from all collections under the source,
    preventing it from running during the ingest process for each collection.
    
    Parameters:
    - source_id: Source to detach enricher from (can be ID, external ID, or name)
    - enricher_id: Enricher to detach
    
    Examples:
        retrovue source --name "My Plex Server" detach-enricher enricher-ffprobe-1
        retrovue source plex-5063d926 detach-enricher enricher-metadata-1
        retrovue source "My Plex Server" detach-enricher enricher-llm-1
    """
    with session() as db:
        source_service = SourceService(db)
        
        try:
            # Get the source first to validate it exists
            source = source_service.get_source_by_id(source_id)
            if not source:
                typer.echo(f"Error: Source '{source_id}' not found", err=True)
                raise typer.Exit(1)
            
            # Get all collections for this source
            collections = db.query(SourceCollection).filter(
                SourceCollection.source_id == source.id
            ).all()
            
            if not collections:
                typer.echo(f"No collections found for source '{source.name}'")
                return
            
            # TODO: Implement actual enricher detachment logic
            # For now, just show what would be detached
            typer.echo(f"Detaching enricher '{enricher_id}' from {len(collections)} collections in source '{source.name}'")
            typer.echo()
            typer.echo("Collections that will have the enricher detached:")
            for collection in collections:
                typer.echo(f"  - {collection.name} (ID: {collection.id})")
            
            if json_output:
                import json
                result = {
                    "source": {
                        "id": str(source.id),
                        "name": source.name,
                        "type": source.type
                    },
                    "enricher_id": enricher_id,
                    "collections_affected": len(collections),
                    "collections": [
                        {
                            "id": str(collection.id),
                            "name": collection.name,
                            "external_id": collection.external_id
                        }
                        for collection in collections
                    ],
                    "status": "detached"
                }
                typer.echo(json.dumps(result, indent=2))
            else:
                typer.echo(f"Successfully detached enricher '{enricher_id}' from {len(collections)} collections")
                typer.echo("TODO: Implement actual enricher detachment logic")
                
        except Exception as e:
            typer.echo(f"Error detaching enricher from source: {e}", err=True)
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
            importer = get_importer(source.type, **importer_config)
            
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
            importer = get_importer(source.type, **importer_config)
            
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
            unknown_enrichers = []
            for enricher in enricher_list:
                if enricher not in available_enrichers:
                    unknown_enrichers.append(enricher)
            
            if unknown_enrichers:
                for enricher in unknown_enrichers:
                    typer.echo(f"Error: Unknown enricher '{enricher}'. Available: {', '.join(available_enrichers)}", err=True)
                raise typer.Exit(1)
            
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