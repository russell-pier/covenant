#!/usr/bin/env python3
"""
Game logic for 2D Minecraft-like World

Contains the core game state, rendering, and input handling logic.
Renders a tile-based world with pipeline generation.
"""

import time
import tcod
from ..generation import WorldGenerator
from ..graphics import GameRenderer
from ..utils import get_config
from .camera import Camera
from .input import InputHandler
try:
    from ..utils import profile_function, start_profiling, end_profiling, print_profiling_stats
except ImportError:
    # Fallback for when profiler is not available
    def profile_function(name=None):
        def decorator(func):
            return func
        return decorator
    def start_profiling(name): pass
    def end_profiling(name): pass
    def print_profiling_stats(): pass


class Game:
    """
    Main game class that manages the game state and coordinates all systems.
    """
    
    def __init__(self):
        """Initialize the game."""
        self.config = get_config()
        self.running = False
        self.world_manager = None
        self.renderer = None
        self.camera = None
        self.input_handler = None
        
        # Performance tracking
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.fps = 0
    
    def initialize(self):
        """Initialize all game systems."""
        print("🚀 STARTING INITIALIZE METHOD")

        # Initialize camera
        print("🔧 Initializing camera...")
        self.camera = Camera(self.config.camera)
        print("✅ Camera initialized successfully")

        # Initialize input handler
        print("🔧 Initializing input handler...")
        self.input_handler = InputHandler()
        print("✅ Input handler initialized successfully")

        # Initialize world manager
        print("🔧 About to initialize world manager...")
        print(f"Config world seed: {self.config.world.seed}")
        print(f"Config world chunk_size: {self.config.world.chunk_size}")
        print(f"Config world pipeline_layers: {self.config.world.pipeline_layers}")

        self.world_manager = WorldGenerator(
            seed=self.config.world.seed,
            chunk_size=self.config.world.chunk_size,
            pipeline_layers=self.config.world.pipeline_layers
        )
        print(f"✅ World manager initialized successfully: {self.world_manager}")

        # Initialize renderer
        print("🔧 Initializing renderer...")
        self.renderer = GameRenderer(self.config)
        print("✅ Renderer initialized successfully")

        print("🎉 INITIALIZE METHOD COMPLETED SUCCESSFULLY")
    
    def shutdown(self):
        """Shutdown all game systems."""
        print("Shutting down game systems...")

        if self.world_manager:
            self.world_manager.shutdown()

        if self.renderer:
            self.renderer.shutdown()

        print("Game systems shutdown complete.")
    
    @profile_function("game.main_loop")
    def run(self):
        """Main game loop."""
        self.running = True
        
        try:
            while self.running:
                start_time = time.time()
                
                # Handle events
                self.handle_events()
                
                # Update game state
                self.update()
                
                # Render frame
                self.render()
                
                # Update performance metrics
                self.update_performance_metrics(start_time)
                
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Exiting gracefully...")
        except Exception as e:
            print(f"An error occurred: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.running = False
    
    def handle_events(self):
        """Handle input events."""
        for event in tcod.event.wait(timeout=0.016):  # ~60 FPS
            if event.type == "QUIT":
                self.running = False
            elif event.type == "KEYDOWN":
                if self.input_handler.handle_keydown(event, self.camera):
                    # Camera moved, trigger world update
                    pass
    
    def update(self):
        """Update game state."""
        # Update world chunks based on camera position
        if self.world_manager and self.camera:
            screen_width = self.config.screen_width
            screen_height = self.config.screen_height
            self.world_manager.update_chunks(self.camera, screen_width, screen_height)
    
    @profile_function("game.render_frame")
    def render(self):
        """Render the current frame."""
        if self.renderer:
            self.renderer.render_frame(self.world_manager, self.camera)
    
    def update_performance_metrics(self, start_time):
        """Update FPS and performance tracking."""
        self.frame_count += 1
        
        # Calculate FPS every second
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.last_fps_time)
            self.frame_count = 0
            self.last_fps_time = current_time
        
        # Print profiling stats periodically
        if self.frame_count % 500 == 0:
            try:
                print_profiling_stats()
            except:
                pass


def run_game():
    """
    Main entry point for the game.
    
    Initializes and runs the game loop.
    """
    game = Game()
    
    try:
        game.initialize()
        print("Starting Covenant...")
        game.run()
    finally:
        game.shutdown()
        print("Application terminated.")
