# CLI Usage Examples

**Common generation patterns and use cases.**

---

## Basic Patterns

### 1. Combinatorial Generation (Classic)

Generate all possible combinations with progressive seeds.

```python
from CLI.image_variation_generator import ImageVariationGenerator

generator = ImageVariationGenerator(
    prompt_template="masterpiece, {Expression}, {Angle}, beautiful girl",
    negative_prompt="low quality, blurry",
    variation_files={
        "Expression": "variations/expressions.txt",
        "Angle": "variations/angles.txt"
    },
    generation_mode="combinatorial",
    seed_mode="progressive",
    seed=42,
    session_name="combinatorial_test"
)

generator.run()
```

**Result:** All combinations with seeds 42, 43, 44, ...

---

### 2. Random Exploration

Generate random unique combinations for creative exploration.

```python
generator = ImageVariationGenerator(
    prompt_template="concept art, {Style}, {Subject}, {Lighting}",
    negative_prompt="low quality",
    variation_files={
        "Style": "variations/styles.txt",
        "Subject": "variations/subjects.txt",
        "Lighting": "variations/lighting.txt"
    },
    generation_mode="random",
    seed_mode="random",
    max_images=100,
    seed=-1,
    session_name="random_exploration"
)

generator.run()
```

**Result:** 100 images with random combinations and random seeds.

---

### 3. Limited Variations Test

Test a subset of variations quickly.

```python
generator = ImageVariationGenerator(
    prompt_template="portrait, {Expression:5}, {Angle:3}, beautiful",
    negative_prompt="low quality",
    variation_files={
        "Expression": "variations/expressions.txt",
        "Angle": "variations/angles.txt"
    },
    generation_mode="combinatorial",
    seed_mode="progressive",
    seed=42,
    session_name="limited_test"
)

generator.run()
```

**Result:** 5 random expressions × 3 random angles = 15 images maximum.

---

### 4. Specific Index Selection

Use only specific variations that work well together.

```python
generator = ImageVariationGenerator(
    prompt_template="portrait, {Hair:#|1|5|8}, {Expression:#|2|7}, beautiful",
    negative_prompt="low quality",
    variation_files={
        "Hair": "variations/hair.txt",
        "Expression": "variations/expressions.txt"
    },
    generation_mode="combinatorial",
    seed_mode="progressive",
    seed=42,
    session_name="curated_selection"
)

generator.run()
```

**Result:** Only combinations of specific indices (Hair: 1,5,8 × Expression: 2,7 = 6 images).

---

## Advanced Patterns

### 5. Character Sheet with Loop Priority

Generate organized character sheets with controlled loop order.

```python
generator = ImageVariationGenerator(
    prompt_template="1girl, emma watson, {Outfit:$1}, {Angle:$10}, {Expression:$20}, high quality",
    negative_prompt="low quality, blurry, bad anatomy",
    variation_files={
        "Outfit": "variations/outfits.txt",
        "Angle": "variations/angles.txt",
        "Expression": "variations/expressions.txt"
    },
    generation_mode="combinatorial",
    seed_mode="progressive",
    seed=42,
    session_name="emma_charactersheet",
    filename_keys=["Outfit", "Angle", "Expression"]
)

generator.run()
```

**Loop order:**
1. Outer loop: Outfit (priority 1)
2. Middle loop: Angle (priority 10)
3. Inner loop: Expression (priority 20)

**Result:** All expressions and angles for each outfit, organized in blocks.

**Filenames:** `001_Outfit-Dress_Angle-Front_Expression-Smiling.png`

---

### 6. A/B Testing

Compare results with and without specific elements using the same seed.

```python
# Configuration commune
base_config = {
    "prompt_template": "portrait, {Hair:#|1|5|8}, {Expression:#|2|7}, {Lighting}, beautiful",
    "negative_prompt": "low quality",
    "generation_mode": "combinatorial",
    "seed_mode": "fixed",
    "seed": 42,
    "filename_keys": ["Hair", "Expression"]
}

# Test WITH lighting
generator_with = ImageVariationGenerator(
    **base_config,
    variation_files={
        "Hair": "variations/hair.txt",
        "Expression": "variations/expressions.txt",
        "Lighting": "variations/lighting.txt"
    },
    session_name="test_with_lighting"
)
generator_with.run()

# Test WITHOUT lighting (placeholder suppressed)
base_config["prompt_template"] = "portrait, {Hair:#|1|5|8}, {Expression:#|2|7}, {Lighting:0}, beautiful"
generator_without = ImageVariationGenerator(
    **base_config,
    variation_files={
        "Hair": "variations/hair.txt",
        "Expression": "variations/expressions.txt",
        "Lighting": "variations/lighting.txt"  # File loaded but not used due to :0
    },
    session_name="test_without_lighting"
)
generator_without.run()
```

**Result:** Same compositions (same seed) with and without lighting, easy comparison.

---

### 7. Progressive Refinement Workflow

Start broad, then narrow down to best results.

```python
# PHASE 1: Broad exploration
generator_explore = ImageVariationGenerator(
    prompt_template="{Hair}, {Expression}, {Pose}",
    negative_prompt="low quality",
    variation_files={
        "Hair": "variations/hair.txt",
        "Expression": "variations/expressions.txt",
        "Pose": "variations/poses.txt"
    },
    generation_mode="random",
    seed_mode="random",
    max_images=50,
    seed=-1,
    session_name="exploration_phase1"
)
generator_explore.run()

# → Review results, identify best combinations
# → Example: Hair index 1,5,8 work well, Expression 2,7,15, Pose 0,3

# PHASE 2: Refined generation with specific indices
generator_refined = ImageVariationGenerator(
    prompt_template="{Hair:#|1|5|8}, {Expression:#|2|7|15}, {Pose:#|0|3}",
    negative_prompt="low quality",
    variation_files={
        "Hair": "variations/hair.txt",
        "Expression": "variations/expressions.txt",
        "Pose": "variations/poses.txt"
    },
    generation_mode="combinatorial",
    seed_mode="progressive",
    seed=42,
    session_name="refined_phase2",
    filename_keys=["Hair", "Expression", "Pose"]
)
generator_refined.run()
```

**Result Phase 1:** 50 random images for exploration.

**Result Phase 2:** 3 hair × 3 expression × 2 pose = 18 precise images.

---

### 8. Multiple Variation Files per Placeholder

Organize variations by category, merge them automatically.

```python
generator = ImageVariationGenerator(
    prompt_template="1girl, {Pose}, outdoor scene, dynamic",
    negative_prompt="low quality",
    variation_files={
        "Pose": [
            "variations/poses/standing.txt",
            "variations/poses/sitting.txt",
            "variations/poses/action.txt"
        ]
    },
    generation_mode="combinatorial",
    seed_mode="progressive",
    seed=42,
    session_name="multi_file_test"
)

generator.run()
```

**Result:** All variations from all 3 files merged into `{Pose}` placeholder.

---

### 9. Nested Variations in Files

Use inline variations within variation files for combinatorial expansion.

**File `variations/action_poses.txt`:**
```
running,{|looking back|arms pumping}
jumping,{|legs bent},{|arms up|reaching}
fighting stance,{|fists raised},{|defensive|aggressive}
dancing,{|spinning},{|arms extended|graceful pose}
```

**Script:**
```python
generator = ImageVariationGenerator(
    prompt_template="1girl, {Pose}, outdoor scene, dynamic",
    negative_prompt="low quality",
    variation_files={
        "Pose": "variations/action_poses.txt"
    },
    generation_mode="combinatorial",
    seed_mode="progressive",
    seed=42,
    session_name="nested_variations"
)

generator.run()
```

**Expanded variations:**
- `running` → 3 variations (base, +looking back, +arms pumping)
- `jumping` → 6 variations (2×3 combinations)
- `fighting stance` → 6 variations
- `dancing` → 6 variations

**Total:** 21 variations from 4 lines!

---

### 10. Using Presets for Reusability

Define reusable configuration presets.

```python
# Define presets
PRESET_CHARACTER_SHEET = {
    "generation_mode": "combinatorial",
    "seed_mode": "progressive",
    "seed": 42,
    "filename_keys": ["Outfit", "Angle", "Expression"]
}

PRESET_CREATIVE_EXPLORATION = {
    "generation_mode": "random",
    "seed_mode": "random",
    "max_images": 100,
    "seed": -1
}

PRESET_QUICK_TEST = {
    "generation_mode": "combinatorial",
    "seed_mode": "fixed",
    "seed": 42
}

# Use preset
generator = ImageVariationGenerator(
    prompt_template="1girl, {Outfit:$1}, {Angle:$10}, {Expression:$20}",
    negative_prompt="low quality",
    variation_files={
        "Outfit": "variations/outfits.txt",
        "Angle": "variations/angles.txt",
        "Expression": "variations/expressions.txt"
    },
    **PRESET_CHARACTER_SHEET,
    session_name="character_test_v3"
)

generator.run()
```

---

## Generation Mode Cheatsheet

| Use Case | Generation Mode | Seed Mode | Max Images |
|----------|----------------|-----------|------------|
| All combinations | `combinatorial` | `progressive` | `-1` (all) |
| Same seed, all combos | `combinatorial` | `fixed` | `-1` |
| Random exploration | `random` | `random` | `100` |
| Controlled random | `random` | `progressive` | `50` |
| Quick test | `combinatorial` | `fixed` | N/A |

---

## Seed Mode Cheatsheet

| Mode | Behavior | Use Case |
|------|----------|----------|
| `fixed` | Same seed for all | Compare variations with identical composition |
| `progressive` | Seeds 42, 43, 44... | Reproducible but different compositions |
| `random` | Random seed (-1) | Maximum diversity |

---

## Placeholder Syntax Cheatsheet

| Syntax | Effect | Example |
|--------|--------|---------|
| `{Name}` | All variations | `{Hair}` |
| `{Name:N}` | N random variations | `{Hair:5}` |
| `{Name:0}` | Suppress placeholder | `{Hair:0}` |
| `{Name:#\|1\|5}` | Specific indices | `{Hair:#\|1\|5\|22}` |
| `{Name:$P}` | Priority P | `{Hair:$3}` |
| `{Name:N$P}` | Limit + priority | `{Hair:10$5}` |

---

## Learn More

- **[Getting Started](getting-started.md)** - First generation tutorial
- **[JSON Config System](json-config-system.md)** - Use JSON instead of Python
- **[Variation Files](variation-files.md)** - Complete placeholder syntax reference

---

**Last updated:** 2025-10-01
