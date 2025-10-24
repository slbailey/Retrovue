# Retrovue Enrichers

This document describes how to implement and use content enrichers in Retrovue. Enrichers are responsible for adding metadata to discovered content items, such as technical details, duration, codecs, and chapter markers.

## Overview

Enrichers follow the **Enrichment Pattern** and implement a common interface for metadata enhancement. They are stateless and operate on `DiscoveredItem` objects, returning enriched versions with additional metadata.

## Enricher Interface

### Base Protocol

```python
from typing import Protocol
from ..importers.base import DiscoveredItem

class Enricher(Protocol):
    """Protocol that all enrichers must implement."""
    name: str

    def enrich(self, discovered_item: DiscoveredItem) -> DiscoveredItem:
        """Enrich a discovered item with additional metadata."""
        ...
```

### Key Requirements

1. **Stateless**: Enrichers should not maintain internal state
2. **Idempotent**: Multiple enrichments should be safe
3. **Error Handling**: Graceful handling of enrichment failures
4. **Non-destructive**: Should not modify original items in place

## Built-in Enrichers

### 1. FFprobe Enricher

**Purpose**: Extracts technical metadata from media files using FFprobe.

**Features**:

- **Duration extraction** in milliseconds
- **Codec detection** (video and audio)
- **Container format** identification
- **Resolution analysis** (width x height)
- **Chapter marker** extraction
- **Stream analysis** for multiple tracks

**Usage**:

```python
from retrovue.adapters.enrichers.ffprobe_enricher import FFprobeEnricher

# Basic usage
enricher = FFprobeEnricher(ffprobe_path="ffprobe")

# Enrich a discovered item
enriched_item = enricher.enrich(discovered_item)
```

**Configuration Options**:

- `ffprobe_path`: Path to FFprobe executable (default: "ffprobe")

**Example Output**:

```python
# Input
DiscoveredItem(
    path_uri="file:///media/movie.mp4",
    raw_labels=["Action", "2023"]
)

# Output (enriched)
DiscoveredItem(
    path_uri="file:///media/movie.mp4",
    raw_labels=[
        "Action", "2023",
        "duration_ms:7200000",      # 2 hours
        "video_codec:h264",
        "audio_codec:aac",
        "container:mov,mp4,m4a,3gp,3g2,mj2",
        "resolution:1920x1080",
        "chapters:12"
    ]
)
```

**FFprobe Command**:

```bash
ffprobe -v quiet -print_format json -show_format -show_streams -show_chapters movie.mp4
```

**Sample FFprobe Output**:

```json
{
  "format": {
    "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
    "duration": "7200.000000"
  },
  "streams": [
    {
      "codec_type": "video",
      "codec_name": "h264",
      "width": 1920,
      "height": 1080
    },
    {
      "codec_type": "audio",
      "codec_name": "aac"
    }
  ],
  "chapters": [
    {
      "id": 0,
      "start_time": "0.000000",
      "end_time": "600.000000",
      "title": "Chapter 1"
    }
  ]
}
```

## Creating Custom Enrichers

### 1. Basic Enricher Structure

```python
from typing import Any
from ..importers.base import DiscoveredItem
from .base import Enricher, EnricherError

class CustomEnricher:
    """Custom enricher for your specific metadata source."""

    name = "custom"

    def __init__(self, config: dict):
        """Initialize with configuration."""
        self.config = config

    def enrich(self, discovered_item: DiscoveredItem) -> DiscoveredItem:
        """Enrich a discovered item with custom metadata."""
        try:
            # Skip if not applicable
            if not self._should_enrich(discovered_item):
                return discovered_item

            # Extract metadata
            metadata = self._extract_metadata(discovered_item)

            # Create enriched labels
            enriched_labels = discovered_item.raw_labels or []
            enriched_labels.extend(self._format_metadata(metadata))

            # Return enriched item
            return DiscoveredItem(
                path_uri=discovered_item.path_uri,
                provider_key=discovered_item.provider_key,
                raw_labels=enriched_labels,
                last_modified=discovered_item.last_modified,
                size=discovered_item.size,
                hash_sha256=discovered_item.hash_sha256
            )

        except Exception as e:
            raise EnricherError(f"Enrichment failed: {str(e)}") from e

    def _should_enrich(self, item: DiscoveredItem) -> bool:
        """Determine if item should be enriched."""
        # Implementation specific to your enricher
        return True

    def _extract_metadata(self, item: DiscoveredItem) -> dict[str, Any]:
        """Extract metadata from the item."""
        # Implementation specific to your enricher
        return {}

    def _format_metadata(self, metadata: dict[str, Any]) -> list[str]:
        """Format metadata as labels."""
        labels = []
        for key, value in metadata.items():
            labels.append(f"{key}:{value}")
        return labels
```

### 2. MediaInfo Enricher Example

```python
import subprocess
import json
from pathlib import Path
from .base import Enricher, EnricherError

class MediaInfoEnricher:
    """Enricher using MediaInfo for detailed media analysis."""

    name = "mediainfo"

    def __init__(self, mediainfo_path: str = "mediainfo"):
        self.mediainfo_path = mediainfo_path

    def enrich(self, discovered_item: DiscoveredItem) -> DiscoveredItem:
        """Enrich with MediaInfo metadata."""
        try:
            if not discovered_item.path_uri.startswith("file://"):
                return discovered_item

            file_path = Path(discovered_item.path_uri[7:])
            if not file_path.exists():
                return discovered_item

            # Run MediaInfo
            metadata = self._run_mediainfo(file_path)

            # Extract relevant information
            enriched_labels = discovered_item.raw_labels or []

            # Add technical details
            if "duration" in metadata:
                enriched_labels.append(f"duration_ms:{metadata['duration']}")

            if "video_codec" in metadata:
                enriched_labels.append(f"video_codec:{metadata['video_codec']}")

            if "audio_codec" in metadata:
                enriched_labels.append(f"audio_codec:{metadata['audio_codec']}")

            if "bitrate" in metadata:
                enriched_labels.append(f"bitrate:{metadata['bitrate']}")

            if "fps" in metadata:
                enriched_labels.append(f"fps:{metadata['fps']}")

            return DiscoveredItem(
                path_uri=discovered_item.path_uri,
                provider_key=discovered_item.provider_key,
                raw_labels=enriched_labels,
                last_modified=discovered_item.last_modified,
                size=discovered_item.size,
                hash_sha256=discovered_item.hash_sha256
            )

        except Exception as e:
            raise EnricherError(f"MediaInfo enrichment failed: {str(e)}") from e

    def _run_mediainfo(self, file_path: Path) -> dict[str, Any]:
        """Run MediaInfo and parse output."""
        cmd = [
            self.mediainfo_path,
            "--Output=JSON",
            str(file_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            raise EnricherError(f"MediaInfo failed: {result.stderr}")

        data = json.loads(result.stdout)

        # Extract metadata from MediaInfo JSON structure
        metadata = {}

        if "media" in data and "track" in data["media"]:
            tracks = data["media"]["track"]

            for track in tracks:
                if track.get("@type") == "General":
                    if "Duration" in track:
                        # Convert to milliseconds
                        duration_str = track["Duration"]
                        if "ms" in duration_str:
                            metadata["duration"] = int(duration_str.replace("ms", ""))
                        elif "s" in duration_str:
                            metadata["duration"] = int(float(duration_str.replace("s", "")) * 1000)

                elif track.get("@type") == "Video":
                    if "CodecID" in track:
                        metadata["video_codec"] = track["CodecID"]
                    if "BitRate" in track:
                        metadata["bitrate"] = track["BitRate"]
                    if "FrameRate" in track:
                        metadata["fps"] = track["FrameRate"]

                elif track.get("@type") == "Audio":
                    if "CodecID" in track:
                        metadata["audio_codec"] = track["CodecID"]

        return metadata
```

### 3. ExifTool Enricher Example

```python
import subprocess
import json
from pathlib import Path
from .base import Enricher, EnricherError

class ExifToolEnricher:
    """Enricher using ExifTool for metadata extraction."""

    name = "exiftool"

    def __init__(self, exiftool_path: str = "exiftool"):
        self.exiftool_path = exiftool_path

    def enrich(self, discovered_item: DiscoveredItem) -> DiscoveredItem:
        """Enrich with ExifTool metadata."""
        try:
            if not discovered_item.path_uri.startswith("file://"):
                return discovered_item

            file_path = Path(discovered_item.path_uri[7:])
            if not file_path.exists():
                return discovered_item

            # Run ExifTool
            metadata = self._run_exiftool(file_path)

            # Extract relevant information
            enriched_labels = discovered_item.raw_labels or []

            # Add metadata tags
            for key, value in metadata.items():
                if isinstance(value, (str, int, float)):
                    enriched_labels.append(f"{key}:{value}")

            return DiscoveredItem(
                path_uri=discovered_item.path_uri,
                provider_key=discovered_item.provider_key,
                raw_labels=enriched_labels,
                last_modified=discovered_item.last_modified,
                size=discovered_item.size,
                hash_sha256=discovered_item.hash_sha256
            )

        except Exception as e:
            raise EnricherError(f"ExifTool enrichment failed: {str(e)}") from e

    def _run_exiftool(self, file_path: Path) -> dict[str, Any]:
        """Run ExifTool and parse output."""
        cmd = [
            self.exiftool_path,
            "-json",
            "-all",
            str(file_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            raise EnricherError(f"ExifTool failed: {result.stderr}")

        data = json.loads(result.stdout)

        if not data:
            return {}

        # Return first file's metadata
        return data[0]
```

### 4. Database Enricher Example

```python
import sqlite3
from pathlib import Path
from .base import Enricher, EnricherError

class DatabaseEnricher:
    """Enricher that looks up metadata from a database."""

    name = "database"

    def __init__(self, db_path: str, query: str):
        self.db_path = Path(db_path)
        self.query = query

    def enrich(self, discovered_item: DiscoveredItem) -> DiscoveredItem:
        """Enrich with database metadata."""
        try:
            if not self.db_path.exists():
                return discovered_item

            # Look up metadata in database
            metadata = self._lookup_metadata(discovered_item)

            if not metadata:
                return discovered_item

            # Add metadata as labels
            enriched_labels = discovered_item.raw_labels or []

            for key, value in metadata.items():
                if value is not None:
                    enriched_labels.append(f"{key}:{value}")

            return DiscoveredItem(
                path_uri=discovered_item.path_uri,
                provider_key=discovered_item.provider_key,
                raw_labels=enriched_labels,
                last_modified=discovered_item.last_modified,
                size=discovered_item.size,
                hash_sha256=discovered_item.hash_sha256
            )

        except Exception as e:
            raise EnricherError(f"Database enrichment failed: {str(e)}") from e

    def _lookup_metadata(self, item: DiscoveredItem) -> dict[str, Any]:
        """Look up metadata in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(self.query, (item.path_uri,))
            row = cursor.fetchone()

            if not row:
                return {}

            # Convert row to dictionary
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
```

## Enricher Pipeline Contract

### 1. Pipeline Execution

```python
class EnrichmentPipeline:
    """Pipeline for executing multiple enrichers in sequence."""

    def __init__(self, enrichers: list[Enricher]):
        self.enrichers = enrichers

    def enrich(self, discovered_item: DiscoveredItem) -> DiscoveredItem:
        """Enrich item through all enrichers."""
        current_item = discovered_item

        for enricher in self.enrichers:
            try:
                current_item = enricher.enrich(current_item)
            except EnricherError as e:
                print(f"Warning: {enricher.name} enrichment failed: {e}")
                # Continue with next enricher
                continue

        return current_item
```

### 2. Conditional Enrichment

```python
class ConditionalEnricher:
    """Enricher that only runs under certain conditions."""

    def __init__(self, enricher: Enricher, condition: callable):
        self.enricher = enricher
        self.condition = condition

    def enrich(self, discovered_item: DiscoveredItem) -> DiscoveredItem:
        """Enrich only if condition is met."""
        if self.condition(discovered_item):
            return self.enricher.enrich(discovered_item)
        return discovered_item

# Usage
ffprobe_enricher = FFprobeEnricher()
conditional_ffprobe = ConditionalEnricher(
    ffprobe_enricher,
    lambda item: item.path_uri.startswith("file://")
)
```

### 3. Parallel Enrichment

```python
from concurrent.futures import ThreadPoolExecutor
from typing import List

class ParallelEnrichmentPipeline:
    """Pipeline that runs enrichers in parallel."""

    def __init__(self, enrichers: List[Enricher]):
        self.enrichers = enrichers

    def enrich(self, discovered_item: DiscoveredItem) -> DiscoveredItem:
        """Enrich item using parallel processing."""
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(enricher.enrich, discovered_item)
                for enricher in self.enrichers
            ]

            # Collect results
            enriched_items = []
            for future in futures:
                try:
                    enriched_item = future.result(timeout=30)
                    enriched_items.append(enriched_item)
                except Exception as e:
                    print(f"Warning: Enrichment failed: {e}")

            # Merge enriched items
            return self._merge_enriched_items(discovered_item, enriched_items)

    def _merge_enriched_items(self, original: DiscoveredItem, enriched: List[DiscoveredItem]) -> DiscoveredItem:
        """Merge multiple enriched items into one."""
        all_labels = original.raw_labels or []

        for item in enriched:
            if item.raw_labels:
                all_labels.extend(item.raw_labels)

        return DiscoveredItem(
            path_uri=original.path_uri,
            provider_key=original.provider_key,
            raw_labels=all_labels,
            last_modified=original.last_modified,
            size=original.size,
            hash_sha256=original.hash_sha256
        )
```

## Enricher Registration

### 1. Registry Pattern

```python
from typing import Dict, Type
from .base import Enricher

class EnricherRegistry:
    """Registry for managing available enrichers."""

    def __init__(self):
        self._enrichers: Dict[str, Type[Enricher]] = {}

    def register(self, name: str, enricher_class: Type[Enricher]):
        """Register an enricher class."""
        self._enrichers[name] = enricher_class

    def get(self, name: str) -> Type[Enricher]:
        """Get an enricher class by name."""
        if name not in self._enrichers:
            raise EnricherNotFoundError(f"Enricher '{name}' not found")
        return self._enrichers[name]

    def create(self, name: str, config: dict) -> Enricher:
        """Create an enricher instance."""
        enricher_class = self.get(name)
        return enricher_class(**config)

    def list_available(self) -> list[str]:
        """List all available enricher names."""
        return list(self._enrichers.keys())

# Global registry instance
registry = EnricherRegistry()

# Register built-in enrichers
registry.register("ffprobe", FFprobeEnricher)
```

### 2. Dynamic Registration

```python
# Register custom enrichers at runtime
from retrovue.adapters.registry import registry
from my_enrichers import MediaInfoEnricher, ExifToolEnricher

registry.register("mediainfo", MediaInfoEnricher)
registry.register("exiftool", ExifToolEnricher)
```

## Error Handling

### 1. Enricher-Specific Errors

```python
class EnricherError(Exception):
    """Base exception for enricher errors."""
    pass

class EnricherNotFoundError(EnricherError):
    """Raised when an enricher is not found."""
    pass

class EnricherConfigurationError(EnricherError):
    """Raised when enricher configuration is invalid."""
    pass

class EnricherTimeoutError(EnricherError):
    """Raised when enricher operation times out."""
    pass
```

### 2. Graceful Error Handling

```python
def enrich_with_fallback(enricher: Enricher, item: DiscoveredItem) -> DiscoveredItem:
    """Enrich with fallback on failure."""
    try:
        return enricher.enrich(item)
    except EnricherError as e:
        print(f"Enrichment failed: {e}")
        # Return original item unchanged
        return item
    except Exception as e:
        print(f"Unexpected error: {e}")
        return item
```

## Testing Enrichers

### 1. Unit Tests

```python
import pytest
from unittest.mock import Mock, patch
from retrovue.adapters.enrichers.ffprobe_enricher import FFprobeEnricher

class TestFFprobeEnricher:
    def test_enrich_basic(self):
        """Test basic enrichment functionality."""
        enricher = FFprobeEnricher()

        # Mock FFprobe output
        mock_output = {
            "format": {"duration": "120.0"},
            "streams": [
                {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080},
                {"codec_type": "audio", "codec_name": "aac"}
            ]
        }

        with patch.object(enricher, '_run_ffprobe', return_value=mock_output):
            item = DiscoveredItem(
                path_uri="file:///test.mp4",
                raw_labels=["test"]
            )

            enriched = enricher.enrich(item)

            assert "duration_ms:120000" in enriched.raw_labels
            assert "video_codec:h264" in enriched.raw_labels
            assert "audio_codec:aac" in enriched.raw_labels
            assert "resolution:1920x1080" in enriched.raw_labels

    def test_enrich_non_file_uri(self):
        """Test that non-file URIs are skipped."""
        enricher = FFprobeEnricher()

        item = DiscoveredItem(
            path_uri="plex://server/item",
            raw_labels=["test"]
        )

        enriched = enricher.enrich(item)
        assert enriched == item  # Should be unchanged
```

### 2. Integration Tests

```python
def test_ffprobe_enricher_integration():
    """Test FFprobe enricher with real files."""
    enricher = FFprobeEnricher()

    # Create a test video file
    test_file = create_test_video()

    item = DiscoveredItem(
        path_uri=f"file://{test_file}",
        raw_labels=["test"]
    )

    enriched = enricher.enrich(item)

    # Verify enrichment worked
    assert len(enriched.raw_labels) > len(item.raw_labels)
    assert any("duration_ms:" in label for label in enriched.raw_labels)
    assert any("video_codec:" in label for label in enriched.raw_labels)
```

## Performance Considerations

### 1. Caching

```python
from functools import lru_cache

class CachedEnricher:
    """Enricher with caching for expensive operations."""

    @lru_cache(maxsize=1000)
    def _get_metadata(self, file_path: str) -> dict:
        """Cache metadata lookups."""
        return self._extract_metadata(file_path)
```

### 2. Timeout Handling

```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds):
    """Context manager for operation timeouts."""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        signal.alarm(0)

class TimeoutEnricher:
    """Enricher with timeout protection."""

    def enrich(self, discovered_item: DiscoveredItem) -> DiscoveredItem:
        """Enrich with timeout protection."""
        try:
            with timeout(30):  # 30 second timeout
                return self._do_enrichment(discovered_item)
        except TimeoutError:
            raise EnricherTimeoutError("Enrichment timed out")
```

### 3. Resource Management

```python
class ResourceEnricher:
    """Enricher that properly manages resources."""

    def __init__(self, config: dict):
        self.config = config
        self.session = None

    def enrich(self, discovered_item: DiscoveredItem) -> DiscoveredItem:
        """Enrich with proper resource management."""
        try:
            self.session = self._create_session()
            return self._do_enrichment(discovered_item)
        finally:
            self._cleanup_resources()

    def _cleanup_resources(self):
        """Clean up resources."""
        if self.session:
            self.session.close()
```

## Best Practices

### 1. Configuration Validation

```python
def validate_enricher_config(config: dict) -> None:
    """Validate enricher configuration."""
    required_fields = ['tool_path']

    for field in required_fields:
        if field not in config:
            raise EnricherConfigurationError(f"Missing required field: {field}")

    if not Path(config['tool_path']).exists():
        raise EnricherConfigurationError(f"Tool not found: {config['tool_path']}")
```

### 2. Logging and Monitoring

```python
import logging
from retrovue.infra.logging import get_logger

class LoggingEnricher:
    """Enricher with comprehensive logging."""

    def __init__(self, config: dict):
        self.logger = get_logger(__name__)
        self.config = config

    def enrich(self, discovered_item: DiscoveredItem) -> DiscoveredItem:
        """Enrich with detailed logging."""
        self.logger.info("Starting enrichment", enricher=self.name, item=discovered_item.path_uri)

        try:
            enriched_item = self._do_enrichment(discovered_item)
            self.logger.info("Enrichment completed",
                           enricher=self.name,
                           original_labels=len(discovered_item.raw_labels or []),
                           enriched_labels=len(enriched_item.raw_labels or []))
            return enriched_item
        except Exception as e:
            self.logger.error("Enrichment failed", enricher=self.name, error=str(e))
            raise
```

### 3. Label Formatting

```python
class StandardizedEnricher:
    """Enricher that formats labels consistently."""

    def _format_label(self, key: str, value: Any) -> str:
        """Format a metadata key-value pair as a label."""
        # Standardize key format
        key = key.lower().replace(' ', '_')

        # Standardize value format
        if isinstance(value, float):
            value = f"{value:.2f}"
        elif isinstance(value, (list, tuple)):
            value = ",".join(str(v) for v in value)
        else:
            value = str(value)

        return f"{key}:{value}"
```

---

_This guide provides comprehensive information for implementing and using enrichers in Retrovue. For more examples, see the source code in `src/retrovue/adapters/enrichers/`._

