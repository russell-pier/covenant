#!/usr/bin/env python3
"""
Configuration system for the 2D Minecraft-like world

Handles loading application settings from TOML configuration files.
"""

import os
from typing import Dict, Any, Tuple
from dataclasses import dataclass

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback for older Python versions


@dataclass
class ApplicationConfig:
    """Application-level configuration."""
    title: str = "2D Minecraft World - Spiral Generation"
    version: str = "0.1.0"


@dataclass
class WindowConfig:
    """Window and display configuration."""
    initial_width: int = 80
    initial_height: int = 50
    vsync: bool = True
    font_path: str = ""  # Empty by default - use system font


@dataclass
class CameraConfig:
    """Camera movement and positioning configuration."""
    initial_x: int = 0
    initial_y: int = 0
    move_speed: int = 1
    fast_move_speed: int = 5


@dataclass
class WorldConfig:
    """World generation configuration."""
    # Core world settings
    seed: int = 12345
    chunk_size: int = 32
    render_chunk_size: int = 64
    generation_cache_limit: int = 200
    
    # Pipeline configuration
    generator_type: str = "pipeline"
    pipeline_layers: list = None
    layer_configs: dict = None
    
    # Async world management
    render_distance: int = 3
    chunk_cache_limit: int = 100
    chunk_unload_distance: int = 5
    
    def __post_init__(self):
        """Initialize default values."""
        if self.pipeline_layers is None:
            self.pipeline_layers = ["lands_and_seas", "zoom"]
        if self.layer_configs is None:
            self.layer_configs = {}


@dataclass
class GameConfig:
    """Main game configuration combining all subsystems."""
    app: ApplicationConfig
    window: WindowConfig
    camera: CameraConfig
    world: WorldConfig
    
    # Convenience properties
    @property
    def screen_width(self) -> int:
        return self.window.initial_width
    
    @property
    def screen_height(self) -> int:
        return self.window.initial_height
    
    @property
    def font_path(self) -> str:
        return self.window.font_path


def load_config(config_path: str = "config/game.toml") -> Dict[str, Any]:
    """
    Load configuration from a TOML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration data
    """
    if not os.path.exists(config_path):
        print(f"Warning: Configuration file {config_path} not found. Using defaults.")
        return {}
    
    try:
        with open(config_path, 'rb') as f:
            config_data = tomllib.load(f)
        return config_data
    except Exception as e:
        print(f"Error loading configuration from {config_path}: {e}")
        return {}


def load_world_config(config_path: str = "config/world.toml") -> Dict[str, Any]:
    """
    Load world configuration from a TOML file.
    
    Args:
        config_path: Path to the world configuration file
        
    Returns:
        Dictionary containing world configuration data
    """
    if not os.path.exists(config_path):
        print(f"Warning: World configuration file {config_path} not found. Using defaults.")
        return {}
    
    try:
        with open(config_path, 'rb') as f:
            config_data = tomllib.load(f)
        return config_data
    except Exception as e:
        print(f"Error loading world configuration from {config_path}: {e}")
        return {}


def get_config() -> GameConfig:
    """
    Get the complete game configuration.
    
    Returns:
        GameConfig object with all settings
    """
    # Load main configuration
    config_data = load_config()
    
    # Load world configuration
    world_data = load_world_config()
    
    # Create configuration objects
    app_config = ApplicationConfig(
        title=config_data.get('app', {}).get('title', "Covenant - 2D World Generator"),
        version=config_data.get('app', {}).get('version', "0.1.0")
    )
    
    window_config = WindowConfig(
        initial_width=config_data.get('window', {}).get('width', 80),
        initial_height=config_data.get('window', {}).get('height', 50),
        vsync=config_data.get('window', {}).get('vsync', True),
        font_path=config_data.get('window', {}).get('font_path', "")  # Empty by default
    )
    
    camera_config = CameraConfig(
        initial_x=config_data.get('camera', {}).get('initial_x', 0),
        initial_y=config_data.get('camera', {}).get('initial_y', 0),
        move_speed=config_data.get('camera', {}).get('move_speed', 1),
        fast_move_speed=config_data.get('camera', {}).get('fast_move_speed', 5)
    )
    
    world_config = WorldConfig(
        seed=world_data.get('world', {}).get('seed', 12345),
        chunk_size=world_data.get('world', {}).get('chunk_size', 32),
        render_chunk_size=world_data.get('world', {}).get('render_chunk_size', 64),
        generation_cache_limit=world_data.get('world', {}).get('generation_cache_limit', 200),
        generator_type=world_data.get('world', {}).get('generator_type', "pipeline"),
        pipeline_layers=world_data.get('world', {}).get('pipeline_layers', ["lands_and_seas", "zoom"]),
        layer_configs=world_data.get('layers', {}),
        render_distance=world_data.get('world', {}).get('render_distance', 3),
        chunk_cache_limit=world_data.get('world', {}).get('chunk_cache_limit', 100),
        chunk_unload_distance=world_data.get('world', {}).get('chunk_unload_distance', 5)
    )
    
    return GameConfig(
        app=app_config,
        window=window_config,
        camera=camera_config,
        world=world_config
    )
