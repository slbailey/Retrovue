# RetroVue Runtime — MasterClock

_Related: [Runtime: Channel manager](ChannelManager.md) • [Runtime: Schedule service](schedule_service.md) • [Runtime: As-run logging](AsRunLogging.md)_

> Authoritative station time source for all runtime components.

**Note:** This document consolidates content from multiple earlier sources (docs/components/_ and docs/runtime/_) as part of documentation unification (2025-10-24).

_MasterClock is RetroVue's authoritative station time source for all runtime components._

## Overview

MasterClock provides consistent, tz-aware time across the entire system. It serves as the single source of truth for temporal operations, ensuring all components operate with synchronized time.

## Core Responsibilities

- **Time Authority**: Provide authoritative UTC and local (system) time
- **Timezone Conversion**: Convert between UTC and local safely
- **Time Calculations**: Calculate time differences with proper clamping
- **Consistency**: Ensure all components see the same "now"

## Key Methods

### `now_utc() -> datetime`

Returns current UTC time as an aware datetime (tzinfo=UTC). This is the authoritative station time.

### `now_local() -> datetime`

Returns current time in the system/station timezone as an aware datetime.

### `seconds_since(dt: datetime) -> float`

Returns max(0, now_utc() - dt_in_utc).total_seconds()

- Accept both aware UTC datetimes and aware local datetimes
- If dt is naive, raise ValueError
- If dt is in the future, return 0.0 instead of a negative number
- This gives ChannelManager a sane non-negative playout offset

### `to_local(dt_utc: datetime) -> datetime`

Converts an aware UTC datetime to an aware datetime in the system local timezone. Raises ValueError on naive input.

### `to_utc(dt_local: datetime) -> datetime`

Converts an aware local datetime to an aware UTC datetime. Raises ValueError on naive input.

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

        # Derive local time (system timezone) if needed
        local_time = self.clock.now_local()

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
        local_time = self.clock.now_local()

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

- DST transitions are handled by the platform timezone rules
- All returned datetimes are timezone-aware

### Consistency

- All components see the same "now"
- Maximum skew between components is minimal
- No naive datetimes are returned

### Broadcast Day Boundaries

- ScheduleService does the broadcast-day classification. MasterClock does NOT know about broadcast days; it only knows "what time is it (UTC + system local)."
- This keeps boundaries clear between time authority and scheduling logic.

### Passive Design

MasterClock is intentionally passive and read-only:

- It does not accept timers or listeners.
- It does not wake other components.
- It does not know broadcast day rules.
- The scheduler_daemon (horizon builder) will poll MasterClock for now_utc() and then ask ScheduleService what needs to be generated.

**MasterClock is read-only, authoritative, and never event-driven.**

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

## CLI Testing Commands

The following CLI commands are available for testing MasterClock functionality:

### Basic Testing

```bash
# Basic functionality test
retrovue test masterclock

# Test with specific precision
retrovue test masterclock --precision microsecond

# Get JSON output for programmatic use
retrovue test masterclock --json
```

### Production Validation Tests

```bash
# Test time monotonicity
retrovue test masterclock-monotonic

# (deprecated) timezone resolution tests — local-time only policy

# Test logging timestamps
retrovue test masterclock-logging

# Test scheduler alignment
retrovue test masterclock-scheduler-alignment

# Test stability
retrovue test masterclock-stability

# Test consistency
retrovue test masterclock-consistency

# Test serialization
retrovue test masterclock-serialization
```

### Performance Testing

```bash
# Basic performance test
retrovue test masterclock-performance

# High-load performance test
retrovue test masterclock-performance --iterations 50000 --timezones 20

# Get JSON output for benchmarking
retrovue test masterclock-performance --json
```

## JSON Output Fields

The test commands provide structured JSON output with the following key fields:

- `uses_masterclock_only`: Confirms no direct datetime.now() usage
- `naive_timestamp_rejected`: Confirms naive timestamps are properly rejected
- `max_skew_seconds`: Maximum time skew between components
- `peak_calls_per_second`: Performance metrics for timezone operations
- `tzinfo_ok`: Timezone information preservation
- `roundtrip_ok`: Serialization round-trip accuracy

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

## Cross-References

| Component                                  | Relationship                                      |
| ------------------------------------------ | ------------------------------------------------- |
| **[ScheduleService](schedule_service.md)** | Uses MasterClock for all scheduling operations    |
| **[ChannelManager](ChannelManager.md)**    | Uses MasterClock for playout offset calculations  |
| **[ProgramDirector](program_director.md)** | Uses MasterClock for system-wide coordination     |
| **[AsRunLogger](AsRunLogging.md)**         | Uses MasterClock for consistent timestamp logging |

_Document version: v0.1 · Last updated: 2025-10-24_
