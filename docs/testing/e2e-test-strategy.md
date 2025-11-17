# E2E Test Strategy - SD Generator CLI

**Document Version:** 1.0
**Last Updated:** 2025-11-14
**Status:** Design Document

---

## Context & Challenges

### Traditional Testing vs GPU Constraints

**Traditional Best Practices:**
- 1 test = 1 concept (perfect isolation)
- Fail-fast for quick feedback
- Parallel execution for speed

**SD Generator Reality:**
- GPU-intensive operations (time + energy + cost)
- Cannot parallelize (single GPU)
- Slow setup/teardown (model loading)
- CI/CD challenging (no GPU on standard agents)
- ~3-5s per image (256x256, 8 steps) minimum

### Our Approach: Composite Tests with Exhaustive Assertions

**Trade-off:** Sacrifice test "purity" for efficiency while maintaining diagnostic clarity

**Key Principle:** Maximize feature coverage per image generated

---

## Test Strategy

### 1. Composite Tests

**Instead of:**
```
Test 1: Import file (2 images)
Test 2: Import inline (2 images)
Test 3: Selector random (2 images)
→ 6 images, 3 runs
```

**We do:**
```
Test 1: Import modes combined (2 images)
  - Placeholder A: import file
  - Placeholder B: import inline dict
  - Placeholder C: import inline string
  - Placeholder D: selector [random:2]
  - Placeholder E: selector [limit:3]
→ 2 images, 1 run, tests 5 features!
```

**Result:** 66% reduction in images generated, same coverage

---

### 2. Exhaustive Assertions (Not Fail-Fast)

**Problem with fail-fast:**
```python
def test_features():
    assert manifest['status'] == 'completed'  # Stops here if fails
    assert len(manifest['images']) == 3       # Never reached
    assert 'Color' in variations              # Never reached
```

**Our approach - collect all failures:**
```python
def test_features():
    errors = []

    # Check everything
    if manifest.get('status') != 'completed':
        errors.append("❌ Status: expected 'completed', got 'ongoing'")

    if len(manifest.get('images', [])) != 3:
        errors.append("❌ Images: expected 3, got 2")

    if 'Color' not in variations:
        errors.append("❌ Import file: 'Color' missing")

    # ... check everything else ...

    # Report all failures at once
    if errors:
        pytest.fail(f"\n{len(errors)} errors:\n" + "\n".join(errors))
```

**Output example:**
```
Test failed with 8 errors:
❌ Status: expected 'completed', got 'ongoing'
❌ Images: expected 3, got 2
❌ Import inline dict: expected ['circle', 'square'], got ['circle']
❌ Selector [random:2]: expected 2 variations, got 5
❌ Selector [limit:3]: expected 3 variations, got 10
❌ Image 0: missing variations: {'Quality'}
❌ Image 1: file not found: /path/to/image_0002.png
❌ Image 1: missing variations: {'Style', 'Quality'}
```

**Benefits:**
- ✅ Complete diagnosis in 1 run (no need to re-run isolated tests)
- ✅ Immediate feedback on ALL broken features
- ✅ Pattern recognition (e.g., "all selectors broken")
- ✅ CI/CD friendly (single run even with multiple failures)

---

## Test Suites

### Suite 1: Basic Generation + Import Modes (1 run, 3 images)

**Features tested:**
- Import from YAML file
- Import inline dict
- Import inline string
- Import inline list
- Selector `[random:N]`
- Selector `[limit:N]`
- Basic generation (random mode)
- Manifest creation

**Template structure:**
```yaml
imports:
  Color: ./test_colors.yaml           # File import
  Shape:                               # Inline dict
    circle: "round, circular"
    square: "angular, geometric"
  Background: "white background"       # Inline string
  Mood: [happy, sad]                   # Inline list
  Style: ./test_styles.yaml            # For selector
  Quality: ./test_quality.yaml         # For selector

prompt: |
  {Color}, {Shape}, {Background}, {Mood},
  {Style[random:2]}, {Quality[limit:3]}

generation:
  mode: random
  seed: 42
  seed_mode: fixed
  max_images: 3

parameters:
  width: 256
  height: 256
  steps: 8
```

**Validations:**
```python
assert_variations(manifest, {
    'Color': 5,                        # 5 colors loaded from file
    'Shape': ['circle', 'square'],     # Exact inline values
    'Background': ['white background'], # Single string
    'Mood': ['happy', 'sad'],          # Inline list
    'Style': 2,                        # Limited by [random:2]
    'Quality': 3,                      # Limited by [limit:3]
})
```

**Time:** ~15s (3 images × 5s)

---

### Suite 2: Seed Modes (3 runs, 6 images)

**Run 1 - Fixed seed (2 images):**
```bash
sdgen -t test_composite.yaml -n 2
```
**Validates:** Both images have same seed

**Run 2 - Progressive seed (2 images):**
```bash
sdgen -t test_progressive.yaml -n 2
```
**Validates:** Seeds are [SEED, SEED+1]

**Run 3 - Seed sweep range (2 images):**
```bash
sdgen -t test_composite.yaml --seeds 100-101
```
**Validates:** Seeds are exactly [100, 101]

**Bonus:** Each run also tests all import modes from Suite 1

**Time:** ~30s (6 images × 5s)

---

### Suite 3: Advanced Features (1 run, 1 image)

**Features tested:**
- Template inheritance (`implements:`)
- Chunks (`{@ChunkName}`)
- Multiple file imports (merge)
- Placeholder removal (`[Remove]`)

**Template structure:**
```yaml
# child.prompt.yaml
implements: ./base.template.yaml

chunks:
  DetailChunk: ./chunks/details.chunk.yaml

imports:
  Outfit:
    - ./casual_clothes.yaml
    - ./formal_clothes.yaml
  Wings: [Remove]

prompt: |
  {@DetailChunk} wearing {Outfit}, {Wings}
```

**Validations:**
```python
# Inheritance
assert 'parameters' in manifest['snapshot']  # From parent
assert manifest['snapshot']['template'] == expected_merged_template

# Chunks
assert '@DetailChunk' not in manifest['snapshot']['resolved_template']
assert 'detailed' in manifest['snapshot']['resolved_template']  # Chunk expanded

# Multiple file imports
assert len(manifest['snapshot']['variations']['Outfit']) > 10  # Merged

# Removal
assert manifest['snapshot']['variations']['Wings'] == ['']  # Empty string
```

**Time:** ~5s (1 image × 5s)

---

### Suite 4: Architecture Parity (2 runs, 2 images)

**Run 1 - Legacy:**
```bash
sdgen -t test_parity.yaml -n 1 --seeds 42
```

**Run 2 - New:**
```bash
SDGEN_USE_NEW_ARCH=true sdgen -t test_parity.yaml -n 1 --seeds 42
```

**Validations:**
```python
# Compare manifests
assert legacy_manifest['snapshot']['variations'] == new_manifest['snapshot']['variations']
assert legacy_manifest['images'][0]['seed'] == new_manifest['images'][0]['seed']
assert legacy_manifest['images'][0]['applied_variations'] == new_manifest['images'][0]['applied_variations']

# Compare parameters
assert legacy_manifest['snapshot']['api_params'] == new_manifest['snapshot']['api_params']
```

**Time:** ~10s (2 images × 5s)

---

### Suite 5: Heavy Features (2 runs, 2 images)

**These remain isolated due to long generation time**

**Run 1 - Hires Fix (1 image):**
```bash
sdgen -t test_hires.yaml -n 1
```
**Validates:**
- Final resolution = `width × hr_scale`
- `enable_hr: true` in manifest parameters

**Run 2 - ADetailer (1 image):**
```bash
sdgen -t test_adetailer.yaml -n 1
```
**Validates:**
- `adetailer` config in manifest parameters
- Detectors present

**Time:** ~75s (hires ~30s + adetailer ~45s)

---

## Summary

| Suite | Runs | Images | Features Tested | Time |
|-------|------|--------|-----------------|------|
| 1. Basic + Imports | 1 | 3 | 8 features | ~15s |
| 2. Seed Modes | 3 | 6 | 3 seed modes + imports | ~30s |
| 3. Advanced | 1 | 1 | inheritance + chunks + removal | ~5s |
| 4. Parity | 2 | 2 | legacy vs new | ~10s |
| 5. Heavy | 2 | 2 | hires + adetailer | ~75s |
| **TOTAL** | **9** | **14** | **~15 features** | **~2m15s** |

**Comparison with traditional approach:**
- Traditional: 21 tests × 2 images = ~42 images (~3 min)
- Composite: 9 runs × ~1.5 images = ~14 images (~2 min)
- **Reduction:** 66% fewer images, same coverage

---

## Validation Categories

### 1. Manifest Structure
```python
errors.extend(collect_errors([
    (manifest.get('status') == 'completed',
     f"Status: expected 'completed', got '{manifest.get('status')}'"),

    (len(manifest.get('images', [])) == expected_count,
     f"Images count: expected {expected_count}, got {len(manifest.get('images', []))}"),

    ('snapshot' in manifest,
     "Snapshot: missing from manifest"),
]))
```

### 2. Variations
```python
def assert_variations(manifest, expected):
    """
    expected = {
        'Color': 5,                        # Expect count
        'Shape': ['circle', 'square'],     # Exact values
        'Background': ['white background'], # Single value
    }
    """
    errors = []
    variations = manifest.get('snapshot', {}).get('variations', {})

    for placeholder, expected_value in expected.items():
        if placeholder not in variations:
            errors.append(f"❌ Placeholder '{placeholder}': missing")
            continue

        actual = variations[placeholder]

        # Check count
        if isinstance(expected_value, int):
            if len(actual) != expected_value:
                errors.append(
                    f"❌ '{placeholder}': expected {expected_value} variations, "
                    f"got {len(actual)}"
                )

        # Check exact values
        elif isinstance(expected_value, list):
            if set(actual) != set(expected_value):
                errors.append(
                    f"❌ '{placeholder}': expected {expected_value}, got {actual}"
                )

    return errors
```

### 3. Generated Images
```python
for i, img_entry in enumerate(manifest.get('images', [])):
    # File exists
    if not img_entry.get('filename'):
        errors.append(f"❌ Image {i}: missing filename")
    else:
        img_path = session_dir / img_entry['filename']
        if not img_path.exists():
            errors.append(f"❌ Image {i}: file not found: {img_path}")

    # Applied variations
    applied = img_entry.get('applied_variations', {})
    expected_keys = {'Color', 'Shape', 'Background', ...}
    missing_keys = expected_keys - set(applied.keys())
    if missing_keys:
        errors.append(f"❌ Image {i}: missing variations: {missing_keys}")

    # Seed
    if img_entry.get('seed') != expected_seeds[i]:
        errors.append(
            f"❌ Image {i}: expected seed {expected_seeds[i]}, "
            f"got {img_entry.get('seed')}"
        )
```

### 4. Parameters
```python
params = manifest.get('snapshot', {}).get('api_params', {})

errors.extend(collect_errors([
    (params.get('width') == 256,
     f"Width: expected 256, got {params.get('width')}"),

    (params.get('steps') == 8,
     f"Steps: expected 8, got {params.get('steps')}"),

    (params.get('sampler') == 'Euler a',
     f"Sampler: expected 'Euler a', got {params.get('sampler')}"),
]))

# Hires Fix
if test_hires_fix:
    errors.extend(collect_errors([
        (params.get('enable_hr') is True,
         "Hires Fix: enable_hr should be True"),

        (params.get('hr_scale') == 2.0,
         f"Hires Fix: expected hr_scale=2.0, got {params.get('hr_scale')}"),
    ]))

# ADetailer
if test_adetailer:
    adetailer = params.get('adetailer', {})
    errors.extend(collect_errors([
        (adetailer.get('enabled') is True,
         "ADetailer: should be enabled"),

        (len(adetailer.get('detectors', [])) > 0,
         "ADetailer: should have detectors"),
    ]))
```

---

## Helper Functions

```python
# tests/e2e/helpers.py

def collect_errors(checks: list[tuple[bool, str]]) -> list[str]:
    """Collect all failed checks.

    Args:
        checks: List of (condition, error_message) tuples

    Returns:
        List of error messages for failed checks
    """
    return [f"❌ {msg}" for passed, msg in checks if not passed]


def load_manifest(session_dir: Path) -> dict:
    """Load manifest.json from session directory."""
    manifest_path = session_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def assert_variations(
    manifest: dict,
    expected: dict[str, int | list[str]]
) -> list[str]:
    """Validate variations in manifest.

    Args:
        manifest: Loaded manifest dict
        expected: Dict of placeholder → expected count or exact values
            Examples:
                {'Color': 5}                    # Expect 5 variations
                {'Shape': ['circle', 'square']} # Exact values

    Returns:
        List of error messages
    """
    errors = []
    variations = manifest.get('snapshot', {}).get('variations', {})

    for placeholder, expected_value in expected.items():
        if placeholder not in variations:
            errors.append(f"❌ Placeholder '{placeholder}': missing")
            continue

        actual = variations[placeholder]

        if isinstance(expected_value, int):
            if len(actual) != expected_value:
                errors.append(
                    f"❌ Placeholder '{placeholder}': "
                    f"expected {expected_value} variations, got {len(actual)}"
                )
        elif isinstance(expected_value, list):
            if set(actual) != set(expected_value):
                errors.append(
                    f"❌ Placeholder '{placeholder}': "
                    f"expected {expected_value}, got {actual}"
                )

    return errors


def assert_images_exist(
    manifest: dict,
    session_dir: Path,
    expected_count: int
) -> list[str]:
    """Validate that all expected images exist.

    Args:
        manifest: Loaded manifest dict
        session_dir: Session directory path
        expected_count: Expected number of images

    Returns:
        List of error messages
    """
    errors = []
    images = manifest.get('images', [])

    if len(images) != expected_count:
        errors.append(
            f"❌ Images count: expected {expected_count}, got {len(images)}"
        )

    for i, img_entry in enumerate(images):
        filename = img_entry.get('filename')
        if not filename:
            errors.append(f"❌ Image {i}: missing filename")
            continue

        img_path = session_dir / filename
        if not img_path.exists():
            errors.append(f"❌ Image {i}: file not found: {img_path}")

    return errors


def assert_seeds(
    manifest: dict,
    expected_seeds: list[int]
) -> list[str]:
    """Validate that seeds match expected values.

    Args:
        manifest: Loaded manifest dict
        expected_seeds: List of expected seeds (order matters)

    Returns:
        List of error messages
    """
    errors = []
    images = manifest.get('images', [])

    for i, (img_entry, expected_seed) in enumerate(zip(images, expected_seeds)):
        actual_seed = img_entry.get('seed')
        if actual_seed != expected_seed:
            errors.append(
                f"❌ Image {i}: expected seed {expected_seed}, got {actual_seed}"
            )

    return errors
```

---

## Test Template Example

```python
# tests/e2e/test_import_modes.py

import pytest
from pathlib import Path
from .helpers import (
    load_manifest,
    collect_errors,
    assert_variations,
    assert_images_exist,
)


def test_import_modes_composite(tmp_path):
    """Test all import modes in a single run (composite test)."""

    # 1. Run generation
    session_dir = run_generation(
        template="fixtures/test_import_modes.yaml",
        args=["-n", "3"],
        output_dir=tmp_path
    )

    # 2. Load manifest
    manifest = load_manifest(session_dir)
    errors = []

    # 3. Structural validation
    errors.extend(collect_errors([
        (manifest.get('status') == 'completed',
         f"Status: expected 'completed', got '{manifest.get('status')}'"),

        ('snapshot' in manifest,
         "Snapshot: missing from manifest"),
    ]))

    # 4. Validate variations (all import modes)
    errors.extend(assert_variations(manifest, {
        'Color': 5,                        # File import
        'Shape': ['circle', 'square'],     # Inline dict
        'Background': ['white background'], # Inline string
        'Mood': ['happy', 'sad'],          # Inline list
        'Style': 2,                        # Selector [random:2]
        'Quality': 3,                      # Selector [limit:3]
    }))

    # 5. Validate images
    errors.extend(assert_images_exist(manifest, session_dir, expected_count=3))

    # 6. Validate applied variations
    for i, img_entry in enumerate(manifest.get('images', [])):
        applied = img_entry.get('applied_variations', {})
        expected_keys = {'Color', 'Shape', 'Background', 'Mood', 'Style', 'Quality'}
        missing_keys = expected_keys - set(applied.keys())
        if missing_keys:
            errors.append(f"❌ Image {i}: missing variations: {missing_keys}")

    # 7. Report all failures
    if errors:
        pytest.fail(f"\n\nTest failed with {len(errors)} errors:\n" + "\n".join(errors))
```

---

## Running Tests

### Run all E2E tests
```bash
cd packages/sd-generator-cli
pytest tests/e2e/ -v
```

### Run specific suite
```bash
pytest tests/e2e/test_import_modes.py -v
```

### Run with detailed output
```bash
pytest tests/e2e/ -v -s
```

### Generate HTML report
```bash
pytest tests/e2e/ --html=report.html --self-contained-html
```

---

## CI/CD Integration

### Prerequisites
- GPU-enabled runner (or skip heavy tests)
- SD WebUI running on localhost:7860
- Model loaded

### GitHub Actions Example
```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: [self-hosted, gpu]  # Custom runner with GPU

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd packages/sd-generator-cli
          pip install -e .
          pip install pytest pytest-html

      - name: Start SD WebUI
        run: |
          # Start SD WebUI in background
          ./start_webui.sh &
          sleep 30  # Wait for model loading

      - name: Run E2E tests (fast suite)
        run: |
          cd packages/sd-generator-cli
          pytest tests/e2e/ -v -m "not slow" --html=report.html

      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: e2e-test-report
          path: packages/sd-generator-cli/report.html
```

### Test Markers
```python
# Mark slow tests (hires fix, adetailer)
@pytest.mark.slow
def test_hires_fix():
    ...

# Run only fast tests in CI
pytest tests/e2e/ -m "not slow"
```

---

## Benefits Summary

| Aspect | Traditional Approach | Our Approach |
|--------|---------------------|--------------|
| Images per test suite | ~42 images | ~14 images |
| Total time | ~3 min | ~2 min |
| Diagnostic clarity | Single failure | All failures reported |
| Re-run needed | Often yes | Rarely |
| CI/CD feasibility | Challenging | Manageable |
| Feature coverage | Same | Same |
| Test isolation | High | Medium (intentional) |

---

## Future Improvements

1. **Parallel GPU execution** (if multiple GPUs available)
2. **Cached model loading** (persistent SD WebUI instance)
3. **Image comparison** (pixel-level diff for regression)
4. **Performance benchmarks** (track generation time)
5. **Manifest schema validation** (JSON Schema)
