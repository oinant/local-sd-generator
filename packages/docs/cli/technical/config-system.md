# Configuration System

**Technical documentation for JSON configuration loading, validation, and global config management.**

**Status:** Phase 2 complete ✅ | 86 tests passing

---

## Overview

The configuration system provides:
1. **Global configuration** (`.sdgen_config.json`) for system-wide settings
2. **JSON config schema** for generation runs
3. **Comprehensive validation** with clear error messages
4. **Type-safe dataclasses** for config representation

---

## Module Structure

```
CLI/config/
├── __init__.py
├── global_config.py     # SF-7: Global config management
├── config_schema.py     # SF-1: Schema definition & dataclasses
└── config_loader.py     # SF-1: Loading & validation
```

---

## Global Configuration (SF-7)

**File:** `CLI/config/global_config.py`

### Purpose

Manage system-wide settings stored in `.sdgen_config.json`.

### Global Config Schema

```json
{
  "configs_dir": "/absolute/path/to/configs",
  "output_dir": "/absolute/path/to/outputs",
  "api_url": "http://127.0.0.1:7860"
}
```

### File Locations

**Search order:**
1. `.sdgen_config.json` in project root
2. `~/.sdgen_config.json` in user home directory
3. Default values (if neither found)

**Defaults:**
```python
DEFAULT_GLOBAL_CONFIG = {
    "configs_dir": "./configs",
    "output_dir": "./apioutput",
    "api_url": "http://127.0.0.1:7860"
}
```

### API Reference

```python
@dataclass
class GlobalConfig:
    """Global configuration settings."""
    configs_dir: Path
    output_dir: Path
    api_url: str

def locate_global_config() -> Optional[Path]:
    """
    Locate global config file.

    Returns:
        Path to config file if found, None otherwise

    Search order:
        1. ./.sdgen_config.json (project root)
        2. ~/.sdgen_config.json (user home)
    """

def load_global_config() -> GlobalConfig:
    """
    Load global config from file or defaults.

    Returns:
        GlobalConfig object with loaded or default values

    Behavior:
        - If file exists: Load and merge with defaults
        - If not exists: Use defaults
        - Always validates paths and URL
    """

def create_default_global_config(path: Path) -> None:
    """
    Create global config file with default values.

    Args:
        path: Where to create the config file

    Creates:
        {
          "configs_dir": "./configs",
          "output_dir": "./apioutput",
          "api_url": "http://127.0.0.1:7860"
        }
    """

def save_global_config(config: GlobalConfig, path: Path) -> None:
    """
    Save global config to file.

    Args:
        config: GlobalConfig object
        path: Target file path

    Format: Pretty-printed JSON (2-space indent)
    """
```

### Usage Example

```python
from CLI.src.config.global_config import load_global_config, create_default_global_config

# Load global config (creates with defaults if not found)
global_config = load_global_config()

print(f"Configs directory: {global_config.configs_dir}")
print(f"Output directory: {global_config.output_dir}")
print(f"API URL: {global_config.api_url}")

# Create config file manually
create_default_global_config(Path(".sdgen_config.json"))
```

### Validation

- **configs_dir**: Must be a valid directory path (created if not exists)
- **output_dir**: Must be a valid directory path (created if not exists)
- **api_url**: Must be a valid HTTP/HTTPS URL

---

## JSON Config Schema (SF-1)

**File:** `CLI/config/config_schema.py`

### Dataclass Definitions

```python
from dataclasses import dataclass
from typing import Optional, Dict, List

@dataclass
class ModelConfig:
    """Model/checkpoint configuration."""
    checkpoint: Optional[str] = None

@dataclass
class PromptConfig:
    """Prompt configuration."""
    template: str
    negative: Optional[str] = None

@dataclass
class GenerationSettings:
    """Generation strategy settings."""
    mode: str  # "combinatorial", "random", "ask"
    seed_mode: str  # "fixed", "progressive", "random", "ask"
    seed: int
    max_images: int  # -1 for ask in random mode

@dataclass
class GenerationParameters:
    """Stable Diffusion parameters."""
    width: int
    height: int
    steps: int
    cfg_scale: float
    sampler: str
    batch_size: int
    batch_count: int

@dataclass
class OutputConfig:
    """Output configuration."""
    session_name: Optional[str] = None
    filename_keys: Optional[List[str]] = None

@dataclass
class GenerationConfig:
    """Complete generation configuration."""
    version: str
    name: Optional[str]
    description: Optional[str]
    model: ModelConfig
    prompt: PromptConfig
    variations: Dict[str, str]  # placeholder -> file path
    generation: GenerationSettings
    parameters: GenerationParameters
    output: OutputConfig
```

### Type Conversions

The schema automatically converts JSON types:
- JSON `null` → Python `None`
- JSON numbers → Python `int` or `float`
- JSON arrays → Python `List`
- JSON objects → Python `Dict` or dataclass

---

## Config Loading & Validation (SF-1)

**File:** `CLI/config/config_loader.py`

### API Reference

```python
class ConfigLoader:
    """Load and validate JSON configuration files."""

    @staticmethod
    def load_config_from_file(path: Path) -> GenerationConfig:
        """
        Load and validate config from JSON file.

        Args:
            path: Path to JSON config file

        Returns:
            GenerationConfig object

        Raises:
            FileNotFoundError: Config file not found
            json.JSONDecodeError: Invalid JSON syntax
            ValidationError: Config validation failed

        Validation steps:
            1. Parse JSON
            2. Validate schema (required fields, types)
            3. Validate enums (modes, seed_mode)
            4. Validate file paths (variations)
            5. Validate placeholders (template ↔ variations)
            6. Validate parameters (ranges, sampler)
        """

    @staticmethod
    def validate_config(config: GenerationConfig) -> List[ValidationError]:
        """
        Comprehensive validation of loaded config.

        Args:
            config: Config object to validate

        Returns:
            List of validation errors (empty if valid)

        Checks:
            - Required fields present
            - Field types correct
            - Enum values valid
            - File paths exist and readable
            - Placeholders match variations
            - Numeric ranges valid
            - Sampler exists (if not "ask")
        """

    @staticmethod
    def validate_variation_files(
        variations: Dict[str, str]
    ) -> List[ValidationError]:
        """
        Validate all variation file paths.

        Args:
            variations: Dict of placeholder -> file path

        Returns:
            List of validation errors

        Checks for each file:
            - File exists
            - File is readable
            - File contains at least one variation
            - File format is valid
        """

    @staticmethod
    def validate_placeholders_match(
        prompt: PromptConfig,
        variations: Dict[str, str]
    ) -> List[ValidationError]:
        """
        Validate placeholders in template match variations.

        Args:
            prompt: Prompt config with template
            variations: Dict of placeholder -> file path

        Returns:
            List of validation errors

        Checks:
            - All placeholders in template have variation files
            - Warns if variations defined but not used in template
        """

    @staticmethod
    def validate_numeric_ranges(
        parameters: GenerationParameters
    ) -> List[ValidationError]:
        """
        Validate numeric parameter ranges.

        Checks:
            - width > 0 (or -1 for ask)
            - height > 0 (or -1 for ask)
            - steps > 0 (or -1 for ask)
            - cfg_scale > 0 (or -1.0 for ask)
            - batch_size > 0 (or -1 for ask)
            - batch_count > 0 (or -1 for ask)
        """
```

### Validation Error Format

```python
@dataclass
class ValidationError:
    """Validation error with context."""
    field: str          # "variations.Expression"
    message: str        # "File not found"
    suggestion: str     # "Check file path and permissions"
    severity: str       # "error" or "warning"
```

### Example Validation Errors

#### Missing Placeholder

```
ValidationError:
  Field: prompt.template
  Message: Placeholder 'Lighting' has no corresponding variation file
  Suggestion: Add "Lighting" to variations object or remove from template
  Severity: error

  Prompt template: "portrait, {Expression}, {Angle}, {Lighting}, beautiful"
  Found placeholders: ['Expression', 'Angle', 'Lighting']
  Defined variations: ['Expression', 'Angle']
```

#### Invalid File Path

```
ValidationError:
  Field: variations.Expression
  Message: File not found at '/path/to/expressions.txt'
  Suggestion: Check file path exists and is readable
  Severity: error
```

#### Invalid Enum Value

```
ValidationError:
  Field: generation.mode
  Message: Invalid mode 'combinatorials' (typo?)
  Suggestion: Valid modes: 'combinatorial', 'random', 'ask'
  Severity: error
```

#### Unused Variation (Warning)

```
ValidationError:
  Field: variations.Lighting
  Message: Variation file defined but not used in prompt template
  Suggestion: Remove unused variation or add {Lighting} to template
  Severity: warning
```

---

## Usage Examples

### Load and Validate Config

```python
from CLI.src.config import ConfigLoader
from pathlib import Path

# Load config
try:
    config = ConfigLoader.load_config_from_file(
        Path("configs/anime_portraits.json")
    )
    print(f"✓ Config loaded: {config.name}")
    print(f"  Prompt: {config.prompt.template}")
    print(f"  Mode: {config.generation.mode}")
    print(f"  Variations: {list(config.variations.keys())}")

except FileNotFoundError as e:
    print(f"✗ Config file not found: {e}")

except ValidationError as e:
    print(f"✗ Validation failed:")
    for error in e.errors:
        print(f"  {error.field}: {error.message}")
        if error.suggestion:
            print(f"    → {error.suggestion}")
```

### Manual Validation

```python
from CLI.src.config import GenerationConfig
from CLI.src.config import ConfigLoader

# Create config object manually
config = GenerationConfig(
    version="1.0",
    name="Test Config",
    description="Testing validation",
    # ... other fields
)

# Validate
errors = ConfigLoader.validate_config(config)

if errors:
    print("Validation errors:")
    for error in errors:
        print(f"  {error.field}: {error.message}")
else:
    print("✓ Config is valid")
```

### Check Variation Files

```python
from CLI.src.config import ConfigLoader

variations = {
    "Expression": "/path/to/expressions.txt",
    "Angle": "/path/to/angles.txt"
}

errors = ConfigLoader.validate_variation_files(variations)

for error in errors:
    print(f"{error.field}: {error.message}")
```

---

## Validation Rules Reference

### Required Fields

All these fields must be present in JSON:

```json
{
  "version": "...",          // Required
  "prompt": { ... },         // Required
  "variations": { ... },     // Required
  "generation": { ... },     // Required
  "parameters": { ... },     // Required
  "output": { ... }          // Required
}
```

### Type Validation

| Field | Expected Type | Example |
|-------|--------------|---------|
| `version` | string | `"1.0"` |
| `name` | string or null | `"My Config"` |
| `prompt.template` | string | `"{Expression}, beautiful"` |
| `variations` | object | `{"Expression": "file.txt"}` |
| `generation.seed` | integer | `42` |
| `parameters.cfg_scale` | float | `7.5` |
| `output.filename_keys` | array of strings | `["Expression"]` |

### Enum Validation

**generation.mode:**
- Valid: `"combinatorial"`, `"random"`, `"ask"`
- Invalid: anything else

**generation.seed_mode:**
- Valid: `"fixed"`, `"progressive"`, `"random"`, `"ask"`
- Invalid: anything else

**parameters.sampler:**
- Valid: Any sampler name from SD API or `"ask"`
- Validation: Query SD API for available samplers

### Path Validation

For each path in `variations`:
1. Must be absolute path (relative not supported in v1.0)
2. File must exist
3. File must be readable
4. File must contain ≥1 variation line

### Placeholder Validation

```python
# Extract placeholders from template
template = "portrait, {Expression}, {Angle}, {Lighting}"
placeholders = ["Expression", "Angle", "Lighting"]

# Check all have variations
for placeholder in placeholders:
    if placeholder not in variations:
        # ERROR: Missing variation file

# Warn about unused variations
for variation_key in variations:
    if variation_key not in placeholders:
        # WARNING: Unused variation file
```

### Numeric Range Validation

All numeric parameters must be:
- Positive (> 0) OR
- `-1` (for "ask" mode) OR
- `-1.0` for float parameters (for "ask" mode)

**Examples:**
```json
{
  "width": 512,      // ✓ Valid
  "height": -1,      // ✓ Valid (ask mode)
  "steps": 0,        // ✗ Invalid (must be > 0 or -1)
  "cfg_scale": 7.5,  // ✓ Valid
  "cfg_scale": -1.0  // ✓ Valid (ask mode)
}
```

---

## Testing

### Test Coverage

**Total:** 86 tests passing ✅

**Breakdown:**
- `test_global_config.py`: 26 tests
- `test_config_schema.py`: 29 tests
- `test_config_loader.py`: 31 tests

### Test Categories

#### Global Config Tests
- File location and search order
- Default value loading
- Config creation and saving
- Path validation
- URL validation

#### Schema Tests
- Dataclass instantiation
- Type conversions (JSON → Python)
- Optional field handling
- Nested object validation

#### Loader Tests
- Valid config loading
- Invalid JSON handling
- Missing required fields
- Type mismatch errors
- Enum validation
- File path validation
- Placeholder validation
- Numeric range validation
- Comprehensive error messages

### Running Tests

```bash
# Run all config tests
pytest tests/test_global_config.py tests/test_config_schema.py tests/test_config_loader.py -v

# Run specific test
pytest tests/test_config_loader.py::test_invalid_generation_mode -v

# Run with coverage
pytest tests/test_config_*.py --cov=CLI/config --cov-report=html
```

---

## Design Decisions

### Why Dataclasses?

**Chosen:** Python dataclasses
**Alternative considered:** Pydantic models

**Rationale:**
- No external dependencies (stdlib only)
- Type hints for IDE support
- Simple and clear
- Easy to extend

**Trade-off:** Less runtime validation than Pydantic, but we implement custom validation.

### Why Separate Schema and Loader?

**Chosen:** `config_schema.py` + `config_loader.py`
**Alternative:** Single file

**Rationale:**
- Clear separation of concerns
- Schema can be imported without validation logic
- Easier to maintain and test
- Allows custom loaders in future (YAML, TOML, etc.)

### Why Absolute Paths Only (v1.0)?

**Chosen:** Require absolute paths for variation files
**Alternative:** Support relative paths

**Rationale:**
- Avoid ambiguity (relative to what? config file? script? cwd?)
- Explicit is better than implicit
- Simpler validation logic
- Can add relative path support in future versions

**Future:** v2.0 may support relative paths with clear resolution rules.

### Why Global Config File?

**Chosen:** `.sdgen_config.json` with search order
**Alternative:** Environment variables or CLI args

**Rationale:**
- Persistent configuration
- Easy to edit (plain JSON)
- Supports both project-level and user-level configs
- Can be version-controlled (project-level)

---

## Future Enhancements

### Planned for v2.0

1. **Relative Paths**
   - Support paths relative to config file location
   - Support paths relative to global `configs_dir`

2. **Config Templates**
   - Base configs that can be extended
   - DRY principle for common settings

3. **Variable Substitution**
   - `${variable}` syntax in prompts and paths
   - Reduce repetition

4. **Config Validation Tool**
   - Standalone CLI tool: `python validate_config.py config.json`
   - JSON Schema for IDE validation

5. **Multiple Config Formats**
   - YAML support
   - TOML support
   - Keep JSON as primary

---

## References

- **[Architecture](architecture.md)** - Overall CLI architecture
- **[JSON Config System](../usage/json-config-system.md)** - User guide
- **[Design Decisions](design-decisions.md)** - Architectural rationale

---

**Implementation:** Phase 2 complete ✅
**Tests:** 86 tests passing ✅
**Next:** Phase 3 execution system 🔄

**Last updated:** 2025-10-01
