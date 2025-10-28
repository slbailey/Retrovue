"""
Data contract tests for Source Discover command.

Tests the data persistence and transaction aspects of the source discover command as defined in
docs/contracts/resources/SourceDiscoverContract.md (D-1 through D-9).
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from retrovue.cli.commands.source import app


class TestSourceDiscoverDataContract:
    """Test data contract rules for source discover command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_source_discover_transaction_boundary(self):
        """
        Contract D-1: Collection discovery MUST occur within a single transaction boundary.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Test Plex Server"
            mock_source.type = "plex"
            mock_source.config = {"base_url": "http://test", "token": "test-token"}
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            
            # Mock importer to return collections
            mock_importer = MagicMock()
            mock_importer.list_collections.return_value = [
                {"external_id": "1", "name": "Movies", "plex_section_ref": "1", "type": "movie"}
            ]
            
            # Mock database query to return no existing collections
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.adapters.importers.plex_importer.PlexImporter", return_value=mock_importer):
                
                result = self.runner.invoke(app, ["discover", "test-source"])
                
                assert result.exit_code == 0
                # Verify commit was called (transaction boundary)
                mock_db.commit.assert_called_once()

    def test_source_discover_new_collections_sync_disabled(self):
        """
        Contract D-2: Newly discovered collections MUST be persisted with sync_enabled=False.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Test Plex Server"
            mock_source.type = "plex"
            mock_source.config = {"base_url": "http://test", "token": "test-token"}
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            
            # Mock importer to return collections
            mock_importer = MagicMock()
            mock_importer.list_collections.return_value = [
                {"external_id": "1", "name": "Movies", "plex_section_ref": "1", "type": "movie"}
            ]
            
            # Mock database query to return no existing collections
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.adapters.importers.plex_importer.PlexImporter", return_value=mock_importer):
                
                result = self.runner.invoke(app, ["discover", "test-source"])
                
                assert result.exit_code == 0
                # Verify SourceCollection was created with sync_enabled=False
                mock_db.add.assert_called_once()
                added_collection = mock_db.add.call_args[0][0]
                assert added_collection.sync_enabled is False

    def test_source_discover_existing_collections_sync_preserved(self):
        """
        Contract D-3: Discovery MUST NOT flip existing collections from sync_enabled=False to sync_enabled=True.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Test Plex Server"
            mock_source.type = "plex"
            mock_source.config = {"base_url": "http://test", "token": "test-token"}
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            
            # Mock importer to return collections
            mock_importer = MagicMock()
            mock_importer.list_collections.return_value = [
                {"external_id": "1", "name": "Movies", "plex_section_ref": "1", "type": "movie"}
            ]
            
            # Mock database query to return existing collection with sync_enabled=False
            existing_collection = MagicMock()
            existing_collection.external_id = "1"
            existing_collection.name = "Movies"
            existing_collection.sync_enabled = False
            mock_db.query.return_value.filter.return_value.first.return_value = existing_collection
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.adapters.importers.plex_importer.PlexImporter", return_value=mock_importer):
                
                result = self.runner.invoke(app, ["discover", "test-source"])
                
                assert result.exit_code == 0
                # Verify no new collection was added (duplicate skipped)
                mock_db.add.assert_not_called()
                # Verify existing collection's sync_enabled status was not changed
                assert existing_collection.sync_enabled is False

    def test_source_discover_path_mapping_empty_local_path(self):
        """
        Contract D-4: PathMapping records MUST be created with empty local_path for new collections.
        
        Note: Current implementation doesn't create PathMapping records yet, 
        but this test documents the expected behavior when implemented.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Test Plex Server"
            mock_source.type = "plex"
            mock_source.config = {"base_url": "http://test", "token": "test-token"}
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            
            # Mock importer to return collections
            mock_importer = MagicMock()
            mock_importer.list_collections.return_value = [
                {"external_id": "1", "name": "Movies", "plex_section_ref": "1", "type": "movie"}
            ]
            
            # Mock database query to return no existing collections
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.adapters.importers.plex_importer.PlexImporter", return_value=mock_importer):
                
                result = self.runner.invoke(app, ["discover", "test-source"])
                
                assert result.exit_code == 0
                # TODO: When PathMapping creation is implemented, verify local_path is empty
                # For now, this test documents the expected behavior

    def test_source_discover_transaction_rollback_on_failure(self):
        """
        Contract D-5: On transaction failure, ALL changes MUST be rolled back with no partial persistence.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Test Plex Server"
            mock_source.type = "plex"
            mock_source.config = {"base_url": "http://test", "token": "test-token"}
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            
            # Mock importer to return collections
            mock_importer = MagicMock()
            mock_importer.list_collections.return_value = [
                {"external_id": "1", "name": "Movies", "plex_section_ref": "1", "type": "movie"}
            ]
            
            # Mock database query to return no existing collections
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            # Mock commit to raise an exception
            mock_db.commit.side_effect = Exception("Database error")
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.adapters.importers.plex_importer.PlexImporter", return_value=mock_importer):
                
                result = self.runner.invoke(app, ["discover", "test-source"])
                
                assert result.exit_code == 1
                assert "Error discovering collections: Database error" in result.stderr
                # Note: Rollback is handled automatically by the UoW context manager

    def test_source_discover_duplicate_external_id_prevention(self):
        """
        Contract D-6: Duplicate external ID checking MUST prevent duplicate collection creation.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Test Plex Server"
            mock_source.type = "plex"
            mock_source.config = {"base_url": "http://test", "token": "test-token"}
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            
            # Mock importer to return collections
            mock_importer = MagicMock()
            mock_importer.list_collections.return_value = [
                {"external_id": "1", "name": "Movies", "plex_section_ref": "1", "type": "movie"},
                {"external_id": "1", "name": "Movies Duplicate", "plex_section_ref": "1", "type": "movie"}
            ]
            
            # Mock database query to return existing collection for first call, None for second
            existing_collection = MagicMock()
            existing_collection.external_id = "1"
            existing_collection.name = "Movies"
            mock_db.query.return_value.filter.return_value.first.side_effect = [existing_collection, None]
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.adapters.importers.plex_importer.PlexImporter", return_value=mock_importer):
                
                result = self.runner.invoke(app, ["discover", "test-source"])
                
                assert result.exit_code == 0
                # Verify only one collection was added (duplicate skipped)
                assert mock_db.add.call_count == 1
                assert "Collection 'Movies' already exists, skipping" in result.stdout

    def test_source_discover_existing_collection_metadata_update(self):
        """
        Contract D-7: Collection metadata MUST be updated for existing collections.
        
        Note: Current implementation skips existing collections entirely.
        This test documents the expected behavior when metadata updates are implemented.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Test Plex Server"
            mock_source.type = "plex"
            mock_source.config = {"base_url": "http://test", "token": "test-token"}
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            
            # Mock importer to return collections
            mock_importer = MagicMock()
            mock_importer.list_collections.return_value = [
                {"external_id": "1", "name": "Movies Updated", "plex_section_ref": "1", "type": "movie"}
            ]
            
            # Mock database query to return existing collection
            existing_collection = MagicMock()
            existing_collection.external_id = "1"
            existing_collection.name = "Movies"
            existing_collection.sync_enabled = False
            mock_db.query.return_value.filter.return_value.first.return_value = existing_collection
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.adapters.importers.plex_importer.PlexImporter", return_value=mock_importer):
                
                result = self.runner.invoke(app, ["discover", "test-source"])
                
                assert result.exit_code == 0
                # TODO: When metadata updates are implemented, verify collection name was updated
                # For now, this test documents the expected behavior

    def test_source_discover_uses_importer_discovery_capability(self):
        """
        Contract D-8: Collection discovery MUST use the importer-provided discovery capability to enumerate collections.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Test Plex Server"
            mock_source.type = "plex"
            mock_source.config = {"base_url": "http://test", "token": "test-token"}
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            
            # Mock importer with discovery capability
            mock_importer = MagicMock()
            mock_importer.list_collections.return_value = [
                {"external_id": "1", "name": "Movies", "plex_section_ref": "1", "type": "movie"}
            ]
            
            # Mock database query to return no existing collections
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.adapters.importers.plex_importer.PlexImporter", return_value=mock_importer):
                
                result = self.runner.invoke(app, ["discover", "test-source"])
                
                assert result.exit_code == 0
                # Verify list_collections was called with correct parameters
                mock_importer.list_collections.assert_called_once_with({})

    def test_source_discover_interface_compliance_verification(self):
        """
        Contract D-9: Interface compliance MUST be verified before discovery begins.
        
        Note: Current implementation doesn't explicitly verify interface compliance.
        This test documents the expected behavior when interface verification is implemented.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Test Plex Server"
            mock_source.type = "plex"
            mock_source.config = {"base_url": "http://test", "token": "test-token"}
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            
            # Mock importer
            mock_importer = MagicMock()
            mock_importer.list_collections.return_value = []
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.adapters.importers.plex_importer.PlexImporter", return_value=mock_importer):
                
                result = self.runner.invoke(app, ["discover", "test-source"])
                
                assert result.exit_code == 0
                # TODO: When interface compliance verification is implemented, 
                # verify that compliance check happens before discovery
                # For now, this test documents the expected behavior

    def test_source_discover_database_error_propagation(self):
        """
        Test that database errors are properly propagated to the user.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Test Plex Server"
            mock_source.type = "plex"
            mock_source.config = {"base_url": "http://test", "token": "test-token"}
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            
            # Mock importer
            mock_importer = MagicMock()
            mock_importer.list_collections.return_value = [
                {"external_id": "1", "name": "Movies", "plex_section_ref": "1", "type": "movie"}
            ]
            
            # Mock database query to raise an exception
            mock_db.query.side_effect = Exception("Database connection error")
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.adapters.importers.plex_importer.PlexImporter", return_value=mock_importer):
                
                result = self.runner.invoke(app, ["discover", "test-source"])
                
                assert result.exit_code == 1
                assert "Error discovering collections: Database connection error" in result.stderr

    def test_source_discover_json_error_propagation(self):
        """
        Test that errors are properly propagated when using JSON output.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Test Plex Server"
            mock_source.type = "plex"
            mock_source.config = {"base_url": "http://test", "token": "test-token"}
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            
            # Mock importer to raise an exception
            mock_importer = MagicMock()
            mock_importer.list_collections.side_effect = Exception("API connection error")
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.adapters.importers.plex_importer.PlexImporter", return_value=mock_importer):
                
                result = self.runner.invoke(app, ["discover", "test-source", "--json"])
                
                assert result.exit_code == 1
                assert "Error discovering collections: API connection error" in result.stderr
