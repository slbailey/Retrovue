"""Template block list usecase (standalone blocks)."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplateBlock


def list_template_blocks(
    db: Session,
) -> list[dict[str, Any]]:
    """List all standalone ScheduleTemplateBlocks and return a contract-aligned list of dicts."""
    blocks = db.query(ScheduleTemplateBlock).order_by(ScheduleTemplateBlock.name).all()

    result = []
    for block in blocks:
        try:
            rule_json_obj = json.loads(block.rule_json)
        except json.JSONDecodeError:
            rule_json_obj = {}
        result.append(
            {
                "id": str(block.id),
                "name": block.name,
                "rule_json": rule_json_obj,
                "created_at": block.created_at.isoformat() if block.created_at else None,
                "updated_at": block.updated_at.isoformat() if block.updated_at else None,
            }
        )

    return result

