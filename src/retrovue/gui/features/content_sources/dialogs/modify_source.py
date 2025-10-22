"""
Modify content source dialog.

This dialog allows users to modify an existing content source configuration.
"""

from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtCore import Signal
from typing import Dict, Any
from retrovue.content_sources.registry import registry


class ModifySourceDialog(QDialog):
    """Dialog for modifying an existing content source."""
    
    source_modified = Signal(dict)  # Emitted when a source is successfully modified
    
    def __init__(self, parent=None, config: Dict[str, Any] = None):
        super().__init__(parent)
        self.config = config or {}
        # Don't set window title or modal - this dialog should be invisible
        
        # Get the source type from config
        source_type = self.config.get('type', 'plex')
        
        try:
            # Get the content source instance
            source = registry.get_source(source_type)
            if not source:
                QMessageBox.warning(self, "Error", f"Content source type '{source_type}' not found")
                return
            
            # Create configuration dialog with existing config
            config_dialog = source.create_config_dialog(self, self.config)
            if config_dialog:
                
                # Show the dialog
                if config_dialog.exec() == QDialog.Accepted:
                    # Get updated configuration
                    updated_config = config_dialog.get_config()
                    if updated_config:
                        # Emit signal with updated source data
                        source_data = {
                            'type': source_type,
                            'name': updated_config.get('name', ''),
                            'config': updated_config
                        }
                        self.source_modified.emit(source_data)
                        self.accept()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open configuration dialog: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """Get the configuration."""
        return getattr(self, 'config', {})