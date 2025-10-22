"""
Database operations for content sources.
"""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime


class ContentSourcesDB:
    """Database operations for content sources."""
    
    def __init__(self, db_path: str = "./retrovue.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database with content_sources table."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create content_sources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS content_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    config TEXT NOT NULL,  -- JSON string
                    status TEXT DEFAULT 'inactive',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def add_content_source(self, name: str, source_type: str, config: Dict[str, Any]) -> int:
        """Add a new content source."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO content_sources (name, source_type, config, status)
                VALUES (?, ?, ?, 'active')
            """, (name, source_type, json.dumps(config)))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_content_sources(self) -> List[Dict[str, Any]]:
        """Get all content sources."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, source_type, config, status, created_at, updated_at
                FROM content_sources
                ORDER BY created_at DESC
            """)
            
            sources = []
            for row in cursor.fetchall():
                sources.append({
                    'id': row[0],
                    'name': row[1],
                    'source_type': row[2],
                    'config': json.loads(row[3]),
                    'status': row[4],
                    'created_at': row[5],
                    'updated_at': row[6]
                })
            
            return sources
    
    def get_content_source(self, source_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific content source by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, source_type, config, status, created_at, updated_at
                FROM content_sources
                WHERE id = ?
            """, (source_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'source_type': row[2],
                    'config': json.loads(row[3]),
                    'status': row[4],
                    'created_at': row[5],
                    'updated_at': row[6]
                }
            
            return None
    
    def update_content_source(self, source_id: int, name: str, config: Dict[str, Any]) -> bool:
        """Update a content source."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE content_sources
                SET name = ?, config = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (name, json.dumps(config), source_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_content_source(self, source_id: int) -> bool:
        """Delete a content source."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM content_sources
                WHERE id = ?
            """, (source_id,))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def update_content_source_status(self, source_id: int, status: str) -> bool:
        """Update content source status."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE content_sources
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, source_id))
            
            conn.commit()
            return cursor.rowcount > 0
