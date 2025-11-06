_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md) • [Contracts](../contracts/README.md) • [ScheduleDay](ScheduleDay.md) • [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) • [SchedulePlanLabel](SchedulePlanLabel.md)_

# Domain — SchedulePlan

## Purpose

SchedulePlan is the **new top-level unit of channel programming**. It is the **single source of scheduling logic** for channel programming, replacing the previous template-based model. Each SchedulePlan represents a complete programming day that begins at 00:00 (relative to the channel's `broadcast_day_start` anchor) and consists of sequential [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) entries that define what content plays and when.

SchedulePlans are layered (Photoshop-style) and can be overridden (e.g., weekday vs. holiday), with more specific layers overriding more generic ones. Plans are channel-bound and span repeating or one-time timeframes. Superseded plans are archived rather than deleted. Plan-based scheduling flows into [ScheduleDay](ScheduleDay.md), which is resolved 3-5 days in advance for EPG and playout purposes.

**Key Points:**
- SchedulePlan is the **new top-level unit of channel programming** — the authoritative source for all scheduling decisions
- Each plan begins at programming day 00:00 (relative to the channel's `broadcast_day_start` anchor) and spans a 24-hour timeline
- Each plan consists of **sequential block assignments** — SchedulePlanBlockAssignment entries that define what content plays and when
- Block assignments can reference either **directly scheduled assets** or **[VirtualAssets](VirtualAsset.md)** (containers that expand to multiple assets)
- Optional [SchedulePlanLabel](SchedulePlanLabel.md) entries provide visual organization and daypart planning (e.g., "Morning", "Afternoon", "Prime Time") but do not affect scheduling logic
- Plans are channel-bound and span repeating or one-time timeframes
- Plans are layered with more specific plans (e.g., holidays) overriding generic ones (e.g., weekdays)
- Templates have been removed; all scheduling logic is defined directly in SchedulePlan
- Plan-based scheduling flows into ScheduleDay, resolved 3-5 days in advance for EPG and playout

## Core Model / Scope

SchedulePlan is the **new top-level unit of channel programming** and the **single source of scheduling logic** for channel programming. It represents a complete programming day that begins at 00:00 (relative to the channel's `broadcast_day_start` anchor) and consists of sequential block assignments. It is a reusable planning construct that:

- **Top-level unit of channel programming**: SchedulePlan is the authoritative source for all scheduling decisions; templates have been removed
- **Begins at programming day 00:00**: Each plan represents a timeline that begins at 00:00 relative to the channel's `broadcast_day_start` anchor and spans 24 hours
- **Consists of sequential block assignments**: Each plan contains sequential [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) entries that define what content plays and when, ordered by their `start_time` offsets from 00:00
- **Supports direct assets and VirtualAssets**: Block assignments can reference either directly scheduled assets (specific content) or [VirtualAssets](VirtualAsset.md) (containers that expand to multiple assets at ScheduleDay or Playlog time)
- **Optional visual organization**: [SchedulePlanLabel](SchedulePlanLabel.md) entries can be used for visual organization and daypart planning (e.g., grouping assignments into "Morning", "Afternoon", "Prime Time" dayparts), but labels do not affect scheduling logic
- **Is channel-bound**: Plans are bound to specific channels and span repeating or one-time timeframes
- **Supports layering and overrides**: Plans are layered (Photoshop-style) and can be overridden (e.g., weekday vs. holiday), with more specific layers overriding more generic ones
- **Is timeless but date-bound**: Plans are timeless (reusable patterns) but bound by effective date ranges (start_date, end_date). Superseded plans are archived (`is_active=false`) rather than deleted
- **Flows into ScheduleDay**: Plan-based scheduling flows into [ScheduleDay](ScheduleDay.md), which is resolved 3-5 days in advance for EPG and playout purposes

## Persistence Model

SchedulePlan is managed by SQLAlchemy with the following fields:

- **id** (UUID, primary key): Unique identifier for relational joins and foreign key references
- **name** (Text, required, unique): Plan identifier (e.g., "WeekdayPlan", "ChristmasPlan", "SummerBlock")
- **description** (Text, optional): Human-readable description of the plan's programming intent
- **cron_expression** (Text, optional): Cron-style expression defining when this plan is active (e.g., "0 6 * * MON-FRI" for weekdays 6am)
- **start_date** (Date, optional): Start date for plan validity (inclusive, can be year-agnostic)
- **end_date** (Date, optional): End date for plan validity (inclusive, can be year-agnostic)
- **priority** (Integer, required, default: 0): Priority for layering; higher priority plans override lower priority plans
- **is_active** (Boolean, required, default: true): Plan operational status; only active plans are eligible for use
- **created_at** (DateTime(timezone=True), required): Record creation timestamp
- **updated_at** (DateTime(timezone=True), required): Record last modification timestamp

SchedulePlan has one-to-many relationships with:

- **SchedulePlanBlockAssignment**: Multiple block assignments can exist within a single plan to define specific content for time periods
- **BroadcastScheduleDay**: Plans are used to generate resolved schedule days

### Table Name

The table is named `schedule_plans` (plural). Schema migration is handled through Alembic. Postgres is the authoritative backing store.

### Constraints

- `name` must be unique across all plans
- `name` max length ≤ 255 characters (enforced at database level)
- `description` max length is database-dependent (typically unlimited for TEXT)
- `priority` must be non-negative (default: 0)
- `start_date` and `end_date` must be valid dates if provided
- `cron_expression` must be valid cron syntax if provided

### Layering and Priority Rules

SchedulePlans use a Photoshop-style layering model where plans are matched by effective dates, with more specific layers overriding more generic ones. Plans can be layered and overridden (e.g., weekday vs. holiday):

- Plans with higher `priority` values override plans with lower `priority` values when both are active and match the same date
- When multiple plans match (via cron_expression or date range), the highest priority plan is used
- More specific plans (e.g., holiday-specific plans like "ChristmasPlan") should have higher priority than general plans (e.g., "WeekdayPlan") to enable overrides
- Plans are channel-bound and span repeating or one-time timeframes
- Plans are timeless but bound by effective date ranges (`start_date`, `end_date`)
- Superseded plans are archived (`is_active=false`) rather than deleted, preserving history

## Contract / Interface

SchedulePlan is the **single source of scheduling logic** for channel programming. It represents a timeline that runs from 00:00 to 24:00 relative to the channel's `broadcast_day_start`. It defines:

- Plan identity and metadata (name, description)
- Channel binding - plans are channel-bound and span repeating or one-time timeframes
- Temporal validity (cron_expression, start_date, end_date) - plans are timeless but bound by effective date ranges
- Priority for layering (priority) - enables Photoshop-style layering where more specific plans (e.g., holidays) override generic ones (e.g., weekdays)
- Operational status (is_active) - superseded plans are archived rather than deleted
- Relationship to block assignments (SchedulePlanBlockAssignment) - each plan contains SchedulePlanBlockAssignment entries that define what to play and when

Plans are timeless and reusable by design. They directly contain programming structure and content selections for recurring patterns (e.g., weekdays, holidays, seasons) or one-time events. Each plan represents a timeline from 00:00 to 24:00 relative to the channel's `broadcast_day_start`, and all time assignments are absolute offsets from that point. Templates have been removed; all scheduling logic is defined directly in SchedulePlan.

Content selection can include regular assets or VirtualAssets. Plan-based scheduling flows into [ScheduleDay](ScheduleDay.md), which is resolved 3-5 days in advance for EPG and playout purposes. ScheduleDays are then used to generate [PlaylogEvent](PlaylogEvent.md) records for actual playout execution.

## Execution Model

SchedulePlan is the **single source of scheduling logic** for channel programming. ScheduleService and schedule generation logic consume SchedulePlan records to determine actual content selections. Plan-based scheduling flows into ScheduleDay, which is resolved 3-5 days in advance:

1. **Identify active plans**: For a given channel and date, determine which plans are active based on cron_expression, effective date ranges (start_date, end_date), and is_active status. Plans are channel-bound and span repeating or one-time timeframes
2. **Resolve layering and overrides**: Apply Photoshop-style layering - if multiple plans match, select the plan with the highest priority. More specific plans (e.g., holidays) override generic ones (e.g., weekdays)
3. **Apply block assignments**: Use the SchedulePlanBlockAssignment entries in the plan to determine what content should air at specific times. Content selection can include regular assets or VirtualAssets
4. **Generate BroadcastScheduleDay**: Resolve the plan into a concrete [BroadcastScheduleDay](ScheduleDay.md) for the specific channel and date (resolved 3-5 days in advance for EPG and playout purposes)
5. **Generate PlaylogEvents**: From the resolved ScheduleDay, generate [BroadcastPlaylogEvent](PlaylogEvent.md) records for actual playout execution
6. **Validate assignments**: Ensure all block assignments are valid and consistent

## SchedulePlanBlockAssignment

SchedulePlanBlockAssignment represents a scheduled piece of content in a SchedulePlan. Each plan consists of **sequential block assignments** that define content to play at specific times, relative to the broadcast day start (00:00). Block assignments can reference either **directly scheduled assets** (specific content) or **[VirtualAssets](VirtualAsset.md)** (containers that expand to multiple assets at ScheduleDay or Playlog time). For complete documentation, see [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md).

### Time Model

**Broadcast Day Timeline:** Each SchedulePlan represents a timeline that runs from 00:00 to 24:00 relative to the channel's `broadcast_day_start`. All time assignments within a plan are **absolute offsets** from this 00:00 starting point.

- `start_time` is specified as "HH:MM" format and represents an absolute offset from 00:00 broadcast time
- For example, `start_time: "06:00"` means 6 hours after the broadcast day start (00:00)
- `duration` specifies how long the content should play in minutes
- The timeline spans from 00:00 to 24:00 relative to the channel's `broadcast_day_start`
- Assignments can span midnight (e.g., start_time: "22:00", duration: 240 minutes spans to 02:00 next day)

**Visual Organization and Daypart Planning:** Optional [SchedulePlanLabel](SchedulePlanLabel.md) entries such as "Morning", "Afternoon", "Prime Time" may be used for visual organization and daypart planning. Labels can be associated with block assignments to group them into logical dayparts (e.g., all morning assignments might share a "Morning" label). These labels provide operator convenience and workflow organization but do not affect scheduling logic — they are purely visual aids for understanding and managing the plan structure.

SchedulePlanBlockAssignments directly define content with `start_time` and `duration` as absolute offsets from 00:00 broadcast time. Each SchedulePlan contains one or more SchedulePlanBlockAssignments that place content in a schedule at specific times.

### Persistence Model

SchedulePlanBlockAssignment is managed by SQLAlchemy with the following fields:

- **id** (UUID, primary key): Unique identifier for relational joins and foreign key references
- **plan_id** (UUID, required, foreign key): Reference to parent SchedulePlan
- **start_time** (Text, required): Start time in "HH:MM" format representing an absolute offset from 00:00 broadcast time (e.g., "06:00" means 6 hours after broadcast day start)
- **duration** (Integer, required): Duration in minutes for this assignment
- **content_type** (Text, required): Type of content selection - one of: "series", "asset", "rule", "random", "virtual_package"
- **content_reference** (Text, required): Reference to the content:
  - For "series": Series identifier or UUID
  - For "asset": Asset UUID (directly scheduled asset)
  - For "rule": Rule JSON (e.g., "random family movie under 2 hours")
  - For "random": Random selection rule JSON
  - For "virtual_package": [VirtualAsset](VirtualAsset.md) UUID (container that expands to multiple assets)
- **episode_policy** (Text, optional): Episode selection policy (e.g., "sequential", "syndication", "random", "least-recently-used")
- **created_at** (DateTime(timezone=True), required): Record creation timestamp
- **updated_at** (DateTime(timezone=True), required): Record last modification timestamp

### Constraints

- `start_time` must be valid "HH:MM" format time representing an absolute offset from 00:00 broadcast time
- `duration` must be a positive integer (duration in minutes)
- `content_type` must be one of: "series", "asset", "rule", "random", "virtual_package"
- Assignments must not overlap within the same plan (calculated using start_time + duration)
- Time assignments are relative to the broadcast day start (00:00) and are absolute offsets from that point

### Content Selection Rules

Block assignments can reference either **directly scheduled assets** or **[VirtualAssets](VirtualAsset.md)**:

- **Series assignments**: Select episodes from a specific series according to the episode_policy
- **Asset assignments**: Schedule a specific asset directly (useful for one-off content like specials or movies)
- **VirtualAsset assignments**: Reference a [VirtualAsset](VirtualAsset.md) container (fixed sequence or rule-based) that expands to multiple assets at ScheduleDay or Playlog time
- **Rule assignments**: Apply a rule for content selection (e.g., "random family movie under 2 hours")
- **Random assignments**: System selects content based on compatibility, freshness, least-recently-used, etc.

**Critical Rules:**
- Assignments directly define what content runs when using `start_time` (absolute offset from 00:00) and `duration`
- Each plan represents a timeline from 00:00 to 24:00 relative to the channel's `broadcast_day_start`, and all time assignments are absolute offsets from that point
- Block assignments can reference either **directly scheduled assets** (specific content) or **[VirtualAssets](VirtualAsset.md)** (containers that expand to multiple assets)
- Assignments are sequential within a plan, ordered by their `start_time` offsets from 00:00
- They are self-contained and do not require any external block definitions
- Optional [SchedulePlanLabel](SchedulePlanLabel.md) entries may be used for visual organization and daypart planning but do not affect scheduling logic

## Failure / Fallback Behavior

If plans are missing or invalid:

- The system falls back to the most recent valid plan or default programming
- ScheduleService skips plans where `is_active=false`
- Missing or invalid block assignments result in gaps (allowed but should generate warnings)
- Invalid assignments (e.g., violating optional block constraints) should be flagged during validation

## Scheduling Model

- **Single source of scheduling logic**: SchedulePlan is the single source of scheduling logic for channel programming; templates have been removed
- **24-hour timeline**: Each plan represents a timeline from 00:00 to 24:00 relative to the channel's `broadcast_day_start`
- **Contains block assignments**: Each SchedulePlan contains SchedulePlanBlockAssignment entries that define what to play and when
- **Channel-bound**: Plans are channel-bound and span repeating or one-time timeframes
- **Layering and overrides**: Plans are layered (Photoshop-style) and can be overridden (e.g., weekday vs. holiday), with more specific layers overriding generic ones
- **Content selection**: Content selection can include regular assets or VirtualAssets
- **Timeless but date-bound**: Plans are timeless (reusable patterns) but bound by effective date ranges
- **Archival**: Superseded plans are archived (`is_active=false`) rather than deleted
- **Flows to ScheduleDay**: Plan-based scheduling flows into ScheduleDay, resolved 3-5 days in advance for EPG and playout
- **Self-contained**: Plans are self-contained and directly define channel programming
- **Operator control**: Operators choose what to place in time slots, but may request system suggestions
- **Validation**: Dry run and validation features should be supported to visualize gaps or rule violations

## Lifecycle and Referential Integrity

- `is_active=false` archives the plan: ScheduleService excludes the plan from schedule generation. Existing assignments remain but are ignored.
- Hard delete is only permitted when no dependent rows exist (e.g., SchedulePlanBlockAssignment, BroadcastScheduleDay). When dependencies exist, prefer archival (`is_active=false`).
- The dependency preflight MUST cover: SchedulePlanBlockAssignment, BroadcastScheduleDay, and any EPG/playlog references that depend on the plan.

## Operator Workflows

**Create Plan**: Define a new plan that directly defines channel programming. Specify name, temporal validity (cron/date range), and priority. Plans are the top-level object and are self-contained.

**Manage Block Assignments**: Add, modify, or remove SchedulePlanBlockAssignment records to define time slots and content selections within the plan.

**Layer Plans**: Create multiple plans with different priorities and effective date ranges to handle recurring patterns (weekdays, weekends, holidays, seasons) or one-time timeframes. Use Photoshop-style layering where more specific plans override generic ones. Plans can be layered and overridden (e.g., weekday vs. holiday).

**Preview Schedule**: Use dry-run or preview features to visualize how a plan will resolve into a BroadcastScheduleDay.

**Validate Plan**: Check for gaps, rule violations, or assignment conflicts before activating the plan.

**Override Plans**: Use higher-priority plans to override general plans for specific dates or patterns. For example, a "HolidayPlan" can override a "WeekdayPlan" on holidays, or a "ChristmasPlan" can override a "WeekdayPlan" on December 25.

**Archive Plans**: Archive plans (`is_active=false`) that are superseded rather than deleting them, preserving history. Plans are timeless but bound by effective date ranges, so superseded plans should be archived.

### CLI Command Examples

**Create Plan**: Use `retrovue schedule-plan add` (or `retrovue plan add`) with required parameters:

```bash
retrovue schedule-plan add --name "WeekdayPlan" \
  --description "Weekday programming plan" \
  --cron "0 6 * * MON-FRI" \
  --priority 10
```

**List Plans**: Use `retrovue schedule-plan list` to see all plans in table format, or `retrovue schedule-plan list --json` for machine-readable output.

**Show Plan**: Use `retrovue schedule-plan show --id <uuid>` or `retrovue schedule-plan show --name <name>` to see detailed plan information including associated block assignments.

**Add Block Assignment**: Use `retrovue schedule-plan assignment add` to assign content to a time slot:

```bash
retrovue schedule-plan assignment add --plan-id <uuid> \
  --start-time 06:00 \
  --duration 30 \
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
- **Block assignment coverage**: Plans should have assignments covering the programming day, though gaps are allowed (with warnings)
- **Time structure**: Assignments directly define time structure using `start_time` and `duration`
- **No overlapping assignments**: Assignments within the same plan must not overlap in time
- **Referential integrity**: Plans cannot be deleted if they have dependent SchedulePlanBlockAssignment or BroadcastScheduleDay records

## Out of Scope (v0.1)

- Plan versioning and effective-dated changes
- Plan inheritance or composition
- Automatic content suggestion algorithms (though operators may request suggestions)
- Ad pod composition and overlay timing within assignments
- Real-time plan modification during active broadcast

## See Also

- [Scheduling](Scheduling.md) - High-level scheduling system
- [ScheduleDay](ScheduleDay.md) - Resolved schedules for specific channel and date
- [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) - Scheduled pieces of content in plans (source of truth for what should air when)
- [SchedulePlanLabel](SchedulePlanLabel.md) - Optional UI-only labels for visual organization
- [Channel](Channel.md) - Channel configuration and timing policy
- [Asset](Asset.md) - Approved content available for scheduling
- [PlaylogEvent](PlaylogEvent.md) - Generated playout events
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures

SchedulePlan is the **single source of scheduling logic** for channel programming. Each SchedulePlan represents a timeline that runs from 00:00 to 24:00 relative to the channel's `broadcast_day_start`. Each SchedulePlan contains SchedulePlanBlockAssignment entries that define what to play and when. Plans are channel-bound and span repeating or one-time timeframes. Plans are layered (Photoshop-style) and can be overridden (e.g., weekday vs. holiday), with more specific layers overriding generic ones. Templates have been removed; all scheduling logic is defined directly in SchedulePlan. Content selection can include regular assets or VirtualAssets. Plans are timeless but bound by effective date ranges, and superseded plans are archived. Plan-based scheduling flows into ScheduleDay, which is resolved 3-5 days in advance for EPG and playout purposes. Optional visual labels (see [SchedulePlanLabel](SchedulePlanLabel.md)) may be used in the UI for operator organization but do not affect scheduling logic.

