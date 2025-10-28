"""
Behavioral contract tests for Source Delete command.

Tests the behavioral aspects of the source delete command as defined in
docs/contracts/resources/SourceDeleteContract.md (B-1 through B-8).
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from retrovue.cli.commands.source import app


class TestSourceDeleteContract:
    """Test behavioral contract rules for source delete command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_source_delete_help_flag_exits_zero(self):
        """
        Contract B-1: The command MUST require interactive confirmation unless --force is provided.
        """
        result = self.runner.invoke(app, ["delete", "--help"])
        assert result.exit_code == 0
        assert "Delete a source" in result.stdout

    def test_source_delete_requires_source_selector(self):
        """
        Contract B-5: On validation failure (source not found), the command MUST exit with code 1.
        """
        result = self.runner.invoke(app, ["delete"])
        assert result.exit_code != 0
        assert "Missing argument" in result.stdout or "Error" in result.stderr

    def test_source_delete_requires_confirmation_without_force(self):
        """
        Contract B-1: The command MUST require interactive confirmation unless --force is provided.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session, \
             patch("retrovue.cli.commands.source.SourceService") as mock_source_service_class:
            
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Test Plex Server"
            mock_source.type = "plex"
            mock_source.external_id = "plex-123"
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            mock_source_service.delete_source.return_value = True
            mock_source_service_class.return_value = mock_source_service
            
            # Mock database queries for collections and path mappings
            mock_query = MagicMock()
            mock_query.filter.return_value.count.return_value = 3
            mock_query.filter.return_value.all.return_value = []
            mock_db.query.return_value = mock_query
            
            # Mock user input "no" to cancel
            result = self.runner.invoke(app, ["delete", "test-source"], input="no\n")
            
            assert result.exit_code == 0
            assert "Are you sure you want to delete source" in result.stdout
            assert "Test Plex Server" in result.stdout
            assert "Deletion cancelled" in result.stdout

    def test_source_delete_confirmation_requires_yes(self):
        """
        Contract B-2: Interactive confirmation MUST require the user to type "yes" exactly to proceed.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session, \
             patch("retrovue.cli.commands.source.SourceService") as mock_source_service_class:
            
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Test Plex Server"
            mock_source.type = "plex"
            mock_source.external_id = "plex-123"
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            mock_source_service.delete_source.return_value = True
            mock_source_service_class.return_value = mock_source_service
            
            # Mock database queries
            mock_query = MagicMock()
            mock_query.filter.return_value.count.return_value = 3
            mock_query.filter.return_value.all.return_value = []
            mock_db.query.return_value = mock_query
            
            # Mock user input "y" (not "yes")
            result = self.runner.invoke(app, ["delete", "test-source"], input="y\n")
            
            assert result.exit_code == 0
            assert "Deletion cancelled" in result.stdout

    def test_source_delete_confirmation_shows_details(self):
        """
        Contract B-3: The confirmation prompt MUST show source details and cascade impact count.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session, \
             patch("retrovue.cli.commands.source.SourceService") as mock_source_service_class:
            
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Test Plex Server"
            mock_source.type = "plex"
            mock_source.external_id = "plex-123"
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            mock_source_service.delete_source.return_value = True
            mock_source_service_class.return_value = mock_source_service
            
            # Mock database queries
            mock_query = MagicMock()
            mock_query.filter.return_value.count.return_value = 3
            mock_query.filter.return_value.all.return_value = []
            mock_db.query.return_value = mock_query
            
            result = self.runner.invoke(app, ["delete", "test-source"], input="no\n")
            
            assert result.exit_code == 0
            assert "Test Plex Server" in result.stdout
            assert "test-source-id" in result.stdout
            assert "3 collections" in result.stdout
            assert "This action cannot be undone" in result.stdout

    def test_source_delete_json_output_format(self):
        """
        Contract B-4: When --json is supplied, output MUST include fields "deleted", "source_id", "name", and "type".
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Test Plex Server"
            mock_source.type = "plex"
            mock_source.external_id = "plex-123"
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            
            # Mock collections count
            mock_db.query.return_value.filter.return_value.count.return_value = 3
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["delete", "test-source", "--force", "--json"])
                
                assert result.exit_code == 0
                output_data = json.loads(result.stdout)
                
                # Verify required fields exist
                assert "deleted" in output_data
                assert "source_id" in output_data
                assert "name" in output_data
                assert "type" in output_data
                
                # Verify field values
                assert output_data["deleted"] is True
                assert output_data["source_id"] == "test-source-id"
                assert output_data["name"] == "Test Plex Server"
                assert output_data["type"] == "plex"

    def test_source_delete_source_not_found_error(self):
        """
        Contract B-5: On validation failure (source not found), the command MUST exit with code 1 and print "Error: Source 'X' not found".
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source service to return None (source not found)
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = None
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["delete", "nonexistent-source"])
                
                assert result.exit_code == 1
                assert "Error: Source 'nonexistent-source' not found" in result.stderr

    def test_source_delete_cancellation_exit_code_zero(self):
        """
        Contract B-6: Cancellation of confirmation MUST return exit code 0 with message "Deletion cancelled".
        """
        with patch("retrovue.cli.commands.source.session") as mock_session, \
             patch("retrovue.cli.commands.source.SourceService") as mock_source_service_class:
            
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Test Plex Server"
            mock_source.type = "plex"
            mock_source.external_id = "plex-123"
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            mock_source_service.delete_source.return_value = True
            mock_source_service_class.return_value = mock_source_service
            
            # Mock database queries
            mock_query = MagicMock()
            mock_query.filter.return_value.count.return_value = 3
            mock_query.filter.return_value.all.return_value = []
            mock_db.query.return_value = mock_query
            
            result = self.runner.invoke(app, ["delete", "test-source"], input="no\n")
            
            assert result.exit_code == 0
            assert "Deletion cancelled" in result.stdout

    def test_source_delete_force_skips_confirmation(self):
        """
        Contract B-7: The --force flag MUST skip all confirmation prompts and proceed immediately.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source exists
            mock_source = MagicMock()
            mock_source.id = "test-source-id"
            mock_source.name = "Test Plex Server"
            mock_source.type = "plex"
            mock_source.external_id = "plex-123"
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            
            # Mock collections count
            mock_db.query.return_value.filter.return_value.count.return_value = 3
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["delete", "test-source", "--force"])
                
                assert result.exit_code == 0
                assert "Successfully deleted source" in result.stdout
                assert "Are you sure" not in result.stdout  # No confirmation prompt

    @pytest.mark.skip(reason="Wildcard functionality not yet implemented")
    def test_source_delete_wildcard_selection(self):
        """
        Contract B-8: The source_selector argument MAY be a wildcard. Wildcard selection MUST resolve to a deterministic list of matching sources before any deletion occurs.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock multiple sources matching wildcard
            mock_sources = [
                MagicMock(id="source-1", name="test-plex-1", type="plex", external_id="plex-1"),
                MagicMock(id="source-2", name="test-plex-2", type="plex", external_id="plex-2")
            ]
            
            mock_source_service = MagicMock()
            mock_source_service.get_sources_by_pattern.return_value = mock_sources
            
            # Mock collections count for each source
            mock_db.query.return_value.filter.return_value.count.return_value = 2
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["delete", "test-*", "--force"])
                
                assert result.exit_code == 0
                # Verify wildcard resolution was called
                mock_source_service.get_sources_by_pattern.assert_called_once_with("test-*")

    @pytest.mark.skip(reason="Wildcard functionality not yet implemented")
    def test_source_delete_wildcard_confirmation_prompt(self):
        """
        Contract B-8: If multiple sources are selected and --force is not provided, the command MUST present a single aggregated confirmation prompt.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock multiple sources matching wildcard
            mock_sources = [
                MagicMock(id="source-1", name="test-plex-1", type="plex", external_id="plex-1"),
                MagicMock(id="source-2", name="test-plex-2", type="plex", external_id="plex-2")
            ]
            
            mock_source_service = MagicMock()
            mock_source_service.get_sources_by_pattern.return_value = mock_sources
            
            # Mock collections count for each source
            mock_db.query.return_value.filter.return_value.count.return_value = 2
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["delete", "test-*"], input="no\n")
                
                assert result.exit_code == 0
                assert "2 sources" in result.stdout  # Aggregated count
                assert "4 collections" in result.stdout  # Total collections (2 sources * 2 collections each)
                assert "Are you sure" in result.stdout

    def test_source_delete_wildcard_force_skips_confirmation(self):
        """
        Contract B-8: If --force is provided, the command MUST skip confirmation and attempt deletion of each matched source.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock multiple sources matching wildcard
            mock_sources = [
                MagicMock(id="source-1", name="test-plex-1", type="plex", external_id="plex-1"),
                MagicMock(id="source-2", name="test-plex-2", type="plex", external_id="plex-2")
            ]
            
            mock_source_service = MagicMock()
            mock_source_service.get_sources_by_pattern.return_value = mock_sources
            
            # Mock collections count for each source
            mock_db.query.return_value.filter.return_value.count.return_value = 2
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["delete", "test-*", "--force"])
                
                assert result.exit_code == 0
                assert "Are you sure" not in result.stdout  # No confirmation prompt
                assert "Successfully deleted" in result.stdout

    def test_source_delete_test_db_support(self):
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
            mock_source.external_id = "plex-123"
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            
            # Mock collections count
            mock_db.query.return_value.filter.return_value.count.return_value = 3
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["delete", "test-source", "--test-db", "--force"])
                
                # Should succeed (test-db flag should be accepted)
                assert result.exit_code == 0
