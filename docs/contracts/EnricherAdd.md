# Enricher Add

## Purpose

Define the behavioral contract for creating new enricher instances. This contract ensures safe, consistent enricher creation with proper validation and configuration handling.

---

## Command Shape

```
retrovue enricher add --type <type> --name <name> [options] [--test-db] [--dry-run] [--json]
```

### Required Parameters

- `--type`: Enricher type identifier ("ffprobe", "metadata", "playout-enricher")
- `--name`: Human-readable name for the enricher instance

### Type-Specific Parameters

**FFprobe Enrichers:**

- `--ffprobe-path`: Path to FFprobe executable (optional, default: "ffprobe")
- `--timeout`: Timeout in seconds for FFprobe operations (optional, default: 30)

**Metadata Enrichers:**

- `--sources`: Comma-separated list of metadata sources (optional, default: "imdb,tmdb")
- `--api-key`: API key for metadata services (optional)

**Playout Enrichers:**

- `--config`: JSON configuration for the enricher (optional, default: "{}")

### Optional Parameters

- `--test-db`: Direct command to test database environment
- `--dry-run`: Show what would be created without executing
- `--json`: Output result in JSON format
- `--help`: Show help for the specified enricher type

---

## Safety Expectations

### Confirmation Model

- No confirmation prompts required for enricher creation
- `--dry-run` shows configuration validation and enricher ID generation
- `--force` flag not applicable (non-destructive operation)

### Validation Requirements

- Enricher type must be valid and available
- Required parameters must be provided for each enricher type
- Enricher ID must be unique (format: "enricher-{type}-{hash}")
- Configuration must be valid before database operations
- Scope validation must be performed

---

## Output Format

### Human-Readable Output

**Success Output:**

```
Successfully created ffprobe enricher: Video Analysis
  ID: enricher-ffprobe-a1b2c3d4
  Type: ffprobe
  Scope: ingest
  Name: Video Analysis
  Configuration: {"ffprobe_path": "ffprobe", "timeout": 30}
```

**Help Output:**

```
Help for ffprobe enricher type:
Description: Video/audio analysis using FFprobe

Required parameters:
  --name: Human-readable label for this enricher

Optional parameters:
  --ffprobe-path: Path to FFprobe executable
    Default: ffprobe
  --timeout: Timeout in seconds for FFprobe operations
    Default: 30

Examples:
  retrovue enricher add --type ffprobe --name 'Video Analysis'
  retrovue enricher add --type ffprobe --name 'Fast Analysis' --timeout 10
```

### JSON Output

```json
{
  "enricher_id": "enricher-ffprobe-a1b2c3d4",
  "type": "ffprobe",
  "scope": "ingest",
  "name": "Video Analysis",
  "config": {
    "ffprobe_path": "ffprobe",
    "timeout": 30
  },
  "status": "created"
}
```

---

## Exit Codes

- `0`: Enricher created successfully
- `1`: Validation error, missing parameters, or creation failure

---

## Data Effects

### Database Changes

1. **Enricher Table**: New record inserted with:

   - Generated UUID primary key
   - Enricher ID in format "enricher-{type}-{hash}"
   - Enricher type and scope
   - Configuration JSON
   - Created/updated timestamps

2. **Registry Updates**:
   - Enricher instance registered in registry
   - Configuration validated against type schema
   - Scope validation performed

### Side Effects

- Enricher ID generation (must be unique)
- Configuration validation
- Registry state updates

---

## Behavior Contract Rules (B-#)

- **B-1:** The command MUST validate enricher type against available types before proceeding.
- **B-2:** Required parameters MUST be validated before any database operations.
- **B-3:** Enricher ID MUST be generated in format "enricher-{type}-{hash}" and MUST be unique.
- **B-4:** When `--json` is supplied, output MUST include fields `"enricher_id"`, `"type"`, `"scope"`, `"name"`, `"config"`, and `"status"`.
- **B-5:** On validation failure, the command MUST exit with code `1` and print a human-readable error message.
- **B-6:** The `--dry-run` flag MUST show configuration validation and enricher ID generation without executing.
- **B-7:** The `--help` flag MUST display detailed help for the specified enricher type and MUST exit with code `0` without creating any enricher instances.
- **B-8:** Configuration validation MUST be performed against the enricher type's schema.

---

## Data Contract Rules (D-#)

- **D-1:** Enricher creation MUST occur within a single transaction boundary.
- **D-2:** Enricher ID generation MUST be atomic and collision-free.
- **D-3:** Configuration validation MUST occur before database persistence.
- **D-4:** On transaction failure, ALL changes MUST be rolled back with no partial creation.
- **D-5:** Enricher type validation MUST occur before database operations.
- **D-6:** Scope validation MUST be performed for the enricher type.
- **D-7:** Registry updates MUST occur within the same transaction as enricher creation.
- **D-8:** Configuration schema validation MUST be performed against the enricher type.

---

## Test Coverage Mapping

- `B-1..B-8` → `test_enricher_add_contract.py`
- `D-1..D-8` → `test_enricher_add_data_contract.py`

---

## Error Conditions

### Validation Errors

- Invalid enricher type: "Unknown enricher type 'invalid'. Available types: ffprobe, metadata, playout-enricher"
- Missing required parameters: "Error: --name is required for ffprobe enrichers"
- Invalid configuration: "Error: Invalid configuration for enricher type 'ffprobe'"

### Database Errors

- Duplicate enricher ID: Transaction rollback, clear error message
- Foreign key violations: Transaction rollback, diagnostic information

---

## Examples

### FFprobe Enricher Creation

```bash
# Create FFprobe enricher with default settings
retrovue enricher add --type ffprobe --name "Video Analysis"

# Create FFprobe enricher with custom settings
retrovue enricher add --type ffprobe --name "Fast Analysis" \
  --ffprobe-path "/usr/bin/ffprobe" --timeout 10

# Get help for FFprobe enricher
retrovue enricher add --type ffprobe --help
```

### Metadata Enricher Creation

```bash
# Create metadata enricher with default sources
retrovue enricher add --type metadata --name "Movie Metadata"

# Create metadata enricher with custom sources
retrovue enricher add --type metadata --name "TV Metadata" \
  --sources "tvdb,imdb" --api-key "your-api-key"
```

### Playout Enricher Creation

```bash
# Create playout enricher with default config
retrovue enricher add --type playout-enricher --name "Channel Branding"

# Create playout enricher with custom config
retrovue enricher add --type playout-enricher --name "Custom Overlay" \
  --config '{"overlay_path": "/path/to/overlay.png"}'
```

### Test Environment Usage

```bash
# Test enricher creation in isolated environment
retrovue enricher add --type ffprobe --name "Test Enricher" \
  --test-db --dry-run

# Test with JSON output
retrovue enricher add --type metadata --name "Test Metadata" \
  --test-db --json
```

---

## Supported Enricher Types

- **ffprobe**: Video/audio analysis using FFprobe (ingest scope)
- **metadata**: Metadata extraction and enrichment (ingest scope)
- **playout-enricher**: Playout-scope enricher for channel processing (playout scope)

---

## Safety Guidelines

- Always use `--test-db` for testing enricher creation logic
- Use `--dry-run` to preview enricher creation
- Verify enricher type availability before creation
- Check configuration validation after creation

---

## See Also

- [Enricher List Types](EnricherListTypes.md) - List available enricher types
- [Enricher List](EnricherList.md) - List configured enricher instances
- [Enricher Update](EnricherUpdate.md) - Update enricher configurations
- [Enricher Remove](EnricherRemove.md) - Remove enricher instances
