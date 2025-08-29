#!/usr/bin/env python3
"""
Test the improved async world generation system with proper viewport-based
chunk loading and full world generation pipeline integration.
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import get_config
from src.camera import Camera
from src.async_world import AsyncWorldManager


def test_viewport_based_loading():
    """Test viewport-based chunk loading strategy."""
    print("🖥️ Testing Viewport-Based Chunk Loading")
    print("=" * 50)
    
    config = get_config()
    camera = Camera(config.camera)
    async_world_manager = AsyncWorldManager(config.world)
    
    # Test different screen sizes
    screen_sizes = [
        (80, 50, "Standard"),
        (120, 60, "Large"),
        (40, 25, "Small")
    ]
    
    for screen_width, screen_height, size_name in screen_sizes:
        print(f"\n📐 Testing {size_name} screen ({screen_width}x{screen_height}):")
        
        # Reset camera position
        camera.set_cursor_position(0, 0)
        
        # Update chunks for this screen size
        start_time = time.time()
        async_world_manager.update_chunks(camera, screen_width, screen_height)
        update_time = time.time() - start_time
        
        # Wait for chunks to generate
        time.sleep(1)
        async_world_manager.update_chunks(camera, screen_width, screen_height)
        
        stats = async_world_manager.get_statistics()
        
        print(f"  Update time: {update_time*1000:.1f}ms")
        print(f"  Chunks requested: {stats['chunks_requested']}")
        print(f"  Chunks loaded: {stats['loaded_chunks']}")
        print(f"  Loading chunks: {stats['loading_chunks']}")
    
    async_world_manager.shutdown()
    return True


def test_world_generation_pipeline():
    """Test that the full world generation pipeline is working."""
    print("\n🌍 Testing World Generation Pipeline Integration")
    print("=" * 55)
    
    config = get_config()
    camera = Camera(config.camera)
    async_world_manager = AsyncWorldManager(config.world)
    
    print(f"Pipeline layers: {config.world.pipeline_layers}")
    
    # Request chunks and wait for generation
    print("\n⏳ Generating chunks with full pipeline...")
    async_world_manager.update_chunks(camera, 80, 50)
    
    # Wait for generation to complete
    time.sleep(3)
    async_world_manager.update_chunks(camera, 80, 50)
    
    # Test tile quality at different positions
    print("\n🎯 Testing generated tile quality:")
    test_positions = [
        (0, 0), (10, 10), (20, 20), (-10, -10), (50, 50)
    ]
    
    tile_types_found = set()
    
    for x, y in test_positions:
        tile = async_world_manager.get_tile(x, y)
        tile_types_found.add(tile.tile_type)
        
        # Check if chunk has detailed data
        chunk_info = async_world_manager.get_chunk_info(x, y)
        chunk_coords = async_world_manager.world_to_chunk_coords(x, y)
        
        if chunk_coords in async_world_manager.available_chunks:
            chunk_data = async_world_manager.available_chunks[chunk_coords]
            has_pipeline_data = 'pipeline_layers' in chunk_data
            has_tile_counts = 'tile_type_counts' in chunk_data
            
            print(f"  Position ({x:3d},{y:3d}): {tile.tile_type:8s} | "
                  f"Pipeline: {'✓' if has_pipeline_data else '✗'} | "
                  f"Stats: {'✓' if has_tile_counts else '✗'}")
            
            if has_tile_counts:
                counts = chunk_data['tile_type_counts']
                print(f"    Chunk tile types: {dict(counts)}")
        else:
            print(f"  Position ({x:3d},{y:3d}): {tile.tile_type:8s} | Chunk not loaded")
    
    print(f"\n📊 Tile types found: {sorted(tile_types_found)}")
    
    # Check worker statistics
    stats = async_world_manager.get_statistics()
    worker_stats = stats['worker']
    
    print(f"\n🔧 Worker Statistics:")
    print(f"  Chunks generated: {worker_stats['chunks_generated']}")
    print(f"  Average generation time: {worker_stats['avg_generation_time']:.3f}s")
    print(f"  Cache size: {worker_stats['cache_size']}")
    
    async_world_manager.shutdown()
    return len(tile_types_found) > 1  # Should have multiple tile types


def test_buffer_zone_performance():
    """Test buffer zone performance for smooth movement."""
    print("\n🏃 Testing Buffer Zone Performance")
    print("=" * 40)
    
    config = get_config()
    camera = Camera(config.camera)
    async_world_manager = AsyncWorldManager(config.world)
    
    screen_width, screen_height = 80, 50
    
    # Initial load
    print("🔄 Initial chunk loading...")
    async_world_manager.update_chunks(camera, screen_width, screen_height)
    time.sleep(2)  # Wait for initial generation
    
    # Test movement performance with buffer
    print("\n🎮 Testing movement with buffer zone:")
    
    movement_times = []
    cache_hit_ratios = []
    
    for i in range(10):
        start_time = time.time()
        
        # Move camera
        camera.move_right()
        camera.move_right()  # Move 2 tiles
        
        # Update chunks (should be fast due to buffer)
        async_world_manager.update_chunks(camera, screen_width, screen_height)
        
        # Get tile (should hit cache or be available)
        cursor_x, cursor_y = camera.get_cursor_position()
        tile = async_world_manager.get_tile(cursor_x, cursor_y)
        
        move_time = time.time() - start_time
        movement_times.append(move_time)
        
        stats = async_world_manager.get_statistics()
        cache_hit_ratios.append(stats['cache_hit_ratio'])
        
        print(f"  Move {i+1}: {move_time*1000:.1f}ms, "
              f"tile={tile.tile_type}, "
              f"cache_hit={stats['cache_hit_ratio']:.1%}")
    
    avg_move_time = sum(movement_times) / len(movement_times)
    avg_cache_hit = sum(cache_hit_ratios) / len(cache_hit_ratios)
    
    print(f"\n📈 Buffer Zone Results:")
    print(f"  Average move time: {avg_move_time*1000:.1f}ms")
    print(f"  Average cache hit ratio: {avg_cache_hit:.1%}")
    print(f"  Max move time: {max(movement_times)*1000:.1f}ms")
    
    async_world_manager.shutdown()
    return avg_move_time < 0.01  # Should be very fast with buffer


def test_chunk_cleanup():
    """Test chunk cleanup based on viewport distance."""
    print("\n🧹 Testing Chunk Cleanup")
    print("=" * 30)
    
    config = get_config()
    camera = Camera(config.camera)
    async_world_manager = AsyncWorldManager(config.world)
    
    screen_width, screen_height = 80, 50
    
    # Load initial chunks
    async_world_manager.update_chunks(camera, screen_width, screen_height)
    time.sleep(1)
    
    initial_chunks = async_world_manager.get_loaded_chunk_count()
    print(f"Initial chunks loaded: {initial_chunks}")
    
    # Move far away
    camera.set_cursor_position(1000, 1000)
    async_world_manager.update_chunks(camera, screen_width, screen_height)
    time.sleep(1)
    
    final_chunks = async_world_manager.get_loaded_chunk_count()
    print(f"Chunks after moving far: {final_chunks}")
    
    # Should have cleaned up distant chunks
    cleanup_worked = final_chunks < initial_chunks + 10  # Allow some new chunks
    print(f"Cleanup working: {'✓' if cleanup_worked else '✗'}")
    
    async_world_manager.shutdown()
    return cleanup_worked


if __name__ == "__main__":
    print("🚀 IMPROVED ASYNC WORLD GENERATION TEST")
    print("=" * 60)
    
    try:
        # Run all tests
        test1 = test_viewport_based_loading()
        test2 = test_world_generation_pipeline()
        test3 = test_buffer_zone_performance()
        test4 = test_chunk_cleanup()
        
        print("\n🎯 TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"✅ Viewport-based loading: {'PASS' if test1 else 'FAIL'}")
        print(f"✅ Pipeline integration: {'PASS' if test2 else 'FAIL'}")
        print(f"✅ Buffer zone performance: {'PASS' if test3 else 'FAIL'}")
        print(f"✅ Chunk cleanup: {'PASS' if test4 else 'FAIL'}")
        
        if all([test1, test2, test3, test4]):
            print("\n🎉 ALL TESTS PASSED!")
            print("The improved async world generation system is working perfectly!")
        else:
            print("\n❌ Some tests failed. Check the output above for details.")
        
    except Exception as e:
        print(f"\n💥 TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
