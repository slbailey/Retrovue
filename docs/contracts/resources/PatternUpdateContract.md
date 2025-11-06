# Pattern Update Contract

_Related: [PatternContract](PatternContract.md) • [PatternAddContract](PatternAddContract.md) • [Domain: Pattern](../../domain/Pattern.md) • [Domain: SchedulePlan](../../domain/SchedulePlan.md)_

## Purpose

This contract defines the behavior of the `retrovue channel plan <channel> <plan> pattern update` command, which updates an existing Pattern within a SchedulePlan.

## Command Syntax

```bash
retrovue channel plan <channel> <plan> pattern update --id <pattern-id> \
  [--name <string>] \
  [--description <string>] \
  [--json] [--test-db]
```

## Required Arguments

- `<channel>` - Channel identifier (UUID or slug)
- `<plan>` - SchedulePlan identifier (UUID or name)
- `--id <pattern-id>` - Pattern identifier (UUID or name)

## Optional Options

All options are optional; only provided fields are updated:

- `--name <string>` - Pattern name (must remain unique within plan if changed)
- `--description <string>` - Pattern description
- `--json` - Output in JSON format
- `--test-db` - Use test database context

## Behavior Contract Rules (B-#)

### B-1: Pattern Resolution

**Rule:** The Pattern identified by `--id` MUST exist within the specified plan.

**Behavior:**
- If Pattern not found → exit 1, error message: "Error: Pattern '<id>' not found in plan '<plan>'"
- If Pattern belongs to different plan → exit 1, error message: "Error: Pattern '<id>' does not belong to plan '<plan>'"
- Pattern must exist and be accessible

### B-2: Partial Updates

**Rule:** Only specified fields MUST be updated; others remain unchanged.

**Behavior:**
- If `--name` not provided → name unchanged
- If `--description` not provided → description unchanged
- All unspecified fields retain current values
- Update applies only to provided fields

### B-3: Name Uniqueness on Update

**Rule:** If name is updated, it MUST remain unique within the SchedulePlan (excluding current Pattern).

**Behavior:**
- If new name conflicts with another Pattern in same plan → exit 1, error: "Error: Pattern name '<name>' already exists in plan '<plan>'"
- Can update to same name (no-op)
- Can update to name that exists in different plan
- Can update to null name (removes name)
- Can update from null to a name

### B-4: JSON Output

**Rule:** `--json` MUST return valid JSON with the updated Pattern.

**Behavior:**
- JSON output includes all Pattern fields
- Timestamps reflect update time
- Format matches PatternAddContract JSON output

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

**Rule:** Pattern update MUST be atomic within a transaction.

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
Pattern updated:
  ID: <pattern-id>
  Plan: <plan-name>
  Name: <pattern-name-or-unnamed>
  Description: <description-or-none>
  Updated: <timestamp>
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

### Example 1: Update Pattern Name

```bash
retrovue channel plan channel-1 plan pattern update --id pattern-1 --name "Prime Time Extended"
```

**Expected:** Pattern name updated, other fields unchanged.

### Example 2: Update Description

```bash
retrovue channel plan channel-1 plan pattern update --id pattern-1 --description "Evening drama, movies, and specials"
```

**Expected:** Pattern description updated.

### Example 3: Remove Name (Set to Null)

```bash
retrovue channel plan channel-1 plan pattern update --id pattern-1 --name ""
```

**Expected:** Pattern name set to null (if empty string is interpreted as null removal).

### Example 4: Invalid - Name Conflict

```bash
retrovue channel plan channel-1 plan pattern update --id pattern-1 --name "Existing Pattern Name"
```

**Expected:** Exit 1, error: "Error: Pattern name 'Existing Pattern Name' already exists in plan '<plan>'"

## Test Coverage Requirements

Tests MUST verify:

1. Successful partial updates (single field, multiple fields)
2. Pattern resolution (valid and invalid cases)
3. Name uniqueness validation on update
4. Null name handling on update
5. Timestamp updates correctly
6. Unchanged fields remain intact
7. JSON output format
8. Error message clarity

## Related Contracts

- [PatternContract](PatternContract.md) - Pattern domain validation contracts
- [PatternAddContract](PatternAddContract.md) - Pattern creation operations
- [PatternListContract](PatternListContract.md) - Pattern listing operations
- [PatternShowContract](PatternShowContract.md) - Pattern display operations
- [PatternDeleteContract](PatternDeleteContract.md) - Pattern deletion operations

## See Also

- [Domain: Pattern](../../domain/Pattern.md) - Complete Pattern domain documentation


