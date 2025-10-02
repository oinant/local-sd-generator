# Phase 2 Implementation Prompt - Character Templates

## Context

La **Phase 1** du système de templating est terminée et commitée. Tu vas maintenant implémenter la **Phase 2 : Character Templates & Multi-field Expansion**.

## Ce qui existe déjà (Phase 1)

```
CLI/templating/
├── __init__.py           ✅ Exports publics
├── types.py              ✅ Dataclasses de base
├── loaders.py            ✅ Charge YAML variations
├── selectors.py          ✅ Parse [keys], [random:N], etc.
├── prompt_config.py      ✅ Charge .prompt.yaml
└── resolver.py           ✅ Résout prompts (combinatorial/random)

CLI/tests/templating/     ✅ 25 tests qui passent
```

**Fonctionnalités Phase 1 :**
- ✅ Variations YAML simples et avec clés
- ✅ Sélecteurs : `[happy,sad]`, `[random:5]`, `[range:1-10]`, `[1,5,8]`
- ✅ Modes : combinatorial, random
- ✅ Seeds : fixed, progressive, random

## Phase 2 - Objectifs

### 1. Character Templates

Permettre de définir des **personnages réutilisables** avec :
- Héritage depuis des templates de base
- Overrides de champs
- Structure hiérarchique

**Exemple d'usage cible :**
```yaml
# characters/emma.char.yaml
name: "Emma - Athletic Portrait"
implements: base/portrait_subject.char.template.yaml

overrides:
  appearance:
    age: "23 years old"
    hair: "long brown hair"

fields:
  identity:
    name: "Emma"
```

### 2. Multi-field Expansion

Un placeholder peut **étendre plusieurs champs simultanément** :

```yaml
# variations/ethnic_features.yaml
type: multi_field
variations:
  - key: african
    fields:
      skin: "dark skin"
      hair: "coily black hair"
      eyes: "dark brown eyes"
```

Quand on utilise `{ETHNICITY}`, ça remplace automatiquement `{skin}`, `{hair}`, `{eyes}`.

### 3. Syntaxe dans prompts

```yaml
prompt: |
  {CHARACTER with ethnicity=ETHNICITIES[african,asian]}
  {POSES[standing]}
```

## Architecture proposée

### Nouveaux fichiers à créer

```
CLI/templating/
├── character.py          # NEW - Chargement et résolution de characters
├── multi_field.py        # NEW - Multi-field expansion
├── types.py              # MODIFIÉ - Ajouter CharacterTemplate, CharacterConfig
└── resolver.py           # MODIFIÉ - Support {CHARACTER with ...}
```

### Nouvelles dataclasses (types.py)

```python
@dataclass
class CharacterTemplate:
    name: str
    type: str  # "template"
    fields: Dict[str, Dict[str, str]]  # Nested fields
    prompt_structure: Optional[str] = None

@dataclass
class CharacterConfig:
    name: str
    implements: Optional[str] = None  # Path to template
    overrides: Dict[str, Dict[str, str]] = field(default_factory=dict)
    fields: Dict[str, Dict[str, str]] = field(default_factory=dict)

@dataclass
class MultiFieldVariation(Variation):
    """Variation qui étend plusieurs champs."""
    fields: Dict[str, str] = field(default_factory=dict)
```

## Implémentation suggérée

### Étape 1 : Character Loading (character.py)

```python
def load_character_template(filepath: Path) -> CharacterTemplate:
    """Load a .char.template.yaml file."""
    # Parse YAML
    # Validate structure
    # Return CharacterTemplate

def load_character(filepath: Path, base_path: Path) -> CharacterConfig:
    """Load a .char.yaml file with inheritance."""
    # Load character YAML
    # If implements: load template
    # Apply overrides
    # Merge fields
    # Return CharacterConfig

def resolve_character_fields(character: CharacterConfig) -> Dict[str, str]:
    """Flatten nested character fields into placeholders."""
    # {"appearance.age": "23"} → {"appearance_age": "23"}
    # Ou garde structure imbriquée
```

### Étape 2 : Multi-field Expansion (multi_field.py)

```python
def is_multi_field_variation(variation_data: dict) -> bool:
    """Check if variation file is multi-field type."""
    return variation_data.get('type') == 'multi_field'

def load_multi_field_variations(filepath: Path) -> Dict[str, MultiFieldVariation]:
    """Load multi-field variation file."""
    # Parse YAML
    # For each variation:
    #   Create MultiFieldVariation with fields dict
    # Return dict of variations

def expand_multi_field(
    variation: MultiFieldVariation,
    character_fields: Dict[str, str]
) -> Dict[str, str]:
    """Expand multi-field variation into character fields."""
    # Copy character_fields
    # Update with variation.fields
    # Return merged dict
```

### Étape 3 : Syntaxe parser (selectors.py)

```python
def parse_character_with_syntax(placeholder_content: str) -> tuple:
    """
    Parse: CHARACTER with ethnicity=ETHNICITIES[african,asian]
    Return: (character_name, overrides_dict)

    overrides_dict = {
        "ethnicity": ("ETHNICITIES", "[african,asian]")
    }
    """
    # Regex pour capturer "CHARACTER with field=SOURCE[selector]"
    # Pattern: r'(\w+)\s+with\s+(.+)'
    # Parse overrides: field=SOURCE[selector]
```

### Étape 4 : Resolver intégration (resolver.py)

Modifier `resolve_prompt()` :
1. Détecter si un placeholder est un CHARACTER
2. Charger le character
3. Détecter les overrides avec multi-field
4. Appliquer les expansions
5. Générer les combinaisons comme avant

## Tests à créer

```python
# tests/templating/test_character.py
def test_load_character_template()
def test_load_character_with_implements()
def test_character_overrides()
def test_character_fields_resolution()

# tests/templating/test_multi_field.py
def test_is_multi_field_variation()
def test_load_multi_field_variations()
def test_expand_multi_field()

# tests/templating/test_character_integration.py
def test_character_in_prompt()
def test_character_with_multi_field_override()
def test_full_resolution_emma_example()
```

## Fixtures à créer

```
CLI/tests/templating/fixtures/
├── base/
│   └── portrait_subject.char.template.yaml
├── characters/
│   └── emma.char.yaml
└── variations/
    └── ethnic_features.yaml  # multi-field
```

## Ordre d'implémentation recommandé

1. **Character loading** (character.py)
   - Load template
   - Load character avec implements
   - Tests

2. **Multi-field** (multi_field.py)
   - Detection
   - Loading
   - Expansion
   - Tests

3. **Syntaxe parser** (selectors.py)
   - Parse `CHARACTER with ...`
   - Tests

4. **Resolver intégration** (resolver.py)
   - Detect characters
   - Apply multi-field
   - Generate combinations
   - Tests

5. **Demo fonctionnelle**
   - Créer fixtures complètes
   - Script demo Phase 2
   - Valider 3 ethnies × 2 poses = 6 variations

## Success Criteria

- [ ] Load character templates (.char.template.yaml)
- [ ] Load characters with implements
- [ ] Overrides fonctionnent
- [ ] Multi-field variations détectées et chargées
- [ ] Expansion multi-field appliquée
- [ ] Syntaxe `{CHARACTER with field=SOURCE}` parsée
- [ ] Résolution complète end-to-end
- [ ] Tests >15 nouveaux tests
- [ ] Demo fonctionnelle
- [ ] Documentation inline (docstrings)

## Exemple complet attendu

**Input:**
```yaml
# prompts/emma_variations.prompt.yaml
name: "Emma Ethnic Variations"
imports:
  CHARACTER: characters/emma.char.yaml
  ETHNICITIES: variations/ethnic_features.yaml
  POSES: variations/poses.yaml

prompt: |
  {CHARACTER with ethnicity=ETHNICITIES[african,asian]}
  {POSES[standing,sitting]}

generation:
  mode: combinatorial
```

**Output:**
```
6 variations (2 ethnies × 2 poses):

Variation 0 (seed 42):
  masterpiece, best quality
  Emma, 23 years old, athletic build
  dark skin, coily black hair, dark brown eyes
  standing

Variation 1 (seed 43):
  masterpiece, best quality
  Emma, 23 years old, athletic build
  dark skin, coily black hair, dark brown eyes
  sitting

Variation 2 (seed 44):
  [asian + standing]
...
```

## Documentation requise

- Mettre à jour le spec dans `docs/roadmap/next/templating-phase2-characters.md` au fur et à mesure
- Ajouter docstrings claires
- Créer `example_phase2_demo.py`
- Une fois terminé : déplacer spec vers `done/`

## Notes importantes

- **Backward compatibility** : Phase 1 doit continuer à fonctionner
- **Tests d'abord** : Créer les tests avant l'implémentation
- **Validation** : Valider la structure des fichiers YAML
- **Erreurs claires** : Messages d'erreur explicites

---

## Pour démarrer

1. Lis les specs complètes : `docs/roadmap/next/templating-phase2-characters.md`
2. Commence par créer les fixtures d'exemple
3. Implémente character.py avec les tests
4. Continue avec multi_field.py
5. Intègre dans resolver.py
6. Crée la demo finale

Prêt à implémenter la Phase 2 ? 🚀
