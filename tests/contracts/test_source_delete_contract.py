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
    
    def _setup_mock_database(self, mock_db, mock_source):
        """Set up database mocking for source delete operations."""
        # Track deleted sources for post-operation validation
        deleted_sources = set()
        
        def mock_query_factory(model_class):
            if model_class.__name__ == 'Source':
                # For Source queries (resolve_source_selector and post-operation validation)
                mock_query = MagicMock()
                filter_mock = MagicMock()
                mock_query.filter.return_value = filter_mock
                
                # For resolve_source_selector: return the source
                order_by_mock = MagicMock()
                filter_mock.order_by.return_value = order_by_mock
                order_by_mock.all.return_value = [mock_source]
                
                # For post-operation validation: return None if source was deleted
                def mock_first():
                    if str(mock_source.id) in deleted_sources:
                        return None
                    return mock_source
                
                filter_mock.first.side_effect = mock_first
                return mock_query
            elif model_class.__name__ == 'SourceCollection':
                # For SourceCollection queries (build_pending_delete_summary and post-operation validation)
                mock_query = MagicMock()
                filter_mock = MagicMock()
                mock_query.filter.return_value = filter_mock
                
                # For build_pending_delete_summary: return count
                def mock_count():
                    if str(mock_source.id) in deleted_sources:
                        return 0
                    return 3
                
                filter_mock.count.side_effect = mock_count
                return mock_query
            elif model_class.__name__ == 'PathMapping':
                # For PathMapping queries (build_pending_delete_summary)
                mock_query = MagicMock()
                join_mock = MagicMock()
                mock_query.join.return_value = join_mock
                filter_mock = MagicMock()
                join_mock.filter.return_value = filter_mock
                filter_mock.count.return_value = 12
                return mock_query
            else:
                # Default mock for other queries
                mock_query = MagicMock()
                filter_mock = MagicMock()
                mock_query.filter.return_value = filter_mock
                filter_mock.count.return_value = 0
                return mock_query
        
        # Track when delete is called
        def mock_delete(obj):
            if hasattr(obj, 'id') and str(obj.id) == str(mock_source.id):
                deleted_sources.add(str(obj.id))
        
        mock_db.delete.side_effect = mock_delete
        mock_db.query.side_effect = mock_query_factory

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
            
            # Set up database mocking
            self._setup_mock_database(mock_db, mock_source)
            
            # Mock user input "no" to cancel
            result = self.runner.invoke(app, ["delete", "test-source"], input="no\n")
            
            assert result.exit_code == 0
            assert "WARNING: This will permanently delete the following:" in result.stdout
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
            
            # Set up database mocking
            self._setup_mock_database(mock_db, mock_source)
            
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
            
            # Set up database mocking
            self._setup_mock_database(mock_db, mock_source)
            
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
            
            # Set up database mocking
            self._setup_mock_database(mock_db, mock_source)
            
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
            
            # Mock database to return no sources (source not found)
            def mock_query_factory(model_class):
                if model_class.__name__ == 'Source':
                    # For Source queries (resolve_source_selector) - return empty list
                    mock_query = MagicMock()
                    mock_query.filter.return_value.order_by.return_value.all.return_value = []
                    return mock_query
                else:
                    # Default mock for other queries
                    mock_query = MagicMock()
                    mock_query.filter.return_value.count.return_value = 0
                    return mock_query
            
            mock_db.query.side_effect = mock_query_factory
            
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
            
            # Set up database mocking
            self._setup_mock_database(mock_db, mock_source)
            
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
            
            # Set up database mocking
            self._setup_mock_database(mock_db, mock_source)
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["delete", "test-source", "--force"])
                
                assert result.exit_code == 0
                assert "Successfully deleted source" in result.stdout
                assert "Are you sure" not in result.stdout  # No confirmation prompt

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
            
            # Set up database mocking for multiple sources using the helper
            # Track deleted sources for post-operation validation
            deleted_sources = set()
            
            def mock_query_factory(model_class):
                if model_class.__name__ == 'Source':
                    # For Source queries (resolve_source_selector and post-operation validation)
                    mock_query = MagicMock()
                    filter_mock = MagicMock()
                    mock_query.filter.return_value = filter_mock
                    
                    # For resolve_source_selector: return multiple sources
                    order_by_mock = MagicMock()
                    filter_mock.order_by.return_value = order_by_mock
                    order_by_mock.all.return_value = mock_sources
                    
                    # For post-operation validation: return None if source was deleted
                    def mock_first():
                        # This is called for each individual source validation
                        # We need to check which specific source is being validated
                        # For simplicity, return None if any source was deleted
                        if deleted_sources:
                            return None
                        return mock_sources[0]  # Return first source for initial validation
                    
                    filter_mock.first.side_effect = mock_first
                    return mock_query
                elif model_class.__name__ == 'SourceCollection':
                    # For SourceCollection queries (build_pending_delete_summary and post-operation validation)
                    mock_query = MagicMock()
                    filter_mock = MagicMock()
                    mock_query.filter.return_value = filter_mock
                    
                    # For build_pending_delete_summary: return count
                    def mock_count():
                        if deleted_sources:
                            return 0
                        return 2
                    
                    filter_mock.count.side_effect = mock_count
                    return mock_query
                elif model_class.__name__ == 'PathMapping':
                    # For PathMapping queries (build_pending_delete_summary)
                    mock_query = MagicMock()
                    join_mock = MagicMock()
                    mock_query.join.return_value = join_mock
                    filter_mock = MagicMock()
                    join_mock.filter.return_value = filter_mock
                    filter_mock.count.return_value = 8
                    return mock_query
                else:
                    # Default mock for other queries
                    mock_query = MagicMock()
                    filter_mock = MagicMock()
                    mock_query.filter.return_value = filter_mock
                    filter_mock.count.return_value = 0
                    return mock_query
            
            # Track when delete is called
            def mock_delete(obj):
                if hasattr(obj, 'id'):
                    deleted_sources.add(str(obj.id))
            
            mock_db.delete.side_effect = mock_delete
            mock_db.query.side_effect = mock_query_factory
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["delete", "test-*", "--force"])
                
                assert result.exit_code == 0
                # Verify wildcard resolution worked (multiple sources were processed)
                assert "Successfully deleted source" in result.stdout
                # Should show multiple sources in output
                assert "source-1" in result.stdout
                assert "source-2" in result.stdout

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
            
            # Set up database mocking for multiple sources
            def mock_query_factory(model_class):
                if model_class.__name__ == 'Source':
                    # For Source queries (resolve_source_selector)
                    mock_query = MagicMock()
                    mock_query.filter.return_value.order_by.return_value.all.return_value = mock_sources
                    return mock_query
                elif model_class.__name__ == 'SourceCollection':
                    # For SourceCollection queries (build_pending_delete_summary)
                    mock_query = MagicMock()
                    mock_query.filter.return_value.count.return_value = 2
                    return mock_query
                elif model_class.__name__ == 'PathMapping':
                    # For PathMapping queries (build_pending_delete_summary)
                    mock_query = MagicMock()
                    mock_query.join.return_value.filter.return_value.count.return_value = 8
                    return mock_query
                else:
                    # Default mock for other queries
                    mock_query = MagicMock()
                    mock_query.filter.return_value.count.return_value = 0
                    return mock_query
            
            mock_db.query.side_effect = mock_query_factory
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["delete", "test-*"], input="no\n")
                
                assert result.exit_code == 0
                assert "WARNING: This will permanently delete 2 sources:" in result.stdout  # Aggregated count
                assert "4 collections" in result.stdout  # Total collections (2 sources * 2 collections each)
                assert "16 path mappings" in result.stdout  # Total path mappings (2 sources * 8 path mappings each)
                assert "Deletion cancelled" in result.stdout

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
            
            # Set up database mocking for multiple sources using the helper
            # Track deleted sources for post-operation validation
            deleted_sources = set()
            
            def mock_query_factory(model_class):
                if model_class.__name__ == 'Source':
                    # For Source queries (resolve_source_selector and post-operation validation)
                    mock_query = MagicMock()
                    filter_mock = MagicMock()
                    mock_query.filter.return_value = filter_mock
                    
                    # For resolve_source_selector: return multiple sources
                    order_by_mock = MagicMock()
                    filter_mock.order_by.return_value = order_by_mock
                    order_by_mock.all.return_value = mock_sources
                    
                    # For post-operation validation: return None if source was deleted
                    def mock_first():
                        # This is called for each individual source validation
                        # We need to check which specific source is being validated
                        # For simplicity, return None if any source was deleted
                        if deleted_sources:
                            return None
                        return mock_sources[0]  # Return first source for initial validation
                    
                    filter_mock.first.side_effect = mock_first
                    return mock_query
                elif model_class.__name__ == 'SourceCollection':
                    # For SourceCollection queries (build_pending_delete_summary and post-operation validation)
                    mock_query = MagicMock()
                    filter_mock = MagicMock()
                    mock_query.filter.return_value = filter_mock
                    
                    # For build_pending_delete_summary: return count
                    def mock_count():
                        if deleted_sources:
                            return 0
                        return 2
                    
                    filter_mock.count.side_effect = mock_count
                    return mock_query
                elif model_class.__name__ == 'PathMapping':
                    # For PathMapping queries (build_pending_delete_summary)
                    mock_query = MagicMock()
                    join_mock = MagicMock()
                    mock_query.join.return_value = join_mock
                    filter_mock = MagicMock()
                    join_mock.filter.return_value = filter_mock
                    filter_mock.count.return_value = 8
                    return mock_query
                else:
                    # Default mock for other queries
                    mock_query = MagicMock()
                    filter_mock = MagicMock()
                    mock_query.filter.return_value = filter_mock
                    filter_mock.count.return_value = 0
                    return mock_query
            
            # Track when delete is called
            def mock_delete(obj):
                if hasattr(obj, 'id'):
                    deleted_sources.add(str(obj.id))
            
            mock_db.delete.side_effect = mock_delete
            mock_db.query.side_effect = mock_query_factory
            
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
            
            # Set up database mocking
            self._setup_mock_database(mock_db, mock_source)
            
            with patch("retrovue.cli.commands.source.SourceService", return_value=mock_source_service):
                result = self.runner.invoke(app, ["delete", "test-source", "--test-db", "--force"])
                
                # Should succeed (test-db flag should be accepted)
                assert result.exit_code == 0
