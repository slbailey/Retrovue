"""Schedule template delete usecase."""

from __future__ import annotations

import uuid as uuid_module
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplate, ScheduleTemplateBlockInstance


def delete_template(
    db: Session,
    *,
    template: str,
) -> dict[str, Any]:
    """Delete a ScheduleTemplate and return a contract-aligned dict."""
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

    uuid_obj = template_obj.id

    # Check for dependent block instances
    instances = (
        db.execute(
            select(ScheduleTemplateBlockInstance).where(ScheduleTemplateBlockInstance.template_id == uuid_obj)
        )
        .scalars()
        .all()
    )
    if instances:
        raise ValueError("Cannot delete template with blocks. Remove all blocks first.")

    # TODO: Check for dependent SchedulePlan records (when SchedulePlan entity exists)
    # TODO: Check for dependent BroadcastScheduleDay records (when entity exists)

    template_id_str = str(template_obj.id)
    db.delete(template_obj)
    db.commit()

    return {"status": "deleted", "id": template_id_str}

