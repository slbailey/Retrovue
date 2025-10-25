# Domain — BroadcastTemplateBlock

## Purpose

BroadcastTemplateBlock represents a time block within a BroadcastTemplate that defines when content should be played and what rules should be used to select that content. Blocks are the core mechanism for automated content selection and scheduling.

BroadcastTemplateBlock enables:

- Time-based programming structure (e.g., "6:00 AM - 12:00 PM: Morning News")
- Content selection rules for each time period
- Flexible programming patterns within templates
- Rule-based content matching from the catalog

The canonical name is BroadcastTemplateBlock throughout code, documentation, and database schema.

## Persistence model and fields

BroadcastTemplateBlock is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Unique identifier for relational joins and foreign key references
- **template_id** (Integer, required, foreign key): Reference to parent BroadcastTemplate
- **start_time** (Text, required): Block start time in "HH:MM" format (local wallclock time)
- **end_time** (Text, required): Block end time in "HH:MM" format (local wallclock time)
- **rule_json** (Text, required): JSON configuration defining content selection rules
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

Schema migration is handled through Alembic. Postgres is the authoritative backing store.

BroadcastTemplateBlock has a many-to-one relationship with BroadcastTemplate. Multiple blocks can exist within a single template to define complex programming patterns.

## Scheduling and interaction rules

ScheduleService consumes BroadcastTemplateBlock records to determine content selection rules for specific time periods. When generating schedules, ScheduleService:

1. Identifies the active template for a channel and date via BroadcastScheduleDay
2. Retrieves all blocks for that template
3. Determines which block applies to the current time period
4. Applies the block's rule_json to select appropriate content from CatalogAsset
5. Generates BroadcastPlaylogEvent entries for the selected content

Template blocks provide the "how to select content" logic that drives automated scheduling decisions.

## Runtime relationship

BroadcastTemplateBlock operates through the content selection pipeline:

**ScheduleService** reads template blocks and applies their rules to select content from the catalog. It uses the rule_json to match content tags, duration constraints, and other criteria.

**ProgramDirector** may reference template blocks for cross-channel programming coordination and content conflict resolution.

**ChannelManager** receives the final playout schedule but does not directly interact with template blocks - it executes the generated BroadcastPlaylogEvent entries.

Runtime hierarchy:
BroadcastTemplateBlock (persistent) → ScheduleService (content selection) → BroadcastPlaylogEvent (generated) → ChannelManager (execution)

## Operator workflows

**Create Template Block**: Define start/end times and content selection rules within a template.

**Configure Content Rules**: Set up rule_json to define how content should be selected (tags, duration, episode policies, etc.).

**Manage Block Timing**: Adjust start_time and end_time to modify programming periods within templates.

**Test Content Selection**: Verify that blocks correctly select appropriate content from the catalog.

**Template Block Maintenance**: Update rules, modify timing, or remove blocks as programming needs change.

## Naming and consistency rules

The canonical name for this concept in code and documentation is BroadcastTemplateBlock.

Template blocks are content selection rules, not runtime components. They define "how to choose content" but do not execute content selection.

All scheduling logic, operator tooling, and documentation MUST refer to BroadcastTemplateBlock as the persisted block definition.

Template blocks define programming periods (kids block, sitcom block, movie block, etc.) with specific content selection rules that ScheduleService uses to automatically choose appropriate content from the catalog.
