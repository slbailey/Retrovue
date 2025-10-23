# Plex CLI Ingest (Single Episode, v0)

## Overview

This document describes the Plex CLI ingest functionality for Retrovue. The goal is to fetch one episode from Plex and upsert it into the content library with full metadata preservation and path mapping support.

## Goal

Fetch a single episode from Plex Media Server and upsert it into the Retrovue content library with full metadata preservation and path mapping support.

## Configuration

**Uses the active Plex server stored in the database (not env vars)**

The Plex CLI commands read Plex server configuration from the database rather than environment variables. This allows for multiple Plex servers and centralized configuration management.

### Adding a Plex Server

Before using the Plex CLI commands, you need to add a Plex server to the database:

```bash
# Add a Plex server (this would be done through the web interface or API)
# The server configuration includes:
# - base_url: Plex server URL (e.g., "http://192.168.1.100:32400")
# - token: Plex authentication token
# - name: Friendly name for the server
```

## CLI Usage Examples

### 1. Verify Plex Connection

```bash
# Test connection to Plex server
retrovue plex verify

# Expected output:
# ✓ Connected to Plex server at http://192.168.1.100:32400
#   Libraries available: 3
#   Status: connected

# JSON output:
retrovue plex verify --json
{
  "server_name": "Plex Server",
  "base_url": "http://192.168.1.100:32400",
  "libraries_count": 3,
  "status": "connected"
}
```

### 2. Get Episode Information (Dry Run)

**Using rating key (fast path):**

```bash
# Fetch episode metadata without inserting into database
retrovue plex get-episode 12345 --dry-run

# Human-readable output:
# Episode: The Pilot
# Series: Breaking Bad S01E01
# Plex path: /media/TV Shows/Breaking Bad/Season 01/Breaking Bad - S01E01 - The Pilot.mkv
# Local path: D:\TV Shows\Breaking Bad\Season 01\Breaking Bad - S01E01 - The Pilot.mkv
# File size: 1,288,490,188 bytes
# Duration: 58 minutes
# Hash: a1b2c3d4e5f6g7h8...
# Action: DRY_RUN
```

**Using series/season/episode (primary method):**

```bash
# Find episode by series, season, and episode number
retrovue plex get-episode --series "Batman TAS" --season 1 --episode 1 --dry-run

# Human-readable output:
# Episode: On Leather Wings
# Series: Batman TAS S01E01
# Plex path: /media/TV Shows/Batman TAS/Season 01/Batman TAS - S01E01 - On Leather Wings.mkv
# Local path: D:\TV Shows\Batman TAS\Season 01\Batman TAS - S01E01 - On Leather Wings.mkv
# File size: 1,200,000,000 bytes
# Duration: 22 minutes
# Hash: b2c3d4e5f6g7h8i9...
# Action: DRY_RUN
```

**JSON output:**

```bash
retrovue plex get-episode --series "Batman TAS" --season 1 --episode 1 --json
{
  "action": "DRY_RUN",
  "provenance": {
    "source": "plex",
    "source_rating_key": "12345",
    "source_guid": "com.plexapp.agents.thetvdb://12345"
  },
  "episode": {
    "series_title": "Batman TAS",
    "season_number": 1,
    "episode_number": 1,
    "title": "On Leather Wings"
  },
  "file": {
    "plex_path": "/media/TV Shows/Batman TAS/Season 01/Batman TAS - S01E01 - On Leather Wings.mkv",
    "resolved_path": "D:\\TV Shows\\Batman TAS\\Season 01\\Batman TAS - S01E01 - On Leather Wings.mkv",
    "duration_sec": 1320.0,
    "hash": "b2c3d4e5f6g7h8i9..."
  }
}
```

### 3. Ingest Episode into Database

**Using rating key (fast path):**

```bash
# Insert/update episode in content library
retrovue plex ingest-episode 12345

# Expected output:
# CREATED asset 550e8400-e29b-41d4-a716-446655440000
#   Episode: The Pilot
#   Series: Breaking Bad S01E01
#   Path: D:\TV Shows\Breaking Bad\Season 01\Breaking Bad - S01E01 - The Pilot.mkv
#   Size: 1,288,490,188 bytes
#   Duration: 58 minutes
```

**Using series/season/episode (primary method):**

```bash
# Find and ingest episode by series, season, and episode number
retrovue plex ingest-episode --series "Batman TAS" --season 1 --episode 1

# Expected output:
# CREATED asset 550e8400-e29b-41d4-a716-446655440001
#   Episode: On Leather Wings
#   Series: Batman TAS S01E01
#   Path: D:\TV Shows\Batman TAS\Season 01\Batman TAS - S01E01 - On Leather Wings.mkv
#   Size: 1,200,000,000 bytes
#   Duration: 22 minutes
```

**JSON output:**

```bash
retrovue plex ingest-episode --series "Batman TAS" --season 1 --episode 1 --json
{
  "rating_key": 12345,
  "asset_id": "550e8400-e29b-41d4-a716-446655440000",
  "episode_id": "550e8400-e29b-41d4-a716-446655440001",
  "title": "The Pilot",
  "series": "Breaking Bad",
  "season": 1,
  "episode": 1,
  "local_path": "D:\\TV Shows\\Breaking Bad\\Season 01\\Breaking Bad - S01E01 - The Pilot.mkv",
  "file_size": 1288490188,
  "file_hash": "a1b2c3d4e5f6g7h8...",
  "duration_ms": 3510000,
  "action": "CREATED"
}
```

### 4. Dry Run Mode

```bash
# Show what would be done without making changes
retrovue plex ingest-episode 12345 --dry-run

# Expected output:
# DRY RUN - No changes will be made
# Would ingest: The Pilot
# Local path: D:\TV Shows\Breaking Bad\Season 01\Breaking Bad - S01E01 - The Pilot.mkv
# File size: 1,288,490,188 bytes
# Duration: 58 minutes
```

## Path Mapping

### Purpose

Plex stores file paths as seen by the Plex server, but Retrovue needs local file paths for playback. Path mapping converts Plex paths to local paths using database-stored mappings.

### Database Configuration

Path mappings are stored in the database and configured through the web interface or API. The CLI commands automatically use these mappings to resolve Plex paths to local paths.

### How It Works

1. Plex provides a file path like `/media/TV Shows/Breaking Bad/Season 01/episode.mkv`
2. The CLI looks up path mappings in the database
3. If a mapping exists (e.g., `/media/TV Shows` → `D:\TV Shows`), it applies the transformation
4. The resolved local path is checked for file existence
5. If the file doesn't exist, the command fails with a clear error message

### Error Handling

```bash
# If no path mappings are configured:
retrovue plex get-episode --rating-key 12345
# Error: No path mappings configured. Cannot resolve Plex path: /media/TV Shows/...

# If the resolved path doesn't exist:
retrovue plex get-episode --rating-key 12345
# Error: Resolved path does not exist: D:\TV Shows\Breaking Bad\Season 01\episode.mkv
# Original Plex path: /media/TV Shows/Breaking Bad/Season 01/episode.mkv
```

## Acceptance Criteria

### 1. Connection Verification

```bash
retrovue plex verify
```

**Success Criteria:**

- ✅ Connects to Plex server successfully
- ✅ Authentication token is valid
- ✅ Server information is displayed
- ✅ No connection errors

### 2. Episode Information Retrieval

**Using rating key:**

```bash
retrovue plex get-episode 12345 --dry-run
```

**Using series/season/episode:**

```bash
retrovue plex get-episode --series "Batman TAS" --season 1 --episode 1 --dry-run
```

**Success Criteria:**

- ✅ Fetches episode metadata from Plex (both methods)
- ✅ Displays human-readable episode information
- ✅ Shows proposed asset row structure in specified JSON format
- ✅ Supports `--json` for machine-readable output
- ✅ Handles path mapping correctly
- ✅ No database modifications (dry-run mode)
- ✅ Handles series/season/episode lookup with proper error messages

### 3. Episode Ingestion

**Using rating key:**

```bash
retrovue plex ingest-episode 12345
```

**Using series/season/episode:**

```bash
retrovue plex ingest-episode --series "Batman TAS" --season 1 --episode 1
```

**Success Criteria:**

- ✅ Inserts new episode into assets table (both methods)
- ✅ Updates existing episode if already present (idempotent)
- ✅ Preserves all metadata from Plex
- ✅ Applies path mapping correctly
- ✅ Returns success confirmation with asset details
- ✅ Handles errors gracefully (missing files, invalid rating keys, series not found)

### 4. Idempotency Test

```bash
# Run the same command twice
retrovue plex ingest-episode 12345
retrovue plex ingest-episode 12345

# Second run should update the same row, not create a duplicate
```

**Success Criteria:**

- ✅ First run creates the asset
- ✅ Second run updates the same asset (idempotent)
- ✅ No duplicate entries in database

## Database Schema

The Plex CLI commands use the existing Retrovue database schema with the following key tables:

### Assets Table

```sql
CREATE TABLE assets (
    id UUID PRIMARY KEY,
    uri TEXT NOT NULL UNIQUE,
    size BIGINT NOT NULL,
    duration_ms INTEGER,
    video_codec VARCHAR(50),
    audio_codec VARCHAR(50),
    container VARCHAR(50),
    hash_sha256 VARCHAR(64),
    discovered_at TIMESTAMP DEFAULT NOW(),
    canonical BOOLEAN DEFAULT FALSE
);
```

### Episodes Table

```sql
CREATE TABLE episodes (
    id UUID PRIMARY KEY,
    title_id UUID REFERENCES titles(id),
    season_id UUID REFERENCES seasons(id),
    number INTEGER,
    name VARCHAR(255),
    external_ids JSON,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Provider References

```sql
CREATE TABLE provider_refs (
    id UUID PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    provider VARCHAR(50) NOT NULL,
    provider_key TEXT NOT NULL,
    raw JSON,
    title_id UUID REFERENCES titles(id),
    episode_id UUID REFERENCES episodes(id),
    asset_id UUID REFERENCES assets(id)
);
```

### Path Mappings

```sql
CREATE TABLE path_mappings (
    id UUID PRIMARY KEY,
    collection_id UUID REFERENCES source_collections(id),
    plex_path VARCHAR(500) NOT NULL,
    local_path VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Error Handling

### Common Error Scenarios

```bash
# No Plex servers configured
retrovue plex verify
# Error: No Plex servers configured. Please add a Plex server first.

# Invalid rating key
retrovue plex get-episode 99999
# Error: Episode not found (rating key: 99999)

# Connection failure
retrovue plex verify
# Error: Cannot connect to Plex server (http://192.168.1.100:32400)
# Check server configuration and network connectivity

# No path mappings configured
retrovue plex get-episode 12345
# Error: No path mappings configured. Cannot resolve Plex path: /media/TV Shows/...

# Resolved path doesn't exist
retrovue plex get-episode 12345
# Error: Resolved path does not exist: D:\TV Shows\Breaking Bad\Season 01\episode.mkv
# Original Plex path: /media/TV Shows/Breaking Bad/Season 01/episode.mkv
```

## Out of Scope (v0)

The following features are **not included** in this initial version:

- ❌ **Streaming playback** - No video streaming functionality
- ❌ **Batch operations** - Only single episode processing
- ❌ **Schedule management** - No playlist or scheduling features
- ❌ **Multi-server support** - Single Plex server only
- ❌ **Library discovery** - Manual rating key specification required
- ❌ **Advanced metadata enrichment** - Basic ffprobe analysis only
- ❌ **File validation** - Basic file existence checking only

## Next Steps (Future Versions)

### v0.1: Episode Discovery

```bash
# Find episodes by show/season
retrovue plex find-episode --show "Breaking Bad" --season 1 --episode 1

# List all episodes in a show
retrovue plex list-episodes --show "Breaking Bad"
```

### v0.2: Playlist Management

```bash
# Create playlists from Plex libraries
retrovue plex create-playlist --library "TV Shows" --name "Breaking Bad Marathon"

# Manage episode sequences
retrovue plex playlist-add --playlist "Breaking Bad Marathon" --rating-key 12345
```

### v0.3: Batch Operations

```bash
# Ingest entire show
retrovue plex ingest-show --show "Breaking Bad"

# Ingest library
retrovue plex ingest-library --library "TV Shows"
```

## Implementation Notes

### CLI Command Structure

```bash
retrovue plex verify                    # Test connection
retrovue plex get-episode              # Fetch metadata (dry-run)
retrovue plex ingest-episode           # Insert into database
```

### Required Dependencies

- `requests` - HTTP client for Plex API
- `sqlalchemy` - Database operations
- `typer` - CLI framework
- `ffprobe` - Media analysis
- `structlog` - Logging

### Configuration

- Database-stored Plex server configuration
- Database-stored path mappings
- JSON output format for automation
- Dry-run mode for safe testing
