# Linux Setup Module

Comprehensive Linux distribution compatibility and setup system for mcp-accurate-click-server.

## Features

- **Automatic Distribution Detection**: Detects OS, version, package manager, and desktop environment
- **Multi-Distribution Support**: Ubuntu, Debian, Fedora, RHEL, Arch, Manjaro, openSUSE, and more
- **Tool Availability Detection**: Checks for required and optional system tools
- **Compatibility Matrix**: Maps packages to distributions
- **Automated Setup**: One-command setup with intelligent fallbacks
- **Comprehensive Validation**: Verifies all requirements before and after installation

## Structure

```
setup/linux/
├── setup.py                          # Main orchestrator script
├── README.md                         # This file
├── LINUX_COMPATIBILITY.md            # Detailed compatibility guide
├── detection/                        # Distribution detection modules
│   ├── __init__.py
│   ├── distro_detector.py           # OS detection
│   └── tool_detector.py             # Tool availability checking
├── matrix/                           # Compatibility matrix
│   ├── __init__.py
│   └── compatibility_matrix.py       # Package mappings
└── scripts/                          # Distribution-specific setup scripts
    ├── setup_ubuntu_debian.sh        # Debian family setup
    ├── setup_fedora_rhel.sh         # Fedora family setup
    ├── setup_arch.sh                # Arch family setup
    └── setup_opensuse.sh            # openSUSE family setup
```

## Quick Start

### Automatic Setup (Recommended)

```bash
cd /path/to/mcp-accurate-click-server
sudo python3 setup/linux/setup.py
```

### Check Compatibility Only

```bash
python3 setup/linux/setup.py --check-only
```

### Verbose Output

```bash
python3 setup/linux/setup.py --verbose
```

### Dry Run (See what would be done)

```bash
python3 setup/linux/setup.py --dry-run
```

## Supported Distributions

### Debian Family
- Ubuntu 18.04 LTS+
- Debian 10+
- Linux Mint 19+
- Elementary OS 5+
- Pop!_OS
- Zorin OS

### Fedora Family
- Fedora 22+
- RHEL 7+
- CentOS 7+
- AlmaLinux
- Rocky Linux

### Arch Family
- Arch Linux
- Manjaro
- Endeavour OS
- ArcoLinux

### openSUSE Family
- openSUSE Leap
- openSUSE Tumbleweed
- SUSE Linux Enterprise

## Components

### 1. Distribution Detector (`detection/distro_detector.py`)

Detects:
- Linux distribution and version
- Package manager (apt, dnf, yum, pacman, zypper)
- Desktop environment (GNOME, KDE, XFCE, etc.)
- Display server (X11 or Wayland)
- Container/WSL environment
- Python version

Usage:
```python
from detection.distro_detector import get_detector

detector = get_detector()
info = detector.detect()

print(f"Distribution: {info.distro_name}")
print(f"Package Manager: {info.package_manager.value}")
print(f"Display Server: {info.display_server.value}")
```

### 2. Tool Detector (`detection/tool_detector.py`)

Detects availability of:
- System tools: xdotool, wmctrl, xwininfo, xprop, xrandr
- Python modules: pynput, python-xlib, psutil
- Fallback methods and alternative locations

Usage:
```python
from detection.tool_detector import get_tool_detector

detector = get_tool_detector()
detector.detect_all()

print(detector.get_summary())
print(f"Has X11 tools: {detector.has_x11_tools()}")
print(f"Has Python base: {detector.has_python_base()}")
```

### 3. Compatibility Matrix (`matrix/compatibility_matrix.py`)

Provides:
- Package name mappings by distribution
- Installation commands
- Required vs optional packages
- Distribution family detection

Usage:
```python
from matrix.compatibility_matrix import CompatibilityMatrix, DistroFamily

family = CompatibilityMatrix.get_distro_family('ubuntu')
packages = CompatibilityMatrix.get_all_required_packages(family)
install_cmd = CompatibilityMatrix.get_install_command('apt', packages)
```

### 4. Setup Orchestrator (`setup.py`)

Main entry point that:
1. Detects distribution
2. Validates compatibility
3. Detects tools
4. Shows summary
5. Runs distribution-specific setup
6. Verifies installation

### 5. Distribution-Specific Scripts

Bash scripts for each distribution family:
- **setup_ubuntu_debian.sh**: Uses apt-get
- **setup_fedora_rhel.sh**: Uses dnf/yum
- **setup_arch.sh**: Uses pacman
- **setup_opensuse.sh**: Uses zypper

Each script:
- Detects distribution details
- Updates package manager
- Installs system packages
- Installs Python packages
- Verifies installation
- Provides post-installation guidance

## Installation Steps

### Step 1: Clone/Navigate to Repository

```bash
cd /path/to/mcp-accurate-click-server
```

### Step 2: Run Setup

```bash
# With sudo (for system packages)
sudo python3 setup/linux/setup.py

# Or if you have sudoers configured
python3 setup/linux/setup.py
```

### Step 3: Verify Installation

```bash
python3 -c "import mcp_server; print('OK')"
```

### Step 4: Test

```bash
python3 -m mcp_server --help
```

## Troubleshooting

### Check Distribution Detection

```bash
python3 -c "from setup.linux.detection import get_detector; print(get_detector())"
```

### Check Tool Availability

```bash
python3 -c "from setup.linux.detection import get_tool_detector; print(get_tool_detector().get_summary())"
```

### Check Compatibility

```bash
python3 setup/linux/setup.py --check-only --verbose
```

### Manual Installation

```bash
# See LINUX_COMPATIBILITY.md for distribution-specific instructions
```

## Key Configuration

### Environment Variables

```bash
# Display server (X11 or wayland)
export XDG_SESSION_TYPE=x11

# X11 display
export DISPLAY=:0

# Wayland display (if using Wayland)
export WAYLAND_DISPLAY=wayland-0
```

### Python Packages Required

```bash
pip3 install pynput>=1.7.6 python-xlib>=0.33 psutil>=5.9.0
```

## Package Details

### System Tools (Required)

| Tool | Purpose | Alternative |
|------|---------|-------------|
| xdotool | Input simulation | pynput (Python) |
| wmctrl | Window management | xdotool |
| xwininfo | Window info | wmctrl |
| xprop | X11 properties | wmctrl |
| xrandr | Monitor detection | None |

### System Tools (Optional)

| Tool | Purpose | Fallback |
|------|---------|----------|
| arandr | GUI monitor tool | xrandr |

### Python Modules (Required)

| Module | Purpose | Alternative |
|--------|---------|------------|
| pynput | Mouse/keyboard control | python-xlib + xdotool |

### Python Modules (Optional)

| Module | Purpose |
|--------|---------|
| python-xlib | X11 native control |
| psutil | Process utilities |

## Display Server Compatibility

### X11
- Full feature support
- All tools available
- Best compatibility

### Wayland
- Partial support
- Limited window management
- pynput works but some features restricted
- Status: Improving

## Multi-Monitor Support

Requires:
- xrandr (for detection)
- Proper GNOME/KDE/XFCE settings
- X11 display server

## Known Issues

### Wayland Limitations
1. wmctrl, xdotool don't work on Wayland
2. Window management features limited
3. Fallback to pynput available

### SELinux
- May block tool execution
- Can disable with `setenforce 0` (temporary)
- Or update policies for specific tools

### WSL
- Requires X11 server
- Can use VcXsrv or WSLg
- Display forwarding required

## Adding Support for New Distributions

To add a new distribution:

1. **Add to compatibility matrix** (`matrix/compatibility_matrix.py`):
   ```python
   DISTRO_TO_FAMILY = {
       'mynewdistro': DistroFamily.FAMILY_NAME,
   }
   ```

2. **Add package mappings**:
   ```python
   PACKAGES = {
       'xdotool': {
           DistroFamily.FAMILY_NAME: PackageInfo(...),
       },
   }
   ```

3. **Create setup script** (if needed):
   - Copy existing script
   - Adjust for package manager

4. **Test**:
   ```bash
   python3 setup.py --check-only --verbose
   ```

## Performance Tips

1. Use X11 for best performance
2. Keep system packages updated
3. Use cached tool detection when possible
4. Consider using native libraries over subprocess calls

## Security Considerations

1. Setup scripts require sudo for system packages
2. Review scripts before running with sudo
3. Input validation in detection modules
4. No arbitrary command execution

## Testing

To test setup without making changes:

```bash
# Check only
python3 setup/linux/setup.py --check-only

# Dry run
python3 setup/linux/setup.py --dry-run

# Verbose (see details)
python3 setup/linux/setup.py --verbose
```

## Contributing

To improve Linux compatibility:

1. Test on your distribution
2. Report issues with output from `--verbose --check-only`
3. Submit pull requests with new distribution support
4. Update compatibility matrix
5. Document specific issues/workarounds

## References

- [LINUX_COMPATIBILITY.md](LINUX_COMPATIBILITY.md) - Detailed compatibility guide
- [../../../docs/](../../../docs/) - Main documentation
- [../../../src/mcp_server/platform/linux/](../../../src/mcp_server/platform/linux/) - Linux platform code

## License

Same as main project (MIT License)

---

For detailed information about specific distributions, see [LINUX_COMPATIBILITY.md](LINUX_COMPATIBILITY.md)
