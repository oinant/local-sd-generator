# Fixed Placeholders

**Feature**: `--use-fixed` parameter
**Purpose**: Lock specific placeholder values while others vary
**Use Case**: Testing single-variable changes, controlled generation

---

## What are Fixed Placeholders?

By default, sdgen generates variations by combining **all** possible values for **all** placeholders. Sometimes you want to **fix** certain placeholders to specific values while letting others vary.

**Example Scenario**:
- You want to test different hair colors
- But keep the same outfit, pose, and mood
- Without fixed placeholders: 10 hair colors × 20 outfits × 15 poses = 3000 combinations
- With fixed placeholders: 10 hair colors × 1 outfit × 1 pose = 10 combinations

---

## Usage

### Basic Syntax

```bash
sdgen generate -t prompt.yaml --use-fixed "Placeholder:variation_key"
```

### Multiple Fixed Values

Use `|` to separate multiple fixed placeholders:

```bash
sdgen generate -t prompt.yaml --use-fixed "Mood:sad|Rendering:semi-realistic"
```

---

## Examples

### Example 1: Test Hair Colors Only

**Scenario**: Test 15 hair colors while keeping everything else constant.

```bash
sdgen generate -t v4-solo.prompt.yaml \
  --use-fixed "Outfit:bikini_top|Pose:standing|Mood:neutral" \
  -n 15
```

**Result**: 15 images with different hair colors, same outfit/pose/mood.

### Example 2: Test Rendering Styles

**Scenario**: Test different rendering styles (anime, semi-realistic, realistic) with same scene.

```bash
sdgen generate -t v4-solo.prompt.yaml \
  --use-fixed "Hair:long_blonde|Outfit:casual_dress|Pose:sitting" \
  -n 10
```

Then manually test each rendering style:
```bash
# Semi-realistic
sdgen generate -t v4-solo.prompt.yaml \
  --use-fixed "Hair:long_blonde|Outfit:casual_dress|Pose:sitting|Rendering:semi-realistic" \
  -n 1

# Anime
sdgen generate -t v4-solo.prompt.yaml \
  --use-fixed "Hair:long_blonde|Outfit:casual_dress|Pose:sitting|Rendering:anime" \
  -n 1
```

### Example 3: A/B Testing Prompts

**Scenario**: Compare two mood variations with same setup.

```bash
# Test A: Happy mood
sdgen generate -t v4-solo.prompt.yaml \
  --use-fixed "Hair:ponytail|Outfit:sportswear|Mood:happy" \
  -n 10 \
  --output-session happy_test

# Test B: Sad mood
sdgen generate -t v4-solo.prompt.yaml \
  --use-fixed "Hair:ponytail|Outfit:sportswear|Mood:sad" \
  -n 10 \
  --output-session sad_test
```

**Result**: Two sessions with same hair/outfit, different moods for comparison.

---

## How It Works

### Step 1: Parse Fixed Values

```python
# --use-fixed "Mood:sad|Rendering:semi-realistic"
# Parsed to:
{
  "Mood": "sad",
  "Rendering": "semi-realistic"
}
```

### Step 2: Filter Context Imports

For each fixed placeholder, the system **filters the variations dict** to contain only the specified key:

```python
# Before filtering
context.imports = {
  "Mood": {
    "happy": "happy, joyful",
    "sad": "sad, melancholic",    # ← This one
    "angry": "angry, fierce"
  },
  "Rendering": {
    "anime": "anime style",
    "semi-realistic": "semi-realistic",  # ← This one
    "realistic": "realistic"
  },
  "Hair": {
    "short": "short hair",
    "long": "long hair"
    # All variations available
  }
}

# After filtering with --use-fixed "Mood:sad|Rendering:semi-realistic"
context.imports = {
  "Mood": {
    "sad": "sad, melancholic"    # Only this one
  },
  "Rendering": {
    "semi-realistic": "semi-realistic"  # Only this one
  },
  "Hair": {
    "short": "short hair",
    "long": "long hair"
    # All variations still available
  }
}
```

### Step 3: Generate Variations

Generation proceeds normally, but fixed placeholders only have 1 variation each:

**Combinatorial mode**:
- Mood: 1 variation (fixed)
- Rendering: 1 variation (fixed)
- Hair: 10 variations (free)
- **Total**: 1 × 1 × 10 = 10 images

**Random mode**:
- Fixed placeholders always use the same value
- Other placeholders vary randomly

---

## Finding Variation Keys

### Method 1: Check Variation Files

```bash
# List keys in a variation file
grep -E "^[a-z_]+:" prompts/hassaku/variations/hair.yaml

# Example output:
# long_blonde: "long blonde hair"
# short_brown: "short brown hair"
# ponytail_red: "red hair in ponytail"
```

Use the **left side** (before `:`) as the key:
```bash
--use-fixed "Hair:long_blonde"
```

### Method 2: Check Manifest

After generating once, check `manifest.json`:

```bash
sdgen generate -t prompt.yaml -n 1
cat apioutput/<session>/manifest.json | jq '.variations'
```

**Output**:
```json
{
  "Hair": ["long_blonde", "short_brown", "ponytail_red"],
  "Outfit": ["casual_dress", "sportswear", "bikini_top"],
  "Mood": ["happy", "sad", "neutral"]
}
```

Use these keys in `--use-fixed`.

### Method 3: Trial and Error

```bash
# Try with a guess
sdgen generate -t prompt.yaml --use-fixed "Hair:blonde" -n 1

# If key doesn't exist, you'll get an error:
# ValueError: Fixed placeholder 'Hair' has invalid key 'blonde'
# Available keys: long_blonde, short_brown, ponytail_red
```

---

## Advanced Usage

### Combining with Other Filters

```bash
# Fixed placeholders + style + theme
sdgen generate -t prompt.yaml \
  --theme cyberpunk \
  --style sexy \
  --use-fixed "Hair:neon_blue|Outfit:leather_jacket" \
  -n 50
```

### Iterating Over Single Variable

```bash
# Script to test each hair color separately
for hair in long_blonde short_brown ponytail_red; do
  sdgen generate -t prompt.yaml \
    --use-fixed "Hair:$hair|Outfit:casual_dress|Pose:standing" \
    -n 1 \
    --output-session "test_hair_$hair"
done
```

### Percentage Testing

```bash
# Generate 80% with fixed mood, 20% random
sdgen generate -t prompt.yaml --use-fixed "Mood:happy" -n 80
sdgen generate -t prompt.yaml -n 20
```

---

## Limitations

### 1. Key Must Exist

The specified key **must exist** in the variation dict:

```bash
# ❌ Error if 'blue_hair' key doesn't exist
--use-fixed "Hair:blue_hair"

# Check available keys first
cat prompts/hassaku/variations/hair.yaml
```

### 2. Placeholder Must Be Used

The fixed placeholder **must appear in the prompt template**:

```bash
# ❌ Error if {Mood} is not in prompt template
--use-fixed "Mood:happy"
```

### 3. No Selector Override

Fixed values work on the **resolved variations**, not on selectors:

```yaml
# prompt.yaml has:
prompt: "{Hair[limit:5]}, beautiful girl"
```

```bash
# This will:
# 1. Apply selector (limit to 5 hair variations)
# 2. THEN apply fixed (narrow to just 'long_blonde')
--use-fixed "Hair:long_blonde"
```

### 4. Generation Mode Still Applies

```bash
# Combinatorial: Generates ALL combinations of non-fixed placeholders
sdgen generate -t prompt.yaml --use-fixed "Hair:blonde" --mode combinatorial

# Random: Generates random combinations of non-fixed placeholders
sdgen generate -t prompt.yaml --use-fixed "Hair:blonde" --mode random -n 50
```

---

## Use Cases

### 1. **Character Design Iteration**

Lock character features, iterate on outfit:
```bash
sdgen generate -t v4-solo.prompt.yaml \
  --use-fixed "Hair:long_red|Eyes:green|Body:athletic" \
  -n 100
# Tests 100 different outfits with same character
```

### 2. **Lighting/Rendering Tests**

Lock scene, test rendering:
```bash
sdgen generate -t v4-solo.prompt.yaml \
  --use-fixed "Hair:ponytail|Outfit:bikini|Pose:standing|Location:beach" \
  -n 20
# Tests rendering variations with same scene setup
```

### 3. **Style Consistency Check**

Lock style elements, test variations:
```bash
sdgen generate -t v4-solo.prompt.yaml \
  --theme cyberpunk \
  --use-fixed "Rendering:neon_lighting|Mood:dark" \
  -n 50
# All images have consistent cyberpunk aesthetic
```

### 4. **Dataset Creation**

Create consistent dataset for training:
```bash
# Same character, 100 different poses
sdgen generate -t v4-solo.prompt.yaml \
  --use-fixed "Hair:long_blonde|Eyes:blue|Outfit:casual|Rendering:semi-realistic" \
  -n 100
```

---

## Troubleshooting

### Error: "Fixed placeholder 'X' has invalid key 'Y'"

**Cause**: The key doesn't exist in the variation dict.

**Fix**: Check available keys:
```bash
# Method 1: Check variation file
cat prompts/hassaku/variations/<placeholder>.yaml

# Method 2: Generate once without --use-fixed and check manifest
sdgen generate -t prompt.yaml -n 1
cat apioutput/<session>/manifest.json | jq '.variations.<Placeholder>'
```

### Error: "Placeholder 'X' not found in context"

**Cause**: The placeholder isn't used in the prompt template.

**Fix**: Verify the placeholder is in the template:
```bash
grep -oE '\{[A-Z][a-zA-Z0-9]*\}' prompts/hassaku/prompt.yaml
```

### No Variations Generated

**Symptom**: Only 1 image generated when expecting more.

**Cause**: All placeholders are fixed.

**Fix**: Leave at least one placeholder unfixed:
```bash
# ❌ All fixed = only 1 image
--use-fixed "Hair:blonde|Outfit:dress|Pose:standing|Mood:happy"

# ✅ Leave Pose free = multiple images
--use-fixed "Hair:blonde|Outfit:dress|Mood:happy"
```

---

## Related Documentation

- [Generation Modes](./generation-modes.md) - Combinatorial vs Random
- [Selectors](./selectors.md) - Filtering variations in templates
- [Manifest Format](../reference/manifest-format.md) - Understanding variation keys

---

## Quick Reference

```bash
# Single fixed placeholder
--use-fixed "Placeholder:key"

# Multiple fixed placeholders
--use-fixed "Placeholder1:key1|Placeholder2:key2"

# With theme and style
--use-fixed "Hair:blonde|Outfit:dress" --theme cyberpunk --style sexy

# Find available keys
cat prompts/<theme>/variations/<placeholder>.yaml
# OR
sdgen generate -t prompt.yaml -n 1 && cat apioutput/<session>/manifest.json | jq .variations
```

---

## Implementation Details

**Code Location**: `sd_generator_cli/templating/utils/fixed_placeholders.py`

**Function**: `parse_fixed_values(fixed_arg: str) -> dict[str, str]`

**Parsing Format**:
- Delimiter between pairs: `|`
- Delimiter within pair: `:`
- Whitespace: Stripped
- Values with colons: Supported (splits on first `:` only)

**Example**:
```python
parse_fixed_values("mood:sad|time:12:30:45")
# Returns: {"mood": "sad", "time": "12:30:45"}
```

---

## See Also

- [Seed-Sweep Mode](./seed-sweep-mode.md) - Test variations on controlled seed sets (perfect combo with `--use-fixed`)
- [Generation Modes](../reference/template-syntax.md#generation) - Combinatorial vs Random generation
- [CLI Commands Reference](../reference/cli-commands.md) - All CLI options
