# Automatic Image Annotations

Automatically add text overlays to generated images showing the variations used (haircut, haircolor, expression, etc.).

## Features

- 🚀 **Background processing** - Annotations run in background, don't slow down generation
- 🎨 **Customizable styling** - Control position, font size, colors, transparency
- 🔍 **Selective display** - Choose which variations to show
- 📝 **Auto-integration** - Just add config to your template YAML

## Quick Start

Add `output.annotations` section to your template:

```yaml
version: '2.0'
name: 'Character Sheet'

imports:
  HairCut: variations/hair_styles.yaml
  HairColor: variations/haircolors.yaml
  Expression: variations/expressions.yaml

prompt: |
  1girl, {HairCut}, {HairColor} hair, {Expression}

output:
  session_name: CharacterSheet_Annotated
  annotations:
    enabled: true
    keys:  # Which variations to display
      - HairCut
      - HairColor
    position: bottom-left
```

**Result:** Each generated image will have a text overlay showing:
```
HairCut: BobCut
HairColor: Blonde
```

## Configuration

### Required

- `enabled` (bool): Enable/disable annotations

### Optional

| Parameter | Default | Description |
|-----------|---------|-------------|
| `keys` | `[]` (all) | List of variation keys to display |
| `position` | `bottom-left` | Position: `top-left`, `top-right`, `bottom-left`, `bottom-right` |
| `font_size` | `16` | Font size in pixels |
| `background_alpha` | `180` | Background transparency (0-255, 0=transparent, 255=opaque) |
| `text_color` | `white` | Text color: `white`, `black`, `red`, `green`, `blue`, `yellow` |
| `padding` | `10` | Padding around text inside box |
| `margin` | `20` | Margin from image edges |

## Examples

### Minimal (all variations)

```yaml
output:
  annotations:
    enabled: true
```

Shows **all** variations with default styling.

### Selective display

```yaml
output:
  annotations:
    enabled: true
    keys:
      - HairCut
      - Expression
```

Shows **only** HairCut and Expression (useful for character sheets).

### Custom styling

```yaml
output:
  annotations:
    enabled: true
    position: top-right
    font_size: 20
    background_alpha: 220  # More opaque
    text_color: yellow
```

Large yellow text in top-right corner with darker background.

### Subtle annotations

```yaml
output:
  annotations:
    enabled: true
    position: bottom-right
    font_size: 14
    background_alpha: 120  # More transparent
    padding: 8
    margin: 15
```

Small, subtle annotations that don't obscure the image.

## Use Cases

### Character Sheet Generation

```yaml
output:
  annotations:
    enabled: true
    keys: [HairCut, HairColor, Outfit]
    position: bottom-left
```

Perfect for organizing character design variations.

### Expression Studies

```yaml
output:
  annotations:
    enabled: true
    keys: [Expression]
    position: top-right
    font_size: 18
```

Quick reference for facial expression studies.

### Style Exploration

```yaml
output:
  annotations:
    enabled: true
    keys: [Style, Lighting, ColorPalette]
    position: bottom-right
```

Track which style combinations work best.

## How It Works

1. **Generation completes** - Images are generated normally
2. **Background process** - Annotation script launches in background
3. **Images annotated** - Text overlays added to each image
4. **No slowdown** - You can continue working while annotations process

The annotation process:
- Reads `manifest.json` from session directory
- For each image, extracts `applied_variations`
- Uses Pillow (PIL) to draw text overlay
- Overwrites images with annotated versions

## Requirements

Annotations require **Pillow** (Python Imaging Library):

```bash
pip install Pillow
```

If Pillow is not installed, annotations will be skipped with a warning.

## Standalone Usage

You can also annotate existing sessions manually:

```bash
# Annotate all variations
python3 tools/annotate_images.py apioutput/2025-01-20_143025

# Annotate specific keys only
python3 tools/annotate_images.py apioutput/session_dir \
    --keys HairCut,HairColor
```

See `tools/README_annotate.md` for full standalone usage.

## Tips

- Use `keys` to show only relevant variations (avoid cluttering with technical params)
- Use `bottom-left` for most images (less likely to obscure important details)
- Increase `font_size` for high-resolution images
- Lower `background_alpha` for more subtle annotations
- Use `top-right` if you have important details in bottom-left

## Troubleshooting

### Annotations not appearing

**Check Pillow is installed:**
```bash
pip install Pillow
```

**Check `enabled: true` in config:**
```yaml
output:
  annotations:
    enabled: true  # ← Make sure this is true
```

### Annotations obscure image details

**Move to different corner:**
```yaml
position: top-right  # or bottom-right
```

**Make more subtle:**
```yaml
background_alpha: 100  # More transparent
font_size: 14  # Smaller text
```

### Wrong variations shown

**Specify exact keys:**
```yaml
keys:
  - HairCut
  - HairColor
  # Only these will be shown
```

## See Also

- [Template Syntax Reference](../reference/template-syntax.md)
- [Output Configuration](../reference/output-config.md)
- [Standalone Annotation Tool](../../../tools/README_annotate.md)
