_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md)_

# Domain — Ingest pipeline

## Purpose

Define how external media becomes part of RetroVue's managed library. The ingest pipeline is responsible for enumerating sources, selecting which collections are eligible, pulling asset records, enriching those records, and storing them in RetroVue.

## Core model / scope

Source is a configured external content provider (e.g. Plex, filesystem, Jellyfin).

A source is stored in the database after running `retrovue source add`.

Each source has:

- type (e.g. plex, filesystem, jellyfin)
- name (operator label)
- connection parameters (URL, API token, root path, etc.)

Sources are registered in the Source Registry. The registry supports:

- listing known source types (`retrovue source list-types`)
- creating instances (`retrovue source add`)
- listing configured instances (`retrovue source list`)
- updating and removing instances

A Collection (also called SourceCollection) is a logical library inside a Source.

Examples:

- Plex libraries such as "Movies", "TV Shows", "Kids Cartoons", "Adult"
- A filesystem subtree such as `/srv/media/cartoons`

Collections sit between Source and Asset. RetroVue ingests from Collections, not directly from the Source as a whole.

Each collection tracks:

- source_id (which Source it belongs to)
- display_name (e.g. "TV Shows")
- source_path (path or mount as reported by the Source, e.g. /media/TV)
- local_path (path RetroVue should actually read, e.g. R:\Media\TV or /mnt/plex/tv)
- sync_enabled (operator toggle; if false, this collection is never ingested)
- path_resolved / reachability state (whether local_path is valid/readable)

Operators can selectively ingest only certain collections. This prevents pulling e.g. adult content or personal footage.

Operators can map remote paths to local paths. Example: Plex reports /media/TV, but RetroVue must read R:\Media\TV. If no usable mapping is provided, the collection is marked not ingestable.

## Contract / interface

AssetDraft is the record produced during ingest for a single media item.

The importer for a collection returns AssetDraft objects with basic fields:

- file path (as reported by the source)
- runtime/duration if known
- guessed title / series / season / episode
- any chapter/ad-break markers discovered

AssetDrafts are then run through ingest-scope enrichers before being stored in RetroVue's catalog.

## Execution model

The ingest orchestration runs in this order:

1. Enumerate collections for a source.

   - `ImporterRegistry.list_collections(source_id)` calls the importer plugin and discovers libraries / folders / sections.
   - RetroVue persists those as Collection rows.

2. For each collection:

   - If sync_enabled is false, skip.
   - If local_path is missing or not reachable, skip.

3. Ingest that collection:
   - `ImporterRegistry.fetch_assets_for_collection(source_id, collection_id, local_path)` retrieves AssetDrafts for that collection.
   - Each AssetDraft is enriched by ingest enrichers attached to that collection (in priority order).
   - The final enriched asset is stored in RetroVue's managed library.

## Failure / fallback behavior

The ingest unit is a Collection, not an entire Source.

Collections act as content filters. Example: "Movies" may be included, "Adult" may be excluded.

Collections also act as path translation points. Each collection can map source_path → local_path.

A collection is considered ineligible for ingest if:

- sync_enabled is false, OR
- local_path is missing/unreadable

Enricher failures on a single AssetDraft do not abort ingest. Failures are logged and ingest continues.

Fatal stop conditions are:

- collection is disabled,
- collection storage path cannot be resolved,
- importer cannot enumerate assets for that collection.

## Operator workflows

- `retrovue source add ...` registers a new Source.
- `retrovue source list` shows all configured Sources.
- `retrovue source list-types` shows all importer types currently available to this build and loaded into the registry.
- `retrovue source sync-collections <source_id>` updates RetroVue's view of that Source's Collections.
- `retrovue collection list --source <source_id>` shows Collections, including sync_enabled and path mappings.
- `retrovue collection update <collection_id> --sync-enabled=false` disables ingest for that Collection.
- `retrovue collection update <collection_id> --local-path "R:\Media\TV"` configures path mapping.
- `retrovue ingest run <collection_id>` ingests just that Collection.
- `retrovue ingest run --source <source_id>` ingests all eligible Collections under that Source.

## Naming rules

- "Source" always refers to an external system instance (e.g. a Plex server).
- "Collection" always refers to a logical library or subtree inside that Source (e.g. "TV Shows").
- "AssetDraft" is the ingest-time representation of a media item before it is promoted into the RetroVue catalog.
- "Ingest Enricher" refers to enrichers with scope=ingest, which run on AssetDraft before catalog storage.

## See also

- [Source](Source.md) - External content providers
- [Asset](Asset.md) - Media file management
- [Enricher](Enricher.md) - Content enhancement
- [Operator CLI](../operator/CLI.md) - Operational procedures
