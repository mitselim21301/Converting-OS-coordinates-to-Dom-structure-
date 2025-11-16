"""
Confidence Scoring System for Click Validation

Provides comprehensive confidence scoring (0-100) for click operations based on:
- Visibility score
- Interactability score
- Stability score
- Hit target score
- Timing score

Reference: CLICK_VALIDATION_RESEARCH.md Section 8
"""

import asyncio
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum


class Recommendation(Enum):
    """Click recommendation based on confidence score"""
    SAFE_TO_CLICK = "SAFE_TO_CLICK"           # >= 90%
    PROBABLY_SAFE = "PROBABLY_SAFE"           # >= 70%
    RISKY = "RISKY"                           # >= 50%
    DO_NOT_CLICK = "DO_NOT_CLICK"             # < 50%


class ActionType(Enum):
    """Types of actions with different confidence thresholds"""
    CRITICAL_ACTION = 95  # Financial transactions, deletions
    STANDARD_CLICK = 80   # Regular navigation, form submissions
    EXPLORATORY = 60      # Testing, optional interactions
    FALLBACK = 40         # Use alternative method below this


@dataclass
class ConfidenceScores:
    """Individual component scores for confidence calculation"""
    visibility: float
    interactability: float
    stability: float
    hit_target: float
    timing: float


@dataclass
class ConfidenceResult:
    """Complete confidence analysis result"""
    confidence: int  # 0-100
    scores: ConfidenceScores
    recommendation: Recommendation
    issues: List[str]
    safe: bool
    details: Dict[str, Any]


class ClickConfidenceCalculator:
    """
    Calculates confidence scores for click operations using weighted factors.

    Weights:
    - Visibility: 25%
    - Interactability: 25%
    - Stability: 20%
    - Hit Target: 20%
    - Timing: 10%
    """

    def __init__(self):
        self.weights = {
            'visibility': 0.25,
            'interactability': 0.25,
            'stability': 0.20,
            'hit_target': 0.20,
            'timing': 0.10
        }

    async def calculate_confidence(
        self,
        element_info: Dict[str, Any],
        page_context: Optional[Dict[str, Any]] = None
    ) -> ConfidenceResult:
        """
        Calculate comprehensive confidence score for clicking an element.

        Args:
            element_info: Element properties (rect, style, attributes, etc.)
            page_context: Page state (loading, animations, network, etc.)

        Returns:
            ConfidenceResult with score and detailed analysis
        """
        # Calculate individual scores
        visibility_score = self.calculate_visibility_score(element_info)
        interactability_score = self.calculate_interactability_score(element_info)
        stability_score = await self.calculate_stability_score(element_info)
        hit_target_score = self.calculate_hit_target_score(element_info)
        timing_score = self.calculate_timing_score(page_context or {})

        scores = ConfidenceScores(
            visibility=visibility_score,
            interactability=interactability_score,
            stability=stability_score,
            hit_target=hit_target_score,
            timing=timing_score
        )

        # Calculate weighted average
        confidence = (
            visibility_score * self.weights['visibility'] +
            interactability_score * self.weights['interactability'] +
            stability_score * self.weights['stability'] +
            hit_target_score * self.weights['hit_target'] +
            timing_score * self.weights['timing']
        )

        # Convert to 0-100 scale
        confidence_percentage = int(round(confidence * 100))

        # Get recommendation and issues
        recommendation = self._get_recommendation(confidence)
        issues = self._get_issues(scores)
        safe = len(issues) == 0

        details = {
            'weights': self.weights,
            'raw_confidence': confidence,
            'score_breakdown': {
                'visibility': f"{visibility_score:.2%}",
                'interactability': f"{interactability_score:.2%}",
                'stability': f"{stability_score:.2%}",
                'hit_target': f"{hit_target_score:.2%}",
                'timing': f"{timing_score:.2%}"
            }
        }

        return ConfidenceResult(
            confidence=confidence_percentage,
            scores=scores,
            recommendation=recommendation,
            issues=issues,
            safe=safe,
            details=details
        )

    def calculate_visibility_score(self, element_info: Dict[str, Any]) -> float:
        """
        Calculate visibility score based on:
        - Element size (width, height)
        - CSS properties (display, visibility, opacity)
        - Viewport visibility
        - Visible area percentage

        Returns: Score between 0.0 and 1.0
        """
        rect = element_info.get('rect', {})
        style = element_info.get('computed_style', {})
        viewport = element_info.get('viewport', {})

        # Check basic size
        width = rect.get('width', 0)
        height = rect.get('height', 0)

        if width == 0 or height == 0:
            return 0.0

        score = 1.0

        # Check display property
        if style.get('display') == 'none':
            return 0.0

        # Check visibility
        if style.get('visibility') == 'hidden':
            return 0.0

        # Penalize low opacity
        opacity = float(style.get('opacity', 1.0))
        score *= opacity

        # Check viewport visibility
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
            score *= 0.5  # Penalize but don't zero out

        # Calculate percentage in viewport
        visible_width = min(right, viewport_width) - max(left, 0)
        visible_height = min(bottom, viewport_height) - max(top, 0)

        visible_area = max(0, visible_width) * max(0, visible_height)
        total_area = width * height

        if total_area > 0:
            visible_percentage = visible_area / total_area
            score *= visible_percentage

        return max(0.0, min(1.0, score))

    def calculate_interactability_score(self, element_info: Dict[str, Any]) -> float:
        """
        Calculate interactability score based on:
        - Disabled state
        - Pointer events
        - ARIA disabled
        - Read-only state

        Returns: Score between 0.0 and 1.0
        """
        attrs = element_info.get('attributes', {})
        style = element_info.get('computed_style', {})
        tag_name = element_info.get('tag_name', '').upper()

        score = 1.0

        # Check if disabled
        if attrs.get('disabled', False):
            return 0.0

        # Check pointer events
        if style.get('pointer_events') == 'none':
            return 0.0

        # Check for form elements with readonly
        is_form_element = tag_name in ['INPUT', 'BUTTON', 'SELECT', 'TEXTAREA']

        if is_form_element and attrs.get('readonly', False):
            score *= 0.3  # Read-only fields have limited interactability

        # Check aria-disabled
        if attrs.get('aria_disabled') == 'true':
            score *= 0.2

        return score

    async def calculate_stability_score(
        self,
        element_info: Dict[str, Any],
        checks: int = 3,
        interval_ms: int = 50
    ) -> float:
        """
        Calculate stability score by checking if element position is stable.

        Args:
            element_info: Element information including position history
            checks: Number of position checks to perform
            interval_ms: Interval between checks

        Returns: Score between 0.0 and 1.0
        """
        # If position history is provided, use it
        position_history = element_info.get('position_history', [])

        if len(position_history) < 2:
            # Not enough data, assume stable
            return 1.0

        # Calculate variance in positions
        total_variance = 0.0

        for i in range(1, len(position_history)):
            prev = position_history[i - 1]
            curr = position_history[i]

            dx = curr.get('x', 0) - prev.get('x', 0)
            dy = curr.get('y', 0) - prev.get('y', 0)
            dw = curr.get('width', 0) - prev.get('width', 0)
            dh = curr.get('height', 0) - prev.get('height', 0)

            variance = math.sqrt(dx*dx + dy*dy + dw*dw + dh*dh)
            total_variance += variance

        # Calculate average variance
        avg_variance = total_variance / (len(position_history) - 1)

        # Convert variance to score (0 variance = 1.0 score)
        # Penalize variance over 5 pixels
        score = max(0.0, 1.0 - (avg_variance / 5.0))

        return score

    def calculate_hit_target_score(self, element_info: Dict[str, Any]) -> float:
        """
        Calculate hit target score based on element-at-point tests.

        Tests multiple points within element to ensure it would receive clicks:
        - Center
        - Four quadrants

        Returns: Score between 0.0 and 1.0
        """
        hit_test_results = element_info.get('hit_test_results', [])

        if not hit_test_results:
            # No hit test data, assume element is hit target
            return 1.0

        # Calculate percentage of test points that hit the target
        hits = sum(1 for result in hit_test_results if result.get('is_target', False))
        total = len(hit_test_results)

        if total == 0:
            return 1.0

        return hits / total

    def calculate_timing_score(self, page_context: Dict[str, Any]) -> float:
        """
        Calculate timing score based on page state:
        - Document ready state
        - Active animations
        - Pending network requests

        Returns: Score between 0.0 and 1.0
        """
        score = 1.0

        # Check document ready state
        ready_state = page_context.get('ready_state', 'complete')
        if ready_state != 'complete':
            score *= 0.5

        # Check for active animations
        active_animations = page_context.get('active_animations', 0)
        if active_animations > 0:
            score *= 0.8

        # Check for pending network requests
        pending_requests = page_context.get('pending_requests', 0)
        if pending_requests > 0:
            score *= 0.7

        return score

    def _get_recommendation(self, confidence: float) -> Recommendation:
        """Get click recommendation based on confidence score"""
        if confidence >= 0.9:
            return Recommendation.SAFE_TO_CLICK
        elif confidence >= 0.7:
            return Recommendation.PROBABLY_SAFE
        elif confidence >= 0.5:
            return Recommendation.RISKY
        else:
            return Recommendation.DO_NOT_CLICK

    def _get_issues(self, scores: ConfidenceScores) -> List[str]:
        """Identify specific issues based on component scores"""
        issues = []

        threshold = 0.8

        if scores.visibility < threshold:
            issues.append('Element visibility is compromised')

        if scores.interactability < threshold:
            issues.append('Element may not be interactable')

        if scores.stability < threshold:
            issues.append('Element position is unstable')

        if scores.hit_target < threshold:
            issues.append('Element may be obscured by other elements')

        if scores.timing < threshold:
            issues.append('Page is still loading or updating')

        return issues


class ClickStrategy(Enum):
    """Click strategy based on confidence level"""
    DIRECT_CLICK = "DIRECT_CLICK"
    RETRY_WITH_IMPROVEMENTS = "RETRY_WITH_IMPROVEMENTS"
    JAVASCRIPT_CLICK = "JAVASCRIPT_CLICK"
    MANUAL_INTERVENTION_REQUIRED = "MANUAL_INTERVENTION_REQUIRED"


def select_click_strategy(
    confidence: int,
    action_type: ActionType = ActionType.STANDARD_CLICK
) -> ClickStrategy:
    """
    Select appropriate click strategy based on confidence and action type.

    Args:
        confidence: Confidence score (0-100)
        action_type: Type of action being performed

    Returns:
        Recommended click strategy
    """
    threshold = action_type.value
    confidence_decimal = confidence / 100.0

    if confidence >= threshold:
        return ClickStrategy.DIRECT_CLICK
    elif confidence >= 50:
        return ClickStrategy.RETRY_WITH_IMPROVEMENTS
    elif confidence >= 30:
        return ClickStrategy.JAVASCRIPT_CLICK
    else:
        return ClickStrategy.MANUAL_INTERVENTION_REQUIRED


class ClickConfidenceMonitor:
    """Monitor and log click confidence scores for pattern analysis"""

    def __init__(self):
        self.click_history: List[Dict[str, Any]] = []

    def log_click_attempt(
        self,
        selector: str,
        confidence_result: ConfidenceResult,
        success: bool
    ):
        """Log a click attempt with its confidence and outcome"""
        entry = {
            'timestamp': asyncio.get_event_loop().time(),
            'selector': selector,
            'confidence': confidence_result.confidence,
            'success': success,
            'scores': confidence_result.scores,
            'recommendation': confidence_result.recommendation.value,
            'issues': confidence_result.issues
        }

        self.click_history.append(entry)

        # Analyze patterns periodically
        if len(self.click_history) % 10 == 0:
            self.analyze_pattern()

    def analyze_pattern(self):
        """Analyze recent click attempts for patterns"""
        if len(self.click_history) < 10:
            return

        recent = self.click_history[-10:]

        # Calculate average confidence
        avg_confidence = sum(e['confidence'] for e in recent) / len(recent)

        if avg_confidence < 70:
            print(f"⚠️  Average click confidence is low: {avg_confidence:.1f}%")
            common_issues = self._get_common_issues(recent)
            if common_issues:
                print(f"   Common issues: {', '.join(common_issues)}")

    def _get_common_issues(self, history: List[Dict[str, Any]]) -> List[str]:
        """Identify most common issues from click history"""
        issue_count: Dict[str, int] = {}

        for entry in history:
            for issue in entry.get('issues', []):
                issue_count[issue] = issue_count.get(issue, 0) + 1

        # Sort by frequency and return top 3
        sorted_issues = sorted(
            issue_count.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return [f"{issue} ({count}x)" for issue, count in sorted_issues[:3]]

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics from click history"""
        if not self.click_history:
            return {}

        total = len(self.click_history)
        successful = sum(1 for e in self.click_history if e['success'])

        confidences = [e['confidence'] for e in self.click_history]
        avg_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)
        max_confidence = max(confidences)

        return {
            'total_attempts': total,
            'successful': successful,
            'success_rate': successful / total if total > 0 else 0,
            'avg_confidence': avg_confidence,
            'min_confidence': min_confidence,
            'max_confidence': max_confidence,
            'common_issues': self._get_common_issues(self.click_history)
        }
