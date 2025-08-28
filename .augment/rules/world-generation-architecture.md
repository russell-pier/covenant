# World Generation Architecture Rules

## Pipeline System Rules

- Use `src/generation/pipeline.py` for core pipeline classes
- Put layers in `src/generation/world/layer_name/` directories
- Inherit all layers from `GenerationLayer` base class
- Use `GenerationData` to pass data between layers
- Configure pipelines in `config.toml` under `[world]` section

## Layer Development Rules

- Create directory: `src/generation/world/my_layer/`
- Required files: `layer.py`, `config.toml`, `test_layer.py`
- Inherit from `GenerationLayer` class
- Implement `process(data, bounds)` method
- Add layer to `WorldTier.create_custom_pipeline()` factory
- Use seeded random generators, never global random
- Preserve existing chunk data from previous layers

## Configuration Rules

- Set `generator_type = "pipeline"` in config.toml
- List layers in `pipeline_layers = ["layer1", "layer2"]`
- Configure each layer in `[world.layer_name]` sections
- Use descriptive parameter names with units in comments
- Provide sensible defaults for all parameters
- Validate parameter ranges in layer `__init__`

## Data Structure Rules

- Use `GenerationData` for all layer communication
- Store chunk data as `chunks[(x,y)] = {properties}`
- Always include: `chunk_x`, `chunk_y`, `chunk_size`, `land_type`
- Add layer to `processed_layers` list after processing
- Use `data.set_chunk_property()` and `data.get_chunk()` methods

## Caching Rules

- Cache results by bounds tuple in `_generation_cache`
- Generate 4x4 regions, not individual chunks
- Check cache before running pipeline
- Use deterministic seeds for reproducible results
- Clear cache when memory limits reached

## Integration Rules

- Use `PipelineWorldGenerator` for game integration
- Configure through `WorldGenerator` class
- Set `visualize=True` for development debugging
- Run `demo_layers.py` to test individual layers
- Update `src/generators/__init__.py` when adding generators
