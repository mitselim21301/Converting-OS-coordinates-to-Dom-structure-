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

### Development
- [Architecture Overview](ARCHITECTURE.md)
- [API Reference](API.md)
- [Examples](../examples/)

### Troubleshooting
- [Common Issues](TROUBLESHOOTING.md)
- [Platform-Specific](TROUBLESHOOTING.md#platform-specific-issues)
- [Performance](TROUBLESHOOTING.md#performance-issues)

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

- **v1.0.0** (2025-11-16) - Initial release
  - Sub-pixel coordinate transformation
  - DOM structure extraction
  - Accessibility tree support
  - MCP protocol implementation
  - Windows DPI handling

## Contributing

See the main [README](../README.md#contributing) for contribution guidelines.

## License

MIT License - See [LICENSE](../LICENSE) file for details.

---

**Need Help?**
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Review [API.md](API.md) for usage examples
- Consult research papers for deep technical details
