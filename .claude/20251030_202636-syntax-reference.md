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

### Simple Variations (String Values)

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

### Multi-Part Variations (Dict Values) - **NEW in v2.1**

**Purpose:** Variations with multiple named parts for advanced positioning control.

**Primary use case:** LoRA tags that must appear at specific positions.

**Structure:**
```yaml
type: variations
version: "1.0"
name: HairStyles
variations:
  short_bob:
    main: short bob cut, brown hair
    lora: <lora:hair_short_bob:0.7>
  long_waves:
    main: long wavy hair, blonde
    lora: <lora:hair_long_waves:0.8>
```

**Key rules:**
- Keys are variation IDs (used in selectors)
- Simple variations: values are strings
- Multi-part variations: values are dicts with named parts
  - Common parts: `main`, `lora`, `negative`
  - Part names are arbitrary (you define them)
- Can mix simple and multi-part in same file
- All part values MUST be strings
- Can be referenced in `imports:`

**Usage:**
```yaml
# In prompt.yaml
prompt: "{Hair:main}, detailed portrait, {Hair:lora}"
```

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
{PlaceholderName}                # Simple variation OR auto-resolve to "main" part
```

### With selectors:
```
{PlaceholderName[random:5]}      # Random 5 variations
{PlaceholderName[limit:10]}      # Limit to first 10
{PlaceholderName[indexes:1,5,8]} # Specific indexes
{PlaceholderName[keys:foo,bar]}  # Specific keys
```

### Sub-placeholders (Multi-Part Variations) - **NEW in v2.1**:
```
{PlaceholderName:part}           # Access specific part of multi-part variation
{Hair:main}                      # Main prompt text
{Hair:lora}                      # LoRA tag
{Hair:negative}                  # Negative prompt addition
```

### Auto-resolve behavior:
- `{Hair}` on multi-part variation → uses "main" part (or first alphabetically if no "main")
- `{Hair}` on simple variation → uses the string value directly

### Important rules:

⚠️ **Selectors and sub-placeholders are MUTUALLY EXCLUSIVE**
- ✅ Valid: `{Hair[random:3]}`           (selector on complete placeholder)
- ✅ Valid: `{Hair:lora}`                 (sub-placeholder without selector)
- ❌ **INVALID:** `{Hair[random:3]:lora}` (selector + sub-placeholder = PARSE ERROR)

**Why this restriction?**
Selectors operate on the list of variations, while sub-placeholders operate on a specific variation's parts. Combining them would create ambiguous semantics.

**Correct usage for selective multi-part:**
```yaml
# If you need to select AND access parts, use separate placeholders:
prompt: "{Hair:main}, {Hair:lora}"  # Both use same selected variation
imports:
  Hair: hair.yaml  # Will be resolved together in generation
```

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

### Multi-Part Variations with LoRA Positioning - **NEW v2.1**:
```yaml
# hair.yaml (multi-part variation file)
short_bob:
  main: short bob cut, brown hair
  lora: <lora:hair_short_bob:0.7>
  negative: long hair, wavy hair

long_waves:
  main: long wavy hair, blonde
  lora: <lora:hair_long_waves:0.8>
  negative: short hair, straight hair

# character.prompt.yaml
type: prompt
version: "2.0"
name: character
implements: base.template.yaml
prompt: "woman, {Hair:main}, detailed portrait"
negative_prompt: "low quality, {Hair:negative}"
imports:
  Hair: hair.yaml
parameters:
  # LoRA tags go at END of positive prompt (SD WebUI convention)
  # Use chunks or manual concatenation
  # NOTE: Phase 2 will add {loras} placeholder for automatic positioning
generation:
  mode: combinatorial
  seed_mode: fixed
  seed: 42
  max_images: 10
```

**Use Cases:**
- LoRA tags positioned at prompt end (SD WebUI convention)
- Negative prompt additions tied to specific variations
- Multiple positioning requirements (future: {loras}, {negatives} placeholders)

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
