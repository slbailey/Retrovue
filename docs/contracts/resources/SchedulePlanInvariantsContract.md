# Schedule Plan Invariants Contract

_Related: [Domain: SchedulePlan](../../domain/SchedulePlan.md) • [Domain: ScheduleDay](../../domain/ScheduleDay.md)_

## Purpose

**Note:** ScheduleTemplate and ScheduleTemplateBlock have been deprecated. SchedulePlan is now the top-level structure that directly defines channel programming. Program directly defines what content runs when using `start_time` and `duration`. This contract defines the critical invariants and constraints that must be enforced for the plan-based scheduling model. These invariants ensure system correctness, prevent scheduling conflicts, and maintain data integrity across SchedulePlan, Program, and BroadcastScheduleDay.

## Scope

This contract applies to:

- **SchedulePlan** - Top-level operator-created plans that define channel programming. SchedulePlans define a 24-hour timeline relative to the channel's broadcast day start.
- **Program** - Time slices within plans that directly define what content runs when using `start_time` and `duration`
- **BroadcastScheduleDay** - Resolved schedules for specific channel and date
- **VirtualAsset** - Reusable containers that encapsulate structured content sequences
- **ContentPolicyRule** - Rules used to validate assignment compatibility (future feature)

## Critical Invariants

### I-1: Plan Assignment Non-Overlap

**Rule:** Program entries within the same plan MUST NOT overlap.

**Rationale:** Each time slice within a plan must have exactly one content assignment. Overlapping assignments would create ambiguity about what content should play.

**Enforcement:**
- Database constraint or validation layer MUST prevent creation of overlapping assignments within the same `plan_id`
- Overlap detection MUST check: `(start_time < other.end_time) AND (end_time > other.start_time)` where `end_time = start_time + duration`
- Assignments that touch at boundaries (e.g., one ends where another starts) are allowed
- Time values are schedule-time (00:00 to 24:00 relative to programming day start)

**Test Coverage:** Tests must verify that:
- Creating overlapping assignments within the same plan fails
- Assignments in different plans can overlap (they're independent)
- Boundary cases (touching assignments) are handled correctly
- Time calculations correctly handle schedule-time offsets

### I-2: Plan Assignment Constraint Compliance (Future)

**Rule:** Program entries SHOULD respect constraints defined by ContentPolicyRule when referenced (future feature).

**Rationale:** ContentPolicyRules provide validation for assignment compatibility (e.g., rating, genre, duration constraints). When a rule is referenced, assignments should comply with its constraints.

**Enforcement:**
- When ContentPolicyRule is implemented, assignments referencing rules MUST validate against rule constraints
- Validation MUST check: content tags, ratings, duration limits, genre restrictions, etc. as defined in the rule
- Invalid assignments MUST be rejected with clear error messages

**Test Coverage:** Tests must verify that:
- Assignments that violate rule constraints are rejected (when rules are implemented)
- Assignments that comply with constraints are accepted
- Edge cases (empty constraints, wildcard constraints) are handled correctly

### I-3: Plan Priority Resolution

**Rule:** When multiple SchedulePlans match for a channel and date, the plan with the highest `priority` value MUST be selected.

**Rationale:** Plan layering allows more specific plans (e.g., "ChristmasPlan") to override general plans (e.g., "WeekdayPlan"). Priority determines which plan takes precedence.

**Enforcement:**
- Plan resolution MUST consider `is_active=true` plans only
- Plan resolution MUST evaluate `cron_expression` and `start_date`/`end_date` to determine matching plans
- Among matching plans, the plan with the highest `priority` MUST be selected
- If multiple plans have the same priority, behavior MUST be deterministic (e.g., highest `id` or creation time)

**Test Coverage:** Tests must verify that:
- Higher priority plans override lower priority plans when both match
- Inactive plans are excluded from resolution
- Cron expressions correctly determine plan matching
- Date ranges correctly determine plan matching
- Priority tie-breaking is deterministic

### I-4: ScheduleDay Immutability

**Rule:** BroadcastScheduleDay records MUST be immutable once generated, unless manually overridden.

**Rationale:** Schedule days represent "what will air" - once generated, they must remain stable for EPG and playout systems. Manual overrides are the exception.

**Enforcement:**
- ScheduleService MUST NOT modify existing BroadcastScheduleDay records during normal operation
- Manual overrides MUST create new BroadcastScheduleDay records with `is_manual_override=true`
- Regeneration MUST create a new BroadcastScheduleDay record (or delete and recreate) rather than modifying existing records
- Historical records MUST be preserved for audit purposes

**Test Coverage:** Tests must verify that:
- ScheduleService does not modify existing schedule days during normal operation
- Manual overrides create new records (not modify existing)
- Regeneration creates new records or properly replaces existing ones
- Historical records are preserved

### I-5: Asset Eligibility

**Rule:** Only assets with `state='ready'` and `approved_for_broadcast=true` are eligible for scheduling.

**Rationale:** This is a critical system-wide rule that ensures only approved, fully-processed content can be scheduled.

**Enforcement:**
- ScheduleService MUST filter assets by `state='ready'` AND `approved_for_broadcast=true` when selecting content
- Plan assignments MUST reference eligible assets only
- Validation MUST reject assignments that reference ineligible assets

**Test Coverage:** Tests must verify that:
- Only eligible assets are considered during schedule generation
- Assignments referencing ineligible assets are rejected
- Asset state changes properly affect schedule generation

## Validation Workflows

### Dry Run and Preview

**Rule:** The system MUST support dry-run and preview features that validate plans without generating actual schedule days.

**Requirements:**
- Preview MUST show how a plan resolves into a BroadcastScheduleDay
- Preview MUST highlight constraint violations, gaps, and conflicts
- Dry-run MUST validate all invariants without committing changes

### Gap Detection

**Rule:** The system SHOULD detect and warn about gaps in schedule coverage but MUST allow gaps (they don't violate invariants).

**Requirements:**
- Gaps are allowed (not an invariant violation)
- Warnings SHOULD be generated for gaps in playout
- Validation tools SHOULD highlight gaps for operator review

### Rule Violation Reporting

**Rule:** When plan assignments violate constraints (e.g., ContentPolicyRule constraints when implemented), the system MUST provide clear, actionable error messages.

**Requirements:**
- Error messages MUST identify the specific constraint violated
- Error messages MUST identify the specific assignment that violates the constraint
- Error messages MUST suggest corrective actions

## Out of Scope (v0.1)

The following are NOT part of this contract:

- Automatic content suggestion algorithms
- Ad pod composition and timing
- Real-time plan modification during active broadcast
- Plan versioning and effective-dated changes
- Template inheritance or composition

## Test Coverage Requirements

Each invariant (I-1 through I-5) MUST have corresponding test coverage that:

1. **Validates the invariant holds** in normal operation
2. **Verifies violation detection** when the invariant would be broken
3. **Confirms error handling** provides clear feedback
4. **Tests edge cases** and boundary conditions

## Related Contracts

- [UnitOfWorkContract](../_ops/UnitOfWorkContract.md) - Transaction boundaries for schedule operations
- [ProductionSafety](../_ops/ProductionSafety.md) - Safety requirements for production operations

## See Also

- [Domain: SchedulePlan](../../domain/SchedulePlan.md) - Complete domain documentation
- [Domain: Program](../../domain/Program.md) - Program domain documentation
- [ProgramContract](ProgramContract.md) - Program-specific contract rules
- [Domain: ScheduleDay](../../domain/ScheduleDay.md) - Resolved schedules

