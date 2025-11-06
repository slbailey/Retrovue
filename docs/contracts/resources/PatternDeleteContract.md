# Pattern Delete Contract

_Related: [PatternContract](PatternContract.md) • [PatternAddContract](PatternAddContract.md) • [Domain: Pattern](../../domain/Pattern.md) • [Domain: SchedulePlan](../../domain/SchedulePlan.md) • [Domain: Zone](../../domain/Zone.md) • [_ops/DestructiveOperationConfirmation](../_ops/DestructiveOperationConfirmation.md)_

## Purpose

This contract defines the behavior of the `retrovue channel plan <channel> <plan> pattern delete` command, which deletes an existing Pattern from a SchedulePlan.

## Command Syntax

```bash
retrovue channel plan <channel> <plan> pattern delete --id <pattern-id> \
  [--yes] \
  [--json] [--test-db]
```

## Required Arguments

- `<channel>` - Channel identifier (UUID or slug)
- `<plan>` - SchedulePlan identifier (UUID or name)
- `--id <pattern-id>` - Pattern identifier (UUID or name)

## Optional Options

- `--yes` - Non-interactive confirmation for destructive action
- `--json` - Output in JSON format
- `--test-db` - Use test database context

## Behavior Contract Rules (B-#)

### B-1: Pattern Resolution

**Rule:** The Pattern identified by `--id` MUST exist within the specified plan.

**Behavior:**
- If Pattern not found → exit 1, error message: "Error: Pattern '<id>' not found in plan '<plan>'"
- If Pattern belongs to different plan → exit 1, error message: "Error: Pattern '<id>' does not belong to plan '<plan>'"

### B-2: Destructive Operation Confirmation

**Rule:** Deletion MUST require confirmation unless `--yes` is provided.

**Behavior:**
- Without `--yes` → prompt for confirmation: "Are you sure you want to delete Pattern '<name>'? This will affect Zones referencing this Pattern. (yes/no): "
- With `--yes` → proceed without prompt
- If confirmation refused → exit 1, no deletion
- Tests MUST use `--yes` for non-interactive execution

### B-3: Dependency Check

**Rule:** Pattern deletion MUST check for dependencies and provide guidance.

**Behavior:**
- If Pattern is referenced by Zones → exit 1, error: "Error: Cannot delete Pattern '<name>'. Pattern is referenced by <count> zone(s). Remove Zone references first: retrovue channel plan <channel> <plan> zone update --id <zone-id> --pattern <other-pattern-id>"
- If Pattern has Programs referencing it → Warning: "Warning: Pattern has <count> program(s) referencing it. Programs will be orphaned. Consider removing Programs from Pattern first."
- If no Zone dependencies → proceed with deletion (Program references can be orphaned or handled separately)

### B-4: JSON Output

**Rule:** `--json` MUST return valid JSON with deletion confirmation.

**Behavior:**
- JSON output includes deletion status and Pattern identifier
- Format: `{"status": "ok", "deleted": 1, "id": "<pattern-uuid>"}`

## Data Contract Rules (D-#)

### D-1: Pattern Deletion

**Rule:** Pattern record MUST be removed from `patterns` table when deletion succeeds.

**Behavior:**
- One row removed from `patterns` table
- Pattern `id` no longer exists in database
- Foreign key constraints prevent orphaned Zone references

### D-2: Cascade Behavior

**Rule:** Pattern deletion MUST handle dependent relationships appropriately.

**Behavior:**
- Programs referencing the Pattern are NOT automatically deleted (Programs belong to Plan, not Pattern)
- Programs with `pattern_id` referencing deleted Pattern may become orphaned (pattern_id set to null or handled separately)
- Zones referencing the Pattern must be updated or deleted first (dependency check prevents deletion)

### D-3: Transaction Boundaries

**Rule:** Pattern deletion MUST be atomic within a transaction.

**Behavior:**
- Dependency check occurs before deletion
- On failure, no partial state persisted
- Rollback on any error

### D-4: Test DB Isolation

**Rule:** `--test-db` MUST isolate from production data.

**Behavior:**
- Test database completely isolated
- No production data affected
- Test data cleaned up after test session

## Success Behavior

On successful deletion:

**Exit Code:** 0

**Output (non-JSON):**
```
Pattern deleted: <pattern-name-or-id>
```

**Output (JSON):**
```json
{
  "status": "ok",
  "deleted": 1,
  "id": "<pattern-uuid>"
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

### Example 1: Delete Pattern with Confirmation

```bash
retrovue channel plan channel-1 weekday-plan pattern delete --id pattern-1 --yes
```

**Expected:** Pattern deleted after confirmation.

### Example 2: Delete Pattern Blocked by Zone Dependencies

```bash
retrovue channel plan channel-1 weekday-plan pattern delete --id pattern-1 --yes
```

**Expected:** Exit 1, error: "Error: Cannot delete Pattern '<name>'. Pattern is referenced by <count> zone(s). Remove Zone references first: retrovue channel plan <channel> <plan> zone update --id <zone-id> --pattern <other-pattern-id>"

### Example 3: Pattern Not Found

```bash
retrovue channel plan channel-1 weekday-plan pattern delete --id non-existent --yes
```

**Expected:** Exit 1, error: "Error: Pattern 'non-existent' not found in plan 'weekday-plan'"

## Test Coverage Requirements

Tests MUST verify:

1. Successful Pattern deletion
2. Pattern resolution (valid and invalid cases)
3. Confirmation prompt behavior (with and without `--yes`)
4. Dependency check (with and without Zone dependencies)
5. Program reference handling (warning vs. blocking)
6. Error message clarity
7. JSON output format
8. Transaction rollback on error
9. Test DB isolation

## Related Contracts

- [PatternContract](PatternContract.md) - Pattern domain validation contracts
- [PatternAddContract](PatternAddContract.md) - Pattern creation operations
- [PatternUpdateContract](PatternUpdateContract.md) - Pattern update operations
- [PatternListContract](PatternListContract.md) - Pattern listing operations
- [PatternShowContract](PatternShowContract.md) - Pattern display operations
- [_ops/DestructiveOperationConfirmation](../_ops/DestructiveOperationConfirmation.md) - Destructive operation safety

## See Also

- [Domain: Pattern](../../domain/Pattern.md) - Complete Pattern domain documentation
- [Domain: Zone](../../domain/Zone.md) - Zone domain documentation (references Patterns)


