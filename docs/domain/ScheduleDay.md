_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md)_

# Domain — Schedule day

## Purpose

BroadcastScheduleDay represents the assignment of a BroadcastTemplate to a Channel for a specific broadcast date. This is planning-time logic that creates the link between programming structure (templates) and actual scheduling execution.

## Core model / scope

BroadcastScheduleDay enables:

- Template-to-channel assignments for specific dates
- Flexible programming that can vary by date
- Multi-channel programming with different templates per channel
- Date-specific programming overrides

## Contract / interface

BroadcastScheduleDay is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Unique identifier for relational joins and foreign key references
- **channel_id** (Integer, required, foreign key): Reference to Channel
- **template_id** (Integer, required, foreign key): Reference to BroadcastTemplate
- **schedule_date** (Text, required): Broadcast date in "YYYY-MM-DD" format
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

BroadcastScheduleDay has a unique constraint on (channel_id, schedule_date) ensuring only one template per channel per date.

## Execution model

ScheduleService consumes BroadcastScheduleDay records to determine which template to use for a given channel and date. This is the primary mechanism for:

1. Identifying the active template for schedule generation
2. Retrieving template blocks for content selection
3. Applying template rules to generate playout schedules
4. Creating BroadcastPlaylogEvent entries for scheduled content

Schedule assignments are the bridge between programming structure (templates) and execution (playout events).

## Failure / fallback behavior

If schedule assignments are missing or invalid, the system falls back to default programming or the most recent valid schedule.

## Naming rules

The canonical name for this concept in code and documentation is BroadcastScheduleDay.

Schedule assignments are programming decisions, not runtime components. They define "what template to use when" but do not execute scheduling.

## Operator workflows

**Assign Template to Channel**: Link a template to a channel for a specific broadcast date.

**Manage Schedule Assignments**: Create, modify, or remove template assignments as programming needs change.

**Multi-Channel Programming**: Assign different templates to different channels for the same date.

**Programming Overrides**: Assign special templates for holidays, special events, or programming changes.

**Schedule Planning**: Plan template assignments in advance for consistent programming patterns.

## See also

- [Scheduling](Scheduling.md) - High-level scheduling system
- [Schedule template](ScheduleTemplate.md) - Reusable programming templates
- [Playlog event](PlaylogEvent.md) - Generated playout events
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
