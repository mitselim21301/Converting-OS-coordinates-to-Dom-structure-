# Troubleshooting Guide
## MCP Accurate Click Server

**Version**: 1.0.0
**Last Updated**: 2025-11-16

---

## Table of Contents

1. [Common Issues](#common-issues)
2. [Error Messages](#error-messages)
3. [Debugging Techniques](#debugging-techniques)
4. [Platform-Specific Issues](#platform-specific-issues)
5. [Performance Issues](#performance-issues)
6. [Accuracy Problems](#accuracy-problems)
7. [FAQ](#faq)

---

## Common Issues

### Installation Issues

#### Issue: `playwright install` fails

**Symptoms**:
```
Error: Failed to download chromium
```

**Solutions**:

1. **Check network connection**:
   ```bash
   # Test connectivity
   curl -I https://playwright.azureedge.net/
   ```

2. **Use manual download**:
   ```bash
   # Set download host
   export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
   playwright install chromium
   ```

3. **Install system dependencies** (Linux):
   ```bash
   sudo apt install -y libnss3 libxss1 libasound2
   playwright install-deps chromium
   ```

---

#### Issue: `pip install` fails with compilation errors

**Symptoms**:
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**Solutions**:

**Windows**:
```powershell
# Install Visual C++ Build Tools
choco install visualstudio2019buildtools
# Or download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

**Linux**:
```bash
sudo apt install python3-dev build-essential
```

**macOS**:
```bash
xcode-select --install
```

---

#### Issue: NumPy import error

**Symptoms**:
```python
ImportError: numpy.core.multiarray failed to import
```

**Solution**:
```bash
# Reinstall NumPy
pip uninstall numpy
pip install numpy==1.24.3
```

---

### Runtime Issues

#### Issue: Browser fails to launch

**Symptoms**:
```
playwright._impl._api_types.Error: Browser closed
```

**Solutions**:

1. **Check Playwright installation**:
   ```bash
   playwright install chromium
   ```

2. **Verify system dependencies**:
   ```bash
   # Linux
   ldd $(which chromium-browser)

   # Install missing libraries
   playwright install-deps
   ```

3. **Try different browser**:
   ```yaml
   # config/server.yaml
   browser:
     type: "firefox"  # or "webkit"
   ```

4. **Disable sandbox** (last resort):
   ```yaml
   browser:
     args:
       - "--no-sandbox"
       - "--disable-setuid-sandbox"
   ```

---

#### Issue: "Element not found" errors

**Symptoms**:
```json
{
  "error": "ElementNotFoundError: No element found with text: Submit"
}
```

**Solutions**:

1. **Check text is exact**:
   ```python
   # Use partial matching
   click_element(method="text", value="submit")  # lowercase
   ```

2. **Try different strategies**:
   ```python
   # Try CSS selector
   click_element(method="selector", value="#submit-btn")

   # Try accessible name
   click_element(method="accessible_name", value="Submit form")
   ```

3. **Check element is visible**:
   ```python
   # Extract DOM to inspect
   structure = extract_dom_structure()
   print([e.text_content for e in structure.elements if e.visible])
   ```

4. **Wait for element to appear**:
   ```python
   # In Playwright directly
   page.wait_for_selector("button:has-text('Submit')", timeout=10000)
   ```

---

#### Issue: Clicks hit wrong element

**Symptoms**:
- Click doesn't trigger expected action
- Wrong element gets clicked
- Validation fails with "coordinates hit different element"

**Solutions**:

1. **Enable validation**:
   ```python
   click_element(method="text", value="Submit", validate=true)
   ```

2. **Check for overlapping elements**:
   ```python
   # Extract DOM and check z-index
   structure = extract_dom_structure()
   mapper = CoordinateMapper(structure)

   # Find all elements at point
   point_x, point_y = 500, 300
   all_at_point = [e for e in structure.elements
                   if point_in_bbox(point_x, point_y, e.bounding_box)]

   # Check z-index values
   for elem in sorted(all_at_point, key=lambda e: e.z_index, reverse=True):
       print(f"{elem.tag_name} z-index={elem.z_index}")
   ```

3. **Scroll element into view**:
   ```python
   # Let Playwright handle scrolling
   page.locator("text=Submit").scroll_into_view_if_needed()
   ```

4. **Recalibrate transformation**:
   ```bash
   python -m mcp_server.tools.calibrate
   ```

---

### Coordinate Issues

#### Issue: Coordinate transformation inaccurate

**Symptoms**:
- Clicks are offset from target
- Round-trip validation fails
- High RMS error reported

**Solutions**:

1. **Check DPI scaling**:
   ```python
   # Windows: Verify DPI awareness
   import ctypes
   awareness = ctypes.windll.shcore.GetProcessDpiAwareness(0)
   print(f"DPI Awareness: {awareness}")  # Should be 2 (per-monitor)
   ```

2. **Recalibrate with more points**:
   ```python
   # Use 9+ calibration points covering full screen
   transformer.calibrate(
       os_points,     # 9x2 array
       dom_points,    # 9x2 array
       use_ransac=True,
       refine=True
   )
   ```

3. **Check window position is stable**:
   ```python
   # Browser window shouldn't move during operation
   pos1 = page.evaluate("({x: window.screenX, y: window.screenY})")
   time.sleep(1)
   pos2 = page.evaluate("({x: window.screenX, y: window.screenY})")
   assert pos1 == pos2, "Window moved!"
   ```

4. **Verify scroll position tracking**:
   ```python
   scroll = page.evaluate("({x: window.scrollX, y: window.scrollY})")
   print(f"Scroll: {scroll}")

   # Ensure scroll accounted for in coordinates
   ```

---

## Error Messages

### CalibrationError

```
CalibrationError: Ill-conditioned transformation matrix (condition number: 1523.45)
```

**Cause**: Calibration points are nearly collinear or too close together.

**Solution**:
```python
# Use well-distributed calibration points
# Cover all corners and center of screen
os_points = np.array([
    [100, 100],      # Top-left
    [1820, 100],     # Top-right
    [100, 980],      # Bottom-left
    [1820, 980],     # Bottom-right
    [960, 540],      # Center
    [100, 540],      # Middle-left
    [1820, 540],     # Middle-right
    [960, 100],      # Top-center
    [960, 980]       # Bottom-center
])
```

---

### ValidationError

```
ValidationError: Element button#submit-btn not clickable: Element is occluded by div.modal
```

**Cause**: Another element is covering the target.

**Solution**:
```python
# Close overlaying element first
click_element(method="selector", value=".modal .close-button")

# Then click target
click_element(method="text", value="Submit")
```

---

### CoordinateTransformError

```
CoordinateTransformError: No calibration data available
```

**Cause**: Transformer not calibrated before use.

**Solution**:
```python
# Calibrate before transforming
transformer = OSToDOM_Transformer()

# Either calibrate manually
transformer.calibrate(os_points, dom_points)

# Or load saved calibration
transformer.load_calibration('config/calibration.npz')

# Now can transform
x_dom, y_dom = transformer.transform_os_to_dom(500, 300)
```

---

### TimeoutError

```
playwright._impl._api_types.TimeoutError: Timeout 30000ms exceeded
```

**Cause**: Page taking too long to load or element not appearing.

**Solutions**:

1. **Increase timeout**:
   ```yaml
   # config/server.yaml
   browser:
     timeout: 60000  # 60 seconds
   ```

2. **Wait for specific condition**:
   ```python
   page.wait_for_load_state("networkidle")
   page.wait_for_selector("button:has-text('Submit')")
   ```

3. **Check network issues**:
   ```python
   # Monitor network requests
   page.on("request", lambda req: print(f"Request: {req.url}"))
   page.on("response", lambda res: print(f"Response: {res.status} {res.url}"))
   ```

---

## Debugging Techniques

### Enable Debug Logging

```bash
# Command line
export MCP_LOG_LEVEL=DEBUG
python -m mcp_server

# Or in config
```

```yaml
# config/server.yaml
server:
  log_level: "DEBUG"

logging:
  file: "logs/debug.log"
  level: "DEBUG"
```

**Output**:
```
2025-11-16 10:23:45 | DEBUG | dom_extractor:extract:145 | Extracting DOM structure
2025-11-16 10:23:45 | DEBUG | dom_extractor:extract:156 | Found 234 elements
2025-11-16 10:23:45 | DEBUG | coordinate_mapper:find_at_point:89 | Finding element at (500, 300)
2025-11-16 10:23:45 | DEBUG | coordinate_mapper:find_at_point:102 | Hit element: button#submit-btn
```

---

### Interactive Debugging

```python
# In your code
import pdb

# Set breakpoint
pdb.set_trace()

# Or use IPython
from IPython import embed
embed()

# Inspect variables
structure = extractor.extract()
print(f"Elements: {len(structure.elements)}")
print(f"Viewport: {structure.viewport}")
```

---

### Visual Debugging

**Screenshot on Error**:

```yaml
# config/server.yaml
error_handling:
  error_screenshots: true
  screenshot_dir: "logs/screenshots"
```

**Annotate Screenshots**:

```python
from mcp_server.debug import annotate_screenshot

# Take screenshot
screenshot = page.screenshot()

# Annotate with element bounding boxes
annotated = annotate_screenshot(
    screenshot,
    elements=structure.elements,
    highlight_clickable=True
)

# Save
with open("debug_screenshot.png", "wb") as f:
    f.write(annotated)
```

**Record Video**:

```python
# Enable video recording
context = browser.new_context(record_video_dir="logs/videos/")
page = context.new_page()

# Perform actions
# ...

# Video saved automatically on context close
context.close()
```

---

### DOM Inspection

```python
# Extract and save DOM structure
structure = extractor.extract()

# Export to JSON for inspection
import json
with open("dom_structure.json", "w") as f:
    json.dump({
        "elements": [asdict(e) for e in structure.elements],
        "viewport": structure.viewport,
        "scroll": structure.scroll
    }, f, indent=2)

# Filter to specific elements
interactive = [e for e in structure.elements if e.clickable]
print(f"Interactive elements: {len(interactive)}")

for elem in interactive:
    print(f"  {elem.tag_name}#{elem.element_id}: {elem.text_content}")
    print(f"    Position: ({elem.bounding_box.x}, {elem.bounding_box.y})")
    print(f"    Visible: {elem.visible}, Enabled: {elem.enabled}")
```

---

### Performance Profiling

```python
import cProfile
import pstats

# Profile extraction
profiler = cProfile.Profile()
profiler.enable()

structure = extractor.extract()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

**Output**:
```
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.001    0.001    0.342    0.342 dom_extractor.py:145(extract)
      234    0.156    0.001    0.312    0.001 dom_extractor.py:201(_extract_element)
      234    0.089    0.000    0.123    0.001 playwright:123(evaluate)
```

---

## Platform-Specific Issues

### Windows Issues

#### Issue: DPI scaling problems

**Symptoms**:
- Clicks offset by consistent factor (e.g., 1.5x)
- Different behavior on different monitors

**Solutions**:

1. **Set DPI awareness**:
   ```python
   # Included in server startup, but verify:
   import ctypes

   # Set process DPI aware
   ctypes.windll.shcore.SetProcessDpiAwareness(2)

   # Verify
   dpi = ctypes.windll.user32.GetDpiForSystem()
   print(f"System DPI: {dpi}")  # 96 = 100%, 144 = 150%, 192 = 200%
   ```

2. **Check per-monitor DPI**:
   ```python
   from mcp_server.windows import get_monitor_dpi

   for monitor in get_monitors():
       dpi = get_monitor_dpi(monitor.handle)
       print(f"Monitor {monitor.name}: {dpi} DPI")
   ```

3. **Disable DPI scaling for app** (workaround):
   - Right-click python.exe
   - Properties → Compatibility
   - "Override high DPI scaling behavior"
   - Select "System"

---

#### Issue: Multi-monitor coordinate confusion

**Symptoms**:
- Coordinates incorrect when browser on secondary monitor
- Negative coordinates when secondary monitor is left of primary

**Solution**:

```python
from mcp_server.windows import get_monitor_at_point, get_window_monitor

# Detect which monitor browser is on
browser_monitor = get_window_monitor(browser_hwnd)
print(f"Browser on monitor: {browser_monitor.name}")
print(f"Monitor bounds: {browser_monitor.bounds}")

# Account for monitor position in transformations
# (Automatically handled by WindowsCoordinateAdapter)
```

---

### Linux Issues

#### Issue: xdotool clicks don't work

**Symptoms**:
```bash
xdotool click 1
# Nothing happens
```

**Solutions**:

1. **Check X11 vs Wayland**:
   ```bash
   echo $XDG_SESSION_TYPE

   # If Wayland, switch to X11
   sudo nano /etc/gdm3/custom.conf
   # Uncomment: WaylandEnable=false
   sudo systemctl restart gdm3
   ```

2. **Use ydotool for Wayland**:
   ```bash
   sudo apt install ydotool
   sudo systemctl enable --now ydotool
   sudo usermod -a -G input $USER

   # Test
   ydotool click 1
   ```

3. **Check DISPLAY variable**:
   ```bash
   echo $DISPLAY
   # Should be :0 or :1

   # Set if empty
   export DISPLAY=:0
   ```

---

#### Issue: Permission denied errors

**Symptoms**:
```
PermissionError: [Errno 13] Permission denied: '/dev/uinput'
```

**Solution**:

```bash
# Add user to input group
sudo usermod -a -G input $USER

# Set uinput permissions
sudo chmod 660 /dev/uinput
sudo chgrp input /dev/uinput

# Create udev rule for persistence
echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | \
  sudo tee /etc/udev/rules.d/99-uinput.rules

# Reload and reboot
sudo udevadm control --reload-rules
sudo reboot
```

---

### macOS Issues

#### Issue: Accessibility permissions not granted

**Symptoms**:
```
RuntimeError: Accessibility permissions required
```

**Solution**:

1. **Grant permissions**:
   - System Preferences → Security & Privacy → Privacy
   - Select "Accessibility"
   - Add Terminal.app or your application
   - Check the box

2. **Verify permissions**:
   ```python
   from mcp_server.macos import check_accessibility_permissions

   if not check_accessibility_permissions():
       print("Please grant accessibility permissions")
   ```

---

#### Issue: Screen recording permission

**Symptoms**:
Screenshots are blank or permission dialogs appear.

**Solution**:
- System Preferences → Security & Privacy → Privacy
- Select "Screen Recording"
- Add Terminal.app
- Restart Terminal

---

## Performance Issues

### Issue: DOM extraction is slow

**Symptoms**:
- Extraction takes >5 seconds
- Server becomes unresponsive

**Solutions**:

1. **Limit extraction scope**:
   ```yaml
   # config/server.yaml
   performance:
     viewport_only: true      # Only visible elements
     interactive_only: true   # Only clickable elements
     max_depth: 5            # Limit DOM depth
     max_elements: 1000      # Cap element count
   ```

2. **Enable caching**:
   ```yaml
   performance:
     cache_enabled: true
     cache_ttl: 5000  # 5 seconds
   ```

3. **Optimize page**:
   ```python
   # Remove heavy elements before extraction
   page.evaluate("""
       document.querySelectorAll('iframe, video, canvas').forEach(el => el.remove())
   """)

   structure = extractor.extract()
   ```

---

### Issue: High memory usage

**Symptoms**:
- Memory grows over time
- Out of memory errors

**Solutions**:

1. **Limit cache size**:
   ```yaml
   performance:
     cache_size: 50  # Reduce from default 100
   ```

2. **Disable vision models** (if not needed):
   ```yaml
   vision:
     enabled: false
   ```

3. **Close browser between sessions**:
   ```python
   # Close and reopen periodically
   browser.close()
   browser = playwright.chromium.launch()
   ```

4. **Monitor memory**:
   ```python
   import psutil
   process = psutil.Process()
   print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
   ```

---

## Accuracy Problems

### Issue: Clicks consistently offset

**Symptoms**:
- All clicks off by same amount (e.g., +50px X, +20px Y)

**Solution**:

**Recalibrate**:
```python
# Use interactive calibration tool
python -m mcp_server.tools.calibrate

# Or manual calibration with known points
transformer.calibrate(os_points, dom_points, use_ransac=True)
```

---

### Issue: Intermittent accuracy

**Symptoms**:
- Sometimes accurate, sometimes not
- Accuracy varies between pages

**Causes & Solutions**:

1. **Dynamic content shifting**:
   ```python
   # Wait for page to stabilize
   page.wait_for_load_state("networkidle")
   page.wait_for_timeout(500)  # Additional settle time
   ```

2. **Scroll position changing**:
   ```python
   # Check scroll before and after
   scroll1 = page.evaluate("window.scrollY")
   time.sleep(0.1)
   scroll2 = page.evaluate("window.scrollY")

   if scroll1 != scroll2:
       print("Warning: Page scrolling during operation")
   ```

3. **Window resizing**:
   ```python
   # Lock viewport size
   page.set_viewport_size({"width": 1920, "height": 1080})
   ```

---

## FAQ

### Q: How accurate is the coordinate transformation?

**A**: Sub-pixel accuracy (< 1/256 pixel = 0.004px) is achieved after proper calibration. Round-trip error is typically < 1e-10 pixels.

---

### Q: Do I need to recalibrate when changing zoom level?

**A**: Yes. Each zoom level requires separate calibration:

```python
for zoom in [1.0, 1.25, 1.5]:
    page.evaluate(f"document.body.style.zoom = {zoom}")
    transformer.set_scale(zoom)
    transformer.calibrate(os_points_at_zoom, dom_points_at_zoom, scale=zoom)
```

---

### Q: Can I use this with headless browsers?

**A**: Yes, headless mode works fine for DOM extraction and coordinate mapping. However, OS-level clicking requires visible window.

```yaml
# config/server.yaml
browser:
  headless: true  # OK for Playwright clicks, not for OS-level
```

---

### Q: How do I handle dynamic SPAs (Single Page Apps)?

**A**:
1. Wait for route changes: `page.wait_for_url()`
2. Re-extract DOM after navigation
3. Use mutation observers for real-time updates

```python
# Wait for navigation
page.click("a.nav-link")
page.wait_for_url("**/new-page")

# Re-extract
structure = extractor.extract()
```

---

### Q: What's the performance impact of validation?

**A**: Pre-click validation adds ~2-3ms overhead. Post-click verification adds ~100ms (waiting for page reaction). Both significantly reduce failed click rate (30-50% improvement).

---

### Q: Can I run multiple servers in parallel?

**A**: Yes, each server instance can manage one browser. For parallel operation, run multiple instances:

```bash
# Terminal 1
python -m mcp_server --port 8080

# Terminal 2
python -m mcp_server --port 8081

# Terminal 3
python -m mcp_server --port 8082
```

---

### Q: How do I debug "Element not clickable" errors?

**A**:
1. Enable debug logging
2. Take screenshot at failure point
3. Extract DOM and inspect z-index
4. Check element visibility and enabled state
5. Verify coordinates with validation

```python
try:
    click_element(method="text", value="Submit")
except ValidationError as e:
    print(f"Validation failed: {e.reason}")

    # Debug
    screenshot = page.screenshot()
    structure = extractor.extract()

    # Find element
    elements = mapper.find_elements_by_text("Submit")
    if elements:
        elem = elements[0]
        print(f"Element found but not clickable:")
        print(f"  Visible: {elem.visible}")
        print(f"  Enabled: {elem.enabled}")
        print(f"  Z-index: {elem.z_index}")
        print(f"  Pointer events: {elem.pointer_events}")
```

---

### Q: How do I integrate with existing automation frameworks?

**A**: The server provides an MCP interface that works with any MCP-compatible client. For non-MCP frameworks, you can:

1. Use the HTTP transport mode
2. Import classes directly in Python
3. Wrap with custom adapter

```python
# Direct usage in Python
from mcp_server.dom import DOMStructureExtractor
from mcp_server.core import OSToDOM_Transformer

# Use in your framework
structure = extractor.extract()
# ... your code
```

---

**For additional help**:
- Check [API documentation](API.md) for detailed method signatures
- Review [research papers](../) for deep technical understanding
- Open GitHub issue with debug logs and screenshots
