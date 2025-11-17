"""
Linux Window Manager - Browser Window Tracking for X11 and Wayland

Handles:
- Browser window detection and tracking on X11 and Wayland
- Window positioning and bounds
- Client area vs non-client area (window decorations)
- Window-to-screen coordinate conversion
- Multi-monitor window tracking
- Support for various window managers (GNOME, KDE, i3, Sway, etc.)

Implementation:
- Primary: python-xlib for X11 native window management
- Fallback: subprocess calls to wmctrl/xdotool/xwininfo
- Wayland: D-Bus and compositor-specific APIs (limited capabilities)
- Process detection: /proc/{pid}/cmdline parsing
"""

import os
import re
import subprocess
import logging
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path

# Import edge case handler
try:
    from .edge_case_handler import get_edge_case_handler
    EDGE_CASE_HANDLER_AVAILABLE = True
except ImportError:
    EDGE_CASE_HANDLER_AVAILABLE = False

logger = logging.getLogger(__name__)

# Try to import X11 libraries
try:
    from Xlib import X, display, Xatom, error as xerror
    from Xlib.protocol import request
    XLIB_AVAILABLE = True
except ImportError:
    XLIB_AVAILABLE = False
    logger.warning("python-xlib not available. Falling back to subprocess methods.")

# Try to import psutil for process information
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available. Process detection will be limited.")

# Import base classes
from mcp_server.platform.base import (
    PlatformWindowManager,
    WindowInfo,
)


class LinuxWindowManager(PlatformWindowManager):
    """
    Manages browser window detection and tracking on Linux.

    Supports both X11 and Wayland display servers with multiple fallback methods.
    """

    # Browser process names (lowercase)
    BROWSER_PROCESSES = {
        'chrome': 'Chrome',
        'chromium': 'Chromium',
        'chromium-browser': 'Chromium',
        'google-chrome': 'Chrome',
        'google-chrome-stable': 'Chrome',
        'google-chrome-beta': 'Chrome Beta',
        'google-chrome-unstable': 'Chrome Dev',
        'firefox': 'Firefox',
        'firefox-esr': 'Firefox ESR',
        'msedge': 'Edge',
        'microsoft-edge': 'Edge',
        'microsoft-edge-stable': 'Edge',
        'microsoft-edge-beta': 'Edge Beta',
        'microsoft-edge-dev': 'Edge Dev',
        'brave': 'Brave',
        'brave-browser': 'Brave',
        'opera': 'Opera',
        'vivaldi': 'Vivaldi',
        'vivaldi-stable': 'Vivaldi',
        'epiphany': 'GNOME Web',
        'epiphany-browser': 'GNOME Web',
        'konqueror': 'Konqueror',
        'midori': 'Midori',
        'qutebrowser': 'qutebrowser',
        'falkon': 'Falkon',
    }

    # Browser WM_CLASS values (class name or instance name)
    BROWSER_WM_CLASSES = [
        'chrome',
        'chromium',
        'chromium-browser',
        'google-chrome',
        'firefox',
        'firefox-esr',
        'navigator',  # Firefox Navigator
        'msedge',
        'microsoft-edge',
        'brave-browser',
        'brave',
        'opera',
        'vivaldi',
        'epiphany',
        'konqueror',
        'midori',
        'qutebrowser',
        'falkon',
    ]

    # X11 Atoms we need to query
    X11_ATOMS = [
        '_NET_CLIENT_LIST',
        '_NET_ACTIVE_WINDOW',
        '_NET_WM_NAME',
        '_NET_WM_VISIBLE_NAME',
        'WM_NAME',
        'WM_CLASS',
        '_NET_WM_PID',
        '_NET_WM_STATE',
        '_NET_WM_STATE_HIDDEN',
        '_NET_WM_STATE_MAXIMIZED_VERT',
        '_NET_WM_STATE_MAXIMIZED_HORZ',
        '_NET_FRAME_EXTENTS',
        '_GTK_FRAME_EXTENTS',
    ]

    def __init__(self):
        """Initialize the Linux window manager."""
        self.display_type = self._detect_display_server()
        self.x_display = None
        self.x_root = None
        self.x_atoms = {}
        self._edge_case_detection = None

        # Check for edge cases
        if EDGE_CASE_HANDLER_AVAILABLE:
            try:
                edge_handler = get_edge_case_handler()
                self._edge_case_detection = edge_handler.detect_edge_cases()

                if self._edge_case_detection.is_headless:
                    logger.warning("Window Manager: Headless environment - window detection will be limited")

                if self._edge_case_detection.is_containerized:
                    logger.info(f"Window Manager: Running in container ({self._edge_case_detection.environment_type.value})")

                if self._edge_case_detection.permission_issues:
                    logger.warning(f"Window Manager: Permission issues: {self._edge_case_detection.permission_issues}")

            except Exception as e:
                logger.debug(f"Edge case detection failed: {e}")

        # Initialize X11 if available and we're on X11
        if self.display_type == 'x11' and XLIB_AVAILABLE:
            try:
                self.x_display = display.Display()
                self.x_root = self.x_display.screen().root
                self._cache_atoms()
                logger.info("Initialized X11 window manager with python-xlib")
            except Exception as e:
                logger.warning(f"Failed to initialize X11 display: {e}. Falling back to subprocess.")
                self.x_display = None

        # Check availability of command-line tools
        self.has_wmctrl = self._check_command('wmctrl')
        self.has_xdotool = self._check_command('xdotool')
        self.has_xwininfo = self._check_command('xwininfo')
        self.has_xprop = self._check_command('xprop')

        if self.display_type == 'x11':
            if not XLIB_AVAILABLE and not (self.has_wmctrl or self.has_xdotool):
                logger.error("No X11 tools available! Install python-xlib, wmctrl, or xdotool.")
        elif self.display_type == 'wayland':
            logger.warning("Wayland detected. Window management capabilities are limited.")

    def _detect_display_server(self) -> str:
        """
        Detect whether we're running on X11 or Wayland.

        Returns:
            'x11', 'wayland', or 'unknown'
        """
        # Check XDG_SESSION_TYPE
        session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        if session_type in ('x11', 'wayland'):
            return session_type

        # Check WAYLAND_DISPLAY
        if os.environ.get('WAYLAND_DISPLAY'):
            return 'wayland'

        # Check DISPLAY (X11)
        if os.environ.get('DISPLAY'):
            return 'x11'

        return 'unknown'

    def _check_command(self, cmd: str) -> bool:
        """Check if a command is available in PATH."""
        try:
            subprocess.run(
                ['which', cmd],
                capture_output=True,
                check=True,
                timeout=1
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _cache_atoms(self) -> None:
        """Cache X11 atoms for faster lookups."""
        if not self.x_display:
            return

        for atom_name in self.X11_ATOMS:
            try:
                self.x_atoms[atom_name] = self.x_display.intern_atom(atom_name)
            except Exception as e:
                logger.debug(f"Failed to intern atom {atom_name}: {e}")

    def _get_window_property(self, window: Any, atom_name: str, prop_type: Any = None) -> Optional[Any]:
        """
        Get a window property using X11.

        Args:
            window: X11 window object
            atom_name: Atom name (e.g., '_NET_WM_NAME')
            prop_type: Property type (default: STRING)

        Returns:
            Property value or None
        """
        if not self.x_display or atom_name not in self.x_atoms:
            return None

        try:
            # Use Xatom.STRING as default if prop_type not specified and Xatom is available
            if prop_type is None and XLIB_AVAILABLE:
                prop_type = Xatom.STRING

            atom = self.x_atoms[atom_name]
            prop = window.get_full_property(atom, prop_type)
            if prop:
                return prop.value
        except Exception as e:
            logger.debug(f"Failed to get property {atom_name}: {e}")

        return None

    def _parse_window_id(self, window_id_str: str) -> Optional[int]:
        """
        Parse window ID from string (handles hex format).

        Args:
            window_id_str: Window ID as string (e.g., '0x1234567')

        Returns:
            Window ID as integer or None
        """
        try:
            # Remove whitespace
            window_id_str = window_id_str.strip()

            # Handle hex format (0x...)
            if window_id_str.startswith('0x'):
                return int(window_id_str, 16)
            else:
                return int(window_id_str)
        except (ValueError, AttributeError):
            return None

    def _get_process_info(self, pid: int) -> Dict[str, Any]:
        """
        Get process information from PID.

        Args:
            pid: Process ID

        Returns:
            Dictionary with process info
        """
        info = {
            'name': None,
            'cmdline': None,
            'exe': None,
        }

        # Try psutil first (most reliable)
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process(pid)
                info['name'] = process.name().lower()
                info['cmdline'] = ' '.join(process.cmdline())
                info['exe'] = process.exe()
                return info
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Fallback: Read /proc/{pid}/ directly
        try:
            # Read cmdline
            cmdline_path = Path(f'/proc/{pid}/cmdline')
            if cmdline_path.exists():
                cmdline = cmdline_path.read_text()
                # cmdline is null-separated
                cmdline_parts = cmdline.split('\x00')
                cmdline_parts = [p for p in cmdline_parts if p]

                if cmdline_parts:
                    info['cmdline'] = ' '.join(cmdline_parts)
                    # Extract process name from first argument
                    exe_path = cmdline_parts[0]
                    info['name'] = Path(exe_path).name.lower()
                    info['exe'] = exe_path

        except (IOError, OSError) as e:
            logger.debug(f"Failed to read process info for PID {pid}: {e}")

        return info

    def _is_browser_process_name(self, process_name: str) -> bool:
        """
        Check if process name matches a known browser.

        Args:
            process_name: Process name (lowercase)

        Returns:
            True if it's a browser process
        """
        if not process_name:
            return False

        process_name = process_name.lower()

        # Exact match
        if process_name in self.BROWSER_PROCESSES:
            return True

        # Partial match (e.g., 'chrome' in 'chrome-1234')
        for browser_name in self.BROWSER_PROCESSES.keys():
            if browser_name in process_name:
                return True

        return False

    def _is_browser_wm_class(self, wm_class: str) -> bool:
        """
        Check if WM_CLASS matches a known browser.

        Args:
            wm_class: WM_CLASS value (lowercase)

        Returns:
            True if it's a browser class
        """
        if not wm_class:
            return False

        wm_class = wm_class.lower()

        for browser_class in self.BROWSER_WM_CLASSES:
            if browser_class in wm_class:
                return True

        return False

    # ==================== X11 Native Methods ====================

    def _get_window_info_x11(self, window_id: int) -> Optional[WindowInfo]:
        """
        Get window information using X11 (python-xlib).

        Args:
            window_id: X11 window ID

        Returns:
            WindowInfo object or None
        """
        if not self.x_display:
            return None

        try:
            # Create window object
            window = self.x_display.create_resource_object('window', window_id)

            # Get window attributes
            try:
                attrs = window.get_attributes()
                is_visible = (attrs.map_state == X.IsViewable)
            except xerror.BadWindow:
                return None

            # Get window title
            title = None
            # Try _NET_WM_NAME first (UTF-8)
            net_wm_name = self._get_window_property(window, '_NET_WM_NAME', self.x_display.intern_atom('UTF8_STRING'))
            if net_wm_name:
                try:
                    title = net_wm_name.decode('utf-8') if isinstance(net_wm_name, bytes) else str(net_wm_name)
                except:
                    pass

            # Fallback to WM_NAME
            if not title:
                wm_name = self._get_window_property(window, 'WM_NAME')
                if wm_name:
                    try:
                        title = wm_name.decode('utf-8') if isinstance(wm_name, bytes) else str(wm_name)
                    except:
                        title = str(wm_name)

            if not title:
                title = ""

            # Get WM_CLASS
            wm_class_prop = window.get_wm_class()
            class_name = ""
            if wm_class_prop:
                # WM_CLASS returns (instance, class)
                class_name = wm_class_prop[1] if len(wm_class_prop) > 1 else wm_class_prop[0]

            # Get PID
            pid_prop = self._get_window_property(window, '_NET_WM_PID', Xatom.CARDINAL)
            process_id = 0
            if pid_prop:
                process_id = pid_prop[0] if isinstance(pid_prop, (list, tuple)) else int(pid_prop)

            # Get geometry
            try:
                geom = window.get_geometry()
                # Translate to root window coordinates
                coords = window.translate_coords(self.x_root, 0, 0)

                window_rect = (
                    coords.x,
                    coords.y,
                    coords.x + geom.width,
                    coords.y + geom.height
                )
            except xerror.BadWindow:
                return None

            # Get frame extents (window decorations)
            frame_extents = self._get_window_property(window, '_NET_FRAME_EXTENTS', Xatom.CARDINAL)
            if not frame_extents:
                frame_extents = self._get_window_property(window, '_GTK_FRAME_EXTENTS', Xatom.CARDINAL)

            # Frame extents: [left, right, top, bottom]
            if frame_extents and len(frame_extents) >= 4:
                left_border = frame_extents[0]
                right_border = frame_extents[1]
                top_border = frame_extents[2]
                bottom_border = frame_extents[3]

                # Client rect excludes decorations
                client_rect = (
                    window_rect[0] + left_border,
                    window_rect[1] + top_border,
                    window_rect[2] - right_border,
                    window_rect[3] - bottom_border
                )
            else:
                # No frame extents available, assume client = window
                client_rect = window_rect

            # Get window state
            wm_state = self._get_window_property(window, '_NET_WM_STATE', Xatom.ATOM)
            is_minimized = False
            is_maximized = False

            if wm_state:
                state_atoms = wm_state if isinstance(wm_state, (list, tuple)) else [wm_state]
                hidden_atom = self.x_atoms.get('_NET_WM_STATE_HIDDEN')
                max_vert_atom = self.x_atoms.get('_NET_WM_STATE_MAXIMIZED_VERT')
                max_horz_atom = self.x_atoms.get('_NET_WM_STATE_MAXIMIZED_HORZ')

                is_minimized = hidden_atom in state_atoms
                is_maximized = (max_vert_atom in state_atoms) and (max_horz_atom in state_atoms)

            return WindowInfo(
                handle=window_id,
                title=title,
                class_name=class_name,
                process_id=process_id,
                thread_id=0,  # Linux doesn't expose thread IDs easily
                is_visible=is_visible,
                is_minimized=is_minimized,
                is_maximized=is_maximized,
                window_rect=window_rect,
                client_rect=client_rect,
                monitor_handle=0,  # Will be determined by monitor detection
            )

        except Exception as e:
            logger.debug(f"Failed to get X11 window info for {window_id}: {e}")
            return None

    def _list_windows_x11(self) -> List[int]:
        """
        List all windows using X11.

        Returns:
            List of window IDs
        """
        if not self.x_display:
            return []

        try:
            # Get client list from root window
            client_list = self._get_window_property(
                self.x_root,
                '_NET_CLIENT_LIST',
                Xatom.WINDOW
            )

            if client_list:
                return list(client_list)

        except Exception as e:
            logger.debug(f"Failed to list X11 windows: {e}")

        return []

    def _get_active_window_x11(self) -> Optional[int]:
        """
        Get active window ID using X11.

        Returns:
            Window ID or None
        """
        if not self.x_display:
            return None

        try:
            active_window = self._get_window_property(
                self.x_root,
                '_NET_ACTIVE_WINDOW',
                Xatom.WINDOW
            )

            if active_window:
                return active_window[0] if isinstance(active_window, (list, tuple)) else int(active_window)

        except Exception as e:
            logger.debug(f"Failed to get active X11 window: {e}")

        return None

    # ==================== Subprocess Fallback Methods ====================

    def _get_window_info_wmctrl(self, window_id: int) -> Optional[WindowInfo]:
        """
        Get window information using wmctrl.

        Args:
            window_id: Window ID

        Returns:
            WindowInfo object or None
        """
        if not self.has_wmctrl:
            return None

        try:
            # Get window list with geometry
            result = subprocess.run(
                ['wmctrl', '-lGpx'],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode != 0:
                return None

            # Parse output
            window_id_hex = f'0x{window_id:08x}'

            for line in result.stdout.strip().split('\n'):
                parts = line.split(None, 8)
                if len(parts) < 9:
                    continue

                wid, desktop, pid, x, y, w, h, wm_class = parts[:8]
                title = parts[8] if len(parts) > 8 else ""

                if wid.lower() == window_id_hex.lower() or wid == str(window_id):
                    process_id = int(pid)

                    # Convert to integers
                    x, y, w, h = int(x), int(y), int(w), int(h)

                    window_rect = (x, y, x + w, y + h)

                    # Approximate client rect (no decoration info from wmctrl)
                    # Assume standard decorations: 2px sides, 30px top
                    client_rect = (x + 2, y + 30, x + w - 2, y + h - 2)

                    return WindowInfo(
                        handle=window_id,
                        title=title,
                        class_name=wm_class,
                        process_id=process_id,
                        thread_id=0,
                        is_visible=True,  # wmctrl only shows visible windows
                        is_minimized=False,
                        is_maximized=False,  # Can't determine from wmctrl -lG
                        window_rect=window_rect,
                        client_rect=client_rect,
                        monitor_handle=0,
                    )

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError) as e:
            logger.debug(f"Failed to get window info via wmctrl: {e}")

        return None

    def _get_window_info_xwininfo(self, window_id: int) -> Optional[WindowInfo]:
        """
        Get window information using xwininfo.

        Args:
            window_id: Window ID

        Returns:
            WindowInfo object or None
        """
        if not self.has_xwininfo:
            return None

        try:
            # Run xwininfo
            result = subprocess.run(
                ['xwininfo', '-id', str(window_id), '-stats'],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode != 0:
                return None

            output = result.stdout

            # Parse output
            info = {}
            for line in output.split('\n'):
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()

            # Extract geometry
            abs_x = int(info.get('Absolute upper-left X', '0'))
            abs_y = int(info.get('Absolute upper-left Y', '0'))
            width = int(info.get('Width', '0'))
            height = int(info.get('Height', '0'))

            # Get relative position (inside decorations)
            rel_x = int(info.get('Relative upper-left X', '0'))
            rel_y = int(info.get('Relative upper-left Y', '0'))

            window_rect = (abs_x, abs_y, abs_x + width, abs_y + height)
            client_rect = (abs_x + rel_x, abs_y + rel_y, abs_x + width, abs_y + height)

            # Get window name
            title = info.get('Window id', '').split('"')[1] if '"' in info.get('Window id', '') else ""

            # Get additional info using xprop if available
            process_id = 0
            class_name = ""

            if self.has_xprop:
                try:
                    xprop_result = subprocess.run(
                        ['xprop', '-id', str(window_id), '_NET_WM_PID', 'WM_CLASS'],
                        capture_output=True,
                        text=True,
                        timeout=1
                    )

                    for line in xprop_result.stdout.split('\n'):
                        if '_NET_WM_PID' in line:
                            match = re.search(r'= (\d+)', line)
                            if match:
                                process_id = int(match.group(1))
                        elif 'WM_CLASS' in line:
                            match = re.search(r'"([^"]+)"', line)
                            if match:
                                class_name = match.group(1)

                except subprocess.TimeoutExpired:
                    pass

            return WindowInfo(
                handle=window_id,
                title=title,
                class_name=class_name,
                process_id=process_id,
                thread_id=0,
                is_visible=True,
                is_minimized=False,
                is_maximized=False,
                window_rect=window_rect,
                client_rect=client_rect,
                monitor_handle=0,
            )

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError) as e:
            logger.debug(f"Failed to get window info via xwininfo: {e}")

        return None

    def _list_windows_wmctrl(self) -> List[int]:
        """
        List all windows using wmctrl.

        Returns:
            List of window IDs
        """
        if not self.has_wmctrl:
            return []

        try:
            result = subprocess.run(
                ['wmctrl', '-l'],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode != 0:
                return []

            window_ids = []
            for line in result.stdout.strip().split('\n'):
                parts = line.split(None, 1)
                if parts:
                    window_id = self._parse_window_id(parts[0])
                    if window_id:
                        window_ids.append(window_id)

            return window_ids

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            logger.debug(f"Failed to list windows via wmctrl: {e}")
            return []

    def _get_active_window_xprop(self) -> Optional[int]:
        """
        Get active window using xprop.

        Returns:
            Window ID or None
        """
        if not self.has_xprop:
            return None

        try:
            result = subprocess.run(
                ['xprop', '-root', '_NET_ACTIVE_WINDOW'],
                capture_output=True,
                text=True,
                timeout=1
            )

            if result.returncode == 0:
                # Parse: _NET_ACTIVE_WINDOW(WINDOW): window id # 0x1234567
                match = re.search(r'0x[0-9a-fA-F]+', result.stdout)
                if match:
                    return self._parse_window_id(match.group(0))

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            logger.debug(f"Failed to get active window via xprop: {e}")

        return None

    # ==================== Public Interface Methods ====================

    def get_window_info(self, window_handle: Any) -> Optional[WindowInfo]:
        """
        Get detailed information about a window.

        Args:
            window_handle: Window ID (integer)

        Returns:
            WindowInfo object or None if failed
        """
        window_id = int(window_handle) if not isinstance(window_handle, int) else window_handle

        # Try X11 native first
        if self.display_type == 'x11' and self.x_display:
            info = self._get_window_info_x11(window_id)
            if info:
                return info

        # Fallback to wmctrl
        if self.has_wmctrl:
            info = self._get_window_info_wmctrl(window_id)
            if info:
                return info

        # Fallback to xwininfo
        if self.has_xwininfo:
            info = self._get_window_info_xwininfo(window_id)
            if info:
                return info

        logger.warning(f"Could not get window info for {window_id}")
        return None

    def is_browser_window(self, window_handle: Any) -> bool:
        """
        Check if window is a browser window.

        Args:
            window_handle: Window ID

        Returns:
            True if window is a browser
        """
        info = self.get_window_info(window_handle)
        if not info or not info.is_visible:
            return False

        # Check WM_CLASS
        if self._is_browser_wm_class(info.class_name):
            return True

        # Check process name
        if info.process_id > 0:
            process_info = self._get_process_info(info.process_id)
            if self._is_browser_process_name(process_info['name']):
                return True

        # Check title for common browser patterns
        title_lower = info.title.lower()
        browser_indicators = [
            'mozilla firefox',
            'google chrome',
            'chromium',
            'microsoft edge',
            'brave browser',
            'opera',
            'vivaldi',
        ]
        return any(indicator in title_lower for indicator in browser_indicators)

    def find_browser_windows(self) -> List[WindowInfo]:
        """
        Find all browser windows.

        Returns:
            List of browser WindowInfo objects
        """
        browser_windows = []

        # Get all window IDs
        window_ids = []

        if self.display_type == 'x11' and self.x_display:
            window_ids = self._list_windows_x11()
        elif self.has_wmctrl:
            window_ids = self._list_windows_wmctrl()

        # Filter browser windows
        for window_id in window_ids:
            try:
                if self.is_browser_window(window_id):
                    info = self.get_window_info(window_id)
                    if info and not info.is_minimized:
                        browser_windows.append(info)
            except Exception as e:
                logger.debug(f"Error checking window {window_id}: {e}")

        return browser_windows

    def get_window_at_point(self, x: int, y: int) -> Optional[WindowInfo]:
        """
        Get window at a specific screen point.

        Args:
            x: X coordinate in screen pixels
            y: Y coordinate in screen pixels

        Returns:
            WindowInfo for window at point or None
        """
        # For X11 with native python-xlib (most accurate)
        if self.display_type == 'x11' and self.x_display:
            try:
                # Get all windows from the window manager
                # Query _NET_CLIENT_LIST_STACKING for window stack order (bottom to top)
                if self._net_client_list_stacking:
                    try:
                        prop = self.x_root.get_full_property(
                            self._net_client_list_stacking,
                            X.AnyPropertyType
                        )
                        if prop and prop.value:
                            # Windows are listed bottom-to-top, we want top-to-bottom
                            window_ids = list(reversed(prop.value))

                            # Check each window from top to bottom
                            for wid in window_ids:
                                try:
                                    window = self.x_display.create_resource_object('window', wid)
                                    geom = window.get_geometry()

                                    # Translate to screen coordinates
                                    coords = window.translate_coords(self.x_root, 0, 0)

                                    # Check if point is within window bounds
                                    if (coords.x <= x < coords.x + geom.width and
                                        coords.y <= y < coords.y + geom.height):
                                        return self.get_window_info(wid)

                                except Exception as e:
                                    continue

                    except Exception as e:
                        logger.debug(f"Failed to query stacking order: {e}")

            except Exception as e:
                logger.debug(f"Failed to get window at point via X11: {e}")

        # Fallback: Check all windows and see which contains the point
        all_windows = []

        if self.display_type == 'x11' and self.x_display:
            window_ids = self._list_windows_x11()
            all_windows = [self.get_window_info(wid) for wid in window_ids]
        elif self.has_wmctrl:
            window_ids = self._list_windows_wmctrl()
            all_windows = [self.get_window_info(wid) for wid in window_ids]

        # Filter out None values
        all_windows = [w for w in all_windows if w]

        # Find window containing point (prefer visible, non-minimized)
        for window in all_windows:
            if window.is_visible and not window.is_minimized:
                left, top, right, bottom = window.window_rect
                if left <= x <= right and top <= y <= bottom:
                    return window

        return None

    def get_foreground_window(self) -> Optional[WindowInfo]:
        """
        Get the foreground (active) window.

        Returns:
            WindowInfo for foreground window or None
        """
        window_id = None

        # Try X11 native
        if self.display_type == 'x11' and self.x_display:
            window_id = self._get_active_window_x11()

        # Fallback to xprop
        if not window_id and self.has_xprop:
            window_id = self._get_active_window_xprop()

        # Fallback to xdotool
        if not window_id and self.has_xdotool:
            try:
                result = subprocess.run(
                    ['xdotool', 'getactivewindow'],
                    capture_output=True,
                    text=True,
                    timeout=1
                )

                if result.returncode == 0:
                    window_id = self._parse_window_id(result.stdout.strip())

            except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
                logger.debug(f"Failed to get active window via xdotool: {e}")

        if window_id:
            return self.get_window_info(window_id)

        return None

    def screen_to_client(
        self,
        window_handle: Any,
        screen_x: int,
        screen_y: int
    ) -> Tuple[int, int]:
        """
        Convert screen coordinates to client (window-relative) coordinates.

        Args:
            window_handle: Window ID
            screen_x: X coordinate in screen pixels
            screen_y: Y coordinate in screen pixels

        Returns:
            Tuple of (client_x, client_y)
        """
        info = self.get_window_info(window_handle)
        if not info:
            return (screen_x, screen_y)

        # Client coordinates are relative to client rect origin
        client_x = screen_x - info.client_rect[0]
        client_y = screen_y - info.client_rect[1]

        return (client_x, client_y)

    def client_to_screen(
        self,
        window_handle: Any,
        client_x: int,
        client_y: int
    ) -> Tuple[int, int]:
        """
        Convert client coordinates to screen coordinates.

        Args:
            window_handle: Window ID
            client_x: X coordinate in client pixels
            client_y: Y coordinate in client pixels

        Returns:
            Tuple of (screen_x, screen_y)
        """
        info = self.get_window_info(window_handle)
        if not info:
            return (client_x, client_y)

        # Screen coordinates are client coords plus client rect origin
        screen_x = client_x + info.client_rect[0]
        screen_y = client_y + info.client_rect[1]

        return (screen_x, screen_y)


# Singleton instance
_window_manager: Optional[LinuxWindowManager] = None


def get_window_manager() -> LinuxWindowManager:
    """Get or create singleton LinuxWindowManager instance."""
    global _window_manager
    if _window_manager is None:
        _window_manager = LinuxWindowManager()
    return _window_manager
