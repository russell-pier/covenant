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
    
    def __init__(self, config_file: str = "config/tiles.toml"):
        self.tiles: Dict[str, TileConfig] = {}
        self.config_file = config_file
        self._load_tiles()
    
    def _load_tiles(self):
        """Load tile configurations from TOML file."""
        if not os.path.exists(self.config_file):
            print(f"Warning: Tile configuration file {self.config_file} not found. Using defaults.")
            self._create_default_tiles()
            return
        
        try:
            with open(self.config_file, 'rb') as f:
                config_data = tomllib.load(f)
            
            # Load tiles from configuration (tiles are at root level)
            for tile_name, tile_data in config_data.items():
                try:
                    tile_config = TileConfig(
                        name=tile_name,
                        character=tile_data.get('character', '?'),
                        font_color=tuple(tile_data.get('font_color', [255, 255, 255])),
                        background_color=tuple(tile_data.get('background_color', [0, 0, 0]))
                    )
                    self.tiles[tile_name] = tile_config
                except Exception as e:
                    print(f"Error loading tile '{tile_name}': {e}")
            
            print(f"Loaded {len(self.tiles)} tile configurations from {self.config_file}")
            
        except Exception as e:
            print(f"Error loading tile configuration from {self.config_file}: {e}")
            self._create_default_tiles()
    
    def _create_default_tiles(self):
        """Create default tile configurations."""
        default_tiles = {
            'void': TileConfig('void', ' ', (0, 0, 0), (0, 0, 0)),
            'loading': TileConfig('loading', '?', (255, 255, 0), (64, 64, 64)),
            'water': TileConfig('water', '~', (100, 150, 255), (0, 50, 150)),
            'stone': TileConfig('stone', '█', (150, 150, 150), (100, 100, 100)),
            'grass': TileConfig('grass', '▓', (100, 200, 100), (50, 150, 50)),
            'sand': TileConfig('sand', '░', (255, 255, 150), (200, 200, 100)),
            'dirt': TileConfig('dirt', '▒', (139, 69, 19), (101, 67, 33)),
            'snow': TileConfig('snow', '▓', (255, 255, 255), (200, 200, 255)),
            'ice': TileConfig('ice', '█', (200, 255, 255), (150, 200, 255)),
            'lava': TileConfig('lava', '~', (255, 100, 0), (200, 0, 0)),
            'tree': TileConfig('tree', '♠', (0, 150, 0), (50, 100, 50)),
            'mountain': TileConfig('mountain', '▲', (100, 100, 100), (150, 150, 150))
        }
        
        self.tiles.update(default_tiles)
        print(f"Created {len(default_tiles)} default tile configurations")
    
    def get(self, tile_name: str, default: Optional[Dict] = None) -> Dict:
        """
        Get tile configuration as a dictionary.
        
        Args:
            tile_name: Name of the tile type
            default: Default configuration if tile not found
            
        Returns:
            Dictionary with tile configuration
        """
        if tile_name in self.tiles:
            tile_config = self.tiles[tile_name]
            return {
                'character': tile_config.character,
                'font_color': tile_config.font_color,
                'background_color': tile_config.background_color
            }
        
        if default is not None:
            return default
        
        # Return default unknown tile
        return {
            'character': '?',
            'font_color': (255, 0, 255),
            'background_color': (64, 0, 64)
        }
    
    def get_tile_config(self, tile_name: str) -> Optional[TileConfig]:
        """
        Get tile configuration object.
        
        Args:
            tile_name: Name of the tile type
            
        Returns:
            TileConfig object or None if not found
        """
        return self.tiles.get(tile_name)
    
    def register_tile(self, tile_config: TileConfig):
        """
        Register a new tile configuration.
        
        Args:
            tile_config: TileConfig object to register
        """
        self.tiles[tile_config.name] = tile_config
    
    def list_tiles(self) -> list:
        """Get list of all registered tile names."""
        return list(self.tiles.keys())
    
    def reload(self):
        """Reload tile configurations from file."""
        self.tiles.clear()
        self._load_tiles()


# Global tile registry instance
_tile_registry = None


def get_tile_registry() -> TileRegistry:
    """
    Get the global tile registry instance.
    
    Returns:
        TileRegistry instance
    """
    global _tile_registry
    if _tile_registry is None:
        _tile_registry = TileRegistry()
    return _tile_registry


def reload_tile_registry():
    """Reload the global tile registry."""
    global _tile_registry
    if _tile_registry is not None:
        _tile_registry.reload()
    else:
        _tile_registry = TileRegistry()
