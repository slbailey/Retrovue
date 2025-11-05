"""Template block update usecase (standalone blocks)."""

from __future__ import annotations

import json
import uuid as uuid_module
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplateBlock


def update_template_block(
    db: Session,
    *,
    block: str,
    name: str | None = None,
    rule_json: str | None = None,
) -> dict[str, Any]:
    """Update a standalone ScheduleTemplateBlock and return a contract-aligned dict."""
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

    # Check if any field is provided
    if name is None and rule_json is None:
        raise ValueError(
            "At least one field (--name or --rule-json) must be provided."
        )

    # Validate and update name if provided
    if name is not None:
        if not name:
            raise ValueError("Template block name cannot be empty.")
        if len(name) > 255:
            raise ValueError("Template block name exceeds maximum length (255 characters).")

        # Validate name uniqueness (case-insensitive, excluding current block)
        existing = (
            db.query(ScheduleTemplateBlock)
            .filter(func.lower(ScheduleTemplateBlock.name) == name.lower())
            .filter(ScheduleTemplateBlock.id != block_obj.id)
            .first()
        )
        if existing is not None:
            raise ValueError("Template block name already exists.")

        block_obj.name = name

    # Validate and update rule_json if provided
    if rule_json is not None:
        try:
            rule_json_obj = json.loads(rule_json)
        except json.JSONDecodeError:
            raise ValueError("rule_json must be valid JSON.")

        if not isinstance(rule_json_obj, dict):
            raise ValueError("rule_json must be a JSON object.")

        block_obj.rule_json = rule_json

    db.commit()
    db.refresh(block_obj)

    # Parse rule_json for response
    try:
        rule_json_obj = json.loads(block_obj.rule_json)
    except json.JSONDecodeError:
        rule_json_obj = {}

    return {
        "id": str(block_obj.id),
        "name": block_obj.name,
        "rule_json": rule_json_obj,
        "created_at": block_obj.created_at.isoformat() if block_obj.created_at else None,
        "updated_at": block_obj.updated_at.isoformat() if block_obj.updated_at else None,
    }

