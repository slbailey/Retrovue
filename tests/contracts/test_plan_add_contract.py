"""Plan Add Contract Tests

Behavioral tests for plan add command.
"""

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from retrovue.cli.main import app


def _mock_plan_result():
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "channel_id": "660e8400-e29b-41d4-a716-446655440001",
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "priority": 10,
        "created_at": "2025-01-01T12:00:00Z",
        "updated_at": None,
    }


class TestPlanAddContract:
    def setup_method(self):
        self.runner = CliRunner()

    def test_plan_add_missing_start_date_exits_one(self):
        result = self.runner.invoke(
            app,
            [
                "channel",
                "plan",
                "test-channel",
                "add",
                "--end-date",
                "2025-12-31",
            ],
        )
        # Typer returns exit code 2 for missing required options (CLI usage error)
        assert result.exit_code in (1, 2)

    def test_plan_add_missing_end_date_exits_one(self):
        result = self.runner.invoke(
            app,
            [
                "channel",
                "plan",
                "test-channel",
                "add",
                "--start-date",
                "2025-01-01",
            ],
        )
        # Typer returns exit code 2 for missing required options (CLI usage error)
        assert result.exit_code in (1, 2)

    def test_plan_add_success_human(self):
        with patch("retrovue.cli.commands.channel.session") as mock_session, patch(
            "retrovue.usecases.plan_add.add_plan"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_plan_result()

            result = self.runner.invoke(
                app,
                [
                    "channel",
                    "plan",
                    "test-channel",
                    "add",
                    "--start-date",
                    "2025-01-01",
                    "--end-date",
                    "2025-12-31",
                    "--priority",
                    "10",
                ],
            )
            assert result.exit_code == 0
            assert "Plan created" in result.stdout or "plan" in result.stdout.lower()

    def test_plan_add_success_json(self):
        with patch("retrovue.cli.commands.channel.session") as mock_session, patch(
            "retrovue.usecases.plan_add.add_plan"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_plan_result()

            result = self.runner.invoke(
                app,
                [
                    "channel",
                    "plan",
                    "test-channel",
                    "add",
                    "--start-date",
                    "2025-01-01",
                    "--end-date",
                    "2025-12-31",
                    "--json",
                ],
            )
            assert result.exit_code == 0
            payload = json.loads(result.stdout)
            assert payload["status"] == "ok"
            for k in ["id", "channel_id", "start_date", "end_date", "priority"]:
                assert k in payload["plan"], f"missing key {k}"

    def test_plan_add_invalid_date_format_exits_one(self):
        with patch("retrovue.cli.commands.channel.session") as mock_session, patch(
            "retrovue.usecases.plan_add.add_plan"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("Invalid date format. Use YYYY-MM-DD")

            result = self.runner.invoke(
                app,
                [
                    "channel",
                    "plan",
                    "test-channel",
                    "add",
                    "--start-date",
                    "2025/01/01",  # Wrong format
                    "--end-date",
                    "2025-12-31",
                ],
            )
            assert result.exit_code == 1
            assert "date format" in result.stderr.lower() or "Invalid" in result.stderr

    def test_plan_add_start_after_end_exits_one(self):
        with patch("retrovue.cli.commands.channel.session") as mock_session, patch(
            "retrovue.usecases.plan_add.add_plan"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("start_date must be <= end_date")

            result = self.runner.invoke(
                app,
                [
                    "channel",
                    "plan",
                    "test-channel",
                    "add",
                    "--start-date",
                    "2025-12-31",
                    "--end-date",
                    "2025-01-01",
                ],
            )
            assert result.exit_code == 1
            assert "start_date" in result.stderr or "end_date" in result.stderr

    def test_plan_add_channel_not_found_exits_one(self):
        with patch("retrovue.cli.commands.channel.session") as mock_session, patch(
            "retrovue.usecases.plan_add.add_plan"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("Channel 'test-channel' not found")

            result = self.runner.invoke(
                app,
                [
                    "channel",
                    "plan",
                    "test-channel",
                    "add",
                    "--start-date",
                    "2025-01-01",
                    "--end-date",
                    "2025-12-31",
                ],
            )
            assert result.exit_code == 1
            assert "not found" in result.stderr.lower()

    def test_plan_add_duplicate_date_range_exits_one(self):
        with patch("retrovue.cli.commands.channel.session") as mock_session, patch(
            "retrovue.usecases.plan_add.add_plan"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError(
                "Plan already exists for channel test-channel with date range 2025-01-01 to 2025-12-31"
            )

            result = self.runner.invoke(
                app,
                [
                    "channel",
                    "plan",
                    "test-channel",
                    "add",
                    "--start-date",
                    "2025-01-01",
                    "--end-date",
                    "2025-12-31",
                ],
            )
            assert result.exit_code == 1
            assert "already exists" in result.stderr.lower()

    def test_plan_add_help_flag_exits_zero(self):
        result = self.runner.invoke(app, ["channel", "plan", "test-channel", "add", "--help"])
        assert result.exit_code == 0
        assert "--start-date" in result.stdout

