# Range Selector Implementation

**Status:** wip
**Priority:** 6
**Component:** cli (templating)
**Created:** 2025-01-20

## Description

Implémenter le sélecteur de range `[#i-j]` pour sélectionner un intervalle d'indices.

**Motivation :**
- Lisibilité : `[#0-10]` au lieu de `[#0,1,2,3,4,5,6,7,8,9,10]`
- Groupes logiques : Sélectionner facilement des catégories (ex: expressions positives #0-20, négatives #21-40)
- Déjà documenté (par erreur) mais non implémenté

## Use Cases

### Avant (verbose)
```yaml
# Sélectionner 11 expressions (0 à 10)
prompt: "{Expression[#0,1,2,3,4,5,6,7,8,9,10]}"
```

### Après (concis)
```yaml
# Même résultat, plus lisible
prompt: "{Expression[#0-10]}"
```

### Groupes logiques
```yaml
# variations/expressions.yaml organisé par catégories :
# Index 0-20: Positive expressions
# Index 21-40: Negative expressions
# Index 41-50: Neutral expressions

# Générer seulement avec expressions positives
prompt: "{Expression[#0-20]}"

# Générer seulement avec expressions négatives
prompt: "{Expression[#21-40]}"
```

### Character sheet par sections
```yaml
# variations/poses.yaml organisé :
# Index 0-9: Standing poses
# Index 10-19: Sitting poses
# Index 20-29: Action poses

# Character sheet standing only
prompt: "1girl, {Outfit}, {Pose[#0-9]}, {Expression}"
```

## Syntax Specification

### Format
```
[#start-end]
```

**Constraints :**
- `start` et `end` sont des entiers positifs
- `start <= end` (sinon erreur)
- Intervalle **inclusif** (start et end inclus)
- `end < nombre_variations` (sinon utilise max disponible)

### Examples
```yaml
[#0-5]      # Indices 0,1,2,3,4,5 (6 variations)
[#10-19]    # Indices 10 à 19 (10 variations)
[#0-0]      # Index 0 seulement (1 variation)
[#5-100]    # Si seulement 20 variations : indices 5-19
```

### Invalid Syntax
```yaml
[#5-2]      # ❌ start > end
[#-5]       # ❌ Pas de start
[#5-]       # ❌ Pas de end
[0-10]      # ❌ Manque préfixe #
```

## Implementation

### 1. Parser Modification

**File:** `packages/sd-generator-cli/sd_generator_cli/templating/resolvers/template_resolver.py`

**Location:** `_parse_selectors()` method (around line 666-674)

**Current code:**
```python
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

**New code:**
```python
# Index selector: #1,3,5 or #start-end (range)
if part.startswith('#'):
    index_str = part[1:]

    # Check for range syntax: start-end
    if '-' in index_str:
        try:
            start, end = index_str.split('-', 1)
            start_idx = int(start.strip())
            end_idx = int(end.strip())

            # Validate range
            if start_idx > end_idx:
                # Invalid range, ignore
                pass
            else:
                # Generate range (inclusive)
                indexes = list(range(start_idx, end_idx + 1))
                selector.indexes = indexes
        except ValueError:
            pass  # Ignore invalid range
    else:
        # Comma-separated indexes
        try:
            indexes = [int(i.strip()) for i in index_str.split(',')]
            selector.indexes = indexes
        except ValueError:
            pass  # Ignore invalid indexes
    continue
```

**Logic :**
1. Check if `#` prefix exists
2. If `-` in string → range mode
3. Split by `-`, parse start and end
4. Validate: `start <= end`
5. Generate `range(start, end+1)` (inclusive)
6. Fallback to comma-separated if range parsing fails

### 2. Data Model

**File:** `packages/sd-generator-cli/sd_generator_cli/templating/resolvers/template_resolver.py`

**Selector dataclass** (already supports this, no change needed):
```python
@dataclass
class Selector:
    """Represents a parsed selector."""
    limit: Optional[int] = None
    indexes: Optional[List[int]] = None  # ✅ Can store range result
    keys: Optional[List[str]] = None
    weight: int = 1
```

## Tasks

- [x] Write specification
- [ ] Implement parser modification
- [ ] Add unit tests
  - [ ] Test `[#0-5]` → `[0,1,2,3,4,5]`
  - [ ] Test `[#10-19]` → `[10,...,19]`
  - [ ] Test `[#0-0]` → `[0]`
  - [ ] Test invalid `[#5-2]` → ignored
  - [ ] Test with weight `[#0-10;$5]`
- [ ] Add integration tests
  - [ ] Test range in combinatorial mode
  - [ ] Test range with actual variation files
- [ ] Update documentation
  - [ ] Add range section to selectors-reference.md
  - [ ] Add examples
  - [ ] Update syntax rules
- [ ] Update examples
  - [ ] Add example using range selector

## Success Criteria

- ✅ `{Expression[#0-10]}` generates 11 variations (indices 0 to 10 inclusive)
- ✅ `{Expression[#5-5]}` generates 1 variation (index 5)
- ✅ Invalid ranges are ignored (no crash)
- ✅ Range works with combinatorial mode
- ✅ Range works combined with weight `[#0-10;$5]`
- ✅ Out-of-bounds end is clamped to max available
- ✅ All tests pass

## Tests

### Unit Tests (`test_template_resolver.py`)

```python
def test_parse_range_selector(self):
    """Test parsing range selector [#0-5]."""
    resolver = TemplateResolver()
    selector = resolver._parse_selectors("#0-5")

    assert selector.limit is None
    assert selector.indexes == [0, 1, 2, 3, 4, 5]
    assert selector.keys is None
    assert selector.weight == 1

def test_parse_range_selector_single(self):
    """Test parsing range with same start/end [#5-5]."""
    resolver = TemplateResolver()
    selector = resolver._parse_selectors("#5-5")

    assert selector.indexes == [5]

def test_parse_range_selector_invalid(self):
    """Test parsing invalid range [#10-5] (start > end)."""
    resolver = TemplateResolver()
    selector = resolver._parse_selectors("#10-5")

    # Should be ignored, no indexes set
    assert selector.indexes is None

def test_parse_range_with_weight(self):
    """Test parsing range with weight [#0-10;$5]."""
    resolver = TemplateResolver()
    selector = resolver._parse_selectors("#0-10;$5")

    assert selector.indexes == list(range(11))  # 0 to 10
    assert selector.weight == 5

def test_apply_range_selector(self):
    """Test applying range selector."""
    variations = {f"item{i}": f"value{i}" for i in range(20)}
    selector = Selector(indexes=list(range(5, 10)))  # [5,6,7,8,9]

    result = resolver._apply_selector(variations, selector, {})

    assert len(result) == 5
    assert result == ["value5", "value6", "value7", "value8", "value9"]
```

### Integration Test

```python
def test_range_selector_in_template(self):
    """Test range selector in actual template."""
    context = ResolvedContext(
        imports={
            'Expression': {
                f'expr{i}': f'expression_{i}'
                for i in range(50)
            }
        },
        chunks={},
        parameters={}
    )

    template = "{Expression[#0-10]}"
    generator = PromptGenerator()
    generation = GenerationConfig(
        mode='combinatorial',
        seed=42,
        seed_mode='fixed',
        max_images=20
    )

    results = generator.generate_prompts(template, context, generation)

    # Should generate 11 combinations (indices 0-10)
    assert len(results) == 11

    # Check values
    for i, result in enumerate(results):
        assert f'expression_{i}' in result['prompt']
```

## Documentation Updates

### Add to selectors-reference.md

```markdown
### 2.5. Sélecteur de range `[#i-j]`

**Syntaxe** : `{Placeholder[#start-end]}`

**Effet** : Sélectionne un **intervalle d'indices** (inclusif)

**Exemples** :

{Expression[#0-10]}    # Indices 0 à 10 (11 variations)
{Expression[#20-29]}   # Indices 20 à 29 (10 variations)
{Expression[#5-5]}     # Index 5 seulement (1 variation)

**Use case - Groupes logiques** :

# variations/expressions.yaml organisé :
# Index 0-20: Positive expressions
# Index 21-40: Negative expressions

prompt: "{Expression[#0-20]}"  # Seulement positives

**Notes** :
- Intervalle inclusif (start et end inclus)
- start doit être <= end (sinon ignoré)
- Préfixe # obligatoire
- Si end > max disponible, utilise max
```

## Edge Cases

### Out-of-bounds end
```python
# 20 variations disponibles
selector = "#5-100"
# Résultat : indices 5-19 (clamped à 19)
```

**Behavior :** Utiliser `min(end, len(variations)-1)`

### Negative numbers
```python
selector = "#-5-10"
# Invalid, ignoré
```

**Behavior :** Ignorer (regex ne match pas)

### Multiple ranges (not supported)
```python
selector = "#0-5,10-15"
# Invalid, parsé comme keys
```

**Behavior :** Fallback to key selector (probablement ne marchera pas)

## Performance

**Impact :** Minimal
- Range parsing : O(1)
- Range generation : O(n) où n = end - start
- Typical n : 10-50 (très faible)

## Compatibility

**Breaking changes :** ❌ None
**Backward compatible :** ✅ Yes
- Existing selectors continue to work
- New syntax is additive

## Future Enhancements

**Multiple ranges :**
```yaml
[#0-5,10-15,20-25]  # 3 ranges combinés
```

**Step syntax :**
```yaml
[#0-20:2]  # Indices pairs : 0,2,4,...,20
```

**Negative indexing :**
```yaml
[#-10--1]  # 10 derniers indices
```

→ Hors scope pour cette implémentation

## Commits

- `feat(templating): Add range selector [#i-j] support`

## Documentation

- Usage: docs/cli/reference/selectors-reference.md
- Technical: Inline code comments

---

**Estimation :** 1-2h (simple feature)
**Risk :** Low (isolated change in parser)
