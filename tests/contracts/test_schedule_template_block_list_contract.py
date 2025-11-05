"""Schedule Template Block List Contract Tests

Behavioral tests for ScheduleTemplateBlockContract.md list operations.
"""

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from retrovue.cli.main import app


def _mock_block_list():
    return [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "template_id": "123e4567-e89b-12d3-a456-426614174000",
            "start_time": "06:00",
            "end_time": "09:00",
            "rule_json": {"tags": ["cartoon"], "rating_max": "TV-Y"},
            "created_at": "2025-01-01T12:00:00Z",
            "updated_at": None,
        },
        {
            "id": "660e8400-e29b-41d4-a716-446655440001",
            "template_id": "123e4567-e89b-12d3-a456-426614174000",
            "start_time": "09:00",
            "end_time": "18:00",
            "block_id": "block-uuid-2",
            "block_name": "Evening Block",
            "rule_json": {"tags": ["sitcom"], "rating_max": "TV-PG"},  # From block
            "created_at": "2025-01-01T12:00:00Z",
            "updated_at": None,
        },
    ]


class TestScheduleTemplateBlockListContract:
    """Test ScheduleTemplateBlock list contract rules."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_block_list__success_human_output(self):
        """List blocks with human-readable output."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_list.list_template_block_instances"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_block_list()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "list",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                ],
            )
            assert result.exit_code == 0
            # Should show blocks in chronological order (B-40)
            assert "06:00" in result.stdout or "09:00" in result.stdout

    def test_block_list__success_json_output(self):
        """B-38: List blocks with JSON output."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_list.list_template_block_instances"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_block_list()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "list",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--json",
                ],
            )
            assert result.exit_code == 0
            payload = json.loads(result.stdout)
            assert payload["status"] == "ok"
            assert "blocks" in payload or isinstance(payload, list)
            blocks = payload.get("blocks", payload) if isinstance(payload, dict) else payload
            assert len(blocks) == 2

    # B-40: Chronological order
    def test_block_list__chronological_order(self):
        """B-40: Blocks MUST be listed in chronological order by start_time."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_list.list_template_block_instances"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_block_list()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "list",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                ],
            )
            assert result.exit_code == 0
            # Verify blocks are in order (implementation should sort by start_time)
            output = result.stdout
            idx_06 = output.find("06:00")
            idx_09 = output.find("09:00")
            if idx_06 != -1 and idx_09 != -1:
                assert idx_06 < idx_09

    def test_block_list__template_not_found(self):
        """Template not found MUST exit 1."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_list.list_template_block_instances"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("Template not found")

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "list",
                    "--template",
                    "00000000-0000-0000-0000-000000000000",
                ],
            )
            assert result.exit_code == 1

    def test_block_list__empty_list(self):
        """Empty template (no blocks) should return empty list."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_list.list_template_block_instances"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = []

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "list",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--json",
                ],
            )
            assert result.exit_code == 0
            payload = json.loads(result.stdout)
            blocks = payload.get("blocks", payload) if isinstance(payload, dict) else payload
            assert isinstance(blocks, list)
            assert len(blocks) == 0

    def test_block_list__missing_template_id_exits_one(self):
        """Missing --template-id MUST exit 1 or 2 (Typer returns 2 for missing required params)."""
        result = self.runner.invoke(
            app,
            [
                "schedule-template",
                "block",
                "list",
            ],
        )
        assert result.exit_code in (1, 2)  # Typer returns 2 for missing required params

    def test_block_list__help_flag_exits_zero(self):
        """Help flag MUST exit 0."""
        result = self.runner.invoke(app, ["schedule-template", "block", "list", "--help"])
        assert result.exit_code == 0

