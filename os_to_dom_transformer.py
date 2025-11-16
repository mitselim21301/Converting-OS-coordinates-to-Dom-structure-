"""
Complete OS to DOM Coordinate Transformation System
High-precision coordinate transformation with sub-pixel accuracy
"""

import numpy as np
from typing import Tuple, Optional, Dict, List
from affine_transform import AffineTransform2D, compute_condition_number
from calibration import (
    calibrate_affine_transform,
    calibrate_ransac,
    iterative_refinement,
    AdaptiveCorrection,
    MultiScaleCalibration
)
from error_analysis import (
    TransformationChainError,
    PrecisionAnalyzer,
    SubPixelValidator
)


class OSToDOM_Transformer:
    """
    High-precision OS to DOM coordinate transformer

    Features:
    - Sub-pixel accuracy (< 1/256 pixel)
    - Robust calibration with RANSAC
    - Adaptive correction based on feedback
    - Multi-scale support for zoom levels
    - Comprehensive error analysis
    - Round-trip validation

    Example:
        transformer = OSToDOM_Transformer()

        # Calibrate from known points
        transformer.calibrate(os_points, dom_points)

        # Transform coordinates
        x_dom, y_dom = transformer.transform_os_to_dom(x_os, y_os)

        # Validate accuracy
        report = transformer.validate()
    """

    def __init__(self, enable_adaptive: bool = True):
        """
        Initialize transformer

        Parameters:
        - enable_adaptive: enable adaptive correction (default True)
        """
        # Primary transformation (OS → DOM)
        self.forward_transform = AffineTransform2D()

        # Cached inverse (DOM → OS)
        self.inverse_transform = AffineTransform2D()
        self._inverse_dirty = True

        # Error tracking
        self.error_tracker = TransformationChainError(
            initial_std_x=0.5,  # 0.5 pixel initial uncertainty
            initial_std_y=0.5
        )

        # Adaptive correction
        self.enable_adaptive = enable_adaptive
        self.adaptive: Optional[AdaptiveCorrection] = None

        # Multi-scale calibration
        self.multi_scale = MultiScaleCalibration()
        self.current_scale = 1.0

        # Calibration history
        self.calibration_points = {
            'source': [],
            'target': []
        }

        # Statistics
        self.stats = {
            'transforms_performed': 0,
            'calibrations_performed': 0,
            'adaptive_corrections': 0
        }

    def calibrate(self,
                 os_points: np.ndarray,
                 dom_points: np.ndarray,
                 use_ransac: bool = True,
                 refine: bool = True,
                 scale: Optional[float] = None) -> Dict:
        """
        Calibrate transformation from point correspondences

        Parameters:
        - os_points: Nx2 array of OS coordinates
        - dom_points: Nx2 array of DOM coordinates
        - use_ransac: use RANSAC for outlier rejection (default True)
        - refine: use iterative refinement (default True)
        - scale: zoom/scale level (None = default scale)

        Returns: calibration report dict
        """
        n = len(os_points)

        if n < 3:
            raise ValueError("At least 3 point pairs required for calibration")

        # Store calibration points
        self.calibration_points['source'] = os_points.copy()
        self.calibration_points['target'] = dom_points.copy()

        # Initial calibration
        if use_ransac and n >= 10:
            transform, inlier_mask, num_inliers = calibrate_ransac(
                os_points, dom_points,
                inlier_threshold=2.0,
                max_iterations=1000
            )
            inlier_ratio = num_inliers / n
            outliers_detected = np.where(~inlier_mask)[0].tolist()
        else:
            transform, residual = calibrate_affine_transform(os_points, dom_points)
            inlier_ratio = 1.0
            outliers_detected = []

        # Iterative refinement
        if refine:
            transform = iterative_refinement(
                transform, os_points, dom_points,
                max_iterations=10
            )

        # Set transformation
        if scale is None:
            self.forward_transform = transform
            self._inverse_dirty = True
        else:
            self.multi_scale.add_calibration(scale, transform)
            if scale == self.current_scale:
                self.forward_transform = transform
                self._inverse_dirty = True

        # Initialize adaptive correction
        if self.enable_adaptive:
            self.adaptive = AdaptiveCorrection(transform, max_history=100)

        # Validate sub-pixel accuracy
        validation = SubPixelValidator.validate(transform, num_tests=500)

        # Precision analysis
        analysis = PrecisionAnalyzer.analyze_transformation(
            transform,
            test_points=os_points
        )

        # Update statistics
        self.stats['calibrations_performed'] += 1

        # Calibration report
        report = {
            'success': True,
            'num_points': n,
            'use_ransac': use_ransac,
            'inlier_ratio': inlier_ratio,
            'outliers_detected': outliers_detected,
            'validation': validation,
            'analysis': analysis,
            'transform': transform,
            'decomposition': transform.decompose()
        }

        return report

    def set_scale(self, scale: float):
        """
        Set current zoom/scale level

        Automatically selects appropriate transformation
        """
        self.current_scale = scale

        try:
            self.forward_transform = self.multi_scale.get_transform(scale)
            self._inverse_dirty = True
        except ValueError:
            # No calibration available for this scale
            pass

    def transform_os_to_dom(self,
                           x: float,
                           y: float,
                           use_adaptive: bool = None) -> Tuple[float, float]:
        """
        Transform OS coordinates to DOM coordinates

        Parameters:
        - x, y: OS coordinates
        - use_adaptive: apply adaptive correction (default: use instance setting)

        Returns: (x_dom, y_dom) with sub-pixel precision
        """
        if use_adaptive is None:
            use_adaptive = self.enable_adaptive

        if use_adaptive and self.adaptive is not None:
            x_dom, y_dom = self.adaptive.transform_with_correction(x, y)
        else:
            x_dom, y_dom = self.forward_transform.transform_point(x, y)

        self.stats['transforms_performed'] += 1
        return x_dom, y_dom

    def transform_dom_to_os(self, x: float, y: float) -> Tuple[float, float]:
        """
        Transform DOM coordinates back to OS coordinates

        For validation and reverse mapping
        """
        # Update inverse if needed
        if self._inverse_dirty:
            self.inverse_transform = self.forward_transform.inverse()
            self._inverse_dirty = False

        return self.inverse_transform.transform_point(x, y)

    def transform_batch_os_to_dom(self, points: np.ndarray) -> np.ndarray:
        """
        Batch transform OS to DOM (efficient for many points)

        Parameters:
        - points: Nx2 array of OS coordinates

        Returns: Nx2 array of DOM coordinates
        """
        return self.forward_transform.transform_points(points)

    def transform_batch_dom_to_os(self, points: np.ndarray) -> np.ndarray:
        """
        Batch transform DOM to OS (efficient for many points)
        """
        if self._inverse_dirty:
            self.inverse_transform = self.forward_transform.inverse()
            self._inverse_dirty = False

        return self.inverse_transform.transform_points(points)

    def add_correction_feedback(self,
                               os_coord: Tuple[float, float],
                               predicted_dom: Tuple[float, float],
                               actual_dom: Tuple[float, float]):
        """
        Add correction feedback from user interaction

        Parameters:
        - os_coord: original OS coordinate
        - predicted_dom: predicted DOM coordinate
        - actual_dom: actual clicked DOM coordinate
        """
        if self.adaptive is not None:
            self.adaptive.add_correction_sample(
                os_coord, predicted_dom, actual_dom
            )
            self.stats['adaptive_corrections'] += 1

    def update_from_feedback(self):
        """
        Update transformation based on accumulated feedback
        """
        if self.adaptive is not None:
            self.adaptive.update_transform()
            self.forward_transform = self.adaptive.transform
            self._inverse_dirty = True

    def validate(self, test_points: Optional[np.ndarray] = None) -> Dict:
        """
        Comprehensive validation of transformation accuracy

        Parameters:
        - test_points: optional specific test points (uses calibration points if None)

        Returns: validation report dict
        """
        if test_points is None:
            if len(self.calibration_points['source']) > 0:
                test_points = self.calibration_points['source']
            else:
                # Generate random test points
                np.random.seed(42)
                test_points = np.random.rand(100, 2) * 1920

        # Round-trip validation
        round_trip_errors = []
        for x, y in test_points:
            x_dom, y_dom = self.transform_os_to_dom(x, y)
            x_recovered, y_recovered = self.transform_dom_to_os(x_dom, y_dom)
            error = np.sqrt((x - x_recovered)**2 + (y - y_recovered)**2)
            round_trip_errors.append(error)

        round_trip_errors = np.array(round_trip_errors)

        # Sub-pixel validation
        subpixel_validation = SubPixelValidator.validate(
            self.forward_transform,
            num_tests=500
        )

        # Precision analysis
        precision = PrecisionAnalyzer.analyze_transformation(
            self.forward_transform,
            test_points=test_points
        )

        # Error propagation report
        error_report = self.error_tracker.get_error_report()

        return {
            'round_trip': {
                'max_error': float(np.max(round_trip_errors)),
                'mean_error': float(np.mean(round_trip_errors)),
                'median_error': float(np.median(round_trip_errors)),
                'std_error': float(np.std(round_trip_errors)),
                'subpixel_accurate': np.max(round_trip_errors) < 1.0/256.0
            },
            'subpixel_validation': subpixel_validation,
            'precision': precision,
            'error_propagation': error_report,
            'statistics': self.stats.copy()
        }

    def get_info(self) -> Dict:
        """
        Get detailed information about current transformation
        """
        decomp = self.forward_transform.decompose()
        condition = compute_condition_number(self.forward_transform)

        return {
            'matrix': self.forward_transform.matrix,
            'decomposition': decomp,
            'condition_number': condition,
            'numerically_stable': condition < 100,
            'current_scale': self.current_scale,
            'adaptive_enabled': self.enable_adaptive,
            'adaptive_samples': len(self.adaptive.correction_history) if self.adaptive else 0,
            'statistics': self.stats.copy()
        }

    def save_calibration(self, filename: str):
        """
        Save calibration to file

        Parameters:
        - filename: path to save file (numpy .npz format)
        """
        np.savez(
            filename,
            matrix=self.forward_transform.matrix,
            calibration_source=self.calibration_points['source'],
            calibration_target=self.calibration_points['target'],
            current_scale=self.current_scale,
            statistics=self.stats
        )

    def load_calibration(self, filename: str):
        """
        Load calibration from file

        Parameters:
        - filename: path to calibration file
        """
        data = np.load(filename, allow_pickle=True)

        self.forward_transform = AffineTransform2D(data['matrix'])
        self._inverse_dirty = True

        if 'calibration_source' in data:
            self.calibration_points['source'] = data['calibration_source']
        if 'calibration_target' in data:
            self.calibration_points['target'] = data['calibration_target']
        if 'current_scale' in data:
            self.current_scale = float(data['current_scale'])
        if 'statistics' in data:
            self.stats = data['statistics'].item()

        # Reinitialize adaptive correction
        if self.enable_adaptive:
            self.adaptive = AdaptiveCorrection(self.forward_transform)


def example_usage():
    """
    Complete example of OS to DOM transformation
    """
    print("=" * 70)
    print("OS to DOM Coordinate Transformation - Example Usage")
    print("=" * 70)
    print()

    # Create transformer
    transformer = OSToDOM_Transformer(enable_adaptive=True)

    # Example calibration data
    # In practice, these would come from actual measurements
    # (e.g., clicking on known DOM elements and recording OS coordinates)

    print("Step 1: Generating synthetic calibration data...")
    print()

    # Simulate a real OS→DOM transformation
    # Typical scenario: 1.2x scaling, 10° rotation, offset of (150, 100)
    true_transform = AffineTransform2D.scale_rotate_translate(
        sx=1.2, sy=1.2,
        theta=np.radians(10),
        tx=150, ty=100
    )

    # Generate calibration points
    np.random.seed(42)
    os_points = np.array([
        [100, 100],   # Top-left region
        [800, 100],   # Top-right region
        [100, 500],   # Bottom-left region
        [800, 500],   # Bottom-right region
        [450, 300],   # Center
        [200, 200],
        [600, 200],
        [200, 400],
        [600, 400],
        [450, 150],
    ], dtype=np.float64)

    # Perfect transformation
    dom_points = true_transform.transform_points(os_points)

    # Add realistic noise (sub-pixel measurement uncertainty)
    noise = np.random.randn(len(dom_points), 2) * 0.3
    dom_points += noise

    # Add a couple of outliers (e.g., user misclicks)
    dom_points[5] += np.array([15, -12])  # Outlier
    dom_points[8] += np.array([-18, 20])  # Outlier

    print(f"Generated {len(os_points)} calibration point pairs")
    print(f"Added measurement noise (0.3 pixel std) and 2 outliers")
    print()

    # Step 2: Calibrate
    print("Step 2: Calibrating transformation...")
    print()

    calibration_report = transformer.calibrate(
        os_points, dom_points,
        use_ransac=True,   # Use RANSAC to handle outliers
        refine=True        # Iterative refinement for better accuracy
    )

    print(f"Calibration successful!")
    print(f"  Points used: {calibration_report['num_points']}")
    print(f"  Inlier ratio: {calibration_report['inlier_ratio']:.1%}")
    print(f"  Outliers detected: {calibration_report['outliers_detected']}")
    print(f"  Sub-pixel accurate: {calibration_report['validation']['is_subpixel_accurate']}")
    print(f"  Max error: {calibration_report['validation']['achieved_accuracy']:.6f} pixels")
    print(f"  Condition number: {calibration_report['analysis']['condition_number']:.2f}")
    print()

    # Step 3: Transform coordinates
    print("Step 3: Transforming coordinates...")
    print()

    test_os_coords = [
        (300, 250),
        (500, 350),
        (150, 150)
    ]

    for x_os, y_os in test_os_coords:
        x_dom, y_dom = transformer.transform_os_to_dom(x_os, y_os)
        print(f"  OS ({x_os:3.0f}, {y_os:3.0f}) → DOM ({x_dom:7.3f}, {y_dom:7.3f})")

    print()

    # Step 4: Validate with round-trip
    print("Step 4: Validating with round-trip transformation...")
    print()

    validation = transformer.validate()

    print(f"Round-trip validation:")
    print(f"  Max error: {validation['round_trip']['max_error']:.6f} pixels")
    print(f"  Mean error: {validation['round_trip']['mean_error']:.6f} pixels")
    print(f"  Median error: {validation['round_trip']['median_error']:.6f} pixels")
    print(f"  Sub-pixel accurate: {validation['round_trip']['subpixel_accurate']}")
    print()

    # Step 5: Adaptive correction simulation
    print("Step 5: Simulating adaptive correction...")
    print()

    # Simulate user feedback: predicted vs actual DOM coordinates
    x_os, y_os = 400, 300
    x_predicted, y_predicted = transformer.transform_os_to_dom(x_os, y_os)

    # Simulate actual click (with small error)
    x_actual = x_predicted + 0.5
    y_actual = y_predicted - 0.3

    transformer.add_correction_feedback(
        (x_os, y_os),
        (x_predicted, y_predicted),
        (x_actual, y_actual)
    )

    print(f"Added correction feedback:")
    print(f"  Predicted: ({x_predicted:.3f}, {y_predicted:.3f})")
    print(f"  Actual:    ({x_actual:.3f}, {y_actual:.3f})")
    print(f"  Error:     ({x_actual-x_predicted:.3f}, {y_actual-y_predicted:.3f})")
    print()

    # Step 6: Get transformation info
    print("Step 6: Transformation details...")
    print()

    info = transformer.get_info()
    decomp = info['decomposition']

    print(f"Decomposition:")
    print(f"  Translation: ({decomp['translation'][0]:.2f}, {decomp['translation'][1]:.2f})")
    print(f"  Rotation: {decomp['rotation_degrees']:.2f}°")
    print(f"  Scale: ({decomp['scale'][0]:.4f}, {decomp['scale'][1]:.4f})")
    print(f"  Shear: {decomp['shear']:.6f}")
    print()
    print(f"Statistics:")
    print(f"  Calibrations: {info['statistics']['calibrations_performed']}")
    print(f"  Transforms: {info['statistics']['transforms_performed']}")
    print(f"  Adaptive corrections: {info['statistics']['adaptive_corrections']}")
    print()

    # Step 7: Save/Load calibration
    print("Step 7: Saving calibration...")
    print()

    calibration_file = "/tmp/os_to_dom_calibration.npz"
    transformer.save_calibration(calibration_file)
    print(f"Calibration saved to: {calibration_file}")
    print()

    # Load it back
    transformer2 = OSToDOM_Transformer()
    transformer2.load_calibration(calibration_file)
    print(f"Calibration loaded successfully")
    print()

    print("=" * 70)
    print("Example completed successfully!")
    print("=" * 70)

    return transformer


if __name__ == "__main__":
    transformer = example_usage()
