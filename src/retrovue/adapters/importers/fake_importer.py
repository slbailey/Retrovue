"""
Fake importer for testing the ingest flow.

This importer returns mock discovery data to test the ingest pipeline
without requiring actual filesystem access.
"""

from typing import Any


class FakeImporter:
    """
    Importer = Adapter. Talks to external system. Discovers content. Does not persist.
    
    Fake importer that returns mock discovery data for testing.
    """

    def discover(self) -> list[dict[str, Any]]:
        """
        Return mock discovery data for testing.

        Returns:
            List of discovery items with different URIs and raw_labels
        """
        return [
            {
                "path_uri": "file:///media/retro/Show.S01E01.mkv",
                "size": 1234567890,  # ~1.2GB
                "hash_sha256": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
                "provider": "fake",
                "raw_labels": {"title_guess": "Show", "season": 1, "episode": 1},
                "last_modified": "2025-01-01T12:00:00Z",
            },
            {
                "path_uri": "file:///media/retro/Movie.2024.mkv",
                "size": 2345678901,  # ~2.3GB
                "hash_sha256": "b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef1234567",
                "provider": "fake",
                "raw_labels": {"title_guess": "Movie", "year": 2024},
                "last_modified": "2025-01-01T13:00:00Z",
            },
        ]
