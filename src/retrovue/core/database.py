"""
Retrovue Database Management v2

Handles SQLite database operations for content scheduling and metadata.
Uses normalized schema with separate tables for media files and metadata.
"""

import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime


class RetrovueDatabase:
    """
    Manages the Retrovue SQLite database for content scheduling and metadata.
    Uses normalized schema with separate tables for media files and metadata.
    """
    
    def __init__(self, db_path: str = "retrovue.db"):
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.connection = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the database with required tables."""
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row  # Enable dict-like access
        self._create_tables()
        self._run_migrations()
    
    def _create_tables(self):
        """Create all required database tables with normalized schema."""
        cursor = self.connection.cursor()
        
        # Media files table (core - one row per media file)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS media_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                duration INTEGER NOT NULL,
                media_type TEXT NOT NULL,  -- 'movie', 'episode', 'commercial', 'bumper'
                source_type TEXT NOT NULL,  -- 'plex', 'tmm', 'manual'
                source_id TEXT,  -- External ID (Plex key, TMM file path, etc.)
                library_name TEXT,  -- Library name from source (e.g., "Horror", "3D Movies")
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_type, source_id)
            )
        """)
        
        # Shows table (for grouping episodes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                total_seasons INTEGER,
                total_episodes INTEGER,
                show_rating TEXT,
                show_summary TEXT,
                genre TEXT,
                source_type TEXT NOT NULL,
                source_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(title, source_type, source_id)
            )
        """)
        
        # Episodes table (links media file to show)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_file_id INTEGER NOT NULL,
                show_id INTEGER NOT NULL,
                episode_title TEXT NOT NULL,
                season_number INTEGER,
                episode_number INTEGER,
                rating TEXT,
                summary TEXT,
                FOREIGN KEY (media_file_id) REFERENCES media_files(id) ON DELETE CASCADE,
                FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE
            )
        """)
        
        # Movies table (links media file to movie metadata)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_file_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                year INTEGER,
                rating TEXT,
                summary TEXT,
                genre TEXT,
                director TEXT,
                FOREIGN KEY (media_file_id) REFERENCES media_files(id) ON DELETE CASCADE
            )
        """)
        
        # Commercials table (for commercial metadata)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commercials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_file_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                company TEXT,
                category TEXT,
                daypart_preference TEXT,
                seasonal_preference TEXT,
                target_demographic TEXT,
                FOREIGN KEY (media_file_id) REFERENCES media_files(id) ON DELETE CASCADE
            )
        """)
        
        # Plex credentials table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plex_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_url TEXT NOT NULL,
                token TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Content scheduling metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_scheduling_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_file_id INTEGER NOT NULL,
                daypart_preference TEXT,
                seasonal_preference TEXT,
                content_rating TEXT,
                target_demographic TEXT,
                content_warnings TEXT,
                FOREIGN KEY (media_file_id) REFERENCES media_files(id) ON DELETE CASCADE
            )
        """)
        
        # Channels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Schedules table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                media_file_id INTEGER NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
                FOREIGN KEY (media_file_id) REFERENCES media_files(id) ON DELETE CASCADE
            )
        """)
        
        # Playout logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS playout_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                media_file_id INTEGER NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES channels(id) ON DELETE CASCADE,
                FOREIGN KEY (media_file_id) REFERENCES media_files(id) ON DELETE CASCADE
            )
        """)
        
        # System config table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Emergency alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emergency_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_files_source_type ON media_files (source_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_files_media_type ON media_files (media_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_episodes_show_id ON episodes (show_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedules_channel_start ON schedules (channel_id, start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_playout_logs_channel_start ON playout_logs (channel_id, start_time)")
        
        self.connection.commit()
    
    def _run_migrations(self):
        """Run database migrations to update schema"""
        cursor = self.connection.cursor()
        
        # Migration 1: Add library_name column to media_files table
        try:
            cursor.execute("ALTER TABLE media_files ADD COLUMN library_name TEXT")
            self.connection.commit()
            print("✅ Added library_name column to media_files table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                # Column already exists, that's fine
                pass
            else:
                print(f"⚠️ Migration warning: {e}")
    
    def store_plex_credentials(self, server_url: str, token: str) -> int:
        """Store Plex credentials in the database"""
        cursor = self.connection.cursor()
        
        # Deactivate any existing credentials
        cursor.execute("UPDATE plex_credentials SET is_active = 0")
        
        # Insert new credentials
        cursor.execute("""
            INSERT INTO plex_credentials (server_url, token, is_active)
            VALUES (?, ?, 1)
        """, (server_url, token))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def get_plex_credentials(self) -> Optional[Dict[str, str]]:
        """Get active Plex credentials from the database"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT server_url, token FROM plex_credentials 
            WHERE is_active = 1 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        result = cursor.fetchone()
        
        if result:
            return {
                'server_url': result['server_url'],
                'token': result['token']
            }
        return None
    
    def add_media_file(self, file_path: str, duration: int, media_type: str, 
                      source_type: str, source_id: str = None, library_name: str = None) -> int:
        """Add a media file to the database"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO media_files
            (file_path, duration, media_type, source_type, source_id, library_name, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (file_path, duration, media_type, source_type, source_id, library_name))
        
        # Get the media_file_id
        if source_id:
            cursor.execute("""
                SELECT id FROM media_files
                WHERE source_type = ? AND source_id = ?
            """, (source_type, source_id))
            result = cursor.fetchone()
            media_file_id = result['id'] if result else cursor.lastrowid
        else:
            media_file_id = cursor.lastrowid
        
        self.connection.commit()
        return media_file_id
    
    def add_show(self, title: str, total_seasons: int = None, total_episodes: int = None,
                show_rating: str = None, show_summary: str = None, genre: str = None,
                source_type: str = None, source_id: str = None) -> int:
        """Add a show to the database"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO shows
            (title, total_seasons, total_episodes, show_rating, show_summary, genre, source_type, source_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, total_seasons, total_episodes, show_rating, show_summary, genre, source_type, source_id))
        
        # Get the show_id
        if source_id:
            cursor.execute("""
                SELECT id FROM shows
                WHERE title = ? AND source_type = ? AND source_id = ?
            """, (title, source_type, source_id))
            result = cursor.fetchone()
            show_id = result['id'] if result else cursor.lastrowid
        else:
            show_id = cursor.lastrowid
        
        self.connection.commit()
        return show_id
    
    def add_episode(self, media_file_id: int, show_id: int, episode_title: str,
                   season_number: int = None, episode_number: int = None,
                   rating: str = None, summary: str = None) -> int:
        """Add an episode to the database"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT INTO episodes
            (media_file_id, show_id, episode_title, season_number, episode_number, rating, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (media_file_id, show_id, episode_title, season_number, episode_number, rating, summary))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def add_movie(self, media_file_id: int, title: str, year: int = None,
                 rating: str = None, summary: str = None, genre: str = None,
                 director: str = None) -> int:
        """Add a movie to the database"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT INTO movies
            (media_file_id, title, year, rating, summary, genre, director)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (media_file_id, title, year, rating, summary, genre, director))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def get_media_files(self, media_type: str = None) -> List[Dict]:
        """Get media files with optional filtering by type"""
        cursor = self.connection.cursor()
        
        if media_type:
            cursor.execute("""
                SELECT * FROM media_files 
                WHERE media_type = ? 
                ORDER BY created_at DESC
            """, (media_type,))
        else:
            cursor.execute("""
                SELECT * FROM media_files 
                ORDER BY created_at DESC
            """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_episodes_with_show_info(self, show_title: str = None) -> List[Dict]:
        """Get episodes with their show information"""
        cursor = self.connection.cursor()
        
        if show_title:
            cursor.execute("""
                SELECT 
                    mf.*,
                    e.episode_title,
                    e.season_number,
                    e.episode_number,
                    e.rating,
                    e.summary,
                    s.title as show_title,
                    s.show_summary
                FROM media_files mf
                JOIN episodes e ON mf.id = e.media_file_id
                JOIN shows s ON e.show_id = s.id
                WHERE s.title = ?
                ORDER BY s.title, e.season_number, e.episode_number
            """, (show_title,))
        else:
            cursor.execute("""
                SELECT 
                    mf.*,
                    e.episode_title,
                    e.season_number,
                    e.episode_number,
                    e.rating,
                    e.summary,
                    s.title as show_title,
                    s.show_summary
                FROM media_files mf
                JOIN episodes e ON mf.id = e.media_file_id
                JOIN shows s ON e.show_id = s.id
                ORDER BY s.title, e.season_number, e.episode_number
            """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_movies_with_metadata(self) -> List[Dict]:
        """Get movies with their metadata"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            SELECT 
                mf.*,
                m.title,
                m.year,
                m.rating,
                m.summary,
                m.genre,
                m.director
            FROM media_files mf
            JOIN movies m ON mf.id = m.media_file_id
            ORDER BY m.title
        """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_shows(self) -> List[Dict]:
        """Get all shows"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM shows ORDER BY title")
        return [dict(row) for row in cursor.fetchall()]
    
    def get_media_types(self) -> List[str]:
        """Get all unique media types"""
        cursor = self.connection.cursor()
        cursor.execute("SELECT DISTINCT media_type FROM media_files ORDER BY media_type")
        return [row['media_type'] for row in cursor.fetchall()]
    
    def get_content_ratings(self) -> List[str]:
        """Get all unique content ratings"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT DISTINCT rating FROM (
                SELECT rating FROM episodes WHERE rating IS NOT NULL
                UNION
                SELECT rating FROM movies WHERE rating IS NOT NULL
            ) ORDER BY rating
        """)
        return [row['rating'] for row in cursor.fetchall()]
    
    # Sync-related methods
    def get_movies_by_source(self, source_type: str) -> List[Dict]:
        """Get all movies from a specific source"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT m.*, mf.source_id, mf.id as media_file_id, mf.library_name, mf.file_path, mf.duration
            FROM movies m
            JOIN media_files mf ON m.media_file_id = mf.id
            WHERE mf.source_type = ?
        """, (source_type,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_shows_by_source(self, source_type: str) -> List[Dict]:
        """Get all shows from a specific source"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT s.*, mf.source_id
            FROM shows s
            JOIN media_files mf ON s.id = mf.id
            WHERE mf.source_type = ?
        """, (source_type,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_episodes_by_show_source_id(self, show_source_id: str) -> List[Dict]:
        """Get all episodes for a show by its source ID"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT e.*, mf.source_id, mf.id as media_file_id
            FROM episodes e
            JOIN shows s ON e.show_id = s.id
            JOIN media_files mf ON e.media_file_id = mf.id
            WHERE s.source_id = ?
        """, (show_source_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_movie_by_source_id(self, source_id: str) -> Optional[Dict]:
        """Get a movie by its source ID"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT m.*, mf.source_id, mf.id as media_file_id, mf.file_path, mf.duration, mf.library_name
            FROM movies m
            JOIN media_files mf ON m.media_file_id = mf.id
            WHERE mf.source_id = ?
        """, (source_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_show_by_source_id(self, source_id: str) -> Optional[Dict]:
        """Get a show by its source ID"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT s.*, mf.source_id
            FROM shows s
            JOIN media_files mf ON s.id = mf.id
            WHERE mf.source_id = ?
        """, (source_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_episode_by_source_id(self, source_id: str) -> Optional[Dict]:
        """Get an episode by its source ID"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT e.*, mf.source_id, mf.id as media_file_id, mf.file_path, mf.duration, mf.library_name
            FROM episodes e
            JOIN media_files mf ON e.media_file_id = mf.id
            WHERE mf.source_id = ?
        """, (source_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_media_file(self, media_file_id: int, file_path: str, duration: int, library_name: str = None) -> bool:
        """Update a media file"""
        try:
            cursor = self.connection.cursor()
            if library_name is not None:
                cursor.execute("""
                    UPDATE media_files 
                    SET file_path = ?, duration = ?, library_name = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (file_path, duration, library_name, media_file_id))
            else:
                cursor.execute("""
                    UPDATE media_files 
                    SET file_path = ?, duration = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (file_path, duration, media_file_id))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Failed to update media file: {e}")
            return False
    
    def update_movie(self, movie_id: int, title: str, year: Optional[int], 
                    rating: str, summary: str, genre: str, director: str) -> bool:
        """Update a movie"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE movies 
                SET title = ?, year = ?, rating = ?, summary = ?, genre = ?, director = ?
                WHERE id = ?
            """, (title, year, rating, summary, genre, director, movie_id))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Failed to update movie: {e}")
            return False
    
    def update_episode(self, episode_id: int, episode_title: str, season_number: int,
                      episode_number: int, rating: str, summary: str) -> bool:
        """Update an episode"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE episodes 
                SET episode_title = ?, season_number = ?, episode_number = ?, rating = ?, summary = ?
                WHERE id = ?
            """, (episode_title, season_number, episode_number, rating, summary, episode_id))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Failed to update episode: {e}")
            return False
    
    def remove_movie_by_source_id(self, source_id: str) -> bool:
        """Remove a movie by its source ID"""
        try:
            cursor = self.connection.cursor()
            # Get media file ID
            cursor.execute("SELECT id FROM media_files WHERE source_id = ?", (source_id,))
            media_file = cursor.fetchone()
            if not media_file:
                return False
            
            # Remove movie (cascade will remove media file)
            cursor.execute("DELETE FROM movies WHERE media_file_id = ?", (media_file['id'],))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Failed to remove movie: {e}")
            return False
    
    def remove_show_by_source_id(self, source_id: str) -> bool:
        """Remove a show by its source ID"""
        try:
            cursor = self.connection.cursor()
            # Get show ID
            cursor.execute("SELECT id FROM shows WHERE source_id = ?", (source_id,))
            show = cursor.fetchone()
            if not show:
                return False
            
            # Remove show (cascade will remove episodes and media files)
            cursor.execute("DELETE FROM shows WHERE id = ?", (show['id'],))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Failed to remove show: {e}")
            return False
    
    def remove_episode_by_source_id(self, source_id: str) -> bool:
        """Remove an episode by its source ID"""
        try:
            cursor = self.connection.cursor()
            # Get media file ID
            cursor.execute("SELECT id FROM media_files WHERE source_id = ?", (source_id,))
            media_file = cursor.fetchone()
            if not media_file:
                return False
            
            # Remove episode (cascade will remove media file)
            cursor.execute("DELETE FROM episodes WHERE media_file_id = ?", (media_file['id'],))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Failed to remove episode: {e}")
            return False
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
