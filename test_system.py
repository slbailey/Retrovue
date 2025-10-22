#!/usr/bin/env python3
"""
Test the Retrovue system components.
"""

import sys
from pathlib import Path

# Add src and cli to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "cli"))

def test_system():
    """Test all system components."""
    print("=== RETROVUE SYSTEM TEST ===")
    print()
    
    try:
        # Test database
        from retrovue.plex.db import Db
        db = Db("retrovue.db")
        print("[OK] Database connection successful")
        
        # Test path mapping
        from retrovue.plex.pathmap import PathMapper
        path_mapper = PathMapper(db.conn)
        print("[OK] Path mapping system ready")
        
        # Test validation
        from retrovue.plex.validation import ContentValidator
        validator = ContentValidator(path_mapper)
        print("[OK] Content validation system ready")
        
        # Test error handling
        from retrovue.plex.error_handling import ErrorHandler
        error_handler = ErrorHandler()
        print("[OK] Error handling system ready")
        
        # Check content
        servers = db.list_plex_servers()
        libraries = db.list_libraries()
        print(f"[INFO] Found {len(servers)} Plex servers")
        print(f"[INFO] Found {len(libraries)} libraries")
        
        print()
        print("[SUCCESS] All systems operational!")
        print()
        print("=== WHAT YOU CAN DO NOW ===")
        print("1. Add a Plex server:")
        print("   .\\venv\\Scripts\\python.exe cli/plex_sync.py servers add --name 'My Plex' --base-url 'http://server:32400' --token 'token'")
        print()
        print("2. List servers:")
        print("   .\\venv\\Scripts\\python.exe cli/plex_sync.py servers list")
        print()
        print("3. Sync content:")
        print("   .\\venv\\Scripts\\python.exe cli/plex_sync.py ingest run")
        print()
        print("4. Run GUI:")
        print("   .\\venv\\Scripts\\python.exe simple_gui.py")
        
    except Exception as e:
        print(f"[ERROR] System test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_system()

