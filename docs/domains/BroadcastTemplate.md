# Domain — BroadcastTemplate

## Purpose

BroadcastTemplate represents a reusable daypart programming template that defines the structure and content rules for a broadcast day. Templates are the building blocks of automated scheduling, allowing operators to create consistent programming patterns that can be applied across multiple channels and dates.

BroadcastTemplate enables:

- Reusable programming patterns (e.g., "All Sitcoms 24x7", "Morning News Block")
- Consistent content selection rules across time periods
- Template-based scheduling that reduces manual programming effort
- Standardized daypart structures for different programming types

The canonical name is BroadcastTemplate throughout code, documentation, and database schema.

## Persistence model and fields

BroadcastTemplate is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Unique identifier for relational joins and foreign key references
- **name** (Text, required, unique): Human-facing template identifier used in UI and operator tooling
- **description** (Text, optional): Human-readable description of template purpose and content
- **is_active** (Boolean, required): Whether template is available for scheduling
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

Schema migration is handled through Alembic. Postgres is the authoritative backing store.

BroadcastTemplate has a one-to-many relationship with BroadcastTemplateBlock, which defines the time blocks and content rules within the template.

## Scheduling and interaction rules

ScheduleService consumes BroadcastTemplate records through BroadcastScheduleDay assignments. Templates provide the programming structure that ScheduleService uses to generate playout schedules.

Templates define the "what" of programming through their associated BroadcastTemplateBlock entries, which contain content selection rules. ScheduleService applies these rules to select appropriate content from the CatalogAsset catalog.

Templates are assigned to channels for specific broadcast dates through BroadcastScheduleDay, creating the link between programming structure and actual scheduling.

## Runtime relationship

BroadcastTemplate operates through the scheduling pipeline:

**ScheduleService** reads template assignments from BroadcastScheduleDay and applies template rules to generate playout schedules. It uses template blocks to determine content selection criteria and timing.

**ProgramDirector** coordinates multiple channels and may reference template assignments for cross-channel programming decisions.

**ChannelManager** executes the generated schedules but does not directly interact with templates - it receives playout instructions from ScheduleService.

Runtime hierarchy:
BroadcastTemplate (persistent) → BroadcastScheduleDay → ScheduleService → ChannelManager → Producer

## Operator workflows

**Create Template**: Define template name, description, and active status. Templates are containers for blocks.

**Manage Template Blocks**: Add, modify, or remove BroadcastTemplateBlock entries that define time periods and content rules.

**Assign Templates**: Use BroadcastScheduleDay to assign templates to channels for specific broadcast dates.

**Template Maintenance**: Update template descriptions, activate/deactivate templates, and manage template lifecycle.

**Template Reuse**: Apply the same template across multiple channels or dates for consistent programming patterns.

## Naming and consistency rules

The canonical name for this concept in code and documentation is BroadcastTemplate.

Templates are programming structure definitions, not runtime components. They define "what to play when" but do not execute playout.

All scheduling logic, operator tooling, and documentation MUST refer to BroadcastTemplate as the persisted template definition.

Templates lay out blocks (kids block, sitcom block, movie block, etc.) that define programming structure and content selection rules for automated scheduling.
