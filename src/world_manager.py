#!/usr/bin/env python3
"""
World Manager for Infinite Procedural World

Manages chunk loading, unloading, and caching for an infinite world system.
Integrates with the existing world generation pipeline to provide seamless
exploration of procedurally generated terrain.
"""

import math
from typing import Dict, Set, Tuple, Optional, List
from collections import OrderedDict
from .camera import Camera
from .config import WorldConfig
from .generators.world_generator import WorldGenerator
from .generators.pipeline_generator import Tile


class WorldManager:
    """
    Manages an infinite world through dynamic chunk loading and unloading.
    
    The WorldManager tracks which chunks are loaded based on camera position
    and render distance, automatically loading new chunks as they come into
    view and unloading chunks that are too far away to conserve memory.
    """
    
    def __init__(self, world_config: WorldConfig, world_generator: WorldGenerator):
        """
        Initialize the world manager.

        Args:
            world_config: World configuration settings
            world_generator: World generator for creating new chunks
        """
        self.config = world_config
        self.world_generator = world_generator

        # Chunk management
        self.chunk_size = world_config.chunk_size
        self.render_distance = world_config.render_distance
        self.chunk_cache_limit = world_config.chunk_cache_limit
        self.chunk_unload_distance = world_config.chunk_unload_distance

        # Loaded chunks - using OrderedDict for LRU behavior
        self.loaded_chunks: OrderedDict[Tuple[int, int], Dict] = OrderedDict()

        # Track which chunks are currently being loaded (for async loading in future)
        self.loading_chunks: Set[Tuple[int, int]] = set()

        # Cache for quick tile lookups
        self._tile_cache: Dict[Tuple[int, int], Tile] = {}

        # Performance optimization - track last camera position to avoid redundant updates
        self._last_camera_chunk: Optional[Tuple[int, int]] = None
        self._last_required_chunks: Set[Tuple[int, int]] = set()

        # Statistics
        self.chunks_loaded_count = 0
        self.chunks_unloaded_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def world_to_chunk_coords(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """
        Convert world coordinates to chunk coordinates.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            
        Returns:
            Tuple of (chunk_x, chunk_y)
        """
        chunk_x = math.floor(world_x / self.chunk_size)
        chunk_y = math.floor(world_y / self.chunk_size)
        return chunk_x, chunk_y
    
    def chunk_to_world_bounds(self, chunk_x: int, chunk_y: int) -> Tuple[int, int, int, int]:
        """
        Get world coordinate bounds for a chunk.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            
        Returns:
            Tuple of (min_world_x, min_world_y, max_world_x, max_world_y)
        """
        min_x = chunk_x * self.chunk_size
        min_y = chunk_y * self.chunk_size
        max_x = min_x + self.chunk_size - 1
        max_y = min_y + self.chunk_size - 1
        return min_x, min_y, max_x, max_y
    
    def get_required_chunks(self, camera: Camera) -> Set[Tuple[int, int]]:
        """
        Calculate which chunks should be loaded based on camera position.
        
        Args:
            camera: Camera instance to check position
            
        Returns:
            Set of (chunk_x, chunk_y) tuples that should be loaded
        """
        cursor_x, cursor_y = camera.get_cursor_position()
        center_chunk_x, center_chunk_y = self.world_to_chunk_coords(cursor_x, cursor_y)
        
        required_chunks = set()
        
        # Load chunks in a square around the camera
        for dx in range(-self.render_distance, self.render_distance + 1):
            for dy in range(-self.render_distance, self.render_distance + 1):
                chunk_x = center_chunk_x + dx
                chunk_y = center_chunk_y + dy
                required_chunks.add((chunk_x, chunk_y))
        
        return required_chunks
    
    def get_chunks_to_unload(self, camera: Camera) -> Set[Tuple[int, int]]:
        """
        Calculate which chunks should be unloaded based on distance from camera.
        
        Args:
            camera: Camera instance to check position
            
        Returns:
            Set of (chunk_x, chunk_y) tuples that should be unloaded
        """
        cursor_x, cursor_y = camera.get_cursor_position()
        center_chunk_x, center_chunk_y = self.world_to_chunk_coords(cursor_x, cursor_y)
        
        chunks_to_unload = set()
        
        for chunk_coords in self.loaded_chunks.keys():
            chunk_x, chunk_y = chunk_coords
            
            # Calculate distance from camera chunk
            dx = abs(chunk_x - center_chunk_x)
            dy = abs(chunk_y - center_chunk_y)
            max_distance = max(dx, dy)
            
            # Unload if beyond unload distance
            if max_distance > self.chunk_unload_distance:
                chunks_to_unload.add(chunk_coords)
        
        return chunks_to_unload
    
    def load_chunk(self, chunk_x: int, chunk_y: int):
        """
        Load a single chunk using the world generator.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
        """
        chunk_coords = (chunk_x, chunk_y)
        
        if chunk_coords in self.loaded_chunks or chunk_coords in self.loading_chunks:
            return
        
        self.loading_chunks.add(chunk_coords)
        
        try:
            # Use the existing world generator to ensure chunk is loaded
            # The pipeline generator will handle the actual generation
            min_x, min_y, max_x, max_y = self.chunk_to_world_bounds(chunk_x, chunk_y)
            
            # Pre-load a few tiles to ensure the chunk is generated
            for x in range(min_x, min_x + 3):  # Just sample a few tiles
                for y in range(min_y, min_y + 3):
                    self.world_generator.get_tile(x, y)
            
            # Mark chunk as loaded
            chunk_data = {
                'chunk_x': chunk_x,
                'chunk_y': chunk_y,
                'world_bounds': (min_x, min_y, max_x, max_y),
                'loaded_at': self.chunks_loaded_count
            }
            
            self.loaded_chunks[chunk_coords] = chunk_data
            self.chunks_loaded_count += 1
            
        finally:
            self.loading_chunks.discard(chunk_coords)
    
    def unload_chunk(self, chunk_x: int, chunk_y: int):
        """
        Unload a single chunk to free memory.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
        """
        chunk_coords = (chunk_x, chunk_y)
        
        if chunk_coords in self.loaded_chunks:
            del self.loaded_chunks[chunk_coords]
            self.chunks_unloaded_count += 1
            
            # Clear related tile cache entries
            min_x, min_y, max_x, max_y = self.chunk_to_world_bounds(chunk_x, chunk_y)
            tiles_to_remove = []
            for tile_coords in self._tile_cache.keys():
                tx, ty = tile_coords
                if min_x <= tx <= max_x and min_y <= ty <= max_y:
                    tiles_to_remove.append(tile_coords)
            
            for tile_coords in tiles_to_remove:
                del self._tile_cache[tile_coords]
    
    def update_chunks(self, camera: Camera):
        """
        Update loaded chunks based on camera position.
        Only updates if camera moved to a different chunk.

        Args:
            camera: Camera instance to check position
        """
        cursor_x, cursor_y = camera.get_cursor_position()
        current_camera_chunk = self.world_to_chunk_coords(cursor_x, cursor_y)

        # Performance optimization: only update if camera moved to a different chunk
        if current_camera_chunk == self._last_camera_chunk:
            return  # No chunk change, no update needed

        # Get required chunks
        required_chunks = self.get_required_chunks(camera)

        # Performance optimization: only update if required chunks changed significantly
        if self._last_required_chunks and len(required_chunks.symmetric_difference(self._last_required_chunks)) < 3:
            # Less than 3 chunks changed, skip update for performance
            self._last_camera_chunk = current_camera_chunk
            return

        # Load new chunks
        for chunk_coords in required_chunks:
            if chunk_coords not in self.loaded_chunks:
                self.load_chunk(*chunk_coords)

        # Unload distant chunks
        chunks_to_unload = self.get_chunks_to_unload(camera)
        for chunk_coords in chunks_to_unload:
            self.unload_chunk(*chunk_coords)

        # Enforce cache limit using LRU
        while len(self.loaded_chunks) > self.chunk_cache_limit:
            # Remove oldest chunk (first in OrderedDict)
            oldest_chunk = next(iter(self.loaded_chunks))
            self.unload_chunk(*oldest_chunk)

        # Update tracking variables
        self._last_camera_chunk = current_camera_chunk
        self._last_required_chunks = required_chunks
    
    def get_tile(self, world_x: int, world_y: int) -> Tile:
        """
        Get a tile at the specified world coordinates.
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            
        Returns:
            Tile at the specified position
        """
        tile_coords = (world_x, world_y)
        
        # Check tile cache first
        if tile_coords in self._tile_cache:
            self.cache_hits += 1
            return self._tile_cache[tile_coords]
        
        # Cache miss - get from world generator
        self.cache_misses += 1
        tile = self.world_generator.get_tile(world_x, world_y)
        
        # Cache the tile (with larger size limit for better performance)
        if len(self._tile_cache) < 50000:  # Increased tile cache size
            self._tile_cache[tile_coords] = tile
        
        return tile
    
    def get_loaded_chunk_count(self) -> int:
        """Get the number of currently loaded chunks."""
        return len(self.loaded_chunks)
    
    def get_statistics(self) -> Dict:
        """
        Get world manager statistics.
        
        Returns:
            Dictionary with performance and usage statistics
        """
        return {
            'loaded_chunks': len(self.loaded_chunks),
            'loading_chunks': len(self.loading_chunks),
            'chunks_loaded_total': self.chunks_loaded_count,
            'chunks_unloaded_total': self.chunks_unloaded_count,
            'tile_cache_size': len(self._tile_cache),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_ratio': self.cache_hits / max(1, self.cache_hits + self.cache_misses)
        }
    
    def get_chunk_info(self, world_x: int, world_y: int) -> Optional[Dict]:
        """
        Get information about the chunk containing the given world position.

        Args:
            world_x: World X coordinate
            world_y: World Y coordinate

        Returns:
            Dictionary with chunk information, or None if chunk not loaded
        """
        chunk_coords = self.world_to_chunk_coords(world_x, world_y)
        return self.loaded_chunks.get(chunk_coords)

    def is_chunk_loaded(self, chunk_x: int, chunk_y: int) -> bool:
        """
        Check if a chunk is currently loaded.

        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate

        Returns:
            True if the chunk is loaded
        """
        return (chunk_x, chunk_y) in self.loaded_chunks

    def get_loaded_chunks_list(self) -> List[Tuple[int, int]]:
        """
        Get a list of all currently loaded chunk coordinates.

        Returns:
            List of (chunk_x, chunk_y) tuples
        """
        return list(self.loaded_chunks.keys())

    def clear_cache(self):
        """Clear all caches and unload all chunks."""
        self.loaded_chunks.clear()
        self.loading_chunks.clear()
        self._tile_cache.clear()
        print("World manager cache cleared")

    def regenerate_world(self):
        """
        Regenerate the world by clearing caches.

        This will force all chunks to be regenerated when next accessed.
        """
        self.clear_cache()
        # Also clear the world generator's cache if it has one
        if hasattr(self.world_generator, 'current_generator'):
            if hasattr(self.world_generator.current_generator, '_chunk_cache'):
                self.world_generator.current_generator._chunk_cache.clear()
        print("World regenerated - all chunks will be recreated")


# Example usage and testing
if __name__ == "__main__":
    from .config import WorldConfig, CameraConfig
    from .camera import Camera
    from .generators.world_generator import WorldGenerator

    # Test the world manager
    world_config = WorldConfig(
        chunk_size=16,
        render_distance=2,
        chunk_cache_limit=25,
        chunk_unload_distance=4,
        seed=12345,
        generator_type="pipeline",
        pipeline_layers=["lands_and_seas"],
        layer_configs={}
    )

    camera_config = CameraConfig(initial_x=0, initial_y=0)
    camera = Camera(camera_config)

    world_generator = WorldGenerator(
        generator_type=world_config.generator_type,
        seed=world_config.seed,
        chunk_size=world_config.chunk_size,
        pipeline_layers=world_config.pipeline_layers,
        layer_configs=world_config.layer_configs
    )

    world_manager = WorldManager(world_config, world_generator)

    print("World Manager Test")
    print(f"Initial loaded chunks: {world_manager.get_loaded_chunk_count()}")

    # Test chunk loading around camera
    world_manager.update_chunks(camera)
    print(f"Chunks after initial load: {world_manager.get_loaded_chunk_count()}")

    # Test tile access
    tile = world_manager.get_tile(0, 0)
    print(f"Tile at (0,0): {tile.tile_type}")

    # Test camera movement and chunk updates
    camera.move_right(fast_mode=True)  # Move 5 tiles right
    camera.move_down(fast_mode=True)   # Move 5 tiles down

    world_manager.update_chunks(camera)
    print(f"Chunks after camera movement: {world_manager.get_loaded_chunk_count()}")

    # Test statistics
    stats = world_manager.get_statistics()
    print(f"Statistics: {stats}")

    print("World manager test completed!")
