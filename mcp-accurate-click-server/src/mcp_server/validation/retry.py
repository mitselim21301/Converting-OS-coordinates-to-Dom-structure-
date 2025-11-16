"""
Retry Logic with Exponential Backoff

Implements robust retry strategies for click operations:
- Exponential backoff with jitter
- Configurable retry conditions
- Error type discrimination
- Adaptive retry delays
- Circuit breaker pattern

Reference: CLICK_VALIDATION_RESEARCH.md Section 3
"""

import asyncio
import random
import math
from typing import Dict, List, Optional, Any, Callable, TypeVar, Awaitable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta


T = TypeVar('T')


class RetryStrategy(Enum):
    """Retry strategy types"""
    EXPONENTIAL = "EXPONENTIAL"
    EXPONENTIAL_WITH_JITTER = "EXPONENTIAL_WITH_JITTER"
    LINEAR = "LINEAR"
    FIXED = "FIXED"


class ErrorCategory(Enum):
    """Categories of errors that can be retried"""
    ELEMENT_NOT_FOUND = "ELEMENT_NOT_FOUND"
    ELEMENT_CLICK_INTERCEPTED = "ELEMENT_CLICK_INTERCEPTED"
    ELEMENT_NOT_INTERACTABLE = "ELEMENT_NOT_INTERACTABLE"
    STALE_ELEMENT_REFERENCE = "STALE_ELEMENT_REFERENCE"
    TIMEOUT = "TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    UNKNOWN = "UNKNOWN"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 5
    base_delay_ms: int = 1000
    max_delay_ms: int = 30000
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_WITH_JITTER
    jitter_factor: float = 1.0  # 0-1.0, adds up to 100% jitter
    backoff_multiplier: float = 2.0
    retryable_errors: Optional[List[ErrorCategory]] = None


@dataclass
class RetryAttempt:
    """Information about a retry attempt"""
    attempt_number: int
    timestamp: datetime
    error: Optional[Exception]
    error_category: ErrorCategory
    delay_ms: int
    success: bool


@dataclass
class RetryResult:
    """Result of retry operation"""
    success: bool
    attempts: int
    total_time_ms: float
    result: Any
    error: Optional[Exception]
    attempt_history: List[RetryAttempt]


class RetryableError(Exception):
    """Base class for retryable errors"""
    def __init__(self, message: str, category: ErrorCategory):
        super().__init__(message)
        self.category = category


class ElementClickInterceptedError(RetryableError):
    """Element click was intercepted by another element"""
    def __init__(self, message: str = "Element click intercepted"):
        super().__init__(message, ErrorCategory.ELEMENT_CLICK_INTERCEPTED)


class ElementNotInteractableError(RetryableError):
    """Element is not interactable"""
    def __init__(self, message: str = "Element not interactable"):
        super().__init__(message, ErrorCategory.ELEMENT_NOT_INTERACTABLE)


class StaleElementError(RetryableError):
    """Element is stale (removed from DOM)"""
    def __init__(self, message: str = "Stale element reference"):
        super().__init__(message, ErrorCategory.STALE_ELEMENT_REFERENCE)


class DelayCalculator:
    """Calculates retry delays based on strategy"""

    @staticmethod
    def calculate_exponential_backoff(
        attempt: int,
        base_delay_ms: int,
        backoff_multiplier: float = 2.0,
        max_delay_ms: int = 30000
    ) -> int:
        """
        Calculate exponential backoff delay.

        Formula: min(base_delay * multiplier^attempt, max_delay)
        """
        delay = base_delay_ms * (backoff_multiplier ** attempt)
        return min(int(delay), max_delay_ms)

    @staticmethod
    def add_jitter(delay_ms: int, jitter_factor: float = 1.0) -> int:
        """
        Add random jitter to delay.

        Args:
            delay_ms: Base delay in milliseconds
            jitter_factor: Factor (0-1.0) controlling jitter amount

        Returns:
            Delay with jitter added
        """
        jitter = random.random() * delay_ms * jitter_factor
        return int(delay_ms + jitter)

    @staticmethod
    def calculate_linear_backoff(
        attempt: int,
        base_delay_ms: int,
        increment_ms: int = 1000,
        max_delay_ms: int = 30000
    ) -> int:
        """
        Calculate linear backoff delay.

        Formula: min(base_delay + (increment * attempt), max_delay)
        """
        delay = base_delay_ms + (increment_ms * attempt)
        return min(delay, max_delay_ms)

    @staticmethod
    def calculate_delay(
        attempt: int,
        config: RetryConfig
    ) -> int:
        """
        Calculate delay based on strategy in config.

        Args:
            attempt: Current attempt number (0-indexed)
            config: Retry configuration

        Returns:
            Delay in milliseconds
        """
        if config.strategy == RetryStrategy.EXPONENTIAL:
            delay = DelayCalculator.calculate_exponential_backoff(
                attempt,
                config.base_delay_ms,
                config.backoff_multiplier,
                config.max_delay_ms
            )

        elif config.strategy == RetryStrategy.EXPONENTIAL_WITH_JITTER:
            base_delay = DelayCalculator.calculate_exponential_backoff(
                attempt,
                config.base_delay_ms,
                config.backoff_multiplier,
                config.max_delay_ms
            )
            delay = DelayCalculator.add_jitter(base_delay, config.jitter_factor)

        elif config.strategy == RetryStrategy.LINEAR:
            delay = DelayCalculator.calculate_linear_backoff(
                attempt,
                config.base_delay_ms,
                config.base_delay_ms,  # Use base as increment
                config.max_delay_ms
            )

        elif config.strategy == RetryStrategy.FIXED:
            delay = config.base_delay_ms

        else:
            delay = config.base_delay_ms

        return delay


class ErrorClassifier:
    """Classifies errors and determines if they're retryable"""

    @staticmethod
    def classify_error(error: Exception) -> ErrorCategory:
        """
        Classify an error into a category.

        Args:
            error: Exception to classify

        Returns:
            ErrorCategory
        """
        if isinstance(error, RetryableError):
            return error.category

        error_msg = str(error).lower()
        error_type = type(error).__name__.lower()

        # Check error message and type for known patterns
        if 'click intercepted' in error_msg or 'clickintercepted' in error_type:
            return ErrorCategory.ELEMENT_CLICK_INTERCEPTED

        if 'not interactable' in error_msg or 'notinteractable' in error_type:
            return ErrorCategory.ELEMENT_NOT_INTERACTABLE

        if 'stale element' in error_msg or 'stale' in error_type:
            return ErrorCategory.STALE_ELEMENT_REFERENCE

        if 'not found' in error_msg or 'nosuchelement' in error_type:
            return ErrorCategory.ELEMENT_NOT_FOUND

        if 'timeout' in error_msg or 'timeout' in error_type:
            return ErrorCategory.TIMEOUT

        if 'network' in error_msg or 'connection' in error_msg:
            return ErrorCategory.NETWORK_ERROR

        return ErrorCategory.UNKNOWN

    @staticmethod
    def is_retryable(
        error: Exception,
        retryable_errors: Optional[List[ErrorCategory]] = None
    ) -> bool:
        """
        Determine if an error should trigger a retry.

        Args:
            error: Exception to check
            retryable_errors: List of retryable error categories (None = all common errors)

        Returns:
            True if error should be retried
        """
        # Default retryable errors
        if retryable_errors is None:
            retryable_errors = [
                ErrorCategory.ELEMENT_CLICK_INTERCEPTED,
                ErrorCategory.ELEMENT_NOT_INTERACTABLE,
                ErrorCategory.STALE_ELEMENT_REFERENCE,
                ErrorCategory.TIMEOUT,
            ]

        category = ErrorClassifier.classify_error(error)
        return category in retryable_errors


class RetryExecutor:
    """Executes operations with retry logic"""

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.delay_calculator = DelayCalculator()
        self.error_classifier = ErrorClassifier()

    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
        config: Optional[RetryConfig] = None
    ) -> RetryResult:
        """
        Execute an operation with retry logic.

        Args:
            operation: Async function to execute
            config: Retry configuration (uses default if None)

        Returns:
            RetryResult with outcome and history
        """
        cfg = config or self.config
        attempt_history: List[RetryAttempt] = []
        start_time = datetime.now()

        for attempt in range(cfg.max_retries):
            attempt_start = datetime.now()

            try:
                # Execute the operation
                result = await operation()

                # Success!
                attempt_history.append(RetryAttempt(
                    attempt_number=attempt,
                    timestamp=attempt_start,
                    error=None,
                    error_category=ErrorCategory.UNKNOWN,
                    delay_ms=0,
                    success=True
                ))

                total_time = (datetime.now() - start_time).total_seconds() * 1000

                return RetryResult(
                    success=True,
                    attempts=attempt + 1,
                    total_time_ms=total_time,
                    result=result,
                    error=None,
                    attempt_history=attempt_history
                )

            except Exception as error:
                # Classify the error
                error_category = self.error_classifier.classify_error(error)

                # Check if we should retry
                is_last_attempt = (attempt == cfg.max_retries - 1)
                is_retryable = self.error_classifier.is_retryable(
                    error,
                    cfg.retryable_errors
                )

                if is_last_attempt or not is_retryable:
                    # Record failed attempt
                    attempt_history.append(RetryAttempt(
                        attempt_number=attempt,
                        timestamp=attempt_start,
                        error=error,
                        error_category=error_category,
                        delay_ms=0,
                        success=False
                    ))

                    total_time = (datetime.now() - start_time).total_seconds() * 1000

                    return RetryResult(
                        success=False,
                        attempts=attempt + 1,
                        total_time_ms=total_time,
                        result=None,
                        error=error,
                        attempt_history=attempt_history
                    )

                # Calculate delay for next retry
                delay_ms = self.delay_calculator.calculate_delay(attempt, cfg)

                # Record attempt
                attempt_history.append(RetryAttempt(
                    attempt_number=attempt,
                    timestamp=attempt_start,
                    error=error,
                    error_category=error_category,
                    delay_ms=delay_ms,
                    success=False
                ))

                # Log retry
                print(f"🔄 Retry {attempt + 1}/{cfg.max_retries} after {delay_ms}ms "
                      f"({error_category.value}): {str(error)}")

                # Wait before retry
                await asyncio.sleep(delay_ms / 1000.0)

        # Should never reach here, but just in case
        total_time = (datetime.now() - start_time).total_seconds() * 1000

        return RetryResult(
            success=False,
            attempts=cfg.max_retries,
            total_time_ms=total_time,
            result=None,
            error=Exception("Max retries exceeded"),
            attempt_history=attempt_history
        )

    async def execute_with_condition(
        self,
        operation: Callable[[], Awaitable[T]],
        success_condition: Callable[[T], bool],
        config: Optional[RetryConfig] = None
    ) -> RetryResult:
        """
        Execute operation and retry if success condition is not met.

        Args:
            operation: Async function to execute
            success_condition: Function to validate result
            config: Retry configuration

        Returns:
            RetryResult
        """
        cfg = config or self.config

        async def validated_operation():
            result = await operation()

            if not success_condition(result):
                raise RetryableError(
                    "Success condition not met",
                    ErrorCategory.UNKNOWN
                )

            return result

        return await self.execute(validated_operation, cfg)


class CircuitBreaker:
    """
    Circuit breaker pattern for preventing cascading failures.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_ms: int = 60000,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_ms = recovery_timeout_ms
        self.success_threshold = success_threshold

        self.failure_count = 0
        self.success_count = 0
        self.state = "CLOSED"
        self.last_failure_time: Optional[datetime] = None

    async def execute(
        self,
        operation: Callable[[], Awaitable[T]]
    ) -> T:
        """
        Execute operation through circuit breaker.

        Args:
            operation: Async function to execute

        Returns:
            Result of operation

        Raises:
            Exception if circuit is open
        """
        # Check if circuit should transition from OPEN to HALF_OPEN
        if self.state == "OPEN":
            if self.last_failure_time:
                time_since_failure = (
                    datetime.now() - self.last_failure_time
                ).total_seconds() * 1000

                if time_since_failure >= self.recovery_timeout_ms:
                    self.state = "HALF_OPEN"
                    self.success_count = 0
                    print("🔄 Circuit breaker: OPEN -> HALF_OPEN")
                else:
                    raise Exception(
                        f"Circuit breaker is OPEN. "
                        f"Retry in {self.recovery_timeout_ms - time_since_failure:.0f}ms"
                    )

        try:
            result = await operation()

            # Operation succeeded
            if self.state == "HALF_OPEN":
                self.success_count += 1

                if self.success_count >= self.success_threshold:
                    self.state = "CLOSED"
                    self.failure_count = 0
                    print("✅ Circuit breaker: HALF_OPEN -> CLOSED")

            elif self.state == "CLOSED":
                # Reset failure count on success
                self.failure_count = 0

            return result

        except Exception as error:
            # Operation failed
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.state == "HALF_OPEN":
                # Failed during recovery, go back to OPEN
                self.state = "OPEN"
                self.success_count = 0
                print("❌ Circuit breaker: HALF_OPEN -> OPEN")

            elif self.state == "CLOSED":
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    print(f"⚠️  Circuit breaker: CLOSED -> OPEN "
                          f"({self.failure_count} failures)")

            raise error

    def reset(self):
        """Reset circuit breaker to CLOSED state"""
        self.state = "CLOSED"
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None


class AdaptiveRetryExecutor(RetryExecutor):
    """
    Retry executor that adapts based on success/failure patterns.

    Learns from previous attempts and adjusts retry behavior.
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        super().__init__(config)
        self.history: List[RetryResult] = []

    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
        config: Optional[RetryConfig] = None
    ) -> RetryResult:
        """
        Execute with adaptive retry logic.

        Adjusts retry delays based on historical success rates.
        """
        # Adapt config based on history
        adapted_config = self._adapt_config(config or self.config)

        # Execute with adapted config
        result = await super().execute(operation, adapted_config)

        # Record result
        self.history.append(result)

        return result

    def _adapt_config(self, base_config: RetryConfig) -> RetryConfig:
        """
        Adapt retry configuration based on historical performance.

        Returns:
            Adapted RetryConfig
        """
        if len(self.history) < 5:
            return base_config

        # Analyze recent history
        recent = self.history[-10:]
        success_rate = sum(1 for r in recent if r.success) / len(recent)
        avg_attempts = sum(r.attempts for r in recent) / len(recent)

        # Adapt based on success rate
        if success_rate < 0.5:
            # Low success rate - increase retries and delays
            return RetryConfig(
                max_retries=min(base_config.max_retries + 2, 10),
                base_delay_ms=int(base_config.base_delay_ms * 1.5),
                max_delay_ms=base_config.max_delay_ms,
                strategy=base_config.strategy,
                jitter_factor=base_config.jitter_factor,
                backoff_multiplier=base_config.backoff_multiplier,
                retryable_errors=base_config.retryable_errors
            )

        elif success_rate > 0.9 and avg_attempts < 2:
            # High success rate - reduce delays
            return RetryConfig(
                max_retries=base_config.max_retries,
                base_delay_ms=max(int(base_config.base_delay_ms * 0.8), 500),
                max_delay_ms=base_config.max_delay_ms,
                strategy=base_config.strategy,
                jitter_factor=base_config.jitter_factor,
                backoff_multiplier=base_config.backoff_multiplier,
                retryable_errors=base_config.retryable_errors
            )

        return base_config

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics from retry history"""
        if not self.history:
            return {}

        total = len(self.history)
        successful = sum(1 for r in self.history if r.success)

        avg_attempts = sum(r.attempts for r in self.history) / total
        avg_time = sum(r.total_time_ms for r in self.history) / total

        # Error category distribution
        error_categories = {}
        for result in self.history:
            for attempt in result.attempt_history:
                if not attempt.success:
                    cat = attempt.error_category.value
                    error_categories[cat] = error_categories.get(cat, 0) + 1

        return {
            'total_operations': total,
            'successful': successful,
            'success_rate': successful / total,
            'avg_attempts': avg_attempts,
            'avg_time_ms': avg_time,
            'error_distribution': error_categories
        }
