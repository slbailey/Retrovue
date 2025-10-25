_Related: [Architecture](../architecture/ArchitectureOverview.md) • [Runtime](../runtime/ChannelManager.md) • [Operator CLI](../operator/CLI.md)_

# Domain — BroadcastChannel

## Purpose

BroadcastChannel defines a persistent broadcast entity with channel identity, configuration, and operational parameters for channels such as "RetroToons" or "MidnightMovies".

## Core model / scope

BroadcastChannel is managed by SQLAlchemy with the following fields:

- **id** (Integer, primary key): Internal identifier for relational joins and foreign key references
- **name** (String(255), required, unique): Human-facing channel label used in UI and operator tooling
- **timezone** (String(255), required): IANA timezone string for all schedule generation and "what's on now" logic
- **grid_size_minutes** (Integer, required): Base grid slot size for scheduling (e.g., 30-minute blocks)
- **grid_offset_minutes** (Integer, required): Grid alignment offset for clean schedule snapping
- **rollover_minutes** (Integer, required): Broadcast day rollover time relative to local midnight (e.g., 360 = 6:00 AM)
- **is_active** (Boolean, required, default=True): Whether channel is on-air and available for scheduling
- **created_at** (DateTime(timezone=True), required): Record creation timestamp
- **updated_at** (DateTime(timezone=True), nullable): Record last modification timestamp

The table is named `broadcast_channels` (plural). Schema migration is handled through Alembic. Postgres is the authoritative backing store.

BroadcastChannel has relationships with schedule data through BroadcastScheduleDay, which links channels to templates for specific broadcast dates.

## Contract / interface

ScheduleService consumes BroadcastChannel records to determine current programming. It generates schedule data using the channel's grid_size_minutes, grid_offset_minutes, and rollover_minutes for accurate block-based scheduling.

The timezone field defines how "local time" is interpreted for that channel's day, including overnight rollover. ScheduleService is authoritative for what to play. BroadcastChannel provides the identity and context.

## Execution model

ChannelManager uses BroadcastChannel to know how to interpret 'now' and how to cut the day (rollover).

A Channel continues to exist even when nobody is watching and ffmpeg is torn down.

## Failure / fallback behavior

If channel configuration is invalid, the system falls back to default programming or the most recent valid configuration.

## Operator workflows

**Create BroadcastChannel**: Use `retrovue channel create` with required parameters:

```bash
retrovue channel create --name "RetroToons" --timezone "America/New_York" \
  --grid-size-minutes 30 --grid-offset-minutes 0 --rollover-minutes 360 --active
```

**List channels**: Use `retrovue channel list` to see all channels in table format, or `retrovue channel list --json` for machine-readable output.

**Inspect channel**: Use `retrovue channel show --id N` to see detailed channel information.

**Activate/deactivate**: Use `retrovue channel update --id N --active` or `--inactive` to toggle is_active status.

**Adjust scheduling**: Use `retrovue channel update --id N` with new grid parameters to modify schedule block alignment and day cutover behavior.

**Retire channel**: Use `retrovue channel update --id N --inactive` to remove from routing and scheduling, or `retrovue channel delete --id N` to permanently remove.

**Update channel**: Use `retrovue channel update --id N` with any combination of fields to modify channel properties.

All operations use integer IDs for channel identification. The CLI provides both human-readable and JSON output formats.

## Naming rules

The canonical name for this concept in code and documentation is BroadcastChannel.

- **Operator-facing noun**: `channel` (humans type `retrovue channel ...`)
- **Internal canonical model**: `BroadcastChannel`
- **Database table**: `broadcast_channels` (plural)
- **CLI commands**: Use integer IDs for channel identification
- **Code and docs**: Always refer to the persisted model as `BroadcastChannel`

BroadcastChannel is always capitalized in internal docs. schedule_date uses YYYY-MM-DD format. broadcast_day is derived from rollover policy and is not wall-clock midnight.

## See also

- [Scheduling](Scheduling.md) - High-level scheduling system
- [Playout pipeline](PlayoutPipeline.md) - Live stream generation
- [Channel manager](../runtime/ChannelManager.md) - Stream execution
- [Operator CLI](../operator/CLI.md) - Operational procedures
