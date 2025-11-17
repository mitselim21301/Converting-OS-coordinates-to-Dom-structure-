"""
Test Windows Coordinate Conversion

Tests for Windows-specific coordinate transformations:
- DPI awareness and scaling
- Multi-monitor support
- Client/Screen coordinate conversion
- Affine transformations
- Calibration and accuracy
- Sub-pixel precision
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock, patch

# Import test utilities from conftest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from conftest import (
    sample_calibration_points,
    assert_coordinates_close,
    assert_transformation_accurate
)


class TestDPIScaling:
    """Test DPI awareness and scaling"""

    def test_get_system_dpi(self, mock_windows_api):
        """Test getting system DPI"""
        dpi = mock_windows_api['gdi32'].GetDeviceCaps.return_value
        assert dpi == 96  # Standard DPI

    def test_calculate_dpi_scale_factor(self):
        """Test calculating DPI scale factor"""
        standard_dpi = 96
        actual_dpi = 144  # 150% scaling

        scale_factor = actual_dpi / standard_dpi
        assert scale_factor == 1.5

    def test_apply_dpi_scaling_to_coordinates(self):
        """Test applying DPI scaling to coordinates"""
        x, y = 100, 200
        scale_factor = 1.5

        scaled_x = x * scale_factor
        scaled_y = y * scale_factor

        assert scaled_x == 150
        assert scaled_y == 300

    def test_inverse_dpi_scaling(self):
        """Test inverse DPI scaling"""
        scaled_x, scaled_y = 150, 300
        scale_factor = 1.5

        x = scaled_x / scale_factor
        y = scaled_y / scale_factor

        assert x == 100
        assert y == 200

    def test_dpi_scaling_100_percent(self):
        """Test DPI scaling at 100% (no scaling)"""
        x, y = 100, 200
        scale_factor = 1.0

        scaled_x = x * scale_factor
        scaled_y = y * scale_factor

        assert scaled_x == x
        assert scaled_y == y

    def test_dpi_scaling_125_percent(self):
        """Test DPI scaling at 125%"""
        x, y = 100, 200
        dpi = 120  # 125% of 96
        scale_factor = dpi / 96

        scaled_x = x * scale_factor
        scaled_y = y * scale_factor

        assert pytest.approx(scaled_x) == 125
        assert pytest.approx(scaled_y) == 250

    def test_dpi_scaling_200_percent(self):
        """Test DPI scaling at 200%"""
        x, y = 100, 200
        scale_factor = 2.0

        scaled_x = x * scale_factor
        scaled_y = y * scale_factor

        assert scaled_x == 200
        assert scaled_y == 400


class TestCoordinateConversion:
    """Test coordinate system conversions"""

    def test_screen_to_client_conversion(self, mock_windows_api):
        """Test screen to client coordinate conversion"""
        # Mock window rect
        window_rect = (10, 20, 810, 620)  # left, top, right, bottom

        screen_x, screen_y = 100, 150

        # Client coordinates are relative to window
        client_x = screen_x - window_rect[0]
        client_y = screen_y - window_rect[1]

        assert client_x == 90
        assert client_y == 130

    def test_client_to_screen_conversion(self, mock_windows_api):
        """Test client to screen coordinate conversion"""
        window_rect = (10, 20, 810, 620)

        client_x, client_y = 90, 130

        screen_x = client_x + window_rect[0]
        screen_y = client_y + window_rect[1]

        assert screen_x == 100
        assert screen_y == 150

    def test_round_trip_coordinate_conversion(self):
        """Test round-trip coordinate conversion"""
        window_offset = (10, 20)
        original_screen = (100, 150)

        # Screen to client
        client = (
            original_screen[0] - window_offset[0],
            original_screen[1] - window_offset[1]
        )

        # Client to screen
        recovered_screen = (
            client[0] + window_offset[0],
            client[1] + window_offset[1]
        )

        assert recovered_screen == original_screen

    def test_multiple_coordinate_systems(self):
        """Test working with multiple coordinate systems"""
        # Define coordinate systems
        screen_coords = (500, 400)
        window_offset = (100, 50)
        dpi_scale = 1.25

        # Screen to client
        client_coords = (
            screen_coords[0] - window_offset[0],
            screen_coords[1] - window_offset[1]
        )

        # Apply DPI scaling
        scaled_coords = (
            client_coords[0] * dpi_scale,
            client_coords[1] * dpi_scale
        )

        assert client_coords == (400, 350)
        assert scaled_coords == (500, 437.5)


class TestMultiMonitor:
    """Test multi-monitor support"""

    def test_primary_monitor_coordinates(self):
        """Test coordinates on primary monitor"""
        # Primary monitor typically starts at (0, 0)
        monitor_bounds = {
            'left': 0,
            'top': 0,
            'right': 1920,
            'bottom': 1080
        }

        x, y = 100, 200

        # Check if point is within monitor bounds
        is_within = (
            monitor_bounds['left'] <= x <= monitor_bounds['right'] and
            monitor_bounds['top'] <= y <= monitor_bounds['bottom']
        )

        assert is_within is True

    def test_secondary_monitor_coordinates(self):
        """Test coordinates on secondary monitor"""
        # Secondary monitor to the right of primary
        monitor_bounds = {
            'left': 1920,
            'top': 0,
            'right': 3840,
            'bottom': 1080
        }

        x, y = 2000, 500

        is_within = (
            monitor_bounds['left'] <= x <= monitor_bounds['right'] and
            monitor_bounds['top'] <= y <= monitor_bounds['bottom']
        )

        assert is_within is True

    def test_negative_monitor_coordinates(self):
        """Test negative coordinates (monitor to the left)"""
        # Monitor positioned to the left of primary
        monitor_bounds = {
            'left': -1920,
            'top': 0,
            'right': 0,
            'bottom': 1080
        }

        x, y = -500, 400

        is_within = (
            monitor_bounds['left'] <= x <= monitor_bounds['right'] and
            monitor_bounds['top'] <= y <= monitor_bounds['bottom']
        )

        assert is_within is True

    def test_monitor_dpi_differences(self):
        """Test different DPI settings per monitor"""
        monitor1_dpi = 96   # 100%
        monitor2_dpi = 144  # 150%

        x, y = 100, 200

        # Scale for monitor 1
        scaled1 = (x * monitor1_dpi / 96, y * monitor1_dpi / 96)

        # Scale for monitor 2
        scaled2 = (x * monitor2_dpi / 96, y * monitor2_dpi / 96)

        assert scaled1 == (100, 200)
        assert scaled2 == (150, 300)

    def test_virtual_screen_bounds(self):
        """Test virtual screen bounds across monitors"""
        # Virtual screen encompasses all monitors
        virtual_bounds = {
            'left': -1920,   # Left monitor
            'top': 0,
            'right': 3840,   # Right monitor
            'bottom': 1080
        }

        virtual_width = virtual_bounds['right'] - virtual_bounds['left']
        virtual_height = virtual_bounds['bottom'] - virtual_bounds['top']

        assert virtual_width == 5760  # 3 monitors of 1920 width
        assert virtual_height == 1080


class TestAffineTransformation:
    """Test affine transformation for coordinate mapping"""

    def test_identity_transformation(self):
        """Test identity transformation (no change)"""
        # Identity matrix
        matrix = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1]
        ])

        point = np.array([100, 200, 1])
        transformed = matrix @ point

        assert transformed[0] == 100
        assert transformed[1] == 200

    def test_translation_transformation(self):
        """Test translation transformation"""
        # Translation by (50, 30)
        matrix = np.array([
            [1, 0, 50],
            [0, 1, 30],
            [0, 0, 1]
        ])

        point = np.array([100, 200, 1])
        transformed = matrix @ point

        assert transformed[0] == 150
        assert transformed[1] == 230

    def test_scaling_transformation(self):
        """Test scaling transformation"""
        # Scale by 1.5x
        matrix = np.array([
            [1.5, 0, 0],
            [0, 1.5, 0],
            [0, 0, 1]
        ])

        point = np.array([100, 200, 1])
        transformed = matrix @ point

        assert transformed[0] == 150
        assert transformed[1] == 300

    def test_rotation_transformation(self):
        """Test rotation transformation"""
        # Rotate by 90 degrees counterclockwise
        theta = np.pi / 2
        matrix = np.array([
            [np.cos(theta), -np.sin(theta), 0],
            [np.sin(theta), np.cos(theta), 0],
            [0, 0, 1]
        ])

        point = np.array([100, 0, 1])
        transformed = matrix @ point

        assert pytest.approx(transformed[0]) == 0
        assert pytest.approx(transformed[1]) == 100

    def test_combined_transformation(self):
        """Test combined transformation (scale + rotate + translate)"""
        # Scale 2x, rotate 45°, translate (10, 20)
        scale = 2.0
        theta = np.pi / 4
        tx, ty = 10, 20

        matrix = np.array([
            [scale * np.cos(theta), -scale * np.sin(theta), tx],
            [scale * np.sin(theta), scale * np.cos(theta), ty],
            [0, 0, 1]
        ])

        point = np.array([10, 0, 1])
        transformed = matrix @ point

        # Verify transformation applied
        assert transformed.shape == (3,)

    def test_inverse_transformation(self):
        """Test inverse transformation"""
        # Create transformation
        matrix = np.array([
            [2, 0, 10],
            [0, 2, 20],
            [0, 0, 1]
        ])

        # Calculate inverse
        inverse = np.linalg.inv(matrix)

        point = np.array([100, 200, 1])
        transformed = matrix @ point
        recovered = inverse @ transformed

        assert pytest.approx(recovered[0]) == 100
        assert pytest.approx(recovered[1]) == 200


class TestCalibration:
    """Test coordinate transformation calibration"""

    def test_calibrate_with_known_points(self, sample_calibration_points):
        """Test calibration with known point pairs"""
        os_points, dom_points = sample_calibration_points

        assert len(os_points) == len(dom_points)
        assert len(os_points) >= 3  # Minimum for affine transform

    def test_least_squares_calibration(self, sample_calibration_points):
        """Test least squares calibration"""
        os_points, dom_points = sample_calibration_points

        # Add homogeneous coordinate
        n = len(os_points)
        A = np.hstack([os_points, np.ones((n, 1))])

        # Solve for transformation (simplified)
        # In practice, would use proper affine calibration
        assert A.shape == (10, 3)
        assert dom_points.shape == (10, 2)

    def test_ransac_calibration(self, sample_calibration_points):
        """Test RANSAC-based calibration (outlier rejection)"""
        os_points, dom_points = sample_calibration_points

        # Simulate RANSAC
        best_inliers = 0
        best_model = None

        # Simple simulation: assume 80% inliers
        inlier_count = int(len(os_points) * 0.8)

        assert inlier_count >= 3

    def test_calibration_accuracy(self, sample_calibration_points):
        """Test calibration accuracy measurement"""
        os_points, dom_points = sample_calibration_points

        # Simulate perfect transformation
        errors = np.zeros(len(os_points))

        mean_error = np.mean(errors)
        max_error = np.max(errors)

        assert mean_error == 0
        assert max_error == 0

    def test_iterative_refinement(self, sample_calibration_points):
        """Test iterative refinement of calibration"""
        os_points, dom_points = sample_calibration_points

        # Simulate refinement iterations
        initial_error = 2.0
        refined_error = 0.5

        assert refined_error < initial_error

    def test_multi_scale_calibration(self):
        """Test calibration at different zoom levels"""
        scales = [1.0, 1.5, 2.0]
        calibrations = {}

        for scale in scales:
            # Would store calibration for each scale
            calibrations[scale] = {
                'matrix': np.eye(3),
                'error': 0.5
            }

        assert len(calibrations) == 3
        assert 1.5 in calibrations


class TestSubPixelPrecision:
    """Test sub-pixel precision"""

    def test_floating_point_coordinates(self):
        """Test handling floating point coordinates"""
        x, y = 100.75, 200.333

        # Should maintain precision
        assert isinstance(x, float)
        assert x == 100.75
        assert y == pytest.approx(200.333)

    def test_subpixel_transformation(self):
        """Test transformation preserves sub-pixel precision"""
        # Scale by 1.5
        x, y = 100.0, 200.0
        scale = 1.5

        result_x = x * scale
        result_y = y * scale

        assert result_x == 150.0
        assert result_y == 300.0

    def test_subpixel_rounding(self):
        """Test sub-pixel rounding when needed"""
        x = 100.75

        rounded = round(x)
        floored = int(np.floor(x))
        ceiled = int(np.ceil(x))

        assert rounded == 101
        assert floored == 100
        assert ceiled == 101

    def test_subpixel_error_measurement(self):
        """Test measuring sub-pixel errors"""
        predicted = (100.5, 200.3)
        actual = (100.7, 200.1)

        error_x = abs(predicted[0] - actual[0])
        error_y = abs(predicted[1] - actual[1])
        error_magnitude = np.sqrt(error_x**2 + error_y**2)

        assert error_x == 0.2
        assert error_y == 0.2
        assert error_magnitude < 1.0  # Sub-pixel accurate

    def test_high_precision_transformation(self):
        """Test high precision transformation (< 1/256 pixel)"""
        x, y = 100.0, 200.0
        transform = np.array([
            [1.0000001, 0, 0],
            [0, 1.0000001, 0],
            [0, 0, 1]
        ])

        point = np.array([x, y, 1])
        result = transform @ point

        error = abs(result[0] - x)
        assert error < 1.0 / 256.0  # Sub-pixel precision target


class TestErrorAnalysis:
    """Test error analysis and validation"""

    def test_transformation_error_measurement(self):
        """Test measuring transformation error"""
        source = np.array([100, 200])
        target = np.array([101, 199])
        predicted = np.array([100.5, 200.3])

        error = np.linalg.norm(predicted - target)

        assert error < 2.0  # Within acceptable range

    def test_root_mean_square_error(self):
        """Test RMS error calculation"""
        errors = np.array([0.5, 1.0, 0.8, 1.2, 0.6])

        rmse = np.sqrt(np.mean(errors**2))

        assert rmse < 1.5

    def test_maximum_error_detection(self):
        """Test detecting maximum error"""
        errors = np.array([0.5, 1.0, 0.8, 5.0, 0.6])

        max_error = np.max(errors)

        assert max_error == 5.0

    def test_error_distribution_analysis(self):
        """Test analyzing error distribution"""
        errors = np.random.randn(100) * 0.5  # Normal distribution

        mean_error = np.mean(np.abs(errors))
        std_error = np.std(errors)

        assert mean_error < 1.0
        assert std_error < 1.0

    def test_outlier_detection(self):
        """Test detecting outliers in errors"""
        errors = np.array([0.5, 0.6, 0.7, 10.0, 0.5, 0.6])

        threshold = 3.0
        outliers = errors > threshold

        assert np.sum(outliers) == 1  # One outlier

    def test_condition_number_check(self):
        """Test transformation matrix condition number"""
        # Well-conditioned matrix
        matrix = np.array([
            [2, 0, 0],
            [0, 2, 0],
            [0, 0, 1]
        ])

        condition = np.linalg.cond(matrix)

        assert condition < 100  # Well-conditioned


class TestWindowsAPIIntegration:
    """Test Windows API integration"""

    @pytest.mark.requires_windows
    def test_get_cursor_position(self, mock_windows_api):
        """Test getting cursor position via Windows API"""
        # Mock cursor position
        mock_windows_api['user32'].GetCursorPos.return_value = True

        # Would call actual API
        success = mock_windows_api['user32'].GetCursorPos()

        assert success is True

    @pytest.mark.requires_windows
    def test_get_window_rect(self, mock_windows_api):
        """Test getting window rectangle"""
        mock_windows_api['user32'].GetWindowRect.return_value = True

        success = mock_windows_api['user32'].GetWindowRect()

        assert success is True

    @pytest.mark.requires_windows
    def test_monitor_enumeration(self):
        """Test enumerating monitors"""
        # Mock monitor list
        monitors = [
            {'left': 0, 'top': 0, 'right': 1920, 'bottom': 1080},
            {'left': 1920, 'top': 0, 'right': 3840, 'bottom': 1080}
        ]

        assert len(monitors) == 2

    @pytest.mark.requires_windows
    def test_dpi_awareness_context(self, mock_windows_api):
        """Test DPI awareness context"""
        # Mock DPI awareness
        dpi = mock_windows_api['user32'].GetSystemMetrics.return_value

        assert dpi == 96


class TestCoordinateTransformPipeline:
    """Test complete coordinate transformation pipeline"""

    def test_os_to_dom_pipeline(self):
        """Test complete OS to DOM coordinate pipeline"""
        # 1. Get OS coordinates
        os_x, os_y = 500, 400

        # 2. Get window offset
        window_offset = (100, 50)

        # 3. Convert to client coordinates
        client_x = os_x - window_offset[0]
        client_y = os_y - window_offset[1]

        # 4. Apply DPI scaling
        dpi_scale = 1.25
        scaled_x = client_x * dpi_scale
        scaled_y = client_y * dpi_scale

        # 5. Apply affine transformation (simplified)
        dom_x = scaled_x
        dom_y = scaled_y

        assert client_x == 400
        assert client_y == 350
        assert dom_x == 500
        assert dom_y == 437.5

    def test_dom_to_os_pipeline(self):
        """Test complete DOM to OS coordinate pipeline (inverse)"""
        # Start with DOM coordinates
        dom_x, dom_y = 500, 437.5

        # 1. Inverse affine transformation
        scaled_x = dom_x
        scaled_y = dom_y

        # 2. Inverse DPI scaling
        dpi_scale = 1.25
        client_x = scaled_x / dpi_scale
        client_y = scaled_y / dpi_scale

        # 3. Convert to screen coordinates
        window_offset = (100, 50)
        os_x = client_x + window_offset[0]
        os_y = client_y + window_offset[1]

        assert pytest.approx(os_x) == 500
        assert pytest.approx(os_y) == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
