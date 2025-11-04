_Related: [Architecture overview](ArchitectureOverview.md) • [Domain: Scheduling](../domain/Scheduling.md) • [Runtime: Channel manager](../runtime/ChannelManager.md) • [Runtime: MasterClock](../domain/MasterClock.md)_

# Scheduling system architecture

## Purpose

The scheduling system defines what content airs on each Channel and when. It operates across multiple layers from high-level templates to granular playout execution. The system maintains a rolling horizon of scheduled content that advances with the master clock, ensuring all viewers see synchronized playback regardless of join time.

## Five-layer architecture

The scheduling system follows a strict separation of concerns across five layers:

**Template → Schedule → EPG → Playlog → As-Run Log**

Each layer has distinct responsibilities:

| Layer          | Responsibility                                                                  | Ownership                | When Generated                    |
| -------------- | ------------------------------------------------------------------------------- | ------------------------ | --------------------------------- |
| **Template**   | Reusable programming structure with dayparts and content selection rules        | Operators create via CLI | Once, reused across days          |
| **Schedule**   | Template instantiation for a specific broadcast day with resolved content types | ScheduleService          | Daily, ahead of broadcast         |
| **EPG**        | Coarse viewer-facing program guide (program-level information)                  | EPG generator            | Days ahead, updated periodically  |
| **Playlog**    | Fine-grained playout plan with specific assets, ads, and timestamps             | ScheduleService          | Rolling horizon (3-4 hours ahead) |
| **As-Run Log** | Factual record of what actually aired                                           | AsRunLogger              | Real-time as playback occurs      |

**Critical principle**: Each layer builds on the previous one. The Template defines structure, Schedule instantiates it, EPG presents it to viewers, Playlog executes it, and As-Run Log records it.

## Core scheduling layers

The scheduling system consists of five interconnected layers:

### 1. Template

A reusable structure that defines dayparts (e.g., 6–9 AM = "Morning Block") with time slots but no specific content assignments. Templates define the programming structure and content selection rules without binding to actual episodes or assets.

- Templates are channel-specific and can be applied to multiple days
- Each template contains daypart definitions and block slots
- Templates include content selection rules (e.g., "cartoons", "series episodes", "movies")
- Metadata like `commType` or `introBumper` can be attached to blocks for downstream logic
- Templates support hierarchical override patterns to minimize duplication (see Template hierarchy below)

### 2. Schedule

Instantiated from a template. Assigns specific programs, content types, or series to each slot for a particular broadcast day. The schedule binds templates to specific dates and resolves content selection rules into actual programming decisions.

- Created from a template applied to a specific broadcast date
- Contains the resolved content assignments for each time slot
- May reference series, movies, or generic content categories
- Maintains the relationship between template structure and actual content

### 3. EPG (Electronic Program Guide)

Derived from the schedule. Public-facing grid that shows what's scheduled to air. The EPG provides a coarse view of programming for viewers and operators.

- Generated from schedule state and playlog events
- Shows program-level information (e.g., "Cheers 9:00 PM - 9:30 PM")
- Can extend 2–3 days ahead for viewer reference
- Does not reflect last-minute playlog changes until they occur
- Safe to generate ahead of time since templates are relatively static

### 4. Playlog

Built from the schedule. Contains real video assets, commercials, and bumpers in exact playout order with precise timestamps. The playlog is the fine-grained execution plan that ChannelManager uses for actual playout.

- Contains specific asset references with exact file paths
- Includes ad breaks, bumpers, and interstitials in correct sequence
- Uses precise timestamps aligned to the master clock
- Generated using a rolling horizon (see Playlog mechanics below)
- Asset-level and file-specific, unlike the schedule which is content-agnostic

### 5. As-Run Log

Tracks what actually aired by recording each segment as it starts playback. This is the factual record of broadcast execution.

- Records every asset as it begins playback
- Includes actual start times from the master clock
- Captures what was attempted vs. what actually aired
- Used for historical accuracy, audits, and reporting
- Independent of the playlog (which is the plan, not the execution)

## Template hierarchy and overrides

The scheduling system supports hierarchical template overrides to minimize template duplication. Instead of creating separate templates for every day, operators can create base templates that cover most of the year, with override templates for seasons, holidays, or special events.

### Override precedence

When resolving which template applies to a specific date, the system uses the following precedence (most specific wins):

1. **Explicit schedule day assignment** (highest priority)

   - A BroadcastScheduleDay record that explicitly assigns a template to a specific date
   - Example: `schedule_date = "2025-12-25"` with `template_id = christmas_day_template`

2. **Date range templates with day-of-week filters**

   - Templates with `starts_on`/`ends_on` date ranges and optional day-of-week filters
   - Example: Monday–Friday from June–September, Monday–Friday from September–June

3. **Date range templates**

   - Templates with `starts_on`/`ends_on` date ranges (no day-of-week filter)
   - Example: Christmas season (December 1–25)

4. **Base template** (lowest priority)
   - Template with no date restrictions, or the widest date range
   - Falls back to default if no other template matches

### Template attributes for hierarchy

Templates support the following attributes for hierarchical matching:

- **`starts_on` / `ends_on`** (date): Date range when template is active
- **`day_of_week_filter`** (array of integers): Optional filter for specific days of week (0=Monday, 6=Sunday)
- **`override_priority`** (integer): Explicit priority level (higher = more specific, overrides lower priority)
- **`is_base_template`** (boolean): Marks template as base fallback when no other matches

### Example hierarchy

Here's a practical example of how template hierarchy works:

**Base Template: "Weekday Standard"**

- `starts_on`: null (always active as fallback)
- `ends_on`: null
- `day_of_week_filter`: [0, 1, 2, 3, 4] (Monday–Friday)
- Covers: Monday–Friday year-round

**Seasonal Template: "Summer Weekdays"**

- `starts_on`: "2025-06-01"
- `ends_on`: "2025-09-30"
- `day_of_week_filter`: [0, 1, 2, 3, 4] (Monday–Friday)
- Covers: Monday–Friday from June–September (overrides base for this period)

**Holiday Template: "Christmas Season"**

- `starts_on`: "2025-12-01"
- `ends_on`: "2025-12-25"
- `day_of_week_filter`: null (all days)
- Covers: All days from December 1–25 (overrides both base and seasonal)

**Special Day Template: "Christmas Day"**

- Explicit BroadcastScheduleDay assignment: `schedule_date = "2025-12-25"`
- Covers: Only December 25 (highest priority, overrides all others)

### Template resolution algorithm

When ScheduleService needs to determine which template applies to a date:

1. **Check explicit assignments**: Query BroadcastScheduleDay for `(channel_id, schedule_date)` match
2. **If no explicit match**: Query templates matching date range and day-of-week
3. **Sort by specificity**:
   - Explicit assignment > Date range with day filter > Date range only > Base template
   - Within same type, higher `override_priority` wins
4. **Apply fallback**: If no match found, use base template or raise error

### Benefits of hierarchical templates

- **Reduced duplication**: One base template covers most of the year
- **Easy overrides**: Special schedules for holidays or seasons without recreating entire templates
- **Flexible patterns**: Date ranges with day-of-week filters handle complex recurring patterns
- **Maintainability**: Changes to base template automatically apply except where overridden

### Template composition

Templates can reference other templates for composition:

- **Parent template**: Base template that defines common structure
- **Override template**: Child template that modifies specific dayparts or blocks
- **Inheritance**: Override templates can inherit blocks from parent and only modify what's different

This allows operators to create "Christmas Base" that inherits from "Weekday Standard" but changes prime time programming.

## Grid blocks and dayparts

### Grid block

The smallest schedulable unit. Typically 30-minute time slots, though the duration is configurable per channel via `grid_block_minutes`.

- Grid blocks are atomic scheduling units
- Can contain series episodes, movies, or generic content types
- Duration must align with channel's grid block configuration
- Metadata like `commType` (e.g., "cartoon") or `introBumper` can be attached

### Daypart

A named block of time made up of one or more grid blocks. Used in templates to define programming patterns.

- Examples: "Morning Block" (6–9 AM), "Prime Time" (7–11 PM)
- Dayparts group related grid blocks with similar content characteristics
- Enable reusable template patterns across different times of day
- Content selection rules are often associated with dayparts

## Playlog mechanics

### Rolling horizon

The full day's playlog is not generated at midnight. Instead, the system uses a rolling horizon approach:

- Only 3–4 hours of playlog are created at a time
- The playlog horizon continuously extends ahead of the current time
- This avoids long gaps and unnecessary prep for time slots no one is watching
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

When no eligible asset is found for a time slot:

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

### Template minimalism

- Keep templates minimal but reusable
- Apply them to multiple days or duplicate if needed
- Templates define structure, not specific content

### Layer separation

- **Schedule and EPG**: High-level representations, not tied to files
- **Playlog**: Asset-level and file-specific, includes ads, bumpers, episode files
- **As-run log**: Factual record of what really aired and when

### Content selection timing

- Content selection, rules, and avails logic are applied during playlog generation
- Templates contain rules, not resolved content
- The playlog builder resolves rules into actual asset references

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

- Single template repeated daily
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

ScheduleService is the primary orchestrator for scheduling:

1. **Template resolution**: Determines which template applies to a date using hierarchical override rules:
   - Checks explicit BroadcastScheduleDay assignments first
   - Falls back to date range templates with day-of-week filters
   - Falls back to date range templates
   - Falls back to base template
2. Reads template blocks and content selection rules
3. Queries assets for eligible content (`state='ready'` and `approved_for_broadcast=true`)
4. Generates playlog events with precise timing
5. Extends the playlog horizon as needed
6. Uses master clock for all timing decisions

### Program director

ProgramDirector coordinates multiple channels and may:

- Reference channel configurations
- Coordinate cross-channel programming
- Apply content conflict resolution rules
- Manage system-wide scheduling state

### Channel manager

ChannelManager executes playout but does not modify scheduling domain models:

- Reads playlog events for playout instructions
- References channel configuration
- Uses asset file paths for content playback
- Aligns playback to master clock timestamps

## Naming rules

- **Template**: Reusable programming structure with dayparts
- **Schedule**: Template instantiation for a specific broadcast day
- **EPG**: Electronic Program Guide (coarse viewer-facing schedule)
- **Playlog**: Fine-grained playout plan with specific assets
- **As-run log**: Record of what actually aired
- **Grid block**: Smallest schedulable time unit
- **Daypart**: Named block of time in a template

## See also

- [Domain: Scheduling](../domain/Scheduling.md) - Core scheduling domain models
- [Domain: ScheduleTemplate](../domain/ScheduleTemplate.md) - Template structure
- [Domain: PlaylogEvent](../domain/PlaylogEvent.md) - Playlog event records
- [Domain: EPGGeneration](../domain/EPGGeneration.md) - EPG generation logic
- [Domain: MasterClock](../domain/MasterClock.md) - Time authority
- [Runtime: ChannelManager](../runtime/ChannelManager.md) - Playout execution
- [Runtime: ScheduleService](../runtime/schedule_service.md) - Scheduling service
- [Runtime: AsRunLogging](../runtime/AsRunLogging.md) - As-run log implementation
