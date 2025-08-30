#!/usr/bin/env python3
"""
Tile configuration system for the 2D Minecraft-like world

Handles loading tile definitions from TOML files and providing
tile rendering information to the rendering system.
"""

import os
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback for older Python versions


@dataclass
class TileConfig:
    """Configuration for a single tile type."""
    name: str
    character: str
    font_color: Tuple[int, int, int]
    background_color: Tuple[int, int, int]
    
    def __post_init__(self):
        """Validate tile configuration after initialization."""
        # Ensure colors are valid RGB tuples
        if not (isinstance(self.font_color, (list, tuple)) and len(self.font_color) == 3):
            raise ValueError(f"Invalid font_color for tile '{self.name}': {self.font_color}")
        if not (isinstance(self.background_color, (list, tuple)) and len(self.background_color) == 3):
            raise ValueError(f"Invalid background_color for tile '{self.name}': {self.background_color}")
        
        # Convert to tuples if they're lists
        self.font_color = tuple(self.font_color)
        self.background_color = tuple(self.background_color)
        
        # Validate RGB values are in range 0-255
        for color_name, color in [("font_color", self.font_color), ("background_color", self.background_color)]:
            for i, value in enumerate(color):
                if not (0 <= value <= 255):
                    raise ValueError(f"Invalid {color_name}[{i}] for tile '{self.name}': {value} (must be 0-255)")


class TileRegistry:
    """Registry for all tile configurations."""

    def __init__(self, config_file: str):
        self.tiles: Dict[str, TileConfig] = {}
        self.config_file = config_file
        self.load_tiles()
    
    def load_tiles(self):
        """Load tile configurations from the TOML file - fails if missing or invalid."""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"❌ Tile configuration file not found: {self.config_file}")

        try:
            with open(self.config_file, 'rb') as f:
                config_data = tomllib.load(f)

            self.tiles.clear()

            for tile_id, tile_data in config_data.items():
                # Require all tile properties - no fallbacks
                if 'name' not in tile_data:
                    raise KeyError(f"❌ Missing required 'name' for tile '{tile_id}'")
                if 'character' not in tile_data:
                    raise KeyError(f"❌ Missing required 'character' for tile '{tile_id}'")
                if 'font_color' not in tile_data:
                    raise KeyError(f"❌ Missing required 'font_color' for tile '{tile_id}'")
                if 'background_color' not in tile_data:
                    raise KeyError(f"❌ Missing required 'background_color' for tile '{tile_id}'")

                tile_config = TileConfig(
                    name=tile_data['name'],
                    character=tile_data['character'],
                    font_color=tile_data['font_color'],
                    background_color=tile_data['background_color']
                )
                self.tiles[tile_id] = tile_config

        except Exception as e:
            raise RuntimeError(f"❌ Failed to load tile configuration from {self.config_file}: {e}") from e
    


    
    def get_tile_config(self, tile_id: str) -> TileConfig:
        """
        Get the configuration for a tile type.

        Args:
            tile_id: The identifier for the tile type

        Returns:
            TileConfig object with rendering information

        Raises:
            KeyError: If tile_id is not configured
        """
        if tile_id not in self.tiles:
            raise KeyError(f"❌ Tile '{tile_id}' is not configured. Available tiles: {list(self.tiles.keys())}")
        return self.tiles[tile_id]
    
    def get_available_tiles(self) -> Dict[str, TileConfig]:
        """Get all available tile configurations."""
        return self.tiles.copy()
    
    def reload_config(self):
        """Reload tile configurations from the file."""
        self.load_tiles()
    
    def add_tile_config(self, tile_id: str, config: TileConfig):
        """Add or update a tile configuration programmatically."""
        self.tiles[tile_id] = config
    
    def has_tile(self, tile_id: str) -> bool:
        """Check if a tile configuration exists."""
        return tile_id in self.tiles


# Global tile registry instance
_tile_registry: Optional[TileRegistry] = None


def get_tile_registry() -> TileRegistry:
    """Get the global tile registry instance."""
    global _tile_registry
    if _tile_registry is None:
        config_file = os.path.join("config", "tiles.toml")
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"❌ Tile configuration file not found: {config_file}")
        _tile_registry = TileRegistry(config_file)
    return _tile_registry


def reload_tile_config():
    """Reload the global tile configuration."""
    global _tile_registry
    if _tile_registry is not None:
        _tile_registry.reload_config()


# Convenience functions for common operations
def get_tile_config(tile_id: str) -> TileConfig:
    """Get tile configuration by ID."""
    return get_tile_registry().get_tile_config(tile_id)


def get_tile_character(tile_id: str) -> str:
    """Get the character for a tile type."""
    return get_tile_config(tile_id).character


def get_tile_colors(tile_id: str) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """Get the font and background colors for a tile type."""
    config = get_tile_config(tile_id)
    return config.font_color, config.background_color


# Example usage and testing
if __name__ == "__main__":
    # Test the tile registry
    registry = TileRegistry(os.path.join("config", "tiles.toml"))
    
    print("Available tiles:")
    for tile_id, config in registry.get_available_tiles().items():
        print(f"  {tile_id}: {config.name} ('{config.character}') "
              f"fg={config.font_color} bg={config.background_color}")
    
    # Test getting specific tiles
    stone_config = registry.get_tile_config('stone')
    print(f"\nStone tile: {stone_config}")
    
    # Test missing tile
    missing_config = registry.get_tile_config('nonexistent')
    print(f"Missing tile: {missing_config}")
    
    # Test convenience functions
    print(f"\nStone character: '{get_tile_character('stone')}'")
    print(f"Stone colors: {get_tile_colors('stone')}")
