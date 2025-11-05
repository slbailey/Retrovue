_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md) • [Contracts](../contracts/README.md) • [Channel](Channel.md) • [ScheduleTemplate](ScheduleTemplate.md) • [SchedulePlan](SchedulePlan.md) • [ScheduleTemplateBlock](ScheduleTemplateBlock.md)_

# Domain — Schedule day

## Purpose

BroadcastScheduleDay represents a resolved schedule for a specific channel and date. It's built from a SchedulePlan using the active ScheduleTemplate. Once generated, it becomes immutable unless manually overridden. The EPG references this layer. This is the execution-time view of "what will air on this channel on this date" after resolving plans and templates into concrete content selections.

## Persistence model

BroadcastScheduleDay is managed by SQLAlchemy with the following fields:

- **id** (UUID, primary key): Unique identifier for relational joins and foreign key references
- **channel_id** (UUID, required, foreign key): Reference to Channel
- **plan_id** (UUID, optional, foreign key): Reference to SchedulePlan that generated this schedule day
- **template_id** (UUID, required, foreign key): Reference to ScheduleTemplate used (may be resolved from plan)
- **schedule_date** (Text, required): Broadcast date in "YYYY-MM-DD" format
- **is_manual_override** (Boolean, required, default: false): Whether this schedule day was manually overridden
- **created_at** (DateTime(timezone=True), required): Record creation timestamp
- **updated_at** (DateTime(timezone=True), required): Record last modification timestamp

BroadcastScheduleDay has a unique constraint on (channel_id, schedule_date) ensuring only one schedule per channel per date.

**Note:** While `plan_id` is optional, the system typically generates schedule days from plans. Manual overrides may not reference a plan.

### Table name

The table is named `broadcast_schedule_days` (plural). Schema migration is handled through Alembic. Postgres is the authoritative backing store.

### Constraints

- `schedule_date` must be in "YYYY-MM-DD" format
- Unique constraint on (channel_id, schedule_date) ensures only one template per channel per broadcast day
- Foreign key constraints ensure channel_id and template_id reference valid entities

## Contract / interface

BroadcastScheduleDay provides the resolved schedule for a specific channel and date. It defines:

- Channel assignment (channel_id)
- Plan reference (plan_id) - the plan that generated this schedule
- Template reference (template_id) - the template structure used (resolved from plan)
- Date assignment (schedule_date)
- Manual override flag (is_manual_override) - indicates if this was manually overridden
- Unique constraint ensuring one schedule per channel per date

Schedule days are the resolved output of the planning process. They represent "what will actually air" after resolving plans (content selections) and templates (structure/constraints) into concrete schedules.

## Execution model

ScheduleService generates BroadcastScheduleDay records by resolving SchedulePlans for specific channels and dates. The process:

1. **Plan resolution**: For a given channel and date, identify the active SchedulePlan (based on cron_expression, date ranges, priority)
2. **Template resolution**: Retrieve the ScheduleTemplate referenced by the plan
3. **Block resolution**: Retrieve ScheduleTemplateBlock records (constraints) and SchedulePlanBlockAssignment records (content selections)
4. **Validation**: Ensure assignments respect template block constraints
5. **Schedule generation**: Create BroadcastScheduleDay record with resolved content
6. **Playlog generation**: Generate BroadcastPlaylogEvent entries from the resolved schedule

**Critical Rule:** Once generated, BroadcastScheduleDay is immutable unless manually overridden. This ensures the EPG and playout systems have a stable view of "what will air."

**Manual Overrides:** Operators can manually override a schedule day, creating a new BroadcastScheduleDay with `is_manual_override=true`. This breaks the link to the plan but preserves the schedule for that specific date.

## Failure / fallback behavior

If schedule assignments are missing or invalid, the system falls back to default programming or the most recent valid schedule.

## Naming rules

The canonical name for this concept in code and documentation is BroadcastScheduleDay.

Schedule assignments are programming decisions, not runtime components. They define "what template to use when" but do not execute scheduling.

## Operator workflows

**Generate Schedule Days**: ScheduleService automatically generates BroadcastScheduleDay records from active SchedulePlans. Operators don't manually create schedule days in normal operation.

**Preview Schedule**: Use preview/dry-run features to see how a plan will resolve into a BroadcastScheduleDay before it's generated.

**Manual Override**: Manually override a generated schedule day for special events, breaking news, or one-off programming changes. This creates a new BroadcastScheduleDay with `is_manual_override=true`.

**Regenerate Schedule**: Force regeneration of a schedule day from its plan (useful after plan updates).

**Validate Schedule**: Check resolved schedule days for gaps, rule violations, or content conflicts.

**Multi-Channel Programming**: Different channels can have different plans, resulting in different schedule days for the same date.

**Schedule Inspection**: View resolved schedule days to see "what will air" for a specific channel and date.

## See also

- [Scheduling](Scheduling.md) - High-level scheduling system
- [SchedulePlan](SchedulePlan.md) - Operator-created plans that fill templates with actual content
- [ScheduleTemplate](ScheduleTemplate.md) - Reusable programming templates (structure)
- [ScheduleTemplateBlock](ScheduleTemplateBlock.md) - Time blocks within templates with content type constraints
- [Channel](Channel.md) - Channel configuration and timing policy
- [PlaylogEvent](PlaylogEvent.md) - Generated playout events
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
