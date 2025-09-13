"""
Retrovue UI Module

This module contains the user interface components for the Retrovue IPTV management system.
It provides a comprehensive PySide6-based desktop application for managing content libraries,
configuring Plex integration, and administering the Retrovue system.

UI Components:

1. Main Window (RetrovueMainWindow):
   - Tabbed interface with multiple functional areas
   - Content library management and browsing
   - Plex server configuration and sync operations
   - Database management and statistics
   - Real-time progress tracking and status updates

2. Key Features:
   - Multi-threaded operations for responsive UI
   - Real-time progress bars and status messages
   - Content browser with filtering and search
   - Plex integration with connection testing
   - Database management and content organization

3. Architecture:
   - PySide6-based desktop application
   - QThread-based background processing
   - Signal/slot communication for real-time updates
   - Modular design for easy extension

Usage:
    from retrovue.ui import RetrovueMainWindow, main
    
    # Launch the main application
    main()
    
    # Or create the main window directly
    app = QApplication(sys.argv)
    window = RetrovueMainWindow()
    window.show()
    sys.exit(app.exec())

The UI provides an intuitive interface for managing the Retrovue system,
making it easy to import content, browse libraries, and configure settings
without needing to interact with the command line or configuration files.
"""

from .main_window import RetrovueMainWindow, main

__all__ = [
    "RetrovueMainWindow",
    "main"
]
