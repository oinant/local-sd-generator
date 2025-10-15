# Error Handling & Validation

**Status:** ✅ Implemented (2025-10-13)
**Component:** CLI / Template System V2.0
**Priority:** High

## Overview

The Template System V2.0 includes comprehensive validation to detect common errors early and provide clear, actionable error messages. This document describes all validation checks and their error messages.

## Philosophy

**Never fail silently.** Every error should:
1. Be detected as early as possible
2. Provide a clear explanation of what went wrong
3. Include actionable suggestions on how to fix it
4. Show examples of correct usage when applicable

## Validation Phases

### Phase 1: YAML Parsing
Validates that files are well-formed YAML with required fields.

**Location:** `loaders/yaml_loader.py`, `loaders/parser.py`

### Phase 2: Path Validation
Validates that all referenced files exist.

**Location:** `validators/validator.py`

### Phase 3: Type Validation
Validates field types and structure.

**Location:** `loaders/parser.py`

### Phase 4: Template Resolution Validation
Validates that placeholders can be resolved.

**Location:** `generators/generator.py`

## Common Errors & Solutions

### 1. Using `variations:` instead of `imports:`

**Error:**
```
ValueError: Invalid field in my_prompt.prompt.yaml:
V2.0 Template System uses 'imports:' field, not 'variations:'.
Please rename 'variations:' to 'imports:' in your YAML file.

Example:
  ✗ Wrong:
    variations:
      HairCut: path/to/haircuts.yaml
  ✓ Correct:
    imports:
      HairCut: path/to/haircuts.yaml
```

**Cause:** V1 used `variations:`, V2.0 uses `imports:` for consistency with the import system.

**Fix:** Replace `variations:` with `imports:` in your `.prompt.yaml` file.

**When detected:** During YAML parsing (early detection)

**File:** `loaders/parser.py:157-169`

---

### 2. Unresolved Placeholders

**Error:**
```
ValueError: Unresolved placeholders in template: EyeColor, Outfit
These placeholders are used in the prompt/template but have no
corresponding variations defined in 'variations:' or 'imports:' sections.
Available variations: HairCut, HairColor
```

**Cause:** You used `{PlaceholderName}` in your prompt but forgot to define it in the `imports:` section.

**Fix:**
1. Add the missing import to your `imports:` section:
   ```yaml
   imports:
     EyeColor: ../../variations/eyecolors.yaml
     Outfit: ../../variations/outfits.yaml
   ```
2. **OR** remove the placeholder from your prompt if it's not needed

**When detected:** During prompt generation (after template resolution)

**File:** `generators/generator.py:139-145`

**Note:** This validation prevents the infamous "silent fail" where the system would generate only 1 image instead of the requested 20.

---

### 3. Using `template:` in Prompt Files

**Error:**
```
ValueError: Invalid field in my_prompt.prompt.yaml:
Prompt files must use 'prompt:' field, not 'template:'.
Please rename 'template:' to 'prompt:' in your file.
```

**Cause:** `.prompt.yaml` files use `prompt:`, while `.template.yaml` files use `template:`.

**Fix:** Rename `template:` to `prompt:` in your prompt file.

**When detected:** During YAML parsing

**File:** `loaders/parser.py:149-154`

---

### 4. Missing `{prompt}` in Template Files

**Error:**
```
ValueError: Invalid template in base.template.yaml:
Template files must contain {prompt} placeholder.
This is the injection point for child content (Template Method Pattern).

Example:
  template: |
    masterpiece, {prompt}, detailed
```

**Cause:** Template files implement the Template Method Pattern and **must** include `{prompt}` as the injection point for child content.

**Fix:** Add `{prompt}` placeholder to your template string.

**When detected:** During template parsing

**File:** `loaders/parser.py:58-66`

---

### 5. Reserved Placeholders in Chunks

**Error:**
```
ValueError: Invalid template in my_chunk.chunk.yaml:
Chunks cannot use reserved placeholders: {prompt}, {negprompt}.
Reserved placeholders are only allowed in template files.
Chunks are reusable blocks composed into templates, not templates themselves.
```

**Cause:** Reserved placeholders (`{prompt}`, `{negprompt}`, `{loras}`) have special meaning in templates and cannot be used in chunks.

**Fix:** Remove reserved placeholders from your chunk template.

**When detected:** During chunk parsing

**File:** `loaders/parser.py:108-116`

---

### 6. Import File Not Found

**Error:**
```
ValidationError: File not found: ../../variations/missing.yaml
Location: my_prompt.prompt.yaml, field: imports.HairCut
```

**Cause:** The file path specified in `imports:` doesn't exist or is incorrect.

**Fix:**
1. Check the file path is correct (relative to the prompt file)
2. Verify the file exists at that location
3. Check for typos in the filename

**When detected:** During path validation (Phase 2)

**File:** `validators/validator.py:282-288`

---

### 7. Type Field Mismatch in Chunks

**Error:**
```
ValidationError: Type mismatch: child.chunk.yaml (positive)
cannot implement parent.chunk.yaml (negative)
```

**Cause:** When using `implements:`, child chunk must have the same `type:` as parent.

**Fix:** Ensure both parent and child chunks have the same `type:` field.

**When detected:** During inheritance validation (Phase 3)

**File:** `validators/validator.py:348-362`

---

## Validation Statistics Display

Since **2025-10-13**, the CLI displays variation statistics before generation to help detect configuration issues early.

### Example Output

```
╭─────────────────────── Detected Variations ───────────────────────╮
│   HairCut: 40 variations                                           │
│   HairColor: 87 variations (4 files merged)                        │
│   EyeColor: 12 variations                                          │
│   Outfit: 156 variations (8 files merged)                          │
│                                                                    │
│   Total combinations: 6,518,400                                    │
│   Generation mode: random                                          │
│   Will generate: 20 images                                         │
╰────────────────────────────────────────────────────────────────────╯
```

### What This Tells You

1. **Per-placeholder counts:** Quickly spot if a placeholder has 0 variations (missing import)
2. **Multi-source indicators:** Shows when variations are merged from multiple files
3. **Total combinations:** Understand the full combinatorial space
4. **Generation info:** Confirm mode (random/combinatorial) and image count

### Implementation

**File:** `cli.py:135-169`, `orchestrator.py:355-423`

**How it works:**
1. Extract all placeholders from template using regex
2. Count variations for each placeholder from `context.imports`
3. Detect multi-source imports by analyzing key prefixes (heuristic)
4. Calculate total combinatorial product
5. Display in Rich panel with color coding

## Best Practices

### 1. Run Validation Before Generation

Use the `validate` command to check your template before generating:

```bash
sdgen validate my_prompt.prompt.yaml
```

This runs all validation phases and reports issues without starting generation.

### 2. Check Statistics Panel

Always review the "Detected Variations" panel before starting a long generation batch. Look for:
- ❌ Missing placeholders (0 variations)
- ⚠️ Unexpectedly low variation counts
- ✅ Expected total combinations

### 3. Use Descriptive Placeholder Names

Good placeholder names make error messages more helpful:
- ✅ `{HairCut}`, `{FacialExpression}`, `{Outfit}`
- ❌ `{var1}`, `{x}`, `{temp}`

### 4. Keep Imports Organized

Group related imports together with comments:

```yaml
imports:
  # Character appearance
  HairCut: ../../variations/body/haircuts.yaml
  HairColor: ../../variations/body/haircolors.yaml
  EyeColor: ../../variations/body/eyecolors.yaml

  # Clothing
  Outfit: ../../variations/outfits/casual.yaml
  Shoes: ../../variations/outfits/shoes.yaml
```

## Testing Validation

### Unit Tests

Validation logic is tested in:
- `tests/v2/unit/test_validators.py` - Validation phase tests
- `tests/v2/unit/test_generators.py` - Generator validation tests
- `tests/templating/test_parser.py` - Parser validation tests

### Integration Tests

End-to-end validation is tested in:
- `tests/v2/integration/test_executor.py` - Full pipeline validation

Run validation tests:

```bash
cd CLI
python3 -m pytest tests/v2/unit/test_validators.py -v
python3 -m pytest tests/v2/unit/test_generators.py::test_unresolved_placeholders -v
```

## Error Message Guidelines (for Developers)

When adding new validation:

1. **Be specific:** Name the exact field and file where the error occurred
2. **Be actionable:** Tell the user how to fix it
3. **Show examples:** Include both wrong and correct usage
4. **Fail fast:** Detect errors as early as possible in the pipeline
5. **Collect errors:** When possible, collect all errors before failing (don't fail-fast if you can report multiple issues)

### Error Message Template

```python
raise ValueError(
    f"[What went wrong] in {source_file.name}: "
    f"[Detailed explanation]. "
    f"[How to fix it].\n"
    f"Example:\n"
    f"  ✗ Wrong:\n"
    f"    [incorrect code]\n"
    f"  ✓ Correct:\n"
    f"    [correct code]"
)
```

## Changelog

### 2025-10-13: Comprehensive Validation Update
- ✅ Added unresolved placeholder detection (`generator.py`)
- ✅ Added `variations:` vs `imports:` validation (`parser.py`)
- ✅ Added variation statistics display (`cli.py`, `orchestrator.py`)
- ✅ Improved error messages with examples
- ✅ Created this documentation

### Previous Validation Features
- ✅ Phase 1-5 validation pipeline (`validator.py`)
- ✅ Type compatibility checks for inheritance
- ✅ Path validation for imports
- ✅ Reserved placeholder validation

## References

- **Architecture:** [architecture.md](./architecture.md)
- **V2 Engine:** [v2-templating-engine.md](./v2-templating-engine.md)
- **Getting Started:** [../usage/getting-started.md](../usage/getting-started.md)
