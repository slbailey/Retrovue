"""Schedule Template Block Show Contract Tests

Behavioral tests for ScheduleTemplateBlockContract.md show operations.
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
        "rule_json": {"tags": ["cartoon"], "rating_max": "TV-Y"},
        "created_at": "2025-01-01T12:00:00Z",
        "updated_at": None,
    }


class TestScheduleTemplateBlockShowContract:
    """Test ScheduleTemplateBlock show contract rules."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_block_show__by_id_success(self):
        """Show block by ID with human-readable output."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_show.show_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_block_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "show",
                    "--id",
                    "550e8400-e29b-41d4-a716-446655440000",
                ],
            )
            assert result.exit_code == 0
            assert "550e8400-e29b-41d4-a716-446655440000" in result.stdout or "ID:" in result.stdout

    # B-39: Human-readable output includes all fields
    def test_block_show__human_output_includes_all_fields(self):
        """B-39: Human-readable output MUST include all block fields."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_show.show_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_block_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "show",
                    "--id",
                    "550e8400-e29b-41d4-a716-446655440000",
                ],
            )
            assert result.exit_code == 0
            output = result.stdout
            assert "06:00" in output or "Start Time" in output
            assert "09:00" in output or "End Time" in output
            assert "cartoon" in output or "rule_json" in output.lower()

    # B-38: JSON output
    def test_block_show__json_output(self):
        """B-38: Show block with JSON output."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_show.show_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_block_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "show",
                    "--id",
                    "550e8400-e29b-41d4-a716-446655440000",
                    "--json",
                ],
            )
            assert result.exit_code == 0
            payload = json.loads(result.stdout)
            assert payload["status"] == "ok"
            assert "block" in payload
            for k in ["id", "template_id", "block_id", "start_time", "end_time"]:
                assert k in payload["block"], f"missing key {k}"

    # B-19: Block not found
    def test_block_show__block_not_found(self):
        """B-19: Showing non-existent block MUST exit 1."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_show.show_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("Template block not found")

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "show",
                    "--id",
                    "00000000-0000-0000-0000-000000000000",
                ],
            )
            assert result.exit_code == 1
            assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    def test_block_show__missing_id_exits_one(self):
        """Missing --id MUST exit 1 or 2 (Typer returns 2 for missing required params)."""
        result = self.runner.invoke(
            app,
            [
                "schedule-template",
                "block",
                "show",
            ],
        )
        assert result.exit_code in (1, 2)  # Typer returns 2 for missing required params

    def test_block_show__help_flag_exits_zero(self):
        """Help flag MUST exit 0."""
        result = self.runner.invoke(app, ["schedule-template", "block", "show", "--help"])
        assert result.exit_code == 0

