# RetroVue UI Design — Core Mission (Living Document)

> Living document for the Retro IPTV Simulation Project UI. This is the umbrella document that establishes the overall mission, guiding principles, module structure, and how this UI fits into the Retro IPTV Simulation Project. Each functional area (Ingest, Schedule, Metadata, etc.) has its own subdocument, referenced here.

---

## 1) Purpose & Vision

The RetroVue UI is the central management console for running all aspects of the Retro IPTV "retro network TV simulator." Its purpose is to provide one place to:

- **Configure channels and templates**
- **Ingest and manage content metadata**
- **Build and maintain daily broadcast schedules**
- **Monitor playout and logs**
- **Troubleshoot and adjust operations**

The vision is to deliver a professional broadcast-operations style interface that hobbyists can use to create autonomous IPTV channels, integrating with Plex and IPTV clients. The experience should feel like programming a real TV station, but remain simple enough for a single-operator setup.

---

## 2) Guiding Principles

- **Single Pane of Glass** — All major operations (ingest, scheduling, metadata editing, logs, channel dashboards) are accessible in one consistent UI.
- **Operator-Centric UX** — The primary user is a single operator. Workflows must be direct, visual, and minimize unnecessary steps.
- **Living but Stable** — This core document changes infrequently; most iteration happens in subdocs.
- **Broadcast Accuracy** — Aligns with real broadcast practices (grid-based scheduling, ad pods, templates, playlogs).
- **Modular Architecture** — Each module (Ingest, Schedule, Metadata, etc.) is defined separately but coordinated under this umbrella.

---

## 3) Major UI Modules

The RetroVue UI is structured into modules, each with its own design document. These modules are:

### 3.1 Ingest & Progress Module

- Ingest media from Plex, TinyMediaManager, filesystem.
- Convert chapter markers → ad break markers.
- Provide deterministic, live-only ingest progress.
- **[See RetroVue_UI_Ingest_Module_v0.1.md]**

### 3.2 Schedule Editor & Playlog Module

- Calendar-style template editor.
- Rule-driven content slots (series, movies, tags, rating guardrails).
- Hybrid Playlog (grid overview + linear rundown with ad pods).
- **[See RetroVue_UI_Schedule_Module_v0.1.md]**

### 3.3 Content Browser Module (Future)

- Browse ingested assets.
- Add/adjust breakpoints via Media Browser.
- Override metadata if needed.

### 3.4 Metadata Editor Module (Future)

- Fine-tune runtimes, avail lengths, ad breaks.
- Override Plex/TMM metadata for broadcast scheduling purposes.

### 3.5 Playout Log Viewer Module (Future)

- Review what aired, what's airing, and what's next.
- Show errors, missing content, skipped events.

### 3.6 Channel Dashboard Module (Future)

- Channel-level health (stream encoding, transport stream monitoring, statuses).
- Emergency system integration.

---

## 4) Cross-Module Governance

### 4.1 Navigation

- **Left-hand navigation rail** for modules (Ingest, Schedule, Content, Metadata, Logs, Channels).
- **Consistent layout**: list/grid on left, detail/preview on right.

### 4.2 Shared Conventions

- **Error Handling**: Always show actionable context (e.g., missing ad break, content too short).
- **Grid Timekeeping**: All schedules align to 30-minute grids. Blocks may span multiple grids.
- **Ad Breaks**: Always sourced from DB (ingest or manual override), never raw chapter markers.
- **Color Coding**: Consistent across modules (e.g., Series=blue, Movies=green, Promos=yellow).

### 4.3 Persistence Strategy

**Relational Core + JSON Rules:**

- Templates, schedules, playlogs → SQL tables.
- Rules (tags, episode policies, rating guards) → JSON blobs.
- Hybrid ensures extensibility without schema churn.

---

## 5) Subdocument Index

- **Ingest & Progress Module v0.1** — [RetroVue_UI_Ingest_Module_v0.1.md]
- **Schedule Module v0.1** — [RetroVue_UI_Schedule_Module_v0.1.md]
- **(Future) Content Browser Module** — TBD
- **(Future) Metadata Editor Module** — TBD
- **(Future) Playout Log Viewer** — TBD
- **(Future) Channel Dashboard** — TBD

---

## 6) Change Policy

This master document is living but stable. It changes only when:

- A new module is added
- Cross-cutting governance (error handling, navigation, persistence) evolves
- High-level principles shift

Subdocuments evolve more frequently with detailed UX and implementation notes.

---

## 7) Integration Strategy

**Web Application Architecture:**

- Each module operates independently but shares common web UI patterns and components.
- Cross-module data flows through the centralized Postgres database layer.
- Qt signals/slots provide event-driven communication between modules and background workers.
- QThread workers handle long-running operations (ingest, schedule generation) without blocking the UI.
- Direct database access eliminates need for REST API layer.

**Non-goals**: Web-based architecture; external server dependencies; REST API layer.

---

## 8) Technology Stack (v0.1)

- **Frontend**: Web UI (FastAPI + HTML/JS) - Browser-based application
- **Packaging**: PyInstaller (one-folder build) for Windows executable (RetroVue.exe)
- **Database**: PostgreSQL (centralized database managed via Alembic migrations)
- **Threading**: QThread workers with Qt signals for background operations
- **Authentication**: Local admin access for v0.1 (no external authentication required)

---

## 9) Performance & Scalability

- **Single-operator focus**: Designed for one person managing multiple channels on a single Windows machine.
- **Desktop-optimized**: Native Windows application with Qt widgets and layouts.
- **Efficient data loading**: Lazy loading and pagination for large datasets using Qt model/view architecture.
- **Memory management**: Qt's object hierarchy and garbage collection for efficient resource usage.
- **Background processing**: QThread workers prevent UI blocking during long operations.

---

## 10) Security & Permissions (v0.1)

- **Local access only**: No external authentication required.
- **Admin privileges**: Full access to all modules and operations.
- **Future considerations**: Role-based access control for multi-user scenarios.

---

## 11) Roadmap

- **v0.1**: Core modules (Ingest, Schedule) with basic functionality
- **v0.2**: Content Browser and Metadata Editor
- **v0.3**: Playout Log Viewer and Channel Dashboard
- **v1.0**: Full feature parity with legacy system
- **Future**: Advanced features (emergency alerts, graphics overlays, multi-user support)

---

## 12) Acceptance Criteria (v0.1)

- All modules accessible through consistent Qt-based navigation
- Shared Qt UI patterns (error handling, progress indicators, data grids) work across modules
- Cross-module data flows work correctly through centralized Postgres database (e.g., ingested content appears in schedule editor)
- Native Windows desktop application runs without external dependencies
- PyInstaller packaging creates single executable (RetroVue.exe)
- No breaking changes to existing ingest pipeline
