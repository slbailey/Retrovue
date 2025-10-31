# Domain — Asset

Related: [Collection](Collection.md) • [Source](Source.md) • [Scheduling](Scheduling.md) • [Ingest Pipeline](IngestPipeline.md) • [Contracts](../contracts/README.md)

## Purpose

Asset represents the leaf unit of broadcastable content in RetroVue. Each asset belongs to exactly one collection and has lifecycle state fields indicating its readiness for scheduling and playout. Assets are the single source of truth for all broadcastable content, whether just ingested or fully processed and ready for broadcast. Assets form the atomic building blocks of RetroVue's content model, serving as the bridge between ingestion, enrichment, and broadcast domains.

## Core model / scope

### Primary key / identity fields

- **uuid** (UUID, primary key): Stable identifier that serves as the spine connecting all other tables that reference assets

### Canonical identity fields

- **canonical_key** (Text, required): Deterministic string identifying the asset within its collection (used for duplicate detection)
- **canonical_key_hash** (String(64), required): SHA256 hash of canonical_key, stored for efficient lookups
- **collection_uuid** (UUID, foreign key): Reference to the Collection this asset belongs to

**Uniqueness constraint**: `(collection_uuid, canonical_key_hash)` - Only one asset per canonical key per collection

### Required fields

- **uri** (Text, required): File system path or URI to the media file
- **size** (BigInteger, required): File size in bytes
- **state** (Enum, required): Lifecycle state (`new`, `enriching`, `ready`, `retired`)
- **discovered_at** (DateTime(timezone=True), required): When the asset was first discovered during ingest

### Approval / broadcast readiness fields

- **approved_for_broadcast** (Boolean, required, default=False): Runtime gating flag for schedulers and playout
  - **Invariant**: When `true`, `state` MUST be `ready`
  - Used by schedulers to determine what's available for playback
  - Set manually by operators via `asset resolve --approve`
- **operator_verified** (Boolean, required, default=False): Reserved for future operator review workflows (currently unused)
  - Field exists in schema but is not used by current implementation
  - Intended for staged approval workflows distinct from broadcast approval

### Soft delete fields

- **is_deleted** (Boolean, required, default=False): Soft delete flag for content lifecycle management
- **deleted_at** (DateTime(timezone=True), nullable): When the asset was soft deleted

### Technical metadata fields

- **duration_ms** (Integer, nullable): Asset duration in milliseconds
- **video_codec** (String(50), nullable): Video codec information
- **audio_codec** (String(50), nullable): Audio codec information
- **container** (String(50), nullable): Container format
- **hash_sha256** (String(64), nullable): SHA256 hash for content integrity and change detection

### Change tracking fields

- **last_enricher_checksum** (String(64), nullable): Reserved for future enricher change detection (not currently populated)
- **created_at** (DateTime(timezone=True), required, auto-generated): When asset record was created
- **updated_at** (DateTime(timezone=True), required, auto-generated): Last modification timestamp

### Relationships

Asset has relationships with:

- **Collection** (via `collection_uuid` foreign key): The collection this asset belongs to
- **ProviderRef**: External system references (Plex rating keys, etc.)
- **Marker**: Chapters, availability windows, and other asset markers
- **ReviewQueue**: Items requiring human review for quality assurance

**Note**: Episode linkage via `episode_assets` junction table is planned but not yet implemented.

### Indexes

Asset table includes indexes on:

- `collection_uuid` (for collection-based queries)
- `state` (for lifecycle state queries)
- `approved_for_broadcast` (for broadcast eligibility queries)
- `operator_verified` (for operator verification queries)
- `discovered_at` (for chronological queries)
- `is_deleted` (for soft delete filtering)
- `(collection_uuid, canonical_key_hash)` **unique** (for duplicate detection and efficient lookups)
- **Partial index**: `ix_assets_schedulable` on `(collection_uuid, discovered_at)` where `state='ready' AND approved_for_broadcast=true AND is_deleted=false` (hot path for schedulers)

## Contract / interface

### Lifecycle states

Assets have state fields that indicate their processing status:

1. **`new`**: Recently discovered during ingest, minimal metadata, not yet processed
2. **`enriching`**: Being processed by enrichers to add metadata and enhance content
3. **`ready`**: Fully processed and approved for broadcast, eligible for scheduling
4. **`retired`**: No longer available or approved for broadcast

State transitions are enforced procedurally by ingest and enricher services; there is no formal state machine implementation.

### Critical invariants

- **An asset in `ready` state MUST have `approved_for_broadcast=true`** (enforced by database constraint)
- **An asset with `approved_for_broadcast=true` MUST be in `ready` state** (enforced by database constraint)
- **Newly ingested assets enter the system in `new` or `enriching` state, NEVER `ready`**
- **Assets MUST belong to exactly one collection via `collection_uuid`**
- **Approval is manual**: `approved_for_broadcast` is set by operator review via `asset resolve --approve`, not automatically by enrichers

### Typical lifecycle flow

Assets typically progress through these states:

1. **Discovery**: Asset discovered during collection ingest (`state=new`)
2. **Enrichment**: Enrichers process metadata and enhance content (`state=enriching`)
3. **Manual Approval**: Operator reviews and approves via `asset resolve --approve --ready` (sets `state=ready` and `approved_for_broadcast=true`)
4. **Broadcast**: Ready assets are eligible for scheduling and playout
5. **Retirement**: Assets can be marked `state=retired` when no longer available

State transitions are enforced procedurally by ingest, enricher, and operator workflows.

### Canonical key system

Assets are uniquely identified within a collection using a canonical key system:

- **Canonical Key**: Deterministic string generated by `src/retrovue/infra/canonical.py::canonical_key_for()`
  - Primarily normalizes filesystem paths and URIs (e.g., `file:/media/movie.mp4`)
  - Uses `provider_key` or `external_id` when available from importers
  - Format varies by importer; typically includes collection identifier
- **Canonical Hash**: SHA256 hash of canonical key, stored as `canonical_key_hash`
  - Used for efficient database lookups and duplicate detection
  - Enforces uniqueness: `(collection_uuid, canonical_key_hash)`
- **Key Generation**: Handled by ingest service via `src/retrovue/infra/canonical.py`

**Canonical Key Normalization Rules**:
- Windows paths: `C:\path\to\file.mkv` → `/c/path/to/file.mkv`
- UNC paths: `\\server\share\file.mkv` → `//server/share/file.mkv`
- URIs: `file:///path/to/file.mkv` → normalized scheme://host/path
- Paths are lowercased and trailing slashes removed

### Duplicate / change detection behavior

Assets within a collection are identified by canonical identity for duplicate detection:

- **Canonical Identity**: Determined by importer-specific logic via `canonical_key_for()`
- **Uniqueness**: Only one Asset record per canonical identity within a collection (enforced by DB unique constraint on `collection_uuid, canonical_key_hash`)
- **Duplicate Resolution**: When a canonical key hash matches an existing record, ingest updates that record instead of inserting a new one

**Content Change Detection**:

- `hash_sha256` field tracks content signature
- System compares current content hash with stored hash
- Changed assets are re-processed, resetting state to `new` or `enriching`

**Enricher Change Detection**:

- `last_enricher_checksum` field reserved for future use; not currently populated
- Planned: System will compare enricher configuration checksums and re-process when configuration changes

## Contract-driven behavior

### How CLI noun-verb pairs map to Asset operations

**Implemented Operations:**

- **Asset Attention**: `retrovue asset attention` - List assets needing operator attention (downgraded or not broadcastable)
- **Asset Resolve**: `retrovue asset resolve <uuid>` - Resolve a single asset by approving and/or marking ready

**Planned CLI Operations:**

- **Asset Show**: `retrovue asset show <uuid>` - Display detailed asset information
- **Asset List**: `retrovue asset list` - List assets with filtering options
- **Asset Update**: `retrovue asset update <uuid>` - Update asset metadata and configuration
- **Asset Select**: `retrovue assets select` - Select assets by various criteria (UUID, title, series, genre, etc.)
- **Asset Delete**: `retrovue assets delete` - Delete assets (soft delete only in production)
- **Asset Restore**: `retrovue assets restore` - Restore soft-deleted assets

**Note**: Current implementation uses singular noun (`asset`), while some planned operations reference plural (`assets`). This inconsistency should be resolved to standardize on singular throughout.

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

Assets are the source of all scheduled content. The flow is:

1. **Ingest Pipeline**: Importers enumerate assets from external sources (Plex, filesystem, etc.)
2. **Normalization**: Importers return normalized asset descriptions
3. **Persistence**: Ingest service creates Asset records in `new` or `enriching` state (updates existing records if canonical key hash matches)
4. **Duplicate Detection**: System checks canonical identity to prevent duplicates
5. **Change Detection**: System identifies existing assets and re-processes if content hash changed
6. **Enrichment**: Enrichers attach metadata, validate content, enhance descriptions (sets state to `enriching`)
7. **Manual Approval**: Operator reviews assets via `asset attention` and approves via `asset resolve --approve --ready`
8. **Scheduling**: ScheduleService queries for assets with `state='ready' AND approved_for_broadcast=true AND is_deleted=false`
9. **Playout**: Scheduling creates ProgramEpisode entries which reference assets; PlaylogEvents are generated from ProgramEpisodes for playback

**Note**: ScheduleService does not directly schedule Asset records; it consumes ProgramEpisode entries which reference assets. Playback occurs via PlaylogEvent → ProgramEpisode → Asset chain.

### Which services operate on Asset

- **IngestService**: Creates and manages asset lifecycle during collection ingest
- **EnricherService**: Processes assets through enrichment pipeline
- **ScheduleService**: Queries ready, approved assets for scheduling (via ProgramEpisode creation)
- **PlayoutService**: Uses asset metadata from ProgramEpisode references for playout execution

### Which parts of the system are allowed to see/use which states

- **Ingest Layer**: Creates assets in `new` or `enriching` state
- **Enrichment Layer**: Processes assets in `enriching` state
- **Operator Layer**: Reviews and approves via `asset attention` and `asset resolve`
- **Scheduling Layer**: ONLY queries `ready` assets with `approved_for_broadcast=true AND is_deleted=false`
- **Runtime Layer**: Consumes assets indirectly via PlaylogEvent → ProgramEpisode references

## Failure / fallback behavior

### What happens when ingest or enrichment breaks

If assets fail to be discovered or processed, the system logs errors and continues with available assets. Invalid assets remain in `enriching` state or are marked as `retired`. If ready assets are missing or invalid, the system falls back to default programming or the most recent valid content.

### Safety rules for delete/restore, especially around scheduled content

- **PRODUCTION SAFETY**: Hard deletes are disabled in production; only soft deletes (`is_deleted=true`) are allowed
- **PRODUCTION SAFETY**: Assets referenced by PlaylogEvent or AsRunLog CANNOT be deleted in production, even with `--force`
- Asset deletion requires confirmation unless `--force` is provided (for soft deletes)
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

Assets require manual operator approval before becoming broadcast-ready:

- Use `retrovue asset attention` to list assets needing attention (state='enriching' OR approved_for_broadcast=false)
- Use `retrovue asset resolve <uuid> --approve --ready` to approve and mark asset as ready
- ONLY `ready` assets with `approved_for_broadcast=true` are eligible for scheduling
- Approval is manual; enrichers do not automatically set `approved_for_broadcast=true`

### Cleanup / retirement

Use soft delete (`is_deleted=true`) to remove content while preserving audit trail:

- `retrovue assets delete --uuid <uuid>` - Soft delete (reversible; hard deletes disabled in production)
- Assets can be marked as `retired` to prevent further scheduling without deleting

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

## Future work

The following features are planned but not yet implemented:

### Unimplemented CLI Operations

- **Asset Show**: Display detailed asset information
- **Asset List**: List assets with filtering options
- **Asset Update**: Update asset metadata and configuration
- **Asset Select**: Select assets by various criteria (UUID, title, series, genre, etc.)
- **Asset Delete**: Delete assets (soft delete workflow)
- **Asset Restore**: Restore soft-deleted assets

### Unimplemented Features

- **Episode Linkage**: `episode_assets` junction table for linking assets to TV show episodes
- **Enricher Checksum Tracking**: `last_enricher_checksum` field exists but is not populated
- **Automatic Approval**: Enrichers do not automatically set `approved_for_broadcast=true` on completion
- **Enricher Change Detection**: No automatic re-processing when enricher configuration changes
- **Provider Key Prefixing**: Canonical key generation does not consistently prefix with provider names
- **Operator Verified Workflow**: `operator_verified` field exists but is not used by current implementation

### Planned Enhancements

- Formal state machine implementation for asset lifecycle transitions
- Automatic enricher change detection using `last_enricher_checksum`
- Bulk operations for asset selection, deletion, and restoration
- Integration tests for asset-to-episode linkage
- Standardized CLI naming (singular `asset` throughout)

## See also

- [Asset Contracts](../contracts/resources/README.md#asset-contracts) - Complete behavioral contracts for all Asset operations
- [Collection](Collection.md) - Content groupings that contain assets
- [Source](Source.md) - Content sources that contain collections
- [Importer](Importer.md) - Content discovery and normalization from external systems
- [Ingest Pipeline](IngestPipeline.md) - Content discovery workflow that creates assets
- [Scheduling](Scheduling.md) - How ready assets become scheduled content
- [PlaylogEvent](PlaylogEvent.md) - Scheduled asset playout events
