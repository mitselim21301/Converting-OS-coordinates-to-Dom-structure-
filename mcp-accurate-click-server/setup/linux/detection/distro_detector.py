"""
Linux Distribution Detector

Detects the Linux distribution and desktop environment for compatibility handling.
Provides methods to determine package manager and system characteristics.
"""

import os
import re
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class PackageManager(Enum):
    """Supported Linux package managers."""
    APT = "apt"  # Debian, Ubuntu, Linux Mint
    DNF = "dnf"  # Fedora, RHEL 8+
    YUM = "yum"  # RHEL 7, CentOS
    PACMAN = "pacman"  # Arch, Manjaro
    ZYPPER = "zypper"  # openSUSE, SLE
    UNKNOWN = "unknown"


class DesktopEnvironment(Enum):
    """Supported desktop environments."""
    GNOME = "gnome"
    KDE = "kde"
    XFCE = "xfce"
    LXDE = "lxde"
    CINNAMON = "cinnamon"
    MATE = "mate"
    I3 = "i3"
    SWAY = "sway"
    UNKNOWN = "unknown"


class DisplayServer(Enum):
    """Display servers."""
    X11 = "x11"
    WAYLAND = "wayland"
    UNKNOWN = "unknown"


class DistributionInfo:
    """Information about the current Linux distribution."""

    def __init__(self):
        self.distro_id = ""
        self.distro_name = ""
        self.distro_version = ""
        self.distro_version_id = ""
        self.package_manager = PackageManager.UNKNOWN
        self.desktop_env = DesktopEnvironment.UNKNOWN
        self.display_server = DisplayServer.UNKNOWN
        self.python_version = ""
        self.is_container = False
        self.is_wsl = False


class DistributionDetector:
    """
    Detects Linux distribution and environment details.

    Supports:
    - Ubuntu/Debian (apt-based)
    - Fedora/RHEL (dnf/yum-based)
    - Arch Linux (pacman-based)
    - openSUSE (zypper-based)
    """

    # Paths to check for distribution info
    OS_RELEASE_PATHS = [
        Path("/etc/os-release"),
        Path("/usr/lib/os-release"),
        Path("/etc/lsb-release"),
        Path("/etc/system-release"),
    ]

    def __init__(self):
        """Initialize distribution detector."""
        self._info: Optional[DistributionInfo] = None

    def detect(self) -> DistributionInfo:
        """
        Detect Linux distribution and environment.

        Returns:
            DistributionInfo object with detection results
        """
        if self._info is not None:
            return self._info

        info = DistributionInfo()

        # Detect distribution
        self._detect_distro(info)

        # Detect package manager
        self._detect_package_manager(info)

        # Detect desktop environment
        self._detect_desktop_environment(info)

        # Detect display server
        self._detect_display_server(info)

        # Detect Python version
        self._detect_python_version(info)

        # Detect container/WSL
        self._detect_container_wsl(info)

        logger.info(f"Detected distribution: {info.distro_name} {info.distro_version}")
        logger.info(f"Package manager: {info.package_manager.value}")
        logger.info(f"Desktop environment: {info.desktop_env.value}")
        logger.info(f"Display server: {info.display_server.value}")

        self._info = info
        return info

    def _detect_distro(self, info: DistributionInfo) -> None:
        """Detect Linux distribution from os-release files."""
        os_release_data = {}

        # Try os-release file
        for path in self.OS_RELEASE_PATHS:
            if path.exists():
                try:
                    os_release_data = self._parse_os_release(path)
                    if os_release_data:
                        break
                except Exception as e:
                    logger.debug(f"Failed to parse {path}: {e}")

        # Extract relevant fields
        info.distro_id = os_release_data.get("ID", "").lower()
        info.distro_name = os_release_data.get("NAME", "Unknown Linux")
        info.distro_version = os_release_data.get("VERSION", "")
        info.distro_version_id = os_release_data.get("VERSION_ID", "")

        # Normalize distro ID
        if not info.distro_id:
            info.distro_id = info.distro_name.lower().split()[0]

    def _parse_os_release(self, path: Path) -> Dict[str, str]:
        """
        Parse os-release file format.

        Handles both KEY=VALUE and KEY="VALUE" formats.

        Returns:
            Dictionary of os-release key-value pairs
        """
        data = {}
        try:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    if '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes
                        value = value.strip('"\'')
                        data[key.strip()] = value

        except Exception as e:
            logger.debug(f"Error parsing {path}: {e}")

        return data

    def _detect_package_manager(self, info: DistributionInfo) -> None:
        """Detect package manager based on distro ID."""
        distro_id = info.distro_id.lower()

        # APT-based distributions
        if any(x in distro_id for x in ['ubuntu', 'debian', 'mint', 'elementary', 'pop']):
            info.package_manager = PackageManager.APT
            return

        # DNF-based distributions (Fedora 22+, RHEL 8+)
        if any(x in distro_id for x in ['fedora', 'rhel', 'centos']):
            if self._command_exists('dnf'):
                info.package_manager = PackageManager.DNF
                return
            else:
                info.package_manager = PackageManager.YUM
                return

        # Pacman-based distributions
        if any(x in distro_id for x in ['arch', 'manjaro', 'endeavour']):
            info.package_manager = PackageManager.PACMAN
            return

        # Zypper-based distributions
        if any(x in distro_id for x in ['opensuse', 'suse']):
            info.package_manager = PackageManager.ZYPPER
            return

        # Try to detect by checking available commands
        if self._command_exists('apt') or self._command_exists('apt-get'):
            info.package_manager = PackageManager.APT
        elif self._command_exists('dnf'):
            info.package_manager = PackageManager.DNF
        elif self._command_exists('yum'):
            info.package_manager = PackageManager.YUM
        elif self._command_exists('pacman'):
            info.package_manager = PackageManager.PACMAN
        elif self._command_exists('zypper'):
            info.package_manager = PackageManager.ZYPPER

    def _detect_desktop_environment(self, info: DistributionInfo) -> None:
        """Detect desktop environment from environment variables."""
        xdg_current_desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        xdg_session_desktop = os.environ.get('XDG_SESSION_DESKTOP', '').lower()
        desktop_session = os.environ.get('DESKTOP_SESSION', '').lower()

        # Combine all sources
        desktop_indicators = f"{xdg_current_desktop} {xdg_session_desktop} {desktop_session}".lower()

        if 'gnome' in desktop_indicators:
            info.desktop_env = DesktopEnvironment.GNOME
        elif 'kde' in desktop_indicators or 'plasma' in desktop_indicators:
            info.desktop_env = DesktopEnvironment.KDE
        elif 'xfce' in desktop_indicators:
            info.desktop_env = DesktopEnvironment.XFCE
        elif 'lxde' in desktop_indicators or 'lxqt' in desktop_indicators:
            info.desktop_env = DesktopEnvironment.LXDE
        elif 'cinnamon' in desktop_indicators:
            info.desktop_env = DesktopEnvironment.CINNAMON
        elif 'mate' in desktop_indicators:
            info.desktop_env = DesktopEnvironment.MATE
        elif 'i3' in desktop_indicators:
            info.desktop_env = DesktopEnvironment.I3
        elif 'sway' in desktop_indicators:
            info.desktop_env = DesktopEnvironment.SWAY

    def _detect_display_server(self, info: DistributionInfo) -> None:
        """Detect display server (X11 or Wayland)."""
        xdg_session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        wayland_display = os.environ.get('WAYLAND_DISPLAY', '')
        display = os.environ.get('DISPLAY', '')

        if xdg_session_type in ['x11', 'wayland']:
            info.display_server = DisplayServer.X11 if xdg_session_type == 'x11' else DisplayServer.WAYLAND
        elif wayland_display:
            info.display_server = DisplayServer.WAYLAND
        elif display:
            info.display_server = DisplayServer.X11

    def _detect_python_version(self, info: DistributionInfo) -> None:
        """Detect Python version."""
        import sys
        info.python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    def _detect_container_wsl(self, info: DistributionInfo) -> None:
        """Detect if running in container or WSL."""
        # Check for WSL
        try:
            with open('/proc/version', 'r') as f:
                content = f.read().lower()
                if 'microsoft' in content or 'wsl' in content:
                    info.is_wsl = True
        except:
            pass

        # Check for container (Docker, systemd-nspawn, etc.)
        if Path('/.dockerenv').exists() or Path('/run/.containerenv').exists():
            info.is_container = True

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH."""
        try:
            subprocess.run(
                ['which', command],
                capture_output=True,
                check=True,
                timeout=1
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_info(self) -> DistributionInfo:
        """Get cached distribution info or detect it."""
        if self._info is None:
            self.detect()
        return self._info

    def is_compatible(self) -> bool:
        """Check if distribution is supported."""
        return self.get_info().package_manager != PackageManager.UNKNOWN

    def get_display_server(self) -> DisplayServer:
        """Get detected display server."""
        return self.get_info().display_server

    def get_package_manager(self) -> PackageManager:
        """Get detected package manager."""
        return self.get_info().package_manager

    def __repr__(self) -> str:
        """String representation."""
        info = self.get_info()
        return (
            f"DistributionDetector("
            f"distro={info.distro_name} {info.distro_version}, "
            f"pkg_mgr={info.package_manager.value}, "
            f"de={info.desktop_env.value}, "
            f"display={info.display_server.value}"
            f")"
        )


# Global detector instance
_detector: Optional[DistributionDetector] = None


def get_detector() -> DistributionDetector:
    """Get or create global distribution detector."""
    global _detector
    if _detector is None:
        _detector = DistributionDetector()
    return _detector


__all__ = [
    'DistributionDetector',
    'DistributionInfo',
    'PackageManager',
    'DesktopEnvironment',
    'DisplayServer',
    'get_detector',
]
