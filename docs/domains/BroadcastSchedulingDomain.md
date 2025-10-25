# Broadcast Scheduling Domain

## Domain — Broadcast scheduling flow

The Broadcast Scheduling Domain defines the core data models that enable RetroVue's scheduling and playout systems. This domain contains the persistent entities that ScheduleService, ProgramDirector, and ChannelManager depend upon for generating and executing broadcast schedules.

### Identity model

Scheduling, catalog, and playout all follow the **id** (INTEGER PK) + **uuid** (stable external identity) pattern. Shared **uuid** across ingest assets and catalog_asset is how we trace lineage and generate compliance/as-run reports.

## Domain Overview

The Broadcast Scheduling Domain consists of six primary models that work together to define the complete scheduling infrastructure:

- **BroadcastChannel** - Channel configuration and timing policy
- **BroadcastTemplate** - Reusable daypart programming templates
- **BroadcastTemplateBlock** - Time blocks within templates with content selection rules
- **BroadcastScheduleDay** - Template assignments to channels for specific dates
- **CatalogAsset** - Broadcast-approved catalog entries (airable content)
- **BroadcastPlaylogEvent** - Generated playout events (what was actually played)

## Entity Relationships

These entities work together in a specific flow:

**Channel → Template → ScheduleDay → PlaylogEvent**

1. **BroadcastChannel** defines the channel identity and timing configuration
2. **BroadcastTemplate** and **BroadcastTemplateBlock** define programming structure and content selection rules
3. **BroadcastScheduleDay** binds templates to channels for specific broadcast dates
4. **CatalogAsset** provides the approved content available for scheduling
5. **BroadcastPlaylogEvent** represents the generated playout schedule that ChannelManager executes

## Individual Entity Documentation

For detailed information about each entity, see the individual documentation files:

- [BroadcastChannel.md](BroadcastChannel.md) - Channel configuration and timing policy
- [BroadcastTemplate.md](BroadcastTemplate.md) - Reusable daypart programming templates
- [BroadcastTemplateBlock.md](BroadcastTemplateBlock.md) - Time blocks within templates with content selection rules
- [BroadcastScheduleDay.md](BroadcastScheduleDay.md) - Template assignments to channels for specific dates
- [CatalogAsset.md](CatalogAsset.md) - Broadcast-approved catalog entries (airable content)
- [BroadcastPlaylogEvent.md](BroadcastPlaylogEvent.md) - Generated playout events (what was actually played)

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
