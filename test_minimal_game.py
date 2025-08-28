#!/usr/bin/env python3
"""
Minimal game test to isolate the unhashable dict error.
"""

import sys
import os
sys.path.insert(0, 'src')

def test_minimal_game():
    """Test minimal game components to find the error."""
    print("🎮 MINIMAL GAME TEST")
    print("=" * 30)
    
    try:
        import tcod
        from config import get_config
        from camera import Camera
        from world_manager import WorldManager  # Use old world manager
        from generators.world_generator import WorldGenerator
        from render import GameRenderer
        from input_handler import InputHandler
        
        print("✅ All imports successful")
        
        # Load config
        config = get_config()
        print("✅ Config loaded")
        
        # Create components
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
        input_handler = InputHandler(camera)
        
        print("✅ All components created")
        
        # Test basic operations
        cursor_x, cursor_y = camera.get_cursor_position()
        tile = world_manager.get_tile(cursor_x, cursor_y)
        chunk_info = world_manager.get_chunk_info(cursor_x, cursor_y)
        world_stats = world_manager.get_statistics()
        
        print(f"✅ Basic operations successful")
        print(f"  Tile: {tile.tile_type}")
        print(f"  Chunk info: {chunk_info}")
        print(f"  Stats keys: {list(world_stats.keys())}")
        
        # Test render frame (this might be where the error occurs)
        print("\n🎨 Testing render frame...")
        
        # Create a minimal console
        console = tcod.console.Console(80, 50, order="F")
        
        # Test render frame with old system
        try:
            # This is the exact call from game.py that might be causing the error
            renderer.render_frame(
                console=console,
                world_source=world_manager,
                view_center_x=cursor_x,
                view_center_y=cursor_y,
                cursor_tile=tile,
                cursor_position=(cursor_x, cursor_y),
                chunk_info=chunk_info,
                world_stats=world_stats
            )
            print("✅ Render frame successful with old system")
            
        except Exception as e:
            print(f"❌ Render frame failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n✅ Minimal game test passed - error is specific to dual chunk system")
        return True
        
    except Exception as e:
        print(f"\n💥 MINIMAL GAME TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_minimal_game()
    if success:
        print("\n🎯 The error is specific to the dual chunk system")
        print("The basic game components work fine")
    else:
        print("\n❌ Error is in basic game components")
    
    sys.exit(0 if success else 1)
