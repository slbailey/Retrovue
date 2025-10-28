# Collection Wipe

## Purpose

Ensure that wiping a collection (e.g., channels, schedules, or media metadata) can be tested safely in isolation before running against production data.

## Scope

This contract applies to all RetroVue subsystems where bulk deletion of records may occur, including administrative cleanup tasks and test harness resets.

## Design Principles

- **Safety first:** No destructive operation runs against live data during automated tests.
- **Clarity:** Command syntax must be intuitive for a human operator.
- **Mock-first validation:** All wipe commands must first be tested using a mock or test database.

## CLI Syntax

```
retrovue collection wipe <collection_name> [--dry-run] [--confirm] [--test-db]
```

### Parameters

- `collection_name`: Target collection to wipe (e.g., `channels`, `playlog`, `epg`).
- `--dry-run`: Shows what would be deleted without performing the action.
- `--confirm`: Required flag to proceed with actual deletion.
- `--test-db`: Explicitly directs the command to the mock/test database environment.

### Examples

```
# Preview what would be wiped in test DB
retrovue collection wipe channels --test-db --dry-run

# Execute wipe in test DB
retrovue collection wipe channels --test-db --confirm

# Execute wipe in production (manual only, after test validation)
retrovue collection wipe channels --confirm
```

## Testing Procedure

1. Run the command with `--test-db` to ensure deletion logic functions correctly.
2. Verify mock database reflects expected deletions.
3. Validate that production data remains intact.
4. Only after passing all validations may the command be run against live data manually.

## Documentation Integration

All CLI commands must have consistent, human-friendly syntax and appear in `CONTRIBUTING.md` under the "Operator Commands" section.






