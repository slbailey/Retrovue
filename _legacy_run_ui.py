#!/usr/bin/env python3
"""
Retrovue UI Launcher

This is the main entry point for the Retrovue management UI application.
It launches the PySide6-based desktop interface for managing content libraries,
browsing imported media, and performing sync operations with Plex Media Server.

The UI provides:
- Content library management and browsing
- Plex Media Server integration and sync
- Real-time progress tracking for import operations
- Database management and content organization

Usage:
    python run_ui.py

The application will start the desktop UI where you can:
1. Configure Plex server connection
2. Import/sync content from Plex libraries
3. Browse and organize your media library
4. View content with proper duration formatting
"""

import sys
from pathlib import Path

# Add src directory to Python path so we can import retrovue modules
src_path = str(Path(__file__).parent / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Add venv site-packages to Python path to ensure dependencies are found
venv_site_packages = str(Path(__file__).parent / 'venv' / 'Lib' / 'site-packages')
if venv_site_packages not in sys.path:
    sys.path.insert(0, venv_site_packages)

from retrovue.ui.main_window import main

if __name__ == "__main__":
    main()
