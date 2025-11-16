# MCP Accurate Click Server - Examples

Comprehensive examples demonstrating all features of the MCP Accurate Click Server.

## Table of Contents

- [Quick Start](#quick-start)
- [Examples Overview](#examples-overview)
- [Prerequisites](#prerequisites)
- [Running Examples](#running-examples)
- [Example Descriptions](#example-descriptions)
- [Common Issues](#common-issues)
- [Learning Path](#learning-path)

## Quick Start

```bash
# 1. Install dependencies
pip install -r ../requirements.txt

# 2. Install Playwright browsers
playwright install chromium

# 3. Run basic example
python basic_usage.py

# 4. Explore other examples
python advanced_usage.py
python form_filling.py
python multi_monitor.py
python vision_validation.py
```

## Examples Overview

| Example | Difficulty | Features | Runtime |
|---------|-----------|----------|---------|
| `basic_usage.py` | Beginner | DOM extraction, simple clicking | ~10s |
| `form_filling.py` | Beginner | Form automation, field detection | ~15s |
| `advanced_usage.py` | Intermediate | Multi-step workflows, caching | ~20s |
| `multi_monitor.py` | Intermediate | Multi-monitor coordination | ~15s |
| `vision_validation.py` | Advanced | OCR, visual validation | ~20s |

## Prerequisites

### Required Dependencies

```bash
# Core dependencies (required for all examples)
pip install playwright numpy

# Install Playwright browsers
playwright install chromium
```

### Optional Dependencies

For vision validation example:

```bash
# Computer vision (required for vision_validation.py)
pip install opencv-python pillow

# OCR (optional, enhances vision_validation.py)
pip install pytesseract

# Install Tesseract OCR engine
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract

# Windows:
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

### System Requirements

- Python 3.8 or higher
- 4GB RAM minimum
- 1GB free disk space
- Internet connection (for initial browser download)

## Running Examples

### Basic Usage Example

**What it demonstrates:**
- DOM structure extraction
- Finding elements by text
- Simple coordinate-based clicking
- Element coordinate mapping

**Run it:**
```bash
python basic_usage.py
```

**Expected output:**
- Browser window opens with test page
- DOM structure is extracted
- Elements are found and clicked
- JSON file saved to `/tmp/dom_structure.json`

**Key learning points:**
- How to extract DOM structure
- How to find elements
- How to click at specific coordinates
- Understanding coordinate systems

---

### Form Filling Example

**What it demonstrates:**
- Finding form inputs by label
- Filling text fields
- Selecting dropdown options
- Toggling checkboxes
- Form validation

**Run it:**
```bash
python form_filling.py
```

**Expected output:**
- Browser opens with form
- Form fields are automatically filled
- Form is ready for submission

**Key learning points:**
- Smart form field detection
- Multiple strategies for finding inputs
- Handling different input types
- Form state validation

---

### Advanced Usage Example

**What it demonstrates:**
- Multi-step automation workflows
- DOM structure caching
- Intelligent retry logic
- Performance monitoring
- Coordinate transformation calibration
- Session data persistence

**Run it:**
```bash
python advanced_usage.py
```

**Expected output:**
- Browser opens
- Multiple automation steps execute
- Performance statistics displayed
- Session data saved to `/tmp/automation_session.json`

**Key learning points:**
- Production-ready automation patterns
- Error handling and recovery
- Performance optimization
- State management across operations

---

### Multi-Monitor Example

**What it demonstrates:**
- Monitor detection and configuration
- Per-monitor coordinate transformations
- DPI scaling awareness
- Cross-monitor window tracking

**Run it:**
```bash
python multi_monitor.py
```

**Expected output:**
- Simulated multi-monitor setup displayed
- Per-monitor calibration performed
- Coordinate transformations demonstrated

**Key learning points:**
- Handling multiple monitors
- DPI scaling considerations
- Monitor-specific calibrations
- Coordinate system conversions

**Note:** This example simulates a multi-monitor setup. In production, it would detect actual monitors using platform-specific APIs.

---

### Vision Validation Example

**What it demonstrates:**
- Screenshot capture and analysis
- OCR text detection
- Pre-click validation
- Visual change detection
- Before/after comparison

**Run it:**
```bash
python vision_validation.py
```

**Expected output:**
- Browser opens with test page
- Screenshots captured
- Visual validation performed
- Screenshots saved to `/tmp/vision_validation/`

**Key learning points:**
- Vision-based element detection
- OCR for text validation
- Visual feedback verification
- Screenshot-based debugging

**Note:** Requires OpenCV and optionally pytesseract.

---

## Example Descriptions

### 1. basic_usage.py - Fundamentals

**Purpose:** Introduction to core concepts

**What you'll learn:**
- Extracting DOM structure with `DOMStructureExtractor`
- Creating coordinate mapper with `CoordinateMapper`
- Finding elements by text
- Finding elements at specific coordinates
- Performing basic clicks

**Use cases:**
- Simple click automation
- Element discovery
- Coordinate mapping basics

**Code highlights:**
```python
# Extract DOM structure
extractor = DOMStructureExtractor(page)
structure = extractor.extract()

# Create coordinate mapper
mapper = CoordinateMapper(structure)

# Find element by text
elements = mapper.find_elements_by_text("Example")

# Click at coordinates
page.mouse.click(element.bounding_box.center_x,
                 element.bounding_box.center_y)
```

---

### 2. form_filling.py - Form Automation

**Purpose:** Automated form interaction

**What you'll learn:**
- Finding inputs by label text
- Multiple field detection strategies
- Filling text inputs
- Selecting dropdown options
- Toggling checkboxes
- Form validation

**Use cases:**
- Form automation
- Data entry
- Multi-step form workflows

**Code highlights:**
```python
# Create form filler
filler = FormFiller(page)

# Define form data
form_data = [
    FormField(label="Full Name", field_type="text",
              value="John Doe", required=True),
    # ... more fields
]

# Fill the form
filler.fill_form(form_data)
```

---

### 3. advanced_usage.py - Production Patterns

**Purpose:** Production-ready automation

**What you'll learn:**
- DOM structure caching for performance
- Intelligent retry logic
- Multi-step workflows
- Performance monitoring
- Coordinate transformation calibration
- Session state management

**Use cases:**
- Complex automation workflows
- High-reliability applications
- Performance-critical scenarios

**Code highlights:**
```python
# Create automation context
context = AutomationContext(page=page)
automation = AdvancedClickAutomation(context)

# Smart click with retry
automation.smart_click_by_text("Submit", max_retries=2)

# Execute sequence
sequence = [("Login", False), ("Submit", False)]
automation.click_sequence(sequence)

# Show performance stats
automation.show_performance_stats()
```

---

### 4. multi_monitor.py - Multi-Monitor Support

**Purpose:** Handling multiple displays

**What you'll learn:**
- Monitor detection and configuration
- Per-monitor coordinate transformations
- DPI scaling handling
- Monitor-local coordinate conversion
- Cross-monitor window tracking

**Use cases:**
- Multi-monitor setups
- DPI-aware applications
- Cross-screen automation

**Code highlights:**
```python
# Initialize monitor manager
manager = MonitorManager()

# Detect monitors
monitors = manager.detect_monitors()

# Calibrate each monitor
for monitor in monitors:
    manager.calibrate_monitor(monitor, page)

# Transform screen to DOM
dom_x, dom_y, monitor = manager.transform_screen_to_dom(
    screen_x, screen_y
)
```

---

### 5. vision_validation.py - AI-Enhanced Clicking

**Purpose:** Vision-based validation

**What you'll learn:**
- Screenshot capture
- OCR text detection
- Visual element validation
- Before/after comparison
- Visual change detection

**Use cases:**
- Visual verification
- OCR-based automation
- Screenshot debugging
- Visual regression testing

**Code highlights:**
```python
# Create vision validator
validator = VisionValidator(page)

# Capture screenshot
screenshot = validator.capture_screenshot("page.png")

# Find text with OCR
elements = validator.find_text_visually("Submit")

# Validated click with visual feedback
validator.validated_click(element,
                         expected_text="Submit",
                         expect_visual_change=True)
```

---

## Test Page

The `test_page.html` file provides a comprehensive test environment:

- **Interactive Buttons**: Various button types to practice clicking
- **Sample Form**: Complete form with all input types
- **Interactive Cards**: Clickable card components
- **Navigation Links**: Multiple link elements
- **Click Counter**: Visual feedback for automation
- **Status Messages**: Real-time feedback display

**Features:**
- Fully styled and responsive
- Click tracking and logging
- Form submission handling
- Visual feedback on interactions

**Using the test page:**
```python
# In your code
test_page_path = Path(__file__).parent / "test_page.html"
page.goto(f"file://{test_page_path}")
```

---

## Common Issues

### Issue: ModuleNotFoundError

**Problem:** Missing dependencies

**Solution:**
```bash
pip install playwright numpy
playwright install chromium
```

---

### Issue: Playwright browsers not found

**Problem:** Browser binaries not installed

**Solution:**
```bash
playwright install chromium
```

---

### Issue: OCR not working

**Problem:** Tesseract not installed

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
```

---

### Issue: OpenCV import error

**Problem:** OpenCV not installed

**Solution:**
```bash
pip install opencv-python pillow
```

---

### Issue: Permission denied on /tmp

**Problem:** Cannot write to /tmp directory

**Solution:**
- Change output directory in examples
- Or: Create directory with proper permissions

---

## Learning Path

### Beginner Track

1. **Start here:** `basic_usage.py`
   - Understand DOM extraction
   - Learn coordinate mapping
   - Practice simple clicks

2. **Next:** `form_filling.py`
   - Learn form automation
   - Understand field detection
   - Practice input filling

### Intermediate Track

3. **Then:** `advanced_usage.py`
   - Learn production patterns
   - Understand performance optimization
   - Practice error handling

4. **After that:** `multi_monitor.py`
   - Learn multi-monitor handling
   - Understand coordinate transformations
   - Practice calibration

### Advanced Track

5. **Finally:** `vision_validation.py`
   - Learn vision-based validation
   - Understand OCR integration
   - Practice visual verification

---

## Tips for Success

### Best Practices

1. **Start Simple**: Begin with `basic_usage.py` to understand fundamentals

2. **Read the Code**: All examples are heavily commented - read through them

3. **Experiment**: Modify examples to test your understanding

4. **Check Output**: Examples save data to `/tmp` - inspect these files

5. **Use Test Page**: The included `test_page.html` is designed for testing

### Debugging Tips

1. **Enable Console Logging**: Check browser console for JavaScript errors

2. **Visual Inspection**: Run with `headless=False` to see what's happening

3. **Screenshot Analysis**: Use vision validation to capture debugging screenshots

4. **DOM Inspection**: Save DOM structure to JSON and analyze

5. **Performance Monitoring**: Use advanced example's performance tracking

---

## Next Steps

After completing the examples:

1. **Read Documentation**: See `../docs/` for detailed API reference

2. **Review Research**: Check research documents in root directory

3. **Build Your Own**: Create custom automation using learned patterns

4. **Contribute**: Submit examples or improvements

---

## Support

- **Issues**: Report bugs or ask questions on GitHub Issues
- **Documentation**: See `../docs/` directory
- **Research**: See root directory for detailed research documents

---

## File Structure

```
examples/
├── README.md                  # This file
├── test_page.html            # Test page for examples
├── basic_usage.py            # Basic clicking example
├── form_filling.py           # Form automation example
├── advanced_usage.py         # Advanced patterns example
├── multi_monitor.py          # Multi-monitor example
├── vision_validation.py      # Vision-based validation example
└── output/                   # Created at runtime
    ├── dom_structure.json    # From basic_usage.py
    ├── automation_session.json # From advanced_usage.py
    └── screenshots/          # From vision_validation.py
```

---

## License

MIT License - See LICENSE file for details

---

**Last Updated:** 2025-11-16
**Version:** 1.0.0
