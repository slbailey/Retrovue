# Retrovue Importers

This document describes how to implement and use content importers in Retrovue. Importers are responsible for discovering content from various sources like Plex servers, filesystems, and other media libraries.

## Overview

Importers follow the **Adapter Pattern** and implement a common interface for content discovery. They are stateless and return standardized `DiscoveredItem` objects that can be processed by the ingestion pipeline.

## Importer Interface

### Base Protocol

```python
from typing import Protocol
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DiscoveredItem:
    """Standard format for discovered content items."""
    path_uri: str                    # URI to the content
    provider_key: str | None = None   # Provider-specific identifier
    raw_labels: list[str] | None = None  # Extracted metadata labels
    last_modified: datetime | None = None  # Last modification time
    size: int | None = None           # File size in bytes
    hash_sha256: str | None = None    # Content hash

class Importer(Protocol):
    """Protocol that all importers must implement."""
    name: str

    def discover(self) -> list[DiscoveredItem]:
        """Discover content items from the source."""
        ...
```

### Key Requirements

1. **Stateless**: Importers should not maintain internal state
2. **Idempotent**: Multiple calls should return consistent results
3. **Error Handling**: Graceful handling of discovery failures
4. **Standardized Output**: All importers return `DiscoveredItem` objects

## Built-in Importers

### 1. Filesystem Importer

**Purpose**: Discovers media files from local filesystem directories.

**Features**:

- **Glob pattern matching** for file discovery
- **SHA-256 hash calculation** for content integrity
- **Metadata extraction** from filenames
- **Hidden file filtering** options

**Usage**:

```python
from retrovue.adapters.importers.filesystem_importer import FilesystemImporter

# Basic usage
importer = FilesystemImporter(
    root_paths=["/media/movies", "/media/tv"],
    glob_patterns=["**/*.mp4", "**/*.mkv"],
    include_hidden=False,
    calculate_hash=True
)

discovered_items = importer.discover()
```

**Configuration Options**:

- `root_paths`: List of directories to scan
- `glob_patterns`: File patterns to match (default: common video extensions)
- `include_hidden`: Whether to include hidden files
- `calculate_hash`: Whether to calculate SHA-256 hashes

**Example Output**:

```python
DiscoveredItem(
    path_uri="file:///media/movies/Avengers.Endgame.2019.1080p.mkv",
    provider_key="/media/movies/Avengers.Endgame.2019.1080p.mkv",
    raw_labels=["Avengers", "Endgame", "2019", "1080p"],
    last_modified=datetime(2024, 1, 15, 14, 30, 0),
    size=8589934592,  # 8GB
    hash_sha256="a1b2c3d4e5f6..."
)
```

### 2. Plex Importer

**Purpose**: Discovers content from Plex Media Server libraries.

**Features**:

- **Plex API integration** for metadata retrieval
- **Library-specific discovery** with filtering
- **Rich metadata extraction** from Plex
- **Path mapping support** for local file access

**Usage**:

```python
from retrovue.adapters.importers.plex_importer import PlexImporter

# Plex server configuration
importer = PlexImporter(
    server_url="http://plex-server:32400",
    token="your-plex-token",
    library_ids=["1", "2"],  # Specific libraries
    include_metadata=True
)

discovered_items = importer.discover()
```

**Configuration Options**:

- `server_url`: Plex server URL
- `token`: Plex authentication token
- `library_ids`: Specific libraries to scan
- `include_metadata`: Whether to fetch rich metadata

**Example Output**:

```python
DiscoveredItem(
    path_uri="plex://server/library/12345",
    provider_key="12345",  # Plex rating key
    raw_labels=["Action", "Adventure", "Marvel", "2019"],
    last_modified=datetime(2024, 1, 15, 14, 30, 0),
    size=8589934592,
    hash_sha256=None  # Not calculated by Plex importer
)
```

## Creating Custom Importers

### 1. Basic Importer Structure

```python
from typing import Protocol
from .base import DiscoveredItem, Importer, ImporterError

class CustomImporter:
    """Custom importer for your specific source."""

    name = "custom"

    def __init__(self, config: dict):
        """Initialize with configuration."""
        self.config = config

    def discover(self) -> list[DiscoveredItem]:
        """Discover content from your source."""
        try:
            discovered_items = []

            # Your discovery logic here
            for item in self._scan_source():
                discovered_item = self._create_discovered_item(item)
                if discovered_item:
                    discovered_items.append(discovered_item)

            return discovered_items

        except Exception as e:
            raise ImporterError(f"Discovery failed: {str(e)}") from e

    def _scan_source(self):
        """Scan your content source."""
        # Implementation specific to your source
        pass

    def _create_discovered_item(self, item) -> DiscoveredItem | None:
        """Convert source item to DiscoveredItem."""
        try:
            return DiscoveredItem(
                path_uri=self._get_uri(item),
                provider_key=self._get_provider_key(item),
                raw_labels=self._extract_labels(item),
                last_modified=self._get_modified_time(item),
                size=self._get_size(item),
                hash_sha256=self._calculate_hash(item)
            )
        except Exception as e:
            print(f"Warning: Failed to process item {item}: {e}")
            return None
```

### 2. Jellyfin Importer Example

```python
import requests
from typing import Any
from .base import DiscoveredItem, Importer, ImporterError

class JellyfinImporter:
    """Importer for Jellyfin Media Server."""

    name = "jellyfin"

    def __init__(self, server_url: str, api_key: str, user_id: str):
        self.server_url = server_url.rstrip('/')
        self.api_key = api_key
        self.user_id = user_id
        self.session = requests.Session()
        self.session.headers.update({
            'X-Emby-Token': api_key,
            'Content-Type': 'application/json'
        })

    def discover(self) -> list[DiscoveredItem]:
        """Discover content from Jellyfin."""
        try:
            # Get all items from Jellyfin
            items = self._get_jellyfin_items()
            discovered_items = []

            for item in items:
                discovered_item = self._create_discovered_item(item)
                if discovered_item:
                    discovered_items.append(discovered_item)

            return discovered_items

        except Exception as e:
            raise ImporterError(f"Jellyfin discovery failed: {str(e)}") from e

    def _get_jellyfin_items(self) -> list[dict[str, Any]]:
        """Fetch items from Jellyfin API."""
        url = f"{self.server_url}/Users/{self.user_id}/Items"
        params = {
            'Recursive': 'true',
            'IncludeItemTypes': 'Movie,Episode',
            'Fields': 'Path,DateCreated,MediaSources'
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()

        return response.json().get('Items', [])

    def _create_discovered_item(self, item: dict[str, Any]) -> DiscoveredItem | None:
        """Convert Jellyfin item to DiscoveredItem."""
        try:
            # Extract file path from media sources
            media_sources = item.get('MediaSources', [])
            if not media_sources:
                return None

            file_path = media_sources[0].get('Path', '')
            if not file_path:
                return None

            # Create URI
            path_uri = f"jellyfin://{self.server_url}/item/{item['Id']}"

            # Extract labels from tags and genres
            labels = []
            labels.extend(item.get('Tags', []))
            labels.extend(item.get('Genres', []))

            return DiscoveredItem(
                path_uri=path_uri,
                provider_key=item['Id'],
                raw_labels=labels,
                last_modified=self._parse_date(item.get('DateCreated')),
                size=media_sources[0].get('Size', 0),
                hash_sha256=None  # Jellyfin doesn't provide hashes
            )

        except Exception as e:
            print(f"Warning: Failed to process Jellyfin item {item.get('Name', 'Unknown')}: {e}")
            return None
```

### 3. Database Importer Example

```python
import sqlite3
from pathlib import Path
from .base import DiscoveredItem, Importer, ImporterError

class DatabaseImporter:
    """Importer for content stored in a custom database."""

    name = "database"

    def __init__(self, db_path: str, query: str):
        self.db_path = Path(db_path)
        self.query = query

    def discover(self) -> list[DiscoveredItem]:
        """Discover content from database."""
        try:
            if not self.db_path.exists():
                raise ImporterError(f"Database not found: {self.db_path}")

            discovered_items = []

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(self.query)

                for row in cursor.fetchall():
                    discovered_item = self._create_discovered_item(row)
                    if discovered_item:
                        discovered_items.append(discovered_item)

            return discovered_items

        except Exception as e:
            raise ImporterError(f"Database discovery failed: {str(e)}") from e

    def _create_discovered_item(self, row: tuple) -> DiscoveredItem | None:
        """Convert database row to DiscoveredItem."""
        try:
            # Assuming row format: (id, path, size, modified, labels)
            item_id, path, size, modified, labels_str = row

            # Parse labels
            labels = labels_str.split(',') if labels_str else []

            return DiscoveredItem(
                path_uri=f"db://{self.db_path.name}/{item_id}",
                provider_key=str(item_id),
                raw_labels=labels,
                last_modified=self._parse_timestamp(modified),
                size=size,
                hash_sha256=None
            )

        except Exception as e:
            print(f"Warning: Failed to process database row: {e}")
            return None
```

## Importer Registration

### 1. Registry Pattern

```python
from typing import Dict, Type
from .base import Importer

class ImporterRegistry:
    """Registry for managing available importers."""

    def __init__(self):
        self._importers: Dict[str, Type[Importer]] = {}

    def register(self, name: str, importer_class: Type[Importer]):
        """Register an importer class."""
        self._importers[name] = importer_class

    def get(self, name: str) -> Type[Importer]:
        """Get an importer class by name."""
        if name not in self._importers:
            raise ImporterNotFoundError(f"Importer '{name}' not found")
        return self._importers[name]

    def create(self, name: str, config: dict) -> Importer:
        """Create an importer instance."""
        importer_class = self.get(name)
        return importer_class(**config)

    def list_available(self) -> list[str]:
        """List all available importer names."""
        return list(self._importers.keys())

# Global registry instance
registry = ImporterRegistry()

# Register built-in importers
registry.register("filesystem", FilesystemImporter)
registry.register("plex", PlexImporter)
```

### 2. Dynamic Registration

```python
# Register custom importers at runtime
from retrovue.adapters.registry import registry
from my_importers import JellyfinImporter, DatabaseImporter

registry.register("jellyfin", JellyfinImporter)
registry.register("database", DatabaseImporter)
```

## Error Handling

### 1. Importer-Specific Errors

```python
class ImporterError(Exception):
    """Base exception for importer errors."""
    pass

class ImporterNotFoundError(ImporterError):
    """Raised when an importer is not found."""
    pass

class ImporterConfigurationError(ImporterError):
    """Raised when importer configuration is invalid."""
    pass

class ImporterConnectionError(ImporterError):
    """Raised when importer cannot connect to source."""
    pass
```

### 2. Graceful Error Handling

```python
def discover_with_retry(importer: Importer, max_retries: int = 3) -> list[DiscoveredItem]:
    """Discover content with retry logic."""
    for attempt in range(max_retries):
        try:
            return importer.discover()
        except ImporterConnectionError as e:
            if attempt == max_retries - 1:
                raise
            print(f"Connection failed, retrying in 5 seconds... ({attempt + 1}/{max_retries})")
            time.sleep(5)
        except ImporterError as e:
            print(f"Importer error: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise
```

## Testing Importers

### 1. Unit Tests

```python
import pytest
from unittest.mock import Mock, patch
from retrovue.adapters.importers.filesystem_importer import FilesystemImporter

class TestFilesystemImporter:
    def test_discover_basic(self):
        """Test basic discovery functionality."""
        with patch('pathlib.Path.glob') as mock_glob:
            mock_glob.return_value = [
                Path('/media/movie1.mp4'),
                Path('/media/movie2.mkv')
            ]

            importer = FilesystemImporter(root_paths=['/media'])
            items = importer.discover()

            assert len(items) == 2
            assert items[0].path_uri == "file:///media/movie1.mp4"
            assert items[1].path_uri == "file:///media/movie2.mkv"

    def test_discover_with_filters(self):
        """Test discovery with file filters."""
        importer = FilesystemImporter(
            glob_patterns=['**/*.mp4'],
            include_hidden=False
        )

        # Test implementation...
```

### 2. Integration Tests

```python
def test_plex_importer_integration():
    """Test Plex importer with real server."""
    importer = PlexImporter(
        server_url="http://test-plex:32400",
        token="test-token",
        library_ids=["1"]
    )

    # Mock Plex API responses
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = {
            'MediaContainer': {
                'Metadata': [
                    {
                        'ratingKey': '12345',
                        'title': 'Test Movie',
                        'Media': [{'Part': [{'file': '/path/to/movie.mp4'}]}]
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        items = importer.discover()
        assert len(items) == 1
        assert items[0].provider_key == '12345'
```

## Performance Considerations

### 1. Lazy Loading

```python
class LazyImporter:
    """Importer that loads content on-demand."""

    def discover(self) -> list[DiscoveredItem]:
        """Return generator for memory efficiency."""
        for item in self._scan_lazy():
            yield self._create_discovered_item(item)
```

### 2. Caching

```python
from functools import lru_cache

class CachedImporter:
    """Importer with caching for repeated operations."""

    @lru_cache(maxsize=1000)
    def _get_metadata(self, item_id: str) -> dict:
        """Cache metadata lookups."""
        return self._fetch_metadata(item_id)
```

### 3. Parallel Processing

```python
from concurrent.futures import ThreadPoolExecutor

class ParallelImporter:
    """Importer that processes items in parallel."""

    def discover(self) -> list[DiscoveredItem]:
        """Discover items using parallel processing."""
        items = self._get_raw_items()

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self._process_item, item) for item in items]
            discovered_items = [future.result() for future in futures]

        return [item for item in discovered_items if item is not None]
```

## Best Practices

### 1. Configuration Validation

```python
def validate_config(config: dict) -> None:
    """Validate importer configuration."""
    required_fields = ['server_url', 'token']

    for field in required_fields:
        if field not in config:
            raise ImporterConfigurationError(f"Missing required field: {field}")

    if not config['server_url'].startswith(('http://', 'https://')):
        raise ImporterConfigurationError("Invalid server URL format")
```

### 2. Resource Cleanup

```python
class ResourceImporter:
    """Importer that properly manages resources."""

    def __init__(self, config: dict):
        self.config = config
        self.session = None

    def discover(self) -> list[DiscoveredItem]:
        """Discover with proper resource management."""
        try:
            self.session = self._create_session()
            return self._do_discovery()
        finally:
            self._cleanup_resources()

    def _cleanup_resources(self):
        """Clean up resources."""
        if self.session:
            self.session.close()
```

### 3. Logging and Monitoring

```python
import logging
from retrovue.infra.logging import get_logger

class LoggingImporter:
    """Importer with comprehensive logging."""

    def __init__(self, config: dict):
        self.logger = get_logger(__name__)
        self.config = config

    def discover(self) -> list[DiscoveredItem]:
        """Discover with detailed logging."""
        self.logger.info("Starting content discovery", importer=self.name)

        try:
            items = self._do_discovery()
            self.logger.info("Discovery completed", item_count=len(items))
            return items
        except Exception as e:
            self.logger.error("Discovery failed", error=str(e))
            raise
```

---

_This guide provides comprehensive information for implementing and using importers in Retrovue. For more examples, see the source code in `src/retrovue/adapters/importers/`._

