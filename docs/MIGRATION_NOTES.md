# GUI Migration Notes

## Phase 1 Complete ✓

The new modular Qt application has been scaffolded under `src/retrovue/gui/`.

### Files Removed in Phase 6: ✅

The following Tkinter files have been removed:

- ~~`src/retrovue/gui/`~~ (entire directory - REMOVED)

  - ~~`src/retrovue/gui/app.py`~~
  - ~~`src/retrovue/gui/router.py`~~
  - ~~`src/retrovue/gui/store.py`~~
  - ~~`src/retrovue/gui/features/importers/view.py`~~
  - ~~`src/retrovue/gui/widgets/progress.py`~~
  - ~~All associated `__init__.py` files~~

- ~~`src/retrovue/core/tasks/`~~ (entire directory - REMOVED)
  - ~~`src/retrovue/core/tasks/runner.py`~~ (stub version)

**Note**: `src/retrovue/core/api.py` is NOT removed - it's the Phase 5 API façade and is actively used by the Qt GUI.

### Legacy GUI Files:

- ~~`enhanced_retrovue_gui.py`~~ - REMOVED (was Qt GUI reference)
- ~~`run_enhanced_gui.py`~~ - REMOVED (was Qt GUI launcher)

## Current Status:

- ✓ Web-only architecture with FastAPI + HTML/JS
- ✓ API endpoints for Servers, Libraries, and Content Sync
- ✓ Web interface accessible at http://localhost:8000
- ✓ All Qt/PySide dependencies removed

## Phases Complete:

- ✅ **Phase 1**: Scaffolded modular Qt app structure
- ✅ **Phase 2**: Migrated Servers management (add/list/delete)
- ✅ **Phase 3**: Migrated Libraries discovery with async operations
- ✅ **Phase 4**: Migrated Content Sync with path mappings
- ✅ **Phase 5**: Unified GUI ↔ Core with API façade
- ✅ **Phase 6**: Removed Tkinter code and renamed gui_qt to gui
- ✅ **Phase 7**: Quality & parity checks
- ✅ **Phase 8**: **Web Migration** - Removed all Qt/PySide dependencies and migrated to web-only architecture

## Phase 7 Details: Quality & Parity Checks

### Improvements Made:

1. **Path Mapping Deletion**:

   - Implemented full delete functionality with confirmation
   - Updated database methods to return mapping IDs
   - 4 files modified (db.py, sync.py, api.py, page.py)

2. **API Usage Consistency**:

   - Fixed leftover `self.sync_manager` reference to use `self.api`
   - Ensures consistent use of Phase 5 API façade

3. **Sync Limit Feature**:

   - Wired up the limit spinbox that was previously unused
   - Users can now test syncs with small datasets

4. **Comprehensive Tooltips**:

   - Added 15+ tooltips throughout the GUI
   - Explains inputs, buttons, and workflows
   - Makes interface self-documenting

5. **README Documentation**:
   - Added "Launch the GUI (Recommended)" section
   - Documented features and first-time setup
   - Platform-specific instructions

### Files Modified:

- `src/retrovue/plex/db.py` - Return mapping IDs
- `src/retrovue/core/sync.py` - Update return types
- `src/retrovue/core/api.py` - Update signatures
- `src/retrovue/gui/features/importers/page.py` - 4 fixes + 15 tooltips
- `Readme.md` - GUI documentation

### Quality Status:

- ✅ 0 linter errors
- ✅ GUI launches successfully
- ✅ All Plex import workflows functional
- ✅ Comprehensive documentation

### Known Limitations: ✅ ALL FIXED!

~~1. **UI Freeze During Sync**~~ ✅ FIXED - Added `ingest_library_stream()` generator method  
~~2. **FFprobe Unicode Errors**~~ ✅ FIXED - Added UTF-8 encoding to subprocess call

See `LIMITATIONS_FIXED.md` for technical details.

## Phase 6 Details: Cleanup & Code Removal

### What Was Removed:

1. **Tkinter GUI Directory** (`src/retrovue/gui/`):

   - Entire directory tree removed
   - Files: `app.py`, `router.py`, `store.py`, `features/importers/view.py`, `widgets/progress.py`
   - All `__init__.py` and `__pycache__` files
   - **Reason**: Created before decision to standardize on web-only UI

2. **Stub Tasks Module** (`src/retrovue/core/tasks/`):
   - Entire directory removed
   - File: `runner.py` (simple threading stub)
   - **Reason**: Qt has its own `QThread` system, this stub is not needed

### What Was Renamed:

- **`src/retrovue/gui_qt/`** → **`src/retrovue/gui/`**
  - Since Tkinter code is removed, `_qt` suffix is no longer needed
  - Cleaner, simpler naming convention
  - All imports updated (`from retrovue.gui.app import launch`)

### What Was Kept:

- ✅ **`src/retrovue/core/api.py`**: Phase 5 API façade (actively used by Qt GUI)
- ✅ **`src/retrovue/core/scheduling/`**: Empty placeholder for future Phase 8
- ✅ **`enhanced_retrovue_gui.py`**: Monolithic GUI kept for reference

### Benefits:

- **Cleaner codebase**: Removed unused/obsolete Tkinter code
- **Less confusion**: Only one GUI framework (Qt) in the codebase
- **Smaller footprint**: Reduced number of Python files and directories
- **Simpler naming**: `src/retrovue/gui/` instead of `gui_qt/`
- **Clear architecture**: `src/retrovue/gui/` is the only GUI implementation

## Phase 5 Details: API Façade Layer

### What Was Done:

1. **Created `src/retrovue/core/api.py`**:

   - Unified API façade class (`RetrovueAPI`) that wraps all core managers
   - Consistent interface for server, library, and sync operations
   - Singleton pattern via `get_api()` function for easy access
   - Comprehensive docstrings for all methods

2. **Refactored Qt GUI** (`src/retrovue/gui/features/importers/page.py`):

   - Removed direct imports of `ServerManager`, `LibraryManager`, `SyncManager`
   - Now uses `get_api()` to access unified API
   - All manager calls replaced with API calls (e.g., `self.api.list_servers()`)
   - No behavioral changes - just cleaner architecture

3. **Benefits**:
   - **Separation of Concerns**: GUI doesn't need to know about internal managers
   - **Consistency**: Same API can be used by GUI, CLI, or future interfaces
   - **Maintainability**: Changes to core logic only affect API layer
   - **Testability**: API can be mocked easily for testing
   - **Future-proof**: Easy to add caching, validation, or middleware

### API Methods Available:

**Server Operations:**

- `add_server(name, url, token)` → server_id
- `list_servers()` → List[Dict]
- `get_server(server_id)` → Dict | None
- `delete_server(server_id)` → bool

**Library Operations:**

- `discover_libraries(server_id)` → Generator (async)
- `list_libraries(server_id=None)` → List[Dict]
- `get_library(library_id)` → Dict | None
- `toggle_library_sync(library_id, enabled)` → bool

**Path Mapping Operations:**

- `list_path_mappings(server_id=None, library_id=None)` → List[Dict]
- `add_path_mapping(server_id, library_id, plex_path, local_path)` → mapping_id
- `delete_path_mapping(mapping_id)` → bool

**Sync Operations:**

- `sync_content(server_id, library_keys, kinds, limit=None, dry_run=True)` → Generator (async)

### Next Steps (Future Phases):

- Phase 6: Remove Tkinter code and freeze monolith
- Phase 7: Quality and parity checks
- Consider refactoring CLI to also use `RetrovueAPI` for consistency

## Known Limitations & Future Improvements:

### 1. Content Sync Progress (Phase 4)

**Issue**: During "Sync (Write to DB)", the UI shows initial message then freezes until completion.

**Root Cause**: `IngestOrchestrator.ingest_library()` is a blocking synchronous function that processes all items before returning. It doesn't yield progress updates.

**Workaround**: Console/terminal shows real-time progress. GUI shows completion summary with full stats.

**TODO for Future**: Refactor `src/retrovue/plex/ingest.py` -> `IngestOrchestrator.ingest_library()` to be a generator that yields progress dicts as it processes each item/batch. This would allow:

- Real-time progress updates in GUI log
- Responsive UI during long sync operations
- Ability to show "X of Y items processed"
- Cancellation support

### 2. FFprobe Unicode Errors (Pre-existing)

**Issue**: Console shows `UnicodeDecodeError` warnings during sync:

```
UnicodeDecodeError: 'charmap' codec can't decode byte 0x8d/0x81/0x8f in position X
File "...\subprocess.py", line 1597, in _readerthread
File "...\encodings\cp1252.py", line 23, in decode
```

**Root Cause**: Media validation layer calls `ffprobe` subprocess without specifying encoding, causing Windows to default to cp1252 which can't handle some metadata characters in MKV containers.

**Impact**: Individual files with unicode metadata fail validation and are skipped. Sync continues successfully for other files. Affected files show as "Media file validation failed: Could not extract media information".

**TODO for Future**:

1. Fix `ffprobe` subprocess call in **`src/retrovue/plex/validation.py`**
2. Add proper encoding to subprocess call:
   - Option A: `encoding='utf-8', errors='replace'` to Popen/run()
   - Option B: Use `text=True, encoding='utf-8'` for text mode
   - Option C: Read as bytes and decode manually with error handling
3. Test with files that have unicode metadata (non-ASCII characters in container metadata)

---

## Phase 7 Progress Updates Improvement

**Status**: ✅ Complete (October 22, 2025)

**Issue**: User reported "clunky" progress with long pauses (10-15 seconds) before seeing first update after clicking "Sync". Also, validation errors were only visible in console (stderr), not in the GUI.

**Solution**: Added multiple stages of immediate feedback and moved errors to GUI:

1. **Immediate start messages** - Connecting, fetching from Plex
2. **First 5 items shown** - Display actual movie titles being scanned
3. **Removed "Validating batch..." message** - User found it sluggish
4. **Clean completion updates** - Every 50 items with inserted count and errors
5. **Validation errors in GUI** - All validation errors now appear in sync log with ⚠ prefix

**Result**: User sees activity within <1 second, no sluggish messages, and all errors are visible in the GUI sync log (not just console).

**Files Modified**:

- `src/retrovue/plex/ingest.py` - Added fetching, scanning stages; modified `_process_batch` and `_process_item` to return validation errors; yield errors to GUI

**Documentation**:

- `PROGRESS_IMPROVEMENTS.md` - Detailed breakdown of improvements

---

## Phase 8 - Scheduling Stack Pages (Placeholders)

**Status**: ✅ Complete (October 22, 2025)

**Goal**: Create placeholder UI for scheduling features (actual scheduling logic to be implemented in future phase).

**Features Added**:

1. **Schedules Tab** - New top-level tab for schedule management
   - Schedules subtab with empty table and "Add Schedule" button
   - History subtab with execution history table and log viewer
   - Info messages explaining feature is coming soon
   - Professional UI matching Importers page style

**Files Created**:

- `src/retrovue/gui/features/schedules/__init__.py` - Package init
- `src/retrovue/gui/features/schedules/page.py` - Schedules page with placeholder UI
- `PHASE_8_PLAN.md` - Comprehensive planning document for scheduling features

**Files Modified**:

- `src/retrovue/gui/router.py` - Added Schedules page to router

**Result**: Users can see the Schedules tab, understand that scheduling is planned, and get information about what features will be available. UI foundation is ready for future backend implementation.

**Documentation**:

- `PHASE_8_PLAN.md` - Detailed planning, architecture, and future roadmap
