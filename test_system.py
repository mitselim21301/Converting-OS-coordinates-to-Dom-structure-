"""
Comprehensive Test Suite for OS to DOM Transformation System
"""

import numpy as np
import sys

# Import modules
from affine_transform import (
    AffineTransform2D,
    TransformChain,
    compute_condition_number,
    interpolate_transforms
)
from calibration import (
    calibrate_affine_transform,
    calibrate_ransac,
    iterative_refinement,
    AdaptiveCorrection
)
from error_analysis import (
    ErrorPropagation,
    TransformationChainError,
    PrecisionAnalyzer,
    SubPixelValidator
)
from os_to_dom_transformer import OSToDOM_Transformer


def test_affine_transforms():
    """Test basic affine transformation operations"""
    print("=" * 70)
    print("TEST 1: Affine Transformations")
    print("=" * 70)

    # Test translation
    T = AffineTransform2D.translation(10, 20)
    x, y = T.transform_point(5, 3)
    assert abs(x - 15) < 1e-10 and abs(y - 23) < 1e-10
    print("✓ Translation: (5, 3) + (10, 20) = ({:.1f}, {:.1f})".format(x, y))

    # Test scaling
    S = AffineTransform2D.scaling(2.0, 3.0)
    x, y = S.transform_point(4, 5)
    assert abs(x - 8) < 1e-10 and abs(y - 15) < 1e-10
    print("✓ Scaling: (4, 5) × (2, 3) = ({:.1f}, {:.1f})".format(x, y))

    # Test rotation
    R = AffineTransform2D.rotation(np.pi / 2)  # 90 degrees
    x, y = R.transform_point(1, 0)
    assert abs(x - 0) < 1e-10 and abs(y - 1) < 1e-10
    print("✓ Rotation: (1, 0) rotated 90° = ({:.1f}, {:.1f})".format(x, y))

    # Test composition
    combined = T @ R @ S
    x, y = combined.transform_point(1, 1)
    print("✓ Composition: T∘R∘S transforms (1, 1) to ({:.2f}, {:.2f})".format(x, y))

    # Test inverse
    inv = combined.inverse()
    x_r, y_r = inv.transform_point(x, y)
    error = np.sqrt((1 - x_r)**2 + (1 - y_r)**2)
    assert error < 1e-9
    print("✓ Inverse: Round-trip error = {:.2e}".format(error))

    # Test decomposition
    decomp = combined.decompose()
    print("✓ Decomposition:")
    print("  - Translation: ({:.2f}, {:.2f})".format(*decomp['translation']))
    print("  - Rotation: {:.2f}°".format(decomp['rotation_degrees']))
    print("  - Scale: ({:.2f}, {:.2f})".format(*decomp['scale']))

    print()
    return True


def test_calibration():
    """Test calibration algorithms"""
    print("=" * 70)
    print("TEST 2: Calibration Algorithms")
    print("=" * 70)

    # Create synthetic calibration data
    np.random.seed(42)

    # True transformation
    true_transform = AffineTransform2D.scale_rotate_translate(
        sx=1.5, sy=1.5,
        theta=np.radians(20),
        tx=100, ty=50
    )

    # Source points
    source_points = np.random.rand(10, 2) * 500

    # Perfect target points
    target_points = true_transform.transform_points(source_points)

    # Add noise
    noise = np.random.randn(10, 2) * 0.5
    target_points_noisy = target_points + noise

    # Test least squares
    transform_ls, error = calibrate_affine_transform(source_points, target_points_noisy)
    print("✓ Least Squares Calibration:")
    print("  - Residual error: {:.4f} pixels".format(error))

    # Validate
    test_point = np.array([[250, 250]])
    true_result = true_transform.transform_points(test_point)
    ls_result = transform_ls.transform_points(test_point)
    calibration_error = np.linalg.norm(true_result - ls_result)
    print("  - Accuracy vs ground truth: {:.4f} pixels".format(calibration_error))

    # Add outliers
    target_outliers = target_points_noisy.copy()
    target_outliers[2] += np.array([30, -25])
    target_outliers[7] += np.array([-20, 35])

    # Test RANSAC
    transform_ransac, inlier_mask, num_inliers = calibrate_ransac(
        source_points, target_outliers,
        max_iterations=500,
        inlier_threshold=2.0
    )
    print("✓ RANSAC Calibration:")
    print("  - Inliers: {}/10".format(num_inliers))
    print("  - Outliers detected: {}".format(np.where(~inlier_mask)[0].tolist()))

    # Test iterative refinement
    transform_refined = iterative_refinement(
        transform_ransac, source_points, target_points_noisy,
        max_iterations=5
    )
    print("✓ Iterative Refinement: Complete")

    print()
    return True


def test_error_propagation():
    """Test error propagation analysis"""
    print("=" * 70)
    print("TEST 3: Error Propagation")
    print("=" * 70)

    # Create transformation chain
    T1 = AffineTransform2D.translation(100, 50)
    T2 = AffineTransform2D.scaling(2.0, 2.0)
    T3 = AffineTransform2D.rotation_degrees(30)

    # Track error
    error_tracker = TransformationChainError(initial_std_x=0.5, initial_std_y=0.5)

    print("Initial uncertainty: 0.5 pixels")

    error_tracker.add_transformation(T1)
    std_x, std_y = error_tracker.get_current_std()
    print("✓ After translation: std = ({:.4f}, {:.4f}) pixels".format(std_x, std_y))

    error_tracker.add_transformation(T2)
    std_x, std_y = error_tracker.get_current_std()
    print("✓ After scaling (2x): std = ({:.4f}, {:.4f}) pixels".format(std_x, std_y))

    error_tracker.add_transformation(T3)
    std_x, std_y = error_tracker.get_current_std()
    print("✓ After rotation (30°): std = ({:.4f}, {:.4f}) pixels".format(std_x, std_y))

    error_bound = error_tracker.get_total_error_bound(0.95)
    print("✓ 95% error bound: {:.4f} pixels".format(error_bound))

    print()
    return True


def test_precision_validation():
    """Test numerical precision validation"""
    print("=" * 70)
    print("TEST 4: Precision Validation")
    print("=" * 70)

    # Create transformation
    transform = AffineTransform2D.scale_rotate_translate(
        sx=1.2, sy=1.2,
        theta=np.radians(15),
        tx=100, ty=50
    )

    # Sub-pixel validation
    validation = SubPixelValidator.validate(transform, num_tests=1000)

    print("✓ Sub-Pixel Validation (1000 test points):")
    print("  - Target accuracy: {:.6f} pixels (1/256)".format(validation['target_accuracy']))
    print("  - Achieved accuracy: {:.6f} pixels".format(validation['achieved_accuracy']))
    print("  - Mean error: {:.6f} pixels".format(validation['mean_error']))
    print("  - Condition number: {:.2f}".format(validation['condition_number']))
    print("  - Sub-pixel accurate: {}".format(validation['is_subpixel_accurate']))
    print("  - Numerically stable: {}".format(validation['numerically_stable']))
    print("  - Overall PASS: {}".format(validation['pass']))

    assert validation['pass'], "Sub-pixel validation failed!"

    # Precision analysis
    analysis = PrecisionAnalyzer.analyze_transformation(transform, num_random_tests=500)
    print("✓ Precision Analysis:")
    print("  - Round-trip max error: {:.6f} pixels".format(analysis['round_trip_max_error']))
    print("  - Accuracy ratio: {:.2f}× target".format(analysis['accuracy_ratio']))

    print()
    return True


def test_adaptive_correction():
    """Test adaptive correction"""
    print("=" * 70)
    print("TEST 5: Adaptive Correction")
    print("=" * 70)

    # Base transformation
    base_transform = AffineTransform2D.scale_rotate_translate(
        sx=1.5, sy=1.5,
        theta=np.radians(10),
        tx=150, ty=100
    )

    # Create adaptive corrector
    corrector = AdaptiveCorrection(base_transform, max_history=50)

    print("✓ Adaptive Corrector initialized")

    # Simulate corrections
    test_points = [
        (100, 100),
        (200, 200),
        (300, 300)
    ]

    for i, (x, y) in enumerate(test_points):
        # Base prediction
        x_pred, y_pred = base_transform.transform_point(x, y)

        # Simulate actual (with small error)
        x_actual = x_pred + np.random.randn() * 0.5
        y_actual = y_pred + np.random.randn() * 0.5

        # Add correction
        corrector.add_correction_sample(
            (x, y),
            (x_pred, y_pred),
            (x_actual, y_actual)
        )

    print("✓ Added {} correction samples".format(len(test_points)))

    # Test adaptive transformation
    x_test, y_test = 250, 250
    x_base, y_base = base_transform.transform_point(x_test, y_test)
    x_corrected, y_corrected = corrector.transform_with_correction(x_test, y_test)

    correction = np.sqrt((x_corrected - x_base)**2 + (y_corrected - y_base)**2)
    print("✓ Adaptive correction applied: {:.4f} pixels".format(correction))

    print()
    return True


def test_complete_system():
    """Test the complete OSToDOM_Transformer system"""
    print("=" * 70)
    print("TEST 6: Complete OS to DOM Transformer System")
    print("=" * 70)

    # Create transformer
    transformer = OSToDOM_Transformer(enable_adaptive=True)

    # Generate calibration data
    np.random.seed(42)

    # Simulate real transformation
    true_transform = AffineTransform2D.scale_rotate_translate(
        sx=1.3, sy=1.3,
        theta=np.radians(12),
        tx=120, ty=80
    )

    os_points = np.array([
        [100, 100],
        [800, 100],
        [100, 500],
        [800, 500],
        [450, 300],
        [200, 200],
        [600, 300],
        [300, 400]
    ], dtype=np.float64)

    dom_points = true_transform.transform_points(os_points)
    dom_points += np.random.randn(*dom_points.shape) * 0.3  # Add noise

    # Calibrate
    print("Calibrating transformer...")
    report = transformer.calibrate(os_points, dom_points, use_ransac=True, refine=True)

    print("✓ Calibration complete:")
    print("  - Points used: {}".format(report['num_points']))
    print("  - Inlier ratio: {:.1%}".format(report['inlier_ratio']))
    print("  - Sub-pixel accurate: {}".format(report['validation']['is_subpixel_accurate']))
    print("  - Achieved accuracy: {:.6f} pixels".format(report['validation']['achieved_accuracy']))

    # Transform coordinates
    test_coords = [(300, 250), (500, 350), (150, 150)]
    print("✓ Transforming test coordinates:")

    for x_os, y_os in test_coords:
        x_dom, y_dom = transformer.transform_os_to_dom(x_os, y_os)
        print("  - OS ({:3.0f}, {:3.0f}) → DOM ({:7.3f}, {:7.3f})".format(
            x_os, y_os, x_dom, y_dom))

    # Validate
    validation = transformer.validate()
    print("✓ Validation results:")
    print("  - Max round-trip error: {:.6f} pixels".format(validation['round_trip']['max_error']))
    print("  - Mean round-trip error: {:.6f} pixels".format(validation['round_trip']['mean_error']))
    print("  - Sub-pixel accurate: {}".format(validation['round_trip']['subpixel_accurate']))

    # Get info
    info = transformer.get_info()
    print("✓ Transformer info:")
    print("  - Condition number: {:.2f}".format(info['condition_number']))
    print("  - Numerically stable: {}".format(info['numerically_stable']))
    decomp = info['decomposition']
    print("  - Translation: ({:.2f}, {:.2f})".format(*decomp['translation']))
    print("  - Rotation: {:.2f}°".format(decomp['rotation_degrees']))
    print("  - Scale: ({:.4f}, {:.4f})".format(*decomp['scale']))

    print()
    return True


def run_all_tests():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "OS TO DOM TRANSFORMATION TEST SUITE" + " " * 17 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    tests = [
        ("Affine Transformations", test_affine_transforms),
        ("Calibration Algorithms", test_calibration),
        ("Error Propagation", test_error_propagation),
        ("Precision Validation", test_precision_validation),
        ("Adaptive Correction", test_adaptive_correction),
        ("Complete System", test_complete_system)
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ TEST FAILED: {name}")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            print()

    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print()

    if failed == 0:
        print("✓ ALL TESTS PASSED!")
    else:
        print("✗ SOME TESTS FAILED")
        sys.exit(1)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
