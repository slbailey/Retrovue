# Domain — Asset

## Purpose

Asset represents a media file discovered during content ingestion from external sources like Plex, Jellyfin, or filesystem scanning.

## Persistence model and fields

Asset is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Internal identifier for relational joins and foreign key references
- **uuid** (UUID, required, unique): External stable identifier exposed to API, runtime, and logs
- **uri** (Text, required, unique): File system path or URI to the media file
- **size** (BigInteger, required): File size in bytes
- **duration_ms** (Integer, optional): Asset duration in milliseconds
- **video_codec** (String(50), optional): Video codec information
- **audio_codec** (String(50), optional): Audio codec information
- **container** (String(50), optional): Container format
- **hash_sha256** (String(64), optional): SHA256 hash for content integrity
- **discovered_at** (DateTime(timezone=True), required): When the asset was first discovered
- **canonical** (Boolean, required): Approval status - only canonical assets are eligible for promotion to CatalogAsset
- **is_deleted** (Boolean, required): Soft delete flag for content lifecycle management
- **deleted_at** (DateTime(timezone=True), optional): When the asset was soft deleted

Schema migration is handled through Alembic. Postgres is the authoritative backing store.

Asset has relationships with Episode through EpisodeAsset junction table, and with ProviderRef for external system traceability.

## Scheduling and interaction rules

Asset represents raw ingested content that requires approval before becoming eligible for broadcast. Only assets with canonical=true can be promoted to CatalogAsset entries in the Broadcast Domain.

Asset approval workflow:

1. Asset discovered during ingestion (canonical=false)
2. Content review and approval process
3. Asset marked canonical=true when approved
4. Approved assets can be promoted to CatalogAsset for scheduling

## Runtime behavior

Asset is what actually airs; runtime never directly plays ingest Asset. Only CatalogAsset entries are eligible for scheduling and playout.

## Operator workflows

**Content Discovery**: Assets are automatically discovered during library scanning from external sources.

**Content Approval**: Mark assets as canonical=true to approve them for broadcast promotion.

**Content Management**: Update metadata, manage file paths, and handle content lifecycle.

**Content Promotion**: Promote canonical assets to CatalogAsset entries in the Broadcast Domain.

**Content Cleanup**: Use soft delete (is_deleted=true) to remove content while preserving audit trail.

Operators and external integrations should always refer to objects by uuid, not by integer id.

## Naming rules

The canonical name for this concept in code and documentation is Asset.

API surfaces and logs must surface the UUID, not the integer id.

Asset represents raw ingested content that requires approval before becoming eligible for broadcast scheduling.
