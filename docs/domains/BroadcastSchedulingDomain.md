# Broadcast Scheduling Domain

The Broadcast Scheduling Domain defines the core data models that enable RetroVue's scheduling and playout systems. This domain contains the persistent entities that ScheduleService, ProgramDirector, and ChannelManager depend upon for generating and executing broadcast schedules.

## Domain Overview

The Broadcast Scheduling Domain consists of six primary models:

- **BroadcastChannel** - Channel configuration and timing policy
- **BroadcastTemplate** - Reusable daypart programming templates
- **BroadcastTemplateBlock** - Time blocks within templates with content selection rules
- **BroadcastScheduleDay** - Template assignments to channels for specific dates
- **CatalogAsset** - Broadcast-approved catalog entries (airable content)
- **BroadcastPlaylogEvent** - Generated playout events (what was actually played)

These models work together to define the complete scheduling infrastructure that enables automated broadcast programming.

---

## Domain — BroadcastChannel

### Purpose

BroadcastChannel represents a persistent broadcast entity in the RetroVue system. It defines channel identity, configuration, and operational parameters for channels such as "RetroToons" or "MidnightMovies".

BroadcastChannel is stored in Postgres using SQLAlchemy. It is configuration and identity, not a runtime encoder instance. Operators reference BroadcastChannel when scheduling content, managing programming, and monitoring on-air status.

BroadcastChannel defines:

- Channel identity and human-facing name
- IANA timezone for all scheduling logic
- Broadcast day rollover rules (e.g., 6:00 AM for overnight blocks)
- Clock/grid alignment for scheduling
- Active status for on-air availability

The canonical name is BroadcastChannel throughout code, documentation, and database schema.

### Persistence model and fields

BroadcastChannel is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Unique identifier
- **name** (Text, required, unique): Human-facing channel label used in UI and operator tooling
- **timezone** (Text, required): IANA timezone string for all schedule generation and "what's on now" logic
- **grid_size_minutes** (Integer, required): Base grid slot size for scheduling (e.g., 30-minute blocks)
- **grid_offset_minutes** (Integer, required): Grid alignment offset for clean schedule snapping
- **rollover_minutes** (Integer, required): Broadcast day rollover time relative to local midnight (e.g., 360 = 6:00 AM)
- **is_active** (Boolean, required): Whether channel is on-air and available for scheduling
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

Schema migration is handled through Alembic. Postgres is the authoritative backing store.

BroadcastChannel has relationships with schedule data through BroadcastScheduleDay, which links channels to templates for specific broadcast dates.

### Relationship to scheduling

ScheduleService consumes BroadcastChannel records to determine current programming. It generates schedule data using the channel's grid_size_minutes, grid_offset_minutes, and rollover_minutes for accurate block-based scheduling.

The timezone field defines how "local time" is interpreted for that channel's day, including overnight rollover. ScheduleService is authoritative for what to play. BroadcastChannel provides the identity and context.

### Runtime relationship

BroadcastChannel becomes an active stream through runtime components:

**ChannelManager** is the per-channel runtime orchestrator responsible for putting the channel on-air. It asks ScheduleService what to play but does not generate schedules or make programming decisions.

**Producer** (NormalProducer, EmergencyProducer, GuideProducer) is the output generator that produces continuous MPEG-TS transport stream to stdout. It plays content as instructed without content selection.

**Fan-out**: ChannelManager distributes the stdout stream from the active Producer to multiple viewers/clients using the IPTV one-producer-many-consumers model.

**ChannelRuntimeState** is an in-memory snapshot maintained by ChannelManager. It tracks viewer count, current mode, Producer status, and health for operator dashboards.

Runtime hierarchy:
BroadcastChannel (persistent, Postgres) → ScheduleService → ChannelManager → Producer → viewers

BroadcastChannel is persisted configuration. ChannelManager, Producer, and ChannelRuntimeState are runtime/ephemeral.

### Operator workflows

**Create BroadcastChannel**: Define name, timezone, grid rules, and rollover_minutes. Set active status.

**Activate/deactivate**: Toggle is_active to control on-air availability for scheduling and playout.

**Adjust scheduling**: Modify grid size/offset/rollover to change schedule block alignment and day cutover behavior.

**Inspect status**: Check is_active for operational status. Monitor ChannelRuntimeState for live status (streaming, viewers, mode).

**Retire channel**: Set is_active false to remove from routing and scheduling.

Future operator tooling will include maintenance CLI/admin UI for BroadcastChannel records and Channel Dashboard UI for ChannelRuntimeState display.

### Naming and consistency rules

The canonical name for this concept in code and documentation is BroadcastChannel.

We do NOT maintain a separate "Channel" model alongside BroadcastChannel. There is no parallel "ChannelConfig" entity unless one is explicitly introduced later.

All scheduling logic, runtime orchestration, and operator tooling MUST refer to BroadcastChannel as the persisted channel definition.

ChannelManager, Producer, and ChannelRuntimeState are runtime components that operate on a BroadcastChannel. They are not alternate channel definitions.

---

## Domain — BroadcastTemplate

### Purpose

BroadcastTemplate represents a reusable daypart programming template that defines the structure and content rules for a broadcast day. Templates are the building blocks of automated scheduling, allowing operators to create consistent programming patterns that can be applied across multiple channels and dates.

BroadcastTemplate enables:

- Reusable programming patterns (e.g., "All Sitcoms 24x7", "Morning News Block")
- Consistent content selection rules across time periods
- Template-based scheduling that reduces manual programming effort
- Standardized daypart structures for different programming types

The canonical name is BroadcastTemplate throughout code, documentation, and database schema.

### Persistence model and fields

BroadcastTemplate is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Unique identifier
- **name** (Text, required, unique): Human-facing template identifier used in UI and operator tooling
- **description** (Text, optional): Human-readable description of template purpose and content
- **is_active** (Boolean, required): Whether template is available for scheduling
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

Schema migration is handled through Alembic. Postgres is the authoritative backing store.

BroadcastTemplate has a one-to-many relationship with BroadcastTemplateBlock, which defines the time blocks and content rules within the template.

### Relationship to scheduling

ScheduleService consumes BroadcastTemplate records through BroadcastScheduleDay assignments. Templates provide the programming structure that ScheduleService uses to generate playout schedules.

Templates define the "what" of programming through their associated BroadcastTemplateBlock entries, which contain content selection rules. ScheduleService applies these rules to select appropriate content from the CatalogAsset catalog.

Templates are assigned to channels for specific broadcast dates through BroadcastScheduleDay, creating the link between programming structure and actual scheduling.

### Runtime relationship

BroadcastTemplate operates through the scheduling pipeline:

**ScheduleService** reads template assignments from BroadcastScheduleDay and applies template rules to generate playout schedules. It uses template blocks to determine content selection criteria and timing.

**ProgramDirector** coordinates multiple channels and may reference template assignments for cross-channel programming decisions.

**ChannelManager** executes the generated schedules but does not directly interact with templates - it receives playout instructions from ScheduleService.

Runtime hierarchy:
BroadcastTemplate (persistent) → BroadcastScheduleDay → ScheduleService → ChannelManager → Producer

### Operator workflows

**Create Template**: Define template name, description, and active status. Templates are containers for blocks.

**Manage Template Blocks**: Add, modify, or remove BroadcastTemplateBlock entries that define time periods and content rules.

**Assign Templates**: Use BroadcastScheduleDay to assign templates to channels for specific broadcast dates.

**Template Maintenance**: Update template descriptions, activate/deactivate templates, and manage template lifecycle.

**Template Reuse**: Apply the same template across multiple channels or dates for consistent programming patterns.

### Naming and consistency rules

The canonical name for this concept in code and documentation is BroadcastTemplate.

Templates are programming structure definitions, not runtime components. They define "what to play when" but do not execute playout.

All scheduling logic, operator tooling, and documentation MUST refer to BroadcastTemplate as the persisted template definition.

---

## Domain — BroadcastTemplateBlock

### Purpose

BroadcastTemplateBlock represents a time block within a BroadcastTemplate that defines when content should be played and what rules should be used to select that content. Blocks are the core mechanism for automated content selection and scheduling.

BroadcastTemplateBlock enables:

- Time-based programming structure (e.g., "6:00 AM - 12:00 PM: Morning News")
- Content selection rules for each time period
- Flexible programming patterns within templates
- Rule-based content matching from the catalog

The canonical name is BroadcastTemplateBlock throughout code, documentation, and database schema.

### Persistence model and fields

BroadcastTemplateBlock is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Unique identifier
- **template_id** (Integer, required, foreign key): Reference to parent BroadcastTemplate
- **start_time** (Text, required): Block start time in "HH:MM" format (local wallclock time)
- **end_time** (Text, required): Block end time in "HH:MM" format (local wallclock time)
- **rule_json** (Text, required): JSON configuration defining content selection rules
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

Schema migration is handled through Alembic. Postgres is the authoritative backing store.

BroadcastTemplateBlock has a many-to-one relationship with BroadcastTemplate. Multiple blocks can exist within a single template to define complex programming patterns.

### Relationship to scheduling

ScheduleService consumes BroadcastTemplateBlock records to determine content selection rules for specific time periods. When generating schedules, ScheduleService:

1. Identifies the active template for a channel and date via BroadcastScheduleDay
2. Retrieves all blocks for that template
3. Determines which block applies to the current time period
4. Applies the block's rule_json to select appropriate content from CatalogAsset
5. Generates BroadcastPlaylogEvent entries for the selected content

Template blocks provide the "how to select content" logic that drives automated scheduling decisions.

### Runtime relationship

BroadcastTemplateBlock operates through the content selection pipeline:

**ScheduleService** reads template blocks and applies their rules to select content from the catalog. It uses the rule_json to match content tags, duration constraints, and other criteria.

**ProgramDirector** may reference template blocks for cross-channel programming coordination and content conflict resolution.

**ChannelManager** receives the final playout schedule but does not directly interact with template blocks - it executes the generated BroadcastPlaylogEvent entries.

Runtime hierarchy:
BroadcastTemplateBlock (persistent) → ScheduleService (content selection) → BroadcastPlaylogEvent (generated) → ChannelManager (execution)

### Operator workflows

**Create Template Block**: Define start/end times and content selection rules within a template.

**Configure Content Rules**: Set up rule_json to define how content should be selected (tags, duration, episode policies, etc.).

**Manage Block Timing**: Adjust start_time and end_time to modify programming periods within templates.

**Test Content Selection**: Verify that blocks correctly select appropriate content from the catalog.

**Template Block Maintenance**: Update rules, modify timing, or remove blocks as programming needs change.

### Naming and consistency rules

The canonical name for this concept in code and documentation is BroadcastTemplateBlock.

Template blocks are content selection rules, not runtime components. They define "how to choose content" but do not execute content selection.

All scheduling logic, operator tooling, and documentation MUST refer to BroadcastTemplateBlock as the persisted block definition.

---

## Domain — BroadcastScheduleDay

### Purpose

BroadcastScheduleDay represents the assignment of a BroadcastTemplate to a BroadcastChannel for a specific broadcast date. This creates the link between programming structure (templates) and actual scheduling execution.

BroadcastScheduleDay enables:

- Template-to-channel assignments for specific dates
- Flexible programming that can vary by date
- Multi-channel programming with different templates per channel
- Date-specific programming overrides

The canonical name is BroadcastScheduleDay throughout code, documentation, and database schema.

### Persistence model and fields

BroadcastScheduleDay is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Unique identifier
- **channel_id** (Integer, required, foreign key): Reference to BroadcastChannel
- **template_id** (Integer, required, foreign key): Reference to BroadcastTemplate
- **schedule_date** (Text, required): Broadcast date in "YYYY-MM-DD" format
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

Schema migration is handled through Alembic. Postgres is the authoritative backing store.

BroadcastScheduleDay has a unique constraint on (channel_id, schedule_date) ensuring only one template per channel per date.

### Relationship to scheduling

ScheduleService consumes BroadcastScheduleDay records to determine which template to use for a given channel and date. This is the primary mechanism for:

1. Identifying the active template for schedule generation
2. Retrieving template blocks for content selection
3. Applying template rules to generate playout schedules
4. Creating BroadcastPlaylogEvent entries for scheduled content

Schedule assignments are the bridge between programming structure (templates) and execution (playout events).

### Runtime relationship

BroadcastScheduleDay operates through the scheduling pipeline:

**ScheduleService** reads schedule assignments to determine which template to use for schedule generation. It uses the template_id to retrieve BroadcastTemplateBlock entries and apply their rules.

**ProgramDirector** may reference schedule assignments for cross-channel coordination and programming conflict resolution.

**ChannelManager** receives the final playout schedule but does not directly interact with schedule assignments - it executes the generated BroadcastPlaylogEvent entries.

Runtime hierarchy:
BroadcastScheduleDay (persistent) → ScheduleService (template resolution) → BroadcastTemplateBlock (content selection) → BroadcastPlaylogEvent (generated) → ChannelManager (execution)

### Operator workflows

**Assign Template to Channel**: Link a template to a channel for a specific broadcast date.

**Manage Schedule Assignments**: Create, modify, or remove template assignments as programming needs change.

**Multi-Channel Programming**: Assign different templates to different channels for the same date.

**Programming Overrides**: Assign special templates for holidays, special events, or programming changes.

**Schedule Planning**: Plan template assignments in advance for consistent programming patterns.

### Naming and consistency rules

The canonical name for this concept in code and documentation is BroadcastScheduleDay.

Schedule assignments are programming decisions, not runtime components. They define "what template to use when" but do not execute scheduling.

All scheduling logic, operator tooling, and documentation MUST refer to BroadcastScheduleDay as the persisted schedule assignment definition.

---

## Domain — CatalogAsset

### Purpose

CatalogAsset represents a broadcast-approved catalog entry that is eligible for scheduling and playout. This is the "airable" content that ScheduleService can select and schedule for broadcast.

CatalogAsset enables:

- Broadcast-approved content catalog
- Content metadata for scheduling decisions
- Approval workflow between Library Domain and Broadcast Domain
- Content selection based on tags, duration, and other criteria

The canonical name is CatalogAsset throughout code, documentation, and database schema.

### Persistence model and fields

CatalogAsset is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Unique identifier
- **title** (Text, required): Human-readable asset title
- **duration_ms** (Integer, required): Asset duration in milliseconds
- **tags** (Text, optional): Comma-separated content tags for categorization
- **file_path** (Text, required): Local file system path to the asset
- **canonical** (Boolean, required): Approval status - only canonical assets are eligible for scheduling
- **source_ingest_asset_id** (Integer, optional): Reference to Library Domain asset for traceability
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

Schema migration is handled through Alembic. Postgres is the authoritative backing store.

CatalogAsset has indexes on canonical and tags fields for efficient content selection queries.

### Relationship to scheduling

ScheduleService consumes CatalogAsset records to select content for scheduling. Only assets with canonical=true are eligible for selection. ScheduleService uses:

- Tags to match content selection rules from BroadcastTemplateBlock
- Duration to fit content within time blocks
- File paths to generate playout instructions
- Approval status to ensure only approved content is scheduled

Catalog assets are the source of all scheduled content - no content can be scheduled that is not in the catalog with canonical=true.

### Runtime relationship

CatalogAsset operates through the content selection and playout pipeline:

**ScheduleService** reads catalog assets to select content based on template block rules. It uses tags, duration, and approval status to make selection decisions.

**ChannelManager** receives playout instructions that reference catalog asset file paths for content playback.

**Producer** plays the actual content files referenced by catalog assets.

Runtime hierarchy:
CatalogAsset (persistent) → ScheduleService (content selection) → BroadcastPlaylogEvent (generated) → ChannelManager (playout) → Producer (file playback)

### Operator workflows

**Approve Content**: Set canonical=true to make content eligible for scheduling.

**Manage Content Metadata**: Update titles, tags, and other metadata for better content organization.

**Content Promotion**: Promote content from Library Domain to Broadcast Domain catalog.

**Content Maintenance**: Update file paths, manage content lifecycle, and handle content changes.

**Content Discovery**: Search and filter catalog assets by tags, duration, and approval status.

### Naming and consistency rules

The canonical name for this concept in code and documentation is CatalogAsset.

Catalog assets are broadcast-approved content, not runtime components. They define "what content is available" but do not execute content playback.

All scheduling logic, operator tooling, and documentation MUST refer to CatalogAsset as the persisted catalog entry definition.

---

## Domain — BroadcastPlaylogEvent

### Purpose

BroadcastPlaylogEvent represents a generated playout event that records what content was actually scheduled to play at a specific time. These events are created by ScheduleService and consumed by ChannelManager for playout execution.

BroadcastPlaylogEvent enables:

- Generated playout schedules
- Content timing and sequencing
- Playout execution instructions
- Broadcast day tracking and rollover handling

The canonical name is BroadcastPlaylogEvent throughout code, documentation, and database schema.

### Persistence model and fields

BroadcastPlaylogEvent is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Unique identifier
- **channel_id** (Integer, required, foreign key): Reference to BroadcastChannel
- **asset_id** (Integer, required, foreign key): Reference to CatalogAsset
- **start_utc** (DateTime(timezone=True), required): Event start time in UTC
- **end_utc** (DateTime(timezone=True), required): Event end time in UTC
- **broadcast_day** (Text, required): Broadcast day label in "YYYY-MM-DD" format
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

Schema migration is handled through Alembic. Postgres is the authoritative backing store.

BroadcastPlaylogEvent has indexes on channel_id, start_utc, and broadcast_day for efficient playout queries.

### Relationship to scheduling

ScheduleService generates BroadcastPlaylogEvent records as the output of the scheduling process. These events represent the final playout schedule that will be executed by ChannelManager.

Playlog events are created by:

1. ScheduleService reading template assignments and blocks
2. Applying content selection rules to choose appropriate assets
3. Generating playout events with precise timing and sequencing
4. Creating BroadcastPlaylogEvent records for each scheduled content item

### Runtime relationship

BroadcastPlaylogEvent operates through the playout execution pipeline:

**ScheduleService** generates playlog events as the output of the scheduling process. It creates events with precise timing and content references.

**ChannelManager** reads playlog events to determine what content to play and when. It uses the events to coordinate playout execution.

**Producer** receives playout instructions from ChannelManager and plays the actual content files referenced by the events.

Runtime hierarchy:
BroadcastPlaylogEvent (persistent) → ChannelManager (playout coordination) → Producer (content playback)

### Operator workflows

**Monitor Playout**: View generated playlog events to see what content is scheduled to play.

**Playout Verification**: Verify that scheduled content matches programming intentions and timing.

**Content Timing**: Review start/end times to ensure proper content sequencing and timing.

**Broadcast Day Management**: Track content across broadcast day boundaries and rollover periods.

**Playout Troubleshooting**: Use playlog events to diagnose playout issues and content problems.

### Naming and consistency rules

The canonical name for this concept in code and documentation is BroadcastPlaylogEvent.

Playlog events are generated scheduling output, not runtime components. They define "what to play when" but do not execute playout.

All scheduling logic, operator tooling, and documentation MUST refer to BroadcastPlaylogEvent as the persisted playout event definition.

---

## Runtime Component Relationships

### ScheduleService Integration

ScheduleService is the primary consumer of the Broadcast Scheduling Domain models. It:

- Reads BroadcastScheduleDay to determine active templates
- Retrieves BroadcastTemplateBlock entries for content selection rules
- Queries CatalogAsset for eligible content (canonical=true)
- Generates BroadcastPlaylogEvent records as scheduling output
- Uses BroadcastChannel configuration for timing and grid alignment

### ProgramDirector Integration

ProgramDirector coordinates multiple channels and may reference:

- BroadcastChannel records for channel configuration
- BroadcastScheduleDay assignments for cross-channel programming
- BroadcastTemplateBlock rules for content conflict resolution
- CatalogAsset records for content availability and approval status

### ChannelManager Integration

ChannelManager executes playout but does not generate schedules. It:

- Reads BroadcastPlaylogEvent records for playout instructions
- References BroadcastChannel configuration for channel identity
- Uses CatalogAsset file paths for content playback
- Does not modify any Broadcast Scheduling Domain models

### Data Flow Summary

1. **Configuration**: BroadcastChannel, BroadcastTemplate, BroadcastTemplateBlock define programming structure
2. **Assignment**: BroadcastScheduleDay links templates to channels for specific dates
3. **Content**: CatalogAsset provides approved content for scheduling
4. **Generation**: ScheduleService creates BroadcastPlaylogEvent records
5. **Execution**: ChannelManager executes playlog events for playout

The Broadcast Scheduling Domain provides the complete data foundation for automated broadcast programming, from initial configuration through final playout execution.
