# Importer Contract

## Purpose

This document provides an overview of all Importer domain testing contracts. Individual Importer operations are covered by specific behavioral contracts that define exact CLI syntax, safety expectations, and data effects.

---

## Scope

The Importer domain is covered by the following specific contracts:

- **[Importer List](ImporterList.md)**: Listing all discovered importers
- **[Importer Show](ImporterShow.md)**: Displaying detailed importer information
- **[Importer Validate](ImporterValidate.md)**: Validating importer interface compliance
- **[Source List Types](SourceListTypes.md)**: Listing available source types from registry

---

## Contract Structure

Each Importer operation follows the standard contract pattern:

1. **Command Shape**: Exact CLI syntax and required flags
2. **Safety Expectations**: Discovery behavior, validation requirements, error handling
3. **Output Format**: Human-readable and JSON output structure
4. **Exit Codes**: Success and failure exit codes
5. **Data Effects**: What changes in the registry and filesystem
6. **Behavior Contract Rules (B-#)**: Operator-facing behavior guarantees
7. **Data Contract Rules (D-#)**: Registry, interface, and discovery guarantees
8. **Test Coverage Mapping**: Explicit mapping from rule IDs to test files

---

## Design Principles

- **Discovery-first**: Importers are discovered dynamically from filesystem
- **Interface compliance**: All importers must implement ImporterInterface correctly
- **No direct persistence**: Importers never write to authoritative database tables
- **Error propagation**: Importers raise typed errors, never silently fail
- **Test mode support**: All operations support `--dry-run` and `--test-db` modes

---

## Common Safety Patterns

All Importer contracts follow these safety patterns:

### Runtime Discovery

- Importers discovered from `adapters/importers/` directory
- Source type automatically derived from filename pattern
- Interface validation performed on discovery
- No external system dependencies during discovery

### Interface Validation

- All importers must implement `ImporterInterface` abstract base class
- Method signatures validated against interface requirements
- Source type mapping validated for uniqueness
- Registry maintains mapping from source types to importer implementations

### Error Handling

- Discovery failures handled gracefully with clear error messages
- Interface violations reported with specific method details
- External system errors propagated with diagnostic information
- Test mode prevents external API calls

---

## ImporterInterface Specification

All importers MUST implement the `ImporterInterface` abstract base class:

```python
class ImporterInterface(ABC):
    @abstractmethod
    def validate_ingestible(self, collection: SourceCollection) -> bool:
        """Validate whether a collection meets prerequisites for ingestion."""

    @abstractmethod
    def discover_collections(self, source_id: str) -> List[Dict[str, Any]]:
        """Discover collections from the external source."""

    @abstractmethod
    def ingest_collection(self, collection: SourceCollection, scope: Optional[str] = None) -> Dict[str, Any]:
        """Ingest content from a collection."""
```

### Method Responsibilities

- **validate_ingestible()**: Determines if a collection can be ingested based on importer-specific requirements
- **discover_collections()**: Enumerates available content libraries from external sources
- **ingest_collection()**: Extracts content metadata and returns normalized asset descriptions

### Configuration Schema

Importer-specific configuration is stored in the Source `config` field:

```json
{
  "servers": [{ "base_url": "https://plex.example.com", "token": "***" }],
  "enrichers": ["ffprobe", "metadata"]
}
```

---

## Contract Test Requirements

Each Importer contract must have exactly two test files:

1. **CLI Contract Test**: `tests/contracts/test_importer_{verb}_contract.py`

   - CLI syntax validation
   - Flag behavior verification
   - Output format validation
   - Error message handling

2. **Data Contract Test**: `tests/contracts/test_importer_{verb}_data_contract.py`
   - Registry state changes
   - Interface validation
   - Discovery behavior verification
   - Error propagation validation

---

## See Also

- [Importer Domain Documentation](../domain/Importer.md) - Core domain model and operations
- [Registry Domain Documentation](../domain/Registry.md) - Importer discovery and lifecycle management
- [Source Contracts](Source.md) - Source-level operations that use importers
- [CLI Contract](README.md) - General CLI command standards
