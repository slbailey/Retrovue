#!/usr/bin/env python3
"""
Idempotent ingest integration test.

Tests that running ingest twice produces the same results without duplicates.
Requires PLEX_BASE_URL and PLEX_TOKEN environment variables to be set.
"""

import os
import sys
import tempfile
import subprocess
import time
import json
from pathlib import Path
from typing import Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import required modules
from retrovue.importers.plex.db import Db
from retrovue.importers.plex.config import OFFLINE_EXIT


def plex_env_present() -> bool:
    """Check if Plex environment variables are present."""
    return bool(os.getenv("PLEX_BASE_URL") and os.getenv("PLEX_TOKEN"))


def run_cli(args, env=None, timeout=120) -> Tuple[int, str, str]:
    """Run CLI command with timeout and return code, stdout, stderr."""
    cmd = [sys.executable, "cli/plex_sync.py"] + args
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                          text=True, env=env, cwd=Path(__file__).parent.parent.parent)
    try:
        out, err = proc.communicate(timeout=timeout)
        return proc.returncode, out, err
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        return 124, out, err  # 124 is timeout exit code


def init_database_with_schema(db_path: str) -> None:
    """Initialize database with v1.2.3 schema."""
    schema_path = Path(__file__).parent.parent.parent / "sql" / "retrovue_schema_v1.2.3.sql"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    # Read and execute schema using sqlite3 Python module
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Execute schema using sqlite3 with foreign keys enabled
    import sqlite3
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cli"))
    from db_utils import connect
    
    conn = connect(str(db_path))
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


def test_ingest_idempotent():
    """Test that ingest is idempotent - running twice produces same results."""
    if not plex_env_present():
        print("SKIP: PLEX_BASE_URL and PLEX_TOKEN not set, skipping integration test")
        return True
    
    print("🧪 Testing idempotent ingest integration...")
    
    # Create temporary database
    temp_dir = tempfile.mkdtemp()
    temp_db = Path(temp_dir) / "test.db"
    
    try:
        # Initialize database with v1.2.3 schema
        init_database_with_schema(temp_db)
        print(f"   ✅ Initialized database with v1.2.3 schema: {temp_db}")
        
        # Set up environment
        env = os.environ.copy()
        env['PLEX_BASE_URL'] = os.getenv('PLEX_BASE_URL')
        env['PLEX_TOKEN'] = os.getenv('PLEX_TOKEN')
        
        # Add server via CLI (JSON mode)
        print("   📡 Adding Plex server...")
        code, out, err = run_cli([
            "--format", "json", "servers", "add", 
            "--db", str(temp_db),
            "--name", "TestServer",
            "--base-url", env['PLEX_BASE_URL'],
            "--token", env['PLEX_TOKEN']
        ], env=env, timeout=60)
        
        if code != 0:
            print(f"   ❌ Failed to add server: {err}")
            return False
        
        # Parse server ID from JSON output
        try:
            server_data = json.loads(out)
            server_id = server_data['id']
        except (json.JSONDecodeError, KeyError):
            print(f"   ❌ Failed to parse server ID from: {out}")
            return False
        
        print(f"   ✅ Added server with ID: {server_id}")
        
        # Set as default server
        print("   🔧 Setting default server...")
        code, out, err = run_cli([
            "servers", "set-default",
            "--db", str(temp_db),
            "--server-id", str(server_id)
        ], env=env, timeout=60)
        
        if code != 0:
            print(f"   ❌ Failed to set default server: {err}")
            return False
        
        print("   ✅ Set default server")
        
        # Sync libraries
        print("   📚 Syncing libraries...")
        code, out, err = run_cli([
            "libraries", "sync",
            "--db", str(temp_db)
        ], env=env, timeout=120)
        
        if code != 0:
            print(f"   ❌ Failed to sync libraries: {err}")
            return False
        
        print("   ✅ Synced libraries")
        
        # Get library list to pick one for testing
        print("   📋 Getting library list...")
        code, out, err = run_cli([
            "--format", "json", "libraries", "list",
            "--db", str(temp_db)
        ], env=env, timeout=60)
        
        if code != 0:
            print(f"   ❌ Failed to list libraries: {err}")
            return False
        
        try:
            libraries_data = json.loads(out)
            libraries = libraries_data.get('libraries', [])
        except json.JSONDecodeError:
            print(f"   ❌ Failed to parse libraries JSON: {out}")
            return False
        
        if not libraries:
            print("   ❌ No libraries found")
            return False
        
        # Pick the first library
        library_id = libraries[0]['id']
        library_key = libraries[0]['plex_library_key']
        print(f"   ✅ Selected library ID {library_id} (key: {library_key})")
        
        # Run ingest first time
        print("   🔄 Running ingest (first time)...")
        code, out, err = run_cli([
            "ingest", "run",
            "--db", str(temp_db),
            "--libraries", str(library_id),
            "--kinds", "movie,episode",
            "--limit", "50",
            "--commit"
        ], env=env, timeout=120)
        
        if code != 0:
            print(f"   ❌ First ingest failed: {err}")
            return False
        
        print("   ✅ First ingest completed")
        
        # Get counts after first run
        with Db(str(temp_db)) as db:
            cursor = db.execute("SELECT COUNT(*) as count FROM media_files")
            first_media_count = cursor.fetchone()['count']
            
            cursor = db.execute("SELECT COUNT(*) as count FROM content_item_files")
            first_link_count = cursor.fetchone()['count']
        
        print(f"   📊 After first run: {first_media_count} media files, {first_link_count} links")
        
        # Run ingest second time
        print("   🔄 Running ingest (second time)...")
        code, out, err = run_cli([
            "ingest", "run",
            "--db", str(temp_db),
            "--libraries", str(library_id),
            "--kinds", "movie,episode",
            "--limit", "50",
            "--commit"
        ], env=env, timeout=120)
        
        if code != 0:
            print(f"   ❌ Second ingest failed: {err}")
            return False
        
        print("   ✅ Second ingest completed")
        
        # Get counts after second run
        with Db(str(temp_db)) as db:
            cursor = db.execute("SELECT COUNT(*) as count FROM media_files")
            second_media_count = cursor.fetchone()['count']
            
            cursor = db.execute("SELECT COUNT(*) as count FROM content_item_files")
            second_link_count = cursor.fetchone()['count']
        
        print(f"   📊 After second run: {second_media_count} media files, {second_link_count} links")
        
        # Check for duplicates by unique key
        print("   🔍 Checking for duplicates...")
        with Db(str(temp_db)) as db:
            cursor = db.execute("""
                SELECT server_id, file_path, COUNT(*)
                FROM media_files
                GROUP BY 1,2 HAVING COUNT(*)>1
            """)
            duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"   ❌ Found {len(duplicates)} duplicate media files by unique key")
            for dup in duplicates:
                print(f"      Server {dup[0]}, Path: {dup[1]}, Count: {dup[2]}")
            return False
        
        print("   ✅ No duplicates found by unique key")
        
        # Verify counts are the same
        if first_media_count != second_media_count:
            print(f"   ❌ Media file count changed: {first_media_count} -> {second_media_count}")
            return False
        
        if first_link_count != second_link_count:
            print(f"   ❌ Link count changed: {first_link_count} -> {second_link_count}")
            return False
        
        print("   ✅ Counts are identical (idempotent)")
        
        # Test items preview
        print("   👀 Testing items preview...")
        code, out, err = run_cli([
            "items", "preview",
            "--db", str(temp_db),
            "--library-key", str(library_key),
            "--limit", "5"
        ], env=env, timeout=60)
        
        if code != 0:
            print(f"   ❌ Items preview failed: {err}")
            return False
        
        print("   ✅ Items preview successful")
        
        print("   🎉 All idempotent ingest tests passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed with exception: {e}")
        return False
        
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)


def main():
    """Main entry point."""
    print("🚀 Starting Idempotent Ingest Integration Test")
    print("=" * 50)
    
    if not plex_env_present():
        print("🔌 Skipping test - PLEX_BASE_URL and PLEX_TOKEN not set")
        print("   Set these environment variables to run the integration test")
        sys.exit(0)
    
    success = test_ingest_idempotent()
    
    if success:
        print("\n🎉 Integration test passed!")
        sys.exit(0)
    else:
        print("\n💥 Integration test failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
