"""
Error Handling Examples and Usage Patterns

This module demonstrates comprehensive usage of the error handling system
for platform-specific operations in the MCP accurate click server.

Examples cover:
1. Using custom exceptions with recovery suggestions
2. Retry logic with exponential backoff
3. Graceful degradation patterns
4. Error context managers
5. Error recovery strategies
6. Error reporting and metrics
7. Logging standardization
"""

import logging
from typing import Tuple

# Import error handling utilities
from .errors import (
    # Exceptions
    InputSimulationError,
    DPIError,
    WindowManagementError,
    CoordinateConversionError,
    ResourceError,
    TimeoutError,
    DisplayServerError,

    # Retry and recovery
    RetryConfig,
    retry_with_backoff,
    graceful_degradation,
    RetryRecoveryStrategy,
    DegradationRecoveryStrategy,

    # Context management
    error_context,

    # Reporting
    get_error_reporter,
    handle_error,

    # Logging
    setup_error_logging,
    LogLevel,
)


# ==================== Example 1: Basic Exception Usage ====================

def example_basic_exception():
    """Example 1: Using custom exceptions with recovery suggestions."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Exception Usage with Recovery Suggestions")
    print("="*70)

    try:
        raise InputSimulationError(
            "Failed to click at coordinates (100, 200)",
            context={
                'x': 100,
                'y': 200,
                'button': 'left',
                'method': 'pynput'
            },
            recovery_suggestions=[
                "Ensure the target window is focused",
                "Check if pynput module is installed",
                "Try increasing click delay",
            ]
        )
    except InputSimulationError as e:
        print(f"\nCaught exception:")
        print(f"Error Code: {e.error_code}")
        print(f"Message: {e.message}")
        print(f"Context: {e.context}")
        print(f"Suggestions:")
        for suggestion in e.recovery_suggestions:
            print(f"  - {suggestion}")


# ==================== Example 2: Retry with Backoff ====================

def example_retry_decorator():
    """Example 2: Using retry decorator with exponential backoff."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Retry Decorator with Exponential Backoff")
    print("="*70)

    # Configure retry strategy
    retry_config = RetryConfig(
        max_attempts=3,
        initial_delay_ms=100,
        max_delay_ms=1000,
        exponential_base=2.0,
        jitter=True
    )

    # Define a function that retries automatically
    @retry_with_backoff(
        config=retry_config,
        exception_types=(InputSimulationError, ResourceError),
    )
    def click_with_retry(x: int, y: int) -> bool:
        """Simulate clicking with automatic retry."""
        import random

        # Simulate random failures for demo
        if random.random() < 0.7:
            raise InputSimulationError(f"Failed to click at ({x}, {y})")

        return True

    try:
        print("\nAttempting click with automatic retries...")
        result = click_with_retry(100, 200)
        print(f"Click successful: {result}")
    except InputSimulationError as e:
        print(f"Click failed after all retries: {e}")


# ==================== Example 3: Graceful Degradation ====================

def example_graceful_degradation():
    """Example 3: Graceful degradation on failure."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Graceful Degradation")
    print("="*70)

    @graceful_degradation(
        fallback_value={'width': 1920, 'height': 1080, 'dpi_x': 96, 'dpi_y': 96},
        log_error=True
    )
    def get_monitor_info():
        """Get monitor info with graceful fallback."""
        # Simulate failure
        raise DPIError("Failed to detect monitor DPI")

    print("\nGetting monitor info (with fallback)...")
    info = get_monitor_info()
    print(f"Monitor info (fallback used): {info}")


# ==================== Example 4: Error Context Manager ====================

def example_error_context():
    """Example 4: Using error context manager."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Error Context Manager")
    print("="*70)

    logger = setup_error_logging(__name__, LogLevel.DEBUG)

    recovery_strategies = [
        RetryRecoveryStrategy(),
        DegradationRecoveryStrategy(),
    ]

    print("\nUsing error context manager...")

    try:
        with error_context(
            operation_name="window_detection",
            recovery_strategies=recovery_strategies,
            logger=logger,
            max_retries=2
        ) as ctx:
            # Add context data
            ctx.context_data['window_title'] = "Chrome"
            ctx.context_data['screen_size'] = (1920, 1080)

            print(f"Operation: {ctx.operation_name}")
            print(f"Context data: {ctx.context_data}")

            # Simulate operation
            print("Attempting window detection...")
            # Success on this example
            print("Window detected successfully!")

    except Exception as e:
        print(f"Operation failed: {e}")


# ==================== Example 5: Error Recovery Strategies ====================

def example_recovery_strategies():
    """Example 5: Implementing custom recovery strategies."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Error Recovery Strategies")
    print("="*70)

    logger = setup_error_logging(__name__, LogLevel.INFO)

    print("\nApplying recovery strategies:")
    print("1. RetryRecoveryStrategy: Automatic retry with exponential backoff")
    print("2. DegradationRecoveryStrategy: Use fallback values gracefully")
    print("3. Custom: Combine multiple strategies for robust error handling")

    # Show strategy usage
    retry_strategy = RetryRecoveryStrategy(RetryConfig(max_attempts=3))
    degrade_strategy = DegradationRecoveryStrategy()

    dpi_error = DPIError("Failed to get DPI information")

    print(f"\nError: {dpi_error}")
    print(f"Can retry strategy recover? {retry_strategy.can_recover(dpi_error)}")
    print(f"Can degrade strategy recover? {degrade_strategy.can_recover(dpi_error)}")

    # Degrade strategy should handle DPI errors
    context = {'operation': 'dpi_detection'}
    if degrade_strategy.can_recover(dpi_error):
        degrade_strategy.recover(dpi_error, context)
        print(f"Recovery applied: {context}")


# ==================== Example 6: Error Reporting ====================

def example_error_reporting():
    """Example 6: Error reporting and metrics."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Error Reporting and Metrics")
    print("="*70)

    logger = setup_error_logging(__name__, LogLevel.INFO)
    reporter = get_error_reporter(logger)

    # Simulate various errors
    errors = [
        InputSimulationError("Click failed", context={'x': 100, 'y': 200}),
        DPIError("DPI detection failed"),
        ResourceError("Display resource unavailable"),
        InputSimulationError("Click timeout"),
    ]

    print("\nReporting errors...")
    for i, error in enumerate(errors, 1):
        print(f"\n  {i}. Reporting: {error.error_code}")
        reporter.report_error(error)

        # Simulate recovery attempts
        if i % 2 == 0:
            reporter.report_recovery(success=True)
            print(f"     Recovery: Successful")
        else:
            reporter.report_recovery(success=False, error="Recovery failed")
            print(f"     Recovery: Failed")

    # Get report
    print("\n" + "-"*70)
    print("ERROR METRICS SUMMARY:")
    print("-"*70)
    report = reporter.get_report()
    metrics = report['metrics']

    print(f"Total Errors: {metrics['total_errors']}")
    print(f"Errors by Type:")
    for error_type, count in metrics['errors_by_type'].items():
        print(f"  - {error_type}: {count}")
    print(f"Recovery Attempts: {metrics['recovery_attempts']}")
    print(f"Successful Recoveries: {metrics['successful_recoveries']}")
    print(f"Recovery Success Rate: {metrics['recovery_success_rate']:.1%}")


# ==================== Example 7: Logging Standardization ====================

def example_logging_standardization():
    """Example 7: Standardized logging setup."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Logging Standardization")
    print("="*70)

    # Set up logger with standard format
    logger = setup_error_logging("platform.operations", LogLevel.DEBUG)

    print("\nDemonstrating standardized logging:")

    # Log at different levels
    logger.debug("Debug: Checking input simulator availability")
    logger.info("Info: Input simulator initialized successfully")
    logger.warning("Warning: Display server detection inconclusive")
    logger.error("Error: Failed to initialize DPI handler")

    print("\n✓ All logs use standardized format:")
    print("  [timestamp] - [logger] - [level] - [file:line] - [message]")


# ==================== Example 8: Complete Error Handling Pattern ====================

def example_complete_pattern():
    """Example 8: Complete error handling pattern."""
    print("\n" + "="*70)
    print("EXAMPLE 8: Complete Error Handling Pattern")
    print("="*70)

    logger = setup_error_logging(__name__, LogLevel.INFO)
    reporter = get_error_reporter(logger)

    def perform_click_operation(x: int, y: int) -> Tuple[bool, str]:
        """
        Perform click with comprehensive error handling.

        Returns:
            (success, message) tuple
        """
        strategies = [
            RetryRecoveryStrategy(RetryConfig(max_attempts=3)),
            DegradationRecoveryStrategy(),
        ]

        try:
            with error_context(
                operation_name=f"click_at_{x}_{y}",
                recovery_strategies=strategies,
                logger=logger,
                max_retries=2
            ) as ctx:
                ctx.context_data['coordinates'] = (x, y)
                ctx.context_data['button'] = 'left'

                # Simulate click operation
                import random
                if random.random() < 0.3:  # 30% failure rate
                    raise InputSimulationError(
                        f"Failed to click at ({x}, {y})"
                    )

                return True, "Click successful"

        except Exception as e:
            error_info = handle_error(
                e,
                operation_name=f"click_at_{x}_{y}",
                logger=logger,
                suppress=True
            )

            if error_info:
                reporter.report_error(e if isinstance(e, Exception) else InputSimulationError(str(e)))
                return False, str(e)

            return False, "Unknown error"

    print("\nPerforming click operations with error handling...")

    for i in range(3):
        success, message = perform_click_operation(100 + i * 50, 200 + i * 30)
        status = "✓" if success else "✗"
        print(f"  {status} Operation {i+1}: {message}")


# ==================== Example 9: Exception Serialization ====================

def example_exception_serialization():
    """Example 9: Serializing exceptions to JSON."""
    print("\n" + "="*70)
    print("EXAMPLE 9: Exception Serialization to JSON")
    print("="*70)

    error = CoordinateConversionError(
        "Failed to convert CSS to physical coordinates",
        context={
            'css_x': 150,
            'css_y': 300,
            'device_pixel_ratio': 2.0,
            'browser_zoom': 1.25
        },
        recovery_suggestions=[
            "Check device pixel ratio value",
            "Verify browser zoom level",
            "Ensure coordinate space transformations are correct"
        ]
    )

    print("\nException as JSON:")
    print("-"*70)

    import json
    error_dict = error.to_dict()

    # Remove traceback for cleaner output
    if 'traceback' in error_dict:
        error_dict['traceback'] = '[traceback info]'

    print(json.dumps(error_dict, indent=2))


# ==================== Main Demo ====================

def run_all_examples():
    """Run all examples."""
    print("\n\n")
    print("*" * 70)
    print("ERROR HANDLING MODULE - COMPREHENSIVE EXAMPLES")
    print("*" * 70)

    example_basic_exception()
    example_retry_decorator()
    example_graceful_degradation()
    example_error_context()
    example_recovery_strategies()
    example_error_reporting()
    example_logging_standardization()
    example_complete_pattern()
    example_exception_serialization()

    print("\n\n")
    print("*" * 70)
    print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
    print("*" * 70)
    print("\nKey Takeaways:")
    print("1. Use specific exception types for different error scenarios")
    print("2. Configure retry logic with exponential backoff for resilience")
    print("3. Apply graceful degradation for non-critical failures")
    print("4. Use error context managers for lifecycle management")
    print("5. Implement recovery strategies for automatic error recovery")
    print("6. Track error metrics for monitoring and debugging")
    print("7. Use standardized logging for consistent error reporting")
    print("8. Serialize exceptions for logging and analysis")
    print("\n")


if __name__ == '__main__':
    run_all_examples()
