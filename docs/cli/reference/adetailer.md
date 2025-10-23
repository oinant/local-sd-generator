# ADetailer Reference

**Feature:** SD WebUI ADetailer extension integration
**Status:** ✅ Implemented
**Version:** 1.0
**Last Updated:** 2025-10-22

## Overview

ADetailer (After Detailer) integration enables automatic region-specific enhancement during image generation. It detects regions (faces, hands, bodies) using YOLO models and applies a secondary inpainting pass with customizable prompts and parameters.

---

## File Format

### .adetailer.yaml Structure

ADetailer preset files use the `.adetailer.yaml` extension.

**Required Fields:**
- `type: "adetailer_config"` - File type identifier
- `version: "1.0"` - Format version
- `detectors: [...]` - Array of detector configurations

**Example:**
```yaml
type: adetailer_config
version: "1.0"

detectors:
  - ad_model: face_yolov9c.pt
    ad_denoising_strength: 0.5
    ad_mask_k_largest: 1
    ad_steps: 40
    ad_use_steps: true

  - ad_model: hand_yolov8n.pt
    ad_mask_k_largest: 2
    ad_denoising_strength: 0.4
    ad_steps: 40
    ad_use_steps: true
```

---

## Detector Configuration

A **detector** represents one detection pass (e.g., face detector, hand detector).

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `ad_model` | string | Detection model name (e.g., `"face_yolov9c.pt"`) |

### Detection Parameters

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `ad_confidence` | float | `0.3` | 0.0-1.0 | Detection confidence threshold |
| `ad_mask_k_largest` | int | `0` | 0+ | Number of regions to process (0 = all) |
| `ad_tab_enable` | bool | `true` | - | Enable this detector |
| `ad_model_classes` | string | `""` | - | Filter by model classes (comma-separated) |

**Examples:**
```yaml
# Detect all faces
ad_confidence: 0.3
ad_mask_k_largest: 0

# Detect only the largest face
ad_confidence: 0.3
ad_mask_k_largest: 1

# Detect 2 largest hands
ad_model: hand_yolov8n.pt
ad_confidence: 0.5
ad_mask_k_largest: 2
```

### Prompts (Optional)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ad_prompt` | string | `""` | Prompt for inpainting pass (empty = use main prompt) |
| `ad_negative_prompt` | string | `""` | Negative prompt for inpainting pass |

**Examples:**
```yaml
# Use main prompt
ad_prompt: ""
ad_negative_prompt: ""

# Custom face prompt
ad_prompt: "highly detailed face, sharp eyes, perfect skin"
ad_negative_prompt: "blurry, distorted, low quality"
```

### Mask Processing

| Field | Type | Default | Options | Description |
|-------|------|---------|---------|-------------|
| `ad_mask_filter_method` | string | `"Area"` | `"Area"`, `"Confidence"` | How to sort detected regions |
| `ad_mask_min_ratio` | float | `0.0` | 0.0-1.0 | Min mask size (% of image) |
| `ad_mask_max_ratio` | float | `1.0` | 0.0-1.0 | Max mask size (% of image) |
| `ad_dilate_erode` | int | `4` | - | Mask expansion (positive) or shrinking (negative) |
| `ad_mask_blur` | int | `4` | 0+ | Edge softening (Gaussian blur radius) |
| `ad_x_offset` | int | `0` | - | Horizontal mask offset (pixels) |
| `ad_y_offset` | int | `0` | - | Vertical mask offset (pixels) |
| `ad_mask_merge_invert` | string | `"None"` | `"None"`, `"Merge"`, `"Merge and Invert"` | Multi-mask merge strategy |

**Examples:**
```yaml
# Standard mask processing
ad_dilate_erode: 4    # Expand mask by 4px
ad_mask_blur: 4       # Soften edges

# Filter by size (faces between 5% and 50% of image)
ad_mask_min_ratio: 0.05
ad_mask_max_ratio: 0.50
```

### Inpainting Region

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ad_inpaint_only_masked` | bool | `true` | Only inpaint masked region (vs entire image) |
| `ad_inpaint_only_masked_padding` | int | `32` | Padding around mask (pixels) |
| `ad_use_inpaint_width_height` | bool | `false` | Use custom inpaint dimensions |
| `ad_inpaint_width` | int | `512` | Custom inpaint width (if `ad_use_inpaint_width_height=true`) |
| `ad_inpaint_height` | int | `512` | Custom inpaint height (if `ad_use_inpaint_width_height=true`) |

**Examples:**
```yaml
# Standard inpainting (masked region only)
ad_inpaint_only_masked: true
ad_inpaint_only_masked_padding: 32

# Force 512x512 inpaint region
ad_use_inpaint_width_height: true
ad_inpaint_width: 512
ad_inpaint_height: 512
```

### Denoising Strength

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `ad_denoising_strength` | float | `0.4` | 0.0-1.0 | Enhancement strength (higher = more change) |

**Guidelines:**
- **0.2-0.3** - Subtle refinement (fix minor issues)
- **0.4-0.5** - Standard enhancement (default range)
- **0.6-0.7** - Strong modification (redraw region)
- **0.8-1.0** - Complete redraw (may lose original structure)

**Examples:**
```yaml
# Subtle face refinement
ad_denoising_strength: 0.3

# Standard face enhancement
ad_denoising_strength: 0.5

# Aggressive hand fix
ad_denoising_strength: 0.7
```

### Generation Overrides

Override main generation parameters for this detector.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ad_use_steps` | bool | `false` | Use custom steps count |
| `ad_steps` | int | `28` | Steps for inpainting (if `ad_use_steps=true`) |
| `ad_use_cfg_scale` | bool | `false` | Use custom CFG scale |
| `ad_cfg_scale` | float | `7.0` | CFG scale for inpainting |
| `ad_use_sampler` | bool | `false` | Use custom sampler |
| `ad_sampler` | string | `"DPM++ 2M Karras"` | Sampler name |
| `ad_scheduler` | string | `"Use same scheduler"` | Scheduler override |

**Examples:**
```yaml
# Use more steps for face refinement
ad_use_steps: true
ad_steps: 40

# Use different sampler for hands
ad_use_sampler: true
ad_sampler: Euler a
```

### Model Overrides

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ad_use_checkpoint` | bool | `false` | Use different checkpoint |
| `ad_checkpoint` | string? | `null` | Checkpoint model name |
| `ad_use_vae` | bool | `false` | Use different VAE |
| `ad_vae` | string? | `null` | VAE model name |

**Example:**
```yaml
# Use specialized face model
ad_use_checkpoint: true
ad_checkpoint: "realisticVision_v50.safetensors"
```

### Advanced Options

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ad_use_noise_multiplier` | bool | `false` | Use custom noise multiplier |
| `ad_noise_multiplier` | float | `1.0` | Noise strength multiplier |
| `ad_use_clip_skip` | bool | `false` | Use custom CLIP skip |
| `ad_clip_skip` | int | `1` | CLIP skip value |
| `ad_restore_face` | bool | `false` | Apply face restoration (CodeFormer/GFPGAN) |

### ControlNet Integration (Future)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ad_controlnet_model` | string | `"None"` | ControlNet model for this detector |
| `ad_controlnet_module` | string | `"None"` | ControlNet preprocessor |
| `ad_controlnet_weight` | float | `1.0` | ControlNet weight |
| `ad_controlnet_guidance_start` | float | `0.0` | ControlNet guidance start |
| `ad_controlnet_guidance_end` | float | `1.0` | ControlNet guidance end |

---

## Usage in Templates

### Format 1: String (Single File Path)

Load a preset file by path (relative to `configs_dir` or absolute).

**Template:**
```yaml
parameters:
  adetailer: presets/face_hq.adetailer.yaml
```

**Resolution:**
1. Parse `.adetailer.yaml` file
2. Load all detectors from file
3. Return `ADetailerConfig` with detectors

### Format 2: List (Multiple Files + Overrides)

Load multiple preset files and/or apply overrides per detector.

**Template (Simple Paths):**
```yaml
parameters:
  adetailer:
    - presets/face_hq.adetailer.yaml
    - presets/hand_fix.adetailer.yaml
```

**Template (With Overrides):**
```yaml
parameters:
  adetailer:
    - import: presets/face_hq.adetailer.yaml
      override:
        ad_denoising_strength: 0.6
        ad_prompt: "detailed face, {Expression}"  # Supports placeholders!
    - import: presets/hand_fix.adetailer.yaml
      override:
        ad_confidence: 0.4
    - presets/body.adetailer.yaml  # Mix simple paths
```

**Resolution:**
1. Parse each `.adetailer.yaml` file in order
2. Apply per-detector overrides if using `import:` + `override:` format
3. Merge all detectors into single `ADetailerConfig`

**List Element Types:**
- **String** - Path to `.adetailer.yaml` file
- **Dict with `import` + `override`** - Override specific detector parameters

**🎯 New Feature:** Override prompts support `{Placeholder}` syntax that references the same variations as the main prompt (no combinatoric impact). See [Overriding Preset Parameters](#overriding-preset-parameters) for details.

### Format 3: Dict (Inline Configuration)

Define a single detector inline without a preset file.

**Template:**
```yaml
parameters:
  adetailer:
    ad_model: face_yolov9c.pt
    ad_denoising_strength: 0.5
    ad_mask_k_largest: 1
    ad_steps: 40
    ad_use_steps: true
```

**Resolution:**
1. Create single `ADetailerDetector` from dict
2. Return `ADetailerConfig` with one detector

### Disabling ADetailer

**Option 1: Omit the field**
```yaml
parameters:
  # No adetailer field = ADetailer disabled
  sampler_name: DPM++ 2M Karras
```

**Option 2: Set to null**
```yaml
parameters:
  adetailer: null
```

---

## API Format

### SD WebUI API Structure

ADetailer configuration is injected into the `alwayson_scripts` field of the generation payload.

**Payload Example:**
```json
{
  "prompt": "masterpiece, beautiful girl",
  "negative_prompt": "low quality",
  "steps": 30,
  "cfg_scale": 7.0,
  "alwayson_scripts": {
    "ADetailer": {
      "args": [
        true,    // [0] ad_enable (global)
        false,   // [1] skip_img2img (global)

        // Detector 1 (indices 2-73+)
        "face_yolov9c.pt",  // [2] ad_model
        "",                 // [3] ad_model_classes
        true,               // [4] ad_tab_enable
        "",                 // [5] ad_prompt
        "",                 // [6] ad_negative_prompt
        0.3,                // [7] ad_confidence
        "Area",             // [8] ad_mask_filter_method
        1,                  // [9] ad_mask_k (maps from ad_mask_k_largest)
        0.0,                // [10] ad_mask_min_ratio
        1.0,                // [11] ad_mask_max_ratio
        4,                  // [12] ad_dilate_erode
        0,                  // [13] ad_x_offset
        0,                  // [14] ad_y_offset
        "None",             // [15] ad_mask_merge_invert
        4,                  // [16] ad_mask_blur
        0.5,                // [17] ad_denoising_strength
        true,               // [18] ad_inpaint_only_masked
        32,                 // [19] ad_inpaint_only_masked_padding
        false,              // [20] ad_use_inpaint_width_height
        512,                // [21] ad_inpaint_width
        512,                // [22] ad_inpaint_height
        true,               // [23] ad_use_steps
        40,                 // [24] ad_steps
        false,              // [25] ad_use_cfg_scale
        7.0,                // [26] ad_cfg_scale
        // ... more parameters ...

        // Detector 2 (if present)
        "hand_yolov8n.pt",  // ad_model
        // ... more parameters ...
      ]
    }
  }
}
```

**Key Points:**
- Flat args array (not nested objects)
- First 2 elements are global flags (`ad_enable`, `skip_img2img`)
- Each detector adds ~72 elements to the array
- `ad_mask_k_largest` → `ad_mask_k` in API
- Maximum detectors depend on SD WebUI ADetailer extension configuration

---

## Python API

### Data Models

**File:** `sd_generator_cli/templating/models/config_models.py`

#### ADetailerDetector

Single detector configuration.

**Constructor:**
```python
from sd_generator_cli.templating.models.config_models import ADetailerDetector

detector = ADetailerDetector(
    ad_model="face_yolov9c.pt",
    ad_confidence=0.3,
    ad_mask_k_largest=1,
    ad_denoising_strength=0.5,
    ad_mask_blur=4,
    ad_dilate_erode=4,
    ad_inpaint_only_masked=True,
    ad_inpaint_only_masked_padding=32,
    ad_use_steps=True,
    ad_steps=40
)
```

**Methods:**

##### `to_dict() -> dict`

Convert to plain dict for JSON serialization (e.g., manifest files).

**Returns:** Dictionary with all fields (mirrors dataclass structure)

**Example:**
```python
detector = ADetailerDetector(ad_model="face_yolov9c.pt")
config_dict = detector.to_dict()
print(config_dict["ad_model"])  # "face_yolov9c.pt"
```

##### `to_api_dict() -> dict`

Convert to SD WebUI ADetailer API format.

**Returns:** Dictionary matching SD WebUI API structure

**Note:** Maps `ad_mask_k_largest` → `ad_mask_k` for API compatibility

**Example:**
```python
detector = ADetailerDetector(ad_model="face_yolov9c.pt", ad_mask_k_largest=1)
api_dict = detector.to_api_dict()
print(api_dict["ad_mask_k"])  # 1 (note: different field name)
```

#### ADetailerConfig

Container for one or more detectors.

**Constructor:**
```python
from sd_generator_cli.templating.models.config_models import ADetailerConfig, ADetailerDetector

detector1 = ADetailerDetector(ad_model="face_yolov9c.pt")
detector2 = ADetailerDetector(ad_model="hand_yolov8n.pt")

config = ADetailerConfig(enabled=True, detectors=[detector1, detector2])
```

**Methods:**

##### `to_dict() -> dict`

Convert to plain dict for JSON serialization.

**Returns:** `{"enabled": bool, "detectors": [detector.to_dict() for ...]}`

**Example:**
```python
config = ADetailerConfig(enabled=True, detectors=[detector1, detector2])
config_dict = config.to_dict()
print(len(config_dict["detectors"]))  # 2
```

##### `to_api_dict() -> Optional[dict]`

Convert to `alwayson_scripts` payload format.

**Returns:**
- `{"ADetailer": {"args": [...]}}` if detectors exist
- `None` if no detectors (enables conditional ADetailer usage)

**Example:**
```python
# No detectors → None
config = ADetailerConfig(enabled=False, detectors=[])
print(config.to_api_dict())  # None

# With detectors → payload
config = ADetailerConfig(enabled=True, detectors=[detector1])
payload = config.to_api_dict()
print("ADetailer" in payload)  # True
```

### Parser Functions

**File:** `sd_generator_cli/templating/loaders/parser.py`

#### `parse_adetailer_file(file_path: str | Path) -> ADetailerConfig`

Parse a `.adetailer.yaml` preset file.

**Args:**
- `file_path` - Path to `.adetailer.yaml` file (absolute or relative)

**Returns:** `ADetailerConfig` with parsed detectors

**Raises:**
- `FileNotFoundError` - File doesn't exist
- `ValueError` - Invalid file format or structure

**Example:**
```python
from sd_generator_cli.templating.loaders.parser import ConfigParser

parser = ConfigParser()
config = parser._parse_adetailer_file("presets/face_hq.adetailer.yaml")
print(len(config.detectors))           # 1
print(config.detectors[0].ad_model)    # "face_yolov9c.pt"
```

**Validation:**
- Checks `type: "adetailer_config"`
- Checks `version: "1.0"`
- Validates `detectors` is non-empty array
- Validates each detector has required `ad_model` field

#### `resolve_adetailer_parameter(value: Any, base_path: str | Path) -> Optional[ADetailerConfig]`

Resolve `parameters.adetailer` field (supports all 3 formats).

**Args:**
- `value` - The adetailer parameter value (`str | list | dict | None`)
- `base_path` - Base directory for resolving relative paths

**Returns:** `ADetailerConfig` or `None` if value is `None`

**Example:**
```python
from pathlib import Path
from sd_generator_cli.templating.loaders.parser import ConfigParser

parser = ConfigParser()

# Format 1: String path
config = parser._resolve_adetailer_parameter(
    "presets/face_hq.adetailer.yaml",
    Path("/configs")
)

# Format 2: List with overrides
config = parser._resolve_adetailer_parameter(
    ["presets/face_hq.adetailer.yaml", {"ad_denoising_strength": 0.6}],
    Path("/configs")
)

# Format 3: Inline dict
config = parser._resolve_adetailer_parameter(
    {"ad_model": "face_yolov9c.pt", "ad_denoising_strength": 0.5},
    Path("/configs")
)
```

---

## CLI Commands

### List Available ADetailer Models

**Command:** `sdgen api adetailer-models`

**Purpose:** Query SD WebUI API for installed ADetailer detection models

**Example:**
```bash
# Using default API URL from config
sdgen api adetailer-models

# Using custom API URL
sdgen api adetailer-models --api-url http://192.168.1.100:7860
```

**Output Example:**
```
Available ADetailer Models (20 found)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   Model Name                Category
──────────────────────────────────────────
1   face_yolov9c.pt           Face
2   face_yolov8n.pt           Face
3   face_yolov8s.pt           Face
4   hand_yolov8n.pt           Hand
5   hand_yolov8s.pt           Hand
6   person_yolov8n-seg.pt     Person
7   mediapipe_face_full.pt    MediaPipe
...
```

**Model Categories:**
- **Face** - Contains "face"
- **Hand** - Contains "hand"
- **Person** - Contains "person"
- **MediaPipe** - Contains "mediapipe"
- **Other** - Everything else

---

## Common Use Cases

### Basic Face Enhancement

Enhance face quality with default settings.

**Preset File:** `presets/face_basic.adetailer.yaml`
```yaml
type: adetailer_config
version: "1.0"

detectors:
  - ad_model: face_yolov9c.pt
    ad_denoising_strength: 0.4
    ad_mask_k_largest: 1
```

**Usage:**
```yaml
parameters:
  adetailer: presets/face_basic.adetailer.yaml
```

### High-Quality Face Refinement

Use more steps and stronger denoising for HQ faces.

**Preset File:** `presets/face_hq.adetailer.yaml`
```yaml
type: adetailer_config
version: "1.0"

detectors:
  - ad_model: face_yolov9c.pt
    ad_denoising_strength: 0.5
    ad_mask_k_largest: 1
    ad_steps: 40
    ad_use_steps: true
    ad_mask_blur: 6
```

**Usage:**
```yaml
parameters:
  adetailer: presets/face_hq.adetailer.yaml
```

### Multi-Detector: Face + Hands

Enhance both faces and hands in a single generation.

**Preset File:** `presets/face_hands.adetailer.yaml`
```yaml
type: adetailer_config
version: "1.0"

detectors:
  - ad_model: face_yolov9c.pt
    ad_denoising_strength: 0.5
    ad_mask_k_largest: 1
    ad_steps: 40
    ad_use_steps: true

  - ad_model: hand_yolov8n.pt
    ad_mask_k_largest: 2  # Process both hands
    ad_denoising_strength: 0.4
    ad_steps: 40
    ad_use_steps: true
```

**Usage:**
```yaml
parameters:
  adetailer: presets/face_hands.adetailer.yaml
```

### Custom Face Prompt

Use a specialized prompt for face inpainting.

**Preset File:** `presets/face_detailed.adetailer.yaml`
```yaml
type: adetailer_config
version: "1.0"

detectors:
  - ad_model: face_yolov9c.pt
    ad_prompt: "highly detailed face, sharp eyes, perfect skin texture, realistic lighting"
    ad_negative_prompt: "blurry, distorted, disfigured, low quality"
    ad_denoising_strength: 0.5
    ad_mask_k_largest: 1
    ad_steps: 40
    ad_use_steps: true
```

**Usage:**
```yaml
parameters:
  adetailer: presets/face_detailed.adetailer.yaml
```

### Overriding Preset Parameters

Override specific fields from a preset file without creating a new file.

**Supported Formats:**

#### 1. Dict Override (Single Detector)
```yaml
parameters:
  adetailer:
    import: presets/face_hq.adetailer.yaml
    override:
      ad_denoising_strength: 0.6  # Override strength
      ad_steps: 50                # Override steps
```

#### 2. List with Overrides (Multiple Detectors)
```yaml
parameters:
  adetailer:
    - import: presets/face_hq.adetailer.yaml
      override:
        ad_denoising_strength: 0.6
    - import: presets/hand_fix.adetailer.yaml
      override:
        ad_confidence: 0.4
    - presets/body.adetailer.yaml  # Simple path (no override)
```

#### 3. Override with Placeholders

**Key Feature:** Override prompts can use `{Placeholder}` syntax to reference the same variations used in the main prompt, **without affecting combinatorial generation**.

**Example:**

**Variations File (`expressions.yaml`):**
```yaml
happy: smiling, joyful expression
sad: melancholic, tearful
angry: furious, intense gaze
```

**Prompt File:**
```yaml
version: "2.0"
name: Dynamic Expression Test
generation:
  mode: combinatorial
  seed: 42

imports:
  Expression: ./expressions.yaml

prompt: "{Expression} girl, beautiful face, masterpiece"

parameters:
  adetailer:
    import: presets/face_hq.adetailer.yaml
    override:
      ad_prompt: "detailed face, {Expression}, sharp eyes, perfect skin"
```

**Behavior:**
- **Image 1** with `Expression = "smiling, joyful expression"`:
  - Main prompt: `"smiling, joyful expression girl, beautiful face, masterpiece"`
  - ADetailer prompt: `"detailed face, smiling, joyful expression, sharp eyes, perfect skin"`

- **Image 2** with `Expression = "melancholic, tearful"`:
  - Main prompt: `"melancholic, tearful girl, beautiful face, masterpiece"`
  - ADetailer prompt: `"detailed face, melancholic, tearful, sharp eyes, perfect skin"`

**Important Notes:**
- Placeholders in ADetailer prompts use the **SAME values** as the main prompt
- **NO new combinatorial variations** are created
- If a placeholder is not found in variations, it remains unchanged `{Placeholder}`
- Works in both `ad_prompt` and `ad_negative_prompt`

**Multi-Detector Example:**
```yaml
parameters:
  adetailer:
    - import: face.adetailer.yaml
      override:
        ad_prompt: "{Expression} face, {EyeColor} eyes"
    - import: hand.adetailer.yaml
      override:
        ad_prompt: "perfect hands, {Pose}"
```

---

## Integration with Parameters

ADetailer can be combined with other SD WebUI parameters.

**Example:**
```yaml
parameters:
  # ADetailer (face refinement)
  adetailer: presets/face_hq.adetailer.yaml

  # ControlNet (composition control)
  controlnet: presets/canny_basic.controlnet.yaml

  # Standard parameters
  sampler_name: DPM++ 2M Karras
  steps: 30
  cfg_scale: 7.0
  width: 768
  height: 512
```

**API Payload Result:**
```json
{
  "sampler_name": "DPM++ 2M Karras",
  "steps": 30,
  "cfg_scale": 7.0,
  "width": 768,
  "height": 512,
  "alwayson_scripts": {
    "ADetailer": {
      "args": [/* ADetailer detectors */]
    },
    "controlnet": {
      "args": [/* ControlNet units */]
    }
  }
}
```

---

## Error Handling

### File Not Found

**Error:**
```
FileNotFoundError: ADetailer preset file not found: presets/missing.adetailer.yaml
```

**Fix:**
- Check file path is correct (relative to `configs_dir`)
- Verify file has `.adetailer.yaml` extension
- Check file exists: `ls presets/`

### Invalid File Type

**Error:**
```
ValueError: Invalid type in presets/foo.adetailer.yaml. Expected 'adetailer_config', got 'controlnet_config'
```

**Fix:**
- Use correct preset file type
- Check `type:` field matches file extension

### Missing Required Field

**Error:**
```
ValueError: Detector #0 in presets/face.adetailer.yaml missing required field 'ad_model'
```

**Fix:**
- Add `ad_model` field to every detector
- Example: `ad_model: face_yolov9c.pt`

### Invalid Version

**Error:**
```
ValueError: Invalid version in presets/face.adetailer.yaml. Expected '1.0', got '2.0'
```

**Fix:**
- Use `version: "1.0"` (current supported version)
- Check file format matches this documentation

---

## Implementation Details

### File Locations

**Source Files:**
```
sd_generator_cli/
├── templating/
│   ├── models/
│   │   └── config_models.py          # ADetailerDetector, ADetailerConfig
│   └── loaders/
│       └── parser.py                 # parse_adetailer_file, resolve_adetailer_parameter
└── api/
    └── sdapi_client.py               # API client with ADetailer injection
```

### Data Flow

```
Template YAML
    ↓
parameters:
  adetailer: "presets/face_hq.adetailer.yaml"
    ↓
resolve_adetailer_parameter()
    ↓
parse_adetailer_file()
    ↓
ADetailerConfig(detectors=[...])
    ↓
config.to_api_dict()
    ↓
{"ADetailer": {"args": [...]}}
    ↓
Injected into alwayson_scripts
    ↓
API Request → SD WebUI
```

### Manifest Serialization

ADetailer configuration is saved in manifest files for reproducibility.

**Manifest Structure:**
```json
{
  "session_name": "test_session",
  "images": [
    {
      "filename": "image_001.png",
      "parameters": {
        "adetailer": {
          "enabled": true,
          "detectors": [
            {
              "ad_model": "face_yolov9c.pt",
              "ad_denoising_strength": 0.5,
              "ad_mask_k_largest": 1,
              "ad_steps": 40,
              "ad_use_steps": true,
              ...
            }
          ]
        }
      }
    }
  ]
}
```

**Serialization Method:** `ADetailerConfig.to_dict()`

---

## Testing

**Test Files:**
- `tests/unit/test_adetailer_models.py` - Data model tests (12 tests)
- `tests/unit/test_adetailer_parser.py` - Parser tests (15 tests)
- `tests/unit/api/test_sdapi_client.py` - API integration tests (3 tests)

**Run Tests:**
```bash
cd packages/sd-generator-cli
../../venv/bin/python3 -m pytest tests/unit/test_adetailer_models.py -v
../../venv/bin/python3 -m pytest tests/unit/test_adetailer_parser.py -v
../../venv/bin/python3 -m pytest tests/unit/api/test_sdapi_client.py::TestSDAPIClient::test_get_adetailer_models -v
```

**Test Coverage:** 30 tests total

---

## Performance Tips

### Balancing Quality vs Speed

**Fast (0.3-0.4 strength, 20-30 steps):**
```yaml
ad_denoising_strength: 0.3
ad_use_steps: true
ad_steps: 20
```

**Balanced (0.4-0.5 strength, 30-40 steps):**
```yaml
ad_denoising_strength: 0.4
ad_use_steps: true
ad_steps: 30
```

**Quality (0.5-0.6 strength, 40-50 steps):**
```yaml
ad_denoising_strength: 0.5
ad_use_steps: true
ad_steps: 40
```

### Multi-Detector Strategies

**Sequential Processing:**
- Detector 1: Face (high priority, high steps)
- Detector 2: Hands (lower priority, fewer steps)

```yaml
detectors:
  - ad_model: face_yolov9c.pt
    ad_denoising_strength: 0.5
    ad_steps: 40
    ad_use_steps: true

  - ad_model: hand_yolov8n.pt
    ad_denoising_strength: 0.4
    ad_steps: 30
    ad_use_steps: true
```

---

## See Also

- [ControlNet Reference](./controlnet.md) - Composition guidance
- [Template System Reference](./template-system.md) - Core template system
- [Parameters Reference](./parameters.md) - All SD WebUI parameters
- [SD WebUI ADetailer Extension](https://github.com/Bing-su/adetailer) - Upstream project
