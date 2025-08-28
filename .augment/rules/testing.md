# Testing Rules

## Required Test Cases

- Test layer creation with valid configuration
- Test deterministic generation with same seeds
- Test different seeds produce different results
- Test configuration validation with invalid parameters
- Test bounds processing covers all chunks in range
- Test data preservation from previous layers
- Test layer adds itself to `processed_layers` list

## Test File Structure

- Create `test_layer.py` in each layer directory
- Use `unittest.TestCase` for test classes
- Set up test fixtures in `setUp()` method
- Use descriptive test method names
- Test both valid and invalid configurations

## Performance Testing

- Test layer performance with large areas
- Set reasonable time limits for completion
- Test memory usage doesn't grow excessively
- Use `time.time()` for duration measurements
- Test with different chunk sizes and bounds

## Integration Testing

- Test layers work together in pipeline sequence
- Test pipeline caching works correctly
- Test visualization mode doesn't break generation
- Test layer dependencies are enforced
- Test configuration loading from TOML

## Validation Testing

- Validate chunk data structure and required fields
- Test statistical distribution matches expected ratios
- Validate coordinate system conversions
- Test error handling with corrupted data
- Test bounds edge cases and empty areas
