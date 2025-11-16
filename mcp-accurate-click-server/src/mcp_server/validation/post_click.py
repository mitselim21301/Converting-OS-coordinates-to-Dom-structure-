"""
Post-Click Verification Module

Validates that click operations produced expected results:
- State change detection (DOM mutations, attribute changes)
- Event listener validation
- Visual state changes (CSS, new elements)
- Application state changes (URL, storage, network)
- Focus state verification

Reference: CLICK_VALIDATION_RESEARCH.md Section 2
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class ChangeType(Enum):
    """Types of changes that can be detected after a click"""
    URL_CHANGED = "URL_CHANGED"
    FOCUS_CHANGED = "FOCUS_CHANGED"
    ATTRIBUTE_CHANGED = "ATTRIBUTE_CHANGED"
    ELEMENT_APPEARED = "ELEMENT_APPEARED"
    ELEMENT_DISAPPEARED = "ELEMENT_DISAPPEARED"
    NETWORK_REQUEST = "NETWORK_REQUEST"
    CLASS_CHANGED = "CLASS_CHANGED"
    STYLE_CHANGED = "STYLE_CHANGED"
    TEXT_CHANGED = "TEXT_CHANGED"
    ARIA_CHANGED = "ARIA_CHANGED"


@dataclass
class StateChange:
    """Represents a detected state change"""
    change_type: ChangeType
    timestamp: float
    details: Dict[str, Any]
    element_selector: Optional[str] = None


@dataclass
class PostClickValidationResult:
    """Result of post-click validation"""
    success: bool
    changes_detected: List[StateChange]
    expected_changes_met: bool
    verification_time_ms: float
    details: Dict[str, Any]


class DOMChangeDetector:
    """Detects DOM mutations and changes"""

    @staticmethod
    async def detect_attribute_changes(
        element_info: Dict[str, Any],
        previous_state: Dict[str, Any],
        timeout_ms: int = 1000
    ) -> List[StateChange]:
        """
        Detect attribute changes on the element.

        Monitors:
        - aria-expanded, aria-selected, aria-checked
        - class changes
        - disabled, readonly, hidden
        - data-* attributes

        Returns:
            List of detected StateChange objects
        """
        changes = []
        start_time = asyncio.get_event_loop().time()

        # Wait briefly for changes to occur
        await asyncio.sleep(timeout_ms / 1000.0)

        current_attrs = element_info.get('attributes', {})
        previous_attrs = previous_state.get('attributes', {})

        # Check ARIA attributes
        aria_attrs = [
            'aria_expanded', 'aria_selected', 'aria_checked',
            'aria_pressed', 'aria_hidden', 'aria_disabled'
        ]

        for attr in aria_attrs:
            prev_value = previous_attrs.get(attr)
            curr_value = current_attrs.get(attr)

            if prev_value != curr_value:
                changes.append(StateChange(
                    change_type=ChangeType.ARIA_CHANGED,
                    timestamp=asyncio.get_event_loop().time(),
                    details={
                        'attribute': attr,
                        'previous_value': prev_value,
                        'current_value': curr_value
                    }
                ))

        # Check class changes
        prev_classes = set(previous_attrs.get('class', '').split())
        curr_classes = set(current_attrs.get('class', '').split())

        if prev_classes != curr_classes:
            added_classes = curr_classes - prev_classes
            removed_classes = prev_classes - curr_classes

            changes.append(StateChange(
                change_type=ChangeType.CLASS_CHANGED,
                timestamp=asyncio.get_event_loop().time(),
                details={
                    'added': list(added_classes),
                    'removed': list(removed_classes),
                    'previous': list(prev_classes),
                    'current': list(curr_classes)
                }
            ))

        # Check state attributes
        state_attrs = ['disabled', 'readonly', 'hidden', 'checked', 'selected']

        for attr in state_attrs:
            prev_value = previous_attrs.get(attr)
            curr_value = current_attrs.get(attr)

            if prev_value != curr_value:
                changes.append(StateChange(
                    change_type=ChangeType.ATTRIBUTE_CHANGED,
                    timestamp=asyncio.get_event_loop().time(),
                    details={
                        'attribute': attr,
                        'previous_value': prev_value,
                        'current_value': curr_value
                    }
                ))

        return changes

    @staticmethod
    async def detect_style_changes(
        element_info: Dict[str, Any],
        previous_state: Dict[str, Any]
    ) -> List[StateChange]:
        """
        Detect CSS computed style changes.

        Returns:
            List of detected StateChange objects
        """
        changes = []

        current_style = element_info.get('computed_style', {})
        previous_style = previous_state.get('computed_style', {})

        # Important style properties to monitor
        monitored_props = [
            'display', 'visibility', 'opacity', 'background_color',
            'color', 'border', 'transform', 'position'
        ]

        style_changes = {}

        for prop in monitored_props:
            prev_value = previous_style.get(prop)
            curr_value = current_style.get(prop)

            if prev_value != curr_value:
                style_changes[prop] = {
                    'previous': prev_value,
                    'current': curr_value
                }

        if style_changes:
            changes.append(StateChange(
                change_type=ChangeType.STYLE_CHANGED,
                timestamp=asyncio.get_event_loop().time(),
                details={'style_changes': style_changes}
            ))

        return changes

    @staticmethod
    async def detect_text_changes(
        element_info: Dict[str, Any],
        previous_state: Dict[str, Any]
    ) -> List[StateChange]:
        """
        Detect text content changes.

        Returns:
            List of detected StateChange objects
        """
        changes = []

        current_text = element_info.get('text_content', '')
        previous_text = previous_state.get('text_content', '')

        if current_text != previous_text:
            changes.append(StateChange(
                change_type=ChangeType.TEXT_CHANGED,
                timestamp=asyncio.get_event_loop().time(),
                details={
                    'previous_text': previous_text,
                    'current_text': current_text,
                    'length_change': len(current_text) - len(previous_text)
                }
            ))

        return changes


class PageStateDetector:
    """Detects page-level state changes"""

    @staticmethod
    async def detect_url_change(
        previous_url: str,
        current_url: str
    ) -> Optional[StateChange]:
        """
        Detect URL changes (navigation).

        Returns:
            StateChange if URL changed, None otherwise
        """
        if previous_url != current_url:
            return StateChange(
                change_type=ChangeType.URL_CHANGED,
                timestamp=asyncio.get_event_loop().time(),
                details={
                    'previous_url': previous_url,
                    'current_url': current_url,
                    'url_changed': True
                }
            )

        return None

    @staticmethod
    async def detect_focus_change(
        previous_focus: Optional[str],
        current_focus: Optional[str]
    ) -> Optional[StateChange]:
        """
        Detect focus changes.

        Args:
            previous_focus: Selector of previously focused element
            current_focus: Selector of currently focused element

        Returns:
            StateChange if focus changed, None otherwise
        """
        if previous_focus != current_focus:
            return StateChange(
                change_type=ChangeType.FOCUS_CHANGED,
                timestamp=asyncio.get_event_loop().time(),
                details={
                    'previous_focus': previous_focus,
                    'current_focus': current_focus
                }
            )

        return None

    @staticmethod
    async def detect_new_elements(
        page_context: Dict[str, Any]
    ) -> List[StateChange]:
        """
        Detect newly appeared elements (modals, dropdowns, tooltips).

        Returns:
            List of detected StateChange objects
        """
        changes = []
        new_elements = page_context.get('new_elements', [])

        for element in new_elements:
            changes.append(StateChange(
                change_type=ChangeType.ELEMENT_APPEARED,
                timestamp=asyncio.get_event_loop().time(),
                details={
                    'selector': element.get('selector'),
                    'tag_name': element.get('tag_name'),
                    'role': element.get('role'),
                    'type': element.get('type', 'unknown')
                },
                element_selector=element.get('selector')
            ))

        return changes

    @staticmethod
    async def detect_removed_elements(
        page_context: Dict[str, Any]
    ) -> List[StateChange]:
        """
        Detect elements that disappeared after click.

        Returns:
            List of detected StateChange objects
        """
        changes = []
        removed_elements = page_context.get('removed_elements', [])

        for element in removed_elements:
            changes.append(StateChange(
                change_type=ChangeType.ELEMENT_DISAPPEARED,
                timestamp=asyncio.get_event_loop().time(),
                details={
                    'selector': element.get('selector'),
                    'tag_name': element.get('tag_name')
                },
                element_selector=element.get('selector')
            ))

        return changes


class NetworkActivityDetector:
    """Detects network activity triggered by clicks"""

    @staticmethod
    async def detect_network_requests(
        network_log: List[Dict[str, Any]]
    ) -> List[StateChange]:
        """
        Detect network requests triggered by the click.

        Returns:
            List of detected StateChange objects
        """
        changes = []

        for request in network_log:
            changes.append(StateChange(
                change_type=ChangeType.NETWORK_REQUEST,
                timestamp=request.get('timestamp', 0),
                details={
                    'url': request.get('url'),
                    'method': request.get('method'),
                    'status': request.get('status'),
                    'type': request.get('type', 'xhr')
                }
            ))

        return changes


class EventValidation:
    """Validates that click event was properly dispatched and handled"""

    @staticmethod
    async def validate_click_event_fired(
        event_log: List[Dict[str, Any]]
    ) -> bool:
        """
        Verify that click event was actually fired.

        Args:
            event_log: Log of events captured

        Returns:
            True if click event was detected
        """
        click_events = [
            e for e in event_log
            if e.get('type') in ['click', 'mousedown', 'mouseup']
        ]

        return len(click_events) > 0

    @staticmethod
    def analyze_event_propagation(
        event_log: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze event propagation and handling.

        Returns:
            Dictionary with propagation analysis
        """
        click_events = [
            e for e in event_log
            if e.get('type') == 'click'
        ]

        if not click_events:
            return {
                'event_fired': False,
                'propagated': False,
                'prevented': False
            }

        # Analyze first click event
        event = click_events[0]

        return {
            'event_fired': True,
            'propagated': not event.get('stopped_propagation', False),
            'prevented': event.get('default_prevented', False),
            'bubbles': event.get('bubbles', True),
            'target': event.get('target'),
            'current_target': event.get('current_target')
        }


class PostClickValidator:
    """
    Main post-click validation orchestrator.

    Validates that click operations produced expected results.
    """

    def __init__(self):
        self.dom_detector = DOMChangeDetector()
        self.page_detector = PageStateDetector()
        self.network_detector = NetworkActivityDetector()
        self.event_validator = EventValidation()

    async def validate(
        self,
        element_info: Dict[str, Any],
        previous_state: Dict[str, Any],
        page_context: Dict[str, Any],
        expected_changes: Optional[List[ChangeType]] = None,
        timeout_ms: int = 1000
    ) -> PostClickValidationResult:
        """
        Run comprehensive post-click validation.

        Args:
            element_info: Current element state
            previous_state: Element state before click
            page_context: Page-level information
            expected_changes: Expected types of changes (None = any change)
            timeout_ms: How long to wait for changes

        Returns:
            PostClickValidationResult with detected changes
        """
        start_time = asyncio.get_event_loop().time()
        all_changes = []

        # Detect DOM changes
        attr_changes = await self.dom_detector.detect_attribute_changes(
            element_info, previous_state, timeout_ms
        )
        all_changes.extend(attr_changes)

        style_changes = await self.dom_detector.detect_style_changes(
            element_info, previous_state
        )
        all_changes.extend(style_changes)

        text_changes = await self.dom_detector.detect_text_changes(
            element_info, previous_state
        )
        all_changes.extend(text_changes)

        # Detect page state changes
        url_change = await self.page_detector.detect_url_change(
            previous_state.get('url', ''),
            page_context.get('url', '')
        )
        if url_change:
            all_changes.append(url_change)

        focus_change = await self.page_detector.detect_focus_change(
            previous_state.get('focused_element'),
            page_context.get('focused_element')
        )
        if focus_change:
            all_changes.append(focus_change)

        # Detect new/removed elements
        new_elements = await self.page_detector.detect_new_elements(page_context)
        all_changes.extend(new_elements)

        removed_elements = await self.page_detector.detect_removed_elements(page_context)
        all_changes.extend(removed_elements)

        # Detect network activity
        network_log = page_context.get('network_log', [])
        network_changes = await self.network_detector.detect_network_requests(network_log)
        all_changes.extend(network_changes)

        # Validate event firing
        event_log = page_context.get('event_log', [])
        event_fired = await self.event_validator.validate_click_event_fired(event_log)
        event_analysis = self.event_validator.analyze_event_propagation(event_log)

        # Check if expected changes occurred
        expected_changes_met = True

        if expected_changes:
            detected_types = {change.change_type for change in all_changes}
            expected_types = set(expected_changes)

            missing_changes = expected_types - detected_types
            expected_changes_met = len(missing_changes) == 0

        end_time = asyncio.get_event_loop().time()
        verification_time_ms = (end_time - start_time) * 1000

        # Determine overall success
        success = (
            event_fired and
            (len(all_changes) > 0 or expected_changes is None) and
            expected_changes_met
        )

        details = {
            'total_changes': len(all_changes),
            'change_types': [c.change_type.value for c in all_changes],
            'event_fired': event_fired,
            'event_analysis': event_analysis,
            'expected_changes': [c.value for c in expected_changes] if expected_changes else None,
            'expected_changes_met': expected_changes_met
        }

        return PostClickValidationResult(
            success=success,
            changes_detected=all_changes,
            expected_changes_met=expected_changes_met,
            verification_time_ms=verification_time_ms,
            details=details
        )

    async def quick_validate(
        self,
        page_context: Dict[str, Any]
    ) -> bool:
        """
        Quick validation - just check if any change occurred.

        Returns:
            True if any change was detected
        """
        event_log = page_context.get('event_log', [])
        event_fired = await self.event_validator.validate_click_event_fired(event_log)

        # Check for URL change
        has_url_change = page_context.get('url_changed', False)

        # Check for new elements
        has_new_elements = len(page_context.get('new_elements', [])) > 0

        # Check for network activity
        has_network = len(page_context.get('network_log', [])) > 0

        return event_fired or has_url_change or has_new_elements or has_network


class ClickResultMonitor:
    """Monitor and log click results for analysis"""

    def __init__(self):
        self.click_results: List[Dict[str, Any]] = []

    def log_result(
        self,
        selector: str,
        validation_result: PostClickValidationResult,
        expected_outcome: Optional[str] = None
    ):
        """Log a click result"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'selector': selector,
            'success': validation_result.success,
            'changes_count': len(validation_result.changes_detected),
            'change_types': [c.change_type.value for c in validation_result.changes_detected],
            'expected_outcome': expected_outcome,
            'verification_time_ms': validation_result.verification_time_ms
        }

        self.click_results.append(entry)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics from logged click results"""
        if not self.click_results:
            return {}

        total = len(self.click_results)
        successful = sum(1 for r in self.click_results if r['success'])

        avg_verification_time = sum(
            r['verification_time_ms'] for r in self.click_results
        ) / total

        # Count change types
        all_change_types = []
        for result in self.click_results:
            all_change_types.extend(result['change_types'])

        change_type_counts = {}
        for ct in all_change_types:
            change_type_counts[ct] = change_type_counts.get(ct, 0) + 1

        return {
            'total_clicks': total,
            'successful': successful,
            'success_rate': successful / total if total > 0 else 0,
            'avg_verification_time_ms': avg_verification_time,
            'change_type_distribution': change_type_counts
        }
