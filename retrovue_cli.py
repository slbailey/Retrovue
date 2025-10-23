#!/usr/bin/env python3
"""
Retrovue CLI entry point.

This script provides the main entry point for the Retrovue CLI,
avoiding module import conflicts.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Import and run the CLI
from retrovue.cli.main import app

if __name__ == "__main__":
    app()