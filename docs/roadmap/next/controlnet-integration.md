# ControlNet Integration

**Status:** next
**Priority:** 6
**Component:** cli
**Created:** 2025-10-21

## Description

Integrate ControlNet support into the template system following the same pattern as ADetailer: preset files, inline configuration, multiple units support, and full parameter control.

ControlNet enables guided image generation using preprocessed control images (edges, depth, pose, etc.), providing precise structural control over SD outputs.

## Motivation

- **Systematic pose/composition control** - Generate consistent character poses across variations
- **LoRA training datasets** - Create controlled variation sets with specific compositions
- **Reproducible workflows** - Version-controlled ControlNet presets
- **Multi-unit support** - Combine multiple ControlNet units (e.g., depth + pose + lineart)

## Implementation

### Architecture

Follow ADetailer pattern:

```
packages/sd-generator-cli/
├── sd_generator_cli/
│   ├── templating/
│   │   ├── models/
│   │   │   └── controlnet.py              # Data models (ControlNetUnit, ControlNetConfig)
│   │   ├── loaders/
│   │   │   └── controlnet_parser.py       # .controlnet.yaml parser
│   │   └── resolvers/
│   │       ├── import_resolver.py         # .controlnet.yaml import support
│   │       └── parameters_resolver.py     # parameters.controlnet resolution
│   ├── api/
│   │   └── sdapi_client.py                # API client with ControlNet injection
│   └── cli.py                             # CLI commands (sdgen api controlnet-models)
└── tests/
    ├── unit/
    │   ├── test_controlnet_models.py
    │   └── test_controlnet_parser.py
    └── api/
        └── test_sdapi_client.py           # ControlNet payload tests
```

### Data Models

#### ControlNetUnit

Single ControlNet unit configuration (similar to ADetailerDetector).

**File:** `sd_generator_cli/templating/models/controlnet.py`

```python
from dataclasses import dataclass, field
from typing import Optional, Any

@dataclass
class ControlNetUnit:
    """Single ControlNet unit configuration"""

    # Required
    model: str                              # e.g., "control_v11p_sd15_canny"

    # Input image (mutually exclusive with module auto-generation)
    image: Optional[str] = None             # Path to control image or base64

    # Preprocessor
    module: str = "none"                    # Preprocessor module (e.g., "canny", "depth_midas")

    # Weight and guidance
    weight: float = 1.0                     # Unit influence (0.0-2.0)
    guidance_start: float = 0.0             # When to start guidance (0.0-1.0)
    guidance_end: float = 1.0               # When to stop guidance (0.0-1.0)

    # Preprocessor parameters
    processor_res: int = 512                # Preprocessor resolution
    threshold_a: float = 64.0               # Preprocessor param A (e.g., canny low threshold)
    threshold_b: float = 128.0              # Preprocessor param B (e.g., canny high threshold)

    # Control modes
    resize_mode: str = "Crop and Resize"   # "Just Resize", "Crop and Resize", "Resize and Fill"
    control_mode: str = "Balanced"          # "Balanced", "My prompt is more important", "ControlNet is more important"

    # Advanced
    pixel_perfect: bool = False             # Auto-calculate processor_res
    lowvram: bool = False                   # Low VRAM mode
    guess_mode: bool = False                # Guess mode (ignore prompts)

    def to_api_dict(self) -> dict[str, Any]:
        """Convert to SD WebUI ControlNet API format"""
        return {
            "enabled": True,
            "module": self.module,
            "model": self.model,
            "weight": self.weight,
            "image": self.image,
            "resize_mode": self.resize_mode,
            "lowvram": self.lowvram,
            "processor_res": self.processor_res,
            "threshold_a": self.threshold_a,
            "threshold_b": self.threshold_b,
            "guidance_start": self.guidance_start,
            "guidance_end": self.guidance_end,
            "control_mode": self.control_mode,
            "pixel_perfect": self.pixel_perfect,
            "guessmode": self.guess_mode,
        }

@dataclass
class ControlNetConfig:
    """Container for ControlNet units"""

    units: list[ControlNetUnit] = field(default_factory=list)

    def to_api_dict(self) -> Optional[dict]:
        """Convert to alwayson_scripts payload format"""
        if not self.units:
            return None

        return {
            "controlnet": {
                "args": [unit.to_api_dict() for unit in self.units]
            }
        }
```

### File Format

#### .controlnet.yaml Structure

```yaml
type: controlnet_config
version: "1.0"

units:
  - model: control_v11p_sd15_canny
    module: canny
    weight: 1.0
    threshold_a: 100
    threshold_b: 200
    guidance_start: 0.0
    guidance_end: 0.5

  - model: control_v11p_sd15_depth
    module: depth_midas
    weight: 0.8
    guidance_start: 0.0
    guidance_end: 1.0
```

**Validation Rules:**
1. `type` must be `"controlnet_config"`
2. `version` must be `"1.0"`
3. `units` must be non-empty array
4. Each unit must have `model` field
5. If `image` is provided, it must be valid path or base64
6. `weight` must be 0.0-2.0
7. `guidance_start`/`guidance_end` must be 0.0-1.0

### Parameter Resolution

Support 3 formats like ADetailer:

#### Format 1: String (Path)

```yaml
parameters:
  controlnet: variations/controlnet/canny/edges_strong.controlnet.yaml
```

#### Format 2: List (Multiple Units + Overrides)

```yaml
parameters:
  controlnet:
    - variations/controlnet/canny/edges.controlnet.yaml
    - variations/controlnet/depth/depth_soft.controlnet.yaml
    - weight: 0.7  # Override first unit weight
```

#### Format 3: Dict (Inline Configuration)

```yaml
parameters:
  controlnet:
    model: control_v11p_sd15_canny
    module: canny
    image: /path/to/control_image.png
    weight: 1.0
    threshold_a: 100
    threshold_b: 200
```

### Preset Library

Create common presets in `variations/controlnet/`:

#### variations/controlnet/canny/edges_strong.controlnet.yaml
```yaml
type: controlnet_config
version: "1.0"

units:
  - model: control_v11p_sd15_canny
    module: canny
    weight: 1.0
    threshold_a: 100      # Strong edges
    threshold_b: 200
    guidance_start: 0.0
    guidance_end: 0.5     # Early guidance
    control_mode: "ControlNet is more important"
```

#### variations/controlnet/depth/depth_soft.controlnet.yaml
```yaml
type: controlnet_config
version: "1.0"

units:
  - model: control_v11p_sd15_depth
    module: depth_midas
    weight: 0.6           # Subtle influence
    guidance_start: 0.0
    guidance_end: 1.0
    control_mode: "Balanced"
```

#### variations/controlnet/pose/openpose_character.controlnet.yaml
```yaml
type: controlnet_config
version: "1.0"

units:
  - model: control_v11p_sd15_openpose
    module: openpose_full
    weight: 1.0
    guidance_start: 0.0
    guidance_end: 0.8
    control_mode: "ControlNet is more important"
```

#### variations/controlnet/multi/depth_canny_combo.controlnet.yaml
```yaml
type: controlnet_config
version: "1.0"

units:
  - model: control_v11p_sd15_depth
    module: depth_midas
    weight: 0.6
    guidance_start: 0.0
    guidance_end: 1.0

  - model: control_v11p_sd15_canny
    module: canny
    weight: 0.8
    threshold_a: 50
    threshold_b: 150
    guidance_start: 0.0
    guidance_end: 0.5
```

### API Client Integration

**File:** `sd_generator_cli/api/sdapi_client.py`

#### New Method: `get_controlnet_models()`

```python
def get_controlnet_models(self) -> dict[str, list[str]]:
    """
    Get available ControlNet models and modules.

    Returns:
        {
            "models": ["control_v11p_sd15_canny", ...],
            "modules": ["canny", "depth_midas", "openpose_full", ...]
        }
    """
    response = self.session.get(f"{self.api_url}/controlnet/model_list")
    models = response.json()["model_list"]

    response = self.session.get(f"{self.api_url}/controlnet/module_list")
    modules = response.json()["module_list"]

    return {
        "models": models,
        "modules": modules
    }
```

#### Update: `_build_payload()`

```python
def _build_payload(self, prompt_config: PromptConfig) -> dict:
    payload = {
        "prompt": ...,
        # ... base fields
    }

    # Initialize alwayson_scripts dict
    alwayson_scripts = {}

    # Add ADetailer if configured
    if prompt_config.parameters and 'adetailer' in prompt_config.parameters:
        adetailer_config = prompt_config.parameters['adetailer']
        if hasattr(adetailer_config, 'to_api_dict'):
            adetailer_payload = adetailer_config.to_api_dict()
            if adetailer_payload:
                alwayson_scripts.update(adetailer_payload)

    # Add ControlNet if configured
    if prompt_config.parameters and 'controlnet' in prompt_config.parameters:
        controlnet_config = prompt_config.parameters['controlnet']
        if hasattr(controlnet_config, 'to_api_dict'):
            controlnet_payload = controlnet_config.to_api_dict()
            if controlnet_payload:
                alwayson_scripts.update(controlnet_payload)

    # Only add alwayson_scripts if not empty
    if alwayson_scripts:
        payload["alwayson_scripts"] = alwayson_scripts

    return payload
```

### CLI Commands

#### `sdgen api controlnet-models`

```python
@api_app.command(name="controlnet-models")
def list_controlnet_models(api_url: Optional[str] = None):
    """List available ControlNet models and preprocessor modules"""
    client = SDAPIClient(api_url=api_url)
    data = client.get_controlnet_models()

    # Models table
    models_table = Table(title=f"ControlNet Models ({len(data['models'])} found)")
    models_table.add_column("#", style="cyan", width=4)
    models_table.add_column("Model Name", style="green")
    models_table.add_column("Type", style="blue")

    for idx, model in enumerate(data["models"], 1):
        model_type = categorize_controlnet_model(model)
        models_table.add_row(str(idx), model, model_type)

    console.print(models_table)
    console.print()

    # Modules table
    modules_table = Table(title=f"Preprocessor Modules ({len(data['modules'])} found)")
    modules_table.add_column("#", style="cyan", width=4)
    modules_table.add_column("Module Name", style="green")
    modules_table.add_column("Category", style="blue")

    for idx, module in enumerate(data["modules"], 1):
        category = categorize_controlnet_module(module)
        modules_table.add_row(str(idx), module, category)

    console.print(modules_table)

def categorize_controlnet_model(model_name: str) -> str:
    """Categorize ControlNet model by name"""
    model_lower = model_name.lower()
    if "canny" in model_lower:
        return "Canny (Edges)"
    elif "depth" in model_lower:
        return "Depth"
    elif "openpose" in model_lower or "pose" in model_lower:
        return "Pose"
    elif "lineart" in model_lower:
        return "Line Art"
    elif "scribble" in model_lower:
        return "Scribble"
    elif "seg" in model_lower:
        return "Segmentation"
    elif "normal" in model_lower:
        return "Normal Map"
    elif "mlsd" in model_lower:
        return "MLSD (Lines)"
    else:
        return "Other"

def categorize_controlnet_module(module_name: str) -> str:
    """Categorize preprocessor module"""
    module_lower = module_name.lower()
    if "canny" in module_lower:
        return "Edge Detection"
    elif "depth" in module_lower:
        return "Depth Estimation"
    elif "openpose" in module_lower or "pose" in module_lower:
        return "Pose Detection"
    elif "lineart" in module_lower:
        return "Line Art Extraction"
    elif "normal" in module_lower:
        return "Normal Map"
    elif "seg" in module_lower:
        return "Segmentation"
    else:
        return "Other"
```

### Example Usage

#### Example 1: Single ControlNet (Canny Edges)

```yaml
name: "Canny Edge Controlled Portrait"
version: 2

payload:
  model: "your-model.safetensors"
  steps: 30
  cfg_scale: 7.5
  width: 512
  height: 768

  prompt:
    template: "masterpiece, beautiful portrait, detailed face"

  negative_prompt: "low quality, blurry"

parameters:
  controlnet: variations/controlnet/canny/edges_strong.controlnet.yaml
```

#### Example 2: Multi-Unit (Depth + Canny)

```yaml
parameters:
  controlnet:
    - variations/controlnet/depth/depth_soft.controlnet.yaml
    - variations/controlnet/canny/edges_strong.controlnet.yaml
```

#### Example 3: Inline with Control Image

```yaml
parameters:
  controlnet:
    model: control_v11p_sd15_openpose
    module: openpose_full
    image: /path/to/pose_reference.png
    weight: 1.0
    guidance_start: 0.0
    guidance_end: 0.8
```

#### Example 4: Combined with ADetailer

```yaml
parameters:
  # ControlNet for composition control
  controlnet: variations/controlnet/pose/openpose_character.controlnet.yaml

  # ADetailer for face enhancement after generation
  adetailer: variations/adetailer/faces/face_hq.adetailer.yaml
```

## Tasks

- [ ] Create `ControlNetUnit` and `ControlNetConfig` data models
- [ ] Implement `.controlnet.yaml` file parser
- [ ] Add `parameters.controlnet` resolution in `parameters_resolver.py`
- [ ] Extend import resolver to support `.controlnet.yaml` files
- [ ] Update `sdapi_client._build_payload()` to inject ControlNet
- [ ] Add `get_controlnet_models()` method to API client
- [ ] Create `sdgen api controlnet-models` CLI command
- [ ] Create preset library (canny, depth, pose, multi-unit)
- [ ] Write unit tests for models (12+ tests)
- [ ] Write unit tests for parser (15+ tests)
- [ ] Write API client tests (3+ tests)
- [ ] Update documentation (`docs/cli/usage/controlnet.md`)
- [ ] Add technical documentation (`docs/cli/technical/controlnet.md`)
- [ ] Add example templates with ControlNet usage

## Success Criteria

- [ ] All 3 parameter formats work (string, list, dict)
- [ ] Multi-unit ControlNet configurations work correctly
- [ ] ControlNet + ADetailer can be used together in same template
- [ ] CLI command lists available models and modules
- [ ] Test coverage >80% for new code
- [ ] Documentation complete with examples
- [ ] Preset library covers common use cases (canny, depth, pose, multi)
- [ ] Type checking passes (mypy strict)
- [ ] All tests pass

## Tests

### Unit Tests (30+ tests expected)

**test_controlnet_models.py** (~12 tests)
- Unit initialization (minimal, full, defaults)
- Config container (single, multiple units)
- API dict conversion (structure, parameters, multi-unit)
- Weight/guidance validation

**test_controlnet_parser.py** (~15 tests)
- File parsing (single, multiple units)
- Validation (missing type, wrong type, no units, nonexistent file)
- Parameter resolution (string, list, dict, overrides, relative paths)
- Image path resolution

**test_sdapi_client.py** (~3 tests)
- `get_controlnet_models()` endpoint
- Payload building with ControlNet config
- Payload building with both ControlNet + ADetailer

### Integration Tests

- Generate image with single ControlNet unit
- Generate image with multi-unit ControlNet
- Generate image with ControlNet + ADetailer combined

## Documentation

### Usage Guide (`docs/cli/usage/controlnet.md`)

Similar structure to `adetailer.md`:
- Overview
- Quick Start (3 formats)
- Available Presets
- Configuration Options (parameters table)
- Common Workflows (5+ examples)
- CLI Commands
- Tips & Best Practices
- Troubleshooting
- Examples

### Technical Documentation (`docs/cli/technical/controlnet.md`)

Similar structure to `adetailer.md`:
- Architecture
- Data Models (ControlNetUnit, ControlNetConfig)
- File Format (.controlnet.yaml)
- Parameter Resolution
- API Client Integration
- CLI Commands
- Testing Strategy
- SD WebUI API Format (alwayson_scripts.controlnet)
- Future Enhancements

## Notes

### Differences from ADetailer

1. **Image input** - ControlNet requires control images (provided or preprocessor-generated)
2. **Multi-unit is common** - Most workflows use 2-3 units (depth + canny + pose)
3. **Preprocessor parameters** - More complex config (threshold_a/b, processor_res)
4. **Control modes** - Balance between prompt and ControlNet influence

### SD WebUI API Format

```json
{
  "alwayson_scripts": {
    "controlnet": {
      "args": [
        {
          "enabled": true,
          "module": "canny",
          "model": "control_v11p_sd15_canny",
          "weight": 1.0,
          "image": "base64_or_path",
          "resize_mode": "Crop and Resize",
          "lowvram": false,
          "processor_res": 512,
          "threshold_a": 100,
          "threshold_b": 200,
          "guidance_start": 0.0,
          "guidance_end": 0.5,
          "control_mode": "Balanced",
          "pixel_perfect": false,
          "guessmode": false
        },
        {
          // Unit 2 (optional)
        }
      ]
    }
  }
}
```

### Compatible with ADetailer

Both can coexist in same payload:

```json
{
  "alwayson_scripts": {
    "controlnet": { ... },
    "ADetailer": { ... }
  }
}
```

## References

- **SD WebUI ControlNet Extension:** https://github.com/Mikubill/sd-webui-controlnet
- **ControlNet Models:** https://huggingface.co/lllyasviel/ControlNet-v1-1
- **API Endpoint:** `/controlnet/model_list`, `/controlnet/module_list`
- **ADetailer Implementation:** `docs/cli/technical/adetailer.md` (reference pattern)

## Future Enhancements

1. **@reference Syntax** - Import ControlNet presets with `@reference`
2. **Image Variations** - Support `{ControlImage}` placeholder in variations
3. **Batch Control Images** - Different control image per generated image
4. **Preprocessor Preview** - CLI command to preview preprocessor output
5. **Preset Combos** - Pre-configured multi-unit combinations
6. **Weight Scheduling** - Animate weight over generation steps
