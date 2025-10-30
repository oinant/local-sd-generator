# Template System V2.0 - Syntax Reference

Quick reference for file formats in the Template System V2.0.

## 1. Template Files (`.template.yaml`)

**Purpose:** Base templates with `{prompt}` placeholder for inheritance.

**Must have:**
- `template` field with `{prompt}` placeholder
- NO `type` field
- NO `generation` field

**Structure:**
```yaml
version: "2.0"
name: base_template
template: "masterpiece, {prompt}, detailed"
negative_prompt: "low quality, blurry"
parameters:
  steps: 30
  cfg_scale: 7.5
```

**Key rules:**
- MUST contain `{prompt}` placeholder
- Used as parent for prompts via `implements:`
- Cannot be executed directly (no generation config)

---

## 2. Prompt Files (`.prompt.yaml`)

**Purpose:** Executable prompts that implement templates (child configs).

**Must have:**
- `type: prompt`
- `generation` block with mode/seed/max_images
- `prompt` field (injected into parent's `{prompt}`)
- `implements:` pointing to parent template

**Structure:**
```yaml
type: prompt
version: "2.0"
name: my_character
themable: true
implements: base.template.yaml
prompt: "beautiful woman, {HairStyle}, {Outfit}"
imports:
  HairStyle: defaults/hairstyles.yaml
  Outfit: defaults/outfits.yaml
generation:
  mode: combinatorial  # or random
  seed_mode: fixed     # fixed, progressive, random
  seed: 42
  max_images: 100
```

**Key rules:**
- `type: prompt` is REQUIRED
- `generation` block is REQUIRED
- Inherits `template` from parent
- `prompt` is injected into parent's `{prompt}`

**Optional blocks:**
- `themes:` - for theme support
- `style_sensitive_placeholders:` - for style-aware imports
- `parameters:` - override parent parameters

---

## 3. Chunk Files (`.chunk.yaml`)

**Purpose:** Reusable template fragments.

**Must have:**
- `type: chunk` (or extension `.chunk.yaml`)
- `template` field (can use placeholders but NOT `{prompt}`)

**Structure:**
```yaml
type: chunk
version: "2.0"
name: lighting_chunk
template: "{LightingType}, {LightingIntensity}"
imports:
  LightingType: chunks/lighting_types.yaml
  LightingIntensity: chunks/lighting_intensity.yaml
defaults:
  LightingType: soft_lighting
  LightingIntensity: moderate
```

**Key rules:**
- CANNOT use `{prompt}` placeholder (reserved for templates)
- Can be imported into templates or other chunks
- Can have own imports and defaults

---

## 4. Variation Files (`.yaml` or `.variations.yaml`)

**Purpose:** Key-value mappings for placeholder substitution.

**Structure:**
```yaml
type: variations
version: "1.0"
name: HairStyles
variations:
  short_bob: short bob cut
  long_waves: long wavy hair
  pixie_cut: pixie cut haircut
```

**Alternative format (legacy):**
```
short_bob: short bob cut
long_waves: long wavy hair
pixie_cut: pixie cut haircut
```

**Key rules:**
- Keys are variation IDs (used in selectors)
- Values are substituted into placeholders
- Can be referenced in `imports:`

---

## 5. Theme Files (`theme.yaml`)

**Purpose:** Theme-specific variation overrides with style support.

**Location:** `configs_dir/themes/{theme_name}/theme.yaml`

**Structure:**
```yaml
type: theme_config
version: "1.0"
imports:
  # Regular imports (no style suffix)
  HairStyle: cyberpunk/hairstyles.yaml
  Outfit: cyberpunk/outfits.yaml

  # Style-specific imports (with .style suffix)
  Outfit.safe: cyberpunk/outfits.safe.yaml
  Outfit.spicy: cyberpunk/outfits.spicy.yaml
  Outfit.restricted: cyberpunk/outfits.restricted.yaml

  # Remove directive (removes placeholder for specific style)
  Jewelry.restricted: [Remove]

variations:
  - HairStyle
  - Outfit
```

**Key rules:**
- Imports are relative to `configs_dir`
- Style notation: `PlaceholderName.style` (dot separator)
- `[Remove]` directive: MUST be exactly `[Remove]` (case-sensitive), single-element list
- Theme imports COMPLETELY REPLACE template imports (not merge)

**Style resolution:**
- Default style uses imports without suffix
- Specific style uses `PlaceholderName.{style}` if exists, else falls back to default
- `[Remove]` directive removes placeholder entirely for that style

---

## 6. Placeholder Syntax

### Basic placeholder:
```
{PlaceholderName}
```

### With selectors:
```
{PlaceholderName[random:5]}      # Random 5 variations
{PlaceholderName[limit:10]}      # Limit to first 10
{PlaceholderName[indexes:1,5,8]} # Specific indexes
{PlaceholderName[keys:foo,bar]}  # Specific keys
```

### Important selector rule:
⚠️ **Selectors only apply to COMPLETE placeholders, NOT sub-placeholders**
- ✅ Valid: `{Hair[random:3]}`
- ❌ Invalid: `{Hair[random:3]:lora}`

---

## 7. File Type Detection Logic

```python
if 'generation' in data:
    return PromptConfig  # .prompt.yaml
elif 'type' in data:
    return ChunkConfig   # .chunk.yaml
else:
    return TemplateConfig  # .template.yaml
```

**Key:**
- Presence of `generation` → Prompt
- Presence of `type` → Chunk
- Otherwise → Template

---

## 8. Common Patterns

### Parent Template + Child Prompt:
```yaml
# base.template.yaml (NO type field!)
version: "2.0"
name: base
template: "masterpiece, {prompt}, detailed"

# character.prompt.yaml
type: prompt
version: "2.0"
name: character
implements: base.template.yaml
prompt: "woman, {Hair}"
imports:
  Hair: hair.yaml
generation:
  mode: combinatorial
  seed_mode: fixed
  seed: 42
  max_images: 10
```

### Themable Prompt:
```yaml
type: prompt
version: "2.0"
name: character
themable: true
implements: base.template.yaml
prompt: "woman, {Hair}, {Outfit}"
imports:
  Hair: defaults/hair.yaml
  Outfit: defaults/outfit.yaml
themes:
  enable_autodiscovery: true
  search_paths: ["."]
generation:
  mode: random
  seed_mode: random
  seed: -1
  max_images: 50
```

### Theme with [Remove] Directive:
```yaml
type: theme_config
version: "1.0"
imports:
  Hair: theme/hair.yaml
  Outfit: theme/outfit.yaml
  Jewelry: theme/jewelry.yaml
  Jewelry.restricted: [Remove]  # Remove jewelry for restricted style
```

---

## 9. Validation Rules

### [Remove] Directive:
- ✅ Valid: `[Remove]` (exactly, case-sensitive)
- ❌ Invalid: `[remove]`, `["Remove"]`, `[]`, `["Remove", "extra"]`

### Template {prompt}:
- Template files MUST contain `{prompt}`
- Chunk files CANNOT contain `{prompt}`

### Generation Config:
- Prompts MUST have `generation` block
- Templates/chunks CANNOT have `generation` block

---

## 10. Style System

**Style notation:** Use dot separator
- Theme file: `PlaceholderName.style` → `Outfit.safe`, `Outfit.restricted`
- Style parameter: `--style safe`, `--style restricted`

**Resolution order:**
1. Check for `PlaceholderName.{style}` in theme
2. If `[Remove]` → remove placeholder entirely
3. If file path → load that file
4. Else fallback to `PlaceholderName` (default)

**Example:**
```yaml
# theme.yaml
imports:
  Outfit: theme/outfit.yaml          # default
  Outfit.safe: theme/outfit.safe.yaml   # safe style variant
  Outfit.restricted: [Remove]           # removed in restricted style
```

When `--style restricted`:
- `Outfit` placeholder is removed entirely (resolves to empty string)

When `--style safe`:
- `Outfit` uses `theme/outfit.safe.yaml`

When `--style default` (or no style):
- `Outfit` uses `theme/outfit.yaml`

---

## Quick Checklist

Before creating test files:

- [ ] Template file: NO `type`, HAS `{prompt}`, NO `generation`
- [ ] Prompt file: `type: prompt`, HAS `generation`, HAS `max_images`
- [ ] Chunk file: `type: chunk`, NO `{prompt}`
- [ ] Theme file: imports relative to `configs_dir`, style uses dots
- [ ] `[Remove]` directive: exactly `[Remove]`, case-sensitive, single element
