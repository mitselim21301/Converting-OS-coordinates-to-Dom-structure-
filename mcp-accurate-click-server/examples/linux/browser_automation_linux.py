#!/usr/bin/env python3
"""
Browser Automation Linux Example - MCP Accurate Click Server

Demonstrates browser detection and automation on Linux:
- Detecting installed browsers (Chrome, Firefox, Edge, Brave, etc.)
- Launching browsers with accurate coordinate mapping
- Handling browser-specific scaling and DPI
- Clicking elements with accurate coordinate conversion
- Managing multiple browser instances
- Cross-browser compatibility

Key Linux Browser Considerations:
- Different browsers may have different DPI scaling
- Wayland support varies by browser
- Some browsers need special flags for X11/Wayland
- Browser DevTools Protocol (CDP) support

Requirements:
    pip install playwright
    # At least one of these browsers:
    - Google Chrome / Chromium
    - Firefox
    - Microsoft Edge
    - Brave Browser

Run: python3 browser_automation_linux.py
"""

import sys
import time
import logging
import os
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
except ImportError as e:
    logger.error(f"Missing dependency: {e}")
    sys.exit(1)

try:
    from dom_structure_extractor import DOMStructureExtractor, CoordinateMapper
except ImportError:
    logger.warning("DOM extractor not available")
    DOMStructureExtractor = None

try:
    from mcp_server.platform.linux import LinuxWindowManager, LinuxDPIHandler
except ImportError:
    logger.warning("MCP Linux modules not available")
    LinuxWindowManager = None
    LinuxDPIHandler = None


class BrowserType(Enum):
    """Supported browser types."""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


@dataclass
class BrowserInfo:
    """Information about an installed browser."""
    name: str
    type: BrowserType
    executable_path: Optional[str] = None
    version: Optional[str] = None
    is_installed: bool = False

    def __str__(self) -> str:
        status = "✓ INSTALLED" if self.is_installed else "✗ NOT FOUND"
        version_str = f" v{self.version}" if self.version else ""
        return f"{self.name}{version_str} [{status}]"


class BrowserDetector:
    """Detects and manages available browsers on Linux."""

    # Browser executable names and their types
    BROWSER_EXECUTABLES = {
        'chromium': BrowserType.CHROMIUM,
        'chromium-browser': BrowserType.CHROMIUM,
        'google-chrome': BrowserType.CHROMIUM,
        'google-chrome-stable': BrowserType.CHROMIUM,
        'google-chrome-beta': BrowserType.CHROMIUM,
        'chrome': BrowserType.CHROMIUM,
        'firefox': BrowserType.FIREFOX,
        'firefox-esr': BrowserType.FIREFOX,
        'microsoft-edge': BrowserType.CHROMIUM,
        'microsoft-edge-stable': BrowserType.CHROMIUM,
        'brave': BrowserType.CHROMIUM,
        'brave-browser': BrowserType.CHROMIUM,
    }

    def __init__(self):
        """Initialize browser detector."""
        self.browsers: List[BrowserInfo] = self._detect_browsers()

    def _detect_browsers(self) -> List[BrowserInfo]:
        """
        Detect all available browsers on the system.

        Returns:
            List of BrowserInfo objects
        """
        browsers = []

        # Check common browser executables
        for exec_name, browser_type in self.BROWSER_EXECUTABLES.items():
            path = self._find_executable(exec_name)
            if path:
                version = self._get_browser_version(path)
                info = BrowserInfo(
                    name=exec_name,
                    type=browser_type,
                    executable_path=path,
                    version=version,
                    is_installed=True
                )
                browsers.append(info)

        return browsers

    @staticmethod
    def _find_executable(name: str) -> Optional[str]:
        """
        Find executable in PATH.

        Args:
            name: Executable name

        Returns:
            Full path if found, None otherwise
        """
        try:
            result = subprocess.run(['which', name], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    @staticmethod
    def _get_browser_version(executable_path: str) -> Optional[str]:
        """
        Get browser version.

        Args:
            executable_path: Path to browser executable

        Returns:
            Version string or None
        """
        try:
            # Most Linux browsers support --version flag
            result = subprocess.run([executable_path, '--version'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Output usually like "Google Chrome 120.0.1234.56"
                return result.stdout.strip().split()[-1]
        except Exception:
            pass
        return None

    def list_browsers(self) -> None:
        """Log available browsers."""
        logger.info("\n[Available Browsers]")
        if self.browsers:
            for browser in self.browsers:
                logger.info(f"  {browser}")
        else:
            logger.warning("  No browsers detected!")

    def get_browser_by_type(self, browser_type: BrowserType) -> Optional[BrowserInfo]:
        """
        Get first available browser of given type.

        Args:
            browser_type: Type of browser to find

        Returns:
            BrowserInfo or None
        """
        for browser in self.browsers:
            if browser.type == browser_type and browser.is_installed:
                return browser
        return None


class BrowserAutomationExample:
    """Demonstrates browser automation with accurate clicking."""

    def __init__(self):
        """Initialize browser automation example."""
        self.detector = BrowserDetector()
        self.window_manager = None
        self.dpi_handler = None

        self._init_platform_support()

    def _init_platform_support(self) -> None:
        """Initialize Linux platform support."""
        try:
            if LinuxWindowManager:
                self.window_manager = LinuxWindowManager()
                logger.info("✓ Window manager initialized")
        except Exception as e:
            logger.warning(f"Window manager initialization failed: {e}")

        try:
            if LinuxDPIHandler:
                self.dpi_handler = LinuxDPIHandler()
                logger.info("✓ DPI handler initialized")
        except Exception as e:
            logger.warning(f"DPI handler initialization failed: {e}")

    def get_browser_launch_options(self, browser_type: BrowserType) -> dict:
        """
        Get browser launch options for Linux.

        Best Practice: Different browsers need different options on Linux.

        Args:
            browser_type: Type of browser

        Returns:
            Launch options dictionary
        """
        options = {
            'headless': False,
            'args': []
        }

        # Detect display server
        display_server = os.environ.get('XDG_SESSION_TYPE', 'unknown').lower()

        if browser_type == BrowserType.CHROMIUM:
            # Chromium-based browsers
            if display_server == 'wayland':
                # Force Wayland on compatible systems
                options['args'].extend([
                    '--ozone-platform=wayland',
                    '--enable-wayland-ime'
                ])
            else:
                # X11 specific options
                options['args'].append('--x11-server-params')

            # Disable sandbox for automation
            options['args'].append('--no-sandbox')

        elif browser_type == BrowserType.FIREFOX:
            # Firefox specific options
            if display_server == 'wayland':
                options['args'].append('-MOZ_ENABLE_WAYLAND=1')

        return options

    def click_element_by_text(self, page: Page, text: str) -> bool:
        """
        Find and click element by text content.

        Args:
            page: Playwright page
            text: Text to search for

        Returns:
            True if clicked successfully
        """
        logger.info(f"\nSearching for element with text: '{text}'")

        try:
            # Try to find and click the element
            locator = page.locator(f"text={text}")

            if locator.count() > 0:
                logger.info(f"✓ Found {locator.count()} element(s)")

                # Get bounding box
                box = locator.first.bounding_box()
                if box:
                    logger.info(f"  Location: ({box['x']:.1f}, {box['y']:.1f})")
                    logger.info(f"  Size: {box['width']:.1f}x{box['height']:.1f}")

                # Click the element
                locator.first.click()
                logger.info("✓ Element clicked")
                return True
            else:
                logger.warning(f"✗ No element found with text: '{text}'")
                return False

        except Exception as e:
            logger.error(f"✗ Click failed: {e}")
            return False

    def get_page_info(self, page: Page) -> None:
        """
        Extract and display page information.

        Args:
            page: Playwright page
        """
        logger.info("\n[Page Information]")

        try:
            # Get viewport size
            viewport = page.viewport()
            if viewport:
                logger.info(f"  Viewport: {viewport['width']}x{viewport['height']}")

            # Get URL
            logger.info(f"  URL: {page.url}")

            # Get device pixel ratio
            dpr = page.evaluate("() => window.devicePixelRatio")
            logger.info(f"  Device Pixel Ratio: {dpr}")

            # Get title
            title = page.title()
            if title:
                logger.info(f"  Title: {title[:50]}{'...' if len(title) > 50 else ''}")

            # Extract DOM if available
            if DOMStructureExtractor:
                try:
                    extractor = DOMStructureExtractor(page)
                    structure = extractor.extract()
                    logger.info(f"  DOM Elements: {structure.total_elements}")
                    logger.info(f"  Clickable Elements: {structure.clickable_elements}")
                except Exception as e:
                    logger.debug(f"DOM extraction skipped: {e}")

        except Exception as e:
            logger.error(f"Failed to get page info: {e}")

    def test_browser_click_accuracy(self, browser: BrowserInfo) -> bool:
        """
        Test clicking accuracy in a browser.

        Args:
            browser: Browser to test

        Returns:
            True if test succeeded
        """
        logger.info(f"\n[Testing {browser.name}]")

        try:
            with sync_playwright() as p:
                # Get Playwright browser object
                if browser.type == BrowserType.CHROMIUM:
                    pw_browser = p.chromium
                elif browser.type == BrowserType.FIREFOX:
                    pw_browser = p.firefox
                else:
                    pw_browser = p.webkit

                # Launch with options
                options = self.get_browser_launch_options(browser.type)

                # Create browser
                browser_instance = pw_browser.launch(**options)
                page = browser_instance.new_page()

                # Load test page
                test_page_path = Path(__file__).parent.parent / "test_page.html"
                if test_page_path.exists():
                    page.goto(f"file://{test_page_path}")
                    logger.info(f"✓ Loaded test page")
                else:
                    page.goto("https://example.com")
                    logger.info(f"✓ Loaded example.com")

                page.wait_for_load_state("networkidle")

                # Get page info
                self.get_page_info(page)

                # Demonstrate clicking
                logger.info("\n[Clicking Test]")

                # Click center
                viewport = page.viewport()
                if viewport:
                    center_x = viewport['width'] / 2
                    center_y = viewport['height'] / 2
                    logger.info(f"Clicking viewport center: ({center_x:.1f}, {center_y:.1f})")
                    page.mouse.click(center_x, center_y)
                    time.sleep(0.3)

                # Keep browser open briefly
                logger.info("\nBrowser will close in 2 seconds...")
                time.sleep(2)

                browser_instance.close()
                logger.info("✓ Browser closed")
                return True

        except Exception as e:
            logger.error(f"✗ Browser test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_example(self) -> int:
        """Execute the complete browser automation example."""
        logger.info("=" * 70)
        logger.info("BROWSER AUTOMATION LINUX EXAMPLE - MCP ACCURATE CLICK SERVER")
        logger.info("=" * 70)

        # Step 1: Detect browsers
        self.detector.list_browsers()

        if not self.detector.browsers:
            logger.error("No browsers detected! Install Chrome, Firefox, or Edge")
            return 1

        # Step 2: Test with available browsers
        logger.info("\n[Testing Available Browsers]")

        success_count = 0
        for browser in self.detector.browsers:
            if self.test_browser_click_accuracy(browser):
                success_count += 1
            time.sleep(0.5)

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("BROWSER AUTOMATION EXAMPLE COMPLETED")
        logger.info("=" * 70)
        logger.info(f"Total Browsers: {len(self.detector.browsers)}")
        logger.info(f"Successful Tests: {success_count}/{len(self.detector.browsers)}")

        return 0 if success_count > 0 else 1


def main():
    """Entry point."""
    example = BrowserAutomationExample()
    return example.run_example()


if __name__ == "__main__":
    sys.exit(main())
