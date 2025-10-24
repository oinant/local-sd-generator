# Themable Templates - CLI Reference

Référence complète des commandes CLI pour les Themable Templates.

## Table des matières

- [sdgen generate](#sdgen-generate)
- [sdgen theme list](#sdgen-theme-list)
- [sdgen theme show](#sdgen-theme-show)
- [sdgen theme validate](#sdgen-theme-validate)
- [File Formats](#file-formats)

---

## sdgen generate

Generate images using a themable template with optional theme and style.

### Syntax

```bash
sdgen generate [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--template` | `-t` | PATH | None | Path to .template.yaml or .prompt.yaml file |
| `--theme` | - | TEXT | None | Theme name (e.g., cyberpunk, rockstar) |
| `--style` | - | TEXT | `default` | Art style (cartoon, realistic, etc.) |
| `--count` | `-n` | INT | None | Number of images to generate |
| `--dry-run` | - | FLAG | False | Save API payloads without generating |
| `--session-name` | - | TEXT | None | Override session name |

### Examples

#### Basic theme usage

```bash
# Generate with cyberpunk theme
sdgen generate -t _tpl_teasing.template.yaml --theme cyberpunk

# Generate with pirates theme, 50 images
sdgen generate -t _tpl_teasing.template.yaml --theme pirates -n 50
```

#### Theme + Style

```bash
# Cyberpunk in cartoon style
sdgen generate -t _tpl_teasing.template.yaml --theme cyberpunk --style cartoon

# Rockstar in realistic style
sdgen generate -t _tpl_teasing.template.yaml --theme rockstar --style realistic -n 100
```

#### Without theme

```bash
# Use template defaults only
sdgen generate -t _tpl_teasing.template.yaml

# With style but no theme
sdgen generate -t _tpl_teasing.template.yaml --style photorealistic
```

#### Dry run

```bash
# Preview API payloads without generating
sdgen generate -t _tpl_teasing.template.yaml --theme cyberpunk --dry-run
```

### Output

**Session directory:**
```
YYYYMMDD_HHMMSS_TemplateName_ThemeName_Style/
├── manifest.json
├── 001_haircut_haircolor.png
├── 002_haircut_haircolor.png
└── ...
```

**Manifest contains:**
- `theme_name` - Theme used (or null)
- `style` - Style used
- `import_resolution` - How each import was resolved

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (file not found, invalid config, etc.) |
| 2 | Validation failed |

---

## sdgen theme list

List all available themes in the configs directory.

### Syntax

```bash
sdgen theme list
```

### Options

None.

### Output

```
Available Themes (6 found)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Theme          Type       Variations
──────────────────────────────────────
cyberpunk      explicit   8 variations
rockstar       explicit   12 variations
pirates        explicit   8 variations
mafia_1920     explicit   8 variations
annees_folles  explicit   8 variations
fantasy        explicit   6 variations
```

**Fields:**
- **Theme** - Theme name
- **Type** - `explicit` (has theme.yaml) or `implicit` (inferred)
- **Variations** - Number of variation files

### Examples

```bash
# List all themes
sdgen theme list
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (themes found) |
| 0 | Success (no themes found - shows empty list) |

---

## sdgen theme show

Show detailed information about a specific theme.

### Syntax

```bash
sdgen theme show <THEME_NAME>
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `THEME_NAME` | TEXT | Yes | Name of the theme to show |

### Output

```
Theme: cyberpunk
Type: Explicit
Path: ./themes/cyberpunk/

Imports:
  HairCut          → cyberpunk/cyberpunk_haircut.yaml
  HairColor        → cyberpunk/cyberpunk_haircolor.yaml
  TechAspect       → cyberpunk/cyberpunk_tech-aspect.yaml
  FemaleCharacter  → cyberpunk/cyberpunk_girl.yaml
  uw               → cyberpunk/cyberpunk_underwear.yaml
  TeasingOutfits   → cyberpunk/cyberpunk_outfit.yaml
  TeasingLocations → cyberpunk/cyberpunk_location.yaml
  TeasingGestures  → cyberpunk/cyberpunk_teasing-gesture.yaml

Variations: 8
Styles detected: default
```

**Fields:**
- **Type** - Explicit or Implicit
- **Path** - Directory path
- **Imports** - List of placeholder → file mappings
- **Variations** - Total variation categories
- **Styles** - Auto-detected styles from import keys

### Examples

```bash
# Show cyberpunk theme details
sdgen theme show cyberpunk

# Show pirates theme
sdgen theme show pirates
```

### Error Handling

```bash
# Theme not found
sdgen theme show unknown

# Output:
❌ Error: Theme 'unknown' not found
Available themes: cyberpunk, rockstar, pirates, mafia_1920, annees_folles, fantasy
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Theme not found |

---

## sdgen theme validate

Validate theme compatibility with a template.

### Syntax

```bash
sdgen theme validate <TEMPLATE_PATH> <THEME_NAME> [OPTIONS]
```

### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `TEMPLATE_PATH` | PATH | Yes | Path to .template.yaml file |
| `THEME_NAME` | TEXT | Yes | Theme name to validate |

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--style` | TEXT | `default` | Style to validate |

### Output

**Compatible theme:**
```
✓ Theme 'cyberpunk' is compatible with template '_tpl_teasing'

Theme provides:
  ✓ HairCut
  ✓ HairColor
  ✓ TechAspect
  ✓ FemaleCharacter
  ✓ TeasingOutfits
  ✓ TeasingLocations
  ✓ TeasingGestures
  ✓ uw (underwear)
```

**Partial compatibility:**
```
⚠ Theme 'cyberpunk' is partially compatible with template '_tpl_teasing'

Theme provides:
  ✓ HairCut
  ✓ HairColor
  ⚠ Outfit (fallback: template default)
  ⚠ Rendering (fallback: common/rendering.default.yaml)

Missing from theme (will use fallbacks):
  - Outfit
  - Rendering
```

**Incompatible:**
```
❌ Theme 'cyberpunk' is NOT compatible with template '_tpl_teasing'

Missing required placeholders:
  ✗ HairCut (no fallback available)
  ✗ Location (no fallback available)
```

### Examples

```bash
# Validate cyberpunk theme with default style
sdgen theme validate _tpl_teasing.template.yaml cyberpunk

# Validate with cartoon style
sdgen theme validate _tpl_teasing.template.yaml cyberpunk --style cartoon

# Validate rockstar theme
sdgen theme validate _tpl_teasing.template.yaml rockstar
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Fully compatible |
| 0 | Partially compatible (warnings) |
| 1 | Incompatible (missing required placeholders) |
| 2 | Template or theme not found |

---

## File Formats

### template.yaml (Themable)

```yaml
version: "2.0"
name: "Template Name"

# Enable theme support
themable: true

# (Optional) Enable style support
style_sensitive: true
style_sensitive_placeholders:
  - Rendering
  - Outfit

# Template with {prompt} placeholder
template: |
  {prompt}
  {Placeholder1}, {Placeholder2}

prompts:
  default: "base prompt"

# Default imports (overridable by themes)
imports:
  Placeholder1: defaults/placeholder1.yaml
  Placeholder2: defaults/placeholder2.yaml

negative_prompt: "low quality"

generation:
  mode: random
  seed: 42
  seed_mode: progressive
  max_images: 100
```

**Required fields:**
- `version` - Must be "2.0"
- `name` - Template name
- `template` - Template string with `{prompt}` placeholder
- `themable` - Set to `true` to enable themes

**Optional fields:**
- `style_sensitive` - Enable style variants
- `style_sensitive_placeholders` - List of style-aware placeholders
- `imports` - Default imports (overridable by themes)

### theme.yaml (Explicit Theme)

```yaml
version: "1.0"
name: theme_name

imports:
  # Non-style-sensitive
  Placeholder1: theme_name/theme_placeholder1.yaml
  Placeholder2: theme_name/theme_placeholder2.yaml

  # Style-sensitive (with suffix)
  Outfit.default:   theme_name/theme_outfit.default.yaml
  Outfit.cartoon:   theme_name/theme_outfit.cartoon.yaml
  Outfit.realistic: theme_name/theme_outfit.realistic.yaml

variations:
  - Placeholder1
  - Placeholder2
  - Outfit
```

**Required fields:**
- `version` - Theme config version
- `name` - Theme name (must match directory name)
- `imports` - Import mappings

**Optional fields:**
- `variations` - List of variation categories (for display)

### Implicit Theme (No theme.yaml)

**Directory structure:**
```
themes/pirates/
├── pirates_haircut.yaml
├── pirates_outfit.yaml
└── pirates_location.yaml
```

**Auto-inferred theme.yaml:**
```yaml
name: pirates
imports:
  HairCut:  pirates/pirates_haircut.yaml
  Outfit:   pirates/pirates_outfit.yaml
  Location: pirates/pirates_location.yaml
```

**Naming convention:**
- `{theme}_{placeholder}.yaml` → `Placeholder: {theme}/{theme}_{placeholder}.yaml`
- `{theme}_{placeholder}.{style}.yaml` → `Placeholder.{style}: {theme}/{theme}_{placeholder}.{style}.yaml`

### prompt.yaml (Using Themable Template)

```yaml
version: "2.0"
name: "Prompt Name"

# Use themable template
implements: "./_tpl_themable.template.yaml"

# Only override common imports if needed
imports:
  CommonVar1: ../common/var1.yaml
  CommonVar2: ../common/var2.yaml
  # Theme provides the rest!

generation:
  mode: random
  seed: 42
  max_images: 100
```

**Usage:**
```bash
# Generate with pirates theme
sdgen generate -t prompt.yaml --theme pirates

# Switch theme without changing file
sdgen generate -t prompt.yaml --theme cyberpunk
```

---

## Environment Variables

### SDGEN_CONFIGS_DIR

Override the configs directory path.

```bash
export SDGEN_CONFIGS_DIR=/path/to/configs
sdgen generate -t template.yaml --theme cyberpunk
```

**Default:** `./configs` (relative to current directory)

### SDGEN_OUTPUT_DIR

Override the output directory path.

```bash
export SDGEN_OUTPUT_DIR=/path/to/output
sdgen generate -t template.yaml
```

**Default:** `./output` or value from `sdgen_config.json`

---

## Configuration File

### sdgen_config.json

```json
{
  "configs_dir": "./prompts",
  "output_dir": "./results",
  "api_url": "http://127.0.0.1:7860"
}
```

**Location:** Current working directory (`./ sdgen_config.json`)

**Initialize:**
```bash
sdgen init
```

**Fields:**
- `configs_dir` - Base directory for configs and themes
- `output_dir` - Output directory for generated images
- `api_url` - Stable Diffusion WebUI API URL

---

## Naming Conventions

### Templates

- **Themable templates:** `_tpl_{name}.template.yaml`
- **Non-themable templates:** `{name}.template.yaml`

### Themes

- **Theme directory:** `themes/{theme_name}/`
- **Theme config:** `themes/{theme_name}/theme.yaml` (explicit)
- **Variation files:** `{theme_name}_{placeholder}.yaml`

### Styles

- **Default:** `{basename}.yaml` or `{basename}.default.yaml`
- **Styled:** `{basename}.{style}.yaml`

**Examples:**
- `outfit.yaml` → default
- `outfit.default.yaml` → default (explicit)
- `outfit.cartoon.yaml` → cartoon style
- `outfit.realistic.yaml` → realistic style

### Session Names

**Format:** `YYYYMMDD_HHMMSS_TemplateName_ThemeName_Style`

**Examples:**
- `20251025_120000_Teasing_cyberpunk_default`
- `20251025_120530_Teasing_pirates_cartoon`
- `20251025_121000_Teasing_rockstar_realistic`

---

## Common Patterns

### Generate for all themes

```bash
for theme in $(sdgen theme list | tail -n +4 | awk '{print $1}'); do
  sdgen generate -t template.yaml --theme $theme -n 25
done
```

### Generate multiple styles

```bash
for style in default cartoon realistic; do
  sdgen generate -t template.yaml --theme cyberpunk --style $style -n 20
done
```

### Matrix generation

```bash
for theme in cyberpunk rockstar pirates; do
  for style in cartoon realistic; do
    sdgen generate -t template.yaml --theme $theme --style $style -n 10
  done
done
```

### Dry-run validation

```bash
# Check what would be generated without actually generating
sdgen generate -t template.yaml --theme cyberpunk --style cartoon --dry-run
```

---

## Troubleshooting

### Theme not found

**Error:**
```
❌ Error: Theme 'unknown' not found
```

**Solution:**
```bash
# List available themes
sdgen theme list

# Check theme exists in configs_dir/themes/
ls -la ./prompts/themes/
```

### Missing import

**Warning:**
```
⚠ Warning: Theme 'cyberpunk' missing Outfit.realistic, using fallback
```

**Explanation:** Non-blocking. The system uses fallback (template or common).

**Fix (optional):** Create the missing file:
```bash
# Create cyberpunk_outfit.realistic.yaml
cp cyberpunk/cyberpunk_outfit.default.yaml \
   cyberpunk/cyberpunk_outfit.realistic.yaml
```

### Template not themable

**Error:**
```
❌ Error: Template '_tpl_old.template.yaml' is not themable
```

**Solution:** Add `themable: true` to the template:
```yaml
version: "2.0"
name: "Template"
themable: true  # Add this
```

---

## See Also

- [Usage Guide](../usage/themable-templates.md) - Guide utilisateur complet
- [Technical Documentation](../technical/themable-templates.md) - Architecture interne
- [Template System V2](./template-system-v2.md) - Système de templates
