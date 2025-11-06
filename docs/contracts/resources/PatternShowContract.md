# Pattern Show Contract

_Related: [PatternContract](PatternContract.md) • [PatternAddContract](PatternAddContract.md) • [Domain: Pattern](../../domain/Pattern.md) • [Domain: SchedulePlan](../../domain/SchedulePlan.md) • [Domain: Program](../../domain/Program.md)_

## Purpose

This contract defines the behavior of the `retrovue channel plan <channel> <plan> pattern show` command, which displays detailed information for a specific Pattern, including its ordered list of Programs.

## Command Syntax

```bash
retrovue channel plan <channel> <plan> pattern show --id <pattern-id> \
  [--json] [--test-db]
```

## Required Arguments

- `<channel>` - Channel identifier (UUID or slug)
- `<plan>` - SchedulePlan identifier (UUID or name)
- `--id <pattern-id>` - Pattern identifier (UUID or name)

## Optional Options

- `--json` - Output in JSON format
- `--test-db` - Use test database context

## Behavior Contract Rules (B-#)

### B-1: Channel and Plan Resolution

**Rule:** The command MUST resolve the channel and plan by their identifiers before showing the Pattern.

**Behavior:**
- If channel is not found → exit 1, error message: "Error: Channel '<identifier>' not found"
- If plan is not found → exit 1, error message: "Error: Plan '<identifier>' not found"
- If plan does not belong to channel → exit 1, error message: "Error: Plan '<plan>' does not belong to channel '<channel>'"

### B-2: Pattern Resolution

**Rule:** The Pattern identified by `--id` MUST exist within the specified plan.

**Behavior:**
- If Pattern not found → exit 1, error message: "Error: Pattern '<id>' not found in plan '<plan>'"
- If Pattern belongs to different plan → exit 1, error message: "Error: Pattern '<id>' does not belong to plan '<plan>'"
- Pattern must exist and be accessible

### B-3: Program List Display

**Rule:** Pattern show MUST display the ordered list of Programs that reference the Pattern.

**Behavior:**
- Programs are ordered by `order` ascending
- Each Program entry shows order, Program name/identifier, and content type
- Empty Patterns show no Programs (empty list)

### B-4: JSON Output Format

**Rule:** `--json` MUST return valid JSON with complete Pattern information including Programs.

**Behavior:**
- JSON object includes all Pattern fields
- Includes array of Programs ordered by `order`
- Each Program entry includes order, Program ID, name, and content type
- Format consistent with PatternAddContract output

## Data Contract Rules (D-#)

### D-1: Read-Only Operation

**Rule:** Show operation MUST NOT modify database state.

**Behavior:**
- No database writes
- No side effects
- Idempotent operation

### D-2: Complete Information

**Rule:** Show MUST return all Pattern fields and related Program information.

**Behavior:**
- All Pattern fields included
- All Programs referencing the Pattern included (ordered by `order`)
- Program order is accurate and deterministic

## Success Behavior

On successful show:

**Exit Code:** 0

**Output (non-JSON):**
```
Pattern: <pattern-name-or-unnamed>
  ID: <pattern-uuid>
  Plan: <plan-name>
  Description: <description-or-none>
  Programs:
    Order  Program                              Content Type
    -----------------------------------------------------------
    0      Cheers (series)                      Series
    1      The Big Bang Theory (series)         Series
    2      Movie Block (rule)                   Rule
  Created: <created-at>
  Updated: <updated-at>
```

**Output (JSON):**
```json
{
  "status": "ok",
  "pattern": {
    "id": "<pattern-uuid>",
    "plan_id": "<plan-uuid>",
    "name": "<pattern-name-or-null>",
    "description": "<description-or-null>",
    "created_at": "<timestamp>",
    "updated_at": "<timestamp>",
    "programs": [
      {
        "order": 0,
        "program_id": "<program-uuid>",
        "program_name": "Cheers",
        "content_type": "series"
      },
      {
        "order": 1,
        "program_id": "<program-uuid>",
        "program_name": "The Big Bang Theory",
        "content_type": "series"
      },
      {
        "order": 2,
        "program_id": "<program-uuid>",
        "program_name": "Movie Block",
        "content_type": "rule"
      }
    ],
    "program_count": 3
  }
}
```

## Empty Pattern Behavior

If Pattern has no Programs:

**Exit Code:** 0

**Output (non-JSON):**
```
Pattern: <pattern-name-or-unnamed>
  ID: <pattern-uuid>
  Plan: <plan-name>
  Description: <description-or-none>
  Programs: (empty)
```

**Output (JSON):**
```json
{
  "status": "ok",
  "pattern": {
    "id": "<pattern-uuid>",
    "plan_id": "<plan-uuid>",
    "name": "<pattern-name-or-null>",
    "description": "<description-or-null>",
    "created_at": "<timestamp>",
    "updated_at": "<timestamp>",
    "programs": [],
    "program_count": 0
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

### Example 1: Show Pattern by UUID

```bash
retrovue channel plan channel-1 weekday-plan pattern show --id 550e8400-e29b-41d4-a716-446655440000
```

**Expected:** Detailed Pattern information with Programs displayed.

### Example 2: Show Pattern by Name

```bash
retrovue channel plan channel-1 weekday-plan pattern show --id "Prime Time Pattern"
```

**Expected:** Pattern found by name and displayed.

### Example 3: JSON Output

```bash
retrovue channel plan channel-1 weekday-plan pattern show --id pattern-1 --json
```

**Expected:** JSON object with complete Pattern information including Programs.

## Test Coverage Requirements

Tests MUST verify:

1. Successful Pattern display
2. Pattern resolution by UUID and name
3. Channel and plan resolution (valid and invalid cases)
4. Pattern not found error handling
5. Pattern from different plan error handling
6. Program list ordering (by `order` ascending)
7. Empty Pattern handling (no Programs)
8. JSON output format
9. Read-only operation (no side effects)
10. Complete information display

## Related Contracts

- [PatternContract](PatternContract.md) - Pattern domain validation contracts
- [PatternAddContract](PatternAddContract.md) - Pattern creation operations
- [PatternUpdateContract](PatternUpdateContract.md) - Pattern update operations
- [PatternListContract](PatternListContract.md) - Pattern listing operations
- [PatternDeleteContract](PatternDeleteContract.md) - Pattern deletion operations

## See Also

- [Domain: Pattern](../../domain/Pattern.md) - Complete Pattern domain documentation
- [Domain: Program](../../domain/Program.md) - Program domain documentation


