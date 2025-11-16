# Windows Multi-Monitor and DPI Scaling: Comprehensive Research

## Table of Contents
1. [Windows Multi-Monitor Coordinate System Architecture](#1-windows-multi-monitor-coordinate-system-architecture)
2. [Per-Monitor DPI Awareness (V1, V2)](#2-per-monitor-dpi-awareness-v1-v2)
3. [Mixed DPI Environments](#3-mixed-dpi-environments)
4. [DPI Virtualization and Scaling Modes](#4-dpi-virtualization-and-scaling-modes)
5. [Coordinate Transformations Across Monitors](#5-coordinate-transformations-across-monitors)
6. [GetDpiForMonitor and Related APIs](#6-getdpiformonitor-and-related-apis)
7. [Common Pitfalls and Bugs](#7-common-pitfalls-and-bugs)
8. [Testing Strategies](#8-testing-strategies)

---

## 1. Windows Multi-Monitor Coordinate System Architecture

### Virtual Screen Concept

Windows treats multiple monitors as a single **virtual screen** - a bounding rectangle that encompasses all display monitors. The primary screen has its upper-left corner at Point(0,0).

### Coordinate System Rules

- **Primary Monitor**: Upper-left corner at (0, 0)
- **Left Displays**: Negative X coordinates
- **Right Displays**: Positive X coordinates
- **Above Primary**: Negative Y coordinates
- **Below Primary**: Positive Y coordinates

### Example Configuration

With 2 displays:
- **Secondary FullHD** (1920x1080) on the left with 100% scaling
- **Primary 4K** (3840x2160) on the right with 200% DPI scaling

The desktop reports **3840x1080 pixels** total:
- Secondary: [-1920..0] (X coordinates)
- Primary: [0..1920] (X coordinates)

### System Metrics for Virtual Screen

Use `GetSystemMetrics()` with these constants:

| Constant | Value | Description |
|----------|-------|-------------|
| `SM_XVIRTUALSCREEN` | 76 | Left edge of virtual screen |
| `SM_YVIRTUALSCREEN` | 77 | Top edge of virtual screen |
| `SM_CXVIRTUALSCREEN` | 78 | Width of virtual screen |
| `SM_CYVIRTUALSCREEN` | 79 | Height of virtual screen |
| `SM_CMONITORS` | 80 | Number of display monitors |
| `SM_SAMEDISPLAYFORMAT` | 81 | Whether all monitors have same color format |

### Critical Consideration: Negative Coordinates

Because negative coordinates can happen easily in a multimonitor system, always use `GET_X_LPARAM` and `GET_Y_LPARAM` macros when retrieving coordinates packed in `lParam`.

**Edge Case**: If your primary monitor is on the right and the app is on your left screen, mouse coordinates will be **negative**.

---

## 2. Per-Monitor DPI Awareness (V1, V2)

### DPI Awareness Modes

Windows supports several DPI awareness modes, each with different capabilities:

#### DPI Unaware
- Renders at fixed 96 DPI (100% scaling)
- Windows stretches the application bitmap on high-DPI displays
- Results in blurry appearance on displays set to >100% scaling
- Windows applies DPI virtualization to all coordinates

#### System DPI Aware
- Application queries DPI of primary display at logon time
- Uses single system-wide DPI value
- No bitmap stretching by Windows on primary monitor
- May appear blurry on secondary displays with different DPI
- Creates virtual screen coordinate system for consistent layout

#### Per-Monitor V1 (PMv1)
- **Introduced**: Windows 8.1
- **Features**:
  - Top-level HWNDs receive DPI change notifications
  - No bitmap stretching by Windows
  - Application sees all displays in physical pixels
- **Limitations**:
  - No automatic scaling for child windows
  - No automatic scaling for non-client areas
  - Common controls (buttons, checkboxes) don't redraw bitmaps correctly
  - Very limited - **NOT RECOMMENDED**

#### Per-Monitor V2 (PMv2)
- **Introduced**: Windows 10 Creators Update (1703)
- **Constant**: `DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2` (-4)
- **RECOMMENDED MODE** for modern applications

**Improvements over V1**:
1. **Child window DPI change notifications** - Entire window tree notified of DPI changes
2. **Automatic non-client area scaling** - Title bars, borders drawn DPI-sensitively
3. **Per-monitor Win32 menu scaling** - Menus scale correctly
4. **Automatic dialog response** - Win32 dialogs handle DPI changes automatically
5. **Improved comctl32 controls** - Common controls scale properly

### Manifest Declaration

#### Basic System DPI Awareness:
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true</dpiAware>
    </windowsSettings>
  </application>
</assembly>
```

#### Per-Monitor V2 (Recommended):
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0" xmlns:asmv3="urn:schemas-microsoft-com:asm.v3">
  <asmv3:application>
    <asmv3:windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
    </asmv3:windowsSettings>
  </asmv3:application>
</assembly>
```

#### Full DPI Awareness with Fallbacks:
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly manifestVersion="1.0" xmlns="urn:schemas-microsoft-com:asm.v1" xmlns:asmv3="urn:schemas-microsoft-com:asm.v3">
  <asmv3:application>
    <asmv3:windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">True/PM</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2, PerMonitor</dpiAwareness>
    </asmv3:windowsSettings>
  </asmv3:application>
</assembly>
```

**Important**: On Windows 10 version 1607+, the `dpiAware` setting is ignored if `dpiAwareness` element is present.

### Programmatic Setting

Use `SetProcessDpiAwarenessContext()` to set DPI awareness programmatically (must be called before any window creation):

```cpp
SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);
```

---

## 3. Mixed DPI Environments

### Common Scenarios

Mixed DPI environments occur in several situations:

1. **4K + 1080p displays** - Primary 4K monitor at 200% scaling + secondary 1080p at 100%
2. **Laptop docking/undocking** - High-DPI laptop (e.g., 150%) + low-DPI external monitor (100%)
3. **Multiple 4K displays** - Different scaling preferences on each monitor
4. **Heterogeneous monitor setups** - Various resolutions and physical sizes

### Coordinate System Example

**Setup**: FullHD secondary (left) at 100% + 4K primary (right) at 200%

**Physical Pixels**:
- Secondary: 1920x1080
- Primary: 3840x2160

**Logical Pixels (DPI-aware)**:
- Secondary: 1920x1080
- Primary: 1920x1080 (scaled down by 2x)

**Virtual Desktop Width** (as reported by Windows): 3840 pixels

### Mouse Movement Issues

**Problem**: Mouse cursor behavior between monitors with different DPIs is problematic.

**Example**: Moving from 4K (2160p vertical) to FullHD (1080p vertical):
- The 1080p vertical resolution is **half** the 2160p
- Mouse movements feel disproportionate
- Cursor jumps occur at monitor boundaries

**Solution**: Third-party tools like **LittleBigMouse** provide accurate mouse screen crossover location within multi-DPI monitor environments.

### Visual Artifacts

1. **Window Dragging**: When dragging a window between monitors with different DPI, you'll see an oddly-shaped representation during the transition
2. **Edge Ballooning**: Placing a window partially on a 100% monitor and partially on a 200% monitor can incorrectly balloon the size
3. **Content Positioning**: Off-screen content may not update correctly when moving between displays

### Developer Recommendations

After making applications per-monitor DPI aware:

1. Test moving windows between displays of different DPI values
2. Test starting applications on different DPI displays
3. Test changing scale factors while the application is running
4. Test with Remote Desktop connections to high-DPI displays

---

## 4. DPI Virtualization and Scaling Modes

### What is DPI Virtualization?

When applications don't declare being "DPI aware", Windows applies **DPI Virtualization**:
- Application renders at 96 DPI (100%) internally
- Windows upscales to configured DPI setting
- Results in bitmap stretching and blurry appearance

### How Virtualization Works

When an HWND or process is DPI unaware or system DPI aware:
- Windows scales and converts DPI-sensitive information from APIs
- Conversions happen to coordinate space of calling thread
- Example: DPI-unaware thread queries screen size on high-DPI display → Windows virtualizes answer as if screen were in 96 DPI units

### Scaling Mode Behavior by DPI Awareness

| Awareness Mode | Scaling Behavior |
|----------------|------------------|
| **DPI Unaware** | Windows creates virtualized coordinate system; app always sees 96 DPI |
| **System DPI Aware** | Windows creates virtual screen coordinate based on primary monitor DPI |
| **Per-Monitor V1** | No bitmap stretching; app responsible for all scaling |
| **Per-Monitor V2** | Enhanced automatic scaling with Windows assistance |

### Mixed-Mode DPI Scaling

**Introduced**: Windows 10 Anniversary Update (1607)

Allows different top-level windows in same process to have different DPI awareness contexts.

**Use Case**: Legacy plugins in modern applications can run at different DPI awareness levels

### GDI Scaling Mode

**Introduced**: Windows 10 Creators Update (1703)

For GDI-based applications that can't be fully updated:
- Windows automatically scales GDI primitives
- Non-client areas scaled automatically
- Compatible with GDI operations

**Limitation**: Off-screen content won't update when window moves between displays with different DPIs

---

## 5. Coordinate Transformations Across Monitors

### Core Transformation Functions

Windows provides specific APIs for coordinate transformations in multi-monitor DPI scenarios:

#### LogicalToPhysicalPointForPerMonitorDPI
```cpp
BOOL LogicalToPhysicalPointForPerMonitorDPI(
  HWND  hWnd,
  LPPOINT lpPoint
);
```

**Purpose**: Converts a point in a window from **logical coordinates** into **physical coordinates**, regardless of DPI awareness of caller.

**When to Use**: When you need actual screen pixel coordinates from DPI-aware logical coordinates.

#### PhysicalToLogicalPointForPerMonitorDPI
```cpp
BOOL PhysicalToLogicalPointForPerMonitorDPI(
  HWND  hWnd,
  LPPOINT lpPoint
);
```

**Purpose**: Converts a point in a window from **physical coordinates** into **logical coordinates**, regardless of DPI awareness of caller.

**When to Use**: When you receive screen coordinates and need to convert them to window's logical coordinate space.

### Legacy Transformation Functions

For system DPI aware applications (not per-monitor):

- `LogicalToPhysicalPoint()` - System DPI aware only
- `PhysicalToLogicalPoint()` - System DPI aware only

**Warning**: These functions don't work correctly in per-monitor DPI scenarios. Always use the `ForPerMonitorDPI` variants.

### Terminology

- **Logical Coordinates**: Translated into process's DPI-aware coordinate space
- **Physical Coordinates**: Actual pixels used by operating system and other high-DPI aware processes

### Monitor Identification APIs

#### MonitorFromWindow
```cpp
HMONITOR MonitorFromWindow(
  HWND  hwnd,
  DWORD dwFlags
);
```

Returns handle to display monitor that has the **largest area of intersection** with the window.

**Flags**:
- `MONITOR_DEFAULTTONEAREST` - Returns nearest monitor
- `MONITOR_DEFAULTTONULL` - Returns NULL if no intersection
- `MONITOR_DEFAULTTOPRIMARY` - Returns primary monitor

#### MonitorFromPoint
```cpp
HMONITOR MonitorFromPoint(
  POINT pt,
  DWORD dwFlags
);
```

Returns handle to display monitor that **contains the specified point**.

#### MonitorFromRect
```cpp
HMONITOR MonitorFromRect(
  LPCRECT lprc,
  DWORD   dwFlags
);
```

Returns handle to display monitor that has largest area of intersection with rectangle.

### Getting Monitor Information

```cpp
BOOL GetMonitorInfo(
  HMONITOR      hMonitor,
  LPMONITORINFO lpmi
);
```

Returns `MONITORINFO` structure containing:
- `rcMonitor` - Rectangle of entire monitor
- `rcWork` - Work area (excludes taskbar)
- `dwFlags` - `MONITORINFOF_PRIMARY` if primary monitor

### Enumerating Monitors

```cpp
BOOL EnumDisplayMonitors(
  HDC             hdc,
  LPCRECT         lprcClip,
  MONITORENUMPROC lpfnEnum,
  LPARAM          dwData
);
```

Enumerates all display monitors, calling callback for each.

**Important**: Use `EnumDisplayMonitors()` (not `EnumDisplayDevices()`) to access `HMONITOR` handle.

### Coordinate Transformation Workflow

1. **Get Monitor Handle**:
   ```cpp
   HMONITOR hMonitor = MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST);
   ```

2. **Get Monitor Info**:
   ```cpp
   MONITORINFO mi = { sizeof(mi) };
   GetMonitorInfo(hMonitor, &mi);
   // mi.rcMonitor contains full monitor rectangle
   ```

3. **Transform Coordinates**:
   ```cpp
   POINT pt = {x, y}; // Physical coordinates
   PhysicalToLogicalPointForPerMonitorDPI(hwnd, &pt);
   // pt now contains logical coordinates
   ```

---

## 6. GetDpiForMonitor and Related APIs

### GetDpiForMonitor (Legacy)

```cpp
HRESULT GetDpiForMonitor(
  HMONITOR         hmonitor,
  MONITOR_DPI_TYPE dpiType,
  UINT             *dpiX,
  UINT             *dpiY
);
```

**Purpose**: Queries DPI of a display.

**Parameters**:
- `hmonitor` - Handle from `MonitorFromWindow/Point/Rect`
- `dpiType` - Type of DPI to query (see below)
- `dpiX`, `dpiY` - Output DPI values

**MONITOR_DPI_TYPE Values**:
- `MDT_EFFECTIVE_DPI` (0) - Effective DPI for rendering (recommended)
- `MDT_ANGULAR_DPI` (1) - DPI based on angular width
- `MDT_RAW_DPI` (2) - DPI based on raw resolution

**CRITICAL WARNING**: This API is **NOT DPI aware**. Returns different values depending on caller's DPI awareness. Should **NOT** be used if calling thread is per-monitor DPI aware.

### GetDpiForWindow (Recommended)

```cpp
UINT GetDpiForWindow(HWND hwnd);
```

**Purpose**: Returns DPI value for the **specified window**.

**When to Use**: This is the **recommended** function for per-monitor DPI aware applications.

**Returns**: DPI value for the window's current display.

**Availability**: Windows 10 version 1607+

### GetSystemMetricsForDpi

```cpp
int GetSystemMetricsForDpi(
  int  nIndex,
  UINT dpi
);
```

**Purpose**: Retrieves system metrics or configuration settings **scaled to a specific DPI value**.

**Replacement For**: `GetSystemMetrics()` when dealing with per-monitor DPI awareness.

**Example**:
```cpp
UINT dpi = GetDpiForWindow(hwnd);
int scrollbarWidth = GetSystemMetricsForDpi(SM_CXVSCROLL, dpi);
```

**Availability**: Windows 10 version 1607+

### AdjustWindowRectExForDpi

```cpp
BOOL AdjustWindowRectExForDpi(
  LPRECT lpRect,
  DWORD  dwStyle,
  BOOL   bMenu,
  DWORD  dwExStyle,
  UINT   dpi
);
```

**Purpose**: Calculates required size of window rectangle based on desired client-area size, **scaled for specific DPI**.

**Use Case**: When creating windows in per-monitor DPI aware applications.

**Example**:
```cpp
RECT rc = {0, 0, desiredWidth, desiredHeight};
UINT dpi = GetDpiForWindow(hwndParent);
AdjustWindowRectExForDpi(&rc, WS_OVERLAPPEDWINDOW, FALSE, 0, dpi);
int windowWidth = rc.right - rc.left;
int windowHeight = rc.bottom - rc.top;
```

**Availability**: Windows 10 version 1607+

### GetDpiForSystem

```cpp
UINT GetDpiForSystem(void);
```

**Purpose**: Returns system DPI (DPI of primary monitor at user login).

**Use Case**: For system DPI aware applications (not per-monitor aware).

### GetProcessDpiAwareness

```cpp
HRESULT GetProcessDpiAwareness(
  HANDLE                hprocess,
  PROCESS_DPI_AWARENESS *value
);
```

**Purpose**: Retrieves DPI awareness of specified process.

**Returns**:
- `PROCESS_DPI_UNAWARE` (0)
- `PROCESS_DPI_SYSTEM_AWARE` (1)
- `PROCESS_DPI_PER_MONITOR_AWARE` (2)

### GetWindowDpiAwarenessContext

```cpp
DPI_AWARENESS_CONTEXT GetWindowDpiAwarenessContext(HWND hwnd);
```

**Purpose**: Returns DPI awareness context for a window (supports PMv2).

**Use Case**: Debugging and checking window DPI awareness level.

### API Migration Path

| Legacy API (Avoid) | Per-Monitor DPI API (Use Instead) |
|---------------------|-------------------------------------|
| `GetSystemMetrics()` | `GetSystemMetricsForDpi()` |
| `AdjustWindowRectEx()` | `AdjustWindowRectExForDpi()` |
| `SystemParametersInfo()` | `SystemParametersInfoForDpi()` |
| `GetDpiForMonitor()` | `GetDpiForWindow()` |
| `LogicalToPhysicalPoint()` | `LogicalToPhysicalPointForPerMonitorDPI()` |

### WM_DPICHANGED Message

```cpp
WM_DPICHANGED
wParam: HIWORD = new Y-axis DPI, LOWORD = new X-axis DPI
lParam: Pointer to RECT with suggested window position/size
```

**When Sent**:
- Window moved to monitor with different DPI
- User changes display scaling while app running
- Display configuration changes

**Critical Implementation**:
```cpp
case WM_DPICHANGED:
{
    // Extract new DPI
    UINT newDpiX = LOWORD(wParam);
    UINT newDpiY = HIWORD(wParam);

    // Get suggested rectangle
    RECT* prcNewWindow = (RECT*)lParam;

    // CRITICAL: Use suggested rectangle to prevent recursive DPI changes
    SetWindowPos(hWnd, NULL,
                 prcNewWindow->left, prcNewWindow->top,
                 prcNewWindow->right - prcNewWindow->left,
                 prcNewWindow->bottom - prcNewWindow->top,
                 SWP_NOZORDER | SWP_NOACTIVATE);

    // Rescale UI elements, reload resources at new DPI
    RescaleUI(newDpiX, newDpiY);

    return 0;
}
```

**Why Use Suggested Rectangle**: Ensures mouse cursor stays in same relative position and prevents recursive DPI change cycles.

---

## 7. Common Pitfalls and Bugs

### 1. Caching DPI Values

**Pitfall**: Caching font sizes and DPI values at process initialization.

**Problem**: Display DPI can change multiple times during application lifetime:
- Moving windows between monitors
- User changing scaling settings
- Docking/undocking laptop
- Remote Desktop connections

**Solution**: Re-evaluate DPI-sensitive data whenever new DPI encountered. Never cache DPI values globally.

```cpp
// BAD
static int g_dpi = 96; // Initialized once

// GOOD
UINT GetCurrentDpi(HWND hwnd) {
    return GetDpiForWindow(hwnd); // Query each time
}
```

### 2. Legacy Framework Assumptions

**Problem**: Most legacy UI frameworks assume display DPI won't change during process lifetime.

**Affected Frameworks**:
- Windows Common Controls (without manifest updates)
- Windows Forms (partial support)
- WPF (improved support in .NET 4.6.2+)
- MFC (no native per-monitor DPI support)

**Solution**: Manually handle `WM_DPICHANGED` and resize/reposition all controls.

### 3. Non-Client Area Rendering in PMv1

**Pitfall**: In Per-Monitor V1, common controls (buttons, checkboxes) don't redraw bitmaps when DPI changes.

**Result**: Bitmaps are too large or too small depending on display topology.

**Solution**: Use Per-Monitor V2 (PMv2) which handles this automatically.

### 4. Coordinate Confusion

**Pitfall**: Mixing logical and physical coordinates without proper conversion.

**Example Error**:
```cpp
// Get mouse position (physical coordinates)
POINT pt;
GetCursorPos(&pt);

// Use directly with window (logical coordinates) - WRONG!
ScreenToClient(hwnd, &pt); // May be incorrect if DPIs differ
```

**Solution**: Use proper transformation functions:
```cpp
POINT pt;
GetCursorPos(&pt);
PhysicalToLogicalPointForPerMonitorDPI(hwnd, &pt);
ScreenToClient(hwnd, &pt);
```

### 5. Using Non-DPI-Aware APIs

**Pitfall**: Using legacy APIs that don't account for per-monitor DPI.

**Common Mistakes**:
- `GetSystemMetrics()` instead of `GetSystemMetricsForDpi()`
- `AdjustWindowRectEx()` instead of `AdjustWindowRectExForDpi()`
- `GetDpiForMonitor()` instead of `GetDpiForWindow()`

**Solution**: Grep codebase for non-DPI-aware APIs and replace with DPI-aware versions.

### 6. Ignoring WM_DPICHANGED Suggested Rectangle

**Pitfall**: Not using the suggested rectangle provided in `WM_DPICHANGED` lParam.

**Consequences**:
- Mouse cursor jumps to different relative position
- Window enters recursive DPI change cycle
- Window positioned incorrectly

**Solution**: ALWAYS use suggested rectangle:
```cpp
RECT* prcNewWindow = (RECT*)lParam;
SetWindowPos(hWnd, NULL, prcNewWindow->left, ...);
```

### 7. Window Positioning at Monitor Edges

**Pitfall**: Placing window edge at exact monitor boundary in mixed DPI setup.

**Problem**: Window can balloon to incorrect size if partially touching higher-DPI monitor.

**Solution**: Add small margin when positioning windows near monitor boundaries.

### 8. Bitmap Resource Scaling

**Pitfall**: Loading single-resolution bitmaps/icons.

**Problem**: Images appear pixelated on high-DPI displays or too small on low-DPI.

**Solution**:
- Provide multiple resolution resources (96, 120, 144, 192 DPI)
- Load appropriate resource based on current DPI
- Use vector formats (SVG) when possible

### 9. Font Size Calculations

**Pitfall**: Using hard-coded font sizes.

**Example**:
```cpp
// BAD
CreateFont(-14, ...); // Fixed size
```

**Solution**: Scale based on DPI:
```cpp
UINT dpi = GetDpiForWindow(hwnd);
int fontSize = MulDiv(14, dpi, 96);
CreateFont(-fontSize, ...);
```

### 10. Remote Desktop DPI Mismatches

**Pitfall**: Not testing with Remote Desktop connections.

**Problem**: RDP can introduce unexpected DPI changes and multi-monitor configurations.

**Issues**:
- Local DPI settings applied remotely
- Multi-monitor RDP inherits different DPI per monitor
- Scaling settings disabled within remote session

**Solution**: Test thoroughly with RDP scenarios.

### 11. Negative Coordinates Not Handled

**Pitfall**: Assuming all coordinates are positive.

**Problem**: Monitors left/above primary have negative coordinates.

**Solution**:
- Use `GET_X_LPARAM` and `GET_Y_LPARAM` macros
- Test with monitors positioned left/above primary

### 12. Primary Monitor Changes

**Pitfall**: Not handling primary monitor changes.

**Scenario**: User changes which display is primary, signs out, signs back in.

**Problem**: System DPI aware apps use wrong DPI.

**Solution**: For per-monitor aware apps, respond to DPI changes dynamically.

### 13. GDI Scaling Limitations

**Pitfall**: Using GDI scaling mode without understanding limitations.

**Problem**: Off-screen content (e.g., compatible bitmaps) won't update when window moves between displays with different DPIs.

**Solution**: Manually invalidate and redraw off-screen content on DPI changes.

### 14. Mixed-Mode Window Tree Issues

**Pitfall**: Having child windows with different DPI awareness in same window tree.

**Problem**: Coordinate transformations become complex; child windows may not scale correctly.

**Solution**: Keep DPI awareness consistent within window tree when possible.

---

## 8. Testing Strategies

### Test Scenarios

#### 1. Window Movement Between Displays
- **Setup**: Configure two monitors with different DPI (e.g., 100% and 200%)
- **Test**: Drag application window back and forth between displays
- **Verify**:
  - Window scales correctly
  - Content remains crisp (not blurry)
  - Window maintains proportions
  - Mouse cursor stays in relative position

#### 2. Application Startup on Different Displays
- **Setup**: Multiple monitors with different DPI
- **Test**:
  - Start application on primary display
  - Start application on secondary display
  - Move window to different display before showing
- **Verify**:
  - Application renders correctly on each display
  - Initial window size appropriate for DPI
  - UI elements scaled properly

#### 3. Runtime DPI Changes
- **Setup**: Application running on single display
- **Test**:
  - Open Windows Display Settings
  - Change scaling slider (e.g., from 100% to 150%)
  - Click "Apply"
- **Verify**:
  - Application receives `WM_DPICHANGED`
  - Window resizes automatically
  - UI scales correctly
  - No visual artifacts

#### 4. Primary Display Changes
- **Setup**: Multi-monitor system
- **Test**:
  - Change primary display in Windows Display Settings
  - Sign out of Windows
  - Sign back in
  - Test application
- **Verify**:
  - Application uses correct DPI on startup
  - System DPI aware apps adapt to new primary DPI

#### 5. Docking/Undocking Laptop
- **Setup**: Laptop with external monitor
- **Test**:
  - Run application on external monitor
  - Undock laptop (external monitor disconnects)
  - Application forced to laptop display
- **Verify**:
  - Application adapts to laptop DPI
  - Window repositions correctly
  - No crashes or hangs

#### 6. Remote Desktop Scenarios
- **Setup**: RDP client and server
- **Test**:
  - Connect via RDP with "Use all monitors" option
  - Test with heterogeneous local monitor DPIs
  - Change DPI on local machine during session
- **Verify**:
  - DPI settings propagate correctly
  - Multi-monitor RDP handles different DPIs
  - No scaling artifacts

### Testing Configurations

#### Recommended Test Setups

1. **Basic Dual Monitor**:
   - Primary: 1080p @ 100%
   - Secondary: 1080p @ 100%
   - Tests: Basic multi-monitor functionality

2. **Mixed DPI Standard**:
   - Primary: 4K @ 200%
   - Secondary: 1080p @ 100%
   - Tests: Most common mixed DPI scenario

3. **Triple Monitor Mixed**:
   - Left: 1080p @ 100%
   - Center: 4K @ 150%
   - Right: 1080p @ 125%
   - Tests: Complex heterogeneous setup

4. **High DPI Only**:
   - Primary: 4K @ 200%
   - Secondary: 4K @ 175%
   - Tests: High DPI handling

5. **Extreme Scaling**:
   - Primary: 4K @ 300%
   - Secondary: 1080p @ 100%
   - Tests: Extreme DPI differences

### Testing Tools

#### Windows Task Manager
- **Feature**: Shows DPI awareness mode of running processes
- **Access**:
  1. Open Task Manager
  2. Click "Details" tab
  3. Right-click column header → "Select columns"
  4. Check "DPI Awareness"
- **Modes Shown**:
  - DPI Unaware
  - System DPI aware
  - Per-Monitor
  - Per-Monitor V2

#### WinSpy++
- **Purpose**: Window inspection utility
- **Features**: Inspect window properties, styles, DPI context
- **Source**: Open source (GitHub: strobejb/winspy)

#### CheckDpiAwareness
- **Purpose**: Console tool showing DPI awareness of running processes
- **Source**: GitHub: Maximus5/CheckDpiAwareness
- **Usage**: Run from command line to list all processes with DPI awareness

#### GetWindowDpiAwarenessContext API
```cpp
DPI_AWARENESS_CONTEXT ctx = GetWindowDpiAwarenessContext(hwnd);
if (AreDpiAwarenessContextsEqual(ctx, DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)) {
    // Window is PMv2
}
```

### Simulating Multi-Monitor Without Hardware

#### 1. Change DPI on Single Monitor
- Open Display Settings
- Adjust "Scale and layout" slider
- Click "Apply" (forces DPI change)
- Application should respond to `WM_DPICHANGED`

#### 2. Remote Desktop Multi-Monitor
- Use RDP with "Use all monitors" option on Display tab
- Can test multi-monitor on remote computer
- Inherits local monitor DPI settings

#### 3. Virtual Machines
- Configure VM with multiple virtual monitors
- Set different scaling on each virtual monitor
- Test application in VM

#### 4. Windows Display Settings Tricks
- Configure monitors in different arrangements
- Set different scaling on each (even if same physical monitor)
- Can simulate mixed DPI by changing settings between tests

### Automated Testing Approaches

#### 1. DPI Change Injection
```cpp
// Programmatically trigger DPI change for testing
SendMessage(hwnd, WM_DPICHANGED,
            MAKEWPARAM(192, 192), // 200% DPI
            (LPARAM)&suggestedRect);
```

#### 2. Monitor Configuration Queries
```cpp
// Enumerate and log all monitor configurations
EnumDisplayMonitors(NULL, NULL, MonitorEnumProc, 0);

BOOL CALLBACK MonitorEnumProc(HMONITOR hMonitor, HDC hdcMonitor,
                              LPRECT lprcMonitor, LPARAM dwData)
{
    MONITORINFO mi = {sizeof(mi)};
    GetMonitorInfo(hMonitor, &mi);

    UINT dpiX, dpiY;
    GetDpiForMonitor(hMonitor, MDT_EFFECTIVE_DPI, &dpiX, &dpiY);

    // Log: monitor rect, work area, DPI
    return TRUE;
}
```

#### 3. UI Automation
- Use Windows UI Automation framework
- Programmatically move windows between monitors
- Verify scaling and positioning

### Regression Test Checklist

- [ ] Window scales correctly on each monitor
- [ ] Content remains crisp (not blurry) on all displays
- [ ] Mouse cursor tracking accurate across monitors
- [ ] Window positioning correct after DPI change
- [ ] `WM_DPICHANGED` handled correctly
- [ ] No recursive DPI change loops
- [ ] Fonts scale proportionally
- [ ] Icons/bitmaps load appropriate resolution
- [ ] Menus render at correct DPI
- [ ] Dialogs scale correctly
- [ ] Controls (buttons, checkboxes) render properly
- [ ] Scrollbars appropriately sized
- [ ] Non-client area (title bar, borders) scales
- [ ] Child windows scale with parent
- [ ] No coordinate calculation errors
- [ ] Negative coordinates handled correctly
- [ ] Application starts correctly on any monitor
- [ ] RDP scenarios work correctly
- [ ] Docking/undocking handled gracefully
- [ ] Primary monitor changes don't break app

### Debugging Techniques

#### 1. Log DPI Changes
```cpp
case WM_DPICHANGED:
{
    UINT oldDpi = GetDpiForWindow(hWnd);
    UINT newDpi = LOWORD(wParam);

    char buffer[256];
    sprintf(buffer, "DPI Changed: %u -> %u", oldDpi, newDpi);
    OutputDebugString(buffer);

    // ... handle DPI change
}
```

#### 2. Monitor Enumeration Logging
```cpp
void LogMonitorConfiguration()
{
    OutputDebugString("=== Monitor Configuration ===");
    EnumDisplayMonitors(NULL, NULL, [](HMONITOR hMon, HDC hdc,
                                       LPRECT rect, LPARAM param) -> BOOL
    {
        MONITORINFO mi = {sizeof(mi)};
        GetMonitorInfo(hMon, &mi);

        UINT dpiX, dpiY;
        GetDpiForMonitor(hMon, MDT_EFFECTIVE_DPI, &dpiX, &dpiY);

        char buf[512];
        sprintf(buf, "Monitor: [%d,%d,%d,%d] DPI: %ux%u %s",
                mi.rcMonitor.left, mi.rcMonitor.top,
                mi.rcMonitor.right, mi.rcMonitor.bottom,
                dpiX, dpiY,
                (mi.dwFlags & MONITORINFOF_PRIMARY) ? "PRIMARY" : "");
        OutputDebugString(buf);

        return TRUE;
    }, 0);
}
```

#### 3. Coordinate Transformation Verification
```cpp
void VerifyCoordinateTransformation(HWND hwnd, POINT physicalPt)
{
    POINT logicalPt = physicalPt;
    PhysicalToLogicalPointForPerMonitorDPI(hwnd, &logicalPt);

    POINT backToPhysical = logicalPt;
    LogicalToPhysicalPointForPerMonitorDPI(hwnd, &backToPhysical);

    char buf[256];
    sprintf(buf, "Physical(%d,%d) -> Logical(%d,%d) -> Physical(%d,%d)",
            physicalPt.x, physicalPt.y,
            logicalPt.x, logicalPt.y,
            backToPhysical.x, backToPhysical.y);
    OutputDebugString(buf);

    // Verify round-trip accuracy
    assert(physicalPt.x == backToPhysical.x);
    assert(physicalPt.y == backToPhysical.y);
}
```

### Performance Considerations

#### Frequent DPI Queries
- Cache DPI per window, invalidate on `WM_DPICHANGED`
- Don't query DPI on every paint/layout cycle
- Use window property to store current DPI

#### Resource Loading
- Pre-load resources at common DPI values (96, 120, 144, 192)
- Lazy load resources for less common DPIs
- Cache scaled resources to avoid repeated scaling

---

## Additional Resources

### Official Microsoft Documentation

1. **High DPI Desktop Application Development**
   - https://learn.microsoft.com/en-us/windows/win32/hidpi/high-dpi-desktop-application-development-on-windows

2. **Mixed-Mode DPI Scaling and DPI-aware APIs**
   - https://learn.microsoft.com/en-us/windows/win32/hidpi/high-dpi-improvements-for-desktop-applications

3. **DPI_AWARENESS_CONTEXT**
   - https://learn.microsoft.com/en-us/windows/win32/hidpi/dpi-awareness-context

4. **WM_DPICHANGED Message**
   - https://learn.microsoft.com/en-us/windows/win32/hidpi/wm-dpichanged

5. **Multiple Display Monitors Functions**
   - https://learn.microsoft.com/en-us/windows/win32/gdi/multiple-display-monitors-functions

6. **GetDpiForWindow API**
   - https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getdpiforwindow

### Developer Blogs and Articles

1. **Windows Developer Blog - High-DPI Scaling Improvements (Creators Update 1703)**
   - https://blogs.windows.com/windowsdeveloper/2017/04/04/high-dpi-scaling-improvements-desktop-applications-windows-10-creators-update/

2. **Windows Developer Blog - Anniversary Update (1607)**
   - https://blogs.windows.com/windowsdeveloper/2016/10/24/high-dpi-scaling-improvements-for-desktop-applications-and-mixed-mode-dpi-scaling-in-the-windows-10-anniversary-update/

3. **How to build high DPI aware native Windows desktop applications**
   - https://mariusbancila.ro/blog/2021/05/19/how-to-build-high-dpi-aware-native-desktop-applications/

4. **Writing Win32 apps like it's 2020: A DPI-aware resizable wizard**
   - https://building.enlyze.com/posts/writing-win32-apps-like-its-2020-part-3/

### Code Samples

1. **Microsoft Windows Classic Samples - DPIAwarenessPerWindow**
   - https://github.com/microsoft/Windows-classic-samples/tree/main/Samples/DPIAwarenessPerWindow

2. **Win32 DPI And Monitor Scaling (Comprehensive Guide)**
   - https://gist.github.com/marler8997/9f39458d26e2d8521d48e36530fbb459

3. **GitHub - tringi/win32-dpi**
   - Example of properly DPI-scaling Win32 windows from XP to Windows 11
   - https://github.com/tringi/win32-dpi

### Community Resources

1. **Stack Overflow - DPI Awareness Tag**
   - Search for real-world issues and solutions
   - Common topics: coordinate transformations, WM_DPICHANGED handling

2. **VirtualDub.org - Implementing per-monitor DPI awareness**
   - https://www.virtualdub.org/blog2/entry_384.html
   - Detailed walkthrough of conversion process

---

## Summary and Best Practices

### Quick Reference: DPI Awareness Decision Tree

```
Is your application new development?
├─ YES → Use Per-Monitor V2 (PMv2)
│        - Add manifest with PerMonitorV2
│        - Use GetDpiForWindow()
│        - Handle WM_DPICHANGED
│        - Use DPI-aware APIs (*ForDpi variants)
│
└─ NO → Is it worth updating?
    ├─ YES → Gradually migrate to PMv2
    │        - Start with manifest
    │        - Replace non-DPI-aware APIs
    │        - Add WM_DPICHANGED handling
    │        - Test thoroughly
    │
    └─ NO → Use GDI Scaling Mode (limited support)
             - Add manifest with PerMonitorV2
             - Enable GDI scaling
             - Accept limitations (off-screen content)
```

### Essential Best Practices

1. **Always use Per-Monitor V2** for new applications
2. **Never cache DPI values** globally
3. **Always use suggested rectangle** in WM_DPICHANGED
4. **Replace all non-DPI-aware APIs** with *ForDpi variants
5. **Test on real multi-monitor mixed-DPI hardware**
6. **Handle negative coordinates** properly
7. **Load multiple resolution resources** (96, 120, 144, 192 DPI)
8. **Scale fonts dynamically** based on current DPI
9. **Use coordinate transformation APIs** correctly
10. **Test RDP scenarios** thoroughly

### Common Mistakes to Avoid

1. ❌ Caching DPI at initialization
2. ❌ Using legacy APIs (GetSystemMetrics, AdjustWindowRectEx)
3. ❌ Ignoring WM_DPICHANGED suggested rectangle
4. ❌ Assuming all coordinates are positive
5. ❌ Using GetDpiForMonitor instead of GetDpiForWindow
6. ❌ Not testing on mixed DPI hardware
7. ❌ Hard-coding font sizes
8. ❌ Loading single-resolution bitmaps
9. ❌ Not handling primary monitor changes
10. ❌ Mixing logical and physical coordinates

---

## Version History and API Availability

| Windows Version | Features Introduced |
|-----------------|---------------------|
| **Windows Vista** | System DPI Awareness, dpiAware manifest |
| **Windows 7** | Improved DPI scaling |
| **Windows 8.1** | Per-Monitor DPI V1, GetDpiForMonitor |
| **Windows 10 1607** | Mixed-Mode DPI, GetDpiForWindow, *ForDpi APIs, dpiAwareness manifest |
| **Windows 10 1703** | Per-Monitor V2, GDI Scaling, Enhanced WM_DPICHANGED |
| **Windows 11** | Continued improvements, better UI framework support |

### Minimum Requirements for PMv2

- **OS**: Windows 10 Creators Update (1703) or later
- **APIs**: GetDpiForWindow, GetSystemMetricsForDpi, AdjustWindowRectExForDpi
- **Manifest**: Both dpiAware and dpiAwareness elements
- **Fallback**: Use PerMonitorV2, PerMonitor in dpiAwareness for compatibility

---

**Last Updated**: 2025-11-16
**Research Focus**: Windows-specific implementations and edge cases
**Primary Sources**: Microsoft Learn, Windows Developer Blog, Stack Overflow, Developer experiences
