"""Schedule template add usecase."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplate


def add_template(
    db: Session,
    *,
    name: str,
    description: str | None = None,
    is_active: bool = True,
) -> dict[str, Any]:
    """Create a ScheduleTemplate and return a contract-aligned dict.

    Minimal validation aligned with ScheduleTemplateContract.md.
    """
    # Validate name
    if not name:
        raise ValueError("Template name cannot be empty.")
    if len(name) > 255:
        raise ValueError("Template name exceeds maximum length (255 characters).")

    # Validate name uniqueness (case-insensitive)
    existing = (
        db.query(ScheduleTemplate)
        .filter(func.lower(ScheduleTemplate.name) == name.lower())
        .first()
    )
    if existing is not None:
        raise ValueError("Template name already exists.")

    template = ScheduleTemplate(
        name=name,
        description=description,
        is_active=is_active,
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    # Count block instances
    blocks_count = len(template.block_instances) if template.block_instances else 0

    return {
        "id": str(template.id),
        "name": template.name,
        "description": template.description,
        "is_active": template.is_active,
        "blocks_count": blocks_count,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    }

