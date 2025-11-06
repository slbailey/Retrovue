_Related: [Architecture](../architecture/ArchitectureOverview.md) • [SchedulePlan](SchedulePlan.md) • [ScheduleDay](ScheduleDay.md) • [VirtualAsset](VirtualAsset.md) • [Operator CLI](../operator/CLI.md)_

# Domain — Program

## Purpose

Program is a **catalog entity** that describes how to resolve content, not a per-day time-slot assignment. Programs are referenced by Patterns within SchedulePlans and define content selection rules, rotation policies, and resolution behavior.

**What a Program is:**

- A catalog entity (series/movie/block/composite) that describes how to resolve content
- Defines resolution rules such as:
  - **Rotation policy**: How to select episodes/content (random, sequential, LRU, seasonal, etc.)
  - **commType**: Commercial type/break behavior
  - **slot_units**: Override for longform content that needs multiple grid blocks (e.g., a 2-hour movie on a 30-minute grid requires `slot_units=4`)

**What a Program is not:**

- A row with `start_time`/`duration` inside the plan (that's now Zone+Pattern)
- A per-day time-slot assignment
- A time-specific placement

Programs are catalog entries referenced by Patterns. The Zone defines when the Pattern applies, and the Pattern defines the sequence of Programs. The plan engine repeats Patterns over Zones until Zones are full, snapping to the Channel's Grid boundaries. At ScheduleDay time, each Program slot resolves to specific assets/episodes.

## Core Model / Scope

Program enables:

- **Catalog entity definition**: Programs define series/movie/block/composite entities with resolution rules
- **Content resolution rules**: Specify how content should be resolved (rotation policy, commType, slot_units)
- **Pattern references**: Programs are referenced by Patterns in ordered sequences
- **Operator intent capture**: Store metadata about programming intent (e.g., "Play Cheers seasonally")
- **VirtualAsset references**: Programs can reference VirtualAssets for packaging (e.g., "intro + episode + outro")

**Key Points:**

- Program is a **catalog entity**, not a per-day time-slot
- Programs define **how to resolve content** (rotation, commType, slot_units), not when it airs
- Programs are **referenced by Patterns** — the Zone defines when, the Pattern defines sequence
- **Resolution at ScheduleDay time**: Each Program slot resolves to specific assets/episodes when ScheduleDay is generated
- **No time placement**: Programs do not have `start_time`/`duration` — that's Zone+Pattern
- **Longform support**: `slot_units` override allows longform content to consume multiple grid blocks
- **VirtualAsset expansion**: VirtualAssets expand at ScheduleDay time, not at plan definition time

## Persistence Model

Program is managed by SQLAlchemy with the following fields:

- **id** (UUID, primary key): Unique identifier for relational joins and foreign key references
- **channel_id** (UUID, required, foreign key): Reference to Channel - the channel this program applies to
- **plan_id** (UUID, required, foreign key): Reference to parent SchedulePlan
- **pattern_id** (UUID, required, foreign key): Reference to Pattern within the SchedulePlan
- **order** (Integer, required): Order within the Pattern (determines sequence when Pattern repeats)
- **content_type** (Text, required): Type of content selection - one of: "series", "asset", "rule", "random", "virtual_package"
- **content_ref** (Text, required): Reference to the content:
  - For "series": Series identifier or UUID
  - For "asset": Asset UUID
  - For "rule": Rule JSON (e.g., "random family movie under 2 hours")
  - For "random": Random selection rule JSON
  - For "virtual_package": [VirtualAsset](VirtualAsset.md) UUID
- **episode_policy** (Text, optional): Episode selection policy for series content (rotation policy) - one of: "sequential", "syndication", "random", "least-recently-used", "seasonal"
- **playback_rules** (JSON, optional): Additional playback rules, constraints, and playout directives (e.g., `rotation`, `commType`, `slot_units`, `offset`, chronological order, freshness requirements)
- **slot_units** (Integer, optional): Override for longform content that needs multiple grid blocks (e.g., a 2-hour movie on a 30-minute grid requires `slot_units=4`). If not specified, content duration determines block consumption.
- **commType** (Text, optional): Commercial type/break behavior for this Program
- **operator_intent** (Text, optional): Operator-defined metadata describing programming intent (e.g., "Play Cheers seasonally", "Rotate through classic movies", "Fill with family-friendly content")
- **created_at** (DateTime(timezone=True), required): Record creation timestamp
- **updated_at** (DateTime(timezone=True), required): Record last modification timestamp

**Note:** Programs are catalog entities and do not have `start_time` or `duration` fields. The Zone defines when the Pattern applies, and the Pattern defines the sequence of Program references. The plan engine repeats Patterns over Zones until Zones are full, snapping to the Channel's Grid boundaries.

### Table Name

The table is named `programs` (plural). Schema migration is handled through Alembic. Postgres is the authoritative backing store.

### Constraints

- `order` must be a non-negative integer (determines sequence within Pattern)
- `content_type` must be one of: "series", "asset", "rule", "random", "virtual_package"
- `channel_id` must reference a valid Channel
- `plan_id` must reference a valid SchedulePlan
- `pattern_id` must reference a valid Pattern within the SchedulePlan

## Contract / Interface

Program is a catalog entry (schedulable entity) in a Pattern. It defines:

- **Channel assignment** (channel_id) - the channel this program applies to
- **Plan membership** (plan_id) - the SchedulePlan this program belongs to
- **Pattern membership** (pattern_id) - the Pattern this program belongs to
- **Order within Pattern** (order) - determines sequence when Pattern repeats over Zone
- **Content selection** (content_type, content_ref) - what content should air: specific asset, [VirtualAsset](VirtualAsset.md) UUID, or random/filtered selection from a set of assets
- **Playout directives** (episode_policy, playback_rules) - optional directives controlling how content is selected and played (e.g., `sequential`, `random`, `offset`, chronological order, seasonal selection)
- **Operator intent** (operator_intent) - metadata describing programming goals and constraints

Programs are catalog entries in Patterns. They do not specify "when" content should air — that is determined by the Zone's time window and the Pattern's position within the Zone. The plan engine repeats the Pattern over the Zone until the Zone is full, snapping to the Channel's Grid boundaries.

## Pattern and Zone Model

**Programs in Patterns:** Programs are catalog entries ordered within Patterns. They do not have durations in the Pattern context — durations are determined by the content itself.

**Pattern Repeating:** The plan engine:

1. Takes the ordered list of Programs from the Pattern
2. Repeats the Pattern over the Zone's time window
3. Snaps to the Channel's Grid boundaries (`grid_block_minutes`, `block_start_offsets_minutes`, `programming_day_start`)
4. Continues until the Zone is full

**Zone Time Windows:** Zones declare when they apply (e.g., base 00:00–24:00, or After Dark 22:00–05:00). The Zone's time window determines when the Pattern applies, not individual Programs.

**Time Resolution:** When a SchedulePlan is resolved into a [ScheduleDay](ScheduleDay.md), the Zone's time window and the Pattern's repeating behavior are combined with the channel's Grid boundaries to produce real-world wall-clock times. Programs are expanded to concrete episodes and VirtualAssets are expanded to real assets at ScheduleDay time.

## Content Selection Model

Program supports multiple content selection approaches, all defined as catalog entities with resolution rules:

1. **Series**: Reference a series with rotation policy (e.g., sequential, random, LRU, seasonal)
2. **Asset**: Reference a specific asset directly (useful for one-off content like specials or movies)
3. **VirtualAsset**: Reference a [VirtualAsset](VirtualAsset.md) container for packaging (e.g., "intro + episode + outro")
4. **Random/Filtered Selection**: Instruct the system to pick at random from a set of filtered assets based on rules

The following content selection types are supported:

### Series Programs

A series Program defines how to select episodes from a series catalog:

```json
{
  "content_type": "series",
  "content_ref": "Cheers",
  "episode_policy": "seasonal",
  "playback_rules": {
    "rotation": "least-recently-used",
    "avoid_repeats": true
  },
  "operator_intent": "Play Cheers seasonally"
}
```

**Rotation Policies (episode_policy):**

- `sequential`: Play episodes in sequential order (S01E01, S01E02, ...)
- `syndication`: Play episodes in syndication order
- `random`: Random episode selection
- `seasonal`: Play episodes appropriate for the current season
- `least-recently-used` (LRU): Select episodes that haven't aired recently

**Additional Resolution Rules (via playback_rules JSON):**

- `rotation`: Override rotation policy (random, sequential, LRU, etc.)
- `avoid_repeats`: Avoid content that has aired recently
- `prefer_new`: Prefer recently added content
- `freshness`: Require content within a certain age range
- `offset`: Start playback at a specific offset within the asset

### Asset Programs

A specific asset Program references a single asset directly:

```json
{
  "content_type": "asset",
  "content_ref": "550e8400-e29b-41d4-a716-446655440000",
  "slot_units": 2
}
```

Useful for one-off content like specials or movies. The `slot_units` field can override block consumption for longform content.

### VirtualAsset Programs

A VirtualAsset Program references a [VirtualAsset](VirtualAsset.md) container for packaging:

```json
{
  "content_type": "virtual_package",
  "content_ref": "550e8400-e29b-41d4-a716-446655440000",
  "operator_intent": "Intro + episode + outro packaging"
}
```

VirtualAssets expand to multiple assets at ScheduleDay time (e.g., "intro + episode + outro" becomes three separate assets in sequence). The `content_ref` must be a valid VirtualAsset UUID.

### Rule Programs (Filtered Selection)

A rule Program uses content selection rules to filter and select assets:

```json
{
  "content_type": "rule",
  "content_ref": "{\"genre\": \"family\", \"max_duration\": 120, \"rating\": \"PG\"}",
  "playback_rules": {
    "rotation": "random",
    "avoid_repeats": true
  }
}
```

The system picks from the filtered set based on the rotation policy in `playback_rules`.

## Execution Model

Programs are consumed during schedule generation:

1. **Plan Resolution**: ScheduleService identifies active SchedulePlans for a channel and date
2. **Layering Resolution**: When multiple plans match the same date, plans are layered by priority. Higher-priority plans override lower-priority plans. Zones from higher-priority plans supersede overlapping Zones from lower-priority plans (e.g., a ChristmasDay plan with priority 20 overrides a WeekdayPlan with priority 10)
3. **Zone and Pattern Resolution**: For each active plan, identify its Zones (time windows) and their associated Patterns (ordered lists of Programs)
4. **Pattern Repeating**: The plan engine repeats each Pattern over its Zone until the Zone is full, snapping to the Channel's Grid boundaries
5. **Content Resolution**: Content references are resolved to specific assets based on content_type and playback rules. This happens at ScheduleDay time, which is the primary expansion point for Programs → episodes and VirtualAssets → assets
6. **ScheduleDay Generation**: Resolved Zones, Patterns, and Programs are used to create [BroadcastScheduleDay](ScheduleDay.md) records (resolved 3-4 days in advance)
7. **PlaylogEvent Generation**: ScheduleDays are used to generate [BroadcastPlaylogEvent](PlaylogEvent.md) records for playout

**Critical Rule:** Program is a catalog entry in a Pattern. The scheduler uses Programs within Patterns to determine content selections. Timing is determined by the Zone's time window and the Pattern's repeating behavior, not by individual Programs.

**Layering Behavior:** When multiple SchedulePlans are active for the same date, they are layered by priority. Lower-priority Zones are superseded by more specific ones. For example, a generic weekday plan (priority 10) might define a Zone for 06:00–24:00, but a ChristmasDay plan (priority 20) can override specific time windows (e.g., 19:00–22:00) with holiday-specific Zones and Patterns. The higher-priority plan's Zones take precedence for overlapping time periods.

## Relationship to ScheduleDay

Programs flow into [ScheduleDay](ScheduleDay.md) via Zones+Patterns during schedule resolution:

1. **Zone and Pattern Resolution**: Zones and Patterns from an active SchedulePlan are retrieved
2. **Pattern Repeating**: The plan engine repeats each Pattern over its Zone until the Zone is full, snapping to the Channel's Grid boundaries
3. **Program Resolution**: At ScheduleDay time, each Program slot resolves to specific assets/episodes:
   - **Series Programs**: Resolve to specific episodes based on rotation policy (sequential, random, LRU, seasonal)
   - **Asset Programs**: Resolve to the referenced asset
   - **VirtualAsset Programs**: Expand to multiple assets (e.g., "intro + episode + outro" becomes three assets)
   - **Rule Programs**: Resolve to assets selected from the filtered set based on rotation policy
4. **Block Consumption**:
   - Under-filled blocks generate avails (gaps that can be filled with commercials or filler)
   - Longform content with `slot_units` override consumes multiple grid blocks
   - Content duration determines block consumption if `slot_units` is not specified
5. **Time Resolution**: Zone time windows and Pattern repeating behavior are combined with channel's Grid boundaries to produce real-world wall-clock times
6. **ScheduleDay Creation**: Resolved Zones, Patterns, and Programs become the resolved asset selections in BroadcastScheduleDay

**Example Flow:**

- Zone: 19:00–22:00 (Prime Time)
- Pattern: [Cheers (series Program), Movie Block (composite Program)]
- Cheers Program: `content_type: "series"`, `content_ref: "Cheers"`, `episode_policy: "seasonal"`, `rotation: "least-recently-used"`
- Resolution at ScheduleDay time: System repeats Pattern over Zone, selects appropriate Cheers episode for current season using LRU rotation
- ScheduleDay: Contains resolved asset UUIDs with wall-clock times (e.g., 2025-12-25 19:00:00 UTC for Cheers episode S11E05)

ScheduleDays are resolved 3-4 days in advance for EPG and playout purposes, based on the Zones, Patterns, and Programs in the active SchedulePlan.

## Operator Workflows

**Create Program in Pattern**: Operators create programs as catalog entries in Patterns. They specify:

- Order within Pattern
- Content selection (asset, series, rule, or virtual package)
- Playback rules (how content should be selected)
- Operator intent (programming goals and constraints)

**Manual Placement**: Operators manually place specific assets or series into Patterns, defining what content should appear in the Pattern's sequence.

**Assisted Placement**: Operators use system assistance to place content:

- System suggests content based on rules and constraints
- Operators review and approve suggestions
- Programs are created with operator intent metadata

**Edit Program**: Operators modify existing programs to:

- Change order within Pattern
- Update content selections
- Adjust playback rules
- Update operator intent

**Preview Program**: Operators preview how a program will resolve:

- See which specific asset/episode will be selected at ScheduleDay time
- View how the Pattern repeats over the Zone
- Check for conflicts or rule violations

## Examples

### Example 1: Series Program with Rotation Rules

**Cheers** as a series Program with rotation policy:

```json
{
  "channel_id": "channel-uuid-1",
  "plan_id": "weekday-plan-uuid",
  "pattern_id": "prime-time-pattern-uuid",
  "order": 0,
  "content_type": "series",
  "content_ref": "Cheers",
  "episode_policy": "seasonal",
  "playback_rules": {
    "rotation": "least-recently-used",
    "avoid_repeats": true
  },
  "operator_intent": "Play Cheers seasonally with LRU rotation"
}
```

This Program defines how to resolve Cheers episodes: select seasonally-appropriate episodes using least-recently-used rotation. At ScheduleDay time, the system selects a specific episode based on these rules.

**Usage in Pattern:**

- Zone: 19:00–22:00 (Prime Time)
- Pattern: `["Cheers", "Frasier", "Seinfeld"]`
- The Pattern repeats over the Zone, and each Cheers slot resolves to a specific episode at ScheduleDay time

### Example 2: Movie Block with slot_units Override

**Movie Block** as a Program with `slot_units` override for longform content:

```json
{
  "channel_id": "channel-uuid-1",
  "plan_id": "weekend-plan-uuid",
  "pattern_id": "movie-pattern-uuid",
  "order": 0,
  "content_type": "rule",
  "content_ref": "{\"genre\": \"drama\", \"min_duration\": 90, \"max_duration\": 150}",
  "playback_rules": {
    "rotation": "random",
    "avoid_repeats": true
  },
  "slot_units": 4,
  "commType": "movie",
  "operator_intent": "2-hour movie block on 30-minute grid"
}
```

This Program defines a movie block that consumes 4 grid blocks (2 hours on a 30-minute grid). The `slot_units=4` override ensures longform content properly consumes multiple blocks.

**Usage in Pattern:**

- Zone: 20:00–22:00 (Prime Time)
- Pattern: `["Movie Block"]`
- On a 30-minute grid, this Program consumes 4 blocks (2 hours total)

### Example 3: VirtualAsset Program for Packaging

**Intro + Episode + Outro** packaging using VirtualAsset:

```json
{
  "channel_id": "channel-uuid-1",
  "plan_id": "weekday-plan-uuid",
  "pattern_id": "series-pattern-uuid",
  "order": 0,
  "content_type": "virtual_package",
  "content_ref": "550e8400-e29b-41d4-a716-446655440000",
  "operator_intent": "Intro + episode + outro packaging"
}
```

This Program references a VirtualAsset that expands to three assets at ScheduleDay time: intro segment, main episode, and outro segment.

**Usage in Pattern:**

- Zone: 19:00–22:00 (Prime Time)
- Pattern: `["Packaged Series"]`
- At ScheduleDay time, the VirtualAsset expands to: [intro asset, episode asset, outro asset]

## Failure / Fallback Behavior

If programs are missing or invalid:

- **Missing programs**: Result in gaps in the schedule (allowed but should generate warnings). Under-filled blocks generate avails.
- **Invalid content references**: System falls back to default content or skips the program slot
- **Unresolvable content**: If content cannot be resolved (e.g., series has no episodes, rule matches no assets), system falls back to alternative content or leaves gap (generates avail)
- **Invalid rotation policies**: System falls back to default rotation (e.g., sequential) if specified policy is invalid
- **VirtualAsset expansion failures**: If VirtualAsset cannot expand, system falls back to alternative content or leaves gap

## Naming Rules

The canonical name for this concept in code and documentation is Program.

Programs are often referred to as "block assignments" or simply "programs" in operator workflows, but the full name should be used in technical documentation and code.

## Validation & Invariants

- **Valid order**: order must be a non-negative integer within the Pattern
- **Valid content reference**: content_ref must be valid for the specified content_type
- **Channel consistency**: channel_id must match the channel associated with the parent SchedulePlan
- **Referential integrity**: plan_id must reference a valid SchedulePlan, pattern_id must reference a valid Pattern within the SchedulePlan

## See Also

- [SchedulePlan](SchedulePlan.md) - Top-level operator-created plans that define channel programming
- [ScheduleDay](ScheduleDay.md) - Resolved schedules for specific channel and date (generated from programs)
- [VirtualAsset](VirtualAsset.md) - ⚠️ FUTURE: Container for multiple assets (can be referenced in programs)
- [PlaylogEvent](PlaylogEvent.md) - Generated playout events (derived from resolved programs)
- [Scheduling](Scheduling.md) - High-level scheduling system
- [Channel](Channel.md) - Channel configuration and timing policy
- [Asset](Asset.md) - Approved content available for scheduling
- [Operator CLI](../operator/CLI.md) - Operational procedures

Program is a **catalog entity** (series/movie/block/composite) that describes how to resolve content, not a per-day time-slot. Programs define resolution rules such as rotation policy (random/sequential/LRU), commType, and slot_units override for longform content. Programs are referenced by Patterns within SchedulePlans — the Zone defines when the Pattern applies, and the Pattern defines the sequence of Program references. Programs do not have `start_time`/`duration` (that's Zone+Pattern). At ScheduleDay time, each Program slot resolves to specific assets/episodes; under-filled blocks generate avails, and longform content with `slot_units` override consumes multiple grid blocks. Programs can reference VirtualAssets for packaging (e.g., "intro + episode + outro"), which expand at ScheduleDay time. Programs flow into ScheduleDay via Zones+Patterns, resolved 3-4 days in advance for EPG and playout purposes.
