# SD Generator CLI

CLI for Stable Diffusion image generation with advanced templating system.

## Features

- 🎨 **Advanced Template System V2.0**
  - Template inheritance with `implements:`
  - Modular imports with `imports:`
  - Reusable chunks
  - Advanced selectors (`[random:N]`, `[limit:N]`, `[indexes:...]`)
  - Weight-based loop ordering

- 🔧 **Generation Modes**
  - Combinatorial: All possible combinations
  - Random: Random sampling with configurable size

- 🌱 **Seed Control**
  - Fixed: Same seed for all images
  - Progressive: Incremental seeds (seed, seed+1, seed+2...)
  - Random: Random seed for each image

- 📦 **Session Management**
  - Automatic session directories with timestamps
  - Manifest files tracking all generation metadata
  - Complete reproducibility

## Installation

**Development mode (current):**
```bash
# From repository root
cd packages/sd-generator-cli
../../venv/bin/python3 -m pip install -e .
```

**Future (after Poetry setup):**
```bash
pip install sd-generator-cli
```

## Usage

### Basic Commands

```bash
# Interactive template selection
sdgen generate

# Direct template execution
sdgen generate -t path/to/template.prompt.yaml

# Limit number of images
sdgen generate -t template.yaml -n 50

# Dry-run (save payloads without generating)
sdgen generate -t template.yaml --dry-run

# List available templates
sdgen list

# Validate a template
sdgen validate template.yaml

# Initialize global config
sdgen init
```

### API Introspection

```bash
# List samplers
sdgen api samplers

# List schedulers
sdgen api schedulers

# List models
sdgen api models

# List upscalers
sdgen api upscalers

# Show current model info
sdgen api model-info

# List ADetailer models
sdgen api adetailer-models
```

## Configuration

The CLI looks for `sdgen_config.json` in the current directory:

```json
{
  "configs_dir": "./prompts",
  "output_dir": "./results",
  "api_url": "http://127.0.0.1:7860"
}
```

Create with: `sdgen init`

## Template System

Example template (`portrait.prompt.yaml`):

```yaml
version: "2.0"
type: prompt
name: Portrait Generator

imports:
  Expression: expressions.txt
  Angle: angles.txt
  Lighting: lighting.txt

template: |
  masterpiece, best quality,
  portrait of a woman, {Expression}, {Angle},
  {Lighting}, detailed face, 8k uhd

negative_prompt: |
  low quality, blurry, distorted

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42

parameters:
  steps: 30
  cfg_scale: 7.5
  width: 512
  height: 768
  sampler: DPM++ 2M
```

See `/docs/cli/` for complete documentation.

## Tests

```bash
# All tests
../../venv/bin/python3 -m pytest tests/ -v

# API tests only
../../venv/bin/python3 -m pytest tests/api/ -v

# V2 tests only
../../venv/bin/python3 -m pytest tests/v2/ -v

# With coverage
../../venv/bin/python3 -m pytest tests/ --cov=sd_generator_cli --cov-report=term-missing
```

## Status

**Current version:** Phase 1 (Monorepo restructure)
**Test status:** 378/441 tests passing (85.6%)
- API tests: 82/82 (100%) ✅
- V2 tests: 225/270 (83%) - bugs being fixed
- Other tests: 71 tests passing

**Next:** Phase 2 - Poetry configuration & packaging

## License

See LICENSE file in repository root.
