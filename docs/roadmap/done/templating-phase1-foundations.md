# Next-Gen Templating System - Phase 1: Foundations

**Status:** done
**Priority:** 5
**Component:** cli
**Created:** 2025-10-02
**Completed:** 2025-10-03

## Description

Implémentation des fondations du système de templating hiérarchique pour la génération de prompts Stable Diffusion. Cette phase établit l'infrastructure de base : loaders YAML, sélecteurs avancés, configuration de prompts, et résolution combinatoriale.

## Implementation

### Architecture

```
CLI/templating/
├── __init__.py           # Exports publics
├── types.py              # Dataclasses (Variation, Selector, PromptConfig, etc.)
├── loaders.py            # Chargement de fichiers YAML de variations
├── selectors.py          # Parsing et résolution de sélecteurs
├── prompt_config.py      # Chargement de .prompt.yaml
└── resolver.py           # Résolution des variations en prompts finaux
```

### Fonctionnalités implémentées

1. **Loaders YAML** (`loaders.py`)
   - Format simple : liste de strings
   - Format avec clés : `key: value` avec poids optionnels
   - Auto-génération de clés pour format simple

2. **Sélecteurs avancés** (`selectors.py`)
   - `[happy,sad]` - Sélection par clés nommées
   - `[1,5,8]` - Sélection par indices
   - `[range:1-10]` - Range d'indices
   - `[random:5]` - Sélection aléatoire
   - Combinaisons multiples : `[happy,sad,random:3]`
   - Extraction de placeholders depuis templates

3. **Configuration de prompts** (`prompt_config.py`)
   - Fichiers `.prompt.yaml` avec structure claire
   - Bloc `imports:` pour mapper placeholders → fichiers
   - Bloc `generation:` pour modes et seeds
   - Bloc `selector_config:` optionnel
   - Validation complète

4. **Resolver** (`resolver.py`)
   - Mode `combinatorial` : toutes les combinaisons
   - Mode `random` : combinaisons aléatoires uniques
   - Seed modes : `fixed`, `progressive`, `random`
   - Limitation `max_images`
   - Remplacement de placeholders dans templates

## Tasks

- [x] Créer structure `CLI/templating/`
- [x] Implémenter `types.py` avec dataclasses
- [x] Implémenter `loaders.py` (YAML uniquement)
- [x] Implémenter `selectors.py` avec tous les types
- [x] Implémenter `prompt_config.py`
- [x] Implémenter `resolver.py` avec modes combinatorial et random
- [x] Créer tests unitaires (25 tests)
- [x] Créer fixtures de test
- [x] Créer demo fonctionnelle
- [x] Déplacer `/tests` vers `/CLI/tests`
- [x] Configurer `pyproject.toml`
- [x] Documenter setup venv et pytest dans CLAUDE.md

## Success Criteria

- [x] Charge fichiers YAML de variations ✅
- [x] Parse tous types de sélecteurs ✅
- [x] Résout prompts en mode combinatorial ✅
- [x] Support des 3 seed modes ✅
- [x] 25 tests unitaires passent ✅
- [x] Demo fonctionnelle qui affiche variations ✅
- [x] Documentation à jour ✅

## Tests

**Coverage:** 25 tests unitaires

- `test_loaders.py` : 4 tests
  - Load YAML avec clés
  - Load YAML format simple
  - Gestion erreurs fichiers
  - Poids par défaut

- `test_selectors.py` : 13 tests
  - Parse chaque type de sélecteur
  - Résolution de sélecteurs
  - Combinaisons multiples
  - Strict mode
  - Extraction de placeholders

- `test_prompt_config.py` : 3 tests
  - Load configuration basique
  - Gestion erreurs
  - Valeurs par défaut

- `test_resolver.py` : 5 tests
  - Résolution simple
  - Seeds progressives
  - Remplacement placeholders
  - Mode combinatorial
  - Limitation max_images

## Documentation

- Technical: Architecture documentée dans ce fichier
- Usage: Demo `example_phase1_demo.py`
- Setup: Instructions pytest et venv dans `/CLAUDE.md`

## Exemples d'utilisation

### Fichier de variations (expressions.yaml)
```yaml
version: "1.0"
variations:
  - key: happy
    value: "smiling, cheerful"
  - key: sad
    value: "crying, tears"
  - key: angry
    value: "frowning, intense"
```

### Fichier de prompt (simple_test.prompt.yaml)
```yaml
name: "Simple Test"

imports:
  EXPRESSIONS: variations/expressions.yaml
  POSES: variations/poses.yaml

prompt: |
  masterpiece, {EXPRESSIONS[happy,sad]}, {POSES[random:3]}

negative_prompt: |
  low quality, blurry

generation:
  mode: combinatorial
  seed_mode: progressive
  seed: 42
```

### Code Python
```python
from CLI.templating import load_prompt_config, resolve_prompt

config = load_prompt_config("prompts/simple_test.prompt.yaml")
variations = resolve_prompt(config)

for var in variations:
    print(f"Seed {var.seed}: {var.final_prompt}")
```

## Commits

Commit principal de la Phase 1 avec toute l'implémentation.

## Notes

**Ce qui n'est PAS dans Phase 1 :**
- ❌ Character templates (Phase 2)
- ❌ Multi-field expansion (Phase 2)
- ❌ Nested variations (Phase 3)
- ❌ Explain system (Phase 3)
- ❌ CLI complète (Phase 4)

**Décisions techniques :**
- YAML uniquement (pas de support .txt pour simplifier)
- Tests dans `/CLI/tests` pour isolation
- `python -m pytest` recommandé pour PYTHONPATH
- Venv Linux (`venv/`) à la racine

## Prochaines étapes

Phase 2 : Character templates et multi-field expansion
