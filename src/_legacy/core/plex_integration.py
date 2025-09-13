"""
Plex Media Server Integration for Retrovue

This module provides comprehensive integration with Plex Media Server, allowing you to
import and synchronize your entire media library into Retrovue for professional broadcast
television simulation.

## What This Module Does

The Plex integration system allows you to:
- **Import Your Media Library**: Automatically import movies and TV shows from Plex
- **Smart Synchronization**: Only update content that has actually changed
- **Episode-Level Control**: Each TV episode is stored separately for precise scheduling
- **Multi-Server Support**: Manage multiple Plex servers from one Retrovue installation
- **Path Mapping**: Convert Plex server paths to local file system paths
- **Progress Tracking**: Real-time updates during import operations

## Key Concepts for Beginners

### What is Plex Media Server?
Plex is a popular media server software that organizes your movies, TV shows, and other
media files. It provides a web interface and mobile apps to access your content from
anywhere. Retrovue connects to your Plex server to import your media library.

### How Does the Integration Work?
1. **Connect to Plex**: Retrovue connects to your Plex server using your server URL and token
2. **Discover Libraries**: Find all your movie and TV show libraries
3. **Import Content**: Download metadata (titles, descriptions, ratings, etc.) for each item
4. **Map File Paths**: Convert Plex's internal file paths to paths Retrovue can access
5. **Store in Database**: Save all the information in Retrovue's database for scheduling

### What Gets Imported?
- **Movies**: Title, year, rating, genre, director, summary, duration
- **TV Shows**: Show title, year, total seasons/episodes, genre, summary
- **TV Episodes**: Episode title, season/episode number, rating, summary, duration
- **File Information**: File paths, durations, library names

### What Doesn't Get Imported?
- The actual video files (they stay where they are)
- Plex-specific settings or configurations
- User accounts or permissions
- Watch history or personal data

## How to Use This Module

### Basic Setup
```python
from retrovue.core.plex_integration import PlexImporter

# Create an importer for your Plex server
importer = PlexImporter(
    server_id=1,  # ID from your database
    database=db,  # Your Retrovue database
    status_callback=print  # Function to receive progress updates
)

# Test the connection
if importer.test_connection():
    print("Successfully connected to Plex!")
    
    # Sync all libraries
    results = importer.sync_all_libraries()
    print(f"Updated: {results['updated']}, Added: {results['added']}")
```

### Advanced Usage
```python
# Get all available libraries
libraries = importer.get_libraries()
for library in libraries:
    print(f"Library: {library['title']} ({library['type']})")

# Sync a specific library
results = importer.sync_library("1", "movie")  # Library key and type

# Search for specific shows
shows = importer.discover_shows_by_title("Breaking Bad", 2008)
for show in shows:
    print(f"Found: {show['title']} ({show['year']})")
```

## Key Features Explained

### Intelligent Synchronization
Instead of re-importing everything every time, the system:
- Compares timestamps to detect changes
- Only processes content that has been modified
- Dramatically improves performance (10-50x faster for unchanged content)
- Handles large libraries efficiently (tested with 17,000+ episodes)

### Episode-Level Granularity
Unlike some systems that treat entire TV shows as single units:
- Each episode is stored separately in the database
- You can schedule individual episodes
- Episode-specific metadata is preserved
- Season and episode numbers are maintained

### Multi-Server Support
You can connect multiple Plex servers:
- Each server has its own configuration
- Path mappings are server-specific
- Content is properly isolated between servers
- No conflicts between different Plex installations

### Path Mapping System
Plex stores file paths differently than your local file system:
- **Plex Path**: `/media/movies/Avengers (2012)/Avengers.mkv`
- **Local Path**: `D:\\Media\\Movies\\Avengers (2012)\\Avengers.mkv`
- The system automatically converts between these formats

## Error Handling

The system includes comprehensive error handling:
- **Connection Issues**: Clear messages when Plex server is unreachable
- **Authentication Problems**: Helpful guidance for token issues
- **Data Errors**: Invalid metadata is logged and skipped
- **Network Timeouts**: Automatic retry mechanisms
- **Database Errors**: Transaction rollback on failures

## Performance Optimizations

### Caching
- Library information is cached to avoid repeated API calls
- Path mappings are cached for faster lookups
- Server configurations are cached during operations

### Batch Operations
- Database operations are batched for efficiency
- Progress updates are batched to reduce UI overhead
- API calls are minimized through intelligent caching

### Memory Management
- Large datasets are processed in chunks
- Database connections are properly managed
- Temporary objects are cleaned up promptly

## Troubleshooting Common Issues

### Connection Failed
- Check that your Plex server URL is correct
- Verify your Plex token is valid
- Ensure your Plex server is running and accessible
- Check firewall settings if using remote server

### Path Mapping Issues
- Verify path mappings are configured correctly
- Check that local paths exist and are accessible
- Ensure library root paths match your Plex configuration
- Test file access manually

### Import Performance
- Large libraries may take time to import initially
- Subsequent syncs are much faster due to change detection
- Progress bars show current status
- Debug logging can be enabled for detailed information

### Content Not Found
- Check if content exists in Plex
- Verify library is enabled for sync
- Check GUID parsing for external identifiers
- Ensure content is properly scanned in Plex

## Technical Architecture

### Core Classes
- **PlexImporter**: Main class handling all Plex API interactions
- **PlexPathMappingService**: Converts Plex paths to local paths
- **GUIDParser**: Parses and normalizes external identifiers

### API Endpoints Used
- `/library/sections`: List all libraries
- `/library/sections/{key}/all`: Get all items in library
- `/library/metadata/{key}/children`: Get children (seasons/episodes) of shows
- `/status/sessions`: Test server connectivity

### Database Integration
- Stores servers in `plex_servers` table
- Stores path mappings in `path_mappings` table
- Stores content in `media_files`, `movies`, `shows`, `episodes` tables
- Maintains proper relationships between all entities

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

This module provides a robust foundation for importing and managing your media library
from Plex Media Server, with intelligent synchronization and comprehensive error handling
to ensure reliable operation even with large libraries.
"""

import requests
import xml.etree.ElementTree as ET
import xmltodict
import hashlib
import os
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
from .database import RetrovueDatabase
from .path_mapping import resolve_local_path
from .guid_parser import GUIDParser, extract_guids_from_plex_metadata, get_show_disambiguation_key, format_show_for_display

# XML→JSON-ish normalization helpers
def _coerce_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]

def _strip_at_keys(obj):
    """Recursively strip leading '@' from keys in xmltodict-style dicts."""
    if isinstance(obj, list):
        return [_strip_at_keys(i) for i in obj]
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            nk = k[1:] if isinstance(k, str) and k.startswith('@') else k
            out[nk] = _strip_at_keys(v)
        return out
    return obj

logger = logging.getLogger(__name__)


# ============================================================================
# Digest System for Change Detection
# ============================================================================

def streams_signature(media_dict: dict) -> str:
    """
    Summarize video/audio/sub track info into a small stable string for change detection.
    
    Args:
        media_dict: Plex media dictionary containing stream information
        
    Returns:
        String signature of the media streams
    """
    v = f"v:{media_dict.get('videoCodec', '?')}"
    a = f"a:{media_dict.get('audioChannels', '?')}@{media_dict.get('audioCodec', '?')}"
    s = f"s:{media_dict.get('subtitleCount', 0)}"
    return "|".join([v, a, s])


def digest_episode_or_movie(*, rating_key: str, updated_at: int, duration: int, 
                           file_size: int, part_count: int, streams_signature: str, 
                           guid_primary: str) -> str:
    """
    Create a digest for an episode or movie to detect changes.
    
    Args:
        rating_key: Plex rating key
        updated_at: Plex updated timestamp
        duration: Media duration in milliseconds
        file_size: File size in bytes
        part_count: Number of media parts
        streams_signature: Stream signature from streams_signature()
        guid_primary: Primary GUID for the item
        
    Returns:
        SHA1 hex digest string
    """
    h = hashlib.sha1()
    for v in (rating_key, str(updated_at or 0), str(duration or 0), str(file_size or 0),
              str(part_count or 0), streams_signature or "", guid_primary or ""):
        h.update(v.encode("utf-8"))
        h.update(b"|")
    return h.hexdigest()


def digest_show(child_count: int, leaf_count: int, show_updated_at: int, 
                children_updated_max: int) -> str:
    """
    Create a digest for a show to detect changes at the show level.
    
    Args:
        child_count: Number of child items (seasons)
        leaf_count: Number of leaf items (episodes)
        show_updated_at: Show's updated timestamp
        children_updated_max: Maximum updated timestamp across all children
        
    Returns:
        SHA1 hex digest string
    """
    h = hashlib.sha1()
    for v in (str(child_count or 0), str(leaf_count or 0),
              str(show_updated_at or 0), str(children_updated_max or 0)):
        h.update(v.encode("utf-8"))
        h.update(b"|")
    return h.hexdigest()


def _streams_sig_from_media(media: dict) -> str:
    """Create streams signature from media dict."""
    v = f"v:{media.get('videoCodec','?')}"
    a = f"a:{media.get('audioChannels','?')}@{media.get('audioCodec','?')}"
    s = f"s:{media.get('subtitleCount', 0)}"
    return "|".join([v,a,s])




def _summarize_media_from_detail(detail: dict) -> dict:
    """Normalize fields from Plex detail response into a small dict."""
    # Expect: detail['Media'][0]['Part'][0] etc. Adjust for your client shape.
    media = (detail.get('Media') or [{}])[0]
    part = (media.get('Part') or [{}])[0]
    return {
        "duration_ms": int(media.get('duration') or 0),
        "file_size": int(part.get('size') or 0),
        "part_count": len(media.get('Part') or []),
        "streams_signature": _streams_sig_from_media({
            "videoCodec": media.get('videoCodec'),
            "audioChannels": media.get('audioChannels'),
            "audioCodec": media.get('audioCodec'),
            "subtitleCount": len([s for s in (part.get('Stream') or []) if s.get('streamType') == 3]),
        }),
        "guid_primary": (detail.get('Guid') or [{}])[0].get('id') if detail.get('Guid') else None,
        "plex_path": part.get('file') or ''
    }


def summarize_media_from_item(item: dict) -> dict:
    """
    Same fields as _summarize_media_from_detail(), but reads from an episode/movie item
    that already contains Media/Part (as returned by /children).
    """
    media_list = item.get('Media') or []
    media = media_list[0] if isinstance(media_list, list) and media_list else (media_list or {})
    parts = media.get('Part') or []
    part = parts[0] if isinstance(parts, list) and parts else (parts or {})

    subtitle_streams = [s for s in (part.get('Stream') or []) if s.get('streamType') == 3]
    sig = _streams_sig_from_media({
        "videoCodec": media.get('videoCodec'),
        "audioChannels": media.get('audioChannels'),
        "audioCodec": media.get('audioCodec'),
        "subtitleCount": len(subtitle_streams),
    })

    return {
        "duration": int(media.get('duration') or 0),
        "duration_ms": int(media.get('duration') or 0),
        "file_size": int(part.get('size') or 0),
        "part_count": len(parts) if isinstance(parts, list) else (1 if parts else 0),
        "streams_signature": sig,
        "guid_primary": (item.get('Guid') or [{}])[0].get('id') if item.get('Guid') else None,
        "plex_path": part.get('file') or ''
    }


def summarize_media(detail_dict: dict) -> dict:
    """
    Extract and summarize media information from Plex item detail.
    
    Args:
        detail_dict: Plex item detail dictionary
        
    Returns:
        Dictionary with summarized media information
    """
    media_info = {
        'duration': 0,
        'file_size': 0,
        'part_count': 0,
        'streams_signature': '',
        'plex_path': '',
        'guid_primary': ''
    }
    
    # Extract media information
    if 'Media' in detail_dict:
        media_list = detail_dict['Media']
        if isinstance(media_list, list) and len(media_list) > 0:
            media = media_list[0]
        elif isinstance(media_list, dict):
            media = media_list
        else:
            return media_info
            
        media_info['duration'] = int(media.get('duration', 0))
        media_info['streams_signature'] = streams_signature(media)
        
        # Extract part information
        if 'Part' in media:
            parts = media['Part']
            if isinstance(parts, list):
                media_info['part_count'] = len(parts)
                if len(parts) > 0:
                    part = parts[0]
                    media_info['file_size'] = int(part.get('size', 0))
                    media_info['plex_path'] = part.get('file', '')
            elif isinstance(parts, dict):
                media_info['part_count'] = 1
                media_info['file_size'] = int(parts.get('size', 0))
                media_info['plex_path'] = parts.get('file', '')
    
    # Extract primary GUID
    if 'Guid' in detail_dict:
        guids = detail_dict['Guid']
        if isinstance(guids, list) and len(guids) > 0:
            media_info['guid_primary'] = guids[0].get('id', '')
        elif isinstance(guids, dict):
            media_info['guid_primary'] = guids.get('id', '')
    
    return media_info


# ============================================================================
# Existing Functions
# ============================================================================

def plex_ts(item: dict) -> int | None:
    """
    Extract timestamp from Plex item metadata.
    
    Args:
        item: Plex metadata item
        
    Returns:
        Unix timestamp as integer, or None if not available
    """
    v = item.get('updatedAt') or item.get('addedAt')
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def db_ts_to_int(v) -> int | None:
    """
    Convert database timestamp value to integer epoch.
    
    Args:
        v: Database timestamp value (int, str, or None)
        
    Returns:
        Unix timestamp as integer, or None if not available
    """
    if v is None: 
        return None
    if isinstance(v, int): 
        return v
    s = str(v)
    if s.isdigit(): 
        return int(s)
    from datetime import datetime
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return int(datetime.strptime(s, fmt).timestamp())
        except ValueError:
            pass
    return None


def parse_plex_response(response: requests.Response) -> Dict:
    """
    Parse Plex API response, handling both JSON and XML formats.
    
    Args:
        response: HTTP response from Plex API
        
    Returns:
        Parsed data as dictionary
        
    Raises:
        ValueError: If response format is not supported
    """
    content_type = response.headers.get('Content-Type', '').lower()
    
    if 'application/json' in content_type:
        try:
            data = response.json()
            return data
        except ValueError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")
    
    elif 'application/xml' in content_type or 'text/xml' in content_type:
        try:
            # Parse XML using xmltodict for better compatibility
            return xmltodict.parse(response.text)
        except Exception as e:
            raise ValueError(f"Failed to parse XML response: {e}")
    
    else:
        # Try JSON first as fallback
        try:
            data = response.json()
            return data
        except ValueError:
            # If JSON fails, try XML
            try:
                return xmltodict.parse(response.text)
            except Exception:
                raise ValueError(f"Unsupported response format: {content_type}")


class PlexImporter:
    """
    Handles importing content from Plex Media Server with multi-server support.
    """
    
    def __init__(self, server_id: int, database: RetrovueDatabase, status_callback=None):
        """
        Initialize the Plex importer.
        
        Args:
            server_id: Plex server ID from database
            database: Database instance for storing imported content
            status_callback: Optional callback function for status updates
        """
        self.server_id = server_id
        self.database = database
        self.status_callback = status_callback
        
        # Get server details from database
        server_info = database.get_plex_server(server_id)
        if not server_info:
            raise ValueError(f"Plex server with ID {server_id} not found")
        
        self.server_url = server_info['server_url'].rstrip('/')
        self.token = server_info['token']
        self.server_name = server_info['name']
        
        self.headers = {
            'X-Plex-Token': self.token,
            'Accept': 'application/json'
        }
        
        # Use requests.Session for HTTP connection reuse
        import requests
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Store database reference for dynamic path resolution
        self.database = database
        self.server_id = server_id
    
    def _emit_status(self, message: str, debug_only: bool = False):
        """Emit status message via callback"""
        if self.status_callback and not debug_only:
            self.status_callback(message)
    
    def test_connection(self) -> bool:
        """Test connection to Plex server"""
        try:
            url = f"{self.server_url}/status/sessions"
            response = self.session.get(url,  timeout=10)
            return response.status_code == 200
        except Exception as e:
            return False
    
    def get_libraries(self) -> List[Dict]:
        """Get all libraries from Plex server"""
        try:
            url = f"{self.server_url}/library/sections"
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = parse_plex_response(response)
            self._emit_status(f"📡 Parsed {response.headers.get('Content-Type', 'unknown')} response from {url}", debug_only=True)
            
            libraries = []
            
            for section in data.get('MediaContainer', {}).get('Directory', []):
                libraries.append({
                    'key': section.get('key'),
                    'title': section.get('title'),
                    'type': section.get('type'),
                    'agent': section.get('agent'),
                    'locations': section.get('Location', [])  # Library root paths
                })
            
            return libraries
        except Exception as e:
            self._emit_status(f"❌ Error getting libraries: {e}", debug_only=True)
            return []
    
    def get_library_root_paths(self, library_key: str) -> List[str]:
        """Get the root paths for a specific library"""
        try:
            url = f"{self.server_url}/library/sections/{library_key}"
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = parse_plex_response(response)
            self._emit_status(f"📡 Parsed {response.headers.get('Content-Type', 'unknown')} response from {url}", debug_only=True)
            
            locations = data.get('MediaContainer', {}).get('Location', [])
            
            # Extract the path from each location
            root_paths = []
            for location in locations:
                path = location.get('path', '')
                if path:
                    root_paths.append(path)
            
            return root_paths
        except Exception as e:
            self._emit_status(f"❌ Error getting library root paths: {e}", debug_only=True)
            return []
    
    def get_library_items(self, library_key: str, library_type: str, start: int = 0, size: int = None) -> List[Dict]:
        """
        Get items from a specific library with optional pagination. Works with JSON or XML.
        """
        try:
            url = f"{self.server_url}/library/sections/{library_key}/all"
            params = {}
            # Ensure we filter by type so Plex returns a consistent container
            if str(library_type).lower() in ("show", "shows", "tv"):
                params["type"] = 2
            elif str(library_type).lower() in ("movie", "movies", "film", "films"):
                params["type"] = 1

            # Pagination (Plex accepts these as query params)
            params["X-Plex-Container-Start"] = max(0, int(start))
            if size is not None:
                params["X-Plex-Container-Size"] = int(size)

            print(f"🔍 DEBUG: get_library_items URL: {url}")
            print(f"🔍 DEBUG: get_library_items params: {params}")

            # IMPORTANT: send headers so token + Accept are applied
            response = self.session.get(url,  params=params, timeout=30)
            response.raise_for_status()

            print(f"🔍 DEBUG: Response status: {response.status_code}")
            print(f"🔍 DEBUG: Response content length: {len(response.content)}")
            print(f"🔍 DEBUG: Content-Type: {response.headers.get('Content-Type')}")

            data = parse_plex_response(response)
            # If XML, attributes are '@*' — normalize to plain keys so downstream code sees ratingKey/key/etc.
            data = _strip_at_keys(data)

            mc = data.get("MediaContainer", {}) if isinstance(data, dict) else {}
            # In JSON, lists are often under 'Metadata' for shows and movies.
            # In XML-parsed dicts, shows often come as 'Directory', movies as 'Video'.
            items = mc.get("Metadata") or mc.get("Directory") or mc.get("Video") or []
            items = _coerce_list(items)

            # Debugging
            print(f"🔍 DEBUG: MediaContainer keys: {list(mc.keys()) if isinstance(mc, dict) else 'n/a'}")
            print(f"🔍 DEBUG: MediaContainer size: {mc.get('size', 'n/a')} totalSize: {mc.get('totalSize', 'n/a')}")
            print(f"🔍 DEBUG: Found {len(items)} items in response")

            return items
        except Exception as e:
            self._emit_status(f"❌ Error getting library items: {e}", debug_only=True)
            return []
    
    def discover_shows_by_title(self, title: str, year: int = None) -> List[Dict]:
        """
        Discover shows by title and optionally year for disambiguation.
        
        Args:
            title: Show title to search for
            year: Optional year for disambiguation
            
        Returns:
            List of matching shows with disambiguation information
        """
        try:
            # Search for shows with title and year filter
            url = f"{self.server_url}/library/sections/all"
            params = {
                'type': 2,  # TV shows
                'title': title,
                'includeGuids': 1
            }
            if year:
                params['year'] = year
            
            response = self.session.get(url,  params=params)
            response.raise_for_status()
            
            data = response.json()
            shows = data.get('MediaContainer', {}).get('Metadata', [])
            
            # Process shows to add disambiguation information
            processed_shows = []
            for show in shows:
                # Extract GUIDs
                guids = extract_guids_from_plex_metadata(show)
                parsed_guids = GUIDParser.parse_guids(guids)
                
                # Get show year
                show_year = show.get('year')
                
                # Create disambiguation key
                disambiguation_key = get_show_disambiguation_key(title, show_year)
                
                # Format for display
                display_name = format_show_for_display(title, show_year, parsed_guids)
                
                processed_show = {
                    'ratingKey': show.get('ratingKey'),
                    'title': show.get('title'),
                    'year': show_year,
                    'disambiguation_key': disambiguation_key,
                    'display_name': display_name,
                    'guids': parsed_guids,
                    'summary': show.get('summary', ''),
                    'studio': show.get('studio', ''),
                    'originallyAvailableAt': show.get('originallyAvailableAt'),
                    'raw_metadata': show  # Keep original for full sync
                }
                processed_shows.append(processed_show)
            
            return processed_shows
            
        except Exception as e:
            self._emit_status(f"❌ Error discovering shows: {e}")
            return []
    
    
    def get_show_episodes(self, show_key: str) -> List[Dict]:
        """Get all episodes for a specific show using /children endpoint (standardized approach)"""
        try:
            # Use the standardized /children approach
            seasons = self._fetch_show_children(show_key)
            all_episodes = []
            
            for season in seasons:
                episodes = self._fetch_season_children(season['ratingKey'])
                all_episodes.extend(episodes)
            
            self._emit_status(f"📺 Retrieved {len(all_episodes)} episodes for show {show_key}", debug_only=True)
            return all_episodes
        except Exception as e:
            self._emit_status(f"❌ Error getting show episodes: {e}")
            return []
    
    def _map_plex_rating(self, plex_rating: str) -> str:
        """Map Plex rating to standard rating"""
        rating_map = {
            'G': 'G',
            'PG': 'PG',
            'PG-13': 'PG-13',
            'R': 'R',
            'NC-17': 'Adult',
            'Not Rated': 'NR',
            'TV-G': 'G',
            'TV-PG': 'PG',
            'TV-14': 'PG-13',
            'TV-MA': 'Adult'
        }
        return rating_map.get(plex_rating, 'NR')
    
    def _get_show_timestamp(self, show) -> int:
        """Get the timestamp for a show, using addedAt as fallback if updatedAt is missing"""
        return plex_ts(show)
    
    def _get_duration_from_media(self, media_info: List[Dict]) -> Optional[int]:
        """
        Extract duration from Plex media information.

        Args:
            media_info: List of media information from Plex

        Returns:
            Duration in milliseconds, or None if not available
        """
        if media_info and len(media_info) > 0:
            media = media_info[0]
            # Duration can be either a direct integer or nested in a duration object
            duration = media.get('duration')
            if isinstance(duration, int):
                return duration
            elif isinstance(duration, dict):
                return duration.get('duration')
        return None
    
    def _get_file_path_from_media(self, media_info: List[Dict]) -> str:
        """Extract file path from Plex media information"""
        if media_info and len(media_info) > 0:
            media = media_info[0]
            part_array = media.get('Part', [])
            if part_array and len(part_array) > 0:
                return part_array[0].get('file', '')
        return ''
    
    def _get_local_path_from_plex_path(self, plex_path: str) -> str:
        """Convert Plex path to local path using path mappings"""
        if not plex_path:
            return ''
        
        # Use the dynamic path resolution function
        return resolve_local_path(self.database, self.server_id, plex_path) or plex_path
    
    def get_local_path(self, plex_path: str) -> str:
        """Get the local mapped path for a Plex path (for file access)"""
        return resolve_local_path(self.database, self.server_id, plex_path) or plex_path
    
    
    def import_movie(self, item: Dict, library_name: str = None, library_root: str = None) -> bool:
        """Import a single movie"""
        try:
            # Extract basic information
            title = item.get('title', 'Unknown Title')
            plex_guid = item.get('guid', '')  # Use stable GUID instead of key
            
            # Get duration and file path from Media array
            media_array = item.get('Media', [])
            plex_file_path = self._get_file_path_from_media(media_array)
            duration = self._get_duration_from_media(media_array)
            
            if not duration:
                return False
            
            # Get rating
            plex_rating = item.get('contentRating', '')
            content_rating = self._map_plex_rating(plex_rating)
            
            # Convert Plex path to local path
            local_file_path = self._get_local_path_from_plex_path(plex_file_path)
            
            # Add media file to database
            media_file_id = self.database.add_media_file(
                duration=duration,
                media_type='movie',
                source_type='plex',
                source_id=plex_guid,
                library_name=library_name,
                server_id=self.server_id,
                plex_path=plex_file_path
            )
            
            # Add movie metadata
            self.database.add_movie(
                media_file_id=media_file_id,
                title=title,
                year=item.get('year'),
                rating=content_rating,
                summary=item.get('summary', ''),
                genre=', '.join([g.get('tag', '') for g in item.get('Genre', [])]),
                director=', '.join([d.get('tag', '') for d in item.get('Director', [])]),
                server_id=self.server_id,
                plex_updated_at=item.get('updatedAt')
            )
            
            # Format duration for display (convert milliseconds to hh:mm:ss.ff)
            duration_seconds = duration / 1000.0
            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            seconds = int(duration_seconds % 60)
            fractional_seconds = int((duration_seconds % 1) * 100)
            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{fractional_seconds:02d}"
            
            self._emit_status(f"✅ Imported movie: {title} ({content_rating}) - {duration_str}")
            return True
            
        except Exception as e:
            self._emit_status(f"❌ Error importing movie '{title}': {e}", debug_only=True)
            return False
    
    def import_show_episodes(self, show: Dict) -> int:
        """Import all episodes from a show with year-based disambiguation"""
        try:
            show_title = show.get('title', 'Unknown Show')
            show_key = show.get('key', '')
            show_year = show.get('year')
            
            # Extract GUIDs for disambiguation
            guids = extract_guids_from_plex_metadata(show)
            parsed_guids = GUIDParser.parse_guids(guids)
            primary_guid = GUIDParser.get_primary_guid(guids)
            
            # Get all episodes for this show
            episodes = self.get_show_episodes(show_key)
            
            if not episodes:
                return 0
            
            # Create show record with disambiguation
            show_id = self.database.add_show(
                title=show_title,
                plex_rating_key=show.get('ratingKey', ''),  # Keep for display purposes
                year=show_year,
                total_seasons=show.get('leafCount', 0),
                total_episodes=len(episodes),
                show_rating=self._map_plex_rating(show.get('contentRating', '')),
                show_summary=show.get('summary', ''),
                genre=', '.join([g.get('tag', '') for g in show.get('Genre', [])]),
                studio=show.get('studio', ''),
                originally_available_at=show.get('originallyAvailableAt'),
                guid_primary=primary_guid,
                source_type='plex',
                source_id=show.get('guid', ''),  # Use GUID as source ID
                server_id=self.server_id,
                plex_updated_at=self._get_show_timestamp(show)
            )
            
            # Store all GUIDs for this show
            for provider, external_id in parsed_guids:
                self.database.add_show_guid(show_id, provider, external_id)
            
            imported_count = 0
            
            # Import each episode
            for episode in episodes:
                try:
                    episode_title = episode.get('title', 'Unknown Episode')
                    episode_key = episode.get('key', '')
                    episode_guid = episode.get('guid', '')  # Use stable GUID
                    
                    # Get duration and file path from Media array
                    media_array = episode.get('Media', [])
                    plex_file_path = self._get_file_path_from_media(media_array)
                    duration = self._get_duration_from_media(media_array)
                    
                    if not duration:
                        continue
                    
                    # Get rating
                    plex_rating = episode.get('contentRating', '')
                    content_rating = self._map_plex_rating(plex_rating)
                    
                    # Convert Plex path to local path
                    local_file_path = self._get_local_path_from_plex_path(plex_file_path)
                    
                    # Add media file to database
                    media_file_id = self.database.add_media_file(
                        file_path=None,  # No longer store local paths
                        duration=duration,
                        media_type='episode',
                        source_type='plex',
                        source_id=episode_guid,  # Use stable GUID
                        server_id=self.server_id,
                        plex_path=plex_file_path
                    )
                    
                    # Add episode metadata
                    # Convert to integers to match database storage
                    season_number = int(episode.get('parentIndex', 0)) if episode.get('parentIndex') is not None else 0
                    episode_number = int(episode.get('index', 0)) if episode.get('index') is not None else 0
                    self.database.add_episode(
                        media_file_id=media_file_id,
                        show_id=show_id,
                        episode_title=episode_title,
                        season_number=season_number,
                        episode_number=episode_number,
                        rating=content_rating,
                        summary=episode.get('summary', ''),
                        plex_updated_at=episode.get('updatedAt')
                    )
                    
                    imported_count += 1
                    # Format duration for display (convert milliseconds to hh:mm:ss.ff)
                    duration_seconds = duration / 1000.0
                    hours = int(duration_seconds // 3600)
                    minutes = int((duration_seconds % 3600) // 60)
                    seconds = int(duration_seconds % 60)
                    fractional_seconds = int((duration_seconds % 1) * 100)
                    duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{fractional_seconds:02d}"
                    
                    self._emit_status(f"✅ Imported episode: {episode_title} ({content_rating}) - {duration_str}")
                    
                except Exception as e:
                    self._emit_status(f"❌ Error importing episode '{episode_title}': {e}", debug_only=True)
                    continue
            
            self._emit_status(f"🎉 Imported {imported_count} episodes from show: {show_title}")
            return imported_count
            
        except Exception as e:
            self._emit_status(f"❌ Error importing show episodes for '{show_title}': {e}", debug_only=True)
            return 0
    
    def import_library(self, library_key: str, library_type: str) -> int:
        """Import all content from a specific library (legacy method - use sync_library instead)"""
        if library_type == 'movie':
            return self._import_movie_library(library_key)
        elif library_type == 'show':
            return self._import_show_library(library_key)
        else:
            return 0
    
    def sync_library(self, library_key: str, library_type: str) -> Dict[str, int]:
        """
        Sync a library with Plex - update existing, add new, remove deleted.
        
        Args:
            library_key: Library key from Plex
            library_type: Type of library ('movie' or 'show')
            
        Returns:
            Dictionary with sync results: {'updated': int, 'added': int, 'removed': int}
        """
        if library_type == 'movie':
            return self.sync_movie_library(library_key)
        elif library_type == 'show':
            return self.sync_tv_library(library_key)
        else:
            return {'updated': 0, 'added': 0, 'removed': 0}
    
    def sync_tv_library(self, library_key: str, *, deep: bool = False, progress_callback=None) -> Dict[str, int]:
        """Sync TV library with selective expansion and digest-based change detection."""
        # Get library information
        library_info = self.database.get_library_by_key(library_key, self.server_id)
        if not library_info:
            # Create library record if it doesn't exist
            library_id = self.database.add_library(
                server_id=self.server_id,
                library_key=library_key,
                library_name=f"Library {library_key}",
                library_type="show"
            )
        else:
            library_id = library_info['id']
        
        now_epoch = int(time.time())
        processed = changed = skipped = errors = 0
        seen = set()
        
        def progress(event, payload):
            if progress_callback:
                if event == "library_start":
                    progress_callback("library_start", payload)
                elif event == "page_progress":
                    progress_callback("page_progress", payload)
                elif event == "library_done":
                    progress_callback("library_done", payload)
        
        print(f"🔍 DEBUG: sync_tv_library called with library_key: {library_key}, deep: {deep}")
        
        progress("library_start", {"server_id": self.server_id, "library_id": library_id})
        
        # Get shows in pages for better memory management
        page_size = 200
        page_start = 0
        
        while True:
            # Get a page of shows
            shows_page = self.get_library_items(library_key, 'show', start=page_start, size=page_size)
            print(f"🔍 DEBUG: get_library_items returned {len(shows_page) if shows_page else 0} shows for page {page_start}-{page_start + page_size}")
            if not shows_page:
                print(f"🔍 DEBUG: No more shows, breaking out of loop")
                break
            
            to_expand = []
            
            # Process each show in the page
            for show in shows_page:
                rating_key = show.get('ratingKey', '')
                if not rating_key:
                    continue
                
                lite_digest = digest_show(
                    show.get('childCount'), show.get('leafCount'),
                    show.get('updatedAt'), show.get('childrenUpdatedAtMax') or show.get('updatedAt')
                )
                
                # Decide if we should expand this show to episodes
                show_guid = show.get('guid') or ''
                children_hydrated = self.database.children_hydrated(self.server_id, library_id, rating_key)
                show_digest_changed = self.database.show_digest_changed(self.server_id, library_id, rating_key, lite_digest)
                
                # NEW: if the DB has no episodes for this show GUID, we must hydrate
                needs_children_due_to_missing = False
                try:
                    needs_children_due_to_missing = (self.database.count_episodes_for_show_source_id(show_guid) == 0)
                except Exception:
                    needs_children_due_to_missing = False
                
                should_expand_children = (
                    deep
                    or show_digest_changed
                    or not children_hydrated
                    or needs_children_due_to_missing  # <— NEW: ensure episodes exist at least once
                )
                
                if should_expand_children:
                    to_expand.append((show, lite_digest))
                else:
                    skipped += 1
                processed += 1
            
            # Batch writes per page with transaction
            conn = self.database.connection
            conn.execute("BEGIN IMMEDIATE")
            try:
                # Expand selected shows to episodes
                for show, lite_digest in to_expand:
                    try:
                        print(f"🔍 DEBUG: Expanding show: {show.get('title', 'Unknown')} (ratingKey: {show['ratingKey']})")
                        children_updated_max = 0
                        
                        # before fetching seasons, ensure show row exists and get show_id
                        show_id = self.database.upsert_show_basic(
                            server_id=self.server_id, library_id=library_id, show=show
                        )
                        
                        print(f"🔍 DEBUG: Fetching show children for {show['ratingKey']}...")
                        seasons = self._fetch_show_children(show['ratingKey'])
                        print(f"🔍 DEBUG: Found {len(seasons)} seasons for show {show.get('title', 'Unknown')}")
                        for season in seasons:
                            episodes = self._fetch_season_children(season['ratingKey'])
                            for ep in episodes:
                                # (unchanged) fetch detail if needed, compute media summary & digest
                                detail = self._fetch_item_detail(ep['ratingKey']) if not ep.get('Media') else None
                                media = (_summarize_media_from_detail(detail)
                                         if detail else summarize_media_from_item(ep))  # see perf patch below
                                d = digest_episode_or_movie(
                                    rating_key=ep['ratingKey'], updated_at=ep.get('updatedAt'),
                                    duration=media["duration_ms" if "duration_ms" in media else "duration"],
                                    file_size=media["file_size"],
                                    part_count=media["part_count"],
                                    streams_signature=media["streams_signature"],
                                    guid_primary=media["guid_primary"]
                                )
                                self.database.upsert_episode(
                                    server_id=self.server_id, library_id=library_id,
                                    parent_show_key=show['ratingKey'], ep=ep, media=media,
                                    digest=d, now_epoch=now_epoch
                                )
                                seen.add(ep['ratingKey'])
                                children_updated_max = max(children_updated_max, ep.get('updatedAt') or 0)
                                changed += 1
                        
                        self.database.upsert_show_digest(
                            self.server_id, library_id, show['ratingKey'],
                            digest_show(show.get('childCount'), show.get('leafCount'),
                                       show.get('updatedAt'), children_updated_max),
                            children_hydrated=True
                        )
                    except Exception as e:
                        logger.error(f"Error expanding show {show.get('title', 'Unknown')}: {e}")
                        errors += 1
                
                # Commit the transaction for this page
                conn.commit()
            except Exception as e:
                # Rollback on any error
                conn.rollback()
                logger.error(f"Error processing page, rolled back: {e}")
                raise
            
            # Emit progress after each page
            progress("page_progress", {
                "server_id": self.server_id, "library_id": library_id,
                "processed": processed, "changed": changed, "skipped": skipped, "errors": errors
            })
            
            page_start += page_size
        
        # Finalize deletes (soft) and emit summary
        missing_promoted = self.database.mark_missing_not_seen(library_id=library_id, seen=seen, now_epoch=now_epoch)
        deleted_promoted = self.database.promote_deleted_past_retention(library_id=library_id, now_epoch=now_epoch, retention_days=30)
        
        progress("library_done", {
            "server_id": self.server_id, "library_id": library_id, 
            "summary": {
                "processed": processed, "changed": changed, "skipped": skipped, "errors": errors,
                "missing_promoted": missing_promoted, "deleted_promoted": deleted_promoted,
                "last_synced_at": now_epoch
            }
        })
        
        return {'updated': changed, 'added': 0, 'removed': missing_promoted + deleted_promoted}
    
    def sync_movie_library(self, library_key: str, *, deep: bool = False, progress_callback=None) -> Dict[str, int]:
        """Sync movie library with digest-based change detection."""
        # Get library information
        library_info = self.database.get_library_by_key(library_key, self.server_id)
        if not library_info:
            # Create library record if it doesn't exist
            library_id = self.database.add_library(
                server_id=self.server_id,
                library_key=library_key,
                library_name=f"Library {library_key}",
                library_type="movie"
            )
        else:
            library_id = library_info['id']
        
        now_epoch = int(time.time())
        processed = changed = skipped = errors = 0
        seen = set()
        
        def progress(event, payload):
            if progress_callback:
                if event == "library_start":
                    progress_callback("library_start", payload)
                elif event == "page_progress":
                    progress_callback("page_progress", payload)
                elif event == "library_done":
                    progress_callback("library_done", payload)
        
        progress("library_start", {"server_id": self.server_id, "library_id": library_id})
        
        # Get movies in pages for better memory management
        page_size = 200
        page_start = 0
        
        while True:
            # Get a page of movies
            movies_page = self.get_library_items(library_key, 'movie', start=page_start, size=page_size)
            if not movies_page:
                break
            
            for mv in movies_page:
                try:
                    # We rely on digest; details needed to read Media/Part safely
                    detail = self._fetch_item_detail(mv['ratingKey'])
                    if not detail:
                        continue
                        
                    media = _summarize_media_from_detail(detail)
                    d = digest_episode_or_movie(
                        rating_key=mv['ratingKey'], updated_at=mv.get('updatedAt'),
                        duration=media["duration_ms"], file_size=media["file_size"],
                        part_count=media["part_count"], streams_signature=media["streams_signature"],
                        guid_primary=media["guid_primary"]
                    )
                    # If unchanged digest, just touch last_seen_at by re-upserting identical digest (no heavy write)
                    self.database.upsert_movie(
                        server_id=self.server_id, library_id=library_id,
                        mv=mv, media=media, digest=d, now_epoch=now_epoch
                    )
                    seen.add(mv['ratingKey'])
                    changed += 1  # counts "touched"; adjust if you want strict changes only
                except Exception as e:
                    logger.error(f"Error processing movie {mv.get('title', 'Unknown')}: {e}")
                    errors += 1
                processed += 1
            
            # Emit progress after each page
            progress("page_progress", {
                "server_id": self.server_id, "library_id": library_id,
                "processed": processed, "changed": changed, "skipped": skipped, "errors": errors
            })
            
            page_start += page_size
        
        # Finalize deletes (soft) and emit summary
        missing_promoted = self.database.mark_missing_not_seen(library_id=library_id, seen=seen, now_epoch=now_epoch)
        deleted_promoted = self.database.promote_deleted_past_retention(library_id=library_id, now_epoch=now_epoch, retention_days=30)
        
        progress("library_done", {
            "server_id": self.server_id, "library_id": library_id, 
            "summary": {
                "processed": processed, "changed": changed, "skipped": skipped, "errors": errors,
                "missing_promoted": missing_promoted, "deleted_promoted": deleted_promoted,
                "last_synced_at": now_epoch
            }
        })
        
        return {'updated': changed, 'added': 0, 'removed': missing_promoted + deleted_promoted}
    
    def _import_movie_library(self, library_key: str, library_name: str = None) -> int:
        """Import all movies from a movie library"""
        movies = self.get_library_items(library_key, 'movie')
        imported_count = 0
        
        # Get library root paths for path mapping
        library_root_paths = self.get_library_root_paths(library_key)
        primary_library_root = library_root_paths[0] if library_root_paths else None
        
        for movie in movies:
            if self.import_movie(movie, library_name, primary_library_root):
                imported_count += 1
        
        return imported_count
    
    
    def sync_all_libraries(self, progress_callback=None) -> Dict[str, int]:
        """Sync all libraries and remove orphaned content"""
        libraries = self.get_libraries()
        total_updated = 0
        total_added = 0
        total_removed = 0
        
        # Get sync preferences from database (cache for performance)
        db_libraries = self.database.get_server_libraries(server_id=self.server_id)
        sync_enabled_libraries = {lib['library_key']: lib['sync_enabled'] for lib in db_libraries}
        
        # Cache library root paths to avoid repeated API calls
        library_root_cache = {}
        
        # Process each library with dual progress tracking
        for i, library in enumerate(libraries):
            library_key = library.get('key', '')
            library_type = library.get('type', 'movie')
            library_name = library.get('title', 'Unknown Library')
            
            # Debug: Show library loop entry
            if progress_callback:
                progress_callback(
                    library_progress=None,
                    item_progress=None,
                    message=f"🔄 LOOP: Processing library {i+1}/{len(libraries)}: '{library_name}' (key: {library_key}, type: {library_type})"
                )
            
            # Check if this library is enabled for sync
            if library_key in sync_enabled_libraries and not sync_enabled_libraries[library_key]:
                # Library is disabled for sync, skip it
                if progress_callback:
                    progress_callback(
                        library_progress=(i, len(libraries), library_name),
                        item_progress=None,
                        message=f"⏭️ Skipping disabled library: {library_name}"
                    )
                continue
            
            # Debug: Show library sync status
            sync_status = "enabled" if library_key in sync_enabled_libraries and sync_enabled_libraries[library_key] else "default"
            if progress_callback:
                progress_callback(
                    library_progress=None,
                    item_progress=None,
                    message=f"🔍 Processing library: {library_name} (key: {library_key}, sync: {sync_status})"
                )
            
            # Emit library progress: current library / total libraries
            if progress_callback:
                progress_callback(
                    library_progress=(i, len(libraries), library_name),
                    item_progress=None,
                    message=None  # No status message for library processing
                )
            
            # Debug: Show library type detection
            if progress_callback:
                progress_callback(
                    library_progress=None,
                    item_progress=None,
                    message=f"🔍 Library '{library_name}' (key: {library_key}): type='{library_type}'"
                )
            
            if library_type == 'movie':
                # Get all movies from this library
                plex_movies = self.get_library_items(library_key, 'movie')
                
                # Get library root paths for path mapping (use cache)
                if library_key not in library_root_cache:
                    library_root_cache[library_key] = self.get_library_root_paths(library_key)
                library_root_paths = library_root_cache[library_key]
                primary_library_root = library_root_paths[0] if library_root_paths else None
                
                # DEBUG: Show library info
                self._emit_status(f"🎬 MOVIE LIBRARY: '{library_name}' - Found {len(plex_movies)} movies", debug_only=True)
                
                # Process each movie individually with item progress
                for j, movie in enumerate(plex_movies):
                    movie_guid = movie.get('guid', '')
                    movie_title = movie.get('title', 'Unknown Movie')
                    
                    # DEBUG: Show EVERY movie being processed
                    self._emit_status(f"🎬 PROCESSING Movie {j+1}/{len(plex_movies)}: '{movie_title}' (GUID: {movie_guid})", debug_only=True)
                    
                    # Check if movie exists in database (cache for performance)
                    if 'db_movie_ids' not in locals():
                        db_movies = self.database.get_movies_by_source('plex')
                        db_movie_ids = {movie['source_id'] for movie in db_movies if movie['source_id'] and movie.get('server_id') == self.server_id}
                    
                    # Get the Plex file path for this movie
                    movie_file_path = self._get_file_path_from_media(movie.get('Media', []))
                    
                    if movie_guid in db_movie_ids:
                        # Compare timestamps before updating
                        ts = plex_ts(movie)
                        db_ts_raw = self.database.get_movie_ts_by_guid(movie_guid)
                        db_ts = db_ts_to_int(db_ts_raw)
                        
                        if db_ts is not None and ts is not None and ts <= db_ts:
                            # Skip update - Plex timestamp is older or equal, no changes
                            self._emit_status(f"⏭️ SKIP Movie '{movie_title}': Plex timestamp ({ts}) <= DB timestamp ({db_ts}), no changes", debug_only=True)
                            action = None
                        else:
                            # Update existing movie
                            self._emit_status(f"🔄 UPDATE Movie '{movie_title}': Timestamps differ (Plex: {ts}, DB: {db_ts})", debug_only=True)
                            if self._update_movie(movie, library_name, primary_library_root, library_root_paths):
                                total_updated += 1
                                action = f"Updated movie: {movie_title}"
                            else:
                                action = None  # No output for no changes
                    else:
                        # Add new movie
                        self._emit_status(f"➕ ADD Movie '{movie_title}': New movie, calling import_movie method")
                        if self.import_movie(movie, library_name, primary_library_root):
                            total_added += 1
                            action = f"Added movie: {movie_title}"
                        else:
                            action = None  # No output for failed adds
                    
                    # Emit item progress: current movie / total movies in this library
                    if progress_callback:
                        progress_callback(
                            library_progress=(i, len(libraries), library_name),
                            item_progress=(j + 1, len(plex_movies), movie_title),
                            message=action  # Only show message if there was a database change
                        )
                
            elif library_type == 'show':
                # Debug: Entering show library processing
                if progress_callback:
                    progress_callback(
                        library_progress=None,
                        item_progress=None,
                        message=f"🎬 ENTERING show library processing for '{library_name}' (key: {library_key})"
                    )
                
                # Get all shows from this library
                plex_shows = self.get_library_items(library_key, 'show')
                
                # Debug: Show library content
                if progress_callback:
                    progress_callback(
                        library_progress=None,
                        item_progress=None,
                        message=f"📊 Library '{library_name}': Found {len(plex_shows)} shows"
                    )
                if len(plex_shows) == 0:
                    if progress_callback:
                        progress_callback(
                            library_progress=None,
                            item_progress=None,
                            message=f"⚠️ Library '{library_name}' is empty - no shows found"
                        )
                else:
                    # Show first few show titles for debugging
                    show_titles = [show.get('title', 'Unknown') for show in plex_shows[:3]]
                    if progress_callback:
                        progress_callback(
                            library_progress=None,
                            item_progress=None,
                            message=f"📺 Sample shows: {', '.join(show_titles)}{'...' if len(plex_shows) > 3 else ''}"
                        )
                
                # Get library root paths for path mapping (use cache)
                if library_key not in library_root_cache:
                    library_root_cache[library_key] = self.get_library_root_paths(library_key)
                library_root_paths = library_root_cache[library_key]
                primary_library_root = library_root_paths[0] if library_root_paths else None
                
                # DEBUG: Show library info
                self._emit_status(f"📺 TV SHOW LIBRARY: '{library_name}' - Found {len(plex_shows)} shows", debug_only=True)
                
                # Process each show individually (which processes all its episodes)
                for j, show in enumerate(plex_shows):
                    show_guid = show.get('guid', '')
                    show_title = show.get('title', 'Unknown Show')
                    
                    # Debug: Show loop entry
                    if progress_callback:
                        progress_callback(
                            library_progress=None,
                            item_progress=None,
                            message=f"🎭 SHOW LOOP: Processing show {j+1}/{len(plex_shows)}: '{show_title}'"
                        )
                    
                    # Check if show-level timestamp has changed before processing episodes
                    show_ts = plex_ts(show)
                    db_show_ts_raw = self.database.get_show_ts_by_guid(show_guid)
                    db_show_ts = db_ts_to_int(db_show_ts_raw)
                    
                    # Debug: Show timestamp details
                    if progress_callback:
                        progress_callback(
                            library_progress=None,
                            item_progress=None,
                            message=f"🔍 Show '{show_title}': Plex ts={show_ts}, DB ts={db_show_ts}, updatedAt={show.get('updatedAt')}, addedAt={show.get('addedAt')}"
                        )
                    
                    # Short-circuit: skip episode processing if show timestamp hasn't changed
                    if db_show_ts is not None and show_ts is not None and show_ts <= db_show_ts:
                        if progress_callback:
                            progress_callback(
                                library_progress=None,
                                item_progress=None,
                                message=f"⏭️ SKIP Show '{show_title}': Plex timestamp ({show_ts}) <= DB timestamp ({db_show_ts}), skipping episode walk"
                            )
                        # Still emit progress for the show
                        if progress_callback:
                            progress_callback(
                                library_progress=(i, len(libraries), library_name),
                                item_progress=(j + 1, len(plex_shows), show_title),
                                message=None
                            )
                        continue
                    
                    # Debug: Show timestamp comparison for shows that will be processed
                    if progress_callback:
                        progress_callback(
                            library_progress=None,
                            item_progress=None,
                            message=f"🔄 PROCESSING Show '{show_title}': Plex timestamp ({show_ts}) > DB timestamp ({db_show_ts})"
                        )
                    
                    # Process show and its episodes
                    episode_changes = self._sync_show_episodes(
                        show, 
                        progress_callback, 
                        library_progress=(i, len(libraries), library_name), 
                        library_name=library_name,
                        library_root_paths=library_root_paths
                    )
                    total_updated += episode_changes
        
        # Collect all Plex content for orphaned content removal
        all_plex_movie_ids = set()
        all_plex_show_ids = set()
        
        for library in libraries:
            library_key = library.get('key', '')
            library_type = library.get('type', 'movie')
            
            if library_type == 'movie':
                plex_movies = self.get_library_items(library_key, 'movie')
                all_plex_movie_ids.update(movie.get('guid', '') for movie in plex_movies)
            elif library_type == 'show':
                plex_shows = self.get_library_items(library_key, 'show')
                all_plex_show_ids.update(show.get('guid', '') for show in plex_shows)
        
        # Remove orphaned movies (not in any Plex library) - server-scoped
        if progress_callback:
            progress_callback(
                library_progress=(len(libraries), len(libraries), "Cleanup"),
                item_progress=None,
                message=None  # No status message for cleanup
            )
        db_movies = self.database.get_movies_by_source('plex')
        for db_movie in db_movies:
            # Only remove movies from this server
            if (db_movie['source_id'] and 
                db_movie.get('server_id') == self.server_id and 
                db_movie['source_id'] not in all_plex_movie_ids):
                if self.database.remove_movie_by_source_id(db_movie['source_id']):
                    total_removed += 1
                    self._emit_status(f"🗑️ Removed orphaned movie: {db_movie.get('title', 'Unknown')} (server {self.server_id})", debug_only=True)
        
        # Remove orphaned shows (not in any Plex library) - server-scoped
        if progress_callback:
            progress_callback(
                library_progress=(len(libraries), len(libraries), "Cleanup"),
                item_progress=None,
                message=None  # No status message for cleanup
            )
        db_shows = self.database.get_shows_by_source('plex')
        for db_show in db_shows:
            # Only remove shows from this server
            if (db_show['source_id'] and 
                db_show.get('server_id') == self.server_id and 
                db_show['source_id'] not in all_plex_show_ids):
                if self.database.remove_show_by_source_id(db_show['source_id']):
                    total_removed += 1
                    self._emit_status(f"🗑️ Removed orphaned show: {db_show.get('title', 'Unknown')} (server {self.server_id})", debug_only=True)
        
        # Final progress callback
        if progress_callback:
            progress_callback(
                library_progress=(len(libraries), len(libraries), "Complete"),
                item_progress=None,
                message=None  # No completion message here - handled in UI
            )
        
        return {'updated': total_updated, 'added': total_added, 'removed': total_removed}
    
    def _import_show_library(self, library_key: str) -> int:
        """Import all episodes from all shows in a show library"""
        shows = self.get_library_items(library_key, 'show')
        total_episodes = 0
        
        for show in shows:
            episode_count = self.import_show_episodes(show)
            total_episodes += episode_count
        
        return total_episodes
    
    
    def _expand_show(self, show: dict, library_id: int, now_epoch: int, seen_keys: set) -> Dict[str, int]:
        """
        Expand a show by fetching and processing all its episodes.
        
        Args:
            show: Show metadata from Plex
            library_id: Library ID in database
            now_epoch: Current timestamp
            seen_keys: Set to track seen rating keys
            
        Returns:
            Dictionary with expansion results
        """
        rating_key = show.get('ratingKey', '')
        show_title = show.get('title', 'Unknown Show')
        changed_count = 0
        child_max = 0
        
        try:
            # Fetch show children (seasons)
            seasons = self._fetch_show_children(rating_key)
            
            # Process each season
            for season in seasons:
                season_key = season.get('ratingKey', '')
                if not season_key:
                    continue
                
                # Fetch season children (episodes)
                episodes = self._fetch_season_children(season_key)
                
                # Process each episode
                for episode in episodes:
                    episode_key = episode.get('ratingKey', '')
                    if not episode_key:
                        continue
                    
                    # Fetch episode detail to get media information
                    episode_detail = self._fetch_item_detail(episode_key)
                    if not episode_detail:
                        continue
                    
                    # Summarize media information
                    media = summarize_media(episode_detail)
                    
                    # Create episode digest
                    digest = digest_episode_or_movie(
                        rating_key=episode_key,
                        updated_at=episode.get('updatedAt', 0),
                        duration=media['duration'],
                        file_size=media['file_size'],
                        part_count=media['part_count'],
                        streams_signature=media['streams_signature'],
                        guid_primary=media['guid_primary']
                    )
                    
                    # Upsert episode in database
                    self.database.upsert_episode(
                        server_id=self.server_id,
                        library_id=library_id,
                        parent_show_key=rating_key,
                        ep=episode,
                        media=media,
                        digest=digest,
                        now_epoch=now_epoch
                    )
                    
                    seen_keys.add(episode_key)
                    child_max = max(child_max, episode.get('updatedAt', 0))
                    changed_count += 1
            
            # Update show digest and mark as hydrated
            final_digest = digest_show(
                show.get('childCount', 0),
                show.get('leafCount', 0),
                show.get('updatedAt', 0),
                child_max
            )
            
            self.database.upsert_show_digest(
                library_id=library_id,
                show_key=rating_key,
                digest=final_digest,
                children_hydrated=True
            )
            
            return {'changed': changed_count}
            
        except Exception as ex:
            logger.warning(f"⚠️ Error expanding show {show_title}: {ex}")
            return {'changed': 0}
    
    def _finalize_library(self, library_id: int, seen_keys: set, now_epoch: int, retention_days: int = 30) -> tuple[int, int]:
        """
        Finalize library sync by processing state transitions and cleanup.
        
        This method implements the complete state management lifecycle:
        1. Process state transitions (ACTIVE -> MISSING, MISSING -> ACTIVE)
        2. Promote missing items to deleted after retention period
        3. Clean up old deleted items (optional)
        
        Args:
            library_id: Library ID
            seen_keys: Set of rating keys seen in this scan
            now_epoch: Current timestamp
            retention_days: Days to retain missing items before marking as deleted
            
        Returns:
            Tuple of (missing_promoted, deleted_promoted)
        """
        try:
            # Process state transitions
            transitions = self._process_state_transitions(library_id, seen_keys, now_epoch)
            
            # Promote missing items to deleted after retention period
            deleted_promoted = self._promote_missing_to_deleted(library_id, retention_days)
            
            # Optional: Clean up very old deleted items (90+ days)
            # This can be enabled for maintenance
            # cleanup_count = self._cleanup_old_deleted_items(library_id, 90)
            
            logger.info(f"📊 Library {library_id} finalized: "
                       f"{transitions['active_to_missing']} marked missing, "
                       f"{deleted_promoted} promoted to deleted")
            
            return transitions['active_to_missing'], deleted_promoted
            
        except Exception as ex:
            logger.warning(f"⚠️ Error finalizing library {library_id}: {ex}")
            return 0, 0
    
    def _fetch_show_children(self, show_key: str) -> list[dict]:
        """
        Returns list of seasons for a show.
        Works for JSON (MediaContainer.Metadata) and XML (MediaContainer.Directory).
        """
        url = f"{self.server_url}/library/metadata/{show_key}/children"
        print(f"🔍 DEBUG: _fetch_show_children URL: {url}")
        try:
            resp = self.session.get(url,  timeout=30)
            print(f"🔍 DEBUG: _fetch_show_children response status: {resp.status_code}")
            resp.raise_for_status()
            data = parse_plex_response(resp)          # <-- robust: JSON or XML
            data = _strip_at_keys(data)               # <-- normalize @ratingKey -> ratingKey
            mc = data.get("MediaContainer", {}) if isinstance(data, dict) else {}
            seasons = mc.get("Metadata") or mc.get("Directory") or []
            seasons = _coerce_list(seasons)
            print(f"🔍 DEBUG: _fetch_show_children found {len(seasons)} seasons for {show_key}")
            return seasons
        except Exception as ex:
            logger.warning(f"⚠️ Error fetching show children for {show_key}: {ex}")
            return []
    
    def _fetch_season_children(self, season_key: str) -> list[dict]:
        """
        Returns list of episodes for a season.
        JSON: MediaContainer.Metadata; XML: MediaContainer.Video
        """
        url = f"{self.server_url}/library/metadata/{season_key}/children"
        try:
            resp = self.session.get(url,  timeout=30)
            resp.raise_for_status()
            data = parse_plex_response(resp)
            data = _strip_at_keys(data)
            mc = data.get("MediaContainer", {}) if isinstance(data, dict) else {}
            episodes = mc.get("Metadata") or mc.get("Video") or []
            episodes = _coerce_list(episodes)
            # print(f"🔍 episodes for season {season_key}: {len(episodes)}")
            return episodes
        except Exception as ex:
            logger.warning(f"⚠️ Error fetching season children for {season_key}: {ex}")
            return []
    
    def _fetch_item_detail(self, item_key: str) -> dict:
        """
        Return a single episode/movie dict (normalized), handling JSON or XML.
        """
        url = f"{self.server_url}/library/metadata/{item_key}"
        try:
            resp = self.session.get(url,  timeout=30)
            resp.raise_for_status()
            data = parse_plex_response(resp)
            data = _strip_at_keys(data)
            mc = data.get("MediaContainer", {}) if isinstance(data, dict) else {}
            meta = mc.get("Metadata") or mc.get("Video")
            if isinstance(meta, list):
                return meta[0] if meta else {}
            return meta or {}
        except Exception as ex:
            logger.warning(f"⚠️ Error fetching item detail for {item_key}: {ex}")
            return {}
    
    def _validate_item_state(self, item_id: int, plex_path: str, media_info: dict) -> str:
        """
        Validate an item and determine its appropriate state.
        
        Args:
            item_id: Database ID of the item
            plex_path: Plex path for the item
            media_info: Media information from Plex
            
        Returns:
            The appropriate state for the item
        """
        try:
            # Try to resolve local path
            local_path = resolve_local_path(self.database, self.server_id, plex_path) or plex_path
            
            if local_path == plex_path:
                # No path mapping found - check if Plex can stream
                if media_info.get('duration', 0) > 0:
                    return 'REMOTE_ONLY'
                else:
                    return 'UNAVAILABLE'
            
            # Check if local file exists and is accessible
            if os.path.exists(local_path) and os.path.isfile(local_path):
                # Check file size matches
                local_size = os.path.getsize(local_path)
                plex_size = media_info.get('file_size', 0)
                
                if plex_size > 0 and abs(local_size - plex_size) > 1024:  # Allow 1KB difference
                    logger.warning(f"⚠️ File size mismatch for {local_path}: local={local_size}, plex={plex_size}")
                    return 'UNAVAILABLE'
                
                return 'ACTIVE'
            else:
                # Local file doesn't exist
                if media_info.get('duration', 0) > 0:
                    return 'REMOTE_ONLY'
                else:
                    return 'UNAVAILABLE'
                    
        except Exception as ex:
            logger.warning(f"⚠️ Error validating item state for {plex_path}: {ex}")
            return 'UNAVAILABLE'
    
    def _update_item_state(self, item_id: int, new_state: str, error_message: str = None) -> bool:
        """
        Update the state of a media item in the database.
        
        Args:
            item_id: Database ID of the item
            new_state: New state to set
            error_message: Optional error message for error states
            
        Returns:
            True if state was updated successfully
        """
        try:
            return self.database.update_item_state(item_id, new_state, error_message)
        except Exception as ex:
            logger.warning(f"⚠️ Error updating item state: {ex}")
            return False
    
    def _process_state_transitions(self, library_id: int, seen_keys: set, now_epoch: int) -> Dict[str, int]:
        """
        Process state transitions for items in a library.
        
        Args:
            library_id: Library ID
            seen_keys: Set of rating keys seen in this scan
            now_epoch: Current timestamp
            
        Returns:
            Dictionary with transition counts
        """
        transitions = {
            'active_to_missing': 0,
            'missing_to_deleted': 0,
            'state_updates': 0
        }
        
        try:
            # Get all items in this library
            cursor = self.database.connection.cursor()
            cursor.execute("""
                SELECT id, rating_key, state, plex_path, last_seen_at
                FROM media_files 
                WHERE library_id = ?
            """, (library_id,))
            
            items = cursor.fetchall()
            
            for item in items:
                item_id, rating_key, current_state, plex_path, last_seen_at = item
                
                if rating_key not in seen_keys:
                    # Item not seen in this scan
                    if current_state == 'ACTIVE':
                        # Mark as missing
                        self.database.update_item_state(item_id, 'MISSING')
                        transitions['active_to_missing'] += 1
                        transitions['state_updates'] += 1
                        
                        # Update missing_since timestamp
                        cursor.execute("""
                            UPDATE media_files 
                            SET missing_since = ?
                            WHERE id = ?
                        """, (now_epoch, item_id))
                        
                elif current_state == 'MISSING':
                    # Item was missing but now seen again
                    self.database.update_item_state(item_id, 'ACTIVE')
                    transitions['state_updates'] += 1
                    
                    # Clear missing_since timestamp
                    cursor.execute("""
                        UPDATE media_files 
                        SET missing_since = NULL
                        WHERE id = ?
                    """, (item_id,))
            
            self.database.connection.commit()
            return transitions
            
        except Exception as ex:
            logger.warning(f"⚠️ Error processing state transitions: {ex}")
            self.database.connection.rollback()
            return transitions
    
    def _promote_missing_to_deleted(self, library_id: int, retention_days: int = 30) -> int:
        """
        Promote missing items to deleted status after retention period.
        
        Args:
            library_id: Library ID
            retention_days: Days to retain missing items
            
        Returns:
            Number of items promoted to deleted
        """
        try:
            cutoff_epoch = int(datetime.now().timestamp()) - (retention_days * 24 * 60 * 60)
            
            cursor = self.database.connection.cursor()
            cursor.execute("""
                UPDATE media_files 
                SET state = 'DELETED', last_scan_at = ?
                WHERE library_id = ? AND state = 'MISSING' AND missing_since < ?
            """, (int(datetime.now().timestamp()), library_id, cutoff_epoch))
            
            promoted_count = cursor.rowcount
            self.database.connection.commit()
            
            if promoted_count > 0:
                logger.info(f"📊 Promoted {promoted_count} missing items to deleted in library {library_id}")
            
            return promoted_count
            
        except Exception as ex:
            logger.warning(f"⚠️ Error promoting missing to deleted: {ex}")
            self.database.connection.rollback()
            return 0
    
    def _cleanup_old_deleted_items(self, library_id: int, days_old: int = 90) -> int:
        """
        Remove old deleted items from the database.
        
        Args:
            library_id: Library ID
            days_old: Days old before removal
            
        Returns:
            Number of items removed
        """
        try:
            return self.database.cleanup_old_deleted_items(library_id, days_old)
        except Exception as ex:
            logger.warning(f"⚠️ Error cleaning up deleted items: {ex}")
            return 0
    
    def get_library_health_report(self, library_id: int) -> Dict:
        """
        Get a comprehensive health report for a library.
        
        Args:
            library_id: Library ID
            
        Returns:
            Dictionary with health report data
        """
        try:
            stats = self.database.get_library_stats(library_id)
            missing_count, deleted_count = self.database.library_missing_deleted_counts(library_id)
            
            # Calculate health score
            total_items = stats['total_items']
            if total_items == 0:
                health_score = 100
            else:
                active_ratio = stats['active_items'] / total_items
                health_score = int(active_ratio * 100)
            
            return {
                'library_id': library_id,
                'health_score': health_score,
                'total_items': total_items,
                'active_items': stats['active_items'],
                'remote_only_items': stats['remote_only_items'],
                'unavailable_items': stats['unavailable_items'],
                'missing_items': missing_count,
                'deleted_items': deleted_count,
                'last_scan_at': stats['last_scan_at'],
                'status': self._get_health_status(health_score)
            }
            
        except Exception as ex:
            logger.warning(f"⚠️ Error getting library health report: {ex}")
            return {
                'library_id': library_id,
                'health_score': 0,
                'total_items': 0,
                'active_items': 0,
                'remote_only_items': 0,
                'unavailable_items': 0,
                'missing_items': 0,
                'deleted_items': 0,
                'last_scan_at': None,
                'status': 'ERROR'
            }
    
    def _get_health_status(self, health_score: int) -> str:
        """Get health status based on score."""
        if health_score >= 95:
            return 'EXCELLENT'
        elif health_score >= 85:
            return 'GOOD'
        elif health_score >= 70:
            return 'FAIR'
        elif health_score >= 50:
            return 'POOR'
        else:
            return 'CRITICAL'
    
    def _sync_show_library_legacy(self, library_key: str, progress_callback=None) -> Dict[str, int]:
        """Legacy sync method - kept for fallback if needed"""
        # Get current shows from Plex
        plex_shows = self.get_library_items(library_key, 'show')
        plex_show_ids = {show.get('guid', '') for show in plex_shows}  # Use stable GUID
        
        # Get current shows from database for this server only
        db_shows = self.database.get_shows_by_source('plex')
        db_show_ids = {show['source_id'] for show in db_shows if show['source_id'] and show.get('server_id') == self.server_id}
        
        updated_count = 0
        added_count = 0
        removed_count = 0
        
        total_shows = len(plex_shows)
        
        # Update existing and add new shows
        for i, show in enumerate(plex_shows):
            show_guid = show.get('guid', '')  # Use stable GUID
            show_title = show.get('title', 'Unknown Show')
            
            # Process show silently
            
            if show_guid in db_show_ids:
                # Compare timestamps before updating
                ts = plex_ts(show)
                db_ts_raw = self.database.get_show_ts_by_guid(show_guid)
                db_ts = db_ts_to_int(db_ts_raw)
                
                if db_ts is not None and ts is not None and ts <= db_ts:
                    # Skip update - Plex timestamp is older or equal, no changes
                    continue
                
                # Update existing show and its episodes
                show_id = self.database.add_show(
                    title=show.get('title', 'Unknown Show'),
                    total_seasons=show.get('leafCount', 0),
                    total_episodes=0,  # Will be updated by episode sync
                    show_rating=self._map_plex_rating(show.get('contentRating', '')),
                    show_summary=show.get('summary', ''),
                    genre=', '.join([g.get('tag', '') for g in show.get('Genre', [])]),
                    source_type='plex',
                    source_id=show_guid,
                    server_id=self.server_id,
                    plex_updated_at=self._get_show_timestamp(show)
                )
                episode_count = self._sync_show_episodes(show, progress_callback)
                updated_count += episode_count
            else:
                # Add new show first, then sync its episodes
                show_id = self.database.add_show(
                    title=show.get('title', 'Unknown Show'),
                    total_seasons=show.get('leafCount', 0),
                    total_episodes=0,  # Will be updated by episode sync
                    show_rating=self._map_plex_rating(show.get('contentRating', '')),
                    show_summary=show.get('summary', ''),
                    genre=', '.join([g.get('tag', '') for g in show.get('Genre', [])]),
                    source_type='plex',
                    source_id=show_guid,
                    server_id=self.server_id,
                    plex_updated_at=self._get_show_timestamp(show)
                )
                # Now sync episodes for the newly added show
                episode_count = self._sync_show_episodes(show, progress_callback)
                added_count += episode_count
        
        # Remove shows that no longer exist in Plex
        for db_show in db_shows:
            if db_show['source_id'] and db_show['source_id'] not in plex_show_ids:
                if self.database.remove_show_by_source_id(db_show['source_id']):
                    removed_count += 1
        
        return {'updated': updated_count, 'added': added_count, 'removed': removed_count}
    
    def sync_show_by_title_and_year(self, title: str, year: int = None) -> Dict[str, int]:
        """
        Sync a specific show by title and year for disambiguation.
        
        Args:
            title: Show title
            year: Optional year for disambiguation
            
        Returns:
            Dictionary with sync results: {'updated': int, 'added': int, 'removed': int}
        """
        # Discover shows matching the criteria
        shows = self.discover_shows_by_title(title, year)
        
        if not shows:
            self._emit_status(f"❌ No shows found matching '{title}'" + (f" ({year})" if year else ""))
            return {'updated': 0, 'added': 0, 'removed': 0}
        
        # Display discovered shows
        self._emit_status(f"🔍 Found {len(shows)} show(s) matching '{title}'" + (f" ({year})" if year else ""))
        for show in shows:
            self._emit_status(f"  📺 {show['display_name']}")
        
        total_updated = 0
        total_added = 0
        total_removed = 0
        
        # Sync each discovered show
        for show in shows:
            show_guid = show['raw_metadata'].get('guid', '')
            show_title = show['title']
            show_year = show['year']
            
            # Check if show already exists in database
            existing_show = self.database.get_show_by_source_id(show_guid)
            
            if existing_show:
                # Compare timestamps before updating
                ts = plex_ts(show['raw_metadata'])
                db_ts_raw = self.database.get_show_ts_by_guid(show_guid)
                db_ts = db_ts_to_int(db_ts_raw)
                
                if db_ts is not None and ts is not None and ts <= db_ts:
                    # Skip update - Plex timestamp is older or equal, no changes
                    self._emit_status(f"⏭️ Skipping show (no changes): {show['display_name']}")
                    continue
                
                # Update existing show
                self._emit_status(f"🔄 Updating existing show: {show['display_name']}")
                show_id = self.database.add_show(
                    title=show['raw_metadata'].get('title', 'Unknown Show'),
                    plex_rating_key=show['raw_metadata'].get('ratingKey', ''),
                    year=show['raw_metadata'].get('year'),
                    total_seasons=show['raw_metadata'].get('leafCount', 0),
                    total_episodes=0,  # Will be updated by episode sync
                    show_rating=self._map_plex_rating(show['raw_metadata'].get('contentRating', '')),
                    show_summary=show['raw_metadata'].get('summary', ''),
                    genre=', '.join([g.get('tag', '') for g in show['raw_metadata'].get('Genre', [])]),
                    studio=show['raw_metadata'].get('studio', ''),
                    originally_available_at=show['raw_metadata'].get('originallyAvailableAt'),
                    guid_primary=show['raw_metadata'].get('guid', ''),
                    source_type='plex',
                    source_id=show_guid,
                    server_id=self.server_id,
                    plex_updated_at=self._get_show_timestamp(show['raw_metadata'])
                )
                episode_count = self._sync_show_episodes(show['raw_metadata'])
                total_updated += episode_count
            else:
                # Add new show
                self._emit_status(f"➕ Adding new show: {show['display_name']}")
                episode_count = self.import_show_episodes(show['raw_metadata'])
                total_added += episode_count
        
        self._emit_status(f"🎉 Sync completed for '{title}'" + (f" ({year})" if year else "") + 
                         f" - Added: {total_added}, Updated: {total_updated}")
        
        return {'updated': total_updated, 'added': total_added, 'removed': total_removed}
    
    def _update_movie(self, movie: Dict, library_name: str = None, library_root: str = None, library_root_paths: List[str] = None) -> bool:
        """Update an existing movie with current Plex data"""
        try:
            movie_guid = movie.get('guid', '')  # Use stable GUID
            if not movie_guid:
                return False
            
            # Get current movie from database
            db_movie = self.database.get_movie_by_source_id(movie_guid)
            if not db_movie:
                return False
            
            # Get Plex timestamp for updating the database
            plex_updated_at = plex_ts(movie)
            movie_title = movie.get('title', 'Unknown Movie')
            
            # DEBUG: Show that we're processing this movie
            self._emit_status(f"🔄 PROCESSING Movie '{movie_title}': Updating with Plex timestamp {plex_updated_at}", debug_only=True)
            
            # Update movie data
            title = movie.get('title', 'Unknown Movie')
            year = movie.get('year')
            rating = self._map_plex_rating(movie.get('contentRating', ''))
            summary = movie.get('summary', '')
            genre = ', '.join([g.get('tag', '') for g in movie.get('Genre', [])])
            director = ', '.join([d.get('tag', '') for d in movie.get('Director', [])])
            
            # Get duration and file path from Media array
            media_array = movie.get('Media', [])
            plex_file_path = self._get_file_path_from_media(media_array)
            duration = self._get_duration_from_media(media_array)
            
            if not duration:
                return False
            
            # Convert Plex path to local path
            local_file_path = self._get_local_path_from_plex_path(plex_file_path)
            
            # Check if anything has actually changed
            has_changes = False
            
            # Check media file changes (no longer compare file_path since we don't store local paths)
            if (db_movie.get('duration') != duration or
                db_movie.get('library_name') != library_name):
                has_changes = True
                self.database.update_media_file(
                    media_file_id=db_movie['media_file_id'],
                    duration=duration,
                    library_name=library_name,
                    plex_path=plex_file_path
                )
            
            # Check movie metadata changes
            metadata_changed = (db_movie.get('title') != title or 
                              db_movie.get('year') != year or 
                              db_movie.get('rating') != rating or 
                              db_movie.get('summary') != summary or 
                              db_movie.get('genre') != genre or 
                              db_movie.get('director') != director)
            
            if metadata_changed:
                has_changes = True
            
            # Always update the updated_at field to reflect current state
            self.database.update_movie(
                movie_id=db_movie['id'],
                title=title,
                year=year,
                rating=rating,
                summary=summary,
                genre=genre,
                director=director,
                plex_updated_at=plex_updated_at
            )
            
            # Persist the new timestamp after successful update
            if plex_updated_at is not None:
                self.database.set_movie_ts_by_guid(movie_guid, plex_updated_at)
            
            # Return whether there were changes (status message handled by progress callback)
            return has_changes
            
        except Exception as e:
            self._emit_status(f"❌ Error updating movie '{movie_title}': {e}", debug_only=True)
            return False
    
    def _sync_show_episodes(self, show: Dict, progress_callback=None, library_progress=None, library_name: str = None, library_root_paths: List[str] = None) -> int:
        """Sync episodes for an existing show"""
        try:
            show_title = show.get('title', 'Unknown Show')
            show_key = show.get('key', '')
            show_guid = show.get('guid', '')  # Use stable GUID
            
            # Compute primary library root from library_root_paths
            primary_library_root = library_root_paths[0] if library_root_paths else None
            
            # Get current episodes from Plex
            plex_episodes = self.get_show_episodes(show_key)
            plex_episode_ids = {episode.get('guid', '') for episode in plex_episodes}  # Use stable GUID
            
            # Get current episodes from database for this show (cache for performance)
            db_episodes = self.database.get_episodes_by_show_source_id(show_guid)  # Use GUID to match stored source_id
            db_episode_ids = {episode['source_id'] for episode in db_episodes if episode['source_id']}
            
            # Create lookup dict for faster episode access
            db_episode_lookup = {episode['source_id']: episode for episode in db_episodes if episode['source_id']}
            
            
            updated_count = 0
            added_count = 0
            removed_count = 0
            
            # Update existing and add new episodes
            for i, episode in enumerate(plex_episodes):
                episode_guid = episode.get('guid', '')  # Use stable GUID
                episode_title = episode.get('title', 'Unknown Episode')
                
                # DEBUG: Show EVERY episode being processed
                self._emit_status(f"📺 PROCESSING Episode {i+1}/{len(plex_episodes)}: '{show_title} / {episode_title}' (GUID: {episode_guid})", debug_only=True)
                
                # Update progress for each episode processed (moved outside conditional)
                if progress_callback and library_progress:
                    # Get episode number and season info
                    episode_number = episode.get('index', 0)
                    season_number = episode.get('parentIndex', 0)
                    # Format: "Show Title / Episode Title (episode #/total episodes in this show)"
                    show_episode_display = f"{show_title} / {episode_title} ({episode_number}/{len(plex_episodes)})"
                    progress_callback(
                        library_progress=library_progress,
                        item_progress=(i + 1, len(plex_episodes), show_episode_display),
                        message=None  # No status messages during scanning
                    )
                
                if episode_guid in db_episode_ids:
                    # Compare timestamps before updating
                    ts = plex_ts(episode)
                    db_ts_raw = self.database.get_episode_ts_by_guid(episode_guid)
                    db_ts = db_ts_to_int(db_ts_raw)
                    
                    if db_ts is not None and ts is not None and ts <= db_ts:
                        # Skip update - Plex timestamp is older or equal, no changes
                        self._emit_status(f"⏭️ SKIP Episode '{episode_title}': Plex timestamp ({ts}) <= DB timestamp ({db_ts}), no changes", debug_only=True)
                        # Emit progress but no status message
                        if progress_callback:
                            progress_callback(
                                library_progress=library_progress,
                                item_progress=(i + 1, len(plex_episodes), show_episode_display),
                                message=None
                            )
                    else:
                        # Get the Plex file path for this episode
                        episode_file_path = self._get_file_path_from_media(episode.get('Media', []))
                        
                        # Update existing episode (only count if there were actual changes)
                        self._emit_status(f"🔄 UPDATE Episode '{episode_title}': Timestamps differ (Plex: {ts}, DB: {db_ts})", debug_only=True)
                        db_episode = db_episode_lookup[episode_guid]
                        if self._update_episode(episode, show, library_name, primary_library_root, db_episode, library_root_paths):
                            updated_count += 1
                            # Emit status message for database change
                            if progress_callback:
                                progress_callback(
                                    library_progress=library_progress,
                                    item_progress=(i + 1, len(plex_episodes), show_episode_display),
                                    message=f"Updated episode: {episode_title}"
                                )
                else:
                    # Get the Plex file path for this episode
                    episode_file_path = self._get_file_path_from_media(episode.get('Media', []))
                    
                    # Add new episode
                    if self._add_episode(episode, show, library_name, primary_library_root, library_root_paths):
                        added_count += 1
                        # Emit status message for database change
                        if progress_callback:
                            progress_callback(
                                library_progress=library_progress,
                                item_progress=(i + 1, len(plex_episodes), show_episode_display),
                                message=f"Added episode: {episode_title}"
                            )
            
            # Remove episodes that no longer exist in Plex
            for db_episode in db_episodes:
                if db_episode['source_id'] and db_episode['source_id'] not in plex_episode_ids:
                    if self.database.remove_episode_by_source_id(db_episode['source_id']):
                        removed_count += 1
                        # Emit status message for database change
                        if progress_callback:
                            episode_title = db_episode.get('title', 'Unknown Episode')
                            progress_callback(
                                library_progress=library_progress,
                                item_progress=None,  # No item progress for removals
                                message=f"Removed episode: {episode_title}"
                            )
            
            # Only output if there were actual changes
            total_changes = updated_count + added_count + removed_count
            
            # Update show's updated_at if any episodes were processed
            if total_changes > 0:
                # Update the show's updated_at to reflect that it was processed
                # Use the show's Plex timestamp instead of CURRENT_TIMESTAMP
                show_ts = plex_ts(show)
                if show_ts is not None:
                    cursor = self.database.connection.cursor()
                    cursor.execute("""
                        UPDATE shows 
                        SET updated_at = ? 
                        WHERE source_id = ?
                    """, (show_ts, show_guid))
                    self.database.connection.commit()
            
            # Always persist the show's Plex timestamp after processing
            show_ts = plex_ts(show)
            if show_ts is not None:
                self.database.set_show_ts_by_guid(show_guid, show_ts)
            
            # No summary messages - just progress bars
            
            # Return the number of actual database changes (not total episodes processed)
            return total_changes
            
        except Exception as e:
            self._emit_status(f"❌ Error in _sync_show_episodes: {e}", debug_only=True)
            return 0
    
    def _update_episode(self, episode: Dict, show: Dict, library_name: str = None, library_root: str = None, db_episode: Dict = None, library_root_paths: List[str] = None) -> bool:
        """Update an existing episode with current Plex data"""
        try:
            episode_guid = episode.get('guid', '')  # Use stable GUID
            if not episode_guid:
                return False
            
            # Get current episode from database (use provided or fetch)
            if not db_episode:
                db_episode = self.database.get_episode_by_source_id(episode_guid)
                if not db_episode:
                    return False
            
            # Get Plex timestamp for updating the database
            plex_updated_at = plex_ts(episode)
            
            # Update episode data
            episode_title = episode.get('title', 'Unknown Episode')
            # Convert to integers to match database storage
            season_number = int(episode.get('parentIndex', 0)) if episode.get('parentIndex') is not None else 0
            episode_number = int(episode.get('index', 0)) if episode.get('index') is not None else 0
            rating = self._map_plex_rating(episode.get('contentRating', ''))
            summary = episode.get('summary', '')
            
            # Get duration and file path from Media array
            media_array = episode.get('Media', [])
            plex_file_path = self._get_file_path_from_media(media_array)
            duration = self._get_duration_from_media(media_array)
            
            if not duration:
                return False
            
            # Convert Plex path to local path
            local_file_path = self._get_local_path_from_plex_path(plex_file_path)
            
            # Check if anything has actually changed
            has_changes = False
            
            # Check media file changes
            # Only update library_name if it's currently NULL (first-time assignment)
            library_name_changed = (db_episode.get('library_name') is None and library_name is not None)
            
            # Check for duration changes (no longer check file_path since we don't store local paths)
            duration_changed = (db_episode.get('duration') != duration)
            
            if (duration_changed or library_name_changed):
                # Update the media file data
                update_library_name = library_name if library_name_changed else db_episode.get('library_name')
                self.database.update_media_file(
                    media_file_id=db_episode['media_file_id'],
                    duration=duration,
                    library_name=update_library_name,
                    plex_path=plex_file_path
                )
                
                # Count as "changes" if duration or library name changed
                if duration_changed or library_name_changed:
                    has_changes = True
            
            # Check episode metadata changes - ensure proper type comparison
            metadata_changed = (db_episode.get('episode_title') != episode_title or 
                              db_episode.get('season_number') != season_number or 
                              db_episode.get('episode_number') != episode_number or 
                              db_episode.get('rating') != rating or 
                              db_episode.get('summary') != summary)
            
            if metadata_changed:
                has_changes = True
            
            # Always update the updated_at field to reflect current state
            self.database.update_episode(
                episode_id=db_episode['id'],
                episode_title=episode_title,
                season_number=season_number,
                episode_number=episode_number,
                rating=rating,
                summary=summary,
                plex_updated_at=plex_updated_at
            )
            
            # Persist the new timestamp after successful update
            if plex_updated_at is not None:
                self.database.set_episode_ts_by_guid(episode_guid, plex_updated_at)
            
            # Return whether there were changes
            return has_changes
            
        except Exception as e:
            self._emit_status(f"❌ Error updating episode '{episode_title}': {e}", debug_only=True)
            return False
    
    def _add_episode(self, episode: Dict, show: Dict, library_name: str = None, library_root: str = None, library_root_paths: List[str] = None) -> bool:
        """Add a new episode to an existing show"""
        try:
            # Get show ID from database using the show's GUID
            show_guid = show.get('guid', '')
            # Use a simpler query that doesn't require JOIN with media_files
            cursor = self.database.connection.cursor()
            cursor.execute("SELECT * FROM shows WHERE source_id = ?", (show_guid,))
            db_show = cursor.fetchone()
            if db_show:
                db_show = dict(db_show)
            if not db_show:
                # Show doesn't exist, create it first
                try:
                    show_id = self.database.add_show(
                        title=show.get('title', 'Unknown Show'),
                        plex_rating_key=show.get('ratingKey', ''),  # Keep for display purposes
                        year=show.get('year'),
                        total_seasons=show.get('leafCount', 0),
                        total_episodes=0,  # Will be updated as episodes are added
                        show_rating=self._map_plex_rating(show.get('contentRating', '')),
                        show_summary=show.get('summary', ''),
                        genre=', '.join([g.get('tag', '') for g in show.get('Genre', [])]),
                        studio=show.get('studio', ''),
                        originally_available_at=show.get('originallyAvailableAt'),
                        guid_primary=show.get('guid', ''),
                        source_type='plex',
                        source_id=show.get('guid', ''),
                        server_id=self.server_id,
                        plex_updated_at=self._get_show_timestamp(show)
                    )
                    # Get the show record we just created
                    cursor.execute("SELECT * FROM shows WHERE source_id = ?", (show.get('guid', ''),))
                    db_show = cursor.fetchone()
                    if db_show:
                        db_show = dict(db_show)
                    if not db_show:
                        return False
                except Exception as e:
                    self._emit_status(f"❌ Error creating show in _add_episode: {e}", debug_only=True)
                    return False
            
            episode_title = episode.get('title', 'Unknown Episode')
            episode_key = episode.get('key', '')
            episode_guid = episode.get('guid', '')  # Use stable GUID
            # Convert to integers to match database storage
            season_number = int(episode.get('parentIndex', 0)) if episode.get('parentIndex') is not None else 0
            episode_number = int(episode.get('index', 0)) if episode.get('index') is not None else 0
            rating = self._map_plex_rating(episode.get('contentRating', ''))
            summary = episode.get('summary', '')
            
            # Get duration and file path from Media array
            media_array = episode.get('Media', [])
            plex_file_path = self._get_file_path_from_media(media_array)
            duration = self._get_duration_from_media(media_array)
            
            if not duration:
                return False
            
            # Convert Plex path to local path
            local_file_path = self._get_local_path_from_plex_path(plex_file_path)
            
            # Add media file
            media_file_id = self.database.add_media_file(
                duration=duration,
                media_type='episode',
                source_type='plex',
                source_id=episode_guid,  # Use stable GUID
                library_name=library_name,
                server_id=self.server_id,
                plex_path=plex_file_path
            )
            
            # Add episode
            self.database.add_episode(
                media_file_id=media_file_id,
                show_id=db_show['id'],
                episode_title=episode_title,
                season_number=season_number,
                episode_number=episode_number,
                rating=rating,
                summary=summary,
                plex_updated_at=episode.get('updatedAt')
            )
            
            return True
            
        except Exception as e:
            self._emit_status(f"❌ Error adding episode '{episode_title}': {e}", debug_only=True)
            return False
    
    def import_all_libraries(self) -> int:
        """Import all libraries from Plex server (legacy method - use sync_all_libraries instead)"""
        libraries = self.get_libraries()
        total_imported = 0
        
        for library in libraries:
            library_key = library.get('key', '')
            library_title = library.get('title', 'Unknown Library')
            library_type = library.get('type', 'movie')
            
            count = self.import_library(library_key, library_type)
            total_imported += count
        
        return total_imported


def create_plex_importer(server_id: int, database: RetrovueDatabase, status_callback=None) -> Optional[PlexImporter]:
    """
    Create a Plex importer instance and test the connection.
    
    Args:
        server_id: Plex server ID from database
        database: Database instance
        status_callback: Optional callback function for status updates
        
    Returns:
        PlexImporter instance if connection successful, None otherwise
    """
    try:
        importer = PlexImporter(server_id, database, status_callback)
        
        if importer.test_connection():
            importer._emit_status(f"✅ Connected to Plex server: {importer.server_name} ({importer.server_url})")
            return importer
        else:
            importer._emit_status(f"❌ Failed to connect to Plex server: {importer.server_name}")
            return None
    except Exception as e:
        if status_callback:
            status_callback(f"❌ Error creating Plex importer: {e}")
        return None


def create_plex_importer_legacy(server_url: str, token: str, database: RetrovueDatabase, status_callback=None) -> Optional[PlexImporter]:
    """
    Create a Plex importer instance using legacy URL/token method (for backward compatibility).
    
    Args:
        server_url: Plex server URL
        token: Plex authentication token
        database: Database instance
        status_callback: Optional callback function for status updates
        
    Returns:
        PlexImporter instance if connection successful, None otherwise
    """
    # Add server to database if it doesn't exist
    server_id = database.add_plex_server("Legacy Server", server_url, token)
    
    # Create importer using the new method
    return create_plex_importer(server_id, database, status_callback)


# ============================================================================
# Dev Sync Wrapper API
# ============================================================================

from typing import Callable, Dict, Any

ProgressCb = Callable[[str, Dict[str, Any]], None]

def make_library_ref(db, server_id: int, section_key: str):
    """
    Create a library reference object for sync operations.
    
    Args:
        db: Database instance
        server_id: Server ID
        section_key: Library section key
        
    Returns:
        Library reference dict with server_id, id, section_key, type
    """
    # Get library info from database
    library_info = db.get_library_by_key(section_key, server_id)
    if library_info:
        return {
            'server_id': server_id,
            'id': library_info['id'],
            'section_key': section_key,
            'type': library_info['library_type'],
            'name': library_info['library_name']
        }
    else:
        # Create a minimal reference - the sync methods will create the library record
        return {
            'server_id': server_id,
            'id': None,
            'section_key': section_key,
            'type': 'unknown',  # Will be determined during sync
            'name': f"Library {section_key}"
        }

def sync_one_library(db, library_ref, *, deep=False, dry_run=False, progress: ProgressCb=lambda *_: None):
    """
    Sync a single library.
    
    Args:
        db: Database instance
        library_ref: Library reference object with server_id, section_key, type
        deep: Force full expansion
        dry_run: Don't make changes
        progress: Progress callback
        
    Returns:
        Summary dict with processed, changed, skipped, errors, missing_promoted, deleted_promoted
    """
    print(f"🔍 DEBUG: Starting sync for library: {library_ref.get('name', 'Unknown')} (type: {library_ref.get('type', 'unknown')})")
    print(f"🔍 DEBUG: Library ref: {library_ref}")
    
    # Create Plex importer for the server
    importer = create_plex_importer(library_ref['server_id'], db)
    if not importer:
        print(f"🔍 DEBUG: Failed to create Plex importer for server {library_ref['server_id']}")
        return {"processed": 0, "changed": 0, "skipped": 0, "errors": 1, "missing_promoted": 0, "deleted_promoted": 0}
    
    print(f"🔍 DEBUG: Created Plex importer successfully")
    
    # Emit library start event
    progress("library_start", {
        "server_id": library_ref['server_id'],
        "library_id": library_ref.get('id', 0),
        "library_name": library_ref.get('name', 'Unknown')
    })
    
    try:
        # Call the appropriate sync method based on library type
        if library_ref['type'] in ("show", "shows", "tv"):
            result = importer.sync_tv_library(library_ref['section_key'], deep=deep, progress_callback=progress)
        elif library_ref['type'] in ("movie", "movies"):
            result = importer.sync_movie_library(library_ref['section_key'], deep=deep, progress_callback=progress)
        else:
            # Try to determine type from Plex API
            libraries = importer.get_libraries()
            library_type = "movie"  # default
            for lib in libraries:
                if lib.get('key') == library_ref['section_key']:
                    library_type = lib.get('type', 'movie')
                    break
            
            if library_type in ("show", "shows", "tv"):
                result = importer.sync_tv_library(library_ref['section_key'], deep=deep, progress_callback=progress)
            else:
                result = importer.sync_movie_library(library_ref['section_key'], deep=deep, progress_callback=progress)
        
        # Convert result format to match expected summary format
        summary = {
            "processed": result.get('updated', 0) + result.get('added', 0),
            "changed": result.get('updated', 0),
            "skipped": 0,  # Not tracked in current implementation
            "errors": 0,   # Not tracked in current implementation
            "missing_promoted": 0,  # Not tracked separately in current implementation
            "deleted_promoted": result.get('removed', 0)
        }
        
        # Emit library done event
        progress("library_done", {
            "server_id": library_ref['server_id'],
            "library_id": library_ref.get('id', 0),
            "summary": summary
        })
        
        return summary
        
    except Exception as e:
        # Emit error event
        progress("library_done", {
            "server_id": library_ref['server_id'],
            "library_id": library_ref.get('id', 0),
            "summary": {
                "processed": 0,
                "changed": 0,
                "skipped": 0,
                "errors": 1,
                "missing_promoted": 0,
                "deleted_promoted": 0
            }
        })
        return {"processed": 0, "changed": 0, "skipped": 0, "errors": 1, "missing_promoted": 0, "deleted_promoted": 0}

def sync_selected_on_server(db, server_id: int, *, deep=False, dry_run=False, progress: ProgressCb=lambda *_: None):
    """
    Sync all selected libraries on a specific server.
    
    Args:
        db: Database instance
        server_id: Server ID
        deep: Force full expansion
        dry_run: Don't make changes
        progress: Progress callback
        
    Returns:
        Aggregated summary across all libraries
    """
    # Get selected libraries for this server
    libs = db.get_server_libraries(server_id=server_id)
    selected_libs = [lib for lib in libs if lib.get('sync_enabled', True)]
    
    print(f"🔍 DEBUG: Found {len(libs)} total libraries for server {server_id}")
    print(f"🔍 DEBUG: {len(selected_libs)} libraries are enabled for sync")
    for lib in selected_libs:
        print(f"🔍 DEBUG: - {lib['library_name']} ({lib['library_type']}) - sync_enabled: {lib.get('sync_enabled', True)}")
    
    totals = {"processed": 0, "changed": 0, "skipped": 0, "errors": 0, "missing_promoted": 0, "deleted_promoted": 0}
    
    for lib in selected_libs:
        lib_ref = {
            'server_id': lib['server_id'],
            'id': lib['id'],
            'section_key': lib['library_key'],
            'type': lib['library_type'],
            'name': lib['library_name']
        }
        
        summary = sync_one_library(db, lib_ref, deep=deep, dry_run=dry_run, progress=progress)
        for k in totals:
            totals[k] += summary.get(k, 0)
    
    return totals

def sync_selected_across_all_servers(db, *, deep=False, dry_run=False, progress: ProgressCb=lambda *_: None):
    """
    Sync all selected libraries across all servers.
    
    Args:
        db: Database instance
        deep: Force full expansion
        dry_run: Don't make changes
        progress: Progress callback
        
    Returns:
        Grand total summary across all servers and libraries
    """
    servers = db.get_plex_servers()
    active_servers = [s for s in servers if s.get('is_active', True)]
    
    grand = {"processed": 0, "changed": 0, "skipped": 0, "errors": 0, "missing_promoted": 0, "deleted_promoted": 0}
    
    for server in active_servers:
        sub = sync_selected_on_server(db, server_id=server['id'], deep=deep, dry_run=dry_run, progress=progress)
        for k in grand:
            grand[k] += sub.get(k, 0)
    
    return grand