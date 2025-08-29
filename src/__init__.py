"""
Covenant - 2D Minecraft-like World Generator

A tile-based world generation and rendering system using python-tcod.
"""

__version__ = "0.1.0"

from .engine import Game, run_game, Camera, InputHandler
from .graphics import GameRenderer, WorldRenderer, EffectRenderer
from .generation import WorldGenerator, Tile
from .utils import get_config, get_tile_registry, profile_function

__all__ = [
    "Game", "run_game", "Camera", "InputHandler",
    "GameRenderer", "WorldRenderer", "EffectRenderer",
    "WorldGenerator", "Tile",
    "get_config", "get_tile_registry", "profile_function"
]
