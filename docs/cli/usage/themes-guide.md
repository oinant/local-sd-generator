# Themes Usage Guide

**Audience**: Theme creators and prompt authors
**Difficulty**: Intermediate
**Prerequisites**: Understanding of Template System V2.0 basics

---

## What is a Theme?

A **theme** is a collection of variation files that provide a **cohesive aesthetic** for your prompts. Themes replace all thematic imports (hair, outfits, locations, etc.) while maintaining the prompt's structure.

**Examples**:
- 🌴 **Tropical**: Beach paradise, sun-kissed aesthetics
- 🤖 **Cyberpunk**: Neon lights, tech aesthetics
- 🏰 **Medieval**: Castles, knights, fantasy
- 🌊 **Underwater**: Ocean depths, mermaids

---

## Using Themes

### Basic Usage

```bash
# Generate with a theme
sdgen generate -t prompt.yaml --theme cyberpunk

# With style variation
sdgen generate -t prompt.yaml --theme cyberpunk --style sexy

# List available themes
sdgen themes list
```

### Theme Discovery

The system automatically discovers themes in directories configured with:

```yaml
# template.yaml
themes:
  enable_autodiscovery: true
  search_paths:
    - ./themes/
    - ./prompts/hassaku-teasing/  # Custom search path
```

**Directory structure**:
```
prompts/hassaku-teasing/
├── template.yaml
├── tropical/
│   ├── theme.yaml          # ← Discovered as "tropical" theme
│   ├── tropical-hair.yaml
│   └── ...
└── cyberpunk/
    ├── theme.yaml          # ← Discovered as "cyberpunk" theme
    ├── cyber-hair.yaml
    └── ...
```

---

## Creating a Theme

### Step 1: Understand Template Requirements

**Before creating a theme, analyze the template and prompts** to understand which placeholders are used.

```bash
# Example: Check what placeholders v4-boys.prompt.yaml uses
grep -E '\{[A-Z][a-zA-Z0-9]*\}' prompts/hassaku-teasing/v4-boys.prompt.yaml
```

**Output**:
```yaml
{ContentRating}    # Style-sensitive
{Rendering}        # Common import
{Ambiance}         # Thematic
{MaleBoy}          # Thematic + style-sensitive
{MaleBoy2}         # Thematic + style-sensitive
{CoupleActionMM}   # Thematic + style-sensitive
{CameraAngle}      # Common import
{Locations}        # Thematic
```

### Step 2: Identify Common vs Thematic Imports

**Common imports**: Needed by ALL themes (camera angles, rendering quality, content rating)
- Must be redefined in EVERY theme
- Usually reference `_commons/` shared files

**Thematic imports**: Specific to the theme (hair, outfits, locations, gestures)
- Define the theme's unique aesthetic
- Different for each theme

**Example from parent template**:
```yaml
# _tpl_base_themable.template.yaml
imports:
  # COMMON (must be in theme)
  CameraAngle: ./_commons/camera_angles.yaml
  Rendering: ./_commons/rendering.yaml
  ContentRating: ./_commons/content_rating.yaml

  # THEMATIC (theme replaces these)
  Hair: ../variations/default/hair.yaml
  Outfit: ../variations/default/outfit.yaml
```

### Step 3: Create Theme Directory

```bash
mkdir -p prompts/hassaku-teasing/mytheme
cd prompts/hassaku-teasing/mytheme
```

### Step 4: Create theme.yaml

```yaml
type: theme_config
version: "2.0"
name: mytheme
description: "My awesome theme description"

imports:
  # ============================================================
  # COMMON IMPORTS (copy from parent template)
  # ============================================================
  CameraAngle: ../_commons/camera_angles.yaml
  Rendering:   ../_commons/rendering.yaml

  # Content Rating (style-aware)
  ContentRating: ../_commons/content_rating.yaml
  ContentRating.revealing: ../_commons/content_rating.revealing.yaml
  ContentRating.teasing: ../_commons/content_rating.teasing.yaml
  ContentRating.sexy: ../_commons/content_rating.sexy.yaml
  ContentRating.xxx: ../_commons/content_rating.xxx.yaml

  # ============================================================
  # THEMATIC IMPORTS (mytheme-specific)
  # ============================================================
  FemaleCharacter: mytheme/mytheme-girl.yaml
  Hair: mytheme/mytheme-hair.yaml
  HairColor: mytheme/mytheme-haircolor.yaml
  Locations: mytheme/mytheme-locations.yaml
  Ambiance: mytheme/mytheme-ambiance.yaml

  # Style-aware thematic imports
  Outfit: mytheme/mytheme-outfit.yaml
  Outfit.teasing: mytheme/mytheme-outfit-teasing.yaml
  Outfit.sexy: mytheme/mytheme-outfit-sexy.yaml
  Outfit.xxx: mytheme/mytheme-outfit-xxx.yaml

  # Male clothing (for couple/trio scenes)
  MaleBoy: mytheme/mytheme-boy-clothing.yaml
  MaleBoy.teasing: mytheme/mytheme-boy-clothing-teasing.yaml
  MaleBoy.sexy: mytheme/mytheme-boy-clothing-sexy.yaml
  MaleBoy.xxx: mytheme/mytheme-boy-clothing-xxx.yaml

# Optional: Declare which variations change with theme
variations:
  - FemaleCharacter
  - Hair
  - HairColor
  - Outfit
  - Locations
  - Ambiance
  - MaleBoy
```

### Step 5: Create Variation Files

```bash
# mytheme/mytheme-hair.yaml
type: variations
version: "2.0"
name: "MyTheme Hair Styles"

variations:
  beachy_waves: "beachy waves, windswept hair, sun-bleached highlights"
  tropical_braid: "tropical flower braid, hibiscus in hair"
  sunset_ponytail: "high ponytail, golden hour lighting"
```

### Step 6: Test the Theme

```bash
# Test with different styles
sdgen generate -t v4-boys.prompt.yaml --theme mytheme -n 1
sdgen generate -t v4-boys.prompt.yaml --theme mytheme --style teasing -n 1
sdgen generate -t v4-boys.prompt.yaml --theme mytheme --style xxx -n 1

# Check for unresolved placeholders
# If error "Unresolved placeholders: X, Y, Z"
# → Add missing imports to theme.yaml
```

---

## Style-Aware Themes

### What are Style-Sensitive Placeholders?

Some placeholders have **different variations depending on the style** (sober, teasing, sexy, xxx):

```yaml
# template.yaml
style_sensitive_placeholders:
  - Outfit      # Changes with style
  - Gestures    # Changes with style
  - MaleBoy     # Changes with style
```

### Providing Style Variants

```yaml
# theme.yaml
imports:
  # Base (default style)
  Outfit: mytheme/outfit.yaml

  # Style variants (more revealing as style progresses)
  Outfit.teasing: mytheme/outfit-teasing.yaml
  Outfit.sexy: mytheme/outfit-sexy.yaml
  Outfit.xxx: mytheme/outfit-xxx.yaml
```

**Resolution with** `--style xxx`:
- System looks for `Outfit.xxx` variant
- If found → uses it
- If not found → falls back to base `Outfit`

### [Remove] Directive for Styles

You can **remove a placeholder for a specific style**:

```yaml
imports:
  Underwear: mytheme/underwear.yaml          # Has underwear by default
  Underwear.xxx: [Remove]                     # No underwear for xxx style
```

**Effect**: When using `--style xxx`, `{Underwear}` resolves to empty string.

---

## Common Patterns

### Pattern 1: Minimal Theme (Reference Commons)

For themes that only need to customize a few thematic imports:

```yaml
# theme.yaml
imports:
  # Reference all commons
  CameraAngle: ../_commons/camera_angles.yaml
  Rendering: ../_commons/rendering.yaml
  ContentRating: ../_commons/content_rating.yaml
  ContentRating.xxx: ../_commons/content_rating.xxx.yaml

  # Customize only hair and outfit
  Hair: mytheme/hair.yaml
  Outfit: mytheme/outfit.yaml

  # Reuse default variations for everything else
  Locations: ../../variations/default/locations.yaml
  Ambiance: ../../variations/default/ambiance.yaml
```

### Pattern 2: Full Custom Theme

For themes with complete custom aesthetics:

```yaml
imports:
  # Commons
  CameraAngle: ../_commons/camera_angles.yaml
  Rendering: ../_commons/rendering.yaml

  # Everything custom
  Hair: mytheme/mytheme-hair.yaml
  Outfit: mytheme/mytheme-outfit.yaml
  Outfit.xxx: mytheme/mytheme-outfit-xxx.yaml
  Locations: mytheme/mytheme-locations.yaml
  Ambiance: mytheme/mytheme-ambiance.yaml
  Gestures: mytheme/mytheme-gestures.yaml
  Gestures.xxx: mytheme/mytheme-gestures-xxx.yaml
```

### Pattern 3: Theme with Removals

For themes that don't use certain placeholders:

```yaml
imports:
  # Regular imports
  Hair: mytheme/hair.yaml
  Outfit: mytheme/outfit.yaml

  # Remove unnecessary placeholders
  Underwear: [Remove]           # Theme doesn't need underwear
  Accessories: [Remove]         # Theme doesn't use accessories
  Makeup.xxx: [Remove]          # No makeup for xxx style specifically
```

---

## Troubleshooting

### Error: "Unresolved placeholders"

**Symptom**:
```
✗ V2 Pipeline error: Unresolved placeholders detected: CameraAngle, Rendering
```

**Cause**: Theme is missing imports that the prompt uses.

**Fix**:
1. Check which placeholders the prompt uses: `grep -oE '\{[A-Z][a-zA-Z0-9]*\}' prompt.yaml`
2. Add missing imports to `theme.yaml`
3. For common imports (CameraAngle, Rendering), reference `../_commons/`

### Missing Style Variants

**Symptom**: Using `--style xxx` but variations don't match the style level.

**Cause**: Theme doesn't define `.xxx` style variants.

**Fix**: Add style-specific variants:
```yaml
imports:
  Outfit: mytheme/outfit.yaml           # Base
  Outfit.xxx: mytheme/outfit-xxx.yaml   # Add this
```

### Fallback to Default Variations

**Symptom**: Theme isn't being applied, seeing default variations instead.

**Cause**:
- Theme name typo in `--theme` parameter
- Theme not discovered (missing `theme.yaml` or autodiscovery not enabled)
- Theme file has syntax errors

**Debug**:
```bash
# List discovered themes
sdgen themes list

# Check if your theme appears
# If not → check autodiscovery config in template.yaml
```

### Relative Path Errors

**Symptom**: `FileNotFoundError` when loading theme imports.

**Cause**: Paths in `theme.yaml` are resolved relative to the **theme file's directory**.

**Fix**:
```yaml
# Wrong: Absolute path
imports:
  Hair: /mnt/d/StableDiffusion/variations/hair.yaml  # ❌ Don't do this

# Correct: Relative to theme.yaml location
imports:
  Hair: ./mytheme-hair.yaml              # ✅ Same directory
  Common: ../_commons/rendering.yaml     # ✅ Parent directory
  Shared: ../../variations/shared.yaml   # ✅ Navigate up
```

---

## Best Practices

### 1. Theme Naming

- Use lowercase with underscores: `tropical_paradise`, `cyberpunk_noir`
- Avoid spaces and special characters
- Keep names short and memorable

### 2. Directory Structure

```
themes/
└── mytheme/
    ├── theme.yaml                    # Theme definition
    ├── README.md                     # Document what prompts this supports
    ├── mytheme-hair.yaml             # Prefix all files with theme name
    ├── mytheme-outfit.yaml
    ├── mytheme-outfit-teasing.yaml
    ├── mytheme-outfit-xxx.yaml
    └── previews/                     # Optional: Preview images
        ├── preview-001.png
        └── preview-002.png
```

### 3. Documentation

Create `README.md` for each theme:

```markdown
# MyTheme

**Description**: Sun-kissed beach paradise aesthetic

**Supported Prompts**:
- v4-solo.prompt.yaml ✅
- v4-couple.prompt.yaml ✅
- v4-boys.prompt.yaml ✅

**Style Variants**:
- default: Casual beachwear
- teasing: Revealing swimwear
- sexy: Minimal coverage
- xxx: Nude/intimate

**Credits**: Inspired by [source]
```

### 4. Version Control

Track themes with git:

```bash
git add themes/mytheme/
git commit -m "feat(themes): Add mytheme with beach aesthetics"
```

### 5. Testing Checklist

Before releasing a theme:

- [ ] Test with all supported prompts
- [ ] Test with all style levels (default, teasing, sexy, xxx)
- [ ] Verify no unresolved placeholders
- [ ] Check manifest.json for correct import sources
- [ ] Generate preview images
- [ ] Document supported prompts in README.md

---

## Advanced: Multi-Theme Projects

For large projects with many themes:

```
prompts/
├── _commons/                    # Shared imports
│   ├── camera_angles.yaml
│   ├── rendering.yaml
│   └── content_rating.yaml
├── themes/
│   ├── tropical/
│   │   ├── theme.yaml
│   │   └── ...
│   ├── cyberpunk/
│   │   ├── theme.yaml
│   │   └── ...
│   └── medieval/
│       ├── theme.yaml
│       └── ...
└── prompts/
    ├── template.yaml            # References themes/
    ├── v4-solo.prompt.yaml
    └── v4-couple.prompt.yaml
```

**Template configuration**:
```yaml
# template.yaml
themes:
  enable_autodiscovery: true
  search_paths:
    - ../themes/          # Search in themes/ directory
    - ./                  # Also search current directory
```

---

## Related Documentation

- [Themes Architecture](../technical/themes-architecture.md) - Technical details
- [Template System V2.0](../technical/template-system-v2.md) - Overall system
- [Style-Sensitive Placeholders](../technical/style-sensitive-placeholders.md) - Style system

---

## Quick Reference

### Theme Definition Skeleton

```yaml
type: theme_config
version: "2.0"
name: <theme_name>

imports:
  # Commons (required)
  CameraAngle: ../_commons/camera_angles.yaml
  Rendering: ../_commons/rendering.yaml
  ContentRating: ../_commons/content_rating.yaml
  ContentRating.xxx: ../_commons/content_rating.xxx.yaml

  # Thematic (customize these)
  Hair: <theme_name>/<theme_name>-hair.yaml
  Outfit: <theme_name>/<theme_name>-outfit.yaml
  Outfit.xxx: <theme_name>/<theme_name>-outfit-xxx.yaml
  # ... add more as needed

variations:
  - Hair
  - Outfit
  # ... list thematic variations
```

### Usage Commands

```bash
# Generate with theme
sdgen generate -t prompt.yaml --theme <name>

# With style
sdgen generate -t prompt.yaml --theme <name> --style xxx

# List themes
sdgen themes list

# Validate theme
sdgen validate themes/mytheme/theme.yaml
```
