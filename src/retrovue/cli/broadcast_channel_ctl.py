"""
DEPRECATED - logic moved into cli/commands/channel.py

This file is kept for reference only. The functionality has been moved to the main Typer CLI
under `retrovue channel` commands. Do not use this file for new development.

Original BroadcastChannel CLI Control Tool

This was an operator/maintenance surface for BroadcastChannel management.
It was NOT ScheduleService - it did not start or stop streaming.
It only managed the persisted BroadcastChannel definitions stored in Postgres.

This CLI provided human-readable operations for:
- Listing all channels
- Viewing channel details  
- Creating new channels
- Updating existing channels
- Deleting channels

All operations went through BroadcastChannelService for business logic enforcement.
"""

import argparse
import json
import sys
from typing import Optional

from ..schedule_manager.broadcast_channel_service import BroadcastChannelService


def list_channels(json_output: bool = False) -> None:
    """List all BroadcastChannels in a table format or JSON."""
    try:
        channels = BroadcastChannelService.list_channels()
        
        if json_output:
            print(json.dumps(channels, indent=2, sort_keys=True))
        else:
            if not channels:
                print("No channels found")
                return
            
            # Print table header
            print(f"{'ID':<4} {'Active':<6} {'Name':<20} {'Timezone':<20} {'Rollover':<8}")
            print("-" * 70)
            
            # Print each channel
            for channel in channels:
                active_str = "Yes" if channel["is_active"] else "No"
                print(f"{channel['id']:<4} {active_str:<6} {channel['name']:<20} {channel['timezone']:<20} {channel['rollover_minutes']:<8}")
                
    except Exception as e:
        print(f"Error listing channels: {e}", file=sys.stderr)
        sys.exit(1)


def show_channel(channel_id: int, json_output: bool = False) -> None:
    """Show detailed information for a single channel."""
    try:
        channel = BroadcastChannelService.get_channel(channel_id)
        
        if not channel:
            print(f"Channel with ID {channel_id} not found", file=sys.stderr)
            sys.exit(1)
        
        if json_output:
            print(json.dumps(channel, indent=2, sort_keys=True))
        else:
            print(f"id: {channel['id']}")
            print(f"name: {channel['name']}")
            print(f"timezone: {channel['timezone']}")
            print(f"grid_size_minutes: {channel['grid_size_minutes']}")
            print(f"grid_offset_minutes: {channel['grid_offset_minutes']}")
            print(f"rollover_minutes: {channel['rollover_minutes']}")
            print(f"is_active: {channel['is_active']}")
            print(f"created_at: {channel['created_at']}")
            
    except Exception as e:
        print(f"Error showing channel: {e}", file=sys.stderr)
        sys.exit(1)


def create_channel(
    name: str,
    timezone: str,
    grid_size_minutes: int,
    grid_offset_minutes: int,
    rollover_minutes: int,
    is_active: Optional[bool] = None
) -> None:
    """Create a new BroadcastChannel."""
    try:
        # Handle is_active logic: if neither --active nor --inactive provided, default to True
        if is_active is None:
            is_active = True
        
        channel = BroadcastChannelService.create_channel(
            name=name,
            timezone=timezone,
            grid_size_minutes=grid_size_minutes,
            grid_offset_minutes=grid_offset_minutes,
            rollover_minutes=rollover_minutes,
            is_active=is_active
        )
        
        print(f"Created channel '{name}' with ID {channel['id']}")
        print(f"  Timezone: {channel['timezone']}")
        print(f"  Grid Size: {channel['grid_size_minutes']} minutes")
        print(f"  Grid Offset: {channel['grid_offset_minutes']} minutes")
        print(f"  Rollover: {channel['rollover_minutes']} minutes")
        print(f"  Active: {channel['is_active']}")
        
    except ValueError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error creating channel: {e}", file=sys.stderr)
        sys.exit(1)


def update_channel(
    channel_id: int,
    name: Optional[str] = None,
    timezone: Optional[str] = None,
    grid_size_minutes: Optional[int] = None,
    grid_offset_minutes: Optional[int] = None,
    rollover_minutes: Optional[int] = None,
    is_active: Optional[bool] = None
) -> None:
    """Update an existing BroadcastChannel."""
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
        if is_active is not None:
            update_fields["is_active"] = is_active
        
        if not update_fields:
            print("No fields to update", file=sys.stderr)
            sys.exit(1)
        
        channel = BroadcastChannelService.update_channel(channel_id, **update_fields)
        
        print(f"Updated channel ID {channel_id}")
        print(f"  Name: {channel['name']}")
        print(f"  Timezone: {channel['timezone']}")
        print(f"  Grid Size: {channel['grid_size_minutes']} minutes")
        print(f"  Grid Offset: {channel['grid_offset_minutes']} minutes")
        print(f"  Rollover: {channel['rollover_minutes']} minutes")
        print(f"  Active: {channel['is_active']}")
        
    except ValueError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error updating channel: {e}", file=sys.stderr)
        sys.exit(1)


def delete_channel(channel_id: int) -> None:
    """Delete a BroadcastChannel."""
    try:
        BroadcastChannelService.delete_channel(channel_id)
        print(f"BroadcastChannel {channel_id} deleted")
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error deleting channel: {e}", file=sys.stderr)
        sys.exit(1)


def run(argv: list[str]) -> int:
    """
    Testable entry point for CLI operations.
    
    Args:
        argv: Command line arguments (excluding script name)
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="BroadcastChannel management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m retrovue.cli.broadcast_channel_ctl list
  python -m retrovue.cli.broadcast_channel_ctl show --id 1
  python -m retrovue.cli.broadcast_channel_ctl create --name "RetroToons" --timezone "America/New_York" --grid-size-minutes 30 --grid-offset-minutes 0 --rollover-minutes 360
  python -m retrovue.cli.broadcast_channel_ctl update --id 1 --name "NewName" --active
  python -m retrovue.cli.broadcast_channel_ctl delete --id 1
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all channels")
    list_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show channel details")
    show_parser.add_argument("--id", type=int, required=True, help="Channel ID")
    show_parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new channel")
    create_parser.add_argument("--name", required=True, help="Channel name")
    create_parser.add_argument("--timezone", required=True, help="IANA timezone string")
    create_parser.add_argument("--grid-size-minutes", type=int, required=True, help="Grid size in minutes")
    create_parser.add_argument("--grid-offset-minutes", type=int, required=True, help="Grid offset in minutes")
    create_parser.add_argument("--rollover-minutes", type=int, required=True, help="Rollover minutes after midnight")
    
    # Active/inactive group for create
    active_group = create_parser.add_mutually_exclusive_group()
    active_group.add_argument("--active", action="store_true", help="Set channel as active (default)")
    active_group.add_argument("--inactive", action="store_true", help="Set channel as inactive")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update an existing channel")
    update_parser.add_argument("--id", type=int, required=True, help="Channel ID to update")
    update_parser.add_argument("--name", help="New channel name")
    update_parser.add_argument("--timezone", help="New timezone")
    update_parser.add_argument("--grid-size-minutes", type=int, help="New grid size in minutes")
    update_parser.add_argument("--grid-offset-minutes", type=int, help="New grid offset in minutes")
    update_parser.add_argument("--rollover-minutes", type=int, help="New rollover minutes")
    
    # Active/inactive group for update
    update_active_group = update_parser.add_mutually_exclusive_group()
    update_active_group.add_argument("--active", action="store_true", help="Set channel as active")
    update_active_group.add_argument("--inactive", action="store_true", help="Set channel as inactive")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a channel")
    delete_parser.add_argument("--id", type=int, required=True, help="Channel ID to delete")
    
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # Route to appropriate handler
        if args.command == "list":
            list_channels(json_output=args.json)
        elif args.command == "show":
            show_channel(channel_id=args.id, json_output=args.json)
        elif args.command == "create":
            # Determine is_active value
            is_active = None
            if args.active:
                is_active = True
            elif args.inactive:
                is_active = False
            
            create_channel(
                name=args.name,
                timezone=args.timezone,
                grid_size_minutes=args.grid_size_minutes,
                grid_offset_minutes=args.grid_offset_minutes,
                rollover_minutes=args.rollover_minutes,
                is_active=is_active
            )
        elif args.command == "update":
            # Determine is_active value
            is_active = None
            if args.active:
                is_active = True
            elif args.inactive:
                is_active = False
            
            update_channel(
                channel_id=args.id,
                name=args.name,
                timezone=args.timezone,
                grid_size_minutes=args.grid_size_minutes,
                grid_offset_minutes=args.grid_offset_minutes,
                rollover_minutes=args.rollover_minutes,
                is_active=is_active
            )
        elif args.command == "delete":
            delete_channel(channel_id=args.id)
        
        return 0
    except SystemExit as e:
        return e.code if e.code is not None else 1
    except Exception:
        return 1


def main():
    """Main CLI entry point."""
    sys.exit(run(sys.argv[1:]))


if __name__ == "__main__":
    main()
