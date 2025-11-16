# Quick Reference Guide
## OS to DOM Coordinate Transformation

### 30-Second Start

```python
from os_to_dom_transformer import OSToDOM_Transformer
import numpy as np

# Calibrate
transformer = OSToDOM_Transformer()
os_pts = np.array([[100,100], [800,100], [100,500], [800,500]])
dom_pts = np.array([[150,180], [1100,180], [150,780], [1100,780]])
transformer.calibrate(os_pts, dom_pts)

# Transform
x_dom, y_dom = transformer.transform_os_to_dom(400, 300)
```

---

## Essential Operations

### Transform Points
```python
# Single point
x, y = transform.transform_point(10, 20)

# Multiple points
points = np.array([[10,20], [30,40]])
results = transform.transform_points(points)
```

### Calibrate
```python
# Basic
transform, error = calibrate_affine_transform(source, target)

# Robust (RANSAC)
transform, mask, n = calibrate_ransac(source, target, 1000, 2.0)
```

### Validate
```python
validation = SubPixelValidator.validate(transform)
assert validation['pass']
```

See README.md and COORDINATE_TRANSFORMATION_MATHEMATICS.md for full documentation.
