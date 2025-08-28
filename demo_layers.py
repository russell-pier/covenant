#!/usr/bin/env python3
"""
Demo script to run each pipeline layer once with on-screen visualization.
"""

from src.generation.pipeline import GenerationData, WorldGenerationPipeline
from src.generation.world import WorldTier
from src.config import get_config

def run_layer_demo():
    """Run each layer once and show the progression."""
    
    print('🎬 Running Single Layer Demo')
    print('=' * 50)
    
    config = get_config()
    
    # Create individual layers
    layer_configs = [
        ('lands_and_seas', config.world.layer_configs.get('lands_and_seas', {})),
        ('zoom', config.world.layer_configs.get('zoom', {})),
        ('zoom', config.world.layer_configs.get('zoom', {}))
    ]
    
    # Initialize data
    data = GenerationData(seed=config.world.seed, chunk_size=config.world.chunk_size)
    bounds = (0, 0, 1, 1)  # 2x2 chunk area
    
    print(f'Starting with seed: {config.world.seed}')
    print(f'Chunk size: {config.world.chunk_size}')
    print(f'Bounds: {bounds}')
    print()
    
    # Run each layer individually
    for i, (layer_name, layer_config) in enumerate(layer_configs):
        print(f'🔄 Running Layer {i+1}/3: {layer_name}')
        
        # Create the layer
        if layer_name == 'lands_and_seas':
            from src.generation.world.lands_and_seas import LandsAndSeasLayer
            layer = LandsAndSeasLayer(layer_config)
        elif layer_name == 'zoom':
            from src.generation.world.zoom import ZoomLayer
            layer = ZoomLayer(layer_config)
        else:
            continue
        
        # Process the layer
        data = layer.process(data, bounds)
        
        # Analyze results
        land_count = sum(1 for chunk in data.chunks.values() if chunk.get('land_type') == 'land')
        water_count = len(data.chunks) - land_count
        land_ratio = land_count / (land_count + water_count) if (land_count + water_count) > 0 else 0
        
        print(f'   Result: {len(data.chunks)} chunks, {land_count} land, {water_count} water ({land_ratio:.1%} land)')
        
        # Show visual pattern
        if data.chunks:
            chunk_coords = list(data.chunks.keys())
            min_x = min(x for x, y in chunk_coords)
            max_x = max(x for x, y in chunk_coords)
            min_y = min(y for x, y in chunk_coords)
            max_y = max(y for x, y in chunk_coords)
            
            print(f'   Grid ({max_x - min_x + 1}x{max_y - min_y + 1}):')
            
            # Show a sample of the pattern (limit to reasonable size)
            display_size = 16
            for y in range(min(max_y, min_y + display_size - 1), min_y - 1, -1):
                line = '   '
                for x in range(min_x, min(max_x + 1, min_x + display_size)):
                    chunk_key = (x, y)
                    if chunk_key in data.chunks:
                        land_type = data.chunks[chunk_key].get('land_type', 'water')
                        line += '█' if land_type == 'land' else '~'
                    else:
                        line += '?'
                print(line)
        
        print()
    
    print('✅ Layer demo complete!')
    print(f'Final result: {len(data.chunks)} chunks with {land_ratio:.1%} land')

if __name__ == '__main__':
    run_layer_demo()
