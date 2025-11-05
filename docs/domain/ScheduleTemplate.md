_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md) • [Contracts](../contracts/README.md) • [Channel](Channel.md) • [ScheduleDay](ScheduleDay.md) • [ScheduleTemplateBlock](ScheduleTemplateBlock.md)_

# Domain — ScheduleTemplate

## Purpose

ScheduleTemplate represents a reusable programming template that defines daypart rules and content selection criteria. Templates are channel-agnostic scheduling patterns that can be assigned to any channel for specific broadcast dates via BroadcastScheduleDay. This is planning-time logic that defines the programming structure used by ScheduleService to generate playout schedules.

## Persistence model

ScheduleTemplate is managed by SQLAlchemy with the following fields:

- **id** (UUID, primary key): Unique identifier for relational joins and foreign key references
- **name** (Text, required, unique): Template identifier (e.g., "All Sitcoms 24x7", "Morning News Block")
- **description** (Text, optional): Human-readable description of the template's programming intent
- **is_active** (Boolean, required): Template operational status; only active templates are eligible for assignment
- **created_at** (DateTime(timezone=True), required): Record creation timestamp
- **updated_at** (DateTime(timezone=True), required): Record last modification timestamp

ScheduleTemplate has one-to-many relationships with:

- **ScheduleTemplateBlock**: Multiple blocks can exist within a single template to define complex programming patterns
- **BroadcastScheduleDay**: Templates are assigned to channels for specific broadcast dates through schedule assignments

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

ScheduleTemplate provides the programming structure for schedule generation. It defines:

- Template identity and metadata (name, description)
- Template operational status (is_active)
- Relationship to time blocks (ScheduleTemplateBlock)
- Relationship to channel assignments (BroadcastScheduleDay)

Templates are channel-agnostic by design. Channel-specific programming is achieved by:

- Assigning templates to channels via BroadcastScheduleDay
- Using rule_json in ScheduleTemplateBlock to filter content appropriate for the channel
- Relying on Channel configuration (grid_block_minutes, programming_day_start) for timing context

## Execution model

ScheduleService consumes ScheduleTemplate records through BroadcastScheduleDay assignments to determine which template to use for a given channel and date. When generating schedules, ScheduleService:

1. Identifies the active template for a channel and date via BroadcastScheduleDay
2. Retrieves all ScheduleTemplateBlock records for that template
3. Determines which blocks apply to specific time periods based on start_time and end_time
4. Applies each block's rule_json to select appropriate content from Asset
5. Generates BroadcastPlaylogEvent entries for the selected content

Templates provide the "what programming pattern to use" logic, while template blocks provide the "how to select content" logic that drives automated scheduling decisions.

## Failure / fallback behavior

If templates are missing or invalid:

- The system falls back to default programming or the most recent valid template assignment
- ScheduleService skips templates where `is_active=false`
- Missing BroadcastScheduleDay assignments result in no schedule generation for that channel/date combination

## Scheduling model

- Templates are reusable across multiple channels via BroadcastScheduleDay assignments
- Exactly one template can be assigned to a channel for a specific broadcast date (enforced by unique constraint on BroadcastScheduleDay)
- Template blocks define time periods and content selection rules within each template
- Content selection rules (rule_json) in template blocks query Asset records where `state='ready'` and `approved_for_broadcast=true`
- Templates can be activated/deactivated via `is_active` flag without deletion

## Lifecycle and referential integrity

- `is_active=false` archives the template: ScheduleService excludes the template from new schedule generation. Existing BroadcastScheduleDay assignments remain but are ignored during schedule generation.
- Hard delete is only permitted when no dependent rows exist (e.g., ScheduleTemplateBlock, BroadcastScheduleDay). When dependencies exist, prefer archival (`is_active=false`). The delete path MUST verify the absence of these references.
- The dependency preflight MUST cover: ScheduleTemplateBlock, BroadcastScheduleDay, and any EPG/playlog references that depend on the template.

## Operator workflows

**Create Template**: Define a new reusable programming template with a descriptive name and optional description.

**Manage Template Blocks**: Add, modify, or remove ScheduleTemplateBlock records to define time periods and content selection rules within the template.

**Assign Template to Channel**: Use BroadcastScheduleDay to link a template to a channel for specific broadcast dates.

**Activate/Deactivate Template**: Toggle `is_active` to enable or disable template availability for new schedule assignments.

**Template Reuse**: Apply the same template to multiple channels or dates to ensure consistent programming patterns.

**Template Maintenance**: Update description, modify blocks, or archive templates as programming needs evolve.

### CLI command examples

**Create Template**: Use `retrovue schedule-template add` (or `retrovue template add`) with required parameters:

```bash
retrovue schedule-template add --name "All Sitcoms 24x7" \
  --description "24-hour sitcom programming block"
```

**List Templates**: Use `retrovue schedule-template list` to see all templates in table format, or `retrovue schedule-template list --json` for machine-readable output.

**Show Template**: Use `retrovue schedule-template show --id <uuid>` or `retrovue schedule-template show --name <name>` to see detailed template information including associated blocks.

**Activate/Deactivate**: Use `retrovue schedule-template update --id <uuid> --active` or `--inactive` to toggle is_active status.

**Update Template**: Use `retrovue schedule-template update --id <uuid>` with any combination of fields to modify template properties.

**Delete Template**: Use `retrovue schedule-template delete --id <uuid>` to permanently remove a template (only if no dependencies exist).

All operations use UUID identifiers for template identification. The CLI provides both human-readable and JSON output formats.

## Validation & invariants

- **Name uniqueness**: `name` must be unique across all templates (enforced at database level)
- **Active status**: Only templates where `is_active=true` are eligible for assignment via BroadcastScheduleDay
- **Block coverage**: Templates should have ScheduleTemplateBlock records that cover the full 24-hour programming day (00:00 to 24:00), though this is not enforced at the template level
- **Referential integrity**: Templates cannot be deleted if they have dependent ScheduleTemplateBlock or BroadcastScheduleDay records

## Out of scope (v0.1)

- Template versioning and effective-dated changes
- Template inheritance or composition
- Template-level content selection rules (rules are defined at the block level)
- Program selection heuristics beyond rule_json matching
- Ad pod composition and overlay timing
- Template validation against Channel grid configuration (this validation may occur during BroadcastScheduleDay assignment)

## See also

- [Scheduling](Scheduling.md) - High-level scheduling system
- [ScheduleDay](ScheduleDay.md) - Template assignments to channels for specific dates
- [ScheduleTemplateBlock](ScheduleTemplateBlock.md) - Time blocks within templates with content selection rules
- [Channel](Channel.md) - Channel configuration and timing policy
- [Asset](Asset.md) - Approved content available for scheduling
- [PlaylogEvent](PlaylogEvent.md) - Generated playout events
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
