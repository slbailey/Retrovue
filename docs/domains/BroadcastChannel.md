# Domain — BroadcastChannel

## Purpose

BroadcastChannel defines a persistent broadcast entity with channel identity, configuration, and operational parameters for channels such as "RetroToons" or "MidnightMovies".

## Persistence model and fields

BroadcastChannel is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Internal identifier for relational joins and foreign key references
- **uuid** (UUID, required, unique): External stable identifier exposed to API, runtime, and logs
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

## Runtime behavior

ChannelManager uses BroadcastChannel to know how to interpret 'now' and how to cut the day (rollover).

## Operator workflows

**Create BroadcastChannel**: Define name, timezone, grid rules, and rollover_minutes. Set active status.

**Activate/deactivate**: Toggle is_active to control on-air availability for scheduling and playout.

**Adjust scheduling**: Modify grid size/offset/rollover to change schedule block alignment and day cutover behavior.

**Inspect status**: Check is_active for operational status. Monitor ChannelRuntimeState for live status (streaming, viewers, mode).

**Retire channel**: Set is_active false to remove from routing and scheduling.

Operators and external integrations should always refer to objects by uuid, not by integer id.

## Naming rules

The canonical name for this concept in code and documentation is BroadcastChannel.

API surfaces and logs must surface the UUID, not the integer id.

BroadcastChannel is always capitalized in internal docs. schedule_date uses YYYY-MM-DD format. broadcast_day is derived from rollover policy and is not wall-clock midnight.
