# Plex CLI Ingest (Single Episode, v0)

## Overview

This document describes the initial Plex CLI ingest functionality for Retrovue. The goal is to fetch one episode from Plex and upsert it into the content library (SQLite for now), with support for `--dry-run` mode.

## Goal

Fetch a single episode from Plex Media Server and upsert it into the Retrovue content library with full metadata preservation and path mapping support.

## Environment Variables

### Required Variables

```bash
# Plex server base URL (include protocol and port)
PLEX_BASEURL="http://192.168.1.100:32400"

# Plex authentication token
PLEX_TOKEN="your_plex_token_here"
```

### Optional Variables

```bash
# Custom server name for identification
PLEX_SERVER_NAME="HomePlex"

# Database URL (defaults to SQLite)
DATABASE_URL="sqlite:///retrovue.db"
```

## CLI Usage Examples

### 1. Verify Plex Connection

```bash
# Test connection to Plex server
retrovue plex:verify

# Expected output:
# ✓ Connected to Plex server: HomePlex (http://192.168.1.100:32400)
# ✓ Authentication successful
# ✓ Server version: 1.32.5.7516
```

### 2. Get Episode Information (Dry Run)

```bash
# Fetch episode metadata without inserting into database
retrovue plex:get-episode --rating-key 12345 --dry-run

# Human-readable output:
# Episode: "The Pilot" (S01E01)
# Show: "Breaking Bad"
# Duration: 00:58:30
# File: /media/TV Shows/Breaking Bad/Season 01/Breaking Bad - S01E01 - The Pilot.mkv
# Size: 1.2 GB
# 
# Proposed asset row:
# - title: "The Pilot"
# - show_title: "Breaking Bad"
# - season: 1
# - episode: 1
# - duration: 3510
# - file_path: "D:\TV Shows\Breaking Bad\Season 01\Breaking Bad - S01E01 - The Pilot.mkv"
# - plex_rating_key: 12345

# JSON output (--format json):
{
  "title": "The Pilot",
  "show_title": "Breaking Bad",
  "season": 1,
  "episode": 1,
  "duration": 3510,
  "file_path": "D:\\TV Shows\\Breaking Bad\\Season 01\\Breaking Bad - S01E01 - The Pilot.mkv",
  "plex_rating_key": 12345,
  "plex_updated_at": "2023-10-15T14:30:00Z",
  "file_size": 1288490188,
  "media_type": "episode"
}
```

### 3. Ingest Episode into Database

```bash
# Insert/update episode in content library
retrovue plex:ingest-episode --rating-key 12345

# Expected output:
# ✓ Episode ingested successfully
# - Asset ID: 42
# - Title: "The Pilot"
# - Show: "Breaking Bad"
# - Season 1, Episode 1
# - Duration: 00:58:30
# - File: D:\TV Shows\Breaking Bad\Season 01\Breaking Bad - S01E01 - The Pilot.mkv
```

### 4. With Path Mapping

```bash
# Map Plex paths to local paths
retrovue plex:ingest-episode --rating-key 12345 --map "/media/TV Shows"="/mnt/media/TV Shows"

# Multiple mappings
retrovue plex:ingest-episode --rating-key 12345 \
  --map "/media/TV Shows"="/mnt/media/TV Shows" \
  --map "/media/Movies"="/mnt/media/Movies"
```

## Path Mapping

### Purpose

Plex stores file paths as seen by the Plex server, but Retrovue needs local file paths for playback. Path mapping converts Plex paths to local paths.

### Syntax

```bash
--map "PLEX_PATH=LOCAL_PATH"
```

### Examples

```bash
# Windows mapping
--map "/media/TV Shows"="D:\TV Shows"

# Linux mapping  
--map "/media/TV Shows"="/mnt/media/TV Shows"

# Network share mapping
--map "/media/TV Shows"="\\server\media\TV Shows"
```

### Multiple Mappings

```bash
# Map different library types
retrovue plex:ingest-episode --rating-key 12345 \
  --map "/media/TV Shows"="/mnt/media/TV Shows" \
  --map "/media/Movies"="/mnt/media/Movies" \
  --map "/media/Music"="/mnt/media/Music"
```

## Acceptance Criteria

### 1. Connection Verification

```bash
retrovue plex:verify
```

**Success Criteria:**
- ✅ Connects to Plex server successfully
- ✅ Authentication token is valid
- ✅ Server information is displayed
- ✅ No connection errors

### 2. Episode Information Retrieval

```bash
retrovue plex:get-episode --rating-key 12345 --dry-run
```

**Success Criteria:**
- ✅ Fetches episode metadata from Plex
- ✅ Displays human-readable episode information
- ✅ Shows proposed asset row structure
- ✅ Supports `--format json` for machine-readable output
- ✅ Handles path mapping correctly
- ✅ No database modifications (dry-run mode)

### 3. Episode Ingestion

```bash
retrovue plex:ingest-episode --rating-key 12345
```

**Success Criteria:**
- ✅ Inserts new episode into assets table
- ✅ Updates existing episode if already present (idempotent)
- ✅ Preserves all metadata from Plex
- ✅ Applies path mapping correctly
- ✅ Returns success confirmation with asset details
- ✅ Handles errors gracefully (missing files, invalid rating keys)

## Database Schema

### Assets Table (SQLite)

```sql
CREATE TABLE assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    show_title TEXT,
    season INTEGER,
    episode INTEGER,
    duration INTEGER,  -- seconds
    file_path TEXT NOT NULL,
    file_size INTEGER,
    plex_rating_key TEXT UNIQUE,
    plex_updated_at TEXT,
    media_type TEXT,  -- 'episode', 'movie', 'clip'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## Error Handling

### Common Error Scenarios

```bash
# Invalid rating key
retrovue plex:get-episode --rating-key 99999
# Error: Episode not found (rating key: 99999)

# Connection failure
retrovue plex:verify
# Error: Cannot connect to Plex server (http://192.168.1.100:32400)
# Check PLEX_BASEURL and network connectivity

# Missing path mapping
retrovue plex:ingest-episode --rating-key 12345
# Warning: No path mapping provided
# File path may not be accessible locally: /media/TV Shows/...
```

## Out of Scope (v0)

The following features are **not included** in this initial version:

- ❌ **Streaming playback** - No video streaming functionality
- ❌ **Batch operations** - Only single episode processing
- ❌ **Schedule management** - No playlist or scheduling features
- ❌ **Multi-server support** - Single Plex server only
- ❌ **Library discovery** - Manual rating key specification required
- ❌ **Metadata enrichment** - No additional metadata processing beyond Plex data
- ❌ **File validation** - No local file existence checking

## Next Steps (Future Versions)

### v0.1: Episode Discovery

```bash
# Find episodes by show/season
retrovue plex:find-episode --show "Breaking Bad" --season 1 --episode 1

# List all episodes in a show
retrovue plex:list-episodes --show "Breaking Bad"
```

### v0.2: Playlist Management

```bash
# Create playlists from Plex libraries
retrovue plex:create-playlist --library "TV Shows" --name "Breaking Bad Marathon"

# Manage episode sequences
retrovue plex:playlist-add --playlist "Breaking Bad Marathon" --rating-key 12345
```

### v0.3: Batch Operations

```bash
# Ingest entire show
retrovue plex:ingest-show --show "Breaking Bad"

# Ingest library
retrovue plex:ingest-library --library "TV Shows"
```

## Implementation Notes

### CLI Command Structure

```bash
retrovue plex:verify                    # Test connection
retrovue plex:get-episode              # Fetch metadata (dry-run)
retrovue plex:ingest-episode           # Insert into database
```

### Required Dependencies

- `requests` - HTTP client for Plex API
- `sqlite3` - Database operations
- `typer` - CLI framework
- `pydantic` - Data validation

### Configuration

- Environment variables for Plex connection
- SQLite database for content storage
- Path mapping for file system integration
- JSON output format for automation
