# Layer Development Rules

## Directory Structure Rules

- Create directory: `src/generation/world/my_layer/`
- Required files: `__init__.py`, `layer.py`, `config.toml`, `test_layer.py`
- Export layer class in `__init__.py`
- Put main implementation in `layer.py`
- Define defaults in `config.toml`

## Layer Class Rules

- Inherit from `GenerationLayer`
- Call `super().__init__("layer_name", config)` in constructor
- Load config with `config.get('param', default_value)`
- Validate config in `_validate_config()` method
- Use `self.rng = random.Random()` for deterministic randomness
- Implement `process(data, bounds)` method
- Set seed with `self._set_seed(data.seed, bounds)`
- Process all chunks in bounds range
- Return modified GenerationData

## Configuration Rules

- Use descriptive parameter names
- Provide sensible defaults for all parameters
- Validate parameter ranges in `_validate_config()`
- Group related parameters together
- Include comments explaining parameter purpose and ranges

## Data Handling Rules

- Check for existing chunks with `data.get_chunk(x, y)`
- Preserve existing data with `existing_chunk.copy()`
- Add new properties without overwriting existing ones
- Always include required fields: `chunk_x`, `chunk_y`, `chunk_size`, `land_type`
- Use `data.set_chunk_data(x, y, chunk_data)` to store results

## Algorithm Rules

- Support multiple algorithms with `algorithm` parameter
- Validate algorithm selection in `_validate_config()`
- Use separate methods for each algorithm implementation
- Set deterministic seeds with chunk coordinates
- Use `self.rng` for all random operations, never global random

## Testing Rules

- Create `test_layer.py` with comprehensive test coverage
- Test deterministic generation with same seeds
- Test different seeds produce different results
- Test configuration validation with invalid parameters
- Test bounds processing covers all chunks in range
- Test data preservation from previous layers
- Test layer adds itself to `processed_layers` list

## Integration Rules

- Add layer to `WorldTier.create_custom_pipeline()` factory method
- Import layer class in factory function
- Handle layer configuration from TOML
- Update `src/generation/world/__init__.py` exports
- Test layer works in pipeline sequence with other layers