# Linux Distribution Compatibility Guide

## Overview

mcp-accurate-click-server provides comprehensive support for multiple Linux distributions through a flexible setup system that automatically detects and configures for your specific distribution.

## Supported Distributions

### Debian Family (apt-based)
- **Ubuntu** 18.04 LTS and later
- **Debian** 10 (Buster) and later
- **Linux Mint** 19 and later
- **Elementary OS** 5 and later
- **Pop!_OS** any version
- **Zorin OS** any version

### Fedora Family (dnf/yum-based)
- **Fedora** 22 and later (dnf)
- **Fedora** 21 and earlier (yum)
- **RHEL** 7+ (yum), 8+ (dnf)
- **CentOS** 7+
- **AlmaLinux** any version
- **Rocky Linux** any version
- **Oracle Linux** any version

### Arch Family (pacman-based)
- **Arch Linux** (rolling release)
- **Manjaro** any version
- **Endeavour OS** any version
- **ArcoLinux** any version

### openSUSE Family (zypper-based)
- **openSUSE Leap** (stable releases)
- **openSUSE Tumbleweed** (rolling release)
- **SUSE Linux Enterprise** (SLE)

## System Requirements

### Minimum Requirements
- **OS**: Any supported Linux distribution
- **Python**: 3.9 or later
- **X11**: For X11-based systems (or Wayland with limitations)
- **Package Manager**: apt, dnf, yum, pacman, or zypper

### Required Packages by Distribution

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y \
    xdotool \
    wmctrl \
    x11-utils \
    libx11-dev \
    python3-pip \
    python3-dev
```

#### Fedora/RHEL
```bash
# For Fedora 22+ (dnf)
sudo dnf install -y \
    xdotool \
    wmctrl \
    libxrandr \
    libX11-devel \
    python3-pip \
    python3-devel

# For RHEL 7 (yum)
sudo yum install -y \
    xdotool \
    wmctrl \
    libXrandr \
    libX11-devel \
    python3-pip \
    python3-devel
```

#### Arch Linux
```bash
sudo pacman -Syu --noconfirm
sudo pacman -S --noconfirm \
    xdotool \
    wmctrl \
    xorg-xrandr \
    xorg-xwininfo \
    xorg-xprop \
    libx11 \
    python-pip
```

#### openSUSE
```bash
# openSUSE Leap/Tumbleweed
sudo zypper install -y \
    xdotool \
    wmctrl \
    xrandr \
    libX11-devel \
    python3-pip \
    python3-devel
```

### Required Python Packages

All distributions need these Python packages:

```bash
pip3 install \
    pynput>=1.7.6 \
    python-xlib>=0.33 \
    psutil>=5.9.0
```

## Display Server Support

### X11 Support (Full)
- Full support for all features
- Requires: xdotool, wmctrl, x11-utils
- Fallback methods: python-xlib, xdotool

### Wayland Support (Partial)
- Limited support due to Wayland security model
- Requires: appropriate Wayland session
- Status: pynput can work, but some features may be limited

### Detection
The system automatically detects your display server:
- Check environment variable: `XDG_SESSION_TYPE`
- Fallback checks: `WAYLAND_DISPLAY` or `DISPLAY`

## Setup Instructions

### Automatic Setup (Recommended)

```bash
# Clone or navigate to the project directory
cd /path/to/mcp-accurate-click-server

# Run the setup script
cd setup/linux
python3 setup.py

# Or with sudo if needed
sudo python3 setup.py
```

### Manual Setup

#### Step 1: Detect Your Distribution

```bash
cat /etc/os-release
```

#### Step 2: Install Required Packages

Choose the script for your distribution:
- Ubuntu/Debian: `bash scripts/setup_ubuntu_debian.sh`
- Fedora/RHEL: `bash scripts/setup_fedora_rhel.sh`
- Arch: `bash scripts/setup_arch.sh`
- openSUSE: `bash scripts/setup_opensuse.sh`

#### Step 3: Install Python Packages

```bash
pip3 install -r requirements.txt
pip3 install -e .[linux]
```

## Compatibility Matrix

### Distribution to Package Manager Mapping

| Distribution | Family | Package Manager |
|--------------|--------|-----------------|
| Ubuntu | Debian | apt |
| Debian | Debian | apt |
| Linux Mint | Debian | apt |
| Elementary OS | Debian | apt |
| Fedora | Fedora | dnf |
| RHEL 8+ | Fedora | dnf |
| RHEL 7 | Fedora | yum |
| CentOS | Fedora | yum |
| Arch Linux | Arch | pacman |
| Manjaro | Arch | pacman |
| openSUSE Leap | openSUSE | zypper |
| openSUSE Tumbleweed | openSUSE | zypper |

### Package Availability by Distribution

#### Core Packages

| Package | Ubuntu/Debian | Fedora/RHEL | Arch | openSUSE |
|---------|---|---|---|---|
| xdotool | xdotool | xdotool | xdotool | xdotool |
| wmctrl | wmctrl | wmctrl | wmctrl | wmctrl |
| x11-utils | x11-utils | xorg-x11-utils | xorg-xwininfo | xdpyinfo |
| xrandr | x11-utils | libxrandr | xorg-xrandr | xrandr |

#### Python Packages

| Package | Ubuntu/Debian | Fedora/RHEL | Arch | openSUSE |
|---------|---|---|---|---|
| pynput | pip/python3-pynput | pip | pip | pip |
| python-xlib | python3-xlib | python3-xlib | python-xlib | python3-xlib |
| psutil | python3-psutil | python3-psutil | python-psutil | python3-psutil |

## Installation Methods

### Method 1: Automatic Setup (Recommended)

```bash
sudo python3 setup/linux/setup.py
```

This automatically:
- Detects your distribution
- Validates compatibility
- Installs required packages
- Configures the environment
- Verifies installation

### Method 2: Using Distribution-Specific Scripts

```bash
# Ubuntu/Debian
sudo bash setup/linux/scripts/setup_ubuntu_debian.sh

# Fedora/RHEL
sudo bash setup/linux/scripts/setup_fedora_rhel.sh

# Arch Linux
sudo bash setup/linux/scripts/setup_arch.sh

# openSUSE
sudo bash setup/linux/scripts/setup_opensuse.sh
```

### Method 3: Manual Installation

```bash
# 1. Install system packages manually
# (See distribution-specific instructions above)

# 2. Install Python packages
pip3 install -r setup/linux/requirements.txt

# 3. Install from source
pip3 install -e .
```

## Verification

### Check Installation

```bash
# Verify system tools
which xdotool wmctrl xrandr

# Verify Python modules
python3 -c "import pynput, Xlib, psutil; print('OK')"

# Test the server
python3 -m mcp_server --help
```

### Troubleshooting

#### Missing xdotool
```bash
# Ubuntu/Debian
sudo apt-get install xdotool

# Fedora
sudo dnf install xdotool

# Arch
sudo pacman -S xdotool

# openSUSE
sudo zypper install xdotool
```

#### Python Module Import Errors
```bash
# Reinstall with verbose output
pip3 install --upgrade --force-reinstall pynput python-xlib psutil -v
```

#### X11/Display Issues
```bash
# Check your display server
echo $XDG_SESSION_TYPE
echo $DISPLAY
echo $WAYLAND_DISPLAY

# List available tools
which xdotool wmctrl xrandr
```

## Alternative Tool Paths

The system supports multiple locations for tools:

### xdotool Alternatives
- `/usr/bin/xdotool` (standard)
- `/usr/local/bin/xdotool` (manual installation)

### wmctrl Alternatives
- `/usr/bin/wmctrl` (standard)
- `/usr/local/bin/wmctrl` (manual installation)

### Python Library Fallbacks
If a primary method is unavailable, the system falls back to:
1. **pynput** (primary, cross-platform)
2. **python-xlib** (X11 native)
3. **xdotool** (external tool)

## Desktop Environment Notes

### GNOME
- Works well with native Wayland
- X11 mode provides better compatibility

### KDE Plasma
- Excellent support on both X11 and Wayland
- All features available

### XFCE
- Works well on X11
- Some features may be limited on Wayland

### i3/Sway (Tiling WMs)
- Full support on X11 (i3)
- Wayland support on Sway is developing

## Container and WSL Support

### Docker/Podman Containers
- Requires X11 forwarding or Wayland socket mounting
- Setup works normally inside container

### WSL (Windows Subsystem for Linux)
- Requires X11 server (e.g., VcXsrv, X410)
- Or WSLg (WSL with integrated GUI)
- Setup detects and notes WSL environment

## Known Limitations

### Wayland Limitations
1. Some tools (xdotool, wmctrl) are X11-only
2. pynput provides fallback support
3. Window management features may be limited

### Multi-Monitor Setup
- Requires xrandr for proper detection
- Some desktop environments handle this differently

### SELinux/AppArmor
- May restrict tool usage in strict modes
- Consider using permissive mode or updating policies

## Getting Help

### Check Compatibility
```bash
python3 setup/linux/setup.py --check-only
```

### Verbose Output
```bash
python3 setup/linux/setup.py --verbose
```

### Dry Run
```bash
python3 setup/linux/setup.py --dry-run
```

## Configuration

After installation, configure via:
- Environment variables: `XDG_SESSION_TYPE`, `DISPLAY`
- Configuration file: `~/.config/mcp-accurate-click-server/config.yml`
- Command-line arguments

## Updates and Maintenance

### Keeping Packages Updated

```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get upgrade

# Fedora
sudo dnf upgrade

# Arch
sudo pacman -Syu

# openSUSE
sudo zypper update
```

### Reinstalling mcp-accurate-click-server

```bash
pip3 install --upgrade --force-reinstall mcp-accurate-click-server
```

## Performance Considerations

### X11 vs Wayland Performance
- X11: Generally better for mouse/keyboard control
- Wayland: Better security but requires native tool support

### Multi-Monitor Performance
- Enable xrandr for faster display detection
- Cache display information when possible

## Additional Resources

- Project Documentation: [../../../docs/](../../../docs/)
- Linux Setup Module: [detection/](detection/) and [matrix/](matrix/)
- Example Scripts: [scripts/](scripts/)
- Python Modules: [../../../src/mcp_server/platform/linux/](../../../src/mcp_server/platform/linux/)
