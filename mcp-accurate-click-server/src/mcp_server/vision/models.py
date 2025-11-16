"""
Vision validation data models.

This module provides data models for vision-based coordinate validation,
including validation results, bounding boxes, and confidence scores.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Any, List
import json


class ValidationMethod(Enum):
    """Available vision validation methods."""
    TEMPLATE_MATCHING = "template_matching"
    FEATURE_MATCHING = "feature_matching"
    OCR = "ocr"
    COLOR_PROFILE = "color_profile"
    EDGE_DETECTION = "edge_detection"
    AI_DETECTION = "ai_detection"
    HYBRID = "hybrid"


class ValidationStatus(Enum):
    """Validation result status."""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    ERROR = "error"


@dataclass
class BoundingBox:
    """
    Bounding box representation for UI elements.

    Attributes:
        x: Left coordinate
        y: Top coordinate
        width: Box width
        height: Box height
    """
    x: int
    y: int
    width: int
    height: int

    @property
    def x2(self) -> int:
        """Right coordinate."""
        return self.x + self.width

    @property
    def y2(self) -> int:
        """Bottom coordinate."""
        return self.y + self.height

    @property
    def center(self) -> tuple[int, int]:
        """Center point of bounding box."""
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def area(self) -> int:
        """Area of bounding box."""
        return self.width * self.height

    def contains_point(self, x: int, y: int) -> bool:
        """Check if point is within bounding box."""
        return self.x <= x <= self.x2 and self.y <= y <= self.y2

    def overlaps(self, other: 'BoundingBox') -> bool:
        """Check if this box overlaps with another."""
        return not (self.x2 < other.x or other.x2 < self.x or
                   self.y2 < other.y or other.y2 < self.y)

    def iou(self, other: 'BoundingBox') -> float:
        """
        Calculate Intersection over Union with another box.

        Returns:
            IoU score between 0.0 and 1.0
        """
        if not self.overlaps(other):
            return 0.0

        # Calculate intersection
        x_left = max(self.x, other.x)
        y_top = max(self.y, other.y)
        x_right = min(self.x2, other.x2)
        y_bottom = min(self.y2, other.y2)

        intersection = (x_right - x_left) * (y_bottom - y_top)
        union = self.area + other.area - intersection

        return intersection / union if union > 0 else 0.0

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height
        }

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'BoundingBox':
        """Create from dictionary."""
        return cls(
            x=data['x'],
            y=data['y'],
            width=data['width'],
            height=data['height']
        )


@dataclass
class ValidationResult:
    """
    Result of a vision validation check.

    Attributes:
        method: Validation method used
        success: Whether validation succeeded
        confidence: Confidence score (0.0 to 1.0)
        bbox: Detected bounding box (if any)
        metadata: Additional validation metadata
        error: Error message (if any)
    """
    method: ValidationMethod
    success: bool
    confidence: float
    bbox: Optional[BoundingBox] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def status(self) -> ValidationStatus:
        """Get validation status."""
        if self.error:
            return ValidationStatus.ERROR
        elif self.success:
            return ValidationStatus.SUCCESS
        elif 0.3 <= self.confidence < 0.7:
            return ValidationStatus.PARTIAL
        else:
            return ValidationStatus.FAILURE

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'method': self.method.value,
            'success': self.success,
            'confidence': self.confidence,
            'status': self.status.value,
            'bbox': self.bbox.to_dict() if self.bbox else None,
            'metadata': self.metadata,
            'error': self.error
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class HybridValidationResult:
    """
    Result from hybrid validation using multiple methods.

    Attributes:
        results: Dictionary of validation results by method
        overall_confidence: Weighted overall confidence score
        primary_bbox: Best bounding box from all methods
        recommendation: Recommended action based on results
    """
    results: Dict[str, ValidationResult]
    overall_confidence: float
    primary_bbox: Optional[BoundingBox] = None
    recommendation: str = ""

    @property
    def all_successful(self) -> bool:
        """Check if all validation methods succeeded."""
        return all(r.success for r in self.results.values())

    @property
    def any_successful(self) -> bool:
        """Check if any validation method succeeded."""
        return any(r.success for r in self.results.values())

    @property
    def success_rate(self) -> float:
        """Get percentage of successful validations."""
        if not self.results:
            return 0.0
        successful = sum(1 for r in self.results.values() if r.success)
        return successful / len(self.results)

    def get_best_result(self) -> Optional[ValidationResult]:
        """Get validation result with highest confidence."""
        if not self.results:
            return None
        return max(self.results.values(), key=lambda r: r.confidence)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'results': {
                method: result.to_dict()
                for method, result in self.results.items()
            },
            'overall_confidence': self.overall_confidence,
            'primary_bbox': self.primary_bbox.to_dict() if self.primary_bbox else None,
            'recommendation': self.recommendation,
            'all_successful': self.all_successful,
            'any_successful': self.any_successful,
            'success_rate': self.success_rate
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class OCRTextElement:
    """
    Text element detected via OCR.

    Attributes:
        text: Detected text content
        confidence: OCR confidence score
        bbox: Bounding box of text
        language: Detected language (if available)
    """
    text: str
    confidence: float
    bbox: BoundingBox
    language: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'text': self.text,
            'confidence': self.confidence,
            'bbox': self.bbox.to_dict(),
            'language': self.language
        }


@dataclass
class TemplateMatch:
    """
    Result from template matching.

    Attributes:
        bbox: Location where template was found
        confidence: Match confidence score
        scale: Scale factor used (for multi-scale matching)
        method: OpenCV matching method used
    """
    bbox: BoundingBox
    confidence: float
    scale: float = 1.0
    method: str = "TM_CCOEFF_NORMED"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'bbox': self.bbox.to_dict(),
            'confidence': self.confidence,
            'scale': self.scale,
            'method': self.method
        }


@dataclass
class ValidationConfig:
    """
    Configuration for vision validation.

    Attributes:
        methods: List of validation methods to use
        confidence_threshold: Minimum confidence for success
        template_path: Path to template image (for template matching)
        expected_text: Expected text content (for OCR)
        expected_color: Expected RGB color tuple (for color validation)
        bbox: Bounding box to validate
        use_grayscale: Convert images to grayscale
        scale_invariant: Use multi-scale matching
        rotation_invariant: Use rotation-invariant features
    """
    methods: List[str] = field(default_factory=lambda: ['template_matching'])
    confidence_threshold: float = 0.7
    template_path: Optional[str] = None
    expected_text: Optional[str] = None
    expected_color: Optional[tuple[int, int, int]] = None
    bbox: Optional[BoundingBox] = None
    use_grayscale: bool = True
    scale_invariant: bool = True
    rotation_invariant: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'methods': self.methods,
            'confidence_threshold': self.confidence_threshold,
            'template_path': self.template_path,
            'expected_text': self.expected_text,
            'expected_color': self.expected_color,
            'bbox': self.bbox.to_dict() if self.bbox else None,
            'use_grayscale': self.use_grayscale,
            'scale_invariant': self.scale_invariant,
            'rotation_invariant': self.rotation_invariant
        }


@dataclass
class ConfidenceWeights:
    """
    Weights for different validation methods in hybrid validation.

    Attributes:
        template_matching: Weight for template matching
        feature_matching: Weight for feature matching
        ocr: Weight for OCR validation
        color_profile: Weight for color validation
        edge_detection: Weight for edge detection
        ai_detection: Weight for AI detection
    """
    template_matching: float = 0.3
    feature_matching: float = 0.25
    ocr: float = 0.25
    color_profile: float = 0.1
    edge_detection: float = 0.1
    ai_detection: float = 0.2

    def normalize(self) -> 'ConfidenceWeights':
        """Normalize weights to sum to 1.0."""
        total = (self.template_matching + self.feature_matching +
                self.ocr + self.color_profile + self.edge_detection +
                self.ai_detection)

        if total == 0:
            return self

        return ConfidenceWeights(
            template_matching=self.template_matching / total,
            feature_matching=self.feature_matching / total,
            ocr=self.ocr / total,
            color_profile=self.color_profile / total,
            edge_detection=self.edge_detection / total,
            ai_detection=self.ai_detection / total
        )

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'template_matching': self.template_matching,
            'feature_matching': self.feature_matching,
            'ocr': self.ocr,
            'color_profile': self.color_profile,
            'edge_detection': self.edge_detection,
            'ai_detection': self.ai_detection
        }
