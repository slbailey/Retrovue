# Series/Episode Usage Analysis

**Date:** 2025-01-27  
**Question:** Where and how are series/episodes used? Thought they were moved to asset metadata.

## Current State: Dual Storage

You're **partially correct** - series/episode information IS stored in asset metadata, but the database tables (`titles`, `seasons`, `episodes`) **still exist** and are linked via `episode_assets` junction table.

## Where Series/Episode Data is Stored

### 1. ✅ Asset Metadata (Primary Storage - Current Design)

**Location:** `asset_editorial.payload` (JSONB field)

**Fields stored:**
- `series_title` - The show/series name
- `season_number` - Season number (integer)
- `episode_number` - Episode number (integer)

**Example from Plex Importer:**
```python
# src/retrovue/adapters/importers/plex_importer.py lines 1298-1315
if series_title or meta.get("grandparentTitle"):
    editorial["series_title"] = series_title
if meta.get("parentIndex"):
    editorial["season_number"] = int(str(meta.get("parentIndex")))
if meta.get("index"):
    editorial["episode_number"] = int(str(meta.get("index")))
```

**Also stored in raw_labels:**
- `series:{series_title}`
- `season:{season_number}`
- `episode:{episode_number}`

### 2. ⚠️ Database Tables (Legacy/Unused?)

**Tables:**
- `titles` - Represents a title (movie or show)
- `seasons` - Represents a season of a show
- `episodes` - Represents an episode of a show
- `episode_assets` - Junction table linking episodes to assets (many-to-many)

**Relationships:**
- `Title` → `Season` (one-to-many)
- `Title` → `Episode` (one-to-many)
- `Season` → `Episode` (one-to-many, optional)
- `Episode` ↔ `Asset` (many-to-many via `episode_assets`)

## Where They're Actually Used

### ✅ Used: Asset Metadata (Editorial)

**Location:** `src/retrovue/adapters/importers/plex_importer.py`
- **Lines 1298-1315:** Plex importer stores series/episode info in `editorial` metadata
- This is the **primary** storage mechanism for series/episode data

**Location:** `src/retrovue/domain/metadata_schema.py`
- **Lines 153-160:** `EpisodeMetadata` model includes `series_id`, `season_number`, `episode_number`
- **Lines 337-341:** `EpisodeSidecar` includes `season_number`, `episode_number`

### ⚠️ Partially Used: Database Tables

**Location:** `src/retrovue/cli/commands/collection.py`
- **Lines 1067-1113:** Collection stats command queries `episode_assets`, `episodes`, `seasons`, `titles`
- **Lines 1167-1202:** Collection deletion command cleans up episode_assets, orphaned episodes, seasons, titles
- **Purpose:** Mostly for reporting/statistics and cleanup

**Location:** `src/retrovue/resolver/adapter.py`
- **Lines 15-75:** `resolve_asset_by_series_season_episode()` function
- **Problem:** Uses legacy `LibraryService` from `src_legacy/` which queries the old model
- **Status:** Legacy code, should be migrated to use asset metadata

### ❌ Not Used: Current Ingest Pipeline

**The current ingest pipeline does NOT create Title/Season/Episode records:**
- Plex importer only stores metadata in `asset_editorial.payload`
- No code creates `Title`, `Season`, or `Episode` records during ingest
- The `episode_assets` table is likely empty or only has legacy data

## The Problem

1. **Metadata is the source of truth** - Series/episode info is stored in `asset_editorial.payload`
2. **Database tables exist but are unused** - `titles`, `seasons`, `episodes` tables exist but aren't populated by current ingest
3. **Legacy resolver still uses old model** - `resolve_asset_by_series_season_episode()` uses legacy `LibraryService`
4. **Collection stats query unused tables** - Stats command queries tables that may have no data

## Recommendation

### Option 1: Remove Database Tables (Recommended)

Since series/episode data is stored in asset metadata:

1. **Drop the tables:**
   - `episode_assets` (junction table)
   - `episodes`
   - `seasons`
   - `titles`

2. **Update code:**
   - Remove queries from `collection.py` stats/deletion
   - Migrate `resolver/adapter.py` to query `asset_editorial.payload` instead of legacy tables
   - Update any tests that reference these tables

3. **Benefits:**
   - Simpler schema
   - Single source of truth (asset metadata)
   - Less maintenance

### Option 2: Keep Tables for Future Use

If you plan to use them for:
- Structured queries across episodes
- Episode relationships/grouping
- Series-level metadata

Then:
1. **Populate them during ingest** - Create Title/Season/Episode records when ingesting
2. **Link them to assets** - Populate `episode_assets` junction table
3. **Use them consistently** - Update resolver and queries to use the tables

## Current Usage Summary

| Component | Uses Metadata | Uses Tables | Status |
|-----------|---------------|-------------|--------|
| Plex Importer | ✅ Yes | ❌ No | Correct |
| Asset Editorial | ✅ Yes | ❌ No | Correct |
| Collection Stats | ❌ No | ⚠️ Yes | Legacy query |
| Resolver | ❌ No | ⚠️ Yes (legacy) | Needs migration |
| Ingest Pipeline | ✅ Yes | ❌ No | Correct |

## Conclusion

**You're correct** - series/episode data was moved to asset metadata (`asset_editorial.payload`). The database tables (`titles`, `seasons`, `episodes`) are **legacy/unused** and should be considered for removal, similar to the broadcast tables we just dropped.

The tables are only referenced in:
1. Collection stats/deletion commands (reporting/cleanup)
2. Legacy resolver (uses old `LibraryService`)

Both of these could be updated to use asset metadata instead.

