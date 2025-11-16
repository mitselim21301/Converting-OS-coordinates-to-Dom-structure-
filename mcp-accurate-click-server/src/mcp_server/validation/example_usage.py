"""
Comprehensive Example Usage of Click Validation System

Demonstrates all features:
- Pre-click validation
- Confidence scoring
- Retry logic with exponential backoff
- Post-click verification
- Complete validation pipeline
"""

import asyncio
from typing import Dict, Any

# Import all validation components
from . import (
    # Pre-click
    PreClickValidator,
    ValidationStatus,

    # Confidence
    ClickConfidenceCalculator,
    select_click_strategy,
    ActionType,
    ClickConfidenceMonitor,

    # Retry
    RetryExecutor,
    AdaptiveRetryExecutor,
    RetryConfig,
    RetryStrategy,
    ErrorCategory,
    ElementClickInterceptedError,
    CircuitBreaker,

    # Post-click
    PostClickValidator,
    ChangeType,
    ClickResultMonitor,
)


# ==============================================================================
# Example 1: Basic Pre-Click Validation
# ==============================================================================

async def example_pre_click_validation():
    """Basic pre-click validation example"""
    print("\n" + "="*80)
    print("Example 1: Pre-Click Validation")
    print("="*80)

    # Sample element data
    element_info = {
        'rect': {'left': 100, 'top': 200, 'width': 150, 'height': 40},
        'computed_style': {
            'display': 'block',
            'visibility': 'visible',
            'opacity': '1.0',
            'pointer_events': 'auto',
            'position': 'relative',
            'z_index': '1',
            'cursor': 'pointer',
        },
        'attributes': {
            'disabled': False,
            'readonly': False,
            'aria_disabled': 'false',
            'class': 'btn btn-primary',
        },
        'tag_name': 'BUTTON',
        'viewport': {'width': 1920, 'height': 1080},
        'has_hover_styles': True,
        'check_visibility': True,
    }

    validator = PreClickValidator()
    result = await validator.validate(element_info)

    print(f"\n✨ Validation Status: {result.status.value}")
    print(f"✅ Can Proceed: {result.can_proceed}")

    if result.issues:
        print(f"\n⚠️  Issues Found ({len(result.issues)}):")
        for issue in result.issues:
            print(f"   [{issue.severity.upper()}] {issue.category}: {issue.message}")

    if result.recommendations:
        print(f"\n💡 Recommendations:")
        for rec in result.recommendations:
            print(f"   - {rec}")

    print(f"\n📊 Details:")
    print(f"   Error count: {result.details['error_count']}")
    print(f"   Warning count: {result.details['warning_count']}")

    return result


# ==============================================================================
# Example 2: Confidence Scoring
# ==============================================================================

async def example_confidence_scoring():
    """Confidence scoring example"""
    print("\n" + "="*80)
    print("Example 2: Confidence Scoring")
    print("="*80)

    element_info = {
        'rect': {'left': 100, 'top': 200, 'width': 150, 'height': 40},
        'computed_style': {
            'display': 'block',
            'visibility': 'visible',
            'opacity': '1.0',
            'pointer_events': 'auto',
        },
        'attributes': {'disabled': False},
        'tag_name': 'BUTTON',
        'viewport': {'width': 1920, 'height': 1080},
        'hit_test_results': [
            {'x': 175, 'y': 220, 'is_target': True},  # Center
            {'x': 137, 'y': 210, 'is_target': True},  # Top-left quad
            {'x': 212, 'y': 210, 'is_target': True},  # Top-right quad
            {'x': 137, 'y': 230, 'is_target': True},  # Bottom-left quad
            {'x': 212, 'y': 230, 'is_target': True},  # Bottom-right quad
        ],
    }

    page_context = {
        'ready_state': 'complete',
        'active_animations': 0,
        'pending_requests': 0,
    }

    calculator = ClickConfidenceCalculator()
    result = await calculator.calculate_confidence(element_info, page_context)

    print(f"\n📊 Confidence Score: {result.confidence}%")
    print(f"💡 Recommendation: {result.recommendation.value}")
    print(f"✅ Safe to Click: {result.safe}")

    print(f"\n🔍 Score Breakdown:")
    for component, score in result.details['score_breakdown'].items():
        print(f"   {component.capitalize()}: {score}")

    if result.issues:
        print(f"\n⚠️  Issues:")
        for issue in result.issues:
            print(f"   - {issue}")

    # Select click strategy
    strategy = select_click_strategy(result.confidence, ActionType.STANDARD_CLICK)
    print(f"\n🎯 Recommended Strategy: {strategy.value}")

    return result


# ==============================================================================
# Example 3: Retry Logic with Exponential Backoff
# ==============================================================================

async def example_retry_logic():
    """Retry logic with exponential backoff example"""
    print("\n" + "="*80)
    print("Example 3: Retry Logic")
    print("="*80)

    # Simulate a click operation that fails a few times
    attempt_count = [0]

    async def flaky_click_operation():
        """Simulates a click that fails first 2 times"""
        attempt_count[0] += 1
        print(f"   Attempt #{attempt_count[0]}")

        if attempt_count[0] < 3:
            raise ElementClickInterceptedError(
                f"Click intercepted by overlay (attempt {attempt_count[0]})"
            )

        print(f"   ✅ Click succeeded!")
        return {'success': True}

    # Configure retry
    config = RetryConfig(
        max_retries=5,
        base_delay_ms=500,
        max_delay_ms=10000,
        strategy=RetryStrategy.EXPONENTIAL_WITH_JITTER,
        jitter_factor=0.5,
    )

    executor = RetryExecutor(config)

    print(f"\n🔄 Executing with retry (max {config.max_retries} attempts)...\n")

    result = await executor.execute(flaky_click_operation)

    print(f"\n📊 Results:")
    print(f"   Success: {result.success}")
    print(f"   Total Attempts: {result.attempts}")
    print(f"   Total Time: {result.total_time_ms:.0f}ms")

    print(f"\n📋 Attempt History:")
    for attempt in result.attempt_history:
        status = "✅ SUCCESS" if attempt.success else f"❌ FAILED ({attempt.error_category.value})"
        print(f"   Attempt {attempt.attempt_number + 1}: {status}")
        if not attempt.success and attempt.delay_ms > 0:
            print(f"      Delay before retry: {attempt.delay_ms}ms")

    return result


# ==============================================================================
# Example 4: Adaptive Retry
# ==============================================================================

async def example_adaptive_retry():
    """Adaptive retry that learns from history"""
    print("\n" + "="*80)
    print("Example 4: Adaptive Retry Executor")
    print("="*80)

    executor = AdaptiveRetryExecutor()

    # Simulate 20 operations with varying success
    print(f"\n🔄 Running 20 operations with adaptive retry...\n")

    for i in range(20):
        attempt_in_op = [0]

        async def operation():
            attempt_in_op[0] += 1
            # Simulate 70% success rate
            if attempt_in_op[0] == 1 and i % 10 < 3:  # Fail 30% on first attempt
                raise ElementClickInterceptedError("Intercepted")
            return {'success': True}

        result = await executor.execute(operation)

        status = "✅" if result.success else "❌"
        print(f"   Op {i+1:2d}: {status} ({result.attempts} attempts, {result.total_time_ms:.0f}ms)")

    # Get statistics
    stats = executor.get_statistics()

    print(f"\n📊 Statistics:")
    print(f"   Total Operations: {stats['total_operations']}")
    print(f"   Success Rate: {stats['success_rate']:.1%}")
    print(f"   Avg Attempts: {stats['avg_attempts']:.2f}")
    print(f"   Avg Time: {stats['avg_time_ms']:.0f}ms")

    return executor


# ==============================================================================
# Example 5: Circuit Breaker
# ==============================================================================

async def example_circuit_breaker():
    """Circuit breaker pattern example"""
    print("\n" + "="*80)
    print("Example 5: Circuit Breaker")
    print("="*80)

    breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout_ms=2000,
        success_threshold=2
    )

    # Simulate operations
    call_count = [0]

    async def operation():
        call_count[0] += 1
        # Fail first 5 calls
        if call_count[0] <= 5:
            raise Exception(f"Service unavailable (call {call_count[0]})")
        return {'success': True}

    print(f"\n🔄 Making calls through circuit breaker...\n")

    for i in range(10):
        try:
            result = await breaker.execute(operation)
            print(f"   Call {i+1}: ✅ SUCCESS (state: {breaker.state})")
        except Exception as e:
            print(f"   Call {i+1}: ❌ FAILED - {str(e)[:50]} (state: {breaker.state})")

        await asyncio.sleep(0.5)

    return breaker


# ==============================================================================
# Example 6: Post-Click Validation
# ==============================================================================

async def example_post_click_validation():
    """Post-click validation example"""
    print("\n" + "="*80)
    print("Example 6: Post-Click Validation")
    print("="*80)

    # State before click
    previous_state = {
        'attributes': {
            'aria_expanded': 'false',
            'class': 'dropdown-toggle'
        },
        'computed_style': {
            'display': 'block',
            'opacity': '1.0'
        },
        'text_content': 'Menu',
        'url': 'https://example.com/page',
        'focused_element': None,
    }

    # State after click (dropdown opened)
    element_info = {
        'attributes': {
            'aria_expanded': 'true',  # Changed!
            'class': 'dropdown-toggle active'  # Changed!
        },
        'computed_style': {
            'display': 'block',
            'opacity': '1.0'
        },
        'text_content': 'Menu',
    }

    page_context = {
        'url': 'https://example.com/page',
        'focused_element': '#dropdown-menu',
        'new_elements': [
            {
                'selector': '#dropdown-menu',
                'tag_name': 'UL',
                'role': 'menu',
                'type': 'dropdown'
            }
        ],
        'removed_elements': [],
        'event_log': [
            {
                'type': 'click',
                'timestamp': 1234567890,
                'target': '.dropdown-toggle',
                'stopped_propagation': False,
                'default_prevented': False,
            }
        ],
        'network_log': [],
    }

    validator = PostClickValidator()

    result = await validator.validate(
        element_info=element_info,
        previous_state=previous_state,
        page_context=page_context,
        expected_changes=[ChangeType.ARIA_CHANGED, ChangeType.ELEMENT_APPEARED],
        timeout_ms=100
    )

    print(f"\n✨ Validation Result: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
    print(f"📊 Changes Detected: {len(result.changes_detected)}")
    print(f"⏱️  Verification Time: {result.verification_time_ms:.1f}ms")

    print(f"\n🔍 Detected Changes:")
    for change in result.changes_detected:
        print(f"   - {change.change_type.value}")
        if change.details:
            for key, value in change.details.items():
                print(f"      {key}: {value}")

    print(f"\n📋 Event Analysis:")
    event_analysis = result.details['event_analysis']
    print(f"   Event Fired: {event_analysis['event_fired']}")
    print(f"   Propagated: {event_analysis['propagated']}")
    print(f"   Default Prevented: {event_analysis['prevented']}")

    return result


# ==============================================================================
# Example 7: Complete Validation Pipeline
# ==============================================================================

async def example_complete_pipeline():
    """Complete validation pipeline example"""
    print("\n" + "="*80)
    print("Example 7: Complete Validation Pipeline")
    print("="*80)

    # Element and page data
    element_info = {
        'rect': {'left': 100, 'top': 200, 'width': 150, 'height': 40},
        'computed_style': {
            'display': 'block',
            'visibility': 'visible',
            'opacity': '1.0',
            'pointer_events': 'auto',
        },
        'attributes': {
            'disabled': False,
            'class': 'btn btn-submit',
            'aria_disabled': 'false',
        },
        'tag_name': 'BUTTON',
        'viewport': {'width': 1920, 'height': 1080},
        'hit_test_results': [
            {'x': 175, 'y': 220, 'is_target': True},
        ],
        'check_visibility': True,
    }

    page_context = {
        'ready_state': 'complete',
        'active_animations': 0,
        'pending_requests': 0,
        'url': 'https://example.com/form',
    }

    print("\n" + "-"*80)
    print("STEP 1: Pre-Click Validation")
    print("-"*80)

    pre_validator = PreClickValidator()
    pre_result = await pre_validator.validate(element_info)

    print(f"Status: {pre_result.status.value}")
    print(f"Can Proceed: {pre_result.can_proceed}")

    if not pre_result.can_proceed:
        print("❌ Cannot proceed - validation failed")
        return None

    print("\n" + "-"*80)
    print("STEP 2: Confidence Scoring")
    print("-"*80)

    calculator = ClickConfidenceCalculator()
    confidence = await calculator.calculate_confidence(element_info, page_context)

    print(f"Confidence: {confidence.confidence}%")
    print(f"Recommendation: {confidence.recommendation.value}")

    if confidence.confidence < 70:
        print(f"⚠️  Low confidence: {confidence.confidence}%")
        print(f"Issues: {', '.join(confidence.issues)}")

    print("\n" + "-"*80)
    print("STEP 3: Capture Pre-Click State")
    print("-"*80)

    previous_state = {
        'attributes': element_info.get('attributes', {}).copy(),
        'computed_style': element_info.get('computed_style', {}).copy(),
        'url': page_context['url'],
    }

    print("State captured ✅")

    print("\n" + "-"*80)
    print("STEP 4: Execute Click with Retry")
    print("-"*80)

    attempt_count = [0]

    async def click_operation():
        attempt_count[0] += 1
        print(f"   Executing click (attempt {attempt_count[0]})...")

        # Simulate occasional failure
        if attempt_count[0] == 1:
            raise ElementClickInterceptedError("Modal overlay blocking click")

        return {'success': True}

    config = RetryConfig(max_retries=3, base_delay_ms=500)
    executor = RetryExecutor(config)

    retry_result = await executor.execute(click_operation)

    print(f"\nClick Result: {'✅ SUCCESS' if retry_result.success else '❌ FAILED'}")
    print(f"Attempts: {retry_result.attempts}")
    print(f"Time: {retry_result.total_time_ms:.0f}ms")

    print("\n" + "-"*80)
    print("STEP 5: Post-Click Verification")
    print("-"*80)

    # Simulate post-click state
    post_page_context = {
        'url': 'https://example.com/success',  # URL changed
        'focused_element': '#success-message',
        'new_elements': [
            {'selector': '#success-message', 'tag_name': 'DIV', 'role': 'alert'}
        ],
        'event_log': [
            {'type': 'click', 'timestamp': 123, 'target': '.btn-submit'}
        ],
        'network_log': [
            {'url': '/api/submit', 'method': 'POST', 'status': 200}
        ],
    }

    post_validator = PostClickValidator()
    post_result = await post_validator.validate(
        element_info=element_info,
        previous_state=previous_state,
        page_context=post_page_context,
        timeout_ms=100
    )

    print(f"Validation: {'✅ SUCCESS' if post_result.success else '❌ FAILED'}")
    print(f"Changes: {len(post_result.changes_detected)}")
    print(f"Expected Changes Met: {post_result.expected_changes_met}")

    print("\n" + "="*80)
    print("✅ PIPELINE COMPLETE")
    print("="*80)

    return {
        'pre_validation': pre_result.can_proceed,
        'confidence': confidence.confidence,
        'click_success': retry_result.success,
        'post_validation': post_result.success,
        'total_attempts': retry_result.attempts,
    }


# ==============================================================================
# Example 8: Monitoring
# ==============================================================================

async def example_monitoring():
    """Monitoring example"""
    print("\n" + "="*80)
    print("Example 8: Confidence Monitoring")
    print("="*80)

    monitor = ClickConfidenceMonitor()
    calculator = ClickConfidenceCalculator()

    # Simulate multiple clicks with varying confidence
    print(f"\n🔄 Simulating 15 click operations...\n")

    for i in range(15):
        # Vary element quality
        opacity = 1.0 if i % 5 != 0 else 0.3  # Some with low opacity

        element_info = {
            'rect': {'left': 100, 'top': 200, 'width': 150, 'height': 40},
            'computed_style': {
                'display': 'block',
                'visibility': 'visible',
                'opacity': str(opacity),
                'pointer_events': 'auto',
            },
            'attributes': {'disabled': False},
            'tag_name': 'BUTTON',
            'viewport': {'width': 1920, 'height': 1080},
            'hit_test_results': [
                {'x': 175, 'y': 220, 'is_target': i % 3 != 0}  # Some obscured
            ],
        }

        page_context = {
            'ready_state': 'complete',
            'active_animations': 1 if i % 4 == 0 else 0,  # Some animating
            'pending_requests': 0,
        }

        confidence = await calculator.calculate_confidence(element_info, page_context)
        success = confidence.confidence >= 70

        monitor.log_click_attempt(
            selector=f'#element-{i}',
            confidence_result=confidence,
            success=success
        )

        status = "✅" if success else "❌"
        print(f"   Click {i+1:2d}: {status} Confidence: {confidence.confidence}%")

    # Get statistics
    stats = monitor.get_statistics()

    print(f"\n📊 Overall Statistics:")
    print(f"   Total Attempts: {stats['total_attempts']}")
    print(f"   Successful: {stats['successful']}")
    print(f"   Success Rate: {stats['success_rate']:.1%}")
    print(f"   Avg Confidence: {stats['avg_confidence']:.1f}%")
    print(f"   Min Confidence: {stats['min_confidence']}%")
    print(f"   Max Confidence: {stats['max_confidence']}%")

    if stats['common_issues']:
        print(f"\n⚠️  Common Issues:")
        for issue in stats['common_issues']:
            print(f"   - {issue}")

    return monitor


# ==============================================================================
# Main Example Runner
# ==============================================================================

async def run_all_examples():
    """Run all examples"""
    print("\n" + "="*80)
    print("CLICK VALIDATION SYSTEM - COMPREHENSIVE EXAMPLES")
    print("="*80)

    try:
        # Run all examples
        await example_pre_click_validation()
        await asyncio.sleep(0.5)

        await example_confidence_scoring()
        await asyncio.sleep(0.5)

        await example_retry_logic()
        await asyncio.sleep(0.5)

        await example_adaptive_retry()
        await asyncio.sleep(0.5)

        await example_circuit_breaker()
        await asyncio.sleep(0.5)

        await example_post_click_validation()
        await asyncio.sleep(0.5)

        await example_complete_pipeline()
        await asyncio.sleep(0.5)

        await example_monitoring()

        print("\n" + "="*80)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(run_all_examples())
