"""
CLI test utilities for RetroVue contract tests.

This module provides utilities for testing CLI commands against the documented contract.
"""

import sys
from pathlib import Path
from typer.testing import CliRunner

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from retrovue.cli.main import app


class CLITestRunner:
    """Helper class for running CLI commands in tests."""
    
    def __init__(self):
        self.runner = CliRunner()
    
    def invoke(self, command_args, **kwargs):
        """
        Invoke a CLI command with the given arguments.
        
        Args:
            command_args: List of command arguments (e.g., ["source", "list"])
            **kwargs: Additional arguments to pass to runner.invoke
            
        Returns:
            Result object from typer.testing.CliRunner
        """
        return self.runner.invoke(app, command_args, **kwargs)
    
    def invoke_help(self, command_args):
        """
        Invoke a CLI command with --help flag.
        
        Args:
            command_args: List of command arguments (e.g., ["source", "add"])
            
        Returns:
            Result object from typer.testing.CliRunner
        """
        return self.invoke(command_args + ["--help"])
    
    def assert_command_exists(self, command_args):
        """
        Assert that a command exists and can be invoked with --help.
        
        Args:
            command_args: List of command arguments (e.g., ["source", "list"])
        """
        result = self.invoke_help(command_args)
        assert result.exit_code == 0, f"Command {command_args} failed with exit code {result.exit_code}: {result.output}"
        return result
    
    def assert_command_help_contains(self, command_args, expected_text):
        """
        Assert that command help contains expected text.
        
        Args:
            command_args: List of command arguments
            expected_text: Text that should be present in help output
        """
        result = self.invoke_help(command_args)
        assert result.exit_code == 0
        assert expected_text in result.output, f"Expected '{expected_text}' not found in help for {command_args}: {result.output}"
        return result
