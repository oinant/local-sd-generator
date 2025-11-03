# Themes Troubleshooting Guide

Quick reference for common theme-related errors and their solutions.

---

## Error: "Unresolved placeholders detected"

### Example

```
✗ V2 Pipeline error: ✗ Unresolved placeholders detected: CameraAngle, ContentRating, Rendering

Diagnostics:
  • CameraAngle:
      → NOT found in loaded imports
      → This placeholder needs to be defined in:
         - Theme 'tropical' imports section (theme.yaml)
         - Template imports section (template.yaml)
         - Prompt imports section (prompt.yaml)
```

### Cause

The theme is **missing imports** that the prompt uses. This happens because themes use **complete substitution** - they replace ALL template imports.

### Solution

**Step 1**: Identify which imports are missing
```bash
# The error message lists them: CameraAngle, ContentRating, Rendering
```

**Step 2**: Check if these are "common" imports in the parent template
```bash
grep -A 50 "^imports:" prompts/hassaku-teasing/_tpl_base_themable.template.yaml
```

**Step 3**: Add missing imports to your theme.yaml
```yaml
# tropical/theme.yaml
imports:
  # Add missing common imports
  CameraAngle: ../_commons/camera_angles.yaml
  Rendering: ../_commons/rendering.yaml
  ContentRating: ../_commons/content_rating.yaml
  ContentRating.xxx: ../_commons/content_rating.xxx.yaml

  # Your existing thematic imports
  Hair: tropical/tropical-hair.yaml
  Outfit: tropical/tropical-outfit.yaml
  # ...
```

**Step 4**: Test again
```bash
sdgen generate -t prompt.yaml --theme tropical --style xxx -n 1
```

### Prevention

**Always include common imports from parent template** when creating a theme:
- CameraAngle
- Rendering
- ContentRating (+ style variants)
- Any other imports defined in the template that ALL prompts need

---

## Error: "Theme 'X' not found"

### Example

```
❌ Theme 'tropical' not found
💡 Available themes: (none)
   Or use --theme-file to load a custom theme
```

### Cause

Theme autodiscovery is not finding your theme.

### Solutions

#### Check 1: theme.yaml exists

```bash
# Verify theme file exists
ls prompts/hassaku-teasing/tropical/theme.yaml
```

#### Check 2: Autodiscovery is enabled

```yaml
# _tpl_base_themable.template.yaml
themes:
  enable_autodiscovery: true  # Must be true
  search_paths:
    - ./                       # Searches current directory
```

#### Check 3: Theme has correct type

```yaml
# tropical/theme.yaml
type: theme_config  # Must be exactly "theme_config"
name: tropical      # Theme name (used in --theme parameter)
```

#### Check 4: Theme name matches directory

```bash
# If directory is "tropical/", theme name should be "tropical"
name: tropical  # ✅ Matches directory name
```

### Debug

```bash
# List discovered themes
sdgen themes list

# If your theme doesn't appear:
# 1. Check search_paths in template.yaml
# 2. Verify theme.yaml exists in theme directory
# 3. Check type: theme_config in theme.yaml
```

---

## Error: "FileNotFoundError" for import

### Example

```
[ERROR] [Hair] Import file not found: tropical/hair.yaml
        → Tried: /mnt/d/StableDiffusion/private-new/prompts/hassaku-teasing/tropical/tropical/hair.yaml
```

### Cause

Path in theme.yaml is incorrect (wrong relative path resolution).

### Understanding Path Resolution

**All paths in theme.yaml are resolved relative to the theme.yaml file location.**

```
prompts/hassaku-teasing/
├── tropical/
│   ├── theme.yaml              ← Paths resolved from here
│   ├── tropical-hair.yaml      ← ./tropical-hair.yaml or just tropical-hair.yaml
│   └── ...
└── _commons/
    └── camera_angles.yaml      ← ../_commons/camera_angles.yaml
```

### Solution

Fix the path in theme.yaml:

```yaml
# ❌ Wrong
imports:
  Hair: tropical/tropical-hair.yaml  # Looks for tropical/tropical/tropical-hair.yaml

# ✅ Correct - Relative to theme.yaml location
imports:
  Hair: ./tropical-hair.yaml         # Same directory as theme.yaml
  # OR
  Hair: tropical-hair.yaml           # Implicit same directory

  # Parent directory
  CameraAngle: ../_commons/camera_angles.yaml  # Up one level, then _commons/
```

### Path Patterns

```yaml
imports:
  # Same directory as theme.yaml
  Hair: ./hair.yaml
  Hair: hair.yaml              # Equivalent

  # Subdirectory
  Hair: variations/hair.yaml

  # Parent directory
  Common: ../shared/common.yaml

  # Navigate up multiple levels
  Shared: ../../variations/shared.yaml
```

---

## Missing Style Variants (No Error but Wrong Variations)

### Symptom

Using `--style xxx` but seeing default/tame variations instead of explicit xxx-level content.

### Cause

Theme doesn't provide style-specific variants for style-sensitive placeholders.

### Solution

**Step 1**: Check which placeholders are style-sensitive
```yaml
# template.yaml or prompt.yaml
style_sensitive_placeholders:
  - Outfit
  - Gestures
  - MaleBoy
```

**Step 2**: Provide style variants in theme.yaml
```yaml
# theme.yaml
imports:
  # Base (default style)
  Outfit: tropical/outfit.yaml

  # Style variants
  Outfit.revealing: tropical/outfit-revealing.yaml
  Outfit.teasing: tropical/outfit-teasing.yaml
  Outfit.sexy: tropical/outfit-sexy.yaml
  Outfit.xxx: tropical/outfit-xxx.yaml  # ← Add this for --style xxx
```

**Note**: System will fallback to base variant if style-specific variant is missing (not an error, but may not be desired behavior).

---

## Debug Messages Not Showing

### Symptom

Not seeing `[LOAD]` messages for imports.

### Cause

Messages are only printed during import resolution phase.

### Solution

Check that you're looking at the right part of output:

```bash
sdgen generate -t prompt.yaml --theme tropical --style xxx -n 1

# Look for this section:
# Loading template: /path/to/prompt.yaml
# Theme: tropical
# Style: xxx
# [LOAD] [FemaleCharacter] Loading: tropical/tropical-girl.yaml  ← Should see these
# [LOAD] [HairCut] Loading: tropical/tropical-haircut.yaml
```

If you don't see ANY `[LOAD]` messages:
- Theme is not being applied
- Check theme discovery (see "Theme 'X' not found" section above)

---

## [Remove] Directive Not Working

### Symptom

Used `[Remove]` directive but placeholder still appears in prompt.

### Check 1: Correct Syntax

```yaml
# ✅ Correct
imports:
  Underwear: [Remove]

# ❌ Wrong
imports:
  Underwear: "[Remove]"  # Don't quote it
  Underwear: Remove      # Need square brackets
```

### Check 2: Style-Specific Removal

```yaml
# Remove for all styles
imports:
  Underwear: [Remove]

# Remove only for xxx style
imports:
  Underwear: mytheme/underwear.yaml  # Has underwear normally
  Underwear.xxx: [Remove]             # No underwear for xxx style
```

### Expected Behavior

`[Remove]` makes the placeholder resolve to **empty string** (not an error):

```
# Prompt template
{Outfit}, {Underwear}, {Location}

# With Underwear: [Remove]
# Result
bikini top, , beach  # Empty string where {Underwear} was
```

---

## Imports from Wrong Source

### Symptom

Checking manifest.json and seeing imports come from wrong source (template instead of theme).

### Example

```json
{
  "import_sources": {
    "Hair": "template:base.template.yaml",  // ❌ Should be from theme
    "Outfit": "theme:tropical"              // ✅ Correct
  }
}
```

### Cause

Theme doesn't define the import, so it falls through to template import (if prompt has explicit import overrides).

### Solution

Define ALL thematic imports in theme.yaml:

```yaml
imports:
  Hair: tropical/hair.yaml     # ✅ Now comes from theme
  Outfit: tropical/outfit.yaml
  # ... define all thematic imports
```

---

## Theme Works but Generates Wrong Aesthetics

### Symptom

Theme is loaded successfully but variations don't match expected aesthetic.

### Debug Steps

**Step 1**: Check which variations are loaded

```bash
# Generate with -n 1 to see one example
sdgen generate -t prompt.yaml --theme tropical -n 1

# Check manifest.json
cat apioutput/<session_name>/manifest.json
```

**Step 2**: Verify variation file contents

```bash
# Check what's in your variation file
cat prompts/hassaku-teasing/tropical/tropical-hair.yaml
```

**Step 3**: Verify import paths

```yaml
# theme.yaml - make sure paths are correct
imports:
  Hair: tropical/tropical-hair.yaml  # Should point to YOUR theme file
  # Not:
  # Hair: ../variations/default/hair.yaml  # ❌ Points to default variations
```

---

## Quick Diagnostic Commands

```bash
# 1. List available themes
sdgen themes list

# 2. Check which imports are in template
grep -A 50 "^imports:" path/to/template.yaml

# 3. Check which imports are in theme
grep -A 100 "^imports:" path/to/theme.yaml

# 4. Find placeholders used in prompt
grep -oE '\{[A-Z][a-zA-Z0-9]*\}' path/to/prompt.yaml

# 5. Compare template imports vs theme imports
comm -3 \
  <(grep -A 50 "^imports:" template.yaml | grep ":" | cut -d: -f1 | sort) \
  <(grep -A 100 "^imports:" theme.yaml | grep ":" | cut -d: -f1 | sort)
# Shows imports in template but NOT in theme (will be lost)

# 6. Verify theme autodiscovery config
grep -A 10 "^themes:" template.yaml

# 7. Check import sources in manifest
cat apioutput/<session>/manifest.json | jq .import_sources
```

---

## Still Having Issues?

### Checklist

- [ ] Theme has `type: theme_config`
- [ ] Theme name matches directory name
- [ ] Autodiscovery is enabled in template
- [ ] Theme.yaml defines ALL imports that prompt uses
- [ ] Common imports (CameraAngle, Rendering, ContentRating) are included
- [ ] Paths are relative to theme.yaml location
- [ ] Style variants are provided for style-sensitive placeholders
- [ ] Tested with `sdgen generate -n 1` to verify

### Get Help

If still stuck, gather this info:

1. Full command: `sdgen generate -t ... --theme ... --style ...`
2. Error message (full output)
3. Theme structure: `tree prompts/hassaku-teasing/tropical/`
4. Theme imports: `grep -A 100 "^imports:" theme.yaml`
5. Prompt placeholders: `grep -oE '\{[A-Z][a-zA-Z0-9]*\}' prompt.yaml`

---

## Related Documentation

- [Themes Usage Guide](./themes-guide.md) - How to create themes
- [Themes Architecture](../technical/themes-architecture.md) - Technical details
- [Template System V2.0](../technical/template-system-v2.md) - Overall system
