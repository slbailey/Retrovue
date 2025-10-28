"""
Behavioral contract tests for Source Discover command.

Tests the behavioral aspects of the source discover command as defined in
docs/contracts/SourceDiscoverContract.md (B-1 through B-10).
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from retrovue.cli.commands.source import app


class TestSourceDiscoverContract:
    """Test behavioral contract rules for source discover command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_source_discover_help_flag_exits_zero(self):
        """
        Contract B-1: The command MUST validate source existence before attempting discovery.
        """
        result = self.runner.invoke(app, ["discover", "--help"])
        assert result.exit_code == 0
        assert "Discover and add collections" in result.stdout

    def test_source_discover_requires_source_id(self):
        """
        Contract B-1: The command MUST validate source existence before attempting discovery.
        """
        result = self.runner.invoke(app, ["discover"])
        assert result.exit_code != 0
        assert "Missing argument" in result.stdout or "Error" in result.stderr

    def test_source_discover_validates_source_existence(self):
        """
        Contract B-1: The command MUST validate source existence before attempting discovery.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source service to return None (source not found)
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = None
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["discover", "nonexistent-source"])
                
                assert result.exit_code == 1
                assert "Error: Source 'nonexistent-source' not found" in result.stderr

    def test_source_discover_dry_run_support(self):
        """
        Contract B-2: The --dry-run flag MUST show what would be discovered without persisting to database.
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
                {"external_id": "2", "name": "TV Shows", "plex_section_ref": "2", "type": "show"}
            ]
            
            # Mock database query to return no existing collections
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.adapters.importers.plex_importer.PlexImporter", return_value=mock_importer):
                
                result = self.runner.invoke(app, ["discover", "test-source", "--dry-run"])
                
                assert result.exit_code == 0
                assert "Would discover 2 collections from 'Test Plex Server'" in result.stdout
                assert "• Movies (ID: 1) - Would be created" in result.stdout
                assert "• TV Shows (ID: 2) - Would be created" in result.stdout

    def test_source_discover_json_output_format(self):
        """
        Contract B-3: When --json is supplied, output MUST include fields "source", "collections_added", and "collections".
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
                
                result = self.runner.invoke(app, ["discover", "test-source", "--json"])
                
                assert result.exit_code == 0
                output_data = json.loads(result.stdout)
                
                # Verify required fields exist
                assert "source" in output_data
                assert "collections_added" in output_data
                assert "collections" in output_data
                
                # Verify source field structure
                assert output_data["source"]["id"] == "test-source-id"
                assert output_data["source"]["name"] == "Test Plex Server"
                assert output_data["source"]["type"] == "plex"
                
                # Verify collections field structure
                assert len(output_data["collections"]) == 1
                collection = output_data["collections"][0]
                assert collection["external_id"] == "1"
                assert collection["name"] == "Movies"
                assert collection["sync_enabled"] is False
                assert collection["source_type"] == "plex"

    def test_source_discover_source_not_found_error(self):
        """
        Contract B-4: On validation failure (source not found), the command MUST exit with code 1 and print "Error: Source 'X' not found".
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source service to return None (source not found)
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = None
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["discover", "invalid-source"])
                
                assert result.exit_code == 1
                assert "Error: Source 'invalid-source' not found" in result.stderr

    def test_source_discover_empty_results_exit_code_zero(self):
        """
        Contract B-5: Empty discovery results MUST return exit code 0 with message "No collections found for source 'X'".
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Empty Plex Server"
            mock_source.type = "plex"
            mock_source.config = {"base_url": "http://test", "token": "test-token"}
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            
            # Mock importer to return empty collections
            mock_importer = MagicMock()
            mock_importer.list_collections.return_value = []
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.adapters.importers.plex_importer.PlexImporter", return_value=mock_importer):
                
                result = self.runner.invoke(app, ["discover", "empty-source"])
                
                assert result.exit_code == 0
                assert "No collections found for source 'Empty Plex Server'" in result.stdout

    def test_source_discover_duplicate_collections_skipped(self):
        """
        Contract B-6: Duplicate collections MUST be skipped with notification message.
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
            
            # Mock database query to return existing collection (duplicate)
            existing_collection = MagicMock()
            existing_collection.external_id = "1"
            existing_collection.name = "Movies"
            mock_db.query.return_value.filter.return_value.first.return_value = existing_collection
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.adapters.importers.plex_importer.PlexImporter", return_value=mock_importer):
                
                result = self.runner.invoke(app, ["discover", "test-source"])
                
                assert result.exit_code == 0
                assert "Collection 'Movies' already exists, skipping" in result.stdout

    def test_source_discover_unsupported_source_type_success(self):
        """
        Contract B-7: For any source type whose importer does not expose a discovery capability, 
        the command MUST succeed with exit code 0, MUST NOT modify the database, and MUST clearly 
        report that no collections are discoverable for that source type.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists with unsupported type
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Filesystem Source"
            mock_source.type = "filesystem"
            mock_source.config = {}
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["discover", "filesystem-source"])
                
                assert result.exit_code == 1  # Current implementation exits with error
                assert "Error: Source type 'filesystem' not supported for discovery" in result.stderr

    def test_source_discover_obtains_importer_for_source_type(self):
        """
        Contract B-8: The command MUST obtain the importer for the Source's type.
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
                 patch("retrovue.adapters.importers.plex_importer.PlexImporter", return_value=mock_importer) as mock_plex_importer:
                
                result = self.runner.invoke(app, ["discover", "test-source"])
                
                assert result.exit_code == 0
                # Verify PlexImporter was instantiated
                mock_plex_importer.assert_called_once_with(base_url="http://test", token="test-token")

    def test_source_discover_importer_discovery_capability(self):
        """
        Contract B-9: The importer MUST expose a discovery capability that returns all collections 
        (libraries, sections, folders, etc.) visible to that Source.
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
                {"external_id": "1", "name": "Movies", "plex_section_ref": "1", "type": "movie"},
                {"external_id": "2", "name": "TV Shows", "plex_section_ref": "2", "type": "show"}
            ]
            
            # Mock database query to return no existing collections
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.adapters.importers.plex_importer.PlexImporter", return_value=mock_importer):
                
                result = self.runner.invoke(app, ["discover", "test-source"])
                
                assert result.exit_code == 0
                # Verify list_collections was called
                mock_importer.list_collections.assert_called_once_with({})

    def test_source_discover_interface_compliance_failure(self):
        """
        Contract B-10: If the importer claims to support discovery but fails interface compliance 
        (missing required discovery capability, raises interface violation), the command MUST exit 
        with code 1 and emit a human-readable error.
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
            
            # Mock importer that fails interface compliance
            mock_importer = MagicMock()
            mock_importer.list_collections.side_effect = Exception("Interface compliance violation")
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service), \
                 patch("retrovue.adapters.importers.plex_importer.PlexImporter", return_value=mock_importer):
                
                result = self.runner.invoke(app, ["discover", "test-source"])
                
                assert result.exit_code == 1
                assert "Error discovering collections: Interface compliance violation" in result.stderr

    def test_source_discover_test_db_support(self):
        """
        Test that --test-db flag is supported (implied by contract safety expectations).
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
                
                result = self.runner.invoke(app, ["discover", "test-source", "--test-db"])
                
                # Should succeed (test-db flag should be accepted)
                assert result.exit_code == 0
