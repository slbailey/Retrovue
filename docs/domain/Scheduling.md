_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md)_

# Domain — Scheduling

## Purpose

The scheduling system assigns CatalogAssets (or rules to select them) into time slots for future air. This is planning-time logic that runs ahead of real time and builds out both the EPG horizon (coarse view) and the Playlog horizon (fine-grained view).

## Core model / scope

The Broadcast Scheduling Domain defines the core data models that enable RetroVue's scheduling and playout systems. This domain contains the persistent entities that ScheduleService, ProgramDirector, and ChannelManager depend upon for generating and executing broadcast schedules.

The Broadcast Scheduling Domain consists of six primary models that work together to define the complete scheduling infrastructure:

- **BroadcastChannel** - Channel configuration and timing policy
- **BroadcastTemplate** - Reusable daypart programming templates
- **BroadcastTemplateBlock** - Time blocks within templates with content selection rules
- **BroadcastScheduleDay** - Template assignments to channels for specific dates
- **CatalogAsset** - Broadcast-approved catalog entries (airable content)
- **BroadcastPlaylogEvent** - Generated playout events (what was actually played)

## Contract / interface

These entities work together in a specific flow:

**Channel → Template → ScheduleDay → PlaylogEvent**

1. **BroadcastChannel** defines the channel identity and timing configuration
2. **BroadcastTemplate** and **BroadcastTemplateBlock** define programming structure and content selection rules
3. **BroadcastScheduleDay** binds templates to channels for specific broadcast dates
4. **CatalogAsset** provides the approved content available for scheduling
5. **BroadcastPlaylogEvent** represents the generated playout schedule that ChannelManager executes

## Execution model

ScheduleService is the primary consumer of the Broadcast Scheduling Domain models. It:

- Reads BroadcastScheduleDay to determine active templates
- Retrieves BroadcastTemplateBlock entries for content selection rules
- Queries CatalogAsset for eligible content (canonical=true)
- Generates BroadcastPlaylogEvent records as scheduling output
- Uses BroadcastChannel configuration for timing and grid alignment

ProgramDirector coordinates multiple channels and may reference:

- BroadcastChannel records for channel configuration
- BroadcastScheduleDay assignments for cross-channel programming
- BroadcastTemplateBlock rules for content conflict resolution
- CatalogAsset records for content availability and approval status

ChannelManager executes playout but does not modify any Broadcast Scheduling Domain models. It:

- Reads BroadcastPlaylogEvent records for playout instructions
- References BroadcastChannel configuration for channel identity
- Uses CatalogAsset file paths for content playback

## Failure / fallback behavior

Scheduling runs ahead of real time and builds out both the EPG horizon (coarse view) and the Playlog horizon (fine-grained view). If scheduling fails, the system falls back to the most recent successful schedule or default programming.

## Naming rules

The canonical name for this concept in code and documentation is "Scheduling" or "Broadcast Scheduling Domain".

Scheduling is planning-time logic, not runtime logic. It defines "what to play when" but does not execute playout.

All scheduling logic, operator tooling, and documentation MUST refer to the Broadcast Scheduling Domain as the complete data foundation for automated broadcast programming.

## See also

- [Schedule day](ScheduleDay.md) - Template assignments to channels
- [Playlog event](PlaylogEvent.md) - Generated playout events
- [Playout pipeline](PlayoutPipeline.md) - Live stream generation
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
