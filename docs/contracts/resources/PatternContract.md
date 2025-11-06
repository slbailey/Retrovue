# Pattern Domain Contracts

_Related: [Pattern Add](PatternAddContract.md) • [Pattern Update](PatternUpdateContract.md) • [Pattern List](PatternListContract.md) • [Pattern Show](PatternShowContract.md) • [Pattern Delete](PatternDeleteContract.md) • [Domain: Pattern](../../domain/Pattern.md) • [Domain: SchedulePlan](../../domain/SchedulePlan.md) • [Domain: Zone](../../domain/Zone.md) • [Domain: Program](../../domain/Program.md)_

## Purpose

This document provides an overview of all Pattern domain testing contracts. Patterns are ordered lists of Program references that define content sequences within SchedulePlans. This contract ensures that Pattern validation, creation, and management behaviors are correctly implemented and can be verified through automated tests.

**Critical Rule:** These contracts are **testable assertions** that must be verified through automated tests. Each contract defines a specific behavior that the Pattern domain must guarantee.

## Status

**Status:** Draft - Contracts defined, implementation pending

## Scope

The Pattern domain is covered by the following specific contracts:

### CRUD Operations

- **[Pattern Add](PatternAddContract.md)**: Creating new Patterns within SchedulePlans
- **[Pattern Update](PatternUpdateContract.md)**: Updating Pattern configuration and metadata
- **[Pattern List](PatternListContract.md)**: Listing Patterns within a SchedulePlan
- **[Pattern Show](PatternShowContract.md)**: Displaying detailed Pattern information
- **[Pattern Delete](PatternDeleteContract.md)**: Deleting Patterns (guarded by dependency checks)

### Domain Validation Contracts

- **[Pattern Domain Validation Contracts](#domain-level-validation-contracts)** (this document): Domain-level validation and behavioral contracts
  - P-VAL-01 through P-VAL-06: Validation contracts
  - P-BEH-01 through P-BEH-02: Behavioral contracts

## Contract Structure

Each Pattern operation follows the standard contract pattern:

1. **Command Shape**: Exact CLI syntax and required flags
2. **Safety Expectations**: Confirmation prompts, validation behavior, dependency checks
3. **Output Format**: Human-readable and JSON output structure
4. **Exit Codes**: Success and failure exit codes
5. **Behavior Contract Rules (B-#)**: Operator-facing behavior guarantees
6. **Data Contract Rules (D-#)**: Persistence, lifecycle, and integrity guarantees
7. **Test Coverage Requirements**: Explicit test coverage mapping

## Design Principles

- **Safety first:** No destructive operation runs against live data during automated tests
- **One contract per noun/verb:** Each Pattern operation has its own focused contract
- **Mock-first validation:** All operations must first be tested using mock/test databases
- **Idempotent where appropriate:** `list`/`show` are read-only and repeatable; `add`/`update` are deterministic with explicit validation
- **Clear error handling:** Failed operations provide actionable diagnostics
- **Unit of Work:** All database-modifying operations are wrapped in atomic transactions
- **Program reference integrity:** Patterns are validated for Program membership and ordering

## Common Safety Patterns

### Test Database Usage

- `--test-db` flag directs operations to an isolated test environment
- Test database must be completely isolated from production
- No test data should persist between test sessions

### Destructive Operation Confirmation

- Delete operations require confirmation prompts
- `--yes` flag skips confirmations in non-interactive contexts
- See [_ops/DestructiveOperationConfirmation.md](../_ops/DestructiveOperationConfirmation.md)

### Dependency Checks

- Pattern deletion checks for dependent Zones
- Provides guidance to remove Zone references before deleting Pattern if dependencies exist

### Validation Scope & Triggers

- Validate on `add`, `update`, and via explicit validation commands
- Always validate the Pattern row
- Cross-validate Program-Pattern-Plan consistency
- Validate Program ordering within Patterns

## Pattern-Specific Guardrails

- **Name uniqueness**: Must be unique within SchedulePlan if provided (optional field)
- **Plan membership**: Pattern must belong to a valid SchedulePlan
- **Program consistency**: All Programs referencing a Pattern must belong to the same SchedulePlan as the Pattern
- **Program ordering**: Programs within a Pattern must have valid, non-negative `order` values
- **At least one Program**: Patterns should have at least one Program reference (enforced via application logic)
- **Pattern durationlessness**: Patterns never define duration, block size, or grid alignment directly — those are determined by Programs and the Channel grid

## Contract Test Requirements

Each Pattern contract should have exactly two test files:

1. **CLI Contract Test**: `tests/contracts/test_pattern_{verb}_contract.py`
   - CLI syntax validation
   - Flag behavior verification
   - Output format validation
   - Error message handling

2. **Data Contract Test**: `tests/contracts/test_pattern_{verb}_data_contract.py`
   - Database state verification
   - Transaction boundaries
   - Data integrity checks
   - Domain-level validation enforcement

---

## Domain-Level Validation Contracts

The following contracts define domain-level validation and behavioral rules that apply to Pattern entities regardless of the CRUD operation being performed.

These contracts apply to:

- **Pattern** - Ordered lists of Program references that define content sequences
- **SchedulePlan** - Parent plans that contain Patterns
- **Program** - Catalog entries that reference Patterns via `pattern_id` and `order`
- **Zone** - Time windows that reference Patterns to define content sequences

### P-VAL-01: Plan Reference Validity

**Contract:** Pattern `plan_id` MUST reference a valid SchedulePlan. Patterns cannot exist without a Plan reference.

**Behavior:**
- `plan_id` is a required field (non-nullable)
- Plan must exist in the database at Pattern creation/update time
- Plan must be valid (not deleted, belongs to channel)
- Validation fails early at Pattern creation/update time if Plan is missing or invalid

**Test Assertions:**
- Creating Pattern with `plan_id=null` → Invalid (rejected)
- Creating Pattern with `plan_id="non-existent-uuid"` → Invalid (Plan not found)
- Creating Pattern with valid `plan_id` → Valid
- Updating Pattern to set `plan_id=null` → Invalid (rejected)
- Deleting Plan referenced by Pattern → Must be prevented or Pattern must be deleted/updated first

**Related Documentation:**
- [Pattern.md](../../domain/Pattern.md) - Plan reference requirement
- [SchedulePlan.md](../../domain/SchedulePlan.md) - Plan existence

**Entities:** Pattern, SchedulePlan

---

### P-VAL-02: Name Uniqueness Within Plan

**Contract:** Pattern `name` MUST be unique within the SchedulePlan if provided. Multiple Patterns can have the same name if they belong to different Plans, or if name is null.

**Behavior:**
- Pattern names are scoped to the SchedulePlan (`plan_id`)
- Two Patterns in the same Plan cannot have the same non-null name
- Two Patterns in different Plans can have the same name
- Null names are allowed (multiple Patterns can have null names in the same Plan)
- Validation fails at Pattern creation/update time

**Test Assertions:**
- Creating Pattern "Prime Time Pattern" in Plan A → Valid
- Creating second Pattern "Prime Time Pattern" in Plan A → Invalid (name conflict)
- Creating Pattern "Prime Time Pattern" in Plan B → Valid (different plan)
- Creating Pattern with `name=null` in Plan A → Valid
- Creating second Pattern with `name=null` in Plan A → Valid (null names allowed)
- Updating Pattern name to conflict with existing Pattern in same plan → Invalid

**Related Documentation:**
- [Pattern.md](../../domain/Pattern.md) - Name uniqueness invariant

**Entities:** Pattern, SchedulePlan

---

### P-VAL-03: Program-Plan Consistency

**Contract:** All Programs that reference a Pattern MUST belong to the same SchedulePlan as that Pattern. This is enforced as an invariant.

**Behavior:**
- When a Program references a Pattern (via `Program.pattern_id`), the Program's `plan_id` must match the Pattern's `plan_id`
- Cross-plan Program references are rejected
- Validation fails early at Program creation/update time if Program-Pattern-Plan inconsistency detected
- Pattern validation should check all referencing Programs for consistency

**Test Assertions:**
- Program with `plan_id="plan-a"` referencing Pattern with `plan_id="plan-a"` → Valid
- Program with `plan_id="plan-a"` referencing Pattern with `plan_id="plan-b"` → Invalid (rejected)
- Pattern with Programs from different plans → Invalid (consistency violation)
- Updating Program to reference Pattern from different plan → Invalid (rejected)

**Related Documentation:**
- [Pattern.md](../../domain/Pattern.md) - Plan consistency invariant
- [Program.md](../../domain/Program.md) - Program-Pattern relationship

**Entities:** Pattern, Program, SchedulePlan

---

### P-VAL-04: Program Order Validity

**Contract:** Programs within a Pattern MUST have valid, non-negative `order` values. Programs with the same `pattern_id` are ordered by `order` to determine the Pattern's sequence.

**Behavior:**
- `order` must be a non-negative integer (0 or greater)
- Programs with the same `pattern_id` are ordered by `order` ascending
- Programs in a Pattern should have unique `order` values (enforced by application logic, not strict database constraint)
- If duplicate `order` values exist, system orders Programs by `order` ascending, then by `created_at` or `id` for deterministic ordering
- Validation occurs when retrieving Pattern's Program list

**Test Assertions:**
- Programs with `order=0, 1, 2` in Pattern → Valid (ordered sequence)
- Programs with `order=-1` → Invalid (negative order)
- Programs with `order=0, 0, 1` → Valid but should warn (duplicate orders handled gracefully)
- Programs with `order=null` → Invalid (order required if pattern_id is set)
- Pattern sequence determined by `order` ascending: `order=0` first, `order=1` second, etc.

**Related Documentation:**
- [Pattern.md](../../domain/Pattern.md) - Program ordering rules

**Entities:** Pattern, Program

---

### P-VAL-05: At Least One Program Reference

**Contract:** Patterns SHOULD have at least one Program reference. Empty Patterns generate warnings but do not block ScheduleDay generation.

**Behavior:**
- Patterns with no Program references are allowed (validation passes)
- Empty Patterns generate warnings at resolution time
- Zone expansion skips empty Patterns with logged warning
- Empty Patterns do not block ScheduleDay generation
- Application logic should encourage operators to add Programs to Patterns

**Test Assertions:**
- Creating Pattern with no Programs → Valid (allowed)
- Pattern with no Programs referenced by Zone → Warning logged, Zone expansion skips
- Adding first Program to Pattern → Valid (Pattern now has content)
- Removing all Programs from Pattern → Valid (allowed, but generates warning)

**Related Documentation:**
- [Pattern.md](../../domain/Pattern.md) - Empty Pattern handling

**Entities:** Pattern, Program

---

### P-VAL-06: Pattern Durationlessness

**Contract:** Patterns NEVER define duration, block size, or grid alignment directly. Durations and grid alignment are determined by Programs and the Channel grid.

**Behavior:**
- Patterns have no duration fields
- Patterns have no grid alignment fields
- Pattern expansion uses Program durations and Channel grid configuration
- Validation ensures Patterns do not have duration/alignment fields

**Test Assertions:**
- Pattern creation with duration field → Invalid (Patterns don't have durations)
- Pattern expansion uses Program durations → Valid
- Pattern expansion uses Channel grid boundaries → Valid
- Pattern defines time windows → Invalid (Zones define time windows, not Patterns)

**Related Documentation:**
- [Pattern.md](../../domain/Pattern.md) - Pattern durationlessness
- [Zone.md](../../domain/Zone.md) - Zone defines time windows

**Entities:** Pattern, Program, Channel

---

## Behavioral Contracts

### P-BEH-01: Pattern Repeating Behavior

**Contract:** Patterns MUST repeat cyclically across Zone time windows until the Zone's declared end time is reached. Pattern repeating snaps to Channel Grid boundaries.

**Behavior:**
- Pattern repeating is cyclical: once all Programs in the Pattern have been placed, the Pattern repeats from the beginning
- Each Program placement snaps to the next valid Grid boundary
- Pattern repeating continues until the Zone's declared end time is reached
- If a Pattern does not fully fill a Zone, the Zone ends at its declared end time, and under-filled time becomes avails

**Test Assertions:**
- Pattern `["A", "B", "C"]` in Zone `00:00-06:00` → Repeats cyclically (A, B, C, A, B, C, ...)
- Pattern `["Movie Block"]` (1.5 hours) in Zone `20:00-22:00` (2 hours) → Movie plays 20:00-21:30, Zone ends at 22:00, 21:30-22:00 becomes avails
- Pattern expansion snaps to Grid boundaries → Valid
- Pattern repeating continues until Zone end time → Valid

**Related Documentation:**
- [Pattern.md](../../domain/Pattern.md) - Pattern repeating behavior
- [ZonesPatterns.md](../ZonesPatterns.md) - C-PATTERN-01

**Entities:** Pattern, Zone, Channel, ScheduleDay

---

### P-BEH-02: Program Resolution at ScheduleDay Time

**Contract:** Programs in Patterns MUST be resolved to concrete episodes/assets at ScheduleDay time, not at Pattern creation time.

**Behavior:**
- Pattern creation stores Program references (catalog entries), not concrete episodes
- Program resolution occurs during ScheduleDay generation
- Series Programs resolve to specific episodes based on rotation policy
- Asset Programs resolve to the referenced asset
- VirtualAsset Programs expand to multiple assets
- Rule Programs resolve to assets selected from the filtered set

**Test Assertions:**
- Pattern with Series Program → Resolves to specific episode at ScheduleDay time
- Pattern with Asset Program → Resolves to referenced asset at ScheduleDay time
- Pattern with Rule Program → Resolves to selected assets at ScheduleDay time
- Pattern creation does not resolve episodes → Valid (resolution deferred to ScheduleDay)

**Related Documentation:**
- [Pattern.md](../../domain/Pattern.md) - Program resolution
- [ScheduleDay.md](../../domain/ScheduleDay.md) - ScheduleDay resolution

**Entities:** Pattern, Program, ScheduleDay

---

## Test Coverage Requirements

Each contract (P-VAL-01 through P-BEH-02) MUST have corresponding test coverage that:

1. **Validates the contract holds** in normal operation
2. **Verifies violation detection** when the contract would be broken
3. **Confirms error handling** provides clear feedback
4. **Tests edge cases** and boundary conditions
5. **Validates domain-level validation** occurs at creation/update time

## Related Contracts

- [ZonesPatterns.md](../ZonesPatterns.md) - High-level Zones + Patterns behavioral contracts
- [SchedulePlanInvariantsContract.md](SchedulePlanInvariantsContract.md) - Cross-entity invariants for SchedulePlan
- [ZoneContract.md](ZoneContract.md) - Zone domain contracts (Patterns referenced by Zones)
- [ProgramContract.md](ProgramContract.md) - Program domain contracts (Programs reference Patterns)

## See Also

- [Domain: Pattern](../../domain/Pattern.md) - Complete Pattern domain documentation
- [Domain: SchedulePlan](../../domain/SchedulePlan.md) - SchedulePlan domain documentation
- [Domain: Zone](../../domain/Zone.md) - Zone domain documentation (references Patterns)
- [Domain: Program](../../domain/Program.md) - Program domain documentation (references Patterns)

---

**Note:** These contracts ensure that Pattern entities are correctly validated, managed, and expanded during schedule generation. All contracts prioritize early validation (domain-level), clear error messages, and deterministic behavior.


