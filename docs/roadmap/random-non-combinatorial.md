# Random Non-Combinatorial Placeholders

**Status:** 🔮 Future
**Priority:** High
**Complexity:** Medium
**Estimated Effort:** 3-4 days

---

## Overview

Add support for placeholders that select random values independently for each combination, without affecting the overall combinatorial structure.

### The Problem

Currently, all placeholders participate in combinatorial expansion:

```python
prompt = "{Outfit}, {Angle}, {Background}"
# 5 outfits × 3 angles × 10 backgrounds = 150 combinations
```

**Issue:** Sometimes you want the `Background` to vary randomly for each `(Outfit, Angle)` pair, without expanding the total combinations.

**Desired:**
```
5 outfits × 3 angles = 15 combinations
For each combination, randomly pick a Background
Result: 15 images, each with a different random background
```

### Current Workaround

Generate multiple times with `{Background:1}` (limit to 1 random):

```python
# Run 1: seed=42
prompt = "{Outfit}, {Angle}, {Background:1}"
# 15 images with one random background per combo

# Run 2: seed=43
# 15 images with different random backgrounds
```

**Problems:**
- Requires multiple runs
- Can't control which backgrounds appear
- No single-run diversity

---

## Goals

1. **Independent Randomization**: Placeholders that randomize per combination
2. **Combinatorial Control**: Choose which placeholders expand combinations
3. **Reproducibility**: Seed controls random selections
4. **Flexibility**: Mix combinatorial and random placeholders

---

## Non-Goals

1. ❌ Weighted random selection (equal probability only)
2. ❌ Per-image unique randomization (reproducibility required)
3. ❌ Complex constraints between random placeholders

---

## Use Cases

### 1. Background Diversity

Generate character sheets with varying backgrounds:

```json
{
  "prompt": {
    "template": "1girl, {Outfit:$1}, {Angle:$10}, {Expression:$20}, {Background:@}"
  },
  "variations": {
    "Outfit": "/path/to/outfits.txt",
    "Angle": "/path/to/angles.txt",
    "Expression": "/path/to/expressions.txt",
    "Background": "/path/to/backgrounds.txt"
  }
}
```

**Behavior:**
- 5 outfits × 3 angles × 10 expressions = 150 combinations
- For each combination, randomly select one background
- Result: 150 images with diverse backgrounds

**Benefit:** Visual variety without combinatorial explosion.

### 2. Quality/Style Randomization

Add random quality tags without expanding combinations:

```json
{
  "prompt": {
    "template": "portrait, {Expression}, {Angle}, {QualityTag:@}"
  },
  "variations": {
    "Expression": ["smiling", "serious", "thoughtful"],
    "Angle": ["front", "side", "3/4"],
    "QualityTag": ["masterpiece", "best quality", "high quality", "ultra detailed"]
  }
}
```

**Result:** 3 × 3 = 9 images, each with random quality tag.

### 3. Lighting Variation

Test different lighting without full combinatorial:

```json
{
  "prompt": {
    "template": "{Character}, {Pose}, {Lighting:@}"
  },
  "variations": {
    "Character": "/path/to/characters.txt",
    "Pose": "/path/to/poses.txt",
    "Lighting": "/path/to/lighting.txt"
  }
}
```

**Without `@`:** 10 characters × 20 poses × 15 lighting = 3000 images
**With `@`:** 10 characters × 20 poses = 200 images (each with random lighting)

**Benefit:** 93% fewer images while maintaining variety.

### 4. Detail Randomization

Add random details without affecting core combinations:

```json
{
  "prompt": {
    "template": "anime girl, {Outfit}, {Expression}, {Detail:@}, {Detail:@}"
  },
  "variations": {
    "Outfit": ["dress", "shirt", "kimono"],
    "Expression": ["smiling", "serious"],
    "Detail": ["jewelry", "tattoo", "scar", "freckles", "mole", "glasses"]
  }
}
```

**Result:** 3 × 2 = 6 images, each with 2 random details.

---

## Proposed Syntax

### Marker: `@` (Random/Stochastic)

```
{PlaceholderName:@}
```

**Behavior:**
- Does NOT expand combinations
- Randomly selects one value for each combination
- Selection is seeded (reproducible)

### Compatible with Other Options

```
{PlaceholderName:N@}        # Pick from N random values
{PlaceholderName:#|1|5|8@}  # Pick randomly from indices 1, 5, 8
{PlaceholderName:@$5}       # Random + priority (priority ignored in random mode)
```

### Multiple Instances

Using the same placeholder multiple times with `@` picks independently:

```python
prompt = "{Detail:@}, {Detail:@}"
# Two different random details (can be the same by chance)
```

---

## Technical Design

### Combination Generation

**Current (all combinatorial):**
```python
placeholders = {
    "Outfit": ["dress", "shirt"],
    "Angle": ["front", "side"]
}

combinations = list(itertools.product(
    placeholders["Outfit"],
    placeholders["Angle"]
))
# Result: [("dress","front"), ("dress","side"), ("shirt","front"), ("shirt","side")]
```

**New (mixed):**
```python
placeholders = {
    "Outfit": ["dress", "shirt"],          # combinatorial
    "Angle": ["front", "side"],            # combinatorial
    "Background": ["forest", "city", "beach"]  # random (@)
}

# Only combinatorial placeholders expand
combinatorial_keys = ["Outfit", "Angle"]
random_keys = ["Background"]

base_combinations = list(itertools.product(
    placeholders["Outfit"],
    placeholders["Angle"]
))
# Result: [("dress","front"), ("dress","side"), ("shirt","front"), ("shirt","side")]

# For each base combination, randomly select from random_keys
final_combinations = []
for combo in base_combinations:
    random_values = {
        key: random.choice(placeholders[key])
        for key in random_keys
    }
    final_combinations.append({**dict(zip(combinatorial_keys, combo)), **random_values})
```

### Seeding Strategy

Use deterministic seeding for reproducibility:

```python
base_seed = 42

for i, combo in enumerate(base_combinations):
    # Seed for this combination
    combo_seed = base_seed + i
    rng = random.Random(combo_seed)

    random_values = {
        key: rng.choice(placeholders[key])
        for key in random_keys
    }
```

**Result:** Same seed always produces same random selections.

### Placeholder Parsing

Update `extract_placeholders_with_limits()`:

```python
def extract_placeholders_with_limits(prompt: str):
    """Extract placeholders with options including random marker."""

    pattern = r'\{(\w+)(?::([^}]+))?\}'
    placeholders = {}

    for match in re.finditer(pattern, prompt):
        name = match.group(1)
        options = match.group(2) or ""

        is_random = '@' in options
        # ... parse other options (limit, index, priority)

        placeholders[name] = {
            "random": is_random,
            "limit": limit,
            "indices": indices,
            "priority": priority
        }

    return placeholders
```

---

## Implementation Plan

### Phase 1: Core Random Support (1.5 days)

**Tasks:**
- [ ] Update `extract_placeholders_with_limits()` to detect `@` marker
- [ ] Separate placeholders into combinatorial vs random sets
- [ ] Implement seeded random selection for random placeholders
- [ ] Update combination generation logic
- [ ] Add tests for basic random placeholder functionality

### Phase 2: Option Combinations (1 day)

**Tasks:**
- [ ] Support `{Name:N@}` (limit + random)
- [ ] Support `{Name:#|1|5@}` (index + random)
- [ ] Handle multiple instances `{Detail:@}, {Detail:@}`
- [ ] Add tests for all option combinations

### Phase 3: Modes and Edge Cases (0.5 days)

**Tasks:**
- [ ] Random mode behavior (already random, `@` has no effect)
- [ ] Combinatorial mode behavior (implement random selection)
- [ ] Edge case: All placeholders marked `@` (error? warning?)
- [ ] Edge case: Random placeholder with 1 value (always same)

### Phase 4: Metadata and Validation (0.5 days)

**Tasks:**
- [ ] Record random placeholders in metadata.json
- [ ] Show which values were selected for random placeholders
- [ ] Validate `@` marker in config validation
- [ ] Add warnings for potential mistakes

### Phase 5: Documentation (0.5 days)

**Tasks:**
- [ ] Update `placeholders.md` with `@` syntax
- [ ] Add examples to `features.md`
- [ ] Update JSON config schema documentation
- [ ] Create tutorial examples

---

## Examples

### Example 1: Character Sheet with Random Backgrounds

**Config:**
```json
{
  "prompt": {
    "template": "1girl, {Outfit:$1}, {Angle:$10}, {Expression:$20}, {Background:@}"
  },
  "variations": {
    "Outfit": ["dress", "shirt", "kimono"],
    "Angle": ["front", "side", "back"],
    "Expression": ["smiling", "serious"],
    "Background": ["forest", "city", "beach", "mountains", "desert"]
  },
  "generation": {
    "mode": "combinatorial",
    "seed_mode": "progressive",
    "seed": 42
  }
}
```

**Result:**
```
Total combinations: 3 × 3 × 2 = 18 images

Image 001: dress, front, smiling, beach (random)
Image 002: dress, front, serious, forest (random)
Image 003: dress, side, smiling, mountains (random)
...
```

Each image gets a different random background.

### Example 2: Quality Tags

**Config:**
```json
{
  "prompt": {
    "template": "portrait, {Expression}, {Quality:@}"
  },
  "variations": {
    "Expression": ["happy", "sad", "angry"],
    "Quality": ["masterpiece", "best quality", "high quality", "detailed"]
  }
}
```

**Result:**
```
3 combinations (one per expression)

Image 001: happy, best quality (random)
Image 002: sad, detailed (random)
Image 003: angry, masterpiece (random)
```

### Example 3: Multiple Random Details

**Config:**
```json
{
  "prompt": {
    "template": "anime girl, {Outfit}, {Detail:@}, {Detail:@}"
  },
  "variations": {
    "Outfit": ["dress", "shirt"],
    "Detail": ["glasses", "jewelry", "tattoo", "scar", "freckles"]
  }
}
```

**Result:**
```
2 combinations (one per outfit)

Image 001: dress, glasses, tattoo
Image 002: shirt, freckles, jewelry
```

Each detail instance picks independently.

### Example 4: Limited Random Pool

**Config:**
```json
{
  "prompt": {
    "template": "{Character}, {Pose}, {Lighting:5@}"
  },
  "variations": {
    "Character": ["Alice", "Bob"],
    "Pose": ["standing", "sitting"],
    "Lighting": "/path/to/50_lighting_options.txt"
  }
}
```

**Result:**
```
4 combinations (2 × 2)

First, randomly select 5 lighting options from 50
Then, for each combination, randomly pick one of those 5

Reproducible: same seed = same 5 options selected
```

---

## Metadata Format

### In metadata.json

```json
{
  "variations": {
    "Outfit": {
      "source_file": "/path/to/outfits.txt",
      "mode": "combinatorial",
      "count": 3,
      "values": ["dress", "shirt", "kimono"]
    },
    "Background": {
      "source_file": "/path/to/backgrounds.txt",
      "mode": "random",
      "count": 5,
      "values": ["forest", "city", "beach", "mountains", "desert"],
      "selected_per_combination": [
        {"combo_index": 0, "value": "beach"},
        {"combo_index": 1, "value": "forest"},
        {"combo_index": 2, "value": "mountains"}
      ]
    }
  },
  "generation": {
    "combinatorial_placeholders": ["Outfit", "Angle", "Expression"],
    "random_placeholders": ["Background"],
    "total_combinations": 18
  }
}
```

---

## Edge Cases

### All Placeholders Random

```python
prompt = "{A:@}, {B:@}, {C:@}"
```

**Behavior:** Generate 1 image (no combinations to expand).

**Alternative:** Error/warning suggesting at least one combinatorial placeholder.

### Random in Random Mode

```python
generation_mode = "random"
prompt = "{Expression}, {Background:@}"
```

**Behavior:** `@` marker ignored (already random mode).

**Metadata:** Note that `@` was present but had no effect.

### Single Value Random

```python
variations = {
    "Background": ["only_one_option"]
}
prompt = "{Expression}, {Background:@}"
```

**Behavior:** Always selects "only_one_option" (deterministic).

---

## Advantages

1. **Reduces Combinatorial Explosion**: Add variety without multiplying combinations
2. **Visual Diversity**: Each image unique without massive image counts
3. **Reproducible**: Seeded random = same results
4. **Flexible**: Choose which placeholders are combinatorial vs random
5. **Intuitive**: `@` marker is clear and concise

---

## Disadvantages

1. **Cannot Generate All Combinations**: Random = subset only
2. **Less Exhaustive**: May miss some combinations
3. **Documentation Needed**: Users must understand combinatorial vs random
4. **Metadata Complexity**: Need to track what was selected

---

## Best Practices

### When to Use Random (`@`)

✅ Use `@` when:
- Background/environment variations
- Quality/detail tags
- Lighting that doesn't need to be systematic
- Adding variety without combinatorial explosion
- Reducing total image count

### When to Use Combinatorial (default)

✅ Use combinatorial when:
- Character attributes (outfit, expression, pose)
- Systematic testing of all combinations
- Creating complete datasets
- Comparing specific combinations

### Recommended Pattern

```json
{
  "variations": {
    // Core attributes: combinatorial
    "Outfit": "...",
    "Expression": "...",
    "Angle": "...",

    // Modifiers: random
    "Background": "...@",
    "Lighting": "...@",
    "Detail": "...@"
  }
}
```

---

## Future Enhancements

### Weighted Random Selection

```json
{
  "variations": {
    "Background": {
      "mode": "random",
      "values": [
        {"value": "forest", "weight": 5},
        {"value": "city", "weight": 3},
        {"value": "beach", "weight": 2}
      ]
    }
  }
}
```

**Status:** Future enhancement

### Random Pools

Define multiple random pools:

```json
{
  "variations": {
    "NaturalBackground": ["forest", "beach", "mountains"],
    "UrbanBackground": ["city", "street", "building"],
    "Background": "@random_choice(NaturalBackground, UrbanBackground)"
  }
}
```

**Status:** Complex, deferred

---

## Success Criteria

- ✅ `@` marker correctly identifies random placeholders
- ✅ Random placeholders don't expand combinations
- ✅ Seeded random selection is reproducible
- ✅ Works with all placeholder options (limit, index, priority)
- ✅ Multiple instances select independently
- ✅ Metadata records random selections
- ✅ Documentation clear and comprehensive

---

## Dependencies

- Depends on: JSON Config System (SF-1, SF-3)
- Depends on: Placeholder system (existing)
- Blocks: None
- Related: Inline Variations (both enhance variation system)

---

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-01 | Claude | Initial specification |
