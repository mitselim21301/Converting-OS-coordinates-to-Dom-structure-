# System Requirements
## MCP Accurate Click Server - Cross-Platform Requirements

**Version**: 1.0.0
**Last Updated**: 2025-11-17
**Scope**: Windows, Linux, macOS

---

## Table of Contents

1. [Minimum Requirements](#minimum-requirements)
2. [Recommended Setup](#recommended-setup)
3. [Platform-Specific Requirements](#platform-specific-requirements)
4. [Optional Dependencies](#optional-dependencies)
5. [Hardware Requirements](#hardware-requirements)
6. [Network Requirements](#network-requirements)
7. [Compatibility Matrix](#compatibility-matrix)
8. [Verification Checklist](#verification-checklist)

---

## Minimum Requirements

### Universal (All Platforms)

| Component | Minimum | Notes |
|-----------|---------|-------|
| **Python** | 3.9 | 3.11+ recommended for better performance |
| **Memory** | 512 MB RAM | For basic operations |
| **Disk Space** | 100 MB | For installation + dependencies |
| **Network** | Optional | Only if using remote AI agents |

### Python Packages (Core)

```bash
# Installed via: pip install -r requirements.txt

playwright >= 1.40.0      # Browser automation
pillow >= 10.0.0          # Image processing
pydantic >= 2.0.0         # Data validation
python-dotenv >= 1.0.0    # Environment config
typing-extensions >= 4.5.0 # Type hints
```

### Verify Minimum Setup

```bash
# Check Python version
python --version  # Should be 3.9+

# Check available memory
free -h  # Linux
wmic OS get totalvisiblememorylength  # Windows
vm_stat  # macOS

# Check disk space
df -h  # Linux/macOS
dir C:  # Windows
```

---

## Recommended Setup

### For Development & Testing

| Component | Recommended | Reason |
|-----------|-------------|--------|
| **Python** | 3.11 or 3.12 | Better performance, security updates |
| **Memory** | 4+ GB RAM | For parallel testing, IDE, Docker |
| **Disk Space** | 2+ GB | For dependencies, test cache, logs |
| **Processor** | Multi-core (4+) | For parallel tests, vision processing |
| **OS Build** | Latest LTS | Long-term support, security patches |

### For Production Deployment

| Component | Recommended | Reason |
|-----------|-------------|--------|
| **Python** | 3.11.0+ | Stable, widely supported |
| **Memory** | 2-8 GB | Depends on concurrency |
| **CPU** | 2+ cores | For browser instances |
| **SSD** | 256+ MB free | For temp files, caching |
| **Network** | 1 Mbps minimum | For AI agent communication |

---

## Platform-Specific Requirements

### Windows Requirements

#### Minimum (Windows 10/11 Standard)

```
OS: Windows 10 Build 19041+ or Windows 11
Python: 3.9.0+ (64-bit)
Memory: 512 MB
Disk: 100 MB free
Display: 96 DPI or higher
```

#### Recommended (Windows 10/11 Professional)

```
OS: Windows 11 22H2+ (latest)
Python: 3.11+ (64-bit)
Memory: 4 GB
Disk: 2 GB free
GPU: Optional (NVIDIA/Intel for vision)
Display: Any modern monitor
```

#### Dependencies (Windows)

**System Libraries** (usually included):
- Windows API (GetDpiForMonitor, SendInput, etc.)
- COM interfaces for accessibility
- Windows Media Foundation (for video)

**Optional** (for enhanced features):
```powershell
# Install using winget, choco, or directly
# For GPU acceleration
nvidia-driver  # NVIDIA
intel-graphics-driver  # Intel

# For clipboard support
# Built-in Windows support, no installation needed
```

#### Installation on Windows

```powershell
# Create virtual environment
python -m venv venv

# Activate
.\venv\Scripts\activate

# Install
pip install -r requirements.txt
pip install -e .
```

### Linux Requirements

#### Minimum (X11 Desktop)

```
OS: Any Linux with kernel 4.4+
Display: X11 (Xorg)
Python: 3.9.0+ (64-bit)
Memory: 512 MB
Disk: 100 MB free
```

**Tested Distributions**:
- Ubuntu 18.04 LTS, 20.04 LTS, 22.04 LTS
- Debian 10, 11, 12
- Fedora 37, 38, 39
- Arch Linux
- CentOS/RHEL 8+

#### Recommended (Modern Linux)

```
OS: Ubuntu 22.04 LTS+ or Fedora 38+
Display: X11 or Wayland
Python: 3.11+ (64-bit)
Memory: 2+ GB
Disk: 500 MB free
GPU: Optional (for vision tasks)
```

#### Dependencies (Linux)

**Core System Packages** (X11):
```bash
# Debian/Ubuntu
sudo apt-get install -y \
    python3.11 python3.11-dev \
    x11-utils xdotool xrandr \
    libssl-dev libffi-dev \
    build-essential git

# Fedora/RHEL
sudo dnf install -y \
    python3.11 python3.11-devel \
    xorg-x11-utils xdotool \
    openssl-devel libffi-devel \
    gcc gcc-c++ make git

# Arch
sudo pacman -S \
    python xdotool xorg-utils \
    openssl libffi \
    base-devel git
```

**For Wayland**:
```bash
# Debian/Ubuntu
sudo apt-get install -y wlr-randr

# Fedora
sudo dnf install -y wlr-randr

# Arch
sudo pacman -S wlr-randr
```

**For Browser Support**:
```bash
# Option 1: System Chromium
# Debian/Ubuntu
sudo apt-get install chromium-browser

# Fedora
sudo dnf install chromium

# Option 2: Playwright (automatic)
pip install -r requirements.txt
playwright install chromium
```

#### Installation on Linux

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate
source venv/bin/activate

# Install
pip install -r requirements.txt
pip install -e .

# Verify display server
echo $XDG_SESSION_TYPE  # Should be 'x11' or 'wayland'
```

#### Permission Requirements (Linux)

```bash
# xdotool may need special permissions
sudo chmod u+s /usr/bin/xdotool

# Or run MCP server with sudo
sudo python -m mcp_server

# For better security, use sudo selectively
# Or create dedicated user
sudo useradd -m mcp-server
sudo -u mcp-server python -m mcp_server
```

### macOS Requirements (Experimental)

#### Minimum (macOS 10.15+)

```
OS: macOS 10.15 Catalina+
Python: 3.9.0+ (64-bit)
Memory: 512 MB
Disk: 100 MB free
CPU: Apple Silicon or Intel
```

#### Recommended (macOS 12+)

```
OS: macOS 12 Monterey+ (latest)
Python: 3.11+ (64-bit)
Memory: 2+ GB
Disk: 500 MB free
CPU: Apple Silicon (M1/M2/M3+) preferred
```

#### Installation on macOS

```bash
# Install Python via Homebrew
brew install python@3.11

# Create virtual environment
python3.11 -m venv venv

# Activate
source venv/bin/activate

# Install
pip install -r requirements.txt
pip install -e .
```

#### macOS-Specific Notes

- **Accessibility Permissions**: May require Terminal to have full disk access
- **Gatekeeper**: May need to allow running unsigned code
- **Retina Displays**: Automatic 2x scaling (backed pixels)
- **Notarization**: Required for App Store distribution

---

## Optional Dependencies

### For Vision/AI Features

```bash
# Computer vision (optional)
pip install -r requirements-vision.txt

# Includes:
# - opencv-python >= 4.8.0
# - numpy >= 1.24.0
# - PyYAML >= 6.0
# - scikit-image >= 0.21.0
```

### For Development & Testing

```bash
# Development dependencies
pip install -r requirements-dev.txt

# Includes:
# - pytest >= 7.4.0
# - pytest-asyncio >= 0.21.0
# - pytest-cov >= 4.1.0
# - black >= 23.0.0
# - flake8 >= 6.0.0
# - mypy >= 1.0.0
# - pre-commit >= 3.0.0
```

### For Documentation

```bash
# Documentation dependencies
pip install -r requirements-docs.txt

# Includes:
# - sphinx >= 7.0.0
# - sphinx-rtd-theme >= 1.3.0
# - myst-parser >= 2.0.0
```

---

## Hardware Requirements

### CPU Requirements

| Task | Requirement | Notes |
|------|-------------|-------|
| DOM Extraction | 1 core minimum | Can use 2+ cores for parallel |
| Coordinate Transforms | 1 core sufficient | All operations sub-millisecond |
| Vision Validation | 2+ cores | GPU preferred for faster inference |
| Multi-agent | 4+ cores | Each agent needs dedicated resources |

### Memory Requirements

| Task | Requirement | Notes |
|------|-------------|-------|
| Idle Server | ~50 MB | Base Python + server overhead |
| Browser Instance | ~200-500 MB | Chromium instance |
| DOM Cache (100 elements) | ~10-20 MB | Cached DOM structure |
| Vision Model | ~500-1000 MB | If using vision validation |
| 10 concurrent agents | ~2-3 GB | Browser + server + models |

### Disk I/O Requirements

| Component | Space | Type | Purpose |
|-----------|-------|------|---------|
| Installation | 100 MB | SSD | Program files |
| Playwright/Chromium | 300 MB | SSD | Browser binary |
| Cache & Logs | 100-500 MB | SSD/HDD | Temporary data |
| Vision Models | 500-2000 MB | SSD | ML models |

### GPU Requirements (Optional)

For vision-based validation (optional):

| GPU | VRAM | Recommendation | Examples |
|-----|------|-----------------|----------|
| None | - | All features work, vision slower | Fine for most uses |
| 2 GB | 2 GB | Adequate for vision tasks | GTX 1050, M1/M2 |
| 4+ GB | 4+ GB | Excellent performance | RTX 2060, M3 Max |
| 8+ GB | 8+ GB | Enterprise grade | RTX 3080, A100 |

---

## Network Requirements

### Minimum Network

```
Bandwidth: No minimum for local operation
Latency: No requirement for local use
```

### For Remote AI Agents

```
Download: 1 Mbps+ (for agent requests)
Upload: 1 Mbps+ (for responses)
Latency: <100ms preferred (for good UX)
Stability: No special requirements
```

### Network Configuration

```python
# Configure MCP server for network use
# In mcp_config.json:
{
  "server": {
    "host": "0.0.0.0",  # Listen on all interfaces
    "port": 5000,        # Configurable port
    "tls": true,         # Use TLS for security
    "certificate": "/path/to/cert.pem",
    "key": "/path/to/key.pem"
  }
}
```

---

## Compatibility Matrix

### Operating System Compatibility

| Feature | Windows 10/11 | Ubuntu 20.04+ | Fedora 38+ | Arch | macOS 12+ |
|---------|---|---|---|---|---|
| Basic Click | ✅ | ✅ | ✅ | ✅ | 🚧 |
| DOM Extraction | ✅ | ✅ | ✅ | ✅ | 🚧 |
| Coordinate Transform | ✅ | ✅ | ✅ | ✅ | 🚧 |
| Multi-Monitor | ✅ | ✅ | ✅ | ✅ | 🚧 |
| Vision Validation | ✅ | ✅ | ✅ | ✅ | 🚧 |
| Accessibility API | ✅ | ✅ | ✅ | ✅ | 🚧 |

Legend: ✅ Supported, 🚧 Experimental, ❌ Not supported

### Python Version Compatibility

| Python | Windows | Linux | macOS | Notes |
|--------|---------|-------|-------|-------|
| 3.8 | ❌ | ❌ | ❌ | Not supported |
| 3.9 | ✅ | ✅ | ✅ | Minimum supported |
| 3.10 | ✅ | ✅ | ✅ | Stable |
| 3.11 | ✅ | ✅ | ✅ | Recommended |
| 3.12 | ✅ | ✅ | ✅ | Latest |
| 3.13 | 🚧 | 🚧 | 🚧 | Development |

### Display Server Compatibility (Linux)

| Display Server | Support | Notes |
|---|---|---|
| X11 (Xorg) | ✅ Primary | Mature, widely tested |
| Wayland | ✅ Full | Modern, fully supported |
| Mir | ❌ | Not supported |
| Framebuffer | ❌ | Not supported |

### Browser Compatibility

| Browser | Status | Notes |
|---------|--------|-------|
| Chromium/Chrome | ✅ | Primary, fully supported |
| Firefox | 🚧 | Experimental |
| Safari | ❌ | Not supported yet |
| Edge | ✅ | Via Chromium engine |

---

## Verification Checklist

### Pre-Installation Checklist

- [ ] Python 3.9+ installed (`python --version`)
- [ ] pip is available (`pip --version`)
- [ ] Virtual environment support (`python -m venv --help`)
- [ ] Sufficient disk space (check with `df` or `dir`)
- [ ] Sufficient RAM (check with `free -h` or `vm_stat`)
- [ ] Internet connection (for downloading dependencies)

### Post-Installation Checklist

Run verification script:

```bash
#!/bin/bash
echo "=== MCP Server Verification ==="

# Check Python
echo "✓ Python: $(python --version)"

# Check pip
echo "✓ Pip: $(pip --version)"

# Check virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✓ Virtual Env: $VIRTUAL_ENV"
else
    echo "⚠ Virtual Env: Not activated"
fi

# Check imports
python << 'EOF'
import sys
print(f"✓ Python Path: {sys.executable}")

modules = ['mcp_server', 'playwright', 'pydantic', 'PIL']
for module in modules:
    try:
        __import__(module)
        print(f"✓ {module}")
    except ImportError:
        print(f"✗ {module} (not installed)")
EOF

# Check platform-specific
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "✓ Platform: Linux"
    echo "  Display: $XDG_SESSION_TYPE"
    if command -v xrandr &> /dev/null; then
        echo "  xrandr: found"
    else
        echo "  xrandr: not found"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "✓ Platform: macOS"
elif [[ "$OSTYPE" == "msys" ]]; then
    echo "✓ Platform: Windows"
fi

echo "=== Verification Complete ==="
```

### Runtime Verification

```bash
# Start server in test mode
python -m mcp_server --test

# Expected output:
# Starting MCP Accurate Click Server
# Version: 1.0.0
# Platform: [Windows|Linux|macOS]
# Status: Ready
```

---

## Troubleshooting

### Python Not Found

```bash
# Try explicit version
python3 --version
python3.11 --version

# Add to PATH if needed
export PATH="/usr/bin/python3.11:$PATH"
```

### Permission Denied (Linux)

```bash
# Fix virtual environment activation
chmod +x venv/bin/activate
source venv/bin/activate

# Fix xdotool permissions
sudo chmod u+s /usr/bin/xdotool
```

### Out of Memory

```bash
# Reduce cache size
export MCP_DOM_CACHE_SIZE=10

# Reduce concurrent agents
# Or increase available memory
```

### Display Server Errors

```bash
# Check DISPLAY variable
echo $DISPLAY

# Set for X11
export DISPLAY=:0

# Check Wayland
echo $XDG_SESSION_TYPE
```

---

## Version Support Timeline

| Version | Release | Support Ends | Status |
|---------|---------|--------------|--------|
| 1.0.0 | 2025-11-17 | 2026-11-17 | Current |
| 1.1.0 | 2026-Q2 | 2027-Q2 | Planned |
| 2.0.0 | 2027-Q1 | 2028-Q1 | Future |

---

**Status**: Production Ready
**Last Verified**: 2025-11-17
**Tested Platforms**: Windows 11, Ubuntu 22.04 LTS, Fedora 39, Arch Linux
