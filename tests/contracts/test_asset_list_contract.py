"""
Contract tests for `retrovue asset list` command.

Enforces CLI behavior, defaults, output formats, filtering, and test-db handling
as specified in docs/contracts/resources/AssetListContract.md.
"""

from __future__ import annotations

import json
from unittest.mock import ANY, MagicMock, patch

import pytest
from typer.testing import CliRunner

from retrovue.cli.main import app


class TestAssetListContract:
    def setup_method(self):
        self.runner = CliRunner()

    def test_help_flag_exits_zero(self):
        """
        CONTRACT: The command MUST support help and exit with code 0.
        """
        result = self.runner.invoke(app, ["asset", "list", "--help"])
        assert result.exit_code == 0
        assert "asset" in result.stdout and "list" in result.stdout

    def test_default_lists_broadcast_ready_assets(self):
        """
        CONTRACT: Default behavior lists broadcast-ready assets (state=ready, approved=true, not deleted).
        """
        rows = [
            {
                "uuid": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "collection_uuid": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "uri": "/media/r1.mp4",
                "state": "ready",
                "approved_for_broadcast": True,
                "discovered_at": "2025-10-30T12:00:00Z",
            }
        ]

        with patch("retrovue.cli.commands.asset._get_db_context") as mock_db_ctx, patch(
            "retrovue.usecases.asset_list.list_assets", return_value=rows
        ) as list_fn:
            db_cm = MagicMock()
            db = MagicMock()
            db_cm.__enter__.return_value = db
            mock_db_ctx.return_value = db_cm

            result = self.runner.invoke(app, ["asset", "list", "--json"])

        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["status"] in ("ok", "success")
        assert payload["total"] == 1
        assert payload["assets"] == rows

        # Defaults must request broadcast-ready only
        call_kwargs = list_fn.call_args[1]
        assert call_kwargs.get("state") == "ready"
        assert call_kwargs.get("approved") is True
        assert call_kwargs.get("include_deleted") is False

    def test_json_output_format(self):
        """
        CONTRACT: --json MUST return stable envelope: status, total, assets.
        """
        rows = []
        with patch("retrovue.cli.commands.asset._get_db_context") as mock_db_ctx, patch(
            "retrovue.usecases.asset_list.list_assets", return_value=rows
        ):
            db_cm = MagicMock()
            db = MagicMock()
            db_cm.__enter__.return_value = db
            mock_db_ctx.return_value = db_cm

            result = self.runner.invoke(app, ["asset", "list", "--json"])

        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert set(payload.keys()) >= {"status", "total", "assets"}
        assert payload["assets"] == []

    def test_json_includes_rich_fields(self):
        """
        CONTRACT: JSON output MUST include rich fields usable for human context.
        - canonical_key, canonical_uri
        - title.name, title.kind, title.year
        - collection.name
        """
        rows = [
            {
                "uuid": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "uri": "/media/r1.mp4",
                "state": "ready",
                "approved_for_broadcast": True,
                "canonical_key": "canon:tv/airplane-2012",
                "canonical_uri": "rv://assets/abc123",
                "collection": {"uuid": "c" * 36, "name": "TV Shows"},
                "title": {"name": "Airplane (2012)", "kind": "movie", "year": 2012},
                "discovered_at": "2025-10-30T12:00:00Z",
            }
        ]
        with patch("retrovue.cli.commands.asset._get_db_context") as mock_db_ctx, patch(
            "retrovue.usecases.asset_list.list_assets", return_value=rows
        ):
            db_cm = MagicMock()
            db = MagicMock()
            db_cm.__enter__.return_value = db
            mock_db_ctx.return_value = db_cm

            result = self.runner.invoke(app, ["asset", "list", "--json"])

        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["assets"][0]["canonical_key"] == "canon:tv/airplane-2012"
        assert payload["assets"][0]["collection"]["name"] == "TV Shows"
        assert payload["assets"][0]["title"]["kind"] == "movie"

    def test_collection_and_state_filters(self):
        """
        CONTRACT: The command MUST support filtering by --collection and --state.
        """
        with patch("retrovue.cli.commands.asset._get_db_context") as mock_db_ctx, patch(
            "retrovue.usecases.asset_list.list_assets", return_value=[]
        ) as list_fn:
            db_cm = MagicMock()
            db = MagicMock()
            db_cm.__enter__.return_value = db
            mock_db_ctx.return_value = db_cm

            result = self.runner.invoke(
                app,
                [
                    "asset",
                    "list",
                    "--collection",
                    "22222222-2222-2222-2222-222222222222",
                    "--state",
                    "enriching",
                ],
            )

        assert result.exit_code == 0
        list_fn.assert_called_once()
        kwargs = list_fn.call_args[1]
        assert kwargs.get("collection_uuid") == "22222222-2222-2222-2222-222222222222"
        assert kwargs.get("state") == "enriching"

    def test_invalid_state_exits_one(self):
        """
        CONTRACT: Invalid --state MUST exit with code 1.
        """
        with patch("retrovue.cli.commands.asset._get_db_context") as mock_db_ctx:
            db_cm = MagicMock()
            db = MagicMock()
            db_cm.__enter__.return_value = db
            mock_db_ctx.return_value = db_cm

            result = self.runner.invoke(app, ["asset", "list", "--state", "bogus"])

        assert result.exit_code == 1
        out = result.stderr or result.stdout
        assert "Invalid state" in out

    def test_test_db_mode_uses_isolated_session(self):
        """
        CONTRACT: --test-db MUST use test sessionmaker path when available and preserve output shape.
        """
        rows = [
            {
                "uuid": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "collection_uuid": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "uri": "/media/r1.mp4",
                "state": "ready",
                "approved_for_broadcast": True,
                "discovered_at": "2025-10-30T12:00:00Z",
            }
        ]
        with patch("retrovue.cli.commands.asset.get_sessionmaker") as get_sm, patch(
            "retrovue.cli.commands.asset.session"
        ) as default_session, patch("retrovue.usecases.asset_list.list_assets", return_value=rows):
            TestSM = MagicMock(name="TestSessionmaker")
            TestCtx = MagicMock(name="TestSessionContext")
            TestSM.return_value = TestCtx
            get_sm.return_value = TestSM
            TestCtx.__enter__.return_value = MagicMock()

            result = self.runner.invoke(app, ["asset", "list", "--json", "--test-db"])

        assert result.exit_code == 0
        get_sm.assert_called_once_with(for_test=True)
        default_session.assert_not_called()
        payload = json.loads(result.stdout)
        assert payload["total"] == 1

    def test_no_assets_prints_message_and_exits_zero(self):
        """
        CONTRACT: Empty result prints informative message and exits 0 in human-readable mode.
        """
        with patch("retrovue.cli.commands.asset._get_db_context") as mock_db_ctx, patch(
            "retrovue.usecases.asset_list.list_assets", return_value=[]
        ):
            db_cm = MagicMock()
            db = MagicMock()
            db_cm.__enter__.return_value = db
            mock_db_ctx.return_value = db_cm

            result = self.runner.invoke(app, ["asset", "list"])  # no --json

        assert result.exit_code == 0
        assert "No assets found" in result.stdout

    def test_human_output_shows_minimum_columns(self):
        """
        CONTRACT: Human-readable output MUST include canonical ID, title, and type.
        """
        rows = [
            {
                "uuid": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "uri": "/media/r1.mp4",
                "state": "ready",
                "approved_for_broadcast": True,
                "canonical_key": "canon:tv/airplane-2012",
                "title": {"name": "Airplane (2012)", "kind": "movie", "year": 2012},
            }
        ]
        with patch("retrovue.cli.commands.asset._get_db_context") as mock_db_ctx, patch(
            "retrovue.usecases.asset_list.list_assets", return_value=rows
        ):
            db_cm = MagicMock()
            db = MagicMock()
            db_cm.__enter__.return_value = db
            mock_db_ctx.return_value = db_cm

            result = self.runner.invoke(app, ["asset", "list"])  # human-readable

        assert result.exit_code == 0
        out = result.stdout
        assert "canon:tv/airplane-2012" in out
        assert "Airplane (2012)" in out
        assert "movie" in out


