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
- **path_mappings**: How to find your video files on your computer

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
- **Schema Version**: 3 (automatically migrates from older versions)
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
CURRENT_SCHEMA_VERSION = 3


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
    - **path_mappings**: Path conversion rules for each server
    
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
        self.apply_retrovue_schema_upgrade_v5()
        self.migrate_media_files_drop_file_path()
        self.migrate_drop_legacy_unique_source()
        self.repair_source_id_for_episodes()
        self.apply_retrovue_schema_upgrade_media_files()
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
                duration INTEGER NOT NULL,
                media_type TEXT NOT NULL,  -- 'movie', 'episode', 'commercial', 'bumper'
                source_type TEXT NOT NULL,  -- 'plex', 'tmm', 'manual'
                source_id TEXT,  -- External ID (Plex key, TMM file path, etc.)
                library_name TEXT,  -- Library name from source (e.g., "Horror", "3D Movies")
                plex_path TEXT,  -- Plex file path (separate from local file_path)
                server_id INTEGER,  -- Server ID for multi-server support
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at INTEGER,  -- Unix timestamp from Plex
                FOREIGN KEY (server_id) REFERENCES plex_servers(id) ON DELETE CASCADE,
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
        
        # Performance indexes for UPSERT and browse operations
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_media_files_source ON media_files(source_type, source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_episodes_media ON episodes(media_file_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_episodes_show ON episodes(show_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_shows_source ON shows(source_type, source_id)")
        
        self.connection.commit()
    
    def _column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        cursor = self.connection.cursor()
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            return column_name in columns
        except Exception as e:
            logger.warning(f"⚠️ Error checking column {column_name} in {table_name}: {e}")
            return False
    
    def _run_migrations(self):
        """Run database migrations to update schema"""
        cursor = self.connection.cursor()
        
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
            if not self._column_exists('media_files', 'library_name'):
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
            if not self._column_exists('shows', 'updated_at'):
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
            if not self._column_exists('episodes', 'updated_at'):
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
        
        # Migration 6: Update path_mappings table for per-library support
        try:
            # Check if plex_path_mappings table exists before trying to alter it
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='plex_path_mappings'")
            if cursor.fetchone():
                # Add server_id and library_root columns to path_mappings
                cursor.execute("ALTER TABLE plex_path_mappings ADD COLUMN server_id INTEGER")
                cursor.execute("ALTER TABLE plex_path_mappings ADD COLUMN library_root TEXT")
                cursor.execute("ALTER TABLE plex_path_mappings ADD COLUMN library_name TEXT")
                self.connection.commit()
                logger.info("✅ Migration 6: Updated plex_path_mappings table")
            else:
                logger.info("✅ Migration 6: plex_path_mappings table doesn't exist, skipping")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                # Columns already exist, that's fine
                logger.info("✅ Migration 6: Columns already exist")
            elif "no such table" in str(e).lower():
                # Table doesn't exist, that's fine
                logger.info("✅ Migration 6: plex_path_mappings table doesn't exist, skipping")
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
            if not self._column_exists('movies', 'updated_at'):
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
                
                # Migrate existing file_path data to plex_path (if file_path column still exists)
                try:
                    cursor.execute("UPDATE media_files SET plex_path = file_path WHERE plex_path IS NULL AND file_path IS NOT NULL")
                except Exception:
                    # file_path column may not exist anymore, that's fine
                    pass
                
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
                        duration INTEGER NOT NULL,
                        media_type TEXT NOT NULL,
                        source_type TEXT NOT NULL,
                        source_id TEXT,
                        library_name TEXT,
                        plex_path TEXT,
                        server_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at INTEGER,
                        FOREIGN KEY (server_id) REFERENCES plex_servers(id) ON DELETE CASCADE
                    )
                """)
                
                # Copy data from old table to new table
                cursor.execute("""
                    INSERT INTO media_files_new 
                    SELECT id, duration, media_type, source_type, source_id, 
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
        
        # Migration 14: Add foreign key constraint to media_files if missing
        try:
            # Check if foreign key constraint exists
            cursor.execute("PRAGMA foreign_key_list(media_files)")
            fk_list = cursor.fetchall()
            has_server_fk = any(fk[2] == 'server_id' for fk in fk_list)
            
            if not has_server_fk:
                logger.info("🔧 Migration 14: Adding foreign key constraint to media_files")
                # SQLite doesn't support adding foreign keys to existing tables
                # We need to recreate the table with the constraint
                
                # Check if media_files_new already exists and drop it
                cursor.execute("DROP TABLE IF EXISTS media_files_new")
                
                cursor.execute("""
                    CREATE TABLE media_files_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        duration INTEGER NOT NULL,
                        media_type TEXT NOT NULL,
                        source_type TEXT NOT NULL,
                        source_id TEXT,
                        library_name TEXT,
                        plex_path TEXT,
                        server_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at INTEGER,
                        FOREIGN KEY (server_id) REFERENCES plex_servers(id) ON DELETE CASCADE
                    )
                """)
                
                # Copy data from old table to new table
                # Only copy the columns that exist in both tables
                try:
                    # Check which columns exist in the old table
                    cursor.execute("PRAGMA table_info(media_files)")
                    old_columns = {row[1] for row in cursor.fetchall()}
                    
                    # Build column lists based on what actually exists
                    select_columns = []
                    insert_columns = []
                    
                    # Core columns that should always exist
                    core_columns = ['id', 'duration', 'media_type', 'source_type', 'source_id', 'library_name', 'plex_path', 'server_id']
                    for col in core_columns:
                        if col in old_columns:
                            select_columns.append(col)
                            insert_columns.append(col)
                    
                    # Optional columns
                    if 'created_at' in old_columns:
                        select_columns.append('created_at')
                        insert_columns.append('created_at')
                    else:
                        select_columns.append('CURRENT_TIMESTAMP as created_at')
                        insert_columns.append('created_at')
                    
                    if 'updated_at' in old_columns:
                        select_columns.append('updated_at')
                        insert_columns.append('updated_at')
                    else:
                        select_columns.append('0 as updated_at')
                        insert_columns.append('updated_at')
                    
                    # Execute the insert with dynamic column lists
                    insert_sql = f"""
                        INSERT INTO media_files_new ({', '.join(insert_columns)})
                        SELECT {', '.join(select_columns)}
                        FROM media_files
                    """
                    cursor.execute(insert_sql)
                except Exception as e:
                    logger.warning(f"⚠️ Migration 14 warning: Could not copy data: {e}")
                    # Continue with empty table if data copy fails
                
                # Drop old table and rename new table
                cursor.execute("DROP TABLE media_files")
                cursor.execute("ALTER TABLE media_files_new RENAME TO media_files")
                
                self.connection.commit()
                logger.info("✅ Migration 14: Added foreign key constraint to media_files")
            else:
                logger.info("✅ Migration 14: Foreign key constraint already exists")
                
        except Exception as e:
            logger.warning(f"⚠️ Migration 14 warning: {e}")
    
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
        
        # Migration 15: Add digest-based change detection and state management columns
        try:
            logger.info("🔧 Migration 15: Adding digest-based change detection and state management")
            
            # Add new columns to media_files table
            if not self._column_exists('media_files', 'digest'):
                cursor.execute("ALTER TABLE media_files ADD COLUMN digest TEXT")
            if not self._column_exists('media_files', 'updated_at_plex'):
                cursor.execute("ALTER TABLE media_files ADD COLUMN updated_at_plex BIGINT")
            if not self._column_exists('media_files', 'first_seen_at'):
                cursor.execute("ALTER TABLE media_files ADD COLUMN first_seen_at BIGINT")
            if not self._column_exists('media_files', 'last_seen_at'):
                cursor.execute("ALTER TABLE media_files ADD COLUMN last_seen_at BIGINT")
            if not self._column_exists('media_files', 'last_scan_at'):
                cursor.execute("ALTER TABLE media_files ADD COLUMN last_scan_at BIGINT")
            if not self._column_exists('media_files', 'state'):
                cursor.execute("ALTER TABLE media_files ADD COLUMN state TEXT DEFAULT 'ACTIVE'")
            if not self._column_exists('media_files', 'error_count'):
                cursor.execute("ALTER TABLE media_files ADD COLUMN error_count INT DEFAULT 0")
            if not self._column_exists('media_files', 'last_error_at'):
                cursor.execute("ALTER TABLE media_files ADD COLUMN last_error_at BIGINT")
            if not self._column_exists('media_files', 'last_error'):
                cursor.execute("ALTER TABLE media_files ADD COLUMN last_error TEXT")
            
            
            # Check if path_mappings table already exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='path_mappings'")
            path_mappings_exists = cursor.fetchone() is not None
            
            if not path_mappings_exists:
                # Create new path_mappings table for dynamic path resolution
                cursor.execute("""
                    CREATE TABLE path_mappings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        server_id INTEGER NOT NULL,
                        plex_prefix TEXT NOT NULL,
                        local_prefix TEXT NOT NULL,
                        created_at BIGINT DEFAULT (strftime('%s', 'now')),
                        FOREIGN KEY (server_id) REFERENCES plex_servers(id) ON DELETE CASCADE
                    )
                """)
                
                # Create index for path mappings
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_path_mappings_server ON path_mappings(server_id)")
                
                # Migrate existing path mappings if they exist
                try:
                    cursor.execute("SELECT COUNT(*) FROM plex_path_mappings")
                    if cursor.fetchone()[0] > 0:
                        logger.info("🔧 Migrating existing path mappings to new format")
                        cursor.execute("""
                            INSERT INTO path_mappings (server_id, plex_prefix, local_prefix, created_at)
                            SELECT 
                                COALESCE(server_id, 1) as server_id,
                                plex_path as plex_prefix,
                                local_path as local_prefix,
                                strftime('%s', 'now') as created_at
                            FROM plex_path_mappings
                            WHERE plex_path IS NOT NULL AND local_path IS NOT NULL
                        """)
                except sqlite3.OperationalError as e:
                    # Old table might not exist, that's fine - don't log as warning
                    if "no such table" not in str(e).lower():
                        logger.warning(f"⚠️ Error migrating path mappings: {e}")
                
                # Drop old path mappings table
                cursor.execute("DROP TABLE IF EXISTS plex_path_mappings")
            else:
                logger.info("✅ Migration 15: path_mappings table already exists")
            
            self.connection.commit()
            logger.info("✅ Migration 15: Added digest-based change detection and state management")
            
        except Exception as e:
            logger.warning(f"⚠️ Migration 15 warning: {e}")
        
        # Migration 16: Add last_synced_at column to libraries table
        try:
            if not self._column_exists('libraries', 'last_synced_at'):
                cursor.execute("ALTER TABLE libraries ADD COLUMN last_synced_at INTEGER")
                self.connection.commit()
                logger.info("✅ Migration 16: Added last_synced_at column to libraries table")
            else:
                logger.info("✅ Migration 16: last_synced_at column already exists")
        except Exception as e:
            logger.warning(f"⚠️ Migration 16 warning: {e}")
        
        # Migration 17: Add library_id column to shows table
        try:
            if not self._column_exists('shows', 'library_id'):
                cursor.execute("ALTER TABLE shows ADD COLUMN library_id INTEGER")
                self.connection.commit()
                logger.info("✅ Migration 17: Added library_id column to shows table")
            else:
                logger.info("✅ Migration 17: library_id column already exists")
        except Exception as e:
            logger.warning(f"⚠️ Migration 17 warning: {e}")
        
        # Migration 18: Add plex_rating_key column to episodes table
        try:
            if not self._column_exists('episodes', 'plex_rating_key'):
                cursor.execute("ALTER TABLE episodes ADD COLUMN plex_rating_key TEXT")
                self.connection.commit()
                logger.info("✅ Migration 18: Added plex_rating_key column to episodes table")
            else:
                logger.info("✅ Migration 18: plex_rating_key column already exists")
        except Exception as e:
            logger.warning(f"⚠️ Migration 18 warning: {e}")
    
    def apply_retrovue_schema_upgrade_v5(self):
        """Apply schema upgrade v5: add digest/state/timestamps, show tracking, and path mappings."""
        cursor = self.connection.cursor()
        
        def _exec(sql):
            try:
                cursor.execute(sql)
            except Exception:
                pass  # Ignore errors for columns that already exist
        
        # media_files: add digest/state/timestamps and identifiers
        _exec("ALTER TABLE media_files ADD COLUMN digest TEXT;")
        _exec("ALTER TABLE media_files ADD COLUMN updated_at_plex BIGINT;")
        _exec("ALTER TABLE media_files ADD COLUMN first_seen_at BIGINT;")
        _exec("ALTER TABLE media_files ADD COLUMN last_seen_at BIGINT;")
        _exec("ALTER TABLE media_files ADD COLUMN last_scan_at BIGINT;")
        _exec("ALTER TABLE media_files ADD COLUMN state TEXT DEFAULT 'ACTIVE';")
        _exec("ALTER TABLE media_files ADD COLUMN error_count INTEGER DEFAULT 0;")
        _exec("ALTER TABLE media_files ADD COLUMN last_error_at BIGINT;")
        _exec("ALTER TABLE media_files ADD COLUMN last_error TEXT;")
        _exec("ALTER TABLE media_files ADD COLUMN server_id INTEGER;")
        _exec("ALTER TABLE media_files ADD COLUMN library_id INTEGER;")
        _exec("ALTER TABLE media_files ADD COLUMN plex_rating_key TEXT;")
        _exec("ALTER TABLE media_files ADD COLUMN missing_since BIGINT;")
        _exec("ALTER TABLE media_files ADD COLUMN plex_path TEXT;")
        
        # Ensure uniqueness for upserts
        _exec("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_media_files_unique
          ON media_files(server_id, library_id, plex_rating_key);
        """)
        _exec("CREATE INDEX IF NOT EXISTS idx_media_files_state ON media_files(state);")
        
        # Ensure shows and episodes have proper UNIQUE indexes
        _exec("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_shows_srv_lib_rk
        ON shows(server_id, library_id, plex_rating_key);
        """)
        _exec("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_episodes_show_rk
        ON episodes(show_id, plex_rating_key);
        """)
        
        # Additional helpful indexes for episode lookups
        _exec("""
        CREATE INDEX IF NOT EXISTS idx_shows_source_id ON shows(source_id);
        """)
        _exec("""
        CREATE INDEX IF NOT EXISTS idx_shows_plex_rating_key ON shows(plex_rating_key);
        """)
        _exec("""
        CREATE INDEX IF NOT EXISTS idx_media_files_server_plex ON media_files(server_id, plex_rating_key);
        """)
        _exec("""
        CREATE INDEX IF NOT EXISTS idx_media_files_source_id ON media_files(source_id);
        """)
        _exec("""
        CREATE UNIQUE INDEX IF NOT EXISTS uidx_episodes_media_file_id ON episodes(media_file_id);
        """)
        _exec("""
        CREATE INDEX IF NOT EXISTS idx_episodes_show_id ON episodes(show_id);
        """)
        
        # shows_tracking: per-show selective-expansion tracking
        _exec("""
        CREATE TABLE IF NOT EXISTS shows_tracking (
          server_id INTEGER NOT NULL,
          library_id INTEGER NOT NULL,
          rating_key TEXT NOT NULL,
          show_digest TEXT,
          children_hydrated INTEGER DEFAULT 0,
          PRIMARY KEY (server_id, library_id, rating_key)
        );
        """)
        
        # path_mappings: unified table (plex_prefix/local_prefix)
        _exec("""
        CREATE TABLE IF NOT EXISTS path_mappings (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          server_id INTEGER NOT NULL,
          plex_prefix TEXT NOT NULL,
          local_prefix TEXT NOT NULL
        );
        """)
        _exec("CREATE INDEX IF NOT EXISTS idx_pathmap_server ON path_mappings(server_id);")
        
        self.connection.commit()
        logger.info("✅ Applied schema upgrade v5: digest/state tracking, show tracking, and path mappings")
    
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
            """, (CURRENT_SCHEMA_VERSION, "Added digest-based change detection, state management, and dynamic path mapping system"))
            
            self.connection.commit()
            
        except Exception as e:
            logger.warning(f"⚠️ Schema version warning: {e}")
    
    def _get_conn(self):
        """Be resilient to either .connection or .conn"""
        return getattr(self, "connection", None) or getattr(self, "conn", None)
    
    def _conn(self):
        return getattr(self, "connection", None) or getattr(self, "conn", None)

    def _table_columns(self, table_name: str) -> dict:
        cur = self._conn().execute(f"PRAGMA table_info({table_name})")
        cols = {}
        for cid, name, ctype, notnull, dflt, pk in cur.fetchall():
            cols[name] = {"type": ctype, "notnull": notnull, "default": dflt, "pk": pk}
        return cols

    def migrate_media_files_drop_file_path(self):
        """
        Rebuild media_files without file_path (fully removed).
        Safe to run multiple times.
        """
        conn = self._conn(); cur = conn.cursor()
        cols = self._table_columns("media_files")
        if not cols:
            raise RuntimeError("media_files table not found")
        # Only rebuild if file_path exists
        if "file_path" not in cols:
            return

        cur.execute("BEGIN IMMEDIATE")

        # Canonical target schema (no file_path)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS media_files__new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id INTEGER,
                library_id INTEGER,
                plex_rating_key TEXT,
                media_type TEXT,
                source_type TEXT,
                source_id TEXT,
                duration INTEGER,
                updated_at INTEGER,
                updated_at_plex BIGINT,
                first_seen_at BIGINT,
                last_seen_at BIGINT,
                last_scan_at BIGINT,
                state TEXT DEFAULT 'ACTIVE',
                error_count INTEGER DEFAULT 0,
                last_error_at BIGINT,
                last_error TEXT,
                missing_since BIGINT,
                plex_path TEXT,
                part_count INTEGER DEFAULT 0,
                streams_signature TEXT,
                digest TEXT
            );
        """)

        present = set(cols.keys())
        def has(c): return c in present
        def sel(c, default_sql):
            return c if has(c) else f"{default_sql} AS {c}"

        # Build a tolerant SELECT (use defaults if old column absent)
        select_sql = f"""
            INSERT INTO media_files__new (
                id, server_id, library_id, plex_rating_key, media_type, source_type, source_id,
                duration, updated_at, updated_at_plex, first_seen_at, last_seen_at, last_scan_at,
                state, error_count, last_error_at, last_error, missing_since, plex_path,
                part_count, streams_signature, digest
            )
            SELECT
                {sel('id','NULL')},
                {sel('server_id','0')},
                {sel('library_id','0')},
                {sel('plex_rating_key','NULL')},
                {sel('media_type','NULL')},
                {sel('source_type','NULL')},
                {sel('source_id','NULL')},
                {sel('duration','0')},
                {sel('updated_at','0')},
                {sel('updated_at_plex','0')},
                {sel('first_seen_at','0')},
                {sel('last_seen_at','0')},
                {sel('last_scan_at','0')},
                {sel('state',"'ACTIVE'")},
                {sel('error_count','0')},
                {sel('last_error_at','0')},
                {sel('last_error','NULL')},
                {sel('missing_since','0')},
                {sel('plex_path','NULL')},
                {sel('part_count','0')},
                {sel('streams_signature','NULL')},
                {sel('digest','NULL')}
            FROM media_files
        """
        cur.execute(select_sql)

        cur.execute("DROP TABLE media_files")
        cur.execute("ALTER TABLE media_files__new RENAME TO media_files")

        # Recreate indexes used by upserts
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_media_files_unique
            ON media_files(server_id, library_id, plex_rating_key)
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_media_files_state ON media_files(state)")

        conn.commit()

    def migrate_drop_legacy_unique_source(self):
        """
        Drop any UNIQUE index on (source_type, source_id) from media_files.
        Safe to run multiple times.
        """
        conn = getattr(self, "connection", None) or getattr(self, "conn", None)
        cur = conn.cursor()

        # enumerate indexes
        cur.execute("PRAGMA index_list(media_files)")
        idx_rows = cur.fetchall()  # seq, name, unique, origin, partial

        for _, idx_name, is_unique, *_ in idx_rows:
            # inspect index columns
            cur.execute(f"PRAGMA index_info({idx_name})")
            cols = [r[2] for r in cur.fetchall()]  # seqno, cid, name
            if is_unique and len(cols) == 2 and cols[0] == "source_type" and cols[1] == "source_id":
                cur.execute(f"DROP INDEX IF EXISTS {idx_name}")
                conn.commit()

        # ensure our intended unique/indexes exist
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_media_files_unique
            ON media_files(server_id, library_id, plex_rating_key)
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_media_files_state ON media_files(state)")
        conn.commit()

    def repair_source_id_for_episodes(self):
        """
        Repair existing rows' source_id for episodes to use episode ratingKey instead of show key.
        """
        conn = getattr(self, "connection", None) or getattr(self, "conn", None)
        cur = conn.cursor()
        # Set source_id to the item key we already store: plex_rating_key
        cur.execute("""
            UPDATE media_files
               SET source_id = plex_rating_key
             WHERE media_type='episode' AND source_type='plex'
               AND source_id IS NOT plex_rating_key
        """)
        conn.commit()

    def apply_retrovue_schema_upgrade_media_files(self):
        conn = self._conn(); cur = conn.cursor()
        cur.execute("PRAGMA table_info(media_files)")
        existing = {r[1] for r in cur.fetchall()}
        def add(name, ddl): 
            if name not in existing: cur.execute(f"ALTER TABLE media_files ADD COLUMN {name} {ddl}")
        add("server_id","INTEGER"); add("library_id","INTEGER"); add("plex_rating_key","TEXT")
        add("digest","TEXT"); add("updated_at_plex","BIGINT")
        add("first_seen_at","BIGINT"); add("last_seen_at","BIGINT"); add("last_scan_at","BIGINT")
        add("state","TEXT DEFAULT 'ACTIVE'"); add("error_count","INTEGER DEFAULT 0")
        add("last_error_at","BIGINT"); add("last_error","TEXT"); add("missing_since","BIGINT")
        add("plex_path","TEXT"); add("part_count","INTEGER DEFAULT 0"); add("streams_signature","TEXT")
        # don't add file_path here; rebuild handles its nullability
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_media_files_unique
            ON media_files(server_id, library_id, plex_rating_key)
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_media_files_state ON media_files(state)")
        conn.commit()
    
    # ============================================================================
    # Digest System Database Helpers
    # ============================================================================
    
    def show_digest_changed(self, server_id: int, library_id: int, show_key: str, lite_digest: str) -> bool:
        """Check if a show's digest has changed since last scan."""
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT show_digest FROM shows_tracking WHERE server_id=? AND library_id=? AND rating_key=?",
            (server_id, library_id, show_key)
        )
        row = cursor.fetchone()
        return (row is None) or (row[0] != lite_digest)
    
    def children_hydrated(self, server_id: int, library_id: int, show_key: str) -> bool:
        """Check if a show's children have been fully hydrated."""
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT children_hydrated FROM shows_tracking WHERE server_id=? AND library_id=? AND rating_key=?",
            (server_id, library_id, show_key)
        )
        row = cursor.fetchone()
        return bool(row and row[0])
    
    def upsert_show_digest(self, server_id: int, library_id: int, show_key: str, digest: str, *, children_hydrated: bool):
        """Update or insert a show's digest and hydration status."""
        self.connection.execute("""
            INSERT INTO shows_tracking(server_id, library_id, rating_key, show_digest, children_hydrated)
            VALUES(?,?,?,?,?)
            ON CONFLICT(server_id, library_id, rating_key) DO UPDATE SET
              show_digest=excluded.show_digest,
              children_hydrated=excluded.children_hydrated
        """, (server_id, library_id, show_key, digest, 1 if children_hydrated else 0))
        self.connection.commit()
    
    def upsert_episode(self, server_id: int, library_id: int, parent_show_key: str, 
                       ep: dict, media: dict, digest: str, now_epoch: int):
        """Update or insert an episode with digest information."""
        cursor = self.connection.cursor()
        try:
            # Extract episode information
            rating_key = ep.get('ratingKey', '')
            title = ep.get('title', '')
            season_number = int(ep.get('parentIndex', 0))
            episode_number = int(ep.get('index', 0))
            updated_at_plex = int(ep.get('updatedAt', 0))

            # Check if media_file exists for this episode (server+rating_key)
            cursor.execute("""
                SELECT id FROM media_files 
                WHERE server_id = ? AND plex_rating_key = ?
            """, (server_id, rating_key))
            existing = cursor.fetchone()

            if existing:
                # Update existing row
                cursor.execute("""
                    UPDATE media_files SET
                        digest = ?, updated_at_plex = ?, last_seen_at = ?, last_scan_at = ?,
                        state = 'ACTIVE', error_count = 0, last_error = NULL,
                        plex_path = ?, duration = ?
                    WHERE id = ?
                """, (digest, updated_at_plex, now_epoch, now_epoch, 
                      media.get('plex_path', ''), media.get('duration', 0), existing[0]))
                media_file_id = existing[0]
            else:
                # Insert new row
                cursor.execute("""
                    INSERT INTO media_files (
                        server_id, library_id, plex_rating_key, plex_path, duration,
                        media_type, source_type, digest, updated_at_plex,
                        first_seen_at, last_seen_at, last_scan_at, state
                    ) VALUES (?, ?, ?, ?, ?, 'episode', 'plex', ?, ?, ?, ?, ?, 'ACTIVE')
                """, (server_id, library_id, rating_key, media.get('plex_path', ''), 
                      media.get('duration', 0), digest, updated_at_plex, 
                      now_epoch, now_epoch, now_epoch))
                media_file_id = cursor.lastrowid

            # Ensure an episodes row exists/updates
            cursor.execute("""
                INSERT OR REPLACE INTO episodes (
                    media_file_id, show_id, episode_title, season_number, episode_number
                )
                VALUES (?, (SELECT id FROM shows WHERE plex_rating_key = ?), ?, ?, ?)
            """, (media_file_id, parent_show_key, title, season_number, episode_number))

            # self.connection.commit() # Removed for batching
        except Exception as e:
            logger.warning(f"⚠️ Error upserting episode: {e}")
            self.connection.rollback()
            raise
    
    def upsert_movie(self, *, server_id: int, library_id: int, mv: dict, media: dict,
                     digest: str, now_epoch: int) -> None:
        """Update or insert a movie with digest information."""
        pk = mv["ratingKey"]
        updated_at_plex = mv.get("updatedAt") or 0
        self.connection.execute("""
            INSERT INTO media_files(
                server_id, library_id, plex_rating_key, state, digest,
                updated_at_plex, first_seen_at, last_seen_at, last_scan_at,
                duration, media_type, source_type, source_id,
                plex_path, part_count, streams_signature
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(server_id, library_id, plex_rating_key) DO UPDATE SET
                state='ACTIVE',
                digest=excluded.digest,
                updated_at_plex=excluded.updated_at_plex,
                last_seen_at=excluded.last_seen_at,
                last_scan_at=excluded.last_scan_at,
                duration=excluded.duration,
                media_type=excluded.media_type,
                source_type=excluded.source_type,
                source_id=excluded.source_id,
                plex_path=excluded.plex_path,
                part_count=excluded.part_count,
                streams_signature=excluded.streams_signature
        """, (
            server_id, library_id, pk, 'ACTIVE', digest,
            updated_at_plex, now_epoch, now_epoch, now_epoch,
            media.get("duration_ms") or 0, 'movie', 'plex', pk,
            media.get("plex_path") or '', media.get("part_count") or 0, media.get("streams_signature") or ''
        ))
        self.connection.commit()
    
    def upsert_show_basic(self, *, server_id: int, library_id: int, show: dict) -> int:
        """
        Upsert minimal show metadata and return show_id.
        Keyed by (server_id, library_id, plex_rating_key).
        """
        rk = str(show.get("ratingKey") or "")
        title = show.get("title") or ""
        year = int(show.get("year") or 0)
        show_rating = show.get("contentRating") or ""
        show_summary = show.get("summary") or ""
        studio = show.get("studio") or ""
        originally_at = show.get("originallyAvailableAt")
        leaf_count = int(show.get("leafCount") or 0)
        child_count = int(show.get("childCount") or 0)

        cur = self.connection.cursor()
        cur.execute("""
            INSERT INTO shows (server_id, library_id, plex_rating_key, title, year,
                               show_rating, show_summary, studio, originally_available_at,
                               total_episodes, total_seasons, source_type, source_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, strftime('%s','now'))
            ON CONFLICT(server_id, library_id, plex_rating_key) DO UPDATE SET
                title=excluded.title,
                year=excluded.year,
                show_rating=excluded.show_rating,
                show_summary=excluded.show_summary,
                studio=excluded.studio,
                originally_available_at=excluded.originally_available_at,
                total_episodes=excluded.total_episodes,
                total_seasons=excluded.total_seasons,
                source_type=excluded.source_type,
                source_id=excluded.source_id,
                updated_at=strftime('%s','now')
        """, (server_id, library_id, rk, title, year, show_rating, show_summary, studio,
              originally_at, leaf_count, child_count, 'plex', rk))

        cur.execute("""
            SELECT id FROM shows
            WHERE server_id=? AND library_id=? AND plex_rating_key=?
        """, (server_id, library_id, rk))
        row = cur.fetchone()
        return int(row[0]) if row else 0

    def count_episodes_for_show_source_id(self, show_source_id: str) -> int:
        """
        Return count of episodes linked to the show whose shows.source_id == show_source_id (Plex show GUID).
        """
        cur = self.connection.cursor()
        cur.execute("""
            SELECT COUNT(*)
            FROM episodes e
            JOIN shows s ON e.show_id = s.id
            WHERE s.source_id = ?
        """, (show_source_id,))
        row = cur.fetchone()
        return int(row[0]) if row else 0

    def upsert_episode_metadata(self, *, show_id: int, ep: dict) -> None:
        """
        Upsert minimal per-episode metadata (not file info).
        Keyed by (show_id, plex_rating_key).
        """
        ep_rk = str(ep.get("ratingKey") or "")
        episode_title = ep.get("title") or ""
        season = int(ep.get("parentIndex") or 0)
        number = int(ep.get("index") or 0)
        summary = ep.get("summary") or ""
        rating = ep.get("contentRating") or ""
        updated_at = int(ep.get("updatedAt") or 0)

        self.connection.execute("""
            INSERT INTO episodes (show_id, plex_rating_key, episode_title, season_number, episode_number,
                                  summary, rating, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(show_id, plex_rating_key) DO UPDATE SET
                episode_title=excluded.episode_title,
                season_number=excluded.season_number,
                episode_number=excluded.episode_number,
                summary=excluded.summary,
                rating=excluded.rating,
                updated_at=excluded.updated_at
        """, (show_id, ep_rk, episode_title, season, number, summary, rating, updated_at))
    
    def mark_missing_not_seen(self, library_id: int, seen: set[str], now_epoch: int) -> int:
        """Mark items as missing if they weren't seen in this scan."""
        if not seen:
            seen = {"__none__"}  # avoid empty IN ()
        q = f"""
            UPDATE media_files
               SET state='MISSING', missing_since=COALESCE(missing_since, ?)
             WHERE library_id=? AND state <> 'DELETED' AND plex_rating_key NOT IN ({','.join('?'*len(seen))})
        """
        cursor = self.connection.cursor()
        cursor.execute(q, (now_epoch, library_id, *list(seen)))
        self.connection.commit()
        return cursor.rowcount or 0
    
    def promote_deleted_past_retention(self, library_id: int, now_epoch: int, retention_days: int) -> int:
        """Promote missing items to deleted if they've been missing past retention period."""
        cutoff = now_epoch - retention_days*86400
        cursor = self.connection.cursor()
        cursor.execute("""
            UPDATE media_files
               SET state='DELETED'
             WHERE library_id=? AND state='MISSING' AND COALESCE(missing_since, 0) <= ?
        """, (library_id, cutoff))
        self.connection.commit()
        return cursor.rowcount or 0
    
    def get_library_by_key(self, library_key: str, server_id: int) -> Optional[Dict]:
        """Get library information by key and server ID."""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT * FROM libraries 
                WHERE library_key = ? AND server_id = ?
            """, (library_key, server_id))
            result = cursor.fetchone()
            return dict(result) if result else None
        except Exception as e:
            logger.warning(f"⚠️ Error getting library by key: {e}")
            return None
    
    def add_library(self, server_id: int, library_key: str, library_name: str, library_type: str) -> int:
        """Add a new library to the database."""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO libraries (server_id, library_key, library_name, library_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (server_id, library_key, library_name, library_type, 
                  int(datetime.now().timestamp()), int(datetime.now().timestamp())))
            
            library_id = cursor.lastrowid
            self.connection.commit()
            return library_id
        except Exception as e:
            logger.warning(f"⚠️ Error adding library: {e}")
            self.connection.rollback()
            return 0
    
    def get_path_mappings(self, server_id: int) -> list[tuple[str, str]]:
        """Get all path mappings for a server as (plex_prefix, local_prefix) tuples."""
        cursor = self.connection.cursor()
        try:
            cursor.execute("SELECT plex_prefix, local_prefix FROM path_mappings WHERE server_id=? ORDER BY LENGTH(plex_prefix) DESC", (server_id,))
            rows = cursor.fetchall()
            return [(r[0], r[1]) for r in rows]
        except Exception:
            return []
    
    def add_path_mapping(self, server_id: int, plex_prefix: str, local_prefix: str) -> None:
        """Add a new path mapping."""
        self.connection.execute("INSERT INTO path_mappings(server_id, plex_prefix, local_prefix) VALUES(?,?,?)",
                      (server_id, plex_prefix, local_prefix))
        self.connection.commit()
    
    def remove_path_mapping(self, server_id: int, plex_prefix: str) -> None:
        """Remove a path mapping."""
        self.connection.execute("DELETE FROM path_mappings WHERE server_id=? AND plex_prefix=?",
                      (server_id, plex_prefix))
        self.connection.commit()
    
    def update_path_mapping(self, mapping_id: int, plex_prefix: str, local_prefix: str) -> bool:
        """Update a path mapping by ID."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE path_mappings 
                SET plex_prefix = ?, local_prefix = ?
                WHERE id = ?
            """, (plex_prefix, local_prefix, mapping_id))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception:
            return False
    
    def delete_path_mapping_by_id(self, mapping_id: int) -> bool:
        """Delete a path mapping by ID."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM path_mappings WHERE id = ?", (mapping_id,))
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception:
            return False
    
    def get_path_mappings_all(self) -> List[Dict]:
        """Get all path mappings with server names for UI display."""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT pm.id, pm.server_id, pm.plex_prefix, pm.local_prefix, ps.name as server_name
                FROM path_mappings pm
                LEFT JOIN plex_servers ps ON pm.server_id = ps.id
                ORDER BY ps.name, LENGTH(pm.plex_prefix) DESC
            """)
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'server_id': row[1], 
                    'plex_prefix': row[2],
                    'local_prefix': row[3],
                    'server_name': row[4] or f"Server {row[1]}"
                }
                for row in rows
            ]
        except Exception:
            return []
    
    def get_path_mappings_for_server(self, server_id: int) -> List[Dict]:
        """Get path mappings for a specific server."""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT id, server_id, plex_prefix, local_prefix
                FROM path_mappings 
                WHERE server_id = ?
                ORDER BY LENGTH(plex_prefix) DESC
            """, (server_id,))
            rows = cursor.fetchall()
            return [
                {
                    'id': row[0],
                    'server_id': row[1], 
                    'plex_prefix': row[2],
                    'local_prefix': row[3]
                }
                for row in rows
            ]
        except Exception:
            return []
    
    def library_missing_deleted_counts(self, library_id: int) -> tuple[int, int]:
        """Get counts of missing and deleted items for a library."""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN state='MISSING' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN state='DELETED' THEN 1 ELSE 0 END)
                FROM media_files WHERE library_id=?
            """, (library_id,))
            row = cursor.fetchone() or (0, 0)
            return (row[0] or 0, row[1] or 0)
        except Exception as e:
            logger.warning(f"⚠️ Error getting library counts: {e}")
            return (0, 0)
    
    def get_library_stats(self, library_id: int) -> Dict:
        """Get comprehensive statistics for a library."""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT
                    COUNT(*) as total_items,
                    SUM(CASE WHEN state='ACTIVE' THEN 1 ELSE 0 END) as active_items,
                    SUM(CASE WHEN state='REMOTE_ONLY' THEN 1 ELSE 0 END) as remote_only_items,
                    SUM(CASE WHEN state='UNAVAILABLE' THEN 1 ELSE 0 END) as unavailable_items,
                    SUM(CASE WHEN state='MISSING' THEN 1 ELSE 0 END) as missing_items,
                    SUM(CASE WHEN state='DELETED' THEN 1 ELSE 0 END) as deleted_items,
                    MAX(last_scan_at) as last_scan_at
                FROM media_files WHERE library_id=?
            """, (library_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'total_items': row[0] or 0,
                    'active_items': row[1] or 0,
                    'remote_only_items': row[2] or 0,
                    'unavailable_items': row[3] or 0,
                    'missing_items': row[4] or 0,
                    'deleted_items': row[5] or 0,
                    'last_scan_at': row[6]
                }
            return {
                'total_items': 0,
                'active_items': 0,
                'remote_only_items': 0,
                'unavailable_items': 0,
                'missing_items': 0,
                'deleted_items': 0,
                'last_scan_at': None
            }
        except Exception as e:
            logger.warning(f"⚠️ Error getting library stats: {e}")
            return {
                'total_items': 0,
                'active_items': 0,
                'remote_only_items': 0,
                'unavailable_items': 0,
                'missing_items': 0,
                'deleted_items': 0,
                'last_scan_at': None
            }
    
    def update_item_state(self, item_id: int, new_state: str, error_message: str = None) -> bool:
        """Update the state of a media item."""
        cursor = self.connection.cursor()
        try:
            now_epoch = int(datetime.now().timestamp())
            
            if new_state == 'ACTIVE':
                cursor.execute("""
                    UPDATE media_files 
                    SET state=?, last_seen_at=?, last_scan_at=?, error_count=0, last_error_at=NULL, last_error=NULL
                    WHERE id=?
                """, (new_state, now_epoch, now_epoch, item_id))
            elif new_state in ['REMOTE_ONLY', 'UNAVAILABLE']:
                cursor.execute("""
                    UPDATE media_files 
                    SET state=?, last_scan_at=?, error_count=error_count+1, last_error_at=?, last_error=?
                    WHERE id=?
                """, (new_state, now_epoch, now_epoch, error_message or '', item_id))
            else:
                cursor.execute("""
                    UPDATE media_files 
                    SET state=?, last_scan_at=?
                    WHERE id=?
                """, (new_state, now_epoch, item_id))
            
            self.connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logger.warning(f"⚠️ Error updating item state: {e}")
            self.connection.rollback()
            return False
    
    def get_items_by_state(self, library_id: int, state: str, limit: int = 100) -> List[Dict]:
        """Get items by state for a library."""
        cursor = self.connection.cursor()
        try:
            cursor.execute("""
                SELECT * FROM media_files 
                WHERE library_id=? AND state=?
                ORDER BY last_scan_at DESC
                LIMIT ?
            """, (library_id, state, limit))
            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            logger.warning(f"⚠️ Error getting items by state: {e}")
            return []
    
    def cleanup_old_deleted_items(self, library_id: int, days_old: int = 90) -> int:
        """Remove deleted items older than specified days."""
        cursor = self.connection.cursor()
        try:
            cutoff_epoch = int(datetime.now().timestamp()) - (days_old * 24 * 60 * 60)
            cursor.execute("""
                DELETE FROM media_files 
                WHERE library_id=? AND state='DELETED' AND last_scan_at < ?
            """, (library_id, cutoff_epoch))
            
            deleted_count = cursor.rowcount
            self.connection.commit()
            return deleted_count
        except Exception as e:
            logger.warning(f"⚠️ Error cleaning up deleted items: {e}")
            self.connection.rollback()
            return 0
    
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
    
    def update_library_sync_enabled(self, library_id: int, enabled: bool) -> None:
        """Update sync preference for a library by library_id"""
        cur = self.connection.cursor()
        cur.execute("UPDATE libraries SET sync_enabled = ? WHERE id = ?", (1 if enabled else 0, library_id))
        self.connection.commit()
    
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
    
    
    def get_libraries(self) -> List[str]:
        """Get all unique library names from the libraries table"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT DISTINCT library_name 
            FROM libraries 
            WHERE library_name IS NOT NULL AND library_name != ''
            ORDER BY library_name
        """)
        results = cursor.fetchall()
        return [row['library_name'] for row in results]
    
    def get_distinct_libraries_from_media(self) -> List[str]:
        """Get distinct library names from media_files table (for Browse tab dropdown)"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT DISTINCT library_name
            FROM media_files
            WHERE library_name IS NOT NULL AND library_name != ''
            ORDER BY library_name
        """)
        results = cursor.fetchall()
        return [row['library_name'] for row in results]
    
    def backfill_missing_library_data(self) -> Dict[str, int]:
        """Backfill missing library_name, server_id, and plex_path data in media_files"""
        cursor = self.connection.cursor()
        
        # Count rows that need backfilling
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM media_files
            WHERE library_name IS NULL OR library_name = '' OR server_id IS NULL OR plex_path IS NULL
        """)
        total_missing = cursor.fetchone()['count']
        
        if total_missing == 0:
            return {"updated": 0, "skipped": 0, "total": 0}
        
        # Try to backfill from libraries table
        cursor.execute("""
            UPDATE media_files
            SET library_name = (
                SELECT l.library_name
                FROM libraries l
                WHERE l.library_name IS NOT NULL
                LIMIT 1
            )
            WHERE (library_name IS NULL OR library_name = '') 
            AND EXISTS (SELECT 1 FROM libraries WHERE library_name IS NOT NULL)
        """)
        
        # Try to backfill server_id from plex_servers table
        cursor.execute("""
            UPDATE media_files
            SET server_id = (
                SELECT ps.id
                FROM plex_servers ps
                WHERE ps.is_active = 1
                LIMIT 1
            )
            WHERE server_id IS NULL
            AND EXISTS (SELECT 1 FROM plex_servers WHERE is_active = 1)
        """)
        
        # For plex_path, if it's missing but file_path exists, copy file_path to plex_path
        try:
            cursor.execute("""
                UPDATE media_files
                SET plex_path = file_path
                WHERE plex_path IS NULL AND file_path IS NOT NULL
            """)
        except Exception:
            # file_path column may not exist anymore, that's fine
            pass
        
        # Count how many were actually updated
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM media_files
            WHERE library_name IS NULL OR library_name = '' OR server_id IS NULL OR plex_path IS NULL
        """)
        still_missing = cursor.fetchone()['count']
        
        updated_count = total_missing - still_missing
        
        return {
            "updated": updated_count,
            "skipped": still_missing,
            "total": total_missing
        }
    
    def fix_library_name_mapping(self) -> Dict[str, int]:
        """Fix incorrect library name mappings in media_files table"""
        cursor = self.connection.cursor()
        
        # Define the correct library name mappings
        library_fixes = {
            "Adult content ": "Anime TV",  # Fix trailing space and wrong name
            "Adult content": "Anime TV",   # Fix wrong name without trailing space
        }
        
        total_fixed = 0
        
        for wrong_name, correct_name in library_fixes.items():
            # Check if the correct library exists in libraries table
            cursor.execute("""
                SELECT COUNT(*) FROM libraries 
                WHERE library_name = ?
            """, (correct_name,))
            
            if cursor.fetchone()[0] > 0:
                # Update the library names
                cursor.execute("""
                    UPDATE media_files 
                    SET library_name = ?
                    WHERE library_name = ?
                """, (correct_name, wrong_name))
                
                fixed_count = cursor.rowcount
                total_fixed += fixed_count
                
                if fixed_count > 0:
                    print(f"Fixed {fixed_count} items: '{wrong_name}' -> '{correct_name}'")
        
        # Also fix any NULL library names by assigning them to the most common library
        cursor.execute("""
            SELECT library_name, COUNT(*) as count 
            FROM media_files 
            WHERE library_name IS NOT NULL AND library_name != ''
            GROUP BY library_name 
            ORDER BY count DESC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if result:
            most_common_library = result[0]
            cursor.execute("""
                UPDATE media_files 
                SET library_name = ?
                WHERE library_name IS NULL OR library_name = ''
            """, (most_common_library,))
            
            null_fixed = cursor.rowcount
            total_fixed += null_fixed
            
            if null_fixed > 0:
                print(f"Fixed {null_fixed} NULL library names to '{most_common_library}'")
        
        return {
            "fixed": total_fixed,
            "mappings_applied": len(library_fixes)
        }
    
    def cleanup_orphaned_media_files(self) -> Dict[str, int]:
        """Remove media files that reference non-existent servers"""
        cursor = self.connection.cursor()
        
        # Count orphaned media files
        cursor.execute("""
            SELECT COUNT(*) FROM media_files mf
            WHERE mf.server_id IS NOT NULL 
            AND NOT EXISTS (
                SELECT 1 FROM plex_servers ps 
                WHERE ps.id = mf.server_id
            )
        """)
        orphaned_count = cursor.fetchone()[0]
        
        if orphaned_count == 0:
            return {"removed": 0, "total": 0}
        
        # Get details of what will be removed
        cursor.execute("""
            SELECT mf.id, mf.media_type, mf.source_id, mf.server_id
            FROM media_files mf
            WHERE mf.server_id IS NOT NULL 
            AND NOT EXISTS (
                SELECT 1 FROM plex_servers ps 
                WHERE ps.id = mf.server_id
            )
            LIMIT 10
        """)
        sample_orphaned = cursor.fetchall()
        
        # Remove orphaned media files and related data
        # First, remove episodes that reference orphaned media files
        cursor.execute("""
            DELETE FROM episodes 
            WHERE media_file_id IN (
                SELECT mf.id FROM media_files mf
                WHERE mf.server_id IS NOT NULL 
                AND NOT EXISTS (
                    SELECT 1 FROM plex_servers ps 
                    WHERE ps.id = mf.server_id
                )
            )
        """)
        episodes_removed = cursor.rowcount
        
        # Remove movies that reference orphaned media files
        cursor.execute("""
            DELETE FROM movies 
            WHERE media_file_id IN (
                SELECT mf.id FROM media_files mf
                WHERE mf.server_id IS NOT NULL 
                AND NOT EXISTS (
                    SELECT 1 FROM plex_servers ps 
                    WHERE ps.id = mf.server_id
                )
            )
        """)
        movies_removed = cursor.rowcount
        
        # Remove orphaned media files
        cursor.execute("""
            DELETE FROM media_files 
            WHERE server_id IS NOT NULL 
            AND NOT EXISTS (
                SELECT 1 FROM plex_servers ps 
                WHERE ps.id = server_id
            )
        """)
        media_files_removed = cursor.rowcount
        
        # Clean up orphaned shows (shows with no remaining episodes)
        cursor.execute("""
            DELETE FROM shows 
            WHERE id NOT IN (
                SELECT DISTINCT show_id FROM episodes 
                WHERE show_id IS NOT NULL
            )
        """)
        shows_removed = cursor.rowcount
        
        return {
            "removed": media_files_removed,
            "episodes_removed": episodes_removed,
            "movies_removed": movies_removed,
            "shows_removed": shows_removed,
            "total": orphaned_count,
            "sample": [dict(row) for row in sample_orphaned]
        }
    
    def fix_missing_episode_movie_records(self) -> Dict[str, int]:
        """Create missing episode and movie records from media_files"""
        cursor = self.connection.cursor()
        
        # Count missing records
        cursor.execute("""
            SELECT COUNT(*) FROM media_files mf
            WHERE mf.media_type = 'episode' 
            AND NOT EXISTS (SELECT 1 FROM episodes e WHERE e.media_file_id = mf.id)
        """)
        missing_episodes = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM media_files mf
            WHERE mf.media_type = 'movie' 
            AND NOT EXISTS (SELECT 1 FROM movies m WHERE m.media_file_id = mf.id)
        """)
        missing_movies = cursor.fetchone()[0]
        
        episodes_created = 0
        movies_created = 0
        
        if missing_episodes > 0:
            # Create episode records for media_files that don't have them
            # Link them to the first available show
            cursor.execute("SELECT id FROM shows LIMIT 1")
            first_show = cursor.fetchone()
            if first_show:
                show_id = first_show[0]
                cursor.execute("""
                    INSERT INTO episodes (media_file_id, show_id, episode_title, season_number, episode_number, rating, summary)
                    SELECT 
                        mf.id,
                        ? as show_id,
                        'Unknown Episode' as episode_title,
                        1 as season_number,
                        1 as episode_number,
                        '' as rating,
                        '' as summary
                    FROM media_files mf
                    WHERE mf.media_type = 'episode' 
                    AND NOT EXISTS (SELECT 1 FROM episodes e WHERE e.media_file_id = mf.id)
                """, (show_id,))
                episodes_created = cursor.rowcount
        
        if missing_movies > 0:
            # Create movie records for media_files that don't have them
            cursor.execute("""
                INSERT INTO movies (media_file_id, title, year, rating, summary, genre, director)
                SELECT 
                    mf.id,
                    'Unknown Movie' as title,
                    2024 as year,
                    '' as rating,
                    '' as summary,
                    '' as genre,
                    '' as director
                FROM media_files mf
                WHERE mf.media_type = 'movie' 
                AND NOT EXISTS (SELECT 1 FROM movies m WHERE m.media_file_id = mf.id)
            """)
            movies_created = cursor.rowcount
        
        return {
            "episodes_created": episodes_created,
            "movies_created": movies_created,
            "missing_episodes": missing_episodes,
            "missing_movies": missing_movies
        }
    
    def get_local_path_for_media_file(self, media_file_id: int) -> str:
        """Get the local mapped path for a media file (for file access)"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT mf.plex_path, mf.server_id
            FROM media_files mf
            WHERE mf.id = ?
        """, (media_file_id,))

        result = cursor.fetchone()
        if not result:
            return ""

        # Use plex_path column
        plex_path = result['plex_path']
        server_id = result['server_id']
        
        if not plex_path:
            return ""
        
        # Use the path mapping service as the single source of truth
        from .path_mapping import PlexPathMappingService
        path_mapping_service = PlexPathMappingService.create_from_database(self, server_id)
        return path_mapping_service.get_local_path(plex_path)
    
    def add_media_file(
        self,
        file_path: str,
        duration: int,
        media_type: str,
        source_type: str,
        source_id: str = None,
        library_name: str = None,
        server_id: int = None,
        plex_path: str = None
    ) -> int:
        """
        Upsert a media file; never REPLACE the row (preserve row id & FKs).
        - file_path can be NULL (we resolve dynamically)
        - plex_path is the path straight from Plex parts
        """
        cur = self.connection.cursor()

        # ensure unique index exists
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_media_files_source
            ON media_files(source_type, source_id)
        """)

        cur.execute("""
            INSERT INTO media_files (
                file_path, duration, media_type, source_type, source_id,
                library_name, server_id, updated_at, plex_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_type, source_id) DO UPDATE SET
                duration     = excluded.duration,
                media_type   = excluded.media_type,
                library_name = excluded.library_name,
                server_id    = excluded.server_id,
                updated_at   = excluded.updated_at,
                plex_path    = excluded.plex_path
        """, (
            None,                 # file_path (always resolve dynamically)
            duration or 0,
            media_type,
            source_type,
            source_id,
            library_name,
            server_id,
            int(datetime.now().timestamp()),
            plex_path
        ))

        # stable id fetch (id preserved across UPSERT)
        cur.execute("""
            SELECT id FROM media_files
            WHERE source_type = ? AND source_id = ?
        """, (source_type, source_id))
        row = cur.fetchone()
        media_file_id = row["id"]

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
        now_ts = plex_updated_at

        # Use UPSERT to update in place so row IDs never change
        cursor.execute("""
            INSERT INTO shows (plex_rating_key, title, year, total_seasons, total_episodes, show_rating,
                               show_summary, genre, studio, originally_available_at, guid_primary,
                               source_type, source_id, server_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                plex_rating_key = excluded.plex_rating_key,
                title = excluded.title,
                year = excluded.year,
                total_seasons = excluded.total_seasons,
                total_episodes = excluded.total_episodes,
                show_rating = excluded.show_rating,
                show_summary = excluded.show_summary,
                genre = excluded.genre,
                studio = excluded.studio,
                originally_available_at = excluded.originally_available_at,
                guid_primary = excluded.guid_primary,
                source_type = excluded.source_type,
                server_id = excluded.server_id,
                updated_at = excluded.updated_at
            WHERE shows.id = shows.id
            RETURNING id
        """, (plex_rating_key, title, year, total_seasons, total_episodes, show_rating,
              show_summary, genre, studio, originally_available_at, guid_primary,
              source_type, source_id, server_id, now_ts))
        
        row = cursor.fetchone()
        if not row:
            cursor.execute("SELECT id FROM shows WHERE source_id = ?", (source_id,))
            row = cursor.fetchone()
        
        self.connection.commit()
        return row["id"]
    
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
    
    def get_episodes_with_show_info(
        self,
        library_name: str | None = None,
        show_title: str | None = None,
        limit: int = 500,
        offset: int = 0
    ) -> list[dict]:
        """
        Return episode rows joined with show + media_files, ordered nicely.
        """
        cur = self.connection.cursor()

        base_sql = """
            SELECT
                e.id                  AS episode_id,
                e.episode_title       AS episode_title,
                e.season_number       AS season_number,
                e.episode_number      AS episode_number,
                e.plex_rating_key     AS episode_rating_key,
                s.id                  AS show_id,
                s.title               AS show_title,
                s.plex_rating_key     AS show_rating_key,
                mf.id                 AS media_file_id,
                mf.duration           AS duration_ms,
                mf.library_name       AS library_name
            FROM episodes e
            JOIN shows s
              ON s.id = e.show_id
            JOIN media_files mf
              ON mf.id = e.media_file_id
            WHERE 1=1
        """

        params = []
        if library_name:
            base_sql += " AND mf.library_name = ?"
            params.append(library_name)

        if show_title:
            base_sql += " AND s.title = ?"
            params.append(show_title)

        base_sql += """
            ORDER BY
                s.title COLLATE NOCASE ASC,
                e.season_number ASC,
                e.episode_number ASC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        cur.execute(base_sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        return rows
    
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
            SELECT m.*, mf.source_id, mf.id as media_file_id, mf.library_name, mf.duration
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
            SELECT e.*, mf.source_id, mf.id as media_file_id, mf.duration
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
            SELECT m.*, mf.source_id, mf.id as media_file_id, mf.duration, mf.library_name
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
            SELECT e.*, mf.source_id, mf.id as media_file_id, mf.duration, mf.library_name
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
    
    def update_media_file(self, media_file_id: int, duration: int, library_name: str = None, plex_path: str = None) -> bool:
        """Update a media file"""
        try:
            cursor = self.connection.cursor()
            current_timestamp = int(datetime.now().timestamp())
            if library_name is not None and plex_path is not None:
                cursor.execute("""
                    UPDATE media_files 
                    SET duration = ?, library_name = ?, plex_path = ?, updated_at = ?
                    WHERE id = ?
                """, (duration, library_name, plex_path, current_timestamp, media_file_id))
            elif library_name is not None:
                cursor.execute("""
                    UPDATE media_files 
                    SET duration = ?, library_name = ?, updated_at = ?
                    WHERE id = ?
                """, (duration, library_name, current_timestamp, media_file_id))
            elif plex_path is not None:
                cursor.execute("""
                    UPDATE media_files 
                    SET duration = ?, plex_path = ?, updated_at = ?
                    WHERE id = ?
                """, (duration, plex_path, current_timestamp, media_file_id))
            else:
                cursor.execute("""
                    UPDATE media_files 
                    SET duration = ?, updated_at = ?
                    WHERE id = ?
                """, (duration, current_timestamp, media_file_id))
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
    
    def get_library_by_id(self, library_id: int) -> Optional[Dict]:
        """Get a library by its ID"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM libraries WHERE id = ?
            """, (library_id,))
            result = cursor.fetchone()
            if result:
                return dict(result)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to get library by ID {library_id}: {e}")
            return None
    
    def get_all_libraries(self) -> List[Dict]:
        """Get all libraries from all servers"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM libraries ORDER BY server_id, library_name
            """)
            results = cursor.fetchall()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"❌ Failed to get all libraries: {e}")
            return []
    
    def get_server_libraries(self, server_id: int) -> list[dict]:
        """Get all libraries for a specific server with sync_enabled status"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT id, server_id, library_key, library_name, library_type, 
                       COALESCE(sync_enabled, 1) AS sync_enabled
                FROM libraries
                WHERE server_id = ?
                ORDER BY library_name
            """, (server_id,))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ Failed to get server libraries: {e}")
            return []

    def set_library_selected(self, server_id: int, section_key: str, enabled: bool) -> None:
        """Set the sync_enabled status for a library"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE libraries
                SET sync_enabled = ?
                WHERE server_id = ? AND library_key = ?
            """, (1 if enabled else 0, server_id, str(section_key)))
            self.connection.commit()
        except Exception as e:
            logger.error(f"❌ Failed to set library selected: {e}")
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
