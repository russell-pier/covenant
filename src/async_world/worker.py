#!/usr/bin/env python3
"""
World Generation Worker Thread

Runs world generation in a separate thread to avoid blocking the main rendering thread.
Communicates via message bus for smooth, responsive gameplay.
"""

import threading
import time
from typing import Dict, Set, Optional, Tuple
from collections import OrderedDict

from .messages import MessageBus, Message, MessageType, Priority
from .dual_chunk_system import DualChunkManager, GenerationChunk, RenderChunk

# Handle imports for both direct execution and package import
try:
    from ..generators.world_generator import WorldGenerator
    from ..config import WorldConfig
except ImportError:
    try:
        # Fallback for direct execution
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from generators.world_generator import WorldGenerator
        from config import WorldConfig
    except ImportError:
        # Final fallback - create minimal implementations for testing
        print("Warning: Using minimal implementations for testing")

        class Tile:
            def __init__(self, x, y, tile_type="stone"):
                self.x = x
                self.y = y
                self.tile_type = tile_type

        class WorldGenerator:
            def __init__(self, **kwargs):
                pass
            def get_tile(self, x, y):
                return Tile(x, y, "water" if (x + y) % 3 == 0 else "stone")

        class WorldConfig:
            def __init__(self):
                self.chunk_size = 32
                self.pipeline_layers = ["lands_and_seas", "zoom"]


class WorldGenerationWorker:
    """
    Worker thread that handles world generation requests asynchronously.
    
    Runs the world generation pipeline in a separate thread and communicates
    results back to the main thread via message bus.
    """
    
    def __init__(self, world_config: WorldConfig, message_bus: MessageBus, worker_id: str = "worker_1"):
        """
        Initialize the world generation worker.
        
        Args:
            world_config: World configuration settings
            message_bus: Message bus for communication
            worker_id: Unique identifier for this worker
        """
        self.world_config = world_config
        self.message_bus = message_bus
        self.worker_id = worker_id
        
        # Create world generator for this worker
        self.world_generator = WorldGenerator(
            generator_type=world_config.generator_type,
            seed=world_config.seed,
            chunk_size=world_config.chunk_size,
            pipeline_layers=world_config.pipeline_layers,
            layer_configs=world_config.layer_configs,
            visualize=False  # Disable visualization in worker thread
        )
        
        # Worker state
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Dual chunk system
        self.render_chunk_size = 64  # Fixed render chunk size
        self.dual_chunk_manager = DualChunkManager(render_chunk_size=self.render_chunk_size)

        # Calculate final generation chunk size
        self.final_generation_chunk_size = self.dual_chunk_manager.calculate_final_generation_chunk_size(
            world_config.chunk_size, world_config.pipeline_layers
        )

        # Chunk management - now caches render chunks
        self.render_chunk_cache: OrderedDict[Tuple[int, int], RenderChunk] = OrderedDict()
        self.cache_limit = world_config.chunk_cache_limit
        
        # Request tracking
        self.active_requests: Set[str] = set()
        self.cancelled_requests: Set[str] = set()
        
        # Statistics
        self.chunks_generated = 0
        self.total_generation_time = 0.0
        self.requests_processed = 0
        self.requests_cancelled = 0
    
    def start(self):
        """Start the worker thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._worker_loop, name=f"WorldWorker-{self.worker_id}")
        self.thread.daemon = True
        self.thread.start()
        print(f"World generation worker {self.worker_id} started")
    
    def stop(self, timeout: float = 5.0):
        """
        Stop the worker thread.
        
        Args:
            timeout: Maximum time to wait for worker to stop
        """
        if not self.running:
            return
        
        # Send shutdown message
        shutdown_msg = Message.shutdown(f"Stop requested for {self.worker_id}")
        self.message_bus.send_to_worker(shutdown_msg, block=False)
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=timeout)
            if self.thread.is_alive():
                print(f"Warning: Worker {self.worker_id} did not stop within {timeout}s")
        
        self.running = False
        print(f"World generation worker {self.worker_id} stopped")
    
    def _worker_loop(self):
        """Main worker thread loop."""
        print(f"Worker {self.worker_id} loop started")
        
        while self.running:
            try:
                # Receive message from main thread
                message = self.message_bus.receive_from_main(block=True, timeout=1.0)
                
                if message is None:
                    continue  # Timeout, check if still running
                
                # Process message
                self._process_message(message)
                
                # Send periodic status updates
                if self.requests_processed % 10 == 0:
                    self._send_status_update()
                
            except Exception as e:
                print(f"Worker {self.worker_id} error: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"Worker {self.worker_id} loop ended")
    
    def _process_message(self, message: Message):
        """Process a message from the main thread."""
        if message.message_type == MessageType.SHUTDOWN:
            print(f"Worker {self.worker_id} received shutdown signal")
            self.running = False
            
        elif message.message_type == MessageType.CHUNK_REQUEST:
            self._handle_chunk_request(message)
            
        elif message.message_type == MessageType.CHUNK_CANCEL:
            self._handle_chunk_cancel(message)
            
        else:
            print(f"Worker {self.worker_id} received unknown message type: {message.message_type}")
    
    def _handle_chunk_request(self, message: Message):
        """Handle a chunk generation request."""
        request = message.payload
        chunk_x, chunk_y = request.chunk_x, request.chunk_y
        request_id = request.request_id
        
        # Check if request was cancelled
        if request_id in self.cancelled_requests:
            self.cancelled_requests.discard(request_id)
            self.requests_cancelled += 1
            return
        
        # Check if render chunk is already cached
        render_chunk_key = (chunk_x, chunk_y)
        if render_chunk_key in self.render_chunk_cache:
            # Send cached render chunk
            render_chunk = self.render_chunk_cache[render_chunk_key]
            render_chunk_data = {
                'chunk_x': render_chunk.chunk_x,
                'chunk_y': render_chunk.chunk_y,
                'chunk_size': render_chunk.chunk_size,
                'aggregated_tiles': render_chunk.aggregated_tiles,
                'metadata': render_chunk.metadata,
                'generation_chunks': []
            }
            response = Message.chunk_response(
                chunk_x, chunk_y, render_chunk_data, request_id, 0.0, True, None, self.worker_id
            )
            self.message_bus.send_to_main(response, block=False)
            return
        
        # Generate render chunk by aggregating generation chunks
        self.active_requests.add(request_id)
        start_time = time.time()

        try:
            # Generate render chunk using dual chunk system
            render_chunk = self._generate_render_chunk(chunk_x, chunk_y)
            generation_time = time.time() - start_time

            # Cache the render chunk
            self.render_chunk_cache[render_chunk_key] = render_chunk
            self._enforce_cache_limit()

            # Send response with render chunk data (convert to serializable format)
            render_chunk_data = {
                'chunk_x': render_chunk.chunk_x,
                'chunk_y': render_chunk.chunk_y,
                'chunk_size': render_chunk.chunk_size,
                'aggregated_tiles': render_chunk.aggregated_tiles,
                'metadata': render_chunk.metadata,
                'generation_chunks': []  # Don't send full generation chunks to save bandwidth
            }

            response = Message.chunk_response(
                chunk_x, chunk_y, render_chunk_data, request_id, generation_time, True, None, self.worker_id
            )
            self.message_bus.send_to_main(response, block=False)

            # Update statistics
            self.chunks_generated += 1
            self.total_generation_time += generation_time
            
        except Exception as e:
            generation_time = time.time() - start_time
            error_msg = f"Failed to generate chunk ({chunk_x}, {chunk_y}): {e}"
            print(f"Worker {self.worker_id}: {error_msg}")
            
            # Send error response
            response = Message.chunk_response(
                chunk_x, chunk_y, {}, request_id, generation_time, False, error_msg, self.worker_id
            )
            self.message_bus.send_to_main(response, block=False)
        
        finally:
            self.active_requests.discard(request_id)
            self.requests_processed += 1
    
    def _handle_chunk_cancel(self, message: Message):
        """Handle a chunk cancellation request."""
        cancel = message.payload
        request_id = cancel.request_id
        
        if request_id in self.active_requests:
            # Mark as cancelled (can't stop generation in progress, but won't send response)
            self.cancelled_requests.add(request_id)
        
        self.requests_cancelled += 1
    
    def _generate_render_chunk(self, render_chunk_x: int, render_chunk_y: int) -> RenderChunk:
        """
        Generate a render chunk by aggregating multiple generation chunks.

        Args:
            render_chunk_x: Render chunk X coordinate
            render_chunk_y: Render chunk Y coordinate

        Returns:
            Complete render chunk with aggregated generation data
        """
        # Get all generation chunks that overlap with this render chunk
        generation_chunk_coords = self.dual_chunk_manager.get_generation_chunks_for_render_chunk(
            render_chunk_x, render_chunk_y, self.final_generation_chunk_size
        )

        # Generate all required generation chunks
        generation_chunks = []

        for gen_chunk_x, gen_chunk_y in generation_chunk_coords:
            gen_chunk = self._generate_generation_chunk(gen_chunk_x, gen_chunk_y)
            generation_chunks.append(gen_chunk)

        # Aggregate generation chunks into render chunk
        render_chunk = self.dual_chunk_manager.aggregate_generation_chunks(
            generation_chunks, render_chunk_x, render_chunk_y
        )

        return render_chunk

    def _generate_generation_chunk(self, chunk_x: int, chunk_y: int) -> GenerationChunk:
        """
        Generate a single chunk using the full world generation pipeline.

        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate

        Returns:
            Dictionary containing chunk data and tile information
        """
        # Calculate effective chunk size after zoom layers
        effective_chunk_size = self.world_config.chunk_size
        zoom_count = sum(1 for layer_name in self.world_config.pipeline_layers if layer_name == "zoom")
        for _ in range(zoom_count):
            effective_chunk_size //= 2

        # Calculate world bounds for this chunk
        min_world_x = chunk_x * effective_chunk_size
        min_world_y = chunk_y * effective_chunk_size
        max_world_x = min_world_x + effective_chunk_size - 1
        max_world_y = min_world_y + effective_chunk_size - 1

        # Generate all tiles in this chunk using the full pipeline
        # This ensures the world generation pipeline (lands_and_seas -> zoom -> zoom) runs properly
        chunk_tiles = {}

        for world_y in range(min_world_y, max_world_y + 1):
            for world_x in range(min_world_x, max_world_x + 1):
                # Use the world generator to get the tile (runs full pipeline)
                tile = self.world_generator.get_tile(world_x, world_y)
                chunk_tiles[(world_x, world_y)] = {
                    'tile_type': tile.tile_type,
                    'x': tile.x,
                    'y': tile.y
                }

        # Calculate chunk statistics for debugging
        tile_types = [tile_data['tile_type'] for tile_data in chunk_tiles.values()]
        tile_type_counts = {}
        for tile_type in tile_types:
            tile_type_counts[tile_type] = tile_type_counts.get(tile_type, 0) + 1

        # Create GenerationChunk object
        metadata = {
            'world_bounds': (min_world_x, min_world_y, max_world_x, max_world_y),
            'tile_type_counts': tile_type_counts,
            'total_tiles': len(chunk_tiles),
            'generated_at': time.time(),
            'pipeline_layers': self.world_config.pipeline_layers.copy()
        }

        return GenerationChunk(
            chunk_x=chunk_x,
            chunk_y=chunk_y,
            chunk_size=effective_chunk_size,
            tiles=chunk_tiles,
            metadata=metadata
        )
    
    def _enforce_cache_limit(self):
        """Enforce cache size limit using LRU eviction."""
        while len(self.render_chunk_cache) > self.cache_limit:
            # Remove oldest render chunk (first in OrderedDict)
            oldest_chunk = next(iter(self.render_chunk_cache))
            del self.render_chunk_cache[oldest_chunk]
    
    def _send_status_update(self):
        """Send status update to main thread."""
        status_msg = Message.status_update(
            message=f"Worker {self.worker_id} active",
            worker_id=self.worker_id,
            chunks_in_queue=len(self.active_requests),
            chunks_generated=self.chunks_generated,
            cache_size=len(self.render_chunk_cache)
        )
        self.message_bus.send_to_main(status_msg, block=False)
    
    def get_statistics(self) -> Dict:
        """Get worker statistics."""
        avg_generation_time = (
            self.total_generation_time / max(1, self.chunks_generated)
        )
        
        return {
            'worker_id': self.worker_id,
            'running': self.running,
            'chunks_generated': self.chunks_generated,
            'requests_processed': self.requests_processed,
            'requests_cancelled': self.requests_cancelled,
            'cache_size': len(self.render_chunk_cache),
            'active_requests': len(self.active_requests),
            'avg_generation_time': avg_generation_time,
            'total_generation_time': self.total_generation_time
        }
