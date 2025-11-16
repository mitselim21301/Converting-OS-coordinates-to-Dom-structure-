# Configuration Guide
## MCP Accurate Click Server

**Version**: 1.0.0
**Last Updated**: 2025-11-16

---

## Table of Contents

1. [Installation](#installation)
2. [Server Configuration](#server-configuration)
3. [Client Configuration](#client-configuration)
4. [Environment Variables](#environment-variables)
5. [Platform-Specific Setup](#platform-specific-setup)
6. [Advanced Configuration](#advanced-configuration)

---

## Installation

### Prerequisites

- **Python**: 3.9 or higher
- **Operating System**: Windows 10/11 (primary), Linux (experimental), macOS (experimental)
- **Memory**: 512 MB minimum, 1 GB recommended
- **Disk Space**: 500 MB for dependencies and browser

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/mcp-accurate-click-server.git
cd mcp-accurate-click-server
```

### Step 2: Create Virtual Environment

**Windows**:
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install optional vision dependencies (for computer vision validation)
pip install -r requirements-vision.txt  # Optional
```

### Step 4: Install Playwright Browsers

```bash
# Install Chromium browser for automation
playwright install chromium

# Or install all browsers
playwright install
```

### Step 5: Install MCP Server

```bash
# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Step 6: Verify Installation

```bash
# Test the server
python -m mcp_server --version

# Run tests
pytest tests/
```

---

## Server Configuration

### Configuration File

The server uses a YAML configuration file located at `config/server.yaml`.

**Default Configuration** (`config/server.yaml`):

```yaml
# MCP Server Configuration
server:
  name: "accurate-click"
  version: "1.0.0"
  transport: "stdio"  # stdio, http, or websocket
  log_level: "INFO"   # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Browser Configuration
browser:
  type: "chromium"    # chromium, firefox, webkit
  headless: false     # Run in headless mode
  timeout: 30000      # Default timeout in milliseconds
  viewport:
    width: 1920
    height: 1080
  args:
    - "--disable-blink-features=AutomationControlled"
    - "--disable-dev-shm-usage"

# Coordinate Transformation
transformation:
  enable_adaptive: true          # Adaptive correction from feedback
  sub_pixel_threshold: 0.00390625  # 1/256 pixel
  ransac_iterations: 1000
  ransac_threshold: 2.0
  refinement_iterations: 10
  cache_ttl: 2000                # DOM cache TTL in milliseconds

# Validation
validation:
  pre_click: true                # Validate before clicking
  post_click: true               # Verify after clicking
  wait_after_click: 100          # Milliseconds to wait after click
  stability_check: true          # Check element not animating
  confidence_threshold: 0.8      # Minimum confidence to proceed

# Vision (Optional)
vision:
  enabled: false                 # Enable computer vision validation
  model: "yolov8"               # yolov8, faster-rcnn, etc.
  model_path: "models/ui-elements.pt"
  confidence_threshold: 0.5
  use_ocr: false                 # Enable OCR for text detection

# Performance
performance:
  max_elements: 5000             # Maximum elements to extract
  extraction_timeout: 5000       # DOM extraction timeout (ms)
  parallel_extractions: 1        # Number of parallel extractions
  cache_enabled: true
  cache_size: 100                # Number of cached DOM snapshots

# Accessibility
accessibility:
  enable_tree: true              # Extract accessibility tree
  use_cdp: true                  # Use Chrome DevTools Protocol
  semantic_search: true          # Enable semantic element search

# Error Handling
error_handling:
  retry_count: 3                 # Number of retries on failure
  retry_delay: 1000              # Delay between retries (ms)
  fallback_strategies: true      # Try alternative click methods
  log_errors: true
  error_screenshots: true        # Capture screenshot on error

# Security
security:
  sandbox: true                  # Run browser in sandbox
  disable_javascript: false
  allow_popups: false
  max_redirects: 5
```

### Loading Custom Configuration

**Command Line**:
```bash
python -m mcp_server --config /path/to/custom-config.yaml
```

**Environment Variable**:
```bash
export MCP_CONFIG_PATH=/path/to/custom-config.yaml
python -m mcp_server
```

**Python Code**:
```python
from mcp_server import MCPServer

server = MCPServer(config_path="/path/to/custom-config.yaml")
server.start()
```

---

## Client Configuration

### Claude Desktop Configuration

Add to Claude Desktop config file:

**Location**:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**Configuration**:

```json
{
  "mcpServers": {
    "accurate-click": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "env": {
        "MCP_LOG_LEVEL": "INFO",
        "MCP_BROWSER_HEADLESS": "false"
      }
    }
  }
}
```

### Custom AI Client Configuration

**JSON-RPC over stdio**:

```python
import subprocess
import json

# Start server
process = subprocess.Popen(
    ["python", "-m", "mcp_server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Send request
request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "click_element",
        "arguments": {
            "method": "text",
            "value": "Submit"
        }
    }
}

process.stdin.write(json.dumps(request) + "\n")
process.stdin.flush()

# Read response
response = process.stdout.readline()
result = json.loads(response)
```

**HTTP Transport**:

```yaml
# config/server.yaml
server:
  transport: "http"
  host: "0.0.0.0"
  port: 8080
  cors_enabled: true
```

```python
import requests

response = requests.post(
    "http://localhost:8080/mcp",
    json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "click_element",
            "arguments": {"method": "text", "value": "Submit"}
        }
    }
)

result = response.json()
```

---

## Environment Variables

### Core Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_CONFIG_PATH` | Path to configuration file | `config/server.yaml` |
| `MCP_LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | `INFO` |
| `MCP_LOG_FILE` | Log file path (empty = console only) | `""` |
| `MCP_TRANSPORT` | Transport type (stdio/http/websocket) | `stdio` |

### Browser Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_BROWSER_TYPE` | Browser type (chromium/firefox/webkit) | `chromium` |
| `MCP_BROWSER_HEADLESS` | Run in headless mode (true/false) | `false` |
| `MCP_BROWSER_TIMEOUT` | Default timeout in milliseconds | `30000` |
| `MCP_VIEWPORT_WIDTH` | Viewport width | `1920` |
| `MCP_VIEWPORT_HEIGHT` | Viewport height | `1080` |

### Transformation Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_ENABLE_ADAPTIVE` | Enable adaptive correction | `true` |
| `MCP_RANSAC_ITERATIONS` | RANSAC iterations | `1000` |
| `MCP_CACHE_TTL` | DOM cache TTL (ms) | `2000` |
| `MCP_SUB_PIXEL_THRESHOLD` | Sub-pixel accuracy threshold | `0.00390625` |

### Validation Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_PRE_CLICK_VALIDATION` | Validate before clicking | `true` |
| `MCP_POST_CLICK_VALIDATION` | Verify after clicking | `true` |
| `MCP_WAIT_AFTER_CLICK` | Wait time after click (ms) | `100` |
| `MCP_CONFIDENCE_THRESHOLD` | Minimum confidence | `0.8` |

### Vision Settings (Optional)

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_VISION_ENABLED` | Enable vision validation | `false` |
| `MCP_VISION_MODEL` | Vision model type | `yolov8` |
| `MCP_VISION_MODEL_PATH` | Path to model weights | `models/ui-elements.pt` |
| `MCP_OCR_ENABLED` | Enable OCR | `false` |

### Performance Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_MAX_ELEMENTS` | Maximum elements to extract | `5000` |
| `MCP_EXTRACTION_TIMEOUT` | DOM extraction timeout (ms) | `5000` |
| `MCP_CACHE_ENABLED` | Enable DOM caching | `true` |
| `MCP_CACHE_SIZE` | Cache size (snapshots) | `100` |

---

## Platform-Specific Setup

### Windows Setup

#### 1. Install Python

Download from [python.org](https://www.python.org/downloads/) (3.9+)

Ensure "Add Python to PATH" is checked during installation.

#### 2. Install Visual C++ Build Tools

Required for some Python packages:

Download from [Microsoft](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

Or install via chocolatey:
```powershell
choco install visualstudio2019buildtools
```

#### 3. DPI Awareness

The server automatically registers as DPI-aware. To verify:

**Registry Check**:
```powershell
reg query "HKEY_CURRENT_USER\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers"
```

**Manual Registration** (if needed):
```python
# Included in server startup
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
```

#### 4. Multi-Monitor Setup

For multi-monitor configurations, ensure monitors are properly configured:

```powershell
# Display current monitor configuration
powershell -Command "Get-WmiObject -Class Win32_DesktopMonitor"
```

The server automatically detects and handles multiple monitors with different DPI settings.

#### 5. Permissions

No administrator privileges required for normal operation.

For system-wide automation, run as administrator:
```powershell
# Right-click CMD/PowerShell -> "Run as administrator"
python -m mcp_server
```

---

### Linux Setup

#### 1. Install Python

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install python3.9 python3.9-venv python3-pip
```

**Fedora**:
```bash
sudo dnf install python3.9 python3-pip
```

#### 2. Install System Dependencies

**For Playwright**:
```bash
# Ubuntu/Debian
sudo apt install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2

# Fedora
sudo dnf install -y \
    nss \
    nspr \
    atk \
    at-spi2-atk \
    cups-libs \
    libdrm \
    dbus-libs \
    libxkbcommon \
    libXcomposite \
    libXdamage \
    libXfixes \
    libXrandr \
    mesa-libgbm \
    pango \
    cairo \
    alsa-lib
```

#### 3. X11 vs Wayland

**X11** (Recommended):
```bash
# Check if running X11
echo $XDG_SESSION_TYPE
# Output: x11

# Install xdotool (for OS-level automation)
sudo apt install xdotool  # Ubuntu/Debian
sudo dnf install xdotool  # Fedora
```

**Wayland** (Limited Support):
```bash
# Install ydotool (alternative to xdotool)
sudo apt install ydotool  # Ubuntu/Debian

# Start ydotool daemon
sudo systemctl enable --now ydotool

# Add user to input group
sudo usermod -a -G input $USER
```

#### 4. Display Configuration

Set display for headless operation:
```bash
export DISPLAY=:0

# Or use Xvfb for virtual display
sudo apt install xvfb
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
```

---

### macOS Setup

#### 1. Install Python

**Using Homebrew** (recommended):
```bash
brew install python@3.9
```

**Or download from** [python.org](https://www.python.org/downloads/)

#### 2. Install Xcode Command Line Tools

```bash
xcode-select --install
```

#### 3. Accessibility Permissions

Grant Terminal (or your app) accessibility permissions:

1. System Preferences → Security & Privacy → Privacy
2. Select "Accessibility" from left panel
3. Click lock icon and authenticate
4. Add Terminal.app (or your application)
5. Check the box to enable

#### 4. Screen Recording Permission

For screenshot capabilities:

1. System Preferences → Security & Privacy → Privacy
2. Select "Screen Recording"
3. Add Terminal.app
4. Restart Terminal

#### 5. Retina Display Support

The server automatically handles Retina displays (devicePixelRatio = 2).

Verify:
```python
# This is handled automatically
device_pixel_ratio = page.evaluate("window.devicePixelRatio")
print(f"DPR: {device_pixel_ratio}")  # Should be 2 on Retina
```

---

## Advanced Configuration

### Custom Calibration

For improved accuracy, calibrate the transformer with known points:

**Interactive Calibration**:

```bash
python -m mcp_server.tools.calibrate
```

This launches an interactive calibration tool:
1. Click on-screen markers
2. System records OS and DOM coordinates
3. Computes transformation matrix
4. Saves calibration to `config/calibration.npz`

**Manual Calibration**:

```python
from mcp_server.core import OSToDOM_Transformer
import numpy as np

# Collect calibration points
# (Click known positions and record coordinates)
os_points = np.array([[100, 100], [800, 100], [100, 500], [800, 500]])
dom_points = np.array([[150, 180], [1100, 180], [150, 780], [1100, 780]])

# Calibrate
transformer = OSToDOM_Transformer()
report = transformer.calibrate(os_points, dom_points, use_ransac=True)

# Save
transformer.save_calibration('config/calibration.npz')

print(f"Calibration accuracy: {report['validation']['achieved_accuracy']:.6f}px")
```

**Load Saved Calibration**:

```yaml
# config/server.yaml
transformation:
  calibration_file: "config/calibration.npz"
  auto_load: true
```

### Vision Model Configuration

**Download Pre-trained Models**:

```bash
# YOLOv8 UI Detection Model
wget https://example.com/models/ui-elements-yolov8.pt -O models/ui-elements.pt

# OCR Model (optional)
wget https://example.com/models/ocr-model.pt -O models/ocr.pt
```

**Train Custom Model**:

```bash
# Prepare dataset
python -m mcp_server.vision.prepare_dataset --screenshots ./screenshots --output ./dataset

# Train YOLOv8
yolo train data=dataset/data.yaml model=yolov8n.pt epochs=100 imgsz=1920

# Use trained model
python -m mcp_server --vision-model runs/detect/train/weights/best.pt
```

### Logging Configuration

**File-based Logging**:

```yaml
# config/server.yaml
logging:
  file: "logs/mcp-server.log"
  level: "DEBUG"
  rotation: "1 day"
  retention: "7 days"
  format: "{time} | {level} | {module}:{function}:{line} | {message}"
```

**Structured Logging (JSON)**:

```yaml
logging:
  format: "json"
  file: "logs/mcp-server.json"
```

**Log to External Service**:

```yaml
logging:
  handlers:
    - type: "syslog"
      host: "log-server.example.com"
      port: 514
    - type: "http"
      url: "https://logs.example.com/ingest"
      headers:
        Authorization: "Bearer YOUR_TOKEN"
```

### Performance Tuning

**High-Performance Configuration**:

```yaml
# config/server.yaml
performance:
  # Increase parallelism
  parallel_extractions: 4
  worker_threads: 8

  # Optimize caching
  cache_enabled: true
  cache_size: 200
  cache_ttl: 5000

  # Reduce extraction overhead
  viewport_only: true
  interactive_only: true
  max_depth: 5
  max_elements: 1000

  # Browser optimizations
  browser_args:
    - "--disable-extensions"
    - "--disable-gpu"
    - "--disable-dev-shm-usage"
    - "--no-sandbox"
    - "--disable-setuid-sandbox"
```

**Low-Memory Configuration**:

```yaml
performance:
  cache_enabled: false
  max_elements: 500
  parallel_extractions: 1
  browser_args:
    - "--disable-dev-shm-usage"
    - "--single-process"
```

### Network Configuration

**HTTP Server Mode**:

```yaml
# config/server.yaml
server:
  transport: "http"
  host: "0.0.0.0"
  port: 8080
  cors_enabled: true
  cors_origins:
    - "http://localhost:3000"
    - "https://app.example.com"
  auth:
    type: "bearer"
    token: "YOUR_SECRET_TOKEN"
  ssl:
    enabled: true
    cert: "/path/to/cert.pem"
    key: "/path/to/key.pem"
```

**WebSocket Mode**:

```yaml
server:
  transport: "websocket"
  host: "0.0.0.0"
  port: 8080
  ping_interval: 30000
  ping_timeout: 10000
  max_connections: 10
```

---

**Next**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.
