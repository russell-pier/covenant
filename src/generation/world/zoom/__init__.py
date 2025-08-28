"""
Zoom Layer

Progressively refines terrain detail by subdividing chunks and applying
cellular automata to create natural coastlines and terrain boundaries.

This layer can be used multiple times in sequence to create fractal-like
detail while preserving the overall geographic structure.
"""

from .layer import ZoomLayer

__all__ = ["ZoomLayer"]
