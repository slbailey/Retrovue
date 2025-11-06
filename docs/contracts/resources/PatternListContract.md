# Pattern List Contract

_Related: [PatternContract](PatternContract.md) • [PatternAddContract](PatternAddContract.md) • [Domain: Pattern](../../domain/Pattern.md) • [Domain: SchedulePlan](../../domain/SchedulePlan.md)_

## Purpose

This contract defines the behavior of the `retrovue channel plan <channel> <plan> pattern list` command, which lists all Patterns within a SchedulePlan.

## Command Syntax

```bash
retrovue channel plan <channel> <plan> pattern list \
  [--json] [--test-db]
```

## Required Arguments

- `<channel>` - Channel identifier (UUID or slug)
- `<plan>` - SchedulePlan identifier (UUID or name)

## Optional Options

- `--json` - Output in JSON format
- `--test-db` - Use test database context

## Behavior Contract Rules (B-#)

### B-1: Channel and Plan Resolution

**Rule:** The command MUST resolve the channel and plan by their identifiers before listing Patterns.

**Behavior:**
- If channel is not found → exit 1, error message: "Error: Channel '<identifier>' not found"
- If plan is not found → exit 1, error message: "Error: Plan '<identifier>' not found"
- If plan does not belong to channel → exit 1, error message: "Error: Plan '<plan>' does not belong to channel '<channel>'"

### B-2: Empty Result Handling

**Rule:** Empty results MUST be handled gracefully (not an error).

**Behavior:**
- If no Patterns found → exit 0, show empty list or message
- Empty list is valid output, not an error condition

### B-3: Sort Order

**Rule:** Patterns SHOULD be sorted deterministically for consistent output.

**Behavior:**
- Recommended sort: by `name` ascending (nulls last), then by `created_at` ascending
- Sort order must be consistent across invocations
- JSON output order matches human-readable order

### B-4: Program Count Display

**Rule:** Pattern listing SHOULD include the count of Programs referencing each Pattern.

**Behavior:**
- Each Pattern entry shows number of Programs that reference it
- Program count helps operators understand Pattern usage
- Program count is included in both human-readable and JSON output

### B-5: JSON Output Format

**Rule:** `--json` MUST return valid JSON array of Pattern objects.

**Behavior:**
- JSON array contains all matching Patterns
- Each Pattern object includes all fields plus Program count
- Format consistent with PatternAddContract output

## Data Contract Rules (D-#)

### D-1: Read-Only Operation

**Rule:** List operation MUST NOT modify database state.

**Behavior:**
- No database writes
- No side effects
- Idempotent operation

### D-2: Query Accuracy

**Rule:** Listed Patterns MUST belong to the specified SchedulePlan.

**Behavior:**
- Plan membership verified
- No Patterns from other plans included
- Program counts are accurate for each Pattern

## Success Behavior

On successful listing:

**Exit Code:** 0

**Output (non-JSON):**
```
Patterns in plan '<plan-name>':
  ID                                  Name                    Programs  Description
  --------------------------------------------------------------------------------------------
  <pattern-uuid>                      Prime Time Pattern      3         Evening drama and movies
  <pattern-uuid>                      Classic Sitcoms         5         Rotating classic sitcoms
  <pattern-uuid>                      (unnamed)               0         
```

**Output (JSON):**
```json
{
  "status": "ok",
  "patterns": [
    {
      "id": "<pattern-uuid>",
      "plan_id": "<plan-uuid>",
      "name": "Prime Time Pattern",
      "description": "Evening drama and movies",
      "program_count": 3,
      "created_at": "<timestamp>",
      "updated_at": "<timestamp>"
    },
    {
      "id": "<pattern-uuid>",
      "plan_id": "<plan-uuid>",
      "name": null,
      "description": null,
      "program_count": 0,
      "created_at": "<timestamp>",
      "updated_at": "<timestamp>"
    }
  ],
  "count": 2
}
```

## Empty Result Behavior

If no Patterns found:

**Exit Code:** 0

**Output (non-JSON):**
```
No patterns found in plan '<plan-name>'.
```

**Output (JSON):**
```json
{
  "status": "ok",
  "patterns": [],
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

### Example 1: List All Patterns

```bash
retrovue channel plan channel-1 weekday-plan pattern list
```

**Expected:** List all Patterns in the plan.

### Example 2: JSON Output

```bash
retrovue channel plan channel-1 weekday-plan pattern list --json
```

**Expected:** JSON array of all Patterns.

## Test Coverage Requirements

Tests MUST verify:

1. Successful listing with Patterns present
2. Empty result handling (no Patterns)
3. Channel and plan resolution (valid and invalid cases)
4. Sort order consistency
5. Program count accuracy
6. JSON output format
7. Read-only operation (no side effects)

## Related Contracts

- [PatternContract](PatternContract.md) - Pattern domain validation contracts
- [PatternAddContract](PatternAddContract.md) - Pattern creation operations
- [PatternUpdateContract](PatternUpdateContract.md) - Pattern update operations
- [PatternShowContract](PatternShowContract.md) - Pattern display operations
- [PatternDeleteContract](PatternDeleteContract.md) - Pattern deletion operations

## See Also

- [Domain: Pattern](../../domain/Pattern.md) - Complete Pattern domain documentation


