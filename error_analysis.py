"""
Error Propagation and Precision Analysis Module
Analyze numerical precision and error propagation through transformations
"""

import numpy as np
from typing import Tuple, Dict, List, Optional
from affine_transform import AffineTransform2D, compute_condition_number


class ErrorPropagation:
    """
    Error propagation through affine transformations

    Uses covariance-based error analysis and Jacobian propagation
    """

    @staticmethod
    def affine_jacobian(transform: AffineTransform2D) -> np.ndarray:
        """
        Extract Jacobian from affine transformation

        For affine transform, Jacobian is the linear part

        Returns: 2x2 Jacobian matrix
        """
        return transform.matrix[:2, :2]

    @staticmethod
    def propagate_covariance(covariance_in: np.ndarray,
                            transform: AffineTransform2D) -> np.ndarray:
        """
        Propagate error covariance through transformation

        Formula: Σ_out = J × Σ_in × J^T

        Parameters:
        - covariance_in: 2x2 input covariance matrix
        - transform: affine transformation

        Returns: 2x2 output covariance matrix
        """
        J = ErrorPropagation.affine_jacobian(transform)
        return J @ covariance_in @ J.T

    @staticmethod
    def propagate_std(std_x: float, std_y: float,
                     transform: AffineTransform2D) -> Tuple[float, float]:
        """
        Propagate standard deviations through transformation

        Parameters:
        - std_x, std_y: input standard deviations
        - transform: affine transformation

        Returns: (std_x_out, std_y_out)
        """
        # Create diagonal covariance matrix
        covariance_in = np.diag([std_x**2, std_y**2])

        # Propagate
        covariance_out = ErrorPropagation.propagate_covariance(
            covariance_in, transform
        )

        # Extract standard deviations
        std_x_out = float(np.sqrt(covariance_out[0, 0]))
        std_y_out = float(np.sqrt(covariance_out[1, 1]))

        return std_x_out, std_y_out

    @staticmethod
    def error_ellipse(covariance: np.ndarray,
                     confidence: float = 0.95) -> Tuple[float, float, float]:
        """
        Compute error ellipse parameters from covariance matrix

        Parameters:
        - covariance: 2x2 covariance matrix
        - confidence: confidence level (default 95%)

        Returns: (semi_major, semi_minor, angle_radians)
        """
        # Eigenvalue decomposition
        eigenvalues, eigenvectors = np.linalg.eig(covariance)

        # Sort by eigenvalue (descending)
        idx = eigenvalues.argsort()[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Chi-square value for confidence level (2 DOF)
        # For 95%: s ≈ 5.991
        # For 68%: s ≈ 2.296
        if confidence == 0.95:
            s = 5.991
        elif confidence == 0.68:
            s = 2.296
        elif confidence == 0.99:
            s = 9.210
        else:
            # General formula (requires scipy)
            try:
                from scipy.stats import chi2
                s = chi2.ppf(confidence, df=2)
            except ImportError:
                s = 5.991  # Default to 95%

        # Semi-axes lengths
        semi_major = float(np.sqrt(s * eigenvalues[0]))
        semi_minor = float(np.sqrt(s * eigenvalues[1]))

        # Angle of major axis
        angle = float(np.arctan2(eigenvectors[1, 0], eigenvectors[0, 0]))

        return semi_major, semi_minor, angle


class TransformationChainError:
    """
    Track error propagation through transformation chain

    Example:
        error_tracker = TransformationChainError(initial_std=0.5)
        error_tracker.add_transformation(transform1)
        error_tracker.add_transformation(transform2)
        std_x, std_y = error_tracker.get_current_std()
    """

    def __init__(self, initial_std_x: float = 0.5, initial_std_y: float = 0.5):
        """
        Initialize error tracker

        Parameters:
        - initial_std_x, initial_std_y: initial measurement uncertainty (pixels)
          Default: 0.5 pixels (sub-pixel uncertainty)
        """
        self.initial_covariance = np.diag([initial_std_x**2, initial_std_y**2])
        self.current_covariance = self.initial_covariance.copy()
        self.transform_count = 0
        self.history = []

    def add_transformation(self, transform: AffineTransform2D,
                          measurement_noise: Optional[np.ndarray] = None):
        """
        Add transformation to chain and propagate error

        Parameters:
        - transform: affine transformation
        - measurement_noise: optional 2x2 covariance for additional noise
        """
        # Record state before transformation
        std_before = self.get_current_std()

        # Propagate existing error
        self.current_covariance = ErrorPropagation.propagate_covariance(
            self.current_covariance, transform
        )

        # Add measurement noise if provided
        if measurement_noise is not None:
            self.current_covariance += measurement_noise

        self.transform_count += 1

        # Record state after transformation
        std_after = self.get_current_std()

        self.history.append({
            'transform_id': self.transform_count,
            'std_before': std_before,
            'std_after': std_after,
            'covariance': self.current_covariance.copy()
        })

    def get_current_std(self) -> Tuple[float, float]:
        """
        Get current standard deviations

        Returns: (std_x, std_y)
        """
        std_x = float(np.sqrt(self.current_covariance[0, 0]))
        std_y = float(np.sqrt(self.current_covariance[1, 1]))
        return std_x, std_y

    def get_total_error_bound(self, confidence: float = 0.95) -> float:
        """
        Get total error bound at given confidence level

        Returns: maximum error radius in pixels
        """
        semi_major, semi_minor, _ = ErrorPropagation.error_ellipse(
            self.current_covariance, confidence
        )
        return semi_major  # Conservative bound

    def get_error_report(self) -> Dict:
        """
        Get comprehensive error report

        Returns: dict with error statistics
        """
        std_x, std_y = self.get_current_std()
        error_bound_95 = self.get_total_error_bound(0.95)
        error_bound_99 = self.get_total_error_bound(0.99)

        return {
            'transform_count': self.transform_count,
            'std_x': std_x,
            'std_y': std_y,
            'total_std': float(np.sqrt(std_x**2 + std_y**2)),
            'error_bound_95': error_bound_95,
            'error_bound_99': error_bound_99,
            'covariance': self.current_covariance,
            'history': self.history
        }


class PrecisionAnalyzer:
    """
    Analyze numerical precision of transformations

    Validates sub-pixel accuracy and numerical stability
    """

    # Target accuracy: 1/256 pixel = ~0.004 pixels
    TARGET_SUBPIXEL_ACCURACY = 1.0 / 256.0

    # Machine epsilon for float64
    EPSILON = np.finfo(np.float64).eps

    # Tolerance for comparisons
    TOLERANCE = 1e-9

    @staticmethod
    def validate_round_trip(transform: AffineTransform2D,
                           test_points: np.ndarray) -> Dict:
        """
        Validate transformation via round-trip accuracy

        Tests: transform -> inverse -> should equal original

        Parameters:
        - transform: transformation to test
        - test_points: Nx2 array of test coordinates

        Returns: dict with precision metrics
        """
        # Forward transform
        transformed = transform.transform_points(test_points)

        # Inverse transform
        inv_transform = transform.inverse()
        recovered = inv_transform.transform_points(transformed)

        # Compute errors
        errors = np.abs(recovered - test_points)
        error_magnitudes = np.linalg.norm(errors, axis=1)

        return {
            'max_error': float(np.max(error_magnitudes)),
            'mean_error': float(np.mean(error_magnitudes)),
            'std_error': float(np.std(error_magnitudes)),
            'median_error': float(np.median(error_magnitudes)),
            'max_error_x': float(np.max(errors[:, 0])),
            'max_error_y': float(np.max(errors[:, 1])),
            'errors': errors,
            'error_magnitudes': error_magnitudes
        }

    @staticmethod
    def analyze_transformation(transform: AffineTransform2D,
                              test_points: Optional[np.ndarray] = None,
                              num_random_tests: int = 1000) -> Dict:
        """
        Comprehensive precision analysis

        Parameters:
        - transform: transformation to analyze
        - test_points: optional specific test points
        - num_random_tests: number of random points to test

        Returns: dict with comprehensive metrics
        """
        # Generate test points if not provided
        if test_points is None:
            # Random points in typical screen coordinates
            np.random.seed(42)
            test_points = np.random.rand(num_random_tests, 2) * 1920

        # Round-trip validation
        round_trip = PrecisionAnalyzer.validate_round_trip(transform, test_points)

        # Condition number
        condition = compute_condition_number(transform)

        # Decomposition
        decomp = transform.decompose()

        # Sensitivity analysis
        sensitivities = []
        for point in test_points[:min(100, len(test_points))]:  # Sample for speed
            sens = PrecisionAnalyzer.sensitivity_at_point(transform, point)
            sensitivities.append(sens)

        avg_sensitivity = float(np.mean(sensitivities))

        # Sub-pixel accuracy check
        is_subpixel_accurate = (
            round_trip['max_error'] < PrecisionAnalyzer.TARGET_SUBPIXEL_ACCURACY
        )

        return {
            'condition_number': condition,
            'numerically_stable': condition < 100,
            'round_trip_max_error': round_trip['max_error'],
            'round_trip_mean_error': round_trip['mean_error'],
            'subpixel_accurate': is_subpixel_accurate,
            'subpixel_target': PrecisionAnalyzer.TARGET_SUBPIXEL_ACCURACY,
            'accuracy_ratio': round_trip['max_error'] / PrecisionAnalyzer.TARGET_SUBPIXEL_ACCURACY,
            'average_sensitivity': avg_sensitivity,
            'decomposition': decomp,
            'round_trip_details': round_trip
        }

    @staticmethod
    def sensitivity_at_point(transform: AffineTransform2D,
                            point: np.ndarray,
                            perturbation: float = 1e-6) -> float:
        """
        Analyze sensitivity of transformation at a point

        Measures how much output changes per unit input change

        Parameters:
        - transform: transformation to analyze
        - point: (x, y) coordinate
        - perturbation: small delta for numerical derivative

        Returns: sensitivity measure (max output change per unit input)
        """
        x, y = point

        # Transform original point
        x0, y0 = transform.transform_point(x, y)

        # Perturb in x direction
        x1, y1 = transform.transform_point(x + perturbation, y)
        sensitivity_x = np.sqrt((x1 - x0)**2 + (y1 - y0)**2) / perturbation

        # Perturb in y direction
        x2, y2 = transform.transform_point(x, y + perturbation)
        sensitivity_y = np.sqrt((x2 - x0)**2 + (y2 - y0)**2) / perturbation

        return float(max(sensitivity_x, sensitivity_y))

    @staticmethod
    def compensated_summation(values: List[float]) -> float:
        """
        Kahan compensated summation algorithm

        Reduces rounding errors in summation

        Parameters:
        - values: list of values to sum

        Returns: compensated sum
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
    def snap_to_subpixel_grid(x: float, y: float,
                             subpixel_divisions: int = 256) -> Tuple[float, float]:
        """
        Snap coordinates to sub-pixel grid for consistency

        Parameters:
        - x, y: coordinates
        - subpixel_divisions: grid divisions per pixel (default 256 = 1/256 px precision)

        Returns: snapped (x, y)
        """
        scale = float(subpixel_divisions)
        x_snapped = float(np.round(x * scale) / scale)
        y_snapped = float(np.round(y * scale) / scale)
        return x_snapped, y_snapped


class SubPixelValidator:
    """
    Comprehensive sub-pixel accuracy validation
    """

    TARGET_ACCURACY = 1.0 / 256.0  # 1/256 pixel

    @staticmethod
    def validate(transform: AffineTransform2D,
                num_tests: int = 1000,
                test_region: Tuple[float, float] = (1920, 1080)) -> Dict:
        """
        Validate transformation achieves sub-pixel accuracy

        Parameters:
        - transform: transformation to test
        - num_tests: number of random test points
        - test_region: (width, height) of test region

        Returns: validation report dict
        """
        # Generate random test points
        np.random.seed(42)
        test_points = np.random.rand(num_tests, 2) * test_region

        # Analyze precision
        analysis = PrecisionAnalyzer.analyze_transformation(
            transform, test_points
        )

        # Detailed report
        report = {
            'target_accuracy': SubPixelValidator.TARGET_ACCURACY,
            'achieved_accuracy': analysis['round_trip_max_error'],
            'mean_error': analysis['round_trip_mean_error'],
            'condition_number': analysis['condition_number'],
            'is_subpixel_accurate': analysis['subpixel_accurate'],
            'accuracy_ratio': analysis['accuracy_ratio'],
            'numerically_stable': analysis['numerically_stable'],
            'num_tests': num_tests,
            'test_region': test_region,
            'pass': (
                analysis['subpixel_accurate'] and
                analysis['numerically_stable']
            )
        }

        return report

    @staticmethod
    def improve_stability(transform: AffineTransform2D) -> AffineTransform2D:
        """
        Attempt to improve numerical stability of transformation

        Techniques:
        1. Decompose matrix
        2. Clean numerical noise
        3. Rebuild transformation

        Parameters:
        - transform: transformation to improve

        Returns: improved transformation
        """
        # Decompose
        decomp = transform.decompose()

        # Extract components
        sx, sy = decomp['scale']
        theta = decomp['rotation']
        tx, ty = decomp['translation']

        # Rebuild with cleaned components
        improved = AffineTransform2D.scale_rotate_translate(
            sx, sy, theta, tx, ty
        )

        return improved


# Example usage and testing
if __name__ == "__main__":
    print("=== Error Propagation Analysis ===\n")

    # Create a transformation chain
    T1 = AffineTransform2D.translation(100, 50)
    T2 = AffineTransform2D.scaling(1.5, 1.5)
    T3 = AffineTransform2D.rotation_degrees(30)

    # Track error through chain
    error_tracker = TransformationChainError(initial_std_x=0.5, initial_std_y=0.5)

    print("Initial uncertainty: 0.5 pixels")

    error_tracker.add_transformation(T1)
    std_x, std_y = error_tracker.get_current_std()
    print(f"After translation: std_x={std_x:.4f}, std_y={std_y:.4f}")

    error_tracker.add_transformation(T2)
    std_x, std_y = error_tracker.get_current_std()
    print(f"After scaling:     std_x={std_x:.4f}, std_y={std_y:.4f}")

    error_tracker.add_transformation(T3)
    std_x, std_y = error_tracker.get_current_std()
    print(f"After rotation:    std_x={std_x:.4f}, std_y={std_y:.4f}")

    error_bound = error_tracker.get_total_error_bound(0.95)
    print(f"\n95% error bound: {error_bound:.4f} pixels\n")

    # Combined transformation
    combined = T3 @ T2 @ T1

    print("=== Sub-Pixel Validation ===\n")
    validation = SubPixelValidator.validate(combined, num_tests=1000)

    print(f"Target accuracy: {validation['target_accuracy']:.6f} pixels")
    print(f"Achieved accuracy: {validation['achieved_accuracy']:.6f} pixels")
    print(f"Mean error: {validation['mean_error']:.6f} pixels")
    print(f"Condition number: {validation['condition_number']:.2f}")
    print(f"Sub-pixel accurate: {validation['is_subpixel_accurate']}")
    print(f"Numerically stable: {validation['numerically_stable']}")
    print(f"Overall PASS: {validation['pass']}\n")

    # Comprehensive analysis
    print("=== Comprehensive Analysis ===\n")
    analysis = PrecisionAnalyzer.analyze_transformation(combined)

    print(f"Condition number: {analysis['condition_number']:.4f}")
    print(f"Round-trip max error: {analysis['round_trip_max_error']:.6f} pixels")
    print(f"Round-trip mean error: {analysis['round_trip_mean_error']:.6f} pixels")
    print(f"Average sensitivity: {analysis['average_sensitivity']:.4f}")
    print(f"Sub-pixel accurate: {analysis['subpixel_accurate']}")
    print(f"\nDecomposition:")
    for key, value in analysis['decomposition'].items():
        print(f"  {key}: {value}")
