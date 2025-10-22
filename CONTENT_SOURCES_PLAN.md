# Content Sources Architecture Plan

**Goal**: Create a unified "Content Sources" management system where users can add, configure, and manage different content sources that feed into a unified content library.

---

## 🎯 **Core Concepts**

### **Content Sources**

- **Plex Server**: URL, Token, Libraries, Path Mappings
- **Jellyfin Server**: URL, Credentials, Libraries, Path Mappings
- **File System**: Directory paths, File patterns, Metadata settings

### **Content Library**

- **Unified view** of all content from all sources
- **Source attribution** for each content item
- **Filter by source** capability
- **Unified search** across all sources

---

## 🏗️ **Architecture**

### **Directory Structure**

```
src/retrovue/
├── content_sources/              # Content source implementations
│   ├── __init__.py
│   ├── base.py                  # BaseContentSource interface
│   ├── registry.py              # ContentSourceRegistry
│   │
│   ├── plex/                    # Plex content source
│   │   ├── __init__.py
│   │   ├── source.py           # PlexContentSource
│   │   ├── config_dialog.py    # Plex configuration UI
│   │   └── ... (existing plex modules)
│   │
│   ├── jellyfin/                # Jellyfin content source
│   │   ├── __init__.py
│   │   ├── source.py           # JellyfinContentSource
│   │   ├── config_dialog.py    # Jellyfin configuration UI
│   │   └── ...
│   │
│   └── filesystem/              # File system content source
│       ├── __init__.py
│       ├── source.py           # FilesystemContentSource
│       ├── config_dialog.py    # Filesystem configuration UI
│       └── ...
│
├── gui/features/
│   ├── content_sources/         # Content Sources management
│   │   ├── page.py             # Main content sources tab
│   │   └── dialogs/
│   │       ├── add_source.py    # Add content source dialog
│   │       └── modify_source.py # Modify content source dialog
│   │
│   └── content_library/         # Unified content library
│       ├── page.py             # Content library tab
│       └── filters.py          # Source filtering
```

---

## 🖥️ **GUI Design**

### **Content Sources Tab**

```python
class ContentSourcesPage(QWidget):
    """Main content sources management tab."""

    def __init__(self):
        # Table showing all content sources
        self.sources_table = QTableWidget()
        self.sources_table.setColumnCount(5)
        self.sources_table.setHorizontalHeaderLabels([
            "Name", "Type", "Status", "Libraries", "Actions"
        ])

        # Action buttons
        self.add_btn = QPushButton("Add Content Source")
        self.delete_btn = QPushButton("Delete")
        self.modify_btn = QPushButton("Modify")

        # Connect signals
        self.add_btn.clicked.connect(self._add_content_source)
        self.modify_btn.clicked.connect(self._modify_content_source)
        self.delete_btn.clicked.connect(self._delete_content_source)
```

### **Add Content Source Dialog**

```python
class AddContentSourceDialog(QDialog):
    """Dialog for adding a new content source."""

    def __init__(self, parent=None):
        # Source type selection
        self.type_combo = QComboBox()
        self.type_combo.addItem("Plex Media Server")
        self.type_combo.addItem("Jellyfin Media Server")
        self.type_combo.addItem("File System")

        # Dynamic configuration area
        self.config_widget = QWidget()

        # Connect type change to show appropriate config
        self.type_combo.currentTextChanged.connect(self._show_config)
```

### **Plex Configuration Widget**

```python
class PlexConfigWidget(QWidget):
    """Plex-specific configuration."""

    def __init__(self):
        # Basic settings
        self.name_input = QLineEdit()
        self.url_input = QLineEdit()
        self.token_input = QLineEdit()

        # Libraries section
        self.libraries_table = QTableWidget()

        # Path mappings section
        self.path_mappings_table = QTableWidget()

        # Test connection button
        self.test_btn = QPushButton("Test Connection")
```

---

## 🗄️ **Database Schema**

### **Content Sources Table**

```sql
CREATE TABLE content_sources (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,        -- 'plex', 'jellyfin', 'filesystem'
    config TEXT NOT NULL,              -- JSON configuration
    status TEXT DEFAULT 'inactive',    -- 'active', 'inactive', 'error'
    created_at INTEGER,
    updated_at INTEGER
);
```

### **Content Items (Updated)**

```sql
ALTER TABLE content_items
ADD COLUMN source_id INTEGER REFERENCES content_sources(id);

-- Update existing content to reference Plex source
UPDATE content_items SET source_id = 1 WHERE source_id IS NULL;
```

---

## 🔄 **Migration from Current State**

### **Phase 1: Create Content Sources Framework**

1. Create `content_sources/` directory structure
2. Move Plex code to `content_sources/plex/`
3. Create `BaseContentSource` interface
4. Create `ContentSourceRegistry`

### **Phase 2: Update Database Schema**

1. Create `content_sources` table
2. Migrate existing Plex servers to content sources
3. Update `content_items` to reference source_id

### **Phase 3: Create Content Sources GUI**

1. Create `ContentSourcesPage` tab
2. Create add/modify dialogs
3. Implement Plex configuration widget

### **Phase 4: Create Content Library**

1. Create unified content library view
2. Implement source filtering
3. Add source attribution display

---

## 🎯 **User Workflow**

### **Adding a Plex Source**

1. Click "Add Content Source"
2. Select "Plex Media Server"
3. Configure:
   - Name: "My Plex Server"
   - URL: "http://localhost:32400"
   - Token: "abc123..."
4. Test connection
5. Select libraries to sync
6. Configure path mappings
7. Save

### **Modifying a Source**

1. Select source in table
2. Click "Modify"
3. Same dialog opens with current values
4. Make changes
5. Save

### **Content Library View**

1. Switch to "Content Library" tab
2. See all content from all sources
3. Filter by source if desired
4. Each item shows its source

---

## ✅ **Benefits**

| Benefit             | Current         | With Content Sources    |
| ------------------- | --------------- | ----------------------- |
| **Flexibility**     | Plex-only       | Any source type         |
| **Management**      | Scattered       | Centralized             |
| **UI Clarity**      | Mixed workflows | Dedicated management    |
| **Extensibility**   | Hard to add     | Drop in new source type |
| **User Experience** | Complex         | Simple, unified         |

---

**Ready to implement this Content Sources architecture?**
