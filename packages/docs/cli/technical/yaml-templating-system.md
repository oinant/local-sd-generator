# YAML Templating System (Phase 2)

**Status:** ✅ Complete and Active
**Created:** 2025-10-03
**Last Updated:** 2025-10-07
**Tests:** 52 passing ✅

---

## Overview

The Phase 2 YAML templating system provides a powerful, declarative way to define image generation prompts with:
- **Reusable chunks** - Template fragments that can be composed
- **Multi-field variations** - Single placeholder expands multiple fields
- **Advanced selectors** - Fine-grained control over which variations to use
- **Character templates** - Planned for future (see roadmap)

This system replaces the legacy Phase 1 JSON config approach with a more flexible and maintainable architecture.

---

## Current Architecture

### Module Structure

```
CLI/
├── templating/              # Phase 2 engine
│   ├── __init__.py
│   ├── types.py            # Data structures (PromptConfig, ResolvedVariation)
│   ├── loaders.py          # Load YAML files and variations
│   ├── selectors.py        # Parse selector syntax
│   ├── chunk.py            # Chunk template system
│   ├── multi_field.py      # Multi-field expansion
│   └── resolver.py         # Main resolution logic (6 SRP functions)
│
├── api/                     # SRP-compliant API module
│   ├── sdapi_client.py     # Pure HTTP API client
│   ├── session_manager.py  # Directory management
│   ├── image_writer.py     # File I/O
│   ├── progress_reporter.py # Console output
│   └── batch_generator.py  # Orchestration
│
├── output/                  # File naming & metadata
│   ├── output_namer.py     # SF-4: Intelligent naming
│   └── metadata_generator.py # SF-5: JSON metadata
│
├── config/                  # Global configuration
│   └── global_config.py    # SF-7: .sdgen_config.json
│
└── template_cli.py          # Main CLI entry point
```

### Test Coverage

```
tests/templating/            # 52 tests ✅
├── test_chunk.py           # 8 tests - Chunk loading & rendering
├── test_multi_field.py     # 8 tests - Multi-field expansion
├── test_selectors.py       # 13 tests - Selector parsing
├── test_selectors_chunk.py # 6 tests - Chunk-specific selectors
├── test_loaders.py         # 4 tests - YAML/variation loading
├── test_resolver.py        # 5 tests - Main resolution flow
├── test_prompt_config.py   # 3 tests - Config dataclass
└── test_phase2_integration.py # 5 tests - End-to-end
```

---

## File Format: `.prompt.yaml`

### Basic Example

```yaml
name: "Character Portrait"
description: "Generate character portraits with variations"

# Base prompt with placeholders
prompt:
  base: "masterpiece, {Expression}, {Angle}, beautiful character"
  negative: "low quality, blurry"

# Variation files
variations:
  Expression: variations/expressions.yaml
  Angle: variations/angles.yaml

# Generation parameters
generation:
  mode: combinatorial  # or random
  seed_mode: progressive  # or fixed, random
  seed: 42
  max_images: 50

# SD parameters
parameters:
  width: 512
  height: 768
  steps: 30
  cfg_scale: 7.0
  sampler: "DPM++ 2M Karras"
  scheduler: "Karras"  # Optional: explicit scheduler (SD 1.9+)
  batch_size: 1
  batch_count: 1

# Output configuration
output:
  session_name: "character_test"
  filename_keys: ["Expression", "Angle"]
```

### Variation Files (`.yaml`)

**Simple format:**
```yaml
# expressions.yaml
variations:
  - smiling
  - sad
  - angry
  - surprised
```

**With keys:**
```yaml
# expressions.yaml
variations:
  happy: smiling, cheerful
  sad: crying, melancholic
  neutral: neutral expression
```

**With weights (future feature):**
```yaml
variations:
  happy:
    value: smiling, cheerful
    weight: 5
  rare:
    value: rare expression
    weight: 1
```

---

## Advanced Features

### 1. Chunk Templates

Reusable template fragments that can be composed:

```yaml
# base/portrait_base.chunk.yaml
name: "Portrait Base"
type: chunk

fields:
  subject: "1girl"
  quality: "masterpiece, best quality"
  style: "{ArtStyle}"

template: "{quality}, {subject}, {style}"
```

**Usage in prompt:**
```yaml
prompt:
  base: "{PORTRAIT_BASE}, {Expression}"

chunks:
  PORTRAIT_BASE: base/portrait_base.chunk.yaml
```

### 2. Multi-Field Variations

One placeholder expands multiple fields:

```yaml
# ethnic_features.yaml
type: multi_field
variations:
  asian:
    hair: "black hair"
    skin: "fair skin"
    eyes: "dark brown eyes"

  african:
    hair: "black curly hair"
    skin: "dark skin"
    eyes: "brown eyes"
```

**Usage:**
```yaml
prompt:
  base: "{ETHNICITY}, beautiful character"

variations:
  ETHNICITY: ethnic_features.yaml  # Expands to hair+skin+eyes
```

### 3. Advanced Selectors

Fine-grained control over variations:

**Index selection:**
```yaml
prompt:
  base: "{Expression[0,2,5]}, portrait"  # Only indices 0, 2, 5
```

**Range selection:**
```yaml
prompt:
  base: "{Expression[0-4]}, portrait"  # Indices 0 through 4
```

**Random N:**
```yaml
prompt:
  base: "{Expression[:5]}, portrait"  # Random 5 expressions
```

**Key selection:**
```yaml
prompt:
  base: "{Expression[happy,sad]}, portrait"  # Only specific keys
```

**Chunk overrides:**
```yaml
prompt:
  base: "{PORTRAIT_BASE with style=ANIME_STYLE}, {Expression}"
```

---

## CLI Usage

### Interactive Mode

```bash
cd CLI
python3 template_cli.py
```

Prompts to select from available `.prompt.yaml` templates.

### Direct Template

```bash
python3 template_cli.py --template examples/prompts/portrait.prompt.yaml
```

### List Templates

```bash
python3 template_cli.py --list
```

### Dry Run (JSON output only)

```bash
python3 template_cli.py --template test.yaml --dry-run
```

### Override Image Count

```bash
python3 template_cli.py --template test.yaml --count 10
```

---

## Output Structure

### Session Directory

```
apioutput/
└── 20251007_143052_character_test/
    ├── character_test_0001.png
    ├── character_test_0002.png
    ├── ...
    ├── character_test_manifest.json
    └── metadata.json (future)
```

### Manifest File

Generated for each session with all variations:

```json
{
  "session_name": "character_test",
  "template_source": "/path/to/template.yaml",
  "generated_at": "2025-10-07T14:30:52",
  "total_variations": 50,
  "templating_system": "phase2",
  "variations": [
    {
      "index": 1,
      "prompt": "masterpiece, smiling, front view, beautiful character",
      "negative_prompt": "low quality, blurry",
      "seed": 42,
      "placeholders": {
        "Expression": "smiling",
        "Angle": "front view"
      }
    }
  ]
}
```

---

## Implementation Details

### Resolution Flow

**Main function:** `resolve_prompt(config, base_path)` in `templating/resolver.py`

**6 SRP-compliant steps:**

1. **`_validate_template_paths()`** - Verify all files exist
2. **`_load_variations_from_files()`** - Load variation files
3. **`_apply_selectors()`** - Apply selector syntax
4. **`_calculate_combinations()`** - Compute total combinations
5. **`_select_variations_by_mode()`** - Choose which to generate
6. **`_build_resolved_variations()`** - Create final variation list

**Complexity:** All functions rated A (simple) after refactoring from monolithic E-rated function

### Integration with API Module

```python
# template_cli.py (simplified)

# 1. Load and resolve template
config = load_prompt_config(template_path)
variations = resolve_prompt(config, base_path=template_path.parent)

# 2. Create API components
api_client = SDAPIClient(api_url=api_url)
session_manager = SessionManager(base_output_dir, session_name, dry_run)
image_writer = ImageWriter(session_manager.output_dir)
progress = ProgressReporter(total_images=len(variations), ...)
generator = BatchGenerator(api_client, session_manager, image_writer, progress, dry_run)

# 3. Convert to PromptConfig list
prompt_configs = [
    PromptConfig(
        prompt=var.final_prompt,
        negative_prompt=var.negative_prompt,
        seed=var.seed,
        filename=f"{session_name}_{idx:04d}.png"
    )
    for idx, var in enumerate(variations)
]

# 4. Generate
success_count, total_count = generator.generate_batch(prompt_configs, delay=2.0)
```

---

## Completed Features (from Phase 1 spec)

### ✅ SF-4: Enhanced File Naming System

**Module:** `CLI/output/output_namer.py`

**Features:**
- Session folder naming: `{timestamp}_{session_name}`
- Image filename: `{session_name}_{index:04d}.png`
- CamelCase sanitization for variation values
- Filename keys support (optional)

**Tests:** 27 passing

### ✅ SF-5: JSON Metadata Export

**Module:** `CLI/output/metadata_generator.py`

**Features:**
- Structured JSON metadata
- Backward compatibility with legacy text format
- Complete generation information
- Variation details included

**Tests:** 22 passing

### ✅ SF-7: Global Config File

**Module:** `CLI/config/global_config.py`

**Features:**
- `.sdgen_config.json` in project root
- Configurable `configs_dir` and `output_dir`
- Auto-creation with defaults
- Search order: project → home → defaults

**Tests:** 26 passing

---

## Migration from Legacy (Phase 1)

### What Changed

**Before (Phase 1 - Legacy):**
```python
from image_variation_generator import ImageVariationGenerator

generator = ImageVariationGenerator(
    prompt_template="masterpiece, {Expression}, {Angle}",
    negative_prompt="low quality",
    variation_files={
        "Expression": "/path/to/expressions.txt",
        "Angle": "/path/to/angles.txt"
    },
    seed=42,
    generation_mode="combinatorial",
    seed_mode="progressive"
)
generator.run()
```

**After (Phase 2 - YAML):**
```bash
# Create portrait.prompt.yaml
python3 template_cli.py --template portrait.prompt.yaml
```

**Benefits:**
- Declarative configuration
- Reusable templates
- Version controlled
- No Python code needed
- Advanced features (chunks, multi-field, selectors)

### Legacy Code Location

All Phase 1 code moved to `/legacy/` and removed from git tracking:
- `image_variation_generator.py` (23K)
- `sdapi_client.py` (16K)
- `variation_loader.py` (25K)
- 8 legacy test files
- 6 legacy documentation files

**Total removed:** 5,400+ lines of monolithic code

---

## Future Roadmap

See `/docs/roadmap/next/` for planned features:

### 1. Character Templates (Priority 6)

Reusable character definitions with inheritance:

```yaml
# characters/emma.char.yaml
extends: base/portrait_subject.char.template.yaml
name: "Emma"
fields:
  hair: "brown hair"
  eyes: "blue eyes"
  style: "{Outfit}"
```

### 2. Numeric Slider Placeholders (Priority 4)

For testing LoRA sliders:

```yaml
prompt:
  base: "portrait, <lora:DetailSlider:{DetailLevel}>"

variations:
  DetailLevel:
    type: numeric
    range: [-1, 3]
    step: 1  # -1, 0, 1, 2, 3
```

---

## Performance

**Configuration loading:** <50ms for typical templates
**Resolution:** <200ms for 100 variations
**Generation:** Limited by SD API (not templating system)

**Memory:** Variations resolved lazily when possible

---

## Best Practices

### Template Organization

```
prompts/
├── base/                    # Base chunks
│   ├── portrait_base.chunk.yaml
│   └── quality_tags.chunk.yaml
├── characters/              # Character definitions (future)
│   ├── emma.char.yaml
│   └── john.char.yaml
├── variations/              # Variation files
│   ├── expressions.yaml
│   ├── angles.yaml
│   └── outfits.yaml
└── portraits/               # Actual prompt templates
    ├── portrait_simple.prompt.yaml
    └── portrait_full.prompt.yaml
```

### Variation File Naming

- Use `.yaml` extension for structured variations
- Use `.txt` for simple line-based lists (legacy support)
- Name files after what they vary: `expressions.yaml`, not `exp.yaml`

### Prompt Template Tips

1. **Start simple** - Basic prompt + variations
2. **Add chunks** - Once patterns emerge
3. **Use multi-field** - For related attributes
4. **Apply selectors** - For fine-tuning

---

## Troubleshooting

### Template not found

```bash
# Check configs directory
python3 template_cli.py --list

# Verify global config
cat .sdgen_config.json
```

### Variation file errors

Ensure all files referenced in template exist:
```yaml
variations:
  Expression: variations/expressions.yaml  # Must exist!
```

### No variations generated

Check that variation files have content and proper format.

### Placeholder not replaced

Verify placeholder name matches variation key exactly (case-sensitive):
```yaml
prompt:
  base: "{Expression}"  # Must match key below

variations:
  Expression: ...  # Exact match required
```

---

## CLI Commands

### API Introspection

Query SD WebUI API for available options (requires WebUI running):

```bash
# List samplers
python3 template_cli.py --list-samplers

# List schedulers (SD 1.9+)
python3 template_cli.py --list-schedulers

# List models/checkpoints
python3 template_cli.py --list-models

# List upscalers (for Hires Fix)
python3 template_cli.py --list-upscalers

# Show current model info
python3 template_cli.py --show-model-info
```

### Scheduler Parameter

Modern SD WebUI (1.9+) separates sampler and scheduler:

```yaml
parameters:
  sampler: "DPM++ 2M"     # Base algorithm
  scheduler: "Karras"     # Noise schedule
```

Common schedulers: `Karras`, `Exponential`, `SGM Uniform` (SDXL), `Polyexponential`, `Align Your Steps`

See `examples/prompts/scheduler_example.prompt.yaml` for full example.

---

## Related Documentation

- [Getting Started Guide](../guide/getting-started.md)
- [User Guide - Complete Learning Path](../guide/README.md)
- [Templates Basics](../guide/3-templates-basics.md)
- [Templates Advanced](../guide/4-templates-advanced.md)
- [Roadmap](../../roadmap/README.md)
- [Architecture Overview](./architecture.md)

---

## Change History

| Date | Change |
|------|--------|
| 2025-10-03 | Phase 2 implementation complete (52 tests) |
| 2025-10-06 | API module refactoring (SRP architecture) |
| 2025-10-07 | Legacy Phase 1 removed, documentation updated |
| 2025-10-07 | Scheduler parameter + API introspection commands added |

---

**Status:** Production-ready ✅
**Maintainer:** Active development
**Support:** See GitHub issues
