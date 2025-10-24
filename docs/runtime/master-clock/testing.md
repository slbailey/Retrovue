# MasterClock Testing Guide

_How to test MasterClock using the Retrovue CLI._

**All runtime components MUST call MasterClock for time. Direct use of datetime.now() / datetime.utcnow() is considered a defect and will cause test failures.**

## Overview

The Retrovue CLI includes comprehensive testing commands for MasterClock that allow you to verify functionality, performance, and integration patterns directly from the command line.

## Basic Testing Commands

### Test MasterClock Functionality

```bash
# Basic functionality test
retrovue test masterclock

# Test with specific precision and timezone
retrovue test masterclock --precision microsecond --timezone "Europe/London"

# Get JSON output for programmatic use
retrovue test masterclock --json
```

### Test Event Scheduling

```bash
# Test event scheduling functionality
# included for forward-compatibility; currently validates timestamp consistency only.
retrovue test masterclock-events

# Get JSON output
retrovue test masterclock-events --json
```

### Test Performance

```bash
# Basic performance test
retrovue test masterclock-performance

# High-load performance test
retrovue test masterclock-performance --iterations 50000 --timezones 20

# Get JSON output for benchmarking
retrovue test masterclock-performance --json
```

### Test Integration Patterns

```bash
# Test integration with other components
retrovue test masterclock-integration

# Get JSON output
retrovue test masterclock-integration --json
```

## Production Validation Tests

### Test Time Monotonicity

```bash
# Test that time doesn't "run backward" and seconds_since() is never negative
retrovue test masterclock-monotonic

# Test with more iterations
retrovue test masterclock-monotonic --iterations 5000

# Get JSON output
retrovue test masterclock-monotonic --json
```

### Test Timezone Resolution

```bash
# Test timezone mapping is safe and handles invalid timezones gracefully
retrovue test masterclock-timezone-resolution

# Test with specific timezones
retrovue test masterclock-timezone-resolution --timezones "America/New_York,Europe/London,Invalid/Zone"

# Get JSON output
retrovue test masterclock-timezone-resolution --json
```

### Test Logging Timestamps

```bash
# Test timestamps for AsRunLogger are correct and consistent
retrovue test masterclock-logging

# Get JSON output
retrovue test masterclock-logging --json
```

### Test Scheduler Alignment

```bash
# Test schedule lookup logic won't give off-by-one bugs at slot boundaries
retrovue test masterclock-scheduler-alignment

# Get JSON output
retrovue test masterclock-scheduler-alignment --json
```

### Test Stability

```bash
# Stress-test that repeated tz conversion doesn't leak memory or fall off a performance cliff
retrovue test masterclock-stability

# Test with more iterations
retrovue test masterclock-stability --iterations 50000

# Test for specified duration
retrovue test masterclock-stability --minutes 5

# Get JSON output
retrovue test masterclock-stability --json
```

### Test Consistency

```bash
# Test that different high-level components would see the "same now," not different shapes of time
retrovue test masterclock-consistency

# Get JSON output
retrovue test masterclock-consistency --json
```

### Test Serialization

```bash
# Test that we can safely serialize timestamps and round-trip them
retrovue test masterclock-serialization

# Get JSON output
retrovue test masterclock-serialization --json
```

## Test Descriptions

### Production Validation Tests Explained

#### `masterclock-monotonic`

**What it tests:** Proves time doesn't "run backward" and seconds_since() is never negative.
**Why it matters:** ChannelManager uses seconds_since() to compute mid-program offsets. We need non-negative offsets.
**Key assertions:**

- Time never goes backward between consecutive calls
- seconds_since() with future timestamps returns 0.0
- seconds_since() with past timestamps returns positive values

#### `masterclock-timezone-resolution`

**What it tests:** Verifies timezone mapping is safe and handles invalid timezones gracefully.
**Why it matters:** Channel configs are editable. A bad tz string should not take down ChannelManager.
**Key assertions:**

- Valid timezones resolve correctly
- Invalid timezones fall back to UTC
- DST boundaries don't throw exceptions

#### `masterclock-logging`

**What it tests:** Verifies timestamps for AsRunLogger are correct and consistent.
**Why it matters:** AsRunLogger will rely on this format for audit trails.
**Key assertions:**

- All timestamps are timezone-aware
- UTC and local timestamps are consistent
- Millisecond precision is maintained

#### `masterclock-scheduler-alignment`

**What it tests:** Ensures schedule lookup logic won't give off-by-one bugs at slot boundaries. Also detects any use of non-MasterClock timestamps in scheduling logic and fails if found.
**Why it matters:** The guide channel and "Now Playing / Coming Up Next" banners depend on getting this right.
**Key assertions:**

- Boundary conditions work correctly
- DST edge cases are handled
- Off-by-one errors are prevented
- Uses MasterClock only (uses_masterclock_only)
- Naive timestamps rejected (naive_timestamp_rejected)

#### `masterclock-stability`

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

#### `masterclock-consistency`

**What it tests:** Makes sure different high-level components would see the "same now," not different shapes of time. Also verifies that timestamps from ProgramDirector and ChannelManager are tz-aware, serialize to ISO 8601 with offsets, and round-trip back into equivalent instants in UTC.
**Why it matters:** This catches any accidental direct datetime.utcnow() usage in one component vs clock.now_utc() in another.
**Key assertions:**

- All timestamps are timezone-aware
- Maximum skew between components is minimal
- No naive datetimes are returned
- Max skew seconds (max_skew_seconds)
- TZ info preserved (tzinfo_ok)
- Round-trip accuracy (roundtrip_ok)

#### `masterclock-serialization`

**What it tests:** Makes sure we can safely serialize timestamps and round-trip them.
**Why it matters:** These timestamps will end up in logs, DB rows, API responses, and CLI output. If we lose timezone info on serialization, we create pain later.
**Key assertions:**

- Timezone information is preserved
- Round-trip accuracy is maintained
- ISO 8601 serialization works correctly

## Running the Full Test Suite

### Run All Tests

```bash
# Run all MasterClock tests using pytest
retrovue test run-tests

# Run with verbose output
retrovue test run-tests --verbose

# Run specific test types
retrovue test run-tests --type unit
retrovue test run-tests --type performance
retrovue test run-tests --type integration
```

### Test Output Formats

All test commands support JSON output for programmatic use:

```bash
# Get JSON output from any test command
retrovue test masterclock --json
retrovue test masterclock-performance --json
retrovue test run-tests --json
```

## Example Usage Scenarios

### 1. Quick Functionality Check

```bash
# Verify MasterClock is working correctly
retrovue test masterclock
```

**Expected Output:**

```
🕐 MasterClock Test Results
========================================
Precision: millisecond
Test Timezone: America/New_York

📅 Time Operations:
  UTC Time: 2024-01-15 17:30:45.123456+00:00
  Local Time (America/New_York): 2024-01-15 12:30:45.123456-05:00

🌍 Timezone Information:
  Name: America/New_York
  Offset: -1 day, 19:00:00
  DST: 0:00:00

⚡ Performance Test:
  1000 UTC queries in 0.0045 seconds (222222 queries/sec)

🔄 Timezone Conversion Test:
  UTC: 2024-01-15 12:00:00+00:00
  America/New_York: 2024-01-15 07:00:00-05:00

✅ MasterClock test completed successfully!
```

### 2. Performance Benchmarking

```bash
# Run performance benchmark
retrovue test masterclock-performance --iterations 100000
```

**Expected Output:**

```
⚡ MasterClock Performance Test
========================================
Iterations: 100,000
Timezones: 10

🕐 UTC Query Performance:
  Duration: 0.1234 seconds
  Queries/sec: 810,372

🌍 Timezone Conversion Performance:
  Duration: 0.4567 seconds
  Conversions/sec: 218,890

📅 Event Scheduling Performance:
  Events scheduled: 1,000
  Duration: 0.0123 seconds
  Events/sec: 81,300

💾 Cache Information:
  Cached timezones: 10
  Scheduled events: 1,000

✅ Performance test completed!
```

### 3. Integration Testing

```bash
# Test integration patterns
retrovue test masterclock-integration
```

**Expected Output:**

```
🔗 MasterClock Integration Test
========================================
📅 ScheduleService Integration:
  Station time: 2024-01-15 17:30:45.123456+00:00
  Channel time (NY): 2024-01-15 12:30:45.123456-05:00
  Program offset: 1800.00 seconds

📺 ChannelManager Integration:
  Viewer join time: 2024-01-15 17:30:45.123456+00:00
  Playback offset: 1800.00 seconds

🎛️ ProgramDirector Integration:
  Emergency scheduled: 2024-01-15 17:31:15.123456+00:00
  Scheduled events: 1

📝 AsRunLogger Integration:
  playout_started: 2024-01-15T17:30:45.123456+00:00
  commercial_break: 2024-01-15T17:30:45.123456+00:00
  playout_resumed: 2024-01-15T17:30:45.123456+00:00

✅ Integration test completed!
```

## Advanced Testing

### Custom Test Scenarios

```bash
# Test with different precision levels
retrovue test masterclock --precision second
retrovue test masterclock --precision millisecond
retrovue test masterclock --precision microsecond

# Test with different timezones
retrovue test masterclock --timezone "Europe/London"
retrovue test masterclock --timezone "Asia/Tokyo"
retrovue test masterclock --timezone "Australia/Sydney"
```

### Performance Testing Variations

```bash
# Light performance test
retrovue test masterclock-performance --iterations 1000 --timezones 5

# Heavy performance test
retrovue test masterclock-performance --iterations 100000 --timezones 30

# Memory-intensive test
retrovue test masterclock-performance --iterations 50000 --timezones 50
```

### Automated Testing

```bash
# Run full test suite with JSON output
retrovue test run-tests --json > test_results.json

# Run specific test categories
retrovue test run-tests --type unit --verbose
retrovue test run-tests --type performance --verbose
retrovue test run-tests --type integration --verbose
```

## Troubleshooting

### Common Issues

**Command Not Found:**

```bash
# Make sure you're in the project root
cd /path/to/retrovue
python -m retrovue.cli test masterclock
```

**Import Errors:**

```bash
# Install dependencies
pip install -r requirements.txt

# Run from project root
python -m retrovue.cli test masterclock
```

**Performance Issues:**

```bash
# Test with fewer iterations
retrovue test masterclock-performance --iterations 1000

# Check system resources
retrovue test masterclock-performance --iterations 10000
```

### Debug Mode

```bash
# Run with verbose output
retrovue test run-tests --verbose

# Check specific functionality
retrovue test masterclock --timezone "Invalid/Timezone"
```

## Integration with CI/CD

### Automated Testing Script

```bash
#!/bin/bash
# test_masterclock.sh

echo "Running MasterClock tests..."

# Basic functionality
retrovue test masterclock --json > basic_test.json

# Performance test
retrovue test masterclock-performance --iterations 10000 --json > performance_test.json

# Full test suite
retrovue test run-tests --json > full_test.json

echo "Tests completed. Check JSON files for results."
```

### Continuous Integration

```yaml
# .github/workflows/test-masterclock.yml
name: MasterClock Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run MasterClock tests
        run: |
          retrovue test masterclock --json
          retrovue test masterclock-performance --json
          retrovue test run-tests --json
```

## Best Practices

### Regular Testing

```bash
# Daily functionality check
retrovue test masterclock

# Weekly performance check
retrovue test masterclock-performance --iterations 50000

# Monthly full test suite
retrovue test run-tests --verbose
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

## Conclusion

The Retrovue CLI provides comprehensive testing capabilities for MasterClock that allow you to:

- **Verify functionality** with basic tests
- **Measure performance** with benchmark tests
- **Test integration** with component simulation
- **Run full test suites** with pytest integration
- **Get structured output** with JSON formatting

Use these commands regularly to ensure MasterClock is working correctly and performing well in your RetroVue deployment.

## Quick Reference

### Common Use Cases

```bash
# Daily functionality check
retrovue test masterclock

# Production readiness validation
retrovue test masterclock-monotonic
retrovue test masterclock-timezone-resolution
retrovue test masterclock-consistency

# Performance validation
retrovue test masterclock-stability --iterations 10000

# Full validation suite
retrovue test masterclock-monotonic && \
retrovue test masterclock-timezone-resolution && \
retrovue test masterclock-logging && \
retrovue test masterclock-scheduler-alignment && \
retrovue test masterclock-stability && \
retrovue test masterclock-consistency && \
retrovue test masterclock-serialization
```

### Test Command Summary

| Command                           | Purpose               | Key Flags                   |
| --------------------------------- | --------------------- | --------------------------- |
| `masterclock-monotonic`           | Time monotonicity     | `--iterations`              |
| `masterclock-timezone-resolution` | Timezone safety       | `--timezones`               |
| `masterclock-logging`             | Timestamp consistency | None                        |
| `masterclock-scheduler-alignment` | Boundary conditions   | None                        |
| `masterclock-stability`           | Performance stability | `--iterations`, `--minutes` |
| `masterclock-consistency`         | Component consistency | None                        |
| `masterclock-serialization`       | Serialization safety  | None                        |

**Note:** The `masterclock-events` command is forward-looking and not part of v0.1 behavior (MasterClock does not actually schedule events yet — it only timestamps).

_Document version: v0.1 · Last updated: 2025-10-24_
