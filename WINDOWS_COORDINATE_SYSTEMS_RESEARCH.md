# Windows Coordinate Systems for Accurate Clicking - Comprehensive Research

## Table of Contents
1. [Windows Screen Coordinates Overview](#1-windows-screen-coordinates-overview)
2. [Mouse Position and Input APIs](#2-mouse-position-and-input-apis)
3. [Coordinate Transformations](#3-coordinate-transformations)
4. [High DPI Awareness Modes](#4-high-dpi-awareness-modes)
5. [Multi-Monitor Coordinate Systems](#5-multi-monitor-coordinate-systems)
6. [Windows Accessibility APIs](#6-windows-accessibility-apis)
7. [Common Pitfalls and Best Practices](#7-common-pitfalls-and-best-practices)
8. [Code Examples and Formulas](#8-code-examples-and-formulas)

---

## 1. Windows Screen Coordinates Overview

### 1.1 Physical vs. Logical Pixels

Windows maintains two distinct coordinate systems:

- **Physical Coordinates**: The actual offset in pixels from the upper-left corner of the origin point. These represent the true hardware pixels on the display.
- **Logical Coordinates**: The offsets as they would be if the pixels themselves were scaled. These are virtualized by Windows based on DPI settings.

### 1.2 Device-Independent Pixels (DIPs)

- A DIP is defined as **1/96th of a logical inch**
- For many years, Windows used the conversion: **One logical inch = 96 pixels**
- In Direct2D, coordinates are measured in DIPs
- DIPs map to physical pixels through a scalar value determined by the DPI setting

### 1.3 Standard DPI Settings

| Scale % | DPI Value | Relationship |
|---------|-----------|--------------|
| 100%    | 96 DPI    | 96 × 1.00    |
| 125%    | 120 DPI   | 96 × 1.25    |
| 150%    | 144 DPI   | 96 × 1.50    |
| 200%    | 192 DPI   | 96 × 2.00    |

**Formula**: `Logical DPI = 96 × (Scaling Percentage / 100)`

### 1.4 Coordinate Conversion Formulas

**Physical to Logical:**
```
Logical Pixels = Physical Pixels / (DPI / 96)
Logical Pixels = Physical Pixels × (96 / DPI)
```

**Logical to Physical:**
```
Physical Pixels = Logical Pixels × (DPI / 96)
```

**Example**: At 120 DPI (125% scaling):
- Logical coordinate (100, 48) → Physical coordinate (125, 60)
- Calculation: 100 × (120/96) = 125, 48 × (120/96) = 60

---

## 2. Mouse Position and Input APIs

### 2.1 GetCursorPos

**Function Signature:**
```cpp
BOOL GetCursorPos(LPPOINT lpPoint);
```

**Key Characteristics:**
- Retrieves the position of the mouse cursor in **screen coordinates**
- Returns **logical coordinates** when DPI virtualization is active
- Returns **physical coordinates** when the process is DPI-aware
- Coordinates are relative to the upper-left corner of the screen (0, 0)

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getcursorpos

### 2.2 GetPhysicalCursorPos

**Function Signature:**
```cpp
BOOL GetPhysicalCursorPos(LPPOINT lpPoint);
```

**Key Characteristics:**
- Returns coordinates in **physical (raw, unscaled) pixels**
- Always returns true hardware pixel coordinates regardless of DPI awareness
- Essential for automation tools that need precise positioning
- Critical for mouse hooks that report physical coordinates

**When to Use:**
- When you need actual screen pixels regardless of DPI settings
- In DPI-aware applications working with UI Automation
- For accurate cross-monitor mouse positioning

### 2.3 SetCursorPos

**Function Signature:**
```cpp
BOOL SetCursorPos(int X, int Y);
```

**Key Characteristics:**
- Sets the cursor position in **screen coordinates**
- Expects **logical coordinates** for DPI-unaware applications
- Expects **physical coordinates** for DPI-aware applications
- The cursor is a shared resource; any application can move it

### 2.4 mouse_event (Deprecated)

**Status:** Superseded by SendInput. Microsoft recommends using SendInput instead.

**Function Signature:**
```cpp
VOID mouse_event(
  DWORD     dwFlags,
  DWORD     dx,
  DWORD     dy,
  DWORD     dwData,
  ULONG_PTR dwExtraInfo
);
```

### 2.5 SendInput (Recommended)

**Function Signature:**
```cpp
UINT SendInput(
  UINT    cInputs,
  LPINPUT pInputs,
  int     cbSize
);
```

**MOUSEINPUT Structure:**
```cpp
typedef struct tagMOUSEINPUT {
  LONG      dx;
  LONG      dy;
  DWORD     mouseData;
  DWORD     dwFlags;
  DWORD     time;
  ULONG_PTR dwExtraInfo;
} MOUSEINPUT;
```

**Key Flags:**

| Flag | Description |
|------|-------------|
| MOUSEEVENTF_MOVE | Movement occurred |
| MOUSEEVENTF_ABSOLUTE | dx and dy contain normalized absolute coordinates |
| MOUSEEVENTF_VIRTUALDESK | Coordinates map to entire virtual desktop (multi-monitor) |
| MOUSEEVENTF_LEFTDOWN | Left button down |
| MOUSEEVENTF_LEFTUP | Left button up |
| MOUSEEVENTF_RIGHTDOWN | Right button down |
| MOUSEEVENTF_RIGHTUP | Right button up |

**Coordinate Normalization with MOUSEEVENTF_ABSOLUTE:**

When MOUSEEVENTF_ABSOLUTE is specified, dx and dy contain **normalized absolute coordinates between 0 and 65,535**.

- Coordinate (0, 0) maps to the upper-left corner
- Coordinate (65,535, 65,535) maps to the lower-right corner
- **65,535 = 0xFFFF** (maximum value of unsigned 16-bit integer)

**Conversion Formula (Single Monitor):**
```cpp
normalizedX = (pixelX * 65535) / screenWidth
normalizedY = (pixelY * 65535) / screenHeight
```

**Improved Precision Formula:**
```cpp
normalizedX = (pixelX * 0xFFFF) / screenWidth + 1
normalizedY = (pixelY * 0xFFFF) / screenHeight + 1
```

**How Windows Processes It:**
```cpp
// Internal Windows calculation
actualX = (normalizedX * screenWidth) / 65536
actualY = (normalizedY * screenHeight) / 65536
```

**Multi-Monitor Behavior:**
- **Without MOUSEEVENTF_VIRTUALDESK**: Coordinates map to the primary monitor only
- **With MOUSEEVENTF_VIRTUALDESK**: Coordinates map to the entire virtual desktop

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput

---

## 3. Coordinate Transformations

### 3.1 Screen ↔ Client Conversions

#### ClientToScreen

**Function Signature:**
```cpp
BOOL ClientToScreen(
  HWND    hWnd,
  LPPOINT lpPoint
);
```

**Behavior:**
- Converts client-area coordinates to screen coordinates
- Client coordinates are relative to the upper-left corner of the window's client area
- Screen coordinates are relative to the upper-left corner of the screen
- All coordinates are in **device units** (affected by DPI awareness)

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-clienttoscreen

#### ScreenToClient

**Function Signature:**
```cpp
BOOL ScreenToClient(
  HWND    hWnd,
  LPPOINT lpPoint
);
```

**Behavior:**
- Converts screen coordinates to client-area coordinates
- New coordinates are relative to the upper-left corner of the specified window's client area
- All coordinates are in **device units**

**Important Note:**
Do not use ScreenToClient in mirroring situations (left-to-right to right-to-left layout changes). Use MapWindowPoints instead.

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-screentoclient

### 3.2 Logical ↔ Physical Conversions

#### LogicalToPhysicalPoint

**Function Signature:**
```cpp
BOOL LogicalToPhysicalPoint(
  HWND   hWnd,
  LPPOINT lpPoint
);
```

**Behavior:**
- Converts logical coordinates to physical coordinates
- Specifically designed for DPI awareness scenarios
- Desktop Window Manager (DWM) scales non-DPI-aware windows when display is high DPI

**Important Change in Windows 8.1+:**
Starting with Windows 8.1, LogicalToPhysicalPoint and PhysicalToLogicalPoint no longer transform points. The system returns all points to an application in its own coordinate space. These functions effectively become no-ops for modern applications.

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-logicaltophysicalpoint

#### PhysicalToLogicalPoint

**Function Signature:**
```cpp
BOOL PhysicalToLogicalPoint(
  HWND   hWnd,
  LPPOINT lpPoint
);
```

**Behavior:**
- Converts physical coordinates to logical coordinates
- Used for inter-process communication with non-DPI-aware applications

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-physicaltologicalpoint

#### PhysicalToLogicalPointForPerMonitorDPI (Windows 8.1+)

**Function Signature:**
```cpp
BOOL PhysicalToLogicalPointForPerMonitorDPI(
  HWND   hwnd,
  LPPOINT lpPoint
);
```

**Use Case:**
For converting coordinates between DPI-unaware and per-monitor-aware applications. For example, if a DPI-unaware app needs coordinates that match a per-monitor-aware app's window, it can call this function.

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-physicaltologicalpointforpermonitordpi

### 3.3 MapWindowPoints

**Function Signature:**
```cpp
int MapWindowPoints(
  HWND hWndFrom,
  HWND hWndTo,
  LPPOINT lpPoints,
  UINT cPoints
);
```

**Use Case:**
- Converts points from one window's coordinate space to another
- Preferred over ScreenToClient for mirroring situations
- Can handle multiple points in a single call

---

## 4. High DPI Awareness Modes

### 4.1 DPI Awareness Modes Overview

Windows supports several DPI awareness modes that fundamentally change how coordinates are reported:

| Mode | Introduced | Behavior |
|------|-----------|----------|
| **DPI Unaware** | Windows Vista | Always rendered at 100% scaling (96 DPI). Windows bitmap-scales the application on high-DPI displays. |
| **System DPI Aware** | Windows Vista | Aware of DPI at login time. Uses system DPI for all monitors. |
| **Per-Monitor DPI Aware** | Windows 8.1 | Can render at different DPIs for each monitor. |
| **Per-Monitor V2 (PMv2)** | Windows 10 1703 | **Recommended**. Enhanced per-monitor awareness with improved scaling behaviors. |

### 4.2 Per-Monitor V2 (PMv2) - Recommended Mode

**Availability:** Windows 10 version 1703 (Creators Update) and later

**Key Benefits:**
- Applications see the **raw physical pixels** of each display
- **Never bitmap-scaled** by Windows
- Enables per-top-level-window DPI scaling
- Supports automatic non-client area DPI scaling
- Best for modern desktop applications

**Setting PMv2 via Application Manifest:**
```xml
<application xmlns="urn:schemas-microsoft-com:asm.v3">
  <windowsSettings>
    <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true/PM</dpiAware>
    <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
  </windowsSettings>
</application>
```

**Setting PMv2 via Code:**
```cpp
SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);
```

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/hidpi/high-dpi-desktop-application-development-on-windows

### 4.3 Coordinate Virtualization by Mode

#### DPI Unaware Mode
- Windows virtualizes all coordinate information
- APIs return coordinates as if screen were 96 DPI
- Example: On a 4K monitor at 200% scaling, GetCursorPos returns (960, 540) when physical position is (1920, 1080)

#### System DPI Aware Mode
- APIs return coordinates based on system DPI at login
- If display DPI changes or differs across monitors, Windows scales coordinates
- Can lead to blur on high-DPI monitors

#### Per-Monitor Aware / PMv2 Mode
- APIs return **physical coordinates** directly
- No coordinate virtualization by Windows
- Application responsible for handling DPI scaling
- **Most accurate for automation and clicking**

### 4.4 DPI_AWARENESS_CONTEXT

**Available Contexts:**

```cpp
DPI_AWARENESS_CONTEXT_UNAWARE
DPI_AWARENESS_CONTEXT_SYSTEM_AWARE
DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE
DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
DPI_AWARENESS_CONTEXT_UNAWARE_GDISCALED
```

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/hidpi/dpi-awareness-context

### 4.5 Thread-Level DPI Awareness

#### SetThreadDpiAwarenessContext

**Function Signature:**
```cpp
DPI_AWARENESS_CONTEXT SetThreadDpiAwarenessContext(
  DPI_AWARENESS_CONTEXT dpiContext
);
```

**Introduced:** Windows 10 Anniversary Update (1607)

**Key Features:**
- Sets DPI awareness for the **current thread only**
- Returns the old context (use to restore later)
- Each thread can have individual DPI awareness
- Can be changed at any time during execution

**Common Pattern:**
```cpp
// Save current context
DPI_AWARENESS_CONTEXT previousContext = SetThreadDpiAwarenessContext(
    DPI_AWARENESS_CONTEXT_UNAWARE
);

// Create window or perform operations
CreateWindow(...);

// Restore previous context
SetThreadDpiAwarenessContext(previousContext);
```

**Automatic Context Switching:**
When a window procedure is called, the thread is **automatically switched** to the DPI awareness context that was active when the window was created.

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setthreaddpiawarenesscontext

### 4.6 Getting DPI Values

#### GetDpiForWindow (Recommended)

**Function Signature:**
```cpp
UINT GetDpiForWindow(HWND hwnd);
```

**Introduced:** Windows 10 1607

**Returns:** DPI value for the specified window (96, 120, 144, 192, etc.)

**This is the recommended API for modern applications.**

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getdpiforwindow

#### GetDpiForMonitor

**Function Signature:**
```cpp
HRESULT GetDpiForMonitor(
  HMONITOR         hmonitor,
  MONITOR_DPI_TYPE dpiType,
  UINT             *dpiX,
  UINT             *dpiY
);
```

**Note:** Not DPI-aware itself. Should not be used if calling thread is per-monitor DPI-aware. Use GetDpiForWindow instead.

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/api/shellscalingapi/nf-shellscalingapi-getdpiformonitor

#### GetDpiForSystem

**Function Signature:**
```cpp
UINT GetDpiForSystem();
```

**Returns:** System DPI value

**More efficient than:**
```cpp
HDC hdc = GetDC(NULL);
int dpi = GetDeviceCaps(hdc, LOGPIXELSX);
ReleaseDC(NULL, hdc);
```

**Note:** Returns system DPI relative to the DPI-awareness mode of the calling thread.

### 4.7 Scaling Calculations with MulDiv

**Recommended Pattern:**
```cpp
// Scale value based on DPI
int scaledValue = MulDiv(originalValue, currentDPI, 96);

// Example: Scale 100 pixels for 144 DPI
int scaled = MulDiv(100, 144, 96); // Result: 150
```

---

## 5. Multi-Monitor Coordinate Systems

### 5.1 Virtual Screen Concept

All enabled monitors form a **single virtual desktop**:
- The primary monitor is at position **(0, 0)**
- Monitors can be positioned in any arrangement
- Monitors to the **left** of the primary have **negative X coordinates**
- Monitors **above** the primary have **negative Y coordinates**

**Example Configuration:**
```
Monitor 2 (1920x1080)    Monitor 1 [Primary] (1920x1080)
Position: (-1920, 0)     Position: (0, 0)
Range: -1920 to -1       Range: 0 to 1919
```

### 5.2 Virtual Screen Metrics

**GetSystemMetrics Values:**

| Metric | Description |
|--------|-------------|
| SM_XVIRTUALSCREEN | X-coordinate of upper-left corner of virtual screen |
| SM_YVIRTUALSCREEN | Y-coordinate of upper-left corner of virtual screen |
| SM_CXVIRTUALSCREEN | Width of virtual screen in pixels |
| SM_CYVIRTUALSCREEN | Height of virtual screen in pixels |
| SM_CMONITORS | Number of monitors attached to desktop |
| SM_SAMEDISPLAYFORMAT | Whether all monitors have same color format |

**Example Usage:**
```cpp
int virtualLeft = GetSystemMetrics(SM_XVIRTUALSCREEN);
int virtualTop = GetSystemMetrics(SM_YVIRTUALSCREEN);
int virtualWidth = GetSystemMetrics(SM_CXVIRTUALSCREEN);
int virtualHeight = GetSystemMetrics(SM_CYVIRTUALSCREEN);
int monitorCount = GetSystemMetrics(SM_CMONITORS);
```

**Critical DPI Note:**
GetSystemMetrics is **not DPI-aware**. When the calling thread is per-monitor DPI-aware, use **GetSystemMetricsForDPI** instead to get accurate values.

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/gdi/multiple-monitor-system-metrics

### 5.3 Monitor Enumeration

#### EnumDisplayMonitors

**Function Signature:**
```cpp
BOOL EnumDisplayMonitors(
  HDC             hdc,
  LPCRECT         lprcClip,
  MONITORENUMPROC lpfnEnum,
  LPARAM          dwData
);
```

**Behavior:**
- If `hdc` is NULL, enumerates all visible monitors
- If `hdc` is non-NULL, enumerates monitors that intersect with the clipping rectangle
- If `hdc` is NULL, coordinates are **virtual-screen coordinates**
- If `hdc` is non-NULL, coordinates are relative to the device context origin

**Callback Function:**
```cpp
BOOL CALLBACK MonitorEnumProc(
  HMONITOR hMonitor,
  HDC      hdcMonitor,
  LPRECT   lprcMonitor,
  LPARAM   dwData
);
```

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumdisplaymonitors

#### MonitorFromPoint

**Function Signature:**
```cpp
HMONITOR MonitorFromPoint(
  POINT pt,
  DWORD dwFlags
);
```

**Parameters:**
- `pt`: Point in **virtual-screen coordinates**
- `dwFlags`: MONITOR_DEFAULTTONULL, MONITOR_DEFAULTTOPRIMARY, or MONITOR_DEFAULTTONEAREST

**Returns:** Handle to the monitor that contains the point

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-monitorfrompoint

#### MonitorFromWindow

**Function Signature:**
```cpp
HMONITOR MonitorFromWindow(
  HWND  hwnd,
  DWORD dwFlags
);
```

**Returns:** Handle to the monitor that has the largest intersection with the window

#### MonitorFromRect

**Function Signature:**
```cpp
HMONITOR MonitorFromRect(
  LPCRECT lprc,
  DWORD   dwFlags
);
```

**Returns:** Handle to the monitor that has the largest intersection with the rectangle

### 5.4 Getting Monitor Information

#### GetMonitorInfo

**Function Signature:**
```cpp
BOOL GetMonitorInfo(
  HMONITOR      hMonitor,
  LPMONITORINFO lpmi
);
```

**MONITORINFO Structure:**
```cpp
typedef struct tagMONITORINFO {
  DWORD cbSize;
  RECT  rcMonitor;    // Display monitor rectangle (virtual-screen coordinates)
  RECT  rcWork;       // Work area rectangle (excludes taskbar)
  DWORD dwFlags;      // MONITORINFOF_PRIMARY if primary monitor
} MONITORINFO;
```

**Example:**
```cpp
MONITORINFO mi = { sizeof(mi) };
if (GetMonitorInfo(hMonitor, &mi)) {
    // mi.rcMonitor contains the full monitor rectangle
    // mi.rcWork contains the work area (without taskbar)
    bool isPrimary = (mi.dwFlags & MONITORINFOF_PRIMARY) != 0;
}
```

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getmonitorinfoa

### 5.5 SendInput Multi-Monitor Coordinates

**With MOUSEEVENTF_VIRTUALDESK:**

To accurately click across multiple monitors:

```cpp
// Get virtual screen metrics
int virtualLeft = GetSystemMetrics(SM_XVIRTUALSCREEN);
int virtualTop = GetSystemMetrics(SM_YVIRTUALSCREEN);
int virtualWidth = GetSystemMetrics(SM_CXVIRTUALSCREEN);
int virtualHeight = GetSystemMetrics(SM_CYVIRTUALSCREEN);

// Adjust target coordinates to virtual space
int adjustedX = targetX - virtualLeft;
int adjustedY = targetY - virtualTop;

// Normalize to 0-65535 range
int normalizedX = (adjustedX * 65535) / virtualWidth;
int normalizedY = (adjustedY * 65535) / virtualHeight;

INPUT input = {0};
input.type = INPUT_MOUSE;
input.mi.dx = normalizedX;
input.mi.dy = normalizedY;
input.mi.dwFlags = MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK | MOUSEEVENTF_MOVE;
SendInput(1, &input, sizeof(INPUT));
```

**Key Points:**
- **Always use MOUSEEVENTF_VIRTUALDESK** for multi-monitor setups
- Account for negative coordinates (monitors to the left/above primary)
- Use GetSystemMetrics to get virtual screen dimensions

**DPI Consideration:**
When per-monitor DPI-aware, different monitors may have different DPI values. Ensure you're using physical coordinates consistently.

---

## 6. Windows Accessibility APIs

### 6.1 UI Automation (UIA) - Recommended

**Overview:**
- Modern accessibility API introduced with Windows Vista
- Replacement for MSAA (Microsoft Active Accessibility)
- Provides rich information about UI elements
- **Works in physical screen coordinates**

**Important:** The UI Automation API does **not** use logical coordinates. All methods and properties either return physical coordinates or take them as parameters.

#### BoundingRectangle Property

**Purpose:** Returns the bounding rectangle of a UI element

**.NET Property:**
```csharp
AutomationElement.BoundingRectangleProperty
```

**Returns:** Rectangle in **physical screen coordinates**

**Type:** `System.Windows.Rect`

**Key Characteristics:**
- Coordinates are in **physical pixels**
- If element is not visible, returns rectangle of all zeros
- May contain non-clickable points (irregular shapes, occlusion by other elements)
- Automatically updated with absolute screen coordinates

**Example Usage:**
```csharp
AutomationElement element = ...;
Rect bounds = element.Current.BoundingRectangle;

// bounds.X and bounds.Y are in physical screen coordinates
int centerX = (int)(bounds.X + bounds.Width / 2);
int centerY = (int)(bounds.Y + bounds.Height / 2);
```

**Official Documentation:**
https://learn.microsoft.com/en-us/dotnet/api/system.windows.automation.automationelement.boundingrectangleproperty

#### ElementFromPoint

**Function Signature:**
```csharp
AutomationElement ElementFromPoint(Point pt);
```

**Parameters:**
- `pt`: Point in **physical screen coordinates**

**Returns:** The UI automation element at the specified point

**Example:**
```csharp
Point screenPoint = new Point(physicalX, physicalY);
AutomationElement element = AutomationElement.FromPoint(screenPoint);
```

**Official Documentation:**
https://learn.microsoft.com/en-us/dotnet/api/system.windows.automation.automationelement.frompoint

#### Coordinate Conversion for UI Automation

**Critical Issue:**
UI Automation uses physical coordinates, but GetCursorPos may return logical coordinates depending on DPI awareness mode.

**Solution:**
```csharp
// Import GetPhysicalCursorPos
[DllImport("user32.dll")]
static extern bool GetPhysicalCursorPos(out Point lpPoint);

// Get cursor position in physical coordinates
Point physicalCursor;
GetPhysicalCursorPos(out physicalCursor);

// Use with UI Automation
AutomationElement element = AutomationElement.FromPoint(physicalCursor);
```

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-screenscaling

### 6.2 MSAA (Microsoft Active Accessibility)

**Status:** Legacy API, superseded by UI Automation. Still supported for backward compatibility.

#### IAccessible::accLocation

**Purpose:** Retrieves object's current screen location

**Method Signature:**
```cpp
HRESULT accLocation(
  long *pxLeft,
  long *pyTop,
  long *pcxWidth,
  long *pcyHeight,
  VARIANT varChild
);
```

**Parameters:**
- `pxLeft`: X-coordinate of upper-left boundary in **physical screen coordinates**
- `pyTop`: Y-coordinate of upper-left boundary in **physical screen coordinates**
- `pcxWidth`: Width in pixels
- `pcyHeight`: Height in pixels

**Key Points:**
- Returns **bounding rectangle**, not exact bounds
- All visual objects must support this method
- Coordinates are **physical screen pixels**
- Some points within rectangle may not be on the actual object

**Calculate Right/Bottom:**
```cpp
right = left + width;
bottom = top + height;
```

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/api/oleacc/nf-oleacc-iaccessible-acclocation

#### IAccessible::accHitTest

**Purpose:** Identifies the child element at a specific screen location

**Method Signature:**
```cpp
HRESULT accHitTest(
  long xLeft,
  long yTop,
  VARIANT *pvarChild
);
```

**Parameters:**
- `xLeft`: X-coordinate in **screen coordinates**
- `yTop`: Y-coordinate in **screen coordinates**

**Official Documentation:**
https://learn.microsoft.com/en-us/windows/win32/api/oleacc/nf-oleacc-iaccessible-acchittest

### 6.3 DPI Awareness for Accessibility APIs

**Critical Rule:**
When using accessibility APIs for automation:

1. **Make your application DPI-aware** by calling `SetProcessDPIAware()` at startup
2. **Use GetPhysicalCursorPos** instead of GetCursorPos for cursor coordinates
3. **Pass physical coordinates** to UI Automation APIs
4. **Convert coordinates** when communicating with non-DPI-aware applications using:
   - `PhysicalToLogicalPoint`
   - `LogicalToPhysicalPoint`
   - `PhysicalToLogicalPointForPerMonitorDPI`

**Example:**
```cpp
// At application startup
SetProcessDPIAware();

// Getting cursor position for UI Automation
POINT physicalCursor;
GetPhysicalCursorPos(&physicalCursor);

// Use physical coordinates with UI Automation
IUIAutomationElement* element;
uiAutomation->ElementFromPoint(physicalCursor, &element);
```

---

## 7. Common Pitfalls and Best Practices

### 7.1 Critical Pitfalls

#### Pitfall 1: Mixing Logical and Physical Coordinates

**Problem:**
Different APIs return coordinates in different spaces depending on DPI awareness mode:
- `GetCursorPos`: Returns logical coordinates (DPI-unaware) or physical coordinates (DPI-aware)
- `GetPhysicalCursorPos`: Always returns physical coordinates
- UI Automation APIs: Always use physical coordinates
- MSAA APIs: Use physical coordinates

**Solution:**
- Be consistent: Always know which coordinate space you're in
- Document coordinate space in variable names: `physicalX`, `logicalX`
- Use appropriate conversion functions

#### Pitfall 2: DPI Virtualization Confusion

**Problem:**
When a DPI-unaware application queries screen size on high-DPI display:
- Windows virtualizes the answer as if screen were 96 DPI
- A 4K monitor (3840×2160) at 150% scaling appears as 2560×1440

**Example:**
```cpp
// DPI-unaware application on 4K monitor at 150% scaling
int width = GetSystemMetrics(SM_CXSCREEN);   // Returns 2560 (not 3840!)
int height = GetSystemMetrics(SM_CYSCREEN);  // Returns 1440 (not 2160!)
```

**Solution:**
- Declare application as DPI-aware
- Use `GetSystemMetricsForDPI` for specific DPI values

#### Pitfall 3: Multi-Monitor Virtual Screen Offset

**Problem:**
Virtual screen origin may not be (0, 0) if primary monitor is not the leftmost/topmost monitor.

**Example:**
```
[Monitor 2]  [Monitor 1 Primary]
Virtual Screen: X from -1920 to 1919, Y from 0 to 1079
```

**Solution:**
```cpp
int virtualLeft = GetSystemMetrics(SM_XVIRTUALSCREEN);  // May be negative!
int virtualTop = GetSystemMetrics(SM_YVIRTUALSCREEN);   // May be negative!

// Adjust coordinates relative to virtual screen origin
int adjustedX = targetX - virtualLeft;
int adjustedY = targetY - virtualTop;
```

#### Pitfall 4: Mouse Hook Coordinate Mismatch

**Problem:**
When a DPI-aware process uses mouse hooks, `GetCursorPos()` in the hook callback returns **raw physical coordinates**, not logical coordinates. This causes `WindowFromPoint` to fail when applications share the same point.

**Solution:**
Use `GetPhysicalCursorPos` consistently, or convert coordinates based on the target window's DPI awareness.

#### Pitfall 5: Client vs. Screen Coordinates

**Problem:**
Window messages (like `WM_MOUSEMOVE`) return client-area coordinates, while `GetCursorPos` returns screen coordinates.

**Solution:**
```cpp
// Converting message coordinates to screen
POINT pt = {GET_X_LPARAM(lParam), GET_Y_LPARAM(lParam)};
ClientToScreen(hwnd, &pt);

// Converting screen to client
POINT screenPt;
GetCursorPos(&screenPt);
ScreenToClient(hwnd, &screenPt);
```

#### Pitfall 6: SendInput Coordinate Range

**Problem:**
When using `MOUSEEVENTF_ABSOLUTE`, coordinates must be normalized to 0-65535, not pixel values.

**Wrong:**
```cpp
input.mi.dx = 100;  // Wrong! This is not a pixel coordinate
input.mi.dy = 100;
```

**Correct:**
```cpp
input.mi.dx = (100 * 65535) / screenWidth;
input.mi.dy = (100 * 65535) / screenHeight;
```

### 7.2 Best Practices for Accurate Clicking

#### Practice 1: Declare DPI Awareness

**Application Manifest:**
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0" xmlns:asmv3="urn:schemas-microsoft-com:asm.v3">
  <asmv3:application>
    <asmv3:windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true/PM</dpiAware>
      <dpiAwareness xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">PerMonitorV2</dpiAwareness>
    </asmv3:windowsSettings>
  </asmv3:application>
</assembly>
```

**Or via Code (at startup):**
```cpp
// Windows 10 1703+ (Recommended)
SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);

// Or for older Windows versions
SetProcessDPIAware();
```

#### Practice 2: Use Physical Coordinates Consistently

```cpp
// Get physical cursor position
POINT cursor;
GetPhysicalCursorPos(&cursor);

// Get physical screen bounds
int screenWidth = GetSystemMetricsForDPI(SM_CXSCREEN, GetDpiForSystem());
int screenHeight = GetSystemMetricsForDPI(SM_CYSCREEN, GetDpiForSystem());

// Or for per-monitor DPI-aware applications
HMONITOR monitor = MonitorFromPoint(cursor, MONITOR_DEFAULTTONEAREST);
UINT dpiX, dpiY;
GetDpiForMonitor(monitor, MDT_EFFECTIVE_DPI, &dpiX, &dpiY);
```

#### Practice 3: Multi-Monitor Clicking

**Complete Example:**
```cpp
void ClickAtPhysicalCoordinate(int physicalX, int physicalY) {
    // Get virtual screen bounds
    int virtualLeft = GetSystemMetrics(SM_XVIRTUALSCREEN);
    int virtualTop = GetSystemMetrics(SM_YVIRTUALSCREEN);
    int virtualWidth = GetSystemMetrics(SM_CXVIRTUALSCREEN);
    int virtualHeight = GetSystemMetrics(SM_CYVIRTUALSCREEN);

    // Adjust for virtual screen offset
    int adjustedX = physicalX - virtualLeft;
    int adjustedY = physicalY - virtualTop;

    // Normalize to 0-65535
    int normalizedX = (adjustedX * 65535) / virtualWidth;
    int normalizedY = (adjustedY * 65535) / virtualHeight;

    // Move mouse
    INPUT moveInput = {0};
    moveInput.type = INPUT_MOUSE;
    moveInput.mi.dx = normalizedX;
    moveInput.mi.dy = normalizedY;
    moveInput.mi.dwFlags = MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK | MOUSEEVENTF_MOVE;
    SendInput(1, &moveInput, sizeof(INPUT));

    // Click
    INPUT clickInput[2] = {0};
    clickInput[0].type = INPUT_MOUSE;
    clickInput[0].mi.dwFlags = MOUSEEVENTF_LEFTDOWN;
    clickInput[1].type = INPUT_MOUSE;
    clickInput[1].mi.dwFlags = MOUSEEVENTF_LEFTUP;
    SendInput(2, clickInput, sizeof(INPUT));
}
```

#### Practice 4: UI Element Clicking

**Using UI Automation:**
```csharp
// Make application DPI-aware
[DllImport("user32.dll")]
static extern bool SetProcessDPIAware();

static void Main() {
    SetProcessDPIAware();

    // Get UI element
    AutomationElement element = FindElement();

    // Get bounding rectangle (physical coordinates)
    Rect bounds = element.Current.BoundingRectangle;

    // Calculate center
    int centerX = (int)(bounds.X + bounds.Width / 2);
    int centerY = (int)(bounds.Y + bounds.Height / 2);

    // Click at center
    ClickAtPhysicalCoordinate(centerX, centerY);
}
```

#### Practice 5: Handle DPI Changes Dynamically

**Listen for DPI changes:**
```cpp
case WM_DPICHANGED: {
    UINT newDPI = HIWORD(wParam);
    RECT* suggestedRect = (RECT*)lParam;

    // Update scaling
    float scaleFactor = newDPI / 96.0f;

    // Reposition window
    SetWindowPos(hwnd, NULL,
        suggestedRect->left,
        suggestedRect->top,
        suggestedRect->right - suggestedRect->left,
        suggestedRect->bottom - suggestedRect->top,
        SWP_NOZORDER | SWP_NOACTIVATE);

    return 0;
}
```

#### Practice 6: Verify Coordinates Before Clicking

```cpp
bool VerifyClickTarget(int x, int y, HWND expectedWindow) {
    // Convert to POINT
    POINT pt = {x, y};

    // Get window at point
    HWND hwndAtPoint = WindowFromPoint(pt);

    // Verify it's the expected window
    if (hwndAtPoint != expectedWindow) {
        // May need to convert to child window
        ScreenToClient(expectedWindow, &pt);
        HWND child = ChildWindowFromPoint(expectedWindow, pt);
        return child != NULL;
    }

    return true;
}
```

#### Practice 7: Account for Window Borders and Title Bars

```cpp
// Get window rectangle (includes non-client area)
RECT windowRect;
GetWindowRect(hwnd, &windowRect);

// Get client rectangle
RECT clientRect;
GetClientRect(hwnd, &clientRect);

// Convert client to screen
POINT clientTopLeft = {0, 0};
ClientToScreen(hwnd, &clientTopLeft);

// Calculate non-client area offsets
int leftBorder = clientTopLeft.x - windowRect.left;
int topBorder = clientTopLeft.y - windowRect.top;
```

### 7.3 Testing Checklist

When implementing clicking automation, test:

- [ ] **Single monitor** at 100% scaling (96 DPI)
- [ ] **Single monitor** at 125% scaling (120 DPI)
- [ ] **Single monitor** at 150% scaling (144 DPI)
- [ ] **Single monitor** at 200% scaling (192 DPI)
- [ ] **Multi-monitor** with same DPI on all monitors
- [ ] **Multi-monitor** with different DPI per monitor
- [ ] **Primary monitor on the right** (negative X coordinates for left monitor)
- [ ] **Primary monitor in the middle**
- [ ] **Click targets in DPI-aware applications**
- [ ] **Click targets in DPI-unaware applications**
- [ ] **Window movement between monitors** (DPI change events)
- [ ] **Minimized and maximized windows**
- [ ] **Remote Desktop scenarios**

---

## 8. Code Examples and Formulas

### 8.1 Quick Reference Formulas

#### DPI Calculations

```cpp
// Scaling percentage to DPI
int dpi = 96 * (scalingPercentage / 100);

// DPI to scaling percentage
int percentage = (dpi / 96) * 100;

// Physical to logical pixels
int logical = physical * 96 / dpi;

// Logical to physical pixels
int physical = logical * dpi / 96;

// Scale value using MulDiv (recommended)
int scaled = MulDiv(value, currentDPI, 96);
```

#### SendInput Normalization

```cpp
// Single monitor
int normalizedX = (pixelX * 65535) / screenWidth;
int normalizedY = (pixelY * 65535) / screenHeight;

// Multi-monitor (with MOUSEEVENTF_VIRTUALDESK)
int virtualLeft = GetSystemMetrics(SM_XVIRTUALSCREEN);
int virtualTop = GetSystemMetrics(SM_YVIRTUALSCREEN);
int virtualWidth = GetSystemMetrics(SM_CXVIRTUALSCREEN);
int virtualHeight = GetSystemMetrics(SM_CYVIRTUALSCREEN);

int adjustedX = targetX - virtualLeft;
int adjustedY = targetY - virtualTop;
int normalizedX = (adjustedX * 65535) / virtualWidth;
int normalizedY = (adjustedY * 65535) / virtualHeight;
```

### 8.2 Complete Click Implementation (C++)

```cpp
#include <windows.h>

// DPI-aware click function
bool ClickAtCoordinate(int x, int y) {
    // Ensure DPI awareness (call once at startup)
    static bool dpiAwareSet = false;
    if (!dpiAwareSet) {
        SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);
        dpiAwareSet = true;
    }

    // Get virtual screen dimensions
    int virtualLeft = GetSystemMetrics(SM_XVIRTUALSCREEN);
    int virtualTop = GetSystemMetrics(SM_YVIRTUALSCREEN);
    int virtualWidth = GetSystemMetrics(SM_CXVIRTUALSCREEN);
    int virtualHeight = GetSystemMetrics(SM_CYVIRTUALSCREEN);

    // Adjust coordinates for virtual screen offset
    int adjustedX = x - virtualLeft;
    int adjustedY = y - virtualTop;

    // Normalize to 0-65535 range
    int normalizedX = (adjustedX * 65535) / virtualWidth;
    int normalizedY = (adjustedY * 65535) / virtualHeight;

    // Move mouse to position
    INPUT input = {0};
    input.type = INPUT_MOUSE;
    input.mi.dx = normalizedX;
    input.mi.dy = normalizedY;
    input.mi.dwFlags = MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK | MOUSEEVENTF_MOVE;

    if (SendInput(1, &input, sizeof(INPUT)) != 1) {
        return false;
    }

    // Small delay to ensure mouse has moved
    Sleep(10);

    // Click (down then up)
    INPUT clicks[2] = {0};
    clicks[0].type = INPUT_MOUSE;
    clicks[0].mi.dwFlags = MOUSEEVENTF_LEFTDOWN;
    clicks[1].type = INPUT_MOUSE;
    clicks[1].mi.dwFlags = MOUSEEVENTF_LEFTUP;

    return SendInput(2, clicks, sizeof(INPUT)) == 2;
}

// Get physical cursor position
bool GetPhysicalCursor(int* x, int* y) {
    POINT pt;
    if (!GetPhysicalCursorPos(&pt)) {
        return false;
    }
    *x = pt.x;
    *y = pt.y;
    return true;
}

// Get monitor DPI
int GetMonitorDPI(HMONITOR monitor) {
    UINT dpiX, dpiY;
    if (SUCCEEDED(GetDpiForMonitor(monitor, MDT_EFFECTIVE_DPI, &dpiX, &dpiY))) {
        return dpiX;
    }
    return 96; // Default
}

// Get DPI for a specific point
int GetDPIAtPoint(int x, int y) {
    POINT pt = {x, y};
    HMONITOR monitor = MonitorFromPoint(pt, MONITOR_DEFAULTTONEAREST);
    return GetMonitorDPI(monitor);
}
```

### 8.3 Complete Click Implementation (C#)

```csharp
using System;
using System.Runtime.InteropServices;
using System.Windows.Automation;

public class AccurateClicker {
    [DllImport("user32.dll")]
    private static extern bool SetProcessDPIAware();

    [DllImport("user32.dll")]
    private static extern bool GetPhysicalCursorPos(out POINT lpPoint);

    [DllImport("user32.dll")]
    private static extern int GetSystemMetrics(int nIndex);

    [DllImport("user32.dll")]
    private static extern uint SendInput(uint nInputs, INPUT[] pInputs, int cbSize);

    [StructLayout(LayoutKind.Sequential)]
    public struct POINT {
        public int X;
        public int Y;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct INPUT {
        public uint type;
        public MOUSEINPUT mi;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct MOUSEINPUT {
        public int dx;
        public int dy;
        public uint mouseData;
        public uint dwFlags;
        public uint time;
        public IntPtr dwExtraInfo;
    }

    private const uint INPUT_MOUSE = 0;
    private const uint MOUSEEVENTF_MOVE = 0x0001;
    private const uint MOUSEEVENTF_ABSOLUTE = 0x8000;
    private const uint MOUSEEVENTF_VIRTUALDESK = 0x4000;
    private const uint MOUSEEVENTF_LEFTDOWN = 0x0002;
    private const uint MOUSEEVENTF_LEFTUP = 0x0004;

    private const int SM_XVIRTUALSCREEN = 76;
    private const int SM_YVIRTUALSCREEN = 77;
    private const int SM_CXVIRTUALSCREEN = 78;
    private const int SM_CYVIRTUALSCREEN = 79;

    static AccurateClicker() {
        // Make application DPI-aware
        SetProcessDPIAware();
    }

    public static bool ClickAtPhysicalCoordinate(int x, int y) {
        // Get virtual screen bounds
        int virtualLeft = GetSystemMetrics(SM_XVIRTUALSCREEN);
        int virtualTop = GetSystemMetrics(SM_YVIRTUALSCREEN);
        int virtualWidth = GetSystemMetrics(SM_CXVIRTUALSCREEN);
        int virtualHeight = GetSystemMetrics(SM_CYVIRTUALSCREEN);

        // Adjust for virtual screen offset
        int adjustedX = x - virtualLeft;
        int adjustedY = y - virtualTop;

        // Normalize to 0-65535
        int normalizedX = (adjustedX * 65535) / virtualWidth;
        int normalizedY = (adjustedY * 65535) / virtualHeight;

        // Move mouse
        INPUT[] moveInput = new INPUT[1];
        moveInput[0].type = INPUT_MOUSE;
        moveInput[0].mi.dx = normalizedX;
        moveInput[0].mi.dy = normalizedY;
        moveInput[0].mi.dwFlags = MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK | MOUSEEVENTF_MOVE;

        if (SendInput(1, moveInput, Marshal.SizeOf(typeof(INPUT))) != 1) {
            return false;
        }

        System.Threading.Thread.Sleep(10);

        // Click
        INPUT[] clickInputs = new INPUT[2];
        clickInputs[0].type = INPUT_MOUSE;
        clickInputs[0].mi.dwFlags = MOUSEEVENTF_LEFTDOWN;
        clickInputs[1].type = INPUT_MOUSE;
        clickInputs[1].mi.dwFlags = MOUSEEVENTF_LEFTUP;

        return SendInput(2, clickInputs, Marshal.SizeOf(typeof(INPUT))) == 2;
    }

    public static bool ClickUIElement(AutomationElement element) {
        // Get bounding rectangle (physical coordinates)
        System.Windows.Rect bounds = element.Current.BoundingRectangle;

        if (bounds.Width == 0 || bounds.Height == 0) {
            return false; // Element not visible
        }

        // Calculate center
        int centerX = (int)(bounds.X + bounds.Width / 2);
        int centerY = (int)(bounds.Y + bounds.Height / 2);

        // Click at center
        return ClickAtPhysicalCoordinate(centerX, centerY);
    }

    public static POINT GetPhysicalCursorPosition() {
        POINT pt;
        GetPhysicalCursorPos(out pt);
        return pt;
    }
}
```

### 8.4 Python Example (using ctypes)

```python
import ctypes
from ctypes import wintypes
import time

# Load user32.dll
user32 = ctypes.windll.user32

# Define structures
class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [("type", wintypes.DWORD), ("_input", _INPUT)]

# Constants
INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_VIRTUALDESK = 0x4000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

# Set DPI awareness
user32.SetProcessDPIAware()

def click_at_coordinate(x, y):
    """Click at physical screen coordinate (x, y)"""
    # Get virtual screen dimensions
    virtual_left = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    virtual_top = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
    virtual_width = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    virtual_height = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)

    # Adjust for virtual screen offset
    adjusted_x = x - virtual_left
    adjusted_y = y - virtual_top

    # Normalize to 0-65535
    normalized_x = (adjusted_x * 65535) // virtual_width
    normalized_y = (adjusted_y * 65535) // virtual_height

    # Move mouse
    move_input = INPUT()
    move_input.type = INPUT_MOUSE
    move_input.mi.dx = normalized_x
    move_input.mi.dy = normalized_y
    move_input.mi.dwFlags = MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK | MOUSEEVENTF_MOVE

    user32.SendInput(1, ctypes.byref(move_input), ctypes.sizeof(INPUT))
    time.sleep(0.01)

    # Click (down and up)
    click_down = INPUT()
    click_down.type = INPUT_MOUSE
    click_down.mi.dwFlags = MOUSEEVENTF_LEFTDOWN

    click_up = INPUT()
    click_up.type = INPUT_MOUSE
    click_up.mi.dwFlags = MOUSEEVENTF_LEFTUP

    inputs = (INPUT * 2)(click_down, click_up)
    user32.SendInput(2, ctypes.byref(inputs), ctypes.sizeof(INPUT))

def get_physical_cursor_pos():
    """Get physical cursor position"""
    pt = POINT()
    user32.GetPhysicalCursorPos(ctypes.byref(pt))
    return (pt.x, pt.y)

# Example usage
if __name__ == "__main__":
    # Click at physical coordinate (500, 300)
    click_at_coordinate(500, 300)

    # Get current cursor position
    x, y = get_physical_cursor_pos()
    print(f"Cursor at physical position: ({x}, {y})")
```

---

## References and Further Reading

### Official Microsoft Documentation

1. **High DPI Desktop Development**: https://learn.microsoft.com/en-us/windows/win32/hidpi/high-dpi-desktop-application-development-on-windows
2. **DPI and Device-Independent Pixels**: https://learn.microsoft.com/en-us/windows/win32/learnwin32/dpi-and-device-independent-pixels
3. **Mixed-Mode DPI Scaling**: https://learn.microsoft.com/en-us/windows/win32/hidpi/high-dpi-improvements-for-desktop-applications
4. **UI Automation and Screen Scaling**: https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-screenscaling
5. **Multiple Monitor Support**: https://learn.microsoft.com/en-us/windows/win32/gdi/multiple-monitor-system-metrics
6. **SendInput Function**: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput
7. **GetCursorPos Function**: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getcursorpos
8. **SetCursorPos Function**: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setcursorpos
9. **UI Automation Overview**: https://learn.microsoft.com/en-us/windows/win32/winauto/entry-uiauto-win32

### Community Resources

1. Stack Overflow: Multi-monitor SendInput discussions
2. Win32 DPI and Monitor Scaling Gist: https://gist.github.com/marler8997/9f39458d26e2d8521d48e36530fbb459
3. Virtual Screen Coordinates Guide: http://www.flounder.com/virtual_screen_coordinates.htm

---

**Document Version:** 1.0
**Last Updated:** 2025-01-16
**Research Source:** Microsoft Learn Documentation, Stack Overflow, Developer Blogs (2024-2025)
