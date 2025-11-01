"""
File hash enricher: computes SHA-256 for a media file and attaches it to the item.

This enricher reads the file from disk and sets DiscoveredItem.hash_sha256.
It also appends a "hash_sha256:<value>" label for transparency.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from ..importers.base import DiscoveredItem
from .base import BaseEnricher, EnricherConfig, EnricherConfigurationError, EnricherError


class FileHashEnricher(BaseEnricher):
    """
    Enricher that computes the SHA-256 hash of a media file.
    """

    name = "filehash"
    scope = "ingest"

    def __init__(self, chunk_size: int = 2 * 1024 * 1024):
        """
        Initialize the FileHash enricher.

        Args:
            chunk_size: Read chunk size in bytes (default 2 MiB)
        """
        super().__init__(chunk_size=chunk_size)
        self.chunk_size = chunk_size

    def enrich(self, discovered_item: DiscoveredItem) -> DiscoveredItem:
        """
        Compute the SHA-256 of the file and return an updated item.
        """
        try:
            # Accept either file:// URIs or direct filesystem paths
            raw = getattr(discovered_item, "path_uri", "") or ""
            if not raw:
                return discovered_item

            file_path: Path | None = None
            if raw.startswith("file://"):
                from urllib.parse import urlparse, unquote

                parsed = urlparse(raw)
                path_str = unquote(parsed.path or raw[7:])
                if path_str.startswith("/") and len(path_str) > 3 and path_str[2] == ":":
                    path_str = path_str[1:]
                file_path = Path(path_str)
            else:
                file_path = Path(raw)

            if not file_path.exists():
                raise EnricherError(f"File does not exist: {file_path}")

            sha256_hex = self._compute_sha256(file_path)

            # Build new labels with the hash label included
            labels = (discovered_item.raw_labels or []) + [f"hash_sha256:{sha256_hex}"]

            # Return a new DiscoveredItem with hash populated
            return DiscoveredItem(
                path_uri=discovered_item.path_uri,
                provider_key=discovered_item.provider_key,
                raw_labels=labels,
                last_modified=discovered_item.last_modified,
                size=discovered_item.size,
                hash_sha256=sha256_hex,
            )

        except Exception as e:
            raise EnricherError(f"Failed to compute file hash: {e}") from e

    @classmethod
    def get_config_schema(cls) -> EnricherConfig:
        return EnricherConfig(
            required_params=[],
            optional_params=[
                {
                    "name": "chunk_size",
                    "description": "Read chunk size in bytes",
                    "default": str(2 * 1024 * 1024),
                }
            ],
            scope=cls.scope,
            description="Computes SHA-256 for a media file and attaches it to the item",
        )

    def _validate_parameter_types(self) -> None:
        chunk = self._safe_get_config("chunk_size", 2 * 1024 * 1024)
        if not isinstance(chunk, int) or chunk <= 0:
            raise EnricherConfigurationError("chunk_size must be a positive integer")

    def _compute_sha256(self, path: Path) -> str:
        hasher = hashlib.sha256()
        with path.open("rb") as f:
            while True:
                data = f.read(self.chunk_size)
                if not data:
                    break
                hasher.update(data)
        return hasher.hexdigest()


