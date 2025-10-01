# SD Image Generator CLI

**Command-line tool for JSON-driven Stable Diffusion image generation with variations.**

---

## Quick Start

```bash
# Initialize global config
python3 generator_cli.py --init-config

# List available configs
python3 generator_cli.py --list

# Run interactive mode
python3 generator_cli.py

# Run specific config
python3 generator_cli.py --config configs/example_minimal.json
```

---

## Features

✅ **JSON Config System**
- Define prompts, variations, and parameters in JSON
- Reusable configurations
- Version control friendly

✅ **Interactive Selection**
- Browse available configs
- Select from list
- Direct path support

✅ **Interactive Parameters**
- Set values to "ask" or -1 to prompt at runtime
- Flexible experimentation
- Quick parameter changes

✅ **Validation**
- Comprehensive config validation
- Clear error messages
- Helpful suggestions

✅ **Progress Reporting**
- Real-time generation progress
- Success/failure tracking
- Timing information

---

## Usage

### Interactive Mode

```bash
python3 generator_cli.py
```

Displays list of configs and prompts for selection.

### Direct Config Path

```bash
python3 generator_cli.py --config PATH
```

Runs specific config directly.

### List Configs

```bash
python3 generator_cli.py --list
```

Lists all available configs with metadata.

### Initialize Config

```bash
python3 generator_cli.py --init-config
```

Creates `.sdgen_config.json` with global settings.

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

### JSON Config Format

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
