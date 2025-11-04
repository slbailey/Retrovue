# Contract — Channel CLI v0.1

## Scope

Minimal CLI behavior aligned to Channel/Template contracts.

## Global semantics

Exit codes: `0` = OK, `1` = validation/unknown error, `2` = validation errors (validate), `4` = not found.

## Commands & rules

### channel add

- Inputs: `slug`, `title`, `timezone`, `grid_block_minutes`, `kind`, `programming_day_start`, `block_start_offsets_minutes`.
- Enforce:
  - Unique + immutable `slug` (on create)
  - Valid IANA `timezone`
  - `grid_block_minutes ∈ {15,30,60}`
  - Offsets domain (`0..59`, sorted, unique) and `gcd(gaps) == grid_block_minutes`
  - Valid `programming_day_start` time
- Exit codes: `0` success, `1` validation error

### channel update

- Inputs: any mutable field(s).
- Disallow changing `slug`. Revalidate TZ/grid/offsets/time.
- If `grid_block_minutes` changes and the channel has active/effective templates, print a warning to revalidate templates.
- Exit codes: `0` success, `1` validation error, `4` not found

### channel list

- Optional filters: `--active`/`--inactive`, `--kind <value>`, `--prefix <slug-prefix>`.
- Outputs compact table; `--json` returns array of objects.
- Exit codes: `0` success

### channel delete

- If dependencies (templates/schedules) exist → archive (`is_active=false`) and inform user.
- Only physically delete when no dependencies (future `--force` can be introduced; not in v0.1).
- Exit codes: `0` success, `4` not found, `1` error

### channel show <slug> [--json]

- Output fields: `slug`, `title`, `is_active`, `timezone`, `kind`, `programming_day_start`, `grid_block_minutes`, `block_start_offsets_minutes`.
- Computed preview (read-only): gaps, gcd, and 4 upcoming block starts in channel timezone (DST-safe).
- Exit codes: `0` OK, `4` Not found, `1` error

### channel validate [--slug <slug>] [--json] [--strict]

- Validates rules 1–7 from Channel v0.1.
- Summary + per-channel diagnostics; `--strict` treats warnings as errors.
- Exit codes: `0` all OK, `2` errors (or warnings with `--strict`), `4` not found, `1` error

## Required tests (CLI contract placeholders)

(Add later under `tests/contracts/_ops/` when CLI is implemented.)

## Out of scope

Clone, export/import, scheduler integration, runtime effects.

## References

- Contract: [Channel](../domain/ChannelContract.md)
- Contract: [ScheduleTemplate Binding](../domain/ScheduleTemplateBinding.md)
- Domain: [Channel](../../domain/Channel.md)


