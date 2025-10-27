# Source Delete

## Purpose

Define the behavioral contract for deleting content sources from RetroVue. This contract ensures safe, cascade-aware source deletion with proper confirmation and cleanup.

---

## Command Shape

```
retrovue source delete <source_id> [--force] [--test-db] [--confirm] [--json]
```

### Required Parameters

- `source_id`: Source identifier (UUID, external ID, or name)

### Optional Parameters

- `--force`: Skip confirmation prompts
- `--test-db`: Direct command to test database environment
- `--confirm`: Required flag to proceed with deletion
- `--json`: Output result in JSON format

---

## Safety Expectations

### Confirmation Model

**Without `--force`:**

- Interactive confirmation prompt required
- Shows source details and cascade impact
- User must type "yes" to confirm
- Cancellation returns exit code 0

**With `--force`:**

- No confirmation prompts
- Immediate deletion execution
- Use with extreme caution

### Cascade Deletion

Deleting a source removes:

- Source record
- All associated SourceCollection records
- All associated PathMapping records
- Any other related data through foreign key constraints

---

## Output Format

### Human-Readable Output

**Confirmation Prompt:**

```
Are you sure you want to delete source 'My Plex Server' (ID: 4b2b05e7-d7d2-414a-a587-3f5df9b53f44)?
This will also delete:
  - 3 collections
  - 12 path mappings
This action cannot be undone.
Type 'yes' to confirm:
```

**Success Output:**

```
Successfully deleted source: My Plex Server
  ID: 4b2b05e7-d7d2-414a-a587-3f5df9b53f44
  Type: plex
```

### JSON Output

```json
{
  "deleted": true,
  "source_id": "4b2b05e7-d7d2-414a-a587-3f5df9b53f44",
  "name": "My Plex Server",
  "type": "plex",
  "collections_deleted": 3,
  "path_mappings_deleted": 12
}
```

---

## Exit Codes

- `0`: Source deleted successfully or deletion cancelled
- `1`: Source not found, deletion failed, or validation error

---

## Data Effects

### Database Changes

1. **Cascade Deletion**:

   - Source record deleted
   - All SourceCollection records deleted (foreign key cascade)
   - All PathMapping records deleted (foreign key cascade)

2. **Audit Logging**:
   - Deletion logged with source details
   - Count of related records deleted
   - Timestamp of deletion

### Side Effects

- No external system cleanup required
- No filesystem changes
- Database transaction boundary maintained

---

## Behavior Contract Rules (B-#)

- **B-1:** The command MUST require interactive confirmation unless `--force` is provided.
- **B-2:** Interactive confirmation MUST require the user to type "yes" exactly to proceed.
- **B-3:** The confirmation prompt MUST show source details and cascade impact count.
- **B-4:** When `--json` is supplied, output MUST include fields `"deleted"`, `"source_id"`, `"name"`, and `"type"`.
- **B-5:** On validation failure (source not found), the command MUST exit with code `1` and print "Error: Source 'X' not found".
- **B-6:** Cancellation of confirmation MUST return exit code `0` with message "Deletion cancelled".
- **B-7:** The `--force` flag MUST skip all confirmation prompts and proceed immediately.

---

## Data Contract Rules (D-#)

- **D-1:** Source deletion MUST cascade delete all associated SourceCollection records.
- **D-2:** Source deletion MUST cascade delete all associated PathMapping records.
- **D-3:** All deletion operations MUST occur within a single transaction boundary.
- **D-4:** On transaction failure, ALL changes MUST be rolled back with no partial deletions.
- **D-5:** **PRODUCTION SAFETY**: A Source MUST NOT be deleted in production if any Asset from that Source has appeared in a PlaylogEvent or AsRunLog. `--force` MUST NOT override this rule.
- **D-6:** Deletion MUST be logged with source details, collection count, and path mapping count.
- **D-7:** The command MUST verify source existence before attempting deletion.

---

## Test Coverage Mapping

- `B-1..B-7` → `test_source_delete_contract.py`
- `D-1..D-7` → `test_source_delete_data_contract.py`

---

## Error Conditions

### Validation Errors

- Source not found: "Error: Source 'invalid-source' not found"
- Invalid source ID format: Handled gracefully with clear error message

### Database Errors

- Foreign key constraint violations: Transaction rollback
- Concurrent modification: Transaction rollback with retry suggestion

---

## Examples

### Interactive Deletion

```bash
# Delete with confirmation prompt
retrovue source delete "My Plex Server"

# Delete by external ID
retrovue source delete plex-5063d926

# Delete by UUID
retrovue source delete 4b2b05e7-d7d2-414a-a587-3f5df9b53f44
```

### Force Deletion

```bash
# Skip confirmation prompts
retrovue source delete "My Plex Server" --force

# Force deletion with JSON output
retrovue source delete plex-5063d926 --force --json
```

### Test Environment Usage

```bash
# Test deletion in isolated environment
retrovue source delete "Test Plex Server" --test-db --force

# Test confirmation flow
retrovue source delete "Test Source" --test-db
```

---

## Safety Guidelines

- Always use `--test-db` for testing deletion logic
- Verify cascade impact before using `--force`
- Use `--dry-run` equivalent by checking source details first
- Confirm source identification before deletion
