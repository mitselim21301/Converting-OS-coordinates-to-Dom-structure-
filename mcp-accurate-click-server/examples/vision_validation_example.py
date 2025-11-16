"""
Vision Validation System - Comprehensive Examples

This file demonstrates all features of the vision validation system
with practical examples.
"""

import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_1_check_dependencies():
    """Example 1: Check which dependencies are available."""
    print("\n" + "=" * 60)
    print("Example 1: Check Dependencies")
    print("=" * 60)

    from mcp_server.vision import check_dependencies, print_status

    # Print full status
    print_status()

    # Check specific dependencies
    deps = check_dependencies()

    if deps['opencv']:
        print("\n✓ OpenCV is available - Full vision validation enabled")
    else:
        print("\n✗ OpenCV not available - Install: pip install opencv-python")

    if deps['tesseract'] or deps['easyocr']:
        print("✓ OCR is available")
    else:
        print("✗ OCR not available - Install pytesseract or easyocr")


def example_2_template_matching():
    """Example 2: Template matching validation."""
    print("\n" + "=" * 60)
    print("Example 2: Template Matching")
    print("=" * 60)

    from mcp_server.vision import (
        TemplateMatchingValidator,
        BoundingBox,
        capture_screen,
        load_image
    )

    try:
        # Capture screenshot
        print("Capturing screenshot...")
        screenshot = capture_screen()
        print(f"Screenshot size: {screenshot.shape}")

        # Initialize validator
        validator = TemplateMatchingValidator(threshold=0.8)

        # For this example, we'll create a small template from the screenshot
        # In practice, you'd load a pre-saved template
        template_bbox = BoundingBox(x=100, y=100, width=50, height=50)
        template = screenshot[
            template_bbox.y:template_bbox.y2,
            template_bbox.x:template_bbox.x2
        ]

        # Validate with multi-scale matching
        print("\nPerforming multi-scale template matching...")
        result = validator.multi_scale_validate(screenshot, template)

        print(f"\nResult:")
        print(f"  Success: {result.success}")
        print(f"  Confidence: {result.confidence:.2%}")
        if result.bbox:
            print(f"  Found at: {result.bbox.to_dict()}")
        if result.metadata:
            print(f"  Metadata: {result.metadata}")

    except Exception as e:
        print(f"Template matching example failed: {e}")
        print("This is normal if OpenCV is not installed.")


def example_3_ocr_validation():
    """Example 3: OCR text validation."""
    print("\n" + "=" * 60)
    print("Example 3: OCR Text Validation")
    print("=" * 60)

    from mcp_server.vision import (
        OCRValidator,
        BoundingBox,
        capture_screen
    )

    try:
        # Initialize OCR validator
        validator = OCRValidator(confidence_threshold=0.6)

        # Capture screen
        print("Capturing screenshot...")
        screenshot = capture_screen()

        # Extract all text from screenshot
        print("\nExtracting all text from screenshot...")
        text_elements = validator.extract_all_text(screenshot)

        print(f"Found {len(text_elements)} text elements:")
        for i, elem in enumerate(text_elements[:5]):  # Show first 5
            print(f"  {i+1}. '{elem.text}' at {elem.bbox.to_dict()} "
                  f"({elem.confidence:.2%})")

        # Validate specific text
        if text_elements:
            first_text = text_elements[0]
            print(f"\nValidating text '{first_text.text}'...")

            result = validator.validate_text_at_location(
                screenshot,
                expected_text=first_text.text,
                bbox=first_text.bbox
            )

            print(f"  Success: {result.success}")
            print(f"  Confidence: {result.confidence:.2%}")

    except Exception as e:
        print(f"OCR example failed: {e}")
        print("Install pytesseract or easyocr for OCR functionality.")


def example_4_edge_detection():
    """Example 4: Edge detection validation."""
    print("\n" + "=" * 60)
    print("Example 4: Edge Detection")
    print("=" * 60)

    from mcp_server.vision import (
        EdgeDetectionValidator,
        BoundingBox,
        capture_screen
    )

    try:
        # Capture screenshot
        print("Capturing screenshot...")
        screenshot = capture_screen()

        # Initialize validator
        validator = EdgeDetectionValidator()

        # Detect all elements
        print("\nDetecting UI elements via edges...")
        elements = validator.detect_elements(screenshot, min_area=500)

        print(f"Found {len(elements)} UI elements:")
        for i, bbox in enumerate(elements[:10]):  # Show first 10
            print(f"  {i+1}. {bbox.to_dict()} (area: {bbox.area})")

        # Validate specific location
        if elements:
            test_bbox = elements[0]
            print(f"\nValidating element at {test_bbox.to_dict()}...")

            result = validator.validate_element_at_location(
                screenshot,
                expected_bbox=test_bbox,
                tolerance=20
            )

            print(f"  Success: {result.success}")
            print(f"  Confidence: {result.confidence:.2%}")
            print(f"  Distance: {result.metadata.get('distance_from_expected', 0):.1f}px")

    except Exception as e:
        print(f"Edge detection example failed: {e}")
        print("OpenCV required for edge detection.")


def example_5_hybrid_validation():
    """Example 5: Hybrid multi-method validation."""
    print("\n" + "=" * 60)
    print("Example 5: Hybrid Validation")
    print("=" * 60)

    from mcp_server.vision import (
        HybridValidator,
        ValidationConfig,
        BoundingBox,
        ConfidenceWeights
    )

    try:
        # Create validator with custom weights
        weights = ConfidenceWeights(
            template_matching=0.3,
            feature_matching=0.2,
            ocr=0.3,
            edge_detection=0.2
        )

        validator = HybridValidator(weights=weights)

        # Configure validation
        config = ValidationConfig(
            methods=['edge_detection'],  # Start with edge detection only
            confidence_threshold=0.7,
            bbox=BoundingBox(x=100, y=100, width=200, height=50)
        )

        # Capture region
        print("Capturing and validating region...")
        result = validator.validate(config.bbox, config)

        print(f"\nHybrid Validation Results:")
        print(f"  Overall confidence: {result.overall_confidence:.2%}")
        print(f"  Success rate: {result.success_rate:.2%}")
        print(f"  All successful: {result.all_successful}")
        print(f"  Any successful: {result.any_successful}")
        print(f"  Recommendation: {result.recommendation}")

        print(f"\nIndividual Method Results:")
        for method, method_result in result.results.items():
            status = "✓" if method_result.success else "✗"
            print(f"  {status} {method}: {method_result.confidence:.2%}")
            if method_result.error:
                print(f"    Error: {method_result.error}")

        # Export to JSON
        json_output = result.to_json()
        print(f"\nJSON Output (first 500 chars):")
        print(json_output[:500] + "...")

    except Exception as e:
        print(f"Hybrid validation example failed: {e}")


def example_6_dom_vision_validation():
    """Example 6: DOM + Vision validation."""
    print("\n" + "=" * 60)
    print("Example 6: DOM + Vision Validation")
    print("=" * 60)

    from mcp_server.vision import (
        DOMVisionValidator,
        BoundingBox
    )

    try:
        # Create DOM+Vision validator
        validator = DOMVisionValidator()

        # Simulate DOM bounding box
        dom_bbox = BoundingBox(x=150, y=200, width=200, height=50)

        print(f"Validating DOM coordinates: {dom_bbox.to_dict()}")

        # Validate with expected properties
        result = validator.validate_dom_coordinates(
            dom_bbox=dom_bbox,
            expected_properties={
                # 'text': 'Submit',  # Uncomment if you know expected text
                # 'color': (0, 120, 215)  # Uncomment if you know expected color
            }
        )

        print(f"\nDOM Validation Results:")
        print(f"  Overall confidence: {result.overall_confidence:.2%}")
        print(f"  Recommendation: {result.recommendation}")

        # Validate coordinate transformation
        os_bbox = BoundingBox(x=200, y=250, width=200, height=50)

        print(f"\nValidating coordinate transformation...")
        print(f"  OS bbox: {os_bbox.to_dict()}")
        print(f"  DOM bbox: {dom_bbox.to_dict()}")

        transform_result = validator.validate_coordinate_transformation(
            os_bbox=os_bbox,
            dom_bbox=dom_bbox,
            tolerance=0.90
        )

        print(f"\nTransformation Validation:")
        print(f"  Valid: {transform_result.success}")
        print(f"  Similarity: {transform_result.confidence:.2%}")

    except Exception as e:
        print(f"DOM+Vision validation example failed: {e}")


def example_7_click_validation():
    """Example 7: Pre-click validation."""
    print("\n" + "=" * 60)
    print("Example 7: Pre-Click Validation")
    print("=" * 60)

    from mcp_server.vision import ClickValidator

    try:
        # Create click validator
        validator = ClickValidator()

        # Define click target
        click_coords = (300, 400)
        expected_element = {
            'type': 'button',
            # 'text': 'Click Me',  # Uncomment if button has text
            'width': 150,
            'height': 50
        }

        print(f"Validating click at {click_coords}...")
        print(f"Expected element: {expected_element}")

        # Pre-click validation
        result = validator.pre_click_validate(
            click_coords=click_coords,
            expected_element=expected_element
        )

        print(f"\nPre-Click Validation:")
        print(f"  Overall confidence: {result.overall_confidence:.2%}")
        print(f"  Recommendation: {result.recommendation}")

        if result.overall_confidence >= 0.7:
            print("\n✓ Safe to click!")
            # Perform actual click here
            # pyautogui.click(click_coords)
        else:
            print("\n✗ Not safe to click - validation failed")

    except Exception as e:
        print(f"Click validation example failed: {e}")


def example_8_color_validation():
    """Example 8: Color profile validation."""
    print("\n" + "=" * 60)
    print("Example 8: Color Profile Validation")
    print("=" * 60)

    from mcp_server.vision import (
        ColorProfileValidator,
        BoundingBox,
        capture_screen
    )

    try:
        # Capture screenshot
        screenshot = capture_screen()

        # Create validator
        validator = ColorProfileValidator(tolerance=0.15)

        # Define region and expected color
        bbox = BoundingBox(x=100, y=100, width=50, height=50)
        expected_color = (255, 255, 255)  # White

        print(f"Validating color at {bbox.to_dict()}...")
        print(f"Expected color (RGB): {expected_color}")

        result = validator.validate(
            screenshot,
            expected_color=expected_color,
            bbox=bbox
        )

        print(f"\nColor Validation:")
        print(f"  Success: {result.success}")
        print(f"  Confidence: {result.confidence:.2%}")
        if result.metadata:
            print(f"  Found color (RGB): {result.metadata.get('found_color')}")
            print(f"  Color distance: {result.metadata.get('distance', 0):.2f}")

    except Exception as e:
        print(f"Color validation example failed: {e}")


def example_9_save_load_screenshots():
    """Example 9: Screenshot capture and saving."""
    print("\n" + "=" * 60)
    print("Example 9: Screenshot Utilities")
    print("=" * 60)

    from mcp_server.vision import (
        capture_screen,
        capture_region,
        save_screenshot,
        load_image,
        BoundingBox
    )
    import tempfile

    try:
        # Capture full screen
        print("Capturing full screen...")
        screenshot = capture_screen()
        print(f"Screenshot shape: {screenshot.shape}")

        # Capture specific region
        bbox = BoundingBox(x=100, y=100, width=300, height=200)
        print(f"\nCapturing region: {bbox.to_dict()}...")
        region = capture_region(bbox)
        print(f"Region shape: {region.shape}")

        # Save screenshot
        temp_dir = Path(tempfile.gettempdir())
        screenshot_path = temp_dir / "vision_test_screenshot.png"

        print(f"\nSaving screenshot to: {screenshot_path}")
        save_screenshot(region, screenshot_path)

        # Load it back
        print("Loading screenshot...")
        loaded = load_image(screenshot_path)
        print(f"Loaded shape: {loaded.shape}")

        print("\n✓ Screenshot utilities working correctly")

        # Cleanup
        if screenshot_path.exists():
            screenshot_path.unlink()

    except Exception as e:
        print(f"Screenshot utilities example failed: {e}")


def run_all_examples():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("VISION VALIDATION SYSTEM - COMPREHENSIVE EXAMPLES")
    print("=" * 60)

    examples = [
        example_1_check_dependencies,
        example_2_template_matching,
        example_3_ocr_validation,
        example_4_edge_detection,
        example_5_hybrid_validation,
        example_6_dom_vision_validation,
        example_7_click_validation,
        example_8_color_validation,
        example_9_save_load_screenshots,
    ]

    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            logger.error(f"Example {example_func.__name__} failed: {e}")

    print("\n" + "=" * 60)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    run_all_examples()
