# Source List Types

## Purpose

Define the behavioral contract for listing available source types from the importer registry. This contract ensures consistent enumeration of source types derived from discovered importer implementations.

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
- **Dry-run support**: Preview enumeration without external effects
- **Test isolation**: `--test-db` prevents external system calls

### Source Type Derivation

- Source types derived from importer filenames
- Registry maintains mapping from source types to importers
- Validation of source type uniqueness
- Reporting of source type availability

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
      "available": true
    },
    {
      "name": "filesystem",
      "importer_file": "filesystem_importer.py",
      "display_name": "Local Filesystem",
      "available": true
    },
    {
      "name": "jellyfin",
      "importer_file": "jellyfin_importer.py",
      "display_name": "Jellyfin Media Server",
      "available": true
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

   - Registry scans discovered importers
   - Extracts source types from importer filenames
   - Validates source type uniqueness

2. **Mapping Validation**:
   - Verifies source type to importer mapping
   - Reports availability status
   - Maintains registry state consistency

### Side Effects

- Registry state queries (read-only)
- No external system calls or database modifications
- No filesystem changes

---

## Behavior Contract Rules (B-#)

- **B-1:** The command MUST return source types derived from discovered importer filenames.
- **B-2:** The command MUST validate source type uniqueness before reporting.
- **B-3:** When `--json` is supplied, output MUST include fields `"status"`, `"source_types"`, and `"total"` with appropriate data structures.
- **B-4:** On enumeration failure (registry error), the command MUST exit with code `1` and print a human-readable error message.
- **B-5:** The `--dry-run` flag MUST show what would be listed without executing external validation.
- **B-6:** Source type enumeration MUST be deterministic - the same registry state MUST produce the same enumeration results.
- **B-7:** The command MUST support both valid and invalid importer files, reporting availability appropriately.
- **B-8:** Empty enumeration results (no source types) MUST return exit code `0` with message "No source types available".

---

## Data Contract Rules (D-#)

- **D-1:** Registry MUST maintain mapping from source types to importer implementations.
- **D-2:** Source type mapping MUST be derived automatically from importer filenames.
- **D-3:** Multiple importers claiming the same source type MUST cause registration failure with clear error message.
- **D-4:** Source type enumeration MUST NOT modify external systems or database tables.
- **D-5:** Registry state queries MUST be read-only during enumeration.
- **D-6:** Source type availability MUST be validated against importer implementation status.
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
- Invalid filename pattern: "Error: Importer file 'plex.py' does not follow naming pattern"
- Interface violation: "Error: Importer 'plex' does not implement required interface"

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

- [Importer List](ImporterList.md) - List all discovered importers
- [Importer Show](ImporterShow.md) - Detailed importer information
- [Importer Validate](ImporterValidate.md) - Interface validation
- [Unit of Work](UnitOfWork.md) - Registry state management
