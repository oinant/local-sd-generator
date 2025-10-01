# JSON Config CLI - Phase 3

**Command-line interface for JSON-driven image generation.**

---

## Overview

The JSON Config CLI (`generator_cli.py`) allows you to run image generation directly from JSON configuration files, with support for:

- Interactive config selection
- Direct config path execution
- Interactive parameter prompts
- Validation before generation
- Progress reporting

---

## Quick Start

### 1. Initialize Global Config

First time setup:

```bash
python3 CLI/generator_cli.py --init-config
```

This creates `.sdgen_config.json` in your project directory with:
- `configs_dir`: Where to find JSON configs (default: `./configs`)
- `output_dir`: Where to save generated images (default: `./apioutput`)
- `api_url`: Stable Diffusion API endpoint (default: `http://127.0.0.1:7860`)

### 2. Create a JSON Config

Create `configs/anime_portraits.json`:

```json
{
  "version": "1.0",
  "name": "Anime Portrait Generation",
  "description": "Character portraits with expressions and angles",

  "prompt": {
    "template": "masterpiece, best quality, {Expression}, {Angle}, 1girl, anime style",
    "negative": "low quality, blurry, bad anatomy, text"
  },

  "variations": {
    "Expression": "./variations/expressions.txt",
    "Angle": "./variations/angles.txt"
  },

  "generation": {
    "mode": "combinatorial",
    "seed_mode": "progressive",
    "seed": 42,
    "max_images": 20
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
    "session_name": "anime_portraits",
    "filename_keys": ["Expression", "Angle"]
  }
}
```

### 3. Run Generation

```bash
# Interactive mode - select from list
python3 CLI/generator_cli.py

# Direct path
python3 CLI/generator_cli.py --config configs/anime_portraits.json

# List available configs
python3 CLI/generator_cli.py --list
```

---

## CLI Commands

### Interactive Mode

```bash
python3 CLI/generator_cli.py
```

**Flow:**
1. Lists all JSON files in `configs_dir`
2. Displays name and description for each
3. Prompts user to select one
4. Validates config
5. Prompts for any "ask" parameters
6. Runs generation
7. Displays results

**Example output:**

```
=== SD Image Generator - JSON Config Mode ===

Available configurations:

  1. anime_portraits.json
     Anime Portrait Generation
     Character portraits with expressions and angles

  2. character_study.json
     Character Study - Multiple Outfits
     Full character sheet

Select configuration (1-2): 1

Loading config: anime_portraits.json...
✓ Config loaded successfully

Validating config...
✓ Config validated

Starting generation...
[==============================] 20/20 (100%)

✓ Generation complete!
  Session: 20251001_143052_anime_portraits
  Images: 20
  Time: 3m 15s
```

### Direct Config Path

```bash
python3 CLI/generator_cli.py --config PATH
```

Run specific config directly without selection prompt.

**Path resolution:**
- Absolute paths: Used as-is
- Relative paths: Tried relative to `configs_dir` first, then current directory

**Examples:**

```bash
# Relative to configs_dir
python3 CLI/generator_cli.py --config anime_portraits.json

# Relative path with subdirectory
python3 CLI/generator_cli.py --config characters/emma.json

# Absolute path
python3 CLI/generator_cli.py --config /path/to/config.json

# Relative to current directory
python3 CLI/generator_cli.py --config ../other/config.json
```

### List Configs

```bash
python3 CLI/generator_cli.py --list
```

List all available configs with metadata:

```
Configuration files in /path/to/configs:

  • anime_portraits.json
    Name: Anime Portrait Generation
    Description: Character portraits with expressions and angles
    Path: /path/to/configs/anime_portraits.json

  • character_study.json
    Name: Character Study
    Description: Full character sheet
    Path: /path/to/configs/character_study.json
```

### Initialize Config

```bash
python3 CLI/generator_cli.py --init-config
```

Create or recreate global config file with interactive prompts.

### Override API URL

```bash
python3 CLI/generator_cli.py --api-url URL
```

Override API URL for this run:

```bash
python3 CLI/generator_cli.py --config test.json --api-url http://localhost:8000
```

---

## Interactive Parameters

Config values can be set to `"ask"` or `-1` to prompt user at runtime.

### Generation Mode

```json
"generation": {
  "mode": "ask"
}
```

**Prompt:**

```
Generation mode not specified in config.
Available modes:
  1. combinatorial - Generate all possible combinations
  2. random - Generate random unique combinations

Select mode (1-2): _
```

### Seed Mode

```json
"generation": {
  "seed_mode": "ask"
}
```

**Prompt:**

```
Seed mode not specified in config.
Available modes:
  1. fixed - Same seed for all images
  2. progressive - Seeds increment (seed, seed+1, seed+2...)
  3. random - Random seed for each image

Select mode (1-3): _
```

### Max Images

```json
"generation": {
  "max_images": -1
}
```

**Prompt:**

```
Total possible combinations: 150

How many images would you like to generate?
  • Enter a number (1-150)
  • Press Enter to generate all 150

Number of images (default: 150): _
```

### Numeric Parameters

Any parameter can be set to `-1` to prompt:

```json
"parameters": {
  "width": -1,
  "height": -1,
  "steps": -1,
  "cfg_scale": -1.0
}
```

**Prompts:**

```
Width not specified in config.
Width (default: 512): _

Height not specified in config.
Height (default: 768): _

Steps not specified in config.
Steps (default: 30): _

CFG Scale not specified in config.
CFG Scale (default: 7.0): _
```

### Sampler Selection

```json
"parameters": {
  "sampler": "ask"
}
```

**Prompt:**

```
Sampler not specified in config.
Available samplers:

  1. Euler a
  2. Euler
  3. DPM++ 2M Karras
  4. DPM++ SDE Karras
  5. DDIM
  ...

Select sampler (1-15): _
```

### Seed Value

```json
"generation": {
  "seed": -1
}
```

**Prompt:**

```
Seed not specified in config.
Seed (default: 42): _
```

---

## Example Workflows

### Full Interactive Config

Create a config that asks for everything:

```json
{
  "version": "1.0",
  "name": "Interactive Test",

  "prompt": {
    "template": "{Subject}, {Style}"
  },

  "variations": {
    "Subject": "./variations/subjects.txt",
    "Style": "./variations/styles.txt"
  },

  "generation": {
    "mode": "ask",
    "seed_mode": "ask",
    "seed": -1,
    "max_images": -1
  },

  "parameters": {
    "width": -1,
    "height": -1,
    "steps": -1,
    "cfg_scale": -1.0,
    "sampler": "ask",
    "batch_size": 1,
    "batch_count": 1
  }
}
```

### Minimal Fixed Config

Config with all parameters specified (no prompts):

```json
{
  "version": "1.0",

  "prompt": {
    "template": "{Style}, landscape"
  },

  "variations": {
    "Style": "./variations/styles.txt"
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
  }
}
```

### Quick Experimentation

Config that only asks for key parameters:

```json
{
  "version": "1.0",
  "name": "Quick Experiment",

  "prompt": {
    "template": "{Subject}, {Style}"
  },

  "variations": {
    "Subject": "./variations/subjects.txt",
    "Style": "./variations/styles.txt"
  },

  "generation": {
    "mode": "random",
    "seed_mode": "ask",
    "seed": -1,
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
  }
}
```

---

## Validation

The CLI validates configs before generation:

**Checks:**
- Required fields present
- Valid enum values (modes, etc.)
- Variation files exist and readable
- Placeholders match variation files
- Filename keys reference existing variations
- Numeric parameters in valid ranges

**Example validation output:**

```
Validating config...
✗ Config validation failed:

Validation Errors:
  ✗ variations.Expression: Variation file not found: /path/to/missing.txt
    → Check that the path is correct and the file exists

  ✗ output.filename_keys: Filename key 'Missing' not found in variations
    → Available keys: Expression, Angle

⚠ Warnings:
  ⚠ variations.Unused: Variation file defined but placeholder '{Unused}' not used in prompt
    → Either add '{Unused}' to prompt or remove from variations
```

---

## Exit Codes

- `0` - Success (at least one image generated)
- `1` - Error (config invalid, no images generated, etc.)
- `130` - User cancelled (Ctrl+C)

---

## Non-Interactive Usage

For automation, ensure all parameters are specified (no "ask" or `-1`):

```bash
# Check if stdin is TTY
if [ -t 0 ]; then
    python3 CLI/generator_cli.py
else
    echo "Error: Interactive mode requires a terminal"
    python3 CLI/generator_cli.py --config fixed_config.json
fi
```

---

## Troubleshooting

### "Interactive mode requires a TTY"

**Problem:** Running in non-interactive environment with "ask" parameters.

**Solution:** Specify all parameters in config or provide them via command line.

### "Configs directory not found"

**Problem:** Global config points to non-existent directory.

**Solution:**
```bash
# Create the directory
mkdir -p configs

# Or update global config
python3 CLI/generator_cli.py --init-config
```

### "Config file not found"

**Problem:** Specified config doesn't exist.

**Solution:**
```bash
# List available configs
python3 CLI/generator_cli.py --list

# Use correct path
python3 CLI/generator_cli.py --config configs/correct_name.json
```

### "Validation failed"

**Problem:** Config has errors.

**Solution:** Read validation messages and fix errors:
- Check file paths
- Verify placeholders match
- Ensure all required fields present

---

## See Also

- [JSON Config System](./json-config-system.md) - Config format reference
- [Getting Started](./getting-started.md) - First generation tutorial
- [Advanced Features](../technical/advanced-features.md) - Advanced usage

---

**Last updated:** 2025-10-01
