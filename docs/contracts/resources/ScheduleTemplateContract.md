# Schedule Template Contract

_Related: [Domain: ScheduleTemplate](../../domain/ScheduleTemplate.md) • [Domain: ScheduleTemplateBlock](../../domain/ScheduleTemplateBlock.md) • [ScheduleTemplateBlockContract](ScheduleTemplateBlockContract.md) • [SchedulePlanInvariantsContract](SchedulePlanInvariantsContract.md)_

## Purpose

Define the behavioral contract for ScheduleTemplate operations in RetroVue. ScheduleTemplates are reusable, channel-agnostic shells that define 24-hour patterns of ScheduleTemplateBlock definitions. Each template represents a programming structure (blueprint) that can be used by multiple channels and plans. Templates are not channel-specific — they're assigned to channels through SchedulePlans and BroadcastScheduleDay.

---

## Command Shape

### Add Template

```
retrovue schedule-template add \
  --name <string> \
  [--description <string>] \
  [--active | --inactive] \
  [--json] [--test-db]
```

### Update Template

```
retrovue schedule-template update \
  --template <name-or-uuid> \
  [--name <string>] \
  [--description <string>] \
  [--active | --inactive] \
  [--json] [--test-db]
```

### Delete Template

```
retrovue schedule-template delete \
  --template <name-or-uuid> \
  [--yes] [--json] [--test-db]
```

### List Templates

```
retrovue schedule-template list \
  [--active-only] \
  [--json] [--test-db]
```

### Show Template

```
retrovue schedule-template show \
  --template <name-or-uuid> \
  [--json] [--test-db]
```

---

## Parameters

### Add Parameters

- `--name` (required): Template identifier (e.g., "All Sitcoms 24x7", "Morning News Block")
- `--description` (optional): Human-readable description of the template's programming intent
- `--active` / `--inactive` (optional): Initial active state. Default `--active`.
- `--json` (optional): Machine-readable output
- `--test-db` (optional): Use isolated test database session

### Update Parameters

- `--template` (required): Template identifier - accepts either name or UUID (case-insensitive name lookup)
- `--name` (optional): New template name
- `--description` (optional): New template description
- `--active` / `--inactive` (optional): Toggle active status
- `--json` (optional): Machine-readable output
- `--test-db` (optional): Use isolated test database session

### Delete Parameters

- `--template` (required): Template identifier - accepts either name or UUID (case-insensitive name lookup)
- `--yes` (optional): Skip confirmation prompt
- `--json` (optional): Machine-readable output
- `--test-db` (optional): Use isolated test database session

### List Parameters

- `--active-only` (optional): Show only active templates (is_active=true)
- `--json` (optional): Machine-readable output
- `--test-db` (optional): Use isolated test database session

### Show Parameters

- `--template` (required): Template identifier - accepts either name or UUID (case-insensitive name lookup)
- `--json` (optional): Machine-readable output
- `--test-db` (optional): Use isolated test database session

---

## Safety Expectations

- **Add**: Creates exactly one `ScheduleTemplate` row. Validates name uniqueness.
- **Update**: Modifies existing template. Re-validates name uniqueness if name changes.
- **Delete**: Removes template. Requires confirmation unless `--yes` provided. Checks for dependent entities (blocks, plans, schedule days).
- **No side effects**: Operations affect only the specified template and its relationships.
- `--test-db` MUST isolate from production data.

---

## Output Format

### Human-Readable (Add)

```
Template created:
  ID: 123e4567-e89b-12d3-a456-426614174000
  Name: All Sitcoms 24x7
  Description: 24-hour sitcom programming template
  Active: true
  Blocks: 0
  Created: 2025-01-01 12:00:00
```

### JSON (Add)

```json
{
  "status": "ok",
  "template": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "All Sitcoms 24x7",
    "description": "24-hour sitcom programming template",
    "is_active": true,
    "blocks_count": 0,
    "created_at": "2025-01-01T12:00:00Z",
    "updated_at": null
  }
}
```

### Human-Readable (Show)

```
Template:
  ID: 123e4567-e89b-12d3-a456-426614174000
  Name: All Sitcoms 24x7
  Description: 24-hour sitcom programming template
  Active: true
  Blocks (3):
    06:00-09:00: {"tags": ["cartoon"]}
    09:00-18:00: {"tags": ["sitcom"], "rating_max": "TV-PG"}
    18:00-24:00: {"tags": ["sitcom"], "rating_max": "TV-14"}
  Plans using this template: 2
  Created: 2025-01-01 12:00:00
  Updated: 2025-01-15 10:30:00
```

---

## Exit Codes

- `0`: Operation completed successfully
- `1`: Validation failed, referential integrity violation, or DB failure

---

## Behavior Contract Rules (T-#)

### Name Uniqueness

- **T-1:** Template `name` MUST be unique across all templates (case-insensitive)
- **T-2:** Creating a template with duplicate name MUST exit 1 with error: "Error: Template name already exists."
- **T-3:** Updating a template name to a duplicate name MUST exit 1 with error: "Error: Template name already exists."
- **T-4:** Name uniqueness validation MUST occur before any database operations
- **T-5:** Name comparison MUST be case-insensitive (e.g., "Template" and "template" are considered duplicates)

### Name Format

- **T-6:** Template `name` MUST be non-empty
- **T-7:** Template `name` max length MUST be ≤ 255 characters (enforced at database level)
- **T-8:** Creating or updating with empty name MUST exit 1 with error: "Error: Template name cannot be empty."
- **T-9:** Creating or updating with name exceeding 255 characters MUST exit 1 with error: "Error: Template name exceeds maximum length (255 characters)."

### Minimum Block Requirement

- **T-10:** Template MUST have at least one ScheduleTemplateBlock before it can be used in SchedulePlan creation
- **T-11:** Creating a SchedulePlan that references a template with no blocks MUST exit 1 with error: "Error: Template has no blocks. Add at least one block before creating a plan."
- **T-12:** Template can be created without blocks, but blocks MUST be added before template is usable
- **T-13:** Template validation SHOULD warn (but not fail) if template has no blocks when listing or showing

### Active Status and Assignability

- **T-14:** `is_active` flag governs whether template is eligible for assignment in new SchedulePlans
- **T-15:** Only templates where `is_active=true` are eligible for use in new SchedulePlan creation
- **T-16:** Creating a SchedulePlan that references an inactive template (`is_active=false`) MUST exit 1 with error: "Error: Template is not active. Activate template before creating a plan."
- **T-17:** `--active` flag sets `is_active=true`; `--inactive` flag sets `is_active=false`
- **T-18:** Default state for new templates is `is_active=true` (unless `--inactive` is specified)
- **T-19:** ScheduleService MUST exclude templates where `is_active=false` from schedule generation
- **T-20:** Archived templates (`is_active=false`) are excluded from scheduler assignment

### Referential Integrity

- **T-21:** Template cannot be deleted if it has dependent ScheduleTemplateBlock records
- **T-22:** Deleting a template with blocks MUST exit 1 with error: "Error: Cannot delete template with blocks. Remove all blocks first."
- **T-23:** Template cannot be deleted if it has dependent SchedulePlan records
- **T-24:** Deleting a template with plans MUST exit 1 with error: "Error: Cannot delete template with active plans. Archive template or remove plans first."
- **T-25:** Template cannot be deleted if it has dependent BroadcastScheduleDay records
- **T-26:** Deleting a template with schedule days MUST exit 1 with error: "Error: Cannot delete template with schedule days. Archive template first."
- **T-27:** Dependency check MUST verify: ScheduleTemplateBlock, SchedulePlan, and BroadcastScheduleDay
- **T-28:** Blocks MUST be cleaned up (deleted) before template deletion is allowed
- **T-29:** Referential integrity validation MUST occur before database deletion operation

### Template Reuse

- **T-30:** Templates are channel-agnostic and can be reused across multiple channels
- **T-31:** Same template CAN be referenced by multiple SchedulePlans
- **T-32:** Same template CAN be used by plans for different channels
- **T-33:** Template reuse MUST NOT violate any constraints (name uniqueness still applies)
- **T-34:** Template changes affect all plans that reference the template

### Lifecycle Rules

#### Create

- **T-35:** Creating a template MUST persist the template with all provided fields
- **T-36:** Creating a template MUST initialize `created_at` and `updated_at` timestamps
- **T-37:** Creating a template MUST assign a UUID for the `id` field
- **T-38:** Creating a template MUST initialize `is_active=true` unless `--inactive` is specified
- **T-39:** Creating a template MUST validate name uniqueness before persisting

#### Update

- **T-40:** Updating a template MUST preserve existing field values for fields not provided in the update
- **T-41:** Updating a template MUST update `updated_at` timestamp
- **T-42:** Updating template name MUST validate name uniqueness for the new name
- **T-43:** At least one field (name, description, or active status) MUST be provided for update
- **T-44:** Updating with no fields provided MUST exit 1 with error: "Error: At least one field (--name, --description, or --active/--inactive) must be provided."
- **T-45:** Updating `is_active` from `true` to `false` archives the template
- **T-46:** Updating `is_active` from `false` to `true` reactivates the template

#### Delete

- **T-47:** Deleting a template MUST require confirmation unless `--yes` flag is provided
- **T-48:** Confirmation prompt MUST ask: "Are you sure you want to delete this template? This will affect all plans using this template. (yes/no): "
- **T-49:** Deleting a template MUST check for dependent entities (blocks, plans, schedule days)
- **T-50:** Deleting a template MUST permanently remove the template from the database
- **T-51:** Deleting a template MUST NOT affect other templates

### Scheduler Assignment

- **T-52:** ScheduleService MUST only consider templates where `is_active=true` when resolving plans
- **T-53:** ScheduleService MUST exclude archived templates (`is_active=false`) from schedule generation
- **T-54:** Existing schedule days that reference archived templates remain valid but are not regenerated
- **T-55:** Archived templates remain readable but are not eligible for new schedule generation

### Output Format

- **T-56:** `--json` flag MUST return valid JSON with the operation result
- **T-57:** Human-readable output MUST include all template fields (id, name, description, is_active, blocks_count, timestamps)
- **T-58:** Show command MUST display associated blocks and plans count
- **T-59:** List command MUST show all templates (or only active if `--active-only` specified)

### Test Database

- **T-60:** `--test-db` flag MUST behave identically in output shape and exit codes
- **T-61:** `--test-db` MUST NOT read/write production tables

---

## Data Contract Rules (D-#)

### Persistence

- **D-1:** Template records MUST be persisted in `schedule_templates` table
- **D-2:** Timestamps MUST be stored in UTC with timezone information
- **D-3:** `name` MUST be stored as TEXT with uniqueness constraint
- **D-4:** `description` MUST be stored as TEXT (nullable)
- **D-5:** `is_active` MUST be stored as BOOLEAN (NOT NULL, default true)
- **D-6:** Database constraint MUST enforce `name` uniqueness

### Referential Integrity

- **D-7:** Foreign key constraints MUST prevent deleting templates that have dependent ScheduleTemplateBlock records (RESTRICT or CASCADE based on schema design)
- **D-8:** Foreign key constraints MUST prevent deleting templates that have dependent SchedulePlan records (RESTRICT or CASCADE based on schema design)
- **D-9:** Foreign key constraints MUST prevent deleting templates that have dependent BroadcastScheduleDay records (RESTRICT or CASCADE based on schema design)
- **D-10:** If CASCADE is used, deletion of template MUST cascade to dependent blocks (blocks are part of template structure)
- **D-11:** If RESTRICT is used, deletion MUST fail when dependencies exist

### Transaction Boundaries

- **D-12:** All create/update/delete operations MUST occur within a single database transaction
- **D-13:** Transaction MUST rollback on any validation failure
- **D-14:** Test database operations MUST use isolated transactions

### Block Relationship

- **D-15:** ScheduleTemplateBlock records MUST reference valid ScheduleTemplate via `template_id`
- **D-16:** Template deletion MUST handle dependent blocks according to schema constraints (CASCADE or require manual cleanup)

---

## Tests

Planned tests:

- `tests/contracts/test_schedule_template_add_contract.py::test_template_add__success_human_output`
- `tests/contracts/test_schedule_template_add_contract.py::test_template_add__success_json_output`
- `tests/contracts/test_schedule_template_add_contract.py::test_template_add__duplicate_name_fails`
- `tests/contracts/test_schedule_template_add_contract.py::test_template_add__empty_name_fails`
- `tests/contracts/test_schedule_template_add_contract.py::test_template_add__name_too_long_fails`
- `tests/contracts/test_schedule_template_add_contract.py::test_template_add__inactive_flag`
- `tests/contracts/test_schedule_template_update_contract.py::test_template_update__success`
- `tests/contracts/test_schedule_template_update_contract.py::test_template_update__duplicate_name_fails`
- `tests/contracts/test_schedule_template_update_contract.py::test_template_update__archive_template`
- `tests/contracts/test_schedule_template_update_contract.py::test_template_update__reactivate_template`
- `tests/contracts/test_schedule_template_delete_contract.py::test_template_delete__success_with_confirmation`
- `tests/contracts/test_schedule_template_delete_contract.py::test_template_delete__with_yes_flag`
- `tests/contracts/test_schedule_template_delete_contract.py::test_template_delete__with_blocks_fails`
- `tests/contracts/test_schedule_template_delete_contract.py::test_template_delete__with_plans_fails`
- `tests/contracts/test_schedule_template_delete_contract.py::test_template_delete__with_schedule_days_fails`
- `tests/contracts/test_schedule_template_list_contract.py::test_template_list__all_templates`
- `tests/contracts/test_schedule_template_list_contract.py::test_template_list__active_only`
- `tests/contracts/test_schedule_template_show_contract.py::test_template_show__by_id`
- `tests/contracts/test_schedule_template_show_contract.py::test_template_show__by_name`
- `tests/contracts/test_schedule_template_show_contract.py::test_template_show__with_blocks`

---

## Error Conditions

### Name Validation Errors

- Duplicate name: exit 1, "Error: Template name already exists."
- Empty name: exit 1, "Error: Template name cannot be empty."
- Name too long: exit 1, "Error: Template name exceeds maximum length (255 characters)."

### Referential Integrity Errors

- Template with blocks: exit 1, "Error: Cannot delete template with blocks. Remove all blocks first."
- Template with plans: exit 1, "Error: Cannot delete template with active plans. Archive template or remove plans first."
- Template with schedule days: exit 1, "Error: Cannot delete template with schedule days. Archive template first."

### Active Status Errors

- Inactive template for plan: exit 1, "Error: Template is not active. Activate template before creating a plan."
- Template with no blocks for plan: exit 1, "Error: Template has no blocks. Add at least one block before creating a plan."

### Update Errors

- No fields provided: exit 1, "Error: At least one field (--name, --description, or --active/--inactive) must be provided."

---

## Template Reuse Examples

### Example 1: Multiple Plans, Same Template

```
Template: "General Programming"
  - Used by: WeekdayPlan (Channel A)
  - Used by: WeekendPlan (Channel A)
  - Used by: WeekdayPlan (Channel B)
```

**Result:** Template is reused across multiple plans and channels. Changes to template affect all plans.

### Example 2: Archive Template

```
Template: "Holiday Programming"
  - is_active: false (archived)
  - Used by: ChristmasPlan (existing, still valid)
  - NOT eligible for: New plan creation
```

**Result:** Archived template cannot be used in new plans, but existing schedule days remain valid.

---

## See also

- [Domain: ScheduleTemplate](../../domain/ScheduleTemplate.md) - Complete domain documentation
- [Domain: ScheduleTemplateBlock](../../domain/ScheduleTemplateBlock.md) - Block entity
- [ScheduleTemplateBlockContract](ScheduleTemplateBlockContract.md) - Block operations contract
- [SchedulePlanInvariantsContract](SchedulePlanInvariantsContract.md) - Cross-entity invariants
- [CLI Data Guarantees](cross-domain/CLI_Data_Guarantees.md) - General CLI guarantees

