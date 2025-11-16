"""
Pre-Click Validation Module

Comprehensive pre-click validation including:
- Visibility checks (checkVisibility API, computed styles)
- Interactability validation (enabled, pointer-events)
- Stability checks (no animation, stable position)
- Element-at-point verification
- Z-index handling for overlapping elements
- Hover state validation

Reference: CLICK_VALIDATION_RESEARCH.md Sections 1, 5, 6
"""

import asyncio
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


class ValidationStatus(Enum):
    """Pre-click validation status"""
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"


@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    severity: str  # 'error', 'warning'
    category: str  # 'visibility', 'interactability', 'stability', etc.
    message: str
    details: Dict[str, Any]


@dataclass
class PreClickValidationResult:
    """Result of pre-click validation"""
    passed: bool
    status: ValidationStatus
    issues: List[ValidationIssue]
    can_proceed: bool
    recommendations: List[str]
    details: Dict[str, Any]


class VisibilityChecker:
    """Handles all visibility-related validation"""

    @staticmethod
    def check_visibility(element_info: Dict[str, Any]) -> Tuple[bool, List[ValidationIssue]]:
        """
        Comprehensive visibility check using multiple methods.

        Checks:
        1. Element has dimensions (width > 0, height > 0)
        2. Not display: none
        3. Not visibility: hidden
        4. Opacity > 0
        5. In viewport (at least partially)
        6. checkVisibility API (if available)

        Returns:
            (is_visible, issues)
        """
        issues = []
        rect = element_info.get('rect', {})
        style = element_info.get('computed_style', {})
        viewport = element_info.get('viewport', {})

        # Check 1: Element dimensions
        width = rect.get('width', 0)
        height = rect.get('height', 0)

        if width <= 0 or height <= 0:
            issues.append(ValidationIssue(
                severity='error',
                category='visibility',
                message='Element has no dimensions',
                details={'width': width, 'height': height}
            ))
            return False, issues

        # Check 2: Display property
        display = style.get('display', '')
        if display == 'none':
            issues.append(ValidationIssue(
                severity='error',
                category='visibility',
                message='Element has display: none',
                details={'display': display}
            ))
            return False, issues

        # Check 3: Visibility property
        visibility = style.get('visibility', 'visible')
        if visibility == 'hidden':
            issues.append(ValidationIssue(
                severity='error',
                category='visibility',
                message='Element has visibility: hidden',
                details={'visibility': visibility}
            ))
            return False, issues

        # Check 4: Opacity
        opacity = float(style.get('opacity', 1.0))
        if opacity <= 0:
            issues.append(ValidationIssue(
                severity='error',
                category='visibility',
                message='Element has opacity: 0',
                details={'opacity': opacity}
            ))
            return False, issues
        elif opacity < 0.5:
            issues.append(ValidationIssue(
                severity='warning',
                category='visibility',
                message='Element has low opacity',
                details={'opacity': opacity}
            ))

        # Check 5: Viewport visibility
        viewport_width = viewport.get('width', 1920)
        viewport_height = viewport.get('height', 1080)

        left = rect.get('left', 0)
        top = rect.get('top', 0)
        right = left + width
        bottom = top + height

        in_viewport = (
            top < viewport_height and
            bottom > 0 and
            left < viewport_width and
            right > 0
        )

        if not in_viewport:
            issues.append(ValidationIssue(
                severity='error',
                category='visibility',
                message='Element is outside viewport',
                details={
                    'rect': rect,
                    'viewport': {'width': viewport_width, 'height': viewport_height}
                }
            ))
            return False, issues

        # Calculate visible percentage
        visible_width = min(right, viewport_width) - max(left, 0)
        visible_height = min(bottom, viewport_height) - max(top, 0)
        visible_area = max(0, visible_width) * max(0, visible_height)
        total_area = width * height
        visible_percentage = (visible_area / total_area) * 100 if total_area > 0 else 0

        if visible_percentage < 50:
            issues.append(ValidationIssue(
                severity='warning',
                category='visibility',
                message=f'Only {visible_percentage:.1f}% of element is visible',
                details={'visible_percentage': visible_percentage}
            ))

        # Check 6: checkVisibility API (if data provided)
        check_visibility_result = element_info.get('check_visibility', True)
        if not check_visibility_result:
            issues.append(ValidationIssue(
                severity='error',
                category='visibility',
                message='Element failed checkVisibility() API check',
                details={'check_visibility': check_visibility_result}
            ))
            return False, issues

        # Element is visible if no error issues found
        has_errors = any(issue.severity == 'error' for issue in issues)
        return not has_errors, issues


class InteractabilityChecker:
    """Handles interactability validation"""

    @staticmethod
    def check_interactability(element_info: Dict[str, Any]) -> Tuple[bool, List[ValidationIssue]]:
        """
        Check if element is interactable.

        Checks:
        1. Not disabled
        2. pointer-events not 'none'
        3. Not aria-disabled
        4. Not readonly (for form elements)
        5. Has event listeners (optional)

        Returns:
            (is_interactable, issues)
        """
        issues = []
        attrs = element_info.get('attributes', {})
        style = element_info.get('computed_style', {})
        tag_name = element_info.get('tag_name', '').upper()

        # Check 1: Disabled attribute
        if attrs.get('disabled', False):
            issues.append(ValidationIssue(
                severity='error',
                category='interactability',
                message='Element is disabled',
                details={'disabled': True}
            ))
            return False, issues

        # Check 2: Pointer events
        pointer_events = style.get('pointer_events', 'auto')
        if pointer_events == 'none':
            issues.append(ValidationIssue(
                severity='error',
                category='interactability',
                message='Element has pointer-events: none',
                details={'pointer_events': pointer_events}
            ))
            return False, issues

        # Check 3: ARIA disabled
        aria_disabled = attrs.get('aria_disabled', 'false')
        if aria_disabled == 'true':
            issues.append(ValidationIssue(
                severity='warning',
                category='interactability',
                message='Element has aria-disabled="true"',
                details={'aria_disabled': aria_disabled}
            ))

        # Check 4: Readonly (for form elements)
        is_form_element = tag_name in ['INPUT', 'BUTTON', 'SELECT', 'TEXTAREA']
        if is_form_element and attrs.get('readonly', False):
            issues.append(ValidationIssue(
                severity='warning',
                category='interactability',
                message='Form element is readonly',
                details={'readonly': True, 'tag_name': tag_name}
            ))

        # Element is interactable if no error issues found
        has_errors = any(issue.severity == 'error' for issue in issues)
        return not has_errors, issues


class StabilityChecker:
    """Handles element stability validation"""

    @staticmethod
    async def check_stability(
        element_info: Dict[str, Any],
        threshold_px: float = 2.0
    ) -> Tuple[bool, List[ValidationIssue]]:
        """
        Check if element position is stable (not animating).

        Checks position history to ensure element is not moving.
        Element is considered stable if position variance < threshold.

        Args:
            element_info: Element information with position history
            threshold_px: Maximum allowed movement in pixels

        Returns:
            (is_stable, issues)
        """
        issues = []
        position_history = element_info.get('position_history', [])

        if len(position_history) < 2:
            # Not enough data, assume stable
            return True, issues

        # Calculate movement between consecutive positions
        movements = []

        for i in range(1, len(position_history)):
            prev = position_history[i - 1]
            curr = position_history[i]

            dx = curr.get('x', 0) - prev.get('x', 0)
            dy = curr.get('y', 0) - prev.get('y', 0)

            movement = math.sqrt(dx * dx + dy * dy)
            movements.append(movement)

        max_movement = max(movements) if movements else 0
        avg_movement = sum(movements) / len(movements) if movements else 0

        if max_movement > threshold_px:
            issues.append(ValidationIssue(
                severity='error',
                category='stability',
                message='Element position is unstable (moving)',
                details={
                    'max_movement_px': max_movement,
                    'avg_movement_px': avg_movement,
                    'threshold_px': threshold_px
                }
            ))
            return False, issues

        if avg_movement > threshold_px / 2:
            issues.append(ValidationIssue(
                severity='warning',
                category='stability',
                message='Element position shows minor instability',
                details={
                    'avg_movement_px': avg_movement,
                    'threshold_px': threshold_px
                }
            ))

        # Check for animations
        has_animations = element_info.get('has_animations', False)
        if has_animations:
            issues.append(ValidationIssue(
                severity='warning',
                category='stability',
                message='Element has active CSS animations',
                details={'has_animations': True}
            ))

        has_errors = any(issue.severity == 'error' for issue in issues)
        return not has_errors, issues


class HitTargetChecker:
    """Handles element-at-point and z-index validation"""

    @staticmethod
    def check_hit_target(element_info: Dict[str, Any]) -> Tuple[bool, List[ValidationIssue]]:
        """
        Verify element would receive click at various points.

        Tests multiple points within element bounds:
        - Center
        - Four quadrants

        Returns:
            (is_hit_target, issues)
        """
        issues = []
        hit_test_results = element_info.get('hit_test_results', [])

        if not hit_test_results:
            # No hit test data available
            issues.append(ValidationIssue(
                severity='warning',
                category='hit_target',
                message='No hit test data available',
                details={'hit_test_results': None}
            ))
            return True, issues

        # Count successful hits
        total_tests = len(hit_test_results)
        successful_hits = sum(1 for r in hit_test_results if r.get('is_target', False))
        hit_percentage = (successful_hits / total_tests * 100) if total_tests > 0 else 0

        # Analyze failed hits
        failed_tests = [r for r in hit_test_results if not r.get('is_target', False)]

        if successful_hits == 0:
            # Element is completely obscured
            obscuring_elements = [r.get('actual_element') for r in failed_tests]
            issues.append(ValidationIssue(
                severity='error',
                category='hit_target',
                message='Element is completely obscured by other elements',
                details={
                    'hit_percentage': 0,
                    'obscuring_elements': obscuring_elements
                }
            ))
            return False, issues

        if hit_percentage < 80:
            # Element is partially obscured
            obscuring_elements = [r.get('actual_element') for r in failed_tests]
            issues.append(ValidationIssue(
                severity='warning',
                category='hit_target',
                message=f'Element is partially obscured ({hit_percentage:.0f}% hit rate)',
                details={
                    'hit_percentage': hit_percentage,
                    'successful_hits': successful_hits,
                    'total_tests': total_tests,
                    'obscuring_elements': obscuring_elements
                }
            ))

        has_errors = any(issue.severity == 'error' for issue in issues)
        return not has_errors, issues

    @staticmethod
    def analyze_z_index(element_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze element's z-index and stacking context.

        Returns:
            Dictionary with z-index analysis
        """
        style = element_info.get('computed_style', {})
        position = style.get('position', 'static')
        z_index = style.get('z_index', 'auto')

        # z-index only works on positioned elements
        is_positioned = position in ['relative', 'absolute', 'fixed', 'sticky']

        try:
            z_index_value = int(z_index) if z_index != 'auto' else None
        except (ValueError, TypeError):
            z_index_value = None

        effective_z_index = z_index_value if is_positioned else None

        return {
            'position': position,
            'z_index': z_index,
            'is_positioned': is_positioned,
            'effective_z_index': effective_z_index,
            'creates_stacking_context': is_positioned and z_index != 'auto'
        }


class HoverStateChecker:
    """Handles hover state validation"""

    @staticmethod
    def check_hover_state(element_info: Dict[str, Any]) -> Tuple[bool, List[ValidationIssue]]:
        """
        Check if element responds to hover events.

        Checks:
        1. pointer-events not 'none'
        2. Element has :hover styles defined
        3. Cursor changes on hover

        Returns:
            (is_hoverable, issues)
        """
        issues = []
        style = element_info.get('computed_style', {})
        has_hover_styles = element_info.get('has_hover_styles', False)

        # Check pointer events
        pointer_events = style.get('pointer_events', 'auto')
        if pointer_events == 'none':
            issues.append(ValidationIssue(
                severity='error',
                category='hover',
                message='Element cannot receive hover (pointer-events: none)',
                details={'pointer_events': pointer_events}
            ))
            return False, issues

        # Check for hover styles
        if not has_hover_styles:
            issues.append(ValidationIssue(
                severity='warning',
                category='hover',
                message='Element has no :hover styles defined',
                details={'has_hover_styles': False}
            ))

        # Check cursor style
        cursor = style.get('cursor', 'auto')
        if cursor not in ['pointer', 'hand', 'grab']:
            issues.append(ValidationIssue(
                severity='warning',
                category='hover',
                message=f'Element cursor is "{cursor}", not a clickable cursor',
                details={'cursor': cursor}
            ))

        has_errors = any(issue.severity == 'error' for issue in issues)
        return not has_errors, issues


class PreClickValidator:
    """
    Main pre-click validation orchestrator.

    Coordinates all validation checks and provides comprehensive results.
    """

    def __init__(self):
        self.visibility_checker = VisibilityChecker()
        self.interactability_checker = InteractabilityChecker()
        self.stability_checker = StabilityChecker()
        self.hit_target_checker = HitTargetChecker()
        self.hover_state_checker = HoverStateChecker()

    async def validate(
        self,
        element_info: Dict[str, Any],
        checks: Optional[List[str]] = None
    ) -> PreClickValidationResult:
        """
        Run comprehensive pre-click validation.

        Args:
            element_info: Complete element information
            checks: Specific checks to run (None = all checks)

        Returns:
            PreClickValidationResult with detailed findings
        """
        all_checks = checks or [
            'visibility',
            'interactability',
            'stability',
            'hit_target',
            'hover'
        ]

        all_issues = []
        check_results = {}
        recommendations = []

        # Run visibility check
        if 'visibility' in all_checks:
            visible, vis_issues = self.visibility_checker.check_visibility(element_info)
            check_results['visibility'] = visible
            all_issues.extend(vis_issues)

            if not visible:
                recommendations.append('Scroll element into viewport')
                recommendations.append('Check if element is hidden by CSS')

        # Run interactability check
        if 'interactability' in all_checks:
            interactable, int_issues = self.interactability_checker.check_interactability(element_info)
            check_results['interactability'] = interactable
            all_issues.extend(int_issues)

            if not interactable:
                recommendations.append('Enable the element before clicking')
                recommendations.append('Check pointer-events CSS property')

        # Run stability check
        if 'stability' in all_checks:
            stable, stab_issues = await self.stability_checker.check_stability(element_info)
            check_results['stability'] = stable
            all_issues.extend(stab_issues)

            if not stable:
                recommendations.append('Wait for element position to stabilize')
                recommendations.append('Wait for animations to complete')

        # Run hit target check
        if 'hit_target' in all_checks:
            is_target, hit_issues = self.hit_target_checker.check_hit_target(element_info)
            check_results['hit_target'] = is_target
            all_issues.extend(hit_issues)

            if not is_target:
                recommendations.append('Remove or dismiss overlaying elements')
                recommendations.append('Use JavaScript click to bypass visual layer')

        # Run hover state check
        if 'hover' in all_checks:
            hoverable, hover_issues = self.hover_state_checker.check_hover_state(element_info)
            check_results['hover'] = hoverable
            all_issues.extend(hover_issues)

        # Determine overall status
        has_errors = any(issue.severity == 'error' for issue in all_issues)
        all_passed = all(check_results.values())

        if has_errors:
            status = ValidationStatus.FAILED
            can_proceed = False
        elif all_issues:
            status = ValidationStatus.WARNING
            can_proceed = True
        else:
            status = ValidationStatus.PASSED
            can_proceed = True

        # Add z-index analysis to details
        z_index_analysis = self.hit_target_checker.analyze_z_index(element_info)

        details = {
            'check_results': check_results,
            'z_index_analysis': z_index_analysis,
            'total_issues': len(all_issues),
            'error_count': sum(1 for i in all_issues if i.severity == 'error'),
            'warning_count': sum(1 for i in all_issues if i.severity == 'warning')
        }

        return PreClickValidationResult(
            passed=all_passed,
            status=status,
            issues=all_issues,
            can_proceed=can_proceed,
            recommendations=recommendations,
            details=details
        )

    async def quick_validate(self, element_info: Dict[str, Any]) -> bool:
        """
        Quick validation for fast checks.
        Returns True if element can be clicked safely.

        Checks only:
        - Visibility
        - Interactability
        - Hit target
        """
        result = await self.validate(
            element_info,
            checks=['visibility', 'interactability', 'hit_target']
        )

        return result.can_proceed
