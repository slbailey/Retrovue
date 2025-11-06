# Zone Domain Contracts

_Related: [Zone Add](ZoneAddContract.md) • [Zone Update](ZoneUpdateContract.md) • [Zone List](ZoneListContract.md) • [Zone Show](ZoneShowContract.md) • [Zone Delete](ZoneDeleteContract.md) • [Domain: Zone](../../domain/Zone.md) • [Domain: SchedulePlan](../../domain/SchedulePlan.md) • [Domain: Pattern](../../domain/Pattern.md) • [Domain: Channel](../../domain/Channel.md) • [Zones + Patterns Contracts](../ZonesPatterns.md)_

## Purpose

This document provides an overview of all Zone domain testing contracts. Zones are named time windows within the programming day that declare when content should play. This contract ensures that Zone validation, activation, and expansion behaviors are correctly implemented and can be verified through automated tests.

**Critical Rule:** These contracts are **testable assertions** that must be verified through automated tests. Each contract defines a specific behavior that the Zone domain must guarantee.

## Status

**Status:** Draft - Contracts defined, implementation pending

## Scope

The Zone domain is covered by the following specific contracts:

### CRUD Operations

- **[Zone Add](ZoneAddContract.md)**: Creating new Zones within SchedulePlans
- **[Zone Update](ZoneUpdateContract.md)**: Updating Zone configuration and state
- **[Zone List](ZoneListContract.md)**: Listing Zones within a SchedulePlan
- **[Zone Show](ZoneShowContract.md)**: Displaying detailed Zone information
- **[Zone Delete](ZoneDeleteContract.md)**: Deleting Zones (guarded by dependency checks)

### Domain Validation Contracts

- **[Zone Domain Validation Contracts](#domain-level-validation-contracts)** (this document): Domain-level validation, activation, and behavioral contracts
  - Z-VAL-01 through Z-VAL-09: Validation contracts
  - Z-ACT-00 through Z-ACT-03: Activation contracts
  - Z-BEH-01 through Z-BEH-04: Behavioral contracts
  - Z-STOR-01: Storage semantics

## Contract Structure

Each Zone operation follows the standard contract pattern:

1. **Command Shape**: Exact CLI syntax and required flags
2. **Safety Expectations**: Confirmation prompts, validation behavior, dependency checks
3. **Output Format**: Human-readable and JSON output structure
4. **Exit Codes**: Success and failure exit codes
5. **Behavior Contract Rules (B-#)**: Operator-facing behavior guarantees
6. **Data Contract Rules (D-#)**: Persistence, lifecycle, and integrity guarantees
7. **Test Coverage Requirements**: Explicit test coverage mapping

## Design Principles

- **Safety first:** No destructive operation runs against live data during automated tests
- **One contract per noun/verb:** Each Zone operation has its own focused contract
- **Mock-first validation:** All operations must first be tested using mock/test databases
- **Idempotent where appropriate:** `list`/`show` are read-only and repeatable; `add`/`update` are deterministic with explicit validation
- **Clear error handling:** Failed operations provide actionable diagnostics
- **Unit of Work:** All database-modifying operations are wrapped in atomic transactions
- **Early validation:** Domain-level validation occurs at creation/update time, not deferred to resolution

## Common Safety Patterns

### Test Database Usage

- `--test-db` flag directs operations to an isolated test environment
- Test database must be completely isolated from production
- No test data should persist between test sessions

### Destructive Operation Confirmation

- Delete operations require confirmation prompts
- `--yes` flag skips confirmations in non-interactive contexts
- See [\_ops/DestructiveOperationConfirmation.md](../_ops/DestructiveOperationConfirmation.md)

### Dependency Checks

- Zone deletion checks for dependent ScheduleDays
- Provides guidance to disable Zone instead of deleting if dependencies exist

### Validation Scope & Triggers

- Validate on `add`, `update`, and via explicit validation commands
- Always validate the Zone row
- Cross-validate Pattern-Plan consistency
- Domain-level validation occurs at creation/update time (not deferred to ScheduleDay resolution)

## Zone-Specific Guardrails

- **Name uniqueness**: Must be unique within SchedulePlan
- **Grid alignment**: Start and end times must align with Channel Grid boundaries
- **Grid divisibility**: Zone duration must be divisible by `grid_block_minutes`
- **Pattern-Plan consistency**: Pattern must belong to same SchedulePlan as Zone
- **Time window validity**: Times must be valid broadcast day format (00:00:00 to 24:00:00)
- **Day filters**: Valid JSON array of day abbreviations if provided
- **Effective dates**: Valid date range if both dates provided
- **DST policy**: Valid policy value and directionally compatible with DST transition type
- **Activation order**: Deterministic evaluation order (enabled → effective dates → day filters → time window)

## Contract Test Requirements

Each Zone contract should have exactly two test files:

1. **CLI Contract Test**: `tests/contracts/test_zone_{verb}_contract.py`

   - CLI syntax validation
   - Flag behavior verification
   - Output format validation
   - Error message handling

2. **Data Contract Test**: `tests/contracts/test_zone_{verb}_data_contract.py`
   - Database state verification
   - Transaction boundaries
   - Data integrity checks
   - Domain-level validation enforcement

---

## Domain-Level Validation Contracts

The following contracts define domain-level validation, activation, and behavioral rules that apply to Zone entities regardless of the CRUD operation being performed.

These contracts apply to:

- **Zone** - Named time windows within the programming day that reference Patterns
- **SchedulePlan** - Parent plans that contain Zones
- **Pattern** - Content sequences referenced by Zones
- **Channel** - Provides Grid configuration that Zones must align to

### Z-VAL-01: Grid Divisibility Invariant

**Contract:** Zone duration in minutes MUST be divisible by the Channel's `grid_block_minutes`. Validation occurs at Zone creation/update time (domain-level validation), not only during ScheduleDay resolution.

**Behavior:**

- Zone duration is calculated as `(end_time - start_time)` in minutes (accounting for midnight spanning)
- Duration MUST be divisible by `grid_block_minutes` without remainder
- If not divisible, the system rejects the configuration unless a policy allows rounding to nearest boundary
- Validation fails early at Zone creation/update time, not deferred to resolution

**Test Assertions:**

- Given Channel with `grid_block_minutes=30`:
  - Zone `00:00-01:00` (60 minutes) → Valid (60 % 30 == 0)
  - Zone `00:00-01:15` (75 minutes) → Invalid (75 % 30 == 15, not 0)
  - Zone `19:00-22:00` (180 minutes) → Valid (180 % 30 == 0)
- Given Channel with `grid_block_minutes=15`:
  - Zone `00:00-01:00` (60 minutes) → Valid (60 % 15 == 0)
  - Zone `00:00-01:10` (70 minutes) → Invalid (70 % 15 == 10, not 0)
- Zone spanning midnight `22:00-05:00` (420 minutes) with `grid_block_minutes=30` → Valid (420 % 30 == 0)

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Grid divisibility invariant
- [Channel.md](../../domain/Channel.md) - Grid configuration

**Entities:** Zone, Channel

---

### Z-VAL-02: Grid Boundary Alignment

**Contract:** Zone start and end times MUST align with the Channel's Grid boundaries (`block_start_offsets_minutes`). Validation occurs at Zone creation/update time (domain-level validation). Times must use broadcast day offsets, and seconds/microseconds must be zero (except for 24:00 normalization).

**Behavior:**

- Zone `start_time` minute component MUST be in `block_start_offsets_minutes`
- Zone `end_time` minute component MUST be in `block_start_offsets_minutes`
- Times are in broadcast day format (00:00:00 to 24:00:00 relative to `programming_day_start`)
- Seconds and microseconds MUST be zero (00:00:00), except for end-of-day normalization (24:00:00 stored as 23:59:59.999999)
- Alignment is relative to broadcast day, not calendar midnight
- Validation fails early at Zone creation/update time

**Test Assertions:**

- Given Channel with `block_start_offsets_minutes=[0, 30]`, `programming_day_start=00:00:00`:
  - Zone `00:00-01:00` → Valid (both :00)
  - Zone `19:30-22:00` → Valid (both :00 and :30)
  - Zone `19:00-22:15` → Invalid (22:15 not in [0, 30])
  - Zone `19:07-22:00` → Invalid (19:07 not in [0, 30])
- Given Channel with `block_start_offsets_minutes=[0, 15, 30, 45]`, `programming_day_start=00:00:00`:
  - Zone `00:15-01:30` → Valid
  - Zone `00:10-01:00` → Invalid (00:10 not in [0, 15, 30, 45])
- Given Channel with `block_start_offsets_minutes=[0, 30]`, `programming_day_start=06:00:00`:
  - Zone `22:00-05:00` (broadcast day time, spans midnight) → Valid (both :00)
  - Zone `22:15-05:00` → Valid only if 15 ∈ `block_start_offsets_minutes` (alignment uses broadcast-day offsets)
  - Zone `22:15-05:30` → Valid only if both 15 and 30 ∈ `block_start_offsets_minutes`
- Seconds/microseconds validation:
  - Zone `19:00:00-22:00:00` → Valid (seconds zero)
  - Zone `19:00:30-22:00:00` → Invalid (non-zero seconds)
  - Zone `19:00:00.123456-22:00:00` → Invalid (non-zero microseconds, unless normalized end-of-day)

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Grid alignment invariant
- [Channel.md](../../domain/Channel.md) - Grid boundaries, programming_day_start

**Entities:** Zone, Channel

---

### Z-VAL-03: Pattern-Plan Consistency

**Contract:** Zone `pattern_id` MUST reference a Pattern that belongs to the same SchedulePlan as the Zone. This is enforced as an invariant at Zone creation/update time.

**Behavior:**

- When creating or updating a Zone, `pattern_id` must reference a Pattern with the same `plan_id` as the Zone
- Cross-plan Pattern references are rejected
- Validation fails early at Zone creation/update time

**Test Assertions:**

- Given Zone with `plan_id="plan-a"`, Pattern with `plan_id="plan-a"` → Valid
- Given Zone with `plan_id="plan-a"`, Pattern with `plan_id="plan-b"` → Invalid (rejected)
- Updating Zone to reference Pattern from different plan → Invalid (rejected)

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Pattern-Plan consistency invariant
- [Pattern.md](../../domain/Pattern.md) - Plan membership

**Entities:** Zone, Pattern, SchedulePlan

---

### Z-VAL-03a: Pattern Required

**Contract:** Zone `pattern_id` MUST be non-null and resolvable at Zone creation/update time. Zones cannot exist without a Pattern reference.

**Behavior:**

- `pattern_id` is a required field (non-nullable)
- Pattern must exist in the database at Zone creation/update time
- Pattern must be valid (not deleted, belongs to same plan)
- Validation fails early at Zone creation/update time if Pattern is missing or invalid

**Test Assertions:**

- Creating Zone with `pattern_id=null` → Invalid (rejected)
- Creating Zone with `pattern_id="non-existent-uuid"` → Invalid (Pattern not found)
- Creating Zone with valid `pattern_id` → Valid
- Updating Zone to set `pattern_id=null` → Invalid (rejected)
- Deleting Pattern referenced by Zone → Must be prevented or Zone must be deleted/updated first

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Pattern reference requirement
- [Pattern.md](../../domain/Pattern.md) - Pattern existence

**Entities:** Zone, Pattern

---

### Z-VAL-04: Name Uniqueness Within Plan

**Contract:** Zone `name` MUST be unique within the SchedulePlan. Multiple Zones can have the same name if they belong to different Plans.

**Behavior:**

- Zone names are scoped to the SchedulePlan (`plan_id`)
- Two Zones in the same Plan cannot have the same name
- Two Zones in different Plans can have the same name
- Validation fails at Zone creation/update time

**Test Assertions:**

- Creating Zone "Prime Time" in Plan A → Valid
- Creating second Zone "Prime Time" in Plan A → Invalid (name conflict)
- Creating Zone "Prime Time" in Plan B → Valid (different plan)
- Updating Zone name to conflict with existing Zone in same plan → Invalid

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Name uniqueness invariant

**Entities:** Zone, SchedulePlan

---

### Z-VAL-05: Time Window Validity

**Contract:** Zone `start_time` and `end_time` MUST be valid times in broadcast day format (00:00:00 to 24:00:00 relative to `programming_day_start`), and `start_time` must be less than `end_time` unless spanning midnight. Duration and midnight-span calculations must use broadcast day (not calendar midnight).

**Behavior:**

- Times must be valid Time values (00:00:00 to 24:00:00) in broadcast day format
- Times are relative to `Channel.programming_day_start`, not calendar midnight
- For non-spanning Zones: `start_time < end_time` (in broadcast day time)
- For midnight-spanning Zones: `end_time < start_time` is allowed when calculated using broadcast day (e.g., `22:00-05:00` relative to `programming_day_start=06:00`)
- Duration calculation: `(end_time - start_time)` accounts for midnight spanning within broadcast day
- Midnight-span detection: Uses broadcast day boundaries, not calendar day boundaries
- Validation fails at Zone creation/update time

**Test Assertions:**

- Zone `00:00-24:00` (broadcast day) → Valid (non-spanning, 24 hours)
- Zone `19:00-22:00` (broadcast day) → Valid (non-spanning, 3 hours)
- Zone `22:00-05:00` with `programming_day_start=06:00` (broadcast day) → Valid (midnight-spanning, 7 hours)
  - Spans from 22:00 calendar Day 1 to 05:00 calendar Day 2
  - Both times within same broadcast day (06:00 Day 1 to 06:00 Day 2)
  - Duration = 420 minutes (7 hours)
- Zone `22:00-22:00` → Invalid (zero duration)
- Zone `22:00-21:00` (non-spanning) → Invalid (start > end, not midnight-spanning)
- Zone `25:00-26:00` → Invalid (times out of range)
- Duration calculation for midnight-spanning Zones:
  - Zone `22:00-05:00` with `programming_day_start=06:00`: Duration = (05:00 + 24:00) - 22:00 = 7:00 (420 minutes)
  - Duration calculation uses broadcast day math, not calendar day math

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Time window validation, broadcast day alignment
- [Channel.md](../../domain/Channel.md) - programming_day_start

**Entities:** Zone, Channel

---

### Z-VAL-06: Day Filter Validity

**Contract:** Zone `day_filters` MUST be a valid JSON array of day abbreviations if provided. If null, Zone is active on all days.

**Behavior:**

- `day_filters` must be null or a valid JSON array
- If array, must contain only valid day abbreviations: `MON`, `TUE`, `WED`, `THU`, `FRI`, `SAT`, `SUN`
- Array can be empty (treated as null - active all days)
- Validation fails at Zone creation/update time

**Test Assertions:**

- `day_filters=null` → Valid (active all days)
- `day_filters=["MON", "TUE", "WED", "THU", "FRI"]` → Valid
- `day_filters=["SAT", "SUN"]` → Valid
- `day_filters=["INVALID"]` → Invalid (invalid day abbreviation)
- `day_filters="MON"` → Invalid (not an array)
- `day_filters=[]` → Valid (treated as null - active all days)

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Day filter validation

**Entities:** Zone

---

### Z-VAL-07: Effective Date Range Validity

**Contract:** Zone `effective_start` and `effective_end` MUST form a valid date range (effective_start <= effective_end) if both are provided.

**Behavior:**

- Either field can be null (unbounded start or end)
- If both provided, `effective_start <= effective_end` must hold
- Validation fails at Zone creation/update time

**Test Assertions:**

- `effective_start=null, effective_end=null` → Valid (unbounded)
- `effective_start="2025-01-01", effective_end=null` → Valid (unbounded end)
- `effective_start=null, effective_end="2025-12-31"` → Valid (unbounded start)
- `effective_start="2025-01-01", effective_end="2025-12-31"` → Valid (valid range)
- `effective_start="2025-12-31", effective_end="2025-01-01"` → Invalid (start > end)

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Effective date range validation

**Entities:** Zone

---

### Z-VAL-08: DST Policy Validation

**Contract:** Zone `dst_policy` MUST be one of: "reject", "shrink_one_block", "expand_one_block" if provided. On DST transition dates, Zone duration is validated per this policy. Policy directionality must match DST transition type.

**Behavior:**

- `dst_policy` can be null (defaults to system-wide DST policy)
- If provided, must be one of the three valid values
- On DST transition dates (23-hour or 25-hour days), Zone duration is validated per policy
- "reject" → fails validation on DST dates if duration cannot be accommodated
- "shrink_one_block" → reduces duration by one grid block on spring-forward dates (23-hour day)
- "expand_one_block" → increases duration by one grid block on fall-back dates (25-hour day)
- **Directionality guardrail**: Policy must match transition type:
  - On spring-forward (23h day): only "reject" or "shrink_one_block" are valid; "expand_one_block" → invalid
  - On fall-back (25h day): only "reject" or "expand_one_block" are valid; "shrink_one_block" → invalid
- Validation fails at Zone creation/update time if policy is invalid or directionally incompatible

**Test Assertions:**

- `dst_policy=null` → Valid (uses system default)
- `dst_policy="reject"` → Valid (works for both transition types)
- `dst_policy="shrink_one_block"` → Valid (spring-forward only)
- `dst_policy="expand_one_block"` → Valid (fall-back only)
- `dst_policy="invalid"` → Invalid (rejected)
- On DST spring-forward date (23-hour day):
  - `dst_policy="reject"` → Valid
  - `dst_policy="shrink_one_block"` → Valid
  - `dst_policy="expand_one_block"` → Invalid (nonsensical - cannot expand on 23-hour day)
- On DST fall-back date (25-hour day):
  - `dst_policy="reject"` → Valid
  - `dst_policy="expand_one_block"` → Valid
  - `dst_policy="shrink_one_block"` → Invalid (nonsensical - cannot shrink on 25-hour day)
- On DST spring-forward date with `dst_policy="shrink_one_block"` → Zone duration reduces by one grid block
- On DST fall-back date with `dst_policy="expand_one_block"` → Zone duration increases by one grid block

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - DST policy validation
- [Channel.md](../../domain/Channel.md) - DST handling

**Entities:** Zone, Channel

---

### Z-VAL-09: Same-Plan Overlap Policy

**Contract:** Within the same SchedulePlan, overlapping Zones MUST either be rejected or resolved deterministically using a tie-breaker (e.g., lexicographic by name or creation time).

**Behavior:**

- Zones within the same Plan can overlap in time windows
- System MUST choose one of two policies:
  - **Option A (Reject)**: Overlapping Zones in same plan are rejected at creation/update time
  - **Option B (Resolve)**: Overlapping Zones are allowed, with deterministic resolution using a tie-breaker
- If resolving overlaps, tie-breaker MUST be deterministic (e.g., lexicographic by `name`, or by `created_at` timestamp)
- Cross-plan overlaps are handled by priority resolution (separate contract)
- Validation or resolution occurs at Zone creation/update time

**Test Assertions:**

- **If policy is "reject"**:
  - Zone A: `19:00-22:00` in Plan X → Valid
  - Zone B: `20:00-23:00` in Plan X → Invalid (overlaps with Zone A)
  - Zone C: `22:00-24:00` in Plan X → Valid (touching boundary, no overlap)
- **If policy is "resolve" with lexicographic tie-breaker**:
  - Zone A ("Evening"): `19:00-22:00` in Plan X
  - Zone B ("Prime Time"): `20:00-23:00` in Plan X
  - Both valid, resolution uses name: "Evening" < "Prime Time" lexicographically
  - Zone A takes precedence for overlap period `20:00-22:00`
- **If policy is "resolve" with creation time tie-breaker**:
  - Zone A (created earlier): `19:00-22:00` in Plan X
  - Zone B (created later): `20:00-23:00` in Plan X
  - Both valid, resolution uses `created_at`: earlier Zone takes precedence
- Overlaps are detected using: `(start_time < other.end_time) AND (end_time > other.start_time)`
- Boundary-touching Zones (one ends where another starts) are NOT considered overlapping

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Zone overlap handling
- [SchedulePlan.md](../../domain/SchedulePlan.md) - Plan structure

**Entities:** Zone, SchedulePlan

---

## Activation Contracts

### Z-ACT-00: Activation Order

**Contract:** Zone activation evaluation MUST follow a deterministic order: enabled → effective date range → day_filters → time window. Each check must be evaluated in sequence, and if any check fails, the Zone is inactive.

**Behavior:**

- Activation evaluation order is fixed and deterministic:
  1. **Enabled check**: If `enabled=false`, Zone is skipped (no further evaluation)
  2. **Effective date range**: If date falls outside `effective_start`/`effective_end` range, Zone is skipped
  3. **Day-of-week filter**: If `day_filters` is provided and date's day doesn't match, Zone is skipped
  4. **Time window**: Zone must be active for the time window being evaluated
- All checks must pass for Zone to be active
- Order is critical for performance (fail-fast on disabled Zones)

**Test Assertions:**

- Zone with `enabled=false` → Skipped immediately (other checks not evaluated)
- Zone with `enabled=true, effective_start="2025-06-01"`, date `2025-05-31` → Inactive (fails effective date check)
- Zone with `enabled=true, effective_start=null, day_filters=["MON"]`, date is Tuesday → Inactive (fails day filter check)
- Zone with all checks passing → Active
- Evaluation order must be deterministic: same inputs produce same activation result

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Zone activation evaluation

**Entities:** Zone, ScheduleDay

---

### Z-ACT-01: Enabled Status Check

**Contract:** Disabled Zones (`enabled=false`) MUST be ignored during schedule resolution. Only enabled Zones are considered for activation.

**Behavior:**

- `enabled` defaults to true
- During ScheduleDay resolution, Zones with `enabled=false` are skipped
- Disabled Zones do not participate in priority resolution or Pattern expansion
- Zone activation evaluation first checks `enabled` status

**Test Assertions:**

- Zone with `enabled=true` → Included in resolution
- Zone with `enabled=false` → Excluded from resolution
- Zone with `enabled=false` but matching date/time → Still excluded
- Multiple Zones, one disabled → Only enabled Zones considered for priority resolution

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Enable/disable behavior

**Entities:** Zone, ScheduleDay

---

### Z-ACT-02: Effective Date Range Activation

**Contract:** Zone activation MUST respect `effective_start` and `effective_end` date ranges. Zones are only active for dates within their effective range.

**Behavior:**

- If `effective_start` is provided, Zone is inactive before that date
- If `effective_end` is provided, Zone is inactive after that date
- If both provided, Zone is active only within the range (inclusive)
- If both null, Zone is active for all dates (subject to other activation checks)

**Test Assertions:**

- Zone with `effective_start="2025-06-01", effective_end="2025-08-31"`:
  - Date `2025-05-31` → Inactive (before start)
  - Date `2025-06-01` → Active (inclusive start)
  - Date `2025-07-15` → Active (within range)
  - Date `2025-08-31` → Active (inclusive end)
  - Date `2025-09-01` → Inactive (after end)
- Zone with `effective_start=null, effective_end=null` → Active for all dates (subject to other checks)

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Effective date range activation

**Entities:** Zone, ScheduleDay

---

### Z-ACT-03: Day-of-Week Filter Activation

**Contract:** Zone activation MUST respect `day_filters`. Zones are only active on days matching their day filters (or all days if null).

**Behavior:**

- If `day_filters` is null, Zone is active on all days of the week
- If `day_filters` is provided, Zone is active only on matching days
- Day matching is based on the date's day of week
- Zone activation evaluation checks day filters after enabled and effective date checks

**Test Assertions:**

- Zone with `day_filters=null` → Active on all days (Mon-Sun)
- Zone with `day_filters=["MON", "TUE", "WED", "THU", "FRI"]`:
  - Monday date → Active
  - Friday date → Active
  - Saturday date → Inactive
  - Sunday date → Inactive
- Zone with `day_filters=["SAT", "SUN"]`:
  - Saturday date → Active
  - Sunday date → Active
  - Monday date → Inactive

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Day-of-week filtering

**Entities:** Zone, ScheduleDay

---

## Behavioral Contracts

### Z-BEH-01: Soft-Start-After-Current Policy

**Contract:** If a Zone opens while content is already playing, the Zone MUST wait until the current item ends, then start its Pattern at the next grid boundary. This behavior applies identically whether the next Zone is from the same plan or a different plan.

**Behavior:**

- When a Zone becomes active but content from a previous Zone or carry-in is still playing, the new Zone does not interrupt
- The Zone's Pattern begins at the next grid boundary after the current content completes
- This prevents mid-content interruptions and ensures smooth transitions
- **Cross-plan behavior**: Behavior is identical when transitioning between Zones from different plans. Plan boundaries do not affect soft-start policy.
- Content continuation applies regardless of whether previous Zone and new Zone belong to the same SchedulePlan

**Test Assertions:**

- Given content playing from 19:00 expected to end at 21:15, and Zone opening at 20:00:
  - Current content continues until 21:15
  - Zone's Pattern starts at 21:30 (next grid boundary after 21:15)
- Given content playing from 04:00 expected to end at 06:45, and Zone opening at 06:00:
  - Current content continues until 06:45
  - Zone's Pattern starts at 07:00 (next grid boundary after 06:45)
- **Cross-plan transition**: Zone A (Plan X) ends with content playing until 21:15, Zone B (Plan Y, different plan) opens at 20:00:
  - Content continues until 21:15 (soft-start applies across plan boundaries)
  - Zone B's Pattern starts at 21:30 (next grid boundary)

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Soft-start policy
- [ZonesPatterns.md](../ZonesPatterns.md) - C-ZONE-01

**Entities:** Zone, ScheduleDay, SchedulePlan

---

### Z-BEH-02: Carry-Out Policy

**Contract:** If Zone ends while content is mid-program, content finishes to completion, then the next Zone begins at the next grid boundary. This behavior applies identically whether the next Zone is from the same plan or a different plan.

**Behavior:**

- This is the mirror rule to soft-start: Zones don't cut content mid-play when closing
- Content that extends past Zone end time continues to completion
- Next Zone's Pattern starts at the next grid boundary after content completes
- Longform content can consume additional grid blocks past Zone end
- **Cross-plan behavior**: Behavior is identical when transitioning between Zones from different plans. Plan boundaries do not affect carry-out policy.
- Content continuation applies regardless of whether current Zone and next Zone belong to the same SchedulePlan

**Test Assertions:**

- Given Zone `19:00-22:00` with Pattern `["Movie Block"]` that resolves to 2.5-hour movie:
  - Movie plays to completion (ends at 21:30)
  - Next Zone starts at 22:00 (next grid boundary)
- Given Zone `19:00-22:00` with Pattern `["Movie Block"]` that resolves to 3-hour movie:
  - Movie plays to completion, consuming additional grid blocks past Zone end
  - Next Zone's Pattern starts at next grid boundary after movie completion (e.g., 22:30)
- **Cross-plan transition**: Zone A (Plan X) ends at 22:00 but content plays until 22:30, Zone B (Plan Y, different plan) starts at 22:00:
  - Content continues until 22:30 (carry-out applies across plan boundaries)
  - Zone B's Pattern starts at 22:30 or next grid boundary after completion

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Carry-out policy

**Entities:** Zone, ScheduleDay, SchedulePlan

---

### Z-BEH-03: Priority-Based Zone Override

**Contract:** When multiple SchedulePlans are active for the same date, Zones are resolved by priority. Higher-priority plans' Zones override lower-priority plans' Zones for overlapping time windows.

**Behavior:**

- Plan priority determines which Zones apply when plans overlap
- Higher-priority plans' Zones completely supersede overlapping Zones from lower-priority plans
- More specific plans (e.g., holidays) should have higher priority than general plans (e.g., weekdays)
- Priority resolution occurs before Zone expansion

**Test Assertions:**

- WeekdayPlan (priority 10): Zone `00:00-24:00` with Pattern `["Series A", "Series B"]`
- ChristmasPlan (priority 30): Zone `19:00-22:00` with Pattern `["Christmas Special"]`
- Result on December 25:
  - ChristmasPlan Zone overrides WeekdayPlan Zone for 19:00-22:00
  - WeekdayPlan Zone applies for 00:00-19:00 and 22:00-24:00

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Priority-based override
- [SchedulePlan.md](../../domain/SchedulePlan.md) - Plan priority

**Entities:** Zone, SchedulePlan, ScheduleDay

---

### Z-BEH-04: Midnight-Spanning Zone Handling

**Contract:** Zones that span midnight (e.g., `22:00-05:00`) MUST be handled correctly within the broadcast day context. Both times are within the same broadcast day.

**Behavior:**

- Zones use broadcast day time (00:00-24:00 relative to `programming_day_start`)
- A Zone like `22:00-05:00` spans from 22:00 on one calendar day to 05:00 the next calendar day
- Both times are within the same broadcast day
- Zone duration calculation accounts for midnight spanning

**Test Assertions:**

- Zone `22:00-05:00` with broadcast day start 06:00:
  - Zone starts at 22:00 on Day 1 (calendar)
  - Zone ends at 05:00 on Day 2 (calendar)
  - Both times within same broadcast day (06:00 Day 1 to 06:00 Day 2)
  - Duration = 7 hours (420 minutes)
- Pattern expansion correctly handles midnight-spanning Zones

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Broadcast day alignment

**Entities:** Zone, Channel, ScheduleDay

---

## 24:00 Storage Semantics

### Z-STOR-01: End-of-Day Time Storage

**Contract:** Zones with `end_time=24:00:00` MUST be stored correctly. Postgres TIME type cannot store 24:00:00, so normalization is required. Round-trip persistence MUST preserve the conceptual 24:00:00 in the domain layer.

**Behavior:**

- Zones with `end_time=24:00:00` are stored as `23:59:59.999999` in the database
- Domain layer normalizes this for clarity (converts back to 24:00:00 when reading)
- Documentation uses 24:00:00 for conceptual accuracy
- Zone duration calculations handle end-of-day correctly
- **Round-trip preservation**: Writing 24:00:00 → storing as 23:59:59.999999 → reading → domain layer shows 24:00:00

**Test Assertions:**

- Creating Zone with `end_time=24:00:00` → Stored as `23:59:59.999999` in database
- Reading Zone with `end_time=23:59:59.999999` from database → Displayed as `24:00:00` in domain layer
- **Round-trip test**: Write Zone with `end_time=24:00:00` → Persist → Read → Domain layer shows `24:00:00` (conceptual value preserved)
- Duration calculation for Zone `00:00-24:00` → 24 hours (1440 minutes)
- Zone expansion correctly handles end-of-day boundaries using conceptual 24:00:00

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - 24:00 storage semantics

**Entities:** Zone

---

## Gap Handling and Warnings

When Zones are disabled, rejected, or create gaps in schedule coverage, the system MUST log appropriate telemetry:

- **Disabled Zones** (`enabled=false`): Log at INFO level (expected behavior, not an error)
- **Rejected Zones** (validation failure): Log at WARN level with specific validation error
- **Gaps from missing Zones**: Log at WARN level (allowed but should be flagged for operator review)
- **Gaps from under-filled Zones**: Log at INFO level (expected when Patterns don't fill Zones completely)

**Note:** Detailed gap and warning level specifications are defined in ScheduleDay contracts. This contract references them for completeness in Zone activation scenarios.

## Test Coverage Requirements

Each contract (Z-VAL-01 through Z-STOR-01) MUST have corresponding test coverage that:

1. **Validates the contract holds** in normal operation
2. **Verifies violation detection** when the contract would be broken
3. **Confirms error handling** provides clear feedback
4. **Tests edge cases** and boundary conditions
5. **Validates domain-level validation** occurs at creation/update time, not deferred to resolution
6. **Validates activation order** (Z-ACT-00) is deterministic and fail-fast

## Related Contracts

- [ZonesPatterns.md](../ZonesPatterns.md) - High-level Zones + Patterns behavioral contracts
- [SchedulePlanInvariantsContract.md](SchedulePlanInvariantsContract.md) - Cross-entity invariants for SchedulePlan
- [PatternContract.md](PatternContract.md) - Pattern-specific contract rules (future)
- [ScheduleDayContract.md](ScheduleDayContract.md) - ScheduleDay generation and validation contracts

## See Also

- [Domain: Zone](../../domain/Zone.md) - Complete Zone domain documentation
- [Domain: SchedulePlan](../../domain/SchedulePlan.md) - SchedulePlan domain documentation
- [Domain: Pattern](../../domain/Pattern.md) - Pattern domain documentation
- [Domain: Channel](../../domain/Channel.md) - Channel Grid configuration

---

**Note:** These contracts ensure that Zone entities are correctly validated, activated, and expanded during schedule generation. All contracts prioritize early validation (domain-level), clear error messages, and deterministic behavior.

## Integration Contracts

The following contracts define how Zones integrate with SchedulePlan sessions, validation systems, and other operational contexts. These contracts ensure consistent behavior across different usage patterns (CLI, Planning Session, APIs).

### Z-INT-01: Shared Validator

**Contract:** The SchedulePlanningSession MUST invoke the same Zone validator used by CRUD operations. Tests may call either pathway and MUST observe identical results and error messages.

**Behavior:**

- Zone validation logic is shared between CRUD operations and SchedulePlan session operations
- SchedulePlanningSession must delegate to the same domain validator used by CLI commands
- Validation results (success/failure, error messages) must be identical regardless of calling pathway
- Tests can validate behavior through either CLI commands or Planning Session APIs
- No duplicate validation logic should exist in Planning Session layer

**Test Assertions:**

- Creating Zone via CLI with invalid grid alignment → Validation error with specific message
- Creating same Zone via Planning Session with same inputs → Identical validation error and message
- Error messages must match exactly between CLI and Planning Session pathways
- Validation codes (e.g., Z-VAL-01) must be consistent across both pathways
- Test suite includes tests that exercise both pathways with identical inputs and verify identical outputs

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Single Source of Truth principle
- [ZoneAddContract.md](ZoneAddContract.md) - Zone creation validation

**Entities:** Zone, SchedulePlanningSession

---

### Z-INT-02: Transactional Semantics

**Contract:** On validation failure, no partial updates persist (atomic create/update). Tests assert DB state is unchanged after failed ops.

**Behavior:**

- Zone create/update operations are atomic within transactions
- If validation fails at any point, the entire operation rolls back
- Database state before and after a failed operation must be identical
- No partial Zone records, no orphaned references, no inconsistent state
- Transaction boundaries must encompass all validation and persistence steps

**Test Assertions:**

- Creating Zone with invalid Pattern reference → Transaction rolls back, no Zone record created
- Updating Zone with invalid grid alignment → Transaction rolls back, original Zone unchanged
- Creating Zone that violates name uniqueness → Transaction rolls back, no Zone record created
- Database state before failed operation equals database state after failed operation
- Tests verify database state using queries, not just exit codes

**Related Documentation:**

- [ZoneAddContract.md](ZoneAddContract.md) - Transaction boundaries
- [ZoneUpdateContract.md](ZoneUpdateContract.md) - Transaction boundaries
- [\_ops/UnitOfWorkContract.md](../_ops/UnitOfWorkContract.md) - Unit of Work pattern

**Entities:** Zone

---

### Z-INT-03: Clock Injection

**Contract:** Domain functions accept a clock provider; tests can inject a fixed clock. The planning session MUST pass its clock provider through.

**Behavior:**

- Zone validation and activation functions accept a clock provider parameter
- Clock provider is abstracted (e.g., `MasterClock` interface) to allow test injection
- Planning Session must pass its clock provider to Zone domain functions
- Tests can inject a fixed clock for deterministic behavior
- Production code uses `MasterClock.now()` via the clock provider

**Test Assertions:**

- Zone activation evaluation uses injected clock → Deterministic activation results
- Zone validation with DST transition dates uses injected clock → Deterministic validation
- Planning Session passes clock provider to Zone functions → Clock provider flows through correctly
- Tests with fixed clock produce identical results across test runs
- Clock injection does not affect validation logic, only time queries

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Clock & Timezone requirements
- [MasterClockContract.md](MasterClockContract.md) - MasterClock interface

**Entities:** Zone, SchedulePlanningSession, MasterClock

---

### Z-INT-04: Channel Context Required

**Contract:** Zone validation requires Channel grid (grid_block_minutes, block_start_offsets_minutes, programming_day_start). Callers MUST supply it explicitly; no hidden defaults.

**Behavior:**

- Zone validation functions require Channel grid configuration as explicit parameters
- No default values are assumed for grid configuration
- Callers (CLI, Planning Session, APIs) must explicitly provide Channel grid context
- Validation fails if Channel grid is not provided
- Channel grid is resolved before Zone validation occurs

**Test Assertions:**

- Zone validation called without Channel grid → Error: "Channel grid configuration required"
- Zone validation called with explicit Channel grid → Validation proceeds normally
- Grid alignment validation uses provided `block_start_offsets_minutes` → Correct alignment checks
- Grid divisibility validation uses provided `grid_block_minutes` → Correct divisibility checks
- Broadcast day calculations use provided `programming_day_start` → Correct time calculations

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Grid alignment and divisibility requirements
- [Channel.md](../../domain/Channel.md) - Channel grid configuration

**Entities:** Zone, Channel

---

### Z-INT-05: Error Model Stability

**Contract:** Violations raise ValidationError (or your chosen type) with stable code strings matching contract IDs (e.g., Z-VAL-01). Tests assert on code.

**Behavior:**

- Zone validation failures raise a consistent exception type (e.g., `ValidationError`)
- Each validation failure includes a stable error code matching the contract ID (e.g., `Z-VAL-01`, `Z-VAL-02`)
- Error codes are stable across versions (not changed without deprecation)
- Tests assert on error codes, not error messages (messages may vary for localization)
- Error codes enable programmatic error handling and testing

**Test Assertions:**

- Zone with invalid grid divisibility → Raises `ValidationError` with code `Z-VAL-01`
- Zone with invalid grid alignment → Raises `ValidationError` with code `Z-VAL-02`
- Zone with cross-plan Pattern reference → Raises `ValidationError` with code `Z-VAL-03`
- Tests assert error code matches contract ID → `assert error.code == "Z-VAL-01"`
- Error codes are stable across CLI and Planning Session pathways → Same code for same violation

**Related Documentation:**

- [ZoneContract.md](ZoneContract.md) - Validation contract IDs (Z-VAL-01 through Z-VAL-09)
- [ZoneAddContract.md](ZoneAddContract.md) - Error behavior

**Entities:** Zone

---

### Z-INT-06: Seconds Policy

**Contract:** Start/end seconds and micros MUST be zero (except normalized 24:00). Validation rejects non-aligned second/micro values.

**Behavior:**

- Zone `start_time` and `end_time` must have seconds and microseconds set to 00
- Exception: End-of-day normalization (24:00:00 stored as 23:59:59.999999) is allowed
- Validation explicitly checks seconds and microseconds components
- Non-zero seconds or microseconds (except normalized end-of-day) cause validation failure
- Error message clearly identifies the violation (non-zero seconds/microseconds)

**Test Assertions:**

- Zone with `start_time="19:00:00"` → Valid (seconds and microseconds zero)
- Zone with `start_time="19:00:30"` → Invalid (non-zero seconds), error code Z-VAL-02
- Zone with `start_time="19:00:00.123456"` → Invalid (non-zero microseconds), error code Z-VAL-02
- Zone with `end_time="24:00:00"` → Valid (normalized to 23:59:59.999999 in storage)
- Zone with `end_time="22:00:00.123456"` → Invalid (non-zero microseconds), error code Z-VAL-02
- Validation error includes specific field and violation type → "start_time has non-zero seconds: 30"

**Related Documentation:**

- [Zone.md](../../domain/Zone.md) - Time normalization requirements
- [ZoneContract.md](ZoneContract.md) - Z-VAL-02: Grid Boundary Alignment

**Entities:** Zone

---

### Z-INT-07: Same-Plan Overlap Policy

**Contract:** Within a single plan, overlapping Zones are (choose one): rejected at validation or resolved by a deterministic tiebreak (e.g., higher priority, then name ASC). Tests assert the chosen policy.

**Behavior:**

- System MUST choose one of two policies for same-plan Zone overlaps:
  - **Option A (Reject)**: Overlapping Zones in same plan are rejected at validation time
  - **Option B (Resolve)**: Overlapping Zones are allowed, with deterministic resolution using a tie-breaker
- If resolving overlaps, tie-breaker MUST be deterministic (e.g., lexicographic by name, or by creation time)
- The chosen policy must be documented and consistently applied
- Tests must verify the chosen policy is enforced

**Test Assertions:**

- **If policy is "reject"**:
  - Zone A: `19:00-22:00` in Plan X → Valid
  - Zone B: `20:00-23:00` in Plan X → Invalid (overlaps with Zone A), error code Z-VAL-09
  - Zone C: `22:00-24:00` in Plan X → Valid (touching boundary, no overlap)
- **If policy is "resolve" with lexicographic tie-breaker**:
  - Zone A ("Evening"): `19:00-22:00` in Plan X → Valid
  - Zone B ("Prime Time"): `20:00-23:00` in Plan X → Valid
  - Both valid, resolution uses name: "Evening" < "Prime Time" lexicographically
  - Zone A takes precedence for overlap period `20:00-22:00`
- **If policy is "resolve" with creation time tie-breaker**:
  - Zone A (created earlier): `19:00-22:00` in Plan X → Valid
  - Zone B (created later): `20:00-23:00` in Plan X → Valid
  - Both valid, resolution uses `created_at`: earlier Zone takes precedence
- Overlaps are detected using: `(start_time < other.end_time) AND (end_time > other.start_time)`
- Boundary-touching Zones (one ends where another starts) are NOT considered overlapping
- Tests assert the chosen policy is consistently applied across all Zone operations

**Related Documentation:**

- [ZoneContract.md](ZoneContract.md) - Z-VAL-09: Same-Plan Overlap Policy
- [Zone.md](../../domain/Zone.md) - Zone overlap handling

**Entities:** Zone, SchedulePlan

---
