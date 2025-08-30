#!/usr/bin/env python3
"""
Test script to verify the game renders tiles correctly without pink question marks
"""

def test_game_tile_rendering():
    """Test that the game renders tiles correctly"""
    try:
        from src.config import WorldConfig
        from src.world import WorldManager
        from src.tiles import get_tile_registry
        
        print("🎮 Testing game tile rendering...")
        
        # Test tile registry first
        registry = get_tile_registry()
        print(f"✅ Tile registry loaded with {len(registry.get_available_tiles())} tiles")
        
        # Create world manager
        config = WorldConfig()
        config.pipeline_layers = ["lands_and_seas"]
        config.layer_configs = {"lands_and_seas": {"land_ratio": 5, "algorithm": "cellular_automata"}}
        
        world_manager = WorldManager(config)
        print("✅ WorldManager created")
        
        # Test tile access
        print("\n🔍 Testing tile access:")
        
        # Get some tiles and check their types
        test_positions = [(0, 0), (1, 1), (5, 5), (10, 10)]
        
        for x, y in test_positions:
            tile = world_manager.get_tile(x, y)
            config = registry.get_tile_config(tile.tile_type)
            
            if config.character == "?":
                print(f"  ❌ Tile at ({x}, {y}): type='{tile.tile_type}' -> PINK QUESTION MARK")
            else:
                print(f"  ✅ Tile at ({x}, {y}): type='{tile.tile_type}' -> '{config.character}' {config.background_color}")
        
        # Process messages to see if chunks load
        print("\n⏳ Processing worker messages...")
        import time
        for i in range(10):
            world_manager.process_worker_messages()
            time.sleep(0.1)
        
        # Check tiles again after processing
        print("\n🔍 Re-checking tiles after processing:")
        for x, y in test_positions:
            tile = world_manager.get_tile(x, y)
            config = registry.get_tile_config(tile.tile_type)
            
            if config.character == "?":
                print(f"  ❌ Tile at ({x}, {y}): type='{tile.tile_type}' -> PINK QUESTION MARK")
            else:
                print(f"  ✅ Tile at ({x}, {y}): type='{tile.tile_type}' -> '{config.character}' {config.background_color}")
        
        # Get statistics
        stats = world_manager.get_statistics()
        print(f"\n📊 Statistics:")
        print(f"  Available chunks: {stats['available_chunks']}")
        print(f"  Loading chunks: {stats['loading_chunks']}")
        print(f"  Cache hits: {stats['cache_hits']}")
        print(f"  Cache misses: {stats['cache_misses']}")
        
        # Cleanup
        world_manager.shutdown()
        print("✅ WorldManager shutdown successful")
        
        print("\n🎉 Game tile rendering test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_game_tile_rendering()
