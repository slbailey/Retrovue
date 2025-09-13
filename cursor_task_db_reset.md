# Cursor Task: Wipe Database History and Recreate Fresh v1.1 Schema

**Goal**: Remove ALL prior database work (migrations, alembic, legacy schemas), and initialize a brand‑new SQLite database from the v1.1 schema. No migrations; clean create only.

## Hard Requirements
- Delete/ignore all old migration tooling and files.
- Create a **new** SQLite file from `sql/retrovue_schema_v1.1.sql` (no migration framework).
- Provide `make` targets and scripts to recreate the DB deterministically.
- Do **not** attempt to auto-migrate or reuse any tables/data.

## Deliverables (create/update these in the repo)
1. `sql/retrovue_schema_v1.1.sql` — authoritative schema (no diffs/migrations).
2. `scripts/db_reset.sh` — nukes old DB and applies schema (Linux/macOS).
3. `scripts/db_reset.py` — cross‑platform Python version of the same.
4. `Makefile` targets: `db-reset`, `db-create`.
5. `docs/README_DB_RESET.md` — concise instructions and safety notes.

## Implementation Details

### 1) Remove old DB and migration frameworks
- Delete the SQLite file(s), e.g. `data/retrovue.db`, `retrovue.db`.
- Remove **all** migration artifacts:
  - `alembic.ini`, `alembic/` and any `migrations/` folders
  - any custom migration scripts/tools
- Remove migration dependencies from the project (pyproject/requirements).

### 2) Wire up schema
- Create `sql/retrovue_schema_v1.1.sql` and treat it as the **single source of truth**.
- The `db_reset.sh` script must:
  - read `DB_PATH` (default `data/retrovue.db`)
  - ensure parent dir exists
  - delete any existing DB
  - run: `sqlite3 "$DB_PATH" < sql/retrovue_schema_v1.1.sql`
- Provide a Python fallback (`db_reset.py`) that does the same via `sqlite3` module.

### 3) Makefile
- `DB_PATH ?= data/retrovue.db`
- `SCHEMA ?= sql/retrovue_schema_v1.1.sql`
- `db-create`: creates parent dir and runs sqlite3 to apply schema if DB missing
- `db-reset`: force delete DB and run schema
- Guard: print a warning if `$(DB_PATH)` looks like a production path

### 4) CI Hygiene
- Ensure CI uses `make db-reset` before tests that require a DB.
- Cache nothing related to the DB between runs.

## Acceptance Criteria
- Running `make db-reset` produces a brand‑new DB matching the v1.1 schema.
- The project runs without any migration framework present.
- No code references alembic/migrations remain.

## Files to import from the user (drop into repo)
- Attach these files content exactly as provided by the user:
  - `sql/retrovue_schema_v1.1.sql` (authoritative schema)
  - `scripts/db_reset.sh`
  - `scripts/db_reset.py`
  - `docs/README_DB_RESET.md`
