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


@app.command("collections")
def list_collections(
    source_id: Optional[str] = typer.Option(None, "--source-id", help="Filter by specific source ID"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    List collections for sources.
    
    Examples:
        retrovue source collections
        retrovue source collections --source-id plex
        retrovue source collections --json
    """
    with session() as db:
        source_service = SourceService(db)
        
        try:
            if source_id:
                collections = source_service.list_enabled_collections(source_id)
            else:
                # Get all sources and their collections
                sources = source_service.list_sources()
                collections = []
                for source in sources:
                    source_collections = source_service.list_enabled_collections(source.external_id)
                    collections.extend(source_collections)
            
            if json_output:
                import json
                typer.echo(json.dumps([collection.model_dump() for collection in collections], indent=2))
            else:
                typer.echo(f"Found {len(collections)} collections:")
                for collection in collections:
                    typer.echo(f"  - {collection.name} ({collection.source_type})")
                    typer.echo(f"    External ID: {collection.external_id}")
                    typer.echo(f"    Enabled: {collection.enabled}")
                    typer.echo(f"    Path mappings: {len(collection.mapping_pairs)}")
                    typer.echo()
                    
        except Exception as e:
            typer.echo(f"Error listing collections: {e}", err=True)
            raise typer.Exit(1)
