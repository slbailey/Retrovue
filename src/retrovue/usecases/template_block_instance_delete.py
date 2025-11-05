"""Template block instance delete usecase (remove block from template)."""

from __future__ import annotations

import uuid as uuid_module
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplateBlockInstance


def delete_template_block_instance(
    db: Session,
    *,
    instance_id: str,
) -> dict[str, Any]:
    """Delete a template block instance and return a contract-aligned dict."""
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

    # TODO: Check for dependent SchedulePlanBlockAssignment records (when entity exists)
    # For now, we allow deletion

    instance_id_str = str(instance.id)
    db.delete(instance)
    db.commit()

    return {"status": "deleted", "id": instance_id_str}

