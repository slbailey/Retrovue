_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md) • [Contracts](../contracts/README.md) • [Channel](Channel.md) • [SchedulePlan](SchedulePlan.md) • [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) • [PlaylogEvent](PlaylogEvent.md)_

# Domain — Schedule day

## Purpose

BroadcastScheduleDay is a **resolved, immutable daily schedule** for a specific channel and calendar date. **It is derived from [SchedulePlan](SchedulePlan.md)** and materialized 3–4 days in advance. Once generated, the schedule day is **frozen** (locked and immutable) unless force-regenerated or manually overridden by an operator.

The schedule day contains the resolved schedule for a channel on a specific date, with resolved asset selections and real-world wall-clock times. **Wall-clock times are calculated by anchoring schedule times to the channel's `programming_day_start`** (also referred to as `broadcast_day_start`). Schedule times from [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) entries are expressed as `start_time` offsets from 00:00 (relative to the programming day), and the channel's `programming_day_start` defines when the programming day begins in wall-clock time (e.g., 6:00 AM local time). The resolution process anchors the schedule time offsets to the `programming_day_start` to produce the final wall-clock times.

ScheduleDay contains **resolved `asset_uuid` entries** that reference concrete Asset records. These asset UUIDs may be derived directly from plan assignments, or they may be resolved from [VirtualAssets](VirtualAsset.md) that were referenced in the plan assignments. When a VirtualAsset is referenced in a [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md), it expands to one or more concrete Asset UUIDs during ScheduleDay generation.

The EPG references this layer, and [PlaylogEvents](PlaylogEvent.md) are generated from it. This is the execution-time view of "what will air on this channel on this date" after resolving plans into concrete content selections.

## Persistence model

BroadcastScheduleDay is managed by SQLAlchemy with the following fields:

- **id** (UUID, primary key): Unique identifier for relational joins and foreign key references
- **channel_id** (UUID, required, foreign key): Reference to Channel
- **plan_id** (UUID, optional, foreign key): Reference to SchedulePlan that generated this schedule day
- **schedule_date** (Text, required): Broadcast date in "YYYY-MM-DD" format
- **is_manual_override** (Boolean, required, default: false): Whether this schedule day was manually overridden
- **created_at** (DateTime(timezone=True), required): Record creation timestamp
- **updated_at** (DateTime(timezone=True), required): Record last modification timestamp

BroadcastScheduleDay has a unique constraint on (channel_id, schedule_date) ensuring only one schedule per channel per date.

**Note:** While `plan_id` is optional, the system typically generates schedule days from plans. Manual overrides may not reference a plan.

### Table name

The table is named `broadcast_schedule_days` (plural). Schema migration is handled through Alembic. Postgres is the authoritative backing store.

### Constraints

- `schedule_date` must be in "YYYY-MM-DD" format
- Unique constraint on (channel_id, schedule_date) ensures only one schedule per channel per broadcast day
- Foreign key constraints ensure channel_id and plan_id reference valid entities

## Contract / interface

BroadcastScheduleDay is a resolved, immutable daily schedule **derived from [SchedulePlan](SchedulePlan.md)** and **materialized 3–4 days in advance**. It provides the concrete schedule for a specific channel and calendar date. Once generated, the schedule day is **frozen** (locked and immutable) unless force-regenerated or manually overridden. It contains resolved asset selections with real-world wall-clock times and playback instructions. It defines:

- Channel assignment (channel_id) - the channel this schedule applies to
- Plan reference (plan_id) - the [SchedulePlan](SchedulePlan.md) that generated this schedule (may reference the highest-priority plan when multiple plans are layered)
- Date assignment (schedule_date) - the calendar date for this schedule
- Resolved asset selections - concrete `asset_uuid` entries selected from the plan's [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) entries, possibly derived from [VirtualAssets](VirtualAsset.md) that expand to concrete Asset references during resolution
- Real-world wall-clock times - calculated by anchoring schedule times (from [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) `start_time` offsets) to the channel's `programming_day_start` (also referred to as `broadcast_day_start`) to produce final wall-clock times
- Playback instructions - derived from the assignments in the matching plan (episode policies, playback rules, operator intent)
- Manual override flag (is_manual_override) - indicates if this was manually overridden
- Unique constraint ensuring one schedule per channel per date

Schedule days are the resolved output of the planning process. They are **derived from [SchedulePlan](SchedulePlan.md)** and **materialized 3–4 days in advance**, then **frozen** after generation. They represent "what will actually air" after resolving active layered plans for a given channel and date into concrete schedules with specific `asset_uuid` selections (possibly derived from [VirtualAssets](VirtualAsset.md)), wall-clock times anchored to the channel's `programming_day_start`, and playback instructions derived from [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) entries. Manual overrides are permitted post-generation even after the schedule day has been frozen.

## Execution model

ScheduleService generates BroadcastScheduleDay records **derived from active layered [SchedulePlans](SchedulePlan.md) for a given channel and date**. Schedule days are **materialized 3–4 days in advance** to provide stable schedules for EPG and playout systems. The process:

1. **Plan resolution**: For a given channel and date, identify all applicable active [SchedulePlans](SchedulePlan.md) (based on cron_expression, date ranges, priority). Apply Photoshop-style layering where more specific plans override generic ones.
2. **Assignment resolution**: Retrieve [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) records from the matching plan(s) (content selections and time structure defined directly using `start_time` and `duration`)
3. **Content resolution**: Resolve content references to specific `asset_uuid` entries based on content_type, playback rules, and operator intent from the assignments. If a [VirtualAsset](VirtualAsset.md) is referenced, expand it to one or more concrete Asset UUIDs at this stage.
4. **Time calculation**: Calculate real-world wall-clock times by anchoring schedule times to the channel's `programming_day_start`:
   - Schedule times from [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) are expressed as `start_time` offsets from 00:00 (e.g., "06:00" means 6 hours after programming day start at 00:00)
   - The channel's `programming_day_start` (also referred to as `broadcast_day_start`) defines the wall-clock time when the programming day begins (e.g., 6:00 AM local time = 360 minutes after midnight)
   - Final wall-clock time = `programming_day_start` + schedule time offset
   - Example: If `programming_day_start` is 6:00 AM (360 minutes) and schedule `start_time` is "02:00" (120 minutes), the wall-clock time is 6:00 AM + 2 hours = 8:00 AM
   - This anchoring ensures all schedule times are properly aligned to the channel's programming day boundary
5. **Playback instruction extraction**: Extract playback instructions from the assignments (episode policies, playback rules, operator intent) and include them in the resolved schedule day
6. **Validation**: Ensure assignments are valid and consistent
7. **Schedule generation**: Create BroadcastScheduleDay record with resolved `asset_uuid` entries, wall-clock times, and playback instructions
8. **Freezing**: Once generated, the schedule day is **frozen** (locked and immutable) unless force-regenerated or manually overridden by an operator
9. **Playlog generation**: Generate [BroadcastPlaylogEvent](PlaylogEvent.md) entries from the resolved schedule

**Time Resolution:** Real-world wall-clock times in the schedule day are calculated by anchoring schedule times to the channel's `programming_day_start` (also referred to as `broadcast_day_start`). Schedule times from [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) are expressed as `start_time` offsets from 00:00 (absolute offsets within the programming day). The channel's `programming_day_start` defines when the programming day begins in wall-clock time (e.g., 6:00 AM local time). The resolution process anchors the schedule time offsets to the `programming_day_start` to produce the final wall-clock time. This anchoring ensures that schedule times are properly aligned to the channel's programming day boundary.

**Asset Resolution:** ScheduleDay contains resolved `asset_uuid` entries that reference concrete Asset records. These may be:
- Direct asset references from plan assignments (when `content_type` is "asset")
- Resolved from [VirtualAssets](VirtualAsset.md) that were referenced in plan assignments (when `content_type` is "virtual_package")
- Selected based on rules or series policies from plan assignments

**Playback Instructions:** Resolved ScheduleDay assets include playback instructions derived from the assignments in the matching plan. These instructions include:
- Episode selection policies (for series content)
- Playback rules (chronological, random, seasonal, etc.)
- Operator intent metadata
- Content selection constraints

**Critical Rule:** Once generated, BroadcastScheduleDay is **frozen** (locked and immutable). Schedule days are materialized 3–4 days in advance and remain frozen to ensure the EPG and playout systems have a stable view of "what will air." The only ways to modify a frozen schedule day are:
- **Force regeneration**: Recreate the schedule day from its plan(s) with updated content based on the current plan state
- **Manual override**: Operators can manually override a frozen schedule day post-generation, creating a new BroadcastScheduleDay with `is_manual_override=true`. This breaks the link to the plan but preserves the schedule for that specific date

**Force Regeneration:** Operators can force-regenerate a schedule day from its plan(s), which recreates the schedule day with updated content selections and times based on the current plan state. This is useful after plan updates.

**Manual Overrides (Post-Generation):** Operators can manually override a frozen schedule day post-generation for special events, breaking news, or one-off programming changes. This creates a new BroadcastScheduleDay with `is_manual_override=true`, which breaks the link to the plan but preserves the schedule for that specific date. Manual overrides are permitted even after the schedule day has been frozen.

## Freezing and Playlog Generation

**Schedule Day Freezing:** Once a BroadcastScheduleDay is created (materialized 3–4 days in advance), it is **frozen** (locked and immutable). This freezing ensures:
- EPG systems have a stable reference for "what will air"
- Playout systems can rely on consistent schedule data
- Changes to the source [SchedulePlan](SchedulePlan.md) do not automatically affect already-generated schedule days

The only ways to modify a frozen schedule day are:
- **Force regeneration**: Operators can force-regenerate the schedule day from its plan(s), which recreates it with updated content based on the current plan state
- **Manual override (post-generation)**: Operators can manually override the frozen schedule day post-generation, creating a new BroadcastScheduleDay record with `is_manual_override=true`. Manual overrides are permitted even after the schedule day has been frozen

**PlaylogEvent Generation:** [PlaylogEvents](PlaylogEvent.md) are generated from the resolved BroadcastScheduleDay. The schedule day's resolved asset selections, wall-clock times, and playback instructions are used to create the playout events that drive actual broadcast execution. This generation happens after the schedule day is created and locked, ensuring playout events are based on stable, immutable schedule data.

## Failure / fallback behavior

If schedule assignments are missing or invalid, the system falls back to default programming or the most recent valid schedule.

## Naming rules

The canonical name for this concept in code and documentation is BroadcastScheduleDay.

Schedule days are resolved from plans. They define "what will air when" for a specific channel and date, but do not execute scheduling.

## Operator workflows

**Generate Schedule Days**: ScheduleService automatically generates BroadcastScheduleDay records derived from active layered SchedulePlans for a given channel and date. Schedule days are materialized 3–4 days in advance and frozen after generation. Operators don't manually create schedule days in normal operation.

**Preview Schedule**: Use preview/dry-run features to see how a plan will resolve into a BroadcastScheduleDay before it's generated.

**Manual Override (Post-Generation)**: Manually override a frozen schedule day post-generation for special events, breaking news, or one-off programming changes. This creates a new BroadcastScheduleDay with `is_manual_override=true`. Manual overrides are permitted even after the schedule day has been frozen.

**Force Regenerate Schedule**: Force regeneration of a schedule day from its plan(s) (useful after plan updates). This recreates the schedule day with updated content selections, times, and playback instructions based on the current plan state. The day must be unlocked for regeneration.

**Validate Schedule**: Check resolved schedule days for gaps, rule violations, or content conflicts.

**Multi-Channel Programming**: Different channels can have different plans, resulting in different schedule days for the same date.

**Schedule Inspection**: View resolved schedule days to see "what will air" for a specific channel and date.

## See also

- [Scheduling](Scheduling.md) - High-level scheduling system
- [SchedulePlan](SchedulePlan.md) - Top-level operator-created plans that define channel programming (layered to generate schedule days)
- [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) - Scheduled pieces of content in plans (source of truth for what should air when, from which playback instructions are derived)
- [VirtualAsset](VirtualAsset.md) - Container for multiple assets that expand to concrete Asset UUIDs during ScheduleDay resolution
- [PlaylogEvent](PlaylogEvent.md) - Generated playout events (created from resolved schedule days)
- [Channel](Channel.md) - Channel configuration and timing policy (provides `programming_day_start` / `broadcast_day_start` for time anchoring)
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
