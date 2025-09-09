"""
Retrovue TinyMediaManager Integration

This module handles importing content from TinyMediaManager (TMM) .nfo files into the
Retrovue database. TMM is a popular media management tool that creates detailed
metadata files for movies and TV shows, which can be imported into Retrovue for
scheduling and content management.

Key Features:
- Parse TMM .nfo files and extract comprehensive metadata
- Import movies and TV shows with detailed information
- Extract custom fields and scheduling metadata
- Map TMM content ratings to Retrovue rating system
- Support for recursive directory scanning
- Robust error handling and validation

Supported Metadata:
- Basic Information: Title, plot, genre, year, rating, duration
- Content Classification: Content type (movie/show), content rating
- Custom Fields: TMM-specific custom fields and scheduling metadata
- File Information: File paths and source tracking

Content Rating Mapping:
- Maps TMM ratings (G, PG, PG-13, R, NC-17, TV-G, TV-PG, TV-14, TV-MA) to Retrovue system
- Defaults to PG-13 for unknown ratings
- Supports both movie and TV content ratings

Scheduling Metadata:
- Extracts custom scheduling fields from TMM .nfo files
- Sets default daypart preferences based on content type
- Preserves custom fields for advanced scheduling features
- Tracks import timestamps and source information

Usage:
    importer = TMMImporter(database)
    count = importer.import_directory("/path/to/media", recursive=True)
    
    # Or import specific files
    count = importer.import_specific_files([Path("movie.nfo"), Path("show.nfo")])

Architecture:
- TMMImporter: Main class for .nfo file processing
- XML parsing with robust error handling
- Database integration for content storage
- Custom field extraction for scheduling metadata

Note: This module is designed for future use when TMM integration is needed.
Currently, the main content import is handled by the Plex integration module.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from .database import RetrovueDatabase


class TMMImporter:
    """
    Imports content from TinyMediaManager .nfo files into the Retrovue database.
    """
    
    def __init__(self, database: RetrovueDatabase):
        """
        Initialize the TMM importer.
        
        Args:
            database: Retrovue database instance
        """
        self.db = database
    
    def scan_directory(self, directory_path: str, recursive: bool = True) -> List[Path]:
        """
        Scan a directory for .nfo files.
        
        Args:
            directory_path: Path to scan for .nfo files
            recursive: Whether to scan subdirectories recursively
            
        Returns:
            List of .nfo file paths
        """
        directory = Path(directory_path)
        if not directory.exists():
            print(f"❌ Directory does not exist: {directory_path}")
            return []
        
        pattern = "**/*.nfo" if recursive else "*.nfo"
        nfo_files = list(directory.glob(pattern))
        
        print(f"🔍 Found {len(nfo_files)} .nfo files in {directory_path}")
        return nfo_files
    
    def parse_nfo_file(self, nfo_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse a single .nfo file and extract metadata.
        
        Args:
            nfo_path: Path to the .nfo file
            
        Returns:
            Dictionary with parsed metadata, or None if parsing failed
        """
        try:
            tree = ET.parse(nfo_path)
            root = tree.getroot()
            
            # Extract basic information
            metadata = {
                'file_path': str(nfo_path),
                'title': self._get_text(root, 'title', 'Unknown Title'),
                'plot': self._get_text(root, 'plot', ''),
                'genre': self._get_text(root, 'genre', ''),
                'year': self._get_text(root, 'year', ''),
                'rating': self._get_text(root, 'rating', ''),
                'content_rating': self._get_text(root, 'mpaa', ''),
                'duration': self._get_duration(root),
                'content_type': self._determine_content_type(root),
                'source_type': 'tmm'
            }
            
            # Extract custom fields (TMM-specific scheduling metadata)
            custom_fields = self._extract_custom_fields(root)
            metadata.update(custom_fields)
            
            return metadata
            
        except ET.ParseError as e:
            print(f"❌ Failed to parse {nfo_path}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error processing {nfo_path}: {e}")
            return None
    
    def _get_text(self, element: ET.Element, tag: str, default: str = '') -> str:
        """Get text content from an XML element."""
        child = element.find(tag)
        return child.text if child is not None and child.text else default
    
    def _get_duration(self, root: ET.Element) -> Optional[int]:
        """Extract duration from XML, handling different formats."""
        # Try different duration fields
        duration_fields = ['runtime', 'duration', 'time']
        
        for field in duration_fields:
            duration_text = self._get_text(root, field)
            if duration_text:
                try:
                    # Handle different duration formats
                    if ':' in duration_text:
                        # Format: "1:30:00" or "90:00"
                        parts = duration_text.split(':')
                        if len(parts) == 3:  # HH:MM:SS
                            hours, minutes, seconds = map(int, parts)
                            return hours * 3600 + minutes * 60 + seconds
                        elif len(parts) == 2:  # MM:SS
                            minutes, seconds = map(int, parts)
                            return minutes * 60 + seconds
                    else:
                        # Assume it's already in seconds
                        return int(duration_text)
                except ValueError:
                    continue
        
        return None
    
    def _determine_content_type(self, root: ET.Element) -> str:
        """Determine content type from XML structure."""
        # Check for TV show indicators
        if root.find('episode') is not None or root.find('season') is not None:
            return 'show'
        
        # Check for movie indicators
        if root.find('movie') is not None or root.find('title') is not None:
            return 'movie'
        
        # Default to movie if we can't determine
        return 'movie'
    
    def _extract_custom_fields(self, root: ET.Element) -> Dict[str, Any]:
        """Extract custom fields that might contain scheduling metadata."""
        custom_fields = {}
        
        # Look for custom fields in TMM format
        custom_element = root.find('custom')
        if custom_element is not None:
            for child in custom_element:
                if child.text:
                    custom_fields[f"custom_{child.tag}"] = child.text
        
        # Look for scheduling-specific fields
        scheduling_fields = [
            'daypart_preference', 'seasonal_preference', 'target_demographic',
            'commercial_company', 'commercial_category', 'content_warnings',
            'scheduling_notes'
        ]
        
        for field in scheduling_fields:
            value = self._get_text(root, field)
            if value:
                custom_fields[field] = value
        
        return custom_fields
    
    def _map_tmm_rating(self, tmm_rating: str) -> str:
        """Map TMM content rating to Retrovue content rating."""
        rating_map = {
            'G': 'G',
            'PG': 'PG',
            'PG-13': 'PG-13',
            'R': 'R',
            'NC-17': 'Adult',
            'X': 'Adult',
            'TV-G': 'G',
            'TV-PG': 'PG',
            'TV-14': 'PG-13',
            'TV-MA': 'Adult'
        }
        return rating_map.get(tmm_rating, 'PG-13')  # Default to PG-13
    
    def import_directory(self, directory_path: str, recursive: bool = True) -> int:
        """
        Import all .nfo files from a directory.
        
        Args:
            directory_path: Path to directory containing .nfo files
            recursive: Whether to scan subdirectories recursively
            
        Returns:
            Number of items imported
        """
        print(f"🔄 Importing .nfo files from {directory_path}...")
        
        nfo_files = self.scan_directory(directory_path, recursive)
        imported_count = 0
        
        for nfo_path in nfo_files:
            metadata = self.parse_nfo_file(nfo_path)
            if metadata:
                try:
                    # Map TMM rating to Retrovue rating
                    content_rating = self._map_tmm_rating(metadata.get('content_rating', ''))
                    
                    # Add content item to database
                    content_id = self.db.add_content_item(
                        file_path=metadata['file_path'],
                        title=metadata['title'],
                        duration=metadata.get('duration'),
                        content_type=metadata['content_type'],
                        source_type='tmm',
                        source_id=str(nfo_path)
                    )
                    
                    # Prepare scheduling metadata
                    scheduling_metadata = {
                        'content_rating': content_rating,
                        'scheduling_notes': f"Imported from TMM .nfo on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                    
                    # Add any custom scheduling fields
                    for key, value in metadata.items():
                        if key.startswith('custom_') or key in [
                            'daypart_preference', 'seasonal_preference', 'target_demographic',
                            'commercial_company', 'commercial_category', 'content_warnings'
                        ]:
                            scheduling_metadata[key] = value
                    
                    # Set default daypart preference based on content type
                    if metadata['content_type'] == 'movie':
                        scheduling_metadata.setdefault('daypart_preference', 'evening')
                    elif metadata['content_type'] == 'show':
                        scheduling_metadata.setdefault('daypart_preference', 'afternoon')
                    
                    self.db.add_scheduling_metadata(content_id, **scheduling_metadata)
                    imported_count += 1
                    
                    print(f"✅ Imported: {metadata['title']} ({content_rating}) - {metadata.get('duration', 'Unknown')}s")
                    
                except Exception as e:
                    print(f"❌ Failed to import {metadata.get('title', 'Unknown')}: {e}")
        
        print(f"🎉 Imported {imported_count} items from TMM .nfo files")
        return imported_count
    
    def import_specific_files(self, nfo_paths: List[Path]) -> int:
        """
        Import specific .nfo files.
        
        Args:
            nfo_paths: List of .nfo file paths to import
            
        Returns:
            Number of items imported
        """
        print(f"🔄 Importing {len(nfo_paths)} specific .nfo files...")
        
        imported_count = 0
        
        for nfo_path in nfo_paths:
            metadata = self.parse_nfo_file(nfo_path)
            if metadata:
                try:
                    # Map TMM rating to Retrovue rating
                    content_rating = self._map_tmm_rating(metadata.get('content_rating', ''))
                    
                    # Add content item to database
                    content_id = self.db.add_content_item(
                        file_path=metadata['file_path'],
                        title=metadata['title'],
                        duration=metadata.get('duration'),
                        content_type=metadata['content_type'],
                        source_type='tmm',
                        source_id=str(nfo_path)
                    )
                    
                    # Prepare scheduling metadata
                    scheduling_metadata = {
                        'content_rating': content_rating,
                        'scheduling_notes': f"Imported from TMM .nfo on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                    
                    # Add any custom scheduling fields
                    for key, value in metadata.items():
                        if key.startswith('custom_') or key in [
                            'daypart_preference', 'seasonal_preference', 'target_demographic',
                            'commercial_company', 'commercial_category', 'content_warnings'
                        ]:
                            scheduling_metadata[key] = value
                    
                    # Set default daypart preference based on content type
                    if metadata['content_type'] == 'movie':
                        scheduling_metadata.setdefault('daypart_preference', 'evening')
                    elif metadata['content_type'] == 'show':
                        scheduling_metadata.setdefault('daypart_preference', 'afternoon')
                    
                    self.db.add_scheduling_metadata(content_id, **scheduling_metadata)
                    imported_count += 1
                    
                    print(f"✅ Imported: {metadata['title']} ({content_rating}) - {metadata.get('duration', 'Unknown')}s")
                    
                except Exception as e:
                    print(f"❌ Failed to import {metadata.get('title', 'Unknown')}: {e}")
        
        print(f"🎉 Imported {imported_count} items from specific .nfo files")
        return imported_count


def create_tmm_importer(database: RetrovueDatabase) -> TMMImporter:
    """
    Create a TMM importer instance.
    
    Args:
        database: Retrovue database instance
        
    Returns:
        TMMImporter instance
    """
    return TMMImporter(database)
