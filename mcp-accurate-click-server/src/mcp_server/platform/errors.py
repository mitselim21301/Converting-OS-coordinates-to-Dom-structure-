"""
Comprehensive Error Handling Module for Platform-Specific Operations

Provides platform-specific exception classes, error recovery strategies, retry logic,
error reporting utilities, graceful degradation handlers, and logging standardization
for cross-platform MCP accurate click server.

Features:
- Platform-specific exception hierarchy
- Exponential backoff retry logic
- Graceful degradation handlers
- Detailed error messages with solutions
- Error context managers
- Error reporting and metrics
- Logging standardization
- Recovery strategies
"""

import logging
import time
import traceback
import functools
from typing import Optional, Callable, Any, Dict, List, Tuple, Type
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from contextlib import contextmanager
from datetime import datetime
import json


# ==================== Logging Configuration ====================

class LogLevel(Enum):
    """Standardized logging levels."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def setup_error_logging(logger_name: str, level: LogLevel = LogLevel.INFO) -> logging.Logger:
    """
    Set up standardized error logging.

    Args:
        logger_name: Logger name (typically __name__)
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level.value)

    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# ==================== Exception Hierarchy ====================

class PlatformException(Exception):
    """
    Base exception for all platform-related errors.

    Attributes:
        message: Error message
        error_code: Platform-specific error code
        context: Additional error context
        recovery_suggestions: List of recovery suggestions
    """

    error_code = "PLATFORM_ERROR"

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        recovery_suggestions: Optional[List[str]] = None
    ):
        """
        Initialize platform exception.

        Args:
            message: Error message
            error_code: Platform-specific error code
            context: Additional context
            recovery_suggestions: Suggestions for recovery
        """
        self.message = message
        self.error_code = error_code or self.error_code
        self.context = context or {}
        self.recovery_suggestions = recovery_suggestions or []
        self.timestamp = datetime.now()
        super().__init__(message)

    def __str__(self) -> str:
        """Return formatted error string."""
        msg = f"[{self.error_code}] {self.message}"
        if self.recovery_suggestions:
            msg += "\n\nSuggestions:\n" + "\n".join(f"  - {s}" for s in self.recovery_suggestions)
        return msg

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'context': self.context,
            'recovery_suggestions': self.recovery_suggestions,
            'timestamp': self.timestamp.isoformat(),
            'traceback': traceback.format_exc()
        }


class InputSimulationError(PlatformException):
    """Error during input simulation (mouse/keyboard)."""

    error_code = "INPUT_SIMULATION_ERROR"

    def __init__(self, message: str, **kwargs):
        suggestions = [
            "Check if input simulator is properly initialized",
            "Verify mouse/keyboard permissions",
            "Try reducing click speed or increasing delays",
            "Ensure window is focused before input"
        ]
        kwargs.setdefault('recovery_suggestions', []).extend(suggestions)
        super().__init__(message, **kwargs)


class DPIError(PlatformException):
    """Error in DPI/scaling detection or conversion."""

    error_code = "DPI_ERROR"

    def __init__(self, message: str, **kwargs):
        suggestions = [
            "Verify DPI settings in system display properties",
            "Check for multiple monitors with different DPI",
            "Update graphics drivers",
            "Try disabling display scaling"
        ]
        kwargs.setdefault('recovery_suggestions', []).extend(suggestions)
        super().__init__(message, **kwargs)


class WindowManagementError(PlatformException):
    """Error in window detection or management."""

    error_code = "WINDOW_MANAGEMENT_ERROR"

    def __init__(self, message: str, **kwargs):
        suggestions = [
            "Ensure target window exists and is visible",
            "Check window permissions",
            "Try focusing window manually first",
            "Verify window handle is still valid"
        ]
        kwargs.setdefault('recovery_suggestions', []).extend(suggestions)
        super().__init__(message, **kwargs)


class CoordinateConversionError(PlatformException):
    """Error in coordinate space conversion."""

    error_code = "COORDINATE_CONVERSION_ERROR"

    def __init__(self, message: str, **kwargs):
        suggestions = [
            "Verify source and destination coordinate spaces",
            "Check DPI scaling values",
            "Ensure coordinates are within valid ranges",
            "Check for conflicting scaling transformations"
        ]
        kwargs.setdefault('recovery_suggestions', []).extend(suggestions)
        super().__init__(message, **kwargs)


class PlatformNotSupportedError(PlatformException):
    """Platform or feature not supported."""

    error_code = "PLATFORM_NOT_SUPPORTED"

    def __init__(self, message: str, **kwargs):
        suggestions = [
            "Check supported platforms",
            "Review feature requirements",
            "Update to latest version",
            "Report issue with platform details"
        ]
        kwargs.setdefault('recovery_suggestions', []).extend(suggestions)
        super().__init__(message, **kwargs)


class ResourceError(PlatformException):
    """Error accessing platform resources."""

    error_code = "RESOURCE_ERROR"

    def __init__(self, message: str, **kwargs):
        suggestions = [
            "Check resource availability",
            "Verify permissions and access rights",
            "Clear unused resources",
            "Restart application or service"
        ]
        kwargs.setdefault('recovery_suggestions', []).extend(suggestions)
        super().__init__(message, **kwargs)


class TimeoutError(PlatformException):
    """Operation timeout."""

    error_code = "TIMEOUT_ERROR"

    def __init__(self, message: str, timeout_ms: Optional[int] = None, **kwargs):
        self.timeout_ms = timeout_ms
        suggestions = [
            "Increase timeout value",
            "Check system load and performance",
            "Verify network connectivity if applicable",
            "Try operation again"
        ]
        kwargs.setdefault('recovery_suggestions', []).extend(suggestions)
        super().__init__(message, **kwargs)


class DisplayServerError(PlatformException):
    """Error related to display server (X11, Wayland, etc.)."""

    error_code = "DISPLAY_SERVER_ERROR"

    def __init__(self, message: str, **kwargs):
        suggestions = [
            "Verify display server is running",
            "Check DISPLAY or WAYLAND_DISPLAY environment variables",
            "Restart display server if necessary",
            "Check for permission issues"
        ]
        kwargs.setdefault('recovery_suggestions', []).extend(suggestions)
        super().__init__(message, **kwargs)


# ==================== Retry Configuration and Logic ====================

@dataclass
class RetryConfig:
    """Configuration for retry logic with exponential backoff."""

    max_attempts: int = 3
    initial_delay_ms: float = 100
    max_delay_ms: float = 5000
    exponential_base: float = 2.0
    jitter: bool = True

    def get_delay_ms(self, attempt: int) -> float:
        """
        Calculate delay for given attempt with exponential backoff.

        Args:
            attempt: Zero-indexed attempt number

        Returns:
            Delay in milliseconds
        """
        delay = self.initial_delay_ms * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay_ms)

        if self.jitter:
            import random
            # Add jitter of +/- 10%
            jitter_amount = delay * 0.1
            delay = delay + random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)


# ==================== Error Recovery Strategies ====================

class RecoveryStrategy(ABC):
    """Abstract base class for error recovery strategies."""

    @abstractmethod
    def can_recover(self, error: Exception) -> bool:
        """Check if this strategy can handle the error."""
        pass

    @abstractmethod
    def recover(self, error: Exception, context: Dict[str, Any]) -> bool:
        """
        Attempt recovery.

        Returns:
            True if recovery successful, False otherwise
        """
        pass


class RetryRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy that retries the operation."""

    def __init__(self, config: Optional[RetryConfig] = None):
        """Initialize retry strategy."""
        self.config = config or RetryConfig()

    def can_recover(self, error: Exception) -> bool:
        """Can recover from transient errors."""
        return isinstance(error, (
            InputSimulationError,
            ResourceError,
            TimeoutError,
            DisplayServerError
        ))

    def recover(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Log retry attempt."""
        logger = logging.getLogger(__name__)
        attempt = context.get('attempt', 0)
        delay = self.config.get_delay_ms(attempt)
        logger.info(f"Retrying operation (attempt {attempt + 1}), delay: {delay}ms")
        time.sleep(delay / 1000.0)
        return True


class DegradationRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy that degrades functionality gracefully."""

    def can_recover(self, error: Exception) -> bool:
        """Can degrade from certain errors."""
        return isinstance(error, (DPIError, DisplayServerError))

    def recover(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Use fallback values or reduced functionality."""
        logger = logging.getLogger(__name__)
        logger.warning(f"Degrading functionality due to: {error}")
        context['degraded'] = True
        context['fallback_values'] = True
        return True


class SkipRecoveryStrategy(RecoveryStrategy):
    """Recovery strategy that skips the failing operation."""

    def can_recover(self, error: Exception) -> bool:
        """Can skip non-critical operations."""
        return isinstance(error, PlatformNotSupportedError)

    def recover(self, error: Exception, context: Dict[str, Any]) -> bool:
        """Skip operation."""
        logger = logging.getLogger(__name__)
        logger.warning(f"Skipping operation: {error}")
        context['skipped'] = True
        return True


# ==================== Error Context Manager ====================

@dataclass
class ErrorContext:
    """Context information for error handling."""

    operation_name: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    errors: List[Exception] = field(default_factory=list)
    recovery_strategies: List[RecoveryStrategy] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)
    successful: bool = False

    def add_error(self, error: Exception) -> None:
        """Add error to context."""
        self.errors.append(error)

    def get_duration_ms(self) -> float:
        """Get operation duration in milliseconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds() * 1000

    def attempt_recovery(self, error: Exception) -> bool:
        """Attempt recovery using registered strategies."""
        logger = logging.getLogger(__name__)

        for strategy in self.recovery_strategies:
            if strategy.can_recover(error):
                try:
                    self.context_data['attempt'] = len(self.errors)
                    if strategy.recover(error, self.context_data):
                        logger.info(f"Recovery successful using {strategy.__class__.__name__}")
                        return True
                except Exception as recovery_error:
                    logger.warning(f"Recovery failed: {recovery_error}")

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            'operation': self.operation_name,
            'duration_ms': self.get_duration_ms(),
            'successful': self.successful,
            'error_count': len(self.errors),
            'errors': [str(e) for e in self.errors],
            'context': self.context_data
        }


@contextmanager
def error_context(
    operation_name: str,
    recovery_strategies: Optional[List[RecoveryStrategy]] = None,
    logger: Optional[logging.Logger] = None,
    max_retries: int = 3
):
    """
    Context manager for error handling with recovery.

    Args:
        operation_name: Name of operation for logging
        recovery_strategies: List of recovery strategies to try
        logger: Logger instance
        max_retries: Maximum retry attempts

    Yields:
        ErrorContext object

    Example:
        with error_context("mouse_click", recovery_strategies=[...]) as ctx:
            ctx.context_data['x'] = 100
            ctx.context_data['y'] = 200
            # operation code
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    if recovery_strategies is None:
        recovery_strategies = [
            RetryRecoveryStrategy(),
            DegradationRecoveryStrategy(),
            SkipRecoveryStrategy()
        ]

    ctx = ErrorContext(
        operation_name=operation_name,
        recovery_strategies=recovery_strategies
    )

    attempt = 0
    while attempt < max_retries:
        try:
            logger.debug(f"Starting operation: {operation_name} (attempt {attempt + 1})")
            yield ctx
            ctx.successful = True
            ctx.end_time = datetime.now()
            logger.debug(f"Operation completed: {operation_name} ({ctx.get_duration_ms():.2f}ms)")
            break
        except PlatformException as e:
            ctx.add_error(e)
            logger.warning(f"Platform error in {operation_name}: {e}")

            if ctx.attempt_recovery(e):
                attempt += 1
                continue
            else:
                ctx.end_time = datetime.now()
                raise
        except Exception as e:
            ctx.add_error(e)
            logger.error(f"Unexpected error in {operation_name}: {e}", exc_info=True)
            ctx.end_time = datetime.now()
            raise

    if not ctx.successful and ctx.errors:
        ctx.end_time = datetime.now()
        raise ctx.errors[-1]


# ==================== Retry Decorators ====================

def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    exception_types: Tuple[Type[Exception], ...] = (PlatformException,),
    logger: Optional[logging.Logger] = None
):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        config: Retry configuration
        exception_types: Tuple of exception types to catch and retry
        logger: Logger instance

    Returns:
        Decorator function

    Example:
        @retry_with_backoff(RetryConfig(max_attempts=3))
        def click(x, y):
            ...
    """
    if config is None:
        config = RetryConfig()

    if logger is None:
        logger = logging.getLogger(__name__)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_error = None

            for attempt in range(config.max_attempts):
                try:
                    logger.debug(f"Calling {func.__name__} (attempt {attempt + 1})")
                    return func(*args, **kwargs)
                except exception_types as e:
                    last_error = e
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}): {e}"
                    )

                    if attempt < config.max_attempts - 1:
                        delay = config.get_delay_ms(attempt)
                        logger.debug(f"Waiting {delay:.2f}ms before retry")
                        time.sleep(delay / 1000.0)

            logger.error(
                f"{func.__name__} failed after {config.max_attempts} attempts"
            )
            raise last_error or RuntimeError(f"Failed to execute {func.__name__}")

        return wrapper

    return decorator


def graceful_degradation(
    fallback_value: Any = None,
    log_error: bool = True
):
    """
    Decorator for graceful degradation on error.

    Args:
        fallback_value: Value to return on error
        log_error: Whether to log errors

    Returns:
        Decorator function

    Example:
        @graceful_degradation(fallback_value={"width": 1920, "height": 1080})
        def get_screen_resolution():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger(__name__)

            try:
                return func(*args, **kwargs)
            except PlatformException as e:
                if log_error:
                    logger.warning(
                        f"{func.__name__} failed, using fallback: {e}"
                    )
                return fallback_value
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                return fallback_value

        return wrapper

    return decorator


# ==================== Error Reporting and Metrics ====================

@dataclass
class ErrorMetrics:
    """Metrics for error tracking and reporting."""

    total_errors: int = 0
    errors_by_type: Dict[str, int] = field(default_factory=dict)
    errors_by_code: Dict[str, int] = field(default_factory=dict)
    recovery_attempts: int = 0
    successful_recoveries: int = 0
    last_error: Optional[PlatformException] = None

    def record_error(self, error: PlatformException) -> None:
        """Record error metrics."""
        self.total_errors += 1
        self.last_error = error

        error_type = type(error).__name__
        self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1

        self.errors_by_code[error.error_code] = self.errors_by_code.get(
            error.error_code, 0
        ) + 1

    def record_recovery_attempt(self, successful: bool) -> None:
        """Record recovery attempt."""
        self.recovery_attempts += 1
        if successful:
            self.successful_recoveries += 1

    def get_success_rate(self) -> float:
        """Get recovery success rate (0.0 to 1.0)."""
        if self.recovery_attempts == 0:
            return 0.0
        return self.successful_recoveries / self.recovery_attempts

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'total_errors': self.total_errors,
            'errors_by_type': self.errors_by_type,
            'errors_by_code': self.errors_by_code,
            'recovery_attempts': self.recovery_attempts,
            'successful_recoveries': self.successful_recoveries,
            'recovery_success_rate': self.get_success_rate(),
            'last_error': str(self.last_error) if self.last_error else None
        }


class ErrorReporter:
    """Centralized error reporting and metrics collection."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize error reporter."""
        self.logger = logger or logging.getLogger(__name__)
        self.metrics = ErrorMetrics()
        self.error_history: List[Dict[str, Any]] = []

    def report_error(self, error: PlatformException) -> None:
        """Report an error."""
        self.metrics.record_error(error)
        self.error_history.append(error.to_dict())

        self.logger.error(f"Error reported: {error}")

    def report_recovery(self, success: bool, error: Optional[Exception] = None) -> None:
        """Report recovery attempt."""
        self.metrics.record_recovery_attempt(success)

        status = "successful" if success else "failed"
        message = f"Recovery {status}"
        if error:
            message += f": {error}"

        self.logger.info(message)

    def get_report(self) -> Dict[str, Any]:
        """Get comprehensive error report."""
        return {
            'timestamp': datetime.now().isoformat(),
            'metrics': self.metrics.to_dict(),
            'recent_errors': self.error_history[-10:],  # Last 10 errors
        }

    def export_json(self, filepath: str) -> None:
        """Export error report as JSON."""
        report = self.get_report()
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        self.logger.info(f"Error report exported to {filepath}")


# ==================== Global Error Reporter ====================

_global_error_reporter: Optional[ErrorReporter] = None


def get_error_reporter(logger: Optional[logging.Logger] = None) -> ErrorReporter:
    """Get or create global error reporter."""
    global _global_error_reporter

    if _global_error_reporter is None:
        _global_error_reporter = ErrorReporter(logger)

    return _global_error_reporter


# ==================== Error Handler Utilities ====================

def handle_error(
    error: Exception,
    operation_name: str,
    logger: Optional[logging.Logger] = None,
    suppress: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Handle an error with logging and reporting.

    Args:
        error: Exception to handle
        operation_name: Name of operation that failed
        logger: Logger instance
        suppress: Whether to suppress the error (return instead of raise)

    Returns:
        Error info dict if suppress=True, None otherwise

    Raises:
        Original exception if suppress=False
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    error_info = {
        'operation': operation_name,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'timestamp': datetime.now().isoformat()
    }

    if isinstance(error, PlatformException):
        get_error_reporter(logger).report_error(error)
        logger.error(
            f"Platform error in {operation_name}: {error}",
            exc_info=True
        )
    else:
        logger.error(
            f"Unexpected error in {operation_name}: {error}",
            exc_info=True
        )

    if suppress:
        return error_info
    else:
        raise error


# ==================== Exports ====================

__all__ = [
    # Logging
    'LogLevel',
    'setup_error_logging',

    # Exceptions
    'PlatformException',
    'InputSimulationError',
    'DPIError',
    'WindowManagementError',
    'CoordinateConversionError',
    'PlatformNotSupportedError',
    'ResourceError',
    'TimeoutError',
    'DisplayServerError',

    # Retry
    'RetryConfig',
    'retry_with_backoff',
    'graceful_degradation',

    # Recovery
    'RecoveryStrategy',
    'RetryRecoveryStrategy',
    'DegradationRecoveryStrategy',
    'SkipRecoveryStrategy',

    # Context managers
    'ErrorContext',
    'error_context',

    # Reporting
    'ErrorMetrics',
    'ErrorReporter',
    'get_error_reporter',
    'handle_error',
]
