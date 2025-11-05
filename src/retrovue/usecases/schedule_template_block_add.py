"""Schedule template block add usecase."""

from __future__ import annotations

import json
import uuid as uuid_module
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplate, ScheduleTemplateBlock


def _validate_time_format(time_str: str) -> tuple[int, int]:
    """Validate HH:MM format and return (hour, minute)."""
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            raise ValueError("Invalid time format. Expected HH:MM (00:00-23:59).")
        hour = int(parts[0])
        minute = int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Invalid time format. Expected HH:MM (00:00-23:59).")
        return hour, minute
    except (ValueError, IndexError) as e:
        if isinstance(e, ValueError) and "Invalid time format" in str(e):
            raise
        raise ValueError("Invalid time format. Expected HH:MM (00:00-23:59).")


def _validate_time_logic(start_time: str, end_time: str) -> None:
    """Validate that start_time < end_time."""
    start_hour, start_minute = _validate_time_format(start_time)
    end_hour, end_minute = _validate_time_format(end_time)

    start_total = start_hour * 60 + start_minute
    end_total = end_hour * 60 + end_minute

    if start_total >= end_total:
        raise ValueError("start_time must be less than end_time.")


def _check_overlap(
    db: Session,
    template_id: uuid_module.UUID,
    start_time: str,
    end_time: str,
    exclude_block_id: uuid_module.UUID | None = None,
) -> None:
    """Check if the time range overlaps with existing blocks in the template."""
    # Convert times to minutes for comparison
    start_hour, start_minute = _validate_time_format(start_time)
    end_hour, end_minute = _validate_time_format(end_time)
    start_total = start_hour * 60 + start_minute
    end_total = end_hour * 60 + end_minute

    # Get all blocks for this template
    query = db.query(ScheduleTemplateBlock).filter(ScheduleTemplateBlock.template_id == template_id)
    if exclude_block_id:
        query = query.filter(ScheduleTemplateBlock.id != exclude_block_id)
    existing_blocks = query.all()

    for block in existing_blocks:
        block_start_hour, block_start_minute = _validate_time_format(block.start_time)
        block_end_hour, block_end_minute = _validate_time_format(block.end_time)
        block_start_total = block_start_hour * 60 + block_start_minute
        block_end_total = block_end_hour * 60 + block_end_minute

        # Check overlap: (start < other.end) AND (end > other.start)
        # Blocks that touch at boundaries are allowed (not overlapping)
        if start_total < block_end_total and end_total > block_start_total:
            raise ValueError("Block overlaps with existing block(s) in template.")


def _validate_rule_json(rule_json_str: str) -> dict[str, Any]:
    """Validate rule_json and return parsed dict."""
    try:
        rule_json_obj = json.loads(rule_json_str)
    except json.JSONDecodeError:
        raise ValueError("rule_json must be valid JSON.")

    if not isinstance(rule_json_obj, dict):
        raise ValueError("rule_json must be a JSON object.")

    return rule_json_obj


def add_template_block(
    db: Session,
    *,
    template_id: str,
    start_time: str,
    end_time: str,
    rule_json: str,
) -> dict[str, Any]:
    """Create a ScheduleTemplateBlock and return a contract-aligned dict.

    Minimal validation aligned with ScheduleTemplateBlockContract.md.
    """
    # Validate template exists
    try:
        template_uuid = uuid_module.UUID(template_id)
        template = db.execute(select(ScheduleTemplate).where(ScheduleTemplate.id == template_uuid)).scalars().first()
    except ValueError:
        raise ValueError("Template not found")

    if template is None:
        raise ValueError("Template not found")

    # Validate time format and logic
    _validate_time_logic(start_time, end_time)

    # Validate rule_json
    _validate_rule_json(rule_json)

    # Check for overlap
    _check_overlap(db, template_uuid, start_time, end_time)

    block = ScheduleTemplateBlock(
        template_id=template_uuid,
        start_time=start_time,
        end_time=end_time,
        rule_json=rule_json,
    )

    db.add(block)
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

