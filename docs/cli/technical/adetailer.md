# ADetailer Integration - Technical Documentation

**Status:** ✅ Implemented
**Version:** 1.0
**Last Updated:** 2025-10-13

## Overview

The ADetailer integration enables automatic region-specific enhancement (faces, hands, etc.) during image generation. The implementation supports preset files, inline configuration, and multiple detectors with full parameter control.

## Architecture

### Component Structure

```
CLI/src/
├── templating/
│   ├── models/
│   │   └── adetailer.py                # Data models (ADetailerDetector, ADetailerConfig)
│   ├── loaders/
│   │   └── adetailer_parser.py         # .adetailer.yaml file parser
│   └── resolvers/
│       ├── import_resolver.py          # .adetailer.yaml import support
│       └── parameters_resolver.py      # parameters.adetailer resolution
├── api/
│   └── sdapi_client.py                 # API client with ADetailer injection
└── cli.py                              # CLI commands (sdgen api adetailer-models)

CLI/tests/
├── api/
│   └── test_sdapi_client.py            # API client tests (3 tests)
└── v2/unit/
    ├── test_adetailer_models.py        # Data model tests (12 tests)
    └── test_adetailer_parser.py        # Parser tests (15 tests)
```

### Data Flow

```
Template YAML → Parameters Resolver → ADetailer Config → API Payload
     ↓                    ↓                   ↓              ↓
parameters:      parse_adetailer_file()  to_api_dict()  alwayson_scripts
 adetailer:      or inline dict          ADetailerConfig  injection
```

## Data Models

### ADetailerDetector

**File:** `CLI/src/templating/models/adetailer.py`

Represents a single detection pass configuration (e.g., face detector, hand detector).

**Key Fields:**
```python
@dataclass
class ADetailerDetector:
    # Required
    ad_model: str                           # Detection model (e.g., "face_yolov9c.pt")

    # Core parameters
    ad_prompt: str = ""
    ad_negative_prompt: str = ""
    ad_confidence: float = 0.3              # Detection threshold
    ad_mask_k_largest: int = 1              # Number of regions to process
    ad_mask_blur: int = 4                   # Edge softening
    ad_dilate_erode: int = 4                # Mask expansion
    ad_denoising_strength: float = 0.4      # Enhancement strength

    # Inpainting region
    ad_inpaint_only_masked: bool = True
    ad_inpaint_only_masked_padding: int = 32
    ad_use_inpaint_width_height: bool = False
    ad_inpaint_width: int = 512
    ad_inpaint_height: int = 512

    # Steps override
    ad_use_steps: bool = False
    ad_steps: int = 28

    # Advanced overrides
    ad_use_cfg_scale: bool = False
    ad_cfg_scale: float = 7.0
    ad_use_checkpoint: bool = False
    ad_checkpoint: str = ""
    ad_use_vae: bool = False
    ad_vae: str = ""
    ad_use_sampler: bool = False
    ad_sampler: str = ""
    ad_use_noise_multiplier: bool = False
    ad_noise_multiplier: float = 1.0
    ad_use_clip_skip: bool = False
    ad_clip_skip: int = 1
    ad_restore_face: bool = False

    # Positioning
    ad_x_offset: int = 0
    ad_y_offset: int = 0
    ad_mask_merge_invert: str = "none"

    # ControlNet (future)
    ad_controlnet_model: str = "none"
    ad_controlnet_module: str = "none"
    ad_controlnet_weight: float = 1.0
    ad_controlnet_guidance_start: float = 0.0
    ad_controlnet_guidance_end: float = 1.0
```

### ADetailerConfig

**File:** `CLI/src/templating/models/adetailer.py`

Container for one or more detectors. Converts to SD WebUI API format.

**Key Methods:**

#### `to_api_dict() -> Optional[dict]`

Converts configuration to SD WebUI API payload format.

**Returns:**
```python
{
    "ADetailer": {
        "args": [
            # Global flags (2 elements)
            True,   # ad_enable
            False,  # skip_img2img

            # First detector (72 elements, indices 2-73)
            "face_yolov9c.pt",  # ad_model
            "",                 # ad_prompt
            "",                 # ad_negative_prompt
            0.3,                # ad_confidence
            # ... 67 more parameters

            # Second detector (72 elements, indices 74-145)
            "hand_yolov8n.pt",  # ad_model
            # ... 71 more parameters
        ]
    }
}
```

**Total args length:** `2 + (72 × num_detectors)`

**Returns `None` if:** No detectors configured (enables conditional ADetailer usage).

## File Format

### .adetailer.yaml Structure

**Type:** `adetailer_config`
**Version:** `"1.0"`

**Required Fields:**
- `type: adetailer_config`
- `version: "1.0"`
- `detectors: [...]` (array of detector configs)

**Example:**
```yaml
type: adetailer_config
version: "1.0"

detectors:
  - ad_model: face_yolov9c.pt
    ad_denoising_strength: 0.5
    ad_steps: 40
    ad_mask_k_largest: 1
    ad_use_steps: true

  - ad_model: hand_yolov8n.pt
    ad_mask_k_largest: 2
    ad_denoising_strength: 0.4
    ad_use_steps: true
    ad_steps: 40
```

### Validation Rules

1. **type** must be `"adetailer_config"`
2. **version** must be `"1.0"`
3. **detectors** must be non-empty array
4. Each detector must have **ad_model** field

## Parameter Resolution

### Supported Formats

The `parameters.adetailer` field supports 3 formats:

#### Format 1: String (Path)

```yaml
parameters:
  adetailer: variations/adetailer/faces/face_hq.adetailer.yaml
```

**Resolution:**
1. Parse file at path (relative to `configs_dir`)
2. Return `ADetailerConfig` with detectors from file

#### Format 2: List (Multiple Files + Overrides)

```yaml
parameters:
  adetailer:
    - variations/adetailer/faces/face_hq.adetailer.yaml
    - variations/adetailer/hands/hand_fix.adetailer.yaml
    - ad_model: face_yolov8n.pt  # Override
```

**Resolution:**
1. Parse each `.adetailer.yaml` file in list
2. Merge all detectors into single `ADetailerConfig`
3. Apply dict overrides to **first detector**

**List Elements:**
- **String:** Path to `.adetailer.yaml` file
- **Dict:** Override parameters for first detector

#### Format 3: Dict (Inline Configuration)

```yaml
parameters:
  adetailer:
    ad_model: face_yolov9c.pt
    ad_denoising_strength: 0.5
    ad_steps: 40
```

**Resolution:**
1. Create single `ADetailerDetector` from dict
2. Return `ADetailerConfig` with one detector

### Resolution Logic

**File:** `CLI/src/templating/resolvers/parameters_resolver.py`

```python
def resolve_adetailer_parameter(value, base_path: str) -> Optional[ADetailerConfig]:
    """
    Resolve parameters.adetailer field

    Args:
        value: str | list | dict | None
        base_path: Base directory for resolving relative paths

    Returns:
        ADetailerConfig or None
    """
    if value is None:
        return None

    if isinstance(value, str):
        # Format 1: Single file path
        return parse_adetailer_file(resolve_path(value, base_path))

    elif isinstance(value, list):
        # Format 2: Multiple files + overrides
        detectors = []
        overrides = None

        for item in value:
            if isinstance(item, str):
                # Parse file and add detectors
                config = parse_adetailer_file(resolve_path(item, base_path))
                detectors.extend(config.detectors)
            elif isinstance(item, dict):
                # Store overrides for first detector
                if overrides is None:
                    overrides = item

        if detectors:
            # Apply overrides to first detector
            if overrides:
                for key, val in overrides.items():
                    setattr(detectors[0], key, val)

            return ADetailerConfig(detectors=detectors)

        return None

    elif isinstance(value, dict):
        # Format 3: Inline config
        detector = ADetailerDetector(**value)
        return ADetailerConfig(detectors=[detector])

    return None
```

## Import Resolver Integration

**File:** `CLI/src/templating/resolvers/import_resolver.py`

The import resolver was extended to support `.adetailer.yaml` files alongside `.yaml` imports.

**Changes:**
```python
def resolve_imports(config: TemplateConfig, configs_dir: str) -> dict[str, Any]:
    """
    Resolve imports: field

    Supports:
    - .yaml files → dict
    - .adetailer.yaml files → ADetailerConfig
    - inline strings → string
    """
    if not config.imports:
        return {}

    resolved = {}
    for key, value in config.imports.items():
        if isinstance(value, str):
            if value.endswith('.adetailer.yaml'):
                # Parse ADetailer preset file
                resolved[key] = parse_adetailer_file(...)
            elif value.endswith('.yaml'):
                # Parse YAML variations
                resolved[key] = parse_variations_file(...)
            else:
                # Inline string
                resolved[key] = value

    return resolved
```

**Usage Example:**
```yaml
imports:
  face_preset: variations/adetailer/faces/face_hq.adetailer.yaml

parameters:
  adetailer: $face_preset  # Future: Use @reference syntax
```

**Note:** Currently, direct path syntax is recommended. `@reference` syntax is planned for future enhancement.

## API Client Integration

**File:** `CLI/src/api/sdapi_client.py`

### Method: `get_adetailer_models()`

**Endpoint:** `/adetailer/v1/ad_model`

**Returns:** `list[str]` - Available detection model names

**Example:**
```python
client = SDAPIClient()
models = client.get_adetailer_models()
# ["face_yolov9c.pt", "face_yolov8n.pt", "hand_yolov8n.pt", ...]
```

### Method: `_build_payload()`

**Change:** Injects `alwayson_scripts` when `parameters.adetailer` is present.

```python
def _build_payload(self, prompt_config: PromptConfig) -> dict:
    payload = {
        "prompt": ...,
        "negative_prompt": ...,
        # ... base fields
    }

    # Add ADetailer if configured
    if prompt_config.parameters and 'adetailer' in prompt_config.parameters:
        adetailer_config = prompt_config.parameters['adetailer']
        if hasattr(adetailer_config, 'to_api_dict'):
            adetailer_payload = adetailer_config.to_api_dict()
            if adetailer_payload:  # Only add if not None
                payload["alwayson_scripts"] = adetailer_payload

    return payload
```

**Flow:**
1. Check if `parameters.adetailer` exists
2. Verify it's an `ADetailerConfig` object
3. Call `to_api_dict()` to get payload
4. Inject into `alwayson_scripts` field

## CLI Commands

### `sdgen api adetailer-models`

**File:** `CLI/src/cli.py`

**Purpose:** List available ADetailer detection models from SD WebUI API.

**Implementation:**
```python
@api_app.command(name="adetailer-models")
def list_adetailer_models(api_url: Optional[str] = None):
    client = SDAPIClient(api_url=api_url)
    models = client.get_adetailer_models()

    # Display in Rich table with categorization
    table = Table(title=f"Available ADetailer Models ({len(models)} found)")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Model Name", style="green")
    table.add_column("Category", style="blue")

    for idx, model in enumerate(models, 1):
        category = categorize_model(model)  # face/hand/person/other
        table.add_row(str(idx), model, category)

    console.print(table)
```

**Category Logic:**
- Contains "face" → "Face"
- Contains "hand" → "Hand"
- Contains "person" → "Person"
- Contains "mediapipe" → "MediaPipe"
- Otherwise → "Other"

## Testing Strategy

### Test Coverage

**Total:** 30 tests across 3 files

#### 1. Data Models Tests (`test_adetailer_models.py`) - 12 tests

- Detector initialization (minimal, full, defaults)
- Config container (single, multiple detectors)
- API dict conversion (structure, prompts, flags, presets)

#### 2. Parser Tests (`test_adetailer_parser.py`) - 15 tests

- File parsing (single, multiple detectors, prompts)
- Validation (missing type, wrong type, no detectors, nonexistent file)
- Parameter resolution (string, list, dict, overrides, relative paths, empty/None)

#### 3. API Client Tests (`test_sdapi_client.py`) - 3 tests

- `get_adetailer_models()` endpoint
- Payload building with ADetailer config
- Payload building without ADetailer (no alwayson_scripts)

### Running Tests

```bash
# ADetailer-specific tests
cd CLI
../venv/bin/python3 -m pytest tests/api/test_sdapi_client.py::TestSDAPIClient::test_get_adetailer_models -v
../venv/bin/python3 -m pytest tests/api/test_sdapi_client.py::TestSDAPIClient::test_generate_image_with_adetailer -v
../venv/bin/python3 -m pytest tests/v2/unit/test_adetailer_models.py -v
../venv/bin/python3 -m pytest tests/v2/unit/test_adetailer_parser.py -v

# All API tests (76 total)
../venv/bin/python3 -m pytest tests/api/ -v
```

## SD WebUI API Format

### alwayson_scripts Structure

```json
{
  "alwayson_scripts": {
    "ADetailer": {
      "args": [
        // Global flags (2)
        true,   // ad_enable
        false,  // skip_img2img

        // Detector 1 (72 parameters, indices 2-73)
        "face_yolov9c.pt",      // [2] ad_model
        "",                     // [3] ad_prompt
        "",                     // [4] ad_negative_prompt
        0.3,                    // [5] ad_confidence
        1,                      // [6] ad_mask_k_largest
        0.5,                    // [7] ad_denoising_strength
        4,                      // [8] ad_mask_blur
        4,                      // [9] ad_dilate_erode
        0,                      // [10] ad_x_offset
        0,                      // [11] ad_y_offset
        "none",                 // [12] ad_mask_merge_invert
        true,                   // [13] ad_inpaint_only_masked
        32,                     // [14] ad_inpaint_only_masked_padding
        false,                  // [15] ad_use_inpaint_width_height
        512,                    // [16] ad_inpaint_width
        512,                    // [17] ad_inpaint_height
        true,                   // [18] ad_use_steps
        40,                     // [19] ad_steps
        false,                  // [20] ad_use_cfg_scale
        7.0,                    // [21] ad_cfg_scale
        false,                  // [22] ad_use_checkpoint
        "",                     // [23] ad_checkpoint
        false,                  // [24] ad_use_vae
        "",                     // [25] ad_vae
        false,                  // [26] ad_use_sampler
        "",                     // [27] ad_sampler
        false,                  // [28] ad_use_noise_multiplier
        1.0,                    // [29] ad_noise_multiplier
        false,                  // [30] ad_use_clip_skip
        1,                      // [31] ad_clip_skip
        false,                  // [32] ad_restore_face
        "none",                 // [33] ad_controlnet_model
        "none",                 // [34] ad_controlnet_module
        1.0,                    // [35] ad_controlnet_weight
        0.0,                    // [36] ad_controlnet_guidance_start
        1.0,                    // [37] ad_controlnet_guidance_end
        // ... (indices 38-73 reserved)

        // Detector 2 (72 parameters, indices 74-145)
        "hand_yolov8n.pt",      // [74] ad_model
        // ... (75-145)
      ]
    }
  }
}
```

**Key Points:**
- Flat args array (not nested objects)
- Fixed positions for each parameter
- Maximum 2 detectors per request
- Missing parameters filled with defaults

## Implementation Commits

1. **5e99de3** - Move ADetailer spec to WIP
2. **cfa2bd4** - Add core data models and file parsing
3. **7389901** - Add parameters.adetailer parsing with file loading
4. **64287e0** - Add alwayson_scripts injection in API client
5. **[current]** - Add CLI command, presets, tests, documentation

## Future Enhancements

1. **@reference Syntax Support**
   ```yaml
   imports:
     face: variations/adetailer/faces/face_hq.adetailer.yaml

   parameters:
     adetailer: @face  # Cleaner than direct path
   ```

2. **Preset Library Expansion**
   - More face presets (anime, realistic, painterly)
   - Body/person detection presets
   - Multi-detector combo presets

3. **Validation Layer**
   - Check model names against available models
   - Warn about invalid parameter ranges
   - Suggest alternatives for deprecated models

4. **Template Introspection**
   - Detect ADetailer usage in templates
   - Show effective ADetailer config in dry-run
   - Export merged detector configs to JSON

## References

- **SD WebUI ADetailer Extension:** https://github.com/Bing-su/adetailer
- **API Endpoint Docs:** `/docs` endpoint in SD WebUI (http://127.0.0.1:7860/docs)
- **Detection Models:** YOLOv8/v9 from Ultralytics
