#!/usr/bin/env python3
"""
TierManager - Coordinates multi-tier generation pipeline

Manages the relationship between WorldTier, RegionTier, and LocalTier
for scalable world generation across different levels of detail.
"""

from typing import Dict, List, Tuple, Optional, Any
from .pipeline import GenerationPipeline, GenerationData
from .world_tier import WorldTier


class TierManager:
    """
    Coordinates multi-tier generation pipeline.
    
    Manages WorldTier (current: lands_and_seas → zoom layers)
    Prepared for future RegionTier and LocalTier.
    Each tier operates on appropriate chunk scales.
    """
    
    def __init__(self):
        """Initialize the tier manager."""
        # Tiers - only WorldTier implemented for now
        self.world_tier: Optional[GenerationPipeline] = None
        self.region_tier: Optional[GenerationPipeline] = None  # Future
        self.local_tier: Optional[GenerationPipeline] = None   # Future
        
        # Configuration tracking
        self._world_tier_config: Optional[List[Tuple[str, Dict[str, Any]]]] = None
    
    def set_world_tier(self, layer_configs: List[Tuple[str, Dict[str, Any]]]):
        """
        Set the world tier pipeline with configured layers.

        Args:
            layer_configs: List of (layer_name, config_dict) tuples
        """
        self.world_tier = WorldTier.create_custom_pipeline(layer_configs)
        self._world_tier_config = layer_configs
    
    def set_region_tier(self, layer_configs: List[Tuple[str, Dict[str, Any]]]):
        """
        Set the region tier pipeline (future implementation).
        
        Args:
            layer_configs: List of (layer_name, config_dict) tuples
        """
        # TODO: Implement when RegionTier is available
        raise NotImplementedError("RegionTier not yet implemented")
    
    def set_local_tier(self, layer_configs: List[Tuple[str, Dict[str, Any]]]):
        """
        Set the local tier pipeline (future implementation).
        
        Args:
            layer_configs: List of (layer_name, config_dict) tuples
        """
        # TODO: Implement when LocalTier is available
        raise NotImplementedError("LocalTier not yet implemented")
    
    def process_tiers(self, data: GenerationData, bounds: Tuple[int, int, int, int]) -> GenerationData:
        """
        Process data through all configured tiers in sequence.
        
        Args:
            data: The generation data to process
            bounds: (min_chunk_x, min_chunk_y, max_chunk_x, max_chunk_y)
            
        Returns:
            The processed generation data
        """
        # Process through world tier
        if self.world_tier:
            data = self.world_tier.process(data, bounds)
        
        # TODO: Process through region tier
        if self.region_tier:
            data = self.region_tier.process(data, bounds)
        
        # TODO: Process through local tier  
        if self.local_tier:
            data = self.local_tier.process(data, bounds)
        
        return data
    
    def get_world_tier_info(self) -> Dict[str, Any]:
        """Get information about the world tier configuration."""
        if not self.world_tier:
            return {"configured": False}
        
        return {
            "configured": True,
            "layer_count": len(self.world_tier.layers),
            "layer_names": [layer.name for layer in self.world_tier.layers],
            "config": self._world_tier_config
        }
    
    def get_tier_summary(self) -> Dict[str, Any]:
        """Get summary of all configured tiers."""
        return {
            "world_tier": self.get_world_tier_info(),
            "region_tier": {"configured": self.region_tier is not None},
            "local_tier": {"configured": self.local_tier is not None}
        }
    
    def is_configured(self) -> bool:
        """Check if at least one tier is configured."""
        return self.world_tier is not None
    
    def clear_all_tiers(self):
        """Clear all tier configurations."""
        self.world_tier = None
        self.region_tier = None
        self.local_tier = None
        self._world_tier_config = None


# Example usage and testing
if __name__ == "__main__":
    # Create tier manager
    tier_manager = TierManager()

    # Test configuration
    layer_configs = [
        ("lands_and_seas", {"land_ratio": 3}),
        ("zoom", {"subdivision_factor": 2})
    ]

    tier_manager.set_world_tier(layer_configs)

    # Test info retrieval
    world_info = tier_manager.get_world_tier_info()
    tier_summary = tier_manager.get_tier_summary()
