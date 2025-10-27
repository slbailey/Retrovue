# Enricher Remove

## Purpose

Define the behavioral contract for removing enricher instances from RetroVue. This contract ensures safe, cascade-aware enricher removal with proper confirmation and cleanup.

---

## Command Shape

```
retrovue enricher remove <enricher_id> [--force] [--test-db] [--confirm] [--json]
```

### Required Parameters

- `enricher_id`: Enricher instance identifier (UUID or enricher ID)

### Optional Parameters

- `--force`: Skip confirmation prompts
- `--test-db`: Direct command to test database environment
- `--confirm`: Required flag to proceed with removal
- `--json`: Output result in JSON format

---

## Safety Expectations

### Confirmation Model

**Without `--force`:**

- Interactive confirmation prompt required
- Shows enricher details and cascade impact
- User must type "yes" to confirm
- Cancellation returns exit code 0

**With `--force`:**

- No confirmation prompts
- Immediate removal execution
- Use with extreme caution

### Cascade Removal

Removing an enricher instance removes:

- Enricher instance record
- All associated attachment records (collections/channels)
- Any other related data through foreign key constraints

---

## Output Format

### Human-Readable Output

**Confirmation Prompt:**

```
Are you sure you want to remove enricher 'Video Analysis' (ID: enricher-ffprobe-a1b2c3d4)?
This will also remove:
  - 2 collection attachments
  - 0 channel attachments
This action cannot be undone.
Type 'yes' to confirm:
```

**Success Output:**

```
Successfully removed enricher: Video Analysis
  ID: enricher-ffprobe-a1b2c3d4
  Type: ffprobe
  Scope: ingest
```

### JSON Output

```json
{
  "removed": true,
  "enricher_id": "enricher-ffprobe-a1b2c3d4",
  "name": "Video Analysis",
  "type": "ffprobe",
  "scope": "ingest",
  "collection_attachments_removed": 2,
  "channel_attachments_removed": 0
}
```

---

## Exit Codes

- `0`: Enricher removed successfully or removal cancelled
- `1`: Enricher not found, removal failed, or validation error

---

## Data Effects

### Database Changes

1. **Cascade Removal**:

   - Enricher instance record deleted
   - All collection attachment records deleted (foreign key cascade)
   - All channel attachment records deleted (foreign key cascade)

2. **Audit Logging**:
   - Removal logged with enricher details
   - Count of related records deleted
   - Timestamp of removal

### Side Effects

- No external system cleanup required
- No filesystem changes
- Database transaction boundary maintained

---

## Behavior Contract Rules (B-#)

- **B-1:** The command MUST require interactive confirmation unless `--force` is provided.
- **B-2:** Interactive confirmation MUST require the user to type "yes" exactly to proceed.
- **B-3:** The confirmation prompt MUST show enricher details and cascade impact count.
- **B-4:** When `--json` is supplied, output MUST include fields `"removed"`, `"enricher_id"`, `"name"`, `"type"`, and `"scope"`.
- **B-5:** On validation failure (enricher not found), the command MUST exit with code `1` and print "Error: Enricher 'X' not found".
- **B-6:** Cancellation of confirmation MUST return exit code `0` with message "Removal cancelled".
- **B-7:** The `--force` flag MUST skip all confirmation prompts and proceed immediately.

---

## Data Contract Rules (D-#)

- **D-1:** Enricher removal MUST cascade delete all associated collection attachment records.
- **D-2:** Enricher removal MUST cascade delete all associated channel attachment records.
- **D-3:** All removal operations MUST occur within a single transaction boundary.
- **D-4:** On transaction failure, ALL changes MUST be rolled back with no partial deletions.
- **D-5:** **PRODUCTION SAFETY**: An Enricher MUST NOT be removed in production if it has been used in any active ingest or playout operations. `--force` MUST NOT override this rule.
- **D-6:** Removal MUST be logged with enricher details, collection count, and channel count.
- **D-7:** The command MUST verify enricher existence before attempting removal.

---

## Test Coverage Mapping

- `B-1..B-7` → `test_enricher_remove_contract.py`
- `D-1..D-7` → `test_enricher_remove_data_contract.py`

---

## Error Conditions

### Validation Errors

- Enricher not found: "Error: Enricher 'enricher-ffprobe-a1b2c3d4' not found"
- Invalid enricher ID format: Handled gracefully with clear error message

### Database Errors

- Foreign key constraint violations: Transaction rollback
- Concurrent modification: Transaction rollback with retry suggestion

---

## Examples

### Interactive Removal

```bash
# Remove with confirmation prompt
retrovue enricher remove enricher-ffprobe-a1b2c3d4

# Remove by enricher ID
retrovue enricher remove enricher-metadata-b2c3d4e5

# Remove by UUID
retrovue enricher remove 550e8400-e29b-41d4-a716-446655440000
```

### Force Removal

```bash
# Skip confirmation prompts
retrovue enricher remove enricher-ffprobe-a1b2c3d4 --force

# Force removal with JSON output
retrovue enricher remove enricher-metadata-b2c3d4e5 --force --json
```

### Test Environment Usage

```bash
# Test removal in isolated environment
retrovue enricher remove enricher-ffprobe-a1b2c3d4 --test-db --force

# Test confirmation flow
retrovue enricher remove enricher-metadata-b2c3d4e5 --test-db
```

---

## Safety Guidelines

- Always use `--test-db` for testing removal logic
- Verify cascade impact before using `--force`
- Use `--dry-run` equivalent by checking enricher details first
- Confirm enricher identification before removal

---

## See Also

- [Enricher List Types](EnricherListTypes.md) - List available enricher types
- [Enricher Add](EnricherAdd.md) - Create enricher instances
- [Enricher List](EnricherList.md) - List configured enricher instances
- [Enricher Update](EnricherUpdate.md) - Update enricher configurations
