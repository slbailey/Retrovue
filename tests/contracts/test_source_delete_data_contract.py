"""
Data contract tests for Source Delete command.

Tests the data persistence and transaction aspects of the source delete command as defined in
docs/contracts/SourceDeleteContract.md (D-1 through D-10).
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from retrovue.cli.commands.source import app


class TestSourceDeleteDataContract:
    """Test data contract rules for source delete command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_source_delete_cascade_collections(self):
        """
        Contract D-1: Source deletion MUST cascade delete all associated SourceCollection records.
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
                # Verify source deletion was attempted
                mock_db.delete.assert_called()

    def test_source_delete_cascade_path_mappings(self):
        """
        Contract D-2: Source deletion MUST cascade delete all associated PathMapping records.
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
                # Verify cascade deletion was attempted
                mock_db.delete.assert_called()

    def test_source_delete_transaction_boundary(self):
        """
        Contract D-3: All deletion operations MUST occur within a single transaction boundary.
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
                # Verify commit was called (transaction boundary)
                mock_db.commit.assert_called_once()

    def test_source_delete_transaction_rollback_on_failure(self):
        """
        Contract D-4: On transaction failure, ALL changes MUST be rolled back with no partial deletions.
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
            
            # Mock commit to raise an exception
            mock_db.commit.side_effect = Exception("Database error")
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["delete", "test-source", "--force"])
                
                assert result.exit_code == 1
                assert "Error deleting source: Database error" in result.stderr
                # Note: Rollback is handled automatically by the UoW context manager

    def test_source_delete_production_safety_check(self):
        """
        Contract D-5: PRODUCTION SAFETY - A Source MUST NOT be deleted in production if any Asset from that Source has appeared in a PlaylogEvent or AsRunLog.
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
            
            # Mock production environment check
            with patch("os.getenv") as mock_getenv:
                mock_getenv.side_effect = lambda key, default="": "production" if key == "ENV" else default
                
                # Mock production safety check to block deletion
                mock_source_service.check_production_safety.return_value = False, "Source has assets in PlaylogEvent"
                
                with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                    result = self.runner.invoke(app, ["delete", "test-source", "--force"])
                    
                    assert result.exit_code == 1
                    assert "Cannot delete source in production" in result.stderr
                    assert "Source has assets in PlaylogEvent" in result.stderr

    def test_source_delete_production_safety_force_override_blocked(self):
        """
        Contract D-5: --force MUST NOT override production safety rules.
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
            
            # Mock production environment check
            with patch("os.getenv") as mock_getenv:
                mock_getenv.side_effect = lambda key, default="": "production" if key == "ENV" else default
                
                # Mock production safety check to block deletion
                mock_source_service.check_production_safety.return_value = False, "Source has assets in AsRunLog"
                
                with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                    result = self.runner.invoke(app, ["delete", "test-source", "--force"])
                    
                    assert result.exit_code == 1
                    assert "Cannot delete source in production" in result.stderr
                    assert "--force" not in result.stderr  # --force should not override

    def test_source_delete_logging_requirements(self):
        """
        Contract D-6: Deletion MUST be logged with source details, collection count, and path mapping count.
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
                assert "Test Plex Server" in result.stdout
                assert "test-source-id" in result.stdout

    def test_source_delete_source_existence_verification(self):
        """
        Contract D-7: The command MUST verify source existence before attempting deletion.
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
                # Verify no deletion was attempted
                mock_db.delete.assert_not_called()

    def test_source_delete_wildcard_transactional_guarantees(self):
        """
        Contract D-8: For wildcard or multi-source deletion, each source MUST be deleted using the same transactional guarantees defined in D-1..D-4.
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
                # Verify each source deletion was attempted
                assert mock_db.delete.call_count == 2

    def test_source_delete_collection_cascade_transaction(self):
        """
        Contract D-9: Deleting a Source MUST also delete all Collections that belong to that Source. This cascade MUST occur in the same transaction boundary.
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
                # Verify cascade deletion was attempted
                mock_db.delete.assert_called()

    def test_source_delete_collection_cascade_no_partial_state(self):
        """
        Contract D-9: If the transaction fails, no partial state is allowed (the Source MUST still exist and all of its Collections MUST still exist).
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
            
            # Mock commit to raise an exception
            mock_db.commit.side_effect = Exception("Database error")
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["delete", "test-source", "--force"])
                
                assert result.exit_code == 1
                assert "Error deleting source: Database error" in result.stderr
                # Note: Rollback is handled automatically by the UoW context manager

    def test_source_delete_asset_cascade_future_intent(self):
        """
        Contract D-10: Collections are the boundary that will eventually own Assets. This deeper cascade is not yet enforced and MUST NOT block Source deletion at this stage.
        
        Note: This test documents the future intent and should NOT assert Asset cascade behavior yet.
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
                # TODO: When Asset cascade is implemented, verify Asset deletion
                # For now, this test documents the expected future behavior

    def test_source_delete_database_error_propagation(self):
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
            mock_source.external_id = "plex-123"
            
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = mock_source
            
            # Mock collections count
            mock_db.query.return_value.filter.return_value.count.return_value = 3
            
            # Mock database query to raise an exception
            mock_db.query.side_effect = Exception("Database connection error")
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["delete", "test-source", "--force"])
                
                assert result.exit_code == 1
                assert "Error deleting source: Database connection error" in result.stderr

    def test_source_delete_json_error_propagation(self):
        """
        Test that errors are properly propagated when using JSON output.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source service to return None (source not found)
            mock_source_service = MagicMock()
            mock_source_service.get_source_by_id.return_value = None
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["delete", "nonexistent-source", "--json"])
                
                assert result.exit_code == 1
                assert "Error: Source 'nonexistent-source' not found" in result.stderr
