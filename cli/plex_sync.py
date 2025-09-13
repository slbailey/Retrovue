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
    
    command = sys.argv[1]
    args = {}
    
    # Handle subcommands
    if command == 'servers' and len(sys.argv) >= 3:
        subcommand = sys.argv[2]
        command = f'servers_{subcommand}'
        i = 3
    elif command == 'sync-libraries' and len(sys.argv) >= 3:
        subcommand = sys.argv[2]
        command = f'sync_libraries_{subcommand}'
        i = 3
    elif command == 'libraries' and len(sys.argv) >= 3:
        subcommand = sys.argv[2]
        command = f'libraries_{subcommand}'
        i = 3
    else:
        i = 2
    
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.startswith('--'):
            key = arg[2:]
            if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--'):
                args[key] = sys.argv[i + 1]
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
    print("\nCommands:")
    print("  libraries     List Plex libraries")
    print("  preview-items Preview raw items returned by Plex for a library")
    print("  resolve-path  Resolve a Plex path to local path via DB path_mappings")
    print("  map-item      Map one Plex item JSON to our model")
    print("  ingest        Ingest: discover + map + upsert (writes to database)")
    print("  test-guid     Test GUID parsing")
    print("  test-pathmap  Test path mapping functionality")
    print("  list-mappings List path mappings for a server and library")
    print("  add-mapping   Add a new path mapping")
    print("  servers       Plex server management (add, list, delete, update-token, set-default)")
    print("  libraries     Library management (list, tag, tag-all, tag-none, delete, delete-all, sync-from-plex)")
    print("  sync-libraries Library sync management (list, enable, disable)")
    print("  ingest-status Show ingest status for libraries")
    print("\nUse <command> --help for command-specific help")


def cmd_libraries(args):
    """List Plex libraries."""
    if 'help' in args:
        print("List Plex libraries")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --server-name TEXT  Server name (from stored credentials)")
        print("  --server-id INTEGER Server ID (from stored credentials)")
        print("  --verbose, -v       Enable verbose output")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_name = args.get('server-name')
    server_id = args.get('server-id')
    
    try:
        # Lazy import to avoid pulling requests for non-network commands
        from retrovue.plex.client import PlexClient
        from retrovue.plex.config import resolve_server
        import requests
        
        # Resolve server credentials from database
        with Db(db_path) as db:
            server = resolve_server(db, server_name, int(server_id) if server_id else None)
        
        client = PlexClient(server['base_url'], server['token'])
        libraries = client.get_libraries()
        
        print(f"[OK] Found {len(libraries)} libraries:")
        for lib in libraries:
            print(f"  {lib.key}: {lib.title} ({lib.type})")
            
    except ValueError as e:
        # Server not found or no default set
        print(f"[ERROR] {e}")
        sys.exit(2)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in [401, 403]:
            print(f"[ERROR] Authentication failed (HTTP {e.response.status_code}): Invalid token")
        else:
            print(f"[ERROR] HTTP error {e.response.status_code}: {e}")
        sys.exit(3)
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(3)
    except Exception as e:
        print(f"[ERROR] Failed to fetch libraries: {e}")
        sys.exit(1)


def cmd_preview_items(args):
    """Preview raw items returned by Plex for a library."""
    if 'help' in args:
        print("Preview raw items returned by Plex for a library")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --server-name TEXT  Server name (from stored credentials)")
        print("  --server-id INTEGER Server ID (from stored credentials)")
        print("  --library-key TEXT  Library key")
        print("  --kind TEXT         Content kind (movie, episode)")
        print("  --limit INTEGER     Number of items to preview")
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
            
    except ValueError as e:
        # Server not found or no default set
        print(f"[ERROR] {e}")
        sys.exit(2)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in [401, 403]:
            print(f"[ERROR] Authentication failed (HTTP {e.response.status_code}): Invalid token")
        elif e.response.status_code == 404:
            print(f"[ERROR] Library {library_key} not found")
        else:
            print(f"[ERROR] HTTP error {e.response.status_code}: {e}")
        sys.exit(3)
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(3)
    except Exception as e:
        print(f"[ERROR] Failed to fetch items: {e}")
        sys.exit(1)


def cmd_resolve_path(args):
    """Resolve a Plex path to local path via DB path_mappings."""
    if 'help' in args:
        print("Resolve a Plex path to local path via DB path_mappings")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --server-id INTEGER Server ID")
        print("  --library-id INTEGER Library ID")
        print("  --plex-path TEXT    Plex path to resolve")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_id = int(args.get('server-id', 1))
    library_id = int(args.get('library-id', 1))
    plex_path = args.get('plex-path', '/data/TV/Show/ep1.mkv')
    
    try:
        with Db(db_path) as db:
            path_mapper = PathMapper(db.conn)
            local_path = path_mapper.resolve(server_id, library_id, plex_path)
            
            if local_path:
                print(f"[OK] Resolved path: {plex_path} -> {local_path}")
            else:
                print(f"No mapping found for: {plex_path}")
                sys.exit(2)
                
    except Exception as e:
        print(f"[ERROR] Failed to resolve path: {e}")
        sys.exit(1)


def cmd_map_item(args):
    """Map one Plex item JSON to our model."""
    if 'help' in args:
        print("Map one Plex item JSON to our model")
        print("\nOptions:")
        print("  --from-json TEXT   JSON file path")
        print("  --from-stdin       Read from stdin")
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


def cmd_ingest(args):
    """Ingest: discover + map + upsert (writes to database)."""
    if 'help' in args:
        print("Ingest: discover + map + upsert (writes to database)")
        print("\nOptions:")
        print("  --db TEXT           Database path")
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
            
    except ValueError as e:
        # Server not found or no default set
        print(f"[ERROR] {e}")
        sys.exit(2)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in [401, 403]:
            print(f"[ERROR] Authentication failed (HTTP {e.response.status_code}): Invalid token")
        else:
            print(f"[ERROR] HTTP error {e.response.status_code}: {e}")
        sys.exit(3)
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(3)
    except Exception as e:
        print(f"[ERROR] Ingest failed: {e}")
        sys.exit(1)


def cmd_test_guid(args):
    """Test GUID parsing."""
    if 'help' in args:
        print("Test GUID parsing")
        print("\nOptions:")
        print("  --guid TEXT   GUID string to parse")
        return
    
    guid = args.get('guid', '')
    parser = GuidParser()
    result = parser.parse(guid)
    
    print(f"[OK] Parsed GUID: {guid}")
    for key, value in result.items():
        if value:
            print(f"  {key}: {value}")


def cmd_test_pathmap(args):
    """Test path mapping functionality."""
    if 'help' in args:
        print("Test path mapping functionality")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --server-id INTEGER Server ID")
        print("  --library-id INTEGER Library ID")
        print("  --plex-path TEXT    Plex path to test")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_id = int(args.get('server-id', 1))
    library_id = int(args.get('library-id', 1))
    plex_path = args.get('plex-path', '/data/TV/Show/ep1.mkv')
    
    try:
        with Db(db_path) as db:
            path_mapper = PathMapper(db.conn)
            local_path = path_mapper.resolve(server_id, library_id, plex_path)
            
            print(f"[OK] Path mapping test:")
            print(f"  Plex: {plex_path}")
            print(f"  Local: {local_path}")
            
    except Exception as e:
        print(f"[ERROR] Path mapping test failed: {e}")
        sys.exit(1)


def cmd_list_mappings(args):
    """List path mappings for a server and library."""
    if 'help' in args:
        print("List path mappings for a server and library")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --server-id INTEGER Server ID")
        print("  --library-id INTEGER Library ID")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_id = int(args.get('server-id', 1))
    library_id = int(args.get('library-id', 1))
    
    try:
        with Db(db_path) as db:
            path_mapper = PathMapper(db.conn)
            mappings = path_mapper.list_mappings(server_id, library_id)
            
            if mappings:
                print(f"[OK] Found {len(mappings)} path mappings for server {server_id}, library {library_id}:")
                for plex_prefix, local_prefix in mappings:
                    print(f"  {plex_prefix} -> {local_prefix}")
            else:
                print(f"[OK] No path mappings found for server {server_id}, library {library_id}")
                
    except Exception as e:
        print(f"[ERROR] Failed to list mappings: {e}")
        sys.exit(1)


def cmd_add_mapping(args):
    """Add a new path mapping."""
    if 'help' in args:
        print("Add a new path mapping")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --server-id INTEGER Server ID")
        print("  --library-id INTEGER Library ID")
        print("  --plex-prefix TEXT  Plex path prefix")
        print("  --local-prefix TEXT Local path prefix")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_id = int(args.get('server-id', 1))
    library_id = int(args.get('library-id', 1))
    plex_prefix = args.get('plex-prefix')
    local_prefix = args.get('local-prefix')
    
    if not plex_prefix or not local_prefix:
        print("[ERROR] --plex-prefix and --local-prefix are required")
        sys.exit(1)
    
    try:
        with Db(db_path) as db:
            mapping_id = db.insert_path_mapping(server_id, library_id, plex_prefix, local_prefix)
            print(f"[OK] Added path mapping with ID {mapping_id}:")
            print(f"  {plex_prefix} -> {local_prefix}")
                
    except Exception as e:
        print(f"[ERROR] Failed to add mapping: {e}")
        sys.exit(1)


# Servers command group
def cmd_servers_add(args):
    """Add a Plex server."""
    if 'help' in args:
        print("Add a Plex server")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --name TEXT         Server name")
        print("  --base-url TEXT     Server base URL")
        print("  --token TEXT        Server authentication token")
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
            print(f"[OK] Added server with ID {server_id}: {name} ({base_url})")
            print("Stored Plex token in SQLite (plaintext). Consider restricting file access to this repo.")
                
    except Exception as e:
        print(f"[ERROR] Failed to add server: {e}")
        sys.exit(1)


def cmd_servers_list(args):
    """List Plex servers."""
    if 'help' in args:
        print("List Plex servers")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        return
    
    db_path = args.get('db', './retrovue.db')
    
    try:
        with Db(db_path) as db:
            servers = db.list_plex_servers()
            
            if servers:
                print(f"[OK] Found {len(servers)} Plex servers:")
                print(f"{'ID':<4} {'Name':<15} {'Base URL':<25} {'Default':<8}")
                print("-" * 60)
                for server in servers:
                    default_status = "✅" if server.get('is_default') else "❌"
                    print(f"{server['id']:<4} {server['name'][:14]:<15} {server['base_url'][:24]:<25} {default_status:<8}")
            else:
                print("[OK] No Plex servers found")
                
    except Exception as e:
        print(f"[ERROR] Failed to list servers: {e}")
        sys.exit(1)


def cmd_servers_delete(args):
    """Delete a Plex server."""
    if 'help' in args:
        print("Delete a Plex server")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --id INTEGER        Server ID to delete")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_id = args.get('id')
    
    if not server_id:
        print("[ERROR] --id is required")
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
        print("[ERROR] --id must be an integer")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to delete server: {e}")
        sys.exit(1)


def cmd_servers_update_token(args):
    """Update a Plex server's token."""
    if 'help' in args:
        print("Update a Plex server's token")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --id INTEGER        Server ID")
        print("  --token TEXT        New authentication token")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_id = args.get('id')
    token = args.get('token')
    
    if not server_id or not token:
        print("[ERROR] --id and --token are required")
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
        print("[ERROR] --id must be an integer")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Failed to update token: {e}")
        sys.exit(1)


def cmd_servers_set_default(args):
    """Set the default Plex server."""
    if 'help' in args:
        print("Set the default Plex server")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --server-name TEXT  Server name to set as default")
        print("  --server-id INTEGER Server ID to set as default")
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


def cmd_sync_libraries_list(args):
    """List libraries with sync status."""
    if 'help' in args:
        print("List libraries with sync status")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --server-name TEXT  Server name (from stored credentials)")
        print("  --server-id INTEGER Server ID (from stored credentials)")
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
            
            print(f"Libraries (showing {len(libraries)}):")
            print(f"{'ID':<4} {'Key':<6} {'Title':<20} {'Type':<8} {'Sync':<5} {'Last Full':<12} {'Last Incr':<12}")
            print("-" * 80)
            
            for lib in libraries:
                sync_status = "ON" if lib['sync_enabled'] else "OFF"
                last_full = lib['last_full_sync_epoch'] or "Never"
                last_incr = lib['last_incremental_sync_epoch'] or "Never"
                
                print(f"{lib['id']:<4} {lib['plex_library_key']:<6} {lib['title'][:19]:<20} {lib['library_type']:<8} {sync_status:<5} {str(last_full):<12} {str(last_incr):<12}")
                
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(2)
    except Exception as e:
        print(f"[ERROR] Failed to list libraries: {e}")
        sys.exit(1)


def cmd_sync_libraries_enable(args):
    """Enable sync for a library."""
    if 'help' in args:
        print("Enable sync for a library")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --library-id INTEGER Library ID to enable")
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


def cmd_sync_libraries_disable(args):
    """Disable sync for a library."""
    if 'help' in args:
        print("Disable sync for a library")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --library-id INTEGER Library ID to disable")
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


def cmd_ingest_status(args):
    """Show ingest status for libraries."""
    if 'help' in args:
        print("Show ingest status for libraries")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --server-name TEXT  Server name (from stored credentials)")
        print("  --server-id INTEGER Server ID (from stored credentials)")
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


def cmd_libraries_list(args):
    """List libraries with sync status."""
    if 'help' in args:
        print("List libraries with sync status")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --server-name TEXT  Server name (from stored credentials)")
        print("  --server-id INTEGER Server ID (from stored credentials)")
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


def cmd_libraries_tag(args):
    """Enable or disable sync for a single library."""
    if 'help' in args:
        print("Enable or disable sync for a single library")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --library-id INTEGER Library ID to modify")
        print("  --sync-enabled {0|1} Enable (1) or disable (0) sync")
        return
    
    db_path = args.get('db', './retrovue.db')
    library_id = args.get('library-id')
    sync_enabled = args.get('sync-enabled')
    
    if not library_id:
        print("[ERROR] --library-id is required")
        sys.exit(1)
    
    if sync_enabled is None:
        print("[ERROR] --sync-enabled is required (0 or 1)")
        sys.exit(1)
    
    try:
        sync_enabled_bool = bool(int(sync_enabled))
    except ValueError:
        print("[ERROR] --sync-enabled must be 0 or 1")
        sys.exit(1)
    
    try:
        with Db(db_path) as db:
            rows_updated = db.set_library_sync_enabled(int(library_id), sync_enabled_bool)
            
            if rows_updated > 0:
                status = "enabled" if sync_enabled_bool else "disabled"
                print(f"[OK] {status.capitalize()} sync for library ID {library_id}")
            else:
                print(f"[ERROR] Library ID {library_id} not found")
                sys.exit(2)
                
    except Exception as e:
        print(f"[ERROR] Failed to update library sync: {e}")
        sys.exit(1)


def cmd_libraries_tag_all(args):
    """Enable or disable sync for all libraries."""
    if 'help' in args:
        print("Enable or disable sync for all libraries")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --server-name TEXT  Server name (from stored credentials)")
        print("  --server-id INTEGER Server ID (from stored credentials)")
        print("  --sync-enabled {0|1} Enable (1) or disable (0) sync")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_name = args.get('server-name')
    server_id = args.get('server-id')
    sync_enabled = args.get('sync-enabled')
    
    if sync_enabled is None:
        print("[ERROR] --sync-enabled is required (0 or 1)")
        sys.exit(1)
    
    try:
        sync_enabled_bool = bool(int(sync_enabled))
    except ValueError:
        print("[ERROR] --sync-enabled must be 0 or 1")
        sys.exit(1)
    
    try:
        with Db(db_path) as db:
            # Resolve server if specified
            server_id_filter = None
            if server_name or server_id:
                from retrovue.plex.config import resolve_server
                server = resolve_server(db, server_name, int(server_id) if server_id else None)
                server_id_filter = server['id']
            
            rows_updated = db.set_all_libraries_sync_enabled(sync_enabled_bool, server_id_filter)
            
            status = "enabled" if sync_enabled_bool else "disabled"
            scope = f" for server {server_name or server_id}" if server_name or server_id else ""
            print(f"[OK] {status.capitalize()} sync for {rows_updated} libraries{scope}")
                
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(2)
    except Exception as e:
        print(f"[ERROR] Failed to update library sync: {e}")
        sys.exit(1)


def cmd_libraries_delete(args):
    """Delete a single library by internal DB ID."""
    if 'help' in args:
        print("Delete a single library by internal DB ID")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --library-id INTEGER Library ID to delete")
        return
    
    db_path = args.get('db', './retrovue.db')
    library_id = args.get('library-id')
    
    if not library_id:
        print("[ERROR] --library-id is required")
        sys.exit(1)
    
    try:
        with Db(db_path) as db:
            rows_affected = db.delete_library(int(library_id))
            
            if rows_affected > 0:
                print(f"Deleted {rows_affected} library (id={library_id})")
            else:
                print(f"No such library id: {library_id}")
                
    except Exception as e:
        print(f"[ERROR] Failed to delete library: {e}")
        sys.exit(1)


def cmd_libraries_delete_all(args):
    """Delete all libraries for a given server."""
    if 'help' in args:
        print("Delete all libraries for a given server")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --server-name TEXT  Server name (from stored credentials)")
        print("  --server-id INTEGER Server ID (from stored credentials)")
        print("  --yes               Confirm deletion (required)")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_name = args.get('server-name')
    server_id = args.get('server-id')
    confirm = args.get('yes', False)
    
    if not confirm:
        print("[ERROR] --yes is required to confirm deletion")
        sys.exit(2)
    
    try:
        with Db(db_path) as db:
            # Resolve server
            from retrovue.plex.config import resolve_server
            server = resolve_server(db, server_name, int(server_id) if server_id else None)
            
            rows_affected = db.delete_all_libraries_for_server(server['id'])
            print(f"Deleted {rows_affected} libraries for server '{server['name']}' (id={server['id']})")
                
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(2)
    except Exception as e:
        print(f"[ERROR] Failed to delete libraries: {e}")
        sys.exit(1)


def cmd_libraries_sync_from_plex(args):
    """Fetch all libraries from Plex and upsert them into the database."""
    if 'help' in args:
        print("Fetch all libraries from Plex and upsert them into the database")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --server-name TEXT  Server name (from stored credentials)")
        print("  --server-id INTEGER Server ID (from stored credentials)")
        print("  --enable-all        Enable sync for all imported libraries")
        print("  --disable-all       Disable sync for all imported libraries")
        return
    
    db_path = args.get('db', './retrovue.db')
    server_name = args.get('server-name')
    server_id = args.get('server-id')
    enable_all = args.get('enable-all', False)
    disable_all = args.get('disable-all', False)
    
    if enable_all and disable_all:
        print("[ERROR] Cannot specify both --enable-all and --disable-all")
        sys.exit(1)
    
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
                
                library_id = db.upsert_library(
                    server['id'], 
                    int(plex_lib.key), 
                    plex_lib.title, 
                    plex_lib.type
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
            print(f"inserted={inserted} updated={updated} unchanged={unchanged} total={total}")
            
            if enable_all:
                print(f"Enabled sync for {len(returned_keys)} libraries")
            elif disable_all:
                print(f"Disabled sync for {len(returned_keys)} libraries")
                
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(2)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in [401, 403]:
            print(f"[ERROR] Authentication failed (HTTP {e.response.status_code}): Invalid token")
        else:
            print(f"[ERROR] HTTP error {e.response.status_code}: {e}")
        sys.exit(3)
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(3)
    except Exception as e:
        print(f"[ERROR] Failed to sync libraries from Plex: {e}")
        sys.exit(1)


def cmd_libraries_tag_none(args):
    """Disable sync for all libraries."""
    if 'help' in args:
        print("Disable sync for all libraries")
        print("\nOptions:")
        print("  --db TEXT           Database path")
        print("  --server-name TEXT  Server name (from stored credentials)")
        print("  --server-id INTEGER Server ID (from stored credentials)")
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
            
            rows_updated = db.set_all_libraries_sync(False, server_id_filter)
            
            scope = f" for server {server_name or server_id}" if server_name or server_id else ""
            print(f"[OK] Disabled sync for {rows_updated} libraries{scope}")
                
    except ValueError as e:
        print(f"[ERROR] {e}")
        sys.exit(2)
    except Exception as e:
        print(f"[ERROR] Failed to disable library sync: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    command, args = parse_args()
    
    if not command or command == '--help':
        cmd_help()
        return
    
    commands = {
        'libraries': cmd_libraries,
        'preview-items': cmd_preview_items,
        'resolve-path': cmd_resolve_path,
        'map-item': cmd_map_item,
        'ingest': cmd_ingest,
        'test-guid': cmd_test_guid,
        'test-pathmap': cmd_test_pathmap,
        'list-mappings': cmd_list_mappings,
        'add-mapping': cmd_add_mapping,
        'servers_add': cmd_servers_add,
        'servers_list': cmd_servers_list,
        'servers_delete': cmd_servers_delete,
        'servers_update-token': cmd_servers_update_token,
        'servers_set-default': cmd_servers_set_default,
        'libraries_list': cmd_libraries_list,
        'libraries_tag': cmd_libraries_tag,
        'libraries_tag-all': cmd_libraries_tag_all,
        'libraries_tag-none': cmd_libraries_tag_none,
        'libraries_delete': cmd_libraries_delete,
        'libraries_delete-all': cmd_libraries_delete_all,
        'libraries_sync-from-plex': cmd_libraries_sync_from_plex,
        'sync_libraries_list': cmd_sync_libraries_list,
        'sync_libraries_enable': cmd_sync_libraries_enable,
        'sync_libraries_disable': cmd_sync_libraries_disable,
        'ingest-status': cmd_ingest_status,
    }
    
    if command in commands:
        commands[command](args)
    else:
        print(f"Unknown command: {command}")
        cmd_help()
        sys.exit(1)


if __name__ == "__main__":
    main()