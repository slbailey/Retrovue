"""
Path mapping service for converting Plex paths to local paths with per-library support
"""

import os
import re
from typing import List, Dict, Optional


class PlexPathMappingService:
    """Service for mapping Plex server paths to local paths with per-library support"""
    
    def __init__(self, path_mappings: List[Dict], server_id: int = None):
        """
        Initialize the path mapping service
        
        Args:
            path_mappings: List of path mappings from database
            server_id: Optional server ID to filter mappings
        """
        self.path_mappings = path_mappings
        self.server_id = server_id
    
    def get_local_path(self, plex_path: str, library_root: str = None) -> str:
        """
        Convert a Plex path to a local path using the configured mappings
        
        Args:
            plex_path: The path as reported by Plex server
            library_root: Optional library root path to find specific mapping
            
        Returns:
            The mapped local path
        """
        if not plex_path or not self.path_mappings:
            return plex_path
        
        # Find the best matching mapping
        mapping = self._find_best_mapping(plex_path, library_root)
        if not mapping:
            return plex_path
        
        plex_prefix = mapping['plex_path']
        local_prefix = mapping['local_path']
        
        # Normalize paths for comparison
        plex_prefix_normalized = self._normalize_path(plex_prefix)
        plex_path_normalized = self._normalize_path(plex_path)
        
        # Check if the plex path starts with our mapping prefix
        if plex_path_normalized.startswith(plex_prefix_normalized):
            # Replace the plex prefix with the local prefix
            relative_path = plex_path_normalized[len(plex_prefix_normalized):]
            # Remove leading slash if present
            if relative_path.startswith('/'):
                relative_path = relative_path[1:]
            
            # Build the local path
            local_path = os.path.join(local_prefix, relative_path)
            
            # Normalize the final path for the current OS
            return os.path.normpath(local_path)
        
        # If no mapping applies, return the original path
        return plex_path
    
    def _find_best_mapping(self, plex_path: str, library_root: str = None) -> Optional[Dict]:
        """
        Find the best matching path mapping for a given Plex path
        
        Args:
            plex_path: The Plex path to map
            library_root: Optional library root to find specific mapping
            
        Returns:
            The best matching mapping or None
        """
        if not self.path_mappings:
            return None
        
        # Filter mappings by server_id if specified
        filtered_mappings = self.path_mappings
        if self.server_id is not None:
            filtered_mappings = [m for m in filtered_mappings if m.get('server_id') == self.server_id]
        
        if not filtered_mappings:
            return None
        
        # If library_root is specified, try to find exact match first
        if library_root:
            for mapping in filtered_mappings:
                if (mapping.get('library_root') == library_root and 
                    plex_path.startswith(mapping['plex_path'])):
                    return mapping
        
        # Find the longest matching prefix (most specific mapping)
        best_mapping = None
        best_match_length = 0
        
        for mapping in filtered_mappings:
            plex_prefix = mapping['plex_path']
            if plex_path.startswith(plex_prefix) and len(plex_prefix) > best_match_length:
                best_mapping = mapping
                best_match_length = len(plex_prefix)
        
        return best_mapping
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize a path for comparison (handle different path separators)
        
        Args:
            path: The path to normalize
            
        Returns:
            Normalized path with forward slashes
        """
        if not path:
            return ""
        
        # Convert backslashes to forward slashes for consistent comparison
        normalized = path.replace('\\', '/')
        
        # Remove trailing slash if present
        if normalized.endswith('/') and len(normalized) > 1:
            normalized = normalized[:-1]
        
        return normalized
    
    @classmethod
    def create_from_database(cls, database, server_id: int = None) -> 'PlexPathMappingService':
        """
        Create a path mapping service from database mappings
        
        Args:
            database: The database instance
            server_id: Optional server ID to filter mappings
            
        Returns:
            Configured PlexPathMappingService instance
        """
        path_mappings = database.get_plex_path_mappings(server_id=server_id)
        return cls(path_mappings, server_id)
