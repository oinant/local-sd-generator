# JSON Config System - Phase 2: Configuration

**Status:** ✅ Complete
**Completed:** 2025-10-01
**Tests:** 86 passing
**Component:** cli

---

## Overview

Phase 2 implemented the JSON configuration system with comprehensive validation. Users can now define generation runs in JSON files with clear error messages for invalid configurations.

---

## Sub-Features

### SF-7: Global Config File

**Priority:** 6
**Complexity:** Low
**Status:** ✅ Complete

#### Description

Global configuration file to specify configs and outputs directories.

#### Implementation

**Files created:**
- `CLI/config/global_config.py` - Global config management
- `tests/test_global_config.py` - 26 tests

**Features:**
1. **File Location Search Order**
   - `.sdgen_config.json` in project root
   - `~/.sdgen_config.json` in user home
   - Default values if neither found

2. **Schema**
   ```json
   {
     "configs_dir": "/absolute/path/to/configs",
     "output_dir": "/absolute/path/to/outputs",
     "api_url": "http://127.0.0.1:7860"
   }
   ```

3. **Automatic Creation**
   - Creates with defaults on first run
   - User confirmation before creation

4. **Defaults**
   - `configs_dir`: `./configs`
   - `output_dir`: `./apioutput`
   - `api_url`: `http://127.0.0.1:7860`

#### API

```python
from CLI.config.global_config import load_global_config

# Load global config (creates with defaults if not found)
config = load_global_config()

print(config.configs_dir)  # Path
print(config.output_dir)   # Path
print(config.api_url)      # str
```

#### Success Criteria

- ✅ Global config file located and loaded
- ✅ Defaults used if not found
- ✅ Created automatically with user confirmation
- ✅ Used by CLI for paths

---

### SF-1: JSON Config Loading & Validation

**Priority:** 3
**Complexity:** High
**Status:** ✅ Complete

#### Description

Load and validate JSON configuration files with clear error messages.

#### Implementation

**Files created:**
- `CLI/config/config_schema.py` - Dataclass schema definitions
- `CLI/config/config_loader.py` - Loading & validation logic
- `tests/test_config_schema.py` - 29 tests
- `tests/test_config_loader.py` - 31 tests
- `CLI/test_integration_phase2.py` - Integration tests

**Features:**
1. **Comprehensive Schema Validation**
   - Required fields presence
   - Type validation (str, int, float, dict, list)
   - Enum validation (generation modes, seed modes)
   - File path validation (existence, readability)
   - Placeholder validation (template ↔ variations match)

2. **Clear Error Messages**
   ```
   ValidationError: Placeholder 'Lighting' in prompt template has no corresponding variation file.

   Prompt template: "portrait, {Expression}, {Angle}, {Lighting}, beautiful"
   Found placeholders: ['Expression', 'Angle', 'Lighting']
   Defined variations: ['Expression', 'Angle']

   Solution: Add "Lighting" to variations object or remove from template.
   ```

3. **Dataclass-Based Schema**
   ```python
   @dataclass
   class GenerationConfig:
       version: str
       name: Optional[str]
       description: Optional[str]
       model: ModelConfig
       prompt: PromptConfig
       variations: Dict[str, str]
       generation: GenerationSettings
       parameters: GenerationParameters
       output: OutputConfig
   ```

4. **Validation Categories**
   - Schema validation (structure, types)
   - File validation (paths exist, readable)
   - Placeholder validation (template ↔ variations)
   - Parameter validation (ranges, samplers)
   - Enum validation (mode values)

#### API

```python
from CLI.config.config_loader import ConfigLoader
from pathlib import Path

# Load and validate config
try:
    config = ConfigLoader.load_config_from_file(
        Path("configs/anime_portraits.json")
    )
    print(f"✓ Config loaded: {config.name}")

except ValidationError as e:
    print(f"✗ Validation failed:")
    for error in e.errors:
        print(f"  {error.field}: {error.message}")
        if error.suggestion:
            print(f"    → {error.suggestion}")
```

#### Success Criteria

- ✅ Valid configs load without errors
- ✅ Invalid configs fail fast with clear messages
- ✅ All file paths validated before generation starts
- ✅ Placeholder/variation mismatches detected
- ✅ 100% test coverage on validation logic

---

## JSON Config Schema

**Complete schema example:**

```json
{
  "version": "1.0",
  "name": "Anime Portrait Generation",
  "description": "Character portraits with various expressions and angles",

  "model": {
    "checkpoint": "animePastelDream_v1.safetensors"
  },

  "prompt": {
    "template": "masterpiece, {Expression}, {Angle}, beautiful anime girl, detailed",
    "negative": "low quality, blurry, bad anatomy, text, watermark"
  },

  "variations": {
    "Expression": "/absolute/path/to/expressions.txt",
    "Angle": "/absolute/path/to/angles.txt"
  },

  "generation": {
    "mode": "combinatorial",
    "seed_mode": "progressive",
    "seed": 42,
    "max_images": -1
  },

  "parameters": {
    "width": 512,
    "height": 768,
    "steps": 30,
    "cfg_scale": 7.0,
    "sampler": "DPM++ 2M Karras",
    "batch_size": 1,
    "batch_count": 1
  },

  "output": {
    "session_name": "anime_test_v2",
    "filename_keys": ["Expression", "Angle"]
  }
}
```

---

## Validation Examples

### Valid Config

```json
{
  "version": "1.0",
  "prompt": {
    "template": "{Expression}, beautiful",
    "negative": "low quality"
  },
  "variations": {
    "Expression": "/path/to/expressions.txt"
  },
  "generation": {
    "mode": "combinatorial",
    "seed_mode": "progressive",
    "seed": 42,
    "max_images": -1
  },
  "parameters": {...},
  "output": {...}
}
```

**Result:** ✓ Config loaded successfully

### Missing Placeholder

```json
{
  "prompt": {
    "template": "{Expression}, {Angle}, beautiful"
  },
  "variations": {
    "Expression": "/path/to/expressions.txt"
    // Missing "Angle"
  }
}
```

**Error:**
```
ValidationError:
  Field: prompt.template
  Message: Placeholder 'Angle' has no corresponding variation file
  Suggestion: Add "Angle" to variations object or remove from template
```

### Invalid File Path

```json
{
  "variations": {
    "Expression": "/nonexistent/file.txt"
  }
}
```

**Error:**
```
ValidationError:
  Field: variations.Expression
  Message: File not found at '/nonexistent/file.txt'
  Suggestion: Check file path exists and is readable
```

### Invalid Enum Value

```json
{
  "generation": {
    "mode": "combinatorials"  // Typo
  }
}
```

**Error:**
```
ValidationError:
  Field: generation.mode
  Message: Invalid mode 'combinatorials' (typo?)
  Suggestion: Valid modes: 'combinatorial', 'random', 'ask'
```

---

## Testing

**Total:** 86 tests passing ✅

**Coverage:**
- `test_global_config.py`: 26 tests
  - File location and search order
  - Default value loading
  - Config creation and saving
  - Path validation
  - URL validation

- `test_config_schema.py`: 29 tests
  - Dataclass instantiation
  - Type conversions (JSON → Python)
  - Optional field handling
  - Nested object validation

- `test_config_loader.py`: 31 tests
  - Valid config loading
  - Invalid JSON handling
  - Missing required fields
  - Type mismatch errors
  - Enum validation
  - File path validation
  - Placeholder validation
  - Numeric range validation
  - Comprehensive error messages

**Integration tests:**
- `CLI/test_integration_phase2.py`
  - End-to-end config loading
  - Validation with real files
  - Error handling

**Run tests:**
```bash
pytest tests/test_global_config.py tests/test_config_schema.py tests/test_config_loader.py -v
```

---

## Usage Examples

### Create Test Config

**File:** `configs/test_config_phase2.json`

```json
{
  "version": "1.0",
  "name": "Test Config - Phase 2",
  "description": "Testing JSON config loading and validation",

  "prompt": {
    "template": "masterpiece, {Expression}, {Angle}, beautiful portrait",
    "negative": "low quality, blurry"
  },

  "variations": {
    "Expression": "/path/to/expressions.txt",
    "Angle": "/path/to/angles.txt"
  },

  "generation": {
    "mode": "combinatorial",
    "seed_mode": "progressive",
    "seed": 42,
    "max_images": -1
  },

  "parameters": {
    "width": 512,
    "height": 768,
    "steps": 20,
    "cfg_scale": 7.0,
    "sampler": "Euler a",
    "batch_size": 1,
    "batch_count": 1
  },

  "output": {
    "session_name": "phase2_test",
    "filename_keys": ["Expression", "Angle"]
  }
}
```

### Load and Validate

```python
from CLI.config.config_loader import ConfigLoader
from pathlib import Path

# Load config
config = ConfigLoader.load_config_from_file(
    Path("configs/test_config_phase2.json")
)

# Access fields
print(f"Config: {config.name}")
print(f"Prompt: {config.prompt.template}")
print(f"Mode: {config.generation.mode}")
print(f"Variations: {list(config.variations.keys())}")
```

---

## Test Variation Files

Created test variation files for integration testing:

**`variations/test_expressions.txt`:**
```
happy→smiling, cheerful expression
sad→sad, melancholic look
neutral→neutral expression
```

**`variations/test_angles.txt`:**
```
front→front view, facing camera
side→side view, profile
back→back view
```

---

## Documentation

**User Guides:**
- [JSON Config System](../../cli/usage/json-config-system.md) - Complete user guide
- [Getting Started](../../cli/usage/getting-started.md) - Basic usage

**Technical Docs:**
- [Config System](../../cli/technical/config-system.md) - Implementation details
- [Architecture](../../cli/technical/architecture.md) - System overview

---

## Commits

- feat(config): Add Phase 2 - SF-7 Global Config & SF-1 Config Loading/Validation

---

## Lessons Learned

### What Went Well

1. **Dataclass Schema**
   - Type-safe, clear structure
   - No external dependencies
   - IDE autocomplete support
   - Easy to extend

2. **Comprehensive Validation**
   - Clear, actionable error messages
   - Validates everything before generation
   - Catches errors early
   - Prevents runtime failures

3. **Test Coverage**
   - 86 tests, all passing
   - Edge cases covered
   - Integration tests validate real usage

4. **Documentation-First**
   - Spec written before implementation
   - Clear success criteria
   - Examples for every feature

### Challenges

1. **Error Message Quality**
   - Challenge: Make errors actionable
   - Solution: Include field path, message, suggestion

2. **Placeholder Validation**
   - Challenge: Complex regex parsing
   - Solution: Reuse existing `extract_placeholders_with_limits()`

3. **Multiple Validation Layers**
   - Challenge: Avoid duplicate checks
   - Solution: Clear validation pipeline

### Improvements for Next Phase

1. **Relative Path Support** (v2.0)
   - Currently: Absolute paths only
   - Future: Relative to config file or global configs_dir

2. **Config Templates** (v2.0)
   - Base configs that can be extended
   - Reduce duplication

3. **Variable Substitution** (v2.0)
   - `${variable}` syntax in prompts/paths
   - More flexible configs

---

## Next Steps

**Phase 3:** Execution (SF-2, SF-3) 🔄
- Interactive config selection
- JSON-driven generation
- CLI entry point
- End-to-end execution

**Estimated duration:** 2-3 days

---

**Last updated:** 2025-10-01
