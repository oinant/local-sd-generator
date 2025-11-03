# Theme System Architecture (V2.0)

**Component**: Template System V2.0
**Location**: `sd_generator_cli/templating/`
**Status**: Stable
**Last Updated**: 2025-01-03

---

## Overview

The Theme System allows complete customization of variation imports for different thematic contexts (e.g., cyberpunk, tropical, medieval) while preserving the prompt's structure and logic.

**Key Principle**: Themes use **COMPLETE SUBSTITUTION** of imports, not merging.

---

## Architecture

### Import Resolution Flow

```
1. Load Prompt Config
   ├── imports: {} (usually empty)
   └── implements: template.yaml

2. Resolve Inheritance Chain
   ├── Merge prompt ← template ← grandparent...
   └── Result: resolved_config with all parent imports

3. Apply Theme (if --theme specified)
   ├── Load theme.yaml
   ├── Filter theme imports by style (--style)
   └── REPLACE resolved_config.imports = filtered_theme_imports  ← COMPLETE SUBSTITUTION

4. Re-apply Prompt's Explicit Imports
   └── Override theme imports with prompt-specific overrides

5. Load Variation Files
   └── Resolve each import path and load variations

6. Generate Prompts
   └── Detect unresolved placeholders
```

### Code Reference

**orchestrator.py:257** (Complete Substitution):
```python
# COMPLETE substitution of template imports by theme
resolved_config.imports = filtered_theme_imports
```

**orchestrator.py:261** (Prompt overrides):
```python
# Re-apply prompt's explicit imports as final overrides
resolved_config.imports.update(prompt_explicit_imports)
```

---

## Complete Substitution Model

### What Happens

When a theme is applied:

1. **Template imports are REPLACED** (not merged)
2. **Theme imports become the source of truth**
3. **Only prompt's explicit imports survive** as overrides

### Example

**Template defines**:
```yaml
imports:
  CameraAngle: common/camera_angles.yaml
  Rendering: common/rendering.yaml
  Hair: variations/hair.yaml
```

**Theme defines**:
```yaml
imports:
  Hair: themes/cyberpunk/cyber_hair.yaml
  Outfit: themes/cyberpunk/cyber_outfit.yaml
```

**Result after theme application**:
```yaml
imports:
  # ✅ From theme
  Hair: themes/cyberpunk/cyber_hair.yaml
  Outfit: themes/cyberpunk/cyber_outfit.yaml

  # ❌ LOST from template
  # CameraAngle: ...
  # Rendering: ...
```

**Consequence**: If prompt uses `{CameraAngle}` → **ValueError: Unresolved placeholder**

---

## Why Complete Substitution?

### Design Rationale

1. **Thematic Coherence**: Ensures ALL variations match the theme's aesthetic
2. **No Mixing**: Prevents accidental mixing of cyberpunk hair with medieval outfits
3. **Explicit Control**: Theme author has full control over which variations are available
4. **Predictable Behavior**: Clear and deterministic - no complex merge rules

### Alternative Considered (Merge)

A merge-based approach was considered but rejected:

```yaml
# Hypothetical merge behavior (NOT implemented)
imports:
  CameraAngle: common/camera_angles.yaml  # From template
  Rendering: common/rendering.yaml        # From template
  Hair: themes/cyberpunk/cyber_hair.yaml  # From theme (overrides template)
  Outfit: themes/cyberpunk/cyber_outfit.yaml  # From theme
```

**Why rejected**:
- Hard to predict which imports come from where
- Risk of "theme leakage" (non-thematic variations sneaking in)
- Complex conflict resolution rules
- Theme authors lose control over the final import set

---

## Style-Aware Filtering

Themes can define **style-specific variants** of placeholders:

### Theme Definition

```yaml
imports:
  # Base version (default style)
  Outfit: themes/cyberpunk/outfit.yaml

  # Style-specific variants
  Outfit.teasing: themes/cyberpunk/outfit_teasing.yaml
  Outfit.sexy: themes/cyberpunk/outfit_sexy.yaml
  Outfit.xxx: themes/cyberpunk/outfit_xxx.yaml
```

### Resolution with `--style xxx`

```python
# orchestrator.py filters imports by style
if '.' in import_name:
    base_name, import_style = import_name.rsplit('.', 1)
    if import_style == style:
        # Use style-specific variant
        filtered_theme_imports[base_name] = import_path
```

**Result**:
```yaml
imports:
  Outfit: themes/cyberpunk/outfit_xxx.yaml  # .xxx variant used
```

---

## [Remove] Directive

Themes can **explicitly remove** placeholders using `[Remove]` directive:

### Theme Definition

```yaml
imports:
  Underwear: [Remove]  # Remove this placeholder entirely
  Outfit.xxx: [Remove]  # Remove for xxx style specifically
```

### Effect

```python
# orchestrator.py tracks removed placeholders
removed_placeholders.add(import_name)
# Placeholder will resolve to empty string ""
```

**Use case**: Some themes (e.g., naturist) don't need underwear variations.

---

## Import Sources Tracking

The system tracks **where each import comes from** for debugging:

```python
# orchestrator.py:264-267
for placeholder in theme.imports.keys():
    import_sources[placeholder] = f"theme:{theme.name}"
for placeholder in prompt_explicit_imports.keys():
    import_sources[placeholder] = f"prompt:{config.source_file.name}"
```

**Stored in**: `ResolvedContext.import_sources`

**Used in**: Manifest generation, debug messages

---

## Common Pitfalls

### 1. Missing Common Imports

**Problem**: Template defines "common" imports that themes forget to redefine

```yaml
# template.yaml
imports:
  CameraAngle: common/camera_angles.yaml  # "common" import
  Hair: variations/hair.yaml              # thematic import

# theme.yaml
imports:
  Hair: themes/cyberpunk/hair.yaml  # Redefines Hair
  # ❌ Forgets CameraAngle
```

**Result**: `ValueError: Unresolved placeholder: CameraAngle`

**Solution**: Themes must be **self-sufficient** and define ALL imports needed by prompts.

### 2. Style-Sensitive Misconfiguration

**Problem**: Template declares placeholder as style-sensitive but theme doesn't provide variants

```yaml
# template.yaml
style_sensitive_placeholders:
  - Outfit

# theme.yaml
imports:
  Outfit: themes/cyberpunk/outfit.yaml  # ❌ No .xxx variant

# With --style xxx
# Result: Fallback to base variant (not an error, but may not be intended)
```

**Solution**: Provide all style variants if placeholder is style-sensitive.

### 3. Absolute vs Relative Paths

**Problem**: Theme uses relative paths that are resolved relative to theme file location

```yaml
# themes/cyberpunk/theme.yaml
imports:
  Hair: ./hair.yaml  # ✅ Relative to themes/cyberpunk/
  Outfit: hair.yaml  # ✅ Also relative to themes/cyberpunk/
  Common: ../../common/camera.yaml  # ✅ Go up and navigate
```

**Note**: All paths in theme.yaml are resolved relative to the theme file's directory.

---

## Best Practices

### Theme Structure

```
themes/
└── cyberpunk/
    ├── theme.yaml              # Theme definition
    ├── cyber_hair.yaml         # Thematic variations
    ├── cyber_outfit.yaml
    ├── cyber_outfit_xxx.yaml   # Style variant
    └── ...

# Alternative: Reference shared commons
themes/
├── _commons/                   # Shared across themes
│   ├── camera_angles.yaml
│   └── rendering.yaml
└── cyberpunk/
    ├── theme.yaml              # References ../_commons/
    └── ...
```

### Theme Definition Template

```yaml
type: theme_config
version: "2.0"
name: mytheme

imports:
  # ========================================
  # COMMON IMPORTS (required by all prompts)
  # ========================================
  CameraAngle: ../_commons/camera_angles.yaml
  Rendering:   ../_commons/rendering.yaml
  ContentRating: ../_commons/content_rating.yaml
  ContentRating.xxx: ../_commons/content_rating_xxx.yaml

  # ========================================
  # THEMATIC IMPORTS (theme-specific)
  # ========================================
  Hair: mytheme/hair.yaml
  Outfit: mytheme/outfit.yaml
  Outfit.teasing: mytheme/outfit_teasing.yaml
  Outfit.sexy: mytheme/outfit_sexy.yaml
  Outfit.xxx: mytheme/outfit_xxx.yaml

  # ========================================
  # OPTIONAL REMOVALS
  # ========================================
  Underwear: [Remove]  # This theme doesn't use underwear

# Declare which variations should change with this theme
variations:
  - Hair
  - Outfit
  - Location
  # ... (optional, for manifest tracking)
```

### Checklist for Theme Authors

Before creating a theme, ensure:

1. ✅ **Audit template imports**: List ALL imports defined in parent template(s)
2. ✅ **Identify common vs thematic**: Separate shared imports (CameraAngle) from theme-specific (Hair)
3. ✅ **Redefine common imports**: Include camera_angles, rendering, etc. in theme
4. ✅ **Provide style variants**: If template declares style-sensitive placeholders, provide .teasing/.sexy/.xxx variants
5. ✅ **Test all prompts**: Run all prompts that use this theme with different --style options
6. ✅ **Document theme**: Add README.md explaining which prompts/templates this theme supports

---

## Debug Tips

### Find Missing Imports

Run with verbose debug to see which imports are loaded:

```bash
sdgen generate -t prompt.yaml --theme mytheme --style xxx -n 1
# Look for [LOAD] messages - missing placeholders won't have [LOAD] lines
```

### Trace Import Sources

Check manifest.json after generation:

```json
{
  "import_sources": {
    "Hair": "theme:cyberpunk",
    "CameraAngle": "template:base.template.yaml",
    "Outfit": "prompt:v4-girls.prompt.yaml"
  }
}
```

### Compare Template vs Theme Imports

```bash
# List template imports
grep -A 50 "^imports:" template.yaml

# List theme imports
grep -A 100 "^imports:" themes/cyberpunk/theme.yaml

# Find imports in template but not in theme
# → These will be LOST when theme is applied
```

---

## Future Considerations

### Potential Enhancements

1. **Theme Inheritance**: Allow themes to inherit from a base theme
   ```yaml
   type: theme_config
   name: cyberpunk_noir
   implements: themes/_base_theme.yaml  # Inherit common imports
   ```

2. **Partial Theme Mode**: Optional merge mode for themes that only override specific imports
   ```yaml
   type: theme_config
   merge_mode: partial  # Don't replace all imports, just override specified ones
   ```

3. **Import Validation**: Warn if theme is missing imports that template defines
   ```bash
   ⚠️ Warning: Theme 'tropical' missing imports: CameraAngle, Rendering
   ```

4. **Theme Compatibility Matrix**: Document which themes work with which templates

**Note**: These are not implemented yet. Current behavior is **complete substitution only**.

---

## Related Documentation

- [Themes Usage Guide](../usage/themes-guide.md) - How to use themes
- [Template System V2.0](./template-system-v2.md) - Overall architecture
- [Import Resolution](./import-resolution.md) - How imports are resolved
- [Style-Sensitive Placeholders](./style-sensitive-placeholders.md) - Style system

---

## Changelog

- **2025-01-03**: Initial documentation of complete substitution model
