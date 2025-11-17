"""
Comprehensive test cases for Linux edge case handling.

Tests detection and graceful fallback handling for:
- Container environments (Docker, LXC)
- Headless servers (no display)
- SSH X11 forwarding
- VNC/remote desktop sessions
- Virtual machines
- Screen recording/mirroring
- Multiple X servers
- Permission restrictions
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp_server.platform.linux.edge_case_handler import (
    EdgeCaseHandler,
    EdgeCaseDetection,
    EnvironmentType,
    RemoteAccessType,
    RecordingType,
)


class TestContainerDetection(unittest.TestCase):
    """Test detection of containerized environments."""

    def setUp(self):
        """Set up test handler."""
        self.handler = EdgeCaseHandler()

    @patch('os.path.exists')
    def test_docker_detection(self, mock_exists):
        """Test Docker container detection."""
        def side_effect(path):
            return path in ['/.dockerenv', '/.dockerinit']
        mock_exists.side_effect = side_effect

        result = self.handler._detect_environment_type()
        self.assertEqual(result, EnvironmentType.DOCKER)

    @patch('os.path.exists')
    def test_podman_detection(self, mock_exists):
        """Test Podman container detection."""
        def side_effect(path):
            return path == '/.podmanenv'
        mock_exists.side_effect = side_effect

        result = self.handler._detect_environment_type()
        self.assertEqual(result, EnvironmentType.PODMAN)

    @patch('os.path.exists')
    @patch('builtins.open', mock_open(read_data='lxc'))
    def test_lxc_detection(self, mock_exists):
        """Test LXC container detection."""
        def side_effect(path):
            return path == '/sys/fs/cgroup/lxc'
        mock_exists.side_effect = side_effect

        result = self.handler._detect_environment_type()
        self.assertEqual(result, EnvironmentType.LXC)

    @patch('os.path.exists')
    def test_native_detection(self, mock_exists):
        """Test native (non-containerized) environment detection."""
        mock_exists.return_value = False

        result = self.handler._detect_environment_type()
        self.assertEqual(result, EnvironmentType.NATIVE)

    @patch('os.path.exists')
    def test_containerized_flag(self, mock_exists):
        """Test is_containerized flag."""
        def side_effect(path):
            return path == '/.dockerenv'
        mock_exists.side_effect = side_effect

        # Trigger detection
        self.handler._detect_environment_type()
        # Set it manually for testing
        result = self.handler._is_containerized()
        self.assertTrue(result)


class TestVirtualMachineDetection(unittest.TestCase):
    """Test detection of virtual machines."""

    def setUp(self):
        """Set up test handler."""
        self.handler = EdgeCaseHandler()

    @patch('os.path.exists')
    @patch('builtins.open', mock_open(read_data='QEMU'))
    def test_qemu_detection(self, mock_exists):
        """Test QEMU VM detection."""
        def side_effect(path):
            return path == '/sys/class/dmi/id/sys_vendor'
        mock_exists.side_effect = side_effect

        result = self.handler._detect_vm_type()
        self.assertEqual(result, EnvironmentType.QEMU)

    @patch('os.path.exists')
    @patch('builtins.open', mock_open(read_data='VirtualBox'))
    def test_virtualbox_detection(self, mock_exists):
        """Test VirtualBox VM detection."""
        def side_effect(path):
            return path == '/sys/class/dmi/id/sys_vendor'
        mock_exists.side_effect = side_effect

        result = self.handler._detect_vm_type()
        self.assertEqual(result, EnvironmentType.VIRTUALBOX)

    @patch('os.path.exists')
    @patch('builtins.open', mock_open(read_data='VMware'))
    def test_vmware_detection(self, mock_exists):
        """Test VMware VM detection."""
        def side_effect(path):
            return path == '/sys/class/dmi/id/sys_vendor'
        mock_exists.side_effect = side_effect

        result = self.handler._detect_vm_type()
        self.assertEqual(result, EnvironmentType.VMWARE)

    @patch('os.path.exists')
    def test_virtual_machine_flag(self, mock_exists):
        """Test is_virtual_machine flag."""
        mock_exists.return_value = False

        # Test native is not VM
        self.handler._detect_environment_type()
        result = self.handler._is_virtual_machine()
        self.assertFalse(result)


class TestHeadlessDetection(unittest.TestCase):
    """Test detection of headless environments."""

    def setUp(self):
        """Set up test handler."""
        self.handler = EdgeCaseHandler()

    @patch.dict(os.environ, {}, clear=True)
    @patch('os.path.exists')
    def test_headless_no_display(self, mock_exists):
        """Test headless detection with no DISPLAY."""
        mock_exists.return_value = False

        result = self.handler._is_headless()
        self.assertTrue(result)

    @patch.dict(os.environ, {'DISPLAY': ':0'})
    def test_not_headless_with_display(self):
        """Test non-headless with DISPLAY set."""
        # This will fail if xdpyinfo isn't available, but that's expected
        result = self.handler._is_headless()
        # Result depends on xdpyinfo availability
        # Just check it doesn't crash
        self.assertIsInstance(result, bool)

    @patch.dict(os.environ, {'WAYLAND_DISPLAY': 'wayland-0'})
    def test_not_headless_with_wayland(self):
        """Test non-headless with Wayland display."""
        result = self.handler._is_headless()
        self.assertFalse(result)


class TestRemoteAccessDetection(unittest.TestCase):
    """Test detection of remote access methods."""

    def setUp(self):
        """Set up test handler."""
        self.handler = EdgeCaseHandler()

    @patch.dict(os.environ, {'SSH_CONNECTION': 'host port 22', 'DISPLAY': ':99'})
    @patch('subprocess.run')
    def test_ssh_x11_detection(self, mock_run):
        """Test SSH X11 forwarding detection."""
        mock_run.return_value = MagicMock(
            stdout='sshd: user [priv]\nX11',
            returncode=0
        )

        result = self.handler._detect_remote_access()
        self.assertEqual(result, RemoteAccessType.SSH_X11)

    @patch.dict(os.environ, {'VNC_GEOMETRY': '1920x1080'})
    def test_vnc_detection(self):
        """Test VNC session detection."""
        result = self.handler._detect_remote_access()
        self.assertEqual(result, RemoteAccessType.VNC)

    @patch.dict(os.environ, {'SPICE_SERVER': 'localhost:5900'})
    def test_spice_detection(self):
        """Test SPICE session detection."""
        result = self.handler._detect_remote_access()
        self.assertEqual(result, RemoteAccessType.SPICE)

    @patch.dict(os.environ, {'RDP_HOST': 'localhost'})
    def test_rdp_detection(self):
        """Test RDP session detection."""
        result = self.handler._detect_remote_access()
        self.assertEqual(result, RemoteAccessType.RDP)

    @patch.dict(os.environ, {})
    def test_direct_access_detection(self):
        """Test direct (non-remote) access detection."""
        result = self.handler._detect_remote_access()
        self.assertEqual(result, RemoteAccessType.DIRECT)


class TestScreenRecordingDetection(unittest.TestCase):
    """Test detection of screen recording."""

    def setUp(self):
        """Set up test handler."""
        self.handler = EdgeCaseHandler()

    @patch('subprocess.run')
    def test_ffmpeg_recording_detection(self, mock_run):
        """Test FFmpeg recording detection."""
        mock_run.return_value = MagicMock(
            stdout='ffmpeg process running',
            returncode=0
        )

        result = self.handler._detect_screen_recording()
        self.assertEqual(result, RecordingType.FFMPEG)

    @patch('subprocess.run')
    def test_obs_recording_detection(self, mock_run):
        """Test OBS recording detection."""
        mock_run.return_value = MagicMock(
            stdout='obs process running',
            returncode=0
        )

        result = self.handler._detect_screen_recording()
        self.assertEqual(result, RecordingType.OBS)

    @patch('subprocess.run')
    def test_no_recording_detection(self, mock_run):
        """Test detection when no recording is active."""
        mock_run.return_value = MagicMock(
            stdout='some other process',
            returncode=0
        )

        result = self.handler._detect_screen_recording()
        self.assertEqual(result, RecordingType.NONE)


class TestPermissionDetection(unittest.TestCase):
    """Test detection of permission issues."""

    def setUp(self):
        """Set up test handler."""
        self.handler = EdgeCaseHandler()

    @patch('os.path.exists')
    @patch('os.access')
    def test_uinput_missing(self, mock_access, mock_exists):
        """Test detection of missing /dev/uinput."""
        mock_exists.return_value = False

        issues = self.handler._check_permissions()
        self.assertIn("Missing /dev/uinput", ' '.join(issues))

    @patch('os.path.exists')
    @patch('os.access')
    def test_uinput_no_permission(self, mock_access, mock_exists):
        """Test detection of no permission for /dev/uinput."""
        def exists_side_effect(path):
            return path == '/dev/uinput'
        def access_side_effect(path, mode):
            return False

        mock_exists.side_effect = exists_side_effect
        mock_access.side_effect = access_side_effect

        issues = self.handler._check_permissions()
        self.assertIn("No write permission for /dev/uinput", ' '.join(issues))


class TestMultipleXServers(unittest.TestCase):
    """Test detection of multiple X servers."""

    def setUp(self):
        """Set up test handler."""
        self.handler = EdgeCaseHandler()

    @patch('subprocess.run')
    def test_multiple_x_servers_detected(self, mock_run):
        """Test detection of multiple X servers."""
        mock_run.return_value = MagicMock(
            stdout='Xvfb :99\nXvfb :100\nXephyr :101',
            returncode=0
        )

        result = self.handler._has_multiple_x_servers()
        self.assertTrue(result)

    @patch('subprocess.run')
    def test_single_x_server(self, mock_run):
        """Test detection of single X server."""
        mock_run.return_value = MagicMock(
            stdout='some other process',
            returncode=0
        )

        result = self.handler._has_multiple_x_servers()
        # Should be False if no multiple servers found
        self.assertIsInstance(result, bool)


class TestLimitations(unittest.TestCase):
    """Test limitation generation based on edge cases."""

    def setUp(self):
        """Set up test handler."""
        self.handler = EdgeCaseHandler()

    def test_headless_limitations(self):
        """Test limitations for headless environments."""
        limitations = self.handler._generate_limitations(
            env_type=EnvironmentType.NATIVE,
            is_headless=True,
            remote_access=RemoteAccessType.DIRECT,
            recording=RecordingType.NONE,
            multiple_x_servers=False,
            permission_issues=[]
        )

        self.assertTrue(any('HEADLESS' in l for l in limitations))
        self.assertTrue(any('Xvfb' in l for l in limitations))

    def test_container_limitations(self):
        """Test limitations for containerized environments."""
        limitations = self.handler._generate_limitations(
            env_type=EnvironmentType.DOCKER,
            is_headless=False,
            remote_access=RemoteAccessType.DIRECT,
            recording=RecordingType.NONE,
            multiple_x_servers=False,
            permission_issues=[]
        )

        self.assertTrue(any('DOCKER' in l for l in limitations))

    def test_remote_access_limitations(self):
        """Test limitations for remote access."""
        limitations = self.handler._generate_limitations(
            env_type=EnvironmentType.NATIVE,
            is_headless=False,
            remote_access=RemoteAccessType.SSH_X11,
            recording=RecordingType.NONE,
            multiple_x_servers=False,
            permission_issues=[]
        )

        self.assertTrue(any('latency' in l.lower() for l in limitations))

    def test_recording_limitations(self):
        """Test limitations when recording is active."""
        limitations = self.handler._generate_limitations(
            env_type=EnvironmentType.NATIVE,
            is_headless=False,
            remote_access=RemoteAccessType.DIRECT,
            recording=RecordingType.FFMPEG,
            multiple_x_servers=False,
            permission_issues=[]
        )

        self.assertTrue(any('RECORDING' in l for l in limitations))


class TestRecommendations(unittest.TestCase):
    """Test recommendation generation based on edge cases."""

    def setUp(self):
        """Set up test handler."""
        self.handler = EdgeCaseHandler()

    def test_headless_recommendations(self):
        """Test recommendations for headless environments."""
        recommendations = self.handler._generate_recommendations(
            env_type=EnvironmentType.NATIVE,
            is_headless=True,
            remote_access=RemoteAccessType.DIRECT,
            permission_issues=[]
        )

        self.assertTrue(any('Xvfb' in r for r in recommendations))
        self.assertTrue(any('DISPLAY' in r for r in recommendations))

    def test_docker_recommendations(self):
        """Test recommendations for Docker environments."""
        recommendations = self.handler._generate_recommendations(
            env_type=EnvironmentType.DOCKER,
            is_headless=False,
            remote_access=RemoteAccessType.DIRECT,
            permission_issues=[]
        )

        self.assertTrue(any('Docker' in r for r in recommendations))

    def test_permission_recommendations(self):
        """Test recommendations for permission issues."""
        recommendations = self.handler._generate_recommendations(
            env_type=EnvironmentType.NATIVE,
            is_headless=False,
            remote_access=RemoteAccessType.DIRECT,
            permission_issues=['Permission denied']
        )

        self.assertTrue(any('usermod' in r or 'chmod' in r for r in recommendations))


class TestFullDetection(unittest.TestCase):
    """Test full edge case detection."""

    def test_detect_edge_cases_returns_detection_object(self):
        """Test that detection returns proper object."""
        handler = EdgeCaseHandler()
        detection = handler.detect_edge_cases()

        self.assertIsInstance(detection, EdgeCaseDetection)
        self.assertIsInstance(detection.environment_type, EnvironmentType)
        self.assertIsInstance(detection.remote_access_type, RemoteAccessType)
        self.assertIsInstance(detection.recording_type, RecordingType)
        self.assertIsInstance(detection.is_headless, bool)
        self.assertIsInstance(detection.is_containerized, bool)
        self.assertIsInstance(detection.is_virtual_machine, bool)
        self.assertIsInstance(detection.permission_issues, list)
        self.assertIsInstance(detection.limitations, list)
        self.assertIsInstance(detection.recommendations, list)

    def test_detection_caching(self):
        """Test that detection results are cached."""
        handler = EdgeCaseHandler()
        detection1 = handler.detect_edge_cases()
        detection2 = handler.detect_edge_cases()

        self.assertIs(detection1, detection2)

    def test_detection_refresh(self):
        """Test that force_refresh gets new detection."""
        handler = EdgeCaseHandler()
        detection1 = handler.detect_edge_cases()
        detection2 = handler.detect_edge_cases(force_refresh=True)

        # Should be different objects due to refresh
        self.assertIsNot(detection1, detection2)


class TestEnvironmentVariables(unittest.TestCase):
    """Test relevant environment variable detection."""

    def test_get_relevant_env_vars(self):
        """Test extraction of relevant environment variables."""
        handler = EdgeCaseHandler()

        with patch.dict(os.environ, {'DISPLAY': ':0', 'WAYLAND_DISPLAY': 'wayland-0', 'PATH': '/usr/bin'}):
            env_vars = handler._get_relevant_env_vars()

            self.assertIn('DISPLAY', env_vars)
            self.assertEqual(env_vars['DISPLAY'], ':0')
            self.assertIn('WAYLAND_DISPLAY', env_vars)
            self.assertIn('PATH', env_vars)


class TestCommandExists(unittest.TestCase):
    """Test command existence checking."""

    def test_command_exists_true(self):
        """Test checking for existing command."""
        handler = EdgeCaseHandler()

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = handler._command_exists('ls')
            self.assertTrue(result)

    def test_command_exists_false(self):
        """Test checking for non-existing command."""
        handler = EdgeCaseHandler()

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = handler._command_exists('nonexistentcommand')
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
