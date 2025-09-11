# Plex Integration Documentation

## Overview

The Plex integration in Retrovue provides comprehensive functionality for importing and synchronizing content from Plex Media Server. It supports multiple servers, intelligent sync operations, robust error handling, and advanced performance optimizations including timestamp-based change detection and pagination support.

## Architecture

### Core Components

1. **`PlexImporter`** - Main class handling all Plex API interactions
2. **`PlexPathMappingService`** - Converts Plex server paths to local filesystem paths
3. **`GUIDParser`** - Parses and normalizes external identifiers (TVDB, TMDB, IMDB, Plex)
4. **Database Integration** - Stores servers, path mappings, and imported content
5. **UI Integration** - Provides user interface for server management and sync operations

### Key Features

- **Multi-Server Support**: Manage multiple Plex servers with individual configurations
- **Intelligent Sync**: Timestamp-based sync that only updates changed content for dramatic performance improvements
- **Episode-Level Granularity**: Each TV episode is stored separately for precise control
- **Advanced Path Mapping**: Complete translation between Plex server paths and local filesystem paths
- **GUID-Based Identification**: Use stable external identifiers for reliable content matching
- **Progress Tracking**: Real-time progress updates with dual-level progress bars
- **Conflict Resolution**: Handle content that exists in multiple libraries
- **Pagination Support**: Automatic handling of large episode collections with pagination
- **Server-Scoped Operations**: Safe multi-server support with proper data isolation
- **Robust Error Handling**: Comprehensive error surfacing and recovery mechanisms
- **JSON/XML Response Handling**: Automatic detection and parsing of both response formats

## Data Flow

### 1. Server Management

```
User → UI → Database → PlexImporter
```

- Servers are stored in `plex_servers` table
- Each server has: name, URL, token, active status
- Path mappings stored in `plex_path_mappings` table

### 2. Content Sync Process

```
PlexImporter → Plex API → Database → UI Progress Updates
```

1. **Library Discovery**: Get all libraries from Plex server
2. **Content Fetching**: Retrieve movies/shows from each library
3. **Change Detection**: Compare Plex timestamps with database
4. **Content Processing**: Import/update only changed items
5. **Progress Reporting**: Send updates to UI via callbacks

### 3. Episode Processing

```
Show → Episodes → Media Files → Database
```

- Each show creates one record in `shows` table
- Each episode creates one record in `episodes` table
- Each episode links to a `media_files` record
- GUIDs stored in `show_guids` table for disambiguation

## API Endpoints Used

### Library Management
- `GET /library/sections` - List all libraries
- `GET /library/sections/{key}` - Get library details and root paths
- `GET /library/sections/{key}/all` - Get all items in library

### Content Retrieval
- `GET /library/sections/{key}/allLeaves` - Get all episodes (TV shows)
- `GET {show_key}/allLeaves` - Get episodes for specific show
- `GET /status/sessions` - Test server connectivity

### Search and Discovery
- `GET /library/sections/all?type=2&title={title}&year={year}` - Search shows by title/year

## Database Schema

### Core Tables

#### `plex_servers`
- `id` (INTEGER PRIMARY KEY)
- `name` (TEXT) - Server display name
- `server_url` (TEXT) - Plex server URL
- `token` (TEXT) - Authentication token
- `is_active` (BOOLEAN) - Whether server is active
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### `plex_path_mappings`
- `id` (INTEGER PRIMARY KEY)
- `server_id` (INTEGER) - Foreign key to plex_servers
- `library_root` (TEXT) - Library root path on Plex server
- `library_name` (TEXT) - Library display name
- `plex_path` (TEXT) - Plex server path prefix
- `local_path` (TEXT) - Local filesystem path prefix
- `created_at` (TIMESTAMP)

#### `shows`
- `id` (INTEGER PRIMARY KEY)
- `title` (TEXT) - Show title
- `year` (INTEGER) - Release year
- `total_seasons` (INTEGER)
- `total_episodes` (INTEGER)
- `show_rating` (TEXT) - Content rating
- `show_summary` (TEXT)
- `genre` (TEXT)
- `studio` (TEXT)
- `originally_available_at` (TEXT)
- `guid_primary` (TEXT) - Primary external identifier
- `source_type` (TEXT) - Always 'plex'
- `source_id` (TEXT) - Plex GUID
- `server_id` (INTEGER) - Foreign key to plex_servers
- `updated_at` (INTEGER) - Plex timestamp (Unix epoch seconds)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### `episodes`
- `id` (INTEGER PRIMARY KEY)
- `media_file_id` (INTEGER) - Foreign key to media_files
- `show_id` (INTEGER) - Foreign key to shows
- `episode_title` (TEXT)
- `season_number` (INTEGER)
- `episode_number` (INTEGER)
- `rating` (TEXT) - Content rating
- `summary` (TEXT)
- `updated_at` (INTEGER) - Plex timestamp (Unix epoch seconds)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### `media_files`
- `id` (INTEGER PRIMARY KEY)
- `file_path` (TEXT) - Local file path (accessible filesystem path)
- `plex_path` (TEXT) - Plex server path (internal Plex path)
- `duration` (INTEGER) - Duration in milliseconds
- `media_type` (TEXT) - 'movie' or 'episode'
- `source_type` (TEXT) - Always 'plex'
- `source_id` (TEXT) - Plex GUID
- `library_name` (TEXT) - Library name from Plex
- `server_id` (INTEGER) - Foreign key to plex_servers
- `created_at` (TIMESTAMP)
- `updated_at` (INTEGER) - Plex timestamp (Unix epoch seconds)

## Key Methods

### PlexImporter Class

#### `__init__(server_id, database, status_callback)`
- Initialize importer with server ID from database
- Load server configuration (URL, token, name)
- Initialize path mapping service

#### `test_connection() -> bool`
- Test connectivity to Plex server
- Uses `/status/sessions` endpoint
- Returns True if connection successful

#### `get_libraries() -> List[Dict]`
- Retrieve all libraries from Plex server
- Returns list of library metadata including key, title, type, agent

#### `sync_all_libraries(progress_callback) -> Dict[str, int]`
- Main sync method for all libraries
- Processes each library with progress tracking
- Returns counts of updated/added/removed items
- Handles orphaned content removal

#### `sync_library(library_key, library_type) -> Dict[str, int]`
- Sync specific library
- Delegates to `_sync_movie_library` or `_sync_show_library`

#### `discover_shows_by_title(title, year) -> List[Dict]`
- Search for shows by title and optional year
- Returns list of matching shows with disambiguation info
- Used for manual show selection

### Path Mapping

#### `PlexPathMappingService.get_local_path(plex_path, library_root) -> str`
- Convert Plex server path to local filesystem path
- Uses configured path mappings
- Handles multiple mapping priorities

### GUID Processing

#### `GUIDParser.parse_guid(guid) -> Tuple[str, str]`
- Parse Plex GUID into provider and external_id
- Supports TVDB, TMDB, IMDB, and Plex formats
- Returns (provider, external_id) tuple

#### `extract_guids_from_plex_metadata(metadata) -> List[str]`
- Extract all GUIDs from Plex metadata structure
- Handles both direct `guid` field and `Guid` array

## Sync Logic

### Movie Sync Process

1. **Fetch Movies**: Get all movies from Plex library
2. **Check Existence**: Compare Plex GUIDs with database
3. **Update Existing**: Only update if Plex timestamp differs
4. **Add New**: Import movies not in database
5. **Remove Orphaned**: Remove movies no longer in Plex

### Show Sync Process

1. **Fetch Shows**: Get all shows from Plex library
2. **Process Episodes**: For each show, get all episodes
3. **Episode Sync**: Update/add/remove episodes individually
4. **Show Metadata**: Update show-level information
5. **GUID Storage**: Store all external identifiers

### Timestamp-Based Change Detection

- Plex provides `updatedAt` timestamps for all content
- Database stores `updated_at` (INTEGER epoch seconds) for comparison
- Only content with different timestamps is processed
- Dramatically reduces processing time for large libraries (10-50x performance improvement)
- Handles both show-level and episode-level change detection
- Automatic fallback for content without timestamps

## Error Handling

### Connection Errors
- Network timeouts handled gracefully
- Invalid tokens return clear error messages
- Server unavailable shows appropriate status

### Data Errors
- Missing required fields logged and skipped
- Invalid GUIDs handled without crashing
- Database constraint violations caught and reported
- JSON/XML parsing errors handled gracefully with automatic format detection
- Path mapping errors logged with fallback to original paths

### Progress Reporting
- Dual-level progress: library progress + item progress
- Status messages for important events
- Error messages for failed operations

## Performance Optimizations

### Caching
- Library root paths cached to avoid repeated API calls
- Database queries optimized with lookup dictionaries
- Server configurations cached during sync operations
- Path mapping service cached for performance

### Batch Operations
- Database operations batched where possible
- Progress callbacks batched to reduce UI updates
- API calls minimized through intelligent caching

### Memory Management
- Large datasets processed in chunks
- Database connections properly managed
- Temporary objects cleaned up promptly
- Pagination support for large episode collections
- Server-scoped operations to prevent memory bloat

## Configuration

### Server Setup
1. Add Plex server via UI or database
2. Configure path mappings for each library
3. Test connection to verify setup
4. Enable/disable libraries for sync

### Path Mapping Examples
```
Plex Path: /media/movies
Local Path: D:\Media\Movies

Plex Path: /othermedia/godzilla
Local Path: E:\Godzilla Collection

Plex Path: /media/tv
Local Path: \\server\share\tv
```

### Path Mapping Features
- **Automatic Path Separation**: Database stores both Plex paths and local paths
- **Server-Scoped Mappings**: Each server can have different path mappings
- **Longest Prefix Matching**: Intelligent selection of best matching mapping
- **Fallback Handling**: Uses original path if no mapping found

### Library Configuration
- Each library can be enabled/disabled for sync
- Path mappings configured per library root
- Sync preferences stored in database

## Usage Examples

### Basic Server Setup
```python
from retrovue.core.plex_integration import create_plex_importer

# Create importer
importer = create_plex_importer(server_id, database, status_callback)

# Test connection
if importer.test_connection():
    # Sync all libraries
    results = importer.sync_all_libraries(progress_callback)
    print(f"Updated: {results['updated']}, Added: {results['added']}")
```

### Manual Show Discovery
```python
# Search for specific show
shows = importer.discover_shows_by_title("Breaking Bad", 2008)

# Sync specific show
results = importer.sync_show_by_title_and_year("Breaking Bad", 2008)
```

### Path Mapping
```python
# Get local path for Plex file
plex_path = "/media/movies/Avengers (2012)/Avengers.mkv"
local_path = importer.get_local_path(plex_path, "/media/movies")
# Returns: "D:\Media\Movies\Avengers (2012)\Avengers.mkv"
```

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check server URL and token
   - Verify network connectivity
   - Ensure Plex server is running

2. **Path Mapping Issues**
   - Verify path mappings are correct
   - Check library root paths match Plex configuration
   - Ensure local paths exist and are accessible

3. **Sync Performance**
   - Large libraries may take time to sync
   - Progress bars show current status
   - Debug logging can be enabled for detailed information

4. **Content Not Found**
   - Check if content exists in Plex
   - Verify library is enabled for sync
   - Check GUID parsing for external identifiers

### Debug Information

- Enable debug logging for detailed sync information
- Check database for stored content and timestamps
- Verify path mappings in database
- Test individual library sync operations

## Future Enhancements

### Planned Features
- Content quality filtering
- Advanced search and filtering
- Bulk operations for content management
- Integration with other media servers
- Advanced scheduling metadata
- Content validation and codec checking

### Performance Improvements
- Parallel processing for large libraries
- Background sync operations
- Advanced caching strategies
- Database query optimization
- Incremental sync optimizations (already implemented)
- Pagination for very large libraries (already implemented)

## API Reference

### PlexImporter Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `test_connection()` | Test server connectivity | None | bool |
| `get_libraries()` | Get all libraries | None | List[Dict] |
| `sync_all_libraries()` | Sync all libraries | progress_callback | Dict[str, int] |
| `sync_library()` | Sync specific library | library_key, library_type | Dict[str, int] |
| `discover_shows_by_title()` | Search shows | title, year | List[Dict] |
| `get_local_path()` | Convert path | plex_path, library_root | str |

### Database Methods

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `add_plex_server()` | Add server | name, url, token | int |
| `get_plex_servers()` | Get all servers | None | List[Dict] |
| `add_plex_path_mapping()` | Add path mapping | plex_path, local_path, server_id | int |
| `get_plex_path_mappings()` | Get path mappings | server_id | List[Dict] |

This documentation provides a comprehensive overview of the Plex integration system. For specific implementation details, refer to the source code in `src/retrovue/core/plex_integration.py`.
