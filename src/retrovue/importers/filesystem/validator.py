"""
File validator for filesystem files.
"""

import os
from pathlib import Path
from typing import Dict, Any


class FileValidator:
    """Validate filesystem files."""
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate a single file."""
        path = Path(file_path)
        
        if not path.exists():
            return {"valid": False, "error": "File does not exist"}
        
        if not path.is_file():
            return {"valid": False, "error": "Not a file"}
        
        # Check file size
        try:
            size = path.stat().st_size
            if size == 0:
                return {"valid": False, "error": "File is empty"}
        except OSError as e:
            return {"valid": False, "error": f"Cannot access file: {e}"}
        
        # Check if file is readable
        try:
            with open(file_path, 'rb') as f:
                f.read(1024)  # Try to read first 1KB
        except Exception as e:
            return {"valid": False, "error": f"Cannot read file: {e}"}
        
        return {"valid": True, "size": size}
    
    def validate_directory(self, directory_path: str) -> Dict[str, Any]:
        """Validate a directory for scanning."""
        path = Path(directory_path)
        
        if not path.exists():
            return {"valid": False, "error": "Directory does not exist"}
        
        if not path.is_dir():
            return {"valid": False, "error": "Not a directory"}
        
        # Check if directory is readable
        try:
            list(path.iterdir())
        except Exception as e:
            return {"valid": False, "error": f"Cannot read directory: {e}"}
        
        return {"valid": True}
