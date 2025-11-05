"""Template block instance update usecase (update timing for block in template)."""

from __future__ import annotations

import uuid as uuid_module
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplateBlockInstance
from .template_block_instance_add import _check_overlap_for_instances, _validate_time_logic


def update_template_block_instance(
    db: Session,
    *,
    instance_id: str,
    start_time: str | None = None,
    end_time: str | None = None,
) -> dict[str, Any]:
    """Update a template block instance and return a contract-aligned dict."""
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

    # Check if any field is provided
    if start_time is None and end_time is None:
        raise ValueError(
            "At least one field (--start-time or --end-time) must be provided."
        )

    # Prepare new values
    new_start_time = start_time if start_time is not None else instance.start_time
    new_end_time = end_time if end_time is not None else instance.end_time

    # Validate time format and logic if times are being updated
    if start_time is not None or end_time is not None:
        _validate_time_logic(new_start_time, new_end_time)

    # Update times if provided
    if start_time is not None:
        instance.start_time = start_time
    if end_time is not None:
        instance.end_time = end_time

    # Re-check overlap with updated times
    if start_time is not None or end_time is not None:
        _check_overlap_for_instances(
            db, instance.template_id, new_start_time, new_end_time, exclude_instance_id=instance.id
        )

    db.commit()
    db.refresh(instance)

    return {
        "id": str(instance.id),
        "template_id": str(instance.template_id),
        "block_id": str(instance.block_id),
        "start_time": instance.start_time,
        "end_time": instance.end_time,
        "created_at": instance.created_at.isoformat() if instance.created_at else None,
        "updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
    }

