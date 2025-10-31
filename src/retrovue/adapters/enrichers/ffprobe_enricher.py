"""
FFprobe enricher for extracting media metadata.

This enricher uses FFprobe to extract technical metadata from media files,
including duration, codecs, container format, and chapter markers.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from ..importers.base import DiscoveredItem
from .base import BaseEnricher, EnricherConfig, EnricherConfigurationError, EnricherError


class FFprobeEnricher(BaseEnricher):
    """
    Enricher that extracts technical metadata from media files using FFprobe.

    This enricher analyzes media files using FFprobe and extracts technical
    metadata including duration, codecs, container format, and chapter markers.
    """

    name = "ffprobe"
    scope = "ingest"

    def __init__(self, ffprobe_path: str = "ffprobe", timeout: int = 30):
        """
        Initialize the FFprobe enricher.

        Args:
            ffprobe_path: Path to the ffprobe executable
            timeout: Timeout in seconds for FFprobe operations
        """
        super().__init__(ffprobe_path=ffprobe_path, timeout=timeout)
        self.ffprobe_path = ffprobe_path
        self.timeout = timeout

    def enrich(self, discovered_item: DiscoveredItem) -> DiscoveredItem:
        """
        Enrich a discovered item with FFprobe metadata.

        Args:
            discovered_item: The item to enrich

        Returns:
            The enriched item

        Raises:
            EnricherError: If enrichment fails
        """
        try:
            # Only process file:// URIs
            if not discovered_item.path_uri.startswith("file://"):
                return discovered_item

            # Extract file path from URI
            file_path = Path(discovered_item.path_uri[7:])  # Remove "file://" prefix

            if not file_path.exists():
                raise EnricherError(f"File does not exist: {file_path}")

            # Run FFprobe to get metadata
            metadata = self._run_ffprobe(file_path)

            # Convert metadata to labels
            additional_labels = self._metadata_to_labels(metadata)

            # Return enriched item
            return self._create_enriched_item(discovered_item, additional_labels)

        except Exception as e:
            raise EnricherError(f"Failed to enrich item: {str(e)}") from e

    @classmethod
    def get_config_schema(cls) -> EnricherConfig:
        """Return configuration schema for the FFprobe enricher."""
        return EnricherConfig(
            required_params=[
                {"name": "ffprobe_path", "description": "Path to the FFprobe executable"}
            ],
            optional_params=[
                {
                    "name": "timeout",
                    "description": "Timeout in seconds for FFprobe operations",
                    "default": "30",
                }
            ],
            scope=cls.scope,
            description="Extracts technical media metadata (duration, codecs, resolution) using FFprobe",
        )

    def _validate_parameter_types(self) -> None:
        """Validate parameter types for the FFprobe enricher."""
        # Validate ffprobe_path is a non-empty string
        ffprobe_path = self._safe_get_config("ffprobe_path")
        if not isinstance(ffprobe_path, str) or not ffprobe_path.strip():
            raise EnricherConfigurationError("ffprobe_path must be a non-empty string")

        # Validate timeout is a positive integer
        timeout = self._safe_get_config("timeout", 30)
        if not isinstance(timeout, int) or timeout <= 0:
            raise EnricherConfigurationError("timeout must be a positive integer")

    def _run_ffprobe(self, file_path: Path) -> dict[str, Any]:
        """
        Run FFprobe on a file and return parsed metadata.

        Args:
            file_path: Path to the media file

        Returns:
            Dictionary containing extracted metadata

        Raises:
            EnricherError: If FFprobe fails
        """
        try:
            # Build FFprobe command
            cmd = [
                self.ffprobe_path,
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                "-show_chapters",
                str(file_path),
            ]

            # Run FFprobe
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)

            if result.returncode != 0:
                raise EnricherError(f"FFprobe failed: {result.stderr}")

            # Parse JSON output
            data = json.loads(result.stdout)

            # Extract relevant metadata
            metadata = {}

            # Duration from format
            if "format" in data and "duration" in data["format"]:
                metadata["duration"] = data["format"]["duration"]

            # Container format
            if "format" in data and "format_name" in data["format"]:
                metadata["container"] = data["format"]["format_name"]

            # Stream information
            if "streams" in data:
                video_streams = [s for s in data["streams"] if s.get("codec_type") == "video"]
                audio_streams = [s for s in data["streams"] if s.get("codec_type") == "audio"]

                # Video codec
                if video_streams:
                    video_stream = video_streams[0]
                    if "codec_name" in video_stream:
                        metadata["video_codec"] = video_stream["codec_name"]

                    # Resolution
                    if "width" in video_stream and "height" in video_stream:
                        width = video_stream["width"]
                        height = video_stream["height"]
                        metadata["resolution"] = f"{width}x{height}"

                # Audio codec
                if audio_streams:
                    audio_stream = audio_streams[0]
                    if "codec_name" in audio_stream:
                        metadata["audio_codec"] = audio_stream["codec_name"]

            # Chapter information
            if "chapters" in data:
                metadata["chapters"] = data["chapters"]

            return metadata

        except subprocess.TimeoutExpired:
            raise EnricherError("FFprobe timed out") from None
        except json.JSONDecodeError as e:
            raise EnricherError(f"Failed to parse FFprobe output: {e}") from e
        except Exception as e:
            raise EnricherError(f"FFprobe execution failed: {e}") from e

    def _metadata_to_labels(self, metadata: dict[str, Any]) -> list[str]:
        """
        Convert metadata dictionary to label list.

        Args:
            metadata: Dictionary containing extracted metadata

        Returns:
            List of labels in "key:value" format
        """
        labels = []

        # Add duration if available
        if "duration" in metadata:
            duration_ms = int(float(metadata["duration"]) * 1000)
            labels.append(f"duration_ms:{duration_ms}")

        # Add video codec if available
        if "video_codec" in metadata:
            labels.append(f"video_codec:{metadata['video_codec']}")

        # Add audio codec if available
        if "audio_codec" in metadata:
            labels.append(f"audio_codec:{metadata['audio_codec']}")

        # Add container format if available
        if "container" in metadata:
            labels.append(f"container:{metadata['container']}")

        # Add resolution if available
        if "resolution" in metadata:
            labels.append(f"resolution:{metadata['resolution']}")

        # Add chapter markers if available
        if "chapters" in metadata:
            chapter_count = len(metadata["chapters"])
            labels.append(f"chapters:{chapter_count}")

        return labels
