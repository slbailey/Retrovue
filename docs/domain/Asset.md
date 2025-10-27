_Related: [Architecture](../overview/architecture.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md)_

# Domain — Asset

## Purpose

Asset represents the leaf unit RetroVue can eventually broadcast. Each asset belongs to exactly one collection and has a lifecycle state indicating its readiness for scheduling and playout.

## Core model / scope

Asset is managed by SQLAlchemy with the following fields:

### Primary Key

- **uuid** (UUID, primary key): Stable identifier that serves as the spine connecting all other tables that reference assets

### Required Fields (at `ready` state)

- **title** (Text, required): Human-readable asset title
- **runtime_ms** (Integer, required): Asset duration in milliseconds
- **canonical_path** (Text, required): Local file system path to the asset
- **type** (String(50), required): Content type (episode, movie, bumper, commercial, etc.)
- **rating** (String(20), required): Content rating (G, PG, PG-13, R, etc.)
- **tags** (Text, optional): Comma-separated content tags for categorization
- **approved_for_broadcast** (Boolean, required): Approval status for scheduling eligibility

### Lifecycle Fields

- **state** (String(20), required): Lifecycle state (`new`, `enriching`, `ready`, `retired`)
- **collection_uuid** (UUID, required, foreign key): Reference to the collection this asset belongs to

### Technical Fields

- **uri** (Text, optional): Original file system path or URI to the media file
- **size** (BigInteger, optional): File size in bytes
- **video_codec** (String(50), optional): Video codec information
- **audio_codec** (String(50), optional): Audio codec information
- **container** (String(50), optional): Container format
- **hash_sha256** (String(64), optional): SHA256 hash for content integrity
- **discovered_at** (DateTime(timezone=True), required): When the asset was first discovered
- **is_deleted** (Boolean, required): Soft delete flag for content lifecycle management
- **deleted_at** (DateTime(timezone=True), optional): When the asset was soft deleted

Schema migration is handled through Alembic. Postgres is the authoritative backing store.

Asset has relationships with Collection through collection_uuid foreign key, and with ProviderRef for external system traceability.

## Contract / interface

Asset represents content that progresses through a lifecycle state machine:

1. **`new`**: Recently discovered, minimal metadata
2. **`enriching`**: Being processed by enrichers
3. **`ready`**: Fully processed, approved for broadcast
4. **`retired`**: No longer available or approved

### Critical Invariants

- **An asset in `ready` state MUST have `approved_for_broadcast=true`**
- **An asset with `approved_for_broadcast=true` MUST be in `ready` state**
- **Scheduling and playout only operate on assets in state `ready`**

Asset approval workflow:

1. Asset discovered during ingestion (`state=new`)
2. Enrichers process metadata (`state=enriching`)
3. Asset marked `state=ready` and `approved_for_broadcast=true` when fully processed
4. Ready assets are eligible for scheduling and playout

## Execution model

Asset is what actually airs; runtime only plays assets in `ready` state. ScheduleService consumes Asset records to select content for scheduling, using:

- Tags to match content selection rules from BroadcastTemplateBlock
- Runtime to fit content within time blocks
- Canonical path to generate playout instructions
- State and approval status to ensure only ready content is scheduled

Assets are the source of all scheduled content - no content can be scheduled that is not in `ready` state with `approved_for_broadcast=true`.

## Failure / fallback behavior

If assets fail to be discovered or processed, the system logs errors and continues with available assets. Invalid assets remain in `enriching` state or are marked as `retired`. If ready assets are missing or invalid, the system falls back to default programming or the most recent valid content.

## Operator workflows

**Content Discovery**: Assets are automatically discovered during library scanning from external sources.

**Content Enrichment**: Monitor and manage assets progressing through the enrichment pipeline.

**Content Approval**: Assets automatically become `ready` when fully processed and approved.

**Content Management**: Update metadata, manage file paths, and handle content lifecycle.

**Content Scheduling**: Only `ready` assets are eligible for scheduling and playout.

**Content Cleanup**: Use soft delete (`is_deleted=true`) to remove content while preserving audit trail.

Operators and external integrations should always refer to objects by UUID. The UUID serves as the primary key and spine connecting all asset-related tables.

## Naming rules

The canonical name for this concept in code and documentation is Asset.

API surfaces and logs must surface the UUID as the primary identifier.

Asset represents the single source of truth for all broadcastable content, with lifecycle states ensuring only fully-processed, approved content reaches the scheduling layer. The UUID serves as the spine connecting all other tables that reference assets.

## See also

- [Collection](Collection.md) - Content groupings
- [Source](Source.md) - Content sources
- [Ingest pipeline](IngestPipeline.md) - Content discovery workflow
- [Operator CLI](../operator/CLI.md) - Operational procedures
