_Related: [Architecture](../architecture/ArchitectureOverview.md) • [SchedulePlan](SchedulePlan.md) • [ScheduleDay](ScheduleDay.md) • [SchedulePlanLabel](SchedulePlanLabel.md) • [VirtualAsset](VirtualAsset.md) • [Operator CLI](../operator/CLI.md)_

# Domain — SchedulePlanBlockAssignment

## Purpose

SchedulePlanBlockAssignment represents a scheduled piece of content in a SchedulePlan. This is where content is selected and placed manually or with assistance. SchedulePlanBlockAssignment is the **canonical source for "what to play when" at the planning layer** — the authoritative definition of what content should air at specific times.

Each assignment defines:
- **When** content should air (start_time in schedule-time and duration in minutes)
- **What** content should air (specific asset, [VirtualAsset](VirtualAsset.md) reference, or random/filtered selection)
- **How** content should be selected (playback rules, playout directives, and operator intent)

SchedulePlanBlockAssignments are the building blocks of SchedulePlans. They directly specify what content runs at specific times within a plan, using schedule-time (00:00 to 24:00 relative to programming day) and duration in minutes (aligned with channel grid).

## Core Model / Scope

SchedulePlanBlockAssignment enables:

- **Content placement**: Operators place specific content or content rules into time slots
- **Time structure definition**: Assignments define when content airs using schedule-relative start_time (00:00–24:00) and duration
- **Content selection rules**: Specify how content should be selected (chronological, random, seasonal, etc.)
- **Operator intent capture**: Store metadata about programming intent (e.g., "Play Cheers seasonally")
- **Source of truth**: Assignments are the authoritative definition of what should air when
- **Layering support**: Assignments from higher-priority plans override assignments from lower-priority plans when they overlap
- **Visual organization**: Optional label_id reference to SchedulePlanLabel for grouping and visualization

**Key Points:**
- SchedulePlanBlockAssignment is the **canonical source for "what to play when" at the planning layer**
- Assignments can reference a **specific asset**, a **[VirtualAsset](VirtualAsset.md)**, or **instruct the system to pick at random from a set of filtered assets**
- **Start time** is expressed in schedule-time (00:00 to 24:00 relative to programming day), not wall-clock time
- **Duration** is in minutes, aligned with channel grid
- Includes optional **playout directives** like `sequential`, `random`, `offset`, etc. (via `episode_policy` and `playback_rules`)
- Content is selected and placed manually or with operator assistance
- Each assignment belongs to a SchedulePlan and defines a time slot with content
- Lower-priority blocks are superseded by more specific ones when plans are layered (e.g., weekday layer overridden by ChristmasDay)
- Optional label_id reference to SchedulePlanLabel for visualization/grouping

## Persistence Model

SchedulePlanBlockAssignment is managed by SQLAlchemy with the following fields:

- **id** (UUID, primary key): Unique identifier for relational joins and foreign key references
- **channel_id** (UUID, required, foreign key): Reference to Channel - the channel this assignment applies to
- **plan_id** (UUID, required, foreign key): Reference to parent SchedulePlan
- **start_time** (Text, required): Start time in "HH:MM" format expressed in schedule-time (00:00 to 24:00 relative to programming day), not wall-clock time (e.g., "06:00" means 6 hours after programming day start at 00:00, regardless of actual wall-clock time)
- **duration** (Integer, required): Duration in minutes for this assignment, aligned with channel grid
- **content_type** (Text, required): Type of content selection - one of: "series", "asset", "rule", "random", "virtual_package"
- **content_reference** (Text, required): Reference to the content:
  - For "series": Series identifier or UUID
  - For "asset": Asset UUID
  - For "rule": Rule JSON (e.g., "random family movie under 2 hours")
  - For "random": Random selection rule JSON
  - For "virtual_package": [VirtualAsset](VirtualAsset.md) UUID
- **label_id** (UUID, optional, foreign key): Reference to [SchedulePlanLabel](SchedulePlanLabel.md) (formerly "container") for visualization/grouping purposes
- **episode_policy** (Text, optional): Episode selection policy for series content, also serves as a playout directive (e.g., "sequential", "syndication", "random", "least-recently-used", "seasonal")
- **playback_rules** (JSON, optional): Additional playback rules, constraints, and playout directives (e.g., `sequential`, `random`, `offset`, chronological order, freshness requirements)
- **operator_intent** (Text, optional): Operator-defined metadata describing programming intent (e.g., "Play Cheers seasonally", "Rotate through classic movies", "Fill with family-friendly content")
- **created_at** (DateTime(timezone=True), required): Record creation timestamp
- **updated_at** (DateTime(timezone=True), required): Record last modification timestamp

### Table Name

The table is named `schedule_plan_block_assignments` (plural). Schema migration is handled through Alembic. Postgres is the authoritative backing store.

### Constraints

- `start_time` must be valid "HH:MM" format time expressed in schedule-time (00:00 to 24:00 relative to programming day), not wall-clock time
- `duration` must be a positive integer (duration in minutes, aligned with channel grid)
- `content_type` must be one of: "series", "asset", "rule", "random", "virtual_package"
- Assignments must not overlap within the same plan (calculated using start_time + duration)
- Time assignments are schedule-relative (00:00–24:00), representing absolute offsets from the broadcast day start (00:00)
- `channel_id` must reference a valid Channel
- `plan_id` must reference a valid SchedulePlan
- `label_id` must reference a valid SchedulePlanLabel if provided (optional)

## Contract / Interface

SchedulePlanBlockAssignment is the source of truth for what should air when. It defines:

- **Channel assignment** (channel_id) - the channel this assignment applies to
- **Plan membership** (plan_id) - the SchedulePlan this assignment belongs to
- **Time placement** (start_time, duration) - when content should air, using schedule-time (00:00 to 24:00 relative to programming day), duration in minutes aligned with channel grid
- **Content selection** (content_type, content_reference) - what content should air: specific asset, [VirtualAsset](VirtualAsset.md) UUID, or random/filtered selection from a set of assets
- **Playout directives** (episode_policy, playback_rules) - optional directives controlling how content is selected and played (e.g., `sequential`, `random`, `offset`, chronological order, seasonal selection)
- **Operator intent** (operator_intent) - metadata describing programming goals and constraints
- **Visual grouping** (label_id, optional) - reference to [SchedulePlanLabel](SchedulePlanLabel.md) for visualization/grouping purposes

Assignments are the building blocks of plans. They directly specify what content runs when, making them the authoritative source for scheduling decisions.

## Time Model

**Schedule-Time:** Each SchedulePlan begins at programming day 00:00 (relative to the channel's `broadcast_day_start` anchor). All time assignments within a plan use **schedule-time** (00:00 to 24:00 relative to programming day), not wall-clock time.

- `start_time` is specified as "HH:MM" format and represents schedule-time (00:00 to 24:00 relative to programming day), not wall-clock time
- For example, `start_time: "06:00"` means 6 hours after the programming day start (00:00), regardless of the actual wall-clock time
- `duration` specifies how long the content should play in **minutes**, aligned with the channel grid
- Assignments can span midnight (e.g., start_time: "22:00", duration: 240 minutes spans to 02:00 next day)
- Time values are absolute offsets from the programming day start (00:00), representing positions within the 24-hour schedule day

**Time Resolution:** When a SchedulePlan is resolved into a [ScheduleDay](ScheduleDay.md), the assignment's schedule-time `start_time` and `duration` are combined with the channel's `broadcast_day_start` to produce real-world wall-clock times.

## Content Selection Model

SchedulePlanBlockAssignment supports three primary content selection approaches:

1. **Specific Asset**: Reference a specific asset directly (useful for one-off content like specials or movies)
2. **VirtualAsset**: Reference a [VirtualAsset](VirtualAsset.md) container that expands to multiple assets at ScheduleDay or Playlog time
3. **Random/Filtered Selection**: Instruct the system to pick at random from a set of filtered assets based on rules, series, or compatibility criteria

The following content selection types are supported:

### Asset Assignments

Direct assignment of a specific asset (useful for one-off content like specials or movies):

```json
{
  "content_type": "asset",
  "content_reference": "550e8400-e29b-41d4-a716-446655440000",
  "start_time": "20:00",
  "duration": 120
}
```

### Series Assignments

Assignment of a series with episode selection policy:

```json
{
  "content_type": "series",
  "content_reference": "Cheers",
  "episode_policy": "seasonal",
  "operator_intent": "Play Cheers seasonally",
  "start_time": "19:00",
  "duration": 30
}
```

**Episode Policies (Playout Directives):**
- `sequential`: Play episodes in sequential order (S01E01, S01E02, ...)
- `syndication`: Play episodes in syndication order
- `random`: Random episode selection
- `seasonal`: Play episodes appropriate for the current season
- `least-recently-used`: Select episodes that haven't aired recently

**Additional Playout Directives (via playback_rules JSON):**
- `sequential`: Play content in sequential order
- `random`: Random selection from filtered set
- `offset`: Start playback at a specific offset within the asset
- `avoid_repeats`: Avoid content that has aired recently
- `prefer_new`: Prefer recently added content
- `freshness`: Require content within a certain age range


### Random Assignments

System-selected content based on compatibility and freshness. This instructs the system to pick at random from a set of filtered assets:

```json
{
  "content_type": "random",
  "content_reference": "{\"compatibility\": \"family-friendly\", \"freshness\": \"recent\"}",
  "playback_rules": {"avoid_repeats": true, "prefer_new": true, "random": true},
  "start_time": "15:00",
  "duration": 90
}
```

### Rule Assignments (Filtered Selection)

Assignment using content selection rules that filter assets and instruct the system to pick from the filtered set:

```json
{
  "content_type": "rule",
  "content_reference": "{\"genre\": \"family\", \"max_duration\": 120, \"rating\": \"PG\"}",
  "playback_rules": {"random": true, "avoid_repeats": true},
  "start_time": "14:00",
  "duration": 120
}
```

### VirtualAsset Assignments

Assignment of a [VirtualAsset](VirtualAsset.md) (container for multiple assets - fixed sequence or rule-based):

```json
{
  "content_type": "virtual_package",
  "content_reference": "550e8400-e29b-41d4-a716-446655440000",
  "operator_intent": "Rotate through classic movies",
  "start_time": "22:00",
  "duration": 120
}
```

This assignment uses a [VirtualAsset](VirtualAsset.md) UUID to reference a container of classic movies in the 10:00 PM late night slot. VirtualAssets expand to actual assets at ScheduleDay or Playlog time. The `content_reference` must be a valid VirtualAsset UUID.

## Execution Model

SchedulePlanBlockAssignments are consumed during schedule generation:

1. **Plan Resolution**: ScheduleService identifies active SchedulePlans for a channel and date
2. **Layering Resolution**: When multiple plans match the same date, plans are layered by priority. Higher-priority plans override lower-priority plans. Block assignments from higher-priority plans supersede overlapping assignments from lower-priority plans (e.g., a ChristmasDay plan with priority 20 overrides a WeekdayPlan with priority 10)
3. **Assignment Retrieval**: SchedulePlanBlockAssignments are retrieved from the active plan(s), with higher-priority assignments taking precedence
4. **Content Resolution**: Content references are resolved to specific assets based on content_type and playback rules
5. **Time Resolution**: Assignment schedule-relative times (start_time, duration) are combined with channel's broadcast_day_start to produce wall-clock times
6. **ScheduleDay Generation**: Resolved assignments are used to create [BroadcastScheduleDay](ScheduleDay.md) records
7. **PlaylogEvent Generation**: ScheduleDays are used to generate [BroadcastPlaylogEvent](PlaylogEvent.md) records for playout

**Critical Rule:** SchedulePlanBlockAssignment is the source of truth for what should air when. The scheduler uses assignments directly to determine content selections and timing.

**Layering Behavior:** When multiple SchedulePlans are active for the same date, they are layered by priority. Lower-priority blocks are superseded by more specific ones. For example, a generic weekday plan (priority 10) might define blocks for 06:00–24:00, but a ChristmasDay plan (priority 20) can override specific time slots (e.g., 19:00–20:00) with holiday-specific content. The higher-priority plan's assignments take precedence for overlapping time periods.

## Relationship to SchedulePlanLabel

[SchedulePlanLabel](SchedulePlanLabel.md) can optionally be associated with SchedulePlanBlockAssignments for visual organization and grouping:

- **Visual Grouping**: Labels group related assignments together (e.g., "Morning Cartoons" groups all morning cartoon assignments)
- **Optional Reference**: Assignments can reference a SchedulePlanLabel via the optional `label_id` field (formerly called "container")
- **Visualization/Grouping**: Labels are used for visualization and grouping purposes in the UI
- **No Scheduling Impact**: Labels do not affect scheduling logic or execution
- **Optional**: Assignments can exist without labels (label_id is nullable)

Example: Multiple assignments with start_time "06:00", "06:30", "07:00" might share the same `label_id` referencing a "Morning Cartoons" label for operator convenience and visual organization, but the label has no impact on scheduling.

## Relationship to ScheduleDay

SchedulePlanBlockAssignments flow into [ScheduleDay](ScheduleDay.md) during schedule resolution:

1. **Assignment Resolution**: SchedulePlanBlockAssignments from an active SchedulePlan are retrieved
2. **Content Selection**: Content references are resolved to specific assets based on content_type, playback rules, and operator intent
3. **Time Resolution**: Assignment times are combined with channel's broadcast_day_start to produce real-world wall-clock times
4. **ScheduleDay Creation**: Resolved assignments become the resolved asset selections in BroadcastScheduleDay

**Example Flow:**
- Assignment: `start_time: "19:00"`, `duration: 30`, `content_type: "series"`, `content_reference: "Cheers"`, `episode_policy: "seasonal"`
- Resolution: System selects appropriate Cheers episode for current season
- ScheduleDay: Contains resolved asset UUID with wall-clock time (e.g., 2025-12-25 19:00:00 UTC)

ScheduleDays are resolved 3-5 days in advance for EPG and playout purposes, based on the assignments in the active SchedulePlan.

## Operator Workflows

**Create Assignment**: Operators create assignments to place content in schedule plans. They specify:
- Time slot (start_time, duration)
- Content selection (asset, series, rule, or virtual package)
- Playback rules (how content should be selected)
- Operator intent (programming goals and constraints)

**Manual Placement**: Operators manually place specific assets or series into time slots, defining exactly what should air when.

**Assisted Placement**: Operators use system assistance to place content:
- System suggests content based on rules and constraints
- Operators review and approve suggestions
- Assignments are created with operator intent metadata

**Edit Assignment**: Operators modify existing assignments to:
- Change time slots
- Update content selections
- Adjust playback rules
- Update operator intent

**Preview Assignment**: Operators preview how an assignment will resolve:
- See which specific asset will be selected
- View resolved wall-clock times
- Check for conflicts or rule violations

## Examples

### Example 1: Morning Cartoons

```json
{
  "channel_id": "channel-uuid-1",
  "plan_id": "weekday-plan-uuid",
  "start_time": "06:00",
  "duration": 30,
  "content_type": "series",
  "content_reference": "Tom & Jerry",
  "episode_policy": "syndication",
  "operator_intent": "Morning cartoons for kids"
}
```

This assignment places Tom & Jerry episodes in the 6:00 AM slot on weekdays, using syndication order.

### Example 2: Prime Time Movie

```json
{
  "channel_id": "channel-uuid-1",
  "plan_id": "weekday-plan-uuid",
  "start_time": "20:00",
  "duration": 120,
  "content_type": "rule",
  "content_reference": "{\"genre\": \"drama\", \"min_duration\": 90, \"max_duration\": 150}",
  "playback_rules": {"avoid_repeats": true, "prefer_recent": false},
  "operator_intent": "Prime time drama movies"
}
```

This assignment uses a rule to select drama movies between 90-150 minutes for the 8:00 PM prime time slot.

### Example 3: Seasonal Series

```json
{
  "channel_id": "channel-uuid-1",
  "plan_id": "holiday-plan-uuid",
  "start_time": "19:00",
  "duration": 30,
  "content_type": "series",
  "content_reference": "Cheers",
  "episode_policy": "seasonal",
  "operator_intent": "Play Cheers seasonally"
}
```

This assignment places Cheers episodes in the 7:00 PM slot, with seasonal episode selection based on the current time of year.

### Example 4: Late Night Movies

```json
{
  "channel_id": "channel-uuid-1",
  "plan_id": "weekday-plan-uuid",
  "start_time": "22:00",
  "duration": 120,
  "content_type": "virtual_package",
  "content_reference": "550e8400-e29b-41d4-a716-446655440000",
  "playback_rules": {"rotation": "least-recently-used", "avoid_repeats": true},
  "operator_intent": "Rotate through classic movies",
  "label_id": "label-uuid-1"
}
```

This assignment uses a VirtualAsset UUID to reference a container of classic movies in the 10:00 PM late night slot. The `label_id` references a SchedulePlanLabel for visual grouping (e.g., "Late Night Movies").

## Failure / Fallback Behavior

If assignments are missing or invalid:

- **Missing assignments**: Result in gaps in the schedule (allowed but should generate warnings)
- **Invalid content references**: System falls back to default content or skips the assignment
- **Overlapping assignments**: Validation should flag conflicts; highest priority assignment takes precedence
- **Invalid time ranges**: Assignments outside valid broadcast day are rejected during validation
- **Unresolvable content**: If content cannot be resolved (e.g., series has no episodes), system falls back to alternative content or leaves gap

## Naming Rules

The canonical name for this concept in code and documentation is SchedulePlanBlockAssignment.

Assignments are often referred to as "block assignments" or simply "assignments" in operator workflows, but the full name should be used in technical documentation and code.

## Validation & Invariants

- **No overlapping assignments**: Assignments within the same plan must not overlap in time (calculated using start_time + duration)
- **Valid time format**: start_time must be valid "HH:MM" format
- **Positive duration**: duration must be a positive integer
- **Valid content reference**: content_reference must be valid for the specified content_type
- **Channel consistency**: channel_id must match the channel associated with the parent SchedulePlan
- **Referential integrity**: plan_id must reference a valid SchedulePlan

## See Also

- [SchedulePlan](SchedulePlan.md) - Top-level operator-created plans that define channel programming
- [ScheduleDay](ScheduleDay.md) - Resolved schedules for specific channel and date (generated from assignments)
- [SchedulePlanLabel](SchedulePlanLabel.md) - Optional UI-only labels for visual organization of assignments
- [VirtualAsset](VirtualAsset.md) - ⚠️ FUTURE: Container for multiple assets (can be referenced in assignments)
- [PlaylogEvent](PlaylogEvent.md) - Generated playout events (derived from resolved assignments)
- [Scheduling](Scheduling.md) - High-level scheduling system
- [Channel](Channel.md) - Channel configuration and timing policy
- [Asset](Asset.md) - Approved content available for scheduling
- [Operator CLI](../operator/CLI.md) - Operational procedures

SchedulePlanBlockAssignment is the **canonical source for "what to play when" at the planning layer**. Assignments can reference a specific asset, a VirtualAsset, or instruct the system to pick at random from a set of filtered assets. Start time is expressed in schedule-time (00:00 to 24:00 relative to programming day), and duration is in minutes (aligned with channel grid). Assignments include optional playout directives like `sequential`, `random`, `offset`, etc. Content is selected and placed manually or with operator assistance, and assignments flow into ScheduleDay for resolution 3-5 days in advance for EPG and playout purposes.

