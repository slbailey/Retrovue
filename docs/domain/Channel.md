_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Contracts](../contracts/README.md) • [ScheduleTemplate](ScheduleTemplate.md)_

# Domain — Channel

## Purpose

Define the canonical, persisted Channel entity: the time root for schedule template interpretation and horizon building.

## Persistence model

Each field is persisted and scheduling-centric:

- **id (UUID)** — primary key.
- **slug (str, unique)** — lowercase kebab-case machine id, immutable after creation.
- **title (str)** — operator-facing name.
- **timezone (IANA string)** — the station clock (all schedule math interprets in this zone).
- **grid_block_minutes (int)** — base grid size; allowed: 15, 30, or 60.
- **kind (str)** — lightweight label; `network` | `premium` | `specialty` (non-functional in v0.1).
- **programming_day_start (time)** — e.g., `06:00:00`; daypart anchor.
- **block_start_offsets_minutes (json array[int])** — allowed minute offsets within the hour (e.g., `[0,30]`, `[5,35]`).
- **is_active (bool)** — included in horizon builders when true.
- **created_at / updated_at (timestamps)** — audit fields.

## Scheduling model

- All dayparts and templates are channel-scoped and interpreted in `timezone`, anchored to `programming_day_start`.
- Block starts must align to the channel's allowed offsets; durations are expressed in grid blocks (not minutes).

## Interaction & lifecycle

Operators manage Channels through standard CRUD-like actions:

- Create, update, list, show, validate
- Archive via `is_active=false`
- Delete (only allowed if no dependencies reference the channel)

## Invariants (summary)

- **slug** is unique and immutable after creation.
- **grid_block_minutes ∈ {15,30,60}**.
- **block_start_offsets_minutes** is sorted, unique, values in `0–59`; gaps’ gcd equals `grid_block_minutes`.
- **horizon builders exclude** channels where `is_active=false`.

## Out of scope (v0.1)

Branding, overlays, content ratings, ad/avail policy, guide playout specifics.
