#!/usr/bin/env python3
"""
Test script to verify the world generation system refactoring works correctly.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work correctly."""
    print("🧪 Testing imports...")
    
    try:
        # Test core world imports
        from src.world import WorldManager, WorldConfig, Tile, TierManager
        print("✅ Core world imports successful")
        
        # Test render imports
        from src.render.render import GameRenderer
        print("✅ Render imports successful")
        
        # Test engine imports
        from src.engine.game import run_game
        print("✅ Engine imports successful")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tier_manager():
    """Test TierManager functionality."""
    print("\n🧪 Testing TierManager...")
    
    try:
        from src.world import TierManager
        
        # Create tier manager
        tier_manager = TierManager()
        
        # Configure world tier
        layer_configs = [
            ("lands_and_seas", {"land_ratio": 3}),
            ("zoom", {"subdivision_factor": 2})
        ]
        tier_manager.set_world_tier(layer_configs, visualize=False)
        
        # Test info retrieval
        world_info = tier_manager.get_world_tier_info()
        tier_summary = tier_manager.get_tier_summary()
        
        print(f"✅ TierManager configured: {world_info['configured']}")
        print(f"✅ Layer count: {world_info['layer_count']}")
        print(f"✅ Is configured: {tier_manager.is_configured()}")
        
        return True
    except Exception as e:
        print(f"❌ TierManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_world_manager():
    """Test WorldManager functionality."""
    print("\n🧪 Testing WorldManager...")
    
    try:
        from src.world import WorldManager, WorldConfig
        
        # Create configuration
        config = WorldConfig()
        config.pipeline_layers = ["lands_and_seas"]
        config.layer_configs = {"lands_and_seas": {"land_ratio": 3}}
        
        # Create world manager
        world_manager = WorldManager(config)
        
        # Test basic operations
        stats = world_manager.get_statistics()
        print(f"✅ WorldManager created successfully")
        print(f"✅ Statistics available: {len(stats)} keys")
        
        # Test tile access (should return placeholder)
        tile = world_manager.get_tile(0, 0)
        print(f"✅ Tile access works: {tile.tile_type}")
        
        # Cleanup
        world_manager.shutdown()
        print("✅ WorldManager shutdown successful")
        
        return True
    except Exception as e:
        print(f"❌ WorldManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Starting refactoring verification tests...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_tier_manager,
        test_world_manager
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Refactoring is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
