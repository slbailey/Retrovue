#!/usr/bin/env python3
"""
CLI for Plex synchronization.

Thin wrapper around the real Plex integration components.
"""

import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure local src/ takes precedence over any installed/legacy 'retrovue'
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

# Import only the non-network components that don't require requests
from retrovue.plex.guid import GuidParser
from retrovue.plex.pathmap import PathMapper
from retrovue.plex.mapper import Mapper
from retrovue.plex.db import Db
from retrovue.plex.config import OFFLINE_EXIT

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("retrovue.plex")


def print_output(message: str):
    """Print output."""
    print(message)


def parse_args():
    """Parse command line arguments manually."""
    if len(sys.argv) < 2:
        return None, {}
    
    # Check for global flags first
    global_flags = {}
    filtered_argv = []
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--offline':
            global_flags['offline'] = True
            i += 1
        elif arg == '--format':
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--'):
                global_flags['format'] = sys.argv[i + 1]
                i += 2
            else:
                global_flags['format'] = 'json'
                i += 1
        elif arg.startswith('--format='):
            global_flags['format'] = arg.split('=', 1)[1]
            i += 1
        else:
            filtered_argv.append(arg)
            i += 1
    
    # Check environment variable for offline mode
    import os
    if os.getenv('PLEX_OFFLINE') == '1':
        global_flags['offline'] = True
    
    if not filtered_argv:
        return None, global_flags
    
    command = filtered_argv[0]
    args = global_flags.copy()
    
    # Handle command groups and subcommands
    if len(filtered_argv) >= 2:
        subcommand = filtered_argv[1]
        
        # Check if subcommand is --help
        if subcommand == '--help':
            # Return the command group with help flag
            args['help'] = True
            return command, args
        
        if command == 'servers':
            command = f'servers_{subcommand}'
            i = 2
        elif command == 'libraries':
            if subcommand == 'sync':
                if len(filtered_argv) >= 3:
                    sync_subcommand = filtered_argv[2]
                    if sync_subcommand == '--help':
                        # Return the libraries_sync command with help flag
                        args['help'] = True
                        return 'libraries_sync', args
                    elif sync_subcommand in ['list', 'enable', 'disable']:
                        # Handle libraries sync list/enable/disable
                        command = f'libraries_sync_{sync_subcommand}'
                        i = 3
                    else:
                        # This is libraries sync with arguments, not a subcommand
                        command = 'libraries_sync'
                        i = 2
                else:
                    # This is just libraries sync with no additional arguments
                    command = 'libraries_sync'
                    i = 2
            else:
                command = f'libraries_{subcommand}'
                i = 2
        elif command == 'mappings':
            command = f'mappings_{subcommand}'
            i = 2
        elif command == 'ingest':
            command = f'ingest_{subcommand}'
            i = 2
        elif command == 'items':
            command = f'items_{subcommand}'
            i = 2
        elif command == 'guid':
            command = f'guid_{subcommand}'
            i = 2
        else:
            i = 1
    else:
        i = 1
    
    while i < len(filtered_argv):
        arg = filtered_argv[i]
        if arg.startswith('--'):
            key = arg[2:]
            if i + 1 < len(filtered_argv) and not filtered_argv[i + 1].startswith('--'):
                args[key] = filtered_argv[i + 1]
                i += 2
            else:
                args[key] = True
                i += 1
        else:
            i += 1
    
    return command, args


def cmd_help():
    """Show help."""
    print("Plex synchronization CLI")
    print("\nCommand Groups:")
    print("  servers     Plex server management")
    print("  libraries   Library management and sync control")
    print("  mappings    Path mapping management")
    print("  ingest      Data ingestion operations")
    print("  items       Item preview and mapping")
    print("  guid        GUID parsing and testing")
    print("\nUse <group> --help for group-specific help")
    print("Use <group> <subcommand> --help for subcommand-specific help")


def cmd_servers_help():
    """Show servers command group help."""
    print("Servers command group - Plex server management")
    print("\nSubcommands:")
    print("  list                    List Plex servers")
    print("  add                     Add a Plex server")
    print("  update-token            Update a Plex server's token")
    print("  set-default             Set the default Plex server")
    print("  delete                  Delete a Plex server")
    print("\nUse 'servers <subcommand> --help' for subcommand-specific help")


def cmd_libraries_help():
    """Show libraries command group help."""
    print("Libraries command group - Library management and sync control")
    print("\nSubcommands:")
    print("  list                    List libraries with sync status")
    print("  sync                    Sync libraries from Plex (default: enable-all)")
    print("  sync list               List libraries with sync status")
    print("  sync enable             Enable sync for a library")
    print("  sync disable            Disable sync for a library")
    print("  delete                  Delete a library")
    print("\nUse 'libraries <subcommand> --help' for subcommand-specific help")


def cmd_mappings_help():
    """Show mappings command group help."""
    print("Mappings command group - Path mapping management")
    print("\nSubcommands:")
    print("  list                    List path mappings for a server and library")
    print("  add                     Add a new path mapping")
    print("  resolve                 Resolve a Plex path to local path")
    print("  test                    Test path mapping functionality")
    print("\nUse 'mappings <subcommand> --help' for subcommand-specific help")


def cmd_ingest_help():
    """Show ingest command group help."""
    print("Ingest command group - Data ingestion operations")
    print("\nSubcommands:")
    print("  run                     Run ingest: discover + map + upsert")
    print("  status                  Show ingest status for libraries")
    print("\nUse 'ingest <subcommand> --help' for subcommand-specific help")


def cmd_items_help():
    """Show items command group help."""
    print("Items command group - Item preview and mapping")
    print("\nSubcommands:")
    print("  preview                 Preview raw items returned by Plex for a library")
    print("  map                     Map one Plex item JSON to our model")
    print("\nUse 'items <subcommand> --help' for subcommand-specific help")


def cmd_guid_help():
    """Show guid command group help."""
    print("GUID command group - GUID parsing and testing")
    print("\nSubcommands:")
    print("  test                    Test GUID parsing")
    print("\nUse 'guid <subcommand> --help' for subcommand-specific help")


# ============================================================================
# SERVERS COMMAND GROUP
# ============================================================================

def cmd_servers_list(args):
    """List Plex servers."""
    if 'help' in args:
        print("List Plex servers")
        print("\nOptions:")
        print("  --db TEXT           Database path (default: ./retrovue.db)")
        print("\nExamples:")
        print("  servers list")
        print("  servers list --db /path/to/retrovue.db")
        return
    
    db_path = args.get('db', './retrovue.db')
    
    try:
        with Db(db_path) as db:
            servers = db.list_plex_servers()
            
            # Check for JSON format
            if args.get('format') == 'json':
                result = {
                    "servers": [
                        {
                            "id": server['id'],
                            "name": server['name'],
                            "base_url": server['base_url'],
                            "is_default": bool(server.get('is_default'))
                        }
                        for server in servers
                    ]
                }
                print(json.dumps(result))
            else:
                if servers:
                    print(f"[OK] Found {len(servers)} Plex servers:")
                    print(f"{'ID':<4} {'Name':<15} {'Base URL':<25} {'Default':<8}")
                    print("-" * 60)
                    for server in servers:
                        default_status = "YES" if server.get('is_default') else "NO"
                        print(f"{server['id']:<4} {server['name'][:14]:<15} {server['base_url'][:24]:<25} {default_status:<8}")
                else:
                    print("[OK] No Plex servers found")
                
    except Exception as e:
        print(f"[ERROR] Failed to list servers: {e}")
        sys.exit(1)


def cmd_servers_add(args):
    """Add a Plex server."""
    if 'help' in args:
        print("Add a Plex server")
        print("\nOptions:")
        print("  --db TEXT           Database path (default: ./retrovue.db)")
        print("  --name TEXT         Server name")
        print("  --base-url TEXT     Server base URL")
        print("  --token TEXT        Server authentication token")
        print("\nExamples:")
        print("  servers add --name \"My Plex\" --base-url http://192.168.1.100:32400 --token abc123")
        return
    
    db_path = args.get('db', './retrovue.db')
    name = args.get('name')
    base_url = args.get('base-url')
    token = args.get('token')
    
    if not name or not base_url or not token:
        print("[ERROR] --name, --base-url, and --token are required")
        sys.exit(1)
    
    try:
        with Db(db_path) as db:
            server_id = db.add_plex_server(name, base_url, token)
            
            # Check for JSON format
            if args.get('format') == 'json':
                result = {
                    "id": server_id,
                    "name": name,
                    "base_url": base_url
                }
                print(json.dumps(result))
            else:
                print(f"[OK] Added server with ID {server_id}: {name} ({base_url})")
                print("Stored Plex token in SQLite (plaintext). Consider restricting file access to this repo.")
                
    except Exception as e:
        print(f"[ERROR] Failed to add server: {e}")
        sys.exit(1)


def cmd_servers_update_token(args):
    """Update a Plex server's token."""
    if 'help' in args:
        print("Update a Plex server's token")
        print("\nOptions:")
        print("  --db TEXT           Database path (default: ./retrovue.db)")
        print("  --server-id INTEGER Server ID")
        print("  --token TEXT        New authentication token")
        print("\nExamples:")
        print("  servers update-token --server-id 1 --token newtoken123")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_id = args.get('server-id')
    token = args.get('token')
    
    if not server_id or not token:
        print("[ERROR] --server-id and --token are required")
        sys.exit(1)
    
    try:
        server_id = int(server_id)
        with Db(db_path) as db:
            rows_updated = db.update_plex_server_token(server_id, token)
            if rows_updated > 0:
                print(f"[OK] Updated token for server ID {server_id} ({rows_updated} row(s) affected)")
            else:
                print(f"[ERROR] Server ID {server_id} not found")
                sys.exit(1)
                
    except ValueError:
        print("[ERROR] --server-id must be an integer")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to update token: {e}")
        sys.exit(1)


def cmd_servers_set_default(args):
    """Set the default Plex server."""
    if 'help' in args:
        print("Set the default Plex server")
        print("\nOptions:")
        print("  --db TEXT           Database path (default: ./retrovue.db)")
        print("  --server-id INTEGER Server ID to set as default")
        print("  --server-name TEXT  Server name to set as default")
        print("\nExamples:")
        print("  servers set-default --server-id 1")
        print("  servers set-default --server-name \"My Plex\"")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_name = args.get('server-name')
    server_id = args.get('server-id')
    
    if not server_name and not server_id:
        print("[ERROR] Either --server-name or --server-id is required")
        sys.exit(1)
    
    if server_name and server_id:
        print("[ERROR] Specify either --server-name or --server-id, not both")
        sys.exit(1)
    
    try:
        with Db(db_path) as db:
            if server_name:
                # Verify server exists
                server = db.get_plex_server_by_name(server_name)
                if not server:
                    print(f"[ERROR] Server '{server_name}' not found")
                    sys.exit(2)
                
                db.set_default_server_by_name(server_name)
                print(f"[OK] Set '{server_name}' as default server")
            else:
                # Verify server exists
                server = db.get_plex_server_by_id(int(server_id))
                if not server:
                    print(f"[ERROR] Server ID {server_id} not found")
                    sys.exit(2)
                
                db.set_default_server_by_id(int(server_id))
                print(f"[OK] Set server ID {server_id} as default server")
                
    except Exception as e:
        print(f"[ERROR] Failed to set default server: {e}")
        sys.exit(1)


def cmd_servers_delete(args):
    """Delete a Plex server."""
    if 'help' in args:
        print("Delete a Plex server")
        print("\nOptions:")
        print("  --db TEXT           Database path (default: ./retrovue.db)")
        print("  --server-id INTEGER Server ID to delete")
        print("\nExamples:")
        print("  servers delete --server-id 1")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_id = args.get('server-id')
    
    if not server_id:
        print("[ERROR] --server-id is required")
        sys.exit(1)
    
    try:
        server_id = int(server_id)
        with Db(db_path) as db:
            rows_deleted = db.delete_plex_server(server_id)
            if rows_deleted > 0:
                print(f"[OK] Deleted server ID {server_id} ({rows_deleted} row(s) affected)")
            else:
                print(f"[ERROR] Server ID {server_id} not found")
                sys.exit(1)
                
    except ValueError:
        print("[ERROR] --server-id must be an integer")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to delete server: {e}")
        sys.exit(1)


# ============================================================================
# LIBRARIES COMMAND GROUP
# ============================================================================

def cmd_libraries_list(args):
    """List libraries with sync status."""
    if 'help' in args:
        print("List libraries with sync status")
        print("\nOptions:")
        print("  --db TEXT           Database path (default: ./retrovue.db)")
        print("  --server-name TEXT  Server name (from stored credentials)")
        print("  --server-id INTEGER Server ID (from stored credentials)")
        print("\nExamples:")
        print("  libraries list")
        print("  libraries list --server-id 1")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_name = args.get('server-name')
    server_id = args.get('server-id')
    
    try:
        with Db(db_path) as db:
            # Resolve server if specified
            server_id_filter = None
            if server_name or server_id:
                from retrovue.plex.config import resolve_server
                server = resolve_server(db, server_name, int(server_id) if server_id else None)
                server_id_filter = server['id']
            
            libraries = db.list_libraries(server_id_filter)
            
            # Check for JSON format
            if args.get('format') == 'json':
                result = {
                    "libraries": [
                        {
                            "id": lib['id'],
                            "server_id": lib['server_id'],
                            "plex_library_key": lib['plex_library_key'],
                            "title": lib['title'],
                            "library_type": lib['library_type'],
                            "sync_enabled": bool(lib['sync_enabled']),
                            "last_full_sync_epoch": lib['last_full_sync_epoch'],
                            "last_incremental_sync_epoch": lib['last_incremental_sync_epoch'],
                            "created_at": lib['created_at'],
                            "updated_at": lib['updated_at']
                        }
                        for lib in libraries
                    ]
                }
                print(json.dumps(result))
            else:
                if not libraries:
                    print("No libraries found")
                    return
                
                print(f"Libraries (showing {len(libraries)}):")
                print(f"{'ID':<4} {'Key':<6} {'Title':<20} {'Type':<8} {'Sync':<5} {'Last Full':<20} {'Last Incr':<20}")
                print("-" * 90)
                
                for lib in libraries:
                    sync_status = "ON" if lib['sync_enabled'] else "OFF"
                    
                    # Format timestamps
                    last_full = "Never"
                    if lib['last_full_sync_epoch']:
                        import datetime
                        dt = datetime.datetime.fromtimestamp(lib['last_full_sync_epoch'])
                        last_full = f"{dt.strftime('%Y-%m-%d %H:%M')}"
                    
                    last_incr = "Never"
                    if lib['last_incremental_sync_epoch']:
                        import datetime
                        dt = datetime.datetime.fromtimestamp(lib['last_incremental_sync_epoch'])
                        last_incr = f"{dt.strftime('%Y-%m-%d %H:%M')}"
                    
                    print(f"{lib['id']:<4} {lib['plex_library_key']:<6} {lib['title'][:19]:<20} {lib['library_type']:<8} {sync_status:<5} {last_full:<20} {last_incr:<20}")
                
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(2)
    except Exception as e:
        print(f"[ERROR] Failed to list libraries: {e}")
        sys.exit(1)


def cmd_libraries_sync(args):
    """Sync libraries from Plex (default: enable-all)."""
    if 'help' in args:
        print("Sync libraries from Plex")
        print("\nOptions:")
        print("  --db TEXT           Database path (default: ./retrovue.db)")
        print("  --server-name TEXT  Server name (from stored credentials)")
        print("  --server-id INTEGER Server ID (from stored credentials)")
        print("  --enable-all        Enable sync for all imported libraries (default)")
        print("  --disable-all       Disable sync for all imported libraries")
        print("\nExamples:")
        print("  libraries sync")
        print("  libraries sync --server-id 1")
        print("  libraries sync --server-id 1 --disable-all")
        print("  libraries sync --server-id 1 --enable-all")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_name = args.get('server-name')
    server_id = args.get('server-id')
    enable_all = args.get('enable-all', False)
    disable_all = args.get('disable-all', False)
    
    # Default behavior: if neither flag is specified, default to enable-all
    if not enable_all and not disable_all:
        enable_all = True
    
    if enable_all and disable_all:
        print("[ERROR] Cannot specify both --enable-all and --disable-all")
        sys.exit(1)
    
    # Check for offline mode
    if args.get('offline'):
        print("[ERROR] Offline mode: network operations disabled.")
        sys.exit(OFFLINE_EXIT)
    
    try:
        # Lazy import to avoid pulling requests for non-network commands
        from retrovue.plex.client import PlexClient
        import requests
        
        with Db(db_path) as db:
            # Resolve server
            from retrovue.plex.config import resolve_server
            server = resolve_server(db, server_name, int(server_id) if server_id else None)
            
            # Create Plex client
            plex_client = PlexClient(server['base_url'], server['token'])
            
            # Fetch libraries from Plex
            plex_libraries = plex_client.get_libraries()
            
            if not plex_libraries:
                print("No libraries found in Plex")
                return
            
            # Upsert each library
            inserted = 0
            updated = 0
            total = len(plex_libraries)
            returned_keys = []
            
            for plex_lib in plex_libraries:
                # Check if library already exists
                existing = db.get_library_by_key(server['id'], plex_lib.key)
                
                # Use section type (movie/show) instead of item kind
                library_type = plex_lib.type
                if library_type not in ['movie', 'show']:
                    logger.warning(f"Unknown library type '{library_type}' for library {plex_lib.key}, defaulting to 'movie'")
                    library_type = 'movie'
                
                library_id = db.upsert_library(
                    server['id'], 
                    int(plex_lib.key), 
                    plex_lib.title, 
                    library_type
                )
                
                if existing:
                    updated += 1
                else:
                    inserted += 1
                
                returned_keys.append(int(plex_lib.key))
            
            # Handle bulk enable/disable if requested
            if enable_all or disable_all:
                sync_value = 1 if enable_all else 0
                if returned_keys:
                    # Create placeholders for the IN clause
                    placeholders = ','.join(['?' for _ in returned_keys])
                    cursor = db.execute(f"""
                        UPDATE libraries 
                        SET sync_enabled = ?, updated_at = datetime('now')
                        WHERE server_id = ? AND plex_library_key IN ({placeholders})
                    """, [sync_value, server['id']] + returned_keys)
                    db.commit()
            
            unchanged = total - (inserted + updated)
            
            # Print clear summary
            print(f"\n=== LIBRARY SYNC SUMMARY ===")
            print(f"Libraries processed: {total}")
            print(f"  - Inserted: {inserted}")
            print(f"  - Updated: {updated}")
            print(f"  - Unchanged: {unchanged}")
            
            if enable_all:
                print(f"Sync enabled for: {len(returned_keys)} libraries")
            elif disable_all:
                print(f"Sync disabled for: {len(returned_keys)} libraries")
                
    except ImportError as e:
        print(f"[ERROR] Missing required module: {e}")
        print("[ERROR] Please install required dependencies: pip install requests")
        sys.exit(1)
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(2)
    except Exception as e:
        # Check if it's a requests-related error
        if 'requests' in str(type(e).__module__):
            if hasattr(e, 'response') and e.response:
                if e.response.status_code in [401, 403]:
                    print(f"[ERROR] Authentication failed (HTTP {e.response.status_code}): Invalid token")
                else:
                    print(f"[ERROR] HTTP error {e.response.status_code}: {e}")
                sys.exit(OFFLINE_EXIT)
            else:
                print(f"[ERROR] Connection failed: {e}")
                sys.exit(OFFLINE_EXIT)
        else:
            print(f"[ERROR] Failed to sync libraries from Plex: {e}")
            sys.exit(1)


def cmd_libraries_sync_list(args):
    """List libraries with sync status."""
    # This is the same as libraries list, but we'll keep it for consistency
    cmd_libraries_list(args)


def cmd_libraries_sync_enable(args):
    """Enable sync for a library."""
    if 'help' in args:
        print("Enable sync for a library")
        print("\nOptions:")
        print("  --db TEXT           Database path (default: ./retrovue.db)")
        print("  --library-id INTEGER Library ID to enable")
        print("\nExamples:")
        print("  libraries sync enable --library-id 1")
        return
    
    db_path = args.get('db', './retrovue.db')
    library_id = args.get('library-id')
    
    if not library_id:
        print("[ERROR] --library-id is required")
        sys.exit(1)
    
    try:
        with Db(db_path) as db:
            rows_updated = db.set_library_sync(int(library_id), True)
            
            if rows_updated > 0:
                print(f"[OK] Enabled sync for library ID {library_id}")
            else:
                print(f"[ERROR] Library ID {library_id} not found")
                sys.exit(2)
                
    except Exception as e:
        print(f"[ERROR] Failed to enable sync: {e}")
        sys.exit(1)


def cmd_libraries_sync_disable(args):
    """Disable sync for a library."""
    if 'help' in args:
        print("Disable sync for a library")
        print("\nOptions:")
        print("  --db TEXT           Database path (default: ./retrovue.db)")
        print("  --library-id INTEGER Library ID to disable")
        print("\nExamples:")
        print("  libraries sync disable --library-id 1")
        return
    
    db_path = args.get('db', './retrovue.db')
    library_id = args.get('library-id')
    
    if not library_id:
        print("[ERROR] --library-id is required")
        sys.exit(1)
    
    try:
        with Db(db_path) as db:
            rows_updated = db.set_library_sync(int(library_id), False)
            
            if rows_updated > 0:
                print(f"[OK] Disabled sync for library ID {library_id}")
            else:
                print(f"[ERROR] Library ID {library_id} not found")
                sys.exit(2)
                
    except Exception as e:
        print(f"[ERROR] Failed to disable sync: {e}")
        sys.exit(1)


def cmd_libraries_delete(args):
    """Delete a library."""
    if 'help' in args:
        print("Delete a library")
        print("\nOptions:")
        print("  --db TEXT           Database path (default: ./retrovue.db)")
        print("  --server-name TEXT  Server name (from stored credentials)")
        print("  --server-id INTEGER Server ID (from stored credentials)")
        print("  --library-id INTEGER Library ID to delete")
        print("  --all               Delete all libraries for the selected/default server")
        print("  --yes               Confirm deletion (required for --all)")
        print("\nExamples:")
        print("  libraries delete --library-id 1")
        print("  libraries delete --all --yes")
        print("  libraries delete --all --yes --server-id 1")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_name = args.get('server-name')
    server_id = args.get('server-id')
    library_id = args.get('library-id')
    delete_all = args.get('all', False)
    confirm = args.get('yes', False)
    
    if delete_all:
        if not confirm:
            print("[ERROR] --yes is required to confirm deletion of all libraries")
            sys.exit(2)
        
        try:
            with Db(db_path) as db:
                # Resolve server if specified
                if server_name or server_id:
                    from retrovue.plex.config import resolve_server
                    server = resolve_server(db, server_name, int(server_id) if server_id else None)
                    server_id_filter = server['id']
                    server_name_display = server['name']
                else:
                    # Use default server
                    from retrovue.plex.config import resolve_server
                    server = resolve_server(db, None, None)
                    server_id_filter = server['id']
                    server_name_display = server['name']
                
                # Count libraries before deletion for confirmation
                libraries = db.list_libraries(server_id_filter)
                library_count = len(libraries)
                
                if library_count == 0:
                    if args.get('format') == 'json':
                        result = {"libraries": []}
                        print(json.dumps(result))
                    else:
                        print(f"[OK] No libraries found for server '{server_name_display}' (ID: {server_id_filter})")
                    return
                
                # Delete all libraries for the server
                rows_affected = db.delete_all_libraries_for_server(server_id_filter)
                
                if args.get('format') == 'json':
                    result = {"libraries": []}
                    print(json.dumps(result))
                else:
                    print(f"[OK] Deleted {rows_affected} libraries from server '{server_name_display}' (ID: {server_id_filter})")
                
        except ValueError as e:
            print(f"[ERROR] {e}")
            sys.exit(2)
        except Exception as e:
            print(f"[ERROR] Failed to delete all libraries: {e}")
            sys.exit(1)
    else:
        if not library_id:
            print("[ERROR] --library-id is required (or use --all --yes to delete all)")
            sys.exit(1)
        
        try:
            with Db(db_path) as db:
                rows_affected = db.delete_library(int(library_id))
                
                if rows_affected > 0:
                    print(f"[OK] Deleted library ID {library_id}")
                else:
                    print(f"[ERROR] Library ID {library_id} not found")
                    sys.exit(2)
                    
        except Exception as e:
            print(f"[ERROR] Failed to delete library: {e}")
            sys.exit(1)


# ============================================================================
# MAPPINGS COMMAND GROUP
# ============================================================================

def cmd_mappings_list(args):
    """List path mappings for a server and library."""
    if 'help' in args:
        print("List path mappings for a server and library")
        print("\nOptions:")
        print("  --db TEXT           Database path (default: ./retrovue.db)")
        print("  --server-id INTEGER Server ID")
        print("  --library-id INTEGER Library ID")
        print("\nExamples:")
        print("  mappings list --server-id 1 --library-id 1")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_id = args.get('server-id')
    library_id = args.get('library-id')
    
    if not server_id or not library_id:
        print("[ERROR] --server-id and --library-id are required")
        sys.exit(1)
    
    try:
        with Db(db_path) as db:
            path_mapper = PathMapper(db.conn)
            mappings = path_mapper.list_mappings(int(server_id), int(library_id))
            
            # Check for JSON format
            if args.get('format') == 'json':
                result = {
                    "mappings": [
                        {
                            "plex_prefix": plex_prefix,
                            "local_prefix": local_prefix
                        }
                        for plex_prefix, local_prefix in mappings
                    ]
                }
                print(json.dumps(result))
            else:
                if mappings:
                    print(f"[OK] Found {len(mappings)} path mappings for server {server_id}, library {library_id}:")
                    for plex_prefix, local_prefix in mappings:
                        print(f"  {plex_prefix} -> {local_prefix}")
                else:
                    print(f"[OK] No path mappings found for server {server_id}, library {library_id}")
                
    except Exception as e:
        print(f"[ERROR] Failed to list mappings: {e}")
        sys.exit(1)


def cmd_mappings_add(args):
    """Add a new path mapping."""
    if 'help' in args:
        print("Add a new path mapping")
        print("\nOptions:")
        print("  --db TEXT           Database path (default: ./retrovue.db)")
        print("  --server-id INTEGER Server ID")
        print("  --library-id INTEGER Library ID")
        print("  --plex-prefix TEXT  Plex path prefix")
        print("  --local-prefix TEXT Local path prefix")
        print("\nExamples:")
        print("  mappings add --server-id 1 --library-id 1 --plex-prefix \"/data/TV\" --local-prefix \"D:\\TV\"")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_id = args.get('server-id')
    library_id = args.get('library-id')
    plex_prefix = args.get('plex-prefix')
    local_prefix = args.get('local-prefix')
    
    if not server_id or not library_id or not plex_prefix or not local_prefix:
        print("[ERROR] --server-id, --library-id, --plex-prefix, and --local-prefix are required")
        sys.exit(1)
    
    try:
        with Db(db_path) as db:
            mapping_id = db.insert_path_mapping(int(server_id), int(library_id), plex_prefix, local_prefix)
            print(f"[OK] Added path mapping with ID {mapping_id}:")
            print(f"  {plex_prefix} -> {local_prefix}")
                
    except Exception as e:
        print(f"[ERROR] Failed to add mapping: {e}")
        sys.exit(1)


def cmd_mappings_resolve(args):
    """Resolve a Plex path to local path via DB path_mappings."""
    if 'help' in args:
        print("Resolve a Plex path to local path via DB path_mappings")
        print("\nOptions:")
        print("  --db TEXT           Database path (default: ./retrovue.db)")
        print("  --server-id INTEGER Server ID")
        print("  --library-id INTEGER Library ID")
        print("  --plex-path TEXT    Plex path to resolve")
        print("\nExamples:")
        print("  mappings resolve --server-id 1 --library-id 1 --plex-path \"/data/TV/Show/ep1.mkv\"")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_id = args.get('server-id')
    library_id = args.get('library-id')
    plex_path = args.get('plex-path')
    
    if not server_id or not library_id or not plex_path:
        print("[ERROR] --server-id, --library-id, and --plex-path are required")
        sys.exit(1)
    
    try:
        with Db(db_path) as db:
            path_mapper = PathMapper(db.conn)
            local_path = path_mapper.resolve(int(server_id), int(library_id), plex_path)
            
            if local_path:
                print(f"[OK] Resolved path: {plex_path} -> {local_path}")
            else:
                print(f"No mapping found for: {plex_path}")
                sys.exit(2)
                
    except Exception as e:
        print(f"[ERROR] Failed to resolve path: {e}")
        sys.exit(1)


def cmd_mappings_test(args):
    """Test path mapping functionality."""
    if 'help' in args:
        print("Test path mapping functionality")
        print("\nOptions:")
        print("  --db TEXT           Database path (default: ./retrovue.db)")
        print("  --server-id INTEGER Server ID")
        print("  --library-id INTEGER Library ID")
        print("  --plex-path TEXT    Plex path to test")
        print("\nExamples:")
        print("  mappings test --server-id 1 --library-id 1 --plex-path \"/data/TV/Show/ep1.mkv\"")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_id = args.get('server-id')
    library_id = args.get('library-id')
    plex_path = args.get('plex-path')
    
    if not server_id or not library_id or not plex_path:
        print("[ERROR] --server-id, --library-id, and --plex-path are required")
        sys.exit(1)
    
    try:
        with Db(db_path) as db:
            path_mapper = PathMapper(db.conn)
            local_path = path_mapper.resolve(int(server_id), int(library_id), plex_path)
            
            print(f"[OK] Path mapping test:")
            print(f"  Plex: {plex_path}")
            print(f"  Local: {local_path}")
            
    except Exception as e:
        print(f"[ERROR] Path mapping test failed: {e}")
        sys.exit(1)


# ============================================================================
# INGEST COMMAND GROUP
# ============================================================================

def cmd_ingest_run(args):
    """Run ingest: discover + map + upsert (writes to database)."""
    if 'help' in args:
        print("Run ingest: discover + map + upsert (writes to database)")
        print("\nOptions:")
        print("  --db TEXT           Database path (default: ./retrovue.db)")
        print("  --server-name TEXT  Server name (from stored credentials)")
        print("  --server-id INTEGER Server ID (from stored credentials)")
        print("  --mode TEXT         Ingest mode: 'full' or 'incremental' (default: full)")
        print("  --since-epoch INTEGER Manual since epoch for incremental mode")
        print("  --libraries TEXT    Comma-separated library IDs (default: all sync-enabled)")
        print("  --kinds TEXT        Comma-separated content kinds (default: movie,episode)")
        print("  --limit INTEGER     Maximum items per library")
        print("  --batch-size INTEGER Batch size for commits (default: 50)")
        print("  --dry-run           Show planned inserts/updates only (default)")
        print("  --commit            Perform actual database writes")
        print("  --verbose, -v       Enable verbose output")
        print("\nExamples:")
        print("  ingest run --dry-run")
        print("  ingest run --commit --server-id 1 --libraries 1,2")
        print("  ingest run --mode incremental --since-epoch 1640995200 --commit")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_name = args.get('server-name')
    server_id = args.get('server-id')
    mode = args.get('mode', 'full')
    since_epoch = args.get('since-epoch')
    libraries_str = args.get('libraries', '')
    kinds_str = args.get('kinds', 'movie,episode')
    limit = args.get('limit')
    batch_size = int(args.get('batch-size', 50))
    dry_run = args.get('dry-run', False)
    commit = args.get('commit', False)
    verbose = args.get('verbose', False)
    
    # Default to dry-run if neither dry-run nor commit is specified
    if not dry_run and not commit:
        dry_run = True
    
    # Parse since_epoch if provided
    if since_epoch:
        try:
            since_epoch = int(since_epoch)
        except ValueError:
            print("[ERROR] --since-epoch must be an integer")
            sys.exit(1)
    
    # Parse kinds
    kinds = [x.strip() for x in kinds_str.split(',') if x.strip()]
    
    # Check for offline mode
    if args.get('offline'):
        print("[ERROR] Offline mode: network operations disabled.")
        sys.exit(OFFLINE_EXIT)
    
    try:
        # Lazy import to avoid pulling requests for non-network commands
        from retrovue.plex.client import PlexClient
        from retrovue.plex.config import resolve_server
        from retrovue.plex.ingest import IngestOrchestrator
        from retrovue.plex.pathmap import PathMapper
        import requests
        
        # Set logging level
        if verbose:
            logging.getLogger("retrovue.plex").setLevel(logging.DEBUG)
        
        # Resolve server credentials from database
        with Db(db_path) as db:
            server = resolve_server(db, server_name, int(server_id) if server_id else None)
        
        # Create Plex client
        plex_client = PlexClient(server['base_url'], server['token'])
        
        # Determine libraries to process
        with Db(db_path) as db:
            if libraries_str:
                # Use explicitly specified libraries
                libraries = [int(x.strip()) for x in libraries_str.split(',') if x.strip()]
            else:
                # Use all sync-enabled libraries
                libraries = db.list_sync_enabled_library_keys(server['id'])
                if not libraries:
                    print("[ERROR] No sync-enabled libraries found. Use --libraries to specify libraries or enable sync for libraries.")
                    sys.exit(2)
        
        # Run ingest for each library and kind combination
        total_stats = {
            "scanned": 0, "mapped": 0, "inserted_items": 0, "updated_items": 0,
            "inserted_files": 0, "updated_files": 0, "linked": 0, "skipped": 0, "errors": 0
        }
        
        with Db(db_path) as db:
            path_mapper = PathMapper(db.conn)
            orchestrator = IngestOrchestrator(db, plex_client, path_mapper, logger)
            
            for library_key in libraries:
                for kind in kinds:
                    print(f"\nProcessing library {library_key} ({kind}) in {mode} mode...")
                    
                    stats = orchestrator.ingest_library(
                        server, library_key, kind, 
                        mode=mode,
                        since_epoch=since_epoch,
                        limit=int(limit) if limit else None,
                        dry_run=dry_run, 
                        verbose=verbose,
                        batch_size=batch_size
                    )
                    
                    # Accumulate stats
                    for key in total_stats:
                        total_stats[key] += stats[key]
                    
                    print(f"Library {library_key} ({kind}): {stats['scanned']} scanned, {stats['mapped']} mapped, {stats['errors']} errors")
        
        # Print final summary
        print(f"\n=== FINAL SUMMARY ===")
        print(f"Total scanned: {total_stats['scanned']}")
        print(f"Total mapped: {total_stats['mapped']}")
        print(f"Total items: {total_stats['inserted_items']}")
        print(f"Total files: {total_stats['inserted_files']}")
        print(f"Total linked: {total_stats['linked']}")
        print(f"Total errors: {total_stats['errors']}")
        
        if dry_run:
            print(f"\n[DRY RUN] No database writes were performed. Use --commit to perform actual writes.")
        else:
            print(f"\n[COMMIT] Database writes completed successfully.")
        
        if total_stats['errors'] > 0:
            print(f"\n[WARNING] {total_stats['errors']} errors occurred during ingest.")
            sys.exit(1)
        else:
            print(f"\n[OK] Ingest completed successfully.")
            
    except ImportError as e:
        print(f"[ERROR] Missing required module: {e}")
        print("[ERROR] Please install required dependencies: pip install requests")
        sys.exit(1)
    except ValueError as e:
        # Server not found or no default set
        print(f"[ERROR] {e}")
        sys.exit(2)
    except Exception as e:
        # Check if it's a requests-related error
        if 'requests' in str(type(e).__module__):
            if hasattr(e, 'response') and e.response:
                if e.response.status_code in [401, 403]:
                    print(f"[ERROR] Authentication failed (HTTP {e.response.status_code}): Invalid token")
                else:
                    print(f"[ERROR] HTTP error {e.response.status_code}: {e}")
                sys.exit(OFFLINE_EXIT)
            else:
                print(f"[ERROR] Connection failed: {e}")
                sys.exit(OFFLINE_EXIT)
        else:
            print(f"[ERROR] Ingest failed: {e}")
            sys.exit(1)


def cmd_ingest_status(args):
    """Show ingest status for libraries."""
    if 'help' in args:
        print("Show ingest status for libraries")
        print("\nOptions:")
        print("  --db TEXT           Database path (default: ./retrovue.db)")
        print("  --server-name TEXT  Server name (from stored credentials)")
        print("  --server-id INTEGER Server ID (from stored credentials)")
        print("\nExamples:")
        print("  ingest status")
        print("  ingest status --server-id 1")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_name = args.get('server-name')
    server_id = args.get('server-id')
    
    try:
        with Db(db_path) as db:
            # Resolve server if specified
            server_id_filter = None
            if server_name or server_id:
                from retrovue.plex.config import resolve_server
                server = resolve_server(db, server_name, int(server_id) if server_id else None)
                server_id_filter = server['id']
            
            libraries = db.list_libraries(server_id_filter)
            
            if not libraries:
                print("No libraries found")
                return
            
            print(f"Ingest Status (showing {len(libraries)} libraries):")
            print(f"{'ID':<4} {'Key':<6} {'Title':<20} {'Type':<8} {'Sync':<5} {'Last Full':<20} {'Last Incr':<20}")
            print("-" * 90)
            
            for lib in libraries:
                sync_status = "ON" if lib['sync_enabled'] else "OFF"
                
                # Format timestamps
                last_full = "Never"
                if lib['last_full_sync_epoch']:
                    import datetime
                    dt = datetime.datetime.fromtimestamp(lib['last_full_sync_epoch'])
                    last_full = f"{dt.strftime('%Y-%m-%d %H:%M')} ({lib['last_full_sync_epoch']})"
                
                last_incr = "Never"
                if lib['last_incremental_sync_epoch']:
                    import datetime
                    dt = datetime.datetime.fromtimestamp(lib['last_incremental_sync_epoch'])
                    last_incr = f"{dt.strftime('%Y-%m-%d %H:%M')} ({lib['last_incremental_sync_epoch']})"
                
                print(f"{lib['id']:<4} {lib['plex_library_key']:<6} {lib['title'][:19]:<20} {lib['library_type']:<8} {sync_status:<5} {last_full:<20} {last_incr:<20}")
                
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(2)
    except Exception as e:
        print(f"[ERROR] Failed to show ingest status: {e}")
        sys.exit(1)


# ============================================================================
# ITEMS COMMAND GROUP
# ============================================================================

def cmd_items_preview(args):
    """Preview raw items returned by Plex for a library."""
    if 'help' in args:
        print("Preview raw items returned by Plex for a library")
        print("\nOptions:")
        print("  --db TEXT           Database path (default: ./retrovue.db)")
        print("  --server-name TEXT  Server name (from stored credentials)")
        print("  --server-id INTEGER Server ID (from stored credentials)")
        print("  --library-key TEXT  Library key")
        print("  --kind TEXT         Content kind (movie, episode)")
        print("  --limit INTEGER     Number of items to preview")
        print("\nExamples:")
        print("  items preview --library-key 1 --kind movie --limit 5")
        print("  items preview --server-id 1 --library-key 2 --kind episode")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_name = args.get('server-name')
    server_id = args.get('server-id')
    library_key = args.get('library-key')
    kind = args.get('kind', 'movie')
    limit = int(args.get('limit', 5))
    
    if not library_key:
        print("[ERROR] --library-key is required")
        sys.exit(1)
    
    # Check for offline mode
    if args.get('offline'):
        print("[ERROR] Offline mode: network operations disabled.")
        sys.exit(OFFLINE_EXIT)
    
    try:
        # Lazy import to avoid pulling requests for non-network commands
        from retrovue.plex.client import PlexClient
        from retrovue.plex.config import resolve_server
        import requests
        
        # Resolve server credentials from database
        with Db(db_path) as db:
            server = resolve_server(db, server_name, int(server_id) if server_id else None)
        
        client = PlexClient(server['base_url'], server['token'])
        items = list(client.iter_items(library_key, kind, limit))
        
        print(f"[OK] Found {len(items)} {kind} items in library {library_key}:")
        for i, item in enumerate(items, 1):
            if kind == 'movie':
                duration_min = int(item.get('duration', 0)) // 60000 if item.get('duration') else 0
                print(f"  {i}. {item.get('title', 'Unknown')} (ratingKey: {item.get('ratingKey', 'N/A')}, {duration_min}min, updated: {item.get('updatedAt', 'N/A')})")
            elif kind == 'episode':
                season = item.get('parentIndex', 0)
                episode = item.get('index', 0)
                show = item.get('grandparentTitle', 'Unknown Show')
                print(f"  {i}. {show} S{season:02d}E{episode:02d} - {item.get('title', 'Unknown')} (ratingKey: {item.get('ratingKey', 'N/A')})")
            else:
                print(f"  {i}. {item.get('title', 'Unknown')} (ratingKey: {item.get('ratingKey', 'N/A')})")
            
    except ImportError as e:
        print(f"[ERROR] Missing required module: {e}")
        print("[ERROR] Please install required dependencies: pip install requests")
        sys.exit(1)
    except ValueError as e:
        # Server not found or no default set
        print(f"[ERROR] {e}")
        sys.exit(2)
    except Exception as e:
        # Check if it's a requests-related error
        if 'requests' in str(type(e).__module__):
            if hasattr(e, 'response') and e.response:
                if e.response.status_code in [401, 403]:
                    print(f"[ERROR] Authentication failed (HTTP {e.response.status_code}): Invalid token")
                elif e.response.status_code == 404:
                    print(f"[ERROR] Library {library_key} not found")
                else:
                    print(f"[ERROR] HTTP error {e.response.status_code}: {e}")
                sys.exit(OFFLINE_EXIT)
            else:
                print(f"[ERROR] Connection failed: {e}")
                sys.exit(OFFLINE_EXIT)
        else:
            print(f"[ERROR] Failed to fetch items: {e}")
            sys.exit(1)


def cmd_items_map(args):
    """Map one Plex item JSON to our model."""
    if 'help' in args:
        print("Map one Plex item JSON to our model")
        print("\nOptions:")
        print("  --from-json TEXT   JSON file path")
        print("  --from-stdin       Read from stdin")
        print("\nExamples:")
        print("  items map --from-json item.json")
        print("  echo '{\"title\":\"Movie\"}' | items map --from-stdin")
        return
    
    if args.get('from-stdin'):
        json_data = json.loads(sys.stdin.read())
    elif 'from-json' in args:
        with open(args['from-json'], 'r') as f:
            json_data = json.load(f)
    else:
        print("[ERROR] Must specify either --from-json or --from-stdin")
        sys.exit(1)
    
    mapper = Mapper()
    result = mapper.map_from_json(json_data)
    
    print(f"[OK] Mapped: {result.get('title', 'Unknown')} ({result.get('kind', 'unknown')})")
    if result.get('duration_ms'):
        print(f"  Duration: {result['duration_ms']} ms")
    if result.get('rating'):
        print(f"  Rating: {result['rating']}")


# ============================================================================
# GUID COMMAND GROUP
# ============================================================================

def cmd_guid_test(args):
    """Test GUID parsing."""
    if 'help' in args:
        print("Test GUID parsing")
        print("\nOptions:")
        print("  --guid TEXT   GUID string to parse")
        print("\nExamples:")
        print("  guid test --guid \"com.plexapp.agents.imdb://tt1234567\"")
        print("  guid test --guid \"com.plexapp.agents.thetvdb://123456\"")
        return
    
    guid = args.get('guid', '')
    if not guid:
        print("[ERROR] --guid is required")
        sys.exit(1)
    
    parser = GuidParser()
    result = parser.parse(guid)
    
    print(f"[OK] Parsed GUID: {guid}")
    for key, value in result.items():
        if value:
            print(f"  {key}: {value}")


# ============================================================================
# MAIN DISPATCHER
# ============================================================================

def main():
    """Main CLI entry point."""
    command, args = parse_args()
    
    if not command or command == '--help':
        cmd_help()
        return
    
    # Handle command group help
    if args.get('help') and command in ['servers', 'libraries', 'mappings', 'ingest', 'items', 'guid']:
        if command == 'servers':
            cmd_servers_help()
        elif command == 'libraries':
            cmd_libraries_help()
        elif command == 'mappings':
            cmd_mappings_help()
        elif command == 'ingest':
            cmd_ingest_help()
        elif command == 'items':
            cmd_items_help()
        elif command == 'guid':
            cmd_guid_help()
        return
    
    commands = {
        # Servers commands
        'servers_list': cmd_servers_list,
        'servers_add': cmd_servers_add,
        'servers_update-token': cmd_servers_update_token,
        'servers_set-default': cmd_servers_set_default,
        'servers_delete': cmd_servers_delete,
        
        # Libraries commands
        'libraries_list': cmd_libraries_list,
        'libraries_sync': cmd_libraries_sync,
        'libraries_sync_list': cmd_libraries_sync_list,
        'libraries_sync_enable': cmd_libraries_sync_enable,
        'libraries_sync_disable': cmd_libraries_sync_disable,
        'libraries_delete': cmd_libraries_delete,
        
        # Mappings commands
        'mappings_list': cmd_mappings_list,
        'mappings_add': cmd_mappings_add,
        'mappings_resolve': cmd_mappings_resolve,
        'mappings_test': cmd_mappings_test,
        
        # Ingest commands
        'ingest_run': cmd_ingest_run,
        'ingest_status': cmd_ingest_status,
        
        # Items commands
        'items_preview': cmd_items_preview,
        'items_map': cmd_items_map,
        
        # GUID commands
        'guid_test': cmd_guid_test,
    }
    
    if command in commands:
        commands[command](args)
    else:
        print(f"Unknown command: {command}")
        cmd_help()
        sys.exit(1)


if __name__ == "__main__":
    main()