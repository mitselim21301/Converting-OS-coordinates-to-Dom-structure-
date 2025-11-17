#!/bin/bash

################################################################################
# openSUSE Setup Script
# Setup mcp-accurate-click-server on openSUSE Leap and Tumbleweed
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_privileges() {
    if [[ $EUID -ne 0 ]]; then
        log_warning "This script should be run as root for system package installation"
        log_info "Attempting to use sudo..."
        if ! command -v sudo &> /dev/null; then
            log_error "sudo is not available"
            exit 1
        fi
    fi
}

# Detect distribution details
detect_distro() {
    log_info "Detecting distribution..."

    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO_NAME=$NAME
        DISTRO_VERSION=$VERSION_ID
        log_success "Detected: $DISTRO_NAME $DISTRO_VERSION"
    else
        log_error "Cannot detect distribution"
        exit 1
    fi
}

# Update package manager
update_packages() {
    log_info "Updating package repository..."

    zypper refresh || {
        log_error "Failed to refresh package repository"
        exit 1
    }

    log_success "Package repository updated"
}

# Install required system packages
install_system_packages() {
    log_info "Installing required system packages..."

    local packages=(
        "xdotool"                  # Input simulation
        "wmctrl"                   # Window management
        "xrandr"                   # Monitor detection
        "xdpyinfo"                 # X11 display info
        "libX11-devel"             # X11 development libraries
        "libxcb-devel"             # Additional X11 libraries
        "python3-pip"              # Python package manager
        "python3-devel"            # Python development headers
    )

    log_info "Packages to install:"
    printf '%s\n' "${packages[@]}" | sed 's/^/  - /'

    # Install packages
    zypper install -y "${packages[@]}" || {
        log_error "Failed to install system packages"
        exit 1
    }

    log_success "System packages installed"
}

# Install Python packages
install_python_packages() {
    log_info "Installing Python packages..."

    local packages=(
        "pynput>=1.7.6"          # Mouse/keyboard control
        "python-xlib>=0.33"      # X11 low-level control
        "psutil>=5.9.0"          # Process utilities
    )

    log_info "Python packages to install:"
    printf '%s\n' "${packages[@]}" | sed 's/^/  - /'

    # Install via pip
    python3 -m pip install --upgrade pip || {
        log_warning "Failed to upgrade pip (may already be latest)"
    }

    for package in "${packages[@]}"; do
        log_info "Installing $package..."
        python3 -m pip install "$package" || {
            log_warning "Failed to install $package (may be optional)"
        }
    done

    log_success "Python packages installed"
}

# Verify installation
verify_installation() {
    log_info "Verifying installation..."

    local errors=0

    # Check system tools
    log_info "Checking system tools..."
    for tool in xdotool wmctrl xrandr xdpyinfo; do
        if command -v "$tool" &> /dev/null; then
            log_success "  ✓ $tool found"
        else
            log_warning "  ✗ $tool not found"
            errors=$((errors + 1))
        fi
    done

    # Check for xwininfo and xprop (might be in different packages)
    for tool in xwininfo xprop; do
        if command -v "$tool" &> /dev/null; then
            log_success "  ✓ $tool found"
        else
            log_warning "  ✗ $tool not found (may need xorg-x11-utilities)"
        fi
    done

    # Check Python modules
    log_info "Checking Python modules..."
    python3 << EOF
import sys
modules = ['pynput', 'Xlib', 'psutil']
for module in modules:
    try:
        __import__(module)
        print(f"  ✓ {module} available")
    except ImportError:
        print(f"  ✗ {module} not available")
        sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        log_success "All Python modules available"
    else
        log_warning "Some Python modules are missing"
    fi

    if [ $errors -eq 0 ]; then
        log_success "Installation verified successfully"
    else
        log_warning "Installation verification completed with $errors warnings"
    fi
}

# Display post-installation instructions
post_installation_info() {
    echo ""
    log_info "Post-installation steps:"
    echo ""
    echo "1. Additional packages that might be useful:"
    echo "   zypper install xorg-x11-utilities  # For xwininfo, xprop"
    echo ""
    echo "2. If using a display server other than X11:"
    echo "   - Export XDG_SESSION_TYPE environment variable"
    echo "   - Some features may be limited on Wayland"
    echo ""
    echo "3. To use mcp-accurate-click-server:"
    echo "   python3 -m mcp_server"
    echo ""
    echo "4. For Leap vs Tumbleweed:"
    echo "   - Leap: stable releases, tested packages"
    echo "   - Tumbleweed: rolling release, latest versions"
    echo ""
    echo "5. For more information:"
    echo "   - Check /docs/SETUP.md"
    echo "   - Visit https://github.com/yourusername/mcp-accurate-click-server"
    echo ""
}

# Main execution
main() {
    echo ""
    log_info "openSUSE Setup Script for mcp-accurate-click-server"
    echo ""

    detect_distro
    update_packages
    install_system_packages
    install_python_packages
    verify_installation
    post_installation_info

    log_success "Setup completed successfully!"
}

# Run main function
main "$@"
