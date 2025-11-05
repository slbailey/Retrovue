"""Schedule template show usecase."""

from __future__ import annotations

import json
import uuid as uuid_module
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplate


def show_template(
    db: Session,
    *,
    template: str,
) -> dict[str, Any]:
    """Show a ScheduleTemplate and return a contract-aligned dict."""
    template_obj = None
    # Try UUID first
    try:
        uuid_obj = uuid_module.UUID(template)
        template_obj = db.execute(select(ScheduleTemplate).where(ScheduleTemplate.id == uuid_obj)).scalars().first()
    except ValueError:
        pass

    # If not found by UUID, try name (case-insensitive)
    if not template_obj:
        template_obj = (
            db.execute(select(ScheduleTemplate).where(func.lower(ScheduleTemplate.name) == template.lower()))
            .scalars()
            .first()
        )

    if template_obj is None:
        raise ValueError("Template not found")

    # Get block instances sorted by start_time
    instances = sorted(template_obj.block_instances, key=lambda i: i.start_time) if template_obj.block_instances else []

    # Parse rule_json for display
    blocks_data = []
    for instance in instances:
        block = instance.block
        try:
            rule_json_obj = json.loads(block.rule_json)
        except json.JSONDecodeError:
            rule_json_obj = {}
        blocks_data.append(
            {
                "block_name": block.name,
                "start_time": instance.start_time,
                "end_time": instance.end_time,
                "rule_json": rule_json_obj,
            }
        )

    # TODO: Count plans using this template (when SchedulePlan entity exists)
    plans_count = 0

    return {
        "id": str(template_obj.id),
        "name": template_obj.name,
        "description": template_obj.description,
        "is_active": template_obj.is_active,
        "blocks_count": len(instances),
        "plans_count": plans_count,
        "blocks": blocks_data,
        "created_at": template_obj.created_at.isoformat() if template_obj.created_at else None,
        "updated_at": template_obj.updated_at.isoformat() if template_obj.updated_at else None,
    }

