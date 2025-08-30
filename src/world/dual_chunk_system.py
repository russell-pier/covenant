#!/usr/bin/env python3
"""
Dual Chunk System for Efficient World Generation and Rendering

Separates generation chunks (optimized for pipeline processing) from render chunks
(optimized for display and memory management). This provides the best of both worlds:
- Small generation chunks for efficient pipeline processing
- Large render chunks for efficient rendering and reduced management overhead
"""

import math
from typing import Dict, List, Tuple, Set, Any, Optional
from dataclasses import dataclass


@dataclass
class GenerationChunk:
    """
    Small chunks optimized for world generation pipeline processing.

    These chunks have dynamic sizes that depend on the pipeline layers:
    - lands_and_seas: 64x64 tiles
    - After 1 zoom: 32x32 tiles
    - After 2 zooms: 16x16 tiles
    - etc.
    """
    chunk_x: int
    chunk_y: int
    chunk_size: int  # Dynamic size based on pipeline stage
    tiles: Dict[Tuple[int, int], str]  # (world_x, world_y) -> tile_type
    metadata: Dict[str, Any]
    
    def get_world_bounds(self) -> Tuple[int, int, int, int]:
        """Get world coordinate bounds for this generation chunk."""
        min_x = self.chunk_x * self.chunk_size
        min_y = self.chunk_y * self.chunk_size
        max_x = min_x + self.chunk_size - 1
        max_y = min_y + self.chunk_size - 1
        return min_x, min_y, max_x, max_y


@dataclass
class RenderChunk:
    """
    Large chunks optimized for rendering and memory management.

    Fixed size of 64x64 tiles regardless of generation pipeline.
    Each render chunk aggregates multiple generation chunks.
    """
    chunk_x: int
    chunk_y: int
    generation_chunks: List[GenerationChunk]
    aggregated_tiles: Dict[Tuple[int, int], str]  # Cached tile lookup
    metadata: Dict[str, Any]
    chunk_size: int = 64  # Fixed size for rendering efficiency
    
    def get_world_bounds(self) -> Tuple[int, int, int, int]:
        """Get world coordinate bounds for this render chunk."""
        min_x = self.chunk_x * self.chunk_size
        min_y = self.chunk_y * self.chunk_size
        max_x = min_x + self.chunk_size - 1
        max_y = min_y + self.chunk_size - 1
        return min_x, min_y, max_x, max_y
    
    def get_tile(self, world_x: int, world_y: int) -> Optional[str]:
        """Get tile type at world coordinates."""
        return self.aggregated_tiles.get((world_x, world_y))


class DualChunkManager:
    """
    Manages the relationship between generation chunks and render chunks.
    
    Handles:
    - Converting between generation and render chunk coordinates
    - Aggregating generation chunks into render chunks
    - Efficient tile lookups across the dual system
    """
    
    def __init__(self, render_chunk_size: int = 64):
        """
        Initialize the dual chunk manager.
        
        Args:
            render_chunk_size: Size of render chunks in tiles (default: 64x64)
        """
        self.render_chunk_size = render_chunk_size
        
        # Cache for coordinate conversions
        self._coord_cache: Dict[Tuple[int, int, int], Tuple[int, int]] = {}
    
    def world_to_render_chunk(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Convert world coordinates to render chunk coordinates."""
        render_chunk_x = math.floor(world_x / self.render_chunk_size)
        render_chunk_y = math.floor(world_y / self.render_chunk_size)
        return render_chunk_x, render_chunk_y
    
    def world_to_generation_chunk(self, world_x: int, world_y: int, 
                                 generation_chunk_size: int) -> Tuple[int, int]:
        """Convert world coordinates to generation chunk coordinates."""
        cache_key = (world_x, world_y, generation_chunk_size)
        if cache_key in self._coord_cache:
            return self._coord_cache[cache_key]
        
        gen_chunk_x = math.floor(world_x / generation_chunk_size)
        gen_chunk_y = math.floor(world_y / generation_chunk_size)
        
        self._coord_cache[cache_key] = (gen_chunk_x, gen_chunk_y)
        return gen_chunk_x, gen_chunk_y
    
    def get_generation_chunks_for_render_chunk(self, render_chunk_x: int, render_chunk_y: int,
                                             generation_chunk_size: int) -> List[Tuple[int, int]]:
        """
        Get all generation chunk coordinates that overlap with a render chunk.
        
        Args:
            render_chunk_x: Render chunk X coordinate
            render_chunk_y: Render chunk Y coordinate
            generation_chunk_size: Size of generation chunks
            
        Returns:
            List of (gen_chunk_x, gen_chunk_y) coordinates
        """
        # Calculate world bounds of the render chunk
        render_min_x = render_chunk_x * self.render_chunk_size
        render_min_y = render_chunk_y * self.render_chunk_size
        render_max_x = render_min_x + self.render_chunk_size - 1
        render_max_y = render_min_y + self.render_chunk_size - 1
        
        # Find all generation chunks that overlap with this render chunk
        gen_chunks = []
        
        # Calculate generation chunk bounds that overlap with render chunk
        min_gen_x = math.floor(render_min_x / generation_chunk_size)
        min_gen_y = math.floor(render_min_y / generation_chunk_size)
        max_gen_x = math.floor(render_max_x / generation_chunk_size)
        max_gen_y = math.floor(render_max_y / generation_chunk_size)
        
        for gen_x in range(min_gen_x, max_gen_x + 1):
            for gen_y in range(min_gen_y, max_gen_y + 1):
                gen_chunks.append((gen_x, gen_y))
        
        return gen_chunks
    
    def aggregate_generation_chunks(self, generation_chunks: List[GenerationChunk],
                                  render_chunk_x: int, render_chunk_y: int) -> RenderChunk:
        """
        Aggregate multiple generation chunks into a single render chunk.
        
        Args:
            generation_chunks: List of generation chunks to aggregate
            render_chunk_x: Target render chunk X coordinate
            render_chunk_y: Target render chunk Y coordinate
            
        Returns:
            Aggregated render chunk
        """
        # Calculate render chunk world bounds
        render_min_x = render_chunk_x * self.render_chunk_size
        render_min_y = render_chunk_y * self.render_chunk_size
        render_max_x = render_min_x + self.render_chunk_size - 1
        render_max_y = render_min_y + self.render_chunk_size - 1
        
        # Aggregate all tiles from generation chunks
        aggregated_tiles = {}
        
        for gen_chunk in generation_chunks:
            for (world_x, world_y), tile_data in gen_chunk.tiles.items():
                # Only include tiles that fall within the render chunk bounds
                if (render_min_x <= world_x <= render_max_x and
                    render_min_y <= world_y <= render_max_y):
                    # Extract tile_type from tile_data dictionary
                    if isinstance(tile_data, dict):
                        tile_type = tile_data.get('tile_type', 'land')
                    else:
                        tile_type = tile_data  # Fallback if it's already a string
                    aggregated_tiles[(world_x, world_y)] = tile_type
        
        # Aggregate metadata
        aggregated_metadata = {
            'generation_chunk_count': len(generation_chunks),
            'generation_chunk_sizes': [chunk.chunk_size for chunk in generation_chunks],
            'tile_count': len(aggregated_tiles),
            'render_chunk_bounds': (render_min_x, render_min_y, render_max_x, render_max_y)
        }
        
        # Add metadata from generation chunks
        for i, gen_chunk in enumerate(generation_chunks):
            aggregated_metadata[f'gen_chunk_{i}_metadata'] = gen_chunk.metadata
        
        return RenderChunk(
            chunk_x=render_chunk_x,
            chunk_y=render_chunk_y,
            chunk_size=self.render_chunk_size,
            generation_chunks=generation_chunks,
            aggregated_tiles=aggregated_tiles,
            metadata=aggregated_metadata
        )
    
    def get_render_chunks_for_area(self, min_world_x: int, min_world_y: int,
                                  max_world_x: int, max_world_y: int) -> List[Tuple[int, int]]:
        """
        Get all render chunk coordinates that overlap with a world area.
        
        Args:
            min_world_x: Minimum world X coordinate
            min_world_y: Minimum world Y coordinate
            max_world_x: Maximum world X coordinate
            max_world_y: Maximum world Y coordinate
            
        Returns:
            List of (render_chunk_x, render_chunk_y) coordinates
        """
        min_render_x = math.floor(min_world_x / self.render_chunk_size)
        min_render_y = math.floor(min_world_y / self.render_chunk_size)
        max_render_x = math.floor(max_world_x / self.render_chunk_size)
        max_render_y = math.floor(max_world_y / self.render_chunk_size)
        
        render_chunks = []
        for render_x in range(min_render_x, max_render_x + 1):
            for render_y in range(min_render_y, max_render_y + 1):
                render_chunks.append((render_x, render_y))
        
        return render_chunks
    
    def calculate_final_generation_chunk_size(self, initial_chunk_size: int, 
                                            pipeline_layers: List[str]) -> int:
        """
        Calculate the final generation chunk size after all pipeline layers.

        Args:
            initial_chunk_size: Starting chunk size (e.g., 64 for lands_and_seas)
            pipeline_layers: List of pipeline layer names

        Returns:
            Final generation chunk size after all zoom layers
        """
        current_size = initial_chunk_size
        
        for layer_name in pipeline_layers:
            if layer_name == "zoom":
                current_size = current_size // 2  # Each zoom layer halves the size
        
        # Ensure minimum size of 1
        return max(1, current_size)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the dual chunk system."""
        return {
            'render_chunk_size': self.render_chunk_size,
            'coord_cache_size': len(self._coord_cache),
            'cache_hit_ratio': 'N/A'  # Could be implemented with hit/miss counters
        }