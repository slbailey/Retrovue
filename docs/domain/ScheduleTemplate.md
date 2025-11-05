_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md) • [Contracts](../contracts/README.md) • [Channel](Channel.md) • [ScheduleDay](ScheduleDay.md) • [ScheduleTemplateBlock](ScheduleTemplateBlock.md)_

# Domain — ScheduleTemplate

## Purpose

ScheduleTemplate represents a reusable, channel-agnostic shell that defines what *types of content* should appear in a day. Think of this like a layout or blueprint — it includes one or more ScheduleTemplateBlocks that define constraints (e.g., "cartoons only" or "family-friendly content") but does NOT define actual content selections. Templates provide the structure that SchedulePlans fill with actual content choices made by operators.

## Persistence model

ScheduleTemplate is managed by SQLAlchemy with the following fields:

- **id** (UUID, primary key): Unique identifier for relational joins and foreign key references
- **name** (Text, required, unique): Template identifier (e.g., "All Sitcoms 24x7", "Morning News Block")
- **description** (Text, optional): Human-readable description of the template's programming intent
- **is_active** (Boolean, required): Template operational status; only active templates are eligible for assignment
- **created_at** (DateTime(timezone=True), required): Record creation timestamp
- **updated_at** (DateTime(timezone=True), required): Record last modification timestamp

ScheduleTemplate has relationships with:

- **ScheduleTemplateBlockInstance**: Junction table linking templates to standalone blocks with template-specific timing. Multiple instances can exist within a single template to define complex programming patterns (guardrails/constraints)
- **ScheduleTemplateBlock**: Many-to-many relationship via ScheduleTemplateBlockInstance. Blocks are standalone and reusable across multiple templates
- **SchedulePlan**: Plans created by operators that fill templates with actual content selections
- **BroadcastScheduleDay**: Resolved schedules for specific channel and date (generated from plans using templates)

### Table name

The table is named `schedule_templates` (plural). Schema migration is handled through Alembic. Postgres is the authoritative backing store.

### Constraints

- `name` must be unique across all templates
- `name` max length ≤ 255 characters (enforced at database level)
- `description` max length is database-dependent (typically unlimited for TEXT)

### Naming rules

- `name` is a human-readable identifier; it should be descriptive and reflect the template's programming intent
- `name` uniqueness is enforced at the database level

## Contract / interface

ScheduleTemplate provides the programming structure (shell/blueprint) for schedule generation. It defines:

- Template identity and metadata (name, description)
- Template operational status (is_active)
- Relationship to time blocks (ScheduleTemplateBlock) - these define constraints, not content
- Relationship to plans (SchedulePlan) - these fill templates with actual content
- Relationship to resolved schedules (BroadcastScheduleDay)

**Critical Distinction:** Templates define *what types of content* should appear, not *what specific content* appears. Actual content selections are made in SchedulePlans, which operators create to fill templates.

Templates are channel-agnostic by design. Channel-specific programming is achieved by:

- Creating plans that fill templates with content appropriate for the channel
- Using rule_json in ScheduleTemplateBlock to filter content types (guardrails)
- Relying on Channel configuration (grid_block_minutes, programming_day_start) for timing context

## Execution model

ScheduleService consumes ScheduleTemplate records through SchedulePlan and BroadcastScheduleDay to determine which template structure to use. When generating schedules, ScheduleService:

1. Identifies the active plan for a channel and date (which references a template)
2. Retrieves all ScheduleTemplateBlock records for that template (these define constraints)
3. Retrieves SchedulePlanBlockAssignment records for the plan (these define actual content selections)
4. Validates that assignments respect template block rules (rule_json)
5. Resolves the plan into a BroadcastScheduleDay for the specific channel and date
6. Generates BroadcastPlaylogEvent entries for the scheduled content

Templates provide the "what programming pattern to use" structure (constraints/guardrails), while plans provide the "what specific content to use" selections. Template blocks define constraints; plan assignments define content.

## Failure / fallback behavior

If templates are missing or invalid:

- The system falls back to default programming or the most recent valid template assignment
- ScheduleService skips templates where `is_active=false`
- Missing BroadcastScheduleDay assignments result in no schedule generation for that channel/date combination

## Scheduling model

- Templates are reusable, channel-agnostic shells that define content type constraints
- Templates define structure; plans fill that structure with actual content
- Multiple plans can reference the same template (e.g., "WeekdayPlan" and "WeekendPlan" both use "GeneralTemplate")
- Template blocks define time periods and content type constraints (guardrails) within each template
- Content type constraints (rule_json) in template blocks define what *types* of content are allowed (e.g., "cartoons only")
- Actual content selections are made in SchedulePlans via SchedulePlanBlockAssignment
- Templates can be activated/deactivated via `is_active` flag without deletion

## Lifecycle and referential integrity

- `is_active=false` archives the template: ScheduleService excludes the template from new schedule generation. Existing BroadcastScheduleDay assignments remain but are ignored during schedule generation.
- Hard delete is only permitted when no dependent rows exist (e.g., ScheduleTemplateBlock, BroadcastScheduleDay). When dependencies exist, prefer archival (`is_active=false`). The delete path MUST verify the absence of these references.
- The dependency preflight MUST cover: ScheduleTemplateBlock, BroadcastScheduleDay, and any EPG/playlog references that depend on the template.

## Operator workflows

**Create Template**: Define a new reusable programming template (shell/blueprint) with a descriptive name and optional description. This defines the *structure* and *constraints*, not specific content.

**Manage Template Block Instances**: Add, modify, or remove ScheduleTemplateBlockInstance records to link standalone blocks to the template with template-specific timing. Blocks define what *types* of content are allowed, not what specific content appears. The same block can be used in multiple templates with different timing.

**Create Plans**: Operators create SchedulePlans that fill templates with actual content selections. Plans reference templates and provide specific content choices.

**Activate/Deactivate Template**: Toggle `is_active` to enable or disable template availability for new plan creation.

**Template Reuse**: Apply the same template to multiple plans (e.g., "WeekdayPlan" and "WeekendPlan" can both use "GeneralTemplate") to ensure consistent programming structure.

**Template Maintenance**: Update description, modify blocks, or archive templates as programming needs evolve. Note that template changes affect all plans that reference the template.

### CLI command examples

**Create Template**: Use `retrovue schedule-template add` (or `retrovue template add`) with required parameters:

```bash
retrovue schedule-template add --name "All Sitcoms 24x7" \
  --description "24-hour sitcom programming template (defines structure/constraints)"
```

**List Templates**: Use `retrovue schedule-template list` to see all templates in table format, or `retrovue schedule-template list --json` for machine-readable output.

**Show Template**: Use `retrovue schedule-template show --template <name-or-uuid>` to see detailed template information including associated blocks and plans that reference it. The `--template` parameter accepts either a template name or UUID.

**Add Block to Template**: After creating standalone blocks, link them to templates with timing:

```bash
retrovue schedule-template block add --template <name-or-uuid> --block <block-name-or-uuid> --start-time 06:00 --end-time 09:00
```

Both `--template` and `--block` parameters accept either a name or UUID, making commands easier to use.

**Broadcast Day Time Format**: Times support `HH:MM` or `HH:MM+1` format where `+1` indicates the next calendar day. Broadcast days run from 06:00 to 06:00+1 (next day), so blocks can span midnight:
- Valid: `22:00` to `04:00` (spans midnight, same broadcast day)
- Invalid: `22:00` to `08:00` (crosses broadcast day boundary at 06:00)
- Valid: `06:00` to `06:00+1` (full broadcast day)
- Valid: `22:00` to `02:00+1` (spans midnight, ends before 06:00 next day)

**Create Plan**: After creating a template with blocks, create a plan that fills it with content:

```bash
retrovue schedule-plan add --name "WeekdayPlan" --template <name-or-uuid> --cron "0 6 * * MON-FRI"
```

**Activate/Deactivate**: Use `retrovue schedule-template update --template <name-or-uuid> --active` or `--inactive` to toggle is_active status.

**Update Template**: Use `retrovue schedule-template update --template <name-or-uuid>` with any combination of fields to modify template properties.

**Delete Template**: Use `retrovue schedule-template delete --template <name-or-uuid>` to permanently remove a template (only if no dependencies exist, including plans).

All operations accept either name or UUID for template identification (name lookups are case-insensitive). The CLI provides both human-readable and JSON output formats.

## Validation & invariants

- **Name uniqueness**: `name` must be unique across all templates (enforced at database level)
- **Active status**: Only templates where `is_active=true` are eligible for use in new SchedulePlans
- **Block coverage**: Templates should have ScheduleTemplateBlockInstance records that cover the full 24-hour programming day (00:00 to 24:00), though this is not enforced at the template level
- **Block instance non-overlap**: Block instances within a template must not overlap (enforced by validation or database constraints)
- **Referential integrity**: Templates cannot be deleted if they have dependent ScheduleTemplateBlockInstance, SchedulePlan, or BroadcastScheduleDay records

## Out of scope (v0.1)

- Template versioning and effective-dated changes
- Template inheritance or composition
- Template-level content selection rules (rules are defined at the block level)
- Program selection heuristics beyond rule_json matching
- Ad pod composition and overlay timing
- Template validation against Channel grid configuration (this validation may occur during BroadcastScheduleDay assignment)

## See also

- [Scheduling](Scheduling.md) - High-level scheduling system
- [SchedulePlan](SchedulePlan.md) - Operator-created plans that fill templates with actual content
- [ScheduleDay](ScheduleDay.md) - Resolved schedules for specific channel and date
- [ScheduleTemplateBlock](ScheduleTemplateBlock.md) - Standalone, reusable blocks with content type constraints
- [Channel](Channel.md) - Channel configuration and timing policy
- [Asset](Asset.md) - Approved content available for scheduling
- [PlaylogEvent](PlaylogEvent.md) - Generated playout events
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
