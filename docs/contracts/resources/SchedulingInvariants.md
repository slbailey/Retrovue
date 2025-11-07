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

