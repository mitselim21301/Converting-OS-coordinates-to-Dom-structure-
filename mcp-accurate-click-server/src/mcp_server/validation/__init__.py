"""
Click Validation System

Comprehensive validation system for accurate click operations including:
- Pre-click validation (visibility, interactability, stability, hit target)
- Post-click verification (state changes, event validation)
- Retry logic with exponential backoff and jitter
- Confidence scoring (0-100 scale)

This module provides production-ready validation for converting OS coordinates
to DOM structure interactions.

Example Usage:
    >>> from mcp_server.validation import (
    ...     PreClickValidator,
    ...     PostClickValidator,
    ...     ClickConfidenceCalculator,
    ...     RetryExecutor,
    ...     RetryConfig
    ... )
    ...
    >>> # Pre-click validation
    >>> validator = PreClickValidator()
    >>> result = await validator.validate(element_info)
    >>> if result.can_proceed:
    ...     # Safe to click
    ...     click_element()
    ...
    >>> # Confidence scoring
    >>> calculator = ClickConfidenceCalculator()
    >>> confidence = await calculator.calculate_confidence(element_info)
    >>> print(f"Confidence: {confidence.confidence}%")
    ...
    >>> # Retry with exponential backoff
    >>> executor = RetryExecutor(RetryConfig(max_retries=5))
    >>> result = await executor.execute(click_operation)

Reference: CLICK_VALIDATION_RESEARCH.md
"""

# Pre-click validation
from .pre_click import (
    PreClickValidator,
    ValidationStatus,
    ValidationIssue,
    PreClickValidationResult,
    VisibilityChecker,
    InteractabilityChecker,
    StabilityChecker,
    HitTargetChecker,
    HoverStateChecker,
)

# Post-click validation
from .post_click import (
    PostClickValidator,
    ChangeType,
    StateChange,
    PostClickValidationResult,
    DOMChangeDetector,
    PageStateDetector,
    NetworkActivityDetector,
    EventValidation,
    ClickResultMonitor,
)

# Confidence scoring
from .confidence import (
    ClickConfidenceCalculator,
    ConfidenceResult,
    ConfidenceScores,
    Recommendation,
    ActionType,
    ClickStrategy,
    ClickConfidenceMonitor,
    select_click_strategy,
)

# Retry logic
from .retry import (
    RetryExecutor,
    AdaptiveRetryExecutor,
    RetryConfig,
    RetryResult,
    RetryAttempt,
    RetryStrategy,
    ErrorCategory,
    RetryableError,
    ElementClickInterceptedError,
    ElementNotInteractableError,
    StaleElementError,
    DelayCalculator,
    ErrorClassifier,
    CircuitBreaker,
)


__all__ = [
    # Pre-click validation
    'PreClickValidator',
    'ValidationStatus',
    'ValidationIssue',
    'PreClickValidationResult',
    'VisibilityChecker',
    'InteractabilityChecker',
    'StabilityChecker',
    'HitTargetChecker',
    'HoverStateChecker',

    # Post-click validation
    'PostClickValidator',
    'ChangeType',
    'StateChange',
    'PostClickValidationResult',
    'DOMChangeDetector',
    'PageStateDetector',
    'NetworkActivityDetector',
    'EventValidation',
    'ClickResultMonitor',

    # Confidence scoring
    'ClickConfidenceCalculator',
    'ConfidenceResult',
    'ConfidenceScores',
    'Recommendation',
    'ActionType',
    'ClickStrategy',
    'ClickConfidenceMonitor',
    'select_click_strategy',

    # Retry logic
    'RetryExecutor',
    'AdaptiveRetryExecutor',
    'RetryConfig',
    'RetryResult',
    'RetryAttempt',
    'RetryStrategy',
    'ErrorCategory',
    'RetryableError',
    'ElementClickInterceptedError',
    'ElementNotInteractableError',
    'StaleElementError',
    'DelayCalculator',
    'ErrorClassifier',
    'CircuitBreaker',
]


__version__ = '1.0.0'
__author__ = 'MCP Accurate Click Server Team'
__description__ = 'Comprehensive click validation system for accurate DOM interactions'
