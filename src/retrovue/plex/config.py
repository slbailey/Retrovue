"""
Configuration management for Plex integration.

Loads configuration from CLI args and optional .env file.
"""

import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path

# Centralized exit codes
OFFLINE_EXIT = 3


@dataclass
class PlexConfig:
    """Configuration for Plex integration."""
    
    # Plex connection
    base_url: str
    token: str
    
    # Database
    db_path: str = "./retrovue.db"
    
    # Server info
    server_name: str = "Plex Server"
    server_id: int = 1
    
    # Libraries to process
    libraries: List[int] = None
    
    # Content kinds to process
    kinds: List[str] = None
    
    # Operation flags
    dry_run: bool = False
    verbose: bool = False
    
    def __post_init__(self):
        """Post-initialization validation and defaults."""
        if self.libraries is None:
            self.libraries = []
        if self.kinds is None:
            self.kinds = ["movie", "episode"]
        
        # Ensure db_path is absolute
        self.db_path = str(Path(self.db_path).resolve())


def load_config_from_env() -> dict:
    """Load configuration from environment variables."""
    config = {}
    
    # Plex connection
    if base_url := os.getenv("PLEX_BASE_URL"):
        config["base_url"] = base_url
    if token := os.getenv("PLEX_TOKEN"):
        config["token"] = token
    
    # Database
    if db_path := os.getenv("RETROVUE_DB_PATH"):
        config["db_path"] = db_path
    
    # Server info
    if server_name := os.getenv("PLEX_SERVER_NAME"):
        config["server_name"] = server_name
    if server_id := os.getenv("PLEX_SERVER_ID"):
        try:
            config["server_id"] = int(server_id)
        except ValueError:
            pass
    
    return config


def create_config(
    base_url: str,
    token: str,
    db_path: str = "./retrovue.db",
    server_name: str = "Plex Server",
    server_id: int = 1,
    libraries: Optional[List[int]] = None,
    kinds: Optional[List[str]] = None,
    dry_run: bool = False,
    verbose: bool = False,
    use_env: bool = True
) -> PlexConfig:
    """
    Create configuration with optional environment variable overrides.
    
    Args:
        base_url: Plex server base URL
        token: Plex authentication token
        db_path: Path to SQLite database
        server_name: Name for the Plex server
        server_id: ID for the Plex server
        libraries: List of library IDs to process
        kinds: List of content kinds to process
        dry_run: Whether to run in dry-run mode
        verbose: Whether to enable verbose logging
        use_env: Whether to load from environment variables
    
    Returns:
        PlexConfig instance
    """
    # Start with provided values
    config_data = {
        "base_url": base_url,
        "token": token,
        "db_path": db_path,
        "server_name": server_name,
        "server_id": server_id,
        "libraries": libraries,
        "kinds": kinds,
        "dry_run": dry_run,
        "verbose": verbose
    }
    
    # Override with environment variables if requested
    if use_env:
        env_config = load_config_from_env()
        config_data.update(env_config)
    
    return PlexConfig(**config_data)


def resolve_server(db, server_name: Optional[str], server_id: Optional[int]) -> Dict[str, Any]:
    """
    Resolve server credentials from database.

    Resolution order:
    1. If server_name provided -> fetch by name
    2. Elif server_id provided -> fetch by id
    3. Else -> fetch the row with is_default=1
    4. Else raise ValueError with a friendly message

    Args:
        db: Database connection
        server_name: Server name to look up
        server_id: Server ID to look up

    Returns:
        Server dict with {id, name, base_url, token, is_default}

    Raises:
        ValueError: If no server can be resolved
    """
    server = None

    if server_name:
        server = db.get_plex_server_by_name(server_name)
        if not server:
            raise ValueError(f"Server '{server_name}' not found in database")
    elif server_id:
        server = db.get_plex_server_by_id(server_id)
        if not server:
            raise ValueError(f"Server ID {server_id} not found in database")
    else:
        # Try default server (is_default=1)
        cursor = db.execute("SELECT * FROM plex_servers WHERE is_default = 1")
        row = cursor.fetchone()
        if row:
            server = dict(row)
        else:
            raise ValueError(
                "No server specified and no default server set. Use --server-name, --server-id, or set a default server. "
                "Run 'servers list' to see available servers."
            )

    return server