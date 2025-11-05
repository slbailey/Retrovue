"""Template block instance show usecase (show block instance in template)."""

from __future__ import annotations

import json
import uuid as uuid_module
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplateBlockInstance


def show_template_block_instance(
    db: Session,
    *,
    instance_id: str,
) -> dict[str, Any]:
    """Show a template block instance and return a contract-aligned dict."""
    # Find instance by UUID
    try:
        uuid_obj = uuid_module.UUID(instance_id)
        instance = db.execute(
            select(ScheduleTemplateBlockInstance).where(ScheduleTemplateBlockInstance.id == uuid_obj)
        ).scalars().first()
    except ValueError:
        raise ValueError("Template block instance not found")

    if instance is None:
        raise ValueError("Template block instance not found")

    # Load block to get name and rule_json
    block = instance.block
    try:
        rule_json_obj = json.loads(block.rule_json)
    except json.JSONDecodeError:
        rule_json_obj = {}

    return {
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

