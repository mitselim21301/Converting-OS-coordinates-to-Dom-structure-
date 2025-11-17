"""
Comprehensive Test Suite for Validation Modules

Tests all 4 validation modules with 50+ tests:
1. pre_click.py - Pre-click validation (visibility, interactability, stability, hit target, hover)
2. post_click.py - Post-click verification (DOM changes, page state, network, events)
3. confidence.py - Confidence scoring algorithms
4. retry.py - Retry mechanisms with exponential backoff

Target: 85%+ coverage for validation module
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import validation modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server.validation.pre_click import (
    VisibilityChecker,
    InteractabilityChecker,
    StabilityChecker,
    HitTargetChecker,
    HoverStateChecker,
    PreClickValidator,
    ValidationStatus,
    ValidationIssue,
)

from mcp_server.validation.post_click import (
    DOMChangeDetector,
    PageStateDetector,
    NetworkActivityDetector,
    EventValidation,
    PostClickValidator,
    ClickResultMonitor,
    ChangeType,
    StateChange,
)

from mcp_server.validation.confidence import (
    ClickConfidenceCalculator,
    ClickConfidenceMonitor,
    select_click_strategy,
    Recommendation,
    ActionType,
    ClickStrategy,
)

from mcp_server.validation.retry import (
    DelayCalculator,
    ErrorClassifier,
    RetryExecutor,
    CircuitBreaker,
    AdaptiveRetryExecutor,
    RetryConfig,
    RetryStrategy,
    ErrorCategory,
    RetryableError,
    ElementClickInterceptedError,
    ElementNotInteractableError,
    StaleElementError,
)


# ============================================================================
# Test Pre-Click Validation Module
# ============================================================================

class TestVisibilityChecker:
    """Test VisibilityChecker class"""

    def test_check_visibility_valid_element(self):
        """Test visibility check for valid visible element"""
        element_info = {
            'rect': {'width': 100, 'height': 50, 'left': 100, 'top': 100},
            'computed_style': {
                'display': 'block',
                'visibility': 'visible',
                'opacity': 1.0
            },
            'viewport': {'width': 1920, 'height': 1080},
            'check_visibility': True
        }

        visible, issues = VisibilityChecker.check_visibility(element_info)

        assert visible is True
        assert all(issue.severity != 'error' for issue in issues)

    def test_check_visibility_zero_dimensions(self):
        """Test visibility check fails for zero dimensions"""
        element_info = {
            'rect': {'width': 0, 'height': 0, 'left': 100, 'top': 100},
            'computed_style': {'display': 'block', 'visibility': 'visible', 'opacity': 1.0},
            'viewport': {'width': 1920, 'height': 1080}
        }

        visible, issues = VisibilityChecker.check_visibility(element_info)

        assert visible is False
        assert any('no dimensions' in issue.message.lower() for issue in issues)

    def test_check_visibility_display_none(self):
        """Test visibility check fails for display: none"""
        element_info = {
            'rect': {'width': 100, 'height': 50, 'left': 100, 'top': 100},
            'computed_style': {
                'display': 'none',
                'visibility': 'visible',
                'opacity': 1.0
            },
            'viewport': {'width': 1920, 'height': 1080}
        }

        visible, issues = VisibilityChecker.check_visibility(element_info)

        assert visible is False
        assert any('display: none' in issue.message.lower() for issue in issues)

    def test_check_visibility_hidden(self):
        """Test visibility check fails for visibility: hidden"""
        element_info = {
            'rect': {'width': 100, 'height': 50, 'left': 100, 'top': 100},
            'computed_style': {
                'display': 'block',
                'visibility': 'hidden',
                'opacity': 1.0
            },
            'viewport': {'width': 1920, 'height': 1080}
        }

        visible, issues = VisibilityChecker.check_visibility(element_info)

        assert visible is False
        assert any('visibility: hidden' in issue.message.lower() for issue in issues)

    def test_check_visibility_zero_opacity(self):
        """Test visibility check fails for opacity: 0"""
        element_info = {
            'rect': {'width': 100, 'height': 50, 'left': 100, 'top': 100},
            'computed_style': {
                'display': 'block',
                'visibility': 'visible',
                'opacity': 0.0
            },
            'viewport': {'width': 1920, 'height': 1080}
        }

        visible, issues = VisibilityChecker.check_visibility(element_info)

        assert visible is False
        assert any('opacity' in issue.message.lower() for issue in issues)

    def test_check_visibility_low_opacity_warning(self):
        """Test visibility check warns for low opacity"""
        element_info = {
            'rect': {'width': 100, 'height': 50, 'left': 100, 'top': 100},
            'computed_style': {
                'display': 'block',
                'visibility': 'visible',
                'opacity': 0.3
            },
            'viewport': {'width': 1920, 'height': 1080}
        }

        visible, issues = VisibilityChecker.check_visibility(element_info)

        assert visible is True
        assert any(issue.severity == 'warning' and 'opacity' in issue.message.lower() for issue in issues)

    def test_check_visibility_outside_viewport(self):
        """Test visibility check fails for element outside viewport"""
        element_info = {
            'rect': {'width': 100, 'height': 50, 'left': 2000, 'top': 100},
            'computed_style': {'display': 'block', 'visibility': 'visible', 'opacity': 1.0},
            'viewport': {'width': 1920, 'height': 1080}
        }

        visible, issues = VisibilityChecker.check_visibility(element_info)

        assert visible is False
        assert any('outside viewport' in issue.message.lower() for issue in issues)

    def test_check_visibility_partially_visible(self):
        """Test visibility check warns when element is partially visible"""
        element_info = {
            'rect': {'width': 200, 'height': 100, 'left': 1850, 'top': 100},
            'computed_style': {'display': 'block', 'visibility': 'visible', 'opacity': 1.0},
            'viewport': {'width': 1920, 'height': 1080}
        }

        visible, issues = VisibilityChecker.check_visibility(element_info)

        # Should still be visible but with warning
        assert visible is True
        assert any('visible' in issue.message.lower() for issue in issues if issue.severity == 'warning')


class TestInteractabilityChecker:
    """Test InteractabilityChecker class"""

    def test_check_interactability_valid(self):
        """Test interactability check for valid element"""
        element_info = {
            'attributes': {'disabled': False},
            'computed_style': {'pointer_events': 'auto'},
            'tag_name': 'button'
        }

        interactable, issues = InteractabilityChecker.check_interactability(element_info)

        assert interactable is True
        assert all(issue.severity != 'error' for issue in issues)

    def test_check_interactability_disabled(self):
        """Test interactability check fails for disabled element"""
        element_info = {
            'attributes': {'disabled': True},
            'computed_style': {'pointer_events': 'auto'},
            'tag_name': 'button'
        }

        interactable, issues = InteractabilityChecker.check_interactability(element_info)

        assert interactable is False
        assert any('disabled' in issue.message.lower() for issue in issues)

    def test_check_interactability_pointer_events_none(self):
        """Test interactability check fails for pointer-events: none"""
        element_info = {
            'attributes': {},
            'computed_style': {'pointer_events': 'none'},
            'tag_name': 'div'
        }

        interactable, issues = InteractabilityChecker.check_interactability(element_info)

        assert interactable is False
        assert any('pointer-events' in issue.message.lower() for issue in issues)

    def test_check_interactability_aria_disabled(self):
        """Test interactability check warns for aria-disabled"""
        element_info = {
            'attributes': {'aria_disabled': 'true'},
            'computed_style': {'pointer_events': 'auto'},
            'tag_name': 'button'
        }

        interactable, issues = InteractabilityChecker.check_interactability(element_info)

        assert interactable is True
        assert any(issue.severity == 'warning' and 'aria-disabled' in issue.message.lower() for issue in issues)

    def test_check_interactability_readonly_input(self):
        """Test interactability check warns for readonly input"""
        element_info = {
            'attributes': {'readonly': True},
            'computed_style': {'pointer_events': 'auto'},
            'tag_name': 'INPUT'
        }

        interactable, issues = InteractabilityChecker.check_interactability(element_info)

        assert interactable is True
        assert any('readonly' in issue.message.lower() for issue in issues)


class TestStabilityChecker:
    """Test StabilityChecker class"""

    @pytest.mark.asyncio
    async def test_check_stability_stable_element(self):
        """Test stability check for stable element"""
        element_info = {
            'position_history': [
                {'x': 100, 'y': 200},
                {'x': 100, 'y': 200},
                {'x': 100, 'y': 200}
            ]
        }

        stable, issues = await StabilityChecker.check_stability(element_info)

        assert stable is True
        assert all(issue.severity != 'error' for issue in issues)

    @pytest.mark.asyncio
    async def test_check_stability_moving_element(self):
        """Test stability check fails for moving element"""
        element_info = {
            'position_history': [
                {'x': 100, 'y': 200},
                {'x': 105, 'y': 200},
                {'x': 110, 'y': 200}
            ]
        }

        stable, issues = await StabilityChecker.check_stability(element_info, threshold_px=2.0)

        assert stable is False
        assert any('unstable' in issue.message.lower() for issue in issues)

    @pytest.mark.asyncio
    async def test_check_stability_insufficient_data(self):
        """Test stability check assumes stable with insufficient data"""
        element_info = {
            'position_history': [{'x': 100, 'y': 200}]
        }

        stable, issues = await StabilityChecker.check_stability(element_info)

        assert stable is True

    @pytest.mark.asyncio
    async def test_check_stability_with_animations(self):
        """Test stability check warns for CSS animations"""
        element_info = {
            'position_history': [
                {'x': 100, 'y': 200},
                {'x': 100, 'y': 200}
            ],
            'has_animations': True
        }

        stable, issues = await StabilityChecker.check_stability(element_info)

        assert stable is True
        assert any('animation' in issue.message.lower() for issue in issues)


class TestHitTargetChecker:
    """Test HitTargetChecker class"""

    def test_check_hit_target_fully_clickable(self):
        """Test hit target check for fully clickable element"""
        element_info = {
            'hit_test_results': [
                {'is_target': True},
                {'is_target': True},
                {'is_target': True},
                {'is_target': True},
                {'is_target': True}
            ]
        }

        is_target, issues = HitTargetChecker.check_hit_target(element_info)

        assert is_target is True
        assert all(issue.severity != 'error' for issue in issues)

    def test_check_hit_target_completely_obscured(self):
        """Test hit target check fails for completely obscured element"""
        element_info = {
            'hit_test_results': [
                {'is_target': False, 'actual_element': 'div.overlay'},
                {'is_target': False, 'actual_element': 'div.overlay'},
                {'is_target': False, 'actual_element': 'div.overlay'}
            ]
        }

        is_target, issues = HitTargetChecker.check_hit_target(element_info)

        assert is_target is False
        assert any('obscured' in issue.message.lower() for issue in issues)

    def test_check_hit_target_partially_obscured(self):
        """Test hit target check warns for partially obscured element"""
        element_info = {
            'hit_test_results': [
                {'is_target': True},
                {'is_target': True},
                {'is_target': False, 'actual_element': 'div.overlay'},
                {'is_target': False, 'actual_element': 'div.overlay'},
                {'is_target': True}
            ]
        }

        is_target, issues = HitTargetChecker.check_hit_target(element_info)

        assert is_target is True
        assert any('partially obscured' in issue.message.lower() for issue in issues)

    def test_check_hit_target_no_data(self):
        """Test hit target check with no data"""
        element_info = {'hit_test_results': []}

        is_target, issues = HitTargetChecker.check_hit_target(element_info)

        assert is_target is True
        assert any('no hit test data' in issue.message.lower() for issue in issues)

    def test_analyze_z_index_positioned_element(self):
        """Test z-index analysis for positioned element"""
        element_info = {
            'computed_style': {
                'position': 'absolute',
                'z_index': '10'
            }
        }

        analysis = HitTargetChecker.analyze_z_index(element_info)

        assert analysis['is_positioned'] is True
        assert analysis['effective_z_index'] == 10
        assert analysis['creates_stacking_context'] is True

    def test_analyze_z_index_static_element(self):
        """Test z-index analysis for static element"""
        element_info = {
            'computed_style': {
                'position': 'static',
                'z_index': '10'
            }
        }

        analysis = HitTargetChecker.analyze_z_index(element_info)

        assert analysis['is_positioned'] is False
        assert analysis['effective_z_index'] is None


class TestHoverStateChecker:
    """Test HoverStateChecker class"""

    def test_check_hover_state_valid(self):
        """Test hover state check for valid hoverable element"""
        element_info = {
            'computed_style': {'pointer_events': 'auto', 'cursor': 'pointer'},
            'has_hover_styles': True
        }

        hoverable, issues = HoverStateChecker.check_hover_state(element_info)

        assert hoverable is True

    def test_check_hover_state_pointer_events_none(self):
        """Test hover state check fails for pointer-events: none"""
        element_info = {
            'computed_style': {'pointer_events': 'none'},
            'has_hover_styles': False
        }

        hoverable, issues = HoverStateChecker.check_hover_state(element_info)

        assert hoverable is False

    def test_check_hover_state_no_hover_styles(self):
        """Test hover state check warns for no hover styles"""
        element_info = {
            'computed_style': {'pointer_events': 'auto', 'cursor': 'default'},
            'has_hover_styles': False
        }

        hoverable, issues = HoverStateChecker.check_hover_state(element_info)

        assert hoverable is True
        assert any('no :hover styles' in issue.message.lower() for issue in issues)


class TestPreClickValidator:
    """Test PreClickValidator orchestrator"""

    @pytest.mark.asyncio
    async def test_validate_full_checks_passing(self):
        """Test full validation with all checks passing"""
        element_info = {
            'rect': {'width': 100, 'height': 50, 'left': 100, 'top': 100},
            'computed_style': {
                'display': 'block',
                'visibility': 'visible',
                'opacity': 1.0,
                'pointer_events': 'auto',
                'cursor': 'pointer'
            },
            'viewport': {'width': 1920, 'height': 1080},
            'check_visibility': True,
            'attributes': {},
            'tag_name': 'button',
            'position_history': [{'x': 100, 'y': 200}],
            'hit_test_results': [{'is_target': True}],
            'has_hover_styles': True
        }

        validator = PreClickValidator()
        result = await validator.validate(element_info)

        assert result.status == ValidationStatus.PASSED
        assert result.can_proceed is True
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_validate_visibility_failure(self):
        """Test validation fails on visibility check"""
        element_info = {
            'rect': {'width': 0, 'height': 0, 'left': 100, 'top': 100},
            'computed_style': {'display': 'none', 'pointer_events': 'auto'},
            'viewport': {'width': 1920, 'height': 1080},
            'attributes': {},
            'tag_name': 'button'
        }

        validator = PreClickValidator()
        result = await validator.validate(element_info)

        assert result.status == ValidationStatus.FAILED
        assert result.can_proceed is False

    @pytest.mark.asyncio
    async def test_validate_specific_checks_only(self):
        """Test validation with specific checks only"""
        element_info = {
            'rect': {'width': 100, 'height': 50, 'left': 100, 'top': 100},
            'computed_style': {'display': 'block', 'visibility': 'visible', 'opacity': 1.0},
            'viewport': {'width': 1920, 'height': 1080},
            'check_visibility': True
        }

        validator = PreClickValidator()
        result = await validator.validate(element_info, checks=['visibility'])

        assert 'visibility' in result.details['check_results']
        assert 'interactability' not in result.details['check_results']

    @pytest.mark.asyncio
    async def test_quick_validate(self):
        """Test quick validation method"""
        element_info = {
            'rect': {'width': 100, 'height': 50, 'left': 100, 'top': 100},
            'computed_style': {'display': 'block', 'visibility': 'visible', 'opacity': 1.0, 'pointer_events': 'auto'},
            'viewport': {'width': 1920, 'height': 1080},
            'check_visibility': True,
            'attributes': {},
            'tag_name': 'button',
            'hit_test_results': [{'is_target': True}]
        }

        validator = PreClickValidator()
        can_proceed = await validator.quick_validate(element_info)

        assert can_proceed is True


# ============================================================================
# Test Post-Click Validation Module
# ============================================================================

class TestDOMChangeDetector:
    """Test DOMChangeDetector class"""

    @pytest.mark.asyncio
    async def test_detect_attribute_changes_aria(self):
        """Test detecting ARIA attribute changes"""
        element_info = {
            'attributes': {'aria_expanded': 'true', 'class': 'btn active'}
        }
        previous_state = {
            'attributes': {'aria_expanded': 'false', 'class': 'btn'}
        }

        detector = DOMChangeDetector()
        changes = await detector.detect_attribute_changes(element_info, previous_state, timeout_ms=10)

        assert len(changes) > 0
        assert any(c.change_type == ChangeType.ARIA_CHANGED for c in changes)
        assert any(c.change_type == ChangeType.CLASS_CHANGED for c in changes)

    @pytest.mark.asyncio
    async def test_detect_attribute_changes_class(self):
        """Test detecting class changes"""
        element_info = {
            'attributes': {'class': 'btn btn-primary active'}
        }
        previous_state = {
            'attributes': {'class': 'btn btn-primary'}
        }

        detector = DOMChangeDetector()
        changes = await detector.detect_attribute_changes(element_info, previous_state, timeout_ms=10)

        class_changes = [c for c in changes if c.change_type == ChangeType.CLASS_CHANGED]
        assert len(class_changes) > 0
        assert 'active' in class_changes[0].details['added']

    @pytest.mark.asyncio
    async def test_detect_style_changes(self):
        """Test detecting CSS style changes"""
        element_info = {
            'computed_style': {'display': 'block', 'opacity': '1', 'color': 'red'}
        }
        previous_state = {
            'computed_style': {'display': 'block', 'opacity': '0.5', 'color': 'blue'}
        }

        detector = DOMChangeDetector()
        changes = await detector.detect_style_changes(element_info, previous_state)

        assert len(changes) > 0
        style_change = changes[0]
        assert style_change.change_type == ChangeType.STYLE_CHANGED
        assert 'opacity' in style_change.details['style_changes']

    @pytest.mark.asyncio
    async def test_detect_text_changes(self):
        """Test detecting text content changes"""
        element_info = {'text_content': 'Clicked!'}
        previous_state = {'text_content': 'Click Me'}

        detector = DOMChangeDetector()
        changes = await detector.detect_text_changes(element_info, previous_state)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.TEXT_CHANGED
        assert changes[0].details['current_text'] == 'Clicked!'


class TestPageStateDetector:
    """Test PageStateDetector class"""

    @pytest.mark.asyncio
    async def test_detect_url_change(self):
        """Test detecting URL changes"""
        detector = PageStateDetector()
        change = await detector.detect_url_change(
            'http://example.com/page1',
            'http://example.com/page2'
        )

        assert change is not None
        assert change.change_type == ChangeType.URL_CHANGED
        assert change.details['current_url'] == 'http://example.com/page2'

    @pytest.mark.asyncio
    async def test_detect_no_url_change(self):
        """Test no URL change detection"""
        detector = PageStateDetector()
        change = await detector.detect_url_change(
            'http://example.com/page1',
            'http://example.com/page1'
        )

        assert change is None

    @pytest.mark.asyncio
    async def test_detect_focus_change(self):
        """Test detecting focus changes"""
        detector = PageStateDetector()
        change = await detector.detect_focus_change('#input1', '#input2')

        assert change is not None
        assert change.change_type == ChangeType.FOCUS_CHANGED

    @pytest.mark.asyncio
    async def test_detect_new_elements(self):
        """Test detecting new elements"""
        page_context = {
            'new_elements': [
                {'selector': '#modal', 'tag_name': 'div', 'role': 'dialog', 'type': 'modal'}
            ]
        }

        detector = PageStateDetector()
        changes = await detector.detect_new_elements(page_context)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.ELEMENT_APPEARED

    @pytest.mark.asyncio
    async def test_detect_removed_elements(self):
        """Test detecting removed elements"""
        page_context = {
            'removed_elements': [
                {'selector': '#tooltip', 'tag_name': 'div'}
            ]
        }

        detector = PageStateDetector()
        changes = await detector.detect_removed_elements(page_context)

        assert len(changes) == 1
        assert changes[0].change_type == ChangeType.ELEMENT_DISAPPEARED


class TestNetworkActivityDetector:
    """Test NetworkActivityDetector class"""

    @pytest.mark.asyncio
    async def test_detect_network_requests(self):
        """Test detecting network requests"""
        network_log = [
            {'url': '/api/submit', 'method': 'POST', 'status': 200, 'timestamp': 123.45},
            {'url': '/api/data', 'method': 'GET', 'status': 200, 'timestamp': 123.46}
        ]

        detector = NetworkActivityDetector()
        changes = await detector.detect_network_requests(network_log)

        assert len(changes) == 2
        assert all(c.change_type == ChangeType.NETWORK_REQUEST for c in changes)


class TestEventValidation:
    """Test EventValidation class"""

    @pytest.mark.asyncio
    async def test_validate_click_event_fired(self):
        """Test validating click event was fired"""
        event_log = [
            {'type': 'mousedown', 'timestamp': 123.45},
            {'type': 'click', 'timestamp': 123.46},
            {'type': 'mouseup', 'timestamp': 123.47}
        ]

        validator = EventValidation()
        fired = await validator.validate_click_event_fired(event_log)

        assert fired is True

    @pytest.mark.asyncio
    async def test_validate_no_click_event(self):
        """Test detecting no click event"""
        event_log = []

        validator = EventValidation()
        fired = await validator.validate_click_event_fired(event_log)

        assert fired is False

    def test_analyze_event_propagation(self):
        """Test analyzing event propagation"""
        event_log = [
            {
                'type': 'click',
                'stopped_propagation': False,
                'default_prevented': True,
                'bubbles': True,
                'target': '#button',
                'current_target': '#button'
            }
        ]

        validator = EventValidation()
        analysis = validator.analyze_event_propagation(event_log)

        assert analysis['event_fired'] is True
        assert analysis['propagated'] is True
        assert analysis['prevented'] is True


class TestPostClickValidator:
    """Test PostClickValidator orchestrator"""

    @pytest.mark.asyncio
    async def test_validate_comprehensive(self):
        """Test comprehensive post-click validation"""
        element_info = {
            'attributes': {'aria_expanded': 'true'},
            'computed_style': {'opacity': '1'},
            'text_content': 'Clicked'
        }
        previous_state = {
            'attributes': {'aria_expanded': 'false'},
            'computed_style': {'opacity': '1'},
            'text_content': 'Click',
            'url': 'http://example.com',
            'focused_element': None
        }
        page_context = {
            'url': 'http://example.com',
            'focused_element': '#button',
            'new_elements': [],
            'removed_elements': [],
            'network_log': [],
            'event_log': [{'type': 'click'}]
        }

        validator = PostClickValidator()
        result = await validator.validate(
            element_info,
            previous_state,
            page_context,
            timeout_ms=10
        )

        assert result.success is True
        assert len(result.changes_detected) > 0

    @pytest.mark.asyncio
    async def test_validate_expected_changes(self):
        """Test validation with expected changes"""
        element_info = {'attributes': {}, 'computed_style': {}, 'text_content': ''}
        previous_state = {'attributes': {}, 'computed_style': {}, 'text_content': '', 'url': 'http://example.com'}
        page_context = {
            'url': 'http://example.com/new',
            'new_elements': [],
            'removed_elements': [],
            'network_log': [],
            'event_log': [{'type': 'click'}]
        }

        validator = PostClickValidator()
        result = await validator.validate(
            element_info,
            previous_state,
            page_context,
            expected_changes=[ChangeType.URL_CHANGED],
            timeout_ms=10
        )

        assert result.expected_changes_met is True

    @pytest.mark.asyncio
    async def test_quick_validate(self):
        """Test quick validation method"""
        page_context = {
            'event_log': [{'type': 'click'}],
            'url_changed': False,
            'new_elements': [],
            'network_log': []
        }

        validator = PostClickValidator()
        has_change = await validator.quick_validate(page_context)

        assert has_change is True


class TestClickResultMonitor:
    """Test ClickResultMonitor class"""

    def test_log_result(self):
        """Test logging click result"""
        monitor = ClickResultMonitor()

        from mcp_server.validation.post_click import PostClickValidationResult

        result = PostClickValidationResult(
            success=True,
            changes_detected=[],
            expected_changes_met=True,
            verification_time_ms=50.0,
            details={}
        )

        monitor.log_result('#button', result, 'navigation')

        assert len(monitor.click_results) == 1
        assert monitor.click_results[0]['selector'] == '#button'

    def test_get_statistics(self):
        """Test getting statistics from monitor"""
        monitor = ClickResultMonitor()

        from mcp_server.validation.post_click import PostClickValidationResult, StateChange

        # Log some results
        for i in range(10):
            result = PostClickValidationResult(
                success=i % 2 == 0,
                changes_detected=[
                    StateChange(ChangeType.URL_CHANGED, 123.45, {})
                ],
                expected_changes_met=True,
                verification_time_ms=50.0,
                details={}
            )
            monitor.log_result(f'#button{i}', result)

        stats = monitor.get_statistics()

        assert stats['total_clicks'] == 10
        assert stats['successful'] == 5
        assert stats['success_rate'] == 0.5


# ============================================================================
# Test Confidence Scoring Module
# ============================================================================

class TestClickConfidenceCalculator:
    """Test ClickConfidenceCalculator class"""

    @pytest.mark.asyncio
    async def test_calculate_confidence_high(self):
        """Test calculating high confidence score"""
        element_info = {
            'rect': {'width': 100, 'height': 50, 'left': 100, 'top': 100},
            'computed_style': {
                'display': 'block',
                'visibility': 'visible',
                'opacity': 1.0,
                'pointer_events': 'auto'
            },
            'viewport': {'width': 1920, 'height': 1080},
            'attributes': {},
            'tag_name': 'button',
            'position_history': [{'x': 100, 'y': 200, 'width': 100, 'height': 50}],
            'hit_test_results': [{'is_target': True}]
        }
        page_context = {
            'ready_state': 'complete',
            'active_animations': 0,
            'pending_requests': 0
        }

        calculator = ClickConfidenceCalculator()
        result = await calculator.calculate_confidence(element_info, page_context)

        assert result.confidence >= 80
        assert result.recommendation in [Recommendation.SAFE_TO_CLICK, Recommendation.PROBABLY_SAFE]
        assert result.safe is True

    def test_calculate_visibility_score_perfect(self):
        """Test calculating perfect visibility score"""
        element_info = {
            'rect': {'width': 100, 'height': 50, 'left': 100, 'top': 100},
            'computed_style': {
                'display': 'block',
                'visibility': 'visible',
                'opacity': 1.0
            },
            'viewport': {'width': 1920, 'height': 1080}
        }

        calculator = ClickConfidenceCalculator()
        score = calculator.calculate_visibility_score(element_info)

        assert score == 1.0

    def test_calculate_visibility_score_low_opacity(self):
        """Test visibility score with low opacity"""
        element_info = {
            'rect': {'width': 100, 'height': 50, 'left': 100, 'top': 100},
            'computed_style': {
                'display': 'block',
                'visibility': 'visible',
                'opacity': 0.5
            },
            'viewport': {'width': 1920, 'height': 1080}
        }

        calculator = ClickConfidenceCalculator()
        score = calculator.calculate_visibility_score(element_info)

        assert score == 0.5

    def test_calculate_interactability_score_perfect(self):
        """Test calculating perfect interactability score"""
        element_info = {
            'attributes': {},
            'computed_style': {'pointer_events': 'auto'},
            'tag_name': 'button'
        }

        calculator = ClickConfidenceCalculator()
        score = calculator.calculate_interactability_score(element_info)

        assert score == 1.0

    def test_calculate_interactability_score_disabled(self):
        """Test interactability score for disabled element"""
        element_info = {
            'attributes': {'disabled': True},
            'computed_style': {'pointer_events': 'auto'},
            'tag_name': 'button'
        }

        calculator = ClickConfidenceCalculator()
        score = calculator.calculate_interactability_score(element_info)

        assert score == 0.0

    @pytest.mark.asyncio
    async def test_calculate_stability_score_stable(self):
        """Test calculating stability score for stable element"""
        element_info = {
            'position_history': [
                {'x': 100, 'y': 200, 'width': 100, 'height': 50},
                {'x': 100, 'y': 200, 'width': 100, 'height': 50}
            ]
        }

        calculator = ClickConfidenceCalculator()
        score = await calculator.calculate_stability_score(element_info)

        assert score == 1.0

    @pytest.mark.asyncio
    async def test_calculate_stability_score_moving(self):
        """Test calculating stability score for moving element"""
        element_info = {
            'position_history': [
                {'x': 100, 'y': 200, 'width': 100, 'height': 50},
                {'x': 110, 'y': 210, 'width': 100, 'height': 50}
            ]
        }

        calculator = ClickConfidenceCalculator()
        score = await calculator.calculate_stability_score(element_info)

        assert score < 1.0

    def test_calculate_hit_target_score_perfect(self):
        """Test calculating perfect hit target score"""
        element_info = {
            'hit_test_results': [
                {'is_target': True},
                {'is_target': True},
                {'is_target': True}
            ]
        }

        calculator = ClickConfidenceCalculator()
        score = calculator.calculate_hit_target_score(element_info)

        assert score == 1.0

    def test_calculate_hit_target_score_partial(self):
        """Test calculating partial hit target score"""
        element_info = {
            'hit_test_results': [
                {'is_target': True},
                {'is_target': False},
                {'is_target': True}
            ]
        }

        calculator = ClickConfidenceCalculator()
        score = calculator.calculate_hit_target_score(element_info)

        assert score == pytest.approx(2/3, rel=0.01)

    def test_calculate_timing_score_perfect(self):
        """Test calculating perfect timing score"""
        page_context = {
            'ready_state': 'complete',
            'active_animations': 0,
            'pending_requests': 0
        }

        calculator = ClickConfidenceCalculator()
        score = calculator.calculate_timing_score(page_context)

        assert score == 1.0

    def test_calculate_timing_score_loading(self):
        """Test timing score during page loading"""
        page_context = {
            'ready_state': 'loading',
            'active_animations': 2,
            'pending_requests': 3
        }

        calculator = ClickConfidenceCalculator()
        score = calculator.calculate_timing_score(page_context)

        assert score < 1.0


class TestClickStrategy:
    """Test click strategy selection"""

    def test_select_direct_click_strategy(self):
        """Test selecting direct click strategy for high confidence"""
        strategy = select_click_strategy(95, ActionType.STANDARD_CLICK)

        assert strategy == ClickStrategy.DIRECT_CLICK

    def test_select_retry_strategy(self):
        """Test selecting retry strategy for medium confidence"""
        strategy = select_click_strategy(60, ActionType.STANDARD_CLICK)

        assert strategy == ClickStrategy.RETRY_WITH_IMPROVEMENTS

    def test_select_javascript_strategy(self):
        """Test selecting JavaScript click strategy for low confidence"""
        strategy = select_click_strategy(40, ActionType.STANDARD_CLICK)

        assert strategy == ClickStrategy.JAVASCRIPT_CLICK

    def test_select_manual_intervention(self):
        """Test selecting manual intervention for very low confidence"""
        strategy = select_click_strategy(20, ActionType.STANDARD_CLICK)

        assert strategy == ClickStrategy.MANUAL_INTERVENTION_REQUIRED


class TestClickConfidenceMonitor:
    """Test ClickConfidenceMonitor class"""

    def test_log_click_attempt(self):
        """Test logging click attempt"""
        monitor = ClickConfidenceMonitor()

        from mcp_server.validation.confidence import ConfidenceResult, ConfidenceScores

        result = ConfidenceResult(
            confidence=85,
            scores=ConfidenceScores(1.0, 1.0, 1.0, 1.0, 1.0),
            recommendation=Recommendation.SAFE_TO_CLICK,
            issues=[],
            safe=True,
            details={}
        )

        monitor.log_click_attempt('#button', result, True)

        assert len(monitor.click_history) == 1

    def test_get_statistics(self):
        """Test getting statistics from monitor"""
        monitor = ClickConfidenceMonitor()

        from mcp_server.validation.confidence import ConfidenceResult, ConfidenceScores

        # Log multiple attempts
        for i in range(10):
            result = ConfidenceResult(
                confidence=80 + i,
                scores=ConfidenceScores(1.0, 1.0, 1.0, 1.0, 1.0),
                recommendation=Recommendation.SAFE_TO_CLICK,
                issues=[],
                safe=True,
                details={}
            )
            monitor.log_click_attempt(f'#button{i}', result, True)

        stats = monitor.get_statistics()

        assert stats['total_attempts'] == 10
        assert stats['successful'] == 10
        assert stats['avg_confidence'] == 84.5


# ============================================================================
# Test Retry Module
# ============================================================================

class TestDelayCalculator:
    """Test DelayCalculator class"""

    def test_calculate_exponential_backoff(self):
        """Test exponential backoff calculation"""
        delay = DelayCalculator.calculate_exponential_backoff(
            attempt=2,
            base_delay_ms=1000,
            backoff_multiplier=2.0
        )

        assert delay == 4000  # 1000 * 2^2

    def test_calculate_exponential_backoff_with_max(self):
        """Test exponential backoff respects max delay"""
        delay = DelayCalculator.calculate_exponential_backoff(
            attempt=10,
            base_delay_ms=1000,
            backoff_multiplier=2.0,
            max_delay_ms=5000
        )

        assert delay == 5000

    def test_add_jitter(self):
        """Test adding jitter to delay"""
        base_delay = 1000
        jittered = DelayCalculator.add_jitter(base_delay, jitter_factor=0.5)

        # Jittered delay should be within range
        assert base_delay <= jittered <= base_delay * 1.5

    def test_calculate_linear_backoff(self):
        """Test linear backoff calculation"""
        delay = DelayCalculator.calculate_linear_backoff(
            attempt=3,
            base_delay_ms=1000,
            increment_ms=500
        )

        assert delay == 2500  # 1000 + (500 * 3)

    def test_calculate_delay_exponential_strategy(self):
        """Test delay calculation with exponential strategy"""
        config = RetryConfig(
            base_delay_ms=1000,
            strategy=RetryStrategy.EXPONENTIAL,
            backoff_multiplier=2.0
        )

        delay = DelayCalculator.calculate_delay(2, config)

        assert delay == 4000

    def test_calculate_delay_fixed_strategy(self):
        """Test delay calculation with fixed strategy"""
        config = RetryConfig(
            base_delay_ms=1000,
            strategy=RetryStrategy.FIXED
        )

        delay = DelayCalculator.calculate_delay(5, config)

        assert delay == 1000


class TestErrorClassifier:
    """Test ErrorClassifier class"""

    def test_classify_click_intercepted_error(self):
        """Test classifying click intercepted error"""
        error = ElementClickInterceptedError()

        category = ErrorClassifier.classify_error(error)

        assert category == ErrorCategory.ELEMENT_CLICK_INTERCEPTED

    def test_classify_not_interactable_error(self):
        """Test classifying not interactable error"""
        error = ElementNotInteractableError()

        category = ErrorClassifier.classify_error(error)

        assert category == ErrorCategory.ELEMENT_NOT_INTERACTABLE

    def test_classify_stale_element_error(self):
        """Test classifying stale element error"""
        error = StaleElementError()

        category = ErrorClassifier.classify_error(error)

        assert category == ErrorCategory.STALE_ELEMENT_REFERENCE

    def test_classify_generic_error_by_message(self):
        """Test classifying generic error by message"""
        error = Exception("Element click intercepted by overlay")

        category = ErrorClassifier.classify_error(error)

        assert category == ErrorCategory.ELEMENT_CLICK_INTERCEPTED

    def test_is_retryable_default(self):
        """Test default retryable errors"""
        error = ElementClickInterceptedError()

        is_retryable = ErrorClassifier.is_retryable(error)

        assert is_retryable is True

    def test_is_not_retryable(self):
        """Test non-retryable error"""
        error = Exception("Unknown error")

        is_retryable = ErrorClassifier.is_retryable(error)

        assert is_retryable is False


class TestRetryExecutor:
    """Test RetryExecutor class"""

    @pytest.mark.asyncio
    async def test_execute_success_first_attempt(self):
        """Test successful execution on first attempt"""
        async def operation():
            return "success"

        executor = RetryExecutor()
        result = await executor.execute(operation)

        assert result.success is True
        assert result.attempts == 1
        assert result.result == "success"

    @pytest.mark.asyncio
    async def test_execute_success_after_retries(self):
        """Test successful execution after retries"""
        attempt_count = 0

        async def operation():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ElementClickInterceptedError()
            return "success"

        config = RetryConfig(max_retries=5, base_delay_ms=10)
        executor = RetryExecutor(config)
        result = await executor.execute(operation)

        assert result.success is True
        assert result.attempts == 3

    @pytest.mark.asyncio
    async def test_execute_failure_max_retries(self):
        """Test failure after max retries"""
        async def operation():
            raise ElementClickInterceptedError()

        config = RetryConfig(max_retries=3, base_delay_ms=10)
        executor = RetryExecutor(config)
        result = await executor.execute(operation)

        assert result.success is False
        assert result.attempts == 3

    @pytest.mark.asyncio
    async def test_execute_non_retryable_error(self):
        """Test non-retryable error stops immediately"""
        async def operation():
            raise ValueError("Non-retryable error")

        config = RetryConfig(max_retries=5, base_delay_ms=10)
        executor = RetryExecutor(config)
        result = await executor.execute(operation)

        assert result.success is False
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_execute_with_condition(self):
        """Test execute with success condition"""
        attempt_count = 0

        async def operation():
            nonlocal attempt_count
            attempt_count += 1
            return attempt_count

        def success_condition(result):
            return result >= 3

        config = RetryConfig(
            max_retries=5,
            base_delay_ms=10,
            retryable_errors=[
                ErrorCategory.ELEMENT_CLICK_INTERCEPTED,
                ErrorCategory.ELEMENT_NOT_INTERACTABLE,
                ErrorCategory.STALE_ELEMENT_REFERENCE,
                ErrorCategory.TIMEOUT,
                ErrorCategory.UNKNOWN  # Add UNKNOWN to retryable errors
            ]
        )
        executor = RetryExecutor(config)
        result = await executor.execute_with_condition(operation, success_condition, config)

        assert result.success is True
        assert result.result == 3


class TestCircuitBreaker:
    """Test CircuitBreaker class"""

    @pytest.mark.asyncio
    async def test_circuit_closed_normal_operation(self):
        """Test circuit breaker in closed state"""
        async def operation():
            return "success"

        breaker = CircuitBreaker(failure_threshold=3)
        result = await breaker.execute(operation)

        assert result == "success"
        assert breaker.state == "CLOSED"

    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures"""
        async def operation():
            raise Exception("Failure")

        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout_ms=1000)

        # Trigger failures
        for _ in range(3):
            with pytest.raises(Exception):
                await breaker.execute(operation)

        assert breaker.state == "OPEN"

    @pytest.mark.asyncio
    async def test_circuit_half_open_after_timeout(self):
        """Test circuit breaker transitions to half-open after timeout"""
        async def operation():
            raise Exception("Failure")

        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_ms=50)

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.execute(operation)

        assert breaker.state == "OPEN"

        # Wait for recovery timeout
        await asyncio.sleep(0.1)

        # Next call should transition to HALF_OPEN
        with pytest.raises(Exception):
            await breaker.execute(operation)

        # Should be back to OPEN after failure in HALF_OPEN
        assert breaker.state == "OPEN"

    def test_circuit_reset(self):
        """Test resetting circuit breaker"""
        breaker = CircuitBreaker()
        breaker.state = "OPEN"
        breaker.failure_count = 10

        breaker.reset()

        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0


class TestAdaptiveRetryExecutor:
    """Test AdaptiveRetryExecutor class"""

    @pytest.mark.asyncio
    async def test_adaptive_executor_learns(self):
        """Test adaptive executor adapts configuration"""
        executor = AdaptiveRetryExecutor()

        # Simulate multiple failures to trigger adaptation
        async def failing_operation():
            raise ElementClickInterceptedError()

        config = RetryConfig(max_retries=2, base_delay_ms=100)

        for _ in range(10):
            await executor.execute(failing_operation, config)

        # After failures, should have adapted
        assert len(executor.history) == 10

    def test_get_statistics(self):
        """Test getting statistics from adaptive executor"""
        executor = AdaptiveRetryExecutor()

        from mcp_server.validation.retry import RetryResult, RetryAttempt

        # Add some mock history
        for i in range(5):
            result = RetryResult(
                success=i % 2 == 0,
                attempts=2,
                total_time_ms=100.0,
                result=None,
                error=None,
                attempt_history=[
                    RetryAttempt(0, datetime.now(), None, ErrorCategory.UNKNOWN, 0, False),
                    RetryAttempt(1, datetime.now(), None, ErrorCategory.UNKNOWN, 0, True)
                ]
            )
            executor.history.append(result)

        stats = executor.get_statistics()

        assert stats['total_operations'] == 5
        assert stats['avg_attempts'] == 2.0


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
