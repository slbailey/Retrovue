"""
Schedules Management Page - Placeholder UI for Phase 8

This page provides a UI for managing sync schedules (create, edit, delete)
and viewing schedule execution history.

Current Status: PLACEHOLDER - Backend not yet implemented
Future: Will connect to src/retrovue/core/scheduling/manager.py
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QGroupBox,
    QTextEdit, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class SchedulesPage(QWidget):
    """
    Schedules management page with two subtabs:
    1. Schedules: Create and manage sync schedules
    2. History: View past schedule executions
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self._build_ui()
    
    def _build_ui(self):
        """Build the main UI structure."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Create tab widget for Schedules and History
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_schedules_tab(), "Schedules")
        self.tabs.addTab(self._create_history_tab(), "History")
        
        layout.addWidget(self.tabs)
    
    def _create_schedules_tab(self):
        """Create the schedules management tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Header with Add button
        header_layout = QHBoxLayout()
        
        header_label = QLabel("Sync Schedules")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        self.add_schedule_btn = QPushButton("➕ Add Schedule")
        self.add_schedule_btn.clicked.connect(self._add_schedule)
        self.add_schedule_btn.setToolTip("Create a new sync schedule (coming soon)")
        header_layout.addWidget(self.add_schedule_btn)
        
        layout.addLayout(header_layout)
        
        # Schedules table
        schedules_group = QGroupBox("Configured Schedules")
        schedules_layout = QVBoxLayout()
        
        self.schedules_table = QTableWidget()
        self.schedules_table.setColumnCount(7)
        self.schedules_table.setHorizontalHeaderLabels([
            "Name", "Server", "Library", "Frequency", "Next Run", "Enabled", "Actions"
        ])
        self.schedules_table.horizontalHeader().setStretchLastSection(False)
        self.schedules_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.schedules_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.schedules_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.schedules_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.schedules_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.schedules_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.schedules_table.setColumnWidth(6, 150)
        
        # Show empty state message
        self.schedules_table.setRowCount(1)
        empty_msg = QTableWidgetItem("No schedules configured yet. Click 'Add Schedule' to create your first one.")
        empty_msg.setFlags(Qt.ItemIsEnabled)
        empty_msg.setTextAlignment(Qt.AlignCenter)
        self.schedules_table.setItem(0, 0, empty_msg)
        self.schedules_table.setSpan(0, 0, 1, 7)
        
        schedules_layout.addWidget(self.schedules_table)
        schedules_group.setLayout(schedules_layout)
        layout.addWidget(schedules_group)
        
        # Info message
        info_layout = QHBoxLayout()
        info_label = QLabel("ℹ️ <i>Scheduling backend is not yet implemented. This is a placeholder for future functionality.</i>")
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        layout.addLayout(info_layout)
        
        return tab
    
    def _create_history_tab(self):
        """Create the schedule history tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Header
        header_label = QLabel("Schedule Execution History")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # History table
        history_group = QGroupBox("Past Executions")
        history_layout = QVBoxLayout()
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "Schedule", "Server", "Library", "Start Time", "Items Synced", "Errors", "Status"
        ])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        
        # Show empty state message
        self.history_table.setRowCount(1)
        empty_msg = QTableWidgetItem("No schedule executions yet. History will appear here after schedules run.")
        empty_msg.setFlags(Qt.ItemIsEnabled)
        empty_msg.setTextAlignment(Qt.AlignCenter)
        self.history_table.setItem(0, 0, empty_msg)
        self.history_table.setSpan(0, 0, 1, 7)
        
        history_layout.addWidget(self.history_table)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        # Log viewer
        log_group = QGroupBox("Execution Log")
        log_layout = QVBoxLayout()
        
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setPlaceholderText("Select a schedule execution above to view detailed logs...")
        self.log_viewer.setMaximumHeight(150)
        
        log_layout.addWidget(self.log_viewer)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Info message
        info_layout = QHBoxLayout()
        info_label = QLabel("ℹ️ <i>Schedule execution history will be available after the scheduling backend is implemented.</i>")
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        layout.addLayout(info_layout)
        
        return tab
    
    def _add_schedule(self):
        """Show dialog for adding a new schedule (placeholder)."""
        QMessageBox.information(
            self,
            "Feature Coming Soon",
            "<b>Scheduling Backend Not Yet Implemented</b><br><br>"
            "The scheduling feature is planned for a future release. You will be able to:<br><br>"
            "• Create sync schedules with cron expressions or simple intervals<br>"
            "• Choose which server and library to sync<br>"
            "• Set sync options (dry run, limits, content types)<br>"
            "• Enable/disable schedules<br>"
            "• View execution history and logs<br><br>"
            "<i>For now, use the 'Importers' tab to manually sync your content.</i>"
        )

