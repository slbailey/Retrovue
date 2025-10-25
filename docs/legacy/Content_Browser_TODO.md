# Content Browser - Enhancement TODO

> **Legacy Document** — Pre-Alembic version, retained for reference only.

## Current Status (v0.1)

The Content Browser currently supports:

- ✅ Browse modes: All Content, By Library, TV Shows, Movies, By Genre, Media Files
- ✅ Filter by library and search
- ✅ TV Show navigation via dropdown selectors (Show → Season)
- ✅ Display content metadata (Title, Type, Duration, Year, Show, Library, Rating)
- ✅ Display media file paths (Plex Path, Mapped Path)
- ✅ VLC Play button for playable content (movies/episodes)
- ✅ Smart path/play button visibility (only shows for actual playable content, not show/season lists)

## Planned Enhancements

### 1. Double-Click Navigation

**Priority: High**

Currently, users navigate TV shows via dropdown menus. This should be enhanced to support intuitive double-click navigation:

- **Double-click on Show** → Navigate to that show's seasons
- **Double-click on Season** → Navigate to that season's episodes
- **Double-click on Episode/Movie** → Play in VLC (same as clicking Play button)

**Implementation Notes:**

- Add `doubleClicked` signal handler to `content_table`
- Detect current browse mode and item type
- Update `current_show_id` / `current_season_id` accordingly
- Call `refresh_content()` to update the view
- Add breadcrumb navigation to show current drill-down path (e.g., "Shows → 7 Little Johnstons → Season 1")

### 2. Enhanced Media File Display

**Priority: Medium**

Currently, duration is shown in minutes (e.g., "90 min"). For media files, this should be expanded to show precise runtime:

**Current:**

```
Duration: 90 min
```

**Enhanced:**

```
Duration: 01:30:45.23  (90 min)
```

**Implementation Notes:**

- Update `populate_content_table()` to format `duration_ms` as `HH:MM:SS.ss`
- Consider adding this as a separate column for media file details
- Option 1: Replace existing Duration column format
- Option 2: Add new "Runtime" column that only populates for playable content
- Source: `media_files.duration_ms` field (stored in milliseconds)

### 3. Breadcrumb Navigation

**Priority: Medium**

Add a breadcrumb trail above the content table to show the current navigation path and allow quick navigation back:

```
[Content Browser] > [TV Shows] > [7 Little Johnstons] > [Season 1]
```

- Each segment clickable to navigate back
- Shows current filter/selection state
- Helps users understand where they are in the hierarchy

### 4. Context Menu Enhancements

**Priority: Low**

Expand the right-click context menu with additional options:

- "Open in File Explorer" (open folder containing the file)
- "Copy Plex Path" / "Copy Mapped Path" (copy to clipboard)
- "Show All Episodes" (when right-clicking an episode, show all episodes for that show)
- "Play Next Episode" (auto-play next episode in sequence)

### 5. Keyboard Navigation

**Priority: Low**

Add keyboard shortcuts for common actions:

- **Enter** → Play selected content
- **Backspace** → Navigate up one level (e.g., from episodes back to seasons)
- **Arrow Keys** → Navigate content list (already works)
- **Ctrl+F** → Focus search box

### 6. Multi-File Support

**Priority: Low**

Currently, only the first media file is shown for content items. Some content may have multiple files (e.g., different quality versions):

- Show indicator when multiple files exist (e.g., "▶ Play (2 files)")
- Dropdown or submenu to select which file to play
- Show all file paths and codecs in "View Files" dialog

## Technical Considerations

### Database Schema

Current schema supports all planned features. Key tables:

- `content_items` - episodes, movies, etc.
- `media_files` - file paths, codecs, durations
- `shows` - TV show metadata
- `seasons` - season metadata

### Performance

- Media file queries are per-row, which may be slow for large content libraries
- Consider batch fetching media files for all visible rows
- Add caching for media file data during a browse session

### UI/UX

- Ensure double-click doesn't conflict with single-click selection
- Provide visual feedback during navigation transitions
- Consider adding a "Back" button as alternative to breadcrumbs

## Future Vision

The Content Browser should eventually support:

- **Playlist Creation** - Select multiple items and create a playlist
- **Smart Collections** - Auto-generated collections based on criteria (e.g., "90s Action Movies")
- **Recently Added** - Quick view of newly synced content
- **Watch History** - Integration with play log to show watched/unwatched status
- **Thumbnail Previews** - Show poster/thumbnail images for content
- **Sorting Options** - Sort by title, year, rating, duration, date added
- **Advanced Filters** - Filter by rating, year range, codec, resolution

---

**Last Updated:** 2025-01-22  
**Version:** 0.1  
**Status:** Active Development
