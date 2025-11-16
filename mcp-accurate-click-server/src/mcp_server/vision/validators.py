"""
Vision-based validation methods.

This module provides template matching, OCR, edge detection, and color profile
validators with graceful dependency handling.
"""

import logging
from typing import List, Optional, Tuple, Union
import numpy as np
from pathlib import Path

from .models import (
    BoundingBox, ValidationResult, ValidationMethod,
    OCRTextElement, TemplateMatch
)
from .screenshot import ScreenCapture, CV2_AVAILABLE, PIL_AVAILABLE

logger = logging.getLogger(__name__)

# Optional OCR dependencies
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    pytesseract = None
    logger.warning("pytesseract not available. OCR validation disabled.")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    easyocr = None
    logger.info("EasyOCR not available. Using Tesseract if available.")

# OpenCV required for most validators
if not CV2_AVAILABLE:
    logger.warning("OpenCV not available. Many vision validators will be disabled.")
    cv2 = None  # Placeholder to prevent undefined errors


class TemplateMatchingValidator:
    """
    Validate coordinates using template matching.

    Requires OpenCV (cv2).
    """

    def __init__(self, threshold: float = 0.8):
        """
        Initialize template matching validator.

        Args:
            threshold: Confidence threshold for successful match (0.0 to 1.0)
        """
        self.threshold = threshold
        self.screen_capture = ScreenCapture()

        if not CV2_AVAILABLE:
            logger.error("OpenCV required for template matching")

    def validate(
        self,
        screenshot: np.ndarray,
        template: np.ndarray,
        method: int = None
    ) -> ValidationResult:
        """
        Validate using template matching.

        Args:
            screenshot: Full screenshot (BGR)
            template: Template image to find (BGR)
            method: OpenCV matching method (default: TM_CCOEFF_NORMED)

        Returns:
            ValidationResult with match information
        """
        if not CV2_AVAILABLE:
            return ValidationResult(
                method=ValidationMethod.TEMPLATE_MATCHING,
                success=False,
                confidence=0.0,
                error="OpenCV not available"
            )

        try:
            if method is None:
                method = cv2.TM_CCOEFF_NORMED

            # Convert to grayscale for better matching
            screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

            # Perform template matching
            result = cv2.matchTemplate(screenshot_gray, template_gray, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            # For SQDIFF methods, lower is better
            if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                confidence = 1.0 - min_val
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
                metadata={
                    'match_score': float(confidence),
                    'location': location,
                    'method': 'TM_CCOEFF_NORMED'
                }
            )

        except Exception as e:
            logger.error(f"Template matching failed: {e}")
            return ValidationResult(
                method=ValidationMethod.TEMPLATE_MATCHING,
                success=False,
                confidence=0.0,
                error=str(e)
            )

    def multi_scale_validate(
        self,
        screenshot: np.ndarray,
        template: np.ndarray,
        scales: Optional[List[float]] = None
    ) -> ValidationResult:
        """
        Template matching with scale invariance.

        Args:
            screenshot: Full screenshot
            template: Template to find
            scales: List of scale factors to try (default: 0.5 to 1.5)

        Returns:
            Best matching result across all scales
        """
        if not CV2_AVAILABLE:
            return ValidationResult(
                method=ValidationMethod.TEMPLATE_MATCHING,
                success=False,
                confidence=0.0,
                error="OpenCV not available"
            )

        if scales is None:
            scales = np.linspace(0.5, 1.5, 20).tolist()

        best_result = None
        best_confidence = 0.0

        for scale in scales:
            try:
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

            except Exception as e:
                logger.debug(f"Scale {scale} failed: {e}")
                continue

        if best_result is None:
            return ValidationResult(
                method=ValidationMethod.TEMPLATE_MATCHING,
                success=False,
                confidence=0.0,
                error="No matches found at any scale"
            )

        return best_result


class FeatureMatchingValidator:
    """
    Validate using feature detection and matching (ORB).

    Requires OpenCV (cv2).
    """

    def __init__(self, min_matches: int = 10, threshold: float = 0.7):
        """
        Initialize feature matching validator.

        Args:
            min_matches: Minimum number of good matches required
            threshold: Confidence threshold for success
        """
        self.min_matches = min_matches
        self.threshold = threshold

        if CV2_AVAILABLE:
            self.detector = cv2.ORB_create(nfeatures=2000)
            self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        else:
            logger.error("OpenCV required for feature matching")

    def validate(
        self,
        screenshot: np.ndarray,
        template: np.ndarray
    ) -> ValidationResult:
        """
        Validate using ORB feature matching.

        Args:
            screenshot: Full screenshot
            template: Template to find

        Returns:
            ValidationResult with match information
        """
        if not CV2_AVAILABLE:
            return ValidationResult(
                method=ValidationMethod.FEATURE_MATCHING,
                success=False,
                confidence=0.0,
                error="OpenCV not available"
            )

        try:
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
                    error="No features detected"
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
                src_pts = np.float32([
                    kp1[m.queryIdx].pt
                    for m in matches[:self.min_matches]
                ])

                # Calculate bounding box from matched points
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

        except Exception as e:
            logger.error(f"Feature matching failed: {e}")
            return ValidationResult(
                method=ValidationMethod.FEATURE_MATCHING,
                success=False,
                confidence=0.0,
                error=str(e)
            )


class OCRValidator:
    """
    Validate coordinates using OCR.

    Supports Tesseract and EasyOCR (graceful fallback).
    """

    def __init__(
        self,
        confidence_threshold: float = 0.6,
        engine: str = 'auto'
    ):
        """
        Initialize OCR validator.

        Args:
            confidence_threshold: Minimum OCR confidence for success
            engine: OCR engine ('auto', 'tesseract', 'easyocr')
        """
        self.confidence_threshold = confidence_threshold
        self.engine = self._select_engine(engine)
        self.easyocr_reader = None

    def _select_engine(self, engine: str) -> str:
        """Select best available OCR engine."""
        if engine == 'auto':
            if TESSERACT_AVAILABLE:
                return 'tesseract'
            elif EASYOCR_AVAILABLE:
                return 'easyocr'
            else:
                logger.error("No OCR engine available")
                return 'none'

        if engine == 'tesseract' and not TESSERACT_AVAILABLE:
            logger.warning("Tesseract requested but not available")
            return 'none'
        if engine == 'easyocr' and not EASYOCR_AVAILABLE:
            logger.warning("EasyOCR requested but not available")
            return 'none'

        return engine

    def validate_text_at_location(
        self,
        screenshot: np.ndarray,
        expected_text: str,
        bbox: Optional[BoundingBox] = None
    ) -> ValidationResult:
        """
        Validate that expected text exists at location.

        Args:
            screenshot: Screenshot (or region)
            expected_text: Text that should be present
            bbox: Optional bounding box to search within

        Returns:
            ValidationResult indicating if text was found
        """
        if self.engine == 'none':
            return ValidationResult(
                method=ValidationMethod.OCR,
                success=False,
                confidence=0.0,
                error="No OCR engine available"
            )

        try:
            # Extract region if bbox provided
            if bbox:
                region = screenshot[bbox.y:bbox.y2, bbox.x:bbox.x2]
            else:
                region = screenshot

            # Preprocess for better OCR
            preprocessed = self._preprocess_for_ocr(region)

            # Perform OCR based on engine
            if self.engine == 'tesseract':
                return self._validate_tesseract(
                    preprocessed, expected_text, bbox
                )
            elif self.engine == 'easyocr':
                return self._validate_easyocr(
                    preprocessed, expected_text, bbox
                )
            else:
                return ValidationResult(
                    method=ValidationMethod.OCR,
                    success=False,
                    confidence=0.0,
                    error=f"Unknown OCR engine: {self.engine}"
                )

        except Exception as e:
            logger.error(f"OCR validation failed: {e}")
            return ValidationResult(
                method=ValidationMethod.OCR,
                success=False,
                confidence=0.0,
                error=str(e)
            )

    def _validate_tesseract(
        self,
        image: np.ndarray,
        expected_text: str,
        bbox_offset: Optional[BoundingBox]
    ) -> ValidationResult:
        """Validate using Tesseract."""
        ocr_data = pytesseract.image_to_data(
            image,
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
                        if bbox_offset:
                            x += bbox_offset.x
                            y += bbox_offset.y

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
                'found_text': found_text,
                'engine': 'tesseract'
            }
        )

    def _validate_easyocr(
        self,
        image: np.ndarray,
        expected_text: str,
        bbox_offset: Optional[BoundingBox]
    ) -> ValidationResult:
        """Validate using EasyOCR."""
        if self.easyocr_reader is None:
            self.easyocr_reader = easyocr.Reader(['en'], gpu=False)

        results = self.easyocr_reader.readtext(image)

        best_confidence = 0.0
        found_text = ""
        found_bbox = None

        for bbox_points, text, confidence in results:
            if expected_text.lower() in text.lower():
                if confidence > best_confidence:
                    best_confidence = confidence
                    found_text = text

                    # Convert bbox points to BoundingBox
                    x_coords = [point[0] for point in bbox_points]
                    y_coords = [point[1] for point in bbox_points]

                    x = int(min(x_coords))
                    y = int(min(y_coords))
                    width = int(max(x_coords) - x)
                    height = int(max(y_coords) - y)

                    if bbox_offset:
                        x += bbox_offset.x
                        y += bbox_offset.y

                    found_bbox = BoundingBox(x=x, y=y, width=width, height=height)

        success = (expected_text.lower() in found_text.lower() and
                  best_confidence >= self.confidence_threshold)

        return ValidationResult(
            method=ValidationMethod.OCR,
            success=success,
            confidence=best_confidence,
            bbox=found_bbox,
            metadata={
                'expected_text': expected_text,
                'found_text': found_text,
                'engine': 'easyocr'
            }
        )

    def extract_all_text(
        self,
        screenshot: np.ndarray
    ) -> List[OCRTextElement]:
        """
        Extract all text elements from screenshot.

        Returns:
            List of OCRTextElement objects
        """
        if self.engine == 'none':
            return []

        try:
            preprocessed = self._preprocess_for_ocr(screenshot)

            if self.engine == 'tesseract':
                return self._extract_tesseract(preprocessed)
            elif self.engine == 'easyocr':
                return self._extract_easyocr(preprocessed)
            else:
                return []

        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return []

    def _extract_tesseract(self, image: np.ndarray) -> List[OCRTextElement]:
        """Extract text using Tesseract."""
        ocr_data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT
        )

        text_elements = []
        for i, text in enumerate(ocr_data['text']):
            if text.strip() and float(ocr_data['conf'][i]) > 0:
                text_elements.append(OCRTextElement(
                    text=text,
                    confidence=float(ocr_data['conf'][i]) / 100.0,
                    bbox=BoundingBox(
                        x=ocr_data['left'][i],
                        y=ocr_data['top'][i],
                        width=ocr_data['width'][i],
                        height=ocr_data['height'][i]
                    )
                ))

        return text_elements

    def _extract_easyocr(self, image: np.ndarray) -> List[OCRTextElement]:
        """Extract text using EasyOCR."""
        if self.easyocr_reader is None:
            self.easyocr_reader = easyocr.Reader(['en'], gpu=False)

        results = self.easyocr_reader.readtext(image)

        text_elements = []
        for bbox_points, text, confidence in results:
            x_coords = [point[0] for point in bbox_points]
            y_coords = [point[1] for point in bbox_points]

            text_elements.append(OCRTextElement(
                text=text,
                confidence=confidence,
                bbox=BoundingBox(
                    x=int(min(x_coords)),
                    y=int(min(y_coords)),
                    width=int(max(x_coords) - min(x_coords)),
                    height=int(max(y_coords) - min(y_coords))
                )
            ))

        return text_elements

    @staticmethod
    def _preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR accuracy."""
        if not CV2_AVAILABLE:
            return image

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


class EdgeDetectionValidator:
    """
    Validate UI elements using edge detection.

    Requires OpenCV (cv2).
    """

    def detect_elements(
        self,
        screenshot: np.ndarray,
        min_area: int = 100
    ) -> List[BoundingBox]:
        """
        Detect UI elements using edge detection.

        Args:
            screenshot: Screenshot to analyze
            min_area: Minimum area for detected elements

        Returns:
            List of detected element bounding boxes
        """
        if not CV2_AVAILABLE:
            logger.error("OpenCV required for edge detection")
            return []

        try:
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

        except Exception as e:
            logger.error(f"Edge detection failed: {e}")
            return []

    def validate_element_at_location(
        self,
        screenshot: np.ndarray,
        expected_bbox: BoundingBox,
        tolerance: int = 10
    ) -> ValidationResult:
        """
        Validate that an element exists at expected location.

        Args:
            screenshot: Screenshot to analyze
            expected_bbox: Expected element location
            tolerance: Pixel tolerance for position matching

        Returns:
            ValidationResult based on edge detection
        """
        if not CV2_AVAILABLE:
            return ValidationResult(
                method=ValidationMethod.EDGE_DETECTION,
                success=False,
                confidence=0.0,
                error="OpenCV not available"
            )

        try:
            detected_elements = self.detect_elements(screenshot)

            # Find closest match
            best_match = None
            min_distance = float('inf')

            expected_center = expected_bbox.center

            for element in detected_elements:
                element_center = element.center
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
                    'num_detected_elements': len(detected_elements),
                    'tolerance': tolerance
                }
            )

        except Exception as e:
            logger.error(f"Edge validation failed: {e}")
            return ValidationResult(
                method=ValidationMethod.EDGE_DETECTION,
                success=False,
                confidence=0.0,
                error=str(e)
            )


class ColorProfileValidator:
    """
    Validate element presence by color signature.

    Requires OpenCV or numpy.
    """

    def __init__(self, tolerance: float = 0.1):
        """
        Initialize color profile validator.

        Args:
            tolerance: Color distance tolerance (0.0 to 1.0)
        """
        self.tolerance = tolerance

    def validate(
        self,
        screenshot: np.ndarray,
        expected_color: Tuple[int, int, int],
        bbox: BoundingBox
    ) -> ValidationResult:
        """
        Validate that region contains expected color.

        Args:
            screenshot: Full screenshot (BGR)
            expected_color: RGB color tuple (0-255)
            bbox: Region to check

        Returns:
            ValidationResult based on color match
        """
        try:
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

        except Exception as e:
            logger.error(f"Color validation failed: {e}")
            return ValidationResult(
                method=ValidationMethod.COLOR_PROFILE,
                success=False,
                confidence=0.0,
                error=str(e)
            )
