_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md)_

# Domain — Catalog asset

## Purpose

CatalogAsset represents the stored, durable record of an ingested piece of content after ingest/enrichment. This is the promoted/stored version of an AssetDraft after ingest finishes. A CatalogAsset is what the scheduler and Producers reference when building the future Channel lineup.

## Core model / scope

CatalogAsset represents a broadcast-approved catalog entry that is eligible for scheduling and playout. This is the "airable" content that ScheduleService can select and schedule for broadcast.

## Contract / interface

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

CatalogAsset has indexes on canonical, tags, and source_ingest_asset_id fields for efficient content selection queries.

## Execution model

CatalogAsset is only created from approved ingest content, and only canonical CatalogAsset entries are eligible for scheduling.

ScheduleService consumes CatalogAsset records to select content for scheduling. Only assets with canonical=true are eligible for selection. ScheduleService uses:

- Tags to match content selection rules from BroadcastTemplateBlock
- Duration to fit content within time blocks
- File paths to generate playout instructions
- Approval status to ensure only approved content is scheduled

Catalog assets are the source of all scheduled content - no content can be scheduled that is not in the catalog with canonical=true.

## Failure / fallback behavior

If catalog assets are missing or invalid, the system falls back to default programming or the most recent valid content.

## Naming rules

The canonical name for this concept in code and documentation is CatalogAsset.

API surfaces and logs must surface the UUID, not the integer id.

CatalogAsset represents the broadcast-approved catalog entries (airable content) that are eligible for scheduling and playout, with full traceability back to the ingest domain through shared UUID values and foreign key relationships.

## Operator workflows

**Approve Content**: Set canonical=true to make content eligible for scheduling.

**Manage Content Metadata**: Update titles, tags, and other metadata for better content organization.

**Content Promotion**: Promote content from Library Domain to Broadcast Domain catalog.

**Content Maintenance**: Update file paths, manage content lifecycle, and handle content changes.

**Content Discovery**: Search and filter catalog assets by tags, duration, and approval status.

## See also

- [Scheduling](Scheduling.md) - High-level scheduling system
- [Asset](Asset.md) - Ingest-time content
- [Source](Source.md) - Content sources
- [Playlog event](PlaylogEvent.md) - Generated playout events
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
