"""Template block add usecase (standalone blocks)."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplateBlock


def add_template_block(
    db: Session,
    *,
    name: str,
    rule_json: str,
) -> dict[str, Any]:
    """Create a standalone ScheduleTemplateBlock and return a contract-aligned dict."""
    # Validate name
    if not name:
        raise ValueError("Template block name cannot be empty.")
    if len(name) > 255:
        raise ValueError("Template block name exceeds maximum length (255 characters).")

    # Validate name uniqueness (case-insensitive)
    existing = (
        db.query(ScheduleTemplateBlock)
        .filter(func.lower(ScheduleTemplateBlock.name) == name.lower())
        .first()
    )
    if existing is not None:
        raise ValueError("Template block name already exists.")

    # Validate rule_json
    try:
        rule_json_obj = json.loads(rule_json)
    except json.JSONDecodeError:
        raise ValueError("rule_json must be valid JSON.")

    if not isinstance(rule_json_obj, dict):
        raise ValueError("rule_json must be a JSON object.")

    block = ScheduleTemplateBlock(
        name=name,
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
        "name": block.name,
        "rule_json": rule_json_obj,
        "created_at": block.created_at.isoformat() if block.created_at else None,
        "updated_at": block.updated_at.isoformat() if block.updated_at else None,
    }

