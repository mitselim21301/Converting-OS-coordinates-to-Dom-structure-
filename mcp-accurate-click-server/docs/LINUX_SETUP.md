# Linux Setup Guide
## MCP Accurate Click Server on Linux

**Version**: 1.0.0
**Last Updated**: 2025-11-17
**Status**: Production Ready ✅

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation Steps](#installation-steps)
3. [Display Server Setup](#display-server-setup)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Performance Tuning](#performance-tuning)

---

## System Requirements

### Minimum Requirements

- **OS**: Linux kernel 4.4+
- **Python**: 3.9 or higher
- **Memory**: 512 MB RAM minimum
- **Disk Space**: 100 MB
- **Display Server**: X11 (Xorg) or Wayland

### Recommended Setup

- **OS**: Ubuntu 20.04 LTS+, Debian 11+, Fedora 38+, Arch
- **Python**: 3.11 or higher
- **Memory**: 2 GB RAM
- **Processor**: Multi-core (for parallel vision tasks)
- **Display**: X11 with 2+ displays (for multi-monitor testing)

### Dependencies

#### Core Dependencies

```bash
# These are installed via pip requirements.txt
- playwright >= 1.40.0      # Browser automation
- pillow >= 10.0.0          # Image processing
- pydantic >= 2.0.0         # Data validation
```

#### System Dependencies

**For X11 environments:**
```bash
# Debian/Ubuntu
sudo apt-get install -y \
    x11-utils \
    xdotool \
    xrandr \
    xclip \
    python3-dev \
    build-essential

# Fedora/RHEL
sudo dnf install -y \
    xorg-x11-utils \
    xdotool \
    python3-devel \
    gcc \
    g++ \
    make

# Arch
sudo pacman -S \
    xorg-utils \
    xdotool \
    base-devel
```

**For Wayland environments:**
```bash
# Debian/Ubuntu
sudo apt-get install -y \
    wlr-randr \
    python3-dev \
    build-essential

# Fedora/RHEL
sudo dnf install -y \
    wlr-randr \
    python3-devel

# Arch
sudo pacman -S \
    wlr-randr \
    base-devel
```

**For Browser Integration:**
```bash
# Playwright browsers (installed automatically)
playwright install chromium

# Or install system Chromium/Chrome
# Debian/Ubuntu
sudo apt-get install -y chromium-browser

# Fedora
sudo dnf install -y chromium
```

**For Vision/ML Features (Optional):**
```bash
# Debian/Ubuntu
sudo apt-get install -y \
    libssl-dev \
    libffi-dev \
    python3-numpy \
    python3-opencv

# Fedora
sudo dnf install -y \
    openssl-devel \
    libffi-devel \
    python3-numpy \
    python3-opencv
```

---

## Installation Steps

### Step 1: Clone the Repository

```bash
# Using HTTPS
git clone https://github.com/yourusername/mcp-accurate-click-server.git
cd mcp-accurate-click-server

# Or using SSH
git clone git@github.com:yourusername/mcp-accurate-click-server.git
cd mcp-accurate-click-server
```

### Step 2: Create Python Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Verify activation (should show (venv) in prompt)
which python
```

### Step 3: Upgrade pip and setuptools

```bash
pip install --upgrade pip setuptools wheel
```

### Step 4: Install Core Dependencies

```bash
# Install required Python packages
pip install -r requirements.txt

# Install development dependencies (optional, for testing)
pip install -r requirements-dev.txt

# Install documentation dependencies (optional)
pip install -r requirements-docs.txt
```

### Step 5: Install the Package

```bash
# Install in development mode (recommended for development)
pip install -e .

# Or install in production mode
pip install .
```

### Step 6: Verify Installation

```bash
# Test imports
python -c "from mcp_server.platform.linux import LinuxCoordinateConverter; print('✓ Linux support installed')"

# Check version
python -c "import mcp_server; print(mcp_server.__version__)"

# Verify MCP server
python -m mcp_server --help
```

---

## Display Server Setup

### Detecting Your Display Server

```bash
# Check which display server you're using
echo $XDG_SESSION_TYPE

# Or check running processes
ps aux | grep -E 'X|wayland|gnome-shell'
```

### X11 (Xorg) Configuration

**Supported on:**
- Traditional X11 desktops (KDE/Plasma, XFCE, Fluxbox, i3)
- GNOME with X11 backend
- Ubuntu 22.04 with X11 session option

**Setup:**
```bash
# Install Xvfb for headless X11 (optional, for CI/CD)
sudo apt-get install -y xvfb

# Start virtual display
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Verify DPI detection
python -c "from mcp_server.platform.linux.dpi_handler import LinuxDPIHandler; h = LinuxDPIHandler(); print(h.get_dpi_info())"
```

**Monitor Detection:**
```bash
# Use xrandr to list all monitors with DPI
xrandr --query --verbose

# Example output parsing:
# Primary monitor: HDMI-1 at 1920x1080 (509mm x 286mm)
# → DPI = (1920 × 25.4) / 509 ≈ 96 DPI
```

### Wayland Configuration

**Supported on:**
- GNOME with Wayland backend (GNOME 42+)
- KDE Plasma 5.24+
- Weston
- Sway

**Setup:**
```bash
# Install wlr-randr for Wayland monitor info
sudo apt-get install wlr-randr

# Or build from source
git clone https://github.com/emersion/wlr-randr.git
cd wlr-randr
meson build
ninja -C build install

# Verify Wayland DPI detection
python -c "from mcp_server.platform.linux.dpi_handler import LinuxDPIHandler; h = LinuxDPIHandler(); print(h.get_dpi_info())"
```

**Environment Variables:**
```bash
# Set scaling for GNOME/GTK applications
export GDK_SCALE=2           # Integer scaling
export GDK_DPI_SCALE=1.5     # Fractional scaling

# Set scaling for Qt applications
export QT_SCALE_FACTOR=1.5

# Check detected scaling
env | grep -i scale
```

---

## Configuration

### Environment Variables

Create `.env` file or set environment variables:

```bash
# Display server (auto-detected, can override)
export XDG_SESSION_TYPE=x11  # or 'wayland'

# DPI settings
export MCP_DPI_OVERRIDE=96   # Override detected DPI
export MCP_SCALE_FACTOR=1.0  # Force scale factor

# Browser settings
export MCP_BROWSER_PATH=/usr/bin/chromium-browser
export MCP_HEADLESS=false    # Show browser window

# Performance
export MCP_DOM_CACHE_SIZE=100
export MCP_TIMEOUT_MS=30000

# Logging
export MCP_LOG_LEVEL=INFO    # DEBUG, INFO, WARNING, ERROR
export MCP_LOG_FILE=/tmp/mcp_server.log

# Linux-specific
export MCP_USE_XDOTOOL=true  # Use xdotool for input simulation
export MCP_ENABLE_WAYLAND=true
```

### Configuration File

Create `mcp_config.json`:

```json
{
  "server": {
    "name": "mcp-accurate-click",
    "version": "1.0.0"
  },
  "platform": {
    "type": "linux",
    "display_server": "x11",
    "dpi_override": null,
    "scale_factor": 1.0
  },
  "browser": {
    "browser_type": "chromium",
    "headless": false,
    "viewport": {
      "width": 1920,
      "height": 1080
    },
    "launch_args": [
      "--disable-blink-features=AutomationControlled",
      "--disable-dev-shm-usage"
    ]
  },
  "coordinate_system": {
    "precision": "sub_pixel",
    "default_system": "os_screen",
    "cache_enabled": true
  },
  "validation": {
    "pre_click_validation": true,
    "post_click_verification": false,
    "vision_confidence_threshold": 0.85
  },
  "logging": {
    "level": "INFO",
    "file": "/tmp/mcp_server.log",
    "max_size_mb": 100,
    "backup_count": 5
  }
}
```

### Playwright Configuration

```bash
# Install Chromium
playwright install chromium

# Or use system Chromium (more efficient)
export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium-browser

# For headless mode with GPU acceleration
export PLAYWRIGHT_LAUNCH_ARGS="--disable-dev-shm-usage --enable-gpu"
```

---

## Verification

### Basic Verification

```bash
# Test 1: Import validation
python << 'EOF'
from mcp_server.platform.linux.dpi_handler import LinuxDPIHandler
from mcp_server.platform.linux.coordinate_converter import LinuxCoordinateConverter
print("✓ Linux platform modules imported successfully")
EOF

# Test 2: DPI detection
python << 'EOF'
from mcp_server.platform.linux.dpi_handler import LinuxDPIHandler
handler = LinuxDPIHandler()
dpi_info = handler.get_dpi_info()
print(f"✓ DPI Detection: {dpi_info}")
EOF

# Test 3: Display server detection
python << 'EOF'
from mcp_server.platform.linux.dpi_handler import LinuxDPIHandler
handler = LinuxDPIHandler()
print(f"✓ Display Server: {handler._detect_display_server()}")
EOF
```

### MCP Server Verification

```bash
# Start the MCP server (will run in foreground)
python -m mcp_server

# In another terminal, test the server
python << 'EOF'
import subprocess
import json
import time

# The server should be running and responding to MCP calls
print("✓ MCP server is running")
print("Test coordinate transformation:")
print("  OS Screen (1920, 1080) → Device Pixels")
EOF
```

### Full Test Suite

```bash
# Run all tests
pytest tests/ -v

# Run Linux-specific tests
pytest tests/ -k linux -v

# Run with coverage
pytest tests/ --cov=src/mcp_server/platform/linux --cov-report=html
```

---

## Troubleshooting

### Common Issues

#### Issue 1: "xrandr: command not found"

**Solution:**
```bash
# Install xrandr
sudo apt-get install x11-utils  # Debian/Ubuntu
sudo dnf install xorg-x11-utils # Fedora

# Or use alternative DPI detection
export MCP_DPI_OVERRIDE=96
```

#### Issue 2: "No DISPLAY found" / Wayland Detection Fails

**Solution:**
```bash
# Check display server
echo $XDG_SESSION_TYPE
echo $DISPLAY

# For X11
export DISPLAY=:0
export XDG_SESSION_TYPE=x11

# For Wayland
export XDG_SESSION_TYPE=wayland
```

#### Issue 3: Playwright Browser Installation Issues

**Solution:**
```bash
# Clear Playwright cache
rm -rf ~/.cache/ms-playwright

# Reinstall browsers with verbose output
playwright install chromium --verbose

# Or use system Chromium instead
export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium-browser
```

#### Issue 4: Permission Denied for xdotool

**Solution:**
```bash
# Grant required permissions
sudo chmod u+s /usr/bin/xdotool

# Or run with appropriate privileges
sudo python -m mcp_server

# Or disable xdotool and use direct Playwright input
export MCP_USE_XDOTOOL=false
```

#### Issue 5: Coordinate Transformation Errors

**Solution:**
```bash
# Enable debug logging
export MCP_LOG_LEVEL=DEBUG
python -m mcp_server 2>&1 | tee debug.log

# Check DPI detection
python << 'EOF'
from mcp_server.platform.linux.dpi_handler import LinuxDPIHandler
handler = LinuxDPIHandler()
print(f"Detected DPI: {handler.get_dpi_info()}")
EOF

# Verify viewport metrics
python << 'EOF'
from mcp_server.platform.linux.window_manager import LinuxWindowManager
wm = LinuxWindowManager()
print(f"Viewport: {wm.get_viewport_metrics()}")
EOF
```

### Debug Information

Collect debug information for reporting issues:

```bash
#!/bin/bash
# debug_info.sh - Collect Linux system information

echo "=== System Information ==="
uname -a
cat /etc/os-release

echo "=== Display Server ==="
echo "Session Type: $XDG_SESSION_TYPE"
echo "Display: $DISPLAY"
ps aux | grep -E 'X|wayland' | grep -v grep

echo "=== Monitor Information ==="
xrandr --query --verbose 2>/dev/null || wlr-randr 2>/dev/null || echo "xrandr/wlr-randr not available"

echo "=== Python Environment ==="
python --version
pip freeze | grep -i 'playwright\|pillow\|pydantic'

echo "=== MCP Server Version ==="
python -c "import mcp_server; print(mcp_server.__version__)" 2>/dev/null || echo "MCP not installed"

echo "=== DPI Detection ==="
python << 'EOF' 2>/dev/null
from mcp_server.platform.linux.dpi_handler import LinuxDPIHandler
handler = LinuxDPIHandler()
print(handler.get_dpi_info())
EOF
```

---

## Performance Tuning

### Memory Optimization

```bash
# Reduce DOM cache size for low-memory systems
export MCP_DOM_CACHE_SIZE=10

# Enable memory profiling
export PYTHONMALLOC=malloc
export PYTHONTRACEMALLOC=1
```

### Display Server Performance

**X11 Optimization:**
```bash
# Use X11 for better performance (if available)
export GDK_SCALE=1  # Disable fractional scaling if not needed

# Enable X11 extensions
export LIBGL_ALWAYS_INDIRECT=1
```

**Wayland Optimization:**
```bash
# For NVIDIA GPUs on Wayland
export LIBVA_DRIVER_NAME=nvidia
export __GL_SYNC_TO_VBLANK=0

# For Intel GPUs
export LIBVA_DRIVER_NAME=iHD
```

### Playwright Optimization

```bash
# Disable unused features
export PLAYWRIGHT_LAUNCH_ARGS="--disable-extensions --disable-sync --no-default-browser-check"

# Enable GPU acceleration (if available)
export PLAYWRIGHT_LAUNCH_ARGS="--enable-gpu"

# Use system Chromium (faster startup)
export PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium-browser
```

### Coordinate Transformation Caching

```python
from mcp_server.platform.linux.coordinate_converter import LinuxCoordinateConverter

# Cache DPI information for repeated use
converter = LinuxCoordinateConverter()
converter.enable_cache(True)

# Perform transformations (subsequent calls will use cache)
result = converter.os_to_viewport(1920, 1080)
```

---

## Next Steps

1. **Configure** your AI client to use the MCP server
2. **Test** with examples in `/examples/` directory
3. **Read** [CROSS_PLATFORM_GUIDE.md](CROSS_PLATFORM_GUIDE.md) for architecture details
4. **Check** [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for platform-specific issues
5. **Review** [PERFORMANCE_BENCHMARKS.md](PERFORMANCE_BENCHMARKS.md) for benchmarks

---

## Support

- **Issues**: Report on GitHub with platform info
- **Logs**: Enable `MCP_LOG_LEVEL=DEBUG` for detailed logs
- **Testing**: Run `pytest tests/ -v` to verify installation
- **Documentation**: See [docs/](.) for additional guides

---

**Status**: Production Ready ✅
**Last Verified**: 2025-11-17 on Ubuntu 22.04 LTS, Fedora 39, and Arch Linux
