# Importer Framework Refactor - Phase Plan

**Goal**: Refactor Retrovue to use a plugin-based importer system where Plex is just one of many content sources, with filesystem import as a second importer.

---

## Phase 1: Backend Restructure (Non-Breaking)

**Goal**: Move existing Plex functionality into the importer framework without changing behavior.

### 1.1 Create Importer Framework Structure

**Files to Create:**

```
src/retrovue/importers/
├── __init__.py
├── base.py                    # Abstract base importer
├── registry.py                # Importer registry/factory
├── exceptions.py              # Importer-specific exceptions
│
├── plex/                      # Plex importer (moved from root)
│   ├── __init__.py
│   ├── importer.py           # PlexImporter class
│   ├── client.py             # (moved from plex/client.py)
│   ├── config.py             # (moved from plex/config.py)
│   ├── db.py                 # (moved from plex/db.py)
│   ├── ingest.py             # (moved from plex/ingest.py)
│   ├── mapper.py             # (moved from plex/mapper.py)
│   ├── pathmap.py            # (moved from plex/pathmap.py)
│   ├── validation.py         # (moved from plex/validation.py)
│   ├── error_handling.py     # (moved from plex/error_handling.py)
│   └── guid.py               # (moved from plex/guid.py)
│
├── filesystem/                # New filesystem importer
│   ├── __init__.py
│   ├── importer.py           # FilesystemImporter class
│   ├── scanner.py            # File system scanner
│   ├── metadata_reader.py   # Read metadata from files
│   └── validator.py          # Validate files
│
└── jellyfin/                  # Scaffold for future
    ├── __init__.py
    ├── importer.py           # JellyfinImporter class (stub)
    └── README.md             # "Coming soon" placeholder
```

### 1.2 Create Abstract Base Importer

**File: `src/retrovue/importers/base.py`**

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator, Optional
from dataclasses import dataclass
from enum import Enum

class ImporterCapabilities(Enum):
    SUPPORTS_SERVERS = "supports_servers"      # Has server concept (Plex/Jellyfin)
    SUPPORTS_LIBRARIES = "supports_libraries"  # Has library concept
    SUPPORTS_METADATA = "supports_metadata"    # Imports metadata
    SUPPORTS_STREAMING = "supports_streaming"  # Can stream content
    REQUIRES_PATH_MAPPING = "requires_path_mapping"  # Needs path translation

@dataclass
class ContentItem:
    """Standardized content item across all importers."""
    title: str
    kind: str  # 'movie', 'episode', 'season', 'show'
    file_path: str
    duration_ms: Optional[int] = None
    source: str = ""  # Importer source ID
    source_id: str = ""  # External ID
    metadata: Dict[str, Any] = None

class BaseImporter(ABC):
    """Abstract base class for all content importers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name (e.g., 'Plex Media Server')."""
        pass

    @property
    @abstractmethod
    def source_id(self) -> str:
        """Unique identifier (e.g., 'plex', 'filesystem', 'jellyfin')."""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[ImporterCapabilities]:
        """What features this importer supports."""
        pass

    @abstractmethod
    def discover_libraries(self, server_id: int) -> Generator[Dict[str, Any], None, None]:
        """Discover available libraries/collections."""
        pass

    @abstractmethod
    def sync_content(
        self,
        server_id: int,
        library_id: int,
        **kwargs
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Import content from this source.
        Yields progress updates.
        """
        pass

    @abstractmethod
    def validate_content(self, content_item: ContentItem) -> bool:
        """Validate that content is accessible and playable."""
        pass
```

### 1.3 Create Importer Registry

**File: `src/retrovue/importers/registry.py`**

```python
from typing import Dict, Type, List
from .base import BaseImporter
from .plex.importer import PlexImporter
from .filesystem.importer import FilesystemImporter

class ImporterRegistry:
    """Registry for all available importers."""

    def __init__(self):
        self._importers: Dict[str, Type[BaseImporter]] = {}
        self._register_default_importers()

    def _register_default_importers(self):
        """Register built-in importers."""
        self.register(PlexImporter)
        self.register(FilesystemImporter)

    def register(self, importer_class: Type[BaseImporter]):
        """Register a new importer."""
        instance = importer_class()
        self._importers[instance.source_id] = importer_class

    def get_importer(self, source_id: str) -> BaseImporter:
        """Get importer instance by source ID."""
        if source_id not in self._importers:
            raise ValueError(f"Unknown importer: {source_id}")
        return self._importers[source_id]()

    def list_importers(self) -> List[BaseImporter]:
        """List all available importers."""
        return [cls() for cls in self._importers.values()]

    def get_importer_by_capability(self, capability) -> List[BaseImporter]:
        """Get importers that support a specific capability."""
        return [
            importer for importer in self.list_importers()
            if capability in importer.capabilities
        ]

# Global registry instance
registry = ImporterRegistry()
```

### 1.4 Move Plex Code to Importer Framework

**Tasks:**

1. Move all files from `src/retrovue/plex/` to `src/retrovue/importers/plex/`
2. Create `src/retrovue/importers/plex/importer.py` implementing `BaseImporter`
3. Update all imports throughout codebase
4. Ensure existing functionality still works

**File: `src/retrovue/importers/plex/importer.py`**

```python
from ..base import BaseImporter, ImporterCapabilities, ContentItem
from .client import PlexClient
from .ingest import IngestOrchestrator
# ... other imports

class PlexImporter(BaseImporter):
    @property
    def name(self) -> str:
        return "Plex Media Server"

    @property
    def source_id(self) -> str:
        return "plex"

    @property
    def capabilities(self) -> List[ImporterCapabilities]:
        return [
            ImporterCapabilities.SUPPORTS_SERVERS,
            ImporterCapabilities.SUPPORTS_LIBRARIES,
            ImporterCapabilities.SUPPORTS_METADATA,
            ImporterCapabilities.REQUIRES_PATH_MAPPING
        ]

    def discover_libraries(self, server_id: int):
        # Move logic from LibraryManager
        ...

    def sync_content(self, server_id: int, library_id: int, **kwargs):
        # Move logic from SyncManager
        ...
```

### 1.5 Update Core API to Use Importer Registry

**File: `src/retrovue/core/api.py`**

```python
from ..importers.registry import registry

class RetrovueAPI:
    def __init__(self, db_path: str = "./retrovue.db"):
        self.db_path = db_path
        self._importers = {}

    def get_importer(self, source_id: str):
        """Get importer instance."""
        if source_id not in self._importers:
            self._importers[source_id] = registry.get_importer(source_id)
        return self._importers[source_id]

    # Update existing methods to use importer registry
    def discover_libraries(self, server_id: int, source_id: str = "plex"):
        importer = self.get_importer(source_id)
        yield from importer.discover_libraries(server_id)

    def sync_content(self, server_id: int, library_id: int, source_id: str = "plex", **kwargs):
        importer = self.get_importer(source_id)
        yield from importer.sync_content(server_id, library_id, **kwargs)
```

### 1.6 Database Schema Updates

**Add source tracking to content:**

```sql
-- Add source columns to existing tables
ALTER TABLE content_items
ADD COLUMN source TEXT DEFAULT 'plex';

ALTER TABLE content_items
ADD COLUMN source_id TEXT;

-- Create index for source queries
CREATE INDEX idx_content_source ON content_items(source, source_id);

-- Update existing content to have source='plex'
UPDATE content_items SET source='plex' WHERE source IS NULL;
```

---

## Phase 2: Filesystem Importer Implementation

**Goal**: Create a working filesystem importer that can scan directories and import content directly.

### 2.1 Filesystem Importer Core

**File: `src/retrovue/importers/filesystem/importer.py`**

```python
from ..base import BaseImporter, ImporterCapabilities, ContentItem
from .scanner import FilesystemScanner
from .metadata_reader import MetadataReader
from .validator import FileValidator

class FilesystemImporter(BaseImporter):
    @property
    def name(self) -> str:
        return "Filesystem Scanner"

    @property
    def source_id(self) -> str:
        return "filesystem"

    @property
    def capabilities(self) -> List[ImporterCapabilities]:
        return [
            ImporterCapabilities.SUPPORTS_METADATA,
            # No servers, no libraries, no path mapping needed
        ]

    def discover_libraries(self, server_id: int):
        """For filesystem, 'libraries' are just directory paths."""
        # Return configured scan directories as "libraries"
        ...

    def sync_content(self, server_id: int, library_id: int, **kwargs):
        """Scan filesystem and import content."""
        scanner = FilesystemScanner()
        metadata_reader = MetadataReader()

        for file_path in scanner.scan_directory(library_id):  # library_id = directory path
            content_item = metadata_reader.read_metadata(file_path)
            if self.validate_content(content_item):
                yield {"stage": "content_found", "item": content_item}
                # Import to database
                ...
```

### 2.2 Filesystem Scanner

**File: `src/retrovue/importers/filesystem/scanner.py`**

```python
import os
from pathlib import Path
from typing import Generator, List
import mimetypes

class FilesystemScanner:
    """Scan filesystem for media files."""

    SUPPORTED_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm'}

    def scan_directory(self, directory_path: str) -> Generator[str, None, None]:
        """Scan directory for media files."""
        path = Path(directory_path)
        if not path.exists():
            raise ValueError(f"Directory does not exist: {directory_path}")

        for file_path in path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                yield str(file_path)

    def get_directory_info(self, directory_path: str) -> dict:
        """Get information about a directory."""
        path = Path(directory_path)
        if not path.exists():
            return {"error": "Directory does not exist"}

        media_files = list(self.scan_directory(directory_path))
        return {
            "path": directory_path,
            "name": path.name,
            "media_count": len(media_files),
            "total_size": sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        }
```

### 2.3 Metadata Reader

**File: `src/retrovue/importers/filesystem/metadata_reader.py`**

```python
import os
from pathlib import Path
from typing import Dict, Any, Optional
import json

class MetadataReader:
    """Read metadata from files and NFO files."""

    def read_metadata(self, file_path: str) -> ContentItem:
        """Read metadata for a file."""
        path = Path(file_path)

        # Try to read NFO file first
        nfo_path = path.with_suffix('.nfo')
        metadata = {}
        if nfo_path.exists():
            metadata = self._read_nfo_file(nfo_path)

        # Extract from filename if no NFO
        if not metadata:
            metadata = self._extract_from_filename(path.name)

        # Determine content type
        kind = self._determine_content_type(path, metadata)

        return ContentItem(
            title=metadata.get('title', path.stem),
            kind=kind,
            file_path=str(path),
            source='filesystem',
            source_id=f"fs_{path.name}",
            metadata=metadata
        )

    def _read_nfo_file(self, nfo_path: Path) -> Dict[str, Any]:
        """Read NFO file (XML format)."""
        # Parse NFO XML
        ...

    def _extract_from_filename(self, filename: str) -> Dict[str, Any]:
        """Extract metadata from filename patterns."""
        # Handle patterns like "Movie (2023).mkv", "Show S01E01.mkv"
        ...

    def _determine_content_type(self, path: Path, metadata: Dict[str, Any]) -> str:
        """Determine if this is a movie, episode, etc."""
        # Logic to determine content type
        ...
```

### 2.4 File Validator

**File: `src/retrovue/importers/filesystem/validator.py`**

```python
import os
from pathlib import Path
from typing import List, Dict, Any
import subprocess

class FileValidator:
    """Validate filesystem files."""

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Validate a single file."""
        path = Path(file_path)

        if not path.exists():
            return {"valid": False, "error": "File does not exist"}

        if not path.is_file():
            return {"valid": False, "error": "Not a file"}

        # Check file size
        size = path.stat().st_size
        if size == 0:
            return {"valid": False, "error": "File is empty"}

        # Check if file is readable
        try:
            with open(file_path, 'rb') as f:
                f.read(1024)  # Try to read first 1KB
        except Exception as e:
            return {"valid": False, "error": f"Cannot read file: {e}"}

        return {"valid": True, "size": size}

    def validate_directory(self, directory_path: str) -> Dict[str, Any]:
        """Validate a directory for scanning."""
        path = Path(directory_path)

        if not path.exists():
            return {"valid": False, "error": "Directory does not exist"}

        if not path.is_dir():
            return {"valid": False, "error": "Not a directory"}

        # Check if directory is readable
        try:
            list(path.iterdir())
        except Exception as e:
            return {"valid": False, "error": f"Cannot read directory: {e}"}

        return {"valid": True}
```

---

## Phase 3: GUI Updates

**Goal**: Update the GUI to support multiple importers with separate tabs.

### 3.1 Restructure Importers Page

**File: `src/retrovue/gui/features/importers/page.py`**

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from .plex_tab import PlexImporterTab
from .filesystem_tab import FilesystemImporterTab

class ImportersPage(QWidget):
    """Container for all importer tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.api = get_api()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create tab widget for different importers
        self.tabs = QTabWidget()

        # Add importer tabs
        self.tabs.addTab(PlexImporterTab(self), "Plex")
        self.tabs.addTab(FilesystemImporterTab(self), "Filesystem")

        layout.addWidget(self.tabs)
```

### 3.2 Extract Plex Tab

**File: `src/retrovue/gui/features/importers/plex_tab.py`**

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
# ... other imports

class PlexImporterTab(QWidget):
    """Plex-specific import workflow (Servers → Libraries → Sync)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.api = get_api()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create subtabs for Plex workflow
        self.subtabs = QTabWidget()
        self.subtabs.addTab(self._create_servers_tab(), "Servers")
        self.subtabs.addTab(self._create_libraries_tab(), "Libraries")
        self.subtabs.addTab(self._create_sync_tab(), "Content Sync")

        layout.addWidget(self.subtabs)

    # Move existing Plex UI methods here
    def _create_servers_tab(self):
        # Existing server management UI
        ...

    def _create_libraries_tab(self):
        # Existing library discovery UI
        ...

    def _create_sync_tab(self):
        # Existing sync UI
        ...
```

### 3.3 Create Filesystem Tab

**File: `src/retrovue/gui/features/importers/filesystem_tab.py`**

```python
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QGroupBox, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from retrovue.core.api import get_api
from ...threads import Worker

class FilesystemImporterTab(QWidget):
    """Filesystem import workflow (Directories → Scan → Import)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.api = get_api()
        self.worker = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Directory selection
        dir_group = QGroupBox("Scan Directory")
        dir_layout = QVBoxLayout()

        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Directory:"))
        self.directory_input = QLineEdit()
        self.directory_input.setPlaceholderText("C:\\Media\\Movies")
        self.directory_input.setToolTip("Directory to scan for media files")
        path_layout.addWidget(self.directory_input)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_directory)
        path_layout.addWidget(self.browse_btn)

        dir_layout.addLayout(path_layout)
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)

        # Scan and import buttons
        button_layout = QHBoxLayout()

        self.scan_btn = QPushButton("Scan Directory")
        self.scan_btn.clicked.connect(self._scan_directory)
        self.scan_btn.setToolTip("Scan directory for media files (preview only)")
        button_layout.addWidget(self.scan_btn)

        self.import_btn = QPushButton("Import Files")
        self.import_btn.clicked.connect(self._import_files)
        self.import_btn.setToolTip("Import found files to database")
        button_layout.addWidget(self.import_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Progress log
        log_group = QGroupBox("Import Progress")
        log_layout = QVBoxLayout()

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Import progress will appear here...")
        log_layout.addWidget(self.log)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

    def _browse_directory(self):
        """Open directory browser."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory to Scan", ""
        )
        if directory:
            self.directory_input.setText(directory)

    def _scan_directory(self):
        """Scan directory for media files."""
        directory = self.directory_input.text().strip()
        if not directory:
            QMessageBox.warning(self, "No Directory", "Please select a directory to scan")
            return

        self._log("Scanning directory...")
        # TODO: Implement directory scanning
        self._log("Directory scan complete!")

    def _import_files(self):
        """Import found files to database."""
        directory = self.directory_input.text().strip()
        if not directory:
            QMessageBox.warning(self, "No Directory", "Please select a directory to scan first")
            return

        self._log("Starting filesystem import...")
        # TODO: Implement filesystem import
        self._log("Filesystem import complete!")

    def _log(self, message: str):
        """Add message to log."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{timestamp}] {message}")
```

---

## Phase 4: Database Schema Updates

**Goal**: Update database to support multiple content sources.

### 4.1 Add Source Tracking

```sql
-- Add source columns to content_items
ALTER TABLE content_items
ADD COLUMN source TEXT DEFAULT 'plex';

ALTER TABLE content_items
ADD COLUMN source_id TEXT;

-- Create index for source queries
CREATE INDEX idx_content_source ON content_items(source, source_id);

-- Update existing content
UPDATE content_items SET source='plex' WHERE source IS NULL;
```

### 4.2 Generic Server Management

```sql
-- Rename plex_servers to import_servers (generic)
CREATE TABLE import_servers (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,        -- 'plex', 'jellyfin', 'filesystem'
    name TEXT NOT NULL,
    base_url TEXT,              -- For network sources
    credentials TEXT,           -- JSON: token, username, password, etc.
    config TEXT,                -- JSON: additional configuration
    enabled BOOLEAN DEFAULT 1,
    created_at INTEGER,
    updated_at INTEGER
);

-- Migrate existing plex_servers data
INSERT INTO import_servers (id, source, name, base_url, credentials, enabled, created_at, updated_at)
SELECT id, 'plex', name, base_url, token, 1,
       COALESCE(created_at, strftime('%s', 'now')),
       COALESCE(updated_at, strftime('%s', 'now'))
FROM plex_servers;

-- Drop old table (after migration)
-- DROP TABLE plex_servers;
```

### 4.3 Update Library Management

```sql
-- Rename plex_libraries to import_libraries
CREATE TABLE import_libraries (
    id INTEGER PRIMARY KEY,
    server_id INTEGER NOT NULL,
    source TEXT NOT NULL,        -- 'plex', 'filesystem', etc.
    external_id TEXT NOT NULL,  -- Plex library key, directory path, etc.
    name TEXT NOT NULL,
    kind TEXT,                   -- 'movie', 'episode', 'mixed'
    config TEXT,                -- JSON: additional configuration
    sync_enabled BOOLEAN DEFAULT 0,
    created_at INTEGER,
    updated_at INTEGER,
    FOREIGN KEY (server_id) REFERENCES import_servers(id)
);

-- Migrate existing data
INSERT INTO import_libraries (id, server_id, source, external_id, name, kind, sync_enabled, created_at, updated_at)
SELECT id, server_id, 'plex', plex_library_key, name, kind, sync_enabled, created_at, updated_at
FROM plex_libraries;
```

---

## Phase 5: Content Library Unification

**Goal**: Create a unified content library view that shows content from all sources.

### 5.1 Content Library API

**File: `src/retrovue/core/content_library.py`**

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class UnifiedContentItem:
    """Unified content item from any source."""
    id: int
    title: str
    kind: str
    file_path: str
    source: str
    source_name: str
    duration_ms: Optional[int]
    metadata: Dict[str, Any]

class ContentLibrary:
    """Unified content library across all sources."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def list_content(self, source: Optional[str] = None) -> List[UnifiedContentItem]:
        """List all content, optionally filtered by source."""
        # Query content_items with source information
        ...

    def get_content_by_source(self, source: str) -> List[UnifiedContentItem]:
        """Get all content from a specific source."""
        return self.list_content(source=source)

    def search_content(self, query: str, source: Optional[str] = None) -> List[UnifiedContentItem]:
        """Search content by title, optionally filtered by source."""
        ...

    def get_content_stats(self) -> Dict[str, Any]:
        """Get statistics about content library."""
        # Count by source, kind, etc.
        ...
```

### 5.2 Content Library GUI

**File: `src/retrovue/gui/features/content_library/page.py`**

```python
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
    QGroupBox, QHeaderView
)
from PySide6.QtCore import Qt
from retrovue.core.content_library import ContentLibrary

class ContentLibraryPage(QWidget):
    """Unified content library view."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.content_library = ContentLibrary("./retrovue.db")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Filters
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Source:"))
        self.source_filter = QComboBox()
        self.source_filter.addItem("All Sources", None)
        self.source_filter.addItem("Plex", "plex")
        self.source_filter.addItem("Filesystem", "filesystem")
        self.source_filter.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.source_filter)

        filter_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search content...")
        self.search_input.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.search_input)

        filter_layout.addStretch()
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # Content table
        self.content_table = QTableWidget()
        self.content_table.setColumnCount(6)
        self.content_table.setHorizontalHeaderLabels([
            "Title", "Kind", "Source", "Duration", "File Path", "Actions"
        ])
        self.content_table.horizontalHeader().setStretchLastSection(True)
        self.content_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.content_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.content_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.content_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.content_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

        layout.addWidget(self.content_table)

        # Load initial content
        self._load_content()

    def _load_content(self):
        """Load content into table."""
        source_filter = self.source_filter.currentData()
        search_query = self.search_input.text().strip()

        if search_query:
            content = self.content_library.search_content(search_query, source_filter)
        else:
            content = self.content_library.list_content(source_filter)

        self.content_table.setRowCount(len(content))

        for row, item in enumerate(content):
            self.content_table.setItem(row, 0, QTableWidgetItem(item.title))
            self.content_table.setItem(row, 1, QTableWidgetItem(item.kind))
            self.content_table.setItem(row, 2, QTableWidgetItem(item.source_name))

            duration = f"{item.duration_ms // 60000}min" if item.duration_ms else "Unknown"
            self.content_table.setItem(row, 3, QTableWidgetItem(duration))

            self.content_table.setItem(row, 4, QTableWidgetItem(item.file_path))

            # Actions column (placeholder)
            actions_btn = QPushButton("View")
            self.content_table.setCellWidget(row, 5, actions_btn)

    def _apply_filters(self):
        """Apply current filters and reload content."""
        self._load_content()
```

---

## Implementation Timeline

| Phase       | Duration  | Risk   | Dependencies |
| ----------- | --------- | ------ | ------------ |
| **Phase 1** | 2-3 hours | Low    | None         |
| **Phase 2** | 4-6 hours | Medium | Phase 1      |
| **Phase 3** | 3-4 hours | Medium | Phase 1      |
| **Phase 4** | 1-2 hours | Low    | Phase 1      |
| **Phase 5** | 2-3 hours | Low    | Phase 1-4    |

**Total Estimated Time**: 12-18 hours

---

## Success Criteria

### Phase 1 Complete When:

- [ ] All Plex code moved to `importers/plex/`
- [ ] `BaseImporter` interface created
- [ ] `ImporterRegistry` working
- [ ] Existing functionality unchanged
- [ ] All tests passing

### Phase 2 Complete When:

- [ ] Filesystem importer implemented
- [ ] Can scan directories for media files
- [ ] Can import filesystem content to database
- [ ] Content tagged with `source='filesystem'`

### Phase 3 Complete When:

- [ ] GUI shows separate tabs for Plex and Filesystem
- [ ] Filesystem tab allows directory selection
- [ ] Filesystem import workflow functional
- [ ] UI matches existing Plex workflow quality

### Phase 4 Complete When:

- [ ] Database schema updated
- [ ] Existing data migrated
- [ ] Source tracking working
- [ ] No data loss

### Phase 5 Complete When:

- [ ] Unified content library view
- [ ] Can filter by source
- [ ] Can search across all content
- [ ] Content shows source information

---

## Benefits

| Benefit              | Before              | After                     |
| -------------------- | ------------------- | ------------------------- |
| **Flexibility**      | Plex-only           | Any source                |
| **Code Reuse**       | Duplicate logic     | Shared base class         |
| **UI Clarity**       | Mixed workflows     | One tab per source        |
| **Content Tracking** | Implicit (all Plex) | Explicit (source tracked) |
| **Future Features**  | Hard to add         | Drop in new importer      |
| **Content Library**  | Plex-centric        | Unified view              |

---

**Ready to start Phase 1?** This is the foundation that makes everything else possible!
