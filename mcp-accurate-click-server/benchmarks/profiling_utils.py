"""
Performance Profiling Utilities.

Tools for profiling critical paths in Linux implementation:
- Function timing decorator
- Call counter
- Memory profiler integration
- Subprocess call tracker
- Cache statistics collector
"""

import functools
import time
import os
import subprocess
from typing import Callable, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import sys
from contextlib import contextmanager


@dataclass
class FunctionStats:
    """Statistics for a profiled function."""
    name: str
    calls: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0

    @property
    def avg_time(self) -> float:
        """Average execution time."""
        return self.total_time / self.calls if self.calls > 0 else 0

    def __str__(self) -> str:
        """String representation."""
        return (
            f"{self.name}\n"
            f"  Calls: {self.calls}\n"
            f"  Total: {self.total_time:.6f}s\n"
            f"  Avg:   {self.avg_time:.6f}s\n"
            f"  Min:   {self.min_time:.6f}s\n"
            f"  Max:   {self.max_time:.6f}s"
        )


class FunctionProfiler:
    """Profile function execution times."""

    _stats: Dict[str, FunctionStats] = {}

    @classmethod
    def reset(cls):
        """Reset all statistics."""
        cls._stats.clear()

    @classmethod
    def profile(cls, func: Callable) -> Callable:
        """Decorator to profile a function."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"

            if func_name not in cls._stats:
                cls._stats[func_name] = FunctionStats(func_name)

            stats = cls._stats[func_name]
            start = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.perf_counter() - start
                stats.calls += 1
                stats.total_time += elapsed
                stats.min_time = min(stats.min_time, elapsed)
                stats.max_time = max(stats.max_time, elapsed)

        return wrapper

    @classmethod
    def get_stats(cls) -> Dict[str, FunctionStats]:
        """Get all profiling statistics."""
        return cls._stats.copy()

    @classmethod
    def print_stats(cls, sort_by: str = 'total'):
        """Print profiling statistics.

        Args:
            sort_by: 'total', 'avg', 'calls', 'max'
        """
        if not cls._stats:
            print("No statistics collected.")
            return

        print("\n" + "=" * 70)
        print("FUNCTION PROFILING STATISTICS")
        print("=" * 70)

        # Sort statistics
        if sort_by == 'total':
            sorted_stats = sorted(cls._stats.values(), key=lambda s: s.total_time, reverse=True)
        elif sort_by == 'avg':
            sorted_stats = sorted(cls._stats.values(), key=lambda s: s.avg_time, reverse=True)
        elif sort_by == 'calls':
            sorted_stats = sorted(cls._stats.values(), key=lambda s: s.calls, reverse=True)
        elif sort_by == 'max':
            sorted_stats = sorted(cls._stats.values(), key=lambda s: s.max_time, reverse=True)
        else:
            sorted_stats = list(cls._stats.values())

        for stats in sorted_stats:
            print(f"\n{stats.name}")
            print(f"  Calls:  {stats.calls}")
            print(f"  Total:  {stats.total_time*1000:.3f} ms")
            print(f"  Avg:    {stats.avg_time*1000:.3f} ms")
            print(f"  Min:    {stats.min_time*1000:.3f} ms")
            print(f"  Max:    {stats.max_time*1000:.3f} ms")


class CallCounter:
    """Track subprocess and system calls."""

    _calls: Dict[str, int] = {}
    _enabled = False

    @classmethod
    def enable(cls):
        """Enable call counting."""
        cls._enabled = True

    @classmethod
    def disable(cls):
        """Disable call counting."""
        cls._enabled = False

    @classmethod
    def reset(cls):
        """Reset call counts."""
        cls._calls.clear()

    @classmethod
    def count_call(cls, call_name: str, count: int = 1):
        """Count a system call."""
        if not cls._enabled:
            return

        if call_name not in cls._calls:
            cls._calls[call_name] = 0
        cls._calls[call_name] += count

    @classmethod
    def get_counts(cls) -> Dict[str, int]:
        """Get all call counts."""
        return cls._calls.copy()

    @classmethod
    def print_counts(cls):
        """Print call counts."""
        if not cls._calls:
            print("No calls recorded.")
            return

        print("\n" + "=" * 70)
        print("SYSTEM CALL STATISTICS")
        print("=" * 70)

        sorted_calls = sorted(cls._calls.items(), key=lambda x: x[1], reverse=True)
        total = sum(x[1] for x in sorted_calls)

        for call_name, count in sorted_calls:
            percentage = (count / total * 100) if total > 0 else 0
            print(f"{call_name:40} {count:6d} ({percentage:5.1f}%)")

        print(f"\nTotal calls: {total}")


@contextmanager
def profile_block(name: str):
    """Context manager to profile a code block."""
    start = time.perf_counter()
    print(f"[PROFILE] Starting: {name}")

    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"[PROFILE] Completed: {name} ({elapsed*1000:.3f} ms)")


class CacheStatistics:
    """Track cache performance."""

    def __init__(self, name: str, max_size: int = 100):
        """Initialize cache statistics tracker.

        Args:
            name: Cache name
            max_size: Maximum cache size
        """
        self.name = name
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def record_hit(self):
        """Record a cache hit."""
        self.hits += 1

    def record_miss(self):
        """Record a cache miss."""
        self.misses += 1

    def record_eviction(self):
        """Record a cache eviction."""
        self.evictions += 1

    @property
    def hit_rate(self) -> float:
        """Cache hit rate (0-1)."""
        total = self.hits + self.misses
        return (self.hits / total) if total > 0 else 0

    def __str__(self) -> str:
        """String representation."""
        return (
            f"{self.name} Cache\n"
            f"  Hits:       {self.hits}\n"
            f"  Misses:     {self.misses}\n"
            f"  Evictions:  {self.evictions}\n"
            f"  Hit Rate:   {self.hit_rate*100:.1f}%"
        )


class SubprocessCallTracker:
    """Track subprocess calls for optimization analysis."""

    _calls: Dict[str, list] = {}
    _enabled = False

    @classmethod
    def enable(cls):
        """Enable tracking."""
        cls._enabled = True

    @classmethod
    def disable(cls):
        """Disable tracking."""
        cls._enabled = False

    @classmethod
    def reset(cls):
        """Reset tracking data."""
        cls._calls.clear()

    @classmethod
    def track_call(cls, cmd: str, duration: float):
        """Track a subprocess call.

        Args:
            cmd: Command name or full command
            duration: Execution time in seconds
        """
        if not cls._enabled:
            return

        if cmd not in cls._calls:
            cls._calls[cmd] = []

        cls._calls[cmd].append(duration)

    @classmethod
    def get_summary(cls) -> Dict[str, Dict[str, Any]]:
        """Get summary statistics.

        Returns:
            Dict with call counts, total time, and average time
        """
        summary = {}

        for cmd, durations in cls._calls.items():
            summary[cmd] = {
                'count': len(durations),
                'total_time': sum(durations),
                'avg_time': sum(durations) / len(durations) if durations else 0,
                'min_time': min(durations) if durations else 0,
                'max_time': max(durations) if durations else 0,
            }

        return summary

    @classmethod
    def print_summary(cls):
        """Print subprocess call summary."""
        summary = cls.get_summary()

        if not summary:
            print("No subprocess calls tracked.")
            return

        print("\n" + "=" * 70)
        print("SUBPROCESS CALL STATISTICS")
        print("=" * 70)

        # Sort by total time
        sorted_calls = sorted(summary.items(), key=lambda x: x[1]['total_time'], reverse=True)

        for cmd, stats in sorted_calls:
            print(f"\n{cmd}")
            print(f"  Count:      {stats['count']}")
            print(f"  Total Time: {stats['total_time']*1000:.3f} ms")
            print(f"  Avg Time:   {stats['avg_time']*1000:.3f} ms")
            print(f"  Min Time:   {stats['min_time']*1000:.3f} ms")
            print(f"  Max Time:   {stats['max_time']*1000:.3f} ms")


class PerformanceReport:
    """Generate comprehensive performance report."""

    def __init__(self):
        """Initialize report."""
        self.timestamp = time.time()

    def generate(self) -> str:
        """Generate comprehensive report."""
        lines = [
            "\n" + "=" * 70,
            "COMPREHENSIVE PERFORMANCE REPORT",
            "=" * 70,
        ]

        # Function profiling
        if FunctionProfiler._stats:
            lines.append("\nFunction Profiling:")
            lines.append("-" * 70)
            for stats in sorted(FunctionProfiler._stats.values(), key=lambda s: s.total_time, reverse=True)[:10]:
                lines.append(f"{stats.name:40} {stats.avg_time*1000:8.3f} ms (calls: {stats.calls})")

        # System calls
        if CallCounter._calls:
            lines.append("\nSystem Calls:")
            lines.append("-" * 70)
            total_calls = sum(CallCounter._calls.values())
            for call_name, count in sorted(CallCounter._calls.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"{call_name:40} {count:6d} calls")

        # Subprocess calls
        summary = SubprocessCallTracker.get_summary()
        if summary:
            lines.append("\nSubprocess Calls:")
            lines.append("-" * 70)
            for cmd, stats in sorted(summary.items(), key=lambda x: x[1]['total_time'], reverse=True):
                lines.append(f"{cmd:40} {stats['count']:3d} calls ({stats['total_time']*1000:8.1f} ms total)")

        return "\n".join(lines)

    def save(self, filepath: Path):
        """Save report to file."""
        with open(filepath, 'w') as f:
            f.write(self.generate())


# Global profiler instances
_profiler = FunctionProfiler()
_call_counter = CallCounter()
_subprocess_tracker = SubprocessCallTracker()
_performance_report = PerformanceReport()


__all__ = [
    'FunctionProfiler',
    'CallCounter',
    'profile_block',
    'CacheStatistics',
    'SubprocessCallTracker',
    'PerformanceReport',
]
