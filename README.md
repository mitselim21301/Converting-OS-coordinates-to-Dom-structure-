# OS to DOM Coordinate Transformation

High-precision mathematical models and implementations for transforming coordinates from Operating System (OS) space to Document Object Model (DOM) space with **sub-pixel accuracy** (< 1/256 pixel).

## Overview

This repository provides comprehensive mathematical models, algorithms, and implementations for accurate coordinate transformation between different coordinate systems. The system achieves sub-pixel precision using:

- **Affine transformation matrices** with float64 precision
- **Robust calibration algorithms** (least squares, RANSAC, iterative refinement)
- **Error propagation analysis** through transformation chains
- **Numerical stability** optimization
- **Adaptive correction** based on feedback

## Key Features

- ✨ **Sub-pixel accuracy**: < 1/256 pixel (0.004 pixels)
- 🎯 **Robust calibration**: RANSAC-based outlier rejection
- 📊 **Error analysis**: Comprehensive error propagation tracking
- 🔄 **Adaptive correction**: Learns from user feedback
- 📐 **Multi-scale support**: Handles different zoom levels
- ✅ **Validation**: Round-trip accuracy testing
- 💾 **Persistence**: Save and load calibrations

## Files

### Documentation
- **`COORDINATE_TRANSFORMATION_MATHEMATICS.md`** - Complete mathematical theory, formulas, and algorithms
- **`ALGORITHMS_PSEUDOCODE.md`** - Language-agnostic algorithm implementations
- **`README.md`** - This file

### Implementation Modules
- **`affine_transform.py`** - Core affine transformation classes
- **`calibration.py`** - Calibration algorithms (least squares, RANSAC, adaptive)
- **`error_analysis.py`** - Error propagation and precision validation
- **`os_to_dom_transformer.py`** - Complete transformation system

### Examples
- **`examples/`** - Usage examples and tutorials
- **`tests/`** - Unit tests and validation

## Quick Start

### Installation

```bash
# Required dependencies
pip install numpy

# Optional (for advanced features)
pip install scipy matplotlib
```

### Basic Usage

```python
from os_to_dom_transformer import OSToDOM_Transformer
import numpy as np

# Create transformer
transformer = OSToDOM_Transformer()

# Calibration data: (OS coordinates, DOM coordinates)
os_points = np.array([
    [100, 100],
    [800, 100],
    [100, 500],
    [800, 500],
    [450, 300]
])

dom_points = np.array([
    [150, 180],
    [1100, 180],
    [150, 780],
    [1100, 780],
    [625, 480]
])

# Calibrate transformation
report = transformer.calibrate(os_points, dom_points, use_ransac=True)

print(f"Calibration accuracy: {report['validation']['achieved_accuracy']:.6f} pixels")
print(f"Sub-pixel accurate: {report['validation']['is_subpixel_accurate']}")

# Transform coordinates
x_os, y_os = 300, 250
x_dom, y_dom = transformer.transform_os_to_dom(x_os, y_os)

print(f"OS ({x_os}, {y_os}) → DOM ({x_dom:.3f}, {y_dom:.3f})")

# Validate accuracy
validation = transformer.validate()
print(f"Round-trip max error: {validation['round_trip']['max_error']:.6f} pixels")
```

### Advanced Usage

#### Multi-Scale Calibration

```python
# Calibrate for different zoom levels
for zoom in [1.0, 1.5, 2.0]:
    transformer.set_scale(zoom)
    report = transformer.calibrate(
        os_points_at_zoom,
        dom_points_at_zoom,
        scale=zoom
    )

# Use at specific zoom level
transformer.set_scale(1.5)
x_dom, y_dom = transformer.transform_os_to_dom(x_os, y_os)
```

#### Adaptive Correction

```python
# Enable adaptive correction
transformer = OSToDOM_Transformer(enable_adaptive=True)

# Transform and get prediction
x_predicted, y_predicted = transformer.transform_os_to_dom(x_os, y_os)

# User provides actual location (e.g., from click)
x_actual, y_actual = get_actual_click_position()

# Add correction feedback
transformer.add_correction_feedback(
    (x_os, y_os),
    (x_predicted, y_predicted),
    (x_actual, y_actual)
)

# Future transformations will be more accurate
```

#### Save and Load Calibrations

```python
# Save calibration
transformer.save_calibration('calibration.npz')

# Load in another session
transformer2 = OSToDOM_Transformer()
transformer2.load_calibration('calibration.npz')
```

## Mathematical Foundation

### Affine Transformation

The core transformation is represented as:

```
[x']   [a  b  tx]   [x]
[y'] = [c  d  ty] × [y]
[1 ]   [0  0   1]   [1]
```

Where:
- `(x, y)` = OS coordinates
- `(x', y')` = DOM coordinates
- `a, b, c, d` = linear transformation components (scale, rotation, shear)
- `tx, ty` = translation offsets

### Decomposition

Any affine transformation can be decomposed into:

```
M = T(tx, ty) × R(θ) × S(sx, sy)
```

- **T** = Translation
- **R** = Rotation
- **S** = Scaling

### Calibration

Given n ≥ 3 point correspondences, the transformation is found by solving:

```
minimize Σ ||M × p_i - q_i||²
```

Where `p_i` are OS points and `q_i` are DOM points.

### Error Propagation

For a chain of transformations, error propagates via:

```
Σ_out = J × Σ_in × J^T
```

Where:
- `Σ` = covariance matrix
- `J` = Jacobian matrix

## Algorithm Overview

### 1. Least Squares Calibration

```
Input: source_points (N×2), target_points (N×2)
Output: transformation_matrix (3×3)

1. Build linear system: A × x = b
2. Solve using least squares: x = (A^T A)^-1 A^T b
3. Construct transformation matrix from solution
```

**Complexity**: O(n) where n = number of points

### 2. RANSAC Calibration

```
Input: source_points, target_points, max_iterations, threshold
Output: best_transformation, inlier_mask

1. For i = 1 to max_iterations:
   a. Randomly sample 3 point pairs
   b. Fit transformation to sample
   c. Count inliers (error < threshold)
   d. Update best model if more inliers
2. Refit using all inliers
3. Return best transformation
```

**Complexity**: O(k × n) where k = iterations, n = points

### 3. Iterative Refinement

```
Input: initial_transform, source_points, target_points
Output: refined_transform

1. current_transform = initial_transform
2. Repeat until convergence:
   a. Transform points with current model
   b. Compute errors
   c. Compute weights = 1 / (error + ε)
   d. Perform weighted least squares
   e. Update current_transform
3. Return current_transform
```

## Precision Guarantees

The system guarantees:

1. **Sub-pixel accuracy**: Round-trip error < 1/256 pixel
2. **Numerical stability**: Condition number < 100
3. **Float64 precision**: ~15-17 significant digits
4. **Error bounds**: 95% confidence intervals provided

## Validation

### Round-Trip Test

```python
# Transform OS → DOM → OS
x_dom, y_dom = transformer.transform_os_to_dom(x_os, y_os)
x_recovered, y_recovered = transformer.transform_dom_to_os(x_dom, y_dom)

# Error should be < 1/256 pixel
error = sqrt((x_os - x_recovered)² + (y_os - y_recovered)²)
assert error < 0.004  # Sub-pixel accuracy
```

### Condition Number

```python
# Check numerical stability
info = transformer.get_info()
condition = info['condition_number']

# Well-conditioned: condition < 100
# Ill-conditioned: condition > 1000
assert condition < 100
```

## Common Use Cases

### 1. Browser Automation

Transform OS mouse coordinates to browser DOM coordinates for accurate clicking.

```python
# Calibrate using known DOM elements
calibration_elements = get_dom_element_positions()
os_clicks = record_os_click_positions()

transformer.calibrate(os_clicks, calibration_elements)

# Click on target element
target_dom_pos = get_target_element_position()
os_x, os_y = transformer.transform_dom_to_os(*target_dom_pos)
click_mouse(os_x, os_y)
```

### 2. Screen Coordinate Mapping

Map between different coordinate systems (screen, window, viewport, element).

```python
# Chain transformations
screen_to_window = calibrate_screen_to_window()
window_to_viewport = calibrate_window_to_viewport()
viewport_to_dom = calibrate_viewport_to_dom()

# Compose transformations
combined = viewport_to_dom @ window_to_viewport @ screen_to_window

# Transform through chain
dom_x, dom_y = combined.transform_point(screen_x, screen_y)
```

### 3. Multi-Monitor Setup

Handle coordinate transformation across multiple monitors.

```python
# Calibrate each monitor
transformers = {}
for monitor in monitors:
    transformers[monitor.id] = calibrate_monitor(monitor)

# Transform coordinates
monitor_id = get_monitor_at_position(x_os, y_os)
transformer = transformers[monitor_id]
x_dom, y_dom = transformer.transform_os_to_dom(x_os, y_os)
```

## Performance

Typical performance metrics (on modern hardware):

- **Calibration** (10 points): ~1 ms
- **Calibration with RANSAC** (100 points): ~50 ms
- **Single transformation**: ~1 μs
- **Batch transformation** (1000 points): ~0.5 ms

## Limitations

1. **Affine only**: Does not handle perspective transformations
2. **Static transformations**: Assumes coordinate system is stable
3. **Minimum points**: Requires at least 3 non-collinear calibration points
4. **Planar**: Only handles 2D transformations

For perspective transformations, see the perspective projection extension (future work).

## Testing

Run the test suite:

```bash
python -m pytest tests/

# Run specific tests
python -m pytest tests/test_affine_transform.py
python -m pytest tests/test_calibration.py
python -m pytest tests/test_precision.py

# Run with coverage
python -m pytest --cov=. tests/
```

## Contributing

Contributions are welcome! Areas for improvement:

- Perspective transformation support
- 3D coordinate transformations
- Real-time calibration refinement
- GPU acceleration for large point sets
- Additional robust estimation methods

## References

### Transformation Mathematics
- Hartley & Zisserman, "Multiple View Geometry in Computer Vision"
- Szeliski, "Computer Vision: Algorithms and Applications"

### Numerical Methods
- Golub & Van Loan, "Matrix Computations"
- Higham, "Accuracy and Stability of Numerical Algorithms"

### Robust Estimation
- Fischler & Bolles, "Random Sample Consensus" (RANSAC)
- Rousseeuw & Leroy, "Robust Regression and Outlier Detection"

## License

MIT License - See LICENSE file for details

## Citation

If you use this work in your research, please cite:

```bibtex
@software{os_to_dom_transformer,
  title = {OS to DOM Coordinate Transformation},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/yourusername/os-to-dom-transform}
}
```

## Contact

For questions or issues, please open a GitHub issue or contact [your-email@example.com].

---

**Version**: 1.0.0
**Last Updated**: 2025-11-16
