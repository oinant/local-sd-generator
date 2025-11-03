# Themes Documentation

Complete documentation for the Theme System in Template System V2.0.

---

## 📚 Documentation Structure

### For Users

- **[Themes Usage Guide](usage/themes-guide.md)** - How to use and create themes
  - Basic usage
  - Creating themes step-by-step
  - Style-aware themes
  - Best practices
  - Testing checklist

- **[Themes Troubleshooting](usage/themes-troubleshooting.md)** - Common errors and fixes
  - Unresolved placeholders
  - Theme not found
  - File path errors
  - Style variants issues
  - Diagnostic commands

### For Developers

- **[Themes Architecture](technical/themes-architecture.md)** - Technical documentation
  - Complete substitution model
  - Import resolution flow
  - Style-aware filtering
  - [Remove] directive
  - Why complete substitution (design rationale)
  - Debug tips
  - Future enhancements

---

## 🚀 Quick Start

### Using a Theme

```bash
# Generate with a theme
sdgen generate -t prompt.yaml --theme cyberpunk

# With style variation
sdgen generate -t prompt.yaml --theme cyberpunk --style sexy
```

### Creating a Theme

```bash
# 1. Create theme directory
mkdir -p prompts/hassaku-teasing/mytheme

# 2. Create theme.yaml
cat > prompts/hassaku-teasing/mytheme/theme.yaml <<EOF
type: theme_config
version: "2.0"
name: mytheme

imports:
  # Common imports (required)
  CameraAngle: ../_commons/camera_angles.yaml
  Rendering: ../_commons/rendering.yaml
  ContentRating: ../_commons/content_rating.yaml

  # Thematic imports (custom)
  Hair: mytheme/mytheme-hair.yaml
  Outfit: mytheme/mytheme-outfit.yaml
EOF

# 3. Create variation files
# ... (see usage guide for details)

# 4. Test
sdgen generate -t prompt.yaml --theme mytheme -n 1
```

---

## ⚠️ Key Concepts

### Complete Substitution

**Themes REPLACE all template imports** (not merge):

```yaml
# Template defines
imports:
  CameraAngle: common/camera.yaml
  Hair: default/hair.yaml

# Theme defines
imports:
  Hair: mytheme/hair.yaml

# Result after theme application
imports:
  Hair: mytheme/hair.yaml
  # ❌ CameraAngle is LOST
```

**Consequence**: Themes must be **self-sufficient** and define ALL imports needed by prompts.

### Common vs Thematic Imports

- **Common**: Needed by ALL themes → must be redefined in every theme
  - CameraAngle, Rendering, ContentRating
  - Usually reference `_commons/` files

- **Thematic**: Define the theme's unique aesthetic
  - Hair, Outfit, Locations, Ambiance
  - Different for each theme

---

## 📖 Examples

### Minimal Theme

```yaml
type: theme_config
name: minimal

imports:
  # Commons (required)
  CameraAngle: ../_commons/camera_angles.yaml
  Rendering: ../_commons/rendering.yaml

  # Thematic (minimal customization)
  Hair: minimal/hair.yaml
  Outfit: minimal/outfit.yaml
```

### Full Theme with Style Variants

```yaml
type: theme_config
name: tropical

imports:
  # Commons
  CameraAngle: ../_commons/camera_angles.yaml
  Rendering: ../_commons/rendering.yaml
  ContentRating: ../_commons/content_rating.yaml
  ContentRating.xxx: ../_commons/content_rating.xxx.yaml

  # Thematic (style-aware)
  Hair: tropical/hair.yaml
  Outfit: tropical/outfit.yaml
  Outfit.teasing: tropical/outfit-teasing.yaml
  Outfit.sexy: tropical/outfit-sexy.yaml
  Outfit.xxx: tropical/outfit-xxx.yaml

  Locations: tropical/locations.yaml
  Ambiance: tropical/ambiance.yaml
```

---

## 🐛 Common Errors

### Error: "Unresolved placeholders: X, Y, Z"

**Fix**: Add missing imports to theme.yaml
```yaml
imports:
  X: ../_commons/x.yaml
  Y: ../_commons/y.yaml
  Z: ../_commons/z.yaml
```

[See full troubleshooting guide →](usage/themes-troubleshooting.md)

### Error: "Theme 'X' not found"

**Fix**: Enable autodiscovery in template.yaml
```yaml
themes:
  enable_autodiscovery: true
  search_paths:
    - ./
```

[See full troubleshooting guide →](usage/themes-troubleshooting.md)

---

## 🔗 Related Documentation

- [Template System V2.0](technical/template-system-v2.md) - Overall architecture
- [Style-Sensitive Placeholders](technical/style-sensitive-placeholders.md) - Style system
- [Import Resolution](technical/import-resolution.md) - How imports are resolved

---

## 📝 Changelog

- **2025-01-03**: Initial comprehensive documentation of theme system
  - Architecture documentation
  - Usage guide
  - Troubleshooting guide
  - Complete substitution model documented
