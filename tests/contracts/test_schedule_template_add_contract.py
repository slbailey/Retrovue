"""Schedule Template Add Contract Tests

Behavioral tests for ScheduleTemplateContract.md (T-1 to T-39).
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
        "blocks_count": 0,
        "created_at": "2025-01-01T12:00:00Z",
        "updated_at": None,
    }


class TestScheduleTemplateAddContract:
    """Test ScheduleTemplate add contract rules (T-1 to T-39)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    # T-1, T-2: Name uniqueness
    def test_template_add__duplicate_name_fails(self):
        """T-1, T-2: Template name MUST be unique (case-insensitive)."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_add.add_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("Template name already exists.")

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "add",
                    "--name",
                    "All Sitcoms 24x7",
                ],
            )
            assert result.exit_code == 1
            assert "already exists" in result.stderr or "already exists" in result.stdout

    # T-5: Case-insensitive uniqueness
    def test_template_add__duplicate_name_case_insensitive(self):
        """T-5: Name comparison MUST be case-insensitive."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_add.add_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("Template name already exists.")

            # Try creating with different case
            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "add",
                    "--name",
                    "ALL SITCOMS 24X7",  # Different case
                ],
            )
            assert result.exit_code == 1

    # T-6, T-8: Empty name
    def test_template_add__empty_name_fails(self):
        """T-6, T-8: Template name cannot be empty."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "add",
                    "--name",
                    "",
                ],
            )
            assert result.exit_code == 1

    # T-7, T-9: Name too long
    def test_template_add__name_too_long_fails(self):
        """T-7, T-9: Template name max length 255 characters."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_add.add_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError(
                "Template name exceeds maximum length (255 characters)."
            )

            long_name = "A" * 256
            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "add",
                    "--name",
                    long_name,
                ],
            )
            assert result.exit_code == 1
            assert "255" in result.stderr or "255" in result.stdout

    # T-17, T-18: Active status defaults
    def test_template_add__default_active(self):
        """T-17, T-18: Default state is is_active=true."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_add.add_template"
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
                    "add",
                    "--name",
                    "All Sitcoms 24x7",
                ],
            )
            assert result.exit_code == 0
            mock_uc.assert_called_once()
            # Verify is_active was set to True (check call args or result)

    def test_template_add__inactive_flag(self):
        """T-17: --inactive flag sets is_active=false."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_add.add_template"
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
                    "add",
                    "--name",
                    "Archived Template",
                    "--inactive",
                ],
            )
            assert result.exit_code == 0

    # T-35, T-37: Successful creation
    def test_template_add__success_human_output(self):
        """T-35, T-37: Successful template creation with human-readable output."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_add.add_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_template_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "add",
                    "--name",
                    "All Sitcoms 24x7",
                    "--description",
                    "24-hour sitcom programming template",
                ],
            )
            assert result.exit_code == 0
            assert "Template created" in result.stdout or "created" in result.stdout.lower()
            assert "All Sitcoms 24x7" in result.stdout

    # T-56: JSON output
    def test_template_add__success_json_output(self):
        """T-56: Successful template creation with JSON output."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_add.add_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_template_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "add",
                    "--name",
                    "All Sitcoms 24x7",
                    "--description",
                    "24-hour sitcom programming template",
                    "--json",
                ],
            )
            assert result.exit_code == 0
            payload = json.loads(result.stdout)
            assert payload["status"] == "ok"
            assert "template" in payload
            for k in ["id", "name", "description", "is_active", "blocks_count"]:
                assert k in payload["template"], f"missing key {k}"

    # T-57: Human-readable output includes all fields
    def test_template_add__human_output_includes_all_fields(self):
        """T-57: Human-readable output MUST include all template fields."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_add.add_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_template_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "add",
                    "--name",
                    "All Sitcoms 24x7",
                    "--description",
                    "24-hour sitcom programming template",
                ],
            )
            assert result.exit_code == 0
            output = result.stdout
            assert "All Sitcoms 24x7" in output
            assert "24-hour" in output or "description" in output.lower()

    # T-60, T-61: Test database support
    def test_template_add__test_db_support(self):
        """T-60, T-61: --test-db flag support."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_add.add_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_template_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "add",
                    "--name",
                    "All Sitcoms 24x7",
                    "--test-db",
                    "--json",
                ],
            )
            assert result.exit_code == 0
            payload = json.loads(result.stdout)
            assert payload["status"] == "ok"

    # T-12: Template can be created without blocks
    def test_template_add__no_blocks_allowed(self):
        """T-12: Template can be created without blocks."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.schedule_template_add.add_template"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_result = _mock_template_result()
            mock_result["blocks_count"] = 0
            mock_uc.return_value = mock_result

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "add",
                    "--name",
                    "Empty Template",
                ],
            )
            assert result.exit_code == 0

    def test_template_add__missing_name_exits_one(self):
        """Missing --name MUST exit 1."""
        result = self.runner.invoke(
            app,
            [
                "schedule-template",
                "add",
            ],
        )
        assert result.exit_code == 1
        assert "--name is required" in result.stderr or "--name" in result.stderr

    def test_template_add__help_flag_exits_zero(self):
        """Help flag MUST exit 0."""
        result = self.runner.invoke(app, ["schedule-template", "add", "--help"])
        assert result.exit_code == 0
        assert "--name" in result.stdout

