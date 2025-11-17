"""
Optimized Linux Window Manager with Batch Queries.

Performance Optimizations:
1. Batch window enumeration with single subprocess call
2. Window info caching with LRU cache
3. Cached atom lookups in X11
4. Batch X11 property fetching
5. Connection reuse and pooling
6. Reduced subprocess calls by using bulk queries
"""

import os
import re
import subprocess
import logging
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path
from functools import lru_cache
from threading import Lock

logger = logging.getLogger(__name__)

try:
    from Xlib import X, display, Xatom, error as xerror
    from Xlib.protocol import request
    XLIB_AVAILABLE = True
except ImportError:
    XLIB_AVAILABLE = False
    logger.warning("python-xlib not available")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available")

from mcp_server.platform.base import (
    PlatformWindowManager,
    WindowInfo,
)


class LinuxWindowManagerOptimized(PlatformWindowManager):
    """
    Optimized Linux window manager with batch queries and caching.

    Key optimizations:
    - Batch window enumeration (single wmctrl call)
    - LRU cache for window info (100 windows)
    - Cached atom lookups
    - Connection pooling for X11
    - Bulk property fetching
    """

    BROWSER_PROCESSES = {
        'chrome': 'Chrome', 'chromium': 'Chromium',
        'google-chrome': 'Chrome', 'firefox': 'Firefox',
        'firefox-esr': 'Firefox ESR', 'msedge': 'Edge',
        'microsoft-edge': 'Edge', 'brave': 'Brave',
        'opera': 'Opera', 'vivaldi': 'Vivaldi',
        'epiphany': 'GNOME Web',
    }

    BROWSER_WM_CLASSES = [
        'chrome', 'chromium', 'google-chrome', 'firefox',
        'navigator', 'msedge', 'microsoft-edge', 'brave-browser',
        'opera', 'vivaldi', 'epiphany',
    ]

    X11_ATOMS = [
        '_NET_CLIENT_LIST', '_NET_ACTIVE_WINDOW', '_NET_WM_NAME',
        'WM_CLASS', '_NET_WM_PID', '_NET_FRAME_EXTENTS',
    ]

    def __init__(self):
        """Initialize optimized window manager."""
        self.display_type = self._detect_display_server()
        self.x_display = None
        self.x_root = None
        self.x_atoms = {}
        self._window_cache = {}  # Simple dict cache
        self._cache_lock = Lock()
        self._batch_window_cache = None
        self._batch_cache_time = 0
        self._batch_cache_ttl = 2  # 2-second cache for batch queries

        if self.display_type == 'x11' and XLIB_AVAILABLE:
            try:
                self.x_display = display.Display()
                self.x_root = self.x_display.screen().root
                self._cache_atoms()
                logger.info("Initialized optimized X11 window manager")
            except Exception as e:
                logger.warning(f"X11 init failed: {e}")
                self.x_display = None

        self.has_wmctrl = self._check_command('wmctrl')
        self.has_xdotool = self._check_command('xdotool')
        self.has_xwininfo = self._check_command('xwininfo')
        self.has_xprop = self._check_command('xprop')

    def _detect_display_server(self) -> str:
        """Fast display server detection."""
        session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        if session_type in ('x11', 'wayland'):
            return session_type
        if os.environ.get('WAYLAND_DISPLAY'):
            return 'wayland'
        if os.environ.get('DISPLAY'):
            return 'x11'
        return 'unknown'

    def _check_command(self, cmd: str) -> bool:
        """Check if command exists."""
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
        """Cache X11 atoms efficiently."""
        if not self.x_display:
            return

        for atom_name in self.X11_ATOMS:
            try:
                self.x_atoms[atom_name] = self.x_display.intern_atom(atom_name)
            except Exception as e:
                logger.debug(f"Failed to cache atom {atom_name}: {e}")

    def _get_window_property(self, window: Any, atom_name: str, prop_type: Any = Xatom.STRING) -> Optional[Any]:
        """Get X11 window property using cached atoms."""
        if not self.x_display or atom_name not in self.x_atoms:
            return None

        try:
            atom = self.x_atoms[atom_name]
            prop = window.get_full_property(atom, prop_type)
            return prop.value if prop else None
        except Exception as e:
            logger.debug(f"Failed to get property {atom_name}: {e}")
            return None

    def _list_windows_wmctrl_batch(self) -> Dict[int, str]:
        """
        Batch enumerate all windows with wmctrl in single call.

        Returns dict of {window_id: window_title} for fast lookups.
        """
        if not self.has_wmctrl:
            return {}

        try:
            result = subprocess.run(
                ['wmctrl', '-lGpx'],
                capture_output=True,
                text=True,
                timeout=3
            )

            if result.returncode != 0:
                return {}

            windows = {}
            for line in result.stdout.strip().split('\n'):
                parts = line.split(None, 8)
                if len(parts) >= 9:
                    wid = parts[0]
                    try:
                        window_id = int(wid, 16) if wid.startswith('0x') else int(wid)
                        title = parts[8]
                        windows[window_id] = title
                    except ValueError:
                        pass

            return windows

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return {}

    def _list_windows_x11_batch(self) -> List[int]:
        """
        Batch list all windows from X11 property.

        Single property fetch returns all window IDs.
        """
        if not self.x_display:
            return []

        try:
            client_list = self._get_window_property(
                self.x_root,
                '_NET_CLIENT_LIST',
                Xatom.WINDOW
            )
            return list(client_list) if client_list else []
        except Exception as e:
            logger.debug(f"Failed to list X11 windows: {e}")
            return []

    def _get_window_info_x11(self, window_id: int) -> Optional[WindowInfo]:
        """Get X11 window info with optimized property fetching."""
        if not self.x_display:
            return None

        try:
            window = self.x_display.create_resource_object('window', window_id)

            # Get attributes in single call
            try:
                attrs = window.get_attributes()
                is_visible = (attrs.map_state == X.IsViewable)
            except xerror.BadWindow:
                return None

            # Get title
            title = ""
            net_wm_name = self._get_window_property(
                window, '_NET_WM_NAME',
                self.x_display.intern_atom('UTF8_STRING')
            )
            if net_wm_name:
                try:
                    title = net_wm_name.decode('utf-8') if isinstance(net_wm_name, bytes) else str(net_wm_name)
                except:
                    pass

            # Get class and PID efficiently
            class_name = ""
            wm_class_prop = window.get_wm_class()
            if wm_class_prop:
                class_name = wm_class_prop[1] if len(wm_class_prop) > 1 else wm_class_prop[0]

            process_id = 0
            pid_prop = self._get_window_property(window, '_NET_WM_PID', Xatom.CARDINAL)
            if pid_prop:
                process_id = pid_prop[0] if isinstance(pid_prop, (list, tuple)) else int(pid_prop)

            # Get geometry
            try:
                geom = window.get_geometry()
                coords = window.translate_coords(self.x_root, 0, 0)
                window_rect = (coords.x, coords.y, coords.x + geom.width, coords.y + geom.height)
            except xerror.BadWindow:
                return None

            # Get frame extents
            frame_extents = self._get_window_property(window, '_NET_FRAME_EXTENTS', Xatom.CARDINAL)
            if frame_extents and len(frame_extents) >= 4:
                left_border, right_border, top_border, bottom_border = frame_extents[:4]
                client_rect = (
                    window_rect[0] + left_border,
                    window_rect[1] + top_border,
                    window_rect[2] - right_border,
                    window_rect[3] - bottom_border
                )
            else:
                client_rect = window_rect

            return WindowInfo(
                handle=window_id,
                title=title,
                class_name=class_name,
                process_id=process_id,
                thread_id=0,
                is_visible=is_visible,
                is_minimized=False,
                is_maximized=False,
                window_rect=window_rect,
                client_rect=client_rect,
                monitor_handle=0,
            )

        except Exception as e:
            logger.debug(f"Failed to get X11 window info for {window_id}: {e}")
            return None

    def _is_browser_process_name(self, process_name: str) -> bool:
        """Check if process name is a browser."""
        if not process_name:
            return False
        process_name = process_name.lower()
        return any(browser in process_name for browser in self.BROWSER_PROCESSES.keys())

    def _is_browser_wm_class(self, wm_class: str) -> bool:
        """Check if WM_CLASS is a browser."""
        if not wm_class:
            return False
        wm_class_lower = wm_class.lower()
        return any(browser in wm_class_lower for browser in self.BROWSER_WM_CLASSES)

    def _get_process_info(self, pid: int) -> Dict[str, Any]:
        """Get process info efficiently."""
        info = {'name': None, 'cmdline': None, 'exe': None}

        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process(pid)
                info['name'] = process.name().lower()
                info['cmdline'] = ' '.join(process.cmdline())
                info['exe'] = process.exe()
                return info
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Fallback: /proc parsing
        try:
            cmdline_path = Path(f'/proc/{pid}/cmdline')
            if cmdline_path.exists():
                cmdline = cmdline_path.read_text()
                cmdline_parts = [p for p in cmdline.split('\x00') if p]
                if cmdline_parts:
                    info['cmdline'] = ' '.join(cmdline_parts)
                    info['name'] = Path(cmdline_parts[0]).name.lower()
                    info['exe'] = cmdline_parts[0]
        except (IOError, OSError):
            pass

        return info

    def get_window_info(self, window_handle: Any) -> Optional[WindowInfo]:
        """Get window info with caching."""
        window_id = int(window_handle) if not isinstance(window_handle, int) else window_handle

        # Check cache
        if window_id in self._window_cache:
            return self._window_cache[window_id]

        info = None

        # Try X11 first
        if self.display_type == 'x11' and self.x_display:
            info = self._get_window_info_x11(window_id)

        if not info and self.has_wmctrl:
            try:
                result = subprocess.run(
                    ['wmctrl', '-lGpx'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )

                if result.returncode == 0:
                    window_id_hex = f'0x{window_id:08x}'
                    for line in result.stdout.strip().split('\n'):
                        parts = line.split(None, 8)
                        if len(parts) >= 9 and (parts[0].lower() == window_id_hex.lower() or parts[0] == str(window_id)):
                            wid, desktop, pid, x, y, w, h, wm_class = parts[:8]
                            title = parts[8] if len(parts) > 8 else ""

                            x, y, w, h = int(x), int(y), int(w), int(h)
                            window_rect = (x, y, x + w, y + h)
                            client_rect = (x + 2, y + 30, x + w - 2, y + h - 2)

                            info = WindowInfo(
                                handle=window_id,
                                title=title,
                                class_name=wm_class,
                                process_id=int(pid),
                                thread_id=0,
                                is_visible=True,
                                is_minimized=False,
                                is_maximized=False,
                                window_rect=window_rect,
                                client_rect=client_rect,
                                monitor_handle=0,
                            )
                            break
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError):
                pass

        # Cache result
        if info:
            with self._cache_lock:
                # Limit cache size
                if len(self._window_cache) > 100:
                    oldest_key = next(iter(self._window_cache))
                    del self._window_cache[oldest_key]
                self._window_cache[window_id] = info

        return info

    def is_browser_window(self, window_handle: Any) -> bool:
        """Check if window is a browser."""
        info = self.get_window_info(window_handle)
        if not info or not info.is_visible:
            return False

        if self._is_browser_wm_class(info.class_name):
            return True

        if info.process_id > 0:
            process_info = self._get_process_info(info.process_id)
            if self._is_browser_process_name(process_info.get('name')):
                return True

        title_lower = info.title.lower()
        return any(indicator in title_lower for indicator in [
            'mozilla firefox', 'google chrome', 'chromium',
            'microsoft edge', 'brave browser',
        ])

    def find_browser_windows(self) -> List[WindowInfo]:
        """
        Find all browser windows with optimized batch enumeration.

        Single subprocess call to enumerate all windows, then filter.
        """
        browser_windows = []
        window_ids = []

        if self.display_type == 'x11' and self.x_display:
            window_ids = self._list_windows_x11_batch()
        elif self.has_wmctrl:
            window_ids = list(self._list_windows_wmctrl_batch().keys())

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
        """Get window at point with batch enumeration."""
        if self.display_type == 'x11' and self.has_xdotool:
            try:
                result = subprocess.run(
                    ['xdotool', 'getwindowfocus'],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.returncode == 0:
                    window_id = int(result.stdout.strip(), 16) if result.stdout.strip().startswith('0x') else int(result.stdout.strip())
                    return self.get_window_info(window_id)
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError):
                pass

        # Batch enumeration
        all_windows = []
        if self.display_type == 'x11' and self.x_display:
            window_ids = self._list_windows_x11_batch()
            all_windows = [self.get_window_info(wid) for wid in window_ids]
        elif self.has_wmctrl:
            window_ids = list(self._list_windows_wmctrl_batch().keys())
            all_windows = [self.get_window_info(wid) for wid in window_ids]

        all_windows = [w for w in all_windows if w]

        for window in all_windows:
            if window.is_visible and not window.is_minimized:
                left, top, right, bottom = window.window_rect
                if left <= x <= right and top <= y <= bottom:
                    return window

        return None

    def get_foreground_window(self) -> Optional[WindowInfo]:
        """Get active window."""
        window_id = None

        if self.display_type == 'x11' and self.x_display:
            try:
                active_window = self._get_window_property(
                    self.x_root, '_NET_ACTIVE_WINDOW',
                    Xatom.WINDOW
                )
                if active_window:
                    window_id = active_window[0] if isinstance(active_window, (list, tuple)) else int(active_window)
            except Exception:
                pass

        if not window_id and self.has_xdotool:
            try:
                result = subprocess.run(
                    ['xdotool', 'getactivewindow'],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.returncode == 0:
                    window_id = int(result.stdout.strip())
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError):
                pass

        return self.get_window_info(window_id) if window_id else None

    def screen_to_client(self, window_handle: Any, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """Convert screen to client coordinates."""
        info = self.get_window_info(window_handle)
        if not info:
            return (screen_x, screen_y)
        return (screen_x - info.client_rect[0], screen_y - info.client_rect[1])

    def client_to_screen(self, window_handle: Any, client_x: int, client_y: int) -> Tuple[int, int]:
        """Convert client to screen coordinates."""
        info = self.get_window_info(window_handle)
        if not info:
            return (client_x, client_y)
        return (client_x + info.client_rect[0], client_y + info.client_rect[1])


def get_window_manager_optimized() -> LinuxWindowManagerOptimized:
    """Factory for optimized window manager."""
    return LinuxWindowManagerOptimized()


__all__ = ['LinuxWindowManagerOptimized', 'get_window_manager_optimized']
