_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md)_

# Domain — Schedule template block

## Purpose

BroadcastTemplateBlock represents a single slot inside a schedule template. It can point to a series, a movie block, a themed block ("Action Hour"), or another rule. This is planning-time logic that defines when content should be played and what rules should be used to select that content.

## Core model / scope

BroadcastTemplateBlock enables:

- Time-based programming structure (e.g., "6:00 AM - 12:00 PM: Morning News")
- Content selection rules for each time period
- Flexible programming patterns within templates
- Rule-based content matching from the catalog

## Contract / interface

BroadcastTemplateBlock is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Unique identifier for relational joins and foreign key references
- **template_id** (Integer, required, foreign key): Reference to parent BroadcastTemplate
- **start_time** (Text, required): Block start time in "HH:MM" format (local wallclock time)
- **end_time** (Text, required): Block end time in "HH:MM" format (local wallclock time)
- **rule_json** (Text, required): JSON configuration defining content selection rules
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

BroadcastTemplateBlock has a many-to-one relationship with BroadcastTemplate. Multiple blocks can exist within a single template to define complex programming patterns.

## Execution model

ScheduleService consumes BroadcastTemplateBlock records to determine content selection rules for specific time periods. When generating schedules, ScheduleService:

1. Identifies the active template for a channel and date via BroadcastScheduleDay
2. Retrieves all blocks for that template
3. Determines which block applies to the current time period
4. Applies the block's rule_json to select appropriate content from Asset
5. Generates BroadcastPlaylogEvent entries for the selected content

Template blocks provide the "how to select content" logic that drives automated scheduling decisions.

## Failure / fallback behavior

If template blocks are missing or invalid, the system falls back to default programming or the most recent valid block configuration.

## Naming rules

The canonical name for this concept in code and documentation is BroadcastTemplateBlock.

Template blocks are content selection rules, not runtime components. They define "how to choose content" but do not execute content selection.

## Operator workflows

**Create Template Block**: Define start/end times and content selection rules within a template.

**Configure Content Rules**: Set up rule_json to define how content should be selected (tags, duration, episode policies, etc.).

**Manage Block Timing**: Adjust start_time and end_time to modify programming periods within templates.

**Test Content Selection**: Verify that blocks correctly select appropriate content from the catalog.

**Template Block Maintenance**: Update rules, modify timing, or remove blocks as programming needs change.

## See also

- [Scheduling](Scheduling.md) - High-level scheduling system
- [Schedule template](ScheduleTemplate.md) - Reusable programming templates
- [Schedule day](ScheduleDay.md) - Template assignments
- [Asset](Asset.md) - Approved content
- [Playlog event](PlaylogEvent.md) - Generated playout events
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
