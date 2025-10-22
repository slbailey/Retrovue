# Phase 8 - Plan the Scheduling Stack Pages

**Status**: 🚧 In Progress  
**Date Started**: October 22, 2025  
**Goal**: Add placeholder pages/tabs for scheduling features to the modular Qt GUI

---

## Overview

Phase 8 creates the UI foundation for scheduling features, allowing users to:

1. Create and manage sync schedules (e.g., "Sync Movies library every night at 2 AM")
2. View schedule execution history and logs
3. Monitor active/upcoming schedules

This phase focuses on **UI scaffolding and placeholders**. The actual scheduling logic (cron, background tasks) will be implemented in a future phase.

---

## Scheduling Features Analysis

### What is a Schedule?

A schedule defines **when** and **what** to sync:

- **When**: Cron expression or simple interval (e.g., "every 6 hours", "daily at 2 AM")
- **What**: Server + Library + Sync options (dry run, limit, etc.)
- **Settings**: Enabled/disabled, notification preferences

### Use Cases

1. **Nightly Movie Sync**: "Sync 'Movies' library from 'Plex Server' every day at 2:00 AM"
2. **Weekend TV Sync**: "Sync 'TV Shows' library every Saturday at midnight"
3. **Quick Updates**: "Sync 'Recently Added' library every 2 hours"

---

## Pages to Create

### 1. **Schedules Management Page** (Primary)

**Tab Name**: "Schedules"  
**Location**: New top-level tab in main window  
**Purpose**: Create, view, edit, delete sync schedules

**UI Components**:

- **Schedules Table**:
  - Columns: Name, Server, Library, Frequency, Last Run, Next Run, Status (Enabled/Disabled), Actions
  - Actions: Edit, Delete, Enable/Disable toggle
- **"Add Schedule" Button**: Opens schedule creation form
- **Schedule Form** (dialog or sidebar):
  - Name (text input)
  - Server (dropdown)
  - Library (dropdown)
  - Frequency:
    - Simple: "Every X hours/days" (dropdown + spinbox)
    - Advanced: Cron expression (text input with validator)
  - Sync Options: Dry run, limit, kinds (movies/episodes)
  - Enabled/Disabled checkbox
  - Save/Cancel buttons

**Placeholder Behavior**:

- Display empty table with helpful message: "No schedules configured. Click 'Add Schedule' to create one."
- "Add Schedule" button shows a TODO dialog: "Scheduling backend not yet implemented. Coming soon!"

---

### 2. **Schedule History Page** (Secondary)

**Tab Name**: "Schedule History"  
**Location**: Subtab under "Schedules" tab or separate top-level tab  
**Purpose**: View past schedule executions and results

**UI Components**:

- **History Table**:
  - Columns: Schedule Name, Server, Library, Start Time, Duration, Items Synced, Errors, Status (Success/Failed)
  - Filters: Date range, schedule name, status
  - Sort: By start time (most recent first)
- **Log Viewer**: Click a row to see detailed execution log (QTextEdit)

**Placeholder Behavior**:

- Display empty table: "No schedule history yet. Schedules will appear here after they run."
- Log viewer shows: "Select a schedule execution to view logs."

---

### 3. **Schedule Monitoring (Optional - Simpler for Phase 8)**

**Integration**: Add a status widget to the main window status bar or Schedules page  
**Purpose**: Show currently running schedule (if any)

**UI Components**:

- **Status Badge**: "Idle" | "Running: [Schedule Name]" | "Next: [Schedule Name] in 2h 15m"
- **Progress Indicator**: If a schedule is running, show progress (similar to manual sync)

**Placeholder Behavior**:

- Always shows "Idle - No schedules configured"

---

## Architecture Design

### Database Schema (Planning for Future)

```sql
-- schedules table
CREATE TABLE schedules (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    server_id INTEGER NOT NULL,
    library_id INTEGER NOT NULL,
    cron_expression TEXT,  -- e.g., "0 2 * * *" for daily at 2 AM
    interval_seconds INTEGER,  -- Alternative: simple interval in seconds
    sync_options TEXT,  -- JSON: { "dry_run": false, "limit": null, "kinds": ["movie"] }
    enabled BOOLEAN DEFAULT 1,
    created_at INTEGER,
    updated_at INTEGER,
    FOREIGN KEY (server_id) REFERENCES plex_servers(id),
    FOREIGN KEY (library_id) REFERENCES plex_libraries(id)
);

-- schedule_executions table
CREATE TABLE schedule_executions (
    id INTEGER PRIMARY KEY,
    schedule_id INTEGER NOT NULL,
    start_time INTEGER NOT NULL,
    end_time INTEGER,
    status TEXT,  -- 'running', 'success', 'failed'
    items_scanned INTEGER DEFAULT 0,
    items_inserted INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    log_text TEXT,  -- Full execution log
    FOREIGN KEY (schedule_id) REFERENCES schedules(id)
);
```

### Core Modules (Placeholder for Future)

- **`src/retrovue/core/scheduling/manager.py`**: Schedule CRUD operations
- **`src/retrovue/core/scheduling/executor.py`**: Execute schedules (background thread/process)
- **`src/retrovue/core/scheduling/cron.py`**: Cron expression parser and next-run calculator
- **`src/retrovue/core/api.py`**: Add schedule methods to API façade

---

## Phase 8 Implementation Steps

### Step 1: Create GUI Page Structure ✅

- [x] Create `src/retrovue/gui/features/schedules/` directory
- [x] Create `src/retrovue/gui/features/schedules/__init__.py`
- [x] Create `src/retrovue/gui/features/schedules/page.py` with placeholder UI

### Step 2: Add Schedules Tab to Main Window ✅

- [x] Update `src/retrovue/gui/router.py` to register "Schedules" page
- [x] Verify tab appears and loads correctly

### Step 3: Create Schedule Management UI (Placeholder) ✅

- [ ] Schedules table with empty state message
- [ ] "Add Schedule" button (shows TODO dialog)
- [ ] Clean, professional layout matching Importers page style

### Step 4: Create Schedule History UI (Placeholder) ✅

- [ ] History table with empty state message
- [ ] Log viewer panel
- [ ] Date range filters (disabled for now)

### Step 5: Documentation ✅

- [x] Create `PHASE_8_PLAN.md` (this file)
- [ ] Update `MIGRATION_NOTES.md` with Phase 8 progress
- [ ] Update `Readme.md` with scheduling UI mention (coming soon)

---

## UI Mockup

### Schedules Tab Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ Schedules                                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────┐   [Add Schedule] │
│  │ Schedules                                   │               │
│  ├──────┬────────┬────────┬──────────┬─────────┤               │
│  │ Name │ Server │ Library│ Frequency│ Next Run│ Enabled│Actions│
│  ├──────┼────────┼────────┼──────────┼─────────┼────────┼───────┤
│  │                                                               │
│  │           No schedules configured yet.                       │
│  │      Click "Add Schedule" to create your first one.         │
│  │                                                               │
│  └──────────────────────────────────────────────────────────────┘
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐
│  │ Schedule History                                            │
│  ├────────┬────────┬──────────┬──────────┬────────┬───────────┤
│  │ Name   │ Server │ Library  │ Start    │ Items  │ Status    │
│  ├────────┼────────┼──────────┼──────────┼────────┼───────────┤
│  │                                                              │
│  │         No schedule executions yet.                         │
│  │                                                              │
│  └─────────────────────────────────────────────────────────────┘
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Success Criteria

Phase 8 is complete when:

1. ✅ "Schedules" tab appears in main GUI
2. ✅ Schedules management UI is visible with empty state
3. ✅ Schedule history UI is visible with empty state
4. ✅ "Add Schedule" button shows "Coming soon" message
5. ✅ UI matches style/quality of Importers page
6. ✅ Documentation is updated

---

## Future Phases (Beyond Phase 8)

### Phase 9 (Future): Implement Scheduling Backend

- Implement `src/retrovue/core/scheduling/manager.py`
- Add database migrations for schedules tables
- Create cron parser or use library (e.g., `croniter`)
- Implement schedule executor with threading or multiprocessing

### Phase 10 (Future): Wire Up Scheduling UI

- Connect "Add Schedule" form to backend
- Implement schedule CRUD operations
- Show real schedules in table
- Enable/disable schedules
- View schedule execution history

### Phase 11 (Future): Background Scheduler Service

- Create background scheduler process
- Auto-start scheduler on GUI launch
- Monitor scheduler health
- Handle schedule conflicts and failures

---

## Notes

- **Keep It Simple**: Phase 8 is about UI placeholders, not functionality
- **Match Existing Style**: Follow the patterns from Importers page (tabs, tables, buttons)
- **Document Everything**: Clear TODOs and "Coming soon" messages for users
- **Extensible Design**: Structure UI so backend can be plugged in later without major refactoring

---

**Phase 8 Started**: October 22, 2025  
**Expected Completion**: Same day (UI placeholders only)
