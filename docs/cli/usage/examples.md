# CLI Usage Examples - Template System V2.0

**Common generation patterns and use cases using YAML templates.**

---

## Important Note

This document covers the **Template System V2.0** which uses YAML configuration files.

The old Python script system (`ImageVariationGenerator`) has been **completely removed** as of 2025-10-10.

All examples use `.prompt.yaml` files with the V2.0 syntax.

---

## Basic Patterns

### 1. Combinatorial Generation (Classic)

Generate all possible combinations with progressive seeds.

**File: `prompts/combinatorial_test.prompt.yaml`**

```yaml
version: '2.0'
name: 'Combinatorial Test'

imports:
  Expression: ../variations/expressions.yaml
  Angle: ../variations/angles.yaml

prompt: |
  masterpiece, {Expression}, {Angle}, beautiful girl

negative_prompt: |
  low quality, blurry

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1  # Generate all combinations

output:
  session_name: combinatorial_test
```

**Result:** All combinations with seeds 42, 43, 44, ...

---

### 2. Random Exploration

Generate random unique combinations for creative exploration.

**File: `prompts/random_exploration.prompt.yaml`**

```yaml
version: '2.0'
name: 'Random Exploration'

imports:
  Style: ../variations/styles.yaml
  Subject: ../variations/subjects.yaml
  Lighting: ../variations/lighting.yaml

prompt: |
  concept art, {Style}, {Subject}, {Lighting}

negative_prompt: |
  low quality

generation:
  mode: random
  seed_mode: random
  seed: -1
  max_images: 100

output:
  session_name: random_exploration
```

**Result:** 100 images with random combinations and random seeds.

---

### 3. Limited Variations Test

Test a subset of variations quickly using **selectors**.

**File: `prompts/limited_test.prompt.yaml`**

```yaml
version: '2.0'
name: 'Limited Test'

imports:
  Expression: ../variations/expressions.yaml  # 100 expressions available
  Angle: ../variations/angles.yaml           # 20 angles available

prompt: |
  portrait, {Expression[random:5]}, {Angle[random:3]}, beautiful

negative_prompt: |
  low quality

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1

output:
  session_name: limited_test
```

**Result:** 5 random expressions × 3 random angles = 15 images maximum.

---

### 4. Specific Index Selection

Use only specific variations that work well together.

**File: `prompts/curated_selection.prompt.yaml`**

```yaml
version: '2.0'
name: 'Curated Selection'

imports:
  Hair: ../variations/hair.yaml
  Expression: ../variations/expressions.yaml

prompt: |
  portrait, {Hair[#1,5,8]}, {Expression[#2,7]}, beautiful

negative_prompt: |
  low quality

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1

output:
  session_name: curated_selection
```

**Result:** Only combinations of specific indices (Hair: 1,5,8 × Expression: 2,7 = 6 images).

**Note:** Use `#` prefix for index selection: `[#1,5,8]`

---

## Advanced Patterns

### 5. Character Sheet with Loop Priority

Generate organized character sheets with controlled loop order using **weight selectors**.

**File: `prompts/emma_charactersheet.prompt.yaml`**

```yaml
version: '2.0'
name: 'Emma Character Sheet'

imports:
  Outfit: ../variations/outfits.yaml
  Angle: ../variations/angles.yaml
  Expression: ../variations/expressions.yaml

prompt: |
  1girl, emma watson, {Outfit[$1]}, {Angle[$10]}, {Expression[$20]}, high quality

negative_prompt: |
  low quality, blurry, bad anatomy

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1

output:
  session_name: emma_charactersheet
  filename_keys:
    - Outfit
    - Angle
    - Expression
```

**Loop order:**
1. Outer loop: Outfit (weight 1 - lowest, changes least often)
2. Middle loop: Angle (weight 10)
3. Inner loop: Expression (weight 20 - highest, changes most often)

**Result:** All expressions and angles for each outfit, organized in blocks.

**Filenames:** `001_Outfit-Dress_Angle-Front_Expression-Smiling.png`

**Important:** Weights control loop nesting order - **lower weight = outer loop**.

---

### 6. Excluding Placeholders from Combinatorial Loop

Use **weight 0** to exclude a placeholder from combinatorial loop and pick randomly per image.

**File: `prompts/random_quality.prompt.yaml`**

```yaml
version: '2.0'
name: 'Random Quality Tags'

imports:
  Outfit: ../variations/outfits.yaml      # 5 variations
  Angle: ../variations/angles.yaml        # 3 variations
  Quality: ../variations/quality_tags.yaml # 10 variations

prompt: |
  1girl, {Outfit}, {Angle}, {Quality[$0]}, detailed

negative_prompt: |
  low quality

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1

output:
  session_name: random_quality
```

**Behavior:**
- Outfit × Angle = 15 combinations (combinatorial)
- Quality is picked **randomly for each of the 15 images** (weight 0)

**Result:** 15 images with all Outfit×Angle combos, but Quality varies randomly.

---

### 7. A/B Testing

Compare results with and without specific elements using the same seed.

**Base configuration file: `templates/ab_test_base.template.yaml`**

```yaml
version: '2.0'
name: 'A/B Test Base'

imports:
  Hair: ../variations/hair.yaml
  Expression: ../variations/expressions.yaml
  Lighting: ../variations/lighting.yaml

parameters:
  width: 512
  height: 768
  steps: 30
  cfg_scale: 7.0
  sampler: DPM++ 2M Karras

generation:
  mode: combinatorial
  seed_mode: fixed
  seed: 42
  max_images: -1
```

**Test WITH lighting: `prompts/ab_test_with_lighting.prompt.yaml`**

```yaml
version: '2.0'
name: 'A/B Test - With Lighting'
implements: ../templates/ab_test_base.template.yaml

prompt: |
  portrait, {Hair[#1,5,8]}, {Expression[#2,7]}, {Lighting}, beautiful

negative_prompt: |
  low quality

output:
  session_name: test_with_lighting
  filename_keys:
    - Hair
    - Expression
```

**Test WITHOUT lighting: `prompts/ab_test_without_lighting.prompt.yaml`**

```yaml
version: '2.0'
name: 'A/B Test - Without Lighting'
implements: ../templates/ab_test_base.template.yaml

prompt: |
  portrait, {Hair[#1,5,8]}, {Expression[#2,7]}, beautiful

negative_prompt: |
  low quality

output:
  session_name: test_without_lighting
  filename_keys:
    - Hair
    - Expression
```

**Result:** Same compositions (same seed) with and without lighting, easy comparison.

**Note:** No need to use `{Lighting[$0]}` or `:0` syntax - just remove the placeholder entirely.

---

### 8. Progressive Refinement Workflow

Start broad, then narrow down to best results.

**Phase 1 - Exploration: `prompts/exploration_phase1.prompt.yaml`**

```yaml
version: '2.0'
name: 'Exploration Phase 1'

imports:
  Hair: ../variations/hair.yaml
  Expression: ../variations/expressions.yaml
  Pose: ../variations/poses.yaml

prompt: |
  {Hair}, {Expression}, {Pose}

negative_prompt: |
  low quality

generation:
  mode: random
  seed_mode: random
  seed: -1
  max_images: 50

output:
  session_name: exploration_phase1
```

**Phase 2 - Refined: `prompts/refined_phase2.prompt.yaml`**

After reviewing phase 1 results, you identify best combinations:
- Hair indices: 1, 5, 8
- Expression indices: 2, 7, 15
- Pose indices: 0, 3

```yaml
version: '2.0'
name: 'Refined Phase 2'

imports:
  Hair: ../variations/hair.yaml
  Expression: ../variations/expressions.yaml
  Pose: ../variations/poses.yaml

prompt: |
  {Hair[#1,5,8]}, {Expression[#2,7,15]}, {Pose[#0,3]}

negative_prompt: |
  low quality

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1

output:
  session_name: refined_phase2
  filename_keys:
    - Hair
    - Expression
    - Pose
```

**Result Phase 1:** 50 random images for exploration.

**Result Phase 2:** 3 hair × 3 expression × 2 pose = 18 precise images.

---

### 9. Multiple Variation Files per Placeholder

Organize variations by category, merge them automatically.

**File: `prompts/multi_file_test.prompt.yaml`**

```yaml
version: '2.0'
name: 'Multi-File Test'

imports:
  Pose:
    - ../variations/poses/standing.yaml
    - ../variations/poses/sitting.yaml
    - ../variations/poses/action.yaml

prompt: |
  1girl, {Pose}, outdoor scene, dynamic

negative_prompt: |
  low quality

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1

output:
  session_name: multi_file_test
```

**Result:** All variations from all 3 files merged into `{Pose}` placeholder.

The CLI will show:
```
Detected Variations:
  Pose: 45 variations (3 files merged)
```

---

### 10. Using Template Inheritance for Reusability

Define reusable base templates with `implements:`.

**Base template: `templates/preset_character_sheet.template.yaml`**

```yaml
version: '2.0'
name: 'Character Sheet Preset'

parameters:
  width: 512
  height: 768
  steps: 24
  cfg_scale: 7.0
  sampler: DPM++ 2M Karras

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
  max_images: -1

output:
  filename_keys:
    - Outfit
    - Angle
    - Expression
```

**Prompt using preset: `prompts/character_test_v3.prompt.yaml`**

```yaml
version: '2.0'
name: 'Character Test V3'
implements: ../templates/preset_character_sheet.template.yaml

imports:
  Outfit: ../variations/outfits.yaml
  Angle: ../variations/angles.yaml
  Expression: ../variations/expressions.yaml

prompt: |
  1girl, {Outfit[$1]}, {Angle[$10]}, {Expression[$20]}

negative_prompt: |
  low quality

output:
  session_name: character_test_v3
```

**Inheritance behavior:**
- **Parameters** are merged (child overrides parent)
- **Imports** are merged (child adds to parent)
- **Template/prompt** in child **replaces** parent template
- **Generation** and **output** configs can be overridden

---

## Selector Syntax Reference

### Syntax Summary

| Syntax | Effect | Example |
|--------|--------|---------|
| `{Name}` | All variations | `{Hair}` |
| `{Name[random:N]}` | N random variations | `{Hair[random:5]}` |
| `{Name[#i,j,k]}` | Specific indices (note the `#`) | `{Hair[#1,5,22]}` |
| `{Name[key1,key2]}` | Specific keys | `{Hair[BobCut,LongHair]}` |
| `{Name[$W]}` | Weight W for loop order | `{Hair[$3]}` |
| `{Name[random:N;$W]}` | Combine selectors with `;` | `{Hair[random:10;$5]}` |

### Important Syntax Notes

1. **Index selector requires `#` prefix**: `{Name[#1,5,8]}` not `{Name[1,5,8]}`
2. **Weight selector uses `$`**: `{Name[$5]}` not `{Name:$5}` or `{Name:5}`
3. **Combine with semicolon**: `{Name[random:10;$3]}` not `{Name[random:10,$3]}`
4. **All selectors go in brackets `[]`**: Never use `:` outside brackets

### Examples of Correct Syntax

```yaml
prompt: |
  # ✅ Correct - all variations
  {Expression}

  # ✅ Correct - 5 random variations
  {Expression[random:5]}

  # ✅ Correct - specific indices with # prefix
  {Expression[#0,2,4,7]}

  # ✅ Correct - specific named keys
  {Expression[happy,sad,angry]}

  # ✅ Correct - weight 0 (exclude from combinatorial)
  {Quality[$0]}

  # ✅ Correct - weight 10 for loop ordering
  {Angle[$10]}

  # ✅ Correct - combination of selectors
  {Expression[random:10;$5]}
```

### Examples of WRONG Syntax

```yaml
prompt: |
  # ❌ WRONG - using : instead of []
  {Expression:5}

  # ❌ WRONG - using :$ instead of [$]
  {Outfit:$0}

  # ❌ WRONG - missing # for index selector
  {Hair[1,5,8]}

  # ❌ WRONG - using comma instead of semicolon
  {Hair[random:10,$5]}
```

---

## Generation Mode Cheatsheet

| Use Case | Generation Mode | Seed Mode | Max Images |
|----------|----------------|-----------|------------|
| All combinations | `combinatorial` | `progressive` | `-1` (all) |
| Same seed, all combos | `combinatorial` | `fixed` | `-1` |
| Random exploration | `random` | `random` | `100` |
| Controlled random | `random` | `progressive` | `50` |
| Quick test | `combinatorial` | `fixed` | `5` |

---

## Seed Mode Cheatsheet

| Mode | Behavior | Use Case |
|------|----------|----------|
| `fixed` | Same seed for all | Compare variations with identical composition |
| `progressive` | Seeds 42, 43, 44... | Reproducible but different compositions |
| `random` | Random seed (-1) | Maximum diversity |

---

## Weight System for Loop Ordering

Weights control the nesting order of combinatorial loops:

- **Lower weight = outer loop** (changes less often)
- **Higher weight = inner loop** (changes more often)
- **Weight 0 = excluded from loops** (random per image)

### Example

```yaml
prompt: |
  {Outfit[$1]}, {Angle[$10]}, {Expression[$20]}
```

**Loop structure:**
```
for outfit in Outfits:      # Weight 1 (outer)
  for angle in Angles:      # Weight 10 (middle)
    for expression in Expressions:  # Weight 20 (inner)
      generate_image()
```

**Result:** All expressions for each angle, all angles for each outfit.

---

## Learn More

- **[Getting Started](getting-started.md)** - First generation tutorial
- **[YAML Templating Guide](yaml-templating-guide.md)** - Complete V2.0 guide with examples
- **[Variation Files](variation-files.md)** - Complete variation file format reference

---

**Last updated:** 2025-10-13
**System version:** V2.0 (Python script system removed)
