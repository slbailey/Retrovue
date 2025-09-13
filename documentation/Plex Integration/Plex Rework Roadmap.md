# Retrovue – Plex Ingest (00–04)  
## Sync Design + Minimal UI Contract (GUI, on-demand)

**Scope:** Manual GUI tool; multi-server; per-library ingest; full coverage (shows→seasons→episodes→media parts, movies→media parts); robust adds/changes/deletes; dynamic per-server path mapping (no stored local path); clear item states; minimal UI refresh hooks.

**Files this doc touches**
- `database.py`  → new columns, state transitions, helpers
- `plex_integration.py` → selective expansion, digests, progress emits
- `path_mapping.py` → dynamic resolver (no persisted local paths)
- `main_window.py` → connect minimal UI signals (no new screens)
- *(optional small new)* `ui_bus.py` → Qt signals hub

---

## 00 — Change Detection & Minimal-Work Fullness

### Goals
- Import all levels but **touch only changed items** on normal runs.
- Detect **adds / changes / deletes** reliably.
- **Incremental scan** rarely expands episodes unless a show changed.

### Core idea: digests
- **Episode/Movie digest** = hash of:  
  `ratingKey | updatedAt | duration | file_size | part_count | streams_signature | guid_primary`
- **Show digest** = hash of:  
  `child_count | leaf_count | max(updatedAt across children) | show.updatedAt`
- **Incremental pass**: list shows (light). If `show.digest` changes **or** children never hydrated → expand that show; otherwise skip episode walk.

### DB columns (per item) — add
- `digest` (TEXT)
- `updated_at_plex` (BIGINT)
- `first_seen_at`, `last_seen_at`, `last_scan_at` (BIGINT)
- `state` (`ACTIVE|MISSING|UNAVAILABLE|REMOTE_ONLY|DELETED`)
- `error_count` (INT), `last_error_at` (BIGINT), `last_error` (TEXT)
- *(for shows, separate table or columns to store `show_digest` and `children_hydrated`)*

**Portable DDL (adjust names to your schema):**
```sql
ALTER TABLE media_items ADD COLUMN IF NOT EXISTS digest TEXT;
ALTER TABLE media_items ADD COLUMN IF NOT EXISTS updated_at_plex BIGINT;
ALTER TABLE media_items ADD COLUMN IF NOT EXISTS first_seen_at BIGINT;
ALTER TABLE media_items ADD COLUMN IF NOT EXISTS last_seen_at BIGINT;
ALTER TABLE media_items ADD COLUMN IF NOT EXISTS last_scan_at BIGINT;
ALTER TABLE media_items ADD COLUMN IF NOT EXISTS state TEXT DEFAULT 'ACTIVE';
ALTER TABLE media_items ADD COLUMN IF NOT EXISTS error_count INT DEFAULT 0;
ALTER TABLE media_items ADD COLUMN IF NOT EXISTS last_error_at BIGINT;
ALTER TABLE media_items ADD COLUMN IF NOT EXISTS last_error TEXT;

CREATE TABLE IF NOT EXISTS shows (
  server_id INT NOT NULL,
  rating_key TEXT NOT NULL,
  show_digest TEXT,
  children_hydrated BOOLEAN DEFAULT FALSE,
  PRIMARY KEY (server_id, rating_key)
);
Implementation (digest helpers)
python
Copy code
# plex_integration.py (helpers)
import hashlib

def streams_sig(media_dict) -> str:
    # Summarize video/audio/sub track info into a small stable string
    v = f"v:{media_dict.get('videoCodec','?')}"
    a = f"a:{media_dict.get('audioChannels','?')}@{media_dict.get('audioCodec','?')}"
    s = f"s:{media_dict.get('subtitleCount', 0)}"
    return "|".join([v,a,s])

def digest_ep_or_movie(*, rating_key, updated_at, duration, file_size, part_count, streams_signature, guid_primary) -> str:
    h = hashlib.sha1()
    for v in (rating_key, str(updated_at or 0), str(duration or 0), str(file_size or 0),
              str(part_count or 0), streams_signature or "", guid_primary or ""):
        h.update(v.encode("utf-8")); h.update(b"|")
    return h.hexdigest()

def digest_show(child_count, leaf_count, show_updated_at, children_updated_max) -> str:
    h = hashlib.sha1()
    for v in (str(child_count or 0), str(leaf_count or 0),
              str(show_updated_at or 0), str(children_updated_max or 0)):
        h.update(v.encode("utf-8")); h.update(b"|")
    return h.hexdigest()
Library run flow (TV) — selective expansion
python
Copy code
# plex_integration.py
def sync_tv_library(client, db, library, *, deep=False, progress=lambda *_: None, now_epoch:int=0):
    processed=changed=skipped=errors=0
    seen_keys=set()
    progress("library_start", {"server_id": client.server_id, "library_id": library.id})

    for page_shows in client.iter_shows(library.section_key, page_size=200):
        to_expand=[]
        for show in page_shows:
            # compute lite show digest from listing data
            lite = digest_show(show.get('childCount'), show.get('leafCount'),
                               show.get('updatedAt'), show.get('childrenUpdatedAtMax') or show.get('updatedAt'))
            if deep or db.show_digest_changed(library.id, show['ratingKey'], lite) or not db.children_hydrated(library.id, show['ratingKey']):
                to_expand.append((show, lite))
            else:
                skipped += 1
            processed += 1

        # expand only required shows
        for show, lite in to_expand:
            try:
                seasons = client.fetch_show_children(show['ratingKey'])
                eps=[]
                for season in seasons:
                    eps.extend(client.fetch_season_children(season['ratingKey']))

                child_max = 0
                for ep in eps:
                    det = client.fetch_item_detail(ep['ratingKey'])  # to read Media/Part safely
                    media = summarize_media(det)  # duration, file_size, part_count, streams_signature, plex_path, guid_primary
                    d = digest_ep_or_movie(
                        rating_key=ep['ratingKey'], updated_at=ep.get('updatedAt'),
                        duration=media.duration, file_size=media.file_size, part_count=media.part_count,
                        streams_signature=media.streams_signature, guid_primary=media.guid_primary
                    )
                    db.upsert_episode(client.server_id, library.id, show['ratingKey'], ep, media, d, now_epoch)
                    seen_keys.add(ep['ratingKey'])
                    child_max = max(child_max, ep.get('updatedAt') or 0)
                    changed += 1

                db.upsert_show_digest(library.id, show['ratingKey'], digest_show(
                    show.get('childCount'), show.get('leafCount'),
                    show.get('updatedAt'), child_max
                ), children_hydrated=True)
            except Exception as ex:
                errors += 1

        # emit after COMMIT (see transaction notes below)
        progress("page_progress", {"server_id": client.server_id, "library_id": library.id,
                                   "processed": processed, "changed": changed,
                                   "skipped": skipped, "errors": errors})

    # finalize (mark MISSING / promote DELETED)
    missing_promoted, deleted_promoted = finalize_library(db, library.id, seen_keys, now_epoch)
    progress("library_done", {"server_id": client.server_id, "library_id": library.id, "summary": {
        "processed": processed, "changed": changed, "skipped": skipped, "errors": errors,
        "missing_promoted": missing_promoted, "deleted_promoted": deleted_promoted,
        "last_synced_at": now_epoch
    }})
UI contract (minimal, now)
Events emitted by importer (plex_integration.py):

library_start(server_id, library_id)

page_progress(server_id, library_id, processed, changed, skipped, errors)

library_done(server_id, library_id, summary)

Threading rule: Importer (worker thread) → call progress(event, payload). Worker forwards to UiBus signals on the main thread.

When to emit: page_progress after the page transaction commits; library_done after finalize_library.

Small glue (copy-paste):

python
Copy code
# ui_bus.py
from PySide6.QtCore import QObject, Signal
class UiBus(QObject):
    sync_started = Signal(int, int)
    page_progress = Signal(int, int, int, int, int, int)
    sync_completed = Signal(int, int, dict)
python
Copy code
# main_window.py (wiring)
self.ui_bus.sync_started.connect(self.onSyncStarted)
self.ui_bus.page_progress.connect(self.onPageProgress)
self.ui_bus.sync_completed.connect(self.onSyncCompleted)
python
Copy code
# import_worker.py (bridge the importer -> UiBus)
def _progress(self, event, payload):
    if event=="library_start":
        self.ui_bus.sync_started.emit(payload["server_id"], payload["library_id"])
    elif event=="page_progress":
        p=payload; self.ui_bus.page_progress.emit(p["server_id"], p["library_id"], p["processed"], p["changed"], p["skipped"], p["errors"])
    elif event=="library_done":
        self.ui_bus.sync_completed.emit(payload["server_id"], payload["library_id"], payload["summary"])
01 — Plex Endpoints & Coverage
Endpoints (light → selective expand)
Shows list: /library/sections/{key}/all?type=2 → ratingKey,title,updatedAt,childCount,leafCount,guid

Show expand (when needed):

/library/metadata/{ratingKey}/children (seasons)

/library/metadata/{seasonRatingKey}/children (episodes) or /library/metadata/{showRatingKey}?includeChildren=1

Movies list: /library/sections/{key}/all?type=1

Item detail (episode/movie): /library/metadata/{ratingKey} to read Media/Part (size, duration, streams)

Paging & commits
Iterate in pages (e.g., 200); for each page:

Compare digests; prepare upserts

Transaction: upsert items in batch → commit

Emit page_progress after commit

Minimal UI contract (where to emit)
After each page commit → page_progress

After library finalize → library_done (include last_synced_at, missing/deleted counts)

02 — Adds, Changes, Deletes (Algorithm)
Mutation rules
Add: not in DB → insert; set first_seen_at=now, last_seen_at=now, state='ACTIVE'

Change: in DB and digest differs → update; last_seen_at=now, state='ACTIVE'

Unchanged: in DB and digest same → last_seen_at=now (touch only), no large writes

Soft delete:

End of library run: items in DB for this library but not in seen → state='MISSING', missing_since=now

If MISSING ≥ retention days (or deep confirms) → state='DELETED' (optional later purge)

DAL helpers (database.py)
python
Copy code
def show_digest_changed(self, library_id:int, show_key:str, lite_digest:str) -> bool: ...
def children_hydrated(self, library_id:int, show_key:str) -> bool: ...
def upsert_show_digest(self, library_id:int, show_key:str, digest:str, *, children_hydrated:bool): ...
def upsert_episode(self, server_id:int, library_id:int, parent_show_key:str, ep:dict, media, digest:str, now_epoch:int): ...
def upsert_movie(self, server_id:int, library_id:int, mv:dict, media, digest:str, now_epoch:int): ...
def mark_missing_not_seen(self, library_id:int, seen:set[str], now_epoch:int) -> int: ...
def promote_deleted_past_retention(self, library_id:int, now_epoch:int, retention_days:int) -> int: ...
Finalize step:

python
Copy code
def finalize_library(db, library_id:int, seen:set[str], now_epoch:int, retention_days:int=30):
    missing = db.mark_missing_not_seen(library_id, seen, now_epoch)
    deleted = db.promote_deleted_past_retention(library_id, now_epoch, retention_days)
    return missing, deleted
Transactions & UI semantics
One transaction per page for upserts → commit → emit page_progress.

finalize_library runs in its own transaction; then emit library_done.

In main_window.py, on sync_completed, refresh:

Libraries row (Last Synced, optional counts)

If items view is showing this library, itemsModel.refresh(library_id)

03 — Dynamic Path Mapping (Per-Server; No Stored Local Path)
Design
Never store local paths. Store only Plex path (Media/Part/file) + server_id.

path_mappings table:

server_id INT, plex_prefix TEXT, local_prefix TEXT, optional computed priority = length(plex_prefix)

At runtime, resolve local paths for actions like “Open in Player”.

DDL:

sql
Copy code
CREATE TABLE IF NOT EXISTS path_mappings (
  id SERIAL PRIMARY KEY,
  server_id INT NOT NULL,
  plex_prefix TEXT NOT NULL,
  local_prefix TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_map_server ON path_mappings(server_id);
Resolver (path_mapping.py):

python
Copy code
def resolve_local_path(db, server_id:int, plex_path:str) -> str | None:
    mappings = db.get_path_mappings(server_id)  # return sorted by len(plex_prefix) DESC
    for pp, lp in mappings:
        if plex_path.startswith(pp):
            return plex_path.replace(pp, lp, 1)
    return None
UI usage

When the user clicks “Open file” / “Reveal in Finder,” call resolve_local_path(server_id, item.plex_path) on demand.

You may cache resolutions in memory during a single run; do not persist.

04 — State & Cleanup Posture
States
ACTIVE – seen this run, metadata/media OK

REMOTE_ONLY – no local mapping resolves, but Plex can stream

UNAVAILABLE – Plex lists parts but not playable / incomplete

MISSING – not seen this run but exists in DB

DELETED – promoted after retention or deep-confirmed missing

Transitions (high level)
From → To	Trigger
(any) → ACTIVE	item processed this run and OK
ACTIVE → REMOTE_ONLY	could not resolve local path; Plex streamable
ACTIVE → UNAVAILABLE	Plex reports but item not playable/incomplete
ACTIVE/MISSING → MISSING	not seen in this run’s listing
MISSING → DELETED	missing for ≥ retention days (or deep confirms)

Cleanup
End of library run: mark unseen as MISSING; report counts.

Promote: MISSING older than retention → DELETED.

Optional purge: separate manual action later.

Counts to surface to UI on sync_completed:

missing_promoted, deleted_promoted, last_synced_at

Libraries model helper (database.py)

python
Copy code
def library_missing_deleted_counts(self, library_id:int) -> tuple[int,int]:
    cur = self.conn.execute("""
        SELECT
          SUM(CASE WHEN state='MISSING' THEN 1 ELSE 0 END),
          SUM(CASE WHEN state='DELETED' THEN 1 ELSE 0 END)
        FROM media_items WHERE library_id=?
    """, (library_id,))
    row = cur.fetchone() or (0,0)
    return (row[0] or 0, row[1] or 0)
UI refresh (main_window.py)

python
Copy code
def onSyncCompleted(self, server_id:int, library_id:int, summary:dict):
    self.librariesModel.refresh_row(library_id)   # updates Last Synced & counts
    if getattr(self.itemsModel, "library_id", None) == library_id:
        self.itemsModel.refresh(library_id)
    self.statusBar().showMessage(
        f"Sync finished: +{summary['changed']} ~{summary['skipped']} !{summary['errors']} " +
        f"(missing↑{summary['missing_promoted']}, deleted↑{summary['deleted_promoted']})"
    )
Notes on DB engine (dev quality of life)
If SQLite is slowing iteration, point your DAL at PostgreSQL or MariaDB via DB_URL (SQLAlchemy/Alembic). The model above is portable; migrations stay simple while you churn schema during development.

Quick Checklist (to implement now)
 Add columns/tables from 00; create digest_* helpers.

 Implement TV selective expansion and Movies digest path; page + commit + emit.

 Implement finalize_library and DAL state transitions (02).

 Replace stored local paths with on-demand resolver (03).

 Hook minimal UI events; refresh libraries/items on completion (00/01/04).
