_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md) • [Contracts](../contracts/README.md) • [Channel](Channel.md) • [SchedulePlan](SchedulePlan.md) • [Program](Program.md) • [PlaylogEvent](PlaylogEvent.md)_

# Domain — Schedule day

> **Note:** This document reflects the modern scheduling architecture. Active chain: **SchedulePlan (Zones + Patterns) → ScheduleDay (resolved) → PlaylogEvent (runtime) → AsRunLog.**

## Purpose

BroadcastScheduleDay is a **resolved, immutable daily schedule** for a specific channel and calendar date. **It is derived from [SchedulePlan](SchedulePlan.md) using Zones (time windows) and Patterns (ordered Program lists). If multiple plans are active, priority resolves overlapping Zones.** ScheduleDay is materialized 3–4 days in advance. Once generated, the schedule day is **frozen** (locked and immutable) unless force-regenerated or manually overridden by an operator.

**Primary Expansion Point:** ScheduleDay is the **primary expansion point** for:
- **Programs → concrete episodes**: Programs (catalog entries) in Patterns are expanded to specific episodes based on rotation policy
- **VirtualAssets → real assets**: VirtualAssets referenced in Programs are expanded to concrete Asset UUIDs

The schedule day contains the resolved schedule for a channel on a specific date, with resolved asset selections and real-world wall-clock times. **Wall-clock times are calculated by anchoring Zone time windows and Pattern repeating behavior to the channel's Grid boundaries** (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`). Zones declare when they apply (e.g., base 00:00–24:00, or After Dark 22:00–05:00), and the plan engine repeats Patterns over Zones until Zones are full, snapping to Grid boundaries.

ScheduleDay contains **resolved `asset_uuid` entries** that reference concrete Asset records. These asset UUIDs may be derived directly from Programs, or they may be resolved from [VirtualAssets](VirtualAsset.md) that were referenced in Programs. When a VirtualAsset is referenced in a Program, it expands to one or more concrete Asset UUIDs during ScheduleDay generation.

The EPG references this layer, and [PlaylogEvents](PlaylogEvent.md) are generated from it. This is the execution-time view of "what will air on this channel on this date" after resolving Zones, Patterns, and Programs into concrete content selections.

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

BroadcastScheduleDay is a resolved, immutable daily schedule **derived from [SchedulePlan](SchedulePlan.md) using Zones (time windows) and Patterns (ordered Program lists). If multiple plans are active, priority resolves overlapping Zones.** ScheduleDay is **materialized 3–4 days in advance**. It provides the concrete schedule for a specific channel and calendar date. Once generated, the schedule day is **frozen** (locked and immutable) unless force-regenerated or manually overridden. It contains resolved asset selections with real-world wall-clock times and playback instructions. It defines:

- Channel assignment (channel_id) - the channel this schedule applies to
- Plan reference (plan_id) - the [SchedulePlan](SchedulePlan.md) that generated this schedule (may reference the highest-priority plan when multiple plans are layered)
- Date assignment (schedule_date) - the calendar date for this schedule
- **Primary expansion point**: ScheduleDay is the primary expansion point for Programs → concrete episodes and VirtualAssets → real assets
- Resolved asset selections - concrete `asset_uuid` entries selected from the plan's Zones, Patterns, and Programs, possibly derived from [VirtualAssets](VirtualAsset.md) that expand to concrete Asset references during resolution
- Real-world wall-clock times - calculated by anchoring Zone time windows and Pattern repeating behavior to the channel's Grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`) to produce final wall-clock times
- Playback instructions - derived from the Programs in the matching plan (episode policies, playback rules, operator intent)
- Manual override flag (is_manual_override) - indicates if this was manually overridden
- Unique constraint ensuring one schedule per channel per date

Schedule days are the resolved output of the planning process. They are **derived from [SchedulePlan](SchedulePlan.md) using Zones (time windows) and Patterns (ordered Program lists). If multiple plans are active, priority resolves overlapping Zones.** ScheduleDays are **materialized 3–4 days in advance**, then **frozen** after generation. They represent "what will actually air" after resolving active plans for a given channel and date into concrete schedules with specific `asset_uuid` selections (possibly derived from [VirtualAssets](VirtualAsset.md)), wall-clock times anchored to the channel's Grid boundaries, and playback instructions derived from Programs. **ScheduleDay is the primary expansion point for Programs → episodes and VirtualAssets → assets.** Manual overrides are permitted post-generation even after the schedule day has been frozen.

## Execution model

ScheduleService generates BroadcastScheduleDay records **derived from active [SchedulePlans](SchedulePlan.md) using Zones (time windows) and Patterns (ordered Program lists) for a given channel and date. If multiple plans are active, priority resolves overlapping Zones.** Schedule days are **materialized 3–4 days in advance** to provide stable schedules for EPG and playout systems. The process:

1. **Plan resolution**: For a given channel and date, identify all applicable active [SchedulePlans](SchedulePlan.md) (based on cron_expression, date ranges, priority). Apply priority-based layering where more specific plans override generic ones. Zones from higher-priority plans override overlapping Zones from lower-priority plans.
2. **Zone and Pattern resolution**: Retrieve Zones (time windows) and Patterns (ordered lists of Programs) from the matching plan(s)
3. **Pattern repeating**: The plan engine repeats each Pattern over its Zone until the Zone is full, snapping to the Channel's Grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`)
4. **Primary expansion point**: ScheduleDay is the primary expansion point for:
   - **Programs → concrete episodes**: Programs (catalog entries) in Patterns are expanded to specific episodes based on rotation policy
   - **VirtualAssets → real assets**: VirtualAssets referenced in Programs are expanded to concrete Asset UUIDs
5. **Content resolution**: Resolve content references to specific `asset_uuid` entries based on content_type, playback rules, and operator intent from the Programs. If a [VirtualAsset](VirtualAsset.md) is referenced, expand it to one or more concrete Asset UUIDs at this stage.
6. **Time calculation**: Calculate real-world wall-clock times by anchoring Zone time windows and Pattern repeating behavior to the channel's Grid boundaries:
   - Zones declare when they apply (e.g., base 00:00–24:00, or After Dark 22:00–05:00)
   - The plan engine repeats Patterns over Zones until Zones are full
   - All scheduling snaps to the Channel's Grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`)
   - Final wall-clock times are calculated based on Zone time windows, Pattern repeating, and Grid alignment
7. **Playback instruction extraction**: Extract playback instructions from the Programs (episode policies, playback rules, operator intent) and include them in the resolved schedule day
8. **Validation**: Ensure Zones, Patterns, and Programs are valid and consistent
9. **Schedule generation**: Create BroadcastScheduleDay record with resolved `asset_uuid` entries, wall-clock times, and playback instructions
10. **Freezing**: Once generated, the schedule day is **frozen** (locked and immutable) unless force-regenerated or manually overridden by an operator
11. **Playlog generation**: Generate [BroadcastPlaylogEvent](PlaylogEvent.md) entries from the resolved schedule

**Time Resolution:** Real-world wall-clock times in the schedule day are calculated by anchoring Zone time windows and Pattern repeating behavior to the channel's Grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`). Zones declare when they apply, and the plan engine repeats Patterns over Zones until Zones are full, snapping to Grid boundaries. This ensures all schedule times are properly aligned to the channel's Grid.

**Asset Resolution (Primary Expansion Point):** ScheduleDay is the **primary expansion point** for:
- **Programs → concrete episodes**: Programs (catalog entries) in Patterns are expanded to specific episodes based on rotation policy
- **VirtualAssets → real assets**: VirtualAssets referenced in Programs are expanded to concrete Asset UUIDs

ScheduleDay contains resolved `asset_uuid` entries that reference concrete Asset records. These may be:
- Direct asset references from Programs (when `content_type` is "asset")
- Resolved from [VirtualAssets](VirtualAsset.md) that were referenced in Programs (when `content_type` is "virtual_package")
- Selected based on rules or series policies from Programs (episodes resolved at ScheduleDay time)

## Resolution Semantics for Zones + Patterns

ScheduleDay generation resolves Zones and Patterns into concrete asset selections with precise timing. The resolution process follows these semantics:

### Zone and Pattern Expansion

**For each Zone, expand its Pattern across the Zone's window, snapping to the Channel grid:**

1. **Zone identification**: Identify all active Zones from SchedulePlans for the channel and date. If multiple plans are active, priority resolves overlapping Zones.
2. **Pattern retrieval**: For each Zone, retrieve its associated Pattern (ordered list of Program references)
3. **Pattern repeating**: Repeat the Pattern across the Zone's active window, snapping to the Channel's Grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`)
4. **Grid alignment**: All content placement snaps to valid grid boundaries; no fractional-minute scheduling

### Program Reference Resolution

**Each Program reference in the pattern resolves to concrete assets:**

- **Series → episode(s)**: Series Programs resolve to specific episodes based on rotation policy (sequential, random, LRU, seasonal, etc.). The selected episode's duration determines block consumption.
- **Movie → one or more grid blocks**: Movie/asset Programs resolve to the referenced asset. If the asset is longform and has a `slot_units` override, it consumes the specified number of grid blocks. Otherwise, the asset's duration determines block consumption.
- **Composite → VirtualAsset expansion**: Programs referencing VirtualAssets expand to multiple concrete assets (e.g., "intro + episode + outro" becomes three separate assets in sequence). Each asset in the expansion is resolved individually.

### Block Consumption and Avails

**Underfill inside a block becomes avails; overlength consumes additional blocks if allowed:**

- **Underfill**: If content runtime is shorter than the allocated grid block(s), the remaining time becomes an **avail** (gap that can be filled with commercials or filler content)
- **Overlength**: If content runtime exceeds the allocated grid block(s), it consumes additional blocks if:
  - The Program has a `slot_units` override that allows the expansion, or
  - The series pick (for series Programs) naturally requires multiple blocks
- **No mid-longform cuts**: Longform content (with `slot_units` override) is **never cut mid-play**. It always consumes the full number of blocks specified by `slot_units` or required by its duration.

### Soft-Start and Carry-In

**Soft-start & carry-in policies handle Zone transitions and day boundaries:**

- **Soft-start-after-current**: If a Zone opens while content is already playing (in-flight content from a previous Zone), the current program continues to completion. The new Zone's Pattern begins at the **next valid Grid boundary** after the current program ends. This prevents mid-program interruptions.
- **Carry-in across broadcast day seams**: If content crosses the programming-day seam (e.g., a program starting at 23:30 continues past midnight), Day+1 starts with a **carry-in** until the content completes. The carry-in content is part of Day+1's schedule but originated from Day's plan resolution.

**Example:**
- Zone A: 19:00–22:00 with Pattern [Series A, Series B]
- Zone B: 20:00–22:00 with Pattern [Movie Block]
- If Series A is still playing at 20:00 when Zone B opens, Series A continues to completion, and Zone B's Movie Block starts at the next grid boundary after Series A ends.

**Cross-Day Carryover Example:**

If a movie starts at 5:00 AM and ends at 7:00 AM, it belongs to the 5:00–6:00 portion of the prior day's plan, but will carry into the next broadcast day's runtime log seamlessly.

**Timeline (assuming `programming_day_start=06:00`):**

```
Broadcast Day 1 (Jan 15)          Broadcast Day 2 (Jan 16)
06:00 ──────────────────────────── 06:00 ────────────────────────────
                                    │
                                    │ programming_day_start
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │ Movie starts at 05:00       │
                    │ (Day 1's plan, Zone 05:00-06:00)
                    │                             │
                    │ Movie continues...          │
                    │                             │
                    │ Movie ends at 07:00         │
                    │ (carries into Day 2)        │
                    └─────────────────────────────┘
                                    │
                                    │ Day 2's first Zone
                                    │ starts at 07:00
                                    │ (next grid boundary)
                                    ▼
```

**Key Points:**
- The movie (05:00–07:00) is scheduled by **Day 1's plan** (Zone covering 05:00–06:00)
- The movie **carries into Day 2's runtime** seamlessly, ending at 07:00
- Day 2's first Zone starts at the next grid boundary after the carry-in completes (07:00)
- The carry-in content appears in **Day 2's ScheduleDay** and runtime log, but originated from **Day 1's plan resolution**
- This ensures seamless transitions across broadcast day boundaries without content interruption

### Immutability and EPG Truthfulness

ScheduleDay maintains these critical properties:

- **Resolved & immutable**: Once generated, ScheduleDay is **frozen** (locked and immutable) unless force-regenerated or manually overridden. Schedule days are materialized **3–4 days in advance** to provide stable schedules.
- **EPG truthfulness**: The EPG references ScheduleDay as the source of truth for "what will air when." ScheduleDay's resolved asset selections and wall-clock times are authoritative for EPG generation.
- **Playlog generation from ScheduleDay**: [PlaylogEvents](PlaylogEvent.md) are generated from the resolved ScheduleDay. The schedule day's resolved asset selections, wall-clock times, and playback instructions are used to create the playout events that drive actual broadcast execution.

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

**Generate Schedule Days**: ScheduleService automatically generates BroadcastScheduleDay records derived from active SchedulePlans using Zones (time windows) and Patterns (ordered Program lists) for a given channel and date. If multiple plans are active, priority resolves overlapping Zones. Schedule days are materialized 3–4 days in advance and frozen after generation. Operators don't manually create schedule days in normal operation.

**Preview Schedule**: Use preview/dry-run features to see how a plan will resolve into a BroadcastScheduleDay before it's generated.

**Manual Override (Post-Generation)**: Manually override a frozen schedule day post-generation for special events, breaking news, or one-off programming changes. This creates a new BroadcastScheduleDay with `is_manual_override=true`. Manual overrides are permitted even after the schedule day has been frozen.

**Force Regenerate Schedule**: Force regeneration of a schedule day from its plan(s) (useful after plan updates). This recreates the schedule day with updated content selections, times, and playback instructions based on the current plan state. The day must be unlocked for regeneration.

**Validate Schedule**: Check resolved schedule days for gaps, rule violations, or content conflicts.

**Multi-Channel Programming**: Different channels can have different plans, resulting in different schedule days for the same date.

**Schedule Inspection**: View resolved schedule days to see "what will air" for a specific channel and date.

## Invocation

**CLI:**

```bash
retrovue schedule plan preview --channel <id> --date YYYY-MM-DD
retrovue schedule day build --channel <id> --date YYYY-MM-DD
```

**Programmatic:**

```python
from retrovue.scheduling import preview_schedule, build_schedule_day
```

## See also

- [Scheduling](Scheduling.md) - High-level scheduling system
- [SchedulePlan](SchedulePlan.md) - Top-level operator-created plans that define channel programming using Zones and Patterns (layered to generate schedule days)
- [Program](Program.md) - Catalog entries in Patterns (expanded to concrete episodes at ScheduleDay time)
- [VirtualAsset](VirtualAsset.md) - Container for multiple assets that expand to concrete Asset UUIDs during ScheduleDay resolution (primary expansion point)
- [PlaylogEvent](PlaylogEvent.md) - Generated playout events (created from resolved schedule days)
- [Channel](Channel.md) - Channel configuration and timing policy (owns Grid: `grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`)
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
