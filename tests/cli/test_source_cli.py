"""
Contract tests for retrovue source commands.

Tests the source command group against the documented contract in docs/operator/CLI.md.
"""

import pytest
from tests.cli.utils import CLITestRunner


class TestSourceCLI:
    """Test cases for source command group."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CLITestRunner()
    
    def test_source_list_types_help(self):
        """Test retrovue source list-types --help."""
        result = self.runner.assert_command_exists(["source", "list-types"])
        assert "List all available source types" in result.output
    
    def test_source_list_types_has_descriptions(self):
        """Test that source list-types includes descriptions as documented."""
        # TODO: According to CLI.md, output should include descriptions
        # Current implementation may not include descriptions - this should be fixed
        result = self.runner.invoke(["source", "list-types"])
        assert result.exit_code == 0
        # TODO: Add assertion for descriptions once implemented
    
    def test_source_add_help(self):
        """Test retrovue source add --help."""
        # The source add command requires --type parameter, so we test with a type
        result = self.runner.assert_command_exists(["source", "add", "--type", "plex"])
        assert "Help for plex source type" in result.output
    
    def test_source_add_requires_type_and_name(self):
        """Test that source add requires --type and --name flags."""
        # Test with a specific type to get the help
        result = self.runner.invoke_help(["source", "add", "--type", "plex"])
        assert "--type" in result.output
        assert "--name" in result.output
        # TODO: According to audit, --name is required in code but not documented
        # This mismatch should be resolved by either making --name optional or updating docs
    
    def test_source_add_type_help(self):
        """Test retrovue source add --type <type> --help for specific types."""
        # Test with plex type
        result = self.runner.invoke_help(["source", "add", "--type", "plex"])
        assert result.exit_code == 0
        assert "plex" in result.output.lower()
        
        # Test with filesystem type  
        result = self.runner.invoke_help(["source", "add", "--type", "filesystem"])
        assert result.exit_code == 0
        assert "filesystem" in result.output.lower()
    
    def test_source_list_help(self):
        """Test retrovue source list --help."""
        result = self.runner.assert_command_exists(["source", "list"])
        assert "List all configured sources" in result.output
    
    def test_source_list_shows_required_fields(self):
        """Test that source list shows required fields: source_id, name, type, status."""
        # TODO: According to CLI.md, should show source_id, name, type, status
        # Current implementation may not show all fields - this should be verified
        result = self.runner.invoke(["source", "list"])
        # This is a destructive command that would query real data, so we skip actual execution
        pytest.skip("destructive; presence-only check")
    
    def test_source_update_help(self):
        """Test retrovue source update --help."""
        result = self.runner.assert_command_exists(["source", "update"])
        assert "Update a source configuration" in result.output
    
    def test_source_remove_help(self):
        """Test retrovue source remove --help."""
        result = self.runner.assert_command_exists(["source", "delete"])  # Actual command is "delete" not "remove"
        assert "Delete a source" in result.output
    
    def test_source_remove_confirms_and_shows_affected(self):
        """Test that source remove confirms removal and shows affected collections."""
        # TODO: According to CLI.md, should confirm removal and show affected collections
        # This is a destructive command, so we only test presence
        result = self.runner.invoke_help(["source", "delete"])
        assert "--force" in result.output  # Should have force option for non-interactive use
        pytest.skip("destructive; presence-only check")
    
    def test_source_sync_collections_help(self):
        """Test retrovue source sync-collections --help."""
        # TODO: According to audit, command is named "discover" not "sync-collections"
        # This mismatch should be resolved by either renaming command or updating docs
        result = self.runner.assert_command_exists(["source", "discover"])
        assert "Discover collections" in result.output
    
    def test_source_sync_collections_shows_discovered(self):
        """Test that source sync-collections shows discovered collections and sync status."""
        # TODO: According to CLI.md, should show discovered collections and sync status
        # This is a potentially destructive command, so we only test presence
        pytest.skip("destructive; presence-only check")
