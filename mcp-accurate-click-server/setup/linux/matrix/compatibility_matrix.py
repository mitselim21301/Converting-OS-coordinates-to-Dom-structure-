"""
Linux Distribution Compatibility Matrix

Defines package names, installation commands, and compatibility information
for each supported Linux distribution family.
"""

from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass


class DistroFamily(Enum):
    """Linux distribution families."""
    DEBIAN = "debian"  # Ubuntu, Debian, Linux Mint, Elementary
    FEDORA = "fedora"  # Fedora, RHEL, CentOS, AlmaLinux
    ARCH = "arch"  # Arch, Manjaro, Endeavour
    OPENSUSE = "opensuse"  # openSUSE, SLE
    UNKNOWN = "unknown"


@dataclass
class PackageInfo:
    """Information about a package."""
    name: str
    alternative_names: List[str]
    description: str
    required: bool = False
    python_package: bool = False
    version_check: Optional[str] = None


class CompatibilityMatrix:
    """
    Comprehensive compatibility matrix for Linux distributions.

    Provides:
    - Package names for each distribution family
    - Installation commands
    - Alternative package names
    - Compatibility information
    """

    # Package definitions by distribution family
    PACKAGES = {
        'pynput': {
            DistroFamily.DEBIAN: PackageInfo(
                name='python3-pynput',
                alternative_names=['pip', 'pip3'],
                description='Mouse/keyboard control (Python)',
                required=True,
                python_package=True,
            ),
            DistroFamily.FEDORA: PackageInfo(
                name='python3-pynput',
                alternative_names=['pip', 'pip3'],
                description='Mouse/keyboard control (Python)',
                required=True,
                python_package=True,
            ),
            DistroFamily.ARCH: PackageInfo(
                name='python-pynput',
                alternative_names=['pip'],
                description='Mouse/keyboard control (Python)',
                required=True,
                python_package=True,
            ),
            DistroFamily.OPENSUSE: PackageInfo(
                name='python3-pynput',
                alternative_names=['pip', 'pip3'],
                description='Mouse/keyboard control (Python)',
                required=True,
                python_package=True,
            ),
        },

        'python-xlib': {
            DistroFamily.DEBIAN: PackageInfo(
                name='python3-xlib',
                alternative_names=['pip', 'pip3'],
                description='X11 low-level control (Python)',
                python_package=True,
            ),
            DistroFamily.FEDORA: PackageInfo(
                name='python3-xlib',
                alternative_names=['pip', 'pip3'],
                description='X11 low-level control (Python)',
                python_package=True,
            ),
            DistroFamily.ARCH: PackageInfo(
                name='python-xlib',
                alternative_names=['pip'],
                description='X11 low-level control (Python)',
                python_package=True,
            ),
            DistroFamily.OPENSUSE: PackageInfo(
                name='python3-xlib',
                alternative_names=['pip', 'pip3'],
                description='X11 low-level control (Python)',
                python_package=True,
            ),
        },

        'psutil': {
            DistroFamily.DEBIAN: PackageInfo(
                name='python3-psutil',
                alternative_names=['pip', 'pip3'],
                description='Process utilities (Python)',
                python_package=True,
            ),
            DistroFamily.FEDORA: PackageInfo(
                name='python3-psutil',
                alternative_names=['pip', 'pip3'],
                description='Process utilities (Python)',
                python_package=True,
            ),
            DistroFamily.ARCH: PackageInfo(
                name='python-psutil',
                alternative_names=['pip'],
                description='Process utilities (Python)',
                python_package=True,
            ),
            DistroFamily.OPENSUSE: PackageInfo(
                name='python3-psutil',
                alternative_names=['pip', 'pip3'],
                description='Process utilities (Python)',
                python_package=True,
            ),
        },

        'xdotool': {
            DistroFamily.DEBIAN: PackageInfo(
                name='xdotool',
                alternative_names=['xdotool-dev'],
                description='X11 input simulation tool',
                required=True,
            ),
            DistroFamily.FEDORA: PackageInfo(
                name='xdotool',
                alternative_names=['xdotool-devel'],
                description='X11 input simulation tool',
                required=True,
            ),
            DistroFamily.ARCH: PackageInfo(
                name='xdotool',
                alternative_names=[],
                description='X11 input simulation tool',
                required=True,
            ),
            DistroFamily.OPENSUSE: PackageInfo(
                name='xdotool',
                alternative_names=['xdotool-devel'],
                description='X11 input simulation tool',
                required=True,
            ),
        },

        'wmctrl': {
            DistroFamily.DEBIAN: PackageInfo(
                name='wmctrl',
                alternative_names=[],
                description='Window manager control tool',
                required=True,
            ),
            DistroFamily.FEDORA: PackageInfo(
                name='wmctrl',
                alternative_names=[],
                description='Window manager control tool',
                required=True,
            ),
            DistroFamily.ARCH: PackageInfo(
                name='wmctrl',
                alternative_names=[],
                description='Window manager control tool',
                required=True,
            ),
            DistroFamily.OPENSUSE: PackageInfo(
                name='wmctrl',
                alternative_names=[],
                description='Window manager control tool',
                required=True,
            ),
        },

        'x11-utils': {
            DistroFamily.DEBIAN: PackageInfo(
                name='x11-utils',
                alternative_names=[],
                description='X11 utilities (xwininfo, xprop)',
            ),
            DistroFamily.FEDORA: PackageInfo(
                name='libxrandr',
                alternative_names=['xrandr'],
                description='X11 utilities (xwininfo, xprop)',
            ),
            DistroFamily.ARCH: PackageInfo(
                name='xorg-xwininfo',
                alternative_names=['xorg-xprop'],
                description='X11 utilities (xwininfo, xprop)',
            ),
            DistroFamily.OPENSUSE: PackageInfo(
                name='xdpyinfo',
                alternative_names=['xprop', 'xwininfo'],
                description='X11 utilities (xwininfo, xprop)',
            ),
        },

        'xrandr': {
            DistroFamily.DEBIAN: PackageInfo(
                name='x11-utils',
                alternative_names=['xrandr'],
                description='Monitor detection tool',
            ),
            DistroFamily.FEDORA: PackageInfo(
                name='xrandr',
                alternative_names=['libxrandr'],
                description='Monitor detection tool',
            ),
            DistroFamily.ARCH: PackageInfo(
                name='xorg-xrandr',
                alternative_names=[],
                description='Monitor detection tool',
            ),
            DistroFamily.OPENSUSE: PackageInfo(
                name='xrandr',
                alternative_names=[],
                description='Monitor detection tool',
            ),
        },

        'libx11-dev': {
            DistroFamily.DEBIAN: PackageInfo(
                name='libx11-dev',
                alternative_names=[],
                description='X11 development libraries',
            ),
            DistroFamily.FEDORA: PackageInfo(
                name='libX11-devel',
                alternative_names=[],
                description='X11 development libraries',
            ),
            DistroFamily.ARCH: PackageInfo(
                name='libx11',
                alternative_names=[],
                description='X11 development libraries',
            ),
            DistroFamily.OPENSUSE: PackageInfo(
                name='libX11-devel',
                alternative_names=[],
                description='X11 development libraries',
            ),
        },
    }

    # Installation commands by package manager
    INSTALL_COMMANDS = {
        'apt': 'sudo apt-get update && sudo apt-get install -y {packages}',
        'dnf': 'sudo dnf install -y {packages}',
        'yum': 'sudo yum install -y {packages}',
        'pacman': 'sudo pacman -Syu --noconfirm && sudo pacman -S --noconfirm {packages}',
        'zypper': 'sudo zypper install -y {packages}',
    }

    # Distribution to family mapping
    DISTRO_TO_FAMILY = {
        'ubuntu': DistroFamily.DEBIAN,
        'debian': DistroFamily.DEBIAN,
        'mint': DistroFamily.DEBIAN,
        'elementary': DistroFamily.DEBIAN,
        'pop': DistroFamily.DEBIAN,
        'neon': DistroFamily.DEBIAN,
        'deepin': DistroFamily.DEBIAN,
        'zorin': DistroFamily.DEBIAN,
        'peppermint': DistroFamily.DEBIAN,

        'fedora': DistroFamily.FEDORA,
        'rhel': DistroFamily.FEDORA,
        'centos': DistroFamily.FEDORA,
        'almalinux': DistroFamily.FEDORA,
        'rockylinux': DistroFamily.FEDORA,
        'oraclelinux': DistroFamily.FEDORA,

        'arch': DistroFamily.ARCH,
        'manjaro': DistroFamily.ARCH,
        'endeavouros': DistroFamily.ARCH,
        'arcolinux': DistroFamily.ARCH,

        'opensuse-leap': DistroFamily.OPENSUSE,
        'opensuse-tumbleweed': DistroFamily.OPENSUSE,
        'opensuse': DistroFamily.OPENSUSE,
        'sles': DistroFamily.OPENSUSE,
    }

    @classmethod
    def get_distro_family(cls, distro_id: str) -> DistroFamily:
        """
        Get distribution family from distribution ID.

        Args:
            distro_id: Distribution ID from os-release

        Returns:
            DistroFamily enum value
        """
        distro_id = distro_id.lower()

        # Direct match
        if distro_id in cls.DISTRO_TO_FAMILY:
            return cls.DISTRO_TO_FAMILY[distro_id]

        # Partial match
        for pattern, family in cls.DISTRO_TO_FAMILY.items():
            if pattern in distro_id or distro_id in pattern:
                return family

        return DistroFamily.UNKNOWN

    @classmethod
    def get_package_name(
        cls,
        package_id: str,
        distro_family: DistroFamily
    ) -> Optional[str]:
        """
        Get package name for a given distribution family.

        Args:
            package_id: Package identifier (e.g., 'xdotool')
            distro_family: Distribution family

        Returns:
            Package name or None if not supported
        """
        if package_id not in cls.PACKAGES:
            return None

        package_info = cls.PACKAGES[package_id].get(distro_family)
        if package_info:
            return package_info.name

        return None

    @classmethod
    def get_package_info(
        cls,
        package_id: str,
        distro_family: DistroFamily
    ) -> Optional[PackageInfo]:
        """
        Get complete package information.

        Args:
            package_id: Package identifier
            distro_family: Distribution family

        Returns:
            PackageInfo object or None
        """
        if package_id not in cls.PACKAGES:
            return None

        return cls.PACKAGES[package_id].get(distro_family)

    @classmethod
    def get_install_command(
        cls,
        package_manager: str,
        packages: List[str]
    ) -> Optional[str]:
        """
        Get installation command for a package manager.

        Args:
            package_manager: Package manager name (apt, dnf, etc.)
            packages: List of package names

        Returns:
            Installation command string or None
        """
        if package_manager not in cls.INSTALL_COMMANDS:
            return None

        if not packages:
            return None

        package_str = ' '.join(packages)
        template = cls.INSTALL_COMMANDS[package_manager]
        return template.format(packages=package_str)

    @classmethod
    def get_all_required_packages(
        cls,
        distro_family: DistroFamily
    ) -> List[str]:
        """
        Get all required packages for a distribution family.

        Args:
            distro_family: Distribution family

        Returns:
            List of package names
        """
        packages = []

        for package_id, families in cls.PACKAGES.items():
            if distro_family in families:
                package_info = families[distro_family]
                if package_info.required and not package_info.python_package:
                    packages.append(package_info.name)

        return packages

    @classmethod
    def get_all_packages(
        cls,
        distro_family: DistroFamily
    ) -> Dict[str, PackageInfo]:
        """
        Get all packages for a distribution family.

        Args:
            distro_family: Distribution family

        Returns:
            Dictionary of package_id to PackageInfo
        """
        packages = {}

        for package_id, families in cls.PACKAGES.items():
            if distro_family in families:
                packages[package_id] = families[distro_family]

        return packages

    @classmethod
    def get_python_packages(
        cls,
        distro_family: DistroFamily
    ) -> Dict[str, PackageInfo]:
        """
        Get Python packages for a distribution family.

        Args:
            distro_family: Distribution family

        Returns:
            Dictionary of package_id to PackageInfo
        """
        packages = {}

        for package_id, families in cls.PACKAGES.items():
            if distro_family in families:
                package_info = families[distro_family]
                if package_info.python_package:
                    packages[package_id] = package_info

        return packages

    @classmethod
    def get_compatibility_summary(cls) -> str:
        """
        Get summary of supported distributions.

        Returns:
            Formatted summary string
        """
        lines = ["Linux Distribution Compatibility Summary", ""]

        lines.append("Supported Distribution Families:")
        for family in DistroFamily:
            if family != DistroFamily.UNKNOWN:
                lines.append(f"  - {family.value.upper()}")

        lines.append("")
        lines.append("Package Manager Support:")
        for pm, cmd in cls.INSTALL_COMMANDS.items():
            lines.append(f"  - {pm.upper()}")

        return "\n".join(lines)


__all__ = [
    'CompatibilityMatrix',
    'DistroFamily',
    'PackageInfo',
]
