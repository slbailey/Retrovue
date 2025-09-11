
# Plex Integration — Step‑by‑Step Fix Checklist (Cursor-Friendly)

> Purpose: small, bite‑sized tasks Cursor can confidently implement. Do them **in order**. Check each box as you complete it.

---

## Phase 0 — Safety & Setup

- [ ] Create a new git branch: `fix/plex-sync-gotchas`.
- [ ] Run tests (or a dry run) to capture current behavior.
- [ ] Enable verbose logging locally (so you can see status/debug messages).

---

## 1) Make `updated_at` an **INTEGER epoch** for **movies**

**Why:** Mixed types (INTEGER vs TIMESTAMP) break equality checks. We standardize on Plex epoch seconds (int).

**Files:** `database.py` (migrations/DDL)

**Steps**
- [ ] Create a migration that rebuilds the `movies` table with `updated_at INTEGER` (no default).
- [ ] Copy data over, converting any string/TIMESTAMP to epoch int.
- [ ] Drop old table and rename the new one.

**Diff skeleton (guide for Cursor)**
```python
# database.py — add a migration similar to the 'shows' pattern
def migrate_movies_updated_at_to_integer(self, conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movies_new (
            id INTEGER PRIMARY KEY,
            guid TEXT UNIQUE,
            title TEXT,
            year INTEGER,
            rating TEXT,
            updated_at INTEGER,              -- <- integer epoch (no default)
            source TEXT,
            server_id TEXT
        );
    """)
    # copy/convert
    cur.execute("""
        INSERT INTO movies_new (id, guid, title, year, rating, updated_at, source, server_id)
        SELECT id, guid, title, year, rating,
               CASE
                   WHEN typeof(updated_at) = 'integer' THEN updated_at
                   WHEN CAST(updated_at AS TEXT) GLOB '[0-9]*' THEN CAST(updated_at AS INTEGER)
                   ELSE CAST(strftime('%s', updated_at) AS INTEGER)
               END AS updated_at,
               source, server_id
        FROM movies;
    """)
    cur.execute("DROP TABLE movies;")
    cur.execute("ALTER TABLE movies_new RENAME TO movies;")
    conn.commit()
```
**Acceptance**
- [ ] Schema shows `movies.updated_at` is `INTEGER` with no default.
- [ ] Existing rows have integer `updated_at` values.

---

## 2) Add timestamp helpers (single source of truth)

**Why:** Normalize Plex/DB timestamps once; avoid scattered parsing logic.

**Files:** `plex_integration.py`

**Steps**
- [ ] Add:
```python
def plex_ts(item: dict) -> int | None:
    v = item.get('updatedAt') or item.get('addedAt')
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None

def db_ts_to_int(v) -> int | None:
    if v is None: return None
    if isinstance(v, int): return v
    s = str(v)
    if s.isdigit(): return int(s)
    from datetime import datetime
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return int(datetime.strptime(s, fmt).timestamp())
        except ValueError:
            pass
    return None
```
- [ ] Replace ad‑hoc conversions with these functions.

**Acceptance**
- [ ] All timestamp reads use `plex_ts(...)` or `db_ts_to_int(...)`.

---

## 3) Movies: **compare before update** using list endpoints only

**Why:** Avoid unnecessary API calls & DB writes if the metadata hasn't changed.

**Files:** `plex_integration.py`

**Steps**
- [ ] In your movie sync loop, obtain `ts = plex_ts(movie_item)`.
- [ ] Get `db_ts = db.get_movie_ts_by_guid(guid)` (or equivalent helper).
- [ ] If `db_ts is not None and ts == db_ts` → **skip** update/import.
- [ ] Only call `_update_movie(...)` or `import_movie(...)` if **new** or **ts changed**.

**Diff skeleton**
```python
# inside movies sync loop
ts = plex_ts(movie)
db_ts = db.get_movie_ts_by_guid(movie.get('guid'))
if db_ts is not None and ts is not None and ts == db_ts:
    # no-op if unchanged
    continue
# else proceed to import/update
```

**Acceptance**
- [ ] Sync logs show many items skipped when timestamps match.
- [ ] Total API calls drop; DB writes occur only on changes.

---

## 4) Episodes (and Shows): **compare before update**

**Why:** Same as movies; `/allLeaves` entries contain timestamps.

**Files:** `plex_integration.py`

**Steps**
- [ ] In episode sync paths, compare `plex_ts(episode)` to the DB value by GUID (or compound key) **before** writing.
- [ ] Only write when **new** or **ts changed**.
- [ ] Keep your season‑fallback for when `/allLeaves` fails, but still compare timestamps there too.

**Acceptance**
- [ ] Episode imports/updates only happen on deltas.
- [ ] Full library sync is notably faster on subsequent runs.

---

## 5) Harden JSON/XML handling for Plex endpoints

**Why:** Some Plex servers ignore `Accept: application/json` and return XML.

**Files:** `plex_integration.py` (HTTP GET helpers/parsers)

**Steps**
- [ ] After each request, check `Content-Type` header.
- [ ] If JSON → `response.json()`; if XML → parse XML (use a small utility function) and convert to dict‑like structures you rely on.
- [ ] Emit a debug message showing which format was parsed.

**Acceptance**
- [ ] Sync succeeds against servers that return XML.
- [ ] No crashes at `response.json()` with XML payloads.

---

## 6) Fix path map JOIN (avoid wrong local path)

**Why:** Current `LEFT JOIN ... ON 1=1` can pick a wrong mapping when multiple servers/roots exist.

**Files:** `database.py` (helper `get_local_path_for_media_file`)

**Steps**
- [ ] Join on `server_id` at minimum: `mf.server_id = ppm.server_id`.
- [ ] Optionally also match `library_root` if available.
- [ ] If multiple candidates remain, pick **longest prefix** match on `plex_path`.

**Acceptance**
- [ ] Files resolve to the expected local paths per server/root.
- [ ] No more “first row wins” behavior.

---

## 7) Clarify & store **Plex path vs Local path**

**Why:** Docs say `media_files.file_path` is local, but code stores Plex path. That confuses downstream consumers.

**Files:** `database.py`, `plex_integration.py`, docs

**Steps** (pick one strategy)
- **Option A (recommended):** Keep existing `file_path` as **local_path**, and add a new `plex_path` column. Populate both at import/update time.
- **Option B:** Keep `file_path` as **plex_path** and add `local_path`. Update docs accordingly.

**Acceptance**
- [ ] One column is clearly Plex path, one is local path.
- [ ] Mapping service is used consistently to derive `local_path`.

---

## 8) Orphan cleanup must be **server‑scoped**

**Why:** Prevent deleting content that exists on another Plex server.

**Files:** `database.py`/`plex_integration.py` (or wherever orphaning is performed)

**Steps**
- [ ] Filter by `server_id` in all queries that gather candidates for orphan deletion.
- [ ] Compare GUIDs only within the same `server_id`.

**Acceptance**
- [ ] Orphan cleanup leaves content from other servers untouched.
- [ ] Logs explicitly note the `server_id` used during cleanup.

---

## 9) Ratings: default to **'NR'** (not rated)

**Why:** Mapping `'Not Rated' → 'PG-13'` is misleading.

**Files:** `plex_integration.py` (rating mapping)

**Steps**
- [ ] Change default to `'NR'`.
- [ ] Map `'Not Rated'` and unknowns to `'NR'`.
- [ ] Preserve original rating in a raw field if needed for UI.

**Acceptance**
- [ ] No content is silently up‑rated to PG‑13.

---

## 10) Multiple library roots: choose the **correct** one

**Why:** You currently pick `library_root_paths[0]`, which fails when a library has multiple locations.

**Files:** `plex_integration.py` (where `primary_library_root` is set)

**Steps**
- [ ] Build a list of library roots from Plex.
- [ ] For each media item, select the root with the **longest matching prefix** against the item’s Plex path.
- [ ] Pass that chosen root into mapping logic.

**Acceptance**
- [ ] Files in non‑primary roots map correctly.

---

## 11) Pagination for large `/allLeaves` responses

**Why:** Very large libraries may require container pagination.

**Files:** `plex_integration.py` (episode retrieval)

**Steps**
- [ ] Detect container size vs total. If partial, paginate using `X-Plex-Container-Start`/`X-Plex-Container-Size` (or query params).
- [ ] Merge pages before processing.
- [ ] Maintain timestamp compare on each page.

**Acceptance**
- [ ] All episodes are discovered/imported in very large shows.

---

## 12) Don’t swallow exceptions — surface them to logs/status

**Why:** Silent `except Exception: return False/[]` makes triage painful.

**Files:** `plex_integration.py`

**Steps**
- [ ] Replace bare `except` blocks with logging to your `_emit_status(..., debug_only=True)` or a logger.
- [ ] Re‑raise critical failures where appropriate; return structured errors otherwise.

**Acceptance**
- [ ] Failures show actionable messages in logs.
- [ ] Cursor can reason about precise failure points.

---

## 13) Single source of truth for path mapping

**Why:** DB helper and `PlexPathMappingService` both try to map paths; they can disagree.

**Files:** `database.py`, `plex_integration.py`

**Steps**
- [ ] Route all path resolution through `PlexPathMappingService`.
- [ ] If a DB helper remains, make it call the service (don’t duplicate logic).

**Acceptance**
- [ ] Only one code path maps Plex→local, covered by tests.

---

## 14) Docs vs code: align on the timestamp field name

**Why:** Docs mention `plex_updated_at`; code uses `updated_at` for Plex’s timestamp. Ambiguity causes mistakes.

**Files:** `PLEX_INTEGRATION_DOCUMENTATION.md`

**Steps**
- [ ] Decide: keep `updated_at` as “Plex epoch seconds” **or** rename to `plex_updated_at`.
- [ ] Update docs to match the code and schema, including type (INTEGER epoch).

**Acceptance**
- [ ] Documentation clearly states the single timestamp field and its type.

---

## Final Validation

- [ ] Run a full “sync all libraries” twice. On the second run, verify:
  - [ ] Minimal/no DB writes for unchanged items.
  - [ ] API call count is reduced (no per‑item detail fetch unless changed).
  - [ ] Orphan cleanup is server‑safe.
  - [ ] Logs are clear on format (JSON/XML), mapping decisions, and skips.

---

### Optional test ideas (nice to have)
- Unit tests for `plex_ts`, `db_ts_to_int`.
- Path‑mapping tests with multiple servers and roots.
- Parsing tests for JSON vs XML payloads.
