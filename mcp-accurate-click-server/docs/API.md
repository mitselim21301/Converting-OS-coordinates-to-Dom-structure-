# API Reference
## MCP Accurate Click Server

**Version**: 1.0.0
**Last Updated**: 2025-11-16

---

## Table of Contents

1. [MCP Tools](#mcp-tools)
2. [Core Classes](#core-classes)
3. [Coordinate System Types](#coordinate-system-types)
4. [Error Types](#error-types)
5. [Examples](#examples)

---

## MCP Tools

MCP tools are the primary interface for AI agents to interact with the server.

### click_element

Click on a DOM element using multiple finding strategies.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "method": {
      "type": "string",
      "enum": ["text", "selector", "coordinates", "accessible_name"],
      "description": "Method to find the element"
    },
    "value": {
      "type": "string",
      "description": "Search value (text content, CSS selector, or 'x,y' coordinates)"
    },
    "validate": {
      "type": "boolean",
      "default": true,
      "description": "Perform pre-click validation"
    },
    "wait_after": {
      "type": "number",
      "default": 100,
      "description": "Milliseconds to wait after clicking"
    },
    "retry": {
      "type": "boolean",
      "default": true,
      "description": "Retry with alternative strategies on failure"
    }
  },
  "required": ["method", "value"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Whether the click succeeded"
    },
    "element": {
      "type": "string",
      "description": "Element identifier (tag#id or tag.class)"
    },
    "text": {
      "type": "string",
      "description": "Element text content"
    },
    "coordinates": {
      "type": "object",
      "properties": {
        "viewport": {"type": "array", "items": {"type": "number"}},
        "page": {"type": "array", "items": {"type": "number"}},
        "screen": {"type": "array", "items": {"type": "number"}}
      }
    },
    "validation": {
      "type": "object",
      "properties": {
        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
      }
    },
    "outcome": {
      "type": "string",
      "description": "What happened after click (navigation, modal, etc.)"
    },
    "error": {
      "type": "string",
      "description": "Error message if success=false"
    }
  }
}
```

**Examples**:

```python
# Click by text
result = await call_tool("click_element", {
    "method": "text",
    "value": "Submit"
})
# Result: {"success": true, "element": "button#submit-btn", ...}

# Click by CSS selector
result = await call_tool("click_element", {
    "method": "selector",
    "value": "#login-button"
})

# Click at coordinates
result = await call_tool("click_element", {
    "method": "coordinates",
    "value": "500,300"
})

# Click by accessible name
result = await call_tool("click_element", {
    "method": "accessible_name",
    "value": "Close dialog"
})
```

---

### extract_dom_structure

Extract complete DOM structure with coordinates and metadata.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "include_hidden": {
      "type": "boolean",
      "default": false,
      "description": "Include hidden elements"
    },
    "interactive_only": {
      "type": "boolean",
      "default": false,
      "description": "Only return interactive elements"
    },
    "viewport_only": {
      "type": "boolean",
      "default": false,
      "description": "Only elements in current viewport"
    },
    "max_depth": {
      "type": "number",
      "default": -1,
      "description": "Maximum DOM depth (-1 for unlimited)"
    }
  }
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "elements": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "uid": {"type": "string"},
          "tag_name": {"type": "string"},
          "element_id": {"type": "string"},
          "class_names": {"type": "array", "items": {"type": "string"}},
          "role": {"type": "string"},
          "aria_label": {"type": "string"},
          "accessible_name": {"type": "string"},
          "text_content": {"type": "string"},
          "inner_text": {"type": "string"},
          "value": {"type": "string"},
          "bounding_box": {
            "type": "object",
            "properties": {
              "x": {"type": "number"},
              "y": {"type": "number"},
              "width": {"type": "number"},
              "height": {"type": "number"},
              "page_x": {"type": "number"},
              "page_y": {"type": "number"}
            }
          },
          "visible": {"type": "boolean"},
          "enabled": {"type": "boolean"},
          "clickable": {"type": "boolean"},
          "xpath": {"type": "string"},
          "css_selector": {"type": "string"}
        }
      }
    },
    "viewport": {
      "type": "object",
      "properties": {
        "width": {"type": "number"},
        "height": {"type": "number"}
      }
    },
    "scroll": {
      "type": "object",
      "properties": {
        "x": {"type": "number"},
        "y": {"type": "number"}
      }
    },
    "device_pixel_ratio": {"type": "number"},
    "url": {"type": "string"},
    "total_elements": {"type": "number"}
  }
}
```

**Example**:

```python
structure = await call_tool("extract_dom_structure", {
    "interactive_only": true,
    "viewport_only": true
})

# Result:
# {
#   "elements": [
#     {
#       "uid": "abc123",
#       "tag_name": "button",
#       "element_id": "submit-btn",
#       "text_content": "Submit",
#       "bounding_box": {
#         "x": 400, "y": 300,
#         "width": 100, "height": 40,
#         "page_x": 400, "page_y": 1800
#       },
#       "visible": true,
#       "clickable": true,
#       ...
#     },
#     ...
#   ],
#   "viewport": {"width": 1920, "height": 1080},
#   "scroll": {"x": 0, "y": 1500},
#   "total_elements": 26
# }
```

---

### find_element

Find element(s) using various search strategies.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "strategy": {
      "type": "string",
      "enum": ["text", "selector", "xpath", "role", "accessible_name"],
      "description": "Search strategy"
    },
    "value": {
      "type": "string",
      "description": "Search query"
    },
    "exact": {
      "type": "boolean",
      "default": false,
      "description": "Exact match for text/name searches"
    },
    "case_sensitive": {
      "type": "boolean",
      "default": false,
      "description": "Case-sensitive text matching"
    },
    "return_all": {
      "type": "boolean",
      "default": false,
      "description": "Return all matches (default: first only)"
    }
  },
  "required": ["strategy", "value"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "found": {"type": "boolean"},
    "count": {"type": "number"},
    "elements": {
      "type": "array",
      "items": {"$ref": "#/definitions/DOMElement"}
    }
  }
}
```

**Examples**:

```python
# Find by text (partial match)
result = await call_tool("find_element", {
    "strategy": "text",
    "value": "submit",
    "case_sensitive": false
})

# Find by ARIA role
result = await call_tool("find_element", {
    "strategy": "role",
    "value": "button",
    "return_all": true
})

# Find by accessible name
result = await call_tool("find_element", {
    "strategy": "accessible_name",
    "value": "Close",
    "exact": true
})
```

---

### transform_coordinates

Transform coordinates between different coordinate systems.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "x": {"type": "number"},
    "y": {"type": "number"},
    "from_system": {
      "type": "string",
      "enum": ["os_screen", "css_screen", "viewport", "page"],
      "description": "Source coordinate system"
    },
    "to_system": {
      "type": "string",
      "enum": ["os_screen", "css_screen", "viewport", "page"],
      "description": "Target coordinate system"
    }
  },
  "required": ["x", "y", "from_system", "to_system"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "x": {"type": "number"},
    "y": {"type": "number"},
    "coordinate_system": {"type": "string"},
    "transformation_info": {
      "type": "object",
      "properties": {
        "dpi_scale": {"type": "number"},
        "window_offset": {"type": "array", "items": {"type": "number"}},
        "scroll_offset": {"type": "array", "items": {"type": "number"}}
      }
    }
  }
}
```

**Example**:

```python
# OS screen → viewport
result = await call_tool("transform_coordinates", {
    "x": 1500,
    "y": 800,
    "from_system": "os_screen",
    "to_system": "viewport"
})
# Result: {"x": 400, "y": 300, ...}
```

---

### validate_click_target

Validate that an element can be clicked at given coordinates.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "element_uid": {
      "type": "string",
      "description": "Element unique identifier"
    },
    "x": {"type": "number", "description": "X coordinate"},
    "y": {"type": "number", "description": "Y coordinate"},
    "coordinate_system": {
      "type": "string",
      "enum": ["viewport", "page"],
      "default": "viewport"
    }
  },
  "required": ["element_uid", "x", "y"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "valid": {"type": "boolean"},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "issues": {
      "type": "array",
      "items": {"type": "string"},
      "description": "List of validation issues"
    },
    "checks": {
      "type": "object",
      "properties": {
        "visible": {"type": "boolean"},
        "enabled": {"type": "boolean"},
        "not_occluded": {"type": "boolean"},
        "stable": {"type": "boolean"},
        "coordinates_hit": {"type": "boolean"}
      }
    }
  }
}
```

**Example**:

```python
validation = await call_tool("validate_click_target", {
    "element_uid": "abc123",
    "x": 400,
    "y": 300
})

# Result:
# {
#   "valid": true,
#   "confidence": 0.95,
#   "issues": [],
#   "checks": {
#     "visible": true,
#     "enabled": true,
#     "not_occluded": true,
#     "stable": true,
#     "coordinates_hit": true
#   }
# }
```

---

### calibrate_transformer

Calibrate coordinate transformation from known point correspondences.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "os_points": {
      "type": "array",
      "items": {
        "type": "array",
        "items": {"type": "number"},
        "minItems": 2,
        "maxItems": 2
      },
      "minItems": 3,
      "description": "OS screen coordinates [[x1,y1], [x2,y2], ...]"
    },
    "dom_points": {
      "type": "array",
      "items": {
        "type": "array",
        "items": {"type": "number"},
        "minItems": 2,
        "maxItems": 2
      },
      "minItems": 3,
      "description": "Corresponding DOM coordinates"
    },
    "use_ransac": {
      "type": "boolean",
      "default": true,
      "description": "Use RANSAC for robust calibration"
    },
    "refine": {
      "type": "boolean",
      "default": true,
      "description": "Iterative refinement"
    }
  },
  "required": ["os_points", "dom_points"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "success": {"type": "boolean"},
    "accuracy": {"type": "number", "description": "RMS error in pixels"},
    "subpixel_accurate": {"type": "boolean"},
    "condition_number": {"type": "number"},
    "inlier_ratio": {"type": "number"},
    "transformation_matrix": {
      "type": "array",
      "items": {"type": "array", "items": {"type": "number"}}
    }
  }
}
```

**Example**:

```python
calibration = await call_tool("calibrate_transformer", {
    "os_points": [[100, 100], [800, 100], [100, 500], [800, 500]],
    "dom_points": [[150, 180], [1100, 180], [150, 780], [1100, 780]],
    "use_ransac": true,
    "refine": true
})

# Result:
# {
#   "success": true,
#   "accuracy": 0.000001,
#   "subpixel_accurate": true,
#   "condition_number": 1.2,
#   "inlier_ratio": 1.0
# }
```

---

## Core Classes

### DOMStructureExtractor

Extracts comprehensive DOM structure from browser page.

**Location**: `src/mcp_server/dom/dom_structure_extractor.py`

#### Constructor

```python
DOMStructureExtractor(page: Page)
```

**Parameters**:
- `page`: Playwright Page object

#### Methods

##### extract()

Extract complete DOM structure.

```python
def extract(self,
           include_hidden: bool = False,
           interactive_only: bool = False,
           viewport_only: bool = False) -> DOMStructure
```

**Returns**: `DOMStructure` object containing:
- `elements`: List of `DOMElement` objects
- `viewport`: Viewport dimensions
- `scroll`: Scroll position
- `device_pixel_ratio`: DPR value
- `url`: Current URL
- `total_elements`: Element count

**Example**:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('https://example.com')

    extractor = DOMStructureExtractor(page)
    structure = extractor.extract(interactive_only=True)

    print(f"Found {len(structure.elements)} interactive elements")
    for elem in structure.elements:
        print(f"  {elem.tag_name}: {elem.text_content}")
```

---

### CoordinateMapper

Maps between coordinates and DOM elements.

**Location**: `src/mcp_server/dom/coordinate_mapper.py`

#### Constructor

```python
CoordinateMapper(structure: DOMStructure)
```

**Parameters**:
- `structure`: DOMStructure from extractor

#### Methods

##### find_element_at_point()

Find element at specific coordinates.

```python
def find_element_at_point(self,
                          x: float,
                          y: float,
                          coordinate_type: str = 'viewport') -> Optional[DOMElement]
```

**Parameters**:
- `x`, `y`: Coordinates
- `coordinate_type`: 'viewport' or 'page'

**Returns**: `DOMElement` or `None`

**Example**:

```python
mapper = CoordinateMapper(structure)
element = mapper.find_element_at_point(500, 300, coordinate_type='viewport')
if element:
    print(f"Element at (500, 300): {element.tag_name}")
```

##### find_elements_by_text()

Find elements containing specific text.

```python
def find_elements_by_text(self,
                          text: str,
                          exact: bool = False,
                          case_sensitive: bool = False) -> List[DOMElement]
```

**Parameters**:
- `text`: Search text
- `exact`: Exact match (default: partial)
- `case_sensitive`: Case-sensitive search

**Returns**: List of matching elements

**Example**:

```python
buttons = mapper.find_elements_by_text("submit", exact=False)
for btn in buttons:
    print(f"Found: {btn.text_content} at ({btn.bounding_box.x}, {btn.bounding_box.y})")
```

##### find_clickable_near_text()

Find clickable elements near text.

```python
def find_clickable_near_text(self,
                             text: str,
                             max_distance: float = 100) -> List[DOMElement]
```

**Example**:

```python
# Find buttons near "Username" label
buttons = mapper.find_clickable_near_text("Username", max_distance=50)
```

---

### OSToDOM_Transformer

High-precision coordinate transformer with sub-pixel accuracy.

**Location**: `src/mcp_server/core/os_to_dom_transformer.py`

#### Constructor

```python
OSToDOM_Transformer(enable_adaptive: bool = True)
```

**Parameters**:
- `enable_adaptive`: Enable adaptive correction from feedback

#### Methods

##### calibrate()

Calibrate from point correspondences.

```python
def calibrate(self,
             os_points: np.ndarray,
             dom_points: np.ndarray,
             use_ransac: bool = True,
             refine: bool = True,
             scale: Optional[float] = None) -> Dict
```

**Parameters**:
- `os_points`: Nx2 array of OS coordinates
- `dom_points`: Nx2 array of DOM coordinates
- `use_ransac`: Use RANSAC for outlier rejection
- `refine`: Iterative refinement
- `scale`: Zoom/scale factor (optional)

**Returns**: Calibration report dict

**Example**:

```python
import numpy as np

transformer = OSToDOM_Transformer()

os_points = np.array([[100, 100], [800, 100], [100, 500], [800, 500]])
dom_points = np.array([[150, 180], [1100, 180], [150, 780], [1100, 780]])

report = transformer.calibrate(os_points, dom_points, use_ransac=True)

print(f"Accuracy: {report['validation']['achieved_accuracy']:.6f} pixels")
print(f"Sub-pixel: {report['validation']['is_subpixel_accurate']}")
```

##### transform_os_to_dom()

Transform OS coordinates to DOM.

```python
def transform_os_to_dom(self, x: float, y: float) -> Tuple[float, float]
```

**Returns**: (x_dom, y_dom) tuple

**Example**:

```python
x_dom, y_dom = transformer.transform_os_to_dom(500, 300)
print(f"OS (500, 300) → DOM ({x_dom:.2f}, {y_dom:.2f})")
```

##### transform_dom_to_os()

Transform DOM coordinates to OS.

```python
def transform_dom_to_os(self, x: float, y: float) -> Tuple[float, float]
```

**Example**:

```python
x_os, y_os = transformer.transform_dom_to_os(650, 450)
```

##### add_correction_feedback()

Add feedback for adaptive learning.

```python
def add_correction_feedback(self,
                           os_coords: Tuple[float, float],
                           predicted_dom: Tuple[float, float],
                           actual_dom: Tuple[float, float])
```

**Example**:

```python
# Predicted click position
x_pred, y_pred = transformer.transform_os_to_dom(500, 300)

# Actual position after click (from validation)
x_actual, y_actual = 652, 451

# Add feedback
transformer.add_correction_feedback((500, 300), (x_pred, y_pred), (x_actual, y_actual))

# Future transforms will be more accurate
```

##### validate()

Validate transformation accuracy.

```python
def validate(self) -> Dict
```

**Returns**: Validation report with round-trip errors, condition number, etc.

---

### AffineTransform2D

Low-level affine transformation class.

**Location**: `src/mcp_server/core/affine_transform.py`

#### Constructor

```python
AffineTransform2D(matrix: Optional[np.ndarray] = None)
```

**Parameters**:
- `matrix`: 3x3 transformation matrix (default: identity)

#### Class Methods

```python
@classmethod
def identity() -> AffineTransform2D

@classmethod
def translation(tx: float, ty: float) -> AffineTransform2D

@classmethod
def rotation_degrees(angle: float) -> AffineTransform2D

@classmethod
def rotation_radians(angle: float) -> AffineTransform2D

@classmethod
def scaling(sx: float, sy: float) -> AffineTransform2D
```

#### Instance Methods

```python
def transform_point(self, x: float, y: float) -> Tuple[float, float]

def transform_points(self, points: np.ndarray) -> np.ndarray

def inverse(self) -> AffineTransform2D

def compose(self, other: AffineTransform2D) -> AffineTransform2D

def decompose(self) -> Dict[str, Any]
```

**Example**:

```python
# Create transformation: Translate, then rotate, then scale
T = AffineTransform2D.translation(100, 50)
R = AffineTransform2D.rotation_degrees(30)
S = AffineTransform2D.scaling(1.5, 1.5)

combined = T @ R @ S  # Matrix multiplication

x_out, y_out = combined.transform_point(10, 20)
```

---

## Coordinate System Types

### OS Screen Coordinates
- **Unit**: Physical pixels
- **Origin**: Top-left of primary monitor
- **Scale**: Actual device pixels (e.g., 1920×1080 at 150% DPI = 2880×1620 physical)

### CSS Screen Coordinates
- **Unit**: Logical pixels (CSS pixels)
- **Origin**: Top-left of primary monitor
- **Scale**: DPI-independent (1920×1080 regardless of scaling)
- **Conversion**: `css = physical / DPR`

### Browser Viewport Coordinates
- **Unit**: CSS pixels
- **Origin**: Top-left of browser viewport (excludes chrome/toolbars)
- **Conversion**: `viewport = css_screen - window.screen{X,Y}`

### Page Coordinates
- **Unit**: CSS pixels
- **Origin**: Top-left of document
- **Conversion**: `page = viewport + scroll{X,Y}`

---

## Error Types

### ElementNotFoundError

```python
class ElementNotFoundError(Exception):
    """Raised when element cannot be found"""
    def __init__(self, strategy: str, value: str)
```

### CoordinateTransformError

```python
class CoordinateTransformError(Exception):
    """Raised when coordinate transformation fails"""
    def __init__(self, message: str, details: Dict)
```

### ValidationError

```python
class ValidationError(Exception):
    """Raised when click validation fails"""
    def __init__(self, element: str, reason: str, confidence: float)
```

### CalibrationError

```python
class CalibrationError(Exception):
    """Raised when calibration fails"""
    def __init__(self, message: str, condition_number: float)
```

---

## Examples

### Complete Click Workflow

```python
from mcp_server.dom import DOMStructureExtractor, CoordinateMapper
from mcp_server.validation import ClickValidator
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('https://example.com')

    # 1. Extract DOM
    extractor = DOMStructureExtractor(page)
    structure = extractor.extract(interactive_only=True)

    # 2. Find element
    mapper = CoordinateMapper(structure)
    elements = mapper.find_elements_by_text("Submit", exact=False)

    if not elements:
        raise ElementNotFoundError("text", "Submit")

    element = elements[0]

    # 3. Get click coordinates
    click_x = element.bounding_box.center_x
    click_y = element.bounding_box.center_y

    # 4. Validate
    validator = ClickValidator(structure)
    validation = validator.validate_target(element, click_x, click_y)

    if not validation['valid']:
        raise ValidationError(element.uid, validation['issues'][0], validation['confidence'])

    # 5. Click
    page.mouse.click(click_x, click_y)

    # 6. Wait and verify
    page.wait_for_timeout(100)
    new_structure = extractor.extract()

    if new_structure.url != structure.url:
        print("Navigation occurred!")
    elif new_structure.total_elements != structure.total_elements:
        print("DOM changed!")
```

### Calibration from Known Points

```python
import numpy as np
from mcp_server.core import OSToDOM_Transformer

# Collect calibration points
# (These would be obtained from user clicking known positions)
os_points = np.array([
    [100, 100],   # Top-left
    [800, 100],   # Top-right
    [100, 500],   # Bottom-left
    [800, 500],   # Bottom-right
    [450, 300]    # Center
])

dom_points = np.array([
    [150, 180],
    [1100, 180],
    [150, 780],
    [1100, 780],
    [625, 480]
])

# Calibrate
transformer = OSToDOM_Transformer(enable_adaptive=True)
report = transformer.calibrate(
    os_points,
    dom_points,
    use_ransac=True,
    refine=True
)

# Check results
print(f"Calibration accuracy: {report['validation']['achieved_accuracy']:.6f} pixels")
print(f"Sub-pixel accurate: {report['validation']['is_subpixel_accurate']}")
print(f"Condition number: {report['condition_number']:.2f}")

# Transform coordinates
x_dom, y_dom = transformer.transform_os_to_dom(500, 300)
print(f"OS (500, 300) → DOM ({x_dom:.2f}, {y_dom:.2f})")

# Save calibration
transformer.save_calibration('calibration.npz')
```

### Vision-Validated Click

```python
from mcp_server.vision import VisionValidator
from mcp_server.dom import DOMStructureExtractor

# Extract DOM
structure = extractor.extract()

# Find element
element = mapper.find_elements_by_text("Login")[0]
expected_bbox = element.bounding_box

# Vision validation
screenshot = page.screenshot()
vision = VisionValidator()
detections = vision.detect_elements(screenshot)

# Find matching detection
for detection in detections:
    iou = calculate_iou(expected_bbox, detection.bbox)
    if iou > 0.8:  # High overlap
        # Use vision-detected center
        click_x = detection.bbox.center_x
        click_y = detection.bbox.center_y
        print(f"Vision-validated coordinates: ({click_x}, {click_y})")
        break
else:
    # Fall back to DOM coordinates
    click_x = expected_bbox.center_x
    click_y = expected_bbox.center_y
    print("Using DOM coordinates (no vision match)")

page.mouse.click(click_x, click_y)
```

---

**Next**: See [CONFIGURATION.md](CONFIGURATION.md) for setup instructions.
