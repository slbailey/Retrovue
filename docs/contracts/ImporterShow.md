# Importer Show

## Purpose

Define the behavioral contract for displaying detailed information about a specific importer. This contract ensures comprehensive importer inspection with interface compliance reporting.

---

## Command Shape

```
retrovue importer show <importer_name> [--json] [--test-db] [--dry-run]
```

### Required Parameters

- `importer_name`: Importer identifier (source type name)

### Optional Parameters

- `--json`: Output result in JSON format
- `--test-db`: Direct command to test database environment
- `--dry-run`: Show what would be displayed without executing

---

## Safety Expectations

### Inspection Model

- **Non-destructive operation**: Only displays importer information
- **Idempotent**: Safe to run multiple times
- **Dry-run support**: Preview display without external effects
- **Test isolation**: `--test-db` prevents external system calls

### Information Display

- Importer metadata and configuration requirements
- Interface compliance status
- Method signature validation
- Source type mapping information

---

## Output Format

### Human-Readable Output

**Valid Importer:**

```
Importer: plex
Display Name: Plex Media Server
Source Type: plex
Status: Valid
Interface: ImporterInterface ✓
Methods: validate_ingestible ✓, discover_collections ✓, ingest_collection ✓
File Path: adapters/importers/plex_importer.py
Configuration Schema:
  - servers: List of server configurations
  - enrichers: List of enricher types
```

**Invalid Importer:**

```
Importer: plex
Display Name: Plex Media Server
Source Type: plex
Status: Invalid
Interface: ImporterInterface ✗
Methods: validate_ingestible ✓, discover_collections ✗, ingest_collection ✓
File Path: adapters/importers/plex_importer.py
Errors:
  - Missing method: discover_collections
  - Method signature mismatch: ingest_collection
```

### JSON Output

**Valid Importer:**

```json
{
  "status": "ok",
  "importer": {
    "name": "plex",
    "display_name": "Plex Media Server",
    "source_type": "plex",
    "status": "valid",
    "interface_compliant": true,
    "file_path": "adapters/importers/plex_importer.py",
    "methods": {
      "validate_ingestible": {
        "implemented": true,
        "signature_valid": true
      },
      "discover_collections": {
        "implemented": true,
        "signature_valid": true
      },
      "ingest_collection": {
        "implemented": true,
        "signature_valid": true
      }
    },
    "configuration_schema": {
      "servers": "List of server configurations",
      "enrichers": "List of enricher types"
    }
  }
}
```

**Invalid Importer:**

```json
{
  "status": "error",
  "importer": {
    "name": "plex",
    "display_name": "Plex Media Server",
    "source_type": "plex",
    "status": "invalid",
    "interface_compliant": false,
    "file_path": "adapters/importers/plex_importer.py",
    "methods": {
      "validate_ingestible": {
        "implemented": true,
        "signature_valid": true
      },
      "discover_collections": {
        "implemented": false,
        "signature_valid": false
      },
      "ingest_collection": {
        "implemented": true,
        "signature_valid": false
      }
    },
    "errors": [
      "Missing method: discover_collections",
      "Method signature mismatch: ingest_collection"
    ]
  }
}
```

---

## Exit Codes

- `0`: Importer information displayed successfully
- `1`: Importer not found, validation error, or display failure

---

## Data Effects

### Registry Inspection

1. **Importer Lookup**:

   - Registry searches for importer by source type
   - Validates importer file existence
   - Loads importer class for inspection

2. **Interface Validation**:
   - Checks `ImporterInterface` implementation
   - Validates method signatures
   - Reports compliance status

### Side Effects

- Python module loading for interface inspection
- Registry state queries (read-only)
- No external system calls or database modifications

---

## Behavior Contract Rules (B-#)

- **B-1:** The command MUST display detailed information about the specified importer, including interface compliance status.
- **B-2:** The command MUST validate importer existence before attempting display.
- **B-3:** When `--json` is supplied, output MUST include fields `"status"`, `"importer"`, and detailed method information.
- **B-4:** On validation failure (importer not found), the command MUST exit with code `1` and print "Error: Importer 'X' not found".
- **B-5:** The `--dry-run` flag MUST show what would be displayed without executing external validation.
- **B-6:** Interface compliance MUST be reported with specific method details and signature validation.
- **B-7:** The command MUST display configuration schema requirements for the importer.
- **B-8:** Invalid importers MUST be displayed with detailed error information.

---

## Data Contract Rules (D-#)

- **D-1:** Registry MUST validate importer existence before attempting display.
- **D-2:** Registry MUST validate `ImporterInterface` implementation for the specified importer.
- **D-3:** Method signature validation MUST be performed against interface requirements.
- **D-4:** Configuration schema MUST be extracted from importer implementation.
- **D-5:** Display operations MUST NOT modify external systems or database tables.
- **D-6:** Registry state queries MUST be read-only during inspection.
- **D-7:** Importer class loading MUST be performed safely with error handling.
- **D-8:** Interface compliance reporting MUST be accurate and detailed.

---

## Test Coverage Mapping

- `B-1..B-8` → `test_importer_show_contract.py`
- `D-1..D-8` → `test_importer_show_data_contract.py`

---

## Error Conditions

### Validation Errors

- Importer not found: "Error: Importer 'invalid' not found"
- File not found: "Error: Importer file 'plex_importer.py' not found"
- Class loading failure: "Error: Failed to load importer class from plex_importer.py"

### Interface Errors

- Missing methods: "Error: Importer 'plex' missing required method 'discover_collections'"
- Signature mismatch: "Error: Method 'ingest_collection' signature does not match interface"
- Interface violation: "Error: Importer 'plex' does not implement ImporterInterface"

---

## Examples

### Basic Display

```bash
# Show detailed importer information
retrovue importer show plex

# Show with JSON output
retrovue importer show plex --json

# Preview display without validation
retrovue importer show plex --dry-run
```

### Test Environment Usage

```bash
# Test importer inspection in isolated environment
retrovue importer show plex --test-db

# Test with mock importer files
retrovue importer show plex --test-db --json
```

### Error Scenarios

```bash
# Importer not found
retrovue importer show invalid
# Error: Importer 'invalid' not found

# Invalid importer
retrovue importer show plex
# Shows detailed error information for interface violations
```

---

## Supported Importer Types

- **Plex**: Plex Media Server integration
- **Filesystem**: Local filesystem scanning
- **Jellyfin**: Jellyfin Media Server integration
- **Custom**: Third-party importer implementations

---

## Safety Guidelines

- Always use `--test-db` for testing inspection logic
- Use `--dry-run` to preview display results
- Verify importer existence before inspection
- Check interface compliance after inspection

---

## See Also

- [Importer List](ImporterList.md) - List all discovered importers
- [Importer Validate](ImporterValidate.md) - Interface validation
- [Source List Types](SourceListTypes.md) - Source type enumeration
- [Unit of Work](UnitOfWork.md) - Registry state management
