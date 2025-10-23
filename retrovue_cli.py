#!/usr/bin/env python3
"""
Retrovue CLI entry point.

This script provides easy access to the Retrovue CLI commands.
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from retrovue.cli.main import cli

if __name__ == "__main__":
    cli()
