# MasterClock Testing - Quick Reference

_Quick reference for testing MasterClock with the Retrovue CLI._

## 🚀 Quick Start

```bash
# Basic functionality test
retrovue test masterclock

# Performance test
retrovue test masterclock-performance

# Full test suite
retrovue test run-tests
```

## 📋 Command Reference

### Basic Testing

```bash
retrovue test masterclock                    # Basic functionality test
retrovue test masterclock --json             # JSON output
retrovue test masterclock --precision second # Different precision
retrovue test masterclock --timezone "Europe/London" # Different timezone
```

### Event Testing

```bash
retrovue test masterclock-events             # Test event scheduling
                                             # (intended for forward compatibility.  Currently only validates timestamp)
retrovue test masterclock-events --json      # JSON output
```

### Performance Testing

```bash
retrovue test masterclock-performance                    # Basic performance test
retrovue test masterclock-performance --iterations 50000 # High-load test
retrovue test masterclock-performance --timezones 20    # Many timezones
retrovue test masterclock-performance --json            # JSON output
```

### Integration Testing

```bash
retrovue test masterclock-integration        # Test component integration
retrovue test masterclock-integration --json # JSON output
```

### Full Test Suite

```bash
retrovue test run-tests                      # Run all tests
retrovue test run-tests --verbose            # Verbose output
retrovue test run-tests --type unit          # Unit tests only
retrovue test run-tests --type performance   # Performance tests only
retrovue test run-tests --type integration   # Integration tests only
retrovue test run-tests --json               # JSON output
```

## 🎯 Common Use Cases

### Daily Health Check

```bash
retrovue test masterclock
```

### Performance Benchmark

```bash
retrovue test masterclock-performance --iterations 100000
```

### Integration Verification

```bash
retrovue test masterclock-integration
```

### Full Regression Test

```bash
retrovue test run-tests --verbose
```

### CI/CD Integration

```bash
retrovue test run-tests --json > test_results.json
```

## 🔧 Troubleshooting

### Command Not Found

```bash
# Run from project root
cd /path/to/retrovue
python -m retrovue.cli test masterclock
```

### Performance Issues

```bash
# Reduce test load
retrovue test masterclock-performance --iterations 1000
```

### Debug Mode

```bash
# Verbose output
retrovue test run-tests --verbose
```

## 📊 Output Examples

### Basic Test Output

```
🕐 MasterClock Test Results
========================================
Precision: millisecond
Test Timezone: America/New_York

📅 Time Operations:
  UTC Time: 2024-01-15 17:30:45.123456+00:00
  Local Time (America/New_York): 2024-01-15 12:30:45.123456-05:00

⚡ Performance Test:
  1000 UTC queries in 0.0045 seconds (222222 queries/sec)

✅ MasterClock test completed successfully!
```

### Performance Test Output

```
⚡ MasterClock Performance Test
========================================
Iterations: 10,000
Timezones: 10

🕐 UTC Query Performance:
  Duration: 0.1234 seconds
  Queries/sec: 81,037

🌍 Timezone Conversion Performance:
  Duration: 0.4567 seconds
  Conversions/sec: 21,889

✅ Performance test completed!
```

## 🏃‍♂️ Quick Commands

| Command                                        | Purpose             | Output         |
| ---------------------------------------------- | ------------------- | -------------- |
| `retrovue test masterclock`                    | Basic functionality | Human-readable |
| `retrovue test masterclock --json`             | Basic functionality | JSON           |
| `retrovue test masterclock-performance`        | Performance test    | Human-readable |
| `retrovue test masterclock-performance --json` | Performance test    | JSON           |
| `retrovue test run-tests`                      | Full test suite     | Human-readable |
| `retrovue test run-tests --json`               | Full test suite     | JSON           |

## 🎛️ Options Reference

### MasterClock Test Options

- `--precision`: `second`, `millisecond`, `microsecond`
- `--timezone`: Any valid timezone name (e.g., `"America/New_York"`)
- `--json`: JSON output format

### Performance Test Options

- `--iterations`: Number of test iterations (default: 10000)
- `--timezones`: Number of timezones to test (default: 10)
- `--json`: JSON output format

### Test Suite Options

- `--type`: `all`, `unit`, `performance`, `integration`
- `--verbose`: Verbose output
- `--json`: JSON output format

## 🚨 Error Codes

| Exit Code | Meaning               |
| --------- | --------------------- |
| 0         | Success               |
| 1         | Test failure or error |
| 2         | Invalid arguments     |

## 💡 Tips

1. **Start Simple**: Begin with `retrovue test masterclock`
2. **Check Performance**: Use `retrovue test masterclock-performance` regularly
3. **Verify Integration**: Run `retrovue test masterclock-integration` after changes
4. **Use JSON**: Add `--json` for programmatic processing
5. **Monitor Performance**: Track performance metrics over time
6. **Test Different Timezones**: Verify timezone handling works correctly
7. **Run Full Suite**: Use `retrovue test run-tests` for comprehensive testing
