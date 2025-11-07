# Scheduling Invariants (Plans • Zones • Patterns • ScheduleDay)

_Status: Enforced_

**Scope:** Applies to SchedulePlan, Zone, Pattern, Program (catalog), ScheduleDay, PlaylogEvent, AsRunLog.

## Core Invariants

**S-INV-01: Zone Non-Overlap (per plan)**

- After grid normalization, Zones in the same plan must not overlap when active day filters are applied.
- Touching boundaries (end == start) are allowed.

**S-INV-02: Grid Alignment**

- All Zone boundaries snap to the channel grid (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`).

**S-INV-03: Pattern Is Durationless**

- Patterns contain ordered Program references only (no durations). The engine repeats the Pattern to fill the Zone.

**S-INV-04: Episode Resolution Timing**

- Program → episode resolution occurs at **ScheduleDay** build time, using the Program's rotation policy (`sequential`, `random`, `lru`).

**S-INV-05: Plan Resolution & Layering**

- Active plan set for a channel/date: `is_active=true` ∧ (date in `[start_date,end_date]` if present) ∧ (cron matches day-of-week/month; hour/minute ignored).
- If multiple match, pick highest `priority`. Tie-breaker is deterministic (`created_at` asc, then `id` asc).

**S-INV-06: Zone Transition (Soft-Start-After-Current)**

- If a Zone opens while content is playing, finish current program; start the new Zone's Pattern at the next grid boundary following the current program's natural end (no mid-longform cuts).

**S-INV-07: Viewer Join**

- On viewer join, playout starts at the **beginning of the current grid block**.

**S-INV-08: ScheduleDay Immutability**

- ScheduleDay rows are immutable once generated. Manual changes create a new row or an override; history is preserved.

**S-INV-09: Asset Eligibility**

- Only assets with `state='ready'` and `approved_for_broadcast=true` are eligible.

**S-INV-10: Gaps Allowed, Warned**

- Gaps are permitted (not an invariant violation) but must surface as warnings in validation/preview.

**S-INV-11: Horizons**

- **EPG horizon:** ScheduleDays resolved **2–3 days** ahead.  
- **Playlog horizon:** PlaylogEvents continuously extended **~3–4 hours** ahead.

**S-INV-12: Longform Integrity**

- No mid-longform cuts due to Zone end; respect fixed zone end and carry-in rules (finish current item, then snap to next block).

**S-INV-13: Validation & Atomicity**

- All plan/zone/pattern mutations use shared domain validators and run in a single transaction (rollback on failure).

**S-INV-14: Plan Must Have Full Coverage (INV_PLAN_MUST_HAVE_FULL_COVERAGE)**

- A SchedulePlan must contain one or more Zones whose combined coverage spans 00:00–24:00 with no gaps.
- When a plan is created without explicit zones, the system automatically initializes it with a default "test pattern" zone covering the full 24-hour period (00:00–24:00).
- This invariant ensures that every plan provides complete daily coverage, preventing runtime gaps where no content is scheduled.
- Validation occurs on plan creation and on any update that modifies zones (save/update operations enforce this invariant unless in developer debug mode).

## Rationale: Why Blank Plans Are Disallowed

Blank plans (plans without zones or with coverage gaps) are disallowed for runtime because the scheduling engine requires continuous coverage to generate valid ScheduleDays. Without full 24-hour coverage, the engine cannot determine what content to play during uncovered time periods, leading to runtime errors or undefined behavior. The default "test pattern" zone ensures new plans are immediately usable while allowing operators to replace it with actual programming zones.

## Validation Examples

The following examples demonstrate valid and invalid plans according to INV_PLAN_MUST_HAVE_FULL_COVERAGE (S-INV-14):

### Example 1: Valid Plan with Single Full-Day Test Pattern Zone

**Plan:** `WeekdayPlan`

**Zones:**
- `Base` (00:00–24:00) — Default test pattern zone

**Validation Result:** ✅ **Valid** — Single zone provides complete 24-hour coverage with no gaps.

**Note:** This is the default state when a plan is created without explicit zones. The system automatically initializes the plan with this test pattern zone.

### Example 2: Valid Plan with Multiple Sequential Zones

**Plan:** `PrimeTimePlan`

**Zones:**
- `Morning` (00:00–12:00) — Morning programming
- `Afternoon` (12:00–19:00) — Afternoon programming
- `Prime Time` (19:00–22:00) — Prime time programming
- `Late Night` (22:00–24:00) — Late night programming

**Validation Result:** ✅ **Valid** — Multiple zones provide complete 24-hour coverage with no gaps. Zone boundaries touch (e.g., Morning ends at 12:00, Afternoon starts at 12:00), which is allowed.

### Example 3: Invalid Plan with Coverage Gap

**Plan:** `IncompletePlan`

**Zones:**
- `Morning` (00:00–12:00) — Morning programming
- `Afternoon` (12:00–19:00) — Afternoon programming
- `Prime Time` (19:00–22:00) — Prime time programming
- **Missing:** No zone covering 22:00–24:00

**Validation Result:** ❌ **Invalid** — Plan has a coverage gap from 22:00–24:00. The scheduling engine cannot determine what content to play during this period, violating INV_PLAN_MUST_HAVE_FULL_COVERAGE.

**Error Message:** `Error Code E-INV-14: Coverage Invariant Violation — Plan no longer covers 00:00–24:00. Suggested Fix: Add a zone covering the missing range or enable default test pattern seeding.`

**Resolution:** Add a zone covering 22:00–24:00, or extend an existing zone to cover the gap.

## Outdated/Removed Concepts

- ❌ Program-level `start_time`/`duration` inside plans  
- ❌ ScheduleTemplate/TemplateBlock  
- ✅ Use **ScheduleDay** (not "BroadcastScheduleDay") and **PlaylogEvent**

## Test Coverage Requirements

- Zone overlap rejection after grid normalization
- Deterministic plan selection (priority and tie-breaks)
- Pattern repetition fills zone; no durations present
- Rotation policies honored at ScheduleDay build
- Soft-start-after-current at Zone boundary
- Viewer join at start-of-block
- ScheduleDay immutability & override behavior
- Eligibility filter excludes non-ready/non-approved assets
- EPG/Playlog horizon behavior
- Plan full coverage validation (00:00–24:00 with no gaps)

## See Also

- [SchedulePlan Domain](../../domain/SchedulePlan.md)
- [Zone Domain](../../domain/Zone.md)
- [Pattern Domain](../../domain/Pattern.md)
- [ScheduleDay Domain](../../domain/ScheduleDay.md)
- [SchedulePlan Contract](SchedulePlanContract.md)
- [SchedulePlan Add Contract](SchedulePlanAddContract.md)
- [SchedulePlan List Contract](SchedulePlanListContract.md)
- [SchedulePlan Show Contract](SchedulePlanShowContract.md)
- [SchedulePlan Update Contract](SchedulePlanUpdateContract.md)
- [SchedulePlan Delete Contract](SchedulePlanDeleteContract.md)

## Referenced By

- [SchedulePlanAddContract.md](SchedulePlanAddContract.md)
- [SchedulePlanUpdateContract.md](SchedulePlanUpdateContract.md)
- [SchedulePlanShowContract.md](SchedulePlanShowContract.md)
- [SchedulePlanListContract.md](SchedulePlanListContract.md)

