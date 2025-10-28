# Source Ingest

## Purpose

Defines the exact behavior, safety, idempotence, and data effects of the ingest operation for an entire source. This is an iterative operation that processes all enabled collections within a source, following the same pattern as Source Discover but for asset ingestion rather than collection discovery. All operations must use importers that implement the ImporterInterface correctly. Each collection ingest operates in its own transaction boundary, allowing for partial success when some collections fail.

NOTE: This command operates at the source level and iterates across all enabled collections, processing each collection's ingest operation. Each collection ingest follows the exact same process defined in the Collection Ingest, with each collection operating in its own transaction boundary to allow for partial success when some collections fail.

---

## Command Shape

**CLI Syntax:**

```
retrovue source ingest <source_id>|"<source name>" [--dry-run] [--test-db] [--json]
```

- `<source_id>`: The UUID or database identifier for the source to ingest
- `"source name"`: Human-friendly, quoted name for the source (alternative to ID)
- `--dry-run`: Show intended ingest actions without modifying the database
- `--test-db`: Direct all actions at the isolated test database environment
- `--json`: Output information in a structured JSON format for automation

**Scope Restrictions:**

- **BULK OPERATION ONLY**: This command operates at the source level and processes ALL enabled collections
- **NO COLLECTION-LEVEL NARROWING**: The command MUST NOT accept or forward any collection-level narrowing flags:
  - `--title`
  - `--season`
  - `--episode`
- **SURGICAL CONTROL**: For targeted ingest of specific titles/seasons/episodes, use `retrovue collection ingest <collection_id> [--title ... --season ... --episode ...]`

**Requirements:**

- The command MUST require either a source ID or exact source name
- Named lookup MUST support both human and machine workflows
- The command MUST iterate over all collections where `enabled=true` for the specified source

---

## Safety Expectations

- The command MUST refuse to run against a source that has no enabled collections
- The command MUST verify that the source exists and is accessible before attempting collection iteration
- **COLLECTION-LEVEL NARROWING FORBIDDEN**: If any collection-level narrowing flags (`--title`, `--season`, `--episode`) are provided, the CLI MUST refuse to run, exit with code 1, and emit a human-readable error directing the operator to use `retrovue collection ingest`
- If `--dry-run` is provided, the command MUST NOT make any database or persistent state changes, but MUST show what _would_ be ingested across all collections
- If `--test-db` is provided, the command MUST operate solely on an isolated, non-production database
- Partial or failed ingest operations across collections MUST NOT result in orphaned or incomplete database records
- By design, individual collection ingest failures MUST NOT abort the entire source ingest operation unless all collections fail
- Source's importer must be interface compliant (ImporterInterface). Implementations that subclass BaseImporter are considered compliant by construction. Non-compliant importers MUST cause the command to fail with exit code 1.
- Asset ingestion MUST use importer's enumeration capability for content discovery
- Interface compliance MUST be verified before ingest attempt

---

## Output Format

### Human-Readable Output

- Source identification and summary
- Total number of enabled collections found
- Per-collection ingest results:
  - Collection name and status
  - Number of assets created per collection
  - Number of assets skipped per collection
  - Number of duplicate candidates per collection
  - List and count of failed enrichments per collection
- Overall summary with total counts across all collections
- Summary line with clear status: `Success`, `Partial Success`, `Error: No enabled collections`, etc.
- EXAMPLE: Source ingest complete: 4 collections processed (3 success, 1 failed)

### JSON Output (if `--json` is provided)

- Top-level deterministic keys:
  - `"status"`: `"ok"` | `"partial"` | `"error"`
  - `"source"`: Source identification object
  - `"collections_processed"`: Number of collections processed
  - `"total_created_assets"`: Total assets created across all collections
  - `"total_skipped_assets"`: Total assets skipped across all collections
  - `"total_duplicates"`: Total duplicate candidates across all collections
  - `"collection_results"`: [array of per-collection result objects]
  - `"errors"`: [array of error objects/messages]
- Must include all the information from the human-readable output in a machine-consumable way.

---

## Exit Codes

- `0` — Success; all collections ingested successfully or (if `--dry-run`) actions listed with no errors.
- `1` — Validation failure (e.g., source not found, no enabled collections, mapping invalid).
- `2` — Partial success; some collections succeeded, some failed.
- `3` — External system unreachable (source location cannot be accessed).
- All non-zero exit codes MUST be accompanied by a clear error message in both human and JSON output.

---

## Data Effects

- For each enabled collection, the ingest process follows the exact same rules as defined in the [Collection Ingest](CollectionIngestContract.md).
- New Assets MUST be created with state = `new` or `enriching` per collection.
- Duplicate detection logic MUST prevent the creation of duplicate Asset records within each collection.
- Any enrichment hooks MAY run during ingest per collection, following the same per-asset failure handling.
- Assets created by this operation MUST NOT be marked as approved for broadcast automatically.
- **The entire source ingest operation MUST be wrapped in a Unit of Work, ensuring atomicity across all collections.**
- If any collection ingest fails fatally, the entire source ingest operation MUST be rolled back.
- Individual collection ingest failures (non-fatal) MUST NOT abort the entire source ingest operation.

---

## Behavior Contract

#### Behavior Contract Rules (B-#)

- **B-1:** The command MUST require `<source_id>` or exact `"source name"` as a positional argument.
- **B-2:** The command MUST iterate ingest across all collections belonging to `<source_id>` that are both `sync_enabled=true` AND `ingestible=true`.
- **B-3:** The command MUST NOT accept or forward any of the collection-level narrowing flags: `--title`, `--season`, `--episode`.
- **B-4:** If any collection-level narrowing flags (`--title`, `--season`, `--episode`) are provided, the CLI MUST refuse to run, exit with code 1, and emit the error message: "Per-title/season/episode ingest is only supported at the collection level. Use: retrovue collection ingest <collection_id> [--title ... --season ... --episode ...]"
- **B-5:** Source ingest MUST clearly summarize, in human-readable output and in `--json` mode, which collections were targeted and which were skipped (and why). Partial failures are allowed and MUST produce exit code 2.
- **B-6:** When run with `--dry-run`, the command MUST enumerate what would be ingested for each eligible collection but MUST NOT call actual ingest routines that mutate data.
- **B-7:** Output with `--json` MUST include `"status": "ok" | "partial" | "error"` and explicit per-collection results.
- **B-8:** When run with `--test-db`, no changes may affect production or staging databases.
- **B-9:** Individual collection ingest failures MUST NOT abort the entire source ingest operation unless all collections fail.
- **B-10:** Source's importer must be interface compliant (ImporterInterface). Implementations that subclass BaseImporter are considered compliant by construction. Non-compliant importers MUST cause the command to fail with exit code 1.
- **B-11:** For each eligible collection, the system MUST ask the importer to enumerate ingestable assets for that collection before ingest.
- **B-12:** Interface compliance MUST be verified before ingest attempt.

---

### Data Contract

#### Data Contract Rules (D-#)

- **D-1:** Each collection ingest MUST execute within its own Unit of Work / transaction boundary.
- **D-2:** A fatal error in one collection MUST roll back the ingest for that collection, but MUST NOT roll back successfully ingested sibling collections.
- **D-3:** The overall source ingest operation MUST still report partial success (exit code 2) if any collections failed.
- **D-4:** All per-collection ingests MUST be logged/audited with enough context to recover or retry failures.
- **D-5:** Source ingest MUST NOT ingest any collection whose `sync_enabled` is false OR `ingestible` is false, even if the collection would otherwise be eligible.
- **D-6:** Source ingest MUST invoke the same underlying ingestion pipeline that collection ingest uses for "full collection" mode (no `--title`/`--season`/`--episode`), but MUST call it in "full collection" scope only.
- **D-7:** All ingest operations triggered under source ingest MUST be tracked individually per collection in ingest logs/audit trails, distinguishing between bulk source ingest and manual surgical ingest.
- **D-8:** Duplicate detection logic MUST prevent the creation of duplicate Asset records within each collection, following the Collection Ingest.
- **D-9:** Every new Asset MUST begin in lifecycle state `new` or `enriching` and MUST NOT be in `ready` state at creation time, per collection.
- **D-10:** Importer interface compliance MUST be verified before ingest attempt.
- **D-11:** Asset discovery MUST use the importer's enumeration capability to retrieve the assets belonging to that collection, in full-collection mode.
- **D-12:** The ingestible field MUST be validated by calling the importer's ingestibility check before ingesting the collection.
- **D-13:** If `ingestible=false`, the collection MUST NOT be included in bulk ingest operations, even if `sync_enabled=true`.
- **D-14:** All operations run with `--test-db` MUST be isolated from production database storage, tables, and triggers.
- **D-15:** Source-level ingest MUST NOT create any source-level database records; all persistence occurs at the collection level.

---

## Test Coverage Mapping

- **B-1..B-9** → `test_source_ingest_contract.py`
- **D-1..D-14** → `test_source_ingest_data_contract.py`

Each rule above MUST have explicit test coverage in its respective test file, following the contract test responsibilities in [README.md](./README.md).  
Each test file MUST reference these rule IDs in docstrings or comments to provide bidirectional traceability.

Future related tests (integration or scenario-level) MAY reference these same rule IDs for coverage mapping but must not redefine behavior.

---

## Examples

### Valid Source Ingest Operations

```bash
# Ingest all enabled collections from a source
retrovue source ingest "My Plex Server"

# Ingest with JSON output
retrovue source ingest "My Plex Server" --json

# Dry-run source ingest
retrovue source ingest "My Plex Server" --dry-run

# Test source ingest
retrovue source ingest "My Plex Server" --test-db --dry-run
```

### Forbidden Operations (Will Fail)

```bash
# FORBIDDEN: Collection-level narrowing flags
retrovue source ingest "My Plex Server" --title "The Big Bang Theory"
# Error: Per-title/season/episode ingest is only supported at the collection level.
# Use: retrovue collection ingest <collection_id> [--title ... --season ... --episode ...]

# FORBIDDEN: Season flag
retrovue source ingest "My Plex Server" --season 1
# Error: Per-title/season/episode ingest is only supported at the collection level.

# FORBIDDEN: Episode flag
retrovue source ingest "My Plex Server" --episode 6
# Error: Per-title/season/episode ingest is only supported at the collection level.
```

### Correct Surgical Operations

```bash
# For targeted ingest, use collection ingest instead
retrovue collection ingest "TV Shows" --title "The Big Bang Theory"
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" --season 1
retrovue collection ingest "TV Shows" --title "The Big Bang Theory" --season 1 --episode 6
```

---

## Relationship to Collection Ingest

This Source Ingest builds upon and orchestrates the Collection Ingest:

- **Iteration**: Source ingest iterates across all enabled collections, similar to Source Discover
- **Unit of Work**: The entire source ingest operation is wrapped in a single Unit of Work
- **Atomicity**: All collection ingests occur within the same transaction boundary
- **Error Handling**: Fatal collection ingest failures abort the entire operation; non-fatal failures are logged but don't abort
- **Aggregation**: Source ingest aggregates results from multiple collection ingests into a unified output
- **Safety**: Source ingest maintains the same safety guarantees as collection ingest, applied across all collections atomically

All collection-level behavior, safety expectations, and data effects are inherited from the Collection Ingest and MUST be enforced for each collection processed by the source ingest operation.

---

## Examples

### Basic Source Ingest

```bash
# Ingest all enabled collections from a source
retrovue source ingest "My Plex Server"

# Ingest by source ID
retrovue source ingest plex-5063d926

# Ingest with JSON output
retrovue source ingest "My Plex Server" --json
```

### Dry-run Testing

```bash
# Preview ingest across all collections
retrovue source ingest "My Plex Server" --dry-run

# Test ingest logic
retrovue source ingest "Test Source" --test-db --dry-run
```

### Test Environment Usage

```bash
# Test source ingest in isolated environment
retrovue source ingest "Test Plex Server" --test-db
```

---

## Safety Guidelines

- Always use `--test-db` for testing source ingest logic
- Use `--dry-run` to preview ingest actions across all collections
- Verify source configuration and enabled collections before ingest
- Monitor per-collection results for partial failures
- Confirm source identification before ingest

---

## See Also

- [Unit of Work](../_ops/UnitOfWorkContract.md) - Transaction management requirements for atomic operations
- [Source Discover](SourceDiscoverContract.md) - Iterative collection discovery operations
- [Collection Ingest](CollectionIngestContract.md) - Individual collection ingest operations
