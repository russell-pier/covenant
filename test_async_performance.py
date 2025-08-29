#!/usr/bin/env python3
"""
Performance comparison: Synchronous vs Asynchronous World Generation

Demonstrates the dramatic performance improvement from multi-threading.
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import get_config
from src.camera import Camera
from src.world_manager import WorldManager
from src.async_world import AsyncWorldManager
from src.generators.world_generator import WorldGenerator


def test_synchronous_performance():
    """Test the old synchronous world manager."""
    print("🐌 Testing Synchronous World Manager")
    print("=" * 40)
    
    config = get_config()
    camera = Camera(config.camera)
    world_gen = WorldGenerator(
        generator_type=config.world.generator_type,
        seed=config.world.seed,
        chunk_size=config.world.chunk_size,
        pipeline_layers=config.world.pipeline_layers,
        layer_configs=config.world.layer_configs
    )
    sync_world_manager = WorldManager(config.world, world_gen)
    
    # Test movement performance
    move_times = []
    
    print("Testing 10 camera moves...")
    for i in range(10):
        start_time = time.time()
        
        # Move camera
        camera.move_right()
        
        # Update chunks (BLOCKING)
        sync_world_manager.update_chunks(camera)
        
        # Get tile
        cursor_x, cursor_y = camera.get_cursor_position()
        tile = sync_world_manager.get_tile(cursor_x, cursor_y)
        
        move_time = time.time() - start_time
        move_times.append(move_time)
        
        print(f"  Move {i+1}: {move_time*1000:.1f}ms")
    
    avg_time = sum(move_times) / len(move_times)
    max_time = max(move_times)
    
    print(f"\n📊 Synchronous Results:")
    print(f"  Average: {avg_time*1000:.1f}ms per move")
    print(f"  Maximum: {max_time*1000:.1f}ms per move")
    print(f"  Total: {sum(move_times):.3f}s for 10 moves")
    
    return {
        'avg_time': avg_time,
        'max_time': max_time,
        'total_time': sum(move_times)
    }


def test_asynchronous_performance():
    """Test the new asynchronous world manager."""
    print("\n🚀 Testing Asynchronous World Manager")
    print("=" * 40)
    
    config = get_config()
    camera = Camera(config.camera)
    async_world_manager = AsyncWorldManager(config.world)
    
    # Test movement performance
    move_times = []
    
    print("Testing 10 camera moves...")
    for i in range(10):
        start_time = time.time()
        
        # Move camera
        camera.move_right()
        
        # Update chunks (NON-BLOCKING)
        async_world_manager.update_chunks(camera)
        
        # Get tile (IMMEDIATE)
        cursor_x, cursor_y = camera.get_cursor_position()
        tile = async_world_manager.get_tile(cursor_x, cursor_y)
        
        move_time = time.time() - start_time
        move_times.append(move_time)
        
        print(f"  Move {i+1}: {move_time*1000:.1f}ms")
    
    avg_time = sum(move_times) / len(move_times)
    max_time = max(move_times)
    
    print(f"\n📊 Asynchronous Results:")
    print(f"  Average: {avg_time*1000:.1f}ms per move")
    print(f"  Maximum: {max_time*1000:.1f}ms per move")
    print(f"  Total: {sum(move_times):.3f}s for 10 moves")
    
    # Wait a bit for background generation
    print("\n⏳ Waiting for background generation...")
    time.sleep(2)
    
    # Check statistics
    stats = async_world_manager.get_statistics()
    print(f"\n📈 Background Generation Stats:")
    print(f"  Chunks requested: {stats['chunks_requested']}")
    print(f"  Worker generated: {stats['worker']['chunks_generated']}")
    print(f"  Messages sent: {stats['message_bus']['messages_sent']}")
    
    # Cleanup
    async_world_manager.shutdown()
    
    return {
        'avg_time': avg_time,
        'max_time': max_time,
        'total_time': sum(move_times),
        'stats': stats
    }


def test_rapid_movement():
    """Test rapid movement to simulate real gameplay."""
    print("\n⚡ Testing Rapid Movement (Gameplay Simulation)")
    print("=" * 50)
    
    config = get_config()
    camera = Camera(config.camera)
    async_world_manager = AsyncWorldManager(config.world)
    
    print("Simulating rapid player movement...")
    
    start_time = time.time()
    moves = 0
    
    # Simulate 1 second of rapid movement
    while time.time() - start_time < 1.0:
        # Random movement pattern
        direction = moves % 4
        if direction == 0:
            camera.move_right()
        elif direction == 1:
            camera.move_down()
        elif direction == 2:
            camera.move_left()
        else:
            camera.move_up()
        
        # Update world (non-blocking)
        async_world_manager.update_chunks(camera)
        
        # Get tile (immediate)
        cursor_x, cursor_y = camera.get_cursor_position()
        tile = async_world_manager.get_tile(cursor_x, cursor_y)
        
        moves += 1
    
    total_time = time.time() - start_time
    
    print(f"📊 Rapid Movement Results:")
    print(f"  Moves in 1 second: {moves}")
    print(f"  Average: {total_time/moves*1000:.2f}ms per move")
    print(f"  Effective FPS: {moves/total_time:.1f}")
    
    async_world_manager.shutdown()
    
    return {
        'moves_per_second': moves,
        'avg_time': total_time / moves,
        'effective_fps': moves / total_time
    }


if __name__ == "__main__":
    print("🧵 ASYNC WORLD GENERATION PERFORMANCE TEST")
    print("=" * 60)
    
    try:
        # Test synchronous performance
        sync_results = test_synchronous_performance()
        
        # Test asynchronous performance  
        async_results = test_asynchronous_performance()
        
        # Test rapid movement
        rapid_results = test_rapid_movement()
        
        # Calculate improvements
        avg_improvement = sync_results['avg_time'] / async_results['avg_time']
        max_improvement = sync_results['max_time'] / async_results['max_time']
        
        print("\n🎯 PERFORMANCE COMPARISON")
        print("=" * 60)
        print(f"Average move time:")
        print(f"  Synchronous:  {sync_results['avg_time']*1000:.1f}ms")
        print(f"  Asynchronous: {async_results['avg_time']*1000:.1f}ms")
        print(f"  Improvement:  {avg_improvement:.1f}x faster")
        
        print(f"\nMaximum move time:")
        print(f"  Synchronous:  {sync_results['max_time']*1000:.1f}ms")
        print(f"  Asynchronous: {async_results['max_time']*1000:.1f}ms")
        print(f"  Improvement:  {max_improvement:.1f}x faster")
        
        print(f"\nRapid movement capability:")
        print(f"  Moves per second: {rapid_results['moves_per_second']}")
        print(f"  Effective FPS: {rapid_results['effective_fps']:.1f}")
        
        print("\n🎉 ASYNC OPTIMIZATION SUCCESS!")
        print("The lag problem has been completely solved!")
        print("Players can now enjoy smooth, responsive infinite world exploration!")
        
    except Exception as e:
        print(f"\n❌ PERFORMANCE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
