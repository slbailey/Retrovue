# Source List Types

## Purpose

Define the behavioral contract for listing available source types from the importer registry. This contract ensures consistent enumeration of source types derived from discovered importer implementations that comply with the ImporterInterface runtime contract.

---

## Command Shape

```
retrovue source list-types [--json] [--test-db] [--dry-run]
```

### Optional Parameters

- `--json`: Output result in JSON format
- `--test-db`: Direct command to test database environment
- `--dry-run`: Show what would be listed without executing

---

## Safety Expectations

### Enumeration Model

- **Non-destructive operation**: Only lists available source types
- **Idempotent**: Safe to run multiple times
- **Dry-run support**: Preview enumeration without external effects. In --dry-run mode, the command MAY use an in-memory view of the registry state instead of re-scanning the filesystem.
- **Test isolation**: `--test-db` prevents external system calls

### Source Type Derivation

- Source types derived from importer filenames following `{source_type}_importer.py` pattern
- Registry maintains mapping from source types to importer implementations
- All importers must implement `ImporterInterface` runtime contract
- Validation of source type uniqueness and interface compliance
- Reporting of source type availability and interface status

---

## Output Format

### Human-Readable Output

**Source Types Available:**

```
Available source types:
  plex
  filesystem
  jellyfin

Total: 3 source types available
```

**Dry-run Output:**

```
Would list 3 source types from registry:
  • plex (plex_importer.py)
  • filesystem (filesystem_importer.py)
  • jellyfin (jellyfin_importer.py)
```

### JSON Output

```json
{
  "status": "ok",
  "source_types": [
    {
      "name": "plex",
      "importer_file": "plex_importer.py",
      "display_name": "Plex Media Server",
      "available": true,
      "interface_compliant": true,
      "status": "valid"
    },
    {
      "name": "filesystem",
      "importer_file": "filesystem_importer.py",
      "display_name": "Local Filesystem",
      "available": true,
      "interface_compliant": true,
      "status": "valid"
    },
    {
      "name": "jellyfin",
      "importer_file": "jellyfin_importer.py",
      "display_name": "Jellyfin Media Server",
      "available": true,
      "interface_compliant": true,
      "status": "valid"
    }
  ],
  "total": 3
}
```

---

## Exit Codes

- `0`: Source types listed successfully
- `1`: Registry error, enumeration failure, or validation error

---

## Data Effects

### Registry Enumeration

1. **Source Type Discovery**:

   - Registry scans discovered importers from `adapters/importers/` directory
   - Extracts source types from importer filenames following `{source_type}_importer.py` pattern
   - Validates source type uniqueness and interface compliance
   - Checks `ImporterInterface` implementation for each discovered importer

2. **Mapping Validation**:
   - Verifies source type to importer mapping
   - Reports availability status and interface compliance
   - Maintains registry state consistency
   - Validates configuration schema compliance

### Side Effects

- Registry state queries (read-only)
- No external system calls or database modifications
- No filesystem changes

---

## Behavior Contract Rules (B-#)

- **B-1:** The command MUST return source types derived from discovered importer filenames following `{source_type}_importer.py` pattern.
- **B-2:** The command MUST validate source type uniqueness and interface compliance before reporting.
- **B-3:** When `--json` is supplied, output MUST include fields `"status"`, `"source_types"`, and `"total"` with appropriate data structures including interface compliance status.
- **B-4:** On enumeration failure (registry error), the command MUST exit with code `1` and print a human-readable error message.
- **B-5:** The `--dry-run` flag MUST show what would be listed without executing external validation. In --dry-run mode, the command MAY use an in-memory view of the registry state instead of re-scanning the filesystem. It MUST still produce deterministic output.
- **B-6:** Source type enumeration MUST be deterministic - the same registry state MUST produce the same enumeration results.
- **B-7:** The command MUST support both valid and invalid importer files, reporting availability and interface compliance appropriately.
- **B-8:** Empty enumeration results (no source types) MUST return exit code `0` with message "No source types available".

---

## Data Contract Rules (D-#)

- **D-1:** Registry MUST maintain mapping from source types to importer implementations that implement `ImporterInterface`.
- **D-2:** Source type mapping MUST be derived automatically from importer filenames following `{source_type}_importer.py` pattern.
- **D-3:** Multiple importers claiming the same source type MUST cause registration failure with clear error message.
- **D-4:** Source type enumeration MUST NOT modify external systems or database tables.
- **D-5:** Registry state queries MUST be read-only during enumeration.
- **D-6:** Source type availability MUST be validated against importer implementation status and `ImporterInterface` compliance.
- **D-7:** Enumeration operations MUST be atomic and consistent.
- **D-8:** Source type mapping MUST be maintained atomically during registry updates.

---

## Test Coverage Mapping

- `B-1..B-8` → `test_source_list_types_contract.py`
- `D-1..D-8` → `test_source_list_types_data_contract.py`

---

## Error Conditions

### Registry Errors

- Registry not initialized: "Error: Importer registry not initialized"
- Discovery failure: "Error: Failed to discover importers from registry"
- Mapping error: "Error: Failed to build source type mapping"

### Validation Errors

- Duplicate source types: "Error: Multiple importers claim source type 'plex'"
- Invalid filename pattern: "Error: Importer file 'plex.py' does not follow naming pattern '{source_type}\_importer.py'"
- Interface violation: "Error: Importer 'plex' does not implement ImporterInterface"
- Configuration schema error: "Error: Importer 'plex' has invalid configuration schema"

---

## Examples

### Basic Enumeration

```bash
# List all available source types
retrovue source list-types

# List with JSON output
retrovue source list-types --json

# Preview enumeration without validation
retrovue source list-types --dry-run
```

### Test Environment Usage

```bash
# Test source type enumeration in isolated environment
retrovue source list-types --test-db

# Test with mock importer files
retrovue source list-types --test-db --json
```

### Error Scenarios

```bash
# Registry not initialized
retrovue source list-types
# Error: Importer registry not initialized

# No source types available
retrovue source list-types
# No source types available
```

---

## Supported Source Types

- **Plex**: Plex Media Server integration
- **Filesystem**: Local filesystem scanning
- **Jellyfin**: Jellyfin Media Server integration
- **Custom**: Third-party importer implementations

---

## Safety Guidelines

- Always use `--test-db` for testing enumeration logic
- Use `--dry-run` to preview enumeration results
- Verify registry state before enumeration
- Check source type availability after enumeration

---

## See Also

- [Source Add](SourceAddContract.md) - Creating sources with importer validation
- [Source Discover](SourceDiscoverContract.md) - Discovering collections using importers
- [Source Ingest](SourceIngestContract.md) - Ingesting content using importers
- [Unit of Work](UnitOfWorkContract.md) - Registry state management
