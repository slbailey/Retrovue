"""
GUID parser for normalizing Plex GUIDs.

Parses and normalizes Plex GUIDs to extract imdb/tmdb/tvdb/plex identifiers.
"""

import re
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger("retrovue.plex")


@dataclass
class ParsedGuid:
    """Parsed GUID information."""
    plex: Optional[str] = None
    imdb: Optional[str] = None
    tmdb: Optional[str] = None
    tvdb: Optional[str] = None
    raw: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert to dictionary."""
        return {
            "plex": self.plex,
            "imdb": self.imdb,
            "tmdb": self.tmdb,
            "tvdb": self.tvdb,
            "raw": self.raw
        }
    
    def get_primary(self) -> Optional[str]:
        """Get primary GUID (prefer TVDB > TMDB > IMDB > Plex)."""
        if self.tvdb:
            return f"tvdb://{self.tvdb}"
        elif self.tmdb:
            return f"tmdb://{self.tmdb}"
        elif self.imdb:
            return f"imdb://{self.imdb}"
        elif self.plex:
            return f"plex://{self.plex}"
        return None


class GuidParser:
    """Parser for Plex GUIDs."""
    
    # Regex patterns for different GUID formats
    PATTERNS = {
        'imdb': re.compile(r'imdb://tt(\d+)'),
        'tmdb': re.compile(r'tmdb://(\d+)'),
        'tvdb': re.compile(r'tvdb://(\d+)'),
        'plex': re.compile(r'plex://([^/]+)'),
        'plex_show': re.compile(r'plex://show/([^/]+)'),
        'plex_movie': re.compile(r'plex://movie/([^/]+)'),
        'plex_episode': re.compile(r'plex://episode/([^/]+)'),
    }
    
    def __init__(self):
        """Initialize GUID parser."""
        pass
    
    def parse(self, guid: str) -> Dict[str, Optional[str]]:
        """
        Parse a Plex GUID string.
        
        Args:
            guid: Plex GUID string (e.g., "imdb://tt1234567" or "plex://show/abc123")
            
        Returns:
            Dictionary with extracted identifiers
        """
        if not guid:
            return {"plex": None, "imdb": None, "tmdb": None, "tvdb": None, "raw": None}
        
        logger.debug(f"Parsing GUID: {guid}")
        
        result = {
            "plex": None,
            "imdb": None,
            "tmdb": None,
            "tvdb": None,
            "raw": guid
        }
        
        # Try each pattern
        for guid_type, pattern in self.PATTERNS.items():
            match = pattern.search(guid)
            if match:
                value = match.group(1)
                
                if guid_type == 'imdb':
                    result["imdb"] = value
                elif guid_type == 'tmdb':
                    result["tmdb"] = value
                elif guid_type == 'tvdb':
                    result["tvdb"] = value
                elif guid_type.startswith('plex'):
                    result["plex"] = value
        
        logger.debug(f"Parsed GUID result: {result}")
        return result
    
    def parse_guid_list(self, guid_list: list) -> ParsedGuid:
        """
        Parse a list of GUIDs and merge results.
        
        Args:
            guid_list: List of GUID strings
            
        Returns:
            ParsedGuid object with merged identifiers
        """
        if not guid_list:
            return ParsedGuid()
        
        result = ParsedGuid()
        
        for guid in guid_list:
            parsed = self.parse(guid)
            
            # Merge results, preferring non-None values
            if parsed["imdb"] and not result.imdb:
                result.imdb = parsed["imdb"]
            if parsed["tmdb"] and not result.tmdb:
                result.tmdb = parsed["tmdb"]
            if parsed["tvdb"] and not result.tvdb:
                result.tvdb = parsed["tvdb"]
            if parsed["plex"] and not result.plex:
                result.plex = parsed["plex"]
        
        result.raw = guid_list[0] if guid_list else None
        return result
    
    def parse_plex_item(self, item: Dict[str, Any]) -> ParsedGuid:
        """
        Parse GUIDs from a Plex item.
        
        Args:
            item: Plex item dictionary
            
        Returns:
            ParsedGuid object
        """
        # Try different GUID fields
        guid_fields = ['guid', 'Guid', 'guids', 'Guids']
        
        for field in guid_fields:
            if field in item:
                guid_value = item[field]
                
                if isinstance(guid_value, list):
                    return self.parse_guid_list(guid_value)
                elif isinstance(guid_value, str):
                    return self.parse(guid_value)
                elif isinstance(guid_value, dict):
                    # Handle case where GUIDs are in a dict format
                    guid_list = []
                    for guid_item in guid_value.get('Guid', []):
                        if isinstance(guid_item, dict) and 'id' in guid_item:
                            guid_list.append(guid_item['id'])
                    return self.parse_guid_list(guid_list)
        
        # Fallback: try to extract from other fields
        if 'ratingKey' in item:
            return ParsedGuid(plex=item['ratingKey'], raw=item['ratingKey'])
        
        return ParsedGuid()
    
    def normalize_rating_system(self, content_rating: str) -> tuple[str, str]:
        """
        Normalize content rating to system and code.
        
        Args:
            content_rating: Content rating string (e.g., "TV-PG", "PG-13")
            
        Returns:
            Tuple of (rating_system, rating_code)
        """
        if not content_rating:
            return "unknown", "unknown"
        
        content_rating = content_rating.strip().upper()
        
        # TV ratings
        if content_rating.startswith('TV-'):
            return "TV", content_rating
        
        # MPAA ratings
        mpaa_ratings = ['G', 'PG', 'PG-13', 'R', 'NC-17', 'NR']
        if content_rating in mpaa_ratings:
            return "MPAA", content_rating
        
        # Other common ratings
        if content_rating in ['UNRATED', 'NOT RATED']:
            return "MPAA", "NR"
        
        return "unknown", content_rating
    
    def infer_kids_friendly(self, content_rating: str) -> bool:
        """
        Infer if content is kids-friendly based on rating.
        
        Args:
            content_rating: Content rating string
            
        Returns:
            True if content is likely kids-friendly
        """
        if not content_rating:
            return False
        
        content_rating = content_rating.strip().upper()
        
        # Kids-friendly ratings
        kids_ratings = ['G', 'TV-Y', 'TV-Y7', 'TV-G']
        return content_rating in kids_ratings