#!/usr/bin/env python3
"""
Comprehensive smoke test script for the Plex Sync CLI.

This script exercises all the new command tree structure to ensure
the CLI is working correctly. It uses a temporary database and
mocks network operations where possible.

Usage:
    python scripts/smoke_test.py

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
import unittest
from pathlib import Path
from typing import Tuple
from typing import List, Tuple, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Test fixtures for live connectivity
def plex_env_present() -> bool:
    """Check if Plex environment variables are present."""
    return bool(os.getenv("PLEX_BASE_URL") and os.getenv("PLEX_TOKEN"))

def run_cli(args, env=None, timeout=120) -> Tuple[int, str, str]:
    """Run CLI command with timeout and return code, stdout, stderr."""
    cmd = [sys.executable, "cli/plex_sync.py"] + args
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                          text=True, env=env, cwd=Path(__file__).parent.parent)
    try:
        out, err = proc.communicate(timeout=timeout)
        return proc.returncode, out, err
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
        return 124, out, err  # 124 is timeout exit code

def run_cli_with_retry(args, env=None, timeout=120, max_retries=1) -> Tuple[int, str, str]:
    """Run CLI command with retry logic for transient network issues."""
    for attempt in range(max_retries + 1):
        code, out, err = run_cli(args, env, timeout)
        
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
# Use environment variables if available, otherwise fall back to test values
TEST_SERVER_NAME = os.getenv("PLEX_SERVER_NAME", "SmokeTestServer")
TEST_SERVER_URL = os.getenv("PLEX_BASE_URL", "http://127.0.0.1:32400")
TEST_SERVER_TOKEN = os.getenv("PLEX_TOKEN", "smoke-test-token-12345")
TEST_LIBRARY_KEY = "1"
TEST_GUID = "com.plexapp.agents.imdb://tt1234567"

# Check if we're in live mode
LIVE_MODE = plex_env_present()


class SmokeTestRunner:
    """Runs comprehensive smoke tests for the CLI."""
    
    def __init__(self):
        """Initialize the test runner."""
        self.temp_dir = None
        self.temp_db = None
        self.cli_path = Path(__file__).parent.parent / "cli" / "plex_sync.py"
        self.failed_tests = []
        self.passed_tests = []
        
    def setup(self):
        """Set up test environment."""
        print("🔧 Setting up test environment...")
        self.temp_dir = tempfile.mkdtemp(prefix="retrovue_smoke_")
        self.temp_db = Path(self.temp_dir) / "test.db"
        print(f"   Temporary directory: {self.temp_dir}")
        print(f"   Test database: {self.temp_db}")
        
        # Initialize database with schema
        self.init_database(self.temp_db)
    
    def init_database(self, db_path):
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
    
    def has_help(self, stdout: str) -> bool:
        """Check if output contains help indicators."""
        indicators = ("Usage:", "Options:", "Subcommands:", "Command Groups:", "Examples:", "Description:")
        return any(tok in stdout for tok in indicators)
    
    def get_server_id_from_output(self, stdout):
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
        
    def teardown(self):
        """Clean up test environment."""
        if self.temp_dir and Path(self.temp_dir).exists():
            import shutil
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Cleaned up temporary directory: {self.temp_dir}")
    
    def run_command(self, args: List[str], expect_success: bool = True, 
                   input_data: Optional[str] = None) -> Tuple[bool, str, str]:
        """
        Run a CLI command and return success status, stdout, and stderr.
        
        Args:
            args: Command arguments (without the script path)
            expect_success: Whether the command should succeed
            input_data: Optional input data for stdin
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        cmd = [sys.executable, str(self.cli_path)] + args
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                input=input_data,
                timeout=30,
                cwd=Path(__file__).parent.parent
            )
            
            success = (result.returncode == 0) == expect_success
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out after 30 seconds"
        except Exception as e:
            return False, "", f"Command failed with exception: {e}"
    
    def test_help_commands(self):
        """Test help commands."""
        print("\n📖 Testing help commands...")
        
        # Test main help
        success, stdout, stderr = self.run_command(["--help"])
        if success and self.has_help(stdout):
            self.passed_tests.append("main help")
            print("   ✅ Main help")
        else:
            self.failed_tests.append("main help")
            print(f"   ❌ Main help failed: {stderr}")
        
        # Test command group help
        for group in ["servers", "libraries", "mappings", "ingest", "items", "guid"]:
            success, stdout, stderr = self.run_command([group, "--help"])
            if success and self.has_help(stdout):
                self.passed_tests.append(f"{group} help")
                print(f"   ✅ {group} help")
            else:
                self.failed_tests.append(f"{group} help")
                print(f"   ❌ {group} help failed: {stderr}")
    
    def test_servers_commands(self):
        """Test server management commands."""
        print("\n🖥️  Testing server commands...")
        
        # Test servers list (should work even with empty database)
        success, stdout, stderr = self.run_command([
            "servers", "list", "--db", str(self.temp_db)
        ])
        if success:
            self.passed_tests.append("servers list")
            print("   ✅ servers list")
        else:
            self.failed_tests.append("servers list")
            print(f"   ❌ servers list failed: {stderr}")
        
        # Test servers add and capture server ID using JSON format
        success, stdout, stderr = self.run_command([
            "--format", "json", "servers", "add",
            "--db", str(self.temp_db),
            "--name", TEST_SERVER_NAME,
            "--base-url", TEST_SERVER_URL,
            "--token", TEST_SERVER_TOKEN
        ])
        if success:
            self.passed_tests.append("servers add")
            print("   ✅ servers add")
            server_id = self.get_server_id_from_output(stdout)
            if not server_id:
                # Fallback: get from servers list with JSON
                success2, stdout2, stderr2 = self.run_command(["--format", "json", "servers", "list", "--db", str(self.temp_db)])
                if success2:
                    server_id = self.get_server_id_from_output(stdout2)
        else:
            self.failed_tests.append("servers add")
            print(f"   ❌ servers add failed: {stderr}")
            server_id = "1"  # Fallback for remaining tests
        
        # Test servers list again (should now show the added server) - use JSON format
        success, stdout, stderr = self.run_command([
            "--format", "json", "servers", "list", "--db", str(self.temp_db)
        ])
        if success:
            # Parse JSON to verify server exists
            try:
                data = json.loads(stdout)
                if 'servers' in data and len(data['servers']) > 0:
                    self.passed_tests.append("servers list with data")
                    print("   ✅ servers list with data")
                else:
                    self.failed_tests.append("servers list with data")
                    print(f"   ❌ servers list with data failed: No servers found in JSON")
            except json.JSONDecodeError:
                self.failed_tests.append("servers list with data")
                print(f"   ❌ servers list with data failed: Invalid JSON")
        else:
            self.failed_tests.append("servers list with data")
            print(f"   ❌ servers list with data failed: {stderr}")
        
        # Test servers update-token with dynamic ID
        new_token = "updated-token-67890"
        success, stdout, stderr = self.run_command([
            "servers", "update-token",
            "--db", str(self.temp_db),
            "--server-id", server_id,
            "--token", new_token
        ])
        if success:
            self.passed_tests.append("servers update-token")
            print("   ✅ servers update-token")
        else:
            self.failed_tests.append("servers update-token")
            print(f"   ❌ servers update-token failed: {stderr}")
        
        # Test servers set-default with dynamic ID
        success, stdout, stderr = self.run_command([
            "servers", "set-default",
            "--db", str(self.temp_db),
            "--server-id", server_id
        ])
        if success:
            self.passed_tests.append("servers set-default")
            print("   ✅ servers set-default")
        else:
            self.failed_tests.append("servers set-default")
            print(f"   ❌ servers set-default failed: {stderr}")
        
        # Test servers delete with dynamic ID
        success, stdout, stderr = self.run_command([
            "servers", "delete",
            "--db", str(self.temp_db),
            "--server-id", server_id
        ])
        if success:
            self.passed_tests.append("servers delete")
            print("   ✅ servers delete")
        else:
            self.failed_tests.append("servers delete")
            print(f"   ❌ servers delete failed: {stderr}")
    
    def test_libraries_commands(self):
        """Test library management commands."""
        print("\n📚 Testing library commands...")
        
        # First add a server back for library tests
        self.run_command([
            "servers", "add",
            "--db", str(self.temp_db),
            "--name", TEST_SERVER_NAME,
            "--base-url", TEST_SERVER_URL,
            "--token", TEST_SERVER_TOKEN
        ])
        
        # Test libraries list (should work even with empty database) - use JSON format
        success, stdout, stderr = self.run_command([
            "--format", "json", "libraries", "list", "--db", str(self.temp_db)
        ])
        if success:
            # Parse JSON to verify empty libraries list
            try:
                data = json.loads(stdout)
                if 'libraries' in data and len(data['libraries']) == 0:
                    self.passed_tests.append("libraries list")
                    print("   ✅ libraries list")
                else:
                    self.failed_tests.append("libraries list")
                    print(f"   ❌ libraries list failed: Expected empty libraries list")
            except json.JSONDecodeError:
                self.failed_tests.append("libraries list")
                print(f"   ❌ libraries list failed: Invalid JSON")
        else:
            self.failed_tests.append("libraries list")
            print(f"   ❌ libraries list failed: {stderr}")
        
        # Test libraries sync (live or offline mode)
        if LIVE_MODE:
            success, stdout, stderr = self.run_command([
                "libraries", "sync", "--db", str(self.temp_db)
            ], expect_success=True)
            if success:
                self.passed_tests.append("libraries sync (live mode)")
                print("   ✅ libraries sync (live mode)")
            else:
                self.failed_tests.append("libraries sync (live mode)")
                print(f"   ❌ libraries sync (live mode) failed: {stderr}")
        else:
            success, stdout, stderr = self.run_command([
                "--offline", "libraries", "sync", "--db", str(self.temp_db)
            ], expect_success=False)
            if success:  # Should fail (success=True means it matched our expectation of failure)
                self.passed_tests.append("libraries sync (offline mode)")
                print("   ✅ libraries sync (offline mode)")
            else:
                self.failed_tests.append("libraries sync (offline mode)")
                print(f"   ❌ libraries sync (offline mode) failed: {stderr}")
        
        # Test libraries sync list - use JSON format
        success, stdout, stderr = self.run_command([
            "--format", "json", "libraries", "sync", "list", "--db", str(self.temp_db)
        ])
        if success:
            # Parse JSON to verify empty libraries list
            try:
                data = json.loads(stdout)
                if 'libraries' in data and len(data['libraries']) == 0:
                    self.passed_tests.append("libraries sync list")
                    print("   ✅ libraries sync list")
                else:
                    self.failed_tests.append("libraries sync list")
                    print(f"   ❌ libraries sync list failed: Expected empty libraries list")
            except json.JSONDecodeError:
                self.failed_tests.append("libraries sync list")
                print(f"   ❌ libraries sync list failed: Invalid JSON")
        else:
            self.failed_tests.append("libraries sync list")
            print(f"   ❌ libraries sync list failed: {stderr}")
        
        # Test libraries sync enable (should fail with no libraries) - check exit code only
        success, stdout, stderr = self.run_command([
            "libraries", "sync", "enable",
            "--db", str(self.temp_db),
            "--library-id", "1"
        ], expect_success=False)
        if success:  # Command failed as expected
            self.passed_tests.append("libraries sync enable (no library)")
            print("   ✅ libraries sync enable (no library)")
        else:
            self.failed_tests.append("libraries sync enable")
            print(f"   ❌ libraries sync enable failed: {stderr}")
        
        # Test libraries sync disable (should fail with no libraries) - check exit code only
        success, stdout, stderr = self.run_command([
            "libraries", "sync", "disable",
            "--db", str(self.temp_db),
            "--library-id", "1"
        ], expect_success=False)
        if success:  # Command failed as expected
            self.passed_tests.append("libraries sync disable (no library)")
            print("   ✅ libraries sync disable (no library)")
        else:
            self.failed_tests.append("libraries sync disable")
            print(f"   ❌ libraries sync disable failed: {stderr}")
        
        # Test libraries delete (should fail with no libraries) - check exit code only
        success, stdout, stderr = self.run_command([
            "libraries", "delete",
            "--db", str(self.temp_db),
            "--library-id", "1"
        ], expect_success=False)
        if success:  # Command failed as expected
            self.passed_tests.append("libraries delete (no library)")
            print("   ✅ libraries delete (no library)")
        else:
            self.failed_tests.append("libraries delete")
            print(f"   ❌ libraries delete failed: {stderr}")
        
        # Test libraries delete --all --yes (should work with no libraries) - use JSON format
        success, stdout, stderr = self.run_command([
            "--format", "json", "libraries", "delete",
            "--db", str(self.temp_db),
            "--all", "--yes"
        ])
        if success:
            # Parse JSON to verify empty libraries list
            try:
                data = json.loads(stdout)
                if 'libraries' in data and len(data['libraries']) == 0:
                    self.passed_tests.append("libraries delete --all --yes")
                    print("   ✅ libraries delete --all --yes")
                else:
                    self.failed_tests.append("libraries delete --all --yes")
                    print(f"   ❌ libraries delete --all --yes failed: Expected empty libraries list")
            except json.JSONDecodeError:
                self.failed_tests.append("libraries delete --all --yes")
                print(f"   ❌ libraries delete --all --yes failed: Invalid JSON")
        else:
            self.failed_tests.append("libraries delete --all --yes")
            print(f"   ❌ libraries delete --all --yes failed: {stderr}")
    
    def test_mappings_commands(self):
        """Test path mapping commands."""
        print("\n🗺️  Testing mapping commands...")
        
        # Insert a library row for FK checks
        import sqlite3
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "cli"))
        from db_utils import connect
        
        conn = connect(str(self.temp_db))
        cur = conn.cursor()
        cur.execute("INSERT INTO libraries (server_id, plex_library_key, title, library_type, sync_enabled) VALUES (?,?,?,?,1)", 
                   (1, "1", "Test Library", "movie"))
        lib_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        # Test mappings list (should work even with empty database)
        success, stdout, stderr = self.run_command([
            "mappings", "list",
            "--db", str(self.temp_db),
            "--server-id", "1",
            "--library-id", str(lib_id)
        ])
        if success and "Found 0 path mappings" in stdout:
            self.passed_tests.append("mappings list")
            print("   ✅ mappings list")
        else:
            self.failed_tests.append("mappings list")
            print(f"   ❌ mappings list failed: {stderr}")
        
        # Test mappings add
        success, stdout, stderr = self.run_command([
            "mappings", "add",
            "--db", str(self.temp_db),
            "--server-id", "1",
            "--library-id", str(lib_id),
            "--plex-prefix", "/data/Movies",
            "--local-prefix", "C:/Media/Movies"
        ])
        if success and "Added path mapping" in stdout:
            self.passed_tests.append("mappings add")
            print("   ✅ mappings add")
        else:
            self.failed_tests.append("mappings add")
            print(f"   ❌ mappings add failed: {stderr}")
        
        # Test mappings list again (should now show the added mapping)
        success, stdout, stderr = self.run_command([
            "mappings", "list",
            "--db", str(self.temp_db),
            "--server-id", "1",
            "--library-id", str(lib_id)
        ])
        if success and "/data/Movies" in stdout and "C:/Media/Movies" in stdout:
            self.passed_tests.append("mappings list with data")
            print("   ✅ mappings list with data")
        else:
            self.failed_tests.append("mappings list with data")
            print(f"   ❌ mappings list with data failed: {stderr}")
        
        # Test mappings resolve
        success, stdout, stderr = self.run_command([
            "mappings", "resolve",
            "--db", str(self.temp_db),
            "--server-id", "1",
            "--library-id", str(lib_id),
            "--plex-path", "/data/Movies/Test.mkv"
        ])
        if success and "C:/Media/Movies/Test.mkv" in stdout:
            self.passed_tests.append("mappings resolve")
            print("   ✅ mappings resolve")
        else:
            self.failed_tests.append("mappings resolve")
            print(f"   ❌ mappings resolve failed: {stderr}")
        
        # Test mappings test
        success, stdout, stderr = self.run_command([
            "mappings", "test",
            "--db", str(self.temp_db),
            "--server-id", "1",
            "--library-id", str(lib_id),
            "--plex-path", "/data/Movies/Test.mkv"
        ])
        if success and "Path mapping test:" in stdout:
            self.passed_tests.append("mappings test")
            print("   ✅ mappings test")
        else:
            self.failed_tests.append("mappings test")
            print(f"   ❌ mappings test failed: {stderr}")
    
    def test_ingest_commands(self):
        """Test ingest commands."""
        print("\n📥 Testing ingest commands...")
        
        # Test ingest status
        success, stdout, stderr = self.run_command([
            "ingest", "status", "--db", str(self.temp_db)
        ])
        if success and "No libraries found" in stdout:
            self.passed_tests.append("ingest status")
            print("   ✅ ingest status")
        else:
            self.failed_tests.append("ingest status")
            print(f"   ❌ ingest status failed: {stderr}")
        
        # Test ingest run --dry-run (live or offline mode)
        if LIVE_MODE:
            success, stdout, stderr = self.run_command([
                "ingest", "run",
                "--db", str(self.temp_db),
                "--mode", "full",
                "--dry-run"
            ], expect_success=True)
            if success:
                self.passed_tests.append("ingest run --dry-run (live mode)")
                print("   ✅ ingest run --dry-run (live mode)")
            else:
                self.failed_tests.append("ingest run --dry-run (live mode)")
                print(f"   ❌ ingest run --dry-run (live mode) failed: {stderr}")
        else:
            success, stdout, stderr = self.run_command([
                "--offline", "ingest", "run",
                "--db", str(self.temp_db),
                "--mode", "full",
                "--dry-run"
            ], expect_success=False)
            if success:  # Should fail (success=True means it matched our expectation of failure)
                self.passed_tests.append("ingest run --dry-run (offline mode)")
                print("   ✅ ingest run --dry-run (offline mode)")
            else:
                self.failed_tests.append("ingest run --dry-run (offline mode)")
                print(f"   ❌ ingest run --dry-run (offline mode) failed: {stderr}")
    
    def test_items_commands(self):
        """Test item operations commands."""
        print("\n📦 Testing items commands...")
        
        # Test items preview (live or offline mode)
        if LIVE_MODE:
            success, stdout, stderr = self.run_command([
                "items", "preview",
                "--db", str(self.temp_db),
                "--library-key", TEST_LIBRARY_KEY,
                "--kind", "movie",
                "--limit", "1"
            ], expect_success=True)
            if success:
                self.passed_tests.append("items preview (live mode)")
                print("   ✅ items preview (live mode)")
            else:
                self.failed_tests.append("items preview (live mode)")
                print(f"   ❌ items preview (live mode) failed: {stderr}")
        else:
            success, stdout, stderr = self.run_command([
                "--offline", "items", "preview",
                "--db", str(self.temp_db),
                "--library-key", TEST_LIBRARY_KEY,
                "--kind", "movie",
                "--limit", "1"
            ], expect_success=False)
            if success:  # Should fail (success=True means it matched our expectation of failure)
                self.passed_tests.append("items preview (offline mode)")
                print("   ✅ items preview (offline mode)")
            else:
                self.failed_tests.append("items preview (offline mode)")
                print(f"   ❌ items preview (offline mode) failed: {stderr}")
        
        # Test items map --from-json
        test_json = {
            "title": "Test Movie",
            "type": "movie",
            "duration": 7200000,
            "contentRating": "PG-13",
            "ratingKey": "12345"
        }
        test_json_file = Path(self.temp_dir) / "test_movie.json"
        with open(test_json_file, 'w') as f:
            json.dump(test_json, f)
        
        success, stdout, stderr = self.run_command([
            "items", "map",
            "--from-json", str(test_json_file)
        ])
        if success and "Test Movie" in stdout and "movie" in stdout:
            self.passed_tests.append("items map --from-json")
            print("   ✅ items map --from-json")
        else:
            self.failed_tests.append("items map --from-json")
            print(f"   ❌ items map --from-json failed: {stderr}")
        
        # Test items map --from-stdin
        test_json_str = json.dumps(test_json)
        if not test_json_str.endswith("\n"):
            test_json_str += "\n"
        success, stdout, stderr = self.run_command([
            "items", "map", "--from-stdin"
        ], input_data=test_json_str)
        if success and "Test Movie" in stdout and "movie" in stdout:
            self.passed_tests.append("items map --from-stdin")
            print("   ✅ items map --from-stdin")
        else:
            self.failed_tests.append("items map --from-stdin")
            print(f"   ❌ items map --from-stdin failed: {stderr}")
    
    def test_guid_commands(self):
        """Test GUID commands."""
        print("\n🔍 Testing GUID commands...")
        
        # Test guid test
        success, stdout, stderr = self.run_command([
            "guid", "test",
            "--guid", TEST_GUID
        ])
        if success and "Parsed GUID:" in stdout and "imdb:" in stdout:
            self.passed_tests.append("guid test")
            print("   ✅ guid test")
        else:
            self.failed_tests.append("guid test")
            print(f"   ❌ guid test failed: {stderr}")
        
        # Test guid test with different GUID format
        tvdb_guid = "com.plexapp.agents.thetvdb://123456"
        success, stdout, stderr = self.run_command([
            "guid", "test",
            "--guid", tvdb_guid
        ])
        if success and "Parsed GUID:" in stdout and "tvdb:" in stdout:
            self.passed_tests.append("guid test (tvdb)")
            print("   ✅ guid test (tvdb)")
        else:
            self.failed_tests.append("guid test (tvdb)")
            print(f"   ❌ guid test (tvdb) failed: {stderr}")
    
    def test_error_handling(self):
        """Test error handling for invalid commands."""
        print("\n⚠️  Testing error handling...")
        
        # Test unknown command
        success, stdout, stderr = self.run_command([
            "unknown-command"
        ], expect_success=False)
        if success:  # Should fail (success=True means it matched our expectation of failure)
            self.passed_tests.append("unknown command error")
            print("   ✅ unknown command error")
        else:
            self.failed_tests.append("unknown command error")
            print(f"   ❌ unknown command error failed: {stderr}")
        
        # Test missing required parameters
        success, stdout, stderr = self.run_command([
            "servers", "add"
        ], expect_success=False)
        if success:  # Should fail (success=True means it matched our expectation of failure)
            self.passed_tests.append("missing required parameters")
            print("   ✅ missing required parameters")
        else:
            self.failed_tests.append("missing required parameters")
            print(f"   ❌ missing required parameters failed: {stderr}")
    
    def run_all_tests(self):
        """Run all smoke tests."""
        print("🚀 Starting Plex Sync CLI Smoke Tests")
        print("=" * 50)
        
        if LIVE_MODE:
            print("🌐 Running in LIVE MODE with Plex server")
            print(f"   Server: {TEST_SERVER_URL}")
            print(f"   Name: {TEST_SERVER_NAME}")
        else:
            print("🔌 Running in OFFLINE MODE (no network operations)")
            print("   Set PLEX_BASE_URL and PLEX_TOKEN to enable live mode")
        print()
        
        try:
            self.setup()
            
            # Run all test suites
            self.test_help_commands()
            self.test_servers_commands()
            self.test_libraries_commands()
            self.test_mappings_commands()
            self.test_ingest_commands()
            self.test_items_commands()
            self.test_guid_commands()
            self.test_error_handling()
            
        finally:
            self.teardown()
        
        # Print results
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS")
        print("=" * 50)
        print(f"✅ Passed: {len(self.passed_tests)}")
        print(f"❌ Failed: {len(self.failed_tests)}")
        
        if self.passed_tests:
            print("\n✅ PASSED TESTS:")
            for test in self.passed_tests:
                print(f"   - {test}")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"   - {test}")
        
        return len(self.failed_tests) == 0


def main():
    """Main entry point."""
    runner = SmokeTestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n🎉 All smoke tests passed!")
        sys.exit(0)
    else:
        print(f"\n💥 {len(runner.failed_tests)} smoke test(s) failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
