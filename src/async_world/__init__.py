#!/usr/bin/env python3
"""
Async World Generation Package

Provides asynchronous world generation with multi-threading and message passing
for smooth, lag-free gameplay in infinite procedural worlds.

Key Components:
- AsyncWorldManager: Non-blocking world manager for main thread
- WorldGenerationWorker: Background worker thread for world generation
- MessageBus: Thread-safe communication system
- Messages: Type-safe message definitions

Usage:
    from src.async_world import AsyncWorldManager
    
    # Replace synchronous WorldManager with AsyncWorldManager
    world_manager = AsyncWorldManager(world_config)
    
    # Use exactly the same API - it's non-blocking now!
    world_manager.update_chunks(camera)
    tile = world_manager.get_tile(x, y)
    
    # Don't forget to shutdown when done
    world_manager.shutdown()
"""

from .manager import AsyncWorldManager
from .worker import WorldGenerationWorker
from .messages import MessageBus, Message, MessageType, Priority

__all__ = [
    'AsyncWorldManager',
    'WorldGenerationWorker', 
    'MessageBus',
    'Message',
    'MessageType',
    'Priority'
]

__version__ = '1.0.0'
__author__ = 'Covenant World Generation Team'
__description__ = 'Asynchronous world generation system for smooth infinite worlds'
