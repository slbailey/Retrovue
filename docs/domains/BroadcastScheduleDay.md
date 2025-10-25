# Domain — BroadcastScheduleDay

## Purpose

BroadcastScheduleDay represents the assignment of a BroadcastTemplate to a BroadcastChannel for a specific broadcast date. This creates the link between programming structure (templates) and actual scheduling execution.

BroadcastScheduleDay enables:

- Template-to-channel assignments for specific dates
- Flexible programming that can vary by date
- Multi-channel programming with different templates per channel
- Date-specific programming overrides

The canonical name is BroadcastScheduleDay throughout code, documentation, and database schema.

## Persistence model and fields

BroadcastScheduleDay is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Unique identifier for relational joins and foreign key references
- **channel_id** (Integer, required, foreign key): Reference to BroadcastChannel
- **template_id** (Integer, required, foreign key): Reference to BroadcastTemplate
- **schedule_date** (Text, required): Broadcast date in "YYYY-MM-DD" format
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

Schema migration is handled through Alembic. Postgres is the authoritative backing store.

BroadcastScheduleDay has a unique constraint on (channel_id, schedule_date) ensuring only one template per channel per date.

## Scheduling and interaction rules

ScheduleService consumes BroadcastScheduleDay records to determine which template to use for a given channel and date. This is the primary mechanism for:

1. Identifying the active template for schedule generation
2. Retrieving template blocks for content selection
3. Applying template rules to generate playout schedules
4. Creating BroadcastPlaylogEvent entries for scheduled content

Schedule assignments are the bridge between programming structure (templates) and execution (playout events).

## Runtime relationship

BroadcastScheduleDay operates through the scheduling pipeline:

**ScheduleService** reads schedule assignments to determine which template to use for schedule generation. It uses the template_id to retrieve BroadcastTemplateBlock entries and apply their rules.

**ProgramDirector** may reference schedule assignments for cross-channel coordination and programming conflict resolution.

**ChannelManager** receives the final playout schedule but does not directly interact with schedule assignments - it executes the generated BroadcastPlaylogEvent entries.

Runtime hierarchy:
BroadcastScheduleDay (persistent) → ScheduleService (template resolution) → BroadcastTemplateBlock (content selection) → BroadcastPlaylogEvent (generated) → ChannelManager (execution)

## Operator workflows

**Assign Template to Channel**: Link a template to a channel for a specific broadcast date.

**Manage Schedule Assignments**: Create, modify, or remove template assignments as programming needs change.

**Multi-Channel Programming**: Assign different templates to different channels for the same date.

**Programming Overrides**: Assign special templates for holidays, special events, or programming changes.

**Schedule Planning**: Plan template assignments in advance for consistent programming patterns.

## Naming and consistency rules

The canonical name for this concept in code and documentation is BroadcastScheduleDay.

Schedule assignments are programming decisions, not runtime components. They define "what template to use when" but do not execute scheduling.

All scheduling logic, operator tooling, and documentation MUST refer to BroadcastScheduleDay as the persisted schedule assignment definition.

BroadcastScheduleDay binds a template to a specific channel on a specific broadcast date. This feeds ScheduleService to generate the Playlog horizon.
