_Related: [Architecture overview](ArchitectureOverview.md) • [Domain: Scheduling](../domain/Scheduling.md) • [Runtime: Channel manager](../runtime/ChannelManager.md) • [Runtime: MasterClock](../domain/MasterClock.md)_

# Scheduling system architecture

> **Note:** This document reflects the modern scheduling architecture.  
> The active scheduling chain is: **SchedulePlan → ScheduleDay → PlaylogEvent → AsRunLog.**

## Purpose

The scheduling system defines what content airs on each Channel and when. It operates across multiple layers from high-level plans to granular playout execution. The system extends the plan horizon ahead of time, ensuring all viewers see synchronized playback regardless of join time.

## Five-layer architecture

The scheduling system follows a strict separation of concerns across five layers:

**SchedulePlan → ScheduleDay → EPG → Playlog → As-Run Log**

Each layer has distinct responsibilities:

| Layer          | Responsibility                                                                  | Ownership                | When Generated                    |
| -------------- | ------------------------------------------------------------------------------- | ------------------------ | --------------------------------- |
| **SchedulePlan** | Top-level operator-created plans defining 24-hour timeline with block assignments | Operators create via CLI | Once, reused across days          |
| **ScheduleDay** | Resolved, immutable daily schedule for specific channel and date                 | ScheduleService (daemon)  | 3–4 days in advance               |
| **EPG**        | Coarse viewer-facing program guide (program-level information)                  | EPG generator            | Days ahead, updated periodically  |
| **Playlog**    | Fine-grained playout plan with specific assets, ads, and timestamps             | ScheduleService          | Rolling horizon (3-4 hours ahead) |
| **As-Run Log** | Factual record of what actually aired                                           | AsRunLogger              | Real-time as playback occurs      |

**Critical principle**: Each layer builds on the previous one. SchedulePlan defines structure, ScheduleDay instantiates it, EPG presents it to viewers, Playlog executes it, and As-Run Log records it.

## Core scheduling layers

The scheduling system consists of five interconnected layers:

### 1. SchedulePlan

Top-level operator-created plans that define channel programming. Each SchedulePlan represents a complete 24-hour timeline (00:00 to 24:00 relative to the channel's `programming_day_start` / `broadcast_day_start` anchor) with sequential block assignments.

- Plans are channel-specific and can be applied to multiple days via cron expressions or date ranges
- Each plan contains [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) entries that directly define what content runs when using `start_time` (schedule-time offset from 00:00) and `duration` (minutes)
- Plans can reference assets, series, rules, or [VirtualAssets](VirtualAsset.md) (reusable containers that encapsulate structured content sequences)
- Plans support layering with priority resolution (higher priority plans override lower priority plans)
- [ContentPolicyRule](ContentPolicyRule.md) can be used to validate assignment compatibility (future feature)

### 2. ScheduleDay

Resolved, immutable daily schedule derived from SchedulePlans. SchedulingService uses the channel's programming day anchor to generate ScheduleDay rows 3–4 days in advance.

- Generated from active, layered SchedulePlans for a specific channel and date
- Contains resolved asset selections with real-world wall-clock times
- Times are calculated by anchoring schedule-time offsets to the channel's `programming_day_start`
- Immutable once generated (frozen) unless force-regenerated or manually overridden
- VirtualAssets expand to concrete Asset UUIDs during ScheduleDay generation
- Maintains the relationship between plan assignments and resolved content

### 3. EPG (Electronic Program Guide)

Derived from ScheduleDay. Public-facing grid that shows what's scheduled to air. The EPG provides a coarse view of programming for viewers and operators.

- Generated from ScheduleDay state and playlog events
- Shows program-level information (e.g., "Cheers 9:00 PM - 9:30 PM")
- Can extend 2–3 days ahead for viewer reference
- Does not reflect last-minute playlog changes until they occur
- Safe to generate ahead of time since ScheduleDays are frozen 3–4 days in advance

### 4. Playlog

Built from ScheduleDay. Contains the resolved list of media segments to be played, with real video assets, commercials, and bumpers in exact playout order with precise timestamps. The playlog is the fine-grained execution plan that ChannelManager uses for actual playout.

- Contains specific asset references with exact file paths
- Each entry maps to a ScheduleDay and points to a resolved asset or asset segment (for VirtualAssets)
- Includes ad breaks, bumpers, and interstitials in correct sequence
- Uses precise timestamps aligned to the master clock
- Generated using a rolling horizon (see Playlog mechanics below)
- Supports fallback mechanisms and last-minute overrides
- Asset-level and file-specific, unlike ScheduleDay which contains resolved asset selections

### 5. As-Run Log

Tracks what actually aired by recording each segment as it starts playback. This is the factual record of broadcast execution.

- Records every asset as it begins playback
- Includes actual start times from the master clock
- Captures what was attempted vs. what actually aired
- Used for historical accuracy, audits, and reporting
- Independent of the playlog (which is the plan, not the execution)

## SchedulePlan layering and priority

The scheduling system supports plan layering (Photoshop-style priority resolution) to minimize plan duplication. Instead of creating separate plans for every day, operators can create base plans that cover most of the year, with higher-priority plans for seasons, holidays, or special events.

### Plan priority resolution

When multiple SchedulePlans match for a channel and date, the system uses priority resolution (highest priority wins):

1. **Plan matching**: ScheduleService identifies all active SchedulePlans that match the channel and date based on:
   - `cron_expression` (e.g., "0 6 * * MON-FRI" for weekdays)
   - `start_date` / `end_date` date ranges
   - `is_active=true` status

2. **Priority resolution**: Among matching plans, the plan with the highest `priority` value is selected
   - Higher priority plans override lower priority plans
   - More specific plans (e.g., holidays) should have higher priority than general plans (e.g., weekdays)

3. **Assignment layering**: Block assignments from the selected plan are used to generate the ScheduleDay
   - If multiple plans match but have different priorities, only the highest priority plan's assignments are used
   - Lower priority plans are completely superseded, not merged

### Plan attributes for layering

SchedulePlans support the following attributes for matching and layering:

- **`cron_expression`** (text): Cron-style expression defining when the plan is active (e.g., "0 6 * * MON-FRI")
- **`start_date` / `end_date`** (date): Date range when the plan is valid (can be year-agnostic)
- **`priority`** (integer): Priority level for layering (higher = more specific, overrides lower priority)
- **`is_active`** (boolean): Whether the plan is active and eligible for use

### Example layering

Here's a practical example of how plan layering works:

**Base Plan: "WeekdayPlan"**

- `cron_expression`: "0 6 * * MON-FRI" (weekdays 6am)
- `priority`: 10
- `start_date`: null, `end_date`: null
- Covers: Monday–Friday year-round

**Seasonal Plan: "SummerWeekdayPlan"**

- `cron_expression`: "0 6 * * MON-FRI" (weekdays 6am)
- `priority`: 20
- `start_date`: "2025-06-01", `end_date`: "2025-09-30"
- Covers: Monday–Friday from June–September (overrides WeekdayPlan for this period)

**Holiday Plan: "ChristmasPlan"**

- `cron_expression`: null
- `priority`: 30
- `start_date`: "2025-12-25", `end_date`: "2025-12-25"
- Covers: December 25 only (overrides both WeekdayPlan and SummerWeekdayPlan)

### Plan resolution algorithm

When ScheduleService needs to determine which plan applies to a date:

1. **Identify matching plans**: Query active SchedulePlans for the channel that match the date based on cron_expression and date ranges
2. **Apply priority resolution**: Select the plan with the highest `priority` value among matching plans
3. **Generate ScheduleDay**: Use the selected plan's block assignments to generate the ScheduleDay

### Benefits of plan layering

- **Reduced duplication**: One base plan covers most of the year
- **Easy overrides**: Special schedules for holidays or seasons without recreating entire plans
- **Flexible patterns**: Cron expressions and date ranges handle complex recurring patterns
- **Maintainability**: Changes to base plans automatically apply except where overridden by higher priority plans

## Grid blocks and dayparts

### Grid block

The smallest schedulable unit. Typically 30-minute grid blocks, though the duration is configurable per channel via `grid_block_minutes`.

- Grid blocks are atomic scheduling units
- Can contain series episodes, movies, or generic content types
- Duration must align with channel's grid block configuration
- Metadata like `commType` (e.g., "cartoon") or `introBumper` can be attached

### Daypart (Visual Organization)

A named block of time used for visual organization. Dayparts can be represented as Zones within SchedulePlans for operator convenience.

- Examples: "Morning Block" (6–9 AM), "Prime Time" (7–11 PM)
- Dayparts are represented as Zones within SchedulePlans
- Content selection is defined directly in Patterns within Zones, not through separate daypart rules

## Playlog mechanics

### Rolling horizon

The full day's playlog is not generated at midnight. Instead, the system uses a rolling horizon approach:

- Only 3–4 hours of playlog are created at a time
- The playlog horizon continuously extends ahead of the current time
- This avoids long gaps and unnecessary prep for grid blocks no one is watching
- Reduces computational overhead while maintaining sufficient lookahead

### Content composition

During playlog generation:

- Content is stitched together in exact order
- Ad breaks are inserted at designated avails
- Bumpers and interstitials are placed between segments
- Transitions between content items are specified
- All timing aligns with the master clock

### Asset eligibility

The playlog builder only considers assets where `state == 'ready'` and `approved_for_broadcast == true`. Assets in `new`, `enriching`, or `retired` states are never included in playlog generation.

### Skippability and underfills

When no eligible asset is found for a grid block:

- **Skippable segments**: If a segment cannot be filled and skipping is allowed, the playlog builder creates a gap event or moves to the next segment
- **Underfill handling**: If a grid block is partially filled (e.g., 20 minutes of content in a 30-minute slot), the system may:
  - Insert a fallback playlog event (e.g., holding pattern, bumper, or error screen)
  - Extend adjacent content if rules permit
  - Leave the gap and notify operators
- **Operator notification**: All skips, gaps, and underfills are logged and surfaced to operators for review
- **Fallback events**: The playlog includes explicit fallback events with type indicators (e.g., `event_type: "gap"` or `event_type: "fallback"`) so ChannelManager knows how to handle them

## Viewer join behavior

When a viewer joins a stream:

- The system starts generating the playlog from the beginning of the current grid block, not the viewer's join time
- This ensures everyone joins midstream at the same time offset as real-time viewers
- Prevents edge cases where someone joins 3 minutes into an episode and sees the wrong point
- All viewers see synchronized playback aligned to the master clock

### Real-time lifecycle example

Here's a concrete example of how the system handles a viewer join:

**8:55 PM** - System extends playlog horizon:

- ScheduleService checks master clock: `now_utc = 2025-11-04T20:55:00Z`
- Current playlog horizon ends at 11:00 PM
- Extends playlog to cover 9:00 PM - 12:00 AM
- Generates BroadcastPlaylogEvent for "Cheers S2E5" starting at 9:00 PM

**9:00 PM** - Program starts:

- ChannelManager reads playlog event for 9:00 PM
- Locates asset: `asset_uuid = "cheers_s2e5_uuid"`
- Verifies asset state: `state='ready'`, `approved_for_broadcast=true`
- Starts playback at file offset `00:00:00`
- AsRunLogger records: `{timestamp: "2025-11-04T21:00:00Z", asset: "cheers_s2e5", event_type: "program"}`

**9:03 PM** - Viewer joins:

- New viewer connects to Channel 1
- ChannelManager identifies current grid block (9:00 PM - 9:30 PM)
- Finds playlog event: "Cheers S2E5" starting at 9:00 PM
- Calculates offset: `master_clock.now_utc() - playlog_event.start_utc = 180 seconds`
- Starts viewer playback at file offset `00:03:00` in `cheers_s2e5.mp4`
- Viewer sees synchronized content with all other viewers

**9:30 PM** - Program ends:

- AsRunLogger records program completion
- ChannelManager transitions to next playlog event (e.g., commercial break)
- All viewers see the same transition at the same time

This ensures perfect synchronization regardless of join time.

## Master clock synchronization

The master clock dictates when each asset should start. Every segment in the playlog aligns with the clock to prevent drift.

### Component responsibilities

Synchronization logic is distributed across components with clear ownership:

| Component           | Responsibility                              | Sync Role                                                         |
| ------------------- | ------------------------------------------- | ----------------------------------------------------------------- |
| **MasterClock**     | Provides current time + timestamp authority | Single source of truth for "now"                                  |
| **ScheduleService** | Extends playlog horizon aligned to clock    | Generates playlog events with `start_utc` from master clock       |
| **ChannelManager**  | Executes playback, syncs viewer joins       | Calculates playback offset using master clock, aligns all viewers |
| **AsRunLogger**     | Logs playback events with clock time        | Records actual start times from master clock                      |

**Critical rule**: All timing decisions must use MasterClock. Direct calls to `datetime.now()` or `datetime.utcnow()` are not allowed in runtime code.

### Clock alignment

- Every playlog event has a precise `start_utc` timestamp from the master clock
- When generating playout for a viewer, ChannelManager:
  1. Queries master clock for current time
  2. Locates the current grid block using master clock time
  3. Finds the correct time offset within the segment: `offset = master_clock.now_utc() - playlog_event.start_utc`
  4. Starts playback exactly from that point in the asset file
- Prevents "drifting ahead" due to faster encoding or random delays
- Ensures all viewers see the same content at the same absolute time

### Sync checkpoints

The system may use sync checkpoints to allow newly joined viewers to align to the current master clock offset quickly. These checkpoints help minimize join latency while maintaining perfect synchronization.

## BroadcastPlaylogEvent structure

The playlog is composed of BroadcastPlaylogEvent records. Each event represents a single playout segment with precise timing and asset references.

### Event structure

```json
{
  "id": 12345,
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "channel_id": 1,
  "asset_uuid": "cheers_s2e5_uuid",
  "start_utc": "2025-11-04T21:00:00Z",
  "end_utc": "2025-11-04T21:23:00Z",
  "broadcast_day": "2025-11-04",
  "event_type": "program",
  "duration_seconds": 1380,
  "playout_path": "/mnt/media/cheers/season2/cheers_s2e5.mp4",
  "created_at": "2025-11-04T20:55:00Z"
}
```

### Event types

- **`program`**: Regular content (episodes, movies)
- **`commercial`**: Ad break segment
- **`bumper`**: Transition bumper or station ID
- **`interstitial`**: Short filler content
- **`gap`**: Skipped or unfilled slot (fallback)
- **`fallback`**: Error screen or holding pattern

### Event lifecycle

1. **Generation**: ScheduleService creates BroadcastPlaylogEvent during horizon extension
2. **Storage**: Events persisted in database with indexes on `channel_id`, `start_utc`, `broadcast_day`
3. **Retrieval**: ChannelManager queries events by channel and time range
4. **Execution**: ChannelManager uses events to build playout plans
5. **Recording**: AsRunLogger records when events actually start playback

## As-run log

Every time an asset begins playback, it's recorded in the as-run log. This log reflects actual playout execution, not the plan.

### What gets logged

- Time the segment started (from master clock)
- What asset actually aired
- Channel identifier
- Reference to the originating BroadcastPlaylogEvent
- Any fallback conditions (e.g., emergency slate instead of intended content)
- Any enrichers applied during playout

### Use cases

- Historical accuracy: What actually aired on a given date/time
- Audits and compliance: Proof of what content was broadcast
- Reporting: Analytics on actual vs. planned programming
- Troubleshooting: Understanding discrepancies between playlog and actual airing

## Design principles

### Plan minimalism

- Keep plans minimal but reusable
- Apply them to multiple days via cron expressions or date ranges
- Plans define structure and content placement directly via block assignments

### Layer separation

- **SchedulePlan and ScheduleDay**: High-level representations defining what content should air when
- **EPG**: Coarse viewer-facing representation derived from ScheduleDay
- **Playlog**: Asset-level and file-specific, includes ads, bumpers, episode files (resolved list of media segments)
- **As-run log**: Factual record of what really aired and when

### Content selection timing

- Content selection is defined in SchedulePlanBlockAssignment entries (assets, series, rules, or VirtualAssets)
- ScheduleDays are generated 3–4 days in advance with resolved asset selections
- VirtualAssets expand to concrete Asset UUIDs during ScheduleDay generation
- PlaylogEvents are generated from ScheduleDays with already-resolved asset references

### Rolling generation

- EPG can be generated days ahead (coarse view)
- Playlog is generated hours ahead (fine-grained view)
- As-run log is generated in real time (actual execution)

## Failure / fallback behavior

The system handles failures at each layer with specific fallback strategies:

### Failure flow diagram

```
[Playlog Generation Fails]
    ↓
[Use Most Recent Successful Schedule] → [Notify Operators]
    ↓
[Generate Fallback Playlog Events] → [Continue Playout]

[Playlog Gap Detected]
    ↓
[Check for On-Demand Generation] → [Generate Playlog] → [Continue Playout]
    ↓ (if generation fails)
[Insert Fallback Event] → [Error Screen or Holding Pattern] → [Notify Operators]

[Master Clock Unavailable]
    ↓
[Critical Error Detected]
    ↓
[Stop All Playout] → [Critical Alert to Operators] → [System Degraded Mode]
```

### Scheduling failures

- If playlog generation fails, the system falls back to the most recent successful schedule
- Missing playlog events trigger default programming or error handling
- Operators are notified of scheduling failures via alerts

### Playlog gaps

When the playlog horizon is not ready when needed:

1. **Detection**: ChannelManager detects missing playlog events for current time
2. **On-demand generation**: Attempts to generate playlog on-demand (with potential latency)
3. **Fallback events**: If generation fails, inserts fallback playlog event:
   - Event type: `fallback`
   - Content: Error screen or holding pattern
   - Duration: Until next available playlog event
4. **Operator notification**: All gaps and fallbacks are logged and surfaced to operators

### Asset availability failures

When no eligible asset is found:

1. **Skip logic**: If segment is skippable, creates gap event and moves to next segment
2. **Underfill handling**: If partial fill, creates fallback event for remaining time
3. **Fallback content**: Uses configured fallback content (e.g., station ID, holding pattern)
4. **Operator alert**: Notifies operators of missing content for review

### Master clock issues

- If master clock is unavailable, downstream services cannot safely determine "what is on right now"
- This condition is considered critical and triggers:
  - All playout stops
  - Critical alert to operators
  - System enters degraded mode
- All scheduling decisions depend on authoritative time from the master clock
- No graceful degradation is possible without master clock

### Recovery procedures

After failures:

1. **Scheduling recovery**: ScheduleService retries playlog generation
2. **Gap recovery**: ChannelManager periodically checks for newly available playlog events
3. **Clock recovery**: System waits for master clock restoration before resuming playout
4. **Operator intervention**: Manual override commands available for critical situations

## Proof of concept strategy

Early-stage testing can use simplified configurations:

- Single plan applied to multiple days via cron expression or date range
- Populate each daypart with fixed content (e.g., "Cheers" or "Big Bang Theory")
- Validate the system end-to-end with minimal complexity
- Gaps (like unused avails) can be left empty or filled with placeholders
- EPG reflects this schedule and is safe to generate ahead of time
- Playlog horizon allows flexible real-time generation without performance issues

## Future concepts

### Preemption logic

The system may support preemption and rebalancing content mid-day (e.g., during breaking news). This would require:

- Dynamic playlog updates during active broadcast
- Content substitution rules
- EPG updates to reflect changes

### Guide data extension

Guide data should extend ahead 2–3 days but may not reflect last-minute playlog changes. The EPG represents the plan, not the exact execution.

### Fallback playout

If the playlog isn't ready when a viewer joins, the system may:

- Display an error screen or holding pattern
- Stall until playlog is available
- Use a default fallback playlist

### Sync checkpoint optimization

Sync checkpoints can allow newly joined viewers to align to the current master clock offset quickly, reducing join latency while maintaining perfect synchronization.

## Execution model

### Schedule service

ScheduleService is a background daemon that orchestrates scheduling:

1. **Plan resolution**: Determines which SchedulePlan applies to a channel and date:
   - Identifies active SchedulePlans matching the channel and date (based on cron_expression, date ranges)
   - Applies priority resolution (highest priority plan wins)
   - Uses the channel's programming day anchor (`programming_day_start` / `broadcast_day_start`) for time anchoring
2. **ScheduleDay generation**: Extends the plan horizon by generating ScheduleDay rows 3–4 days in advance:
   - Retrieves block assignments from the selected plan
   - Resolves VirtualAssets to concrete Asset UUIDs
   - Resolves content references (assets, series, rules) to specific assets
   - Anchors schedule-time offsets to programming day start to produce wall-clock times
   - Creates frozen, immutable ScheduleDay records
3. **PlaylogEvent generation**: Builds runtime playlog by generating PlaylogEvents from ScheduleDays:
   - Each PlaylogEvent maps to a ScheduleDay and points to a resolved asset or asset segment
   - Creates precise timestamps for playout execution
   - Supports fallback mechanisms and last-minute overrides
4. **Content eligibility**: Queries assets for eligible content (`state='ready'` and `approved_for_broadcast=true`)
5. **Horizon management**: Extends the plan horizon and builds the runtime playlog as needed (rolling 3–4 hours ahead)
6. **Timing**: Uses master clock for all timing decisions

### Program director

ProgramDirector coordinates multiple channels and may:

- Reference channel configurations
- Coordinate cross-channel programming
- Apply content conflict resolution rules
- Manage system-wide scheduling state

### Channel manager

ChannelManager executes playout but does not modify scheduling domain models. It:

- Reads playlog events for playout instructions
- References channel configuration
- Uses asset file paths for content playback
- Aligns playback to master clock timestamps

## Naming rules

- **SchedulePlan**: Top-level operator-created plan defining 24-hour timeline with block assignments
- **ScheduleDay**: Resolved, immutable daily schedule for specific channel and date (generated 3–4 days in advance)
- **EPG**: Electronic Program Guide (coarse viewer-facing schedule)
- **Playlog**: Resolved list of media segments to be played (fine-grained playout plan)
- **As-run log**: Record of what actually aired
- **Grid block**: Smallest schedulable time unit (aligned with channel grid)
- **Daypart**: Named block of time represented as a Zone within a SchedulePlan

## See also

- [Domain: Scheduling](../domain/Scheduling.md) - Core scheduling domain models
- [Domain: SchedulePlan](../domain/SchedulePlan.md) - Plan structure and scheduling logic
- [Domain: PlaylogEvent](../domain/PlaylogEvent.md) - Playlog event records
- [Domain: EPGGeneration](../domain/EPGGeneration.md) - EPG generation logic
- [Domain: MasterClock](../domain/MasterClock.md) - Time authority
- [Runtime: ChannelManager](../runtime/ChannelManager.md) - Playout execution
- [Runtime: ScheduleService](../runtime/schedule_service.md) - Scheduling service
- [Runtime: AsRunLogging](../runtime/AsRunLogging.md) - As-run log implementation
