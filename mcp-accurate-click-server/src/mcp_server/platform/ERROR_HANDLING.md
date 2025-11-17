# Error Handling Module Documentation

## Overview

The error handling module provides comprehensive error management, recovery strategies, retry logic, and error reporting for the MCP accurate click server platform layer. It ensures robust operation across Windows, Linux, and macOS platforms.

## Features

### 1. Platform-Specific Exception Classes

The module defines 8 specialized exception types, each with:
- Descriptive error codes
- Custom error messages
- Automatic recovery suggestions
- Context data for debugging
- JSON serialization support

#### Exception Hierarchy

```
PlatformException (base)
├── InputSimulationError      # Mouse/keyboard failures
├── DPIError                  # Scaling/DPI issues
├── WindowManagementError     # Window detection failures
├── CoordinateConversionError # Coordinate space issues
├── PlatformNotSupportedError # Unsupported features
├── ResourceError             # Resource access failures
├── TimeoutError              # Operation timeouts
└── DisplayServerError        # X11/Wayland issues
```

### 2. Retry Logic with Exponential Backoff

Automatic retry mechanism with configurable parameters:

```python
from mcp_server.platform import RetryConfig, retry_with_backoff

# Configure retry strategy
retry_config = RetryConfig(
    max_attempts=3,                    # Try up to 3 times
    initial_delay_ms=100,              # Start with 100ms delay
    max_delay_ms=5000,                 # Cap delay at 5 seconds
    exponential_base=2.0,              # Double delay each attempt
    jitter=True                        # Add randomization
)

# Use as decorator
@retry_with_backoff(config=retry_config)
def click(x, y):
    # Automatically retries on PlatformException
    pass
```

### 3. Error Recovery Strategies

Pluggable recovery strategies for automatic error handling:

- **RetryRecoveryStrategy**: Automatic retry with exponential backoff
- **DegradationRecoveryStrategy**: Use fallback values gracefully
- **SkipRecoveryStrategy**: Skip non-critical operations

```python
from mcp_server.platform import (
    error_context,
    RetryRecoveryStrategy,
    DegradationRecoveryStrategy
)

strategies = [
    RetryRecoveryStrategy(),
    DegradationRecoveryStrategy(),
]

with error_context("operation_name", recovery_strategies=strategies) as ctx:
    # Operation with automatic error recovery
    pass
```

### 4. Graceful Degradation

Handle failures gracefully with fallback values:

```python
from mcp_server.platform import graceful_degradation

@graceful_degradation(
    fallback_value={'width': 1920, 'height': 1080},
    log_error=True
)
def get_screen_resolution():
    # Returns fallback on error instead of raising
    pass
```

### 5. Error Context Managers

Manage operation lifecycle with automatic recovery:

```python
from mcp_server.platform import error_context

with error_context(
    operation_name="window_detection",
    recovery_strategies=[...],
    logger=logger,
    max_retries=3
) as ctx:
    # Track operation context
    ctx.context_data['window_title'] = "Chrome"
    ctx.context_data['screen_size'] = (1920, 1080)

    # Operation code here
    # Errors automatically trigger recovery strategies
```

### 6. Error Reporting and Metrics

Centralized error tracking and metrics collection:

```python
from mcp_server.platform import get_error_reporter

reporter = get_error_reporter(logger)

# Report errors
reporter.report_error(exception)

# Track recovery attempts
reporter.report_recovery(success=True)

# Get metrics
report = reporter.get_report()
print(f"Total errors: {report['metrics']['total_errors']}")
print(f"Recovery rate: {report['metrics']['recovery_success_rate']:.1%}")

# Export to JSON
reporter.export_json("error_report.json")
```

### 7. Standardized Logging

Consistent logging format across the platform layer:

```python
from mcp_server.platform import setup_error_logging, LogLevel

logger = setup_error_logging(__name__, LogLevel.INFO)

logger.debug("Debug information")
logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error message")
```

Log format: `[timestamp] - [logger] - [level] - [file:line] - [message]`

### 8. Detailed Error Messages with Solutions

Each exception includes:

```python
from mcp_server.platform import InputSimulationError

error = InputSimulationError(
    "Failed to click at (100, 200)",
    context={'x': 100, 'y': 200},
    recovery_suggestions=[
        "Ensure target window is focused",
        "Check pynput installation",
        "Increase click delay"
    ]
)

print(error)  # Prints formatted message with suggestions
error_dict = error.to_dict()  # JSON-serializable dict with full context
```

## Usage Patterns

### Pattern 1: Basic Exception Handling

```python
from mcp_server.platform import InputSimulationError

try:
    # Input simulation code
    if failed:
        raise InputSimulationError(
            "Click failed",
            context={'x': x, 'y': y}
        )
except InputSimulationError as e:
    print(f"Error: {e}")
    for suggestion in e.recovery_suggestions:
        print(f"  - {suggestion}")
```

### Pattern 2: Automatic Retry

```python
from mcp_server.platform import retry_with_backoff, RetryConfig

config = RetryConfig(max_attempts=3, initial_delay_ms=100)

@retry_with_backoff(config=config)
def click_element(x, y):
    # Automatically retries on platform errors
    return simulator.click(x, y)
```

### Pattern 3: Graceful Degradation

```python
from mcp_server.platform import graceful_degradation

@graceful_degradation(
    fallback_value={'dpi_x': 96, 'dpi_y': 96},
    log_error=True
)
def get_monitor_dpi():
    # Returns fallback DPI if detection fails
    return dpi_handler.get_system_dpi()
```

### Pattern 4: Operation with Recovery Context

```python
from mcp_server.platform import error_context, RetryRecoveryStrategy

with error_context(
    operation_name="click_operation",
    recovery_strategies=[RetryRecoveryStrategy()],
    max_retries=3
) as ctx:
    # Add context data
    ctx.context_data['coordinates'] = (x, y)
    ctx.context_data['timeout'] = 5000

    # Operation code
    result = simulator.click(x, y)
    ctx.successful = True
```

### Pattern 5: Error Handling and Reporting

```python
from mcp_server.platform import handle_error, get_error_reporter, InputSimulationError

reporter = get_error_reporter(logger)

try:
    perform_operation()
except InputSimulationError as e:
    # Handle with reporting
    error_info = handle_error(
        e,
        operation_name="click",
        logger=logger,
        suppress=False  # Set to True to suppress and return error info
    )
```

## Exception Reference

### InputSimulationError

**Use when:** Mouse/keyboard input simulation fails

**Recovery suggestions:**
- Ensure input simulator is properly initialized
- Verify mouse/keyboard permissions
- Try reducing click speed or increasing delays
- Ensure window is focused before input

### DPIError

**Use when:** DPI/scaling detection or conversion fails

**Recovery suggestions:**
- Verify DPI settings in system display properties
- Check for multiple monitors with different DPI
- Update graphics drivers
- Try disabling display scaling

### WindowManagementError

**Use when:** Window detection or management fails

**Recovery suggestions:**
- Ensure target window exists and is visible
- Check window permissions
- Try focusing window manually first
- Verify window handle is still valid

### CoordinateConversionError

**Use when:** Coordinate space conversion fails

**Recovery suggestions:**
- Verify source and destination coordinate spaces
- Check DPI scaling values
- Ensure coordinates are within valid ranges
- Check for conflicting scaling transformations

### PlatformNotSupportedError

**Use when:** Platform or feature is not supported

**Recovery suggestions:**
- Check supported platforms
- Review feature requirements
- Update to latest version
- Report issue with platform details

### ResourceError

**Use when:** Platform resources cannot be accessed

**Recovery suggestions:**
- Check resource availability
- Verify permissions and access rights
- Clear unused resources
- Restart application or service

### TimeoutError

**Use when:** Operation exceeds time limit

**Recovery suggestions:**
- Increase timeout value
- Check system load and performance
- Verify network connectivity if applicable
- Try operation again

### DisplayServerError

**Use when:** Display server (X11, Wayland) issues occur

**Recovery suggestions:**
- Verify display server is running
- Check DISPLAY/WAYLAND_DISPLAY environment variables
- Restart display server if necessary
- Check for permission issues

## Configuration

### RetryConfig Parameters

```python
from mcp_server.platform import RetryConfig

config = RetryConfig(
    max_attempts=3,           # Maximum retry attempts
    initial_delay_ms=100,     # Initial delay in milliseconds
    max_delay_ms=5000,        # Maximum delay cap
    exponential_base=2.0,     # Exponential growth factor
    jitter=True               # Add random variance to delay
)
```

### LogLevel Options

```python
from mcp_server.platform import LogLevel, setup_error_logging

logger = setup_error_logging(
    __name__,
    level=LogLevel.DEBUG      # DEBUG, INFO, WARNING, ERROR, CRITICAL
)
```

## Best Practices

1. **Use Specific Exceptions**: Choose the most specific exception type for your error condition

2. **Provide Context**: Include relevant data in the `context` parameter for debugging

3. **Set Recovery Suggestions**: Help users solve problems with specific recovery steps

4. **Enable Retries**: Use `@retry_with_backoff` for transient failures

5. **Monitor Errors**: Use `ErrorReporter` to track error trends

6. **Degrade Gracefully**: Use `@graceful_degradation` for non-critical features

7. **Log Consistently**: Use `setup_error_logging` for standardized logs

8. **Export Metrics**: Regularly export error metrics for analysis

## Examples

### Complete Click Operation with Error Handling

```python
from mcp_server.platform import (
    error_context,
    RetryRecoveryStrategy,
    DegradationRecoveryStrategy,
    InputSimulationError,
    setup_error_logging,
    get_error_reporter,
)

logger = setup_error_logging(__name__)
reporter = get_error_reporter(logger)

def click_with_error_handling(x: int, y: int) -> bool:
    strategies = [
        RetryRecoveryStrategy(),
        DegradationRecoveryStrategy(),
    ]

    try:
        with error_context(
            operation_name=f"click_at_{x}_{y}",
            recovery_strategies=strategies,
            logger=logger,
            max_retries=3
        ) as ctx:
            ctx.context_data['coordinates'] = (x, y)
            ctx.context_data['button'] = 'left'

            # Perform click
            return simulator.click(x, y)

    except InputSimulationError as e:
        reporter.report_error(e)
        logger.error(f"Click failed: {e}")
        return False

# Usage
success = click_with_error_handling(100, 200)
if success:
    print("Click successful")
else:
    # Check error metrics
    report = reporter.get_report()
    print(f"Errors: {report['metrics']['total_errors']}")
```

### Monitor and Export Metrics

```python
from mcp_server.platform import get_error_reporter, setup_error_logging

logger = setup_error_logging(__name__)
reporter = get_error_reporter(logger)

# ... perform operations that may generate errors ...

# Export metrics
reporter.export_json("error_metrics.json")

# Get summary
report = reporter.get_report()
print(f"Total errors: {report['metrics']['total_errors']}")
print(f"Success rate: {report['metrics']['recovery_success_rate']:.1%}")
```

## Testing Error Handling

### Unit Test Example

```python
import unittest
from mcp_server.platform import (
    InputSimulationError,
    retry_with_backoff,
    RetryConfig,
)

class TestErrorHandling(unittest.TestCase):
    def test_exception_with_suggestions(self):
        error = InputSimulationError("Test error")
        self.assertIsNotNone(error.recovery_suggestions)
        self.assertTrue(len(error.recovery_suggestions) > 0)

    def test_retry_logic(self):
        attempt_count = 0

        config = RetryConfig(max_attempts=3, initial_delay_ms=10)

        @retry_with_backoff(config=config)
        def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise InputSimulationError("Test")
            return True

        result = failing_function()
        self.assertTrue(result)
        self.assertEqual(attempt_count, 3)
```

## Troubleshooting

### Issue: Too Many Retries

**Solution:** Reduce `max_attempts` in `RetryConfig`:

```python
config = RetryConfig(max_attempts=1)  # Disable retries if not needed
```

### Issue: Slow Error Recovery

**Solution:** Increase `initial_delay_ms` and adjust `exponential_base`:

```python
config = RetryConfig(
    initial_delay_ms=50,
    exponential_base=1.5
)
```

### Issue: Missing Error Context

**Solution:** Add context data to `ErrorContext`:

```python
with error_context(...) as ctx:
    ctx.context_data['important_value'] = value
```

### Issue: Recovery Not Applied

**Solution:** Ensure recovery strategy `can_recover()` returns True:

```python
class CustomRecoveryStrategy(RecoveryStrategy):
    def can_recover(self, error):
        return isinstance(error, SpecificErrorType)
```

## Module Exports

### Exception Classes
- `PlatformException`
- `InputSimulationError`
- `DPIError`
- `WindowManagementError`
- `CoordinateConversionError`
- `PlatformNotSupportedError`
- `ResourceError`
- `TimeoutError`
- `DisplayServerError`

### Configuration
- `RetryConfig`

### Decorators
- `retry_with_backoff`
- `graceful_degradation`

### Recovery Strategies
- `RecoveryStrategy` (abstract base)
- `RetryRecoveryStrategy`
- `DegradationRecoveryStrategy`
- `SkipRecoveryStrategy`

### Context Management
- `ErrorContext`
- `error_context`

### Reporting
- `ErrorMetrics`
- `ErrorReporter`
- `get_error_reporter`
- `handle_error`

### Logging
- `LogLevel`
- `setup_error_logging`

## Performance Considerations

1. **Logging Overhead**: Standardized logging adds minimal overhead
2. **Retry Delays**: Exponential backoff ensures system stability
3. **Error Collection**: Error history is limited to 10 recent errors
4. **Memory**: Error metrics are kept in memory for monitoring

## Security Considerations

1. **Error Information**: Error messages don't expose sensitive paths
2. **Recovery Suggestions**: Generic suggestions avoid revealing implementation details
3. **JSON Export**: Sanitize exported error reports before sharing
4. **Log Files**: Secure log files to prevent unauthorized access

## Future Enhancements

- Remote error reporting to monitoring systems
- Machine learning-based error pattern detection
- Automatic error signature grouping
- Integration with APM (Application Performance Monitoring) tools
- Custom error handlers registry
- Error notification webhooks
