"""Schedule template list usecase."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplate


def list_templates(
    db: Session,
    *,
    active_only: bool = False,
) -> list[dict[str, Any]]:
    """List ScheduleTemplates and return a contract-aligned list of dicts."""
    query = db.query(ScheduleTemplate)

    if active_only:
        query = query.filter(ScheduleTemplate.is_active == True)  # noqa: E712

    templates = query.order_by(ScheduleTemplate.name).all()

    return [
        {
            "id": str(t.id),
            "name": t.name,
            "description": t.description,
            "is_active": t.is_active,
            "blocks_count": len(t.block_instances) if t.block_instances else 0,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        }
        for t in templates
    ]

