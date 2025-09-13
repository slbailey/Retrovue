"""
Mapper for converting Plex JSON to domain models.

Converts Plex items to ContentItemData, MediaFileData (typed dataclasses).
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .guid import GuidParser, ParsedGuid

logger = logging.getLogger("retrovue.plex")


@dataclass
class ContentItemData:
    """Data class for content items."""
    kind: str  # 'movie', 'episode', 'interstitial', etc.
    title: str
    synopsis: Optional[str] = None
    duration_ms: Optional[int] = None
    rating_system: Optional[str] = None
    rating_code: Optional[str] = None
    is_kids_friendly: int = 0
    show_title: Optional[str] = None
    season_number: Optional[int] = None
    episode_number: Optional[int] = None
    metadata_updated_at: Optional[int] = None  # epoch secs


@dataclass
class MediaFileData:
    """Data class for media files."""
    plex_rating_key: str
    file_path: str
    size_bytes: Optional[int] = None
    container: Optional[str] = None
    video_codec: Optional[str] = None
    audio_codec: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    bitrate: Optional[int] = None
    frame_rate: Optional[float] = None
    channels: Optional[int] = None
    updated_at_plex: Optional[int] = None


@dataclass
class EditorialData:
    """Represents editorial metadata."""
    source_name: str                 # 'plex'
    source_payload_json: str         # full compact JSON of the Plex item
    original_title: Optional[str]
    original_synopsis: Optional[str]


@dataclass
class TagRow:
    """Represents a content tag."""
    namespace: str                   # e.g., 'rating' | 'audience'
    key: str                         # e.g., 'system' | 'code' | 'kids'
    value: str                       # 'TV' | 'TV-PG' | '1'


class Mapper:
    """Maps Plex items to domain models."""
    
    def __init__(self):
        """Initialize mapper."""
        self.guid_parser = GuidParser()
    
    def map_from_json(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map a Plex item to basic summary (for CLI compatibility).
        
        Args:
            item: Plex item dictionary
            
        Returns:
            Dictionary with basic item information
        """
        result = {
            "title": item.get("title", "Unknown"),
            "kind": item.get("type", "unknown"),
            "duration_ms": item.get("duration"),
            "rating": item.get("contentRating"),
            "year": item.get("year"),
            "summary": item.get("summary")
        }
        
        # Handle GUIDs
        if "guid" in item:
            result["guid"] = item["guid"]
        elif "Guid" in item:
            # Handle list format
            if isinstance(item["Guid"], list) and item["Guid"]:
                result["guid"] = item["Guid"][0].get("id", "")
        
        # Handle episode-specific fields
        if result["kind"] == "episode":
            result["season"] = item.get("parentIndex")
            result["episode"] = item.get("index")
            result["show_title"] = item.get("grandparentTitle")
        
        return result
    
    def map_plex_item(
        self, 
        item: Dict[str, Any], 
        server_id: int, 
        library_id: int,
        show_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> Tuple[ContentItemData, List[MediaFileData], Dict[str, Any], List[Dict[str, Any]]]:
        """
        Map a Plex item to domain models.
        
        Args:
            item: Plex item dictionary
            server_id: Server ID
            library_id: Library ID
            show_id: Optional show ID (for episodes)
            season_id: Optional season ID (for episodes)
            
        Returns:
            Tuple of (ContentItemData, List[MediaFileData], editorial_data, tags)
        """
        logger.debug(f"Mapping Plex item: {item.get('title', 'Unknown')}")
        
        # Parse GUIDs
        parsed_guid = self.guid_parser.parse_plex_item(item)
        
        # Determine content kind
        kind = self._infer_kind(item)
        
        # Map content item
        content_item = self._map_content_item(item, parsed_guid, kind, show_id, season_id)
        
        # Map media files
        media_files = self._map_media_files(item)
        
        # Map editorial data
        editorial = self._map_editorial(item)
        
        # Map tags
        tags = self._map_tags(item)
        
        return content_item, media_files, editorial, tags
    
    def _infer_kind(self, item: Dict[str, Any]) -> str:
        """
        Infer content kind from Plex item.
        
        Args:
            item: Plex item dictionary
            
        Returns:
            Content kind string
        """
        # Check type field first
        item_type = item.get('type', '').lower()
        
        if item_type == 'movie':
            return 'movie'
        elif item_type == 'episode':
            return 'episode'
        elif item_type == 'show':
            return 'show'
        elif item_type == 'season':
            return 'season'
        
        # Check for episode-specific fields
        if 'parentRatingKey' in item and 'index' in item:
            return 'episode'
        
        # Check for movie-specific fields
        if 'viewCount' in item and 'parentRatingKey' not in item:
            return 'movie'
        
        # Default fallback
        return 'unknown'
    
    def _map_content_item(
        self, 
        item: Dict[str, Any], 
        parsed_guid: ParsedGuid, 
        kind: str,
        show_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> ContentItemData:
        """
        Map Plex item to ContentItemData.
        
        Args:
            item: Plex item dictionary
            parsed_guid: Parsed GUID information
            kind: Content kind
            show_id: Optional show ID
            season_id: Optional season ID
            
        Returns:
            ContentItemData object
        """
        # Parse rating information
        content_rating = item.get('contentRating', '')
        rating_system, rating_code = self.guid_parser.normalize_rating_system(content_rating)
        is_kids_friendly = 1 if self.guid_parser.infer_kids_friendly(content_rating) else 0
        
        # Get episode/season numbers
        season_number = None
        episode_number = None
        show_title = None
        if kind == 'episode':
            season_number = item.get('parentIndex')
            episode_number = item.get('index')
            show_title = item.get('grandparentTitle')
        
        # Get metadata updated timestamp
        metadata_updated_at = None
        if 'updatedAt' in item:
            try:
                metadata_updated_at = int(item['updatedAt'])
            except (ValueError, TypeError):
                pass
        
        return ContentItemData(
            kind=kind,
            title=item.get('title', 'Unknown'),
            synopsis=item.get('summary'),
            duration_ms=item.get('duration'),
            rating_system=rating_system,
            rating_code=rating_code,
            is_kids_friendly=is_kids_friendly,
            show_title=show_title,
            season_number=season_number,
            episode_number=episode_number,
            metadata_updated_at=metadata_updated_at
        )
    
    def _map_media_files(self, item: Dict[str, Any]) -> List[MediaFileData]:
        """
        Map Plex item media to MediaFileData list.
        
        Args:
            item: Plex item dictionary
            
        Returns:
            List of MediaFileData objects
        """
        media_files = []
        
        # Get media information
        media_list = item.get('Media', [])
        if not media_list:
            logger.warning(f"No media found for item: {item.get('title', 'Unknown')}")
            return media_files
        
        for media in media_list:
            # Get parts
            parts = media.get('Part', [])
            if not parts:
                continue
            
            for part in parts:
                # Get file path
                file_path = part.get('file', '')
                if not file_path:
                    continue
                
                # Get file size
                size_bytes = None
                if 'size' in part:
                    try:
                        size_bytes = int(part['size'])
                    except (ValueError, TypeError):
                        pass
                
                # Get container format
                container = part.get('container', '')
                
                # Get video information
                video_codec = media.get('videoCodec', '')
                width = media.get('width')
                height = media.get('height')
                bitrate = media.get('bitrate')
                frame_rate = media.get('videoFrameRate')
                
                # Get audio information
                audio_codec = media.get('audioCodec', '')
                channels = media.get('audioChannels')
                
                # Get Plex updated timestamp
                updated_at_plex = None
                if 'updatedAt' in item:
                    try:
                        updated_at_plex = int(item['updatedAt'])
                    except (ValueError, TypeError):
                        pass
                
                media_file = MediaFileData(
                    plex_rating_key=item.get('ratingKey', ''),
                    file_path=file_path,
                    size_bytes=size_bytes,
                    container=container,
                    video_codec=video_codec,
                    audio_codec=audio_codec,
                    width=width,
                    height=height,
                    bitrate=bitrate,
                    frame_rate=frame_rate,
                    channels=channels,
                    updated_at_plex=updated_at_plex
                )
                
                media_files.append(media_file)
        
        return media_files
    
    def _map_editorial(self, item: Dict[str, Any]) -> EditorialData:
        """
        Map Plex item to editorial data.
        
        Args:
            item: Plex item dictionary
            
        Returns:
            EditorialData object
        """
        import json
        
        # Serialize the entire item as source payload
        source_payload_json = json.dumps(item, default=str, separators=(',', ':'))
        
        return EditorialData(
            source_name='plex',
            source_payload_json=source_payload_json,
            original_title=item.get('title'),
            original_synopsis=item.get('summary')
        )
    
    def _map_tags(self, item: Dict[str, Any]) -> List[TagRow]:
        """
        Map Plex item to tags.
        
        Args:
            item: Plex item dictionary
            
        Returns:
            List of TagRow objects
        """
        tags = []
        
        # Map rating to tags
        content_rating = item.get('contentRating', '')
        if content_rating:
            rating_system, rating_code = self.guid_parser.normalize_rating_system(content_rating)
            if rating_system:
                tags.append(TagRow('rating', 'system', rating_system))
            if rating_code:
                tags.append(TagRow('rating', 'code', rating_code))
        
        # Map kids-friendly flag
        is_kids_friendly = self.guid_parser.infer_kids_friendly(content_rating)
        if is_kids_friendly:
            tags.append(TagRow('audience', 'kids', '1'))
        
        # Map genres
        genres = item.get('Genre', [])
        for genre in genres:
            if isinstance(genre, dict) and 'tag' in genre:
                tags.append(TagRow('genre', 'primary', genre['tag']))
        
        # Map studios
        studios = item.get('Studio', [])
        for studio in studios:
            if isinstance(studio, dict) and 'tag' in studio:
                tags.append(TagRow('studio', 'primary', studio['tag']))
        
        return tags