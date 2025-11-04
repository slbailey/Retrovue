_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Contracts](../contracts/README.md) • [Channel](Channel.md)_

# Domain — ScheduleTemplate

## Purpose

Reusable, channel-specific plan for EPG layout and inputs to playlog building.

## Persistence model

- **id (UUID)**
- **channel_id (UUID, FK Channel.id)** — required
- **name (str)**
- **version (int)** — increment on material change
- **daypart_rules (json)** — array of `{name, start_time, end_time}` in channel timezone
- **block_slots (json)** — ordered slots per daypart; each has:
  - **program_ref** (slug or external selector)
  - **duration_blocks** (int ≥1, multiples of channel grid_block_minutes)
  - **allow_underfill** (bool, default false)
  - **notes** (optional)
- **starts_on / ends_on (date|null)**
- **is_active (bool)**
- **created_at / updated_at**

## Scheduling model

- Exactly one effective active template per channel at a given instant (considering date windows).
- Underfill deltas (when allowed) are computed during playlog building.

## Out of scope (v0.1)

Program selection heuristics, ad pod composition, overlay timing.
