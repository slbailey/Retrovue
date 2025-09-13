#!/usr/bin/env python3
"""
Simple smoke test script for the Plex Sync CLI.

This script exercises the core functionality without requiring network access.
It focuses on testing the command structure, argument parsing, and basic operations.

Usage:
    python scripts/smoke_test_simple.py

Exit codes:
    0 - All tests passed
    1 - One or more tests failed
"""

import os
import sys
import tempfile
import json
import subprocess
import time
from pathlib import Path
from typing import Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Test fixtures for live connectivity
def plex_env_present() -> bool:
    """Check if Plex environment variables are present."""
    return bool(os.getenv("PLEX_BASE_URL") and os.getenv("PLEX_TOKEN"))

def run_cli(args, env=None, timeout=120, input_data=None) -> Tuple[int, str, str]:
    """Run CLI command with timeout and return code, stdout, stderr."""
    cmd = [sys.executable, "cli/plex_sync.py"] + args
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                          text=True, env=env, cwd=Path(__file__).parent.parent, stdin=subprocess.PIPE)
    try:
        out, err = proc.communicate(input=input_data, timeout=timeout)
        return proc.returncode, out, err
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        return 124, out, err  # 124 is timeout exit code

def run_cli_with_retry(args, env=None, timeout=120, max_retries=1, input_data=None) -> Tuple[int, str, str]:
    """Run CLI command with retry logic for transient network issues."""
    for attempt in range(max_retries + 1):
        code, out, err = run_cli(args, env, timeout, input_data)
        
        # If successful or not a network issue, return immediately
        if code == 0 or attempt == max_retries:
            return code, out, err
            
        # Check if it's a transient network issue
        if any(phrase in err.lower() for phrase in ['connection reset', 'timeout', 'network']):
            print(f"   ⚠️  Network issue detected, retrying... (attempt {attempt + 1}/{max_retries + 1})")
            time.sleep(1)
            continue
            
        # Not a network issue, return immediately
        return code, out, err
    
    return code, out, err

# Test configuration
CLI_PATH = Path(__file__).parent.parent / "cli" / "plex_sync.py"

# Use environment variables if available, otherwise fall back to test values
TEST_SERVER_NAME = os.getenv("PLEX_SERVER_NAME", "SmokeTestServer")
TEST_SERVER_URL = os.getenv("PLEX_BASE_URL", "http://127.0.0.1:32400")
TEST_SERVER_TOKEN = os.getenv("PLEX_TOKEN", "smoke-test-token-12345")
TEST_GUID = "com.plexapp.agents.imdb://tt1234567"

# Check if we're in live mode
LIVE_MODE = plex_env_present()


def run_command(args, expect_success=True, input_data=None):
    """Run a CLI command and return success status, stdout, and stderr."""
    # Use the new CLI runner with retry logic for network commands
    if any(arg in args for arg in ['libraries', 'sync', 'ingest', 'run', 'items', 'preview']):
        # Network commands get retry logic
        code, out, err = run_cli_with_retry(args, input_data=input_data)
    else:
        # Non-network commands use regular timeout
        code, out, err = run_cli(args, timeout=60, input_data=input_data)
    
    # success should be True if the result matches our expectation
    if expect_success:
        success = (code == 0)
    else:
        success = (code != 0)
    return success, out, err


def test_help_commands():
    """Test help commands."""
    print("📖 Testing help commands...")
    
    tests = [
        ("main help", ["--help"], True),
        ("servers help", ["servers", "--help"], True),
        ("libraries help", ["libraries", "--help"], True),
        ("mappings help", ["mappings", "--help"], True),
        ("ingest help", ["ingest", "--help"], True),
        ("items help", ["items", "--help"], True),
        ("guid help", ["guid", "--help"], True),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, args, expect_success in tests:
        success, stdout, stderr = run_command(args, expect_success)
        # Check for help indicators using helper function
        if success and has_help(stdout):
            print(f"   ✅ {test_name}")
            passed += 1
        else:
            print(f"   ❌ {test_name} failed: {stderr.strip()}")
            failed += 1
    
    return passed, failed


def init_database(db_path):
    """Initialize database with schema."""
    # Use stable schema file
    schema_path = Path(__file__).parent.parent / "sql" / "schema.sql"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    # Read and execute schema using sqlite3 Python module
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Execute schema using sqlite3 with foreign keys enabled
    import sqlite3
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "cli"))
    from db_utils import connect
    
    conn = connect(str(db_path))
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()


def has_help(stdout: str) -> bool:
    """Check if output contains help indicators."""
    indicators = ("Usage:", "Options:", "Subcommands:", "Command Groups:", "Examples:", "Description:")
    return any(tok in stdout for tok in indicators)


def get_server_id_from_output(stdout):
    """Extract server ID from command output using JSON or regex patterns."""
    import re
    import json
    
    # Try JSON parsing first
    try:
        data = json.loads(stdout)
        if 'id' in data:
            return str(data['id'])
        elif 'servers' in data and data['servers']:
            return str(data['servers'][0]['id'])
    except (json.JSONDecodeError, KeyError, IndexError):
        pass
    
    # Fallback to regex patterns
    # Pattern 1: "Added server ID 1" or "Added server 1"
    match = re.search(r'Added server\s+(?:ID\s+)?(\d+)', stdout, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Pattern 2: Table format "ID   1   Name"
    match = re.search(r'ID\s+(\d+)\s+\w+', stdout)
    if match:
        return match.group(1)
    
    # Pattern 3: "Set server ID 1 as default"
    match = re.search(r'Set server ID (\d+) as default', stdout, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Pattern 4: Any standalone number that looks like an ID
    match = re.search(r'\b(\d+)\b', stdout)
    if match:
        return match.group(1)
    
    return None


def test_servers_commands():
    """Test server management commands."""
    print("\n🖥️  Testing server commands...")
    
    # Create temporary database
    temp_dir = tempfile.mkdtemp()
    temp_db = Path(temp_dir) / "test.db"
    
    try:
        # Initialize database with schema
        init_database(temp_db)
        passed = 0
        failed = 0
        
        # Test servers list (empty)
        success, stdout, stderr = run_command(["servers", "list", "--db", str(temp_db)], True)
        if success:
            print(f"   ✅ servers list")
            passed += 1
        else:
            print(f"   ❌ servers list failed: {stderr.strip()}")
            failed += 1
        
        # Test servers add and capture server ID using JSON format
        success, stdout, stderr = run_command(["--format", "json", "servers", "add", "--db", str(temp_db), "--name", TEST_SERVER_NAME, 
                                             "--base-url", TEST_SERVER_URL, "--token", TEST_SERVER_TOKEN], True)
        if success:
            print(f"   ✅ servers add")
            passed += 1
            server_id = get_server_id_from_output(stdout)
            if not server_id:
                # Fallback to parsing servers list with JSON
                success2, stdout2, stderr2 = run_command(["--format", "json", "servers", "list", "--db", str(temp_db)], True)
                if success2:
                    server_id = get_server_id_from_output(stdout2)
        else:
            print(f"   ❌ servers add failed: {stderr.strip()}")
            failed += 1
            server_id = "1"  # Fallback for remaining tests
        
        # Test servers list with data - use JSON format
        success, stdout, stderr = run_command(["--format", "json", "servers", "list", "--db", str(temp_db)], True)
        if success:
            # Parse JSON to verify server exists
            try:
                data = json.loads(stdout)
                if 'servers' in data and len(data['servers']) > 0:
                    print(f"   ✅ servers list with data")
                    passed += 1
                else:
                    print(f"   ❌ servers list with data failed: No servers found in JSON")
                    failed += 1
            except json.JSONDecodeError:
                print(f"   ❌ servers list with data failed: Invalid JSON")
                failed += 1
        else:
            print(f"   ❌ servers list with data failed: {stderr.strip()}")
            failed += 1
        
        # Test servers update-token with dynamic ID
        success, stdout, stderr = run_command(["servers", "update-token", "--db", str(temp_db), 
                                             "--server-id", server_id, "--token", "new-token"], True)
        if success:
            print(f"   ✅ servers update-token")
            passed += 1
        else:
            print(f"   ❌ servers update-token failed: {stderr.strip()}")
            failed += 1
        
        # Test servers set-default with dynamic ID
        success, stdout, stderr = run_command(["servers", "set-default", "--db", str(temp_db), 
                                             "--server-id", server_id], True)
        if success:
            print(f"   ✅ servers set-default")
            passed += 1
        else:
            print(f"   ❌ servers set-default failed: {stderr.strip()}")
            failed += 1
        
        # Test servers delete with dynamic ID
        success, stdout, stderr = run_command(["servers", "delete", "--db", str(temp_db), "--server-id", server_id], True)
        if success:
            print(f"   ✅ servers delete")
            passed += 1
        else:
            print(f"   ❌ servers delete failed: {stderr.strip()}")
            failed += 1
        
        return passed, failed
        
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)


def test_libraries_commands():
    """Test library management commands."""
    print("\n📚 Testing library commands...")
    
    # Create temporary database with a server
    temp_dir = tempfile.mkdtemp()
    temp_db = Path(temp_dir) / "test.db"
    
    try:
        # Initialize database with schema
        init_database(temp_db)
        
        # Add a server first and capture ID
        success, stdout, stderr = run_command(["servers", "add", "--db", str(temp_db), "--name", TEST_SERVER_NAME,
                                             "--base-url", TEST_SERVER_URL, "--token", TEST_SERVER_TOKEN])
        server_id = get_server_id_from_output(stdout) or "1"
        
        # Set as default server
        run_command(["servers", "set-default", "--db", str(temp_db), "--server-id", server_id])
        
        passed = 0
        failed = 0
        
        # Test libraries list - use JSON format
        success, stdout, stderr = run_command(["--format", "json", "libraries", "list", "--db", str(temp_db)], True)
        if success:
            # Parse JSON to verify empty libraries list
            try:
                data = json.loads(stdout)
                if 'libraries' in data and len(data['libraries']) == 0:
                    print(f"   ✅ libraries list")
                    passed += 1
                else:
                    print(f"   ❌ libraries list failed: Expected empty libraries list")
                    failed += 1
            except json.JSONDecodeError:
                print(f"   ❌ libraries list failed: Invalid JSON")
                failed += 1
        else:
            print(f"   ❌ libraries list failed: {stderr.strip()}")
            failed += 1
        
        # Test libraries sync list - use JSON format
        success, stdout, stderr = run_command(["--format", "json", "libraries", "sync", "list", "--db", str(temp_db)], True)
        if success:
            # Parse JSON to verify empty libraries list
            try:
                data = json.loads(stdout)
                if 'libraries' in data and len(data['libraries']) == 0:
                    print(f"   ✅ libraries sync list")
                    passed += 1
                else:
                    print(f"   ❌ libraries sync list failed: Expected empty libraries list")
                    failed += 1
            except json.JSONDecodeError:
                print(f"   ❌ libraries sync list failed: Invalid JSON")
                failed += 1
        else:
            print(f"   ❌ libraries sync list failed: {stderr.strip()}")
            failed += 1
        
        # Test libraries sync enable (should fail with no libraries) - check exit code only
        success, stdout, stderr = run_command(["libraries", "sync", "enable", "--db", str(temp_db), 
                                              "--library-id", "1"], False)
        if success:  # Command failed as expected
            print(f"   ✅ libraries sync enable (no library)")
            passed += 1
        else:
            print(f"   ❌ libraries sync enable failed: {stderr.strip()}")
            failed += 1
        
        # Test libraries sync disable (should fail with no libraries) - check exit code only
        success, stdout, stderr = run_command(["libraries", "sync", "disable", "--db", str(temp_db), 
                                               "--library-id", "1"], False)
        if success:  # Command failed as expected
            print(f"   ✅ libraries sync disable (no library)")
            passed += 1
        else:
            print(f"   ❌ libraries sync disable failed: {stderr.strip()}")
            failed += 1
        
        # Test libraries delete (should fail with no libraries) - check exit code only
        success, stdout, stderr = run_command(["libraries", "delete", "--db", str(temp_db), 
                                             "--library-id", "1"], False)
        if success:  # Command failed as expected
            print(f"   ✅ libraries delete (no library)")
            passed += 1
        else:
            print(f"   ❌ libraries delete failed: {stderr.strip()}")
            failed += 1
        
        # Test libraries delete --all --yes - use JSON format
        success, stdout, stderr = run_command(["--format", "json", "libraries", "delete", "--db", str(temp_db), 
                                            "--all", "--yes"], True)
        if success:
            # Parse JSON to verify empty libraries list
            try:
                data = json.loads(stdout)
                if 'libraries' in data and len(data['libraries']) == 0:
                    print(f"   ✅ libraries delete --all --yes")
                    passed += 1
                else:
                    print(f"   ❌ libraries delete --all --yes failed: Expected empty libraries list")
                    failed += 1
            except json.JSONDecodeError:
                print(f"   ❌ libraries delete --all --yes failed: Invalid JSON")
                failed += 1
        else:
            print(f"   ❌ libraries delete --all --yes failed: {stderr.strip()}")
            failed += 1
        
        return passed, failed
        
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)


def test_mappings_commands():
    """Test path mapping commands."""
    print("\n🗺️  Testing mapping commands...")
    
    # Create temporary database with a server
    temp_dir = tempfile.mkdtemp()
    temp_db = Path(temp_dir) / "test.db"
    
    try:
        # Initialize database with schema
        init_database(temp_db)
        
        # Add a server first and capture ID
        success, stdout, stderr = run_command(["servers", "add", "--db", str(temp_db), "--name", TEST_SERVER_NAME,
                                             "--base-url", TEST_SERVER_URL, "--token", TEST_SERVER_TOKEN])
        server_id = get_server_id_from_output(stdout) or "1"
        
        # Insert a library row for FK checks
        import sqlite3
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "cli"))
        from db_utils import connect
        
        conn = connect(str(temp_db))
        cur = conn.cursor()
        cur.execute("INSERT INTO libraries (server_id, plex_library_key, title, library_type, sync_enabled) VALUES (?,?,?,?,1)", 
                   (server_id, "1", "Test Library", "movie"))
        lib_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        tests = [
            ("mappings list", ["mappings", "list", "--db", str(temp_db), "--server-id", server_id, 
                             "--library-id", str(lib_id)], True),
            ("mappings add", ["mappings", "add", "--db", str(temp_db), "--server-id", server_id, 
                            "--library-id", str(lib_id), "--plex-prefix", "/data/Movies", 
                            "--local-prefix", "C:/Media/Movies"], True),
            ("mappings list with data", ["mappings", "list", "--db", str(temp_db), "--server-id", server_id, 
                                       "--library-id", str(lib_id)], True),
            ("mappings resolve", ["mappings", "resolve", "--db", str(temp_db), "--server-id", server_id, 
                                "--library-id", str(lib_id), "--plex-path", "/data/Movies/Test.mkv"], True),
            ("mappings test", ["mappings", "test", "--db", str(temp_db), "--server-id", server_id, 
                             "--library-id", str(lib_id), "--plex-path", "/data/Movies/Test.mkv"], True),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, args, expect_success in tests:
            success, stdout, stderr = run_command(args, expect_success)
            if success:
                print(f"   ✅ {test_name}")
                passed += 1
            else:
                print(f"   ❌ {test_name} failed: {stderr.strip()}")
                failed += 1
        
        return passed, failed
        
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)


def test_ingest_commands():
    """Test ingest commands."""
    print("\n📥 Testing ingest commands...")
    
    # Create temporary database
    temp_dir = tempfile.mkdtemp()
    temp_db = Path(temp_dir) / "test.db"
    
    try:
        # Initialize database with schema
        init_database(temp_db)
        tests = [
            ("ingest status", ["ingest", "status", "--db", str(temp_db)], True),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, args, expect_success in tests:
            success, stdout, stderr = run_command(args, expect_success)
            if success:
                print(f"   ✅ {test_name}")
                passed += 1
            else:
                print(f"   ❌ {test_name} failed: {stderr.strip()}")
                failed += 1
        
        return passed, failed
        
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)


def test_items_commands():
    """Test item operations commands."""
    print("\n📦 Testing items commands...")
    
    # Create temporary directory for test files
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create test JSON file
        test_json = {
            "title": "Test Movie",
            "type": "movie",
            "duration": 7200000,
            "contentRating": "PG-13",
            "ratingKey": "12345"
        }
        test_json_file = Path(temp_dir) / "test_movie.json"
        with open(test_json_file, 'w') as f:
            json.dump(test_json, f)
        
        tests = [
            ("items map --from-json", ["items", "map", "--from-json", str(test_json_file)], True),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, args, expect_success in tests:
            success, stdout, stderr = run_command(args, expect_success)
            if success and "Test Movie" in stdout:
                print(f"   ✅ {test_name}")
                passed += 1
            else:
                print(f"   ❌ {test_name} failed: {stderr.strip()}")
                failed += 1
        
        # Test items map --from-stdin
        test_json_str = json.dumps(test_json)
        if not test_json_str.endswith("\n"):
            test_json_str += "\n"
        success, stdout, stderr = run_command(["items", "map", "--from-stdin"], 
                                            input_data=test_json_str)
        if success and "Test Movie" in stdout:
            print(f"   ✅ items map --from-stdin")
            passed += 1
        else:
            print(f"   ❌ items map --from-stdin failed: {stderr.strip()}")
            failed += 1
        
        return passed, failed
        
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)


def test_guid_commands():
    """Test GUID commands."""
    print("\n🔍 Testing GUID commands...")
    
    tests = [
        ("guid test", ["guid", "test", "--guid", TEST_GUID], True),
        ("guid test (tvdb)", ["guid", "test", "--guid", "com.plexapp.agents.thetvdb://123456"], True),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, args, expect_success in tests:
        success, stdout, stderr = run_command(args, expect_success)
        if success and "Parsed GUID:" in stdout:
            print(f"   ✅ {test_name}")
            passed += 1
        else:
            print(f"   ❌ {test_name} failed: {stderr.strip()}")
            failed += 1
    
    return passed, failed


def test_network_commands():
    """Test network commands that are expected to fail without network access."""
    print("\n🌐 Testing network commands (expected to fail)...")
    
    # Create temporary database with a server
    temp_dir = tempfile.mkdtemp()
    temp_db = Path(temp_dir) / "test.db"
    
    try:
        # Initialize database with schema
        init_database(temp_db)
        
        # Add a server first and capture ID
        success, stdout, stderr = run_command(["servers", "add", "--db", str(temp_db), "--name", TEST_SERVER_NAME,
                                             "--base-url", TEST_SERVER_URL, "--token", TEST_SERVER_TOKEN])
        server_id = get_server_id_from_output(stdout) or "1"
        
        # Set as default server
        run_command(["servers", "set-default", "--db", str(temp_db), "--server-id", server_id])
        
        if LIVE_MODE:
            # In live mode, these commands should succeed
            tests = [
                ("libraries sync (live mode)", ["libraries", "sync", "--db", str(temp_db)], True),
                ("ingest run --dry-run (live mode)", ["ingest", "run", "--db", str(temp_db), 
                                                   "--mode", "full", "--dry-run"], True),
                ("items preview (live mode)", ["items", "preview", "--db", str(temp_db), 
                                            "--library-key", "1", "--kind", "movie", "--limit", "1"], True),
            ]
        else:
            # In offline mode, these commands should fail
            tests = [
                ("libraries sync (offline mode)", ["--offline", "libraries", "sync", "--db", str(temp_db)], False),
                ("ingest run --dry-run (offline mode)", ["--offline", "ingest", "run", "--db", str(temp_db), 
                                                       "--mode", "full", "--dry-run"], False),
                ("items preview (offline mode)", ["--offline", "items", "preview", "--db", str(temp_db), 
                                                "--library-key", "1", "--kind", "movie", "--limit", "1"], False),
            ]
        
        passed = 0
        failed = 0
        
        for test_name, args, expect_success in tests:
            success, stdout, stderr = run_command(args, expect_success)
            # For network commands, we expect them to fail (non-zero exit code)
            if success:  # Command failed as expected (success=True means it matched our expectation)
                print(f"   ✅ {test_name}")
                passed += 1
            else:
                print(f"   ❌ {test_name} (unexpected result)")
                failed += 1
        
        return passed, failed
        
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)


def test_error_handling():
    """Test error handling for invalid commands."""
    print("\n⚠️  Testing error handling...")
    
    tests = [
        ("unknown command error", ["unknown-command"], False),
        ("missing required parameters", ["servers", "add"], False),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, args, expect_success in tests:
        success, stdout, stderr = run_command(args, expect_success)
        # For error tests, we expect them to fail (non-zero exit code)
        if success:  # Command failed as expected (success=True means it matched our expectation)
            print(f"   ✅ {test_name}")
            passed += 1
        else:
            print(f"   ❌ {test_name} (unexpected result)")
            failed += 1
    
    return passed, failed


def main():
    """Main entry point."""
    print("🚀 Starting Plex Sync CLI Simple Smoke Tests")
    print("=" * 50)
    
    if LIVE_MODE:
        print("🌐 Running in LIVE MODE with Plex server")
        print(f"   Server: {TEST_SERVER_URL}")
        print(f"   Name: {TEST_SERVER_NAME}")
    else:
        print("🔌 Running in OFFLINE MODE (no network operations)")
        print("   Set PLEX_BASE_URL and PLEX_TOKEN to enable live mode")
    print()
    
    total_passed = 0
    total_failed = 0
    
    # Run all test suites
    passed, failed = test_help_commands()
    total_passed += passed
    total_failed += failed
    
    passed, failed = test_servers_commands()
    total_passed += passed
    total_failed += failed
    
    passed, failed = test_libraries_commands()
    total_passed += passed
    total_failed += failed
    
    passed, failed = test_mappings_commands()
    total_passed += passed
    total_failed += failed
    
    passed, failed = test_ingest_commands()
    total_passed += passed
    total_failed += failed
    
    passed, failed = test_items_commands()
    total_passed += passed
    total_failed += failed
    
    passed, failed = test_guid_commands()
    total_passed += passed
    total_failed += failed
    
    passed, failed = test_network_commands()
    total_passed += passed
    total_failed += failed
    
    passed, failed = test_error_handling()
    total_passed += passed
    total_failed += failed
    
    # Print results
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    
    if total_failed == 0:
        print("\n🎉 All smoke tests passed!")
        sys.exit(0)
    else:
        print(f"\n💥 {total_failed} smoke test(s) failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
