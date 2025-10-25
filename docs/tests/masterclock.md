# MasterClock Testing

_Related: [Runtime: Master clock](../runtime/MasterClock.md) • [Runtime: Channel manager](../runtime/ChannelManager.md) • [Contributing: Runtime](../contributing/CONTRIBUTING_RUNTIME.md)_

This document describes the MasterClock validation tests, including what fields they emit in --json output and what failures mean.

## Overview

The MasterClock tests validate that RetroVue's authoritative time source works correctly and that all runtime components use it properly. These tests enforce the contract that MasterClock is the only legal source of current time in the system.

## Test Commands

### Basic Functionality Tests

```bash
# Basic functionality test
retrovue test masterclock

# Test with specific precision and timezone
retrovue test masterclock --precision microsecond --timezone "Europe/London"

# Get JSON output for programmatic use
retrovue test masterclock --json
```

### Production Validation Tests

```bash
# Test time monotonicity
retrovue test masterclock-monotonic

# Test timezone resolution
retrovue test masterclock-timezone-resolution

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

### Performance Tests

```bash
# Basic performance test
retrovue test masterclock-performance

# High-load performance test
retrovue test masterclock-performance --iterations 50000 --timezones 20

# Get JSON output for benchmarking
retrovue test masterclock-performance --json
```

## Test Descriptions

### `masterclock-monotonic`

**What it tests:** Proves time doesn't "run backward" and seconds_since() is never negative.

**Why it matters:** ChannelManager uses seconds_since() to compute mid-program offsets. We need non-negative offsets.

**Key assertions:**

- Time never goes backward between consecutive calls
- seconds_since() with future timestamps returns 0.0
- seconds_since() with past timestamps returns positive values

### `masterclock-timezone-resolution`

**What it tests:** Verifies timezone mapping is safe and handles invalid timezones gracefully.

**Why it matters:** Channel configs are editable. A bad tz string should not take down ChannelManager.

**Key assertions:**

- Valid timezones resolve correctly
- Invalid timezones fall back to UTC
- DST boundaries don't throw exceptions

### `masterclock-logging`

**What it tests:** Verifies timestamps for AsRunLogger are correct and consistent.

**Why it matters:** AsRunLogger will rely on this format for audit trails.

**Key assertions:**

- All timestamps are timezone-aware
- UTC and local timestamps are consistent
- Millisecond precision is maintained

### `masterclock-scheduler-alignment`

**What it tests:** Ensures schedule lookup logic won't give off-by-one bugs at slot boundaries. Also detects any use of non-MasterClock timestamps in scheduling logic and fails if found.

**Why it matters:** The guide channel and "Now Playing / Coming Up Next" banners depend on getting this right.

**Key assertions:**

- Boundary conditions work correctly
- DST edge cases are handled
- Off-by-one errors are prevented
- Uses MasterClock only (uses_masterclock_only)
- Naive timestamps rejected (naive_timestamp_rejected)

### `masterclock-stability`

**What it tests:** Stress-tests that repeated tz conversion doesn't leak memory or fall off a performance cliff.

**Why it matters:** ProgramDirector and ChannelManager are long-lived; we need to prove we don't keep creating new ZoneInfo objects forever.

**Key assertions:**

- Performance remains stable over time
- Memory usage doesn't grow unbounded
- Timezone caching works efficiently
- Peak calls per second (peak_calls_per_second)
- Min calls per second (min_calls_per_second)
- Final calls per second (final_calls_per_second)

We track these so we can catch regressions in timezone conversion or cache behavior over long runtimes.

### `masterclock-consistency`

**What it tests:** Makes sure different high-level components would see the "same now," not different shapes of time. Also verifies that timestamps from ProgramDirector and ChannelManager are tz-aware, serialize to ISO 8601 with offsets, and round-trip back into equivalent instants in UTC.

**Why it matters:** This catches any accidental direct datetime.utcnow() usage in one component vs clock.now_utc() in another.

**Key assertions:**

- All timestamps are timezone-aware
- Maximum skew between components is minimal
- No naive datetimes are returned
- Max skew seconds (max_skew_seconds)
- TZ info preserved (tzinfo_ok)
- Round-trip accuracy (roundtrip_ok)

### `masterclock-serialization`

**What it tests:** Makes sure we can safely serialize timestamps and round-trip them.

**Why it matters:** These timestamps will end up in logs, DB rows, API responses, and CLI output. If we lose timezone info on serialization, we create pain later.

**Key assertions:**

- Timezone information is preserved
- Round-trip accuracy is maintained
- ISO 8601 serialization works correctly

## JSON Output Fields

The test commands provide structured JSON output with the following key fields:

### Common Fields

- `test_passed`: Boolean indicating if the test passed
- `errors`: Array of error messages if the test failed
- `duration_seconds`: Time taken to run the test
- `timestamp`: When the test was run

### MasterClock-Specific Fields

- `uses_masterclock_only`: Confirms no direct datetime.now() usage
- `naive_timestamp_rejected`: Confirms naive timestamps are properly rejected
- `max_skew_seconds`: Maximum time skew between components
- `peak_calls_per_second`: Performance metrics for timezone operations
- `min_calls_per_second`: Minimum performance during test
- `final_calls_per_second`: Performance at end of test
- `tzinfo_ok`: Timezone information preservation
- `roundtrip_ok`: Serialization round-trip accuracy

### Performance Fields

- `iterations`: Number of test iterations performed
- `timezones_tested`: Number of timezones used in test
- `memory_usage_mb`: Memory usage during test
- `cache_hits`: Number of timezone cache hits
- `cache_misses`: Number of timezone cache misses

## Example JSON Output

```json
{
  "test_passed": true,
  "duration_seconds": 2.45,
  "timestamp": "2025-10-24T17:30:45.123456+00:00",
  "uses_masterclock_only": true,
  "naive_timestamp_rejected": true,
  "max_skew_seconds": 0.001,
  "peak_calls_per_second": 50000,
  "min_calls_per_second": 45000,
  "final_calls_per_second": 48000,
  "tzinfo_ok": true,
  "roundtrip_ok": true,
  "iterations": 10000,
  "timezones_tested": 10,
  "memory_usage_mb": 15.2,
  "cache_hits": 9500,
  "cache_misses": 500,
  "errors": []
}
```

## Failure Scenarios

### Common Failures

**Direct datetime.now() usage:**

```json
{
  "test_passed": false,
  "uses_masterclock_only": false,
  "errors": ["Component ChannelManager uses datetime.now() directly"]
}
```

**Naive timestamp acceptance:**

```json
{
  "test_passed": false,
  "naive_timestamp_rejected": false,
  "errors": ["Component accepted naive datetime without timezone info"]
}
```

**Performance degradation:**

```json
{
  "test_passed": false,
  "peak_calls_per_second": 1000,
  "min_calls_per_second": 500,
  "errors": ["Performance degraded below acceptable threshold"]
}
```

**Timezone conversion failure:**

```json
{
  "test_passed": false,
  "tzinfo_ok": false,
  "errors": ["Timezone information lost during conversion"]
}
```

## CI Integration

These tests are designed for CI integration to guarantee that RetroVue never regresses and starts using system time directly or loses timezone information. The tests should be run as part of the continuous integration pipeline to ensure MasterClock contracts remain enforced.

## Best Practices

### Regular Testing

```bash
# Daily functionality check
retrovue test masterclock

# Weekly performance check
retrovue test masterclock-performance --iterations 50000

# Monthly full test suite
retrovue test masterclock-monotonic && \
retrovue test masterclock-timezone-resolution && \
retrovue test masterclock-logging && \
retrovue test masterclock-scheduler-alignment && \
retrovue test masterclock-stability && \
retrovue test masterclock-consistency && \
retrovue test masterclock-serialization
```

### Performance Monitoring

```bash
# Baseline performance test
retrovue test masterclock-performance --iterations 10000 --json > baseline.json

# Compare with current performance
retrovue test masterclock-performance --iterations 10000 --json > current.json
```

### Integration Verification

```bash
# Verify integration patterns work
retrovue test masterclock-integration

# Test with different timezones
retrovue test masterclock-integration --timezone "Europe/London"
```

## See also

- [Runtime: Master clock](../runtime/MasterClock.md) - MasterClock implementation
- [Runtime: Schedule service](../runtime/schedule_service.md) - Uses MasterClock for scheduling
- [Runtime: Channel manager](../runtime/ChannelManager.md) - Uses MasterClock for playout
- [Contributing: Runtime](../contributing/CONTRIBUTING_RUNTIME.md) - Runtime development process
- [Tests: Broadcast day alignment](broadcast_day_alignment.md) - Broadcast day testing

_Document version: v0.1 · Last updated: 2025-10-24_
