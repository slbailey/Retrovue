_Related: [Architecture](../overview/architecture.md) • [Contracts](../contracts/README.md) • [ScheduleTemplate](ScheduleTemplate.md)_

# Domain — Channel

## Purpose

Define the canonical, persisted Channel entity. Channel is the time root for interpreting
schedule templates and building programming horizons in a specific IANA timezone.

## Persistence model

Scheduling-centric fields persisted on Channel:

- **id (UUID)** — primary key
- **slug (str, unique)** — lowercase kebab-case machine id; immutable post-create
- **title (str)** — operator-facing label
- **timezone (IANA string)** — station clock; all schedule math interprets in this zone
- **grid_block_minutes (int)** — base grid size; allowed: 15, 30, or 60
- **kind (str)** — lightweight label; `network` | `premium` | `specialty` (non-functional in v0.1)
- **programming_day_start (time)** — e.g., `06:00:00`; daypart anchor
- **block_start_offsets_minutes (json array[int])** — allowed minute offsets within the hour
  (e.g., `[0,30]`, `[5,35]`)
- **is_active (bool)** — included in horizon builders when true
- **created_at / updated_at (timestamps)** — audit fields (UTC)
- **version (int)** — optional optimistic-locking counter for concurrent updates

Constraints (guardrails):

- `title` max length ≤ 120 characters; `slug` max length ≤ 64 characters.

Naming rules:

- `slug` is lowercase, kebab-case (`a-z0-9-`), and never changes after creation.

## Contract / interface

- Channel provides the temporal context for:
  - interpreting `ScheduleTemplate` dayparts and `block_slots` in `timezone`,
  - validating block alignment against `block_start_offsets_minutes`,
  - grid math using `grid_block_minutes`,
  - computing programming day boundaries anchored by `programming_day_start`.
- Horizon builders and EPG generation consult only Channels where `is_active=true`.
- CLI/Usecases expose CRUD-like operations; deletions require no dependent references.
- A system-level `validateChannel(channelId)` use case recomputes and reports all invariant
  violations across dependent `ScheduleTemplate` and `ScheduleDay` assignments.

## Scheduling model

- All dayparts and templates are channel-scoped and interpreted in `timezone`, anchored to
  `programming_day_start`.
- Block starts must align to the channel's allowed offsets; durations are expressed in grid
  blocks (not minutes).

### Time and calendar semantics

- Dayparts and blocks are computed in the channel's IANA timezone using timezone-aware
  arithmetic. All conversions MUST handle non-existent and ambiguous local times during DST
  transitions (spring-forward and fall-back).
- Programming days are anchored to `programming_day_start` in local time. A block belongs to
  the programming day whose anchor is the most recent at-or-before the block's start
  timestamp (in channel local time), even when the block crosses wall-clock midnight.
- On DST transitions, programming days may contain 23 or 25 wall-clock hours. Block math is
  still derived from grid counts; do not assume 60-minute hours. Ambiguous/non-existent local
  times must be disambiguated via timezone rules, not naive offsets.
- Systems MAY cache resolved UTC offsets per date for performance, but MUST invalidate caches
  when tzdata (IANA database) updates are detected.

### Effective-dated changes

- Timezone changes: post-create, timezone edits MUST be effective-dated. No retroactive
  reinterpretation of historical horizons; force a full horizon/EPG rebuild starting at the
  effective date.
- Programming-day anchor (`programming_day_start`) changes: MUST be effective-dated and trigger
  dependent rebuilds from that date forward; prevent silent reassignment of historical blocks.

## Operator workflows

Operators manage Channels via standard workflows:

- Create, update, list, show, validate
- Archive via `is_active=false`
- Delete (only if no dependencies reference the channel)

### Lifecycle and referential integrity

- `is_active=false` archives the channel for prospective operations: horizon builders and EPG
  generation exclude the channel going forward. Already-materialized horizons/EPG rows are not
  retroactively deleted; operators may trigger rebuilds if policy requires.
- Hard delete is only permitted when no dependent rows exist (e.g., `ScheduleTemplate`,
  `ScheduleDay`, EPG rows, playout configurations). When dependencies exist, prefer archival
  (`is_active=false`). The delete path MUST verify the absence of these references.
  The dependency preflight MUST cover: `ScheduleTemplate`, `ScheduleDay`, EPG rows, playout
  pipelines/configs, broadcast bindings, and ad/avail policies (when present).

## Validation & invariants

- **Slug immutability**: `slug` is unique and immutable post-creation.
- **Grid size**: `grid_block_minutes ∈ {15,30,60}`.
- **Offsets validity**: `block_start_offsets_minutes` is sorted, unique, values in `0–59`.
- **Grid alignment (chosen rule)**: every offset satisfies `offset % grid_block_minutes == 0`.
- **Programming day start alignment**: `programming_day_start.minute % grid_block_minutes == 0`
  and `programming_day_start.minute ∈ block_start_offsets_minutes`.
- **Second alignment**: All starts are minute-precision; seconds MUST equal `00`.
- **Activity filter**: horizon builders exclude channels where `is_active=false`.

Offset set shape:

- Require `1 ≤ len(block_start_offsets_minutes) ≤ 6`.
- Require monotone hourly repeatability: the same set of allowed offsets applies to every
  hour uniformly.

Validation guidelines:

- Reject templates or blocks that violate offset/grid rules for the channel.
- Changing `grid_block_minutes` or `block_start_offsets_minutes` requires revalidation of
  existing `ScheduleTemplate` and `ScheduleDay` assignments; consider a temporary
  "pending-change" state with migration aids (diffs and fix-up suggestions).

### Input validation surface

- Timezone MUST be validated against a known IANA set at write-time; reject `Etc/GMT±N` and
  other footguns.
- `kind` is a forward-compatible enum; unknown values fail closed.
- Title and slug constraints: enforce lowercase kebab-case for `slug` at write-time, maximum
  lengths, reserved words, and normalization; reject on violation.
- Audit timestamps are stored as UTC; define whether DB triggers or application code sets
  `created_at`/`updated_at` consistently.

## Out of scope (v0.1)

Branding, overlays, content ratings, ad/avail policy, guide playout specifics.

## Scheduling policy clarifications

- Durations are specified in grid blocks. When mapping content to blocks:
  - If content runtime is shorter than allocated blocks, any underfill is handled per
    template rules (e.g., `allow_underfill`) and finalized during playlog building.
  - Overflow beyond allocated block count is not permitted; adjust the template or block
    allocation.
- Horizon window: default look-ahead and look-behind windows are implementation-defined (e.g.,
  14 days ahead, 1 day behind). Rebuild triggers include channel field changes (grid, offsets,
  timezone, programming_day_start), tzdata updates, template edits, and content substitutions.

## Concurrency & operations

- Use optimistic locking for updates (e.g., `version` or `updated_at` precondition) to avoid
  last-write-wins overwrites.
- When flipping `is_active` from false to true, the system SHOULD backfill missing
  horizons/EPG for the standard window.

Version semantics:

- Updates MUST include the current `version` precondition and fail if it does not match the
  persisted value; on success increment `version` by 1 (never resets).
- Define the system of record for increments (DB trigger vs application layer) and apply it
  consistently.

## Validator entrypoint

- `validateChannel(channelId)` recomputes invariants and cross-validates dependent
  `ScheduleTemplate`/`ScheduleDay` for block alignment and timezone policies. If
  `grid_block_minutes`/offsets change, mark all dependents as `needs-review`.
  When validation flags `needs-review` or violations, emit a typed observability event such as
  `channel.validation.failed` for job runners/ops workflows.

## Lint rules (non-fatal warnings)

- Warn if `grid_block_minutes=60` but `block_start_offsets_minutes` contains non-zero values.
- Warn if offsets are "sparse" or unusual (e.g., only `[47]`).

## API guardrails (non-binding domain guidance)

- Channel list responses SHOULD support pagination to avoid large unbounded payloads.

## See also

- [ScheduleTemplate](ScheduleTemplate.md) — Reusable programming templates per channel
- [ScheduleDay](ScheduleDay.md) — Template assignments for specific dates
- [Scheduling](Scheduling.md) — Planning-time logic for future air
- [EPGGeneration](EPGGeneration.md) — Electronic Program Guide generation
