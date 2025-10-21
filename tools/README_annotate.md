# Image Annotation Tool

Post-processing tool to automatically add text annotations to generated images showing the variations used (haircut, haircolor, expression, etc.).

## Installation

```bash
pip install Pillow
```

## Usage

### Basic usage (annotate all variations)

```bash
python3 tools/annotate_images.py apioutput/2025-01-20_143025_CharacterSheet
```

**Result:** Creates `*_annotated.png` files with variation info in the bottom-left corner.

### Annotate specific variations only

```bash
python3 tools/annotate_images.py apioutput/2025-01-20_143025_CharacterSheet \
    --keys HairCut,HairColor,Expression
```

### Custom position

```bash
# Top-right corner
python3 tools/annotate_images.py apioutput/session_dir --position top-right

# Bottom-right corner
python3 tools/annotate_images.py apioutput/session_dir --position bottom-right
```

### Custom styling

```bash
python3 tools/annotate_images.py apioutput/session_dir \
    --font-size 20 \
    --background-alpha 200 \
    --position bottom-right
```

### Overwrite originals (no backup)

```bash
python3 tools/annotate_images.py apioutput/session_dir --overwrite
```

**⚠️ Warning:** This will modify your original images!

## Examples

### Character sheet with haircut/haircolor labels

```bash
python3 tools/annotate_images.py \
    apioutput/2025-01-20_CharacterSheet \
    --keys HairCut,HairColor \
    --position bottom-left \
    --font-size 18
```

**Output:**
```
┌─────────────────────────────────────────┐
│                                         │
│                                         │
│                                         │
│                                         │
│                                         │
│  ┌──────────────────┐                   │
│  │ HairCut: BobCut  │                   │
│  │ HairColor: Blonde│                   │
│  └──────────────────┘                   │
└─────────────────────────────────────────┘
```

### Expression study with minimal text

```bash
python3 tools/annotate_images.py \
    apioutput/2025-01-20_ExpressionStudy \
    --keys Expression \
    --position top-right \
    --font-size 14
```

## Integration with CLI (Future)

In the future, this could be integrated directly in the template YAML:

```yaml
version: '2.0'
name: 'Character Sheet'

output:
  session_name: CharacterSheet_Annotated
  annotations:
    enabled: true
    position: bottom-left
    keys:
      - HairCut
      - HairColor
    style:
      font_size: 16
      background_alpha: 180
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--keys` | All | Comma-separated list of variation keys to display |
| `--position` | `bottom-left` | Position: `top-left`, `top-right`, `bottom-left`, `bottom-right` |
| `--font-size` | `16` | Font size in pixels |
| `--background-alpha` | `180` | Background transparency (0-255, 0=transparent, 255=opaque) |
| `--overwrite` | `false` | Overwrite original images instead of creating copies |

## How it works

1. Reads `manifest.json` from session directory
2. For each image, extracts `applied_variations` data
3. Uses Pillow (PIL) to draw text overlay on image
4. Saves annotated image with `_annotated` suffix (or overwrites if `--overwrite`)

## Session structure

The tool expects a session directory with this structure:

```
apioutput/2025-01-20_143025_CharacterSheet/
├── manifest.json          # Contains variation metadata
├── image_0001.png
├── image_0002.png
└── ...
```

## Tips

- Use `--keys` to show only relevant variations (e.g., just HairCut and HairColor for a hairstyle study)
- Use `--position bottom-right` if you have important details in the bottom-left
- Increase `--font-size` for high-resolution images
- Lower `--background-alpha` for more subtle annotations
- Run without `--overwrite` first to preview results
