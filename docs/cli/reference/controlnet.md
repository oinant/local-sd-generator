# ControlNet Reference

**Feature:** SD WebUI ControlNet extension integration
**Status:** ✅ Implemented
**Version:** 1.0
**Last Updated:** 2025-10-22

## Overview

ControlNet integration allows you to guide image generation using preprocessed control images (edges, depth, pose, etc.). The implementation supports preset files, inline configuration, and multiple ControlNet units with full parameter control.

---

## File Format

### .controlnet.yaml Structure

ControlNet preset files use the `.controlnet.yaml` extension.

**Required Fields:**
- `type: "controlnet_config"` - File type identifier
- `version: "1.0"` - Format version
- `units: [...]` - Array of ControlNet unit configurations

**Example:**
```yaml
type: controlnet_config
version: "1.0"

units:
  - model: control_v11p_sd15_canny
    module: canny
    weight: 1.0
    threshold_a: 100
    threshold_b: 200
    processor_res: 512
    guidance_start: 0.0
    guidance_end: 1.0
```

---

## ControlNet Unit Configuration

A **unit** represents one ControlNet preprocessor + model combination.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | ControlNet model name (e.g., `"control_v11p_sd15_canny"`) |

### Input Image

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `image` | string? | `null` | Path to control image or base64 encoded image data |

**Note:** Mutually exclusive with automatic preprocessor generation via `module`.

### Preprocessor

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `module` | string | `"none"` | Preprocessor module name |

**Common Preprocessors:**
- `"canny"` - Canny edge detection
- `"depth_midas"` - MiDaS depth estimation
- `"openpose"` - OpenPose skeleton detection
- `"softedge_hed"` - HED soft edge detection
- `"lineart"` - Line art detection
- `"none"` - No preprocessing (use raw image)

### Weight & Guidance

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `weight` | float | `1.0` | 0.0-2.0 | ControlNet influence strength |
| `guidance_start` | float | `0.0` | 0.0-1.0 | When to start applying guidance (% of steps) |
| `guidance_end` | float | `1.0` | 0.0-1.0 | When to stop applying guidance (% of steps) |

**Examples:**
```yaml
# Full strength throughout generation
weight: 1.0
guidance_start: 0.0
guidance_end: 1.0

# Apply only during early steps (structure)
weight: 1.2
guidance_start: 0.0
guidance_end: 0.5

# Apply only during late steps (details)
weight: 0.8
guidance_start: 0.5
guidance_end: 1.0
```

### Preprocessor Parameters

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `processor_res` | int | `512` | Preprocessor resolution (px) |
| `threshold_a` | float | `64.0` | Preprocessor param A (e.g., Canny low threshold) |
| `threshold_b` | float | `128.0` | Preprocessor param B (e.g., Canny high threshold) |

**Preprocessor-Specific Parameters:**

**Canny:**
- `threshold_a` - Low threshold (edges below this are discarded)
- `threshold_b` - High threshold (edges above this are kept)

**Depth:**
- `threshold_a` - Depth near plane
- `threshold_b` - Depth far plane

**OpenPose:**
- `threshold_a` - Detection confidence threshold
- `threshold_b` - Unused

### Control Modes

| Field | Type | Default | Options |
|-------|------|---------|---------|
| `control_mode` | string | `"Balanced"` | `"Balanced"`, `"My prompt is more important"`, `"ControlNet is more important"` |
| `resize_mode` | string | `"Crop and Resize"` | `"Just Resize"`, `"Crop and Resize"`, `"Resize and Fill"` |

**Control Mode Behavior:**
- **Balanced** - Equal weight between prompt and ControlNet
- **My prompt is more important** - Prioritize text prompt over ControlNet
- **ControlNet is more important** - Prioritize ControlNet over text prompt

### Advanced Options

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `pixel_perfect` | bool | `false` | Automatically adjust preprocessor resolution |
| `low_vram` | bool | `false` | Enable low VRAM mode (slower, less memory) |
| `guess_mode` | bool | `false` | Guess control strength automatically (experimental) |

---

## Usage in Templates

### Format 1: String (Single File Path)

Load a preset file by path (relative to `configs_dir` or absolute).

**Template:**
```yaml
parameters:
  controlnet: presets/canny.controlnet.yaml
```

**Resolution:**
1. Parse `.controlnet.yaml` file
2. Load all units from file
3. Return `ControlNetConfig` with units

### Format 2: List (Multiple Files + Overrides)

Load multiple preset files and/or apply overrides to the first unit.

**Template:**
```yaml
parameters:
  controlnet:
    - presets/canny.controlnet.yaml
    - presets/depth.controlnet.yaml
    - weight: 0.8  # Override first unit's weight
```

**Resolution:**
1. Parse each `.controlnet.yaml` file in order
2. Merge all units into single `ControlNetConfig`
3. Apply dict overrides to **first unit only**

**List Element Types:**
- **String** - Path to `.controlnet.yaml` file
- **Dict** - Override parameters for first unit

### Format 3: Dict (Inline Configuration)

Define a single ControlNet unit inline without a preset file.

**Template:**
```yaml
parameters:
  controlnet:
    model: control_v11p_sd15_canny
    module: canny
    weight: 1.0
    threshold_a: 100
    threshold_b: 200
```

**Resolution:**
1. Create single `ControlNetUnit` from dict
2. Return `ControlNetConfig` with one unit

### Disabling ControlNet

**Option 1: Omit the field**
```yaml
parameters:
  # No controlnet field = ControlNet disabled
  sampler_name: DPM++ 2M Karras
```

**Option 2: Set to null**
```yaml
parameters:
  controlnet: null
```

---

## API Format

### SD WebUI API Structure

ControlNet configuration is injected into the `alwayson_scripts` field of the generation payload.

**Payload Example:**
```json
{
  "prompt": "masterpiece, beautiful landscape",
  "negative_prompt": "low quality",
  "steps": 30,
  "cfg_scale": 7.0,
  "alwayson_scripts": {
    "controlnet": {
      "args": [
        {
          "enabled": true,
          "module": "canny",
          "model": "control_v11p_sd15_canny",
          "weight": 1.0,
          "image": null,
          "resize_mode": "Crop and Resize",
          "low_vram": false,
          "processor_res": 512,
          "threshold_a": 100.0,
          "threshold_b": 200.0,
          "guidance_start": 0.0,
          "guidance_end": 1.0,
          "control_mode": "Balanced",
          "pixel_perfect": false,
          "guessmode": false
        }
      ]
    }
  }
}
```

**Key Points:**
- `args` is an array of unit objects (not a flat array like ADetailer)
- Each unit is a nested object with all parameters
- Maximum units depend on SD WebUI ControlNet extension configuration

---

## Python API

### Data Models

**File:** `sd_generator_cli/templating/models/controlnet.py`

#### ControlNetUnit

Single ControlNet unit configuration.

**Constructor:**
```python
from sd_generator_cli.templating.models.controlnet import ControlNetUnit

unit = ControlNetUnit(
    model="control_v11p_sd15_canny",
    module="canny",
    weight=1.0,
    threshold_a=100.0,
    threshold_b=200.0,
    processor_res=512,
    guidance_start=0.0,
    guidance_end=1.0,
    resize_mode="Crop and Resize",
    control_mode="Balanced",
    pixel_perfect=False,
    low_vram=False,
    guess_mode=False
)
```

**Methods:**

##### `to_dict() -> dict[str, Any]`

Convert to plain dict for JSON serialization (e.g., manifest files).

**Returns:** Dictionary with all fields (mirrors dataclass structure)

**Example:**
```python
unit = ControlNetUnit(model="control_v11p_sd15_canny", module="canny")
config_dict = unit.to_dict()
print(config_dict["model"])  # "control_v11p_sd15_canny"
```

##### `to_api_dict() -> dict[str, Any]`

Convert to SD WebUI ControlNet API format.

**Returns:** Dictionary matching SD WebUI API structure (includes `enabled: true`)

**Example:**
```python
unit = ControlNetUnit(model="control_v11p_sd15_canny", module="canny")
api_dict = unit.to_api_dict()
print(api_dict["enabled"])  # True
print(api_dict["model"])    # "control_v11p_sd15_canny"
```

#### ControlNetConfig

Container for one or more ControlNet units.

**Constructor:**
```python
from sd_generator_cli.templating.models.controlnet import ControlNetConfig, ControlNetUnit

unit1 = ControlNetUnit(model="control_v11p_sd15_canny", module="canny")
unit2 = ControlNetUnit(model="control_v11p_sd15_depth", module="depth_midas")

config = ControlNetConfig(units=[unit1, unit2])
```

**Methods:**

##### `to_dict() -> dict[str, Any]`

Convert to plain dict for JSON serialization.

**Returns:** `{"units": [unit.to_dict() for unit in self.units]}`

**Example:**
```python
config = ControlNetConfig(units=[unit1, unit2])
config_dict = config.to_dict()
print(len(config_dict["units"]))  # 2
```

##### `to_api_dict() -> Optional[dict[str, Any]]`

Convert to `alwayson_scripts` payload format.

**Returns:**
- `{"controlnet": {"args": [...]}}` if units exist
- `None` if no units (enables conditional ControlNet usage)

**Example:**
```python
# No units → None
config = ControlNetConfig(units=[])
print(config.to_api_dict())  # None

# With units → payload
config = ControlNetConfig(units=[unit1])
payload = config.to_api_dict()
print("controlnet" in payload)  # True
print(len(payload["controlnet"]["args"]))  # 1
```

### Parser Functions

**File:** `sd_generator_cli/templating/loaders/controlnet_parser.py`

#### `parse_controlnet_file(file_path: str | Path) -> ControlNetConfig`

Parse a `.controlnet.yaml` preset file.

**Args:**
- `file_path` - Path to `.controlnet.yaml` file (absolute or relative)

**Returns:** `ControlNetConfig` with parsed units

**Raises:**
- `FileNotFoundError` - File doesn't exist
- `ControlNetParseError` - Invalid file format or structure

**Example:**
```python
from sd_generator_cli.templating.loaders.controlnet_parser import parse_controlnet_file

config = parse_controlnet_file("presets/canny.controlnet.yaml")
print(len(config.units))           # 1
print(config.units[0].model)       # "control_v11p_sd15_canny"
```

**Validation:**
- Checks `type: "controlnet_config"`
- Checks `version: "1.0"`
- Validates `units` is non-empty array
- Validates each unit has required `model` field

#### `resolve_controlnet_parameter(value: Any, base_path: str | Path) -> Optional[ControlNetConfig]`

Resolve `parameters.controlnet` field (supports all 3 formats).

**Args:**
- `value` - The controlnet parameter value (`str | list | dict | None`)
- `base_path` - Base directory for resolving relative paths

**Returns:** `ControlNetConfig` or `None` if value is `None`

**Example:**
```python
from pathlib import Path
from sd_generator_cli.templating.loaders.controlnet_parser import resolve_controlnet_parameter

# Format 1: String path
config = resolve_controlnet_parameter(
    "presets/canny.controlnet.yaml",
    Path("/configs")
)

# Format 2: List with overrides
config = resolve_controlnet_parameter(
    ["presets/canny.controlnet.yaml", {"weight": 0.8}],
    Path("/configs")
)

# Format 3: Inline dict
config = resolve_controlnet_parameter(
    {"model": "control_v11p_sd15_canny", "module": "canny"},
    Path("/configs")
)
```

---

## CLI Commands

### List Available ControlNet Models

**Command:** `sdgen api controlnet-models`

**Purpose:** Query SD WebUI API for installed ControlNet models

**Example:**
```bash
# Using default API URL from config
sdgen api controlnet-models

# Using custom API URL
sdgen api controlnet-models --api-url http://192.168.1.100:7860
```

**Output Example:**
```
Available ControlNet Models (15 found)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   Model Name                       Category
───────────────────────────────────────────
1   control_v11p_sd15_canny          Canny
2   control_v11p_sd15_depth          Depth
3   control_v11p_sd15_openpose       Pose
4   control_v11p_sd15_softedge       Edge
5   control_v11p_sd15_lineart        Line Art
...
```

**Model Categories:**
- **Canny** - Contains "canny"
- **Depth** - Contains "depth"
- **Pose** - Contains "pose" or "openpose"
- **Edge** - Contains "softedge" or "hed"
- **Line Art** - Contains "lineart"
- **Other** - Everything else

---

## Common Use Cases

### Basic Edge Control

Control composition using Canny edge detection.

**Preset File:** `presets/canny_basic.controlnet.yaml`
```yaml
type: controlnet_config
version: "1.0"

units:
  - model: control_v11p_sd15_canny
    module: canny
    weight: 1.0
    threshold_a: 100
    threshold_b: 200
```

**Usage:**
```yaml
parameters:
  controlnet: presets/canny_basic.controlnet.yaml
```

### Multi-Unit: Structure + Depth

Combine Canny (structure) and Depth (3D information).

**Preset File:** `presets/canny_depth.controlnet.yaml`
```yaml
type: controlnet_config
version: "1.0"

units:
  - model: control_v11p_sd15_canny
    module: canny
    weight: 0.8
    guidance_start: 0.0
    guidance_end: 0.5  # Structure only in early steps

  - model: control_v11p_sd15_depth
    module: depth_midas
    weight: 0.6
    guidance_start: 0.0
    guidance_end: 1.0  # Depth throughout generation
```

**Usage:**
```yaml
parameters:
  controlnet: presets/canny_depth.controlnet.yaml
```

### Pose-Guided Character Generation

Control character pose using OpenPose skeleton detection.

**Preset File:** `presets/openpose_character.controlnet.yaml`
```yaml
type: controlnet_config
version: "1.0"

units:
  - model: control_v11p_sd15_openpose
    module: openpose
    weight: 1.2
    processor_res: 512
    control_mode: ControlNet is more important
```

**Usage:**
```yaml
parameters:
  controlnet: presets/openpose_character.controlnet.yaml
```

### Dynamic Override

Load preset but adjust weight per generation.

**Template:**
```yaml
parameters:
  controlnet:
    - presets/canny_basic.controlnet.yaml
    - weight: 0.7  # Override default weight
    - guidance_end: 0.6  # Override guidance range
```

---

## Integration with Parameters

ControlNet can be combined with other SD WebUI parameters.

**Example:**
```yaml
parameters:
  # ControlNet
  controlnet: presets/canny_basic.controlnet.yaml

  # ADetailer (face refinement)
  adetailer: presets/face_hq.adetailer.yaml

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
    "controlnet": {
      "args": [/* ControlNet units */]
    },
    "ADetailer": {
      "args": [/* ADetailer detectors */]
    }
  }
}
```

---

## Error Handling

### File Not Found

**Error:**
```
FileNotFoundError: ControlNet preset file not found: presets/missing.controlnet.yaml
```

**Fix:**
- Check file path is correct (relative to `configs_dir`)
- Verify file has `.controlnet.yaml` extension
- Check file exists: `ls presets/`

### Invalid File Type

**Error:**
```
ControlNetParseError: Invalid type in presets/foo.controlnet.yaml. Expected 'controlnet_config', got 'adetailer_config'
```

**Fix:**
- Use correct preset file type
- Check `type:` field matches file extension

### Missing Required Field

**Error:**
```
ControlNetParseError: Unit #0 in presets/canny.controlnet.yaml missing required field 'model'
```

**Fix:**
- Add `model` field to every unit
- Example: `model: control_v11p_sd15_canny`

### Invalid Version

**Error:**
```
ControlNetParseError: Invalid version in presets/canny.controlnet.yaml. Expected '1.0', got '2.0'
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
│   │   └── controlnet.py          # ControlNetUnit, ControlNetConfig
│   └── loaders/
│       └── controlnet_parser.py   # parse_controlnet_file, resolve_controlnet_parameter
└── api/
    └── sdapi_client.py            # API client with ControlNet injection
```

### Data Flow

```
Template YAML
    ↓
parameters:
  controlnet: "presets/canny.controlnet.yaml"
    ↓
resolve_controlnet_parameter()
    ↓
parse_controlnet_file()
    ↓
ControlNetConfig(units=[...])
    ↓
config.to_api_dict()
    ↓
{"controlnet": {"args": [...]}}
    ↓
Injected into alwayson_scripts
    ↓
API Request → SD WebUI
```

### Manifest Serialization

ControlNet configuration is saved in manifest files for reproducibility.

**Manifest Structure:**
```json
{
  "session_name": "test_session",
  "images": [
    {
      "filename": "image_001.png",
      "parameters": {
        "controlnet": {
          "units": [
            {
              "model": "control_v11p_sd15_canny",
              "module": "canny",
              "weight": 1.0,
              "threshold_a": 100.0,
              "threshold_b": 200.0,
              ...
            }
          ]
        }
      }
    }
  ]
}
```

**Serialization Method:** `ControlNetConfig.to_dict()`

---

## Testing

**Test Files:**
- `tests/unit/test_controlnet_models.py` - Data model tests
- `tests/unit/test_controlnet_parser.py` - Parser tests
- `tests/integration/test_controlnet_integration.py` - End-to-end tests

**Run Tests:**
```bash
cd packages/sd-generator-cli
../../venv/bin/python3 -m pytest tests/unit/test_controlnet_models.py -v
../../venv/bin/python3 -m pytest tests/unit/test_controlnet_parser.py -v
```

---

## See Also

- [ADetailer Reference](./adetailer.md) - Region-specific refinement
- [Template System Reference](./template-system.md) - Core template system
- [Parameters Reference](./parameters.md) - All SD WebUI parameters
