_Related: [Architecture](../architecture/ArchitectureOverview.md) • [SchedulePlan](SchedulePlan.md) • [Pattern](Pattern.md) • [ScheduleDay](ScheduleDay.md) • [Channel](Channel.md) • [Operator CLI](../operator/CLI.md)_

# Domain — Zone

> **Note:** This document reflects the modern scheduling architecture. Active chain: **SchedulePlan (Zones + Patterns) → ScheduleDay (resolved) → PlaylogEvent (runtime) → AsRunLog.**

## Purpose

Zone is a **named time window within the programming day** that declares when content should play. Zones are components of [SchedulePlan](SchedulePlan.md) and reference [Pattern](Pattern.md) entries that define the content sequence for the Zone. Zones do not hold episodes or assets directly — they declare **when** content should play and **which Pattern to use**. The plan engine applies the Pattern repeatedly across the Zone's active window until the Zone is full, snapping to the Channel's Grid boundaries.

**What a Zone is:**

- A named time window within the programming day (e.g., "Base", "Prime Time", "After Dark")
- Declares when it applies (e.g., `00:00–24:00`, `19:00–22:00`, `22:00–05:00`)
- References a [Pattern](Pattern.md) that defines the content sequence
- May have optional day-of-week filters (e.g., Mon–Fri, Sat–Sun)
- Uses broadcast day time (00:00–24:00 relative to `programming_day_start`)

**What a Zone is not:**

- A container for episodes or assets (that's what Programs are)
- A definition of what content plays (that's what Patterns are)
- A time-block assignment (that's resolved at ScheduleDay time)
- A calendar day boundary (Zones use broadcast day time)

Zones are part of SchedulePlans. When a SchedulePlan is resolved into a [ScheduleDay](ScheduleDay.md), Zones expand their Patterns across the Zone's time window, snapping to the Channel's Grid boundaries. Programs in the Pattern are resolved to concrete episodes at ScheduleDay time.

## Core Model / Scope

Zone enables:

- **Time window declaration**: Zones define when content should play within the programming day
- **Pattern association**: Each Zone references a [Pattern](Pattern.md) that defines the content sequence
- **Day-of-week filtering**: Optional day filters restrict when Zones are active (e.g., weekday-only, weekend-only)
- **Broadcast day alignment**: Zones use broadcast day time (00:00–24:00 relative to `programming_day_start`), not calendar day time
- **Grid boundary snapping**: All Zone expansions snap to the Channel's Grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`)

**Key Points:**

- Zone declares **when** content should play (time window)
- Zone references **which Pattern** to use (content sequence)
- Zones are part of SchedulePlans, not standalone entities
- Zones use broadcast day time (00:00–24:00), not calendar day time
- Zones can span midnight (e.g., `22:00–05:00`) within the same broadcast day
- Zones support optional day-of-week filters for recurring patterns
- Zone expansions snap to Channel Grid boundaries during ScheduleDay resolution

## Persistence Model

Zone is managed by SQLAlchemy with the following fields:

- **id** (UUID, primary key): Unique identifier for relational joins and foreign key references
- **plan_id** (UUID, required, foreign key): Reference to parent [SchedulePlan](SchedulePlan.md)
- **name** (Text, required): Human-readable identifier (e.g., "Base", "After Dark", "Prime Time", "Weekend Morning")
- **start_time** (Time, required): Start time of the Zone's active window in broadcast day time (e.g., `00:00:00`, `19:00:00`, `22:00:00`)
- **end_time** (Time, required): End time of the Zone's active window in broadcast day time (e.g., `24:00:00`, `22:00:00`, `05:00:00`)
- **pattern_id** (UUID, required, foreign key): Reference to the [Pattern](Pattern.md) that defines the content sequence for this Zone
- **day_filters** (JSON, optional): Day-of-week constraints that restrict when the Zone is active (e.g., `["MON", "TUE", "WED", "THU", "FRI"]` for weekdays, `["SAT", "SUN"]` for weekends). If null, Zone is active on all days.
- **enabled** (Boolean, required, default: true): Whether the Zone is active and eligible for schedule generation. Disabled Zones are ignored during resolution.
- **effective_start** (Date, optional): Start date for Zone validity (inclusive). If null, Zone is valid from plan creation.
- **effective_end** (Date, optional): End date for Zone validity (inclusive). If null, Zone is valid indefinitely.
- **dst_policy** (Text, optional): DST transition handling policy - one of: "reject", "shrink_one_block", "expand_one_block". If null, defaults to system-wide DST policy. On DST transition dates, Zone duration is validated per this policy.
- **created_at** (DateTime(timezone=True), required): Record creation timestamp
- **updated_at** (DateTime(timezone=True), required): Record last modification timestamp

**Note:** Zones use broadcast day time (00:00–24:00 relative to `programming_day_start`), not calendar day time. A Zone like `22:00–05:00` spans from 22:00 on one calendar day to 05:00 the next calendar day, but both times are within the same broadcast day (e.g., 06:00 to 06:00 next day).

**24:00 Storage Semantics:** Postgres TIME type cannot store 24:00:00. Zones with `end_time=24:00:00` are stored as `23:59:59.999999` in the database, with a flag or normalization logic indicating end-of-day. The domain layer normalizes this for clarity, but documentation uses 24:00:00 for conceptual accuracy.

### Table Name

The table is named `zones` (plural). Schema migration is handled through Alembic. Postgres is the authoritative backing store.

### Constraints

- `name` must be non-empty and unique within the SchedulePlan
- `start_time` and `end_time` must be valid times in broadcast day format (00:00:00 to 24:00:00)
- `start_time` must be less than `end_time` (unless spanning midnight, in which case end_time < start_time is allowed, e.g., `22:00–05:00`)
- `plan_id` must reference a valid SchedulePlan
- `pattern_id` must reference a valid Pattern within the same SchedulePlan (enforced as invariant)
- `day_filters` must be a valid JSON array of day abbreviations if provided (e.g., `["MON", "TUE", "WED", "THU", "FRI"]`)
- `enabled` defaults to true; disabled Zones are ignored during resolution
- `dst_policy` must be one of: "reject", "shrink_one_block", "expand_one_block" if provided
- `effective_start` and `effective_end` must form a valid date range (effective_start <= effective_end) if both are provided
- **Grid divisibility invariant**: Zone duration in minutes must be divisible by the Channel's `grid_block_minutes`. Validation occurs at Zone creation/update time (domain-level validation), not only during ScheduleDay resolution. If not divisible, the system rejects the configuration unless a policy allows rounding to nearest boundary.
- **Zone time windows alignment**: Zone start and end times must align with the Channel's Grid boundaries (`block_start_offsets_minutes`). Validation occurs at Zone creation/update time (domain-level validation).
- **DST transition handling**: On DST transition dates, Zone duration is validated per `dst_policy`: "reject" (fail validation), "shrink_one_block" (reduce duration by one grid block), or "expand_one_block" (increase duration by one grid block). If `dst_policy` is null, defaults to system-wide DST policy.

### Relationships

Zone has relationships with:

- **SchedulePlan** (many-to-one): Multiple Zones belong to a single SchedulePlan
- **Pattern** (many-to-one): Each Zone references one Pattern that defines the content sequence
- **ScheduleDay** (one-to-many via resolution): Zones are expanded during ScheduleDay generation

## Contract / Interface

Zone is a named time window within the programming day. It defines:

- **Plan membership** (plan_id) - the SchedulePlan this Zone belongs to
- **Time window** (start_time, end_time) - when the Zone applies (broadcast day time, 00:00–24:00)
- **Pattern reference** (pattern_id) - which Pattern defines the content sequence for this Zone
- **Day-of-week filtering** (day_filters) - optional constraints that restrict when the Zone is active
- **Name** (name) - human-readable identifier for operator reference

Zones declare **when** content should play and **which Pattern to use**. They do not hold episodes or assets directly. The plan engine applies the Pattern repeatedly across the Zone's active window until the Zone is full, snapping to the Channel's Grid boundaries.

**Zone Alignment:**

- Zones align to **broadcast days**, not calendar days
- The broadcast day is defined by the Channel's `programming_day_start` (e.g., 06:00)
- Zones use broadcast day time (00:00–24:00 relative to `programming_day_start`)
- A Zone like `22:00–05:00` spans from 22:00 on one calendar day to 05:00 the next calendar day, but both times are within the same broadcast day

**Zone Expansion:**

- During ScheduleDay resolution, Zones expand their Patterns across the Zone's time window
- Pattern repeating continues until the Zone's declared end time is reached
- All content placement snaps to the Channel's Grid boundaries
- Long content can bridge Zone boundaries (soft-start-after-current policy for Zone openings, carry-out policy for Zone closings)

**Zone Activation:**

- Zones are evaluated for activation based on:
  1. `enabled` status (disabled Zones are ignored)
  2. `effective_start` and `effective_end` date range (if provided)
  3. The date's day of week (via `day_filters` if provided)
  4. The Zone's time window

## Execution Model

Zones are consumed during schedule generation:

1. **Plan Resolution**: ScheduleService identifies active SchedulePlans for a channel and date
2. **Layering Resolution**: When multiple plans match, priority resolves overlapping Zones. Higher-priority plans' Zones override lower-priority plans' Zones for overlapping time windows
3. **Zone Identification**: For each active plan, identify its Zones (time windows) that apply to the date (considering `enabled`, `effective_start`/`effective_end`, `day_filters`, and time window)
4. **Pattern Expansion**: For each Zone, retrieve its associated Pattern and expand it across the Zone's active window:
   - Take the ordered list of Program references from the Pattern
   - Repeat the Pattern across the Zone's time window
   - Snap to the Channel's Grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`)
   - Continue until the Zone's declared end time is reached
5. **Soft-Start Handling**: If a Zone opens while content is already playing (from a previous Zone or carry-in), apply the soft-start-after-current policy:
   - Current content continues to completion
   - Zone's Pattern begins at the next valid Grid boundary after the current content completes
6. **ScheduleDay Generation**: Resolved Zones, Patterns, and Programs are used to create [ScheduleDay](ScheduleDay.md) records (resolved 3-4 days in advance)

**Time Resolution:** Zone time windows are combined with the Channel's Grid boundaries to produce real-world wall-clock times. Zones declare when they apply (e.g., base 00:00–24:00, or After Dark 22:00–05:00), and the plan engine repeats Patterns over Zones until Zones are full, snapping to Grid boundaries.

**Conflict Resolution:** When multiple Zones from different plans overlap, priority resolution determines which Zone applies. Higher-priority plans' Zones override lower-priority plans' Zones for overlapping time windows. When a Zone opens while content is already playing, the soft-start-after-current policy ensures clean transitions without mid-program interruptions.

## Zone Expansion and Pattern Repeating

Zones expand their Patterns across the Zone's time window during ScheduleDay resolution. The expansion process:

1. **Zone Activation**: Determine if the Zone is active for the given date (considering day_filters)
2. **Pattern Retrieval**: Retrieve the Pattern referenced by the Zone
3. **Pattern Repeating**: Repeat the Pattern across the Zone's active window:
   - Take the ordered list of Program references from the Pattern
   - Place each Program at the next valid Grid boundary
   - Continue repeating the Pattern until the Zone's declared end time is reached
4. **Grid Alignment**: All Program placements snap to the Channel's Grid boundaries
5. **Zone Completion**: Zone ends at its declared end time, even if the Pattern has not fully filled the Zone (under-filled time becomes avails)

**Example:**

- Zone: `19:00–22:00` (Prime Time, 3 hours)
- Pattern: `["Cheers", "The Big Bang Theory"]`
- Result: The pattern repeats across the 3-hour window:
  - Cheers (episode 1) starts at 19:00, ends at 19:30
  - The Big Bang Theory (episode 1) starts at 19:30, ends at 20:00
  - Cheers (episode 2) starts at 20:00, ends at 20:30
  - The Big Bang Theory (episode 2) starts at 20:30, ends at 21:00
  - Cheers (episode 3) starts at 21:00, ends at 21:30
  - The Big Bang Theory (episode 3) starts at 21:30, ends at 22:00 (zone end)

**Key Point:** The pattern repeats cyclically until the Zone's declared end time (22:00) is reached. Each Program reference expands to a specific episode at ScheduleDay time, and the pattern continues repeating regardless of individual episode lengths (they snap to grid boundaries).

## Soft-Start and Conflict Resolution

**Soft-Start-After-Current Policy:**
When a Zone opens while content is already playing (e.g., a Zone starts at 19:00 but a program from a previous Zone is still running), the system applies the soft-start-after-current policy:

- The current program continues to completion
- The new Zone's Pattern starts at the next valid Grid boundary after the current program ends
- This ensures clean transitions and prevents mid-program interruptions

**Example:**

- Content playing from 19:00 expected to end at 21:15
- Zone opening at 20:00
- Result: Current content continues until 21:15, then Zone's Pattern starts at 21:30 (next grid boundary)

**Carry-Out Policy:**
If Zone ends while content is mid-program, content finishes to completion, then the next Zone begins at the next grid boundary. This is the mirror rule to soft-start: just as Zones don't interrupt in-flight content when opening, Zones don't cut content mid-play when closing.

**Example:**

- Zone: `19:00–22:00` with Pattern `["Movie Block"]`
- Movie Block resolves to a 2.5-hour movie (ends at 21:30)
- Next Zone starts at 22:00
- Result: Movie plays to completion at 21:30, then next Zone's Pattern starts at 22:00 (next grid boundary)

**Example with Overflow:**

- Zone: `19:00–22:00` with Pattern `["Movie Block"]`
- Movie Block resolves to a 3-hour movie (would end at 22:00)
- Next Zone starts at 22:00
- Result: Movie plays to completion, consuming additional grid blocks past Zone end if needed. Next Zone's Pattern starts at the next grid boundary after movie completion (e.g., 22:30 if grid is 30-minute blocks).

**Priority-Based Zone Override:**
When multiple SchedulePlans are active for the same date, Zones are resolved by priority:

- Higher-priority plans' Zones override lower-priority plans' Zones for overlapping time windows
- More specific plans (e.g., holidays) should have higher priority than general plans (e.g., weekdays)
- Zones from higher-priority plans completely supersede overlapping Zones from lower-priority plans

**Example:**

- WeekdayPlan (priority 10): Zone `00:00–24:00` with Pattern `["Series A", "Series B"]`
- ChristmasPlan (priority 30): Zone `19:00–22:00` with Pattern `["Christmas Special"]`
- Result: On December 25, the ChristmasPlan Zone overrides the WeekdayPlan Zone for 19:00–22:00, but WeekdayPlan Zone applies for 00:00–19:00 and 22:00–24:00

## Broadcast Day Alignment

Zones align to **broadcast days**, not calendar days. The broadcast day is defined by the Channel's `programming_day_start` (e.g., 06:00).

**Key Points:**

- Zones use broadcast day time (00:00–24:00 relative to `programming_day_start`)
- A Zone like `22:00–05:00` spans from 22:00 on one calendar day to 05:00 the next calendar day, but both times are within the same broadcast day
- Long content can bridge the broadcast day boundary without truncation
- For example, a movie starting at 23:00 can continue past midnight (00:00) and into the next calendar day's early hours (e.g., until 01:30) without being cut
- The carry-in policy ensures content that crosses the programming-day seam continues into the next broadcast day until completion

**Example:**

- Broadcast day start: 06:00
- Zone: `22:00–05:00` (After Dark)
- Calendar interpretation:
  - Zone starts at 22:00 on Day 1 (calendar)
  - Zone ends at 05:00 on Day 2 (calendar)
  - Both times are within the same broadcast day (06:00 Day 1 to 06:00 Day 2)

## Day-of-Week Filtering

Zones support optional day-of-week filters that restrict when the Zone is active. This enables recurring patterns like "weekday mornings" or "weekend afternoons."

**Day Filter Format:**

- `day_filters` is a JSON array of day abbreviations (e.g., `["MON", "TUE", "WED", "THU", "FRI"]`)
- If `day_filters` is null, the Zone is active on all days
- Day abbreviations: `MON`, `TUE`, `WED`, `THU`, `FRI`, `SAT`, `SUN`

**Examples:**

- Weekday Zone: `day_filters: ["MON", "TUE", "WED", "THU", "FRI"]` - Active Monday through Friday
- Weekend Zone: `day_filters: ["SAT", "SUN"]` - Active Saturday and Sunday
- All Days Zone: `day_filters: null` - Active every day

**Zone Activation Evaluation:**
During ScheduleDay resolution, Zones are evaluated for activation in this order:

1. **Enabled check**: If `enabled=false`, Zone is skipped
2. **Effective date range**: If `effective_start` or `effective_end` are provided, date must fall within the range (inclusive)
3. **Day-of-week filter**: If `day_filters` is provided, the date's day of week must match
4. **Time window**: The Zone's time window must apply to the schedule being generated

If all checks pass, the Zone is active for that date.

## Relationship to ScheduleDay

Zones flow into [ScheduleDay](ScheduleDay.md) via Pattern expansion during schedule resolution:

1. **Zone Identification**: Zones from active SchedulePlans are identified for the channel and date
2. **Priority Resolution**: When multiple plans match, priority resolves overlapping Zones
3. **Pattern Expansion**: Each Zone's Pattern is expanded across the Zone's time window, snapping to Grid boundaries
4. **Program Resolution**: Programs in Patterns are resolved to concrete episodes at ScheduleDay time
5. **Time Calculation**: Zone time windows are combined with Grid boundaries to produce real-world wall-clock times
6. **ScheduleDay Creation**: Resolved Zones, Patterns, and Programs become the resolved asset selections in BroadcastScheduleDay

**Example Flow:**

- Zone: 19:00–22:00 (Prime Time)
- Pattern: [Cheers (series Program), Movie Block (composite Program)]
- Resolution at ScheduleDay time: System expands Pattern over Zone, selects appropriate episodes for Cheers, resolves Movie Block to specific assets
- ScheduleDay: Contains resolved asset UUIDs with wall-clock times (e.g., 2025-12-25 19:00:00 UTC for Cheers episode S11E05)

ScheduleDays are resolved 3-4 days in advance for EPG and playout purposes, based on the Zones, Patterns, and Programs in the active SchedulePlan.

## Operator Workflows

**Create Zone in Plan**: Operators create Zones as time windows within SchedulePlans. They specify:

- Name (e.g., "Prime Time", "After Dark")
- Time window (start_time, end_time in broadcast day time)
- Pattern reference (which Pattern defines the content sequence)
- Optional day filters (restrict to specific days of week)

**Edit Zone**: Operators modify existing Zones to:

- Change time window
- Update Pattern reference
- Modify day filters
- Update name

**Preview Zone**: Operators preview how a Zone will resolve:

- See how the Pattern repeats across the Zone's time window
- View grid alignment and timing
- Check for conflicts or rule violations

**Layer Zones**: Operators use multiple SchedulePlans with different priorities to layer Zones:

- Base plan with general Zones (e.g., weekday plan)
- Higher-priority plans with specific Zones (e.g., holiday plan)
- Higher-priority Zones override lower-priority Zones for overlapping time windows

## Examples

### Example 1: Base Zone

**Base zone covering full programming day:**

- Name: "Base"
- Start time: `00:00:00`
- End time: `24:00:00`
- Pattern: `["Cheers", "The Big Bang Theory"]`
- Day filters: `null` (active every day)
- Result: Pattern repeats across the full 24-hour day

### Example 2: Prime Time Zone

**Prime Time zone for evening programming:**

- Name: "Prime Time"
- Start time: `19:00:00`
- End time: `22:00:00`
- Pattern: `["Drama Series", "Movie Block"]`
- Day filters: `null` (active every day)
- Result: Pattern repeats across the 3-hour prime time window

### Example 3: After Dark Zone (Spanning Midnight)

**After Dark zone spanning midnight:**

- Name: "After Dark"
- Start time: `22:00:00`
- End time: `05:00:00`
- Pattern: `["Late Night Talk", "Classic Movies"]`
- Day filters: `null` (active every day)
- Result: Zone spans from 22:00 on one calendar day to 05:00 the next, but both times are within the same broadcast day

### Example 4: Weekend Morning Zone (Day Filtered)

**Weekend Morning zone with day filters:**

- Name: "Weekend Morning"
- Start time: `06:00:00`
- End time: `12:00:00`
- Pattern: `["Cartoons", "Kids Shows"]`
- Day filters: `["SAT", "SUN"]`
- Result: Zone is active only on weekends, 06:00–12:00

## Failure / Fallback Behavior

If Zones are missing or invalid:

- **Missing Zones**: Result in gaps in the schedule (allowed but should generate warnings). Under-filled time becomes avails.
- **Invalid time windows**: System validates Zone time windows against Grid boundaries and reports errors
- **Invalid Pattern references**: System validates that `pattern_id` references a Pattern within the same SchedulePlan (domain-level validation fails early). Invalid references are rejected at Zone creation/update time.
- **Overlapping Zones**: Priority resolution determines which Zone applies (higher priority wins)
- **Grid divisibility violations**: Zone duration must be divisible by `grid_block_minutes`. Violations are rejected at Zone creation/update time (domain-level validation), unless policy allows rounding.
- **DST transition conflicts**: On DST transition dates, Zone duration is validated per `dst_policy`. If policy is "reject" and duration cannot be accommodated, validation fails at Zone creation/update time.

## Naming Rules

The canonical name for this concept in code and documentation is Zone.

Zones are often referred to as "dayparts" or "time windows" in operator workflows, but the full name should be used in technical documentation and code.

## Validation & Invariants

- **Valid time window**: start_time and end_time must be valid times in broadcast day format (00:00:00 to 24:00:00)
- **Valid time range**: start_time must be less than end_time (unless spanning midnight, in which case end_time < start_time is allowed)
- **Valid Pattern reference**: pattern_id must reference a valid Pattern within the same SchedulePlan (enforced as invariant)
- **Pattern-Plan consistency**: pattern_id must belong to the same SchedulePlan as the Zone (enforced as invariant)
- **Grid alignment**: Zone start and end times must align with the Channel's Grid boundaries (`block_start_offsets_minutes`). Validation occurs at Zone creation/update time (domain-level validation).
- **Grid divisibility**: Zone duration in minutes must be divisible by the Channel's `grid_block_minutes`. If not divisible, the system rejects the configuration unless a policy allows rounding to nearest boundary. Validation occurs at Zone creation/update time (domain-level validation).
- **Name uniqueness**: name must be unique within the SchedulePlan (enforced as invariant)
- **Day filter validity**: day_filters must be a valid JSON array of day abbreviations if provided
- **Effective date range**: effective_start and effective_end must form a valid date range (effective_start <= effective_end) if both are provided
- **DST policy**: On DST transition dates, Zone duration is validated per `dst_policy`: "reject" (fail validation), "shrink_one_block" (reduce duration by one grid block), or "expand_one_block" (increase duration by one grid block)
- **Enable/disable**: enabled defaults to true; disabled Zones are ignored during resolution
- **Episode length constraint**: Programs in Patterns that resolve to episodes must have episode length ≤ grid block duration; the delta becomes an avail. This is enforced in Pattern/Program contracts and referenced here for completeness.

## Runtime & Validation Notes

This section defines critical runtime behavior and validation requirements that apply when Zones are used within SchedulePlan sessions or other operational contexts.

### Single Source of Truth

**All Zone validation is performed by the domain validator.** Higher layers (CLI, Planning Session, APIs) MUST call the same validator and MUST NOT re-implement rules.

- Zone validation logic is centralized in the domain layer
- CLI commands, Planning Session workflows, and API endpoints must delegate to the domain validator
- Re-implementing validation rules in higher layers violates the single source of truth principle and risks inconsistencies
- The domain validator enforces all invariants defined in the Validation & Invariants section
- Validation failures must propagate from the domain layer with consistent error messages

### Clock & Timezone

**All time math uses `MasterClock.now()` and the Channel's timezone.** Tests may inject a fake clock.

- Zone activation evaluation uses `MasterClock.now()` for current time queries
- All time calculations respect the Channel's timezone configuration
- Broadcast day calculations use `Channel.programming_day_start` relative to the Channel's timezone
- Tests must use a test clock (fake clock) for deterministic behavior
- Production code must never use system time directly; always use `MasterClock.now()`
- Timezone-aware datetime operations ensure correct handling of DST transitions and time offsets

### Time Normalization

**24:00 is stored as 23:59:59.999999 and normalized back to 24:00:00 in the domain layer.** Seconds/microseconds MUST be 00 for start/end (except normalized end-of-day).

- PostgreSQL TIME type cannot store 24:00:00, so end-of-day Zones are stored as 23:59:59.999999
- Domain layer normalizes stored values back to conceptual 24:00:00 for all operations
- Zone start_time and end_time must have seconds and microseconds set to 00 (except for normalized end-of-day)
- Round-trip persistence (write → read → domain) must preserve the conceptual 24:00:00 value
- Duration calculations and time comparisons use normalized values internally
- External interfaces (CLI, API) display and accept 24:00:00 as the canonical representation

### Activation Order

**Activation is evaluated strictly in this order:** enabled → effective date range → day_filters → time window.

- Zone activation checks must be evaluated in the specified sequence (fail-fast)
- If `enabled=false`, Zone is skipped immediately (no further checks)
- If date falls outside `effective_start`/`effective_end` range, Zone is skipped
- If `day_filters` is provided and date's day doesn't match, Zone is skipped
- If time window doesn't match the current time, Zone is inactive
- All checks must pass for Zone to be active
- Order is critical for performance optimization (disabled Zones fail fast)

### Determinism

**Given the same inputs (plan, channel grid, clock), Zone selection and expansion are deterministic.**

- Zone activation results must be identical for identical inputs
- Zone expansion (Pattern repeating) must produce the same schedule for the same inputs
- Deterministic behavior enables reproducible testing and predictable schedule generation
- Non-deterministic behavior (random selection, race conditions) must be explicitly avoided
- Test fixtures must provide deterministic inputs (fixed clock, fixed plan state, fixed grid configuration)
- ScheduleDay generation must be idempotent for the same inputs

### Plan Scope

**pattern_id MUST belong to the same plan_id as the Zone.** Cross-plan references are invalid.

- Zone `pattern_id` must reference a Pattern with the same `plan_id` as the Zone
- Cross-plan Pattern references are rejected at validation time
- This invariant ensures that Patterns and Zones are properly scoped within SchedulePlans
- Zone creation/update must validate Pattern-Plan consistency
- Pattern resolution must verify Plan membership before accepting the reference
- This constraint prevents accidental cross-plan dependencies and maintains plan isolation

## See Also

- [SchedulePlan](SchedulePlan.md) - Top-level operator-created plans that define channel programming (contain Zones)
- [Pattern](Pattern.md) - Ordered lists of Program references (referenced by Zones)
- [Program](Program.md) - Catalog entries in Patterns (expanded to concrete episodes at ScheduleDay time)
- [ScheduleDay](ScheduleDay.md) - Resolved schedules for specific channel and date (generated from Zones and Patterns)
- [Channel](Channel.md) - Channel configuration and timing policy (owns Grid: `grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`)
- [Scheduling](Scheduling.md) - High-level scheduling system
- [Operator CLI](../operator/CLI.md) - Operational procedures

Zone is a **named time window within the programming day** that declares when content should play. Zones are components of SchedulePlans and reference Patterns that define the content sequence. Zones do not hold episodes or assets directly — they declare **when** content should play and **which Pattern to use**. The plan engine applies the Pattern repeatedly across the Zone's active window until the Zone is full, snapping to the Channel's Grid boundaries. Zones use broadcast day time (00:00–24:00 relative to `programming_day_start`), not calendar day time. Zones can span midnight (e.g., `22:00–05:00`) within the same broadcast day and support optional day-of-week filters for recurring patterns. Zones flow into ScheduleDay via Pattern expansion during schedule resolution, with priority resolving overlapping Zones when multiple plans match.
