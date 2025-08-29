"""
Shared Utilities

Contains configuration loading, profiling, tile registry, and other shared utilities.
"""

from .config import get_config, load_config
from .tiles import get_tile_registry
try:
    from .profiler import profile_function, start_profiling, end_profiling
except ImportError:
    # Fallback for when profiler is not available
    def profile_function(name=None):
        def decorator(func):
            return func
        return decorator
    def start_profiling(name): pass
    def end_profiling(name): pass

__all__ = [
    "get_config",
    "load_config", 
    "get_tile_registry",
    "profile_function",
    "start_profiling",
    "end_profiling"
]
