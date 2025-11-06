# Zone List Contract

_Related: [ZoneContract](ZoneContract.md) • [ZoneAddContract](ZoneAddContract.md) • [Domain: Zone](../../domain/Zone.md) • [Domain: SchedulePlan](../../domain/SchedulePlan.md)_

## Purpose

This contract defines the behavior of the `retrovue channel plan <channel> <plan> zone list` command, which lists all Zones within a SchedulePlan.

## Command Syntax

```bash
retrovue channel plan <channel> <plan> zone list \
  [--enabled-only] \
  [--disabled-only] \
  [--json] [--test-db]
```

## Required Arguments

- `<channel>` - Channel identifier (UUID or slug)
- `<plan>` - SchedulePlan identifier (UUID or name)

## Optional Options

- `--enabled-only` - Show only enabled Zones
- `--disabled-only` - Show only disabled Zones
- `--json` - Output in JSON format
- `--test-db` - Use test database context

## Behavior Contract Rules (B-#)

### B-1: Channel and Plan Resolution

**Rule:** The command MUST resolve the channel and plan by their identifiers before listing Zones.

**Behavior:**
- If channel is not found → exit 1, error message: "Error: Channel '<identifier>' not found"
- If plan is not found → exit 1, error message: "Error: Plan '<identifier>' not found"
- If plan does not belong to channel → exit 1, error message: "Error: Plan '<plan>' does not belong to channel '<channel>'"

### B-2: Filtering Behavior

**Rule:** Zone listing MUST respect enabled/disabled filters if provided.

**Behavior:**
- If `--enabled-only` → show only Zones with `enabled=true`
- If `--disabled-only` → show only Zones with `enabled=false`
- If neither specified → show all Zones (enabled and disabled)
- Filters are mutually exclusive

### B-3: Empty Result Handling

**Rule:** Empty results MUST be handled gracefully (not an error).

**Behavior:**
- If no Zones found → exit 0, show empty list or message
- Empty list is valid output, not an error condition

### B-4: Sort Order

**Rule:** Zones SHOULD be sorted deterministically for consistent output.

**Behavior:**
- Recommended sort: by `start_time` ascending, then by `name` ascending
- Sort order must be consistent across invocations
- JSON output order matches human-readable order

### B-5: JSON Output Format

**Rule:** `--json` MUST return valid JSON array of Zone objects.

**Behavior:**
- JSON array contains all matching Zones
- Each Zone object includes all fields
- Format consistent with ZoneAddContract output

## Data Contract Rules (D-#)

### D-1: Read-Only Operation

**Rule:** List operation MUST NOT modify database state.

**Behavior:**
- No database writes
- No side effects
- Idempotent operation

### D-2: Query Accuracy

**Rule:** Listed Zones MUST match filter criteria exactly.

**Behavior:**
- Enabled filter applies correctly
- Plan membership verified
- No Zones from other plans included

## Success Behavior

On successful listing:

**Exit Code:** 0

**Output (non-JSON):**
```
Zones in plan '<plan-name>':
  ID                                  Name              Start      End        Pattern              Enabled
  ------------------------------------------------------------------------------------------------------------
  <zone-uuid>                         Base              00:00:00   24:00:00   base-pattern         ✅
  <zone-uuid>                         Prime Time        19:00:00   22:00:00   prime-time-pattern   ✅
  <zone-uuid>                         After Dark        22:00:00   05:00:00   late-night-pattern   ✅
```

**Output (JSON):**
```json
{
  "status": "ok",
  "zones": [
    {
      "id": "<zone-uuid>",
      "plan_id": "<plan-uuid>",
      "name": "Base",
      "start_time": "00:00:00",
      "end_time": "24:00:00",
      "pattern_id": "<pattern-uuid>",
      "day_filters": null,
      "enabled": true,
      "effective_start": null,
      "effective_end": null,
      "dst_policy": null,
      "created_at": "<timestamp>",
      "updated_at": "<timestamp>"
    },
    ...
  ],
  "count": 3
}
```

## Empty Result Behavior

If no Zones found:

**Exit Code:** 0

**Output (non-JSON):**
```
No zones found in plan '<plan-name>'.
```

**Output (JSON):**
```json
{
  "status": "ok",
  "zones": [],
  "count": 0
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

### Example 1: List All Zones

```bash
retrovue channel plan channel-1 weekday-plan zone list
```

**Expected:** List all Zones in the plan.

### Example 2: List Only Enabled Zones

```bash
retrovue channel plan channel-1 weekday-plan zone list --enabled-only
```

**Expected:** List only enabled Zones.

### Example 3: JSON Output

```bash
retrovue channel plan channel-1 weekday-plan zone list --json
```

**Expected:** JSON array of all Zones.

## Test Coverage Requirements

Tests MUST verify:

1. Successful listing with Zones present
2. Empty result handling (no Zones)
3. Channel and plan resolution (valid and invalid cases)
4. Enabled/disabled filtering
5. Sort order consistency
6. JSON output format
7. Read-only operation (no side effects)

## Related Contracts

- [ZoneContract](ZoneContract.md) - Zone domain validation contracts
- [ZoneAddContract](ZoneAddContract.md) - Zone creation operations
- [ZoneUpdateContract](ZoneUpdateContract.md) - Zone update operations
- [ZoneShowContract](ZoneShowContract.md) - Zone display operations
- [ZoneDeleteContract](ZoneDeleteContract.md) - Zone deletion operations

## See Also

- [Domain: Zone](../../domain/Zone.md) - Complete Zone domain documentation

