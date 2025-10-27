# Source Discover

## Purpose

Define the behavioral contract for discovering collections from content sources. This contract ensures safe collection discovery with proper validation and persistence handling.

---

## Command Shape

```
retrovue source discover <source_id> [--json] [--test-db] [--dry-run]
```

### Required Parameters

- `source_id`: Source identifier (UUID, external ID, or name)

### Optional Parameters

- `--json`: Output result in JSON format
- `--test-db`: Direct command to test database environment
- `--dry-run`: Show what would be discovered without persisting

---

## Safety Expectations

### Discovery Model

- **Non-destructive operation**: Only discovers and persists collections
- **Idempotent**: Safe to run multiple times
- **Dry-run support**: Preview discovery without database changes
- **Test isolation**: `--test-db` prevents external API calls

### Collection Handling

- Newly discovered collections start with `enabled=False`
- Existing collections are updated with current metadata
- Duplicate collections are skipped with notification
- Path mappings created with empty `local_path` values

---

## Output Format

### Human-Readable Output

**Discovery Results:**

```
Successfully added 3 collections from 'My Plex Server':
  • Movies (ID: 1) - Disabled by default
  • TV Shows (ID: 2) - Disabled by default
  • Music (ID: 3) - Disabled by default

Use 'retrovue collection update <name> --sync-enabled true' to enable collections for sync
```

**Dry-run Output:**

```
Would discover 3 collections from 'My Plex Server':
  • Movies (ID: 1) - Would be created
  • TV Shows (ID: 2) - Would be created
  • Music (ID: 3) - Would be created
```

### JSON Output

```json
{
  "source": {
    "id": "4b2b05e7-d7d2-414a-a587-3f5df9b53f44",
    "name": "My Plex Server",
    "type": "plex"
  },
  "collections_added": 3,
  "collections": [
    {
      "external_id": "1",
      "name": "Movies",
      "sync_enabled": false,
      "ingestible": false,
      "source_type": "plex"
    },
    {
      "external_id": "2",
      "name": "TV Shows",
      "sync_enabled": false,
      "ingestible": false,
      "source_type": "plex"
    },
    {
      "external_id": "3",
      "name": "Music",
      "sync_enabled": false,
      "ingestible": false,
      "source_type": "plex"
    }
  ]
}
```

---

## Exit Codes

- `0`: Discovery completed successfully
- `1`: Source not found, discovery failed, or validation error

---

## Data Effects

### Database Changes

1. **Collection Persistence**:

   - New SourceCollection records created
   - Existing collections updated with current metadata
   - All collections start with `enabled=False`

2. **Path Mapping Creation**:
   - PathMapping records created for each collection
   - `plex_path` populated from external system
   - `local_path` left empty for operator configuration

### Side Effects

- External API calls to source system (unless `--test-db`)
- Database transaction for collection persistence
- Logging of discovery results and errors

---

## Behavior Contract Rules (B-#)

- **B-1:** The command MUST validate source existence before attempting discovery.
- **B-2:** The `--dry-run` flag MUST show what would be discovered without persisting to database.
- **B-3:** When `--json` is supplied, output MUST include fields `"source"`, `"collections_added"`, and `"collections"`.
- **B-4:** On validation failure (source not found), the command MUST exit with code `1` and print "Error: Source 'X' not found".
- **B-5:** Empty discovery results MUST return exit code `0` with message "No collections found for source 'X'".
- **B-6:** Duplicate collections MUST be skipped with notification message.
- **B-7:** The command MUST support both Plex and filesystem source types (filesystem returns empty).

---

## Data Contract Rules (D-#)

- **D-1:** Collection discovery MUST occur within a single transaction boundary.
- **D-2:** Newly discovered collections MUST be persisted with `sync_enabled=False`.
- **D-3:** Discovery MUST NOT flip existing collections from `sync_enabled=False` to `sync_enabled=True`.
- **D-4:** PathMapping records MUST be created with empty `local_path` for new collections.
- **D-5:** On transaction failure, ALL changes MUST be rolled back with no partial persistence.
- **D-6:** Duplicate external ID checking MUST prevent duplicate collection creation.
- **D-7:** Collection metadata MUST be updated for existing collections.

---

## Test Coverage Mapping

- `B-1..B-7` → `test_source_discover_contract.py`
- `D-1..D-7` → `test_source_discover_data_contract.py`

---

## Error Conditions

### Validation Errors

- Source not found: "Error: Source 'invalid-source' not found"
- Unsupported source type: "Error: Source type 'filesystem' not supported for discovery"
- Missing configuration: "Error: Plex source 'My Plex' missing base_url or token"

### Discovery Errors

- Connection failure: Graceful error handling, no collections discovered
- API errors: Clear error messages with diagnostic information
- Empty results: "No collections found for source 'My Plex Server'"

### Database Errors

- Transaction rollback on any persistence failure
- Foreign key constraint violations handled gracefully
- Duplicate external ID prevention

---

## Examples

### Basic Discovery

```bash
# Discover collections from Plex source
retrovue source discover "My Plex Server"

# Discover by external ID
retrovue source discover plex-5063d926

# Discover with JSON output
retrovue source discover "My Plex Server" --json
```

### Dry-run Testing

```bash
# Preview discovery without changes
retrovue source discover "My Plex Server" --dry-run

# Test discovery logic
retrovue source discover "Test Plex" --test-db --dry-run
```

### Test Environment Usage

```bash
# Test discovery in isolated environment
retrovue source discover "Test Plex Server" --test-db

# Test with mock data
retrovue source discover "Test Source" --test-db --json
```

---

## Supported Source Types

- **Plex**: Full collection discovery from Plex Media Server
- **Filesystem**: Not supported (collections are directory-based)

---

## Safety Guidelines

- Always use `--test-db` for testing discovery logic
- Use `--dry-run` to preview discovery results
- Verify source configuration before discovery
- Check collection counts after discovery
