"""
Database wrapper for SQLite operations.
"""

import sqlite3
import logging
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger("retrovue.plex")


class Db:
    """SQLite database wrapper."""
    
    def __init__(self, db_path: str):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = str(Path(db_path).resolve())
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Connect to database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.conn:
            self.conn.close()
    
    def get_server(self, server_id: int) -> Optional[Dict[str, Any]]:
        """Get server by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM plex_servers WHERE id = ?", (server_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
