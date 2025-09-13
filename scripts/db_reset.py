#!/usr/bin/env python3
"""
Retrovue Database Reset Script (Python)
Cross-platform version of db_reset.sh
Nukes old DB and applies fresh v1.1 schema
"""

import os
import sys
import sqlite3
import argparse
from pathlib import Path
from typing import Optional


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color


def print_status(message: str) -> None:
    """Print status message in green"""
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {message}")


def print_warning(message: str) -> None:
    """Print warning message in yellow"""
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {message}")


def print_error(message: str) -> None:
    """Print error message in red"""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")


def check_production_path(path: str) -> bool:
    """Check if path looks like a production path"""
    production_indicators = ['/var/', '/opt/', '/usr/', '/home/', 'production']
    return any(indicator in path.lower() for indicator in production_indicators)


def ensure_parent_directory(db_path: str) -> None:
    """Ensure parent directory exists"""
    parent_dir = Path(db_path).parent
    if not parent_dir.exists():
        print_status(f"Creating database directory: {parent_dir}")
        parent_dir.mkdir(parents=True, exist_ok=True)


def remove_existing_database(db_path: str) -> None:
    """Remove existing database if it exists"""
    if os.path.exists(db_path):
        print_status(f"Removing existing database: {db_path}")
        os.remove(db_path)


def apply_schema(db_path: str, schema_path: str) -> bool:
    """Apply schema to database"""
    try:
        print_status(f"Applying schema from: {schema_path}")
        print_status(f"Creating database at: {db_path}")
        
        # Read schema file
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Create database and apply schema
        conn = sqlite3.connect(db_path)
        conn.executescript(schema_sql)
        conn.close()
        
        return True
    except Exception as e:
        print_error(f"Failed to apply schema: {e}")
        return False


def verify_database(db_path: str) -> bool:
    """Verify database was created successfully"""
    if not os.path.exists(db_path):
        print_error("Database file was not created!")
        return False
    
    try:
        # Get file size
        file_size = os.path.getsize(db_path)
        print_status(f"Database file size: {file_size} bytes")
        
        # Get table count
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
        table_count = cursor.fetchone()[0]
        conn.close()
        
        print_status(f"Tables created: {table_count}")
        return True
    except Exception as e:
        print_error(f"Failed to verify database: {e}")
        return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Retrovue Database Reset Script')
    parser.add_argument('--db-path', default='data/retrovue.db',
                       help='Database file path (default: data/retrovue.db)')
    parser.add_argument('--schema', default='sql/retrovue_schema_v1.2.sql',
                       help='Schema file path (default: sql/retrovue_schema_v1.2.sql)')
    parser.add_argument('--force', action='store_true',
                       help='Skip production path warning')
    
    args = parser.parse_args()
    
    print_status("Retrovue Database Reset Script")
    print_status("==============================")
    
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    db_path = args.db_path
    schema_path = args.schema
    
    # Check if schema file exists
    if not os.path.exists(schema_path):
        print_error(f"Schema file not found: {schema_path}")
        print_error("Please ensure the schema file exists in the project root")
        sys.exit(1)
    
    # Check if path looks like production
    if not args.force and check_production_path(db_path):
        print_warning(f"WARNING: Database path '{db_path}' looks like a production path!")
        print_warning("This script will DELETE the existing database and recreate it.")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print_status("Operation cancelled by user")
            sys.exit(0)
    
    # Ensure parent directory exists
    ensure_parent_directory(db_path)
    
    # Remove existing database
    remove_existing_database(db_path)
    
    # Apply schema
    if not apply_schema(db_path, schema_path):
        sys.exit(1)
    
    # Verify database
    if not verify_database(db_path):
        sys.exit(1)
    
    print_status("Database reset completed successfully!")


if __name__ == '__main__':
    main()