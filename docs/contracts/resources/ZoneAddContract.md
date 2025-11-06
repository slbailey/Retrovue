# Zone Add Contract

_Related: [ZoneContract](ZoneContract.md) • [Domain: Zone](../../domain/Zone.md) • [Domain: SchedulePlan](../../domain/SchedulePlan.md) • [Domain: Pattern](../../domain/Pattern.md) • [Domain: Channel](../../domain/Channel.md)_

## Purpose

This contract defines the behavior of the `retrovue channel plan <channel> <plan> zone add` command, which creates a new Zone within a SchedulePlan. Zones are named time windows that declare when content should play and reference Patterns to define content sequences.

## Command Syntax

```bash
retrovue channel plan <channel> <plan> zone add \
  --name <string> \
  --start-time <HH:MM:SS> \
  --end-time <HH:MM:SS> \
  --pattern <pattern-id-or-name> \
  [--day-filters <json-array>] \
  [--enabled | --disabled] \
  [--effective-start <YYYY-MM-DD>] \
  [--effective-end <YYYY-MM-DD>] \
  [--dst-policy <policy>] \
  [--json] [--test-db]
```

## Required Arguments

- `<channel>` - Channel identifier (UUID or slug)
- `<plan>` - SchedulePlan identifier (UUID or name)

## Required Options

- `--name <string>` - Human-readable Zone name (must be unique within the SchedulePlan)
- `--start-time <HH:MM:SS>` - Zone start time in broadcast day format (00:00:00 to 24:00:00)
- `--end-time <HH:MM:SS>` - Zone end time in broadcast day format (00:00:00 to 24:00:00)
- `--pattern <pattern-id-or-name>` - Pattern identifier (UUID or name) that defines the content sequence

## Optional Options

- `--day-filters <json-array>` - Day-of-week filters as JSON array (e.g., `["MON","TUE","WED","THU","FRI"]`). If not provided, Zone is active on all days.
- `--enabled` / `--disabled` - Zone enabled status (default: `--enabled`)
- `--effective-start <YYYY-MM-DD>` - Start date for Zone validity (inclusive)
- `--effective-end <YYYY-MM-DD>` - End date for Zone validity (inclusive)
- `--dst-policy <policy>` - DST transition handling policy: "reject", "shrink_one_block", or "expand_one_block"
- `--json` - Output in JSON format
- `--test-db` - Use test database context

## Behavior Contract Rules (B-#)

### B-1: Channel and Plan Resolution

**Rule:** The command MUST resolve the channel and plan by their identifiers before creating the Zone.

**Behavior:**

- If channel is not found → exit 1, error message: "Error: Channel '<identifier>' not found"
- If plan is not found → exit 1, error message: "Error: Plan '<identifier>' not found"
- If plan does not belong to channel → exit 1, error message: "Error: Plan '<plan>' does not belong to channel '<channel>'"

### B-2: Pattern Resolution

**Rule:** The `--pattern` identifier MUST resolve to a Pattern that belongs to the same SchedulePlan as the Zone.

**Behavior:**

- If Pattern is not found → exit 1, error message: "Error: Pattern '<identifier>' not found"
- If Pattern belongs to different plan → exit 1, error message: "Error: Pattern '<pattern>' does not belong to plan '<plan>'"
- Pattern must exist and be valid

### B-3: Name Uniqueness

**Rule:** Zone name MUST be unique within the SchedulePlan.

**Behavior:**

- If name conflicts with existing Zone in same plan → exit 1, error message: "Error: Zone name '<name>' already exists in plan '<plan>'"
- Zones in different plans can have the same name
- Name validation occurs at creation time

### B-4: Time Window Validation

**Rule:** Start and end times MUST be valid and align with Channel Grid boundaries.

**Behavior:**

- Invalid time format → exit 1, error message: "Error: Invalid time format: <time>. Expected HH:MM:SS"
- Times out of range (not 00:00:00 to 24:00:00) → exit 1, error message: "Error: Time out of range: <time>. Must be between 00:00:00 and 24:00:00"
- Times don't align with Grid boundaries → exit 1, error message: "Error: Zone times must align with channel grid boundaries"
- Seconds/microseconds must be zero (except for 24:00 normalization) → exit 1, error message: "Error: Time must have zero seconds: <time>"

### B-5: Grid Divisibility

**Rule:** Zone duration MUST be divisible by Channel's `grid_block_minutes`.

**Behavior:**

- If duration not divisible by `grid_block_minutes` → exit 1, error message: "Error: Zone duration must be divisible by channel grid_block_minutes (<minutes>). Zone duration: <duration> minutes"
- Validation occurs at creation time (domain-level validation)

### B-6: Day Filters Validation

**Rule:** `--day-filters` MUST be valid JSON array of day abbreviations if provided.

**Behavior:**

- Invalid JSON → exit 1, error message: "Error: Invalid JSON for day-filters: <error>"
- Invalid day abbreviations → exit 1, error message: "Error: Invalid day abbreviation in day-filters. Valid values: MON, TUE, WED, THU, FRI, SAT, SUN"
- Valid JSON array → proceed
- If not provided → Zone active on all days

### B-7: Effective Date Range Validation

**Rule:** Effective date range MUST be valid if both dates provided.

**Behavior:**

- If `effective_start > effective_end` → exit 1, error message: "Error: effective-start must be <= effective-end"
- Invalid date format → exit 1, error message: "Error: Invalid date format: <date>. Expected YYYY-MM-DD"

### B-8: DST Policy Validation

**Rule:** DST policy MUST be valid and directionally compatible with DST transition types.

**Behavior:**

- Invalid policy value → exit 1, error message: "Error: Invalid dst-policy. Valid values: reject, shrink_one_block, expand_one_block"
- Policy directionality validation (if context allows) → warn or reject based on DST transition type

### B-9: Enabled Status

**Rule:** Zone enabled status defaults to enabled unless `--disabled` is specified.

**Behavior:**

- Default → `enabled=true`
- `--enabled` → `enabled=true`
- `--disabled` → `enabled=false`

## Data Contract Rules (D-#)

### D-1: Zone Persistence

**Rule:** Zone MUST be persisted in `zones` table with all provided fields.

**Behavior:**

- Record created with all required fields: `id`, `plan_id`, `name`, `start_time`, `end_time`, `pattern_id`
- Optional fields persisted if provided: `day_filters`, `enabled`, `effective_start`, `effective_end`, `dst_policy`
- Defaults applied: `enabled=true` if not specified
- Timestamps: `created_at`, `updated_at` set automatically

### D-2: Pattern Reference Integrity

**Rule:** Zone `pattern_id` MUST reference a valid Pattern within the same SchedulePlan.

**Behavior:**

- Foreign key constraint enforced
- Pattern must exist in database
- Pattern must belong to same plan as Zone
- Validation occurs at creation time

### D-3: Plan Reference Integrity

**Rule:** Zone `plan_id` MUST reference the resolved SchedulePlan.

**Behavior:**

- Foreign key constraint enforced
- Plan must exist in database
- Plan must belong to resolved channel

### D-4: Name Uniqueness Enforcement

**Rule:** Zone name uniqueness MUST be enforced at database or application layer.

**Behavior:**

- Unique constraint on (`plan_id`, `name`) or application-level validation
- Violation fails creation with clear error

### D-5: Timestamp Storage

**Rule:** Timestamps MUST be stored in UTC with timezone awareness.

**Behavior:**

- `created_at` set to current UTC time
- `updated_at` set to current UTC time
- Timezone-aware DateTime fields

### D-6: Transaction Boundaries

**Rule:** Zone creation MUST be atomic within a transaction.

**Behavior:**

- All validation occurs before any database writes
- On failure, no partial state persisted
- Rollback on any validation or persistence error

## Success Behavior

On successful creation:

**Exit Code:** 0

**Output (non-JSON):**

```
Zone created:
  ID: <zone-id>
  Plan: <plan-name>
  Name: <zone-name>
  Start Time: <start-time>
  End Time: <end-time>
  Pattern: <pattern-name>
  Day Filters: <day-filters-or-all-days>
  Enabled: <true/false>
  Effective Range: <start-date> to <end-date> (if provided)
```

**Output (JSON):**

```json
{
  "status": "ok",
  "zone": {
    "id": "<zone-uuid>",
    "plan_id": "<plan-uuid>",
    "name": "<zone-name>",
    "start_time": "<start-time>",
    "end_time": "<end-time>",
    "pattern_id": "<pattern-uuid>",
    "day_filters": <json-array-or-null>,
    "enabled": true,
    "effective_start": "<date-or-null>",
    "effective_end": "<date-or-null>",
    "dst_policy": "<policy-or-null>",
    "created_at": "<timestamp>",
    "updated_at": "<timestamp>"
  }
}
```

## Error Behavior

On error:

**Exit Code:** 1

**Output (non-JSON):**

```
Error: <error-message>
```

**Output (JSON):**

```json
{
  "status": "error",
  "error": "<error-message>"
}
```

## Examples

### Example 1: Create Base Zone

```bash
retrovue channel plan channel-1 weekday-plan zone add \
  --name "Base" \
  --start-time "00:00:00" \
  --end-time "24:00:00" \
  --pattern "base-pattern"
```

**Expected:** Zone created covering full programming day.

### Example 2: Create Prime Time Zone

```bash
retrovue channel plan channel-1 weekday-plan zone add \
  --name "Prime Time" \
  --start-time "19:00:00" \
  --end-time "22:00:00" \
  --pattern "prime-time-pattern"
```

**Expected:** Zone created for prime time window.

### Example 3: Create Weekend Zone with Day Filters

```bash
retrovue channel plan channel-1 base-plan zone add \
  --name "Weekend Morning" \
  --start-time "06:00:00" \
  --end-time "12:00:00" \
  --pattern "weekend-pattern" \
  --day-filters '["SAT","SUN"]'
```

**Expected:** Zone created active only on weekends.

### Example 4: Create Zone with Effective Dates

```bash
retrovue channel plan channel-1 seasonal-plan zone add \
  --name "Summer Prime" \
  --start-time "19:00:00" \
  --end-time "22:00:00" \
  --pattern "summer-pattern" \
  --effective-start "2025-06-01" \
  --effective-end "2025-08-31"
```

**Expected:** Zone created active only during summer months.

### Example 5: Invalid - Grid Not Divisible

```bash
retrovue channel plan channel-1 plan zone add \
  --name "Invalid" \
  --start-time "00:00:00" \
  --end-time "01:15:00" \
  --pattern "pattern-1"
```

**Expected:** Exit 1, error: "Error: Zone duration must be divisible by channel grid_block_minutes (30). Zone duration: 75 minutes"

### Example 6: Invalid - Pattern from Different Plan

```bash
retrovue channel plan channel-1 plan-a zone add \
  --name "Invalid" \
  --start-time "00:00:00" \
  --end-time "01:00:00" \
  --pattern "pattern-from-plan-b"
```

**Expected:** Exit 1, error: "Error: Pattern 'pattern-from-plan-b' does not belong to plan 'plan-a'"

## Test Coverage Requirements

Tests MUST verify:

1. Successful Zone creation with all field combinations
2. Channel and plan resolution (valid and invalid cases)
3. Pattern resolution and plan consistency
4. Name uniqueness within plan
5. Time window validation (format, range, grid alignment)
6. Grid divisibility validation
7. Day filters validation (JSON format, valid day abbreviations)
8. Effective date range validation
9. DST policy validation
10. Enabled status defaults and flags
11. JSON output format
12. Error message clarity
13. Domain-level validation occurs at creation time (not deferred)

## Related Contracts

- [ZoneContract](ZoneContract.md) - Zone domain validation contracts
- [ZoneUpdateContract](ZoneUpdateContract.md) - Zone update operations
- [ZoneListContract](ZoneListContract.md) - Zone listing operations
- [ZoneShowContract](ZoneShowContract.md) - Zone display operations
- [ZoneDeleteContract](ZoneDeleteContract.md) - Zone deletion operations
- [SchedulePlanInvariantsContract](SchedulePlanInvariantsContract.md) - Plan-level invariants

## See Also

- [Domain: Zone](../../domain/Zone.md) - Complete Zone domain documentation
- [Domain: SchedulePlan](../../domain/SchedulePlan.md) - SchedulePlan domain documentation
- [Domain: Pattern](../../domain/Pattern.md) - Pattern domain documentation
