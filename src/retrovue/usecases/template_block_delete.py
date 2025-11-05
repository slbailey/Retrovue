"""Template block delete usecase (standalone blocks)."""

from __future__ import annotations

import uuid as uuid_module
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplateBlock, ScheduleTemplateBlockInstance


def delete_template_block(
    db: Session,
    *,
    block: str,
) -> dict[str, Any]:
    """Delete a standalone ScheduleTemplateBlock and return a contract-aligned dict."""
    block_obj = None
    # Try UUID first
    try:
        uuid_obj = uuid_module.UUID(block)
        block_obj = db.execute(select(ScheduleTemplateBlock).where(ScheduleTemplateBlock.id == uuid_obj)).scalars().first()
    except ValueError:
        pass

    # If not found by UUID, try name (case-insensitive)
    if not block_obj:
        block_obj = (
            db.execute(select(ScheduleTemplateBlock).where(func.lower(ScheduleTemplateBlock.name) == block.lower()))
            .scalars()
            .first()
        )

    if block_obj is None:
        raise ValueError("Template block not found")

    uuid_obj = block_obj.id

    # Check for dependent instances
    instances = (
        db.execute(
            select(ScheduleTemplateBlockInstance).where(ScheduleTemplateBlockInstance.block_id == uuid_obj)
        )
        .scalars()
        .all()
    )
    if instances:
        raise ValueError(
            "Cannot delete template block with active template instances. Remove all instances first."
        )

    block_id_str = str(block_obj.id)
    db.delete(block_obj)
    db.commit()

    return {"status": "deleted", "id": block_id_str}

