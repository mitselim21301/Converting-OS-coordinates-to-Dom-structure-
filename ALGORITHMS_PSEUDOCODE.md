# Algorithm Pseudocode
## Language-Agnostic Implementation Guide

This document provides detailed pseudocode for all key algorithms in the OS to DOM coordinate transformation system. Implementations can be created in any programming language following these specifications.

---

## Table of Contents

1. [Core Data Structures](#1-core-data-structures)
2. [Affine Transformation](#2-affine-transformation)
3. [Calibration Algorithms](#3-calibration-algorithms)
4. [Error Propagation](#4-error-propagation)
5. [Precision Validation](#5-precision-validation)
6. [Adaptive Correction](#6-adaptive-correction)

---

## 1. Core Data Structures

### 1.1 Point2D

```
STRUCTURE Point2D:
    float64 x
    float64 y
```

### 1.2 Matrix3x3

```
STRUCTURE Matrix3x3:
    float64[3][3] data

    METHODS:
        - multiply(Matrix3x3 other) -> Matrix3x3
        - transform_point(Point2D p) -> Point2D
        - determinant() -> float64
        - inverse() -> Matrix3x3
```

### 1.3 AffineTransform

```
STRUCTURE AffineTransform:
    Matrix3x3 matrix  // 3x3 transformation matrix

    METHODS:
        - transform(Point2D p) -> Point2D
        - inverse() -> AffineTransform
        - compose(AffineTransform other) -> AffineTransform
        - decompose() -> (translation, rotation, scale, shear)
```

---

## 2. Affine Transformation

### 2.1 Create Transformation Matrix

#### Translation Matrix

```
FUNCTION create_translation_matrix(tx: float64, ty: float64) -> Matrix3x3:
    RETURN Matrix3x3([
        [1.0, 0.0, tx],
        [0.0, 1.0, ty],
        [0.0, 0.0, 1.0]
    ])
```

#### Scaling Matrix

```
FUNCTION create_scaling_matrix(sx: float64, sy: float64) -> Matrix3x3:
    RETURN Matrix3x3([
        [sx,  0.0, 0.0],
        [0.0, sy,  0.0],
        [0.0, 0.0, 1.0]
    ])
```

#### Rotation Matrix

```
FUNCTION create_rotation_matrix(theta: float64) -> Matrix3x3:
    // theta in radians, counter-clockwise

    cos_theta = cos(theta)
    sin_theta = sin(theta)

    RETURN Matrix3x3([
        [cos_theta, -sin_theta, 0.0],
        [sin_theta,  cos_theta, 0.0],
        [0.0,        0.0,       1.0]
    ])
```

#### Combined SRT Transformation

```
FUNCTION create_srt_transform(sx, sy, theta, tx, ty) -> Matrix3x3:
    // Scale-Rotate-Translate composition
    // Order: Scale -> Rotate -> Translate

    S = create_scaling_matrix(sx, sy)
    R = create_rotation_matrix(theta)
    T = create_translation_matrix(tx, ty)

    // Matrix multiplication: T × R × S
    RETURN matrix_multiply(T, matrix_multiply(R, S))
```

### 2.2 Transform Point

```
FUNCTION transform_point(matrix: Matrix3x3, point: Point2D) -> Point2D:
    // Convert to homogeneous coordinates
    homogeneous = [point.x, point.y, 1.0]

    // Matrix-vector multiplication
    result = matrix_multiply(matrix, homogeneous)

    // Convert back to Cartesian (ignore w component)
    RETURN Point2D(result[0], result[1])
```

### 2.3 Batch Transform

```
FUNCTION transform_points(matrix: Matrix3x3, points: Array<Point2D>) -> Array<Point2D>:
    n = length(points)
    results = Array<Point2D>(n)

    FOR i = 0 TO n-1:
        results[i] = transform_point(matrix, points[i])

    RETURN results
```

### 2.4 Matrix Inverse

```
FUNCTION inverse_affine_matrix(M: Matrix3x3) -> Matrix3x3:
    // Extract components
    a = M[0][0]
    b = M[0][1]
    tx = M[0][2]
    c = M[1][0]
    d = M[1][1]
    ty = M[1][2]

    // Compute determinant
    det = a * d - b * c

    // Check for singularity
    IF abs(det) < EPSILON:
        RAISE Error("Matrix is singular, cannot invert")

    // Compute inverse using analytical formula
    inv = Matrix3x3([
        [ d/det, -b/det, (b*ty - d*tx)/det],
        [-c/det,  a/det, (c*tx - a*ty)/det],
        [ 0.0,    0.0,    1.0              ]
    ])

    RETURN inv

CONSTANT EPSILON = 1e-10
```

### 2.5 Matrix Decomposition

```
FUNCTION decompose_affine(M: Matrix3x3) -> (translation, rotation, scale, shear):
    // Extract components
    a = M[0][0]
    b = M[0][1]
    tx = M[0][2]
    c = M[1][0]
    d = M[1][1]
    ty = M[1][2]

    // Translation
    translation = (tx, ty)

    // Determinant
    det = a * d - b * c

    // Rotation angle
    rotation = atan2(c, a)  // in radians

    // Scale factors
    sx = sqrt(a² + c²)
    sy = det / sx  IF sx ≠ 0 ELSE 0

    // Shear
    shear = (a*b + c*d) / (a² + c²)  IF (a² + c²) ≠ 0 ELSE 0

    RETURN (translation, rotation, (sx, sy), shear)
```

---

## 3. Calibration Algorithms

### 3.1 Least Squares Calibration

```
FUNCTION calibrate_least_squares(
    source_points: Array<Point2D>,
    target_points: Array<Point2D>
) -> (Matrix3x3, float64):

    n = length(source_points)

    IF n < 3:
        RAISE Error("At least 3 point pairs required")

    // Check for collinearity
    IF n == 3 AND are_collinear(source_points):
        RAISE Error("Points are collinear")

    // Build linear system: A × x = b
    // Variables: [a, b, tx, c, d, ty]
    A = Matrix(2*n, 6)
    b = Vector(2*n)

    FOR i = 0 TO n-1:
        xi = source_points[i].x
        yi = source_points[i].y
        xi_prime = target_points[i].x
        yi_prime = target_points[i].y

        // Row for x' equation: x' = a*x + b*y + tx
        A[2*i] = [xi, yi, 1.0, 0.0, 0.0, 0.0]
        b[2*i] = xi_prime

        // Row for y' equation: y' = c*x + d*y + ty
        A[2*i + 1] = [0.0, 0.0, 0.0, xi, yi, 1.0]
        b[2*i + 1] = yi_prime

    // Solve using least squares: x = (A^T A)^-1 A^T b
    params = solve_least_squares(A, b)

    // Extract parameters
    a = params[0]
    b_param = params[1]
    tx = params[2]
    c = params[3]
    d = params[4]
    ty = params[5]

    // Build transformation matrix
    matrix = Matrix3x3([
        [a, b_param, tx],
        [c, d,       ty],
        [0, 0,        1]
    ])

    // Compute residual error
    residual = compute_residual_error(A, params, b)

    RETURN (matrix, residual)


FUNCTION solve_least_squares(A: Matrix, b: Vector) -> Vector:
    // Solve: (A^T A) x = A^T b
    AtA = transpose(A) × A
    Atb = transpose(A) × b
    x = solve_linear_system(AtA, Atb)
    RETURN x


FUNCTION are_collinear(points: Array<Point2D>) -> bool:
    IF length(points) < 3:
        RETURN true

    p1 = points[0]
    p2 = points[1]
    p3 = points[2]

    // Compute cross product
    v1_x = p2.x - p1.x
    v1_y = p2.y - p1.y
    v2_x = p3.x - p1.x
    v2_y = p3.y - p1.y

    cross = v1_x * v2_y - v1_y * v2_x

    RETURN abs(cross) < EPSILON

CONSTANT EPSILON = 1e-9
```

### 3.2 RANSAC Calibration

```
FUNCTION calibrate_ransac(
    source_points: Array<Point2D>,
    target_points: Array<Point2D>,
    max_iterations: int,
    inlier_threshold: float64,
    min_inliers: int
) -> (Matrix3x3, Array<bool>, int):

    n = length(source_points)

    best_matrix = NULL
    best_inliers = 0
    best_inlier_mask = NULL

    FOR iteration = 0 TO max_iterations-1:
        // Step 1: Randomly sample 3 point pairs
        sample_indices = random_sample(n, 3)
        sample_source = select_points(source_points, sample_indices)
        sample_target = select_points(target_points, sample_indices)

        // Check for collinearity
        IF are_collinear(sample_source):
            CONTINUE

        // Step 2: Fit transformation to sample
        TRY:
            matrix, _ = calibrate_least_squares(sample_source, sample_target)
        CATCH:
            CONTINUE

        // Step 3: Test on all points
        transformed = transform_points(matrix, source_points)
        errors = compute_distances(transformed, target_points)

        // Step 4: Count inliers
        inlier_mask = Array<bool>(n)
        num_inliers = 0

        FOR i = 0 TO n-1:
            IF errors[i] < inlier_threshold:
                inlier_mask[i] = true
                num_inliers += 1
            ELSE:
                inlier_mask[i] = false

        // Step 5: Update best model
        IF num_inliers > best_inliers:
            best_inliers = num_inliers
            best_matrix = matrix
            best_inlier_mask = inlier_mask

        // Early exit
        IF best_inliers >= min_inliers:
            BREAK

    // Step 6: Refit using all inliers
    IF best_matrix == NULL:
        RAISE Error("RANSAC failed")

    inlier_source = select_points(source_points, best_inlier_mask)
    inlier_target = select_points(target_points, best_inlier_mask)

    final_matrix, _ = calibrate_least_squares(inlier_source, inlier_target)

    RETURN (final_matrix, best_inlier_mask, best_inliers)


FUNCTION compute_distances(points1: Array<Point2D>, points2: Array<Point2D>) -> Array<float64>:
    n = length(points1)
    distances = Array<float64>(n)

    FOR i = 0 TO n-1:
        dx = points1[i].x - points2[i].x
        dy = points1[i].y - points2[i].y
        distances[i] = sqrt(dx² + dy²)

    RETURN distances
```

### 3.3 Iterative Refinement

```
FUNCTION iterative_refinement(
    initial_matrix: Matrix3x3,
    source_points: Array<Point2D>,
    target_points: Array<Point2D>,
    max_iterations: int,
    convergence_threshold: float64
) -> Matrix3x3:

    current_matrix = initial_matrix

    FOR iteration = 0 TO max_iterations-1:
        // Transform points with current matrix
        transformed = transform_points(current_matrix, source_points)

        // Compute errors
        errors = compute_distances(transformed, target_points)

        // Compute weights (inverse of error)
        weights = compute_weights(errors)

        // Weighted least squares
        refined_matrix = weighted_calibration(
            source_points,
            target_points,
            weights
        )

        // Check convergence
        matrix_change = matrix_norm(refined_matrix - current_matrix)

        IF matrix_change < convergence_threshold:
            BREAK

        current_matrix = refined_matrix

    RETURN current_matrix


FUNCTION compute_weights(errors: Array<float64>) -> Array<float64>:
    n = length(errors)
    weights = Array<float64>(n)
    sum = 0.0

    FOR i = 0 TO n-1:
        weights[i] = 1.0 / (errors[i] + EPSILON)
        sum += weights[i]

    // Normalize weights
    FOR i = 0 TO n-1:
        weights[i] /= sum

    RETURN weights

CONSTANT EPSILON = 1e-6
```

### 3.4 Weighted Calibration

```
FUNCTION weighted_calibration(
    source_points: Array<Point2D>,
    target_points: Array<Point2D>,
    weights: Array<float64>
) -> Matrix3x3:

    n = length(source_points)

    // Build weighted system
    A = Matrix(2*n, 6)
    b = Vector(2*n)
    W = DiagonalMatrix(2*n)

    FOR i = 0 TO n-1:
        xi = source_points[i].x
        yi = source_points[i].y
        xi_prime = target_points[i].x
        yi_prime = target_points[i].y
        w = weights[i]

        // Rows for x' and y' equations
        A[2*i] = [xi, yi, 1.0, 0.0, 0.0, 0.0]
        b[2*i] = xi_prime
        W[2*i][2*i] = w

        A[2*i + 1] = [0.0, 0.0, 0.0, xi, yi, 1.0]
        b[2*i + 1] = yi_prime
        W[2*i + 1][2*i + 1] = w

    // Weighted least squares: (A^T W A) x = A^T W b
    AtWA = transpose(A) × W × A
    AtWb = transpose(A) × W × b
    params = solve_linear_system(AtWA, AtWb)

    // Build matrix
    matrix = Matrix3x3([
        [params[0], params[1], params[2]],
        [params[3], params[4], params[5]],
        [0,         0,         1        ]
    ])

    RETURN matrix
```

---

## 4. Error Propagation

### 4.1 Jacobian Extraction

```
FUNCTION extract_jacobian(matrix: Matrix3x3) -> Matrix2x2:
    // For affine transform, Jacobian is the linear part
    RETURN Matrix2x2([
        [matrix[0][0], matrix[0][1]],
        [matrix[1][0], matrix[1][1]]
    ])
```

### 4.2 Covariance Propagation

```
FUNCTION propagate_covariance(
    covariance_in: Matrix2x2,
    transform: Matrix3x3
) -> Matrix2x2:

    // Extract Jacobian
    J = extract_jacobian(transform)

    // Propagate: Σ_out = J × Σ_in × J^T
    covariance_out = J × covariance_in × transpose(J)

    RETURN covariance_out
```

### 4.3 Error Ellipse Computation

```
FUNCTION compute_error_ellipse(
    covariance: Matrix2x2,
    confidence: float64
) -> (semi_major, semi_minor, angle):

    // Eigenvalue decomposition
    eigenvalues, eigenvectors = eigen_decomposition(covariance)

    // Sort by eigenvalue (descending)
    IF eigenvalues[1] > eigenvalues[0]:
        SWAP(eigenvalues[0], eigenvalues[1])
        SWAP(eigenvectors[0], eigenvectors[1])

    // Chi-square value for confidence level
    IF confidence == 0.95:
        s = 5.991  // 95% confidence, 2 DOF
    ELSE IF confidence == 0.68:
        s = 2.296  // 68% confidence
    ELSE IF confidence == 0.99:
        s = 9.210  // 99% confidence
    ELSE:
        s = chi_square_inverse_cdf(confidence, 2)

    // Semi-axes lengths
    semi_major = sqrt(s * eigenvalues[0])
    semi_minor = sqrt(s * eigenvalues[1])

    // Angle of major axis
    angle = atan2(eigenvectors[0][1], eigenvectors[0][0])

    RETURN (semi_major, semi_minor, angle)
```

### 4.4 Transformation Chain Error

```
FUNCTION track_error_through_chain(
    transformations: Array<Matrix3x3>,
    initial_std_x: float64,
    initial_std_y: float64
) -> (final_std_x, final_std_y):

    // Initialize covariance
    covariance = DiagonalMatrix2x2(initial_std_x², initial_std_y²)

    // Propagate through each transformation
    FOR transform IN transformations:
        covariance = propagate_covariance(covariance, transform)

    // Extract standard deviations
    final_std_x = sqrt(covariance[0][0])
    final_std_y = sqrt(covariance[1][1])

    RETURN (final_std_x, final_std_y)
```

---

## 5. Precision Validation

### 5.1 Round-Trip Validation

```
FUNCTION validate_round_trip(
    transform: Matrix3x3,
    test_points: Array<Point2D>
) -> (max_error, mean_error, std_error):

    n = length(test_points)
    errors = Array<float64>(n)

    // Compute inverse
    inverse_transform = inverse_affine_matrix(transform)

    FOR i = 0 TO n-1:
        // Forward transform
        transformed = transform_point(transform, test_points[i])

        // Inverse transform
        recovered = transform_point(inverse_transform, transformed)

        // Compute error
        dx = test_points[i].x - recovered.x
        dy = test_points[i].y - recovered.y
        errors[i] = sqrt(dx² + dy²)

    max_error = max(errors)
    mean_error = mean(errors)
    std_error = standard_deviation(errors)

    RETURN (max_error, mean_error, std_error)
```

### 5.2 Condition Number

```
FUNCTION compute_condition_number(matrix: Matrix3x3) -> float64:
    // Extract linear part
    linear = Matrix2x2([
        [matrix[0][0], matrix[0][1]],
        [matrix[1][0], matrix[1][1]]
    ])

    // Compute singular values
    singular_values = svd(linear)

    // Condition number = max(σ) / min(σ)
    IF singular_values[1] < EPSILON:
        RETURN INFINITY

    RETURN singular_values[0] / singular_values[1]

CONSTANT EPSILON = 1e-10
```

### 5.3 Sub-Pixel Accuracy Validation

```
FUNCTION validate_subpixel_accuracy(
    transform: Matrix3x3,
    num_tests: int
) -> (is_accurate, max_error, report):

    CONSTANT TARGET_ACCURACY = 1.0 / 256.0  // 1/256 pixel

    // Generate random test points
    test_points = generate_random_points(num_tests, (0, 1920), (0, 1080))

    // Round-trip validation
    max_error, mean_error, std_error = validate_round_trip(transform, test_points)

    // Condition number
    condition = compute_condition_number(transform)

    // Check criteria
    is_accurate = (max_error < TARGET_ACCURACY) AND (condition < 100)

    report = {
        'target_accuracy': TARGET_ACCURACY,
        'achieved_accuracy': max_error,
        'mean_error': mean_error,
        'std_error': std_error,
        'condition_number': condition,
        'is_subpixel_accurate': is_accurate,
        'accuracy_ratio': max_error / TARGET_ACCURACY
    }

    RETURN (is_accurate, max_error, report)
```

### 5.4 Sensitivity Analysis

```
FUNCTION compute_sensitivity(
    transform: Matrix3x3,
    point: Point2D,
    perturbation: float64
) -> float64:

    // Transform original point
    p0 = transform_point(transform, point)

    // Perturb in x direction
    px = Point2D(point.x + perturbation, point.y)
    tx = transform_point(transform, px)
    sensitivity_x = distance(tx, p0) / perturbation

    // Perturb in y direction
    py = Point2D(point.x, point.y + perturbation)
    ty = transform_point(transform, py)
    sensitivity_y = distance(ty, p0) / perturbation

    RETURN max(sensitivity_x, sensitivity_y)

FUNCTION distance(p1: Point2D, p2: Point2D) -> float64:
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    RETURN sqrt(dx² + dy²)
```

---

## 6. Adaptive Correction

### 6.1 Data Structure

```
STRUCTURE CorrectionSample:
    Point2D source       // Original OS coordinate
    Point2D predicted    // Predicted DOM coordinate
    Point2D actual       // Actual DOM coordinate
    Point2D error        // actual - predicted
    float64 error_magnitude

STRUCTURE AdaptiveCorrector:
    Matrix3x3 base_transform
    Array<CorrectionSample> history
    int max_history_size
```

### 6.2 Add Correction Sample

```
FUNCTION add_correction_sample(
    corrector: AdaptiveCorrector,
    source: Point2D,
    predicted: Point2D,
    actual: Point2D
):
    // Compute error
    error = Point2D(actual.x - predicted.x, actual.y - predicted.y)
    error_magnitude = sqrt(error.x² + error.y²)

    // Create sample
    sample = CorrectionSample{
        source: source,
        predicted: predicted,
        actual: actual,
        error: error,
        error_magnitude: error_magnitude
    }

    // Add to history
    corrector.history.append(sample)

    // Limit history size
    IF length(corrector.history) > corrector.max_history_size:
        corrector.history.remove_first()
```

### 6.3 Compute Adaptive Correction

```
FUNCTION compute_adaptive_correction(
    corrector: AdaptiveCorrector,
    point: Point2D
) -> Point2D:

    IF length(corrector.history) == 0:
        RETURN Point2D(0.0, 0.0)

    // Compute distances to all samples
    distances = Array<float64>()
    corrections = Array<Point2D>()

    FOR sample IN corrector.history:
        dist = distance(point, sample.source)

        // Very close match
        IF dist < EPSILON:
            RETURN sample.error

        distances.append(dist)
        corrections.append(sample.error)

    // Inverse distance weighting (power of 2)
    weights = Array<float64>(length(distances))
    weight_sum = 0.0

    FOR i = 0 TO length(distances)-1:
        weights[i] = 1.0 / (distances[i]²)
        weight_sum += weights[i]

    // Normalize weights
    FOR i = 0 TO length(weights)-1:
        weights[i] /= weight_sum

    // Weighted average correction
    correction_x = 0.0
    correction_y = 0.0

    FOR i = 0 TO length(corrections)-1:
        correction_x += weights[i] * corrections[i].x
        correction_y += weights[i] * corrections[i].y

    RETURN Point2D(correction_x, correction_y)

CONSTANT EPSILON = 1e-6
```

### 6.4 Transform with Correction

```
FUNCTION transform_with_correction(
    corrector: AdaptiveCorrector,
    point: Point2D
) -> Point2D:

    // Base transformation
    transformed = transform_point(corrector.base_transform, point)

    // Compute adaptive correction
    correction = compute_adaptive_correction(corrector, point)

    // Apply correction
    corrected = Point2D(
        transformed.x + correction.x,
        transformed.y + correction.y
    )

    RETURN corrected
```

### 6.5 Update Base Transform

```
FUNCTION update_base_transform(corrector: AdaptiveCorrector):
    IF length(corrector.history) < 3:
        RETURN  // Not enough samples

    // Extract source and actual points
    source_points = Array<Point2D>()
    actual_points = Array<Point2D>()

    FOR sample IN corrector.history:
        source_points.append(sample.source)
        actual_points.append(sample.actual)

    // Re-calibrate transformation
    TRY:
        new_transform, _ = calibrate_least_squares(source_points, actual_points)
        corrector.base_transform = new_transform

        // Clear history after updating
        corrector.history.clear()
    CATCH:
        // Keep existing transformation if calibration fails
        PASS
```

---

## 7. Numerical Precision Techniques

### 7.1 Kahan Summation

```
FUNCTION kahan_summation(values: Array<float64>) -> float64:
    // Compensated summation for reduced rounding error

    sum = 0.0
    compensation = 0.0

    FOR value IN values:
        y = value - compensation
        t = sum + y
        compensation = (t - sum) - y
        sum = t

    RETURN sum
```

### 7.2 Sub-Pixel Grid Snapping

```
FUNCTION snap_to_subpixel_grid(
    point: Point2D,
    subdivisions: int
) -> Point2D:

    // Default: 256 subdivisions = 1/256 pixel precision
    scale = float64(subdivisions)

    x_snapped = round(point.x * scale) / scale
    y_snapped = round(point.y * scale) / scale

    RETURN Point2D(x_snapped, y_snapped)
```

### 7.3 Stable Matrix Multiplication

```
FUNCTION stable_matrix_multiply(A: Matrix3x3, B: Matrix3x3) -> Matrix3x3:
    result = Matrix3x3()

    FOR i = 0 TO 2:
        FOR j = 0 TO 2:
            // Use Kahan summation for each element
            terms = Array<float64>()

            FOR k = 0 TO 2:
                terms.append(A[i][k] * B[k][j])

            result[i][j] = kahan_summation(terms)

    RETURN result
```

---

## 8. Complete Workflow

### 8.1 Full Calibration and Transformation Pipeline

```
FUNCTION complete_workflow_example():
    // Step 1: Collect calibration data
    os_points = [
        Point2D(100, 100),
        Point2D(800, 100),
        Point2D(100, 500),
        Point2D(800, 500),
        Point2D(450, 300)
    ]

    dom_points = [
        Point2D(150, 180),
        Point2D(1100, 180),
        Point2D(150, 780),
        Point2D(1100, 780),
        Point2D(625, 480)
    ]

    // Step 2: Calibrate with RANSAC
    transform, inlier_mask, num_inliers = calibrate_ransac(
        os_points,
        dom_points,
        max_iterations = 1000,
        inlier_threshold = 2.0,
        min_inliers = 3
    )

    PRINT("Calibration complete: " + num_inliers + " inliers")

    // Step 3: Iterative refinement
    transform = iterative_refinement(
        transform,
        os_points,
        dom_points,
        max_iterations = 10,
        convergence_threshold = 1e-6
    )

    // Step 4: Validate sub-pixel accuracy
    is_accurate, max_error, report = validate_subpixel_accuracy(
        transform,
        num_tests = 500
    )

    PRINT("Sub-pixel accurate: " + is_accurate)
    PRINT("Max error: " + max_error + " pixels")

    // Step 5: Create adaptive corrector
    corrector = AdaptiveCorrector{
        base_transform: transform,
        history: [],
        max_history_size: 100
    }

    // Step 6: Transform coordinates
    test_point = Point2D(300, 250)
    result = transform_with_correction(corrector, test_point)

    PRINT("OS " + test_point + " -> DOM " + result)

    // Step 7: Add feedback
    actual_click = Point2D(result.x + 0.5, result.y - 0.3)
    add_correction_sample(corrector, test_point, result, actual_click)

    // Step 8: Future transforms use adaptive correction
    next_point = Point2D(400, 300)
    next_result = transform_with_correction(corrector, next_point)

    RETURN transform
```

---

## 9. Complexity Analysis

| Algorithm | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| Least Squares Calibration | O(n) | O(n) |
| RANSAC Calibration | O(k × n) | O(n) |
| Iterative Refinement | O(m × n) | O(n) |
| Transform Point | O(1) | O(1) |
| Transform Batch | O(n) | O(n) |
| Round-Trip Validation | O(n) | O(n) |
| Adaptive Correction | O(h) | O(h) |

Where:
- n = number of calibration points
- k = RANSAC iterations
- m = refinement iterations
- h = correction history size

---

## 10. Implementation Notes

### Precision Requirements
- Use **float64** (double precision) for all floating-point operations
- Machine epsilon: ε ≈ 2.22 × 10⁻¹⁶
- Comparison tolerance: 1 × 10⁻⁹

### Numerical Stability
- Check condition number < 100 for stability
- Use Kahan summation for critical operations
- Avoid catastrophic cancellation in subtractions

### Edge Cases
- Handle singular matrices (det ≈ 0)
- Check for collinear calibration points
- Validate minimum number of points (n ≥ 3)
- Handle division by zero in normalization

### Optimization Opportunities
- Cache matrix inverse
- Batch process transformations
- Use SIMD for vector operations
- Lazy evaluation of composed transformations

---

**End of Pseudocode Documentation**
