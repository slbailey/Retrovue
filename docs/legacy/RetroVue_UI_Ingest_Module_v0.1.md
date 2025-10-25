# RetroVue UI Design — Ingest & Progress (Draft v0.1)

> **Legacy Document** — Pre-Alembic version, retained for reference only.

> Living document for the Retro IPTV Simulation Project UI. Scope for this draft: ingestion UX, progress visualization, and integration contracts with the existing Plex ingest pipeline. This doc will evolve into a full product spec.

---

## 1) Goals & Principles

- **Low-latency, trustworthy feedback** while ingesting Plex media.
- **Deterministic progress bars** (no guessing) for:
  1. Overall run across selected libraries
  2. Per-library (Movies: items; TV: shows)
  3. Per-show episode progress (for TV libraries)
- **Decoupled architecture**: ingest emits **domain events**; UI consumes via push or polling.
- **Resumable & auditable**: persist all runs + event snapshots.
- **Start simple, grow safely**: DB polling first, add live push later without changing ingest core.

---

## 2) High-Level UX

### 2.1 Ingestion Console (primary view)

- **Header**: Server selector; “Run ingest” (Full / Incremental / Dry Run); Filters (Libraries, Kinds: movie/episode).
- **Overall Progress Bar**: `completedLibraries / totalLibrariesEnabled`.
- **Libraries Panel** (list): Each library shows:
  - Library title & type (Movie / TV)
  - Status chip: Idle / Running / Error / Done
  - **Library Progress Bar**
  - For TV libraries: expandable **Show Queue** with per-show episode bar.
- **Event Stream** (right rail): Rolling, filterable by level (info/warn/error), phase, library.
- **Run Summary**: Stats snapshot when run completes (inserted/updated/skipped/errors).

### 2.2 Library Manager (supporting view)

- Toggle **Sync Enabled** per library.
- Show **last full/incremental sync epoch** per library.
- Path mappings editor (read-only in v0.1; writes in later iteration).

### 2.3 Content Browser (future)

- Browse ingested items; deep-link from event stream rows to items.

---

## 3) Integration Strategy (Best Practice)

**Hybrid Event + Persistence**

- Ingest emits **structured events** to a pluggable Reporter.
- Reporter **persists** to DB for history & polling.
- Reporter emits **WebSocket events** for live UI updates in web application.

**Non-goals**: UI parsing logs; ingest calling UI directly.

---

## 4) Event Model (UI-facing contract)

### 4.1 Event Schema

```
Event {
  run_id: string,                 // unique per ingest run
  ts: int,                        // epoch seconds
  phase: enum[overall, library, show, episode, batch, done, error, dry_run],
  scope: {
    server_id?: int,
    library_key?: string,
    library_title?: string,
    kind?: enum[movie, episode],
    show_title?: string,
    season_number?: int,
    episode_number?: int,
  },
  progress?: { current: int, total: int },
  message?: string,
  extra?: object                  // optional payload (paths, ratingKey, stats, etc.)
}
```

### 4.2 Emission Points

- **overall:start** — before iterating selected libraries
- **library:start** — resolved section type + counts known
- **library:tick** — each N items (movies) or each show (TV)
- **show:start** — TV only; after computing episode count
- **episode:tick** — per episode processed
- **batch:commit** — after each DB commit
- **error** — any exception with context (item title/ratingKey)
- **done** — final stats snapshot
- **dry_run** — explicit marker for dry runs

### 4.3 Frequency Guidelines

- Default N = 25 items for `library:tick` (configurable); always emit at `batch:commit` and boundary transitions.

---

## 5) Persistence Model

**Decision for v0.1 (your preference): _Live-only; no history._**

- We will not persist ingest runs or events. If content isn’t visible afterward, you’ll just run it again.
- Implementation: in-memory event bus only (thread-safe queue / Qt signals). The UI renders live progress and final stats for the current session.

**Future (optional, not planned now):** If you ever want history, add two small tables (`ingest_runs`, `ingest_events`) and a polling endpoint; the rest of the design already supports it without changing ingest logic.

---

## 6) Ingest Service Interface (v0.1)

> Implementation detail: Direct integration with web application. Background workers handle ingest operations with WebSocket events for progress updates.

**Service Methods:**

- `start_ingest_run(server_id, mode, libraries[], kinds[], dry_run, verbose)` — Start new ingest run
  - Returns run_id for tracking
- `get_run_status(run_id)` — Get run metadata + latest stats
- `get_run_events(run_id, after_ts=None)` — Get paged events for polling
- `get_ingest_status()` — Last run per server + per-library last sync epochs

**Qt Integration:**

- QThread worker handles long-running ingest operations
- Qt signals emit progress updates to UI components
- Direct database access for persistence

---

## 7) Progress Computation (Deterministic)

We support **multiple libraries per content type** and multiple sources in one run. Progress is computed over a fixed **Selection Set** you choose at start.

### 7.1 Selection Set (what you pick before running)

A selection set can include any combination of:

- Plex libraries of type **movie** (e.g., Kids Movies, Horror Movies, Adult Movies)
- Plex libraries of type **show** (e.g., Kids TV, 80s TV, Sitcoms)
- Filesystem roots (Commercials, Promos) and/or TMM-NFO roots

### 7.2 Fixed Global Denominator (no stutter)

Before ingest begins, we compute a fixed **total_work_units** across the whole selection set:

```
 total_work_units =
   Σ_over_selected_movie_libraries( total_movies_in_library ) +
   Σ_over_selected_show_libraries( total_episodes_in_library ) +
   Σ_over_selected_fs_roots( total_files_found )
```

- **Movies**: `total_movies_in_library` comes from Plex `totalSize` for each _movie_ section.
- **TV**: `total_episodes_in_library` is the sum of episodes across all shows in each _show_ section (fast pre-scan of shows→seasons→episodes).
- **Filesystem/TMM**: `total_files_found` comes from a quick pre-scan (extension filter, size>0, optional NFO required).

This denominator is **locked** for the run, so the unified bar never resets.

### 7.3 Commit-based Progress

We increment **committed_work_units** only after each successful batch commit. The unified bar shows:

```
progress_percent = committed_work_units / total_work_units
```

We also surface mini chips for each library/root:

```
lib_progress = committed_in_lib / total_in_lib
```

### 7.4 Incremental mode

If you choose incremental ingest, the pre-scan filters by `since_epoch` (per source) to compute totals _only for items that would be processed_, keeping the denominator honest.

---

## 8) Mapping to Current Code (Readiness)

- **Ingest loop & batches**: clear emission points around iteration and `_process_batch`.
- **Plex totals**: pagination responses provide `totalSize`; TV child endpoints provide episode counts per show.
- **Library metadata**: already reading sections and writing library rows; last sync epochs are present for UI badges.
- **Path mapping**: resolved in `_process_item`; expose resolved paths in `extra` for UI previews.

**Gaps to fill (small)**

- Add `run_id` and a small Reporter interface.
- Add DB tables `ingest_runs`/`ingest_events` and light DAO helpers.
- Add endpoint stubs (polling first).

---

## 9) Error Handling & UX

- Event-level `error` entries with item context + suggestion (e.g., missing path mapping).
- Library row shows a red chip with count; clicking filters the event stream.
- A run with any error ends in `status=error`; UI shows partial stats but allows “Retry failed only” (future).

---

## 10) Performance & Resilience

- Batch commits remain authoritative; emit `batch:commit` to avoid chatty updates.
- If UI disconnects, it can reload by pulling events since the last seen `ts`.
- Reporter should be non-blocking (queue + background writer) to avoid slowing ingest.

---

## 11) Security & Permissions (early)

- Read-only endpoints for status/events; POST to start runs requires local/admin access.
- No PII; store file paths only if needed for operator diagnostics.

---

## 12) Roadmap Add-ons

- **Live Progress Updates** via Qt signals with backpressure handling.
- **Run Cancellation & Pausing** (Qt signals to worker thread).
- **Metrics** (performance counters for runs, items/sec).
- **Notifications** (Qt message boxes/toasts on done/error).
- **Plugin System** (drop-in sources via `plugins/` folder) ← see §22.

---

## 13) Open Questions

- Do we need per-library concurrency controls (parallel libraries) in v0.1?
- Should episode bar aggregate across shows as a secondary bar at the library level, or remain per-show only?
- How aggressively should we prune `ingest_events`?

---

## 14) Acceptance Criteria (v0.1)

- Start an ingest run from the UI and see three progress bars update deterministically (Movies, TV shows + episodes; or folder/NFO collections).
- Live-only mode: progress is visible while the UI is open; no run history is stored.
- Errors surface with actionable context (e.g., missing path mapping, unreadable file) during the run.
- No DB schema changes are required for history; only the in-memory event bus + existing DB writes for content.

## 23) Multi-Library / Multi-Source Runs — Concrete Examples

### Example A: 3 Movie libraries + 2 TV libraries (Plex)

Selection Set:

- Movies: Kids Movies (412), Horror Movies (1,203), Adult Movies (756)
- TV: Kids TV (episodes=1,142), 80s TV (episodes=3,486)
  Global denominator = 412 + 1,203 + 756 + 1,142 + 3,486 = **6,999** work units.
  Unified bar advances only on commits; mini chips show per-library progress.

### Example B: TV (Plex) + Commercials (Filesystem)

- TV: Sitcoms (episodes=2,110)
- FS: Commercials root (files=528)
  Denominator = 2,638. If 100 commercials commit in first batch, unified bar advances by 100/2,638.

### Example C: Incremental on 4 libraries

- We compute totals per library using `since_epoch` (Plex filters + enumeration; FS pre-scan by file mtime).
- Unified bar uses the filtered totals, so percentages are still accurate even though we’re not scanning the whole library.

---

## 24) FastStart Pre‑Scan & No‑Backtrack Guarantees (v0.1)

**Goals**

- Never looks frozen; always shows motion (counting, chips, mini bars).
- Unified progress never moves backward.

**Behavior**

1. **Instant activity (T=0s):** show “Indexing N sources…” with animated chips per library/root. Movies lock totals immediately; TV chips show running episode counts; FS/TMM show file counts rising.
2. **Start ingest immediately:** as soon as any source is locked, ingest begins on that source even while others finish pre‑scan.
3. **Lock denominator before showing %:** the unified percent appears only when the global denominator is finalized. Until then, show live item counters and per‑library mini bars so it never looks idle.
4. **Commit‑based advancement:** the unified bar advances only on **successful batch commits**; retries/rollbacks do not decrement progress.
5. **Smooth updates:** UI throttles paint to ~100–200ms and interpolates between commits for a steady visual.

**Feedback Injection Points**

- `prescan:start` → activating chips per source.
- `prescan:partial` → update live counts per source (TV episode enumeration, FS/TMM file count).
- `prescan:locked` → totals fixed for a source.
- `ingest:start` → begins as soon as any source is ready.
- `batch:commit` → increments unified bar (commit‑based units).
- `error` → increments an error counter; does not affect the unified %.
- `done` → final stats.

**Monotonicity Rule**

- Unified percent is derived from **committed_work_units / total_work_units** only. We do not display a determinate percent until **total_work_units** is finalized.
