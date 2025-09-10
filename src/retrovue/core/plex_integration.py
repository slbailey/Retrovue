"""
Plex Integration for Retrovue v2

This module handles all interactions with Plex Media Server for content import and synchronization.
It provides comprehensive functionality for importing movies and TV shows with episode-level
granularity, intelligent sync operations, and progress tracking.

Key Features:
- Import movies and TV shows from Plex libraries
- Episode-level granularity for TV shows (each episode stored separately)
- Intelligent sync that only updates changed content
- Conflict resolution for content in multiple libraries
- Progress tracking with granular updates
- Stable GUID-based identification for reliable sync
- Support for multiple library types (movies, shows)

Architecture:
- PlexImporter: Main class for Plex API interactions
- Sync operations: Compare Plex content with database and update only changes
- Progress callbacks: Real-time progress updates for UI
- Error handling: Robust error handling with detailed logging

Database Integration:
- Stores media files with proper metadata
- Links episodes to their parent shows
- Maintains source tracking for sync operations
- Handles library name storage as media file attributes

Usage:
    importer = PlexImporter(server_url, token, database, status_callback)
    importer.sync_all_libraries()  # Sync all libraries
    importer.import_all_libraries()  # Full import (legacy)
"""

import requests
from typing import List, Dict, Optional, Any
from .database import RetrovueDatabase
from .path_mapping import PlexPathMappingService
from .guid_parser import GUIDParser, extract_guids_from_plex_metadata, get_show_disambiguation_key, format_show_for_display


class PlexImporter:
    """
    Handles importing content from Plex Media Server.
    """
    
    def __init__(self, server_url: str, token: str, database: RetrovueDatabase, status_callback=None):
        """
        Initialize the Plex importer.
        
        Args:
            server_url: Plex server URL
            token: Plex authentication token
            database: Database instance for storing imported content
            status_callback: Optional callback function for status updates
        """
        self.server_url = server_url.rstrip('/')
        self.token = token
        self.database = database
        self.status_callback = status_callback
        self.headers = {
            'X-Plex-Token': token,
            'Accept': 'application/json'
        }
        
        # Initialize path mapping service
        self.path_mapping_service = PlexPathMappingService.create_from_database(database)
    
    def _emit_status(self, message: str):
        """Emit status message via callback"""
        if self.status_callback:
            self.status_callback(message)
    
    def test_connection(self) -> bool:
        """Test connection to Plex server"""
        try:
            url = f"{self.server_url}/status/sessions"
            response = requests.get(url, headers=self.headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            return False
    
    def get_libraries(self) -> List[Dict]:
        """Get all libraries from Plex server"""
        try:
            url = f"{self.server_url}/library/sections"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            libraries = []
            
            for section in data.get('MediaContainer', {}).get('Directory', []):
                libraries.append({
                    'key': section.get('key'),
                    'title': section.get('title'),
                    'type': section.get('type'),
                    'agent': section.get('agent')
                })
            
            return libraries
        except Exception as e:
            return []
    
    def get_library_items(self, library_key: str, library_type: str) -> List[Dict]:
        """Get all items from a specific library"""
        try:
            url = f"{self.server_url}/library/sections/{library_key}/all"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get('MediaContainer', {}).get('Metadata', [])
        except Exception as e:
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
            
            response = requests.get(url, headers=self.headers, params=params)
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
    
    def get_library_episode_count(self, section_key: str) -> int:
        """Get total episode count for a library section using allLeaves endpoint"""
        try:
            all_leaves_url = f"{self.server_url}/library/sections/{section_key}/allLeaves"
            response = requests.get(all_leaves_url, headers=self.headers)
            response.raise_for_status()
            
            episodes_data = response.json()
            media_container = episodes_data.get('MediaContainer', {})
            total_episodes = media_container.get('size', 0)
            
            return total_episodes
        except Exception as e:
            self._emit_status(f"❌ Error getting episode count: {e}")
            return 0
    
    def get_show_episodes(self, show_key: str) -> List[Dict]:
        """Get all episodes for a specific show using allLeaves endpoint"""
        try:
            # Use allLeaves endpoint to get all episodes directly
            all_leaves_url = f"{self.server_url}{show_key}/allLeaves"
            response = requests.get(all_leaves_url, headers=self.headers)
            response.raise_for_status()
            
            episodes_data = response.json()
            episodes = episodes_data.get('MediaContainer', {}).get('Metadata', [])
            
            return episodes
        except Exception as e:
            # Fallback to the old method if allLeaves fails
            try:
                # First get seasons, then get episodes from each season
                seasons_url = f"{self.server_url}{show_key}"
                response = requests.get(seasons_url, headers=self.headers)
                response.raise_for_status()
                
                seasons_data = response.json()
                seasons = seasons_data.get('MediaContainer', {}).get('Metadata', [])
                
                all_episodes = []
                
                # Get episodes from each season
                for season in seasons:
                    season_key = season.get('key', '')
                    if season_key:
                        # Get episodes from this season
                        episodes_url = f"{self.server_url}{season_key}"
                        episodes_response = requests.get(episodes_url, headers=self.headers)
                        episodes_response.raise_for_status()
                        
                        episodes_data = episodes_response.json()
                        episodes = episodes_data.get('MediaContainer', {}).get('Metadata', [])
                        all_episodes.extend(episodes)
                
                return all_episodes
            except Exception as e2:
                return []
    
    def _map_plex_rating(self, plex_rating: str) -> str:
        """Map Plex rating to standard rating"""
        rating_map = {
            'G': 'G',
            'PG': 'PG',
            'PG-13': 'PG-13',
            'R': 'R',
            'NC-17': 'Adult',
            'Not Rated': 'PG-13',
            'TV-G': 'G',
            'TV-PG': 'PG',
            'TV-14': 'PG-13',
            'TV-MA': 'Adult'
        }
        return rating_map.get(plex_rating, 'PG-13')
    
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
    
    def get_local_path(self, plex_path: str) -> str:
        """Get the local mapped path for a Plex path (for file access)"""
        return self.path_mapping_service.get_local_path(plex_path)
    
    def import_movie(self, item: Dict, library_name: str = None) -> bool:
        """Import a single movie"""
        try:
            # Extract basic information
            title = item.get('title', 'Unknown Title')
            plex_guid = item.get('guid', '')  # Use stable GUID instead of key
            
            # Get duration and file path from Media array
            media_array = item.get('Media', [])
            file_path = self._get_file_path_from_media(media_array)
            duration = self._get_duration_from_media(media_array)
            
            if not duration:
                return False
            
            # Get rating
            plex_rating = item.get('contentRating', '')
            content_rating = self._map_plex_rating(plex_rating)
            
            # Add media file to database
            media_file_id = self.database.add_media_file(
                file_path=file_path,
                duration=duration,
                media_type='movie',
                source_type='plex',
                source_id=plex_guid,
                library_name=library_name
            )
            
            # Add movie metadata
            self.database.add_movie(
                media_file_id=media_file_id,
                title=title,
                year=item.get('year'),
                rating=content_rating,
                summary=item.get('summary', ''),
                genre=', '.join([g.get('tag', '') for g in item.get('Genre', [])]),
                director=', '.join([d.get('tag', '') for d in item.get('Director', [])])
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
            return False
    
    def import_show_episodes(self, show: Dict) -> int:
        """Import all episodes from a show with year-based disambiguation"""
        try:
            show_title = show.get('title', 'Unknown Show')
            show_key = show.get('key', '')
            show_rating_key = show.get('ratingKey', '')
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
                plex_rating_key=show_rating_key,
                year=show_year,
                total_seasons=show.get('leafCount', 0),
                total_episodes=len(episodes),
                show_rating=self._map_plex_rating(show.get('contentRating', '')),
                show_summary=show.get('summary', ''),
                genre=', '.join([g.get('tag', '') for g in show.get('Genre', [])]),
                studio=show.get('studio', ''),
                originally_available_at=show.get('originallyAvailableAt'),
                guid_primary=primary_guid,
                updated_at_plex=show.get('updatedAt'),
                source_type='plex',
                source_id=show_rating_key  # Use rating key as source ID
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
                    file_path = self._get_file_path_from_media(media_array)
                    duration = self._get_duration_from_media(media_array)
                    
                    if not duration:
                        continue
                    
                    # Get rating
                    plex_rating = episode.get('contentRating', '')
                    content_rating = self._map_plex_rating(plex_rating)
                    
                    # Add media file to database
                    media_file_id = self.database.add_media_file(
                        file_path=file_path,
                        duration=duration,
                        media_type='episode',
                        source_type='plex',
                        source_id=episode_guid  # Use stable GUID
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
                        summary=episode.get('summary', '')
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
                    continue
            
            self._emit_status(f"🎉 Imported {imported_count} episodes from show: {show_title}")
            return imported_count
            
        except Exception as e:
            return 0
    
    def import_library(self, library_key: str, library_type: str) -> int:
        """Import all content from a specific library"""
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
            return self._sync_movie_library(library_key)
        elif library_type == 'show':
            return self._sync_show_library(library_key)
        else:
            return {'updated': 0, 'added': 0, 'removed': 0}
    
    def _import_movie_library(self, library_key: str, library_name: str = None) -> int:
        """Import all movies from a movie library"""
        movies = self.get_library_items(library_key, 'movie')
        imported_count = 0
        
        for movie in movies:
            if self.import_movie(movie, library_name):
                imported_count += 1
        
        return imported_count
    
    def _sync_movie_library(self, library_key: str, library_name: str = None, progress_callback=None) -> Dict[str, int]:
        """Sync a movie library with Plex"""
        # Get current movies from Plex
        plex_movies = self.get_library_items(library_key, 'movie')
        plex_movie_ids = {movie.get('guid', '') for movie in plex_movies}  # Use stable GUID
        
        # Get current movies from database for this library
        db_movies = self.database.get_movies_by_source('plex')
        db_movie_ids = {movie['source_id'] for movie in db_movies if movie['source_id']}
        
        updated_count = 0
        added_count = 0
        removed_count = 0
        
        # Update existing and add new movies
        for i, movie in enumerate(plex_movies):
            movie_guid = movie.get('guid', '')  # Use stable GUID
            if movie_guid in db_movie_ids:
                # Check if movie already has a library name (processed by another library)
                db_movie = self.database.get_movie_by_source_id(movie_guid)
                if db_movie and db_movie.get('library_name'):
                    # Movie already processed by another library, skip to avoid conflicts
                    continue
                
                # Update existing movie (only count if there were actual changes)
                if self._update_movie(movie, library_name):
                    updated_count += 1
            else:
                # Add new movie
                if self.import_movie(movie, library_name):
                    added_count += 1
            
            # Emit progress for each movie processed
            if progress_callback:
                progress_callback(i + 1, len(plex_movies), f"Processing movie {i+1}/{len(plex_movies)}: {movie.get('title', 'Unknown')}")
        
        # NOTE: We don't remove movies here because this is per-library sync
        # Removal should be handled at the global level after all libraries are processed
        
        return {'updated': updated_count, 'added': added_count, 'removed': removed_count}
    
    def sync_all_libraries(self, progress_callback=None) -> Dict[str, int]:
        """Sync all libraries and remove orphaned content"""
        libraries = self.get_libraries()
        total_updated = 0
        total_added = 0
        total_removed = 0
        
        # Process each library with dual progress tracking
        for i, library in enumerate(libraries):
            library_key = library.get('key', '')
            library_type = library.get('type', 'movie')
            library_name = library.get('title', 'Unknown Library')
            
            # Emit library progress: current library / total libraries
            if progress_callback:
                progress_callback(
                    library_progress=(i, len(libraries), library_name),
                    item_progress=None,
                    message=None  # No status message for library processing
                )
            
            if library_type == 'movie':
                # Get all movies from this library
                plex_movies = self.get_library_items(library_key, 'movie')
                
                # Process each movie individually with item progress
                for j, movie in enumerate(plex_movies):
                    movie_guid = movie.get('guid', '')
                    movie_title = movie.get('title', 'Unknown Movie')
                    
                    # Check if movie exists in database
                    db_movies = self.database.get_movies_by_source('plex')
                    db_movie_ids = {movie['source_id'] for movie in db_movies if movie['source_id']}
                    
                    if movie_guid in db_movie_ids:
                        # Check if movie already has a library name (processed by another library)
                        db_movie = self.database.get_movie_by_source_id(movie_guid)
                        if db_movie and db_movie.get('library_name'):
                            # Movie already processed by another library, skip to avoid conflicts
                            action = None  # No output for ignored items
                        else:
                            # Update existing movie
                            if self._update_movie(movie, library_name):
                                total_updated += 1
                                action = f"Updated movie: {movie_title}"
                            else:
                                action = None  # No output for no changes
                    else:
                        # Add new movie
                        if self.import_movie(movie, library_name):
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
                # Get all shows from this library
                plex_shows = self.get_library_items(library_key, 'show')
                
                # Process each show individually (which processes all its episodes)
                for j, show in enumerate(plex_shows):
                    show_guid = show.get('guid', '')
                    show_title = show.get('title', 'Unknown Show')
                    
                    # Process this show and all its episodes
                    episode_count = self._sync_show_episodes(
                        show, 
                        progress_callback, 
                        library_progress=(i, len(libraries), library_name), 
                        library_name=library_name
                    )
                    total_updated += episode_count
        
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
        
        # Remove orphaned movies (not in any Plex library)
        if progress_callback:
            progress_callback(
                library_progress=(len(libraries), len(libraries), "Cleanup"),
                item_progress=None,
                message=None  # No status message for cleanup
            )
        db_movies = self.database.get_movies_by_source('plex')
        for db_movie in db_movies:
            if db_movie['source_id'] and db_movie['source_id'] not in all_plex_movie_ids:
                if self.database.remove_movie_by_source_id(db_movie['source_id']):
                    total_removed += 1
        
        # Remove orphaned shows (not in any Plex library)
        if progress_callback:
            progress_callback(
                library_progress=(len(libraries), len(libraries), "Cleanup"),
                item_progress=None,
                message=None  # No status message for cleanup
            )
        db_shows = self.database.get_shows_by_source('plex')
        for db_show in db_shows:
            if db_show['source_id'] and db_show['source_id'] not in all_plex_show_ids:
                if self.database.remove_show_by_source_id(db_show['source_id']):
                    total_removed += 1
        
        # Final progress callback
        if progress_callback:
            progress_callback(
                library_progress=(len(libraries), len(libraries), "Complete"),
                item_progress=None,
                message=f"🎉 Sync completed! Added: {total_added}, Updated: {total_updated}, Removed: {total_removed}"
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
    
    def _sync_show_library(self, library_key: str, progress_callback=None) -> Dict[str, int]:
        """Sync a show library with Plex"""
        # Get current shows from Plex
        plex_shows = self.get_library_items(library_key, 'show')
        plex_show_ids = {show.get('guid', '') for show in plex_shows}  # Use stable GUID
        
        # Get current shows from database for this library
        db_shows = self.database.get_shows_by_source('plex')
        db_show_ids = {show['source_id'] for show in db_shows if show['source_id']}
        
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
                # Update existing show and its episodes
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
                    source_id=show_guid
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
            show_rating_key = show['ratingKey']
            show_title = show['title']
            show_year = show['year']
            
            # Check if show already exists in database
            existing_show = self.database.get_show_by_plex_rating_key(show_rating_key)
            
            if existing_show:
                # Update existing show
                self._emit_status(f"🔄 Updating existing show: {show['display_name']}")
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
    
    def _update_movie(self, movie: Dict, library_name: str = None) -> bool:
        """Update an existing movie with current Plex data"""
        try:
            movie_guid = movie.get('guid', '')  # Use stable GUID
            if not movie_guid:
                return False
            
            # Get current movie from database
            db_movie = self.database.get_movie_by_source_id(movie_guid)
            if not db_movie:
                return False
            
            # Update movie data
            title = movie.get('title', 'Unknown Movie')
            year = movie.get('year')
            rating = self._map_plex_rating(movie.get('contentRating', ''))
            summary = movie.get('summary', '')
            genre = ', '.join([g.get('tag', '') for g in movie.get('Genre', [])])
            director = ', '.join([d.get('tag', '') for d in movie.get('Director', [])])
            
            # Get duration and file path from Media array
            media_array = movie.get('Media', [])
            file_path = self._get_file_path_from_media(media_array)
            duration = self._get_duration_from_media(media_array)
            
            if not duration:
                return False
            
            # Check if anything has actually changed
            has_changes = False
            
            # Check media file changes
            if (db_movie.get('file_path') != file_path or 
                db_movie.get('duration') != duration or
                db_movie.get('library_name') != library_name):
                has_changes = True
                self.database.update_media_file(
                    media_file_id=db_movie['media_file_id'],
                    file_path=file_path,
                    duration=duration,
                    library_name=library_name
                )
            
            # Check movie metadata changes
            if (db_movie.get('title') != title or 
                db_movie.get('year') != year or 
                db_movie.get('rating') != rating or 
                db_movie.get('summary') != summary or 
                db_movie.get('genre') != genre or 
                db_movie.get('director') != director):
                has_changes = True
                self.database.update_movie(
                    movie_id=db_movie['id'],
                    title=title,
                    year=year,
                    rating=rating,
                    summary=summary,
                    genre=genre,
                    director=director
                )
            
            # Only output if there were actual changes
            if has_changes:
                # Format duration for display (convert milliseconds to hh:mm:ss.ff)
                duration_seconds = duration / 1000.0
                hours = int(duration_seconds // 3600)
                minutes = int((duration_seconds % 3600) // 60)
                seconds = int(duration_seconds % 60)
                fractional_seconds = int((duration_seconds % 1) * 100)
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{fractional_seconds:02d}"
                
                self._emit_status(f"✅ Updated movie: {title} ({rating}) - {duration_str}")
            
            return has_changes
            
        except Exception as e:
            return False
    
    def _sync_show_episodes(self, show: Dict, progress_callback=None, library_progress=None, library_name: str = None) -> int:
        """Sync episodes for an existing show"""
        try:
            show_title = show.get('title', 'Unknown Show')
            show_key = show.get('key', '')
            show_guid = show.get('guid', '')  # Use stable GUID
            
            # Get current episodes from Plex
            plex_episodes = self.get_show_episodes(show_key)
            plex_episode_ids = {episode.get('guid', '') for episode in plex_episodes}  # Use stable GUID
            
            # Get current episodes from database for this show
            db_episodes = self.database.get_episodes_by_show_source_id(show_guid)  # Use stable GUID
            db_episode_ids = {episode['source_id'] for episode in db_episodes if episode['source_id']}
            
            updated_count = 0
            added_count = 0
            removed_count = 0
            
            # Update existing and add new episodes
            for i, episode in enumerate(plex_episodes):
                episode_guid = episode.get('guid', '')  # Use stable GUID
                episode_title = episode.get('title', 'Unknown Episode')
                
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
                    # Update existing episode (only count if there were actual changes)
                    if self._update_episode(episode, show, library_name):
                        updated_count += 1
                        # Emit status message for database change
                        if progress_callback:
                            progress_callback(
                                library_progress=library_progress,
                                item_progress=(i + 1, len(plex_episodes), show_episode_display),
                                message=f"Updated episode: {episode_title}"
                            )
                else:
                    # Add new episode
                    if self._add_episode(episode, show, library_name):
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
            
            # No summary messages - just progress bars
            
            # Return the number of episodes processed (not just changes)
            return len(plex_episodes)
            
        except Exception as e:
            return 0
    
    def _update_episode(self, episode: Dict, show: Dict, library_name: str = None) -> bool:
        """Update an existing episode with current Plex data"""
        try:
            episode_guid = episode.get('guid', '')  # Use stable GUID
            if not episode_guid:
                return False
            
            # Get current episode from database
            db_episode = self.database.get_episode_by_source_id(episode_guid)
            if not db_episode:
                return False
            
            # Update episode data
            episode_title = episode.get('title', 'Unknown Episode')
            # Convert to integers to match database storage
            season_number = int(episode.get('parentIndex', 0)) if episode.get('parentIndex') is not None else 0
            episode_number = int(episode.get('index', 0)) if episode.get('index') is not None else 0
            rating = self._map_plex_rating(episode.get('contentRating', ''))
            summary = episode.get('summary', '')
            
            # Get duration and file path from Media array
            media_array = episode.get('Media', [])
            file_path = self._get_file_path_from_media(media_array)
            duration = self._get_duration_from_media(media_array)
            
            if not duration:
                return False
            
            # Check if anything has actually changed
            has_changes = False
            
            # Check media file changes
            # Only update library_name if it's currently NULL (first-time assignment)
            library_name_changed = (db_episode.get('library_name') is None and library_name is not None)
            
            # Check for file path or duration changes (these are legitimate updates)
            file_path_changed = (db_episode.get('file_path') != file_path)
            duration_changed = (db_episode.get('duration') != duration)
            
            if (file_path_changed or duration_changed or library_name_changed):
                # Update the media file data
                update_library_name = library_name if library_name_changed else db_episode.get('library_name')
                self.database.update_media_file(
                    media_file_id=db_episode['media_file_id'],
                    file_path=file_path,
                    duration=duration,
                    library_name=update_library_name
                )
                
                # Only count as "changes" if it's not just a file path change
                # File path changes are often due to library reorganization and shouldn't be treated as major updates
                if duration_changed or library_name_changed:
                    has_changes = True
            
            # Check episode metadata changes - ensure proper type comparison
            if (db_episode.get('episode_title') != episode_title or 
                db_episode.get('season_number') != season_number or 
                db_episode.get('episode_number') != episode_number or 
                db_episode.get('rating') != rating or 
                db_episode.get('summary') != summary):
                has_changes = True
                self.database.update_episode(
                    episode_id=db_episode['id'],
                    episode_title=episode_title,
                    season_number=season_number,
                    episode_number=episode_number,
                    rating=rating,
                    summary=summary
                )
            
            # Only output if there were actual changes
            return has_changes
            
        except Exception as e:
            return False
    
    def _add_episode(self, episode: Dict, show: Dict, library_name: str = None) -> bool:
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
                        total_seasons=show.get('leafCount', 0),
                        total_episodes=0,  # Will be updated as episodes are added
                        show_rating=self._map_plex_rating(show.get('contentRating', '')),
                        show_summary=show.get('summary', ''),
                        genre=', '.join([g.get('tag', '') for g in show.get('Genre', [])]),
                        source_type='plex',
                        source_id=show_guid
                    )
                    # Get the show record we just created
                    cursor.execute("SELECT * FROM shows WHERE source_id = ?", (show_guid,))
                    db_show = cursor.fetchone()
                    if db_show:
                        db_show = dict(db_show)
                    if not db_show:
                        return False
                except Exception as e:
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
            file_path = self._get_file_path_from_media(media_array)
            duration = self._get_duration_from_media(media_array)
            
            if not duration:
                return False
            
            # Add media file
            media_file_id = self.database.add_media_file(
                file_path=file_path,
                duration=duration,
                media_type='episode',
                source_type='plex',
                source_id=episode_guid,  # Use stable GUID
                library_name=library_name
            )
            
            # Add episode
            self.database.add_episode(
                media_file_id=media_file_id,
                show_id=db_show['id'],
                episode_title=episode_title,
                season_number=season_number,
                episode_number=episode_number,
                rating=rating,
                summary=summary
            )
            
            return True
            
        except Exception as e:
            return False
    
    def import_all_libraries(self) -> int:
        """Import all libraries from Plex server"""
        libraries = self.get_libraries()
        total_imported = 0
        
        for library in libraries:
            library_key = library.get('key', '')
            library_title = library.get('title', 'Unknown Library')
            library_type = library.get('type', 'movie')
            
            count = self.import_library(library_key, library_type)
            total_imported += count
        
        return total_imported


def create_plex_importer(server_url: str, token: str, database: RetrovueDatabase, status_callback=None) -> Optional[PlexImporter]:
    """
    Create a Plex importer instance and test the connection.
    
    Args:
        server_url: Plex server URL
        token: Plex authentication token
        database: Database instance
        status_callback: Optional callback function for status updates
        
    Returns:
        PlexImporter instance if connection successful, None otherwise
    """
    importer = PlexImporter(server_url, token, database, status_callback)
    
    if importer.test_connection():
        importer._emit_status(f"✅ Connected to Plex server: {server_url}")
        return importer
    else:
        return None
