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
# Removed dual chunk system - now using fixed chunks
from .tier_manager import TierManager
from .pipeline import GenerationData
from ..config import WorldConfig

# Import the real pipeline system components
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Define Tile class locally to avoid circular imports
class Tile:
    """Represents a single tile in the world."""
    def __init__(self, x: int, y: int, tile_type: str = "land"):
        self.x = x
        self.y = y
        self.tile_type = tile_type

class WorldGenerationWorker:
    """
    Worker thread that handles world generation requests asynchronously.
    
    Runs the world generation pipeline in a separate thread and communicates
    results back to the main thread via message bus.
    """
    
    def __init__(self, world_config: WorldConfig, message_bus: MessageBus, tier_manager: Optional[TierManager] = None, worker_id: str = "worker_1"):
        """
        Initialize the world generation worker.

        Args:
            world_config: World configuration settings
            message_bus: Message bus for communication
            tier_manager: TierManager instance for pipeline coordination
            worker_id: Unique identifier for this worker
        """
        self.world_config = world_config
        self.message_bus = message_bus
        self.worker_id = worker_id
        self.seed = world_config.seed
        self.chunk_size = world_config.chunk_size

        # Use provided TierManager or create a new one
        if tier_manager:
            self.tier_manager = tier_manager
        else:
            self.tier_manager = TierManager()
            # Setup tier manager with world config
            layer_configs = []
            for layer_name in world_config.pipeline_layers:
                layer_config = world_config.layer_configs.get(layer_name, {})
                layer_configs.append((layer_name, layer_config))
            self.tier_manager.set_world_tier(layer_configs)
        
        # Worker state
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Fixed chunk system - all chunks are the same size
        self.chunk_size = world_config.chunk_size

        # Chunk management - caches generated chunks
        self.chunk_cache: OrderedDict[Tuple[int, int], Dict] = OrderedDict()
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
                pass

        self.running = False
    
    def _worker_loop(self):
        """Main worker thread loop."""

        
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
                # Log the error and terminate worker - no silent failures
                error_msg = f"❌ Worker {self.worker_id} encountered fatal error: {e}"
                print(error_msg)
                self.running = False
                raise RuntimeError(error_msg) from e
    
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
        """Handle chunk generation with proper response"""
        request = message.payload
        chunk_x, chunk_y = request.chunk_x, request.chunk_y
        request_id = request.request_id

        # Check if request was cancelled
        if request_id in self.cancelled_requests:
            self.cancelled_requests.discard(request_id)
            self.requests_cancelled += 1
            return

        # Check if chunk is already cached
        chunk_key = (chunk_x, chunk_y)
        if chunk_key in self.chunk_cache:
            # Send cached chunk response immediately
            response = Message.chunk_response(
                chunk_x, chunk_y,
                {"status": "ready"},  # Minimal response data
                request_id,
                0.0,
                True, None, self.worker_id
            )
            self.message_bus.send_to_main(response, block=False)
            return

        # Generate chunk using new fixed chunk system
        self.active_requests.add(request_id)
        start_time = time.time()

        try:
            # Generate chunk using pipeline system
            chunk_data = self._generate_chunk(chunk_x, chunk_y)
            generation_time = time.time() - start_time

            # Cache the chunk
            self.chunk_cache[chunk_key] = chunk_data
            self._enforce_cache_limit()

            # Send success response immediately
            response = Message.chunk_response(
                chunk_x, chunk_y,
                {"status": "ready"},  # Minimal response data
                request_id,
                generation_time,
                True, None, self.worker_id
            )
            self.message_bus.send_to_main(response, block=False)

            # Update statistics
            self.chunks_generated += 1
            self.total_generation_time += generation_time

        except Exception as e:
            generation_time = time.time() - start_time

            # Send error response
            response = Message.chunk_response(
                chunk_x, chunk_y, {}, request_id, generation_time, False, str(e), self.worker_id
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
    
    def _generate_chunk(self, chunk_x: int, chunk_y: int) -> Dict:
        """
        Generate a single chunk using the TierManager pipeline system.

        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate

        Returns:
            Dictionary containing chunk data and tile information
        """
        return self._generate_chunk_data(chunk_x, chunk_y)

    def _generate_chunk_data(self, chunk_x: int, chunk_y: int) -> Dict:
        """
        Generate a single chunk using the TierManager pipeline system.

        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate

        Returns:
            Dictionary containing chunk data and tile information
        """
        # Fixed chunk size - no more dynamic sizing
        chunk_size = self.chunk_size

        # Calculate world bounds for this chunk
        min_world_x = chunk_x * chunk_size
        min_world_y = chunk_y * chunk_size
        max_world_x = min_world_x + chunk_size - 1
        max_world_y = min_world_y + chunk_size - 1

        # Create generation data for the pipeline
        generation_data = GenerationData(
            seed=self.seed,
            chunk_size=chunk_size,
            continental_samples={},
            regional_samples={},
            local_samples={},
            chunks={},
            processed_layers=[],
            custom_data={}
        )

        # Define bounds for pipeline processing (single chunk)
        bounds = (chunk_x, chunk_y, chunk_x, chunk_y)

        # Process through TierManager pipeline
        processed_data = self.tier_manager.process_tiers(generation_data, bounds)

        # Extract tiles from processed data
        chunk_key = (chunk_x, chunk_y)
        if chunk_key not in processed_data.chunks:
            raise RuntimeError(f"❌ Pipeline failed to generate chunk ({chunk_x}, {chunk_y}). "
                             f"Available chunks: {list(processed_data.chunks.keys())}. "
                             f"TierManager configured: {self.tier_manager.is_configured()}")

        chunk_data = processed_data.chunks[chunk_key]

        # Verify pipeline provided tiles
        if 'tiles' not in chunk_data:
            raise RuntimeError(f"❌ Pipeline failed to provide 'tiles' for chunk ({chunk_x}, {chunk_y}). "
                             f"Available data: {list(chunk_data.keys())}")

        # Get tiles from the pipeline
        chunk_tiles = {}
        for (world_x, world_y), tile_type in chunk_data['tiles'].items():
            chunk_tiles[(world_x, world_y)] = {
                'tile_type': tile_type,
                'x': world_x,
                'y': world_y
            }

        # Calculate chunk statistics for debugging
        tile_types = [tile_data['tile_type'] for tile_data in chunk_tiles.values()]
        tile_type_counts = {}
        for tile_type in tile_types:
            tile_type_counts[tile_type] = tile_type_counts.get(tile_type, 0) + 1

        # Create chunk data dictionary
        chunk_result = {
            'chunk_x': chunk_x,
            'chunk_y': chunk_y,
            'chunk_size': chunk_size,
            'tiles': chunk_tiles,
            'metadata': {
                'world_bounds': (min_world_x, min_world_y, max_world_x, max_world_y),
                'tile_type_counts': tile_type_counts,
                'total_tiles': len(chunk_tiles),
                'generated_at': time.time(),
                'pipeline_layers': self.world_config.pipeline_layers.copy()
            }
        }

        return chunk_result
    
    def _enforce_cache_limit(self):
        """Enforce cache size limit using LRU eviction."""
        while len(self.chunk_cache) > self.cache_limit:
            # Remove oldest chunk (first in OrderedDict)
            oldest_chunk = next(iter(self.chunk_cache))
            del self.chunk_cache[oldest_chunk]
    
    def _send_status_update(self):
        """Send status update to main thread."""
        status_msg = Message.status_update(
            message=f"Worker {self.worker_id} active",
            worker_id=self.worker_id,
            chunks_in_queue=len(self.active_requests),
            chunks_generated=self.chunks_generated,
            cache_size=len(self.chunk_cache)
        )
        self.message_bus.send_to_main(status_msg, block=False)
    
    def is_chunk_ready(self, chunk_x: int, chunk_y: int) -> bool:
        """Check if a chunk is ready (cached)."""
        return (chunk_x, chunk_y) in self.chunk_cache

    def get_ready_chunks(self) -> set:
        """Get set of ready chunk coordinates."""
        return set(self.chunk_cache.keys())

    def get_chunk_tiles(self, chunk_x: int, chunk_y: int) -> Dict[Tuple[int, int], Tile]:
        """Get all tiles in a chunk."""
        chunk_key = (chunk_x, chunk_y)
        if chunk_key in self.chunk_cache:
            chunk_data = self.chunk_cache[chunk_key]
            # Convert chunk tiles to Tile objects
            tiles = {}
            for (world_x, world_y), tile_data in chunk_data['tiles'].items():
                tile_type = tile_data['tile_type'] if isinstance(tile_data, dict) else tile_data
                tiles[(world_x, world_y)] = Tile(world_x, world_y, tile_type)
            return tiles
        return {}

    def request_chunk(self, chunk_x: int, chunk_y: int, request_id: Optional[str] = None, priority=None):
        """Request a chunk to be generated."""
        if request_id is None:
            import uuid
            request_id = str(uuid.uuid4())

        if priority is None:
            from .messages import Priority
            priority = Priority.NORMAL

        # Create chunk request message
        from .messages import Message
        request_msg = Message.chunk_request(chunk_x, chunk_y, priority, "main")
        self.message_bus.send_to_worker(request_msg, block=False)

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
            'cache_size': len(self.chunk_cache),
            'active_requests': len(self.active_requests),
            'avg_generation_time': avg_generation_time,
            'total_generation_time': self.total_generation_time
        }
