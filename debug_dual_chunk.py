#!/usr/bin/env python3
"""
Debug script to isolate the unhashable dict error.
"""

import sys
import os
sys.path.insert(0, 'src')

def debug_dual_chunk_error():
    """Debug the unhashable dict error step by step."""
    print("🔍 DEBUGGING DUAL CHUNK SYSTEM ERROR")
    print("=" * 50)
    
    try:
        # Step 1: Test basic imports
        print("Step 1: Testing imports...")
        from config import get_config
        from async_world import AsyncWorldManager
        from camera import Camera
        print("✅ Imports successful")
        
        # Step 2: Test config loading
        print("\nStep 2: Testing config...")
        config = get_config()
        print("✅ Config loaded")
        
        # Step 3: Test async manager creation
        print("\nStep 3: Testing AsyncWorldManager creation...")
        async_manager = AsyncWorldManager(config.world)
        print("✅ AsyncWorldManager created")
        
        # Step 4: Test camera creation
        print("\nStep 4: Testing Camera creation...")
        camera = Camera(config.camera)
        print("✅ Camera created")
        
        # Step 5: Test basic tile access (should return placeholder)
        print("\nStep 5: Testing basic tile access...")
        tile = async_manager.get_tile(0, 0)
        print(f"✅ Tile access successful: {tile.tile_type}")
        
        # Step 6: Test chunk info
        print("\nStep 6: Testing chunk info...")
        chunk_info = async_manager.get_chunk_info(0, 0)
        print(f"✅ Chunk info successful: {chunk_info}")
        
        # Step 7: Test statistics
        print("\nStep 7: Testing statistics...")
        stats = async_manager.get_statistics()
        print(f"✅ Statistics successful: {len(stats)} keys")
        
        # Step 8: Test chunk update (this might be where the error occurs)
        print("\nStep 8: Testing chunk update...")
        try:
            async_manager.update_chunks(camera, 80, 50)
            print("✅ Chunk update successful")
        except Exception as e:
            print(f"❌ Chunk update failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Step 9: Test render frame components
        print("\nStep 9: Testing render components...")
        try:
            from render import GameRenderer
            renderer = GameRenderer()
            print("✅ Renderer created")
            
            # Test getting render data
            cursor_x, cursor_y = camera.get_cursor_position()
            cursor_tile = async_manager.get_tile(cursor_x, cursor_y)
            chunk_info = async_manager.get_chunk_info(cursor_x, cursor_y)
            world_stats = async_manager.get_statistics()
            
            print(f"✅ Render data prepared")
            print(f"  Cursor tile: {cursor_tile.tile_type}")
            print(f"  Chunk info keys: {list(chunk_info.keys())}")
            print(f"  World stats keys: {list(world_stats.keys())}")
            
        except Exception as e:
            print(f"❌ Render component test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Step 10: Test status display
        print("\nStep 10: Testing status display...")
        try:
            from ui.status_display import StatusDisplay
            status_display = StatusDisplay()
            print("✅ Status display created")
            
            # Test the specific method that might be causing issues
            # This is likely where the unhashable dict error occurs
            
        except Exception as e:
            print(f"❌ Status display test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Cleanup
        async_manager.shutdown()
        print("\n✅ All tests passed - error might be in game loop")
        
        return True
        
    except Exception as e:
        print(f"\n💥 DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = debug_dual_chunk_error()
    if success:
        print("\n🎯 Error is likely in the game loop or event handling")
        print("The dual chunk system itself appears to be working correctly")
    else:
        print("\n❌ Error found in dual chunk system components")
    
    sys.exit(0 if success else 1)
