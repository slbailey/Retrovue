# Domain — Asset

Related: [Collection](Collection.md) • [Source](Source.md) • [Scheduling](Scheduling.md) • [Ingest Pipeline](IngestPipeline.md) • [Contracts](../contracts/README.md)

## Purpose

Asset represents the leaf unit of broadcastable content in RetroVue. Each asset belongs to exactly one collection and progresses through a lifecycle state machine indicating its readiness for scheduling and playout. Assets are the single source of truth for all broadcastable content, whether just ingested or fully processed and ready for broadcast. Assets form the atomic building blocks of RetroVue's content model, serving as the bridge between ingestion, enrichment, and broadcast domains.

## Core model / scope

### Primary key / identity fields

- **uuid** (UUID, primary key): Stable identifier that serves as the spine connecting all other tables that reference assets

### Required fields

- **uri** (Text, required, unique): File system path or URI to the media file
- **size** (BigInteger, required): File size in bytes
- **state** (String(20), required): Lifecycle state (`new`, `enriching`, `ready`, `retired`)
- **canonical** (Boolean, required, default=False): Operator-verified content ready for scheduling (distinct from `approved_for_broadcast`, which is the runtime gating flag)

### Lifecycle / state fields

- **collection_uuid** (UUID, foreign key): Reference to the SourceCollection this asset belongs to
- **approved_for_broadcast** (Boolean, required, default=False): Asset approval status for broadcast (must be true when state='ready')
- **discovered_at** (DateTime(timezone=True), required): When the asset was first discovered during ingest
- **is_deleted** (Boolean, required, default=False): Soft delete flag for content lifecycle management
- **deleted_at** (DateTime(timezone=True), nullable): When the asset was soft deleted

### Technical metadata fields

- **duration_ms** (Integer, nullable): Asset duration in milliseconds
- **video_codec** (String(50), nullable): Video codec information
- **audio_codec** (String(50), nullable): Audio codec information
- **container** (String(50), nullable): Container format
- **hash_sha256** (String(64), nullable): SHA256 hash for content integrity and change detection

### Relationships

Asset has relationships with:

- **SourceCollection** (via `collection_uuid` foreign key): The collection this asset belongs to
- **ProviderRef**: External system references (Plex rating keys, etc.)
- **Marker**: Chapters, availability windows, and other asset markers
- **ReviewQueue**: Items requiring human review for quality assurance
- **Episode**: Many-to-many relationship through `episode_assets` junction table (for TV show content)

### Indexes

Asset table includes indexes on:

- `canonical` (for efficient filtering of approved assets)
- `discovered_at` (for chronological queries)
- `is_deleted` (for soft delete filtering)
- `state` (for lifecycle state queries)
- `approved_for_broadcast` (for broadcast eligibility queries)
- `collection_uuid` (for collection-based queries)

## Contract / interface

### Lifecycle states

Asset represents content that progresses through a lifecycle state machine:

1. **`new`**: Recently discovered during ingest, minimal metadata, not yet processed
2. **`enriching`**: Being processed by enrichers to add metadata and enhance content
3. **`ready`**: Fully processed, approved for broadcast, eligible for scheduling and playout
4. **`retired`**: No longer available or approved for broadcast

### Critical invariants

- **An asset in `ready` state MUST have `approved_for_broadcast=true`**
- **An asset with `approved_for_broadcast=true` MUST be in `ready` state**
- **Scheduling and playout ONLY operate on assets in state `ready` with `approved_for_broadcast=true`**
- **Newly ingested assets MUST enter the system in `new` or `enriching` state, NEVER `ready`**
- **Assets MUST belong to exactly one collection via `collection_uuid`**

### Allowed lifecycle transitions

Assets progress through the lifecycle as follows:

1. **Discovery**: Asset discovered during collection ingest (`state=new`)
2. **Enrichment**: Enrichers process metadata and enhance content (`state=enriching`)
3. **Approval**: Asset marked `state=ready` and `approved_for_broadcast=true` when fully processed
4. **Broadcast**: Ready assets are eligible for scheduling and playout
5. **Retirement**: Assets can be marked `state=retired` when no longer available

### Duplicate / change detection behavior

Assets within a collection are identified by canonical identity for duplicate detection:

- **Canonical Identity**: Determined by importer-specific logic (typically `external_id + collection_id` or `file_path + collection_id`)
- **Uniqueness**: Only one Asset record per canonical identity within a collection
- **Update Detection**: Existing assets are identified and re-processed if content or enricher configuration has changed

**Content Change Detection**:

- `hash_sha256` field tracks content signature
- System compares current content hash with stored hash
- Changed assets are re-processed, resetting state to `new` or `enriching`

**Enricher Change Detection**:

- System tracks which enrichers were active when asset was last ingested
- System compares current enricher configuration with configuration active at last ingest
- Assets are re-processed when enrichers change, resetting state to `new` or `enriching`

## Contract-driven behavior

### How CLI noun-verb pairs map to Asset operations

The Asset domain is covered by the following operations:

- **Asset Select**: `retrovue assets select` - Select assets by various criteria (UUID, title, series, genre, etc.)
- **Asset Delete**: `retrovue assets delete` - Delete assets (soft or hard delete)
- **Asset Restore**: `retrovue assets restore` - Restore soft-deleted assets
- **Asset Show** (planned): Display detailed asset information
- **Asset List** (planned): List assets with filtering options
- **Asset Update** (planned): Update asset metadata and configuration

### Safety expectations

All Asset operations are defined by behavioral contracts that specify exact CLI syntax, safety expectations, output formats, and data effects:

- **Safety first**: No destructive operations run against live data during automated tests
- **One contract per noun-verb pair**: Each Asset operation has its own focused contract
- **Test isolation**: All operations support `--test-db` for isolated testing
- **Idempotent operations**: Asset operations are safely repeatable
- **Clear error handling**: Failed operations provide clear diagnostic information
- **Unit of Work**: All database-modifying operations MUST be wrapped in atomic transactions

### Testability expectations

- Contract-driven testing ensures behavioral consistency
- Clear error messages and diagnostic information

### Idempotence / transaction boundaries

- Asset operations are safely repeatable
- All database-modifying operations MUST be wrapped in atomic transactions
- Transaction rollback occurs on any fatal error, ensuring no partial state changes

## Execution model

### How Assets flow through ingest → enrichment → approval → scheduling → playout

Assets are the source of all scheduled content - no content can be scheduled that is not in `ready` state with `approved_for_broadcast=true`. The flow is:

1. **Ingest Pipeline**: Importers enumerate assets from external sources (Plex, filesystem, etc.)
2. **Normalization**: Importers return normalized asset descriptions
3. **Persistence**: Ingest service creates Asset records in `new` or `enriching` state
4. **Duplicate Detection**: System checks canonical identity to prevent duplicates
5. **Change Detection**: System identifies existing assets and re-processes if needed
6. **Enrichment**: Enrichers attach metadata, validate content, enhance descriptions
7. **State Progression**: Assets move from `new` → `enriching` → `ready`
8. **Approval**: Fully processed assets are marked `approved_for_broadcast=true`
9. **Scheduling**: ScheduleService queries for `state='ready'` AND `approved_for_broadcast=true`
10. **Playout**: Scheduled assets become PlaylogEvents in the broadcast pipeline

### Which services operate on Asset

- **IngestService**: Creates and manages asset lifecycle during collection ingest
- **EnricherService**: Processes assets through enrichment pipeline
- **ScheduleService**: Consumes ready assets for scheduling
- **PlayoutService**: Uses asset metadata for playout execution

### Which parts of the system are allowed to see/use which states

- **Ingest Layer**: Manages assets through `new` → `enriching` → `ready` progression
- **Scheduling Layer**: ONLY considers `ready` assets with `approved_for_broadcast=true`
- **Runtime Layer**: ONLY plays `ready` assets with `approved_for_broadcast=true`

## Failure / fallback behavior

### What happens when ingest or enrichment breaks

If assets fail to be discovered or processed, the system logs errors and continues with available assets. Invalid assets remain in `enriching` state or are marked as `retired`. If ready assets are missing or invalid, the system falls back to default programming or the most recent valid content.

### Safety rules for delete/restore, especially around scheduled content

- Asset deletion requires confirmation unless `--force` is provided
- **PRODUCTION SAFETY**: Assets referenced by PlaylogEvent or AsRunLog CANNOT be deleted in production, even with `--force`
- Individual asset ingest failures do not abort the entire collection ingest operation
- Transaction rollback occurs on any fatal error, ensuring no partial state changes

## Operator workflows

### Discovery / ingest

Assets are automatically discovered during collection ingest operations:

- `retrovue collection ingest <collection_id>` - Ingest assets from a collection
- `retrovue source ingest <source_id>` - Bulk ingest from all enabled collections in a source

### Selection / filtering / targeting assets

Select assets for operations:

- `retrovue assets select --uuid <uuid>` - Select specific asset by UUID
- `retrovue assets select --type "TV" --title "The Simpsons" --season 1 --episode 1` - Select by TV show hierarchy
- `retrovue assets select --type "Movie" --title "The Matrix"` - Select movie assets

### Approval / broadcast readiness

Assets automatically become `ready` when fully processed and approved:

- Enrichers validate and enhance content
- System marks assets as `approved_for_broadcast=true` when processing completes
- ONLY `ready` assets with `approved_for_broadcast=true` are eligible for scheduling

### Cleanup / retirement

Use soft delete (`is_deleted=true`) to remove content while preserving audit trail:

- `retrovue assets delete --uuid <uuid> --soft` - Soft delete (reversible)
- `retrovue assets delete --uuid <uuid> --hard --force` - Hard delete (permanent, requires --force)

## Naming rules

### Canonical casing (Asset vs assets)

- **Operator-facing noun**: `assets` (humans type `retrovue assets ...`)
- **Internal canonical model**: `Asset`
- **Database table**: `assets` (plural)
- **CLI commands**: Use UUID as primary identifier
- **Code and docs**: Always refer to the persisted model as `Asset` (singular, capitalized)

### Table naming

- Database table: `assets` (plural)
- Foreign key references: `collection_uuid`

### CLI naming

- CLI noun: `assets` (plural)
- Commands: `retrovue assets select`, `retrovue assets delete`, etc.
- Primary identifier: UUID

### UUID spine rule

Asset UUID is the primary key and spine connecting all asset-related tables. There is no "AssetDraft" - importers return normalized Asset data that becomes Asset records during ingest.

## See also

- [Asset Contracts](../contracts/resources/README.md#asset-contracts) - Complete behavioral contracts for all Asset operations
- [Collection](Collection.md) - Content groupings that contain assets
- [Source](Source.md) - Content sources that contain collections
- [Importer](Importer.md) - Content discovery and normalization from external systems
- [Ingest Pipeline](IngestPipeline.md) - Content discovery workflow that creates assets
- [Scheduling](Scheduling.md) - How ready assets become scheduled content
- [PlaylogEvent](PlaylogEvent.md) - Scheduled asset playout events
