_Related: [Architecture](../architecture/ArchitectureOverview.md) • [SchedulePlan](SchedulePlan.md) • [Zone](Zone.md) • [Program](Program.md) • [ScheduleDay](ScheduleDay.md) • [Operator CLI](../operator/CLI.md)_

# Domain — Pattern

> **Note:** This document reflects the modern scheduling architecture. Active chain: **SchedulePlan (Zones + Patterns) → ScheduleDay (resolved) → PlaylogEvent (runtime) → AsRunLog.**

## Purpose

Pattern is an **ordered list of [Program](Program.md) references** (catalog entries such as series, movies, blocks, or composites). Patterns are components of [SchedulePlan](SchedulePlan.md) and are referenced by [Zone](Zone.md) entries to define the content sequence for time windows. Patterns have no durations — the plan engine repeats the Pattern across the Zone until the Zone is full, snapping to the Channel's Grid boundaries.

**What a Pattern is:**

- An ordered list of Program references (catalog entries)
- Referenced by Zones to define content sequences
- Has no durations — Programs determine their own block consumption
- Repeats cyclically across Zone time windows
- Defines **what** content plays (order and sequence)

**What a Pattern is not:**

- A time-block assignment (that's resolved at ScheduleDay time)
- A container with fixed durations (Programs determine block consumption)
- A single content item (Patterns contain multiple Program references)
- A schedule resolution (that's what ScheduleDay is)

Patterns are part of SchedulePlans. When a SchedulePlan is resolved into a [ScheduleDay](ScheduleDay.md), Patterns are expanded across their Zone's time windows. Programs in the Pattern are resolved to concrete episodes at ScheduleDay time, and the Pattern repeats until the Zone is full.

## Core Model / Scope

Pattern enables:

- **Content sequence definition**: Patterns define the order of Programs that should play
- **Repeating behavior**: Patterns repeat cyclically across Zone time windows
- **Program organization**: Patterns group related Programs into logical sequences
- **Zone association**: Each Pattern is referenced by one or more Zones to define their content sequences
- **Grid boundary snapping**: Pattern expansion snaps to the Channel's Grid boundaries during ScheduleDay resolution

**Key Points:**

- Pattern defines **what** content plays (ordered list of Programs)
- Pattern has no durations — Programs determine their own block consumption
- Pattern repeats cyclically across Zone time windows until the Zone is full
- Patterns are referenced by Zones to define content sequences
- Programs in Patterns are resolved to concrete episodes at ScheduleDay time
- Pattern expansion snaps to Channel Grid boundaries during ScheduleDay resolution

## Persistence Model

Pattern is managed by SQLAlchemy with the following fields:

- **id** (UUID, primary key): Unique identifier for relational joins and foreign key references
- **plan_id** (UUID, required, foreign key): Reference to parent [SchedulePlan](SchedulePlan.md)
- **name** (Text, optional): Human-readable identifier (e.g., "Prime Time Pattern", "Weekday Morning Pattern"). Optional for operator convenience.
- **description** (Text, optional): Human-readable description of the Pattern's programming intent
- **created_at** (DateTime(timezone=True), required): Record creation timestamp
- **updated_at** (DateTime(timezone=True), required): Record last modification timestamp

**Note:** Patterns do not store the ordered list of Programs directly. Instead, Programs reference Patterns via `pattern_id` and `order` fields. The ordered list is determined by querying Programs with the same `pattern_id`, ordered by `order`.

### Table Name

The table is named `patterns` (plural). Schema migration is handled through Alembic. Postgres is the authoritative backing store.

### Constraints

- `plan_id` must reference a valid SchedulePlan
- `name` must be unique within the SchedulePlan if provided (optional field)
- Patterns must have at least one Program reference (enforced via application logic, not database constraint)

### Relationships

Pattern has relationships with:

- **SchedulePlan** (many-to-one): Multiple Patterns belong to a single SchedulePlan
- **Zone** (one-to-many): One Pattern can be referenced by multiple Zones (though typically one Pattern per Zone)
- **Program** (one-to-many): Multiple Programs reference the Pattern via `Program.pattern_id` and `Program.order`

**Program Ordering:** Programs are ordered within a Pattern using the `order` field in the Program entity. Programs with the same `pattern_id` are ordered by `order` to determine the Pattern's sequence.

## Contract / Interface

Pattern is an ordered list of Program references. It defines:

- **Plan membership** (plan_id) - the SchedulePlan this Pattern belongs to
- **Program sequence** (via Programs with `pattern_id` and `order`) - the ordered list of Program references that define the content sequence
- **Name** (name, optional) - human-readable identifier for operator reference
- **Description** (description, optional) - metadata describing the Pattern's programming intent

Patterns have no durations — Programs determine their own block consumption. The plan engine repeats the Pattern across the Zone until the Zone is full, snapping to the Channel's Grid boundaries.

**Pattern Repeating:**
The plan engine expands Patterns by:

1. Taking the ordered list of Program references from the Pattern (ordered by `Program.order`)
2. Repeating the Pattern across the Zone's active window
3. Snapping to the Channel's Grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`)
4. Continuing until the Zone's declared end time is reached

**Program Resolution:**
Programs in Patterns are resolved to concrete episodes at ScheduleDay time:

- Series Programs resolve to specific episodes based on rotation policy
- Asset Programs resolve to the referenced asset
- VirtualAsset Programs expand to multiple assets
- Rule Programs resolve to assets selected from the filtered set

## Execution Model

Patterns are consumed during schedule generation:

1. **Zone Expansion**: When a Zone expands during ScheduleDay resolution, it retrieves its referenced Pattern
2. **Program Retrieval**: The system retrieves all Programs with `pattern_id` matching the Pattern, ordered by `order`
3. **Pattern Repeating**: The ordered list of Programs is repeated cyclically across the Zone's time window:
   - Take the first Program in the Pattern
   - Place it at the next valid Grid boundary
   - Move to the next Program in the Pattern
   - Continue repeating until the Zone's declared end time is reached
4. **Grid Alignment**: All Program placements snap to the Channel's Grid boundaries
5. **Program Resolution**: Each Program reference is resolved to concrete episodes/assets at ScheduleDay time
6. **Zone Completion**: Pattern repeating continues until the Zone's declared end time is reached (even if Pattern hasn't fully filled the Zone)

**Pattern Repeating Example:**

- Zone: `19:00–22:00` (Prime Time, 3 hours)
- Pattern: `["Cheers", "The Big Bang Theory"]` (ordered by `Program.order`)
- Result: The pattern repeats across the 3-hour window:
  - Cheers (episode 1) starts at 19:00, ends at 19:30
  - The Big Bang Theory (episode 1) starts at 19:30, ends at 20:00
  - Cheers (episode 2) starts at 20:00, ends at 20:30
  - The Big Bang Theory (episode 2) starts at 20:30, ends at 21:00
  - Cheers (episode 3) starts at 21:00, ends at 21:30
  - The Big Bang Theory (episode 3) starts at 21:30, ends at 22:00 (zone end)

**Key Point:** The pattern repeats cyclically until the Zone's declared end time (22:00) is reached. Each Program reference expands to a specific episode at ScheduleDay time, and the pattern continues repeating regardless of individual episode lengths (they snap to grid boundaries).

## Pattern Repeating Behavior

Patterns have no durations and repeat cyclically across Zone time windows. The repeating behavior:

1. **Cyclical Repeating**: Patterns repeat from the beginning once all Programs in the Pattern have been placed
2. **Grid Boundary Snapping**: Each Program placement snaps to the next valid Grid boundary
3. **Zone Completion**: Pattern repeating continues until the Zone's declared end time is reached
4. **Under-Fill Handling**: If a Pattern does not fully fill a Zone, the Zone ends at its declared end time, and under-filled time becomes avails

**Example: Cyclical Repeating**

- Pattern: `["A", "B", "C"]` (3 Programs)
- Zone: `00:00–06:00` (6 hours)
- Result: Pattern repeats twice:
  - First cycle: A at 00:00, B at 00:30, C at 01:00
  - Second cycle: A at 01:30, B at 02:00, C at 02:30
  - Third cycle: A at 03:00, B at 03:30, C at 04:00
  - Fourth cycle: A at 04:30, B at 05:00, C at 05:30
  - Zone ends at 06:00 (no fifth cycle needed)

**Example: Under-Fill**

- Pattern: `["Movie Block"]` (1 Program, 1.5 hours)
- Zone: `20:00–22:00` (2 hours)
- Result:
  - Movie Block plays 20:00–21:30
  - Zone ends at 22:00 as declared
  - 21:30–22:00 becomes avails (not filled by Pattern)

## Program Ordering

Programs are ordered within a Pattern using the `order` field in the Program entity. The ordering determines the sequence when the Pattern repeats.

**Ordering Rules:**

- Programs with the same `pattern_id` are ordered by `order` (ascending)
- `order` must be a non-negative integer
- Programs in a Pattern should have unique `order` values (enforced by application logic)
- The first Program in the Pattern has the lowest `order` value

**Example:**

- Pattern: "Prime Time Pattern"
- Programs:
  - Program A: `pattern_id="pattern-uuid"`, `order=0` (first)
  - Program B: `pattern_id="pattern-uuid"`, `order=1` (second)
  - Program C: `pattern_id="pattern-uuid"`, `order=2` (third)
- Pattern sequence: `["A", "B", "C"]` (ordered by `order`)

**Pattern Expansion:**
When a Pattern is expanded across a Zone, Programs are placed in order:

1. Program with `order=0` is placed first
2. Program with `order=1` is placed second
3. Program with `order=2` is placed third
4. Pattern repeats from `order=0` again

## Relationship to Zone

Patterns are referenced by Zones to define content sequences. The relationship:

- **Zone references Pattern**: Each Zone has a `pattern_id` that references a Pattern
- **Pattern defines content sequence**: The Pattern's ordered list of Programs defines what content plays
- **Zone defines time window**: The Zone's time window defines when the Pattern applies
- **Pattern expands across Zone**: The Pattern repeats across the Zone's time window until the Zone is full

**Zone-Pattern Flow:**

1. Zone declares time window (e.g., `19:00–22:00`)
2. Zone references Pattern (via `pattern_id`)
3. Pattern provides ordered list of Programs (e.g., `["Cheers", "The Big Bang Theory"]`)
4. Plan engine expands Pattern across Zone's time window
5. Programs are resolved to concrete episodes at ScheduleDay time

**Multiple Zones, One Pattern:**
A single Pattern can be referenced by multiple Zones (though typically one Pattern per Zone). This allows operators to reuse content sequences across different time windows.

**Example:**

- Pattern: "Classic Sitcoms" (`["Cheers", "Frasier", "Seinfeld"]`)
- Zone 1: "Weekday Morning" (`06:00–12:00`) references Pattern
- Zone 2: "Weekend Afternoon" (`12:00–18:00`) references same Pattern
- Result: Both Zones use the same content sequence, but at different times

## Relationship to ScheduleDay

Patterns flow into [ScheduleDay](ScheduleDay.md) via Zone expansion during schedule resolution:

1. **Zone Expansion**: Zones expand their referenced Patterns across Zone time windows
2. **Pattern Repeating**: Patterns repeat cyclically across Zone time windows until Zones are full
3. **Program Resolution**: Programs in Patterns are resolved to concrete episodes at ScheduleDay time
4. **Time Calculation**: Pattern repeating is combined with Zone time windows and Grid boundaries to produce real-world wall-clock times
5. **ScheduleDay Creation**: Resolved Zones, Patterns, and Programs become the resolved asset selections in ScheduleDay

**Example Flow:**

- Zone: 19:00–22:00 (Prime Time)
- Pattern: [Cheers (series Program), Movie Block (composite Program)]
- Resolution at ScheduleDay time: System expands Pattern over Zone, selects appropriate episodes for Cheers, resolves Movie Block to specific assets
- ScheduleDay: Contains resolved asset UUIDs with wall-clock times (e.g., 2025-12-25 19:00:00 UTC for Cheers episode S11E05)

ScheduleDays are resolved 3-4 days in advance for EPG and playout purposes, based on the Zones, Patterns, and Programs in the active SchedulePlan.

## Operator Workflows

**Create Pattern in Plan**: Operators create Patterns as ordered lists of Program references within SchedulePlans. They specify:

- Name (optional, for operator convenience)
- Description (optional, for documenting programming intent)
- Add Programs to the Pattern in the desired order

**Add Programs to Pattern**: Operators add Programs to Patterns by:

- Creating or selecting Programs
- Setting `pattern_id` to reference the Pattern
- Setting `order` to determine sequence within the Pattern

**Edit Pattern**: Operators modify existing Patterns by:

- Updating name or description
- Reordering Programs (changing `order` values)
- Adding or removing Programs

**Preview Pattern**: Operators preview how a Pattern will resolve:

- See how Programs repeat across a Zone's time window
- View grid alignment and timing
- Check for conflicts or rule violations

**Reuse Patterns**: Operators reuse Patterns across multiple Zones:

- Create a Pattern once
- Reference it from multiple Zones
- Update the Pattern to affect all referencing Zones

## Examples

### Example 1: Simple Pattern

**Prime Time Pattern:**

- Name: "Prime Time Pattern"
- Description: "Evening drama and movies"
- Programs (ordered):
  - Program A: `order=0`, "Drama Series"
  - Program B: `order=1`, "Movie Block"
- Usage: Referenced by Zone "Prime Time" (19:00–22:00)
- Result: Pattern repeats across prime time window: Drama, Movie, Drama, Movie, etc.

### Example 2: Repeating Sitcom Pattern

**Classic Sitcoms Pattern:**

- Name: "Classic Sitcoms"
- Description: "Rotating classic sitcoms"
- Programs (ordered):
  - Program A: `order=0`, "Cheers" (series)
  - Program B: `order=1`, "Frasier" (series)
  - Program C: `order=2`, "Seinfeld" (series)
- Usage: Referenced by Zone "Base" (00:00–24:00)
- Result: Pattern repeats across full day: Cheers, Frasier, Seinfeld, Cheers, Frasier, Seinfeld, etc.

### Example 3: Weighted Pattern

**Weighted Pattern (via Program order repetition):**

- Name: "Morning Block"
- Description: "More news, less weather"
- Programs (ordered):
  - Program A: `order=0`, "News" (series)
  - Program B: `order=1`, "News" (series) - duplicate reference for weighting
  - Program C: `order=2`, "Weather" (series)
- Usage: Referenced by Zone "Morning" (06:00–09:00)
- Result: Pattern repeats with News appearing twice as often as Weather: News, News, Weather, News, News, Weather, etc.

**Note:** Weighted patterns are achieved by repeating Program references in the Pattern's order sequence. Each Program reference is independent, so the same series can appear multiple times with different `order` values.

### Example 4: Movie Block Pattern

**Movie Block Pattern:**

- Name: "Movie Block"
- Description: "Feature films"
- Programs (ordered):
  - Program A: `order=0`, "Movie Block" (rule-based, selects movies 90-150 minutes)
- Usage: Referenced by Zone "Weekend Afternoon" (12:00–18:00)
- Result: Pattern repeats across weekend afternoons, selecting different movies for each slot

## Failure / Fallback Behavior

If Patterns are missing or invalid:

- **Missing Patterns**: Result in gaps in the schedule (allowed but should generate warnings). Zones without valid Patterns cannot be expanded.
- **Empty Patterns**: Patterns with no Program references generate a scheduling error at resolution time; Zone expansion skips with logged warning but does not block ScheduleDay generation
- **Invalid Program references**: System falls back to default content or skips the Program entry
- **Invalid order values**: System orders Programs by `order` ascending, handling missing or duplicate values gracefully

## Naming Rules

The canonical name for this concept in code and documentation is Pattern.

Patterns are often referred to as "content sequences" or "program sequences" in operator workflows, but the full name should be used in technical documentation and code.

## Validation & Invariants

- **Valid Plan reference**: plan_id must reference a valid SchedulePlan
- **Name uniqueness**: name must be unique within the SchedulePlan if provided (optional field)
- **At least one Program**: Patterns should have at least one Program reference (enforced via application logic)
- **Program order validity**: Programs in a Pattern should have unique, non-negative `order` values
- **Zone reference validity**: Patterns referenced by Zones must belong to the same SchedulePlan as the Zone
- **Plan consistency**: All Programs that reference a Pattern must belong to the same SchedulePlan as that Pattern (enforced as invariant)
- **Pattern durationlessness**: Patterns never define duration, block size, or grid alignment directly — those are determined by Programs and the Channel grid

## Runtime & Validation Notes

This section defines critical runtime behavior and validation requirements that apply when Patterns are used within SchedulePlan sessions or other operational contexts.

### Single Source of Truth

**Pattern validation is enforced in the domain; callers MUST reuse the same validator.**

- Pattern validation logic is centralized in the domain layer
- CLI commands, Planning Session workflows, and API endpoints must delegate to the domain validator
- Re-implementing validation rules in higher layers violates the single source of truth principle and risks inconsistencies
- The domain validator enforces all invariants defined in the Validation & Invariants section
- Validation failures must propagate from the domain layer with consistent error messages

### No Durations

**Pattern never carries durations or grid info; Programs and Channel grid define these.**

- Patterns have no duration fields (no `duration`, `block_size`, or grid alignment fields)
- Pattern expansion uses Program durations (from Program catalog entries)
- Grid alignment is determined by the Channel's Grid configuration (`grid_block_minutes`, `block_start_offsets_minutes`)
- Pattern repeating behavior is determined by Program block consumption and Channel grid boundaries
- Duration calculations occur at ScheduleDay resolution time, not at Pattern creation time
- Pattern operations (create, update, list, show) work with Program references, not durations

### Plan Scope

**All Programs referencing a Pattern MUST belong to the same plan_id as the Pattern (or be explicitly plan-agnostic per Program spec).**

- Pattern `plan_id` defines the Plan scope for the Pattern
- Programs with `pattern_id` referencing a Pattern must have matching `plan_id` (unless Program spec explicitly allows plan-agnostic Programs)
- Cross-plan Program references are rejected at validation time (unless plan-agnostic Programs are supported)
- This invariant ensures that Patterns and Programs are properly scoped within SchedulePlans
- Pattern creation/update must validate Program-Plan consistency
- Program addition to Patterns must verify Plan membership before accepting the reference
- This constraint prevents accidental cross-plan dependencies and maintains plan isolation

### Determinism

**Given the same Program order and rotation policy, expansion is deterministic.**

- Pattern repeating must produce identical results for identical inputs (same Program order, same rotation policies)
- Program ordering within Patterns must be deterministic (ordered by `order` field)
- Program resolution at ScheduleDay time must be deterministic (based on rotation policies and rules)
- Series Programs with rotation policies (sequential, syndication, etc.) must produce deterministic episode selection
- Non-deterministic behavior (random selection without seed, race conditions) must be explicitly avoided
- Test fixtures must provide deterministic inputs (fixed Program order, fixed rotation state, fixed grid configuration)
- ScheduleDay generation from Patterns must be idempotent for the same inputs

### Empty Patterns

**At resolution time, empty Patterns cause a scheduling error; the Zone expansion is skipped with a warning, but ScheduleDay generation continues.**

- Empty Patterns (no Programs) are valid at creation time (Pattern can be created without Programs)
- At ScheduleDay resolution time, empty Patterns cause a scheduling error (logged)
- Zones referencing empty Patterns skip expansion with a warning
- ScheduleDay generation continues even if some Zones reference empty Patterns (non-blocking)
- Application logic should encourage operators to add Programs to Patterns before resolution
- Pattern validation should warn (not error) on empty Patterns during creation, but error at resolution time

## See Also

- [Scheduling Invariants](../contracts/resources/SchedulingInvariants.md) - Cross-cutting scheduling invariants
- [SchedulePlan](SchedulePlan.md) - Top-level operator-created plans that define channel programming (contain Patterns)
- [Zone](Zone.md) - Named time windows that reference Patterns (define when Patterns apply)
- [Program](Program.md) - Catalog entries in Patterns (ordered by `order`, expanded to concrete episodes at ScheduleDay time)
- [ScheduleDay](ScheduleDay.md) - Resolved schedules for specific channel and date (generated from Zones and Patterns)
- [Channel](Channel.md) - Channel configuration and timing policy (owns Grid: `grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`)
- [Scheduling](Scheduling.md) - High-level scheduling system
- [Operator CLI](../operator/CLI.md) - Operational procedures

Pattern is an **ordered list of Program references** (catalog entries such as series, movies, blocks, or composites). Patterns are components of SchedulePlans and are referenced by Zones to define content sequences. Patterns have no durations — the plan engine repeats the Pattern across the Zone until the Zone is full, snapping to the Channel's Grid boundaries. Programs in Patterns are resolved to concrete episodes at ScheduleDay time, and the Pattern repeats cyclically across Zone time windows. Patterns flow into ScheduleDay via Zone expansion during schedule resolution, with Programs ordered by `order` to determine the sequence.
