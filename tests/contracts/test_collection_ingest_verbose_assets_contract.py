"""
Contract tests for per-run asset change detail when using --verbose-assets.

Covers:
- Created assets list with {uuid, uri}
- Updated assets list with {uuid, uri, reason}
- Default output unchanged when flag not provided
"""

from __future__ import annotations

import json
import uuid
from typing import Any
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from retrovue.cli.main import app


class _FakeImporter:
    def __init__(self, name: str, items: list[dict[str, Any]]):
        self.name = name
        self._items = items

    def validate_ingestible(self, _collection) -> bool:
        return True

    def discover(self) -> list[dict[str, Any]]:
        return list(self._items)


def _make_collection(source_id: str):
    coll = MagicMock()
    coll.uuid = uuid.uuid4()
    coll.name = "Movies"
    coll.sync_enabled = True
    coll.ingestible = True
    coll.source_id = source_id
    return coll


def _make_source(source_type: str, name: str = "Test Source"):
    src = MagicMock()
    src.type = source_type
    src.name = name
    src.config = {}
    return src


class TestCollectionIngestVerboseAssets:
    def setup_method(self):
        self.runner = CliRunner()

    @patch("retrovue.cli.commands.collection.session")
    @patch("retrovue.cli.commands.collection.resolve_collection_selector")
    @patch("retrovue.cli.commands.collection.get_importer")
    def test_collection_ingest_verbose_returns_created_assets(self, mock_get_importer, mock_resolve, mock_session):
        # Arrange DB and collection
        db = MagicMock()
        mock_session.return_value.__enter__.return_value = db
        source_id = str(uuid.uuid4())
        collection = _make_collection(source_id)
        mock_resolve.return_value = collection
        db.query.return_value.filter.return_value.first.return_value = _make_source("filesystem")

        # Importer emits two new items
        items = [
            {"path": "/media/new1.mkv", "hash_sha256": "h1"},
            {"path": "/media/new2.mkv", "hash_sha256": "h2"},
        ]
        importer = _FakeImporter("filesystem", items)
        mock_get_importer.return_value = importer

        # No existing assets
        db.scalar.return_value = None

        # Act
        result = self.runner.invoke(app, [
            "collection", "ingest", str(collection.uuid), "--json", "--verbose-assets"
        ])

        # Assert
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["status"] == "success"
        assert "created_assets" in payload
        assert "updated_assets" in payload
        assert len(payload["created_assets"]) == 2
        uris = {a["uri"] for a in payload["created_assets"]}
        assert uris == {"/media/new1.mkv", "/media/new2.mkv"}
        # UUIDs should be present and non-empty strings
        for a in payload["created_assets"]:
            assert isinstance(a.get("uuid"), str) and len(a["uuid"]) > 0

    @patch("retrovue.cli.commands.collection.session")
    @patch("retrovue.cli.commands.collection.resolve_collection_selector")
    @patch("retrovue.cli.commands.collection.get_importer")
    def test_collection_ingest_verbose_returns_updated_assets(self, mock_get_importer, mock_resolve, mock_session):
        # Arrange DB and collection
        db = MagicMock()
        mock_session.return_value.__enter__.return_value = db
        source_id = str(uuid.uuid4())
        collection = _make_collection(source_id)
        mock_resolve.return_value = collection
        db.query.return_value.filter.return_value.first.return_value = _make_source("filesystem")

        # Importer emits two existing items with different changes
        items = [
            {"path": "/media/existing1.mkv", "hash_sha256": "newhash"},  # content change
            {"path": "/media/existing2.mkv", "enricher_checksum": "e2"},  # enricher change
        ]
        importer = _FakeImporter("filesystem", items)
        mock_get_importer.return_value = importer

        # Existing assets returned in order: two lookups
        existing1 = MagicMock()
        existing1.uuid = uuid.uuid4()
        existing1.hash_sha256 = "oldhash"
        existing1.last_enricher_checksum = None

        existing2 = MagicMock()
        existing2.uuid = uuid.uuid4()
        existing2.hash_sha256 = None
        existing2.last_enricher_checksum = "e1"

        db.scalar.side_effect = [existing1, existing2]

        # Act
        result = self.runner.invoke(app, [
            "collection", "ingest", str(collection.uuid), "--json", "--verbose-assets"
        ])

        # Assert
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["status"] == "success"
        assert "updated_assets" in payload
        reasons = {a["reason"] for a in payload["updated_assets"]}
        assert reasons == {"content", "enricher"}
        uris = {a["uri"] for a in payload["updated_assets"]}
        assert uris == {"/media/existing1.mkv", "/media/existing2.mkv"}
        # UUIDs should be present
        for a in payload["updated_assets"]:
            assert isinstance(a.get("uuid"), str) and len(a["uuid"]) > 0

    @patch("retrovue.cli.commands.collection.session")
    @patch("retrovue.cli.commands.collection.resolve_collection_selector")
    @patch("retrovue.cli.commands.collection.get_importer")
    def test_collection_ingest_verbose_does_not_affect_default_output(self, mock_get_importer, mock_resolve, mock_session):
        # Arrange DB and collection
        db = MagicMock()
        mock_session.return_value.__enter__.return_value = db
        source_id = str(uuid.uuid4())
        collection = _make_collection(source_id)
        mock_resolve.return_value = collection
        db.query.return_value.filter.return_value.first.return_value = _make_source("filesystem")

        # Importer emits one new item
        items = [{"path": "/media/new.mkv"}]
        importer = _FakeImporter("filesystem", items)
        mock_get_importer.return_value = importer

        # No existing assets
        db.scalar.return_value = None

        # Act (without --verbose-assets)
        result = self.runner.invoke(app, [
            "collection", "ingest", str(collection.uuid), "--json"
        ])

        # Assert
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["status"] == "success"
        assert "created_assets" not in payload
        assert "updated_assets" not in payload






