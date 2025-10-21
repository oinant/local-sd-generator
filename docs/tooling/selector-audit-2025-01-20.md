# Selector Audit Report - Documentation vs Implementation

**Date:** 2025-01-20
**Component:** Template System V2.0 Selectors
**Status:** 🔴 CRITICAL - Documentation contains false information

---

## Executive Summary

**Finding:** The selector documentation (`docs/cli/reference/selectors-reference.md`) contains **incorrect syntax** and **undocumented features**.

**Impact:**
- Users following the documentation will write **non-functional templates**
- Weight selector syntax is completely wrong (`[weight:W]` vs `[$W]`)
- Critical feature (weight 0) is **not documented**
- Features claimed in docs (`[random:N]`, `[#i-j]`) **do not exist**

**Priority:** 🔴 **P1 - CRITICAL** (blocks users from using core features)

---

## Detailed Findings

### 1. Weight Selector - WRONG SYNTAX ❌

| Aspect | Documentation | Implementation | Status |
|--------|--------------|----------------|--------|
| **Syntax** | `[weight:W]` | `[$W]` | ❌ **WRONG** |
| **Example** | `{Outfit[weight:2]}` | `{Outfit[$2]}` | ❌ **WRONG** |
| **Code location** | - | `template_resolver.py:658-664` | - |

**Evidence from code:**
```python
# template_resolver.py:658-664
# Weight selector: $8
if part.startswith('$'):
    try:
        selector.weight = int(part[1:])
    except ValueError:
        pass  # Ignore invalid weight
    continue
```

**Evidence from tests:**
```python
# test_generator.py
template = "{Outfit[$2]}, {Angle[$10]}"  # ✅ Real syntax
template = "{Color[$2]}, {Quality[$0]}"  # ✅ Real syntax
```

**Evidence from examples:**
- ❌ No examples use `[weight:W]` (because it doesn't work!)
- ✅ All test files use `[$W]`

---

### 2. Weight Zero - NOT DOCUMENTED ❌

| Feature | Documentation | Implementation | Status |
|---------|--------------|----------------|--------|
| **Weight 0** | ❌ Not mentioned | ✅ Fully implemented | ❌ **MISSING** |
| **Behavior** | - | Exclude from combinatorial loops | - |
| **Tests** | - | 2 unit tests + integration | - |

**What weight 0 does:**

In combinatorial mode:
- `weight > 0` → Variable in nested loops (multiplication)
- `weight = 0` → Variable **excluded** from loops, selected **randomly per image**

**Use case:**
```yaml
# Problem: 5 Outfits × 3 Angles × 100 HairColors = 1500 images
# Solution: HairColor[$0] to avoid combinatorial explosion

prompt: "{Outfit[$2]}, {Angle[$10]}, {HairColor[$0]}"

# Result: 15 images (5×3), HairColor random each time
```

**Evidence from tests:**
```python
# test_generator.py:132-161
def test_combinatorial_weight_zero_excluded(self):
    """Test that weight $0 excludes variable from combinatorial."""
    template = "{Color[$2]}, {Quality[$0]}"

    # 2 colors × 2 qualities
    results = generator.generate_prompts(...)

    # ✅ Generates 2 images (not 4)
    assert len(results) == 2

    # ✅ Quality is random but present
    for r in results:
        assert 'Quality' in r['variations']
```

---

### 3. Phantom Features - DO NOT EXIST ❌

The documentation claims these selectors exist, but they **do not**:

#### 3.1. `[random:N]` selector

**Documentation claims:**
```markdown
### 5. Sélecteur random `[random:N]`
**Syntaxe** : `{Placeholder[random:N]}`
**Effet** : Tire N variations aléatoires (syntaxe alternative à `[N]`)
```

**Reality:**
- ❌ Code does NOT parse `random:N`
- ❌ No tests for `random:N`
- ❌ No examples use `random:N`
- ✅ Only `[N]` (plain number) works

**Parser code:**
```python
# template_resolver.py:676-679
# Limit selector: 15 (pure number)
if part.isdigit():
    selector.limit = int(part)
    continue
```

**No code for `random:` anywhere!**

#### 3.2. `[#i-j]` range selector

**Documentation claims:**
```markdown
### 4. Sélecteur de range `[#i-j]`
**Syntaxe** : `{Placeholder[#i-j]}`
**Effet** : Sélectionne un intervalle d'indices (inclusif)

Example: {Expression[#0-5]} → indices 0,1,2,3,4,5
```

**Reality:**
- ❌ Code does NOT parse range syntax
- ❌ No tests for range
- ❌ No examples use range

**Parser code:**
```python
# template_resolver.py:666-674
# Index selector: #1,3,5
if part.startswith('#'):
    index_str = part[1:]
    try:
        indexes = [int(i.strip()) for i in index_str.split(',')]
        selector.indexes = indexes
    except ValueError:
        pass  # Ignore invalid indexes
    continue
```

**Only parses comma-separated indexes, NOT ranges!**

---

## Implemented Selectors (Reality)

Based on code analysis, tests, and examples:

### ✅ 1. Limit Selector `[N]`

**Syntax:** `{Placeholder[N]}`
**Effect:** Select N random variations
**Code:** `template_resolver.py:676-679`
**Tests:** ✅ `test_parse_limit_selector`, `test_apply_limit_selector`
**Examples:** ❌ Not used in examples

**Example:**
```yaml
prompt: "{Expression[5]}"  # 5 random expressions
```

---

### ✅ 2. Index Selector `[#i,j,k]`

**Syntax:** `{Placeholder[#i,j,k]}`
**Effect:** Select specific indexes (0-based, comma-separated)
**Code:** `template_resolver.py:666-674`
**Tests:** ✅ `test_parse_index_selector`, `test_apply_index_selector`
**Examples:** ❌ Not used in examples

**Example:**
```yaml
# expressions.yaml has 10 items
prompt: "{Expression[#0,2,4]}"  # Items at index 0, 2, 4
```

**Notes:**
- Prefix `#` is **mandatory**
- Indexes are 0-based
- Out-of-bounds indexes are **skipped** (no error)

---

### ✅ 3. Key Selector `[key1,key2]`

**Syntax:** `{Placeholder[key1,key2,key3]}`
**Effect:** Select variations by key name
**Code:** `template_resolver.py:681-685`
**Tests:** ✅ `test_parse_key_selector`, `test_apply_key_selector`
**Examples:** ✅ Used in all examples!

**Example:**
```yaml
# variations/lighting.yaml
# natural_soft: soft natural lighting
# studio_rembrandt: dramatic rembrandt lighting
# cinematic: cinematic lighting

prompt: "{LIGHTING[natural_soft,cinematic]}"
```

**Detection logic:**
```python
# Key selector if contains comma OR starts with uppercase
if ',' in part or part[0].isupper():
    keys = [k.strip() for k in part.split(',')]
    selector.keys = keys
```

**Notes:**
- Most commonly used selector in practice
- Non-existent keys are **skipped** (no error)

---

### ✅ 4. Weight Selector `[$W]`

**Syntax:** `{Placeholder[$W]}`
**Effect:** Control loop order in combinatorial mode
**Code:** `template_resolver.py:658-664`
**Tests:** ✅ `test_parse_weight_selector`, `test_combinatorial_weight_zero_excluded`
**Examples:** ❌ Not used in examples

**Behavior:**
- **Lower weight** = outer loop (changes less often)
- **Higher weight** = inner loop (changes more often)
- **Weight 0** = excluded from loops (random per image) 🔥

**Example:**
```yaml
prompt: "{Outfit[$2]}, {Angle[$10]}, {HairColor[$0]}"

# Result:
# Image 1: Outfit=casual, Angle=front, HairColor=random
# Image 2: Outfit=casual, Angle=side, HairColor=random
# Image 3: Outfit=formal, Angle=front, HairColor=random
# ...
```

**Weight 0 use case:**
```yaml
# Problem: 5 Outfits × 3 Angles × 100 HairColors = 1500 images ❌
# Solution:
prompt: "{Outfit[$2]}, {Angle[$10]}, {HairColor[$0]}"
# Result: 15 images (5×3), HairColor random ✅
```

---

### ✅ 5. Combined Selectors `[selector1;selector2]`

**Syntax:** `{Placeholder[limit/index/keys;$weight]}`
**Effect:** Combine selection + weight
**Separator:** `;` (semicolon)
**Code:** `template_resolver.py:651-652`
**Tests:** ✅ Multiple tests
**Examples:** ❌ Not used in examples

**Examples:**
```yaml
{Expression[5;$10]}              # 5 random, weight 10
{Angle[#0,2,4;$0]}               # Indexes 0,2,4, weight 0 (random)
{Haircut[BobCut,Pixie;$5]}       # Keys, weight 5
```

**Notes:**
- Order doesn't matter: `[5;$10]` = `[$10;5]`
- Can combine limit/index/keys with weight
- Cannot combine limit + index + keys together

---

## Summary Table

| Selector | Documented Syntax | Real Syntax | Exists? | Tested? | Used in Examples? |
|----------|------------------|-------------|---------|---------|-------------------|
| **Limit** | `[N]` | `[N]` | ✅ | ✅ | ❌ |
| **Index** | `[#i,j,k]` | `[#i,j,k]` | ✅ | ✅ | ❌ |
| **Keys** | `[key1,key2]` | `[key1,key2]` | ✅ | ✅ | ✅ |
| **Weight** | `[weight:W]` ❌ | `[$W]` ✅ | ✅ | ✅ | ❌ |
| **Weight 0** | ❌ Not documented | `[$0]` | ✅ | ✅ | ❌ |
| **Random** | `[random:N]` ❌ | - | ❌ | ❌ | ❌ |
| **Range** | `[#i-j]` ❌ | - | ❌ | ❌ | ❌ |
| **Combined** | ❌ Not documented | `[sel;$W]` | ✅ | ✅ | ❌ |

**Legend:**
- ✅ Yes / Correct
- ❌ No / Wrong / Missing

---

## Issues by Priority

### 🔴 P1 - CRITICAL (Blocks users)

1. **Weight selector syntax is completely wrong**
   - Doc: `[weight:W]`
   - Real: `[$W]`
   - Impact: Users cannot use combinatorial mode properly

2. **Weight 0 not documented**
   - Critical feature for avoiding combinatorial explosion
   - Users will generate thousands of unnecessary images

### 🟠 P2 - HIGH (Misleading)

3. **Phantom features documented**
   - `[random:N]` does not exist
   - `[#i-j]` range does not exist
   - Users will try to use them and fail

4. **Combined selectors not documented**
   - Feature exists and works (`[5;$10]`)
   - Users don't know they can combine selectors

### 🟡 P3 - MEDIUM (Incomplete)

5. **Examples don't demonstrate all features**
   - Only key selector is used in examples
   - No examples for limit, index, weight

---

## Recommended Actions

### Immediate (P1)

1. **Fix weight selector syntax**
   - Replace ALL occurrences of `[weight:W]` with `[$W]`
   - Update examples to use `[$W]`

2. **Document weight 0**
   - Add dedicated section explaining behavior
   - Add example showing combinatorial explosion prevention
   - Add to use cases table

### Short-term (P2)

3. **Remove phantom features**
   - Delete `[random:N]` section (doesn't exist)
   - Delete `[#i-j]` range section (doesn't exist)
   - Add note explaining only `[N]` and `[#i,j,k]` work

4. **Document combined selectors**
   - Add section on `;` separator
   - Show examples: `[5;$10]`, `[BobCut,Pixie;$0]`

### Medium-term (P3)

5. **Expand examples**
   - Add examples using limit selector
   - Add examples using index selector
   - Add examples using weight selectors
   - Add character sheet example with weights

6. **Add visual guide**
   - Diagram showing loop order with weights
   - Flowchart for weight 0 behavior
   - Decision tree for choosing selector

---

## Code Locations

**Parser implementation:**
- `packages/sd-generator-cli/sd_generator_cli/templating/resolvers/template_resolver.py`
  - `_parse_selectors()`: Lines 632-687
  - `_apply_selector()`: Lines 689-736
  - `extract_weights()`: Lines 738-762

**Tests:**
- `packages/sd-generator-cli/tests/unit/test_template_resolver.py`
  - Lines 19-85: Parser tests
  - Lines 101-149: Application tests
- `packages/sd-generator-cli/tests/unit/test_generator.py`
  - Lines 62-161: Weight and combinatorial tests

**Documentation:**
- `docs/cli/reference/selectors-reference.md` (❌ NEEDS UPDATE)

**Examples:**
- `packages/sd-generator-cli/sd_generator_cli/examples/prompts/*.yaml`

---

## Validation Checklist

Before marking this audit as complete:

- [ ] Fix weight selector syntax in docs
- [ ] Add weight 0 documentation
- [ ] Remove phantom features (random:N, range)
- [ ] Document combined selectors
- [ ] Add missing examples
- [ ] Verify all examples work
- [ ] Update quick reference table
- [ ] Cross-reference with code comments

---

**Report compiled by:** Claude Code
**Review status:** Pending human validation
**Next action:** Update `selectors-reference.md`
