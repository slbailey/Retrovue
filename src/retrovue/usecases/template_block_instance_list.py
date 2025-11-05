"""Template block instance list usecase (list blocks in a template)."""

from __future__ import annotations

import json
import uuid as uuid_module
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplate, ScheduleTemplateBlockInstance


def list_template_block_instances(
    db: Session,
    *,
    template: str,
) -> list[dict[str, Any]]:
    """List template block instances for a template and return a contract-aligned list of dicts."""
    template_obj = None
    # Try UUID first
    try:
        template_uuid = uuid_module.UUID(template)
        template_obj = db.execute(select(ScheduleTemplate).where(ScheduleTemplate.id == template_uuid)).scalars().first()
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

    template_uuid = template_obj.id

    # Get instances sorted by start_time (chronological order)
    instances = (
        db.query(ScheduleTemplateBlockInstance)
        .filter(ScheduleTemplateBlockInstance.template_id == template_uuid)
        .order_by(ScheduleTemplateBlockInstance.start_time)
        .all()
    )

    result = []
    for instance in instances:
        # Load block to get name and rule_json
        block = instance.block
        try:
            rule_json_obj = json.loads(block.rule_json)
        except json.JSONDecodeError:
            rule_json_obj = {}
        result.append(
            {
                "id": str(instance.id),
                "template_id": str(instance.template_id),
                "block_id": str(instance.block_id),
                "block_name": block.name,
                "start_time": instance.start_time,
                "end_time": instance.end_time,
                "rule_json": rule_json_obj,
                "created_at": instance.created_at.isoformat() if instance.created_at else None,
                "updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
            }
        )

    return result

