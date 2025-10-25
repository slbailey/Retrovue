_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md)_

# Domain — Source

## Purpose

Source defines a persistent content discovery entity that connects to external media systems (Plex, filesystem) and manages collections of content libraries. Sources provide the foundation for content discovery and ingestion workflows.

## Core model / scope

Source is managed by SQLAlchemy with the following fields:

- **id** (UUID, primary key): Internal identifier for relational joins and foreign key references
- **external_id** (String(255), required, unique): External system identifier (e.g., "plex-abc123", "filesystem-def456")
- **name** (String(255), required): Human-facing source label used in UI and operator tooling
- **kind** (String(50), required): Source type identifier ("plex", "filesystem", etc.)
- **config** (JSON, nullable): Source-specific configuration including connection details and enrichers
- **created_at** (DateTime(timezone=True), required): Record creation timestamp
- **updated_at** (DateTime(timezone=True), required): Record last modification timestamp

The table is named `sources` (plural). Schema migration is handled through Alembic. Postgres is the authoritative backing store.

Source has relationships with SourceCollection through foreign key constraints with cascade deletion.

## Contract / interface

SourceCollection represents individual content libraries within a source (e.g., Plex libraries, filesystem directories). Collections are automatically discovered when Plex sources are created and can be enabled/disabled individually.

SourceCollection fields:

- **id** (UUID, primary key): Internal identifier
- **source_id** (UUID, foreign key): Reference to parent Source
- **external_id** (String(255), required): External system identifier (e.g., Plex library key)
- **name** (String(255), required): Human-readable collection name
- **enabled** (Boolean, required, default=False): Whether collection is active for content discovery
- **config** (JSON, nullable): Collection-specific configuration
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

PathMapping provides path translation between external systems and local storage:

- **id** (UUID, primary key): Internal identifier
- **collection_id** (UUID, foreign key): Reference to parent SourceCollection
- **plex_path** (String(500), required): External system path
- **local_path** (String(500), required): Local filesystem path

## Execution model

SourceService manages source lifecycle and collection discovery. When a Plex source is created, collections are automatically discovered and persisted with enabled=False by default.

IngestOrchestrator consumes enabled collections to discover content for ingestion workflows.

## Failure / fallback behavior

If source connections fail, the system logs errors and continues with available sources. Collections with invalid paths are marked as not ingestable.

## Operator workflows

**Create Plex source**: Use `retrovue source add --type plex` with required parameters. Collections are automatically discovered and persisted:

```bash
retrovue source add --type plex --name "My Plex Server" \
  --base-url "https://plex.example.com" --token "your-token"
```

**Create filesystem source**: Use `retrovue source add --type filesystem` with required parameters:

```bash
retrovue source add --type filesystem --name "Media Library" \
  --base-path "/media/movies"
```

**List sources**: Use `retrovue source list` to see all sources, or `retrovue source list --json` for machine-readable output.

**Show source details**: Use `retrovue source show "Source Name"` to see detailed source information including configuration and enrichers.

**Update source**: Use `retrovue source update "Source Name"` with new parameters to modify source configuration.

**Update enrichers**: Use `retrovue source enrichers "Source Name" "enricher1,enricher2"` to add or modify enrichers without recreating the source.

**Manage collections**: Use `retrovue source collections` to view all collections, `retrovue source enable "Collection Name"` to activate collections, and `retrovue source disable "Collection Name"` to deactivate collections.

**Delete source**: Use `retrovue source delete "Source Name" --force` to permanently remove source and all related collections and path mappings.

All operations support identification by name, UUID, or external ID. The CLI provides both human-readable and JSON output formats.

## Naming rules

The canonical name for this concept in code and documentation is Source.

- **Operator-facing noun**: `source` (humans type `retrovue source ...`)
- **Internal canonical model**: `Source`
- **Database table**: `sources` (plural)
- **CLI commands**: Use names, UUIDs, or external IDs for source identification
- **Code and docs**: Always refer to the persisted model as `Source`

Source is always capitalized in internal docs. external_id uses format "type-hash" (e.g., "plex-abc123"). Collections are automatically discovered for Plex sources and start disabled by default.

## See also

- [Source collection](SourceCollection.md) - Content library management
- [Ingest pipeline](IngestPipeline.md) - Content discovery workflow
- [Asset](Asset.md) - Media file management
- [Operator CLI](../operator/CLI.md) - Operational procedures
