"""
Path mapping for resolving Plex paths to local paths.

Reads path_mappings from database and performs longest-prefix substitution.
"""

import logging
import os
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger("retrovue.plex")


@dataclass(frozen=True)
class Mapping:
    """Represents a path mapping entry."""
    plex_prefix: str
    local_prefix: str
    plex_prefix_norm: str  # normalized for comparison


class PathMapper:
    """Maps Plex paths to local paths using database mappings with longest-prefix matching."""
    
    def __init__(self, conn):
        """
        Initialize path mapper.
        
        Args:
            conn: SQLite database connection
        """
        self._conn = conn
        self._cache: Dict[Tuple[int, int], List[Mapping]] = {}
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize a path for comparison.
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized path
        """
        # Convert backslashes to forward slashes for consistent comparison
        # Treat Plex paths as POSIX (forward slashes)
        return path.replace('\\', '/')
    
    def _get_mappings(self, server_id: int, library_id: int) -> List[Mapping]:
        """
        Get path mappings for a server and library with caching.
        
        Args:
            server_id: Server ID
            library_id: Library ID
            
        Returns:
            List of Mapping objects, sorted by plex_prefix length (longest first)
        """
        cache_key = (server_id, library_id)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        logger.debug(f"Loading path mappings for server {server_id}, library {library_id}")
        
        cursor = self._conn.execute("""
            SELECT plex_path, local_path
            FROM path_mappings
            WHERE server_id = ? AND library_id = ?
        """, (server_id, library_id))
        
        mappings = []
        for row in cursor.fetchall():
            plex_prefix = row['plex_path']
            local_prefix = row['local_path']
            plex_prefix_norm = self._normalize_path(plex_prefix)
            
            mapping = Mapping(
                plex_prefix=plex_prefix,
                local_prefix=local_prefix,
                plex_prefix_norm=plex_prefix_norm
            )
            mappings.append(mapping)
        
        # Sort by descending length of normalized plex_prefix (longest first)
        mappings.sort(key=lambda m: len(m.plex_prefix_norm), reverse=True)
        
        # Cache the results
        self._cache[cache_key] = mappings
        
        logger.debug(f"Loaded {len(mappings)} path mappings")
        return mappings
    
    def resolve(self, server_id: int, library_id: int, plex_path: str) -> Optional[str]:
        """
        Resolve a Plex path to a local path using longest-prefix matching.
        
        Args:
            server_id: Server ID
            library_id: Library ID
            plex_path: Plex file path
            
        Returns:
            Local file path if mapping found, None otherwise
        """
        if not plex_path:
            return None
        
        logger.debug(f"Resolving path: {plex_path}")
        
        mappings = self._get_mappings(server_id, library_id)
        plex_path_norm = self._normalize_path(plex_path)
        
        # Find longest matching prefix
        for mapping in mappings:
            if plex_path_norm.startswith(mapping.plex_prefix_norm):
                # Replace the prefix in the original plex_path (preserve case/slashes)
                local_path = plex_path.replace(mapping.plex_prefix, mapping.local_prefix, 1)
                
                # Handle path separators properly
                if not mapping.local_prefix.endswith(('/', '\\')):
                    # If local_prefix doesn't end with separator, use os.path.join
                    remainder = plex_path[len(mapping.plex_prefix):]
                    if remainder.startswith(('/', '\\')):
                        remainder = remainder[1:]
                    local_path = os.path.join(mapping.local_prefix, remainder)
                
                logger.debug(f"Mapped {plex_path} -> {local_path}")
                return local_path
        
        logger.warning(f"No path mapping found for: {plex_path}")
        return None
    
    def list_mappings(self, server_id: int, library_id: int) -> List[Tuple[str, str]]:
        """
        List path mappings for a server and library.
        
        Args:
            server_id: Server ID
            library_id: Library ID
            
        Returns:
            List of (plex_prefix, local_prefix) tuples
        """
        mappings = self._get_mappings(server_id, library_id)
        return [(m.plex_prefix, m.local_prefix) for m in mappings]
    
    def clear_cache(self):
        """Clear the path mapping cache."""
        self._cache.clear()
        logger.debug("Path mapping cache cleared")