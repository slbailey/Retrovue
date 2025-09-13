# Repository Cleanup Summary

## Overview
This cleanup focused on the `./src` directory, keeping only files that are directly or indirectly imported by the trusted entrypoint `cli/plex_sync.py`.

## What Was Moved to Legacy

### Moved to `src/_legacy/`:
- **`core/`** - Core functionality not used by plex_sync.py
  - `cli.py`, `database.py`, `guid_parser.py`, `path_mapping.py`
  - `plex_integration.py`, `streaming.py`, `tmm_integration.py`
- **`ui/`** - UI components not used by plex_sync.py
  - `main_window.py`, `import_worker.py`, `ui_bus.py`
- **`ui_v2/`** - UI v2 components not used by plex_sync.py
  - `main_window_v2.py`, `pages/browse_page.py`, `pages/libraries_page.py`
- **`__main__.py`** - Module entry point using core.cli
- **`version.py`** - Version information not imported by plex_sync.py
- **`__init__.py`** - Package init not used by plex_sync.py

### Moved to root level with `_legacy_` prefix:
- **`_legacy_main.py`** - Main server entry point using core modules
- **`_legacy_run_ui.py`** - UI launcher using ui modules  
- **`_legacy_run_ui_v2.py`** - UI v2 launcher using ui_v2 modules

## What Remains in `src/`

### Active Files (Used by plex_sync.py):
```
src/
└── retrovue/
    ├── __init__.py
    └── plex/
        ├── __init__.py
        ├── client.py      # Lazy import in plex_sync.py
        ├── config.py      # Lazy import in plex_sync.py
        ├── db.py          # Direct import
        ├── guid.py        # Direct import
        ├── ingest.py      # Lazy import in plex_sync.py
        ├── mapper.py      # Direct import
        └── pathmap.py     # Direct import
```

## Verification

✅ **plex_sync.py still works correctly:**
```bash
python -m cli.plex_sync --help
python -m cli.plex_sync libraries list --db .\retrovue.db
```

## Rollback Instructions

If you need to restore the legacy functionality:

1. **Restore from git history:**
   ```bash
   git checkout Plex-Integration-Focus -- src/
   git checkout Plex-Integration-Focus -- main.py
   git checkout Plex-Integration-Focus -- run_ui.py  
   git checkout Plex-Integration-Focus -- run_ui_v2.py
   ```

2. **Or restore from this branch:**
   ```bash
   git checkout repo-cleanup-plex-sync-only
   # Copy files back from _legacy/ and _legacy_* files
   ```

## Impact

- **Reduced complexity**: Only plex_sync.py dependencies remain
- **Clear separation**: Legacy code is preserved but isolated
- **Maintained functionality**: plex_sync.py works exactly as before
- **Easy rollback**: All changes are in git history

## Files Moved Summary

| Original Location | New Location | Reason |
|------------------|--------------|---------|
| `src/retrovue/core/` | `src/_legacy/core/` | Not used by plex_sync.py |
| `src/retrovue/ui/` | `src/_legacy/ui/` | Not used by plex_sync.py |
| `src/retrovue/ui_v2/` | `src/_legacy/ui_v2/` | Not used by plex_sync.py |
| `src/retrovue/__main__.py` | `src/_legacy/__main__.py` | Uses core.cli, not plex_sync.py |
| `src/retrovue/version.py` | `src/_legacy/version.py` | Not imported by plex_sync.py |
| `src/__init__.py` | `src/_legacy/__init__.py` | Not imported by plex_sync.py |
| `main.py` | `_legacy_main.py` | Uses core modules, not plex_sync.py |
| `run_ui.py` | `_legacy_run_ui.py` | Uses ui modules, not plex_sync.py |
| `run_ui_v2.py` | `_legacy_run_ui_v2.py` | Uses ui_v2 modules, not plex_sync.py |

**Total: 9 items moved (3 directories + 6 files)**
