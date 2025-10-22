"""
Tests for content validation functionality.
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

from src.retrovue.importers.plex.validation import ContentValidator, ValidationStatus, ValidationResult
from src.retrovue.importers.plex.pathmap import PathMapper


class TestContentValidator:
    """Test cases for ContentValidator."""
    
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
        
        # Insert test mapping
        self.conn.execute("""
            INSERT INTO path_mappings (server_id, library_id, plex_path, local_path)
            VALUES (1, 1, '/data/movies/', 'C:/movies/')
        """)
        self.conn.commit()
        
        # Create path mapper
        self.path_mapper = PathMapper(self.conn)
        
        # Create validator
        self.validator = ContentValidator(self.path_mapper)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.conn.close()
        Path(self.temp_db.name).unlink()
    
    def test_validation_result_creation(self):
        """Test ValidationResult creation."""
        result = ValidationResult(
            status=ValidationStatus.VALID,
            message="Test message",
            local_path="/test/path.mp4",
            file_size=1024
        )
        
        assert result.status == ValidationStatus.VALID
        assert result.message == "Test message"
        assert result.local_path == "/test/path.mp4"
        assert result.file_size == 1024
    
    def test_path_mapping_failure(self):
        """Test validation when path mapping fails."""
        result = self.validator.validate_media_file(
            server_id=1,
            library_id=1,
            plex_path="/unknown/path/movie.mp4"
        )
        
        assert result.status == ValidationStatus.PATH_MAPPING_FAILED
        assert "Could not resolve path mapping" in result.message
        assert result.local_path is None
    
    def test_file_not_found(self):
        """Test validation when file doesn't exist."""
        # Mock path mapping to return a non-existent path
        with patch.object(self.path_mapper, 'resolve', return_value="C:/nonexistent/movie.mp4"):
            result = self.validator.validate_media_file(
                server_id=1,
                library_id=1,
                plex_path="/data/movies/movie.mp4"
            )
        
        assert result.status == ValidationStatus.FILE_NOT_FOUND
        assert "File does not exist" in result.message
        assert result.local_path == "C:/nonexistent/movie.mp4"
    
    def test_file_not_accessible(self):
        """Test validation when path is not a file."""
        # Create a directory instead of a file
        temp_dir = tempfile.mkdtemp()
        temp_file = Path(temp_dir) / "test_dir"
        temp_file.mkdir()  # Create directory instead of file
        
        with patch.object(self.path_mapper, 'resolve', return_value=str(temp_file)):
            result = self.validator.validate_media_file(
                server_id=1,
                library_id=1,
                plex_path="/data/movies/movie.mp4"
            )
        
        assert result.status == ValidationStatus.FILE_NOT_ACCESSIBLE
        assert "Path is not a file" in result.message
        
        # Cleanup
        temp_file.rmdir()
        Path(temp_dir).rmdir()
    
    def test_empty_file(self):
        """Test validation when file is empty."""
        # Create empty file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        
        with patch.object(self.path_mapper, 'resolve', return_value=temp_file.name):
            result = self.validator.validate_media_file(
                server_id=1,
                library_id=1,
                plex_path="/data/movies/movie.mp4"
            )
        
        assert result.status == ValidationStatus.FILE_NOT_ACCESSIBLE
        assert "File is empty" in result.message
        assert result.file_size == 0
        
        # Cleanup
        Path(temp_file.name).unlink()
    
    @patch('subprocess.run')
    def test_media_validation_success(self, mock_run):
        """Test successful media validation."""
        # Mock ffprobe output
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '''
        {
            "format": {
                "duration": "120.5",
                "size": "1048576"
            },
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080
                },
                {
                    "codec_type": "audio",
                    "codec_name": "aac"
                }
            ]
        }
        '''
        
        # Create test file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_file.write(b"fake video content")
        temp_file.close()
        
        with patch.object(self.path_mapper, 'resolve', return_value=temp_file.name):
            result = self.validator.validate_media_file(
                server_id=1,
                library_id=1,
                plex_path="/data/movies/movie.mp4"
            )
        
        assert result.status == ValidationStatus.VALID
        assert "File is valid and playable" in result.message
        assert result.duration_ms == 120500
        assert result.video_codec == "h264"
        assert result.audio_codec == "aac"
        assert result.resolution == (1920, 1080)
        
        # Cleanup
        Path(temp_file.name).unlink()
    
    @patch('subprocess.run')
    def test_unsupported_codec(self, mock_run):
        """Test validation with unsupported codec."""
        # Mock ffprobe output with unsupported codec
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '''
        {
            "format": {"duration": "120.5"},
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "unsupported_codec"
                }
            ]
        }
        '''
        
        # Create test file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_file.write(b"fake video content")
        temp_file.close()
        
        with patch.object(self.path_mapper, 'resolve', return_value=temp_file.name):
            result = self.validator.validate_media_file(
                server_id=1,
                library_id=1,
                plex_path="/data/movies/movie.mp4"
            )
        
        assert result.status == ValidationStatus.INVALID_CODEC
        assert "Unsupported video codec" in result.message
        assert result.video_codec == "unsupported_codec"
        
        # Cleanup
        Path(temp_file.name).unlink()
    
    def test_validation_batch(self):
        """Test batch validation."""
        items = [
            {
                'server_id': 1,
                'library_id': 1,
                'plex_path': '/data/movies/movie1.mp4',
                'media_info': {}
            },
            {
                'server_id': 1,
                'library_id': 1,
                'plex_path': '/data/movies/movie2.mp4',
                'media_info': {}
            }
        ]
        
        # Mock path mapping to return non-existent paths
        with patch.object(self.path_mapper, 'resolve', return_value="C:/nonexistent/movie.mp4"):
            results = self.validator.validate_batch(items)
        
        assert len(results) == 2
        assert all(result.status == ValidationStatus.FILE_NOT_FOUND for result in results)
    
    def test_validation_summary(self):
        """Test validation summary generation."""
        results = [
            ValidationResult(ValidationStatus.VALID, "Valid file"),
            ValidationResult(ValidationStatus.FILE_NOT_FOUND, "Missing file"),
            ValidationResult(ValidationStatus.INVALID_CODEC, "Bad codec"),
            ValidationResult(ValidationStatus.VALID, "Another valid file")
        ]
        
        summary = self.validator.get_validation_summary(results)
        
        assert summary['total'] == 4
        assert summary['valid'] == 2
        assert summary['invalid'] == 2
        assert summary['by_status']['valid'] == 2
        assert summary['by_status']['file_not_found'] == 1
        assert summary['by_status']['invalid_codec'] == 1
        assert len(summary['errors']) == 2

