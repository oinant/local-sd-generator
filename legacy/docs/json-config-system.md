# JSON Configuration System

**Define generation runs declaratively with JSON files instead of writing Python code.**

---

## Overview

Instead of creating Python scripts, you can define complete generation configurations in JSON files and run them with a simple CLI command.

### Python Script (Old Way)

```python
generator = ImageVariationGenerator(
    prompt_template="masterpiece, {Expression}, {Angle}, beautiful",
    negative_prompt="low quality, blurry",
    variation_files={
        "Expression": "/path/to/expressions.txt",
        "Angle": "/path/to/angles.txt"
    },
    seed=42,
    generation_mode="combinatorial",
    seed_mode="progressive",
    # ... many more parameters
)
generator.run()
```

### JSON Config (New Way)

**`configs/anime_portraits.json`:**
```json
{
  "version": "1.0",
  "name": "Anime Portrait Generation",
  "description": "Character portraits with various expressions and angles",

  "prompt": {
    "template": "masterpiece, {Expression}, {Angle}, beautiful anime girl, detailed",
    "negative": "low quality, blurry, bad anatomy"
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

**Run it:**
```bash
python3 generator_cli.py --config configs/anime_portraits.json
```

---

## JSON Schema Reference

### Complete Example

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

## Field Specifications

### `version` (string, required)

Schema version for future compatibility. Current: `"1.0"`

### `name` (string, optional)

Human-readable name for the configuration.

### `description` (string, optional)

Description of what this config generates.

### `model` (object, optional)

**Fields:**
- `checkpoint` (string, optional): Checkpoint filename (e.g., `"realisticVision_v51.safetensors"`)
  - If not specified: uses currently loaded checkpoint
  - If specified but not found: warning + uses current checkpoint

**Note:** Automatic checkpoint loading is a future feature (Phase 4).

### `prompt` (object, required)

**Fields:**
- `template` (string, required): Prompt with placeholders (e.g., `"{Expression}, beautiful portrait"`)
- `negative` (string, optional): Negative prompt

**Placeholder syntax:**
- `{Name}` - All variations
- `{Name:N}` - N random variations
- `{Name:#|1|5|22}` - Specific indices
- `{Name:$P}` - Priority weight P

See [Variation Files](variation-files.md) for complete syntax.

### `variations` (object, required)

Map of placeholder names to variation file paths.

**Format:**
```json
{
  "Expression": "/absolute/path/to/expressions.txt",
  "Angle": "/absolute/path/to/angles.txt"
}
```

**Validation:**
- All placeholders in `prompt.template` must have entries here
- All file paths must exist and be readable
- Paths must be absolute (relative paths not supported in v1.0)

### `generation` (object, required)

**Fields:**

- **`mode`** (string, required): `"combinatorial"`, `"random"`, or `"ask"`
  - `"combinatorial"`: Generate all combinations
  - `"random"`: Generate random unique combinations
  - `"ask"`: Prompt user interactively at runtime

- **`seed_mode`** (string, required): `"fixed"`, `"progressive"`, `"random"`, or `"ask"`
  - `"fixed"`: Same seed for all images
  - `"progressive"`: Increment seeds (42, 43, 44, ...)
  - `"random"`: Random seed (-1) for each image
  - `"ask"`: Prompt user at runtime

- **`seed`** (integer, required): Base seed value
  - Any integer including `-1` (random in SD)
  - Does NOT trigger ask mode (use `seed_mode: "ask"` for that)

- **`max_images`** (integer, required): Maximum images to generate
  - `-1`: Ask user interactively
  - Positive integer: Use that value
  - Only applies to `"random"` mode

### `parameters` (object, required)

Stable Diffusion generation parameters.

**Fields:**
- `width` (integer): Image width in pixels (or `-1` to ask)
- `height` (integer): Image height in pixels (or `-1` to ask)
- `steps` (integer): Sampling steps (or `-1` to ask)
- `cfg_scale` (float): CFG scale (or `-1.0` to ask)
- `sampler` (string): Sampler name (or `"ask"` to prompt)
- `batch_size` (integer): Batch size (or `-1` to ask)
- `batch_count` (integer): Batch count (or `-1` to ask)

**Interactive mode:** Use `-1` or `"ask"` to prompt user at runtime.

### `output` (object, required)

**Fields:**

- **`session_name`** (string, optional): Custom session folder name
  - If present: `{timestamp}_{session_name}/` (e.g., `20251001_143052_anime_test_v2/`)
  - If absent: `{timestamp}_{key1}_{key2}.../` using `filename_keys`

- **`filename_keys`** (array of strings, optional): Variation keys to include in filenames
  - Keys must exist in `variations`
  - Order determines filename order
  - Format: `{index}_{key1}-{value1}_{key2}-{value2}.png`
  - Example: `["Angle", "Expression"]` → `001_Angle-Front_Expression-Smiling.png`
  - If empty/absent: Files named `{index}.png` only

---

## Interactive Parameters

Use `"ask"` or `-1` to prompt users at runtime.

### Example: Ask for generation mode

```json
{
  "generation": {
    "mode": "ask",
    "seed_mode": "progressive",
    "seed": 42
  }
}
```

**Prompt at runtime:**
```
Generation mode not specified in config.
Available modes:
  1. combinatorial - Generate all possible combinations
  2. random - Generate random unique combinations

Select mode (1-2): _
```

### Example: Ask for image count

```json
{
  "generation": {
    "mode": "random",
    "max_images": -1
  }
}
```

**Prompt at runtime:**
```
Total combinations: 150

How many images to generate? (1-150): _
```

### Example: Ask for sampler

```json
{
  "parameters": {
    "sampler": "ask"
  }
}
```

**Prompt at runtime:**
```
Available samplers:
  1. Euler a
  2. DPM++ 2M Karras
  3. DPM++ SDE Karras
  ...

Select sampler (1-15): _
```

---

## Usage Examples

### Basic Generation

**`configs/simple.json`:**
```json
{
  "version": "1.0",
  "name": "Simple Test",

  "prompt": {
    "template": "{Style}, beautiful landscape",
    "negative": "low quality"
  },

  "variations": {
    "Style": "/path/to/styles.txt"
  },

  "generation": {
    "mode": "combinatorial",
    "seed_mode": "progressive",
    "seed": 42,
    "max_images": -1
  },

  "parameters": {
    "width": 512,
    "height": 512,
    "steps": 20,
    "cfg_scale": 7.0,
    "sampler": "Euler a",
    "batch_size": 1,
    "batch_count": 1
  },

  "output": {
    "filename_keys": ["Style"]
  }
}
```

**Run:**
```bash
python3 generator_cli.py --config configs/simple.json
```

### Interactive Exploration

```json
{
  "version": "1.0",
  "name": "Interactive Exploration",

  "prompt": {
    "template": "{Subject}, {Style}",
    "negative": "low quality"
  },

  "variations": {
    "Subject": "/path/to/subjects.txt",
    "Style": "/path/to/styles.txt"
  },

  "generation": {
    "mode": "ask",
    "seed_mode": "ask",
    "seed": -1,
    "max_images": -1
  },

  "parameters": {
    "width": 512,
    "height": 512,
    "steps": -1,
    "cfg_scale": -1.0,
    "sampler": "ask",
    "batch_size": 1,
    "batch_count": 1
  },

  "output": {
    "session_name": "exploration",
    "filename_keys": ["Subject", "Style"]
  }
}
```

Prompts user for all `-1` and `"ask"` parameters.

### Character Sheet

```json
{
  "version": "1.0",
  "name": "Character Sheet - Emma Watson",
  "description": "Full character sheet with outfits, angles, and expressions",

  "prompt": {
    "template": "1girl, emma watson, {Outfit:$1}, {Angle:$10}, {Expression:$20}, high quality",
    "negative": "low quality, blurry, bad anatomy"
  },

  "variations": {
    "Outfit": "/path/to/outfits.txt",
    "Angle": "/path/to/angles.txt",
    "Expression": "/path/to/expressions.txt"
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
    "cfg_scale": 7.5,
    "sampler": "DPM++ 2M Karras",
    "batch_size": 1,
    "batch_count": 1
  },

  "output": {
    "session_name": "emma_charactersheet_v1",
    "filename_keys": ["Outfit", "Angle", "Expression"]
  }
}
```

**Result:** Organized by outfit, then angle, then expression (priority weights: 1 < 10 < 20)

---

## Global Configuration

Global settings are stored in `.sdgen_config.json` at project root or `~/.sdgen_config.json`.

**Example `.sdgen_config.json`:**
```json
{
  "configs_dir": "/absolute/path/to/configs",
  "output_dir": "/absolute/path/to/outputs",
  "api_url": "http://127.0.0.1:7860"
}
```

**Defaults** (if file not found):
- `configs_dir`: `./configs`
- `output_dir`: `./apioutput`
- `api_url`: `http://127.0.0.1:7860`

The system will create this file automatically on first run.

---

## Validation

Configs are validated on load:

### Required Fields

All required fields must be present:
- `version`, `prompt`, `variations`, `generation`, `parameters`, `output`

### Type Validation

Field types must match schema:
- Strings, integers, floats, objects, arrays

### Enum Validation

Enum fields must have valid values:
- `generation.mode`: `"combinatorial"`, `"random"`, `"ask"`
- `generation.seed_mode`: `"fixed"`, `"progressive"`, `"random"`, `"ask"`

### File Path Validation

All variation file paths must:
- Exist on filesystem
- Be readable
- Contain at least one variation

### Placeholder Validation

All placeholders in `prompt.template` must have corresponding entries in `variations`.

**Example error:**
```
ValidationError: Placeholder 'Lighting' in prompt template has no corresponding variation file.
Found placeholders: ['Expression', 'Angle', 'Lighting']
Defined variations: ['Expression', 'Angle']
```

---

## Learn More

- **[Variation Files](variation-files.md)** - Placeholder syntax and variation file formats
- **[Examples](examples.md)** - Common generation patterns
- **[Technical Docs](../technical/config-system.md)** - Implementation details

---

**Status:** Phase 2 completed ✅
**Phase 3** (CLI execution) in progress 🔄

**Last updated:** 2025-10-01
