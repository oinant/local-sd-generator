# Next-Gen Templating System - Implementation Prompt

## Context

Tu vas implémenter un système de templating hiérarchique pour la génération de prompts Stable Diffusion. Ce système permet la réutilisation de configurations, l'héritage de caractéristiques, et la variation ciblée de paramètres.

## Documentation complète

Les spécifications détaillées se trouvent dans :
- `docs/roadmap/future/nextGenTemplating/README.md` - Vue d'ensemble
- `docs/roadmap/future/nextGenTemplating/01-hierarchical-character-templates.md`
- `docs/roadmap/future/nextGenTemplating/02-advanced-variation-selectors.md`
- `docs/roadmap/future/nextGenTemplating/03-multi-field-expansion.md`
- `docs/roadmap/future/nextGenTemplating/04-nested-variations.md`
- `docs/roadmap/future/nextGenTemplating/05-explain-debug-system.md`

## Phase actuelle : Phase 1 - Fondations (Priority 5-6)

### Objectifs de cette session

1. **Loader YAML avec backward compatibility**
   - Parser les fichiers `.yaml` de variations
   - Supporter les anciens fichiers `.txt`
   - Auto-détection du format

2. **Parser de sélecteurs de variations**
   - Syntaxe : `{SOURCE[selectors]}`
   - Types : `[random:N]`, `[key1,key2]`, `[range:N-M]`, `[1,5,8]`
   - Combinaisons multiples

3. **Système d'imports basique**
   - Bloc `imports:` dans les fichiers `.prompt.yaml`
   - Résolution des références
   - Validation basique

### Ce qu'on NE fait PAS encore

- ❌ Character templates (Phase 2)
- ❌ Multi-field expansion (Phase 2)
- ❌ Nested variations (Phase 3)
- ❌ Explain system (Phase 3)
- ❌ CLI complète (Phase 4)

### Approche

**Architecture minimale pour Phase 1 :**

```python
# Core modules à créer
src/templating/
├── __init__.py
├── loaders.py           # load_variations(), auto_detect_format()
├── selectors.py         # parse_selector(), resolve_selectors()
├── prompt_config.py     # PromptConfig class
└── resolver.py          # resolve_prompt()

# Tests
tests/templating/
├── test_loaders.py
├── test_selectors.py
└── test_resolver.py
```

**Workflow cible :**

```python
# Usage qu'on vise
from src.templating import load_prompt_config, resolve_prompt

config = load_prompt_config("prompts/test.prompt.yaml")
variations = resolve_prompt(config)

for variation in variations:
    print(variation.final_prompt)
    # Generate with SD API...
```

### Exemples à supporter

**Fichier de prompt minimal :**
```yaml
# prompts/simple_test.prompt.yaml
name: "Simple Test"

imports:
  EXPRESSIONS: variations/expressions.yaml
  POSES: variations/poses.yaml

prompt: |
  masterpiece, {EXPRESSIONS[happy,sad]}, {POSES[random:3]}

generation:
  mode: combinatorial
```

**Fichier de variations (nouveau format) :**
```yaml
# variations/expressions.yaml
version: "1.0"
variations:
  - key: happy
    value: "smiling, cheerful"
  - key: sad
    value: "crying, tears"
  - key: angry
    value: "frowning"
```

**Fichier de variations (ancien format) :**
```
# variations/expressions.txt
happy→smiling, cheerful
sad→crying, tears
angry→frowning
```

### Tests critiques à implémenter

```python
def test_load_yaml_variations():
    """Charge un fichier .yaml"""
    variations = load_variations("expressions.yaml")
    assert len(variations) == 3
    assert variations["happy"] == "smiling, cheerful"

def test_load_txt_variations():
    """Charge un fichier .txt (backward compat)"""
    variations = load_variations("expressions.txt")
    assert variations["happy"] == "smiling, cheerful"

def test_parse_selector_keys():
    """Parse [happy,sad]"""
    selector = parse_selector("[happy,sad]")
    assert selector.type == "keys"
    assert selector.keys == ["happy", "sad"]

def test_parse_selector_random():
    """Parse [random:5]"""
    selector = parse_selector("[random:5]")
    assert selector.type == "random"
    assert selector.count == 5

def test_parse_selector_range():
    """Parse [range:1-10]"""
    selector = parse_selector("[range:1-10]")
    assert selector.type == "range"
    assert selector.start == 1
    assert selector.end == 10

def test_parse_selector_combined():
    """Parse [happy,sad,random:3]"""
    selectors = parse_selector("[happy,sad,random:3]")
    assert len(selectors) == 2
    assert selectors[0].type == "keys"
    assert selectors[1].type == "random"

def test_resolve_simple_prompt():
    """Résout un prompt simple"""
    config = load_prompt_config("simple_test.prompt.yaml")
    variations = resolve_prompt(config)
    # happy,sad × 3 random poses = 2×3 = 6 variations
    assert len(variations) == 6
```

### Contraintes

1. **Simplicité** : Phase 1 = fondations solides, pas de sur-engineering
2. **Tests** : Coverage >80% minimum
3. **Backward compat** : Support des fichiers `.txt` existants
4. **Performance** : < 100ms pour résoudre un prompt avec 50 variations
5. **Validation** : Erreurs claires si syntaxe invalide

### Fichiers existants à ne PAS toucher

- `image_variation_generator.py` (ancien système)
- `variation_loader.py` (ancien système)
- Tout le code existant doit continuer à fonctionner

### Structure de données suggérée

```python
@dataclass
class Variation:
    key: str
    value: str
    weight: float = 1.0

@dataclass
class Selector:
    type: str  # "keys", "random", "range", "indices"
    keys: List[str] = field(default_factory=list)
    indices: List[int] = field(default_factory=list)
    count: Optional[int] = None
    start: Optional[int] = None
    end: Optional[int] = None

@dataclass
class PromptConfig:
    name: str
    imports: Dict[str, str]  # {EXPRESSIONS: "path/to/file.yaml"}
    prompt_template: str
    negative_prompt: str = ""
    generation_mode: str = "combinatorial"
    seed_mode: str = "progressive"
    seed: int = 42

@dataclass
class ResolvedVariation:
    index: int
    seed: int
    placeholders: Dict[str, str]  # {EXPRESSIONS: "happy", POSES: "standing"}
    final_prompt: str
```

### Ordre d'implémentation suggéré

1. **Loaders** (loaders.py)
   - `load_variations_yaml()`
   - `load_variations_txt()`
   - `load_variations()` avec auto-detect

2. **Selectors** (selectors.py)
   - `parse_selector()` pour un type à la fois
   - `resolve_selectors()` pour appliquer

3. **Prompt Config** (prompt_config.py)
   - `load_prompt_config()`
   - Validation basique

4. **Resolver** (resolver.py)
   - `resolve_prompt()` mode combinatorial
   - Génération des seeds

5. **Tests** pour chaque module

### Questions à anticiper

**Q: Où mettre le code ?**
A: `src/templating/` comme nouveau module

**Q: Comment gérer les placeholders dans le prompt ?**
A: Regex simple : `r'\{([A-Z_]+)(?:\[([^\]]+)\])?\}'`

**Q: Format interne des variations ?**
A: `Dict[str, Variation]` pour lookup O(1) par clé

**Q: Comment tester ?**
A: Créer des fixtures YAML/txt dans `tests/templating/fixtures/`

### Success criteria pour cette session

- [ ] Load variations from YAML
- [ ] Load variations from TXT (backward compat)
- [ ] Parse selectors : keys, random, range, indices
- [ ] Parse selectors : combinaisons
- [ ] Load prompt config YAML
- [ ] Resolve simple prompt (combinatorial mode)
- [ ] Tests unitaires >80% coverage
- [ ] Documentation inline (docstrings)

### Pour démarrer

Lis d'abord les specs complètes dans :
1. `docs/roadmap/future/nextGenTemplating/README.md`
2. `docs/roadmap/future/nextGenTemplating/02-advanced-variation-selectors.md`

Puis démarre par créer la structure de base et les premiers tests.

---

**Prêt à implémenter la Phase 1 ? On commence par quoi ?**
