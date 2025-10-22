"""
Server management logic - reusable across GUI and CLI.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path


class ServerManager:
    """
    Manages Plex server CRUD operations.
    
    This is a thin facade over the database layer to provide
    a consistent API for both GUI and CLI.
    """
    
    def __init__(self, db_path: str = "./retrovue.db"):
        """
        Initialize server manager.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = str(Path(db_path).resolve())
    
    def _get_db(self):
        """Get database instance. Import lazily to avoid circular deps."""
        from retrovue.importers.plex.db import Db
        return Db(self.db_path)
    
    def list_servers(self) -> List[Dict[str, Any]]:
        """
        List all Plex servers.
        
        Returns:
            List of server dictionaries with keys: id, name, base_url, is_default, created_at, updated_at
        """
        with self._get_db() as db:
            return db.list_plex_servers()
    
    def add_server(self, name: str, base_url: str, token: str) -> int:
        """
        Add a new Plex server or update existing one.
        
        Args:
            name: Server name (unique)
            base_url: Server base URL (e.g., http://192.168.1.100:32400)
            token: Plex authentication token
            
        Returns:
            Server ID
            
        Raises:
            ValueError: If validation fails
        """
        # Validation
        if not name or not name.strip():
            raise ValueError("Server name cannot be empty")
        
        if not base_url or not base_url.strip():
            raise ValueError("Server URL cannot be empty")
        
        if not token or not token.strip():
            raise ValueError("Server token cannot be empty")
        
        # Basic URL validation
        base_url = base_url.strip()
        if not (base_url.startswith('http://') or base_url.startswith('https://')):
            raise ValueError("Server URL must start with http:// or https://")
        
        with self._get_db() as db:
            server_id = db.add_plex_server(name.strip(), base_url, token.strip())
            return server_id
    
    def delete_server(self, server_id: int) -> bool:
        """
        Delete a Plex server.
        
        Args:
            server_id: Server ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        with self._get_db() as db:
            rows_deleted = db.delete_plex_server(server_id)
            return rows_deleted > 0
    
    def get_server(self, server_id: int) -> Optional[Dict[str, Any]]:
        """
        Get server by ID.
        
        Args:
            server_id: Server ID
            
        Returns:
            Server dictionary or None if not found
        """
        with self._get_db() as db:
            return db.get_plex_server_by_id(server_id)
    
    def update_token(self, server_id: int, token: str) -> bool:
        """
        Update server token.
        
        Args:
            server_id: Server ID
            token: New token
            
        Returns:
            True if updated, False if not found
        """
        if not token or not token.strip():
            raise ValueError("Token cannot be empty")
        
        with self._get_db() as db:
            rows_updated = db.update_plex_server_token(server_id, token.strip())
            return rows_updated > 0
    
    def set_default(self, server_id: int) -> bool:
        """
        Set a server as default.
        
        Args:
            server_id: Server ID
            
        Returns:
            True if set as default, False if not found
        """
        # Verify server exists first
        if not self.get_server(server_id):
            return False
        
        with self._get_db() as db:
            db.set_default_server_by_id(server_id)
            return True

