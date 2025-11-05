"""Schedule template block update usecase."""

from __future__ import annotations

import json
import uuid as uuid_module
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplateBlock
from .schedule_template_block_add import (
    _check_overlap,
    _validate_rule_json,
    _validate_time_logic,
)


def update_template_block(
    db: Session,
    *,
    block_id: str,
    start_time: str | None = None,
    end_time: str | None = None,
    rule_json: str | None = None,
) -> dict[str, Any]:
    """Update a ScheduleTemplateBlock and return a contract-aligned dict."""
    # Find block by UUID
    try:
        uuid_obj = uuid_module.UUID(block_id)
        block = db.execute(select(ScheduleTemplateBlock).where(ScheduleTemplateBlock.id == uuid_obj)).scalars().first()
    except ValueError:
        raise ValueError("Template block not found")

    if block is None:
        raise ValueError("Template block not found")

    # Check if any field is provided
    if start_time is None and end_time is None and rule_json is None:
        raise ValueError(
            "At least one field (--start-time, --end-time, or --rule-json) must be provided."
        )

    # Prepare new values
    new_start_time = start_time if start_time is not None else block.start_time
    new_end_time = end_time if end_time is not None else block.end_time

    # Validate time format and logic if times are being updated
    if start_time is not None or end_time is not None:
        _validate_time_logic(new_start_time, new_end_time)

    # Validate rule_json if provided
    if rule_json is not None:
        _validate_rule_json(rule_json)
        block.rule_json = rule_json

    # Update times if provided
    if start_time is not None:
        block.start_time = start_time
    if end_time is not None:
        block.end_time = end_time

    # Re-check overlap with updated times
    if start_time is not None or end_time is not None:
        _check_overlap(db, block.template_id, new_start_time, new_end_time, exclude_block_id=block.id)

    db.commit()
    db.refresh(block)

    # Parse rule_json for response
    try:
        rule_json_obj = json.loads(block.rule_json)
    except json.JSONDecodeError:
        rule_json_obj = {}

    return {
        "id": str(block.id),
        "template_id": str(block.template_id),
        "start_time": block.start_time,
        "end_time": block.end_time,
        "rule_json": rule_json_obj,
        "created_at": block.created_at.isoformat() if block.created_at else None,
        "updated_at": block.updated_at.isoformat() if block.updated_at else None,
    }

