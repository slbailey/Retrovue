"""
Importers page: Servers → Libraries → Content Sync workflow.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, 
    QPushButton, QLineEdit, QTextEdit, QFormLayout, QGroupBox,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QComboBox, QSpinBox
)
from PySide6.QtCore import Qt
from datetime import datetime

from retrovue.core.api import get_api
from ...threads import Worker


class ImportersPage(QWidget):
    """
    Main importers page containing subtabs for the full Plex import workflow.
    
    Uses the unified API façade for all operations instead of directly
    accessing managers.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        
        # Get the unified API instance
        self.api = get_api()
        
        # Worker thread for async operations
        self.worker = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the UI with three subtabs."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Subtab widget
        self.subtabs = QTabWidget()
        layout.addWidget(self.subtabs)
        
        # Add the three workflow tabs
        self.subtabs.addTab(self._create_servers_tab(), "Servers")
        self.subtabs.addTab(self._create_libraries_tab(), "Libraries")
        self.subtabs.addTab(self._create_content_sync_tab(), "Content Sync")
    
    def _create_servers_tab(self):
        """Create the Servers management subtab (fully implemented)."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Server list
        list_group = QGroupBox("Existing Servers")
        list_layout = QVBoxLayout()
        
        self.server_table = QTableWidget()
        self.server_table.setColumnCount(4)
        self.server_table.setHorizontalHeaderLabels(["ID", "Name", "Base URL", "Default"])
        self.server_table.horizontalHeader().setStretchLastSection(True)
        self.server_table.setSelectionBehavior(QTableWidget.SelectRows)
        list_layout.addWidget(self.server_table)
        
        # Buttons for server list
        btn_layout = QHBoxLayout()
        self.refresh_servers_btn = QPushButton("Refresh")
        self.refresh_servers_btn.clicked.connect(self._refresh_servers)
        self.refresh_servers_btn.setToolTip("Reload the server list from database")
        
        self.delete_server_btn = QPushButton("Delete Selected")
        self.delete_server_btn.clicked.connect(self._delete_server)
        self.delete_server_btn.setToolTip("Delete the selected server from database")
        
        btn_layout.addWidget(self.refresh_servers_btn)
        btn_layout.addWidget(self.delete_server_btn)
        btn_layout.addStretch()
        list_layout.addLayout(btn_layout)
        
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        # Add server form
        form_group = QGroupBox("Add New Server")
        form_layout = QFormLayout()
        
        self.server_name = QLineEdit()
        self.server_name.setPlaceholderText("My Plex Server")
        self.server_name.setToolTip("Friendly name to identify this server")
        
        self.server_url = QLineEdit()
        self.server_url.setPlaceholderText("https://plex.example.com")
        self.server_url.setToolTip("Base URL of your Plex server (e.g., http://192.168.1.100:32400)")
        
        self.server_token = QLineEdit()
        self.server_token.setPlaceholderText("Your Plex token")
        self.server_token.setEchoMode(QLineEdit.Password)
        self.server_token.setToolTip("Plex authentication token (get from Plex settings)")
        
        self.add_server_btn = QPushButton("Add Server")
        self.add_server_btn.clicked.connect(self._add_server)
        self.add_server_btn.setToolTip("Add this Plex server to the database")
        
        form_layout.addRow("Name:", self.server_name)
        form_layout.addRow("Base URL:", self.server_url)
        form_layout.addRow("Token:", self.server_token)
        form_layout.addRow("", self.add_server_btn)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Log area
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        
        self.servers_log = QTextEdit()
        self.servers_log.setReadOnly(True)
        self.servers_log.setMaximumHeight(150)
        self.servers_log.setPlaceholderText("Operations log will appear here...")
        log_layout.addWidget(self.servers_log)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Load servers on init
        self._refresh_servers()
        
        return tab
    
    def _create_libraries_tab(self):
        """Create the Libraries discovery subtab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Server selection
        server_group = QGroupBox("Server Selection")
        server_layout = QHBoxLayout()
        
        server_layout.addWidget(QLabel("Server:"))
        self.library_server_combo = QComboBox()
        self.library_server_combo.currentIndexChanged.connect(self._on_library_server_changed)
        self.library_server_combo.setToolTip("Select a Plex server to discover its libraries")
        server_layout.addWidget(self.library_server_combo)
        
        self.discover_btn = QPushButton("Discover Libraries")
        self.discover_btn.clicked.connect(self._discover_libraries)
        self.discover_btn.setToolTip("Connect to the selected server and discover all available libraries")
        server_layout.addWidget(self.discover_btn)
        
        self.refresh_libraries_btn = QPushButton("Refresh")
        self.refresh_libraries_btn.clicked.connect(self._refresh_libraries)
        self.refresh_libraries_btn.setToolTip("Reload libraries list from database")
        server_layout.addWidget(self.refresh_libraries_btn)
        
        server_layout.addStretch()
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # Libraries table
        list_group = QGroupBox("Libraries")
        list_layout = QVBoxLayout()
        
        self.library_table = QTableWidget()
        self.library_table.setColumnCount(5)
        self.library_table.setHorizontalHeaderLabels(["ID", "Key", "Title", "Type", "Sync Enabled"])
        self.library_table.horizontalHeader().setStretchLastSection(True)
        self.library_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.library_table.itemChanged.connect(self._on_library_sync_changed)
        list_layout.addWidget(self.library_table)
        
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        # Log area
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        
        self.libraries_log = QTextEdit()
        self.libraries_log.setReadOnly(True)
        self.libraries_log.setMaximumHeight(150)
        self.libraries_log.setPlaceholderText("Discovery progress will appear here...")
        log_layout.addWidget(self.libraries_log)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Populate server dropdown
        self._populate_library_server_combo()
        
        return tab
    
    def _create_content_sync_tab(self):
        """Create the Content Sync subtab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Server and library selection
        selection_group = QGroupBox("Sync Configuration")
        selection_layout = QVBoxLayout()
        
        # Server dropdown
        server_layout = QHBoxLayout()
        server_layout.addWidget(QLabel("Server:"))
        self.sync_server_combo = QComboBox()
        self.sync_server_combo.currentIndexChanged.connect(self._on_sync_server_changed)
        self.sync_server_combo.setToolTip("Select which Plex server to sync content from")
        server_layout.addWidget(self.sync_server_combo)
        server_layout.addStretch()
        selection_layout.addLayout(server_layout)
        
        # Library selection
        library_layout = QHBoxLayout()
        library_layout.addWidget(QLabel("Library:"))
        self.sync_library_combo = QComboBox()
        self.sync_library_combo.currentIndexChanged.connect(self._on_sync_library_changed)
        self.sync_library_combo.setToolTip("Select which library to sync (must have sync enabled)")
        library_layout.addWidget(self.sync_library_combo)
        library_layout.addStretch()
        selection_layout.addLayout(library_layout)
        
        # Limit input
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(QLabel("Limit items (0 for no limit):"))
        self.sync_limit_spinbox = QSpinBox()
        self.sync_limit_spinbox.setRange(0, 99999)
        self.sync_limit_spinbox.setValue(0)
        self.sync_limit_spinbox.setToolTip("Limit number of items to sync (0 = no limit, useful for testing)")
        limit_layout.addWidget(self.sync_limit_spinbox)
        limit_layout.addStretch()
        selection_layout.addLayout(limit_layout)
        
        selection_group.setLayout(selection_layout)
        layout.addWidget(selection_group)
        
        # Path mappings
        mappings_group = QGroupBox("Path Mappings")
        mappings_layout = QVBoxLayout()
        
        self.mappings_table = QTableWidget()
        self.mappings_table.setColumnCount(3)
        self.mappings_table.setHorizontalHeaderLabels(["Plex Path", "Local Path", ""])
        self.mappings_table.horizontalHeader().setStretchLastSection(False)
        self.mappings_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.mappings_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.mappings_table.setColumnWidth(2, 80)
        self.mappings_table.setMaximumHeight(150)
        mappings_layout.addWidget(self.mappings_table)
        
        # Add mapping form
        add_mapping_layout = QHBoxLayout()
        add_mapping_layout.addWidget(QLabel("Plex Path:"))
        self.plex_path_input = QLineEdit()
        self.plex_path_input.setPlaceholderText("/mnt/media/movies")
        self.plex_path_input.setToolTip("Path prefix as seen by Plex server (e.g., /mnt/media/movies)")
        add_mapping_layout.addWidget(self.plex_path_input)
        
        add_mapping_layout.addWidget(QLabel("Local Path:"))
        self.local_path_input = QLineEdit()
        self.local_path_input.setPlaceholderText("D:\\Movies")
        self.local_path_input.setToolTip("Corresponding local path on this machine (e.g., D:\\Movies)")
        add_mapping_layout.addWidget(self.local_path_input)
        
        self.add_mapping_btn = QPushButton("Add Mapping")
        self.add_mapping_btn.clicked.connect(self._add_path_mapping)
        self.add_mapping_btn.setToolTip("Add this path mapping to the database")
        add_mapping_layout.addWidget(self.add_mapping_btn)
        
        mappings_layout.addLayout(add_mapping_layout)
        mappings_group.setLayout(mappings_layout)
        layout.addWidget(mappings_group)
        
        # Sync buttons
        button_layout = QHBoxLayout()
        
        self.dry_run_btn = QPushButton("Dry Run (Preview)")
        self.dry_run_btn.clicked.connect(lambda: self._start_sync(dry_run=True))
        self.dry_run_btn.setToolTip("Preview sync without writing to database - safe to test")
        button_layout.addWidget(self.dry_run_btn)
        
        self.sync_btn = QPushButton("Sync (Write to DB)")
        self.sync_btn.clicked.connect(lambda: self._start_sync(dry_run=False))
        self.sync_btn.setToolTip("Sync content and write to database - this will modify data")
        button_layout.addWidget(self.sync_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Log area
        log_group = QGroupBox("Sync Progress")
        log_layout = QVBoxLayout()
        
        self.sync_log = QTextEdit()
        self.sync_log.setReadOnly(True)
        self.sync_log.setPlaceholderText("Sync progress will appear here...")
        log_layout.addWidget(self.sync_log)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Populate dropdowns
        self._populate_sync_server_combo()
        
        return tab
    
    # --- Servers Tab Handlers ---
    
    def _refresh_servers(self):
        """Refresh the server list from persistence."""
        try:
            servers = self.api.list_servers()
            
            self.server_table.setRowCount(len(servers))
            
            for row, server in enumerate(servers):
                # ID
                id_item = QTableWidgetItem(str(server['id']))
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
                self.server_table.setItem(row, 0, id_item)
                
                # Name
                name_item = QTableWidgetItem(server['name'])
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                self.server_table.setItem(row, 1, name_item)
                
                # Base URL
                url_item = QTableWidgetItem(server['base_url'])
                url_item.setFlags(url_item.flags() & ~Qt.ItemIsEditable)
                self.server_table.setItem(row, 2, url_item)
                
                # Default
                default = "YES" if server.get('is_default') else "NO"
                default_item = QTableWidgetItem(default)
                default_item.setFlags(default_item.flags() & ~Qt.ItemIsEditable)
                self.server_table.setItem(row, 3, default_item)
            
            # Auto-resize columns
            self.server_table.resizeColumnsToContents()
            
            self._log_servers(f"Loaded {len(servers)} server(s)")
            
        except Exception as e:
            self._log_servers(f"Error loading servers: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load servers: {e}")
    
    def _add_server(self):
        """Add a new Plex server."""
        name = self.server_name.text().strip()
        url = self.server_url.text().strip()
        token = self.server_token.text().strip()
        
        if not all([name, url, token]):
            QMessageBox.warning(self, "Validation Error", "Please fill in all fields")
            return
        
        try:
            server_id = self.api.add_server(name, url, token)
            self._log_servers(f"✓ Added server '{name}' (ID: {server_id})")
            
            # Clear form
            self.server_name.clear()
            self.server_url.clear()
            self.server_token.clear()
            
            # Refresh list
            self._refresh_servers()
            
            QMessageBox.information(self, "Success", f"Server '{name}' added successfully!")
            
        except ValueError as e:
            self._log_servers(f"✗ Validation error: {e}")
            QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e:
            self._log_servers(f"✗ Error adding server: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add server: {e}")
    
    def _delete_server(self):
        """Delete the selected server."""
        current_row = self.server_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a server to delete")
            return
        
        # Get server info
        server_id = int(self.server_table.item(current_row, 0).text())
        server_name = self.server_table.item(current_row, 1).text()
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete server '{server_name}' (ID: {server_id})?\n\n"
            "This will also delete all associated libraries, path mappings, and content!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            success = self.api.delete_server(server_id)
            
            if success:
                self._log_servers(f"✓ Deleted server '{server_name}' (ID: {server_id})")
                self._refresh_servers()
                QMessageBox.information(self, "Success", f"Server '{server_name}' deleted successfully!")
            else:
                self._log_servers(f"✗ Server ID {server_id} not found")
                QMessageBox.warning(self, "Not Found", f"Server ID {server_id} not found")
                
        except Exception as e:
            self._log_servers(f"✗ Error deleting server: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete server: {e}")
    
    def _log_servers(self, message: str):
        """Append a timestamped message to the servers log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.servers_log.append(f"[{timestamp}] {message}")
    
    # --- Libraries Tab Handlers ---
    
    def _populate_library_server_combo(self):
        """Populate the server dropdown for libraries tab."""
        try:
            servers = self.api.list_servers()
            
            self.library_server_combo.clear()
            
            for server in servers:
                self.library_server_combo.addItem(
                    f"{server['name']} ({server['base_url']})",
                    server['id']  # Store server_id as item data
                )
            
            if not servers:
                self._log_libraries("No servers found. Please add a server first.")
                self.discover_btn.setEnabled(False)
                self.refresh_libraries_btn.setEnabled(False)
            else:
                self.discover_btn.setEnabled(True)
                self.refresh_libraries_btn.setEnabled(True)
                # Auto-load libraries for first server
                self._refresh_libraries()
                
        except Exception as e:
            self._log_libraries(f"Error loading servers: {e}")
    
    def _on_library_server_changed(self):
        """Handle server selection change."""
        self._refresh_libraries()
    
    def _refresh_libraries(self):
        """Refresh the libraries list for the selected server."""
        server_id = self.library_server_combo.currentData()
        
        if not server_id:
            self.library_table.setRowCount(0)
            return
        
        try:
            libraries = self.api.list_libraries(server_id)
            
            # Temporarily disconnect to avoid triggering during population
            self.library_table.itemChanged.disconnect(self._on_library_sync_changed)
            
            self.library_table.setRowCount(len(libraries))
            
            for row, lib in enumerate(libraries):
                # ID
                id_item = QTableWidgetItem(str(lib['id']))
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
                self.library_table.setItem(row, 0, id_item)
                
                # Key
                key_item = QTableWidgetItem(str(lib['plex_library_key']))
                key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
                self.library_table.setItem(row, 1, key_item)
                
                # Title
                title_item = QTableWidgetItem(lib['title'])
                title_item.setFlags(title_item.flags() & ~Qt.ItemIsEditable)
                self.library_table.setItem(row, 2, title_item)
                
                # Type
                type_item = QTableWidgetItem(lib['library_type'])
                type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                self.library_table.setItem(row, 3, type_item)
                
                # Sync Enabled (checkbox)
                sync_item = QTableWidgetItem()
                sync_item.setFlags(sync_item.flags() | Qt.ItemIsUserCheckable)
                sync_item.setCheckState(Qt.Checked if lib['sync_enabled'] else Qt.Unchecked)
                self.library_table.setItem(row, 4, sync_item)
            
            # Reconnect
            self.library_table.itemChanged.connect(self._on_library_sync_changed)
            
            # Auto-resize columns
            self.library_table.resizeColumnsToContents()
            
            self._log_libraries(f"Loaded {len(libraries)} library(ies)")
            
        except Exception as e:
            self._log_libraries(f"Error loading libraries: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load libraries: {e}")
    
    def _discover_libraries(self):
        """Discover libraries from the selected Plex server (async)."""
        server_id = self.library_server_combo.currentData()
        
        if not server_id:
            QMessageBox.warning(self, "No Server", "Please select a server first")
            return
        
        # Disable button during discovery
        self.discover_btn.setEnabled(False)
        self._log_libraries("Starting library discovery...")
        
        # Create worker thread
        self.worker = Worker(self.api.discover_libraries, server_id)
        
        # Connect signals
        self.worker.signals.progress.connect(self._on_discovery_progress)
        self.worker.signals.finished.connect(self._on_discovery_finished)
        self.worker.signals.error.connect(self._on_discovery_error)
        
        # Start worker
        self.worker.start()
    
    def _on_discovery_progress(self, progress: dict):
        """Handle discovery progress updates."""
        msg = progress.get('msg', '')
        self._log_libraries(msg)
    
    def _on_discovery_finished(self):
        """Handle discovery completion."""
        self._log_libraries("✓ Discovery complete!")
        self.discover_btn.setEnabled(True)
        
        # Refresh the table to show discovered libraries
        self._refresh_libraries()
    
    def _on_discovery_error(self, error_msg: str):
        """Handle discovery error."""
        self._log_libraries(f"✗ Error: {error_msg}")
        self.discover_btn.setEnabled(True)
        QMessageBox.critical(self, "Discovery Error", f"Failed to discover libraries:\n\n{error_msg}")
    
    def _on_library_sync_changed(self, item: QTableWidgetItem):
        """Handle sync checkbox change."""
        # Only handle checkbox column (column 4)
        if item.column() != 4:
            return
        
        row = item.row()
        library_id = int(self.library_table.item(row, 0).text())
        library_title = self.library_table.item(row, 2).text()
        enabled = item.checkState() == Qt.Checked
        
        try:
            success = self.api.toggle_library_sync(library_id, enabled)
            
            if success:
                status = "enabled" if enabled else "disabled"
                self._log_libraries(f"✓ Sync {status} for '{library_title}'")
            else:
                self._log_libraries(f"✗ Library ID {library_id} not found")
                
        except Exception as e:
            self._log_libraries(f"✗ Error updating sync: {e}")
            QMessageBox.critical(self, "Error", f"Failed to update sync status: {e}")
    
    def _log_libraries(self, message: str):
        """Append a timestamped message to the libraries log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.libraries_log.append(f"[{timestamp}] {message}")
    
    # --- Content Sync Tab Handlers ---
    
    def _populate_sync_server_combo(self):
        """Populate the server dropdown for sync tab."""
        try:
            servers = self.api.list_servers()
            
            self.sync_server_combo.clear()
            
            for server in servers:
                self.sync_server_combo.addItem(
                    f"{server['name']} ({server['base_url']})",
                    server['id']
                )
            
            if not servers:
                self._log_sync("No servers found. Please add a server first.")
                self.dry_run_btn.setEnabled(False)
                self.sync_btn.setEnabled(False)
            else:
                # Auto-load libraries for first server
                self._on_sync_server_changed()
                
        except Exception as e:
            self._log_sync(f"Error loading servers: {e}")
    
    def _on_sync_server_changed(self):
        """Handle server selection change."""
        server_id = self.sync_server_combo.currentData()
        
        if not server_id:
            self.sync_library_combo.clear()
            return
        
        try:
            # Load sync-enabled libraries
            libraries = self.api.list_libraries(server_id)
            sync_enabled_libs = [lib for lib in libraries if lib['sync_enabled']]
            
            self.sync_library_combo.clear()
            
            for lib in sync_enabled_libs:
                self.sync_library_combo.addItem(
                    f"{lib['title']} ({lib['library_type']})",
                    lib['id']
                )
            
            if not sync_enabled_libs:
                self._log_sync("No sync-enabled libraries found. Please enable sync for libraries first.")
                self.dry_run_btn.setEnabled(False)
                self.sync_btn.setEnabled(False)
            else:
                self.dry_run_btn.setEnabled(True)
                self.sync_btn.setEnabled(True)
                # Auto-load mappings for first library
                self._on_sync_library_changed()
                
        except Exception as e:
            self._log_sync(f"Error loading libraries: {e}")
    
    def _on_sync_library_changed(self):
        """Handle library selection change."""
        self._refresh_path_mappings()
    
    def _refresh_path_mappings(self):
        """Refresh the path mappings table."""
        server_id = self.sync_server_combo.currentData()
        library_id = self.sync_library_combo.currentData()
        
        if not server_id or not library_id:
            self.mappings_table.setRowCount(0)
            return
        
        try:
            mappings = self.api.list_path_mappings(server_id, library_id)
            
            self.mappings_table.setRowCount(len(mappings))
            
            for row, mapping in enumerate(mappings):
                mapping_id = mapping['id']
                plex_path = mapping['plex_path']
                local_path = mapping['local_path']
                
                # Plex Path
                plex_item = QTableWidgetItem(plex_path)
                plex_item.setFlags(plex_item.flags() & ~Qt.ItemIsEditable)
                plex_item.setData(Qt.UserRole, mapping_id)  # Store mapping ID
                self.mappings_table.setItem(row, 0, plex_item)
                
                # Local Path
                local_item = QTableWidgetItem(local_path)
                local_item.setFlags(local_item.flags() & ~Qt.ItemIsEditable)
                self.mappings_table.setItem(row, 1, local_item)
                
                # Delete button
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, mid=mapping_id: self._delete_path_mapping(mid))
                self.mappings_table.setCellWidget(row, 2, delete_btn)
            
            self._log_sync(f"Loaded {len(mappings)} path mapping(s)")
            
        except Exception as e:
            self._log_sync(f"Error loading path mappings: {e}")
    
    def _add_path_mapping(self):
        """Add a new path mapping."""
        server_id = self.sync_server_combo.currentData()
        library_id = self.sync_library_combo.currentData()
        plex_path = self.plex_path_input.text().strip()
        local_path = self.local_path_input.text().strip()
        
        if not server_id or not library_id:
            QMessageBox.warning(self, "No Selection", "Please select a server and library first")
            return
        
        if not plex_path or not local_path:
            QMessageBox.warning(self, "Validation Error", "Please enter both Plex path and local path")
            return
        
        try:
            mapping_id = self.api.add_path_mapping(server_id, library_id, plex_path, local_path)
            self._log_sync(f"✓ Added path mapping (ID: {mapping_id})")
            
            # Clear inputs
            self.plex_path_input.clear()
            self.local_path_input.clear()
            
            # Refresh table
            self._refresh_path_mappings()
            
        except ValueError as e:
            self._log_sync(f"✗ Validation error: {e}")
            QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e:
            self._log_sync(f"✗ Error adding mapping: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add path mapping: {e}")
    
    def _delete_path_mapping(self, mapping_id: int):
        """Delete a path mapping."""
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete this path mapping (ID: {mapping_id})?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            success = self.api.delete_path_mapping(mapping_id)
            
            if success:
                self._log_sync(f"✓ Deleted path mapping (ID: {mapping_id})")
                self._refresh_path_mappings()
                QMessageBox.information(self, "Success", "Path mapping deleted successfully!")
            else:
                self._log_sync(f"✗ Path mapping not found (ID: {mapping_id})")
                QMessageBox.warning(self, "Not Found", "Path mapping not found")
                
        except Exception as e:
            self._log_sync(f"✗ Error deleting mapping: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete path mapping: {e}")
    
    def _start_sync(self, dry_run: bool = True):
        """Start the sync operation (async)."""
        server_id = self.sync_server_combo.currentData()
        library_id = self.sync_library_combo.currentData()
        
        if not server_id or not library_id:
            QMessageBox.warning(self, "No Selection", "Please select a server and library first")
            return
        
        # Check if library has path mappings
        mappings = self.api.list_path_mappings(server_id, library_id)
        if not mappings:
            QMessageBox.warning(
                self,
                "No Path Mappings",
                "This library has no path mappings configured.\n\n"
                "Please add at least one path mapping before syncing."
            )
            return
        
        # Get library key for sync
        try:
            library = self.api.get_library(library_id)
            if not library:
                QMessageBox.critical(self, "Error", "Library not found")
                return
            
            library_key = library['plex_library_key']
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get library info: {e}")
            return
        
        # Get sync limit from spinbox
        limit = self.sync_limit_spinbox.value() if self.sync_limit_spinbox.value() > 0 else None
        
        # Disable buttons during sync
        self.dry_run_btn.setEnabled(False)
        self.sync_btn.setEnabled(False)
        
        mode_str = "DRY RUN" if dry_run else "COMMIT"
        limit_str = f" (limit: {limit})" if limit else ""
        self._log_sync(f"Starting sync [{mode_str}]{limit_str}...")
        
        # Create worker thread
        self.worker = Worker(
            self.api.sync_content,
            server_id,
            [library_key],
            ["movie", "episode"],
            limit,
            dry_run
        )
        
        # Connect signals
        self.worker.signals.progress.connect(self._on_sync_progress)
        self.worker.signals.finished.connect(self._on_sync_finished)
        self.worker.signals.error.connect(self._on_sync_error)
        
        # Start worker
        self.worker.start()
    
    def _on_sync_progress(self, progress: dict):
        """Handle sync progress updates."""
        msg = progress.get('msg', '')
        self._log_sync(msg)
    
    def _on_sync_finished(self):
        """Handle sync completion."""
        self._log_sync("✓ Sync operation complete!")
        self.dry_run_btn.setEnabled(True)
        self.sync_btn.setEnabled(True)
    
    def _on_sync_error(self, error_msg: str):
        """Handle sync error."""
        self._log_sync(f"✗ Error: {error_msg}")
        self.dry_run_btn.setEnabled(True)
        self.sync_btn.setEnabled(True)
        QMessageBox.critical(self, "Sync Error", f"Sync operation failed:\n\n{error_msg}")
    
    def _log_sync(self, message: str):
        """Append a timestamped message to the sync log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.sync_log.append(f"[{timestamp}] {message}")

