# Covenant World Generation Documentation

This directory contains comprehensive documentation for the Covenant world generation system.

## Architecture

- **[Pipeline Architecture](pipeline-architecture.md)**: Overview of the layered generation system, core classes, and data flow

## Layers

### World Tier Layers

- **[Lands and Seas](layers/lands-and-seas.md)**: Foundation layer that determines basic land/water distribution
- **[Zoom](layers/zoom.md)**: Progressive detail refinement through subdivision and cellular automata

### Future Layers

- **Climate**: Temperature and precipitation patterns *(planned)*
- **Biomes**: Forest, desert, grassland distribution *(planned)*
- **Resources**: Ore deposits and resource placement *(planned)*
- **Structures**: Cities, dungeons, and landmarks *(planned)*

## Quick Start

### Basic Configuration

```toml
[world]
generator_type = "pipeline"
seed = 12345
chunk_size = 16
pipeline_layers = ["lands_and_seas", "zoom"]

[world.lands_and_seas]
land_ratio = 2  # 20% land

[world.zoom]
subdivision_factor = 2
land_expansion_threshold = 6
iterations = 2
```

### Running the Pipeline

```python
from src.generators import WorldGenerator

generator = WorldGenerator(
    generator_type="pipeline",
    seed=12345,
    chunk_size=16,
    pipeline_layers=["lands_and_seas", "zoom"],
    layer_configs={
        "lands_and_seas": {"land_ratio": 2},
        "zoom": {"subdivision_factor": 2, "iterations": 2}
    }
)

tile = generator.get_tile(x, y)
```

### Visualization

Enable layer-by-layer visualization:

```python
# Set visualize=True in WorldGenerator
generator = WorldGenerator(..., visualize=True)

# Or run the demo script
python demo_layers.py
```

## Design Principles

### Modularity
Each layer is self-contained with its own configuration, tests, and documentation.

### Configurability
All parameters are exposed through TOML configuration files for easy tuning.

### Determinism
Same seed and configuration always produce identical results.

### Extensibility
New layers can be added without modifying existing code.

### Performance
Efficient caching and batch processing for scalable generation.

## Development

### Adding a New Layer

1. **Create layer directory**: `src/generation/world/my_layer/`
2. **Implement layer class**: Inherit from `GenerationLayer`
3. **Add configuration**: Create `config.toml` with parameters
4. **Write tests**: Comprehensive test coverage
5. **Update integration**: Add to `WorldTier.create_custom_pipeline()`
6. **Document**: Create layer documentation in `docs/layers/`

### Testing

```bash
# Test individual layers
python src/generation/world/lands_and_seas/test_layer.py
python src/generation/world/zoom/test_layer.py

# Test full pipeline
python demo_layers.py

# Test integration
python -c "from src.generators import WorldGenerator; ..."
```

### Configuration Guidelines

- **Use descriptive parameter names**: `land_expansion_threshold` not `threshold`
- **Include comments**: Explain what each parameter does
- **Provide examples**: Show common use cases
- **Set sensible defaults**: Layer should work without configuration
- **Validate inputs**: Check parameter ranges and types

## Examples

### Island World
```toml
[world.lands_and_seas]
land_ratio = 1  # 10% land - scattered islands

[world.zoom]
land_expansion_threshold = 8  # Very conservative expansion
erosion_probability = 0.05    # Minimal erosion
```

### Continental World
```toml
[world.lands_and_seas]
land_ratio = 6  # 60% land - large continents

[world.zoom]
land_expansion_threshold = 3  # Moderate expansion
erosion_probability = 0.15    # Natural coastlines
```

### Fractal Archipelago
```toml
[world.lands_and_seas]
land_ratio = 3  # 30% land

[world.zoom]
subdivision_factor = 2
fractal_perturbation = true
perturbation_strength = 0.4
edge_noise_boost = true
```

## Troubleshooting

### Common Issues

**Pipeline not running**: Check `generator_type = "pipeline"` in config

**No land generated**: Increase `land_ratio` in lands_and_seas layer

**Too much land**: Increase `land_expansion_threshold` in zoom layer

**Blocky terrain**: Add more zoom layers or enable fractal features

**Performance issues**: Reduce `subdivision_factor` or chunk generation area

### Debug Tools

- **Layer visualization**: Set `visualize=True`
- **Demo script**: `python demo_layers.py`
- **Pipeline info**: `generator.get_pipeline_info()`
- **Chunk inspection**: Check `chunk_data` properties

## Contributing

When contributing to the generation system:

1. **Follow the layer pattern**: Each layer in its own directory with code, config, tests, and docs
2. **Maintain determinism**: Same inputs must produce same outputs
3. **Add comprehensive tests**: Cover edge cases and configuration validation
4. **Document thoroughly**: Include usage examples and parameter explanations
5. **Consider performance**: Optimize for large-scale generation

## Future Roadmap

### Short Term
- **Region Tier**: Medium-scale biome and climate generation
- **Performance optimization**: Multi-threading and streaming
- **More algorithms**: Perlin noise, Voronoi diagrams

### Long Term
- **Local Tier**: Structure and detail placement
- **3D generation**: Height maps and elevation
- **Dynamic worlds**: Time-based changes and erosion
- **Multiplayer support**: Consistent generation across clients
