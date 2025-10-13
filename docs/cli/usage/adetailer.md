# ADetailer Integration - Usage Guide

**Status:** ✅ Feature Complete
**Version:** 1.0
**Component:** CLI

## Overview

ADetailer (After Detailer) integration enables automatic enhancement of specific image regions (faces, hands, etc.) during generation. The integration supports preset files, inline configuration, and multiple detectors per image.

## Quick Start

### Basic Usage (String Path)

```yaml
# portrait.prompt.yaml
name: "Portrait with Face Enhancement"
type: prompt_template
version: "2.0"

template: |
  masterpiece, beautiful portrait, detailed

parameters:
  adetailer: variations/adetailer/faces/face_hq.adetailer.yaml
```

### Multiple Detectors (List)

```yaml
parameters:
  adetailer:
    - variations/adetailer/faces/face_hq.adetailer.yaml
    - variations/adetailer/hands/hand_fix.adetailer.yaml
```

### Override Detection Model (List with Dict)

```yaml
parameters:
  adetailer:
    - variations/adetailer/faces/face_hq.adetailer.yaml
    - ad_model: face_yolov8n.pt  # Override to faster model
```

### Inline Configuration (Dict)

```yaml
parameters:
  adetailer:
    ad_model: face_yolov9c.pt
    ad_denoising_strength: 0.5
    ad_steps: 40
    ad_mask_k_largest: 1
```

## Available Presets

The project includes 3 pre-configured presets optimized for common use cases.

### Face Enhancement

#### `variations/adetailer/faces/face_hq.adetailer.yaml`
High-quality face enhancement for portraits and final renders.

- **Model:** face_yolov9c.pt (YOLOv9c - best accuracy)
- **Denoising:** 0.5 (strong enhancement)
- **Steps:** 40 (high quality)
- **Use Case:** Hero images, professional portraits

#### `variations/adetailer/faces/face_soft.adetailer.yaml`
Subtle face enhancement that preserves original style.

- **Model:** face_yolov9c.pt
- **Denoising:** 0.25 (subtle)
- **Steps:** 40
- **Use Case:** Batch processing, style-sensitive art

### Hand Fixing

#### `variations/adetailer/hands/hand_fix.adetailer.yaml`
Fixes common hand anatomy issues.

- **Model:** hand_yolov8n.pt (fast & accurate)
- **Denoising:** 0.4 (balanced)
- **Steps:** 40
- **Processes:** Up to 2 hands per image
- **Use Case:** Character art with visible hands

## Configuration Options

### Core Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ad_model` | string | **required** | Detection model (e.g., "face_yolov9c.pt") |
| `ad_denoising_strength` | float | 0.4 | Strength of enhancement (0.0-1.0) |
| `ad_steps` | int | 28 | Inpainting steps |
| `ad_use_steps` | bool | false | Override default steps |
| `ad_mask_k_largest` | int | 1 | Number of regions to process |

### Detection Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ad_confidence` | float | 0.3 | Detection threshold (0.0-1.0) |
| `ad_mask_blur` | int | 4 | Edge softening |
| `ad_dilate_erode` | int | 4 | Mask expansion/contraction |
| `ad_x_offset` | int | 0 | Horizontal mask offset |
| `ad_y_offset` | int | 0 | Vertical mask offset |

### Prompts (Optional)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ad_prompt` | string | "" | Additional prompt for inpainting |
| `ad_negative_prompt` | string | "" | Additional negative prompt |

### Advanced Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ad_inpaint_only_masked` | bool | true | Process only detected areas (faster) |
| `ad_inpaint_only_masked_padding` | int | 32 | Context pixels around mask |
| `ad_use_cfg_scale` | bool | false | Override CFG scale |
| `ad_cfg_scale` | float | 7.0 | CFG scale for inpainting |
| `ad_restore_face` | bool | false | Use face restoration model |

## Common Workflows

### Workflow 1: Single Face Portrait

```yaml
parameters:
  width: 512
  height: 768
  steps: 30
  adetailer: variations/adetailer/faces/face_hq.adetailer.yaml
```

**Result:** High-quality face enhancement with 40 inpainting steps.

### Workflow 2: Group Portrait (Multiple Faces)

```yaml
parameters:
  adetailer:
    - variations/adetailer/faces/face_hq.adetailer.yaml
    - ad_mask_k_largest: 3  # Process 3 largest faces
```

**Result:** Enhances up to 3 faces in the image.

### Workflow 3: Full Character (Face + Hands)

```yaml
parameters:
  adetailer:
    - variations/adetailer/faces/face_hq.adetailer.yaml
    - variations/adetailer/hands/hand_fix.adetailer.yaml
```

**Result:** Processes both face and hands with separate optimized settings.

### Workflow 4: Style-Preserving Enhancement

```yaml
parameters:
  adetailer:
    - variations/adetailer/faces/face_soft.adetailer.yaml
```

**Result:** Subtle improvements that maintain original artistic style.

### Workflow 5: Custom Prompts

```yaml
parameters:
  adetailer:
    - variations/adetailer/faces/face_hq.adetailer.yaml
    - ad_prompt: "piercing blue eyes, freckles, detailed skin texture"
      ad_negative_prompt: "red eyes, glowing eyes"
```

**Result:** Face enhancement with specific feature guidance.

## CLI Commands

### List Available Detection Models

```bash
sdgen api adetailer-models
```

**Output:**
```
┌───┬────────────────────────┬───────────┐
│ # │ Model Name             │ Category  │
├───┼────────────────────────┼───────────┤
│ 1 │ face_yolov9c.pt        │ Face      │
│ 2 │ face_yolov8n.pt        │ Face      │
│ 3 │ hand_yolov8n.pt        │ Hand      │
│ 4 │ person_yolov8n-seg.pt  │ Person    │
│ 5 │ mediapipe_face_full    │ MediaPipe │
└───┴────────────────────────┴───────────┘
```

## Tips & Best Practices

### Performance Optimization

1. **Use YOLOv8n models for batch processing** (faster than YOLOv9c)
   ```yaml
   ad_model: face_yolov8n.pt  # ~2x faster than face_yolov9c.pt
   ```

2. **Lower denoising for subtle changes** (faster generation)
   ```yaml
   ad_denoising_strength: 0.25  # Minimal style change
   ```

3. **Reduce steps for quick tests**
   ```yaml
   ad_use_steps: true
   ad_steps: 20  # Faster, lower quality
   ```

### Quality Optimization

1. **Increase steps for high-quality output**
   ```yaml
   ad_use_steps: true
   ad_steps: 60  # Maximum detail
   ```

2. **Adjust denoising for stronger changes**
   ```yaml
   ad_denoising_strength: 0.6  # Strong enhancement
   ```

3. **Use custom prompts for specific features**
   ```yaml
   ad_prompt: "symmetrical face, perfect eyes, detailed iris"
   ```

### Detection Tuning

1. **Lower confidence for missed detections**
   ```yaml
   ad_confidence: 0.2  # More sensitive detection
   ```

2. **Increase mask_k_largest for group shots**
   ```yaml
   ad_mask_k_largest: 5  # Process 5 faces
   ```

3. **Expand mask for more context**
   ```yaml
   ad_inpaint_only_masked_padding: 64  # More surrounding context
   ```

## Troubleshooting

### Issue: Faces Not Detected

**Solution 1:** Lower confidence threshold
```yaml
ad_confidence: 0.2
```

**Solution 2:** Try different detection model
```yaml
ad_model: face_yolov8n.pt  # Alternative detector
```

### Issue: Style Changed Too Much

**Solution:** Lower denoising strength
```yaml
ad_denoising_strength: 0.25  # More subtle
```

### Issue: Only One Face Processed (Group Shot)

**Solution:** Increase mask_k_largest
```yaml
ad_mask_k_largest: 3  # Process 3 faces
```

### Issue: Hands Still Look Wrong

**Solution 1:** Increase denoising
```yaml
ad_denoising_strength: 0.5
```

**Solution 2:** Add custom prompt
```yaml
ad_prompt: "perfect hands, five fingers, anatomically correct"
```

## Examples

See full example templates in:
- `/CLI/src/examples/templates/adetailer_portrait.prompt.yaml`
- `/CLI/src/examples/templates/adetailer_character.prompt.yaml`

## See Also

- [ADetailer Technical Documentation](../technical/adetailer.md)
- [Parameters Documentation](../technical/parameters.md)
- [Template System V2.0](../technical/template_system_v2.md)
