# Contract — Collection Ingest

## Purpose

Defines the behavioral rules for `retrovue collection ingest` including discovery, validation, enrichment, and persistence effects.

This contract explicitly specifies how URIs are persisted during ingest:
- `source_uri`: Source-native locator provided by the importer (e.g., `plex://12345`).
- `canonical_uri`: Locally-resolvable native filesystem path derived during ingest via importer path
  resolution and `PathMapping` (e.g., `R:\media\tv\...` on Windows, `/mnt/media/...` on Linux).

## Commands

- `retrovue collection ingest <selector> [--title <t>] [--season <n>] [--episode <n>] [--dry-run] [--json] [--verbose-assets]`

## Preconditions

- Collection exists and is ingestible.
- For full ingest (no title/season/episode filters), `sync_enabled=true`.

## Behavior

1) Discovery
- Importer is invoked to discover items (supports scoped discovery when filters provided).
- Importer returns items with a stable `source_uri` (native to the source) and provider metadata.

2) URI Resolution
- Ingest calls `importer.resolve_local_uri(item, *, collection, path_mappings)` to obtain a local `file://` URI for enrichment.
- The resolved local URI is used transiently for enrichment only.

3) Persistence
- Collection ingest MAY ONLY create new `Asset` rows. It MUST NOT mutate existing assets.
- New `Asset` rows include:
  - `source_uri`: persisted verbatim from the importer (unique per `(collection_uuid, source_uri)`).
  - `canonical_uri`: persisted from the resolved local path (native OS path; not `file://`).
  - Canonical identity: `canonical_key` and `canonical_key_hash` are derived from canonical path + collection.
  - `hash_sha256`: computed natively by ingest at create-time when the local file is reachable; otherwise left null.

4) Enrichment
- Attached ingest-scope enrichers run in priority order.
- Enricher outputs update technical fields (e.g., `duration_ms`, `video_codec`, `audio_codec`, `container`).
  Hash computation is not an enricher responsibility.
- A stable `last_enricher_checksum` is stored for change detection.
- Enricher dependency errors (e.g., FFprobe not installed) MUST be surfaced as readable messages in `stats.errors`. Ingest continues for other items without crashing.

5) Updates vs Creates
- If `(collection_uuid, canonical_key_hash)` matches an existing asset: collection ingest MUST SKIP without updating.
- Asset modifications (content/enricher/approval) are handled by a separate `asset update` command (pending).

6) Failure Modes
- If importer cannot resolve a local URI for an ingestible collection, ingest fails with a validation error referencing `PathMapping`.
- Importer/network errors are returned with appropriate exit code and surfaced in `--json` mode.

## Output

### Human
- Prints scope and summary stats (discovered/ingested/skipped). No updates are performed during ingest.

### JSON (`--json`)
- Returns an object with `status`, `scope`, `collection_id`, `collection_name`, `stats`, and optional `last_ingest_time`.
- When `--verbose-assets` is provided:
  - `created_assets[]` entries SHOULD include `uuid`, `source_uri`, `canonical_uri`.
  - `updated_assets[]` MUST be an empty list (updates are disallowed during ingest).

## Safety
- `--dry-run` must execute discovery and enrichment preparation without any DB writes.
- Transactions are atomic; partial writes are rolled back on error.

## Notes
- This contract supersedes prior ambiguity about `uri` by explicitly separating `source_uri` and `canonical_uri` and assigning importer vs ingest responsibilities.
- Asset mutation is deferred to an upcoming `asset update` command (pending); ingest is create-only.
