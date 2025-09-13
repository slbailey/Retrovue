# Dev Tools

This directory contains development and testing tools for Retrovue.

## dev_sync.py

A headless command-line tool for syncing Plex libraries without using the UI. This tool is useful for:

- Testing the sync functionality
- Validating digests and selective expansion
- Testing missing→deleted state transitions
- Validating dynamic path mapping
- Running sync operations in scripts or CI/CD

### Usage

```bash
# Sync all selected libraries across all servers
python tools/dev_sync.py --all-selected

# Sync selected libraries on a specific server
python tools/dev_sync.py --server-selected 1

# Sync one specific library by server ID and section key
python tools/dev_sync.py --library 1 3

# Force full expansion (bypass selective expansion)
python tools/dev_sync.py --all-selected --deep

# Dry run (don't make changes, just test)
python tools/dev_sync.py --all-selected --dry-run

# Output results as JSON
python tools/dev_sync.py --all-selected --json

# Use a different database file
python tools/dev_sync.py --all-selected --db /path/to/other.db
```

### Options

- `--all-selected`: Sync all selected libraries across all active servers
- `--server-selected SERVER_ID`: Sync selected libraries on a specific server
- `--library SERVER_ID SECTION_KEY`: Sync one specific library
- `--deep`: Force full expansion (bypass selective expansion based on digests)
- `--dry-run`: Don't make changes, just test the sync process
- `--json`: Output final summary as JSON
- `--db PATH`: Use a different database file (default: retrovue.db)

### Output

The tool provides real-time progress output showing:
- `[START]`: When a library sync begins
- `[PAGE]`: Progress updates during sync (if available)
- `[DONE]`: When a library sync completes with summary

Example output:
```
[START] server=1 library=3
[DONE]  server=1 lib=3 +5 ~10 !0 missing↑2 deleted↑1
```

Where:
- `+5`: 5 items changed/updated
- `~10`: 10 items skipped (no changes)
- `!0`: 0 errors
- `missing↑2`: 2 items promoted from missing to deleted
- `deleted↑1`: 1 item promoted from deleted to removed

### Requirements

- Python 3.7+
- Retrovue database with configured Plex servers
- Active Plex servers with libraries marked for sync
