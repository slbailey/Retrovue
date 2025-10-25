"""
Contract tests for retrovue collection commands.

Tests the collection command group against the documented contract in docs/operator/CLI.md.
"""

import pytest
from tests.cli.utils import CLITestRunner


class TestCollectionCLI:
    """Test cases for collection command group."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CLITestRunner()
    
    @pytest.mark.xfail(reason="Collection commands not implemented as separate command group per CLI contract")
    def test_collection_list_help(self):
        """Test retrovue collection list --help."""
        # TODO: According to CLI.md, should have retrovue collection list --source <source_id>
        # Current implementation has this as retrovue source assets list <source_id>
        result = self.runner.assert_command_exists(["collection", "list"])
        assert "List Collections for a Source" in result.output
    
    @pytest.mark.xfail(reason="Collection commands not implemented as separate command group per CLI contract")
    def test_collection_list_shows_required_fields(self):
        """Test that collection list shows required fields."""
        # TODO: According to CLI.md, should show:
        # - collection_id, display_name, source_path, local_path, sync_enabled, ingestable
        pytest.skip("destructive; presence-only check")
    
    @pytest.mark.xfail(reason="Collection commands not implemented as separate command group per CLI contract")
    def test_collection_update_help(self):
        """Test retrovue collection update --help."""
        # TODO: According to CLI.md, should have retrovue collection update <collection_id> --sync-enabled <true|false> [--local-path <path>]
        result = self.runner.assert_command_exists(["collection", "update"])
        assert "Enable/disable ingest for that Collection" in result.output
    
    @pytest.mark.xfail(reason="Collection commands not implemented as separate command group per CLI contract")
    def test_collection_update_has_sync_enabled_and_local_path_flags(self):
        """Test that collection update has --sync-enabled and --local-path flags."""
        result = self.runner.invoke_help(["collection", "update"])
        assert "--sync-enabled" in result.output
        assert "--local-path" in result.output
    
    @pytest.mark.xfail(reason="Collection commands not implemented as separate command group per CLI contract")
    def test_collection_attach_enricher_help(self):
        """Test retrovue collection attach-enricher --help."""
        # TODO: According to CLI.md, should have retrovue collection attach-enricher <collection_id> <enricher_id> --priority <n>
        result = self.runner.assert_command_exists(["collection", "attach-enricher"])
        assert "Attach an ingest-scope enricher" in result.output
    
    @pytest.mark.xfail(reason="Collection commands not implemented as separate command group per CLI contract")
    def test_collection_attach_enricher_has_priority_flag(self):
        """Test that collection attach-enricher has --priority flag."""
        result = self.runner.invoke_help(["collection", "attach-enricher"])
        assert "--priority" in result.output
    
    @pytest.mark.xfail(reason="Collection commands not implemented as separate command group per CLI contract")
    def test_collection_detach_enricher_help(self):
        """Test retrovue collection detach-enricher --help."""
        # TODO: According to CLI.md, should have retrovue collection detach-enricher <collection_id> <enricher_id>
        result = self.runner.assert_command_exists(["collection", "detach-enricher"])
        assert "Remove enricher from collection" in result.output
    
    def test_source_assets_list_as_collection_alternative(self):
        """Test that retrovue source assets list exists as alternative to collection list."""
        # Current implementation has collection functionality under source assets
        result = self.runner.assert_command_exists(["source", "assets", "list"])
        assert "List asset groups" in result.output
        # TODO: This is a workaround - proper collection commands should be implemented
