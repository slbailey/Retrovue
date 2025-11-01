"""
Data contract tests for Asset List usecase.

Verifies filtering semantics and read-only guarantees.

CONTRACT: docs/contracts/resources/AssetListContract.md
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

try:
    from retrovue.usecases.asset_list import list_assets
except Exception:  # pragma: no cover - allow contract-first where impl may not exist yet
    list_assets = None  # type: ignore[assignment]


def _asset(**kwargs):
    defaults = dict(
        uuid="a" * 36,
        collection_uuid="b" * 36,
        uri="/media/a.mp4",
        state="ready",
        approved_for_broadcast=True,
        discovered_at=datetime(2025, 10, 30, 12, 0, tzinfo=UTC),
        is_deleted=False,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class _ScalarResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


@pytest.mark.skipif(list_assets is None, reason="usecase not implemented yet")
def test_default_filter_is_broadcast_ready():
    # Arrange: DB returns a mix of assets
    ready_approved = _asset(uuid="r" * 36, state="ready", approved_for_broadcast=True)
    ready_unapproved = _asset(uuid="u" * 36, state="ready", approved_for_broadcast=False)
    enriching = _asset(uuid="e" * 36, state="enriching", approved_for_broadcast=False)
    retired = _asset(uuid="t" * 36, state="retired", approved_for_broadcast=False)

    fake_db = MagicMock()
    fake_db.execute.return_value.scalars.return_value = _ScalarResult(
        [ready_approved, ready_unapproved, enriching, retired]
    )

    rows = list_assets(fake_db)

    # Only ready+approved+not deleted are returned
    ids = {r["uuid"] for r in rows}
    assert "r" * 36 in ids
    assert "u" * 36 not in ids
    assert "e" * 36 not in ids
    assert "t" * 36 not in ids


@pytest.mark.skipif(list_assets is None, reason="usecase not implemented yet")
def test_explicit_state_filter_overrides_default():
    enriching = _asset(uuid="e" * 36, state="enriching", approved_for_broadcast=False)
    fake_db = MagicMock()
    fake_db.execute.return_value.scalars.return_value = _ScalarResult([enriching])

    rows = list_assets(fake_db, state="enriching")

    assert len(rows) == 1
    assert rows[0]["uuid"] == "e" * 36


@pytest.mark.skipif(list_assets is None, reason="usecase not implemented yet")
def test_read_only_no_writes():
    fake_db = MagicMock()
    fake_db.execute.return_value.scalars.return_value = _ScalarResult([])

    _ = list_assets(fake_db)

    fake_db.add.assert_not_called()
    fake_db.commit.assert_not_called()


