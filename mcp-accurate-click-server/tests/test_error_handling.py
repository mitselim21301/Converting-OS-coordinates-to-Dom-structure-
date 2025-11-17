"""
Comprehensive Test Suite for Error Handling Module

Tests all error classes, retry logic, recovery strategies, error reporting,
and context management functionality with 90%+ coverage target.

Test Coverage:
- All 9 exception classes
- Retry logic with exponential backoff
- Recovery strategies (Retry, Degradation, Skip)
- Error context and context managers
- Error reporting and metrics
- Logging utilities
- Decorators (retry_with_backoff, graceful_degradation)
"""

import pytest
import logging
import time
import json
import tempfile
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime
from typing import Dict, Any

# Import all error handling components
from mcp_server.platform.errors import (
    # Logging
    LogLevel,
    setup_error_logging,

    # Exceptions
    PlatformException,
    InputSimulationError,
    DPIError,
    WindowManagementError,
    CoordinateConversionError,
    PlatformNotSupportedError,
    ResourceError,
    TimeoutError,
    DisplayServerError,

    # Retry
    RetryConfig,
    retry_with_backoff,
    graceful_degradation,

    # Recovery
    RecoveryStrategy,
    RetryRecoveryStrategy,
    DegradationRecoveryStrategy,
    SkipRecoveryStrategy,

    # Context
    ErrorContext,
    error_context,

    # Reporting
    ErrorMetrics,
    ErrorReporter,
    get_error_reporter,
    handle_error,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def logger():
    """Create test logger"""
    return logging.getLogger("test_errors")


@pytest.fixture
def retry_config():
    """Create retry configuration"""
    return RetryConfig(
        max_attempts=3,
        initial_delay_ms=100,
        max_delay_ms=1000,
        exponential_base=2.0,
        jitter=False
    )


@pytest.fixture
def error_reporter(logger):
    """Create error reporter"""
    return ErrorReporter(logger)


@pytest.fixture
def mock_time():
    """Mock time.sleep to speed up tests"""
    with patch('time.sleep') as mock_sleep:
        yield mock_sleep


# ============================================================================
# Test Logging Configuration
# ============================================================================

class TestLogging:
    """Tests for logging configuration"""

    def test_log_level_enum_values(self):
        """Test LogLevel enum has correct values"""
        assert LogLevel.DEBUG.value == logging.DEBUG
        assert LogLevel.INFO.value == logging.INFO
        assert LogLevel.WARNING.value == logging.WARNING
        assert LogLevel.ERROR.value == logging.ERROR
        assert LogLevel.CRITICAL.value == logging.CRITICAL

    def test_setup_error_logging_basic(self):
        """Test basic logger setup"""
        logger = setup_error_logging("test_logger_1")

        assert logger is not None
        assert logger.name == "test_logger_1"
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_setup_error_logging_with_level(self):
        """Test logger setup with specific level"""
        logger = setup_error_logging("test_logger_2", LogLevel.DEBUG)

        assert logger.level == logging.DEBUG

    def test_setup_error_logging_formatter(self):
        """Test logger has correct formatter"""
        logger = setup_error_logging("test_logger_3")

        handler = logger.handlers[0]
        formatter = handler.formatter

        assert formatter is not None
        assert '%(asctime)s' in formatter._fmt
        assert '%(name)s' in formatter._fmt
        assert '%(levelname)s' in formatter._fmt

    def test_setup_error_logging_idempotent(self):
        """Test logger setup doesn't add duplicate handlers"""
        logger1 = setup_error_logging("test_logger_4")
        handler_count_1 = len(logger1.handlers)

        logger2 = setup_error_logging("test_logger_4")
        handler_count_2 = len(logger2.handlers)

        assert handler_count_1 == handler_count_2


# ============================================================================
# Test Exception Classes
# ============================================================================

class TestPlatformException:
    """Tests for PlatformException base class"""

    def test_platform_exception_basic(self):
        """Test basic exception creation"""
        error = PlatformException("Test error")

        assert error.message == "Test error"
        assert error.error_code == "PLATFORM_ERROR"
        assert error.context == {}
        assert error.recovery_suggestions == []
        assert isinstance(error.timestamp, datetime)

    def test_platform_exception_with_context(self):
        """Test exception with context data"""
        context = {"x": 100, "y": 200}
        error = PlatformException("Test error", context=context)

        assert error.context == context

    def test_platform_exception_with_error_code(self):
        """Test exception with custom error code"""
        error = PlatformException("Test error", error_code="CUSTOM_ERROR")

        assert error.error_code == "CUSTOM_ERROR"

    def test_platform_exception_with_recovery_suggestions(self):
        """Test exception with recovery suggestions"""
        suggestions = ["Try again", "Check settings"]
        error = PlatformException("Test error", recovery_suggestions=suggestions)

        assert error.recovery_suggestions == suggestions

    def test_platform_exception_str_basic(self):
        """Test exception string representation"""
        error = PlatformException("Test error")
        error_str = str(error)

        assert "[PLATFORM_ERROR]" in error_str
        assert "Test error" in error_str

    def test_platform_exception_str_with_suggestions(self):
        """Test exception string includes suggestions"""
        error = PlatformException(
            "Test error",
            recovery_suggestions=["Suggestion 1", "Suggestion 2"]
        )
        error_str = str(error)

        assert "Suggestions:" in error_str
        assert "Suggestion 1" in error_str
        assert "Suggestion 2" in error_str

    def test_platform_exception_to_dict(self):
        """Test exception serialization to dict"""
        error = PlatformException(
            "Test error",
            error_code="TEST_ERROR",
            context={"key": "value"},
            recovery_suggestions=["Try again"]
        )
        error_dict = error.to_dict()

        assert error_dict['error_code'] == "TEST_ERROR"
        assert error_dict['message'] == "Test error"
        assert error_dict['context'] == {"key": "value"}
        assert error_dict['recovery_suggestions'] == ["Try again"]
        assert 'timestamp' in error_dict
        assert 'traceback' in error_dict


class TestInputSimulationError:
    """Tests for InputSimulationError"""

    def test_input_simulation_error_creation(self):
        """Test InputSimulationError creation"""
        error = InputSimulationError("Mouse click failed")

        assert error.message == "Mouse click failed"
        assert error.error_code == "INPUT_SIMULATION_ERROR"
        assert len(error.recovery_suggestions) > 0

    def test_input_simulation_error_has_default_suggestions(self):
        """Test InputSimulationError has default recovery suggestions"""
        error = InputSimulationError("Test error")

        assert any("input simulator" in s.lower() for s in error.recovery_suggestions)
        assert any("permissions" in s.lower() for s in error.recovery_suggestions)

    def test_input_simulation_error_custom_suggestions(self):
        """Test InputSimulationError with custom suggestions"""
        error = InputSimulationError(
            "Test error",
            recovery_suggestions=["Custom suggestion"]
        )

        assert "Custom suggestion" in error.recovery_suggestions


class TestDPIError:
    """Tests for DPIError"""

    def test_dpi_error_creation(self):
        """Test DPIError creation"""
        error = DPIError("DPI detection failed")

        assert error.message == "DPI detection failed"
        assert error.error_code == "DPI_ERROR"
        assert len(error.recovery_suggestions) > 0

    def test_dpi_error_has_default_suggestions(self):
        """Test DPIError has DPI-specific suggestions"""
        error = DPIError("Test error")

        assert any("dpi" in s.lower() for s in error.recovery_suggestions)
        assert any("scaling" in s.lower() for s in error.recovery_suggestions)


class TestWindowManagementError:
    """Tests for WindowManagementError"""

    def test_window_management_error_creation(self):
        """Test WindowManagementError creation"""
        error = WindowManagementError("Window not found")

        assert error.message == "Window not found"
        assert error.error_code == "WINDOW_MANAGEMENT_ERROR"
        assert len(error.recovery_suggestions) > 0

    def test_window_management_error_has_default_suggestions(self):
        """Test WindowManagementError has window-specific suggestions"""
        error = WindowManagementError("Test error")

        assert any("window" in s.lower() for s in error.recovery_suggestions)
        assert any("visible" in s.lower() or "exists" in s.lower() for s in error.recovery_suggestions)


class TestCoordinateConversionError:
    """Tests for CoordinateConversionError"""

    def test_coordinate_conversion_error_creation(self):
        """Test CoordinateConversionError creation"""
        error = CoordinateConversionError("Invalid coordinates")

        assert error.message == "Invalid coordinates"
        assert error.error_code == "COORDINATE_CONVERSION_ERROR"
        assert len(error.recovery_suggestions) > 0

    def test_coordinate_conversion_error_has_default_suggestions(self):
        """Test CoordinateConversionError has coordinate-specific suggestions"""
        error = CoordinateConversionError("Test error")

        assert any("coordinate" in s.lower() for s in error.recovery_suggestions)
        assert any("dpi" in s.lower() or "scaling" in s.lower() for s in error.recovery_suggestions)


class TestPlatformNotSupportedError:
    """Tests for PlatformNotSupportedError"""

    def test_platform_not_supported_error_creation(self):
        """Test PlatformNotSupportedError creation"""
        error = PlatformNotSupportedError("Platform not supported")

        assert error.message == "Platform not supported"
        assert error.error_code == "PLATFORM_NOT_SUPPORTED"
        assert len(error.recovery_suggestions) > 0

    def test_platform_not_supported_error_has_default_suggestions(self):
        """Test PlatformNotSupportedError has platform-specific suggestions"""
        error = PlatformNotSupportedError("Test error")

        assert any("platform" in s.lower() for s in error.recovery_suggestions)


class TestResourceError:
    """Tests for ResourceError"""

    def test_resource_error_creation(self):
        """Test ResourceError creation"""
        error = ResourceError("Resource unavailable")

        assert error.message == "Resource unavailable"
        assert error.error_code == "RESOURCE_ERROR"
        assert len(error.recovery_suggestions) > 0

    def test_resource_error_has_default_suggestions(self):
        """Test ResourceError has resource-specific suggestions"""
        error = ResourceError("Test error")

        assert any("resource" in s.lower() for s in error.recovery_suggestions)
        assert any("permissions" in s.lower() or "access" in s.lower() for s in error.recovery_suggestions)


class TestTimeoutError:
    """Tests for TimeoutError"""

    def test_timeout_error_creation(self):
        """Test TimeoutError creation"""
        error = TimeoutError("Operation timed out")

        assert error.message == "Operation timed out"
        assert error.error_code == "TIMEOUT_ERROR"
        assert len(error.recovery_suggestions) > 0

    def test_timeout_error_with_timeout_value(self):
        """Test TimeoutError with timeout value"""
        error = TimeoutError("Operation timed out", timeout_ms=5000)

        assert error.timeout_ms == 5000

    def test_timeout_error_has_default_suggestions(self):
        """Test TimeoutError has timeout-specific suggestions"""
        error = TimeoutError("Test error")

        assert any("timeout" in s.lower() for s in error.recovery_suggestions)


class TestDisplayServerError:
    """Tests for DisplayServerError"""

    def test_display_server_error_creation(self):
        """Test DisplayServerError creation"""
        error = DisplayServerError("Display server error")

        assert error.message == "Display server error"
        assert error.error_code == "DISPLAY_SERVER_ERROR"
        assert len(error.recovery_suggestions) > 0

    def test_display_server_error_has_default_suggestions(self):
        """Test DisplayServerError has display-specific suggestions"""
        error = DisplayServerError("Test error")

        assert any("display" in s.lower() for s in error.recovery_suggestions)


# ============================================================================
# Test Retry Configuration
# ============================================================================

class TestRetryConfig:
    """Tests for RetryConfig"""

    def test_retry_config_defaults(self):
        """Test RetryConfig default values"""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.initial_delay_ms == 100
        assert config.max_delay_ms == 5000
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_retry_config_custom_values(self):
        """Test RetryConfig with custom values"""
        config = RetryConfig(
            max_attempts=5,
            initial_delay_ms=200,
            max_delay_ms=10000,
            exponential_base=3.0,
            jitter=False
        )

        assert config.max_attempts == 5
        assert config.initial_delay_ms == 200
        assert config.max_delay_ms == 10000
        assert config.exponential_base == 3.0
        assert config.jitter is False

    def test_retry_config_get_delay_exponential(self):
        """Test exponential backoff delay calculation"""
        config = RetryConfig(
            initial_delay_ms=100,
            exponential_base=2.0,
            max_delay_ms=10000,
            jitter=False
        )

        # Attempt 0: 100ms
        assert config.get_delay_ms(0) == 100
        # Attempt 1: 200ms
        assert config.get_delay_ms(1) == 200
        # Attempt 2: 400ms
        assert config.get_delay_ms(2) == 400
        # Attempt 3: 800ms
        assert config.get_delay_ms(3) == 800

    def test_retry_config_get_delay_max_limit(self):
        """Test delay respects max_delay_ms"""
        config = RetryConfig(
            initial_delay_ms=100,
            exponential_base=2.0,
            max_delay_ms=500,
            jitter=False
        )

        # Should be capped at max_delay_ms
        assert config.get_delay_ms(10) == 500

    def test_retry_config_get_delay_with_jitter(self):
        """Test delay with jitter adds randomness"""
        config = RetryConfig(
            initial_delay_ms=100,
            exponential_base=2.0,
            jitter=True
        )

        delay = config.get_delay_ms(0)
        # Should be within 10% of 100ms
        assert 90 <= delay <= 110

    def test_retry_config_get_delay_never_negative(self):
        """Test delay is never negative"""
        config = RetryConfig(initial_delay_ms=0.1, jitter=True)

        delay = config.get_delay_ms(0)
        assert delay >= 0


# ============================================================================
# Test Recovery Strategies
# ============================================================================

class TestRetryRecoveryStrategy:
    """Tests for RetryRecoveryStrategy"""

    def test_retry_strategy_creation(self):
        """Test RetryRecoveryStrategy creation"""
        strategy = RetryRecoveryStrategy()

        assert strategy.config is not None
        assert isinstance(strategy.config, RetryConfig)

    def test_retry_strategy_with_custom_config(self, retry_config):
        """Test RetryRecoveryStrategy with custom config"""
        strategy = RetryRecoveryStrategy(retry_config)

        assert strategy.config == retry_config

    def test_retry_strategy_can_recover_input_error(self):
        """Test can recover from InputSimulationError"""
        strategy = RetryRecoveryStrategy()
        error = InputSimulationError("Test error")

        assert strategy.can_recover(error) is True

    def test_retry_strategy_can_recover_resource_error(self):
        """Test can recover from ResourceError"""
        strategy = RetryRecoveryStrategy()
        error = ResourceError("Test error")

        assert strategy.can_recover(error) is True

    def test_retry_strategy_can_recover_timeout_error(self):
        """Test can recover from TimeoutError"""
        strategy = RetryRecoveryStrategy()
        error = TimeoutError("Test error")

        assert strategy.can_recover(error) is True

    def test_retry_strategy_cannot_recover_dpi_error(self):
        """Test cannot recover from DPIError"""
        strategy = RetryRecoveryStrategy()
        error = DPIError("Test error")

        assert strategy.can_recover(error) is False

    def test_retry_strategy_recover_sleeps(self, mock_time):
        """Test recover method sleeps for delay"""
        config = RetryConfig(initial_delay_ms=100, jitter=False)
        strategy = RetryRecoveryStrategy(config)

        error = InputSimulationError("Test error")
        context = {"attempt": 0}

        result = strategy.recover(error, context)

        assert result is True
        mock_time.assert_called_once()
        # Check sleep was called with ~0.1 seconds
        assert 0.09 <= mock_time.call_args[0][0] <= 0.11


class TestDegradationRecoveryStrategy:
    """Tests for DegradationRecoveryStrategy"""

    def test_degradation_strategy_creation(self):
        """Test DegradationRecoveryStrategy creation"""
        strategy = DegradationRecoveryStrategy()

        assert strategy is not None

    def test_degradation_strategy_can_recover_dpi_error(self):
        """Test can recover from DPIError"""
        strategy = DegradationRecoveryStrategy()
        error = DPIError("Test error")

        assert strategy.can_recover(error) is True

    def test_degradation_strategy_can_recover_display_server_error(self):
        """Test can recover from DisplayServerError"""
        strategy = DegradationRecoveryStrategy()
        error = DisplayServerError("Test error")

        assert strategy.can_recover(error) is True

    def test_degradation_strategy_cannot_recover_input_error(self):
        """Test cannot recover from InputSimulationError"""
        strategy = DegradationRecoveryStrategy()
        error = InputSimulationError("Test error")

        assert strategy.can_recover(error) is False

    def test_degradation_strategy_recover_sets_degraded_flag(self):
        """Test recover sets degraded flag in context"""
        strategy = DegradationRecoveryStrategy()
        error = DPIError("Test error")
        context: Dict[str, Any] = {}

        result = strategy.recover(error, context)

        assert result is True
        assert context['degraded'] is True
        assert context['fallback_values'] is True


class TestSkipRecoveryStrategy:
    """Tests for SkipRecoveryStrategy"""

    def test_skip_strategy_creation(self):
        """Test SkipRecoveryStrategy creation"""
        strategy = SkipRecoveryStrategy()

        assert strategy is not None

    def test_skip_strategy_can_recover_platform_not_supported(self):
        """Test can recover from PlatformNotSupportedError"""
        strategy = SkipRecoveryStrategy()
        error = PlatformNotSupportedError("Test error")

        assert strategy.can_recover(error) is True

    def test_skip_strategy_cannot_recover_other_errors(self):
        """Test cannot recover from other errors"""
        strategy = SkipRecoveryStrategy()
        error = InputSimulationError("Test error")

        assert strategy.can_recover(error) is False

    def test_skip_strategy_recover_sets_skipped_flag(self):
        """Test recover sets skipped flag in context"""
        strategy = SkipRecoveryStrategy()
        error = PlatformNotSupportedError("Test error")
        context: Dict[str, Any] = {}

        result = strategy.recover(error, context)

        assert result is True
        assert context['skipped'] is True


# ============================================================================
# Test Error Context
# ============================================================================

class TestErrorContext:
    """Tests for ErrorContext"""

    def test_error_context_creation(self):
        """Test ErrorContext creation"""
        ctx = ErrorContext(operation_name="test_operation")

        assert ctx.operation_name == "test_operation"
        assert isinstance(ctx.start_time, datetime)
        assert ctx.end_time is None
        assert len(ctx.errors) == 0
        assert len(ctx.recovery_strategies) == 0
        assert ctx.context_data == {}
        assert ctx.successful is False

    def test_error_context_add_error(self):
        """Test adding errors to context"""
        ctx = ErrorContext(operation_name="test_operation")
        error = PlatformException("Test error")

        ctx.add_error(error)

        assert len(ctx.errors) == 1
        assert ctx.errors[0] == error

    def test_error_context_get_duration_ms(self):
        """Test duration calculation"""
        ctx = ErrorContext(operation_name="test_operation")
        time.sleep(0.01)  # Sleep 10ms

        duration = ctx.get_duration_ms()

        assert duration >= 10

    def test_error_context_get_duration_ms_with_end_time(self):
        """Test duration calculation with end time"""
        ctx = ErrorContext(operation_name="test_operation")
        time.sleep(0.01)
        ctx.end_time = datetime.now()

        duration = ctx.get_duration_ms()

        assert duration >= 10

    def test_error_context_attempt_recovery_success(self):
        """Test successful recovery attempt"""
        strategy = RetryRecoveryStrategy()
        ctx = ErrorContext(
            operation_name="test_operation",
            recovery_strategies=[strategy]
        )
        error = InputSimulationError("Test error")

        with patch('time.sleep'):
            result = ctx.attempt_recovery(error)

        assert result is True

    def test_error_context_attempt_recovery_failure(self):
        """Test failed recovery attempt"""
        strategy = RetryRecoveryStrategy()
        ctx = ErrorContext(
            operation_name="test_operation",
            recovery_strategies=[strategy]
        )
        error = DPIError("Test error")  # Cannot be recovered by retry strategy

        result = ctx.attempt_recovery(error)

        assert result is False

    def test_error_context_to_dict(self):
        """Test conversion to dictionary"""
        ctx = ErrorContext(operation_name="test_operation")
        ctx.add_error(PlatformException("Test error"))
        ctx.context_data['key'] = 'value'
        ctx.successful = True

        result = ctx.to_dict()

        assert result['operation'] == "test_operation"
        assert result['successful'] is True
        assert result['error_count'] == 1
        assert len(result['errors']) == 1
        assert result['context']['key'] == 'value'
        assert 'duration_ms' in result

    def test_error_context_recovery_strategy_exception(self):
        """Test when recovery strategy itself raises an exception"""
        mock_strategy = Mock(spec=RecoveryStrategy)
        mock_strategy.can_recover.return_value = True
        mock_strategy.recover.side_effect = RuntimeError("Recovery failed")

        ctx = ErrorContext(
            operation_name="test_operation",
            recovery_strategies=[mock_strategy]
        )

        error = InputSimulationError("Test error")
        result = ctx.attempt_recovery(error)

        # Should return False when recovery raises exception
        assert result is False


class TestErrorContextManager:
    """Tests for error_context context manager"""

    def test_error_context_manager_success(self, mock_time):
        """Test error_context on successful operation"""
        with error_context("test_operation") as ctx:
            ctx.context_data['x'] = 100

        assert ctx.successful is True
        assert ctx.end_time is not None
        assert len(ctx.errors) == 0

    def test_error_context_manager_with_error(self):
        """Test error_context with error"""
        with pytest.raises(ValueError):
            with error_context("test_operation") as ctx:
                raise ValueError("Test error")

        assert ctx.successful is False
        assert len(ctx.errors) == 1

    def test_error_context_manager_captures_context_data(self):
        """Test error_context captures context data"""
        with error_context("test_operation") as ctx:
            ctx.context_data['x'] = 100
            ctx.context_data['y'] = 200

        assert ctx.context_data['x'] == 100
        assert ctx.context_data['y'] == 200
        assert ctx.successful is True

    def test_error_context_manager_recovery_strategies_invoked(self):
        """Test error_context invokes recovery strategies"""
        mock_strategy = Mock(spec=RecoveryStrategy)
        mock_strategy.can_recover.return_value = True
        mock_strategy.recover.return_value = False  # Recovery fails

        error = InputSimulationError("Test error")

        with pytest.raises(InputSimulationError):
            with error_context("test_operation", recovery_strategies=[mock_strategy], max_retries=1) as ctx:
                raise error

        # Strategy should have been called
        mock_strategy.can_recover.assert_called_once_with(error)
        mock_strategy.recover.assert_called_once()


# ============================================================================
# Test Retry Decorator
# ============================================================================

class TestRetryWithBackoff:
    """Tests for retry_with_backoff decorator"""

    def test_retry_decorator_success_first_attempt(self, mock_time):
        """Test retry decorator on first successful attempt"""
        call_count = [0]

        @retry_with_backoff()
        def test_func():
            call_count[0] += 1
            return "success"

        result = test_func()

        assert result == "success"
        assert call_count[0] == 1
        mock_time.assert_not_called()

    def test_retry_decorator_success_after_retry(self, mock_time):
        """Test retry decorator succeeds after retries"""
        call_count = [0]

        @retry_with_backoff(RetryConfig(max_attempts=3))
        def test_func():
            call_count[0] += 1
            if call_count[0] < 3:
                raise InputSimulationError("Test error")
            return "success"

        result = test_func()

        assert result == "success"
        assert call_count[0] == 3
        assert mock_time.call_count == 2  # Two retries

    def test_retry_decorator_failure_after_max_attempts(self, mock_time):
        """Test retry decorator fails after max attempts"""
        call_count = [0]

        @retry_with_backoff(RetryConfig(max_attempts=3))
        def test_func():
            call_count[0] += 1
            raise InputSimulationError("Test error")

        with pytest.raises(InputSimulationError):
            test_func()

        assert call_count[0] == 3
        assert mock_time.call_count == 2

    def test_retry_decorator_with_custom_exception_types(self, mock_time):
        """Test retry decorator with custom exception types"""
        call_count = [0]

        @retry_with_backoff(exception_types=(ValueError,))
        def test_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Test error")
            return "success"

        result = test_func()

        assert result == "success"
        assert call_count[0] == 2

    def test_retry_decorator_doesnt_catch_other_exceptions(self, mock_time):
        """Test retry decorator doesn't catch non-specified exceptions"""
        @retry_with_backoff(exception_types=(InputSimulationError,))
        def test_func():
            raise ValueError("Different error")

        with pytest.raises(ValueError):
            test_func()

        mock_time.assert_not_called()


# ============================================================================
# Test Graceful Degradation Decorator
# ============================================================================

class TestGracefulDegradation:
    """Tests for graceful_degradation decorator"""

    def test_graceful_degradation_success(self):
        """Test graceful_degradation on success"""
        @graceful_degradation(fallback_value="fallback")
        def test_func():
            return "success"

        result = test_func()

        assert result == "success"

    def test_graceful_degradation_on_platform_error(self):
        """Test graceful_degradation returns fallback on platform error"""
        @graceful_degradation(fallback_value="fallback")
        def test_func():
            raise DPIError("Test error")

        result = test_func()

        assert result == "fallback"

    def test_graceful_degradation_on_unexpected_error(self):
        """Test graceful_degradation returns fallback on unexpected error"""
        @graceful_degradation(fallback_value="fallback")
        def test_func():
            raise ValueError("Test error")

        result = test_func()

        assert result == "fallback"

    def test_graceful_degradation_with_none_fallback(self):
        """Test graceful_degradation with None fallback"""
        @graceful_degradation(fallback_value=None)
        def test_func():
            raise DPIError("Test error")

        result = test_func()

        assert result is None

    def test_graceful_degradation_with_dict_fallback(self):
        """Test graceful_degradation with dict fallback"""
        fallback = {"width": 1920, "height": 1080}

        @graceful_degradation(fallback_value=fallback)
        def test_func():
            raise DPIError("Test error")

        result = test_func()

        assert result == fallback


# ============================================================================
# Test Error Metrics
# ============================================================================

class TestErrorMetrics:
    """Tests for ErrorMetrics"""

    def test_error_metrics_creation(self):
        """Test ErrorMetrics creation"""
        metrics = ErrorMetrics()

        assert metrics.total_errors == 0
        assert metrics.errors_by_type == {}
        assert metrics.errors_by_code == {}
        assert metrics.recovery_attempts == 0
        assert metrics.successful_recoveries == 0
        assert metrics.last_error is None

    def test_error_metrics_record_error(self):
        """Test recording errors"""
        metrics = ErrorMetrics()
        error = InputSimulationError("Test error")

        metrics.record_error(error)

        assert metrics.total_errors == 1
        assert metrics.errors_by_type['InputSimulationError'] == 1
        assert metrics.errors_by_code['INPUT_SIMULATION_ERROR'] == 1
        assert metrics.last_error == error

    def test_error_metrics_record_multiple_errors(self):
        """Test recording multiple errors"""
        metrics = ErrorMetrics()

        metrics.record_error(InputSimulationError("Error 1"))
        metrics.record_error(InputSimulationError("Error 2"))
        metrics.record_error(DPIError("Error 3"))

        assert metrics.total_errors == 3
        assert metrics.errors_by_type['InputSimulationError'] == 2
        assert metrics.errors_by_type['DPIError'] == 1

    def test_error_metrics_record_recovery_attempt(self):
        """Test recording recovery attempts"""
        metrics = ErrorMetrics()

        metrics.record_recovery_attempt(True)
        metrics.record_recovery_attempt(True)
        metrics.record_recovery_attempt(False)

        assert metrics.recovery_attempts == 3
        assert metrics.successful_recoveries == 2

    def test_error_metrics_get_success_rate(self):
        """Test calculating success rate"""
        metrics = ErrorMetrics()

        metrics.record_recovery_attempt(True)
        metrics.record_recovery_attempt(True)
        metrics.record_recovery_attempt(False)

        assert metrics.get_success_rate() == 2.0 / 3.0

    def test_error_metrics_get_success_rate_no_attempts(self):
        """Test success rate with no attempts"""
        metrics = ErrorMetrics()

        assert metrics.get_success_rate() == 0.0

    def test_error_metrics_to_dict(self):
        """Test converting metrics to dict"""
        metrics = ErrorMetrics()
        error = InputSimulationError("Test error")
        metrics.record_error(error)
        metrics.record_recovery_attempt(True)

        result = metrics.to_dict()

        assert result['total_errors'] == 1
        assert 'errors_by_type' in result
        assert 'errors_by_code' in result
        assert result['recovery_attempts'] == 1
        assert result['successful_recoveries'] == 1
        assert 'recovery_success_rate' in result
        assert result['last_error'] is not None


# ============================================================================
# Test Error Reporter
# ============================================================================

class TestErrorReporter:
    """Tests for ErrorReporter"""

    def test_error_reporter_creation(self, logger):
        """Test ErrorReporter creation"""
        reporter = ErrorReporter(logger)

        assert reporter.logger == logger
        assert isinstance(reporter.metrics, ErrorMetrics)
        assert reporter.error_history == []

    def test_error_reporter_creation_default_logger(self):
        """Test ErrorReporter creation with default logger"""
        reporter = ErrorReporter()

        assert reporter.logger is not None

    def test_error_reporter_report_error(self, logger):
        """Test reporting an error"""
        reporter = ErrorReporter(logger)
        error = InputSimulationError("Test error")

        reporter.report_error(error)

        assert reporter.metrics.total_errors == 1
        assert len(reporter.error_history) == 1

    def test_error_reporter_report_recovery(self, logger):
        """Test reporting recovery attempts"""
        reporter = ErrorReporter(logger)

        reporter.report_recovery(True)
        reporter.report_recovery(False)

        assert reporter.metrics.recovery_attempts == 2
        assert reporter.metrics.successful_recoveries == 1

    def test_error_reporter_report_recovery_with_error(self, logger):
        """Test reporting recovery with error details"""
        reporter = ErrorReporter(logger)
        error = InputSimulationError("Test error")

        reporter.report_recovery(True, error)
        reporter.report_recovery(False, error)

        assert reporter.metrics.recovery_attempts == 2
        assert reporter.metrics.successful_recoveries == 1

    def test_error_reporter_get_report(self, logger):
        """Test getting comprehensive report"""
        reporter = ErrorReporter(logger)
        error = InputSimulationError("Test error")
        reporter.report_error(error)
        reporter.report_recovery(True)

        report = reporter.get_report()

        assert 'timestamp' in report
        assert 'metrics' in report
        assert 'recent_errors' in report
        assert report['metrics']['total_errors'] == 1

    def test_error_reporter_export_json(self, logger):
        """Test exporting report as JSON"""
        reporter = ErrorReporter(logger)
        error = InputSimulationError("Test error")
        reporter.report_error(error)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filepath = f.name

        try:
            reporter.export_json(filepath)

            # Read and verify JSON
            with open(filepath, 'r') as f:
                data = json.load(f)

            assert 'timestamp' in data
            assert 'metrics' in data
            assert data['metrics']['total_errors'] == 1
        finally:
            import os
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_error_reporter_recent_errors_limit(self, logger):
        """Test error history is limited to last 10 errors"""
        reporter = ErrorReporter(logger)

        # Add 15 errors
        for i in range(15):
            reporter.report_error(InputSimulationError(f"Error {i}"))

        report = reporter.get_report()

        # Should only have last 10
        assert len(report['recent_errors']) == 10


class TestGlobalErrorReporter:
    """Tests for global error reporter"""

    def test_get_error_reporter_creates_instance(self, logger):
        """Test get_error_reporter creates global instance"""
        # Reset global instance
        import mcp_server.platform.errors as errors_module
        errors_module._global_error_reporter = None

        reporter = get_error_reporter(logger)

        assert reporter is not None
        assert isinstance(reporter, ErrorReporter)

    def test_get_error_reporter_returns_same_instance(self):
        """Test get_error_reporter returns same instance"""
        reporter1 = get_error_reporter()
        reporter2 = get_error_reporter()

        assert reporter1 is reporter2


# ============================================================================
# Test Error Handler Utility
# ============================================================================

class TestHandleError:
    """Tests for handle_error utility"""

    def test_handle_error_platform_exception(self, logger):
        """Test handling platform exception"""
        error = InputSimulationError("Test error")

        with pytest.raises(InputSimulationError):
            handle_error(error, "test_operation", logger=logger)

    def test_handle_error_unexpected_exception(self, logger):
        """Test handling unexpected exception"""
        error = ValueError("Test error")

        with pytest.raises(ValueError):
            handle_error(error, "test_operation", logger=logger)

    def test_handle_error_with_suppress(self, logger):
        """Test handling error with suppress"""
        error = InputSimulationError("Test error")

        result = handle_error(error, "test_operation", logger=logger, suppress=True)

        assert result is not None
        assert result['operation'] == "test_operation"
        assert result['error_type'] == 'InputSimulationError'
        # Error message includes formatting from __str__
        assert "Test error" in result['error_message']
        assert 'timestamp' in result

    def test_handle_error_default_logger(self):
        """Test handling error with default logger"""
        error = InputSimulationError("Test error")

        with pytest.raises(InputSimulationError):
            handle_error(error, "test_operation")


# ============================================================================
# Test Integration Scenarios
# ============================================================================

class TestIntegrationScenarios:
    """Integration tests for complete error handling workflows"""

    def test_complete_error_recovery_workflow(self, mock_time):
        """Test complete error recovery workflow with error reporting"""
        reporter = ErrorReporter()

        # Simulate error reporting workflow
        error1 = InputSimulationError("Error 1")
        error2 = DPIError("Error 2")
        error3 = TimeoutError("Error 3")

        # Report errors
        reporter.report_error(error1)
        reporter.report_recovery(True)

        reporter.report_error(error2)
        reporter.report_recovery(False)

        reporter.report_error(error3)
        reporter.report_recovery(True)

        # Verify metrics
        assert reporter.metrics.total_errors == 3
        assert reporter.metrics.recovery_attempts == 3
        assert reporter.metrics.successful_recoveries == 2
        assert reporter.metrics.get_success_rate() == 2.0 / 3.0

        # Verify error history
        assert len(reporter.error_history) == 3

    def test_error_reporting_with_metrics(self, logger):
        """Test error reporting collects metrics"""
        reporter = ErrorReporter(logger)

        # Simulate multiple errors
        for i in range(5):
            error = InputSimulationError(f"Error {i}")
            reporter.report_error(error)
            reporter.report_recovery(i % 2 == 0)  # 3 successful, 2 failed

        metrics = reporter.metrics
        assert metrics.total_errors == 5
        assert metrics.recovery_attempts == 5
        assert metrics.successful_recoveries == 3

    def test_retry_with_multiple_strategies(self, mock_time):
        """Test retry with multiple recovery strategies"""
        retry_strategy = RetryRecoveryStrategy()
        degradation_strategy = DegradationRecoveryStrategy()

        ctx = ErrorContext(
            operation_name="test_operation",
            recovery_strategies=[retry_strategy, degradation_strategy]
        )

        # Test retry strategy
        input_error = InputSimulationError("Test error")
        assert ctx.attempt_recovery(input_error) is True

        # Test degradation strategy
        dpi_error = DPIError("Test error")
        assert ctx.attempt_recovery(dpi_error) is True
