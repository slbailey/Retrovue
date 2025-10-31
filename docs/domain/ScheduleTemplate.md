_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md)_

# Domain — Schedule template

## Purpose

BroadcastTemplate represents a reusable daypart programming template that defines the structure and content rules for a broadcast day. This is planning-time logic that enables consistent programming patterns that can be applied across multiple channels and dates.

## Core model / scope

BroadcastTemplate enables:

- Reusable programming patterns (e.g., "All Sitcoms 24x7", "Morning News Block")
- Consistent content selection rules across time periods
- Template-based scheduling that reduces manual programming effort
- Standardized daypart structures for different programming types

## Contract / interface

BroadcastTemplate is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Unique identifier for relational joins and foreign key references
- **name** (Text, required, unique): Human-facing template identifier used in UI and operator tooling
- **description** (Text, optional): Human-readable description of template purpose and content
- **is_active** (Boolean, required): Whether template is available for scheduling
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

BroadcastTemplate has a one-to-many relationship with BroadcastTemplateBlock, which defines the time blocks and content rules within the template.

## Execution model

ScheduleService consumes BroadcastTemplate records through BroadcastScheduleDay assignments. Templates provide the programming structure that ScheduleService uses to generate playout schedules.

Templates define the "what" of programming through their associated BroadcastTemplateBlock entries, which contain content selection rules. ScheduleService applies these rules to select appropriate content from the Asset catalog.

Templates are assigned to channels for specific broadcast dates through BroadcastScheduleDay, creating the link between programming structure and actual scheduling.

## Failure / fallback behavior

If templates are missing or invalid, the system falls back to default programming or the most recent valid template.

## Naming rules

The canonical name for this concept in code and documentation is BroadcastTemplate.

Templates are programming structure definitions, not runtime components. They define "what to play when" but do not execute playout.

## Operator workflows

**Create Template**: Define template name, description, and active status. Templates are containers for blocks.

**Manage Template Blocks**: Add, modify, or remove BroadcastTemplateBlock entries that define time periods and content rules.

**Assign Templates**: Use BroadcastScheduleDay to assign templates to channels for specific broadcast dates.

**Template Maintenance**: Update template descriptions, activate/deactivate templates, and manage template lifecycle.

**Template Reuse**: Apply the same template across multiple channels or dates for consistent programming patterns.

## See also

- [Scheduling](Scheduling.md) - High-level scheduling system
- [Schedule day](ScheduleDay.md) - Template assignments
- [Schedule template block](ScheduleTemplateBlock.md) - Time blocks within templates
- [Playlog event](PlaylogEvent.md) - Generated playout events
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
