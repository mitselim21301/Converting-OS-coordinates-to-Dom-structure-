# Vision-Based Validation System

Production-ready vision validation for coordinate verification with graceful dependency handling.

## Features

- **Template Matching**: OpenCV-based template matching with multi-scale support
- **Feature Matching**: ORB feature detection for rotation-invariant matching
- **OCR Validation**: Text verification using Tesseract or EasyOCR
- **Edge Detection**: Canny edge detection for UI element boundaries
- **Color Profile**: Color-based element verification
- **Hybrid Validation**: Combines multiple methods with confidence scoring
- **DOM Integration**: Validates DOM coordinates against visual appearance
- **Graceful Degradation**: Works with partial dependencies installed

## Installation

### Basic Installation (required)
```bash
pip install numpy Pillow
```

### Full Installation (recommended)
```bash
pip install numpy Pillow opencv-python pytesseract mss
```

### Optional Enhancements
```bash
# For better OCR (larger download)
pip install easyocr

# For GPU-accelerated vision (if you have CUDA)
pip install opencv-contrib-python
```

### System Requirements

**Tesseract OCR** (for text validation):
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
```

## Quick Start

### Check Available Features
```python
from mcp_server.vision import check_dependencies, print_status

# Check what's available
print_status()

# Get dependency status
deps = check_dependencies()
if deps['opencv']:
    print("OpenCV available - all validators enabled")
```

### Basic Template Matching
```python
from mcp_server.vision import (
    TemplateMatchingValidator,
    BoundingBox,
    capture_screen
)

# Capture screenshot
screenshot = capture_screen()

# Load template
validator = TemplateMatchingValidator(threshold=0.8)

# Validate
result = validator.multi_scale_validate(screenshot, template)

if result.success:
    print(f"Found at: {result.bbox.to_dict()}")
    print(f"Confidence: {result.confidence:.2%}")
```

### OCR Text Validation
```python
from mcp_server.vision import OCRValidator, capture_region, BoundingBox

# Capture button region
bbox = BoundingBox(x=100, y=200, width=150, height=50)
screenshot = capture_region(bbox)

# Validate text
validator = OCRValidator(confidence_threshold=0.6)
result = validator.validate_text_at_location(
    screenshot,
    expected_text="Submit"
)

if result.success:
    print(f"Text found: {result.metadata['found_text']}")
```

### Hybrid Validation
```python
from mcp_server.vision import (
    HybridValidator,
    ValidationConfig,
    BoundingBox
)

# Create validator with custom weights
validator = HybridValidator()

# Configure validation
config = ValidationConfig(
    methods=['template_matching', 'ocr', 'edge_detection'],
    expected_text='Click Me',
    template_path='button_template.png',
    confidence_threshold=0.7
)

# Validate
bbox = BoundingBox(x=100, y=200, width=200, height=50)
result = validator.validate(bbox, config)

print(f"Overall confidence: {result.overall_confidence:.2%}")
print(f"Success rate: {result.success_rate:.2%}")
print(f"Recommendation: {result.recommendation}")

# Check individual results
for method, method_result in result.results.items():
    print(f"{method}: {method_result.confidence:.2%}")
```

### DOM + Vision Validation
```python
from mcp_server.vision import DOMVisionValidator, BoundingBox

# Validate DOM coordinates match visual appearance
validator = DOMVisionValidator()

result = validator.validate_dom_coordinates(
    dom_bbox=BoundingBox(x=100, y=200, width=150, height=40),
    expected_properties={
        'text': 'Submit Button',
        'color': (0, 120, 215)  # RGB
    }
)

if result.overall_confidence > 0.8:
    print("DOM coordinates validated!")
```

### Pre-Click Validation
```python
from mcp_server.vision import ClickValidator

validator = ClickValidator()

# Validate before clicking
result = validator.pre_click_validate(
    click_coords=(250, 350),
    expected_element={
        'type': 'button',
        'text': 'Submit',
        'width': 120,
        'height': 40
    }
)

if result.overall_confidence > 0.7:
    print("Safe to click!")
    # Perform click here
else:
    print(f"Not safe: {result.recommendation}")
```

### Coordinate Transformation Validation
```python
from mcp_server.vision import DOMVisionValidator, BoundingBox

validator = DOMVisionValidator()

# Validate OS to DOM coordinate transformation
result = validator.validate_coordinate_transformation(
    os_bbox=BoundingBox(x=500, y=300, width=200, height=50),
    dom_bbox=BoundingBox(x=450, y=250, width=200, height=50),
    tolerance=0.95
)

if result.success:
    print(f"Transformation valid: {result.confidence:.2%}")
```

## Configuration

### Custom Confidence Weights
```python
from mcp_server.vision import HybridValidator, ConfidenceWeights

weights = ConfidenceWeights(
    template_matching=0.4,
    feature_matching=0.3,
    ocr=0.2,
    edge_detection=0.1
)

validator = HybridValidator(weights=weights)
```

### OCR Engine Selection
```python
from mcp_server.vision import OCRValidator

# Auto-select best available
validator = OCRValidator(engine='auto')

# Force specific engine
tesseract_validator = OCRValidator(engine='tesseract')
easyocr_validator = OCRValidator(engine='easyocr')
```

### Screenshot Backend
```python
from mcp_server.vision import ScreenCapture

# Auto-select (prefers mss for speed)
capture = ScreenCapture(backend='auto')

# Force PIL
capture = ScreenCapture(backend='pil')

# Force mss (faster)
capture = ScreenCapture(backend='mss')
```

## Error Handling

All validators handle missing dependencies gracefully:

```python
from mcp_server.vision import TemplateMatchingValidator

validator = TemplateMatchingValidator()
result = validator.validate(screenshot, template)

if result.error:
    print(f"Validation error: {result.error}")
    # Common errors:
    # - "OpenCV not available"
    # - "No template provided"
    # - "Template larger than screenshot"
```

## Performance Tips

1. **Use mss for screenshots** (3-5x faster than PIL)
2. **Enable result caching** for repeated validations
3. **Use scale-invariant matching** only when needed
4. **Preprocess images** for better OCR accuracy
5. **Choose appropriate confidence thresholds**

```python
# Enable caching
validator = HybridValidator(enable_cache=True)

# Disable scale-invariant for speed
config = ValidationConfig(scale_invariant=False)
```

## Troubleshooting

### OpenCV Not Found
```bash
pip install opencv-python
# Or for full features:
pip install opencv-contrib-python
```

### Tesseract Not Found
```python
# Set tesseract path manually (Windows)
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Poor OCR Accuracy
- Ensure good image quality (high contrast)
- Preprocess images (included automatically)
- Try different OCR engines
- Increase image resolution

### Low Confidence Scores
- Adjust confidence thresholds
- Use multiple validation methods
- Check template quality
- Verify color/text expectations

## API Reference

See inline documentation for detailed API reference:
```python
from mcp_server.vision import HybridValidator
help(HybridValidator)
```

## Dependencies

| Package | Required | Purpose |
|---------|----------|---------|
| numpy | Yes | Array operations |
| Pillow | Recommended | Image capture |
| opencv-python | Recommended | Template/feature matching |
| pytesseract | Optional | OCR validation |
| easyocr | Optional | Alternative OCR |
| mss | Optional | Fast screenshots |

## License

Part of the mcp-accurate-click-server project.
