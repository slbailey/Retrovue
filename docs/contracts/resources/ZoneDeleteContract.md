# Zone Delete Contract

_Related: [ZoneContract](ZoneContract.md) • [ZoneAddContract](ZoneAddContract.md) • [Domain: Zone](../../domain/Zone.md) • [Domain: SchedulePlan](../../domain/SchedulePlan.md) • [_ops/DestructiveOperationConfirmation](../_ops/DestructiveOperationConfirmation.md)_

## Purpose

This contract defines the behavior of the `retrovue channel plan <channel> <plan> zone delete` command, which deletes an existing Zone from a SchedulePlan.

## Command Syntax

```bash
retrovue channel plan <channel> <plan> zone delete --id <zone-id> \
  [--yes] \
  [--json] [--test-db]
```

## Required Arguments

- `<channel>` - Channel identifier (UUID or slug)
- `<plan>` - SchedulePlan identifier (UUID or name)
- `--id <zone-id>` - Zone identifier (UUID or name)

## Optional Options

- `--yes` - Non-interactive confirmation for destructive action
- `--json` - Output in JSON format
- `--test-db` - Use test database context

## Behavior Contract Rules (B-#)

### B-1: Zone Resolution

**Rule:** The Zone identified by `--id` MUST exist within the specified plan.

**Behavior:**
- If Zone not found → exit 1, error message: "Error: Zone '<id>' not found in plan '<plan>'"
- If Zone belongs to different plan → exit 1, error message: "Error: Zone '<id>' does not belong to plan '<plan>'"

### B-2: Destructive Operation Confirmation

**Rule:** Deletion MUST require confirmation unless `--yes` is provided.

**Behavior:**
- Without `--yes` → prompt for confirmation: "Are you sure you want to delete Zone '<name>'? (yes/no): "
- With `--yes` → proceed without prompt
- If confirmation refused → exit 1, no deletion
- Tests MUST use `--yes` for non-interactive execution

### B-3: Dependency Check

**Rule:** Zone deletion MUST check for dependencies and provide guidance.

**Behavior:**
- If Zone is referenced by ScheduleDays → exit 1, error: "Error: Cannot delete Zone '<name>'. Zone is referenced by <count> schedule day(s). Consider disabling the Zone instead with: retrovue channel plan <channel> <plan> zone update --id <zone-id> --disabled"
- If no dependencies → proceed with deletion
- Deletion allowed only if Zone has no dependent ScheduleDays

### B-4: JSON Output

**Rule:** `--json` MUST return valid JSON with deletion confirmation.

**Behavior:**
- JSON output includes deletion status and Zone identifier
- Format: `{"status": "ok", "deleted": 1, "id": "<zone-uuid>"}`

## Data Contract Rules (D-#)

### D-1: Zone Deletion

**Rule:** Zone record MUST be removed from `zones` table when deletion succeeds.

**Behavior:**
- One row removed from `zones` table
- Zone `id` no longer exists in database
- Foreign key constraints prevent orphaned references

### D-2: Cascade Behavior

**Rule:** Zone deletion MUST handle dependent relationships appropriately.

**Behavior:**
- Programs referencing Zone's Pattern are NOT deleted (Pattern belongs to Plan, not Zone)
- ScheduleDays referencing Zone may prevent deletion (dependency check)
- No orphaned references created

### D-3: Transaction Boundaries

**Rule:** Zone deletion MUST be atomic within a transaction.

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
Zone deleted: <zone-name>
```

**Output (JSON):**
```json
{
  "status": "ok",
  "deleted": 1,
  "id": "<zone-uuid>"
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

### Example 1: Delete Zone with Confirmation

```bash
retrovue channel plan channel-1 weekday-plan zone delete --id zone-1 --yes
```

**Expected:** Zone deleted after confirmation.

### Example 2: Delete Zone Blocked by Dependencies

```bash
retrovue channel plan channel-1 weekday-plan zone delete --id zone-1 --yes
```

**Expected:** Exit 1, error: "Error: Cannot delete Zone '<name>'. Zone is referenced by <count> schedule day(s). Consider disabling the Zone instead with: retrovue channel plan <channel> <plan> zone update --id <zone-id> --disabled"

### Example 3: Zone Not Found

```bash
retrovue channel plan channel-1 weekday-plan zone delete --id non-existent --yes
```

**Expected:** Exit 1, error: "Error: Zone 'non-existent' not found in plan 'weekday-plan'"

## Test Coverage Requirements

Tests MUST verify:

1. Successful Zone deletion
2. Zone resolution (valid and invalid cases)
3. Confirmation prompt behavior (with and without `--yes`)
4. Dependency check (with and without dependencies)
5. Error message clarity
6. JSON output format
7. Transaction rollback on error
8. Test DB isolation

## Related Contracts

- [ZoneContract](ZoneContract.md) - Zone domain validation contracts
- [ZoneAddContract](ZoneAddContract.md) - Zone creation operations
- [ZoneUpdateContract](ZoneUpdateContract.md) - Zone update operations
- [ZoneListContract](ZoneListContract.md) - Zone listing operations
- [ZoneShowContract](ZoneShowContract.md) - Zone display operations
- [_ops/DestructiveOperationConfirmation](../_ops/DestructiveOperationConfirmation.md) - Destructive operation safety

## See Also

- [Domain: Zone](../../domain/Zone.md) - Complete Zone domain documentation

