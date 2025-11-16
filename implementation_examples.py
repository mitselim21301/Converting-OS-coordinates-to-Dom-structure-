"""
Practical Implementation Examples for Vision-Based Coordinate Validation

This file contains ready-to-use code examples combining different
validation techniques for OS to DOM coordinate conversion.
"""

import cv2
import numpy as np
from PIL import Image, ImageGrab
import pytesseract
from typing import Dict, List, Tuple, Optional
import asyncio
from dataclasses import dataclass
from enum import Enum


# =============================================================================
# Data Models
# =============================================================================

class ValidationMethod(Enum):
    """Available validation methods"""
    TEMPLATE_MATCHING = "template_matching"
    FEATURE_MATCHING = "feature_matching"
    OCR = "ocr"
    COLOR_PROFILE = "color_profile"
    EDGE_DETECTION = "edge_detection"
    AI_DETECTION = "ai_detection"


@dataclass
class BoundingBox:
    """Bounding box representation"""
    x: int
    y: int
    width: int
    height: int

    @property
    def x2(self) -> int:
        return self.x + self.width

    @property
    def y2(self) -> int:
        return self.y + self.height

    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is within bounding box"""
        return self.x <= x <= self.x2 and self.y <= y <= self.y2

    def to_dict(self) -> Dict:
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height
        }


@dataclass
class ValidationResult:
    """Result of a validation check"""
    method: ValidationMethod
    success: bool
    confidence: float
    bbox: Optional[BoundingBox] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            'method': self.method.value,
            'success': self.success,
            'confidence': self.confidence,
            'bbox': self.bbox.to_dict() if self.bbox else None,
            'metadata': self.metadata or {}
        }


# =============================================================================
# Screenshot Capture Utilities
# =============================================================================

class ScreenCapture:
    """Utilities for capturing screenshots"""

    @staticmethod
    def capture_region(bbox: BoundingBox) -> np.ndarray:
        """
        Capture screenshot of specific region

        Args:
            bbox: Bounding box to capture

        Returns:
            Screenshot as numpy array (BGR format for OpenCV)
        """
        screenshot = ImageGrab.grab(bbox=(bbox.x, bbox.y, bbox.x2, bbox.y2))
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    @staticmethod
    def capture_full_screen() -> np.ndarray:
        """Capture full screen screenshot"""
        screenshot = ImageGrab.grab()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    @staticmethod
    def save_screenshot(image: np.ndarray, path: str):
        """Save screenshot to file"""
        cv2.imwrite(path, image)


# =============================================================================
# Template Matching Validator
# =============================================================================

class TemplateMatchingValidator:
    """Validate coordinates using template matching"""

    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold

    def validate(
        self,
        screenshot: np.ndarray,
        template: np.ndarray,
        method: int = cv2.TM_CCOEFF_NORMED
    ) -> ValidationResult:
        """
        Validate using template matching

        Args:
            screenshot: Full screenshot
            template: Template image to find
            method: OpenCV matching method

        Returns:
            ValidationResult with match information
        """
        # Convert to grayscale
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        # Perform template matching
        result = cv2.matchTemplate(screenshot_gray, template_gray, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # For SQDIFF methods, lower is better
        if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            confidence = 1 - min_val
            location = min_loc
        else:
            confidence = max_val
            location = max_loc

        success = confidence >= self.threshold

        bbox = BoundingBox(
            x=location[0],
            y=location[1],
            width=template.shape[1],
            height=template.shape[0]
        ) if success else None

        return ValidationResult(
            method=ValidationMethod.TEMPLATE_MATCHING,
            success=success,
            confidence=float(confidence),
            bbox=bbox,
            metadata={'match_score': float(confidence)}
        )

    def multi_scale_validate(
        self,
        screenshot: np.ndarray,
        template: np.ndarray,
        scales: Optional[List[float]] = None
    ) -> ValidationResult:
        """
        Template matching with scale invariance

        Args:
            screenshot: Full screenshot
            template: Template to find
            scales: List of scale factors to try

        Returns:
            Best matching result across all scales
        """
        if scales is None:
            scales = np.linspace(0.5, 1.5, 20)

        best_result = None
        best_confidence = 0

        for scale in scales:
            # Resize template
            width = int(template.shape[1] * scale)
            height = int(template.shape[0] * scale)

            if width <= 0 or height <= 0:
                continue

            resized_template = cv2.resize(template, (width, height))

            # Skip if template is larger than screenshot
            if (resized_template.shape[0] > screenshot.shape[0] or
                resized_template.shape[1] > screenshot.shape[1]):
                continue

            # Validate
            result = self.validate(screenshot, resized_template)

            if result.confidence > best_confidence:
                best_confidence = result.confidence
                best_result = result
                if best_result.bbox:
                    best_result.metadata['scale'] = scale

        return best_result or ValidationResult(
            method=ValidationMethod.TEMPLATE_MATCHING,
            success=False,
            confidence=0.0
        )


# =============================================================================
# Feature Matching Validator
# =============================================================================

class FeatureMatchingValidator:
    """Validate using feature detection and matching"""

    def __init__(self, min_matches: int = 10, threshold: float = 0.7):
        self.min_matches = min_matches
        self.threshold = threshold
        self.detector = cv2.ORB_create(nfeatures=2000)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

    def validate(
        self,
        screenshot: np.ndarray,
        template: np.ndarray
    ) -> ValidationResult:
        """
        Validate using ORB feature matching

        Args:
            screenshot: Full screenshot
            template: Template to find

        Returns:
            ValidationResult with match information
        """
        # Convert to grayscale
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        # Detect keypoints and descriptors
        kp1, des1 = self.detector.detectAndCompute(screenshot_gray, None)
        kp2, des2 = self.detector.detectAndCompute(template_gray, None)

        if des1 is None or des2 is None:
            return ValidationResult(
                method=ValidationMethod.FEATURE_MATCHING,
                success=False,
                confidence=0.0,
                metadata={'error': 'No features detected'}
            )

        # Match features
        matches = self.matcher.match(des1, des2)
        matches = sorted(matches, key=lambda x: x.distance)

        # Calculate confidence based on number of good matches
        num_good_matches = len([m for m in matches if m.distance < 50])
        confidence = min(num_good_matches / self.min_matches, 1.0)

        success = num_good_matches >= self.min_matches and confidence >= self.threshold

        bbox = None
        if success and len(matches) >= 4:
            # Extract matched keypoints
            src_pts = np.float32([kp1[m.queryIdx].pt for m in matches[:self.min_matches]])
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches[:self.min_matches]])

            # Find bounding box from matched points
            x_min, y_min = src_pts.min(axis=0)
            x_max, y_max = src_pts.max(axis=0)

            bbox = BoundingBox(
                x=int(x_min),
                y=int(y_min),
                width=int(x_max - x_min),
                height=int(y_max - y_min)
            )

        return ValidationResult(
            method=ValidationMethod.FEATURE_MATCHING,
            success=success,
            confidence=confidence,
            bbox=bbox,
            metadata={
                'num_matches': len(matches),
                'num_good_matches': num_good_matches
            }
        )


# =============================================================================
# OCR Validator
# =============================================================================

class OCRValidator:
    """Validate coordinates using OCR"""

    def __init__(self, confidence_threshold: float = 0.6):
        self.confidence_threshold = confidence_threshold

    def validate_text_at_location(
        self,
        screenshot: np.ndarray,
        expected_text: str,
        bbox: Optional[BoundingBox] = None
    ) -> ValidationResult:
        """
        Validate that expected text exists at location

        Args:
            screenshot: Screenshot (or region)
            expected_text: Text that should be present
            bbox: Optional bounding box to search within

        Returns:
            ValidationResult indicating if text was found
        """
        # Extract region if bbox provided
        if bbox:
            region = screenshot[bbox.y:bbox.y2, bbox.x:bbox.x2]
        else:
            region = screenshot

        # Preprocess for better OCR
        preprocessed = self._preprocess_for_ocr(region)

        # Perform OCR
        ocr_data = pytesseract.image_to_data(
            preprocessed,
            output_type=pytesseract.Output.DICT
        )

        # Find matching text
        found_text = ""
        best_confidence = 0.0
        found_bbox = None

        for i, text in enumerate(ocr_data['text']):
            if text.strip():
                conf = float(ocr_data['conf'][i]) / 100.0

                # Check if text matches
                if expected_text.lower() in text.lower():
                    if conf > best_confidence:
                        best_confidence = conf
                        found_text = text

                        # Get bounding box
                        x = ocr_data['left'][i]
                        y = ocr_data['top'][i]
                        w = ocr_data['width'][i]
                        h = ocr_data['height'][i]

                        # Adjust if we searched in a sub-region
                        if bbox:
                            x += bbox.x
                            y += bbox.y

                        found_bbox = BoundingBox(x=x, y=y, width=w, height=h)

        success = (expected_text.lower() in found_text.lower() and
                  best_confidence >= self.confidence_threshold)

        return ValidationResult(
            method=ValidationMethod.OCR,
            success=success,
            confidence=best_confidence,
            bbox=found_bbox,
            metadata={
                'expected_text': expected_text,
                'found_text': found_text
            }
        )

    def extract_all_text(
        self,
        screenshot: np.ndarray
    ) -> List[Dict]:
        """
        Extract all text elements from screenshot

        Returns:
            List of text elements with bounding boxes
        """
        preprocessed = self._preprocess_for_ocr(screenshot)

        ocr_data = pytesseract.image_to_data(
            preprocessed,
            output_type=pytesseract.Output.DICT
        )

        text_elements = []
        for i, text in enumerate(ocr_data['text']):
            if text.strip() and float(ocr_data['conf'][i]) > 0:
                text_elements.append({
                    'text': text,
                    'confidence': float(ocr_data['conf'][i]) / 100.0,
                    'bbox': BoundingBox(
                        x=ocr_data['left'][i],
                        y=ocr_data['top'][i],
                        width=ocr_data['width'][i],
                        height=ocr_data['height'][i]
                    )
                })

        return text_elements

    @staticmethod
    def _preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR accuracy"""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray)

        # Increase contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrasted = clahe.apply(denoised)

        # Threshold
        _, binary = cv2.threshold(
            contrasted, 0, 255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        return binary


# =============================================================================
# Color Profile Validator
# =============================================================================

class ColorProfileValidator:
    """Validate element presence by color signature"""

    def __init__(self, tolerance: float = 0.1):
        self.tolerance = tolerance

    def validate(
        self,
        screenshot: np.ndarray,
        expected_color: Tuple[int, int, int],
        bbox: BoundingBox
    ) -> ValidationResult:
        """
        Validate that region contains expected color

        Args:
            screenshot: Full screenshot
            expected_color: RGB color tuple
            bbox: Region to check

        Returns:
            ValidationResult based on color match
        """
        # Extract region
        region = screenshot[bbox.y:bbox.y2, bbox.x:bbox.x2]

        # Calculate average color
        avg_color = region.mean(axis=(0, 1))

        # Convert BGR to RGB
        avg_color_rgb = avg_color[[2, 1, 0]]

        # Calculate color distance
        distance = np.linalg.norm(avg_color_rgb - np.array(expected_color))
        max_distance = np.linalg.norm([255, 255, 255])

        # Calculate confidence (inverse of normalized distance)
        confidence = 1.0 - (distance / max_distance)

        success = confidence >= (1.0 - self.tolerance)

        return ValidationResult(
            method=ValidationMethod.COLOR_PROFILE,
            success=success,
            confidence=confidence,
            bbox=bbox,
            metadata={
                'expected_color': expected_color,
                'found_color': avg_color_rgb.tolist(),
                'distance': float(distance)
            }
        )


# =============================================================================
# Edge Detection Validator
# =============================================================================

class EdgeDetectionValidator:
    """Validate UI elements using edge detection"""

    def detect_elements(
        self,
        screenshot: np.ndarray,
        min_area: int = 100
    ) -> List[BoundingBox]:
        """
        Detect UI elements using edge detection

        Args:
            screenshot: Screenshot to analyze
            min_area: Minimum area for detected elements

        Returns:
            List of detected element bounding boxes
        """
        # Convert to grayscale
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

        # Blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Edge detection
        edges = cv2.Canny(blurred, 50, 150)

        # Find contours
        contours, _ = cv2.findContours(
            edges,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Extract bounding boxes
        elements = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= min_area:
                x, y, w, h = cv2.boundingRect(contour)
                elements.append(BoundingBox(x=x, y=y, width=w, height=h))

        return elements

    def validate_element_at_location(
        self,
        screenshot: np.ndarray,
        expected_bbox: BoundingBox,
        tolerance: int = 10
    ) -> ValidationResult:
        """
        Validate that an element exists at expected location

        Args:
            screenshot: Screenshot to analyze
            expected_bbox: Expected element location
            tolerance: Pixel tolerance for position matching

        Returns:
            ValidationResult based on edge detection
        """
        detected_elements = self.detect_elements(screenshot)

        # Find closest match
        best_match = None
        min_distance = float('inf')

        for element in detected_elements:
            # Calculate center distance
            expected_center = (
                expected_bbox.x + expected_bbox.width // 2,
                expected_bbox.y + expected_bbox.height // 2
            )
            element_center = (
                element.x + element.width // 2,
                element.y + element.height // 2
            )

            distance = np.sqrt(
                (expected_center[0] - element_center[0]) ** 2 +
                (expected_center[1] - element_center[1]) ** 2
            )

            if distance < min_distance:
                min_distance = distance
                best_match = element

        success = best_match is not None and min_distance <= tolerance
        confidence = 1.0 - (min_distance / (tolerance * 2)) if best_match else 0.0
        confidence = max(0.0, min(1.0, confidence))

        return ValidationResult(
            method=ValidationMethod.EDGE_DETECTION,
            success=success,
            confidence=confidence,
            bbox=best_match,
            metadata={
                'distance_from_expected': float(min_distance),
                'num_detected_elements': len(detected_elements)
            }
        )


# =============================================================================
# Hybrid Validator
# =============================================================================

class HybridCoordinateValidator:
    """
    Combines multiple validation methods for robust verification
    """

    def __init__(self):
        self.template_validator = TemplateMatchingValidator()
        self.feature_validator = FeatureMatchingValidator()
        self.ocr_validator = OCRValidator()
        self.color_validator = ColorProfileValidator()
        self.edge_validator = EdgeDetectionValidator()

    def validate(
        self,
        screenshot: np.ndarray,
        validation_config: Dict
    ) -> Dict[str, ValidationResult]:
        """
        Run multiple validation methods

        Args:
            screenshot: Screenshot to validate
            validation_config: Configuration for validation
                {
                    'template': np.ndarray,  # Optional template image
                    'expected_text': str,    # Optional expected text
                    'expected_color': tuple, # Optional RGB color
                    'bbox': BoundingBox,     # Optional bounding box
                    'methods': List[str]     # Methods to use
                }

        Returns:
            Dictionary of validation results by method
        """
        results = {}
        methods = validation_config.get('methods', [])

        # Template matching
        if 'template_matching' in methods and 'template' in validation_config:
            results['template_matching'] = \
                self.template_validator.multi_scale_validate(
                    screenshot,
                    validation_config['template']
                )

        # Feature matching
        if 'feature_matching' in methods and 'template' in validation_config:
            results['feature_matching'] = \
                self.feature_validator.validate(
                    screenshot,
                    validation_config['template']
                )

        # OCR
        if 'ocr' in methods and 'expected_text' in validation_config:
            results['ocr'] = self.ocr_validator.validate_text_at_location(
                screenshot,
                validation_config['expected_text'],
                validation_config.get('bbox')
            )

        # Color profile
        if 'color_profile' in methods and 'expected_color' in validation_config:
            if 'bbox' in validation_config:
                results['color_profile'] = self.color_validator.validate(
                    screenshot,
                    validation_config['expected_color'],
                    validation_config['bbox']
                )

        # Edge detection
        if 'edge_detection' in methods and 'bbox' in validation_config:
            results['edge_detection'] = \
                self.edge_validator.validate_element_at_location(
                    screenshot,
                    validation_config['bbox']
                )

        return results

    def get_overall_confidence(
        self,
        results: Dict[str, ValidationResult],
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate weighted overall confidence

        Args:
            results: Validation results from different methods
            weights: Optional custom weights for each method

        Returns:
            Overall confidence score (0.0 to 1.0)
        """
        if not results:
            return 0.0

        # Default weights
        if weights is None:
            weights = {
                'template_matching': 0.3,
                'feature_matching': 0.25,
                'ocr': 0.25,
                'color_profile': 0.1,
                'edge_detection': 0.1
            }

        total_confidence = 0.0
        total_weight = 0.0

        for method, result in results.items():
            weight = weights.get(method, 0.0)
            total_confidence += result.confidence * weight
            total_weight += weight

        return total_confidence / total_weight if total_weight > 0 else 0.0


# =============================================================================
# Coordinate Transformer
# =============================================================================

class CoordinateTransformer:
    """
    Transform coordinates between different coordinate systems
    """

    def __init__(self):
        self.screen_scale = 1.0  # Display scaling factor
        self.browser_chrome_height = 0  # Browser chrome height

    def os_to_browser(
        self,
        os_x: int,
        os_y: int,
        browser_window_pos: Tuple[int, int]
    ) -> Tuple[int, int]:
        """
        Convert OS coordinates to browser viewport coordinates

        Args:
            os_x, os_y: OS screen coordinates
            browser_window_pos: Browser window position (x, y)

        Returns:
            Browser viewport coordinates (x, y)
        """
        browser_x = os_x - browser_window_pos[0]
        browser_y = os_y - browser_window_pos[1] - self.browser_chrome_height

        return (browser_x, browser_y)

    def browser_to_dom(
        self,
        browser_x: int,
        browser_y: int,
        scroll_position: Tuple[int, int]
    ) -> Tuple[int, int]:
        """
        Convert browser viewport coordinates to DOM coordinates

        Args:
            browser_x, browser_y: Browser viewport coordinates
            scroll_position: Current scroll position (scroll_x, scroll_y)

        Returns:
            DOM coordinates (x, y)
        """
        dom_x = browser_x + scroll_position[0]
        dom_y = browser_y + scroll_position[1]

        return (dom_x, dom_y)

    def validate_transformation(
        self,
        os_coords: BoundingBox,
        dom_element_screenshot: np.ndarray,
        validator: HybridCoordinateValidator
    ) -> ValidationResult:
        """
        Validate coordinate transformation using visual comparison

        Args:
            os_coords: OS coordinates of element
            dom_element_screenshot: Screenshot of DOM element
            validator: HybridCoordinateValidator instance

        Returns:
            ValidationResult indicating transformation accuracy
        """
        # Capture OS coordinate region
        os_screenshot = ScreenCapture.capture_region(os_coords)

        # Compare using template matching
        result = validator.template_validator.validate(
            os_screenshot,
            dom_element_screenshot
        )

        return result


# =============================================================================
# Usage Example
# =============================================================================

def example_usage():
    """Example of how to use the validation system"""

    # Initialize validator
    validator = HybridCoordinateValidator()

    # Capture screenshot
    bbox = BoundingBox(x=100, y=200, width=300, height=100)
    screenshot = ScreenCapture.capture_region(bbox)

    # Configuration for validation
    validation_config = {
        'expected_text': 'Submit',
        'bbox': BoundingBox(x=100, y=200, width=100, height=40),
        'methods': ['ocr', 'edge_detection']
    }

    # Run validation
    results = validator.validate(screenshot, validation_config)

    # Get overall confidence
    confidence = validator.get_overall_confidence(results)

    print(f"Overall confidence: {confidence:.2%}")

    for method, result in results.items():
        print(f"\n{method}:")
        print(f"  Success: {result.success}")
        print(f"  Confidence: {result.confidence:.2%}")
        if result.bbox:
            print(f"  BBox: {result.bbox.to_dict()}")
        if result.metadata:
            print(f"  Metadata: {result.metadata}")


if __name__ == "__main__":
    example_usage()
