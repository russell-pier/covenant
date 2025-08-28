#!/usr/bin/env python3
"""
Async World Manager

Non-blocking world manager that coordinates with worker threads for smooth gameplay.
Handles chunk requests, caching, and provides immediate responses for rendering.
"""

import time
import math
from typing import Dict, Set, Tuple, Optional, List
from collections import OrderedDict

from .messages import MessageBus, Message, Priority
from .worker import WorldGenerationWorker
from .spiral_generator import ChunkLoadingManager
from .dual_chunk_system import DualChunkManager, RenderChunk
try:
    from ..profiler import profile_function, start_profiling, end_profiling
except ImportError:
    # Fallback for when profiler is not available
    def profile_function(name=None):
        def decorator(func):
            return func
        return decorator
    def start_profiling(name): pass
    def end_profiling(name): pass

# Handle imports for both direct execution and package import
try:
    from ..camera import Camera
    from ..config import WorldConfig
    from ..generators.pipeline_generator import Tile
except ImportError:
    try:
        # Fallback for direct execution
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from camera import Camera
        from config import WorldConfig
        from generators.pipeline_generator import Tile
    except ImportError:
        # Final fallback - create minimal implementations for testing
        print("Warning: Using minimal implementations for testing")

        class Camera:
            def __init__(self, config=None):
                self.x, self.y = 0, 0
            def get_cursor_position(self):
                return self.x, self.y

        class WorldConfig:
            def __init__(self):
                self.chunk_size = 32
                self.render_distance = 3
                self.chunk_cache_limit = 100
                self.chunk_unload_distance = 5

        class Tile:
            def __init__(self, x, y, tile_type="stone"):
                self.x = x
                self.y = y
                self.tile_type = tile_type


class AsyncWorldManager:
    """
    Asynchronous world manager that provides non-blocking chunk access.
    
    Coordinates with worker threads to generate chunks in the background
    while providing immediate responses for rendering.
    """
    
    def __init__(self, world_config: WorldConfig):
        """
        Initialize the async world manager.
        
        Args:
            world_config: World configuration settings
        """
        self.config = world_config
        
        # Dual chunk system setup
        self.base_chunk_size = world_config.chunk_size  # Starting size (32 for lands_and_seas)
        self.render_chunk_size = 64  # Fixed size for render chunks

        # Calculate final generation chunk size after all pipeline layers
        self.dual_chunk_manager = DualChunkManager(render_chunk_size=self.render_chunk_size)
        self.final_generation_chunk_size = self.dual_chunk_manager.calculate_final_generation_chunk_size(
            self.base_chunk_size, world_config.pipeline_layers
        )

        print(f"🔧 Dual chunk system: Render chunks {self.render_chunk_size}x{self.render_chunk_size}, "
              f"Generation chunks {self.base_chunk_size}→{self.final_generation_chunk_size}")
        
        # Chunk management
        self.render_distance = world_config.render_distance
        self.chunk_cache_limit = world_config.chunk_cache_limit
        self.chunk_unload_distance = world_config.chunk_unload_distance

        # Available render chunks (main thread cache) - now using 64x64 render chunks
        self.available_render_chunks: OrderedDict[Tuple[int, int], RenderChunk] = OrderedDict()

        # Chunk states
        self.requested_chunks: Set[Tuple[int, int]] = set()
        self.loading_chunks: Set[Tuple[int, int]] = set()

        # Message bus and worker
        self.message_bus = MessageBus()
        self.worker = WorldGenerationWorker(world_config, self.message_bus)

        # Spiral chunk loading manager (Minecraft-style) - now works with render chunks
        self.chunk_loader = ChunkLoadingManager(
            load_radius=self.render_distance,
            unload_radius=self.chunk_unload_distance
        )

        # Tile cache for immediate access
        self._tile_cache: Dict[Tuple[int, int], Tile] = {}
        self._placeholder_tile = Tile(0, 0, "loading")  # Correct constructor: x, y, tile_type

        # Performance tracking
        self._last_camera_chunk: Optional[Tuple[int, int]] = None
        self._last_update_time = 0.0
        self._update_throttle = 0.05  # Update every 50ms max (more responsive)
        self._initial_load_done = False
        
        # Statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.chunks_requested = 0
        self.chunks_received = 0
        
        # Start worker thread
        self.worker.start()
    
    def shutdown(self):
        """Shutdown the async world manager and worker threads."""
        print("Shutting down async world manager...")
        self.worker.stop()
        print("Async world manager shutdown complete")
    
    def world_to_render_chunk_coords(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Convert world coordinates to render chunk coordinates."""
        return self.dual_chunk_manager.world_to_render_chunk(world_x, world_y)

    def world_to_generation_chunk_coords(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Convert world coordinates to generation chunk coordinates."""
        return self.dual_chunk_manager.world_to_generation_chunk(
            world_x, world_y, self.final_generation_chunk_size
        )
    
    @profile_function("async_world.update_chunks")
    def update_chunks(self, camera: Camera, screen_width: int = 80, screen_height: int = 50):
        """
        Update chunks using Minecraft-style spiral generation (non-blocking).

        Args:
            camera: Camera instance to check position
            screen_width: Width of the screen in tiles (for compatibility)
            screen_height: Height of the screen in tiles (for compatibility)
        """
        current_time = time.time()

        # Throttle updates for performance
        if current_time - self._last_update_time < self._update_throttle:
            # Still process incoming messages even when throttled
            self._process_incoming_messages()
            return

        cursor_x, cursor_y = camera.get_cursor_position()
        current_camera_chunk = self.world_to_render_chunk_coords(cursor_x, cursor_y)

        # Process incoming chunk data first
        self._process_incoming_messages()

        # Handle initial load vs movement
        if not self._initial_load_done:
            # Initial spiral load around starting position
            chunks_to_generate = self.chunk_loader.get_initial_chunks(current_camera_chunk)
            chunks_to_unload = []
            self._initial_load_done = True
            print(f"🌀 Initial spiral load: {len(chunks_to_generate)} render chunks around {current_camera_chunk}")
        else:
            # Efficient movement-based loading (only new render chunks at edges)
            chunks_to_generate, chunks_to_unload = self.chunk_loader.update_for_position(current_camera_chunk)

            if chunks_to_generate:
                print(f"🏃 Movement: +{len(chunks_to_generate)} new render chunks, -{len(chunks_to_unload)} unloaded")

        # Request new chunks in spiral order (closest first)
        self._request_chunks_in_priority_order(chunks_to_generate)

        # Unload distant chunks
        self._unload_chunks(chunks_to_unload)

        # Update tracking
        self._last_camera_chunk = current_camera_chunk
        self._last_update_time = current_time
    
    @profile_function("async_world.get_tile")
    def get_tile(self, world_x: int, world_y: int) -> Tile:
        """
        Get a tile at the specified world coordinates (immediate response).
        
        Args:
            world_x: World X coordinate
            world_y: World Y coordinate
            
        Returns:
            Tile at the specified position (may be placeholder if loading)
        """
        tile_coords = (world_x, world_y)
        
        # Check tile cache first
        if tile_coords in self._tile_cache:
            self.cache_hits += 1
            return self._tile_cache[tile_coords]
        
        # Check if render chunk is available
        render_chunk_coords = self.world_to_render_chunk_coords(world_x, world_y)

        if render_chunk_coords in self.available_render_chunks:
            # Render chunk is available, get tile from aggregated data
            self.cache_misses += 1

            render_chunk_data = self.available_render_chunks[render_chunk_coords]

            # Get tile from render chunk's aggregated tiles
            tile_type = render_chunk_data['aggregated_tiles'].get((world_x, world_y))

            if tile_type:
                # Use actual generated tile data
                tile = Tile(world_x, world_y, tile_type)
            else:
                # Fallback to basic pattern if tile data missing
                if (world_x + world_y) % 3 == 0:
                    tile = Tile(world_x, world_y, "water")
                else:
                    tile = Tile(world_x, world_y, "stone")

            # Cache the tile
            if len(self._tile_cache) < 50000:
                self._tile_cache[tile_coords] = tile

            return tile
        else:
            # Chunk not available, return placeholder
            self.cache_misses += 1
            return self._placeholder_tile
    
    def is_chunk_loaded(self, chunk_x: int, chunk_y: int) -> bool:
        """Check if a render chunk is loaded and available."""
        return (chunk_x, chunk_y) in self.available_render_chunks

    def is_chunk_loading(self, chunk_x: int, chunk_y: int) -> bool:
        """Check if a render chunk is currently being loaded."""
        return (chunk_x, chunk_y) in self.loading_chunks

    def get_loaded_chunk_count(self) -> int:
        """Get the number of currently loaded render chunks."""
        return len(self.available_render_chunks)
    
    def get_chunk_info(self, world_x: int, world_y: int) -> Optional[Dict]:
        """Get information about the render chunk containing the given world position."""
        render_chunk_coords = self.world_to_render_chunk_coords(world_x, world_y)
        render_chunk = self.available_render_chunks.get(render_chunk_coords)

        if render_chunk:
            return {
                'chunk_x': render_chunk_coords[0],
                'chunk_y': render_chunk_coords[1],
                'chunk_size': self.render_chunk_size,
                'chunk_type': 'render',
                'tile_count': render_chunk.get('tile_count', 0),
                'loaded': True,
                'loading': False
            }
        elif render_chunk_coords in self.loading_chunks:
            return {
                'chunk_x': render_chunk_coords[0],
                'chunk_y': render_chunk_coords[1],
                'chunk_size': self.render_chunk_size,
                'chunk_type': 'render',
                'loaded': False,
                'loading': True
            }
        else:
            return {
                'chunk_x': render_chunk_coords[0],
                'chunk_y': render_chunk_coords[1],
                'chunk_size': self.render_chunk_size,
                'chunk_type': 'render',
                'loaded': False,
                'loading': False
            }
    
    def _request_chunks_in_priority_order(self, chunks_to_generate: List[Tuple[int, int]]):
        """
        Request chunks in priority order (spiral order - closest first).

        Args:
            chunks_to_generate: List of chunk coordinates in priority order
        """
        for chunk_coords in chunks_to_generate:
            chunk_x, chunk_y = chunk_coords

            # Skip if already available or being loaded
            if (chunk_coords in self.available_render_chunks or
                chunk_coords in self.loading_chunks or
                chunk_coords in self.requested_chunks):
                continue

            # Calculate priority based on distance from cursor
            priority = self.chunk_loader.get_generation_priority(chunk_coords)

            # Use URGENT priority for closest chunks, HIGH for nearby, NORMAL for distant
            if priority <= 1.0:
                msg_priority = Priority.URGENT
            elif priority <= 2.0:
                msg_priority = Priority.HIGH
            else:
                msg_priority = Priority.NORMAL

            # Send request to worker
            request_msg = Message.chunk_request(chunk_x, chunk_y, msg_priority)
            self.message_bus.send_to_worker(request_msg, block=False)

            # Track request
            self.requested_chunks.add(chunk_coords)
            self.loading_chunks.add(chunk_coords)
            self.chunks_requested += 1

    def _unload_chunks(self, chunks_to_unload: List[Tuple[int, int]]):
        """
        Unload chunks that are too far away.

        Args:
            chunks_to_unload: List of chunk coordinates to unload
        """
        for chunk_coords in chunks_to_unload:
            # Remove from available render chunks
            if chunk_coords in self.available_render_chunks:
                del self.available_render_chunks[chunk_coords]

            # Remove from tracking sets
            self.loading_chunks.discard(chunk_coords)
            self.requested_chunks.discard(chunk_coords)

            # Clear related tiles from cache
            self._clear_chunk_tiles_from_cache(chunk_coords)

    def _clear_chunk_tiles_from_cache(self, chunk_coords: Tuple[int, int]):
        """Clear tiles belonging to a render chunk from the tile cache."""
        chunk_x, chunk_y = chunk_coords

        # Calculate render chunk bounds (using render chunk size)
        min_world_x = chunk_x * self.render_chunk_size
        min_world_y = chunk_y * self.render_chunk_size
        max_world_x = min_world_x + self.render_chunk_size - 1
        max_world_y = min_world_y + self.render_chunk_size - 1

        # Remove tiles in this render chunk from cache
        tiles_to_remove = []
        for tile_coords in self._tile_cache.keys():
            tile_x, tile_y = tile_coords
            if (min_world_x <= tile_x <= max_world_x and
                min_world_y <= tile_y <= max_world_y):
                tiles_to_remove.append(tile_coords)

        for tile_coords in tiles_to_remove:
            del self._tile_cache[tile_coords]
    
    def _request_missing_chunks(self, required_chunks: Set[Tuple[int, int]]):
        """Legacy method - now handled by spiral generation."""
        # This method is kept for compatibility but spiral generation
        # handles chunk requests more efficiently
        pass
    
    def _process_incoming_messages(self):
        """Process messages from worker threads."""
        # Process all available messages (non-blocking)
        while True:
            message = self.message_bus.receive_from_worker(block=False)
            if message is None:
                break
            
            if message.message_type.value == "chunk_response":
                self._handle_chunk_response(message)
            elif message.message_type.value == "status_update":
                self._handle_status_update(message)
    
    def _handle_chunk_response(self, message: Message):
        """Handle render chunk response from worker."""
        response = message.payload
        render_chunk_coords = (response.chunk_x, response.chunk_y)

        if response.success:
            # Handle chunk_data - store as simple dict to avoid unhashable type issues
            chunk_data = response.chunk_data

            # Store chunk data as a simple dictionary instead of RenderChunk object
            # to avoid potential unhashable type issues
            if isinstance(chunk_data, dict) and 'aggregated_tiles' in chunk_data:
                # Create a simplified render chunk representation
                render_chunk_data = {
                    'chunk_x': chunk_data['chunk_x'],
                    'chunk_y': chunk_data['chunk_y'],
                    'chunk_size': chunk_data.get('chunk_size', self.render_chunk_size),
                    'aggregated_tiles': chunk_data['aggregated_tiles'],
                    'metadata': chunk_data.get('metadata', {}),
                    'tile_count': len(chunk_data['aggregated_tiles'])
                }

                # Add render chunk data to available chunks
                self.available_render_chunks[render_chunk_coords] = render_chunk_data
                self.chunks_received += 1

                # Enforce cache limit
                while len(self.available_render_chunks) > self.chunk_cache_limit:
                    oldest_chunk = next(iter(self.available_render_chunks))
                    del self.available_render_chunks[oldest_chunk]
            else:
                print(f"Invalid render chunk data received: {type(chunk_data)}")
        else:
            print(f"Render chunk generation failed: {response.error_message}")

        # Remove from loading state
        self.loading_chunks.discard(render_chunk_coords)
        self.requested_chunks.discard(render_chunk_coords)
    
    def _handle_status_update(self, message: Message):
        """Handle status update from worker."""
        # Could log or display worker status
        pass
    
    def _cleanup_distant_chunks(self, camera: Camera, screen_width: int, screen_height: int):
        """Legacy method - now handled by spiral generation."""
        # Chunk cleanup is now handled by the spiral chunk loader
        # which is more efficient and only unloads chunks when moving
        pass
    
    def get_statistics(self) -> Dict:
        """Get world manager statistics."""
        # Get basic statistics without nested dictionaries to avoid unhashable type errors
        try:
            worker_stats = self.worker.get_statistics()
            worker_chunks_generated = worker_stats.get('chunks_generated', 0)
            worker_cache_size = worker_stats.get('cache_size', 0)
        except:
            worker_chunks_generated = 0
            worker_cache_size = 0

        try:
            bus_stats = self.message_bus.get_stats()
            messages_sent = bus_stats.get('messages_sent', 0)
        except:
            messages_sent = 0

        return {
            'loaded_render_chunks': len(self.available_render_chunks),
            'loading_chunks': len(self.loading_chunks),
            'requested_chunks': len(self.requested_chunks),
            'chunks_requested': self.chunks_requested,
            'chunks_received': self.chunks_received,
            'tile_cache_size': len(self._tile_cache),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_ratio': self.cache_hits / max(1, self.cache_hits + self.cache_misses),
            'render_chunk_size': self.render_chunk_size,
            'generation_chunk_size': self.final_generation_chunk_size,
            'worker_chunks_generated': worker_chunks_generated,
            'worker_cache_size': worker_cache_size,
            'messages_sent': messages_sent
        }
