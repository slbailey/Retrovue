"""
Content Sources management page.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox, QGroupBox, QLabel, QDialog
)
from PySide6.QtCore import Qt, Signal
from typing import Dict, Any, List
from retrovue.content_sources.registry import registry
from retrovue.core.api import get_api
from .dialogs.add_source import AddSourceDialog
from .dialogs.modify_source import ModifySourceDialog


class ContentSourcesPage(QWidget):
    """Main content sources management page."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.api = get_api()
        self._build_ui()
        self._load_content_sources()
    
    def _build_ui(self):
        """Build the content sources UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header
        header_group = QGroupBox("Content Sources")
        header_layout = QVBoxLayout()
        
        header_label = QLabel("Manage your content sources. Add Plex servers, Jellyfin servers, or file system directories to import content into your unified library.")
        header_label.setWordWrap(True)
        header_layout.addWidget(header_label)
        
        header_group.setLayout(header_layout)
        layout.addWidget(header_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add Content Source")
        self.add_btn.clicked.connect(self._add_content_source)
        self.add_btn.setToolTip("Add a new content source (Plex, Jellyfin, or File System)")
        
        self.modify_btn = QPushButton("Modify")
        self.modify_btn.clicked.connect(self._modify_content_source)
        self.modify_btn.setToolTip("Modify selected content source")
        self.modify_btn.setEnabled(False)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self._delete_content_source)
        self.delete_btn.setToolTip("Delete selected content source")
        self.delete_btn.setEnabled(False)
        
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.modify_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Content sources table
        self.sources_table = QTableWidget()
        self.sources_table.setColumnCount(5)
        self.sources_table.setHorizontalHeaderLabels([
            "Name", "Type", "Status", "Libraries", "Actions"
        ])
        
        # Configure table
        self.sources_table.horizontalHeader().setStretchLastSection(True)
        self.sources_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.sources_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.sources_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.sources_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        # Connect selection change
        self.sources_table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        
        layout.addWidget(self.sources_table)
    
    def _load_content_sources(self):
        """Load content sources from API."""
        try:
            sources = self.api.list_content_sources()
            self.sources_table.setRowCount(len(sources))
            
            for i, source in enumerate(sources):
                # Name
                self.sources_table.setItem(i, 0, QTableWidgetItem(source['name']))
                
                # Type
                source_type = source['source_type'].title()
                self.sources_table.setItem(i, 1, QTableWidgetItem(source_type))
                
                # Status
                status = source['status'].title()
                self.sources_table.setItem(i, 2, QTableWidgetItem(status))
                
                # Libraries count
                libraries = source['config'].get('libraries', [])
                libraries_count = len([lib for lib in libraries if lib.get('sync_enabled', False)])
                self.sources_table.setItem(i, 3, QTableWidgetItem(f"{libraries_count} libraries"))
                
                # Actions (placeholder for now)
                self.sources_table.setItem(i, 4, QTableWidgetItem("Configure"))
                
                # Store source ID in the row for later use
                self.sources_table.item(i, 0).setData(Qt.UserRole, source['id'])
            
            # Add placeholder if no sources
            if len(sources) == 0:
                self.sources_table.setRowCount(1)
                self.sources_table.setItem(0, 0, QTableWidgetItem("No content sources configured"))
                self.sources_table.setItem(0, 1, QTableWidgetItem(""))
                self.sources_table.setItem(0, 2, QTableWidgetItem(""))
                self.sources_table.setItem(0, 3, QTableWidgetItem(""))
                self.sources_table.setItem(0, 4, QTableWidgetItem("Click 'Add Content Source' to get started"))
                
        except Exception as e:
            QMessageBox.critical(self, "API Error", f"Failed to load content sources: {e}")
            self.sources_table.setRowCount(0)
    
    def _on_selection_changed(self):
        """Handle table selection change."""
        has_selection = len(self.sources_table.selectedItems()) > 0
        self.modify_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def _add_content_source(self):
        """Add a new content source."""
        dialog = AddSourceDialog(self)
        dialog.source_added.connect(self._on_source_added)
        dialog.exec()
    
    def _on_source_added(self, source_data):
        """Handle source added signal."""
        try:
            # Save via API
            source_id = self.api.add_content_source(
                name=source_data['name'],
                source_type=source_data['type'],
                config=source_data['config']
            )
            
            # Reload the table
            self._load_content_sources()
            # Success - new source is visible in the table, no need for message box
            
        except Exception as e:
            QMessageBox.critical(self, "API Error", f"Failed to save content source: {e}")
    
    def _modify_content_source(self):
        """Modify selected content source."""
        current_row = self.sources_table.currentRow()
        if current_row < 0:
            return
        
        # Get source ID from the row
        name_item = self.sources_table.item(current_row, 0)
        if not name_item:
            return
        
        source_id = name_item.data(Qt.UserRole)
        if not source_id:
            return
        
        try:
            # Load existing config via API
            source = self.api.get_content_source(source_id)
            if not source:
                QMessageBox.warning(self, "Error", "Content source not found")
                return
            
            config = source['config']
            config['name'] = source['name']
            config['type'] = source['source_type']
            
            # Get the content source type and open its configuration dialog directly
            source_type = config.get('type', 'plex')
            source = registry.get_source(source_type)
            if source:
                config_dialog = source.create_config_dialog(self, config)
                if config_dialog and config_dialog.exec() == QDialog.Accepted:
                    # Get updated configuration
                    updated_config = config_dialog.get_config()
                    if updated_config:
                        # Handle the modification
                        self._on_source_modified({
                            'type': source_type,
                            'name': updated_config.get('name', ''),
                            'config': updated_config
                        })
            
        except Exception as e:
            QMessageBox.critical(self, "API Error", f"Failed to load content source: {e}")
    
    def _on_source_modified(self, source_data):
        """Handle source modified signal."""
        try:
            # Get source ID from current selection
            current_row = self.sources_table.currentRow()
            name_item = self.sources_table.item(current_row, 0)
            source_id = name_item.data(Qt.UserRole)
            
            # Update via API
            success = self.api.update_content_source(
                source_id=source_id,
                name=source_data['name'],
                config=source_data['config']
            )
            
            if success:
                self._load_content_sources()
                # Success - changes are visible in the table, no need for message box
            else:
                QMessageBox.warning(self, "Update Failed", "Failed to update content source")
                
        except Exception as e:
            QMessageBox.critical(self, "API Error", f"Failed to update content source: {e}")
    
    def _delete_content_source(self):
        """Delete selected content source."""
        current_row = self.sources_table.currentRow()
        if current_row < 0:
            return
        
        name_item = self.sources_table.item(current_row, 0)
        if not name_item:
            return
        
        name = name_item.text()
        source_id = name_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, 
            "Delete Content Source",
            f"Are you sure you want to delete '{name}'?\n\nThis will also delete all content imported from this source.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Delete via API
                success = self.api.delete_content_source(source_id)
                if success:
                    self._load_content_sources()
                    QMessageBox.information(self, "Content Source Deleted", f"Deleted {name} successfully")
                else:
                    QMessageBox.warning(self, "Delete Failed", "Failed to delete content source")
                    
            except Exception as e:
                QMessageBox.critical(self, "API Error", f"Failed to delete content source: {e}")
