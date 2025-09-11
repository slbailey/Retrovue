
# Plex Integration — Checklist Phase 3 (Cursor-Friendly)

> Purpose: Clean up remaining runtime gotchas. Do these **in order**, one small step at a time.

---

## 1) Fix `library_root_paths` NameError in `import_movie`
- [ ] In `plex_integration.py`, update the call to `_get_local_path_from_plex_path` inside `import_movie`.
- [ ] Remove the undefined `library_root_paths` variable.
- [ ] Either:
  - Pass `[library_root] if library_root else []`, OR
  - Remove the second argument entirely if not used.

**Acceptance**
- [ ] `import_movie` runs without `NameError: name 'library_root_paths' is not defined`.

---

## 2) Make all inserts/updates epoch-only
- [ ] In `database.py` → `add_media_file`, replace `CURRENT_TIMESTAMP` with `int(time.time())` (epoch int).
- [ ] Keep only the `update_media_file` that sets `updated_at` to epoch int.
- [ ] Delete/replace the one using `CURRENT_TIMESTAMP` (string).

**Acceptance**
- [ ] Every row in `media_files`, `movies`, `shows`, `episodes` has `updated_at` as INTEGER epoch seconds.

---

## 3) Remove unused `library_root_paths` param
- [ ] In `plex_integration.py`, edit `_get_local_path_from_plex_path`:
  - Remove the `library_root_paths` parameter from its signature.
  - Update all calls (including `import_movie`) to not pass it.

**Acceptance**
- [ ] Function signatures and calls align, no unused params left.

---

## 4) Consolidate to one `plex_integration.py`
- [ ] Identify duplicate versions in the repo.
- [ ] Keep the one that has robust `parse_plex_response` (JSON+XML tolerant) and pagination.
- [ ] Delete or merge the simpler variant that only uses `response.json()`.

**Acceptance**
- [ ] Only one `plex_integration.py` exists, containing the JSON/XML parser and pagination logic.

---

## 5) Standardize movie import paths
- [ ] In `import_movie`, always set both:
  - `plex_path = Part[0].file` (from Plex XML/JSON)
  - `file_path = self.get_local_path(plex_path, library_root)` (mapped local path)
- [ ] In `add_media_file`, store both `plex_path` and `file_path` accordingly.

**Acceptance**
- [ ] DB rows for media files contain **both** raw Plex path (`plex_path`) and mapped local path (`file_path`).

---

## 6) Enforce timestamp compare on every update path
- [ ] Verify that all update flows (`_update_movie`, show sync, episode sync) use:
```python
plex_int = plex_ts(item)
db_int = db_ts_to_int(db_val)
if plex_int is not None and db_int is not None and plex_int <= db_int:
    skip_update()
```
- [ ] If any are missing, add the check.

**Acceptance**
- [ ] On second sync run, unchanged items are skipped without DB writes.

---

## 7) Add/verify server-scoped orphan cleanup
- [ ] In `sync_all_libraries`, collect Plex GUIDs **per server_id**.
- [ ] Query DB for items with `source_type='plex' AND server_id=?`.
- [ ] Delete only items that belong to that server and are missing from Plex.
- [ ] Cover both `movies` and `episodes` (CASCADE will handle children if FKs are set).

**Acceptance**
- [ ] Sync on one server does not delete items from another server.
- [ ] Logs show server_id in orphan cleanup steps.

---

## Final Validation
- [ ] Run two consecutive full syncs.
- [ ] Confirm that:
  - [ ] No NameError in `import_movie`.
  - [ ] All timestamps are epoch integers.
  - [ ] Only one version of `plex_integration.py` remains.
  - [ ] Media files have both `plex_path` and `file_path`.
  - [ ] Skips occur on unchanged items.
  - [ ] Orphan cleanup is server-scoped.

- [ ] Commit: `git add -A && git commit -m "Phase3: normalize timestamps, path fixes, orphan cleanup, parser consolidation"`
