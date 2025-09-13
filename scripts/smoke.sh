#!/bin/bash
# Comprehensive smoke test script for the Plex Sync CLI
# This script exercises all the new command tree structure

set -e  # Exit on any error
set -o pipefail  # Exit on pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CLI_PATH="$PROJECT_ROOT/cli/plex_sync.py"
TEMP_DIR=$(mktemp -d)
TEMP_DB="$TEMP_DIR/test.db"

# Test configuration
TEST_SERVER_NAME="SmokeTestServer"
TEST_SERVER_URL="http://127.0.0.1:32400"
TEST_SERVER_TOKEN="smoke-test-token-12345"
TEST_LIBRARY_KEY="1"
TEST_GUID="com.plexapp.agents.imdb://tt1234567"

# Counters
PASSED=0
FAILED=0

# Cleanup function
cleanup() {
    echo -e "${BLUE}🧹 Cleaning up temporary directory: $TEMP_DIR${NC}"
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASSED++))
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    ((FAILED++))
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to get server ID from output
get_server_id() {
    local output="$1"
    # Extract server ID using multiple patterns
    # Pattern 1: "Added server ID 1" or "Added server 1"
    local id=$(echo "$output" | grep -o 'Added server[[:space:]]*ID[[:space:]]*[0-9]\+' | grep -o '[0-9]\+' | head -1)
    if [ -n "$id" ]; then
        echo "$id"
        return
    fi
    
    # Pattern 2: "Added server 1"
    id=$(echo "$output" | grep -o 'Added server[[:space:]]*[0-9]\+' | grep -o '[0-9]\+' | head -1)
    if [ -n "$id" ]; then
        echo "$id"
        return
    fi
    
    # Pattern 3: Table format "ID   1   Name"
    id=$(echo "$output" | grep -o 'ID[[:space:]]*[0-9]\+[[:space:]]*[A-Za-z]' | grep -o '[0-9]\+' | head -1)
    if [ -n "$id" ]; then
        echo "$id"
        return
    fi
    
    # Pattern 4: "Set server ID 1 as default"
    id=$(echo "$output" | grep -o 'Set server ID [0-9]\+' | grep -o '[0-9]\+' | head -1)
    if [ -n "$id" ]; then
        echo "$id"
        return
    fi
    
    # Fallback: any number
    echo "$output" | grep -o '[0-9]\+' | head -1
}

# Function to initialize database
init_database() {
    local db_path="$1"
    local schema_path="$PROJECT_ROOT/sql/schema.sql"
    
    if [ ! -f "$schema_path" ]; then
        log_error "Schema file not found: $schema_path"
        exit 1
    fi
    
    # Use sqlite3 command to initialize database
    sqlite3 "$db_path" < "$schema_path"
    if [ $? -ne 0 ]; then
        log_error "Failed to initialize database with schema"
        exit 1
    fi
}

# Test runner function
run_test() {
    local test_name="$1"
    local command="$2"
    local expect_success="${3:-true}"
    
    log_info "Testing: $test_name"
    
    if eval "$command" >/dev/null 2>&1; then
        if [ "$expect_success" = "true" ]; then
            log_success "$test_name"
            return 0
        else
            log_error "$test_name (unexpected success)"
            return 1
        fi
    else
        if [ "$expect_success" = "false" ]; then
            log_success "$test_name (expected failure)"
            return 0
        else
            log_error "$test_name"
            return 1
        fi
    fi
}

# Offline test runner function - expects exit code 3
run_offline_test() {
    local name="$1"; shift
    local -a cmd=( "$@" )
    log_info "Testing (offline): $name"
    if "${cmd[@]}" >/dev/null 2>&1; then
        log_error "$name (unexpected success)"; return 1
    else
        local code=$?
        [[ $code -eq 3 ]] && log_success "$name (offline code 3)" || { log_error "$name (exit $code, expected 3)"; return 1; }
    fi
}

# Main test execution
main() {
    echo -e "${BLUE}🚀 Starting Plex Sync CLI Smoke Tests${NC}"
    echo "=================================================="
    
    # Check for Plex environment variables (unless in offline mode)
    if [ "$PLEX_OFFLINE" != "1" ] && ([ -z "$PLEX_BASE_URL" ] || [ -z "$PLEX_TOKEN" ]); then
        echo -e "${RED}❌ Missing required environment variables${NC}"
        echo "   Please set PLEX_BASE_URL and PLEX_TOKEN to run live tests"
        echo "   Example:"
        echo "     export PLEX_BASE_URL=\"http://192.168.1.100:32400\""
        echo "     export PLEX_TOKEN=\"your_plex_token_here\""
        echo "     export PLEX_SERVER_NAME=\"HomePlex\"  # optional"
        echo ""
        echo "   Or set PLEX_OFFLINE=1 to run in offline mode"
        exit 1
    fi
    
    echo -e "${BLUE}🔧 Setting up test environment...${NC}"
    echo "   Temporary directory: $TEMP_DIR"
    echo "   Test database: $TEMP_DB"
    if [ "$PLEX_OFFLINE" = "1" ]; then
        echo "   Mode: OFFLINE (no network operations)"
        echo "   Server: Test server (offline mode)"
    else
        echo "   Mode: LIVE (with Plex server)"
        echo "   Plex server: $PLEX_BASE_URL"
        echo "   Server name: ${PLEX_SERVER_NAME:-LivePlex}"
    fi
    echo ""
    
    # Test help commands
    echo -e "${BLUE}📖 Testing help commands...${NC}"
    run_test "main help" "\"${PYTHON:-python3}\" '$CLI_PATH' --help | grep -qE '(Usage:|Options:|Subcommands:|Command Groups:|Examples:|Description:)'"
    run_test "servers help" "\"${PYTHON:-python3}\" '$CLI_PATH' servers --help | grep -qE '(Usage:|Options:|Subcommands:|Command Groups:|Examples:|Description:)'"
    run_test "libraries help" "\"${PYTHON:-python3}\" '$CLI_PATH' libraries --help | grep -qE '(Usage:|Options:|Subcommands:|Command Groups:|Examples:|Description:)'"
    run_test "mappings help" "\"${PYTHON:-python3}\" '$CLI_PATH' mappings --help | grep -qE '(Usage:|Options:|Subcommands:|Command Groups:|Examples:|Description:)'"
    run_test "ingest help" "\"${PYTHON:-python3}\" '$CLI_PATH' ingest --help | grep -qE '(Usage:|Options:|Subcommands:|Command Groups:|Examples:|Description:)'"
    run_test "items help" "\"${PYTHON:-python3}\" '$CLI_PATH' items --help | grep -qE '(Usage:|Options:|Subcommands:|Command Groups:|Examples:|Description:)'"
    run_test "guid help" "\"${PYTHON:-python3}\" '$CLI_PATH' guid --help | grep -qE '(Usage:|Options:|Subcommands:|Command Groups:|Examples:|Description:)'"
    
    # Test server commands
    echo -e "${BLUE}🖥️  Testing server commands...${NC}"
    
    # Initialize database
    init_database "$TEMP_DB"
    
    run_test "servers list" "\"${PYTHON:-python3}\" '$CLI_PATH' servers list --db '$TEMP_DB'"
    
    # Add server and capture ID using environment variables or test values
    if [ "$PLEX_OFFLINE" = "1" ]; then
        SERVER_NAME="TestServer"
        SERVER_URL="http://127.0.0.1:32400"
        SERVER_TOKEN="test-token-12345"
    else
        SERVER_NAME="${PLEX_SERVER_NAME:-LivePlex}"
        SERVER_URL="$PLEX_BASE_URL"
        SERVER_TOKEN="$PLEX_TOKEN"
    fi
    SERVER_OUTPUT=$("${PYTHON:-python3}" "$CLI_PATH" --format json servers add --db "$TEMP_DB" --name "$SERVER_NAME" --base-url "$SERVER_URL" --token "$SERVER_TOKEN" 2>/dev/null)
    if [ $? -eq 0 ]; then
        log_success "servers add"
        SERVER_ID=$("${PYTHON:-python3}" - <<'PY'
import sys, json
try:
    d=json.load(sys.stdin)
    print(d.get("id") or (d.get("servers", [{}])[0].get("id")) or "")
except Exception:
    print("")
PY
<<< "$SERVER_OUTPUT")
        if [ -z "$SERVER_ID" ]; then
            # Fallback to text parsing
            SERVER_ID=$(get_server_id "$SERVER_OUTPUT")
        fi
        SERVER_ID=${SERVER_ID:-1}  # Default to 1 if still not found
    else
        log_error "servers add failed"
        SERVER_ID=1  # Fallback for remaining tests
    fi
    
    run_test "servers list with data" "\"${PYTHON:-python3}\" '$CLI_PATH' servers list --db '$TEMP_DB' | grep -q '$SERVER_NAME'"
    run_test "servers update-token" "\"${PYTHON:-python3}\" '$CLI_PATH' servers update-token --db '$TEMP_DB' --server-id '$SERVER_ID' --token 'updated-token-67890'"
    run_test "servers set-default" "\"${PYTHON:-python3}\" '$CLI_PATH' servers set-default --db '$TEMP_DB' --server-id '$SERVER_ID'"
    run_test "servers delete" "\"${PYTHON:-python3}\" '$CLI_PATH' servers delete --db '$TEMP_DB' --server-id '$SERVER_ID'"
    
    # Re-add server for library tests and get new ID
    SERVER_OUTPUT=$("${PYTHON:-python3}" "$CLI_PATH" --format json servers add --db "$TEMP_DB" --name "$SERVER_NAME" --base-url "$SERVER_URL" --token "$SERVER_TOKEN" 2>/dev/null)
    SERVER_ID=$("${PYTHON:-python3}" - <<'PY'
import sys, json
try:
    d=json.load(sys.stdin)
    print(d.get("id") or (d.get("servers", [{}])[0].get("id")) or "")
except Exception:
    print("")
PY
<<< "$SERVER_OUTPUT")
    if [ -z "$SERVER_ID" ]; then
        # Fallback to text parsing
        SERVER_ID=$(get_server_id "$SERVER_OUTPUT")
    fi
    SERVER_ID=${SERVER_ID:-1}
    
    # Set as default server
    run_test "servers set-default (pre-libraries)" "\"${PYTHON:-python3}\" '$CLI_PATH' servers set-default --db '$TEMP_DB' --server-id '$SERVER_ID'"
    
    # Test library commands
    echo -e "${BLUE}📚 Testing library commands...${NC}"
    run_test "libraries list" "\"${PYTHON:-python3}\" '$CLI_PATH' libraries list --db '$TEMP_DB'"
    if [ "$PLEX_OFFLINE" = "1" ]; then
        run_offline_test "libraries sync (offline mode)" "${PYTHON:-python3}" "$CLI_PATH" --offline libraries sync --db "$TEMP_DB"
    else
        run_test "libraries sync (live mode)" "\"${PYTHON:-python3}\" '$CLI_PATH' libraries sync --db '$TEMP_DB'"
    fi
    run_test "libraries sync list" "\"${PYTHON:-python3}\" '$CLI_PATH' libraries sync list --db '$TEMP_DB'"
    run_test "libraries sync enable (no library)" "\"${PYTHON:-python3}\" '$CLI_PATH' libraries sync enable --db '$TEMP_DB' --library-id 1" "false"
    run_test "libraries sync disable (no library)" "\"${PYTHON:-python3}\" '$CLI_PATH' libraries sync disable --db '$TEMP_DB' --library-id 1" "false"
    run_test "libraries delete (no library)" "\"${PYTHON:-python3}\" '$CLI_PATH' libraries delete --db '$TEMP_DB' --library-id 1" "false"
    run_test "libraries delete --all --yes" "\"${PYTHON:-python3}\" '$CLI_PATH' libraries delete --db '$TEMP_DB' --all --yes"
    
    # Test mapping commands
    echo -e "${BLUE}🗺️  Testing mapping commands...${NC}"
    
    # Insert a library row and capture its ID
    LIB_ID=$(sqlite3 "$TEMP_DB" "INSERT INTO libraries (server_id, plex_library_key, title, library_type, sync_enabled) VALUES ($SERVER_ID, '1', 'Test Library', 'movie', 1); SELECT last_insert_rowid();")
    
    run_test "mappings list" "\"${PYTHON:-python3}\" '$CLI_PATH' mappings list --db '$TEMP_DB' --server-id '$SERVER_ID' --library-id '$LIB_ID'"
    run_test "mappings add" "\"${PYTHON:-python3}\" '$CLI_PATH' mappings add --db '$TEMP_DB' --server-id '$SERVER_ID' --library-id '$LIB_ID' --plex-prefix '/data/Movies' --local-prefix 'C:/Media/Movies'"
    run_test "mappings list with data" "\"${PYTHON:-python3}\" '$CLI_PATH' mappings list --db '$TEMP_DB' --server-id '$SERVER_ID' --library-id '$LIB_ID' | grep -q '/data/Movies'"
    run_test "mappings resolve" "\"${PYTHON:-python3}\" '$CLI_PATH' mappings resolve --db '$TEMP_DB' --server-id '$SERVER_ID' --library-id '$LIB_ID' --plex-path '/data/Movies/Test.mkv'"
    run_test "mappings test" "\"${PYTHON:-python3}\" '$CLI_PATH' mappings test --db '$TEMP_DB' --server-id '$SERVER_ID' --library-id '$LIB_ID' --plex-path '/data/Movies/Test.mkv'"
    
    # Test ingest commands
    echo -e "${BLUE}📥 Testing ingest commands...${NC}"
    run_test "ingest status" "\"${PYTHON:-python3}\" '$CLI_PATH' ingest status --db '$TEMP_DB'"
    if [ "$PLEX_OFFLINE" = "1" ]; then
        run_offline_test "ingest run --dry-run (offline mode)" "${PYTHON:-python3}" "$CLI_PATH" --offline ingest run --db "$TEMP_DB" --mode full --dry-run
    else
        run_test "ingest run --dry-run (live mode)" "\"${PYTHON:-python3}\" '$CLI_PATH' ingest run --db '$TEMP_DB' --mode full --dry-run"
    fi
    
    # Test items commands
    echo -e "${BLUE}📦 Testing items commands...${NC}"
    if [ "$PLEX_OFFLINE" = "1" ]; then
        run_offline_test "items preview (offline mode)" "${PYTHON:-python3}" "$CLI_PATH" --offline items preview --db "$TEMP_DB" --library-key "$TEST_LIBRARY_KEY" --kind movie --limit 1
    else
        run_test "items preview (live mode)" "\"${PYTHON:-python3}\" '$CLI_PATH' items preview --db '$TEMP_DB' --library-key '$TEST_LIBRARY_KEY' --kind movie --limit 1"
    fi
    
    # Create test JSON file
    cat > "$TEMP_DIR/test_movie.json" << EOF
{
    "title": "Test Movie",
    "type": "movie",
    "duration": 7200000,
    "contentRating": "PG-13",
    "ratingKey": "12345"
}
EOF
    
    run_test "items map --from-json" "\"${PYTHON:-python3}\" '$CLI_PATH' items map --from-json '$TEMP_DIR/test_movie.json'"
    
# Test items map --from-stdin using here-string
run_test "items map --from-stdin" "\"${PYTHON:-python3}\" '$CLI_PATH' items map --from-stdin" <<< \
    '{"title":"Test Movie","type":"movie","duration":7200000,"contentRating":"PG-13","ratingKey":"12345"}'
    
    # Test GUID commands
    echo -e "${BLUE}🔍 Testing GUID commands...${NC}"
    run_test "guid test" "\"${PYTHON:-python3}\" '$CLI_PATH' guid test --guid '$TEST_GUID'"
    run_test "guid test (tvdb)" "\"${PYTHON:-python3}\" '$CLI_PATH' guid test --guid 'com.plexapp.agents.thetvdb://123456'"
    
    # Test error handling
    echo -e "${BLUE}⚠️  Testing error handling...${NC}"
    run_test "unknown command error" "\"${PYTHON:-python3}\" '$CLI_PATH' unknown-command" "false"
    run_test "missing required parameters" "\"${PYTHON:-python3}\" '$CLI_PATH' servers add" "false"
    
    # Print results
    echo ""
    echo "=================================================="
    echo -e "${BLUE}📊 TEST RESULTS${NC}"
    echo "=================================================="
    echo -e "${GREEN}✅ Passed: $PASSED${NC}"
    echo -e "${RED}❌ Failed: $FAILED${NC}"
    
    if [ $FAILED -eq 0 ]; then
        echo -e "\n${GREEN}🎉 All smoke tests passed!${NC}"
        exit 0
    else
        echo -e "\n${RED}💥 $FAILED smoke test(s) failed!${NC}"
        exit 1
    fi
}

# Run main function
main "$@"
