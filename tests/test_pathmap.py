"""
Tests for path mapping functionality.
"""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from src.retrovue.importers.plex.pathmap import PathMapper, Mapping


class TestPathMapper:
    """Test cases for PathMapper."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Create database connection
        self.conn = sqlite3.connect(self.temp_db.name)
        self.conn.row_factory = sqlite3.Row
        
        # Create path_mappings table
        self.conn.execute("""
            CREATE TABLE path_mappings (
                id INTEGER PRIMARY KEY,
                server_id INTEGER NOT NULL,
                library_id INTEGER NOT NULL,
                plex_path TEXT NOT NULL,
                local_path TEXT NOT NULL
            )
        """)
        
        # Insert test data
        test_mappings = [
            (1, 1, "/data/", "C:/data/"),
            (2, 1, "/data/TV/", "D:/TV/"),
            (3, 1, "/data/Movies/", "E:/Movies/"),
            (4, 2, "/media/", "F:/media/"),
        ]
        
        for mapping in test_mappings:
            self.conn.execute(
                "INSERT INTO path_mappings (server_id, library_id, plex_path, local_path) VALUES (?, ?, ?, ?)",
                mapping
            )
        
        self.conn.commit()
        
        # Create path mapper
        self.path_mapper = PathMapper(self.conn)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.conn.close()
        Path(self.temp_db.name).unlink()
    
    def test_get_path_mappings(self):
        """Test getting path mappings."""
        mappings = self.path_mapper.get_path_mappings(1, 1)
        
        assert len(mappings) == 3
        assert mappings[0].plex_prefix == "/data/TV/"  # Longest first
        assert mappings[0].local_prefix == "D:/TV/"
        assert mappings[1].plex_prefix == "/data/Movies/"
        assert mappings[1].local_prefix == "E:/Movies/"
        assert mappings[2].plex_prefix == "/data/"
        assert mappings[2].local_prefix == "C:/data/"
    
    def test_resolve_local_path_exact_match(self):
        """Test resolving path with exact match."""
        local_path = self.path_mapper.resolve_local_path(1, 1, "/data/TV/Show/ep1.mkv")
        assert local_path == "D:/TV/Show/ep1.mkv"
    
    def test_resolve_local_path_partial_match(self):
        """Test resolving path with partial match."""
        local_path = self.path_mapper.resolve_local_path(1, 1, "/data/Movies/movie.mp4")
        assert local_path == "E:/Movies/movie.mp4"
    
    def test_resolve_local_path_fallback(self):
        """Test resolving path with fallback to shorter match."""
        local_path = self.path_mapper.resolve_local_path(1, 1, "/data/Other/file.mkv")
        assert local_path == "C:/data/Other/file.mkv"
    
    def test_resolve_local_path_no_match(self):
        """Test resolving path with no match."""
        local_path = self.path_mapper.resolve_local_path(1, 1, "/other/path/file.mkv")
        assert local_path is None
    
    def test_resolve_local_path_wrong_server(self):
        """Test resolving path with wrong server ID."""
        local_path = self.path_mapper.resolve_local_path(2, 1, "/data/TV/Show/ep1.mkv")
        assert local_path is None
    
    def test_resolve_local_path_wrong_library(self):
        """Test resolving path with wrong library ID."""
        local_path = self.path_mapper.resolve_local_path(1, 2, "/data/TV/Show/ep1.mkv")
        assert local_path is None
    
    def test_resolve_local_path_different_server_library(self):
        """Test resolving path with different server/library combination."""
        local_path = self.path_mapper.resolve_local_path(1, 2, "/media/movie.mp4")
        assert local_path == "F:/media/movie.mp4"
    
    def test_add_path_mapping(self):
        """Test adding a new path mapping."""
        mapping_id = self.path_mapper.add_path_mapping(1, 1, "/new/path/", "G:/new/path/")
        
        assert mapping_id > 0
        
        # Verify it was added
        mappings = self.path_mapper.get_path_mappings(1, 1)
        assert len(mappings) == 4
        
        # Test resolution
        local_path = self.path_mapper.resolve_local_path(1, 1, "/new/path/file.mkv")
        assert local_path == "G:/new/path/file.mkv"
    
    def test_remove_path_mapping(self):
        """Test removing a path mapping."""
        # Add a mapping first
        mapping_id = self.path_mapper.add_path_mapping(1, 1, "/temp/path/", "H:/temp/path/")
        
        # Remove it
        result = self.path_mapper.remove_path_mapping(mapping_id)
        assert result is True
        
        # Verify it was removed
        local_path = self.path_mapper.resolve_local_path(1, 1, "/temp/path/file.mkv")
        assert local_path is None
    
    def test_remove_nonexistent_path_mapping(self):
        """Test removing a non-existent path mapping."""
        result = self.path_mapper.remove_path_mapping(99999)
        assert result is False
    
    def test_list_path_mappings_all(self):
        """Test listing all path mappings."""
        mappings = self.path_mapper.list_path_mappings()
        assert len(mappings) == 4
    
    def test_list_path_mappings_by_server(self):
        """Test listing path mappings by server."""
        mappings = self.path_mapper.list_path_mappings(server_id=1)
        assert len(mappings) == 3
        
        mappings = self.path_mapper.list_path_mappings(server_id=2)
        assert len(mappings) == 0  # No mappings for server 2
    
    def test_cache_behavior(self):
        """Test that caching works correctly."""
        # First call should load from database
        mappings1 = self.path_mapper.get_path_mappings(1, 1)
        
        # Second call should use cache
        mappings2 = self.path_mapper.get_path_mappings(1, 1)
        
        assert mappings1 is mappings2  # Same object (cached)
    
    def test_cache_invalidation(self):
        """Test that cache is invalidated when mappings change."""
        # Load mappings (populates cache)
        self.path_mapper.get_path_mappings(1, 1)
        
        # Add new mapping (should invalidate cache)
        self.path_mapper.add_path_mapping(1, 1, "/cache/test/", "I:/cache/test/")
        
        # Load mappings again (should reload from database)
        mappings = self.path_mapper.get_path_mappings(1, 1)
        assert len(mappings) == 4  # Should include the new mapping
    
    def test_clear_cache(self):
        """Test clearing the cache."""
        # Load mappings (populates cache)
        mappings1 = self.path_mapper.get_path_mappings(1, 1)
        
        # Clear cache
        self.path_mapper.clear_cache()
        
        # Load mappings again (should reload from database)
        mappings2 = self.path_mapper.get_path_mappings(1, 1)
        
        assert mappings1 is not mappings2  # Different objects
        assert len(mappings1) == len(mappings2)  # Same content
    
    def test_mapping_dataclass(self):
        """Test Mapping dataclass behavior."""
        mapping = Mapping(
            plex_prefix="/test/",
            local_prefix="C:/test/",
            plex_prefix_norm="/test/"
        )
        
        # Test basic properties
        assert mapping.plex_prefix == "/test/"
        assert mapping.local_prefix == "C:/test/"
        assert mapping.plex_prefix_norm == "/test/"
