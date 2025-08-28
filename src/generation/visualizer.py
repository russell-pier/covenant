#!/usr/bin/env python3
"""
On-screen visualization for the generation pipeline.

Shows layer-by-layer progression in the game window instead of console.
"""

import time
import tcod
from typing import Dict, Any, Tuple
from ..generation.pipeline import GenerationData


class PipelineVisualizer:
    """
    Visualizes generation pipeline progression on screen.
    """
    
    def __init__(self, console: tcod.Console):
        self.console = console
        self.width = console.width
        self.height = console.height
    
    def visualize_layer_progression(self, data: GenerationData, layer_name: str, delay: float = 1.0):
        """
        Visualize the result of a layer on screen.
        
        Args:
            data: Generation data after layer processing
            layer_name: Name of the layer that was processed
            delay: Delay in seconds before continuing
        """
        # Clear the console
        self.console.clear()
        
        # Draw title
        title = f"Layer: {layer_name}"
        self.console.print(self.width // 2 - len(title) // 2, 1, title, fg=tcod.white)
        
        # Analyze the data
        if not data.chunks:
            self.console.print(2, 3, "No chunks generated", fg=tcod.red)
            tcod.console_flush()
            time.sleep(delay)
            return
        
        land_count = sum(1 for chunk in data.chunks.values() if chunk.get('land_type') == 'land')
        water_count = len(data.chunks) - land_count
        land_ratio = land_count / (land_count + water_count) if (land_count + water_count) > 0 else 0
        
        # Display stats
        stats = f"Chunks: {len(data.chunks)}, Land: {land_count}, Water: {water_count} ({land_ratio:.1%})"
        self.console.print(2, 3, stats, fg=tcod.yellow)
        
        # Draw the terrain grid
        self._draw_terrain_grid(data, start_y=5)
        
        # Show processed layers
        layers_text = f"Processed: {', '.join(data.processed_layers)}"
        self.console.print(2, self.height - 2, layers_text, fg=tcod.light_gray)
        
        # Flush and wait
        tcod.console_flush()
        time.sleep(delay)
    
    def _draw_terrain_grid(self, data: GenerationData, start_y: int = 5):
        """
        Draw a visual representation of the terrain.
        
        Args:
            data: Generation data to visualize
            start_y: Y position to start drawing the grid
        """
        if not data.chunks:
            return
        
        # Find bounds of the generated chunks
        chunk_coords = list(data.chunks.keys())
        min_x = min(x for x, y in chunk_coords)
        max_x = max(x for x, y in chunk_coords)
        min_y = min(y for x, y in chunk_coords)
        max_y = max(y for x, y in chunk_coords)
        
        # Calculate grid size and scaling
        grid_width = max_x - min_x + 1
        grid_height = max_y - min_y + 1
        
        # Scale to fit on screen
        max_display_width = self.width - 4
        max_display_height = self.height - start_y - 3
        
        scale_x = max(1, grid_width // max_display_width + 1)
        scale_y = max(1, grid_height // max_display_height + 1)
        scale = max(scale_x, scale_y)
        
        # Draw the grid
        for chunk_y in range(min_y, max_y + 1, scale):
            for chunk_x in range(min_x, max_x + 1, scale):
                # Sample the area to determine dominant terrain
                land_samples = 0
                total_samples = 0
                
                for sy in range(chunk_y, min(chunk_y + scale, max_y + 1)):
                    for sx in range(chunk_x, min(chunk_x + scale, max_x + 1)):
                        chunk_key = (sx, sy)
                        if chunk_key in data.chunks:
                            total_samples += 1
                            if data.chunks[chunk_key].get('land_type') == 'land':
                                land_samples += 1
                
                # Determine display character and color
                if total_samples == 0:
                    continue
                
                land_ratio = land_samples / total_samples
                
                screen_x = 2 + (chunk_x - min_x) // scale
                screen_y = start_y + (max_y - chunk_y) // scale
                
                if screen_x >= self.width - 1 or screen_y >= self.height - 1:
                    continue
                
                if land_ratio > 0.7:
                    # Mostly land
                    self.console.print(screen_x, screen_y, "█", fg=tcod.light_gray, bg=tcod.dark_gray)
                elif land_ratio > 0.3:
                    # Mixed
                    self.console.print(screen_x, screen_y, "▓", fg=tcod.gray, bg=tcod.dark_blue)
                else:
                    # Mostly water
                    self.console.print(screen_x, screen_y, "~", fg=tcod.light_blue, bg=tcod.dark_blue)


def run_single_layer_demo():
    """
    Run a single demonstration of each layer with on-screen visualization.
    """
    from ..generation.pipeline import WorldGenerationPipeline
    from ..generation.world import WorldTier
    from ..config import get_config
    
    # Initialize display
    tcod.console_set_custom_font("arial10x10.png", tcod.FONT_TYPE_GREYSCALE | tcod.FONT_LAYOUT_TCOD)
    console = tcod.console_init_root(80, 50, "Pipeline Visualization", False)
    
    config = get_config()
    visualizer = PipelineVisualizer(console)
    
    # Create pipeline layers
    layer_configs = [
        ('lands_and_seas', config.layer_configs.get('lands_and_seas', {})),
        ('zoom', config.layer_configs.get('zoom', {})),
        ('zoom', config.layer_configs.get('zoom', {}))
    ]
    
    # Run each layer individually
    pipeline = WorldGenerationPipeline(config.world.seed, config.world.chunk_size)
    bounds = (0, 0, 1, 1)  # 2x2 chunk area
    
    # Initialize data
    from ..generation.pipeline import GenerationData
    data = GenerationData(seed=config.world.seed, chunk_size=config.world.chunk_size)
    
    for layer_name, layer_config in layer_configs:
        # Create and run single layer
        if layer_name == 'lands_and_seas':
            from ..generation.world.lands_and_seas import LandsAndSeasLayer
            layer = LandsAndSeasLayer(layer_config)
        elif layer_name == 'zoom':
            from ..generation.world.zoom import ZoomLayer
            layer = ZoomLayer(layer_config)
        else:
            continue
        
        # Process the layer
        data = layer.process(data, bounds)
        
        # Visualize the result
        visualizer.visualize_layer_progression(data, layer_name, delay=3.0)
        
        # Wait for user input to continue
        console.clear()
        console.print(console.width // 2 - 10, console.height // 2, "Press any key to continue...", fg=tcod.white)
        tcod.console_flush()
        
        while True:
            for event in tcod.event.wait():
                if isinstance(event, tcod.event.KeyDown):
                    break
            else:
                continue
            break
    
    # Final result
    console.clear()
    console.print(console.width // 2 - 8, console.height // 2, "Pipeline Complete!", fg=tcod.green)
    tcod.console_flush()
    time.sleep(2)
    
    tcod.console_delete(None)
