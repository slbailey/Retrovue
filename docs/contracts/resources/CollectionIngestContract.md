# Collection Ingest Contract

## Purpose

Defines the exact behavior, safety, idempotence, and data effects of the ingest operation for a single collection. This is the "do the work" operation for populating new Assets from external sources within the RetroVue ingest pipeline.

NOTE: This command operates strictly on the collection level. While a "source" may contain multiple collections, a "collection ingest" targets only the enabled collection specified. "Source ingest" is a higher-level orchestration that triggers multiple collection ingests in sequence.

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

- The command MUST refuse to run against a collection that is not `sync_enabled=true` OR `ingestible=false` for full collection ingest
- Targeted ingest (title/season/episode) MAY run even if `sync_enabled=false` (surgical operator action)
- The command MUST verify that any required path mapping is both valid and known
- If `--dry-run` is provided, the command MUST NOT make any database or persistent state changes, but MUST show what _would_ be ingested
- If `--test-db` is provided, the command MUST operate solely on an isolated, non-production database
- Partial or failed ingest operations MUST NOT result in orphaned or incomplete database records
- The command MUST validate hierarchical flag dependencies (season requires title, episode requires both)

---

## Output Format

### Human-Readable Output

**Full Collection Ingest:**

```
Ingesting entire collection "TV Shows"
Discovered 128 titles, 2,931 assets
(...progress / summary...)
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
    "errors": []
  }
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
- If an incoming asset candidate matches an existing canonical identity, it MUST NOT be duplicated in the database
- Any enrichment hook MAY run during ingest
- Per-asset enrichment failure MUST NOT abort the entire ingest run
- Assets created by this operation MUST NOT be marked as approved for broadcast automatically
- **The entire collection ingest operation MUST be wrapped in a single Unit of Work, following Unit of Work principles**
- All ingest changes MUST be atomic—either all database changes for the ingest run are committed, or none are
- **Scope isolation**: Ingest MUST only touch records reachable under the chosen scope:
  - Whole collection: may scan all titles in that collection
  - Title ingest: MUST NOT scan other titles in the same collection
  - Season ingest: MUST NOT scan other seasons of the same title
  - Episode ingest: MUST ingest at most one logical episode
- **Audit metadata**: The ingest process MUST record scope information (collection/title/season/episode) for audit and debugging

---

### Behavior Contract

#### Behavior Contract Rules (B-#)

- **B-1:** The command MUST accept `<collection_id>` as any of: full UUID, external ID (e.g. Plex library key), or case-insensitive display name. If the name is ambiguous (multiple matches), the CLI MUST print a disambiguation table and exit with code 1.
- **B-2:** If no `--title` is provided, the command MUST ingest the entire collection.
- **B-3:** `--season` MUST NOT be provided unless `--title` is also provided. If violated, the CLI MUST exit with code 1 and a human-readable error.
- **B-4:** `--episode` MUST NOT be provided unless both `--title` and `--season` are provided. If violated, exit code MUST be 1.
- **B-5:** When `--json` is supplied, output MUST include: `"status"` ("success" or "error"), `"scope"` (one of: "collection", "title", "season", "episode"), `"collection_id"`, and `"stats"` (object with counts: assets_discovered, assets_ingested, assets_skipped, errors).
- **B-6:** The CLI MUST report exactly what scope it is acting on in human-readable mode (e.g., "Ingesting entire collection 'TV Shows'", "Ingesting title 'The Big Bang Theory' from collection 'TV Shows'").
- **B-7:** The command MUST support `--dry-run`. When `--dry-run` is present, NO database writes or file operations may occur, but the CLI MUST still resolve IDs and print what would be ingested.
- **B-8:** If the requested title/season/episode cannot be found in that collection, the command MUST exit with code 2 and say exactly what failed to resolve, still outputting valid JSON if `--json` was passed.
- **B-9:** If `--episode` is provided without an integer value, or a negative/non-integer is provided for `--season` or `--episode`, exit code MUST be 1 with "invalid argument" style messaging.
- **B-10:** When run with `--test-db`, no changes may affect production or staging databases.

---

### Data Contract

#### Data Contract Rules (D-#)

- **D-1:** The entire collection ingest operation MUST be wrapped in a single Unit of Work, following Unit of Work principles. If a fatal error occurs before successful completion, no assets, relationships, or side effects from that ingest run may persist.
- **D-2:** Ingest MUST only touch records reachable under the chosen scope: whole collection ingest may scan all titles; title ingest MUST NOT scan other titles; season ingest MUST NOT scan other seasons; episode ingest MUST ingest at most one logical episode.
- **D-3:** Ingest MUST respect collection sync rules: if the collection is not `sync_enabled=true` OR `ingestible=false`, a full-collection ingest MUST refuse to run (exit code 1) unless `--dry-run` was given. A targeted ingest (title/season/episode) MAY run even if `sync_enabled` is false.
- **D-4:** All ingest operations MUST run inside a single transaction boundary when running against the test DB (`--test-db`), and MUST roll back on error.
- **D-5:** The ingest process MUST record enough metadata to know what scope was ingested (collection/title/season/episode) for audit and future debugging.
- **D-6:** Duplicate detection logic MUST prevent the creation of a second Asset record for the same episode, file, or canonical identity within the collection.
- **D-7:** Every new Asset MUST begin in lifecycle state `new` or `enriching` and MUST NOT be in `ready` state at creation time.
- **D-9:** The `ingestible` field MUST be validated by calling the importer's `validate_ingestible()` method before any ingest operation.
- **D-10:** If `ingestible=false`, the collection MUST NOT be ingested, even if `sync_enabled=true`.
- **D-11:** All operations run with `--test-db` MUST be isolated from production database storage, tables, and triggers.

---

## Test Coverage Mapping

- **B-1..B-10** → `test_collection_ingest_contract.py`
- **D-1..D-11** → `test_collection_ingest_data_contract.py`

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
```

---

## See Also

- [Unit of Work](../_ops/UnitOfWorkContract.md) - Transaction management requirements for atomic operations
- [Source Ingest](SourceIngestContract.md) - Source-level orchestration of multiple collection ingests
- [Source Discover](SourceDiscoverContract.md) - Collection discovery operations

---
