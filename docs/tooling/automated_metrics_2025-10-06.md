# Automated Code Quality Metrics - CLI Module

**Date:** 2025-10-06
**Tools Used:** flake8, radon, vulture, bandit
**Scope:** `/mnt/d/StableDiffusion/local-sd-generator/CLI/`

---

## Summary

| Tool | Issues Found | Severity |
|------|--------------|----------|
| **flake8** | 105 style/lint issues | 🟠 Medium |
| **radon** | 1 very complex function (E) | 🔴 High |
| **vulture** | 1 unused variable | 🟢 Low |
| **bandit** | 1 security issue (+ test false positives) | 🟠 Medium |

**Overall Code Quality:** 🟡 **Good with improvements needed**

---

## Flake8 - Style & Linting (105 issues)

### Summary by Category

| Code | Count | Description | Priority |
|------|-------|-------------|----------|
| E402 | 15 | Module import not at top of file | 🟠 High |
| F541 | 27 | f-string without placeholders | 🟡 Low |
| E127/E128 | 37 | Continuation line indentation | 🟢 Trivial |
| F401 | 12 | Imported but unused | 🟡 Medium |
| E501 | 5 | Line too long (>120 chars) | 🟢 Trivial |
| W292 | 5 | No newline at end of file | 🟢 Trivial |
| Others | 4 | Various minor issues | 🟢 Trivial |

### Critical Issues

#### **E402 - Imports Not at Top** (15 instances)

**Priority:** 🔴 High - **MUST FIX**

Files affected:
- `config/config_loader.py` (lines 14, 15, 293)
- `execution/json_generator.py` (lines 14-18)
- `template_cli.py` (lines 24-26)
- `generator_cli.py` (lines 22-24)
- `example_phase1_demo.py` (line 13)

**Example from config_loader.py:**
```python
# Lines 11-14
sys.path.insert(0, str(Path(__file__).parent.parent))

from variation_loader import extract_placeholders  # ← E402
from config.config_schema import ValidationError   # ← E402
```

**Problem:**
- `sys.path.insert()` at line 12
- Imports at lines 14-15 (after sys.path manipulation)
- `import os` at line 293 (bottom of file!) ← **CRITICAL BUG**

**Fix:**
```python
# Move all imports to top
import json
import os  # ← Move from line 293
import sys
from pathlib import Path
from typing import List, Set, Optional

# Then do sys.path manipulation if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

# Then project imports
from variation_loader import extract_placeholders
from config.config_schema import ValidationError
```

#### **F401 - Unused Imports** (12 instances)

**Priority:** 🟡 Medium

```python
# config/config_loader.py:9
from typing import Set  # imported but unused

# config/config_loader.py:15
from config.config_schema import ValidationError  # imported but unused

# template_cli.py:26
from execution.json_generator import run_generation_from_config  # unused
```

**Fix:** Remove unused imports

#### **F541 - f-strings Without Placeholders** (27 instances)

**Priority:** 🟢 Low (style issue, not a bug)

```python
# Bad
print(f"Starting generation...")  # No {} placeholders

# Good
print("Starting generation...")
```

**Action:** Quick automated fix possible

---

## Radon - Cyclomatic Complexity

### Summary

- **Total blocks analyzed:** 106
- **Average complexity:** B (9.57) ← Good
- **Very complex (E):** 1 function ← **Critical**
- **Complex (D):** 4 functions ← Important
- **Moderate (C):** ~15 functions ← Acceptable

### Complexity Scale
- **A (1-5):** Simple ✅
- **B (6-10):** Moderate ✅
- **C (11-20):** Complex 🟡
- **D (21-30):** Very complex 🟠
- **E (31-40):** Extremely complex 🔴
- **F (41+):** Unmaintainable 💀

### Critical - Very Complex (E)

#### `templating/resolver.py:resolve_prompt()` - **Complexity: E** 🔴

```
F 213:0 resolve_prompt - E
```

**Lines:** 213-397 (185 lines!)
**Complexity:** ~35 (estimated)

**Responsibilities (violates SRP):**
1. Load imports from config
2. Parse prompt for placeholders and chunks
3. Resolve chunk with overrides
4. Resolve variation placeholders
5. Generate combinations (combinatorial/random)
6. Assign seeds (fixed/progressive/random)
7. Build final ResolvedVariation objects

**Impact:**
- ⬛ Impossible to unit test individual steps
- ⬛ Extremely difficult to maintain
- ⬛ High risk of bugs when modifying

**Recommendation:** REFACTOR IMMEDIATELY (see detailed plan in main review)

### Important - Complex (D)

#### 1. `template_cli.py:main()` - **Complexity: D**

```
F 202:0 main - D
```

**Lines:** 202-457 (255 lines)
**Complexity:** ~28

**Issue:** CLI main function doing too much

**Fix:** Extract logical sections into functions:
- `_load_and_validate_config()`
- `_initialize_client()`
- `_generate_manifest()`
- `_run_generation_loop()`

#### 2. `variation_loader.py:load_variations_for_placeholders()` - **Complexity: D**

```
F 414:0 load_variations_for_placeholders - D
```

**Complexity:** ~25

**Issue:** Complex file loading with multiple edge cases

#### 3. `templating/selectors.py:resolve_selectors()` - **Complexity: D**

```
F 92:0 resolve_selectors - D
```

**Complexity:** ~22

**Issue:** Multiple selector types with nested conditionals

**Note:** This complexity is somewhat justified given the feature's nature

---

## Vulture - Dead Code Analysis

### Results: ✅ **Excellent**

**Found:** 1 unused variable (100% confidence)

```
output/output_namer.py:69: unused variable 'variations_sample' (100% confidence)
```

**Analysis:**
- Very clean codebase
- No dead functions or classes
- Only 1 unused variable detected

**Action:** Remove `variations_sample` variable

---

## Bandit - Security Analysis

### Critical Issues

#### **B113 - Request Without Timeout** 🔴

**File:** `sdapi_client.py:177`
**Severity:** Medium
**Confidence:** Low

```python
# Line 177
response = requests.post(f"{self.api_url}/sdapi/v1/txt2img", json=payload)
```

**Problem:**
- No timeout specified
- Can hang indefinitely if server doesn't respond
- Blocks entire generation process

**Fix:**
```python
# Add timeout parameter
response = requests.post(
    f"{self.api_url}/sdapi/v1/txt2img",
    json=payload,
    timeout=30  # 30 seconds timeout
)
```

**Also check:**
- `sdapi_client.py:78` - `test_connection()` has timeout=5 ✅
- Other requests calls should have timeouts too

### False Positives (Tests)

**B108 - Hardcoded /tmp directory** (7 instances in tests)

All instances are in test files using `/tmp/` paths:
- `tests/integration/test_integration_phase2.py` (lines 204-206)
- `tests/integration/test_new_features.py` (line 134)
- `tests/test_config_loader.py` (line 47)
- `output/metadata_generator.py:315` (in example/docstring)

**Assessment:** ✅ Acceptable in test code

---

## Priority Action Items

### P1 - Critical (Fix Immediately)

1. **Fix import order bug** in `config_loader.py`
   - Move `import os` from line 293 to top
   - **Risk:** Code crashes if function called before line 293
   - **Effort:** 2 minutes

2. **Add timeout to API requests** in `sdapi_client.py`
   - Add `timeout=30` to `requests.post()` at line 177
   - **Risk:** Application hangs indefinitely
   - **Effort:** 5 minutes

### P2 - High Priority (This Week)

3. **Refactor `resolve_prompt()`** (complexity E)
   - Break into 6-7 smaller functions
   - **Effort:** 6-8 hours
   - **Impact:** Massive maintainability improvement

4. **Fix E402 import errors** (15 instances)
   - Reorganize imports in all affected files
   - **Effort:** 30 minutes

### P3 - Medium Priority (This Sprint)

5. **Remove unused imports** (12 instances)
   - Clean up F401 errors
   - **Effort:** 15 minutes

6. **Refactor complex functions** (D complexity)
   - `template_cli.py:main()`
   - `variation_loader.py:load_variations_for_placeholders()`
   - **Effort:** 4-6 hours total

### P4 - Low Priority (Backlog)

7. **Fix f-strings without placeholders** (27 instances)
   - Automated fix possible
   - **Effort:** 10 minutes

8. **Fix style issues** (indentation, newlines)
   - Run autopep8 or black
   - **Effort:** 5 minutes

---

## Comparison with Manual Review

| Aspect | Manual | Automated | Agreement |
|--------|--------|-----------|-----------|
| **resolve_prompt() complexity** | ⚠️ Very long (185 lines) | 🔴 E complexity | ✅ **Confirmed** |
| **Import order bug** | ⚠️ Found (config_loader.py:293) | 🔴 15× E402 | ✅ **Confirmed** |
| **Dead code** | ✅ Very little | ✅ 1 variable | ✅ **Confirmed** |
| **Security** | Not checked | 🟠 1 missing timeout | ✅ **New finding** |
| **Code duplication** | ⚠️ 2 instances found | N/A (not checked by tools) | - |
| **Overall quality** | 🟡 Good | 🟡 Good | ✅ **Confirmed** |

---

## Recommended Tool Configuration

Add to `CLI/pyproject.toml`:

```toml
[tool.flake8]
max-line-length = 120
exclude = [
    "tests",
    "__pycache__",
    "*.pyc",
    "private_generators",
    "example_*.py"
]
ignore = [
    "E128",  # continuation line under-indented (subjective)
    "E127",  # continuation line over-indented (subjective)
]

[tool.bandit]
exclude_dirs = ["/tests"]
skips = ["B108"]  # Skip hardcoded /tmp in tests

[tool.vulture]
min_confidence = 80
paths = ["CLI"]
exclude = ["tests/", "example_*.py"]
```

---

## Tool Usage Commands

```bash
# From project root

# Style checking
venv/bin/python3 -m flake8 CLI --exclude=tests,__pycache__,private_generators --max-line-length=120

# Complexity analysis
venv/bin/python3 -m radon cc CLI --exclude="tests,__pycache__,private_generators,example_*" -a -nb

# Dead code detection
cd CLI && ../venv/bin/python3 -m vulture . --min-confidence=80 | grep -v "tests/" | grep -v "example_"

# Security scan
venv/bin/python3 -m bandit -r CLI -ll -f txt

# All checks in one go
venv/bin/python3 -m flake8 CLI && \
venv/bin/python3 -m radon cc CLI -a && \
venv/bin/python3 -m bandit -r CLI -ll
```

---

## Next Steps

1. ✅ **Install tools** - Done (added to pyproject.toml)
2. ✅ **Fix P1 issues** - **COMPLETED 2025-10-06**
   - ✅ Import order fixed (`config_loader.py:293` → line 8)
   - ✅ Timeout added (`sdapi_client.py:177` → `timeout=300`)
3. 🔨 **Schedule P2 refactoring** - resolve_prompt() (8 hours) - **IN PROGRESS**
4. ⏭️ **Set up pre-commit hooks** - Run flake8 automatically
5. ⏭️ **Add to CI/CD** - Fail builds on critical issues

---

**Generated by:** Claude Code
**Report Version:** 1.0
