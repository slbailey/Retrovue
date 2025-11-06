# Zone Update Contract

_Related: [ZoneContract](ZoneContract.md) • [ZoneAddContract](ZoneAddContract.md) • [Domain: Zone](../../domain/Zone.md) • [Domain: SchedulePlan](../../domain/SchedulePlan.md)_

## Purpose

This contract defines the behavior of the `retrovue channel plan <channel> <plan> zone update` command, which updates an existing Zone within a SchedulePlan.

## Command Syntax

```bash
retrovue channel plan <channel> <plan> zone update --id <zone-id> \
  [--name <string>] \
  [--start-time <HH:MM:SS>] \
  [--end-time <HH:MM:SS>] \
  [--pattern <pattern-id-or-name>] \
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
- `--id <zone-id>` - Zone identifier (UUID or name)

## Optional Options

All options are optional; only provided fields are updated:

- `--name <string>` - Zone name (must remain unique within plan if changed)
- `--start-time <HH:MM:SS>` - Zone start time
- `--end-time <HH:MM:SS>` - Zone end time
- `--pattern <pattern-id-or-name>` - Pattern reference
- `--day-filters <json-array>` - Day-of-week filters
- `--enabled` / `--disabled` - Enabled status
- `--effective-start <YYYY-MM-DD>` - Effective start date
- `--effective-end <YYYY-MM-DD>` - Effective end date
- `--dst-policy <policy>` - DST policy
- `--json` - Output in JSON format
- `--test-db` - Use test database context

## Behavior Contract Rules (B-#)

### B-1: Zone Resolution

**Rule:** The Zone identified by `--id` MUST exist within the specified plan.

**Behavior:**
- If Zone not found → exit 1, error message: "Error: Zone '<id>' not found in plan '<plan>'"
- If Zone belongs to different plan → exit 1, error message: "Error: Zone '<id>' does not belong to plan '<plan>'"
- Zone must exist and be accessible

### B-2: Partial Updates

**Rule:** Only specified fields MUST be updated; others remain unchanged.

**Behavior:**
- If `--name` not provided → name unchanged
- If `--start-time` not provided → start_time unchanged
- All unspecified fields retain current values
- Update applies only to provided fields

### B-3: Validation on Changed Fields

**Rule:** Updated fields MUST be validated using the same rules as creation (Z-VAL-01 through Z-VAL-09).

**Behavior:**
- If `--start-time` or `--end-time` changed → grid alignment and divisibility validated
- If `--pattern` changed → pattern-plan consistency validated
- If `--name` changed → name uniqueness validated
- All domain-level validation contracts apply to updated fields

### B-4: Name Uniqueness on Update

**Rule:** If name is updated, it MUST remain unique within the SchedulePlan (excluding current Zone).

**Behavior:**
- If new name conflicts with another Zone in same plan → exit 1, error: "Error: Zone name '<name>' already exists in plan '<plan>'"
- Can update to same name (no-op)
- Can update to name that exists in different plan

### B-5: Pattern-Plan Consistency on Update

**Rule:** If pattern is updated, it MUST belong to the same SchedulePlan.

**Behavior:**
- If pattern belongs to different plan → exit 1, error: "Error: Pattern '<pattern>' does not belong to plan '<plan>'"
- Pattern must exist and be valid

### B-6: Time Window Validation on Update

**Rule:** If time window is updated, it MUST align with Grid boundaries and be divisible by grid_block_minutes.

**Behavior:**
- Grid alignment validated if `--start-time` or `--end-time` changed
- Grid divisibility validated if time window changed
- All Z-VAL-02 and Z-VAL-01 rules apply

### B-7: JSON Output

**Rule:** `--json` MUST return valid JSON with the updated Zone.

**Behavior:**
- JSON output includes all Zone fields
- Timestamps reflect update time
- Format matches ZoneAddContract JSON output

## Data Contract Rules (D-#)

### D-1: Selective Field Updates

**Rule:** Only modified fields change; others remain intact.

**Behavior:**
- Database update applies only to provided fields
- Unspecified fields retain existing values
- No side effects on unrelated fields

### D-2: Timestamp Updates

**Rule:** `updated_at` MUST be set to current UTC time on successful update.

**Behavior:**
- `updated_at` updated automatically
- `created_at` remains unchanged
- Timestamps timezone-aware (UTC)

### D-3: Transaction Boundaries

**Rule:** Zone update MUST be atomic within a transaction.

**Behavior:**
- All validation occurs before any database writes
- On failure, no partial state persisted
- Rollback on any validation or persistence error

### D-4: Validation Order

**Rule:** Pre-flight validation MUST occur before any database modifications.

**Behavior:**
- Validate all updated fields before writing
- Check constraints and invariants
- Fail fast on validation errors

## Success Behavior

On successful update:

**Exit Code:** 0

**Output (non-JSON):**
```
Zone updated:
  ID: <zone-id>
  Plan: <plan-name>
  Name: <zone-name>
  Start Time: <start-time>
  End Time: <end-time>
  Pattern: <pattern-name>
  Updated: <timestamp>
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

### Example 1: Update Zone Name

```bash
retrovue channel plan channel-1 plan zone update --id zone-1 --name "Prime Time Extended"
```

**Expected:** Zone name updated, other fields unchanged.

### Example 2: Update Time Window

```bash
retrovue channel plan channel-1 plan zone update --id zone-1 \
  --start-time "20:00:00" \
  --end-time "23:00:00"
```

**Expected:** Zone time window updated, validated against Grid boundaries.

### Example 3: Update Pattern Reference

```bash
retrovue channel plan channel-1 plan zone update --id zone-1 --pattern "new-pattern"
```

**Expected:** Zone pattern reference updated, validated for plan consistency.

### Example 4: Disable Zone

```bash
retrovue channel plan channel-1 plan zone update --id zone-1 --disabled
```

**Expected:** Zone `enabled` set to false.

### Example 5: Invalid - Grid Not Divisible

```bash
retrovue channel plan channel-1 plan zone update --id zone-1 \
  --start-time "00:00:00" \
  --end-time "01:15:00"
```

**Expected:** Exit 1, error: "Error: Zone duration must be divisible by channel grid_block_minutes (30). Zone duration: 75 minutes"

## Test Coverage Requirements

Tests MUST verify:

1. Successful partial updates (single field, multiple fields)
2. Zone resolution (valid and invalid cases)
3. Name uniqueness validation on update
4. Pattern-plan consistency validation on update
5. Time window validation on update
6. Grid divisibility validation on update
7. All domain-level validation contracts apply to updated fields
8. Timestamp updates correctly
9. Unchanged fields remain intact
10. JSON output format
11. Error message clarity

## Related Contracts

- [ZoneContract](ZoneContract.md) - Zone domain validation contracts
- [ZoneAddContract](ZoneAddContract.md) - Zone creation operations
- [ZoneListContract](ZoneListContract.md) - Zone listing operations
- [ZoneShowContract](ZoneShowContract.md) - Zone display operations
- [ZoneDeleteContract](ZoneDeleteContract.md) - Zone deletion operations

## See Also

- [Domain: Zone](../../domain/Zone.md) - Complete Zone domain documentation


