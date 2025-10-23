#!/usr/bin/env python3
"""
Simple script to start the Retrovue admin interface.
This script ensures the virtual environment is activated and dependencies are installed.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, shell=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("Starting Retrovue Admin Interface...")
    print()
    
    # Add the src directory to the Python path
    src_dir = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_dir))
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Warning: Virtual environment not detected!")
        print("   Please run: .\\venv\\Scripts\\activate")
        print("   Then run this script again.")
        return
    
    print("Virtual environment detected")
    
    # Check if required packages are installed
    print("Checking dependencies...")
    success, stdout, stderr = run_command("python -c \"import fastapi, uvicorn, jinja2, structlog, sqlalchemy\"")
    
    if not success:
        print("Installing missing dependencies...")
        success, stdout, stderr = run_command("pip install -r requirements.txt")
        if not success:
            print(f"Failed to install dependencies: {stderr}")
            return
        print("Dependencies installed")
    else:
        print("All dependencies found")
    
    print()
    print("Starting server at http://localhost:8000")
    print("   Press Ctrl+C to stop the server")
    print()
    
    # Start the server
    try:
        import uvicorn
        from retrovue.api.main import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"Error starting server: {e}")
        return

if __name__ == "__main__":
    main()
