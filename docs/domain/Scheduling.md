_Related: [Scheduling system architecture](../architecture/SchedulingSystem.md) • [Architecture overview](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md)_

# Domain — Scheduling

## Purpose

The scheduling system assigns assets (or rules to select them) into time slots for future air. This is planning-time logic that runs ahead of real time and builds out both the EPG horizon (coarse view) and the Playlog horizon (fine-grained view).

**End-to-End Flow:**
1. Operator creates a [SchedulePlan](SchedulePlan.md)
2. Blocks are assigned, optionally grouped with [SchedulePlanLabel](SchedulePlanLabel.md) labels
3. A background daemon uses the channel's programming day anchor to generate [ScheduleDay](ScheduleDay.md) rows 3–4 days in advance
4. ScheduleDays resolve to [PlaylogEvent](PlaylogEvent.md) records
5. PlaylogEvents drive the playout stream

**Critical Rule:** The scheduler and playlog builder may only consider assets where `state == 'ready'` and `approved_for_broadcast == true`.

## Core model / scope

The Broadcast Scheduling Domain defines the core data models that enable RetroVue's scheduling and playout systems. This domain contains the persistent entities that ScheduleService, ProgramDirector, and ChannelManager depend upon for generating and executing broadcast schedules.

### Simplified Architecture

The scheduling system follows a simplified, layered architecture:

1. **SchedulePlan is the top-level construct** - Plans define operator intent for channel programming. Each plan represents a complete 24-hour timeline (00:00 to 24:00 relative to the channel's broadcast day start).

2. **Layering allows combining multiple plans** - Plans can be layered using Photoshop-style priority resolution. For example, a base weekday plan can be overlaid with a holiday-specific plan. Higher priority plans override lower priority plans when both are active for the same date.

3. **SchedulePlanBlockAssignment defines timeline content** - Assignments directly specify what content runs when using `start_time` (absolute offset from 00:00) and `duration`. Assignments can optionally be grouped via [SchedulePlanLabel](SchedulePlanLabel.md) for visual organization in the UI, but labels do not affect scheduling logic.

4. **VirtualAssets enable modular packaging** - [VirtualAssets](VirtualAsset.md) are containers for multiple assets that can be referenced in assignments. They expand to actual assets during schedule resolution, enabling reusable modular programming blocks (e.g., branded intro → episode → outro).

5. **Scheduler builds ScheduleDay (resolved, immutable) → PlaylogEvent (runtime)** - The Scheduler resolves active plans into [BroadcastScheduleDay](ScheduleDay.md) records, which are resolved, immutable daily schedules. ScheduleDays are then used to generate [BroadcastPlaylogEvent](PlaylogEvent.md) records for actual playout execution.

### Primary Models

The Broadcast Scheduling Domain consists of these primary models:

- **Channel** - Channel configuration and timing policy
- **SchedulePlan** - Top-level scheduling construct that defines operator intent
- **SchedulePlanBlockAssignment** - Timeline content definitions within plans
- **SchedulePlanLabel** - Optional UI-only labels for visual grouping (does not affect scheduling)
- **VirtualAsset** - Modular asset containers for reusable programming blocks
- **BroadcastScheduleDay** - Resolved, immutable daily schedules (generated from plans)
- **Asset** - Broadcast-approved content (airable content)
- **BroadcastPlaylogEvent** - Generated playout events (runtime execution)

## Contract / interface

### Architecture Flow

The scheduling system follows this end-to-end flow:

**Operator creates SchedulePlan → Blocks assigned (optionally grouped with labels) → Background daemon generates ScheduleDay 3–4 days in advance → ScheduleDays resolve to PlaylogEvents → PlaylogEvents drive playout stream**

1. **Operator creates SchedulePlan**: Operators create [SchedulePlan](SchedulePlan.md) records that define channel programming intent. Plans can be layered (e.g., base plan + holiday overlay) with higher priority plans overriding lower priority plans.

2. **Blocks are assigned, optionally grouped with labels**: Operators assign [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) entries to plans, directly specifying what content runs when using `start_time` (absolute offset from 00:00) and `duration`. Assignments can reference assets, series, rules, or [VirtualAssets](VirtualAsset.md). Assignments can optionally be grouped via [SchedulePlanLabel](SchedulePlanLabel.md) for visual organization (labels do not affect scheduling logic).

3. **Background daemon generates ScheduleDay 3–4 days in advance**: A background daemon (ScheduleService) uses the channel's programming day anchor (`programming_day_start` / `broadcast_day_start`) to generate [ScheduleDay](ScheduleDay.md) rows 3–4 days in advance. ScheduleDays are resolved, immutable daily schedules that contain resolved asset selections with real-world wall-clock times.

4. **ScheduleDays resolve to PlaylogEvents**: [PlaylogEvent](PlaylogEvent.md) records are generated from ScheduleDay records. Each PlaylogEvent is a resolved media segment mapping to a ScheduleDay and pointing to a resolved asset or asset segment.

5. **PlaylogEvents drive the playout stream**: PlaylogEvents contain precise timestamps for playout execution and feed ChannelManager for actual playout stream generation.

### Key Architectural Principles

- **SchedulePlan is the top-level construct** - All scheduling logic flows from plans
- **Layering enables plan composition** - Multiple plans can be combined (base + overlays)
- **Assignments define timeline content** - Direct time-based content placement
- **Labels are UI-only** - SchedulePlanLabel provides visual organization but does not affect scheduling
- **VirtualAssets enable modularity** - Reusable asset containers for complex programming blocks
- **ScheduleDay is resolved and immutable** - Once generated, days are locked unless manually overridden
- **PlaylogEvent is runtime** - Generated from ScheduleDay for actual playout execution

## Execution model

### Scheduler Process

The Scheduler (ScheduleService) is a background daemon that processes the Broadcast Scheduling Domain models. It follows this end-to-end flow:

1. **Operator creates SchedulePlan**: Operators create SchedulePlan records that define channel programming intent. Plans can be layered (e.g., base plan + holiday overlay) with higher priority plans overriding lower priority plans.

2. **Blocks are assigned, optionally grouped with labels**: Operators assign SchedulePlanBlockAssignment entries to plans, directly specifying what content runs when using `start_time` (absolute offset from 00:00) and `duration`. Assignments can reference assets, series, rules, or VirtualAssets. Assignments can optionally be grouped via SchedulePlanLabel for visual organization (labels do not affect scheduling logic).

3. **Background daemon generates ScheduleDay 3–4 days in advance**: The ScheduleService background daemon:
   - Identifies active SchedulePlans for channels and dates (based on cron_expression, date ranges, priority)
   - Applies layering: combines multiple plans using priority resolution (higher priority plans override lower priority plans)
   - Retrieves SchedulePlanBlockAssignment entries from active plans
   - Resolves VirtualAssets to actual assets (if referenced in assignments)
   - Resolves content references (assets, series, rules) to specific assets
   - Uses the channel's programming day anchor (`programming_day_start` / `broadcast_day_start`) to anchor schedule times
   - Builds BroadcastScheduleDay records (resolved, immutable daily schedules) 3–4 days in advance
   - Combines assignment times with channel's programming day anchor to produce real-world wall-clock times
   - Resolves all content selections to concrete assets
   - Validates assignments and ensures no gaps or conflicts

4. **ScheduleDays resolve to PlaylogEvents**: The ScheduleService generates BroadcastPlaylogEvent records from ScheduleDay records:
   - Each PlaylogEvent is a resolved media segment mapping to a ScheduleDay
   - Points to a resolved asset or asset segment (for VirtualAssets)
   - Creates precise playout timestamps for runtime execution

5. **PlaylogEvents drive the playout stream**: PlaylogEvents feed ChannelManager for actual playout stream generation.

### Content Eligibility

The Scheduler queries Asset for eligible content:
- Only assets with `state='ready'` and `approved_for_broadcast=true` are eligible
- VirtualAssets expand to actual assets during resolution
- Content references (series, rules) resolve to eligible assets

**Critical Rules:**

- **Scheduler never touches assets in `new` or `enriching` state**
- **Only assets with `state='ready'` and `approved_for_broadcast=true` are eligible for scheduling**
- **Plan assignments directly define time structure using `start_time` (absolute offset from 00:00) and `duration`**
- **ScheduleDays are immutable once generated (unless manually overridden)**

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

Scheduling runs ahead of real time and builds out both the EPG horizon (coarse view) and the Playlog horizon (fine-grained view). If scheduling fails, the system falls back to the most recent successful schedule or default programming.

## Naming rules

The canonical name for this concept in code and documentation is "Scheduling" or "Broadcast Scheduling Domain".

Scheduling is planning-time logic, not runtime logic. It defines "what to play when" but does not execute playout.

All scheduling logic, operator tooling, and documentation MUST refer to the Broadcast Scheduling Domain as the complete data foundation for automated broadcast programming.

## See also

- [Scheduling system architecture](../architecture/SchedulingSystem.md) - Comprehensive scheduling system architecture
- [Scheduling roadmap](../architecture/SchedulingRoadmap.md) - Implementation roadmap
- [SchedulePlan](SchedulePlan.md) - Top-level scheduling construct that defines operator intent
- [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) - Timeline content definitions within plans
- [SchedulePlanLabel](SchedulePlanLabel.md) - Optional UI-only labels for visual grouping
- [VirtualAsset](VirtualAsset.md) - Modular asset containers for reusable programming blocks
- [ScheduleDay](ScheduleDay.md) - Resolved, immutable daily schedules (generated from plans)
- [PlaylogEvent](PlaylogEvent.md) - Generated playout events (runtime execution)
- [PlayoutPipeline](PlayoutPipeline.md) - Live stream generation
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
