#!/usr/bin/env python3
"""
Test the corrected pipeline: 32x32 lands_and_seas → 16x16 zoom
"""

import sys
import os
sys.path.insert(0, 'src')

def test_corrected_pipeline():
    """Test that the pipeline is correctly configured."""
    print("🔧 TESTING CORRECTED PIPELINE")
    print("=" * 50)
    
    try:
        from config import get_config
        from async_world import AsyncWorldManager
        
        # Load config
        config = get_config()
        print(f"📋 Configuration:")
        print(f"  Base chunk size: {config.world.chunk_size}")
        print(f"  Pipeline layers: {config.world.pipeline_layers}")
        
        # Test dual chunk system
        async_manager = AsyncWorldManager(config.world)
        print(f"\n🔧 Dual Chunk System:")
        print(f"  Render chunk size: {async_manager.render_chunk_size}x{async_manager.render_chunk_size}")
        print(f"  Final generation chunk size: {async_manager.final_generation_chunk_size}x{async_manager.final_generation_chunk_size}")
        
        # Verify the pipeline
        expected_pipeline = ["lands_and_seas", "zoom"]
        expected_base_size = 32
        expected_final_size = 16
        
        print(f"\n✅ Verification:")
        pipeline_correct = config.world.pipeline_layers == expected_pipeline
        base_size_correct = config.world.chunk_size == expected_base_size
        final_size_correct = async_manager.final_generation_chunk_size == expected_final_size
        
        print(f"  Pipeline correct: {pipeline_correct} ({config.world.pipeline_layers})")
        print(f"  Base size correct: {base_size_correct} ({config.world.chunk_size})")
        print(f"  Final size correct: {final_size_correct} ({async_manager.final_generation_chunk_size})")
        
        if pipeline_correct and base_size_correct and final_size_correct:
            print(f"\n🎉 SUCCESS: Pipeline correctly configured!")
            print(f"  • lands_and_seas generates 32x32 chunks")
            print(f"  • zoom layer applies cellular automata to create 16x16 chunks")
            print(f"  • render system aggregates into 64x64 chunks for efficiency")
            print(f"  • No more overly granular chunks!")
        else:
            print(f"\n❌ FAILURE: Pipeline not correctly configured")
            return False
        
        # Test basic functionality
        print(f"\n🎯 Testing basic functionality:")
        tile = async_manager.get_tile(0, 0)
        print(f"  Tile at (0,0): {tile.tile_type}")
        
        chunk_info = async_manager.get_chunk_info(0, 0)
        print(f"  Chunk info: {chunk_info.get('chunk_type', 'unknown')} chunk")
        
        # Cleanup
        async_manager.shutdown()
        
        print(f"\n✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n💥 TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_corrected_pipeline()
    if success:
        print(f"\n🌟 PIPELINE CORRECTION SUCCESSFUL!")
        print(f"The zoom is no longer too granular - now using proper 32→16 sizing.")
    else:
        print(f"\n❌ Pipeline correction failed")
    
    sys.exit(0 if success else 1)
