# Themable Templates - CLI Reference

Référence complète des commandes CLI, formats de fichiers, et conventions pour le système de themable templates (Phase 2).

## Table des matières

- [CLI Commands](#cli-commands)
- [File Formats](#file-formats)
- [Naming Conventions](#naming-conventions)
- [Configuration](#configuration)
- [Exit Codes](#exit-codes)
- [Environment Variables](#environment-variables)
- [Error Messages](#error-messages)

---

## CLI Commands

### `sdgen list-themes`

Liste les themes disponibles pour un template themable spécifique.

#### Synopsis

```bash
sdgen list-themes -t <template_path> [--configs-dir <path>]
```

#### Options

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `-t, --template` | PATH | ✅ Yes | - | Path to template file to discover themes for |
| `--configs-dir` | PATH | ❌ No | From config | Override configs directory |

#### Behavior

1. Load template file and resolve inheritance chain
2. Check if template has `themes:` block
3. Discover available themes (explicit + autodiscovered)
4. Load each theme and validate imports
5. Display detailed theme information with rich formatting

#### Output Format

```
📋 Theme Configuration
├─ Autodiscovery: ✓ Enabled / ✗ Disabled
├─ Search paths:
│  ├─ • ./themes/
│  └─ • ../shared/
└─ Explicit themes: N
   ├─ • theme1
   └─ • theme2

🎨 pirates (autodiscovered)
├─ Path: ./themes/pirates/theme.yaml
└─ Imports: 8
   ├─ ✓ HairCut → pirates/pirates-haircut.yaml
   ├─ ✓ Outfit → pirates/pirates-outfit.yaml
   ├─ ✗ Location → pirates/location.yaml (missing)
   └─ ...

Summary: N theme(s) found
  • X explicit
  • Y autodiscovered
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (themes found or template not themable) |
| 1 | Template file not found or invalid |

#### Examples

```bash
# List themes for a template (autodiscovery enabled)
sdgen list-themes -t ./prompts/character.template.yaml

# With custom configs directory
sdgen list-themes -t template.yaml --configs-dir /path/to/configs

# Template not found
sdgen list-themes -t nonexistent.yaml
# Error: Template not found: nonexistent.yaml

# Template not themable
sdgen list-themes -t regular_template.yaml
# ⚠ Template 'RegularTemplate' is not themable
# 💡 Add a 'themes:' block to make it themable
```

---

### `sdgen generate` (with themes)

Génère des images depuis un template themable avec un theme optionnel.

#### Synopsis

```bash
sdgen generate [OPTIONS]
```

#### Theme Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--template` | `-t` | PATH | None | Path to .template.yaml or .prompt.yaml file |
| `--theme` | - | TEXT | None | Theme name (must be in template's themes: block) |
| `--theme-file` | - | PATH | None | Direct path to theme.yaml (bypasses discovery) |
| `--style` | - | TEXT | `default` | Art style (cartoon, realistic, etc.) |

**⚠️ Important:** `--theme` et `--theme-file` sont mutuellement exclusifs.

#### Other Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--count` | `-n` | INT | None | Maximum number of images to generate |
| `--dry-run` | - | FLAG | False | Save API payloads without generating |
| `--session-name` | `-sn` | TEXT | None | Override session directory name |
| `--api-url` | - | URL | From config | Override SD API URL |

#### Behavior (Theme Resolution)

1. Load template file and resolve inheritance
2. If `--theme` provided:
   - Check `themes:` block exists
   - Discover available themes (explicit + autodiscovered)
   - Validate theme name exists
   - Load theme from discovered path
3. If `--theme-file` provided:
   - Load theme directly from file (bypass discovery)
4. Apply theme with priority: prompt > theme > template
5. Generate images with resolved imports

#### Output

**Session directory format:**
```
YYYYMMDD_HHMMSS-SessionName-ThemeName-Style/
├── manifest.json
├── SessionName_0000.png
├── SessionName_0001.png
└── ...
```

**Examples:**
- With theme: `20251029_143022-teasing-cyberpunk-cartoon/`
- No theme: `20251029_143522-portrait/` (default style omitted when alone)
- Custom style: `20251029_144012-character-realistic/`

**Manifest enrichment:**
```json
{
  "snapshot": {
    "theme_name": "cyberpunk",
    "style": "cartoon",
    ...
  }
}
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (missing file, invalid config, API connection failed) |
| 130 | Interrupted by user (Ctrl+C) |

#### Examples

```bash
# Basic theme usage
sdgen generate -t template.yaml --theme pirates

# Theme + style
sdgen generate -t template.yaml --theme cyberpunk --style cartoon -n 50

# Direct theme file (bypass discovery)
sdgen generate -t template.yaml --theme-file ~/my-themes/custom/theme.yaml

# Without theme (use template defaults)
sdgen generate -t template.yaml

# Dry-run to preview
sdgen generate -t template.yaml --theme pirates --dry-run

# Error: Both --theme and --theme-file
sdgen generate -t template.yaml --theme pirates --theme-file custom.yaml
# ✗ Cannot use both --theme and --theme-file

# Error: No themes: block
sdgen generate -t old_template.yaml --theme pirates
# ❌ No 'themes:' block found in OldTemplate
# 💡 Use --theme-file to specify theme path directly, or add a themes: block

# Error: Theme not found
sdgen generate -t template.yaml --theme unknown
# ❌ Theme 'unknown' not found
# 💡 Available themes: pirates, cyberpunk, rockstar
#    Or use --theme-file to load a custom theme
```

---

### `sdgen theme list`

Liste tous les themes disponibles dans le système (global).

#### Synopsis

```bash
sdgen theme list
```

#### Options

None.

#### Behavior

1. Load global configuration
2. Scan `configs_dir/themes/` directory
3. Discover all themes (explicit and implicit)
4. Display summary table

#### Output Format

```
Available Themes (N found)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Theme          Type       Variations
───────────────────────────────────
cyberpunk      explicit   8 variations
rockstar       explicit   12 variations
pirates        explicit   8 variations
mafia_1920     explicit   8 variations
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | No config found (run `sdgen init`) |

#### Examples

```bash
# List all themes
sdgen theme list

# No config
sdgen theme list
# ✗ No config found in current directory
# Run 'sdgen init' to create sdgen_config.json
```

---

### `sdgen theme show`

Affiche les détails d'un theme spécifique (global).

#### Synopsis

```bash
sdgen theme show <theme_name>
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `theme_name` | TEXT | ✅ Yes | Name of the theme to display |

#### Options

None.

#### Behavior

1. Load global configuration
2. Load theme by name from `configs_dir/themes/`
3. Display theme details (type, path, imports, variations, styles)

#### Output Format

```
┌────────────────────────┐
│      cyberpunk         │
└────────────────────────┘

Property  Value
────────────────────────────────────────────────────
Path      ./themes/cyberpunk/
Type      Explicit (theme.yaml)
Styles    default, cartoon, realistic
Variations   Ambiance, HairCut, Outfit, Location
Imports   12

Theme Imports:
Placeholder       File
─────────────────────────────────────────────────────────────
Ambiance          cyberpunk/cyberpunk-ambiance.yaml
HairCut           cyberpunk/cyberpunk-haircut.yaml
Outfit            cyberpunk/cyberpunk-outfit.yaml
Outfit.cartoon    cyberpunk/cyberpunk-outfit.cartoon.yaml
...
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Theme not found or config error |

#### Examples

```bash
# Show theme details
sdgen theme show cyberpunk

# Theme not found
sdgen theme show unknown
# ✗ Error: Theme 'unknown' not found
```

---

### `sdgen theme validate`

Valide la compatibilité d'un theme avec un template.

#### Synopsis

```bash
sdgen theme validate <template_path> <theme_name> [--style <style>]
```

#### Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `template_path` | PATH | ✅ Yes | Path to .template.yaml file |
| `theme_name` | TEXT | ✅ Yes | Theme name to validate |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--style` | TEXT | `default` | Art style to validate |

#### Behavior

1. Load template file
2. Load theme by name
3. Check which placeholders theme provides
4. Validate completeness and report missing/provided/fallback

#### Output Format

**Compatible:**
```
✓ Theme 'cyberpunk' is compatible with template '_tpl_character'

Theme provides:
  ✓ HairCut
  ✓ HairColor
  ✓ Outfit
  ✓ Location
```

**Partial compatibility:**
```
⚠ Theme 'cyberpunk' is partially compatible

Theme provides:
  ✓ HairCut
  ✓ HairColor
  ⚠ Outfit (fallback: template default)
  ⚠ Rendering (fallback: common/rendering.yaml)

Missing from theme (will use fallbacks):
  - Outfit
  - Rendering
```

**Incompatible:**
```
✗ Theme 'cyberpunk' is NOT compatible

Missing required placeholders:
  ✗ HairCut (no fallback available)
  ✗ Location (no fallback available)
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Fully compatible or partially compatible (warnings) |
| 1 | Incompatible (missing required placeholders) |
| 2 | Template or theme not found |

#### Examples

```bash
# Validate with default style
sdgen theme validate template.yaml cyberpunk

# Validate with specific style
sdgen theme validate template.yaml cyberpunk --style cartoon

# Template not found
sdgen theme validate nonexistent.yaml cyberpunk
# ✗ Template file not found: nonexistent.yaml
```

---

## File Formats

### `template.yaml` (Themable)

Template avec support des themes (Phase 2).

#### Format

```yaml
version: "2.0"
name: "Template Name"

# 🆕 Phase 2: Theme configuration block
themes:
  enable_autodiscovery: bool          # Enable theme autodiscovery
  search_paths: [PATH, ...]           # Directories to scan (optional)
  explicit:                            # Manual theme declarations (optional)
    theme_name: path/to/theme.yaml

# Template with placeholders
template: |
  {prompt}
  {Placeholder1}, {Placeholder2}

prompts:
  default: "base prompt"

# Default imports (can be replaced by themes)
imports:
  Placeholder1: defaults/placeholder1.yaml
  Placeholder2: defaults/placeholder2.yaml

negative_prompt: "low quality"

generation:
  mode: random | combinatorial
  seed: int
  seed_mode: fixed | progressive | random
  max_images: int
```

#### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | string | Must be "2.0" |
| `name` | string | Template name |
| `template` | string | Template text with `{prompt}` placeholder |

#### Themes Block (Optional)

**Présence de `themes:` indique que le template est themable.**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enable_autodiscovery` | bool | `false` | Enable automatic theme discovery |
| `search_paths` | list[str] | `['.']` | Directories to scan for themes (relative to template) |
| `explicit` | dict[str, str] | `{}` | Manual theme name → path mappings |

#### Modes

**Mode 1: Explicit only (default)**
```yaml
themes:
  explicit:
    pirates: ./themes/pirates/theme.yaml
    cyberpunk: ../shared/cyberpunk/theme.yaml
```

**Mode 2: Autodiscovery only**
```yaml
themes:
  enable_autodiscovery: true
  search_paths: [./themes/]
```

**Mode 3: Hybrid (recommended)**
```yaml
themes:
  enable_autodiscovery: true
  search_paths: [./themes/, ../shared/]
  explicit:
    custom: ~/my-themes/custom/theme.yaml
```

---

### `theme.yaml` (Explicit Theme)

Configuration d'un theme explicite.

#### Format

```yaml
type: theme_config
version: "1.0"

imports:
  # Non-style-sensitive
  Placeholder1: theme_name/theme-placeholder1.yaml
  Placeholder2: theme_name/theme-placeholder2.yaml

  # Style-sensitive (with suffix)
  Outfit.default:   theme_name/theme-outfit.yaml
  Outfit.cartoon:   theme_name/theme-outfit.cartoon.yaml
  Outfit.realistic: theme_name/theme-outfit.realistic.yaml
```

#### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Must be "theme_config" |
| `version` | string | Theme config version (e.g., "1.0") |
| `imports` | dict[str, str] | Import mappings (placeholder → file path) |

#### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `variations` | list[str] | List of variation categories (for display) |

#### Import Keys Format

**Base placeholder:**
```yaml
HairCut: theme/theme-haircut.yaml
```

**With style suffix:**
```yaml
Outfit.cartoon: theme/theme-outfit.cartoon.yaml
Outfit.realistic: theme/theme-outfit.realistic.yaml
```

---

### Implicit Theme (No `theme.yaml`)

Theme inféré automatiquement depuis les fichiers.

#### Directory Structure

```
themes/pirates/
├── pirates-haircut.yaml
├── pirates-outfit.yaml
├── pirates-outfit.cartoon.yaml
└── pirates-location.yaml
```

#### Auto-inferred `theme.yaml`

```yaml
name: pirates
imports:
  HairCut:         pirates/pirates-haircut.yaml
  Outfit:          pirates/pirates-outfit.yaml
  Outfit.cartoon:  pirates/pirates-outfit.cartoon.yaml
  Location:        pirates/pirates-location.yaml
```

#### Inference Rules

1. **Filename convention:** `{theme}-{placeholder}.yaml`
2. **Style suffix:** `{theme}-{placeholder}.{style}.yaml`
3. **Placeholder conversion:** `outfit` → `Outfit`, `hair-color` → `HairColor`
4. **Path format:** `{theme}/{filename}`

---

### `prompt.yaml` (Using Themable Template)

Prompt qui utilise un template themable.

#### Format

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

#### Usage

```bash
# Use with different themes without changing file
sdgen generate -t prompt.yaml --theme pirates
sdgen generate -t prompt.yaml --theme cyberpunk
sdgen generate -t prompt.yaml --theme rockstar
```

---

## Naming Conventions

### Templates

| Type | Convention | Example |
|------|------------|---------|
| Themable template | `_tpl_{name}.template.yaml` | `_tpl_character.template.yaml` |
| Non-themable template | `{name}.template.yaml` | `portrait.template.yaml` |

### Themes

| Component | Convention | Example |
|-----------|------------|---------|
| Theme directory | `themes/{theme_name}/` | `themes/cyberpunk/` |
| Theme config (explicit) | `themes/{theme_name}/theme.yaml` | `themes/cyberpunk/theme.yaml` |

### Variation Files

**CRITICAL:** Respecter la convention avec **tirets** (Phase 2).

| Format | Convention | Example |
|--------|------------|---------|
| Base variation | `{theme}-{placeholder}.yaml` | `pirates-haircut.yaml` |
| With style | `{theme}-{placeholder}.{style}.yaml` | `cyberpunk-outfit.cartoon.yaml` |
| Multi-word placeholder | `{theme}-{word1}-{word2}.yaml` | `cyberpunk-tech-aspect.yaml` |

**✅ Correct:**
```
pirates-haircut.yaml
cyberpunk-outfit.cartoon.yaml
fantasy-tech-aspect.yaml
rockstar-hair-color.realistic.yaml
```

**❌ Incorrect:**
```
pirates_haircut.yaml          # Underscore instead of dash
piratesHaircut.yaml           # PascalCase
haircut-pirates.yaml          # Reversed order
pirates-haircut-cartoon.yaml  # Style with dash instead of dot
```

### Session Names

| Format | Convention | Example |
|--------|------------|---------|
| With theme + style | `YYYYMMDD_HHMMSS-SessionName-ThemeName-Style` | `20251029_143022-teasing-cyberpunk-cartoon` |
| With theme (default) | `YYYYMMDD_HHMMSS-SessionName-ThemeName-default` | `20251029_143522-teasing-pirates-default` |
| Without theme | `YYYYMMDD_HHMMSS-SessionName` | `20251029_144012-portrait` |
| Custom style (no theme) | `YYYYMMDD_HHMMSS-SessionName-Style` | `20251029_144512-character-realistic` |

**Format rules:**
- Components separated by dashes (`-`)
- Timestamp format: `YYYYMMDD_HHMMSS` (underscore for date/time separation)
- SessionName: from `generation.session_name:` or template `name:` field
- Theme always implies style (shows `default` if not specified)
- Style shown alone only if custom and no theme

---

## Configuration

### `sdgen_config.json`

Configuration globale du CLI.

#### Location

Current working directory (`./sdgen_config.json`)

#### Format

```json
{
  "configs_dir": "./prompts",
  "output_dir": "./results",
  "api_url": "http://172.29.128.1:7860"
}
```

#### Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `configs_dir` | string | ✅ Yes | - | Base directory for configs and themes |
| `output_dir` | string | ✅ Yes | - | Output directory for generated images |
| `api_url` | string | ✅ Yes | - | SD WebUI API URL |

#### Initialize

```bash
sdgen init
```

---

## Exit Codes

### Standard Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | - |
| 1 | General error | Check error message |
| 2 | Validation error | Fix config/template |
| 130 | Interrupted (Ctrl+C) | - |

### Command-Specific Exit Codes

#### `sdgen list-themes`

| Code | Meaning |
|------|---------|
| 0 | Success (themes found or template not themable) |
| 1 | Template file not found or invalid |

#### `sdgen generate --theme`

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Theme not found, no themes: block, or API error |
| 130 | Interrupted by user |

#### `sdgen theme validate`

| Code | Meaning |
|------|---------|
| 0 | Compatible (fully or partially) |
| 1 | Incompatible (missing required placeholders) |
| 2 | Template or theme not found |

---

## Environment Variables

### `SDGEN_CONFIGS_DIR`

Override the configs directory path.

```bash
export SDGEN_CONFIGS_DIR=/path/to/configs
sdgen generate -t template.yaml --theme cyberpunk
```

**Default:** `./prompts` (from `sdgen_config.json`)

### `SDGEN_OUTPUT_DIR`

Override the output directory path.

```bash
export SDGEN_OUTPUT_DIR=/path/to/output
sdgen generate -t template.yaml
```

**Default:** `./results` (from `sdgen_config.json`)

---

## Error Messages

### No themes: block found

```
❌ No 'themes:' block found in TemplateName
💡 Use --theme-file to specify theme path directly, or add a themes: block to your template
```

**Cause:** Template doesn't have `themes:` block but `--theme` was used.

**Solutions:**
1. Add `themes:` block to template
2. Use `--theme-file` instead to bypass discovery

---

### Theme not found

```
❌ Theme 'unknown' not found
💡 Available themes: pirates, cyberpunk, rockstar
   Or use --theme-file to load a custom theme
```

**Cause:** Theme name doesn't exist in discovered themes.

**Solutions:**
1. Use `sdgen list-themes -t template.yaml` to see available themes
2. Check theme name spelling
3. Use `--theme-file` for themes outside discovery paths

---

### Cannot use both --theme and --theme-file

```
✗ Cannot use both --theme and --theme-file

Use --theme for themes defined in the template, or --theme-file for custom theme files
```

**Cause:** Both options provided simultaneously.

**Solution:** Choose one:
- `--theme <name>` for themes in template's `themes:` block
- `--theme-file <path>` for direct theme file path

---

### Template not themable

```
⚠ Template 'TemplateName' is not themable
💡 Add a 'themes:' block to make it themable
```

**Cause:** Using `sdgen list-themes` on a template without `themes:` block.

**Solution:** Add `themes:` block to template:
```yaml
themes:
  enable_autodiscovery: true
  search_paths: [./themes/]
```

---

### Missing import file

```
⚠ Warning: Theme 'cyberpunk' missing Outfit.realistic, using fallback
```

**Cause:** Theme doesn't provide a required import variant.

**Behavior:** Non-blocking - system uses template default or common fallback.

**Fix (optional):** Create the missing file:
```bash
cp themes/cyberpunk/cyberpunk-outfit.yaml \
   themes/cyberpunk/cyberpunk-outfit.realistic.yaml
```

---

### File not found

```
❌ Error: File not found: themes/cyberpunk/cyberpunk-outfit.yaml
```

**Cause:** Import path in `theme.yaml` points to non-existent file.

**Solutions:**
1. Check file exists: `ls themes/cyberpunk/`
2. Verify path in `theme.yaml` is correct (relative to `configs_dir`)
3. Check filename follows convention (dash, not underscore)

---

### Invalid theme.yaml syntax

```
❌ Invalid theme.yaml: mapping values are not allowed here
```

**Cause:** YAML syntax error in `theme.yaml`.

**Solution:** Fix YAML syntax:
```bash
# Validate YAML
python3 -c "import yaml; yaml.safe_load(open('theme.yaml'))"
```

---

## See Also

- [Usage Guide](../usage/themable-templates.md) - Guide utilisateur complet
- [Technical Documentation](../technical/themable-templates.md) - Architecture interne
- [Template System V2](./template-syntax.md) - Syntaxe des templates
- [CLI Commands Reference](./cli-commands.md) - Toutes les commandes CLI
