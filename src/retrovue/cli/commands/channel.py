"""
Channel management commands for RetroVue infrastructure.
"""
import json
import typer
from typing import Optional

from ...infra.uow import session
from ...schedule_manager.broadcast_channel_service import BroadcastChannelService

app = typer.Typer(help="Channel management operations for BroadcastChannel")


@app.command("list")
def list_cmd(json_output: bool = typer.Option(False, "--json", help="Output as JSON")):
    """List all channels."""
    try:
        channels = BroadcastChannelService.list_channels()
        
        if json_output:
            typer.echo(json.dumps(channels, indent=2, sort_keys=True))
        else:
            if not channels:
                typer.echo("No channels found")
                return
            
            typer.echo(f"Found {len(channels)} channels:")
            # Print table header matching contract
            typer.echo(f"{'channel_id':<12} {'label':<20} {'producer':<20} {'enrichers':<30}")
            typer.echo("-" * 90)
            
            # Print each channel
            for channel in channels:
                # TODO: Get actual producer and enricher data when available
                producer = "N/A"  # TODO: Get active producer instance
                enrichers = "N/A"  # TODO: Get attached playout enrichers with priority
                
                typer.echo(f"{channel['id']:<12} {channel['name']:<20} {producer:<20} {enrichers:<30}")
                
    except Exception as e:
        typer.echo(f"Error listing channels: {e}", err=True)
        raise typer.Exit(1)


@app.command("show")
def show_cmd(
    id: int = typer.Option(..., "--id", help="Channel ID"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Show detailed information for a single channel."""
    try:
        channel = BroadcastChannelService.get_channel(id)
        
        if not channel:
            typer.echo(f"Channel with ID {id} not found", err=True)
            raise typer.Exit(1)
        
        if json_output:
            typer.echo(json.dumps(channel, indent=2, sort_keys=True))
        else:
            typer.echo(f"id: {channel['id']}")
            typer.echo(f"name: {channel['name']}")
            typer.echo(f"timezone: {channel['timezone']}")
            typer.echo(f"grid_size_minutes: {channel['grid_size_minutes']}")
            typer.echo(f"grid_offset_minutes: {channel['grid_offset_minutes']}")
            typer.echo(f"rollover_minutes: {channel['rollover_minutes']}")
            typer.echo(f"is_active: {channel['is_active']}")
            typer.echo(f"created_at: {channel['created_at']}")
            
    except Exception as e:
        typer.echo(f"Error showing channel: {e}", err=True)
        raise typer.Exit(1)


@app.command("create")
def create_cmd(
    name: str = typer.Option(..., "--name", help="Channel name"),
    timezone: str = typer.Option(..., "--timezone", help="IANA timezone string"),
    grid_size_minutes: int = typer.Option(..., "--grid-size-minutes", help="Grid size in minutes"),
    grid_offset_minutes: int = typer.Option(..., "--grid-offset-minutes", help="Grid offset in minutes"),
    rollover_minutes: int = typer.Option(..., "--rollover-minutes", help="Rollover minutes after midnight"),
    active: bool = typer.Option(False, "--active", help="Set active"),
    inactive: bool = typer.Option(False, "--inactive", help="Set inactive"),
):
    """Create a new channel."""
    try:
        # Determine is_active value
        if active and inactive:
            typer.echo("Error: Cannot specify both --active and --inactive", err=True)
            raise typer.Exit(1)
        elif active:
            is_active = True
        elif inactive:
            is_active = False
        else:
            is_active = True  # default like broadcast_channel_ctl
        
        channel = BroadcastChannelService.create_channel(
            name=name,
            timezone=timezone,
            grid_size_minutes=grid_size_minutes,
            grid_offset_minutes=grid_offset_minutes,
            rollover_minutes=rollover_minutes,
            is_active=is_active
        )
        
        typer.echo(f"Created channel '{name}' with ID {channel['id']}")
        typer.echo(f"  Timezone: {channel['timezone']}")
        typer.echo(f"  Grid Size: {channel['grid_size_minutes']} minutes")
        typer.echo(f"  Grid Offset: {channel['grid_offset_minutes']} minutes")
        typer.echo(f"  Rollover: {channel['rollover_minutes']} minutes")
        typer.echo(f"  Active: {channel['is_active']}")
        
    except ValueError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error creating channel: {e}", err=True)
        raise typer.Exit(1)


@app.command("update")
def update_cmd(
    id: int = typer.Option(..., "--id", help="Channel ID to update"),
    name: Optional[str] = typer.Option(None, "--name", help="New channel name"),
    timezone: Optional[str] = typer.Option(None, "--timezone", help="New timezone"),
    grid_size_minutes: Optional[int] = typer.Option(None, "--grid-size-minutes", help="New grid size in minutes"),
    grid_offset_minutes: Optional[int] = typer.Option(None, "--grid-offset-minutes", help="New grid offset in minutes"),
    rollover_minutes: Optional[int] = typer.Option(None, "--rollover-minutes", help="New rollover minutes"),
    active: bool = typer.Option(False, "--active", help="Set channel as active"),
    inactive: bool = typer.Option(False, "--inactive", help="Set channel as inactive"),
):
    """Update an existing channel."""
    try:
        # Build update fields dict, only including provided values
        update_fields = {}
        if name is not None:
            update_fields["name"] = name
        if timezone is not None:
            update_fields["timezone"] = timezone
        if grid_size_minutes is not None:
            update_fields["grid_size_minutes"] = grid_size_minutes
        if grid_offset_minutes is not None:
            update_fields["grid_offset_minutes"] = grid_offset_minutes
        if rollover_minutes is not None:
            update_fields["rollover_minutes"] = rollover_minutes
        
        # Handle is_active logic
        if active and inactive:
            typer.echo("Error: Cannot specify both --active and --inactive", err=True)
            raise typer.Exit(1)
        elif active:
            update_fields["is_active"] = True
        elif inactive:
            update_fields["is_active"] = False
        
        if not update_fields:
            typer.echo("No fields to update", err=True)
            raise typer.Exit(1)
        
        channel = BroadcastChannelService.update_channel(id, **update_fields)
        
        typer.echo(f"Updated channel ID {id}")
        typer.echo(f"  Name: {channel['name']}")
        typer.echo(f"  Timezone: {channel['timezone']}")
        typer.echo(f"  Grid Size: {channel['grid_size_minutes']} minutes")
        typer.echo(f"  Grid Offset: {channel['grid_offset_minutes']} minutes")
        typer.echo(f"  Rollover: {channel['rollover_minutes']} minutes")
        typer.echo(f"  Active: {channel['is_active']}")
        
    except ValueError as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error updating channel: {e}", err=True)
        raise typer.Exit(1)


@app.command("delete")
def delete_cmd(
    id: int = typer.Option(..., "--id", help="Channel ID"),
):
    """Delete a channel."""
    try:
        BroadcastChannelService.delete_channel(id)
        typer.echo(f"BroadcastChannel {id} deleted")
        
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error deleting channel: {e}", err=True)
        raise typer.Exit(1)


@app.command("attach-enricher")
def attach_enricher(
    channel_id: str = typer.Argument(..., help="Target channel"),
    enricher_id: str = typer.Argument(..., help="Enricher to attach"),
    priority: int = typer.Option(..., "--priority", help="Priority order (lower numbers run first)"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Attach a playout-scope enricher to the Channel. Enrichers run in ascending priority.
    
    Parameters:
    - channel_id: Target channel
    - enricher_id: Enricher to attach
    - --priority: Priority order (lower numbers run first)
    
    Examples:
        retrovue channel attach-enricher channel-1 enricher-playout-1 --priority 1
    """
    try:
        # TODO: Implement actual enricher attachment logic
        if json_output:
            import json
            result = {
                "channel_id": channel_id,
                "enricher_id": enricher_id,
                "priority": priority,
                "status": "attached"
            }
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo(f"Successfully attached enricher {enricher_id} to channel {channel_id}")
            typer.echo(f"  Priority: {priority}")
            typer.echo("TODO: implement actual attachment logic")
                
    except Exception as e:
        typer.echo(f"Error attaching enricher: {e}", err=True)
        raise typer.Exit(1)


@app.command("detach-enricher")
def detach_enricher(
    channel_id: str = typer.Argument(..., help="Target channel"),
    enricher_id: str = typer.Argument(..., help="Enricher to detach"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """
    Remove enricher from channel.
    
    Examples:
        retrovue channel detach-enricher channel-1 enricher-playout-1
    """
    try:
        # TODO: Implement actual enricher detachment logic
        if json_output:
            import json
            result = {
                "channel_id": channel_id,
                "enricher_id": enricher_id,
                "status": "detached"
            }
            typer.echo(json.dumps(result, indent=2))
        else:
            typer.echo(f"Successfully detached enricher {enricher_id} from channel {channel_id}")
            typer.echo("TODO: implement actual detachment logic")
                
    except Exception as e:
        typer.echo(f"Error detaching enricher: {e}", err=True)
        raise typer.Exit(1)