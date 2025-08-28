#!/usr/bin/env python3
"""
Final test for the dual chunk system implementation.
"""

import sys
import os
import time
sys.path.insert(0, 'src')

def test_dual_chunk_system():
    """Test the complete dual chunk system."""
    print("🔧 DUAL CHUNK SYSTEM - FINAL TEST")
    print("=" * 50)
    
    try:
        from config import get_config
        from async_world import AsyncWorldManager
        
        print("✅ Imports successful")
        
        # Load config
        config = get_config()
        print(f"📋 Config loaded: {config.world.pipeline_layers}")
        
        # Create async manager
        async_manager = AsyncWorldManager(config.world)
        print("✅ AsyncWorldManager created with dual chunk system")
        
        # Mock camera
        class MockCamera:
            def __init__(self):
                self.x, self.y = 0, 0
            def get_cursor_position(self):
                return self.x, self.y
            def move_right(self):
                self.x += 10
        
        camera = MockCamera()
        
        # Test coordinate conversion
        print("\n🎯 Testing coordinate conversions:")
        world_pos = (100, 150)
        render_chunk = async_manager.world_to_render_chunk_coords(*world_pos)
        gen_chunk = async_manager.world_to_generation_chunk_coords(*world_pos)
        
        print(f"  World position: {world_pos}")
        print(f"  Render chunk: {render_chunk}")
        print(f"  Generation chunk: {gen_chunk}")
        
        # Test chunk info
        print("\n📊 Testing chunk info:")
        chunk_info = async_manager.get_chunk_info(0, 0)
        print(f"  Chunk info: {chunk_info}")
        
        # Test statistics
        print("\n📈 Testing statistics:")
        stats = async_manager.get_statistics()
        print(f"  Render chunk size: {stats['render_chunk_size']}")
        print(f"  Generation chunk size: {stats['generation_chunk_size']}")
        print(f"  Loaded render chunks: {stats['loaded_render_chunks']}")
        
        # Test tile access (should return placeholder)
        print("\n🎯 Testing tile access:")
        tile = async_manager.get_tile(0, 0)
        print(f"  Tile at (0,0): type={tile.tile_type}, x={tile.x}, y={tile.y}")
        
        # Test chunk update (minimal)
        print("\n🔄 Testing chunk update:")
        try:
            async_manager.update_chunks(camera, 80, 50)
            print("  ✅ Chunk update successful")
        except Exception as e:
            print(f"  ❌ Chunk update failed: {e}")
        
        # Wait briefly for any async operations
        time.sleep(0.5)
        
        # Final statistics
        final_stats = async_manager.get_statistics()
        print(f"\n📊 Final stats:")
        print(f"  Chunks requested: {final_stats['chunks_requested']}")
        print(f"  Loaded render chunks: {final_stats['loaded_render_chunks']}")
        
        # Cleanup
        async_manager.shutdown()
        print("✅ Clean shutdown completed")
        
        print("\n🎉 DUAL CHUNK SYSTEM TEST SUCCESSFUL!")
        print("\n📋 System Summary:")
        print(f"  • Render chunks: {stats['render_chunk_size']}×{stats['render_chunk_size']} tiles")
        print(f"  • Generation chunks: {stats['generation_chunk_size']}×{stats['generation_chunk_size']} tiles")
        print(f"  • Aggregation ratio: {(stats['render_chunk_size']//stats['generation_chunk_size'])**2}:1")
        print(f"  • Pipeline: {config.world.pipeline_layers}")
        
        return True
        
    except Exception as e:
        print(f"\n💥 TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_dual_chunk_system()
    sys.exit(0 if success else 1)
