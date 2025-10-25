_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md)_

# Domain — Playlog event

## Purpose

BroadcastPlaylogEvent represents a single scheduled, timestamped playout unit in the near-term horizon. This object feeds Producers and ChannelManager so they can build a playout plan at 'now', but this object itself does not launch ffmpeg.

## Core model / scope

BroadcastPlaylogEvent enables:

- Generated playout schedules
- Content timing and sequencing
- Playout execution instructions
- Broadcast day tracking and rollover handling

## Contract / interface

BroadcastPlaylogEvent is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Unique identifier for relational joins and foreign key references
- **uuid** (UUID, required, unique): Stable external identifier used for audit, cross-domain tracing, and as-run logs
- **channel_id** (Integer, required, foreign key): Reference to BroadcastChannel
- **asset_id** (Integer, required, foreign key): Reference to CatalogAsset
- **start_utc** (DateTime(timezone=True), required): Event start time in UTC
- **end_utc** (DateTime(timezone=True), required): Event end time in UTC
- **broadcast_day** (Text, required): Broadcast day label in "YYYY-MM-DD" format
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

BroadcastPlaylogEvent has indexes on channel_id, start_utc, and broadcast_day for efficient playout queries.

## Execution model

ScheduleService generates BroadcastPlaylogEvent records as the output of the scheduling process. These events represent the final playout schedule that will be executed by ChannelManager.

Playlog events are created by:

1. ScheduleService reading template assignments and blocks
2. Applying content selection rules to choose appropriate assets
3. Generating playout events with precise timing and sequencing
4. Creating BroadcastPlaylogEvent records for each scheduled content item

## Failure / fallback behavior

If playlog events are missing or invalid, the system falls back to default programming or the most recent valid schedule.

## Naming rules

The canonical name for this concept in code and documentation is BroadcastPlaylogEvent.

Playlog events are generated scheduling output, not runtime components. They define "what to play when" but do not execute playout.

## Operator workflows

**Monitor Playout**: View generated playlog events to see what content is scheduled to play.

**Playout Verification**: Verify that scheduled content matches programming intentions and timing.

**Content Timing**: Review start/end times to ensure proper content sequencing and timing.

**Broadcast Day Management**: Track content across broadcast day boundaries and rollover periods.

**Playout Troubleshooting**: Use playlog events to diagnose playout issues and content problems.

## See also

- [Scheduling](Scheduling.md) - High-level scheduling system
- [Schedule day](ScheduleDay.md) - Template assignments
- [Catalog asset](CatalogAsset.md) - Approved content
- [Playout pipeline](PlayoutPipeline.md) - Live stream generation
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
