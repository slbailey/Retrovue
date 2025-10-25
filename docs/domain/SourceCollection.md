_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md)_

# Domain — SourceCollection

## Purpose

SourceCollection defines a persistent content library entity that represents individual libraries within a content source (e.g., Plex libraries, filesystem directories). Collections provide granular control over which content libraries are included in content discovery workflows.

## Core model / scope

SourceCollection is managed by SQLAlchemy with the following fields:

- **id** (UUID, primary key): Internal identifier for relational joins and foreign key references
- **source_id** (UUID, foreign key, required): Reference to parent Source with cascade deletion
- **external_id** (String(255), required): External system identifier (e.g., Plex library key "1", "2")
- **name** (String(255), required): Human-readable collection name (e.g., "Movies", "TV Shows")
- **enabled** (Boolean, required, default=False): Whether collection is active for content discovery
- **config** (JSON, nullable): Collection-specific configuration including type and path mappings
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

The table is named `source_collections` (plural). Schema migration is handled through Alembic. Postgres is the authoritative backing store.

SourceCollection has relationships with PathMapping through foreign key constraints with cascade deletion.

## Contract / interface

PathMapping provides path translation between external systems and local storage:

- **id** (UUID, primary key): Internal identifier
- **collection_id** (UUID, foreign key, required): Reference to parent SourceCollection with cascade deletion
- **plex_path** (String(500), required): External system path (e.g., "/plex/movies")
- **local_path** (String(500), required): Local filesystem path (e.g., "/media/movies")
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

## Execution model

SourceService manages collection lifecycle and discovery. Collections are automatically discovered when Plex sources are created and start with enabled=False by default.

IngestOrchestrator consumes enabled collections to discover content for ingestion workflows. Only enabled collections participate in content discovery.

## Failure / fallback behavior

If collections are not reachable or have invalid paths, they are marked as not ingestable and excluded from content discovery.

## Operator workflows

**View collections**: Use `retrovue source collections` to see all collections with their enabled status, or `retrovue source collections --json` for machine-readable output.

**Enable collection**: Use `retrovue source enable "Collection Name"` to activate a collection for content discovery:

```bash
retrovue source enable "Movies"
retrovue source enable "TV Shows"
```

**Disable collection**: Use `retrovue source disable "Collection Name"` to deactivate a collection:

```bash
retrovue source disable "Horror"
```

**Filter by source**: Use `retrovue source collections --source-id "Source Name"` to view collections for a specific source.

**Automatic discovery**: Collections are automatically discovered and persisted when Plex sources are created. No manual discovery is required.

All operations support identification by name or external ID. The CLI provides both human-readable and JSON output formats.

## Naming rules

The canonical name for this concept in code and documentation is SourceCollection.

- **Operator-facing noun**: `collection` (humans type `retrovue source collections ...`)
- **Internal canonical model**: `SourceCollection`
- **Database table**: `source_collections` (plural)
- **CLI commands**: Use names or external IDs for collection identification
- **Code and docs**: Always refer to the persisted model as `SourceCollection`

SourceCollection is always capitalized in internal docs. external_id uses the external system's identifier (e.g., Plex library key "1", "2"). Collections start disabled by default and must be explicitly enabled for content discovery.

## See also

- [Source](Source.md) - External content providers
- [Ingest pipeline](IngestPipeline.md) - Content discovery workflow
- [Asset](Asset.md) - Media file management
- [Operator CLI](../operator/CLI.md) - Operational procedures
