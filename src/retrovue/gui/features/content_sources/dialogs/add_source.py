"""
Add Content Source Dialog

This dialog allows users to add a new content source by selecting the type
and configuring the specific settings for that source type.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QWidget, QMessageBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from retrovue.content_sources.registry import registry


class AddSourceDialog(QDialog):
    """Dialog for adding a new content source."""
    
    source_added = Signal(dict)  # Emitted when a source is successfully added
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Content Source")
        self.setModal(True)
        self.resize(400, 300)
        
        # Store the selected source type and config widget
        self.selected_source_type = None
        self.config_widget = None
        
        self._setup_ui()
        self._populate_source_types()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Select Content Source Type")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Description
        desc = QLabel("Choose the type of content source you want to add:")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Source type list
        self.source_list = QListWidget()
        self.source_list.itemDoubleClicked.connect(self._on_source_selected)
        layout.addWidget(self.source_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self._on_next_clicked)
        self.next_button.setEnabled(False)
        button_layout.addWidget(self.next_button)
        
        layout.addLayout(button_layout)
        
        # Connect selection change
        self.source_list.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _populate_source_types(self):
        """Populate the source type list with available content sources."""
        try:
            sources = registry.list_sources()
            for source in sources:
                item = QListWidgetItem(source.name)
                item.setData(Qt.UserRole, source.source_type)
                item.setToolTip(f"Type: {source.source_type}\nCapabilities: {', '.join([cap.value for cap in source.capabilities])}")
                self.source_list.addItem(item)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load content sources: {e}")
    
    def _on_selection_changed(self):
        """Handle selection change."""
        has_selection = len(self.source_list.selectedItems()) > 0
        self.next_button.setEnabled(has_selection)
    
    def _on_source_selected(self, item):
        """Handle double-click on source item."""
        self._open_config_dialog(item)
    
    def _on_next_clicked(self):
        """Handle Next button click."""
        selected_items = self.source_list.selectedItems()
        if selected_items:
            self._open_config_dialog(selected_items[0])
    
    def _open_config_dialog(self, item):
        """Open the configuration dialog for the selected source type."""
        source_type = item.data(Qt.UserRole)
        if not source_type:
            return
            
        try:
            # Get the content source instance
            source = registry.get_source(source_type)
            if not source:
                QMessageBox.warning(self, "Error", f"Content source type '{source_type}' not found")
                return
            
            # Create configuration dialog
            config_dialog = source.create_config_dialog(self)
            if config_dialog and config_dialog.exec() == QDialog.Accepted:
                # Get configuration from the dialog
                config = config_dialog.get_config()
                if config:
                    # Emit signal with source data
                    source_data = {
                        'type': source_type,
                        'name': config.get('name', ''),
                        'config': config
                    }
                    self.source_added.emit(source_data)
                    self.accept()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open configuration dialog: {e}")