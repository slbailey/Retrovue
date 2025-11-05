"""Template block show usecase (standalone blocks)."""

from __future__ import annotations

import json
import uuid as uuid_module
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplateBlock


def show_template_block(
    db: Session,
    *,
    block: str,
) -> dict[str, Any]:
    """Show a standalone ScheduleTemplateBlock and return a contract-aligned dict."""
    block_obj = None
    # Try UUID first
    try:
        uuid_obj = uuid_module.UUID(block)
        block_obj = db.execute(select(ScheduleTemplateBlock).where(ScheduleTemplateBlock.id == uuid_obj)).scalars().first()
    except ValueError:
        pass

    # If not found by UUID, try name (case-insensitive)
    if not block_obj:
        block_obj = (
            db.execute(select(ScheduleTemplateBlock).where(func.lower(ScheduleTemplateBlock.name) == block.lower()))
            .scalars()
            .first()
        )

    if block_obj is None:
        raise ValueError("Template block not found")

    # Parse rule_json for response
    try:
        rule_json_obj = json.loads(block_obj.rule_json)
    except json.JSONDecodeError:
        rule_json_obj = {}

    return {
        "id": str(block_obj.id),
        "name": block_obj.name,
        "rule_json": rule_json_obj,
        "created_at": block_obj.created_at.isoformat() if block_obj.created_at else None,
        "updated_at": block_obj.updated_at.isoformat() if block_obj.updated_at else None,
    }

