"""
Islands Layer

Converts isolated water chunks (completely surrounded by land) into land chunks.
Creates small islands and fills water gaps within landmasses for more natural terrain.
"""

from .layer import IslandsLayer

__all__ = ["IslandsLayer"]