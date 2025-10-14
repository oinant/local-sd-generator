# ADetailer Integration

**Status:** next
**Priority:** 6
**Component:** cli
**Created:** 2025-10-12

## Description

Integrate Adetailer (After Detailer) extension support into the CLI to enable automatic face/hand/body refinement during image generation. Adetailer is a SD WebUI extension that detects specific regions (faces, hands, etc.) using YOLO models and applies a secondary inpainting pass with customizable prompts and parameters.

## Problem Statement

Currently, the CLI sends basic txt2img payloads without support for WebUI extensions. Users who want to use Adetailer must:
- ❌ Generate images through CLI
- ❌ Manually re-process them through WebUI with Adetailer
- ❌ Track which images were processed manually
- ❌ Cannot batch-process hundreds of generated images efficiently

This breaks the "hands-free batch generation" workflow that the CLI is designed for.

## Use Cases

### 1. **Automatic Face Refinement** (Primary Use Case)
**Problem:** Generated faces often have minor artifacts (blurry eyes, uneven skin, etc.)
**Solution:** Adetailer detects faces and applies high-quality inpainting pass automatically

**Example:**
```yaml
adetailer:
  enabled: true
  ad_model: "face_yolov8n.pt"
  ad_confidence: 0.3
  ad_prompt: "detailed eyes, perfect skin, high quality face"
```

**Benefit:** 100 portraits → 100 refined faces, zero manual intervention

### 2. **Hand Correction**
**Problem:** SD models notoriously struggle with hands (extra fingers, distortion)
**Solution:** Dedicated hand detection model + inpainting pass

**Example:**
```yaml
adetailer:
  enabled: true
  ad_model: "hand_yolov8n.pt"
  ad_prompt: "anatomically correct hand, 5 fingers, natural pose"
```

### 3. **Multi-Region Refinement**
**Problem:** Complex scenes need multiple refinements (face + hands + body)
**Solution:** Adetailer supports multiple detector passes in sequence

**Example:**
```yaml
adetailer:
  enabled: true
  detectors:
    - model: "face_yolov8n.pt"
      prompt: "perfect face, detailed eyes"
    - model: "hand_yolov8n.pt"
      prompt: "correct anatomy, 5 fingers"
```

### 4. **Character-Specific Refinement**
**Problem:** LoRA characters need consistent features maintained during refinement
**Solution:** Inject character-specific prompts in Adetailer pass

**Example:**
```yaml
prompt: |
  emma_watson, <lora:emma:0.8>, casual outfit

adetailer:
  enabled: true
  ad_prompt: "emma_watson, <lora:emma:0.8>, detailed face"  # Maintains character consistency
```

## API Research & Analysis

### Adetailer API Structure

Adetailer integrates via the `alwayson_scripts` section of SD WebUI API requests. This is the standard extension mechanism for WebUI scripts that run automatically.

**Official API Documentation:**
https://github.com/Bing-su/adetailer/wiki/REST-API

**Key Insights:**
1. ✅ No separate endpoint needed (uses existing `/sdapi/v1/txt2img`)
2. ✅ Fully backward compatible (ignored if extension not installed)
3. ✅ Supports multiple detection passes (array of detector configs)
4. ⚠️ Complex configuration (~30 parameters per detector)
5. ⚠️ Minimal vs full config formats available

### API Payload Structure

#### Minimal Configuration (Recommended Starting Point)
```json
{
  "prompt": "beautiful woman, detailed",
  "sampler_name": "DPM++ 2M Karras",
  "alwayson_scripts": {
    "ADetailer": {
      "args": [
        {
          "ad_model": "face_yolov8n.pt"
        }
      ]
    }
  }
}
```

#### Full Configuration (All Parameters)
```json
{
  "prompt": "...",
  "alwayson_scripts": {
    "ADetailer": {
      "args": [
        true,   // ad_enable (can be omitted if args is object)
        false,  // skip_img2img
        {
          // Detection
          "ad_model": "face_yolov8n.pt",
          "ad_model_classes": "",
          "ad_tab_enable": true,
          "ad_confidence": 0.3,
          "ad_mask_k_largest": 0,
          "ad_mask_min_ratio": 0.0,
          "ad_mask_max_ratio": 1.0,

          // Mask Processing
          "ad_dilate_erode": 4,
          "ad_x_offset": 0,
          "ad_y_offset": 0,
          "ad_mask_merge_invert": "None",

          // Inpainting
          "ad_mask_blur": 4,
          "ad_denoising_strength": 0.4,
          "ad_inpaint_only_masked": true,
          "ad_inpaint_only_masked_padding": 32,

          // Prompts
          "ad_prompt": "detailed face, perfect skin",
          "ad_negative_prompt": "blurry, distorted",

          // Generation Override
          "ad_use_steps": false,
          "ad_steps": 28,
          "ad_use_cfg_scale": false,
          "ad_cfg_scale": 7.0,
          "ad_use_checkpoint": false,
          "ad_checkpoint": "Use same checkpoint",
          "ad_use_vae": false,
          "ad_vae": "Use same VAE",
          "ad_use_sampler": false,
          "ad_sampler": "DPM++ 2M Karras",
          "ad_use_noise_multiplier": false,
          "ad_noise_multiplier": 1.0,
          "ad_use_clip_skip": false,
          "ad_clip_skip": 1,

          // Advanced
          "ad_restore_face": false,
          "ad_controlnet_model": "None",
          "ad_controlnet_weight": 1.0,
          "ad_controlnet_guidance_start": 0.0,
          "ad_controlnet_guidance_end": 1.0
        }
      ]
    }
  }
}
```

### Multi-Detector Configuration
```json
{
  "alwayson_scripts": {
    "ADetailer": {
      "args": [
        {
          "ad_model": "face_yolov8n.pt",
          "ad_prompt": "beautiful face, detailed eyes"
        },
        {
          "ad_model": "hand_yolov8n.pt",
          "ad_prompt": "anatomically correct hand"
        }
      ]
    }
  }
}
```

**Note:** Multiple detectors = multiple objects in `args` array

## Implementation Approaches

### Option A: Full Parameter Support (Comprehensive)

**How it works:**
- Expose all 30+ Adetailer parameters in YAML config
- Map every parameter to dataclass fields
- Generate complete API payloads

**Pros:**
- ✅ Maximum flexibility for power users
- ✅ Future-proof (no need to add params later)
- ✅ 1:1 mapping with Adetailer API

**Cons:**
- ❌ Complex YAML configuration (overwhelming for beginners)
- ❌ Large dataclass definition (~30 fields)
- ❌ Harder to maintain (API changes require updates)
- ❌ Most parameters rarely used (90% use defaults)

**Verdict:** Overkill for MVP. Better as future enhancement.

---

### Option B: Essential Parameters Only (Pragmatic) ✅ RECOMMENDED

**How it works:**
- Support ~10 most commonly used parameters
- Use sensible defaults for everything else
- Allow gradual expansion based on user feedback

**Pros:**
- ✅ Simple and approachable YAML config
- ✅ Covers 90% of real-world use cases
- ✅ Easier to document and test
- ✅ Faster implementation
- ✅ Can expand later without breaking changes

**Cons:**
- ⚠️ Power users may need to wait for advanced features
- ⚠️ Some edge cases not supported initially

**Essential Parameters (Phase 1):**
```python
@dataclass
class ADetailerDetector:
    ad_model: str = "face_yolov8n.pt"
    ad_confidence: float = 0.3
    ad_prompt: str = ""
    ad_negative_prompt: str = ""
    ad_denoising_strength: float = 0.4
    ad_dilate_erode: int = 4
    ad_mask_blur: int = 4
    ad_inpaint_only_masked: bool = True
    ad_inpaint_only_masked_padding: int = 32
    ad_x_offset: int = 0
    ad_y_offset: int = 0

@dataclass
class ADetailerConfig:
    enabled: bool = False
    detectors: List[ADetailerDetector] = field(default_factory=list)
```

**Verdict:** Best balance of simplicity and utility. ✅

---

### Option C: Preset-Based Configuration (Template-Driven)

**How it works:**
- Define common presets: "face_refine", "hand_fix", "full_body"
- Users select preset by name, override specific params if needed

**Example:**
```yaml
adetailer:
  enabled: true
  preset: "face_refine"  # Uses pre-configured defaults
  overrides:
    ad_denoising_strength: 0.5
```

**Pros:**
- ✅ Ultra-simple for beginners
- ✅ Encodes best practices
- ✅ Easy to add new presets

**Cons:**
- ❌ Requires maintaining preset library
- ❌ Less transparent (users don't see full config)
- ❌ Overhead of preset resolution logic

**Verdict:** Great idea for future enhancement, but adds complexity to MVP.

---

### Option D: Modular File-Based Configuration ✅✅ STRONGLY RECOMMENDED

**How it works:**
- Store Adetailer configs in dedicated `.adetailer.yaml` files (like `.chunk.yaml`)
- Import via `parameters:` section (consistent with V2.0 architecture)
- Support single/multi imports, overrides, and semantic naming
- Leverage existing `ImportResolver` infrastructure

**Example Files:**
```yaml
# /variations/adetailer/face_hq.adetailer.yaml
version: '2.0'
name: 'High Quality Face Refinement'
description: 'Optimal settings for portrait face refinement'

detector:
  ad_model: "face_yolov8n.pt"
  ad_confidence: 0.3
  ad_prompt: "detailed eyes, perfect skin, high quality face"
  ad_denoising_strength: 0.4
  ad_dilate_erode: 4
```

**Example Usage:**
```yaml
# Simple import
parameters:
  adetailer: "../variations/adetailer/face_hq.adetailer.yaml"

# Multi-detector
parameters:
  adetailer:
    - "../variations/adetailer/face_hq.adetailer.yaml"
    - "../variations/adetailer/hand_fix.adetailer.yaml"

# With override
parameters:
  adetailer:
    import: "../variations/adetailer/face_hq.adetailer.yaml"
    override:
      ad_prompt: "emma_watson, <lora:emma:0.8>, detailed face"
```

**Pros:**
- ✅✅ **Perfect consistency with V2.0 architecture** (same pattern as chunks/variations)
- ✅ **DRY principle:** 50 prompts share ONE config file
- ✅ **Semantic naming:** `@face_hq` instead of repeating 11 parameters
- ✅ **Built-in documentation:** `name`, `description` fields in config
- ✅ **Versioning:** Multiple variants (`face_hq_v1`, `face_anime`, etc.)
- ✅ **Organized structure:** `/variations/adetailer/faces/`, `/hands/`, etc.
- ✅ **Reuses existing infrastructure:** `ImportResolver`, `YamlLoader`
- ✅ **Easy testing:** Test configs independently of prompts
- ✅ **Community sharing:** Exchange `.adetailer.yaml` presets

**Cons:**
- ⚠️ Slightly more initial setup (need to parse new file type)
- ⚠️ Users need to understand import system (already learned for V2.0)

**Verdict:** **BEST OPTION.** Most architecturally consistent with V2.0. Scales better than inline configs. ✅✅

---

## Recommended Solution: Option D (Modular Files) + Option B (Essential Params)

**Architecture:**
- Store configs in `.adetailer.yaml` files (Option D)
- Support 11 essential parameters per detector (Option B)
- Import via `parameters:` section (V2.0 pattern)
- Support inline configs for quick experiments (fallback to Option B)

**Why this combo?**
1. **Modular files** = DRY, maintainable, shareable
2. **Essential params only** = Simple, focused, easy to document
3. **Inline fallback** = Quick testing without creating files
4. **V2.0 consistency** = Users already know this pattern

### Phased Approach

**Phase 1 (MVP):**
- `.adetailer.yaml` file format with essential parameters
- Parser for `.adetailer.yaml` files
- Import via `parameters:` (string, array, dict with override)
- Fallback inline config support (for quick tests)
- Basic preset library (face_hq, hand_fix)

**Phase 2:**
- Expanded preset library (10+ configs)
- Multi-detector combinations
- Community preset repository

**Phase 3:**
- Advanced parameters (generation overrides, ControlNet)
- Nested overrides (override specific detector in multi-config)

**Phase 4:**
- Analytics (track which presets work best)
- Auto-recommendation based on prompt type

---

## Technical Design

### 1. File Format: `.adetailer.yaml`

New dedicated file type for Adetailer configurations (similar to `.chunk.yaml`).

**File structure:**
```yaml
version: '2.0'
name: 'High Quality Face Refinement'
description: 'Optimal settings for close-up portraits with detailed eyes and skin'

detector:
  # Detection
  ad_model: "face_yolov8n.pt"
  ad_confidence: 0.3

  # Prompts (optional - uses main prompt if empty)
  ad_prompt: "detailed eyes, perfect skin, high quality face"
  ad_negative_prompt: "blurry face, distorted, low quality"

  # Inpainting
  ad_denoising_strength: 0.4
  ad_inpaint_only_masked: true
  ad_inpaint_only_masked_padding: 32

  # Mask Processing
  ad_dilate_erode: 4
  ad_mask_blur: 4
  ad_x_offset: 0
  ad_y_offset: 0
```

**Required fields:**
- `version`: Must be `'2.0'`
- `detector`: Dict with detector parameters

**Optional fields:**
- `name`: Human-readable name (for documentation)
- `description`: Explains when to use this config

**Location:**
```
/variations/adetailer/
├── faces/
│   ├── face_hq.adetailer.yaml
│   ├── face_anime.adetailer.yaml
│   └── face_soft.adetailer.yaml
├── hands/
│   ├── hand_fix.adetailer.yaml
│   └── hand_aggressive.adetailer.yaml
└── combined/
    └── portrait_full.adetailer.yaml
```

---

### 2. Data Models (`CLI/src/templating/models/config_models.py`)

Add new classes for Adetailer configuration:

```python
@dataclass
class ADetailerFileConfig:
    """
    Configuration parsed from a .adetailer.yaml file.

    This represents a reusable Adetailer preset that can be
    imported into prompts via parameters: section.
    """
    version: str
    name: str
    detector: 'ADetailerDetector'
    source_file: Path
    description: str = ''


@dataclass
class ADetailerDetector:
    """
    Configuration for a single ADetailer detector pass.

    Each detector runs independently and can target different regions
    (e.g., face, hands, body) with different models and prompts.
    """
    # Detection
    ad_model: str = "face_yolov8n.pt"
    ad_confidence: float = 0.3

    # Prompts (optional - uses main prompt if empty)
    ad_prompt: str = ""
    ad_negative_prompt: str = ""

    # Inpainting
    ad_denoising_strength: float = 0.4
    ad_inpaint_only_masked: bool = True
    ad_inpaint_only_masked_padding: int = 32

    # Mask Processing
    ad_dilate_erode: int = 4
    ad_mask_blur: int = 4
    ad_x_offset: int = 0
    ad_y_offset: int = 0

    def to_api_dict(self) -> dict:
        """Convert to Adetailer API format"""
        return {
            "ad_model": self.ad_model,
            "ad_confidence": self.ad_confidence,
            "ad_prompt": self.ad_prompt,
            "ad_negative_prompt": self.ad_negative_prompt,
            "ad_denoising_strength": self.ad_denoising_strength,
            "ad_inpaint_only_masked": self.ad_inpaint_only_masked,
            "ad_inpaint_only_masked_padding": self.ad_inpaint_only_masked_padding,
            "ad_dilate_erode": self.ad_dilate_erode,
            "ad_mask_blur": self.ad_mask_blur,
            "ad_x_offset": self.ad_x_offset,
            "ad_y_offset": self.ad_y_offset,
        }


@dataclass
class ADetailerConfig:
    """
    Top-level ADetailer configuration.

    Supports multiple detectors for multi-region refinement
    (e.g., face + hands in single generation).
    """
    enabled: bool = False
    detectors: List[ADetailerDetector] = field(default_factory=list)

    def to_api_dict(self) -> Optional[dict]:
        """
        Convert to alwayson_scripts format for SD WebUI API.

        Returns None if disabled or no detectors configured.
        """
        if not self.enabled or not self.detectors:
            return None

        return {
            "ADetailer": {
                "args": [detector.to_api_dict() for detector in self.detectors]
            }
        }
```

**Extend GenerationConfig:**

```python
@dataclass
class GenerationConfig:
    """Configuration for image generation settings"""
    mode: str
    seed: int
    seed_mode: str
    max_images: int
    adetailer: Optional[ADetailerConfig] = None  # ← NEW
```

**Why not extend SDAPIClient.GenerationConfig?**
- Adetailer is prompt-level config, not global generation config
- Different prompts may want different Adetailer settings
- Keeps separation of concerns (SDAPIClient = pure HTTP, PromptConfig = templating logic)

---

### 3. YAML Usage in Prompts (`*.prompt.yaml`)

#### Method 1: Simple Import (Recommended)
```yaml
version: '2.0'
name: 'Portrait with Face Refinement'
implements: 'base.template.yaml'

prompt: |
  beautiful woman, detailed portrait, {Expression}

# Import Adetailer config via parameters
parameters:
  adetailer: "../variations/adetailer/faces/face_hq.adetailer.yaml"

generation:
  mode: random
  seed: 42
  seed_mode: progressive
  max_images: 100
```

**Benefits:**
- ✅ DRY: Config reused across multiple prompts
- ✅ Semantic: Clear what config does
- ✅ Maintainable: Update one file, all prompts updated

---

#### Method 2: Multi-Detector Import
```yaml
# Face + hands refinement
parameters:
  adetailer:
    - "../variations/adetailer/faces/face_hq.adetailer.yaml"
    - "../variations/adetailer/hands/hand_fix.adetailer.yaml"

generation:
  mode: combinatorial
  seed: 123
  seed_mode: fixed
  max_images: 50
```

**Use case:** Full-body portraits needing multiple refinements

---

#### Method 3: Import with Override
```yaml
# Character-specific face refinement
parameters:
  adetailer:
    import: "../variations/adetailer/faces/face_hq.adetailer.yaml"
    override:
      ad_prompt: "emma_watson, <lora:emma:0.8>, detailed face, perfect skin"
      ad_denoising_strength: 0.35  # Lighter for LoRA preservation
```

**Use case:** Base config + character-specific tweaks

---

#### Method 4: Via imports: (Most Modular)
```yaml
imports:
  FaceRefine: "../variations/adetailer/faces/face_hq.adetailer.yaml"
  HandFix: "../variations/adetailer/hands/hand_fix.adetailer.yaml"

parameters:
  adetailer: ["@FaceRefine", "@HandFix"]
```

**Benefits:**
- ✅ Named references
- ✅ Can override individually
- ✅ Most flexible

---

#### Method 5: Inline Config (Fallback for Quick Tests)
```yaml
# Quick test without creating file
generation:
  mode: random
  seed: 42
  seed_mode: fixed
  max_images: 10

  adetailer:
    enabled: true
    detectors:
      - ad_model: "face_yolov8n.pt"
        ad_confidence: 0.3
        ad_prompt: "test prompt"
```

**Use case:** Rapid experimentation before creating reusable config

---

### 4. File Parsing (`CLI/src/templating/loaders/config_parser.py`)

Add parser for `.adetailer.yaml` files:

```python
def parse_adetailer_file(data: dict, source_file: Path) -> ADetailerFileConfig:
    """
    Parse a .adetailer.yaml file into ADetailerFileConfig.

    Args:
        data: Parsed YAML dict
        source_file: Path to .adetailer.yaml file

    Returns:
        ADetailerFileConfig with detector settings

    Raises:
        ValueError: If version invalid or required fields missing
    """
    # Validate version
    if 'version' not in data:
        raise ValueError(f"Missing 'version' field in {source_file}")
    if data['version'] != '2.0':
        raise ValueError(f"Invalid version '{data['version']}' in {source_file} (expected '2.0')")

    # Validate required fields
    if 'detector' not in data:
        raise ValueError(f"Missing 'detector' section in {source_file}")

    # Parse detector config
    detector_data = data['detector']
    detector = ADetailerDetector(
        ad_model=detector_data.get('ad_model', 'face_yolov8n.pt'),
        ad_confidence=detector_data.get('ad_confidence', 0.3),
        ad_prompt=detector_data.get('ad_prompt', ''),
        ad_negative_prompt=detector_data.get('ad_negative_prompt', ''),
        ad_denoising_strength=detector_data.get('ad_denoising_strength', 0.4),
        ad_inpaint_only_masked=detector_data.get('ad_inpaint_only_masked', True),
        ad_inpaint_only_masked_padding=detector_data.get('ad_inpaint_only_masked_padding', 32),
        ad_dilate_erode=detector_data.get('ad_dilate_erode', 4),
        ad_mask_blur=detector_data.get('ad_mask_blur', 4),
        ad_x_offset=detector_data.get('ad_x_offset', 0),
        ad_y_offset=detector_data.get('ad_y_offset', 0),
    )

    return ADetailerFileConfig(
        version=data['version'],
        name=data.get('name', source_file.stem),
        detector=detector,
        source_file=source_file,
        description=data.get('description', '')
    )
```

---

### 5. Import Resolution (`CLI/src/templating/resolvers/import_resolver.py`)

Extend `_load_variation_file()` to support `.adetailer.yaml`:

```python
def _load_variation_file(self, path: str, base_path: Path):
    """Load variations from a single file (EXTENDED for Adetailer)"""
    resolved_path = self.loader.resolve_path(path, base_path)
    data = self.loader.load_file(resolved_path, base_path)

    # Check file type
    if resolved_path.name.endswith('.chunk.yaml'):
        return self._parse_chunk(data, resolved_path)

    # ← NEW: Support .adetailer.yaml
    elif resolved_path.name.endswith('.adetailer.yaml'):
        adetailer_config = self.parser.parse_adetailer_file(data, resolved_path)
        # Return detector directly (will be used in parameters parsing)
        return adetailer_config.detector

    else:
        # Regular variation file
        return self.parser.parse_variations(data)
```

---

### 6. Parameters Parsing (`CLI/src/templating/loaders/prompt_loader.py`)

Parse `parameters.adetailer` section:

```python
def _parse_parameters(yaml_data: dict, resolved_imports: dict, base_path: Path) -> dict:
    """
    Parse parameters section (EXTENDED for Adetailer).

    Args:
        yaml_data: Full YAML data
        resolved_imports: Dict of resolved imports from imports: section
        base_path: Base path for resolving relative file paths

    Returns:
        Dict of parsed parameters including adetailer config
    """
    params = yaml_data.get('parameters', {})

    # ← NEW: Handle adetailer parameter
    if 'adetailer' in params:
        adetailer_value = params['adetailer']

        if isinstance(adetailer_value, str):
            # Single import: path or @reference
            if adetailer_value.startswith('@'):
                # Reference to imports: section
                import_name = adetailer_value[1:]
                if import_name not in resolved_imports:
                    raise ValueError(f"Unknown import reference: {adetailer_value}")
                detector = resolved_imports[import_name]
                params['adetailer'] = ADetailerConfig(enabled=True, detectors=[detector])
            else:
                # Direct file path - load it
                detector = _load_adetailer_file(adetailer_value, base_path)
                params['adetailer'] = ADetailerConfig(enabled=True, detectors=[detector])

        elif isinstance(adetailer_value, list):
            # Multi-detector: array of paths or @references
            detectors = []
            for item in adetailer_value:
                if isinstance(item, str):
                    if item.startswith('@'):
                        import_name = item[1:]
                        detectors.append(resolved_imports[import_name])
                    else:
                        detectors.append(_load_adetailer_file(item, base_path))
            params['adetailer'] = ADetailerConfig(enabled=True, detectors=detectors)

        elif isinstance(adetailer_value, dict):
            # Override syntax: {import: ..., override: {...}}
            if 'import' in adetailer_value:
                import_path = adetailer_value['import']
                base_detector = _load_adetailer_file(import_path, base_path)

                # Apply overrides
                if 'override' in adetailer_value:
                    overrides = adetailer_value['override']
                    for key, value in overrides.items():
                        if hasattr(base_detector, key):
                            setattr(base_detector, key, value)

                params['adetailer'] = ADetailerConfig(enabled=True, detectors=[base_detector])

    return params


def _load_adetailer_file(path: str, base_path: Path) -> ADetailerDetector:
    """
    Load a .adetailer.yaml file and return detector config.

    Helper function for parameters parsing.
    """
    # Resolve path relative to base_path
    resolved_path = (base_path / path).resolve()

    if not resolved_path.exists():
        raise FileNotFoundError(f"Adetailer file not found: {resolved_path}")

    # Load and parse
    with open(resolved_path, 'r') as f:
        data = yaml.safe_load(f)

    config = parse_adetailer_file(data, resolved_path)
    return config.detector
```

---

### 7. Inline Config Fallback (`CLI/src/templating/loaders/prompt_loader.py`)

Support inline configs in `generation:` for quick tests:

```python
def _parse_adetailer_config(gen_data: dict) -> Optional[ADetailerConfig]:
    """
    Parse adetailer configuration from generation section.

    Args:
        gen_data: generation: section from YAML

    Returns:
        ADetailerConfig if enabled, None otherwise
    """
    if 'adetailer' not in gen_data:
        return None

    ad_data = gen_data['adetailer']

    # Check if enabled
    if not ad_data.get('enabled', False):
        return ADetailerConfig(enabled=False)

    # Parse detectors
    detectors = []
    for detector_data in ad_data.get('detectors', []):
        detector = ADetailerDetector(
            ad_model=detector_data.get('ad_model', 'face_yolov8n.pt'),
            ad_confidence=detector_data.get('ad_confidence', 0.3),
            ad_prompt=detector_data.get('ad_prompt', ''),
            ad_negative_prompt=detector_data.get('ad_negative_prompt', ''),
            ad_denoising_strength=detector_data.get('ad_denoising_strength', 0.4),
            ad_inpaint_only_masked=detector_data.get('ad_inpaint_only_masked', True),
            ad_inpaint_only_masked_padding=detector_data.get('ad_inpaint_only_masked_padding', 32),
            ad_dilate_erode=detector_data.get('ad_dilate_erode', 4),
            ad_mask_blur=detector_data.get('ad_mask_blur', 4),
            ad_x_offset=detector_data.get('ad_x_offset', 0),
            ad_y_offset=detector_data.get('ad_y_offset', 0),
        )
        detectors.append(detector)

    return ADetailerConfig(enabled=True, detectors=detectors)


def _parse_generation_config(yaml_data: dict) -> GenerationConfig:
    """Parse generation configuration (UPDATED)"""
    gen = yaml_data.get('generation', {})

    # Parse adetailer config
    adetailer_config = _parse_adetailer_config(gen)

    return GenerationConfig(
        mode=gen['mode'],
        seed=gen['seed'],
        seed_mode=gen['seed_mode'],
        max_images=gen['max_images'],
        adetailer=adetailer_config  # ← NEW
    )
```

---

### 4. API Payload Generation (`CLI/src/api/sdapi_client.py`)

Update `_build_payload()` to inject `alwayson_scripts`:

```python
def _build_payload(self, prompt_config: PromptConfig) -> dict:
    """
    Build API payload from prompt config (UPDATED)

    Args:
        prompt_config: Prompt configuration (now includes adetailer)

    Returns:
        dict: API payload ready to send
    """
    # Normalize prompts
    prompt = self._normalize_prompt(prompt_config.prompt)
    negative_prompt = self._normalize_prompt(prompt_config.negative_prompt)

    # Base payload
    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "seed": prompt_config.seed if prompt_config.seed is not None else -1,
        "steps": self.generation_config.steps,
        "cfg_scale": self.generation_config.cfg_scale,
        "width": self.generation_config.width,
        "height": self.generation_config.height,
        "sampler_name": self.generation_config.sampler_name,
        "batch_size": self.generation_config.batch_size,
        "n_iter": self.generation_config.n_iter
    }

    # Add scheduler if specified
    if self.generation_config.scheduler is not None:
        payload["scheduler"] = self.generation_config.scheduler

    # Add Hires Fix if enabled
    if self.generation_config.enable_hr:
        payload["enable_hr"] = True
        payload["hr_scale"] = self.generation_config.hr_scale
        # ... (existing Hires Fix logic)

    # ========== NEW: Add Adetailer if configured ==========
    if hasattr(prompt_config, 'adetailer') and prompt_config.adetailer:
        adetailer_dict = prompt_config.adetailer.to_api_dict()
        if adetailer_dict:
            payload["alwayson_scripts"] = adetailer_dict

    return payload
```

**Key Design Decision:**
- `alwayson_scripts` is **additive** (doesn't overwrite other scripts)
- If user has other scripts configured in WebUI, they coexist
- Only adds `ADetailer` key to `alwayson_scripts` dict

---

### 5. API Introspection (`CLI/src/api/sdapi_client.py`)

Add method to list available Adetailer models:

```python
def get_adetailer_models(self, timeout: int = 5) -> list[str]:
    """
    Get list of available ADetailer detection models.

    Requires Adetailer extension installed in SD WebUI.

    Returns:
        List of model names (e.g., ["face_yolov8n.pt", "hand_yolov8n.pt"])

    Example:
        [
            "face_yolov8n.pt",
            "face_yolov8s.pt",
            "hand_yolov8n.pt",
            "person_yolov8n-seg.pt",
            "mediapipe_face_full",
            "mediapipe_face_short"
        ]

    Raises:
        requests.exceptions.RequestException: If API call fails (extension not installed)
    """
    response = requests.get(
        f"{self.api_url}/adetailer/v1/ad_model",
        timeout=timeout
    )
    response.raise_for_status()
    return response.json()
```

**Note:** This endpoint is specific to Adetailer extension (not core WebUI API)

---

### 6. CLI Command (`CLI/src/cli.py`)

Add new command to list Adetailer models:

```python
@api_app.command("adetailer-models")
def api_adetailer_models():
    """List available ADetailer detection models"""
    config = GlobalConfig.load()
    client = SDAPIClient(api_url=config.api_url)

    try:
        models = client.get_adetailer_models()

        print("\nAvailable ADetailer Models:")
        print("=" * 50)

        for model in models:
            print(f"  • {model}")

        print(f"\nTotal: {len(models)} models")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print("❌ Adetailer extension not installed in SD WebUI")
            print("   Install: https://github.com/Bing-su/adetailer")
        else:
            print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
```

**Usage:**
```bash
python3 src/cli.py api adetailer-models
```

---

### 7. Validation & Error Handling

#### Validation Rules

```python
def validate_adetailer_config(config: ADetailerConfig) -> List[str]:
    """
    Validate Adetailer configuration.

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    if not config.enabled:
        return errors  # Nothing to validate if disabled

    if not config.detectors:
        errors.append("Adetailer enabled but no detectors configured")

    for i, detector in enumerate(config.detectors):
        prefix = f"Detector {i+1}"

        # Validate confidence (0.0 - 1.0)
        if not 0.0 <= detector.ad_confidence <= 1.0:
            errors.append(f"{prefix}: ad_confidence must be between 0.0 and 1.0")

        # Validate denoising strength (0.0 - 1.0)
        if not 0.0 <= detector.ad_denoising_strength <= 1.0:
            errors.append(f"{prefix}: ad_denoising_strength must be between 0.0 and 1.0")

        # Validate model name (basic check)
        if not detector.ad_model:
            errors.append(f"{prefix}: ad_model cannot be empty")

        # Validate mask parameters
        if detector.ad_dilate_erode < 0:
            errors.append(f"{prefix}: ad_dilate_erode must be >= 0")

        if detector.ad_mask_blur < 0:
            errors.append(f"{prefix}: ad_mask_blur must be >= 0")

        if detector.ad_inpaint_only_masked_padding < 0:
            errors.append(f"{prefix}: ad_inpaint_only_masked_padding must be >= 0")

    return errors
```

#### Error Handling Strategy

**During YAML parsing:**
- Invalid config → Raise validation error with helpful message
- Missing optional fields → Use defaults (graceful degradation)

**During API call:**
- Adetailer not installed → Warning + continue without Adetailer
- Invalid model name → API returns error, propagate to user
- Other errors → Standard API error handling

---

### 8. Metadata Tracking

Update metadata.json to record Adetailer usage:

```json
{
  "version": "1.0",
  "generation_info": { ... },
  "adetailer": {
    "enabled": true,
    "detectors": [
      {
        "ad_model": "face_yolov8n.pt",
        "ad_confidence": 0.3,
        "ad_prompt": "detailed face",
        "ad_denoising_strength": 0.4
      }
    ]
  },
  "prompt": { ... }
}
```

**Why track this?**
- Reproducibility (know which images used Adetailer)
- Debugging (compare Adetailer vs non-Adetailer results)
- Analysis (which settings worked best?)

---

## Tasks

### Phase 1: Core Implementation (MVP)

#### Data Models & Parsing
- [ ] **T1.1:** Add `ADetailerFileConfig` data model to `config_models.py`
- [ ] **T1.2:** Add `ADetailerDetector` and `ADetailerConfig` to `config_models.py`
- [ ] **T1.3:** Add `to_api_dict()` methods for API payload generation
- [ ] **T1.4:** Add `parse_adetailer_file()` to `config_parser.py`

#### Import & Resolution
- [ ] **T1.5:** Extend `ImportResolver._load_variation_file()` to support `.adetailer.yaml`
- [ ] **T1.6:** Add `_parse_parameters()` logic for `parameters.adetailer` imports
- [ ] **T1.7:** Support string/array/dict import formats
- [ ] **T1.8:** Implement override mechanism for imported configs

#### Inline Fallback
- [ ] **T1.9:** Add `_parse_adetailer_config()` for inline configs in `generation:`
- [ ] **T1.10:** Support both modular and inline approaches

#### API Integration
- [ ] **T1.11:** Update `_build_payload()` in `sdapi_client.py` to inject `alwayson_scripts`
- [ ] **T1.12:** Add validation function `validate_adetailer_config()`
- [ ] **T1.13:** Update metadata generator to include Adetailer info
- [ ] **T1.14:** Add `get_adetailer_models()` to `SDAPIClient`
- [ ] **T1.15:** Add `api adetailer-models` CLI command

#### Preset Library
- [ ] **T1.16:** Create `/variations/adetailer/` directory structure
- [ ] **T1.17:** Create `face_hq.adetailer.yaml` preset
- [ ] **T1.18:** Create `hand_fix.adetailer.yaml` preset
- [ ] **T1.19:** Create `face_soft.adetailer.yaml` preset
- [ ] **T1.20:** Create README for preset library

### Phase 2: Testing

#### Unit Tests - File Parsing
- [ ] **T2.1:** Test `parse_adetailer_file()` with valid config
- [ ] **T2.2:** Test `parse_adetailer_file()` with missing version
- [ ] **T2.3:** Test `parse_adetailer_file()` with invalid version
- [ ] **T2.4:** Test `parse_adetailer_file()` with missing detector section
- [ ] **T2.5:** Test `parse_adetailer_file()` with defaults

#### Unit Tests - Imports & Parameters
- [ ] **T2.6:** Test `parameters.adetailer` with string path
- [ ] **T2.7:** Test `parameters.adetailer` with array of paths
- [ ] **T2.8:** Test `parameters.adetailer` with @reference
- [ ] **T2.9:** Test `parameters.adetailer` with override dict
- [ ] **T2.10:** Test error on invalid import reference

#### Unit Tests - API Integration
- [ ] **T2.11:** Test `ADetailerConfig.to_api_dict()` single detector
- [ ] **T2.12:** Test `ADetailerConfig.to_api_dict()` multi detector
- [ ] **T2.13:** Test payload generation with Adetailer
- [ ] **T2.14:** Test validation function catches invalid configs

#### Integration Tests
- [ ] **T2.15:** Generate with imported `.adetailer.yaml` file
- [ ] **T2.16:** Generate with multi-detector import
- [ ] **T2.17:** Generate with override
- [ ] **T2.18:** Generate with inline config (fallback)
- [ ] **T2.19:** Verify metadata includes Adetailer info
- [ ] **T2.20:** Graceful handling when extension not installed

### Phase 3: Documentation

#### User Documentation
- [ ] **T3.1:** Create `/docs/cli/usage/adetailer-guide.md`
  - Introduction & prerequisites
  - File format reference (`.adetailer.yaml`)
  - Import methods (5 methods with examples)
  - Common use cases & recipes
  - Troubleshooting
  - Performance tips

- [ ] **T3.2:** Create `/variations/adetailer/README.md` (Preset Library Guide)
  - Overview of available presets
  - When to use each preset
  - How to create custom presets
  - Sharing & community presets

- [ ] **T3.3:** Add example prompts to `/examples/adetailer/`
  - `portrait_simple.prompt.yaml` - Simple face refinement
  - `portrait_character.prompt.yaml` - Character-specific with override
  - `fullbody_multi.prompt.yaml` - Multi-detector (face + hands)
  - `test_inline.prompt.yaml` - Inline config for quick test

#### Technical Documentation
- [ ] **T3.4:** Update `/docs/cli/technical/yaml-format.md`
  - Add `.adetailer.yaml` format specification
  - Add `parameters.adetailer` usage patterns
  - Import vs inline comparison table

- [ ] **T3.5:** Create `/docs/cli/technical/adetailer-implementation.md`
  - Architecture overview (file-based approach)
  - Data flow diagram
  - Import resolution process
  - API payload format
  - Testing strategy

- [ ] **T3.6:** Update main README
  - Add Adetailer to features list
  - Quick example with import
  - Link to full guide

### Phase 4: Polish & UX

- [ ] **T4.1:** Add helpful error messages for common misconfigurations
- [ ] **T4.2:** Validate model names against available models (optional warning)
- [ ] **T4.3:** Add `--dry-run` support to preview Adetailer payload
- [ ] **T4.4:** Performance metrics: track generation time impact

---

## Success Criteria

### Functional
- [ ] ✅ Single detector config in YAML generates correct API payload
- [ ] ✅ Multi-detector config generates correct API payload
- [ ] ✅ Disabled Adetailer does not add `alwayson_scripts` to payload
- [ ] ✅ Invalid configs produce clear validation errors
- [ ] ✅ `api adetailer-models` command lists available models
- [ ] ✅ Metadata.json includes Adetailer settings used

### Quality
- [ ] ✅ All unit tests pass (100% coverage of new code)
- [ ] ✅ Integration tests verify end-to-end workflow
- [ ] ✅ Backward compatible (no breaking changes to existing configs)
- [ ] ✅ Works alongside Hires Fix without conflicts
- [ ] ✅ Graceful degradation if Adetailer not installed

### Documentation
- [ ] ✅ User guide explains all parameters with examples
- [ ] ✅ Technical docs cover API format and implementation
- [ ] ✅ Example YAML files demonstrate common use cases

---

## Tests

### Unit Tests

**File:** `tests/v2/unit/test_adetailer_config.py`

```python
def test_adetailer_detector_to_api_dict():
    """Test detector converts to API format correctly"""
    detector = ADetailerDetector(
        ad_model="face_yolov8n.pt",
        ad_confidence=0.5,
        ad_prompt="beautiful face"
    )

    api_dict = detector.to_api_dict()

    assert api_dict["ad_model"] == "face_yolov8n.pt"
    assert api_dict["ad_confidence"] == 0.5
    assert api_dict["ad_prompt"] == "beautiful face"


def test_adetailer_config_disabled():
    """Test disabled config returns None"""
    config = ADetailerConfig(enabled=False)
    assert config.to_api_dict() is None


def test_adetailer_config_multi_detector():
    """Test multi-detector config generates correct payload"""
    config = ADetailerConfig(
        enabled=True,
        detectors=[
            ADetailerDetector(ad_model="face_yolov8n.pt"),
            ADetailerDetector(ad_model="hand_yolov8n.pt")
        ]
    )

    api_dict = config.to_api_dict()

    assert "ADetailer" in api_dict
    assert len(api_dict["ADetailer"]["args"]) == 2


def test_adetailer_validation():
    """Test validation catches invalid configs"""
    config = ADetailerConfig(
        enabled=True,
        detectors=[
            ADetailerDetector(ad_confidence=1.5)  # Invalid
        ]
    )

    errors = validate_adetailer_config(config)
    assert len(errors) > 0
    assert "confidence" in errors[0].lower()
```

**File:** `tests/v2/unit/test_prompt_loader_adetailer.py`

```python
def test_parse_adetailer_simple(tmp_path):
    """Test parsing simple adetailer config"""
    yaml_content = """
version: '2.0'
name: 'Test'
prompt: 'test'
generation:
  mode: random
  seed: 42
  seed_mode: fixed
  max_images: 1
  adetailer:
    enabled: true
    detectors:
      - ad_model: "face_yolov8n.pt"
        ad_confidence: 0.4
"""

    # ... parse YAML ...

    assert config.generation.adetailer.enabled is True
    assert len(config.generation.adetailer.detectors) == 1
    assert config.generation.adetailer.detectors[0].ad_model == "face_yolov8n.pt"


def test_parse_adetailer_disabled():
    """Test parsing disabled adetailer"""
    # YAML without adetailer section
    config = parse_yaml(yaml_without_adetailer)

    assert config.generation.adetailer is None


def test_parse_adetailer_multi_detector():
    """Test parsing multi-detector config"""
    # ... YAML with 2 detectors ...

    assert len(config.generation.adetailer.detectors) == 2
```

**File:** `tests/api/test_sdapi_client_adetailer.py`

```python
def test_build_payload_with_adetailer():
    """Test payload includes alwayson_scripts"""
    client = SDAPIClient()

    prompt_config = PromptConfig(
        prompt="test",
        adetailer=ADetailerConfig(
            enabled=True,
            detectors=[ADetailerDetector(ad_model="face_yolov8n.pt")]
        )
    )

    payload = client._build_payload(prompt_config)

    assert "alwayson_scripts" in payload
    assert "ADetailer" in payload["alwayson_scripts"]


def test_build_payload_without_adetailer():
    """Test payload omits alwayson_scripts when disabled"""
    client = SDAPIClient()
    prompt_config = PromptConfig(prompt="test")

    payload = client._build_payload(prompt_config)

    assert "alwayson_scripts" not in payload


@patch('requests.get')
def test_get_adetailer_models(mock_get):
    """Test fetching Adetailer models"""
    mock_get.return_value.json.return_value = [
        "face_yolov8n.pt",
        "hand_yolov8n.pt"
    ]

    client = SDAPIClient()
    models = client.get_adetailer_models()

    assert len(models) == 2
    assert "face_yolov8n.pt" in models
```

### Integration Tests

**File:** `tests/integration/test_adetailer_generation.py`

```python
@pytest.mark.integration
@pytest.mark.skipif(not is_sd_api_running(), reason="SD API not available")
def test_generate_with_adetailer():
    """
    Full integration test: Generate image with Adetailer

    Prerequisites:
    - SD WebUI running on http://127.0.0.1:7860
    - Adetailer extension installed
    """
    # Create prompt config with Adetailer
    config = PromptConfig(...)

    # Generate
    result = executor.generate_batch(config)

    # Verify
    assert result.success
    assert result.images_generated > 0

    # Check metadata
    metadata = load_metadata(result.output_path)
    assert metadata["adetailer"]["enabled"] is True


@pytest.mark.integration
def test_generate_without_adetailer_extension():
    """
    Test graceful handling when Adetailer not installed
    """
    # Attempt to use Adetailer
    # Should warn but not crash
    pass
```

---

## Performance Impact

### Generation Time

**Expected overhead per image:**
- Single detector (face only): **+30-50% generation time**
- Multi-detector (face + hands): **+60-100% generation time**

**Example:**
- Base generation: 10s/image
- With face refinement: 13-15s/image
- With face + hands: 16-20s/image

**Why?**
- Each detector pass = full inpainting generation
- Detection overhead ~1-2s per image
- Inpainting pass ≈ 50-80% of original generation time

### Memory Impact

**Minimal:** Adetailer runs sequentially (doesn't hold multiple images in memory)

### Mitigation Strategies

1. **Selective Use:** Only enable for final batch, not test runs
2. **Batch Optimization:** Process detectors in parallel (future enhancement)
3. **Model Selection:** Smaller YOLO models (yolov8n vs yolov8x) trade accuracy for speed

---

## Backward Compatibility

### YAML Files
- ✅ Existing prompts without `adetailer` section continue to work
- ✅ `adetailer` is optional field (defaults to None)
- ✅ No migration needed for old configs

### API Payloads
- ✅ `alwayson_scripts` only added when Adetailer configured
- ✅ Other scripts in WebUI unaffected
- ✅ Non-Adetailer generations identical to before

### CLI Interface
- ✅ No breaking changes to existing commands
- ✅ New `api adetailer-models` command is additive

---

## Dependencies

### Required
- ✅ SD WebUI with Adetailer extension installed
- ✅ At least one YOLO detection model downloaded

### Installation
```bash
# In SD WebUI:
# 1. Extensions > Install from URL
# 2. https://github.com/Bing-su/adetailer.git
# 3. Restart WebUI
```

### Model Download
Adetailer automatically downloads models on first use (face_yolov8n.pt, etc.)

---

## Security Considerations

### Input Validation
- ✅ All numeric parameters bounded (confidence, denoising, etc.)
- ✅ Model names sanitized (no path traversal)
- ✅ Prompt injection not possible (params are separate from prompts)

### API Safety
- ✅ Adetailer runs server-side (no local file access)
- ✅ No credential/token handling required
- ✅ Standard WebUI authentication applies

---

## Preset Library Organization

**Recommended directory structure:**

```
/variations/adetailer/
├── README.md                    # Overview of all presets, usage guide
│
├── faces/
│   ├── face_hq.adetailer.yaml         # High quality realistic faces
│   ├── face_anime.adetailer.yaml      # Optimized for anime/manga
│   ├── face_soft.adetailer.yaml       # Subtle refinement
│   ├── face_portrait.adetailer.yaml   # Portrait photography
│   └── face_aggressive.adetailer.yaml # Strong refinement
│
├── hands/
│   ├── hand_fix.adetailer.yaml        # Standard hand correction
│   ├── hand_aggressive.adetailer.yaml # Strong correction (6+ fingers)
│   └── hand_soft.adetailer.yaml       # Subtle adjustment
│
├── body/
│   ├── body_refine.adetailer.yaml     # Full body refinement
│   └── person_fullbody.adetailer.yaml # Complete person detection
│
└── combined/
    ├── portrait_full.adetailer.yaml   # Face + hands (portrait use)
    └── character_hq.adetailer.yaml    # Face + hands + body (full character)
```

**Note:** "combined" presets are actually multiple `.adetailer.yaml` files imported together in prompts:
```yaml
parameters:
  adetailer:
    - "../variations/adetailer/faces/face_hq.adetailer.yaml"
    - "../variations/adetailer/hands/hand_fix.adetailer.yaml"
```

**Naming conventions:**
- `{target}_{variant}.adetailer.yaml`
- Target: `face`, `hand`, `body`, `person`
- Variant: `hq`, `soft`, `aggressive`, `anime`, `portrait`, etc.

**Preset characteristics:**

| Preset | Model | Confidence | Denoising | Use Case |
|--------|-------|------------|-----------|----------|
| `face_hq` | face_yolov8n.pt | 0.3 | 0.4 | High-quality portraits |
| `face_soft` | face_yolov8n.pt | 0.3 | 0.25 | Subtle face touch-up |
| `face_anime` | face_yolov8n.pt | 0.35 | 0.35 | Anime/manga characters |
| `hand_fix` | hand_yolov8n.pt | 0.4 | 0.45 | Standard hand correction |
| `hand_aggressive` | hand_yolov8n.pt | 0.35 | 0.5 | Severe hand issues |
| `body_refine` | person_yolov8n-seg.pt | 0.3 | 0.35 | Full body refinement |

**Community sharing:**
- Users can create custom presets in their `/variations/adetailer/custom/` directory
- Share presets as single `.adetailer.yaml` files
- Version presets with `_v1`, `_v2` suffixes for experimentation

---

## Future Enhancements (Post-MVP)

### Phase 2: Advanced Parameters
- [ ] Generation overrides (steps, CFG, sampler per detector)
- [ ] ControlNet integration for guided refinement
- [ ] Custom mask processing (merge, invert)

### Phase 3: Preset System
- [ ] Built-in presets: "face_hq", "hand_fix", "full_character"
- [ ] User-defined preset library
- [ ] Preset inheritance (extend existing presets)

### Phase 4: Workflow Integration
- [ ] Batch post-processing mode (apply Adetailer to existing images)
- [ ] A/B testing (generate with/without Adetailer for comparison)
- [ ] Auto-detection of optimal settings based on prompt

### Phase 5: Performance Optimization
- [ ] Parallel detector execution (if API supports)
- [ ] Smart caching of detection results
- [ ] Adaptive confidence thresholds

### Phase 6: Analytics
- [ ] Track success rate (% of images where faces detected)
- [ ] Average quality improvement metrics
- [ ] Cost analysis (time/compute trade-offs)

---

## Related Features

### Existing
- **Hires Fix:** Complements Adetailer (upscale + refine workflow)
- **Metadata Export:** Already captures generation params, extends naturally
- **Batch Generation:** Adetailer integrates seamlessly

### Future
- **ControlNet Support:** Could guide Adetailer inpainting (Phase 3)
- **Multi-Stage Pipelines:** txt2img → Adetailer → upscale → refine
- **Quality Scoring:** Auto-enable Adetailer for low-quality faces

---

## Documentation Plan

### User Documentation

**File:** `/docs/cli/usage/adetailer-guide.md`

**Contents:**
1. Introduction & Prerequisites
2. Basic Configuration (single detector)
3. Multi-Detector Workflows
4. Parameter Reference Table
5. Common Use Cases & Recipes
6. Troubleshooting
7. Performance Tips

**File:** `/docs/cli/usage/examples/adetailer-examples.yaml`

Example configs demonstrating:
- Simple face refinement
- Multi-region (face + hands)
- Character consistency with LoRA
- High-quality portrait workflow

### Technical Documentation

**File:** `/docs/cli/technical/adetailer-implementation.md`

**Contents:**
1. Architecture Overview
2. Data Flow Diagram
3. API Payload Format
4. Validation Rules
5. Error Handling Strategy
6. Testing Strategy

**File:** `/docs/cli/technical/yaml-format.md` (UPDATE)

Add section:
- Adetailer YAML Schema
- Field Descriptions
- Default Values Reference

---

## Priority Justification

**Priority 6** (Important, Near-Term):

**Pros:**
- ✅ High user value (face/hand quality is #1 pain point)
- ✅ Relatively simple implementation (no complex logic)
- ✅ Natural fit with existing batch workflow
- ✅ Enables new use cases (hands-free quality refinement)

**Cons:**
- ⚠️ Requires external extension (not pure CLI feature)
- ⚠️ Performance overhead may surprise users

**Comparison to other features:**
- **Higher than P7-8:** More impactful than nice-to-haves
- **Lower than P1-3:** Not blocking core functionality
- **Similar to model metadata (P7):** Both enhance reproducibility

---

## Effort Estimate

**Medium-Large** (~10-12 hours):

| Task | Time | Notes |
|------|------|-------|
| Data models (`ADetailerFileConfig`, `ADetailerDetector`, `ADetailerConfig`) | 1.5h | 3 dataclasses + `to_api_dict()` |
| File parser (`parse_adetailer_file()`) | 1h | YAML → ADetailerFileConfig |
| Import resolution (extend `ImportResolver`) | 1.5h | Support `.adetailer.yaml` files |
| Parameters parsing (modular imports) | 2h | String/array/dict formats + overrides |
| Inline fallback parsing | 0.5h | `generation.adetailer` quick test support |
| API client payload injection | 1h | `alwayson_scripts` integration |
| Validation & error handling | 1h | Bounds checking, helpful messages |
| Unit tests (20 tests) | 2h | File parsing, imports, API integration |
| Integration tests (6 tests) | 1h | End-to-end workflows |
| Preset library (4 configs + README) | 1h | `face_hq`, `hand_fix`, `face_soft`, docs |
| Documentation (user + technical) | 2h | Guide, examples, technical specs |
| **TOTAL** | **~13.5h** | Round down to 10-12h realistic |

**Breakdown by Phase:**
- **Phase 1 (MVP):** 9h (implementation + presets)
- **Phase 2 (Testing):** 3h (20 unit + 6 integration tests)
- **Phase 3 (Documentation):** 2h (guides + examples)
- **Phase 4 (Polish):** 1h (error messages, validation)

**Confidence:** Medium-High
- ✅ **High confidence:** Parsing, imports (reuses existing infrastructure)
- ⚠️ **Medium confidence:** API payload format (minor uncertainty)
- ⚠️ **Medium confidence:** Override mechanism edge cases

**Comparison to inline-only approach:**
- Inline-only: ~6-8h (simpler, less infrastructure)
- **Modular (chosen):** ~10-12h (+30% time, but 10x better UX and maintainability)

---

## References

- **Adetailer GitHub:** https://github.com/Bing-su/adetailer
- **Adetailer API Wiki:** https://github.com/Bing-su/adetailer/wiki/REST-API
- **SD WebUI API Docs:** https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/API
- **YOLO Models:** YOLOv8 (Ultralytics) used for detection

---

## Open Questions

1. **Should we validate model names against available models?**
   - Pro: Catch typos early
   - Con: Requires API call, may slow down validation
   - **Decision:** Optional warning, not blocking error

2. **How to handle multiple `alwayson_scripts` extensions?**
   - Current design: Only manages ADetailer
   - Future: Generic `alwayson_scripts` config section?
   - **Decision:** Start specific (ADetailer only), generalize if needed

3. **Should ad_prompt inherit from main prompt if empty?**
   - Pro: DRY principle, less config duplication
   - Con: May want different prompts for refinement
   - **Decision:** Empty = use main prompt (Adetailer default behavior)

4. **Performance: Cache detection results between seeds?**
   - Same composition, different seeds → same faces?
   - Probably not worth complexity for MVP
   - **Decision:** Defer to Phase 5 optimization

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Adetailer API changes | High | Low | Pin API version in docs, add version check |
| Extension not installed | Medium | Medium | Clear error message + installation guide |
| Performance overhead unexpected | Medium | Medium | Document expected slowdown prominently |
| Parameter complexity overwhelming | Low | Medium | Start minimal (11 params), expand gradually |
| Conflicts with other extensions | Medium | Low | Test with common extensions (ControlNet, etc.) |

---

## Success Metrics

**Post-Implementation (1 month after release):**

- [ ] **Adoption:** >20% of users enable Adetailer in at least one prompt
- [ ] **Satisfaction:** No major bug reports or confusion in documentation
- [ ] **Performance:** Average generation time increase ≤ 60% (acceptable)
- [ ] **Requests:** Low demand for advanced parameters (validates MVP approach)

---

## Approval & Sign-Off

**Recommended Approach:**
1. ✅ Implement MVP (Phase 1) with essential parameters
2. ✅ Gather user feedback for 2-4 weeks
3. 🔄 Expand to advanced parameters (Phase 2) based on demand

**Next Steps:**
1. Review this spec with stakeholders
2. Approve/adjust priority & scope
3. Move to `/roadmap/wip/` when implementation starts
4. Track progress with task checklist

---

## Summary of Recommended Approach

**✅ Option D (Modular Files) is the clear winner:**

1. **Architecture Consistency:** Perfect alignment with V2.0 (same pattern as `.chunk.yaml`)
2. **DRY Principle:** 50 prompts share ONE config file instead of duplicating 11 parameters
3. **Maintainability:** Update one preset → all prompts updated instantly
4. **User Experience:** Semantic naming (`@face_hq`) instead of cryptic parameters
5. **Community Value:** Easy to share, version, and document presets
6. **Extensibility:** Natural path to preset library, overrides, and combinations

**Trade-off:** +30% implementation time (10-12h vs 6-8h) for 10x better long-term UX.

**Fallback:** Inline configs still supported for quick testing (best of both worlds).

---

_Last Updated: 2025-10-12_
_Status: Ready for Implementation_
_Approach: Modular `.adetailer.yaml` files + Essential Parameters (Option D + B)_
