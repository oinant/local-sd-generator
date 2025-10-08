# SD Image Generator CLI (`sdgen`)

**Modern command-line tool for YAML-driven Stable Diffusion image generation with advanced templating.**

---

## 🚀 Quick Start

### 1. **First-time Setup** (IMPORTANT!)

```bash
# Initialize your global config
sdgen init
```

This creates `~/.sdgen_config.json` with:
- `configs_dir`: Path to your YAML templates
- `output_dir`: Where images are saved
- `api_url`: Stable Diffusion WebUI API endpoint

**⚠️ IMPORTANT:** The config file MUST be in your home directory (`~/.sdgen_config.json`), not in the project folder!

### 2. **Basic Usage**

```bash
# List available templates
sdgen list

# Generate images (interactive mode)
sdgen generate

# Generate from specific template
sdgen generate -t path/to/template.prompt.yaml

# Dry-run (test without API)
sdgen generate -t template.yaml --dry-run

# Validate a template
sdgen validate template.yaml

# API introspection
sdgen api samplers
sdgen api models
```

**Note:** Phase 1 JSON config system has been removed. Use YAML templates (`.prompt.yaml`) instead.

---

## Features

✅ **YAML Template System**
- Define prompts, variations, and parameters in `.prompt.yaml` files
- Reusable chunk templates with inheritance
- Multi-field variations and flexible selectors
- Version control friendly

✅ **Interactive Selection**
- Browse available templates
- Select from list
- Direct path support

✅ **Advanced Templating**
- Placeholder system: `{PlaceholderName}`
- Inline variations: direct lists in YAML
- Chunk templates: reusable components with `implements`
- Template inheritance: `extends` for base templates
- Flexible selectors: keys, indices, ranges, random

✅ **Validation**
- Comprehensive template validation
- Clear error messages
- Helpful suggestions

✅ **Progress Reporting**
- Real-time generation progress
- Success/failure tracking
- Timing information
- Dry-run mode for testing

---

## 📖 Usage

### Interactive Mode

```bash
sdgen generate
```

Displays list of templates and prompts for selection.

### Direct Template Path

```bash
sdgen generate -t PATH
```

Runs specific template directly.

### List Templates

```bash
sdgen list
```

Lists all available `.prompt.yaml` templates with metadata.

### Initialize Config

```bash
sdgen init
```

Creates `~/.sdgen_config.json` in your home directory with global settings.

---

## Configuration

### Global Config (`.sdgen_config.json`)

```json
{
  "configs_dir": "./configs",
  "output_dir": "./apioutput",
  "api_url": "http://127.0.0.1:7860"
}
```

**Important:** `sdgen` searches for `.sdgen_config.json` in the current working directory first, then in the user's home directory (`~/.sdgen_config.json`). **Always use the home directory for global config!**

**WSL Users:** Use absolute WSL paths (e.g., `/mnt/d/StableDiffusion/private/results`) instead of Windows paths (e.g., `D:/StableDiffusion/private/results`).

**Output Directories:**
- `generator_cli.py` (Legacy JSON): Images saved to `{output_dir}/{session_name}/`
- `sdgen` (Phase 2 YAML): Images saved to `{output_dir}/{session_name}_{timestamp}/`
- `sdgen --dry-run`: API requests saved as JSON in session directory
- `generate_from_template.py`: JSON variations saved to `{output_dir}/dryrun/` (utility tool, generates JSON only)

### Phase 2 YAML Template CLI

The `sdgen` provides a complete workflow for Phase 2 templates:

```bash
# Interactive template selection
sdgen generate

# Direct template execution
sdgen generate -t /path/to/template.prompt.yaml

# Generate specific count (overrides template config)
sdgen generate -t test.yaml --count 10

# Dry-run mode (saves API requests as JSON, no image generation)
sdgen generate -t test.yaml --dry-run
```

**Output structure:**
```
{output_dir}/
└── {session_name}_{timestamp}/
    ├── {session_name}_manifest.json    # All variations with prompts
    ├── {session_name}_0000.png         # Generated images
    ├── {session_name}_0001.png
    └── ...
```

In `--dry-run` mode, `request_NNNN.json` files are saved instead of images.

### JSON Config Format (Legacy/Phase 1)

```json
{
  "version": "1.0",
  "name": "Config Name",
  "description": "Description",

  "prompt": {
    "template": "prompt with {Placeholders}",
    "negative": "negative prompt"
  },

  "variations": {
    "Placeholder": "path/to/variations.txt"
  },

  "generation": {
    "mode": "combinatorial",
    "seed_mode": "progressive",
    "seed": 42,
    "max_images": 100
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
    "session_name": "session_name",
    "filename_keys": ["Placeholder"]
  }
}
```

---

## Module Structure

```
CLI/
├── generator_cli.py           # Main entry point
│
├── config/                    # Config management
│   ├── global_config.py       # Global settings
│   ├── config_loader.py       # JSON loading/validation
│   ├── config_schema.py       # Data structures
│   └── config_selector.py     # Interactive selection
│
├── execution/                 # Generation execution
│   └── json_generator.py      # Interactive prompts & execution
│
├── image_variation_generator.py  # Core generator
├── sdapi_client.py               # SD API client
├── variation_loader.py           # Variation file loading
│
└── output/                    # Output handling
    ├── output_namer.py        # Filename generation
    └── metadata_generator.py  # Metadata JSON
```

---

## Examples

### Example 1: Fixed Parameters

`configs/landscape.json`:

```json
{
  "version": "1.0",
  "name": "Landscape Generation",

  "prompt": {
    "template": "{Style}, landscape, nature, detailed"
  },

  "variations": {
    "Style": "./variations/styles.txt"
  },

  "generation": {
    "mode": "combinatorial",
    "seed_mode": "progressive",
    "seed": 42,
    "max_images": 10
  },

  "parameters": {
    "width": 768,
    "height": 512,
    "steps": 30,
    "cfg_scale": 7.0,
    "sampler": "DPM++ 2M Karras"
  }
}
```

### Example 2: Interactive Parameters

`configs/quick_test.json`:

```json
{
  "version": "1.0",
  "name": "Quick Test",

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
    "width": 512,
    "height": 768,
    "steps": 30,
    "cfg_scale": 7.0,
    "sampler": "ask"
  }
}
```

---

## Documentation

- **[Getting Started](../docs/cli/usage/getting-started.md)** - First generation tutorial
- **[JSON Config CLI](../docs/cli/usage/json-config-cli.md)** - Complete CLI guide
- **[JSON Config System](../docs/cli/usage/json-config-system.md)** - Config format reference

---

## Testing

```bash
# Run all tests
python3 -m pytest tests/

# Run specific test modules
python3 -m pytest tests/test_config_selector.py
python3 -m pytest tests/test_json_generator.py
python3 -m pytest tests/test_integration_phase3.py
```

---

## Requirements

- Python 3.8+
- Stable Diffusion WebUI with API enabled
- Required packages (see `requirements.txt`)

---

## Support

For issues, questions, or feature requests:
- Check documentation in `docs/`
- Review examples in `configs/`
- See roadmap in `docs/roadmap/`

---

**Version:** Phase 3 Complete
**Last Updated:** 2025-10-01
