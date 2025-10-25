# Domain — BroadcastChannel

## Purpose

BroadcastChannel represents a persistent broadcast entity in the RetroVue system. It defines channel identity, configuration, and operational parameters for channels such as "RetroToons" or "MidnightMovies".

BroadcastChannel is stored in Postgres using SQLAlchemy. It is configuration and identity, not a runtime encoder instance. Operators reference BroadcastChannel when scheduling content, managing programming, and monitoring on-air status.

BroadcastChannel defines:

- Channel identity and human-facing name
- IANA timezone for all scheduling logic
- Broadcast day rollover rules (e.g., 6:00 AM for overnight blocks)
- Clock/grid alignment for scheduling
- Active status for on-air availability

The canonical name is BroadcastChannel throughout code, documentation, and database schema.

## Persistence model and fields

BroadcastChannel is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Unique identifier for relational joins and foreign key references
- **uuid** (UUID, required, unique): Stable external identifier used for audit, cross-domain tracing, and as-run logs
- **name** (Text, required, unique): Human-facing channel label used in UI and operator tooling
- **timezone** (Text, required): IANA timezone string for all schedule generation and "what's on now" logic
- **grid_size_minutes** (Integer, required): Base grid slot size for scheduling (e.g., 30-minute blocks)
- **grid_offset_minutes** (Integer, required): Grid alignment offset for clean schedule snapping
- **rollover_minutes** (Integer, required): Broadcast day rollover time relative to local midnight (e.g., 360 = 6:00 AM)
- **is_active** (Boolean, required): Whether channel is on-air and available for scheduling
- **created_at** (DateTime(timezone=True), required): Record creation timestamp

Schema migration is handled through Alembic. Postgres is the authoritative backing store.

BroadcastChannel has relationships with schedule data through BroadcastScheduleDay, which links channels to templates for specific broadcast dates.

## Scheduling and interaction rules

ScheduleService consumes BroadcastChannel records to determine current programming. It generates schedule data using the channel's grid_size_minutes, grid_offset_minutes, and rollover_minutes for accurate block-based scheduling.

The timezone field defines how "local time" is interpreted for that channel's day, including overnight rollover. ScheduleService is authoritative for what to play. BroadcastChannel provides the identity and context.

## Runtime relationship

BroadcastChannel becomes an active stream through runtime components:

**ChannelManager** is the per-channel runtime orchestrator responsible for putting the channel on-air. It asks ScheduleService what to play but does not generate schedules or make programming decisions.

**Producer** (NormalProducer, EmergencyProducer, GuideProducer) is the output generator that produces continuous MPEG-TS transport stream to stdout. It plays content as instructed without content selection.

**Fan-out**: ChannelManager distributes the stdout stream from the active Producer to multiple viewers/clients using the IPTV one-producer-many-consumers model.

**ChannelRuntimeState** is an in-memory snapshot maintained by ChannelManager. It tracks viewer count, current mode, Producer status, and health for operator dashboards.

Runtime hierarchy:
BroadcastChannel (persistent, Postgres) → ScheduleService → ChannelManager → Producer → viewers

BroadcastChannel is persisted configuration. ChannelManager, Producer, and ChannelRuntimeState are runtime/ephemeral.

## Operator workflows

**Create BroadcastChannel**: Define name, timezone, grid rules, and rollover_minutes. Set active status.

**Activate/deactivate**: Toggle is_active to control on-air availability for scheduling and playout.

**Adjust scheduling**: Modify grid size/offset/rollover to change schedule block alignment and day cutover behavior.

**Inspect status**: Check is_active for operational status. Monitor ChannelRuntimeState for live status (streaming, viewers, mode).

**Retire channel**: Set is_active false to remove from routing and scheduling.

Future operator tooling will include maintenance CLI/admin UI for BroadcastChannel records and Channel Dashboard UI for ChannelRuntimeState display.

## Naming and consistency rules

The canonical name for this concept in code and documentation is BroadcastChannel.

We do NOT maintain a separate "Channel" model alongside BroadcastChannel. There is no parallel "ChannelConfig" entity unless one is explicitly introduced later.

All scheduling logic, runtime orchestration, and operator tooling MUST refer to BroadcastChannel as the persisted channel definition.

ChannelManager, Producer, and ChannelRuntimeState are runtime components that operate on a BroadcastChannel. They are not alternate channel definitions.

**Important**: broadcast_channel is the ONLY canonical persisted channel table. The old UUID-based channels table is deprecated. BroadcastChannel.uuid is exposed externally (guide, logs, analytics).
