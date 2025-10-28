"""
Contract tests for SourceList command.

Tests the behavioral contract rules (B-#) defined in SourceListContract.md.
These tests verify CLI behavior, filtering, output formats, and read-only operation guarantees.
"""

import json
import pytest
import uuid
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from retrovue.cli.main import app


class TestSourceListContract:
    """Test SourceList contract behavioral rules (B-#)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_source_list_help_flag_exits_zero(self):
        """
        Contract: Help flag MUST exit with code 0.
        """
        result = self.runner.invoke(app, ["source", "list", "--help"])
        assert result.exit_code == 0
        assert "List all configured sources" in result.stdout

    def test_source_list_successful_execution_exits_zero(self):
        """
        Contract B-1: The command MUST return all known sources unless filtered.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock sources query
            mock_source1 = MagicMock()
            mock_source1.id = "4b2b05e7-d7d2-414a-a587-3f5df9b53f44"
            mock_source1.name = "My Plex Server"
            mock_source1.type = "plex"
            mock_source1.created_at = "2024-01-15T10:30:00Z"
            mock_source1.updated_at = "2024-01-20T14:45:00Z"
            
            mock_source2 = MagicMock()
            mock_source2.id = "8c3d12f4-e9a1-4b2c-d6e7-1f8a9b0c2d3e"
            mock_source2.name = "Local Media Library"
            mock_source2.type = "filesystem"
            mock_source2.created_at = "2024-01-10T09:15:00Z"
            mock_source2.updated_at = "2024-01-18T16:20:00Z"
            
            mock_db.query.return_value.all.return_value = [mock_source1, mock_source2]
            
            # Mock collection counts
            mock_db.query.return_value.filter.return_value.count.return_value = 2  # enabled_collections
            mock_db.query.return_value.filter.return_value.count.return_value = 1  # ingestible_collections
            
            result = self.runner.invoke(app, ["source", "list"])
            
            assert result.exit_code == 0
            assert "My Plex Server" in result.stdout
            assert "Local Media Library" in result.stdout
            assert "Total: 2 sources configured" in result.stdout

    def test_source_list_type_filter_valid_type(self):
        """
        Contract B-2: --type MUST restrict results to sources whose type exactly matches a known importer type.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock plex source only
            mock_source = MagicMock()
            mock_source.id = "4b2b05e7-d7d2-414a-a587-3f5df9b53f44"
            mock_source.name = "My Plex Server"
            mock_source.type = "plex"
            mock_source.created_at = "2024-01-15T10:30:00Z"
            mock_source.updated_at = "2024-01-20T14:45:00Z"
            
            mock_db.query.return_value.filter.return_value.all.return_value = [mock_source]
            
            # Mock collection counts
            mock_db.query.return_value.filter.return_value.count.return_value = 2
            
            result = self.runner.invoke(app, ["source", "list", "--type", "plex"])
            
            assert result.exit_code == 0
            assert "My Plex Server" in result.stdout
            assert "plex" in result.stdout
            assert "Total: 1 plex source configured" in result.stdout

    def test_source_list_type_filter_invalid_type_exits_one(self):
        """
        Contract B-3: --type with an unknown type MUST produce no data changes and MUST exit 1 with an error message.
        """
        with patch("retrovue.cli.commands.source.list_importers") as mock_list_importers:
            mock_list_importers.return_value = ["plex", "filesystem"]
            
            result = self.runner.invoke(app, ["source", "list", "--type", "unknown"])
            
            assert result.exit_code == 1
            assert "Unknown source type 'unknown'" in result.stderr
            assert "Available types: plex, filesystem" in result.stderr

    def test_source_list_json_output_format(self):
        """
        Contract B-4: --json MUST return valid JSON output with the required fields (status, total, sources).
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock source
            mock_source = MagicMock()
            mock_source.id = "4b2b05e7-d7d2-414a-a587-3f5df9b53f44"
            mock_source.name = "My Plex Server"
            mock_source.type = "plex"
            mock_source.created_at = "2024-01-15T10:30:00Z"
            mock_source.updated_at = "2024-01-20T14:45:00Z"
            
            mock_db.query.return_value.all.return_value = [mock_source]
            
            # Mock collection counts
            mock_db.query.return_value.filter.return_value.count.return_value = 2  # enabled_collections
            mock_db.query.return_value.filter.return_value.count.return_value = 1  # ingestible_collections
            
            result = self.runner.invoke(app, ["source", "list", "--json"])
            
            assert result.exit_code == 0
            
            # Parse JSON output
            output = json.loads(result.stdout)
            
            # Check required top-level fields
            assert "status" in output
            assert "total" in output
            assert "sources" in output
            
            assert output["status"] == "ok"
            assert output["total"] == 1
            assert len(output["sources"]) == 1
            
            # Check source object fields
            source = output["sources"][0]
            assert "id" in source
            assert "name" in source
            assert "type" in source
            assert "enabled_collections" in source
            assert "ingestible_collections" in source
            assert "created_at" in source
            assert "updated_at" in source

    def test_source_list_deterministic_ordering(self):
        """
        Contract B-5: The output MUST be deterministic. Results MUST be sorted by source name ascending (case-insensitive).
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock sources with different names
            mock_source1 = MagicMock()
            mock_source1.id = "1"
            mock_source1.name = "Zebra Server"
            mock_source1.type = "plex"
            mock_source1.created_at = "2024-01-15T10:30:00Z"
            mock_source1.updated_at = "2024-01-20T14:45:00Z"
            
            mock_source2 = MagicMock()
            mock_source2.id = "2"
            mock_source2.name = "apple server"
            mock_source2.type = "filesystem"
            mock_source2.created_at = "2024-01-10T09:15:00Z"
            mock_source2.updated_at = "2024-01-18T16:20:00Z"
            
            mock_source3 = MagicMock()
            mock_source3.id = "3"
            mock_source3.name = "Apple Server"  # Same name as source2, different case
            mock_source3.type = "plex"
            mock_source3.created_at = "2024-01-12T11:20:00Z"
            mock_source3.updated_at = "2024-01-19T13:30:00Z"
            
            # Sources should be returned in name order: apple server, Apple Server, Zebra Server
            mock_db.query.return_value.all.return_value = [mock_source2, mock_source3, mock_source1]
            
            # Mock collection counts
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            
            result = self.runner.invoke(app, ["source", "list"])
            
            assert result.exit_code == 0
            
            # Check that sources appear in alphabetical order by name
            output_lines = result.stdout.split('\n')
            source_lines = [line for line in output_lines if 'Name:' in line]
            
            assert len(source_lines) == 3
            assert "apple server" in source_lines[0]
            assert "Apple Server" in source_lines[1]
            assert "Zebra Server" in source_lines[2]

    def test_source_list_no_results_human_readable(self):
        """
        Contract B-6: When there are no results, output MUST still be structurally valid (empty table in human mode).
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock empty results
            mock_db.query.return_value.all.return_value = []
            
            result = self.runner.invoke(app, ["source", "list"])
            
            assert result.exit_code == 0
            assert "No sources configured" in result.stdout
            assert "Total: 0 sources configured" in result.stdout

    def test_source_list_no_results_json(self):
        """
        Contract B-6: When there are no results, output MUST still be structurally valid (empty list in JSON mode).
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock empty results
            mock_db.query.return_value.all.return_value = []
            
            result = self.runner.invoke(app, ["source", "list", "--json"])
            
            assert result.exit_code == 0
            
            # Parse JSON output
            output = json.loads(result.stdout)
            
            assert output["status"] == "ok"
            assert output["total"] == 0
            assert output["sources"] == []

    def test_source_list_read_only_operation(self):
        """
        Contract B-7: The command MUST be read-only and MUST NOT mutate database state, importer registry state, or collection ingest state.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock sources query
            mock_source = MagicMock()
            mock_source.id = "test-id"
            mock_source.name = "Test Source"
            mock_source.type = "plex"
            mock_source.created_at = "2024-01-15T10:30:00Z"
            mock_source.updated_at = "2024-01-20T14:45:00Z"
            
            mock_db.query.return_value.all.return_value = [mock_source]
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            
            result = self.runner.invoke(app, ["source", "list"])
            
            assert result.exit_code == 0
            
            # Verify only read operations were called
            mock_db.query.assert_called()
            mock_db.add.assert_not_called()
            mock_db.commit.assert_not_called()
            mock_db.delete.assert_not_called()

    def test_source_list_test_db_mode(self):
        """
        Contract B-8: --test-db MUST query the test DB session instead of production.
        Contract B-9: --test-db MUST keep response shape and exit code behavior identical to production mode.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock sources query
            mock_source = MagicMock()
            mock_source.id = "test-id"
            mock_source.name = "Test Source"
            mock_source.type = "plex"
            mock_source.created_at = "2024-01-15T10:30:00Z"
            mock_source.updated_at = "2024-01-20T14:45:00Z"
            
            mock_db.query.return_value.all.return_value = [mock_source]
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            
            result = self.runner.invoke(app, ["source", "list", "--test-db"])
            
            assert result.exit_code == 0
            assert "Test Source" in result.stdout
            assert "Total: 1 source configured" in result.stdout

    def test_source_list_test_db_json_mode(self):
        """
        Contract B-9: --test-db MUST keep response shape and exit code behavior identical to production mode.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock sources query
            mock_source = MagicMock()
            mock_source.id = "test-id"
            mock_source.name = "Test Source"
            mock_source.type = "plex"
            mock_source.created_at = "2024-01-15T10:30:00Z"
            mock_source.updated_at = "2024-01-20T14:45:00Z"
            
            mock_db.query.return_value.all.return_value = [mock_source]
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            
            result = self.runner.invoke(app, ["source", "list", "--test-db", "--json"])
            
            assert result.exit_code == 0
            
            # Parse JSON output
            output = json.loads(result.stdout)
            
            assert output["status"] == "ok"
            assert output["total"] == 1
            assert len(output["sources"]) == 1
            assert output["sources"][0]["name"] == "Test Source"

    def test_source_list_no_external_system_calls(self):
        """
        Contract B-10: The command MUST NOT call external systems (importers, Plex APIs, filesystem scans, etc.). It is metadata-only.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session, \
             patch("retrovue.cli.commands.source.get_importer") as mock_get_importer:
            
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock sources query
            mock_source = MagicMock()
            mock_source.id = "test-id"
            mock_source.name = "Test Source"
            mock_source.type = "plex"
            mock_source.created_at = "2024-01-15T10:30:00Z"
            mock_source.updated_at = "2024-01-20T14:45:00Z"
            
            mock_db.query.return_value.all.return_value = [mock_source]
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            
            result = self.runner.invoke(app, ["source", "list"])
            
            assert result.exit_code == 0
            
            # Verify no external system calls were made
            mock_get_importer.assert_not_called()

    def test_source_list_test_db_session_failure_exits_one(self):
        """
        Contract: --test-db session failure MUST exit with code 1.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock session failure
            mock_session.side_effect = Exception("Test database connection failed")
            
            result = self.runner.invoke(app, ["source", "list", "--test-db"])
            
            assert result.exit_code == 1
            assert "Error" in result.stderr

    def test_source_list_database_query_failure_exits_one(self):
        """
        Contract: Database query failure MUST exit with code 1.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock query failure
            mock_db.query.side_effect = Exception("Database query failed")
            
            result = self.runner.invoke(app, ["source", "list"])
            
            assert result.exit_code == 1
            assert "Error" in result.stderr

    def test_source_list_collection_counting_accuracy(self):
        """
        Contract: enabled_collections and ingestible_collections counts MUST be accurate.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session, \
             patch("retrovue.cli.commands.source.SourceService") as mock_source_service_class:
            
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock SourceService instance
            mock_source_service = MagicMock()
            mock_source_service_class.return_value = mock_source_service
            
            # Mock the return value from list_sources_with_collection_counts
            mock_source_service.list_sources_with_collection_counts.return_value = [
                {
                    "id": "test-id",
                    "name": "Test Source",
                    "type": "plex",
                    "enabled_collections": 3,
                    "ingestible_collections": 2,
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-20T14:45:00Z"
                }
            ]
            
            result = self.runner.invoke(app, ["source", "list", "--json"])
            
            assert result.exit_code == 0
            
            # Parse JSON output
            output = json.loads(result.stdout)
            
            source = output["sources"][0]
            assert source["enabled_collections"] == 3
            assert source["ingestible_collections"] == 2

    def test_source_list_multiple_sources_json_output(self):
        """
        Contract: JSON output MUST handle multiple sources correctly.
        """
        with patch("retrovue.cli.commands.source.session") as mock_session:
            # Mock database session
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Mock multiple sources
            mock_source1 = MagicMock()
            mock_source1.id = "id1"
            mock_source1.name = "Source 1"
            mock_source1.type = "plex"
            mock_source1.created_at = "2024-01-15T10:30:00Z"
            mock_source1.updated_at = "2024-01-20T14:45:00Z"
            
            mock_source2 = MagicMock()
            mock_source2.id = "id2"
            mock_source2.name = "Source 2"
            mock_source2.type = "filesystem"
            mock_source2.created_at = "2024-01-10T09:15:00Z"
            mock_source2.updated_at = "2024-01-18T16:20:00Z"
            
            mock_db.query.return_value.all.return_value = [mock_source1, mock_source2]
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            
            result = self.runner.invoke(app, ["source", "list", "--json"])
            
            assert result.exit_code == 0
            
            # Parse JSON output
            output = json.loads(result.stdout)
            
            assert output["status"] == "ok"
            assert output["total"] == 2
            assert len(output["sources"]) == 2
            
            # Check that both sources are present
            source_names = [source["name"] for source in output["sources"]]
            assert "Source 1" in source_names
            assert "Source 2" in source_names
