#!/usr/bin/env python3
"""
Spiral world generator for 2D Minecraft-like game

Generates tiles in a counter-clockwise spiral pattern.
"""

from typing import List, Tuple, Dict


class Tile:
    """Represents a single tile in the world."""

    def __init__(self, x: int, y: int, tile_type: str = "stone"):
        self.x = x
        self.y = y
        self.tile_type = tile_type  # This is now just the tile ID for lookup


class SpiralGenerator:
    """Generates tiles in a counter-clockwise spiral pattern."""
    
    def __init__(self):
        self.tiles: Dict[Tuple[int, int], Tile] = {}
    
    def generate_spiral(self, center_x: int, center_y: int, max_radius: int) -> Dict[Tuple[int, int], Tile]:
        """
        Generate tiles in a counter-clockwise spiral starting from the center.

        Args:
            center_x: X coordinate of the spiral center
            center_y: Y coordinate of the spiral center
            max_radius: Maximum radius to generate tiles to

        Returns:
            Dictionary mapping (x, y) coordinates to Tile objects
        """
        self.tiles.clear()

        # Start at the center
        x, y = center_x, center_y
        self.tiles[(x, y)] = Tile(x, y, "center_marker")

        # Simple approach: fill the entire rectangular area in a spiral pattern
        # Direction vectors: right, up, left, down (counter-clockwise)
        dx = [1, 0, -1, 0]
        dy = [0, -1, 0, 1]
        direction = 0  # Start moving right

        steps_in_direction = 1
        steps_taken = 0
        direction_changes = 0

        while abs(x - center_x) <= max_radius or abs(y - center_y) <= max_radius:
            # Move one step in current direction
            x += dx[direction]
            y += dy[direction]

            # Add tile if within bounds
            if abs(x - center_x) <= max_radius and abs(y - center_y) <= max_radius:
                self.tiles[(x, y)] = Tile(x, y, "stone")

            steps_taken += 1

            # Check if we need to change direction
            if steps_taken == steps_in_direction:
                direction = (direction + 1) % 4  # Turn counter-clockwise
                direction_changes += 1
                steps_taken = 0

                # Increase steps every two direction changes
                if direction_changes % 2 == 0:
                    steps_in_direction += 1

            # Safety check to prevent infinite loops
            if abs(x - center_x) > max_radius + 5 and abs(y - center_y) > max_radius + 5:
                break

        return self.tiles
    
    def get_tile(self, x: int, y: int) -> Tile:
        """Get a tile at the specified coordinates, or return a default tile if none exists."""
        return self.tiles.get((x, y), Tile(x, y, "void"))
    
    def get_tiles_in_bounds(self, min_x: int, min_y: int, max_x: int, max_y: int) -> List[Tile]:
        """Get all tiles within the specified bounds."""
        tiles_in_bounds = []
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                if (x, y) in self.tiles:
                    tiles_in_bounds.append(self.tiles[(x, y)])
        return tiles_in_bounds


class WorldGenerator:
    """Main world generator that can use different generation strategies."""

    def __init__(self, generator_type: str = "spiral", seed: int = None, chunk_size: int = 32,
                 pipeline_layers: list = None, layer_configs: dict = None, visualize: bool = False):
        """
        Initialize the world generator.

        Args:
            generator_type: Type of generator to use ("spiral" or "pipeline")
            seed: Random seed for generation
            chunk_size: Size of each chunk in tiles
            pipeline_layers: List of pipeline layers to use
            layer_configs: Configuration for each layer
            visualize: Whether to show visualization between layers
        """
        self.spiral_generator = SpiralGenerator()

        if generator_type == "pipeline":
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
        else:
            self.current_generator = self.spiral_generator
            self.generator_type = "spiral"

    def generate_world(self, center_x: int, center_y: int, radius: int) -> Dict[Tuple[int, int], Tile]:
        """Generate a world using the current generator."""
        if self.generator_type == "spiral":
            return self.spiral_generator.generate_spiral(center_x, center_y, radius)
        else:
            # For chunk generator, pre-load tiles in the radius area
            tiles = {}
            for x in range(center_x - radius, center_x + radius + 1):
                for y in range(center_y - radius, center_y + radius + 1):
                    tile = self.current_generator.get_tile(x, y)
                    tiles[(x, y)] = tile
            return tiles

    def generate_for_view(self, center_x: int, center_y: int, view_width: int, view_height: int):
        """Generate tiles specifically for a view area, ensuring full coverage."""
        half_width = view_width // 2
        half_height = view_height // 2

        if self.generator_type == "spiral":
            # Calculate the radius needed to cover the entire view
            radius = max(half_width, half_height) + 2

            # Generate the spiral
            self.spiral_generator.generate_spiral(center_x, center_y, radius)

            # Fill any gaps by ensuring every position in the view has a tile
            for x in range(center_x - half_width, center_x + half_width + 1):
                for y in range(center_y - half_height, center_y + half_height + 1):
                    if (x, y) not in self.spiral_generator.tiles:
                        # Add a stone tile if missing
                        self.spiral_generator.tiles[(x, y)] = Tile(x, y, "stone")
        else:
            # For chunk generator, just ensure tiles are loaded for the view area
            # The chunk generator handles this automatically when tiles are requested
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
    # Test the spiral generator
    generator = WorldGenerator()
    tiles = generator.generate_world(0, 0, 10)
    
    print(f"Generated {len(tiles)} tiles in a spiral pattern")
    
    # Print a small section to visualize
    for y in range(-5, 6):
        line = ""
        for x in range(-5, 6):
            tile = generator.get_tile(x, y)
            if tile.tile_type in ["stone", "center_marker"]:
                line += "█"
            else:
                line += " "
        print(line)
