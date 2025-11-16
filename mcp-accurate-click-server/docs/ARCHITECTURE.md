# Architecture Overview
## MCP Accurate Click Server

**Version**: 1.0.0
**Last Updated**: 2025-11-16

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [Coordinate Transformation Pipeline](#coordinate-transformation-pipeline)
5. [Integration Points](#integration-points)
6. [Design Decisions](#design-decisions)
7. [Performance Considerations](#performance-considerations)

---

## System Overview

The MCP Accurate Click Server is a Model Context Protocol server that provides AI agents with high-precision computer interaction capabilities through accurate coordinate transformation and multi-strategy validation.

### Core Objectives

1. **Accuracy**: Achieve sub-pixel precision in coordinate transformations
2. **Reliability**: Validate clicks before execution with multiple strategies
3. **Performance**: Fast DOM extraction and coordinate mapping
4. **Compatibility**: Handle Windows DPI scaling, multi-monitor setups
5. **Integration**: Standard MCP interface for AI agents

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         AI Agent                                 │
│                    (Claude, GPT-4, etc.)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │ MCP Protocol (JSON-RPC)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Server Layer                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                │
│  │   Tools    │  │ Resources  │  │  Prompts   │                │
│  │            │  │            │  │            │                │
│  └─────┬──────┘  └──────┬─────┘  └──────┬─────┘                │
└────────┼────────────────┼────────────────┼──────────────────────┘
         │                │                │
         ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Core Engine                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Coordinate Transformation Engine             │  │
│  │  ┌───────────┐  ┌──────────┐  ┌──────────┐              │  │
│  │  │  Affine   │  │   DPI    │  │ Viewport │              │  │
│  │  │ Transform │  │ Scaling  │  │  Scroll  │              │  │
│  │  └───────────┘  └──────────┘  └──────────┘              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Element Detection & Validation               │  │
│  │  ┌──────────┐  ┌──────────────┐  ┌──────────┐           │  │
│  │  │   DOM    │  │ Accessibility│  │  Vision  │           │  │
│  │  │Extractor │  │     Tree     │  │Validator │           │  │
│  │  └──────────┘  └──────────────┘  └──────────┘           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 Platform Adapters                         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │  │
│  │  │ Windows  │  │  Linux   │  │  macOS   │               │  │
│  │  │Coordinate│  │Coordinate│  │Coordinate│               │  │
│  │  └──────────┘  └──────────┘  └──────────┘               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┬────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Browser (Playwright)                          │
│                      Operating System                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. MCP Server Layer

**Purpose**: Implements the Model Context Protocol for AI agent communication

**Components**:
- **Tools Registry**: Manages available MCP tools (click_element, extract_dom_structure, etc.)
- **Resource Manager**: Provides access to browser state, screenshots, DOM snapshots
- **Prompts Library**: Pre-configured prompts for common automation tasks

**Key Files**:
- `src/mcp_server/__init__.py` - Server initialization
- `src/mcp_server/server.py` - MCP protocol implementation
- `src/mcp_server/tools.py` - Tool definitions and handlers

### 2. Core Engine

#### 2.1 Coordinate Transformation Engine

**Purpose**: High-precision coordinate conversion between different systems

**Sub-components**:

##### Affine Transform Module
```python
Location: src/mcp_server/core/affine_transform.py

Classes:
- AffineTransform2D: 3x3 transformation matrices
- TransformationChain: Compose multiple transforms

Features:
- Float64 precision (15-17 significant digits)
- Sub-pixel accuracy (< 1/256 pixel)
- Efficient matrix operations
- Analytical inverse computation
```

##### Calibration Module
```python
Location: src/mcp_server/core/calibration.py

Functions:
- calibrate_affine_transform(): Least squares calibration
- calibrate_ransac(): Robust calibration with outlier rejection
- iterative_refinement(): Improve accuracy through iteration

Algorithms:
- Least Squares: O(n) time complexity
- RANSAC: O(k·n), k=1000 iterations typical
- Iterative: O(m·n), m=5-10 iterations
```

##### OS to DOM Transformer
```python
Location: src/mcp_server/core/os_to_dom_transformer.py

Class: OSToDOM_Transformer

Capabilities:
- Calibration from point correspondences
- Forward transform (OS → DOM)
- Inverse transform (DOM → OS)
- Multi-scale support (zoom levels)
- Adaptive correction from feedback
- Validation and error analysis
```

#### 2.2 Element Detection & Validation

##### DOM Extractor
```python
Location: src/mcp_server/dom/dom_structure_extractor.py

Class: DOMStructureExtractor

Responsibilities:
- Extract complete DOM structure via Playwright
- Compute bounding boxes in multiple coordinate systems
- Identify interactive elements
- Extract text content and accessibility info
- Build XPath and CSS selector paths

Performance:
- Simple page (26 elements): ~50ms
- Complex page (500 elements): ~350ms
- Very complex (2000 elements): ~1.2s
```

##### Coordinate Mapper
```python
Location: src/mcp_server/dom/coordinate_mapper.py

Class: CoordinateMapper

Functions:
- find_element_at_point(): Element from coordinates
- find_elements_by_text(): Search by text content
- find_clickable_near_text(): Find nearby interactive elements
- validate_click_target(): Pre-click validation

Accuracy:
- Coordinate-based: 100% (when coords correct)
- Text-based: 90-95% (unique text)
- Hybrid: 95-100% (validated)
```

##### Accessibility Tree
```python
Location: src/mcp_server/accessibility/tree_extractor.py

Class: AccessibilityTreeExtractor

Features:
- Chrome DevTools Protocol integration
- Query by role and accessible name
- Get coordinates from accessibility nodes
- Map between DOM and accessibility tree
- State validation (disabled, hidden, focusable)

Benefits:
- Semantic targeting (by role/name, not CSS)
- Stable identifiers (ARIA changes less)
- Built-in state information
```

##### Vision Validator (Optional)
```python
Location: src/mcp_server/vision/vision_validator.py

Class: VisionValidator

Methods:
- detect_elements(): YOLO-based element detection
- extract_text(): OCR for text recognition
- validate_click(): Visual confirmation
- compare_expected_actual(): IoU comparison

Models:
- YOLOv8 (fine-tuned for UI elements)
- OCR (DeepSeek or similar)
- Vision-language models (GPT-4V)
```

#### 2.3 Platform Adapters

##### Windows Adapter
```python
Location: src/mcp_server/windows/windows_coordinates.py

Class: WindowsCoordinateAdapter

Responsibilities:
- Get DPI for each monitor
- Convert physical ↔ logical pixels
- Handle multi-monitor configurations
- Track window positions
- Account for browser chrome (titlebar, toolbars)

Windows APIs:
- GetDpiForMonitor()
- GetDpiForWindow()
- GetCursorPos()
- ScreenToClient()
```

##### Linux Adapter
```python
Location: src/mcp_server/linux/linux_coordinates.py

Status: Experimental

Challenges:
- X11 vs Wayland differences
- Limited automation support in Wayland
- Varying DPI handling across desktop environments
```

##### macOS Adapter
```python
Location: src/mcp_server/macos/macos_coordinates.py

Status: Experimental

Features:
- Retina display support
- Accessibility API integration
- Mission Control handling
```

---

## Data Flow

### Click Operation Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. AI Agent Request                                              │
│    Tool: click_element                                           │
│    Params: {method: "text", value: "Submit"}                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. DOM Extraction                                                │
│    - Playwright executes JavaScript in browser                  │
│    - Extracts all elements with:                                │
│      * Bounding boxes (viewport & page coords)                  │
│      * Text content, ARIA labels                                │
│      * Interactive state, z-index                               │
│    - Returns DOMStructure object                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Element Finding                                               │
│    CoordinateMapper searches:                                   │
│    - By text: "Submit" in text_content, inner_text, aria_label │
│    - Filters: clickable=true, visible=true                      │
│    - Returns: List of candidate elements                        │
│    Result: [<button id="submit-btn" text="Submit">]            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Coordinate Calculation                                        │
│    From element bounding box:                                   │
│    - Viewport: (400, 300) [center of element]                  │
│    - Page: (400, 1800) [accounting for scroll=1500px]          │
│    - Screen CSS: (900, 500) [+window position]                 │
│    - Screen Physical: (1350, 750) [×DPR=1.5]                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Pre-Click Validation                                          │
│    ✓ Element visible (opacity, display, visibility)            │
│    ✓ Element enabled (not disabled)                            │
│    ✓ Not occluded (check z-index, pointer-events)              │
│    ✓ Stable position (not animating)                           │
│    ✓ Coordinates hit target element                            │
│    Confidence: 0.95                                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Execute Click                                                 │
│    Options:                                                      │
│    A. Playwright click (recommended)                            │
│       page.mouse.click(viewport_x, viewport_y)                  │
│    B. JavaScript click                                          │
│       element.click()                                            │
│    C. OS-level click (via pyautogui, xdotool)                  │
│       click_at(physical_x, physical_y)                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Post-Click Verification                                       │
│    - Wait 100ms for reaction                                    │
│    - Extract new DOM structure                                  │
│    - Check for changes:                                         │
│      * URL changed (navigation)                                 │
│      * Element count changed (modal, new content)               │
│      * Expected state change (checkbox checked)                 │
│    Result: Success/Failure with details                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. Response to AI Agent                                          │
│    {                                                             │
│      "success": true,                                           │
│      "element": "button#submit-btn",                            │
│      "text": "Submit",                                          │
│      "coordinates": {"viewport": [400, 300],                    │
│                     "screen": [1350, 750]},                     │
│      "validation": {"confidence": 0.95},                        │
│      "outcome": "Navigation occurred"                           │
│    }                                                             │
└─────────────────────────────────────────────────────────────────┘
```

### Coordinate Transformation Data Flow

```
OS Screen Coordinates (physical pixels)
         │
         │ ÷ DPI scaling factor
         ▼
CSS Screen Coordinates (logical pixels)
         │
         │ - window.screenX, window.screenY
         ▼
Browser Viewport Coordinates
         │
         │ - scroll.scrollX, scroll.scrollY
         ▼
Page Coordinates (document)
         │
         │ document.elementFromPoint()
         ▼
DOM Element
```

**Reverse Direction** (DOM → OS):

```
DOM Element
         │
         │ element.getBoundingClientRect()
         ▼
Browser Viewport Coordinates
         │
         │ + scroll.scrollX, scroll.scrollY
         ▼
Page Coordinates
         │
         │ + window.screenX, window.screenY
         ▼
CSS Screen Coordinates
         │
         │ × DPI scaling factor
         ▼
OS Screen Coordinates
```

---

## Coordinate Transformation Pipeline

### Mathematical Model

The complete transformation is represented as a composition of affine transformations:

```
T_total = T_scroll × T_window × T_dpi

Where:
- T_dpi: Physical → CSS pixels (scale by 1/DPR)
- T_window: CSS screen → Viewport (translate by -window pos)
- T_scroll: Viewport → Page (translate by -scroll pos)
```

**Matrix Form**:

```
[viewport_x]   [1  0  -scroll_x]   [1  0  -window_x]   [1/DPR  0    0]   [os_x]
[viewport_y] = [0  1  -scroll_y] × [0  1  -window_y] × [0    1/DPR  0] × [os_y]
[    1     ]   [0  0      1    ]   [0  0      1    ]   [0      0    1]   [ 1  ]
```

### Sub-pixel Precision

Achieved through:

1. **Float64 precision**: All calculations use double precision floating point
2. **Kahan summation**: For critical accumulations to minimize rounding errors
3. **Condition number monitoring**: Ensure matrix is well-conditioned (< 100)
4. **RANSAC calibration**: Robust to measurement outliers
5. **Iterative refinement**: Improve solution through weighted least squares

**Validation**:
- Round-trip error: < 1/256 pixel (0.004 px)
- Mean error: < 1e-11 pixels
- Max error: < 1e-10 pixels

---

## Integration Points

### 1. MCP Protocol Integration

**JSON-RPC over stdio**:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "click_element",
    "arguments": {
      "method": "text",
      "value": "Submit",
      "validate": true
    }
  }
}
```

**Response**:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "element": "button#submit-btn",
    "coordinates": {"x": 650, "y": 450}
  }
}
```

### 2. Browser Integration (Playwright)

**CDP (Chrome DevTools Protocol)**:
- Direct control over browser rendering
- Access to accessibility tree
- Element inspection
- JavaScript execution in page context

**Playwright API**:
- Page automation
- Screenshot capture
- Event interception
- Network monitoring

### 3. Operating System Integration

**Windows**:
- `ctypes` for Windows API calls
- `win32api`, `win32gui` for window management
- DPI awareness registration

**Linux**:
- `xdotool` for X11 automation
- `ydotool` for Wayland support
- D-Bus for desktop environment integration

**macOS**:
- Accessibility API via `pyobjc`
- Quartz for window management
- Core Graphics for coordinate systems

### 4. Vision AI Integration (Optional)

**YOLOv8 for UI Detection**:
```python
from ultralytics import YOLO

model = YOLO('ui-elements-yolov8.pt')
results = model(screenshot)
elements = results[0].boxes
```

**OCR for Text**:
```python
import pytesseract

text_regions = pytesseract.image_to_data(screenshot, output_type='dict')
```

---

## Design Decisions

### 1. Why Playwright over Selenium?

**Chosen**: Playwright

**Reasons**:
- Built-in waiting and retry mechanisms
- Direct CDP access for accessibility tree
- Better multi-browser support
- Faster execution
- Auto-waits for element actionability

### 2. Why Affine Transformations?

**Chosen**: Affine transformations (6 DOF)

**Not Chosen**: Perspective transformations (8 DOF)

**Reasons**:
- Sufficient for flat screens (no perspective distortion)
- Simpler calibration (3 points minimum vs 4)
- Faster computation
- Better numerical stability
- Parallel lines remain parallel

### 3. Why Multiple Finding Strategies?

**Strategies**:
1. Text-based (most robust to layout changes)
2. Selector-based (most precise when available)
3. Coordinate-based (when other info not available)
4. Accessibility-based (most semantic)

**Reason**: No single strategy works in all cases. Fallback chain ensures reliability.

### 4. Why Pre-Click Validation?

**Validation before execution**:
- Prevents wasted clicks on invisible elements
- Detects overlapping elements early
- Provides confidence scores to AI agent
- Enables retry with alternative strategies

**Cost**: ~2-3ms overhead per click
**Benefit**: 30-50% reduction in failed clicks

### 5. Why Cache DOM Structure?

**TTL**: 1-2 seconds

**Benefits**:
- Multiple operations per extraction
- Consistent view during multi-step actions
- Performance (avoid repeated extractions)

**Tradeoffs**:
- Must invalidate on navigation
- May miss rapid dynamic changes
- Memory overhead (~100KB per snapshot)

---

## Performance Considerations

### Bottlenecks

1. **DOM Extraction**: Slowest operation (50-1200ms)
   - **Mitigation**: Cache for 1-2 seconds
   - **Optimization**: Extract only visible viewport

2. **Vision Validation**: 100-500ms per inference
   - **Mitigation**: Optional, use only when needed
   - **Optimization**: GPU acceleration, model quantization

3. **Network Latency**: MCP over network adds RTT
   - **Mitigation**: Use stdio transport when possible
   - **Optimization**: Batch operations

### Memory Usage

| Component | Memory | Notes |
|-----------|--------|-------|
| Server Base | ~50 MB | Python runtime + libraries |
| DOM Cache | ~100 KB | Per snapshot |
| Browser (Playwright) | ~200 MB | Chromium instance |
| Vision Models (optional) | ~500 MB | YOLOv8 + OCR |
| **Total** | ~250-750 MB | Depending on features |

### Scalability

**Single Instance**:
- Handles 1 browser at a time
- Sequential operation (one click at a time)
- Suitable for single AI agent

**Multi-Instance**:
- Run multiple servers for parallel browsers
- Each server manages one browser
- Coordinate via external orchestrator

---

## Security Considerations

### 1. Input Validation

All inputs sanitized:
- CSS selectors: Parsed and validated
- Coordinates: Range-checked
- Text queries: Escaped for injection protection

### 2. Sandboxing

Browser runs in isolated process:
- Playwright launches Chrome with `--no-sandbox` disabled
- Separate user data directory per instance
- No persistent cookies/storage

### 3. Permissions

Requires:
- Screen capture (for screenshots)
- Input simulation (for clicks)
- Process creation (for browser)

Does NOT require:
- Elevated privileges (no admin/root)
- Network access (unless browser navigates)
- File system write (except temp directory)

---

## Future Enhancements

1. **Real-time DOM Streaming**: WebSocket-based live updates instead of polling
2. **GPU Acceleration**: CUDA for vision validation
3. **Multi-browser**: Firefox, Safari support
4. **Distributed Mode**: Multiple browsers across machines
5. **Recording/Replay**: Capture interaction sequences for debugging
6. **ML Refinement**: Learn better click strategies from feedback

---

**Next**: See [API.md](API.md) for detailed API documentation.
