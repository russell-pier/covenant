"""
World Generation System

Contains the generation pipeline, layers, and algorithms.
"""

from typing import Dict, Tuple, Optional, List, Any
from .pipeline import WorldGenerationPipeline, GenerationData
from .world import WorldTier


class Tile:
    """Simple tile representation."""
    def __init__(self, x: int, y: int, tile_type: str = "stone"):
        self.x = x
        self.y = y
        self.tile_type = tile_type


class PipelineWorldGenerator:
    """
    Pipeline-based world generator that uses the generation pipeline system.
    """

    def __init__(self, seed: int = None, chunk_size: int = 32,
                 pipeline_layers: List[str] = None, layer_configs: Dict[str, Any] = None,
                 visualize: bool = False):
        """
        Initialize the pipeline world generator.

        Args:
            seed: Random seed for generation
            chunk_size: Size of chunks for generation
            pipeline_layers: List of layer names to use in the pipeline
            layer_configs: Configuration for each layer
            visualize: Whether to enable visualization between layers
        """

        self.seed = seed if seed is not None else 12345
        self.chunk_size = chunk_size
        self.pipeline_layers = pipeline_layers or ["lands_and_seas"]
        self.layer_configs = layer_configs or {}
        self.visualize = visualize

        # Create the generation pipeline
        self.pipeline = WorldGenerationPipeline(self.seed, self.chunk_size)

        # Set up world tier with configured layers
        layer_configs_list = [(layer_name, self.layer_configs.get(layer_name, {}))
                             for layer_name in self.pipeline_layers]
        world_tier = WorldTier.create_custom_pipeline(layer_configs_list, visualize=self.visualize)
        self.pipeline.set_world_tier(world_tier)

        # Cache for generated tiles
        self._tile_cache: Dict[Tuple[int, int], Tile] = {}

    def get_tile(self, x: int, y: int) -> Tile:
        """
        Get a tile at the specified coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Tile at the specified coordinates
        """
        # Check cache first
        if (x, y) in self._tile_cache:
            return self._tile_cache[(x, y)]

        # Determine which chunk this tile belongs to
        chunk_x = x // self.chunk_size
        chunk_y = y // self.chunk_size

        # Generate the chunk if needed
        chunk_bounds = (chunk_x, chunk_y, chunk_x + 1, chunk_y + 1)
        generation_data = self.pipeline.generate_chunks(chunk_bounds)

        # Extract tile from generation data
        local_x = x % self.chunk_size
        local_y = y % self.chunk_size

        chunk_key = (chunk_x, chunk_y)
        if chunk_key in generation_data.chunks:
            chunk_data = generation_data.chunks[chunk_key]
            if local_y < len(chunk_data) and local_x < len(chunk_data[local_y]):
                tile_type = chunk_data[local_y][local_x]
                tile = Tile(x, y, tile_type)
                self._tile_cache[(x, y)] = tile
                return tile

        # Fallback to stone if no data available
        tile = Tile(x, y, "stone")
        self._tile_cache[(x, y)] = tile
        return tile

    def update_chunks(self, camera, screen_width: int = 80, screen_height: int = 50):
        """Update chunks around the camera position (placeholder)."""
        # This is a placeholder - in a real implementation this would
        # manage chunk loading/unloading based on camera position
        pass

    def shutdown(self):
        """Shutdown the world generator (placeholder)."""
        # This is a placeholder - in a real implementation this would
        # clean up resources, stop worker threads, etc.
        pass


# For backward compatibility, alias the pipeline generator as WorldGenerator
WorldGenerator = PipelineWorldGenerator

__all__ = [
    "Tile",
    "WorldGenerator",
    "PipelineWorldGenerator"
]
