_Related: [Scheduling system architecture](../architecture/SchedulingSystem.md) • [Architecture overview](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md)_

# Domain — Scheduling

## Purpose

The scheduling system assigns assets (or rules to select them) into time slots for future air. This is planning-time logic that runs ahead of real time and builds out both the EPG horizon (coarse view) and the Playlog horizon (fine-grained view).

**Critical Rule:** The scheduler and playlog builder may only consider assets where `state == 'ready'` and `approved_for_broadcast == true`.

## Core model / scope

The Broadcast Scheduling Domain defines the core data models that enable RetroVue's scheduling and playout systems. This domain contains the persistent entities that ScheduleService, ProgramDirector, and ChannelManager depend upon for generating and executing broadcast schedules.

The Broadcast Scheduling Domain consists of six primary models that work together to define the complete scheduling infrastructure:

- **Channel** - Channel configuration and timing policy
- **ScheduleTemplate** - Reusable daypart programming templates
- **ScheduleTemplateBlock** - Time blocks within templates with content selection rules
- **BroadcastScheduleDay** - Template assignments to channels for specific dates
- **Asset** - Broadcast-approved content (airable content)
- **BroadcastPlaylogEvent** - Generated playout events (what was actually played)

## Contract / interface

These entities work together in a specific flow:

**Channel → Template → ScheduleDay → PlaylogEvent**

1. **Channel** defines the channel identity and timing configuration
2. **ScheduleTemplate** and **ScheduleTemplateBlock** define programming structure and content selection rules
3. **BroadcastScheduleDay** binds templates to channels for specific broadcast dates
4. **Asset** provides the approved content available for scheduling (must be in `ready` state)
5. **BroadcastPlaylogEvent** represents the generated playout schedule that ChannelManager executes

## Execution model

ScheduleService is the primary consumer of the Broadcast Scheduling Domain models. It:

- Reads BroadcastScheduleDay to determine active templates
- Retrieves ScheduleTemplateBlock entries for content selection rules
- Queries Asset for eligible content (`state='ready'` and `approved_for_broadcast=true`)
- Generates BroadcastPlaylogEvent records as scheduling output
- Uses Channel configuration for timing and grid alignment

**Critical Rules:**

- **Scheduler never touches assets in `new` or `enriching` state**
- **Only assets with `state='ready'` and `approved_for_broadcast=true` are eligible for scheduling**

ProgramDirector coordinates multiple channels and may reference:

- Channel records for channel configuration
- BroadcastScheduleDay assignments for cross-channel programming
- ScheduleTemplateBlock rules for content conflict resolution
- Asset records for content availability and approval status

ChannelManager executes playout but does not modify any Broadcast Scheduling Domain models. It:

- Reads BroadcastPlaylogEvent records for playout instructions
- References Channel configuration for channel identity
- Uses Asset file paths for content playback

**Critical Rule:**

- **Runtime never spins up playout for an asset unless it's in `ready` state**

## Failure / fallback behavior

Scheduling runs ahead of real time and builds out both the EPG horizon (coarse view) and the Playlog horizon (fine-grained view). If scheduling fails, the system falls back to the most recent successful schedule or default programming.

## Naming rules

The canonical name for this concept in code and documentation is "Scheduling" or "Broadcast Scheduling Domain".

Scheduling is planning-time logic, not runtime logic. It defines "what to play when" but does not execute playout.

All scheduling logic, operator tooling, and documentation MUST refer to the Broadcast Scheduling Domain as the complete data foundation for automated broadcast programming.

## See also

- [Scheduling system architecture](../architecture/SchedulingSystem.md) - Comprehensive scheduling system architecture
- [Scheduling roadmap](../architecture/SchedulingRoadmap.md) - Implementation roadmap
- [Schedule day](ScheduleDay.md) - Template assignments to channels
- [Playlog event](PlaylogEvent.md) - Generated playout events
- [Playout pipeline](PlayoutPipeline.md) - Live stream generation
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
