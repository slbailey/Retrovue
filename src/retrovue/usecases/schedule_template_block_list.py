"""Schedule template block list usecase."""

from __future__ import annotations

import json
import uuid as uuid_module
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplate, ScheduleTemplateBlock


def list_template_blocks(
    db: Session,
    *,
    template_id: str,
) -> list[dict[str, Any]]:
    """List ScheduleTemplateBlocks for a template and return a contract-aligned list of dicts."""
    # Validate template exists
    try:
        template_uuid = uuid_module.UUID(template_id)
        template = db.execute(select(ScheduleTemplate).where(ScheduleTemplate.id == template_uuid)).scalars().first()
    except ValueError:
        raise ValueError("Template not found")

    if template is None:
        raise ValueError("Template not found")

    # Get blocks sorted by start_time (chronological order)
    blocks = (
        db.query(ScheduleTemplateBlock)
        .filter(ScheduleTemplateBlock.template_id == template_uuid)
        .order_by(ScheduleTemplateBlock.start_time)
        .all()
    )

    result = []
    for block in blocks:
        try:
            rule_json_obj = json.loads(block.rule_json)
        except json.JSONDecodeError:
            rule_json_obj = {}
        result.append(
            {
                "id": str(block.id),
                "template_id": str(block.template_id),
                "start_time": block.start_time,
                "end_time": block.end_time,
                "rule_json": rule_json_obj,
                "created_at": block.created_at.isoformat() if block.created_at else None,
                "updated_at": block.updated_at.isoformat() if block.updated_at else None,
            }
        )

    return result

