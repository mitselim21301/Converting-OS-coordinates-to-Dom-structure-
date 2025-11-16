"""
Vision-based validation package.

Provides vision-based coordinate validation with graceful dependency handling.
Falls back gracefully when computer vision libraries are not installed.

Optional Dependencies:
    - opencv-python (cv2): Template matching, feature matching, edge detection
    - pytesseract or easyocr: OCR text validation
    - pillow (PIL): Image capture and manipulation
    - mss: Fast screenshot capture
    - numpy: Array operations

Example:
    Basic usage:

    >>> from mcp_server.vision import HybridValidator, ValidationConfig, BoundingBox
    >>>
    >>> # Create validator
    >>> validator = HybridValidator()
    >>>
    >>> # Capture and validate
    >>> bbox = BoundingBox(x=100, y=200, width=300, height=100)
    >>> config = ValidationConfig(
    ...     methods=['template_matching', 'ocr'],
    ...     expected_text='Submit',
    ...     template_path='button_template.png'
    ... )
    >>>
    >>> result = validator.validate(bbox, config)
    >>> print(f"Confidence: {result.overall_confidence:.2%}")
    >>> print(f"Success: {result.all_successful}")

    DOM + Vision validation:

    >>> from mcp_server.vision import DOMVisionValidator
    >>>
    >>> validator = DOMVisionValidator()
    >>> result = validator.validate_dom_coordinates(
    ...     dom_bbox=BoundingBox(x=100, y=200, width=150, height=40),
    ...     expected_properties={
    ...         'text': 'Click Me',
    ...         'color': (0, 120, 215)
    ...     }
    ... )
"""

import logging
import warnings

# Configure logging
logger = logging.getLogger(__name__)

# Version
__version__ = "1.0.0"

# Check for dependencies
_DEPENDENCIES_AVAILABLE = {
    'opencv': False,
    'pil': False,
    'tesseract': False,
    'easyocr': False,
    'mss': False,
    'numpy': True  # Required
}

try:
    import cv2
    _DEPENDENCIES_AVAILABLE['opencv'] = True
except ImportError:
    warnings.warn(
        "OpenCV (cv2) not installed. Template matching, feature matching, "
        "and edge detection will be unavailable. "
        "Install with: pip install opencv-python",
        ImportWarning
    )

try:
    from PIL import Image, ImageGrab
    _DEPENDENCIES_AVAILABLE['pil'] = True
except ImportError:
    warnings.warn(
        "Pillow (PIL) not installed. Screenshot capture will be limited. "
        "Install with: pip install Pillow",
        ImportWarning
    )

try:
    import pytesseract
    _DEPENDENCIES_AVAILABLE['tesseract'] = True
except ImportError:
    logger.info("pytesseract not installed. OCR validation will use EasyOCR if available.")

try:
    import easyocr
    _DEPENDENCIES_AVAILABLE['easyocr'] = True
except ImportError:
    logger.info("EasyOCR not installed. OCR validation will use Tesseract if available.")

try:
    import mss
    _DEPENDENCIES_AVAILABLE['mss'] = True
except ImportError:
    logger.info("mss not installed. Using PIL for screenshots (slower).")

# Core imports (always available)
from .models import (
    BoundingBox,
    ValidationResult,
    ValidationMethod,
    ValidationStatus,
    HybridValidationResult,
    ValidationConfig,
    ConfidenceWeights,
    OCRTextElement,
    TemplateMatch,
)

# Screenshot utilities
from .screenshot import (
    ScreenCapture,
    ScreenshotError,
    capture_region,
    capture_screen,
    save_screenshot,
    load_image,
)

# Validators (gracefully handle missing dependencies)
from .validators import (
    TemplateMatchingValidator,
    FeatureMatchingValidator,
    OCRValidator,
    EdgeDetectionValidator,
    ColorProfileValidator,
)

# Hybrid validation
from .hybrid import (
    HybridValidator,
    DOMVisionValidator,
    ClickValidator,
)

# Export all public APIs
__all__ = [
    # Version
    '__version__',

    # Dependency info
    'check_dependencies',
    'get_available_validators',

    # Models
    'BoundingBox',
    'ValidationResult',
    'ValidationMethod',
    'ValidationStatus',
    'HybridValidationResult',
    'ValidationConfig',
    'ConfidenceWeights',
    'OCRTextElement',
    'TemplateMatch',

    # Screenshot
    'ScreenCapture',
    'ScreenshotError',
    'capture_region',
    'capture_screen',
    'save_screenshot',
    'load_image',

    # Validators
    'TemplateMatchingValidator',
    'FeatureMatchingValidator',
    'OCRValidator',
    'EdgeDetectionValidator',
    'ColorProfileValidator',

    # Hybrid
    'HybridValidator',
    'DOMVisionValidator',
    'ClickValidator',
]


def check_dependencies() -> dict:
    """
    Check which optional dependencies are available.

    Returns:
        Dictionary of dependency availability status

    Example:
        >>> from mcp_server.vision import check_dependencies
        >>> deps = check_dependencies()
        >>> if deps['opencv']:
        ...     print("OpenCV is available")
        >>> if deps['tesseract'] or deps['easyocr']:
        ...     print("OCR is available")
    """
    return _DEPENDENCIES_AVAILABLE.copy()


def get_available_validators() -> list[str]:
    """
    Get list of available validation methods based on installed dependencies.

    Returns:
        List of available validator names

    Example:
        >>> from mcp_server.vision import get_available_validators
        >>> validators = get_available_validators()
        >>> print(f"Available: {', '.join(validators)}")
    """
    available = []

    if _DEPENDENCIES_AVAILABLE['opencv']:
        available.extend([
            'template_matching',
            'feature_matching',
            'edge_detection'
        ])

    if _DEPENDENCIES_AVAILABLE['tesseract'] or _DEPENDENCIES_AVAILABLE['easyocr']:
        available.append('ocr')

    # Color profile only needs numpy (always available)
    available.append('color_profile')

    return available


def print_status():
    """
    Print status of vision validation system.

    Useful for debugging dependency issues.
    """
    print("Vision Validation System Status")
    print("=" * 50)
    print(f"Version: {__version__}")
    print()

    print("Dependencies:")
    deps = check_dependencies()
    for name, available in deps.items():
        status = "✓ Available" if available else "✗ Not installed"
        print(f"  {name:15s}: {status}")

    print()
    print("Available Validators:")
    validators = get_available_validators()
    for validator in validators:
        print(f"  • {validator}")

    print()

    if not deps['opencv']:
        print("⚠ Warning: OpenCV not installed")
        print("  Template matching, feature matching, and edge detection unavailable")
        print("  Install with: pip install opencv-python")
        print()

    if not (deps['tesseract'] or deps['easyocr']):
        print("⚠ Warning: No OCR engine installed")
        print("  Text validation unavailable")
        print("  Install with: pip install pytesseract  (or)  pip install easyocr")
        print()

    if not deps['pil']:
        print("⚠ Warning: Pillow not installed")
        print("  Screenshot capture unavailable")
        print("  Install with: pip install Pillow")
        print()


# Provide helpful message if imported with missing dependencies
if not any([_DEPENDENCIES_AVAILABLE['opencv'],
            _DEPENDENCIES_AVAILABLE['pil'],
            _DEPENDENCIES_AVAILABLE['tesseract'],
            _DEPENDENCIES_AVAILABLE['easyocr']]):
    logger.warning(
        "Vision validation package imported but no optional dependencies found. "
        "Most validation methods will be unavailable. "
        "Install dependencies with: pip install opencv-python pillow pytesseract"
    )
