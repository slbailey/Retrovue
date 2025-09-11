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
    QDialogButtonBox, QMenuBar, QMenu, QCheckBox
)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont, QAction

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from retrovue.core.database import RetrovueDatabase
from retrovue.core.plex_integration import create_plex_importer, create_plex_importer_legacy


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
    
    def __init__(self, db_path: str, server_id: int = None, server_url: str = None, token: str = None):
        super().__init__()
        self.db_path = db_path
        self.server_id = server_id
        self.server_url = server_url
        self.token = token
        self.database = None
    
    def run(self):
        """Run the import process"""
        try:
            # Create a new database connection in this thread
            self.database = RetrovueDatabase(self.db_path)
            
            # Create Plex importer with status callback
            if self.server_id is not None:
                # Use new multi-server system
                importer = create_plex_importer(self.server_id, self.database, self.status.emit)
            else:
                # Use legacy system for backward compatibility
                self.database.store_plex_credentials(self.server_url, self.token)
                self.status.emit("🔐 Credentials stored in database")
                importer = create_plex_importer_legacy(self.server_url, self.token, self.database, self.status.emit)
            
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


class PlexServersDialog(QDialog):
    """Modal dialog for managing multiple Plex servers and path mappings"""
    
    def __init__(self, database: RetrovueDatabase, parent=None):
        super().__init__(parent)
        self.database = database
        self.setWindowTitle("Plex Servers & Path Mappings")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self._setup_ui()
        self._load_servers()
        self._load_path_mappings()
    
    def _setup_ui(self):
        """Set up the UI for multi-server management"""
        layout = QVBoxLayout()
        
        # Create tab widget for servers and path mappings
        tab_widget = QTabWidget()
        
        # Servers Tab
        servers_tab = QWidget()
        servers_layout = QVBoxLayout()
        
        # Server Management Group
        server_group = QGroupBox("Plex Servers")
        server_layout = QVBoxLayout()
        
        # Server List
        self.servers_table = QTableWidget()
        self.servers_table.setColumnCount(4)
        self.servers_table.setHorizontalHeaderLabels(["Name", "Server URL", "Status", "Actions"])
        self.servers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        server_layout.addWidget(self.servers_table)
        
        # Server Controls
        server_controls = QHBoxLayout()
        self.add_server_btn = QPushButton("Add Server")
        self.add_server_btn.clicked.connect(self._add_server)
        self.edit_server_btn = QPushButton("Edit Server")
        self.edit_server_btn.clicked.connect(self._edit_server)
        self.delete_server_btn = QPushButton("Delete Server")
        self.delete_server_btn.clicked.connect(self._delete_server)
        self.test_server_btn = QPushButton("Test Connection")
        self.test_server_btn.clicked.connect(self._test_server_connection)
        
        server_controls.addWidget(self.add_server_btn)
        server_controls.addWidget(self.edit_server_btn)
        server_controls.addWidget(self.delete_server_btn)
        server_controls.addWidget(self.test_server_btn)
        server_controls.addStretch()
        
        server_layout.addLayout(server_controls)
        server_group.setLayout(server_layout)
        servers_layout.addWidget(server_group)
        
        servers_tab.setLayout(servers_layout)
        tab_widget.addTab(servers_tab, "Servers")
        
        # Path Mappings Tab
        mappings_tab = QWidget()
        mappings_layout = QVBoxLayout()
        
        # Path Mapping Management Group
        mapping_group = QGroupBox("Path Mappings")
        mapping_layout = QVBoxLayout()
        
        # Path Mappings List
        self.mappings_table = QTableWidget()
        self.mappings_table.setColumnCount(6)
        self.mappings_table.setHorizontalHeaderLabels(["Server", "Library Name", "Library Root", "Plex Path", "Local Path", "Actions"])
        self.mappings_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        mapping_layout.addWidget(self.mappings_table)
        
        # Mapping Controls
        mapping_controls = QHBoxLayout()
        self.add_mapping_btn = QPushButton("Add Mapping")
        self.add_mapping_btn.clicked.connect(self._add_path_mapping)
        self.edit_mapping_btn = QPushButton("Edit Mapping")
        self.edit_mapping_btn.clicked.connect(self._edit_path_mapping)
        self.delete_mapping_btn = QPushButton("Delete Mapping")
        self.delete_mapping_btn.clicked.connect(self._delete_path_mapping)
        
        mapping_controls.addWidget(self.add_mapping_btn)
        mapping_controls.addWidget(self.edit_mapping_btn)
        mapping_controls.addWidget(self.delete_mapping_btn)
        mapping_controls.addStretch()
        
        mapping_layout.addLayout(mapping_controls)
        mapping_group.setLayout(mapping_layout)
        mappings_layout.addWidget(mapping_group)
        
        # Path Mapping Info
        mapping_info = QLabel("""
        <b>Per-Library Path Mapping:</b><br>
        • Most libraries use /media → D:\\Media mapping<br>
        • Special libraries (like Godzilla) can have custom mappings<br>
        • Library root paths are automatically detected from Plex<br>
        • Example: Godzilla library at /othermedia/godzilla → E:\\Godzilla Collection
        """)
        mapping_info.setWordWrap(True)
        mapping_info.setStyleSheet("color: #666; font-size: 11px; padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc;")
        mappings_layout.addWidget(mapping_info)
        
        mappings_tab.setLayout(mappings_layout)
        tab_widget.addTab(mappings_tab, "Path Mappings")
        
        layout.addWidget(tab_widget)
        
        # Status Text
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def _load_servers(self):
        """Load Plex servers from database"""
        servers = self.database.get_plex_servers()
        self.servers_table.setRowCount(len(servers))
        
        for i, server in enumerate(servers):
            self.servers_table.setItem(i, 0, QTableWidgetItem(server['name']))
            self.servers_table.setItem(i, 1, QTableWidgetItem(server['server_url']))
            status = "Active" if server['is_active'] else "Inactive"
            self.servers_table.setItem(i, 2, QTableWidgetItem(status))
            
            # Store server ID in the row for later use
            self.servers_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, server['id'])
        
        self.servers_table.resizeColumnsToContents()
        self.status_text.append(f"📡 Loaded {len(servers)} Plex servers")
    
    def _load_path_mappings(self):
        """Load path mappings from database"""
        mappings = self.database.get_plex_path_mappings()
        self.mappings_table.setRowCount(len(mappings))
        
        for i, mapping in enumerate(mappings):
            # Get server name
            server = self.database.get_plex_server(mapping['server_id'])
            server_name = server['name'] if server else f"Server {mapping['server_id']}"
            
            self.mappings_table.setItem(i, 0, QTableWidgetItem(server_name))
            self.mappings_table.setItem(i, 1, QTableWidgetItem(mapping.get('library_name', '')))
            self.mappings_table.setItem(i, 2, QTableWidgetItem(mapping.get('library_root', '')))
            self.mappings_table.setItem(i, 3, QTableWidgetItem(mapping['plex_path']))
            self.mappings_table.setItem(i, 4, QTableWidgetItem(mapping['local_path']))
            
            # Store mapping ID in the row for later use
            self.mappings_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, mapping['id'])
        
        self.mappings_table.resizeColumnsToContents()
        self.status_text.append(f"🗺️ Loaded {len(mappings)} path mappings")
    
    def _add_server(self):
        """Add a new Plex server"""
        dialog = ServerEditDialog(self.database, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_servers()
    
    def _edit_server(self):
        """Edit selected Plex server"""
        current_row = self.servers_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a server to edit.")
            return
        
        server_id = self.servers_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = ServerEditDialog(self.database, server_id=server_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_servers()
    
    def _delete_server(self):
        """Delete selected Plex server"""
        current_row = self.servers_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a server to delete.")
            return
        
        server_id = self.servers_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        server_name = self.servers_table.item(current_row, 0).text()
        
        reply = QMessageBox.question(
            self, "Delete Server", 
            f"Are you sure you want to delete server '{server_name}'?\n\nThis will also delete all associated path mappings.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.database.delete_plex_server(server_id):
                self.status_text.append(f"🗑️ Deleted server '{server_name}'")
                self._load_servers()
                self._load_path_mappings()  # Refresh mappings in case any were deleted
            else:
                QMessageBox.critical(self, "Delete Error", "Failed to delete server.")
    
    def _test_server_connection(self):
        """Test connection to selected Plex server"""
        current_row = self.servers_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a server to test.")
            return
        
        server_id = self.servers_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        server_name = self.servers_table.item(current_row, 0).text()
        
        self.status_text.append(f"🔄 Testing connection to '{server_name}'...")
        
        try:
            importer = create_plex_importer(server_id, self.database)
            if importer:
                libraries = importer.get_libraries()
                self.status_text.append(f"✅ Connection successful! Found {len(libraries)} libraries on '{server_name}'")
            else:
                self.status_text.append(f"❌ Connection failed to '{server_name}'")
        except Exception as e:
            self.status_text.append(f"❌ Connection error: {str(e)}")
    
    def _add_path_mapping(self):
        """Add a new path mapping"""
        dialog = PathMappingEditDialog(self.database, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_path_mappings()
    
    def _edit_path_mapping(self):
        """Edit selected path mapping"""
        current_row = self.mappings_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a path mapping to edit.")
            return
        
        mapping_id = self.mappings_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        dialog = PathMappingEditDialog(self.database, mapping_id=mapping_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_path_mappings()
    
    def _delete_path_mapping(self):
        """Delete selected path mapping"""
        current_row = self.mappings_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a path mapping to delete.")
            return
        
        mapping_id = self.mappings_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
        plex_path = self.mappings_table.item(current_row, 3).text()
        
        reply = QMessageBox.question(
            self, "Delete Path Mapping", 
            f"Are you sure you want to delete the path mapping for '{plex_path}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.database.delete_plex_path_mapping(mapping_id):
                self.status_text.append(f"🗑️ Deleted path mapping for '{plex_path}'")
                self._load_path_mappings()
            else:
                QMessageBox.critical(self, "Delete Error", "Failed to delete path mapping.")


class ServerEditDialog(QDialog):
    """Dialog for adding/editing Plex servers"""
    
    def __init__(self, database: RetrovueDatabase, server_id: int = None, parent=None):
        super().__init__(parent)
        self.database = database
        self.server_id = server_id
        self.setWindowTitle("Edit Plex Server" if server_id else "Add Plex Server")
        self.setModal(True)
        self.setFixedSize(400, 300)
        self._setup_ui()
        self._load_server_data()
    
    def _setup_ui(self):
        """Set up the UI for server editing"""
        layout = QVBoxLayout()
        
        # Server Information Group
        server_group = QGroupBox("Server Information")
        server_layout = QGridLayout()
        
        # Server Name
        server_layout.addWidget(QLabel("Server Name:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("My Plex Server")
        server_layout.addWidget(self.name_input, 0, 1)
        
        # Server URL
        server_layout.addWidget(QLabel("Server URL:"), 1, 0)
        self.server_url_input = QLineEdit()
        self.server_url_input.setPlaceholderText("https://your-plex-server.com")
        server_layout.addWidget(self.server_url_input, 1, 1)
        
        # Token
        server_layout.addWidget(QLabel("Token:"), 2, 0)
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setPlaceholderText("Your Plex token")
        server_layout.addWidget(self.token_input, 2, 1)
        
        # Active Status
        self.active_checkbox = QCheckBox("Active")
        self.active_checkbox.setChecked(True)
        server_layout.addWidget(self.active_checkbox, 3, 0, 1, 2)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # Test Connection Button
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self._test_connection)
        layout.addWidget(self.test_btn)
        
        # Status Text
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(80)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._ok_clicked)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def _load_server_data(self):
        """Load server data for editing"""
        if self.server_id:
            server = self.database.get_plex_server(self.server_id)
            if server:
                self.name_input.setText(server['name'])
                self.server_url_input.setText(server['server_url'])
                self.token_input.setText(server['token'])
                self.active_checkbox.setChecked(server['is_active'])
                self.status_text.append("📡 Loaded server data for editing")
    
    def _test_connection(self):
        """Test connection to Plex server"""
        server_url = self.server_url_input.text().strip()
        token = self.token_input.text().strip()
        
        if not server_url or not token:
            self.status_text.append("⚠️ Please enter both server URL and token")
            return
        
        self.status_text.append("🔄 Testing connection...")
        
        try:
            # Test connection without creating any database records
            import requests
            
            # Test basic connectivity to Plex server
            test_url = f"{server_url}/status/sessions"
            headers = {'X-Plex-Token': token}
            response = requests.get(test_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Test library access
                libraries_url = f"{server_url}/library/sections"
                lib_response = requests.get(libraries_url, headers=headers, timeout=10)
                
                if lib_response.status_code == 200:
                    # Parse XML to count libraries
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(lib_response.text)
                    libraries = root.findall('.//Directory')
                    self.status_text.append(f"✅ Connection successful! Found {len(libraries)} libraries")
                else:
                    self.status_text.append(f"✅ Connection successful! (Library access: HTTP {lib_response.status_code})")
            else:
                self.status_text.append(f"❌ Connection failed: HTTP {response.status_code}")
            
        except Exception as e:
            self.status_text.append(f"❌ Connection error: {str(e)}")
    
    def _ok_clicked(self):
        """Handle OK button click - save server and close dialog"""
        name = self.name_input.text().strip()
        server_url = self.server_url_input.text().strip()
        token = self.token_input.text().strip()
        is_active = self.active_checkbox.isChecked()
        
        if not name or not server_url or not token:
            QMessageBox.warning(self, "Missing Fields", "Please fill in all required fields.")
            return
        
        try:
            if self.server_id:
                # Update existing server
                success = self.database.update_plex_server(
                    server_id=self.server_id, 
                    name=name, 
                    server_url=server_url, 
                    token=token, 
                    is_active=is_active
                )
                if success:
                    self.status_text.append("💾 Server updated successfully")
                    self.accept()
                else:
                    self.status_text.append("❌ Failed to update server")
            else:
                # Add new server
                server_id = self.database.add_plex_server(name, server_url, token, is_active)
                if server_id:
                    self.status_text.append(f"💾 Server added successfully (ID: {server_id})")
                    self.accept()
                else:
                    self.status_text.append("❌ Failed to add server")
                    
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save server: {str(e)}")


class PathMappingEditDialog(QDialog):
    """Dialog for adding/editing path mappings"""
    
    def __init__(self, database: RetrovueDatabase, mapping_id: int = None, server_id: int = None, parent=None):
        super().__init__(parent)
        self.database = database
        self.mapping_id = mapping_id
        self.server_id = server_id
        self.setWindowTitle("Edit Path Mapping" if mapping_id else "Add Path Mapping")
        self.setModal(True)
        self.setFixedSize(500, 400)
        self._setup_ui()
        self._load_mapping_data()
    
    def _setup_ui(self):
        """Set up the UI for path mapping editing"""
        layout = QVBoxLayout()
        
        # Path Mapping Information Group
        mapping_group = QGroupBox("Path Mapping Information")
        mapping_layout = QGridLayout()
        
        # If server_id is provided, show server name (read-only)
        if self.server_id:
            server = self.database.get_plex_server(self.server_id)
            server_name = server['name'] if server else 'Unknown Server'
            mapping_layout.addWidget(QLabel("Server:"), 0, 0)
            server_label = QLabel(server_name)
            server_label.setStyleSheet("font-weight: bold; color: #0078d4;")
            mapping_layout.addWidget(server_label, 0, 1)
            row = 1
        else:
            # Server Selection (only if no server_id provided)
            mapping_layout.addWidget(QLabel("Server:"), 0, 0)
            self.server_combo = QComboBox()
            mapping_layout.addWidget(self.server_combo, 0, 1)
            row = 1
        
        # Plex Path
        mapping_layout.addWidget(QLabel("Plex Path:"), row, 0)
        self.plex_path_input = QLineEdit()
        self.plex_path_input.setPlaceholderText("/media/movies")
        mapping_layout.addWidget(self.plex_path_input, row, 1)
        
        # Local Path
        mapping_layout.addWidget(QLabel("Local Path:"), row + 1, 0)
        self.local_path_input = QLineEdit()
        self.local_path_input.setPlaceholderText("D:\\Movies")
        mapping_layout.addWidget(self.local_path_input, row + 1, 1)
        
        mapping_group.setLayout(mapping_layout)
        layout.addWidget(mapping_group)
        
        # Path Mapping Info
        mapping_info = QLabel("""
        <b>Path Mapping Guidelines:</b><br>
        • Plex Path: The path prefix from Plex (e.g., /media/movies)<br>
        • Local Path: Where the files are located locally (e.g., D:\\Movies)<br>
        • This will map all files starting with the Plex Path to the Local Path
        """)
        mapping_info.setWordWrap(True)
        mapping_info.setStyleSheet("color: #666; font-size: 11px; padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc;")
        layout.addWidget(mapping_info)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._ok_clicked)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # Load servers only if no server_id provided
        if not self.server_id:
            self._load_servers()
    
    def _load_servers(self):
        """Load available servers"""
        servers = self.database.get_plex_servers()
        self.server_combo.clear()
        for server in servers:
            self.server_combo.addItem(server['name'], server['id'])
        
        # If server_id is specified, select it
        if self.server_id:
            for i in range(self.server_combo.count()):
                if self.server_combo.itemData(i) == self.server_id:
                    self.server_combo.setCurrentIndex(i)
                    break
    
    def _load_mapping_data(self):
        """Load mapping data for editing"""
        if self.mapping_id:
            mappings = self.database.get_plex_path_mappings()
            for mapping in mappings:
                if mapping['id'] == self.mapping_id:
                    # Set server (only if no server_id provided)
                    if not self.server_id and hasattr(self, 'server_combo'):
                        for i in range(self.server_combo.count()):
                            if self.server_combo.itemData(i) == mapping['server_id']:
                                self.server_combo.setCurrentIndex(i)
                                break
                    
                    # Load the path data
                    self.plex_path_input.setText(mapping['plex_path'])
                    self.local_path_input.setText(mapping['local_path'])
                    break
    
    def _ok_clicked(self):
        """Handle OK button click - save mapping and close dialog"""
        # Get server_id - either from parameter or combo box
        if self.server_id:
            server_id = self.server_id
        else:
            server_id = self.server_combo.currentData()
        
        plex_path = self.plex_path_input.text().strip()
        local_path = self.local_path_input.text().strip()
        
        if not server_id or not plex_path or not local_path:
            QMessageBox.warning(self, "Missing Fields", "Please fill in all required fields.")
            return
        
        try:
            if self.mapping_id:
                # Update existing mapping
                self.database.update_plex_path_mapping(
                    self.mapping_id, plex_path, local_path, server_id
                )
            else:
                # Add new mapping (simplified - no library info needed)
                self.database.add_plex_path_mapping(
                    plex_path, local_path, server_id
                )
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save path mapping: {str(e)}")


class PlexManagementTab(QWidget):
    """Main tab for managing Plex servers, libraries, and path mappings"""
    
    # Signal to notify when servers change
    servers_changed = Signal()
    
    def __init__(self, database: RetrovueDatabase):
        super().__init__()
        self.database = database
        self._setup_ui()
        self._load_servers()
    
    def _setup_ui(self):
        """Set up the UI for Plex management"""
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel("Plex Media Sources")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(header_label)
        
        # Server List Group
        server_group = QGroupBox("Plex Servers")
        server_layout = QVBoxLayout()
        
        # Server Table
        self.servers_table = QTableWidget()
        self.servers_table.setColumnCount(3)
        self.servers_table.setHorizontalHeaderLabels(["Name", "Address", "Actions"])
        self.servers_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.servers_table.setAlternatingRowColors(True)
        
        # Enable context menu for the table
        self.servers_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.servers_table.customContextMenuRequested.connect(self._show_server_context_menu)
        
        server_layout.addWidget(self.servers_table)
        
        # Server Controls
        server_controls = QHBoxLayout()
        self.add_server_btn = QPushButton("Add Plex Server")
        self.add_server_btn.clicked.connect(self._add_server)
        self.refresh_all_btn = QPushButton("Refresh All Libraries")
        self.refresh_all_btn.clicked.connect(self._refresh_all_libraries)
        self.sign_out_btn = QPushButton("Sign Out of Plex")
        self.sign_out_btn.clicked.connect(self._sign_out_plex)
        
        server_controls.addWidget(self.add_server_btn)
        server_controls.addWidget(self.refresh_all_btn)
        server_controls.addStretch()
        server_controls.addWidget(self.sign_out_btn)
        
        server_layout.addLayout(server_controls)
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # Status Text
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(120)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        self.setLayout(layout)
    
    def _load_servers(self):
        """Load Plex servers from database"""
        servers = self.database.get_plex_servers()
        self.servers_table.setRowCount(len(servers))
        
        for i, server in enumerate(servers):
            # Server name
            self.servers_table.setItem(i, 0, QTableWidgetItem(server['name']))
            
            # Server address
            self.servers_table.setItem(i, 1, QTableWidgetItem(server['server_url']))
            
            # Actions (create action buttons)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(5, 2, 5, 2)
            
            # Edit Server button
            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Edit Server")
            edit_btn.setFixedSize(30, 25)
            edit_btn.clicked.connect(lambda checked, srv_id=server['id']: self._edit_server(srv_id))
            actions_layout.addWidget(edit_btn)
            
            # Refresh Libraries button
            refresh_btn = QPushButton("🔄")
            refresh_btn.setToolTip("Refresh Libraries")
            refresh_btn.setFixedSize(30, 25)
            refresh_btn.clicked.connect(lambda checked, srv_id=server['id']: self._refresh_libraries(srv_id))
            actions_layout.addWidget(refresh_btn)
            
            # Manage Libraries button
            libraries_btn = QPushButton("📚")
            libraries_btn.setToolTip("Manage Libraries")
            libraries_btn.setFixedSize(30, 25)
            libraries_btn.clicked.connect(lambda checked, srv_id=server['id']: self._manage_libraries(srv_id))
            actions_layout.addWidget(libraries_btn)
            
            # Path Mappings button
            paths_btn = QPushButton("🗺️")
            paths_btn.setToolTip("Path Mappings")
            paths_btn.setFixedSize(30, 25)
            paths_btn.clicked.connect(lambda checked, srv_id=server['id']: self._manage_path_mappings(srv_id))
            actions_layout.addWidget(paths_btn)
            
            # Delete Server button
            delete_btn = QPushButton("🗑️")
            delete_btn.setToolTip("Delete Server")
            delete_btn.setFixedSize(30, 25)
            delete_btn.clicked.connect(lambda checked, srv_id=server['id']: self._delete_server(srv_id))
            actions_layout.addWidget(delete_btn)
            
            actions_widget.setLayout(actions_layout)
            self.servers_table.setCellWidget(i, 2, actions_widget)
            
            # Store server ID in the row for later use
            self.servers_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, server['id'])
        
        self.servers_table.resizeColumnsToContents()
        self.status_text.append(f"📡 Loaded {len(servers)} Plex servers")
    
    def _add_server(self):
        """Add a new Plex server"""
        dialog = ServerEditDialog(self.database, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_servers()
            self.status_text.append("✅ Added new Plex server")
            self.servers_changed.emit()  # Notify main window to refresh dropdown
    
    def _edit_server(self, server_id: int):
        """Edit an existing Plex server"""
        dialog = ServerEditDialog(self.database, server_id=server_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_servers()
            self.status_text.append("✅ Updated Plex server")
            self.servers_changed.emit()  # Notify main window to refresh dropdown
    
    def _delete_server(self, server_id: int):
        """Delete a Plex server"""
        server = self.database.get_plex_server(server_id)
        if not server:
            self.status_text.append("❌ Server not found")
            return
        
        reply = QMessageBox.question(
            self, "Delete Server", 
            f"Are you sure you want to delete server '{server['name']}'?\n\nThis will also delete all associated path mappings.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.database.delete_plex_server(server_id):
                self._load_servers()
                self.status_text.append(f"🗑️ Deleted server '{server['name']}'")
                self.servers_changed.emit()  # Notify main window to refresh dropdown
            else:
                QMessageBox.critical(self, "Delete Error", "Failed to delete server.")
    
    def _refresh_libraries(self, server_id: int):
        """Refresh libraries for a specific server"""
        server = self.database.get_plex_server(server_id)
        if not server:
            self.status_text.append("❌ Server not found")
            return
        
        self.status_text.append(f"🔄 Refreshing libraries for {server['name']}...")
        
        try:
            importer = create_plex_importer(server_id, self.database)
            if importer:
                libraries = importer.get_libraries()
                self.status_text.append(f"✅ Found {len(libraries)} libraries on {server['name']}")
                
                # Update library information in database
                for library in libraries:
                    # Store library information (we'll need to add this to database)
                    pass
            else:
                self.status_text.append(f"❌ Failed to connect to {server['name']}")
        except Exception as e:
            self.status_text.append(f"❌ Error refreshing libraries: {str(e)}")
    
    def _refresh_all_libraries(self):
        """Refresh libraries for all servers"""
        servers = self.database.get_plex_servers()
        self.status_text.append(f"🔄 Refreshing libraries for {len(servers)} servers...")
        
        for server in servers:
            self._refresh_libraries(server['id'])
    
    def _manage_libraries(self, server_id: int):
        """Open library management dialog for a server"""
        dialog = LibraryManagementDialog(self.database, server_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.status_text.append("✅ Library settings updated")
    
    def _manage_path_mappings(self, server_id: int):
        """Open path mappings dialog for a server"""
        dialog = ServerPathMappingsDialog(self.database, server_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.status_text.append("✅ Path mappings updated")
    
    def _sign_out_plex(self):
        """Sign out of Plex (remove all servers)"""
        reply = QMessageBox.question(
            self, "Sign Out of Plex", 
            "Are you sure you want to remove all Plex servers?\n\nThis will delete all server configurations and path mappings.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            servers = self.database.get_plex_servers()
            for server in servers:
                self.database.delete_plex_server(server['id'])
            
            self._load_servers()
            self.status_text.append("🚪 Signed out of Plex - all servers removed")
    
    def _show_server_context_menu(self, position):
        """Show context menu for server table items"""
        item = self.servers_table.itemAt(position)
        if item is None:
            return
        
        row = item.row()
        server_id = self.servers_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        server_name = self.servers_table.item(row, 0).text()
        
        # Create context menu
        menu = QMenu(self)
        
        # Edit server action
        edit_action = QAction("Edit Server", self)
        edit_action.triggered.connect(lambda: self._edit_server(server_id))
        menu.addAction(edit_action)
        
        # Delete server action
        delete_action = QAction("Delete Server", self)
        delete_action.triggered.connect(lambda: self._delete_server(server_id))
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        # Refresh libraries action
        refresh_action = QAction("Refresh Libraries", self)
        refresh_action.triggered.connect(lambda: self._refresh_libraries(server_id))
        menu.addAction(refresh_action)
        
        # Manage libraries action
        libraries_action = QAction("Manage Libraries", self)
        libraries_action.triggered.connect(lambda: self._manage_libraries(server_id))
        menu.addAction(libraries_action)
        
        # Path mappings action
        paths_action = QAction("Path Mappings", self)
        paths_action.triggered.connect(lambda: self._manage_path_mappings(server_id))
        menu.addAction(paths_action)
        
        # Show menu
        menu.exec(self.servers_table.mapToGlobal(position))


class LibraryManagementDialog(QDialog):
    """Dialog for managing libraries and sync settings for a specific server"""
    
    def __init__(self, database: RetrovueDatabase, server_id: int, parent=None):
        super().__init__(parent)
        self.database = database
        self.server_id = server_id
        self.server = database.get_plex_server(server_id)
        self.setWindowTitle(f"Libraries - {self.server['name'] if self.server else 'Unknown Server'}")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        self._setup_ui()
        self._load_libraries()
    
    def _setup_ui(self):
        """Set up the UI for library management"""
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel(f"{self.server['name']} Libraries")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(header_label)
        
        # Libraries Table
        self.libraries_table = QTableWidget()
        self.libraries_table.setColumnCount(4)
        self.libraries_table.setHorizontalHeaderLabels(["Library Name", "Type", "Root Path", "Synchronize"])
        self.libraries_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.libraries_table.setAlternatingRowColors(True)
        layout.addWidget(self.libraries_table)
        
        # Controls
        controls_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Libraries")
        self.refresh_btn.clicked.connect(self._refresh_libraries)
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self._save_changes)
        
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.save_btn)
        layout.addLayout(controls_layout)
        
        # Status
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(80)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._ok_clicked)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def _load_libraries(self):
        """Load libraries from the Plex server"""
        if not self.server:
            self.status_text.append("❌ Server not found")
            return
        
        self.status_text.append(f"🔄 Loading libraries from {self.server['name']}...")
        
        try:
            importer = create_plex_importer(self.server_id, self.database)
            if importer:
                libraries = importer.get_libraries()
                self.libraries_table.setRowCount(len(libraries))
                
                # Get saved libraries from database
                saved_libraries = self.database.get_server_libraries(server_id=self.server_id)
                saved_lib_dict = {lib['library_key']: lib for lib in saved_libraries}
                
                for i, library in enumerate(libraries):
                    # Library name
                    self.libraries_table.setItem(i, 0, QTableWidgetItem(library['title']))
                    
                    # Type
                    media_type = "Movies" if library['type'] == 'movie' else "Shows"
                    self.libraries_table.setItem(i, 1, QTableWidgetItem(media_type))
                    
                    # Root path (from locations)
                    root_path = ""
                    if 'locations' in library and library['locations']:
                        root_path = library['locations'][0]['path']
                    self.libraries_table.setItem(i, 2, QTableWidgetItem(root_path))
                    
                    # Synchronize checkbox - use saved preference or default to True
                    sync_checkbox = QCheckBox()
                    library_key = library.get('key', '')
                    saved_lib = saved_lib_dict.get(library_key)
                    is_sync_enabled = saved_lib['sync_enabled'] if saved_lib else True  # Default to True
                    sync_checkbox.setChecked(is_sync_enabled)
                    self.libraries_table.setCellWidget(i, 3, sync_checkbox)
                    
                    # Store library data
                    self.libraries_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, library)
                
                self.libraries_table.resizeColumnsToContents()
                self.status_text.append(f"✅ Loaded {len(libraries)} libraries")
            else:
                self.status_text.append(f"❌ Failed to connect to {self.server['name']}")
        except Exception as e:
            self.status_text.append(f"❌ Error loading libraries: {str(e)}")
    
    def _refresh_libraries(self):
        """Refresh the libraries list"""
        self._load_libraries()
    
    def _save_changes(self):
        """Save library sync settings"""
        saved_count = 0
        enabled_count = 0
        
        for i in range(self.libraries_table.rowCount()):
            # Get library data
            library_item = self.libraries_table.item(i, 0)
            if not library_item:
                continue
                
            library = library_item.data(Qt.ItemDataRole.UserRole)
            if not library:
                continue
            
            # Get sync checkbox
            checkbox = self.libraries_table.cellWidget(i, 3)
            if not checkbox:
                continue
            
            # Get library details
            library_key = library.get('key', '')
            library_name = library.get('title', '')
            library_type = library.get('type', '')
            library_root = ""
            if 'locations' in library and library['locations']:
                library_root = library['locations'][0]['path']
            
            is_sync_enabled = checkbox.isChecked()
            if is_sync_enabled:
                enabled_count += 1
            
            # Save/update library in database
            try:
                self.database.add_library(
                    server_id=self.server_id,
                    library_key=library_key,
                    library_name=library_name,
                    library_type=library_type,
                    library_root=library_root,
                    sync_enabled=is_sync_enabled
                )
                saved_count += 1
            except Exception as e:
                self.status_text.append(f"❌ Failed to save library {library_name}: {e}")
        
        self.status_text.append(f"💾 Saved {saved_count} libraries ({enabled_count} enabled for sync)")
    
    def _ok_clicked(self):
        """Handle OK button - save changes and close"""
        self._save_changes()
        self.accept()


class ServerPathMappingsDialog(QDialog):
    """Dialog for managing path mappings for a specific server"""
    
    def __init__(self, database: RetrovueDatabase, server_id: int, parent=None):
        super().__init__(parent)
        self.database = database
        self.server_id = server_id
        self.server = database.get_plex_server(server_id)
        self.setWindowTitle(f"Path Replacements - {self.server['name'] if self.server else 'Unknown Server'}")
        self.setModal(True)
        self.setMinimumSize(700, 500)
        self._setup_ui()
        self._load_path_mappings()
    
    def _setup_ui(self):
        """Set up the UI for path mappings"""
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel(f"{self.server['name']} Path Replacements")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(header_label)
        
        # Path Mappings Table
        self.mappings_table = QTableWidget()
        self.mappings_table.setColumnCount(5)
        self.mappings_table.setHorizontalHeaderLabels(["Plex Path", "Local Path", "Server", "Library", "Actions"])
        self.mappings_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.mappings_table.setAlternatingRowColors(True)
        layout.addWidget(self.mappings_table)
        
        # Controls
        controls_layout = QHBoxLayout()
        self.add_mapping_btn = QPushButton("Add New Path Replacement")
        self.add_mapping_btn.clicked.connect(self._add_path_mapping)
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.clicked.connect(self._save_changes)
        
        controls_layout.addWidget(self.add_mapping_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.save_btn)
        layout.addLayout(controls_layout)
        
        # Status
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(80)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._ok_clicked)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def _load_path_mappings(self):
        """Load path mappings for this server"""
        mappings = self.database.get_plex_path_mappings(server_id=self.server_id)
        self.mappings_table.setRowCount(len(mappings))
        
        for i, mapping in enumerate(mappings):
            # Plex Path
            self.mappings_table.setItem(i, 0, QTableWidgetItem(mapping['plex_path']))
            
            # Local Path
            self.mappings_table.setItem(i, 1, QTableWidgetItem(mapping['local_path']))
            
            # Server
            server_name = self.server['name'] if self.server else f"Server {self.server_id}"
            self.mappings_table.setItem(i, 2, QTableWidgetItem(server_name))
            
            # Library
            library_name = mapping.get('library_name', 'All Libraries')
            self.mappings_table.setItem(i, 3, QTableWidgetItem(library_name))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(5, 2, 5, 2)
            
            # Edit button
            edit_btn = QPushButton("✏️")
            edit_btn.setToolTip("Edit")
            edit_btn.setFixedSize(25, 25)
            edit_btn.clicked.connect(lambda checked, map_id=mapping['id']: self._edit_mapping(map_id))
            actions_layout.addWidget(edit_btn)
            
            # Delete button
            delete_btn = QPushButton("🗑️")
            delete_btn.setToolTip("Delete")
            delete_btn.setFixedSize(25, 25)
            delete_btn.clicked.connect(lambda checked, map_id=mapping['id']: self._delete_mapping(map_id))
            actions_layout.addWidget(delete_btn)
            
            actions_widget.setLayout(actions_layout)
            self.mappings_table.setCellWidget(i, 4, actions_widget)
            
            # Store mapping ID
            self.mappings_table.item(i, 0).setData(Qt.ItemDataRole.UserRole, mapping['id'])
        
        self.mappings_table.resizeColumnsToContents()
        self.status_text.append(f"🗺️ Loaded {len(mappings)} path mappings")
    
    def _add_path_mapping(self):
        """Add a new path mapping"""
        dialog = PathMappingEditDialog(self.database, server_id=self.server_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_path_mappings()
            self.status_text.append("✅ Added new path mapping")
    
    def _edit_mapping(self, mapping_id: int):
        """Edit an existing path mapping"""
        dialog = PathMappingEditDialog(self.database, mapping_id=mapping_id, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_path_mappings()
            self.status_text.append("✅ Updated path mapping")
    
    def _delete_mapping(self, mapping_id: int):
        """Delete a path mapping"""
        reply = QMessageBox.question(
            self, "Delete Path Mapping", 
            "Are you sure you want to delete this path mapping?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.database.delete_plex_path_mapping(mapping_id):
                self._load_path_mappings()
                self.status_text.append("🗑️ Deleted path mapping")
            else:
                QMessageBox.critical(self, "Delete Error", "Failed to delete path mapping.")
    
    def _save_changes(self):
        """Save path mapping changes"""
        self.status_text.append("💾 Path mappings saved")
    
    def _ok_clicked(self):
        """Handle OK button - save changes and close"""
        self._save_changes()
        self.accept()


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
        
        # Server Selection Group
        server_group = QGroupBox("Server Selection")
        server_layout = QVBoxLayout()
        
        # Server Selection
        server_layout.addWidget(QLabel("Select Plex Server:"))
        self.server_combo = QComboBox()
        self.server_combo.currentTextChanged.connect(self._on_server_changed)
        server_layout.addWidget(self.server_combo)
        
        # Server Info
        self.server_info_label = QLabel("No server selected")
        self.server_info_label.setWordWrap(True)
        self.server_info_label.setStyleSheet("color: #666; font-style: italic;")
        server_layout.addWidget(self.server_info_label)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # Sync Controls Group
        sync_group = QGroupBox("Content Sync")
        sync_layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel("Select a server above, then use the sync button below to import content from all libraries on that server.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic;")
        sync_layout.addWidget(info_label)
        
        # Sync Button
        self.import_btn = QPushButton("Sync All Libraries")
        self.import_btn.clicked.connect(self._start_import)
        self.import_btn.setMinimumHeight(40)
        self.import_btn.setEnabled(False)  # Disabled until server is selected
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
        """Load available Plex servers from database"""
        servers = self.database.get_plex_servers()
        self.server_combo.clear()
        
        if servers:
            for server in servers:
                if server['is_active']:
                    self.server_combo.addItem(server['name'], server['id'])
            
            if self.server_combo.count() > 0:
                self.status_text.append(f"📡 Found {len(servers)} Plex servers ({self.server_combo.count()} active)")
                self._on_server_changed()  # Update server info
            else:
                self.status_text.append("⚠️ No active Plex servers found. Please configure in Settings menu.")
        else:
            self.status_text.append("⚠️ No Plex servers found. Please configure in Settings menu.")
    
    def _on_server_changed(self):
        """Handle server selection change"""
        if self.server_combo.count() == 0:
            self.server_info_label.setText("No servers available")
            self.import_btn.setEnabled(False)
            return
        
        server_id = self.server_combo.currentData()
        if server_id:
            server = self.database.get_plex_server(server_id)
            if server:
                self.server_info_label.setText(f"Server: {server['name']}\nURL: {server['server_url']}")
                self.import_btn.setEnabled(True)
            else:
                self.server_info_label.setText("Server not found")
                self.import_btn.setEnabled(False)
        else:
            self.server_info_label.setText("No server selected")
            self.import_btn.setEnabled(False)
    
    def _start_import(self):
        """Start the import process"""
        # Get selected server
        server_id = self.server_combo.currentData()
        if not server_id:
            QMessageBox.warning(
                self, "No Server Selected", 
                "Please select a Plex server before syncing."
            )
            return
        
        server = self.database.get_plex_server(server_id)
        if not server:
            QMessageBox.warning(
                self, "Server Not Found", 
                "Selected server not found in database."
            )
            return
        
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
        self.status_text.append(f"🔄 Starting sync from server: {server['name']}")
        
        # Start import worker with server ID
        self.import_worker = ImportWorker('retrovue.db', server_id=server_id)
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
        self.plex_tab = PlexManagementTab(self.database)
        self.import_tab = ContentImportTab(self.database)
        self.browser_tab = ContentBrowserTab(self.database)
        central_widget.addTab(self.plex_tab, "Plex Servers")
        
        # Connect signal to refresh main window dropdown when servers change
        self.plex_tab.servers_changed.connect(self.import_tab._load_stored_credentials)
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
        
        # Note: Plex server management is now handled in the "Plex Servers" tab
    
    
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
