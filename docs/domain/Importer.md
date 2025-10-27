_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Contracts](../contracts/README.md) • [Registry](Registry.md) • [Source](Source.md) • [Collection](Collection.md)_

# Domain — Importer

## Purpose

Importer defines the conceptual domain for content discovery and ingestion from external media systems. Importers bridge the gap between external content sources (Plex, filesystem, etc.) and RetroVue's internal content management system by implementing standardized discovery, validation, and ingestion operations.

Importers are **modular and extensible** - they can be developed by third parties without modifying core RetroVue code. The [Registry](Registry.md) domain manages importer discovery, registration, and lifecycle.

### Importer vs Source

An **Importer** is code. A **Source** is a configured instance of that Importer type (with credentials, base URLs, etc.) stored in the database and referenced by `source_id`. Operators interact with Sources through `retrovue source ....` Importers are never configured directly; they are discovered at runtime by the Registry.

## Core model / scope

Importer is implemented as an abstract interface (`ImporterInterface`) that defines the contract for all content importers. Each importer type (Plex, filesystem, etc.) implements this interface with source-specific logic for:

- **Collection Discovery**: Enumerating content libraries from external sources
- **Prerequisites Validation**: Verifying that collections can be ingested
- **Content Ingestion**: Extracting metadata and producing normalized asset descriptions that become Asset records

The interface ensures consistent behavior across all importer types while allowing source-specific implementations.

## Contract / interface

### ImporterInterface

At the domain level, an Importer is defined by its ability to:

- verify a collection can be ingested,
- enumerate available collections,
- and drive ingestion of a collection (full or partial).

Orchestration may call these behaviors at different granularities. For the developer-facing method signatures and CLI wiring (including `param_spec()`, filtering by title/season/episode, etc.), see the [Importer Development Guide](../developer/Importer.md).

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

**Note:** RetroVue orchestration may call importer behavior at two granularities: discovery / asset fetch (per collection, per title/season/episode), and full ingest execution of that collection. For clarity, `ImporterInterface` here reflects the semantic responsibilities at the domain level. For method signatures and CLI-driven calling patterns, see [Importer Development Guide](../developer/Importer.md).

### Prerequisites Validation

The `validate_ingestible()` method determines whether a collection can be ingested based on importer-specific requirements:

- **Plex Importer**: Validates that path mappings exist and are resolvable
- **Filesystem Importer**: Validates that directory paths exist and are accessible
- **Future Importers**: Will implement their own prerequisite validation logic

### Collection Discovery

The `discover_collections()` method enumerates available content libraries from external sources:

- **Plex Importer**: Queries Plex API for available libraries
- **Filesystem Importer**: Scans directory structure for content collections
- **Future Importers**: Will implement their own discovery mechanisms

### Content Ingestion

The `ingest_collection()` method extracts content metadata and returns canonicalized asset descriptions to the ingest service. The ingest service is responsible for creating Asset records in the database inside a Unit of Work. Newly ingested assets MUST enter the system in a known lifecycle state (e.g. `new`, `enriching`). Importers MUST NOT persist directly to authoritative tables.

- **Scope Support**: Handles full collection, title, season, or episode-level ingestion
- **Metadata Extraction**: Extracts title, season, episode, duration, and file information
- **Asset Normalization**: Returns canonicalized asset descriptions in RetroVue's unified format
- **Duplicate Prevention**: Implements duplicate detection logic

**Important:** The importer DOES NOT directly persist to authoritative tables. The importer returns discovered/normalized assets. The ingest service, running under a Unit of Work, is what commits the data to the database.

## Contract-driven behavior

All importer operations are defined by behavioral contracts that specify exact CLI syntax, safety expectations, output formats, and data effects. The contracts ensure:

- **Safety first**: No destructive operations run against live data during automated tests
- **Atomicity**: All operations wrapped in Unit of Work for consistency
- **Idempotence**: Operations can be safely repeated without side effects
- **Audit trails**: All operations tracked for debugging and compliance

### Key Contract Requirements

- **Prerequisites Validation**: `ingestible` field MUST be validated before any ingest operation
- **Collection Discovery**: New collections MUST be created with `sync_enabled=false`
- **Asset Normalization**: Importers MUST return canonicalized asset descriptions, not persist directly
- **Error Handling**: Per-asset failures MUST NOT abort the entire ingest operation. Importers MUST raise typed errors for asset-level failures; orchestration is responsible for catching, logging, and continuing

## Implementation patterns

### Modular Architecture

Importers are developed as independent files in the `adapters/importers/` directory:

```
adapters/importers/
├── plex_importer.py        # Source type: "plex"
├── filesystem_importer.py  # Source type: "filesystem"
├── jellyfin_importer.py   # Source type: "jellyfin"
└── custom_importer.py     # Source type: "custom"
```

### Importer Naming Convention

Each importer file MUST follow the naming pattern `{source_type}_importer.py`:

- **`plex_importer.py`** → Source type: `"plex"`, Class: `PlexImporter`
- **`filesystem_importer.py`** → Source type: `"filesystem"`, Class: `FilesystemImporter`
- **`jellyfin_importer.py`** → Source type: `"jellyfin"`, Class: `JellyfinImporter`
- **`custom_importer.py`** → Source type: `"custom"`, Class: `CustomImporter`

### Registry Integration

Importers are managed by the Registry domain:

- **Runtime Discovery**: Registry scans `adapters/importers/` directory for `*_importer.py` files
- **Source Type Mapping**: Source type automatically derived from filename
- **Dynamic Loading**: Importers loaded on-demand when needed
- **Interface Validation**: Registry validates `ImporterInterface` implementation

### Configuration Management

Importer-specific configuration is stored in the Source `config` field:

```json
{
  "servers": [{ "base_url": "https://plex.example.com", "token": "***" }],
  "enrichers": ["ffprobe", "metadata"]
}
```

## Operator workflows

### Source Management

- **Add source**: `retrovue source add --type plex --name "My Plex Server" --discover`
- **Discover collections**: `retrovue source discover "My Plex Server"`
- **Validate prerequisites**: `retrovue collection show "TV Shows"` (shows `ingestible` status)

The list of valid `--type` values is provided at runtime by the Importer registry and surfaced to operators via `retrovue source list-types`.

### Collection Operations

- **Bulk ingest**: `retrovue source ingest "My Plex Server"` (processes all `sync_enabled=true` AND `ingestible=true` collections)
- **Targeted ingest**: `retrovue collection ingest "TV Shows" --title "The Simpsons" --season 1`

### Prerequisites Validation

- **Check ingestibility**: `retrovue collection show <collection_id>` shows `ingestible` field
- **Validate path mappings**: Plex importer validates that `plex_path` → `local_path` mappings are resolvable
- **Test connectivity**: Importers validate external system accessibility

## Key execution patterns

### Discovery Workflow

1. **Importer Discovery**: Registry scans `adapters/importers/` directory for `*_importer.py` files
2. **Source Creation**: Source created with `type` field
3. **Importer Selection**: Registry provides importer based on source type
4. **Collection Discovery**: `discover_collections()` called to enumerate libraries
5. **Prerequisites Validation**: `validate_ingestible()` called for each collection
6. **Collection Persistence**: Collections created with `sync_enabled=false`, `ingestible=<validation_result>`

### Ingest Workflow

1. **Collection Selection**: Collections filtered by `sync_enabled=true` AND `ingestible=true`
2. **Prerequisites Revalidation**: `validate_ingestible()` called before ingest
3. **Content Extraction**: `ingest_collection()` called with appropriate scope
4. **Asset Creation**: The ingest service writes Assets into the database in `new` or `enriching` state, using the normalized data returned by the importer
5. **Audit Logging**: Ingest results tracked for debugging and compliance

### Error Handling

- **Per-asset failures**: Individual asset failures do not abort collection ingest
- **Collection failures**: Individual collection failures do not abort source ingest
- **Fatal errors**: Fatal errors (database constraints, external system unreachable) abort entire operation
- **Transaction rollback**: All operations wrapped in Unit of Work for atomicity

## Business rules

### Importer Lifecycle

- **Discovery**: Importers discovered at runtime from filesystem
- **Validation**: All importers MUST implement `ImporterInterface`
- **Configuration**: Each importer declares its configuration requirements
- **Availability**: Importers immediately available when files exist

### Source Type Mapping

- **Automatic Derivation**: Source type derived from filename pattern
- **Unique Mapping**: Each source type maps to exactly one importer
- **Conflict Resolution**: Multiple importers claiming same source type cause registration failure

### Content Processing

- **Normalization**: All content normalized into RetroVue's unified model
- **Stable Identification**: External IDs preserved for incremental operations
- **Metadata Extraction**: Title, season, episode, duration extracted consistently
- **Duplicate Prevention**: Duplicate detection prevents redundant processing
- **No Direct Persistence**: Importers return normalized data; ingest service handles persistence

### Safety and Isolation

- **Test Mode Support**: All operations support `--dry-run` and `--test-db` modes
- **Non-Destructive Discovery**: Discovery operations never mutate external systems
- **Error Isolation**: Per-asset failures isolated from bulk operations
- **Transaction Boundaries**: All persistence within controlled Unit of Work
- **Importer as Infrastructure**: Importers are infrastructure components; ingest service owns persistence authority

## Cross-references

- **[Registry Domain](Registry.md)** - Importer discovery, registration, and lifecycle management
- **[Source Contracts](../contracts/Source.md)** - Source-level operations that use importers
- **[Collection Contracts](../contracts/Collection.md)** - Collection-level operations that use importers
- **[Unit of Work](../contracts/UnitOfWork.md)** - Transaction management for importer operations
- **[CLI Contract](../contracts/README.md)** - General CLI command standards
- **[Source Domain](Source.md)** - Source entity model and relationships
- **[Collection Domain](Collection.md)** - Collection entity model and relationships
- **[Developer Guide](../developer/Importer.md)** - Implementation details and development guide

## Contract test requirements

All importer operations MUST have comprehensive test coverage following the contract test responsibilities in [README.md](../contracts/README.md). Tests MUST:

- **Validate prerequisites**: Test `validate_ingestible()` for each importer type
- **Test discovery**: Verify `discover_collections()` returns expected results
- **Test ingestion**: Verify `ingest_collection()` returns normalized asset data that results in correct Asset records being created by the ingest service
- **Test error handling**: Verify graceful handling of external system failures
- **Test atomicity**: Verify Unit of Work behavior for all operations
- **Test idempotence**: Verify operations can be safely repeated

Each test MUST reference specific contract rule IDs to provide bidirectional traceability between contracts and implementation.
