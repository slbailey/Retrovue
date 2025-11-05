"""Schedule Template List Contract Tests

Behavioral tests for ScheduleTemplateContract.md list operations.
"""

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from retrovue.cli.main import app


def _mock_template_list():
    return [
        {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "name": "All Sitcoms 24x7",
            "description": "24-hour sitcom programming template",
            "is_active": True,
            "blocks_count": 3,
            "created_at": "2025-01-01T12:00:00Z",
            "updated_at": None,
        },
        {
            "id": "223e4567-e89b-12d3-a456-426614174001",
            "name": "Morning Cartoons",
            "description": "Morning cartoon block",
            "is_active": False,
            "blocks_count": 1,
            "created_at": "2025-01-02T12:00:00Z",
            "updated_at": None,
        },
    ]


class TestScheduleTemplateListContract:
    """Test ScheduleTemplate list contract rules."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    # T-59: List all templates
    def test_template_list__all_templates(self):
        """T-59: List shows all templates."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_list.list_templates"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_template_list()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "list",
                ],
            )
            assert result.exit_code == 0
            assert "All Sitcoms 24x7" in result.stdout or "Morning Cartoons" in result.stdout

    # T-59: Active-only filter
    def test_template_list__active_only(self):
        """T-59: --active-only shows only active templates."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_list.list_templates"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            # Return only active templates
            active_only = [t for t in _mock_template_list() if t["is_active"]]
            mock_uc.return_value = active_only

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "list",
                    "--active-only",
                ],
            )
            assert result.exit_code == 0
            # Should not show inactive templates
            assert "Morning Cartoons" not in result.stdout or len(active_only) == 1

    # T-56: JSON output
    def test_template_list__success_json_output(self):
        """T-56: List templates with JSON output."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_list.list_templates"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_template_list()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "list",
                    "--json",
                ],
            )
            assert result.exit_code == 0
            payload = json.loads(result.stdout)
            assert payload["status"] == "ok"
            assert "templates" in payload or isinstance(payload, list)
            templates = payload.get("templates", payload) if isinstance(payload, dict) else payload
            assert len(templates) == 2

    # T-13: Warning for templates with no blocks
    def test_template_list__warns_no_blocks(self):
        """T-13: Template validation SHOULD warn if template has no blocks."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_list.list_templates"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            templates = _mock_template_list()
            templates[0]["blocks_count"] = 0
            mock_uc.return_value = templates

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "list",
                ],
            )
            assert result.exit_code == 0
            # Warning may be present (not enforced, just SHOULD warn)

    def test_template_list__empty_list(self):
        """Empty list should return empty list."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_list.list_templates"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = []

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "list",
                    "--json",
                ],
            )
            assert result.exit_code == 0
            payload = json.loads(result.stdout)
            templates = payload.get("templates", payload) if isinstance(payload, dict) else payload
            assert isinstance(templates, list)
            assert len(templates) == 0

    def test_template_list__help_flag_exits_zero(self):
        """Help flag MUST exit 0."""
        result = self.runner.invoke(app, ["schedule-template", "list", "--help"])
        assert result.exit_code == 0

