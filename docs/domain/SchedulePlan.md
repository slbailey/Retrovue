_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md) • [Contracts](../contracts/README.md) • [ScheduleTemplate](ScheduleTemplate.md) • [ScheduleTemplateBlock](ScheduleTemplateBlock.md) • [ScheduleDay](ScheduleDay.md)_

# Domain — SchedulePlan

## Purpose

SchedulePlan represents an operator-created plan that fills a ScheduleTemplate with actual content selections. Unlike templates (which define what *types* of content should appear), plans define *specific* content choices made by an operator. SchedulePlans can be layered with priority based on specificity (e.g., day-of-week, date range, or holiday-specific plan) and overridden by more specific layers.

**Key Distinction:** ScheduleTemplate defines the *structure* (what types of content go where), while SchedulePlan fills that structure with *actual selections* (specific series, episodes, or rules for content selection).

## Core Model / Scope

SchedulePlan is a reusable, timeless planning construct that:

- **Fills templates with content**: Operators select series (or rules like "random family movie under 2 hours") to populate template blocks
- **Supports layering**: Plans can be layered via cron-style windows with priority based on specificity
- **Enables overrides**: More specific plans (e.g., "ChristmasPlan") take precedence over general plans (e.g., "WeekdayPlan")
- **Is timeless**: Plans are valid from start to end dates every year (cron-like), not tied to specific calendar dates

## Persistence Model

SchedulePlan is managed by SQLAlchemy with the following fields:

- **id** (UUID, primary key): Unique identifier for relational joins and foreign key references
- **name** (Text, required, unique): Plan identifier (e.g., "WeekdayPlan", "ChristmasPlan", "SummerBlock")
- **description** (Text, optional): Human-readable description of the plan's programming intent
- **template_id** (UUID, required, foreign key): Reference to the ScheduleTemplate this plan fills
- **cron_expression** (Text, optional): Cron-style expression defining when this plan is active (e.g., "0 6 * * MON-FRI" for weekdays 6am)
- **start_date** (Date, optional): Start date for plan validity (inclusive, can be year-agnostic)
- **end_date** (Date, optional): End date for plan validity (inclusive, can be year-agnostic)
- **priority** (Integer, required, default: 0): Priority for layering; higher priority plans override lower priority plans
- **is_active** (Boolean, required, default: true): Plan operational status; only active plans are eligible for use
- **created_at** (DateTime(timezone=True), required): Record creation timestamp
- **updated_at** (DateTime(timezone=True), required): Record last modification timestamp

SchedulePlan has one-to-many relationships with:

- **SchedulePlanBlockAssignment**: Multiple block assignments can exist within a single plan to define specific content for each template block
- **BroadcastScheduleDay**: Plans are used to generate resolved schedule days (though the relationship may be indirect)

### Table Name

The table is named `schedule_plans` (plural). Schema migration is handled through Alembic. Postgres is the authoritative backing store.

### Constraints

- `name` must be unique across all plans
- `name` max length ≤ 255 characters (enforced at database level)
- `description` max length is database-dependent (typically unlimited for TEXT)
- `template_id` must reference a valid ScheduleTemplate
- `priority` must be non-negative (default: 0)
- `start_date` and `end_date` must be valid dates if provided
- `cron_expression` must be valid cron syntax if provided

### Layering and Priority Rules

- Plans with higher `priority` values override plans with lower `priority` values when both are active
- When multiple plans match (via cron_expression or date range), the highest priority plan is used
- More specific plans (e.g., holiday-specific, day-of-week specific) should have higher priority than general plans
- Superseded plans should be archived (`is_active=false`) or cloned rather than deleted

## Contract / Interface

SchedulePlan provides the content selection layer that fills templates with actual programming choices. It defines:

- Plan identity and metadata (name, description)
- Template relationship (which template this plan fills)
- Temporal validity (cron_expression, start_date, end_date)
- Priority for layering (priority)
- Operational status (is_active)
- Relationship to block assignments (SchedulePlanBlockAssignment)

Plans are timeless and reusable by design. They define "what content goes in which template blocks" for recurring patterns (e.g., weekdays, holidays, seasons).

## Execution Model

ScheduleService and schedule generation logic consume SchedulePlan records to determine actual content selections:

1. **Identify active plans**: For a given channel and date, determine which plans are active based on cron_expression, date ranges, and is_active status
2. **Resolve priority**: If multiple plans match, select the plan with the highest priority
3. **Apply block assignments**: For each template block, use the corresponding SchedulePlanBlockAssignment to determine what content should fill that block
4. **Generate BroadcastScheduleDay**: Resolve the plan into a concrete BroadcastScheduleDay for the specific channel and date
5. **Validate assignments**: Ensure all block assignments follow the rules from their corresponding ScheduleTemplateBlock

**Critical Rule:** Block assignments must respect the constraints defined in their parent ScheduleTemplateBlock's `rule_json`. For example, if a template block specifies "cartoons only", plan assignments for that block must select cartoon content.

## SchedulePlanBlockAssignment

SchedulePlanBlockAssignment represents a time slice within a template block in a specific SchedulePlan. It records the operator's content selection for a specific time period within a block.

### Persistence Model

SchedulePlanBlockAssignment is managed by SQLAlchemy with the following fields:

- **id** (UUID, primary key): Unique identifier for relational joins and foreign key references
- **plan_id** (UUID, required, foreign key): Reference to parent SchedulePlan
- **template_block_id** (UUID, required, foreign key): Reference to ScheduleTemplateBlock that this assignment fills
- **start_time_offset** (Integer, required): Offset in minutes from the template block's start_time (0 = block start)
- **end_time_offset** (Integer, required): Offset in minutes from the template block's start_time (must be > start_time_offset)
- **content_type** (Text, required): Type of content selection - one of: "series", "asset", "rule", "random"
- **content_reference** (Text, required): Reference to the content:
  - For "series": Series identifier or UUID
  - For "asset": Asset UUID
  - For "rule": Rule JSON (e.g., "random family movie under 2 hours")
  - For "random": Random selection rule JSON
- **episode_policy** (Text, optional): Episode selection policy (e.g., "sequential", "syndication", "random", "least-recently-used")
- **created_at** (DateTime(timezone=True), required): Record creation timestamp
- **updated_at** (DateTime(timezone=True), required): Record last modification timestamp

### Constraints

- `start_time_offset` must be ≥ 0
- `end_time_offset` must be > `start_time_offset`
- `template_block_id` must reference a valid ScheduleTemplateBlock
- `content_type` must be one of: "series", "asset", "rule", "random"
- Assignments must not overlap within the same plan and template block
- Assignments must respect the constraints defined in their parent ScheduleTemplateBlock's `rule_json`

### Content Selection Rules

- **Series assignments**: Select episodes from a specific series according to the episode_policy
- **Asset assignments**: Schedule a specific asset (useful for one-off content like specials or movies)
- **Rule assignments**: Apply a rule for content selection (e.g., "random family movie under 2 hours")
- **Random assignments**: System selects content based on compatibility, freshness, least-recently-used, etc.

**Critical Rule:** Assignments define *content*, not template blocks. They fill blocks with actual selections but must follow the rules from the template block they're part of.

## Failure / Fallback Behavior

If plans are missing or invalid:

- The system falls back to the most recent valid plan or default programming
- ScheduleService skips plans where `is_active=false`
- Missing or invalid block assignments result in gaps (allowed but should generate warnings)
- Invalid assignments (e.g., violating template block rules) should be flagged during validation

## Scheduling Model

- Plans are reusable across multiple channels and dates via template relationships
- Plans can be layered with priority-based resolution
- Plans are timeless and cron-like - valid from start to end dates every year
- Block assignments define specific content selections, not template blocks
- Operators choose what to place in blocks, but may request system suggestions
- Dry run and validation features should be supported to visualize gaps or rule violations

## Lifecycle and Referential Integrity

- `is_active=false` archives the plan: ScheduleService excludes the plan from schedule generation. Existing assignments remain but are ignored.
- Hard delete is only permitted when no dependent rows exist (e.g., SchedulePlanBlockAssignment, BroadcastScheduleDay). When dependencies exist, prefer archival (`is_active=false`).
- The dependency preflight MUST cover: SchedulePlanBlockAssignment, BroadcastScheduleDay, and any EPG/playlog references that depend on the plan.

## Operator Workflows

**Create Plan**: Define a new plan that fills a template with content selections. Specify name, template, temporal validity (cron/date range), and priority.

**Manage Block Assignments**: Add, modify, or remove SchedulePlanBlockAssignment records to define specific content for each template block.

**Layer Plans**: Create multiple plans with different priorities and temporal validity to handle recurring patterns (weekdays, weekends, holidays, seasons).

**Preview Schedule**: Use dry-run or preview features to visualize how a plan will resolve into a BroadcastScheduleDay.

**Validate Plan**: Check for gaps, rule violations, or assignment conflicts before activating the plan.

**Override Plans**: Use higher-priority plans to override general plans for specific dates or patterns (e.g., "ChristmasPlan" overrides "WeekdayPlan" on December 25).

**Archive Plans**: Deactivate plans that are superseded rather than deleting them, preserving history.

### CLI Command Examples

**Create Plan**: Use `retrovue schedule-plan add` (or `retrovue plan add`) with required parameters:

```bash
retrovue schedule-plan add --name "WeekdayPlan" \
  --template-id <uuid> \
  --description "Weekday programming plan" \
  --cron "0 6 * * MON-FRI" \
  --priority 10
```

**List Plans**: Use `retrovue schedule-plan list` to see all plans in table format, or `retrovue schedule-plan list --json` for machine-readable output.

**Show Plan**: Use `retrovue schedule-plan show --id <uuid>` or `retrovue schedule-plan show --name <name>` to see detailed plan information including associated block assignments.

**Add Block Assignment**: Use `retrovue schedule-plan assignment add` to assign content to a template block:

```bash
retrovue schedule-plan assignment add --plan-id <uuid> \
  --template-block-id <uuid> \
  --start-offset 0 \
  --end-offset 30 \
  --content-type series \
  --content-reference "Tom & Jerry" \
  --episode-policy syndication
```

**Preview Schedule**: Use `retrovue schedule-plan preview --plan-id <uuid> --date 2025-12-25` to see how a plan resolves for a specific date.

**Validate Plan**: Use `retrovue schedule-plan validate --plan-id <uuid>` to check for gaps, rule violations, or conflicts.

**Activate/Deactivate**: Use `retrovue schedule-plan update --id <uuid> --active` or `--inactive` to toggle is_active status.

**Update Plan**: Use `retrovue schedule-plan update --id <uuid>` with any combination of fields to modify plan properties.

**Delete Plan**: Use `retrovue schedule-plan delete --id <uuid>` to permanently remove a plan (only if no dependencies exist).

All operations use UUID identifiers for plan identification. The CLI provides both human-readable and JSON output formats.

## Validation & Invariants

- **Name uniqueness**: `name` must be unique across all plans (enforced at database level)
- **Active status**: Only plans where `is_active=true` are eligible for schedule generation
- **Template relationship**: Plan must reference a valid ScheduleTemplate
- **Block assignment coverage**: Plans should have assignments for all template blocks, though gaps are allowed (with warnings)
- **Rule compliance**: Block assignments must respect the constraints defined in their parent ScheduleTemplateBlock's `rule_json`
- **No overlapping assignments**: Assignments within the same plan and template block must not overlap
- **Referential integrity**: Plans cannot be deleted if they have dependent SchedulePlanBlockAssignment or BroadcastScheduleDay records

## Out of Scope (v0.1)

- Plan versioning and effective-dated changes
- Plan inheritance or composition
- Automatic content suggestion algorithms (though operators may request suggestions)
- Ad pod composition and overlay timing within assignments
- Real-time plan modification during active broadcast

## See Also

- [Scheduling](Scheduling.md) - High-level scheduling system
- [ScheduleTemplate](ScheduleTemplate.md) - Reusable programming templates (structure)
- [ScheduleTemplateBlock](ScheduleTemplateBlock.md) - Time blocks within templates with content selection rules
- [ScheduleDay](ScheduleDay.md) - Resolved schedules for specific channel and date
- [Channel](Channel.md) - Channel configuration and timing policy
- [Asset](Asset.md) - Approved content available for scheduling
- [PlaylogEvent](PlaylogEvent.md) - Generated playout events
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures

