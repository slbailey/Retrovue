"""Schedule Template Block Update Contract Tests

Behavioral tests for ScheduleTemplateBlockContract.md (B-27 to B-32).
"""

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from retrovue.cli.main import app


def _mock_block_result():
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "template_id": "123e4567-e89b-12d3-a456-426614174000",
        "start_time": "06:00",
        "end_time": "09:00",
        "block_id": "block-uuid-123",
        "block_name": "Test Block",
        "created_at": "2025-01-01T12:00:00Z",
        "updated_at": "2025-01-02T10:00:00Z",
    }


class TestScheduleTemplateBlockUpdateContract:
    """Test ScheduleTemplateBlock update contract rules (B-27 to B-32)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    # B-27, B-28: Successful update
    def test_block_update__success(self):
        """B-27, B-28: Update preserves existing fields and updates timestamp."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_update.update_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_block_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "update",
                    "--id",
                    "550e8400-e29b-41d4-a716-446655440000",
                    "--start-time",
                    "07:00",
                ],
            )
            assert result.exit_code == 0
            assert "updated" in result.stdout.lower() or "Block instance updated" in result.stdout or "Instance updated" in result.stdout

    # B-29, B-30: Overlap validation after update
    def test_block_update__overlap_after_update(self):
        """B-29, B-30: Update re-validates non-overlap."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_update.update_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("Block overlaps with existing block(s) in template")

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "update",
                    "--id",
                    "550e8400-e29b-41d4-a716-446655440000",
                    "--start-time",
                    "07:00",  # Would overlap with another block
                    "--end-time",
                    "10:00",
                ],
            )
            assert result.exit_code == 1
            assert "overlap" in result.stderr.lower() or "overlap" in result.stdout.lower()

    # B-19: Block not found
    def test_block_update__block_not_found(self):
        """B-18, B-19: Updating non-existent block MUST exit 1."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_update.update_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("Template block not found")

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "update",
                    "--id",
                    "00000000-0000-0000-0000-000000000000",
                    "--start-time",
                    "07:00",
                ],
            )
            assert result.exit_code == 1
            assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    # B-31, B-32: No fields provided
    def test_block_update__no_fields_provided(self):
        """B-31, B-32: At least one field must be provided."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Try to update with no fields - validation happens in CLI before usecase
            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "update",
                    "--id",
                    "550e8400-e29b-41d4-a716-446655440000",
                ],
            )
            assert result.exit_code == 1
            assert (
                "At least one field" in result.stderr or "At least one field" in result.stdout
            )

    # B-38: JSON output
    def test_block_update__success_json_output(self):
        """B-38: Update with JSON output."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_update.update_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_block_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "update",
                    "--id",
                    "550e8400-e29b-41d4-a716-446655440000",
                    "--start-time",
                    "07:00",
                    "--json",
                ],
            )
            assert result.exit_code == 0
            payload = json.loads(result.stdout)
            assert payload["status"] == "ok"
            assert "block" in payload

    # B-29: Invalid rule_json in update
    def test_block_update__invalid_rule_json(self):
        """B-29: Update validates rule_json."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_update.update_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("rule_json must be valid JSON")

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "update",
                    "--id",
                    "550e8400-e29b-41d4-a716-446655440000",
                    "--rule-json",
                    '{"tags": ["cartoon"',  # Invalid JSON
                ],
            )
            assert result.exit_code == 1

    # B-29: Invalid time format in update
    def test_block_update__invalid_time_format(self):
        """B-29: Update validates time format."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "update",
                    "--id",
                    "550e8400-e29b-41d4-a716-446655440000",
                    "--start-time",
                    "25:00",  # Invalid
                ],
            )
            assert result.exit_code == 1

    # B-29: Time logic in update
    def test_block_update__start_time_gte_end_time(self):
        """B-29: Update validates time logic."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_update.update_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("start_time must be less than end_time")

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "update",
                    "--id",
                    "550e8400-e29b-41d4-a716-446655440000",
                    "--start-time",
                    "09:00",
                    "--end-time",
                    "06:00",
                ],
            )
            assert result.exit_code == 1

    def test_block_update__help_flag_exits_zero(self):
        """Help flag MUST exit 0."""
        result = self.runner.invoke(app, ["schedule-template", "block", "update", "--help"])
        assert result.exit_code == 0

