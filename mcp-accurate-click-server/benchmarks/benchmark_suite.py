#!/usr/bin/env python3
"""
Comprehensive Performance Benchmark Suite for Linux Optimizations.

Benchmarks:
1. DPI Query Caching Performance
2. Monitor Enumeration Speed (Batch vs Individual)
3. Subprocess Call Reduction
4. Window Enumeration Performance
5. Coordinate Transformation Pipeline
6. Memory Usage Analysis
7. Cache Hit Rate Analysis

Run with: python -m benchmarks.benchmark_suite
"""

import time
import sys
import os
from typing import List, Dict, Any, Callable, Tuple
import json
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class BenchmarkResult:
    """Result of a single benchmark run."""

    def __init__(self, name: str, iterations: int):
        self.name = name
        self.iterations = iterations
        self.times: List[float] = []
        self.start_time = None

    def start(self):
        """Start timing."""
        self.start_time = time.perf_counter()

    def end(self):
        """End timing."""
        if self.start_time is not None:
            elapsed = time.perf_counter() - self.start_time
            self.times.append(elapsed)
            self.start_time = None

    @property
    def min_ms(self) -> float:
        """Minimum time in milliseconds."""
        return min(self.times) * 1000 if self.times else 0

    @property
    def max_ms(self) -> float:
        """Maximum time in milliseconds."""
        return max(self.times) * 1000 if self.times else 0

    @property
    def mean_ms(self) -> float:
        """Mean time in milliseconds."""
        return (sum(self.times) / len(self.times) * 1000) if self.times else 0

    @property
    def median_ms(self) -> float:
        """Median time in milliseconds."""
        if not self.times:
            return 0
        sorted_times = sorted(self.times)
        mid = len(sorted_times) // 2
        if len(sorted_times) % 2 == 0:
            return (sorted_times[mid - 1] + sorted_times[mid]) / 2 * 1000
        return sorted_times[mid] * 1000

    @property
    def total_ms(self) -> float:
        """Total time in milliseconds."""
        return sum(self.times) * 1000 if self.times else 0

    def __str__(self) -> str:
        """String representation."""
        return (
            f"{self.name}\n"
            f"  Iterations: {len(self.times)}\n"
            f"  Min:    {self.min_ms:.3f} ms\n"
            f"  Max:    {self.max_ms:.3f} ms\n"
            f"  Mean:   {self.mean_ms:.3f} ms\n"
            f"  Median: {self.median_ms:.3f} ms\n"
            f"  Total:  {self.total_ms:.3f} ms"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'iterations': len(self.times),
            'min_ms': self.min_ms,
            'max_ms': self.max_ms,
            'mean_ms': self.mean_ms,
            'median_ms': self.median_ms,
            'total_ms': self.total_ms,
        }


class BenchmarkSuite:
    """Main benchmark suite."""

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.environment = self._get_environment()

    def _get_environment(self) -> Dict[str, str]:
        """Get environment information."""
        return {
            'display_server': os.environ.get('XDG_SESSION_TYPE', 'unknown'),
            'wayland_display': os.environ.get('WAYLAND_DISPLAY', 'none'),
            'x11_display': os.environ.get('DISPLAY', 'none'),
            'platform': sys.platform,
            'python_version': sys.version.split()[0],
        }

    def benchmark(self, name: str, func: Callable, iterations: int = 10) -> BenchmarkResult:
        """
        Run a benchmark function multiple times.

        Args:
            name: Benchmark name
            func: Function to benchmark (takes no arguments)
            iterations: Number of iterations to run

        Returns:
            BenchmarkResult with timing data
        """
        result = BenchmarkResult(name, iterations)
        print(f"\nRunning: {name} ({iterations} iterations)...", end='', flush=True)

        try:
            for i in range(iterations):
                result.start()
                func()
                result.end()
                if (i + 1) % max(1, iterations // 5) == 0:
                    print(f".", end='', flush=True)

            print(" OK")
            self.results.append(result)
            return result

        except Exception as e:
            print(f" FAILED: {e}")
            return result

    def run_dpi_handler_benchmarks(self):
        """Benchmark DPI handler performance."""
        print("\n" + "=" * 60)
        print("DPI HANDLER BENCHMARKS")
        print("=" * 60)

        try:
            from mcp_server.platform.linux.dpi_handler import LinuxDPIHandler

            # Create instance
            dpi_handler = LinuxDPIHandler()

            # Benchmark 1: Initial monitor enumeration
            def enumerate_monitors():
                dpi_handler.enumerate_monitors(refresh=True)

            result1 = self.benchmark("DPI Handler - Monitor Enumeration (with refresh)", enumerate_monitors, iterations=5)

            # Benchmark 2: Cached monitor enumeration (should be much faster)
            def enumerate_cached():
                dpi_handler.enumerate_monitors(refresh=False)

            result2 = self.benchmark("DPI Handler - Monitor Enumeration (cached)", enumerate_cached, iterations=20)

            # Benchmark 3: Get DPI at point
            def get_dpi_at_point():
                dpi_handler.get_dpi_at_point(100, 100)

            result3 = self.benchmark("DPI Handler - Get DPI at point", get_dpi_at_point, iterations=20)

            # Benchmark 4: Get system DPI
            def get_system_dpi():
                dpi_handler.get_system_dpi()

            result4 = self.benchmark("DPI Handler - Get system DPI", get_system_dpi, iterations=20)

            # Calculate speedup
            if result1.mean_ms > 0 and result2.mean_ms > 0:
                cache_speedup = result1.mean_ms / result2.mean_ms
                print(f"\nCache Speedup: {cache_speedup:.1f}x faster")

        except Exception as e:
            print(f"DPI Handler benchmarks failed: {e}")

    def run_optimized_dpi_benchmarks(self):
        """Benchmark optimized DPI handler."""
        print("\n" + "=" * 60)
        print("OPTIMIZED DPI HANDLER BENCHMARKS")
        print("=" * 60)

        try:
            from mcp_server.platform.linux.dpi_handler_optimized import LinuxDPIHandlerOptimized

            dpi_handler = LinuxDPIHandlerOptimized()

            # Benchmark 1: Monitor enumeration
            def enumerate_monitors():
                dpi_handler.enumerate_monitors(refresh=True)

            result1 = self.benchmark("Optimized DPI - Monitor Enumeration (with refresh)", enumerate_monitors, iterations=5)

            # Benchmark 2: Cached enumeration
            def enumerate_cached():
                dpi_handler.enumerate_monitors(refresh=False)

            result2 = self.benchmark("Optimized DPI - Monitor Enumeration (cached)", enumerate_cached, iterations=20)

            # Benchmark 3: Point DPI cache
            def get_dpi_cached():
                for i in range(10):
                    dpi_handler.get_dpi_at_point(100 + i, 100 + i)

            result3 = self.benchmark("Optimized DPI - Point DPI cache (10 points)", get_dpi_cached, iterations=10)

            # Cache hit analysis
            print("\nPoint Cache Analysis:")
            cache = dpi_handler._point_dpi_cache
            print(f"  Cache size: {len(cache)} points")

        except Exception as e:
            print(f"Optimized DPI benchmarks failed: {e}")

    def run_window_manager_benchmarks(self):
        """Benchmark window manager performance."""
        print("\n" + "=" * 60)
        print("WINDOW MANAGER BENCHMARKS")
        print("=" * 60)

        try:
            from mcp_server.platform.linux.window_manager import LinuxWindowManager

            wm = LinuxWindowManager()

            # Benchmark 1: Find browser windows
            def find_browsers():
                wm.find_browser_windows()

            result1 = self.benchmark("Window Manager - Find browser windows", find_browsers, iterations=5)

            # Benchmark 2: Get foreground window
            def get_foreground():
                wm.get_foreground_window()

            result2 = self.benchmark("Window Manager - Get foreground window", get_foreground, iterations=10)

        except Exception as e:
            print(f"Window Manager benchmarks failed: {e}")

    def run_optimized_window_benchmarks(self):
        """Benchmark optimized window manager."""
        print("\n" + "=" * 60)
        print("OPTIMIZED WINDOW MANAGER BENCHMARKS")
        print("=" * 60)

        try:
            from mcp_server.platform.linux.window_manager_optimized import LinuxWindowManagerOptimized

            wm = LinuxWindowManagerOptimized()

            # Benchmark 1: Batch window enumeration
            def batch_enumerate():
                wm._list_windows_wmctrl_batch()

            result1 = self.benchmark("Optimized WM - Batch window enumeration", batch_enumerate, iterations=10)

            # Benchmark 2: Find browsers with batch
            def find_browsers():
                wm.find_browser_windows()

            result2 = self.benchmark("Optimized WM - Find browser windows (batched)", find_browsers, iterations=5)

            # Benchmark 3: Window cache hit
            if hasattr(wm, '_window_cache'):
                print(f"\nWindow cache: {len(wm._window_cache)} cached windows")

        except Exception as e:
            print(f"Optimized Window Manager benchmarks failed: {e}")

    def run_coordinate_benchmarks(self):
        """Benchmark coordinate conversion performance."""
        print("\n" + "=" * 60)
        print("COORDINATE CONVERTER BENCHMARKS")
        print("=" * 60)

        try:
            from mcp_server.platform.linux.coordinate_converter import LinuxCoordinateConverter

            converter = LinuxCoordinateConverter()

            # Benchmark 1: Physical to logical
            def phys_to_logic():
                converter.physical_to_logical(1920, 1080, dpi=96)

            result1 = self.benchmark("Coordinator - Physical to logical", phys_to_logic, iterations=100)

            # Benchmark 2: Logical to physical
            def logic_to_phys():
                converter.logical_to_physical(1920, 1080, dpi=96)

            result2 = self.benchmark("Coordinator - Logical to physical", logic_to_phys, iterations=100)

            # Benchmark 3: Full transformation chain
            def full_chain():
                converter.physical_to_dom_full_chain(
                    1920, 1080, dpi=96,
                    device_pixel_ratio=1.0, browser_zoom=1.0,
                    viewport_offset_x=0, viewport_offset_y=0,
                    scroll_x=0, scroll_y=0
                )

            result3 = self.benchmark("Coordinator - Full transformation chain", full_chain, iterations=50)

        except Exception as e:
            print(f"Coordinate benchmarks failed: {e}")

    def run_all_benchmarks(self):
        """Run all benchmark suites."""
        print("\n" + "=" * 70)
        print("LINUX PERFORMANCE OPTIMIZATION BENCHMARKS")
        print("=" * 70)

        print("\nEnvironment:")
        for key, value in self.environment.items():
            print(f"  {key}: {value}")

        self.run_dpi_handler_benchmarks()
        self.run_optimized_dpi_benchmarks()
        self.run_window_manager_benchmarks()
        self.run_optimized_window_benchmarks()
        self.run_coordinate_benchmarks()

        self.print_summary()

    def print_summary(self):
        """Print benchmark summary."""
        print("\n" + "=" * 70)
        print("BENCHMARK SUMMARY")
        print("=" * 70)

        if not self.results:
            print("No benchmarks completed.")
            return

        # Group by category
        categories = {}
        for result in self.results:
            # Extract category from name (first part before -)
            parts = result.name.split('-')
            category = parts[0].strip() if parts else result.name

            if category not in categories:
                categories[category] = []
            categories[category].append(result)

        # Print by category
        for category in sorted(categories.keys()):
            print(f"\n{category}:")
            for result in categories[category]:
                print(f"  {result.name}")
                print(f"    Mean: {result.mean_ms:.3f} ms (iterations: {len(result.times)})")

        # Export to JSON
        self.export_results()

    def export_results(self):
        """Export results to JSON file."""
        output_file = Path(__file__).parent / "benchmark_results.json"

        results_data = {
            'timestamp': datetime.now().isoformat(),
            'environment': self.environment,
            'results': [r.to_dict() for r in self.results],
        }

        try:
            with open(output_file, 'w') as f:
                json.dump(results_data, f, indent=2)
            print(f"\nResults saved to: {output_file}")
        except Exception as e:
            print(f"Failed to save results: {e}")


def main():
    """Main entry point."""
    suite = BenchmarkSuite()
    suite.run_all_benchmarks()


if __name__ == '__main__':
    main()
