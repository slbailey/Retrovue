"""
Command Line Interface for Retrovue

This module provides CLI commands for content management and synchronization,
with special support for disambiguating series with the same title but different years.

Key Features:
- Discover shows by title and year
- Sync specific shows with disambiguation
- Full library synchronization
- Progress tracking and status reporting

Usage Examples:
    python -m retrovue discover --title "Battlestar Galactica" --year 1978
    python -m retrovue sync --title "Battlestar Galactica" --year 2003
    python -m retrovue sync-all --page-size 200
"""

import argparse
import sys
import os
from typing import Optional

# Handle both relative and absolute imports
try:
    from .database import RetrovueDatabase
    from .plex_integration import create_plex_importer
    from .guid_parser import format_show_for_display
except ImportError:
    # If running as standalone script, add parent directory to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database import RetrovueDatabase
    from plex_integration import create_plex_importer
    from guid_parser import format_show_for_display


def setup_argparse() -> argparse.ArgumentParser:
    """Set up command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Retrovue - Retro IPTV Simulation Project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover shows by title
  python -m retrovue discover --title "Battlestar Galactica"
  
  # Discover specific year
  python -m retrovue discover --title "Battlestar Galactica" --year 1978
  
  # Sync specific show
  python -m retrovue sync --title "Battlestar Galactica" --year 2003
  
  # Sync all libraries
  python -m retrovue sync-all --page-size 200
        """
    )
    
    # Global options
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--db-path', default='retrovue.db', help='Path to SQLite database file')
    
    # Plex connection options
    parser.add_argument('--plex-url', help='Plex server URL (or set PLEX_BASE_URL env var)')
    parser.add_argument('--plex-token', help='Plex authentication token (or set PLEX_TOKEN env var)')
    parser.add_argument('--plex-section', type=int, help='Plex TV section key (or set PLEX_TV_SECTION_KEY env var)')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Discover shows by title and year')
    discover_parser.add_argument('--title', required=True, help='Show title to search for')
    discover_parser.add_argument('--year', type=int, help='Year for disambiguation (e.g., 1978 or 2003)')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync a specific show by title and year')
    sync_parser.add_argument('--title', required=True, help='Show title to sync')
    sync_parser.add_argument('--year', type=int, help='Year for disambiguation (e.g., 1978 or 2003)')
    
    # Sync-all command
    sync_all_parser = subparsers.add_parser('sync-all', help='Sync all libraries')
    sync_all_parser.add_argument('--page-size', type=int, default=200, help='Page size for Plex API requests')
    sync_all_parser.add_argument('--since-plex-updated', help='Only sync shows updated since this ISO8601 timestamp')
    
    return parser


def get_plex_credentials(args) -> tuple[Optional[str], Optional[str]]:
    """Get Plex credentials from args or environment variables"""
    server_url = args.plex_url or os.getenv('PLEX_BASE_URL')
    token = args.plex_token or os.getenv('PLEX_TOKEN')
    
    if not server_url:
        print("❌ Error: Plex server URL required. Use --plex-url or set PLEX_BASE_URL environment variable.")
        return None, None
    
    if not token:
        print("❌ Error: Plex token required. Use --plex-token or set PLEX_TOKEN environment variable.")
        return None, None
    
    return server_url, token


def status_callback(message: str):
    """Status callback for progress updates"""
    print(message)


def cmd_discover(args):
    """Discover shows by title and year"""
    server_url, token = get_plex_credentials(args)
    if not server_url or not token:
        return 1
    
    # Initialize database
    db = RetrovueDatabase(args.db_path)
    
    # Create Plex importer
    importer = create_plex_importer(server_url, token, db, status_callback)
    if not importer:
        print("❌ Failed to connect to Plex server")
        return 1
    
    # Discover shows
    print(f"🔍 Discovering shows matching '{args.title}'" + (f" ({args.year})" if args.year else ""))
    shows = importer.discover_shows_by_title(args.title, args.year)
    
    if not shows:
        print("❌ No shows found")
        return 1
    
    print(f"\n📺 Found {len(shows)} show(s):")
    for i, show in enumerate(shows, 1):
        print(f"  {i}. {show['display_name']}")
        print(f"     Rating Key: {show['ratingKey']}")
        print(f"     Year: {show['year']}")
        if show['guids']:
            print(f"     GUIDs: {', '.join([f'{p.upper()}:{eid}' for p, eid in show['guids']])}")
        print()
    
    return 0


def cmd_sync(args):
    """Sync a specific show by title and year"""
    server_url, token = get_plex_credentials(args)
    if not server_url or not token:
        return 1
    
    # Initialize database
    db = RetrovueDatabase(args.db_path)
    
    # Create Plex importer
    importer = create_plex_importer(server_url, token, db, status_callback)
    if not importer:
        print("❌ Failed to connect to Plex server")
        return 1
    
    # Sync show
    print(f"🔄 Syncing show '{args.title}'" + (f" ({args.year})" if args.year else ""))
    if args.dry_run:
        print("🔍 DRY RUN - No changes will be made")
        shows = importer.discover_shows_by_title(args.title, args.year)
        if shows:
            print(f"Would sync {len(shows)} show(s):")
            for show in shows:
                print(f"  📺 {show['display_name']}")
        return 0
    
    results = importer.sync_show_by_title_and_year(args.title, args.year)
    
    print(f"\n🎉 Sync completed!")
    print(f"  Added: {results['added']}")
    print(f"  Updated: {results['updated']}")
    print(f"  Removed: {results['removed']}")
    
    return 0


def cmd_sync_all(args):
    """Sync all libraries"""
    server_url, token = get_plex_credentials(args)
    if not server_url or not token:
        return 1
    
    # Initialize database
    db = RetrovueDatabase(args.db_path)
    
    # Create Plex importer
    importer = create_plex_importer(server_url, token, db, status_callback)
    if not importer:
        print("❌ Failed to connect to Plex server")
        return 1
    
    # Sync all libraries
    print("🔄 Syncing all libraries...")
    if args.dry_run:
        print("🔍 DRY RUN - No changes will be made")
        libraries = importer.get_libraries()
        print(f"Would sync {len(libraries)} libraries:")
        for lib in libraries:
            print(f"  📚 {lib['title']} ({lib['type']})")
        return 0
    
    def progress_callback(library_progress=None, item_progress=None, message=None):
        if library_progress:
            lib_idx, lib_total, lib_name = library_progress
            print(f"📚 Library {lib_idx + 1}/{lib_total}: {lib_name}")
        
        if item_progress:
            item_idx, item_total, item_name = item_progress
            print(f"  📺 Item {item_idx + 1}/{item_total}: {item_name}")
        
        if message:
            print(f"  {message}")
    
    results = importer.sync_all_libraries(progress_callback)
    
    print(f"\n🎉 Full sync completed!")
    print(f"  Added: {results['added']}")
    print(f"  Updated: {results['updated']}")
    print(f"  Removed: {results['removed']}")
    
    return 0


def main():
    """Main CLI entry point"""
    parser = setup_argparse()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Set up logging if debug mode
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    # Execute command
    if args.command == 'discover':
        return cmd_discover(args)
    elif args.command == 'sync':
        return cmd_sync(args)
    elif args.command == 'sync-all':
        return cmd_sync_all(args)
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
