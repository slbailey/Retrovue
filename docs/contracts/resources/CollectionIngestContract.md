# Collection Ingest Contract

## Purpose

Defines the exact behavior, safety, idempotence, and data effects of the ingest operation for a single collection. This is the "do the work" operation for populating new Assets from external sources within the RetroVue ingest pipeline.

NOTE: This command operates strictly on the collection level. While a "source" may contain multiple collections, a "collection ingest" targets only the enabled collection specified. "Source ingest" is a higher-level orchestration that iterates over all collections that are both `sync_enabled=true` AND `ingestible=true`, calling collection ingest for each eligible collection. Collection ingest is the atomic unit of work that source ingest loops over.

---

## Command Shape

**CLI Syntax:**

```
retrovue collection ingest <collection_id> [--title <title>] [--season <n>] [--episode <n>] [--dry-run] [--test-db] [--json]
```

- `<collection_id>`: The UUID, external ID, or display name for the collection to ingest
- `--title`: Specific title to ingest (movie/show name)
- `--season`: Season number (requires --title)
- `--episode`: Episode number (requires --title and --season)
- `--dry-run`: Show intended ingest actions without modifying the database
- `--test-db`: Direct all actions at the isolated test database environment
- `--json`: Output information in a structured JSON format for automation

**Interpretation Rules:**

- **No flags** → Full ingest of the entire collection
- **`--title` only** → Ingest that one title (all seasons, all episodes)
- **`--title` + `--season`** → Ingest just that single season of that title
- **`--title` + `--season` + `--episode`** → Ingest one specific episode

**Requirements:**

- The command MUST require either a collection ID, external ID, or exact collection name
- Named lookup MUST support both human and machine workflows
- Hierarchical narrowing: collection → title → season → episode

---

## Safety Expectations

- **Full Collection Ingest Prerequisites**: For full collection ingest (no `--title`/`--season`/`--episode` flags), the collection MUST be both `sync_enabled=true` AND `ingestible=true`. If either condition is false, the command MUST refuse to run (exit code 1) unless `--dry-run` is provided.
- **Targeted Ingest Bypass**: Targeted ingest (title/season/episode) MAY run even if `sync_enabled=false` (surgical operator action), but MUST still validate that `ingestible=true`. This allows operators to manually ingest specific content even when bulk sync is disabled.
- **Source Ingest Alignment**: When called from `source ingest`, collection ingest receives collections that have already been filtered to meet both prerequisites (`sync_enabled=true` AND `ingestible=true`). The same validation rules apply regardless of whether collection ingest is called directly or via source ingest.
- **Validation Before Enumeration**: The importer's `validate_ingestible()` method MUST be called BEFORE any call to `enumerate_assets()` or any ingest work. If `validate_ingestible()` returns `false`, the command MUST exit with code 1 (or allow `--dry-run` preview) and MUST NOT call `enumerate_assets()`. This ensures efficient failure and prevents unnecessary enumeration work.
- Importers MAY describe assets, but MUST NOT write assets. Only the ingest service layer is allowed to persist assets and update state.
- The command MUST verify that any required path mapping is both valid and known
- If `--dry-run` is provided, the command MUST NOT make any database or persistent state changes, but MUST show what _would_ be ingested
- If `--test-db` is provided, the command MUST operate solely on an isolated, non-production database
- When both `--dry-run` and `--test-db` are provided, `--dry-run` takes precedence: no database writes occur (neither production nor test), but test DB context is still used for resolution and validation
- Partial or failed ingest operations MUST NOT result in orphaned or incomplete database records
- The command MUST validate hierarchical flag dependencies (season requires title, episode requires both)

---

## Output Format

### Human-Readable Output

**Full Collection Ingest:**

```
Ingesting entire collection "TV Shows"
Discovered 128 titles, 2,931 assets
  Assets discovered: 2,931
  Assets ingested: 245 (new or changed)
  Assets skipped: 2,663 (unchanged)
  Assets updated: 23 (enricher changes detected)
Last ingest: 2024-01-15 10:30:00
Done.
```

**Title Ingest:**

```
Ingesting title "The Big Bang Theory" from collection "TV Shows"
Seasons found: 1-12
Episodes found: 279
(...progress / summary...)
Done.
```

**Season Ingest:**

```
Ingesting Season 1 of "The Big Bang Theory" from collection "TV Shows"
Episodes found: 17
(...progress / summary...)
Done.
```

**Episode Ingest:**

```
Ingesting S1E6 of "The Big Bang Theory" from collection "TV Shows"
1 episode scheduled
(...progress / summary...)
Done.
```

**Dry-run Output:**

```
[DRY RUN] Would ingest:
Collection: TV Shows
Title: The Big Bang Theory
Season: 1
Episode: 6
No changes were applied.
```

### JSON Output (if `--json` is provided)

**Episode Ingest:**

```json
{
  "status": "success",
  "scope": "episode",
  "collection_id": "4b2b05e7-d7d2-414a-a587-3f5df9b53f44",
  "collection_name": "TV Shows",
  "title": "The Big Bang Theory",
  "season": 1,
  "episode": 6,
  "stats": {
    "assets_discovered": 1,
    "assets_ingested": 1,
    "assets_skipped": 0,
    "assets_updated": 0,
    "duplicates_prevented": 0,
    "errors": []
  },
  "last_ingest_time": "2024-01-15T10:30:00Z"
}
```

**Full Collection Ingest:**

```json
{
  "status": "success",
  "scope": "collection",
  "collection_id": "4b2b05e7-d7d2-414a-a587-3f5df9b53f44",
  "collection_name": "TV Shows",
  "stats": {
    "assets_discovered": 2931,
    "assets_ingested": 245,
    "assets_skipped": 2663,
    "assets_updated": 23,
    "duplicates_prevented": 0,
    "errors": []
  },
  "last_ingest_time": "2024-01-15T10:30:00Z"
}
```

**Re-ingestion After Enricher Change:**

```json
{
  "status": "success",
  "scope": "season",
  "collection_id": "4b2b05e7-d7d2-414a-a587-3f5df9b53f44",
  "collection_name": "TV Shows",
  "title": "The Big Bang Theory",
  "season": 1,
  "stats": {
    "assets_discovered": 17,
    "assets_ingested": 0,
    "assets_skipped": 0,
    "assets_updated": 17,
    "duplicates_prevented": 0,
    "errors": []
  },
  "last_ingest_time": "2024-01-15T10:30:00Z"
}
```

---

## Exit Codes

- `0` — Success; ingest completed or (if `--dry-run`) actions listed with no errors
- `1` — Validation failure (e.g., collection not enabled, mapping invalid, missing collection, invalid flag combinations)
- `2` — Scope resolution failure (e.g., title/season/episode not found in collection)
- `3` — External system unreachable (source location cannot be scanned or accessed)
- All non-zero exit codes MUST be accompanied by a clear error message in both human and JSON output

---

## Data Effects

- New Assets MUST be created with state = `new` or `enriching`
- **Duplicate Detection**: If an incoming asset candidate matches an existing canonical identity (determined by importer's canonical identity logic, typically external_id + collection_id), it MUST NOT be duplicated in the database. The existing asset MUST be identified and evaluated for updates.
- **Incremental Sync**: Assets that have not changed since the last ingest (as determined by comparing content hash, modification time, or importer-provided change detection) MUST be skipped unless enricher changes require re-ingestion.
- **Enricher Change Detection**: If the collection's enricher configuration has changed since an asset was last ingested, existing assets MUST be re-ingested to apply new enrichers, even if content has not changed. Re-ingestion MUST update the asset's enrichment state without creating duplicates.
- **Update vs Create**: Existing assets identified during ingest MUST be updated (metadata refresh, enricher re-application) rather than creating new records. The system MUST distinguish between "new asset" and "existing asset requiring update".
- **Lifecycle Reset on Reprocess**: If an existing asset was `ready` and is being reprocessed because content or enricher configuration changed, ingest MUST reset its state back to `new` or `enriching`. This forces enrichers to run again before the asset can return to `ready` / broadcastable.
- Any enrichment hook MAY run during ingest
- Per-asset enrichment failure MUST NOT abort the entire ingest run
- Assets created by this operation MUST NOT be marked as approved for broadcast automatically
- **Ingest Time Tracking**: Upon successful completion of ingest, the collection's `last_ingest_time` field MUST be updated to reflect the completion timestamp. This timestamp MUST be recorded regardless of whether any assets were actually ingested or skipped.
- **The entire collection ingest operation MUST be wrapped in a single Unit of Work, following Unit of Work principles**
- All ingest changes MUST be atomic—either all database changes for the ingest run are committed, or none are
- **Scope isolation**: Ingest MUST only touch records reachable under the chosen scope:
  - Whole collection: may scan all titles in that collection
  - Title ingest: MUST NOT scan other titles in the same collection
  - Season ingest: MUST NOT scan other seasons of the same title
  - Episode ingest: MUST ingest at most one logical episode
- **Audit metadata**: The ingest process MUST record scope information (collection/title/season/episode) for audit and future debugging

### Duplicate Handling / Canonical Identity (B-16 / D-9..D-12)

This section defines how duplicate Assets are identified and handled during collection ingest. These rules elaborate on B-16, B-17, B-18 and D-9 through D-12 and are considered part of Collection Ingest (not a separate noun-verb contract).

#### Canonical Identity Computation

- Canonical identity determines whether two discovered items refer to the same logical Asset within a collection.
- Importers MUST provide enough information to compute a deterministic canonical identity per item.
- Typical strategies by source type:
  - Plex sources: `external_id + collection_id` (e.g., rating key + collection UUID)
  - Filesystem sources: normalized `file_path + collection_id` (path normalization per importer rules)
- The ingest service is responsible for computing and using canonical identity to find existing Assets; importers MUST NOT persist.

#### Uniqueness Within a Collection

- For a given collection, there MUST be at most one Asset per canonical identity (D-9).
- Ingest MUST treat a second appearance of the same canonical identity as referring to the existing Asset, NOT as a new record (B-16).

#### Silent De-duplication Behavior (Update vs Skip)

- When an existing Asset is found by canonical identity:
  - If content has not changed AND enrichers have not changed since last ingest → the Asset MUST be skipped (counted in `assets_skipped`) (B-17, D-10).
  - If content has changed OR enrichers have changed since last ingest → the Asset MUST be updated (counted in `assets_updated`) (B-18, D-11, D-12).
- Duplicate encounters MUST NOT be treated as operator-visible errors; they are normal ingest flow decisions (B-16).

#### Integration Into Ingest Flow

- Ordering relative to other steps:
  1. Validate collection prerequisites (`ingestible`, and `sync_enabled` for full ingest) (B-15 step 2).
  2. Resolve scope (title/season/episode) (B-15 step 3).
  3. Enumerate assets from importer (B-14), then for each item:
     - Compute canonical identity (per strategy above).
     - Attempt to find an existing Asset in the same collection by canonical identity (D-9).
     - Apply update/skip rules based on content/enricher change detection (D-10..D-12).
- Content change detection SHOULD use importer-provided signatures or stored fields such as `hash_sha256` when available (D-10).
- Enricher change detection MUST compare the current collection enricher configuration with what was last applied to the Asset (D-12).

#### Test Coverage Mapping

- Behavior: B-16, B-17, B-18 in `test_collection_ingest_contract.py`.
- Data: D-9, D-10, D-11, D-12 in `test_collection_ingest_data_contract.py`.

---

### Behavior Contract

#### Behavior Contract Rules (B-#)

- **B-1:** The command MUST accept `<collection_id>` as any of: full UUID, external ID (e.g. Plex library key), or case-insensitive display name. Collection name matching MUST be case-insensitive. If multiple collections match the provided name (case-insensitive), the command MUST exit with code 1 and emit: "Multiple collections named '<name>' exist. Please specify the UUID." Resolution MUST NOT prefer one collection over another, even if one has exact casing match.
- **B-2:** If no `--title` is provided, the command MUST ingest the entire collection.
- **B-3:** `--season` MUST NOT be provided unless `--title` is also provided. If violated, the CLI MUST exit with code 1 and a human-readable error.
- **B-4:** `--episode` MUST NOT be provided unless both `--title` and `--season` are provided. If violated, exit code MUST be 1.
- **B-5:** When `--json` is supplied, output MUST include: `"status"` ("success" or "error"), `"scope"` (one of: "collection", "title", "season", "episode"), `"collection_id"`, and `"stats"` (object with counts: assets_discovered, assets_ingested, assets_skipped, errors).
- **B-6:** The CLI MUST report exactly what scope it is acting on in human-readable mode (e.g., "Ingesting entire collection 'TV Shows'", "Ingesting title 'The Big Bang Theory' from collection 'TV Shows'").
- **B-7:** The command MUST support `--dry-run`. When `--dry-run` is present, NO database writes or file operations may occur, but the CLI MUST still resolve IDs and print what would be ingested.
- **B-8:** If the requested title/season/episode cannot be found in that collection, the command MUST exit with code 2 and say exactly what failed to resolve, still outputting valid JSON if `--json` was passed.
- **B-9:** If `--episode` is provided without an integer value, or a negative/non-integer is provided for `--season` or `--episode`, exit code MUST be 1 with "invalid argument" style messaging.
- **B-10:** When run with `--test-db`, no changes may affect production or staging databases.
- **B-10a:** When both `--dry-run` and `--test-db` are provided, `--dry-run` takes precedence. The command MUST NOT write to any database (neither production nor test), but MUST still use the test DB context for resolution and validation. Output MUST be well-formed, exit code MUST be 0 (if validation passes), and the command MUST verify that production databases were not touched.
- **B-11:** For full collection ingest (no scope flags), the collection MUST be both `sync_enabled=true` AND `ingestible=true`. If `sync_enabled=false`, the command MUST exit with code 1 and emit: "Error: Collection 'X' is not sync-enabled. Use targeted ingest (--title/--season/--episode) for surgical operations, or enable sync with 'retrovue collection update <id> --enable-sync'."
- **B-12:** For full collection ingest, if `ingestible=false`, the command MUST exit with code 1 and emit: "Error: Collection 'X' is not ingestible. Check path mappings and prerequisites with 'retrovue collection show <id>'."
- **B-13:** For targeted ingest (title/season/episode), if `ingestible=false`, the command MUST exit with code 1. Targeted ingest MAY bypass `sync_enabled=false` but MUST still require `ingestible=true`.
- **B-14:** The command MUST use the importer's `enumerate_assets()` method to discover assets from the external source. The importer MUST return normalized asset descriptions (normalized Asset data) without performing any database writes. All database persistence MUST be handled by the ingest service layer.
- **B-14a:** **Validation Before Enumeration**: The importer's `validate_ingestible()` method MUST be called BEFORE any call to `enumerate_assets()` or any other ingest work. If `validate_ingestible()` returns `false`, the command MUST exit with code 1 (or allow `--dry-run` preview per B-11/B-12 rules) and MUST NOT call `enumerate_assets()`. This ensures that asset enumeration only occurs when the collection is confirmed to be ingestible.
- **B-15:** **Validation Order Requirement**: The command MUST perform validations in the following strict order, failing fast at the first failure:
  1. **Collection Resolution**: Resolve `<collection_id>` to a collection (UUID, external ID, or name). Collection name matching MUST be case-insensitive. If collection is not found, exit with code 1 immediately. If multiple collections match the provided name (case-insensitive), exit with code 1 and emit: "Multiple collections named '<name>' exist. Please specify the UUID." Resolution MUST NOT prefer one collection over another, even if one has exact casing match.
  2. **Prerequisite Validation**: Check `ingestible=true` (and `sync_enabled=true` for full ingest). If prerequisites fail, exit with code 1 immediately. Prerequisite validation MUST NOT proceed if collection resolution failed.
  3. **Scope Resolution**: If targeted ingest flags (`--title`, `--season`, `--episode`) are provided, resolve the scope within the collection. If scope cannot be resolved (title/season/episode not found), exit with code 2. Scope resolution MUST NOT proceed if prerequisite validation failed.
- **B-16:** Duplicate detection MUST prevent creating a second Asset record for the same canonical identity (as determined by the importer's identity logic). If an asset with the same canonical identity already exists, the system MUST identify it as an existing asset and evaluate whether an update is needed. Duplicate detection MUST operate silently as part of normal ingest flow—existing assets are identified and processed for updates or skips, not treated as errors.
- **B-17:** When an existing asset is identified during ingest, the system MUST check if the asset's content has changed (via content hash, modification time, or importer-provided change detection). If content has not changed AND enrichers have not changed since last ingest, the asset MUST be skipped (counted in `assets_skipped`).
- **B-18:** When an existing asset is identified and either (a) content has changed OR (b) collection enrichers have changed since the asset was last ingested, the asset MUST be re-ingested (counted in `assets_updated`). Re-ingestion MUST update the existing asset record without creating a duplicate.
- **B-19:** Upon successful completion of ingest (even if all assets were skipped), the collection's `last_ingest_time` field MUST be updated to the current timestamp. This timestamp MUST be recorded atomically within the same transaction as asset updates.
- **B-20:** The output (both human-readable and JSON) MUST include statistics distinguishing between new assets (`assets_ingested`), skipped assets (`assets_skipped`), and updated assets (`assets_updated`).
- **B-21:** When `--json` is supplied, output MUST include `"last_ingest_time"` field showing the timestamp of the completed ingest operation.

---

### Data Contract

#### Data Contract Rules (D-#)

- **D-1:** The entire collection ingest operation MUST be wrapped in a single Unit of Work, following Unit of Work principles. If a fatal error occurs before successful completion, no assets, relationships, or side effects from that ingest run may persist.
- **D-2:** Ingest MUST only touch records reachable under the chosen scope: whole collection ingest may scan all titles; title ingest MUST NOT scan other titles; season ingest MUST NOT scan other seasons; episode ingest MUST ingest at most one logical episode.
- **D-3:** For full collection ingest, both `sync_enabled=true` AND `ingestible=true` MUST be validated before any ingest operation begins. If either condition is false, the operation MUST NOT proceed (exit code 1) unless `--dry-run` is provided.
- **D-4:** For targeted ingest (title/season/episode), `ingestible=true` MUST be validated before any ingest operation begins, but `sync_enabled=false` MAY be bypassed. This allows surgical operations on collections that are not enabled for bulk sync.
- **D-4a:** **Validation Order Enforcement**: Validation MUST occur in strict order: (1) Collection resolution, (2) Prerequisite validation (`ingestible`, `sync_enabled`), (3) Scope resolution (title/season/episode). Each validation step MUST complete successfully before proceeding to the next step. If prerequisite validation fails (exit code 1), scope resolution MUST NOT be attempted. This ensures that scope resolution errors (exit code 2) only occur when the collection exists and meets prerequisites.
- **D-5:** The `ingestible` field MUST be validated by calling the importer's `validate_ingestible()` method before any ingest operation. This validation MUST occur regardless of whether collection ingest is called directly or via source ingest.
- **D-5a:** The importer MUST be used solely for asset enumeration and discovery. The importer's `enumerate_assets()` method MUST return normalized asset descriptions (normalized Asset data) and MUST NOT perform any database writes or persistence operations. Importers MUST NOT directly persist to authoritative database tables.
- **D-5b:** All database persistence operations (Asset creation, updates, collection state updates) MUST be performed by the ingest service layer within Unit of Work transaction boundaries. The service layer is responsible for processing normalized asset data returned by the importer and persisting it to the database.
- **D-5c:** **Validation Before Enumeration**: The importer's `validate_ingestible()` method MUST be called BEFORE any call to `enumerate_assets()` or any other ingest work. If `validate_ingestible()` returns `false`, the command MUST exit with code 1 (or allow `--dry-run` preview per B-11/B-12 rules) and MUST NOT call `enumerate_assets()`. This ensures that asset enumeration only occurs when the collection is confirmed to be ingestible.
- **D-6:** If `ingestible=false`, the collection MUST NOT be ingested, regardless of `sync_enabled` status. The `ingestible` flag is the authoritative gate for all ingest operations.
- **D-7:** All ingest operations MUST run inside a single transaction boundary when running against the test DB (`--test-db`), and MUST roll back on error.
- **D-7a:** When both `--dry-run` and `--test-db` are provided, `--dry-run` takes precedence. No database writes may occur (neither production nor test database), but the command MUST still use the test DB context for resolution and validation. The command MUST verify that production databases were not accessed or modified.
- **D-8:** The ingest process MUST record enough metadata to know what scope was ingested (collection/title/season/episode) for audit and future debugging.
- **D-9:** Duplicate detection logic MUST prevent the creation of a second Asset record for the same canonical identity within the collection. Canonical identity MUST be determined by the importer's identity resolution logic (typically `external_id` + `collection_id`, but may include additional fields like `file_path` for filesystem sources).
- **D-10:** For existing assets identified during ingest, the system MUST compare the asset's content signature (hash, modification time, or importer-provided change detection) with the previous ingest signature. If signatures match AND the collection's enricher configuration has not changed since the asset was last ingested, the asset MUST be skipped.
- **D-11:** For existing assets where content has changed OR collection enrichers have changed since last ingest, the asset MUST be re-ingested. Re-ingestion MUST update the existing asset record (metadata refresh, enricher re-application) rather than creating a new record.
- **D-12:** To detect enricher changes requiring re-ingestion, the system MUST compare the current collection enricher configuration (enricher IDs and priorities) with the enricher configuration that was active when each asset was last ingested. This comparison MUST occur per-asset during the ingest process. The system MUST store or derive the enricher configuration that was active when each asset was last ingested (e.g., via asset metadata, enricher configuration snapshot, or comparison timestamp).
- **D-13:** Every new Asset (not existing) MUST begin in lifecycle state `new` and MUST NOT be in `ready` state at creation time. If enrichers are attached to the collection, assets MAY transition through `enriching` state during active enrichment processing, but MUST NOT remain in `enriching` state after enrichment completes.
- **D-14:** Updated assets (re-ingested due to content or enricher changes) MUST have their lifecycle state reset to `new` if they were previously in `ready` state. If enrichers are attached to the collection, assets MAY transition through `enriching` state during active enrichment processing, but MUST NOT remain in `enriching` state after enrichment completes.
- **D-15:** The collection's `last_ingest_time` field MUST be updated atomically within the same transaction as asset creation/updates. This update MUST occur only on successful completion of the ingest operation.
- **D-16:** The `last_ingest_time` update MUST occur regardless of whether any assets were actually ingested, updated, or skipped. Even if all assets are skipped, the timestamp MUST be updated to reflect that an ingest operation was attempted/completed.
- **D-17:** Asset update timestamps (e.g., `asset.updated_at`) MUST be refreshed when assets are re-ingested due to content or enricher changes, allowing the system to track when assets were last processed.
- **D-18:** All operations run with `--test-db` MUST be isolated from production database storage, tables, and triggers.

---

## Test Coverage Mapping

- **B-1..B-21** → `test_collection_ingest_contract.py`
- **D-1..D-2, D-7..D-8, D-18** → `test_collection_ingest_data_contract.py`
- **D-3..D-6, D-4a, D-5a..D-5c** → `test_collection_ingest_data_contract.py` (prerequisite validation rules, validation order, and importer/service separation)
- **D-9..D-17** → `test_collection_ingest_data_contract.py` (duplicate detection, incremental sync, and re-ingestion rules)
- **B-7, B-10, B-10a, D-7, D-7a, D-18** → `test_collection_ingest_data_contract.py` (dry-run and test-db isolation rules)
- **B-14a, D-5c** → `test_collection_ingest_data_contract.py` (validation before enumeration - Phase 1 testable)

Each rule above MUST have explicit test coverage in its respective test file, following the contract test responsibilities in [README.md](./README.md).  
Each test file MUST reference these rule IDs in docstrings or comments to provide bidirectional traceability.

Future related tests (integration or scenario-level) MAY reference these same rule IDs for coverage mapping but must not redefine behavior.

---

## Examples

### Full Collection Ingest

```bash
# Ingest entire collection
retrovue collection ingest "TV Shows"

# Ingest with JSON output
retrovue collection ingest "TV Shows" --json

# Test collection ingest
retrovue collection ingest "TV Shows" --test-db --dry-run

# Dry-run with test-db (dry-run takes precedence)
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" --season 1 --test-db --dry-run
# Success: Exit code 0, no database writes (neither production nor test),
# but test DB context used for resolution and validation, output well-formed
```

### Title Ingest

```bash
# Ingest specific title (all seasons)
retrovue collection ingest "TV Shows" --title "The Big Bang Theory"

# Ingest title with JSON output
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" --json

# Dry-run title ingest
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" --dry-run
```

### Season Ingest

```bash
# Ingest specific season
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" --season 1

# Ingest season with JSON output
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" --season 1 --json
```

### Episode Ingest

```bash
# Ingest specific episode
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" --season 1 --episode 6

# Ingest episode with JSON output
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" --season 1 --episode 6 --json
```

### Error Cases

```bash
# Invalid: season without title
retrovue collection ingest "TV Shows" --season 1
# Error: --season requires --title

# Invalid: episode without season
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" --episode 6
# Error: --episode requires --season

# Invalid: non-existent title
retrovue collection ingest "TV Shows" --title "Non-existent Show"
# Error: Title 'Non-existent Show' not found in collection 'TV Shows'

# Invalid: ambiguous collection name
retrovue collection ingest "Movies"
# Error: Multiple collections named 'Movies' exist. Please specify the UUID.

# Valid: use ID to disambiguate
retrovue collection ingest 4b2b05e7-d7d2-414a-a587-3f5df9b53f44
# Success: Uses UUID to identify collection uniquely

# Invalid: full collection ingest on sync-disabled collection
retrovue collection ingest "TV Shows"
# Error: Collection 'TV Shows' is not sync-enabled. Use targeted ingest (--title/--season/--episode) for surgical operations, or enable sync with 'retrovue collection update <id> --enable-sync'.

# Invalid: full collection ingest on non-ingestible collection
retrovue collection ingest "TV Shows"
# Error: Collection 'TV Shows' is not ingestible. Check path mappings and prerequisites with 'retrovue collection show <id>'.

# Invalid: targeted ingest on non-ingestible collection
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" --season 1
# Error: Collection 'TV Shows' is not ingestible. Check path mappings and prerequisites with 'retrovue collection show <id>'.
# Exit code: 1
# Note: Scope resolution (title/season) is NOT attempted because prerequisite validation failed

# Invalid: Collection not found, but scope flags provided
retrovue collection ingest "Nonexistent Collection" --title "The Big Bang Theory" --season 1
# Error: Collection 'Nonexistent Collection' not found.
# Exit code: 1
# Note: Prerequisite validation and scope resolution are NOT attempted because collection resolution failed

# Invalid: Scope resolution failure (title not found)
retrovue collection ingest "TV Shows" --title "Nonexistent Show" --season 1
# Error: Title 'Nonexistent Show' not found in collection 'TV Shows'
# Exit code: 2
# Note: Collection exists and meets prerequisites, but title cannot be resolved

# Valid: targeted ingest bypasses sync_enabled=false (but still requires ingestible=true)
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" --season 1
# Success: Surgical operation allowed even though sync is disabled

# Scenario: Re-ingest after adding enricher
retrovue collection update "TV Shows" --add-enricher enricher-metadata-1 --priority 2
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" --season 1
# Success: Existing assets re-ingested to apply new enricher
# Stats: assets_discovered: 17, assets_ingested: 0, assets_updated: 17, assets_skipped: 0

# Scenario: Incremental sync (content unchanged)
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" --season 1
# Success: Content unchanged since last ingest, assets skipped
# Stats: assets_discovered: 17, assets_ingested: 0, assets_updated: 0, assets_skipped: 17

# Scenario: Content changed (new episode added)
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" --season 1
# Success: New episode detected and ingested
# Stats: assets_discovered: 18, assets_ingested: 1, assets_updated: 0, assets_skipped: 17
```

---

## End-to-End Workflow Example

The following workflow demonstrates the complete collection ingest lifecycle:

### Step 1: Add Source

```bash
retrovue source add --type plex --name "My Plex Server" \
  --base-url "https://plex.example.com" --token "your-token"
```

### Step 2: Discover Collections

```bash
retrovue source discover "My Plex Server"
# Creates collections with sync_enabled=false and ingestible=false
```

### Step 3: List Collections

```bash
retrovue collection list --source "My Plex Server"
# Shows discovered collections, their sync_enabled and ingestible status
```

### Step 4: Configure Path Mappings

```bash
retrovue collection update "TV Shows" --path-mapping /media/tv-shows
# Sets local path, triggers ingestible revalidation
```

### Step 5: Add Enrichers

```bash
retrovue collection update "TV Shows" --add-enricher enricher-ffprobe-1 --priority 1
retrovue collection update "TV Shows" --add-enricher enricher-metadata-2 --priority 2
```

### Step 6: Enable Collection

```bash
retrovue collection update "TV Shows" --enable-sync
# Requires ingestible=true (validated in step 4)
```

### Step 7: Ingest Specific Episode

```bash
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" \
  --season 1 --episode 6
# Targeted ingest bypasses sync_enabled requirement
# Updates last_ingest_time for collection
```

### Step 8: Ingest Specific Season

```bash
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" --season 1
# Ingest entire season, skipping unchanged episodes
# Updates last_ingest_time for collection
```

### Step 9: Ingest Specific TV Show

```bash
retrovue collection ingest "TV Shows" --title "The Big Bang Theory"
# Ingest all seasons/episodes for the show
# Updates last_ingest_time for collection
```

### Step 10: Ingest Entire Collection

```bash
retrovue collection ingest "TV Shows"
# Requires sync_enabled=true AND ingestible=true
# Skips unchanged assets, updates changed assets, re-ingests if enrichers changed
# Updates last_ingest_time for collection
```

### Step 11: Re-ingest After Enricher Changes

```bash
retrovue collection update "TV Shows" --add-enricher enricher-llm-3 --priority 3
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" --season 1
# Detects enricher change, re-ingests existing assets to apply new enricher
# Stats show: assets_updated: 17, assets_skipped: 0
```

---

## See Also

- [Unit of Work](../_ops/UnitOfWorkContract.md) - Transaction management requirements for atomic operations
- [Source Ingest](SourceIngestContract.md) - Source-level orchestration that iterates over collections meeting both `sync_enabled=true` AND `ingestible=true`, calling collection ingest for each eligible collection
- [Source Discover](SourceDiscoverContract.md) - Collection discovery operations
- [Collection Update](CollectionUpdateContract.md) - Managing collection configuration, enrichers, and path mappings
- [Collection List](CollectionListContract.md) - Listing collections
- [Collection Show](CollectionShowContract.md) - Viewing collection details

---
