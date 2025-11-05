"""Schedule Template Update Contract Tests

Behavioral tests for ScheduleTemplateContract.md (T-40 to T-46).
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
        "created_at": "2025-01-01T12:00:00Z",
        "updated_at": "2025-01-15T10:30:00Z",
    }


class TestScheduleTemplateUpdateContract:
    """Test ScheduleTemplate update contract rules (T-40 to T-46)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    # T-40, T-41: Successful update
    def test_template_update__success(self):
        """T-40, T-41: Update preserves existing fields and updates timestamp."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_update.update_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_template_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "update",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--name",
                    "Updated Template Name",
                ],
            )
            assert result.exit_code == 0
            assert "updated" in result.stdout.lower() or "Template updated" in result.stdout

    # T-3: Duplicate name on update
    def test_template_update__duplicate_name_fails(self):
        """T-3: Updating to duplicate name MUST exit 1."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_update.update_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("Template name already exists.")

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "update",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--name",
                    "Existing Template",
                ],
            )
            assert result.exit_code == 1
            assert "already exists" in result.stderr or "already exists" in result.stdout

    # T-45: Archive template
    def test_template_update__archive_template(self):
        """T-45: Updating is_active from true to false archives the template."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_update.update_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_result = _mock_template_result()
            mock_result["is_active"] = False
            mock_uc.return_value = mock_result

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "update",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--inactive",
                ],
            )
            assert result.exit_code == 0

    # T-46: Reactivate template
    def test_template_update__reactivate_template(self):
        """T-46: Updating is_active from false to true reactivates the template."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_update.update_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_result = _mock_template_result()
            mock_result["is_active"] = True
            mock_uc.return_value = mock_result

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "update",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--active",
                ],
            )
            assert result.exit_code == 0

    # T-43, T-44: No fields provided
    def test_template_update__no_fields_provided(self):
        """T-43, T-44: At least one field must be provided."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            
            # Try to update with no fields - validation happens in CLI before usecase
            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "update",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                ],
            )
            assert result.exit_code == 1
            assert (
                "At least one field" in result.stderr or "At least one field" in result.stdout
            )

    # T-19: Template not found
    def test_template_update__template_not_found(self):
        """Template not found MUST exit 1."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_update.update_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("Template not found")

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "update",
                    "--template",
                    "00000000-0000-0000-0000-000000000000",
                    "--name",
                    "New Name",
                ],
            )
            assert result.exit_code == 1
            assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    # T-56: JSON output
    def test_template_update__success_json_output(self):
        """T-56: Update with JSON output."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_update.update_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_template_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "update",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--name",
                    "Updated Name",
                    "--json",
                ],
            )
            assert result.exit_code == 0
            payload = json.loads(result.stdout)
            assert payload["status"] == "ok"
            assert "template" in payload

    def test_template_update__missing_id_exits_one(self):
        """Missing --template MUST exit 1 or 2 (Typer returns 2 for missing required params)."""
        result = self.runner.invoke(
            app,
            [
                "schedule-template",
                "update",
                "--name",
                "New Name",
            ],
        )
        assert result.exit_code == 1

    def test_template_update__help_flag_exits_zero(self):
        """Help flag MUST exit 0."""
        result = self.runner.invoke(app, ["schedule-template", "update", "--help"])
        assert result.exit_code == 0

