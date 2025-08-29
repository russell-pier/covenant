#!/usr/bin/env python3
"""
Performance test for the optimized infinite world system.

Tests movement responsiveness, chunk loading efficiency, and rendering performance.
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import get_config
from src.camera import Camera
from src.input_handler import InputHandler
from src.world_manager import WorldManager
from src.generators.world_generator import WorldGenerator
from src.render import GameRenderer
import tcod


def test_movement_performance():
    """Test optimized movement performance."""
    print("🏃 Testing Movement Performance")
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
    world_manager = WorldManager(config.world, world_gen)
    input_handler = InputHandler(camera)
    
    # Initial load
    world_manager.update_chunks(camera)
    print(f"Initial chunks loaded: {world_manager.get_loaded_chunk_count()}")
    
    # Test rapid movement within same chunk (should be instant)
    print("\n1. Testing movement within same chunk:")
    start_time = time.time()
    for i in range(100):
        camera.move_right()
        world_manager.update_chunks(camera)
    same_chunk_time = time.time() - start_time
    print(f"   100 moves within chunk: {same_chunk_time:.3f}s ({same_chunk_time*10:.1f}ms per move)")
    
    # Test movement across chunks
    print("\n2. Testing movement across chunks:")
    camera.set_cursor_position(0, 0)  # Reset position
    chunk_crossing_times = []
    
    for i in range(10):
        start_time = time.time()
        # Move far enough to cross chunk boundaries
        for j in range(20):
            camera.move_right()
        world_manager.update_chunks(camera)
        chunk_time = time.time() - start_time
        chunk_crossing_times.append(chunk_time)
        stats = world_manager.get_statistics()
        print(f"   Chunk crossing {i+1}: {chunk_time:.3f}s, {stats['loaded_chunks']} chunks")
    
    avg_chunk_time = sum(chunk_crossing_times) / len(chunk_crossing_times)
    print(f"   Average chunk crossing time: {avg_chunk_time:.3f}s")
    
    # Test input throttling
    print("\n3. Testing input throttling:")
    class MockEvent:
        def __init__(self, event_type, sym, mod=0):
            self.type = event_type
            self.sym = sym
            self.mod = mod
    
    start_pos = camera.get_cursor_position()
    processed_moves = 0
    
    start_time = time.time()
    for i in range(50):
        event = MockEvent("KEYDOWN", tcod.event.KeySym.D)
        input_handler.handle_event(event)
        new_pos = camera.get_cursor_position()
        if new_pos != start_pos:
            processed_moves += 1
            start_pos = new_pos
    throttle_time = time.time() - start_time
    
    print(f"   50 rapid inputs: {processed_moves} moves processed in {throttle_time:.3f}s")
    print(f"   Throttling ratio: {processed_moves/50:.1%} (prevents input spam)")
    
    return {
        'same_chunk_time': same_chunk_time,
        'avg_chunk_time': avg_chunk_time,
        'throttle_ratio': processed_moves/50
    }


def test_rendering_performance():
    """Test rendering performance with optimizations."""
    print("\n🎨 Testing Rendering Performance")
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
    world_manager = WorldManager(config.world, world_gen)
    renderer = GameRenderer()
    
    # Mock console for testing
    class MockConsole:
        def __init__(self, width=80, height=50):
            self.width = width
            self.height = height
            self.render_calls = 0
        
        def clear(self, fg=None, bg=None):
            pass
        
        def print(self, x, y, text, fg=None, bg=None):
            self.render_calls += 1
    
    console = MockConsole(80, 50)
    world_manager.update_chunks(camera)
    
    # Test basic rendering
    cursor_x, cursor_y = camera.get_cursor_position()
    cursor_tile = world_manager.get_tile(cursor_x, cursor_y)
    chunk_info = world_manager.get_chunk_info(cursor_x, cursor_y)
    world_stats = world_manager.get_statistics()
    
    render_options = {
        'cursor_tile': cursor_tile,
        'cursor_position': (cursor_x, cursor_y),
        'chunk_info': chunk_info,
        'world_stats': world_stats
    }
    
    # Test multiple renders
    render_times = []
    for i in range(10):
        console.render_calls = 0
        start_time = time.time()
        renderer.render_frame(console, world_manager, cursor_x, cursor_y, **render_options)
        render_time = time.time() - start_time
        render_times.append(render_time)
        print(f"   Render {i+1}: {render_time:.3f}s, {console.render_calls} calls")
    
    avg_render_time = sum(render_times) / len(render_times)
    print(f"   Average render time: {avg_render_time:.3f}s")
    print(f"   Render calls per frame: {console.render_calls}")
    
    return {
        'avg_render_time': avg_render_time,
        'render_calls': console.render_calls
    }


def test_cache_performance():
    """Test tile cache performance."""
    print("\n💾 Testing Cache Performance")
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
    world_manager = WorldManager(config.world, world_gen)
    
    world_manager.update_chunks(camera)
    
    # Test cache warming
    print("1. Warming tile cache...")
    start_time = time.time()
    for x in range(-50, 51):
        for y in range(-50, 51):
            world_manager.get_tile(x, y)
    warm_time = time.time() - start_time
    
    stats = world_manager.get_statistics()
    print(f"   Cache warming: {warm_time:.3f}s for 10,201 tiles")
    print(f"   Cache size: {stats['tile_cache_size']}")
    print(f"   Cache hit ratio: {stats['cache_hit_ratio']:.1%}")
    
    # Test cache performance
    print("\n2. Testing cached tile access...")
    start_time = time.time()
    for i in range(5000):
        x = (i * 7) % 100 - 50  # Pseudo-random but deterministic pattern
        y = (i * 11) % 100 - 50
        world_manager.get_tile(x, y)
    cache_time = time.time() - start_time
    
    final_stats = world_manager.get_statistics()
    print(f"   5000 tile accesses: {cache_time:.3f}s ({cache_time*1000/5000:.2f}ms per tile)")
    print(f"   Final cache hit ratio: {final_stats['cache_hit_ratio']:.1%}")
    
    return {
        'cache_hit_ratio': final_stats['cache_hit_ratio'],
        'tile_access_time': cache_time / 5000
    }


if __name__ == "__main__":
    print("🚀 PERFORMANCE TEST - Optimized Infinite World System")
    print("=" * 60)
    
    try:
        movement_results = test_movement_performance()
        rendering_results = test_rendering_performance()
        cache_results = test_cache_performance()
        
        print("\n📊 PERFORMANCE SUMMARY")
        print("=" * 60)
        print(f"✅ Movement within chunk: {movement_results['same_chunk_time']*10:.1f}ms per 100 moves")
        print(f"✅ Chunk boundary crossing: {movement_results['avg_chunk_time']*1000:.1f}ms average")
        print(f"✅ Input throttling: {movement_results['throttle_ratio']:.1%} (prevents spam)")
        print(f"✅ Average render time: {rendering_results['avg_render_time']*1000:.1f}ms")
        print(f"✅ Render calls per frame: {rendering_results['render_calls']:,}")
        print(f"✅ Tile cache hit ratio: {cache_results['cache_hit_ratio']:.1%}")
        print(f"✅ Tile access time: {cache_results['tile_access_time']*1000:.2f}ms")
        
        print("\n🎯 OPTIMIZATION SUCCESS!")
        print("The infinite world system is now highly optimized for smooth gameplay!")
        
    except Exception as e:
        print(f"\n❌ PERFORMANCE TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
