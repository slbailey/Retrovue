from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from ..domain.entities import Channel, SchedulePlan


def add_plan(
    db: Session,
    *,
    channel_id: str,
    start_date: str,
    end_date: str,
    priority: int | None = None,
) -> dict[str, Any]:
    """Create a SchedulePlan and return a contract-aligned dict.

    Args:
        db: Database session
        channel_id: Channel UUID (as string)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        priority: Optional priority (lower number = higher priority)

    Returns:
        Dictionary with plan details

    Raises:
        ValueError: If validation fails or channel not found
    """
    # Validate and parse dates
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError as e:
        raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {e}")

    if start > end:
        raise ValueError("start_date must be <= end_date")

    # Resolve channel
    try:
        import uuid as _uuid
        channel_uuid = _uuid.UUID(channel_id)
    except ValueError:
        raise ValueError(f"Invalid channel UUID: {channel_id}")

    channel = db.query(Channel).filter(Channel.id == channel_uuid).first()
    if not channel:
        raise ValueError(f"Channel '{channel_id}' not found")

    # Check for duplicate date range (unique constraint)
    existing = (
        db.query(SchedulePlan)
        .filter(
            SchedulePlan.channel_id == channel_uuid,
            SchedulePlan.start_date == start,
            SchedulePlan.end_date == end,
        )
        .first()
    )
    if existing:
        raise ValueError(
            f"Plan already exists for channel {channel_id} with date range {start_date} to {end_date}"
        )

    # Create plan
    plan = SchedulePlan(
        channel_id=channel_uuid,
        start_date=start,
        end_date=end,
        priority=priority,
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return {
        "id": str(plan.id),
        "channel_id": str(plan.channel_id),
        "start_date": plan.start_date.isoformat(),
        "end_date": plan.end_date.isoformat(),
        "priority": plan.priority,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
    }

