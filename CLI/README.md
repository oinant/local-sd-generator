# SD Image Generator CLI (`sdgen`)

**Modern command-line tool for YAML-driven Stable Diffusion image generation with Template System V2.0.**

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
sdgen api upscalers
sdgen api schedulers
```

---

## ✨ Features

✅ **Template System V2.0**
- YAML-based templates (`.prompt.yaml`)
- Placeholder system with selectors
- Template inheritance with `implements:`
- Reusable chunks with `@ChunkName`
- Multi-file variation imports
- Comprehensive validation

✅ **Advanced Selectors**
- Random selection: `{Hair[random:5]}`
- Index selection: `{Hair[#1,5,8]}`
- Key selection: `{Hair[BobCut,LongHair]}`
- Weight-based loops: `{Hair[$10]}`
- Exclude from combinatorial: `{Quality[$0]}`

✅ **Generation Modes**
- **Combinatorial**: All possible combinations
- **Random**: Random unique combinations
- **Seed modes**: fixed, progressive, random

✅ **Validation & Statistics**
- Pre-generation validation
- Variation count display
- Total combinations calculation
- Clear error messages with suggestions

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

### Validate Template

```bash
sdgen validate path/to/template.prompt.yaml
```

Validates template syntax and structure without generating images.

### Initialize Config

```bash
sdgen init
```

Creates `~/.sdgen_config.json` in your home directory with global settings.

### API Introspection

```bash
# List available samplers
sdgen api samplers

# List available models
sdgen api models

# List upscalers
sdgen api upscalers

# List schedulers
sdgen api schedulers

# Get model info
sdgen api model-info
```

---

## 📝 Configuration

### Global Config (`.sdgen_config.json`)

```json
{
  "configs_dir": "/path/to/your/templates",
  "output_dir": "/path/to/output",
  "api_url": "http://127.0.0.1:7860"
}
```

**Important:**
- Always use `~/.sdgen_config.json` in your home directory for global config
- `sdgen` searches current directory first, then home directory
- **WSL Users:** Use absolute WSL paths (e.g., `/mnt/d/StableDiffusion/output`) instead of Windows paths

**Output Directories:**
- Images saved to `{output_dir}/{session_name}_{timestamp}/`
- `--dry-run`: API requests saved as JSON in session directory

---

## 📄 YAML Template Format (V2.0)

### Basic Template

```yaml
version: '2.0'
name: 'My Template'
description: 'Template description'

imports:
  Expression: ../variations/expressions.yaml
  Outfit: ../variations/outfits.yaml

prompt: |
  masterpiece, {Expression}, {Outfit}, detailed

negative_prompt: |
  low quality, blurry

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1  # -1 = all combinations

parameters:
  width: 512
  height: 768
  steps: 30
  cfg_scale: 7.0
  sampler: DPM++ 2M Karras

output:
  session_name: my_session
  filename_keys:
    - Expression
    - Outfit
```

### Template with Selectors

```yaml
version: '2.0'
name: 'Advanced Template'

imports:
  Hair: ../variations/hair.yaml        # 50 variations
  Angle: ../variations/angles.yaml     # 20 variations
  Quality: ../variations/quality.yaml  # 10 variations

prompt: |
  portrait, {Hair[random:5]}, {Angle[#0,2,5]}, {Quality[$0]}

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1
```

**Selectors:**
- `{Hair[random:5]}` - 5 random variations
- `{Angle[#0,2,5]}` - Indices 0, 2, 5 only
- `{Quality[$0]}` - Weight 0 (random per image, excluded from combinatorial loop)

**Result:** 5 Hair × 3 Angle = 15 combinations, with Quality picked randomly for each.

### Template Inheritance

```yaml
# Base template: base_portrait.template.yaml
version: '2.0'
name: 'Base Portrait'

imports:
  Hair: ../variations/hair.yaml
  Outfit: ../variations/outfits.yaml

parameters:
  width: 832
  height: 1216
  steps: 24
  cfg_scale: 3.0
  sampler: DPM++ 2M Karras
```

```yaml
# Child template: portrait_smiling.prompt.yaml
version: '2.0'
name: 'Smiling Portrait'
implements: ../templates/base_portrait.template.yaml

prompt: |
  smiling, happy, {Hair}, {Outfit}, looking at viewer

generation:
  mode: random
  seed_mode: progressive
  seed: 1000
  max_images: 50

output:
  session_name: portrait_happy
```

**Inheritance rules:**
- `parameters` are merged (child overrides parent)
- `imports` are merged (child adds to parent)
- `prompt` in child replaces parent's prompt
- `generation` and `output` can be overridden

### Loop Ordering with Weights

Control combinatorial loop nesting order with weights:

```yaml
prompt: |
  {Outfit[$1]}, {Angle[$10]}, {Expression[$20]}
```

**Loop structure:**
- Lower weight = outer loop (changes less often)
- Higher weight = inner loop (changes more often)
- Weight 0 = excluded from loops (random per image)

**Result:**
```
for outfit in Outfits:         # Weight 1 (outer)
  for angle in Angles:         # Weight 10 (middle)
    for expression in Expressions:  # Weight 20 (inner)
      generate_image()
```

All expressions for each angle, all angles for each outfit.

---

## 🔍 Validation & Statistics

**Since 2025-10-13**, `sdgen` displays variation statistics before generation:

```
╭─────────────────────── Detected Variations ───────────────────────╮
│   HairCut: 40 variations                                           │
│   HairColor: 87 variations (4 files merged)                        │
│   EyeColor: 12 variations                                          │
│   Outfit: 156 variations (8 files merged)                          │
│                                                                    │
│   Total combinations: 6,518,400                                    │
│   Generation mode: random                                          │
│   Will generate: 20 images                                         │
╰────────────────────────────────────────────────────────────────────╯
```

**Common errors are detected automatically:**

### Error: Unresolved Placeholder

```
ValueError: Unresolved placeholders in template: EyeColor
These placeholders are used in the prompt/template but have no
corresponding variations defined in 'imports:' section.
Available variations: HairCut, HairColor, Outfit
```

**Solution:** Add missing import:
```yaml
imports:
  EyeColor: ../variations/eyecolors.yaml  # ← Add this
```

### Error: Wrong Selector Syntax

If you use `:$0` instead of `[$0]`, the placeholder won't be resolved correctly.

**Wrong:**
```yaml
prompt: |
  {Outfit:$0}, {HairCut:$0}  # ❌ WRONG SYNTAX
```

**Correct:**
```yaml
prompt: |
  {Outfit[$0]}, {HairCut[$0]}  # ✅ CORRECT SYNTAX
```

---

## 🗂️ Module Structure

```
CLI/
├── src/
│   ├── cli.py                 # Main CLI entry point (Typer)
│   │
│   ├── templating/            # Template System V2.0
│   │   ├── models/            # Data models
│   │   ├── loaders/           # YAML loading
│   │   ├── validators/        # Template validation
│   │   ├── resolvers/         # Inheritance & imports
│   │   ├── generators/        # Prompt generation
│   │   ├── normalizers/       # Prompt normalization
│   │   └── orchestrator.py    # Main V2 orchestrator
│   │
│   ├── api/                   # SD API client
│   │   ├── client.py
│   │   └── models.py
│   │
│   ├── config/                # Config management
│   │   └── global_config.py
│   │
│   └── execution/             # Execution & output
│       ├── executor.py
│       └── output_handler.py
│
├── tests/                     # Test suite
│   ├── api/                   # API client tests (76 tests)
│   ├── templating/            # Templating tests (3 tests)
│   ├── v2/                    # V2 system tests (227 tests)
│   │   ├── unit/
│   │   └── integration/
│   └── legacy/                # Old tests (archived)
│
└── pyproject.toml             # Package config
```

---

## 🧪 Examples

### Example 1: Basic Combinatorial

```yaml
version: '2.0'
name: 'Portrait Variations'

imports:
  Expression: ../variations/expressions.yaml
  Angle: ../variations/angles.yaml

prompt: |
  masterpiece, beautiful portrait, {Expression}, {Angle}, detailed

negative_prompt: |
  low quality, blurry

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1

parameters:
  width: 512
  height: 768
  steps: 30
  cfg_scale: 7.0
  sampler: DPM++ 2M Karras

output:
  session_name: portrait_variations
  filename_keys:
    - Expression
    - Angle
```

### Example 2: Random Exploration

```yaml
version: '2.0'
name: 'Creative Exploration'

imports:
  Style: ../variations/styles.yaml
  Subject: ../variations/subjects.yaml
  Lighting: ../variations/lighting.yaml

prompt: |
  concept art, {Style}, {Subject}, {Lighting}

negative_prompt: |
  low quality

generation:
  mode: random
  seed_mode: random
  seed: -1
  max_images: 100

output:
  session_name: creative_exploration
```

### Example 3: Character Sheet with Weights

```yaml
version: '2.0'
name: 'Character Sheet'

imports:
  Outfit: ../variations/outfits.yaml
  Angle: ../variations/angles.yaml
  Expression: ../variations/expressions.yaml

prompt: |
  1girl, character name, {Outfit[$1]}, {Angle[$10]}, {Expression[$20]}, high quality

negative_prompt: |
  low quality, bad anatomy

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1

output:
  session_name: character_sheet
  filename_keys:
    - Outfit
    - Angle
    - Expression
```

**Result:** Images organized by outfit (outer loop), then angle, then expression (inner loop).

---

## 📚 Documentation

- **[Getting Started](../docs/cli/usage/getting-started.md)** - First generation tutorial
- **[YAML Templating Guide](../docs/cli/usage/yaml-templating-guide.md)** - Complete V2.0 guide
- **[Examples](../docs/cli/usage/examples.md)** - Common use cases with correct syntax
- **[Variation Files](../docs/cli/usage/variation-files.md)** - Variation file format
- **[Architecture](../docs/cli/technical/architecture.md)** - Technical documentation

---

## 🧪 Testing

**IMPORTANT:** Always activate the venv first from the project root!

```bash
# Activate venv (from project root)
cd /mnt/d/StableDiffusion/local-sd-generator
source venv/bin/activate

# Go to CLI directory
cd CLI

# Run all tests (excluding legacy)
python3 -m pytest tests/ --ignore=tests/legacy -v

# Run specific test suites
python3 -m pytest tests/api/ -v                    # API tests (76 tests) ✅
python3 -m pytest tests/templating/ -v             # Templating tests (3 tests) ✅
python3 -m pytest tests/v2/ -v                     # V2 system tests (227 tests) 🟢

# With coverage
python3 -m pytest tests/v2/ --cov=templating --cov-report=term-missing -v
```

**Test Statistics:**
- **Total:** 306 tests
- **Passing:** 300 tests (98%)
- **API client:** 76 tests (100% ✅)
- **V2 templating:** 230 tests (96.5% 🟢)

---

## 🔧 Requirements

- **Python 3.8+** (use `python3` on WSL/Linux)
- **Stable Diffusion WebUI** with API enabled
- **Dependencies:** `pyyaml`, `requests`, `typer`, `rich`

```bash
# Install dependencies
pip install -r requirements.txt
```

---

## 🛠️ Development

### Code Quality Tools

```bash
# Style checking (PEP 8)
venv/bin/python3 -m flake8 CLI --exclude=tests,private_generators --max-line-length=120

# Complexity analysis
venv/bin/python3 -m radon cc CLI --exclude="tests,private_generators" -a -nb

# Dead code detection
cd CLI && ../venv/bin/python3 -m vulture . --min-confidence=80 2>&1 | grep -v "tests/" | grep -v "example_"

# Security scanning
venv/bin/python3 -m bandit -r CLI -ll -f txt
```

### Project Status

**Current version:** V2.0 (stable)
**Template system:** V2.0 only (V1 removed)
**Tests:** 306 total (98% pass rate)
**Last major migration:** 2025-10-10 (V1→V2 complete)

---

## 📞 Support

For issues, questions, or feature requests:
- Check documentation in `../docs/cli/`
- Review examples in `src/examples/prompts/`
- See roadmap in `../docs/roadmap/`

---

**Version:** V2.0 (Template System)
**Last Updated:** 2025-10-13
