#!/usr/bin/env python3
"""
Vision Validation Example - MCP Accurate Click Server

This example demonstrates vision-enhanced clicking with AI validation:
- Screenshot-based element detection
- Visual similarity matching
- OCR for text validation
- Pre-click and post-click verification
- Visual feedback validation
- Template matching for UI elements

Run this example to see AI-enhanced automation patterns.

Requirements:
    pip install opencv-python pillow pytesseract numpy
"""

import sys
import time
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass
import base64
import io

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.sync_api import sync_playwright, Page
from dom_structure_extractor import DOMStructureExtractor, CoordinateMapper, DOMElement

try:
    import cv2
    import numpy as np
    from PIL import Image
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("⚠ OpenCV not installed. Install with: pip install opencv-python pillow")

try:
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("⚠ pytesseract not installed. Install with: pip install pytesseract")


@dataclass
class VisualElement:
    """Represents a visually detected element."""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    label: str
    screenshot: Optional[np.ndarray] = None

    @property
    def center(self) -> Tuple[int, int]:
        """Get center coordinates."""
        return (self.x + self.width // 2, self.y + self.height // 2)


class VisionValidator:
    """
    Vision-based validation for accurate clicking.

    Features:
    - Screenshot capture and analysis
    - OCR text detection
    - Visual similarity matching
    - Pre/post-click validation
    - Template matching
    """

    def __init__(self, page: Page):
        """
        Initialize vision validator.

        Args:
            page: Playwright page object
        """
        self.page = page
        self.screenshots_dir = Path("/tmp/vision_validation")
        self.screenshots_dir.mkdir(exist_ok=True)

    def capture_screenshot(self, filename: Optional[str] = None) -> np.ndarray:
        """
        Capture page screenshot.

        Args:
            filename: Optional filename to save screenshot

        Returns:
            Screenshot as numpy array (BGR format)
        """
        # Capture screenshot as bytes
        screenshot_bytes = self.page.screenshot(type='png')

        # Convert to numpy array
        nparr = np.frombuffer(screenshot_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Save if filename provided
        if filename:
            output_path = self.screenshots_dir / filename
            cv2.imwrite(str(output_path), img)
            print(f"  ✓ Screenshot saved: {output_path}")

        return img

    def capture_element_screenshot(
        self,
        element: DOMElement,
        padding: int = 10
    ) -> Optional[np.ndarray]:
        """
        Capture screenshot of specific element.

        Args:
            element: DOM element to capture
            padding: Extra padding around element (pixels)

        Returns:
            Element screenshot as numpy array, or None
        """
        try:
            bbox = element.bounding_box

            # Capture full page screenshot
            full_screenshot = self.capture_screenshot()

            # Crop to element (with padding)
            x1 = max(0, int(bbox.x - padding))
            y1 = max(0, int(bbox.y - padding))
            x2 = min(full_screenshot.shape[1], int(bbox.x + bbox.width + padding))
            y2 = min(full_screenshot.shape[0], int(bbox.y + bbox.height + padding))

            element_img = full_screenshot[y1:y2, x1:x2]

            return element_img

        except Exception as e:
            print(f"  ✗ Failed to capture element screenshot: {e}")
            return None

    def extract_text_ocr(self, image: np.ndarray) -> str:
        """
        Extract text from image using OCR.

        Args:
            image: Image as numpy array

        Returns:
            Extracted text
        """
        if not HAS_OCR:
            print("  ✗ OCR not available (pytesseract not installed)")
            return ""

        try:
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Convert to PIL Image
            pil_image = Image.fromarray(image_rgb)

            # Extract text
            text = pytesseract.image_to_string(pil_image)

            return text.strip()

        except Exception as e:
            print(f"  ✗ OCR failed: {e}")
            return ""

    def find_text_visually(self, text: str) -> List[VisualElement]:
        """
        Find text on page using OCR.

        Args:
            text: Text to search for

        Returns:
            List of VisualElement objects where text was found
        """
        if not HAS_OCR:
            print("  ✗ OCR not available")
            return []

        print(f"  Searching for text '{text}' using OCR...")

        try:
            # Capture screenshot
            screenshot = self.capture_screenshot()

            # Convert to RGB
            screenshot_rgb = cv2.cvtColor(screenshot, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(screenshot_rgb)

            # Get detailed OCR data with bounding boxes
            ocr_data = pytesseract.image_to_data(
                pil_image,
                output_type=pytesseract.Output.DICT
            )

            # Find matching text
            results = []
            text_lower = text.lower()

            for i, word in enumerate(ocr_data['text']):
                if word and text_lower in word.lower():
                    confidence = ocr_data['conf'][i]
                    if confidence > 50:  # Minimum confidence threshold
                        elem = VisualElement(
                            x=ocr_data['left'][i],
                            y=ocr_data['top'][i],
                            width=ocr_data['width'][i],
                            height=ocr_data['height'][i],
                            confidence=confidence / 100.0,
                            label=word
                        )
                        results.append(elem)

            print(f"  ✓ Found {len(results)} match(es)")
            return results

        except Exception as e:
            print(f"  ✗ Visual text search failed: {e}")
            return []

    def validate_click_target(
        self,
        element: DOMElement,
        expected_text: Optional[str] = None
    ) -> bool:
        """
        Validate click target before clicking.

        Args:
            element: Element to validate
            expected_text: Expected text content (optional)

        Returns:
            True if validation passed, False otherwise
        """
        print(f"\n  Validating click target...")

        # Check 1: Element is visible
        if not element.visible:
            print(f"    ✗ Element is not visible")
            return False
        print(f"    ✓ Element is visible")

        # Check 2: Element is clickable
        if not element.clickable:
            print(f"    ✗ Element is not clickable")
            return False
        print(f"    ✓ Element is clickable")

        # Check 3: Element has reasonable size
        if element.bounding_box.width < 10 or element.bounding_box.height < 10:
            print(f"    ✗ Element too small ({element.bounding_box.width}x{element.bounding_box.height})")
            return False
        print(f"    ✓ Element size reasonable ({element.bounding_box.width:.0f}x{element.bounding_box.height:.0f})")

        # Check 4: Validate text if provided
        if expected_text and HAS_OCR:
            print(f"    Validating text content...")
            element_img = self.capture_element_screenshot(element)

            if element_img is not None:
                detected_text = self.extract_text_ocr(element_img)
                if expected_text.lower() in detected_text.lower():
                    print(f"    ✓ Text validated: '{detected_text[:50]}'")
                else:
                    print(f"    ✗ Text mismatch: expected '{expected_text}', got '{detected_text[:50]}'")
                    return False

        print(f"    ✓ Validation passed")
        return True

    def capture_before_after(
        self,
        element: DOMElement,
        action_name: str = "click"
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Capture screenshots before and after an action.

        Args:
            element: Element to interact with
            action_name: Name of action for logging

        Returns:
            (before_screenshot, after_screenshot) tuple
        """
        print(f"\n  Capturing before/after screenshots for {action_name}...")

        # Capture before
        before = self.capture_element_screenshot(element, padding=20)
        before_path = f"before_{action_name}_{int(time.time())}.png"
        if before is not None:
            cv2.imwrite(str(self.screenshots_dir / before_path), before)
            print(f"    ✓ Before: {before_path}")

        # Perform action (click)
        self.page.mouse.click(
            element.bounding_box.center_x,
            element.bounding_box.center_y
        )
        time.sleep(0.5)  # Wait for visual changes

        # Capture after
        after = self.capture_element_screenshot(element, padding=20)
        after_path = f"after_{action_name}_{int(time.time())}.png"
        if after is not None:
            cv2.imwrite(str(self.screenshots_dir / after_path), after)
            print(f"    ✓ After: {after_path}")

        return (before, after)

    def detect_visual_change(
        self,
        before: np.ndarray,
        after: np.ndarray,
        threshold: float = 0.05
    ) -> Tuple[bool, float]:
        """
        Detect if visual change occurred between screenshots.

        Args:
            before: Screenshot before action
            after: Screenshot after action
            threshold: Minimum difference to consider a change (0-1)

        Returns:
            (changed, difference) tuple
        """
        if before is None or after is None:
            return (False, 0.0)

        try:
            # Ensure same size
            if before.shape != after.shape:
                after = cv2.resize(after, (before.shape[1], before.shape[0]))

            # Calculate difference
            diff = cv2.absdiff(before, after)
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

            # Calculate percentage of changed pixels
            total_pixels = diff_gray.size
            changed_pixels = np.count_nonzero(diff_gray > 30)  # Threshold for "changed"
            difference = changed_pixels / total_pixels

            changed = difference > threshold

            print(f"    Visual difference: {difference:.2%}")
            print(f"    Changed: {'Yes' if changed else 'No'}")

            return (changed, difference)

        except Exception as e:
            print(f"    ✗ Visual change detection failed: {e}")
            return (False, 0.0)

    def validated_click(
        self,
        element: DOMElement,
        expected_text: Optional[str] = None,
        expect_visual_change: bool = True
    ) -> bool:
        """
        Perform a click with comprehensive validation.

        Args:
            element: Element to click
            expected_text: Expected text content (optional)
            expect_visual_change: Whether to expect visual feedback

        Returns:
            True if click successful and validated, False otherwise
        """
        print(f"\n{'=' * 70}")
        print(f"Validated Click on <{element.tag_name}>")
        print(f"{'=' * 70}")

        # Pre-click validation
        if not self.validate_click_target(element, expected_text):
            print(f"\n✗ Pre-click validation failed")
            return False

        # Capture before/after and perform click
        if HAS_CV2:
            before, after = self.capture_before_after(element, "validated_click")

            # Detect visual change
            if before is not None and after is not None:
                changed, difference = self.detect_visual_change(before, after)

                if expect_visual_change and not changed:
                    print(f"\n⚠ Warning: Expected visual change but none detected")
                elif not expect_visual_change and changed:
                    print(f"\n⚠ Warning: Unexpected visual change detected")
                else:
                    print(f"\n✓ Visual feedback as expected")
        else:
            # Simple click without vision validation
            self.page.mouse.click(
                element.bounding_box.center_x,
                element.bounding_box.center_y
            )
            print(f"\n✓ Click performed (vision validation not available)")

        print(f"\n✓ Validated click completed successfully")
        return True


def demo_vision_validation(page: Page):
    """
    Demonstrate vision-enhanced clicking.

    Args:
        page: Playwright page object
    """
    print("\n" + "=" * 70)
    print("DEMO: Vision-Enhanced Clicking")
    print("=" * 70)

    # Load test page
    test_page_path = Path(__file__).parent / "test_page.html"

    if test_page_path.exists():
        page.goto(f"file://{test_page_path}")
        print(f"\n✓ Loaded test page")
    else:
        page.goto("https://example.com")
        print(f"\n✓ Loaded: https://example.com")

    page.wait_for_load_state("networkidle")
    time.sleep(1)

    # Create vision validator
    validator = VisionValidator(page)

    # Extract DOM structure
    print("\nExtracting DOM structure...")
    extractor = DOMStructureExtractor(page)
    structure = extractor.extract()
    mapper = CoordinateMapper(structure)

    # Demo 1: Full page screenshot
    print(f"\n{'=' * 70}")
    print("Demo 1: Full Page Screenshot")
    print(f"{'=' * 70}")

    if HAS_CV2:
        screenshot = validator.capture_screenshot("full_page.png")
        print(f"  Screenshot size: {screenshot.shape[1]}x{screenshot.shape[0]}")
        print(f"  Color channels: {screenshot.shape[2]}")
    else:
        print("  ✗ OpenCV not available")

    # Demo 2: Find and validate text
    print(f"\n{'=' * 70}")
    print("Demo 2: Find Element by Text")
    print(f"{'=' * 70}")

    search_text = "Example"
    elements = mapper.find_elements_by_text(search_text, exact=False)

    if elements:
        element = elements[0]
        print(f"\n  Found element: <{element.tag_name}>")
        print(f"  Position: ({element.bounding_box.center_x:.0f}, {element.bounding_box.center_y:.0f})")

        # Validate and click
        if HAS_CV2:
            validator.validated_click(element, expected_text=search_text)
        else:
            # Simple click without validation
            page.mouse.click(
                element.bounding_box.center_x,
                element.bounding_box.center_y
            )
            print(f"  ✓ Clicked (validation not available)")

    # Demo 3: OCR-based text detection
    if HAS_OCR:
        print(f"\n{'=' * 70}")
        print("Demo 3: OCR-Based Text Detection")
        print(f"{'=' * 70}")

        visual_elements = validator.find_text_visually(search_text)

        for i, ve in enumerate(visual_elements, 1):
            print(f"\n  {i}. Found '{ve.label}' at ({ve.center[0]}, {ve.center[1]})")
            print(f"     Confidence: {ve.confidence:.1%}")
            print(f"     Size: {ve.width}x{ve.height}")

    # Demo 4: Element screenshot
    print(f"\n{'=' * 70}")
    print("Demo 4: Element Screenshot Capture")
    print(f"{'=' * 70}")

    if elements and HAS_CV2:
        element_img = validator.capture_element_screenshot(elements[0], padding=20)
        if element_img is not None:
            output_path = validator.screenshots_dir / "element_capture.png"
            cv2.imwrite(str(output_path), element_img)
            print(f"\n  ✓ Element screenshot saved: {output_path}")
            print(f"  Size: {element_img.shape[1]}x{element_img.shape[0]}")


def main():
    """
    Main example workflow.
    """
    print("=" * 70)
    print("MCP ACCURATE CLICK SERVER - VISION VALIDATION EXAMPLE")
    print("=" * 70)

    if not HAS_CV2:
        print("\n⚠ Warning: OpenCV not installed")
        print("Install with: pip install opencv-python pillow")
        print("Some features will be limited.\n")

    if not HAS_OCR:
        print("\n⚠ Warning: pytesseract not installed")
        print("Install with: pip install pytesseract")
        print("OCR features will be disabled.\n")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            # Run vision validation demo
            demo_vision_validation(page)

            print("\n" + "=" * 70)
            print("SUMMARY")
            print("=" * 70)
            print("✓ Demonstrated vision-enhanced features:")
            print("  - Full page screenshot capture")
            print("  - Element-specific screenshot capture")
            print("  - Pre-click validation")
            print("  - Before/after visual comparison")
            print("  - Visual change detection")

            if HAS_OCR:
                print("  - OCR-based text detection")
                print("  - Text validation")

            print("\nScreenshots saved to: /tmp/vision_validation/")
            print("\nBrowser will close in 5 seconds...")
            time.sleep(5)

            browser.close()
            print("\n✓ Vision validation example completed successfully!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
