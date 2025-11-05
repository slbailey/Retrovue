# Schedule Template Block Instance Contract

_Related: [Domain: ScheduleTemplateBlock](../../domain/ScheduleTemplateBlock.md) • [Domain: ScheduleTemplate](../../domain/ScheduleTemplate.md) • [SchedulePlanInvariantsContract](SchedulePlanInvariantsContract.md)_

## Purpose

Define the behavioral contract for ScheduleTemplateBlockInstance operations in RetroVue (via `retrovue schedule-template block` commands). Block instances link standalone ScheduleTemplateBlocks to ScheduleTemplates with template-specific timing (start_time, end_time). The standalone blocks define content type constraints (rule_json guardrails), while instances provide the timing context within templates.

---

## Command Shape

### Add Block Instance

```
retrovue schedule-template block add \
  --template <name-or-uuid> \
  --block <name-or-uuid> \
  --start-time <HH:MM|HH:MM+1> \
  --end-time <HH:MM|HH:MM+1> \
  [--json] [--test-db]
```

**Time Format**: Times support `HH:MM` or `HH:MM+1` format where `+1` indicates the next calendar day. Broadcast days run from 06:00 to 06:00+1, so blocks can span midnight (e.g., `22:00` to `04:00` is valid, but `22:00` to `08:00` crosses the broadcast day boundary).

### Update Block Instance

```
retrovue schedule-template block update \
  --id <uuid> \
  [--start-time <HH:MM|HH:MM+1>] \
  [--end-time <HH:MM|HH:MM+1>] \
  [--json] [--test-db]
```

### Delete Block Instance

```
retrovue schedule-template block delete \
  --id <uuid> \
  [--yes] [--json] [--test-db]
```

### List Block Instances

```
retrovue schedule-template block list \
  --template <name-or-uuid> \
  [--json] [--test-db]
```

### Show Block Instance

```
retrovue schedule-template block show \
  --id <uuid> \
  [--json] [--test-db]
```

---

## Parameters

### Add Parameters

- `--template` (required): Template identifier - accepts either name or UUID (case-insensitive name lookup)
- `--block` (required): Standalone block identifier - accepts either name or UUID (case-insensitive name lookup). The block's rule_json defines content type constraints (guardrails) for this instance.
- `--start-time` (required): Block instance start time in "HH:MM" or "HH:MM+1" format (local wallclock time, template-specific). The `+1` suffix indicates the next calendar day. Broadcast days run from 06:00 to 06:00+1, so blocks can span midnight (e.g., `22:00` to `04:00` is valid).
- `--end-time` (required): Block instance end time in "HH:MM" or "HH:MM+1" format (local wallclock time, template-specific). Must be after start_time and within the same broadcast day (cannot cross the 06:00+1 boundary).
- `--json` (optional): Machine-readable output
- `--test-db` (optional): Use isolated test database session

### Update Parameters

- `--id` (required): UUID of the ScheduleTemplateBlockInstance to update (only timing can be updated, not the block or template)
- `--start-time` (optional): New block instance start time in "HH:MM" or "HH:MM+1" format
- `--end-time` (optional): New block instance end time in "HH:MM" or "HH:MM+1" format
- `--json` (optional): Machine-readable output
- `--test-db` (optional): Use isolated test database session

### Delete Parameters

- `--id` (required): UUID of the ScheduleTemplateBlockInstance to delete
- `--yes` (optional): Skip confirmation prompt
- `--json` (optional): Machine-readable output
- `--test-db` (optional): Use isolated test database session

### List Parameters

- `--template` (required): Template identifier - accepts either name or UUID (case-insensitive name lookup)
- `--json` (optional): Machine-readable output
- `--test-db` (optional): Use isolated test database session

### Show Parameters

- `--id` (required): UUID of the ScheduleTemplateBlockInstance to display
- `--json` (optional): Machine-readable output
- `--test-db` (optional): Use isolated test database session

---

## Safety Expectations

- **Add**: Creates exactly one `ScheduleTemplateBlockInstance` row linking a standalone block to a template with timing. Validates time format, non-overlap within template, and that both template and block exist.
- **Update**: Modifies existing block instance timing. Re-validates all constraints (time format, non-overlap within template). Cannot change the block or template reference.
- **Delete**: Removes block instance. Requires confirmation unless `--yes` provided. Does not affect the standalone block or template.
- **No side effects**: Operations affect only the specified block instance. Standalone blocks and templates remain unchanged.
- `--test-db` MUST isolate from production data.

---

## Output Format

### Human-Readable (Add)

```
Template block created:
  ID: 550e8400-e29b-41d4-a716-446655440000
  Template: Morning Cartoons
  Start Time: 06:00
  End Time: 09:00
  Rule JSON: {"tags": ["cartoon"], "rating_max": "TV-Y"}
  Created: 2025-01-01 12:00:00
```

### JSON (Add)

```json
{
  "status": "ok",
  "block": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "template_id": "123e4567-e89b-12d3-a456-426614174000",
    "start_time": "06:00",
    "end_time": "09:00",
    "rule_json": {"tags": ["cartoon"], "rating_max": "TV-Y"},
    "created_at": "2025-01-01T12:00:00Z",
    "updated_at": null
  }
}
```

---

## Exit Codes

- `0`: Operation completed successfully
- `1`: Validation failed, referential integrity violation, overlap detected, or DB failure

---

## Behavior Contract Rules (B-#)

### Time Format and Logic

- **B-1:** `start-time` and `end-time` MUST be in "HH:MM" format where HH is 00-23 and MM is 00-59
- **B-2:** `start-time` MUST be less than `end-time` (start_time < end_time)
- **B-3:** Time format validation MUST occur before any database operations
- **B-4:** Invalid time formats MUST exit 1 with error: "Error: Invalid time format. Expected HH:MM (00:00-23:59)."
- **B-5:** Invalid time logic (start_time >= end_time) MUST exit 1 with error: "Error: start_time must be less than end_time."

### Non-Overlap Constraint

- **B-6:** Blocks within the same template MUST NOT overlap in time periods
- **B-7:** Overlap detection MUST check: `(start_time < other.end_time) AND (end_time > other.start_time)`
- **B-8:** Blocks that touch at boundaries (e.g., one ends at 09:00, another starts at 09:00) are allowed (not considered overlapping)
- **B-9:** Creating or updating a block that would overlap with existing blocks in the same template MUST exit 1 with error: "Error: Block overlaps with existing block(s) in template."
- **B-10:** Overlap validation MUST check all blocks in the same template, excluding the block being updated (if updating)

### Rule JSON Structure

- **B-11:** `rule-json` MUST be valid JSON syntax
- **B-12:** `rule-json` MUST be a JSON object (not array, string, or primitive)
- **B-13:** `rule-json` SHOULD contain at least one constraint field (tags, rating_max, duration_max, genre, etc.) but empty object `{}` is allowed
- **B-14:** Invalid JSON syntax MUST exit 1 with error: "Error: rule_json must be valid JSON."
- **B-15:** Non-object JSON (array, string, number, etc.) MUST exit 1 with error: "Error: rule_json must be a JSON object."

### Referential Integrity

- **B-16:** `template-id` MUST reference an existing ScheduleTemplate
- **B-17:** Creating a block with non-existent `template-id` MUST exit 1 with error: "Error: Template not found."
- **B-18:** Updating a block MUST verify the block exists
- **B-19:** Updating a non-existent block MUST exit 1 with error: "Error: Template block not found."
- **B-20:** Deleting a block MUST verify the block exists
- **B-21:** Deleting a non-existent block MUST exit 1 with error: "Error: Template block not found."
- **B-22:** Deleting a block with dependent SchedulePlanBlockAssignment records MUST exit 1 with error: "Error: Cannot delete block with active plan assignments. Archive or remove assignments first."

### Lifecycle Rules

#### Create

- **B-23:** Creating a block MUST persist the block with all provided fields
- **B-24:** Creating a block MUST initialize `created_at` and `updated_at` timestamps
- **B-25:** Creating a block MUST assign a UUID for the `id` field
- **B-26:** Creating a block MUST validate all constraints (time format, time logic, non-overlap, rule_json, referential integrity) before persisting

#### Update

- **B-27:** Updating a block MUST preserve existing field values for fields not provided in the update
- **B-28:** Updating a block MUST update `updated_at` timestamp
- **B-29:** Updating a block MUST validate all constraints (time format, time logic, non-overlap, rule_json) for the new values
- **B-30:** Updating a block MUST re-validate non-overlap with all other blocks in the template (excluding itself)
- **B-31:** At least one field (start-time, end-time, or rule-json) MUST be provided for update
- **B-32:** Updating with no fields provided MUST exit 1 with error: "Error: At least one field (--start-time, --end-time, or --rule-json) must be provided."

#### Delete

- **B-33:** Deleting a block MUST require confirmation unless `--yes` flag is provided
- **B-34:** Confirmation prompt MUST ask: "Are you sure you want to delete this template block? (yes/no): "
- **B-35:** Deleting a block MUST check for dependent SchedulePlanBlockAssignment records
- **B-36:** Deleting a block MUST permanently remove the block from the database
- **B-37:** Deleting a block MUST NOT affect other blocks in the template or the parent template

### Output Format

- **B-38:** `--json` flag MUST return valid JSON with the operation result
- **B-39:** Human-readable output MUST include all block fields (id, template_id, start_time, end_time, rule_json, timestamps)
- **B-40:** List command MUST show all blocks for the specified template in chronological order (by start_time)

### Test Database

- **B-41:** `--test-db` flag MUST behave identically in output shape and exit codes
- **B-42:** `--test-db` MUST NOT read/write production tables

---

## Data Contract Rules (D-#)

### Persistence

- **D-1:** Block records MUST be persisted in `schedule_template_blocks` table
- **D-2:** Timestamps MUST be stored in UTC with timezone information
- **D-3:** `template_id` MUST be stored as UUID foreign key reference
- **D-4:** `rule_json` MUST be stored as TEXT (PostgreSQL JSONB recommended for query efficiency)
- **D-5:** Database constraints MUST enforce `template_id` foreign key relationship

### Referential Integrity

- **D-6:** Foreign key constraint MUST prevent creating blocks with non-existent `template_id`
- **D-7:** Foreign key constraint SHOULD prevent deleting templates that have dependent blocks (CASCADE or RESTRICT based on schema design)
- **D-8:** Deleting a template MUST handle dependent blocks according to schema constraints (CASCADE deletes blocks, or RESTRICT prevents template deletion)

### Non-Overlap Enforcement

- **D-9:** Non-overlap constraint MAY be enforced at database level (exclusion constraint) or application level (validation)
- **D-10:** If enforced at database level, constraint MUST use exclusion constraint on `(template_id, start_time, end_time)` with time range overlap operator
- **D-11:** If enforced at application level, validation MUST occur before database commit

### Transaction Boundaries

- **D-12:** All create/update/delete operations MUST occur within a single database transaction
- **D-13:** Transaction MUST rollback on any validation failure
- **D-14:** Test database operations MUST use isolated transactions

---

## Tests

Planned tests:

- `tests/contracts/test_schedule_template_block_add_contract.py::test_block_add__success_human_output`
- `tests/contracts/test_schedule_template_block_add_contract.py::test_block_add__success_json_output`
- `tests/contracts/test_schedule_template_block_add_contract.py::test_block_add__invalid_time_format`
- `tests/contracts/test_schedule_template_block_add_contract.py::test_block_add__start_time_gte_end_time`
- `tests/contracts/test_schedule_template_block_add_contract.py::test_block_add__overlap_detection`
- `tests/contracts/test_schedule_template_block_add_contract.py::test_block_add__touching_blocks_allowed`
- `tests/contracts/test_schedule_template_block_add_contract.py::test_block_add__invalid_rule_json`
- `tests/contracts/test_schedule_template_block_add_contract.py::test_block_add__non_object_rule_json`
- `tests/contracts/test_schedule_template_block_add_contract.py::test_block_add__template_not_found`
- `tests/contracts/test_schedule_template_block_update_contract.py::test_block_update__success`
- `tests/contracts/test_schedule_template_block_update_contract.py::test_block_update__overlap_after_update`
- `tests/contracts/test_schedule_template_block_update_contract.py::test_block_update__block_not_found`
- `tests/contracts/test_schedule_template_block_delete_contract.py::test_block_delete__success_with_confirmation`
- `tests/contracts/test_schedule_template_block_delete_contract.py::test_block_delete__with_yes_flag`
- `tests/contracts/test_schedule_template_block_delete_contract.py::test_block_delete__with_dependent_assignments`
- `tests/contracts/test_schedule_template_block_delete_contract.py::test_block_delete__block_not_found`

---

## Error Conditions

### Time Validation Errors

- Invalid time format: exit 1, "Error: Invalid time format. Expected HH:MM (00:00-23:59)."
- Start time >= end time: exit 1, "Error: start_time must be less than end_time."

### Overlap Errors

- Overlapping block: exit 1, "Error: Block overlaps with existing block(s) in template."

### Rule JSON Errors

- Invalid JSON: exit 1, "Error: rule_json must be valid JSON."
- Non-object JSON: exit 1, "Error: rule_json must be a JSON object."

### Referential Integrity Errors

- Template not found: exit 1, "Error: Template not found."
- Block not found: exit 1, "Error: Template block not found."
- Block with dependencies: exit 1, "Error: Cannot delete block with active plan assignments. Archive or remove assignments first."

### Update Errors

- No fields provided: exit 1, "Error: At least one field (--start-time, --end-time, or --rule-json) must be provided."

---

## Example rule_json Structures

### Minimal (Empty Constraints)

```json
{}
```

### Tags Only

```json
{
  "tags": ["cartoon", "family"]
}
```

### Rating Constraint

```json
{
  "rating_max": "TV-Y7",
  "tags": ["cartoon"]
}
```

### Duration Constraint

```json
{
  "duration_max_minutes": 30,
  "tags": ["sitcom"]
}
```

### Genre Constraint

```json
{
  "genre": ["comedy", "family"],
  "rating_max": "TV-PG"
}
```

### Complex Constraints

```json
{
  "tags": ["cartoon", "family"],
  "rating_max": "TV-Y7",
  "duration_max_minutes": 30,
  "genre": ["comedy", "adventure"],
  "exclude_tags": ["horror", "violence"]
}
```

---

## See also

- [Domain: ScheduleTemplateBlock](../../domain/ScheduleTemplateBlock.md) - Complete domain documentation
- [Domain: ScheduleTemplate](../../domain/ScheduleTemplate.md) - Parent template entity
- [SchedulePlanInvariantsContract](SchedulePlanInvariantsContract.md) - Cross-entity invariants
- [CLI Data Guarantees](cross-domain/CLI_Data_Guarantees.md) - General CLI guarantees

