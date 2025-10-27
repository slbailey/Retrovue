# Importer Validate

## Purpose

Define the behavioral contract for validating importer interface compliance. This contract ensures thorough validation of importer implementations against the ImporterInterface requirements.

---

## Command Shape

```
retrovue importer validate <importer_name> [--json] [--test-db] [--dry-run]
```

### Required Parameters

- `importer_name`: Importer identifier (source type name)

### Optional Parameters

- `--json`: Output result in JSON format
- `--test-db`: Direct command to test database environment
- `--dry-run`: Show what would be validated without executing

---

## Safety Expectations

### Validation Model

- **Non-destructive operation**: Only validates importer implementation
- **Idempotent**: Safe to run multiple times
- **Dry-run support**: Preview validation without external effects
- **Test isolation**: `--test-db` prevents external system calls

### Validation Scope

- Interface implementation compliance
- Method signature validation
- Abstract method implementation
- Configuration schema validation

---

## Output Format

### Human-Readable Output

**Valid Importer:**

```
Importer: plex
Status: Valid ✓
Interface: ImporterInterface ✓
Methods: validate_ingestible ✓, discover_collections ✓, ingest_collection ✓
Configuration: Valid ✓
File Path: adapters/importers/plex_importer.py
```

**Invalid Importer:**

```
Importer: plex
Status: Invalid ✗
Interface: ImporterInterface ✗
Methods: validate_ingestible ✓, discover_collections ✗, ingest_collection ✗
Configuration: Invalid ✗
File Path: adapters/importers/plex_importer.py
Errors:
  - Missing method: discover_collections
  - Method signature mismatch: ingest_collection
  - Invalid configuration schema
```

### JSON Output

**Valid Importer:**

```json
{
  "status": "ok",
  "importer": {
    "name": "plex",
    "status": "valid",
    "interface_compliant": true,
    "file_path": "adapters/importers/plex_importer.py",
    "validation_results": {
      "interface": {
        "compliant": true,
        "errors": []
      },
      "methods": {
        "validate_ingestible": {
          "implemented": true,
          "signature_valid": true,
          "errors": []
        },
        "discover_collections": {
          "implemented": true,
          "signature_valid": true,
          "errors": []
        },
        "ingest_collection": {
          "implemented": true,
          "signature_valid": true,
          "errors": []
        }
      },
      "configuration": {
        "valid": true,
        "errors": []
      }
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
    "status": "invalid",
    "interface_compliant": false,
    "file_path": "adapters/importers/plex_importer.py",
    "validation_results": {
      "interface": {
        "compliant": false,
        "errors": ["Missing method: discover_collections"]
      },
      "methods": {
        "validate_ingestible": {
          "implemented": true,
          "signature_valid": true,
          "errors": []
        },
        "discover_collections": {
          "implemented": false,
          "signature_valid": false,
          "errors": ["Method not implemented"]
        },
        "ingest_collection": {
          "implemented": true,
          "signature_valid": false,
          "errors": ["Method signature mismatch"]
        }
      },
      "configuration": {
        "valid": false,
        "errors": ["Invalid configuration schema"]
      }
    }
  }
}
```

---

## Exit Codes

- `0`: Validation completed successfully (valid or invalid importer)
- `1`: Importer not found, validation error, or validation failure

---

## Data Effects

### Validation Process

1. **Importer Lookup**:

   - Registry searches for importer by source type
   - Validates importer file existence
   - Loads importer class for validation

2. **Interface Validation**:

   - Checks `ImporterInterface` implementation
   - Validates method signatures against interface
   - Reports detailed compliance status

3. **Configuration Validation**:
   - Validates configuration schema
   - Checks parameter requirements
   - Reports configuration compliance

### Side Effects

- Python module loading for interface validation
- Registry state queries (read-only)
- No external system calls or database modifications

---

## Behavior Contract Rules (B-#)

- **B-1:** The command MUST verify that the importer implements `ImporterInterface` correctly and report any violations.
- **B-2:** The command MUST validate importer existence before attempting validation.
- **B-3:** When `--json` is supplied, output MUST include fields `"status"`, `"importer"`, and detailed validation results.
- **B-4:** On validation failure (importer not found), the command MUST exit with code `1` and print "Error: Importer 'X' not found".
- **B-5:** The `--dry-run` flag MUST show what would be validated without executing external validation.
- **B-6:** Interface compliance MUST be reported with specific method details and signature validation.
- **B-7:** Configuration validation MUST be performed and reported.
- **B-8:** Validation results MUST be comprehensive and actionable.

---

## Data Contract Rules (D-#)

- **D-1:** Registry MUST validate importer existence before attempting validation.
- **D-2:** Registry MUST validate `ImporterInterface` implementation for the specified importer.
- **D-3:** Method signature validation MUST be performed against interface requirements.
- **D-4:** Configuration schema validation MUST be performed.
- **D-5:** Validation operations MUST NOT modify external systems or database tables.
- **D-6:** Registry state queries MUST be read-only during validation.
- **D-7:** Importer class loading MUST be performed safely with error handling.
- **D-8:** Validation results MUST be accurate and detailed.

---

## Test Coverage Mapping

- `B-1..B-8` → `test_importer_validate_contract.py`
- `D-1..D-8` → `test_importer_validate_data_contract.py`

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

### Configuration Errors

- Invalid schema: "Error: Invalid configuration schema for importer 'plex'"
- Missing parameters: "Error: Required configuration parameter 'servers' missing"

---

## Examples

### Basic Validation

```bash
# Validate importer interface compliance
retrovue importer validate plex

# Validate with JSON output
retrovue importer validate plex --json

# Preview validation without execution
retrovue importer validate plex --dry-run
```

### Test Environment Usage

```bash
# Test importer validation in isolated environment
retrovue importer validate plex --test-db

# Test with mock importer files
retrovue importer validate plex --test-db --json
```

### Error Scenarios

```bash
# Importer not found
retrovue importer validate invalid
# Error: Importer 'invalid' not found

# Invalid importer
retrovue importer validate plex
# Shows detailed validation errors for interface violations
```

---

## Supported Importer Types

- **Plex**: Plex Media Server integration
- **Filesystem**: Local filesystem scanning
- **Jellyfin**: Jellyfin Media Server integration
- **Custom**: Third-party importer implementations

---

## Safety Guidelines

- Always use `--test-db` for testing validation logic
- Use `--dry-run` to preview validation results
- Verify importer existence before validation
- Check interface compliance after validation

---

## See Also

- [Importer List](ImporterList.md) - List all discovered importers
- [Importer Show](ImporterShow.md) - Detailed importer information
- [Source List Types](SourceListTypes.md) - Source type enumeration
- [Unit of Work](UnitOfWork.md) - Registry state management
