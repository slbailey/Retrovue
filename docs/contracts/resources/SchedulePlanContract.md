# SchedulePlan

Status: Enforced

## Purpose

This document provides an overview of all SchedulePlan domain testing contracts. Individual SchedulePlan operations are covered by specific behavioral contracts that define exact CLI syntax, safety expectations, and data effects. SchedulePlans are the top-level unit of channel programming, defining Zones (time windows) and Patterns (content sequences).

---

## Scope

The SchedulePlan domain is covered by the following specific contracts:

- **[SchedulePlan Add](SchedulePlanAddContract.md)**: Creating new schedule plans (non-interactive, API/web UI use)
- **[SchedulePlan Build](SchedulePlanBuildContract.md)**: Creating new schedule plans with interactive REPL (CLI use)
- **[SchedulePlan List](SchedulePlanListContract.md)**: Listing schedule plans
- **[SchedulePlan Show](SchedulePlanShowContract.md)**: Displaying a schedule plan
- **[SchedulePlan Update](SchedulePlanUpdateContract.md)**: Updating plan configuration/state
- **[SchedulePlan Delete](SchedulePlanDeleteContract.md)**: Deleting plans (guarded by dependency checks)

---

## Contract Structure

Each SchedulePlan operation follows the standard contract pattern:

1. **Command Shape**: Exact CLI syntax and required flags
2. **Safety Expectations**: Confirmation prompts, dry-run behavior (where applicable)
3. **Output Format**: Human-readable and JSON output structure
4. **Exit Codes**: Success and failure exit codes
5. **Data Effects**: What changes in the database
6. **Behavior Contract Rules (B-#)**: Operator-facing behavior guarantees
7. **Data Contract Rules (D-#)**: Persistence, lifecycle, and integrity guarantees
8. **Test Coverage Mapping**: Explicit mapping from rule IDs to test files

---

## Design Principles

- **Safety first:** No destructive operation runs against live data during automated tests
- **One contract per noun/verb:** Each SchedulePlan operation has its own focused contract
- **Mock-first validation:** All operations must first be tested using mock/test databases
- **Idempotent where appropriate:** `list`/`show` are read-only and repeatable; `add`/`update` are deterministic with explicit validation
- **Clear error handling:** Failed operations provide actionable diagnostics
- **Unit of Work:** All database-modifying operations are wrapped in atomic transactions
- **Channel-bound:** Plans are bound to specific channels; name uniqueness is per-channel

---

## Common Safety Patterns

### Test Database Usage

- `--test-db` flag directs operations to an isolated test environment
- Test database must be completely isolated from production
- No test data should persist between test sessions

### Confirmation Models

- Destructive operations (e.g., delete) require confirmation prompts
- `--yes` flag skips confirmations in non-interactive contexts

### Channel Binding

- All plans are bound to a specific channel via `channel_id`
- Plan names must be unique within each channel (not globally)
- Channel must exist before plan creation

### Temporal Validity

- Plans use `start_date`/`end_date` for date range matching
- Plans use `cron_expression` for recurring patterns (day-of-week/month only; hour/minute ignored)
- Both can be used together for complex matching
- Cron matching is evaluated against MasterClock (system local time)

### Clock & Calendar

All date and cron evaluation use the system clock via MasterClock. There is no per-channel timezone setting. Cron evaluation uses MasterClock day-of-week/month only; hour/minute ignored.

### Priority Layering

- Plans have a `priority` field (higher number = higher priority)
- When multiple plans match a date, the highest priority plan wins
- More specific plans (e.g., holidays) should have higher priority than generic ones

---

## SchedulePlan Lifecycle

1. **Creation**: Plan is created with channel binding, name, temporal validity, and priority
2. **Configuration**: Zones and Patterns are added to define programming structure
3. **Activation**: Plan becomes eligible for schedule generation when `is_active=true`
4. **Archival**: `is_active=false` excludes plan from schedule generation (historical data retained)
5. **Deletion**: Only allowed with no dependencies (Zones, Patterns, ScheduleDays)

---

## Validation Scope & Triggers

- Validate on `add`, `update`, and via explicit validation commands
- Always validate the SchedulePlan row
- **Coverage Invariant (INV_PLAN_MUST_HAVE_FULL_COVERAGE)**: All plans must satisfy full 24-hour coverage (00:00–24:00) with no gaps. Plans are automatically initialized with a default "test pattern" zone (00:00–24:00) when created without explicit zones. See [Scheduling Invariants](SchedulingInvariants.md) S-INV-14 for details.
- Cross-validate Zone/Pattern alignment with Channel Grid boundaries
- Validate cron expression syntax (if provided)
- Validate date ranges (start_date <= end_date)
- Validate name uniqueness within channel

## DST Behavior

DST transitions are resolved by MasterClock. Zones/patterns snap to grid; "soft-start-after-current" prevents mid-program cuts on 23h/25h broadcast days.

---

## Contract Test Requirements

Each SchedulePlan contract should have exactly two test files:

1. **CLI Contract Test**: `tests/contracts/test_plan_{verb}_contract.py`

   - CLI syntax validation
   - Flag behavior verification
   - Output format validation
   - Error message handling

2. **Data Contract Test**: `tests/contracts/test_plan_{verb}_data_contract.py`

   - Database state changes
   - Transaction boundaries
   - Data integrity verification
   - Side effects validation

---

## See Also

- [Scheduling Invariants](SchedulingInvariants.md) - Cross-cutting scheduling invariants
- [Scheduling Invariants → S-INV-14 Coverage Invariant](SchedulingInvariants.md#s-inv-14-plan-must-have-full-coverage-inv_plan_must_have_full_coverage) - Plan full coverage requirement (00:00–24:00)
- [SchedulePlan Domain Documentation](../../domain/SchedulePlan.md) - Core domain model and rules
- [Zone Contract](ZoneContract.md) - Zone operations within plans
- [Pattern Contract](PatternContract.md) - Pattern operations within plans
- [CLI Contract](README.md) - General CLI command standards
- [Unit of Work](../_ops/UnitOfWorkContract.md) - Transaction management requirements
