# Domain — CatalogAsset

## Purpose

CatalogAsset represents a broadcast-approved catalog entry that is eligible for scheduling and playout. This is the "airable" content that ScheduleService can select and schedule for broadcast.

## Persistence model and fields

CatalogAsset is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Internal identifier for relational joins and foreign key references
- **uuid** (UUID, required, unique): External stable identifier exposed to API, runtime, and logs
- **title** (Text, required): Human-readable asset title
- **duration_ms** (Integer, required): Asset duration in milliseconds
- **tags** (Text, optional): Comma-separated content tags for categorization
- **file_path** (Text, required): Local file system path to the asset
- **canonical** (Boolean, required): Approval status - only canonical assets are eligible for scheduling
- **source_ingest_asset_id** (Integer, optional, foreign key): Reference to Library Domain asset for traceability
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

Schema migration is handled through Alembic. Postgres is the authoritative backing store.

CatalogAsset has indexes on canonical, tags, and source_ingest_asset_id fields for efficient content selection queries.

**Important**: CatalogAsset inherits the same uuid value as its source ingest Asset. It stores source_ingest_asset_id (INTEGER FK to ingest assets.id) for lineage and QC traceability.

## Scheduling and interaction rules

CatalogAsset is only created from approved ingest content, and only canonical CatalogAsset entries are eligible for scheduling.

ScheduleService consumes CatalogAsset records to select content for scheduling. Only assets with canonical=true are eligible for selection. ScheduleService uses:

- Tags to match content selection rules from BroadcastTemplateBlock
- Duration to fit content within time blocks
- File paths to generate playout instructions
- Approval status to ensure only approved content is scheduled

Catalog assets are the source of all scheduled content - no content can be scheduled that is not in the catalog with canonical=true.

## Runtime behavior

CatalogAsset is what actually airs; runtime never directly plays ingest Asset.

## Operator workflows

**Approve Content**: Set canonical=true to make content eligible for scheduling.

**Manage Content Metadata**: Update titles, tags, and other metadata for better content organization.

**Content Promotion**: Promote content from Library Domain to Broadcast Domain catalog.

**Content Maintenance**: Update file paths, manage content lifecycle, and handle content changes.

**Content Discovery**: Search and filter catalog assets by tags, duration, and approval status.

Operators and external integrations should always refer to objects by uuid, not by integer id.

## Naming rules

The canonical name for this concept in code and documentation is CatalogAsset.

API surfaces and logs must surface the UUID, not the integer id.

CatalogAsset represents the broadcast-approved catalog entries (airable content) that are eligible for scheduling and playout, with full traceability back to the ingest domain through shared UUID values and foreign key relationships.
