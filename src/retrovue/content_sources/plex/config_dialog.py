"""
Plex content source configuration dialog.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QLabel, QTextEdit, QCheckBox, QSpinBox, QAbstractItemView,
    QFileDialog, QMenu
)
from PySide6.QtCore import Qt, Signal
from typing import Dict, Any, List
import os
import datetime


class PlexConfigDialog(QDialog):
    """Dialog for configuring Plex content source."""
    
    config_saved = Signal(dict)  # Emitted when configuration is saved
    
    def __init__(self, parent=None, config: Dict[str, Any] = None):
        super().__init__(parent)
        self.config = config or {}
        self._build_ui()
        self._load_config()
    
    def _build_ui(self):
        """Build the configuration UI."""
        self.setWindowTitle("Configure Plex Content Source")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Basic settings
        basic_group = QGroupBox("Basic Settings")
        basic_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("My Plex Server")
        self.name_input.setToolTip("Friendly name for this Plex server")
        basic_layout.addRow("Name:", self.name_input)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("http://localhost:32400")
        self.url_input.setToolTip("Plex server URL")
        basic_layout.addRow("URL:", self.url_input)
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Plex authentication token")
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setToolTip("Plex authentication token")
        basic_layout.addRow("Token:", self.token_input)
        
        # Test connection button
        self.test_btn = QPushButton("Test Connection")
        self.test_btn.clicked.connect(self._test_connection)
        basic_layout.addRow("", self.test_btn)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Libraries section
        libraries_group = QGroupBox("Libraries")
        libraries_layout = QVBoxLayout()
        
        # Libraries table - Enhanced with path mapping functionality
        self.libraries_table = QTableWidget()
        self.libraries_table.setColumnCount(8)
        self.libraries_table.setHorizontalHeaderLabels([
            "Key", "Title", "Type", "Sync", "Last Sync", "Plex Path", "Mapped Path", "Browse"
        ])
        # Set column widths
        self.libraries_table.setColumnWidth(0, 40)   # Key - narrow
        self.libraries_table.setColumnWidth(4, 150)  # Last Sync - medium
        self.libraries_table.setColumnWidth(5, 200)  # Plex Path - wide enough for paths
        self.libraries_table.setColumnWidth(7, 60)   # Browse button column - narrow
        self.libraries_table.horizontalHeader().setStretchLastSection(False)
        self.libraries_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Title stretches
        self.libraries_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)  # Mapped Path stretches
        self.libraries_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Set default row height for better text alignment
        self.libraries_table.verticalHeader().setDefaultSectionSize(30)
        self.libraries_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.libraries_table.customContextMenuRequested.connect(self._show_library_context_menu)
        # Make Mapped Path column editable
        self.libraries_table.itemChanged.connect(self._on_library_table_item_changed)
        
        # Flag to prevent auto-save when programmatically updating cells
        self._suppress_item_changed = False
        
        # Discover libraries button
        self.discover_btn = QPushButton("Discover Libraries")
        self.discover_btn.clicked.connect(self._discover_libraries)
        libraries_layout.addWidget(self.discover_btn)
        
        # Library selection buttons
        library_buttons = QHBoxLayout()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self._select_all_libraries)
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self._deselect_all_libraries)
        
        library_buttons.addWidget(self.select_all_btn)
        library_buttons.addWidget(self.deselect_all_btn)
        library_buttons.addStretch()
        
        libraries_layout.addLayout(library_buttons)
        libraries_layout.addWidget(self.libraries_table)
        
        libraries_group.setLayout(libraries_layout)
        layout.addWidget(libraries_group)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._save_config)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _load_config(self):
        """Load existing configuration."""
        if self.config:
            self.name_input.setText(self.config.get('name', ''))
            self.url_input.setText(self.config.get('url', ''))
            self.token_input.setText(self.config.get('token', ''))
            
            # Load existing libraries from database
            self._load_existing_libraries_from_db()
    
    def _test_connection(self):
        """Test connection to Plex server."""
        url = self.url_input.text().strip()
        token = self.token_input.text().strip()
        
        if not url or not token:
            QMessageBox.warning(self, "Missing Information", "Please enter URL and token")
            return
        
        try:
            from .client import PlexClient
            client = PlexClient(url, token)
            if client.test_connection():
                QMessageBox.information(self, "Connection Successful", "Successfully connected to Plex server")
            else:
                QMessageBox.warning(self, "Connection Failed", "Could not connect to Plex server")
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Error testing connection: {e}")
    
    def _discover_libraries(self):
        """Discover libraries from Plex server."""
        url = self.url_input.text().strip()
        token = self.token_input.text().strip()
        
        if not url or not token:
            QMessageBox.warning(self, "Missing Information", "Please enter URL and token first")
            return
        
        try:
            from .client import PlexClient
            client = PlexClient(url, token)
            libraries = client.get_libraries()
            
            # Temporarily disconnect itemChanged to avoid triggering during population
            self.libraries_table.itemChanged.disconnect(self._on_library_table_item_changed)
            
            self.libraries_table.setRowCount(len(libraries))
            for i, library in enumerate(libraries):
                # Plex Key (show this to user instead of database ID)
                key_item = QTableWidgetItem(str(library.key))
                key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
                # Store library data in UserRole for internal use
                key_item.setData(Qt.UserRole, {
                    'key': library.key,
                    'title': library.title,
                    'type': library.type,
                    'agent': library.agent
                })
                self.libraries_table.setItem(i, 0, key_item)
                
                # Title
                title_item = QTableWidgetItem(library.title)
                title_item.setFlags(title_item.flags() & ~Qt.ItemIsEditable)
                self.libraries_table.setItem(i, 1, title_item)
                
                # Type
                type_item = QTableWidgetItem(library.type)
                type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                self.libraries_table.setItem(i, 2, type_item)
                
                # Sync Enabled (checkbox)
                sync_checkbox = QCheckBox()
                sync_checkbox.setChecked(True)  # Default to enabled
                self.libraries_table.setCellWidget(i, 3, sync_checkbox)
                
                # Last Sync (placeholder - would need database integration)
                last_sync_item = QTableWidgetItem("Never")
                last_sync_item.setFlags(last_sync_item.flags() & ~Qt.ItemIsEditable)
                self.libraries_table.setItem(i, 4, last_sync_item)
                
                # Plex Path (generated from library name)
                library_name = library.title.lower().replace(" ", "").replace("-", "")
                plex_path = f'/media/{library_name}'
                plex_path_item = QTableWidgetItem(plex_path)
                plex_path_item.setFlags(plex_path_item.flags() & ~Qt.ItemIsEditable)
                self.libraries_table.setItem(i, 5, plex_path_item)
                
                # Mapped Path (EDITABLE) - starts empty
                mapped_path_item = QTableWidgetItem("")
                mapped_path_item.setFlags(mapped_path_item.flags() | Qt.ItemIsEditable)
                # Store library data for change detection
                mapped_path_item.setData(Qt.UserRole, {
                    'key': library.key,
                    'title': library.title,
                    'plex_path': plex_path,
                    'old_path': ''  # Store original value for change detection
                })
                self.libraries_table.setItem(i, 6, mapped_path_item)
                
                # Browse button
                browse_btn = QPushButton("...")
                browse_btn.setMaximumWidth(30)
                browse_btn.setToolTip("Browse for local folder")
                browse_btn.clicked.connect(lambda checked, row=i: self._browse_library_path(row))
                self.libraries_table.setCellWidget(i, 7, browse_btn)
            
            # Reconnect itemChanged
            self.libraries_table.itemChanged.connect(self._on_library_table_item_changed)
            
            # Save discovered libraries to database
            self._save_discovered_libraries_to_db(libraries)
            
            QMessageBox.information(self, "Libraries Discovered", f"Found {len(libraries)} libraries")
        except Exception as e:
            QMessageBox.critical(self, "Discovery Error", f"Error discovering libraries: {e}")
    
    def _select_all_libraries(self):
        """Select all libraries for sync."""
        for row in range(self.libraries_table.rowCount()):
            sync_checkbox = self.libraries_table.cellWidget(row, 3)
            if sync_checkbox:
                sync_checkbox.setChecked(True)
    
    def _deselect_all_libraries(self):
        """Deselect all libraries for sync."""
        for row in range(self.libraries_table.rowCount()):
            sync_checkbox = self.libraries_table.cellWidget(row, 3)
            if sync_checkbox:
                sync_checkbox.setChecked(False)
    
    def _on_library_table_item_changed(self, item):
        """Handle when a library table item is edited."""
        try:
            # Skip if suppressed (programmatic update)
            if self._suppress_item_changed:
                return
                
            # Only handle Mapped Path column (column 6)
            if item.column() != 6:
                return
            
            # Get the library info
            row = item.row()
            library_data = self.libraries_table.item(row, 0).data(Qt.UserRole)
            library_title = self.libraries_table.item(row, 1).text()
            plex_path = self.libraries_table.item(row, 5).text()
            new_mapped_path = item.text().strip()
            
            # Get stored data
            data = item.data(Qt.UserRole)
            if not data:
                return
            
            old_mapped_path = data.get('old_path', '')
            
            # Skip if the path hasn't actually changed
            if new_mapped_path == old_mapped_path:
                return
            
            # Update the stored old_path
            if data:
                data['old_path'] = new_mapped_path
                item.setData(Qt.UserRole, data)
            
            # Save to database
            if new_mapped_path:
                print(f"Path mapping for {library_title}: {plex_path} -> {new_mapped_path}")
                # Save to database (this would need database integration)
                self._save_path_mapping_to_db(library_data, plex_path, new_mapped_path)
                # Try to extrapolate mappings for other libraries
                self._extrapolate_mappings(plex_path, new_mapped_path)
            else:
                print(f"Cleared path mapping for {library_title}")
                # Remove from database
                self._remove_path_mapping_from_db(library_data)
                
        except Exception as e:
            print(f"Error in _on_library_table_item_changed: {e}")
    
    def _browse_library_path(self, row):
        """Open folder browser for a library row."""
        # Get current mapped path
        mapped_path_item = self.libraries_table.item(row, 6)
        current_path = mapped_path_item.text().strip() if mapped_path_item else ""
        
        # Start from a reasonable default directory
        if current_path and os.path.exists(current_path):
            start_dir = current_path
        else:
            start_dir = ""  # Let QFileDialog choose default
        
        # Open folder dialog
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Local Folder",
            start_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if folder and mapped_path_item:
            # Update the table item (suppress auto-save)
            self._suppress_item_changed = True
            mapped_path_item.setText(folder)
            self._suppress_item_changed = False
            
            # Update stored data
            data = mapped_path_item.data(Qt.UserRole)
            if data:
                data['old_path'] = folder
                mapped_path_item.setData(Qt.UserRole, data)
            
            print(f"Selected local path for {self.libraries_table.item(row, 1).text()}: {folder}")
    
    def _show_library_context_menu(self, position):
        """Show context menu for library table."""
        item = self.libraries_table.itemAt(position)
        if item is None:
            return
            
        # Get the library info from the row
        row = item.row()
        library_data = self.libraries_table.item(row, 0).data(Qt.UserRole)
        library_title = self.libraries_table.item(row, 1).text()
        
        # Create context menu
        menu = QMenu(self)
        
        # Toggle sync action
        sync_checkbox = self.libraries_table.cellWidget(row, 3)
        if sync_checkbox and sync_checkbox.isChecked():
            toggle_action = menu.addAction(f"Disable Sync for '{library_title}'")
            toggle_action.triggered.connect(lambda: sync_checkbox.setChecked(False))
        else:
            toggle_action = menu.addAction(f"Enable Sync for '{library_title}'")
            toggle_action.triggered.connect(lambda: sync_checkbox.setChecked(True))
        
        # Show menu
        menu.exec(self.libraries_table.mapToGlobal(position))
    
    def _extrapolate_mappings(self, known_plex_path, known_local_path):
        """
        Try to extrapolate path mappings for other libraries based on a known mapping.
        
        Example:
        If known_plex_path = "/media/adultcontent" and known_local_path = "R:\\Media\\AdultContent"
        Then for plex_path = "/media/anime-movies", suggest "R:\\Media\\Anime-Movies"
        """
        try:
            if not known_plex_path or not known_local_path:
                return
            
            print("Analyzing path patterns for suggestions...")
            
            # Normalize paths for comparison
            known_plex_path = known_plex_path.replace('\\', '/').strip('/')
            known_local_path = known_local_path.replace('/', '\\').rstrip('\\')
            
            # Extract the common base and the specific folder
            plex_parts = known_plex_path.split('/')
            local_parts = known_local_path.split('\\')
            
            if len(plex_parts) < 2 or len(local_parts) < 2:
                return  # Not enough structure to extrapolate
            
            # Get all libraries from the table
            suggestions = []
            
            for row in range(self.libraries_table.rowCount()):
                # Get library data
                library_data = self.libraries_table.item(row, 0).data(Qt.UserRole)
                if not library_data:
                    continue
                
                lib_plex_path = library_data.get('plex_path', '').replace('\\', '/').strip('/')
                if not lib_plex_path or lib_plex_path == known_plex_path:
                    continue
                
                # Check if library already has a mapping
                mapped_path_item = self.libraries_table.item(row, 6)
                if mapped_path_item and mapped_path_item.text().strip():
                    continue  # Skip libraries that already have mappings
                
                lib_plex_parts = lib_plex_path.split('/')
                
                # Try to find common prefix between known_plex_path and lib_plex_path
                common_prefix_len = 0
                for i in range(min(len(plex_parts), len(lib_plex_parts))):
                    if plex_parts[i].lower() == lib_plex_parts[i].lower():
                        common_prefix_len = i + 1
                    else:
                        break
                
                if common_prefix_len > 0:
                    # We have a common prefix! Try to map it
                    # Build suggested local path
                    suggested_local_parts = local_parts[:common_prefix_len]
                    
                    # Add the remaining parts from lib_plex_path
                    for i in range(common_prefix_len, len(lib_plex_parts)):
                        # Try to match case style from known mapping
                        plex_part = lib_plex_parts[i]
                        # Convert to title case (capitalize first letter of each word)
                        suggested_part = plex_part.replace('-', ' ').replace('_', ' ').title().replace(' ', '')
                        suggested_local_parts.append(suggested_part)
                    
                    suggested_local_path = '\\'.join(suggested_local_parts)
                    
                    suggestions.append({
                        'row': row,
                        'library_title': library_data.get('title', ''),
                        'plex_path': lib_plex_path,
                        'suggested_local_path': suggested_local_path,
                        'confidence': 'medium'
                    })
            
            if suggestions:
                print(f"Found {len(suggestions)} potential mappings based on pattern")
                self._show_mapping_suggestions(suggestions)
            else:
                print("No similar library paths found for auto-mapping")
                
        except Exception as e:
            print(f"Error extrapolating mappings: {e}")
    
    def _show_mapping_suggestions(self, suggestions):
        """Show dialog with suggested path mappings."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Suggested Path Mappings")
        dialog.setMinimumWidth(700)
        dialog.setMinimumHeight(400)
        
        layout = QVBoxLayout(dialog)
        
        # Info label
        info_label = QLabel(
            f"Based on the mapping you just entered, I found {len(suggestions)} potential mappings.\n"
            "Select the ones you want to apply:"
        )
        layout.addWidget(info_label)
        
        # Table for suggestions
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Apply", "Library", "Plex Path", "Suggested Local Path", "Status"])
        table.setRowCount(len(suggestions))
        table.horizontalHeader().setStretchLastSection(True)
        table.setColumnWidth(0, 50)
        table.setColumnWidth(2, 200)
        table.setColumnWidth(3, 200)
        
        checkboxes = []
        for i, suggestion in enumerate(suggestions):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(suggestion['confidence'] == 'high')
            checkboxes.append(checkbox)
            table.setCellWidget(i, 0, checkbox)
            
            # Library title
            table.setItem(i, 1, QTableWidgetItem(suggestion['library_title']))
            
            # Plex path
            table.setItem(i, 2, QTableWidgetItem(suggestion['plex_path']))
            
            # Suggested local path
            local_path_item = QTableWidgetItem(suggestion['suggested_local_path'])
            local_path_item.setFlags(local_path_item.flags() | Qt.ItemIsEditable)
            table.setItem(i, 3, local_path_item)
            
            # Status (will verify after dialog opens)
            status_item = QTableWidgetItem("Checking...")
            table.setItem(i, 4, status_item)
        
        layout.addWidget(table)
        
        # Buttons
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(lambda: [cb.setChecked(True) for cb in checkboxes])
        button_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(lambda: [cb.setChecked(False) for cb in checkboxes])
        button_layout.addWidget(deselect_all_btn)
        
        button_layout.addStretch()
        
        apply_btn = QPushButton("Apply Selected")
        apply_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(apply_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Verify paths asynchronously after showing dialog
        def verify_paths():
            for i, suggestion in enumerate(suggestions):
                path = table.item(i, 3).text()
                if os.path.exists(path):
                    table.item(i, 4).setText("✓ Path exists")
                    checkboxes[i].setChecked(True)
                else:
                    table.item(i, 4).setText("⚠ Path not found")
                    checkboxes[i].setChecked(False)
        
        # Use QTimer to verify paths after dialog is visible
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, verify_paths)
        
        # Show dialog
        result = dialog.exec()
        
        if result == QDialog.Accepted:
            # Apply selected mappings
            applied_count = 0
            for i, suggestion in enumerate(suggestions):
                if checkboxes[i].isChecked():
                    local_path = table.item(i, 3).text().strip()
                    if local_path:
                        # Update the table directly
                        row = suggestion['row']
                        mapped_path_item = self.libraries_table.item(row, 6)
                        if mapped_path_item:
                            self._suppress_item_changed = True
                            mapped_path_item.setText(local_path)
                            self._suppress_item_changed = False
                            
                            # Update stored data
                            data = mapped_path_item.data(Qt.UserRole)
                            if data:
                                data['old_path'] = local_path
                                mapped_path_item.setData(Qt.UserRole, data)
                            
                            applied_count += 1
                            print(f"✓ Applied mapping for {suggestion['library_title']}")
            
            if applied_count > 0:
                print(f"✓ Successfully applied {applied_count} mapping(s)")
    
    def _auto_populate_path_mappings(self, libraries):
        """Auto-populate path mappings for discovered libraries."""
        # Note: Path mappings are now handled inline in the libraries table
        # The Plex paths are already set in the table during library discovery
        pass
    
    def _load_existing_libraries_from_db(self):
        """Load existing libraries from database."""
        try:
            # This would need to integrate with the actual database
            # For now, just log the action
            print("Loading existing libraries from database...")
            # TODO: Implement actual database load
            # For now, show empty table
            self.libraries_table.setRowCount(0)
        except Exception as e:
            print(f"Error loading existing libraries from database: {e}")
    
    def _save_discovered_libraries_to_db(self, libraries):
        """Save discovered libraries to database using API."""
        try:
            # Get the API instance
            from retrovue.core.api import get_api
            api = get_api()
            
            # First, we need to ensure the server exists in the database
            # For now, we'll store the libraries in the config and save them when the dialog is saved
            # This is a limitation of the current architecture - we need a server ID
            
            # Convert libraries to the format expected by the API
            library_data = []
            for library in libraries:
                # Extract library path from location data
                plex_path = None
                if hasattr(library, 'location') and library.location and len(library.location) > 0:
                    plex_path = library.location[0].get('path', '')
                else:
                    # Generate default path if no location data
                    library_name = library.title.lower().replace(" ", "").replace("-", "")
                    plex_path = f'/media/{library_name}'
                
                library_data.append({
                    'key': library.key,
                    'title': library.title,
                    'type': library.type,
                    'agent': getattr(library, 'agent', ''),
                    'plex_path': plex_path,
                    'sync_enabled': True  # Default to enabled
                })
            
            # Store discovered libraries for later saving
            self._discovered_libraries = library_data
            
            print(f"Prepared {len(library_data)} discovered libraries for saving:")
            for lib_data in library_data:
                print(f"  - {lib_data['title']} ({lib_data['type']}) - Key: {lib_data['key']}")
                
        except Exception as e:
            print(f"Error preparing discovered libraries: {e}")
    
    def _save_path_mapping_to_db(self, library_data, plex_path, local_path):
        """Save path mapping to database."""
        try:
            # This would need to integrate with the actual database
            # For now, just log the action
            print(f"Saving path mapping to database: {library_data.get('title')} -> {plex_path} -> {local_path}")
            # TODO: Implement actual database save
        except Exception as e:
            print(f"Error saving path mapping to database: {e}")
    
    def _remove_path_mapping_from_db(self, library_data):
        """Remove path mapping from database."""
        try:
            # This would need to integrate with the actual database
            # For now, just log the action
            print(f"Removing path mapping from database: {library_data.get('title')}")
            # TODO: Implement actual database removal
        except Exception as e:
            print(f"Error removing path mapping from database: {e}")
    
    def _save_config(self):
        """Save configuration."""
        # Validate required fields
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        token = self.token_input.text().strip()
        
        # Check for missing required fields
        missing_fields = []
        if not name:
            missing_fields.append("Name")
        if not url:
            missing_fields.append("URL")
        if not token:
            missing_fields.append("Token")
        
        if missing_fields:
            QMessageBox.warning(self, "Missing Information", f"Please enter: {', '.join(missing_fields)}")
            return
        
        # Use discovered libraries if available, otherwise collect from table
        if hasattr(self, '_discovered_libraries') and self._discovered_libraries:
            libraries = self._discovered_libraries
            # Update sync status from table
            for i, lib in enumerate(libraries):
                if i < self.libraries_table.rowCount():
                    sync_checkbox = self.libraries_table.cellWidget(i, 3)
                    if sync_checkbox:
                        lib['sync_enabled'] = sync_checkbox.isChecked()
        else:
            # Fallback: collect from table
            libraries = []
            for row in range(self.libraries_table.rowCount()):
                name_item = self.libraries_table.item(row, 1)  # Title column
                type_item = self.libraries_table.item(row, 2)  # Type column
                sync_checkbox = self.libraries_table.cellWidget(row, 3)
                
                if name_item and type_item:
                    libraries.append({
                        'title': name_item.text(),
                        'type': type_item.text(),
                        'sync_enabled': sync_checkbox.isChecked() if sync_checkbox else False
                    })
        
        # Collect path mappings from libraries table
        path_mappings = []
        for row in range(self.libraries_table.rowCount()):
            plex_path_item = self.libraries_table.item(row, 5)  # Plex Path column
            local_path_item = self.libraries_table.item(row, 6)  # Mapped Path column
            
            if plex_path_item and local_path_item:
                plex_path = plex_path_item.text().strip()
                local_path = local_path_item.text().strip()
                
                if plex_path and local_path:
                    path_mappings.append({
                        'plex_path': plex_path,
                        'local_path': local_path
                    })
        
        # Create configuration
        config = {
            'name': name,
            'url': url,
            'token': token,
            'libraries': libraries,
            'path_mappings': path_mappings
        }
        
        # Save libraries to database if we have discovered libraries
        if hasattr(self, '_discovered_libraries') and self._discovered_libraries:
            try:
                # Get the API instance
                from retrovue.core.api import get_api
                api = get_api()
                
                # First, we need to ensure the server exists in the database
                # For now, we'll add the server if it doesn't exist
                # This is a workaround for the current architecture limitation
                
                # Try to find existing server by URL
                existing_servers = api.list_servers()
                server_id = None
                
                for server in existing_servers:
                    if server.get('base_url') == url:
                        server_id = server['id']
                        break
                
                # If no existing server, create one
                if not server_id:
                    server_id = api.add_server(name, url, token)
                    print(f"Created new server with ID: {server_id}")
                else:
                    print(f"Using existing server with ID: {server_id}")
                
                # Now save the libraries using the API (which calls CLI)
                print(f"Saving {len(self._discovered_libraries)} libraries to database...")
                
                # Use the API's discover_libraries method which calls the CLI
                for progress in api.discover_libraries(server_id, "plex"):
                    if progress.get('stage') == 'progress':
                        print(f"CLI: {progress.get('msg')}")
                    elif progress.get('stage') == 'complete':
                        print(f"Library discovery complete: {progress.get('msg')}")
                    elif progress.get('stage') == 'error':
                        print(f"Error: {progress.get('msg')}")
                        raise Exception(progress.get('msg'))
                
                print("Libraries saved to database successfully via CLI!")
                
            except Exception as e:
                print(f"Error saving libraries to database: {e}")
                # Continue with saving the config even if database save fails
                QMessageBox.warning(self, "Database Save Warning", 
                                  f"Libraries were discovered but couldn't be saved to database: {e}")
        
        # Store config and emit signal
        self.config = config
        self.config_saved.emit(config)
        self.accept()
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        return self.config
