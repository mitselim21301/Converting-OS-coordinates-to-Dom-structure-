#!/usr/bin/env python3
"""
Comprehensive DOM Structure Accuracy Testing

Tests DOM extraction and coordinate mapping accuracy across multiple real websites.
Measures precision, recall, and coordinate accuracy.
"""

import json
import time
from typing import List, Dict, Tuple
from dataclasses import dataclass
from playwright.sync_api import sync_playwright, Page
from dom_structure_extractor import DOMStructureExtractor, CoordinateMapper, DOMElement


@dataclass
class TestResult:
    """Result of a single test"""
    test_name: str
    passed: bool
    duration: float
    details: str
    metrics: Dict[str, any]


@dataclass
class AccuracyMetrics:
    """Accuracy metrics for coordinate mapping"""
    total_tests: int
    successful: int
    failed: int
    accuracy_percentage: float
    avg_coordinate_error: float
    max_coordinate_error: float
    sub_pixel_accurate: int  # Within 1 pixel


class DOMAccuracyTester:
    """Comprehensive DOM extraction and accuracy testing"""

    def __init__(self):
        self.results: List[TestResult] = []

    def run_all_tests(self) -> Dict:
        """Run complete test suite"""
        print("=" * 80)
        print("DOM STRUCTURE EXTRACTION & ACCURACY TEST SUITE")
        print("=" * 80)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})

            # Run tests on different websites
            self._test_simple_website(context)
            self._test_complex_website(context)
            self._test_interactive_elements(context)
            self._test_text_finding_accuracy(context)
            self._test_coordinate_precision(context)
            self._test_scroll_handling(context)
            self._test_overlapping_elements(context)

            browser.close()

        # Generate report
        return self._generate_report()

    def _test_simple_website(self, context):
        """Test 1: Simple website extraction"""
        print("\n" + "─" * 80)
        print("TEST 1: Simple Website (example.com)")
        print("─" * 80)

        start_time = time.time()
        page = context.new_page()

        try:
            page.goto('https://example.com', wait_until='networkidle')

            extractor = DOMStructureExtractor(page)
            structure = extractor.extract()

            # Verify basic extraction
            assert structure.total_elements > 0, "No elements extracted"
            assert structure.visible_elements > 0, "No visible elements"
            assert len(structure.text_elements) > 0, "No text elements found"

            # Find specific text
            mapper = CoordinateMapper(structure)
            example_elements = mapper.find_elements_by_text("Example Domain", exact=False)

            assert len(example_elements) > 0, "Could not find 'Example Domain' text"

            # Verify coordinate accuracy
            h1_element = example_elements[0]
            print(f"  Found h1 element: '{h1_element.text_content[:50]}'")
            print(f"  Position: ({h1_element.bounding_box.x:.1f}, {h1_element.bounding_box.y:.1f})")
            print(f"  Size: {h1_element.bounding_box.width:.1f} × {h1_element.bounding_box.height:.1f}")

            # Verify we can find element at its center
            center_x = h1_element.bounding_box.center_x
            center_y = h1_element.bounding_box.center_y
            found_element = mapper.find_element_at_point(center_x, center_y)

            assert found_element is not None, "Could not find element at its center"
            assert found_element.uid == h1_element.uid or \
                   h1_element.uid in [e.uid for e in [found_element]], \
                   "Found different element at center coordinates"

            duration = time.time() - start_time

            self.results.append(TestResult(
                test_name="Simple Website Extraction",
                passed=True,
                duration=duration,
                details=f"Extracted {structure.total_elements} elements, "
                       f"{structure.visible_elements} visible, "
                       f"{len(structure.text_elements)} with text",
                metrics={
                    'total_elements': structure.total_elements,
                    'visible_elements': structure.visible_elements,
                    'text_elements': len(structure.text_elements),
                    'clickable_elements': structure.clickable_elements
                }
            ))

            print(f"✓ PASSED (duration: {duration:.2f}s)")

        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name="Simple Website Extraction",
                passed=False,
                duration=duration,
                details=str(e),
                metrics={}
            ))
            print(f"✗ FAILED: {e}")

        finally:
            page.close()

    def _test_complex_website(self, context):
        """Test 2: Complex website (GitHub)"""
        print("\n" + "─" * 80)
        print("TEST 2: Complex Website (github.com)")
        print("─" * 80)

        start_time = time.time()
        page = context.new_page()

        try:
            page.goto('https://github.com', wait_until='networkidle', timeout=15000)
            time.sleep(1)  # Let dynamic content load

            extractor = DOMStructureExtractor(page)
            structure = extractor.extract()

            # Complex site should have many elements
            assert structure.total_elements > 100, f"Too few elements: {structure.total_elements}"
            assert structure.clickable_elements > 10, "Too few clickable elements"

            # Verify interactive elements have coordinates
            interactive_with_coords = 0
            for elem in structure.interactive_elements:
                if elem.bounding_box.area > 0:
                    interactive_with_coords += 1

            coord_percentage = (interactive_with_coords / len(structure.interactive_elements)) * 100

            print(f"  Total elements: {structure.total_elements}")
            print(f"  Interactive elements: {len(structure.interactive_elements)}")
            print(f"  Interactive with valid coordinates: {interactive_with_coords} ({coord_percentage:.1f}%)")

            assert coord_percentage > 80, f"Too many elements without coordinates: {coord_percentage:.1f}%"

            duration = time.time() - start_time

            self.results.append(TestResult(
                test_name="Complex Website Extraction",
                passed=True,
                duration=duration,
                details=f"Extracted {structure.total_elements} elements from complex site",
                metrics={
                    'total_elements': structure.total_elements,
                    'interactive_elements': len(structure.interactive_elements),
                    'coordinate_coverage': coord_percentage
                }
            ))

            print(f"✓ PASSED (duration: {duration:.2f}s)")

        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name="Complex Website Extraction",
                passed=False,
                duration=duration,
                details=str(e),
                metrics={}
            ))
            print(f"✗ FAILED: {e}")

        finally:
            page.close()

    def _test_interactive_elements(self, context):
        """Test 3: Interactive element detection"""
        print("\n" + "─" * 80)
        print("TEST 3: Interactive Element Detection")
        print("─" * 80)

        start_time = time.time()
        page = context.new_page()

        try:
            # Create test HTML with various interactive elements
            test_html = """
            <!DOCTYPE html>
            <html>
            <head><title>Interactive Test</title></head>
            <body style="padding: 20px;">
                <button id="btn1" style="margin: 10px;">Click Me</button>
                <a href="#" id="link1" style="margin: 10px;">Link</a>
                <input type="text" id="input1" placeholder="Type here" style="margin: 10px;">
                <select id="select1" style="margin: 10px;">
                    <option>Option 1</option>
                    <option>Option 2</option>
                </select>
                <div role="button" id="div-btn" style="cursor: pointer; margin: 10px;">
                    Div Button
                </div>
                <textarea id="textarea1" style="margin: 10px;"></textarea>
                <label for="checkbox1" style="margin: 10px;">
                    <input type="checkbox" id="checkbox1"> Checkbox
                </label>
            </body>
            </html>
            """

            page.set_content(test_html)
            page.wait_for_load_state('networkidle')

            extractor = DOMStructureExtractor(page)
            structure = extractor.extract()

            # Verify all interactive elements are detected
            interactive_ids = {elem.element_id for elem in structure.interactive_elements
                             if elem.element_id}

            expected_interactive = {'btn1', 'link1', 'input1', 'select1', 'div-btn', 'textarea1', 'checkbox1'}
            found_interactive = interactive_ids & expected_interactive

            detection_rate = (len(found_interactive) / len(expected_interactive)) * 100

            print(f"  Expected interactive: {expected_interactive}")
            print(f"  Found interactive: {found_interactive}")
            print(f"  Detection rate: {detection_rate:.1f}%")

            assert detection_rate == 100, f"Missed interactive elements: {expected_interactive - found_interactive}"

            # Verify all have valid coordinates
            for elem_id in found_interactive:
                elem = next(e for e in structure.interactive_elements if e.element_id == elem_id)
                assert elem.bounding_box.area > 0, f"Element {elem_id} has no bounding box"
                print(f"  ✓ {elem_id}: ({elem.bounding_box.x:.1f}, {elem.bounding_box.y:.1f}) "
                      f"{elem.bounding_box.width:.1f}×{elem.bounding_box.height:.1f}")

            duration = time.time() - start_time

            self.results.append(TestResult(
                test_name="Interactive Element Detection",
                passed=True,
                duration=duration,
                details=f"Detected {len(found_interactive)}/{len(expected_interactive)} interactive elements",
                metrics={
                    'detection_rate': detection_rate,
                    'found': list(found_interactive)
                }
            ))

            print(f"✓ PASSED (duration: {duration:.2f}s)")

        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name="Interactive Element Detection",
                passed=False,
                duration=duration,
                details=str(e),
                metrics={}
            ))
            print(f"✗ FAILED: {e}")

        finally:
            page.close()

    def _test_text_finding_accuracy(self, context):
        """Test 4: Text finding accuracy"""
        print("\n" + "─" * 80)
        print("TEST 4: Text Finding Accuracy")
        print("─" * 80)

        start_time = time.time()
        page = context.new_page()

        try:
            test_html = """
            <!DOCTYPE html>
            <html>
            <body style="padding: 20px;">
                <h1>Main Heading</h1>
                <p>This is a paragraph with some text.</p>
                <button>Submit Form</button>
                <div>Nested <span>text content</span> here</div>
                <a href="#">Click this link</a>
            </body>
            </html>
            """

            page.set_content(test_html)
            page.wait_for_load_state('networkidle')

            extractor = DOMStructureExtractor(page)
            structure = extractor.extract()
            mapper = CoordinateMapper(structure)

            # Test exact text matching
            test_cases = [
                ("Main Heading", True, True),
                ("paragraph", False, True),
                ("Submit Form", True, True),
                ("text content", False, True),
                ("Click this link", True, True),
                ("NonExistent", False, False),
            ]

            passed = 0
            failed = 0

            for text, exact, should_find in test_cases:
                results = mapper.find_elements_by_text(text, exact=exact)
                found = len(results) > 0

                status = "✓" if found == should_find else "✗"
                print(f"  {status} Text '{text}' (exact={exact}): "
                      f"Expected {should_find}, Got {found} ({len(results)} matches)")

                if found == should_find:
                    passed += 1
                else:
                    failed += 1

            accuracy = (passed / len(test_cases)) * 100

            assert accuracy == 100, f"Text finding accuracy: {accuracy:.1f}%"

            duration = time.time() - start_time

            self.results.append(TestResult(
                test_name="Text Finding Accuracy",
                passed=True,
                duration=duration,
                details=f"{passed}/{len(test_cases)} text searches correct",
                metrics={
                    'accuracy': accuracy,
                    'passed': passed,
                    'failed': failed
                }
            ))

            print(f"✓ PASSED - Accuracy: {accuracy:.1f}% (duration: {duration:.2f}s)")

        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name="Text Finding Accuracy",
                passed=False,
                duration=duration,
                details=str(e),
                metrics={}
            ))
            print(f"✗ FAILED: {e}")

        finally:
            page.close()

    def _test_coordinate_precision(self, context):
        """Test 5: Coordinate mapping precision"""
        print("\n" + "─" * 80)
        print("TEST 5: Coordinate Mapping Precision")
        print("─" * 80)

        start_time = time.time()
        page = context.new_page()

        try:
            # Create test page with precisely positioned elements
            test_html = """
            <!DOCTYPE html>
            <html>
            <body style="margin: 0; padding: 0;">
                <div id="box1" style="position: absolute; left: 100px; top: 100px;
                                      width: 200px; height: 150px; background: red;">
                    Box 1
                </div>
                <div id="box2" style="position: absolute; left: 350px; top: 100px;
                                      width: 200px; height: 150px; background: blue;">
                    Box 2
                </div>
                <div id="box3" style="position: absolute; left: 100px; top: 300px;
                                      width: 200px; height: 150px; background: green;">
                    Box 3
                </div>
            </body>
            </html>
            """

            page.set_content(test_html)
            page.wait_for_load_state('networkidle')

            extractor = DOMStructureExtractor(page)
            structure = extractor.extract()
            mapper = CoordinateMapper(structure)

            # Test coordinate precision
            test_points = [
                ('box1', 100, 100, 200, 150),
                ('box2', 350, 100, 200, 150),
                ('box3', 100, 300, 200, 150),
            ]

            total_error = 0.0
            max_error = 0.0
            sub_pixel_count = 0
            tests = 0

            print("\n  Element Position Accuracy:")
            print("  " + "─" * 60)

            for elem_id, expected_x, expected_y, expected_w, expected_h in test_points:
                # Find element
                elem = next((e for e in structure.elements if e.element_id == elem_id), None)
                assert elem is not None, f"Could not find element {elem_id}"

                # Check position accuracy
                x_error = abs(elem.bounding_box.x - expected_x)
                y_error = abs(elem.bounding_box.y - expected_y)
                w_error = abs(elem.bounding_box.width - expected_w)
                h_error = abs(elem.bounding_box.height - expected_h)

                position_error = (x_error**2 + y_error**2)**0.5
                size_error = (w_error**2 + h_error**2)**0.5

                total_error += position_error
                max_error = max(max_error, position_error)

                if position_error < 1.0:
                    sub_pixel_count += 1

                print(f"  {elem_id}:")
                print(f"    Expected: ({expected_x}, {expected_y}) {expected_w}×{expected_h}")
                print(f"    Actual:   ({elem.bounding_box.x:.1f}, {elem.bounding_box.y:.1f}) "
                      f"{elem.bounding_box.width:.1f}×{elem.bounding_box.height:.1f}")
                print(f"    Error:    position={position_error:.3f}px, size={size_error:.3f}px")

                tests += 1

                # Test finding element at its center
                center_x = elem.bounding_box.center_x
                center_y = elem.bounding_box.center_y
                found = mapper.find_element_at_point(center_x, center_y)

                assert found is not None, f"Could not find {elem_id} at center ({center_x}, {center_y})"
                assert found.element_id == elem_id, \
                    f"Wrong element at center: expected {elem_id}, got {found.element_id}"

                print(f"    ✓ Found correctly at center ({center_x:.1f}, {center_y:.1f})")

            avg_error = total_error / tests if tests > 0 else 0

            metrics = AccuracyMetrics(
                total_tests=tests,
                successful=tests,
                failed=0,
                accuracy_percentage=100.0,
                avg_coordinate_error=avg_error,
                max_coordinate_error=max_error,
                sub_pixel_accurate=sub_pixel_count
            )

            print("\n  Summary:")
            print(f"    Average position error: {avg_error:.3f} pixels")
            print(f"    Maximum position error: {max_error:.3f} pixels")
            print(f"    Sub-pixel accurate (<1px): {sub_pixel_count}/{tests} ({sub_pixel_count/tests*100:.1f}%)")

            duration = time.time() - start_time

            self.results.append(TestResult(
                test_name="Coordinate Precision",
                passed=True,
                duration=duration,
                details=f"Avg error: {avg_error:.3f}px, Max: {max_error:.3f}px",
                metrics={
                    'avg_error': avg_error,
                    'max_error': max_error,
                    'sub_pixel_count': sub_pixel_count,
                    'total_tests': tests
                }
            ))

            print(f"\n✓ PASSED (duration: {duration:.2f}s)")

        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name="Coordinate Precision",
                passed=False,
                duration=duration,
                details=str(e),
                metrics={}
            ))
            print(f"✗ FAILED: {e}")

        finally:
            page.close()

    def _test_scroll_handling(self, context):
        """Test 6: Scroll handling"""
        print("\n" + "─" * 80)
        print("TEST 6: Scroll Position Handling")
        print("─" * 80)

        start_time = time.time()
        page = context.new_page()

        try:
            # Create tall page
            test_html = """
            <!DOCTYPE html>
            <html>
            <body style="height: 3000px; margin: 0;">
                <div id="top" style="position: absolute; top: 100px; left: 100px;">Top Element</div>
                <div id="middle" style="position: absolute; top: 1500px; left: 100px;">Middle Element</div>
                <div id="bottom" style="position: absolute; top: 2800px; left: 100px;">Bottom Element</div>
            </body>
            </html>
            """

            page.set_content(test_html)
            page.wait_for_load_state('networkidle')

            # Test at different scroll positions
            scroll_positions = [0, 1000, 2000]

            for scroll_y in scroll_positions:
                page.evaluate(f"window.scrollTo(0, {scroll_y})")
                time.sleep(0.2)

                extractor = DOMStructureExtractor(page)
                structure = extractor.extract()

                print(f"\n  Scroll position: {scroll_y}px")
                print(f"    Detected scroll: {structure.scroll_y:.1f}px")

                # Verify scroll position is captured
                assert abs(structure.scroll_y - scroll_y) < 1, \
                    f"Scroll detection error: expected {scroll_y}, got {structure.scroll_y}"

                # Verify page coordinates vs viewport coordinates
                mapper = CoordinateMapper(structure)
                top_elem = next((e for e in structure.elements if e.element_id == 'top'), None)

                if top_elem:
                    viewport_y = top_elem.bounding_box.y
                    page_y = top_elem.bounding_box.page_y
                    expected_page_y = 100  # Absolute position in HTML

                    print(f"    Top element - Viewport Y: {viewport_y:.1f}, Page Y: {page_y:.1f}")
                    print(f"    Expected page Y: {expected_page_y}")

                    assert abs(page_y - expected_page_y) < 1, \
                        f"Page coordinate error: expected {expected_page_y}, got {page_y}"

            duration = time.time() - start_time

            self.results.append(TestResult(
                test_name="Scroll Handling",
                passed=True,
                duration=duration,
                details=f"Tested {len(scroll_positions)} scroll positions",
                metrics={
                    'scroll_positions_tested': len(scroll_positions)
                }
            ))

            print(f"\n✓ PASSED (duration: {duration:.2f}s)")

        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name="Scroll Handling",
                passed=False,
                duration=duration,
                details=str(e),
                metrics={}
            ))
            print(f"✗ FAILED: {e}")

        finally:
            page.close()

    def _test_overlapping_elements(self, context):
        """Test 7: Overlapping element detection"""
        print("\n" + "─" * 80)
        print("TEST 7: Overlapping Element Detection")
        print("─" * 80)

        start_time = time.time()
        page = context.new_page()

        try:
            # Create overlapping elements with different z-index
            test_html = """
            <!DOCTYPE html>
            <html>
            <body style="margin: 0;">
                <div id="bottom" style="position: absolute; left: 100px; top: 100px;
                                        width: 200px; height: 200px;
                                        background: red; z-index: 1;">
                    Bottom
                </div>
                <div id="middle" style="position: absolute; left: 150px; top: 150px;
                                        width: 200px; height: 200px;
                                        background: blue; z-index: 2;">
                    Middle
                </div>
                <div id="top" style="position: absolute; left: 200px; top: 200px;
                                     width: 200px; height: 200px;
                                     background: green; z-index: 3;">
                    Top
                </div>
            </body>
            </html>
            """

            page.set_content(test_html)
            page.wait_for_load_state('networkidle')

            extractor = DOMStructureExtractor(page)
            structure = extractor.extract()
            mapper = CoordinateMapper(structure)

            # Test points in overlapping area
            test_points = [
                (250, 250, 'top'),     # Should find top element
                (175, 175, 'middle'),   # Should find middle element
                (125, 125, 'bottom'),   # Should find bottom element
            ]

            print("\n  Testing overlapping element detection:")

            for x, y, expected_id in test_points:
                found = mapper.find_element_at_point(x, y)

                if found:
                    result = "✓" if found.element_id == expected_id else "✗"
                    print(f"  {result} ({x}, {y}): Expected '{expected_id}', "
                          f"Found '{found.element_id}' (z-index: {found.z_index})")

                    assert found.element_id == expected_id, \
                        f"Wrong element: expected {expected_id}, got {found.element_id}"
                else:
                    print(f"  ✗ ({x}, {y}): No element found")
                    raise AssertionError(f"No element found at ({x}, {y})")

            duration = time.time() - start_time

            self.results.append(TestResult(
                test_name="Overlapping Element Detection",
                passed=True,
                duration=duration,
                details=f"Correctly identified topmost elements",
                metrics={
                    'test_points': len(test_points)
                }
            ))

            print(f"\n✓ PASSED (duration: {duration:.2f}s)")

        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name="Overlapping Element Detection",
                passed=False,
                duration=duration,
                details=str(e),
                metrics={}
            ))
            print(f"✗ FAILED: {e}")

        finally:
            page.close()

    def _generate_report(self) -> Dict:
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("TEST REPORT")
        print("=" * 80)

        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        total_duration = sum(r.duration for r in self.results)

        print(f"\nOverall Results:")
        print(f"  Total Tests: {total}")
        print(f"  Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"  Failed: {failed} ({failed/total*100:.1f}%)")
        print(f"  Total Duration: {total_duration:.2f}s")

        print(f"\nDetailed Results:")
        print("  " + "─" * 76)

        for i, result in enumerate(self.results, 1):
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"  {i}. {status} - {result.test_name} ({result.duration:.2f}s)")
            print(f"     {result.details}")

            if result.metrics:
                print(f"     Metrics: {json.dumps(result.metrics, indent=8)}")

        # Extract key metrics
        coord_test = next((r for r in self.results if r.test_name == "Coordinate Precision"), None)
        if coord_test and coord_test.passed:
            print(f"\nCoordinate Accuracy:")
            print(f"  Average Error: {coord_test.metrics['avg_error']:.3f} pixels")
            print(f"  Maximum Error: {coord_test.metrics['max_error']:.3f} pixels")
            print(f"  Sub-pixel Accurate: {coord_test.metrics['sub_pixel_count']}/{coord_test.metrics['total_tests']}")

        # Save report to file
        report = {
            'timestamp': time.time(),
            'summary': {
                'total_tests': total,
                'passed': passed,
                'failed': failed,
                'pass_rate': passed / total * 100 if total > 0 else 0,
                'total_duration': total_duration
            },
            'tests': [
                {
                    'name': r.test_name,
                    'passed': r.passed,
                    'duration': r.duration,
                    'details': r.details,
                    'metrics': r.metrics
                }
                for r in self.results
            ]
        }

        report_path = '/tmp/dom_test_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n✓ Full report saved to: {report_path}")
        print("=" * 80)

        return report


if __name__ == '__main__':
    tester = DOMAccuracyTester()
    report = tester.run_all_tests()

    # Exit with appropriate code
    exit(0 if all(r.passed for r in tester.results) else 1)
