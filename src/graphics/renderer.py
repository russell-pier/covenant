#!/usr/bin/env python3
"""
Main Game Renderer

Coordinates all rendering operations including world tiles, UI overlays, and effects.
"""

import tcod
from tcod import libtcodpy
from typing import Dict, Tuple, Optional, List
from .world_renderer import WorldRenderer
from .ui_renderer import EffectRenderer
from ..utils import get_tile_registry

try:
    from ..utils import profile_function, start_profiling, end_profiling
except ImportError:
    # Fallback for when profiler is not available
    def profile_function(name=None):
        def decorator(func):
            return func
        return decorator
    def start_profiling(name): pass
    def end_profiling(name): pass


class GameRenderer:
    """
    Main game renderer that coordinates all rendering systems.
    
    Manages the rendering pipeline including world rendering, UI rendering,
    and visual effects. Provides a unified interface for the game loop.
    """
    
    def __init__(self, config):
        """
        Initialize the game renderer.
        
        Args:
            config: Game configuration object
        """
        self.config = config
        
        # Initialize rendering subsystems
        self.world_renderer = WorldRenderer()
        self.effect_renderer = EffectRenderer()
        
        # Initialize TCOD console
        self.console = None
        self.context = None
        self._initialize_tcod()
        
        # Performance tracking
        self.frame_count = 0
        
    def _initialize_tcod(self):
        """Initialize TCOD console and context."""
        # Load font if specified
        if hasattr(self.config, 'font_path') and self.config.font_path:
            font_path = self.config.font_path
            libtcodpy.console_set_custom_font(
                font_path,
                libtcodpy.FONT_TYPE_GREYSCALE | libtcodpy.FONT_LAYOUT_TCOD,
                nb_char_horiz=16,
                nb_char_vertic=16
            )
        
        # Create console
        self.console = tcod.console.Console(
            self.config.screen_width,
            self.config.screen_height,
            order="F"
        )
        
        # Create context
        context_kwargs = {
            "columns": self.config.screen_width,
            "rows": self.config.screen_height,
            "title": "Covenant - 2D World Generator",
            "vsync": True
        }

        # Only add tileset if font_path is specified
        if hasattr(self.config, 'font_path') and self.config.font_path:
            context_kwargs["tileset"] = tcod.tileset.load_tilesheet(
                self.config.font_path, 16, 16, tcod.tileset.CHARMAP_CP437
            )

        self.context = tcod.context.new(**context_kwargs)
    
    @profile_function("renderer.render_frame")
    def render_frame(self, world_manager, camera):
        """
        Render a complete frame.
        
        Args:
            world_manager: World manager providing tile data
            camera: Camera for viewport calculations
        """
        start_profiling("renderer.render_frame")
        
        # Clear console
        self.console.clear()
        
        # Render world
        self.world_renderer.render_world(
            self.console, world_manager, camera,
            self.config.screen_width, self.config.screen_height
        )
        
        # Render effects
        self.effect_renderer.render_effects(self.console)
        
        # Render cursor highlight
        self.effect_renderer.render_cursor_highlight(
            self.console, self.config.screen_width, self.config.screen_height
        )
        
        # TODO: Add UI rendering when UI module is implemented
        
        # Present frame
        self.context.present(self.console, keep_aspect=True, integer_scaling=True)
        
        self.frame_count += 1
        end_profiling("renderer.render_frame")
    
    def shutdown(self):
        """Shutdown the renderer."""
        if self.context:
            self.context.close()
    
    def get_statistics(self) -> Dict:
        """Get renderer statistics."""
        return {
            'frames_rendered': self.frame_count,
            'screen_width': self.config.screen_width,
            'screen_height': self.config.screen_height
        }
