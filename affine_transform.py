"""
Affine Transformation Module
High-precision 2D coordinate transformations for OS to DOM conversion
"""

import numpy as np
from typing import Tuple, Optional, List


class AffineTransform2D:
    """
    2D Affine transformation with sub-pixel precision

    Represents transformations of the form:
        x' = a·x + b·y + tx
        y' = c·x + d·y + ty

    Uses float64 precision throughout for maximum accuracy.
    """

    def __init__(self, matrix: Optional[np.ndarray] = None):
        """
        Initialize affine transformation

        Parameters:
        - matrix: 3x3 transformation matrix (default: identity)
        """
        if matrix is None:
            self.matrix = np.eye(3, dtype=np.float64)
        else:
            self.matrix = np.array(matrix, dtype=np.float64)
            if self.matrix.shape != (3, 3):
                raise ValueError("Matrix must be 3x3")

    @classmethod
    def from_components(cls, a: float, b: float, c: float, d: float,
                       tx: float, ty: float) -> 'AffineTransform2D':
        """
        Create transformation from individual components

        Parameters:
        - a, d: scaling factors
        - b, c: shearing/rotation factors
        - tx, ty: translation offsets
        """
        matrix = np.array([
            [a,  b,  tx],
            [c,  d,  ty],
            [0,  0,   1]
        ], dtype=np.float64)
        return cls(matrix)

    @classmethod
    def translation(cls, tx: float, ty: float) -> 'AffineTransform2D':
        """Create translation transformation"""
        return cls.from_components(1, 0, 0, 1, tx, ty)

    @classmethod
    def scaling(cls, sx: float, sy: Optional[float] = None) -> 'AffineTransform2D':
        """
        Create scaling transformation

        Parameters:
        - sx: x-axis scale factor
        - sy: y-axis scale factor (defaults to sx for uniform scaling)
        """
        if sy is None:
            sy = sx
        return cls.from_components(sx, 0, 0, sy, 0, 0)

    @classmethod
    def rotation(cls, theta: float) -> 'AffineTransform2D':
        """
        Create rotation transformation

        Parameters:
        - theta: rotation angle in radians (counter-clockwise)
        """
        cos_theta = np.cos(theta)
        sin_theta = np.sin(theta)
        return cls.from_components(cos_theta, -sin_theta, sin_theta, cos_theta, 0, 0)

    @classmethod
    def rotation_degrees(cls, degrees: float) -> 'AffineTransform2D':
        """Create rotation from degrees"""
        return cls.rotation(np.radians(degrees))

    @classmethod
    def scale_rotate_translate(cls, sx: float, sy: float, theta: float,
                              tx: float, ty: float) -> 'AffineTransform2D':
        """
        Create combined Scale-Rotate-Translate transformation

        Order: Scale -> Rotate -> Translate
        """
        S = cls.scaling(sx, sy)
        R = cls.rotation(theta)
        T = cls.translation(tx, ty)
        return T @ R @ S

    def transform_point(self, x: float, y: float) -> Tuple[float, float]:
        """
        Transform a single point with sub-pixel accuracy

        Returns: (x', y') as float64
        """
        point = np.array([x, y, 1], dtype=np.float64)
        transformed = self.matrix @ point
        return float(transformed[0]), float(transformed[1])

    def transform_points(self, points: np.ndarray) -> np.ndarray:
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

    def inverse(self) -> 'AffineTransform2D':
        """
        Compute inverse transformation

        Returns: AffineTransform2D representing inverse

        Raises:
        - ValueError if matrix is singular
        """
        a, b, tx = self.matrix[0, :]
        c, d, ty = self.matrix[1, :]

        # Compute determinant
        det = a * d - b * c

        # Check for singularity
        if abs(det) < 1e-10:
            raise ValueError(
                f"Matrix is singular (det={det}), cannot invert"
            )

        # Compute inverse using analytical formula
        inv_matrix = np.array([
            [ d/det, -b/det, (b*ty - d*tx)/det],
            [-c/det,  a/det, (c*tx - a*ty)/det],
            [ 0.0,    0.0,    1.0              ]
        ], dtype=np.float64)

        return AffineTransform2D(inv_matrix)

    def decompose(self) -> dict:
        """
        Decompose transformation into components

        Returns: dict with 'translation', 'rotation', 'scale', 'shear'
        """
        a, b, tx = self.matrix[0, :]
        c, d, ty = self.matrix[1, :]

        # Translation
        translation = (float(tx), float(ty))

        # Determinant
        det = a * d - b * c

        # Rotation angle
        rotation = np.arctan2(c, a)

        # Scale factors
        sx = np.sqrt(a**2 + c**2)
        sy = det / sx if abs(sx) > 1e-10 else 0

        # Shear
        shear = (a * b + c * d) / (a**2 + c**2) if abs(a**2 + c**2) > 1e-10 else 0

        return {
            'translation': translation,
            'rotation': float(rotation),  # radians
            'rotation_degrees': float(np.degrees(rotation)),
            'scale': (float(sx), float(sy)),
            'shear': float(shear),
            'determinant': float(det)
        }

    def __matmul__(self, other: 'AffineTransform2D') -> 'AffineTransform2D':
        """
        Compose transformations using @ operator

        Usage: M3 = M1 @ M2
        """
        if not isinstance(other, AffineTransform2D):
            return NotImplemented

        result_matrix = self.matrix @ other.matrix
        return AffineTransform2D(result_matrix)

    def __repr__(self) -> str:
        decomp = self.decompose()
        return (
            f"AffineTransform2D(\n"
            f"  translation: {decomp['translation']},\n"
            f"  rotation: {decomp['rotation_degrees']:.2f}°,\n"
            f"  scale: {decomp['scale']},\n"
            f"  shear: {decomp['shear']:.4f}\n"
            f")"
        )

    def __str__(self) -> str:
        return f"AffineTransform2D:\n{self.matrix}"


def to_homogeneous(points: np.ndarray) -> np.ndarray:
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


def from_homogeneous(points: np.ndarray) -> np.ndarray:
    """
    Convert homogeneous coordinates to 2D Cartesian

    Parameters:
    - points: Nx3 array of (x, y, w) coordinates

    Returns: Nx2 array of (x/w, y/w) coordinates
    """
    w = points[:, 2:3]
    # Avoid division by zero
    w = np.where(np.abs(w) < 1e-10, 1.0, w)
    return points[:, :2] / w


class TransformChain:
    """
    Efficient composition of multiple transformations

    Example:
        chain = TransformChain()
        chain.add_translation(100, 50)
             .add_rotation(np.pi/4)
             .add_scaling(2.0, 2.0)

        x', y' = chain.transform(x, y)
    """

    def __init__(self):
        self.transforms: List[AffineTransform2D] = []
        self._combined: Optional[AffineTransform2D] = None
        self._dirty = True

    def add_translation(self, tx: float, ty: float) -> 'TransformChain':
        """Add translation to chain"""
        self.transforms.append(AffineTransform2D.translation(tx, ty))
        self._dirty = True
        return self

    def add_scaling(self, sx: float, sy: Optional[float] = None) -> 'TransformChain':
        """Add scaling to chain"""
        self.transforms.append(AffineTransform2D.scaling(sx, sy))
        self._dirty = True
        return self

    def add_rotation(self, theta: float) -> 'TransformChain':
        """Add rotation to chain (radians)"""
        self.transforms.append(AffineTransform2D.rotation(theta))
        self._dirty = True
        return self

    def add_rotation_degrees(self, degrees: float) -> 'TransformChain':
        """Add rotation to chain (degrees)"""
        return self.add_rotation(np.radians(degrees))

    def add_transform(self, transform: AffineTransform2D) -> 'TransformChain':
        """Add arbitrary transformation"""
        self.transforms.append(transform)
        self._dirty = True
        return self

    def get_combined(self) -> AffineTransform2D:
        """
        Get combined transformation matrix
        Uses lazy evaluation for efficiency
        """
        if self._dirty or self._combined is None:
            # Start with identity
            self._combined = AffineTransform2D()

            # Multiply all transforms (left to right)
            for transform in self.transforms:
                self._combined = self._combined @ transform

            self._dirty = False

        return self._combined

    def transform(self, x: float, y: float) -> Tuple[float, float]:
        """Transform a point through the chain"""
        combined = self.get_combined()
        return combined.transform_point(x, y)

    def transform_points(self, points: np.ndarray) -> np.ndarray:
        """Transform multiple points through the chain"""
        combined = self.get_combined()
        return combined.transform_points(points)

    def clear(self) -> 'TransformChain':
        """Clear all transformations"""
        self.transforms = []
        self._combined = None
        self._dirty = True
        return self


def compute_condition_number(transform: AffineTransform2D) -> float:
    """
    Compute condition number of transformation matrix

    A high condition number indicates numerical instability

    Returns: condition number (1.0 = perfect, inf = singular)
    """
    # Extract linear part
    linear = transform.matrix[:2, :2]

    # Compute singular values
    singular_values = np.linalg.svd(linear, compute_uv=False)

    # Condition number = max(σ) / min(σ)
    if singular_values[-1] < 1e-10:
        return np.inf

    return float(singular_values[0] / singular_values[-1])


def interpolate_transforms(T1: AffineTransform2D, T2: AffineTransform2D,
                          t: float) -> AffineTransform2D:
    """
    Interpolate between two transformations

    Parameters:
    - T1, T2: transformations to interpolate
    - t: interpolation parameter [0, 1]

    Returns: interpolated transformation
    """
    # Decompose both
    d1 = T1.decompose()
    d2 = T2.decompose()

    # Interpolate components
    tx = (1 - t) * d1['translation'][0] + t * d2['translation'][0]
    ty = (1 - t) * d1['translation'][1] + t * d2['translation'][1]

    sx = (1 - t) * d1['scale'][0] + t * d2['scale'][0]
    sy = (1 - t) * d1['scale'][1] + t * d2['scale'][1]

    # Angle interpolation (shortest path)
    angle1 = d1['rotation']
    angle2 = d2['rotation']
    diff = (angle2 - angle1 + np.pi) % (2 * np.pi) - np.pi
    angle = angle1 + t * diff

    # Reconstruct
    return AffineTransform2D.scale_rotate_translate(sx, sy, angle, tx, ty)


# Example usage
if __name__ == "__main__":
    # Create transformation
    transform = AffineTransform2D.scale_rotate_translate(
        sx=1.5, sy=1.5,           # 1.5x scaling
        theta=np.pi/6,             # 30 degree rotation
        tx=100, ty=50              # translate by (100, 50)
    )

    print(transform)
    print()

    # Transform a point
    x, y = 10, 20
    x_t, y_t = transform.transform_point(x, y)
    print(f"({x}, {y}) -> ({x_t:.3f}, {y_t:.3f})")
    print()

    # Inverse transformation
    inv = transform.inverse()
    x_r, y_r = inv.transform_point(x_t, y_t)
    print(f"Round-trip: ({x_r:.6f}, {y_r:.6f})")
    print(f"Error: {abs(x - x_r):.2e}, {abs(y - y_r):.2e}")
    print()

    # Condition number
    cond = compute_condition_number(transform)
    print(f"Condition number: {cond:.2f}")
