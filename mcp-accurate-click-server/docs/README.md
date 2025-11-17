# MCP Accurate Click Server - Documentation

Welcome to the documentation for the MCP Accurate Click Server.

## Documentation Structure

This directory contains comprehensive documentation for the MCP Accurate Click Server:

### Core Documentation

1. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
   - Component overview
   - Data flow diagrams
   - Integration points
   - Design decisions

2. **[API.md](API.md)** - Complete API reference
   - MCP tools documentation
   - Public classes and methods
   - Parameters and return types
   - Code examples

3. **[CONFIGURATION.md](CONFIGURATION.md)** - Configuration guide
   - Installation instructions
   - Environment variables
   - Server configuration
   - Client setup

4. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
   - Error messages
   - Debugging techniques
   - Platform-specific issues
   - FAQ

### Cross-Platform Support Documentation

5. **[CROSS_PLATFORM_GUIDE.md](CROSS_PLATFORM_GUIDE.md)** - Platform abstraction architecture
   - Unified platform abstraction layer
   - Platform adapters for Windows, Linux, macOS
   - Coordinate system differences
   - Implementation guide for new platforms
   - Testing strategy
   - Migration guide

6. **[PLATFORM_API_REFERENCE.md](PLATFORM_API_REFERENCE.md)** - Platform abstraction layer API
   - PlatformFactory and base classes
   - Coordinate transformer interface
   - Click validator interface
   - Input simulator interface
   - Platform-specific implementations
   - Error handling and thread safety
   - Complete code examples

7. **[SYSTEM_REQUIREMENTS.md](SYSTEM_REQUIREMENTS.md)** - Minimum and recommended requirements
   - Minimum vs. recommended specifications
   - Windows 10/11 requirements
   - Linux (X11/Wayland) requirements
   - macOS requirements (experimental)
   - Dependency lists for each platform
   - Hardware and network requirements
   - Compatibility matrix
   - Verification checklist

### Linux-Specific Documentation

8. **[LINUX_SETUP.md](LINUX_SETUP.md)** - Linux installation and setup guide
   - System dependencies for X11 and Wayland
   - Step-by-step installation
   - Display server configuration
   - DPI detection and configuration
   - Verification procedures
   - Troubleshooting for Linux-specific issues
   - Performance tuning

9. **[LINUX_CODE_EXAMPLES.md](LINUX_CODE_EXAMPLES.md)** - Linux usage examples
   - Basic usage and initialization
   - DPI detection and handling
   - Coordinate transformation on Linux
   - Click operations
   - Input simulation
   - Multi-monitor setup
   - Display server detection (X11 vs Wayland)
   - Advanced examples and patterns

### Performance and Optimization

10. **[PERFORMANCE_BENCHMARKS.md](PERFORMANCE_BENCHMARKS.md)** - Performance metrics across platforms
    - Overall performance summary
    - Methodology and test environments
    - Windows performance benchmarks
    - Linux performance benchmarks (X11/Wayland)
    - macOS performance (experimental)
    - Comparative platform analysis
    - Optimization recommendations
    - Profiling guide for performance monitoring

## Research Papers

The server is built on extensive research documented in the parent directory:

### Coordinate Systems & Mathematics
- **COORDINATE_TRANSFORMATION_MATHEMATICS.md** - Mathematical foundations
- **ALGORITHMS_PSEUDOCODE.md** - Algorithm implementations
- **WINDOWS_COORDINATE_SYSTEMS_RESEARCH.md** - Windows-specific coordinate handling
- **MULTI_MONITOR_DPI_RESEARCH.md** - Multi-monitor DPI scaling

### Clicking Accuracy
- **RESEARCH.md** - Analysis of clicking accuracy across frameworks
- **CLICK_VALIDATION_RESEARCH.md** - Click validation strategies
- **DOM_APPROACH_SUMMARY.md** - DOM structure extraction (100% accuracy)
- **ACCESSIBILITY_TREE_FOR_CLICKING.md** - Accessibility tree usage

### Vision & AI
- **VISION_RESEARCH.md** - Computer vision approaches
- **AI_VISION_APPROACHES.md** - AI-powered element detection
- **HYBRID_VALIDATION_ARCHITECTURE.md** - Combining multiple validation methods

### Implementation
- **IMPLEMENTATION_SUMMARY.md** - Implementation overview
- **IMPLEMENTATION_GUIDE.md** - Development guide
- **IMPLEMENTATION_EXAMPLES.md** - Code examples

## Quick Links

### Getting Started
- [Main README](../README.md)
- [Installation](CONFIGURATION.md#installation)
- [Quick Start](../README.md#quick-start)
- [System Requirements](SYSTEM_REQUIREMENTS.md)

### Linux Users
- [Linux Setup Guide](LINUX_SETUP.md)
- [Linux Code Examples](LINUX_CODE_EXAMPLES.md)
- [Display Server Configuration](LINUX_SETUP.md#display-server-setup)
- [DPI Detection](LINUX_CODE_EXAMPLES.md#dpi-detection)

### Development & Architecture
- [Architecture Overview](ARCHITECTURE.md)
- [API Reference](API.md)
- [Platform Abstraction Guide](CROSS_PLATFORM_GUIDE.md)
- [Platform API Reference](PLATFORM_API_REFERENCE.md)
- [Examples](../examples/)

### Performance & Optimization
- [Performance Benchmarks](PERFORMANCE_BENCHMARKS.md)
- [Optimization Tips](PERFORMANCE_BENCHMARKS.md#optimization-recommendations)
- [Profiling Guide](PERFORMANCE_BENCHMARKS.md#profiling-guide)

### Troubleshooting
- [Common Issues](TROUBLESHOOTING.md)
- [Platform-Specific](TROUBLESHOOTING.md#platform-specific-issues)
- [Performance Issues](TROUBLESHOOTING.md#performance-issues)
- [Linux Troubleshooting](LINUX_SETUP.md#troubleshooting)

## Key Concepts

### Coordinate Systems

The server handles four coordinate systems:

1. **OS Screen Coordinates** - Physical pixels on screen
2. **CSS Screen Coordinates** - Logical pixels (accounting for DPI)
3. **Browser Viewport Coordinates** - Relative to visible browser area
4. **DOM Element Coordinates** - Relative to document (including scroll)

### Transformation Pipeline

```
OS Screen → CSS Screen → Viewport → DOM Element
  (÷DPR)    (-window)    (-scroll)  (elementFromPoint)
```

### Accuracy Methods

1. **DOM Extraction** - 100% precision for element centers
2. **Coordinate Math** - Sub-pixel affine transformations
3. **Accessibility Tree** - Semantic element identification
4. **Vision Validation** - Visual confirmation (optional)

## Version History

- **v1.0.0** (2025-11-17) - Initial production release with cross-platform support
  - Sub-pixel coordinate transformation
  - DOM structure extraction
  - Accessibility tree support
  - MCP protocol implementation
  - **Windows Support**: Full DPI handling, multi-monitor
  - **Linux Support**: X11 and Wayland, xrandr/wlr-randr DPI detection
  - **macOS Support**: Experimental with Quartz Display Services
  - Comprehensive cross-platform documentation
  - Platform abstraction layer with unified API
  - Performance benchmarks for all platforms
  - Linux setup guide and code examples
  - System requirements and compatibility matrix

## Contributing

See the main [README](../README.md#contributing) for contribution guidelines.

## License

MIT License - See [LICENSE](../LICENSE) file for details.

---

**Need Help?**
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Review [API.md](API.md) for usage examples
- Consult research papers for deep technical details
