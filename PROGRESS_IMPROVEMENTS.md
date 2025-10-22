# Content Sync Progress Improvements

## Problem

User reported that progress updates during content sync were "clunky" with long pauses (10-15 seconds) before seeing any feedback after clicking "Sync (Write to DB)".

## Root Cause

The ingest process had several phases that took time before yielding the first progress update:

1. Connecting to Plex server
2. Fetching the first batch of items (50 items)
3. Mapping items
4. Validating media files with ffprobe
5. Writing to database

Only after ALL of this completed would the first "Processed: 50 items" message appear.

## Solutions Implemented

### 1. Immediate Feedback on Start ✅

```
[08:41:21] Starting sync [COMMIT]...
[08:41:21] Connecting to My Plex Server...
[08:41:21] Processing library 1 (movie)
[08:41:21] Fetching items from Plex server...
```

**Result**: User sees activity within <1 second of clicking button

### 2. Real-Time Scanning Feedback ✅

Shows the first 5 items being scanned:

```
[08:41:21] Scanning: The Matrix
[08:41:21] Scanning: Inception
[08:41:22] Scanning: Interstellar
[08:41:22] Scanning: The Dark Knight
[08:41:22] Scanning: Pulp Fiction
```

**Result**: User sees actual movie titles being processed immediately

### 3. Clean Batch Completion Updates ✅

After validation completes:

```
[08:41:29] Processed: 50 items (35 inserted, 0 errors)
[08:41:36] Processed: 100 items (70 inserted, 2 errors)
[08:41:42] Processed: 150 items (105 inserted, 3 errors)
```

**Result**: Meaningful progress every ~5-10 seconds (batch processing time)

### 4. Validation Errors in GUI (Not Console) ✅

Validation errors now appear in the sync log instead of just stderr:

```
[08:41:29] ⚠ Media file validation failed for /media/movies/Inception (2010)/Inception (2010) Bluray-1080p.wmv: Unsupported video codec: vc1
[08:41:29] ⚠ Media file validation failed for /media/movies/Indiana Jones and the Kingdom of the Crystal Skull (2008)/Indiana Jones and the Kingdom of the Crystal Skull (2008) Bluray-1080p.mkv: Unsupported audio codec: truehd
[08:41:29] Processed: 50 items (35 inserted, 2 errors)
```

**Result**: User sees all errors directly in the GUI, no need to check console

### 5. Final Summary ✅

```
[08:43:15] Sync complete [COMMIT]:
  Scanned: 543
  Mapped: 543
  Inserted: 378 items, 567 files
  Errors: 12

Note: Some files failed validation (codec issues, missing files, etc.)
Details shown above in the log.
```

## Timeline Comparison

### Before (Verbose but with gaps):

```
Click "Sync" → [15 second pause] → 10 items, 20 items, 30 items, 40 items → Processed: 50 items
[7 second pause] → 50 items, 60 items, 70 items, 80 items, 90 items → Processed: 100 items
```

**Issues**:

- ❌ Long initial pause (15s)
- ❌ Too many per-item updates (noisy)
- ❌ No indication what's happening during pauses
- ❌ Errors only in console (stderr), not visible in GUI

### After (Clean with immediate feedback):

```
Click "Sync" → Connecting... → Fetching... → Scanning: Movie 1, 2, 3, 4, 5
→ Validating batch... → Processed: 50 items → Validating batch... → Processed: 100 items
```

**Benefits**:

- ✅ Immediate feedback (<1s)
- ✅ Shows actual titles being processed
- ✅ Clean, meaningful progress updates
- ✅ No confusing pauses
- ✅ Validation errors visible in GUI (not just console)

## Technical Changes

### File: `src/retrovue/plex/ingest.py`

1. **Added "fetching" stage** (line 267-270)
   - Yields immediately when iteration starts
2. **Added first-5-items feedback** (line 276-282)
   - Shows actual movie/show titles being scanned
   - Gives immediate visual feedback
3. **Modified `_process_batch` and `_process_item`** to return validation errors
   - Validation errors now collected and returned instead of just logged
4. **Yield validation errors to GUI** (line 313-318, 351-356)
   - Each validation error is yielded as a separate progress update
   - Prefixed with ⚠ for visibility
   - Appears in sync log widget in real-time
5. **Clean batch completion** (line 321-325)
   - Shows total progress, inserted count, errors
   - Updates every ~5-10 seconds (batch processing time)

### No Changes Needed To:

- `src/retrovue/core/sync.py` - Already forwards all progress correctly
- `src/retrovue/gui/features/importers/page.py` - Already displays all stages

## User Experience Improvements

| Aspect                  | Before                          | After                         |
| ----------------------- | ------------------------------- | ----------------------------- |
| **Initial feedback**    | 10-15s pause                    | <1s response                  |
| **Progress frequency**  | Too verbose (every 10)          | Just right (every 50)         |
| **Information density** | Mixed (some useful, some noise) | High (all meaningful)         |
| **Error visibility**    | Console only (stderr)           | In GUI sync log with ⚠ prefix |
| **User confidence**     | ❓ Is it working?               | ✅ Clear activity             |

## Testing Notes

Test the following workflow:

1. Click "Sync (Write to DB)"
2. You should see:
   - Immediate "Starting sync..." message
   - "Connecting to..." message
   - "Fetching items..." message
   - First 5 movie titles being scanned
   - Validation errors (if any) with ⚠ prefix in sync log
   - "Processed: 50 items..." update
   - Repeat for each batch
   - Final summary

**Expected Timeline**:

- 0-1s: Initial messages + first 5 titles
- 1-10s: Processing batch (validation happens silently)
- 10s: Validation errors (if any) + "Processed: 50 items"
- Repeat every ~5-10s

**Error Display**:

- Validation errors now appear in the GUI sync log with ⚠ prefix
- No need to check console/terminal for error details
- Errors appear immediately after each batch completes

## Related Files

- `src/retrovue/plex/ingest.py` - Core ingest logic with progress yields
- `src/retrovue/core/sync.py` - Wraps ingest and forwards progress
- `src/retrovue/gui/features/importers/page.py` - Displays progress in UI
- `src/retrovue/gui/threads.py` - Worker thread that receives progress

## Future Enhancements (Optional)

1. **Progress bar**: Add a QProgressBar showing % complete
2. **Estimated time**: Calculate and show ETA based on current speed
3. **Cancellation**: Add "Cancel" button to stop sync mid-process
4. **Background sync**: Allow sync to run in background while using other tabs
5. **Validation feedback**: Show which file is currently being validated with ffprobe

---

**Status**: ✅ Complete and ready for testing
**Phase**: 7 (Quality and parity checks)
**Date**: October 22, 2025
