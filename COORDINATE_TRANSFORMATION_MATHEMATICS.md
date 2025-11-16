# Mathematical Models for OS to DOM Coordinate Transformation

## Table of Contents
1. [Affine Transformation Matrices](#1-affine-transformation-matrices)
2. [Scaling, Translation, and Rotation](#2-scaling-translation-and-rotation)
3. [Homogeneous Coordinates and Composition](#3-homogeneous-coordinates-and-composition)
4. [Inverse Transformations](#4-inverse-transformations)
5. [Error Propagation](#5-error-propagation)
6. [Numerical Precision](#6-numerical-precision)
7. [Calibration Algorithms](#7-calibration-algorithms)

---

## 1. Affine Transformation Matrices

### 1.1 Mathematical Foundation

An affine transformation preserves points, straight lines, and planes. For 2D coordinate transformation from OS to DOM:

**General Form:**
```
[x']   [a  b  tx]   [x]
[y'] = [c  d  ty] × [y]
[1 ]   [0  0   1]   [1]
```

Where:
- `(x, y)` = OS coordinates
- `(x', y')` = DOM coordinates
- `a, b, c, d` = linear transformation components
- `tx, ty` = translation components

**Expanded Form:**
```
x' = a·x + b·y + tx
y' = c·x + d·y + ty
```

### 1.2 Matrix Representation

```python
import numpy as np

class AffineTransform2D:
    """
    2D Affine transformation with sub-pixel precision
    """
    def __init__(self):
        # Initialize as identity matrix
        self.matrix = np.eye(3, dtype=np.float64)

    def set_matrix(self, a, b, c, d, tx, ty):
        """
        Set transformation matrix components

        Parameters:
        - a, d: scaling factors
        - b, c: shearing/rotation factors
        - tx, ty: translation offsets
        """
        self.matrix = np.array([
            [a,  b,  tx],
            [c,  d,  ty],
            [0,  0,   1]
        ], dtype=np.float64)

    def transform_point(self, x, y):
        """
        Transform a single point with sub-pixel accuracy

        Returns: (x', y') as float64
        """
        point = np.array([x, y, 1], dtype=np.float64)
        transformed = self.matrix @ point
        return transformed[0], transformed[1]

    def transform_points(self, points):
        """
        Batch transform multiple points efficiently

        Parameters:
        - points: Nx2 array of (x, y) coordinates

        Returns: Nx2 array of transformed coordinates
        """
        n = len(points)
        homogeneous = np.ones((n, 3), dtype=np.float64)
        homogeneous[:, :2] = points

        transformed = (self.matrix @ homogeneous.T).T
        return transformed[:, :2]
```

### 1.3 Decomposition of Affine Matrix

Any affine transformation can be decomposed into:

```
M = T(tx, ty) × R(θ) × S(sx, sy) × Sh(shx, shy)
```

Where:
- T = Translation
- R = Rotation
- S = Scaling
- Sh = Shearing

**Decomposition Algorithm:**

```python
def decompose_affine(matrix):
    """
    Decompose affine matrix into translation, rotation, scale, and shear

    Returns: dict with 'translation', 'rotation', 'scale', 'shear'
    """
    a, b, tx = matrix[0, :]
    c, d, ty = matrix[1, :]

    # Translation
    translation = (tx, ty)

    # Scaling and rotation (using SVD decomposition)
    linear = np.array([[a, b], [c, d]])

    # Determinant for reflection detection
    det = np.linalg.det(linear)

    # Compute rotation angle
    rotation = np.arctan2(c, a)

    # Compute scale factors
    sx = np.sqrt(a**2 + c**2)
    sy = det / sx if sx != 0 else 0

    # Compute shear
    shear = (a * b + c * d) / (a**2 + c**2) if (a**2 + c**2) != 0 else 0

    return {
        'translation': translation,
        'rotation': rotation,  # in radians
        'scale': (sx, sy),
        'shear': shear,
        'determinant': det
    }
```

---

## 2. Scaling, Translation, and Rotation

### 2.1 Translation Matrix

**Formula:**
```
T(tx, ty) = [1  0  tx]
            [0  1  ty]
            [0  0   1]
```

**Properties:**
- Preserves angles and distances
- Commutative: T(a) × T(b) = T(b) × T(a)
- Inverse: T⁻¹(tx, ty) = T(-tx, -ty)

**Implementation:**
```python
def translation_matrix(tx, ty):
    """
    Create translation transformation matrix

    Parameters:
    - tx, ty: translation offsets in pixels

    Returns: 3x3 numpy array
    """
    return np.array([
        [1.0, 0.0, float(tx)],
        [0.0, 1.0, float(ty)],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)
```

### 2.2 Scaling Matrix

**Formula:**
```
S(sx, sy) = [sx  0   0]
            [0   sy  0]
            [0   0   1]
```

**Uniform Scaling:**
```
S(s) = S(s, s)
```

**Properties:**
- Scale about origin
- Non-uniform scaling: sx ≠ sy
- Inverse: S⁻¹(sx, sy) = S(1/sx, 1/sy)

**Implementation:**
```python
def scaling_matrix(sx, sy=None):
    """
    Create scaling transformation matrix

    Parameters:
    - sx: x-axis scale factor
    - sy: y-axis scale factor (defaults to sx for uniform scaling)

    Returns: 3x3 numpy array
    """
    if sy is None:
        sy = sx

    return np.array([
        [float(sx), 0.0,       0.0],
        [0.0,       float(sy), 0.0],
        [0.0,       0.0,       1.0]
    ], dtype=np.float64)
```

**Scale about arbitrary point:**
```python
def scale_about_point(sx, sy, cx, cy):
    """
    Scale about point (cx, cy) instead of origin

    Formula: T(cx, cy) × S(sx, sy) × T(-cx, -cy)
    """
    T1 = translation_matrix(-cx, -cy)
    S = scaling_matrix(sx, sy)
    T2 = translation_matrix(cx, cy)

    return T2 @ S @ T1
```

### 2.3 Rotation Matrix

**Formula (counter-clockwise):**
```
R(θ) = [cos(θ)  -sin(θ)  0]
       [sin(θ)   cos(θ)  0]
       [0        0       1]
```

**Properties:**
- Rotation about origin
- Preserves distances and angles
- Orthogonal: R^T = R⁻¹
- det(R) = 1

**Implementation:**
```python
def rotation_matrix(theta):
    """
    Create rotation transformation matrix

    Parameters:
    - theta: rotation angle in radians (counter-clockwise)

    Returns: 3x3 numpy array
    """
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)

    return np.array([
        [cos_theta, -sin_theta, 0.0],
        [sin_theta,  cos_theta, 0.0],
        [0.0,        0.0,       1.0]
    ], dtype=np.float64)

def rotation_matrix_degrees(degrees):
    """Rotation matrix from degrees"""
    return rotation_matrix(np.radians(degrees))

def rotate_about_point(theta, cx, cy):
    """
    Rotate about point (cx, cy) instead of origin

    Formula: T(cx, cy) × R(θ) × T(-cx, -cy)
    """
    T1 = translation_matrix(-cx, -cy)
    R = rotation_matrix(theta)
    T2 = translation_matrix(cx, cy)

    return T2 @ R @ T1
```

### 2.4 Combined Transformations

**Scale-Rotate-Translate (SRT) Composition:**

```python
def create_srt_transform(scale_x, scale_y, rotation, trans_x, trans_y):
    """
    Create Scale-Rotate-Translate transformation

    Order matters: T × R × S

    Parameters:
    - scale_x, scale_y: scale factors
    - rotation: rotation angle in radians
    - trans_x, trans_y: translation offsets

    Returns: 3x3 transformation matrix
    """
    S = scaling_matrix(scale_x, scale_y)
    R = rotation_matrix(rotation)
    T = translation_matrix(trans_x, trans_y)

    # Apply in order: Scale -> Rotate -> Translate
    return T @ R @ S

def create_trs_transform(trans_x, trans_y, rotation, scale_x, scale_y):
    """
    Alternative order: Translate-Rotate-Scale
    """
    T = translation_matrix(trans_x, trans_y)
    R = rotation_matrix(rotation)
    S = scaling_matrix(scale_x, scale_y)

    return S @ R @ T
```

---

## 3. Homogeneous Coordinates and Transformation Composition

### 3.1 Homogeneous Coordinate System

**Definition:**
A 2D point (x, y) is represented as (x, y, 1) in homogeneous coordinates.

**Advantages:**
1. Unified representation of transformations
2. Translation becomes matrix multiplication
3. Perspective projections possible
4. Easy composition of transformations

**Conversion:**
```
Cartesian → Homogeneous: (x, y) → (x, y, 1)
Homogeneous → Cartesian: (x, y, w) → (x/w, y/w)
```

**Implementation:**
```python
def to_homogeneous(points):
    """
    Convert 2D Cartesian coordinates to homogeneous

    Parameters:
    - points: Nx2 array of (x, y) coordinates

    Returns: Nx3 array of (x, y, 1) coordinates
    """
    n = len(points)
    homogeneous = np.ones((n, 3), dtype=np.float64)
    homogeneous[:, :2] = points
    return homogeneous

def from_homogeneous(points):
    """
    Convert homogeneous coordinates to 2D Cartesian

    Parameters:
    - points: Nx3 array of (x, y, w) coordinates

    Returns: Nx2 array of (x/w, y/w) coordinates
    """
    # Handle division by w component
    w = points[:, 2:3]
    # Avoid division by zero
    w = np.where(np.abs(w) < 1e-10, 1.0, w)
    return points[:, :2] / w
```

### 3.2 Transformation Composition

**Composition Rule:**
Multiple transformations are composed by matrix multiplication (right to left):

```
M = Mn × Mn-1 × ... × M2 × M1
```

**Order matters:**
```
R(θ) × T(tx, ty) ≠ T(tx, ty) × R(θ)
```

**Implementation:**
```python
class TransformChain:
    """
    Compose multiple transformations efficiently
    """
    def __init__(self):
        self.transforms = []
        self._combined_matrix = None
        self._dirty = True

    def add_translation(self, tx, ty):
        """Add translation to chain"""
        self.transforms.append(translation_matrix(tx, ty))
        self._dirty = True
        return self

    def add_scaling(self, sx, sy=None):
        """Add scaling to chain"""
        self.transforms.append(scaling_matrix(sx, sy))
        self._dirty = True
        return self

    def add_rotation(self, theta):
        """Add rotation to chain"""
        self.transforms.append(rotation_matrix(theta))
        self._dirty = True
        return self

    def add_matrix(self, matrix):
        """Add arbitrary transformation matrix"""
        self.transforms.append(matrix.copy())
        self._dirty = True
        return self

    def get_combined_matrix(self):
        """
        Get combined transformation matrix
        Uses lazy evaluation for efficiency
        """
        if self._dirty or self._combined_matrix is None:
            # Start with identity
            self._combined_matrix = np.eye(3, dtype=np.float64)

            # Multiply all transforms (left to right)
            for transform in self.transforms:
                self._combined_matrix = self._combined_matrix @ transform

            self._dirty = False

        return self._combined_matrix

    def transform(self, x, y):
        """Transform a point through the chain"""
        matrix = self.get_combined_matrix()
        point = np.array([x, y, 1], dtype=np.float64)
        result = matrix @ point
        return result[0], result[1]

    def clear(self):
        """Clear all transformations"""
        self.transforms = []
        self._combined_matrix = None
        self._dirty = True
```

### 3.3 Transformation Interpolation

For smooth animations between coordinate systems:

```python
def interpolate_transforms(M1, M2, t):
    """
    Interpolate between two transformation matrices

    Parameters:
    - M1, M2: 3x3 transformation matrices
    - t: interpolation parameter [0, 1]

    Returns: interpolated transformation matrix
    """
    # Decompose both matrices
    decomp1 = decompose_affine(M1)
    decomp2 = decompose_affine(M2)

    # Interpolate components
    tx = (1 - t) * decomp1['translation'][0] + t * decomp2['translation'][0]
    ty = (1 - t) * decomp1['translation'][1] + t * decomp2['translation'][1]

    sx = (1 - t) * decomp1['scale'][0] + t * decomp2['scale'][0]
    sy = (1 - t) * decomp1['scale'][1] + t * decomp2['scale'][1]

    # Angle interpolation (shortest path)
    angle1 = decomp1['rotation']
    angle2 = decomp2['rotation']

    # Normalize angle difference to [-π, π]
    diff = (angle2 - angle1 + np.pi) % (2 * np.pi) - np.pi
    angle = angle1 + t * diff

    shear = (1 - t) * decomp1['shear'] + t * decomp2['shear']

    # Reconstruct matrix
    return create_srt_transform(sx, sy, angle, tx, ty)
```

---

## 4. Inverse Transformations

### 4.1 Mathematical Foundation

For validation and bidirectional mapping, we need inverse transformations:

```
M × M⁻¹ = I
```

**Affine Matrix Inverse:**

For matrix:
```
M = [a  b  tx]
    [c  d  ty]
    [0  0   1]
```

The inverse is:
```
M⁻¹ = [d/D   -b/D   (b·ty - d·tx)/D]
      [-c/D   a/D   (c·tx - a·ty)/D]
      [0      0      1              ]
```

Where D = det(M) = ad - bc

**Condition:** D ≠ 0 (matrix must be non-singular)

### 4.2 Implementation

```python
def inverse_affine_transform(matrix):
    """
    Compute inverse of affine transformation matrix

    Parameters:
    - matrix: 3x3 affine transformation matrix

    Returns: 3x3 inverse matrix

    Raises:
    - ValueError if matrix is singular (det ≈ 0)
    """
    a, b, tx = matrix[0, :]
    c, d, ty = matrix[1, :]

    # Compute determinant
    det = a * d - b * c

    # Check for singularity (with numerical tolerance)
    if abs(det) < 1e-10:
        raise ValueError(
            f"Matrix is singular (det={det}), cannot invert. "
            "This usually indicates overlapping transformations."
        )

    # Compute inverse using analytical formula
    inv_matrix = np.array([
        [ d/det, -b/det, (b*ty - d*tx)/det],
        [-c/det,  a/det, (c*tx - a*ty)/det],
        [ 0.0,    0.0,    1.0              ]
    ], dtype=np.float64)

    return inv_matrix

def inverse_transform_safe(matrix):
    """
    Safe inverse with fallback to pseudoinverse

    Uses numpy's pinv for ill-conditioned matrices
    """
    try:
        return inverse_affine_transform(matrix)
    except ValueError:
        # Use Moore-Penrose pseudoinverse as fallback
        return np.linalg.pinv(matrix)
```

### 4.3 Special Case Inverses

**Translation Inverse:**
```python
def inverse_translation(tx, ty):
    """T⁻¹(tx, ty) = T(-tx, -ty)"""
    return translation_matrix(-tx, -ty)
```

**Scaling Inverse:**
```python
def inverse_scaling(sx, sy):
    """S⁻¹(sx, sy) = S(1/sx, 1/sy)"""
    if abs(sx) < 1e-10 or abs(sy) < 1e-10:
        raise ValueError("Cannot invert zero scaling")
    return scaling_matrix(1.0/sx, 1.0/sy)
```

**Rotation Inverse:**
```python
def inverse_rotation(theta):
    """R⁻¹(θ) = R(-θ) = R^T"""
    return rotation_matrix(-theta)
```

### 4.4 Validation Through Round-Trip

```python
def validate_inverse(matrix, tolerance=1e-9):
    """
    Validate inverse transformation through round-trip

    Parameters:
    - matrix: original transformation matrix
    - tolerance: maximum allowed error

    Returns: (is_valid, max_error)
    """
    # Compute inverse
    inv_matrix = inverse_affine_transform(matrix)

    # Compute M × M⁻¹
    product = matrix @ inv_matrix

    # Should equal identity matrix
    identity = np.eye(3, dtype=np.float64)

    # Compute maximum error
    error = np.abs(product - identity)
    max_error = np.max(error)

    is_valid = max_error < tolerance

    return is_valid, max_error

def test_round_trip_transformation(transform_matrix, test_points):
    """
    Test round-trip transformation accuracy

    Parameters:
    - transform_matrix: transformation to test
    - test_points: Nx2 array of test coordinates

    Returns: maximum round-trip error in pixels
    """
    # Convert to homogeneous
    homogeneous = to_homogeneous(test_points)

    # Forward transform
    transformed = (transform_matrix @ homogeneous.T).T

    # Inverse transform
    inv_matrix = inverse_affine_transform(transform_matrix)
    recovered = (inv_matrix @ transformed.T).T

    # Compute error
    error = np.abs(homogeneous - recovered)
    max_error = np.max(error[:, :2])  # Ignore homogeneous coordinate

    return max_error
```

---

## 5. Error Propagation in Coordinate Chains

### 5.1 Error Propagation Theory

When transforming through multiple coordinate systems:
```
OS → Browser Viewport → Document → Element → Target
```

Errors accumulate at each stage. For a chain of transformations:

```
P' = Mn × ... × M2 × M1 × P
```

**Error accumulation:**
```
σ²_total = σ²_1 + σ²_2 + ... + σ²_n
```

For independent errors, standard deviation grows as:
```
σ_total = √(σ²_1 + σ²_2 + ... + σ²_n)
```

### 5.2 Jacobian-Based Error Propagation

For transformation f(x, y) = (x', y'), the Jacobian matrix is:

```
J = [∂x'/∂x  ∂x'/∂y]
    [∂y'/∂x  ∂y'/∂y]
```

For affine transformation:
```
J = [a  b]
    [c  d]
```

**Error propagation:**
```
Σ_output = J × Σ_input × J^T
```

Where Σ is the covariance matrix.

### 5.3 Implementation

```python
class CoordinateErrorAnalysis:
    """
    Analyze and track error propagation through transformations
    """

    @staticmethod
    def affine_jacobian(matrix):
        """
        Extract Jacobian from affine transformation matrix

        For affine transform, Jacobian is the linear part
        """
        return matrix[:2, :2]

    @staticmethod
    def propagate_error_covariance(covariance_in, transform_matrix):
        """
        Propagate error covariance through transformation

        Parameters:
        - covariance_in: 2x2 input covariance matrix
        - transform_matrix: 3x3 affine transformation

        Returns: 2x2 output covariance matrix
        """
        J = CoordinateErrorAnalysis.affine_jacobian(transform_matrix)

        # Σ_out = J × Σ_in × J^T
        covariance_out = J @ covariance_in @ J.T

        return covariance_out

    @staticmethod
    def propagate_error_std(std_x, std_y, transform_matrix):
        """
        Propagate standard deviation through transformation

        Parameters:
        - std_x, std_y: input standard deviations
        - transform_matrix: 3x3 affine transformation

        Returns: (std_x_out, std_y_out)
        """
        # Create diagonal covariance matrix
        covariance_in = np.diag([std_x**2, std_y**2])

        # Propagate
        covariance_out = CoordinateErrorAnalysis.propagate_error_covariance(
            covariance_in, transform_matrix
        )

        # Extract standard deviations
        std_x_out = np.sqrt(covariance_out[0, 0])
        std_y_out = np.sqrt(covariance_out[1, 1])

        return std_x_out, std_y_out

    @staticmethod
    def error_ellipse(covariance, confidence=0.95):
        """
        Compute error ellipse parameters from covariance matrix

        Parameters:
        - covariance: 2x2 covariance matrix
        - confidence: confidence level (default 95%)

        Returns: (semi_major, semi_minor, angle)
        """
        # Eigenvalue decomposition
        eigenvalues, eigenvectors = np.linalg.eig(covariance)

        # Sort by eigenvalue (descending)
        idx = eigenvalues.argsort()[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Chi-square value for confidence level
        from scipy.stats import chi2
        s = chi2.ppf(confidence, df=2)

        # Semi-axes lengths
        semi_major = np.sqrt(s * eigenvalues[0])
        semi_minor = np.sqrt(s * eigenvalues[1])

        # Angle of major axis
        angle = np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0])

        return semi_major, semi_minor, angle

class TransformationChainError:
    """
    Track error propagation through transformation chain
    """

    def __init__(self, initial_std_x=0.5, initial_std_y=0.5):
        """
        Initialize with initial measurement uncertainty

        Default: 0.5 pixels (sub-pixel uncertainty)
        """
        self.initial_covariance = np.diag([initial_std_x**2, initial_std_y**2])
        self.current_covariance = self.initial_covariance.copy()
        self.transform_count = 0

    def add_transformation(self, transform_matrix, measurement_noise=None):
        """
        Add transformation to chain and propagate error

        Parameters:
        - transform_matrix: 3x3 affine transformation
        - measurement_noise: optional 2x2 covariance matrix for additional noise
        """
        # Propagate existing error
        self.current_covariance = CoordinateErrorAnalysis.propagate_error_covariance(
            self.current_covariance, transform_matrix
        )

        # Add measurement noise if provided
        if measurement_noise is not None:
            self.current_covariance += measurement_noise

        self.transform_count += 1

    def get_current_std(self):
        """
        Get current standard deviations

        Returns: (std_x, std_y)
        """
        std_x = np.sqrt(self.current_covariance[0, 0])
        std_y = np.sqrt(self.current_covariance[1, 1])
        return std_x, std_y

    def get_total_error_bound(self, confidence=0.95):
        """
        Get total error bound at given confidence level

        Returns: maximum error radius in pixels
        """
        semi_major, semi_minor, _ = CoordinateErrorAnalysis.error_ellipse(
            self.current_covariance, confidence
        )
        return semi_major  # Conservative bound
```

### 5.4 Conditioning and Sensitivity Analysis

```python
def compute_condition_number(matrix):
    """
    Compute condition number of transformation matrix

    A high condition number indicates numerical instability

    Returns: condition number (1.0 = perfect, ∞ = singular)
    """
    # Extract linear part
    linear = matrix[:2, :2]

    # Compute singular values
    singular_values = np.linalg.svd(linear, compute_uv=False)

    # Condition number = max(σ) / min(σ)
    if singular_values[-1] < 1e-10:
        return np.inf

    return singular_values[0] / singular_values[-1]

def sensitivity_analysis(transform_matrix, point, perturbation=1e-6):
    """
    Analyze sensitivity of transformation at a point

    Parameters:
    - transform_matrix: 3x3 transformation
    - point: (x, y) coordinate
    - perturbation: small delta for numerical derivative

    Returns: sensitivity measure (max change per unit input change)
    """
    x, y = point

    # Transform original point
    p0 = np.array([x, y, 1])
    t0 = transform_matrix @ p0

    # Perturb in x direction
    px = np.array([x + perturbation, y, 1])
    tx = transform_matrix @ px
    sensitivity_x = np.linalg.norm(tx[:2] - t0[:2]) / perturbation

    # Perturb in y direction
    py = np.array([x, y + perturbation, 1])
    ty = transform_matrix @ py
    sensitivity_y = np.linalg.norm(ty[:2] - t0[:2]) / perturbation

    return max(sensitivity_x, sensitivity_y)
```

---

## 6. Numerical Precision and Floating-Point Considerations

### 6.1 Floating-Point Representation

**IEEE 754 Double Precision (float64):**
- 1 sign bit
- 11 exponent bits
- 52 mantissa bits
- Machine epsilon: ε ≈ 2.22 × 10⁻¹⁶
- Precision: ~15-17 decimal digits

**Key Considerations:**
1. Catastrophic cancellation
2. Loss of significance
3. Accumulation of rounding errors
4. Non-associativity of floating-point arithmetic

### 6.2 Precision-Preserving Strategies

```python
class PreciseCoordinateTransform:
    """
    High-precision coordinate transformation with error mitigation
    """

    # Use float64 consistently
    DTYPE = np.float64

    # Machine epsilon for float64
    EPSILON = np.finfo(np.float64).eps

    # Tolerance for comparisons
    TOLERANCE = 1e-9

    @staticmethod
    def stable_matrix_multiply(A, B):
        """
        Numerically stable matrix multiplication

        Uses Kahan summation for reduced rounding error
        """
        result = np.zeros((3, 3), dtype=PreciseCoordinateTransform.DTYPE)

        for i in range(3):
            for j in range(3):
                # Kahan summation algorithm
                sum_val = 0.0
                compensation = 0.0

                for k in range(3):
                    term = A[i, k] * B[k, j]
                    y = term - compensation
                    t = sum_val + y
                    compensation = (t - sum_val) - y
                    sum_val = t

                result[i, j] = sum_val

        return result

    @staticmethod
    def compensated_summation(values):
        """
        Kahan compensated summation algorithm

        Reduces rounding errors in summation
        """
        sum_val = 0.0
        compensation = 0.0

        for value in values:
            y = value - compensation
            t = sum_val + y
            compensation = (t - sum_val) - y
            sum_val = t

        return sum_val

    @staticmethod
    def nearly_equal(a, b, tolerance=None):
        """
        Compare floating-point values with tolerance

        Uses relative and absolute tolerance
        """
        if tolerance is None:
            tolerance = PreciseCoordinateTransform.TOLERANCE

        # Absolute difference
        abs_diff = abs(a - b)

        # Relative tolerance
        rel_tolerance = tolerance * max(abs(a), abs(b))

        return abs_diff <= max(tolerance, rel_tolerance)

    @staticmethod
    def snap_to_subpixel_grid(x, y, subpixel_divisions=256):
        """
        Snap coordinates to sub-pixel grid for consistency

        Parameters:
        - x, y: coordinates
        - subpixel_divisions: number of subdivisions per pixel
          (default 256 = 1/256 pixel precision)

        Returns: snapped (x, y)
        """
        scale = float(subpixel_divisions)
        x_snapped = np.round(x * scale) / scale
        y_snapped = np.round(y * scale) / scale
        return x_snapped, y_snapped
```

### 6.3 Precision Analysis

```python
def analyze_transformation_precision(matrix, test_points):
    """
    Analyze numerical precision of transformation

    Parameters:
    - matrix: transformation matrix to analyze
    - test_points: Nx2 array of test coordinates

    Returns: dict with precision metrics
    """
    # Forward transform
    homogeneous = to_homogeneous(test_points)
    transformed = (matrix @ homogeneous.T).T

    # Backward transform (should recover original)
    inv_matrix = inverse_affine_transform(matrix)
    recovered = (inv_matrix @ transformed.T).T

    # Compute round-trip error
    error = np.abs(recovered[:, :2] - test_points)

    metrics = {
        'max_error': np.max(error),
        'mean_error': np.mean(error),
        'std_error': np.std(error),
        'error_x': error[:, 0],
        'error_y': error[:, 1],
        'max_error_x': np.max(error[:, 0]),
        'max_error_y': np.max(error[:, 1]),
        'condition_number': compute_condition_number(matrix)
    }

    return metrics

def optimal_transformation_order(transforms):
    """
    Determine optimal order for transform composition

    Minimize numerical error by ordering from smallest to largest
    condition numbers

    Parameters:
    - transforms: list of transformation matrices

    Returns: reordered list of transforms
    """
    # Compute condition numbers
    conditions = [compute_condition_number(T) for T in transforms]

    # Sort by condition number (ascending)
    sorted_indices = np.argsort(conditions)

    return [transforms[i] for i in sorted_indices]
```

### 6.4 Sub-Pixel Accuracy Validation

```python
class SubPixelValidator:
    """
    Validate and ensure sub-pixel accuracy in transformations
    """

    # Target accuracy: 1/256 pixel = ~0.004 pixels
    TARGET_ACCURACY = 1.0 / 256.0

    @staticmethod
    def validate_subpixel_accuracy(transform_matrix, num_tests=1000):
        """
        Validate transformation achieves sub-pixel accuracy

        Parameters:
        - transform_matrix: transformation to test
        - num_tests: number of random test points

        Returns: (is_subpixel_accurate, max_error, report)
        """
        # Generate random test points in typical screen coordinates
        np.random.seed(42)
        test_points = np.random.rand(num_tests, 2) * 1920  # Typical screen width

        # Analyze precision
        metrics = analyze_transformation_precision(transform_matrix, test_points)

        # Check if meets sub-pixel criteria
        is_accurate = metrics['max_error'] < SubPixelValidator.TARGET_ACCURACY

        report = {
            'target_accuracy': SubPixelValidator.TARGET_ACCURACY,
            'achieved_accuracy': metrics['max_error'],
            'mean_error': metrics['mean_error'],
            'condition_number': metrics['condition_number'],
            'is_subpixel_accurate': is_accurate,
            'accuracy_ratio': metrics['max_error'] / SubPixelValidator.TARGET_ACCURACY
        }

        return is_accurate, metrics['max_error'], report

    @staticmethod
    def improve_numerical_stability(matrix):
        """
        Attempt to improve numerical stability of matrix

        Techniques:
        1. Normalize scale components
        2. Orthogonalize rotation components
        3. Remove numerical noise
        """
        # Decompose matrix
        decomp = decompose_affine(matrix)

        # Rebuild with cleaned components
        sx, sy = decomp['scale']
        theta = decomp['rotation']
        tx, ty = decomp['translation']

        # Rebuild transformation
        improved = create_srt_transform(sx, sy, theta, tx, ty)

        return improved
```

---

## 7. Calibration and Correction Algorithms

### 7.1 Point-Based Calibration

Given known point correspondences:
```
OS points: (x1, y1), (x2, y2), (x3, y3), ...
DOM points: (x1', y1'), (x2', y2'), (x3', y3'), ...
```

Find transformation matrix M such that:
```
[xi']   [a  b  tx]   [xi]
[yi'] = [c  d  ty] × [yi]
[1  ]   [0  0   1]   [1 ]
```

### 7.2 Least Squares Solution

**For n ≥ 3 point pairs, solve overdetermined system:**

```python
def calibrate_affine_transform(source_points, target_points):
    """
    Calibrate affine transformation from point correspondences

    Uses least squares to find best-fit transformation

    Parameters:
    - source_points: Nx2 array of source (OS) coordinates
    - target_points: Nx2 array of target (DOM) coordinates

    Returns: 3x3 affine transformation matrix

    Minimum 3 non-collinear point pairs required
    """
    n = len(source_points)

    if n < 3:
        raise ValueError("At least 3 point pairs required for calibration")

    # Check for collinearity
    if n == 3:
        if are_collinear(source_points):
            raise ValueError("Points are collinear, cannot determine unique transformation")

    # Build system: A × x = b
    # For each point: [xi yi 1 0  0  0 ] [a ]   [xi']
    #                 [0  0  0 xi yi 1 ] [b ]   [yi']
    #                                     [tx]
    #                                     [c ]
    #                                     [d ]
    #                                     [ty]

    A = np.zeros((2*n, 6), dtype=np.float64)
    b = np.zeros(2*n, dtype=np.float64)

    for i in range(n):
        xi, yi = source_points[i]
        xi_prime, yi_prime = target_points[i]

        # Row for x' equation
        A[2*i] = [xi, yi, 1, 0, 0, 0]
        b[2*i] = xi_prime

        # Row for y' equation
        A[2*i + 1] = [0, 0, 0, xi, yi, 1]
        b[2*i + 1] = yi_prime

    # Solve using least squares
    params, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)

    # Extract parameters
    a, b_param, tx, c, d, ty = params

    # Build transformation matrix
    matrix = np.array([
        [a, b_param, tx],
        [c, d,       ty],
        [0, 0,        1]
    ], dtype=np.float64)

    # Compute calibration quality metrics
    residual_error = np.sqrt(np.sum(residuals) / n) if len(residuals) > 0 else 0

    return matrix, residual_error

def are_collinear(points, tolerance=1e-9):
    """
    Check if points are collinear

    Uses cross product method
    """
    if len(points) < 3:
        return True

    p1, p2, p3 = points[:3]

    # Vectors
    v1 = p2 - p1
    v2 = p3 - p1

    # Cross product (in 2D, returns scalar)
    cross = v1[0] * v2[1] - v1[1] * v2[0]

    return abs(cross) < tolerance
```

### 7.3 RANSAC for Robust Calibration

Handle outliers in calibration data:

```python
def calibrate_ransac(source_points, target_points,
                     max_iterations=1000,
                     inlier_threshold=2.0,
                     min_inliers=None):
    """
    RANSAC-based robust calibration

    Handles outliers in point correspondences

    Parameters:
    - source_points: Nx2 array of source coordinates
    - target_points: Nx2 array of target coordinates
    - max_iterations: maximum RANSAC iterations
    - inlier_threshold: maximum error for inliers (pixels)
    - min_inliers: minimum number of inliers (default: 60% of points)

    Returns: (best_matrix, inlier_mask, num_inliers)
    """
    n = len(source_points)

    if min_inliers is None:
        min_inliers = int(0.6 * n)

    best_matrix = None
    best_inliers = 0
    best_inlier_mask = None

    for iteration in range(max_iterations):
        # Randomly sample 3 point pairs
        sample_indices = np.random.choice(n, 3, replace=False)
        sample_source = source_points[sample_indices]
        sample_target = target_points[sample_indices]

        # Check for collinearity
        if are_collinear(sample_source):
            continue

        try:
            # Fit transformation to sample
            matrix, _ = calibrate_affine_transform(sample_source, sample_target)
        except:
            continue

        # Test on all points
        transformed = transform_points_batch(source_points, matrix)
        errors = np.linalg.norm(transformed - target_points, axis=1)

        # Count inliers
        inlier_mask = errors < inlier_threshold
        num_inliers = np.sum(inlier_mask)

        # Update best model
        if num_inliers > best_inliers:
            best_inliers = num_inliers
            best_matrix = matrix
            best_inlier_mask = inlier_mask

        # Early exit if we have enough inliers
        if best_inliers >= min_inliers:
            break

    if best_matrix is None:
        raise ValueError("RANSAC failed to find valid transformation")

    # Refit using all inliers
    inlier_source = source_points[best_inlier_mask]
    inlier_target = target_points[best_inlier_mask]

    final_matrix, residual = calibrate_affine_transform(inlier_source, inlier_target)

    return final_matrix, best_inlier_mask, best_inliers

def transform_points_batch(points, matrix):
    """Helper: transform batch of points"""
    homogeneous = to_homogeneous(points)
    transformed = (matrix @ homogeneous.T).T
    return transformed[:, :2]
```

### 7.4 Iterative Refinement

```python
def iterative_refinement(initial_matrix, source_points, target_points,
                        max_iterations=10, convergence_threshold=1e-6):
    """
    Iteratively refine transformation using weighted least squares

    Parameters:
    - initial_matrix: initial transformation estimate
    - source_points: Nx2 source coordinates
    - target_points: Nx2 target coordinates
    - max_iterations: maximum refinement iterations
    - convergence_threshold: stop when change < threshold

    Returns: refined transformation matrix
    """
    current_matrix = initial_matrix.copy()

    for iteration in range(max_iterations):
        # Transform points with current matrix
        transformed = transform_points_batch(source_points, current_matrix)

        # Compute errors
        errors = np.linalg.norm(transformed - target_points, axis=1)

        # Compute weights (inverse of error)
        # Points with smaller errors get higher weight
        weights = 1.0 / (errors + 1e-6)
        weights = weights / np.sum(weights)  # Normalize

        # Weighted least squares
        refined_matrix = weighted_calibration(
            source_points, target_points, weights
        )

        # Check convergence
        matrix_change = np.linalg.norm(refined_matrix - current_matrix)

        if matrix_change < convergence_threshold:
            break

        current_matrix = refined_matrix

    return current_matrix

def weighted_calibration(source_points, target_points, weights):
    """
    Weighted least squares calibration

    Parameters:
    - source_points: Nx2 source coordinates
    - target_points: Nx2 target coordinates
    - weights: N-element array of weights

    Returns: 3x3 transformation matrix
    """
    n = len(source_points)

    # Build weighted system
    A = np.zeros((2*n, 6), dtype=np.float64)
    b = np.zeros(2*n, dtype=np.float64)
    W = np.zeros(2*n, dtype=np.float64)

    for i in range(n):
        xi, yi = source_points[i]
        xi_prime, yi_prime = target_points[i]
        w = weights[i]

        # Row for x' equation
        A[2*i] = [xi, yi, 1, 0, 0, 0]
        b[2*i] = xi_prime
        W[2*i] = w

        # Row for y' equation
        A[2*i + 1] = [0, 0, 0, xi, yi, 1]
        b[2*i + 1] = yi_prime
        W[2*i + 1] = w

    # Weighted least squares: (A^T W A) x = A^T W b
    W_matrix = np.diag(W)
    A_weighted = A.T @ W_matrix @ A
    b_weighted = A.T @ W_matrix @ b

    # Solve
    params = np.linalg.solve(A_weighted, b_weighted)

    # Build matrix
    a, b_param, tx, c, d, ty = params
    matrix = np.array([
        [a, b_param, tx],
        [c, d,       ty],
        [0, 0,        1]
    ], dtype=np.float64)

    return matrix
```

### 7.5 Multi-Scale Calibration

```python
class MultiScaleCalibration:
    """
    Hierarchical calibration for different zoom levels
    """

    def __init__(self):
        self.calibrations = {}  # zoom_level -> transformation matrix

    def add_calibration(self, zoom_level, matrix):
        """
        Add calibration for specific zoom level
        """
        self.calibrations[zoom_level] = matrix.copy()

    def get_transform_for_zoom(self, zoom_level):
        """
        Get transformation for given zoom level

        Interpolates if exact zoom not calibrated
        """
        if zoom_level in self.calibrations:
            return self.calibrations[zoom_level]

        # Find nearest calibrated zoom levels
        zoom_levels = sorted(self.calibrations.keys())

        if not zoom_levels:
            raise ValueError("No calibrations available")

        if zoom_level < zoom_levels[0]:
            # Use lowest calibrated zoom
            return self.calibrations[zoom_levels[0]]

        if zoom_level > zoom_levels[-1]:
            # Use highest calibrated zoom
            return self.calibrations[zoom_levels[-1]]

        # Interpolate between two nearest zooms
        for i in range(len(zoom_levels) - 1):
            z1, z2 = zoom_levels[i], zoom_levels[i+1]

            if z1 <= zoom_level <= z2:
                # Interpolation parameter
                t = (zoom_level - z1) / (z2 - z1)

                M1 = self.calibrations[z1]
                M2 = self.calibrations[z2]

                # Interpolate transformation
                return interpolate_transforms(M1, M2, t)

        # Fallback
        return self.calibrations[zoom_levels[0]]

    def calibrate_zoom_level(self, zoom_level, source_points, target_points):
        """
        Calibrate transformation for specific zoom level
        """
        matrix, error = calibrate_affine_transform(source_points, target_points)
        self.add_calibration(zoom_level, matrix)
        return matrix, error
```

### 7.6 Adaptive Correction

```python
class AdaptiveCorrection:
    """
    Adaptive correction based on ongoing validation
    """

    def __init__(self, initial_transform):
        self.transform = initial_transform.copy()
        self.correction_history = []
        self.max_history = 100

    def add_correction_sample(self, source, target, actual):
        """
        Add a correction sample from user feedback

        Parameters:
        - source: OS coordinate
        - target: predicted DOM coordinate
        - actual: actual DOM coordinate (ground truth)
        """
        error = np.array(actual) - np.array(target)

        self.correction_history.append({
            'source': source,
            'target': target,
            'actual': actual,
            'error': error,
            'error_magnitude': np.linalg.norm(error)
        })

        # Limit history size
        if len(self.correction_history) > self.max_history:
            self.correction_history.pop(0)

    def compute_adaptive_correction(self, point):
        """
        Compute adaptive correction at given point

        Uses inverse distance weighting of nearby corrections
        """
        if not self.correction_history:
            return (0, 0)

        # Compute distances to all correction samples
        distances = []
        corrections = []

        for sample in self.correction_history:
            source = np.array(sample['source'])
            dist = np.linalg.norm(point - source)

            if dist < 1e-6:
                # Very close match, use this correction directly
                return tuple(sample['error'])

            distances.append(dist)
            corrections.append(sample['error'])

        distances = np.array(distances)
        corrections = np.array(corrections)

        # Inverse distance weighting
        # Use power of 2 for stronger locality
        weights = 1.0 / (distances ** 2)
        weights = weights / np.sum(weights)

        # Weighted average correction
        adaptive_correction = np.sum(
            corrections * weights[:, np.newaxis],
            axis=0
        )

        return tuple(adaptive_correction)

    def transform_with_correction(self, x, y):
        """
        Transform point with adaptive correction
        """
        # Base transformation
        base_point = np.array([x, y, 1])
        transformed = self.transform @ base_point
        x_t, y_t = transformed[0], transformed[1]

        # Adaptive correction
        correction = self.compute_adaptive_correction(np.array([x, y]))

        # Apply correction
        x_final = x_t + correction[0]
        y_final = y_t + correction[1]

        return x_final, y_final

    def update_transform(self):
        """
        Update base transformation using correction history
        """
        if len(self.correction_history) < 3:
            return

        # Extract source and actual target points
        sources = np.array([s['source'] for s in self.correction_history])
        actuals = np.array([s['actual'] for s in self.correction_history])

        # Re-calibrate transformation
        try:
            new_transform, _ = calibrate_affine_transform(sources, actuals)
            self.transform = new_transform

            # Clear history after updating
            self.correction_history = []
        except:
            pass  # Keep existing transformation if calibration fails
```

---

## 8. Complete Implementation Example

```python
"""
Complete OS to DOM coordinate transformation system
with sub-pixel accuracy
"""

import numpy as np
from typing import Tuple, List, Optional

class OSToDOM_Transformer:
    """
    High-precision OS to DOM coordinate transformer
    """

    def __init__(self):
        # Primary transformation matrix (OS → DOM)
        self.forward_transform = np.eye(3, dtype=np.float64)

        # Cached inverse transformation (DOM → OS)
        self.inverse_transform = np.eye(3, dtype=np.float64)
        self._inverse_dirty = False

        # Error tracking
        self.error_tracker = TransformationChainError()

        # Adaptive correction
        self.adaptive = None

        # Calibration data
        self.calibration_points = {'source': [], 'target': []}

    def calibrate(self, os_points: np.ndarray, dom_points: np.ndarray,
                  use_ransac: bool = True) -> float:
        """
        Calibrate transformation from point correspondences

        Parameters:
        - os_points: Nx2 array of OS coordinates
        - dom_points: Nx2 array of DOM coordinates
        - use_ransac: use RANSAC for outlier rejection

        Returns: calibration residual error
        """
        if use_ransac and len(os_points) > 10:
            matrix, inlier_mask, num_inliers = calibrate_ransac(
                os_points, dom_points
            )
            print(f"RANSAC: {num_inliers}/{len(os_points)} inliers")
        else:
            matrix, residual = calibrate_affine_transform(os_points, dom_points)

        # Set transformation
        self.forward_transform = matrix
        self._inverse_dirty = True

        # Initialize adaptive correction
        self.adaptive = AdaptiveCorrection(matrix)

        # Validate sub-pixel accuracy
        validator = SubPixelValidator()
        is_accurate, max_error, report = validator.validate_subpixel_accuracy(matrix)

        print(f"Sub-pixel validation: {report}")

        return max_error

    def transform_os_to_dom(self, x: float, y: float,
                           use_adaptive: bool = False) -> Tuple[float, float]:
        """
        Transform OS coordinates to DOM coordinates

        Parameters:
        - x, y: OS coordinates
        - use_adaptive: apply adaptive correction

        Returns: (x_dom, y_dom) with sub-pixel precision
        """
        if use_adaptive and self.adaptive is not None:
            return self.adaptive.transform_with_correction(x, y)

        point = np.array([x, y, 1], dtype=np.float64)
        transformed = self.forward_transform @ point

        return transformed[0], transformed[1]

    def transform_dom_to_os(self, x: float, y: float) -> Tuple[float, float]:
        """
        Transform DOM coordinates back to OS coordinates

        For validation and reverse mapping
        """
        # Update inverse if needed
        if self._inverse_dirty:
            self.inverse_transform = inverse_affine_transform(
                self.forward_transform
            )
            self._inverse_dirty = False

        point = np.array([x, y, 1], dtype=np.float64)
        transformed = self.inverse_transform @ point

        return transformed[0], transformed[1]

    def validate_round_trip(self, test_points: np.ndarray) -> dict:
        """
        Validate transformation accuracy via round-trip
        """
        errors = []

        for x, y in test_points:
            # OS → DOM → OS
            x_dom, y_dom = self.transform_os_to_dom(x, y)
            x_recovered, y_recovered = self.transform_dom_to_os(x_dom, y_dom)

            error = np.sqrt((x - x_recovered)**2 + (y - y_recovered)**2)
            errors.append(error)

        errors = np.array(errors)

        return {
            'max_error': np.max(errors),
            'mean_error': np.mean(errors),
            'std_error': np.std(errors),
            'median_error': np.median(errors),
            'subpixel_accurate': np.max(errors) < 1.0/256.0
        }

    def get_transformation_info(self) -> dict:
        """
        Get detailed information about current transformation
        """
        decomp = decompose_affine(self.forward_transform)
        condition = compute_condition_number(self.forward_transform)

        return {
            'matrix': self.forward_transform,
            'translation': decomp['translation'],
            'rotation_deg': np.degrees(decomp['rotation']),
            'scale': decomp['scale'],
            'shear': decomp['shear'],
            'determinant': decomp['determinant'],
            'condition_number': condition,
            'numerically_stable': condition < 100
        }

# Example usage
def example_usage():
    """
    Example: Calibrate and use OS to DOM transformer
    """
    # Create transformer
    transformer = OSToDOM_Transformer()

    # Calibration data (example)
    # In practice, these would come from actual measurements
    os_calibration_points = np.array([
        [100, 100],
        [500, 100],
        [100, 400],
        [500, 400],
        [300, 250]
    ], dtype=np.float64)

    # DOM coordinates (with scaling and offset)
    dom_calibration_points = np.array([
        [150, 180],
        [750, 180],
        [150, 680],
        [750, 680],
        [450, 430]
    ], dtype=np.float64)

    # Calibrate
    error = transformer.calibrate(os_calibration_points, dom_calibration_points)
    print(f"Calibration error: {error:.6f} pixels")

    # Get transformation info
    info = transformer.get_transformation_info()
    print(f"Transformation info: {info}")

    # Transform a point
    x_os, y_os = 300, 250
    x_dom, y_dom = transformer.transform_os_to_dom(x_os, y_os)
    print(f"OS ({x_os}, {y_os}) → DOM ({x_dom:.3f}, {y_dom:.3f})")

    # Validate
    validation = transformer.validate_round_trip(os_calibration_points)
    print(f"Validation: {validation}")

    return transformer

if __name__ == "__main__":
    transformer = example_usage()
```

---

## Summary

This document provides comprehensive mathematical models for OS to DOM coordinate transformation with sub-pixel accuracy:

1. **Affine Transformations**: Complete matrix formulation and decomposition
2. **Basic Transformations**: Translation, scaling, rotation with arbitrary pivot points
3. **Homogeneous Coordinates**: Unified representation and composition
4. **Inverse Transformations**: Analytical and numerical methods with validation
5. **Error Propagation**: Covariance-based error tracking through transformation chains
6. **Numerical Precision**: Float64 precision with Kahan summation and stability analysis
7. **Calibration**: Least squares, RANSAC, iterative refinement, and adaptive correction

All implementations use float64 precision and include validation for sub-pixel accuracy (< 1/256 pixel).
