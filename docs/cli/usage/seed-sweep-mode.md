# Seed-Sweep Mode

**Test variations scientifically with controlled seed sets**

---

## Overview

Seed-sweep mode allows you to test multiple prompt variations against the same set of seeds, enabling scientific comparison of different formulations. Instead of using different seeds for each image, this approach isolates variation as the only changing variable.

**Key concept**: Each variation is tested on ALL seeds in the list.

```
12 variations × 20 seeds = 240 images
```

This creates a scientific experiment where you can:
- Compare stability rates between different tag formulations
- Identify which seeds work reliably across variations
- Detect seed-specific biases in model behavior
- Build optimized tag dictionaries specific to your model

---

## Quick Start

**Basic example** - Test 3 hair color variations on 20 seeds:

```bash
# Create a simple template
cat > test.prompt.yaml <<EOF
name: Hair Color Test
template: "portrait, {HairColor}, detailed face"
imports:
  HairColor: variations/hair_colors.txt
generation:
  mode: combinatorial
parameters:
  width: 512
  height: 768
  steps: 20
EOF

# Run with seed-sweep
sdgen generate -t test.prompt.yaml --seeds 20#1000
```

**Result**: 3 variations × 20 seeds = 60 images

Each variation (e.g., "red hair", "crimson hair", "scarlet hair") will be tested on seeds 1000-1019, allowing you to compare which formulation is most stable.

---

## Syntax

The `--seeds` parameter accepts three formats:

### 1. Explicit List

Specify exact seeds to test:

```bash
--seeds 1000,1005,1008,1042
```

**Use case**: Test on specific seeds you know are problematic or interesting.

**Example**:
```bash
sdgen generate -t portrait.yaml --seeds 1000,1005,1008,1042
```

**Output**: 4 seeds × N variations = 4N images

---

### 2. Range

Continuous range of seeds:

```bash
--seeds 1000-1019
```

**Use case**: Systematic testing across a range.

**Example**:
```bash
sdgen generate -t character.yaml --seeds 1000-1019
```

**Output**: 20 seeds × N variations = 20N images

**Note**: Range is inclusive on both ends (1000-1019 includes both 1000 and 1019).

---

### 3. Count + Start

Specify how many seeds starting from a value:

```bash
--seeds 20#1000
```

Format: `<count>#<start>`
- Count: Number of sequential seeds
- Start: First seed value

**Use case**: Quick specification of sequential seeds.

**Example**:
```bash
sdgen generate -t test.yaml --seeds 20#1000
```

**Output**: 20 seeds (1000-1019) × N variations = 20N images

**Equivalent to**: `--seeds 1000-1019`

---

## Use Cases

### 1. Semantic A/B Testing

Compare different tag formulations to find the most stable wording:

```bash
# Template with semantic variations
cat > semantic_test.yaml <<EOF
name: Red Hair Semantic Test
template: "portrait, {RedHairVariant}, detailed"
imports:
  RedHairVariant: |
    variant_a: red hair
    variant_b: crimson hair
    variant_c: scarlet hair
    variant_d: auburn hair
generation:
  mode: combinatorial
EOF

# Test all variants on same 50 seeds
sdgen generate -t semantic_test.yaml --seeds 50#1000
```

**Analysis**: Compare output images to see which formulation produces:
- Most consistent results across seeds
- Fewest artifacts or unwanted features
- Best adherence to intended concept

**Result**: Build a "stability dictionary" of proven tags for your model.

---

### 2. Model Reverse Engineering

Discover which tags your model understands natively:

```bash
# Template testing pose keywords
cat > pose_test.yaml <<EOF
name: Pose Keyword Test
template: "{PoseKeyword}, full body shot, studio lighting"
imports:
  PoseKeyword: variations/pose_synonyms.txt
generation:
  mode: combinatorial
EOF

# Test on diverse seed set
sdgen generate -t pose_test.yaml --seeds 100#5000
```

**Analysis**:
- Tags that work on 80%+ of seeds → model understands natively
- Tags that fail on 50%+ of seeds → model needs reinforcement
- Inconsistent tags → potential training targets

**Result**: Optimized tag vocabulary for your specific checkpoint.

---

### 3. Seed Bias Detection

Find which seeds are reliable for testing:

```bash
# Test simple concept on many seeds
cat > seed_test.yaml <<EOF
name: Seed Reliability Test
template: "portrait, smiling, professional photo"
generation:
  mode: combinatorial
EOF

# Test 200 seeds with no variations
sdgen generate -t seed_test.yaml --seeds 200#1000
```

**Analysis**: Identify seeds that:
- Consistently produce good results → "safe seeds" for future tests
- Frequently produce artifacts → avoid these seeds
- Show interesting emergent features → bookmark for creative use

**Result**: Curated list of reliable seeds for scientific testing.

---

### 4. Semantic Dictionary Building

Build a comprehensive stability database:

```bash
# Test multiple concepts systematically
cat > concept_test.yaml <<EOF
name: Concept Stability Matrix
template: "portrait, {Concept}, detailed"
imports:
  Concept: variations/concepts_to_test.txt
generation:
  mode: combinatorial
EOF

# Test each concept on 30 seeds
sdgen generate -t concept_test.yaml --seeds 30#1000
```

**variations/concepts_to_test.txt**:
```
happy: smiling, cheerful, joyful, happy expression
angry: angry, furious, mad, enraged
sad: sad, melancholic, crying, tearful
# ... etc
```

**Analysis**: Calculate stability score per concept:
```
Stability = (Good images / Total images) × 100
```

**Result**: Ranked list of stable concepts for LoRA training.

---

## Output Format

### Filename Convention

Images include the seed in the filename:

```
session_0001_seed-1000.png
session_0002_seed-1001.png
session_0003_seed-1002.png
...
```

**Format**: `{session_name}_{index:04d}_seed-{seed}.png`

This makes it easy to:
- Sort by seed to compare variations
- Identify which seed produced which result
- Track problematic seeds across sessions

---

### Manifest Structure

The `manifest.json` includes seed-sweep metadata:

```json
{
  "snapshot": {
    "version": "2.0",
    "timestamp": "2025-11-07T15:30:00",
    "generation_params": {
      "mode": "combinatorial",
      "seed_mode": "fixed",
      "base_seed": -1,
      "seed_list": [1000, 1001, 1002, ..., 1019],
      "num_images": 60,
      "total_combinations": 3
    },
    "variations": {
      "HairColor": {
        "available": ["red hair", "crimson hair", "scarlet hair"],
        "used": ["red hair", "crimson hair", "scarlet hair"],
        "count": 3
      }
    }
  },
  "images": [
    {
      "filename": "test_0001_seed-1000.png",
      "seed": 1000,
      "prompt": "portrait, red hair, detailed face",
      "applied_variations": {
        "HairColor": "red hair"
      }
    },
    {
      "filename": "test_0002_seed-1001.png",
      "seed": 1001,
      "prompt": "portrait, red hair, detailed face",
      "applied_variations": {
        "HairColor": "red hair"
      }
    },
    ...
  ]
}
```

**Key fields**:
- `generation_params.seed_list`: All seeds used in the sweep
- `images[].seed`: Actual seed used for each image
- `images[].applied_variations`: Which variation values were used

---

## Integration with Other Features

### Combining with `--use-fixed`

Lock specific placeholders while sweeping seeds:

```bash
# Fix outfit, sweep seeds across poses
sdgen generate -t character.yaml \
  --use-fixed "Outfit:casual_jeans" \
  --seeds 20#1000
```

**Use case**: Test pose variations in the same outfit across seeds.

**Example template**:
```yaml
name: Pose Test
template: "{Outfit}, {Pose}, detailed"
imports:
  Outfit: variations/outfits.txt
  Pose: variations/poses.txt
generation:
  mode: combinatorial
```

**Result**: 1 outfit × 12 poses × 20 seeds = 240 images

All images have same outfit, allowing pure pose comparison.

---

### Generation Modes

Seed-sweep works with both generation modes:

#### Combinatorial Mode

**All combinations × All seeds**:

```bash
sdgen generate -t test.yaml --seeds 10#1000
```

If template has 12 variations:
- 12 combinations × 10 seeds = 120 images
- Each combination tested on ALL 10 seeds

**Order**:
```
Variation 1 + Seed 1000
Variation 1 + Seed 1001
...
Variation 1 + Seed 1009
Variation 2 + Seed 1000
Variation 2 + Seed 1001
...
```

---

#### Random Mode

**Random combinations × All seeds**:

```yaml
generation:
  mode: random
  max_images: 100
```

```bash
sdgen generate -t test.yaml --seeds 10#1000
```

**Behavior**:
- Pick random combinations until `max_images / len(seed_list)` unique combos
- Test each combo on ALL seeds

**Example**: `max_images: 100` with 10 seeds:
- 100 / 10 = 10 unique combinations needed
- Each combo tested on all 10 seeds
- Total: 10 combos × 10 seeds = 100 images

---

### Seed Mode Override

**Important**: When `--seeds` is specified, the template's `seed_mode` is ignored.

Template:
```yaml
generation:
  seed_mode: progressive  # Ignored when --seeds is used
  seed: 42                # Ignored when --seeds is used
```

Command:
```bash
sdgen generate -t test.yaml --seeds 20#1000
```

**Result**: Uses seeds 1000-1019 (from `--seeds`), not progressive seeds starting at 42.

**Why**: Seed-sweep mode requires explicit control over seeds for scientific reproducibility.

---

### Theme Support

Seed-sweep works seamlessly with themes:

```bash
# Test theme variations on same seeds
sdgen generate -t character.template.yaml \
  --theme cyberpunk \
  --seeds 20#1000
```

**Use case**: Compare how different themes affect stability across seeds.

**Example workflow**:
```bash
# Test cyberpunk theme
sdgen generate -t char.template.yaml --theme cyberpunk --seeds 20#1000

# Test pirate theme (same seeds!)
sdgen generate -t char.template.yaml --theme pirates --seeds 20#1000

# Compare stability between themes
```

---

## Tips & Best Practices

### 1. Choose Seed Count Wisely

| Seed Count | Use Case | Time Investment |
|------------|----------|-----------------|
| 5-10       | Quick test, proof of concept | ~5-15 min |
| 20-30      | Standard A/B testing | ~30-60 min |
| 50-100     | Comprehensive stability analysis | 2-4 hours |
| 100+       | Model reverse engineering | 4+ hours |

**Recommendation**: Start with 20 seeds for most scientific tests.

---

### 2. Use Explicit Lists for Known Seeds

If you've identified specific problematic seeds:

```bash
# Test only on seeds known to cause issues
--seeds 1005,1008,1042,1234,5678
```

**Benefit**: Faster testing, focused on problem areas.

---

### 3. Range for Systematic Testing

For unbiased testing:

```bash
# Test consecutive range
--seeds 1000-1099  # 100 seeds
```

**Benefit**: No cherry-picking bias, systematic coverage.

---

### 4. Count#Start for Convenience

When you just need N sequential seeds:

```bash
# Quick: 20 seeds starting at 1000
--seeds 20#1000

# Equivalent but more verbose
--seeds 1000-1019
```

**Benefit**: Fastest to type, clear intent.

---

### 5. Combine with `--count` for Limits

Limit total images while using seed-sweep:

```bash
# Template has 50 variations, 20 seeds = 1000 images
# Limit to first 100
sdgen generate -t large.yaml --seeds 20#1000 --count 100
```

**Result**: First 100 images only (5 variations × 20 seeds).

**Use case**: Quick sampling of large sweeps.

---

### 6. Analyze Results Systematically

**Sort by seed** to compare variations:
```bash
ls -1 session_*_seed-1000.png  # All variations on seed 1000
ls -1 session_*_seed-1001.png  # All variations on seed 1001
```

**Sort by variation** (use manifest.json):
```python
import json

manifest = json.load(open("manifest.json"))
images_by_variation = {}

for img in manifest["images"]:
    var_key = tuple(sorted(img["applied_variations"].items()))
    if var_key not in images_by_variation:
        images_by_variation[var_key] = []
    images_by_variation[var_key].append(img["filename"])

# Now you have all images grouped by variation
```

---

### 7. Document Your Findings

After seed-sweep analysis, document:
- Which tags/concepts are stable (>80% success)
- Which seeds are reliable (consistent results)
- Which combinations to avoid (frequent artifacts)

**Example**:
```markdown
# Stability Report - Hair Color Tags (2025-11-07)

Tested on seeds 1000-1019 (20 seeds)

## Results
- "red hair": 18/20 success (90%) ✓ STABLE
- "crimson hair": 12/20 success (60%) ⚠ UNSTABLE
- "scarlet hair": 8/20 success (40%) ✗ AVOID

## Reliable Seeds
- 1000, 1002, 1005, 1010, 1015: 100% success across all tags

## Conclusion
Use "red hair" tag for production. Avoid seeds 1003, 1008, 1012.
```

---

## Examples

### Example 1: Quick Semantic Test

```bash
# Test 3 synonyms on 10 seeds (30 images, ~5 min)
cat > quick_test.yaml <<EOF
name: Happy Face Test
template: "portrait, {Expression}, detailed"
imports:
  Expression: |
    smile: smiling
    happy: happy expression
    cheerful: cheerful face
generation:
  mode: combinatorial
parameters:
  width: 512
  height: 512
  steps: 15
EOF

sdgen generate -t quick_test.yaml --seeds 10#1000
```

---

### Example 2: Comprehensive Stability Analysis

```bash
# Test 10 concepts on 50 seeds (500 images, ~2 hours)
cat > stability_test.yaml <<EOF
name: Emotion Stability Matrix
template: "portrait, {Emotion}, professional photo"
imports:
  Emotion: variations/emotions.txt
generation:
  mode: combinatorial
parameters:
  width: 512
  height: 768
  steps: 20
EOF

sdgen generate -t stability_test.yaml --seeds 50#1000
```

**variations/emotions.txt**:
```
happy: smiling, happy
sad: sad expression
angry: angry face
surprised: surprised
neutral: neutral expression
confused: confused
excited: excited, enthusiastic
calm: calm, serene
worried: worried expression
confident: confident expression
```

---

### Example 3: Seed Reliability Baseline

```bash
# Find reliable seeds (200 images, ~45 min)
cat > seed_baseline.yaml <<EOF
name: Seed Baseline
template: "portrait, neutral expression, studio lighting"
generation:
  mode: combinatorial
parameters:
  width: 512
  height: 768
  steps: 20
EOF

sdgen generate -t seed_baseline.yaml --seeds 200#1000
```

**Analysis**: Review all 200 images, tag seeds with:
- ✓ Good: Clean, artifact-free
- ⚠ OK: Acceptable but minor issues
- ✗ Bad: Artifacts, distortions

---

### Example 4: Fixed Outfit, Variable Pose

```bash
# Lock outfit, test poses on 20 seeds
cat > pose_sweep.yaml <<EOF
name: Pose Sweep
template: "{Outfit}, {Pose}, detailed character"
imports:
  Outfit: variations/outfits.txt
  Pose: variations/poses.txt
generation:
  mode: combinatorial
EOF

sdgen generate -t pose_sweep.yaml \
  --use-fixed "Outfit:casual_jeans" \
  --seeds 20#1000
```

**Result**: All images in same outfit, pure pose comparison.

---

### Example 5: Theme Comparison

```bash
# Compare cyberpunk vs scifi on same seeds
sdgen generate -t character.template.yaml \
  --theme cyberpunk \
  --seeds 30#1000 \
  --session-name cyberpunk_sweep

sdgen generate -t character.template.yaml \
  --theme scifi \
  --seeds 30#1000 \
  --session-name scifi_sweep

# Now compare outputs side-by-side
```

---

## Advanced: Scripting Analysis

### Python Script to Calculate Stability

```python
#!/usr/bin/env python3
"""Calculate stability scores from seed-sweep results."""

import json
from pathlib import Path
from collections import defaultdict

def analyze_seed_sweep(manifest_path):
    """
    Analyze seed-sweep manifest to calculate stability.

    Returns:
        dict: Variation -> stability score (0-1)
    """
    with open(manifest_path) as f:
        manifest = json.load(f)

    # Group images by variation
    variation_groups = defaultdict(list)

    for img in manifest["images"]:
        # Create variation key
        var_items = sorted(img["applied_variations"].items())
        var_key = " | ".join(f"{k}={v}" for k, v in var_items)
        variation_groups[var_key].append(img)

    # Calculate stability (manual review needed, this is skeleton)
    print(f"Seed-sweep analysis for {len(variation_groups)} variations:")
    print()

    for variation, images in variation_groups.items():
        seed_count = len(images)
        print(f"{variation}:")
        print(f"  Tested on {seed_count} seeds")
        print(f"  Images: {', '.join(img['filename'] for img in images[:5])}...")
        print()

    return variation_groups

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: analyze_sweep.py manifest.json")
        sys.exit(1)

    analyze_seed_sweep(sys.argv[1])
```

**Usage**:
```bash
python analyze_sweep.py apioutput/20251107_153000_test/manifest.json
```

---

## Troubleshooting

### Issue: Too Many Images

**Problem**: 50 variations × 100 seeds = 5000 images (too many).

**Solution**: Use `--count` to limit:
```bash
sdgen generate -t large.yaml --seeds 100#1000 --count 500
```

---

### Issue: Ran Out of Seeds

**Problem**: Random mode exhausted unique combinations before filling all seeds.

**Symptom**: Fewer images than expected.

**Solution**: Increase `max_images` in template:
```yaml
generation:
  mode: random
  max_images: 200  # Increase this
```

---

### Issue: Seeds Not in Filename

**Problem**: Filenames don't include `_seed-XXXX`.

**Cause**: Not using seed-sweep mode (forgot `--seeds`).

**Solution**: Always specify `--seeds` parameter:
```bash
sdgen generate -t test.yaml --seeds 20#1000
```

---

### Issue: Seed List Not in Manifest

**Problem**: `manifest.json` doesn't have `seed_list` field.

**Cause**: Older version or not using seed-sweep.

**Solution**: Update to latest version with seed-sweep support (commit ba7fd75+).

---

## See Also

- [Fixed Placeholders](./fixed-placeholders.md) - Lock specific variations
- [Generation Modes](../reference/template-syntax.md#generation) - Combinatorial vs Random
- [CLI Commands Reference](../reference/cli-commands.md) - All CLI options
- [Variation Files](./variation-files.md) - Creating variation dictionaries

---

## Summary

Seed-sweep mode enables scientific testing of prompt variations by:

✓ Testing variations on identical seed sets
✓ Isolating variation as the only changing variable
✓ Identifying stable vs unstable tags/concepts
✓ Building optimized dictionaries for your model
✓ Finding reliable seeds for future testing

**Quick command reference**:
```bash
# Explicit list
--seeds 1000,1005,1008

# Range
--seeds 1000-1019

# Count + start
--seeds 20#1000
```

**Output**: Filenames include seed (`session_0001_seed-1000.png`), manifest tracks full seed list.

**Integration**: Works with `--use-fixed`, themes, and both generation modes.
