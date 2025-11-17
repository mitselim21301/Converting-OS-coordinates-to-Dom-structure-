# Error Handling Module - Quick Reference Guide

## Location
`/mcp_server/platform/errors.py` (784 lines)

## Quick Start

### 1. Basic Exception Handling

```python
from mcp_server.platform import InputSimulationError

try:
    if click_failed:
        raise InputSimulationError(
            "Click failed at (100, 200)",
            context={'x': 100, 'y': 200}
        )
except InputSimulationError as e:
    print(e)  # Shows message + recovery suggestions
```

### 2. Automatic Retry

```python
from mcp_server.platform import retry_with_backoff, RetryConfig

@retry_with_backoff(config=RetryConfig(max_attempts=3))
def click(x, y):
    return simulator.click(x, y)
```

### 3. Graceful Degradation

```python
from mcp_server.platform import graceful_degradation

@graceful_degradation(fallback_value={'dpi': 96})
def get_dpi():
    return dpi_handler.get_system_dpi()  # Returns fallback on error
```

### 4. Operation with Recovery

```python
from mcp_server.platform import error_context

with error_context("click_operation", max_retries=3) as ctx:
    ctx.context_data['x'] = 100
    ctx.context_data['y'] = 200
    result = simulator.click(100, 200)
```

### 5. Error Reporting

```python
from mcp_server.platform import get_error_reporter

reporter = get_error_reporter(logger)
reporter.report_error(exception)
report = reporter.get_report()
reporter.export_json("errors.json")
```

---

## Exception Types

| Exception | Use Case | Key Suggestions |
|-----------|----------|-----------------|
| `InputSimulationError` | Click/keyboard failed | Window focus, permissions, delays |
| `DPIError` | DPI detection failed | Display settings, drivers, scaling |
| `WindowManagementError` | Window not found | Ensure exists, visibility, permissions |
| `CoordinateConversionError` | Coordinate transform failed | Check coordinate spaces, DPI values |
| `PlatformNotSupportedError` | Feature unavailable | Check platform, update version |
| `ResourceError` | Resource unavailable | Check availability, permissions |
| `TimeoutError` | Operation timed out | Increase timeout, check system load |
| `DisplayServerError` | X11/Wayland issue | Check server, environment variables |

---

## Common Patterns

### Pattern 1: Retry Transient Failures
```python
@retry_with_backoff(RetryConfig(max_attempts=3, initial_delay_ms=100))
def click_with_retry(x, y):
    return simulator.click(x, y)
```

### Pattern 2: Fallback Values
```python
@graceful_degradation(fallback_value=(1920, 1080))
def get_screen_size():
    return monitor.get_size()
```

### Pattern 3: Lifecycle Management
```python
with error_context("operation", max_retries=2) as ctx:
    ctx.context_data['key'] = value
    perform_operation()
    ctx.successful = True
```

### Pattern 4: Error Tracking
```python
reporter = get_error_reporter(logger)
try:
    operation()
except InputSimulationError as e:
    reporter.report_error(e)
    reporter.report_recovery(success=False)
```

### Pattern 5: Centralized Handling
```python
from mcp_server.platform import handle_error

try:
    operation()
except InputSimulationError as e:
    handle_error(e, "click_operation", logger)
```

---

## Configuration

### RetryConfig
```python
from mcp_server.platform import RetryConfig

config = RetryConfig(
    max_attempts=3,              # Max retry count
    initial_delay_ms=100,        # First retry delay
    max_delay_ms=5000,           # Maximum delay cap
    exponential_base=2.0,        # Backoff multiplier
    jitter=True                  # Add randomization
)
```

### Logging Setup
```python
from mcp_server.platform import setup_error_logging, LogLevel

logger = setup_error_logging(
    __name__,
    level=LogLevel.DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
)
```

---

## API Summary

### Exception Classes (8)
- `PlatformException`
- `InputSimulationError`
- `DPIError`
- `WindowManagementError`
- `CoordinateConversionError`
- `PlatformNotSupportedError`
- `ResourceError`
- `TimeoutError`
- `DisplayServerError`

### Decorators (2)
- `@retry_with_backoff()` - Auto-retry with exponential backoff
- `@graceful_degradation()` - Return fallback on error

### Context Managers (1)
- `error_context()` - Manage operation lifecycle with recovery

### Recovery Strategies (3)
- `RetryRecoveryStrategy` - Automatic retry
- `DegradationRecoveryStrategy` - Use fallback values
- `SkipRecoveryStrategy` - Skip operation

### Reporting (4)
- `ErrorMetrics` - Track error statistics
- `ErrorReporter` - Centralized error collection
- `get_error_reporter()` - Get global reporter
- `handle_error()` - Central error handling

### Utilities (7)
- `RetryConfig` - Configure retry parameters
- `LogLevel` - Logging level enum
- `setup_error_logging()` - Setup logger
- `ErrorContext` - Operation context tracking
- `RecoveryStrategy` - Base strategy class
- `error_context()` - Context manager
- More...

---

## Best Practices

1. **Use Specific Exceptions** - Choose the most appropriate exception type
2. **Provide Context** - Include relevant data in exception context
3. **Suggest Recovery** - Give users actionable recovery steps
4. **Enable Retries** - Use @retry_with_backoff for transient errors
5. **Monitor Errors** - Use ErrorReporter to track trends
6. **Degrade Gracefully** - Use @graceful_degradation for non-critical features
7. **Log Consistently** - Use setup_error_logging for standard format
8. **Export Metrics** - Regularly export and analyze error metrics

---

## Examples

See `/mcp_server/platform/error_handling_examples.py` for 9 complete examples:
1. Basic exception usage
2. Retry decorator
3. Graceful degradation
4. Error context manager
5. Recovery strategies
6. Error reporting
7. Logging standardization
8. Complete integration pattern
9. Exception serialization

---

## Documentation

- **Main Guide:** `/mcp_server/platform/ERROR_HANDLING.md` (598 lines)
- **Implementation Summary:** `/ERROR_HANDLING_SUMMARY.md` (694 lines)
- **Examples:** `/mcp_server/platform/error_handling_examples.py` (425 lines)

---

## Testing Example

```python
import unittest
from mcp_server.platform import InputSimulationError, retry_with_backoff, RetryConfig

class TestErrorHandling(unittest.TestCase):
    def test_exception_suggestions(self):
        error = InputSimulationError("Test error")
        self.assertTrue(len(error.recovery_suggestions) > 0)

    def test_retry_mechanism(self):
        attempts = []
        config = RetryConfig(max_attempts=3, initial_delay_ms=10)

        @retry_with_backoff(config=config)
        def test_func():
            attempts.append(1)
            if len(attempts) < 3:
                raise InputSimulationError("Retry")
            return True

        result = test_func()
        self.assertTrue(result)
        self.assertEqual(len(attempts), 3)
```

---

## Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `errors.py` | Core error handling implementation | 784 |
| `error_handling_examples.py` | 9 usage examples | 425 |
| `ERROR_HANDLING.md` | Comprehensive documentation | 598 |
| `__init__.py` | Module exports & integration | 208+ |

**Total Lines:** 2,501+
**Total Utilities:** 30+
**Exception Types:** 8
**Recovery Strategies:** 3

---

## Troubleshooting

### Too many retries?
```python
config = RetryConfig(max_attempts=1)  # Reduce attempts
```

### Slow recovery?
```python
config = RetryConfig(initial_delay_ms=50, exponential_base=1.5)
```

### Missing context?
```python
with error_context(...) as ctx:
    ctx.context_data['key'] = value  # Add data
```

### Recovery not applied?
```python
# Check if strategy can_recover() returns True for your error type
class CustomStrategy(RecoveryStrategy):
    def can_recover(self, error):
        return isinstance(error, YourErrorType)
```

---

## Integration Checklist

- [ ] Import error handling utilities into your module
- [ ] Replace generic Exception with specific exception types
- [ ] Add @retry_with_backoff to transient failure functions
- [ ] Add @graceful_degradation to non-critical functions
- [ ] Use error_context for critical operations
- [ ] Set up error reporting with ErrorReporter
- [ ] Configure logging with setup_error_logging
- [ ] Add context data to operations
- [ ] Test error handling paths
- [ ] Export and analyze error metrics

---

## Support

For detailed information, see:
- **Feature Details:** `ERROR_HANDLING.md`
- **Implementation Notes:** `ERROR_HANDLING_SUMMARY.md`
- **Working Examples:** `error_handling_examples.py`

---

**Last Updated:** November 17, 2025
**Status:** Production Ready
