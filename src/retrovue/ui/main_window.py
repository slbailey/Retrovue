"""
Retrovue Main Window v2

This is the main PySide6-based desktop application for managing the Retrovue IPTV system.
It provides a comprehensive user interface for content management, Plex integration,
and system administration.

Key Features:
- Content Library Management: Browse and organize imported media
- Plex Integration: Connect to Plex Media Server and sync content
- Real-time Progress Tracking: Visual progress bars and status updates
- Database Management: View and manage the content database
- Multi-threaded Operations: Background processing for import/sync operations

UI Components:
- Main Window: Tabbed interface with multiple functional areas
- Import Tab: Plex server configuration and content import/sync
- Browse Tab: Content library browser with filtering and search
- Database Tab: Database management and statistics
- Progress Tracking: Real-time progress bars and status messages

Architecture:
- MainWindow: Main application window with tabbed interface
- ImportWorker: QThread-based worker for background import operations
- Progress Callbacks: Real-time progress updates from import operations
- Database Integration: Direct database access for content browsing

Threading:
- Import operations run in background threads to keep UI responsive
- Progress callbacks provide real-time updates to the UI
- Error handling ensures robust operation during long-running tasks

Usage:
    python run_ui.py  # Launches the desktop application

The application provides a complete management interface for the Retrovue system,
allowing users to import content, browse libraries, and manage the database
through an intuitive desktop interface.
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, 
    QProgressBar, QTableWidget, QTableWidgetItem, QComboBox,
    QGroupBox, QGridLayout, QMessageBox, QFileDialog
)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from retrovue.core.database import RetrovueDatabase
from retrovue.core.plex_integration import create_plex_importer


def format_duration_milliseconds(duration_ms: int) -> str:
    """
    Format duration from milliseconds to hh:mm:ss.ff format
    
    Args:
        duration_ms: Duration in milliseconds
        
    Returns:
        Formatted duration string (hh:mm:ss.ff)
    """
    if not duration_ms:
        return "00:00:00.00"
    
    # Convert milliseconds to total seconds
    total_seconds = duration_ms / 1000.0
    
    # Calculate hours, minutes, seconds, and fractional seconds
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    fractional_seconds = int((total_seconds % 1) * 100)  # Get centiseconds
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{fractional_seconds:02d}"


class ImportWorker(QThread):
    """Worker thread for importing content from Plex"""
    
    progress = Signal(int, int)  # current, total
    status = Signal(str)
    finished = Signal()
    error = Signal(str)
    
    def __init__(self, db_path: str, server_url: str, token: str):
        super().__init__()
        self.db_path = db_path
        self.server_url = server_url
        self.token = token
        self.database = None
    
    def run(self):
        """Run the import process"""
        try:
            # Create a new database connection in this thread
            self.database = RetrovueDatabase(self.db_path)
            
            # Store credentials in database
            self.database.store_plex_credentials(self.server_url, self.token)
            self.status.emit("🔐 Credentials stored in database")
            
            # Create Plex importer with status callback
            importer = create_plex_importer(self.server_url, self.token, self.database, self.status.emit)
            if not importer:
                self.error.emit("Failed to connect to Plex server")
                return
            
            # Get libraries
            libraries = importer.get_libraries()
            if not libraries:
                self.error.emit("No libraries found on Plex server")
                return
            
            self.status.emit(f"📚 Found {len(libraries)} libraries")
            
            # Simple progress callback - just pass through the structured progress
            def progress_callback(current: int, total: int, message: str):
                if message:
                    self.status.emit(message)
                
                # Simple progress calculation: (current / total) * 100
                if total > 0:
                    progress = int((current / total) * 100)
                    self.progress.emit(progress, 100)
            
            # Use the new sync_all_libraries method with progress callback
            result = importer.sync_all_libraries(progress_callback)
            
            # Update progress to 100%
            self.progress.emit(100, 100)
            
            self.status.emit(f"🎉 Sync completed! {result['updated']} updated, {result['added']} added, {result['removed']} removed")
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(f"Sync failed: {str(e)}")
        finally:
            # Close database connection
            if self.database:
                self.database.close()


class ContentImportTab(QWidget):
    """Tab for importing content from Plex"""
    
    def __init__(self, database: RetrovueDatabase):
        super().__init__()
        self.database = database
        self.import_worker = None
        self._setup_ui()
        self._load_stored_credentials()
    
    def _setup_ui(self):
        """Set up the UI for content import"""
        layout = QVBoxLayout()
        
        # Plex Connection Group
        connection_group = QGroupBox("Plex Connection")
        connection_layout = QGridLayout()
        
        # Server URL
        connection_layout.addWidget(QLabel("Server URL:"), 0, 0)
        self.server_url_input = QLineEdit()
        self.server_url_input.setPlaceholderText("https://your-plex-server.com")
        connection_layout.addWidget(self.server_url_input, 0, 1)
        
        # Token
        connection_layout.addWidget(QLabel("Token:"), 1, 0)
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setPlaceholderText("Your Plex token")
        connection_layout.addWidget(self.token_input, 1, 1)
        
        # Test Connection Button
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self._test_connection)
        connection_layout.addWidget(self.test_btn, 2, 0)
        
        # Sync Button
        self.import_btn = QPushButton("Sync All Libraries")
        self.import_btn.clicked.connect(self._start_import)
        connection_layout.addWidget(self.import_btn, 2, 1)
        
        connection_group.setLayout(connection_layout)
        layout.addWidget(connection_group)
        
        # Progress Group
        progress_group = QGroupBox("Import Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(150)
        self.status_text.setReadOnly(True)
        progress_layout.addWidget(self.status_text)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        self.setLayout(layout)
    
    def _load_stored_credentials(self):
        """Load stored Plex credentials from database"""
        creds = self.database.get_plex_credentials()
        if creds:
            self.server_url_input.setText(creds['server_url'])
            self.token_input.setText(creds['token'])
            self.status_text.append("🔐 Loaded stored Plex credentials")
    
    def _test_connection(self):
        """Test connection to Plex server"""
        server_url = self.server_url_input.text().strip()
        token = self.token_input.text().strip()
        
        if not server_url or not token:
            QMessageBox.warning(self, "Missing Information", "Please enter both server URL and token")
            return
        
        try:
            importer = create_plex_importer(server_url, token, self.database)
            if importer:
                libraries = importer.get_libraries()
                QMessageBox.information(
                    self, "Connection Successful", 
                    f"Connected to Plex server!\nFound {len(libraries)} libraries."
                )
                self.status_text.append(f"✅ Connected to Plex server: {server_url}")
            else:
                QMessageBox.critical(self, "Connection Failed", "Failed to connect to Plex server")
                self.status_text.append(f"❌ Failed to connect to Plex server: {server_url}")
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Error: {str(e)}")
            self.status_text.append(f"❌ Connection error: {str(e)}")
    
    def _start_import(self):
        """Start the import process"""
        server_url = self.server_url_input.text().strip()
        token = self.token_input.text().strip()
        
        if not server_url or not token:
            QMessageBox.warning(self, "Missing Information", "Please enter both server URL and token")
            return
        
        # Disable buttons during import
        self.test_btn.setEnabled(False)
        self.import_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Clear status text
        self.status_text.clear()
        
        # Start import worker
        self.import_worker = ImportWorker('retrovue.db', server_url, token)
        self.import_worker.progress.connect(self._update_progress)
        self.import_worker.status.connect(self._update_status)
        self.import_worker.finished.connect(self._import_finished)
        self.import_worker.error.connect(self._import_error)
        self.import_worker.start()
    
    def _update_progress(self, current: int, total: int):
        """Update progress bar"""
        self.progress_bar.setValue(current)
    
    def _update_status(self, message: str):
        """Update status text"""
        self.status_text.append(message)
    
    def _import_finished(self):
        """Handle import completion"""
        self.test_btn.setEnabled(True)
        self.import_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_text.append("🎉 Import completed successfully!")
        
        # Emit signal to refresh content browser
        # Find the main window by traversing up the parent chain
        widget = self
        while widget and not hasattr(widget, 'refresh_content_browser'):
            widget = widget.parent()
        
        if widget and hasattr(widget, 'refresh_content_browser'):
            widget.refresh_content_browser()
    
    def _import_error(self, error_message: str):
        """Handle import error"""
        self.test_btn.setEnabled(True)
        self.import_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_text.append(f"❌ Import failed: {error_message}")
        QMessageBox.critical(self, "Import Error", error_message)


class ContentBrowserTab(QWidget):
    """Tab for browsing imported content"""
    
    def __init__(self, database: RetrovueDatabase):
        super().__init__()
        self.database = database
        self._setup_ui()
        self._load_content()
    
    def _setup_ui(self):
        """Set up the UI for content browsing"""
        layout = QVBoxLayout()
        
        # Filter Group
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout()
        
        # Media Type Filter
        filter_layout.addWidget(QLabel("Media Type:"))
        self.media_type_combo = QComboBox()
        self.media_type_combo.addItem("All")
        self.media_type_combo.currentTextChanged.connect(self._filter_content)
        filter_layout.addWidget(self.media_type_combo)
        
        # Show Filter (for episodes)
        filter_layout.addWidget(QLabel("Show:"))
        self.show_combo = QComboBox()
        self.show_combo.addItem("All Shows")
        self.show_combo.currentTextChanged.connect(self._filter_content)
        filter_layout.addWidget(self.show_combo)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Content Table
        self.content_table = QTableWidget()
        self.content_table.setColumnCount(6)
        self.content_table.setHorizontalHeaderLabels([
            "Title", "Type", "Duration", "Rating", "Show", "Season/Episode"
        ])
        layout.addWidget(self.content_table)
        
        self.setLayout(layout)
    
    def _load_content(self):
        """Load content from database"""
        # Load media types
        media_types = self.database.get_media_types()
        self.media_type_combo.clear()
        self.media_type_combo.addItem("All")
        self.media_type_combo.addItems(media_types)
        
        # Load shows
        shows = self.database.get_shows()
        self.show_combo.clear()
        self.show_combo.addItem("All Shows")
        for show in shows:
            self.show_combo.addItem(show['title'])
        
        # Load content
        self._filter_content()
    
    def _filter_content(self):
        """Filter content based on selected criteria"""
        media_type = self.media_type_combo.currentText()
        show_title = self.show_combo.currentText()
        
        # Clear table
        self.content_table.setRowCount(0)
        
        # Load content based on filters
        if media_type == "All" or media_type == "episode":
            episodes = self.database.get_episodes_with_show_info()
            for episode in episodes:
                if show_title != "All Shows" and episode['show_title'] != show_title:
                    continue
                
                row = self.content_table.rowCount()
                self.content_table.insertRow(row)
                
                # Format duration (stored in milliseconds)
                duration = episode['duration']
                duration_str = format_duration_milliseconds(duration)
                
                # Season/Episode
                season = episode.get('season_number', '')
                episode_num = episode.get('episode_number', '')
                season_episode = f"S{season:02d}E{episode_num:02d}" if season and episode_num else ""
                
                self.content_table.setItem(row, 0, QTableWidgetItem(episode['episode_title']))
                self.content_table.setItem(row, 1, QTableWidgetItem("Episode"))
                self.content_table.setItem(row, 2, QTableWidgetItem(duration_str))
                self.content_table.setItem(row, 3, QTableWidgetItem(episode.get('rating', '')))
                self.content_table.setItem(row, 4, QTableWidgetItem(episode['show_title']))
                self.content_table.setItem(row, 5, QTableWidgetItem(season_episode))
        
        if media_type == "All" or media_type == "movie":
            movies = self.database.get_movies_with_metadata()
            for movie in movies:
                row = self.content_table.rowCount()
                self.content_table.insertRow(row)
                
                # Format duration (stored in milliseconds)
                duration = movie['duration']
                duration_str = format_duration_milliseconds(duration)
                
                self.content_table.setItem(row, 0, QTableWidgetItem(movie['title']))
                self.content_table.setItem(row, 1, QTableWidgetItem("Movie"))
                self.content_table.setItem(row, 2, QTableWidgetItem(duration_str))
                self.content_table.setItem(row, 3, QTableWidgetItem(movie.get('rating', '')))
                self.content_table.setItem(row, 4, QTableWidgetItem(""))
                self.content_table.setItem(row, 5, QTableWidgetItem(""))
        
        # Resize columns to content
        self.content_table.resizeColumnsToContents()


class RetrovueMainWindow(QMainWindow):
    """Main window for Retrovue application"""
    
    def __init__(self):
        super().__init__()
        self.database = RetrovueDatabase('retrovue.db')
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the main window UI"""
        self.setWindowTitle("Retrovue - IPTV Management System v2")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget with tabs
        central_widget = QTabWidget()
        self.setCentralWidget(central_widget)
        
        # Add tabs
        self.import_tab = ContentImportTab(self.database)
        self.browser_tab = ContentBrowserTab(self.database)
        central_widget.addTab(self.import_tab, "Import Content")
        central_widget.addTab(self.browser_tab, "Browse Content")
        
        # Set font
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)
    
    def refresh_content_browser(self):
        """Refresh the content browser tab"""
        self.browser_tab._load_content()
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.database:
            self.database.close()
        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Retrovue")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Retrovue")
    
    # Create and show main window
    window = RetrovueMainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
