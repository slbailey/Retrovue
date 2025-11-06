# Pattern Add Contract

_Related: [PatternContract](PatternContract.md) • [Domain: Pattern](../../domain/Pattern.md) • [Domain: SchedulePlan](../../domain/SchedulePlan.md) • [Domain: Program](../../domain/Program.md)_

## Purpose

This contract defines the behavior of the `retrovue channel plan <channel> <plan> pattern add` command, which creates a new Pattern within a SchedulePlan. Patterns are ordered lists of Program references that define content sequences.

## Command Syntax

```bash
retrovue channel plan <channel> <plan> pattern add \
  [--name <string>] \
  [--description <string>] \
  [--json] [--test-db]
```

## Required Arguments

- `<channel>` - Channel identifier (UUID or slug)
- `<plan>` - SchedulePlan identifier (UUID or name)

## Optional Options

- `--name <string>` - Human-readable Pattern name (must be unique within the SchedulePlan if provided)
- `--description <string>` - Human-readable description of the Pattern's programming intent
- `--json` - Output in JSON format
- `--test-db` - Use test database context

## Behavior Contract Rules (B-#)

### B-1: Channel and Plan Resolution

**Rule:** The command MUST resolve the channel and plan by their identifiers before creating the Pattern.

**Behavior:**
- If channel is not found → exit 1, error message: "Error: Channel '<identifier>' not found"
- If plan is not found → exit 1, error message: "Error: Plan '<identifier>' not found"
- If plan does not belong to channel → exit 1, error message: "Error: Plan '<plan>' does not belong to channel '<channel>'"

### B-2: Name Uniqueness

**Rule:** Pattern name MUST be unique within the SchedulePlan if provided.

**Behavior:**
- If name conflicts with existing Pattern in same plan → exit 1, error message: "Error: Pattern name '<name>' already exists in plan '<plan>'"
- Patterns in different plans can have the same name
- Null names are allowed (multiple Patterns can have null names)
- Name validation occurs at creation time

### B-3: Optional Fields

**Rule:** Both name and description are optional fields.

**Behavior:**
- Pattern can be created with no name (`name=null`) → Valid
- Pattern can be created with no description (`description=null`) → Valid
- Pattern can be created with both name and description → Valid
- Pattern can be created with only name or only description → Valid

## Data Contract Rules (D-#)

### D-1: Pattern Persistence

**Rule:** Pattern MUST be persisted in `patterns` table with all provided fields.

**Behavior:**
- Record created with all required fields: `id`, `plan_id`
- Optional fields persisted if provided: `name`, `description`
- Defaults applied: `name=null`, `description=null` if not specified
- Timestamps: `created_at`, `updated_at` set automatically

### D-2: Plan Reference Integrity

**Rule:** Pattern `plan_id` MUST reference the resolved SchedulePlan.

**Behavior:**
- Foreign key constraint enforced
- Plan must exist in database
- Plan must belong to resolved channel

### D-3: Name Uniqueness Enforcement

**Rule:** Pattern name uniqueness MUST be enforced at database or application layer if name is provided.

**Behavior:**
- Unique constraint on (`plan_id`, `name`) where `name IS NOT NULL` or application-level validation
- Violation fails creation with clear error
- Null names are allowed (no uniqueness constraint on null)

### D-4: Timestamp Storage

**Rule:** Timestamps MUST be stored in UTC with timezone awareness.

**Behavior:**
- `created_at` set to current UTC time
- `updated_at` set to current UTC time
- Timezone-aware DateTime fields

### D-5: Transaction Boundaries

**Rule:** Pattern creation MUST be atomic within a transaction.

**Behavior:**
- All validation occurs before any database writes
- On failure, no partial state persisted
- Rollback on any validation or persistence error

## Success Behavior

On successful creation:

**Exit Code:** 0

**Output (non-JSON):**
```
Pattern created:
  ID: <pattern-id>
  Plan: <plan-name>
  Name: <pattern-name-or-unnamed>
  Description: <description-or-none>
  Programs: 0
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

### Example 1: Create Pattern with Name

```bash
retrovue channel plan channel-1 weekday-plan pattern add \
  --name "Prime Time Pattern"
```

**Expected:** Pattern created with name "Prime Time Pattern".

### Example 2: Create Pattern with Name and Description

```bash
retrovue channel plan channel-1 weekday-plan pattern add \
  --name "Prime Time Pattern" \
  --description "Evening drama and movies"
```

**Expected:** Pattern created with name and description.

### Example 3: Create Unnamed Pattern

```bash
retrovue channel plan channel-1 weekday-plan pattern add
```

**Expected:** Pattern created with no name (null).

### Example 4: Invalid - Name Conflict

```bash
retrovue channel plan channel-1 weekday-plan pattern add \
  --name "Prime Time Pattern"
# First creation succeeds
retrovue channel plan channel-1 weekday-plan pattern add \
  --name "Prime Time Pattern"
```

**Expected:** Second command exits 1, error: "Error: Pattern name 'Prime Time Pattern' already exists in plan 'weekday-plan'"

## Test Coverage Requirements

Tests MUST verify:

1. Successful Pattern creation with all field combinations (name, description, both, neither)
2. Channel and plan resolution (valid and invalid cases)
3. Name uniqueness within plan
4. Null name handling (multiple Patterns with null names allowed)
5. JSON output format
6. Error message clarity
7. Domain-level validation occurs at creation time

## Related Contracts

- [PatternContract](PatternContract.md) - Pattern domain validation contracts
- [PatternUpdateContract](PatternUpdateContract.md) - Pattern update operations
- [PatternListContract](PatternListContract.md) - Pattern listing operations
- [PatternShowContract](PatternShowContract.md) - Pattern display operations
- [PatternDeleteContract](PatternDeleteContract.md) - Pattern deletion operations
- [SchedulePlanInvariantsContract](SchedulePlanInvariantsContract.md) - Plan-level invariants

## See Also

- [Domain: Pattern](../../domain/Pattern.md) - Complete Pattern domain documentation
- [Domain: SchedulePlan](../../domain/SchedulePlan.md) - SchedulePlan domain documentation


