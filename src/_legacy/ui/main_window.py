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
import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, 
    QProgressBar, QTableWidget, QTableWidgetItem, QTableView, QComboBox,
    QGroupBox, QGridLayout, QMessageBox, QFileDialog, QDialog,
    QDialogButtonBox, QMenuBar, QMenu, QCheckBox
)
from PySide6.QtCore import QThread, Signal, Qt, QModelIndex, QAbstractTableModel
from PySide6.QtGui import QFont, QAction

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from retrovue.core.database import RetrovueDatabase
from retrovue.ui.ui_bus import UiBus
from retrovue.ui.import_worker import ImportWorker
import retrovue.core.plex_integration as sync_api


class LibrariesModel(QAbstractTableModel):
    """Model for displaying libraries with refresh_row capability"""
    
    def __init__(self, database: RetrovueDatabase, server_id: int = None):
        super().__init__()
        self.database = database
        self.server_id = server_id
        self._rows = []
        self._row_index_by_library_id = {}
        self._load_data()
    
    def _load_data(self):
        """Load library data from database"""
        try:
            if self.server_id:
                libraries = self.database.get_server_libraries(server_id=self.server_id)
            else:
                libraries = self.database.get_all_libraries()
            
            self._rows = []
            self._row_index_by_library_id = {}
            
            for i, library in enumerate(libraries):
                self._rows.append(library)
                self._row_index_by_library_id[library['id']] = i
                
        except Exception as e:
            print(f"Error loading libraries: {e}")
            self._rows = []
            self._row_index_by_library_id = {}
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._rows)
    
    def columnCount(self, parent=QModelIndex()):
        return 5  # Name, Type, Root Path, Sync Enabled, Last Synced
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            headers = ["Library Name", "Type", "Root Path", "Sync Enabled", "Last Synced"]
            if section < len(headers):
                return headers[section]
        return None
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._rows):
            return None
        
        library = self._rows[index.row()]
        column = index.column()
        
        if role == Qt.DisplayRole:
            if column == 0:  # Name
                return library.get('library_name', 'Unknown')
            elif column == 1:  # Type
                return "Movies" if library.get('library_type') == 'movie' else "Shows"
            elif column == 2:  # Root Path
                return library.get('library_root', '')
            elif column == 3:  # Sync Enabled
                return "Yes" if library.get('sync_enabled', True) else "No"
            elif column == 4:  # Last Synced
                last_synced = library.get('last_synced_at')
                if last_synced:
                    try:
                        # Convert epoch timestamp to datetime
                        dt = datetime.datetime.fromtimestamp(last_synced)
                        return dt.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        return "Unknown"
                return "Never"
        
        elif role == Qt.UserRole:
            return library
        
        return None
    
    def refresh_row(self, library_id: int):
        """Refresh a specific library row"""
        try:
            if library_id in self._row_index_by_library_id:
                row = self._row_index_by_library_id[library_id]
                # Fetch updated library data
                updated_library = self.database.get_library_by_id(library_id)
                if updated_library:
                    self._rows[row] = updated_library
                    # Emit dataChanged for the entire row
                    top_left = self.index(row, 0)
                    bottom_right = self.index(row, self.columnCount() - 1)
                    self.dataChanged.emit(top_left, bottom_right)
        except Exception as e:
            print(f"Error refreshing library row {library_id}: {e}")
            # Fallback to full refresh
            self.beginResetModel()
            self._load_data()
            self.endResetModel()
    
    def refresh(self):
        """Refresh all data"""
        self.beginResetModel()
        self._load_data()
        self.endResetModel()


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
        self.mappings_table.setColumnCount(3)
        self.mappings_table.setHorizontalHeaderLabels(["Server", "Plex Prefix", "Local Prefix"])
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
        # Populate the Path Mappings table with per-server prefixes
        rows = []
        for server in self.database.get_plex_servers():
            for (pp, lp) in self.database.get_path_mappings(server["id"]):
                rows.append((server["name"], pp, lp))
        
        self.mappings_table.setColumnCount(3)
        self.mappings_table.setHorizontalHeaderLabels(["Server", "Plex Prefix", "Local Prefix"])
        self.mappings_table.setRowCount(len(rows))
        
        for r, (srv, pp, lp) in enumerate(rows):
            self.mappings_table.setItem(r, 0, QTableWidgetItem(srv))
            self.mappings_table.setItem(r, 1, QTableWidgetItem(pp))
            self.mappings_table.setItem(r, 2, QTableWidgetItem(lp))
        
        self.mappings_table.resizeColumnsToContents()
        self.status_text.append(f"🗺️ Loaded {len(rows)} path mappings")
    
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
            # Test connection using the wrapper API
            # For now, just show a basic success message
            self.status_text.append(f"✅ Connection test for '{server_name}' - use sync to verify full connectivity")
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
        
        # Get the mapping details from the table
        server_name = self.mappings_table.item(current_row, 0).text()
        plex_path = self.mappings_table.item(current_row, 1).text()
        local_path = self.mappings_table.item(current_row, 2).text()
        
        # Find the server ID
        server_id = None
        for server in self.database.get_plex_servers():
            if server['name'] == server_name:
                server_id = server['id']
                break
        
        if server_id:
            dialog = PathMappingEditDialog(self.database, server_id=server_id, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self._load_path_mappings()
        else:
            QMessageBox.critical(self, "Edit Error", "Could not find server for this mapping.")
    
    def _delete_path_mapping(self):
        """Delete selected path mapping"""
        current_row = self.mappings_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a path mapping to delete.")
            return
        
        # Get the mapping details from the table
        server_name = self.mappings_table.item(current_row, 0).text()
        plex_path = self.mappings_table.item(current_row, 1).text()
        local_path = self.mappings_table.item(current_row, 2).text()
        
        reply = QMessageBox.question(
            self, "Delete Path Mapping", 
            f"Are you sure you want to delete the path mapping for '{plex_path}' on server '{server_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Find the server ID
            server_id = None
            for server in self.database.get_plex_servers():
                if server['name'] == server_name:
                    server_id = server['id']
                    break
            
            if server_id:
                self.database.remove_path_mapping(server_id, plex_path)
                self.status_text.append(f"🗑️ Deleted path mapping for '{plex_path}' on server '{server_name}'")
                self._load_path_mappings()
            else:
                QMessageBox.critical(self, "Delete Error", "Could not find server for this mapping.")


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
                    self.result_server_id = self.server_id  # Set result for parent
                    self.accept()
                else:
                    self.status_text.append("❌ Failed to update server")
            else:
                # Add new server
                server_id = self.database.add_plex_server(name, server_url, token, is_active)
                if server_id:
                    self.status_text.append(f"💾 Server added successfully (ID: {server_id})")
                    self.result_server_id = server_id  # Set result for parent
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
            mappings = self.database.get_path_mappings_all()
            for mapping in mappings:
                if mapping['id'] == self.mapping_id:
                    # Set server (only if no server_id provided)
                    if not self.server_id and hasattr(self, 'server_combo'):
                        for i in range(self.server_combo.count()):
                            if self.server_combo.itemData(i) == mapping['server_id']:
                                self.server_combo.setCurrentIndex(i)
                                break
                    
                    # Load the path data
                    self.plex_path_input.setText(mapping['plex_prefix'])
                    self.local_path_input.setText(mapping['local_prefix'])
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
                success = self.database.update_path_mapping(
                    self.mapping_id, plex_path, local_path
                )
                if not success:
                    QMessageBox.critical(self, "Update Error", "Failed to update path mapping.")
                    return
            else:
                # Add new mapping
                self.database.add_path_mapping(server_id, plex_path, local_path)
            
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

            server_id = getattr(dialog, "result_server_id", None)
            if server_id:
                # Immediately discover & persist libraries for the new server
                self._refresh_libraries(server_id)
            else:
                # Safe fallback (shouldn't happen once result_server_id is set)
                self._refresh_all_libraries()
    
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
        """Refresh libraries for a specific server and persist them."""
        server = self.database.get_plex_server(server_id)
        if not server:
            self.status_text.append("❌ Server not found")
            return

        self.status_text.append(f"🔄 Refreshing libraries for {server['name']}...")

        try:
            from retrovue.core.plex_integration import create_plex_importer
            importer = create_plex_importer(server_id, self.database)
            if not importer:
                self.status_text.append(f"❌ Failed to connect to {server['name']}")
                return

            libs = importer.get_libraries()  # [{ key, title, type, agent, locations }]
            self.status_text.append(f"📚 Found {len(libs)} libraries on {server['name']}")

            saved = 0
            for lib in libs:
                section_key = str(lib.get("key"))
                title = lib.get("title") or "Untitled"
                lib_type = lib.get("type") or "unknown"

                # Normalize root locations across JSON/XML shapes
                roots = []
                locs = lib.get("locations") or []
                if isinstance(locs, dict):
                    # xmltodict can yield a dict or a list of dicts
                    locs = [locs]
                for loc in locs:
                    if isinstance(loc, dict):
                        p = loc.get("path")
                        if p:
                            roots.append(p)

                # Fallback: per-library fetch if needed
                if not roots:
                    try:
                        roots = importer.get_library_root_paths(section_key)
                    except Exception:
                        roots = []

                root_str = ";".join(roots) if roots else None

                # Persist (INSERT OR REPLACE in your DB schema)
                self.database.add_library(
                    server_id=server_id,
                    library_key=section_key,
                    library_name=title,
                    library_type=lib_type,
                    library_root=root_str,
                    sync_enabled=True,  # default true so "Sync Selected" works immediately
                )
                saved += 1

            self.status_text.append(f"✅ Saved/updated {saved} libraries for {server['name']}")
        except Exception as e:
            self.status_text.append(f"❌ Error refreshing libraries: {e}")
    
    def _refresh_all_libraries(self):
        """Refresh libraries for all servers"""
        servers = self.database.get_plex_servers()
        self.status_text.append(f"🔄 Refreshing libraries for {len(servers)} servers...")
        
        for server in servers:
            self._refresh_libraries(server['id'])

    def currentServerId(self) -> int | None:
        """Get the currently selected server ID from the servers table"""
        row = self.servers_table.currentRow()
        if row < 0:
            return None
        return self.servers_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
    
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
        self.libraries_table.setColumnCount(3)
        self.libraries_table.setHorizontalHeaderLabels(["Name", "Type", "Selected"])
        self.libraries_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.libraries_table.setAlternatingRowColors(True)
        self.libraries_table.horizontalHeader().setStretchLastSection(True)
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
            # Get libraries from database
            libs = self.database.get_server_libraries(self.server_id)
            self.libraries_table.setRowCount(len(libs))
            
            for r, lib in enumerate(libs):
                # Name column
                item_name = QTableWidgetItem(lib['library_name'])
                # Keep section_key on the item so we can save later
                item_name.setData(Qt.ItemDataRole.UserRole, lib['library_key'])
                self.libraries_table.setItem(r, 0, item_name)

                # Type column
                self.libraries_table.setItem(r, 1, QTableWidgetItem(lib['library_type']))

                # Selected column (checkbox)
                w = QWidget()
                cb = QCheckBox("Synchronize")
                cb.setChecked(bool(lib.get('sync_enabled', True)))
                lay = QHBoxLayout(w)
                lay.setContentsMargins(0, 0, 0, 0)
                lay.addWidget(cb)
                lay.addStretch()
                w.setLayout(lay)
                self.libraries_table.setCellWidget(r, 2, w)
            
            self.libraries_table.resizeColumnsToContents()
            self.status_text.append(f"✅ Loaded {len(libs)} saved libraries")
        except Exception as e:
            self.status_text.append(f"❌ Error loading libraries: {str(e)}")
    
    def currentLibraryRow(self):
        """Get the currently selected library row data"""
        current_row = self.libraries_table.currentRow()
        if current_row >= 0:
            name_item = self.libraries_table.item(current_row, 0)
            type_item = self.libraries_table.item(current_row, 1)
            
            if name_item and type_item:
                # Create a simple object with the required fields
                class LibraryRow:
                    def __init__(self, server_id, library_key, library_type, library_name):
                        self.server_id = server_id
                        self.library_id = None  # We don't have the DB ID here
                        self.section_key = library_key
                        self.type = library_type
                        self.name = library_name
                
                library_key = name_item.data(Qt.ItemDataRole.UserRole)
                return LibraryRow(self.server_id, library_key, type_item.text(), name_item.text())
        return None
    
    
    def _refresh_libraries(self):
        """Refresh libraries from Plex and save them to database"""
        if not self.server:
            self.status_text.append("❌ Server not found")
            return

        self.status_text.append(f"🔄 Refreshing libraries for {self.server['name']}...")

        try:
            from retrovue.core.plex_integration import create_plex_importer
            importer = create_plex_importer(self.server_id, self.database)
            if not importer:
                self.status_text.append(f"❌ Failed to connect to {self.server['name']}")
                return

            libs = importer.get_libraries()  # [{ key, title, type, agent, locations }]
            self.status_text.append(f"📚 Found {len(libs)} libraries on {self.server['name']}")

            saved = 0
            for lib in libs:
                section_key = str(lib.get("key"))
                title = lib.get("title") or "Untitled"
                lib_type = lib.get("type") or "unknown"

                # Normalize root locations across JSON/XML shapes
                roots = []
                locs = lib.get("locations") or []
                if isinstance(locs, dict):
                    # xmltodict can yield a dict or a list of dicts
                    locs = [locs]
                for loc in locs:
                    if isinstance(loc, dict):
                        p = loc.get("path")
                        if p:
                            roots.append(p)

                # Fallback: per-library fetch if needed
                if not roots:
                    try:
                        roots = importer.get_library_root_paths(section_key)
                    except Exception:
                        roots = []

                root_str = ";".join(roots) if roots else None

                # Persist (INSERT OR REPLACE in your DB schema)
                self.database.add_library(
                    server_id=self.server_id,
                    library_key=section_key,
                    library_name=title,
                    library_type=lib_type,
                    library_root=root_str,
                    sync_enabled=True,  # default true so "Sync Selected" works immediately
                )
                saved += 1

            self.status_text.append(f"✅ Saved/updated {saved} libraries for {self.server['name']}")
            
            # Reload the table to show the updated libraries
            self._load_libraries()
        except Exception as e:
            self.status_text.append(f"❌ Error refreshing libraries: {e}")
    
    def _save_changes(self):
        """Save library sync settings"""
        try:
            rows = self.libraries_table.rowCount()
            saved_count = 0
            
            for r in range(rows):
                name_item = self.libraries_table.item(r, 0)
                if name_item:
                    section_key = name_item.data(Qt.ItemDataRole.UserRole)
                    selected_w = self.libraries_table.cellWidget(r, 2)
                    cb = selected_w.findChild(QCheckBox) if selected_w else None
                    enabled = cb.isChecked() if cb else True
                    
                    self.database.set_library_selected(self.server_id, section_key, enabled)
                    saved_count += 1
            
            self.status_text.append(f"💾 Saved sync settings for {saved_count} libraries")
        except Exception as e:
            self.status_text.append(f"❌ Error saving changes: {str(e)}")
    
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
        self.mappings_table.setColumnCount(3)
        self.mappings_table.setHorizontalHeaderLabels(["Server", "Plex Prefix", "Local Prefix"])
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
        mappings = self.database.get_path_mappings_for_server(self.server_id)
        self.mappings_table.setRowCount(len(mappings))
        
        # Get server name
        server = self.database.get_plex_server(self.server_id)
        server_name = server['name'] if server else f"Server {self.server_id}"
        
        for i, mapping in enumerate(mappings):
            # Server
            self.mappings_table.setItem(i, 0, QTableWidgetItem(server_name))
            
            # Plex Prefix
            self.mappings_table.setItem(i, 1, QTableWidgetItem(mapping['plex_prefix']))
            
            # Local Prefix
            self.mappings_table.setItem(i, 2, QTableWidgetItem(mapping['local_prefix']))
            
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
            if self.database.delete_path_mapping_by_id(mapping_id):
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
        info_label = QLabel("Select a server above, then use the sync options in the toolbar or Tools menu to import content.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic;")
        sync_layout.addWidget(info_label)
        
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
            return
        
        server_id = self.server_combo.currentData()
        if server_id:
            server = self.database.get_plex_server(server_id)
            if server:
                self.server_info_label.setText(f"Server: {server['name']}\nURL: {server['server_url']}")
            else:
                self.server_info_label.setText("Server not found")
        else:
            self.server_info_label.setText("No server selected")


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
        
        # Add backfill button
        self.backfill_btn = QPushButton("Fix Missing Data")
        self.backfill_btn.setToolTip("Backfill missing library names and server data")
        self.backfill_btn.clicked.connect(self.backfill_missing_data)
        filter_layout.addWidget(self.backfill_btn)
        
        # Add library mapping fix button
        self.fix_mapping_btn = QPushButton("Fix Library Names")
        self.fix_mapping_btn.setToolTip("Fix incorrect library name mappings (e.g., 'Adult content' -> 'Anime TV')")
        self.fix_mapping_btn.clicked.connect(self.fix_library_mapping)
        filter_layout.addWidget(self.fix_mapping_btn)
        
        # Add cleanup orphaned data button
        self.cleanup_btn = QPushButton("Clean Orphaned Data")
        self.cleanup_btn.setToolTip("Remove media files from deleted Plex servers")
        self.cleanup_btn.clicked.connect(self.cleanup_orphaned_data)
        filter_layout.addWidget(self.cleanup_btn)
        
        # Add fix missing records button
        self.fix_records_btn = QPushButton("Fix Missing Records")
        self.fix_records_btn.setToolTip("Create missing episode/movie records for media files")
        self.fix_records_btn.clicked.connect(self.fix_missing_records)
        filter_layout.addWidget(self.fix_records_btn)
        
        # Add refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setToolTip("Reload from database")
        self.refresh_btn.clicked.connect(self.refresh_content)
        filter_layout.addWidget(self.refresh_btn)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Content Table
        self.content_table = QTableWidget()
        self.content_table.setColumnCount(8)
        self.content_table.setHorizontalHeaderLabels([
            "Title", "Type", "Duration", "Rating", "Show", "Season/Episode", "Library", "Resolved Path"
        ])
        
        # Enable context menu for the table
        self.content_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.content_table.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.content_table)
        
        self.setLayout(layout)
    
    def _load_content(self):
        """Load content from database and repopulate filters + table."""
        try:
            # Block signals so we don't trigger _filter_content() repeatedly mid-load
            self.media_type_combo.blockSignals(True)
            self.show_combo.blockSignals(True)
            self.library_combo.blockSignals(True)

            # Media types
            media_types = self.database.get_media_types()  # ["episode","movie"]
            self.media_type_combo.clear()
            self.media_type_combo.addItem("All")
            self.media_type_combo.addItems(media_types)

            # Shows
            shows = self.database.get_shows()  # list of dicts with 'title'
            self.show_combo.clear()
            self.show_combo.addItem("All Shows")
            for s in shows:
                self.show_combo.addItem(s['title'])

            # Libraries
            libraries = self.database.get_distinct_libraries_from_media()  # list of library names
            self.library_combo.clear()
            self.library_combo.addItem("All Libraries")
            for lib in libraries:
                self.library_combo.addItem(lib)
        finally:
            # Always re-enable signals
            self.media_type_combo.blockSignals(False)
            self.show_combo.blockSignals(False)
            self.library_combo.blockSignals(False)

        # Single, intentional redraw at the end
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
                
                # Get resolved path using path mapping service
                resolved_path = self.database.get_local_path_for_media_file(episode['id']) \
                    if episode.get('id') else episode.get('file_path', '')
                
                self.content_table.setItem(row, 0, QTableWidgetItem(episode['episode_title']))
                self.content_table.setItem(row, 1, QTableWidgetItem("Episode"))
                self.content_table.setItem(row, 2, QTableWidgetItem(duration_str))
                self.content_table.setItem(row, 3, QTableWidgetItem(episode.get('rating', '')))
                self.content_table.setItem(row, 4, QTableWidgetItem(episode['show_title']))
                self.content_table.setItem(row, 5, QTableWidgetItem(season_episode))
                self.content_table.setItem(row, 6, QTableWidgetItem(episode.get('library_name', '')))
                self.content_table.setItem(row, 7, QTableWidgetItem(resolved_path))
                
                # Store media_file_id for context menu operations
                self.content_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, episode['id'])
        
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
                
                # Get resolved path using path mapping service
                resolved_path = self.database.get_local_path_for_media_file(movie['id']) \
                    if movie.get('id') else movie.get('file_path', '')
                
                self.content_table.setItem(row, 0, QTableWidgetItem(movie['title']))
                self.content_table.setItem(row, 1, QTableWidgetItem("Movie"))
                self.content_table.setItem(row, 2, QTableWidgetItem(duration_str))
                self.content_table.setItem(row, 3, QTableWidgetItem(movie.get('rating', '')))
                self.content_table.setItem(row, 4, QTableWidgetItem(""))
                self.content_table.setItem(row, 5, QTableWidgetItem(""))
                self.content_table.setItem(row, 6, QTableWidgetItem(movie.get('library_name', '')))
                self.content_table.setItem(row, 7, QTableWidgetItem(resolved_path))
                
                # Store media_file_id for context menu operations
                self.content_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, movie['id'])
        
        # Resize columns to content
        self.content_table.resizeColumnsToContents()
    
    def refresh_content(self):
        """Refresh the content browser after database updates"""
        self._load_content()
    
    def backfill_missing_data(self):
        """Backfill missing library data and refresh the browser"""
        try:
            result = self.database.backfill_missing_library_data()
            if result["total"] > 0:
                QMessageBox.information(
                    self, "Data Backfill Complete",
                    f"Backfilled {result['updated']} rows, {result['skipped']} still missing data.\n\n"
                    f"Total rows processed: {result['total']}"
                )
                self.refresh_content()
            else:
                QMessageBox.information(
                    self, "No Backfill Needed",
                    "All media files already have complete library data."
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Backfill Error",
                f"Failed to backfill missing data: {str(e)}"
            )
    
    def fix_library_mapping(self):
        """Fix incorrect library name mappings"""
        try:
            result = self.database.fix_library_name_mapping()
            if result["fixed"] > 0:
                QMessageBox.information(
                    self, "Library Mapping Fixed",
                    f"Fixed {result['fixed']} items with incorrect library names.\n\n"
                    f"Applied {result['mappings_applied']} library name corrections."
                )
                self.refresh_content()
            else:
                QMessageBox.information(
                    self, "No Mapping Issues Found",
                    "All library names are correctly mapped."
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Library Mapping Error",
                f"Failed to fix library mappings: {str(e)}"
            )
    
    def cleanup_orphaned_data(self):
        """Remove media files from deleted servers"""
        try:
            result = self.database.cleanup_orphaned_media_files()
            if result["total"] > 0:
                QMessageBox.information(
                    self, "Orphaned Data Cleaned",
                    f"Removed {result['removed']} orphaned media files from deleted servers.\n\n"
                    f"Details:\n"
                    f"• Episodes removed: {result['episodes_removed']}\n"
                    f"• Movies removed: {result['movies_removed']}\n"
                    f"• Shows removed: {result['shows_removed']}\n"
                    f"• Total items: {result['total']}"
                )
                self.refresh_content()
            else:
                QMessageBox.information(
                    self, "No Orphaned Data Found",
                    "All media files are properly linked to existing servers."
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Cleanup Error",
                f"Failed to cleanup orphaned data: {str(e)}"
            )
    
    def fix_missing_records(self):
        """Create missing episode and movie records"""
        try:
            result = self.database.fix_missing_episode_movie_records()
            if result["episodes_created"] > 0 or result["movies_created"] > 0:
                QMessageBox.information(
                    self, "Missing Records Fixed",
                    f"Created missing records:\n\n"
                    f"• Episodes created: {result['episodes_created']}\n"
                    f"• Movies created: {result['movies_created']}\n\n"
                    f"Missing before fix:\n"
                    f"• Episodes: {result['missing_episodes']}\n"
                    f"• Movies: {result['missing_movies']}"
                )
                self.refresh_content()
            else:
                QMessageBox.information(
                    self, "No Missing Records Found",
                    "All media files already have corresponding episode/movie records."
                )
        except Exception as e:
            QMessageBox.critical(
                self, "Fix Records Error",
                f"Failed to create missing records: {str(e)}"
            )
    
    def _show_context_menu(self, position):
        """Show context menu for table items"""
        item = self.content_table.itemAt(position)
        if item is None:
            return
        
        row = item.row()
        media_path_item = self.content_table.item(row, 7)  # Resolved Path column
        if media_path_item is None:
            return
        
        media_path = media_path_item.text()
        if not media_path:
            return
        
        # Get media_file_id from stored data
        media_file_id = self.content_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        # Create context menu
        menu = QMenu(self)
        
        # Copy path action
        copy_action = QAction("Copy Media Path", self)
        copy_action.triggered.connect(lambda: self._copy_to_clipboard(media_path))
        menu.addAction(copy_action)
        
        # Copy local path action (if path mapping is configured)
        if media_file_id:
            try:
                local_path = self.database.get_local_path_for_media_file(media_file_id)
                if local_path and local_path != media_path:
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
    
    def refresh_content(self):
        """Public entry to reload filters and table."""
        self._load_content()


class RetrovueMainWindow(QMainWindow):
    """Main window for Retrovue application"""
    
    def __init__(self):
        super().__init__()
        self.database = RetrovueDatabase('retrovue.db')
        self.ui_bus = UiBus()
        self._last_worker = None
        self._current_library = None  # Track currently selected library
        self.librariesModel = LibrariesModel(self.database)  # Create libraries model
        self._setup_ui()
        self._setup_sync_signals()
    
    def _setup_ui(self):
        """Set up the main window UI"""
        self.setWindowTitle("Retrovue - IPTV Management System v2")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create sync toolbar
        self._create_sync_toolbar()
        
        # Create central widget with tabs
        central_widget = QTabWidget()
        self.setCentralWidget(central_widget)
        
        # Add progress bar to status bar
        self.progressBar = QProgressBar()
        self.progressBar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progressBar)
        
        # Add tabs
        self.plex_tab = PlexManagementTab(self.database)
        self.import_tab = ContentImportTab(self.database)
        self.browser_tab = ContentBrowserTab(self.database)
        central_widget.addTab(self.plex_tab, "Plex Servers")
        
        # Connect signal to refresh main window dropdown when servers change
        self.plex_tab.servers_changed.connect(self.import_tab._load_stored_credentials)
        central_widget.addTab(self.import_tab, "Import Content")
        central_widget.addTab(self.browser_tab, "Browse Content")
        
        # Keep a handle to the tab widget and connect tab change signal
        self._tabs = central_widget
        self._tabs.currentChanged.connect(self._on_tab_changed)
        
        # Set font
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)
    
    def _create_menu_bar(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('View')
        refresh_browse = QAction('Refresh Browse Content', self)
        refresh_browse.setShortcut('F5')
        refresh_browse.triggered.connect(self.refresh_content_browser)
        view_menu.addAction(refresh_browse)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        # Sync actions
        sync_all_action = QAction('Sync Selected (All Servers)', self)
        sync_all_action.triggered.connect(self._sync_all_selected)
        tools_menu.addAction(sync_all_action)
        
        sync_server_action = QAction('Sync Selected (Server)', self)
        sync_server_action.triggered.connect(self._sync_selected_server)
        tools_menu.addAction(sync_server_action)
        
        sync_library_action = QAction('Sync This Library', self)
        sync_library_action.triggered.connect(self._sync_this_library)
        tools_menu.addAction(sync_library_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        about_action = QAction('About', self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About Retrovue", 
                         "Retrovue - Plex Content Management\n\n"
                         "A tool for managing and syncing Plex content.")
    
    def _on_tab_changed(self, index: int):
        """Refresh Browse tab whenever it becomes active."""
        try:
            w = self._tabs.widget(index)
            if w is self.browser_tab:
                self.browser_tab.refresh_content()
        except Exception as e:
            # Non-fatal; just surface to status bar
            self.statusBar().showMessage(f"Browse refresh failed: {e}")
    
    def _setup_sync_signals(self):
        """Set up sync signal connections"""
        self.ui_bus.sync_started.connect(self.onSyncStarted)
        self.ui_bus.page_progress.connect(self.onPageProgress)
        self.ui_bus.sync_completed.connect(self.onSyncCompleted)
    
    def _create_sync_toolbar(self):
        """Create sync toolbar with actions and options"""
        tb = self.addToolBar("Sync")
        
        # Sync actions
        self.actSyncLibrary = QAction("Sync This Library", self)
        self.actSyncServerSelected = QAction("Sync Selected (Server)", self)
        self.actSyncAllSelected = QAction("Sync Selected (All Servers)", self)
        
        self.actSyncLibrary.triggered.connect(self._sync_this_library)
        self.actSyncServerSelected.triggered.connect(self._sync_selected_server)
        self.actSyncAllSelected.triggered.connect(self._sync_all_selected)
        
        tb.addAction(self.actSyncLibrary)
        tb.addAction(self.actSyncServerSelected)
        tb.addAction(self.actSyncAllSelected)
        
        # Options
        self.chkDeep = QCheckBox("Deep", self)
        self.chkDry = QCheckBox("Dry Run", self)
        tb.addWidget(self.chkDeep)
        tb.addWidget(self.chkDry)
    
    def _start_worker(self, mode: str, server_id=None, library_ref=None):
        """Start a sync worker"""
        w = ImportWorker(
            db_path='retrovue.db',
            ui_bus=self.ui_bus,
            mode=mode,
            server_id=server_id,
            library_ref=library_ref,
            deep=getattr(self, "chkDeep", None).isChecked() if hasattr(self, "chkDeep") else False,
            dry_run=getattr(self, "chkDry", None).isChecked() if hasattr(self, "chkDry") else False,
            sync_api=sync_api,
        )
        w.start()
        self._last_worker = w  # prevent GC
    
    def onSyncStarted(self, server_id, library_id):
        """Handle sync started event"""
        self.statusBar().showMessage(f"🔄 Sync started (server {server_id}, library {library_id})")
        if hasattr(self, "progressBar"):
            self.progressBar.setVisible(True)
            self.progressBar.setRange(0, 0)  # busy spinner
        
        # Add to status text if available (simplified for now)
        # TODO: Add proper tab-based status display
    
    def onPageProgress(self, server_id, library_id, processed, changed, skipped, errors):
        """Handle page progress event"""
        # Update status bar with progress
        self.statusBar().showMessage(f"📊 Processing: {processed} items (+{changed} ~{skipped} !{errors})")
        
        # Add to status text if available (simplified for now)
        # TODO: Add proper tab-based status display
    
    def onSyncCompleted(self, server_id, library_id, summary: dict):
        """Handle sync completed event"""
        if hasattr(self, "progressBar"):
            self.progressBar.setRange(0, 1)
            self.progressBar.setValue(1)
            self.progressBar.setVisible(False)
        
        # Refresh views safely
        if hasattr(self, "librariesModel"):
            if hasattr(self.librariesModel, "refresh_row"):
                try:
                    self.librariesModel.refresh_row(library_id)
                except Exception:
                    pass
            elif hasattr(self.librariesModel, "refresh"):
                self.librariesModel.refresh()
        
        if hasattr(self, "itemsModel") and getattr(self.itemsModel, "library_id", None) == library_id:
            self.itemsModel.refresh(library_id)
        
        # Refresh the content browser to show newly imported content
        if hasattr(self, "browser_tab"):
            try:
                self.browser_tab.refresh_content()
            except Exception as e:
                print(f"Error refreshing browser tab: {e}")
        
        # Update status bar with final results
        self.statusBar().showMessage(
            f"✅ Sync completed: +{summary['changed']} ~{summary['skipped']} !{summary['errors']} "
            f"(missing↑{summary.get('missing_promoted',0)}, deleted↑{summary.get('deleted_promoted',0)})"
        )
        
        # Add to status text if available (simplified for now)
        # TODO: Add proper tab-based status display
    
    def _current_server_id(self) -> int | None:
        """Get the current server ID from UI"""
        # Try to get from import tab server combo (primary server selection)
        if hasattr(self, 'import_tab') and hasattr(self.import_tab, 'server_combo'):
            server_id = self.import_tab.server_combo.currentData()
            if server_id:
                return server_id
        
        # Try to get from plex management tab
        if hasattr(self, 'plex_tab') and hasattr(self.plex_tab, 'currentServerId'):
            return self.plex_tab.currentServerId()
        
        return None
    
    def _current_library_ref(self) -> dict | None:
        """
        Must return: {'server_id','id','section_key','type','name'}
        """
        # Check if we have a currently selected library
        if self._current_library:
            return self._current_library
        
        # Try to get from plex management tab
        if hasattr(self, 'plex_tab') and hasattr(self.plex_tab, 'currentLibraryRow'):
            row = self.plex_tab.currentLibraryRow()
            if row:
                return {
                    "server_id": row.server_id,
                    "id": row.library_id,
                    "section_key": row.section_key,
                    "type": row.type,
                    "name": row.name
                }
        
        # If no specific library is selected, return None to indicate "all libraries"
        return None
    
    def set_current_library(self, library_ref: dict | None):
        """Set the currently selected library"""
        self._current_library = library_ref
    
    def _sync_this_library(self):
        """Sync the currently selected library"""
        lib = self._current_library_ref()
        if lib:
            self._start_worker("one", library_ref=lib)
        else:
            self.statusBar().showMessage("No library selected")
    
    def _sync_selected_server(self):
        """Sync selected libraries on current server"""
        sid = self._current_server_id()
        if not sid:
            QMessageBox.warning(self, "No Server Selected", "Pick a Plex server first.")
            return
        self._start_worker("server_selected", server_id=sid)
    
    def _sync_all_selected(self):
        """Sync all selected libraries across all servers"""
        self._start_worker("all_selected")
    
    def refresh_content_browser(self):
        """Refresh the content browser tab"""
        self.browser_tab.refresh_content()
    
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
