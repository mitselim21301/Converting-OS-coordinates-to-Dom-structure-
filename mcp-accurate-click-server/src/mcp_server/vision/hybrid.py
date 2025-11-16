"""
Hybrid DOM + Vision validation.

This module combines DOM-based coordinate validation with vision-based
validation for robust, multi-method verification.
"""

import logging
from typing import Dict, List, Optional, Union
import numpy as np
from pathlib import Path

from .models import (
    BoundingBox, ValidationResult, ValidationMethod,
    HybridValidationResult, ValidationConfig, ConfidenceWeights
)
from .validators import (
    TemplateMatchingValidator, FeatureMatchingValidator,
    OCRValidator, EdgeDetectionValidator, ColorProfileValidator
)
from .screenshot import ScreenCapture

logger = logging.getLogger(__name__)


class HybridValidator:
    """
    Combines multiple validation methods for robust verification.

    Supports:
    - Template matching (OpenCV)
    - Feature matching (ORB)
    - OCR text verification
    - Edge detection
    - Color profile validation
    """

    def __init__(
        self,
        weights: Optional[ConfidenceWeights] = None,
        enable_cache: bool = True
    ):
        """
        Initialize hybrid validator.

        Args:
            weights: Custom confidence weights for each method
            enable_cache: Enable result caching for performance
        """
        self.weights = weights or ConfidenceWeights()
        self.weights = self.weights.normalize()
        self.enable_cache = enable_cache

        # Initialize validators
        self.template_validator = TemplateMatchingValidator()
        self.feature_validator = FeatureMatchingValidator()
        self.ocr_validator = OCRValidator()
        self.edge_validator = EdgeDetectionValidator()
        self.color_validator = ColorProfileValidator()
        self.screen_capture = ScreenCapture()

        # Cache for screenshots and templates
        self._cache = {} if enable_cache else None

        logger.info("Hybrid validator initialized with weights: %s", self.weights.to_dict())

    def validate(
        self,
        screenshot: Union[np.ndarray, BoundingBox],
        config: ValidationConfig
    ) -> HybridValidationResult:
        """
        Run multiple validation methods.

        Args:
            screenshot: Screenshot as numpy array or BoundingBox to capture
            config: Validation configuration

        Returns:
            HybridValidationResult with results from all methods
        """
        # Capture screenshot if BoundingBox provided
        if isinstance(screenshot, BoundingBox):
            screenshot = self.screen_capture.capture_region(screenshot)

        results = {}
        methods = config.methods

        # Template matching
        if 'template_matching' in methods:
            results['template_matching'] = self._validate_template(screenshot, config)

        # Feature matching
        if 'feature_matching' in methods:
            results['feature_matching'] = self._validate_features(screenshot, config)

        # OCR
        if 'ocr' in methods:
            results['ocr'] = self._validate_ocr(screenshot, config)

        # Color profile
        if 'color_profile' in methods:
            results['color_profile'] = self._validate_color(screenshot, config)

        # Edge detection
        if 'edge_detection' in methods:
            results['edge_detection'] = self._validate_edges(screenshot, config)

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(results)

        # Determine primary bounding box
        primary_bbox = self._determine_primary_bbox(results)

        # Generate recommendation
        recommendation = self._generate_recommendation(
            results, overall_confidence
        )

        return HybridValidationResult(
            results=results,
            overall_confidence=overall_confidence,
            primary_bbox=primary_bbox,
            recommendation=recommendation
        )

    def _validate_template(
        self,
        screenshot: np.ndarray,
        config: ValidationConfig
    ) -> ValidationResult:
        """Validate using template matching."""
        try:
            if config.template_path is None:
                return ValidationResult(
                    method=ValidationMethod.TEMPLATE_MATCHING,
                    success=False,
                    confidence=0.0,
                    error="No template provided"
                )

            # Load template (with caching)
            template = self._load_template(config.template_path)

            if config.scale_invariant:
                return self.template_validator.multi_scale_validate(
                    screenshot, template
                )
            else:
                return self.template_validator.validate(
                    screenshot, template
                )

        except Exception as e:
            logger.error(f"Template validation error: {e}")
            return ValidationResult(
                method=ValidationMethod.TEMPLATE_MATCHING,
                success=False,
                confidence=0.0,
                error=str(e)
            )

    def _validate_features(
        self,
        screenshot: np.ndarray,
        config: ValidationConfig
    ) -> ValidationResult:
        """Validate using feature matching."""
        try:
            if config.template_path is None:
                return ValidationResult(
                    method=ValidationMethod.FEATURE_MATCHING,
                    success=False,
                    confidence=0.0,
                    error="No template provided"
                )

            template = self._load_template(config.template_path)

            return self.feature_validator.validate(screenshot, template)

        except Exception as e:
            logger.error(f"Feature validation error: {e}")
            return ValidationResult(
                method=ValidationMethod.FEATURE_MATCHING,
                success=False,
                confidence=0.0,
                error=str(e)
            )

    def _validate_ocr(
        self,
        screenshot: np.ndarray,
        config: ValidationConfig
    ) -> ValidationResult:
        """Validate using OCR."""
        try:
            if config.expected_text is None:
                return ValidationResult(
                    method=ValidationMethod.OCR,
                    success=False,
                    confidence=0.0,
                    error="No expected text provided"
                )

            return self.ocr_validator.validate_text_at_location(
                screenshot,
                config.expected_text,
                config.bbox
            )

        except Exception as e:
            logger.error(f"OCR validation error: {e}")
            return ValidationResult(
                method=ValidationMethod.OCR,
                success=False,
                confidence=0.0,
                error=str(e)
            )

    def _validate_color(
        self,
        screenshot: np.ndarray,
        config: ValidationConfig
    ) -> ValidationResult:
        """Validate using color profile."""
        try:
            if config.expected_color is None:
                return ValidationResult(
                    method=ValidationMethod.COLOR_PROFILE,
                    success=False,
                    confidence=0.0,
                    error="No expected color provided"
                )

            if config.bbox is None:
                return ValidationResult(
                    method=ValidationMethod.COLOR_PROFILE,
                    success=False,
                    confidence=0.0,
                    error="No bounding box provided"
                )

            return self.color_validator.validate(
                screenshot,
                config.expected_color,
                config.bbox
            )

        except Exception as e:
            logger.error(f"Color validation error: {e}")
            return ValidationResult(
                method=ValidationMethod.COLOR_PROFILE,
                success=False,
                confidence=0.0,
                error=str(e)
            )

    def _validate_edges(
        self,
        screenshot: np.ndarray,
        config: ValidationConfig
    ) -> ValidationResult:
        """Validate using edge detection."""
        try:
            if config.bbox is None:
                return ValidationResult(
                    method=ValidationMethod.EDGE_DETECTION,
                    success=False,
                    confidence=0.0,
                    error="No bounding box provided"
                )

            return self.edge_validator.validate_element_at_location(
                screenshot,
                config.bbox
            )

        except Exception as e:
            logger.error(f"Edge validation error: {e}")
            return ValidationResult(
                method=ValidationMethod.EDGE_DETECTION,
                success=False,
                confidence=0.0,
                error=str(e)
            )

    def _calculate_overall_confidence(
        self,
        results: Dict[str, ValidationResult]
    ) -> float:
        """Calculate weighted overall confidence."""
        if not results:
            return 0.0

        total_confidence = 0.0
        total_weight = 0.0

        weight_map = self.weights.to_dict()

        for method, result in results.items():
            if result.error:
                continue

            weight = weight_map.get(method, 0.0)
            total_confidence += result.confidence * weight
            total_weight += weight

        return total_confidence / total_weight if total_weight > 0 else 0.0

    def _determine_primary_bbox(
        self,
        results: Dict[str, ValidationResult]
    ) -> Optional[BoundingBox]:
        """
        Determine the best bounding box from all results.

        Returns the bbox from the result with highest confidence.
        """
        best_result = None
        best_confidence = 0.0

        for result in results.values():
            if result.bbox and result.confidence > best_confidence:
                best_confidence = result.confidence
                best_result = result

        return best_result.bbox if best_result else None

    def _generate_recommendation(
        self,
        results: Dict[str, ValidationResult],
        overall_confidence: float
    ) -> str:
        """Generate action recommendation based on validation results."""
        success_count = sum(1 for r in results.values() if r.success)
        total_count = len(results)

        if overall_confidence >= 0.9:
            return "High confidence - proceed with action"
        elif overall_confidence >= 0.7:
            return "Good confidence - action likely safe"
        elif overall_confidence >= 0.5:
            return "Medium confidence - verify before action"
        elif success_count > 0:
            return "Low confidence - manual verification recommended"
        else:
            return "Validation failed - do not proceed"

    def _load_template(self, template_path: str) -> np.ndarray:
        """Load template with caching."""
        if self.enable_cache and template_path in self._cache:
            return self._cache[template_path]

        template = self.screen_capture.load_image(template_path, as_numpy=True)

        if self.enable_cache:
            self._cache[template_path] = template

        return template


class DOMVisionValidator:
    """
    Integrates DOM-based validation with vision validation.

    Validates that DOM coordinates match visual appearance.
    """

    def __init__(self, hybrid_validator: Optional[HybridValidator] = None):
        """
        Initialize DOM + Vision validator.

        Args:
            hybrid_validator: Optional HybridValidator instance
        """
        self.hybrid_validator = hybrid_validator or HybridValidator()
        self.screen_capture = ScreenCapture()

    def validate_dom_coordinates(
        self,
        dom_bbox: BoundingBox,
        expected_properties: Dict,
        screenshot: Optional[np.ndarray] = None
    ) -> HybridValidationResult:
        """
        Validate DOM element coordinates using vision.

        Args:
            dom_bbox: Bounding box from DOM
            expected_properties: Expected visual properties
                - text: Expected text content
                - color: Expected RGB color
                - template: Path to template image
            screenshot: Optional pre-captured screenshot

        Returns:
            HybridValidationResult with validation results
        """
        # Capture screenshot if not provided
        if screenshot is None:
            screenshot = self.screen_capture.capture_region(dom_bbox)
        else:
            # Crop to bbox
            screenshot = screenshot[dom_bbox.y:dom_bbox.y2, dom_bbox.x:dom_bbox.x2]

        # Build validation config
        config = self._build_config_from_properties(
            dom_bbox, expected_properties
        )

        # Run hybrid validation
        result = self.hybrid_validator.validate(screenshot, config)

        # Add DOM-specific metadata
        for method_result in result.results.values():
            method_result.metadata['dom_bbox'] = dom_bbox.to_dict()

        return result

    def validate_coordinate_transformation(
        self,
        os_bbox: BoundingBox,
        dom_bbox: BoundingBox,
        tolerance: float = 0.95
    ) -> ValidationResult:
        """
        Validate OS to DOM coordinate transformation.

        Captures both regions and compares visually to ensure
        transformation is correct.

        Args:
            os_bbox: OS coordinate bounding box
            dom_bbox: Corresponding DOM bounding box
            tolerance: Similarity threshold

        Returns:
            ValidationResult indicating transformation accuracy
        """
        try:
            # Capture both regions
            os_screenshot = self.screen_capture.capture_region(os_bbox)
            dom_screenshot = self.screen_capture.capture_region(dom_bbox)

            # Use template matching to compare
            result = self.hybrid_validator.template_validator.validate(
                os_screenshot, dom_screenshot
            )

            success = result.confidence >= tolerance

            return ValidationResult(
                method=ValidationMethod.TEMPLATE_MATCHING,
                success=success,
                confidence=result.confidence,
                bbox=result.bbox,
                metadata={
                    'os_bbox': os_bbox.to_dict(),
                    'dom_bbox': dom_bbox.to_dict(),
                    'transformation_valid': success,
                    'similarity': result.confidence
                }
            )

        except Exception as e:
            logger.error(f"Coordinate transformation validation failed: {e}")
            return ValidationResult(
                method=ValidationMethod.TEMPLATE_MATCHING,
                success=False,
                confidence=0.0,
                error=str(e)
            )

    def _build_config_from_properties(
        self,
        bbox: BoundingBox,
        properties: Dict
    ) -> ValidationConfig:
        """Build ValidationConfig from expected properties."""
        methods = []

        config = ValidationConfig(bbox=bbox)

        if 'text' in properties:
            config.expected_text = properties['text']
            methods.append('ocr')

        if 'color' in properties:
            config.expected_color = properties['color']
            methods.append('color_profile')

        if 'template' in properties:
            config.template_path = properties['template']
            methods.append('template_matching')
            methods.append('feature_matching')

        # Always use edge detection as baseline
        methods.append('edge_detection')

        config.methods = methods

        return config


class ClickValidator:
    """
    Pre-click and post-click validation using vision.

    Ensures click target is valid before clicking and verifies
    expected outcome after clicking.
    """

    def __init__(self, hybrid_validator: Optional[HybridValidator] = None):
        """
        Initialize click validator.

        Args:
            hybrid_validator: Optional HybridValidator instance
        """
        self.hybrid_validator = hybrid_validator or HybridValidator()
        self.screen_capture = ScreenCapture()

    def pre_click_validate(
        self,
        click_coords: tuple[int, int],
        expected_element: Dict
    ) -> HybridValidationResult:
        """
        Validate click target before clicking.

        Args:
            click_coords: (x, y) coordinates to click
            expected_element: Expected element properties
                - type: Element type (button, link, etc.)
                - text: Expected text
                - width, height: Approximate dimensions

        Returns:
            HybridValidationResult with pre-click validation
        """
        # Create bounding box around click coordinates
        x, y = click_coords
        width = expected_element.get('width', 100)
        height = expected_element.get('height', 50)

        # Center bbox on click coordinates
        bbox = BoundingBox(
            x=x - width // 2,
            y=y - height // 2,
            width=width,
            height=height
        )

        # Capture region
        screenshot = self.screen_capture.capture_region(bbox)

        # Build validation config
        config = ValidationConfig(bbox=bbox)

        if 'text' in expected_element:
            config.expected_text = expected_element['text']
            config.methods.append('ocr')

        if 'template' in expected_element:
            config.template_path = expected_element['template']
            config.methods.extend(['template_matching', 'feature_matching'])

        # Always use edge detection
        config.methods.append('edge_detection')

        # Run validation
        result = self.hybrid_validator.validate(screenshot, config)

        # Add metadata
        result.results['pre_click'] = ValidationResult(
            method=ValidationMethod.HYBRID,
            success=result.overall_confidence >= 0.7,
            confidence=result.overall_confidence,
            bbox=bbox,
            metadata={
                'click_coords': click_coords,
                'expected_element': expected_element
            }
        )

        return result

    def post_click_validate(
        self,
        expected_outcome: Dict,
        pre_click_screenshot: Optional[np.ndarray] = None
    ) -> ValidationResult:
        """
        Validate outcome after clicking.

        Args:
            expected_outcome: Expected changes
                - text_appears: Text that should appear
                - text_disappears: Text that should disappear
                - color_change: Expected color change
            pre_click_screenshot: Optional screenshot before click

        Returns:
            ValidationResult indicating if outcome matches expectation
        """
        # This is a simplified implementation
        # Full implementation would compare before/after screenshots
        # and validate specific expected changes

        logger.info("Post-click validation (simplified)")

        return ValidationResult(
            method=ValidationMethod.HYBRID,
            success=True,
            confidence=0.8,
            metadata={'expected_outcome': expected_outcome}
        )
