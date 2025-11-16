# Implementation Guide
## Getting Started with Vision-Based Coordinate Validation

---

## Quick Start

### 1. Installation

#### Python Dependencies

Create a `requirements.txt`:

```txt
# Core Computer Vision
opencv-python>=4.8.0
opencv-contrib-python>=4.8.0
numpy>=1.24.0
pillow>=10.0.0
scikit-image>=0.21.0
mss>=9.0.0

# OCR Libraries
pytesseract>=0.3.10
easyocr>=1.7.0
paddleocr>=2.7.0

# Object Detection / AI
ultralytics>=8.0.0  # YOLOv8
torch>=2.0.0
torchvision>=0.15.0
transformers>=4.30.0
detectron2  # Install separately, see below

# Image Comparison
imagehash>=4.3.1
scikit-learn>=1.3.0

# Browser Automation
playwright>=1.40.0
selenium>=4.15.0
pyautogui>=0.9.54

# AI APIs (optional)
openai>=1.0.0
anthropic>=0.7.0

# Utilities
python-dotenv>=1.0.0
aiohttp>=3.9.0
requests>=2.31.0
```

Install with:
```bash
pip install -r requirements.txt
```

#### Special Installation: Detectron2

Detectron2 requires special installation:

```bash
# For CUDA 11.8
python -m pip install 'git+https://github.com/facebookresearch/detectron2.git'

# Or for CPU only
python -m pip install detectron2 -f \
  https://dl.fbaipublicfiles.com/detectron2/wheels/cpu/torch2.0/index.html
```

#### System Dependencies

**Tesseract OCR:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-eng

# macOS
brew install tesseract

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

**Playwright Browsers:**
```bash
playwright install chromium firefox webkit
```

---

### 2. Project Structure

```
project/
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration
├── core/
│   ├── __init__.py
│   ├── coordinate_transform.py  # Coordinate transformations
│   ├── validation.py        # Validation orchestrator
│   └── models.py           # Data models
├── validators/
│   ├── __init__.py
│   ├── vision.py           # Vision-based validation
│   ├── ocr.py             # OCR validation
│   ├── ai.py              # AI-powered validation
│   └── template.py        # Template matching
├── utils/
│   ├── __init__.py
│   ├── screenshot.py      # Screenshot utilities
│   ├── cache.py          # Caching
│   └── metrics.py        # Performance metrics
├── tests/
│   ├── test_validation.py
│   └── test_transforms.py
├── examples/
│   ├── simple_click.py
│   └── form_filling.py
├── requirements.txt
├── setup.py
└── README.md
```

---

### 3. Basic Configuration

Create `config/settings.py`:

```python
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent.parent
CACHE_DIR = BASE_DIR / "cache"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
MODELS_DIR = BASE_DIR / "models"

# Create directories
for dir_path in [CACHE_DIR, SCREENSHOTS_DIR, MODELS_DIR]:
    dir_path.mkdir(exist_ok=True)

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Validation Settings
VALIDATION_SETTINGS = {
    "default_strategy": "balanced",
    "confidence_threshold": 0.75,
    "cache_ttl": 5,  # seconds
    "max_retries": 3,
    "timeout": 30,  # seconds
}

# Vision Settings
VISION_SETTINGS = {
    "template_matching_threshold": 0.8,
    "feature_matching_min_matches": 10,
    "ocr_confidence_threshold": 0.6,
    "edge_detection_min_area": 100,
}

# AI Settings
AI_SETTINGS = {
    "provider": "openai",  # or "anthropic"
    "model": "gpt-4o",
    "max_tokens": 1000,
    "temperature": 0.1,
}

# Browser Settings
BROWSER_SETTINGS = {
    "default_browser": "chromium",
    "headless": False,
    "slow_mo": 50,  # milliseconds
}

# Display Settings
DISPLAY_SETTINGS = {
    "screenshot_format": "png",
    "screenshot_quality": 95,
    "scale_detection_auto": True,
}
```

Create `.env`:
```bash
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

---

### 4. Minimal Working Example

Create `examples/minimal_example.py`:

```python
"""
Minimal working example of coordinate validation
"""

import asyncio
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from implementation_examples import (
    HybridCoordinateValidator,
    BoundingBox,
    ScreenCapture,
    ValidationMethod
)


async def main():
    """Simple coordinate validation example"""

    print("Initializing validator...")
    validator = HybridCoordinateValidator()

    # Define the region to validate
    bbox = BoundingBox(x=100, y=100, width=200, height=100)

    print(f"Capturing screenshot at {bbox.to_dict()}...")
    screenshot = ScreenCapture.capture_region(bbox)

    # Save for inspection
    ScreenCapture.save_screenshot(screenshot, "test_screenshot.png")
    print("Screenshot saved as test_screenshot.png")

    # Define what we're looking for
    validation_config = {
        'expected_text': 'Hello',  # Text we expect to find
        'bbox': bbox,
        'methods': ['ocr', 'edge_detection']  # Validation methods to use
    }

    print("Running validation...")
    results = validator.validate(screenshot, validation_config)

    # Print results
    print("\nValidation Results:")
    print("-" * 50)

    for method, result in results.items():
        print(f"\n{method}:")
        print(f"  Success: {result.success}")
        print(f"  Confidence: {result.confidence:.2%}")
        if result.metadata:
            print(f"  Metadata: {result.metadata}")

    # Overall confidence
    overall_confidence = validator.get_overall_confidence(results)
    print(f"\nOverall Confidence: {overall_confidence:.2%}")

    if overall_confidence > 0.7:
        print("\n✓ Validation PASSED")
    else:
        print("\n✗ Validation FAILED")


if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python examples/minimal_example.py
```

---

### 5. Browser Integration Example

Create `examples/browser_validation.py`:

```python
"""
Example using Playwright for browser-based validation
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from implementation_examples import (
    HybridCoordinateValidator,
    BoundingBox
)


async def main():
    """Validate element in browser"""

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        page = await p.new_page()

        # Navigate to page
        await page.goto("https://example.com")

        # Get button element
        button = page.locator("text=More information")
        await button.wait_for()

        # Get element bounding box
        bbox = await button.bounding_box()
        print(f"Element bounding box: {bbox}")

        # Take screenshot
        screenshot_bytes = await page.screenshot()

        # Get viewport position to convert to OS coordinates
        viewport = page.viewport_size

        print(f"Viewport size: {viewport}")

        # In a real scenario, you would:
        # 1. Convert browser coords to OS coords
        # 2. Validate the OS coordinates
        # 3. Perform action if validated

        # Example: Take element screenshot for template
        element_screenshot = await button.screenshot()

        # Save template
        with open("button_template.png", "wb") as f:
            f.write(element_screenshot)

        print("Element template saved as button_template.png")

        # Close browser
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
```

---

### 6. AI-Powered Validation Example

Create `examples/ai_validation.py`:

```python
"""
Example using AI for semantic validation
"""

import asyncio
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


async def main():
    """AI-powered element detection"""

    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not set")
        print("Set it in .env file or export OPENAI_API_KEY=your-key")
        return

    # Import after API key check
    import openai
    import base64
    import json

    # Take a screenshot (placeholder - replace with actual screenshot)
    screenshot_path = "test_screenshot.png"

    if not Path(screenshot_path).exists():
        print(f"Error: {screenshot_path} not found")
        print("Run minimal_example.py first to create a test screenshot")
        return

    # Load image
    with open(screenshot_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    print("Analyzing screenshot with GPT-4 Vision...")

    # Ask AI to find elements
    response = await openai.ChatCompletion.acreate(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Analyze this screenshot and identify all interactive elements.

For each element, provide:
1. Type (button, input, link, etc.)
2. Approximate bounding box (x, y, width, height)
3. Text or label
4. Confidence (0.0-1.0)

Return as JSON array."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ],
        max_tokens=1000
    )

    # Parse response
    result_text = response.choices[0].message.content

    print("\nAI Analysis Result:")
    print("-" * 50)
    print(result_text)

    # Try to parse as JSON
    try:
        elements = json.loads(result_text)
        print("\nDetected Elements:")
        for i, elem in enumerate(elements, 1):
            print(f"\n{i}. {elem.get('type', 'unknown')}")
            print(f"   Label: {elem.get('label', elem.get('text', 'N/A'))}")
            print(f"   BBox: {elem.get('bounding_box', elem.get('bbox', 'N/A'))}")
            print(f"   Confidence: {elem.get('confidence', 'N/A')}")
    except json.JSONDecodeError:
        print("\nNote: Response was not in JSON format")


if __name__ == "__main__":
    asyncio.run(main())
```

---

### 7. Complete Integration Example

Create `examples/complete_workflow.py`:

```python
"""
Complete workflow: Browser automation with vision validation
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import sys
import pyautogui

sys.path.insert(0, str(Path(__file__).parent.parent))

from implementation_examples import (
    HybridCoordinateValidator,
    BoundingBox,
    ScreenCapture
)


async def validated_click(x, y, element_description):
    """
    Perform a click with vision-based validation

    Args:
        x, y: OS coordinates
        element_description: What we expect to find
    """
    validator = HybridCoordinateValidator()

    # Pre-click validation
    print(f"\nValidating click at ({x}, {y})...")
    print(f"Expected: {element_description}")

    # Capture region
    bbox = BoundingBox(x=x-50, y=y-50, width=100, height=100)
    screenshot = ScreenCapture.capture_region(bbox)

    # Validate
    validation_config = {
        'expected_text': element_description.get('text', ''),
        'bbox': BoundingBox(x=40, y=40, width=20, height=20),  # Center of captured region
        'methods': ['ocr', 'edge_detection']
    }

    results = validator.validate(screenshot, validation_config)
    confidence = validator.get_overall_confidence(results)

    print(f"Validation confidence: {confidence:.2%}")

    if confidence > 0.7:
        print("✓ Validation passed - executing click")
        pyautogui.click(x, y)

        # Post-click validation
        await asyncio.sleep(0.5)
        print("✓ Click executed")

        return True
    else:
        print("✗ Validation failed - click aborted")
        return False


async def main():
    """Complete automated workflow with validation"""

    async with async_playwright() as p:
        # Launch browser
        print("Launching browser...")
        browser = await p.chromium.launch(headless=False)
        page = await p.new_page(viewport={'width': 1280, 'height': 720})

        # Navigate
        print("Navigating to page...")
        await page.goto("https://example.com")
        await page.wait_for_load_state("networkidle")

        # Get browser window position
        # In real implementation, you'd get actual window position
        window_x, window_y = 100, 100

        # Find element we want to click
        element = page.locator("text=More information")
        await element.wait_for()

        # Get element bounding box in browser
        bbox = await element.bounding_box()

        if bbox:
            # Calculate OS coordinates
            # browser_chrome_height = 90  # Approximate
            os_x = int(window_x + bbox['x'] + bbox['width'] / 2)
            os_y = int(window_y + bbox['y'] + bbox['height'] / 2)

            print(f"\nElement found at browser coords: {bbox}")
            print(f"Calculated OS coords: ({os_x}, {os_y})")

            # Perform validated click
            success = await validated_click(
                os_x, os_y,
                {'text': 'More information'}
            )

            if success:
                print("\n✓ Workflow completed successfully")
            else:
                print("\n✗ Workflow failed")

        else:
            print("Element not found")

        # Keep browser open for inspection
        await asyncio.sleep(3)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 8. Testing

Create `tests/test_validation.py`:

```python
"""
Unit tests for validation system
"""

import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from implementation_examples import (
    HybridCoordinateValidator,
    TemplateMatchingValidator,
    OCRValidator,
    BoundingBox,
    ValidationMethod
)


class TestTemplateMatching:
    """Test template matching validator"""

    def test_exact_match(self):
        """Test exact template match"""
        validator = TemplateMatchingValidator(threshold=0.95)

        # Create test images (identical)
        screenshot = np.random.randint(0, 255, (500, 500, 3), dtype=np.uint8)
        template = screenshot[100:200, 100:200]

        result = validator.validate(screenshot, template)

        assert result.success
        assert result.confidence > 0.95
        assert result.bbox.x == 100
        assert result.bbox.y == 100

    def test_no_match(self):
        """Test when template doesn't match"""
        validator = TemplateMatchingValidator(threshold=0.8)

        screenshot = np.random.randint(0, 255, (500, 500, 3), dtype=np.uint8)
        template = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        result = validator.validate(screenshot, template)

        # Random images should have low confidence
        assert result.confidence < 0.5


class TestOCR:
    """Test OCR validator"""

    @pytest.mark.skipif(
        not Path("/usr/bin/tesseract").exists(),
        reason="Tesseract not installed"
    )
    def test_text_detection(self):
        """Test OCR text detection"""
        from PIL import Image, ImageDraw, ImageFont

        # Create test image with text
        img = Image.new('RGB', (200, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 40), "Hello World", fill='black')

        # Convert to numpy
        img_array = np.array(img)

        validator = OCRValidator(confidence_threshold=0.5)
        result = validator.validate_text_at_location(
            img_array,
            "Hello"
        )

        assert result.success
        assert "hello" in result.metadata['found_text'].lower()


class TestHybridValidator:
    """Test hybrid validation system"""

    def test_multiple_methods(self):
        """Test running multiple validation methods"""
        validator = HybridCoordinateValidator()

        # Create test screenshot
        screenshot = np.random.randint(0, 255, (500, 500, 3), dtype=np.uint8)

        config = {
            'bbox': BoundingBox(x=100, y=100, width=100, height=100),
            'methods': ['edge_detection']
        }

        results = validator.validate(screenshot, config)

        assert 'edge_detection' in results
        assert results['edge_detection'].method == ValidationMethod.EDGE_DETECTION

    def test_confidence_aggregation(self):
        """Test confidence score aggregation"""
        validator = HybridCoordinateValidator()

        # Mock results
        from implementation_examples import ValidationResult

        results = {
            'method1': ValidationResult(
                method=ValidationMethod.TEMPLATE_MATCHING,
                success=True,
                confidence=0.9
            ),
            'method2': ValidationResult(
                method=ValidationMethod.OCR,
                success=True,
                confidence=0.8
            )
        }

        confidence = validator.get_overall_confidence(results)

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.8  # Should be high since both methods passed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

Run tests:
```bash
pytest tests/ -v
```

---

## 9. Performance Optimization Tips

### 1. Use Caching
```python
# Cache validation results for recently checked coordinates
from functools import lru_cache

@lru_cache(maxsize=100)
def validate_cached(coords_key, element_hash):
    # Validation logic
    pass
```

### 2. Parallel Processing
```python
import asyncio

async def validate_multiple_elements(elements):
    """Validate multiple elements in parallel"""
    tasks = [validate_element(elem) for elem in elements]
    results = await asyncio.gather(*tasks)
    return results
```

### 3. Use Appropriate Image Resolution
```python
# Downscale screenshots for faster processing
def downscale_if_needed(image, max_dimension=1920):
    h, w = image.shape[:2]
    if max(h, w) > max_dimension:
        scale = max_dimension / max(h, w)
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(image, (new_w, new_h))
    return image
```

### 4. GPU Acceleration
```python
# Use CUDA for AI models
import torch

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)
```

---

## 10. Troubleshooting

### Common Issues

**1. Tesseract not found:**
```bash
# Ubuntu
sudo apt-get install tesseract-ocr

# Set TESSDATA_PREFIX if needed
export TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/
```

**2. OpenCV import errors:**
```bash
pip uninstall opencv-python opencv-contrib-python
pip install opencv-contrib-python
```

**3. Playwright browsers not installed:**
```bash
playwright install
```

**4. Low OCR accuracy:**
```python
# Preprocess image before OCR
import cv2

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
text = pytesseract.image_to_string(thresh)
```

**5. CUDA out of memory:**
```python
# Reduce batch size or use CPU
device = torch.device('cpu')
```

---

## 11. Next Steps

1. **Collect Training Data:** Gather screenshots of your specific UI for training custom models
2. **Fine-tune Models:** Train YOLO or DETR on your UI elements
3. **Build Template Library:** Create templates for common elements
4. **Implement Logging:** Add comprehensive logging for debugging
5. **Add Monitoring:** Track validation performance metrics
6. **Scale Up:** Implement distributed validation for parallel testing

---

## 12. Resources

### Documentation
- OpenCV: https://docs.opencv.org/
- Tesseract OCR: https://tesseract-ocr.github.io/
- Playwright: https://playwright.dev/python/
- YOLOv8: https://docs.ultralytics.com/
- Transformers: https://huggingface.co/docs/transformers/

### Datasets
- Rico: http://interactionmining.org/rico
- CLAY: https://github.com/google-research/google-research/tree/master/clay
- Common Objects in Context (COCO): https://cocodataset.org/

### Communities
- r/computervision: https://reddit.com/r/computervision
- OpenCV Forum: https://forum.opencv.org/
- Hugging Face: https://discuss.huggingface.co/

---

This implementation guide should get you started with vision-based coordinate validation. Start with the minimal example and gradually add more sophisticated validation methods as needed.
