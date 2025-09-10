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
    QGroupBox, QGridLayout, QMessageBox, QFileDialog, QDialog,
    QDialogButtonBox, QMenuBar, QMenu
)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont, QAction

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
    
    library_progress = Signal(int, int, str)  # current, total, library_name
    item_progress = Signal(int, int, str)     # current, total, item_name
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
            
            # Dual progress callback - handle library and item progress separately
            def progress_callback(library_progress=None, item_progress=None, message=None):
                if message:
                    self.status.emit(message)
                
                # Handle library progress
                if library_progress:
                    lib_current, lib_total, lib_name = library_progress
                    if lib_total > 0:
                        lib_progress = int((lib_current / lib_total) * 100)
                        self.library_progress.emit(lib_progress, 100, lib_name)
                
                # Handle item progress
                if item_progress:
                    item_current, item_total, item_name = item_progress
                    if item_total > 0:
                        item_progress_percent = int((item_current / item_total) * 100)
                        # The item_name now already includes the episode number format from plex_integration
                        self.item_progress.emit(item_progress_percent, 100, item_name)
            
            # Use the new sync_all_libraries method with progress callback
            result = importer.sync_all_libraries(progress_callback)
            
            # Update progress to 100%
            self.library_progress.emit(100, 100, "Complete")
            self.item_progress.emit(100, 100, "Complete")
            
            self.status.emit(f"🎉 Sync completed! {result['updated']} updated, {result['added']} added, {result['removed']} removed")
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(f"Sync failed: {str(e)}")
        finally:
            # Close database connection
            if self.database:
                self.database.close()


class PlexSettingsDialog(QDialog):
    """Modal dialog for Plex settings configuration"""
    
    def __init__(self, database: RetrovueDatabase, parent=None):
        super().__init__(parent)
        self.database = database
        self.setWindowTitle("Plex Settings")
        self.setModal(True)
        self.setFixedSize(500, 400)
        self._setup_ui()
        self._load_stored_credentials()
    
    def _setup_ui(self):
        """Set up the UI for Plex settings"""
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
        connection_layout.addWidget(self.test_btn, 2, 0, 1, 2)
        
        connection_group.setLayout(connection_layout)
        layout.addWidget(connection_group)
        
        # Path Mapping Group
        path_group = QGroupBox("Path Mapping")
        path_layout = QGridLayout()
        
        # Plex Path
        path_layout.addWidget(QLabel("Plex Path:"), 0, 0)
        self.plex_path_input = QLineEdit()
        self.plex_path_input.setPlaceholderText("/media")
        path_layout.addWidget(self.plex_path_input, 0, 1)
        
        # Local Path
        path_layout.addWidget(QLabel("Local Path:"), 1, 0)
        self.local_path_input = QLineEdit()
        self.local_path_input.setPlaceholderText("R:\\media")
        path_layout.addWidget(self.local_path_input, 1, 1)
        
        # Path mapping info
        path_info = QLabel("Map Plex server paths to local paths. Example: /media → R:\\media")
        path_info.setWordWrap(True)
        path_info.setStyleSheet("color: #666; font-size: 11px;")
        path_layout.addWidget(path_info, 2, 0, 1, 2)
        
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)
        
        # Status Text
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        # Dialog buttons with Apply button
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        button_box.accepted.connect(self._ok_clicked)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_clicked)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def _load_stored_credentials(self):
        """Load stored Plex credentials from database"""
        creds = self.database.get_plex_credentials()
        if creds:
            self.server_url_input.setText(creds['server_url'])
            self.token_input.setText(creds['token'])
            self.status_text.append("🔐 Loaded stored Plex credentials")
        
        # Load path mappings
        path_mappings = self.database.get_plex_path_mappings()
        if path_mappings:
            # For now, just use the first mapping (we can extend this later)
            mapping = path_mappings[0]
            self.plex_path_input.setText(mapping['plex_path'])
            self.local_path_input.setText(mapping['local_path'])
            self.status_text.append("🗺️ Loaded path mappings")
    
    def _test_connection(self):
        """Test connection to Plex server"""
        server_url = self.server_url_input.text().strip()
        token = self.token_input.text().strip()
        
        if not server_url or not token:
            self.status_text.append("⚠️ Please enter both server URL and token")
            return
        
        self.status_text.append("🔄 Testing connection...")
        
        try:
            importer = create_plex_importer(server_url, token, self.database)
            if importer:
                libraries = importer.get_libraries()
                self.status_text.append(f"✅ Connection successful! Found {len(libraries)} libraries on {server_url}")
            else:
                self.status_text.append(f"❌ Connection failed to {server_url}")
        except Exception as e:
            self.status_text.append(f"❌ Connection error: {str(e)}")
    
    def _validate_settings(self):
        """Validate all settings and return list of missing fields"""
        missing_fields = []
        
        server_url = self.server_url_input.text().strip()
        token = self.token_input.text().strip()
        plex_path = self.plex_path_input.text().strip()
        local_path = self.local_path_input.text().strip()
        
        if not server_url:
            missing_fields.append("Server URL")
        
        if not token:
            missing_fields.append("Token")
        
        if not plex_path:
            missing_fields.append("Plex Path")
        
        if not local_path:
            missing_fields.append("Local Path")
        
        return missing_fields
    
    def _show_validation_error(self, missing_fields):
        """Show modal dialog for missing required fields"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Missing Required Fields")
        msg.setText("The following required fields are missing:\n\n" + "\n".join(f"• {field}" for field in missing_fields))
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()
    
    def _save_settings(self):
        """Save Plex settings to database with validation"""
        missing_fields = self._validate_settings()
        
        if missing_fields:
            self._show_validation_error(missing_fields)
            return False
        
        server_url = self.server_url_input.text().strip()
        token = self.token_input.text().strip()
        plex_path = self.plex_path_input.text().strip()
        local_path = self.local_path_input.text().strip()
        
        try:
            # Store credentials in database
            self.database.store_plex_credentials(server_url, token)
            
            # Store path mappings
            self.database.store_plex_path_mapping(plex_path, local_path)
            
            self.status_text.append("💾 Settings and path mappings saved successfully")
            return True
        except Exception as e:
            self.status_text.append(f"❌ Save error: {str(e)}")
            return False
    
    def _apply_clicked(self):
        """Handle Apply button click - save settings but don't close dialog"""
        self._save_settings()
    
    def _ok_clicked(self):
        """Handle OK button click - save settings and close dialog"""
        if self._save_settings():
            self.accept()
    
    def get_credentials(self):
        """Get the current credentials from the dialog"""
        return {
            'server_url': self.server_url_input.text().strip(),
            'token': self.token_input.text().strip()
        }


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
        
        # Sync Controls Group
        sync_group = QGroupBox("Content Sync")
        sync_layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel("Configure Plex settings in the Settings menu, then use the sync button below to import content.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic;")
        sync_layout.addWidget(info_label)
        
        # Sync Button
        self.import_btn = QPushButton("Sync All Libraries")
        self.import_btn.clicked.connect(self._start_import)
        self.import_btn.setMinimumHeight(40)
        sync_layout.addWidget(self.import_btn)
        
        sync_group.setLayout(sync_layout)
        layout.addWidget(sync_group)
        
        # Progress Group
        progress_group = QGroupBox("Import Progress")
        progress_layout = QVBoxLayout()
        
        # Library Progress
        self.library_progress_label = QLabel("Library Progress")
        self.library_progress_label.setVisible(False)
        progress_layout.addWidget(self.library_progress_label)
        
        self.library_progress_bar = QProgressBar()
        self.library_progress_bar.setVisible(False)
        progress_layout.addWidget(self.library_progress_bar)
        
        # Item Progress
        self.item_progress_label = QLabel("Item Progress")
        self.item_progress_label.setVisible(False)
        progress_layout.addWidget(self.item_progress_label)
        
        self.item_progress_bar = QProgressBar()
        self.item_progress_bar.setVisible(False)
        progress_layout.addWidget(self.item_progress_bar)
        
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
            self.status_text.append("🔐 Plex credentials found in database")
        else:
            self.status_text.append("⚠️ No Plex credentials found. Please configure in Settings menu.")
    
    def _start_import(self):
        """Start the import process"""
        # Get credentials from database
        creds = self.database.get_plex_credentials()
        if not creds:
            QMessageBox.warning(
                self, "No Plex Settings", 
                "Please configure Plex settings in the Settings menu before syncing."
            )
            return
        
        server_url = creds['server_url']
        token = creds['token']
        
        # Disable button during import
        self.import_btn.setEnabled(False)
        
        # Show progress bars and labels
        self.library_progress_label.setVisible(True)
        self.library_progress_bar.setVisible(True)
        self.library_progress_bar.setValue(0)
        self.item_progress_label.setVisible(True)
        self.item_progress_bar.setVisible(True)
        self.item_progress_bar.setValue(0)
        
        # Clear status text
        self.status_text.clear()
        
        # Start import worker
        self.import_worker = ImportWorker('retrovue.db', server_url, token)
        self.import_worker.library_progress.connect(self._update_library_progress)
        self.import_worker.item_progress.connect(self._update_item_progress)
        self.import_worker.status.connect(self._update_status)
        self.import_worker.finished.connect(self._import_finished)
        self.import_worker.error.connect(self._import_error)
        self.import_worker.start()
    
    def _update_library_progress(self, current: int, total: int, library_name: str):
        """Update library progress bar and label"""
        self.library_progress_bar.setValue(current)
        self.library_progress_label.setText(f"Library Progress: {library_name} ({current}%)")
    
    def _update_item_progress(self, current: int, total: int, item_name: str):
        """Update item progress bar and label"""
        self.item_progress_bar.setValue(current)
        self.item_progress_label.setText(f"Item Progress: {item_name}")
    
    def _update_status(self, message: str):
        """Update status text"""
        self.status_text.append(message)
    
    def _import_finished(self):
        """Handle import completion"""
        self.import_btn.setEnabled(True)
        
        # Hide progress bars and labels
        self.library_progress_label.setVisible(False)
        self.library_progress_bar.setVisible(False)
        self.item_progress_label.setVisible(False)
        self.item_progress_bar.setVisible(False)
        
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
        self.import_btn.setEnabled(True)
        
        # Hide progress bars and labels
        self.library_progress_label.setVisible(False)
        self.library_progress_bar.setVisible(False)
        self.item_progress_label.setVisible(False)
        self.item_progress_bar.setVisible(False)
        
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
        
        # Library Filter
        filter_layout.addWidget(QLabel("Library:"))
        self.library_combo = QComboBox()
        self.library_combo.addItem("All Libraries")
        self.library_combo.currentTextChanged.connect(self._filter_content)
        filter_layout.addWidget(self.library_combo)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Content Table
        self.content_table = QTableWidget()
        self.content_table.setColumnCount(8)
        self.content_table.setHorizontalHeaderLabels([
            "Title", "Type", "Duration", "Rating", "Show", "Season/Episode", "Library", "Media Path"
        ])
        
        # Enable context menu for the table
        self.content_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.content_table.customContextMenuRequested.connect(self._show_context_menu)
        
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
        
        # Load libraries
        libraries = self.database.get_libraries()
        self.library_combo.clear()
        self.library_combo.addItem("All Libraries")
        for library in libraries:
            self.library_combo.addItem(library)
        
        # Load content
        self._filter_content()
    
    def _filter_content(self):
        """Filter content based on selected criteria"""
        media_type = self.media_type_combo.currentText()
        show_title = self.show_combo.currentText()
        library_name = self.library_combo.currentText()
        
        # Clear table
        self.content_table.setRowCount(0)
        
        # Load content based on filters
        if media_type == "All" or media_type == "episode":
            episodes = self.database.get_episodes_with_show_info()
            for episode in episodes:
                if show_title != "All Shows" and episode['show_title'] != show_title:
                    continue
                if library_name != "All Libraries" and episode.get('library_name', '') != library_name:
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
                self.content_table.setItem(row, 6, QTableWidgetItem(episode.get('library_name', '')))
                self.content_table.setItem(row, 7, QTableWidgetItem(episode.get('file_path', '')))
        
        if media_type == "All" or media_type == "movie":
            movies = self.database.get_movies_with_metadata()
            for movie in movies:
                if library_name != "All Libraries" and movie.get('library_name', '') != library_name:
                    continue
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
                self.content_table.setItem(row, 6, QTableWidgetItem(movie.get('library_name', '')))
                self.content_table.setItem(row, 7, QTableWidgetItem(movie.get('file_path', '')))
        
        # Resize columns to content
        self.content_table.resizeColumnsToContents()
    
    def _show_context_menu(self, position):
        """Show context menu for table items"""
        item = self.content_table.itemAt(position)
        if item is None:
            return
        
        row = item.row()
        media_path_item = self.content_table.item(row, 7)  # Media Path column
        if media_path_item is None:
            return
        
        media_path = media_path_item.text()
        if not media_path:
            return
        
        # Create context menu
        menu = QMenu(self)
        
        # Copy path action
        copy_action = QAction("Copy Media Path", self)
        copy_action.triggered.connect(lambda: self._copy_to_clipboard(media_path))
        menu.addAction(copy_action)
        
        # Copy local path action (if path mapping is configured)
        try:
            local_path = self.database.get_local_path_for_media_file(
                self.content_table.item(row, 0).data(Qt.ItemDataRole.UserRole)  # We'll need to store media_file_id
            )
            if local_path != media_path:
                copy_local_action = QAction("Copy Local Path", self)
                copy_local_action.triggered.connect(lambda: self._copy_to_clipboard(local_path))
                menu.addAction(copy_local_action)
        except:
            pass  # Ignore if we can't get local path
        
        # Show in Explorer action
        show_action = QAction("Show in Explorer", self)
        show_action.triggered.connect(lambda: self._show_in_explorer(media_path))
        menu.addAction(show_action)
        
        # Show menu
        menu.exec(self.content_table.mapToGlobal(position))
    
    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
    
    def _show_in_explorer(self, file_path: str):
        """Show file in Windows Explorer"""
        import os
        import subprocess
        
        # Convert to local path if path mapping is configured
        try:
            # For now, just use the path as-is
            # In the future, we could use the path mapping service here
            local_path = file_path
            
            # Get the directory containing the file
            directory = os.path.dirname(local_path)
            
            # Open in Windows Explorer
            subprocess.run(['explorer', '/select,', local_path], check=False)
        except Exception as e:
            print(f"Error opening in Explorer: {e}")


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
        
        # Create menu bar
        self._create_menu_bar()
        
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
    
    def _create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # Settings menu
        settings_menu = menubar.addMenu('Settings')
        
        # Plex Settings action
        plex_settings_action = QAction('Plex Settings', self)
        plex_settings_action.triggered.connect(self._open_plex_settings)
        settings_menu.addAction(plex_settings_action)
    
    def _open_plex_settings(self):
        """Open the Plex settings dialog"""
        dialog = PlexSettingsDialog(self.database, self)
        dialog.exec()
        
        # Refresh the import tab to show updated credentials status
        self.import_tab._load_stored_credentials()
    
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
