"""Schedule template update usecase."""

from __future__ import annotations

import uuid as uuid_module
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplate


def update_template(
    db: Session,
    *,
    template: str,
    name: str | None = None,
    description: str | None = None,
    is_active: bool | None = None,
) -> dict[str, Any]:
    """Update a ScheduleTemplate and return a contract-aligned dict."""
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

    # Check if any field is provided
    if name is None and description is None and is_active is None:
        raise ValueError(
            "At least one field (--name, --description, or --active/--inactive) must be provided."
        )

    # Validate name if provided
    if name is not None:
        if not name:
            raise ValueError("Template name cannot be empty.")
        if len(name) > 255:
            raise ValueError("Template name exceeds maximum length (255 characters).")

        # Validate name uniqueness (case-insensitive, excluding current template)
        existing = (
            db.query(ScheduleTemplate)
            .filter(func.lower(ScheduleTemplate.name) == name.lower())
            .filter(ScheduleTemplate.id != template_obj.id)
            .first()
        )
        if existing is not None:
            raise ValueError("Template name already exists.")

        template_obj.name = name

    if description is not None:
        template_obj.description = description

    if is_active is not None:
        template_obj.is_active = is_active

    db.commit()
    db.refresh(template_obj)

    # Count block instances
    blocks_count = len(template_obj.block_instances) if template_obj.block_instances else 0

    return {
        "id": str(template_obj.id),
        "name": template_obj.name,
        "description": template_obj.description,
        "is_active": template_obj.is_active,
        "blocks_count": blocks_count,
        "created_at": template_obj.created_at.isoformat() if template_obj.created_at else None,
        "updated_at": template_obj.updated_at.isoformat() if template_obj.updated_at else None,
    }

