# MasterClock Implementation

_Implementation guide for RetroVue's authoritative time source._

## Overview

This document describes the implementation of MasterClock, RetroVue's authoritative time source for all runtime components. MasterClock provides consistent, timezone-aware time across the entire system.

## Implementation Details

### Core Class: `MasterClock`

**Location:** `src/retrovue/runtime/clock.py`

The MasterClock class provides the following key methods:

- `now_utc()` - Get current UTC time as system master reference
- `now_local(channel_tz)` - Get current local time for a channel's timezone
- `seconds_since(dt)` - Calculate seconds elapsed since a given datetime
- `convert_timezone(dt, from_tz, to_tz)` - Convert between timezones
- `schedule_event()` - Schedule time-based events
- `trigger_scheduled_events()` - Trigger due events

### Key Features

#### Timezone Handling

- Uses Python's built-in `zoneinfo` module for timezone operations
- Caches timezone objects for performance
- Handles DST transitions automatically
- Supports all standard timezone names

#### Precision Control

- Three precision levels: SECOND, MILLISECOND, MICROSECOND
- Configurable per instance
- Affects all time output methods

#### Event Scheduling

- Schedule time-based events with precise timing
- Query events in time ranges
- Automatic event triggering
- Thread-safe event management

## Testing

### Test Structure

**Location:** `tests/runtime/`

- `test_clock.py` - Core functionality tests
- `test_clock_performance.py` - Performance and scalability tests
- `conftest.py` - Shared test fixtures
- `run_clock_tests.py` - Test runner script

### Running Tests

```bash
# Run all MasterClock tests
python tests/runtime/run_clock_tests.py

# Run performance tests only
python tests/runtime/run_clock_tests.py --performance

# Run specific test
python tests/runtime/run_clock_tests.py --test=TestMasterClock.test_now_utc
```

### Test Coverage

The test suite covers:

- **Core Functionality**: All public methods and edge cases
- **Timezone Operations**: Conversion, caching, DST handling
- **Event Scheduling**: Creation, querying, triggering
- **Performance**: High-frequency operations, caching efficiency
- **Integration**: Usage patterns for other components
- **Error Handling**: Invalid inputs, edge cases

## Usage Examples

### Basic Usage

```python
from retrovue.runtime.clock import MasterClock

# Create instance
clock = MasterClock()

# Get current time
utc_time = clock.now_utc()
local_time = clock.now_local("America/New_York")

# Calculate time differences
seconds_ago = clock.seconds_since(some_datetime)
```

### ScheduleService Integration

```python
class ScheduleService:
    def __init__(self, clock: MasterClock):
        self.clock = clock

    def get_playout_plan_now(self, channel_id: str, at_station_time: datetime):
        # Get authoritative time
        now_utc = self.clock.now_utc()

        # Get channel-specific time
        channel_time = self.clock.now_local("America/New_York")

        # Calculate offset for mid-program joins
        offset_seconds = self.clock.seconds_since(at_station_time)

        return self._build_playout_plan(channel_id, now_utc, offset_seconds)
```

### ChannelManager Integration

```python
class ChannelManager:
    def __init__(self, clock: MasterClock):
        self.clock = clock

    def viewer_join(self, session_id: str, session_info: Dict[str, Any]):
        # Get current time for logging
        join_time = self.clock.now_utc()

        # Calculate playback offset for mid-program joins
        program_start = self._get_program_start_time()
        offset = self.clock.seconds_since(program_start)

        # Start producer with correct offset
        self._start_producer_with_offset(offset)
```

## Performance Characteristics

### Timezone Caching

- First access to a timezone populates cache
- Subsequent accesses use cached timezone objects
- Significant performance improvement for repeated timezone operations

### Precision Impact

- SECOND precision: Fastest, zero microseconds
- MILLISECOND precision: Good balance of speed and accuracy
- MICROSECOND precision: Highest accuracy, slightly slower

### Scalability

- Handles 30+ timezones efficiently
- Supports high-frequency time queries (10,000+ per second)
- Event scheduling scales to 1000+ events
- Memory usage remains constant with timezone caching

## Dependencies

### Required

- Python 3.11+
- `zoneinfo` module (built-in)

### Optional

- `pytest` for testing
- `pytest-asyncio` for async tests (future)

## Future Enhancements

### Planned Features

- **NTP Synchronization**: External time source integration
- **PTP Support**: Precision Time Protocol for broadcast-grade timing
- **Frame-Level Precision**: Ultra-high precision for critical operations
- **Event Coordination**: Integration with scheduler daemon

### Backward Compatibility

- All future enhancements will maintain the v0.1 interface
- New features will be opt-in via configuration
- Existing code will continue to work unchanged

## Error Handling

### Timezone Errors

- Invalid timezone names raise exceptions
- Graceful fallback to UTC when possible
- Clear error messages for debugging

### Event Scheduling

- Duplicate event IDs are handled gracefully
- Invalid trigger times are validated
- Event cleanup on errors

### Performance Degradation

- Timezone cache can be cleared on memory pressure
- Event cleanup for large event sets
- Precision can be adjusted for performance

## Monitoring and Debugging

### Logging

- Timezone cache hits/misses
- Event scheduling and triggering
- Performance metrics
- Error conditions

### Metrics

- Time query frequency
- Timezone conversion performance
- Event scheduling efficiency
- Memory usage patterns

## Security Considerations

### Time Manipulation

- MasterClock uses system time as authoritative source
- No external time sources in v0.1 (reduces attack surface)
- Timezone data comes from system zoneinfo database

### Event Security

- Event payloads are not validated (component responsibility)
- Event timing is not cryptographically secured
- No authentication for event scheduling

## Integration Guidelines

### Component Integration

1. **Dependency Injection**: Pass MasterClock to components via constructor
2. **No Direct System Time**: Always use MasterClock instead of `datetime.now()`
3. **Timezone Awareness**: Use appropriate timezone for each channel
4. **Event Timing**: Use MasterClock for all time-based events

### Testing Integration

1. **Mock MasterClock**: Use test doubles for unit tests
2. **Time Control**: Use fixed times for deterministic tests
3. **Timezone Testing**: Test with different timezone configurations
4. **Performance Testing**: Include MasterClock in performance benchmarks

## Troubleshooting

### Common Issues

**Timezone Not Found**

```
Exception: Invalid timezone 'Invalid/Timezone'
```

Solution: Use valid timezone names from IANA database

**Performance Issues**

```
Slow timezone conversions
```

Solution: Check timezone caching, consider precision settings

**Event Not Triggering**

```
Scheduled events not firing
```

Solution: Check trigger times, ensure timezone consistency

### Debug Tools

```python
# Check timezone cache
print(clock.timezone_cache)

# Check scheduled events
print(clock.scheduled_events)

# Validate time consistency
print(clock.validate_time_consistency())

# Get timezone information
print(clock.get_timezone_info("America/New_York"))
```

## Conclusion

MasterClock provides a robust, performant time authority for RetroVue's runtime system. Its design emphasizes simplicity, reliability, and performance while maintaining the flexibility needed for future enhancements.

The implementation follows RetroVue's architectural patterns and provides the temporal foundation that enables all other components to operate with consistent, accurate time.
