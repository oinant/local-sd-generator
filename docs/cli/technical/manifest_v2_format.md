# Manifest V2 Format - Technical Specification

**Version:** 2.0
**Status:** Production
**Last Updated:** 2025-10-13

## Overview

The Manifest V2 format is a complete snapshot system that captures all information necessary to reproduce image generations. Each generation session creates a `manifest.json` file containing:

- Complete snapshot of the generation configuration
- Runtime information (model checkpoint, etc.)
- Resolved template with placeholders
- All generation and API parameters
- Variation values used
- Metadata for each generated image

## Purpose

The Manifest V2 system addresses the following needs:

1. **Reproducibility** - Recreate generations even after template modifications
2. **Traceability** - Know exactly what produced each image
3. **Portability** - Self-contained format independent of original files
4. **History** - Archive successful configurations without keeping templates

## File Structure

### Top Level

```json
{
  "snapshot": { /* Configuration snapshot */ },
  "images": [ /* Array of generated images */ ]
}
```

### Snapshot Section

The `snapshot` object contains all generation metadata:

```json
{
  "snapshot": {
    "version": "2.0",
    "timestamp": "2025-10-13T14:23:45Z",
    "runtime_info": { /* Runtime environment */ },
    "resolved_template": { /* Template with placeholders */ },
    "generation_params": { /* Generation settings */ },
    "api_params": { /* SD WebUI API parameters */ },
    "variations": { /* Variation values used */ }
  }
}
```

#### version (string)

Manifest format version. Always `"2.0"` for this specification.

```json
"version": "2.0"
```

#### timestamp (string)

ISO 8601 timestamp of generation start.

```json
"timestamp": "2025-10-13T14:23:45.123456"
```

#### runtime_info (object)

Runtime environment information captured from SD WebUI API.

**Fields:**
- `sd_model_checkpoint` (string): Currently loaded model/checkpoint
  - Format: `"model_name.safetensors [hash]"`
  - Value: `"unknown"` if API unavailable

```json
"runtime_info": {
  "sd_model_checkpoint": "animefull_v1.safetensors [abc123def456]"
}
```

**Future extensions** (reserved for future use):
- `sd_vae`: VAE model name
- `clip_skip`: CLIP skip value
- `extensions_enabled`: List of active extensions
- `webui_version`: A1111/Forge version

#### resolved_template (object)

The template after Phase 1 resolution (chunk injection) but before variation substitution.

**Fields:**
- `prompt` (string): Positive prompt with placeholders
- `negative` (string): Negative prompt with placeholders

```json
"resolved_template": {
  "prompt": "masterpiece, {Expression}, {Angle}, beautiful girl, detailed",
  "negative": "low quality, {Defect}, blurry"
}
```

**Notes:**
- Placeholders are in `{Name}` format
- This is the template used for variation substitution
- Chunks are already injected (no `@Chunk` references)

#### generation_params (object)

Generation orchestration parameters.

**Fields:**
- `mode` (string): Generation mode
  - `"combinatorial"`: All combinations of variations
  - `"random"`: Random sampling of combinations
- `seed_mode` (string): Seed management strategy
  - `"fixed"`: Same seed for all images
  - `"progressive"`: Incremental seeds (seed, seed+1, seed+2, ...)
  - `"random"`: Random seed (-1) for each image
- `base_seed` (integer): Starting seed value
  - `-1` for random seed
- `num_images` (integer): Number of images generated
- `total_combinations` (integer): Total possible combinations

```json
"generation_params": {
  "mode": "random",
  "seed_mode": "progressive",
  "base_seed": 42,
  "num_images": 100,
  "total_combinations": 240
}
```

#### api_params (object)

Complete SD WebUI API parameters sent with each request.

**Core parameters:**
- `steps` (integer): Number of sampling steps
- `cfg_scale` (float): CFG scale value
- `width` (integer): Image width in pixels
- `height` (integer): Image height in pixels
- `sampler_name` (string): Sampler algorithm name
- `scheduler` (string|null): Scheduler name (Karras, Exponential, etc.)
- `batch_size` (integer): Images per batch
- `n_iter` (integer): Number of iterations

**Hires Fix parameters** (if `enable_hr` is true):
- `enable_hr` (boolean): Hires Fix enabled
- `hr_scale` (float): Upscale factor
- `hr_upscaler` (string): Upscaler model name
- `denoising_strength` (float): Denoising strength for second pass
- `hr_second_pass_steps` (integer|null): Steps for second pass

**Other parameters:**
- `restore_faces` (boolean): Face restoration enabled
- `tiling` (boolean): Tiling mode
- `seed`, `subseed`, `subseed_strength` (various): Seed settings
- `override_settings` (object): Temporary settings overrides
- `alwayson_scripts` (object): Extension scripts (ADetailer, ControlNet, etc.)

```json
"api_params": {
  "steps": 30,
  "cfg_scale": 7.5,
  "width": 512,
  "height": 768,
  "sampler_name": "DPM++ 2M Karras",
  "scheduler": "karras",
  "batch_size": 1,
  "n_iter": 1,
  "enable_hr": false,
  "restore_faces": false,
  "tiling": false,
  "seed": 42,
  "subseed": -1,
  "subseed_strength": 0,
  "alwayson_scripts": {},
  "override_settings": {},
  "send_images": true,
  "save_images": false
}
```

**Notes:**
- Contains ALL parameters from API payload
- Scripts (ADetailer, etc.) are in `alwayson_scripts` if used
- Portable across different SD implementations (adapt as needed)

#### variations (object)

Map of placeholder names to variation metadata including complete pool and used values.

**Structure:**
```json
{
  "PlaceholderName": {
    "available": ["all", "possible", "values"],
    "used": ["actually", "used", "values"],
    "count": 50
  }
}
```

**Fields:**
- `available` (array): Complete pool of variation values from import files
- `used` (array): Subset of values actually used in generation
- `count` (integer): Total number of available values (redundant but convenient)

**Example:**
```json
"variations": {
  "Expression": {
    "available": [
      "happy", "sad", "angry", "surprised", "neutral",
      "smiling", "frowning", "laughing", "crying", "shocked",
      "... (40 more values)"
    ],
    "used": [
      "happy", "sad", "angry", "surprised", "neutral"
    ],
    "count": 50
  },
  "Angle": {
    "available": [
      "front", "side", "back", "3/4 view", "top view",
      "bottom view", "diagonal", "close-up"
    ],
    "used": [
      "front", "side", "back", "3/4 view", "top view"
    ],
    "count": 8
  },
  "Defect": {
    "available": ["blurry", "distorted"],
    "used": ["blurry", "distorted"],
    "count": 2
  }
}
```

**Notes:**
- `available` contains the complete pool from variation files
- `used` contains only values actually used in generated images
- Useful when selectors (`[random:N]`, `[limit:N]`) reduce the pool
- Order may not be preserved from original files
- Empty object `{}` if no variations used

**Use Case:**
With `{Expression[random:5]}`, you might have:
- `available`: 50 expressions from file
- `used`: 5 randomly selected expressions
- This lets you see what was available vs what was actually used

### Images Section

Array of generated image metadata:

```json
{
  "images": [
    {
      "filename": "img_0001.png",
      "seed": 42,
      "prompt": "masterpiece, happy, front, beautiful girl, detailed",
      "negative_prompt": "low quality, blurry, blurry",
      "applied_variations": {
        "Expression": "happy",
        "Angle": "front",
        "Defect": "blurry"
      }
    }
  ]
}
```

#### Image Object

Each image in the `images` array has these fields:

**Fields:**
- `filename` (string): Image filename (relative to manifest)
- `seed` (integer): Actual seed used for generation
  - May differ from `base_seed` if `seed_mode` is `progressive` or `random`
- `prompt` (string): Final resolved prompt sent to API
  - All placeholders substituted with actual values
- `negative_prompt` (string): Final resolved negative prompt
- `applied_variations` (object): Variation values for this specific image

```json
{
  "filename": "img_0042.png",
  "seed": 84,
  "prompt": "masterpiece, smiling happily, side view, beautiful girl, detailed",
  "negative_prompt": "low quality, distorted, blurry",
  "applied_variations": {
    "Expression": "smiling happily",
    "Angle": "side view",
    "Defect": "distorted"
  }
}
```

## Complete Example

```json
{
  "snapshot": {
    "version": "2.0",
    "timestamp": "2025-10-13T14:23:45.678901",
    "runtime_info": {
      "sd_model_checkpoint": "animefull_v1.safetensors [abc123def456]"
    },
    "resolved_template": {
      "prompt": "masterpiece, best quality, 1girl, {Expression}, {Angle}, detailed face",
      "negative": "low quality, worst quality, {Defect}"
    },
    "generation_params": {
      "mode": "random",
      "seed_mode": "progressive",
      "base_seed": 42,
      "num_images": 10,
      "total_combinations": 50
    },
    "api_params": {
      "steps": 30,
      "cfg_scale": 7.5,
      "width": 512,
      "height": 768,
      "sampler_name": "DPM++ 2M Karras",
      "scheduler": "karras",
      "batch_size": 1,
      "n_iter": 1,
      "enable_hr": false,
      "restore_faces": false,
      "tiling": false,
      "seed": 42,
      "subseed": -1,
      "subseed_strength": 0,
      "alwayson_scripts": {},
      "override_settings": {}
    },
    "variations": {
      "Expression": {
        "available": ["happy", "sad", "neutral", "surprised", "angry", "smiling", "frowning", "laughing", "crying", "shocked"],
        "used": ["happy", "sad", "neutral", "surprised", "angry"],
        "count": 10
      },
      "Angle": {
        "available": ["front", "side", "3/4 view", "back"],
        "used": ["front", "side", "3/4 view", "back"],
        "count": 4
      },
      "Defect": {
        "available": ["blurry", "distorted"],
        "used": ["blurry", "distorted"],
        "count": 2
      }
    }
  },
  "images": [
    {
      "filename": "img_0001.png",
      "seed": 42,
      "prompt": "masterpiece, best quality, 1girl, happy, front, detailed face",
      "negative_prompt": "low quality, worst quality, blurry",
      "applied_variations": {
        "Expression": "happy",
        "Angle": "front",
        "Defect": "blurry"
      }
    },
    {
      "filename": "img_0002.png",
      "seed": 43,
      "prompt": "masterpiece, best quality, 1girl, sad, side, detailed face",
      "negative_prompt": "low quality, worst quality, distorted",
      "applied_variations": {
        "Expression": "sad",
        "Angle": "side",
        "Defect": "distorted"
      }
    }
  ]
}
```

## Use Cases

### Reproducing a Generation

To reproduce images from a manifest:

1. **Extract snapshot data**:
   - `resolved_template.prompt` and `negative`
   - `variations` values
   - `api_params` settings
   - `generation_params` (mode, seed strategy)

2. **Recreate template** (optional):
   - Create new `.prompt.yaml` file
   - Use `resolved_template` as template
   - Create variation files from `variations` object

3. **Recreate specific image**:
   - Use `prompt` and `negative_prompt` from image object
   - Use exact `seed` value
   - Apply same `api_params`

### Analyzing Successful Generations

```python
import json

with open('manifest.json', 'r') as f:
    manifest = json.load(f)

# What model was used?
model = manifest['snapshot']['runtime_info']['sd_model_checkpoint']
print(f"Model: {model}")

# What were the generation settings?
params = manifest['snapshot']['generation_params']
print(f"Mode: {params['mode']}, Seeds: {params['seed_mode']}")

# What variations were available vs used?
variations = manifest['snapshot']['variations']
for placeholder, data in variations.items():
    print(f"{placeholder}:")
    print(f"  Available: {data['count']} values")
    print(f"  Used: {len(data['used'])} values")
    if data['count'] > len(data['used']):
        print(f"  Selector reduced pool by {data['count'] - len(data['used'])} values")

# Which variations produced the best results?
for img in manifest['images']:
    print(f"{img['filename']}: {img['applied_variations']}")

# Were there any unused variations?
for placeholder, data in variations.items():
    unused = set(data['available']) - set(data['used'])
    if unused:
        print(f"{placeholder} - Unused values ({len(unused)}): {list(unused)[:5]}...")
```

### Comparing Sessions

Compare two manifests to see what changed:

```python
# Compare prompts
prompt1 = manifest1['snapshot']['resolved_template']['prompt']
prompt2 = manifest2['snapshot']['resolved_template']['prompt']

# Compare parameters
params1 = manifest1['snapshot']['api_params']
params2 = manifest2['snapshot']['api_params']

# Compare variations
vars1 = manifest1['snapshot']['variations']
vars2 = manifest2['snapshot']['variations']
```

## Implementation Notes

### Generation Process

1. **Before generation**:
   - Create snapshot with template, params, and empty images array
   - Retrieve runtime info from API (`/sdapi/v1/options`)
   - Extract variation values from generated prompts
   - Write initial manifest

2. **After generation**:
   - Update manifest with actual seeds from metadata files
   - Add final prompts and applied variations per image
   - Write final manifest

### Error Handling

- If API unavailable: `runtime_info.sd_model_checkpoint = "unknown"`
- If metadata file missing: Use seed from prompt generation
- Manifest write failures should not block image generation

### File Location

Manifest is always written to:
```
{output_dir}/{session_name}/manifest.json
```

Example:
```
output/portrait_20251013_142345/manifest.json
output/portrait_20251013_142345/img_0001.png
output/portrait_20251013_142345/img_0002.png
...
```

## Migration from V1

The V1 manifest format is deprecated. Key differences:

| Feature | V1 | V2 |
|---------|----|----|
| Runtime info | ❌ No | ✅ Yes (checkpoint) |
| Template | ❌ No | ✅ Yes (with placeholders) |
| Variations values | ❌ Partial | ✅ Complete |
| API params | ❌ Partial | ✅ Complete |
| Seed tracking | ❌ No | ✅ Yes (actual seeds) |
| Self-contained | ❌ No | ✅ Yes |

## Future Extensions

Possible additions to the format (backward compatible):

- `runtime_info.vae`: VAE model name
- `runtime_info.clip_skip`: CLIP skip value
- `runtime_info.extensions`: Active extensions list
- `runtime_info.webui_version`: A1111/Forge version
- `snapshot.source_files`: Original template and variation file paths/hashes
- `images[].metadata`: Additional per-image metadata (face detection, etc.)
- `statistics`: Summary statistics (avg seed, most common variations, etc.)

## See Also

- [Rebuild Tool Specification](../../roadmap/future/rebuild_tool.md) - Reconstruct templates from manifests
- [Template System V2.0](./template_system_v2.md) - Template format and resolution
- [Generation Modes](./generation_modes.md) - Combinatorial vs Random generation
