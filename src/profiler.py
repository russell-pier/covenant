#!/usr/bin/env python3
"""
Performance profiler for identifying bottlenecks in the game.
"""

import time
import functools
from collections import defaultdict, deque
from typing import Dict, List, Callable, Any
import threading

# Profiling flag - controlled by command line argument --profiling
ENABLE_PROFILING = False  # Default: disabled for performance

# To enable profiling:
# Run with: python main.py --profiling
# Profiling stats will print every 10 seconds in console


class PerformanceProfiler:
    """
    Lightweight profiler to identify performance bottlenecks.
    """
    
    def __init__(self, max_samples: int = 100):
        self.max_samples = max_samples
        self.timings: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_samples))
        self.call_counts: Dict[str, int] = defaultdict(int)
        self.active_timers: Dict[str, float] = {}
        self.lock = threading.Lock()
        
    def start_timer(self, name: str):
        """Start timing an operation."""
        with self.lock:
            self.active_timers[name] = time.perf_counter()
    
    def end_timer(self, name: str):
        """End timing an operation and record the duration."""
        with self.lock:
            if name in self.active_timers:
                duration = time.perf_counter() - self.active_timers[name]
                self.timings[name].append(duration)
                self.call_counts[name] += 1
                del self.active_timers[name]
                return duration
            return 0.0
    
    def time_function(self, name: str = None):
        """Decorator to time function calls."""
        def decorator(func: Callable) -> Callable:
            func_name = name or f"{func.__module__}.{func.__name__}"
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                self.start_timer(func_name)
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    self.end_timer(func_name)
            return wrapper
        return decorator
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics."""
        stats = {}
        with self.lock:
            for name, times in self.timings.items():
                if times:
                    times_list = list(times)
                    stats[name] = {
                        'count': self.call_counts[name],
                        'total_time': sum(times_list),
                        'avg_time': sum(times_list) / len(times_list),
                        'min_time': min(times_list),
                        'max_time': max(times_list),
                        'recent_avg': sum(list(times)[-10:]) / min(10, len(times))
                    }
        return stats
    
    def print_stats(self, top_n: int = 10):
        """Print performance statistics."""
        stats = self.get_stats()
        
        print("\n🔍 PERFORMANCE PROFILER RESULTS")
        print("=" * 60)
        
        # Sort by total time
        sorted_stats = sorted(stats.items(), key=lambda x: x[1]['total_time'], reverse=True)
        
        print(f"{'Operation':<30} {'Count':<8} {'Total(ms)':<10} {'Avg(ms)':<10} {'Recent(ms)':<10}")
        print("-" * 80)
        
        for name, data in sorted_stats[:top_n]:
            print(f"{name:<30} {data['count']:<8} "
                  f"{data['total_time']*1000:<10.2f} {data['avg_time']*1000:<10.2f} "
                  f"{data['recent_avg']*1000:<10.2f}")
        
        # Identify potential bottlenecks
        for name, data in sorted_stats[:5]:
            if data['avg_time'] > 0.016:  # > 16ms (60 FPS threshold)
                pass
            elif data['recent_avg'] > 0.010:  # > 10ms recent
                pass
    
    def reset(self):
        """Reset all profiling data."""
        with self.lock:
            self.timings.clear()
            self.call_counts.clear()
            self.active_timers.clear()


# Global profiler instance
profiler = PerformanceProfiler()


def profile_function(name: str = None):
    """Decorator to profile a function."""
    if ENABLE_PROFILING:
        return profiler.time_function(name)
    else:
        # No-op decorator for production
        def decorator(func: Callable) -> Callable:
            return func
        return decorator


def start_profiling(name: str):
    """Start profiling an operation."""
    if ENABLE_PROFILING:
        profiler.start_timer(name)


def end_profiling(name: str):
    """End profiling an operation."""
    if ENABLE_PROFILING:
        return profiler.end_timer(name)
    return 0.0


def print_profiling_stats(top_n: int = 10):
    """Print profiling statistics."""
    if ENABLE_PROFILING:
        profiler.print_stats(top_n)


def reset_profiling():
    """Reset profiling data."""
    if ENABLE_PROFILING:
        profiler.reset()


def enable_profiling():
    """Enable profiling at runtime."""
    global ENABLE_PROFILING
    ENABLE_PROFILING = True


def disable_profiling():
    """Disable profiling at runtime."""
    global ENABLE_PROFILING
    ENABLE_PROFILING = False


def is_profiling_enabled():
    """Check if profiling is currently enabled."""
    return ENABLE_PROFILING


class ProfiledContext:
    """Context manager for profiling code blocks."""
    
    def __init__(self, name: str):
        self.name = name
    
    def __enter__(self):
        start_profiling(self.name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_profiling(self.name)


def profile_context(name: str):
    """Create a profiling context manager."""
    return ProfiledContext(name)


# Convenience function for quick profiling
def quick_profile(func_or_name):
    """Quick profiling decorator or context manager."""
    if callable(func_or_name):
        # Used as @quick_profile
        return profile_function()(func_or_name)
    else:
        # Used as with quick_profile("name"):
        return profile_context(func_or_name)
