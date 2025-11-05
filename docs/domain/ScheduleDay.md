_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md) • [Channel](Channel.md) • [ScheduleTemplate](ScheduleTemplate.md)_

# Domain — Schedule day

## Purpose

BroadcastScheduleDay represents the assignment of a ScheduleTemplate to a Channel for a specific broadcast date. This is planning-time logic that creates the link between programming structure (templates) and actual scheduling execution.

## Persistence model

BroadcastScheduleDay is managed by SQLAlchemy with the following fields:

- **id** (UUID, primary key): Unique identifier for relational joins and foreign key references
- **channel_id** (UUID, required, foreign key): Reference to Channel
- **template_id** (UUID, required, foreign key): Reference to ScheduleTemplate
- **schedule_date** (Text, required): Broadcast date in "YYYY-MM-DD" format
- **created_at** (DateTime(timezone=True), required): Record creation timestamp
- **updated_at** (DateTime(timezone=True), required): Record last modification timestamp

BroadcastScheduleDay has a unique constraint on (channel_id, schedule_date) ensuring only one template per channel per date.

### Table name

The table is named `broadcast_schedule_days` (plural). Schema migration is handled through Alembic. Postgres is the authoritative backing store.

### Constraints

- `schedule_date` must be in "YYYY-MM-DD" format
- Unique constraint on (channel_id, schedule_date) ensures only one template per channel per broadcast day
- Foreign key constraints ensure channel_id and template_id reference valid entities

## Contract / interface

BroadcastScheduleDay provides the assignment mechanism that links templates to channels for specific dates. It defines:

- Channel assignment (channel_id)
- Template assignment (template_id)
- Date assignment (schedule_date)
- Unique constraint ensuring one template per channel per date

Schedule assignments are the bridge between programming structure (templates) and execution (playout events).

## Execution model

ScheduleService consumes BroadcastScheduleDay records to determine which template to use for a given channel and date. This is the primary mechanism for:

1. Identifying the active template for schedule generation
2. Retrieving template blocks for content selection
3. Applying template rules to generate playout schedules
4. Creating BroadcastPlaylogEvent entries for scheduled content

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
- [Channel](Channel.md) - Channel configuration and timing policy
- [Playlog event](PlaylogEvent.md) - Generated playout events
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
