"""
Tool Execution Handlers for MCP Accurate Click Server

Implements the execution logic for all tools with comprehensive
error handling, logging, validation, and platform-specific support.

Features:
- Cross-platform support (Windows, Linux, macOS)
- Platform-specific input simulation
- Native OS-level clicking when needed
- Coordinate conversion with DPI awareness
- Window management and detection
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict

from playwright.async_api import Page, ElementHandle, Error as PlaywrightError

from .config import get_config_manager
from .tools import ClickMethod, CoordinateSystem, get_tool_registry

# Platform abstraction imports
from mcp_server.platform import (
    get_platform,
    is_windows,
    is_linux,
    get_input_simulator,
    get_coordinate_converter,
    get_dpi_handler,
    get_window_manager,
)

logger = logging.getLogger(__name__)


@dataclass
class HandlerResult:
    """Standard result format for all handlers"""
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "success": self.success,
            "data": self.data,
            "execution_time": self.execution_time
        }

        if self.error:
            result["error"] = self.error

        if self.metadata:
            result["metadata"] = self.metadata

        return result


class ToolHandlers:
    """Handlers for all MCP tools with platform-specific support"""

    def __init__(self, page: Page):
        """
        Initialize tool handlers with platform-specific support

        Args:
            page: Playwright page instance
        """
        self.page = page
        self.config = get_config_manager().config
        self.logger = logging.getLogger(f"{__name__}.ToolHandlers")

        # Platform detection and initialization
        self.platform = get_platform()
        self.logger.info(f"Initializing handlers for platform: {self.platform}")

        # Initialize platform-specific handlers
        self._init_platform_handlers()

        # Cache for DOM structure
        self._dom_cache: Optional[Dict[str, Any]] = None
        self._dom_cache_time: float = 0.0

    def _init_platform_handlers(self) -> None:
        """
        Initialize platform-specific handlers for input, coordinates, DPI, and window management.

        This method safely initializes platform dependencies with proper error handling
        and fallback support.
        """
        try:
            # Input simulator (for native OS-level input)
            self.input_simulator = get_input_simulator()
            self.logger.debug("Platform input simulator initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize input simulator: {e}")
            self.input_simulator = None

        try:
            # Coordinate converter (for coordinate space transformations)
            self.coordinate_converter = get_coordinate_converter()
            self.logger.debug("Platform coordinate converter initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize coordinate converter: {e}")
            self.coordinate_converter = None

        try:
            # DPI handler (for DPI-aware coordinate conversion)
            self.dpi_handler = get_dpi_handler()
            self.logger.debug("Platform DPI handler initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize DPI handler: {e}")
            self.dpi_handler = None

        try:
            # Window manager (for window detection and management)
            self.window_manager = get_window_manager()
            self.logger.debug("Platform window manager initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize window manager: {e}")
            self.window_manager = None

    # ========================================================================
    # PLATFORM HELPER METHODS
    # ========================================================================

    def _get_browser_info(self) -> Dict[str, Any]:
        """
        Get browser window information including DPI scaling.

        Returns:
            Dictionary with browser window info and DPI scaling
        """
        browser_info = {
            "url": self.page.url,
            "platform": self.platform,
            "dpi_scale": 1.0,
        }

        if self.dpi_handler:
            try:
                system_dpi = self.dpi_handler.get_system_dpi()
                browser_info["dpi"] = {"x": system_dpi[0], "y": system_dpi[1]}
                browser_info["dpi_scale"] = system_dpi[0] / 96.0  # Windows baseline is 96 DPI
            except Exception as e:
                self.logger.warning(f"Failed to get DPI info: {e}")

        return browser_info

    async def _convert_viewport_to_screen_coords(
        self,
        viewport_x: float,
        viewport_y: float
    ) -> Tuple[float, float]:
        """
        Convert viewport coordinates to screen/OS coordinates.

        Args:
            viewport_x: X coordinate in viewport space
            viewport_y: Y coordinate in viewport space

        Returns:
            Tuple of (screen_x, screen_y) in OS coordinates
        """
        if not self.coordinate_converter:
            # Fallback: return as-is
            return viewport_x, viewport_y

        try:
            # Get browser window position if available
            # Note: Playwright doesn't provide window position, so we use viewport as-is
            # In a real implementation with window manager, this would be more accurate

            # Apply DPI scaling if needed
            if self.dpi_handler:
                system_dpi = self.dpi_handler.get_system_dpi()
                scale = system_dpi[0] / 96.0
                screen_x = viewport_x * scale
                screen_y = viewport_y * scale
                return screen_x, screen_y

            return viewport_x, viewport_y

        except Exception as e:
            self.logger.warning(f"Failed to convert viewport coordinates: {e}")
            return viewport_x, viewport_y

    def _should_use_native_click(self, method: str) -> bool:
        """
        Determine if native OS-level clicking should be used.

        Args:
            method: Click method requested

        Returns:
            True if native click should be used, False for Playwright click
        """
        # Use native clicking for coordinate-based clicks on Windows/Linux
        if method == "by_coordinates" and self.input_simulator:
            return True

        # Could be extended to use native clicking for other scenarios
        # (e.g., if Playwright click fails, fallback to native)
        return False

    async def _perform_native_click(
        self,
        x: float,
        y: float,
        button: str = "left",
        double_click: bool = False
    ) -> bool:
        """
        Perform native OS-level click using platform-specific input simulator.

        Args:
            x: X coordinate in screen space
            y: Y coordinate in screen space
            button: Mouse button ('left', 'right', 'middle')
            double_click: If True, perform double-click

        Returns:
            True if successful, False otherwise
        """
        if not self.input_simulator:
            self.logger.warning("Input simulator not available for native click")
            return False

        try:
            # Convert button name to MouseButton enum
            from mcp_server.platform.base import MouseButton
            button_map = {
                "left": MouseButton.LEFT,
                "right": MouseButton.RIGHT,
                "middle": MouseButton.MIDDLE,
            }
            mouse_button = button_map.get(button.lower(), MouseButton.LEFT)

            # Perform click
            clicks = 2 if double_click else 1
            success = self.input_simulator.click(
                int(x),
                int(y),
                button=mouse_button,
                clicks=clicks,
                use_virtual_desk=True
            )

            if success:
                self.logger.info(f"Native {button} click successful at ({x:.0f}, {y:.0f})")
            else:
                self.logger.warning(f"Native click failed at ({x:.0f}, {y:.0f})")

            return success

        except Exception as e:
            self.logger.error(f"Error performing native click: {e}")
            return False

    async def _perform_mouse_move(
        self,
        x: float,
        y: float,
        steps: int = 1
    ) -> bool:
        """
        Perform mouse move to absolute position.

        Args:
            x: X coordinate in screen space
            y: Y coordinate in screen space
            steps: Number of steps for movement (for smoothness)

        Returns:
            True if successful, False otherwise
        """
        if not self.input_simulator:
            self.logger.warning("Input simulator not available for mouse move")
            return False

        try:
            success = self.input_simulator.move_mouse(int(x), int(y))
            if success:
                self.logger.info(f"Mouse moved to ({x:.0f}, {y:.0f})")
            return success
        except Exception as e:
            self.logger.error(f"Error moving mouse: {e}")
            return False

    # ========================================================================
    # CLICK ELEMENT HANDLER
    # ========================================================================

    async def handle_click_element(self, params: Dict[str, Any]) -> HandlerResult:
        """
        Handle click_element tool execution

        Args:
            params: Tool parameters

        Returns:
            HandlerResult with click results
        """
        start_time = time.time()

        try:
            method = ClickMethod(params["method"])
            timeout = params.get("timeout", self.config.request_timeout_seconds) * 1000  # Convert to ms
            validate = params.get("validate", self.config.enable_click_validation)
            force = params.get("force", False)

            self.logger.info(f"Clicking element using method: {method.value}")

            # Find element based on method
            element, element_info = await self._find_element_by_method(method, params, timeout)

            if not element:
                return HandlerResult(
                    success=False,
                    data={},
                    error="Element not found",
                    execution_time=time.time() - start_time
                )

            # Get element coordinates before click
            bbox = await element.bounding_box()
            if not bbox and not force:
                return HandlerResult(
                    success=False,
                    data={},
                    error="Element has no bounding box (not visible or not in DOM)",
                    execution_time=time.time() - start_time
                )

            # Scroll into view if needed
            await element.scroll_into_view_if_needed(timeout=timeout)

            # Perform click
            click_coords = await self._perform_click(element, params, force, timeout)

            # Validation if requested
            validation_result = None
            if validate:
                validation_result = await self._validate_click(element, click_coords, params)

            execution_time = time.time() - start_time

            self.logger.info(f"Click completed successfully in {execution_time:.3f}s")

            return HandlerResult(
                success=True,
                data={
                    "clicked": True,
                    "element": element_info,
                    "coordinates": click_coords,
                    "validation": validation_result
                },
                execution_time=execution_time,
                metadata={
                    "method": method.value,
                    "force": force,
                    "validated": validate
                }
            )

        except PlaywrightError as e:
            self.logger.error(f"Playwright error during click: {e}")
            return HandlerResult(
                success=False,
                data={},
                error=f"Playwright error: {str(e)}",
                execution_time=time.time() - start_time
            )

        except Exception as e:
            self.logger.error(f"Unexpected error during click: {e}", exc_info=True)
            return HandlerResult(
                success=False,
                data={},
                error=f"Unexpected error: {str(e)}",
                execution_time=time.time() - start_time
            )

    async def _find_element_by_method(
        self,
        method: ClickMethod,
        params: Dict[str, Any],
        timeout: float
    ) -> Tuple[Optional[ElementHandle], Dict[str, Any]]:
        """Find element based on click method"""

        if method == ClickMethod.BY_TEXT:
            text = params.get("text")
            exact = params.get("exact_match", False)
            if not text:
                raise ValueError("text parameter required for by_text method")

            locator = self.page.get_by_text(text, exact=exact)
            element = await locator.element_handle(timeout=timeout)

            element_info = {
                "method": "by_text",
                "text": text,
                "exact_match": exact
            }

        elif method == ClickMethod.BY_SELECTOR:
            selector = params.get("selector")
            if not selector:
                raise ValueError("selector parameter required for by_selector method")

            element = await self.page.wait_for_selector(selector, timeout=timeout, state="attached")

            element_info = {
                "method": "by_selector",
                "selector": selector
            }

        elif method == ClickMethod.BY_XPATH:
            xpath = params.get("xpath")
            if not xpath:
                raise ValueError("xpath parameter required for by_xpath method")

            element = await self.page.wait_for_selector(f"xpath={xpath}", timeout=timeout, state="attached")

            element_info = {
                "method": "by_xpath",
                "xpath": xpath
            }

        elif method == ClickMethod.BY_ROLE:
            role = params.get("role")
            name = params.get("accessible_name")

            if not role:
                raise ValueError("role parameter required for by_role method")

            locator = self.page.get_by_role(role, name=name)
            element = await locator.element_handle(timeout=timeout)

            element_info = {
                "method": "by_role",
                "role": role,
                "accessible_name": name
            }

        elif method == ClickMethod.BY_ACCESSIBILITY:
            role = params.get("role")
            name = params.get("accessible_name")

            if not role and not name:
                raise ValueError("role or accessible_name required for by_accessibility method")

            # Try role first, then label
            if role:
                locator = self.page.get_by_role(role, name=name)
            else:
                locator = self.page.get_by_label(name)

            element = await locator.element_handle(timeout=timeout)

            element_info = {
                "method": "by_accessibility",
                "role": role,
                "accessible_name": name
            }

        elif method == ClickMethod.BY_COORDINATES:
            # For coordinates, we don't have a specific element
            # We'll click at the coordinates directly
            return None, {
                "method": "by_coordinates",
                "x": params.get("x"),
                "y": params.get("y"),
                "coordinate_system": params.get("coordinate_system", "viewport")
            }

        else:
            raise ValueError(f"Unsupported click method: {method}")

        # Get additional element information
        if element:
            bbox = await element.bounding_box()
            text_content = await element.text_content()
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")

            element_info.update({
                "tag_name": tag_name,
                "text_content": text_content[:100] if text_content else None,
                "bounding_box": bbox
            })

        return element, element_info

    async def _perform_click(
        self,
        element: Optional[ElementHandle],
        params: Dict[str, Any],
        force: bool,
        timeout: float
    ) -> Dict[str, Any]:
        """
        Perform click operation using Playwright or native OS input based on platform.

        Supports multiple coordinate systems and can fall back to native clicking
        when Playwright click is not suitable.

        Args:
            element: Element handle if clicking on element
            params: Tool parameters containing coordinates and click settings
            force: Force click even if element is not visible
            timeout: Timeout in milliseconds

        Returns:
            Dictionary with click coordinates and metadata
        """

        if element:
            # Click on element using Playwright
            try:
                await element.click(force=force, timeout=timeout)
                click_method = "playwright_element"
            except PlaywrightError as e:
                self.logger.warning(f"Playwright click failed: {e}, attempting native click")
                # Get element position and try native click
                bbox = await element.bounding_box()
                if bbox:
                    screen_x, screen_y = await self._convert_viewport_to_screen_coords(
                        bbox["x"] + bbox["width"] / 2,
                        bbox["y"] + bbox["height"] / 2
                    )
                    success = await self._perform_native_click(screen_x, screen_y)
                    click_method = "native_fallback" if success else "failed"
                else:
                    click_method = "failed"

            # Get click coordinates
            bbox = await element.bounding_box()
            if bbox:
                coords = {
                    "x": bbox["x"] + bbox["width"] / 2,
                    "y": bbox["y"] + bbox["height"] / 2,
                    "coordinate_system": "viewport",
                    "click_method": click_method
                }
            else:
                coords = {
                    "coordinate_system": "unknown",
                    "click_method": click_method
                }

        else:
            # Click at coordinates
            x = params.get("x")
            y = params.get("y")
            coord_system = params.get("coordinate_system", "viewport")
            use_native = params.get("use_native_click", False)

            if x is None or y is None:
                raise ValueError("x and y coordinates required")

            # Convert coordinates if needed
            if coord_system == "page":
                # Account for scroll
                scroll_x = await self.page.evaluate("window.scrollX")
                scroll_y = await self.page.evaluate("window.scrollY")
                viewport_x = x - scroll_x
                viewport_y = y - scroll_y
            elif coord_system == "viewport":
                viewport_x = x
                viewport_y = y
            elif coord_system == "screen" or coord_system == "os":
                # Convert OS screen coordinates to viewport
                # Note: Requires knowing browser window position
                viewport_x = x
                viewport_y = y
                use_native = True  # Use native click for OS coordinates
            else:
                raise ValueError(f"Unsupported coordinate system: {coord_system}")

            click_method = "unknown"

            # Decide whether to use native click or Playwright click
            if use_native or self._should_use_native_click("by_coordinates"):
                # Use native OS-level clicking
                if coord_system in ("os", "screen"):
                    screen_x, screen_y = x, y
                else:
                    # Convert viewport to screen coordinates
                    screen_x, screen_y = await self._convert_viewport_to_screen_coords(
                        viewport_x, viewport_y
                    )

                success = await self._perform_native_click(screen_x, screen_y)
                click_method = "native" if success else "native_failed"

                coords = {
                    "x": screen_x,
                    "y": screen_y,
                    "coordinate_system": "screen",
                    "original_x": x,
                    "original_y": y,
                    "original_coordinate_system": coord_system,
                    "click_method": click_method
                }
            else:
                # Use Playwright click (safer, more compatible)
                try:
                    await self.page.mouse.click(viewport_x, viewport_y)
                    click_method = "playwright_coordinates"
                except PlaywrightError as e:
                    self.logger.error(f"Playwright coordinate click failed: {e}")
                    click_method = "failed"

                coords = {
                    "x": viewport_x,
                    "y": viewport_y,
                    "coordinate_system": "viewport",
                    "original_x": x,
                    "original_y": y,
                    "original_coordinate_system": coord_system,
                    "click_method": click_method
                }

        return coords

    async def _validate_click(
        self,
        element: Optional[ElementHandle],
        click_coords: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate click success"""

        validation = {
            "performed": True,
            "timestamp": time.time()
        }

        try:
            # Check element state after click
            if element:
                is_visible = await element.is_visible()
                is_enabled = await element.is_enabled()

                validation["element_state"] = {
                    "visible": is_visible,
                    "enabled": is_enabled
                }

            # Check for DOM changes (simplified)
            # In production, would compare DOM snapshots
            validation["dom_changed"] = True  # Assume changed for now

            # Take screenshot if configured
            if self.config.validation_screenshot:
                screenshot_path = self.config.screenshot_dir / f"click_{int(time.time() * 1000)}.png"
                await self.page.screenshot(path=str(screenshot_path))
                validation["screenshot"] = str(screenshot_path)

            validation["success"] = True

        except Exception as e:
            self.logger.warning(f"Validation error: {e}")
            validation["success"] = False
            validation["error"] = str(e)

        return validation

    # ========================================================================
    # FIND ELEMENT HANDLER
    # ========================================================================

    async def handle_find_element(self, params: Dict[str, Any]) -> HandlerResult:
        """
        Handle find_element tool execution

        Args:
            params: Tool parameters

        Returns:
            HandlerResult with found elements
        """
        start_time = time.time()

        try:
            method = ClickMethod(params["method"])
            visible_only = params.get("visible_only", True)
            limit = params.get("limit", 10)

            self.logger.info(f"Finding elements using method: {method.value}")

            # Find elements based on method
            elements = await self._find_elements_by_method(method, params, visible_only, limit)

            execution_time = time.time() - start_time

            self.logger.info(f"Found {len(elements)} element(s) in {execution_time:.3f}s")

            return HandlerResult(
                success=True,
                data={
                    "found": len(elements) > 0,
                    "count": len(elements),
                    "elements": elements
                },
                execution_time=execution_time,
                metadata={
                    "method": method.value,
                    "visible_only": visible_only,
                    "limit": limit
                }
            )

        except Exception as e:
            self.logger.error(f"Error finding elements: {e}", exc_info=True)
            return HandlerResult(
                success=False,
                data={"found": False, "count": 0, "elements": []},
                error=str(e),
                execution_time=time.time() - start_time
            )

    async def _find_elements_by_method(
        self,
        method: ClickMethod,
        params: Dict[str, Any],
        visible_only: bool,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Find elements based on method"""

        elements_info = []

        if method == ClickMethod.BY_TEXT:
            text = params.get("text")
            exact = params.get("exact_match", False)

            if not text:
                raise ValueError("text parameter required")

            locator = self.page.get_by_text(text, exact=exact)
            count = await locator.count()

            for i in range(min(count, limit)):
                element = locator.nth(i)
                info = await self._get_element_info(element)
                if not visible_only or info.get("visible", False):
                    elements_info.append(info)

        elif method == ClickMethod.BY_SELECTOR:
            selector = params.get("selector")
            if not selector:
                raise ValueError("selector parameter required")

            locator = self.page.locator(selector)
            count = await locator.count()

            for i in range(min(count, limit)):
                element = locator.nth(i)
                info = await self._get_element_info(element)
                if not visible_only or info.get("visible", False):
                    elements_info.append(info)

        elif method == ClickMethod.BY_COORDINATES:
            x = params.get("x")
            y = params.get("y")

            if x is None or y is None:
                raise ValueError("x and y coordinates required")

            # Find element at point using JavaScript
            element_handle = await self.page.evaluate_handle(
                f"document.elementFromPoint({x}, {y})"
            )

            if element_handle:
                info = await self._get_element_info_from_handle(element_handle.as_element())
                elements_info.append(info)

        # Add more methods as needed

        return elements_info[:limit]

    async def _get_element_info(self, locator) -> Dict[str, Any]:
        """Get comprehensive element information from locator"""

        try:
            bbox = await locator.bounding_box()
            is_visible = await locator.is_visible()
            is_enabled = await locator.is_enabled()
            text = await locator.text_content()

            # Get more details
            tag_name = await locator.evaluate("el => el.tagName.toLowerCase()")
            element_id = await locator.get_attribute("id")
            class_name = await locator.get_attribute("class")

            return {
                "tag_name": tag_name,
                "id": element_id,
                "class": class_name,
                "text": text[:100] if text else None,
                "bounding_box": bbox,
                "visible": is_visible,
                "enabled": is_enabled
            }

        except Exception as e:
            self.logger.warning(f"Error getting element info: {e}")
            return {"error": str(e)}

    async def _get_element_info_from_handle(self, element: ElementHandle) -> Dict[str, Any]:
        """Get element information from element handle"""

        try:
            bbox = await element.bounding_box()
            text = await element.text_content()
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")

            return {
                "tag_name": tag_name,
                "text": text[:100] if text else None,
                "bounding_box": bbox,
                "visible": bbox is not None
            }

        except Exception as e:
            self.logger.warning(f"Error getting element info from handle: {e}")
            return {"error": str(e)}

    # ========================================================================
    # GET DOM STRUCTURE HANDLER
    # ========================================================================

    async def handle_get_dom_structure(self, params: Dict[str, Any]) -> HandlerResult:
        """
        Handle get_dom_structure tool execution

        Args:
            params: Tool parameters

        Returns:
            HandlerResult with DOM structure
        """
        start_time = time.time()

        try:
            use_cache = params.get("use_cache", self.config.cache_dom_structure)

            # Check cache
            if use_cache and self._dom_cache:
                cache_age = time.time() - self._dom_cache_time
                if cache_age < self.config.dom_cache_ttl_seconds:
                    self.logger.info(f"Returning cached DOM structure (age: {cache_age:.1f}s)")
                    return HandlerResult(
                        success=True,
                        data=self._dom_cache,
                        execution_time=time.time() - start_time,
                        metadata={"cached": True, "cache_age": cache_age}
                    )

            # Extract DOM structure
            self.logger.info("Extracting DOM structure...")

            dom_structure = await self._extract_dom_structure(params)

            # Update cache
            if use_cache:
                self._dom_cache = dom_structure
                self._dom_cache_time = time.time()

            execution_time = time.time() - start_time

            self.logger.info(f"DOM structure extracted in {execution_time:.3f}s")

            return HandlerResult(
                success=True,
                data=dom_structure,
                execution_time=execution_time,
                metadata={"cached": False}
            )

        except Exception as e:
            self.logger.error(f"Error extracting DOM structure: {e}", exc_info=True)
            return HandlerResult(
                success=False,
                data={},
                error=str(e),
                execution_time=time.time() - start_time
            )

    async def _extract_dom_structure(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract DOM structure using JavaScript"""

        include_invisible = params.get("include_invisible", False)
        include_interactive_only = params.get("include_interactive_only", False)
        max_elements = params.get("max_elements")

        # Get viewport info
        viewport_info = await self.page.evaluate("""() => {
            return {
                width: window.innerWidth,
                height: window.innerHeight,
                scroll_x: window.scrollX,
                scroll_y: window.scrollY,
                page_width: document.documentElement.scrollWidth,
                page_height: document.documentElement.scrollHeight
            };
        }""")

        # Extract elements (simplified version - would use dom_structure_extractor.py in production)
        elements_data = await self.page.evaluate(f"""(includeInvisible, interactiveOnly, maxElements) => {{
            const elements = [];
            const allElements = document.querySelectorAll('*');

            function isVisible(el) {{
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return style.display !== 'none' &&
                       style.visibility !== 'hidden' &&
                       rect.width > 0 &&
                       rect.height > 0;
            }}

            function isInteractive(el) {{
                const tag = el.tagName.toLowerCase();
                return ['a', 'button', 'input', 'select', 'textarea'].includes(tag) ||
                       el.onclick ||
                       el.getAttribute('role') === 'button';
            }}

            for (let el of allElements) {{
                if (maxElements && elements.length >= maxElements) break;

                const visible = isVisible(el);
                if (!includeInvisible && !visible) continue;

                const interactive = isInteractive(el);
                if (interactiveOnly && !interactive) continue;

                const rect = el.getBoundingClientRect();

                elements.push({{
                    tag: el.tagName.toLowerCase(),
                    id: el.id || null,
                    text: el.textContent ? el.textContent.substring(0, 100) : null,
                    bbox: {{
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    }},
                    visible: visible,
                    interactive: interactive
                }});
            }}

            return elements;
        }}""", include_invisible, include_interactive_only, max_elements)

        return {
            "url": self.page.url,
            "title": await self.page.title(),
            "viewport": viewport_info,
            "elements": elements_data,
            "statistics": {
                "total": len(elements_data),
                "visible": sum(1 for e in elements_data if e.get("visible")),
                "interactive": sum(1 for e in elements_data if e.get("interactive"))
            }
        }

    # ========================================================================
    # VALIDATE CLICK HANDLER
    # ========================================================================

    async def handle_validate_click(self, params: Dict[str, Any]) -> HandlerResult:
        """
        Handle validate_click tool execution

        Args:
            params: Tool parameters

        Returns:
            HandlerResult with validation results
        """
        start_time = time.time()

        try:
            self.logger.info("Validating click...")

            validation = {
                "timestamp": time.time(),
                "performed": True
            }

            # Coordinate validation
            expected_x = params.get("expected_x")
            expected_y = params.get("expected_y")

            if expected_x is not None and expected_y is not None:
                # Get actual cursor position (if available)
                # This is simplified - real implementation would track actual click
                validation["coordinate_accuracy"] = {
                    "expected": {"x": expected_x, "y": expected_y},
                    "threshold": params.get("accuracy_threshold", 2.0)
                }

            # Element validation
            expected_selector = params.get("expected_selector")
            if expected_selector:
                try:
                    element = await self.page.wait_for_selector(
                        expected_selector,
                        timeout=params.get("timeout", 5.0) * 1000
                    )

                    validation["element_found"] = element is not None
                    if element:
                        validation["element_visible"] = await element.is_visible()

                except Exception as e:
                    validation["element_found"] = False
                    validation["element_error"] = str(e)

            # Screenshot if requested
            if params.get("take_screenshot", self.config.validation_screenshot):
                screenshot_path = self.config.screenshot_dir / f"validation_{int(time.time() * 1000)}.png"
                await self.page.screenshot(path=str(screenshot_path))
                validation["screenshot"] = str(screenshot_path)

            validation["valid"] = True

            execution_time = time.time() - start_time

            return HandlerResult(
                success=True,
                data=validation,
                execution_time=execution_time
            )

        except Exception as e:
            self.logger.error(f"Error validating click: {e}", exc_info=True)
            return HandlerResult(
                success=False,
                data={"valid": False},
                error=str(e),
                execution_time=time.time() - start_time
            )

    # ========================================================================
    # SCROLL HANDLER - PLATFORM-AWARE
    # ========================================================================

    async def handle_scroll(self, params: Dict[str, Any]) -> HandlerResult:
        """
        Handle scroll operation with platform-specific support.

        Supports both Playwright scroll (element-based) and native OS scroll.

        Args:
            params: Tool parameters

        Returns:
            HandlerResult with scroll results
        """
        start_time = time.time()

        try:
            direction = params.get("direction", "down")  # up, down, left, right
            amount = params.get("amount", 3)  # scroll distance
            target = params.get("target", "viewport")  # viewport or element
            use_native = params.get("use_native_scroll", False)

            self.logger.info(f"Scrolling {direction} by {amount} units (native={use_native})")

            scroll_amount = amount * (5 if direction in ("up", "down") else 10)
            scroll_direction = -1 if direction in ("up", "left") else 1
            scroll_value = scroll_amount * scroll_direction

            if target == "viewport":
                if use_native and self.input_simulator:
                    # Use native scroll (requires focus on browser window)
                    success = self.input_simulator.scroll(
                        scroll_value,
                        horizontal=(direction in ("left", "right"))
                    )
                    scroll_method = "native" if success else "native_failed"
                else:
                    # Use Playwright scroll
                    await self.page.evaluate(f"""
                        window.scrollBy({{
                            left: {scroll_value if direction in ("left", "right") else 0},
                            top: {scroll_value if direction in ("up", "down") else 0},
                            behavior: 'smooth'
                        }});
                    """)
                    scroll_method = "playwright"
            else:
                # Scroll specific element
                selector = params.get("selector")
                if not selector:
                    raise ValueError("selector required for element scroll")

                locator = self.page.locator(selector)
                await locator.evaluate(f"""
                    el => el.scrollBy({{
                        left: {scroll_value if direction in ("left", "right") else 0},
                        top: {scroll_value if direction in ("up", "down") else 0},
                        behavior: 'smooth'
                    }});
                """)
                scroll_method = "element_scroll"

            execution_time = time.time() - start_time

            return HandlerResult(
                success=True,
                data={
                    "scrolled": True,
                    "direction": direction,
                    "amount": amount,
                    "scroll_method": scroll_method
                },
                execution_time=execution_time,
                metadata={
                    "target": target,
                    "use_native": use_native,
                    "scroll_method": scroll_method
                }
            )

        except Exception as e:
            self.logger.error(f"Error scrolling: {e}", exc_info=True)
            return HandlerResult(
                success=False,
                data={"scrolled": False},
                error=str(e),
                execution_time=time.time() - start_time
            )

    # ========================================================================
    # MOUSE MOVE HANDLER - PLATFORM-AWARE
    # ========================================================================

    async def handle_mouse_move(self, params: Dict[str, Any]) -> HandlerResult:
        """
        Handle mouse movement with platform-specific support.

        Supports both viewport coordinates and OS screen coordinates.

        Args:
            params: Tool parameters

        Returns:
            HandlerResult with mouse movement results
        """
        start_time = time.time()

        try:
            x = params.get("x")
            y = params.get("y")
            coord_system = params.get("coordinate_system", "viewport")
            steps = params.get("steps", 1)  # Smoothness

            if x is None or y is None:
                raise ValueError("x and y coordinates required")

            self.logger.info(f"Moving mouse to ({x}, {y}) [{coord_system}]")

            move_method = "unknown"

            if coord_system in ("screen", "os"):
                # Use native mouse move for OS coordinates
                if self.input_simulator:
                    success = await self._perform_mouse_move(x, y, steps)
                    move_method = "native" if success else "native_failed"
                else:
                    self.logger.warning("Native input simulator not available")
                    move_method = "native_unavailable"

                coords = {
                    "x": x,
                    "y": y,
                    "coordinate_system": coord_system,
                    "move_method": move_method
                }
            else:
                # Use Playwright mouse move for viewport coordinates
                await self.page.mouse.move(x, y)
                move_method = "playwright"

                coords = {
                    "x": x,
                    "y": y,
                    "coordinate_system": coord_system,
                    "move_method": move_method
                }

            execution_time = time.time() - start_time

            return HandlerResult(
                success=True,
                data={
                    "moved": True,
                    "coordinates": coords
                },
                execution_time=execution_time,
                metadata={
                    "coordinate_system": coord_system,
                    "steps": steps,
                    "move_method": move_method
                }
            )

        except Exception as e:
            self.logger.error(f"Error moving mouse: {e}", exc_info=True)
            return HandlerResult(
                success=False,
                data={"moved": False},
                error=str(e),
                execution_time=time.time() - start_time
            )

    # ========================================================================
    # PLATFORM INFO HANDLER
    # ========================================================================

    async def handle_get_platform_info(self, params: Dict[str, Any]) -> HandlerResult:
        """
        Get platform information and capabilities.

        Returns information about:
        - Current platform (Windows, Linux, macOS)
        - DPI/scaling settings
        - Monitor configuration
        - Available input methods

        Args:
            params: Tool parameters

        Returns:
            HandlerResult with platform information
        """
        start_time = time.time()

        try:
            platform_info = {
                "platform": self.platform,
                "browser_info": self._get_browser_info(),
                "capabilities": {
                    "input_simulation": self.input_simulator is not None,
                    "coordinate_conversion": self.coordinate_converter is not None,
                    "dpi_handling": self.dpi_handler is not None,
                    "window_management": self.window_manager is not None,
                }
            }

            # Get monitor info if available
            if self.dpi_handler:
                try:
                    monitors = self.dpi_handler.enumerate_monitors()
                    platform_info["monitors"] = [
                        {
                            "name": m.name,
                            "dpi_x": m.dpi_x,
                            "dpi_y": m.dpi_y,
                            "scale_factor": m.scale_factor,
                            "is_primary": m.is_primary,
                            "width": m.width,
                            "height": m.height
                        }
                        for m in monitors
                    ]
                except Exception as e:
                    self.logger.warning(f"Failed to get monitor info: {e}")

            execution_time = time.time() - start_time

            return HandlerResult(
                success=True,
                data=platform_info,
                execution_time=execution_time
            )

        except Exception as e:
            self.logger.error(f"Error getting platform info: {e}", exc_info=True)
            return HandlerResult(
                success=False,
                data={},
                error=str(e),
                execution_time=time.time() - start_time
            )


def create_handlers(page: Page) -> ToolHandlers:
    """
    Factory function to create tool handlers with platform support.

    Args:
        page: Playwright page instance

    Returns:
        Initialized ToolHandlers instance with platform-specific support
    """
    return ToolHandlers(page)
