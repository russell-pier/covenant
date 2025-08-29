#!/usr/bin/env python3
"""
World generator for 2D Minecraft-like game

Uses the pipeline generation system for terrain generation.
"""

from typing import List, Tuple, Dict


class Tile:
    """Represents a single tile in the world."""

    def __init__(self, x: int, y: int, tile_type: str = "stone"):
        self.x = x
        self.y = y
        self.tile_type = tile_type  # Tile type for rendering lookup


class WorldGenerator:
    """Main world generator using the pipeline system."""

    def __init__(self, generator_type: str = "pipeline", seed: int = None, chunk_size: int = 32,
                 pipeline_layers: list = None, layer_configs: dict = None, visualize: bool = False):
        """
        Initialize the world generator.

        Args:
            generator_type: Type of generator to use (only "pipeline" supported)
            seed: Random seed for generation
            chunk_size: Size of each chunk in tiles
            pipeline_layers: List of pipeline layers to use
            layer_configs: Configuration for each layer
            visualize: Whether to show visualization between layers
        """
        if generator_type != "pipeline":
            raise ValueError("Only 'pipeline' generator type is supported")
        
        from .pipeline_generator import PipelineWorldGenerator
        self.pipeline_generator = PipelineWorldGenerator(
            seed=seed,
            chunk_size=chunk_size,
            pipeline_layers=pipeline_layers,
            layer_configs=layer_configs,
            visualize=visualize
        )
        self.current_generator = self.pipeline_generator
        self.generator_type = "pipeline"

    def generate_world(self, center_x: int, center_y: int, radius: int) -> Dict[Tuple[int, int], Tile]:
        """Generate a world using the pipeline generator."""
        tiles = {}
        for x in range(center_x - radius, center_x + radius + 1):
            for y in range(center_y - radius, center_y + radius + 1):
                tile = self.current_generator.get_tile(x, y)
                tiles[(x, y)] = tile
        return tiles

    def generate_for_view(self, center_x: int, center_y: int, view_width: int, view_height: int):
        """Generate tiles specifically for a view area, ensuring full coverage."""
        # Pipeline generator handles this automatically when tiles are requested
        pass

    def get_tile(self, x: int, y: int) -> Tile:
        """Get a tile at the specified coordinates."""
        return self.current_generator.get_tile(x, y)

    def get_tiles_in_view(self, center_x: int, center_y: int, view_width: int, view_height: int) -> List[Tile]:
        """Get all tiles that should be visible in the current view."""
        half_width = view_width // 2
        half_height = view_height // 2

        min_x = center_x - half_width
        max_x = center_x + half_width
        min_y = center_y - half_height
        max_y = center_y + half_height

        return self.current_generator.get_tiles_in_bounds(min_x, min_y, max_x, max_y)


# Example usage and testing
if __name__ == "__main__":
    # Test the pipeline generator
    generator = WorldGenerator(
        generator_type="pipeline",
        seed=12345,
        chunk_size=16,
        pipeline_layers=["lands_and_seas", "zoom"],
        layer_configs={
            "lands_and_seas": {"land_ratio": 3},
            "zoom": {"subdivision_factor": 2}
        }
    )
    
    tiles = generator.generate_world(0, 0, 10)
    print(f"Generated {len(tiles)} tiles using pipeline system")
    
    # Print a small section to visualize
    for y in range(-5, 6):
        line = ""
        for x in range(-5, 6):
            tile = generator.get_tile(x, y)
            if tile.tile_type == "stone":
                line += "█"
            else:
                line += "~"
        print(line)
