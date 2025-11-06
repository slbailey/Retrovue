_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Asset](Asset.md) • [SchedulePlan](SchedulePlan.md) • [Program](Program.md) • [ScheduleDay](ScheduleDay.md) • [PlaylogEvent](PlaylogEvent.md)_

# Domain — VirtualAsset

**⚠️ FUTURE FEATURE — NOT MVP-CRITICAL**

This document describes a planned feature that is not part of the initial MVP release. This feature may be implemented in a future version of RetroVue.

## Purpose

VirtualAsset is a **reusable container of asset references and logic**. It enables packaging and re-use of modular asset bundles that can be referenced in scheduling and plan assignments. VirtualAssets may be referenced by Programs that appear inside Patterns; expansion still occurs during ScheduleDay generation. VirtualAssets are used during scheduling or in plan assignments, but **expand to actual assets at ScheduleDay (primary) or Playlog time (fallback)**.

**Example:** A VirtualAsset might define "intro + 2 random SpongeBob shorts" — a reusable container that combines a fixed intro asset with logic to select 2 random SpongeBob segments.

**Critical Rule:** VirtualAssets are **containers only — not assets themselves**. They are not broadcastable content. They are metadata structures that expand to concrete Asset references when resolved during schedule generation. VirtualAssets never appear in playout; only the expanded Asset references do.

**Key Characteristics:**
- **Reusable container**: A VirtualAsset is a reusable container of asset references and logic that can be used across multiple schedule plans
- **Asset references and logic**: Contains both direct asset references and logic for dynamic selection (e.g., rules, filters, selection criteria)
- **Cross-plan reuse**: Can be reused across multiple schedule plans, allowing operators to define once and use many times

VirtualAssets provide a way to:
- **Package asset sequences**: Create reusable bundles of assets (e.g., intro → clip → clip)
- **Define rule-based collections**: Specify dynamic asset selections (e.g., "intro + 2 random SpongeBob shorts")
- **Enable modular programming**: Reference complex asset combinations as a single unit in schedule plans
- **Support content reuse**: Define once, use many times across different plans and ScheduleDay entries
- **Support playout hints**: Include playout directives like shuffle, sequential, and conditional inserts (e.g., rating slates)

## Core Model / Scope

VirtualAsset enables:

- **Fixed sequences**: Predefined ordered lists of assets (e.g., branded intro → episode clip → outro bumper)
- **Rule-based definitions**: Dynamic asset selections based on rules (e.g., "3 random SpongeBob 11-min segments + branded intro")
- **Modular packaging**: Group related assets into reusable bundles
- **Scheduling abstraction**: Reference complex asset combinations as a single unit in [Program](Program.md) entries that appear inside Patterns
- **Runtime expansion**: Expand to actual Asset references at [ScheduleDay](ScheduleDay.md) or [PlaylogEvent](PlaylogEvent.md) resolution time

**Key Points:**
- VirtualAsset is a **reusable container of asset references and logic** (e.g., intro + 2 random SpongeBob shorts)
- Can be a fixed sequence (intro → clip → clip) or rule-based definition
- **Can be reused across multiple schedule plans** — define once, use many times
- Supports **playout hints** like shuffle, sequential, and conditional inserts (e.g., rating slates)
- Used during scheduling or in plan assignments
- Expands to actual assets at ScheduleDay or Playlog time
- Enables packaging and re-use of modular asset bundles

## Types of VirtualAssets

VirtualAssets come in two fundamental types, distinguished by how they expand to concrete assets:

### Fixed Sequence VirtualAsset

A **predefined ordered list of assets** that always plays in the same sequence. The expansion is deterministic — the same VirtualAsset always expands to the same sequence of assets in the same order.

**Expansion Behavior:**
- Fixed sequences expand to a predetermined list of Asset UUIDs
- The order is always preserved: first asset in sequence → second asset → third asset, etc.
- Each asset reference in the sequence must resolve to a valid Asset in the catalog
- Expansion happens at ScheduleDay time (preferred) or Playlog time (fallback)

**Example:** Branded intro → Episode clip → Outro bumper
- Intro asset: `branded-intro-2024.mp4` (fixed Asset UUID)
- Episode clip: Selected from series based on episode policy (may vary per expansion)
- Outro bumper: `station-outro.mp4` (fixed Asset UUID)

**Use Case:** Consistent branding and packaging for episodic content where the intro/outro remain constant but the main content varies. The structure is fixed, but some components may be selected dynamically.

### Rule-Based VirtualAsset

A **dynamic asset selection based on rules and constraints**. The expansion is non-deterministic — the same VirtualAsset may expand to different assets each time, based on current rules and available catalog content.

**Expansion Behavior:**
- Rule-based VirtualAssets evaluate their rules against the current asset catalog at expansion time
- Rules can specify selection criteria (genre, duration, series, freshness, etc.)
- Rules can specify ordering (random, chronological, least-recently-used, etc.)
- Rules can specify constraints (minimum/maximum duration, count limits, etc.)
- Expansion happens at ScheduleDay time (preferred) or Playlog time (fallback)
- Each expansion may produce different asset selections based on current catalog state

**Example:** "3 random SpongeBob 11-min segments + branded intro"
- Rule: Select 3 random assets from SpongeBob series
- Constraint: Each segment must be approximately 11 minutes (10-12 minute range)
- Fixed component: Branded intro plays first (always the same Asset UUID)
- Order: Intro → Random segment 1 → Random segment 2 → Random segment 3
- **Expansion Result (Day 1):** Intro → SpongeBob S03E12 → SpongeBob S02E08 → SpongeBob S04E05
- **Expansion Result (Day 2):** Intro → SpongeBob S01E15 → SpongeBob S05E03 → SpongeBob S02E20 (different selection)

**Use Case:** Flexible programming blocks where content selection varies but structure remains consistent. The structure and rules are fixed, but the actual asset selections change with each expansion.

## Contract / Interface

VirtualAsset defines:

- **Virtual asset identity**: Unique identifier for the virtual asset container
- **Type**: Fixed sequence or rule-based definition
- **Asset references**: For fixed sequences, ordered list of Asset UUIDs or selection rules
- **Rules**: For rule-based definitions, JSON rules specifying asset selection criteria
- **Playout hints**: Optional playout directives that control how assets are played:
  - `shuffle`: Randomize the order of assets in the container
  - `sequential`: Play assets in the defined order
  - `conditional_inserts`: Conditionally insert assets based on criteria (e.g., rating slates inserted before content based on rating)
- **Expansion behavior**: How the virtual asset expands to concrete assets during resolution
- **Reusability**: Can be referenced across multiple schedule plans

VirtualAssets are referenced in [Program](Program.md) entries using `content_type: "virtual_package"` and `content_ref` pointing to the VirtualAsset UUID. Programs appear inside Patterns within SchedulePlans. The same VirtualAsset can be referenced in multiple plans, enabling cross-plan reuse.

## Execution Model

VirtualAssets are used during scheduling but **expand to actual assets during resolution**. The expansion process converts VirtualAsset containers into concrete Asset references that can be scheduled and played.

### Expansion Flow

1. **Program Reference**: [Program](Program.md) entries inside Patterns reference a VirtualAsset using `content_type: "virtual_package"` and `content_ref: <virtual_asset_uuid>`
   - The Program contains the VirtualAsset reference, not the expanded assets
   - Programs appear inside Patterns within SchedulePlans
   - See [Program](Program.md) for details on how VirtualAssets are referenced in Programs

2. **Schedule Day Resolution** (Primary Expansion Point): When [ScheduleDay](ScheduleDay.md) is generated from the plan:
   - **VirtualAsset expansion occurs here** — VirtualAssets are resolved to concrete Asset references
   - **Fixed sequences**: Expand to the predetermined ordered list of Asset UUIDs
   - **Rule-based definitions**: Evaluate rules against the current asset catalog and expand to selected Asset UUIDs
   - Resolved assets are included in the ScheduleDay with their timing and sequencing
   - The ScheduleDay contains the actual Asset UUIDs, not the VirtualAsset reference
   - See [ScheduleDay](ScheduleDay.md) for details on schedule day resolution

3. **Playlog Generation**: When [PlaylogEvent](PlaylogEvent.md) records are generated from the ScheduleDay:
   - The resolved assets from the VirtualAsset (already expanded in ScheduleDay) are used
   - Each asset becomes a separate PlaylogEvent or segment within a PlaylogEvent
   - Timing and sequencing from the VirtualAsset expansion are preserved
   - See [PlaylogEvent](PlaylogEvent.md) for details on playlog event generation

### Expansion Timing

**Primary Expansion: ScheduleDay Time (3-4 days in advance)**
- VirtualAssets **preferentially expand** when [ScheduleDay](ScheduleDay.md) records are resolved from plans
- This happens 3-4 days before broadcast, providing advance resolution for EPG and planning
- VirtualAssets may be referenced by Programs that appear inside Patterns; expansion still occurs during ScheduleDay generation
- Fixed sequences expand deterministically to their predefined asset lists
- Rule-based VirtualAssets evaluate rules against the catalog state at ScheduleDay generation time
- The expanded Asset references are stored in the ScheduleDay, making it immutable and stable

**Fallback Expansion: Playlog Time (2-3 hours ahead)**
- If a VirtualAsset was not expanded during ScheduleDay resolution (e.g., late plan changes, manual overrides), expansion can occur during [PlaylogEvent](PlaylogEvent.md) generation
- This happens 2-3 hours before broadcast, as a fallback mechanism
- Rule-based VirtualAssets evaluate rules against the catalog state at Playlog generation time
- This ensures VirtualAssets can still be resolved even if ScheduleDay expansion was skipped

**Why ScheduleDay Time is Preferred:**
- Provides stable, immutable schedules for EPG systems
- Allows operators to preview and validate expanded content well in advance
- Enables better planning and conflict detection
- Supports audit trails and compliance requirements

## Relationship to Programs in Patterns

VirtualAssets are referenced in [Program](Program.md) entries using `content_type: "virtual_package"` and `content_ref` pointing to the VirtualAsset UUID. Programs appear inside Patterns within SchedulePlans. VirtualAssets may be referenced by Programs that appear inside Patterns; expansion still occurs during ScheduleDay generation.

**Key Points:**
- Programs contain the VirtualAsset reference, not the expanded assets
- The VirtualAsset is a reusable container that will be expanded later during ScheduleDay resolution
- Programs define what content should play, but not when (that's determined by Zones and Patterns)
- **Cross-plan reuse**: The same VirtualAsset can be referenced in multiple schedule plans, allowing operators to define once and use many times across different plans and ScheduleDay entries

## Relationship to ScheduleDay

When [ScheduleDay](ScheduleDay.md) is generated from a plan containing VirtualAsset references, **VirtualAssets expand to concrete Asset selections**. This is the primary expansion point.

**Expansion Process:**
- VirtualAssets are resolved to concrete Asset UUIDs during ScheduleDay generation
- Fixed sequences expand to their predetermined asset lists
- Rule-based VirtualAssets evaluate rules against the current catalog and expand to selected assets
- The resolved assets are included in the ScheduleDay with their timing and sequencing
- **ScheduleDay contains the actual Asset UUIDs, not the VirtualAsset reference**
- The VirtualAsset container disappears after expansion — only the expanded Asset references remain

See [ScheduleDay](ScheduleDay.md) for details on how schedule days are generated and how VirtualAsset expansion fits into the resolution process.

## Relationship to PlaylogEvent

When [PlaylogEvent](PlaylogEvent.md) records are generated from a ScheduleDay, **the resolved assets from VirtualAssets are used** (VirtualAssets are already expanded by this point).

**Playlog Generation:**
- The ScheduleDay contains already-expanded Asset UUIDs (VirtualAssets were expanded during ScheduleDay generation)
- Each expanded asset becomes a separate PlaylogEvent or segment within a PlaylogEvent
- Timing and sequencing from the VirtualAsset expansion are preserved in the playlog events
- **PlaylogEvents reference concrete Asset UUIDs, not VirtualAsset references**

**Fallback Expansion:**
- If a VirtualAsset was not expanded during ScheduleDay resolution (rare, e.g., late plan changes), expansion can occur during PlaylogEvent generation as a fallback
- This ensures VirtualAssets can still be resolved even if ScheduleDay expansion was skipped

See [PlaylogEvent](PlaylogEvent.md) for details on how playlog events are generated from schedule days.

## Examples

### Example 1: Fixed Sequence - Branded Episode Block

**VirtualAsset Definition:**
- Name: `branded-episode-block`
- Type: **Fixed sequence** (deterministic expansion)
- Sequence:
  1. Branded intro (`branded-intro-2024.mp4`) — fixed Asset UUID
  2. Episode (selected from series based on episode policy) — may vary per expansion
  3. Station bumper (`station-bumper.mp4`) — fixed Asset UUID

**Usage in [Program](Program.md) inside Pattern:**
```json
{
  "content_type": "virtual_package",
  "content_ref": "550e8400-e29b-41d4-a716-446655440000"
}
```

Note: Programs do not have `start_time`/`duration` — that's determined by Zones and Patterns.

**Expansion at ScheduleDay Time:**
When the [ScheduleDay](ScheduleDay.md) is generated 3-5 days in advance, the VirtualAsset expands:

- **Intro**: `asset-uuid-1` (branded-intro-2024.mp4) — always the same
- **Episode**: `asset-uuid-2` (Cheers S01E05, selected based on episode policy for this date)
- **Bumper**: `asset-uuid-3` (station-bumper.mp4) — always the same

The expanded assets are stored in the ScheduleDay. When [PlaylogEvent](PlaylogEvent.md) records are generated, they reference these already-expanded Asset UUIDs.

**Key Point:** The VirtualAsset container disappears after expansion. Only the concrete Asset references remain in the ScheduleDay and PlaylogEvent records.

### Example 2: Rule-Based - Morning Cartoon Block (Intro + 2 Random SpongeBob Shorts)

**VirtualAsset Definition:**
- Name: `morning-cartoon-block`
- Type: **Rule-based** (non-deterministic expansion)
- Description: **Reusable container** of asset references and logic — "intro + 2 random SpongeBob shorts"
- Rules:
  - Add branded intro at start (fixed Asset UUID)
  - Select 2 random SpongeBob segments from catalog
  - Each segment must be 10-12 minutes duration
  - Total duration: ~25 minutes
  - Avoid segments that aired in the last 7 days
- **Playout hints**: `shuffle` (randomize SpongeBob segment order)
- **Reusability**: Can be reused across multiple schedule plans (e.g., weekday morning plan, weekend morning plan)

**Usage in [Program](Program.md) inside Pattern:**
```json
{
  "content_type": "virtual_package",
  "content_reference": "660e8400-e29b-41d4-a716-446655440001",
  "start_time": "06:00",
  "duration": 45
}
```

**Expansion at ScheduleDay Time (Day 1):**
When the [ScheduleDay](ScheduleDay.md) is generated for Monday, the VirtualAsset expands:

- **Intro**: `asset-uuid-1` (branded-intro-2024.mp4) — always the same
- **Segment 1**: `asset-uuid-10` (SpongeBob S03E12, randomly selected, 11 min)
- **Segment 2**: `asset-uuid-15` (SpongeBob S02E08, randomly selected, 10 min)
- **Segment 3**: `asset-uuid-22` (SpongeBob S04E05, randomly selected, 12 min)

**Expansion at ScheduleDay Time (Day 2):**
When the [ScheduleDay](ScheduleDay.md) is generated for Tuesday, the VirtualAsset expands differently:

- **Intro**: `asset-uuid-1` (branded-intro-2024.mp4) — always the same
- **Segment 1**: `asset-uuid-18` (SpongeBob S01E15, randomly selected, 11 min) — different from Day 1
- **Segment 2**: `asset-uuid-25` (SpongeBob S05E03, randomly selected, 10 min) — different from Day 1
- **Segment 3**: `asset-uuid-31` (SpongeBob S02E20, randomly selected, 12 min) — different from Day 1

**Key Point:** The same VirtualAsset expands to different assets each day because it's rule-based. The rules are evaluated fresh against the catalog state at ScheduleDay generation time.

### Example 3: Fixed Sequence - Commercial Pod Structure

**VirtualAsset Definition:**
- Name: `prime-time-commercial-pod`
- Type: **Fixed sequence** (deterministic expansion)
- Sequence:
  1. Station ID bumper (`station-id-2024.mp4`) — fixed Asset UUID
  2. Commercial slot 1 (selected from ad library based on rotation policy)
  3. Commercial slot 2 (selected from ad library based on rotation policy)
  4. Commercial slot 3 (selected from ad library based on rotation policy)
  5. Return bumper (`return-bumper.mp4`) — fixed Asset UUID

**Usage in [Program](Program.md) inside Pattern:**
```json
{
  "content_type": "virtual_package",
  "content_reference": "770e8400-e29b-41d4-a716-446655440002",
  "start_time": "20:15",
  "duration": 3
}
```

**Expansion at ScheduleDay Time:**
The VirtualAsset expands to a fixed structure with some dynamic components:

- **Station ID**: `asset-uuid-100` (station-id-2024.mp4) — always the same
- **Commercial 1**: `asset-uuid-201` (selected from ad library rotation)
- **Commercial 2**: `asset-uuid-205` (selected from ad library rotation)
- **Commercial 3**: `asset-uuid-198` (selected from ad library rotation)
- **Return Bumper**: `asset-uuid-101` (return-bumper.mp4) — always the same

**Key Point:** Even though commercials are selected dynamically, the structure (bumper → 3 ads → bumper) is fixed. This is a fixed sequence with dynamic components.

### Example 4: Rule-Based - Late Night Movie Block

**VirtualAsset Definition:**
- Name: `late-night-movie-block`
- Type: **Rule-based** (non-deterministic expansion)
- Rules:
  - Select 1 random movie from "Classic Movies" collection
  - Duration must be 90-120 minutes
  - Add branded intro at start (fixed Asset UUID)
  - Add station outro at end (fixed Asset UUID)
  - Avoid movies that aired in the last 30 days
  - Prefer movies with "classic" genre tag

**Usage in [Program](Program.md) inside Pattern:**
```json
{
  "content_type": "virtual_package",
  "content_reference": "880e8400-e29b-41d4-a716-446655440003",
  "start_time": "22:00",
  "duration": 120
}
```

**Expansion at ScheduleDay Time (Day 1):**
- **Intro**: `asset-uuid-1` (branded-intro-2024.mp4) — always the same
- **Movie**: `asset-uuid-500` (Casablanca, 102 min, randomly selected from eligible movies)
- **Outro**: `asset-uuid-2` (station-outro.mp4) — always the same

**Expansion at ScheduleDay Time (Day 2):**
- **Intro**: `asset-uuid-1` (branded-intro-2024.mp4) — always the same
- **Movie**: `asset-uuid-523` (The Maltese Falcon, 100 min, randomly selected, different from Day 1)
- **Outro**: `asset-uuid-2` (station-outro.mp4) — always the same

**Key Point:** The structure (intro → movie → outro) is consistent, but the movie selection varies based on rules evaluated at expansion time.

### Example 5: Conditional Inserts - Rating Slates

**VirtualAsset Definition:**
- Name: `prime-time-block-with-rating-slates`
- Type: **Rule-based** (with conditional inserts)
- Description: **Reusable container** of asset references and logic with conditional inserts
- Rules:
  - Select 1 prime-time episode from eligible series
  - Duration must be 42-44 minutes
  - Add branded intro at start (fixed Asset UUID)
  - Add station outro at end (fixed Asset UUID)
- **Playout hints**: 
  - `sequential`: Play in defined order (intro → episode → outro)
  - `conditional_inserts`: Insert rating slate before episode if content rating is PG-13 or R
    - Rating slate asset: `pg13-rating-slate.mp4` (inserted if rating is PG-13)
    - Rating slate asset: `r-rating-slate.mp4` (inserted if rating is R)
- **Reusability**: Can be reused across multiple schedule plans (e.g., weekday prime-time plan, weekend prime-time plan)

**Usage in [Program](Program.md) inside Pattern:**
```json
{
  "content_type": "virtual_package",
  "content_reference": "990e8400-e29b-41d4-a716-446655440004",
  "start_time": "20:00",
  "duration": 45
}
```

**Expansion at ScheduleDay Time (Episode with PG-13 rating):**
- **Intro**: `asset-uuid-1` (branded-intro-2024.mp4) — always the same
- **Rating Slate**: `asset-uuid-300` (pg13-rating-slate.mp4) — conditionally inserted based on content rating
- **Episode**: `asset-uuid-600` (Drama Series S02E05, PG-13 rated, 43 min)
- **Outro**: `asset-uuid-2` (station-outro.mp4) — always the same

**Expansion at ScheduleDay Time (Episode with TV-PG rating):**
- **Intro**: `asset-uuid-1` (branded-intro-2024.mp4) — always the same
- **Episode**: `asset-uuid-605` (Comedy Series S01E12, TV-PG rated, 42 min) — no rating slate inserted
- **Outro**: `asset-uuid-2` (station-outro.mp4) — always the same

**Key Point:** Conditional inserts allow VirtualAssets to dynamically insert assets (like rating slates) based on content metadata or other criteria, while maintaining the reusable container structure across multiple schedule plans.

## Benefits

VirtualAssets provide several benefits:

1. **Reusability**: Define once, use many times across multiple schedule plans and ScheduleDay entries
2. **Modularity**: Package related assets into reusable bundles of asset references and logic
3. **Consistency**: Ensure consistent branding and packaging across programming
4. **Flexibility**: Support both fixed sequences and dynamic rule-based selections
5. **Playout control**: Support playout hints like shuffle, sequential, and conditional inserts (e.g., rating slates)
6. **Abstraction**: Reference complex asset combinations as a single unit in schedule plans
7. **Maintainability**: Update VirtualAsset definitions to affect all references across all plans

## Implementation Considerations

**Future Implementation Notes:**

- VirtualAssets will require a persistence model (table or JSON storage)
- Expansion logic will need to handle both fixed sequences and rule-based definitions
- Rule evaluation will need access to asset catalog for selection
- Timing calculations must account for variable-duration rule-based selections
- Validation must ensure VirtualAssets expand to valid Asset references
- **Playout hints support**: Implementation must support playout directives like shuffle, sequential, and conditional inserts (e.g., rating slates inserted based on content rating)
- **Cross-plan reuse**: VirtualAssets must be designed to be reusable across multiple schedule plans without duplication

## Out of Scope (MVP)

VirtualAssets are not part of the initial MVP release. The following are deferred:

- VirtualAsset persistence and management
- Fixed sequence VirtualAsset support
- Rule-based VirtualAsset support
- VirtualAsset expansion during ScheduleDay resolution
- VirtualAsset expansion during PlaylogEvent generation
- VirtualAsset CLI commands and operator workflows

## See Also

- [Asset](Asset.md) - Atomic unit of broadcastable content (what VirtualAssets contain)
- [SchedulePlan](SchedulePlan.md) - Top-level operator-created plans that define channel programming
- [Program](Program.md) - Catalog entities in Patterns (can reference VirtualAssets)
- [ScheduleDay](ScheduleDay.md) - Resolved schedules for specific channel and date (VirtualAssets expand here)
- [PlaylogEvent](PlaylogEvent.md) - Generated playout events (uses resolved assets from VirtualAssets)
- [Scheduling](Scheduling.md) - High-level scheduling system

**Note:** VirtualAsset is a future feature that enables packaging and re-use of modular asset bundles. A VirtualAsset is a reusable container of asset references and logic (e.g., intro + 2 random SpongeBob shorts) that can be reused across multiple schedule plans. VirtualAssets support playout hints like shuffle, sequential, and conditional inserts (e.g., rating slates). VirtualAssets are containers only — not assets themselves. They are used during scheduling or in plan assignments, but expand to actual assets at ScheduleDay time (preferred, 3-5 days in advance) or Playlog time (fallback, 2-3 hours ahead). After expansion, only the concrete Asset references remain in ScheduleDay and PlaylogEvent records.

