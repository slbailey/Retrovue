_Related: [Architecture](../overview/architecture.md) • [Contracts](../contracts/README.md) • [Channel](Channel.md) • [Runtime: Schedule service](../runtime/schedule_service.md)_

# Domain — MasterClock

## Purpose

MasterClock is the single source of truth for "now" inside RetroVue. It provides authoritative, timezone-aware time across the entire system. All scheduling, playout, logging, and ChannelManager decisions must query MasterClock instead of calling system time directly.

## Core model / scope

- MasterClock is the authority for current wall-clock time in the system.
- All runtime components (ScheduleService, ChannelManager, ProgramDirector, AsRunLogger) MUST obtain wall-clock timestamps from MasterClock.
- Calling `datetime.now()` or `datetime.utcnow()` directly in runtime code is considered a defect.
- MasterClock aligns with the local-time methodology: inputs/outputs presented in local system time; storage and inter-component exchange in UTC.

## Contract / interface

MasterClock exposes:

- **`now_utc() -> datetime`**: Returns current UTC time as an aware datetime (tzinfo=UTC). This is the authoritative station time.
- **`now_local() -> datetime`**: Returns current time in the system/station timezone as an aware datetime.
- **`seconds_since(dt: datetime) -> float`**: Returns `max(0, now_utc() - dt_in_utc).total_seconds()`.
  - Accepts both aware UTC datetimes and aware local datetimes.
  - If `dt` is naive, raises `ValueError`.
  - If `dt` is in the future, returns `0.0` instead of a negative number.
  - This gives ChannelManager a sane non-negative playout offset.
- **`to_local(dt_utc: datetime) -> datetime`**: Converts an aware UTC datetime to an aware datetime in the system local timezone. Raises `ValueError` on naive input.
- **`to_utc(dt_local: datetime) -> datetime`**: Converts an aware local datetime to an aware UTC datetime. Raises `ValueError` on naive input.

Notes:
- No per-channel timezone. "Local" means system local timezone.
- All datetimes are tz-aware; naive datetimes are rejected.

## Design Principles

### Timezone Awareness

All datetimes returned by MasterClock MUST be timezone-aware. UTC is the authoritative source of truth for storage and inter-component exchange.

### Time Monotonicity

Time should never appear to "go backward" from the point of view of ChannelManager's playout math. `now_utc()` never appears to go backward within a process.

### Error Handling

- Naive datetimes raise `ValueError`.
- Future timestamps in `seconds_since()` clamp to `0.0`.
- DST transitions are handled by the platform timezone rules.

### Passive Design

MasterClock is intentionally passive and read-only:

- It does not accept timers or listeners.
- It does not wake other components.
- It does not know broadcast day rules.
- The scheduler_daemon (horizon builder) polls MasterClock for `now_utc()` and then asks ScheduleService what needs to be generated.

**MasterClock is read-only, authoritative, and never event-driven.**

## Integration Patterns

### ScheduleService Integration

ScheduleService uses MasterClock to advance EPG / Playlog horizons:

```python
class ScheduleService:
    def __init__(self, clock: MasterClock):
        self.clock = clock

    def get_playout_plan_now(self, channel_id: str):
        # Get authoritative time
        now_utc = self.clock.now_utc()

        # Derive local time (system timezone) if needed
        local_time = self.clock.now_local()

        # Calculate offset for mid-program joins
        offset_seconds = self.clock.seconds_since(program_start_time)

        return self._build_playout_plan(channel_id, now_utc, offset_seconds)
```

ScheduleService does the broadcast-day classification. MasterClock does NOT know about broadcast days; it only knows "what time is it (UTC + system local)." This keeps boundaries clear between time authority and scheduling logic.

### ChannelManager Integration

ChannelManager uses MasterClock to timestamp transitions and calculate playout offsets:

```python
class ChannelManager:
    def __init__(self, clock: MasterClock):
        self.clock = clock

    def viewer_join(self, session_id: str):
        # Get current time for logging
        join_time = self.clock.now_utc()

        # Calculate playback offset for mid-program joins
        program_start = self._get_program_start_time()
        offset = self.clock.seconds_since(program_start)

        # Start producer with correct offset
        self._start_producer_with_offset(offset)
```

### AsRunLogger Integration

AsRunLogger uses MasterClock to record what actually aired:

```python
class AsRunLogger:
    def __init__(self, clock: MasterClock):
        self.clock = clock

    def log_event(self, event: str, channel: str):
        # Get both UTC and local timestamps
        utc_time = self.clock.now_utc()
        local_time = self.clock.now_local()

        # Log with consistent timestamps
        self._write_log({
            "timestamp": utc_time.isoformat(),
            "local_time": local_time.isoformat(),
            "event": event,
            "channel": channel
        })
```

## Validation & invariants

- **MC-001**: All returned datetimes are tz-aware. UTC is authoritative for storage and exchange.
- **MC-002**: Time monotonicity — `now_utc()` never appears to go backward within a process.
- **MC-003**: `seconds_since(dt)` never returns negative values; future timestamps clamp to `0.0`.
- **MC-004**: Naive datetimes passed to conversion methods raise `ValueError`.
- **MC-005**: Local time is the system timezone; no per-channel timezone parameters.
- **MC-006**: Passive design — no timers, listeners, or event scheduling APIs.
- **MC-007**: Single source of "now" — runtime components must not call `datetime.now()` directly.

## Failure / fallback behavior

If MasterClock is unavailable or returns nonsense, downstream services cannot safely infer "what is on right now." This is considered critical. This condition must be surfaced to operators.

## Execution model

- Scheduler uses MasterClock to advance EPG / Playlog horizons.
- Producer uses MasterClock to figure out "what should be airing right now".
- ChannelManager uses MasterClock to timestamp transitions.
- As-run log uses MasterClock to record what actually aired.

## Naming rules

- "MasterClock" is not ffmpeg's framerate clock. It is the broadcast facility wall clock for RetroVue logic.

## Testing

The MasterClock implementation is validated through comprehensive testing that ensures:

- Contract enforcement (MC-001 through MC-007)
- Time monotonicity (never goes backward)
- Timezone safety (DST transitions handled correctly)
- Consistency (all components see the same "now")
- Boundary conditions (schedule block boundaries work correctly)
- Performance (high-frequency operations remain stable)
- Serialization (timestamps serialize to ISO 8601 correctly)

See [MasterClock Contract](../contracts/resources/MasterClockContract.md) for CLI test contracts and detailed behavior rules.

## See also

- [MasterClock Contract](../contracts/resources/MasterClockContract.md) — Runtime contract and CLI test specifications
- [ScheduleService](../runtime/schedule_service.md) — Uses MasterClock for all scheduling operations
- [ChannelManager](../runtime/ChannelManager.md) — Uses MasterClock for playout offset calculations
- [ProgramDirector](../runtime/program_director.md) — Uses MasterClock for system-wide coordination
- [AsRunLogger](../runtime/AsRunLogging.md) — Uses MasterClock for consistent timestamp logging

