# Next-Gen Templating System - Phase 2: Character Templates

**Status:** next
**Priority:** 6
**Component:** cli
**Created:** 2025-10-03
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

- [ ] Implémenter `character.py`
  - [ ] Loader pour `.char.template.yaml`
  - [ ] Loader pour `.char.yaml`
  - [ ] Résolution d'héritage (implements)
  - [ ] System d'overrides
  - [ ] Validation de structure

- [ ] Implémenter `multi_field.py`
  - [ ] Détection de type `multi_field` dans variations
  - [ ] Expansion de plusieurs champs simultanément
  - [ ] Fusion avec character fields

- [ ] Modifier `resolver.py`
  - [ ] Support syntaxe `{CHARACTER with field=SOURCE[selector]}`
  - [ ] Résolution de characters avant variations
  - [ ] Intégration multi-field expansion

- [ ] Tests
  - [ ] Tests character loading
  - [ ] Tests inheritance
  - [ ] Tests overrides
  - [ ] Tests multi-field expansion
  - [ ] Tests intégration complète

- [ ] Exemples
  - [ ] Template de base portrait
  - [ ] 2-3 characters d'exemple
  - [ ] Variations multi-field
  - [ ] Demo fonctionnelle

## Success Criteria

- [ ] Load character templates
- [ ] Héritage fonctionne correctement
- [ ] Overrides appliqués dans le bon ordre
- [ ] Multi-field expansion fonctionnel
- [ ] Syntaxe `{CHARACTER with ...}` parsée et résolue
- [ ] Tests >80% coverage
- [ ] Demo avec 3 ethnies × 2 poses = 6 variations
- [ ] Documentation technique complète

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

## Prochaines étapes après Phase 2

Phase 3 : Nested variations + Explain system
