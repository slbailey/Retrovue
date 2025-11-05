"""Schedule template block show usecase."""

from __future__ import annotations

import json
import uuid as uuid_module
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplateBlock


def show_template_block(
    db: Session,
    *,
    block_id: str,
) -> dict[str, Any]:
    """Show a ScheduleTemplateBlock and return a contract-aligned dict."""
    # Find block by UUID
    try:
        uuid_obj = uuid_module.UUID(block_id)
        block = db.execute(select(ScheduleTemplateBlock).where(ScheduleTemplateBlock.id == uuid_obj)).scalars().first()
    except ValueError:
        raise ValueError("Template block not found")

    if block is None:
        raise ValueError("Template block not found")

    # Parse rule_json for response
    try:
        rule_json_obj = json.loads(block.rule_json)
    except json.JSONDecodeError:
        rule_json_obj = {}

    return {
        "id": str(block.id),
        "template_id": str(block.template_id),
        "start_time": block.start_time,
        "end_time": block.end_time,
        "rule_json": rule_json_obj,
        "created_at": block.created_at.isoformat() if block.created_at else None,
        "updated_at": block.updated_at.isoformat() if block.updated_at else None,
    }

