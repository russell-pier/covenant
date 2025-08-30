"""
Covenant - 2D Minecraft-like World Generator

A tile-based world generation and rendering system using python-tcod.
"""

__version__ = "0.1.0"

from .render.render import GameRenderer, WorldRenderer, EffectRenderer
from .world import WorldManager, Tile, TierManager
from .ui import StatusDisplay

__all__ = [
    "GameRenderer", "WorldRenderer", "EffectRenderer",
    "WorldManager", "Tile", "TierManager",
    "StatusDisplay"
]
