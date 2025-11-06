_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md) • [Contracts](../contracts/README.md) • [ScheduleDay](ScheduleDay.md) • [Program](Program.md)_

# Domain — SchedulePlan

> **Note:** This document reflects the modern scheduling architecture.  
> The active scheduling chain is: **SchedulePlan → ScheduleDay → PlaylogEvent → AsRunLog.**

## Purpose

SchedulePlan is the **top-level unit of channel programming**. It is the **single source of scheduling logic** for channel programming. Each SchedulePlan defines one or more **Zones** (named time windows within the programming day) and a **Pattern** for each Zone.

**Zones + Patterns Model:**
- **Zone**: Declares when it applies (e.g., base 00:00–24:00, or After Dark 22:00–05:00) and references a Pattern. Zones do not hold episodes or assets.
- **Pattern**: An ordered list of [Program](Program.md) entries (catalog entries such as series, movies, blocks, or composites). No durations inside the pattern. The plan engine repeats the pattern over the Zone until the Zone is full.

SchedulePlans are layered by priority and can be overridden (e.g., weekday vs. holiday), with more specific layers overriding more generic ones. Plans are channel-bound and span repeating or one-time timeframes. Superseded plans are archived rather than deleted. Plan-based scheduling flows into [ScheduleDay](ScheduleDay.md), which is resolved 3-4 days in advance for EPG and playout purposes.

**Key Points:**
- SchedulePlan is the **top-level unit of channel programming** — the authoritative source for all scheduling decisions
- Each plan defines one or more **Zones** (named time windows within the programming day)
- Each Zone references a **Pattern** (ordered list of Programs)
- **Programs** are catalog entries (series, movie, block, composite) that can reference [VirtualAssets](VirtualAsset.md)
- Patterns have no durations — the plan engine repeats the pattern over the Zone until the Zone is full
- Episodes are resolved automatically at ScheduleDay time based on rotation policy
- Plans are channel-bound and span repeating or one-time timeframes
- Plans are layered with more specific plans (e.g., holidays) overriding generic ones (e.g., weekdays)
- All scheduling logic is defined directly in SchedulePlan
- Plan-based scheduling flows into ScheduleDay, resolved 3-4 days in advance for EPG and playout

## Core Model / Scope

SchedulePlan is the **top-level unit of channel programming** and the **single source of scheduling logic** for channel programming. It defines one or more **Zones** (named time windows within the programming day) and a **Pattern** for each Zone. It is a reusable planning construct that:

- **Top-level unit of channel programming**: SchedulePlan is the authoritative source for all scheduling decisions
- **Defines Zones**: Each plan defines one or more Zones (named time windows within the programming day, e.g., base 00:00–24:00, or After Dark 22:00–05:00)
- **Defines Patterns per Zone**: Each Zone references a Pattern (ordered list of [Program](Program.md) entries). Patterns have no durations — the plan engine repeats the pattern over the Zone until the Zone is full
- **Programs are catalog entries**: [Program](Program.md) entries in Patterns are schedulable entities such as series, movies, blocks, or composites (can reference [VirtualAssets](VirtualAsset.md))
- **Episode resolution**: Episodes are resolved automatically at ScheduleDay time based on rotation policy
- **Zone-based time windows**: Zones declare when they apply (e.g., base 00:00–24:00, or After Dark 22:00–05:00) but do not hold episodes or assets
- **Is channel-bound**: Plans are bound to specific channels and span repeating or one-time timeframes
- **Supports layering and overrides**: Plans are layered by priority and can be overridden (e.g., weekday vs. holiday), with more specific layers overriding more generic ones
- **Is timeless but date-bound**: Plans are timeless (reusable patterns) but bound by effective date ranges (start_date, end_date). Superseded plans are archived (`is_active=false`) rather than deleted
- **Flows into ScheduleDay**: Plan-based scheduling flows into [ScheduleDay](ScheduleDay.md), which is resolved 3-4 days in advance for EPG and playout purposes

## Persistence Model

SchedulePlan is managed by SQLAlchemy with the following fields:

- **id** (UUID, primary key): Unique identifier for relational joins and foreign key references
- **name** (Text, required, unique): Plan identifier (e.g., "WeekdayPlan", "ChristmasPlan", "SummerBlock")
- **description** (Text, optional): Human-readable description of the plan's programming intent
- **cron_expression** (Text, optional): Cron-style expression defining when this plan is active (e.g., "0 6 * * MON-FRI" for weekdays 6am)
- **start_date** (Date, optional): Start date for plan validity (inclusive, can be year-agnostic)
- **end_date** (Date, optional): End date for plan validity (inclusive, can be year-agnostic)
- **priority** (Integer, required, default: 0): Priority for layering; higher priority plans override lower priority plans
- **is_active** (Boolean, required, default: true): Plan operational status; only active plans are eligible for use
- **created_at** (DateTime(timezone=True), required): Record creation timestamp
- **updated_at** (DateTime(timezone=True), required): Record last modification timestamp

SchedulePlan has one-to-many relationships with:

- **Zone**: Multiple Zones can exist within a single plan, each defining a time window and Pattern reference
- **Pattern**: Multiple Patterns can exist within a single plan, each defining an ordered list of Program references
- **BroadcastScheduleDay**: Plans are used to generate resolved schedule days

### Table Name

The table is named `schedule_plans` (plural). Schema migration is handled through Alembic. Postgres is the authoritative backing store.

### Constraints

- `name` must be unique across all plans
- `name` max length ≤ 255 characters (enforced at database level)
- `description` max length is database-dependent (typically unlimited for TEXT)
- `priority` must be non-negative (default: 0)
- `start_date` and `end_date` must be valid dates if provided
- `cron_expression` must be valid cron syntax if provided

### Layering and Priority Rules

SchedulePlans use priority-based layering where plans are matched by effective dates, with more specific layers overriding more generic ones. Plans can be layered and overridden (e.g., weekday vs. holiday):

- Plans with higher `priority` values override plans with lower `priority` values when both are active and match the same date
- When multiple plans match (via cron_expression or date range), the highest priority plan is used
- More specific plans (e.g., holiday-specific plans like "ChristmasPlan") should have higher priority than general plans (e.g., "WeekdayPlan") to enable overrides
- Plans are channel-bound and span repeating or one-time timeframes
- Plans are timeless but bound by effective date ranges (`start_date`, `end_date`)
- Superseded plans are archived (`is_active=false`) rather than deleted, preserving history

## Contract / Interface

SchedulePlan is the **single source of scheduling logic** for channel programming. It defines one or more **Zones** (named time windows within the programming day) and a **Pattern** for each Zone. It defines:

- Plan identity and metadata (name, description)
- Channel binding - plans are channel-bound and span repeating or one-time timeframes
- Temporal validity (cron_expression, start_date, end_date) - plans are timeless but bound by effective date ranges
- Priority for layering (priority) - enables plan layering by priority where more specific plans (e.g., holidays) override generic ones (e.g., weekdays)
- Operational status (is_active) - superseded plans are archived rather than deleted
- **Zones** - named time windows within the programming day (e.g., base 00:00–24:00, or After Dark 22:00–05:00)
- **Patterns** - ordered lists of [Program](Program.md) entries for each Zone. Patterns have no durations — the plan engine repeats the pattern over the Zone until the Zone is full

**Zones + Patterns Model:**
- **Zone**: Declares when it applies (e.g., base 00:00–24:00, or After Dark 22:00–05:00) and references a Pattern. Zones do not hold episodes or assets.
- **Pattern**: An ordered list of [Program](Program.md) entries (catalog entries such as series, movies, blocks, or composites). No durations inside the pattern. The plan engine repeats the pattern over the Zone until the Zone is full.
- **Program (catalog)**: A schedulable entity such as a series, movie, block, or composite (can reference a [VirtualAsset](VirtualAsset.md)). Episodes are resolved automatically at ScheduleDay time based on rotation policy.

Plans are timeless and reusable by design. They define Zones and Patterns for recurring patterns (e.g., weekdays, holidays, seasons) or one-time events. All scheduling logic is defined directly in SchedulePlan.

Content selection can include regular assets or VirtualAssets. Plan-based scheduling flows into [ScheduleDay](ScheduleDay.md), which is resolved 3-4 days in advance for EPG and playout purposes. ScheduleDays are then used to generate [PlaylogEvent](PlaylogEvent.md) records for actual playout execution.

## Execution Model

SchedulePlan is the **single source of scheduling logic** for channel programming. ScheduleService and schedule generation logic consume SchedulePlan records to determine actual content selections. Plan-based scheduling flows into ScheduleDay, which is resolved 3-4 days in advance:

1. **Identify active plans**: For a given channel and date, determine which plans are active based on cron_expression, effective date ranges (start_date, end_date), and is_active status. Plans are channel-bound and span repeating or one-time timeframes
2. **Resolve layering and overrides**: Apply plan layering by priority - if multiple plans match, select the plan with the highest priority. More specific plans (e.g., holidays) override generic ones (e.g., weekdays)
3. **Resolve Zones and Patterns**: For each active plan, identify its Zones (time windows with optional day filters) and their associated Patterns (ordered lists of Program references). Zones + Patterns repeat to fill each Zone's active window, snapping to the Channel's Grid boundaries. Apply conflict resolution (soft-start-after-current) when Zones open while content is playing
4. **Generate BroadcastScheduleDay**: Resolve the plan into a concrete [BroadcastScheduleDay](ScheduleDay.md) for the specific channel and date (resolved 3-4 days in advance for EPG and playout purposes). This is the primary expansion point where Programs → concrete episodes and VirtualAssets → real assets
5. **Generate PlaylogEvents**: From the resolved ScheduleDay, generate [BroadcastPlaylogEvent](PlaylogEvent.md) records for actual playout execution
6. **Validate Zones, Patterns, and Programs**: Ensure all Zones, Patterns, and Programs are valid and consistent

## Zones and Patterns

Zones and Patterns are the core contents of a SchedulePlan. A plan defines one or more Zones, and each Zone references a Pattern that repeats to fill the Zone's time window.

### Zone

A Zone defines a named time window within the programming day with the following components:

- **Name**: A human-readable identifier (e.g., "Base", "After Dark", "Prime Time", "Weekend Morning")
- **Active window**: The time range when the Zone applies (e.g., `00:00–24:00`, `22:00–05:00`, `19:00–22:00`)
- **Optional day filters**: Day-of-week constraints (e.g., Mon–Fri, Sat–Sun) that restrict when the Zone is active
- **Pattern reference**: A pointer to a Pattern that defines the content sequence for this Zone

Zones do not hold episodes or assets directly. They declare when content should play and which Pattern to use. The plan engine applies the Pattern repeatedly across the Zone's active window until the Zone is full, snapping to the Channel's Grid boundaries.

**Examples:**
- Base zone: `00:00–24:00` (full programming day) with no day filters
- After Dark zone: `22:00–05:00` (spans midnight) with no day filters
- Prime Time zone: `19:00–22:00` with no day filters
- Weekend Morning zone: `06:00–12:00` with day filter `Sat–Sun`

**Zone Alignment Note:**

Zones align to **broadcast days**, not calendar days. The broadcast day is defined by the Channel's `programming_day_start` (e.g., 06:00). A Zone like `22:00–05:00` spans from 22:00 on one calendar day to 05:00 the next calendar day, but both times are within the same broadcast day (e.g., 06:00 to 06:00 next day).

**Key Points:**
- Zones use broadcast day time (00:00–24:00 relative to `programming_day_start`)
- Long content can bridge the broadcast day boundary without truncation
- For example, a movie starting at 23:00 can continue past midnight (00:00) and into the next calendar day's early hours (e.g., until 01:30) without being cut
- The carry-in policy ensures content that crosses the programming-day seam continues into the next broadcast day until completion

### Pattern

A Pattern is an ordered list of [Program](Program.md) references (catalog entries such as series, movies, blocks, or composites). Patterns have no durations — the plan engine repeats the Pattern across the Zone until the Zone is full.

**Pattern Repeating:** The plan engine:
1. Takes the ordered list of Program references from the Pattern
2. Repeats the Pattern across the Zone's active window
3. Snaps to the Channel's Grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`)
4. Continues until the Zone is full

**Examples:**

**Base zone with pattern:**
- Zone: `00:00–24:00` (Base)
- Pattern: `["Cheers", "The Big Bang Theory"]`
- Result: The pattern repeats across the full 24-hour day, with each Program (series) expanding to episodes at ScheduleDay time

**Weekend zone overriding base:**
- Zone: `00:00–24:00` (Weekend) with day filter `Sat–Sun`
- Pattern: `["Movie Block"]`
- Result: On weekends, this Zone overrides the base Zone, replacing the series pattern with a movie block pattern

**Pattern repeating behavior (crystal clear example):**
- Zone: `19:00–22:00` (Prime Time, 3 hours)
- Pattern:
  - Cheers
  - The Big Bang Theory
  repeat: true
- Result: The pattern auto-repeats until the zone duration is filled, regardless of episode length:
  - Cheers (episode 1) starts at 19:00, ends at 19:30
  - The Big Bang Theory (episode 1) starts at 19:30, ends at 20:00
  - Cheers (episode 2) starts at 20:00, ends at 20:30
  - The Big Bang Theory (episode 2) starts at 20:30, ends at 21:00
  - Cheers (episode 3) starts at 21:00, ends at 21:30
  - The Big Bang Theory (episode 3) starts at 21:30, ends at 22:00 (zone end)
- **Key Point:** The pattern repeats cyclically until the Zone's declared end time (22:00) is reached. Each Program reference expands to a specific episode at ScheduleDay time, and the pattern continues repeating regardless of individual episode lengths (they snap to grid boundaries).

**Conflict Resolution:**

When a Zone opens while content is already playing (e.g., a Zone starts at 19:00 but a program from a previous Zone is still running), the system applies the **soft-start-after-current** policy:

- The current program continues to completion
- The new Zone's Pattern starts at the next valid Grid boundary after the current program ends
- This ensures clean transitions and prevents mid-program interruptions

This policy is applied automatically during ScheduleDay generation to handle Zone transitions gracefully.

### Temporality

Plans are **reusable and timeless** — they define Zones and Patterns that can be applied to any day. Plans are not tied to specific dates in their structure; instead:

- Plans define the **pattern** of programming (Zones + Patterns)
- Plans are **applied per day** to generate [ScheduleDay](ScheduleDay.md) records
- The same plan can generate different ScheduleDays for different dates (e.g., different episodes selected based on rotation policy)
- Plans remain unchanged as they are applied across multiple days

This timeless design allows operators to create reusable programming plans (e.g., "WeekdayPlan", "HolidayPlan") that are applied automatically based on date matching (via `cron_expression` or `start_date`/`end_date`).

## Failure / Fallback Behavior

If plans are missing or invalid:

- The system falls back to the most recent valid plan or default programming
- ScheduleService skips plans where `is_active=false`
- Missing or invalid programs result in gaps (allowed but should generate warnings)
- Invalid programs (e.g., violating optional constraints) should be flagged during validation

## Scheduling Model

- **Single source of scheduling logic**: SchedulePlan is the single source of scheduling logic for channel programming
- **Zones + Patterns model**: Each plan defines one or more Zones (time windows) and Patterns (ordered lists of Programs) for each Zone
- **Grid alignment**: All scheduling snaps to the Channel's Grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`)
- **Pattern repeating**: Patterns have no durations — the plan engine repeats the pattern over the Zone until the Zone is full
- **Programs are catalog entries**: Programs in Patterns are schedulable entities (series, movies, blocks, composites) without durations
- **Episode resolution**: Episodes are resolved automatically at ScheduleDay time based on rotation policy
- **Channel-bound**: Plans are channel-bound and span repeating or one-time timeframes
- **Layering and overrides**: Plans are layered by priority and can be overridden (e.g., weekday vs. holiday), with more specific layers overriding generic ones
- **Content selection**: Content selection can include regular assets or VirtualAssets
- **Timeless but date-bound**: Plans are timeless (reusable patterns) but bound by effective date ranges
- **Archival**: Superseded plans are archived (`is_active=false`) rather than deleted
- **Flows to ScheduleDay**: Plan-based scheduling flows into ScheduleDay, resolved 3-4 days in advance for EPG and playout. ScheduleDay is the primary expansion point for Programs → episodes and VirtualAssets → assets
- **Self-contained**: Plans are self-contained and directly define channel programming
- **Operator control**: Operators choose what to place in Zones and Patterns, but may request system suggestions
- **Validation**: Dry run and validation features should be supported to visualize gaps or rule violations

## Lifecycle and Referential Integrity

- `is_active=false` archives the plan: ScheduleService excludes the plan from schedule generation. Existing Zones and Patterns remain but are ignored.
- Hard delete is only permitted when no dependent rows exist (e.g., Zone, Pattern, BroadcastScheduleDay). When dependencies exist, prefer archival (`is_active=false`).
- The dependency preflight MUST cover: Zone, Pattern, BroadcastScheduleDay, and any EPG/playlog references that depend on the plan.

## Operator Workflows

**Create Plan**: Define a new plan that defines channel programming using Zones and Patterns. Specify name, temporal validity (cron/date range), and priority. Plans are the top-level object and are self-contained.

**Define Zones**: Create Zones (time windows within the programming day) for the plan. Specify name, active window (e.g., `00:00–24:00`, `22:00–05:00`), optional day filters (e.g., Mon–Fri), and a Pattern reference. Examples: base 00:00–24:00, After Dark 22:00–05:00, Prime Time 19:00–22:00, Weekend Morning 06:00–12:00 (Sat–Sun).

**Define Patterns**: Create Patterns (ordered lists of Program references) for each Zone. Patterns have no durations — Zones + Patterns repeat to fill the Zone's active window.

**Manage Program References in Patterns**: Add, modify, or remove Program references (catalog entries) within Patterns. Programs are schedulable entities such as series, movies, blocks, or composites.

**Layer Plans**: Create multiple plans with different priorities and effective date ranges to handle recurring patterns (weekdays, weekends, holidays, seasons) or one-time timeframes. Use plan layering by priority where more specific plans override generic ones. Plans can be layered and overridden (e.g., weekday vs. holiday).

**Preview Schedule**: Use dry-run or preview features to visualize how a plan's Zones and Patterns will resolve into a BroadcastScheduleDay.

**Validate Plan**: Check for gaps, rule violations, or conflicts before activating the plan. Ensure Zones align with Grid boundaries and Patterns are valid.

**Override Plans**: Use higher-priority plans to override general plans for specific dates or patterns. For example, a "HolidayPlan" can override a "WeekdayPlan" on holidays, or a "ChristmasPlan" can override a "WeekdayPlan" on December 25.

**Archive Plans**: Archive plans (`is_active=false`) that are superseded rather than deleting them, preserving history. Plans are timeless but bound by effective date ranges, so superseded plans should be archived.

### Invocation

SchedulePlan operations can be invoked either via CLI or programmatically:

**CLI Example:**

```bash
retrovue schedule plan build --channel-id=1 --date=2025-11-07
```

**Programmatic Example:**

```python
from retrovue.app.schedule import build_schedule_plan
build_schedule_plan(channel_id=1, date=date(2025, 11, 7))
```

### CLI Command Examples

**Create Plan**: Use `retrovue schedule-plan add` (or `retrovue plan add`) with required parameters:

```bash
retrovue schedule-plan add --name "WeekdayPlan" \
  --description "Weekday programming plan" \
  --cron "0 6 * * MON-FRI" \
  --priority 10
```

**List Plans**: Use `retrovue schedule-plan list` to see all plans in table format, or `retrovue schedule-plan list --json` for machine-readable output.

**Show Plan**: Use `retrovue schedule-plan show --id <uuid>` or `retrovue schedule-plan show --name <name>` to see detailed plan information including associated programs.

**Add Program Reference to Pattern**: Use `retrovue channel plan <channel> <plan> pattern <pattern> program add` to add a Program reference (catalog entry) to a Pattern:

```bash
retrovue channel plan <channel> <plan> pattern <pattern> program add \
  --series "Tom & Jerry" \
  --episode-policy sequential
```

**Preview Schedule**: Use `retrovue schedule-plan preview --plan-id <uuid> --date 2025-12-25` to see how a plan resolves for a specific date.

**Validate Plan**: Use `retrovue schedule-plan validate --plan-id <uuid>` to check for gaps, rule violations, or conflicts.

**Activate/Deactivate**: Use `retrovue schedule-plan update --id <uuid> --active` or `--inactive` to toggle is_active status.

**Update Plan**: Use `retrovue schedule-plan update --id <uuid>` with any combination of fields to modify plan properties.

**Delete Plan**: Use `retrovue schedule-plan delete --id <uuid>` to permanently remove a plan (only if no dependencies exist).

All operations use UUID identifiers for plan identification. The CLI provides both human-readable and JSON output formats.

**Build and Preview Commands:**

```bash
retro schedule plan build <channel>
retro schedule plan preview <channel> --date 2025-11-06
```

**Note:** These commands share the same backend functions as the UI scheduler, so both interfaces produce identical results. This ensures consistency between CLI and UI operations and helps future developers understand that CLI and UI are two faces of the same logic layer.

### Operator CLI → Planning Mode

Planning Mode provides an interactive REPL (Read-Eval-Print Loop) for building and editing SchedulePlans. This mode allows operators to iteratively construct plans with immediate feedback and validation.

**Enter Planning Mode:**

```bash
retrovue plan build <channel-slug> --name <PlanName>
```

Upon entering planning mode, the shell prompt changes to indicate the active plan context:

```
(plan:<PlanName>)>
```

**REPL Commands:**

Within the Planning Mode REPL, the following commands are available:

- **`zone add <name> --from HH:MM --to HH:MM [--days MON..SUN]`**
  - Creates a new Zone with the specified name and time window
  - Optional `--days` parameter restricts the Zone to specific days of the week (e.g., `MON..FRI`, `SAT..SUN`)
  - All times snap to the Channel's grid boundaries

- **`pattern set <zone> "<ProgramA>,<ProgramB>,..."`**
  - Sets the Pattern for the specified Zone
  - Takes a comma-separated list of Program names
  - The Pattern repeats to fill the Zone's time window

- **`pattern weight <zone> "<A>,<A>,<B>..."`**
  - Sets a weighted Pattern for the specified Zone
  - Allows repeating Program references to control frequency (e.g., Program A appears twice for every one instance of Program B)
  - The weighted Pattern repeats to fill the Zone's time window

- **`program create <name> --type series|movie|block [--rotation random|sequential|lru] [--slot-units N]`**
  - Creates a new Program catalog entry
  - `--type` specifies the Program type (series, movie, or block)
  - `--rotation` specifies episode selection policy for series (random, sequential, or least-recently-used)
  - `--slot-units` overrides the default block count for longform content (e.g., a 2-hour movie on a 30-minute grid would use `--slot-units 4`)

- **`validate`**
  - Performs validation checks on the current plan
  - Checks grid alignment, zone overlaps, and policy compliance
  - Reports any issues or conflicts before saving

- **`preview day YYYY-MM-DD`**
  - Generates a preview of how the current plan resolves for the specified date
  - Shows the first 12 hours rolled from the current Plan
  - Compiles to a ScheduleDay draft (not persisted) using the same resolution rules used in production
  - Demonstrates how Zones, Patterns, and Programs expand into concrete schedule entries

- **`save`**
  - Saves the current plan and exits Planning Mode
  - Persists all Zones, Patterns, and Programs to the database
  - Returns to the normal shell prompt

- **`discard`**
  - Discards all changes made in Planning Mode and exits
  - No changes are persisted to the database
  - Returns to the normal shell prompt

- **`quit`**
  - Exits Planning Mode without saving
  - Prompts for confirmation if unsaved changes exist
  - Returns to the normal shell prompt

**Behavior:**

- **Grid Alignment**: All entries snap to the Channel grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`)
- **Pattern Repeating**: Patterns repeat to fill Zone windows, with each Program reference expanding at ScheduleDay time
- **Preview Compilation**: The `preview day` command compiles to a ScheduleDay draft using the same resolution rules as production:
  - Zones expand their Patterns across the Zone's window
  - Programs resolve to concrete episodes/assets based on rotation policy
  - Grid alignment, soft-start-after-current, fixed zone end, no mid-longform cuts, and carry-in policies are all applied
  - The preview is not persisted but shows exactly how the plan will resolve

**Parity for UI:**

The Planning Mode REPL commands have equivalent function calls that the UI will use:

- **`PlanAPI.addZone(channelId, planId, zoneName, fromTime, toTime, dayFilters?)`** - Equivalent to `zone add`
- **`PlanAPI.setPattern(channelId, planId, zoneName, programNames[])`** - Equivalent to `pattern set`
- **`PlanAPI.setWeightedPattern(channelId, planId, zoneName, weightedPrograms[])`** - Equivalent to `pattern weight`
- **`ProgramAPI.create(name, type, rotation?, slotUnits?)`** - Equivalent to `program create`
- **`PlanAPI.validate(channelId, planId)`** - Equivalent to `validate`
- **`PlanAPI.previewDay(channelId, planId, date)`** - Equivalent to `preview day`
- **`PlanAPI.save(channelId, planId)`** - Equivalent to `save`
- **`PlanAPI.discard(channelId, planId)`** - Equivalent to `discard`

The UI will provide the same functionality through a visual interface, calling these underlying API functions. The Planning Mode REPL and UI share the same validation, preview, and resolution logic.

## Validation & Invariants

- **Name uniqueness**: `name` must be unique across all plans (enforced at database level)
- **Active status**: Only plans where `is_active=true` are eligible for schedule generation
- **Zone coverage**: Plans should have Zones covering the programming day, though gaps are allowed (with warnings)
- **Pattern validity**: Patterns must contain valid Programs (catalog entries)
- **Grid alignment**: Zones must align with the Channel's Grid boundaries
- **Referential integrity**: Plans cannot be deleted if they have dependent Zones, Patterns, or BroadcastScheduleDay records
- **Zones and Patterns define scheduling**: Zones define *when* by window; Patterns define *what order* (Programs). Patterns have **no durations** and repeat to fill the Zone, snapping to the Channel Grid.

## Out of Scope (v0.1)

- Plan versioning and effective-dated changes
- Plan inheritance or composition
- Automatic content suggestion algorithms (though operators may request suggestions)
- Ad pod composition and overlay timing within assignments
- Real-time plan modification during active broadcast

## See Also

- [Scheduling](Scheduling.md) - High-level scheduling system
- [ScheduleDay](ScheduleDay.md) - Resolved schedules for specific channel and date
- [Program](Program.md) - Catalog entities (series/movie/block) referenced by patterns; episodes resolved at ScheduleDay
- [Channel](Channel.md) - Channel configuration and timing policy
- [Asset](Asset.md) - Approved content available for scheduling
- [PlaylogEvent](PlaylogEvent.md) - Generated playout events
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures

SchedulePlan is the **single source of scheduling logic** for channel programming. Each SchedulePlan defines one or more **Zones** (named time windows with optional day filters) and a **Pattern** for each Zone. **Zones** declare when they apply (e.g., base 00:00–24:00, or After Dark 22:00–05:00) and reference a Pattern. **Patterns** are ordered lists of [Program](Program.md) references (catalog entries such as series, movies, blocks, or composites). No durations inside the pattern — Zones + Patterns repeat to fill the Zone's active window, snapping to the Channel's Grid boundaries. **Programs** are catalog entities (series/movie/block) referenced by patterns; episodes are resolved at ScheduleDay time based on rotation policy. Plans are reusable and timeless — they define Zones and Patterns that are applied per day to generate ScheduleDay records. Plans are channel-bound and span repeating or one-time timeframes. Plans are layered by priority and can be overridden (e.g., weekday vs. holiday), with more specific layers overriding generic ones. Templates have been removed; all scheduling logic is defined directly in SchedulePlan. Content selection can include regular assets or VirtualAssets. Plans are timeless but bound by effective date ranges, and superseded plans are archived. Plan-based scheduling flows into ScheduleDay, which is resolved 3-4 days in advance for EPG and playout purposes. ScheduleDay is the primary expansion point for Programs → episodes and VirtualAssets → assets.

