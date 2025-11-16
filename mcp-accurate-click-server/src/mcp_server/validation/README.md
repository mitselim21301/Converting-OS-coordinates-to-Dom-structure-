# Click Validation System

Comprehensive validation system for accurate click operations when converting OS coordinates to DOM structure interactions.

## Overview

This validation system provides production-ready components for:

1. **Pre-Click Validation** - Verify element is ready to be clicked
2. **Confidence Scoring** - Score click reliability (0-100%)
3. **Retry Logic** - Robust retry with exponential backoff
4. **Post-Click Verification** - Validate click produced expected results

## Components

### 1. Pre-Click Validation (`pre_click.py`)

Validates element before clicking:

- ✅ **Visibility checks** (checkVisibility API, computed styles)
- ✅ **Interactability validation** (enabled, pointer-events)
- ✅ **Stability checks** (position not animating)
- ✅ **Element-at-point verification** (not obscured)
- ✅ **Z-index handling** (stacking context analysis)
- ✅ **Hover state validation**

#### Usage

```python
from mcp_server.validation import PreClickValidator

validator = PreClickValidator()

# Full validation
result = await validator.validate(element_info)

if result.can_proceed:
    print(f"✅ Element is ready to click")
else:
    print(f"❌ Issues found:")
    for issue in result.issues:
        print(f"  - {issue.message}")

    print(f"Recommendations:")
    for rec in result.recommendations:
        print(f"  - {rec}")

# Quick validation (fast checks only)
can_click = await validator.quick_validate(element_info)
```

### 2. Confidence Scoring (`confidence.py`)

Calculates confidence score (0-100%) for click operations:

**Score Components:**
- Visibility: 25%
- Interactability: 25%
- Stability: 20%
- Hit Target: 20%
- Timing: 10%

#### Usage

```python
from mcp_server.validation import (
    ClickConfidenceCalculator,
    select_click_strategy,
    ActionType
)

calculator = ClickConfidenceCalculator()

# Calculate confidence
result = await calculator.calculate_confidence(
    element_info=element_data,
    page_context=page_data
)

print(f"Confidence: {result.confidence}%")
print(f"Recommendation: {result.recommendation.value}")

if not result.safe:
    print(f"Issues:")
    for issue in result.issues:
        print(f"  - {issue}")

# Select click strategy based on confidence
strategy = select_click_strategy(
    result.confidence,
    ActionType.CRITICAL_ACTION  # Higher threshold for critical actions
)

print(f"Strategy: {strategy.value}")
```

#### Confidence Thresholds

| Action Type | Threshold |
|-------------|-----------|
| CRITICAL_ACTION | 95% (financial, deletions) |
| STANDARD_CLICK | 80% (navigation, forms) |
| EXPLORATORY | 60% (testing) |
| FALLBACK | 40% (use alternative) |

### 3. Retry Logic (`retry.py`)

Robust retry with exponential backoff and jitter:

- ✅ **Exponential backoff** with configurable multiplier
- ✅ **Random jitter** to prevent thundering herd
- ✅ **Error classification** (retry only on specific errors)
- ✅ **Circuit breaker** pattern
- ✅ **Adaptive retry** (learns from history)

#### Usage

```python
from mcp_server.validation import (
    RetryExecutor,
    RetryConfig,
    RetryStrategy,
    ErrorCategory
)

# Configure retry behavior
config = RetryConfig(
    max_retries=5,
    base_delay_ms=1000,
    max_delay_ms=30000,
    strategy=RetryStrategy.EXPONENTIAL_WITH_JITTER,
    jitter_factor=1.0,
    retryable_errors=[
        ErrorCategory.ELEMENT_CLICK_INTERCEPTED,
        ErrorCategory.ELEMENT_NOT_INTERACTABLE,
        ErrorCategory.STALE_ELEMENT_REFERENCE,
    ]
)

executor = RetryExecutor(config)

# Execute with retry
result = await executor.execute(click_operation)

if result.success:
    print(f"✅ Success after {result.attempts} attempts")
    print(f"Total time: {result.total_time_ms:.0f}ms")
else:
    print(f"❌ Failed after {result.attempts} attempts")
    print(f"Error: {result.error}")

# Execute with success condition
result = await executor.execute_with_condition(
    operation=click_and_check,
    success_condition=lambda r: r.get('success') == True
)
```

#### Adaptive Retry

```python
from mcp_server.validation import AdaptiveRetryExecutor

# Learns from previous attempts and adapts
executor = AdaptiveRetryExecutor()

for i in range(100):
    result = await executor.execute(operation)

# Get statistics
stats = executor.get_statistics()
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Avg attempts: {stats['avg_attempts']:.1f}")
```

#### Circuit Breaker

```python
from mcp_server.validation import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout_ms=60000,  # Try recovery after 60s
    success_threshold=2        # Close after 2 successes
)

try:
    result = await breaker.execute(risky_operation)
except Exception as e:
    print(f"Circuit breaker prevented call: {e}")
```

### 4. Post-Click Verification (`post_click.py`)

Validates that click produced expected results:

- ✅ **DOM mutation detection** (attributes, classes, text)
- ✅ **State change detection** (URL, focus, visibility)
- ✅ **Event validation** (click event fired and handled)
- ✅ **Network activity** (XHR, fetch requests)
- ✅ **Visual changes** (new elements, style changes)

#### Usage

```python
from mcp_server.validation import (
    PostClickValidator,
    ChangeType
)

validator = PostClickValidator()

# Capture state before click
previous_state = capture_state(element)
page_before = capture_page_state()

# Perform click
element.click()

# Validate after click
result = await validator.validate(
    element_info=element.get_info(),
    previous_state=previous_state,
    page_context=capture_page_state(),
    expected_changes=[
        ChangeType.ARIA_CHANGED,
        ChangeType.CLASS_CHANGED
    ],
    timeout_ms=1000
)

if result.success:
    print(f"✅ Click successful")
    print(f"Changes detected: {len(result.changes_detected)}")

    for change in result.changes_detected:
        print(f"  - {change.change_type.value}: {change.details}")
else:
    print(f"❌ Click failed or produced no changes")
```

## Complete Example

### Full Click Validation Pipeline

```python
import asyncio
from mcp_server.validation import (
    PreClickValidator,
    ClickConfidenceCalculator,
    RetryExecutor,
    PostClickValidator,
    RetryConfig,
    ActionType
)

async def robust_click(element_info, page_context):
    """
    Perform a robust click with full validation.
    """
    # Step 1: Pre-click validation
    pre_validator = PreClickValidator()
    pre_result = await pre_validator.validate(element_info)

    if not pre_result.can_proceed:
        raise Exception(
            f"Pre-click validation failed: {pre_result.issues}"
        )

    # Step 2: Calculate confidence
    calculator = ClickConfidenceCalculator()
    confidence = await calculator.calculate_confidence(
        element_info,
        page_context
    )

    if confidence.confidence < 80:
        raise Exception(
            f"Confidence too low: {confidence.confidence}%"
        )

    print(f"📊 Confidence: {confidence.confidence}%")
    print(f"📋 Recommendation: {confidence.recommendation.value}")

    # Step 3: Capture pre-click state
    previous_state = {
        'attributes': element_info.get('attributes', {}),
        'computed_style': element_info.get('computed_style', {}),
        'url': page_context.get('url', ''),
        'focused_element': page_context.get('focused_element')
    }

    # Step 4: Perform click with retry
    config = RetryConfig(max_retries=3)
    executor = RetryExecutor(config)

    async def click_operation():
        # Your actual click implementation
        await perform_click(element_info)
        return True

    retry_result = await executor.execute(click_operation)

    if not retry_result.success:
        raise Exception(
            f"Click failed after {retry_result.attempts} attempts"
        )

    print(f"✅ Click succeeded after {retry_result.attempts} attempts")

    # Step 5: Post-click validation
    post_validator = PostClickValidator()
    post_result = await post_validator.validate(
        element_info=element_info,
        previous_state=previous_state,
        page_context=page_context,
        timeout_ms=1000
    )

    if post_result.success:
        print(f"✅ Post-click validation passed")
        print(f"   Changes: {len(post_result.changes_detected)}")
    else:
        print(f"⚠️  Warning: No changes detected after click")

    return {
        'success': True,
        'confidence': confidence.confidence,
        'attempts': retry_result.attempts,
        'changes': len(post_result.changes_detected)
    }

# Usage
async def main():
    element_info = {
        'rect': {'left': 100, 'top': 200, 'width': 150, 'height': 40},
        'computed_style': {
            'display': 'block',
            'visibility': 'visible',
            'opacity': '1.0',
            'pointer_events': 'auto'
        },
        'attributes': {
            'disabled': False,
            'aria_disabled': 'false',
            'class': 'btn btn-primary'
        },
        'tag_name': 'BUTTON',
        'viewport': {'width': 1920, 'height': 1080}
    }

    page_context = {
        'ready_state': 'complete',
        'active_animations': 0,
        'pending_requests': 0,
        'url': 'https://example.com'
    }

    result = await robust_click(element_info, page_context)
    print(f"Result: {result}")

if __name__ == '__main__':
    asyncio.run(main())
```

## Element Info Structure

The validation system expects element information in this format:

```python
element_info = {
    # Bounding rectangle
    'rect': {
        'left': float,    # X coordinate
        'top': float,     # Y coordinate
        'width': float,   # Width in pixels
        'height': float,  # Height in pixels
    },

    # Computed CSS styles
    'computed_style': {
        'display': str,           # 'block', 'none', etc.
        'visibility': str,        # 'visible', 'hidden'
        'opacity': str,           # '0.0' to '1.0'
        'pointer_events': str,    # 'auto', 'none'
        'position': str,          # 'static', 'relative', 'absolute', 'fixed'
        'z_index': str,           # '0', 'auto', etc.
        'cursor': str,            # 'pointer', 'default', etc.
    },

    # HTML attributes
    'attributes': {
        'disabled': bool,
        'readonly': bool,
        'aria_disabled': str,     # 'true', 'false'
        'aria_expanded': str,
        'aria_selected': str,
        'class': str,             # Space-separated classes
    },

    # Element properties
    'tag_name': str,              # 'BUTTON', 'A', 'INPUT', etc.
    'text_content': str,          # Text content of element

    # Viewport information
    'viewport': {
        'width': int,             # Viewport width
        'height': int,            # Viewport height
    },

    # Optional: Stability data
    'position_history': [         # List of recent positions
        {'x': float, 'y': float, 'width': float, 'height': float},
        # ... more positions
    ],

    # Optional: Hit test results
    'hit_test_results': [
        {
            'x': float,           # Test point X
            'y': float,           # Test point Y
            'is_target': bool,    # True if element receives click at this point
            'actual_element': str # Selector of element at this point
        },
        # ... more test points
    ],

    # Optional: Hover and animation
    'has_hover_styles': bool,     # Element has :hover CSS
    'has_animations': bool,       # Element has active animations
    'check_visibility': bool,     # Result of checkVisibility() API
}
```

## Page Context Structure

```python
page_context = {
    # Page state
    'ready_state': str,           # 'loading', 'interactive', 'complete'
    'url': str,                   # Current URL
    'focused_element': str,       # Selector of focused element

    # Activity indicators
    'active_animations': int,     # Number of active animations
    'pending_requests': int,      # Number of pending XHR/fetch requests

    # Change detection
    'new_elements': [             # Elements that appeared
        {
            'selector': str,
            'tag_name': str,
            'role': str,
            'type': str          # 'modal', 'dropdown', 'tooltip', etc.
        }
    ],
    'removed_elements': [         # Elements that disappeared
        {'selector': str, 'tag_name': str}
    ],

    # Event log
    'event_log': [                # Captured events
        {
            'type': str,          # 'click', 'mousedown', 'mouseup'
            'timestamp': float,
            'target': str,
            'stopped_propagation': bool,
            'default_prevented': bool,
        }
    ],

    # Network log
    'network_log': [              # Network requests
        {
            'url': str,
            'method': str,        # 'GET', 'POST', etc.
            'status': int,        # HTTP status code
            'type': str,          # 'xhr', 'fetch'
            'timestamp': float,
        }
    ]
}
```

## Error Handling

All validation methods are designed to be defensive and handle missing data gracefully:

```python
# Missing data is handled safely
element_info = {
    'rect': {'left': 100, 'top': 200}  # Missing width/height
}

# Validation will use defaults or skip unavailable checks
result = await validator.validate(element_info)
```

## Performance Considerations

- **Quick validation**: Use `quick_validate()` for fast checks
- **Selective checks**: Pass `checks` parameter to run specific validations
- **Timeouts**: Configure appropriate timeouts for your use case
- **Adaptive retry**: Use `AdaptiveRetryExecutor` for learning retry behavior

## Best Practices

1. ✅ **Always run pre-click validation** before clicking
2. ✅ **Use confidence scoring** for critical actions
3. ✅ **Implement retry logic** for unreliable elements
4. ✅ **Verify post-click changes** for important operations
5. ✅ **Monitor validation metrics** using built-in monitors
6. ✅ **Adjust thresholds** based on your application's needs
7. ✅ **Handle validation failures gracefully** with appropriate fallbacks

## Reference

Based on comprehensive research in:
- `/CLICK_VALIDATION_RESEARCH.md`
- Section 1: Pre-Click Validation Techniques
- Section 2: Post-Click Validation
- Section 3: Retry Strategies with Exponential Backoff
- Section 5: Element Visibility and Interactability Checks
- Section 6: Handling Overlapping Elements and Z-Index
- Section 8: Confidence Scoring for Click Locations

## License

MIT License - Part of MCP Accurate Click Server project
