---
type: "agent_requested"
description: "Rules for configuring world generation parameters, TOML conventions, and layer configuration patterns"
---

# Configuration Rules

## Main Configuration Rules

- Set `generator_type = "pipeline"` in config.toml
- List layers in `pipeline_layers = ["layer1", "layer2"]`
- Configure each layer in `[world.layer_name]` sections
- Use `seed` for deterministic generation
- Set `chunk_size` for tile resolution

## Parameter Naming Rules

- Use descriptive names: `land_expansion_threshold` not `threshold`
- Use consistent scales: 1-10 for ratios, 0.0-1.0 for probabilities
- Use neighbor counts for thresholds: `expansion_threshold = 6`
- Use positive integers for iterations: `iterations = 3`
- Use descriptive booleans: `use_multi_pass = true`

## Parameter Documentation Rules

- Include units/ranges in comments: `# 1-10 scale where 1 = 10%`
- Explain parameter purpose: `# Controls how aggressively land expands`
- Provide valid ranges: `# Valid range: 0-8 neighbors`
- Group related parameters together
- Use consistent comment style

## Layer Configuration Rules

- Put layer config in `[world.layer_name]` sections
- Provide sensible defaults for all optional parameters
- Support algorithm selection with `algorithm = "name"`
- Use subsections for algorithm-specific config: `[world.layer.algorithm]`
- Group multi-pass parameters with prefixes: `pass_1_iterations`, `pass_2_iterations`

## Validation Rules

- Validate parameter ranges in layer `__init__` method
- Raise `ValueError` for invalid parameter values
- Check algorithm names against supported list
- Validate required parameters are present
- Provide clear error messages with expected ranges

## Loading Rules

- Access layer config with `config.get('param', default_value)`
- Load algorithm-specific config from subsections
- Extract layer configs in `src/config.py` during loading
- Pass layer configs to `WorldGenerator` constructor
- Store configs in `WorldConfig.layer_configs` dictionary
