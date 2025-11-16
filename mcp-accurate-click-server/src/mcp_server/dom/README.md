# DOM Extraction Module

Production-ready DOM extraction system with coordinate mapping, caching, and comprehensive element finding strategies.

## Features

### Core Capabilities
- **Complete DOM Extraction**: Extract full DOM structure with all element properties
- **Coordinate Mapping**: Map between OS coordinates, viewport coordinates, and page coordinates
- **Multiple Search Strategies**: Find elements by point, text, role, attributes, and proximity
- **Caching System**: Built-in caching with TTL support for performance
- **Incremental Updates**: Support for updating specific DOM regions
- **Large DOM Optimization**: Efficient handling of pages with 1000+ elements
- **Accessibility Support**: Full accessibility tree extraction and ARIA attribute support

### Performance Features
- **Spatial Indexing**: Grid-based spatial index for fast coordinate lookups
- **Result Caching**: Automatic caching with configurable TTL
- **Batch Processing**: Process large DOMs in configurable batches
- **Filtering Options**: Extract only needed elements to reduce overhead
- **Lazy Evaluation**: On-demand categorization of elements

### Search Capabilities
- **Point Intersection**: Find elements at specific coordinates
- **Text Search**: Exact and fuzzy text matching
- **Role-based Search**: Find elements by ARIA roles
- **Accessibility Search**: Search by accessible names and labels
- **Proximity Search**: Find elements near other elements or coordinates
- **Region Search**: Extract elements within rectangular regions
- **Attribute Search**: Find elements by HTML attributes

## Installation

The module is part of the `mcp-accurate-click-server` package:

```python
from mcp_server.dom import (
    DOMStructureExtractor,
    CoordinateMapper,
    ExtractionOptions
)
```

## Quick Start

### Basic Extraction

```python
from playwright.sync_api import sync_playwright
from mcp_server.dom import DOMStructureExtractor

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('https://example.com')

    # Extract DOM structure
    extractor = DOMStructureExtractor(page)
    structure = extractor.extract()

    print(f"Found {structure.statistics.total_elements} elements")
    print(f"Clickable: {structure.statistics.clickable_elements}")

    browser.close()
```

### Coordinate Mapping

```python
from mcp_server.dom import CoordinateMapper

# After extracting structure...
mapper = CoordinateMapper(structure)

# Find element at coordinates
element = mapper.find_element_at_point(100, 200)
if element:
    print(f"Found: {element.tag_name} at ({x}, {y})")
```

### Text-based Search

```python
# Find elements containing text
results = mapper.find_elements_by_text("Submit", exact=False)

for result in results:
    elem = result.element
    print(f"{elem.tag_name}: {elem.text_content} (confidence: {result.confidence})")

# Find clickable elements near text
clickable = mapper.find_clickable_near_text("Login", max_distance=100)
```

### With Caching

```python
from mcp_server.dom import ExtractionOptions

options = ExtractionOptions(
    use_cache=True,
    cache_ttl=120,  # 2 minutes
    include_invisible=False
)

extractor = DOMStructureExtractor(page, options)
structure = extractor.extract()  # First call: cache miss
structure = extractor.extract()  # Second call: cache hit (fast!)

# Check cache statistics
stats = extractor.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")
```

## API Reference

### DOMStructureExtractor

Main class for extracting DOM structures.

```python
class DOMStructureExtractor:
    def __init__(self, page: Page, options: Optional[ExtractionOptions] = None)
    def extract(self, force_refresh: bool = False) -> DOMStructure
    def get_cache_stats(self) -> Optional[Dict[str, Any]]
    def clear_cache(self)
```

**Methods:**
- `extract()`: Extract complete DOM structure (uses cache if enabled)
- `get_cache_stats()`: Get cache hit rate and statistics
- `clear_cache()`: Clear the extraction cache

### CoordinateMapper

Maps coordinates to DOM elements using multiple strategies.

```python
class CoordinateMapper:
    def __init__(self, dom_structure: DOMStructure)

    def find_element_at_point(
        x: float, y: float,
        coordinate_type: CoordinateType = CoordinateType.VIEWPORT,
        strategies: Optional[List[SearchStrategy]] = None
    ) -> Optional[DOMElement]

    def find_elements_by_text(
        text: str,
        exact: bool = False,
        case_sensitive: bool = False,
        include_invisible: bool = False
    ) -> List[SearchResult]

    def find_elements_by_role(
        role: str,
        name: Optional[str] = None
    ) -> List[SearchResult]

    def find_clickable_near_text(
        text: str,
        max_distance: float = 100,
        exact_text: bool = False
    ) -> List[SearchResult]

    def find_elements_in_region(
        left: float, top: float,
        right: float, bottom: float,
        element_filter: Optional[Callable] = None
    ) -> List[DOMElement]

    def get_clickable_center(element: DOMElement) -> Tuple[float, float]
    def validate_clickable(element: DOMElement, x: float, y: float) -> bool
```

### ExtractionOptions

Configuration options for DOM extraction.

```python
@dataclass
class ExtractionOptions:
    # Performance
    include_invisible: bool = False
    max_text_length: int = 500
    max_depth: Optional[int] = None

    # Filtering
    tag_filter: Optional[List[str]] = None
    class_filter: Optional[List[str]] = None
    exclude_tags: Optional[List[str]] = None

    # Features
    extract_aria: bool = True
    extract_computed_styles: bool = True
    extract_attributes: bool = True

    # Caching
    use_cache: bool = True
    cache_ttl: int = 60  # seconds
    batch_size: int = 100
```

### Data Models

#### DOMElement

Comprehensive representation of a DOM element.

**Properties:**
- `tag_name`: HTML tag name
- `element_id`: Element ID attribute
- `class_names`: List of CSS classes
- `role`: ARIA role
- `aria_label`: ARIA label
- `accessible_name`: Computed accessible name
- `text_content`: Text content
- `bounding_box`: Position and size (BoundingBox)
- `visible`: Visibility state
- `enabled`: Enabled state
- `focusable`: Can receive focus
- `clickable`: Can be clicked
- `xpath`: XPath selector
- `css_selector`: CSS selector
- `attributes`: All HTML attributes
- `uid`: Unique identifier

#### DOMStructure

Complete DOM structure snapshot.

**Properties:**
- `url`: Page URL
- `title`: Page title
- `timestamp`: Extraction timestamp
- `viewport`: Viewport information (ViewportInfo)
- `elements`: All extracted elements
- `interactive_elements`: Interactive elements only
- `text_elements`: Elements with text content
- `form_elements`: Form-related elements
- `clickable_elements`: Clickable elements only
- `statistics`: Extraction statistics (DOMStatistics)

#### SearchResult

Result from element search with confidence scoring.

**Properties:**
- `element`: Found DOM element
- `confidence`: Confidence score (0.0 - 1.0)
- `strategy`: Search strategy used
- `distance`: Distance from target (optional)
- `match_score`: Text match score (optional)

### Search Strategies

Available search strategies for element finding:

- `SearchStrategy.POINT_INTERSECTION`: Elements containing the point
- `SearchStrategy.NEAREST_CLICKABLE`: Nearest clickable element
- `SearchStrategy.TEXT_MATCH`: Text content matching
- `SearchStrategy.ACCESSIBILITY`: Accessibility tree search
- `SearchStrategy.VISUAL_PROXIMITY`: Visual distance-based
- `SearchStrategy.Z_INDEX_PRIORITY`: Highest z-index first

## Advanced Usage

### Large DOM Optimization

For pages with 1000+ elements:

```python
options = ExtractionOptions(
    include_invisible=False,    # Skip hidden elements
    max_text_length=200,        # Limit text content
    max_depth=15,              # Limit nesting depth
    exclude_tags=['script', 'style'],  # Skip unnecessary tags
    use_cache=True,
    batch_size=100
)
```

### Filtering by Tag or Class

Extract only specific element types:

```python
options = ExtractionOptions(
    tag_filter=['a', 'button', 'input'],  # Only these tags
    exclude_tags=['script', 'style'],      # Exclude these
    class_filter=['btn', 'link']           # Only elements with these classes
)
```

### Region-based Search

Find elements in specific viewport regions:

```python
# Top-left quarter of viewport
elements = mapper.find_elements_in_region(
    left=0, top=0,
    right=viewport_width // 2,
    bottom=viewport_height // 2,
    element_filter=lambda e: e.clickable  # Only clickable
)
```

### Accessibility Analysis

```python
from mcp_server.dom.utils import get_accessibility_summary

summary = get_accessibility_summary(structure)
print(f"Accessibility score: {summary['accessibility_score']:.1f}/100")
print(f"Label coverage: {summary['label_coverage_percent']:.1f}%")
```

### Export and Persistence

```python
from mcp_server.dom.utils import (
    save_structure_to_json,
    export_clickable_coordinates
)

# Save complete structure
save_structure_to_json(structure, 'dom_structure.json')

# Export clickable coordinates to CSV
export_clickable_coordinates(structure, 'clickable.csv')
```

## Performance Considerations

### Caching

- Default cache TTL: 60 seconds
- Cache size limit: 100 entries
- Cache invalidation on page navigation
- Per-viewport caching (different sizes = different cache entries)

### Memory Usage

For a typical page:
- ~1000 elements: ~1-2 MB memory
- ~5000 elements: ~5-10 MB memory
- ~10000 elements: ~15-20 MB memory

### Extraction Speed

Typical extraction times:
- Small page (<500 elements): 50-100ms
- Medium page (500-2000 elements): 100-300ms
- Large page (2000-5000 elements): 300-800ms
- Very large page (>5000 elements): 800-2000ms

Cached retrieval: <1ms

## Error Handling

The module includes comprehensive error handling:

```python
try:
    structure = extractor.extract()
except RuntimeError as e:
    logger.error(f"Extraction failed: {e}")
    # Handle error...
```

Common errors:
- `RuntimeError`: Extraction failed (page not loaded, browser crashed, etc.)
- `PlaywrightError`: Playwright-specific errors (element not found, timeout, etc.)

## Logging

Configure logging to see detailed extraction information:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('mcp_server.dom')
```

Log levels:
- `DEBUG`: Detailed extraction progress, cache operations
- `INFO`: Extraction summary, cache hits/misses
- `WARNING`: Potential issues, obscured elements
- `ERROR`: Extraction failures, critical errors

## Testing

Run the comprehensive example:

```bash
python examples/dom_extraction_example.py
```

Run module tests:

```bash
pytest tests/test_dom_extraction.py
```

## License

Part of the MCP Accurate Click Server project.
