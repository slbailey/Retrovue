# Enricher List Types

## Purpose

Define the behavioral contract for listing all available enricher types from the registry. This contract ensures consistent discovery and display of available enricher implementations.

---

## Command Shape

```
retrovue enricher list-types [--json] [--test-db] [--dry-run]
```

### Optional Parameters

- `--json`: Output result in JSON format
- `--test-db`: Direct command to test database environment
- `--dry-run`: Show what would be listed without executing

---

## Safety Expectations

### Discovery Model

- **Non-destructive operation**: Only discovers and displays enricher types
- **Idempotent**: Safe to run multiple times
- **Dry-run support**: Preview discovery without external effects
- **Test isolation**: `--test-db` prevents external system calls

### Discovery Behavior

- Scans registry for available enricher types
- Validates enricher type compliance
- Reports scope information (ingest or playout)
- Displays configuration requirements

---

## Output Format

### Human-Readable Output

**Discovery Results:**

```
Available enricher types:
  ffprobe           - Video/audio analysis using FFprobe (ingest)
  metadata          - Metadata extraction and enrichment (ingest)
  playout-enricher  - Playout-scope enricher for channel processing (playout)

Total: 3 enricher types available
```

**Dry-run Output:**

```
Would list 3 enricher types from registry:
  • ffprobe - Video/audio analysis using FFprobe (ingest)
  • metadata - Metadata extraction and enrichment (ingest)
  • playout-enricher - Playout-scope enricher for channel processing (playout)
```

### JSON Output

```json
{
  "status": "ok",
  "enricher_types": [
    {
      "type": "ffprobe",
      "description": "Video/audio analysis using FFprobe",
      "scope": "ingest",
      "available": true
    },
    {
      "type": "metadata",
      "description": "Metadata extraction and enrichment",
      "scope": "ingest",
      "available": true
    },
    {
      "type": "playout-enricher",
      "description": "Playout-scope enricher for channel processing",
      "scope": "playout",
      "available": true
    }
  ],
  "total": 3
}
```

---

## Exit Codes

- `0`: Discovery completed successfully
- `1`: Discovery failed, validation error, or registry access error

---

## Data Effects

### Registry Changes

1. **Enricher Type Discovery**:

   - Registry scans for available enricher types
   - Validates enricher type compliance
   - Checks scope declarations
   - Updates internal registry state

2. **Scope Validation**:
   - Validates scope declarations (ingest or playout)
   - Reports scope information
   - Maintains scope-based filtering

### Side Effects

- Registry state queries (read-only)
- No external system calls or database modifications
- No filesystem changes

---

## Behavior Contract Rules (B-#)

- **B-1:** The command MUST scan registry for available enricher types and display all discovered types.
- **B-2:** The command MUST validate enricher type compliance and scope declarations.
- **B-3:** When `--json` is supplied, output MUST include fields `"status"`, `"enricher_types"`, and `"total"` with appropriate data structures.
- **B-4:** On discovery failure (registry access error), the command MUST exit with code `1` and print a human-readable error message.
- **B-5:** The `--dry-run` flag MUST show what would be discovered without executing external validation.
- **B-6:** Enricher type discovery MUST be deterministic - the same registry state MUST produce the same discovery results.
- **B-7:** The command MUST support both valid and invalid enricher types, reporting availability appropriately.
- **B-8:** Empty discovery results (no enricher types) MUST return exit code `0` with message "No enricher types available".

---

## Data Contract Rules (D-#)

- **D-1:** Registry MUST scan for available enricher types.
- **D-2:** Registry MUST validate enricher type compliance and scope declarations.
- **D-3:** Scope validation MUST be performed for each discovered enricher type.
- **D-4:** Enricher type discovery MUST NOT modify external systems or database tables.
- **D-5:** Registry state queries MUST be read-only during discovery.
- **D-6:** Enricher type availability MUST be validated against implementation status.
- **D-7:** Discovery operations MUST be atomic and consistent.
- **D-8:** Registry state MUST be maintained atomically during discovery process.

---

## Test Coverage Mapping

- `B-1..B-8` → `test_enricher_list_types_contract.py`
- `D-1..D-8` → `test_enricher_list_types_data_contract.py`

---

## Error Conditions

### Registry Errors

- Registry not initialized: "Error: Enricher registry not initialized"
- Discovery failure: "Error: Failed to discover enricher types from registry"
- Access error: "Error: Cannot access enricher registry"

### Validation Errors

- Invalid enricher type: "Error: Enricher type 'invalid' does not implement required interface"
- Missing scope: "Error: Enricher type 'ffprobe' missing scope declaration"
- Interface violation: "Error: Enricher type 'metadata' does not implement Enricher protocol"

---

## Examples

### Basic Discovery

```bash
# List all available enricher types
retrovue enricher list-types

# List with JSON output
retrovue enricher list-types --json

# Preview discovery without validation
retrovue enricher list-types --dry-run
```

### Test Environment Usage

```bash
# Test enricher type discovery in isolated environment
retrovue enricher list-types --test-db

# Test with mock enricher types
retrovue enricher list-types --test-db --json
```

### Error Scenarios

```bash
# Registry not initialized
retrovue enricher list-types
# Error: Enricher registry not initialized

# No enricher types available
retrovue enricher list-types
# No enricher types available
```

---

## Supported Enricher Types

- **ffprobe**: Video/audio analysis using FFprobe (ingest scope)
- **metadata**: Metadata extraction and enrichment (ingest scope)
- **playout-enricher**: Playout-scope enricher for channel processing (playout scope)
- **Custom**: Third-party enricher implementations

---

## Safety Guidelines

- Always use `--test-db` for testing discovery logic
- Use `--dry-run` to preview discovery results
- Verify registry state before discovery
- Check enricher type availability after discovery

---

## See Also

- [Enricher Add](EnricherAdd.md) - Creating enricher instances
- [Enricher List](EnricherList.md) - Listing configured enrichers
- [Enricher Update](EnricherUpdate.md) - Updating enricher configurations
- [Enricher Remove](EnricherRemove.md) - Removing enricher instances
