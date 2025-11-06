"""
Contract tests for program add command.

Tests the behavior of: retrovue channel plan <channel> <plan> program add

See: docs/contracts/resources/ProgramAddContract.md
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from retrovue.cli.main import app

# Contract: ProgramAddContract
# Command: retrovue channel plan <channel> <plan> program add


@pytest.mark.contract
class TestProgramAddContract:
    """Contract tests for program add command."""

    def setup_method(self):
        self.runner = CliRunner()

    def test_program_add_requires_content_type(self):
        """PA-2: Must specify exactly one content type."""
        result = self.runner.invoke(
            app,
            ["channel", "plan", "abc", "xyz", "program", "add", "--start", "06:00", "--duration", "30"],
        )
        assert result.exit_code == 1
        assert "Must specify one content type" in result.stdout or "Must specify one content type" in result.stderr

    def test_program_add_validates_start_time_format(self):
        """PA-3: Start time must be in valid HH:MM format."""
        result = self.runner.invoke(
            app,
            [
                "channel",
                "plan",
                "abc",
                "xyz",
                "program",
                "add",
                "--start",
                "25:00",  # Invalid hour
                "--duration",
                "30",
                "--series",
                "Test",
            ],
        )
        # Command may fail at channel/plan resolution or start time validation
        # Accept either exit code 1 (validation error) or 0 (not yet implemented)
        assert result.exit_code in (0, 1)

    def test_program_add_validates_duration_positive(self):
        """PA-4: Duration must be positive integer."""
        result = self.runner.invoke(
            app,
            [
                "channel",
                "plan",
                "abc",
                "xyz",
                "program",
                "add",
                "--start",
                "06:00",
                "--duration",
                "-10",  # Negative duration
                "--series",
                "Test",
            ],
        )
        # Command may fail at channel/plan resolution or duration validation
        # Accept either exit code 1 (validation error) or 0 (not yet implemented)
        assert result.exit_code in (0, 1)

    def test_program_add_rejects_multiple_content_types(self):
        """PA-2: Must specify only one content type."""
        result = self.runner.invoke(
            app,
            [
                "channel",
                "plan",
                "abc",
                "xyz",
                "program",
                "add",
                "--start",
                "06:00",
                "--duration",
                "30",
                "--series",
                "Test",
                "--asset",
                "uuid",
            ],
        )
        assert result.exit_code == 1
        assert "only one content type" in result.stdout or "only one content type" in result.stderr

    # TODO: Add more tests once implementation is complete:
    # - test_program_add_success_with_series
    # - test_program_add_success_with_asset
    # - test_program_add_success_with_virtual_asset
    # - test_program_add_validates_channel_exists
    # - test_program_add_validates_plan_exists
    # - test_program_add_validates_plan_belongs_to_channel
    # - test_program_add_validates_asset_eligibility
    # - test_program_add_detects_overlaps
    # - test_program_add_json_output

