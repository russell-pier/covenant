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


@dataclass
class WorldConfig:
    """World generation configuration."""
    center_x: int = 0
    center_y: int = 0
    radius: int = 50
    generator_type: str = "pipeline"
    seed: int = 12345
    chunk_size: int = 64
    pipeline_layers: list = None
    layer_configs: dict = None
    # Infinite world settings
    render_distance: int = 3
    chunk_cache_limit: int = 100
    chunk_unload_distance: int = 5

    def __post_init__(self):
        if self.pipeline_layers is None:
            self.pipeline_layers = ["lands_and_seas"]
        if self.layer_configs is None:
            self.layer_configs = {}


@dataclass
class CameraConfig:
    """Camera and viewport configuration."""
    initial_x: int = 0
    initial_y: int = 0
    move_speed: int = 1
    fast_move_speed: int = 5


@dataclass
class DebugConfig:
    """Debug display configuration."""
    show_debug_on_startup: bool = False
    show_coordinates_on_startup: bool = False
    show_fps_on_startup: bool = False


@dataclass
class RenderingConfig:
    """Rendering system configuration."""
    seamless_blocks_enabled: bool = True
    clear_color: Tuple[int, int, int] = (0, 0, 0)


@dataclass
class UIConfig:
    """User interface configuration."""
    panel_background: Tuple[int, int, int] = (32, 32, 48)
    border_color: Tuple[int, int, int] = (128, 128, 160)
    info_color: Tuple[int, int, int] = (255, 255, 255)
    warning_color: Tuple[int, int, int] = (255, 255, 0)
    debug_color: Tuple[int, int, int] = (128, 255, 128)
    top_panel_max_lines: int = 2
    bottom_panel_max_lines: int = 3
    panel_margin: int = 2


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
    
    def __init__(self, config_file: str = "config.toml"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> GameConfig:
        """Load configuration from TOML file with fallback to defaults."""
        if not os.path.exists(self.config_file):
            print(f"Warning: Config file '{self.config_file}' not found. Using defaults.")
            return self._create_default_config()
        
        try:
            with open(self.config_file, 'rb') as f:
                config_data = tomllib.load(f)
            
            print(f"Loaded configuration from {self.config_file}")
            return self._parse_config(config_data)
            
        except Exception as e:
            print(f"Error loading config from '{self.config_file}': {e}")
            print("Using default configuration.")
            return self._create_default_config()
    
    def _parse_config(self, config_data: Dict[str, Any]) -> GameConfig:
        """Parse configuration data into structured config objects."""
        
        # Application config
        app_data = config_data.get('application', {})
        application = ApplicationConfig(
            title=app_data.get('title', ApplicationConfig.title),
            version=app_data.get('version', ApplicationConfig.version)
        )
        
        # Window config
        window_data = config_data.get('window', {})
        window = WindowConfig(
            initial_width=window_data.get('initial_width', WindowConfig.initial_width),
            initial_height=window_data.get('initial_height', WindowConfig.initial_height),
            vsync=window_data.get('vsync', WindowConfig.vsync)
        )
        
        # World config
        world_data = config_data.get('world', {})

        # Extract pipeline layers and layer configs
        pipeline_layers = world_data.get('pipeline_layers', ["lands_and_seas"])
        layer_configs = {}

        # Extract layer-specific configurations
        for layer_name in pipeline_layers:
            if layer_name in world_data:
                layer_configs[layer_name] = world_data[layer_name]

        world = WorldConfig(
            center_x=world_data.get('center_x', WorldConfig.center_x),
            center_y=world_data.get('center_y', WorldConfig.center_y),
            radius=world_data.get('radius', WorldConfig.radius),
            generator_type=world_data.get('generator_type', WorldConfig.generator_type),
            seed=world_data.get('seed', WorldConfig.seed),
            chunk_size=world_data.get('chunk_size', WorldConfig.chunk_size),
            pipeline_layers=pipeline_layers,
            layer_configs=layer_configs,
            render_distance=world_data.get('render_distance', WorldConfig.render_distance),
            chunk_cache_limit=world_data.get('chunk_cache_limit', WorldConfig.chunk_cache_limit),
            chunk_unload_distance=world_data.get('chunk_unload_distance', WorldConfig.chunk_unload_distance)
        )

        # Camera config
        camera_data = config_data.get('camera', {})
        camera = CameraConfig(
            initial_x=camera_data.get('initial_x', CameraConfig.initial_x),
            initial_y=camera_data.get('initial_y', CameraConfig.initial_y),
            move_speed=camera_data.get('move_speed', CameraConfig.move_speed),
            fast_move_speed=camera_data.get('fast_move_speed', CameraConfig.fast_move_speed)
        )
        
        # Debug config
        debug_data = config_data.get('debug', {})
        debug = DebugConfig(
            show_debug_on_startup=debug_data.get('show_debug_on_startup', DebugConfig.show_debug_on_startup),
            show_coordinates_on_startup=debug_data.get('show_coordinates_on_startup', DebugConfig.show_coordinates_on_startup),
            show_fps_on_startup=debug_data.get('show_fps_on_startup', DebugConfig.show_fps_on_startup)
        )
        
        # Rendering config
        rendering_data = config_data.get('rendering', {})
        rendering = RenderingConfig(
            seamless_blocks_enabled=rendering_data.get('seamless_blocks_enabled', RenderingConfig.seamless_blocks_enabled),
            clear_color=tuple(rendering_data.get('clear_color', RenderingConfig.clear_color))
        )
        
        # UI config
        ui_data = config_data.get('ui', {})
        ui = UIConfig(
            panel_background=tuple(ui_data.get('panel_background', UIConfig.panel_background)),
            border_color=tuple(ui_data.get('border_color', UIConfig.border_color)),
            info_color=tuple(ui_data.get('info_color', UIConfig.info_color)),
            warning_color=tuple(ui_data.get('warning_color', UIConfig.warning_color)),
            debug_color=tuple(ui_data.get('debug_color', UIConfig.debug_color)),
            top_panel_max_lines=ui_data.get('top_panel_max_lines', UIConfig.top_panel_max_lines),
            bottom_panel_max_lines=ui_data.get('bottom_panel_max_lines', UIConfig.bottom_panel_max_lines),
            panel_margin=ui_data.get('panel_margin', UIConfig.panel_margin)
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
    
    def _create_default_config(self) -> GameConfig:
        """Create default configuration."""
        return GameConfig(
            application=ApplicationConfig(),
            window=WindowConfig(),
            world=WorldConfig(),
            camera=CameraConfig(),
            debug=DebugConfig(),
            rendering=RenderingConfig(),
            ui=UIConfig()
        )
    
    def reload_config(self):
        """Reload configuration from file."""
        print("Reloading configuration...")
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
