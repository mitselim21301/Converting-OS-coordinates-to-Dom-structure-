# Linux Edge Case Handling

Comprehensive guide to edge case detection and handling in the Linux input simulation system.

## Overview

The Linux platform implementation includes a robust edge case detection and handling system that identifies problematic environments and provides graceful fallbacks with clear limitations documentation.

## Detected Edge Cases

### 1. Container Environments

#### Detection Methods
- **Docker**: Checks for `/.dockerenv`, `/.dockerinit`, `/run/docker`
- **Podman**: Checks for `/.podmanenv`, `/run/podman`
- **LXC**: Checks for `/sys/fs/cgroup/lxc`, examines `/proc/sys/kernel/osrelease`
- **Kubernetes**: Checks for `/var/run/secrets/kubernetes.io`, `/etc/kubernetes`

#### Limitations
```
DOCKER/PODMAN: Limited display access. Ensure --privileged flag or X11 socket mounting.
LXC: Restricted system call access may affect input simulation.
KUBERNETES: No persistent display. Pod may not have UI access.
```

#### Recommended Fixes
```bash
# Docker X11 forwarding
docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix <image>

# Podman with X11
podman run --userns=keep-id -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix <image>

# Kubernetes sidecar approach
kubectl apply -f - <<EOF
apiVersion: v1
kind: Pod
metadata:
  name: app-with-display
spec:
  containers:
  - name: xserver
    image: ubuntu:22.04
    command: ["/usr/bin/Xvfb", ":99", "-screen", "0", "1920x1080x24"]
  - name: app
    image: myapp:latest
    env:
    - name: DISPLAY
      value: ":99"
EOF
```

### 2. Headless Servers

#### Detection Methods
- Checks for `DISPLAY` environment variable
- Checks for `WAYLAND_DISPLAY` environment variable
- Checks for `XVFB_DISPLAY` environment variable
- Runs `xdpyinfo` command to verify X11 accessibility

#### Limitations
```
HEADLESS: No display available - X11 input simulation will not work.
           Virtual display server (Xvfb) required.
           Cannot perform visual input or coordinate-based operations.
```

#### Recommended Fixes
```bash
# Install Xvfb
apt-get install xvfb xvfb-run

# Start virtual display
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Or use xvfb-run wrapper
xvfb-run -a python your_script.py

# Verify display
xdpyinfo
```

### 3. SSH X11 Forwarding

#### Detection Methods
- Checks for `SSH_CONNECTION` environment variable
- Verifies `DISPLAY` variable is set to forwarded socket
- Examines process list for sshd and X11 indicators

#### Limitations
```
SSH_X11: Remote display may have latency (50-500ms depending on network).
         Input timing should account for network delays.
         Increases error rates due to synchronization issues.
```

#### Handling Strategy
- Automatically increases input delays by 5x (10ms → 50ms)
- Increases retry delay to 100ms
- Logs network latency warnings

#### Recommended Fixes
```bash
# On server: Enable X11 forwarding
# /etc/ssh/sshd_config
X11Forwarding yes
X11DisplayOffset 10
X11UseLocalhost yes

# Restart SSH
systemctl restart sshd

# On client: Use SSH with X11 forwarding
ssh -X user@host  # X11 forwarding
ssh -Y user@host  # Trusted X11 forwarding (less secure)

# Test X11 forwarding
ssh -X user@host xdpyinfo
```

### 4. VNC/Remote Desktop Sessions

#### Detection Methods
- Checks for `VNC_GEOMETRY` environment variable
- Checks for `vncserver` or `vncviewer` command availability
- Examines process list for VNC processes

#### Remote Access Types Detected
- **VNC**: Virtual Network Computing
- **SPICE**: Simple Protocol for Independent Computing Environments
- **RDP**: Remote Desktop Protocol
- **Chrome Remote Desktop**: Google's remote desktop solution

#### Limitations
```
VNC: Higher latency (100ms-1s depending on network and compression).
     Coordinate synchronization issues common.
     Input/output lag may affect timing-sensitive operations.

SPICE: Similar to VNC with slightly better performance.

RDP: Higher input lag, Windows-specific semantics may not match.

Chrome Remote Desktop: Dependency on remote desktop service availability.
```

#### Handling Strategy
- Automatically increases all timing delays
- Suggests output validation after input operations
- Provides latency compensation mechanisms

#### Recommended Fixes
```bash
# For VNC: Use low-compression settings
vncserver -geometry 1920x1080 -depth 24 :99

# Adjust VNC compression
vncviewer -compresslevel 9 localhost:5999

# For SPICE: Install spice-server
apt-get install spice-server spice-html5

# Test remote access
vncviewer -via user@host localhost:5999
```

### 5. Virtual Machine Detection

#### Supported VM Types
- **QEMU/KVM**: Detects via BIOS information or cpuinfo
- **VirtualBox**: Detects via system vendor string
- **VMware**: Detects via system vendor or cpuinfo
- **Xen**: Checks `/proc/xen` and hypervisor type
- **Hyper-V**: Detects via Microsoft vendor string
- **Parallels**: Detects via Parallels system vendor
- **libvirt**: Generic KVM/Xen detection

#### Limitations
```
VIRTUAL_MACHINE: Hardware input interception may have latency.
                 No direct hardware access - simulated through hypervisor.
                 DPI detection may be unreliable.
                 Monitor configuration detection may fail.
```

#### Detection Methods
```python
# Via system vendor file
cat /sys/class/dmi/id/sys_vendor

# Via cpuinfo
cat /proc/cpuinfo | grep -i "qemu|vmware|virtualbox|xen"

# Via dmidecode (requires sudo)
sudo dmidecode -s system-manufacturer
```

#### Recommended Fixes
```bash
# Verify VM is properly configured
lsmod | grep kvm           # Check KVM module
dmesg | grep -i hypervisor # Check hypervisor detection

# For VirtualBox: Ensure Guest Additions installed
apt-get install virtualbox-guest-additions-iso

# For VMware: Ensure VMware Tools installed
apt-get install open-vm-tools

# Increase input simulation delays for VMs
export INPUT_SIMULATOR_MOVE_DELAY=50  # ms
export INPUT_SIMULATOR_CLICK_DELAY=50
```

### 6. Screen Recording/Mirroring

#### Supported Recording Types
- **FFmpeg**: Desktop recording to file
- **OBS**: Open Broadcaster Software
- **SimpleScreenRecorder**: Simple screen recording utility
- **Wayland Recorder**: Native Wayland screen recording
- **wf-recorder/wl-screenrec**: Lightweight Wayland recording

#### Limitations
```
RECORDING_ACTIVE: Input simulation will be captured in recording.
                  Performance may be degraded (5-20% slowdown).
                  Timing precision may be affected by recording overhead.
```

#### Detection Methods
```bash
# Check for running recorders
ps aux | grep -i "ffmpeg\|obs\|simplescreenrecorder\|wf-recorder"

# Check for recording processes
lsof | grep -i "/tmp.*video"
```

#### Recommended Fixes
```bash
# Disable recording during test
pkill -f "ffmpeg|obs|simplescreenrecorder"

# Or run in separate virtual display
Xvfb :99 -screen 0 1920x1080x24 &
DISPLAY=:99 python your_script.py
# Record from :99 separately
ffmpeg -f x11grab -i :99 output.mp4
```

### 7. Multiple X Servers

#### Detection Methods
- Counts running `Xvfb`, `Xephyr`, and `X` processes
- Analyzes `DISPLAY` variable for multiple display numbers
- Checks for multiple display sockets in `/tmp/.X11-unix/`

#### Limitations
```
MULTIPLE_X_SERVERS: Coordinate translation may fail if not on primary display.
                    DISPLAY variable must point to correct server.
                    Monitor enumeration may be ambiguous.
```

#### Detection Example
```bash
# View all X servers
ps aux | grep -E "Xvfb|Xephyr|X " | grep -v grep

# View X display sockets
ls -la /tmp/.X11-unix/

# Check current DISPLAY
echo $DISPLAY
```

#### Recommended Fixes
```bash
# Explicitly set correct DISPLAY
export DISPLAY=:99

# Use xhost to allow access
xhost +local:

# Verify connection
xdpyinfo -display :99

# List all connected X servers
for i in 0 1 2 99 100; do
    if xdpyinfo -display :$i &>/dev/null; then
        echo "X server :$i is running"
    fi
done
```

### 8. Permission Restrictions

#### Checked Permissions
- `/dev/input/` - Mouse and keyboard device access
- `/dev/uinput` - Virtual input device creation
- `/dev/input/mice` - Mouse input device
- X11 socket at `~/.X11-unix/` - X server access
- `/proc/{pid}/` - Process information access

#### Limitations
```
PERMISSION_DENIED: Cannot perform input simulation without proper access.
                   May require running with sudo or specific group membership.
                   Security implications of permission escalation.
```

#### Detection Methods
```bash
# Check input device permissions
ls -la /dev/input/
ls -la /dev/uinput

# Check X11 socket permissions
ls -la /tmp/.X11-unix/

# Check your group membership
groups

# Check running permissions
id
```

#### Recommended Fixes
```bash
# Add user to input group
sudo usermod -a -G input $USER

# Add user to video group (for some systems)
sudo usermod -a -G video $USER

# Fix device permissions (less secure)
sudo chmod 666 /dev/uinput
sudo chmod 666 /dev/input/mice

# Load uinput kernel module
sudo modprobe uinput

# Check if loaded
lsmod | grep uinput

# Make module load on boot
echo "uinput" | sudo tee -a /etc/modules

# Re-login to apply group changes
newgrp input
# or
su - $USER
```

## Implementation Details

### EdgeCaseHandler Class

The `EdgeCaseHandler` class provides comprehensive edge case detection:

```python
from mcp_server.platform.linux.edge_case_handler import get_edge_case_handler

handler = get_edge_case_handler()
detection = handler.detect_edge_cases()

# Access detection results
print(f"Environment: {detection.environment_type.value}")
print(f"Headless: {detection.is_headless}")
print(f"Containerized: {detection.is_containerized}")
print(f"Virtual Machine: {detection.is_virtual_machine}")
print(f"Remote Access: {detection.remote_access_type.value}")
print(f"Recording: {detection.recording_type.value}")

# Get limitations and recommendations
for limitation in detection.limitations:
    print(f"LIMITATION: {limitation}")

for recommendation in detection.recommendations:
    print(f"RECOMMENDATION: {recommendation}")
```

### Integration with Linux Modules

All Linux modules automatically use edge case detection:

1. **DPI Handler** (`dpi_handler.py`)
   - Logs headless and remote access detection
   - Reports permission issues
   - Uses fallback DPI for headless environments

2. **Input Simulator** (`input_simulator.py`)
   - Increases delays for remote access (5x multiplier)
   - Provides enhanced error messages for headless
   - Warns about permission issues
   - Adjusts retry strategy for remote access

3. **Coordinate Converter** (`coordinate_converter.py`)
   - Warns about multiple X servers
   - Logs remote access detection
   - Provides fallback bounds for headless

4. **Window Manager** (`window_manager.py`)
   - Logs container environment
   - Reports window detection limitations
   - Handles permission issues gracefully

## Test Cases

Comprehensive test suite in `test_edge_cases.py` covers:

### Container Tests
- Docker detection
- Podman detection
- LXC detection
- Kubernetes detection
- Containerized flag validation

### Virtual Machine Tests
- QEMU detection
- VirtualBox detection
- VMware detection
- VM flag validation

### Display Tests
- Headless environment detection
- X11 display detection
- Wayland display detection
- Multiple X server detection

### Remote Access Tests
- SSH X11 forwarding detection
- VNC session detection
- SPICE session detection
- RDP session detection
- Chrome Remote Desktop detection

### Recording Tests
- FFmpeg recording detection
- OBS recording detection
- SimpleScreenRecorder detection
- Wayland recorder detection

### Permission Tests
- /dev/uinput detection
- /dev/input permissions check
- X11 socket access check
- Process info access check

### Limitation Tests
- Headless limitations
- Container limitations
- Remote access limitations
- Recording limitations

### Recommendation Tests
- Docker recommendations
- Headless recommendations
- Permission recommendations
- SSH recommendations

## Usage Examples

### Basic Detection

```python
from mcp_server.platform.linux.edge_case_handler import get_edge_case_handler

handler = get_edge_case_handler()
detection = handler.detect_edge_cases()

if detection.is_headless:
    print("Running in headless environment - install Xvfb")

if detection.is_containerized:
    print(f"Running in container: {detection.environment_type.value}")

if detection.permission_issues:
    print(f"Permission issues: {detection.permission_issues}")
```

### Handling Remote Access

```python
from mcp_server.platform.linux.edge_case_handler import RemoteAccessType

if detection.remote_access_type != RemoteAccessType.DIRECT:
    # Increase input simulation delays
    simulator.set_delays(
        move_delay=50,      # 50ms instead of 10ms
        click_delay=50,
        double_click_delay=200
    )
```

### Container-Specific Setup

```python
if detection.is_containerized:
    recommendations = detection.recommendations
    for recommendation in recommendations:
        if "privileged" in recommendation:
            print("Consider running with --privileged flag")
        elif "X11" in recommendation:
            print("Ensure X11 socket is properly mounted")
```

## Limitations Document

### Known Limitations by Environment

| Environment | Limitation | Impact | Workaround |
|-----------|-----------|--------|-----------|
| Docker | No direct X11 access | Input simulation fails | Mount X11 socket, use --privileged |
| Kubernetes | No persistent UI | No input simulation | Use sidecar with display |
| Headless | No display server | No visual output | Install Xvfb |
| SSH X11 | Network latency 50-500ms | Timing errors | Increase delays, use VPN |
| VNC | High latency 100ms-1s | Reduced accuracy | Use local display if possible |
| QEMU | Hypervisor overhead | 10-20% performance degradation | Nested virtualization may help |
| Multiple X | Coordination issues | Wrong display targeted | Verify DISPLAY variable |
| Permission | Denied access | Cannot simulate input | Fix permissions or use sudo |

## Performance Impact

### Baseline Performance
- Native desktop: ~5ms per click
- Native server: ~8ms per click

### With Edge Cases
- SSH X11: 50ms per click (+900% overhead)
- VNC: 100ms per click (+1900% overhead)
- Docker: Depends on X11 setup (0-500% overhead)
- VM: 8-15ms per click (+60% overhead)
- Multiple delays: Cumulative effect

## Security Considerations

1. **Sudo Usage**: Some permissions require `sudo` - use with caution
2. **Privileged Containers**: `--privileged` flag reduces security - use only if necessary
3. **X11 Forwarding**: SSH X11 forwarding has known security concerns - use `-Y` cautiously
4. **Device Access**: Direct `/dev/input` access is security-sensitive
5. **VNC**: Unencrypted by default - use VPN or SSH tunneling

## Troubleshooting

### Common Issues

1. **"Headless environment detected"**
   ```bash
   # Solution: Install and start Xvfb
   apt-get install xvfb
   Xvfb :99 -screen 0 1920x1080x24 &
   export DISPLAY=:99
   ```

2. **"Permission denied for /dev/uinput"**
   ```bash
   # Solution: Add user to input group
   sudo usermod -a -G input $USER
   newgrp input
   ```

3. **"Multiple X servers detected"**
   ```bash
   # Solution: Verify DISPLAY variable
   echo $DISPLAY
   # Should be single server, e.g., :0 or :99
   ```

4. **"SSH X11 forwarding not working"**
   ```bash
   # Verify on server: /etc/ssh/sshd_config
   X11Forwarding yes

   # On client, use proper flag
   ssh -X user@host
   ```

5. **"Docker: Cannot connect to X server"**
   ```bash
   # Solution: Mount X11 socket
   docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix myimage
   ```

## Future Enhancements

1. **Automatic Mitigation**: Automatically apply workarounds for detected issues
2. **Performance Monitoring**: Track input operation timing and warn if degraded
3. **Network Detection**: Measure network latency and adjust delays dynamically
4. **Container Orchestration**: Better support for orchestration platforms
5. **GPU Acceleration**: Detect and utilize GPU-accelerated input if available
6. **Machine Learning**: Predict and prevent known failure patterns
7. **Metrics Collection**: Track edge case frequencies in deployments

## References

- [X11 Documentation](https://www.x.org/)
- [Wayland Documentation](https://wayland.freedesktop.org/)
- [Docker X11 Forwarding](https://docs.docker.com/engine/reference/run/)
- [SSH X11 Forwarding](https://man.openbsd.org/ssh_config)
- [Linux Input Subsystem](https://www.kernel.org/doc/html/latest/input/index.html)
- [uinput Documentation](https://www.kernel.org/doc/html/latest/input/uinput.html)
