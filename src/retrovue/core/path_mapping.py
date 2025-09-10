"""
Path mapping service for converting Plex paths to local paths
"""

import os
import re
from typing import List, Dict, Optional


class PlexPathMappingService:
    """Service for mapping Plex server paths to local paths"""
    
    def __init__(self, path_mappings: List[Dict[str, str]]):
        """
        Initialize the path mapping service
        
        Args:
            path_mappings: List of path mappings from database
        """
        self.path_mappings = path_mappings
    
    def get_local_path(self, plex_path: str) -> str:
        """
        Convert a Plex path to a local path using the configured mappings
        
        Args:
            plex_path: The path as reported by Plex server
            
        Returns:
            The mapped local path
        """
        if not plex_path or not self.path_mappings:
            return plex_path
        
        # Use the first mapping (we can extend this later for multiple mappings)
        mapping = self.path_mappings[0]
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
    def create_from_database(cls, database) -> 'PlexPathMappingService':
        """
        Create a path mapping service from database mappings
        
        Args:
            database: The database instance
            
        Returns:
            Configured PlexPathMappingService instance
        """
        path_mappings = database.get_plex_path_mappings()
        return cls(path_mappings)
