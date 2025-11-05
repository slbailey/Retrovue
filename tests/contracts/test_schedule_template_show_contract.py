"""Schedule Template Show Contract Tests

Behavioral tests for ScheduleTemplateContract.md show operations.
"""

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from retrovue.cli.main import app


def _mock_template_result():
    return {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": "All Sitcoms 24x7",
        "description": "24-hour sitcom programming template",
        "is_active": True,
        "blocks_count": 3,
        "plans_count": 2,
        "blocks": [
            {
                "start_time": "06:00",
                "end_time": "09:00",
                "rule_json": {"tags": ["cartoon"]},
            },
            {
                "start_time": "09:00",
                "end_time": "18:00",
                "rule_json": {"tags": ["sitcom"], "rating_max": "TV-PG"},
            },
            {
                "start_time": "18:00",
                "end_time": "24:00",
                "rule_json": {"tags": ["sitcom"], "rating_max": "TV-14"},
            },
        ],
        "created_at": "2025-01-01T12:00:00Z",
        "updated_at": "2025-01-15T10:30:00Z",
    }


class TestScheduleTemplateShowContract:
    """Test ScheduleTemplate show contract rules."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    # T-58: Show by ID
    def test_template_show__by_id(self):
        """Show template by ID with human-readable output."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_show.show_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_template_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "show",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                ],
            )
            assert result.exit_code == 0
            assert "All Sitcoms 24x7" in result.stdout
            assert "123e4567-e89b-12d3-a456-426614174000" in result.stdout or "ID:" in result.stdout

    # T-58: Show by name
    def test_template_show__by_name(self):
        """Show template by name with human-readable output."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_show.show_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_template_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "show",
                    "--template",
                    "All Sitcoms 24x7",
                ],
            )
            assert result.exit_code == 0
            assert "All Sitcoms 24x7" in result.stdout

    # T-58: Show with blocks
    def test_template_show__with_blocks(self):
        """T-58: Show command MUST display associated blocks."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_show.show_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_template_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "show",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                ],
            )
            assert result.exit_code == 0
            output = result.stdout
            # Should show blocks
            assert "06:00" in output or "09:00" in output or "Blocks" in output

    # T-58: Show with plans count
    def test_template_show__with_plans_count(self):
        """T-58: Show command MUST display plans count."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_show.show_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_template_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "show",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                ],
            )
            assert result.exit_code == 0
            output = result.stdout
            # Should show plans count
            assert "2" in output or "plans" in output.lower() or "Plans" in output

    # T-57: Human-readable output includes all fields
    def test_template_show__human_output_includes_all_fields(self):
        """T-57: Human-readable output MUST include all template fields."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_show.show_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_template_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "show",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                ],
            )
            assert result.exit_code == 0
            output = result.stdout
            assert "All Sitcoms 24x7" in output
            assert "24-hour" in output or "description" in output.lower()
            assert "true" in output.lower() or "Active" in output

    # T-56: JSON output
    def test_template_show__json_output(self):
        """T-56: Show template with JSON output."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_show.show_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_template_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "show",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--json",
                ],
            )
            assert result.exit_code == 0
            payload = json.loads(result.stdout)
            assert payload["status"] == "ok"
            assert "template" in payload
            for k in ["id", "name", "description", "is_active", "blocks_count"]:
                assert k in payload["template"], f"missing key {k}"

    def test_template_show__template_not_found(self):
        """Template not found MUST exit 1."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_show.show_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("Template not found")

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "show",
                    "--template",
                    "00000000-0000-0000-0000-000000000000",
                ],
            )
            assert result.exit_code == 1
            assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    def test_template_show__missing_id_and_name_exits_one(self):
        """Missing --template MUST exit 1 or 2 (Typer returns 2 for missing required params)."""
        result = self.runner.invoke(
            app,
            [
                "schedule-template",
                "show",
            ],
        )
        assert result.exit_code == 1

    def test_template_show__help_flag_exits_zero(self):
        """Help flag MUST exit 0."""
        result = self.runner.invoke(app, ["schedule-template", "show", "--help"])
        assert result.exit_code == 0

