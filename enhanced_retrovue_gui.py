"""
Enhanced Retrovue GUI - Full library and content management.
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTextEdit, QLineEdit, QGroupBox, 
    QFormLayout, QMessageBox, QProgressBar, QCheckBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QComboBox, QSpinBox,
    QHeaderView, QAbstractItemView, QSplitter, QMenu, QFileDialog, QDialog,
    QStyledItemDelegate
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QEvent
from PySide6.QtGui import QFont


class MappedPathDelegate(QStyledItemDelegate):
    """Custom delegate for Mapped Path column to handle Delete key properly."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
    
    def createEditor(self, parent, option, index):
        """Create editor and install event filter."""
        editor = QLineEdit(parent)
        editor.setFrame(False)
        # Remove margins and padding for perfect alignment
        editor.setContentsMargins(0, 0, 0, 0)
        editor.setStyleSheet("QLineEdit { padding: 0px; margin: 0px; }")
        if self.main_window:
            editor.installEventFilter(self.main_window)
        return editor
    
    def updateEditorGeometry(self, editor, option, index):
        """Position editor to exactly match the cell."""
        # Use the exact cell rect, no adjustments
        editor.setGeometry(option.rect)
    
    def setEditorData(self, editor, index):
        """Set the editor's initial data from the model."""
        text = index.model().data(index, Qt.EditRole)
        editor.setText(text if text else "")
        editor.selectAll()  # Select all text when editor opens
    
    def setModelData(self, editor, model, index):
        """Save editor data back to the model."""
        model.setData(index, editor.text(), Qt.EditRole)


class CommandWorker(QThread):
    """Worker thread for running CLI commands."""
    output = Signal(str)
    finished = Signal(bool, str)
    
    def __init__(self, command, description="", stream_output=False):
        super().__init__()
        self.command = command
        self.description = description
        self.stream_output = stream_output
        
    def run(self):
        try:
            if self.stream_output:
                # For long-running commands, stream output in real-time
                process = subprocess.Popen(
                    self.command, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    text=True, 
                    cwd=os.getcwd(),
                    bufsize=1,
                    universal_newlines=True
                )
                
                output_lines = []
                while True:
                    line = process.stdout.readline()
                    if line:
                        self.output.emit(line.rstrip())
                        output_lines.append(line)
                    elif process.poll() is not None:
                        break
                
                # Get any remaining output
                remaining = process.stdout.read()
                if remaining:
                    for line in remaining.splitlines():
                        self.output.emit(line.rstrip())
                        output_lines.append(line)
                
                full_output = ''.join(output_lines)
                self.finished.emit(process.returncode == 0, full_output)
            else:
                # For quick commands, capture all output at once
                result = subprocess.run(self.command, capture_output=True, text=True, cwd=os.getcwd())
                
                if result.returncode == 0:
                    # Combine stdout and stderr for complete output
                    full_output = result.stdout + result.stderr if result.stderr else result.stdout
                    self.finished.emit(True, full_output)
                else:
                    self.finished.emit(False, result.stderr)
                
        except Exception as e:
            self.output.emit(f"✗ Error: {str(e)}")
            self.finished.emit(False, str(e))


class EnhancedRetrovueGUI(QMainWindow):
    """Enhanced Retrovue management interface with full functionality."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Retrovue Management - Enhanced")
        self.setGeometry(100, 100, 1200, 800)
        self.worker = None
        self.db = None
        
        # Setup UI first
        self.setup_ui()
        
        # Initialize database connection after UI is set up
        try:
            import sys
            sys.path.insert(0, 'src')
            from retrovue.importers.plex.db import Db
            self.db = Db('retrovue.db')
            self.log("Database connected successfully")
        except Exception as e:
            self.log(f"Failed to connect to database: {e}")
            self.db = None
        
    def setup_ui(self):
        """Set up the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Title
        title = QLabel("Retrovue Management System")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px; color: #2c3e50;")
        layout.addWidget(title)
        
        # Status
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #7f8c8d; margin: 5px;")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Create main splitter for resizable layout
        main_splitter = QSplitter(Qt.Vertical)
        layout.addWidget(main_splitter)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        main_splitter.addWidget(self.tab_widget)
        
        # Create tabs
        self.setup_system_tab()
        self.setup_servers_tab()
        self.setup_libraries_tab()
        self.setup_sync_tab()
        self.setup_content_tab()
        # Path mappings now integrated into Libraries tab
        
        # Connect tab change signal to auto-refresh
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Output area (resizable)
        output_widget = QWidget()
        output_layout = QVBoxLayout()
        output_widget.setLayout(output_layout)
        
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setPlaceholderText("Command output will appear here...")
        output_layout.addWidget(QLabel("Output:"))
        output_layout.addWidget(self.output_area)
        
        main_splitter.addWidget(output_widget)
        
        # Set initial splitter sizes (main area gets more space)
        main_splitter.setSizes([600, 200])
        
        # Initial status check
        self.check_status()
        
    def setup_system_tab(self):
        """Set up the system status tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # System info
        info_group = QGroupBox("System Information")
        info_layout = QFormLayout()
        
        self.db_status = QLabel("Unknown")
        self.plex_status = QLabel("Unknown")
        self.content_count = QLabel("0")
        self.server_count = QLabel("0")
        
        info_layout.addRow("Database:", self.db_status)
        info_layout.addRow("Plex Connection:", self.plex_status)
        info_layout.addRow("Content Items:", self.content_count)
        info_layout.addRow("Plex Servers:", self.server_count)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.status_btn = QPushButton("Check Status")
        self.status_btn.clicked.connect(self.check_status)
        
        self.test_btn = QPushButton("Test All Systems")
        self.test_btn.clicked.connect(self.test_all_systems)
        
        button_layout.addWidget(self.status_btn)
        button_layout.addWidget(self.test_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "System Status")
        
    def setup_servers_tab(self):
        """Set up the servers management tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Server list
        self.server_table = QTableWidget()
        self.server_table.setColumnCount(4)
        self.server_table.setHorizontalHeaderLabels(["ID", "Name", "URL", "Default"])
        self.server_table.horizontalHeader().setStretchLastSection(True)
        self.server_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.server_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.server_table.customContextMenuRequested.connect(self.show_server_context_menu)
        
        layout.addWidget(QLabel("Plex Servers:"))
        layout.addWidget(self.server_table)
        
        # Note: Server addition now handled by modular GUI (retrovue/gui/features/importers/view.py)
        # Use the new Tkinter-based interface for importing from Plex
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_servers_btn = QPushButton("Refresh Servers")
        self.refresh_servers_btn.clicked.connect(self.refresh_servers)
        
        self.test_server_btn = QPushButton("Test Selected Server")
        self.test_server_btn.clicked.connect(self.test_server)
        
        button_layout.addWidget(self.refresh_servers_btn)
        button_layout.addWidget(self.test_server_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.tab_widget.addTab(tab, "Plex Servers")
        
    def setup_libraries_tab(self):
        """Set up the libraries management tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Server selection
        server_group = QGroupBox("Server Selection")
        server_layout = QHBoxLayout()
        
        self.library_server_combo = QComboBox()
        self.library_server_combo.currentTextChanged.connect(self.refresh_libraries)
        
        server_layout.addWidget(QLabel("Server:"))
        server_layout.addWidget(self.library_server_combo)
        
        self.discover_libraries_btn = QPushButton("Discover Libraries")
        self.discover_libraries_btn.clicked.connect(self.discover_libraries)
        server_layout.addWidget(self.discover_libraries_btn)
        
        self.refresh_libraries_btn = QPushButton("Refresh")
        self.refresh_libraries_btn.clicked.connect(self.refresh_libraries)
        server_layout.addWidget(self.refresh_libraries_btn)
        
        server_layout.addStretch()
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # Library list
        self.library_table = QTableWidget()
        self.library_table.setColumnCount(8)
        self.library_table.setHorizontalHeaderLabels(["Key", "Title", "Type", "Sync Enabled", "Last Sync", "Plex Path", "Mapped Path", ""])
        # Set column widths
        self.library_table.setColumnWidth(0, 40)   # ID - narrow
        self.library_table.setColumnWidth(5, 250)  # Plex Path - wide enough for paths
        self.library_table.setColumnWidth(7, 30)   # Browse button column - narrow
        self.library_table.horizontalHeader().setStretchLastSection(False)
        self.library_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)  # Mapped Path stretches
        self.library_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # Set default row height for better text alignment
        self.library_table.verticalHeader().setDefaultSectionSize(30)
        self.library_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.library_table.customContextMenuRequested.connect(self.show_library_context_menu)
        # Make Mapped Path column editable
        self.library_table.itemChanged.connect(self.on_library_table_item_changed)
        # Set custom delegate for Mapped Path column to handle Delete key
        self.library_table.setItemDelegateForColumn(6, MappedPathDelegate(self))
        
        # Flag to prevent auto-save when programmatically updating cells
        self._suppress_item_changed = False
        
        layout.addWidget(QLabel("Libraries:"))
        layout.addWidget(self.library_table)
        
        self.tab_widget.addTab(tab, "Libraries")
        
    def setup_sync_tab(self):
        """Set up the content sync tab."""
        tab = QWidget()
        main_layout = QVBoxLayout()
        tab.setLayout(main_layout)
        
        # Create splitter for sync tab (options + output)
        sync_splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(sync_splitter)
        
        # Options widget (top part)
        options_widget = QWidget()
        options_layout = QVBoxLayout()
        options_widget.setLayout(options_layout)
        
        # Sync options
        options_group = QGroupBox("Sync Options")
        form_layout = QFormLayout()
        
        self.sync_server_combo = QComboBox()
        self.sync_server_combo.currentTextChanged.connect(self.update_sync_libraries)
        
        self.sync_libraries = QLineEdit()
        self.sync_libraries.setPlaceholderText("1,2,3 (comma-separated library IDs)")
        
        self.sync_limit = QSpinBox()
        self.sync_limit.setRange(0, 10000)
        self.sync_limit.setValue(0)
        self.sync_limit.setSpecialValueText("No limit")
        
        self.dry_run_check = QCheckBox("Dry run (don't write to database)")
        
        form_layout.addRow("Server:", self.sync_server_combo)
        form_layout.addRow("Libraries:", self.sync_libraries)
        form_layout.addRow("Limit:", self.sync_limit)
        form_layout.addRow("", self.dry_run_check)
        
        options_group.setLayout(form_layout)
        options_layout.addWidget(options_group)
        
        # Sync buttons
        button_layout = QHBoxLayout()
        
        self.sync_btn = QPushButton("Start Sync")
        self.sync_btn.clicked.connect(self.start_sync)
        
        self.stop_sync_btn = QPushButton("Stop Sync")
        self.stop_sync_btn.clicked.connect(self.stop_sync)
        self.stop_sync_btn.setEnabled(False)
        
        self.test_sync_btn = QPushButton("Test Sync (Dry Run)")
        self.test_sync_btn.clicked.connect(self.test_sync)
        
        button_layout.addWidget(self.sync_btn)
        button_layout.addWidget(self.stop_sync_btn)
        button_layout.addWidget(self.test_sync_btn)
        button_layout.addStretch()
        
        options_layout.addLayout(button_layout)
        sync_splitter.addWidget(options_widget)
        
        # Sync output (resizable bottom part)
        output_widget = QWidget()
        output_layout = QVBoxLayout()
        output_widget.setLayout(output_layout)
        
        self.sync_output = QTextEdit()
        self.sync_output.setReadOnly(True)
        self.sync_output.setPlaceholderText("Sync output will appear here...")
        output_layout.addWidget(QLabel("Sync Output:"))
        output_layout.addWidget(self.sync_output)
        
        sync_splitter.addWidget(output_widget)
        
        # Set initial splitter sizes (options get more space)
        sync_splitter.setSizes([400, 300])
        
        self.tab_widget.addTab(tab, "Content Sync")
        
    def setup_content_tab(self):
        """Set up the content browser tab."""
        tab = QWidget()
        main_layout = QVBoxLayout()
        tab.setLayout(main_layout)
        
        # Create splitter for browser (filters + content)
        browser_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(browser_splitter)
        
        # Left panel - Filters and navigation
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Browse mode selection
        mode_group = QGroupBox("Browse Mode")
        mode_layout = QVBoxLayout()
        
        self.browse_mode_combo = QComboBox()
        self.browse_mode_combo.addItems([
            "All Content", "By Library", "TV Shows", "Movies", "By Genre", "Media Files"
        ])
        self.browse_mode_combo.currentTextChanged.connect(self.on_browse_mode_changed)
        mode_layout.addWidget(self.browse_mode_combo)
        
        mode_group.setLayout(mode_layout)
        left_layout.addWidget(mode_group)
        
        # Library filter
        self.library_filter_group = QGroupBox("Library Filter")
        library_filter_layout = QVBoxLayout()
        
        self.content_library_combo = QComboBox()
        self.content_library_combo.addItem("All Libraries")
        self.content_library_combo.currentTextChanged.connect(self.refresh_content)
        library_filter_layout.addWidget(self.content_library_combo)
        
        self.library_filter_group.setLayout(library_filter_layout)
        left_layout.addWidget(self.library_filter_group)
        
        # Genre filter
        self.genre_filter_group = QGroupBox("Genre Filter")
        genre_filter_layout = QVBoxLayout()
        
        self.genre_combo = QComboBox()
        self.genre_combo.addItem("All Genres")
        self.genre_combo.currentTextChanged.connect(self.refresh_content)
        genre_filter_layout.addWidget(self.genre_combo)
        
        self.genre_filter_group.setLayout(genre_filter_layout)
        left_layout.addWidget(self.genre_filter_group)
        
        # Search
        search_group = QGroupBox("Search")
        search_layout = QVBoxLayout()
        
        self.content_search = QLineEdit()
        self.content_search.setPlaceholderText("Search content...")
        self.content_search.textChanged.connect(self.refresh_content)
        search_layout.addWidget(self.content_search)
        
        search_group.setLayout(search_layout)
        left_layout.addWidget(search_group)
        
        # TV Show navigation
        self.tv_navigation_group = QGroupBox("TV Show Navigation")
        tv_nav_layout = QVBoxLayout()
        
        self.shows_combo = QComboBox()
        self.shows_combo.currentTextChanged.connect(self.on_show_selected)
        tv_nav_layout.addWidget(QLabel("Show:"))
        tv_nav_layout.addWidget(self.shows_combo)
        
        self.seasons_combo = QComboBox()
        self.seasons_combo.currentTextChanged.connect(self.on_season_selected)
        tv_nav_layout.addWidget(QLabel("Season:"))
        tv_nav_layout.addWidget(self.seasons_combo)
        
        self.tv_navigation_group.setLayout(tv_nav_layout)
        left_layout.addWidget(self.tv_navigation_group)
        
        left_layout.addStretch()
        browser_splitter.addWidget(left_panel)
        
        # Right panel - Content display
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Content table
        self.content_table = QTableWidget()
        self.content_table.setColumnCount(11)
        self.content_table.setHorizontalHeaderLabels([
            "ID", "Title", "Type", "Duration", "Year", "Show", "Library", "Rating", "Plex Path", "Mapped Path", "Play"
        ])
        self.content_table.horizontalHeader().setStretchLastSection(False)
        self.content_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.Stretch)  # Plex Path
        self.content_table.horizontalHeader().setSectionResizeMode(9, QHeaderView.Stretch)  # Mapped Path
        self.content_table.setColumnWidth(10, 60)  # Play button
        self.content_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.content_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.content_table.customContextMenuRequested.connect(self.show_content_context_menu)
        
        right_layout.addWidget(self.content_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_content_btn = QPushButton("Refresh")
        self.refresh_content_btn.clicked.connect(self.refresh_content)
        
        self.view_details_btn = QPushButton("View Details")
        self.view_details_btn.clicked.connect(self.view_content_details)
        
        self.view_files_btn = QPushButton("View Files")
        self.view_files_btn.clicked.connect(self.view_media_files)
        
        button_layout.addWidget(self.refresh_content_btn)
        button_layout.addWidget(self.view_details_btn)
        button_layout.addWidget(self.view_files_btn)
        button_layout.addStretch()
        
        right_layout.addLayout(button_layout)
        
        browser_splitter.addWidget(right_panel)
        
        # Set initial splitter sizes
        browser_splitter.setSizes([300, 700])
        
        # Initialize content
        self.current_browse_mode = "All Content"
        self.current_library_id = None
        self.current_show_id = None
        self.current_season_id = None
        
        self.tab_widget.addTab(tab, "Content Browser")
    
    def on_browse_mode_changed(self, mode):
        """Handle browse mode change."""
        self.current_browse_mode = mode
        
        # Show/hide relevant filter groups
        if mode == "TV Shows":
            self.tv_navigation_group.setVisible(True)
            self.genre_filter_group.setVisible(False)
        elif mode == "By Genre":
            self.tv_navigation_group.setVisible(False)
            self.genre_filter_group.setVisible(True)
        else:
            self.tv_navigation_group.setVisible(False)
            self.genre_filter_group.setVisible(False)
        
        # Refresh content based on new mode
        self.refresh_content()
    
    def on_show_selected(self, show_text):
        """Handle show selection for TV navigation."""
        if not show_text or show_text == "Select Show":
            self.current_show_id = None
            self.seasons_combo.clear()
            self.seasons_combo.addItem("All Seasons")
            return
        
        # Extract show ID from text (format: "ID: Title")
        try:
            show_id = int(show_text.split(":")[0])
            self.current_show_id = show_id
            self.load_seasons_for_show(show_id)
        except (ValueError, IndexError):
            self.current_show_id = None
    
    def on_season_selected(self, season_text):
        """Handle season selection for TV navigation."""
        if not season_text or season_text == "All Seasons":
            self.current_season_id = None
        else:
            # Extract season ID from text (format: "ID: Season X")
            try:
                season_id = int(season_text.split(":")[0])
                self.current_season_id = season_id
            except (ValueError, IndexError):
                self.current_season_id = None
        
        self.refresh_content()
    
    def load_seasons_for_show(self, show_id):
        """Load seasons for a specific show."""
        try:
            seasons = self.db.get_seasons(show_id)
            self.seasons_combo.clear()
            self.seasons_combo.addItem("All Seasons")
            
            for season in seasons:
                season_text = f"{season['id']}: Season {season['season_number']}"
                if season['title']:
                    season_text += f" - {season['title']}"
                season_text += f" ({season['episode_count']} episodes)"
                self.seasons_combo.addItem(season_text)
        except Exception as e:
            self.log(f"Error loading seasons: {e}")
    
    def refresh_content(self):
        """Refresh the content table based on current filters."""
        if not self.db:
            self.log("Database not available")
            return
            
        try:
            mode = self.current_browse_mode
            library_id = self.get_selected_library_id()
            search = self.content_search.text().strip() or None
            
            # Flag to determine if we're showing actual playable content
            showing_playable_content = True
            
            if mode == "All Content":
                content = self.db.get_content_items(library_id=library_id, search=search)
            elif mode == "TV Shows":
                if self.current_show_id:
                    if self.current_season_id:
                        content = self.db.get_episodes(self.current_show_id, self.current_season_id)
                    else:
                        content = self.db.get_episodes(self.current_show_id)
                else:
                    # Browsing shows - not playable content
                    content = self.db.get_shows(library_id=library_id, search=search)
                    showing_playable_content = False
            elif mode == "Movies":
                content = self.db.get_movies(library_id=library_id, search=search)
            elif mode == "By Genre":
                genre = self.genre_combo.currentText()
                if genre != "All Genres":
                    content = self.db.get_content_by_genre(genre, library_id)
                else:
                    content = self.db.get_content_items(library_id=library_id, search=search)
            elif mode == "Media Files":
                # For now, show content items that have media files
                content = self.db.get_content_items(library_id=library_id, search=search)
                content = [item for item in content if item.get('has_media_files', False)]
            else:
                content = []
            
            self.populate_content_table(content, showing_playable_content)
            
        except Exception as e:
            self.log(f"Error refreshing content: {e}")
    
    def get_selected_library_id(self):
        """Get the selected library ID from the combo box."""
        library_text = self.content_library_combo.currentText()
        if library_text == "All Libraries":
            return None
        
        try:
            # Extract library ID from text (format: "ID: Title")
            library_id = int(library_text.split(":")[0])
            return library_id
        except (ValueError, IndexError):
            return None
    
    def populate_content_table(self, content, showing_playable_content=True):
        """Populate the content table with data."""
        self.content_table.setRowCount(len(content))
        
        for row, item in enumerate(content):
            # ID
            self.content_table.setItem(row, 0, QTableWidgetItem(str(item.get('id', ''))))
            
            # Title
            title = item.get('title', '')
            self.content_table.setItem(row, 1, QTableWidgetItem(title))
            
            # Type
            kind = item.get('kind', '')
            if kind == 'episode':
                season = item.get('season_number', '')
                episode = item.get('episode_number', '')
                type_text = f"Episode S{season}E{episode}" if season and episode else "Episode"
            else:
                type_text = kind.title()
            self.content_table.setItem(row, 2, QTableWidgetItem(type_text))
            
            # Duration
            duration_ms = item.get('duration_ms', 0)
            if duration_ms:
                duration_min = duration_ms // 60000
                duration_text = f"{duration_min} min"
            else:
                duration_text = ""
            self.content_table.setItem(row, 3, QTableWidgetItem(duration_text))
            
            # Year
            year = item.get('year') or item.get('show_year', '')
            self.content_table.setItem(row, 4, QTableWidgetItem(str(year) if year else ''))
            
            # Show
            show_title = item.get('show_title', '')
            self.content_table.setItem(row, 5, QTableWidgetItem(show_title))
            
            # Library
            library_title = item.get('library_title', '')
            self.content_table.setItem(row, 6, QTableWidgetItem(library_title))
            
            # Rating
            rating = item.get('rating_code', '')
            self.content_table.setItem(row, 7, QTableWidgetItem(rating))
            
            # Only show file paths and play button for actual playable content
            if showing_playable_content:
                # Fetch media files for this content item
                try:
                    content_id = int(item.get('id', 0))
                    media_files = self.db.get_media_files(content_id) if content_id else []
                    
                    if media_files and len(media_files) > 0:
                        file_info = media_files[0]  # Use first media file
                        plex_path = file_info.get('plex_file_path', '')
                        local_path = file_info.get('local_file_path', '')
                        
                        # Plex Path
                        self.content_table.setItem(row, 8, QTableWidgetItem(plex_path))
                        
                        # Mapped Path
                        self.content_table.setItem(row, 9, QTableWidgetItem(local_path))
                        
                        # Play button
                        play_btn = QPushButton("▶ Play")
                        play_btn.setStyleSheet("QPushButton { padding: 2px 8px; }")
                        play_btn.clicked.connect(lambda checked, path=local_path: self.play_in_vlc(path))
                        self.content_table.setCellWidget(row, 10, play_btn)
                    else:
                        self.content_table.setItem(row, 8, QTableWidgetItem(""))
                        self.content_table.setItem(row, 9, QTableWidgetItem(""))
                        self.content_table.setItem(row, 10, QTableWidgetItem("No file"))
                except Exception as e:
                    self.log(f"Error fetching media files for item {item.get('id')}: {e}")
                    self.content_table.setItem(row, 8, QTableWidgetItem(""))
                    self.content_table.setItem(row, 9, QTableWidgetItem(""))
                    self.content_table.setItem(row, 10, QTableWidgetItem("Error"))
            else:
                # Not showing playable content - leave file columns empty
                self.content_table.setItem(row, 8, QTableWidgetItem(""))
                self.content_table.setItem(row, 9, QTableWidgetItem(""))
                self.content_table.setCellWidget(row, 10, None)  # Clear any existing widget
                self.content_table.setItem(row, 10, QTableWidgetItem(""))
        
        # Auto-resize columns (except stretched ones)
        for col in range(8):
            self.content_table.resizeColumnToContents(col)
    
    def show_content_context_menu(self, position):
        """Show context menu for content items."""
        if self.content_table.itemAt(position) is None:
            return
        
        menu = QMenu(self)
        
        view_details_action = menu.addAction("View Details")
        view_details_action.triggered.connect(self.view_content_details)
        
        view_files_action = menu.addAction("View Media Files")
        view_files_action.triggered.connect(self.view_media_files)
        
        menu.exec(self.content_table.mapToGlobal(position))
    
    def view_content_details(self):
        """View details for selected content item."""
        current_row = self.content_table.currentRow()
        if current_row < 0:
            return
        
        item_id = self.content_table.item(current_row, 0).text()
        if not item_id:
            return
        
        try:
            # Get content item details
            content = self.db.get_content_items()
            item = next((c for c in content if str(c['id']) == item_id), None)
            
            if not item:
                self.log(f"Content item {item_id} not found")
                return
            
            # Create details dialog
            details = QMessageBox()
            details.setWindowTitle("Content Details")
            details.setIcon(QMessageBox.Information)
            
            details_text = f"""
Title: {item.get('title', 'N/A')}
Type: {item.get('kind', 'N/A')}
Duration: {item.get('duration_ms', 0) // 60000} minutes
Rating: {item.get('rating_code', 'N/A')}
Kids Friendly: {'Yes' if item.get('is_kids_friendly') else 'No'}
Show: {item.get('show_title', 'N/A')}
Library: {item.get('library_title', 'N/A')}
Created: {item.get('created_at', 'N/A')}
Updated: {item.get('updated_at', 'N/A')}

Synopsis:
{item.get('synopsis', 'No synopsis available')}
            """.strip()
            
            details.setText(details_text)
            details.exec()
            
        except Exception as e:
            self.log(f"Error viewing content details: {e}")
    
    def view_media_files(self):
        """View media files for selected content item."""
        current_row = self.content_table.currentRow()
        if current_row < 0:
            return
        
        item_id = self.content_table.item(current_row, 0).text()
        if not item_id:
            return
        
        try:
            media_files = self.db.get_media_files(int(item_id))
            
            if not media_files:
                QMessageBox.information(self, "Media Files", "No media files found for this content item.")
                return
            
            # Create media files dialog
            dialog = QMessageBox()
            dialog.setWindowTitle("Media Files")
            dialog.setIcon(QMessageBox.Information)
            
            files_text = f"Found {len(media_files)} media file(s):\n\n"
            
            for i, file_info in enumerate(media_files, 1):
                files_text += f"{i}. {file_info.get('file_path', 'N/A')}\n"
                files_text += f"   Size: {file_info.get('size_bytes', 0) // (1024*1024)} MB\n"
                files_text += f"   Codec: {file_info.get('video_codec', 'N/A')} / {file_info.get('audio_codec', 'N/A')}\n"
                files_text += f"   Resolution: {file_info.get('width', 0)}x{file_info.get('height', 0)}\n\n"
            
            dialog.setText(files_text)
            dialog.exec()
            
        except Exception as e:
            self.log(f"Error viewing media files: {e}")
    
    def initialize_content_browser(self):
        """Initialize the content browser with data."""
        if not self.db:
            self.log("Database not available for content browser")
            return
            
        try:
            # Populate library filter
            self.content_library_combo.clear()
            self.content_library_combo.addItem("All Libraries")
            
            libraries = self.db.list_libraries()
            for library in libraries:
                library_text = f"{library['id']}: {library['title']} ({library['library_type']})"
                self.content_library_combo.addItem(library_text)
            
            # Populate genre filter
            self.genre_combo.clear()
            self.genre_combo.addItem("All Genres")
            
            genres = self.db.get_available_genres()
            for genre in genres:
                self.genre_combo.addItem(genre)
            
            # Populate shows for TV navigation
            self.shows_combo.clear()
            self.shows_combo.addItem("Select Show")
            
            shows = self.db.get_shows()
            for show in shows:
                show_text = f"{show['id']}: {show['title']}"
                if show['year']:
                    show_text += f" ({show['year']})"
                show_text += f" - {show['episode_count']} episodes"
                self.shows_combo.addItem(show_text)
            
            # Initialize seasons combo
            self.seasons_combo.clear()
            self.seasons_combo.addItem("All Seasons")
            
            # Refresh content
            self.refresh_content()
            
        except Exception as e:
            self.log(f"Error initializing content browser: {e}")
        
    def setup_mappings_tab(self):
        """Set up the path mappings tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Mapping list
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(5)
        self.mapping_table.setHorizontalHeaderLabels(["ID", "Server", "Library", "Plex Path", "Local Path"])
        self.mapping_table.horizontalHeader().setStretchLastSection(True)
        self.mapping_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.mapping_table)
        
        # Add mapping form
        form_group = QGroupBox("Add Path Mapping")
        form_layout = QFormLayout()
        
        self.mapping_server_combo = QComboBox()
        self.mapping_library_combo = QComboBox()
        self.plex_path = QLineEdit()
        self.plex_path.setPlaceholderText("/media/movies/...")
        
        # Local path with browse button
        local_path_layout = QHBoxLayout()
        self.local_path = QLineEdit()
        self.local_path.setPlaceholderText("C:\\Movies\\... or click Browse")
        self.browse_local_path_btn = QPushButton("...")
        self.browse_local_path_btn.setMaximumWidth(40)
        self.browse_local_path_btn.setToolTip("Browse for local folder")
        self.browse_local_path_btn.clicked.connect(self.browse_local_path)
        local_path_layout.addWidget(self.local_path)
        local_path_layout.addWidget(self.browse_local_path_btn)
        
        self.add_mapping_btn = QPushButton("Add Mapping")
        self.add_mapping_btn.clicked.connect(self.add_mapping)
        
        form_layout.addRow("Server:", self.mapping_server_combo)
        form_layout.addRow("Library:", self.mapping_library_combo)
        form_layout.addRow("Plex Path:", self.plex_path)
        form_layout.addRow("Local Path:", local_path_layout)
        form_layout.addRow("", self.add_mapping_btn)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_mappings_btn = QPushButton("Refresh Mappings")
        self.refresh_mappings_btn.clicked.connect(self.refresh_mappings)
        
        button_layout.addWidget(self.refresh_mappings_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.tab_widget.addTab(tab, "Path Mappings")
        
    def eventFilter(self, obj, event):
        """Handle events for editor widgets - specifically Delete key in QLineEdit."""
        # Check if this is a QLineEdit (editor) and we have a Delete/Backspace key press
        if isinstance(obj, QLineEdit) and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
                # Check if all text is selected
                if obj.hasSelectedText():
                    selected = obj.selectedText()
                    all_text = obj.text()
                    
                    # If all text is selected, clear it
                    if selected == all_text and all_text:
                        obj.clear()
                        return True  # Handled - text is now cleared
        
        # Pass the event to the base class
        return super().eventFilter(obj, event)
    
    def log(self, message: str):
        """Log a message to the output area."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.output_area.append(f"[{timestamp}] {message}")
        # Auto-scroll to bottom
        scrollbar = self.output_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def on_tab_changed(self, index):
        """Handle tab change to auto-refresh data."""
        tab_name = self.tab_widget.tabText(index)
        
        if tab_name == "Plex Servers":
            self.log("Auto-refreshing servers list...")
            self.refresh_servers()
        elif tab_name == "Libraries":
            self.log("Auto-refreshing libraries list...")
            self.refresh_libraries()
        elif tab_name == "Path Mappings":
            self.log("Auto-refreshing mappings list...")
            self.refresh_mappings()
        elif tab_name == "Content Browser":
            self.log("Initializing content browser...")
            self.initialize_content_browser()
        
    def run_command(self, command, description="", stream_output=False, silent=False):
        """Run a command in a worker thread."""
        if self.worker and self.worker.isRunning():
            if not silent:
                self.log("Another command is already running, please wait...")
            return
            
        self.worker = CommandWorker(command, description, stream_output)
        self.worker.output.connect(self.log)
        self.worker.finished.connect(self.command_finished)
        self.worker.start()
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_label.setText("Running command...")
        
    def command_finished(self, success, output):
        """Handle command completion."""
        self.progress_bar.setVisible(False)
        self.status_label.setText("Ready")
        
        if success:
            # Update relevant displays based on the command
            if "servers list" in " ".join(self.worker.command):
                self.parse_servers_output(output)
            elif "servers add" in " ".join(self.worker.command):
                self.log("Server added successfully! Refreshing list...")
                # Auto-refresh servers list after adding
                self.refresh_servers()
            elif "servers delete" in " ".join(self.worker.command):
                self.log("Server deleted successfully! Refreshing all tabs...")
                # Auto-refresh servers list after deleting
                self.refresh_servers()
                # Clear the library table since libraries were cascade deleted
                self.log("Cascade delete: clearing libraries...")
                self.library_table.setRowCount(0)
                self.library_server_combo.clear()
                # Clear content browser since all content was cascade deleted
                self.log("Cascade delete: clearing content browser...")
                if hasattr(self, 'content_table'):
                    self.content_table.setRowCount(0)
                if self.db:
                    self.refresh_content()
                # Clear path mappings since they were cascade deleted
                self.log("Cascade delete: clearing path mappings...")
                # Note: Path mappings are now shown inline in libraries table, no separate table to clear
                # Clear sync server combo boxes
                if hasattr(self, 'sync_server_combo'):
                    self.sync_server_combo.clear()
                if hasattr(self, 'mapping_server_combo'):
                    self.mapping_server_combo.clear()
                if hasattr(self, 'mapping_library_combo'):
                    self.mapping_library_combo.clear()
            elif "libraries list" in " ".join(self.worker.command):
                self.parse_libraries_output(output)
            elif "libraries sync" in " ".join(self.worker.command):
                self.log("Libraries discovered successfully! Refreshing list...")
                # Auto-refresh libraries list after discovery
                self.refresh_libraries()
            elif "sync enable" in " ".join(self.worker.command) or "sync disable" in " ".join(self.worker.command):
                self.log("Library sync updated successfully! Refreshing list...")
                # Auto-refresh libraries list after sync toggle
                self.refresh_libraries()
            elif "mappings list" in " ".join(self.worker.command):
                self.parse_mappings_output(output)
            elif "mappings add" in " ".join(self.worker.command):
                self.log("Mapping added successfully! Refreshing library list...")
                # Auto-refresh libraries list to show new mapping
                self.refresh_libraries()
                # Also refresh mappings if the tab exists
                if hasattr(self, 'refresh_mappings'):
                    self.refresh_mappings()
            elif "ingest run" in " ".join(self.worker.command):
                self.sync_output.append(output)
                # Auto-scroll sync output to bottom
                scrollbar = self.sync_output.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
                # Auto-refresh content after sync
                self.log("Sync completed! You can now browse content in the Content Browser tab.")
        else:
            self.log(f"Command failed: {output}")
            
    def check_status(self):
        """Check system status."""
        self.log("=== CHECKING SYSTEM STATUS ===")
        
        # Check database
        if os.path.exists('retrovue.db'):
            self.db_status.setText("✓ Connected")
            self.db_status.setStyleSheet("color: green")
        else:
            self.db_status.setText("✗ Not found")
            self.db_status.setStyleSheet("color: red")
            
        # Get basic stats
        self.run_command([
            sys.executable, "cli/plex_sync.py", "servers", "list"
        ], "Check system status")
        
    def test_all_systems(self):
        """Test all system components."""
        self.log("=== TESTING ALL SYSTEMS ===")
        
        # Test database
        if os.path.exists('retrovue.db'):
            self.log("✓ Database file exists")
        else:
            self.log("✗ Database file not found")
            
        # Test servers
        self.run_command([
            sys.executable, "cli/plex_sync.py", "servers", "list"
        ], "Test servers")
        
    def refresh_servers(self):
        """Refresh the servers list."""
        self.run_command([
            sys.executable, "cli/plex_sync.py", "servers", "list"
        ], "Refresh servers")
        
    def discover_libraries(self):
        """Discover and import libraries from the selected server."""
        server_id = self.library_server_combo.currentData()
        if server_id is None:
            QMessageBox.warning(self, "Warning", "Please select a server first")
            return
            
        server_name = self.library_server_combo.currentText()
        self.log(f"=== DISCOVERING LIBRARIES FROM: {server_name} ===")
        self.run_command([
            sys.executable, "cli/plex_sync.py", "libraries", "sync",
            "--server-id", str(server_id),
            "--disable-all"
        ], f"Discover libraries from {server_name}")
        
    def refresh_mappings(self):
        """Refresh the mappings list."""
        self.run_command([
            sys.executable, "cli/plex_sync.py", "mappings", "list"
        ], "Refresh mappings")
        
    def parse_servers_output(self, output):
        """Parse servers list output and update table."""
        lines = output.strip().split('\n')
        servers = []
        
        # Look for the table data lines
        in_table = False
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and info messages
            if not line or line.startswith('INFO:') or line.startswith('[OK]'):
                continue
                
            # Check if we're in the table section
            if 'ID' in line and 'Name' in line and 'Base URL' in line:
                in_table = True
                continue
            elif '---' in line:
                continue
            elif in_table and line and not line.startswith('INFO:'):
                # Parse table row - this is space-separated, not pipe-separated
                parts = line.split()
                if len(parts) >= 4:
                    # ID, Name (may be multiple words), URL, Default
                    server_id = parts[0]
                    default = parts[-1]
                    url = parts[-2]
                    
                    # Name is everything between ID and URL
                    name_parts = parts[1:-2]
                    name = ' '.join(name_parts)
                    
                    servers.append({
                        'id': server_id,
                        'name': name,
                        'url': url,
                        'default': default
                    })
            elif in_table and not line:
                # End of table
                break
        
        self.log(f"Parsed {len(servers)} servers from output")
        for server in servers:
            self.log(f"  - {server['id']}: {server['name']} ({server['url']})")
            
        self.server_table.setRowCount(len(servers))
        for i, server in enumerate(servers):
            self.server_table.setItem(i, 0, QTableWidgetItem(server['id']))
            self.server_table.setItem(i, 1, QTableWidgetItem(server['name']))
            self.server_table.setItem(i, 2, QTableWidgetItem(server['url']))
            self.server_table.setItem(i, 3, QTableWidgetItem(server['default']))
            
        # Auto-resize columns to content
        self.server_table.resizeColumnsToContents()
            
        # Update combo boxes
        self.library_server_combo.clear()
        self.sync_server_combo.clear()
        
        for server in servers:
            display_text = f"{server['name']} ({server['id']})"
            self.library_server_combo.addItem(display_text, server['id'])
            self.sync_server_combo.addItem(display_text, server['id'])
            
        self.server_count.setText(str(len(servers)))
        
    # add_server() and clear_server_form() removed - functionality moved to modular GUI
    # See: retrovue/gui/features/importers/view.py
        
    def show_server_context_menu(self, position):
        """Show context menu for server table."""
        item = self.server_table.itemAt(position)
        if item is None:
            return
            
        # Get the server ID from the first column
        row = item.row()
        server_id = self.server_table.item(row, 0).text()
        server_name = self.server_table.item(row, 1).text()
        
        # Create context menu
        menu = QMenu(self)
        
        # Delete action
        delete_action = menu.addAction(f"Delete '{server_name}'")
        delete_action.triggered.connect(lambda: self.delete_server(server_id, server_name))
        
        # Test action
        test_action = menu.addAction(f"Test '{server_name}'")
        test_action.triggered.connect(lambda: self.test_server_by_id(server_id))
        
        # Show menu
        menu.exec_(self.server_table.mapToGlobal(position))
        
    def delete_server(self, server_id, server_name):
        """Delete a server."""
        reply = QMessageBox.question(
            self, 
            "Delete Server", 
            f"Are you sure you want to delete server '{server_name}' (ID: {server_id})?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.log(f"=== DELETING SERVER: {server_name} (ID: {server_id}) ===")
            self.run_command([
                sys.executable, "cli/plex_sync.py", "servers", "delete",
                "--server-id", server_id
            ], f"Delete server: {server_name}")
            
    def test_server_by_id(self, server_id):
        """Test a specific server by ID."""
        self.log(f"=== TESTING SERVER ID: {server_id} ===")
        self.run_command([
            sys.executable, "cli/plex_sync.py", "libraries", "list",
            "--server-id", server_id
        ], f"Test server ID: {server_id} (via libraries list)")
        
    def test_server(self):
        """Test the selected server."""
        current_row = self.server_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Warning", "Please select a server to test")
            return
            
        server_id = self.server_table.item(current_row, 0).text()
        server_name = self.server_table.item(current_row, 1).text()
        
        self.log(f"=== TESTING SERVER: {server_name} (ID: {server_id}) ===")
        self.run_command([
            sys.executable, "cli/plex_sync.py", "libraries", "list",
            "--server-id", server_id
        ], f"Test server: {server_name} (via libraries list)")
        
    def refresh_libraries(self):
        """Refresh the libraries list directly from database."""
        if not self.db:
            self.log("Cannot refresh libraries: no database connection")
            return
        
        server_id = self.library_server_combo.currentData()
        if server_id is None:
            self.log("No server selected")
            return
        
        try:
            # Get libraries from database
            libraries = self.db.list_libraries(server_id)
            
            self.log(f"Loaded {len(libraries)} libraries from database")
            
            # Temporarily disconnect itemChanged to avoid triggering during population
            self.library_table.itemChanged.disconnect(self.on_library_table_item_changed)
            
            self.library_table.setRowCount(len(libraries))
            for i, lib in enumerate(libraries):
                # Plex Key (show this to user instead of database ID)
                key_item = QTableWidgetItem(str(lib['plex_library_key']))
                key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
                # Store database ID in UserRole for internal use
                key_item.setData(Qt.UserRole, lib['id'])
                self.library_table.setItem(i, 0, key_item)
                
                # Title
                title_item = QTableWidgetItem(lib['title'])
                title_item.setFlags(title_item.flags() & ~Qt.ItemIsEditable)
                self.library_table.setItem(i, 1, title_item)
                
                # Type
                type_item = QTableWidgetItem(lib['library_type'])
                type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
                self.library_table.setItem(i, 2, type_item)
                
                # Sync Enabled
                sync_status = "ON" if lib['sync_enabled'] else "OFF"
                sync_item = QTableWidgetItem(sync_status)
                sync_item.setFlags(sync_item.flags() & ~Qt.ItemIsEditable)
                self.library_table.setItem(i, 3, sync_item)
                
                # Last Sync
                last_full = "Never"
                if lib['last_full_sync_epoch']:
                    import datetime
                    dt = datetime.datetime.fromtimestamp(lib['last_full_sync_epoch'])
                    last_full = dt.strftime('%Y-%m-%d %H:%M')
                last_sync_item = QTableWidgetItem(last_full)
                last_sync_item.setFlags(last_sync_item.flags() & ~Qt.ItemIsEditable)
                self.library_table.setItem(i, 4, last_sync_item)
                
                # Plex Path
                plex_path = lib.get('plex_path') or ''
                plex_path_item = QTableWidgetItem(plex_path)
                plex_path_item.setFlags(plex_path_item.flags() & ~Qt.ItemIsEditable)
                self.library_table.setItem(i, 5, plex_path_item)
                
                # Mapped Path - query path_mappings table (EDITABLE)
                cursor = self.db.execute("""
                    SELECT local_path FROM path_mappings 
                    WHERE server_id = ? AND library_id = ?
                    LIMIT 1
                """, (lib['server_id'], lib['id']))
                mapping = cursor.fetchone()
                mapped_path = mapping['local_path'] if mapping else ''
                mapped_path_item = QTableWidgetItem(mapped_path)
                mapped_path_item.setFlags(mapped_path_item.flags() | Qt.ItemIsEditable)
                # Store server_id, library_id, plex_path, and old_path for change detection
                mapped_path_item.setData(Qt.UserRole, {
                    'server_id': lib['server_id'], 
                    'library_id': lib['id'], 
                    'plex_path': plex_path,
                    'old_path': mapped_path  # Store original value for change detection
                })
                self.library_table.setItem(i, 6, mapped_path_item)
                
                # Browse button
                browse_btn = QPushButton("...")
                browse_btn.setMaximumWidth(30)
                browse_btn.setToolTip("Browse for local folder")
                browse_btn.clicked.connect(lambda checked, row=i: self.browse_library_path(row))
                self.library_table.setCellWidget(i, 7, browse_btn)
            
            # Reconnect itemChanged
            self.library_table.itemChanged.connect(self.on_library_table_item_changed)
            
        except Exception as e:
            self.log(f"Error loading libraries: {e}")
    
    def on_library_table_item_changed(self, item):
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
            # Get database ID from UserRole (column 0 now shows Plex Key)
            library_id = self.library_table.item(row, 0).data(Qt.UserRole)
            library_title = self.library_table.item(row, 1).text()
            plex_path = self.library_table.item(row, 5).text()
            new_mapped_path = item.text().strip()
            
            # Get stored data
            data = item.data(Qt.UserRole)
            if not data:
                return
            
            server_id = data['server_id']
            old_mapped_path = data.get('old_path', '')
            
            # Skip if the path hasn't actually changed
            if new_mapped_path == old_mapped_path:
                return
            
            if not new_mapped_path:
                # User cleared the path - delete the mapping from database
                if old_mapped_path:
                    self.log(f"Removing path mapping for {library_title}")
                    # Delete mapping from database
                    try:
                        self.db.execute("""
                            DELETE FROM path_mappings 
                            WHERE server_id = ? AND library_id = ?
                        """, (server_id, int(library_id)))
                        self.db.commit()
                        self.log(f"✓ Path mapping removed for {library_title}")
                    except Exception as e:
                        self.log(f"✗ Error removing path mapping: {e}")
                
                # Update the stored old_path to empty so we don't trigger again
                if data:
                    data['old_path'] = ''
                    item.setData(Qt.UserRole, data)
                return
            
            # Save the path mapping
            self.log(f"Setting path mapping for {library_title}: {plex_path} -> {new_mapped_path}")
            self.run_command([
                sys.executable, "cli/plex_sync.py", "mappings", "add",
                "--server-id", str(server_id),
                "--library-id", str(library_id),
                "--plex-prefix", plex_path,
                "--local-prefix", new_mapped_path
            ], f"Set path mapping for {library_title}")
            
            # Try to extrapolate mappings for other libraries
            self.extrapolate_mappings(plex_path, new_mapped_path, server_id)
        except Exception as e:
            self.log(f"Error in on_library_table_item_changed: {e}")
            import traceback
            self.log(traceback.format_exc())
    
    def extrapolate_mappings(self, known_plex_path, known_local_path, server_id):
        """
        Try to extrapolate path mappings for other libraries based on a known mapping.
        
        Example:
        If known_plex_path = "/media/adultcontent" and known_local_path = "R:\\Media\\AdultContent"
        Then for plex_path = "/media/anime-movies", suggest "R:\\Media\\Anime-Movies"
        """
        try:
            if not self.db or not known_plex_path or not known_local_path:
                return
            
            self.log("Analyzing path patterns for suggestions...")
            
            # Normalize paths for comparison
            known_plex_path = known_plex_path.replace('\\', '/').strip('/')
            known_local_path = known_local_path.replace('/', '\\').rstrip('\\')
            
            # Extract the common base and the specific folder
            plex_parts = known_plex_path.split('/')
            local_parts = known_local_path.split('\\')
            
            if len(plex_parts) < 2 or len(local_parts) < 2:
                return  # Not enough structure to extrapolate
            
            # Get all libraries for this server
            libraries = self.db.list_libraries(server_id)
            suggestions = []
            
            for lib in libraries:
                lib_plex_path = lib.get('plex_path', '').replace('\\', '/').strip('/')
                if not lib_plex_path or lib_plex_path == known_plex_path:
                    continue
                
                # Check if library already has a mapping
                cursor = self.db.execute("""
                    SELECT local_path FROM path_mappings 
                    WHERE server_id = ? AND library_id = ?
                    LIMIT 1
                """, (server_id, lib['id']))
                existing_mapping = cursor.fetchone()
                if existing_mapping:
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
                    
                    # Add suggestion without checking if path exists (too slow)
                    # We'll mark as "needs verification" and user can check
                    suggestions.append({
                        'library_id': lib['id'],
                        'library_title': lib['title'],
                        'plex_path': lib_plex_path,
                        'suggested_local_path': suggested_local_path,
                        'confidence': 'medium'  # Will verify in dialog
                    })
            
            if suggestions:
                self.log(f"Found {len(suggestions)} potential mappings based on pattern")
                # Verify paths in background while showing dialog
                self.show_mapping_suggestions(suggestions, server_id)
            else:
                self.log("No similar library paths found for auto-mapping")
                
        except Exception as e:
            self.log(f"Error extrapolating mappings: {e}")
    
    def show_mapping_suggestions(self, suggestions, server_id):
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
        QTimer.singleShot(100, verify_paths)
        
        # Show dialog
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            # Apply selected mappings synchronously (multiple commands)
            applied_count = 0
            for i, suggestion in enumerate(suggestions):
                if checkboxes[i].isChecked():
                    local_path = table.item(i, 3).text().strip()
                    if local_path:
                        try:
                            # Run command directly (synchronously) to avoid worker queue issues
                            cmd = [
                                sys.executable, "cli/plex_sync.py", "mappings", "add",
                                "--server-id", str(server_id),
                                "--library-id", str(suggestion['library_id']),
                                "--plex-prefix", suggestion['plex_path'],
                                "--local-prefix", local_path
                            ]
                            
                            result = subprocess.run(
                                cmd,
                                cwd=os.getcwd(),
                                capture_output=True,
                                text=True,
                                encoding='utf-8',
                                errors='replace'
                            )
                            
                            if result.returncode == 0:
                                self.log(f"✓ Applied mapping for {suggestion['library_title']}")
                                applied_count += 1
                            else:
                                self.log(f"✗ Failed to map {suggestion['library_title']}: {result.stderr}")
                        
                        except Exception as e:
                            self.log(f"✗ Error mapping {suggestion['library_title']}: {e}")
            
            if applied_count > 0:
                self.log(f"✓ Successfully applied {applied_count} mapping(s)")
                # Refresh libraries to show new mappings
                self.refresh_libraries()
    
    def browse_library_path(self, row):
        """Open folder browser for a library row."""
        # Get current mapped path
        mapped_path_item = self.library_table.item(row, 6)
        current_path = mapped_path_item.text().strip() if mapped_path_item else ""
        
        # Start from a reasonable default directory (fast)
        # Avoid os.path.exists() check which can be slow for network paths
        if current_path and (current_path.startswith('C:') or current_path.startswith('D:') or current_path.startswith('E:') or 
                             current_path.startswith('R:') or current_path.startswith('S:') or current_path.startswith('T:')):
            start_dir = current_path
        else:
            start_dir = ""  # Let QFileDialog choose default
        
        # Open folder dialog (use QFileDialog.DontUseNativeDialog for faster opening on Windows)
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Local Folder",
            start_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if folder and mapped_path_item:
            # Get library info for saving
            # Get database ID from UserRole (column 0 now shows Plex Key)
            library_id = self.library_table.item(row, 0).data(Qt.UserRole)
            library_title = self.library_table.item(row, 1).text()
            plex_path = self.library_table.item(row, 5).text()
            
            # Get stored data
            data = mapped_path_item.data(Qt.UserRole)
            if not data:
                return
            
            server_id = data['server_id']
            
            # Update the table item (suppress auto-save)
            self._suppress_item_changed = True
            mapped_path_item.setText(folder)
            self._suppress_item_changed = False
            
            # Save immediately
            self.log(f"Setting path mapping for {library_title}: {plex_path} -> {folder}")
            self.run_command([
                sys.executable, "cli/plex_sync.py", "mappings", "add",
                "--server-id", str(server_id),
                "--library-id", str(library_id),
                "--plex-prefix", plex_path,
                "--local-prefix", folder
            ], f"Set path mapping for {library_title}")
            
            # Try to extrapolate mappings for other libraries
            self.extrapolate_mappings(plex_path, folder, server_id)
    
    def parse_libraries_output(self, output):
        """Called after CLI libraries command - just refresh from database."""
        self.refresh_libraries()
        
    def show_library_context_menu(self, position):
        """Show context menu for library table."""
        item = self.library_table.itemAt(position)
        if item is None:
            return
            
        # Get the library info from the row
        row = item.row()
        # Get database ID from UserRole (column 0 now shows Plex Key)
        library_id = self.library_table.item(row, 0).data(Qt.UserRole)
        plex_key = self.library_table.item(row, 0).text()  # For display purposes
        library_title = self.library_table.item(row, 1).text()
        current_sync = self.library_table.item(row, 3).text()
        plex_path = self.library_table.item(row, 5).text()
        mapped_path = self.library_table.item(row, 6).text()
        
        # Create context menu
        menu = QMenu(self)
        
        # Toggle sync action
        if current_sync == "ON":
            toggle_action = menu.addAction(f"Disable Sync for '{library_title}'")
            toggle_action.triggered.connect(lambda: self.toggle_library_sync(library_id, library_title, False))
        else:
            toggle_action = menu.addAction(f"Enable Sync for '{library_title}'")
            toggle_action.triggered.connect(lambda: self.toggle_library_sync(library_id, library_title, True))
        
        # Show menu
        menu.exec_(self.library_table.mapToGlobal(position))
        
    def clear_library_path_mapping(self, row):
        """Clear the path mapping for a library."""
        # Get the mapped path item
        mapped_path_item = self.library_table.item(row, 6)
        if mapped_path_item and mapped_path_item.text():
            # Clear it
            self._suppress_item_changed = True
            mapped_path_item.setText("")
            self._suppress_item_changed = False
            
            # Trigger the change handler to delete from database
            self.on_library_table_item_changed(mapped_path_item)
    
    def set_library_path_mapping(self, library_id, library_title, plex_path, current_mapped_path):
        """Set or edit path mapping for a library."""
        server_id = self.library_server_combo.currentData()
        if server_id is None:
            QMessageBox.warning(self, "Warning", "No server selected")
            return
        
        # Create a dialog to get the local path
        dialog = QMessageBox(self)
        dialog.setWindowTitle(f"Set Path Mapping - {library_title}")
        dialog.setText(f"Library: {library_title}\nPlex Path: {plex_path}\n\nEnter the local path that corresponds to this Plex path:")
        dialog.setIcon(QMessageBox.Question)
        
        # Create input field with browse button
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(0, 0, 0, 0)
        
        local_path_input = QLineEdit()
        local_path_input.setText(current_mapped_path or "")
        local_path_input.setPlaceholderText("E:\\Movies or click Browse...")
        local_path_input.setMinimumWidth(400)
        
        browse_btn = QPushButton("...")
        browse_btn.setMaximumWidth(40)
        browse_btn.setToolTip("Browse for local folder")
        
        def browse_folder():
            start_dir = local_path_input.text().strip() or os.path.expanduser("~")
            folder = QFileDialog.getExistingDirectory(
                dialog,
                "Select Local Folder",
                start_dir,
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            )
            if folder:
                local_path_input.setText(folder)
        
        browse_btn.clicked.connect(browse_folder)
        
        input_layout.addWidget(local_path_input)
        input_layout.addWidget(browse_btn)
        
        # Add the input widget to the dialog
        layout = dialog.layout()
        layout.addWidget(input_widget, layout.rowCount(), 0, 1, layout.columnCount())
        
        dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        
        result = dialog.exec_()
        
        if result == QMessageBox.Ok:
            local_path = local_path_input.text().strip()
            if not local_path:
                QMessageBox.warning(self, "Warning", "Please enter a local path")
                return
            
            # Add the path mapping
            self.log(f"=== SETTING PATH MAPPING FOR {library_title} ===")
            self.run_command([
                sys.executable, "cli/plex_sync.py", "mappings", "add",
                "--server-id", str(server_id),
                "--library-id", str(library_id),
                "--plex-prefix", plex_path,
                "--local-prefix", local_path
            ], f"Set path mapping for {library_title}")
    
    def toggle_library_sync(self, library_id, library_title, enable):
        """Toggle sync for a specific library."""
        server_id = self.library_server_combo.currentData()
        if server_id is None:
            QMessageBox.warning(self, "Warning", "No server selected")
            return
            
        action = "enable" if enable else "disable"
        self.log(f"=== {action.upper()} SYNC FOR LIBRARY: {library_title} (ID: {library_id}) ===")
        
        self.run_command([
            sys.executable, "cli/plex_sync.py", "libraries", "sync", action,
            "--library-id", str(library_id)
        ], f"{action.title()} sync for {library_title}")
        
    def update_sync_libraries(self):
        """Update sync libraries when server changes."""
        if self.sync_server_combo.currentData() is None:
            return
            
        server_id = self.sync_server_combo.currentData()
        self.refresh_libraries()
        
    def start_sync(self):
        """Start content sync."""
        if self.sync_server_combo.currentData() is None:
            QMessageBox.warning(self, "Warning", "Please select a server")
            return
            
        server_id = self.sync_server_combo.currentData()
        libraries = self.sync_libraries.text().strip()
        limit = self.sync_limit.value()
        dry_run = self.dry_run_check.isChecked()
        
        if not libraries:
            QMessageBox.warning(self, "Warning", "Please specify library IDs")
            return
            
        cmd = [
            sys.executable, "cli/plex_sync.py", "ingest", "run",
            "--server-id", str(server_id),
            "--libraries", libraries
        ]
        
        if limit > 0:
            cmd.extend(["--limit", str(limit)])
            
        if dry_run:
            cmd.append("--dry-run")
        else:
            cmd.append("--commit")
            
        self.log(f"=== STARTING SYNC ===")
        self.sync_btn.setEnabled(False)
        self.stop_sync_btn.setEnabled(True)
        
        self.run_command(cmd, "Content sync", stream_output=True)
        
    def stop_sync(self):
        """Stop content sync."""
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            
        self.sync_btn.setEnabled(True)
        self.stop_sync_btn.setEnabled(False)
        self.log("Sync stopped by user")
        
    def test_sync(self):
        """Test sync with dry run."""
        self.dry_run_check.setChecked(True)
        self.start_sync()
        
        
    def refresh_mappings(self):
        """Refresh the path mappings list."""
        self.run_command([
            sys.executable, "cli/plex_sync.py", "mappings", "list"
        ], "Refresh mappings")
        
    def parse_mappings_output(self, output):
        """Parse mappings list output and update table."""
        lines = output.strip().split('\n')
        mappings = []
        
        for line in lines:
            if '|' in line and 'ID' not in line and '---' not in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 5:
                    mappings.append({
                        'id': parts[0],
                        'server': parts[1],
                        'library': parts[2],
                        'plex_path': parts[3],
                        'local_path': parts[4]
                    })
        
        self.mapping_table.setRowCount(len(mappings))
        for i, mapping in enumerate(mappings):
            self.mapping_table.setItem(i, 0, QTableWidgetItem(mapping['id']))
            self.mapping_table.setItem(i, 1, QTableWidgetItem(mapping['server']))
            self.mapping_table.setItem(i, 2, QTableWidgetItem(mapping['library']))
            self.mapping_table.setItem(i, 3, QTableWidgetItem(mapping['plex_path']))
            self.mapping_table.setItem(i, 4, QTableWidgetItem(mapping['local_path']))
            
    def browse_local_path(self):
        """Open folder browser to select local path."""
        # Get current path if any
        current_path = self.local_path.text().strip()
        start_dir = current_path if current_path and os.path.exists(current_path) else os.path.expanduser("~")
        
        # Open folder dialog
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Local Folder",
            start_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if folder:
            self.local_path.setText(folder)
            self.log(f"Selected local path: {folder}")
    
    def add_mapping(self):
        """Add a new path mapping."""
        server_id = self.mapping_server_combo.currentData()
        library_id = self.mapping_library_combo.currentData()
        plex_path = self.plex_path.text().strip()
        local_path = self.local_path.text().strip()
        
        if not all([server_id, library_id, plex_path, local_path]):
            QMessageBox.warning(self, "Warning", "Please fill in all fields")
            return
            
        self.log(f"=== ADDING MAPPING ===")
        self.run_command([
            sys.executable, "cli/plex_sync.py", "mappings", "add",
            "--server-id", str(server_id),
            "--library-id", str(library_id),
            "--plex-prefix", plex_path,
            "--local-prefix", local_path
        ], "Add mapping")
        
        # Clear the form after starting the command
        self.clear_mapping_form()
        
    def clear_mapping_form(self):
        """Clear the add mapping form."""
        self.plex_path.clear()
        self.local_path.clear()
    
    def play_in_vlc(self, file_path):
        """Play a media file in VLC."""
        if not file_path:
            QMessageBox.warning(self, "Play Error", "No file path available")
            return
        
        # Check if file exists
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Play Error", f"File not found: {file_path}")
            return
        
        # Try common VLC paths on Windows
        vlc_paths = [
            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\VideoLAN\VLC\vlc.exe")
        ]
        
        vlc_exe = None
        for path in vlc_paths:
            if os.path.exists(path):
                vlc_exe = path
                break
        
        if not vlc_exe:
            # Try to find VLC in PATH
            try:
                result = subprocess.run(
                    ["where", "vlc.exe"],
                    capture_output=True,
                    text=True,
                    shell=True
                )
                if result.returncode == 0:
                    vlc_exe = result.stdout.strip().split('\n')[0]
            except:
                pass
        
        if not vlc_exe:
            QMessageBox.warning(
                self, 
                "VLC Not Found", 
                "VLC Media Player not found. Please install VLC or ensure it's in your PATH."
            )
            return
        
        try:
            # Launch VLC with the file
            subprocess.Popen([vlc_exe, file_path], shell=False)
            self.log(f"Playing in VLC: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Play Error", f"Failed to launch VLC: {e}")
            self.log(f"Error launching VLC: {e}")


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Retrovue Management")
    app.setApplicationVersion("1.0.0")
    
    # Create and show main window
    window = EnhancedRetrovueGUI()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
