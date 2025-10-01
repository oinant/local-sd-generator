# Variation Loader

**Technical documentation for variation file parsing and placeholder extraction.**

---

## Overview

The `variation_loader` module handles:
1. Parsing variation files in multiple formats
2. Extracting placeholders from prompt templates
3. Expanding nested variations (`{|option1|option2}`)
4. Applying placeholder options (limits, indices, priorities)
5. Supporting multiple files per placeholder

---

## Module Structure

**File:** `CLI/variation_loader.py`

**Functions:**
- `load_variations_from_file()` - Load single file
- `load_variations_for_placeholders()` - Load all needed files
- `extract_placeholders_with_limits()` - Parse placeholder syntax
- `expand_nested_variations()` - Expand `{|}` syntax
- `limit_variations()` - Apply limits and index selection
- `create_random_combinations()` - Generate random combinations

---

## Core Functions

### load_variations_from_file

```python
def load_variations_from_file(
    file_path: str,
    encoding: str = "utf-8"
) -> Dict[str, str]:
    """
    Load variations from a single file.

    Args:
        file_path: Path to variation file
        encoding: File encoding (default UTF-8)

    Returns:
        Dict of key → value

    Supported formats:
        1. key→value:       "happy→smiling, cheerful"
        2. number→value:    "1→front view"
        3. value only:      "realistic style"

    Features:
        - Ignores empty lines
        - Ignores lines starting with #
        - Expands nested variations {|opt1|opt2}
        - Generates keys from values if not provided

    Example:
        File content:
            # Expressions
            happy→smiling, cheerful
            sad→crying, depressed
            neutral

        Returns:
            {
                "happy": "smiling, cheerful",
                "sad": "crying, depressed",
                "neutral": "neutral"
            }
    """
```

**Implementation Details:**

```python
def load_variations_from_file(file_path, encoding="utf-8"):
    variations = {}

    with open(file_path, 'r', encoding=encoding) as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            # Parse line
            if '→' in line:
                # Format: key→value or number→value
                key, value = line.split('→', 1)
                key = key.strip()
                value = value.strip()

                # If key is numeric, generate key from value
                if key.isdigit():
                    key = generate_key_from_value(value)
            else:
                # Format: value only
                value = line
                key = generate_key_from_value(value)

            # Expand nested variations
            expanded = expand_nested_variations(value)

            # Add all expanded variations
            for idx, expanded_value in enumerate(expanded):
                if len(expanded) > 1:
                    variation_key = f"{key}_{idx}"
                else:
                    variation_key = key
                variations[variation_key] = expanded_value

    return variations
```

---

### extract_placeholders_with_limits

```python
@dataclass
class PlaceholderInfo:
    """Information extracted from placeholder syntax."""
    name: str                    # Placeholder name
    limit: Optional[int]         # N from {Name:N}
    indices: Optional[List[int]] # [1,5,22] from {Name:#|1|5|22}
    priority: Optional[int]      # 10 from {Name:$10}
    suppress: bool               # True from {Name:0}

def extract_placeholders_with_limits(
    template: str
) -> Dict[str, PlaceholderInfo]:
    """
    Extract placeholders and their options from template.

    Args:
        template: Prompt template with placeholders

    Returns:
        Dict of placeholder name → PlaceholderInfo

    Syntax supported:
        {Name}              → All variations
        {Name:N}            → N random variations
        {Name:0}            → Suppress placeholder
        {Name:#|1|5|22}     → Specific indices
        {Name:$P}           → Priority P
        {Name:N$P}          → Limit + priority
        {Name:#|1|5$P}      → Indices + priority

    Examples:
        template = "{Expression:5}, {Angle:#|1|3$10}, {Lighting:0}"

        Returns:
            {
                "Expression": PlaceholderInfo(
                    name="Expression",
                    limit=5,
                    indices=None,
                    priority=None,
                    suppress=False
                ),
                "Angle": PlaceholderInfo(
                    name="Angle",
                    limit=None,
                    indices=[1, 3],
                    priority=10,
                    suppress=False
                ),
                "Lighting": PlaceholderInfo(
                    name="Lighting",
                    limit=None,
                    indices=None,
                    priority=None,
                    suppress=True
                )
            }
    """
```

**Parsing Algorithm:**

```python
import re

def extract_placeholders_with_limits(template):
    # Regex pattern for placeholder syntax
    pattern = r'\{([A-Za-z_][A-Za-z0-9_]*)(?::([^}]+))?\}'

    placeholders = {}

    for match in re.finditer(pattern, template):
        name = match.group(1)
        options = match.group(2)

        info = PlaceholderInfo(
            name=name,
            limit=None,
            indices=None,
            priority=None,
            suppress=False
        )

        if options:
            # Parse options string
            # Example: "5$10" → limit=5, priority=10
            # Example: "#|1|5|22$8" → indices=[1,5,22], priority=8
            # Example: "0" → suppress=True

            if '$' in options:
                # Split on $ to get priority
                main_part, priority_str = options.split('$', 1)
                info.priority = int(priority_str)
            else:
                main_part = options

            if main_part == '0':
                # Suppress placeholder
                info.suppress = True
            elif main_part.startswith('#|'):
                # Index selection
                indices_str = main_part[2:]  # Remove #|
                info.indices = [int(i) for i in indices_str.split('|')]
            elif main_part:
                # Numeric limit
                info.limit = int(main_part)

        placeholders[name] = info

    return placeholders
```

---

### expand_nested_variations

```python
def expand_nested_variations(
    variation_value: str
) -> List[str]:
    """
    Expand nested {|option1|option2} syntax.

    Args:
        variation_value: String possibly containing {|...}

    Returns:
        List of all expanded combinations

    Syntax:
        {|option1|option2|option3}

    Rules:
        - Empty option always included (allows "with" or "without")
        - Multiple {|...} generate all combinations

    Examples:
        # Single nested variation
        "standing,{|arms crossed|hands in pockets}"
        →
        [
            "standing",
            "standing,arms crossed",
            "standing,hands in pockets"
        ]

        # Multiple nested variations
        "running,{|fast},{|motion blur}"
        →
        [
            "running",
            "running,fast",
            "running,motion blur",
            "running,fast,motion blur"
        ]

        # Complex example
        "pose,{|mod1},{|mod2|mod3}"
        →
        [
            "pose",
            "pose,mod1",
            "pose,mod2",
            "pose,mod3",
            "pose,mod1,mod2",
            "pose,mod1,mod3"
        ]
    """
```

**Implementation:**

```python
import re
import itertools

def expand_nested_variations(variation_value):
    # Find all {|...} patterns
    pattern = r'\{\|([^}]*)\}'
    matches = list(re.finditer(pattern, variation_value))

    if not matches:
        # No nested variations
        return [variation_value]

    # Extract all option groups
    option_groups = []
    for match in matches:
        options_str = match.group(1)
        # Split on | and add empty option
        options = [''] + options_str.split('|')
        option_groups.append(options)

    # Generate all combinations
    all_combinations = itertools.product(*option_groups)

    results = []
    for combination in all_combinations:
        # Replace each {|...} with selected option
        result = variation_value
        for match, selected_option in zip(matches, combination):
            result = result.replace(match.group(0), selected_option, 1)

        # Clean up extra commas/spaces
        result = re.sub(r',\s*,', ',', result)
        result = re.sub(r',\s*$', '', result)
        result = result.strip()

        results.append(result)

    return results
```

---

### load_variations_for_placeholders

```python
def load_variations_for_placeholders(
    prompt_template: str,
    variation_files: Dict[str, Union[str, List[str]]]
) -> Dict[str, Dict[str, str]]:
    """
    Load only variations needed by placeholders in template.

    Args:
        prompt_template: Template with placeholders
        variation_files: Dict of placeholder → file path(s)

    Returns:
        Dict of placeholder → variations dict

    Features:
        - Supports multiple files per placeholder (merged)
        - Applies placeholder options (limits, indices)
        - Only loads files for placeholders in template
        - Expands nested variations

    Example:
        template = "{Expression:5}, {Angle:#|1|3}"
        variation_files = {
            "Expression": "expressions.txt",
            "Angle": ["angles_basic.txt", "angles_advanced.txt"],
            "Unused": "unused.txt"  # Not loaded
        }

        Returns:
            {
                "Expression": {
                    # 5 random expressions from file
                    "happy": "smiling",
                    "sad": "crying",
                    ...
                },
                "Angle": {
                    # Only indices 1 and 3 from merged files
                    "front": "front view",
                    "side": "side view"
                }
            }
    """
```

**Implementation:**

```python
def load_variations_for_placeholders(prompt_template, variation_files):
    # Extract placeholders with options
    placeholders = extract_placeholders_with_limits(prompt_template)

    loaded_variations = {}

    for placeholder_name, placeholder_info in placeholders.items():
        if placeholder_info.suppress:
            # Placeholder suppressed with :0
            continue

        if placeholder_name not in variation_files:
            raise ValueError(
                f"Placeholder '{placeholder_name}' has no variation file"
            )

        # Get file path(s)
        file_paths = variation_files[placeholder_name]
        if not isinstance(file_paths, list):
            file_paths = [file_paths]

        # Load and merge all files
        merged_variations = {}
        for file_path in file_paths:
            variations = load_variations_from_file(file_path)
            merged_variations.update(variations)

        # Apply options (limit, indices, priority)
        filtered_variations = apply_placeholder_options(
            merged_variations,
            placeholder_info
        )

        loaded_variations[placeholder_name] = filtered_variations

    return loaded_variations
```

---

### limit_variations

```python
def limit_variations(
    variations: Dict[str, str],
    limit: Optional[int] = None,
    indices: Optional[List[int]] = None
) -> Dict[str, str]:
    """
    Apply limit or index selection to variations.

    Args:
        variations: Full variation dict
        limit: Select N random variations (if provided)
        indices: Select specific indices (if provided)

    Returns:
        Filtered variation dict

    Priority:
        1. If indices provided: Use specific indices
        2. Elif limit provided: Select N random
        3. Else: Return all variations

    Examples:
        variations = {
            "v0": "value0",
            "v1": "value1",
            "v2": "value2",
            "v3": "value3",
            "v4": "value4"
        }

        # Limit to 2 random
        limit_variations(variations, limit=2)
        → {"v1": "value1", "v3": "value3"}  # Random selection

        # Specific indices
        limit_variations(variations, indices=[0, 2, 4])
        → {
            "v0": "value0",
            "v2": "value2",
            "v4": "value4"
        }
    """
```

---

### create_random_combinations

```python
def create_random_combinations(
    variations_dict: Dict[str, Dict[str, str]],
    num_combinations: int
) -> List[Dict[str, str]]:
    """
    Generate N random unique combinations.

    Args:
        variations_dict: Dict of placeholder → variations
        num_combinations: Number of combinations to generate

    Returns:
        List of combination dicts

    Features:
        - Guarantees uniqueness
        - Stops at total possible combinations if exceeded
        - Random but deterministic (can set seed externally)

    Example:
        variations_dict = {
            "Expression": {
                "happy": "smiling",
                "sad": "crying"
            },
            "Angle": {
                "front": "front view",
                "side": "side view"
            }
        }

        create_random_combinations(variations_dict, 3)
        →
        [
            {"Expression": "smiling", "Angle": "front view"},
            {"Expression": "crying", "Angle": "side view"},
            {"Expression": "smiling", "Angle": "side view"}
        ]
    """
```

---

## Variation File Formats

### Format 1: key→value

```
# Comments supported
happy→smiling, cheerful expression
sad→sad, melancholic look
angry→angry, frowning
```

**Parsed as:**
```python
{
    "happy": "smiling, cheerful expression",
    "sad": "sad, melancholic look",
    "angry": "angry, frowning"
}
```

### Format 2: number→value

```
1→front view
2→side view, profile
3→3/4 view
4→back view
```

**Parsed as:**
```python
{
    "frontView": "front view",
    "sideViewProfile": "side view, profile",
    "34View": "3/4 view",
    "backView": "back view"
}
```

### Format 3: value only

```
realistic
anime style
oil painting
watercolor
```

**Parsed as:**
```python
{
    "realistic": "realistic",
    "animeStyle": "anime style",
    "oilPainting": "oil painting",
    "watercolor": "watercolor"
}
```

### Format 4: Nested variations

```
standing
sitting
running,{|looking back|arms pumping}
jumping,{|legs bent},{|arms up|reaching}
```

**Parsed as:**
```python
{
    "standing": "standing",
    "sitting": "sitting",
    "running_0": "running",
    "running_1": "running,looking back",
    "running_2": "running,arms pumping",
    "jumping_0": "jumping",
    "jumping_1": "jumping,legs bent",
    "jumping_2": "jumping,arms up",
    "jumping_3": "jumping,legs bent,arms up",
    "jumping_4": "jumping,reaching",
    "jumping_5": "jumping,legs bent,reaching"
}
```

---

## Placeholder Syntax Reference

| Syntax | Meaning | Example |
|--------|---------|---------|
| `{Name}` | All variations | `{Hair}` |
| `{Name:N}` | N random variations | `{Hair:5}` |
| `{Name:0}` | Suppress placeholder | `{Hair:0}` |
| `{Name:#\|1\|5}` | Specific indices | `{Hair:#\|1\|5\|22}` |
| `{Name:$P}` | Priority P | `{Hair:$3}` |
| `{Name:N$P}` | Limit + priority | `{Hair:10$5}` |
| `{Name:#\|1\|5$P}` | Indices + priority | `{Hair:#\|1\|5$8}` |

---

## Usage Examples

### Load Single File

```python
from CLI.variation_loader import load_variations_from_file

variations = load_variations_from_file("expressions.txt")

for key, value in variations.items():
    print(f"{key}: {value}")
```

### Load for Template

```python
from CLI.variation_loader import load_variations_for_placeholders

template = "{Expression:5}, {Angle:#|1|3}, beautiful"

variation_files = {
    "Expression": "expressions.txt",
    "Angle": "angles.txt"
}

loaded = load_variations_for_placeholders(template, variation_files)

print(f"Expression variations: {len(loaded['Expression'])}")  # 5
print(f"Angle variations: {len(loaded['Angle'])}")            # 2
```

### Extract Placeholders

```python
from CLI.variation_loader import extract_placeholders_with_limits

template = "{Hair:10$5}, {Expression:#|1|5|22}, {Background:0}"

placeholders = extract_placeholders_with_limits(template)

for name, info in placeholders.items():
    print(f"{name}:")
    print(f"  Limit: {info.limit}")
    print(f"  Indices: {info.indices}")
    print(f"  Priority: {info.priority}")
    print(f"  Suppress: {info.suppress}")
```

### Expand Nested Variations

```python
from CLI.variation_loader import expand_nested_variations

value = "running,{|fast|slow},{|motion blur}"

expanded = expand_nested_variations(value)

for v in expanded:
    print(v)

# Output:
# running
# running,fast
# running,slow
# running,motion blur
# running,fast,motion blur
# running,slow,motion blur
```

---

## Testing

Tests are located in:
- `tests/test_placeholder_options.py`
- `tests/test_nested_variations.py`
- `tests/test_multiple_files.py`

Run tests:
```bash
pytest tests/test_placeholder*.py tests/test_nested*.py -v
```

---

## Design Decisions

### Why Nested Variation Syntax?

**Chosen:** `{|option1|option2}` within variation files
**Alternative:** Separate files for each combination

**Rationale:**
- DRY: Define base + modifiers in one place
- Combinatorial explosion handled automatically
- Easy to add/remove options
- Clear structure: base,{|modifier}

### Why Empty Option Always Included?

**Chosen:** `{|opt1|opt2}` expands to `["", "opt1", "opt2"]`
**Alternative:** Only explicit options

**Rationale:**
- Allows "with" or "without" modifier
- Common use case: optional attributes
- Predictable behavior

### Why Multiple File Support?

**Chosen:** `{"Pose": ["file1.txt", "file2.txt"]}`
**Alternative:** Single file only

**Rationale:**
- Organize by category
- Modular reusability
- Easy to enable/disable categories
- Collaboration-friendly

---

## References

- **[Architecture](architecture.md)** - System overview
- **[Variation Files User Guide](../usage/variation-files.md)** - User documentation

---

**Last updated:** 2025-10-01
