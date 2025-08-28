#!/usr/bin/env python3
"""
Comprehensive test for the infinite procedural world generation system.

Tests all components working together: camera, input handling, world management,
chunk loading/unloading, and rendering integration.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import get_config
from src.camera import Camera
from src.input_handler import InputHandler
from src.world_manager import WorldManager
from src.generators.world_generator import WorldGenerator
from src.render import GameRenderer
import tcod


def test_infinite_world_system():
    """Test the complete infinite world system."""
    print("🌍 Testing Infinite Procedural World Generation System")
    print("=" * 60)
    
    # 1. Test Configuration System
    print("\n1. Testing Configuration System...")
    config = get_config()
    assert config.world.render_distance == 3, "Render distance should be 3"
    assert config.world.chunk_cache_limit == 100, "Cache limit should be 100"
    assert config.camera.move_speed == 1, "Move speed should be 1"
    assert config.camera.fast_move_speed == 5, "Fast move speed should be 5"
    print("   ✓ Configuration loaded correctly")
    
    # 2. Test Camera System
    print("\n2. Testing Camera System...")
    camera = Camera(config.camera)
    initial_pos = camera.get_cursor_position()
    assert initial_pos == (0, 0), f"Initial position should be (0,0), got {initial_pos}"
    
    # Test movement
    camera.move_right()
    assert camera.get_cursor_position() == (1, 0), "Right movement failed"
    camera.move_up()
    assert camera.get_cursor_position() == (1, -1), "Up movement failed"
    camera.move_left(fast_mode=True)
    assert camera.get_cursor_position() == (-4, -1), "Fast left movement failed"
    print("   ✓ Camera movement working correctly")
    
    # 3. Test World Generation
    print("\n3. Testing World Generation...")
    world_generator = WorldGenerator(
        generator_type=config.world.generator_type,
        seed=config.world.seed,
        chunk_size=config.world.chunk_size,
        pipeline_layers=config.world.pipeline_layers,
        layer_configs=config.world.layer_configs
    )
    
    # Test tile generation
    tile = world_generator.get_tile(0, 0)
    assert tile.tile_type in ['stone', 'water'], f"Invalid tile type: {tile.tile_type}"
    print("   ✓ World generation working correctly")
    
    # 4. Test World Manager
    print("\n4. Testing World Manager...")
    world_manager = WorldManager(config.world, world_generator)
    
    # Reset camera for testing
    camera.set_cursor_position(0, 0)
    
    # Test initial chunk loading
    world_manager.update_chunks(camera)
    initial_chunks = world_manager.get_loaded_chunk_count()
    assert initial_chunks > 0, "No chunks loaded initially"
    print(f"   ✓ Initial chunks loaded: {initial_chunks}")
    
    # Test chunk loading with camera movement
    camera.set_cursor_position(100, 100)  # Move far away
    world_manager.update_chunks(camera)
    new_chunks = world_manager.get_loaded_chunk_count()
    print(f"   ✓ Chunks after movement: {new_chunks}")
    
    # Test tile access
    tile = world_manager.get_tile(100, 100)
    assert tile.tile_type in ['stone', 'water'], "Tile access failed"
    print("   ✓ Tile access working correctly")
    
    # Test statistics
    stats = world_manager.get_statistics()
    assert 'loaded_chunks' in stats, "Statistics missing loaded_chunks"
    assert 'cache_hit_ratio' in stats, "Statistics missing cache_hit_ratio"
    print(f"   ✓ Statistics: {stats['loaded_chunks']} chunks, {stats['cache_hit_ratio']:.1%} cache hit ratio")
    
    # 5. Test Input Handler
    print("\n5. Testing Input Handler...")
    camera.set_cursor_position(0, 0)  # Reset position
    input_handler = InputHandler(camera)
    
    # Test callback setup
    regenerate_called = False
    def test_regenerate():
        nonlocal regenerate_called
        regenerate_called = True
    
    input_handler.set_regenerate_callback(test_regenerate)
    
    # Mock event class
    class MockEvent:
        def __init__(self, event_type, sym, mod=0):
            self.type = event_type
            self.sym = sym
            self.mod = mod
    
    # Test movement keys
    w_event = MockEvent("KEYDOWN", tcod.event.KeySym.W)
    input_handler.handle_event(w_event)
    assert camera.get_cursor_position() == (0, -1), "W key movement failed"
    
    # Test regeneration key
    r_event = MockEvent("KEYDOWN", tcod.event.KeySym.R)
    input_handler.handle_event(r_event)
    assert regenerate_called, "Regeneration callback not called"
    
    print("   ✓ Input handling working correctly")
    
    # 6. Test Rendering Integration
    print("\n6. Testing Rendering Integration...")
    renderer = GameRenderer()
    
    # Create a mock console for testing
    class MockConsole:
        def __init__(self, width=80, height=50):
            self.width = width
            self.height = height
            self.prints = []
        
        def clear(self, fg=None, bg=None):
            pass
        
        def print(self, x, y, text, fg=None, bg=None):
            self.prints.append({'x': x, 'y': y, 'text': text, 'fg': fg, 'bg': bg})
    
    console = MockConsole()
    camera.set_cursor_position(50, 50)
    
    # Test rendering with world manager
    cursor_tile = world_manager.get_tile(50, 50)
    chunk_info = world_manager.get_chunk_info(50, 50)
    world_stats = world_manager.get_statistics()
    
    render_options = {
        'cursor_tile': cursor_tile,
        'cursor_position': (50, 50),
        'chunk_info': chunk_info,
        'world_stats': world_stats
    }
    
    # This should not crash
    try:
        renderer.render_frame(console, world_manager, 50, 50, **render_options)
        print("   ✓ Rendering integration working correctly")
    except Exception as e:
        print(f"   ✗ Rendering failed: {e}")
        raise
    
    # 7. Test Performance
    print("\n7. Testing Performance...")
    import time
    
    # Test chunk loading performance
    start_time = time.time()
    for i in range(10):
        camera.set_cursor_position(i * 50, i * 50)
        world_manager.update_chunks(camera)
    chunk_time = time.time() - start_time
    print(f"   ✓ Chunk loading: {chunk_time:.3f}s for 10 camera moves")
    
    # Test tile access performance
    start_time = time.time()
    for i in range(1000):
        world_manager.get_tile(i % 100, i % 100)
    tile_time = time.time() - start_time
    print(f"   ✓ Tile access: {tile_time:.3f}s for 1000 tile requests")
    
    # Final statistics
    final_stats = world_manager.get_statistics()
    print(f"\n📊 Final Statistics:")
    print(f"   • Loaded chunks: {final_stats['loaded_chunks']}")
    print(f"   • Total chunks loaded: {final_stats['chunks_loaded_total']}")
    print(f"   • Total chunks unloaded: {final_stats['chunks_unloaded_total']}")
    print(f"   • Cache hit ratio: {final_stats['cache_hit_ratio']:.1%}")
    print(f"   • Tile cache size: {final_stats['tile_cache_size']}")
    
    print("\n🎉 All tests passed! Infinite world system is working correctly!")
    return True


if __name__ == "__main__":
    try:
        test_infinite_world_system()
        print("\n✅ SUCCESS: Infinite procedural world generation system is ready!")
        print("\nTo run the game:")
        print("  python main.py")
        print("\nControls:")
        print("  • WASD or Arrow Keys: Move camera")
        print("  • Shift + Movement: Fast movement")
        print("  • R: Regenerate world")
        print("  • F1: Toggle debug info")
        print("  • F2: Toggle coordinates")
        print("  • F3: Toggle chunk debug overlay")
        print("  • F4: Toggle FPS")
        print("  • Ctrl+Q or ESC: Exit")
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
