# Linux Examples - Quick Start Guide

Get up and running with MCP Accurate Click Server on Linux in 5 minutes.

## TL;DR - Just Want to Run Something?

```bash
# 1. Install dependencies
pip install pynput playwright

# 2. Run the basic example
python3 basic_linux_click.py

# That's it! The example will:
# - Detect your display server (X11 or Wayland)
# - Launch a browser
# - Extract DOM structure
# - Demonstrate accurate clicking
```

## Choose Your Example

### I'm a Beginner
Start with **basic_linux_click.py**:
```bash
python3 basic_linux_click.py
```
This shows the fundamentals and works everywhere.

### I Have Multiple Monitors
Run **multi_monitor_linux.py**:
```bash
python3 multi_monitor_linux.py
```
This demonstrates multi-monitor support and per-monitor DPI detection.

### I'm Automating Browser Tasks
Try **browser_automation_linux.py**:
```bash
python3 browser_automation_linux.py
```
This shows how to work with different browsers and handle scaling.

### I Want to Understand DPI/Scaling
Check **dpi_detection_linux.py**:
```bash
python3 dpi_detection_linux.py
```
This explains how DPI works and shows coordinate conversion.

### I'm on X11 (Older Systems)
Run **x11_example.py** (X11 only):
```bash
python3 x11_example.py
```
This uses native X11 APIs and python-xlib.

### I'm on Wayland (Modern Systems)
Run **wayland_example.py** (Wayland only):
```bash
python3 wayland_example.py
```
This shows modern Wayland features and best practices.

## Check Your Display Server

```bash
# Quick check
echo $XDG_SESSION_TYPE

# Will output:
# x11      → You're on X11
# wayland  → You're on Wayland
```

## Common Issues & Fixes

### "Module not found" error
```bash
pip install pynput playwright python-xlib
```

### Clicks not working
```bash
# Try running with sudo
sudo python3 example.py

# Or add yourself to input group
sudo usermod -a -G input $USER
newgrp input
```

### Browser not launching
```bash
# Install Chromium or Firefox
sudo apt-get install chromium-browser firefox

# Or let Playwright download them automatically
python3 -m playwright install
```

### DPI showing as 96 on HiDPI display
```bash
# Install xrandr for better DPI detection
sudo apt-get install xrandr

# Check actual DPI
xrandr --query --verbose | grep -i "connected"
```

## Next Steps

1. **Read the full README.md** for detailed information
2. **Try each example** to understand different features
3. **Explore the code** - all examples are well-commented
4. **Integrate into your project** - copy the patterns you need

## Need Help?

- Check **README.md** for troubleshooting section
- Look at example code comments for detailed explanations
- Check your system info with provided commands
- Ensure all dependencies are installed

## File Structure

```
examples/linux/
├── README.md                    # Full documentation
├── QUICK_START.md              # This file
├── basic_linux_click.py         # Start here - fundamental features
├── multi_monitor_linux.py       # Multiple monitors & scaling
├── browser_automation_linux.py  # Cross-browser automation
├── dpi_detection_linux.py       # DPI/scaling deep dive
├── x11_example.py              # X11-specific features
└── wayland_example.py          # Wayland-specific features
```

## Key Concepts (30 seconds)

### Display Servers
- **X11**: Older, more compatible, direct access to windows
- **Wayland**: Newer, more secure, better multi-monitor support

### DPI/Scaling
- **96 DPI** = 100% (baseline)
- **144 DPI** = 150% (HiDPI)
- **192 DPI** = 200% (Retina)

Your clicks must account for scaling!

### Coordinate Systems
1. **Logical**: What apps see (DPI-adjusted)
2. **Physical**: Actual screen pixels
3. **Viewport**: Browser-specific

The examples handle this conversion for you.

## Tips for Success

✓ Always detect display server first
✓ Check DPI on HiDPI displays
✓ Test on actual hardware (VMs may behave differently)
✓ Use Playwright for browser automation (handles DPI internally)
✓ Add error handling - input can fail on different systems
✓ Keep browser window in focus for clicks to register

## One Minute Example

```python
#!/usr/bin/env python3
import os
from playwright.sync_api import sync_playwright
from dom_structure_extractor import DOMStructureExtractor

# Detect display server
display = os.environ.get('XDG_SESSION_TYPE', 'x11').upper()
print(f"Display: {display}")

# Launch browser
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://example.com")

    # Extract DOM
    extractor = DOMStructureExtractor(page)
    structure = extractor.extract()
    print(f"Found {structure.total_elements} elements")

    # Click center
    page.mouse.click(
        structure.viewport_width / 2,
        structure.viewport_height / 2
    )

    import time
    time.sleep(2)
    browser.close()
```

That's the essence! Run any example for more details.

---

**Ready to go?** Run `python3 basic_linux_click.py` now!
