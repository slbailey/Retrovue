_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md) • [SchedulePlan](SchedulePlan.md) • [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) • [ScheduleDay](ScheduleDay.md) • [VirtualAsset](VirtualAsset.md)_

# Domain — Playlog event

## Purpose

BroadcastPlaylogEvent is the **resolved list of media segments to be played**. Each entry maps to a [ScheduleDay](ScheduleDay.md) and points to a resolved asset or asset segment (for [VirtualAssets](VirtualAsset.md)). PlaylogEvents originate from resolved [BroadcastScheduleDay](ScheduleDay.md) records, which themselves are built from layered [SchedulePlans](SchedulePlan.md) (using Photoshop-style priority resolution) containing [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) entries. This object feeds Producers and ChannelManager so they can build a playout plan at 'now', but this object itself does not launch ffmpeg.

**Critical Rule:** PlaylogEvent is a finalized instruction representing "this asset or asset segment airs at this absolute time on this channel" - it contains resolved `start_utc`, `end_utc`, and `asset_uuid` values. Each entry maps to a ScheduleDay and points to a resolved asset (for direct assignments) or an asset segment (for VirtualAssets that expand to multiple assets). The referenced asset must be in `ready` state with `approved_for_broadcast=true`.

**Generation Lineage:** The scheduling flow follows a clear lineage: **Plan → Day → Playlog**

1. **[SchedulePlan](SchedulePlan.md)** - Top-level operator-created plans containing [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) entries that define what content should air when. Multiple plans are layered using Photoshop-style priority resolution.
2. **[BroadcastScheduleDay](ScheduleDay.md)** - Resolved, immutable daily schedules built from layered SchedulePlans, with resolved asset selections and wall-clock times
3. **BroadcastPlaylogEvent** - Finalized playout instructions generated from the resolved schedule day. Each event contains precise timestamps (`start_utc`, `end_utc`) and a resolved asset reference (`asset_uuid`) for execution

The exact playout times in PlaylogEvents are computed using broadcast day alignment: the schedule times from the plan assignments are combined with the channel's `broadcast_day_start` to produce real-world wall-clock times.

## Core model / scope

BroadcastPlaylogEvent is the **resolved list of media segments to be played**. It enables:

- **Resolved media segments**: Each entry represents a media segment to be played, mapping to a ScheduleDay and pointing to a resolved asset or asset segment
- **Asset resolution**: Points to resolved assets (for direct assignments) or asset segments (for VirtualAssets that expand to multiple assets)
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
- **asset_uuid** (UUID, required, foreign key): Reference to Asset UUID (primary key) - points to a resolved asset or asset segment (for VirtualAssets that expand to multiple assets)
- **schedule_day_id** (UUID, optional, foreign key): Reference to BroadcastScheduleDay - each entry maps to a ScheduleDay for traceability
- **start_utc** (DateTime(timezone=True), required): Event start time in UTC
- **end_utc** (DateTime(timezone=True), required): Event end time in UTC
- **broadcast_day** (Text, required): Broadcast day label in "YYYY-MM-DD" format
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

BroadcastPlaylogEvent has indexes on channel_id, start_utc, broadcast_day, and asset_uuid for efficient playout queries.

## Execution model

ScheduleService generates BroadcastPlaylogEvent records as the output of the scheduling process. These events represent the final playout schedule that will be executed by ChannelManager and reflect exact playout times.

**EPG Relationship:** The EPG is just a coarser view of these same scheduling decisions. EPG entries are derived from PlaylogEvent records but show broader time blocks rather than precise asset timing.

**Generation Lineage: Plan → Day → Playlog**

PlaylogEvents originate from resolved [BroadcastScheduleDay](ScheduleDay.md) records, which themselves are built from layered [SchedulePlans](SchedulePlan.md) containing [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) entries. The lineage is:

```
Layered SchedulePlans (with SchedulePlanBlockAssignments)
    ↓
BroadcastScheduleDay (resolved, immutable daily schedule built from layered plans)
    ↓
BroadcastPlaylogEvent (finalized instructions with start_utc, end_utc, and resolved asset_uuid)
```

**Detailed Generation Process:**

1. **Plan Resolution**: ScheduleService resolves active [SchedulePlans](SchedulePlan.md) for channels and dates (top-level input defining channel programming). Multiple plans are layered using Photoshop-style priority resolution, where more specific plans override generic ones. Plans contain [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) entries that define what content should air when.

2. **Schedule Day Creation**: Creates [BroadcastScheduleDay](ScheduleDay.md) records from the layered plans. ScheduleDays are built from the plan's [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) entries, containing:
   - Resolved asset selections (concrete assets selected from assignments, including assets expanded from [VirtualAssets](VirtualAsset.md) if referenced)
   - Wall-clock times computed from assignment schedule times plus the channel's `broadcast_day_start` (broadcast day alignment)
   - Playback instructions derived from the assignments (episode policies, playback rules, operator intent)

3. **Playlog Generation**: Generates BroadcastPlaylogEvent records from the resolved [ScheduleDay](ScheduleDay.md). Each PlaylogEvent is a finalized instruction containing:
   - Exact playout times (`start_utc`, `end_utc`) extracted from the schedule day's resolved times
   - A resolved asset reference (`asset_uuid`) from the schedule day's asset selections - points to a resolved asset (for direct assignments) or an asset segment (for VirtualAssets)
   - Mapping to the ScheduleDay (`schedule_day_id`) for traceability
   - Playback instructions from the schedule day (which originated from the plan's assignments)

**Note on VirtualAsset Expansions:** PlaylogEvents may originate from [VirtualAsset](VirtualAsset.md) expansions. When a ScheduleDay contains assets that were expanded from VirtualAssets (fixed sequences or rule-based definitions), each resolved asset from the VirtualAsset becomes a separate PlaylogEvent (asset segment) with its own `start_utc`, `end_utc`, and `asset_uuid`. The timing and sequencing from the VirtualAsset are preserved in the generated PlaylogEvents. Each asset segment maps to the same ScheduleDay and represents one segment of the expanded VirtualAsset.

4. **Time Computation**: The exact playout times in PlaylogEvents reflect the real-world wall-clock times derived from the schedule day's resolved times, which were computed using broadcast day alignment from the plan's [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) entries.

**Time Resolution:** Broadcast day alignment is used to compute wall-clock time from schedule time. The channel's `broadcast_day_start` anchors the plan's schedule times (from [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) `start_time` and `duration`) to produce the exact playout times in PlaylogEvents.

**Lineage Summary:**
- **Source of Truth**: [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) entries in layered [SchedulePlans](SchedulePlan.md) define what should air when
- **Resolved Schedule**: [BroadcastScheduleDay](ScheduleDay.md) is built from layered SchedulePlans and resolves assignments into concrete asset selections (including VirtualAsset expansions) with wall-clock times
- **Playout Events**: BroadcastPlaylogEvent contains finalized instructions with exact playout times (`start_utc`, `end_utc`) and resolved asset references (`asset_uuid`) for execution

## Failure / fallback behavior

PlaylogEvent supports **fallback mechanisms** to ensure continuous playout when primary content is unavailable:

- **Missing playlog events**: If playlog events are missing or invalid, the system falls back to default programming or the most recent valid schedule
- **Unavailable assets**: If a referenced asset is unavailable (e.g., file missing, corrupted, or not accessible), the system can fall back to:
  - Alternative assets from the same ScheduleDay
  - Default filler content
  - The next available playlog event in sequence
- **Asset segment failures**: For VirtualAssets that expand to multiple asset segments, if one segment fails, the system can:
  - Skip to the next segment in the sequence
  - Fall back to alternative content for that time slot
  - Continue with the remaining segments if the failure is non-critical

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

**Monitor Playout**: View generated playlog events (the resolved list of media segments) to see what content is scheduled to play. Each entry maps to a ScheduleDay and points to a resolved asset or asset segment.

**Playout Verification**: Verify that scheduled content matches programming intentions and timing. Check that each playlog event correctly maps to its ScheduleDay and references valid resolved assets or asset segments.

**Content Timing**: Review start/end times to ensure proper content sequencing and timing across the resolved media segments.

**Broadcast Day Management**: Track content across broadcast day boundaries and rollover periods.

**Playout Troubleshooting**: Use playlog events to diagnose playout issues and content problems. Trace issues back to the ScheduleDay and original plan assignments.

**Fallback Management**: Monitor and configure fallback behavior for when primary content is unavailable. Review fallback chains and ensure default content is properly configured.

**Last-Minute Overrides**: Apply last-minute overrides for emergency changes, breaking news, or special events. Override specific playlog events or insert new events as needed.

## See also

- [Scheduling](Scheduling.md) - High-level scheduling system
- [SchedulePlan](SchedulePlan.md) - Top-level operator-created plans that define channel programming (source of scheduling lineage)
- [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) - Scheduled pieces of content in plans (source of truth for what should air when, from which schedule days are composed)
- [ScheduleDay](ScheduleDay.md) - Resolved schedules for specific channel and date (composed from plan assignments, from which playlog events originate)
- [Scheduling system architecture](../architecture/SchedulingSystem.md) - Detailed scheduling system architecture and flow
- [Asset](Asset.md) - Approved content
- [VirtualAsset](VirtualAsset.md) - ⚠️ FUTURE: Container for multiple assets that expand to concrete assets during ScheduleDay resolution or PlaylogEvent generation
- [PlayoutPipeline](PlayoutPipeline.md) - Live stream generation
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures

**Lineage:** Layered Plans (with SchedulePlanBlockAssignments) → Day (built from layered plans, resolves assignments including VirtualAsset expansions) → Playlog (resolved list of media segments, each mapping to a ScheduleDay and pointing to a resolved asset or asset segment, with support for fallbacks and last-minute overrides)
