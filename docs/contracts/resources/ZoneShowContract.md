# Zone Show Contract

_Related: [ZoneContract](ZoneContract.md) • [ZoneAddContract](ZoneAddContract.md) • [Domain: Zone](../../domain/Zone.md) • [Domain: SchedulePlan](../../domain/SchedulePlan.md)_

## Purpose

This contract defines the behavior of the `retrovue channel plan <channel> <plan> zone show` command, which displays detailed information for a specific Zone.

## Command Syntax

```bash
retrovue channel plan <channel> <plan> zone show --id <zone-id> \
  [--json] [--test-db]
```

## Required Arguments

- `<channel>` - Channel identifier (UUID or slug)
- `<plan>` - SchedulePlan identifier (UUID or name)
- `--id <zone-id>` - Zone identifier (UUID or name)

## Optional Options

- `--json` - Output in JSON format
- `--test-db` - Use test database context

## Behavior Contract Rules (B-#)

### B-1: Channel and Plan Resolution

**Rule:** The command MUST resolve the channel and plan by their identifiers before showing the Zone.

**Behavior:**
- If channel is not found → exit 1, error message: "Error: Channel '<identifier>' not found"
- If plan is not found → exit 1, error message: "Error: Plan '<identifier>' not found"
- If plan does not belong to channel → exit 1, error message: "Error: Plan '<plan>' does not belong to channel '<channel>'"

### B-2: Zone Resolution

**Rule:** The Zone identified by `--id` MUST exist within the specified plan.

**Behavior:**
- If Zone not found → exit 1, error message: "Error: Zone '<id>' not found in plan '<plan>'"
- If Zone belongs to different plan → exit 1, error message: "Error: Zone '<id>' does not belong to plan '<plan>'"
- Zone must exist and be accessible

### B-3: JSON Output Format

**Rule:** `--json` MUST return valid JSON with complete Zone information.

**Behavior:**
- JSON object includes all Zone fields
- Includes related Pattern information (name, id)
- Format consistent with ZoneAddContract output

## Data Contract Rules (D-#)

### D-1: Read-Only Operation

**Rule:** Show operation MUST NOT modify database state.

**Behavior:**
- No database writes
- No side effects
- Idempotent operation

### D-2: Complete Information

**Rule:** Show MUST return all Zone fields and related information.

**Behavior:**
- All Zone fields included
- Pattern reference resolved to name/id
- Complete Zone state displayed

## Success Behavior

On successful show:

**Exit Code:** 0

**Output (non-JSON):**
```
Zone: <zone-name>
  ID: <zone-uuid>
  Plan: <plan-name>
  Start Time: <start-time>
  End Time: <end-time>
  Pattern: <pattern-name> (<pattern-uuid>)
  Day Filters: <day-filters-or-all-days>
  Enabled: <true/false>
  Effective Range: <start-date> to <end-date> (if provided)
  DST Policy: <policy-or-default>
  Created: <created-at>
  Updated: <updated-at>
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
    "pattern_name": "<pattern-name>",
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

### Example 1: Show Zone by UUID

```bash
retrovue channel plan channel-1 weekday-plan zone show --id 550e8400-e29b-41d4-a716-446655440000
```

**Expected:** Detailed Zone information displayed.

### Example 2: Show Zone by Name

```bash
retrovue channel plan channel-1 weekday-plan zone show --id "Prime Time"
```

**Expected:** Zone found by name and displayed.

### Example 3: JSON Output

```bash
retrovue channel plan channel-1 weekday-plan zone show --id zone-1 --json
```

**Expected:** JSON object with complete Zone information.

## Test Coverage Requirements

Tests MUST verify:

1. Successful Zone display
2. Zone resolution by UUID and name
3. Channel and plan resolution (valid and invalid cases)
4. Zone not found error handling
5. Zone from different plan error handling
6. JSON output format
7. Read-only operation (no side effects)
8. Complete information display

## Related Contracts

- [ZoneContract](ZoneContract.md) - Zone domain validation contracts
- [ZoneAddContract](ZoneAddContract.md) - Zone creation operations
- [ZoneUpdateContract](ZoneUpdateContract.md) - Zone update operations
- [ZoneListContract](ZoneListContract.md) - Zone listing operations
- [ZoneDeleteContract](ZoneDeleteContract.md) - Zone deletion operations

## See Also

- [Domain: Zone](../../domain/Zone.md) - Complete Zone domain documentation


