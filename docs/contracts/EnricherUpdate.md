# Enricher Update

## Purpose

Define the behavioral contract for updating enricher instance configurations. This contract ensures safe, consistent enricher updates with proper validation and configuration handling.

---

## Command Shape

```
retrovue enricher update <enricher_id> [options] [--test-db] [--dry-run] [--json]
```

### Required Parameters

- `enricher_id`: Enricher instance identifier (UUID or enricher ID)

### Type-Specific Parameters

**FFprobe Enrichers:**

- `--ffprobe-path`: Path to FFprobe executable
- `--timeout`: Timeout in seconds for FFprobe operations

**Metadata Enrichers:**

- `--sources`: Comma-separated list of metadata sources
- `--api-key`: API key for metadata services

**Playout Enrichers:**

- `--config`: JSON configuration for the enricher

### Optional Parameters

- `--test-db`: Direct command to test database environment
- `--dry-run`: Show what would be updated without executing
- `--json`: Output result in JSON format

---

## Safety Expectations

### Confirmation Model

- No confirmation prompts required for enricher updates
- `--dry-run` shows configuration validation and update preview
- `--force` flag not applicable (non-destructive operation)

### Validation Requirements

- Enricher instance must exist and be available
- Configuration must be valid for the enricher type
- Configuration validation before database operations
- Scope validation must be maintained

---

## Output Format

### Human-Readable Output

**Success Output:**

```
Successfully updated enricher: Video Analysis
  ID: enricher-ffprobe-a1b2c3d4
  Type: ffprobe
  Scope: ingest
  Name: Video Analysis
  Configuration: {"ffprobe_path": "/usr/bin/ffprobe", "timeout": 60}
  Updated: 2024-01-15 10:30:00
```

**Dry-run Output:**

```
Would update enricher: Video Analysis
  ID: enricher-ffprobe-a1b2c3d4
  Type: ffprobe
  Scope: ingest
  Name: Video Analysis
  Current Configuration: {"ffprobe_path": "ffprobe", "timeout": 30}
  New Configuration: {"ffprobe_path": "/usr/bin/ffprobe", "timeout": 60}
```

### JSON Output

```json
{
  "enricher_id": "enricher-ffprobe-a1b2c3d4",
  "type": "ffprobe",
  "scope": "ingest",
  "name": "Video Analysis",
  "config": {
    "ffprobe_path": "/usr/bin/ffprobe",
    "timeout": 60
  },
  "status": "updated",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

## Exit Codes

- `0`: Enricher updated successfully
- `1`: Validation error, enricher not found, or update failure

---

## Data Effects

### Database Changes

1. **Enricher Table**: Record updated with:

   - New configuration JSON
   - Updated timestamp
   - Validation status

2. **Registry Updates**:
   - Enricher instance configuration updated in registry
   - Configuration validated against type schema
   - Scope validation maintained

### Side Effects

- Configuration validation
- Registry state updates
- No external system calls

---

## Behavior Contract Rules (B-#)

- **B-1:** The command MUST validate enricher instance existence before attempting updates.
- **B-2:** Configuration validation MUST be performed against the enricher type's schema.
- **B-3:** When `--json` is supplied, output MUST include fields `"enricher_id"`, `"type"`, `"scope"`, `"name"`, `"config"`, `"status"`, and `"updated_at"`.
- **B-4:** On validation failure (enricher not found), the command MUST exit with code `1` and print "Error: Enricher 'X' not found".
- **B-5:** The `--dry-run` flag MUST show configuration validation and update preview without executing.
- **B-6:** Configuration updates MUST preserve enricher type and scope.
- **B-7:** The command MUST support partial configuration updates (only specified parameters).
- **B-8:** Update operations MUST be atomic and consistent.

---

## Data Contract Rules (D-#)

- **D-1:** Enricher updates MUST occur within a single transaction boundary.
- **D-2:** Configuration validation MUST occur before database persistence.
- **D-3:** On transaction failure, ALL changes MUST be rolled back with no partial updates.
- **D-4:** Enricher type and scope MUST NOT be changed during updates.
- **D-5:** Registry updates MUST occur within the same transaction as enricher updates.
- **D-6:** Configuration schema validation MUST be performed against the enricher type.
- **D-7:** Update operations MUST preserve enricher instance identity.
- **D-8:** Configuration updates MUST maintain backward compatibility where possible.

---

## Test Coverage Mapping

- `B-1..B-8` → `test_enricher_update_contract.py`
- `D-1..D-8` → `test_enricher_update_data_contract.py`

---

## Error Conditions

### Validation Errors

- Enricher not found: "Error: Enricher 'enricher-ffprobe-a1b2c3d4' not found"
- Invalid configuration: "Error: Invalid configuration for enricher type 'ffprobe'"
- Missing parameters: "Error: No configuration parameters provided for update"

### Database Errors

- Transaction rollback on any persistence failure
- Foreign key constraint violations handled gracefully
- Concurrent modification: Transaction rollback with retry suggestion

---

## Examples

### FFprobe Enricher Update

```bash
# Update FFprobe path
retrovue enricher update enricher-ffprobe-a1b2c3d4 \
  --ffprobe-path "/usr/bin/ffprobe"

# Update timeout
retrovue enricher update enricher-ffprobe-a1b2c3d4 \
  --timeout 60

# Update multiple parameters
retrovue enricher update enricher-ffprobe-a1b2c3d4 \
  --ffprobe-path "/usr/bin/ffprobe" --timeout 60
```

### Metadata Enricher Update

```bash
# Update metadata sources
retrovue enricher update enricher-metadata-b2c3d4e5 \
  --sources "tvdb,imdb,tmdb"

# Update API key
retrovue enricher update enricher-metadata-b2c3d4e5 \
  --api-key "new-api-key"
```

### Playout Enricher Update

```bash
# Update playout configuration
retrovue enricher update enricher-playout-c3d4e5f6 \
  --config '{"overlay_path": "/new/path/to/overlay.png", "opacity": 0.8}'
```

### Test Environment Usage

```bash
# Test enricher update in isolated environment
retrovue enricher update enricher-ffprobe-a1b2c3d4 \
  --timeout 60 --test-db --dry-run

# Test with JSON output
retrovue enricher update enricher-metadata-b2c3d4e5 \
  --sources "tvdb,imdb" --test-db --json
```

---

## Supported Enricher Types

- **ffprobe**: Video/audio analysis using FFprobe (ingest scope)
- **metadata**: Metadata extraction and enrichment (ingest scope)
- **playout-enricher**: Playout-scope enricher for channel processing (playout scope)

---

## Safety Guidelines

- Always use `--test-db` for testing enricher update logic
- Use `--dry-run` to preview enricher updates
- Verify enricher instance existence before updates
- Check configuration validation after updates

---

## See Also

- [Enricher List Types](EnricherListTypes.md) - List available enricher types
- [Enricher Add](EnricherAdd.md) - Create enricher instances
- [Enricher List](EnricherList.md) - List configured enricher instances
- [Enricher Remove](EnricherRemove.md) - Remove enricher instances
