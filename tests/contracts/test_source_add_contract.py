"""
Contract tests for SourceAdd command.

Tests the behavioral contract rules (B-#) defined in SourceAddContract.md.
These tests verify CLI behavior, validation, output formats, and error handling.
"""

import json
import pytest
import uuid
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from retrovue.cli.main import app


class TestSourceAddContract:
    """Test SourceAdd contract behavioral rules (B-#)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_source_add_help_flag_exits_zero(self):
        """
        Contract: Help flag MUST exit with code 0.
        """
        result = self.runner.invoke(app, ["source", "add", "--type", "plex", "--help"])
        assert result.exit_code == 0
        assert "Help for plex source type" in result.stdout

    def test_source_add_type_help_exits_zero(self):
        """
        Contract: Type-specific help MUST exit with code 0.
        """
        with patch("retrovue.cli.commands.source.get_importer_help") as mock_help:
            mock_help.return_value = {
                "description": "Test importer",
                "required_params": [],
                "optional_params": [],
                "examples": []
            }
            
            result = self.runner.invoke(app, ["source", "add", "--type", "plex", "--help"])
            assert result.exit_code == 0

    def test_source_add_missing_type_exits_one(self):
        """
        Contract B-1: Source type MUST be validated against available importers.
        """
        result = self.runner.invoke(app, ["source", "add", "--name", "Test Source"])
        assert result.exit_code == 1
        assert "Error: --type is required" in result.stdout

    def test_source_add_invalid_type_exits_one(self):
        """
        Contract B-1: Invalid source type MUST exit with code 1.
        """
        result = self.runner.invoke(app, ["source", "add", "--type", "invalid", "--name", "Test"])
        assert result.exit_code == 1
        assert "Unknown source type 'invalid'" in result.stderr

    def test_source_add_missing_name_exits_one(self):
        """
        Contract B-2: Required parameters MUST be validated before database operations.
        """
        result = self.runner.invoke(app, ["source", "add", "--type", "plex", "--base-url", "http://test", "--token", "test"])
        assert result.exit_code == 1
        assert "Error: --name is required" in result.stderr

    def test_source_add_plex_missing_base_url_exits_one(self):
        """
        Contract B-2: Plex-specific required parameters MUST be validated.
        """
        result = self.runner.invoke(app, ["source", "add", "--type", "plex", "--name", "Test", "--token", "test"])
        assert result.exit_code == 1
        assert "Error: --base-url is required for Plex sources" in result.stderr

    def test_source_add_plex_missing_token_exits_one(self):
        """
        Contract B-2: Plex-specific required parameters MUST be validated.
        """
        result = self.runner.invoke(app, ["source", "add", "--type", "plex", "--name", "Test", "--base-url", "http://test"])
        assert result.exit_code == 1
        assert "Error: --token is required for Plex sources" in result.stderr

    def test_source_add_filesystem_missing_base_path_exits_one(self):
        """
        Contract B-2: Filesystem-specific required parameters MUST be validated.
        """
        result = self.runner.invoke(app, ["source", "add", "--type", "filesystem", "--name", "Test"])
        assert result.exit_code == 1
        assert "Error: --base-path is required for filesystem sources" in result.stderr

    def test_source_add_successful_creation_exits_zero(self):
        """
        Contract: Successful source creation MUST exit with code 0.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock database session to avoid actual database operations
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock the Source entity creation
            mock_source = MagicMock()
            mock_source.id = "test-id-123"
            mock_source.external_id = "plex-test123"
            mock_source.name = "Test Plex"
            mock_source.type = "plex"
            mock_source.config = {"servers": [{"base_url": "http://test", "token": "test-token"}]}
            
            # Mock database operations
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            # Mock SourceService
            mock_source_service = MagicMock()
            mock_source_service.discover_collections.return_value = []
            
            # Mock importer
            mock_importer = MagicMock()
            mock_importer.name = "PlexImporter"
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.cli.commands.source.get_importer", return_value=mock_importer):
                
                result = self.runner.invoke(app, [
                    "source", "add", 
                    "--type", "plex", 
                    "--name", "Test Plex", 
                    "--base-url", "http://test", 
                    "--token", "test-token"
                ])
                
                assert result.exit_code == 0
                assert "Successfully created plex source: Test Plex" in result.stdout

    def test_source_add_json_output_format(self):
        """
        Contract B-4: JSON output MUST include required fields.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock database session to avoid actual database operations
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock the Source entity creation
            mock_source = MagicMock()
            mock_source.id = "test-id-123"
            mock_source.external_id = "plex-test123"
            mock_source.name = "Test Plex"
            mock_source.type = "plex"
            mock_source.config = {"servers": [{"base_url": "http://test", "token": "test-token"}]}
            
            # Mock database operations
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            # Mock SourceService
            mock_source_service = MagicMock()
            mock_source_service.discover_collections.return_value = []
            
            # Mock importer
            mock_importer = MagicMock()
            mock_importer.name = "PlexImporter"
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.domain.entities.Source", return_value=mock_source), \
                 patch("retrovue.cli.commands.source.get_importer", return_value=mock_importer):
                
                result = self.runner.invoke(app, [
                    "source", "add", 
                    "--type", "plex", 
                    "--name", "Test Plex", 
                    "--base-url", "http://test", 
                    "--token", "test-token",
                    "--json"
                ])
                
                assert result.exit_code == 0
                # Extract JSON from output (it might have discovery messages before it)
                output_lines = result.stdout.strip().split('\n')
                json_start = -1
                for i, line in enumerate(output_lines):
                    if line.strip().startswith('{'):
                        json_start = i
                        break
                
                assert json_start >= 0, "No JSON found in output"
                json_output = '\n'.join(output_lines[json_start:])
                output = json.loads(json_output)
                
                # Check required fields
                assert "id" in output
                assert "external_id" in output
                assert "name" in output
                assert "type" in output
                assert "config" in output
                assert "enrichers" in output
                assert "importer_name" in output

    def test_source_add_external_id_format(self):
        """
        Contract B-3: External ID MUST be generated in format "type-hash".
        """
        with patch("retrovue.cli.commands.source.session") as mock_session, \
             patch("retrovue.cli.commands.source.uuid.uuid4") as mock_uuid:
            
            # Mock UUID to ensure predictable external ID
            mock_uuid_instance = MagicMock()
            mock_uuid_instance.hex = "1234567890abcdef"
            mock_uuid.return_value = mock_uuid_instance
            
            # Mock database session to avoid actual database operations
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock the Source entity creation
            mock_source = MagicMock()
            mock_source.id = "test-id-123"
            mock_source.external_id = "plex-12345678"
            mock_source.name = "Test Plex"
            mock_source.type = "plex"
            mock_source.config = {"servers": [{"base_url": "http://test", "token": "test-token"}]}
            
            # Mock database operations
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            # Mock SourceService
            mock_source_service = MagicMock()
            mock_source_service.discover_collections.return_value = []
            
            # Mock importer
            mock_importer = MagicMock()
            mock_importer.name = "PlexImporter"
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.domain.entities.Source", return_value=mock_source), \
                 patch("retrovue.cli.commands.source.get_importer", return_value=mock_importer):
                
                result = self.runner.invoke(app, [
                    "source", "add", 
                    "--type", "plex", 
                    "--name", "Test Plex", 
                    "--base-url", "http://test", 
                    "--token", "test-token"
                ])
                
                assert result.exit_code == 0
                # External ID should be in format "plex-12345678"
                assert "External ID: plex-12345678" in result.stdout

    def test_source_add_enrichers_validation(self):
        """
        Contract: Enrichers MUST be validated against available enrichers.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session, \
             patch("retrovue.cli.commands.source.list_enrichers") as mock_enrichers:
            
            # Mock enrichers
            mock_enricher = MagicMock()
            mock_enricher.name = "ffprobe"
            mock_enrichers.return_value = [mock_enricher]
            
            # Mock database session to avoid actual database operations
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock the Source entity creation
            mock_source = MagicMock()
            mock_source.id = "test-id-123"
            mock_source.external_id = "plex-test123"
            mock_source.name = "Test Plex"
            mock_source.type = "plex"
            mock_source.config = {"servers": [{"base_url": "http://test", "token": "test-token"}]}
            
            # Mock database operations
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            # Mock SourceService
            mock_source_service = MagicMock()
            mock_source_service.discover_collections.return_value = []
            
            # Mock importer
            mock_importer = MagicMock()
            mock_importer.name = "PlexImporter"
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.domain.entities.Source", return_value=mock_source), \
                 patch("retrovue.cli.commands.source.get_importer", return_value=mock_importer):
                
                result = self.runner.invoke(app, [
                    "source", "add", 
                    "--type", "plex", 
                    "--name", "Test Plex", 
                    "--base-url", "http://test", 
                    "--token", "test-token",
                    "--enrichers", "ffprobe,invalid"
                ])
                
                assert result.exit_code == 0
                assert "Warning: Unknown enricher 'invalid'" in result.stderr

    def test_source_add_plex_collection_discovery(self):
        """
        Contract B-7: --discover flag MUST trigger collection discovery for Plex sources.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock database session to avoid actual database operations
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock database operations
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            # Mock SourceService with collection discovery
            mock_source_service = MagicMock()
            mock_source_service.discover_collections.return_value = [
                {"name": "Movies", "external_id": "1"},
                {"name": "TV Shows", "external_id": "2"}
            ]
            mock_source_service.persist_collections.return_value = True
            
            # Mock importer
            mock_importer = MagicMock()
            mock_importer.name = "plex"
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.cli.commands.source.get_importer", return_value=mock_importer):
                
                result = self.runner.invoke(app, [
                    "source", "add", 
                    "--type", "plex", 
                    "--name", "Test Plex", 
                    "--base-url", "http://test", 
                    "--token", "test-token",
                    "--discover"
                ])
                
                assert result.exit_code == 0
                assert "Discovering collections from Plex server..." in result.stdout
                assert "Discovered and persisted 2 collections" in result.stdout
                mock_source_service.discover_collections.assert_called_once()
                mock_source_service.persist_collections.assert_called_once()

    def test_source_add_filesystem_discover_ignored(self):
        """
        Contract B-7: --discover flag MUST be ignored for filesystem sources.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock database session to avoid actual database operations
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock database operations
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            # Mock SourceService
            mock_source_service = MagicMock()
            
            # Mock importer
            mock_importer = MagicMock()
            mock_importer.name = "filesystem"
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.cli.commands.source.get_importer", return_value=mock_importer):
                
                result = self.runner.invoke(app, [
                    "source", "add", 
                    "--type", "filesystem", 
                    "--name", "Test Filesystem", 
                    "--base-path", "/test/path",
                    "--discover"
                ])
                
                assert result.exit_code == 0
                assert "Warning: Collection discovery not supported for filesystem sources" in result.stderr
                mock_source_service.discover_collections.assert_not_called()
                mock_source_service.persist_collections.assert_not_called()

    def test_source_add_json_with_discover(self):
        """
        Contract B-8: JSON output with --discover MUST include collections fields.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock database session to avoid actual database operations
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock database operations
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            # Mock SourceService with collection discovery
            mock_source_service = MagicMock()
            mock_source_service.discover_collections.return_value = [
                {"name": "Movies", "external_id": "1"},
                {"name": "TV Shows", "external_id": "2"}
            ]
            mock_source_service.persist_collections.return_value = True
            
            # Mock importer
            mock_importer = MagicMock()
            mock_importer.name = "plex"
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.cli.commands.source.get_importer", return_value=mock_importer):
                
                result = self.runner.invoke(app, [
                    "source", "add", 
                    "--type", "plex", 
                    "--name", "Test Plex", 
                    "--base-url", "http://test", 
                    "--token", "test-token",
                    "--discover",
                    "--json"
                ])
                
                assert result.exit_code == 0
                # Parse JSON output - extract JSON from mixed output
                lines = result.stdout.strip().split('\n')
                json_start = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith('{'):
                        json_start = i
                        break
                
                if json_start >= 0:
                    json_lines = lines[json_start:]
                    json_output = json.loads('\n'.join(json_lines))
                    assert "collections_discovered" in json_output
                    assert json_output["collections_discovered"] == 2
                    assert "collections" in json_output
                else:
                    # If no JSON found, the test should fail
                    assert False, "No JSON output found in result"

    def test_source_add_interface_compliance_validation(self):
        """
        Contract B-10: Interface compliance MUST be verified before source creation.
        """
        with patch("retrovue.cli.commands.source.get_importer") as mock_get_importer:
            # Mock importer that raises an exception (non-compliant)
            mock_get_importer.side_effect = Exception("Interface compliance error")
            
            result = self.runner.invoke(app, [
                "source", "add", 
                "--type", "plex", 
                "--name", "Test Plex", 
                "--base-url", "http://test", 
                "--token", "test-token"
            ])
            
            assert result.exit_code == 1
            assert "Error adding source" in result.stderr

    def test_source_add_configuration_schema_validation(self):
        """
        Contract B-11: Configuration MUST be validated against importer's schema.
        """
        with patch("retrovue.cli.commands.source.get_importer") as mock_get_importer:
            # Mock importer that raises validation error
            mock_get_importer.side_effect = ValueError("Invalid configuration schema")
            
            result = self.runner.invoke(app, [
                "source", "add", 
                "--type", "plex", 
                "--name", "Test Plex", 
                "--base-url", "invalid-url", 
                "--token", "test-token"
            ])
            
            assert result.exit_code == 1
            assert "Error adding source" in result.stderr

    def test_source_add_dry_run_support(self):
        """
        Contract B-6: --dry-run flag MUST show validation without executing.
        """
        result = self.runner.invoke(app, [
            "source", "add",
            "--type", "plex",
            "--name", "Test Plex",
            "--base-url", "http://test",
            "--token", "test-token",
            "--dry-run"
        ])
        
        # Should succeed with exit code 0 and show dry-run output
        assert result.exit_code == 0
        assert "[DRY RUN]" in result.stdout
        assert "Would create plex source: Test Plex" in result.stdout
        assert "External ID:" in result.stdout

    def test_source_add_test_db_support(self):
        """
        Contract: --test-db flag MUST be supported.
        """
        result = self.runner.invoke(app, [
            "source", "add",
            "--type", "plex",
            "--name", "Test Plex",
            "--base-url", "http://test",
            "--token", "test-token",
            "--test-db"
        ])
        
        # Should succeed with exit code 0 and show test-db message
        assert result.exit_code == 0
        assert "Using test database environment" in result.stderr
        assert "Successfully created plex source: Test Plex" in result.stdout
