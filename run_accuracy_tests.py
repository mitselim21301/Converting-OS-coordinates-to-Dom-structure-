#!/usr/bin/env python3
"""
Simplified DOM Structure Accuracy Testing

Focuses on local HTML tests to avoid network dependency.
Tests DOM extraction and coordinate mapping accuracy.
"""

import json
import time
from typing import List, Dict
from dataclasses import dataclass
from playwright.sync_api import sync_playwright
from dom_structure_extractor import DOMStructureExtractor, CoordinateMapper


@dataclass
class TestResult:
    """Result of a single test"""
    test_name: str
    passed: bool
    duration: float
    details: str
    metrics: Dict[str, any]


class LocalDOMTester:
    """Test DOM extraction with local HTML"""

    def __init__(self):
        self.results: List[TestResult] = []

    def run_all_tests(self):
        """Run all local tests"""
        print("=" * 80)
        print("DOM STRUCTURE EXTRACTION - LOCAL ACCURACY TESTS")
        print("=" * 80)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})

            # Run local tests
            self._test_basic_extraction(page)
            self._test_interactive_elements(page)
            self._test_text_finding(page)
            self._test_coordinate_precision(page)
            self._test_scroll_handling(page)
            self._test_overlapping_elements(page)
            self._test_complex_layout(page)

            browser.close()

        self._generate_report()

    def _test_basic_extraction(self, page):
        """Test 1: Basic DOM extraction"""
        print("\n" + "─" * 80)
        print("TEST 1: Basic DOM Extraction")
        print("─" * 80)

        start_time = time.time()

        try:
            html = """
            <!DOCTYPE html>
            <html>
            <head><title>Basic Test</title></head>
            <body>
                <h1 id="title">Test Page</h1>
                <p class="description">This is a test page for DOM extraction.</p>
                <button id="submit">Submit</button>
                <a href="#" id="link">Click here</a>
            </body>
            </html>
            """

            page.set_content(html)
            page.wait_for_load_state('domcontentloaded')

            extractor = DOMStructureExtractor(page)
            structure = extractor.extract()

            # Validations
            assert structure.total_elements > 0, "No elements extracted"
            assert structure.visible_elements > 0, "No visible elements"

            # Find specific elements
            mapper = CoordinateMapper(structure)
            title_elements = mapper.find_elements_by_text("Test Page", exact=True)
            assert len(title_elements) > 0, "Could not find title"

            submit_button = next((e for e in structure.elements if e.element_id == 'submit'), None)
            assert submit_button is not None, "Could not find submit button"
            assert submit_button.clickable, "Submit button not detected as clickable"

            duration = time.time() - start_time

            print(f"  ✓ Extracted {structure.total_elements} elements")
            print(f"  ✓ Found {len(structure.interactive_elements)} interactive elements")
            print(f"  ✓ Found {len(structure.text_elements)} text elements")

            self.results.append(TestResult(
                test_name="Basic DOM Extraction",
                passed=True,
                duration=duration,
                details=f"Successfully extracted {structure.total_elements} elements",
                metrics={
                    'total': structure.total_elements,
                    'visible': structure.visible_elements,
                    'interactive': len(structure.interactive_elements)
                }
            ))

            print(f"✓ PASSED ({duration:.2f}s)")

        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name="Basic DOM Extraction",
                passed=False,
                duration=duration,
                details=str(e),
                metrics={}
            ))
            print(f"✗ FAILED: {e}")

    def _test_interactive_elements(self, page):
        """Test 2: Interactive element detection"""
        print("\n" + "─" * 80)
        print("TEST 2: Interactive Element Detection")
        print("─" * 80)

        start_time = time.time()

        try:
            html = """
            <!DOCTYPE html>
            <html>
            <body style="padding: 20px;">
                <button id="btn1">Button</button>
                <a href="#" id="link1">Link</a>
                <input type="text" id="input1" placeholder="Text">
                <select id="select1"><option>Option</option></select>
                <textarea id="textarea1"></textarea>
                <div role="button" id="div-btn" style="cursor: pointer;">Div Button</div>
                <input type="checkbox" id="check1">
                <input type="radio" id="radio1">
            </body>
            </html>
            """

            page.set_content(html)
            page.wait_for_load_state('domcontentloaded')

            extractor = DOMStructureExtractor(page)
            structure = extractor.extract()

            expected = {'btn1', 'link1', 'input1', 'select1', 'textarea1', 'div-btn', 'check1', 'radio1'}
            found = {e.element_id for e in structure.interactive_elements if e.element_id}

            detection_rate = (len(found & expected) / len(expected)) * 100

            print(f"  Expected: {expected}")
            print(f"  Found: {found}")
            print(f"  Detection rate: {detection_rate:.1f}%")

            # Check coordinates
            coord_count = sum(1 for e in structure.interactive_elements if e.bounding_box.area > 0)
            print(f"  Elements with valid coordinates: {coord_count}/{len(structure.interactive_elements)}")

            assert detection_rate >= 75, f"Low detection rate: {detection_rate:.1f}%"

            duration = time.time() - start_time

            self.results.append(TestResult(
                test_name="Interactive Element Detection",
                passed=True,
                duration=duration,
                details=f"Detected {len(found & expected)}/{len(expected)} interactive elements",
                metrics={
                    'detection_rate': detection_rate,
                    'expected': len(expected),
                    'found': len(found & expected)
                }
            ))

            print(f"✓ PASSED ({duration:.2f}s)")

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

    def _test_text_finding(self, page):
        """Test 3: Text finding accuracy"""
        print("\n" + "─" * 80)
        print("TEST 3: Text Finding Accuracy")
        print("─" * 80)

        start_time = time.time()

        try:
            html = """
            <!DOCTYPE html>
            <html>
            <body>
                <h1>Main Heading</h1>
                <p>A paragraph with unique text.</p>
                <button>Click Me</button>
                <div>Nested <span>content</span> here</div>
            </body>
            </html>
            """

            page.set_content(html)
            page.wait_for_load_state('domcontentloaded')

            extractor = DOMStructureExtractor(page)
            structure = extractor.extract()
            mapper = CoordinateMapper(structure)

            tests = [
                ("Main Heading", True, True),
                ("paragraph", False, True),
                ("Click Me", True, True),
                ("Nested", False, True),
                ("NonExistent", False, False),
            ]

            passed = 0
            for text, exact, should_find in tests:
                results = mapper.find_elements_by_text(text, exact=exact)
                found = len(results) > 0

                if found == should_find:
                    passed += 1
                    status = "✓"
                else:
                    status = "✗"

                print(f"  {status} '{text}' (exact={exact}): Found={found}, Expected={should_find}")

            accuracy = (passed / len(tests)) * 100

            duration = time.time() - start_time

            self.results.append(TestResult(
                test_name="Text Finding Accuracy",
                passed=accuracy >= 80,
                duration=duration,
                details=f"Accuracy: {accuracy:.1f}%",
                metrics={'accuracy': accuracy, 'passed': passed, 'total': len(tests)}
            ))

            print(f"{'✓' if accuracy >= 80 else '✗'} Accuracy: {accuracy:.1f}% ({duration:.2f}s)")

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

    def _test_coordinate_precision(self, page):
        """Test 4: Coordinate precision"""
        print("\n" + "─" * 80)
        print("TEST 4: Coordinate Mapping Precision")
        print("─" * 80)

        start_time = time.time()

        try:
            html = """
            <!DOCTYPE html>
            <html>
            <body style="margin: 0; padding: 0;">
                <div id="box1" style="position: absolute; left: 100px; top: 100px;
                                      width: 200px; height: 150px; background: red;">Box 1</div>
                <div id="box2" style="position: absolute; left: 350px; top: 100px;
                                      width: 200px; height: 150px; background: blue;">Box 2</div>
                <div id="box3" style="position: absolute; left: 100px; top: 300px;
                                      width: 200px; height: 150px; background: green;">Box 3</div>
            </body>
            </html>
            """

            page.set_content(html)
            page.wait_for_load_state('domcontentloaded')

            extractor = DOMStructureExtractor(page)
            structure = extractor.extract()
            mapper = CoordinateMapper(structure)

            test_cases = [
                ('box1', 100, 100, 200, 150),
                ('box2', 350, 100, 200, 150),
                ('box3', 100, 300, 200, 150),
            ]

            total_error = 0.0
            max_error = 0.0
            sub_pixel = 0

            print(f"\n  {'Element':<8} {'Expected':<20} {'Actual':<20} {'Error (px)':<15}")
            print(f"  {'-'*70}")

            for elem_id, exp_x, exp_y, exp_w, exp_h in test_cases:
                elem = next((e for e in structure.elements if e.element_id == elem_id), None)
                assert elem is not None, f"Element {elem_id} not found"

                x_err = abs(elem.bounding_box.x - exp_x)
                y_err = abs(elem.bounding_box.y - exp_y)
                w_err = abs(elem.bounding_box.width - exp_w)
                h_err = abs(elem.bounding_box.height - exp_h)

                pos_error = (x_err**2 + y_err**2)**0.5
                size_error = (w_err**2 + h_err**2)**0.5

                total_error += pos_error
                max_error = max(max_error, pos_error)

                if pos_error < 1.0:
                    sub_pixel += 1

                print(f"  {elem_id:<8} ({exp_x},{exp_y}) {exp_w}×{exp_h:<6}  "
                      f"({elem.bounding_box.x:.1f},{elem.bounding_box.y:.1f}) "
                      f"{elem.bounding_box.width:.1f}×{elem.bounding_box.height:.1f:<6}  "
                      f"pos={pos_error:.3f}")

                # Test finding at center
                cx, cy = elem.bounding_box.center_x, elem.bounding_box.center_y
                found = mapper.find_element_at_point(cx, cy)
                assert found is not None, f"Not found at center ({cx}, {cy})"
                assert found.element_id == elem_id, f"Wrong element at center"

            avg_error = total_error / len(test_cases)

            print(f"\n  Summary:")
            print(f"    Average position error: {avg_error:.3f} px")
            print(f"    Maximum position error: {max_error:.3f} px")
            print(f"    Sub-pixel accurate (<1px): {sub_pixel}/{len(test_cases)}")

            duration = time.time() - start_time

            self.results.append(TestResult(
                test_name="Coordinate Precision",
                passed=avg_error < 5.0,
                duration=duration,
                details=f"Avg: {avg_error:.3f}px, Max: {max_error:.3f}px",
                metrics={
                    'avg_error': avg_error,
                    'max_error': max_error,
                    'sub_pixel': sub_pixel,
                    'total': len(test_cases)
                }
            ))

            print(f"✓ PASSED ({duration:.2f}s)")

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

    def _test_scroll_handling(self, page):
        """Test 5: Scroll handling"""
        print("\n" + "─" * 80)
        print("TEST 5: Scroll Position Handling")
        print("─" * 80)

        start_time = time.time()

        try:
            html = """
            <!DOCTYPE html>
            <html>
            <body style="height: 3000px; margin: 0;">
                <div id="top" style="position: absolute; top: 100px; left: 100px;">Top</div>
                <div id="mid" style="position: absolute; top: 1500px; left: 100px;">Middle</div>
                <div id="bot" style="position: absolute; top: 2800px; left: 100px;">Bottom</div>
            </body>
            </html>
            """

            page.set_content(html)
            page.wait_for_load_state('domcontentloaded')

            scroll_tests = [0, 1000, 2000]
            passed = 0

            for scroll_y in scroll_tests:
                page.evaluate(f"window.scrollTo(0, {scroll_y})")
                time.sleep(0.1)

                extractor = DOMStructureExtractor(page)
                structure = extractor.extract()

                if abs(structure.scroll_y - scroll_y) < 5:
                    passed += 1
                    status = "✓"
                else:
                    status = "✗"

                print(f"  {status} Scroll {scroll_y}px → Detected {structure.scroll_y:.1f}px")

            duration = time.time() - start_time

            self.results.append(TestResult(
                test_name="Scroll Handling",
                passed=passed == len(scroll_tests),
                duration=duration,
                details=f"{passed}/{len(scroll_tests)} scroll positions detected accurately",
                metrics={'passed': passed, 'total': len(scroll_tests)}
            ))

            print(f"{'✓' if passed == len(scroll_tests) else '✗'} ({duration:.2f}s)")

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

    def _test_overlapping_elements(self, page):
        """Test 6: Overlapping elements"""
        print("\n" + "─" * 80)
        print("TEST 6: Overlapping Element Detection (Z-Index)")
        print("─" * 80)

        start_time = time.time()

        try:
            html = """
            <!DOCTYPE html>
            <html>
            <body style="margin: 0;">
                <div id="bottom" style="position: absolute; left: 100px; top: 100px;
                    width: 200px; height: 200px; background: red; z-index: 1;">Bottom</div>
                <div id="middle" style="position: absolute; left: 150px; top: 150px;
                    width: 200px; height: 200px; background: blue; z-index: 2;">Middle</div>
                <div id="top" style="position: absolute; left: 200px; top: 200px;
                    width: 200px; height: 200px; background: green; z-index: 3;">Top</div>
            </body>
            </html>
            """

            page.set_content(html)
            page.wait_for_load_state('domcontentloaded')

            extractor = DOMStructureExtractor(page)
            structure = extractor.extract()
            mapper = CoordinateMapper(structure)

            tests = [
                (250, 250, 'top'),
                (175, 175, 'middle'),
                (125, 125, 'bottom'),
            ]

            passed = 0
            for x, y, expected_id in tests:
                found = mapper.find_element_at_point(x, y)

                if found and found.element_id == expected_id:
                    passed += 1
                    status = "✓"
                else:
                    status = "✗"
                    found_id = found.element_id if found else "None"

                print(f"  {status} ({x},{y}): Expected '{expected_id}', Found '{found_id}'")

            duration = time.time() - start_time

            self.results.append(TestResult(
                test_name="Overlapping Elements",
                passed=passed == len(tests),
                duration=duration,
                details=f"{passed}/{len(tests)} correct z-index detections",
                metrics={'passed': passed, 'total': len(tests)}
            ))

            print(f"{'✓' if passed == len(tests) else '✗'} ({duration:.2f}s)")

        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name="Overlapping Elements",
                passed=False,
                duration=duration,
                details=str(e),
                metrics={}
            ))
            print(f"✗ FAILED: {e}")

    def _test_complex_layout(self, page):
        """Test 7: Complex layout with many elements"""
        print("\n" + "─" * 80)
        print("TEST 7: Complex Layout Performance")
        print("─" * 80)

        start_time = time.time()

        try:
            # Generate complex HTML with many elements
            items = '\n'.join([
                f'<div class="item" id="item{i}" style="margin: 5px; padding: 10px; border: 1px solid black;">'
                f'  <h3>Item {i}</h3>'
                f'  <p>Description for item {i}</p>'
                f'  <button id="btn{i}">Action {i}</button>'
                f'</div>'
                for i in range(50)
            ])

            html = f"""
            <!DOCTYPE html>
            <html>
            <body style="padding: 20px;">
                <h1>Complex Layout Test</h1>
                {items}
            </body>
            </html>
            """

            page.set_content(html)
            page.wait_for_load_state('domcontentloaded')

            extract_start = time.time()
            extractor = DOMStructureExtractor(page)
            structure = extractor.extract()
            extract_time = time.time() - extract_start

            # Verify extraction
            assert structure.total_elements > 200, "Too few elements extracted"

            # Test finding specific elements
            mapper = CoordinateMapper(structure)
            item25 = mapper.find_elements_by_text("Item 25", exact=True)
            assert len(item25) > 0, "Could not find Item 25"

            # Test clickable elements
            assert structure.clickable_elements >= 50, "Missing clickable elements"

            duration = time.time() - start_time

            print(f"  Total elements: {structure.total_elements}")
            print(f"  Extraction time: {extract_time:.2f}s")
            print(f"  Interactive elements: {len(structure.interactive_elements)}")
            print(f"  Elements/second: {structure.total_elements / extract_time:.0f}")

            self.results.append(TestResult(
                test_name="Complex Layout Performance",
                passed=True,
                duration=duration,
                details=f"Extracted {structure.total_elements} elements in {extract_time:.2f}s",
                metrics={
                    'total_elements': structure.total_elements,
                    'extraction_time': extract_time,
                    'elements_per_second': structure.total_elements / extract_time
                }
            ))

            print(f"✓ PASSED ({duration:.2f}s)")

        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                test_name="Complex Layout Performance",
                passed=False,
                duration=duration,
                details=str(e),
                metrics={}
            ))
            print(f"✗ FAILED: {e}")

    def _generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 80)
        print("TEST REPORT")
        print("=" * 80)

        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        total_time = sum(r.duration for r in self.results)

        print(f"\nSummary:")
        print(f"  Total Tests: {total}")
        print(f"  Passed: {passed} ✓ ({passed/total*100:.1f}%)")
        print(f"  Failed: {failed} ✗ ({failed/total*100:.1f}%)")
        print(f"  Total Duration: {total_time:.2f}s")

        if passed == total:
            print(f"\n  🎉 ALL TESTS PASSED!")

        # Save detailed report
        report = {
            'timestamp': time.time(),
            'summary': {
                'total': total,
                'passed': passed,
                'failed': failed,
                'pass_rate': passed / total * 100,
                'duration': total_time
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

        with open('/tmp/dom_accuracy_report.json', 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n✓ Full report: /tmp/dom_accuracy_report.json")
        print("=" * 80)


if __name__ == '__main__':
    tester = LocalDOMTester()
    tester.run_all_tests()

    # Exit with appropriate code
    exit(0 if all(r.passed for r in tester.results) else 1)
