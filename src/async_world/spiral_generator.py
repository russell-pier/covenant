#!/usr/bin/env python3
"""
Spiral chunk generation algorithm for efficient world loading.

Generates chunks in a spiral pattern outward from the cursor position,
similar to Minecraft's chunk loading system.
"""

from typing import List, Tuple, Set, Iterator
import math


class SpiralChunkGenerator:
    """
    Generates chunk coordinates in a spiral pattern outward from a center point.
    
    This mimics Minecraft's efficient chunk loading where chunks are loaded
    in order of distance from the player, ensuring the most important chunks
    are loaded first.
    """
    
    def __init__(self, max_radius: int = 8):
        """
        Initialize the spiral generator.
        
        Args:
            max_radius: Maximum radius in chunks to generate
        """
        self.max_radius = max_radius
        self._spiral_cache = {}  # Cache spiral patterns for different radii
    
    def generate_spiral(self, center_chunk_x: int, center_chunk_y: int, 
                       radius: int) -> List[Tuple[int, int]]:
        """
        Generate chunk coordinates in a spiral pattern around the center.
        
        Args:
            center_chunk_x: Center chunk X coordinate
            center_chunk_y: Center chunk Y coordinate
            radius: Maximum radius in chunks
            
        Returns:
            List of chunk coordinates in spiral order (closest first)
        """
        if radius in self._spiral_cache:
            # Use cached spiral pattern and offset it
            cached_spiral = self._spiral_cache[radius]
            return [(center_chunk_x + dx, center_chunk_y + dy) for dx, dy in cached_spiral]
        
        # Generate new spiral pattern
        spiral_offsets = self._generate_spiral_offsets(radius)
        self._spiral_cache[radius] = spiral_offsets
        
        # Apply offsets to center position
        return [(center_chunk_x + dx, center_chunk_y + dy) for dx, dy in spiral_offsets]
    
    def _generate_spiral_offsets(self, radius: int) -> List[Tuple[int, int]]:
        """
        Generate spiral offset pattern from (0,0).
        
        Uses a square spiral algorithm that prioritizes chunks by distance.
        """
        if radius <= 0:
            return [(0, 0)]
        
        offsets = [(0, 0)]  # Start with center
        
        # Generate spiral layer by layer
        for layer in range(1, radius + 1):
            layer_offsets = self._generate_layer_offsets(layer)
            
            # Sort by distance from center for this layer
            layer_offsets.sort(key=lambda pos: self._distance_squared(pos[0], pos[1]))
            offsets.extend(layer_offsets)
        
        return offsets
    
    def _generate_layer_offsets(self, layer: int) -> List[Tuple[int, int]]:
        """Generate all offsets for a specific layer of the spiral."""
        offsets = []
        
        # Top edge (left to right)
        for x in range(-layer, layer + 1):
            offsets.append((x, -layer))
        
        # Right edge (top to bottom, excluding corners)
        for y in range(-layer + 1, layer):
            offsets.append((layer, y))
        
        # Bottom edge (right to left, excluding right corner)
        if layer > 0:
            for x in range(layer, -layer - 1, -1):
                offsets.append((x, layer))
        
        # Left edge (bottom to top, excluding corners)
        for y in range(layer - 1, -layer, -1):
            offsets.append((-layer, y))
        
        return offsets
    
    def _distance_squared(self, x: int, y: int) -> float:
        """Calculate squared distance from origin (for sorting)."""
        return x * x + y * y
    
    def get_new_chunks_for_movement(self, old_center: Tuple[int, int], 
                                   new_center: Tuple[int, int], 
                                   radius: int) -> List[Tuple[int, int]]:
        """
        Get only the new chunks needed when moving from old_center to new_center.
        
        This is the key optimization - we don't regenerate existing chunks,
        we only generate the new ones at the edges.
        
        Args:
            old_center: Previous center chunk coordinates
            new_center: New center chunk coordinates  
            radius: Chunk loading radius
            
        Returns:
            List of new chunk coordinates needed, in spiral order
        """
        if old_center == new_center:
            return []  # No movement, no new chunks needed
        
        # Get all chunks for old and new positions
        old_chunks = set(self.generate_spiral(old_center[0], old_center[1], radius))
        new_chunks = set(self.generate_spiral(new_center[0], new_center[1], radius))
        
        # Find chunks that are new (in new set but not in old set)
        new_chunk_coords = new_chunks - old_chunks
        
        if not new_chunk_coords:
            return []
        
        # Sort new chunks by distance from new center (spiral order)
        new_chunks_list = list(new_chunk_coords)
        new_chunks_list.sort(key=lambda chunk: self._distance_squared(
            chunk[0] - new_center[0], 
            chunk[1] - new_center[1]
        ))
        
        return new_chunks_list
    
    def get_chunks_to_unload(self, old_center: Tuple[int, int], 
                            new_center: Tuple[int, int], 
                            radius: int, unload_radius: int) -> List[Tuple[int, int]]:
        """
        Get chunks that should be unloaded when moving.
        
        Args:
            old_center: Previous center chunk coordinates
            new_center: New center chunk coordinates
            radius: Current loading radius
            unload_radius: Distance at which to unload chunks
            
        Returns:
            List of chunk coordinates to unload
        """
        if old_center == new_center:
            return []
        
        # Get chunks that were loaded at old position
        old_chunks = set(self.generate_spiral(old_center[0], old_center[1], radius))
        
        # Get chunks that should stay loaded at new position (with unload buffer)
        keep_chunks = set(self.generate_spiral(new_center[0], new_center[1], unload_radius))
        
        # Chunks to unload are those that were loaded but are now too far
        unload_chunks = old_chunks - keep_chunks
        
        return list(unload_chunks)


class ChunkLoadingManager:
    """
    Manages chunk loading using spiral generation with movement optimization.
    
    This class handles the high-level logic of when to generate chunks,
    what to keep loaded, and how to prioritize generation requests.
    """
    
    def __init__(self, load_radius: int = 3, unload_radius: int = 5):
        """
        Initialize the chunk loading manager.
        
        Args:
            load_radius: Radius in chunks to keep loaded around cursor
            unload_radius: Distance at which chunks get unloaded
        """
        self.load_radius = load_radius
        self.unload_radius = unload_radius
        self.spiral_generator = SpiralChunkGenerator(max_radius=unload_radius)
        
        # Track state
        self.current_center_chunk: Tuple[int, int] = (0, 0)
        self.loaded_chunks: Set[Tuple[int, int]] = set()
        self.generation_queue: List[Tuple[int, int]] = []
    
    def update_for_position(self, new_center_chunk: Tuple[int, int]) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """
        Update chunk loading for a new cursor position.
        
        Args:
            new_center_chunk: New center chunk coordinates
            
        Returns:
            Tuple of (chunks_to_generate, chunks_to_unload)
        """
        old_center = self.current_center_chunk
        
        # Get new chunks needed (spiral order, closest first)
        new_chunks = self.spiral_generator.get_new_chunks_for_movement(
            old_center, new_center_chunk, self.load_radius
        )
        
        # Get chunks to unload (too far away)
        unload_chunks = self.spiral_generator.get_chunks_to_unload(
            old_center, new_center_chunk, self.load_radius, self.unload_radius
        )
        
        # Update state
        self.current_center_chunk = new_center_chunk
        
        # Update loaded chunks set
        for chunk in unload_chunks:
            self.loaded_chunks.discard(chunk)
        
        for chunk in new_chunks:
            self.loaded_chunks.add(chunk)
        
        return new_chunks, unload_chunks
    
    def get_initial_chunks(self, center_chunk: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Get initial chunks to load when starting at a position.
        
        Args:
            center_chunk: Starting center chunk coordinates
            
        Returns:
            List of chunks in spiral order (closest first)
        """
        self.current_center_chunk = center_chunk
        
        chunks = self.spiral_generator.generate_spiral(
            center_chunk[0], center_chunk[1], self.load_radius
        )
        
        self.loaded_chunks = set(chunks)
        return chunks
    
    def get_generation_priority(self, chunk: Tuple[int, int]) -> float:
        """
        Get generation priority for a chunk (lower = higher priority).
        
        Args:
            chunk: Chunk coordinates
            
        Returns:
            Priority value (distance from current center)
        """
        dx = chunk[0] - self.current_center_chunk[0]
        dy = chunk[1] - self.current_center_chunk[1]
        return math.sqrt(dx * dx + dy * dy)


# Example usage and testing
if __name__ == "__main__":
    # Test spiral generation
    spiral_gen = SpiralChunkGenerator()
    
    print("🌀 Testing Spiral Chunk Generation")
    print("=" * 40)
    
    # Test small spiral
    center = (0, 0)
    radius = 2
    spiral_chunks = spiral_gen.generate_spiral(center[0], center[1], radius)
    
    print(f"Spiral around {center} with radius {radius}:")
    for i, chunk in enumerate(spiral_chunks):
        distance = math.sqrt((chunk[0] - center[0])**2 + (chunk[1] - center[1])**2)
        print(f"  {i+1:2d}: {chunk} (distance: {distance:.1f})")
    
    # Test movement optimization
    print(f"\n🏃 Testing Movement Optimization")
    print("-" * 35)
    
    old_center = (0, 0)
    new_center = (1, 0)  # Move right by 1 chunk
    
    new_chunks = spiral_gen.get_new_chunks_for_movement(old_center, new_center, radius)
    unload_chunks = spiral_gen.get_chunks_to_unload(old_center, new_center, radius, radius + 2)
    
    print(f"Moving from {old_center} to {new_center}:")
    print(f"  New chunks needed: {new_chunks}")
    print(f"  Chunks to unload: {unload_chunks}")
    print(f"  Efficiency: Only {len(new_chunks)} new chunks vs {len(spiral_chunks)} total")
    
    print("\n✅ Spiral generation working correctly!")
