
# Plex Integration — Follow‑Up Fix Checklist (Cursor‑Friendly)

> Purpose: finish the remaining “gotchas” with small, focused tasks. Do them **in order**. Each task has clear acceptance criteria and a minimal code skeleton Cursor can expand.


---

## Phase 0 — Safety & Prep

- [ ] Create a new branch: `fix/plex-sync-followups`.
- [ ] Enable verbose logging.
- [ ] Run one baseline full sync to have reference logs/counters.


---

## 1) Normalize timestamp comparisons everywhere (movies/shows/episodes)

**Why:** Avoid false mismatches by comparing **epoch ints** only and persist the new value after updates.

**Files:** `plex_integration.py` (+ tiny DB getters if missing)

**Steps**
- [ ] Ensure these helpers exist (add if missing and import where used):
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
- [ ] **Movies:** before calling `_update_movie` or `import_movie`, compute `ts = plex_ts(movie)` and `db_ts = db.get_movie_ts_by_guid(guid)` → **skip** if equal.
- [ ] Inside `_update_movie(...)` (and any show/episode update paths), re-check with the helpers and, on success, **write back** the new `updated_at` (epoch int).

**Acceptance**
- [ ] On a second sync, unchanged items are **skipped** before any DB writes.
- [ ] After a real update, the DB row’s `updated_at` equals Plex’s epoch int.


---

## 2) Robust Plex parsing: JSON **or** XML everywhere

**Why:** Some servers return XML even when you request JSON. Avoid crashes at `response.json()`.

**Files:** `plex_integration.py`

**Steps**
- [ ] Add a single parser utility and route all Plex responses through it:
```python
import xmltodict

def parse_plex_response(resp):
    ctype = (resp.headers.get("Content-Type") or "").lower()
    text = resp.text or ""
    if "json" in ctype:
        return resp.json()
    if "xml" in ctype or text.strip().startswith("<"):
        return xmltodict.parse(text)
    raise ValueError(f"Unsupported Plex response format: {ctype}")
```
- [ ] Replace direct `.json()` calls in:
  - `get_libraries`
  - `get_library_root_paths`
  - `get_library_items` (all types)
  - `get_show_episodes` (and any `/allLeaves` fetches)
  - any other Plex GET helpers
- [ ] Emit a debug log telling which format was parsed for easier triage.

**Acceptance**
- [ ] Sync succeeds against servers returning XML.
- [ ] No `JSONDecodeError` where XML is returned.


---

## 3) Make orphan cleanup **server‑scoped**

**Why:** Prevent deleting content that still exists on another Plex server.

**Files:** `plex_integration.py` (+ `database.py` if you need server‑filtered getters)

**Steps**
- [ ] When building in‑memory GUID sets from Plex, keep them **per `server_id`**.
- [ ] When querying DB candidates to delete, **filter by `server_id`** (e.g., `get_movies_by_source_and_server('plex', server_id)`), or filter results before comparing.
- [ ] Perform deletions only within the same `server_id` context.

**Acceptance**
- [ ] Running sync against Server A does not remove items that exist on Server B.
- [ ] Logs explicitly mention the `server_id` during orphan cleanup.


---

## 4) Store **plex_path** and **local file_path** correctly

**Why:** Avoid mixing raw Plex paths with mapped local paths.

**Files:** `plex_integration.py`, `database.py`

**Steps**
- [ ] In import/update for movies and episodes:
```python
plex_path = extracted_plex_file_path  # from the Plex media part
local_path = mapping_service.map_to_local(plex_path, primary_library_root, server_id)

# When saving the media file row:
add_or_update_media_file(
    file_path=local_path,   # local OS path
    plex_path=plex_path,    # raw Plex path as reported
    server_id=server_id,
    ... # other fields
)
```
- [ ] If the `media_files.plex_path` column is missing, add a migration to create it (TEXT, nullable) and backfill from current data if needed.

**Acceptance**
- [ ] New/updated rows have **both** `plex_path` (raw) and `file_path` (local) set correctly.
- [ ] Downstream code reads local path from `file_path` only.


---

## 5) Persist new timestamps on successful updates

**Why:** Ensure DB reflects the latest Plex metadata time after any change.

**Files:** `plex_integration.py`, `database.py`

**Steps**
- [ ] After `_update_movie(...)` (and analogous episode/show updates) completes successfully, update `updated_at` in the corresponding table to the **same epoch int** you compared earlier.
- [ ] Add/verify tiny DB helpers: `set_movie_ts_by_guid(guid, ts)`, `set_episode_ts_by_guid(...)`, etc.

**Acceptance**
- [ ] After a successful update, re‑reading the row shows `updated_at == plex_ts(item)`.


---

## 6) (Optional) Short‑circuit heavy show syncs

**Why:** Speed up reruns by skipping deep episode walks when nothing changed.

**Files:** `plex_integration.py`

**Steps**
- [ ] Before `_sync_show_episodes`, compare show‑level `plex_ts(show)` vs DB and (optionally) a cached leaf count.
- [ ] If unchanged, **skip** the episode walk unless a “force deep” flag is set.

**Acceptance**
- [ ] On steady‑state libraries, second sync runs significantly faster without missing updates.


---

## 7) Log, don’t swallow (failure hygiene)

**Why:** Silent `except: return False/[]` blocks hide real problems.

**Files:** `plex_integration.py`

**Steps**
- [ ] Replace bare `except` blocks with:
  - Logging the exception via your status/debug logger, and
  - Returning a structured error or re‑raising for truly fatal paths.
- [ ] Keep the change minimal — don’t refactor logic, just surface errors.

**Acceptance**
- [ ] Failures now show actionable messages in logs.
- [ ] Cursor can locate exact failure points from logs alone.


---

## Final Validation

- [ ] Run a full “sync all libraries” twice. On the second run, verify:
  - [ ] Most items are **skipped** (timestamps match).
  - [ ] No XML→JSON parsing crashes.
  - [ ] Orphan cleanup logs show `server_id` and do not remove items from other servers.
  - [ ] Media file rows contain both `plex_path` and local `file_path`.
  - [ ] After any real updates, DB `updated_at` matches Plex epoch seconds.
- [ ] Commit: `git add -A && git commit -m "Follow‑up: timestamp normalization, XML parsing, server‑scoped cleanup, path semantics"`

