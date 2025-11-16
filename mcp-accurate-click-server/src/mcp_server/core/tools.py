"""
Tool Registration and Schemas for MCP Accurate Click Server

Defines all available tools with their schemas, parameters, and metadata
following the Model Context Protocol (MCP) specification.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ClickMethod(str, Enum):
    """Available click methods"""
    BY_TEXT = "by_text"
    BY_SELECTOR = "by_selector"
    BY_COORDINATES = "by_coordinates"
    BY_ACCESSIBILITY = "by_accessibility"
    BY_XPATH = "by_xpath"
    BY_ROLE = "by_role"


class CoordinateSystem(str, Enum):
    """Coordinate system types"""
    VIEWPORT = "viewport"
    PAGE = "page"
    SCREEN = "screen"
    OS = "os"


@dataclass
class ToolParameter:
    """Tool parameter definition"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None

    def to_schema(self) -> Dict[str, Any]:
        """Convert to JSON schema format"""
        schema = {
            "type": self.type,
            "description": self.description
        }

        if self.enum:
            schema["enum"] = self.enum

        if self.default is not None:
            schema["default"] = self.default

        return schema


@dataclass
class ToolDefinition:
    """Complete tool definition"""
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    returns: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)

    def to_schema(self) -> Dict[str, Any]:
        """Convert to MCP tool schema format"""
        required_params = [p.name for p in self.parameters if p.required]

        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    p.name: p.to_schema() for p in self.parameters
                },
                "required": required_params
            }
        }


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

CLICK_ELEMENT_TOOL = ToolDefinition(
    name="click_element",
    description="""
    Click on a DOM element using multiple identification methods.

    Supports clicking by:
    - Text content (visible text on element)
    - CSS selector (standard CSS selectors)
    - XPath (XML path expressions)
    - Accessibility role and name
    - Exact coordinates (viewport, page, screen, or OS coordinates)

    Features:
    - Automatic scroll into view
    - Wait for element to be clickable
    - Adaptive correction based on feedback
    - Comprehensive validation
    - Fallback strategies on failure
    """,
    parameters=[
        ToolParameter(
            name="method",
            type="string",
            description="Click identification method",
            required=True,
            enum=[m.value for m in ClickMethod]
        ),
        ToolParameter(
            name="text",
            type="string",
            description="Text content to find (for by_text method)",
            required=False
        ),
        ToolParameter(
            name="selector",
            type="string",
            description="CSS selector (for by_selector method)",
            required=False
        ),
        ToolParameter(
            name="xpath",
            type="string",
            description="XPath expression (for by_xpath method)",
            required=False
        ),
        ToolParameter(
            name="role",
            type="string",
            description="Accessibility role (for by_accessibility/by_role method)",
            required=False
        ),
        ToolParameter(
            name="accessible_name",
            type="string",
            description="Accessibility name/label (for by_accessibility method)",
            required=False
        ),
        ToolParameter(
            name="x",
            type="number",
            description="X coordinate (for by_coordinates method)",
            required=False
        ),
        ToolParameter(
            name="y",
            type="number",
            description="Y coordinate (for by_coordinates method)",
            required=False
        ),
        ToolParameter(
            name="coordinate_system",
            type="string",
            description="Coordinate system type (for by_coordinates method)",
            required=False,
            default="viewport",
            enum=[cs.value for cs in CoordinateSystem]
        ),
        ToolParameter(
            name="exact_match",
            type="boolean",
            description="Require exact text match (for by_text method)",
            required=False,
            default=False
        ),
        ToolParameter(
            name="timeout",
            type="number",
            description="Timeout in seconds",
            required=False,
            default=30.0
        ),
        ToolParameter(
            name="validate",
            type="boolean",
            description="Validate click success",
            required=False,
            default=True
        ),
        ToolParameter(
            name="force",
            type="boolean",
            description="Force click even if element not visible",
            required=False,
            default=False
        )
    ],
    returns={
        "success": "boolean",
        "element": "object with element details",
        "coordinates": "clicked coordinates",
        "validation": "validation results if enabled",
        "error": "error message if failed"
    },
    examples=[
        {
            "description": "Click button by text",
            "input": {
                "method": "by_text",
                "text": "Submit",
                "exact_match": True
            }
        },
        {
            "description": "Click element by CSS selector",
            "input": {
                "method": "by_selector",
                "selector": "#login-button"
            }
        },
        {
            "description": "Click at specific coordinates",
            "input": {
                "method": "by_coordinates",
                "x": 500,
                "y": 300,
                "coordinate_system": "viewport"
            }
        }
    ]
)


FIND_ELEMENT_TOOL = ToolDefinition(
    name="find_element",
    description="""
    Find DOM elements without clicking.

    Supports finding by:
    - Text content (partial or exact match)
    - CSS selector
    - XPath
    - Accessibility role and name
    - Coordinates (find element at specific position)

    Returns detailed element information including:
    - Bounding box and coordinates
    - Visibility and clickability status
    - Text content and attributes
    - Accessibility properties
    - CSS selector and XPath
    """,
    parameters=[
        ToolParameter(
            name="method",
            type="string",
            description="Search method",
            required=True,
            enum=[m.value for m in ClickMethod]
        ),
        ToolParameter(
            name="text",
            type="string",
            description="Text to search for",
            required=False
        ),
        ToolParameter(
            name="selector",
            type="string",
            description="CSS selector",
            required=False
        ),
        ToolParameter(
            name="xpath",
            type="string",
            description="XPath expression",
            required=False
        ),
        ToolParameter(
            name="role",
            type="string",
            description="Accessibility role",
            required=False
        ),
        ToolParameter(
            name="accessible_name",
            type="string",
            description="Accessibility name",
            required=False
        ),
        ToolParameter(
            name="x",
            type="number",
            description="X coordinate",
            required=False
        ),
        ToolParameter(
            name="y",
            type="number",
            description="Y coordinate",
            required=False
        ),
        ToolParameter(
            name="coordinate_system",
            type="string",
            description="Coordinate system",
            required=False,
            default="viewport",
            enum=[cs.value for cs in CoordinateSystem]
        ),
        ToolParameter(
            name="exact_match",
            type="boolean",
            description="Require exact match",
            required=False,
            default=False
        ),
        ToolParameter(
            name="visible_only",
            type="boolean",
            description="Only return visible elements",
            required=False,
            default=True
        ),
        ToolParameter(
            name="limit",
            type="integer",
            description="Maximum number of results",
            required=False,
            default=10
        )
    ],
    returns={
        "found": "boolean",
        "count": "number of elements found",
        "elements": "array of element details",
        "error": "error message if failed"
    },
    examples=[
        {
            "description": "Find all buttons with 'Save' text",
            "input": {
                "method": "by_text",
                "text": "Save",
                "exact_match": False
            }
        },
        {
            "description": "Find element at coordinates",
            "input": {
                "method": "by_coordinates",
                "x": 100,
                "y": 200
            }
        }
    ]
)


GET_DOM_STRUCTURE_TOOL = ToolDefinition(
    name="get_dom_structure",
    description="""
    Extract comprehensive DOM structure with coordinate mapping.

    Provides:
    - Complete element hierarchy
    - Bounding boxes in multiple coordinate systems
    - Interactive and text elements
    - Accessibility information
    - Viewport and page dimensions
    - Statistics and metadata

    Options:
    - Include/exclude specific element types
    - Filter by visibility
    - Limit depth or element count
    - Cache for performance
    """,
    parameters=[
        ToolParameter(
            name="include_invisible",
            type="boolean",
            description="Include invisible elements",
            required=False,
            default=False
        ),
        ToolParameter(
            name="include_text_elements",
            type="boolean",
            description="Include text-only elements",
            required=False,
            default=True
        ),
        ToolParameter(
            name="include_interactive_only",
            type="boolean",
            description="Only include interactive elements",
            required=False,
            default=False
        ),
        ToolParameter(
            name="max_depth",
            type="integer",
            description="Maximum DOM tree depth",
            required=False
        ),
        ToolParameter(
            name="max_elements",
            type="integer",
            description="Maximum number of elements",
            required=False
        ),
        ToolParameter(
            name="use_cache",
            type="boolean",
            description="Use cached DOM structure if available",
            required=False,
            default=True
        )
    ],
    returns={
        "success": "boolean",
        "url": "current page URL",
        "title": "page title",
        "viewport": "viewport dimensions",
        "elements": "array of DOM elements",
        "statistics": "element counts and metrics",
        "error": "error message if failed"
    },
    examples=[
        {
            "description": "Get all interactive elements",
            "input": {
                "include_interactive_only": True,
                "include_invisible": False
            }
        },
        {
            "description": "Get full DOM structure",
            "input": {
                "include_invisible": True,
                "max_elements": 1000
            }
        }
    ]
)


VALIDATE_CLICK_TOOL = ToolDefinition(
    name="validate_click",
    description="""
    Validate click accuracy and success.

    Performs comprehensive validation including:
    - Target element state verification
    - Expected vs actual coordinates comparison
    - DOM changes detection
    - Visual validation (screenshot comparison)
    - Event listener verification
    - Focus state validation

    Returns detailed report with:
    - Success/failure status
    - Accuracy metrics
    - Element state changes
    - Recommendations for improvement
    """,
    parameters=[
        ToolParameter(
            name="expected_selector",
            type="string",
            description="Expected element selector",
            required=False
        ),
        ToolParameter(
            name="expected_x",
            type="number",
            description="Expected X coordinate",
            required=False
        ),
        ToolParameter(
            name="expected_y",
            type="number",
            description="Expected Y coordinate",
            required=False
        ),
        ToolParameter(
            name="coordinate_system",
            type="string",
            description="Coordinate system",
            required=False,
            default="viewport",
            enum=[cs.value for cs in CoordinateSystem]
        ),
        ToolParameter(
            name="check_dom_changes",
            type="boolean",
            description="Check for DOM changes",
            required=False,
            default=True
        ),
        ToolParameter(
            name="take_screenshot",
            type="boolean",
            description="Take validation screenshot",
            required=False,
            default=True
        ),
        ToolParameter(
            name="accuracy_threshold",
            type="number",
            description="Acceptable pixel error threshold",
            required=False,
            default=2.0
        ),
        ToolParameter(
            name="timeout",
            type="number",
            description="Validation timeout in seconds",
            required=False,
            default=5.0
        )
    ],
    returns={
        "valid": "boolean indicating validation success",
        "accuracy": "coordinate accuracy metrics",
        "element_state": "element state information",
        "dom_changes": "detected DOM changes",
        "screenshot": "screenshot data if enabled",
        "recommendations": "improvement recommendations",
        "error": "error message if failed"
    },
    examples=[
        {
            "description": "Validate click accuracy",
            "input": {
                "expected_x": 100,
                "expected_y": 200,
                "accuracy_threshold": 2.0
            }
        },
        {
            "description": "Validate element click with DOM change detection",
            "input": {
                "expected_selector": "#submit-button",
                "check_dom_changes": True
            }
        }
    ]
)


# ============================================================================
# TOOL REGISTRY
# ============================================================================

class ToolRegistry:
    """Registry for all available tools"""

    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.logger = logging.getLogger(f"{__name__}.ToolRegistry")
        self._register_default_tools()

    def _register_default_tools(self):
        """Register all default tools"""
        default_tools = [
            CLICK_ELEMENT_TOOL,
            FIND_ELEMENT_TOOL,
            GET_DOM_STRUCTURE_TOOL,
            VALIDATE_CLICK_TOOL
        ]

        for tool in default_tools:
            self.register(tool)

    def register(self, tool: ToolDefinition):
        """Register a tool"""
        self.tools[tool.name] = tool
        self.logger.info(f"Registered tool: {tool.name}")

    def unregister(self, tool_name: str):
        """Unregister a tool"""
        if tool_name in self.tools:
            del self.tools[tool_name]
            self.logger.info(f"Unregistered tool: {tool_name}")

    def get(self, tool_name: str) -> Optional[ToolDefinition]:
        """Get tool definition by name"""
        return self.tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """List all registered tool names"""
        return list(self.tools.keys())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas in MCP format"""
        return [tool.to_schema() for tool in self.tools.values()]

    def validate_parameters(self, tool_name: str, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate parameters for a tool

        Returns: (is_valid, error_message)
        """
        tool = self.get(tool_name)
        if not tool:
            return False, f"Unknown tool: {tool_name}"

        # Check required parameters
        for param in tool.parameters:
            if param.required and param.name not in params:
                return False, f"Missing required parameter: {param.name}"

        # Check enum values
        for param in tool.parameters:
            if param.name in params and param.enum:
                value = params[param.name]
                if value not in param.enum:
                    return False, f"Invalid value for {param.name}: {value}. Must be one of {param.enum}"

        return True, None


# Global tool registry
_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get global tool registry (singleton)"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def init_tool_registry() -> ToolRegistry:
    """Initialize global tool registry"""
    global _tool_registry
    _tool_registry = ToolRegistry()
    return _tool_registry
