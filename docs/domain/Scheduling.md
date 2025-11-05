_Related: [Scheduling system architecture](../architecture/SchedulingSystem.md) • [Architecture overview](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md)_

# Domain — Scheduling

## Purpose

The scheduling system assigns assets (or rules to select them) into time slots for future air. This is planning-time logic that runs ahead of real time and builds out both the EPG horizon (coarse view) and the Playlog horizon (fine-grained view).

**Critical Rule:** The scheduler and playlog builder may only consider assets where `state == 'ready'` and `approved_for_broadcast == true`.

## Core model / scope

The Broadcast Scheduling Domain defines the core data models that enable RetroVue's scheduling and playout systems. This domain contains the persistent entities that ScheduleService, ProgramDirector, and ChannelManager depend upon for generating and executing broadcast schedules.

The Broadcast Scheduling Domain consists of seven primary models that work together to define the complete scheduling infrastructure:

- **Channel** - Channel configuration and timing policy
- **ScheduleTemplate** - Reusable, channel-agnostic shells that define what *types* of content should appear
- **ScheduleTemplateBlock** - Standalone, reusable blocks with content type constraints (guardrails)
- **ScheduleTemplateBlockInstance** - Junction table linking templates to blocks with template-specific timing
- **SchedulePlan** - Operator-created plans that fill templates with actual content selections
- **SchedulePlanBlockAssignment** - Time slices within plan blocks that define specific content choices
- **BroadcastScheduleDay** - Resolved schedules for specific channel and date (generated from plans)
- **Asset** - Broadcast-approved content (airable content)
- **BroadcastPlaylogEvent** - Generated playout events (what was actually played)

## Contract / interface

These entities work together in a layered, template-based scheduling model:

**Channel → Template → Plan → ScheduleDay → PlaylogEvent**

1. **Channel** defines the channel identity and timing configuration
2. **ScheduleTemplate** and **ScheduleTemplateBlock** (via **ScheduleTemplateBlockInstance**) define programming structure and content type constraints (guardrails)
3. **SchedulePlan** and **SchedulePlanBlockAssignment** fill templates with actual content selections made by operators
4. **BroadcastScheduleDay** resolves plans into concrete schedules for specific channels and dates
5. **Asset** provides the approved content available for scheduling (must be in `ready` state)
6. **BroadcastPlaylogEvent** represents the generated playout schedule that ChannelManager executes

**Key Distinctions:**
- **Templates** define *what types* of content should appear (structure/constraints)
- **Plans** define *what specific* content appears (operator selections)
- **ScheduleDays** are resolved from plans (immutable execution view)
- **PlaylogEvents** are generated from schedule days (actual playout)

## Execution model

ScheduleService is the primary consumer of the Broadcast Scheduling Domain models. It:

- Resolves active SchedulePlans for channels and dates (based on cron_expression, date ranges, priority)
- Retrieves ScheduleTemplate records referenced by plans (structure/constraints)
- Retrieves ScheduleTemplateBlockInstance entries for templates (links to blocks with timing)
- Retrieves ScheduleTemplateBlock entries referenced by instances (content type constraints/guardrails)
- Retrieves SchedulePlanBlockAssignment entries (actual content selections)
- Validates that assignments respect template block constraints
- Generates BroadcastScheduleDay records (resolved schedules)
- Queries Asset for eligible content (`state='ready'` and `approved_for_broadcast=true`)
- Generates BroadcastPlaylogEvent records as scheduling output
- Uses Channel configuration for timing and grid alignment

**Critical Rules:**

- **Scheduler never touches assets in `new` or `enriching` state**
- **Only assets with `state='ready'` and `approved_for_broadcast=true` are eligible for scheduling**
- **Plan assignments must respect template block constraints (rule_json)**
- **ScheduleDays are immutable once generated (unless manually overridden)**

ProgramDirector coordinates multiple channels and may reference:

- Channel records for channel configuration
- SchedulePlan records for plan resolution and layering
- BroadcastScheduleDay records for cross-channel programming
- ScheduleTemplateBlock constraints (via ScheduleTemplateBlockInstance) for content conflict resolution
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
- [ScheduleTemplate](ScheduleTemplate.md) - Reusable programming templates (structure)
- [ScheduleTemplateBlock](ScheduleTemplateBlock.md) - Time blocks with content type constraints
- [SchedulePlan](SchedulePlan.md) - Operator-created plans that fill templates with actual content
- [ScheduleDay](ScheduleDay.md) - Resolved schedules for specific channel and date
- [PlaylogEvent](PlaylogEvent.md) - Generated playout events
- [PlayoutPipeline](PlayoutPipeline.md) - Live stream generation
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
