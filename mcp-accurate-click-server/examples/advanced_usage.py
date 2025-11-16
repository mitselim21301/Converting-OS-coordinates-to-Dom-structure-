#!/usr/bin/env python3
"""
Advanced Usage Example - MCP Accurate Click Server

This example demonstrates advanced features and complex multi-step automation:
- Multi-page navigation with state tracking
- Coordinate transformation calibration
- Sequential clicking workflows
- Error recovery strategies
- Performance optimization
- Caching and reuse of DOM structures

Run this example to see production-ready automation patterns.
"""

import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from playwright.sync_api import sync_playwright, Page, Browser
from dom_structure_extractor import DOMStructureExtractor, CoordinateMapper, DOMStructure
from os_to_dom_transformer import OSToDOM_Transformer
import numpy as np


@dataclass
class AutomationContext:
    """Context for tracking automation state across multiple operations."""
    page: Page
    structure: Optional[DOMStructure] = None
    mapper: Optional[CoordinateMapper] = None
    transformer: Optional[OSToDOM_Transformer] = None
    last_extraction_time: float = 0
    cache_ttl: float = 5.0  # Cache DOM structure for 5 seconds


class AdvancedClickAutomation:
    """
    Advanced automation system with intelligent features.

    Features:
    - DOM structure caching
    - Automatic re-extraction on page changes
    - Click validation and retry
    - Performance monitoring
    - Error recovery
    """

    def __init__(self, context: AutomationContext):
        """
        Initialize automation system.

        Args:
            context: Automation context with page and state
        """
        self.context = context
        self.click_history: List[Dict] = []
        self.performance_metrics: Dict[str, List[float]] = {
            'extraction_time': [],
            'search_time': [],
            'click_time': []
        }

    def ensure_fresh_structure(self, force: bool = False) -> DOMStructure:
        """
        Ensure we have a fresh DOM structure, using cache if valid.

        Args:
            force: Force re-extraction even if cache is valid

        Returns:
            Current DOMStructure
        """
        current_time = time.time()
        cache_age = current_time - self.context.last_extraction_time

        if force or cache_age > self.context.cache_ttl or self.context.structure is None:
            print(f"Extracting DOM structure (cache age: {cache_age:.1f}s)...")

            start_time = time.time()
            extractor = DOMStructureExtractor(self.context.page)
            self.context.structure = extractor.extract()
            self.context.mapper = CoordinateMapper(self.context.structure)
            self.context.last_extraction_time = current_time

            extraction_time = time.time() - start_time
            self.performance_metrics['extraction_time'].append(extraction_time)
            print(f"✓ Extracted in {extraction_time:.3f}s")
        else:
            print(f"✓ Using cached DOM structure (age: {cache_age:.1f}s)")

        return self.context.structure

    def smart_click_by_text(
        self,
        text: str,
        exact: bool = False,
        clickable_only: bool = True,
        max_retries: int = 2
    ) -> bool:
        """
        Intelligently find and click element containing text.

        Args:
            text: Text to search for
            exact: Whether to match text exactly
            clickable_only: Only consider clickable elements
            max_retries: Maximum retry attempts

        Returns:
            True if click succeeded, False otherwise
        """
        print(f"\nSmart click on element with text '{text}'...")

        for attempt in range(max_retries + 1):
            try:
                # Ensure fresh structure
                structure = self.ensure_fresh_structure()

                # Search for element
                start_time = time.time()
                elements = self.context.mapper.find_elements_by_text(text, exact=exact)

                if clickable_only:
                    elements = [e for e in elements if e.clickable]

                search_time = time.time() - start_time
                self.performance_metrics['search_time'].append(search_time)

                if not elements:
                    print(f"  ✗ No {'clickable ' if clickable_only else ''}elements found")
                    if attempt < max_retries:
                        print(f"  Retry {attempt + 1}/{max_retries}...")
                        time.sleep(0.5)
                        # Force re-extraction on retry
                        self.ensure_fresh_structure(force=True)
                        continue
                    return False

                # Use the first matching element
                target = elements[0]
                print(f"  ✓ Found <{target.tag_name}> at "
                      f"({target.bounding_box.center_x:.1f}, {target.bounding_box.center_y:.1f})")

                # Click the element
                start_time = time.time()
                self.context.page.mouse.click(
                    target.bounding_box.center_x,
                    target.bounding_box.center_y
                )
                click_time = time.time() - start_time
                self.performance_metrics['click_time'].append(click_time)

                # Record in history
                self.click_history.append({
                    'timestamp': time.time(),
                    'text': text,
                    'element': target.tag_name,
                    'coordinates': (target.bounding_box.center_x, target.bounding_box.center_y),
                    'attempt': attempt + 1
                })

                print(f"  ✓ Clicked successfully (attempt {attempt + 1})")
                time.sleep(0.3)  # Small delay for UI feedback
                return True

            except Exception as e:
                print(f"  ✗ Click failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries:
                    print(f"  Retrying...")
                    time.sleep(0.5)
                else:
                    return False

        return False

    def click_sequence(self, sequence: List[Tuple[str, bool]]) -> bool:
        """
        Execute a sequence of clicks.

        Args:
            sequence: List of (text, exact) tuples

        Returns:
            True if all clicks succeeded, False otherwise
        """
        print(f"\n{'=' * 70}")
        print(f"Executing click sequence ({len(sequence)} steps)")
        print(f"{'=' * 70}")

        for i, (text, exact) in enumerate(sequence, 1):
            print(f"\nStep {i}/{len(sequence)}: Click '{text}'")

            success = self.smart_click_by_text(text, exact=exact)

            if not success:
                print(f"\n✗ Sequence failed at step {i}")
                return False

            # Wait for page to stabilize after click
            time.sleep(0.5)

        print(f"\n✓ Sequence completed successfully!")
        return True

    def find_and_click_near_text(
        self,
        text: str,
        max_distance: float = 100,
        prefer_buttons: bool = True
    ) -> bool:
        """
        Find clickable elements near text and click the best match.

        Args:
            text: Text to search near
            max_distance: Maximum distance in pixels
            prefer_buttons: Prefer button elements over others

        Returns:
            True if click succeeded, False otherwise
        """
        print(f"\nFinding clickable elements near '{text}'...")

        structure = self.ensure_fresh_structure()
        clickables = self.context.mapper.find_clickable_near_text(text, max_distance)

        if not clickables:
            print(f"  ✗ No clickable elements found near '{text}'")
            return False

        print(f"  ✓ Found {len(clickables)} clickable element(s) nearby")

        # Sort by preference
        if prefer_buttons:
            clickables.sort(key=lambda e: (
                e.tag_name == 'button',
                e.role == 'button',
                e.tag_name == 'a'
            ), reverse=True)

        # Click the best match
        target = clickables[0]
        print(f"  Clicking <{target.tag_name}> at "
              f"({target.bounding_box.center_x:.1f}, {target.bounding_box.center_y:.1f})")

        try:
            self.context.page.mouse.click(
                target.bounding_box.center_x,
                target.bounding_box.center_y
            )
            print("  ✓ Click successful")
            return True
        except Exception as e:
            print(f"  ✗ Click failed: {e}")
            return False

    def calibrate_os_to_dom(self, calibration_points: int = 9) -> bool:
        """
        Calibrate OS coordinate to DOM coordinate transformation.

        Args:
            calibration_points: Number of calibration points to use

        Returns:
            True if calibration succeeded, False otherwise
        """
        print(f"\n{'=' * 70}")
        print("OS to DOM Coordinate Calibration")
        print(f"{'=' * 70}")

        try:
            structure = self.ensure_fresh_structure()

            # Select well-distributed calibration points
            print(f"\nSelecting {calibration_points} calibration points...")

            # Use clickable elements spread across the viewport
            clickables = [e for e in structure.interactive_elements
                         if e.visible and e.clickable]

            if len(clickables) < calibration_points:
                print(f"  ✗ Not enough clickable elements (found {len(clickables)})")
                return False

            # Sort by position to get good distribution
            # Divide viewport into grid and pick one element from each cell
            grid_size = int(np.ceil(np.sqrt(calibration_points)))
            cell_width = structure.viewport_width / grid_size
            cell_height = structure.viewport_height / grid_size

            selected_elements = []
            for i in range(grid_size):
                for j in range(grid_size):
                    if len(selected_elements) >= calibration_points:
                        break

                    # Find elements in this grid cell
                    cell_x_min = i * cell_width
                    cell_x_max = (i + 1) * cell_width
                    cell_y_min = j * cell_height
                    cell_y_max = (j + 1) * cell_height

                    cell_elements = [
                        e for e in clickables
                        if cell_x_min <= e.bounding_box.center_x < cell_x_max
                        and cell_y_min <= e.bounding_box.center_y < cell_y_max
                    ]

                    if cell_elements:
                        selected_elements.append(cell_elements[0])

            if len(selected_elements) < 3:
                print(f"  ✗ Could not find enough distributed elements")
                return False

            print(f"  ✓ Selected {len(selected_elements)} calibration points")

            # Simulate OS coordinates (in a real scenario, these would come from actual OS)
            # Here we create synthetic OS coordinates by applying a transformation
            dom_points = np.array([
                [e.bounding_box.center_x, e.bounding_box.center_y]
                for e in selected_elements
            ])

            # Simulate OS coordinates with scaling and offset
            os_points = dom_points * 1.2 + np.array([50, 80])

            # Add small noise to simulate measurement uncertainty
            os_points += np.random.randn(*os_points.shape) * 2.0

            # Calibrate transformer
            print("\nCalibrating transformation...")
            self.context.transformer = OSToDOM_Transformer(enable_adaptive=True)
            report = self.context.transformer.calibrate(
                os_points,
                dom_points,
                use_ransac=True,
                refine=True
            )

            print(f"  ✓ Calibration successful")
            print(f"  - Accuracy: {report['validation']['achieved_accuracy']:.4f} pixels")
            print(f"  - Sub-pixel accurate: {report['validation']['is_subpixel_accurate']}")
            print(f"  - Inlier ratio: {report['inlier_ratio']:.1%}")

            return True

        except Exception as e:
            print(f"  ✗ Calibration failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def show_performance_stats(self):
        """Display performance statistics."""
        print(f"\n{'=' * 70}")
        print("Performance Statistics")
        print(f"{'=' * 70}")

        for metric, times in self.performance_metrics.items():
            if times:
                print(f"\n{metric.replace('_', ' ').title()}:")
                print(f"  - Count: {len(times)}")
                print(f"  - Mean: {np.mean(times):.3f}s")
                print(f"  - Median: {np.median(times):.3f}s")
                print(f"  - Min: {np.min(times):.3f}s")
                print(f"  - Max: {np.max(times):.3f}s")

        print(f"\nClick History: {len(self.click_history)} clicks")

    def save_session_data(self, filename: str = "automation_session.json"):
        """
        Save session data for analysis.

        Args:
            filename: Output filename
        """
        output_path = Path("/tmp") / filename

        session_data = {
            'timestamp': time.time(),
            'url': self.context.page.url,
            'click_history': self.click_history,
            'performance_metrics': {
                k: {'mean': float(np.mean(v)) if v else 0, 'count': len(v)}
                for k, v in self.performance_metrics.items()
            },
            'structure_stats': {
                'total_elements': self.context.structure.total_elements,
                'clickable_elements': self.context.structure.clickable_elements,
                'visible_elements': self.context.structure.visible_elements
            } if self.context.structure else None
        }

        with open(output_path, 'w') as f:
            json.dump(session_data, f, indent=2)

        print(f"\n✓ Session data saved to {output_path}")


def demo_multi_step_workflow(browser: Browser):
    """
    Demonstrate a complex multi-step automation workflow.

    Args:
        browser: Playwright browser instance
    """
    print("\n" + "=" * 70)
    print("DEMO: Multi-Step Workflow")
    print("=" * 70)

    # Create new page
    page = browser.new_page()
    context = AutomationContext(page=page)
    automation = AdvancedClickAutomation(context)

    try:
        # Step 1: Navigate to test page
        print("\nStep 1: Loading test page...")
        test_page_path = Path(__file__).parent / "test_page.html"
        if test_page_path.exists():
            page.goto(f"file://{test_page_path}")
        else:
            page.goto("https://example.com")
        page.wait_for_load_state("networkidle")
        print(f"✓ Loaded: {page.url}")

        # Step 2: Extract initial structure
        print("\nStep 2: Initial DOM extraction...")
        automation.ensure_fresh_structure()

        # Step 3: Execute click sequence
        print("\nStep 3: Executing automation sequence...")
        sequence = [
            ("Example", False),  # Click anything with "Example"
            ("More", False),     # Then click "More"
        ]
        automation.click_sequence(sequence)

        # Step 4: Calibrate coordinate transformation
        print("\nStep 4: Calibrating coordinate transformation...")
        automation.calibrate_os_to_dom(calibration_points=9)

        # Step 5: Find and click near text
        print("\nStep 5: Finding clickable elements near text...")
        automation.find_and_click_near_text("information", max_distance=150)

        # Step 6: Show statistics
        automation.show_performance_stats()

        # Step 7: Save session data
        automation.save_session_data()

        print("\n✓ Multi-step workflow completed successfully!")

    except Exception as e:
        print(f"\n✗ Workflow failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        time.sleep(2)
        page.close()


def main():
    """
    Main example workflow.
    """
    print("=" * 70)
    print("MCP ACCURATE CLICK SERVER - ADVANCED USAGE EXAMPLE")
    print("=" * 70)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)

            # Run the multi-step workflow demo
            demo_multi_step_workflow(browser)

            print("\n" + "=" * 70)
            print("SUMMARY")
            print("=" * 70)
            print("✓ Demonstrated advanced automation features:")
            print("  - DOM structure caching")
            print("  - Intelligent click with retry logic")
            print("  - Multi-step workflows")
            print("  - Coordinate transformation calibration")
            print("  - Performance monitoring")
            print("  - Session data persistence")

            browser.close()
            print("\n✓ Advanced example completed successfully!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
