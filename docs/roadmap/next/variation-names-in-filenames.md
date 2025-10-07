# Variation Names in Filenames

**Status:** next
**Priority:** 5
**Component:** cli
**Created:** 2025-10-07

## Description

Enhance file naming to include both variation placeholder names AND their values/keys in filenames, making images instantly identifiable without opening them.

Currently: `042_Expression-smiling_Angle-frontView.png`
Proposed: `042_Expression-smiling_Angle-frontView.png` ← **Already implemented!**

Wait... let me check the actual current behavior vs the braindump request.

## Problem Statement

**From braindump:** "use variation names & variant keys in file name : {Session_name}_index_{variationName_variantKey}"

Looking at `output_namer.py:generate_image_filename()` (line 116-159):

**Current format:** `{index:03d}_{key1}-{value1}_{key2}-{value2}.png`
- Example: `042_Expression-smiling_Angle-frontView.png`

**Requested format:** `{Session_name}_index_{variationName_variantKey}`
- Example: `anime_test_042_Expression_smiling_Angle_frontView.png`?

## Analysis: What's the Real Request?

Two interpretations:

### Interpretation A: Include session name in EVERY filename
```
Current:  042_Expression-smiling_Angle-frontView.png
Proposed: anime_test_042_Expression-smiling_Angle-frontView.png
```

**Pros:**
- Files are unique even when moved out of session folder
- Easier to identify source session in mixed folders

**Cons:**
- Longer filenames
- Redundant info (files already in session folder)
- Harder to read at a glance

### Interpretation B: Use variation KEY instead of sanitized value
```
Current:  042_Expression-smiling_Angle-frontView.png
          (uses sanitized VALUE: "smiling", "front view" → "frontView")

Proposed: 042_Expression-2_Angle-5.png
          (uses KEY from variations file: key "2" → "smiling")
```

**Context:** Variation files use `key→value` format:
```
1→neutral face
2→smiling
3→angry
```

**Pros:**
- Shorter filenames (keys are usually 1-2 chars)
- Stable naming even if variation text changes
- Maps directly to variation file structure

**Cons:**
- Less human-readable (what is "Expression-2"?)
- Requires looking up keys in variations file
- Loses descriptive value

### Interpretation C: Both variations as separate components
```
Current:  042_Expression-smiling_Angle-frontView.png
Proposed: 042_Expression_smiling_Angle_frontView.png
```

Change separator from `-` to `_` between name and value?

## Recommended Interpretation: **Hybrid Approach**

Provide CONFIGURABLE format with multiple options:

```python
# In config or CLI args
filename_format: str = "index_variation"  # Options below

# Format options:
# 1. "index_only"
#    → 001.png, 002.png, 003.png

# 2. "index_variation" (current default)
#    → 001_Expression-smiling_Angle-frontView.png

# 3. "session_index_variation"
#    → anime_test_001_Expression-smiling_Angle-frontView.png

# 4. "index_variation_keys"
#    → 001_Expression-2_Angle-5.png

# 5. "custom"
#    → Custom template: "{session}_{index:03d}_{Expression}_{Angle}.png"
```

## Implementation Design

### 1. Update `output_namer.py`

Add new formatting modes:

```python
from enum import Enum

class FilenameFormat(Enum):
    """Filename format options"""
    INDEX_ONLY = "index_only"
    INDEX_VARIATION = "index_variation"  # Current default
    SESSION_INDEX_VARIATION = "session_index_variation"
    INDEX_VARIATION_KEYS = "index_variation_keys"
    CUSTOM = "custom"

def generate_image_filename(
    index: int,
    variation_dict: Optional[Dict[str, str]] = None,
    filename_keys: Optional[List[str]] = None,
    session_name: Optional[str] = None,  # NEW
    format_mode: FilenameFormat = FilenameFormat.INDEX_VARIATION,  # NEW
    custom_template: Optional[str] = None  # NEW for "custom" mode
) -> str:
    """
    Generate image filename with configurable format.

    Args:
        index: Image index (1-based)
        variation_dict: Dict of {placeholder: value} for this image
        filename_keys: List of keys to include in filename
        session_name: Session name (for format modes that include it)
        format_mode: Filename format option
        custom_template: Custom format string (if format_mode == CUSTOM)

    Returns:
        Formatted filename string
    """
    if format_mode == FilenameFormat.INDEX_ONLY:
        return f"{index:03d}.png"

    elif format_mode == FilenameFormat.INDEX_VARIATION:
        # Current behavior (backward compatible)
        return _format_index_variation(index, variation_dict, filename_keys)

    elif format_mode == FilenameFormat.SESSION_INDEX_VARIATION:
        session_prefix = sanitize_filename_component(session_name) if session_name else "session"
        base = _format_index_variation(index, variation_dict, filename_keys)
        return f"{session_prefix}_{base}"

    elif format_mode == FilenameFormat.INDEX_VARIATION_KEYS:
        # Use variation keys instead of values
        return _format_with_keys(index, variation_dict, filename_keys)

    elif format_mode == FilenameFormat.CUSTOM:
        return _format_custom(index, variation_dict, session_name, custom_template)

    else:
        raise ValueError(f"Unknown format mode: {format_mode}")
```

### 2. Update Configuration Files

#### YAML Config (for Phase 2 templating)
```yaml
output:
  filename_format: "session_index_variation"
  # OR
  filename_format: "custom"
  filename_template: "{session}_{index:03d}_{Expression}_{Angle}.png"
```

#### JSON Config (for legacy compatibility)
```json
{
  "output": {
    "filename_format": "index_variation",
    "filename_keys": ["Expression", "Angle"]
  }
}
```

### 3. Update CLI Arguments

```bash
# CLI flag for format selection
python template_cli.py prompt.yaml \
  --filename-format session_index_variation

# Or with custom template
python template_cli.py prompt.yaml \
  --filename-format custom \
  --filename-template "{session}_{index:04d}_{Expression}.png"
```

### 4. Backward Compatibility

- **Default format:** `index_variation` (current behavior)
- **No config changes needed** for existing users
- **Opt-in** to new formats via config or CLI args

## Format Examples

Given:
- Session: `anime_test_v2`
- Index: 42
- Variations: `{"Expression": "smiling", "Angle": "front view"}`
- Variation keys: `{"Expression": "2", "Angle": "5"}`
- `filename_keys: ["Expression", "Angle"]`

**Results:**

| Format | Output |
|--------|--------|
| `index_only` | `042.png` |
| `index_variation` | `042_Expression-smiling_Angle-frontView.png` |
| `session_index_variation` | `animeTestV2_042_Expression-smiling_Angle-frontView.png` |
| `index_variation_keys` | `042_Expression-2_Angle-5.png` |
| `custom: "{session}_{index:04d}"` | `anime_test_v2_0042.png` |

## Tasks

- [ ] Add `FilenameFormat` enum to `output_namer.py`
- [ ] Refactor `generate_image_filename()` to support multiple formats
- [ ] Implement format helper functions (`_format_index_variation`, `_format_with_keys`, etc.)
- [ ] Add `session_name` parameter to filename generation
- [ ] Update `batch_generator.py` to pass format config
- [ ] Add CLI arguments for format selection
- [ ] Update YAML config parser to read `filename_format` option
- [ ] Add unit tests for all 5 format modes (27 existing tests → ~50 tests)
- [ ] Add integration test with real generation
- [ ] Update documentation with format options and examples

## Success Criteria

- [ ] All 5 format modes generate correct filenames
- [ ] Default behavior unchanged (backward compatibility)
- [ ] Format configurable via YAML, JSON, and CLI args
- [ ] Unit tests cover all format edge cases
- [ ] Custom template supports placeholder substitution
- [ ] Documentation includes format examples and use cases

## Tests

**Unit tests** (`tests/output/test_output_namer.py`):
- ✅ Existing 27 tests continue to pass (default format)
- ✅ Test each format mode with typical variations
- ✅ Test format modes with empty variations
- ✅ Test format modes with missing keys
- ✅ Test custom template with valid/invalid placeholders
- ✅ Test session name sanitization in session formats

**Integration tests** (`tests/integration/test_filename_formats.py`):
- ✅ Generate batch with each format mode
- ✅ Verify filenames match expected format
- ✅ Test format selection via CLI args
- ✅ Test format selection via config file

## Edge Cases

1. **Session name with special chars:** `"My Test! Session"` → `"myTestSession"`
2. **Missing variation value:** Key in `filename_keys` but not in `variation_dict` → skip
3. **Custom template with invalid placeholder:** `"{NonExistent}"` → raise error or substitute empty?
4. **Very long filenames:** Session + index + 10 variations → exceeds 255 char limit → truncate
5. **Custom template without extension:** `"{index}"` → automatically append `.png`?

## Performance Impact

- **Negligible:** Format selection is simple string operations
- **No API calls or disk I/O**
- **~1-2ms per filename** (same as current implementation)

## Migration Guide

For users who want the **exact braindump format:**

```yaml
# In your prompt.yaml or config
output:
  filename_format: "session_index_variation"
  filename_keys:
    - Expression
    - Angle
```

Result: `animeTestV2_042_Expression-smiling_Angle-frontView.png`

Or for shorter variant keys format:

```yaml
output:
  filename_format: "index_variation_keys"
  filename_keys:
    - Expression
    - Angle
```

Result: `042_Expression-2_Angle-5.png`

## Future Enhancements

- **Dynamic templates with functions:**
  ```
  "{session}_{index:03d}_{Expression|upper}_{Angle|snake_case}.png"
  ```
- **Date/time in filename:**
  ```
  "{date:%Y%m%d}_{index:03d}_{Expression}.png"
  ```
- **Conditional parts:**
  ```
  "{session}_{index:03d}{_Expression if Expression else ''}.png"
  ```

## Priority Justification

**Priority 5** (Nice-to-have, useful enhancement):
- Not blocking any features
- Current naming is already functional
- Enhances organization and workflow
- Low implementation risk

## Effort Estimate

**Medium** (~4-5 hours):
- 1 hour: Implement format enum and helper functions
- 1 hour: Update batch generator and config parsing
- 1.5 hours: Write comprehensive tests
- 30 min: CLI argument handling
- 1 hour: Update documentation

## Related Features

- **SF-4**: Enhanced File Naming System (already implemented, this extends it)
- **Metadata**: Filenames should match metadata `variations_used` structure

## Documentation

After implementation:
- Update `/docs/cli/technical/file-naming.md` with format options
- Create `/docs/cli/usage/filename-customization-guide.md` with examples
- Add migration guide for users wanting specific formats
