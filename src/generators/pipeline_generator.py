#!/usr/bin/env python3
"""
Pipeline-based world generator that replaces the legacy chunk generator.

This generator uses the new layered generation pipeline system for
highly configurable and extensible world generation.
"""

from typing import Dict, Tuple, Any, List
from .world_generator import Tile
from ..generation.pipeline import WorldGenerationPipeline
from ..generation.world import WorldTier


class PipelineWorldGenerator:
    """
    World generator using the new pipeline system.
    
    This replaces the old ChunkGenerator with a more flexible,
    layered approach to world generation.
    """
    
    def __init__(self, seed: int = None, chunk_size: int = 32, 
                 pipeline_layers: List[str] = None, layer_configs: Dict[str, Any] = None,
                 visualize: bool = False):
        """
        Initialize the pipeline-based world generator.
        
        Args:
            seed: Random seed for generation
            chunk_size: Size of each chunk in tiles
            pipeline_layers: List of layer names to use in the pipeline
            layer_configs: Configuration for each layer
            visualize: Whether to show visualization between layers
        """
        self.seed = seed if seed is not None else 12345
        self.chunk_size = chunk_size
        self.pipeline_layers = pipeline_layers or ["lands_and_seas"]
        self.layer_configs = layer_configs or {}
        self.visualize = visualize
        
        # Create the generation pipeline
        self.pipeline = WorldGenerationPipeline(self.seed, self.chunk_size)
        
        # Configure world tier with specified layers
        layer_config_tuples = []
        for layer_name in self.pipeline_layers:
            layer_config = self.layer_configs.get(layer_name, {})
            layer_config_tuples.append((layer_name, layer_config))
        
        world_tier = WorldTier.create_custom_pipeline(layer_config_tuples, visualize=self.visualize)
        self.pipeline.set_world_tier(world_tier)
        
        # Cache for generated chunks
        self._chunk_cache: Dict[Tuple[int, int], Dict[str, Any]] = {}
    
    def _world_to_chunk_coords(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Convert world coordinates to chunk coordinates, accounting for subdivision."""
        import math

        # Calculate the effective chunk size after all zoom layers
        effective_chunk_size = self.chunk_size
        zoom_count = sum(1 for layer_name in self.pipeline_layers if layer_name == "zoom")

        # Each zoom layer subdivides by factor of 2, reducing effective chunk size
        for _ in range(zoom_count):
            effective_chunk_size //= 2

        chunk_x = math.floor(world_x / effective_chunk_size)
        chunk_y = math.floor(world_y / effective_chunk_size)
        return chunk_x, chunk_y
    
    def _ensure_chunk_loaded(self, chunk_x: int, chunk_y: int):
        """Ensure a chunk is loaded, generating it if necessary."""
        chunk_key = (chunk_x, chunk_y)

        if chunk_key not in self._chunk_cache:
            # Generate a region of chunks around this chunk to improve efficiency
            # This prevents running the pipeline for every single chunk
            region_size = 4  # Generate 4x4 chunks at a time

            # Calculate region bounds
            # Note: region_size is in terms of BASE chunks, not subdivided chunks
            # Convert subdivided chunk coordinates back to base chunk coordinates
            zoom_count = sum(1 for layer_name in self.pipeline_layers if layer_name == "zoom")
            zoom_factor = 2 ** zoom_count  # Each zoom layer subdivides by 2

            # Convert subdivided chunk coordinates to base chunk coordinates
            base_chunk_x = chunk_x // zoom_factor
            base_chunk_y = chunk_y // zoom_factor

            # Calculate region bounds in base chunk coordinates
            region_min_x = (base_chunk_x // region_size) * region_size
            region_min_y = (base_chunk_y // region_size) * region_size
            region_max_x = region_min_x + region_size - 1
            region_max_y = region_min_y + region_size - 1

            bounds = (region_min_x, region_min_y, region_max_x, region_max_y)

            # Generate all chunks in this region
            data = self.pipeline.generate_chunks(bounds)

            # Cache all generated chunks, but prioritize subdivided chunks over base chunks
            # First, add all chunks to cache
            for chunk_coord, chunk_data in data.chunks.items():
                if chunk_coord not in self._chunk_cache:
                    self._chunk_cache[chunk_coord] = chunk_data

            # Then, if we have zoom layers, ensure subdivided chunks take priority
            if any(layer_name == "zoom" for layer_name in self.pipeline_layers):
                # Find the highest subdivision level
                max_subdivision_level = 0
                for chunk_data in data.chunks.values():
                    level = chunk_data.get('subdivision_level', 0)
                    max_subdivision_level = max(max_subdivision_level, level)

                # Remove any chunks that have a lower subdivision level than the maximum
                # This ensures only the most subdivided chunks remain
                if max_subdivision_level > 0:
                    coords_to_remove = []
                    for chunk_coord, chunk_data in self._chunk_cache.items():
                        level = chunk_data.get('subdivision_level', 0)
                        if level < max_subdivision_level:
                            coords_to_remove.append(chunk_coord)

                    for coord in coords_to_remove:
                        del self._chunk_cache[coord]
    
    def get_tile(self, world_x: int, world_y: int) -> Tile:
        """Get a tile at the specified world coordinates."""
        # First, ensure we have chunks loaded for this area
        base_chunk_x, base_chunk_y = self._world_to_chunk_coords(world_x, world_y)
        self._ensure_chunk_loaded(base_chunk_x, base_chunk_y)

        # Now find the actual subdivided chunk that contains this world position
        # The zoom layers may have created many small chunks from the original chunk
        tile_type = 'water'  # Default

        # Look through all cached chunks to find the one containing this world position
        for chunk_coord, chunk_data in self._chunk_cache.items():
            chunk_x, chunk_y = chunk_coord
            chunk_size = chunk_data.get('chunk_size', self.chunk_size)

            # Calculate world bounds for this chunk
            start_x = chunk_x * chunk_size
            start_y = chunk_y * chunk_size
            end_x = start_x + chunk_size - 1
            end_y = start_y + chunk_size - 1

            # Check if this world position is within this chunk
            if start_x <= world_x <= end_x and start_y <= world_y <= end_y:
                land_type = chunk_data.get('land_type', 'water')
                tile_type = 'stone' if land_type == 'land' else 'water'
                break

        return Tile(world_x, world_y, tile_type)
    
    def get_tiles_in_bounds(self, min_x: int, min_y: int, max_x: int, max_y: int) -> list:
        """Get all tiles within the specified bounds."""
        tiles = []
        
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                tile = self.get_tile(x, y)
                tiles.append(tile)
        
        return tiles
    
    def get_chunk_info(self, world_x: int, world_y: int) -> Dict:
        """Get information about the chunk containing the given world position."""
        chunk_x, chunk_y = self._world_to_chunk_coords(world_x, world_y)
        self._ensure_chunk_loaded(chunk_x, chunk_y)
        
        chunk_data = self._chunk_cache[(chunk_x, chunk_y)]
        land_type = chunk_data.get('land_type', 'water')
        
        return {
            "chunk_x": chunk_x,
            "chunk_y": chunk_y,
            "chunk_type": land_type,
            "world_start_x": chunk_x * self.chunk_size,
            "world_start_y": chunk_y * self.chunk_size,
            "world_end_x": chunk_x * self.chunk_size + self.chunk_size - 1,
            "world_end_y": chunk_y * self.chunk_size + self.chunk_size - 1,
        }
    
    def get_loaded_chunks_count(self) -> int:
        """Get the number of currently loaded chunks."""
        return len(self._chunk_cache)
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """Get information about the generation pipeline."""
        world_tier = self.pipeline.world_tier
        if world_tier:
            layer_names = world_tier.get_layer_names()
        else:
            layer_names = []
        
        return {
            'seed': self.seed,
            'chunk_size': self.chunk_size,
            'pipeline_layers': self.pipeline_layers,
            'world_tier_layers': layer_names,
            'loaded_chunks': self.get_loaded_chunks_count(),
            'layer_configs': self.layer_configs
        }
    

