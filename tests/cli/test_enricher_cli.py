"""
Contract tests for retrovue enricher commands.

Tests the enricher command group against the documented contract in docs/operator/CLI.md.
"""

import pytest
from tests.cli.utils import CLITestRunner


class TestEnricherCLI:
    """Test cases for enricher command group."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CLITestRunner()
    
    @pytest.mark.xfail(reason="Enricher commands not implemented per CLI contract")
    def test_enricher_list_types_help(self):
        """Test retrovue enricher list-types --help."""
        # TODO: According to CLI.md, should have retrovue enricher list-types
        # Current implementation does not have enricher command group
        result = self.runner.assert_command_exists(["enricher", "list-types"])
        assert "Show all enricher types" in result.output
    
    @pytest.mark.xfail(reason="Enricher commands not implemented per CLI contract")
    def test_enricher_list_types_shows_scope_and_description(self):
        """Test that enricher list-types shows enricher types with scope and description."""
        # TODO: According to CLI.md, should show list of enricher types with scope and description
        pytest.skip("destructive; output behavior check")
    
    @pytest.mark.xfail(reason="Enricher commands not implemented per CLI contract")
    def test_enricher_add_help(self):
        """Test retrovue enricher add --help."""
        # TODO: According to CLI.md, should have retrovue enricher add --type <type> --name <label> [config...]
        result = self.runner.assert_command_exists(["enricher", "add"])
        assert "Create an enricher instance" in result.output
    
    @pytest.mark.xfail(reason="Enricher commands not implemented per CLI contract")
    def test_enricher_add_requires_type_and_name(self):
        """Test that enricher add requires --type and --name flags."""
        result = self.runner.invoke_help(["enricher", "add"])
        assert "--type" in result.output
        assert "--name" in result.output
    
    @pytest.mark.xfail(reason="Enricher commands not implemented per CLI contract")
    def test_enricher_add_help_without_type_shows_generic_usage(self):
        """Test retrovue enricher add --help shows generic usage plus available types."""
        # TODO: According to CLI.md, should print generic usage plus available types
        result = self.runner.invoke_help(["enricher", "add"])
        assert "available types" in result.output.lower()
    
    @pytest.mark.xfail(reason="Enricher commands not implemented per CLI contract")
    def test_enricher_add_type_help_shows_specific_params(self):
        """Test retrovue enricher add --type <type> --help shows specific parameter contract."""
        # TODO: According to CLI.md, should print that enricher's specific parameter contract
        result = self.runner.invoke_help(["enricher", "add", "--type", "ffprobe"])
        assert "ffprobe" in result.output.lower()
    
    @pytest.mark.xfail(reason="Enricher commands not implemented per CLI contract")
    def test_enricher_list_help(self):
        """Test retrovue enricher list --help."""
        # TODO: According to CLI.md, should have retrovue enricher list
        result = self.runner.assert_command_exists(["enricher", "list"])
        assert "List configured enricher instances" in result.output
    
    @pytest.mark.xfail(reason="Enricher commands not implemented per CLI contract")
    def test_enricher_list_shows_required_fields(self):
        """Test that enricher list shows required fields."""
        # TODO: According to CLI.md, should show:
        # - enricher_id, type, scope (ingest or playout), name/label
        pytest.skip("destructive; output behavior check")
    
    @pytest.mark.xfail(reason="Enricher commands not implemented per CLI contract")
    def test_enricher_update_help(self):
        """Test retrovue enricher update --help."""
        # TODO: According to CLI.md, should have retrovue enricher update <enricher_id> [config...]
        result = self.runner.assert_command_exists(["enricher", "update"])
        assert "Update enricher configuration" in result.output
    
    @pytest.mark.xfail(reason="Enricher commands not implemented per CLI contract")
    def test_enricher_remove_help(self):
        """Test retrovue enricher remove --help."""
        # TODO: According to CLI.md, should have retrovue enricher remove <enricher_id>
        result = self.runner.assert_command_exists(["enricher", "remove"])
        assert "Remove enricher instance" in result.output
    
    @pytest.mark.xfail(reason="Enricher commands not implemented per CLI contract")
    def test_enricher_remove_confirms_and_shows_affected(self):
        """Test that enricher remove confirms removal and shows affected collections/channels."""
        # TODO: According to CLI.md, should confirm removal and show affected collections/channels
        pytest.skip("destructive; presence-only check")
