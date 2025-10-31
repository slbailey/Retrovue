"""
Contract tests for SourceUpdate command.

Tests the behavioral contract rules (B-#) defined in SourceUpdateContract.md.
These tests verify CLI behavior, validation, output formats, and error handling.
"""

import json
import uuid
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from retrovue.cli.commands.source import app


class TestSourceUpdateContract:
    """Test SourceUpdate contract behavioral rules (B-#)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    # Existence and Validation (B-1–B-6)

    def test_source_update_source_not_found_exits_one(self):
        """
        Contract B-1/B-5: Source must exist; on not found, exit 1 with error.
        """
        with patch("retrovue.cli.commands.source.source_get_by_id") as mock_get:
            mock_get.return_value = None
            result = self.runner.invoke(app, [
                "update",
                "non-existent-source",
                "--name", "New Name",
            ])
            assert result.exit_code == 1
            assert "Error: Source 'non-existent-source' not found" in result.stderr

    def test_source_update_requires_update_flags(self):
        """
        Contract B-3/B-12: Must provide at least one supported update flag.
        """
        mock_source = MagicMock()
        mock_source.id = str(uuid.uuid4())
        mock_source.external_id = "plex-12345678"
        mock_source.type = "plex"
        mock_source.name = "Test Plex"
        mock_source.config = {"servers": [{"base_url": "http://test", "token": "token"}]}
        with patch("retrovue.cli.commands.source.source_get_by_id", return_value=mock_source):
            result = self.runner.invoke(app, [
                "update",
                "Test Plex",
            ])
            assert result.exit_code == 1
            assert "Error updating source" in result.stderr or "No updates provided" in result.stderr

    def test_source_update_json_output_format(self):
        """
        Contract B-4: When --json is supplied, output MUST include required fields.
        """
        mock_source = MagicMock()
        mock_source.id = str(uuid.uuid4())
        mock_source.external_id = "plex-12345678"
        mock_source.type = "plex"
        mock_source.name = "Test Plex"
        mock_source.config = {"servers": [{"base_url": "http://test", "token": "token"}]}
        update_result = {
            "id": str(mock_source.id),
            "external_id": mock_source.external_id,
            "type": "plex",
            "name": "Updated Plex Server",
            "config": mock_source.config,
            "updated_at": None,
        }
        with patch("retrovue.cli.commands.source.source_get_by_id", return_value=mock_source), \
             patch("retrovue.cli.commands.source.source_update", return_value=update_result):
            result = self.runner.invoke(app, [
                "update",
                "Test Plex",
                "--name", "Updated Plex Server",
                "--json",
            ])
            assert result.exit_code == 0
            output = json.loads(result.stdout)
            assert set(["id", "external_id", "type", "name", "config"]).issubset(output.keys())

    # Mode Handling (B-7)

    def test_source_update_dry_run_no_writes(self):
        """
        Contract B-7: In --dry-run mode, no database writes occur and exit code is 0.
        """
        mock_source = MagicMock()
        mock_source.id = str(uuid.uuid4())
        mock_source.external_id = "plex-12345678"
        mock_source.type = "plex"
        mock_source.name = "Test Plex"
        mock_source.config = {"servers": [{"base_url": "http://test", "token": "token"}]}
        with patch("retrovue.cli.commands.source.source_get_by_id", return_value=mock_source), \
             patch("retrovue.cli.commands.source.source_update") as mock_update:
            result = self.runner.invoke(app, [
                "update",
                "Test Plex",
                "--name", "New Name",
                "--dry-run",
            ])
            assert result.exit_code == 0
            mock_update.assert_not_called()

    # Update Logic (B-12–B-14)

    def test_source_update_preserves_existing_config(self):
        """
        Contract B-13: Only named keys may change; others preserved.
        """
        original_config = {
            "servers": [{"base_url": "http://original", "token": "original-token"}],
            "enrichers": ["ffprobe", "metadata"],
        }
        mock_source = MagicMock()
        mock_source.id = str(uuid.uuid4())
        mock_source.external_id = "plex-12345678"
        mock_source.type = "plex"
        mock_source.name = "Test Plex"
        mock_source.config = original_config.copy()
        with patch("retrovue.cli.commands.source.source_get_by_id", return_value=mock_source), \
             patch("retrovue.cli.commands.source.source_update", return_value={
                 "id": str(mock_source.id),
                 "external_id": mock_source.external_id,
                 "type": "plex",
                 "name": "Updated Name",
                 "config": {"servers": [{"base_url": "http://updated", "token": "original-token"}], "enrichers": ["ffprobe", "metadata"]},
             }) as mock_update:
            result = self.runner.invoke(app, [
                "update",
                "Test Plex",
                "--name", "Updated Name",
                "--base-url", "http://updated",
            ])
            assert result.exit_code == 0
            # Verify config passed to update preserved enrichers
            args, kwargs = mock_update.call_args
            updates = args[1] if len(args) >= 2 else kwargs.get("updates", {})
            assert "config" in updates
            cfg = updates["config"]
            assert "enrichers" in cfg

    # Output and Redaction (B-15–B-16)

    def test_source_update_redacts_sensitive_values(self):
        """
        Contract B-15/16: Sensitive values are redacted in outputs.
        """
        mock_source = MagicMock()
        mock_source.id = str(uuid.uuid4())
        mock_source.external_id = "plex-12345678"
        mock_source.type = "plex"
        mock_source.name = "Test Plex"
        mock_source.config = {"servers": [{"base_url": "http://test", "token": "secret-token"}]}
        updated = {
            "id": str(mock_source.id),
            "external_id": mock_source.external_id,
            "type": "plex",
            "name": "Updated Name",
            "config": {"servers": [{"base_url": "http://test", "token": "secret-token"}]},
        }
        with patch("retrovue.cli.commands.source.source_get_by_id", return_value=mock_source), \
             patch("retrovue.cli.commands.source.source_update", return_value=updated):
            # Human output
            result = self.runner.invoke(app, [
                "update",
                "Test Plex",
                "--name", "Updated Name",
            ])
            assert result.exit_code == 0
            assert "secret-token" not in result.stdout
            # JSON output
            result_json = self.runner.invoke(app, [
                "update",
                "Test Plex",
                "--name", "Updated Name",
                "--json",
            ])
            assert result_json.exit_code == 0
            output = json.loads(result_json.stdout)
            assert "secret-token" not in json.dumps(output)

    # Importer and External Safety (B-17–B-18)

    def test_source_update_importer_interface_compliance(self):
        """
        Contract B-17: Importer must implement required update methods.
        """
        mock_source = MagicMock()
        mock_source.id = str(uuid.uuid4())
        mock_source.external_id = "plex-12345678"
        mock_source.type = "plex"
        mock_source.name = "Test Plex"
        mock_source.config = {"servers": [{"base_url": "http://test", "token": "token"}]}
        class NonCompliant:
            pass
        with patch("retrovue.cli.commands.source.source_get_by_id", return_value=mock_source), \
             patch("retrovue.adapters.registry.ALIASES", {"plex": "plex"}), \
             patch("retrovue.adapters.registry.SOURCES", {"plex": NonCompliant}):
            result = self.runner.invoke(app, [
                "update",
                "Test Plex",
                "--name", "New Name",
            ])
            assert result.exit_code == 1
            assert "not available or not interface-compliant" in result.stderr

    def test_source_update_no_external_calls(self):
        """
        Contract B-18: Command MUST NOT perform any live external system calls.
        """
        mock_source = MagicMock()
        mock_source.id = str(uuid.uuid4())
        mock_source.external_id = "plex-12345678"
        mock_source.type = "plex"
        mock_source.name = "Test Plex"
        mock_source.config = {"servers": [{"base_url": "http://test", "token": "token"}]}
        with patch("retrovue.cli.commands.source.source_get_by_id", return_value=mock_source), \
             patch("retrovue.cli.commands.source.source_update", return_value={}), \
             patch("requests.get") as mock_get, \
             patch("requests.post") as mock_post:
            result = self.runner.invoke(app, [
                "update",
                "Test Plex",
                "--name", "New Name",
            ])
            assert result.exit_code in (0, 1)
            mock_get.assert_not_called()
            mock_post.assert_not_called()

    # Concurrency (B-19)

    def test_source_update_concurrent_modification_exits_one(self):
        """
        Contract B-19: If update fails concurrently, MUST exit with code 1.
        """
        mock_source = MagicMock()
        mock_source.id = str(uuid.uuid4())
        mock_source.external_id = "plex-12345678"
        mock_source.type = "plex"
        mock_source.name = "Test Plex"
        mock_source.config = {"servers": [{"base_url": "http://test", "token": "token"}]}
        with patch("retrovue.cli.commands.source.source_get_by_id", return_value=mock_source), \
             patch("retrovue.cli.commands.source.source_update", side_effect=Exception("Concurrent modification")):
            result = self.runner.invoke(app, [
                "update",
                "Test Plex",
                "--name", "New Name",
            ])
            assert result.exit_code == 1
            assert "concurrent" in (result.stderr.lower() or "")

