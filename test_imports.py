#!/usr/bin/env python3
"""
Simple test script to verify imports work correctly.
"""

def test_basic_imports():
    """Test basic Python functionality."""
    print("🧪 Testing basic Python...")
    print("✅ Basic Python working")

def test_world_imports():
    """Test world package imports."""
    print("\n🧪 Testing world imports...")
    try:
        from src.world import WorldManager, WorldConfig, Tile
        print("✅ World imports successful")
        
        # Test basic functionality
        config = WorldConfig()
        manager = WorldManager(config)
        tile = manager.get_tile(0, 0)
        stats = manager.get_statistics()
        manager.shutdown()
        
        print(f"✅ WorldManager basic test passed: {tile.tile_type}")
        return True
    except Exception as e:
        print(f"❌ World imports failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_game_imports():
    """Test game imports."""
    print("\n🧪 Testing game imports...")
    try:
        from src.engine.game import run_game
        print("✅ Game imports successful")
        return True
    except Exception as e:
        print(f"❌ Game imports failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Testing imports and basic functionality...")
    print("=" * 50)
    
    test_basic_imports()
    
    world_ok = test_world_imports()
    game_ok = test_game_imports()
    
    print("\n" + "=" * 50)
    if world_ok and game_ok:
        print("🎉 All tests passed! The refactoring is working.")
        return 0
    else:
        print("❌ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
