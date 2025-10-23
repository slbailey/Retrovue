#!/usr/bin/env python3
"""
Simple script to run the Retrovue admin interface.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

if __name__ == "__main__":
    try:
        import uvicorn
        from retrovue.api.main import app
        
        print("Starting Retrovue Admin Interface...")
        print("Server will be available at: http://localhost:8000")
        print("Press Ctrl+C to stop the server")
        print()
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError as e:
        print(f"Error: {e}")
        print("\nPlease make sure you have activated your virtual environment:")
        print("  .\\venv\\Scripts\\activate")
        print("\nAnd installed the required packages:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

