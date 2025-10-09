# Next-Gen Templating System - Phase 2: Character Templates (Chunks)

**Status:** done ✅
**Priority:** 6
**Component:** cli
**Created:** 2025-10-03
**Completed:** 2025-10-08
**Depends on:** Phase 1 (done)

## Description

Implémentation du système de character templates permettant de définir des personnages réutilisables avec héritage et overrides. Support du multi-field expansion où un placeholder peut étendre plusieurs champs à la fois.

## Motivation

Actuellement (Phase 1), chaque prompt doit définir tous ses placeholders individuellement. Avec les character templates, on pourra :

1. **Définir un personnage une fois** et le réutiliser partout
2. **Hériter de templates de base** (ex: `portrait_subject.char.template.yaml`)
3. **Override des champs** pour créer des variations (ex: Emma brune vs Emma blonde)
4. **Multi-field expansion** : `{ETHNICITY}` → modifie `hair`, `skin`, `eyes` en même temps

## Implementation

### Architecture

```
CLI/templating/
├── character.py          # NEW: Chargement et résolution de characters
├── multi_field.py        # NEW: Multi-field expansion
└── resolver.py           # MODIFIÉ: Support des characters

templates/
├── base/
│   └── portrait_subject.char.template.yaml
├── characters/
│   ├── emma.char.yaml
│   └── athlete.char.yaml
└── variations/
    └── ethnic_features.yaml    # Multi-field variations
```

### Fonctionnalités à implémenter

#### 1. Character Templates

**Format `.char.template.yaml` :**
```yaml
name: "Portrait Subject Base"
type: template

fields:
  appearance:
    age: "25 years old"
    body_type: "athletic build"

  technical:
    quality: "masterpiece, best quality, highly detailed"
    composition: "centered, portrait"

prompt_structure: |
  {technical.quality}
  BREAK
  {appearance.age}, {appearance.body_type}
  BREAK
  {composition}
```

**Format `.char.yaml` :**
```yaml
name: "Emma - Athletic Portrait"
implements: base/portrait_subject.char.template.yaml

overrides:
  appearance:
    age: "23 years old"
    hair: "long brown hair"
    eyes: "green eyes"
    ethnicity: "{ETHNICITY}"  # Placeholder pour variations

fields:
  identity:
    name: "Emma"
    personality: "confident, cheerful"
```

#### 2. Multi-field Expansion

**Format `ethnic_features.yaml` :**
```yaml
version: "1.0"
type: multi_field

variations:
  - key: african
    fields:
      skin: "dark skin, ebony complexion"
      hair: "coily black hair"
      eyes: "dark brown eyes"
      features: "full lips, wide nose"

  - key: asian
    fields:
      skin: "light skin, porcelain complexion"
      hair: "straight black hair"
      eyes: "almond-shaped dark eyes"
      features: "delicate features"

  - key: caucasian
    fields:
      skin: "fair skin, pale complexion"
      hair: "wavy blonde hair"
      eyes: "blue eyes"
      features: "soft features"
```

#### 3. Usage dans prompts

**`prompts/emma_variations.prompt.yaml` :**
```yaml
name: "Emma - Ethnic Variations"

imports:
  CHARACTER: characters/emma.char.yaml
  ETHNICITIES: variations/ethnic_features.yaml
  POSES: variations/poses.yaml

prompt: |
  {CHARACTER with ethnicity=ETHNICITIES[african,asian,caucasian]}
  BREAK
  {POSES[standing,sitting]}

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 100
```

**Résultat attendu :**
```
3 ethnies × 2 poses = 6 variations

Variation 0:
  masterpiece, best quality, highly detailed
  BREAK
  Emma, 23 years old, athletic build
  dark skin, ebony complexion, coily black hair, dark brown eyes, full lips
  BREAK
  standing

Variation 1:
  [même structure avec asian]
...
```

## Tasks

- [x] Renommer `character` → `chunk` (plus clair, ce sont des blocs de texte réutilisables)
  - [x] Types: `CharacterTemplate` → `ChunkTemplate`, `CharacterConfig` → `Chunk`
  - [x] Fichier: `character.py` → `chunk.py`

- [x] Implémenter `chunk.py`
  - [x] Loader pour `.chunk.template.yaml` (backward compat avec `.char.template.yaml`)
  - [x] Loader pour `.chunk.yaml` (backward compat avec `.char.yaml`)
  - [x] Résolution de champs (template defaults → chunk values → additional fields)
  - [x] Rendering simple par text replacement
  - [x] 8 tests unitaires ✅

- [x] Implémenter `multi_field.py`
  - [x] Détection de type `multi_field` dans variations
  - [x] Loading de variations multi-field
  - [x] Expansion de plusieurs champs simultanément
  - [x] Fusion avec chunk fields (avec priorités)
  - [x] 8 tests unitaires ✅

- [x] Modifier `selectors.py`
  - [x] Parser syntaxe `{CHUNK with field=SOURCE[selector]}`
  - [x] Support multiple overrides
  - [x] 6 tests unitaires ✅

- [ ] Modifier `resolver.py` (TODO)
  - [ ] Détecter chunks dans imports
  - [ ] Résolution de chunks avec multi-field expansion
  - [ ] Intégration dans le flow combinatorial/random

- [ ] Tests d'intégration (TODO)
  - [ ] Test end-to-end avec fixture emma_variations.prompt.yaml
  - [ ] Validation : 2 ethnies × 2 poses = 4 variations

- [x] Exemples/Fixtures
  - [x] Template de base: `portrait_subject.char.template.yaml`
  - [x] Chunk: `emma.char.yaml`
  - [x] Variations multi-field: `ethnic_features.yaml`
  - [x] Prompt test: `emma_variations.prompt.yaml`

## Success Criteria

- [x] Load chunk templates ✅
- [x] Chunk field resolution avec priorités ✅
- [x] Multi-field expansion fonctionnel ✅
- [x] Syntaxe `{CHUNK with ...}` parsée ✅
- [x] Syntaxe `{CHUNK}` simple (sans "with") supportée ✅ (bonus!)
- [x] Intégration complète dans resolver.py ✅
- [x] 22 tests Phase 2 unitaires ✅
- [x] 5 tests end-to-end d'intégration ✅
- [x] Demo fonctionnelle avec architecture HassakuXL ✅
- [x] **Total : 66 tests Phase 2 passent** ✅

## Tests à implémenter

```python
def test_load_character_template()
def test_load_character_with_implements()
def test_character_overrides()
def test_multi_field_expansion()
def test_character_with_variations()
def test_character_in_prompt_resolution()
```

## Exemple de résolution

**Input:**
```yaml
CHARACTER: emma.char.yaml
  implements: portrait_subject.char.template.yaml
  overrides: age=23, ethnicity={ETHNICITIES}

ETHNICITIES: ethnic_features.yaml (multi_field)
  african: {skin: "dark", hair: "coily", eyes: "brown"}
```

**Résolution:**
1. Load template `portrait_subject.char.template.yaml`
2. Load character `emma.char.yaml`
3. Apply overrides from character
4. Detect `{ETHNICITIES}` placeholder
5. Load multi-field variations
6. For each ethnicity:
   - Expand all fields (skin, hair, eyes)
   - Merge into character
   - Generate final prompt

## Documentation

- Technical: `docs/cli/technical/character-templates.md` (à créer)
- Usage: `docs/cli/usage/character-system.md` (à créer)
- Examples: `CLI/examples/characters/` (à créer)

## Notes

**Backward compatibility:**
- Phase 1 continue de fonctionner tel quel
- Characters sont optionnels
- Anciens prompts sans characters fonctionnent encore

**Limitations Phase 2:**
- Pas de nested characters (un character ne peut pas référencer un autre)
- Pas de conditional fields (si X alors Y)
- Pas de computed fields (formules)

## Completion Summary

**Completed:** 2025-10-08
**Tests:** 66/66 passing ✅ (22 unit + 5 integration + 39 other)
**Files modified:**
- `CLI/src/templating/chunk.py` (new)
- `CLI/src/templating/multi_field.py` (new)
- `CLI/src/templating/selectors.py` (modified - chunk with syntax)
- `CLI/src/templating/resolver.py` (modified - dual chunk syntax support)
- `CLI/src/templating/types.py` (modified - new types)

**Files created:**
- `CLI/tests/templating/test_chunk.py` (8 tests)
- `CLI/tests/templating/test_multi_field.py` (8 tests)
- `CLI/tests/templating/test_selectors_chunk.py` (6 tests)
- `CLI/tests/templating/test_phase2_integration.py` (5 tests)

**Demo architecture created:**
- `/mnt/d/StableDiffusion/private-new/templates/` (HassakuXL templates)
- `/mnt/d/StableDiffusion/private-new/prompts/hassaku/test-templates/` (test prompts)

**Key commits:** (à ajouter manuellement lors du commit)

### Features Delivered

1. **Chunk System** - Reusable text templates with field inheritance
2. **Multi-field Expansion** - Single placeholder expands multiple fields
3. **Dual Syntax** - Support both `{CHUNK}` and `{CHUNK with field=SOURCE}`
4. **Hierarchical Templates** - Base template → Style → Framing → Prompt
5. **Full Integration** - Works with existing Phase 1 variations

### Known Limitations (deferred to Phase 3)

1. **Nested Placeholders**: Placeholders inside chunk fields are not resolved
   - Example: chunk has `body: "{BodyType}"` → `{BodyType}` stays literal
   - **Workaround**: Use overrides with `{CHUNK with body=BodyTypes}`

2. **Chunk → Chunk Inheritance**: Can't chain chunk implements chunk
   - Example: `Manga-FullBody` can't implement `Manga` which implements `Base`
   - **Workaround**: Flatten hierarchy (Manga-FullBody implements Base directly)

3. **No Conditionals**: Can't do `if rating == "nsfw" then outfit=NSFW_OUTFITS`
   - **Workaround**: Create separate prompt files per condition

4. **No Computed Fields**: Can't auto-compute lighting based on time_of_day
   - **Workaround**: Define fields explicitly

## Prochaines étapes après Phase 2

**Phase 3** : Nested variations + Explain system + Fix limitations above
