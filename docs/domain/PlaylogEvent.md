_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md) • [SchedulePlan](SchedulePlan.md) • [Program](Program.md) • [ScheduleDay](ScheduleDay.md) • [VirtualAsset](VirtualAsset.md)_

# Domain — Playlog event

> **Note:** This document reflects the modern scheduling architecture.  
> The active scheduling chain is: **SchedulePlan → ScheduleDay → PlaylogEvent → AsRunLog.**

## Purpose

BroadcastPlaylogEvent is the **resolved list of media segments to be played**. Each entry maps to a [ScheduleDay](ScheduleDay.md) and points to a resolved concrete asset. PlaylogEvents originate from resolved [BroadcastScheduleDay](ScheduleDay.md) records, which themselves are built from [SchedulePlans](SchedulePlan.md) using Zones (time windows) and Patterns (ordered Program lists). If multiple plans are active, priority resolves overlapping Zones. VirtualAssets are already expanded by ScheduleDay time, so PlaylogEvents reference only concrete assets. This object feeds Producers and ChannelManager so they can build a playout plan at 'now', but this object itself does not launch ffmpeg.

**Critical Rule:** PlaylogEvent is a finalized instruction representing "this asset airs at this absolute time on this channel" - it contains resolved `start_utc`, `end_utc`, and `asset_uuid` values. Each entry maps to a ScheduleDay and points to a resolved concrete asset. PlaylogEvents reflect the **exact wall-clock timestamps derived from ScheduleDay**. VirtualAssets are already expanded by ScheduleDay time, so PlaylogEvents reference only concrete assets, not VirtualAsset containers. The referenced asset must be in `ready` state with `approved_for_broadcast=true`.

**Generation Lineage:** The scheduling flow follows a clear lineage: **Plan → Day → Playlog**

1. **[SchedulePlan](SchedulePlan.md)** - Top-level operator-created plans defining Zones (time windows) and Patterns (ordered lists of Program references). Multiple plans are layered using priority resolution. Zones + Patterns resolve to assets.
2. **[BroadcastScheduleDay](ScheduleDay.md)** - Resolved, immutable daily schedules built from SchedulePlans using Zones (time windows) and Patterns (ordered Program lists). If multiple plans are active, priority resolves overlapping Zones. ScheduleDay is the primary expansion point where Zones + Patterns resolve to concrete assets: Programs → episodes and VirtualAssets → real assets. Contains resolved asset selections and exact wall-clock times.
3. **BroadcastPlaylogEvent** - Finalized playout instructions generated from the resolved schedule day. Each event contains **exact wall-clock timestamps** (`start_utc`, `end_utc`) derived from ScheduleDay and a resolved asset reference (`asset_uuid`) for execution. VirtualAssets are already expanded by ScheduleDay time, so PlaylogEvents reference only concrete assets.

PlaylogEvents reflect the **exact wall-clock timestamps derived from ScheduleDay**. The schedule day's resolved times are computed using Grid alignment: Zone time windows and Pattern repeating behavior are combined with the channel's Grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`) to produce real-world wall-clock times, which are then directly used in PlaylogEvents.

## Core model / scope

BroadcastPlaylogEvent is the **resolved list of media segments to be played**. It enables:

- **Resolved media segments**: Each entry represents a media segment to be played, mapping to a ScheduleDay and pointing to a resolved concrete asset
- **Asset resolution**: Points to resolved assets. VirtualAssets are already expanded by ScheduleDay time, so PlaylogEvents reference only concrete assets.
- **ScheduleDay mapping**: Each entry maps to a ScheduleDay, providing traceability from playout back to the resolved schedule
- Generated playout schedules with exact timing
- Content timing and sequencing
- Playout execution instructions
- Broadcast day tracking and rollover handling
- **Fallback support**: Supports fallback mechanisms when primary content is unavailable
- **Last-minute overrides**: Supports last-minute overrides for emergency changes or special events

## Contract / interface

BroadcastPlaylogEvent is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Unique identifier for relational joins and foreign key references
- **uuid** (UUID, required, unique): Stable external identifier used for audit, cross-domain tracing, and as-run logs
- **channel_id** (Integer, required, foreign key): Reference to Channel
- **asset_uuid** (UUID, required, foreign key): Reference to Asset UUID (primary key) - points to a resolved concrete asset. VirtualAssets are already expanded by ScheduleDay time, so this always references a concrete asset, not a VirtualAsset container.
- **schedule_day_id** (UUID, optional, foreign key): Reference to BroadcastScheduleDay - each entry maps to a ScheduleDay for traceability
- **start_utc** (DateTime(timezone=True), required): Event start time in UTC
- **end_utc** (DateTime(timezone=True), required): Event end time in UTC
- **broadcast_day** (Text, required): Broadcast day label in "YYYY-MM-DD" format
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

BroadcastPlaylogEvent has indexes on channel_id, start_utc, broadcast_day, and asset_uuid for efficient playout queries.

## Execution model

ScheduleService generates BroadcastPlaylogEvent records as the output of the scheduling process. These events represent the final playout schedule that will be executed by ChannelManager and reflect **exact wall-clock timestamps derived from ScheduleDay**. VirtualAssets are already expanded by ScheduleDay time, so PlaylogEvents reference only concrete assets.

**EPG Relationship:** The EPG is just a coarser view of these same scheduling decisions. EPG entries are derived from PlaylogEvent records but show broader time blocks rather than precise asset timing.

**Generation Lineage: Plan → Day → Playlog**

PlaylogEvents originate from resolved [BroadcastScheduleDay](ScheduleDay.md) records, which themselves are built from [SchedulePlans](SchedulePlan.md) using Zones (time windows) and Patterns (ordered Program lists). If multiple plans are active, priority resolves overlapping Zones. The lineage is:

```
SchedulePlans (with Zones and Patterns, priority resolves overlapping Zones)
    ↓
BroadcastScheduleDay (resolved, immutable daily schedule; primary expansion point for Programs→episodes and VirtualAssets→assets)
    ↓
BroadcastPlaylogEvent (finalized instructions with start_utc, end_utc, and resolved asset_uuid)
```

**Detailed Generation Process:**

1. **Plan Resolution**: ScheduleService resolves active [SchedulePlans](SchedulePlan.md) for channels and dates (top-level input defining channel programming). Multiple plans are layered using priority resolution, where more specific plans override generic ones. Plans define Zones (time windows) and Patterns (ordered lists of Program references). **Zones + Patterns resolve to assets.**

2. **Schedule Day Creation**: Creates [BroadcastScheduleDay](ScheduleDay.md) records from plans (priority resolves overlapping Zones). ScheduleDays are built from the plan's Zones, Patterns, and Programs, containing:
   - Resolved asset selections (concrete assets from Zones + Patterns resolving to assets). ScheduleDay is the primary expansion point where Programs → concrete episodes and VirtualAssets → real assets. **VirtualAssets are already expanded by ScheduleDay time.**
   - Exact wall-clock times computed from Zone time windows and Pattern repeating behavior, snapped to the channel's Grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`)
   - Playback instructions derived from the Programs (episode policies, playback rules, operator intent)

3. **Playlog Generation**: Generates BroadcastPlaylogEvent records from the resolved [ScheduleDay](ScheduleDay.md). Each PlaylogEvent is a finalized instruction containing:
   - **Exact wall-clock timestamps** (`start_utc`, `end_utc`) derived directly from the schedule day's resolved times
   - A resolved asset reference (`asset_uuid`) from the schedule day's asset selections - **always points to a concrete asset** (VirtualAssets are already expanded by ScheduleDay time)
   - Mapping to the ScheduleDay (`schedule_day_id`) for traceability
   - Playback instructions from the schedule day (which originated from the plan's Programs)

**Note on VirtualAsset Expansions:** VirtualAssets are expanded at ScheduleDay time, not at PlaylogEvent generation. When a ScheduleDay contains assets that were expanded from VirtualAssets (fixed sequences or rule-based definitions), each resolved asset from the VirtualAsset becomes a separate PlaylogEvent with its own `start_utc`, `end_utc`, and `asset_uuid`. The timing and sequencing from the VirtualAsset expansion are preserved in the generated PlaylogEvents. Each PlaylogEvent maps to the same ScheduleDay and represents one concrete asset from the expanded VirtualAsset.

4. **Time Computation**: PlaylogEvents reflect the **exact wall-clock timestamps derived from ScheduleDay**. The schedule day's resolved times are computed using Grid alignment from the plan's Zones, Patterns, and Programs, and these exact times are used directly in PlaylogEvents.

**Time Resolution:** PlaylogEvents reflect the **exact wall-clock timestamps derived from ScheduleDay**. The schedule day computes wall-clock times using Grid alignment from Zone time windows and Pattern repeating behavior, anchored to the channel's Grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`). These exact times from ScheduleDay are used directly in PlaylogEvents.

**Lineage Summary:**
- **Source of Truth**: Zones + Patterns in [SchedulePlans](SchedulePlan.md) define what should air when. Plans can layer by priority; higher-priority zones override lower ones. Zones + Patterns resolve to assets.
- **Resolved Schedule**: [BroadcastScheduleDay](ScheduleDay.md) is built from SchedulePlans using Zones and Patterns, with priority resolving overlapping Zones. ScheduleDay resolves Zones + Patterns into concrete asset selections with exact wall-clock times. ScheduleDay is the primary expansion point where Programs → episodes and VirtualAssets → assets. **VirtualAssets are already expanded by ScheduleDay time.**
- **Playout Events**: BroadcastPlaylogEvent contains finalized instructions with **exact wall-clock timestamps** (`start_utc`, `end_utc`) derived from ScheduleDay and resolved asset references (`asset_uuid`) for execution. PlaylogEvents reference only concrete assets (VirtualAssets already expanded).

## Failure / fallback behavior

PlaylogEvent supports **fallback mechanisms** to ensure continuous playout when primary content is unavailable:

- **Missing playlog events**: If playlog events are missing or invalid, the system falls back to default programming or the most recent valid schedule
- **Unavailable assets**: If a referenced asset is unavailable (e.g., file missing, corrupted, or not accessible), the system can fall back to:
  - Alternative assets from the same ScheduleDay
  - Default filler content
  - The next available playlog event in sequence
- **Asset segment failures**: For assets that originated from VirtualAsset expansions (already expanded by ScheduleDay time), if one asset fails, the system can:
  - Skip to the next asset in the sequence
  - Fall back to alternative content for that grid block
  - Continue with the remaining assets if the failure is non-critical

**Fallback Priority:**
1. Alternative content from the same ScheduleDay assignment
2. Default filler content configured for the channel
3. Skip to the next playlog event in sequence
4. System-wide default programming

## Last-minute overrides

PlaylogEvent supports **last-minute overrides** to handle emergency changes or special events:

- **Override existing events**: Operators can override specific playlog events post-generation to replace content with emergency updates, breaking news, or special programming
- **Insert new events**: Operators can insert new playlog events into the sequence for last-minute additions
- **Modify timing**: Operators can adjust timing of existing playlog events for last-minute schedule changes
- **Preserve ScheduleDay mapping**: Overridden events maintain their mapping to the original ScheduleDay for audit and traceability purposes

**Override Behavior:**
- Last-minute overrides take precedence over generated playlog events
- Overridden events are marked to indicate they were manually changed
- The original ScheduleDay mapping is preserved for audit trails
- Overrides can be applied even after playlog events have been generated and frozen
- Overrides are applied in real-time and take effect immediately for upcoming playout

**Use Cases:**
- Breaking news interruptions
- Emergency announcements
- Special event programming
- Last-minute content substitutions
- Schedule adjustments for technical issues

## Naming rules

The canonical name for this concept in code and documentation is BroadcastPlaylogEvent.

Playlog events are generated scheduling output, not runtime components. They define "what to play when" but do not execute playout.

## Operator workflows

**Monitor Playout**: View generated playlog events (the resolved list of media segments) to see what content is scheduled to play. Each entry maps to a ScheduleDay and points to a resolved concrete asset.

**Playout Verification**: Verify that scheduled content matches programming intentions and timing. Check that each playlog event correctly maps to its ScheduleDay and references valid concrete assets (VirtualAssets already expanded by ScheduleDay time).

**Content Timing**: Review start/end times to ensure proper content sequencing and timing across the resolved media segments.

**Broadcast Day Management**: Track content across broadcast day boundaries and rollover periods.

**Playout Troubleshooting**: Use playlog events to diagnose playout issues and content problems. Trace issues back to the ScheduleDay and original Zones + Patterns from the plan.

**Fallback Management**: Monitor and configure fallback behavior for when primary content is unavailable. Review fallback chains and ensure default content is properly configured.

**Last-Minute Overrides**: Apply last-minute overrides for emergency changes, breaking news, or special events. Override specific playlog events or insert new events as needed.

## See also

- [Scheduling](Scheduling.md) - High-level scheduling system
- [SchedulePlan](SchedulePlan.md) - Top-level operator-created plans that define channel programming using Zones and Patterns (source of scheduling lineage)
- [Program](Program.md) - Catalog entries in Patterns (expanded to concrete episodes at ScheduleDay time)
- [ScheduleDay](ScheduleDay.md) - Resolved schedules for specific channel and date (primary expansion point for Programs→episodes and VirtualAssets→assets, from which playlog events originate)
- [Scheduling system architecture](../architecture/SchedulingSystem.md) - Detailed scheduling system architecture and flow
- [Asset](Asset.md) - Approved content
- [VirtualAsset](VirtualAsset.md) - ⚠️ FUTURE: Container for multiple assets that expand to concrete assets during ScheduleDay resolution (primary expansion point)
- [PlayoutPipeline](PlayoutPipeline.md) - Live stream generation
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures

**Lineage:** Plans (with Zones + Patterns, priority resolves overlapping Zones) → Day (built from plans using Zones and Patterns, resolves Zones + Patterns to concrete assets with exact wall-clock times; primary expansion point for Programs→episodes and VirtualAssets→assets; VirtualAssets already expanded) → Playlog (resolved list of media segments with exact wall-clock timestamps derived from ScheduleDay, each mapping to a ScheduleDay and pointing to a concrete asset, with support for fallbacks and last-minute overrides)
