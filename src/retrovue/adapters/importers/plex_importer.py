"""
Plex Media Server importer plugin for RetroVue.

This importer connects to Plex Media Server instances and discovers content
from their libraries, following the plugin contract defined in docs/developer/PluginAuthoring.md.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ...domain.asset_draft import AssetDraft
from .base import ImporterError

logger = logging.getLogger(__name__)


class PlexClient:
    """Plex HTTP client for fetching libraries and items."""
    
    def __init__(self, base_url: str, token: str):
        """
        Initialize Plex client.
        
        Args:
            base_url: Plex server base URL (e.g., "http://127.0.0.1:32400")
            token: Plex authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def get_libraries(self) -> list[dict[str, Any]]:
        """
        Get all libraries from the Plex server.
        
        Returns:
            List of library information dictionaries
            
        Raises:
            ImporterError: If the request fails
        """
        try:
            url = f"{self.base_url}/library/sections"
            params = {"X-Plex-Token": self.token}
            
            response = self.session.get(url, params=params, timeout=20)
            response.raise_for_status()
            
            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            libraries = []
            sections = root.findall('Directory')
            
            for section in sections:
                lib_id = section.get('key')
                lib_name = section.get('title')
                lib_type = section.get('type')
                
                if lib_id and lib_name:
                    # Extract filesystem locations from Location elements
                    locations = []
                    for location in section.findall('Location'):
                        path = location.get('path')
                        if path:
                            locations.append(path)
                    
                    libraries.append({
                        "key": lib_id,
                        "title": lib_name,
                        "type": lib_type,
                        "locations": locations
                    })
            
            return libraries
            
        except requests.RequestException as e:
            raise ImporterError(f"Failed to fetch libraries: {e}") from e
    
    def get_library_items(self, library_key: str, title_filter: str = None, season_filter: int = None, episode_filter: int = None) -> list[dict[str, Any]]:
        """
        Get all items from a specific library.
        
        Args:
            library_key: The library key to fetch items from
            
        Returns:
            List of item information dictionaries
            
        Raises:
            ImporterError: If the request fails
        """
        try:
            # Get library content to determine type
            url = f"{self.base_url}/library/sections/{library_key}/all"
            params = {"X-Plex-Token": self.token}
            response = self.session.get(url, params=params, timeout=20)
            response.raise_for_status()
            
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            library_type = root.get('type', '')
            view_group = root.get('viewGroup', '')
            
            items = []
            
            # If it's a TV show library, drill down to get episodes
            if library_type == 'show' or view_group == 'show':
                # Use the shows we already have from the root
                shows = root.findall('Directory')
                
                # For each show, get its seasons and episodes
                for show in shows:
                    show_key = show.get('ratingKey')
                    show_title = show.get('title')
                    
                    # Apply title filter if specified
                    if title_filter and title_filter.lower() not in show_title.lower():
                        continue
                    
                    # Get seasons for this show
                    seasons_url = f"{self.base_url}/library/metadata/{show_key}/children"
                    seasons_response = self.session.get(seasons_url, params=params, timeout=20)
                    seasons_response.raise_for_status()
                    
                    seasons_root = ET.fromstring(seasons_response.content)
                    seasons = seasons_root.findall('Directory')
                    
                    # For each season, get its episodes
                    for season in seasons:
                        season_key = season.get('ratingKey')
                        season_title = season.get('title')
                        season_index = season.get('index')
                        
                        # Skip seasons without valid rating key
                        if not season_key:
                            continue
                        
                        # Apply season filter if specified
                        if season_filter is not None and int(season_index) != season_filter:
                            continue
                        
                        # Get episodes for this season
                        episodes_url = f"{self.base_url}/library/metadata/{season_key}/children"
                        episodes_response = self.session.get(episodes_url, params=params, timeout=20)
                        episodes_response.raise_for_status()
                        
                        episodes_root = ET.fromstring(episodes_response.content)
                        episodes = episodes_root.findall('Video')
                        
                        # Process each episode
                        for episode in episodes:
                            rating_key = episode.get('ratingKey')
                            title = episode.get('title')
                            year = episode.get('year')
                            type_attr = episode.get('type')
                            episode_index = episode.get('index')
                            
                            # Apply episode filter if specified
                            if episode_filter is not None and int(episode_index) != episode_filter:
                                continue
                            
                            # Get file information
                            media = episode.find('Media')
                            file_path = None
                            file_size = None
                            duration = None
                            
                            if media is not None:
                                part = media.find('Part')
                                if part is not None:
                                    file_path = part.get('file')
                                    file_size = part.get('size')
                                duration = media.get('duration')
                            
                            if rating_key and title and file_path:
                                items.append({
                                    "ratingKey": rating_key,
                                    "title": title,
                                    "year": year,
                                    "type": type_attr,
                                    "file_path": file_path,
                                    "fileSize": file_size,
                                    "duration": duration,
                                    "updatedAt": episode.get('updatedAt'),
                                    "show_title": show_title,
                                    "season_title": season_title,
                                    "season_index": season_index,
                                    "episode_index": episode.get('index')
                                })
            else:
                # For movie libraries, get movies directly
                url = f"{self.base_url}/library/sections/{library_key}/all"
                response = self.session.get(url, params=params, timeout=20)
                response.raise_for_status()
                
                root = ET.fromstring(response.content)
                
                # Handle Video elements (movies)
                for video in root.findall('Video'):
                    rating_key = video.get('ratingKey')
                    title = video.get('title')
                    year = video.get('year')
                    type_attr = video.get('type')
                    
                    # Get file information
                    media = video.find('Media')
                    file_path = None
                    file_size = None
                    duration = None
                    
                    if media is not None:
                        part = media.find('Part')
                        if part is not None:
                            file_path = part.get('file')
                            file_size = part.get('size')
                        duration = media.get('duration')
                    
                    if rating_key and title and file_path:
                        items.append({
                            "ratingKey": rating_key,
                            "title": title,
                            "year": year,
                            "type": type_attr,
                            "file_path": file_path,
                            "fileSize": file_size,
                            "duration": duration,
                            "updatedAt": video.get('updatedAt')
                        })
            
            return items
            
        except requests.RequestException as e:
            raise ImporterError(f"Failed to fetch library items: {e}") from e
    
    def get_episode_metadata(self, rating_key: int) -> dict[str, Any]:
        """
        Get metadata for a specific episode by rating key.
        
        Args:
            rating_key: The Plex rating key for the episode
            
        Returns:
            Dictionary containing episode metadata
            
        Raises:
            ImporterError: If the request fails
        """
        try:
            url = f"{self.base_url}/library/metadata/{rating_key}"
            params = {"X-Plex-Token": self.token}
            
            response = self.session.get(url, params=params, timeout=20)
            response.raise_for_status()
            
            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            # Find the Video element
            video = root.find('Video')
            if video is None:
                raise ImporterError(f"No video found for rating key {rating_key}")
            
            # Extract metadata
            metadata = {
                "ratingKey": video.get('ratingKey'),
                "title": video.get('title'),
                "grandparentTitle": video.get('grandparentTitle'),
                "parentIndex": video.get('parentIndex'),
                "index": video.get('index'),
                "summary": video.get('summary'),
                "year": video.get('year'),
                "duration": video.get('duration'),
                "Media": []
            }
            
            # Extract Media information
            for media in video.findall('Media'):
                media_info = {
                    "duration": media.get('duration'),
                    "videoCodec": media.get('videoCodec'),
                    "audioCodec": media.get('audioCodec'),
                    "container": media.get('container'),
                    "Part": []
                }
                
                # Extract Part information
                for part in media.findall('Part'):
                    part_info = {
                        "file": part.get('file'),
                        "size": part.get('size'),
                        "duration": part.get('duration')
                    }
                    media_info["Part"].append(part_info)
                
                metadata["Media"].append(media_info)
            
            return metadata
            
        except requests.RequestException as e:
            raise ImporterError(f"Failed to fetch episode metadata: {e}") from e
    
    def find_episode_by_sse(self, series_title: str, season: int, episode: int) -> dict[str, Any]:
        """
        Find an episode by series title, season, and episode number.
        
        Args:
            series_title: The series title
            season: Season number
            episode: Episode number
            
        Returns:
            Episode metadata
            
        Raises:
            ImporterError: If episode not found or multiple matches
        """
        try:
            # Step 1: Find the series
            series_list = self.find_series_by_title(series_title)
            
            if not series_list:
                raise ImporterError(f"No series found matching '{series_title}'")
            
            # Try to find the best match if multiple results
            if len(series_list) > 1:
                # Look for exact title match first
                exact_matches = [s for s in series_list if s['title'].lower() == series_title.lower()]
                if exact_matches:
                    series = exact_matches[0]
                else:
                    # Look for partial matches
                    partial_matches = [s for s in series_list if series_title.lower() in s['title'].lower()]
                    if partial_matches:
                        series = partial_matches[0]
                    else:
                        titles = [s['title'] for s in series_list]
                        raise ImporterError(f"Multiple series found matching '{series_title}': {titles}. Please be more specific.")
            else:
                series = series_list[0]
            
            series_rating_key = int(series['ratingKey'])
            
            # Step 2: Get seasons for the series
            seasons = self.get_series_seasons(series_rating_key)
            
            # Find the requested season
            matching_seasons = [s for s in seasons if int(s.get('parentIndex', 0)) == season]
            
            if not matching_seasons:
                available_seasons = [int(s.get('parentIndex', 0)) for s in seasons]
                raise ImporterError(f"Season {season} not found for series '{series_title}'. Available seasons: {available_seasons}")
            
            if len(matching_seasons) > 1:
                # If multiple seasons with same number, prefer the one that's not a special/collection
                main_season = None
                for s in matching_seasons:
                    title = s.get('title', '').lower()
                    # Prefer seasons that don't have "special", "collection", "complete" in the title
                    if not any(word in title for word in ['special', 'collection', 'complete', 'box set']):
                        main_season = s
                        break
                
                if main_season:
                    matching_seasons = [main_season]
                else:
                    # If no clear main season, use the first one
                    matching_seasons = [matching_seasons[0]]
            
            season_data = matching_seasons[0]
            season_rating_key = int(season_data['ratingKey'])
            
            # Step 3: Get episodes for the season
            episodes = self.get_season_episodes(season_rating_key)
            
            # Find the requested episode
            matching_episodes = [e for e in episodes if int(e.get('index', 0)) == episode]
            
            if not matching_episodes:
                available_episodes = [int(e.get('index', 0)) for e in episodes]
                raise ImporterError(f"Episode {episode} not found in season {season} of '{series_title}'. Available episodes: {available_episodes}")
            
            if len(matching_episodes) > 1:
                raise ImporterError(f"Multiple episodes found with number {episode} in season {season} of '{series_title}'")
            
            episode_data = matching_episodes[0]
            return episode_data
            
        except requests.RequestException as e:
            raise ImporterError(f"Failed to find episode: {e}") from e
    
    def find_series_by_title(self, series_title: str) -> list[dict[str, Any]]:
        """
        Find series by title (case-insensitive search).
        
        Args:
            series_title: The series title to search for
            
        Returns:
            List of matching series
            
        Raises:
            ImporterError: If the request fails
        """
        try:
            # First try the global search without type restriction
            url = f"{self.base_url}/search"
            params = {
                "X-Plex-Token": self.token,
                "query": series_title
            }
            
            response = self.session.get(url, params=params, timeout=20)
            response.raise_for_status()
            
            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            series_list = []
            for video in root.findall('Video'):
                if video.get('type') == 'show':
                    series_info = {
                        "ratingKey": video.get('ratingKey'),
                        "title": video.get('title'),
                        "year": video.get('year'),
                        "summary": video.get('summary')
                    }
                    series_list.append(series_info)
            
            # If no results from global search, try searching in TV libraries
            if not series_list:
                series_list = self._search_in_tv_libraries(series_title)
            
            return series_list
            
        except requests.RequestException as e:
            raise ImporterError(f"Failed to search for series: {e}") from e
    
    def _search_in_tv_libraries(self, series_title: str) -> list[dict[str, Any]]:
        """
        Search for series in TV libraries if global search fails.
        
        Args:
            series_title: The series title to search for
            
        Returns:
            List of matching series
        """
        try:
            # Get all libraries first
            libraries = self.get_libraries()
            tv_libraries = [lib for lib in libraries if lib.get('type') == 'show']
            
            series_list = []
            for library in tv_libraries:
                try:
                    # Try browsing the library directly instead of searching
                    url = f"{self.base_url}/library/sections/{library['key']}/all"
                    params = {
                        "X-Plex-Token": self.token
                    }
                    
                    response = self.session.get(url, params=params, timeout=20)
                    response.raise_for_status()
                    
                    # Parse XML response
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.content)
                    
                    for directory in root.findall('Directory'):
                        if directory.get('type') == 'show':
                            title = directory.get('title', '')
                            # Check if this series matches our search (case-insensitive)
                            if series_title.lower() in title.lower():
                                series_info = {
                                    "ratingKey": directory.get('ratingKey'),
                                    "title": title,
                                    "year": directory.get('year'),
                                    "summary": directory.get('summary'),
                                    "library": library['title']
                                }
                                series_list.append(series_info)
                
                except Exception:
                    continue
            return series_list
            
        except Exception:
            return []
    
    def get_series_seasons(self, series_rating_key: int) -> list[dict[str, Any]]:
        """
        Get seasons for a series.
        
        Args:
            series_rating_key: The series rating key
            
        Returns:
            List of seasons
            
        Raises:
            ImporterError: If the request fails
        """
        try:
            url = f"{self.base_url}/library/metadata/{series_rating_key}/children"
            params = {"X-Plex-Token": self.token}
            
            response = self.session.get(url, params=params, timeout=20)
            response.raise_for_status()
            
            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            seasons = []
            for directory in root.findall('Directory'):
                if directory.get('type') == 'season':
                    seasons.append({
                        "ratingKey": directory.get('ratingKey'),
                        "title": directory.get('title'),
                        "parentIndex": directory.get('parentIndex'),
                        "index": directory.get('index')
                    })
            
            return seasons
            
        except requests.RequestException as e:
            raise ImporterError(f"Failed to fetch series seasons: {e}") from e
    
    def get_season_episodes(self, season_rating_key: int) -> list[dict[str, Any]]:
        """
        Get episodes for a season.
        
        Args:
            season_rating_key: The season rating key
            
        Returns:
            List of episodes
            
        Raises:
            ImporterError: If the request fails
        """
        try:
            url = f"{self.base_url}/library/metadata/{season_rating_key}/children"
            params = {"X-Plex-Token": self.token}
            
            response = self.session.get(url, params=params, timeout=20)
            response.raise_for_status()
            
            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            episodes = []
            for video in root.findall('Video'):
                if video.get('type') == 'episode':
                    episodes.append({
                        "ratingKey": video.get('ratingKey'),
                        "title": video.get('title'),
                        "grandparentTitle": video.get('grandparentTitle'),
                        "parentIndex": video.get('parentIndex'),
                        "index": video.get('index'),
                        "summary": video.get('summary'),
                        "year": video.get('year'),
                        "duration": video.get('duration'),
                        "Media": []
                    })
                    
                    # Extract Media information
                    for media in video.findall('Media'):
                        media_info = {
                            "duration": media.get('duration'),
                            "videoCodec": media.get('videoCodec'),
                            "audioCodec": media.get('audioCodec'),
                            "container": media.get('container'),
                            "bitrate": media.get('bitrate'),
                            "Part": []
                        }
                        
                        # Extract Part information
                        for part in media.findall('Part'):
                            part_info = {
                                "file": part.get('file'),
                                "size": part.get('size'),
                                "duration": part.get('duration')
                            }
                            media_info["Part"].append(part_info)
                        
                        episodes[-1]["Media"].append(media_info)
            
            return episodes
            
        except requests.RequestException as e:
            raise ImporterError(f"Failed to fetch season episodes: {e}") from e


class PlexImporter:
    """
    Plex importer plugin following the plugin contract.
    
    This importer connects to Plex servers and discovers content from their
    libraries, extracting metadata and file paths.
    """
    
    name = "plex"
    
    def __init__(self, base_url: str, token: str):
        """
        Initialize the Plex importer.
        
        Args:
            base_url: Plex server base URL
            token: Plex authentication token
        """
        self.base_url = base_url
        self.token = token
        self.client = PlexClient(base_url, token)
    
    def list_collections(self, source_config: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Return the collections (libraries) available in that source.
        
        Args:
            source_config: Source configuration (unused for Plex)
            
        Returns:
            List of collections with stable identifier, display name, source path, and filesystem locations
        """
        try:
            libraries = self.client.get_libraries()
            
            collections = []
            for lib in libraries:
                collections.append({
                    "external_id": lib["key"],
                    "name": lib["title"],
                    "type": lib.get("type", "unknown"),
                    "plex_section_ref": f"plex://{lib['key']}",
                    "locations": lib.get("locations", [])
                })
            
            return collections
            
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            raise ImporterError(f"Failed to list collections: {e}") from e
    
    def fetch_assets_for_collection(
        self, 
        source_config: dict[str, Any], 
        collection_descriptor: dict[str, Any], 
        local_path: str,
        title_filter: str = None,
        season_filter: int = None,
        episode_filter: int = None
    ) -> list[AssetDraft]:
        """
        Return AssetDraft objects for that collection.
        
        Args:
            source_config: Source configuration (unused for Plex)
            collection_descriptor: Collection information from list_collections
            local_path: Local path mapping for the collection
            
        Returns:
            List of AssetDraft objects representing media items
        """
        try:
            collection_id = collection_descriptor["id"]
            items = self.client.get_library_items(
                collection_id, 
                title_filter=title_filter,
                season_filter=season_filter,
                episode_filter=episode_filter
            )
            
            asset_drafts = []
            for item in items:
                try:
                    asset_draft = self._create_asset_draft(item, collection_descriptor, local_path)
                    if asset_draft:
                        asset_drafts.append(asset_draft)
                except Exception as e:
                    logger.warning(f"Failed to create asset draft for item {item.get('ratingKey', 'unknown')}: {e}")
                    continue
            
            return asset_drafts
            
        except Exception as e:
            logger.error(f"Failed to fetch assets for collection {collection_descriptor.get('name', 'unknown')}: {e}")
            raise ImporterError(f"Failed to fetch assets for collection: {e}") from e
    
    def _create_asset_draft(
        self, 
        item: dict[str, Any], 
        collection_descriptor: dict[str, Any], 
        local_path: str
    ) -> AssetDraft | None:
        """
        Create an AssetDraft from a Plex item.
        
        Args:
            item: Plex item information
            collection_descriptor: Collection information
            local_path: Local path mapping
            
        Returns:
            AssetDraft or None if creation fails
        """
        try:
            # Extract file path and map it to local path
            plex_file_path = item.get("file_path", "")
            if not plex_file_path:
                return None
            
            # Map Plex path to local path
            # This is a simple implementation - in production, you'd want more sophisticated path mapping
            local_file_path = plex_file_path
            if local_path and plex_file_path.startswith("/"):
                # Simple path replacement - in production, use proper path mapping service
                local_file_path = plex_file_path.replace("/", local_path + "/", 1)
            
            # Extract metadata
            title = item.get("title", "Unknown Title")
            year = item.get("year")
            duration = item.get("duration")
            file_size = item.get("fileSize")
            
            # Extract TV show hierarchy information
            series_title = item.get("show_title")
            season_number = item.get("season_index")
            episode_number = item.get("episode_index")
            episode_title = title  # For episodes, the title is the episode title
            
            # Create raw metadata
            raw_metadata = {
                "plex_rating_key": item.get("ratingKey"),
                "plex_type": item.get("type"),
                "plex_year": year,
                "plex_updated_at": item.get("updatedAt"),
                "collection_name": collection_descriptor.get("name"),
                "collection_type": collection_descriptor.get("type"),
                "show_title": series_title,
                "season_title": item.get("season_title"),
                "season_index": season_number,
                "episode_index": episode_number
            }
            
            # Create AssetDraft
            asset_draft = AssetDraft(
                uuid=uuid.uuid4(),
                file_path=local_file_path,
                title=episode_title,  # Use episode title as the main title
                duration_ms=int(duration) if duration else None,
                file_size=int(file_size) if file_size else None,
                source_type="plex",
                source_id=self.base_url,
                collection_id=collection_descriptor["id"],
                external_id=item.get("ratingKey"),
                raw_metadata=raw_metadata,
                discovered_at=datetime.utcnow(),
                # TV show hierarchy
                series_title=series_title,
                season_number=int(season_number) if season_number else None,
                episode_number=int(episode_number) if episode_number else None,
                episode_title=episode_title
            )
            
            return asset_draft
            
        except Exception as e:
            logger.warning(f"Failed to create asset draft: {e}")
            return None
    
    def get_parameter_spec(self) -> dict[str, Any]:
        """
        Get parameter specification for CLI help.
        
        Returns:
            Dictionary containing parameter specification
        """
        return {
            "description": "Connect to Plex Media Server instances and discover content from their libraries",
            "required_params": [
                {
                    "name": "base_url",
                    "type": "string",
                    "description": "Base URL for the Plex server (e.g., http://192.168.1.100:32400)"
                },
                {
                    "name": "token",
                    "type": "string", 
                    "description": "Plex authentication token"
                }
            ],
            "optional_params": [],
            "examples": [
                'retrovue source add --type plex --name "My Plex Server" --base-url "http://192.168.1.100:32400" --token "your-plex-token"'
            ],
            "cli_params": {
                "name": "Friendly name for the Plex server",
                "base_url": "Base URL for the Plex server (e.g., http://192.168.1.100:32400)",
                "token": "Plex authentication token"
            }
        }
