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
        if not path:
            return ""
        
        # Convert backslashes to forward slashes and trim trailing slashes
        normalized = path.replace('\\', '/').rstrip('/')
        return normalized
    
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
    
    def resolve(self, server_id: int, library_id: int, plex_path: str, case_sensitive: bool = (os.name != 'nt')) -> Optional[str]:
        """
        Resolve a Plex path to a local path using longest-prefix matching.
        
        Args:
            server_id: Server ID
            library_id: Library ID
            plex_path: Plex file path
            case_sensitive: Whether to perform case-sensitive matching 
                          (default: False on Windows, True on other platforms)
            
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
            # Normalize both stored prefix and incoming path
            stored_prefix_norm = self._normalize_path(mapping.plex_prefix)
            local_prefix_norm = self._normalize_path(mapping.local_prefix)
            
            # Perform comparison (case-sensitive or case-insensitive)
            if case_sensitive:
                if plex_path_norm.startswith(stored_prefix_norm):
                    match_prefix = stored_prefix_norm
                    match_local = local_prefix_norm
                else:
                    continue
            else:
                if plex_path_norm.lower().startswith(stored_prefix_norm.lower()):
                    match_prefix = stored_prefix_norm
                    match_local = local_prefix_norm
                else:
                    continue
            
            # Compute the remainder from the normalized strings
            remainder = plex_path_norm[len(match_prefix):]
            if remainder.startswith('/'):
                remainder = remainder[1:]
            
            # Join with local prefix using os.path.join and normalize
            if remainder:
                local_path = os.path.normpath(os.path.join(match_local, *remainder.split('/')))
            else:
                local_path = os.path.normpath(match_local)
            
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
    
    def resolve_local_path(self, server_id: int, library_id: int, plex_path: str, case_sensitive: bool = (os.name != 'nt')) -> Optional[str]:
        """
        Resolve a Plex path to a local path (alias for resolve method).
        
        Args:
            server_id: Server ID
            library_id: Library ID
            plex_path: Plex file path
            case_sensitive: Whether to perform case-sensitive matching
            
        Returns:
            Local file path if mapping found, None otherwise
        """
        return self.resolve(server_id, library_id, plex_path, case_sensitive)
    
    def get_path_mappings(self, server_id: int, library_id: int) -> List[Mapping]:
        """
        Get path mappings for a server and library (public interface).
        
        Args:
            server_id: Server ID
            library_id: Library ID
            
        Returns:
            List of Mapping objects, sorted by plex_prefix length (longest first)
        """
        return self._get_mappings(server_id, library_id)
    
    def add_path_mapping(self, server_id: int, library_id: int, plex_path: str, local_path: str) -> int:
        """
        Add a new path mapping.
        
        Args:
            server_id: Server ID
            library_id: Library ID
            plex_path: Plex path prefix
            local_path: Local path prefix
            
        Returns:
            ID of the created mapping
        """
        cursor = self._conn.execute("""
            INSERT INTO path_mappings (server_id, library_id, plex_path, local_path)
            VALUES (?, ?, ?, ?)
        """, (server_id, library_id, plex_path, local_path))
        
        mapping_id = cursor.lastrowid
        self._conn.commit()
        
        # Clear cache for this server/library combination
        cache_key = (server_id, library_id)
        if cache_key in self._cache:
            del self._cache[cache_key]
        
        logger.info(f"Added path mapping: {plex_path} -> {local_path}")
        return mapping_id
    
    def remove_path_mapping(self, mapping_id: int) -> bool:
        """
        Remove a path mapping by ID.
        
        Args:
            mapping_id: ID of the mapping to remove
            
        Returns:
            True if mapping was removed, False if not found
        """
        cursor = self._conn.execute("""
            DELETE FROM path_mappings WHERE id = ?
        """, (mapping_id,))
        
        if cursor.rowcount > 0:
            self._conn.commit()
            # Clear all caches since we don't know which server/library this affects
            self._cache.clear()
            logger.info(f"Removed path mapping with ID {mapping_id}")
            return True
        else:
            logger.warning(f"Path mapping with ID {mapping_id} not found")
            return False
    
    def list_path_mappings(self, server_id: Optional[int] = None) -> List[Tuple[int, int, str, str]]:
        """
        List path mappings, optionally filtered by server.
        
        Args:
            server_id: Optional server ID to filter by
            
        Returns:
            List of (id, server_id, library_id, plex_path, local_path) tuples
        """
        if server_id is not None:
            cursor = self._conn.execute("""
                SELECT id, server_id, library_id, plex_path, local_path
                FROM path_mappings
                WHERE server_id = ?
                ORDER BY LENGTH(plex_path) DESC
            """, (server_id,))
        else:
            cursor = self._conn.execute("""
                SELECT id, server_id, library_id, plex_path, local_path
                FROM path_mappings
                ORDER BY server_id, LENGTH(plex_path) DESC
            """)
        
        return cursor.fetchall()