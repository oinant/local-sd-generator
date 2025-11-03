# Theme Template Example

Copy-paste template for creating new themes quickly.

---

## Basic Theme Template

```yaml
type: theme_config
version: "2.0"
name: mytheme
description: "Brief description of theme aesthetic"

imports:
  # ============================================================
  # COMMON IMPORTS (Required - copy from parent template)
  # ============================================================
  # These are shared across ALL themes and must be redefined

  # Camera angles
  CameraAngle: ../_commons/camera_angles.yaml

  # Rendering quality tags
  Rendering: ../_commons/rendering.yaml

  # Content rating (style-aware)
  ContentRating: ../_commons/content_rating.yaml
  ContentRating.revealing: ../_commons/content_rating.revealing.yaml
  ContentRating.teasing: ../_commons/content_rating.teasing.yaml
  ContentRating.sexy: ../_commons/content_rating.sexy.yaml
  ContentRating.xxx: ../_commons/content_rating.xxx.yaml

  # Eye colors (if used)
  EyeColor: ../_commons/eyecolors.yaml
  EyeColor2: ../_commons/eyecolors.yaml

  # Body features (if used)
  Tits: ../_commons/tits.yaml
  Tits2: ../_commons/tits.yaml

  # ============================================================
  # THEMATIC IMPORTS (Customize these for your theme)
  # ============================================================

  # Character appearance
  FemaleCharacter: mytheme/mytheme-girl.yaml
  Hair: mytheme/mytheme-hair.yaml
  HairColor: mytheme/mytheme-haircolor.yaml

  # Locations and ambiance
  Locations: mytheme/mytheme-locations.yaml
  Ambiance: mytheme/mytheme-ambiance.yaml

  # Female solo outfits (style-aware)
  Outfit: mytheme/mytheme-outfit.yaml
  Outfit.revealing: mytheme/mytheme-outfit-revealing.yaml
  Outfit.teasing: mytheme/mytheme-outfit-teasing.yaml
  Outfit.sexy: mytheme/mytheme-outfit-sexy.yaml
  Outfit.xxx: mytheme/mytheme-outfit-xxx.yaml

  # Underwear (style-aware)
  Underwear: ../_commons/underwear.empty.yaml  # Or use [Remove]
  Underwear.teasing: mytheme/mytheme-underwear-teasing.yaml
  Underwear.sexy: mytheme/mytheme-underwear-sexy.yaml
  Underwear.xxx: mytheme/mytheme-underwear-xxx.yaml

  # Female solo gestures (style-aware)
  Gestures: mytheme/mytheme-gesture-sober.yaml
  Gestures.revealing: mytheme/mytheme-gesture-revealing.yaml
  Gestures.teasing: mytheme/mytheme-gesture-teasing.yaml
  Gestures.sexy: mytheme/mytheme-gesture-sexy.yaml
  Gestures.xxx: mytheme/mytheme-gesture-xxx.yaml

  # Male solo gestures (style-aware)
  BoyGestures: mytheme/mytheme-boy-gesture-sober.yaml
  BoyGestures.revealing: mytheme/mytheme-boy-gesture-revealing.yaml
  BoyGestures.teasing: mytheme/mytheme-boy-gesture-teasing.yaml
  BoyGestures.sexy: mytheme/mytheme-boy-gesture-sexy.yaml
  BoyGestures.xxx: mytheme/mytheme-boy-gesture-xxx.yaml

  # Female clothing for couple/trio scenes (style-aware)
  Clothing: mytheme/mytheme-clothing-sober.yaml
  Clothing.revealing: mytheme/mytheme-clothing-revealing.yaml
  Clothing.teasing: mytheme/mytheme-clothing-teasing.yaml
  Clothing.sexy: mytheme/mytheme-clothing-sexy.yaml
  Clothing.xxx: mytheme/mytheme-clothing-xxx.yaml

  # Male clothing for couple/trio scenes (style-aware)
  MaleBoy: mytheme/mytheme-boy-clothing-sober.yaml
  MaleBoy.revealing: mytheme/mytheme-boy-clothing-revealing.yaml
  MaleBoy.teasing: mytheme/mytheme-boy-clothing-teasing.yaml
  MaleBoy.sexy: mytheme/mytheme-boy-clothing-sexy.yaml
  MaleBoy.xxx: mytheme/mytheme-boy-clothing-xxx.yaml

  # Second character (for trio/lesbian scenes)
  FemaleCharacter2: mytheme/mytheme-girl.yaml
  HairCut2: mytheme/mytheme-hair.yaml
  HairColor2: mytheme/mytheme-haircolor.yaml

  Clothing2: mytheme/mytheme-clothing-sober.yaml
  Clothing2.revealing: mytheme/mytheme-clothing-revealing.yaml
  Clothing2.teasing: mytheme/mytheme-clothing-teasing.yaml
  Clothing2.sexy: mytheme/mytheme-clothing-sexy.yaml
  Clothing2.xxx: mytheme/mytheme-clothing-xxx.yaml

  MaleBoy2: mytheme/mytheme-boy-clothing-sober.yaml
  MaleBoy2.revealing: mytheme/mytheme-boy-clothing-revealing.yaml
  MaleBoy2.teasing: mytheme/mytheme-boy-clothing-teasing.yaml
  MaleBoy2.sexy: mytheme/mytheme-boy-clothing-sexy.yaml
  MaleBoy2.xxx: mytheme/mytheme-boy-clothing-xxx.yaml

  # Couple interactions - MF (heterosexual) (style-aware)
  CoupleAction: mytheme/mytheme-couple-mf-sober.yaml
  CoupleAction.revealing: mytheme/mytheme-couple-mf-revealing.yaml
  CoupleAction.teasing: mytheme/mytheme-couple-mf-teasing.yaml
  CoupleAction.sexy: mytheme/mytheme-couple-mf-sexy.yaml
  CoupleAction.xxx: mytheme/mytheme-couple-mf-xxx.yaml

  # Couple interactions - FF (lesbian) (style-aware)
  CoupleActionFF: mytheme/mytheme-couple-ff-sober.yaml
  CoupleActionFF.revealing: mytheme/mytheme-couple-ff-revealing.yaml
  CoupleActionFF.teasing: mytheme/mytheme-couple-ff-teasing.yaml
  CoupleActionFF.sexy: mytheme/mytheme-couple-ff-sexy.yaml
  CoupleActionFF.xxx: mytheme/mytheme-couple-ff-xxx.yaml

  # Couple interactions - MM (gay) (style-aware)
  CoupleActionMM: mytheme/mytheme-couple-mm-sober.yaml
  CoupleActionMM.revealing: mytheme/mytheme-couple-mm-revealing.yaml
  CoupleActionMM.teasing: mytheme/mytheme-couple-mm-teasing.yaml
  CoupleActionMM.sexy: mytheme/mytheme-couple-mm-sexy.yaml
  CoupleActionMM.xxx: mytheme/mytheme-couple-mm-xxx.yaml

  # Trio interactions - FFM (2 girls + 1 boy) (style-aware)
  TrioActionFFM: mytheme/mytheme-trio-ffm-sober.yaml
  TrioActionFFM.revealing: mytheme/mytheme-trio-ffm-revealing.yaml
  TrioActionFFM.teasing: mytheme/mytheme-trio-ffm-teasing.yaml
  TrioActionFFM.sexy: mytheme/mytheme-trio-ffm-sexy.yaml
  TrioActionFFM.xxx: mytheme/mytheme-trio-ffm-xxx.yaml

  # Trio interactions - MMF (2 boys + 1 girl) (style-aware)
  TrioActionMMF: mytheme/mytheme-trio-mmf-sober.yaml
  TrioActionMMF.revealing: mytheme/mytheme-trio-mmf-revealing.yaml
  TrioActionMMF.teasing: mytheme/mytheme-trio-mmf-teasing.yaml
  TrioActionMMF.sexy: mytheme/mytheme-trio-mmf-sexy.yaml
  TrioActionMMF.xxx: mytheme/mytheme-trio-mmf-xxx.yaml

# Optional: List which variations change with this theme (for manifest)
variations:
  - FemaleCharacter
  - Hair
  - HairColor
  - Locations
  - Ambiance
  - Outfit
  - Underwear
  - Gestures
  - BoyGestures
  - Clothing
  - MaleBoy
  - CoupleAction
  - CoupleActionFF
  - CoupleActionMM
  - TrioActionFFM
  - TrioActionMMF
  - FemaleCharacter2
  - HairCut2
  - HairColor2
  - Clothing2
  - MaleBoy2
```

---

## Minimal Theme Template (Only Essential Imports)

For simpler prompts that don't use couple/trio features:

```yaml
type: theme_config
version: "2.0"
name: mytheme
description: "Brief description"

imports:
  # Common (required)
  CameraAngle: ../_commons/camera_angles.yaml
  Rendering: ../_commons/rendering.yaml
  ContentRating: ../_commons/content_rating.yaml
  ContentRating.xxx: ../_commons/content_rating.xxx.yaml

  # Thematic
  FemaleCharacter: mytheme/mytheme-girl.yaml
  Hair: mytheme/mytheme-hair.yaml
  HairColor: mytheme/mytheme-haircolor.yaml
  Locations: mytheme/mytheme-locations.yaml
  Ambiance: mytheme/mytheme-ambiance.yaml

  # Outfit (style-aware)
  Outfit: mytheme/mytheme-outfit.yaml
  Outfit.teasing: mytheme/mytheme-outfit-teasing.yaml
  Outfit.sexy: mytheme/mytheme-outfit-sexy.yaml
  Outfit.xxx: mytheme/mytheme-outfit-xxx.yaml

  # Gestures (style-aware)
  Gestures: mytheme/mytheme-gesture-sober.yaml
  Gestures.teasing: mytheme/mytheme-gesture-teasing.yaml
  Gestures.sexy: mytheme/mytheme-gesture-sexy.yaml
  Gestures.xxx: mytheme/mytheme-gesture-xxx.yaml

variations:
  - FemaleCharacter
  - Hair
  - HairColor
  - Outfit
  - Locations
  - Gestures
  - Ambiance
```

---

## Variation File Template

```yaml
type: variations
version: "2.0"
name: "MyTheme Hair Styles"
description: "Hair styles for mytheme aesthetic"

variations:
  # Format: key→value or key: value
  # key = unique identifier, value = prompt text

  style1: "hair style 1 description"
  style2: "hair style 2 description"
  style3: "hair style 3 description"

  # With detailed prompts
  beachy_waves→"beachy waves, windswept hair, sun-bleached highlights, natural texture"
  tropical_braid→"tropical flower braid, hibiscus in hair, intricate braiding"
  sunset_ponytail→"high ponytail, golden hour lighting, flowing hair"
```

---

## Directory Structure

```
prompts/hassaku-teasing/
├── _commons/                           # Shared imports
│   ├── camera_angles.yaml
│   ├── rendering.yaml
│   └── content_rating.yaml
│
└── mytheme/                            # Your theme directory
    ├── theme.yaml                      # Theme definition (use template above)
    ├── README.md                       # Document your theme
    │
    ├── mytheme-girl.yaml               # Character definition
    ├── mytheme-hair.yaml               # Hair styles
    ├── mytheme-haircolor.yaml          # Hair colors
    ├── mytheme-locations.yaml          # Locations
    ├── mytheme-ambiance.yaml           # Ambiance/mood
    │
    ├── mytheme-outfit.yaml             # Base outfit (sober)
    ├── mytheme-outfit-revealing.yaml   # Revealing style
    ├── mytheme-outfit-teasing.yaml     # Teasing style
    ├── mytheme-outfit-sexy.yaml        # Sexy style
    ├── mytheme-outfit-xxx.yaml         # Explicit style
    │
    ├── mytheme-gesture-sober.yaml      # Solo gestures (sober)
    ├── mytheme-gesture-teasing.yaml    # Solo gestures (teasing)
    ├── mytheme-gesture-sexy.yaml       # Solo gestures (sexy)
    ├── mytheme-gesture-xxx.yaml        # Solo gestures (explicit)
    │
    ├── mytheme-couple-mf-sober.yaml    # Couple actions (sober)
    ├── mytheme-couple-mf-xxx.yaml      # Couple actions (explicit)
    │
    └── previews/                       # Optional preview images
        ├── preview-001.png
        └── preview-002.png
```

---

## README.md Template

```markdown
# MyTheme

**Aesthetic**: Brief description of the theme's visual style

**Inspiration**: What inspired this theme (movies, art, culture, etc.)

## Supported Prompts

- ✅ v4-solo.prompt.yaml
- ✅ v4-couple.prompt.yaml
- ✅ v4-boys.prompt.yaml
- ❌ v4-trio.prompt.yaml (not yet implemented)

## Style Variants

| Style | Description |
|-------|-------------|
| **default** | Base aesthetic (sober/romantic) |
| **revealing** | More skin showing, suggestive |
| **teasing** | Flirty, intimate |
| **sexy** | Explicit but not pornographic |
| **xxx** | Fully explicit NSFW |

## Variations Included

- **Hair**: 15 styles (beach waves, braids, ponytails, etc.)
- **Outfit**: 20 variations per style level
- **Locations**: 12 iconic locations
- **Ambiance**: 8 mood settings
- **Gestures**: 25 poses per style level

## Preview

![Preview 1](previews/preview-001.png)
![Preview 2](previews/preview-002.png)

## Usage

```bash
# Generate with this theme
sdgen generate -t v4-solo.prompt.yaml --theme mytheme -n 50

# With style variation
sdgen generate -t v4-solo.prompt.yaml --theme mytheme --style sexy -n 50
```

## Credits

- Created by: [Your Name]
- Inspired by: [Sources]
- Date: 2025-01-03
```

---

## Quick Start Steps

```bash
# 1. Create theme directory
mkdir -p prompts/hassaku-teasing/mytheme

# 2. Copy theme template
cat > prompts/hassaku-teasing/mytheme/theme.yaml
# Paste template from above, customize imports

# 3. Create variation files (minimum required)
touch prompts/hassaku-teasing/mytheme/{mytheme-hair,mytheme-outfit,mytheme-locations}.yaml

# 4. Fill variation files with your content
# ... (edit each .yaml file)

# 5. Test
sdgen generate -t v4-solo.prompt.yaml --theme mytheme -n 1

# 6. Fix any "Unresolved placeholders" errors
# Add missing imports to theme.yaml

# 7. Document
cat > prompts/hassaku-teasing/mytheme/README.md
# Paste README template, customize

# 8. Generate previews
sdgen generate -t v4-solo.prompt.yaml --theme mytheme -n 10
# Pick best images for previews/
```

---

## Related Documentation

- [Themes Usage Guide](./themes-guide.md) - Complete guide
- [Themes Troubleshooting](./themes-troubleshooting.md) - Common errors
- [Themes Architecture](../technical/themes-architecture.md) - Technical details
