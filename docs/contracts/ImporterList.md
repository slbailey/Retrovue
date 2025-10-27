# Importer List

## Purpose

Define the behavioral contract for listing all discovered importers from the filesystem. This contract ensures consistent discovery and display of available importer implementations.

---

## Command Shape

```
retrovue importer list [--json] [--test-db] [--dry-run]
```

### Optional Parameters

- `--json`: Output result in JSON format
- `--test-db`: Direct command to test database environment
- `--dry-run`: Show what would be discovered without executing

---

## Safety Expectations

### Discovery Model

- **Non-destructive operation**: Only discovers and displays importers
- **Idempotent**: Safe to run multiple times
- **Dry-run support**: Preview discovery without external effects
- **Test isolation**: `--test-db` prevents external system calls

### Discovery Behavior

- Scans `adapters/importers/` directory for `*_importer.py` files
- Validates filename pattern compliance
- Checks interface implementation
- Reports discovery status for each importer

---

## Output Format

### Human-Readable Output

**Discovery Results:**

```
Available Importers:
  plex        - Plex Media Server
  filesystem  - Local Filesystem
  jellyfin    - Jellyfin Media Server

Total: 3 importers discovered
```

**Dry-run Output:**

```
Would discover 3 importers from adapters/importers/:
  • plex_importer.py - Plex Media Server
  • filesystem_importer.py - Local Filesystem
  • jellyfin_importer.py - Jellyfin Media Server
```

### JSON Output

```json
{
  "status": "ok",
  "importers": [
    {
      "name": "plex",
      "display_name": "Plex Media Server",
      "source_type": "plex",
      "status": "valid",
      "file_path": "adapters/importers/plex_importer.py"
    },
    {
      "name": "filesystem",
      "display_name": "Local Filesystem",
      "source_type": "filesystem",
      "status": "valid",
      "file_path": "adapters/importers/filesystem_importer.py"
    },
    {
      "name": "jellyfin",
      "display_name": "Jellyfin Media Server",
      "source_type": "jellyfin",
      "status": "valid",
      "file_path": "adapters/importers/jellyfin_importer.py"
    }
  ],
  "total": 3
}
```

---

## Exit Codes

- `0`: Discovery completed successfully
- `1`: Discovery failed, validation error, or filesystem access error

---

## Data Effects

### Registry Changes

1. **Importer Discovery**:

   - Registry scans `adapters/importers/` directory
   - Validates filename pattern `{source_type}_importer.py`
   - Checks interface implementation compliance
   - Updates internal registry state

2. **Source Type Mapping**:
   - Source type derived from filename pattern
   - Mapping validated for uniqueness
   - Registry maintains importer-to-source-type mapping

### Side Effects

- Filesystem scanning of importer directory
- Python module loading for interface validation
- Registry state updates (in-memory only)

---

## Behavior Contract Rules (B-#)

- **B-1:** The command MUST scan `adapters/importers/` directory for `*_importer.py` files and display all discovered importers.
- **B-2:** The command MUST validate filename pattern compliance (`{source_type}_importer.py`).
- **B-3:** When `--json` is supplied, output MUST include fields `"status"`, `"importers"`, and `"total"` with appropriate data structures.
- **B-4:** On discovery failure (filesystem access error), the command MUST exit with code `1` and print a human-readable error message.
- **B-5:** The `--dry-run` flag MUST show what would be discovered without executing external validation.
- **B-6:** Importer discovery MUST be deterministic - the same filesystem state MUST produce the same discovery results.
- **B-7:** The command MUST support both valid and invalid importer files, reporting status appropriately.
- **B-8:** Empty discovery results (no importer files) MUST return exit code `0` with message "No importers found in adapters/importers/".

---

## Data Contract Rules (D-#)

- **D-1:** Registry MUST scan `adapters/importers/` directory for `*_importer.py` files.
- **D-2:** Registry MUST validate filename pattern `{source_type}_importer.py` for each discovered file.
- **D-3:** Registry MUST validate that each discovered importer implements `ImporterInterface`.
- **D-4:** Source type mapping MUST be derived automatically from importer filenames.
- **D-5:** Multiple importers claiming the same source type MUST cause registration failure with clear error message.
- **D-6:** Registry MUST maintain mapping from source types to importer implementations.
- **D-7:** Discovery operations MUST NOT modify external systems or database tables.
- **D-8:** Registry state MUST be updated atomically during discovery process.

---

## Test Coverage Mapping

- `B-1..B-8` → `test_importer_list_contract.py`
- `D-1..D-8` → `test_importer_list_data_contract.py`

---

## Error Conditions

### Discovery Errors

- Filesystem access error: "Error: Cannot access adapters/importers/ directory"
- Invalid filename pattern: "Error: Importer file 'plex.py' does not follow naming pattern '\*\_importer.py'"
- Interface violation: "Error: Importer 'plex' does not implement required interface methods"

### Validation Errors

- Class loading failure: "Error: Failed to load importer class from plex_importer.py"
- Method signature mismatch: "Error: validate_ingestible() method signature does not match interface"
- Multiple source types: "Error: Multiple importers claim source type 'plex': plex_importer.py, plex_v2_importer.py"

---

## Examples

### Basic Discovery

```bash
# List all discovered importers
retrovue importer list

# List with JSON output
retrovue importer list --json

# Preview discovery without validation
retrovue importer list --dry-run
```

### Test Environment Usage

```bash
# Test discovery in isolated environment
retrovue importer list --test-db

# Test with mock importer files
retrovue importer list --test-db --json
```

### Error Scenarios

```bash
# Directory not found
retrovue importer list
# Error: Cannot access adapters/importers/ directory

# No importers found
retrovue importer list
# No importers found in adapters/importers/
```

---

## Supported Importer Types

- **Plex**: Plex Media Server integration
- **Filesystem**: Local filesystem scanning
- **Jellyfin**: Jellyfin Media Server integration
- **Custom**: Third-party importer implementations

---

## Safety Guidelines

- Always use `--test-db` for testing discovery logic
- Use `--dry-run` to preview discovery results
- Verify importer directory structure before discovery
- Check interface compliance after discovery

---

## See Also

- [Importer Show](ImporterShow.md) - Detailed importer information
- [Importer Validate](ImporterValidate.md) - Interface validation
- [Source List Types](SourceListTypes.md) - Source type enumeration
- [Unit of Work](UnitOfWork.md) - Registry state management
