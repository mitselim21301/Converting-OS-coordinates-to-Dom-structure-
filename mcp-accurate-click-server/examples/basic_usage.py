#!/usr/bin/env python3
"""
Basic Usage Example - MCP Accurate Click Server

This example demonstrates the fundamental features of the accurate click system:
- DOM structure extraction
- Coordinate mapping
- Simple element clicking
- Basic error handling

Run this example to understand the core functionality.
"""

import sys
import json
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.sync_api import sync_playwright, Page
from dom_structure_extractor import DOMStructureExtractor, CoordinateMapper


def setup_test_page(page: Page):
    """
    Navigate to a test page for demonstration.

    Args:
        page: Playwright page object
    """
    print("Setting up test page...")

    # Navigate to the test page (using local file or a simple website)
    test_page_path = Path(__file__).parent / "test_page.html"

    if test_page_path.exists():
        page.goto(f"file://{test_page_path}")
    else:
        # Fallback to a simple website
        page.goto("https://example.com")

    page.wait_for_load_state("networkidle")
    print(f"✓ Loaded: {page.url}")


def extract_dom_structure(page: Page):
    """
    Extract the complete DOM structure from the page.

    Args:
        page: Playwright page object

    Returns:
        DOMStructure object containing all page elements
    """
    print("\nExtracting DOM structure...")

    # Create extractor and extract structure
    extractor = DOMStructureExtractor(page)
    structure = extractor.extract()

    print(f"✓ Extracted {structure.total_elements} total elements")
    print(f"  - Visible elements: {structure.visible_elements}")
    print(f"  - Clickable elements: {structure.clickable_elements}")
    print(f"  - Interactive elements: {len(structure.interactive_elements)}")

    return structure


def find_element_by_text(structure, mapper: CoordinateMapper, text: str):
    """
    Find and display elements containing specific text.

    Args:
        structure: DOMStructure object
        mapper: CoordinateMapper object
        text: Text to search for
    """
    print(f"\nSearching for elements containing '{text}'...")

    # Find elements by text
    elements = mapper.find_elements_by_text(text, exact=False)

    if not elements:
        print(f"  ✗ No elements found containing '{text}'")
        return None

    print(f"✓ Found {len(elements)} element(s):")
    for i, elem in enumerate(elements, 1):
        print(f"  {i}. <{elem.tag_name}> at ({elem.bounding_box.center_x:.1f}, "
              f"{elem.bounding_box.center_y:.1f})")
        if elem.text_content:
            preview = elem.text_content[:50] + "..." if len(elem.text_content) > 50 else elem.text_content
            print(f"     Text: {preview}")

    return elements[0] if elements else None


def click_element_at_coordinates(page: Page, x: float, y: float):
    """
    Click at specific viewport coordinates.

    Args:
        page: Playwright page object
        x: X coordinate in viewport space
        y: Y coordinate in viewport space
    """
    print(f"\nClicking at coordinates ({x:.1f}, {y:.1f})...")

    try:
        # Use Playwright's click at coordinates
        page.mouse.click(x, y)
        print("✓ Click successful")

        # Small delay to see the effect
        time.sleep(0.5)

    except Exception as e:
        print(f"✗ Click failed: {e}")


def find_element_at_point(mapper: CoordinateMapper, x: float, y: float):
    """
    Find which DOM element is at a specific coordinate.

    Args:
        mapper: CoordinateMapper object
        x: X coordinate
        y: Y coordinate

    Returns:
        DOMElement at the point, or None
    """
    print(f"\nFinding element at point ({x:.1f}, {y:.1f})...")

    element = mapper.find_element_at_point(x, y, coordinate_type='viewport')

    if element:
        print(f"✓ Found element: <{element.tag_name}>")
        print(f"  - ID: {element.element_id or 'none'}")
        print(f"  - Classes: {', '.join(element.class_names) if element.class_names else 'none'}")
        print(f"  - Clickable: {element.clickable}")
        print(f"  - Visible: {element.visible}")
        if element.text_content:
            preview = element.text_content[:50] + "..." if len(element.text_content) > 50 else element.text_content
            print(f"  - Text: {preview}")
    else:
        print("✗ No element found at this point")

    return element


def save_dom_structure(structure, filename: str = "dom_structure.json"):
    """
    Save the DOM structure to a JSON file for inspection.

    Args:
        structure: DOMStructure object
        filename: Output filename
    """
    output_path = Path("/tmp") / filename

    print(f"\nSaving DOM structure to {output_path}...")

    try:
        with open(output_path, 'w') as f:
            json.dump(structure.to_dict(), f, indent=2)
        print(f"✓ Saved to {output_path}")
    except Exception as e:
        print(f"✗ Failed to save: {e}")


def main():
    """
    Main example workflow demonstrating basic usage.
    """
    print("=" * 70)
    print("MCP ACCURATE CLICK SERVER - BASIC USAGE EXAMPLE")
    print("=" * 70)

    try:
        with sync_playwright() as p:
            # Launch browser (visible for demonstration)
            print("\nLaunching browser...")
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            # Step 1: Load test page
            setup_test_page(page)

            # Step 2: Extract DOM structure
            structure = extract_dom_structure(page)

            # Step 3: Create coordinate mapper
            print("\nCreating coordinate mapper...")
            mapper = CoordinateMapper(structure)
            print("✓ Coordinate mapper ready")

            # Step 4: Find element by text (example)
            element = find_element_by_text(structure, mapper, "Example")

            # Step 5: Click on found element (if any)
            if element:
                click_element_at_coordinates(
                    page,
                    element.bounding_box.center_x,
                    element.bounding_box.center_y
                )

            # Step 6: Find element at specific coordinates
            # Check what's at the center of the viewport
            viewport_center_x = structure.viewport_width / 2
            viewport_center_y = structure.viewport_height / 2
            find_element_at_point(mapper, viewport_center_x, viewport_center_y)

            # Step 7: Save structure for inspection
            save_dom_structure(structure)

            # Step 8: Display summary
            print("\n" + "=" * 70)
            print("SUMMARY")
            print("=" * 70)
            print(f"✓ Successfully extracted DOM structure")
            print(f"✓ Total elements: {structure.total_elements}")
            print(f"✓ Clickable elements: {structure.clickable_elements}")
            print(f"✓ Viewport: {structure.viewport_width}x{structure.viewport_height}")
            print(f"✓ Page size: {structure.page_width}x{structure.page_height}")
            print(f"✓ Device pixel ratio: {structure.device_pixel_ratio}")

            # Keep browser open for a moment
            print("\nBrowser will close in 3 seconds...")
            time.sleep(3)

            browser.close()
            print("\n✓ Example completed successfully!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
