#!/usr/bin/env python3
"""
WorldManager - Advanced world manager with pipeline system

Provides world generation using the TierManager pipeline system.
"""

import threading
from typing import Dict, Any, Tuple, Optional, Set
from ..config import WorldConfig
from .worker import WorldGenerationWorker, Tile
from .tier_manager import TierManager
# Removed dual chunk system - now using fixed 16x16 chunks
from .messages import MessageBus


class WorldManager:
    """
    Advanced world manager that uses the TierManager pipeline system.
    """

    def __init__(self, world_config: WorldConfig):
        """Initialize the world manager with pipeline system."""
        self.config = world_config
        self._lock = threading.Lock()

        # Fixed chunk system - all chunks are the same size
        self.chunk_size = world_config.chunk_size

        # Initialize message bus for worker communication
        self.message_bus = MessageBus()

        # Initialize TierManager
        self._setup_tier_manager()

        # Initialize worker
        self.worker = WorldGenerationWorker(
            world_config=world_config,
            tier_manager=self.tier_manager,
            message_bus=self.message_bus
        )
        self.worker.start()

        # Non-blocking tile access system
        self.tile_cache = {}  # (x, y) -> Tile
        self.loading_chunks = set()  # Track requested chunks
        self.ready_chunks = set()   # Track completed chunks

        # Basic statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.chunks_requested = 0
        self.chunks_received = 0


    
    def _setup_tier_manager(self):
        """Set up the TierManager with configured layers."""
        self.tier_manager = TierManager()

        # Load layer configurations as list of tuples (required by TierManager)
        layer_configs = []
        for layer_name in self.config.pipeline_layers:
            if layer_name in self.config.layer_configs:
                layer_configs.append((layer_name, self.config.layer_configs[layer_name]))
            else:
                raise RuntimeError(f"❌ Missing configuration for pipeline layer: {layer_name}")

        if not layer_configs:
            raise RuntimeError("❌ No pipeline layers configured! Cannot proceed without sophisticated generation algorithms.")

        # Set up world tier with layers (expects list of tuples)
        self.tier_manager.set_world_tier(layer_configs)

        # Verify configuration
        if not self.tier_manager.is_configured():
            raise RuntimeError("❌ TierManager failed to configure properly! Pipeline system unavailable.")



    def update_chunks(self, camera, screen_width: int = 80, screen_height: int = 50):
        """Predictively load chunks around camera"""
        camera_chunk_x, camera_chunk_y = self.world_to_render_chunk(
            camera.cursor_x, camera.cursor_y)

        # Load immediate area (current screen)
        immediate_distance = max(screen_width // 64, screen_height // 64) + 1

        # Preload extended area (for smooth movement)
        preload_distance = immediate_distance + 2

        # Request chunks in priority order
        for distance in range(preload_distance + 1):
            for dx in range(-distance, distance + 1):
                for dy in range(-distance, distance + 1):
                    if abs(dx) == distance or abs(dy) == distance:  # Only edge chunks
                        chunk_x = camera_chunk_x + dx
                        chunk_y = camera_chunk_y + dy

                        if (chunk_x, chunk_y) not in self.loading_chunks and \
                           (chunk_x, chunk_y) not in self.ready_chunks:
                            from .messages import Priority
                            priority = Priority.HIGH if distance <= immediate_distance else Priority.NORMAL
                            self._request_chunk_async(chunk_x, chunk_y, priority)
                            self.loading_chunks.add((chunk_x, chunk_y))

        # Unload chunks that are too far away to prevent memory bloat
        self._unload_distant_chunks(camera_chunk_x, camera_chunk_y, preload_distance + 3)

    def get_tile(self, x: int, y: int) -> Tile:
        """Non-blocking tile access - always returns immediately"""
        # Check tile cache first
        if (x, y) in self.tile_cache:
            self.cache_hits += 1
            return self.tile_cache[(x, y)]

        # Check if chunk is ready
        chunk_x, chunk_y = self.world_to_render_chunk(x, y)
        if (chunk_x, chunk_y) in self.ready_chunks:
            # Load chunk tiles into cache
            self._cache_chunk_tiles(chunk_x, chunk_y)
            self.cache_hits += 1
            if (x, y) not in self.tile_cache:
                raise RuntimeError(f"❌ Tile ({x}, {y}) not found in cache after loading chunk ({chunk_x}, {chunk_y})")
            return self.tile_cache[(x, y)]

        # Request chunk if not already loading
        if (chunk_x, chunk_y) not in self.loading_chunks:
            from .messages import Priority
            self._request_chunk_async(chunk_x, chunk_y, Priority.NORMAL)
            self.loading_chunks.add((chunk_x, chunk_y))

        # Return placeholder immediately (legitimate for async loading)
        self.cache_misses += 1
        return Tile(x, y, "loading")

    def _cache_chunk_tiles(self, chunk_x: int, chunk_y: int):
        """Load completed chunk tiles into cache"""
        chunk_tiles = self.worker.get_chunk_tiles(chunk_x, chunk_y)
        self.tile_cache.update(chunk_tiles)

    def _request_chunk_async(self, chunk_x: int, chunk_y: int, priority):
        """Request chunk generation asynchronously"""
        self.worker.request_chunk(chunk_x, chunk_y, priority=priority)
        self.chunks_requested += 1

    def _unload_distant_chunks(self, camera_chunk_x: int, camera_chunk_y: int, max_distance: int):
        """Unload chunks that are too far from camera to prevent memory bloat"""
        chunks_to_unload = []

        # Check ready chunks
        for chunk_x, chunk_y in list(self.ready_chunks):
            distance = max(abs(chunk_x - camera_chunk_x), abs(chunk_y - camera_chunk_y))
            if distance > max_distance:
                chunks_to_unload.append((chunk_x, chunk_y))

        # Unload distant chunks
        for chunk_x, chunk_y in chunks_to_unload:
            self.ready_chunks.discard((chunk_x, chunk_y))
            # Remove tiles from tile cache for this chunk
            chunk_bounds = self.get_render_chunk_bounds(chunk_x, chunk_y)
            min_x, min_y, max_x, max_y = chunk_bounds
            for y in range(min_y, max_y + 1):
                for x in range(min_x, max_x + 1):
                    self.tile_cache.pop((x, y), None)

    def get_chunk_tiles(self, chunk_x: int, chunk_y: int) -> Dict[Tuple[int, int], Tile]:
        """Get all tiles in a chunk."""
        return self.worker.get_chunk_tiles(chunk_x, chunk_y)

    def is_chunk_loaded(self, chunk_x: int, chunk_y: int) -> bool:
        """Check if a chunk is loaded."""
        return self.worker.is_chunk_ready(chunk_x, chunk_y)

    def get_loaded_chunks(self) -> set:
        """Get set of loaded chunk coordinates."""
        return self.worker.get_ready_chunks()

    def get_chunk_info(self, world_x: int, world_y: int) -> Dict[str, Any]:
        """Get information about the chunk containing the given world coordinates."""
        chunk_x, chunk_y = self.world_to_render_chunk(world_x, world_y)
        is_loaded = self.is_chunk_loaded(chunk_x, chunk_y)

        return {
            'chunk_x': chunk_x,
            'chunk_y': chunk_y,
            'world_x': world_x,
            'world_y': world_y,
            'is_loaded': is_loaded,
            'chunk_size': self.config.chunk_size
        }

    def process_worker_messages(self):
        """Process completed chunks from worker - call this each frame"""
        from .messages import MessageType

        messages_processed = 0
        while messages_processed < 10:  # Limit processing per frame to avoid blocking
            message = self.message_bus.receive_from_worker(block=False)
            if not message:
                break

            if message.message_type == MessageType.CHUNK_RESPONSE:
                chunk_x, chunk_y = message.payload.chunk_x, message.payload.chunk_y
                if message.payload.success:
                    self.ready_chunks.add((chunk_x, chunk_y))
                    self.chunks_received += 1
                else:
                    # Handle error case - chunk failed to generate
                    pass
                self.loading_chunks.discard((chunk_x, chunk_y))

            elif message.message_type == MessageType.STATUS_UPDATE:
                # Handle worker status updates if needed
                pass

            messages_processed += 1

    def request_chunks(self, chunk_coords: set, priority=None):
        """Request chunks to be loaded."""
        if priority is None:
            from .messages import Priority
            priority = Priority.NORMAL

        for chunk_x, chunk_y in chunk_coords:
            if not self.is_chunk_loaded(chunk_x, chunk_y):
                self._request_chunk_async(chunk_x, chunk_y, priority)
                self.loading_chunks.add((chunk_x, chunk_y))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get world manager statistics."""
        total_requests = self.cache_hits + self.cache_misses
        cache_hit_ratio = self.cache_hits / max(1, total_requests)

        return {
            "available_chunks": len(self.ready_chunks),
            "requested_chunks": self.chunks_requested,
            "loading_chunks": len(self.loading_chunks),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "chunks_requested": self.chunks_requested,
            "chunks_received": self.chunks_received,
            "cache_hit_ratio": cache_hit_ratio,
            "render_chunk_size": self.config.chunk_size,
            "generation_chunk_size": self.config.chunk_size,
            "tile_cache_size": len(self.tile_cache),
            "predictive_loading": True,
            "memory_management": True
        }
    
    def shutdown(self):
        """Shutdown the world manager."""

        if hasattr(self, 'worker'):
            self.worker.stop()

    def get_render_chunks_in_bounds(self, min_x: int, min_y: int, max_x: int, max_y: int) -> set:
        """Get render chunks within bounds."""
        chunks = set()
        for chunk_x in range(min_x, max_x + 1):
            for chunk_y in range(min_y, max_y + 1):
                chunks.add((chunk_x, chunk_y))
        return chunks

    def get_render_chunk_size(self) -> int:
        """Get the render chunk size."""
        return self.config.chunk_size

    def world_to_render_chunk(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Convert world coordinates to render chunk coordinates."""
        chunk_size = self.get_render_chunk_size()
        chunk_x = world_x // chunk_size
        chunk_y = world_y // chunk_size
        return (chunk_x, chunk_y)

    def get_render_chunk_bounds(self, chunk_x: int, chunk_y: int) -> Tuple[int, int, int, int]:
        """Get the world coordinate bounds of a render chunk."""
        chunk_size = self.get_render_chunk_size()
        min_x = chunk_x * chunk_size
        min_y = chunk_y * chunk_size
        max_x = min_x + chunk_size - 1
        max_y = min_y + chunk_size - 1
        return (min_x, min_y, max_x, max_y)

    def get_render_chunk_tiles(self, chunk_x: int, chunk_y: int) -> Dict[Tuple[int, int], Tile]:
        """Get all tiles in a render chunk."""
        return self.get_chunk_tiles(chunk_x, chunk_y)

    def get_chunk_status(self, chunk_x: int, chunk_y: int) -> str:
        """Get the current status of a chunk for debugging"""
        if (chunk_x, chunk_y) in self.ready_chunks:
            return "ready"
        elif (chunk_x, chunk_y) in self.loading_chunks:
            return "loading"
        else:
            return "not_requested"

