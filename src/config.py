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
    title: str
    version: str


@dataclass
class WindowConfig:
    """Window and display configuration."""
    initial_width: int
    initial_height: int
    vsync: bool


@dataclass
class WorldConfig:
    """World generation configuration."""
    center_x: int
    center_y: int
    radius: int
    generator_type: str
    seed: int
    chunk_size: int
    pipeline_layers: list
    layer_configs: dict
    # Infinite world settings
    render_distance: int
    chunk_cache_limit: int
    chunk_unload_distance: int


@dataclass
class CameraConfig:
    """Camera and viewport configuration."""
    initial_x: int
    initial_y: int
    move_speed: int
    fast_move_speed: int


@dataclass
class DebugConfig:
    """Debug display configuration."""
    show_debug_on_startup: bool
    show_coordinates_on_startup: bool
    show_fps_on_startup: bool


@dataclass
class RenderingConfig:
    """Rendering system configuration."""
    seamless_blocks_enabled: bool
    clear_color: Tuple[int, int, int]


@dataclass
class UIConfig:
    """User interface configuration."""
    panel_background: Tuple[int, int, int]
    border_color: Tuple[int, int, int]
    info_color: Tuple[int, int, int]
    warning_color: Tuple[int, int, int]
    debug_color: Tuple[int, int, int]
    top_panel_max_lines: int
    bottom_panel_max_lines: int
    panel_margin: int


@dataclass
class GameConfig:
    """Complete game configuration."""
    application: ApplicationConfig
    window: WindowConfig
    world: WorldConfig
    camera: CameraConfig
    debug: DebugConfig
    rendering: RenderingConfig
    ui: UIConfig


class ConfigLoader:
    """Loads and manages game configuration."""
    
    def __init__(self, config_file: str = "config/config.toml"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> GameConfig:
        """Load configuration from TOML file - fails if missing or invalid."""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"❌ Configuration file not found: {self.config_file}")

        try:
            with open(self.config_file, 'rb') as f:
                config_data = tomllib.load(f)

            return self._parse_config(config_data)

        except Exception as e:
            raise RuntimeError(f"❌ Failed to load configuration from {self.config_file}: {e}")
    
    def _parse_config(self, config_data: Dict[str, Any]) -> GameConfig:
        """Parse configuration data into structured config objects."""

        # Application config - required
        if 'application' not in config_data:
            raise KeyError("❌ Missing required 'application' section in configuration")
        app_data = config_data['application']
        if 'title' not in app_data:
            raise KeyError("❌ Missing required 'application.title' in configuration")
        if 'version' not in app_data:
            raise KeyError("❌ Missing required 'application.version' in configuration")
        application = ApplicationConfig(
            title=app_data['title'],
            version=app_data['version']
        )

        # Window config - required
        if 'window' not in config_data:
            raise KeyError("❌ Missing required 'window' section in configuration")
        window_data = config_data['window']
        if 'initial_width' not in window_data:
            raise KeyError("❌ Missing required 'window.initial_width' in configuration")
        if 'initial_height' not in window_data:
            raise KeyError("❌ Missing required 'window.initial_height' in configuration")
        if 'vsync' not in window_data:
            raise KeyError("❌ Missing required 'window.vsync' in configuration")
        window = WindowConfig(
            initial_width=window_data['initial_width'],
            initial_height=window_data['initial_height'],
            vsync=window_data['vsync']
        )

        # World config - required
        if 'world' not in config_data:
            raise KeyError("❌ Missing required 'world' section in configuration")
        world_data = config_data['world']

        # Extract pipeline layers and layer configs - required
        if 'pipeline_layers' not in world_data:
            raise KeyError("❌ Missing required 'world.pipeline_layers' in configuration")
        pipeline_layers = world_data['pipeline_layers']
        if not pipeline_layers:
            raise ValueError("❌ 'world.pipeline_layers' cannot be empty")
        layer_configs = {}

        # Extract layer-specific configurations - all must be present
        for layer_name in pipeline_layers:
            if layer_name not in world_data:
                raise KeyError(f"❌ Missing required configuration for layer '{layer_name}' in world config")
            layer_configs[layer_name] = world_data[layer_name]

        # World config validation
        required_world_keys = ['center_x', 'center_y', 'radius', 'generator_type', 'seed', 'chunk_size', 'render_distance', 'chunk_cache_limit', 'chunk_unload_distance']
        for key in required_world_keys:
            if key not in world_data:
                raise KeyError(f"❌ Missing required 'world.{key}' in configuration")

        world = WorldConfig(
            center_x=world_data['center_x'],
            center_y=world_data['center_y'],
            radius=world_data['radius'],
            generator_type=world_data['generator_type'],
            seed=world_data['seed'],
            chunk_size=world_data['chunk_size'],
            pipeline_layers=pipeline_layers,
            layer_configs=layer_configs,
            render_distance=world_data['render_distance'],
            chunk_cache_limit=world_data['chunk_cache_limit'],
            chunk_unload_distance=world_data['chunk_unload_distance']
        )

        # Camera config - required
        if 'camera' not in config_data:
            raise KeyError("❌ Missing required 'camera' section in configuration")
        camera_data = config_data['camera']
        required_camera_keys = ['initial_x', 'initial_y', 'move_speed', 'fast_move_speed']
        for key in required_camera_keys:
            if key not in camera_data:
                raise KeyError(f"❌ Missing required 'camera.{key}' in configuration")
        camera = CameraConfig(
            initial_x=camera_data['initial_x'],
            initial_y=camera_data['initial_y'],
            move_speed=camera_data['move_speed'],
            fast_move_speed=camera_data['fast_move_speed']
        )
        
        # Debug config - required
        if 'debug' not in config_data:
            raise KeyError("❌ Missing required 'debug' section in configuration")
        debug_data = config_data['debug']
        required_debug_keys = ['show_debug_on_startup', 'show_coordinates_on_startup', 'show_fps_on_startup']
        for key in required_debug_keys:
            if key not in debug_data:
                raise KeyError(f"❌ Missing required 'debug.{key}' in configuration")
        debug = DebugConfig(
            show_debug_on_startup=debug_data['show_debug_on_startup'],
            show_coordinates_on_startup=debug_data['show_coordinates_on_startup'],
            show_fps_on_startup=debug_data['show_fps_on_startup']
        )
        
        # Rendering config - required
        if 'rendering' not in config_data:
            raise KeyError("❌ Missing required 'rendering' section in configuration")
        rendering_data = config_data['rendering']
        required_rendering_keys = ['seamless_blocks_enabled', 'clear_color']
        for key in required_rendering_keys:
            if key not in rendering_data:
                raise KeyError(f"❌ Missing required 'rendering.{key}' in configuration")
        rendering = RenderingConfig(
            seamless_blocks_enabled=rendering_data['seamless_blocks_enabled'],
            clear_color=tuple(rendering_data['clear_color'])
        )
        
        # UI config - required
        if 'ui' not in config_data:
            raise KeyError("❌ Missing required 'ui' section in configuration")
        ui_data = config_data['ui']
        required_ui_keys = ['panel_background', 'border_color', 'info_color', 'warning_color', 'debug_color', 'top_panel_max_lines', 'bottom_panel_max_lines', 'panel_margin']
        for key in required_ui_keys:
            if key not in ui_data:
                raise KeyError(f"❌ Missing required 'ui.{key}' in configuration")
        ui = UIConfig(
            panel_background=tuple(ui_data['panel_background']),
            border_color=tuple(ui_data['border_color']),
            info_color=tuple(ui_data['info_color']),
            warning_color=tuple(ui_data['warning_color']),
            debug_color=tuple(ui_data['debug_color']),
            top_panel_max_lines=ui_data['top_panel_max_lines'],
            bottom_panel_max_lines=ui_data['bottom_panel_max_lines'],
            panel_margin=ui_data['panel_margin']
        )
        
        return GameConfig(
            application=application,
            window=window,
            world=world,
            camera=camera,
            debug=debug,
            rendering=rendering,
            ui=ui
        )
    

    
    def reload_config(self):
        """Reload configuration from file."""
        self.config = self.load_config()
    
    def get_config(self) -> GameConfig:
        """Get the current configuration."""
        return self.config


# Global configuration instance
_config_loader = None


def get_config() -> GameConfig:
    """Get the global configuration instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader.get_config()


def reload_config():
    """Reload the global configuration."""
    global _config_loader
    if _config_loader is not None:
        _config_loader.reload_config()


# Example usage and testing
if __name__ == "__main__":
    # Test the configuration system
    config = get_config()
    
    print("Configuration loaded:")
    print(f"  Application: {config.application.title} v{config.application.version}")
    print(f"  Window: {config.window.initial_width}x{config.window.initial_height}")
    print(f"  World center: ({config.world.center_x}, {config.world.center_y})")
    print(f"  Debug on startup: {config.debug.show_debug_on_startup}")
    print(f"  Seamless blocks: {config.rendering.seamless_blocks_enabled}")
    print(f"  Panel background: {config.ui.panel_background}")
