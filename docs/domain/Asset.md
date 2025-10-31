_Related: [Collection](Collection.md) • [Source](Source.md) • [Scheduling](Scheduling.md) • [Ingest Pipeline](IngestPipeline.md)_

# Domain — Asset

## Purpose

Asset is the atomic unit of broadcastable content in RetroVue. It bridges ingestion, enrichment, and playout by defining a consistent, canonical representation of every piece of media. Assets are the foundation of RetroVue's content lifecycle and the single source of truth for anything that can air.

## Core model / scope

### Primary key / identity fields

- **uuid** (UUID, primary key): Primary identifier serving as the spine connecting all asset-related tables

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
  - Invariant: `true` requires `state='ready'` (enforced by database constraint)
  - Used by ScheduleService to determine available content
  - Set by operators via `asset resolve --approve`
- **operator_verified** (Boolean, required, default=False): Reserved for future multi-tier review processes distinct from broadcast approval

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

- **last_enricher_checksum** (String(64), nullable): Reserved for future automatic enricher change detection
- **created_at** (DateTime(timezone=True), required, auto-generated): When asset record was created
- **updated_at** (DateTime(timezone=True), required, auto-generated): Last modification timestamp

### Relationships

Asset has relationships with:

- **Collection** (via `collection_uuid` foreign key): The collection this asset belongs to
- **Episode** (via `episode_assets` junction table): Many-to-many relationship with episodes (planned/WIP)
- **ProviderRef**: External system references (Plex rating keys, etc.)
- **Marker**: Chapters, availability windows, and other asset markers
- **ReviewQueue**: Items requiring human review for quality assurance

### Indexes

Asset table includes indexes on:

- `ix_assets_collection_uuid` on `collection_uuid`
- `ix_assets_state` on `state`
- `ix_assets_approved` on `approved_for_broadcast`
- `ix_assets_operator_verified` on `operator_verified`
- `ix_assets_discovered_at` on `discovered_at`
- `ix_assets_is_deleted` on `is_deleted`
- `ix_assets_collection_canonical_unique` **unique** on `(collection_uuid, canonical_key_hash)`
- `ix_assets_collection_uri_unique` **unique** on `(collection_uuid, uri)` (deployment / storage-layout dependent)
- `ix_assets_schedulable` **partial** on `(collection_uuid, discovered_at)` where `state='ready' AND approved_for_broadcast=true AND is_deleted=false` (hot path for schedulers)

## Contract / interface

### Lifecycle states

Assets progress through four distinct states:

1. **`new`**: Recently discovered, minimal metadata, awaiting processing
2. **`enriching`**: Undergoing enrichment by metadata services
3. **`ready`**: Fully processed, operator-approved, available for scheduling
4. **`retired`**: No longer available for broadcast

Procedural lifecycle control keeps the ingest and enrichment pipeline predictable and transparent. State transitions are enforced by ingest and enricher services.

### Critical invariants

- Check constraint: `chk_approved_implies_ready` enforces that `approved_for_broadcast=true` requires `state='ready'`
- Check constraint: `chk_deleted_at_sync` ensures `is_deleted` and `deleted_at` are synchronized
- Check constraint: `chk_canon_hash_len` enforces canonical key hash length of 64 characters
- Check constraint: `chk_canon_hash_hex` enforces canonical key hash is hexadecimal
- Unique constraint: `ix_assets_collection_canonical_unique` on `(collection_uuid, canonical_key_hash)` prevents duplicate assets
- Unique constraint: `ix_assets_collection_uri_unique` on `(collection_uuid, uri)` prevents duplicate URIs per collection
- Newly ingested assets enter as `new` or `enriching`, never `ready`
- Every asset belongs to exactly one collection via `collection_uuid`

### Lifecycle flow

Assets progress through:

1. **Discovery**: Asset discovered during collection ingest (`state=new`)
2. **Enrichment**: Enrichers process metadata and enhance content (`state=enriching`)
3. **Approval**: Operator reviews and approves via `asset resolve --approve --ready` (sets `state=ready` and `approved_for_broadcast=true`)
4. **Scheduling**: Ready assets become eligible for scheduling and playout
5. **Retirement**: Assets marked `state=retired` when no longer available

State transitions are enforced procedurally by ingest, enricher, and operator workflows.

### Canonical key system

Assets are uniquely identified within a collection using canonical keys:

- **Canonical Key**: Deterministic string generated by `canonical_key_for()`
  - Normalizes filesystem paths and URIs (e.g., `file:/media/movie.mp4`)
  - Uses `provider_key` or `external_id` when available
  - Includes collection identifier
- **Canonical Hash**: SHA256 hash of canonical key, stored as `canonical_key_hash`
  - Enables efficient lookups and duplicate detection
  - Enforces uniqueness: `(collection_uuid, canonical_key_hash)`
- **Key Generation**: Handled by ingest service via `src/retrovue/infra/canonical.py`

**Normalization Rules**:
- Windows paths: `C:\path\to\file.mkv` → `/c/path/to/file.mkv`
- UNC paths: `\\SERVER\share\file.mkv` → `//SERVER/share/file.mkv` (server name preserved)
- URIs: `file:///path/to/file.mkv` → normalized scheme://host/path (host lowercased)
- Paths are lowercased and trailing slashes removed

### Duplicate detection

Assets are identified by canonical identity within a collection:

- **Canonical Identity**: Determined by importer via `canonical_key_for()`
- **Uniqueness**: One asset per canonical identity (enforced by unique constraint on `collection_uuid, canonical_key_hash`)
- **Duplicate Resolution**: Matching canonical key hash updates existing record instead of inserting

**Content Change Detection**:

- `hash_sha256` tracks content signature
- Ingest compares current hash with stored hash
- Changed assets re-process, resetting state to `new` or `enriching`

**Enricher Change Detection**:

- Reserved for future enrichment improvements
- Checksum-based reprocessing will automatically detect configuration changes

## Contract-driven behavior

All Asset operations are defined by behavioral contracts that specify exact CLI syntax, safety expectations, output formats, and data effects. The contracts ensure:

- **Safety first**: No destructive operations run against live data during automated tests
- **One contract per operation**: Each Asset operation has its own focused contract
- **Test isolation**: All operations support `--test-db` for isolated testing
- **Idempotent operations**: Asset operations are safely repeatable
- **Clear error handling**: Failed operations provide clear diagnostic information

Key contract patterns:

- `--test-db` flag directs operations to isolated test environment
- `--dry-run` flag shows what would be performed without executing
- Confirmation prompts for destructive operations (with `--force` override)
- JSON output format for automation and machine consumption
- Atomic transactions with rollback on failure

### CLI operations

**Implemented**:
- `retrovue asset attention` — List assets needing operator attention _(Contract: [Asset Attention](../contracts/resources/AssetAttentionContract.md))_
- `retrovue asset resolve <uuid>` — Approve and/or mark asset ready _(Contract: [Asset Resolve](../contracts/resources/AssetResolveContract.md))_

**Planned**:
- `retrovue asset show <uuid>` — Display detailed asset information _(Contract: [Asset Show](../contracts/resources/AssetShowContract.md))_
- `retrovue asset list` — List assets with filtering options _(Contract: [Asset List](../contracts/resources/AssetListContract.md))_
- `retrovue asset update <uuid>` — Update asset metadata and configuration _(Contract: [Asset Update](../contracts/resources/AssetUpdateContract.md))_
- `retrovue assets select` — Select assets by criteria _(Contract: [Assets Select](../contracts/resources/AssetsSelectContract.md))_
- `retrovue assets delete` — Delete assets _(Contract: [Assets Delete](../contracts/resources/AssetsDeleteContract.md))_

For complete behavioral specifications, see the [Asset Contracts](../contracts/resources/AssetContract.md).

## Execution model

### Asset lifecycle

Assets flow from discovery through scheduling:

1. **Discovery**: Importers enumerate assets from external sources
2. **Normalization**: Importers return normalized asset descriptions
3. **Persistence**: Ingest creates Asset records in `new` or `enriching` state (updates existing records if canonical key hash matches)
4. **Duplicate Detection**: System checks canonical identity to prevent duplicates
5. **Change Detection**: System re-processes existing assets if content hash changed
6. **Enrichment**: Enrichers attach metadata, validate content, set state to `enriching`
7. **Approval**: Operators review via `asset attention` and approve via `asset resolve --approve --ready`
8. **Scheduling**: ScheduleService queries for `state='ready' AND approved_for_broadcast=true AND is_deleted=false`
9. **Playout**: Scheduling creates ProgramEpisode entries referencing assets; PlaylogEvents generated from ProgramEpisodes for playback

**Note**: ScheduleService consumes ProgramEpisode entries, not Asset records directly. Playback follows PlaylogEvent → ProgramEpisode → Asset chain.

### Service integration

- **IngestService**: Creates and manages asset lifecycle during collection ingest
- **EnricherService**: Processes assets through enrichment pipeline
- **ScheduleService**: Queries ready, approved assets for scheduling (via ProgramEpisode creation)
- **PlayoutService**: Uses asset metadata from ProgramEpisode references for playout execution

### State visibility

- **Ingest Layer**: Creates assets in `new` or `enriching` state
- **Enrichment Layer**: Processes assets in `enriching` state
- **Operator Layer**: Reviews and approves via `asset attention` and `asset resolve`
- **Scheduling Layer**: Queries `ready` assets with `approved_for_broadcast=true AND is_deleted=false`
- **Runtime Layer**: Consumes assets indirectly via PlaylogEvent → ProgramEpisode references

## Failure / fallback behavior

### Ingest and enrichment failure handling

If assets fail discovery or processing, the system logs errors and continues with available assets. Invalid assets remain in `enriching` state or marked as `retired`. Missing or invalid ready assets trigger fallback to default programming or most recent valid content.

### Safety rules

- **PRODUCTION SAFETY**: Hard deletes disabled in production; only soft deletes (`is_deleted=true`) permitted
- **PRODUCTION SAFETY**: Assets referenced by PlaylogEvent or AsRunLog cannot be deleted, even with `--force`
- Asset deletion requires confirmation unless `--force` provided
- Individual asset ingest failures do not abort collection ingest operation
- Transaction rollback on any fatal error prevents partial state changes

## Operator workflows

### Discovery and ingest

Assets are automatically discovered during collection ingest:

- `retrovue collection ingest <collection_id>` — Ingest assets from a collection
- `retrovue source ingest <source_id>` — Bulk ingest from all enabled collections in a source

### Selection and filtering

Select assets for operations _(Contract: Planned)_:

- `retrovue assets select --uuid <uuid>` — Select specific asset by UUID
- `retrovue assets select --type "TV" --title "The Simpsons" --season 1 --episode 1` — Select by TV show hierarchy
- `retrovue assets select --type "Movie" --title "The Matrix"` — Select movie assets

### Approval workflow

Assets require operator approval before becoming broadcast-ready:

- Use `retrovue asset attention` to list assets needing attention
- Use `retrovue asset resolve <uuid> --approve --ready` to approve and mark ready
- Only `ready` assets with `approved_for_broadcast=true` are eligible for scheduling
- Enrichers do not automatically set `approved_for_broadcast=true`

### Cleanup and retirement

Use soft delete to remove content while preserving audit trail _(Contract: Planned)_:

- `retrovue assets delete --uuid <uuid>` — Soft delete (reversible; hard deletes disabled in production)
- Mark assets as `retired` to prevent scheduling without deleting

## Naming rules

### Naming conventions

The canonical name for this concept in code and documentation is **Asset**.

- **Operator-facing noun**: `assets` (humans type `retrovue assets ...`)
- **Internal canonical model**: `Asset`
- **Database table**: `assets` (plural)
- **CLI commands**: Use UUID as primary identifier
- **Code and docs**: Always refer to the persisted model as `Asset` (singular, capitalized)

There is no "AssetDraft" — importers return normalized Asset data that becomes Asset records during ingest.

## Future work

The current schema provides a solid foundation for upcoming enrichment and scheduling enhancements. Future iterations will add automatic enricher checksum validation using `last_enricher_checksum`.

## See also

- [Asset Contracts](../contracts/resources/AssetContract.md) - Complete behavioral contracts for all Asset operations
- [Collection](Collection.md) - Content groupings that contain assets
- [Source](Source.md) - Content sources that contain collections
- [Scheduling](Scheduling.md) - How ready assets become scheduled content
- [Ingest Pipeline](IngestPipeline.md) - Content discovery workflow
