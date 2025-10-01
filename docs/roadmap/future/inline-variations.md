# Inline Variations

**Status:** 🔮 Future
**Priority:** Medium
**Complexity:** Low
**Estimated Effort:** 2-3 days

---

## Overview

Allow defining simple variations directly in JSON configuration files instead of requiring separate text files for every placeholder.

### Current State

All variations must be defined in external files:

```json
{
  "variations": {
    "Expression": "/absolute/path/to/expressions.txt",
    "Angle": "/absolute/path/to/angles.txt",
    "Style": "/absolute/path/to/styles.txt"
  }
}
```

### Desired State

Mix external files and inline arrays:

```json
{
  "variations": {
    "Expression": "/absolute/path/to/expressions.txt",
    "Angle": ["front view", "side view", "3/4 view", "back view"],
    "Style": ["anime", "realistic", "oil painting"]
  }
}
```

---

## Goals

1. **Convenience**: Define simple variations without creating files
2. **Portability**: Self-contained JSON configs for simple use cases
3. **Flexibility**: Mix inline and file-based variations
4. **Backward Compatibility**: Existing file-based configs continue working

---

## Non-Goals

1. ❌ Inline variations with nested variations syntax (too complex in JSON)
2. ❌ Replacing file-based system entirely
3. ❌ Supporting inline variations in Python API directly

---

## Use Cases

### 1. Quick Tests and Prototypes

```json
{
  "prompt": {
    "template": "portrait, {Expression}, {Lighting}"
  },
  "variations": {
    "Expression": ["smiling", "sad", "angry"],
    "Lighting": ["soft", "dramatic", "natural"]
  }
}
```

No need to create files for simple 3-4 value variations.

### 2. Boolean/Toggle Options

```json
{
  "variations": {
    "Background": ["", "blurred background", "bokeh"],
    "Detail": ["", "highly detailed", "ultra detailed"]
  }
}
```

Empty string effectively removes the element (like `{Placeholder:0}`).

### 3. Self-Contained Configs

Share a single JSON file without dependencies:

```json
{
  "name": "Simple Portrait Generator",
  "variations": {
    "Mood": ["happy", "serious", "melancholic"],
    "Lighting": ["soft light", "dramatic lighting", "golden hour"],
    "Style": ["realistic", "painterly", "cinematic"]
  }
}
```

Recipient can run immediately without fetching variation files.

### 4. Mixed Approach

Use files for large sets, inline for small ones:

```json
{
  "variations": {
    "Expression": "/path/to/100_expressions.txt",
    "Angle": "/path/to/50_angles.txt",
    "Toggle": ["", "with glasses"],
    "Quality": ["best quality", "masterpiece"]
  }
}
```

---

## Technical Design

### JSON Schema Extension

```json
{
  "variations": {
    "type": "object",
    "patternProperties": {
      ".*": {
        "oneOf": [
          {"type": "string"},
          {"type": "array", "items": {"type": "string"}}
        ]
      }
    }
  }
}
```

### Processing Logic

```python
def load_variations_for_placeholder(placeholder: str, source) -> List[str]:
    """Load variations from file path (string) or inline array."""

    if isinstance(source, str):
        # Existing file-based loading
        return load_variations_from_file(source)

    elif isinstance(source, list):
        # New inline array handling
        return [value for value in source if value.strip()]

    else:
        raise ValueError(f"Invalid variation source for {placeholder}: {type(source)}")
```

### Validation Rules

1. **String values**: Treated as file paths, must exist
2. **Array values**:
   - Must contain at least 1 non-empty string
   - Each element must be a string
   - Empty strings allowed (treated as placeholder suppression)
3. **No nested arrays**: `[["option1"], ["option2"]]` is invalid

---

## Implementation Plan

### Phase 1: Core Support (1 day)

**Tasks:**
- [ ] Update `config_schema.py` to accept string or array for variation sources
- [ ] Update `variation_loader.py` to handle inline arrays
- [ ] Add validation for inline array format
- [ ] Update tests to cover inline variations

### Phase 2: Feature Parity (1 day)

**Tasks:**
- [ ] Ensure inline variations work with all placeholder options:
  - [ ] Limiting: `{Expression:3}` with inline array
  - [ ] Index selection: `{Expression:#|0|2}` with inline array
  - [ ] Priority: `{Expression:$5}` with inline array
- [ ] Add tests for all combinations

### Phase 3: Documentation (0.5 days)

**Tasks:**
- [ ] Update JSON config schema documentation
- [ ] Add inline variation examples to `json-config-feature.md`
- [ ] Update `features.md` with inline variation examples
- [ ] Create sample configs demonstrating mixed approach

### Phase 4: Tooling (0.5 days)

**Tasks:**
- [ ] Update config validation error messages
- [ ] Add warnings for common mistakes (e.g., forgot quotes in array)
- [ ] Display inline variations in metadata.json

---

## Examples

### Simple Inline Config

```json
{
  "version": "1.0",
  "name": "Quick Portrait Test",

  "prompt": {
    "template": "portrait, {Expression}, {Quality}, beautiful"
  },

  "variations": {
    "Expression": ["smiling", "serious", "thoughtful"],
    "Quality": ["high quality", "masterpiece", "best quality"]
  },

  "generation": {
    "mode": "combinatorial",
    "seed_mode": "progressive",
    "seed": 42,
    "max_images": -1
  }
}
```

Result: 3 × 3 = 9 images

### Mixed Inline and Files

```json
{
  "variations": {
    "Character": "/path/to/characters.txt",
    "Expression": "/path/to/expressions.txt",
    "Background": ["", "forest", "city", "beach"],
    "TimeOfDay": ["morning", "noon", "evening", "night"]
  }
}
```

Large sets use files, small modifiers inline.

### Toggle Options

```json
{
  "variations": {
    "BasePrompt": ["portrait of a woman"],
    "Glasses": ["", "wearing glasses"],
    "Hat": ["", "wearing a hat"],
    "Smile": ["", "smiling"]
  }
}
```

All combinations including no accessories.

---

## Metadata Handling

### In metadata.json

Distinguish inline from file-based:

```json
{
  "variations": {
    "Expression": {
      "source_type": "inline",
      "count": 3,
      "values": ["smiling", "sad", "angry"]
    },
    "Angle": {
      "source_type": "file",
      "source_file": "/path/to/angles.txt",
      "count": 10,
      "values": ["front view", "side view", "..."]
    }
  }
}
```

---

## Advantages

1. **Lower Barrier to Entry**: No need to create files for simple tests
2. **Portability**: Single JSON file is self-contained
3. **Quick Iteration**: Modify variations directly in config
4. **Clear Intent**: Obvious what values are being used
5. **Version Control Friendly**: Changes visible in git diff

---

## Disadvantages

1. **Verbosity**: Large variation sets bloat JSON file
2. **No Nested Variations**: Can't use `{|option1|option2}` syntax inline
3. **Less Reusable**: Can't share variation sets across configs easily
4. **No Comments**: Can't annotate variations like in text files

---

## Best Practices

### When to Use Inline

✅ Use inline when:
- 2-5 simple values
- Testing/prototyping
- Boolean toggles (with/without)
- Self-contained one-off configs

### When to Use Files

✅ Use files when:
- 10+ variations
- Reusable across multiple configs
- Need comments/documentation
- Using nested variations `{|...}`
- Collaborative variation libraries

### Recommended Pattern

```json
{
  "variations": {
    // Large, reusable sets → files
    "Expression": "/shared/variations/expressions.txt",
    "Pose": "/shared/variations/poses.txt",

    // Small, config-specific → inline
    "Quality": ["masterpiece", "best quality"],
    "Background": ["", "blurred background"]
  }
}
```

---

## Migration Path

### Existing Configs

No changes required. File-based variations continue working.

### Conversion Tool

Optional utility to extract inline variations to files:

```bash
python tools/extract_inline_variations.py config.json --output-dir variations/
```

Creates files and updates config to reference them.

---

## Future Enhancements

### Inline Nested Variations (Complex)

Support limited nesting in JSON:

```json
{
  "variations": {
    "Pose": [
      "standing",
      {
        "base": "running",
        "modifiers": ["looking back", "arms pumping"]
      }
    ]
  }
}
```

Expands to: `standing`, `running`, `running, looking back`, `running, arms pumping`

**Status:** Deferred (adds significant complexity)

### Variable References

Reference other variations in inline arrays:

```json
{
  "variations": {
    "Character": ["Emma", "Sarah"],
    "Greeting": ["Hello ${Character}", "Hi ${Character}"]
  }
}
```

**Status:** Deferred (requires variable substitution system)

---

## Success Criteria

- ✅ JSON configs support both string and array variation sources
- ✅ Inline arrays work with all placeholder options (limit, index, priority)
- ✅ Validation catches malformed inline arrays
- ✅ Metadata distinguishes inline from file-based
- ✅ Documentation includes inline variation examples
- ✅ Backward compatibility: existing file-based configs unchanged

---

## Dependencies

- Depends on: JSON Config System (SF-1, SF-3)
- Blocks: None
- Related: Random Non-Combinatorial Placeholders (both enhance variation system)

---

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-01 | Claude | Initial specification |
