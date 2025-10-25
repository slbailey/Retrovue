# Domain — BroadcastPlaylogEvent

## Purpose

BroadcastPlaylogEvent represents a generated playout event that records what content was actually scheduled to play at a specific time. These events are created by ScheduleService and consumed by ChannelManager for playout execution.

BroadcastPlaylogEvent enables:

- Generated playout schedules
- Content timing and sequencing
- Playout execution instructions
- Broadcast day tracking and rollover handling

The canonical name is BroadcastPlaylogEvent throughout code, documentation, and database schema.

## Persistence model and fields

BroadcastPlaylogEvent is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Unique identifier for relational joins and foreign key references
- **uuid** (UUID, required, unique): Stable external identifier used for audit, cross-domain tracing, and as-run logs
- **channel_id** (Integer, required, foreign key): Reference to BroadcastChannel
- **asset_id** (Integer, required, foreign key): Reference to CatalogAsset
- **start_utc** (DateTime(timezone=True), required): Event start time in UTC
- **end_utc** (DateTime(timezone=True), required): Event end time in UTC
- **broadcast_day** (Text, required): Broadcast day label in "YYYY-MM-DD" format
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

Schema migration is handled through Alembic. Postgres is the authoritative backing store.

BroadcastPlaylogEvent has indexes on channel_id, start_utc, and broadcast_day for efficient playout queries.

**Important**: BroadcastPlaylogEvent represents scheduled playout segments with absolute wallclock times. It references BroadcastChannel and CatalogAsset by INTEGER FK. It also has its own uuid to uniquely identify the aired segment for compliance review and as-run logging.

## Scheduling and interaction rules

ScheduleService generates BroadcastPlaylogEvent records as the output of the scheduling process. These events represent the final playout schedule that will be executed by ChannelManager.

Playlog events are created by:

1. ScheduleService reading template assignments and blocks
2. Applying content selection rules to choose appropriate assets
3. Generating playout events with precise timing and sequencing
4. Creating BroadcastPlaylogEvent records for each scheduled content item

## Runtime relationship

BroadcastPlaylogEvent operates through the playout execution pipeline:

**ScheduleService** generates playlog events as the output of the scheduling process. It creates events with precise timing and content references.

**ChannelManager** reads playlog events to determine what content to play and when. It uses the events to coordinate playout execution.

**Producer** receives playout instructions from ChannelManager and plays the actual content files referenced by the events.

Runtime hierarchy:
BroadcastPlaylogEvent (persistent) → ChannelManager (playout coordination) → Producer (content playback)

## Operator workflows

**Monitor Playout**: View generated playlog events to see what content is scheduled to play.

**Playout Verification**: Verify that scheduled content matches programming intentions and timing.

**Content Timing**: Review start/end times to ensure proper content sequencing and timing.

**Broadcast Day Management**: Track content across broadcast day boundaries and rollover periods.

**Playout Troubleshooting**: Use playlog events to diagnose playout issues and content problems.

## Naming and consistency rules

The canonical name for this concept in code and documentation is BroadcastPlaylogEvent.

Playlog events are generated scheduling output, not runtime components. They define "what to play when" but do not execute playout.

All scheduling logic, operator tooling, and documentation MUST refer to BroadcastPlaylogEvent as the persisted playout event definition.

BroadcastPlaylogEvent represents the generated playout events (what was actually played) that are created by ScheduleService and executed by ChannelManager for broadcast playout.
