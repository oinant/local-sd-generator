# Placeholder Priority System

**Status:** ✅ Complete
**Completed:** 2025-10-01
**Component:** cli
**Priority:** Medium

---

## Overview

The placeholder priority system allows users to control the order of loops in combinatorial generation mode by assigning priority weights to placeholders.

---

## Description

In combinatorial mode, the generator creates nested loops for each placeholder. The **priority weight** determines which placeholders form outer vs inner loops.

**Rule:** Lower priority = outer loop (changes less often)

---

## Syntax

```
{PlaceholderName:$priority}
{PlaceholderName:limit$priority}
{PlaceholderName:#|1|5$priority}
```

**Examples:**
- `{Outfit:$1}` - Priority 1 (outer loop)
- `{Angle:$10}` - Priority 10 (middle loop)
- `{Expression:$20}` - Priority 20 (inner loop)

---

## Use Case

### Character Sheet Generation

Generate a complete character sheet organized by outfit:

```python
prompt = "1girl, {Outfit:$1}, {Angle:$10}, {Expression:$20}, high quality"
```

**Loop order:**
```
FOR each Outfit:        ← Outer (priority 1)
    FOR each Angle:     ← Middle (priority 10)
        FOR each Expression:  ← Inner (priority 20)
            Generate image
```

**Result:** All angles and expressions for Outfit 1, then all angles and expressions for Outfit 2, etc.

---

## Default Behavior (No Priorities)

Without priorities, placeholders are sorted **alphabetically**:

```python
prompt = "{Outfit}, {Angle}, {Expression}"
```

**Loop order:** Angle → Expression → Outfit (alphabetical)

**Problem:** Images not organized logically.

---

## Examples

### Example 1: Character Sheet

```python
from CLI.image_variation_generator import ImageVariationGenerator

generator = ImageVariationGenerator(
    prompt_template="1girl, {Outfit:$1}, {Angle:$10}, {Expression:$20}, high quality",
    negative_prompt="low quality",
    variation_files={
        "Outfit": "outfits.txt",      # 3 outfits
        "Angle": "angles.txt",        # 5 angles
        "Expression": "expressions.txt"  # 10 expressions
    },
    generation_mode="combinatorial",
    seed_mode="progressive",
    seed=42
)

generator.run()
```

**Generated order:**
```
1. Outfit A, Angle 1, Expression 1
2. Outfit A, Angle 1, Expression 2
...
10. Outfit A, Angle 1, Expression 10
11. Outfit A, Angle 2, Expression 1
...
50. Outfit A, Angle 5, Expression 10  ← All done for Outfit A
51. Outfit B, Angle 1, Expression 1   ← Start Outfit B
...
```

**Total:** 3 × 5 × 10 = 150 images, organized in 3 blocks (one per outfit).

---

### Example 2: Multiple Priorities

```python
prompt = "{Style:$1}, {Subject:$5}, {Lighting:$10}, {Mood:$15}"
```

**Loop order:**
1. Style (outer, priority 1)
2. Subject (priority 5)
3. Lighting (priority 10)
4. Mood (inner, priority 15)

**Behavior:** All moods + lighting for each subject in each style.

---

### Example 3: Combined with Limits

```python
prompt = "{Outfit:8$1}, {Angle:$10}, {Expression:15$20}"
```

- 8 random outfits, priority 1 (outer loop)
- All angles, priority 10 (middle)
- 15 random expressions, priority 20 (inner)

**Total:** 8 × (num angles) × 15 images

---

## Implementation

**File:** `CLI/variation_loader.py`

### Placeholder Parsing

```python
@dataclass
class PlaceholderInfo:
    name: str
    limit: Optional[int]
    indices: Optional[List[int]]
    priority: Optional[int]  # Priority weight
    suppress: bool

def extract_placeholders_with_limits(template: str) -> Dict[str, PlaceholderInfo]:
    """Extract placeholders with priority weights."""
    # Regex pattern: {Name:options$priority}
    pattern = r'\{([A-Za-z_][A-Za-z0-9_]*)(?::([^}]+))?\}'

    for match in re.finditer(pattern, template):
        name = match.group(1)
        options = match.group(2)

        if options and '$' in options:
            main_part, priority_str = options.split('$', 1)
            priority = int(priority_str)
            # ... parse main_part for limit/indices
```

### Loop Order Determination

```python
def _create_combinations_combinatorial(
    variations_dict: Dict[str, Dict],
    placeholder_priorities: Dict[str, int]
) -> List[Dict]:
    """Generate combinations with priority-based loop order."""

    # Sort placeholders by priority (ascending)
    sorted_placeholders = sorted(
        variations_dict.keys(),
        key=lambda p: placeholder_priorities.get(p, 100)
    )

    # Create nested loops in priority order
    # (Lower priority = outer loop)
    combinations = []
    for values in itertools.product(
        *[variations_dict[p].values() for p in sorted_placeholders]
    ):
        combo = dict(zip(sorted_placeholders, values))
        combinations.append(combo)

    return combinations
```

---

## Testing

**Tests:** Included in placeholder option tests

**File:** `tests/test_placeholder_priority.py`

**Test cases:**
- Basic priority ordering
- Multiple priorities
- Combined with limits and indices
- Default behavior (no priorities)
- Edge cases (same priority, missing priority)

**Run tests:**
```bash
pytest tests/test_placeholder_priority.py -v
```

---

## Documentation

**User Guide:** [Variation Files](../../cli/usage/variation-files.md#système-de-priorité-des-boucles)

**Technical:** [Variation Loader](../../cli/technical/variation-loader.md)

---

## Success Criteria

- ✅ Priority syntax supported: `{Name:$P}`
- ✅ Lower priority = outer loop
- ✅ Combined with other options (limit, indices)
- ✅ Default behavior when no priorities specified
- ✅ Clear documentation and examples

---

## Benefits

1. **Organized Output**
   - Logical grouping of images
   - Easy to review results

2. **Character Sheets**
   - All poses/expressions per outfit
   - Professional presentation

3. **Workflow Efficiency**
   - Find related images quickly
   - Delete entire groups easily

4. **Intuitive Control**
   - Clear priority numbers
   - Predictable behavior

---

## Related Features

- **Placeholder Limits:** `{Name:N}`
- **Index Selection:** `{Name:#|1|5}`
- **Suppression:** `{Name:0}`
- **Nested Variations:** `{|option1|option2}` in files

---

**Last updated:** 2025-10-01
