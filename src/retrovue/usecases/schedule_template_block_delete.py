"""Schedule template block delete usecase."""

from __future__ import annotations

import uuid as uuid_module
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplateBlock


def delete_template_block(
    db: Session,
    *,
    block_id: str,
) -> dict[str, Any]:
    """Delete a ScheduleTemplateBlock and return a contract-aligned dict."""
    # Find block by UUID
    try:
        uuid_obj = uuid_module.UUID(block_id)
        block = db.execute(select(ScheduleTemplateBlock).where(ScheduleTemplateBlock.id == uuid_obj)).scalars().first()
    except ValueError:
        raise ValueError("Template block not found")

    if block is None:
        raise ValueError("Template block not found")

    # TODO: Check for dependent SchedulePlanBlockAssignment records (when entity exists)
    # For now, we allow deletion

    block_id_str = str(block.id)
    db.delete(block)
    db.commit()

    return {"status": "deleted", "id": block_id_str}

