_Related: [Scheduling system architecture](../architecture/SchedulingSystem.md) • [Architecture overview](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md)_

# Domain — Scheduling

> **Note:** This document reflects the modern scheduling architecture. Active chain: **SchedulePlan (Zones + Patterns) → ScheduleDay (resolved) → PlaylogEvent (runtime) → AsRunLog.**

> **Chain:** Channel (Grid) → SchedulePlan (Zones + Patterns) → ScheduleDay (resolved) → PlaylogEvent (runtime) → AsRunLog.

## Purpose

The scheduling system assigns assets (or rules to select them) into grid blocks for future air. This is planning-time logic that runs ahead of real time and extends the plan horizon (coarse view) and builds the runtime playlog (fine-grained view).

**End-to-End Flow:**
1. Operator creates a [SchedulePlan](SchedulePlan.md) defining Zones (time windows) and Patterns (ordered lists of Program references)
2. Programs are added to Patterns as catalog entries (series, movies, blocks, composites)
3. SchedulingService uses the channel's Grid boundaries to generate [ScheduleDay](ScheduleDay.md) rows 3–4 days in advance. ScheduleDay is the primary expansion point for Programs → episodes and VirtualAssets → assets.
4. ScheduleDays resolve to [PlaylogEvent](PlaylogEvent.md) records
5. PlaylogEvents drive the playout stream

**Flow:** Plan → ScheduleDay (resolved 3–4 days out) → PlaylogEvent

**Relationship Diagram:**

```
SchedulePlan ─┬─> ScheduleDay ─┬─> PlaylogEvent
               │                 └─> AsRunLog
               │
               └─> Policy/Rules
```

This visual shows the cascade: SchedulePlan generates ScheduleDay (realization), which produces PlaylogEvent (runtime execution) and AsRunLog (audit trail). Policies and rules govern the transformation from Plan to Day.

**Critical Rule:** The scheduler and playlog builder may only consider assets where `state == 'ready'` and `approved_for_broadcast == true`.

## Plan Horizon

The scheduling system operates on a **plan → realization** model:

**SchedulePlan** is the **abstract plan** that defines operator intent:
- Defines Zones (time windows) and Patterns (ordered lists of Program references)
- Timeless and reusable — the same plan can generate different ScheduleDays for different dates
- Contains no specific dates, episodes, or assets — only the structure and catalog references

**ScheduleDay** is the **concrete, date-bound realization**:
- Represents a concrete, date-bound instance of a channel's plan
- Built automatically by SchedulingService 3–4 days in advance
- Generated from the abstract SchedulePlan (zones + patterns) and resolved into real Programs and VirtualAssets
- Immutable once generated — provides stable EPG and playout instructions
- Each ScheduleDay is tied to a specific channel and date

**Key Distinction:**
- **SchedulePlan** = Plan (what should play, when in the day, but not which specific episodes)
- **ScheduleDay** = Realization (which specific episodes/assets play on which specific date)

SchedulingService continuously monitors active plans and extends the plan horizon ahead of time, ensuring the EPG and playout pipeline are always populated with resolved, concrete schedules.

## Core model / scope

The Broadcast Scheduling Domain defines the core data models that enable RetroVue's scheduling and playout systems. This domain contains the persistent entities that ScheduleService, ProgramDirector, and ChannelManager depend upon for generating and executing broadcast schedules.

### Simplified Architecture

The scheduling system follows a simplified architecture based on Zones + Patterns:

**Core Model:** Channel Grid → Plan Zones → repeating Patterns (Program references)

1. **Channel owns the Grid** - Channel owns the Grid configuration (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`) that defines temporal boundaries. All scheduling snaps to these grid boundaries.

2. **SchedulePlan defines Zones** - Plans define operator intent for channel programming using Zones (time windows with optional day filters). Each Zone references a Pattern.

3. **Patterns repeat over Zones** - Patterns are ordered lists of Program references (catalog entries). No durations inside the pattern — the plan engine repeats the pattern over the Zone until the Zone is full, snapping to the Channel's Grid boundaries.

4. **Programs are catalog entities** - Programs in Patterns are schedulable entities such as series, movies, blocks, or composites (can reference [VirtualAssets](VirtualAsset.md)). Episodes are resolved automatically at ScheduleDay time based on rotation policy.

5. **Layering allows combining multiple plans** - Plans may layer by priority; more specific plans override generic ones within overlapping windows. Higher priority plans override lower priority plans when both are active for the same date. Zones from higher-priority plans override overlapping Zones from lower-priority plans.

6. **VirtualAssets enable modular packaging** - [VirtualAssets](VirtualAsset.md) are containers for multiple assets that can be referenced in Programs. They expand to actual assets during ScheduleDay resolution (primary expansion point), enabling reusable modular programming blocks (e.g., branded intro → episode → outro).

7. **Scheduler builds ScheduleDay (resolved, immutable) → PlaylogEvent (runtime)** - The Scheduler resolves active plans into [BroadcastScheduleDay](ScheduleDay.md) records, which are resolved, immutable daily schedules. ScheduleDay is the primary expansion point for Programs → episodes and VirtualAssets → assets. ScheduleDays are then used to generate [BroadcastPlaylogEvent](PlaylogEvent.md) records for actual playout execution.

### Primary Models

The Broadcast Scheduling Domain consists of these primary models:

- **Channel** - Channel configuration and timing policy (owns Grid: `grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`)
- **SchedulePlan** - Top-level scheduling construct that defines operator intent using Zones and Patterns
- **Zone** - Named time windows within the programming day (e.g., base 00:00–24:00, or After Dark 22:00–05:00)
- **Pattern** - Ordered lists of Programs (catalog entries). No durations inside the pattern — the plan engine repeats the pattern over the Zone until the Zone is full.
- **Program** - Catalog entries (schedulable entities) in Patterns: series, movies, blocks, composites (can reference VirtualAssets)
- **VirtualAsset** - Modular asset containers for reusable programming blocks (expanded at ScheduleDay time)
- **BroadcastScheduleDay** - Resolved, immutable daily schedules (generated from plans). Primary expansion point for Programs → episodes and VirtualAssets → assets.
- **Asset** - Broadcast-approved content (airable content)
- **BroadcastPlaylogEvent** - Generated playout events (runtime execution)

## Contract / interface

### Architecture Flow

The scheduling system follows this end-to-end flow:

**Operator creates SchedulePlan → Zones and Patterns defined → Programs added to Patterns → Background daemon generates ScheduleDay 3–4 days in advance (primary expansion point) → ScheduleDays resolve to PlaylogEvents → PlaylogEvents drive playout stream**

1. **Operator creates SchedulePlan**: Operators create [SchedulePlan](SchedulePlan.md) records that define channel programming intent using Zones (time windows with optional day filters) and Patterns (ordered lists of Program references). Plans can be layered (e.g., base plan + holiday overlay) with higher priority plans overriding lower priority plans.

2. **Zones and Patterns are defined**: Operators define Zones (named time windows within the programming day, e.g., base 00:00–24:00, or After Dark 22:00–05:00, with optional day filters like Mon–Fri) and Patterns (ordered lists of Program references) for each Zone. Patterns have no durations — the plan engine repeats the pattern over the Zone until the Zone is full.

3. **Programs are added to Patterns**: Operators add [Program](Program.md) references (catalog entries) to Patterns. Programs are schedulable entities such as series, movies, blocks, or composites (can reference [VirtualAssets](VirtualAsset.md)).

4. **SchedulingService extends the plan horizon 3–4 days in advance**: SchedulingService uses the channel's Grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`) to generate [ScheduleDay](ScheduleDay.md) rows 3–4 days in advance. ScheduleDays are resolved, immutable daily schedules that contain resolved asset selections with real-world wall-clock times. **ScheduleDay is the primary expansion point for Programs → concrete episodes and VirtualAssets → real assets.**

5. **ScheduleDays resolve to PlaylogEvents**: [PlaylogEvent](PlaylogEvent.md) records are generated from ScheduleDay records. Each PlaylogEvent is a resolved media segment mapping to a ScheduleDay and pointing to a resolved asset or asset segment.

6. **PlaylogEvents drive the playout stream**: PlaylogEvents contain precise timestamps for playout execution and feed ChannelManager for actual playout stream generation.

### Key Architectural Principles

- **Channel owns the Grid** - Channel owns Grid configuration (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`). All scheduling snaps to these boundaries.
- **SchedulePlan is the top-level construct** - All scheduling logic flows from plans defining Zones and Patterns
- **Zones + Patterns model** - Plans define Zones (time windows) and Patterns (ordered lists of Programs). Patterns have no durations — the plan engine repeats the pattern over the Zone until the Zone is full.
- **Programs are catalog entries** - Programs in Patterns are schedulable entities (series, movies, blocks, composites) without durations. Episodes are resolved at ScheduleDay time.
- **Layering enables plan composition** - Plans may layer by priority; more specific plans override generic ones within overlapping windows. Zones from higher-priority plans override overlapping Zones from lower-priority plans.
- **VirtualAssets enable modularity** - Reusable asset containers for complex programming blocks (expanded at ScheduleDay time)
- **ScheduleDay is resolved and immutable** - Once generated, days are locked unless manually overridden. ScheduleDay is the primary expansion point for Programs → episodes and VirtualAssets → assets.
- **PlaylogEvent is runtime** - Generated from ScheduleDay for actual playout execution

## Execution model

### Scheduler Process

The Scheduler (ScheduleService) is a background daemon that processes the Broadcast Scheduling Domain models. It follows this end-to-end flow:

1. **Operator creates SchedulePlan**: Operators create SchedulePlan records that define channel programming intent using Zones (time windows with optional day filters) and Patterns (ordered lists of Program references). Plans can be layered (e.g., base plan + holiday overlay) with higher priority plans overriding lower priority plans.

2. **Zones and Patterns are defined**: Operators define Zones (named time windows within the programming day, with optional day filters) and Patterns (ordered lists of Program references) for each Zone. Patterns have no durations — the plan engine repeats the pattern over the Zone until the Zone is full.

3. **Programs are added to Patterns**: Operators add Program references (catalog entries) to Patterns. Programs are schedulable entities such as series, movies, blocks, or composites (can reference VirtualAssets).

4. **SchedulingService extends the plan horizon 3–4 days in advance**: The SchedulingService:
   - Identifies active SchedulePlans for channels and dates (based on cron_expression, date ranges, priority)
   - Applies layering: combines multiple plans using priority resolution (higher priority plans override lower priority plans). Zones from higher-priority plans override overlapping Zones from lower-priority plans.
   - Retrieves Zones and Patterns from active plans
   - Repeats Patterns over Zones until Zones are full, snapping to the Channel's Grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`)
   - Applies scheduling policies: grid alignment, soft-start-after-current, snap-next-boundary, fixed zone end, no mid-longform cuts, carry-in across broadcast day seams
   - **Primary expansion point**: ScheduleDay is the primary expansion point for Programs → concrete episodes and VirtualAssets → real assets
   - Resolves VirtualAssets to actual assets (if referenced in Programs)
   - Resolves content references (assets, series, rules) to specific assets
   - Uses the channel's Grid boundaries to anchor Zone time windows and Pattern repeating behavior
   - Builds BroadcastScheduleDay records (resolved, immutable daily schedules) 3–4 days in advance
   - Combines Zone time windows and Pattern repeating behavior with channel's Grid boundaries to produce real-world wall-clock times
   - Resolves all content selections to concrete assets
   - Validates Zones, Patterns, and Programs and ensures no gaps or conflicts

5. **ScheduleDays resolve to PlaylogEvents**: The ScheduleService generates BroadcastPlaylogEvent records from ScheduleDay records:
   - Each PlaylogEvent is a resolved media segment mapping to a ScheduleDay
   - Points to a resolved asset or asset segment (for VirtualAssets)
   - Creates precise playout timestamps for runtime execution

6. **PlaylogEvents drive the playout stream**: PlaylogEvents feed ChannelManager for actual playout stream generation.

### Content Eligibility

The Scheduler queries Asset for eligible content:
- Only assets with `state='ready'` and `approved_for_broadcast=true` are eligible
- VirtualAssets expand to actual assets during resolution
- Content references (series, rules) resolve to eligible assets

**Critical Rules:**

- **Eligibility rule**: Scheduler never touches assets in `new` or `enriching` state. Only assets with `state='ready'` and `approved_for_broadcast=true` are eligible for scheduling.
- **Immutability rule**: ScheduleDays are immutable once generated (unless manually overridden)

**Scheduling Policies:**

See [SchedulingPolicies.md](SchedulingPolicies.md) for detailed descriptions of each policy and their user-facing outcomes.

- **Grid alignment**: All scheduling snaps to the Channel's Grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`)
- **Soft-start-after-current**: When a Zone opens while content is already playing, the current program continues to completion, and the new Zone's Pattern starts at the next valid Grid boundary
- **Snap-next-boundary**: Content placement snaps to the next valid Grid boundary when transitioning between Zones
- **Fixed zone end**: Zones have fixed end times; Patterns repeat until the Zone is full, respecting the zone boundary
- **No mid-longform cuts**: Longform content (with `slot_units` override) is never cut mid-program; it consumes the required number of grid blocks
- **Carry-in across broadcast day seams**: Content can carry in across broadcast day boundaries (e.g., a program starting at 23:30 can continue into the next programming day)
- **Patterns have no durations** — the plan engine repeats the pattern over the Zone until the Zone is full
- **ScheduleDay is the primary expansion point** for Programs → episodes and VirtualAssets → assets

ProgramDirector coordinates multiple channels and may reference:

- Channel records for channel configuration
- SchedulePlan records for plan resolution and layering
- BroadcastScheduleDay records for cross-channel programming
- Asset records for content availability and approval status

ChannelManager executes playout but does not modify any Broadcast Scheduling Domain models. It:

- Reads BroadcastPlaylogEvent records for playout instructions
- References Channel configuration for channel identity
- Uses Asset file paths for content playback

**Critical Rule:**

- **Runtime never spins up playout for an asset unless it's in `ready` state**

## Failure / fallback behavior

Scheduling runs ahead of real time and extends the plan horizon (coarse view) and builds the runtime playlog (fine-grained view). If scheduling fails, the system falls back to the most recent successful schedule or default programming.

## Naming rules

The canonical name for this concept in code and documentation is "Scheduling" or "Broadcast Scheduling Domain".

Scheduling is planning-time logic, not runtime logic. It defines "what to play when" but does not execute playout.

All scheduling logic, operator tooling, and documentation MUST refer to the Broadcast Scheduling Domain as the complete data foundation for automated broadcast programming.

## Invocation

Scheduling can be invoked either via CLI or programmatically:

**CLI Example:**

```bash
retrovue schedule plan build --channel-id=1 --date=2025-11-07
```

**Programmatic Example:**

```python
from retrovue.app.schedule import build_schedule_plan
build_schedule_plan(channel_id=1, date=date(2025, 11, 7))
```

The CLI entrypoint provides a user-friendly interface to the underlying scheduling functions, which handle plan resolution, Zone/Pattern expansion, and ScheduleDay generation.

**Note:** The CLI "plan-building mode" is a front-end to the same schedule engine the UI uses; both call the same SchedulePlanService methods.

## Next Steps

Implementation checklist for the scheduling system:

- [ ] Implement CLI entrypoint for schedule planning
- [ ] Add FastAPI endpoint for on-demand regeneration
- [ ] Write tests for plan/daily generation integrity

## See also

- [Scheduling system architecture](../architecture/SchedulingSystem.md) - Comprehensive scheduling system architecture
- [Scheduling roadmap](../architecture/SchedulingRoadmap.md) - Implementation roadmap
- [Channel](Channel.md) - Channel configuration and timing policy (owns Grid)
- [SchedulePlan](SchedulePlan.md) - Top-level scheduling construct that defines operator intent using Zones and Patterns
- [Program](Program.md) - Catalog entries (schedulable entities) in Patterns
- [VirtualAsset](VirtualAsset.md) - Modular asset containers for reusable programming blocks (expanded at ScheduleDay time)
- [ScheduleDay](ScheduleDay.md) - Resolved, immutable daily schedules (generated from plans). Primary expansion point for Programs → episodes and VirtualAssets → assets.
- [PlaylogEvent](PlaylogEvent.md) - Generated playout events (runtime execution)
- [PlayoutPipeline](PlayoutPipeline.md) - Live stream generation
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
