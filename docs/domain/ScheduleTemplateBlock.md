_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md) • [ScheduleTemplate](ScheduleTemplate.md)_

# Domain — Schedule template block

## Purpose

ScheduleTemplateBlock represents a standalone, reusable block definition that specifies content type constraints (guardrails) such as "cartoons only" or "family-friendly content". These blocks define *constraints* and *rules*, not actual content selections or time windows. Think of them as reusable constraint libraries that can be instantiated in multiple templates with different timing.

**Key Concept:** Template blocks are standalone entities that can be reused across multiple templates. When a template uses a block, it creates a `ScheduleTemplateBlockInstance` that links the block to the template with template-specific timing (start_time, end_time).

## Persistence model

ScheduleTemplateBlock is managed by SQLAlchemy with the following fields:

- **id** (UUID, primary key): Unique identifier for relational joins and foreign key references
- **name** (Text, required, unique): Block identifier (e.g., "Morning Cartoons", "Family-Friendly Sitcoms")
- **rule_json** (Text, required): JSON configuration defining content type constraints (guardrails) - e.g., "cartoons only", "family-friendly", "PG-13 max"
- **created_at** (DateTime(timezone=True), required): Record creation timestamp
- **updated_at** (DateTime(timezone=True), required): Record last modification timestamp

ScheduleTemplateBlock has a many-to-many relationship with ScheduleTemplate via the `ScheduleTemplateBlockInstance` junction table. A single block can be used in multiple templates, each with different timing.

**Note:** Blocks do NOT contain `start_time` or `end_time` - these are template-specific and stored in `ScheduleTemplateBlockInstance`.

### Table name

The table is named `schedule_template_blocks` (plural). Schema migration is handled through Alembic. Postgres is the authoritative backing store.

### Constraints

- `name` must be unique across all blocks
- `name` max length ≤ 255 characters (enforced at database level)
- `rule_json` must be valid JSON
- **Block reusability**: Blocks can be used in multiple templates via `ScheduleTemplateBlockInstance`
- **Non-overlap requirement**: Block instances within a template MUST NOT have overlapping time periods. This is enforced at the instance level, not the block level.
- **Block boundaries**: Blocks define content type constraints only; time windows are specified when blocks are instantiated in templates

## Contract / interface

ScheduleTemplateBlock provides reusable content type constraints (guardrails). It defines:

- Block identity (name) - human-readable identifier for the constraint set
- Content type constraints (rule_json) - what *types* of content are allowed, not what specific content appears
- Relationship to templates via instances (ScheduleTemplateBlockInstance) - many-to-many with template-specific timing

**Critical Distinctions:**
- Template blocks define *constraints* (what types of content may appear), not *content* (what specific content appears)
- Template blocks do NOT define time windows - timing is specified when blocks are instantiated in templates
- Blocks are reusable across multiple templates - the same block can be used with different timing in different templates
- Actual content selections are made in SchedulePlanBlockAssignment, which must respect block constraints

Template blocks provide the "what types of content are allowed" guardrails that SchedulePlanBlockAssignment must follow when operators select actual content.

## Execution model

ScheduleService consumes ScheduleTemplateBlock records (via ScheduleTemplateBlockInstance) to determine content type constraints for specific time periods. When generating schedules, ScheduleService:

1. Identifies the active plan for a channel and date (which references a template)
2. Retrieves all template block instances for that template (these link blocks to templates with timing)
3. For each instance, retrieves the associated ScheduleTemplateBlock (these define constraints via rule_json)
4. Retrieves plan block assignments for the plan (these define actual content selections)
5. Validates that assignments respect template block constraints (rule_json) for the appropriate time periods
6. Determines which template block instance applies to each time period
7. Ensures plan assignments follow the block's constraints
8. Generates BroadcastPlaylogEvent entries for the validated content

Template blocks provide guardrails; block instances provide timing; plan assignments provide actual content. The system validates that assignments comply with block constraints for the appropriate time windows.

## Failure / fallback behavior

If template blocks are missing or invalid, the system falls back to default programming or the most recent valid block configuration.

## Naming rules

The canonical name for this concept in code and documentation is ScheduleTemplateBlock.

Template blocks are constraint definitions, not runtime components. They define "what types of content are allowed" (guardrails) but do not select or execute content. Actual content selection happens in SchedulePlanBlockAssignment.

## Out of scope (v0.1)

- Block overlap detection and resolution (blocks MUST NOT overlap - this is a critical invariant)
- Block priority/ordering rules beyond time-based selection
- Dynamic block modification during schedule generation
- Block-level content substitution and override rules (content is defined in plan assignments, not blocks)

## Operator workflows

**Create Standalone Block**: Define a reusable block with a name and content type constraints (rule_json). Blocks are standalone and can be used in multiple templates.

```bash
# Create a standalone block
retrovue template-block add --name "Morning Cartoons" \
  --rule-json '{"tags": ["cartoon"], "rating_max": "TV-Y7", "duration_max_minutes": 30}'
```

**Instantiate Block in Template**: Add a block to a template by creating a ScheduleTemplateBlockInstance that links the block to the template with template-specific timing (start_time, end_time).

```bash
# Add a block instance to a template (using names for easier operation)
retrovue schedule-template block add \
  --template "Demo Template" \
  --block "Morning Cartoons" \
  --start-time 06:00 \
  --end-time 09:00

# Blocks can span midnight within the same broadcast day
retrovue schedule-template block add \
  --template "Demo Template" \
  --block "Late Night" \
  --start-time 22:00 \
  --end-time 04:00

# Use +1 notation for next calendar day
retrovue schedule-template block add \
  --template "Demo Template" \
  --block "Full Day" \
  --start-time 06:00 \
  --end-time 06:00+1
```

Both `--template` and `--block` parameters accept either name or UUID (case-insensitive name lookup).

**Broadcast Day Time Format**: Times use `HH:MM` or `HH:MM+1` format where `+1` indicates the next calendar day. Broadcast days run from 06:00 to 06:00+1 (next day), allowing blocks to span midnight:
- Valid: `22:00` to `04:00` (spans midnight, same broadcast day)
- Invalid: `22:00` to `08:00` (crosses broadcast day boundary at 06:00)
- Valid: `06:00` to `06:00+1` (full broadcast day)
- Valid: `22:00` to `02:00+1` (explicitly spans midnight, ends before 06:00 next day)

**Configure Content Constraints**: Set up rule_json to define content type constraints (e.g., "cartoons only", "family-friendly", "PG-13 max"). These are guardrails that plan assignments must respect.

**Manage Block Timing**: Adjust start_time and end_time in block instances to modify programming periods within templates. Ensure instances do not overlap within the same template.

**Reuse Blocks Across Templates**: Use the same block in multiple templates with different timing. For example, "Morning Cartoons" block can be used from 06:00-09:00 in one template and 07:00-10:00 in another.

**Validate Block Constraints**: Verify that blocks correctly define constraints and that plan assignments respect those constraints.

**Template Block Maintenance**: Update block constraints (rule_json) or block name. Note that block changes affect all templates that use the block. To change timing, update the block instance, not the block itself.

```bash
# Update a standalone block (using name or UUID)
retrovue template-block update --block "Morning Cartoons" \
  --rule-json '{"tags": ["cartoon"], "rating_max": "TV-Y", "duration_max_minutes": 30}'

# Update block instance timing (must use instance UUID)
retrovue schedule-template block update --id <instance-uuid> \
  --start-time 07:00 \
  --end-time 10:00
```

**Fill Blocks with Content**: After creating template block instances, operators create SchedulePlanBlockAssignment records to fill blocks with actual content selections that respect the block constraints.

### CLI command examples

**Create Standalone Block**: Use `retrovue template-block add` with required parameters:
```bash
retrovue template-block add --name "Sitcoms" \
  --rule-json '{"duration_max_minutes": 30, "tags": ["sitcom"]}'
```

**List Standalone Blocks**: Use `retrovue template-block list` to see all blocks:
```bash
retrovue template-block list
retrovue template-block list --json
```

**Show Standalone Block**: Use `retrovue template-block show --block <name-or-uuid>`:
```bash
retrovue template-block show --block "Morning Cartoons"
retrovue template-block show --block <uuid>
```

**Update Standalone Block**: Use `retrovue template-block update --block <name-or-uuid>`:
```bash
retrovue template-block update --block "Morning Cartoons" --name "Early Morning Cartoons"
```

**Delete Standalone Block**: Use `retrovue template-block delete --block <name-or-uuid>`:
```bash
retrovue template-block delete --block "Morning Cartoons" --yes
```

All operations accept either name or UUID for block identification (name lookups are case-insensitive).

## See also

- [Scheduling](Scheduling.md) - High-level scheduling system
- [ScheduleTemplate](ScheduleTemplate.md) - Reusable programming templates (structure)
- [SchedulePlan](SchedulePlan.md) - Operator-created plans that fill templates with actual content
- [ScheduleDay](ScheduleDay.md) - Resolved schedules for specific channel and date
- [Asset](Asset.md) - Approved content
- [PlaylogEvent](PlaylogEvent.md) - Generated playout events
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
