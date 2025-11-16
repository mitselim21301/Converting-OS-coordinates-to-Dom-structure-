"""
Calibration Module
Robust calibration algorithms for OS to DOM coordinate transformation
"""

import numpy as np
from typing import Tuple, Optional
from affine_transform import AffineTransform2D, to_homogeneous


def are_collinear(points: np.ndarray, tolerance: float = 1e-9) -> bool:
    """
    Check if points are collinear

    Parameters:
    - points: Nx2 array of points
    - tolerance: collinearity threshold

    Returns: True if points are collinear
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


def calibrate_affine_transform(source_points: np.ndarray,
                               target_points: np.ndarray) -> Tuple[AffineTransform2D, float]:
    """
    Calibrate affine transformation from point correspondences

    Uses least squares to find best-fit transformation

    Parameters:
    - source_points: Nx2 array of source (OS) coordinates
    - target_points: Nx2 array of target (DOM) coordinates

    Returns: (AffineTransform2D, residual_error)

    Raises:
    - ValueError if insufficient points or points are collinear

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
    transform = AffineTransform2D.from_components(a, b_param, c, d, tx, ty)

    # Compute residual error
    residual_error = float(np.sqrt(np.sum(residuals) / n)) if len(residuals) > 0 else 0.0

    return transform, residual_error


def calibrate_ransac(source_points: np.ndarray,
                     target_points: np.ndarray,
                     max_iterations: int = 1000,
                     inlier_threshold: float = 2.0,
                     min_inliers: Optional[int] = None) -> Tuple[AffineTransform2D, np.ndarray, int]:
    """
    RANSAC-based robust calibration

    Handles outliers in point correspondences

    Parameters:
    - source_points: Nx2 array of source coordinates
    - target_points: Nx2 array of target coordinates
    - max_iterations: maximum RANSAC iterations
    - inlier_threshold: maximum error for inliers (pixels)
    - min_inliers: minimum number of inliers (default: 60% of points)

    Returns: (best_transform, inlier_mask, num_inliers)
    """
    n = len(source_points)

    if min_inliers is None:
        min_inliers = int(0.6 * n)

    best_transform = None
    best_inliers = 0
    best_inlier_mask = None

    rng = np.random.RandomState(42)  # Reproducible

    for iteration in range(max_iterations):
        # Randomly sample 3 point pairs
        sample_indices = rng.choice(n, 3, replace=False)
        sample_source = source_points[sample_indices]
        sample_target = target_points[sample_indices]

        # Check for collinearity
        if are_collinear(sample_source):
            continue

        try:
            # Fit transformation to sample
            transform, _ = calibrate_affine_transform(sample_source, sample_target)
        except:
            continue

        # Test on all points
        transformed = transform.transform_points(source_points)
        errors = np.linalg.norm(transformed - target_points, axis=1)

        # Count inliers
        inlier_mask = errors < inlier_threshold
        num_inliers = np.sum(inlier_mask)

        # Update best model
        if num_inliers > best_inliers:
            best_inliers = num_inliers
            best_transform = transform
            best_inlier_mask = inlier_mask

        # Early exit if we have enough inliers
        if best_inliers >= min_inliers:
            break

    if best_transform is None:
        raise ValueError("RANSAC failed to find valid transformation")

    # Refit using all inliers
    inlier_source = source_points[best_inlier_mask]
    inlier_target = target_points[best_inlier_mask]

    final_transform, residual = calibrate_affine_transform(inlier_source, inlier_target)

    return final_transform, best_inlier_mask, best_inliers


def weighted_calibration(source_points: np.ndarray,
                         target_points: np.ndarray,
                         weights: np.ndarray) -> AffineTransform2D:
    """
    Weighted least squares calibration

    Parameters:
    - source_points: Nx2 source coordinates
    - target_points: Nx2 target coordinates
    - weights: N-element array of weights (sum to 1)

    Returns: AffineTransform2D
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
    return AffineTransform2D.from_components(a, b_param, c, d, tx, ty)


def iterative_refinement(initial_transform: AffineTransform2D,
                        source_points: np.ndarray,
                        target_points: np.ndarray,
                        max_iterations: int = 10,
                        convergence_threshold: float = 1e-6) -> AffineTransform2D:
    """
    Iteratively refine transformation using weighted least squares

    Parameters:
    - initial_transform: initial transformation estimate
    - source_points: Nx2 source coordinates
    - target_points: Nx2 target coordinates
    - max_iterations: maximum refinement iterations
    - convergence_threshold: stop when change < threshold

    Returns: refined AffineTransform2D
    """
    current_transform = initial_transform

    for iteration in range(max_iterations):
        # Transform points with current transformation
        transformed = current_transform.transform_points(source_points)

        # Compute errors
        errors = np.linalg.norm(transformed - target_points, axis=1)

        # Compute weights (inverse of error)
        weights = 1.0 / (errors + 1e-6)
        weights = weights / np.sum(weights)  # Normalize

        # Weighted least squares
        refined_transform = weighted_calibration(
            source_points, target_points, weights
        )

        # Check convergence
        matrix_change = np.linalg.norm(
            refined_transform.matrix - current_transform.matrix
        )

        if matrix_change < convergence_threshold:
            break

        current_transform = refined_transform

    return current_transform


class AdaptiveCorrection:
    """
    Adaptive correction based on ongoing validation

    Maintains a history of corrections and applies
    spatially-weighted corrections to new points
    """

    def __init__(self, base_transform: AffineTransform2D, max_history: int = 100):
        """
        Initialize adaptive correction

        Parameters:
        - base_transform: base transformation
        - max_history: maximum correction samples to keep
        """
        self.transform = base_transform
        self.correction_history = []
        self.max_history = max_history

    def add_correction_sample(self, source: Tuple[float, float],
                             target: Tuple[float, float],
                             actual: Tuple[float, float]):
        """
        Add a correction sample from user feedback

        Parameters:
        - source: OS coordinate
        - target: predicted DOM coordinate
        - actual: actual DOM coordinate (ground truth)
        """
        error = np.array(actual) - np.array(target)

        self.correction_history.append({
            'source': np.array(source),
            'target': np.array(target),
            'actual': np.array(actual),
            'error': error,
            'error_magnitude': float(np.linalg.norm(error))
        })

        # Limit history size
        if len(self.correction_history) > self.max_history:
            self.correction_history.pop(0)

    def compute_adaptive_correction(self, point: np.ndarray) -> Tuple[float, float]:
        """
        Compute adaptive correction at given point

        Uses inverse distance weighting of nearby corrections

        Parameters:
        - point: (x, y) coordinate

        Returns: (dx, dy) correction
        """
        if not self.correction_history:
            return (0.0, 0.0)

        # Compute distances to all correction samples
        distances = []
        corrections = []

        for sample in self.correction_history:
            source = sample['source']
            dist = np.linalg.norm(point - source)

            if dist < 1e-6:
                # Very close match, use this correction directly
                return tuple(sample['error'])

            distances.append(dist)
            corrections.append(sample['error'])

        distances = np.array(distances)
        corrections = np.array(corrections)

        # Inverse distance weighting (power of 2 for stronger locality)
        weights = 1.0 / (distances ** 2)
        weights = weights / np.sum(weights)

        # Weighted average correction
        adaptive_correction = np.sum(
            corrections * weights[:, np.newaxis],
            axis=0
        )

        return float(adaptive_correction[0]), float(adaptive_correction[1])

    def transform_with_correction(self, x: float, y: float) -> Tuple[float, float]:
        """
        Transform point with adaptive correction

        Parameters:
        - x, y: source coordinates

        Returns: corrected (x', y')
        """
        # Base transformation
        x_t, y_t = self.transform.transform_point(x, y)

        # Adaptive correction
        dx, dy = self.compute_adaptive_correction(np.array([x, y]))

        # Apply correction
        return x_t + dx, y_t + dy

    def update_transform(self):
        """
        Update base transformation using correction history

        Re-calibrates using all correction samples
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


class MultiScaleCalibration:
    """
    Hierarchical calibration for different zoom levels or scales
    """

    def __init__(self):
        self.calibrations = {}  # scale_level -> AffineTransform2D

    def add_calibration(self, scale_level: float, transform: AffineTransform2D):
        """
        Add calibration for specific scale level

        Parameters:
        - scale_level: zoom/scale level identifier
        - transform: transformation for this scale
        """
        self.calibrations[scale_level] = transform

    def calibrate_scale(self, scale_level: float,
                       source_points: np.ndarray,
                       target_points: np.ndarray,
                       use_ransac: bool = False) -> Tuple[AffineTransform2D, float]:
        """
        Calibrate transformation for specific scale level

        Parameters:
        - scale_level: zoom/scale level
        - source_points: Nx2 source coordinates
        - target_points: Nx2 target coordinates
        - use_ransac: use RANSAC for outlier rejection

        Returns: (transform, error)
        """
        if use_ransac and len(source_points) > 10:
            transform, inliers, num_inliers = calibrate_ransac(
                source_points, target_points
            )
            error = 0.0  # RANSAC doesn't return single error value
        else:
            transform, error = calibrate_affine_transform(
                source_points, target_points
            )

        self.add_calibration(scale_level, transform)
        return transform, error

    def get_transform(self, scale_level: float) -> AffineTransform2D:
        """
        Get transformation for given scale level

        Interpolates if exact scale not calibrated

        Parameters:
        - scale_level: desired scale level

        Returns: AffineTransform2D for this scale
        """
        if scale_level in self.calibrations:
            return self.calibrations[scale_level]

        # Find nearest calibrated scales
        scale_levels = sorted(self.calibrations.keys())

        if not scale_levels:
            raise ValueError("No calibrations available")

        if scale_level < scale_levels[0]:
            # Use lowest calibrated scale
            return self.calibrations[scale_levels[0]]

        if scale_level > scale_levels[-1]:
            # Use highest calibrated scale
            return self.calibrations[scale_levels[-1]]

        # Interpolate between two nearest scales
        from affine_transform import interpolate_transforms

        for i in range(len(scale_levels) - 1):
            s1, s2 = scale_levels[i], scale_levels[i+1]

            if s1 <= scale_level <= s2:
                # Interpolation parameter
                t = (scale_level - s1) / (s2 - s1)

                T1 = self.calibrations[s1]
                T2 = self.calibrations[s2]

                return interpolate_transforms(T1, T2, t)

        # Fallback
        return self.calibrations[scale_levels[0]]


# Example usage
if __name__ == "__main__":
    # Generate synthetic calibration data
    np.random.seed(42)

    # True transformation: scale 1.2, rotate 15°, translate (50, 30)
    true_transform = AffineTransform2D.scale_rotate_translate(
        sx=1.2, sy=1.2,
        theta=np.radians(15),
        tx=50, ty=30
    )

    # Source points (OS coordinates)
    source_points = np.random.rand(20, 2) * 500

    # Target points (perfect transformation)
    target_points = true_transform.transform_points(source_points)

    # Add noise to target points
    noise = np.random.randn(20, 2) * 0.5  # 0.5 pixel noise
    target_points_noisy = target_points + noise

    # Add some outliers
    outlier_indices = [5, 12, 17]
    for idx in outlier_indices:
        target_points_noisy[idx] += np.random.randn(2) * 20  # Large error

    print("=== Standard Calibration ===")
    transform_ls, error_ls = calibrate_affine_transform(
        source_points, target_points_noisy
    )
    print(f"Residual error: {error_ls:.4f} pixels")
    print(transform_ls)
    print()

    print("=== RANSAC Calibration ===")
    transform_ransac, inlier_mask, num_inliers = calibrate_ransac(
        source_points, target_points_noisy,
        inlier_threshold=2.0
    )
    print(f"Inliers: {num_inliers}/20")
    print(f"Outliers detected: {outlier_indices}")
    print(f"Actual outliers: {np.where(~inlier_mask)[0].tolist()}")
    print(transform_ransac)
    print()

    print("=== Iterative Refinement ===")
    transform_refined = iterative_refinement(
        transform_ransac, source_points, target_points_noisy
    )
    print(transform_refined)
