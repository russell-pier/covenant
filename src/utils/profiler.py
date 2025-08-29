#!/usr/bin/env python3
"""
Performance profiler for identifying bottlenecks in the game.
"""

import time
import functools
from collections import defaultdict, deque
from typing import Dict, List, Callable, Any
import threading

# Production flag - set to False to disable profiling overhead
ENABLE_PROFILING = False  # Set to True for development, False for production

# To enable profiling for debugging:
# 1. Change ENABLE_PROFILING = True
# 2. Restart the application
# 3. Profiling stats will print every 10 seconds in console


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
            function_name = name or f"{func.__module__}.{func.__name__}"
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                if not ENABLE_PROFILING:
                    return func(*args, **kwargs)
                
                self.start_timer(function_name)
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    self.end_timer(function_name)
            
            return wrapper
        return decorator
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics."""
        with self.lock:
            stats = {}
            for name, times in self.timings.items():
                if times:
                    times_list = list(times)
                    stats[name] = {
                        'count': self.call_counts[name],
                        'total_time': sum(times_list),
                        'avg_time': sum(times_list) / len(times_list),
                        'min_time': min(times_list),
                        'max_time': max(times_list),
                        'recent_avg': sum(times_list[-10:]) / min(10, len(times_list))
                    }
            return stats
    
    def print_stats(self, top_n: int = 10):
        """Print performance statistics."""
        if not ENABLE_PROFILING:
            return
            
        stats = self.get_stats()
        if not stats:
            return
        
        print("\n" + "="*80)
        print("PERFORMANCE PROFILING STATS")
        print("="*80)
        
        # Sort by total time
        sorted_stats = sorted(stats.items(), key=lambda x: x[1]['total_time'], reverse=True)
        
        print(f"{'Function':<40} {'Count':<8} {'Total(ms)':<10} {'Avg(ms)':<10} {'Recent(ms)':<12}")
        print("-" * 80)
        
        for name, stat in sorted_stats[:top_n]:
            print(f"{name:<40} {stat['count']:<8} {stat['total_time']*1000:<10.2f} "
                  f"{stat['avg_time']*1000:<10.2f} {stat['recent_avg']*1000:<12.2f}")
        
        print("="*80)
    
    def reset(self):
        """Reset all profiling data."""
        with self.lock:
            self.timings.clear()
            self.call_counts.clear()
            self.active_timers.clear()


# Global profiler instance
_profiler = PerformanceProfiler()


def profile_function(name: str = None):
    """
    Decorator to profile function performance.
    
    Args:
        name: Optional custom name for the function
        
    Returns:
        Decorated function
    """
    return _profiler.time_function(name)


def start_profiling(name: str):
    """Start profiling an operation."""
    if ENABLE_PROFILING:
        _profiler.start_timer(name)


def end_profiling(name: str):
    """End profiling an operation."""
    if ENABLE_PROFILING:
        return _profiler.end_timer(name)
    return 0.0


def print_profiling_stats(top_n: int = 10):
    """Print profiling statistics."""
    _profiler.print_stats(top_n)


def reset_profiling():
    """Reset all profiling data."""
    _profiler.reset()


def get_profiling_stats() -> Dict[str, Dict[str, float]]:
    """Get profiling statistics."""
    return _profiler.get_stats()


def enable_profiling():
    """Enable profiling globally."""
    global ENABLE_PROFILING
    ENABLE_PROFILING = True
    print("Profiling enabled")


def disable_profiling():
    """Disable profiling globally."""
    global ENABLE_PROFILING
    ENABLE_PROFILING = False
    print("Profiling disabled")
