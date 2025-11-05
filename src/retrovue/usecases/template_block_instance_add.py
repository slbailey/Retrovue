"""Template block instance add usecase (add block to template with timing)."""

from __future__ import annotations

import uuid as uuid_module
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..domain.entities import ScheduleTemplate, ScheduleTemplateBlock, ScheduleTemplateBlockInstance


def _parse_time_with_next_day(time_str: str) -> tuple[int, int, bool]:
    """
    Parse time string in HH:MM or HH:MM+1 format.
    
    Returns:
        (hour, minute, is_next_day) where is_next_day is True if +1 notation is used
    """
    is_next_day = False
    if time_str.endswith("+1"):
        is_next_day = True
        time_str = time_str[:-2]  # Remove "+1"
    
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            raise ValueError("Time must be in HH:MM or HH:MM+1 format")
        hour = int(parts[0])
        minute = int(parts[1])
        if not (0 <= hour <= 23):
            raise ValueError("Hour must be between 0 and 23")
        if not (0 <= minute <= 59):
            raise ValueError("Minute must be between 0 and 59")
        return hour, minute, is_next_day
    except ValueError as e:
        raise ValueError(f"Invalid time format '{time_str}': {e}")


def _time_to_minutes_since_midnight(hour: int, minute: int, is_next_day: bool) -> int:
    """
    Convert time to minutes since midnight (00:00).
    
    Args:
        hour: Hour (0-23)
        minute: Minute (0-59)
        is_next_day: True if +1 notation (next calendar day)
    
    Returns:
        Minutes since midnight of the current/next calendar day
    """
    total_minutes = hour * 60 + minute
    if is_next_day:
        return total_minutes + 1440  # Add 24 hours for next calendar day
    return total_minutes


def _validate_time_logic(start_time: str, end_time: str, broadcast_day_start_minutes: int = 360) -> None:
    """
    Validate time logic within broadcast day constraints.
    
    Broadcast day runs from 06:00 to 06:00+1 (next calendar day).
    - Valid: 22:00 to 04:00 (spans midnight, ends before 06:00, same broadcast day)
    - Invalid: 22:00 to 08:00 (spans midnight, ends after 06:00, crosses broadcast day boundary)
    - Valid: 06:00 to 06:00+1 (full broadcast day from start to end)
    - Valid: 22:00 to 02:00+1 (spans midnight, ends at 02:00 next day, before 06:00 boundary)
    - Invalid: 22:00 to 08:00+1 (spans midnight, ends after 06:00 next day, crosses boundary)
    
    Strategy:
    1. Convert both times to absolute minutes (accounting for +1)
    2. Normalize to a reference day (the day containing the start time's broadcast day)
    3. Check both are within the same broadcast day (06:00 to 06:00+1)
    4. Check end doesn't cross the 06:00+1 boundary
    
    Args:
        start_time: Start time in HH:MM or HH:MM+1 format
        end_time: End time in HH:MM or HH:MM+1 format
        broadcast_day_start_minutes: Minutes after midnight when broadcast day starts (default 360 = 06:00)
    """
    start_hour, start_minute, start_next = _parse_time_with_next_day(start_time)
    end_hour, end_minute, end_next = _parse_time_with_next_day(end_time)
    
    # Convert to minutes since midnight
    start_mins_base = start_hour * 60 + start_minute
    end_mins_base = end_hour * 60 + end_minute
    
    # Normalize to start's calendar day as reference
    # If start has +1, normalize to day 0 by subtracting 1440
    start_day_offset = 1440 if start_next else 0
    start_mins = start_mins_base - start_day_offset
    
    # Determine end's calendar day relative to start
    # If end has +1, it's in next calendar day after start's day
    # If end doesn't have +1 but end < start, end is implicitly in next calendar day
    end_day_offset = 0
    if end_next:
        end_day_offset = 1440  # Explicitly next calendar day
    elif not start_next and end_mins_base < start_mins_base:
        # End is implicitly in next calendar day (e.g., 22:00 to 04:00)
        end_day_offset = 1440
    
    end_mins = end_mins_base + end_day_offset - start_day_offset
    
    # Now both times are relative to day 0
    # Determine which broadcast day start belongs to
    # Broadcast day 0 runs from 06:00 (360) to 06:00+1 (1800) of day 0
    # If start < 06:00, it's in broadcast day -1 (previous day's broadcast day)
    
    if start_mins < broadcast_day_start_minutes:
        # Start is in previous broadcast day (before 06:00 of day 0)
        # Broadcast day -1: 06:00 of day -1 (which is 06:00-1440 = -1080) to 06:00 of day 0 (360)
        # Normalize start to broadcast day -1: start_mins + 1440
        start_broadcast = start_mins + 1440 - broadcast_day_start_minutes
        
        # End must also be in broadcast day -1
        if end_next:
            # End is explicitly in next calendar day
            # For end to be in broadcast day -1, it must be < 06:00 of day 0
            # end_mins is already normalized (end_mins - 1440 if start had +1)
            # But if end has +1, end_mins already includes +1440
            # So we need: end_mins (without the +1 part) < 360
            end_broadcast = end_mins - broadcast_day_start_minutes
            if end_broadcast > 1440:
                raise ValueError(f"Block crosses broadcast day boundary (ends after {broadcast_day_start_minutes//60:02d}:{broadcast_day_start_minutes%60:02d})")
        elif end_mins < broadcast_day_start_minutes:
            # End is also before 06:00, same broadcast day
            end_broadcast = end_mins + 1440 - broadcast_day_start_minutes
        else:
            # End is after 06:00, crosses boundary
            raise ValueError(f"Block crosses broadcast day boundary (ends after {broadcast_day_start_minutes//60:02d}:{broadcast_day_start_minutes%60:02d})")
        
        if end_broadcast <= start_broadcast:
            raise ValueError("end_time must be after start_time")
    else:
        # Start is at or after 06:00 of day 0, in broadcast day 0
        start_broadcast = start_mins - broadcast_day_start_minutes
        
        # Calculate end relative to broadcast day 0
        # end_mins is already normalized to day 0 (includes day offset adjustments)
        # If end_mins >= 1440, end is in next calendar day
        if end_mins >= 1440:
            # End is in next calendar day (day 1)
            # For it to be in broadcast day 0, it must be < 06:00 of day 1
            # Broadcast day 0 ends at 06:00 of day 1 = 1800 minutes since 06:00 of day 0
            end_broadcast = end_mins - broadcast_day_start_minutes
            if end_broadcast > 1440:
                raise ValueError(f"Block crosses broadcast day boundary (ends after next day's {broadcast_day_start_minutes//60:02d}:{broadcast_day_start_minutes%60:02d})")
        elif end_mins < broadcast_day_start_minutes:
            # End is before 06:00 of day 0, but start is after 06:00
            # This means end is in next calendar day (wrapped around from previous day)
            # end_mins is still < 1440, so it's in day 0, but we need to treat it as day 1
            end_broadcast = end_mins + 1440 - broadcast_day_start_minutes
            if end_broadcast > 1440:
                raise ValueError(f"Block crosses broadcast day boundary (ends after next day's {broadcast_day_start_minutes//60:02d}:{broadcast_day_start_minutes%60:02d})")
        else:
            # End is after 06:00 of day 0, same broadcast day
            end_broadcast = end_mins - broadcast_day_start_minutes
        
        if end_broadcast <= start_broadcast:
            raise ValueError("end_time must be after start_time")
    
    # Final check: duration cannot exceed 24 hours
    duration = end_broadcast - start_broadcast
    if duration > 1440:
        raise ValueError("Block duration exceeds broadcast day (max 24 hours)")


def _resolve_template(db: Session, template_selector: str) -> ScheduleTemplate:
    """Resolve template selector (UUID or name) to ScheduleTemplate entity."""
    template = None
    # Try UUID first
    try:
        template_uuid = uuid_module.UUID(template_selector)
        template = db.execute(select(ScheduleTemplate).where(ScheduleTemplate.id == template_uuid)).scalars().first()
    except ValueError:
        pass

    # If not found by UUID, try name (case-insensitive)
    if not template:
        template = (
            db.execute(select(ScheduleTemplate).where(func.lower(ScheduleTemplate.name) == template_selector.lower()))
            .scalars()
            .first()
        )

    if template is None:
        raise ValueError("Template not found")

    return template


def _resolve_block(db: Session, block_selector: str) -> ScheduleTemplateBlock:
    """Resolve block selector (UUID or name) to ScheduleTemplateBlock entity."""
    block = None
    # Try UUID first
    try:
        block_uuid = uuid_module.UUID(block_selector)
        block = db.execute(select(ScheduleTemplateBlock).where(ScheduleTemplateBlock.id == block_uuid)).scalars().first()
    except ValueError:
        pass

    # If not found by UUID, try name (case-insensitive)
    if not block:
        block = (
            db.execute(select(ScheduleTemplateBlock).where(func.lower(ScheduleTemplateBlock.name) == block_selector.lower()))
            .scalars()
            .first()
        )

    if block is None:
        raise ValueError("Template block not found")

    return block


def add_template_block_instance(
    db: Session,
    *,
    template: str,
    block: str,
    start_time: str,
    end_time: str,
) -> dict[str, Any]:
    """Add a template block instance (link block to template with timing) and return a contract-aligned dict."""
    template_obj = _resolve_template(db, template)
    block_obj = _resolve_block(db, block)

    template_uuid = template_obj.id
    block_uuid = block_obj.id

    # Validate time format and logic
    _validate_time_logic(start_time, end_time)

    # Check for overlap with other instances in this template
    _check_overlap_for_instances(db, template_uuid, start_time, end_time)

    instance = ScheduleTemplateBlockInstance(
        template_id=template_uuid,
        block_id=block_uuid,
        start_time=start_time,
        end_time=end_time,
    )

    db.add(instance)
    db.commit()
    db.refresh(instance)

    return {
        "id": str(instance.id),
        "template_id": str(instance.template_id),
        "block_id": str(instance.block_id),
        "block_name": block_obj.name,
        "start_time": instance.start_time,
        "end_time": instance.end_time,
        "created_at": instance.created_at.isoformat() if instance.created_at else None,
        "updated_at": instance.updated_at.isoformat() if instance.updated_at else None,
    }


def _time_to_comparable_minutes(time_str: str, reference_start_mins: int = 0) -> int:
    """
    Convert time string to comparable minutes for overlap detection.
    
    Normalizes times to a consistent reference point for comparison.
    If reference_start_mins is provided, normalizes relative to that time.
    """
    hour, minute, is_next = _parse_time_with_next_day(time_str)
    mins = hour * 60 + minute
    
    # If has +1, add 1440 (next calendar day)
    if is_next:
        mins += 1440
    
    # Normalize relative to reference (if provided)
    if reference_start_mins > 0:
        # If this time is before reference, assume it's next day
        if mins < reference_start_mins:
            mins += 1440
    
    return mins


def _check_overlap_for_instances(
    db: Session,
    template_id: uuid_module.UUID,
    start_time: str,
    end_time: str,
    exclude_instance_id: uuid_module.UUID | None = None,
) -> None:
    """Check if the time range overlaps with existing instances in the template."""
    # Convert new block times to comparable minutes
    start_hour, start_minute, start_next = _parse_time_with_next_day(start_time)
    end_hour, end_minute, end_next = _parse_time_with_next_day(end_time)
    
    start_mins_base = start_hour * 60 + start_minute
    end_mins_base = end_hour * 60 + end_minute
    
    # Normalize to same reference day
    start_day_offset = 1440 if start_next else 0
    end_day_offset = 1440 if end_next else (1440 if end_mins_base < start_mins_base else 0)
    
    new_start_mins = start_mins_base - start_day_offset
    new_end_mins = end_mins_base + end_day_offset - start_day_offset

    # Get all instances for this template
    query = db.query(ScheduleTemplateBlockInstance).filter(
        ScheduleTemplateBlockInstance.template_id == template_id
    )
    if exclude_instance_id:
        query = query.filter(ScheduleTemplateBlockInstance.id != exclude_instance_id)
    existing_instances = query.all()

    for instance in existing_instances:
        # Parse existing instance times
        inst_start_hour, inst_start_minute, inst_start_next = _parse_time_with_next_day(instance.start_time)
        inst_end_hour, inst_end_minute, inst_end_next = _parse_time_with_next_day(instance.end_time)
        
        inst_start_mins_base = inst_start_hour * 60 + inst_start_minute
        inst_end_mins_base = inst_end_hour * 60 + inst_end_minute
        
        # Normalize to same reference day as new block
        inst_start_day_offset = 1440 if inst_start_next else 0
        inst_end_day_offset = 1440 if inst_end_next else (1440 if inst_end_mins_base < inst_start_mins_base else 0)
        
        inst_start_mins = inst_start_mins_base - inst_start_day_offset
        inst_end_mins = inst_end_mins_base + inst_end_day_offset - inst_start_day_offset
        
        # Adjust instance times to match new block's reference day
        # If new block's start is normalized, adjust instance times accordingly
        if start_day_offset > 0:
            inst_start_mins += 1440
            inst_end_mins += 1440
        
        # Now both are in same reference frame - check overlap
        # Overlap: (new_start < inst_end) AND (new_end > inst_start)
        # Instances that touch at boundaries are allowed (not overlapping)
        if new_start_mins < inst_end_mins and new_end_mins > inst_start_mins:
            raise ValueError("Block instance overlaps with existing block instance(s) in template.")

