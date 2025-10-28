"""
Data contract tests for `retrovue enricher remove` command.

Tests data-layer consistency, database operations, and cascade deletion
as specified in docs/contracts/EnricherRemove.md.

This test enforces the data contract rules (D-#) for the enricher remove command.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from retrovue.cli.main import app


class TestEnricherRemoveDataContract:
    """Data contract tests for retrovue enricher remove command."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_enricher_remove_cascade_collection_attachments(self):
        """
        Contract D-1: Enricher removal MUST cascade delete all associated collection attachment records.
        """
        with patch("retrovue.cli.commands.enricher.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock enricher exists
            mock_enricher = MagicMock()
            mock_enricher.enricher_id = "enricher-ffprobe-a1b2c3d4"
            mock_enricher.type = "ffprobe"
            mock_enricher.name = "Video Analysis"
            mock_enricher.scope = "ingest"
            
            mock_query = MagicMock()
            mock_query.first.return_value = mock_enricher
            mock_db.query.return_value.filter.return_value = mock_query
            
            result = self.runner.invoke(app, ["enricher", "remove", "enricher-ffprobe-a1b2c3d4", "--force"])
            
            assert result.exit_code == 0
            
            # Verify database operations were called
            mock_db.query.assert_called()
            # TODO: Verify cascade deletion when implemented

    def test_enricher_remove_cascade_channel_attachments(self):
        """
        Contract D-2: Enricher removal MUST cascade delete all associated channel attachment records.
        """
        with patch("retrovue.cli.commands.enricher.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock enricher exists
            mock_enricher = MagicMock()
            mock_enricher.enricher_id = "enricher-playout-c3d4e5f6"
            mock_enricher.type = "playout"
            mock_enricher.name = "Channel Branding"
            mock_enricher.scope = "playout"
            
            mock_query = MagicMock()
            mock_query.first.return_value = mock_enricher
            mock_db.query.return_value.filter.return_value = mock_query
            
            result = self.runner.invoke(app, ["enricher", "remove", "enricher-playout-c3d4e5f6", "--force"])
            
            assert result.exit_code == 0
            
            # Verify database operations were called
            mock_db.query.assert_called()
            # TODO: Verify cascade deletion when implemented

    def test_enricher_remove_transaction_boundary(self):
        """
        Contract D-3: All removal operations MUST occur within a single transaction boundary.
        """
        with patch("retrovue.cli.commands.enricher.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock enricher exists
            mock_enricher = MagicMock()
            mock_enricher.enricher_id = "enricher-ffprobe-a1b2c3d4"
            mock_enricher.type = "ffprobe"
            mock_enricher.name = "Video Analysis"
            mock_enricher.scope = "ingest"
            
            mock_query = MagicMock()
            mock_query.first.return_value = mock_enricher
            mock_db.query.return_value.filter.return_value = mock_query
            
            result = self.runner.invoke(app, ["enricher", "remove", "enricher-ffprobe-a1b2c3d4", "--force"])
            
            assert result.exit_code == 0
            
            # Verify transaction operations
            mock_session.assert_called_once()
            mock_db.delete.assert_called_once_with(mock_enricher)
            mock_db.commit.assert_called_once()

    def test_enricher_remove_transaction_rollback_on_failure(self):
        """
        Contract D-4: On transaction failure, ALL changes MUST be rolled back with no partial deletions.
        """
        with patch("retrovue.cli.commands.enricher.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock enricher exists
            mock_enricher = MagicMock()
            mock_enricher.enricher_id = "enricher-ffprobe-a1b2c3d4"
            mock_enricher.type = "ffprobe"
            mock_enricher.name = "Video Analysis"
            mock_enricher.scope = "ingest"
            
            mock_query = MagicMock()
            mock_query.first.return_value = mock_enricher
            mock_db.query.return_value.filter.return_value = mock_query
            
            # Mock database error during removal
            mock_db.delete.side_effect = Exception("Database constraint violation")
            
            result = self.runner.invoke(app, ["enricher", "remove", "enricher-ffprobe-a1b2c3d4", "--force"])
            
            assert result.exit_code == 1
            assert "Error removing enricher" in result.stderr
            
            # Verify rollback was called
            mock_db.rollback.assert_called_once()

    def test_enricher_remove_production_safety_check(self):
        """
        Contract D-5: An Enricher MUST NOT be removed in production if it has been used 
        in any active ingest or playout operations. --force MUST NOT override this rule.
        
        NOTE: This test is currently skipped because production safety checks are not yet implemented.
        """
        pytest.skip("Production safety checks not yet implemented - TODO")

    def test_enricher_remove_audit_logging(self):
        """
        Contract D-6: Removal MUST be logged with enricher details, collection count, and channel count.
        """
        with patch("retrovue.cli.commands.enricher.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock enricher exists
            mock_enricher = MagicMock()
            mock_enricher.enricher_id = "enricher-ffprobe-a1b2c3d4"
            mock_enricher.type = "ffprobe"
            mock_enricher.name = "Video Analysis"
            mock_enricher.scope = "ingest"
            
            mock_query = MagicMock()
            mock_query.first.return_value = mock_enricher
            mock_db.query.return_value.filter.return_value = mock_query
            
            result = self.runner.invoke(app, ["enricher", "remove", "enricher-ffprobe-a1b2c3d4", "--force"])
            
            assert result.exit_code == 0
            
            # TODO: Verify audit logging when implemented

    def test_enricher_remove_verifies_existence(self):
        """
        Contract D-7: The command MUST verify enricher existence before attempting removal.
        """
        with patch("retrovue.cli.commands.enricher.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock enricher not found
            mock_query = MagicMock()
            mock_query.first.return_value = None
            mock_db.query.return_value.filter.return_value = mock_query
            
            result = self.runner.invoke(app, ["enricher", "remove", "enricher-nonexistent-123", "--force"])
            
            assert result.exit_code == 1
            assert "Error removing enricher" in result.stderr
            
            # Verify existence check was performed
            mock_db.query.assert_called()

    def test_enricher_remove_database_error_propagation(self):
        """
        Contract: Database errors MUST be properly propagated to the CLI layer.
        """
        with patch("retrovue.cli.commands.enricher.session") as mock_session:
            mock_session.side_effect = Exception("Database connection failed")
            
            result = self.runner.invoke(app, ["enricher", "remove", "enricher-ffprobe-a1b2c3d4", "--force"])
            
            assert result.exit_code == 1
            assert "Error removing enricher" in result.stderr

    def test_enricher_remove_json_error_propagation(self):
        """
        Contract: Database errors MUST be properly propagated in JSON format.
        """
        with patch("retrovue.cli.commands.enricher.session") as mock_session:
            mock_session.side_effect = Exception("Database access denied")
            
            result = self.runner.invoke(app, ["enricher", "remove", "enricher-ffprobe-a1b2c3d4", "--force", "--json"])
            
            assert result.exit_code == 1
            # JSON output should not be produced on error
            try:
                json.loads(result.stdout)
                pytest.fail("JSON should not be produced on error")
            except json.JSONDecodeError:
                pass  # Expected behavior

    def test_enricher_remove_cascade_count_calculation(self):
        """
        Contract: The command MUST calculate and report cascade impact counts accurately.
        """
        with patch("retrovue.cli.commands.enricher.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock enricher exists
            mock_enricher = MagicMock()
            mock_enricher.enricher_id = "enricher-ffprobe-a1b2c3d4"
            mock_enricher.type = "ffprobe"
            mock_enricher.name = "Video Analysis"
            mock_enricher.scope = "ingest"
            
            mock_query = MagicMock()
            mock_query.first.return_value = mock_enricher
            mock_db.query.return_value.filter.return_value = mock_query
            
            result = self.runner.invoke(app, ["enricher", "remove", "enricher-ffprobe-a1b2c3d4", "--force", "--json"])
            
            assert result.exit_code == 0
            
            # Parse JSON output
            output_data = json.loads(result.stdout)
            
            # Should include cascade counts
            assert "collection_attachments_removed" in output_data
            assert "channel_attachments_removed" in output_data
            assert isinstance(output_data["collection_attachments_removed"], int)
            assert isinstance(output_data["channel_attachments_removed"], int)

    def test_enricher_remove_atomic_operation(self):
        """
        Contract: Removal operations MUST be atomic - either all succeed or all fail.
        """
        with patch("retrovue.cli.commands.enricher.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock enricher exists
            mock_enricher = MagicMock()
            mock_enricher.enricher_id = "enricher-ffprobe-a1b2c3d4"
            mock_enricher.type = "ffprobe"
            mock_enricher.name = "Video Analysis"
            mock_enricher.scope = "ingest"
            
            mock_query = MagicMock()
            mock_query.first.return_value = mock_enricher
            mock_db.query.return_value.filter.return_value = mock_query
            
            result = self.runner.invoke(app, ["enricher", "remove", "enricher-ffprobe-a1b2c3d4", "--force"])
            
            assert result.exit_code == 0
            
            # Verify atomic operation
            mock_session.assert_called_once()
            # TODO: Verify commit/rollback when implemented
