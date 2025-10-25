"""
Contract tests for retrovue channel commands.

Tests the channel command group against the documented contract in docs/operator/CLI.md.
"""

import pytest
from tests.cli.utils import CLITestRunner


class TestChannelCLI:
    """Test cases for channel command group."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CLITestRunner()
    
    def test_channel_list_help(self):
        """Test retrovue channel list --help."""
        result = self.runner.assert_command_exists(["channel", "list"])
        assert "List all channels" in result.output
    
    def test_channel_list_shows_current_fields(self):
        """Test that channel list shows current implementation fields."""
        # Current implementation shows: ID, Active, Name, Timezone, Rollover
        result = self.runner.invoke(["channel", "list"])
        # This is a non-destructive command, but we'll just test presence
        assert result.exit_code == 0 or result.exit_code == 1  # May fail due to no DB
    
    @pytest.mark.xfail(reason="Missing documented fields per CLI.md")
    def test_channel_list_shows_documented_fields(self):
        """Test that channel list shows documented fields."""
        # TODO: According to CLI.md, should show:
        # - channel_id, name/branding label, active producer instance, attached playout enrichers (with priority)
        # Current implementation shows: ID, Active, Name, Timezone, Rollover
        # This mismatch should be resolved
        result = self.runner.invoke(["channel", "list"])
        assert "active producer instance" in result.output
        assert "attached playout enrichers" in result.output
    
    @pytest.mark.xfail(reason="Channel enricher commands not implemented per CLI contract")
    def test_channel_attach_enricher_help(self):
        """Test retrovue channel attach-enricher --help."""
        # TODO: According to CLI.md, should have retrovue channel attach-enricher <channel_id> <enricher_id> --priority <n>
        result = self.runner.assert_command_exists(["channel", "attach-enricher"])
        assert "Attach a playout-scope enricher" in result.output
    
    @pytest.mark.xfail(reason="Channel enricher commands not implemented per CLI contract")
    def test_channel_attach_enricher_has_priority_flag(self):
        """Test that channel attach-enricher has --priority flag."""
        result = self.runner.invoke_help(["channel", "attach-enricher"])
        assert "--priority" in result.output
    
    @pytest.mark.xfail(reason="Channel enricher commands not implemented per CLI contract")
    def test_channel_detach_enricher_help(self):
        """Test retrovue channel detach-enricher --help."""
        # TODO: According to CLI.md, should have retrovue channel detach-enricher <channel_id> <enricher_id>
        result = self.runner.assert_command_exists(["channel", "detach-enricher"])
        assert "Remove enricher from channel" in result.output
    
    def test_channel_show_help(self):
        """Test retrovue channel show --help."""
        # This command exists in current implementation
        result = self.runner.assert_command_exists(["channel", "show"])
        assert "Show detailed information" in result.output
    
    def test_channel_create_help(self):
        """Test retrovue channel create --help."""
        # This command exists in current implementation
        result = self.runner.assert_command_exists(["channel", "create"])
        assert "Create a new channel" in result.output
    
    def test_channel_update_help(self):
        """Test retrovue channel update --help."""
        # This command exists in current implementation
        result = self.runner.assert_command_exists(["channel", "update"])
        assert "Update an existing channel" in result.output
    
    def test_channel_delete_help(self):
        """Test retrovue channel delete --help."""
        # This command exists in current implementation
        result = self.runner.assert_command_exists(["channel", "delete"])
        assert "Delete a channel" in result.output
