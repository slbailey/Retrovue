"""
Filesystem importer for discovering content from local file systems.

This importer scans local directories for media files and returns them as discovered items.
It supports glob patterns and can extract basic metadata from file system attributes.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import DiscoveredItem, ImporterError


class FilesystemImporter:
    """
    Importer = Adapter. Talks to external system. Discovers content. Does not persist.
    
    This importer scans specified directories for media files and returns them
    as discovered items with file:// URIs and basic metadata.
    """
    
    name = "filesystem"
    
    def __init__(
        self,
        source_name: str,
        root_paths: list[str] | None = None,
        glob_patterns: list[str] | None = None,
        include_hidden: bool = False,
        calculate_hash: bool = True
    ):
        """
        Initialize the filesystem importer.
        
        Args:
            source_name: Human-readable name for this filesystem source
            root_paths: List of root directories to scan (default: current directory)
            glob_patterns: List of glob patterns to match (default: common video extensions)
            include_hidden: Whether to include hidden files and directories
            calculate_hash: Whether to calculate SHA-256 hash of files
        """
        self.source_name = source_name
        self.root_paths = root_paths or ["."]
        self.glob_patterns = glob_patterns or [
            "**/*.mp4", "**/*.mkv", "**/*.avi", "**/*.mov", "**/*.wmv",
            "**/*.flv", "**/*.webm", "**/*.m4v", "**/*.3gp", "**/*.ogv"
        ]
        self.include_hidden = include_hidden
        self.calculate_hash = calculate_hash
    
    def discover(self) -> list[DiscoveredItem]:
        """
        Discover media files from the configured file system paths.
        
        Returns:
            List of discovered media files
            
        Raises:
            ImporterError: If discovery fails
        """
        try:
            discovered_items = []
            
            for root_path in self.root_paths:
                root = Path(root_path).resolve()
                
                if not root.exists():
                    raise ImporterError(f"Root path does not exist: {root}")
                
                if not root.is_dir():
                    raise ImporterError(f"Root path is not a directory: {root}")
                
                for pattern in self.glob_patterns:
                    for file_path in root.glob(pattern):
                        if self._should_include_file(file_path):
                            item = self._create_discovered_item(file_path)
                            if item:
                                discovered_items.append(item)
            
            return discovered_items
            
        except Exception as e:
            raise ImporterError(f"Failed to discover files: {str(e)}") from e
    
    def _should_include_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be included in discovery.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if the file should be included
        """
        # Skip hidden files if not including them
        if not self.include_hidden and any(part.startswith('.') for part in file_path.parts):
            return False
        
        # Skip directories
        if file_path.is_dir():
            return False
        
        # Skip if file doesn't exist (broken symlinks, etc.)
        if not file_path.exists():
            return False
        
        # Skip if not a file
        if not file_path.is_file():
            return False
        
        return True
    
    def _create_discovered_item(self, file_path: Path) -> DiscoveredItem | None:
        """
        Create a DiscoveredItem from a file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            DiscoveredItem or None if creation fails
        """
        try:
            # Get file stats
            stat = file_path.stat()
            size = stat.st_size
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            
            # Create file URI
            path_uri = f"file://{file_path.as_posix()}"
            
            # Calculate hash if requested
            hash_sha256 = None
            if self.calculate_hash:
                hash_sha256 = self._calculate_file_hash(file_path)
            
            # Extract basic labels from filename
            raw_labels = self._extract_filename_labels(file_path.name)
            
            return DiscoveredItem(
                path_uri=path_uri,
                provider_key=str(file_path),  # Use file path as provider key
                raw_labels=raw_labels,
                last_modified=last_modified,
                size=size,
                hash_sha256=hash_sha256
            )
            
        except Exception as e:
            # Log error but continue with other files
            print(f"Warning: Failed to process file {file_path}: {e}")
            return None
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 hash as hex string
        """
        hash_sha256 = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()
    
    def _extract_filename_labels(self, filename: str) -> dict[str, Any]:
        """
        Extract structured labels from filename using pattern recognition.
        
        Args:
            filename: Name of the file
            
        Returns:
            Dictionary of extracted labels with confidence indicators
        """
        # Remove extension
        name_without_ext = Path(filename).stem
        
        # Initialize labels dictionary
        labels = {}
        
        # Pattern 1: Show.Name.S02E05.*
        # Matches: Breaking.Bad.S02E05.720p.mkv
        tv_pattern1 = re.compile(r'^(.+?)\.S(\d{1,2})E(\d{1,2})(?:\.|$)', re.IGNORECASE)
        match = tv_pattern1.match(name_without_ext)
        if match:
            labels['title_guess'] = match.group(1).replace('.', ' ').strip()
            labels['season'] = int(match.group(2))
            labels['episode'] = int(match.group(3))
            labels['type'] = 'tv'
            return labels
        
        # Pattern 2: Show Name - S2E5 - Episode Title.*
        # Matches: Breaking Bad - S2E5 - Phoenix.mkv
        tv_pattern2 = re.compile(r'^(.+?)\s*-\s*S(\d{1,2})E(\d{1,2})\s*-\s*(.+?)(?:\s*-\s*|$)', re.IGNORECASE)
        match = tv_pattern2.match(name_without_ext)
        if match:
            labels['title_guess'] = match.group(1).strip()
            labels['season'] = int(match.group(2))
            labels['episode'] = int(match.group(3))
            labels['episode_title'] = match.group(4).strip()
            labels['type'] = 'tv'
            return labels
        
        # Pattern 3: Movie.Name.1987.*
        # Matches: The.Matrix.1999.1080p.mkv
        movie_pattern = re.compile(r'^(.+?)\.(\d{4})\.', re.IGNORECASE)
        match = movie_pattern.match(name_without_ext)
        if match:
            labels['title_guess'] = match.group(1).replace('.', ' ').strip()
            labels['year'] = int(match.group(2))
            labels['type'] = 'movie'
            return labels
        
        # Pattern 4: Show Name (Year) - S01E01.*
        # Matches: Breaking Bad (2008) - S01E01.mkv
        tv_pattern3 = re.compile(r'^(.+?)\s*\((\d{4})\)\s*-\s*S(\d{1,2})E(\d{1,2})', re.IGNORECASE)
        match = tv_pattern3.match(name_without_ext)
        if match:
            labels['title_guess'] = match.group(1).strip()
            labels['year'] = int(match.group(2))
            labels['season'] = int(match.group(3))
            labels['episode'] = int(match.group(4))
            labels['type'] = 'tv'
            return labels
        
        # Pattern 5: Movie Name (Year).*
        # Matches: The Matrix (1999).mkv
        movie_pattern2 = re.compile(r'^(.+?)\s*\((\d{4})\)', re.IGNORECASE)
        match = movie_pattern2.match(name_without_ext)
        if match:
            labels['title_guess'] = match.group(1).strip()
            labels['year'] = int(match.group(2))
            labels['type'] = 'movie'
            return labels
        
        # Fallback: Extract any year from the filename
        year_match = re.search(r'\b(19|20)\d{2}\b', name_without_ext)
        if year_match:
            labels['year'] = int(year_match.group())
        
        # Extract title from the beginning (before any year or episode info)
        title_part = re.split(r'\s*[\(\[].*?[\)\]]\s*|\s*-\s*S\d+E\d+|\s*\.\d{4}\.', name_without_ext)[0]
        if title_part and title_part.strip():
            labels['title_guess'] = title_part.replace('.', ' ').replace('_', ' ').strip()
        
        return labels
    
    def list_asset_groups(self) -> list[dict[str, any]]:
        """
        List the asset groups (directories) available from this filesystem source.
        
        Returns:
            List of dictionaries containing directory information
        """
        try:
            asset_groups = []
            
            for root_path in self.root_paths:
                root = Path(root_path).resolve()
                
                if not root.exists() or not root.is_dir():
                    continue
                
                # For filesystem, each root path is an asset group
                # Count files in this directory
                file_count = 0
                for pattern in self.glob_patterns:
                    try:
                        file_count += len([f for f in root.glob(pattern) if self._should_include_file(f)])
                    except Exception:
                        continue
                
                asset_groups.append({
                    "id": str(root),
                    "name": root.name,
                    "path": str(root),
                    "enabled": True,  # Default to enabled, actual state managed by database
                    "asset_count": file_count,
                    "type": "directory"
                })
            
            return asset_groups
            
        except Exception as e:
            raise ImporterError(f"Failed to list asset groups: {str(e)}") from e
    
    def enable_asset_group(self, group_id: str) -> bool:
        """
        Enable an asset group (directory) for content discovery.
        
        Args:
            group_id: Directory path
            
        Returns:
            True if successfully enabled, False otherwise
        """
        try:
            # For filesystem, we just verify the directory exists
            path = Path(group_id)
            return path.exists() and path.is_dir()
            
        except Exception as e:
            print(f"Failed to enable asset group {group_id}: {e}")
            return False
    
    def disable_asset_group(self, group_id: str) -> bool:
        """
        Disable an asset group (directory) from content discovery.
        
        Args:
            group_id: Directory path
            
        Returns:
            True if successfully disabled, False otherwise
        """
        # For filesystem, disabling is handled at the database level
        # This method just confirms the operation
        return True

    def get_help(self) -> dict[str, any]:
        """
        Get help information for the filesystem importer.
        
        Returns:
            Dictionary containing help information
        """
        return {
            "description": "Scan local filesystem directories for media files and discover content",
            "required_params": [
                {
                    "name": "source_name",
                    "type": "str",
                    "description": "Human-readable name for this filesystem source",
                    "example": '"My Media Library"'
                },
                {
                    "name": "root_paths",
                    "type": "list[str]",
                    "description": "List of root directories to scan",
                    "example": '["/media/movies", "/media/tv"]'
                }
            ],
            "optional_params": [
                {
                    "name": "glob_patterns",
                    "type": "list[str]",
                    "default": "Common video extensions",
                    "description": "List of glob patterns to match files"
                },
                {
                    "name": "include_hidden",
                    "type": "bool",
                    "default": False,
                    "description": "Whether to include hidden files and directories"
                },
                {
                    "name": "calculate_hash",
                    "type": "bool",
                    "default": True,
                    "description": "Whether to calculate SHA-256 hash of files"
                }
            ],
            "examples": [
                'retrovue source add --type filesystem --name "My Media Library" --base-path "/media/movies"',
                'retrovue source add --type filesystem --name "Commercials" --base-path "T:\\Commercials"',
                'retrovue source add --type filesystem --name "Media Library" --base-path "/media" --enrichers "ffprobe"'
            ],
            "cli_params": {
                "name": "Friendly name for the filesystem source",
                "base_path": "Base filesystem path to scan"
            }
        }


# Note: FilesystemImporter should be registered manually when needed
# to avoid circular import issues
