"""
Filesystem scanner for media files.
"""

import os
from pathlib import Path
from typing import Generator, List, Dict, Any


class FilesystemScanner:
    """Scan filesystem for media files."""
    
    SUPPORTED_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'}
    
    def scan_directory(self, directory_path: str) -> Generator[str, None, None]:
        """Scan directory for media files."""
        path = Path(directory_path)
        if not path.exists():
            raise ValueError(f"Directory does not exist: {directory_path}")
        
        for file_path in path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                yield str(file_path)
    
    def get_directory_info(self, directory_path: str) -> Dict[str, Any]:
        """Get information about a directory."""
        path = Path(directory_path)
        if not path.exists():
            return {"error": "Directory does not exist"}
        
        media_files = list(self.scan_directory(directory_path))
        total_size = 0
        for file_path in media_files:
            try:
                total_size += Path(file_path).stat().st_size
            except OSError:
                pass
        
        return {
            "path": directory_path,
            "name": path.name,
            "media_count": len(media_files),
            "total_size": total_size
        }
