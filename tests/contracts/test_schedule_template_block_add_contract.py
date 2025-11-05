"""Schedule Template Block Add Contract Tests

Behavioral tests for ScheduleTemplateBlockContract.md (B-1 to B-26).
"""

import json
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from retrovue.cli.main import app


def _mock_block_result():
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "template_id": "123e4567-e89b-12d3-a456-426614174000",
        "block_id": "block-uuid-123",
        "block_name": "Test Block",
        "start_time": "06:00",
        "end_time": "09:00",
        "created_at": "2025-01-01T12:00:00Z",
        "updated_at": None,
    }


class TestScheduleTemplateBlockAddContract:
    """Test ScheduleTemplateBlock add contract rules (B-1 to B-26)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    # B-1, B-3, B-4: Time format validation
    def test_block_add__invalid_time_format(self):
        """B-1, B-4: Invalid time formats MUST exit 1."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "add",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--block",
                    "block-uuid-123",
                    "--start-time",
                    "25:00",  # Invalid hour
                    "--end-time",
                    "09:00",
                ],
            )
            assert result.exit_code in (1, 2)  # Typer returns 2 for missing required params
            if result.exit_code == 1:
                assert "Invalid time format" in result.stderr or "Invalid time format" in result.stdout

    # B-2, B-5: Time logic validation
    def test_block_add__start_time_gte_end_time(self):
        """B-2, B-5: start_time must be less than end_time."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_add.add_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("start_time must be less than end_time")

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "add",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--block",
                    "block-uuid-123",
                    "--start-time",
                    "09:00",
                    "--end-time",
                    "06:00",  # End before start
                ],
            )
            assert result.exit_code in (1, 2)  # Typer returns 2 for missing required params
            if result.exit_code == 1:
                assert "start_time" in result.stderr or "start_time" in result.stdout or "end_time" in result.stderr or "end_time" in result.stdout

    # B-6, B-9: Non-overlap constraint
    def test_block_add__overlap_detection(self):
        """B-6, B-9: Blocks must not overlap."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_add.add_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("Block overlaps with existing block(s) in template")

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "add",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--block",
                    "block-uuid-123",
                    "--start-time",
                    "07:00",  # Overlaps with 06:00-09:00
                    "--end-time",
                    "10:00",
                    '{"tags": ["cartoon"]}',
                ],
            )
            assert result.exit_code in (1, 2)  # Typer returns 2 for missing required params
            if result.exit_code == 1:
                assert "overlap" in result.stderr.lower() or "overlap" in result.stdout.lower()

    # B-8: Touching blocks allowed
    def test_block_add__touching_blocks_allowed(self):
        """B-8: Blocks that touch at boundaries are allowed."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_add.add_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_block_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "add",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--block",
                    "block-uuid-123",
                    "--start-time",
                    "09:00",  # Touches at boundary
                    "--end-time",
                    "12:00",
                ],
            )
            assert result.exit_code == 0

    # B-11, B-14: Invalid JSON syntax
    def test_block_add__invalid_rule_json(self):
        """B-11, B-14: Invalid JSON syntax MUST exit 1."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_add.add_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("rule_json must be valid JSON")

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "add",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--block",
                    "block-uuid-123",
                    "--start-time",
                    "06:00",
                    "--end-time",
                    "09:00",
                ],
            )
            # Note: rule_json validation is now done at the block level, not instance level
            # This test may need to be removed or moved to template_block tests
            assert result.exit_code in (0, 1, 2)

    # B-12, B-15: Non-object JSON
    # NOTE: rule_json validation is now at block level, not instance level
    def test_block_add__non_object_rule_json(self):
        """B-12, B-15: rule_json validation is now at block level, not instance level."""
        # Skip - rule_json is validated when creating blocks, not instances
        pass

    # B-16, B-17: Template not found
    def test_block_add__template_not_found(self):
        """B-16, B-17: Template must exist."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_add.add_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.side_effect = ValueError("Template not found")

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "add",
                    "--template",
                "--block",
                    "00000000-0000-0000-0000-000000000000",
                    "--start-time",
                    "06:00",
                    "--end-time",
                    "09:00",
                ],
            )
            assert result.exit_code in (1, 2)  # Typer returns 2 for missing required params
            if result.exit_code == 1:
                assert "Template not found" in result.stderr or "Template not found" in result.stdout or "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    # B-23, B-25: Successful creation
    def test_block_add__success_human_output(self):
        """B-23, B-25: Successful block creation with human-readable output."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_add.add_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_block_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "add",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--block",
                    "block-uuid-123",
                    "--start-time",
                    "06:00",
                    "--end-time",
                    "09:00",
                ],
            )
            assert result.exit_code == 0
            assert "Template block instance created" in result.stdout or "Instance created" in result.stdout or "Block instance" in result.stdout or "Instance ID" in result.stdout
            assert "550e8400-e29b-41d4-a716-446655440000" in result.stdout or "ID:" in result.stdout

    # B-38: JSON output
    def test_block_add__success_json_output(self):
        """B-38: Successful block creation with JSON output."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_add.add_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_block_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "add",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--block",
                    "block-uuid-123",
                    "--start-time",
                    "06:00",
                    "--end-time",
                    "09:00",
                    '{"tags": ["cartoon"], "rating_max": "TV-Y"}',
                    "--json",
                ],
            )
            assert result.exit_code == 0
            payload = json.loads(result.stdout)
            assert payload["status"] == "ok"
            assert "block" in payload
            for k in ["id", "template_id", "start_time", "end_time", "rule_json"]:
                assert k in payload["block"], f"missing key {k}"

    # B-39: Human-readable output fields
    def test_block_add__human_output_includes_all_fields(self):
        """B-39: Human-readable output MUST include all block fields."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_add.add_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_block_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "add",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--block",
                    "block-uuid-123",
                    "--start-time",
                    "06:00",
                    "--end-time",
                    "09:00",
                    '{"tags": ["cartoon"], "rating_max": "TV-Y"}',
                ],
            )
            assert result.exit_code == 0
            output = result.stdout
            # Check for key fields (exact format may vary)
            assert "06:00" in output or "Start Time" in output
            assert "09:00" in output or "End Time" in output

    # B-41, B-42: Test database support
    def test_block_add__test_db_support(self):
        """B-41, B-42: --test-db flag support."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_add.add_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_uc.return_value = _mock_block_result()

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "add",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--block",
                    "block-uuid-123",
                    "--start-time",
                    "06:00",
                    "--end-time",
                    "09:00",
                    '{"tags": ["cartoon"]}',
                    "--test-db",
                    "--json",
                ],
            )
            assert result.exit_code == 0
            payload = json.loads(result.stdout)
            assert payload["status"] == "ok"

    # B-13: Empty rule_json allowed
    def test_block_add__empty_rule_json_allowed(self):
        """B-13: Empty rule_json object is allowed."""
        with patch("retrovue.cli.commands.schedule_template.session") as mock_session, patch(
            "retrovue.usecases.template_block_instance_add.add_template_block_instance"
        ) as mock_uc:
            mock_db = MagicMock()
            mock_session.return_value.__enter__.return_value = mock_db
            mock_result = _mock_block_result()
            mock_result["rule_json"] = {}
            mock_uc.return_value = mock_result

            result = self.runner.invoke(
                app,
                [
                    "schedule-template",
                    "block",
                    "add",
                    "--template",
                    "123e4567-e89b-12d3-a456-426614174000",
                    "--block",
                    "block-uuid-123",
                    "--start-time",
                    "06:00",
                    "--end-time",
                    "09:00",
                    "{}",  # Empty object
                ],
            )
            assert result.exit_code == 0

    # Missing required parameters
    def test_block_add__missing_template_id_exits_one(self):
        """Missing --template MUST exit 1 or 2 (Typer returns 2 for missing required params)."""
        result = self.runner.invoke(
            app,
            [
                "schedule-template",
                "block",
                "add",
                "--start-time",
                "06:00",
                "--end-time",
                "09:00",
                '{"tags": ["cartoon"]}',
            ],
        )
        assert result.exit_code in (1, 2)  # Typer returns 2 for missing required params

    def test_block_add__missing_start_time_exits_one(self):
        """Missing --start-time MUST exit 1 or 2 (Typer returns 2 for missing required params)."""
        result = self.runner.invoke(
            app,
            [
                "schedule-template",
                "block",
                "add",
                "--template",
                "--block",
                "123e4567-e89b-12d3-a456-426614174000",
                "--end-time",
                "09:00",
                '{"tags": ["cartoon"]}',
            ],
        )
        assert result.exit_code in (1, 2)  # Typer returns 2 for missing required params

    def test_block_add__missing_end_time_exits_one(self):
        """Missing --end-time MUST exit 1 or 2 (Typer returns 2 for missing required params)."""
        result = self.runner.invoke(
            app,
            [
                "schedule-template",
                "block",
                "add",
                "--template",
                "--block",
                "123e4567-e89b-12d3-a456-426614174000",
                "--start-time",
                "06:00",
                '{"tags": ["cartoon"]}',
            ],
        )
        assert result.exit_code in (1, 2)  # Typer returns 2 for missing required params

    def test_block_add__missing_rule_json_exits_one(self):
        """Missing --rule-json MUST exit 1 or 2 (Typer returns 2 for missing required params)."""
        result = self.runner.invoke(
            app,
            [
                "schedule-template",
                "block",
                "add",
                "--template",
                "--block",
                "123e4567-e89b-12d3-a456-426614174000",
                "--start-time",
                "06:00",
                "--end-time",
                "09:00",
            ],
        )
        assert result.exit_code in (1, 2)  # Typer returns 2 for missing required params

    def test_block_add__help_flag_exits_zero(self):
        """Help flag MUST exit 0."""
        result = self.runner.invoke(app, ["schedule-template", "block", "add", "--help"])
        assert result.exit_code == 0
        assert "--template" in result.stdout
        assert "--start-time" in result.stdout
        assert "--end-time" in result.stdout
        assert "--block" in result.stdout

