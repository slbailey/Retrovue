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
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
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
    
    # Content item operations
    
    def upsert_content_item(
        self, 
        content_item: ContentItemData,
        show_id: Optional[int] = None,
        season_id: Optional[int] = None
    ) -> int:
        """
        Upsert a content item.
        
        Args:
            content_item: ContentItemData object
            show_id: Optional show ID
            season_id: Optional season ID
            
        Returns:
            Content item ID
        """
        logger.debug(f"Upserting content item: {content_item.title}")
        
        # Check if content item exists (by title and kind)
        cursor = self.execute(
            "SELECT id FROM content_items WHERE title = ? AND kind = ?",
            (content_item.title, content_item.kind)
        )
        existing = cursor.fetchone()
        
        if existing:
            content_item_id = existing['id']
            logger.debug(f"Content item exists with ID: {content_item_id}")
        else:
            # Insert new content item
            cursor = self.execute(
                """INSERT INTO content_items 
                   (kind, title, synopsis, duration_ms, rating_system, rating_code, is_kids_friendly, 
                    show_id, season_id, season_number, episode_number)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (content_item.kind, content_item.title, content_item.synopsis, content_item.duration_ms,
                 content_item.rating_system, content_item.rating_code, content_item.is_kids_friendly,
                 show_id, season_id, content_item.season_number, content_item.episode_number)
            )
            content_item_id = cursor.lastrowid
            logger.info(f"Created new content item with ID: {content_item_id}")
        
        self.commit()
        return content_item_id
    
    # Media file operations
    
    def upsert_media_file(
        self, 
        media_file: MediaFileData,
        server_id: int,
        library_id: int,
        content_item_id: int
    ) -> int:
        """
        Upsert a media file.
        
        Args:
            media_file: MediaFileData object
            server_id: Server ID
            library_id: Library ID
            content_item_id: Content item ID
            
        Returns:
            Media file ID
        """
        logger.debug(f"Upserting media file: {media_file.file_path}")
        
        # Check if media file exists (by plex_rating_key)
        cursor = self.execute(
            "SELECT id FROM media_files WHERE plex_rating_key = ?",
            (media_file.plex_rating_key,)
        )
        existing = cursor.fetchone()
        
        if existing:
            media_file_id = existing['id']
            logger.debug(f"Media file exists with ID: {media_file_id}")
        else:
            # Get current timestamp
            now_epoch = int(datetime.now().timestamp())
            
            # Insert new media file
            cursor = self.execute(
                """INSERT INTO media_files 
                   (server_id, library_id, content_item_id, plex_rating_key, file_path, size_bytes, 
                    container, video_codec, audio_codec, width, height, bitrate, frame_rate, channels,
                    updated_at_plex, first_seen_at, last_seen_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (server_id, library_id, content_item_id, media_file.plex_rating_key,
                 media_file.file_path, media_file.size_bytes, media_file.container, media_file.video_codec,
                 media_file.audio_codec, media_file.width, media_file.height, media_file.bitrate,
                 media_file.frame_rate, media_file.channels, media_file.updated_at_plex,
                 now_epoch, now_epoch)
            )
            media_file_id = cursor.lastrowid
            logger.info(f"Created new media file with ID: {media_file_id}")
        
        self.commit()
        return media_file_id
    
    def link_content_item_file(self, content_item_id: int, media_file_id: int, role: str = 'primary') -> None:
        """
        Link a content item to a media file.
        
        Args:
            content_item_id: Content item ID
            media_file_id: Media file ID
            role: Role (primary, secondary, etc.)
        """
        logger.debug(f"Linking content item {content_item_id} to media file {media_file_id}")
        
        # Check if link exists
        cursor = self.execute(
            "SELECT 1 FROM content_item_files WHERE content_item_id = ? AND media_file_id = ? AND role = ?",
            (content_item_id, media_file_id, role)
        )
        existing = cursor.fetchone()
        
        if not existing:
            # Insert new link
            self.execute(
                "INSERT INTO content_item_files (content_item_id, media_file_id, role) VALUES (?, ?, ?)",
                (content_item_id, media_file_id, role)
            )
            self.commit()
            logger.info(f"Linked content item {content_item_id} to media file {media_file_id}")
    
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
        cursor = self.execute("""
            INSERT INTO libraries (server_id, plex_library_key, title, library_type)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(server_id, plex_library_key) DO UPDATE SET
                title=excluded.title,
                library_type=excluded.library_type,
                updated_at=datetime('now')
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
        cursor = self.execute("""
            INSERT INTO shows (server_id, library_id, plex_rating_key, title, year, artwork_url)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(server_id, library_id, plex_rating_key) DO UPDATE SET
                title=excluded.title,
                year=excluded.year,
                artwork_url=excluded.artwork_url,
                updated_at=datetime('now')
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
        cursor = self.execute("""
            INSERT INTO seasons (show_id, season_number, plex_rating_key, title)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(show_id, season_number) DO UPDATE SET
                plex_rating_key=excluded.plex_rating_key,
                title=excluded.title,
                updated_at=datetime('now')
        """, (show_id, season_number, plex_rating_key, title))
        
        season_id = cursor.lastrowid
        self.commit()
        return season_id
    
    def upsert_content_item(self, content_item, show_id: Optional[int] = None, season_id: Optional[int] = None) -> int:
        """
        Upsert a content item.
        
        Args:
            content_item: ContentItemData object
            show_id: Optional show ID
            season_id: Optional season ID
            
        Returns:
            Content item ID
        """
        cursor = self.execute("""
            INSERT INTO content_items(
                kind, title, synopsis, duration_ms, rating_system, rating_code,
                is_kids_friendly, metadata_updated_at, show_id, season_id,
                season_number, episode_number
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                synopsis=excluded.synopsis,
                duration_ms=excluded.duration_ms,
                rating_system=excluded.rating_system,
                rating_code=excluded.rating_code,
                is_kids_friendly=excluded.is_kids_friendly,
                metadata_updated_at=excluded.metadata_updated_at,
                show_id=excluded.show_id,
                season_id=excluded.season_id,
                season_number=excluded.season_number,
                episode_number=excluded.episode_number,
                updated_at=datetime('now')
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
    
    def upsert_media_file(self, media_file, server_id: int, library_id: int, content_item_id: int) -> int:
        """
        Upsert a media file.
        
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
                       created_at, updated_at
                FROM libraries
                WHERE server_id = ?
                ORDER BY title
            """, (server_id,))
        else:
            cursor = self.execute("""
                SELECT id, server_id, plex_library_key, title, library_type,
                       sync_enabled, last_full_sync_epoch, last_incremental_sync_epoch,
                       created_at, updated_at
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
    
    def upsert_library(self, server_id: int, plex_library_key: int, title: str, library_type: str) -> int:
        """
        Upsert one library (idempotent).
        
        Args:
            server_id: Server ID
            plex_library_key: Plex library key
            title: Library title
            library_type: Library type
            
        Returns:
            Library ID
        """
        cursor = self.execute("""
            INSERT INTO libraries(server_id, plex_library_key, title, library_type, sync_enabled)
            VALUES (?, ?, ?, ?, COALESCE(
                (SELECT sync_enabled FROM libraries WHERE server_id=? AND plex_library_key=?), 1))
            ON CONFLICT(server_id, plex_library_key) DO UPDATE SET
                title=excluded.title,
                library_type=excluded.library_type,
                updated_at=datetime('now')
        """, (server_id, plex_library_key, title, library_type, server_id, plex_library_key))
        
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
    
    def get_path_mappings(self, server_id: int, library_id: int) -> List[Tuple[str, str]]:
        """
        Get path mappings for a server and library.
        
        Args:
            server_id: Server ID
            library_id: Library ID
            
        Returns:
            List of (plex_path, local_path) tuples
        """
        cursor = self.execute("""
            SELECT plex_path, local_path
            FROM path_mappings
            WHERE server_id = ? AND library_id = ?
        """, (server_id, library_id))
        
        return [(row['plex_path'], row['local_path']) for row in cursor.fetchall()]
    
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