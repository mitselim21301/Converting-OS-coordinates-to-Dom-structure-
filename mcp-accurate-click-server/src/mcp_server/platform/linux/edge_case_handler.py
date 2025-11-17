"""
Linux Edge Case Handler - Detection and Graceful Fallback

Detects and handles edge cases for Linux input simulation:
- Container environments (Docker, LXC, Kubernetes)
- Headless servers (no display)
- SSH X11 forwarding
- VNC/Remote Desktop sessions
- Virtual machines
- Screen recording/mirroring
- Multiple X servers
- Permission restrictions

Provides detection methods and graceful fallbacks with documentation
of limitations in each scenario.
"""

import os
import subprocess
import logging
import sys
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)


class EnvironmentType(Enum):
    """Detected Linux environment types."""
    NATIVE = "native"
    DOCKER = "docker"
    PODMAN = "podman"
    LXC = "lxc"
    KUBERNETES = "kubernetes"
    QEMU = "qemu"
    VIRTUALBOX = "virtualbox"
    VMWARE = "vmware"
    XEN = "xen"
    HYPER_V = "hyper-v"
    KVM = "kvm"
    PARALLELS = "parallels"


class RemoteAccessType(Enum):
    """Types of remote access/display forwarding."""
    DIRECT = "direct"
    SSH_X11 = "ssh_x11"
    VNC = "vnc"
    SPICE = "spice"
    XVFB = "xvfb"
    XWAYLAND = "xwayland"
    RDP = "rdp"
    CHROME_REMOTE_DESKTOP = "chrome_remote_desktop"
    XEPHYR = "xephyr"
    WAYLAND_REMOTING = "wayland_remoting"


class RecordingType(Enum):
    """Types of screen recording/mirroring."""
    NONE = "none"
    SCREEN_CAPTURE = "screen_capture"
    WAYLAND_RECORDER = "wayland_recorder"
    FFMPEG = "ffmpeg"
    OBS = "obs"
    SIMPLESCREENRECORDER = "simplescreenrecorder"


@dataclass
class EdgeCaseDetection:
    """Result of edge case detection."""
    environment_type: EnvironmentType
    is_headless: bool
    is_containerized: bool
    is_virtual_machine: bool
    remote_access_type: RemoteAccessType
    recording_type: RecordingType
    multiple_x_servers: bool
    permission_issues: List[str]
    environment_vars: Dict[str, str]
    limitations: List[str]
    recommendations: List[str]


class EdgeCaseHandler:
    """Detects and handles Linux edge cases."""

    # Container detection files
    CONTAINER_MARKERS = {
        'docker': [
            '/.dockerenv',
            '/.dockerinit',
            '/run/docker',
            '/docker',
        ],
        'podman': [
            '/.podmanenv',
            '/run/podman',
        ],
        'lxc': [
            '/sys/fs/cgroup/lxc',
            '/proc/sys/kernel/osrelease',  # Contains 'lxc'
        ],
        'kubernetes': [
            '/var/run/secrets/kubernetes.io',
            '/etc/kubernetes',
        ],
    }

    # Virtual machine detection files
    VM_MARKERS = {
        'qemu': [
            '/sys/class/dmi/id/sys_vendor',  # Contains 'QEMU'
            '/proc/cpuinfo',  # Contains 'qemu'
        ],
        'virtualbox': [
            '/sys/class/dmi/id/sys_vendor',  # Contains 'VirtualBox'
            '/proc/cpuinfo',  # Contains 'vbox'
        ],
        'vmware': [
            '/sys/class/dmi/id/sys_vendor',  # Contains 'VMware'
            '/proc/cpuinfo',  # Contains 'VMX'
        ],
        'xen': [
            '/proc/xen',
            '/sys/hypervisor/type',  # Contains 'xen'
        ],
        'kvm': [
            '/proc/cpuinfo',  # Contains 'kvm'
        ],
        'hyper-v': [
            '/sys/class/dmi/id/sys_vendor',  # Contains 'Microsoft'
            '/proc/cpuinfo',  # Contains 'hyperv'
        ],
        'parallels': [
            '/sys/class/dmi/id/sys_vendor',  # Contains 'Parallels'
        ],
    }

    def __init__(self):
        """Initialize edge case handler."""
        self._detection_cache: Optional[EdgeCaseDetection] = None
        logger.info("Linux Edge Case Handler initialized")

    def detect_edge_cases(self, force_refresh: bool = False) -> EdgeCaseDetection:
        """
        Detect all edge cases in current environment.

        Args:
            force_refresh: Force re-detection even if cached

        Returns:
            EdgeCaseDetection with all detected edge cases
        """
        if not force_refresh and self._detection_cache:
            return self._detection_cache

        logger.info("Detecting Linux edge cases...")

        # Get environment info
        env_vars = self._get_relevant_env_vars()
        environment_type = self._detect_environment_type()
        is_containerized = self._is_containerized()
        is_virtual_machine = self._is_virtual_machine()
        is_headless = self._is_headless()
        remote_access_type = self._detect_remote_access()
        recording_type = self._detect_screen_recording()
        multiple_x_servers = self._has_multiple_x_servers()
        permission_issues = self._check_permissions()

        # Generate limitations and recommendations
        limitations = self._generate_limitations(
            environment_type, is_headless, remote_access_type,
            recording_type, multiple_x_servers, permission_issues
        )
        recommendations = self._generate_recommendations(
            environment_type, is_headless, remote_access_type,
            permission_issues
        )

        detection = EdgeCaseDetection(
            environment_type=environment_type,
            is_headless=is_headless,
            is_containerized=is_containerized,
            is_virtual_machine=is_virtual_machine,
            remote_access_type=remote_access_type,
            recording_type=recording_type,
            multiple_x_servers=multiple_x_servers,
            permission_issues=permission_issues,
            environment_vars=env_vars,
            limitations=limitations,
            recommendations=recommendations
        )

        # Cache the result
        self._detection_cache = detection

        # Log findings
        self._log_detection_results(detection)

        return detection

    def _get_relevant_env_vars(self) -> Dict[str, str]:
        """Get relevant environment variables."""
        relevant_vars = [
            'DISPLAY', 'WAYLAND_DISPLAY', 'XDG_SESSION_TYPE',
            'XDG_VTNR', 'XDG_SESSION_ID', 'XDG_RUNTIME_DIR',
            'DOCKER_HOST', 'SSH_CONNECTION', 'SSH_CLIENT',
            'VNC_GEOMETRY', 'SPICE_SERVER', 'RDP_HOST',
            'GDK_SCALE', 'QT_SCALE_FACTOR',
            'TERM', 'TERM_PROGRAM', 'PATH'
        ]

        return {var: os.environ.get(var, '') for var in relevant_vars if os.environ.get(var)}

    def _detect_environment_type(self) -> EnvironmentType:
        """Detect the virtualization/containerization environment."""
        # Check for containers first
        if self._check_container_marker('docker'):
            return EnvironmentType.DOCKER
        if self._check_container_marker('podman'):
            return EnvironmentType.PODMAN
        if self._check_container_marker('lxc'):
            return EnvironmentType.LXC
        if self._check_container_marker('kubernetes'):
            return EnvironmentType.KUBERNETES

        # Check for VMs
        vm_type = self._detect_vm_type()
        if vm_type:
            return vm_type

        return EnvironmentType.NATIVE

    def _check_container_marker(self, container_type: str) -> bool:
        """Check if specific container markers exist."""
        markers = self.CONTAINER_MARKERS.get(container_type, [])

        for marker in markers:
            if marker.startswith('/proc/') or marker.startswith('/sys/'):
                # File content check needed
                try:
                    if os.path.exists(marker):
                        with open(marker, 'r') as f:
                            content = f.read().lower()
                            if container_type.lower() in content:
                                logger.debug(f"Detected {container_type} via {marker}")
                                return True
                except (IOError, OSError):
                    pass
            else:
                # Simple file existence check
                if os.path.exists(marker):
                    logger.debug(f"Detected {container_type} via {marker}")
                    return True

        return False

    def _detect_vm_type(self) -> Optional[EnvironmentType]:
        """Detect if running in a VM and which type."""
        for vm_type, markers in self.VM_MARKERS.items():
            for marker in markers:
                try:
                    if os.path.exists(marker):
                        with open(marker, 'r') as f:
                            content = f.read().lower()
                            if vm_type.lower() in content or (
                                vm_type == 'vmware' and 'vmx' in content
                            ):
                                logger.debug(f"Detected VM: {vm_type}")
                                return EnvironmentType[vm_type.upper().replace('-', '_')]
                except (IOError, OSError):
                    pass

        # Check via dmidecode if available
        try:
            result = subprocess.run(
                ['sudo', 'dmidecode', '-s', 'system-manufacturer'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                output = result.stdout.lower()
                if 'virtualbox' in output:
                    return EnvironmentType.VIRTUALBOX
                if 'vmware' in output:
                    return EnvironmentType.VMWARE
                if 'microsoft' in output or 'hyper-v' in output:
                    return EnvironmentType.HYPER_V
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            pass

        return None

    def _is_containerized(self) -> bool:
        """Check if running in container."""
        env_type = self._detect_environment_type()
        return env_type in (
            EnvironmentType.DOCKER, EnvironmentType.PODMAN,
            EnvironmentType.LXC, EnvironmentType.KUBERNETES
        )

    def _is_virtual_machine(self) -> bool:
        """Check if running in VM."""
        env_type = self._detect_environment_type()
        return env_type in (
            EnvironmentType.QEMU, EnvironmentType.VIRTUALBOX,
            EnvironmentType.VMWARE, EnvironmentType.XEN,
            EnvironmentType.KVM, EnvironmentType.HYPER_V,
            EnvironmentType.PARALLELS
        )

    def _is_headless(self) -> bool:
        """Check if running headless (no display)."""
        # Check for display server
        display = os.environ.get('DISPLAY')
        wayland_display = os.environ.get('WAYLAND_DISPLAY')
        xvfb_display = os.environ.get('XVFB_DISPLAY')

        if display or wayland_display or xvfb_display:
            return False

        # Check if X11 is accessible
        try:
            result = subprocess.run(
                ['xdpyinfo'],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                return False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        logger.warning("Headless display detected")
        return True

    def _detect_remote_access(self) -> RemoteAccessType:
        """Detect remote access/display forwarding type."""
        # Check SSH X11 forwarding
        if os.environ.get('SSH_CONNECTION') and os.environ.get('DISPLAY'):
            # Verify it's actually X11 forwarding
            try:
                result = subprocess.run(
                    ['ps', 'aux'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if 'sshd' in result.stdout and 'X11' in result.stdout:
                    logger.info("Detected SSH X11 forwarding")
                    return RemoteAccessType.SSH_X11
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        # Check VNC
        if os.environ.get('VNC_GEOMETRY'):
            logger.info("Detected VNC session")
            return RemoteAccessType.VNC
        if self._command_exists('vncserver') or self._command_exists('vncviewer'):
            return RemoteAccessType.VNC

        # Check SPICE
        if os.environ.get('SPICE_SERVER'):
            logger.info("Detected SPICE session")
            return RemoteAccessType.SPICE

        # Check RDP
        if os.environ.get('RDP_HOST'):
            logger.info("Detected RDP session")
            return RemoteAccessType.RDP

        # Check Xvfb
        if 'Xvfb' in self._get_x_server_info():
            logger.info("Detected Xvfb")
            return RemoteAccessType.XVFB

        # Check Xwayland
        if os.environ.get('WAYLAND_DISPLAY') and os.environ.get('DISPLAY'):
            logger.info("Detected Xwayland")
            return RemoteAccessType.XWAYLAND

        # Check Chrome Remote Desktop
        if os.path.exists(os.path.expanduser('~/.config/chrome-remote-desktop')):
            logger.info("Detected Chrome Remote Desktop")
            return RemoteAccessType.CHROME_REMOTE_DESKTOP

        return RemoteAccessType.DIRECT

    def _detect_screen_recording(self) -> RecordingType:
        """Detect if screen recording/mirroring is active."""
        try:
            # Check running processes
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=2
            )
            output = result.stdout.lower()

            if 'ffmpeg' in output:
                logger.debug("ffmpeg recording detected")
                return RecordingType.FFMPEG
            if 'obs' in output:
                logger.debug("OBS recording detected")
                return RecordingType.OBS
            if 'simplescreenrecorder' in output:
                logger.debug("SimpleScreenRecorder detected")
                return RecordingType.SIMPLESCREENRECORDER
            if 'wl-screenrec' in output or 'wf-recorder' in output:
                logger.debug("Wayland screen recorder detected")
                return RecordingType.WAYLAND_RECORDER
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return RecordingType.NONE

    def _has_multiple_x_servers(self) -> bool:
        """Check if multiple X servers are running."""
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=2
            )

            x_server_count = result.stdout.count('Xvfb') + result.stdout.count('Xephyr') + result.stdout.count('X ')
            if x_server_count > 1:
                logger.warning(f"Multiple X servers detected: {x_server_count}")
                return True

            # Check DISPLAY variable for multiple displays
            display_nums = set()
            if os.environ.get('DISPLAY'):
                match = re.search(r':(\d+)', os.environ.get('DISPLAY', ''))
                if match:
                    display_nums.add(int(match.group(1)))

            return len(display_nums) > 1
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return False

    def _check_permissions(self) -> List[str]:
        """Check for permission issues."""
        issues = []

        # Check /dev/input access
        try:
            result = subprocess.run(
                ['ls', '-l', '/dev/input/'],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                output = result.stdout.decode('utf-8')
                if 'drwxr' in output or 'cr--' in output:
                    if not os.access('/dev/input/mice', os.R_OK):
                        issues.append("No read permission for /dev/input/mice")
                        logger.warning("Permission denied: /dev/input/mice")
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

        # Check /dev/uinput access
        if not os.path.exists('/dev/uinput'):
            issues.append("Missing /dev/uinput (kernel module not loaded)")
            logger.warning("Missing /dev/uinput")
        elif not os.access('/dev/uinput', os.W_OK):
            issues.append("No write permission for /dev/uinput")
            logger.warning("Permission denied: /dev/uinput")

        # Check X11 socket access
        try:
            display = os.environ.get('DISPLAY', ':0')
            if display:
                socket_path = os.path.expanduser(f'~/.X11-unix/{display}')
                if os.path.exists(socket_path) and not os.access(socket_path, os.R_OK | os.W_OK):
                    issues.append(f"No permission for {socket_path}")
        except Exception:
            pass

        return issues

    def _get_x_server_info(self) -> str:
        """Get X server information."""
        try:
            result = subprocess.run(
                ['xdpyinfo'],
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""

    def _command_exists(self, cmd: str) -> bool:
        """Check if command exists."""
        try:
            subprocess.run(
                ['which', cmd],
                capture_output=True,
                timeout=1,
                check=True
            )
            return True
        except Exception:
            return False

    def _generate_limitations(
        self,
        env_type: EnvironmentType,
        is_headless: bool,
        remote_access: RemoteAccessType,
        recording: RecordingType,
        multiple_x_servers: bool,
        permission_issues: List[str]
    ) -> List[str]:
        """Generate list of limitations based on detected edge cases."""
        limitations = []

        if is_headless:
            limitations.append(
                "HEADLESS: No display available - X11 input simulation will not work. "
                "Use Xvfb or similar virtual display."
            )

        if env_type in (EnvironmentType.DOCKER, EnvironmentType.PODMAN):
            limitations.append(
                f"{env_type.value.upper()}: Limited display access. "
                "Ensure --privileged flag or X11 socket mounting."
            )

        if env_type == EnvironmentType.KUBERNETES:
            limitations.append(
                "KUBERNETES: No persistent display. Pod may not have UI access. "
                "Use sidecar container with display server."
            )

        if remote_access in (RemoteAccessType.SSH_X11, RemoteAccessType.VNC):
            limitations.append(
                f"{remote_access.value.upper()}: Remote display may have latency. "
                "Input timing should account for network delays."
            )

        if recording != RecordingType.NONE:
            limitations.append(
                f"RECORDING ACTIVE ({recording.value}): Input simulation may be captured. "
                "Performance may be degraded."
            )

        if multiple_x_servers:
            limitations.append(
                "MULTIPLE X SERVERS: Coordinate translation may fail if not on primary display. "
                "Verify correct DISPLAY variable."
            )

        for issue in permission_issues:
            limitations.append(f"PERMISSION: {issue}")

        return limitations

    def _generate_recommendations(
        self,
        env_type: EnvironmentType,
        is_headless: bool,
        remote_access: RemoteAccessType,
        permission_issues: List[str]
    ) -> List[str]:
        """Generate recommendations based on detected edge cases."""
        recommendations = []

        if is_headless:
            recommendations.append(
                "Install and start Xvfb: Xvfb :99 -screen 0 1920x1080x24 &"
            )
            recommendations.append("Set DISPLAY=:99 before running")

        if env_type == EnvironmentType.DOCKER:
            recommendations.append(
                "Use Docker flags: -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix"
            )
            recommendations.append("Or use --privileged flag (less secure)")

        if env_type == EnvironmentType.KUBERNETES:
            recommendations.append(
                "Deploy X11 server as sidecar or init container"
            )
            recommendations.append("Use host network: hostNetwork: true")

        if remote_access == RemoteAccessType.SSH_X11:
            recommendations.append(
                "Ensure SSH X11 forwarding is enabled on server: X11Forwarding yes"
            )
            recommendations.append("Use ssh -X or ssh -Y flag when connecting")

        if remote_access == RemoteAccessType.VNC:
            recommendations.append(
                "Increase input simulation delays to account for network latency"
            )

        if permission_issues:
            recommendations.append(
                "Run with: sudo usermod -a -G input $USER"
            )
            recommendations.append(
                "Or: sudo chmod 666 /dev/uinput /dev/input/*"
            )

        return recommendations

    def _log_detection_results(self, detection: EdgeCaseDetection) -> None:
        """Log detection results."""
        logger.info(f"Environment Type: {detection.environment_type.value}")
        logger.info(f"Headless: {detection.is_headless}")
        logger.info(f"Containerized: {detection.is_containerized}")
        logger.info(f"Virtual Machine: {detection.is_virtual_machine}")
        logger.info(f"Remote Access: {detection.remote_access_type.value}")
        logger.info(f"Screen Recording: {detection.recording_type.value}")
        logger.info(f"Multiple X Servers: {detection.multiple_x_servers}")

        if detection.permission_issues:
            logger.warning(f"Permission Issues: {detection.permission_issues}")

        if detection.limitations:
            logger.warning("Detected Limitations:")
            for limitation in detection.limitations:
                logger.warning(f"  - {limitation}")


# Singleton instance
_handler: Optional[EdgeCaseHandler] = None


def get_edge_case_handler() -> EdgeCaseHandler:
    """Get singleton EdgeCaseHandler instance."""
    global _handler
    if _handler is None:
        _handler = EdgeCaseHandler()
    return _handler


__all__ = [
    'EdgeCaseHandler',
    'EdgeCaseDetection',
    'EnvironmentType',
    'RemoteAccessType',
    'RecordingType',
    'get_edge_case_handler',
]
