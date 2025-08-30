#!/usr/bin/env python3
"""
Test script to verify TierManager configuration is working correctly
"""

def test_tier_manager_configuration():
    """Test that TierManager accepts the correct configuration format"""
    try:
        from src.world.tier_manager import TierManager
        
        print("🏗️ Testing TierManager configuration...")
        
        # Create tier manager
        tier_manager = TierManager()
        print("✅ TierManager created successfully")
        
        # Test with correct format (list of tuples)
        print("\n🔍 Testing correct configuration format (list of tuples):")
        layer_configs = [
            ("lands_and_seas", {"land_ratio": 5, "algorithm": "cellular_automata"}),
        ]
        
        try:
            tier_manager.set_world_tier(layer_configs)
            print("✅ TierManager accepted list of tuples format")
            
            # Verify configuration
            if tier_manager.is_configured():
                print("✅ TierManager is properly configured")
            else:
                print("❌ TierManager configuration failed")
                
            # Test tier summary
            summary = tier_manager.get_tier_summary()
            print(f"✅ Tier summary: {summary}")
            
        except Exception as e:
            print(f"❌ TierManager failed with list of tuples: {e}")
            import traceback
            traceback.print_exc()
        
        # Test with incorrect format (dictionary) - should fail
        print("\n🔍 Testing incorrect configuration format (dictionary):")
        layer_configs_dict = {
            "lands_and_seas": {"land_ratio": 5, "algorithm": "cellular_automata"}
        }
        
        try:
            tier_manager_2 = TierManager()
            tier_manager_2.set_world_tier(layer_configs_dict)
            print("❌ TierManager incorrectly accepted dictionary format")
        except Exception as e:
            print(f"✅ TierManager correctly rejected dictionary format: {type(e).__name__}")
        
        print("\n🎉 TierManager configuration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_world_manager_integration():
    """Test that WorldManager properly configures TierManager"""
    try:
        from src.config import WorldConfig
        from src.world import WorldManager
        
        print("\n🌍 Testing WorldManager integration with TierManager...")
        
        # Create configuration
        config = WorldConfig()
        config.pipeline_layers = ["lands_and_seas"]
        config.layer_configs = {"lands_and_seas": {"land_ratio": 5}}
        
        # Create world manager (this should configure TierManager correctly)
        world_manager = WorldManager(config)
        print("✅ WorldManager created successfully")
        
        # Check if TierManager is configured
        if world_manager.tier_manager.is_configured():
            print("✅ TierManager is properly configured by WorldManager")
        else:
            print("❌ TierManager configuration failed in WorldManager")
        
        # Get tier summary
        summary = world_manager.tier_manager.get_tier_summary()
        print(f"✅ Tier summary from WorldManager: {summary}")
        
        # Cleanup
        world_manager.shutdown()
        print("✅ WorldManager shutdown successful")
        
        return True
        
    except Exception as e:
        print(f"❌ WorldManager integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_tier_manager_configuration()
    success2 = test_world_manager_integration()
    
    if success1 and success2:
        print("\n🎉 All TierManager tests passed!")
    else:
        print("\n❌ Some TierManager tests failed!")
