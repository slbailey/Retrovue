# MasterClock Architecture

_MasterClock is RetroVue's authoritative time source for all runtime components._

## Overview

MasterClock provides consistent, timezone-aware time across the entire system. It serves as the single source of truth for temporal operations, ensuring all components operate with synchronized time.

## Core Responsibilities

- **Time Authority**: Provide authoritative UTC and local time
- **Timezone Conversion**: Handle timezone conversions safely
- **Time Calculations**: Calculate time differences with proper clamping
- **Consistency**: Ensure all components see the same "now"

## Key Methods

### `now_utc() -> datetime`

Returns current UTC time as an aware datetime (tzinfo=UTC). This is the authoritative station time.

### `now_local(channel_tz: str | None = None) -> datetime`

Returns current time for the given channel timezone as an aware datetime.

- If channel_tz is None, default to system/station timezone
- If the timezone string is invalid, fall back to UTC
- Uses Python's zoneinfo for tz conversion

### `seconds_since(dt: datetime) -> float`

Returns max(0, now_utc() - dt_in_utc).total_seconds()

- Accept both aware UTC datetimes and aware local datetimes
- If dt is naive, raise ValueError
- If dt is in the future, return 0.0 instead of a negative number
- This gives ChannelManager a sane non-negative playout offset

### `to_channel_time(dt: datetime, channel_tz: str) -> datetime`

Converts an aware UTC datetime to an aware datetime in that channel's timezone.

- If channel_tz is invalid, fall back to UTC
- If dt is naive, raise ValueError

## Design Principles

### Timezone Awareness

All datetimes returned by MasterClock MUST be timezone-aware. UTC is the authoritative source of truth.

### Time Monotonicity

Time should never appear to "go backward" from the point of view of ChannelManager's playout math.

### Error Handling

- Invalid timezones fall back to UTC gracefully
- Naive datetimes raise ValueError
- Future timestamps in seconds_since() clamp to 0.0

## Integration Patterns

### ScheduleService Integration

```python
class ScheduleService:
    def __init__(self, clock: MasterClock):
        self.clock = clock

    def get_playout_plan_now(self, channel_id: str):
        # Get authoritative time
        now_utc = self.clock.now_utc()

        # Get channel-specific time
        channel_time = self.clock.now_local("America/New_York")

        # Calculate offset for mid-program joins
        offset_seconds = self.clock.seconds_since(program_start_time)

        return self._build_playout_plan(channel_id, now_utc, offset_seconds)
```

### ChannelManager Integration

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

```python
class AsRunLogger:
    def __init__(self, clock: MasterClock):
        self.clock = clock

    def log_event(self, event: str, channel: str):
        # Get both UTC and local timestamps
        utc_time = self.clock.now_utc()
        local_time = self.clock.now_local("America/New_York")

        # Log with consistent timestamps
        self._write_log({
            "timestamp": utc_time.isoformat(),
            "local_time": local_time.isoformat(),
            "event": event,
            "channel": channel
        })
```

## Testing Expectations

The MasterClock implementation is validated through comprehensive testing that ensures:

### Contract Enforcement

- All runtime components (ScheduleService, ChannelManager, ProgramDirector, AsRunLogger) MUST get wall clock timestamps from MasterClock
- Calling datetime.now() or datetime.utcnow() directly in runtime code is considered a defect
- MasterClock is the only allowed source of time for scheduling, playout offsets, and AsRun logging
- MasterClock guarantees:
  - tz-aware datetimes
  - non-negative offset math
  - stable timezone conversion, or safe fallback to UTC

### Time Monotonicity

- Time never goes backward
- seconds_since() never returns negative values
- Future timestamps clamp to 0.0

### Timezone Safety

- Invalid timezones fall back to UTC gracefully
- DST transitions are handled correctly
- All returned datetimes are timezone-aware

### Consistency

- All components see the same "now"
- Maximum skew between components is minimal
- No naive datetimes are returned

### Broadcast Day Boundaries

- ScheduleService does the broadcast-day classification. MasterClock does NOT know about broadcast days; it only knows "what time is it (UTC + channel local)."
- This keeps boundaries clear between time authority and scheduling logic.

### Boundary Conditions

- Schedule slot boundaries work correctly
- Off-by-one errors are prevented
- DST edge cases are handled
- masterclock-scheduler-alignment enforces this contract by failing if naive or non-MasterClock timestamps are detected

### Performance

- High-frequency operations remain stable
- Timezone caching works efficiently
- No memory leaks in long-running processes

### Serialization

- Timestamps serialize to ISO 8601 correctly
- Round-trip accuracy is maintained
- Timezone information is preserved

## Version History

- **v0.1**: Initial implementation with core time operations
- **Future**: NTP/PTP synchronization, event scheduling, frame-level precision

## Dependencies

- Python 3.11+
- `zoneinfo` module (built-in)
- `datetime` module (built-in)

## Security Considerations

- MasterClock uses system time as authoritative source
- No external time sources in v0.1 (reduces attack surface)
- Timezone data comes from system zoneinfo database
- No authentication required for time operations

_Document version: v0.1 · Last updated: 2025-10-24_
