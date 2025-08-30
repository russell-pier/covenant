"""
Covenant - 2D Minecraft-like World Generator

A tile-based world generation and rendering system using python-tcod.
"""

__version__ = "0.1.0"

# Core world generation (always available)
from .world import WorldManager, Tile, TierManager

# Optional rendering components (require tcod)
try:
    from .render.render import GameRenderer, WorldRenderer, EffectRenderer
    from .ui import StatusDisplay
    _RENDER_AVAILABLE = True
except ImportError:
    _RENDER_AVAILABLE = False

if _RENDER_AVAILABLE:
    __all__ = [
        "GameRenderer", "WorldRenderer", "EffectRenderer",
        "WorldManager", "Tile", "TierManager",
        "StatusDisplay"
    ]
else:
    __all__ = [
        "WorldManager", "Tile", "TierManager"
    ]
