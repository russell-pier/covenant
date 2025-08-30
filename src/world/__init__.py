#!/usr/bin/env python3
"""
World Generation Package

Provides clean, production-ready world generation with async chunk loading,
pipeline-based terrain generation, and proper multi-tier architecture.

Key Components:
- WorldManager: Single entry point for world access
- TierManager: Coordinates multi-tier generation pipeline
- WorldGenerationWorker: Background worker thread for world generation
- MessageBus: Thread-safe communication system
- Messages: Type-safe message definitions

Usage:
    from src.world import WorldManager, WorldConfig

    # Create world manager with configuration
    config = WorldConfig()
    world_manager = WorldManager(config)

    # Use the clean API
    world_manager.update_chunks(camera)
    tile = world_manager.get_tile(x, y)

    # Don't forget to shutdown when done
    world_manager.shutdown()
"""

from .world_manager import WorldManager
from .tier_manager import TierManager
from .worker import WorldGenerationWorker, Tile
from .messages import MessageBus, Message, MessageType, Priority

__all__ = [
    'WorldManager',
    'Tile',
    'TierManager',
    'WorldGenerationWorker',
    'MessageBus',
    'Message',
    'MessageType',
    'Priority'
]

__version__ = '1.0.0'
__author__ = 'Covenant World Generation Team'
__description__ = 'Asynchronous world generation system for smooth infinite worlds'
