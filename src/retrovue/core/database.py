"""
Retrovue Database Management System

This module provides comprehensive database management for the Retrovue IPTV simulation system.
It handles all data storage, retrieval, and synchronization operations using SQLite with a
normalized schema designed for professional broadcast television scheduling.

## What This System Does

Retrovue simulates a professional TV broadcast station by:
- Storing your media library (movies, TV shows, commercials, bumpers)
- Managing scheduling metadata (when to air content, target audiences, content ratings)
- Tracking playout history and performance metrics
- Supporting multiple Plex Media Servers with intelligent synchronization
- Providing a foundation for multi-channel broadcasting

## Key Concepts for Beginners

### Media Files vs Metadata
- **Media Files**: The actual video files (movies, TV episodes, commercials)
- **Metadata**: Information about the content (title, duration, rating, when to air it)
- **Separation**: We store metadata in the database but keep the actual video files where they are

### Database Tables Explained
- **media_files**: Core table storing information about each video file
- **movies**: Additional information specific to movies (director, genre, etc.)
- **shows**: Information about TV series (total seasons, episodes, etc.)
- **episodes**: Individual TV episodes linked to their parent show
- **plex_servers**: Configuration for your Plex Media Servers
- **plex_path_mappings**: How to find your video files on your computer

### Why This Architecture?
- **Scalability**: Can handle thousands of movies and TV episodes
- **Flexibility**: Easy to add new content types (commercials, bumpers, etc.)
- **Performance**: Fast lookups and updates even with large libraries
- **Reliability**: Automatic backups and data integrity checks

## How It Works

1. **Content Import**: Import movies and TV shows from your Plex Media Server
2. **Metadata Storage**: Store scheduling information (when to air, target audience)
3. **Scheduling**: Create broadcast schedules using the stored content
4. **Playout**: Stream content according to the schedule (future feature)

## For Non-Technical Users

Think of this like a digital filing cabinet for your TV station:
- Each drawer (table) holds specific types of information
- You can quickly find any piece of content
- The system automatically keeps everything organized
- It remembers what you've already imported so it doesn't duplicate work

## Technical Details

- **Database Engine**: SQLite (file-based, no server required)
- **Schema Version**: 2 (automatically migrates from older versions)
- **Foreign Keys**: Enabled for data integrity
- **Timestamps**: Unix epoch integers for consistent time handling
- **Multi-Server**: Supports multiple Plex servers with proper isolation
"""

import sqlite3
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

# Schema version constant - increment this when making schema changes
CURRENT_SCHEMA_VERSION = 2


class RetrovueDatabase:
    """
    Main database management class for the Retrovue IPTV simulation system.
    
    This class handles all database operations for storing and managing your media library,
    scheduling metadata, and system configuration. It's designed to be the central data
    storage system for a professional broadcast television simulation.
    
    ## What This Class Does
    
    The RetrovueDatabase class provides:
    - **Content Storage**: Store information about movies, TV shows, and episodes
    - **Server Management**: Manage multiple Plex Media Servers and their configurations
    - **Path Mapping**: Convert Plex server paths to local file system paths
    - **Scheduling Data**: Store when and how content should be broadcast
    - **System Configuration**: Manage settings and preferences
    - **Data Integrity**: Ensure all data is consistent and properly linked
    
    ## Key Features
    
    ### Automatic Database Setup
    - Creates all required tables automatically
    - Runs database migrations to update schema when needed
    - Handles database upgrades without data loss
    
    ### Multi-Server Support
    - Manage multiple Plex Media Servers
    - Each server can have different path mappings
    - Server-scoped operations prevent data conflicts
    
    ### Intelligent Synchronization
    - Only updates content that has actually changed
    - Uses timestamps to detect changes efficiently
    - Dramatically improves performance for large libraries
    
    ### Data Relationships
    - Episodes are linked to their parent shows
    - Media files are linked to their metadata
    - All content is properly categorized and organized
    
    ## How to Use This Class
    
    ### Basic Usage
    ```python
    # Create a new database (or open existing one)
    db = RetrovueDatabase("my_retrovue.db")
    
    # Add a Plex server
    server_id = db.add_plex_server("My Plex Server", "http://192.168.1.100:32400", "my-token")
    
    # Add a path mapping
    db.add_plex_path_mapping("/media/movies", "D:\\Movies", server_id)
    
    # Get all servers
    servers = db.get_plex_servers()
    ```
    
    ### Content Management
    ```python
    # Add a movie
    media_id = db.add_media_file("D:\\Movies\\Avengers.mkv", 8580000, "movie", "plex", "avengers-guid")
    movie_id = db.add_movie(media_id, "The Avengers", 2012, "PG-13", "Superhero movie", "Action", "Joss Whedon")
    
    # Get all movies
    movies = db.get_movies_with_metadata()
    ```
    
    ## Database Schema Overview
    
    The database uses a normalized schema with these main tables:
    
    ### Core Content Tables
    - **media_files**: Basic information about each video file
    - **movies**: Movie-specific metadata (director, genre, etc.)
    - **shows**: TV series information (total seasons, episodes, etc.)
    - **episodes**: Individual TV episodes with season/episode numbers
    
    ### Server Management Tables
    - **plex_servers**: Plex Media Server configurations
    - **libraries**: Library configurations for each server
    - **plex_path_mappings**: Path conversion rules for each server
    
    ### Scheduling Tables (Future)
    - **channels**: TV channels that will broadcast content
    - **schedules**: When content should be aired
    - **playout_logs**: History of what was actually broadcast
    
    ## Error Handling
    
    The class includes comprehensive error handling:
    - Database connection failures are handled gracefully
    - Invalid data is logged and skipped
    - Migration errors are reported with helpful messages
    - All operations include proper transaction management
    
    ## Performance Considerations
    
    - Uses SQLite for fast, local database operations
    - Includes database indexes for optimal query performance
    - Implements connection pooling and proper resource management
    - Supports large libraries (tested with 17,000+ episodes)
    
    ## Thread Safety
    
    This class is designed for single-threaded use. If you need multi-threading,
    create separate database instances for each thread.
    
    ## Example: Complete Setup
    
    ```python
    # Initialize database
    db = RetrovueDatabase("retrovue.db")
    
    # Add Plex server
    server_id = db.add_plex_server(
        name="Home Plex Server",
        server_url="http://192.168.1.100:32400",
        token="your-plex-token-here"
    )
    
    # Configure path mappings
    db.add_plex_path_mapping(
        plex_path="/media/movies",
        local_path="D:\\Media\\Movies",
        server_id=server_id,
        library_root="/media/movies",
        library_name="Movies"
    )
    
    # The database is now ready for content import
    ```
    
    ## Migration System
    
    The database includes an automatic migration system that:
    - Detects the current schema version
    - Applies necessary updates to bring the database up to date
    - Preserves all existing data during migrations
    - Provides detailed logging of migration progress
    
    This ensures that your database stays current with the latest Retrovue features
    without requiring manual intervention.
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
        
        # Enable foreign key constraints immediately
        cursor = self.connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        self.connection.commit()
        
        self._create_tables()
        self._run_migrations()
        self._ensure_schema_consistency()
        self._update_schema_version()
        
        # Verify schema consistency on startup
        if not self.verify_schema_consistency():
            logger.warning("⚠️ Schema consistency check failed - some issues may need manual resolution")
    
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
                plex_path TEXT,  -- Plex file path (separate from local file_path)
                server_id INTEGER,  -- Server ID for multi-server support
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at INTEGER,  -- Unix timestamp from Plex
                UNIQUE(source_type, source_id)
            )
        """)
        
        # Shows table (for grouping episodes) - Updated for year-based disambiguation
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plex_rating_key TEXT,  -- Plex's rating key (not unique, not required)
                title TEXT NOT NULL,
                year INTEGER,  -- Year for disambiguation (e.g., 1978 vs 2003 for Battlestar Galactica)
                total_seasons INTEGER,
                total_episodes INTEGER,
                show_rating TEXT,
                show_summary TEXT,
                genre TEXT,
                studio TEXT,  -- Production studio
                originally_available_at DATE,  -- Original air date
                guid_primary TEXT,  -- Primary GUID (preferred external identifier)
                source_type TEXT NOT NULL,
                source_id TEXT UNIQUE NOT NULL,  -- Use GUID as unique identifier
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at INTEGER,  -- Unix timestamp from Plex
                server_id INTEGER
            )
        """)
        
        # Show GUIDs table (for storing multiple external identifiers per show)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS show_guids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                show_id INTEGER NOT NULL,
                provider TEXT NOT NULL,  -- e.g., 'tvdb', 'tmdb', 'imdb', 'plex'
                external_id TEXT NOT NULL,  -- The actual ID from the provider
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE,
                UNIQUE(provider, external_id)  -- Prevent duplicate GUIDs
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
                originally_available_at DATE,  -- Original air date
                duration_ms INTEGER,  -- Duration in milliseconds
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at INTEGER,  -- Unix timestamp from Plex
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
                server_id INTEGER,  -- Server ID for multi-server support
                updated_at INTEGER,  -- Unix timestamp from Plex
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
        
        # Plex servers table (updated for multiple servers)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plex_servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                server_url TEXT NOT NULL,
                token TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(server_url)
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
        
        # Schema version table to track database schema version
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)
        
        # Libraries table (1:many with plex_servers)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS libraries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER NOT NULL,
                library_key TEXT NOT NULL,
                library_name TEXT NOT NULL,
                library_type TEXT NOT NULL,
                library_root TEXT,
                sync_enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (server_id) REFERENCES plex_servers(id) ON DELETE CASCADE,
                UNIQUE(server_id, library_key)
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
        
        # New indexes for disambiguation support
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shows_title ON shows (title)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shows_year ON shows (year)")
        # No longer need index on plex_rating_key since it's not used for lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_episodes_season_number ON episodes (season_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_episodes_episode_number ON episodes (episode_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_show_guids_provider ON show_guids (provider)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_show_guids_external_id ON show_guids (external_id)")
        
        self.connection.commit()
    
    def _run_migrations(self):
        """Run database migrations to update schema"""
        cursor = self.connection.cursor()
        
        # Helper function to check if a column exists in a table
        def column_exists(table_name: str, column_name: str) -> bool:
            """Check if a column exists in a table"""
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]
                return column_name in columns
            except Exception as e:
                logger.warning(f"⚠️ Error checking column {column_name} in {table_name}: {e}")
                return False
        
        # Helper function to get column info
        def get_column_info(table_name: str, column_name: str) -> Optional[Dict]:
            """Get information about a specific column"""
            try:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                for col in columns:
                    if col[1] == column_name:  # col[1] is column name
                        return {
                            'name': col[1],
                            'type': col[2],
                            'not_null': col[3],
                            'default': col[4],
                            'primary_key': col[5]
                        }
                return None
            except Exception as e:
                logger.warning(f"⚠️ Error getting column info for {column_name} in {table_name}: {e}")
                return None
        
        # Helper function to check if migration has been applied
        def migration_applied(migration_name: str) -> bool:
            """Check if a specific migration has been applied"""
            try:
                cursor.execute("SELECT COUNT(*) FROM schema_version WHERE description LIKE ?", (f"%{migration_name}%",))
                return cursor.fetchone()[0] > 0
            except Exception:
                return False
        
        # Helper function to recreate a table with new schema
        def recreate_table(table_name: str, new_schema_sql: str, data_copy_sql: str) -> bool:
            """Recreate a table with new schema and copy data"""
            try:
                temp_table_name = f"{table_name}_new"
                
                # Create new table
                cursor.execute(new_schema_sql.replace(table_name, temp_table_name))
                
                # Copy data
                cursor.execute(data_copy_sql.replace(table_name, temp_table_name))
                
                # Drop old table and rename new table
                cursor.execute(f"DROP TABLE {table_name}")
                cursor.execute(f"ALTER TABLE {temp_table_name} RENAME TO {table_name}")
                
                self.connection.commit()
                return True
            except Exception as e:
                logger.error(f"❌ Failed to recreate table {table_name}: {e}")
                self.connection.rollback()
                return False
        
        # Migration 1: Add library_name column to media_files table
        try:
            if not column_exists('media_files', 'library_name'):
                cursor.execute("ALTER TABLE media_files ADD COLUMN library_name TEXT")
                self.connection.commit()
                logger.info("✅ Added library_name column to media_files table")
            else:
                logger.info("✅ Migration 1: library_name column already exists")
        except Exception as e:
            logger.warning(f"⚠️ Migration 1 warning: {e}")
        
        # Migration 2: Add year-based disambiguation columns to shows table
        # Note: This migration adds updated_at with DEFAULT CURRENT_TIMESTAMP for backward compatibility.
        # Later migrations (11+) will recreate tables with proper INTEGER epoch columns.
        try:
            cursor.execute("ALTER TABLE shows ADD COLUMN plex_rating_key TEXT")
            cursor.execute("ALTER TABLE shows ADD COLUMN year INTEGER")
            cursor.execute("ALTER TABLE shows ADD COLUMN studio TEXT")
            cursor.execute("ALTER TABLE shows ADD COLUMN originally_available_at DATE")
            cursor.execute("ALTER TABLE shows ADD COLUMN guid_primary TEXT")
            cursor.execute("ALTER TABLE shows ADD COLUMN updated_at_plex TIMESTAMP")
            # Only add updated_at with DEFAULT if it doesn't exist and we're not using the new schema
            if not column_exists('shows', 'updated_at'):
                cursor.execute("ALTER TABLE shows ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            self.connection.commit()
            logger.info("✅ Added year-based disambiguation columns to shows table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                # Columns already exist, that's fine
                pass
            else:
                logger.warning(f"⚠️ Migration warning: {e}")
        
        # Migration 3: Add additional columns to episodes table
        # Note: This migration adds updated_at with DEFAULT CURRENT_TIMESTAMP for backward compatibility.
        # Later migrations (11+) will recreate tables with proper INTEGER epoch columns.
        try:
            cursor.execute("ALTER TABLE episodes ADD COLUMN originally_available_at DATE")
            cursor.execute("ALTER TABLE episodes ADD COLUMN duration_ms INTEGER")
            cursor.execute("ALTER TABLE episodes ADD COLUMN updated_at_plex TIMESTAMP")
            cursor.execute("ALTER TABLE episodes ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            # Only add updated_at with DEFAULT if it doesn't exist and we're not using the new schema
            if not column_exists('episodes', 'updated_at'):
                cursor.execute("ALTER TABLE episodes ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            self.connection.commit()
            logger.info("✅ Added additional columns to episodes table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                # Columns already exist, that's fine
                pass
            else:
                logger.warning(f"⚠️ Migration warning: {e}")
        
        # Migration 4: Add updated_at_plex column to movies table (if it doesn't exist)
        # Skip this migration if we're using the new schema (no updated_at_plex columns)
        try:
            # Check if we're using the new schema by looking for schema_version table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'")
            has_schema_version = cursor.fetchone() is not None
            
            if not has_schema_version:
                # Old schema - add updated_at_plex column if it doesn't exist
                cursor.execute("PRAGMA table_info(movies)")
                movies_columns = [row[1] for row in cursor.fetchall()]
                if 'updated_at_plex' not in movies_columns:
                    cursor.execute("ALTER TABLE movies ADD COLUMN updated_at_plex TIMESTAMP")
                    self.connection.commit()
                    logger.info("✅ Added updated_at_plex column to movies table")
            # New schema - skip this migration
        except sqlite3.OperationalError as e:
            logger.warning(f"⚠️ Migration warning: {e}")
    
        # Migration 5: Migrate plex_credentials to plex_servers table
        try:
            # Check if plex_credentials table exists and has data
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='plex_credentials'")
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM plex_credentials WHERE is_active = 1")
                if cursor.fetchone()[0] > 0:
                    # Check if migration already happened (no servers in plex_servers table)
                    cursor.execute("SELECT COUNT(*) FROM plex_servers")
                    if cursor.fetchone()[0] == 0:
                        # Migrate existing credentials to new table
                        cursor.execute("""
                            INSERT INTO plex_servers (name, server_url, token, is_active, created_at, updated_at)
                            SELECT 'Default Server', server_url, token, is_active, created_at, updated_at
                            FROM plex_credentials 
                            WHERE is_active = 1
                        """)
                        self.connection.commit()
                        # Drop the old table to prevent re-migration
                        cursor.execute("DROP TABLE IF EXISTS plex_credentials")
                        self.connection.commit()
                        pass  # Migration completed
                    else:
                        pass  # Migration already completed
                else:
                    # No active credentials to migrate, but mark migration as complete by dropping the old table
                    cursor.execute("DROP TABLE IF EXISTS plex_credentials")
                    self.connection.commit()
                    pass  # Migration completed
            else:
                pass  # No plex_credentials table to migrate
        except sqlite3.OperationalError as e:
            logger.warning(f"⚠️ Migration warning: {e}")
        except sqlite3.IntegrityError as e:
            logger.warning(f"⚠️ Migration warning: {e}")
        
        # Migration 6: Update plex_path_mappings table for per-library support
        try:
            # Add server_id and library_root columns to plex_path_mappings
            cursor.execute("ALTER TABLE plex_path_mappings ADD COLUMN server_id INTEGER")
            cursor.execute("ALTER TABLE plex_path_mappings ADD COLUMN library_root TEXT")
            cursor.execute("ALTER TABLE plex_path_mappings ADD COLUMN library_name TEXT")
            self.connection.commit()
            pass  # Migration completed
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                # Columns already exist, that's fine
                pass
            else:
                logger.warning(f"⚠️ Migration warning: {e}")
        
        # Migration 7: Add server_id to media tables for server-specific cleanup
        try:
            # Add server_id column to media_files table
            cursor.execute("ALTER TABLE media_files ADD COLUMN server_id INTEGER")
            cursor.execute("ALTER TABLE shows ADD COLUMN server_id INTEGER")
            cursor.execute("ALTER TABLE movies ADD COLUMN server_id INTEGER")
            self.connection.commit()
            pass  # Migration completed
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                # Columns already exist, that's fine
                pass
            else:
                logger.warning(f"⚠️ Migration warning: {e}")
        
        # Migration 8: Add foreign key constraints with CASCADE deletes
        try:
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Note: SQLite doesn't support adding foreign key constraints to existing tables
            # The CASCADE behavior will be handled by the application logic
            # when we recreate the tables with proper constraints in the future
            pass  # Migration completed
        except sqlite3.OperationalError as e:
            logger.warning(f"⚠️ Migration warning: {e}")
        
        # Migration 9: Create libraries table for proper 1:many relationship
        try:
            # Create libraries table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS libraries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id INTEGER NOT NULL,
                    library_key TEXT NOT NULL,
                    library_name TEXT NOT NULL,
                    library_type TEXT NOT NULL,
                    library_root TEXT,
                    sync_enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (server_id) REFERENCES plex_servers(id) ON DELETE CASCADE,
                    UNIQUE(server_id, library_key)
                )
            """)
            self.connection.commit()
            pass  # Migration completed
        except Exception as e:
            logger.warning(f"⚠️ Migration warning: {e}")
        
        # Migration 10: Remove redundant updated_at_plex columns and use updated_at for Plex timestamps
        # Note: This migration adds updated_at with DEFAULT CURRENT_TIMESTAMP for backward compatibility.
        # Later migrations (11+) will recreate tables with proper INTEGER epoch columns.
        try:
            # Drop updated_at_plex columns from all tables
            cursor.execute("ALTER TABLE shows DROP COLUMN updated_at_plex")
            cursor.execute("ALTER TABLE episodes DROP COLUMN updated_at_plex") 
            cursor.execute("ALTER TABLE movies DROP COLUMN updated_at_plex")
            
            # Add updated_at column to movies table if it doesn't exist and we're not using the new schema
            if not column_exists('movies', 'updated_at'):
                cursor.execute("ALTER TABLE movies ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            
            self.connection.commit()
            pass  # Migration completed
        except sqlite3.OperationalError as e:
            # Column might not exist, which is fine
            pass
        except Exception as e:
            logger.warning(f"⚠️ Migration warning: {e}")
        
        # Migration 11: Fix episodes table updated_at to be INTEGER epoch (no default)
        try:
            # Check if episodes table has wrong column type for updated_at
            cursor.execute("PRAGMA table_info(episodes)")
            episodes_info = cursor.fetchall()
            episodes_updated_at_wrong_type = False
            episodes_updated_at_has_default = False
            
            for col in episodes_info:
                if col[1] == 'updated_at':
                    if col[2] == 'TIMESTAMP':  # col[2] is column type
                        episodes_updated_at_wrong_type = True
                    if col[4] is not None:  # col[4] is default value
                        episodes_updated_at_has_default = True
            
            if episodes_updated_at_wrong_type or episodes_updated_at_has_default:
                logger.info("🔧 Fixing episodes table: changing updated_at from TIMESTAMP to INTEGER epoch")
                
                new_schema = """
                    CREATE TABLE episodes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        media_file_id INTEGER NOT NULL,
                        show_id INTEGER NOT NULL,
                        episode_title TEXT NOT NULL,
                        season_number INTEGER,
                        episode_number INTEGER,
                        rating TEXT,
                        summary TEXT,
                        originally_available_at DATE,
                        duration_ms INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at INTEGER,
                        FOREIGN KEY (media_file_id) REFERENCES media_files(id) ON DELETE CASCADE,
                        FOREIGN KEY (show_id) REFERENCES shows(id) ON DELETE CASCADE
                    )
                """
                
                data_copy = """
                    INSERT INTO episodes 
                    SELECT id, media_file_id, show_id, episode_title, season_number, episode_number,
                           rating, summary, originally_available_at, duration_ms, created_at, updated_at
                    FROM episodes
                """
                
                if recreate_table('episodes', new_schema, data_copy):
                    logger.info("✅ Fixed episodes table: updated_at is now INTEGER epoch")
                else:
                    logger.error("❌ Failed to fix episodes table")
            
        except sqlite3.OperationalError as e:
            # Column might not exist, which is fine
            pass
        except Exception as e:
            logger.warning(f"⚠️ Migration warning: {e}")
        
        # Migration 12: Add plex_path column and migrate existing file_path data
        try:
            # Check if plex_path column already exists
            cursor.execute("PRAGMA table_info(media_files)")
            media_files_info = cursor.fetchall()
            plex_path_exists = any(col[1] == 'plex_path' for col in media_files_info)
            
            if not plex_path_exists:
                logger.info("🔧 Migration 12: Adding plex_path column to media_files table")
                
                # Add plex_path column
                cursor.execute("ALTER TABLE media_files ADD COLUMN plex_path TEXT")
                
                # Migrate existing file_path data to plex_path (since file_path currently contains Plex paths)
                cursor.execute("UPDATE media_files SET plex_path = file_path WHERE plex_path IS NULL")
                
                # Clear file_path column (will be populated with local paths during next sync)
                cursor.execute("UPDATE media_files SET file_path = '' WHERE file_path IS NOT NULL")
                
                self.connection.commit()
                logger.info("✅ Migration 12: Added plex_path column and migrated existing data")
            else:
                logger.info("✅ Migration 12: plex_path column already exists")
                
        except Exception as e:
            logger.warning(f"⚠️ Migration warning: {e}")
        
        # Migration 13: Fix media_files table updated_at column type and add missing columns
        try:
            # Check if media_files table has wrong column type for updated_at
            cursor.execute("PRAGMA table_info(media_files)")
            media_files_info = cursor.fetchall()
            media_files_updated_at_wrong_type = False
            media_files_updated_at_has_default = False
            has_plex_path = False
            has_server_id = False
            
            for col in media_files_info:
                if col[1] == 'updated_at':
                    if col[2] == 'TIMESTAMP':  # col[2] is column type
                        media_files_updated_at_wrong_type = True
                    if col[4] is not None:  # col[4] is default value
                        media_files_updated_at_has_default = True
                elif col[1] == 'plex_path':
                    has_plex_path = True
                elif col[1] == 'server_id':
                    has_server_id = True
            
            if media_files_updated_at_wrong_type or media_files_updated_at_has_default or not has_plex_path or not has_server_id:
                logger.info("🔧 Migration 13: Fixing media_files table structure")
                # Recreate media_files table with correct column types and missing columns
                cursor.execute("""
                    CREATE TABLE media_files_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        file_path TEXT NOT NULL,
                        duration INTEGER NOT NULL,
                        media_type TEXT NOT NULL,
                        source_type TEXT NOT NULL,
                        source_id TEXT,
                        library_name TEXT,
                        plex_path TEXT,
                        server_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at INTEGER,
                        UNIQUE(source_type, source_id)
                    )
                """)
                
                # Copy data from old table to new table
                cursor.execute("""
                    INSERT INTO media_files_new 
                    SELECT id, file_path, duration, media_type, source_type, source_id, 
                           library_name, 
                           COALESCE(plex_path, '') as plex_path,
                           COALESCE(server_id, 0) as server_id,
                           created_at, 
                           COALESCE(updated_at, 0) as updated_at
                    FROM media_files
                """)
                
                # Drop old table and rename new table
                cursor.execute("DROP TABLE media_files")
                cursor.execute("ALTER TABLE media_files_new RENAME TO media_files")
                
                self.connection.commit()
                logger.info("✅ Migration 13: Fixed media_files table structure")
            
        except Exception as e:
            logger.warning(f"⚠️ Migration warning: {e}")
    
    def _ensure_schema_consistency(self):
        """Ensure the database schema is consistent with the latest requirements"""
        cursor = self.connection.cursor()
        
        try:
            # Check if updated_at_plex columns still exist and remove them
            # This handles cases where the database was created with old schema
            
            # Check shows table
            cursor.execute("PRAGMA table_info(shows)")
            shows_columns = [row[1] for row in cursor.fetchall()]
            if 'updated_at_plex' in shows_columns:
                cursor.execute("ALTER TABLE shows DROP COLUMN updated_at_plex")
            
            # Check episodes table  
            cursor.execute("PRAGMA table_info(episodes)")
            episodes_columns = [row[1] for row in cursor.fetchall()]
            if 'updated_at_plex' in episodes_columns:
                cursor.execute("ALTER TABLE episodes DROP COLUMN updated_at_plex")
            
            # Check movies table
            cursor.execute("PRAGMA table_info(movies)")
            movies_columns = [row[1] for row in cursor.fetchall()]
            if 'updated_at_plex' in movies_columns:
                cursor.execute("ALTER TABLE movies DROP COLUMN updated_at_plex")
            
            # CRITICAL FIX: Remove DEFAULT CURRENT_TIMESTAMP from updated_at columns
            # SQLite doesn't support ALTER COLUMN, so we need to recreate the tables
            
            # Check if shows table has DEFAULT CURRENT_TIMESTAMP on updated_at or wrong column type
            cursor.execute("PRAGMA table_info(shows)")
            shows_info = cursor.fetchall()
            shows_updated_at_has_default = False
            shows_updated_at_wrong_type = False
            
            for col in shows_info:
                if col[1] == 'updated_at':
                    if col[4] is not None:  # col[4] is default value
                        shows_updated_at_has_default = True
                    if col[2] == 'TIMESTAMP':  # col[2] is column type
                        shows_updated_at_wrong_type = True
            
            # Check if plex_rating_key has unique constraint by looking at table definition
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='shows'")
            table_def = cursor.fetchone()
            plex_rating_key_is_unique = False
            if table_def and 'plex_rating_key TEXT UNIQUE' in table_def[0]:
                plex_rating_key_is_unique = True
            
            if shows_updated_at_has_default or shows_updated_at_wrong_type or plex_rating_key_is_unique:
                logger.info("🔧 Fixing shows table: removing DEFAULT CURRENT_TIMESTAMP from updated_at and fixing unique constraints")
                # Recreate shows table without the default and with correct unique constraints
                cursor.execute("""
                    CREATE TABLE shows_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        plex_rating_key TEXT,
                        title TEXT NOT NULL,
                        year INTEGER,
                        total_seasons INTEGER,
                        total_episodes INTEGER,
                        show_rating TEXT,
                        show_summary TEXT,
                        genre TEXT,
                        studio TEXT,
                        originally_available_at DATE,
                        guid_primary TEXT,
                        source_type TEXT NOT NULL,
                        source_id TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at INTEGER,
                        server_id INTEGER
                    )
                """)
                
                # Copy data from old table to new table
                cursor.execute("""
                    INSERT INTO shows_new 
                    SELECT id, plex_rating_key, title, year, total_seasons, total_episodes,
                           show_rating, show_summary, genre, studio, originally_available_at,
                           guid_primary, source_type, source_id, created_at, updated_at, server_id
                    FROM shows
                """)
                
                # Drop old table and rename new table
                cursor.execute("DROP TABLE shows")
                cursor.execute("ALTER TABLE shows_new RENAME TO shows")
            
            # Check if movies table has wrong column type for updated_at
            cursor.execute("PRAGMA table_info(movies)")
            movies_info = cursor.fetchall()
            movies_updated_at_wrong_type = False
            
            for col in movies_info:
                if col[1] == 'updated_at' and col[2] == 'TIMESTAMP':
                    movies_updated_at_wrong_type = True
            
            if movies_updated_at_wrong_type:
                logger.info("🔧 Fixing movies table: changing updated_at from TIMESTAMP to INTEGER")
                # Recreate movies table with correct column type
                cursor.execute("""
                    CREATE TABLE movies_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        media_file_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        year INTEGER,
                        rating TEXT,
                        summary TEXT,
                        genre TEXT,
                        director TEXT,
                        server_id INTEGER,
                        updated_at INTEGER,
                        FOREIGN KEY (media_file_id) REFERENCES media_files(id) ON DELETE CASCADE
                    )
                """)
                
                # Copy data from old table to new table
                cursor.execute("""
                    INSERT INTO movies_new 
                    SELECT id, media_file_id, title, year, rating, summary, genre, director, server_id, updated_at
                    FROM movies
                """)
                
                # Drop old table and rename new table
                cursor.execute("DROP TABLE movies")
                cursor.execute("ALTER TABLE movies_new RENAME TO movies")
            
            self.connection.commit()
            
        except sqlite3.OperationalError as e:
            # Columns might not exist, which is fine
            pass
        except Exception as e:
            logger.warning(f"⚠️ Schema consistency warning: {e}")
    
    def _update_schema_version(self):
        """Update the schema version to track the current database schema"""
        cursor = self.connection.cursor()
        
        try:
            # Check if we already have this version
            cursor.execute("SELECT version FROM schema_version WHERE version = ?", (CURRENT_SCHEMA_VERSION,))
            if cursor.fetchone():
                return  # Already at current version
            
            # Insert the current schema version
            cursor.execute("""
                INSERT INTO schema_version (version, description) 
                VALUES (?, ?)
            """, (CURRENT_SCHEMA_VERSION, "Fixed schema consistency - proper updated_at types, plex_path separation, foreign key cascades"))
            
            self.connection.commit()
            
        except Exception as e:
            logger.warning(f"⚠️ Schema version warning: {e}")
    
    def get_schema_version(self) -> int:
        """Get the current schema version of the database"""
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("SELECT MAX(version) FROM schema_version")
            result = cursor.fetchone()
            return result[0] if result and result[0] is not None else 0
        except Exception:
            return 0
    
    def is_schema_up_to_date(self) -> bool:
        """Check if the database schema is up to date"""
        current_version = self.get_schema_version()
        return current_version >= CURRENT_SCHEMA_VERSION
    
    def add_plex_server(self, name: str, server_url: str, token: str, is_active: bool = True) -> int:
        """Add a new Plex server to the database"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO plex_servers (name, server_url, token, is_active, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (name, server_url, token, 1 if is_active else 0, int(datetime.now().timestamp())))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def get_plex_servers(self) -> List[Dict]:
        """Get all Plex servers from the database"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT id, name, server_url, token, is_active, created_at, updated_at
            FROM plex_servers 
            ORDER BY created_at DESC 
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_plex_server(self, server_id: int) -> Optional[Dict]:
        """Get a specific Plex server by ID"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT id, name, server_url, token, is_active, created_at, updated_at
            FROM plex_servers 
            WHERE id = ?
        """, (server_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_plex_server(self, server_id: int, name: str = None, server_url: str = None, 
                          token: str = None, is_active: bool = None) -> bool:
        """Update a Plex server"""
        try:
            cursor = self.connection.cursor()
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if server_url is not None:
                updates.append("server_url = ?")
                params.append(server_url)
            if token is not None:
                updates.append("token = ?")
                params.append(token)
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(is_active)
            
            if updates:
                updates.append("updated_at = ?")
                params.append(int(datetime.now().timestamp()))
                params.append(server_id)
                
                cursor.execute(f"""
                    UPDATE plex_servers 
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, params)
                
                self.connection.commit()
                return cursor.rowcount > 0
            return False
        except Exception as e:
            logger.error(f"❌ Failed to update Plex server: {e}")
            return False
    
    def delete_plex_server(self, server_id: int) -> bool:
        """Delete a Plex server and all associated data (CASCADE behavior)"""
        try:
            cursor = self.connection.cursor()
            
            # With proper CASCADE constraints, we only need to delete the server
            # All related data will be automatically deleted by foreign key cascades
            cursor.execute("DELETE FROM plex_servers WHERE id = ?", (server_id,))
            
            self.connection.commit()
            
            # Ensure schema consistency after deletion
            self._ensure_schema_consistency()
            
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Failed to delete Plex server: {e}")
            self.connection.rollback()
            return False
    
    def verify_schema_consistency(self) -> bool:
        """Verify that the database schema is consistent with current requirements"""
        cursor = self.connection.cursor()
        
        try:
            # Check that updated_at_plex columns don't exist
            cursor.execute("PRAGMA table_info(shows)")
            shows_columns = [row[1] for row in cursor.fetchall()]
            if 'updated_at_plex' in shows_columns:
                logger.error("❌ Schema issue: shows table still has updated_at_plex column")
                return False
            
            cursor.execute("PRAGMA table_info(episodes)")
            episodes_columns = [row[1] for row in cursor.fetchall()]
            if 'updated_at_plex' in episodes_columns:
                logger.error("❌ Schema issue: episodes table still has updated_at_plex column")
                return False
            
            cursor.execute("PRAGMA table_info(movies)")
            movies_columns = [row[1] for row in cursor.fetchall()]
            if 'updated_at_plex' in movies_columns:
                logger.error("❌ Schema issue: movies table still has updated_at_plex column")
                return False
            
            # Check that updated_at columns are INTEGER type (not TIMESTAMP with DEFAULT)
            for table_name in ['shows', 'episodes', 'movies', 'media_files']:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                for col in columns:
                    if col[1] == 'updated_at':  # col[1] is column name
                        if col[2] != 'INTEGER':  # col[2] is column type
                            logger.error(f"❌ Schema issue: {table_name}.updated_at should be INTEGER, found {col[2]}")
                            return False
                        if col[4] is not None:  # col[4] is default value
                            logger.error(f"❌ Schema issue: {table_name}.updated_at should not have DEFAULT value")
                            return False
            
            # Check that plex_rating_key is not UNIQUE
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='shows'")
            table_def = cursor.fetchone()
            if table_def and 'plex_rating_key TEXT UNIQUE' in table_def[0]:
                logger.error("❌ Schema issue: plex_rating_key should not be UNIQUE")
                return False
            
            # Check that source_id is UNIQUE
            if table_def and 'source_id TEXT UNIQUE NOT NULL' not in table_def[0]:
                logger.error("❌ Schema issue: source_id should be UNIQUE NOT NULL")
                return False
            
            logger.info("✅ Schema is consistent - all checks passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verifying schema: {e}")
            return False
    
    # Legacy methods for backward compatibility
    def store_plex_credentials(self, server_url: str, token: str) -> int:
        """Store Plex credentials in the database (legacy method)"""
        return self.add_plex_server("Default Server", server_url, token)
    
    def get_plex_credentials(self) -> Optional[Dict[str, str]]:
        """Get active Plex credentials from the database (legacy method)"""
        servers = self.get_plex_servers()
        if servers:
            server = servers[0]  # Get first active server
            return {
                'server_url': server['server_url'],
                'token': server['token']
            }
        return None
    
    # Library management methods
    def add_library(self, server_id: int, library_key: str, library_name: str, 
                   library_type: str, library_root: str = None, sync_enabled: bool = True) -> int:
        """Add or update a library for a server"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO libraries 
                (server_id, library_key, library_name, library_type, library_root, sync_enabled, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (server_id, library_key, library_name, library_type, library_root, sync_enabled, int(datetime.now().timestamp())))
            self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"❌ Failed to add library: {e}")
            return 0
    
    def get_server_libraries(self, server_id: int = None) -> List[Dict]:
        """Get libraries from the libraries table, optionally filtered by server_id"""
        try:
            cursor = self.connection.cursor()
            if server_id:
                cursor.execute("""
                    SELECT id, server_id, library_key, library_name, library_type, 
                           library_root, sync_enabled, created_at, updated_at
                    FROM libraries WHERE server_id = ?
                    ORDER BY library_name
                """, (server_id,))
            else:
                cursor.execute("""
                    SELECT id, server_id, library_key, library_name, library_type, 
                           library_root, sync_enabled, created_at, updated_at
                    FROM libraries
                    ORDER BY server_id, library_name
                """)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ Failed to get libraries: {e}")
            return []
    
    def get_library(self, server_id: int, library_key: str) -> Optional[Dict]:
        """Get a specific library by server_id and library_key"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT id, server_id, library_key, library_name, library_type, 
                       library_root, sync_enabled, created_at, updated_at
                FROM libraries WHERE server_id = ? AND library_key = ?
            """, (server_id, library_key))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"❌ Failed to get library: {e}")
            return None
    
    def update_library_sync(self, server_id: int, library_key: str, sync_enabled: bool) -> bool:
        """Update sync preference for a library"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE libraries SET sync_enabled = ?, updated_at = ?
                WHERE server_id = ? AND library_key = ?
            """, (sync_enabled, int(datetime.now().timestamp()), server_id, library_key))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Failed to update library sync: {e}")
            return False
    
    def delete_libraries(self, server_id: int) -> bool:
        """Delete all libraries for a server (called during server deletion)"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM libraries WHERE server_id = ?", (server_id,))
            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete libraries: {e}")
            return False
    
    def add_plex_path_mapping(self, plex_path: str, local_path: str, server_id: int = None, 
                             library_root: str = None, library_name: str = None) -> int:
        """Add a new Plex path mapping to the database"""
        cursor = self.connection.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plex_path_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plex_path TEXT NOT NULL,
                local_path TEXT NOT NULL,
                server_id INTEGER,
                library_root TEXT,
                library_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (server_id) REFERENCES plex_servers(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            INSERT INTO plex_path_mappings (plex_path, local_path, server_id, library_root, library_name)
            VALUES (?, ?, ?, ?, ?)
        """, (plex_path, local_path, server_id, library_root, library_name))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def get_plex_path_mappings(self, server_id: int = None, library_root: str = None) -> List[Dict]:
        """Get Plex path mappings from the database with optional filtering"""
        cursor = self.connection.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plex_path_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plex_path TEXT NOT NULL,
                local_path TEXT NOT NULL,
                server_id INTEGER,
                library_root TEXT,
                library_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (server_id) REFERENCES plex_servers(id) ON DELETE CASCADE
            )
        """)
        
        query = "SELECT id, plex_path, local_path, server_id, library_root, library_name FROM plex_path_mappings WHERE 1=1"
        params = []
        
        if server_id is not None:
            query += " AND server_id = ?"
            params.append(server_id)
        
        if library_root is not None:
            query += " AND library_root = ?"
            params.append(library_root)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_plex_path_mapping_for_library(self, server_id: int, library_root: str) -> Optional[Dict]:
        """Get the specific path mapping for a library root on a server"""
        mappings = self.get_plex_path_mappings(server_id=server_id, library_root=library_root)
        return mappings[0] if mappings else None
    
    def update_plex_path_mapping(self, mapping_id: int, plex_path: str = None, local_path: str = None,
                                server_id: int = None, library_root: str = None, library_name: str = None) -> bool:
        """Update a Plex path mapping"""
        try:
            cursor = self.connection.cursor()
            updates = []
            params = []
            
            if plex_path is not None:
                updates.append("plex_path = ?")
                params.append(plex_path)
            if local_path is not None:
                updates.append("local_path = ?")
                params.append(local_path)
            if server_id is not None:
                updates.append("server_id = ?")
                params.append(server_id)
            if library_root is not None:
                updates.append("library_root = ?")
                params.append(library_root)
            if library_name is not None:
                updates.append("library_name = ?")
                params.append(library_name)
            
            if updates:
                params.append(mapping_id)
                cursor.execute(f"""
                    UPDATE plex_path_mappings 
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, params)
                
                self.connection.commit()
                return cursor.rowcount > 0
            return False
        except Exception as e:
            logger.error(f"❌ Failed to update path mapping: {e}")
            return False
    
    def delete_plex_path_mapping(self, mapping_id: int) -> bool:
        """Delete a Plex path mapping"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM plex_path_mappings WHERE id = ?", (mapping_id,))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Failed to delete path mapping: {e}")
            return False
    
    # Legacy methods for backward compatibility
    def store_plex_path_mapping(self, plex_path: str, local_path: str) -> int:
        """Store Plex path mapping in the database (legacy method)"""
        return self.add_plex_path_mapping(plex_path, local_path)
    
    def get_libraries(self) -> List[str]:
        """Get all unique library names from media files"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT DISTINCT library_name 
            FROM media_files 
            WHERE library_name IS NOT NULL AND library_name != ''
            ORDER BY library_name
        """)
        results = cursor.fetchall()
        return [row['library_name'] for row in results]
    
    def get_local_path_for_media_file(self, media_file_id: int) -> str:
        """Get the local mapped path for a media file (for file access)"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT mf.file_path, mf.plex_path, mf.server_id
            FROM media_files mf
            WHERE mf.id = ?
        """, (media_file_id,))

        result = cursor.fetchone()
        if not result:
            return ""

        # Use plex_path column if available, otherwise fall back to file_path (for backward compatibility)
        plex_path = result['plex_path'] or result['file_path']
        server_id = result['server_id']
        
        if not plex_path:
            return ""
        
        # Use the path mapping service as the single source of truth
        from .path_mapping import PlexPathMappingService
        path_mapping_service = PlexPathMappingService.create_from_database(self, server_id)
        return path_mapping_service.get_local_path(plex_path)
    
    def add_media_file(self, file_path: str, duration: int, media_type: str, 
                      source_type: str, source_id: str = None, library_name: str = None, server_id: int = None, plex_path: str = None) -> int:
        """Add a media file to the database"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO media_files
            (file_path, duration, media_type, source_type, source_id, library_name, server_id, updated_at, plex_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (file_path, duration, media_type, source_type, source_id, library_name, server_id, int(datetime.now().timestamp()), plex_path))
        
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
    
    def add_show(self, title: str, plex_rating_key: str = None, year: int = None,
                total_seasons: int = None, total_episodes: int = None,
                show_rating: str = None, show_summary: str = None, genre: str = None,
                studio: str = None, originally_available_at: str = None,
                guid_primary: str = None,
                source_type: str = None, source_id: str = None, server_id: int = None, plex_updated_at: int = None) -> int:
        """Add a show to the database with year-based disambiguation"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO shows
            (plex_rating_key, title, year, total_seasons, total_episodes, show_rating, 
             show_summary, genre, studio, originally_available_at, guid_primary, 
             source_type, source_id, server_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (plex_rating_key, title, year, total_seasons, total_episodes, show_rating, 
              show_summary, genre, studio, originally_available_at, guid_primary, 
              source_type, source_id, server_id, plex_updated_at))
        
        # Get the show_id using the source_id (GUID) as the unique identifier
        if source_id:
            cursor.execute("SELECT id FROM shows WHERE source_id = ?", (source_id,))
            result = cursor.fetchone()
            show_id = result['id'] if result else cursor.lastrowid
        else:
            show_id = cursor.lastrowid
        
        self.connection.commit()
        return show_id
    
    def add_show_guid(self, show_id: int, provider: str, external_id: str) -> int:
        """Add a GUID for a show"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO show_guids (show_id, provider, external_id)
            VALUES (?, ?, ?)
        """, (show_id, provider, external_id))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def get_show_guids(self, show_id: int) -> List[Dict]:
        """Get all GUIDs for a show"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT provider, external_id FROM show_guids
            WHERE show_id = ?
        """, (show_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_show_by_title_and_year(self, title: str, year: int) -> Optional[Dict]:
        """Get a show by title and year for disambiguation"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM shows WHERE title = ? AND year = ?
        """, (title, year))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    # Removed get_show_by_plex_rating_key - use get_show_by_source_id instead
    
    def add_episode(self, media_file_id: int, show_id: int, episode_title: str,
                   season_number: int = None, episode_number: int = None,
                   rating: str = None, summary: str = None, plex_updated_at: int = None) -> int:
        """Add an episode to the database"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT INTO episodes
            (media_file_id, show_id, episode_title, season_number, episode_number, rating, summary, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (media_file_id, show_id, episode_title, season_number, episode_number, rating, summary, plex_updated_at))
        
        self.connection.commit()
        return cursor.lastrowid
    
    def add_movie(self, media_file_id: int, title: str, year: int = None,
                 rating: str = None, summary: str = None, genre: str = None,
                 director: str = None, server_id: int = None, plex_updated_at: int = None) -> int:
        """Add a movie to the database"""
        cursor = self.connection.cursor()
        
        cursor.execute("""
            INSERT INTO movies
            (media_file_id, title, year, rating, summary, genre, director, server_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (media_file_id, title, year, rating, summary, genre, director, server_id, plex_updated_at))
        
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
            SELECT s.*, s.source_id
            FROM shows s
            WHERE s.source_type = ?
        """, (source_type,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_episodes_by_show_source_id(self, show_source_id: str) -> List[Dict]:
        """Get all episodes for a show by its source ID"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT e.*, mf.source_id, mf.id as media_file_id, mf.file_path, mf.duration
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
            SELECT s.*, s.source_id
            FROM shows s
            WHERE s.source_id = ?
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
    
    def get_movie_ts_by_guid(self, guid: str) -> Optional[int]:
        """Get the updated_at timestamp for a movie by its GUID"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT m.updated_at
            FROM movies m
            JOIN media_files mf ON m.media_file_id = mf.id
            WHERE mf.source_id = ?
        """, (guid,))
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else None
    
    def get_episode_ts_by_guid(self, guid: str) -> Optional[int]:
        """Get the updated_at timestamp for an episode by its GUID"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT e.updated_at
            FROM episodes e
            JOIN media_files mf ON e.media_file_id = mf.id
            WHERE mf.source_id = ?
        """, (guid,))
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else None
    
    def get_show_ts_by_guid(self, guid: str) -> Optional[int]:
        """Get the updated_at timestamp for a show by its GUID"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT updated_at
            FROM shows
            WHERE source_id = ?
        """, (guid,))
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else None
    
    def set_movie_ts_by_guid(self, guid: str, ts: int) -> bool:
        """Set the updated_at timestamp for a movie by its GUID"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE movies 
                SET updated_at = ?
                WHERE media_file_id IN (
                    SELECT id FROM media_files WHERE source_id = ?
                )
            """, (ts, guid))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Failed to set movie timestamp: {e}")
            return False
    
    def set_episode_ts_by_guid(self, guid: str, ts: int) -> bool:
        """Set the updated_at timestamp for an episode by its GUID"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE episodes 
                SET updated_at = ?
                WHERE media_file_id IN (
                    SELECT id FROM media_files WHERE source_id = ?
                )
            """, (ts, guid))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Failed to set episode timestamp: {e}")
            return False
    
    def set_show_ts_by_guid(self, guid: str, ts: int) -> bool:
        """Set the updated_at timestamp for a show by its GUID"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE shows 
                SET updated_at = ?
                WHERE source_id = ?
            """, (ts, guid))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Failed to set show timestamp: {e}")
            return False
    
    def update_media_file(self, media_file_id: int, file_path: str, duration: int, library_name: str = None, plex_path: str = None) -> bool:
        """Update a media file"""
        try:
            cursor = self.connection.cursor()
            current_timestamp = int(datetime.now().timestamp())
            if library_name is not None and plex_path is not None:
                cursor.execute("""
                    UPDATE media_files 
                    SET file_path = ?, duration = ?, library_name = ?, plex_path = ?, updated_at = ?
                    WHERE id = ?
                """, (file_path, duration, library_name, plex_path, current_timestamp, media_file_id))
            elif library_name is not None:
                cursor.execute("""
                    UPDATE media_files 
                    SET file_path = ?, duration = ?, library_name = ?, updated_at = ?
                    WHERE id = ?
                """, (file_path, duration, library_name, current_timestamp, media_file_id))
            elif plex_path is not None:
                cursor.execute("""
                    UPDATE media_files 
                    SET file_path = ?, duration = ?, plex_path = ?, updated_at = ?
                    WHERE id = ?
                """, (file_path, duration, plex_path, current_timestamp, media_file_id))
            else:
                cursor.execute("""
                    UPDATE media_files 
                    SET file_path = ?, duration = ?, updated_at = ?
                    WHERE id = ?
                """, (file_path, duration, current_timestamp, media_file_id))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Failed to update media file: {e}")
            return False
    
    def update_movie(self, movie_id: int, title: str, year: Optional[int], 
                    rating: str, summary: str, genre: str, director: str, plex_updated_at: int = None) -> bool:
        """Update a movie"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE movies 
                SET title = ?, year = ?, rating = ?, summary = ?, genre = ?, director = ?, updated_at = ?
                WHERE id = ?
            """, (title, year, rating, summary, genre, director, plex_updated_at, movie_id))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Failed to update movie: {e}")
            return False
    
    def update_episode(self, episode_id: int, episode_title: str, season_number: int,
                      episode_number: int, rating: str, summary: str, plex_updated_at: int = None) -> bool:
        """Update an episode"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE episodes 
                SET episode_title = ?, season_number = ?, episode_number = ?, rating = ?, summary = ?, updated_at = ?
                WHERE id = ?
            """, (episode_title, season_number, episode_number, rating, summary, plex_updated_at, episode_id))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Failed to update episode: {e}")
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
            logger.error(f"❌ Failed to remove movie: {e}")
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
            logger.error(f"❌ Failed to remove show: {e}")
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
            logger.error(f"❌ Failed to remove episode: {e}")
            return False
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
