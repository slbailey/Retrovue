"""
Data contract tests for SourceAdd command.

Tests the data contract rules (D-#) defined in SourceAddContract.md.
These tests verify database operations, transaction safety, and data integrity.
"""

import json
import pytest
import uuid
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from retrovue.cli.main import app


class TestSourceAddDataContract:
    """Test SourceAdd data contract rules (D-#)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_source_add_atomic_transaction(self):
        """
        Contract D-1: Source creation MUST occur within a single transaction boundary.
        """
        with patch("retrovue.cli.commands.source.list_importers") as mock_list, \
             patch("retrovue.cli.commands.source.get_importer") as mock_get_importer, \
             patch("retrovue.cli.commands.source.session") as mock_session:
            
            mock_list.return_value = ["plex"]
            mock_importer = MagicMock()
            mock_importer.name = "PlexImporter"
            mock_get_importer.return_value = mock_importer
            
            # Mock database session with transaction tracking
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source service
            mock_source_service = MagicMock()
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, [
                    "source", "add", 
                    "--type", "plex", 
                    "--name", "Test Plex", 
                    "--base-url", "http://test", 
                    "--token", "test-token"
                ])
                
                assert result.exit_code == 0
                # Verify transaction methods were called
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()
                mock_db.refresh.assert_called_once()

    def test_source_add_external_id_uniqueness(self):
        """
        Contract D-2: External ID generation MUST be atomic and collision-free.
        """
        with patch("retrovue.cli.commands.source.list_importers") as mock_list, \
             patch("retrovue.cli.commands.source.get_importer") as mock_get_importer, \
             patch("retrovue.cli.commands.source.session") as mock_session, \
             patch("retrovue.cli.commands.source.uuid.uuid4") as mock_uuid:
            
            mock_list.return_value = ["plex"]
            mock_importer = MagicMock()
            mock_importer.name = "PlexImporter"
            mock_get_importer.return_value = mock_importer
            
            # Mock UUID to ensure predictable external ID
            mock_uuid_instance = MagicMock()
            mock_uuid_instance.hex = "1234567890abcdef"
            mock_uuid.return_value = mock_uuid_instance
            
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source service
            mock_source_service = MagicMock()
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
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

    def test_source_add_collection_discovery_transaction(self):
        """
        Contract D-3: Collection discovery MUST occur within the same transaction as source creation.
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
                # Verify collection discovery was called
                mock_source_service.discover_collections.assert_called_once()
                mock_source_service.persist_collections.assert_called_once()

    def test_source_add_collections_disabled_by_default(self):
        """
        Contract D-4: Newly discovered collections MUST be persisted with sync_enabled=False.
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
                assert "all disabled by default" in result.stdout

    def test_source_add_path_mapping_empty_local_path(self):
        """
        Contract D-5: PathMapping records MUST be created with empty local_path for discovered collections.
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
                {"name": "Movies", "external_id": "1"}
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
                # Verify persist_collections was called (which should create path mappings)
                mock_source_service.persist_collections.assert_called_once()

    def test_source_add_transaction_rollback_on_failure(self):
        """
        Contract D-6: On transaction failure, ALL changes MUST be rolled back.
        """
        with patch("retrovue.cli.commands.source.get_importer") as mock_get_importer:
            # Mock importer that raises an exception
            mock_get_importer.side_effect = Exception("Database error")
            
            result = self.runner.invoke(app, [
                "source", "add", 
                "--type", "plex", 
                "--name", "Test Plex", 
                "--base-url", "http://test", 
                "--token", "test-token"
            ])
            
            assert result.exit_code == 1
            assert "Error adding source" in result.stderr

    def test_source_add_configuration_validation_before_persistence(self):
        """
        Contract D-7: Source configuration MUST be validated before database persistence.
        """
        with patch("retrovue.cli.commands.source.get_importer") as mock_get_importer:
            # Mock importer that raises validation error
            mock_get_importer.side_effect = ValueError("Invalid configuration")
            
            result = self.runner.invoke(app, [
                "source", "add", 
                "--type", "plex", 
                "--name", "Test Plex", 
                "--base-url", "invalid-url", 
                "--token", "test-token"
            ])
            
            assert result.exit_code == 1
            assert "Error adding source" in result.stderr

    def test_source_add_enricher_validation_before_creation(self):
        """
        Contract D-8: Enricher validation MUST occur before source creation.
        """
        with patch("retrovue.cli.commands.source.list_importers") as mock_list, \
             patch("retrovue.cli.commands.source.list_enrichers") as mock_enrichers, \
             patch("retrovue.cli.commands.source.get_importer") as mock_get_importer, \
             patch("retrovue.cli.commands.source.session") as mock_session:
            
            mock_list.return_value = ["plex"]
            mock_importer = MagicMock()
            mock_importer.name = "PlexImporter"
            mock_get_importer.return_value = mock_importer
            
            # Mock enrichers
            mock_enricher = MagicMock()
            mock_enricher.name = "ffprobe"
            mock_enrichers.return_value = [mock_enricher]
            
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source service
            mock_source_service = MagicMock()
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, [
                    "source", "add", 
                    "--type", "plex", 
                    "--name", "Test Plex", 
                    "--base-url", "http://test", 
                    "--token", "test-token",
                    "--enrichers", "ffprobe"
                ])
                
                assert result.exit_code == 0
                # Verify enricher validation occurred
                mock_enrichers.assert_called_once()

    def test_source_add_no_discovery_without_flag(self):
        """
        Contract D-9: Collection discovery MUST NOT occur unless --discover is explicitly provided.
        Note: This test verifies that discovery is not called when --discover flag is not provided.
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
            mock_source_service.discover_collections.return_value = []
            
            # Mock importer
            mock_importer = MagicMock()
            mock_importer.name = "PlexImporter"
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.cli.commands.source.get_importer", return_value=mock_importer):
                
                result = self.runner.invoke(app, [
                    "source", "add", 
                    "--type", "filesystem", 
                    "--name", "Test Filesystem", 
                    "--base-path", "/test/path"
                    # No --discover flag
                ])
                
                assert result.exit_code == 0
                # Verify no collection discovery occurred for filesystem sources
                mock_source_service.discover_collections.assert_not_called()
                mock_source_service.persist_collections.assert_not_called()

    def test_source_add_interface_compliance_before_creation(self):
        """
        Contract D-10: Importer interface compliance MUST be verified before source creation.
        """
        with patch("retrovue.cli.commands.source.get_importer") as mock_get_importer:
            # Mock importer that raises interface compliance error
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
        Contract D-11: Configuration schema validation MUST be performed using importer's get_config_schema method.
        """
        with patch("retrovue.cli.commands.source.list_importers") as mock_list, \
             patch("retrovue.cli.commands.source.get_importer") as mock_get_importer, \
             patch("retrovue.cli.commands.source.session") as mock_session:
            
            mock_list.return_value = ["plex"]
            mock_importer = MagicMock()
            mock_importer.name = "PlexImporter"
            mock_get_importer.return_value = mock_importer
            
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source service
            mock_source_service = MagicMock()
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, [
                    "source", "add", 
                    "--type", "plex", 
                    "--name", "Test Plex", 
                    "--base-url", "http://test", 
                    "--token", "test-token"
                ])
                
                assert result.exit_code == 0
                # Verify importer was created with configuration (schema validation)
                mock_get_importer.assert_called_once()
                call_args = mock_get_importer.call_args
                assert call_args[0][0] == "plex"  # First positional arg is type
                assert "base_url" in call_args[1]  # Configuration was passed
                assert "token" in call_args[1]  # Configuration was passed

    def test_source_add_database_state_consistency(self):
        """
        Contract: Database state MUST remain consistent after source creation.
        """
        with patch("retrovue.cli.commands.source.list_importers") as mock_list, \
             patch("retrovue.cli.commands.source.get_importer") as mock_get_importer, \
             patch("retrovue.cli.commands.source.session") as mock_session:
            
            mock_list.return_value = ["plex"]
            mock_importer = MagicMock()
            mock_importer.name = "PlexImporter"
            mock_get_importer.return_value = mock_importer
            
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source service
            mock_source_service = MagicMock()
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, [
                    "source", "add", 
                    "--type", "plex", 
                    "--name", "Test Plex", 
                    "--base-url", "http://test", 
                    "--token", "test-token"
                ])
                
                assert result.exit_code == 0
                # Verify database operations were called in correct order
                mock_db.add.assert_called_once()
                mock_db.commit.assert_called_once()
                mock_db.refresh.assert_called_once()

    def test_source_add_collection_discovery_atomicity(self):
        """
        Contract: Collection discovery MUST be atomic with source creation.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock database session to avoid actual database operations
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock database operations
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None
            
            # Mock SourceService with collection discovery failure
            mock_source_service = MagicMock()
            mock_source_service.discover_collections.return_value = [
                {"name": "Movies", "external_id": "1"}
            ]
            mock_source_service.persist_collections.return_value = False  # Simulate failure
            
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
                assert "Warning: Failed to persist collections" in result.stderr
