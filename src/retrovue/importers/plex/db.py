"""
Database wrapper for SQLite operations.

Real sqlite3 implementation with explicit upserts and lookups for v1.2 schema.
"""

import sqlite3
import logging
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from .mapper import ContentItemData, MediaFileData

logger = logging.getLogger("retrovue.plex")


class Db:
    """SQLite database wrapper with explicit upserts and lookups."""
    
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
        """Connect to SQLite database."""
        try:
            # Direct sqlite3 connection without db_utils dependency
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys=ON")
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def execute(self, sql: str, params: Tuple = ()) -> sqlite3.Cursor:
        """
        Execute SQL statement.
        
        Args:
            sql: SQL statement
            params: Parameters for the statement
            
        Returns:
            SQLite cursor
        """
        return self.conn.execute(sql, params)
    
    def commit(self):
        """Commit transaction."""
        self.conn.commit()
    
    def rollback(self):
        """Rollback transaction."""
        self.conn.rollback()
    
    # Server operations
    
    def upsert_server(self, name: str, base_url: str) -> int:
        """
        Upsert a Plex server.
        
        Args:
            name: Server name
            base_url: Server base URL
            
        Returns:
            Server ID
        """
        logger.debug(f"Upserting server: {name}")
        
        # Check if server exists
        cursor = self.execute(
            "SELECT id FROM plex_servers WHERE name = ? AND base_url = ?",
            (name, base_url)
        )
        existing = cursor.fetchone()
        
        if existing:
            server_id = existing['id']
            logger.debug(f"Server exists with ID: {server_id}")
        else:
            # Insert new server
            cursor = self.execute(
                "INSERT INTO plex_servers (name, base_url) VALUES (?, ?)",
                (name, base_url)
            )
            server_id = cursor.lastrowid
            logger.info(f"Created new server with ID: {server_id}")
        
        self.commit()
        return server_id
    
    def get_server(self, server_id: int) -> Optional[Dict[str, Any]]:
        """
        Get server by ID.
        
        Args:
            server_id: Server ID
            
        Returns:
            Server data or None
        """
        cursor = self.execute("SELECT * FROM plex_servers WHERE id = ?", (server_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # Library operations
    
    def upsert_library(
        self, 
        server_id: int, 
        plex_library_key: str, 
        title: str, 
        library_type: str
    ) -> int:
        """
        Upsert a Plex library.
        
        Args:
            server_id: Server ID
            plex_library_key: Plex library key
            title: Library title
            library_type: Library type (movie, show, etc.)
            
        Returns:
            Library ID
        """
        logger.debug(f"Upserting library: {title}")
        
        # Check if library exists
        cursor = self.execute(
            "SELECT id FROM libraries WHERE server_id = ? AND plex_library_key = ?",
            (server_id, plex_library_key)
        )
        existing = cursor.fetchone()
        
        if existing:
            library_id = existing['id']
            logger.debug(f"Library exists with ID: {library_id}")
        else:
            # Insert new library
            cursor = self.execute(
                "INSERT INTO libraries (server_id, plex_library_key, title, library_type) VALUES (?, ?, ?, ?)",
                (server_id, plex_library_key, title, library_type)
            )
            library_id = cursor.lastrowid
            logger.info(f"Created new library with ID: {library_id}")
        
        self.commit()
        return library_id
    
    def get_library(self, library_id: int) -> Optional[Dict[str, Any]]:
        """
        Get library by ID.
        
        Args:
            library_id: Library ID
            
        Returns:
            Library data or None
        """
        cursor = self.execute("SELECT * FROM libraries WHERE id = ?", (library_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # Show operations
    
    def upsert_show(
        self, 
        server_id: int, 
        library_id: int, 
        plex_rating_key: str, 
        title: str, 
        year: Optional[int] = None,
        originally_available_at: Optional[str] = None,
        summary: Optional[str] = None,
        studio: Optional[str] = None,
        artwork_url: Optional[str] = None
    ) -> int:
        """
        Upsert a TV show.
        
        Args:
            server_id: Server ID
            library_id: Library ID
            plex_rating_key: Plex rating key
            title: Show title
            year: Show year
            originally_available_at: Original air date
            summary: Show summary
            studio: Production studio
            artwork_url: Artwork URL
            
        Returns:
            Show ID
        """
        logger.debug(f"Upserting show: {title}")
        
        # Check if show exists
        cursor = self.execute(
            "SELECT id FROM shows WHERE server_id = ? AND library_id = ? AND plex_rating_key = ?",
            (server_id, library_id, plex_rating_key)
        )
        existing = cursor.fetchone()
        
        if existing:
            show_id = existing['id']
            logger.debug(f"Show exists with ID: {show_id}")
        else:
            # Insert new show
            cursor = self.execute(
                """INSERT INTO shows 
                   (server_id, library_id, plex_rating_key, title, year, originally_available_at, summary, studio, artwork_url)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (server_id, library_id, plex_rating_key, title, year, originally_available_at, summary, studio, artwork_url)
            )
            show_id = cursor.lastrowid
            logger.info(f"Created new show with ID: {show_id}")
        
        self.commit()
        return show_id
    
    # Season operations
    
    def upsert_season(
        self, 
        show_id: int, 
        season_number: int, 
        plex_rating_key: Optional[str] = None,
        title: Optional[str] = None
    ) -> int:
        """
        Upsert a TV season.
        
        Args:
            show_id: Show ID
            season_number: Season number
            plex_rating_key: Plex rating key
            title: Season title
            
        Returns:
            Season ID
        """
        logger.debug(f"Upserting season: {season_number}")
        
        # Check if season exists
        cursor = self.execute(
            "SELECT id FROM seasons WHERE show_id = ? AND season_number = ?",
            (show_id, season_number)
        )
        existing = cursor.fetchone()
        
        if existing:
            season_id = existing['id']
            logger.debug(f"Season exists with ID: {season_id}")
        else:
            # Insert new season
            cursor = self.execute(
                "INSERT INTO seasons (show_id, season_number, plex_rating_key, title) VALUES (?, ?, ?, ?)",
                (show_id, season_number, plex_rating_key, title)
            )
            season_id = cursor.lastrowid
            logger.info(f"Created new season with ID: {season_id}")
        
        self.commit()
        return season_id
    
    # Content item operations (v1.2.3 schema)
    
    # Media file operations
    
    def upsert_media_file(
        self, 
        media_file: MediaFileData,
        server_id: int, 
        library_id: int, 
        content_item_id: int
    ) -> int:
        """
        Upsert a media file using the v1.2.3 schema.
        
        Args:
            media_file: MediaFileData object
            server_id: Server ID
            library_id: Library ID
            content_item_id: Content item ID
            
        Returns:
            Media file ID
        """
        import time
        current_time = int(time.time())
        
        cursor = self.execute("""
            INSERT INTO media_files(
                server_id, library_id, content_item_id, plex_rating_key, file_path,
                size_bytes, container, video_codec, audio_codec, width, height, bitrate,
                frame_rate, channels, updated_at_plex, first_seen_at, last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(server_id, file_path) DO UPDATE SET
                content_item_id=excluded.content_item_id,
                size_bytes=excluded.size_bytes,
                container=excluded.container,
                video_codec=excluded.video_codec,
                audio_codec=excluded.audio_codec,
                width=excluded.width,
                height=excluded.height,
                bitrate=excluded.bitrate,
                frame_rate=excluded.frame_rate,
                channels=excluded.channels,
                updated_at_plex=excluded.updated_at_plex,
                last_seen_at=excluded.last_seen_at
        """, (
            server_id,
            library_id,
            content_item_id,
            media_file.plex_rating_key,
            media_file.file_path,
            media_file.size_bytes,
            media_file.container,
            media_file.video_codec,
            media_file.audio_codec,
            media_file.width,
            media_file.height,
            media_file.bitrate,
            media_file.frame_rate,
            media_file.channels,
            media_file.updated_at_plex,
            current_time,  # first_seen_at
            current_time   # last_seen_at
        ))
        
        media_file_id = cursor.lastrowid
        self.commit()
        return media_file_id
    
    
    # Editorial operations
    
    def upsert_editorial(self, content_item_id: int, editorial: Dict[str, Any]) -> None:
        """
        Upsert editorial data.
        
        Args:
            content_item_id: Content item ID
            editorial: Editorial data dictionary
        """
        logger.debug(f"Upserting editorial for content item {content_item_id}")
        
        # Check if editorial exists
        cursor = self.execute(
            "SELECT 1 FROM content_editorial WHERE content_item_id = ?",
            (content_item_id,)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            self.execute(
                """UPDATE content_editorial SET 
                   source_name = ?, source_payload_json = ?, original_title = ?, original_synopsis = ?,
                   override_title = ?, override_synopsis = ?, override_updated_at = ?
                   WHERE content_item_id = ?""",
                (editorial["source_name"], editorial["source_payload_json"], editorial["original_title"],
                 editorial["original_synopsis"], editorial.get("override_title"), editorial.get("override_synopsis"),
                 editorial.get("override_updated_at"), content_item_id)
            )
            logger.debug(f"Updated editorial for content item {content_item_id}")
        else:
            # Insert new
            self.execute(
                """INSERT INTO content_editorial 
                   (content_item_id, source_name, source_payload_json, original_title, original_synopsis,
                    override_title, override_synopsis, override_updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (content_item_id, editorial["source_name"], editorial["source_payload_json"],
                 editorial["original_title"], editorial["original_synopsis"], editorial.get("override_title"),
                 editorial.get("override_synopsis"), editorial.get("override_updated_at"))
            )
            logger.info(f"Created editorial for content item {content_item_id}")
        
        self.commit()
    
    # Tag operations
    
    def upsert_tag(self, content_item_id: int, tag: Dict[str, Any]) -> None:
        """
        Upsert a content tag.
        
        Args:
            content_item_id: Content item ID
            tag: Tag data dictionary
        """
        logger.debug(f"Upserting tag: {tag['namespace']}:{tag['key']}={tag['value']}")
        
        # Check if tag exists
        cursor = self.execute(
            "SELECT 1 FROM content_tags WHERE content_item_id = ? AND namespace = ? AND key = ?",
            (content_item_id, tag["namespace"], tag["key"])
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update existing
            self.execute(
                "UPDATE content_tags SET value = ? WHERE content_item_id = ? AND namespace = ? AND key = ?",
                (tag["value"], content_item_id, tag["namespace"], tag["key"])
            )
            logger.debug(f"Updated tag: {tag['namespace']}:{tag['key']}={tag['value']}")
        else:
            # Insert new
            self.execute(
                "INSERT INTO content_tags (content_item_id, namespace, key, value) VALUES (?, ?, ?, ?)",
                (content_item_id, tag["namespace"], tag["key"], tag["value"])
            )
            logger.info(f"Created tag: {tag['namespace']}:{tag['key']}={tag['value']}")
        
        self.commit()
    
    # Utility operations
    
    # Plex Server Management
    
    def add_plex_server(self, name: str, base_url: str, token: str) -> int:
        """
        Add or update a Plex server.
        
        Args:
            name: Server name (unique)
            base_url: Server base URL
            token: Server authentication token
            
        Returns:
            Server ID
        """
        cursor = self.execute("""
            INSERT INTO plex_servers (name, base_url, token)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET 
                base_url=excluded.base_url,
                token=excluded.token,
                updated_at=datetime('now')
        """, (name, base_url, token))
        
        server_id = cursor.lastrowid
        self.commit()
        return server_id
    
    def get_plex_server_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get Plex server by name.
        
        Args:
            name: Server name
            
        Returns:
            Server dict or None if not found
        """
        cursor = self.execute("""
            SELECT * FROM plex_servers WHERE name = ?
        """, (name,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_plex_server_by_id(self, server_id: int) -> Optional[Dict[str, Any]]:
        """
        Get Plex server by ID.
        
        Args:
            server_id: Server ID
            
        Returns:
            Server dict or None if not found
        """
        cursor = self.execute("""
            SELECT * FROM plex_servers WHERE id = ?
        """, (server_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def list_plex_servers(self) -> List[Dict[str, Any]]:
        """
        List all Plex servers.
        
        Returns:
            List of server dicts, ordered by name
        """
        cursor = self.execute("""
            SELECT id, name, base_url, is_default, created_at, updated_at
            FROM plex_servers
            ORDER BY name ASC
        """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def set_default_server_by_id(self, server_id: int) -> None:
        """
        Set exactly one server as default (flip all others to 0).
        
        Args:
            server_id: Server ID to set as default
        """
        # First, set all servers to not default
        self.execute("UPDATE plex_servers SET is_default = 0")
        
        # Then set the specified server as default
        self.execute("""
            UPDATE plex_servers 
            SET is_default = 1, updated_at = datetime('now')
            WHERE id = ?
        """, (server_id,))
        
        self.commit()
    
    def set_default_server_by_name(self, name: str) -> None:
        """
        Set exactly one server as default by name (flip all others to 0).
        
        Args:
            name: Server name to set as default
        """
        # First, set all servers to not default
        self.execute("UPDATE plex_servers SET is_default = 0")
        
        # Then set the specified server as default
        self.execute("""
            UPDATE plex_servers 
            SET is_default = 1, updated_at = datetime('now')
            WHERE name = ?
        """, (name,))
        
        self.commit()
    
    def delete_plex_server(self, server_id: int) -> int:
        """
        Delete a Plex server.
        
        Args:
            server_id: Server ID to delete
            
        Returns:
            Number of rows deleted
        """
        cursor = self.execute("""
            DELETE FROM plex_servers WHERE id = ?
        """, (server_id,))
        
        rows_deleted = cursor.rowcount
        self.commit()
        return rows_deleted
    
    def update_plex_server_token(self, server_id: int, token: str) -> int:
        """
        Update a Plex server's token.
        
        Args:
            server_id: Server ID
            token: New token
            
        Returns:
            Number of rows updated
        """
        cursor = self.execute("""
            UPDATE plex_servers 
            SET token = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (token, server_id))
        
        rows_updated = cursor.rowcount
        self.commit()
        return rows_updated
    
    def set_default_server_name(self, name: str) -> None:
        """
        Set the default server name in system config.
        
        Args:
            name: Server name to set as default
        """
        self.execute("""
            INSERT INTO system_config(key, value, description)
            VALUES ('default_plex_server_name', ?, 'Optional default server name')
            ON CONFLICT(key) DO UPDATE SET 
                value=excluded.value, 
                updated_at=datetime('now')
        """, (name,))
        
        self.commit()
    
    def get_default_server_name(self) -> Optional[str]:
        """
        Get the default server name from system config.
        
        Returns:
            Default server name or None if not set
        """
        cursor = self.execute("""
            SELECT value FROM system_config 
            WHERE key = 'default_plex_server_name'
        """)
        
        row = cursor.fetchone()
        return row['value'] if row and row['value'] else None

    # Ingest helper methods
    
    def get_or_create_library(self, server_id: int, plex_library_key: str, title: str, library_type: str) -> int:
        """
        Get or create a library.
        
        Args:
            server_id: Server ID
            plex_library_key: Plex library key
            title: Library title
            library_type: Library type
            
        Returns:
            Library ID
        """
        # First try to get existing library
        cursor = self.execute("""
            SELECT id FROM libraries 
            WHERE server_id = ? AND plex_library_key = ?
        """, (server_id, plex_library_key))
        
        existing = cursor.fetchone()
        if existing:
            return existing[0]
        
        # Create new library
        cursor = self.execute("""
            INSERT INTO libraries (server_id, plex_library_key, title, library_type)
            VALUES (?, ?, ?, ?)
        """, (server_id, plex_library_key, title, library_type))
        
        library_id = cursor.lastrowid
        self.commit()
        return library_id
    
    def get_or_create_show(self, server_id: int, library_id: int, plex_rating_key: str, title: str, year: Optional[int] = None, artwork_url: Optional[str] = None) -> int:
        """
        Get or create a show.
        
        Args:
            server_id: Server ID
            library_id: Library ID
            plex_rating_key: Plex rating key
            title: Show title
            year: Show year
            artwork_url: Artwork URL
            
        Returns:
            Show ID
        """
        # First try to get existing show
        cursor = self.execute("""
            SELECT id FROM shows 
            WHERE server_id = ? AND library_id = ? AND plex_rating_key = ?
        """, (server_id, library_id, plex_rating_key))
        
        existing = cursor.fetchone()
        if existing:
            return existing[0]
        
        # Create new show
        print(f"DEBUG: Inserting show with server_id={server_id}, library_id={library_id}, plex_rating_key={plex_rating_key}, title={title}")
        cursor = self.execute("""
            INSERT INTO shows (server_id, library_id, plex_rating_key, title, year, artwork_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (server_id, library_id, plex_rating_key, title, year, artwork_url))
        
        show_id = cursor.lastrowid
        self.commit()
        return show_id
    
    def get_or_create_season(self, show_id: int, season_number: int, plex_rating_key: Optional[str] = None, title: Optional[str] = None) -> int:
        """
        Get or create a season.
        
        Args:
            show_id: Show ID
            season_number: Season number
            plex_rating_key: Plex rating key
            title: Season title
            
        Returns:
            Season ID
        """
        # First try to get existing season
        cursor = self.execute("""
            SELECT id FROM seasons 
            WHERE show_id = ? AND season_number = ?
        """, (show_id, season_number))
        
        existing = cursor.fetchone()
        if existing:
            return existing[0]
        
        # Create new season
        cursor = self.execute("""
            INSERT INTO seasons (show_id, season_number, plex_rating_key, title)
            VALUES (?, ?, ?, ?)
        """, (show_id, season_number, plex_rating_key, title))
        
        season_id = cursor.lastrowid
        self.commit()
        return season_id
    
    def upsert_content_item(self, content_item, show_id: Optional[int] = None, season_id: Optional[int] = None, media_files: List[MediaFileData] = None) -> int:
        """
        Upsert a content item.
        
        Args:
            content_item: ContentItemData object
            show_id: Optional show ID
            season_id: Optional season ID
            media_files: List of MediaFileData objects
            
        Returns:
            Content item ID
        """
        # First try to get existing content item by media file path (most reliable)
        if media_files and media_files[0].file_path:
            # Simplified: content_items directly references media_files via content_item_id
            cursor = self.execute("""
                SELECT ci.id FROM content_items ci
                JOIN media_files mf ON ci.id = mf.content_item_id
                WHERE mf.local_file_path = ?
            """, (media_files[0].file_path,))
            
            existing = cursor.fetchone()
            if existing:
                content_item_id = existing[0]
                # Update existing content item
                cursor = self.execute("""
                    UPDATE content_items SET
                        title=?, synopsis=?, duration_ms=?, rating_system=?, rating_code=?,
                        is_kids_friendly=?, metadata_updated_at=?, season_id=?,
                        updated_at=datetime('now')
                    WHERE id = ?
                """, (
                    content_item.title,
                    content_item.synopsis,
                    content_item.duration_ms,
                    content_item.rating_system,
                    content_item.rating_code,
                    content_item.is_kids_friendly,
                    content_item.metadata_updated_at,
                    season_id,
                    content_item_id
                ))
                self.commit()
                return content_item_id
        
        # Fallback to other methods if no media file path
        if show_id and content_item.season_number is not None and content_item.episode_number is not None:
            # Episode: check by show_id, season_number, episode_number
            cursor = self.execute("""
                SELECT id FROM content_items 
                WHERE show_id = ? AND season_number = ? AND episode_number = ?
            """, (show_id, content_item.season_number, content_item.episode_number))
        elif content_item.kind == 'movie':
            # Movie: check by title and kind (no show_id)
            cursor = self.execute("""
                SELECT id FROM content_items 
                WHERE kind = ? AND title = ? AND show_id IS NULL
            """, (content_item.kind, content_item.title))
        elif show_id:
            # Other content with show: check by show_id, kind, and title
            cursor = self.execute("""
                SELECT id FROM content_items 
                WHERE show_id = ? AND kind = ? AND title = ?
            """, (show_id, content_item.kind, content_item.title))
        else:
            # Other content without show: check by kind and title only
            cursor = self.execute("""
                SELECT id FROM content_items 
                WHERE kind = ? AND title = ? AND show_id IS NULL
            """, (content_item.kind, content_item.title))
        
        existing = cursor.fetchone()
        if existing:
            # Update existing content item
            cursor = self.execute("""
                UPDATE content_items SET
                    synopsis=?, duration_ms=?, rating_system=?, rating_code=?,
                    is_kids_friendly=?, metadata_updated_at=?, season_id=?,
                    updated_at=datetime('now')
                WHERE id = ?
            """, (
                content_item.synopsis,
                content_item.duration_ms,
                content_item.rating_system,
                content_item.rating_code,
                content_item.is_kids_friendly,
                content_item.metadata_updated_at,
                season_id,
                existing[0]
            ))
            content_item_id = existing[0]
            self.commit()
            return content_item_id
        
        # Insert new content item
        cursor = self.execute("""
            INSERT INTO content_items(
                kind, title, synopsis, duration_ms, rating_system, rating_code,
                is_kids_friendly, metadata_updated_at, show_id, season_id,
                season_number, episode_number
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            content_item.kind,
            content_item.title,
            content_item.synopsis,
            content_item.duration_ms,
            content_item.rating_system,
            content_item.rating_code,
            content_item.is_kids_friendly,
            content_item.metadata_updated_at,
            show_id,
            season_id,
            content_item.season_number,
            content_item.episode_number
        ))
        
        content_item_id = cursor.lastrowid
        self.commit()
        return content_item_id
    
    def upsert_media_file(self, media_file: MediaFileData, server_id: int, library_id: int, content_item_id: int, content_kind: str) -> int:
        """
        Upsert a media file.
        
        Args:
            media_file: MediaFileData object
            server_id: Server ID
            library_id: Library ID
            content_item_id: Content item ID
            content_kind: Content kind ('movie' or 'episode')
            
        Returns:
            Media file ID
        """
        # Check if media file already exists by plex path
        cursor = self.execute("""
            SELECT id FROM media_files 
            WHERE plex_file_path = ?
        """, (media_file.plex_path,))
        
        existing = cursor.fetchone()
        if existing:
            # Update existing media file
            cursor = self.execute("""
                UPDATE media_files SET
                    local_file_path=?, file_size_bytes=?, video_codec=?, audio_codec=?,
                    width=?, height=?, duration_ms=?, container=?, content_item_id=?
                WHERE id = ?
            """, (
                media_file.file_path,
                media_file.size_bytes,
                media_file.video_codec,
                media_file.audio_codec,
                media_file.width,
                media_file.height,
                getattr(media_file, 'duration_ms', None),
                media_file.container,
                content_item_id,
                existing[0]
            ))
            media_file_id = existing[0]
            self.commit()
        else:
            # Insert new media file
            cursor = self.execute("""
                INSERT INTO media_files(
                    content_item_id, plex_file_path, local_file_path, file_size_bytes, video_codec,
                    audio_codec, width, height, duration_ms, container
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                content_item_id,
                media_file.plex_path,
                media_file.file_path,
                media_file.size_bytes,
                media_file.video_codec,
                media_file.audio_codec,
                media_file.width,
                media_file.height,
                getattr(media_file, 'duration_ms', None),
                media_file.container
            ))
            
            media_file_id = cursor.lastrowid
            self.commit()
        
        return media_file_id
    
    def link_content_item_file(self, content_item_id: int, media_file_id: int, role: str = 'primary') -> None:
        """
        Link a content item to a media file.
        
        Args:
            content_item_id: Content item ID
            media_file_id: Media file ID
            role: Link role (default: 'primary')
        """
        self.execute("""
            INSERT INTO content_item_files (content_item_id, media_file_id, role)
            VALUES (?, ?, ?)
            ON CONFLICT(content_item_id, media_file_id, role) DO NOTHING
        """, (content_item_id, media_file_id, role))
        
        self.commit()
    
    def upsert_editorial(self, content_item_id: int, editorial) -> None:
        """
        Upsert editorial data.
        
        Args:
            content_item_id: Content item ID
            editorial: EditorialData object
        """
        self.execute("""
            INSERT INTO content_editorial(
                content_item_id, source_name, source_payload_json,
                original_title, original_synopsis
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(content_item_id) DO UPDATE SET
                source_name=excluded.source_name,
                source_payload_json=excluded.source_payload_json,
                original_title=excluded.original_title,
                original_synopsis=excluded.original_synopsis
        """, (
            content_item_id,
            editorial.source_name,
            editorial.source_payload_json,
            editorial.original_title,
            editorial.original_synopsis
        ))
        
        self.commit()
    
    def upsert_tag(self, content_item_id: int, tag) -> None:
        """
        Upsert a content tag.
        
        Args:
            content_item_id: Content item ID
            tag: TagRow object
        """
        self.execute("""
            INSERT INTO content_tags (content_item_id, namespace, key, value)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(content_item_id, namespace, key) DO UPDATE SET
                value=excluded.value
        """, (content_item_id, tag.namespace, tag.key, tag.value))
        
        self.commit()
    
    # Library sync management methods
    
    def set_library_sync_enabled(self, library_id: int, enabled: bool) -> int:
        """
        Enable or disable sync for a library.
        
        Args:
            library_id: Library ID
            enabled: Whether to enable sync
            
        Returns:
            Number of rows updated
        """
        cursor = self.execute("""
            UPDATE libraries 
            SET sync_enabled = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (1 if enabled else 0, library_id))
        
        rows_updated = cursor.rowcount
        self.commit()
        return rows_updated
    
    def set_library_sync(self, library_id: int, enabled: bool) -> int:
        """
        Enable/disable a single library for ingest.
        Returns the number of rows updated (0 if not found).
        """
        return self.set_library_sync_enabled(library_id, enabled)
    
    def set_all_libraries_sync(self, enabled: bool, server_id: Optional[int] = None) -> int:
        """
        Enable/disable all libraries, optionally scoped to a server_id.
        Returns number of rows updated.
        """
        return self.set_all_libraries_sync_enabled(enabled, server_id)
    
    def set_all_libraries_sync_enabled(self, enabled: bool, server_id: Optional[int] = None) -> int:
        """
        Enable/disable all libraries; if server_id given, filter by server.
        
        Args:
            enabled: Whether to enable sync
            server_id: Optional server ID to filter by
            
        Returns:
            Number of rows updated
        """
        if server_id:
            cursor = self.execute("""
                UPDATE libraries 
                SET sync_enabled = ?, updated_at = datetime('now')
                WHERE server_id = ?
            """, (1 if enabled else 0, server_id))
        else:
            cursor = self.execute("""
                UPDATE libraries 
                SET sync_enabled = ?, updated_at = datetime('now')
            """, (1 if enabled else 0,))
        
        rows_updated = cursor.rowcount
        self.commit()
        return rows_updated
    
    def list_libraries(self, server_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List libraries with sync status.
        
        Args:
            server_id: Optional server ID to filter by
            
        Returns:
            List of library dictionaries
        """
        if server_id:
            cursor = self.execute("""
                SELECT id, server_id, plex_library_key, title, library_type,
                       sync_enabled, last_full_sync_epoch, last_incremental_sync_epoch,
                       created_at, updated_at, plex_path
                FROM libraries
                WHERE server_id = ?
                ORDER BY title
            """, (server_id,))
        else:
            cursor = self.execute("""
                SELECT id, server_id, plex_library_key, title, library_type,
                       sync_enabled, last_full_sync_epoch, last_incremental_sync_epoch,
                       created_at, updated_at, plex_path
                FROM libraries
                ORDER BY title
            """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_library(self, library_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a library by ID.
        
        Args:
            library_id: Library ID
            
        Returns:
            Library dictionary or None
        """
        cursor = self.execute("""
            SELECT id, server_id, plex_library_key, title, library_type,
                   sync_enabled, last_full_sync_epoch, last_incremental_sync_epoch,
                   created_at, updated_at
            FROM libraries
            WHERE id = ?
        """, (library_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_library_by_key(self, server_id: int, plex_library_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a library by server ID and Plex library key.
        
        Args:
            server_id: Server ID
            plex_library_key: Plex library key
            
        Returns:
            Library dictionary or None
        """
        cursor = self.execute("""
            SELECT id, server_id, plex_library_key, title, library_type,
                   sync_enabled, last_full_sync_epoch, last_incremental_sync_epoch,
                   created_at, updated_at
            FROM libraries
            WHERE server_id = ? AND plex_library_key = ?
        """, (server_id, plex_library_key))
        
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def set_library_last_full(self, library_id: int, epoch: int) -> None:
        """
        Set the last full sync epoch for a library.
        
        Args:
            library_id: Library ID
            epoch: Epoch timestamp
        """
        self.execute("""
            UPDATE libraries 
            SET last_full_sync_epoch = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (epoch, library_id))
        
        self.commit()
    
    def set_library_last_incremental(self, library_id: int, epoch: int) -> None:
        """
        Set the last incremental sync epoch for a library.
        
        Args:
            library_id: Library ID
            epoch: Epoch timestamp
        """
        self.execute("""
            UPDATE libraries 
            SET last_incremental_sync_epoch = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (epoch, library_id))
        
        self.commit()
    
    def list_sync_enabled_library_keys(self, server_id: int) -> List[int]:
        """
        Get list of sync-enabled library keys for a server.
        
        Args:
            server_id: Server ID
            
        Returns:
            List of library keys (as integers)
        """
        cursor = self.execute("""
            SELECT plex_library_key
            FROM libraries
            WHERE server_id = ? AND sync_enabled = 1
            ORDER BY plex_library_key
        """, (server_id,))
        
        return [int(row['plex_library_key']) for row in cursor.fetchall()]
    
    def upsert_library(self, server_id: int, plex_library_key: int, title: str, library_type: str, plex_path: str = None) -> int:
        """
        Upsert one library (idempotent).
        
        Args:
            server_id: Server ID
            plex_library_key: Plex library key
            title: Library title
            library_type: Library type
            plex_path: Plex library file system path
            
        Returns:
            Library ID
        """
        cursor = self.execute("""
            INSERT INTO libraries(server_id, plex_library_key, title, library_type, sync_enabled, plex_path)
            VALUES (?, ?, ?, ?, COALESCE(
                (SELECT sync_enabled FROM libraries WHERE server_id=? AND plex_library_key=?), 1), ?)
            ON CONFLICT(server_id, plex_library_key) DO UPDATE SET
                title=excluded.title,
                library_type=excluded.library_type,
                plex_path=excluded.plex_path,
                updated_at=datetime('now')
        """, (server_id, plex_library_key, title, library_type, server_id, plex_library_key, plex_path))
        
        library_id = cursor.lastrowid
        self.commit()
        return library_id
    
    def delete_library(self, library_id: int) -> int:
        """
        Delete one library by internal ID.
        
        Args:
            library_id: Library ID to delete
            
        Returns:
            Number of rows affected (0 or 1)
        """
        cursor = self.execute("DELETE FROM libraries WHERE id = ?", (library_id,))
        rows_affected = cursor.rowcount
        self.commit()
        return rows_affected
    
    def delete_all_libraries_for_server(self, server_id: int) -> int:
        """
        Delete all libraries for a server.
        
        Args:
            server_id: Server ID
            
        Returns:
            Number of rows affected
        """
        cursor = self.execute("DELETE FROM libraries WHERE server_id = ?", (server_id,))
        rows_affected = cursor.rowcount
        self.commit()
        return rows_affected
    
    def has_path_mappings(self, server_id: int, library_id: int) -> bool:
        """
        Check if a library has path mappings.
        
        Args:
            server_id: Server ID
            library_id: Library ID
            
        Returns:
            True if library has path mappings, False otherwise
        """
        cursor = self.execute("""
            SELECT COUNT(*) FROM path_mappings 
            WHERE server_id = ? AND library_id = ?
        """, (server_id, library_id))
        
        count = cursor.fetchone()[0]
        return count > 0
    
    def get_libraries_without_mappings(self, server_id: int) -> List[Dict]:
        """
        Get libraries that don't have path mappings.
        
        Args:
            server_id: Server ID
            
        Returns:
            List of libraries without path mappings
        """
        cursor = self.execute("""
            SELECT l.id, l.title, l.library_type, l.plex_path
            FROM libraries l
            LEFT JOIN path_mappings pm ON l.server_id = pm.server_id AND l.id = pm.library_id
            WHERE l.server_id = ? AND l.sync_enabled = 1 AND pm.id IS NULL
        """, (server_id,))
        
        return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    
    def get_path_mappings(self, server_id: int, library_id: int) -> List[Dict[str, Any]]:
        """
        Get path mappings for a server and library.
        
        Args:
            server_id: Server ID
            library_id: Library ID
            
        Returns:
            List of mapping dictionaries with keys: id, plex_path, local_path
        """
        cursor = self.execute("""
            SELECT id, plex_path, local_path
            FROM path_mappings
            WHERE server_id = ? AND library_id = ?
            ORDER BY id
        """, (server_id, library_id))
        
        return [
            {
                'id': row['id'],
                'plex_path': row['plex_path'],
                'local_path': row['local_path']
            }
            for row in cursor.fetchall()
        ]
    
    def insert_path_mapping(
        self, 
        server_id: int, 
        library_id: int, 
        plex_path: str, 
        local_path: str
    ) -> int:
        """
        Insert a new path mapping.
        
        Args:
            server_id: Server ID
            library_id: Library ID
            plex_path: Plex path prefix
            local_path: Local path prefix
            
        Returns:
            ID of the inserted mapping
        """
        cursor = self.execute("""
            INSERT INTO path_mappings (server_id, library_id, plex_path, local_path)
            VALUES (?, ?, ?, ?)
        """, (server_id, library_id, plex_path, local_path))
        
        mapping_id = cursor.lastrowid
        self.commit()
        return mapping_id
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get database statistics.
        
        Returns:
            Dictionary of table counts
        """
        stats = {}
        
        tables = [
            'plex_servers', 'libraries', 'shows', 'seasons', 'content_items',
            'media_files', 'content_item_files', 'content_editorial', 'content_tags',
            'path_mappings'
        ]
        
        for table in tables:
            cursor = self.execute(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = cursor.fetchone()['count']
        
        return stats
    
    # Content browsing methods
    
    def get_content_items(self, library_id: Optional[int] = None, kind: Optional[str] = None, 
                         search: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get content items with optional filtering.
        
        Args:
            library_id: Optional library ID to filter by
            kind: Optional content kind to filter by (movie, episode, etc.)
            search: Optional search term for title/synopsis
            limit: Maximum number of items to return
            
        Returns:
            List of content item dictionaries
        """
        query = """
            SELECT ci.id, ci.kind, ci.title, ci.synopsis, ci.duration_ms, 
                   ci.rating_system, ci.rating_code, ci.is_kids_friendly,
                   ci.season_number, ci.episode_number, ci.created_at, ci.updated_at,
                   s.title as show_title, s.year as show_year,
                   l.title as library_title, l.library_type
            FROM content_items ci
            LEFT JOIN shows s ON ci.show_id = s.id
            LEFT JOIN libraries l ON s.library_id = l.id
            WHERE 1=1
        """
        params = []
        
        if library_id:
            query += " AND l.id = ?"
            params.append(library_id)
        
        if kind and kind != "All":
            query += " AND ci.kind = ?"
            params.append(kind.lower())
        
        if search:
            query += " AND (ci.title LIKE ? OR ci.synopsis LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        query += " ORDER BY ci.title LIMIT ?"
        params.append(limit)
        
        cursor = self.execute(query, params)
        return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    
    def get_shows(self, library_id: Optional[int] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get TV shows with optional filtering.
        
        Args:
            library_id: Optional library ID to filter by
            search: Optional search term for title
            
        Returns:
            List of show dictionaries
        """
        query = """
            SELECT s.id, s.title, s.year, s.artwork_url, s.created_at, s.updated_at,
                   l.title as library_title, l.library_type,
                   COUNT(ci.id) as episode_count,
                   COUNT(DISTINCT se.id) as season_count
            FROM shows s
            LEFT JOIN libraries l ON s.library_id = l.id
            LEFT JOIN content_items ci ON s.id = ci.show_id
            LEFT JOIN seasons se ON s.id = se.show_id
            WHERE 1=1
        """
        params = []
        
        if library_id:
            query += " AND l.id = ?"
            params.append(library_id)
        
        if search:
            query += " AND s.title LIKE ?"
            params.append(f"%{search}%")
        
        query += " GROUP BY s.id ORDER BY s.title"
        
        cursor = self.execute(query, params)
        return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    
    def get_seasons(self, show_id: int) -> List[Dict[str, Any]]:
        """
        Get seasons for a specific show.
        
        Args:
            show_id: Show ID
            
        Returns:
            List of season dictionaries
        """
        query = """
            SELECT se.id, se.season_number, se.title, se.created_at, se.updated_at,
                   COUNT(ci.id) as episode_count
            FROM seasons se
            LEFT JOIN content_items ci ON se.id = ci.season_id
            WHERE se.show_id = ?
            GROUP BY se.id
            ORDER BY se.season_number
        """
        
        cursor = self.execute(query, (show_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_episodes(self, show_id: int, season_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get episodes for a show or specific season.
        
        Args:
            show_id: Show ID
            season_id: Optional season ID to filter by
            
        Returns:
            List of episode dictionaries
        """
        query = """
            SELECT ci.id, ci.title, ci.synopsis, ci.duration_ms, ci.episode_number,
                   ci.rating_system, ci.rating_code, ci.created_at, ci.updated_at,
                   se.season_number
            FROM content_items ci
            LEFT JOIN seasons se ON ci.season_id = se.id
            WHERE ci.show_id = ? AND ci.kind = 'episode'
        """
        params = [show_id]
        
        if season_id:
            query += " AND ci.season_id = ?"
            params.append(season_id)
        
        query += " ORDER BY se.season_number, ci.episode_number"
        
        cursor = self.execute(query, params)
        return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    
    def get_movies(self, library_id: Optional[int] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get movies with optional filtering.
        
        Args:
            library_id: Optional library ID to filter by
            search: Optional search term for title
            
        Returns:
            List of movie dictionaries
        """
        query = """
            SELECT ci.id, ci.title, ci.synopsis, ci.duration_ms, ci.rating_system, 
                   ci.rating_code, ci.is_kids_friendly, ci.created_at, ci.updated_at,
                   l.title as library_title
            FROM content_items ci
            LEFT JOIN libraries l ON ci.show_id IS NULL AND l.id = (
                SELECT library_id FROM shows WHERE id = ci.show_id
            )
            WHERE ci.kind = 'movie'
        """
        params = []
        
        if library_id:
            query += " AND l.id = ?"
            params.append(library_id)
        
        if search:
            query += " AND ci.title LIKE ?"
            params.append(f"%{search}%")
        
        query += " ORDER BY ci.title"
        
        cursor = self.execute(query, params)
        return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    
    def get_content_by_genre(self, genre: str, library_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get content items by genre.
        
        Args:
            genre: Genre name
            library_id: Optional library ID to filter by
            
        Returns:
            List of content item dictionaries
        """
        query = """
            SELECT ci.id, ci.kind, ci.title, ci.synopsis, ci.duration_ms,
                   ci.season_number, ci.episode_number, ci.created_at, ci.updated_at,
                   s.title as show_title, l.title as library_title
            FROM content_items ci
            LEFT JOIN shows s ON ci.show_id = s.id
            LEFT JOIN libraries l ON s.library_id = l.id
            LEFT JOIN content_tags ct ON ci.id = ct.content_item_id
            WHERE ct.namespace = 'genre' AND ct.value = ?
        """
        params = [genre]
        
        if library_id:
            query += " AND l.id = ?"
            params.append(library_id)
        
        query += " ORDER BY ci.title"
        
        cursor = self.execute(query, params)
        return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    
    def get_media_files(self, content_item_id: int) -> List[Dict[str, Any]]:
        """
        Get media files for a content item.
        
        Args:
            content_item_id: Content item ID
            
        Returns:
            List of media file dictionaries
        """
        query = """
            SELECT mf.id, mf.plex_file_path, mf.local_file_path, mf.file_size_bytes, 
                   mf.video_codec, mf.audio_codec, mf.width, mf.height, mf.duration_ms,
                   mf.container, mf.created_at, mf.updated_at
            FROM media_files mf
            JOIN content_item_files cif ON mf.id = cif.media_file_id
            WHERE cif.content_item_id = ?
            ORDER BY mf.created_at
        """
        
        cursor = self.execute(query, (content_item_id,))
        return [dict(zip([col[0] for col in cursor.description], row)) for row in cursor.fetchall()]
    
    def get_available_genres(self) -> List[str]:
        """
        Get list of available genres.
        
        Returns:
            List of genre names
        """
        query = """
            SELECT DISTINCT ct.value
            FROM content_tags ct
            WHERE ct.namespace = 'genre'
            ORDER BY ct.value
        """
        
        cursor = self.execute(query)
        return [row[0] for row in cursor.fetchall()]