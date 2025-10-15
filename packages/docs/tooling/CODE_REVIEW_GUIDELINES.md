# Code Review Guidelines

**Directives et checklist pour les code reviews du projet**

---

## Philosophie de la code review

Une code review efficace vise à :
- ✅ **Améliorer la qualité** : Détecter bugs, problèmes de design, code smell
- ✅ **Partager la connaissance** : Comprendre et documenter les décisions
- ✅ **Maintenir la cohérence** : Standards de code, patterns, architecture
- ✅ **Réduire la dette technique** : Identifier et éliminer le code mort, duplications

**Principe clé** : Une review bienveillante mais rigoureuse. L'objectif est d'améliorer le code, pas de critiquer l'auteur.

---

## Catégories de review

### 1. Architecture et Design

#### 1.1 Principes SOLID

**Single Responsibility Principle (SRP)**
- [ ] Chaque classe/module a une seule raison de changer
- [ ] Les responsabilités sont clairement définies
- [ ] Pas de "God classes" qui font tout

**Exemples à vérifier :**
```python
# ❌ Violation SRP : une classe qui fait trop
class ImageGenerator:
    def load_config(self): ...
    def validate_config(self): ...
    def load_variations(self): ...
    def parse_variations(self): ...
    def generate_combinations(self): ...
    def call_api(self): ...
    def save_images(self): ...
    def generate_metadata(self): ...

# ✅ Respect SRP : responsabilités séparées
class ConfigLoader:
    def load(self): ...

class VariationLoader:
    def load(self): ...

class CombinationGenerator:
    def generate(self): ...

class APIClient:
    def call(self): ...
```

**Open/Closed Principle**
- [ ] Ouvert à l'extension, fermé à la modification
- [ ] Utilisation de patterns (Strategy, Factory) pour l'extensibilité
- [ ] Pas de chaînes de if/elif pour ajouter des fonctionnalités

**Liskov Substitution Principle**
- [ ] Les sous-classes peuvent remplacer les classes parentes
- [ ] Les interfaces sont respectées
- [ ] Pas de comportements surprenants dans les héritages

**Interface Segregation Principle**
- [ ] Pas d'interfaces trop larges
- [ ] Clients ne dépendent que de ce qu'ils utilisent

**Dependency Inversion Principle**
- [ ] Dépendance sur les abstractions, pas les implémentations
- [ ] Injection de dépendances où approprié

#### 1.2 Séparation des responsabilités

**Modules bien délimités**
- [ ] Chaque module a un rôle clair et documenté
- [ ] Pas de dépendances circulaires entre modules
- [ ] Import graph cohérent et simple

**Couches architecturales respectées**
- [ ] UI/CLI séparée de la logique métier
- [ ] Logique métier séparée de la persistence/API
- [ ] Data access layer bien isolée

**Points à vérifier :**
- [ ] `config/` gère uniquement la configuration
- [ ] `templating/` gère uniquement le templating
- [ ] `execution/` orchestre mais ne fait pas la logique
- [ ] `output/` gère uniquement la génération de fichiers
- [ ] Pas de logique métier dans les scripts CLI

#### 1.3 Cohésion et couplage

**Haute cohésion**
- [ ] Les éléments d'un module sont fortement liés
- [ ] Tout ce qui est dans un fichier a un lien logique

**Faible couplage**
- [ ] Modules indépendants autant que possible
- [ ] Changements localisés (modifier un module n'impacte pas les autres)
- [ ] Communication via interfaces claires

---

### 2. Qualité du code

#### 2.1 Complexité et lisibilité

**Longueur des fonctions**
- [ ] Fonctions < 50 lignes (idéalement < 30)
- [ ] Si > 50 lignes, peut-être extraire des sous-fonctions
- [ ] Une fonction = une responsabilité

**Complexité cyclomatique**
- [ ] Pas plus de 3-4 niveaux d'indentation
- [ ] Limiter les if/else imbriqués
- [ ] Extraire les conditions complexes

```python
# ❌ Trop complexe
def process(data):
    if data:
        if data.type == 'A':
            if data.valid:
                if data.has_value:
                    return process_a(data)
                else:
                    return default_a()
            else:
                raise Error()
        elif data.type == 'B':
            # ...
    else:
        return None

# ✅ Simplifié avec early returns
def process(data):
    if not data:
        return None

    if not data.valid:
        raise Error()

    if data.type == 'A':
        return _process_type_a(data)

    if data.type == 'B':
        return _process_type_b(data)

def _process_type_a(data):
    if not data.has_value:
        return default_a()
    return process_a(data)
```

**Nommage**
- [ ] Noms explicites et descriptifs
- [ ] Variables : `snake_case`, classes : `PascalCase`
- [ ] Booléens : `is_`, `has_`, `should_`
- [ ] Pas d'abréviations obscures

```python
# ❌ Mauvais
def proc_dat(d, cfg):
    res = []
    for i in d:
        if i.v > cfg.t:
            res.append(i)
    return res

# ✅ Bon
def filter_variations_by_threshold(variations, config):
    filtered_results = []
    for variation in variations:
        if variation.value > config.threshold:
            filtered_results.append(variation)
    return filtered_results
```

**Commentaires**
- [ ] Code auto-documenté (noms clairs)
- [ ] Commentaires pour le "pourquoi", pas le "quoi"
- [ ] Docstrings pour toutes les fonctions publiques
- [ ] Pas de code commenté (supprimer ou expliquer pourquoi)

```python
# ❌ Commentaire inutile
# Incrémente i de 1
i += 1

# ✅ Commentaire utile
# On utilise +1 ici car l'index_base peut être 0 ou 1 selon la config
adjusted_index = raw_index + config.index_base
```

#### 2.2 DRY (Don't Repeat Yourself)

**Duplication de code**
- [ ] Pas de copier-coller de blocs de code
- [ ] Logique commune extraite dans des fonctions
- [ ] Constantes magiques définies une seule fois

```python
# ❌ Duplication
def process_expressions():
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data['variations']

def process_outfits():
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data['variations']

# ✅ Factorisation
def load_yaml_variations(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data['variations']

def process_expressions():
    return load_yaml_variations(expressions_path)

def process_outfits():
    return load_yaml_variations(outfits_path)
```

**Constantes magiques**
- [ ] Nombres hardcodés extraits en constantes nommées
- [ ] Strings répétés définis une seule fois

```python
# ❌ Magic numbers
if len(prompt) > 77:
    ...
max_retries = 3

# ✅ Constantes nommées
MAX_PROMPT_LENGTH = 77  # SD API limit
MAX_API_RETRIES = 3

if len(prompt) > MAX_PROMPT_LENGTH:
    ...
```

#### 2.3 Gestion d'erreurs

**Exceptions appropriées**
- [ ] Pas de `except Exception` trop large
- [ ] Exceptions spécifiques pour chaque type d'erreur
- [ ] Messages d'erreur clairs et actionnables

```python
# ❌ Trop large
try:
    result = process()
except Exception:
    return None

# ✅ Spécifique
try:
    result = load_config(path)
except FileNotFoundError as e:
    raise ConfigError(f"Config file not found: {path}") from e
except yaml.YAMLError as e:
    raise ConfigError(f"Invalid YAML in {path}: {e}") from e
```

**Validation des entrées**
- [ ] Tous les paramètres publics validés
- [ ] Type hints utilisés partout
- [ ] Assertions pour les invariants internes

**Messages d'erreur**
- [ ] Contexte clair (fichier, ligne, valeur)
- [ ] Solution suggérée si possible
- [ ] Pas de stack traces brutes à l'utilisateur

---

### 3. Organisation du code

#### 3.1 Structure des fichiers

**Taille des fichiers**
- [ ] Fichiers < 500 lignes (idéalement < 300)
- [ ] Un fichier = un concept
- [ ] Découper les gros fichiers en modules

**Organisation interne**
- [ ] Imports en haut, groupés et triés
- [ ] Constantes ensuite
- [ ] Classes et fonctions publiques
- [ ] Fonctions privées (`_prefixed`) à la fin
- [ ] Code exécutable dans `if __name__ == '__main__':`

```python
# Structure recommandée
"""Module docstring."""

# Standard library imports
import os
from pathlib import Path
from typing import Dict, List

# Third-party imports
import yaml

# Local imports
from .types import Variation
from .loaders import load_variations

# Constants
DEFAULT_WEIGHT = 1.0
MAX_VARIATIONS = 1000

# Public classes
class VariationLoader:
    """Public class."""
    pass

# Public functions
def load_from_file(path: Path) -> Dict:
    """Public function."""
    pass

# Private functions
def _parse_yaml(data: dict) -> List:
    """Private helper."""
    pass

# Main execution
if __name__ == '__main__':
    main()
```

#### 3.2 Imports

**Clarté des imports**
- [ ] Pas de `from module import *`
- [ ] Imports relatifs pour le projet, absolus pour les libs
- [ ] Regroupés par : stdlib, third-party, local

**Dépendances circulaires**
- [ ] Pas d'imports circulaires
- [ ] Si nécessaire, import dans la fonction

---

### 4. Tests et maintenabilité

#### 4.1 Testabilité

**Code testable**
- [ ] Fonctions pures autant que possible
- [ ] Dépendances injectables
- [ ] Pas de logique dans les constructeurs
- [ ] Pas d'état global

**Coverage**
- [ ] Fonctions critiques testées
- [ ] Edge cases couverts
- [ ] Tests unitaires séparés des tests d'intégration

#### 4.2 Documentation

**Docstrings**
- [ ] Toutes les fonctions publiques documentées
- [ ] Format cohérent (Google, NumPy, ou reStructuredText)
- [ ] Args, Returns, Raises documentés

```python
def load_variations(filepath: Path, encoding: str = 'utf-8') -> Dict[str, Variation]:
    """
    Load variations from a YAML file.

    Args:
        filepath: Path to the YAML variation file
        encoding: File encoding (default: utf-8)

    Returns:
        Dictionary mapping variation keys to Variation objects

    Raises:
        FileNotFoundError: If filepath doesn't exist
        ValueError: If YAML format is invalid

    Example:
        >>> variations = load_variations(Path('expressions.yaml'))
        >>> variations['happy'].value
        'smiling, cheerful'
    """
    pass
```

**README et guides**
- [ ] README à jour
- [ ] Exemples d'utilisation
- [ ] Architecture documentée

---

### 5. Performance

#### 5.1 Algorithmes

**Complexité**
- [ ] Pas de O(n²) évitables
- [ ] Utilisation de structures de données appropriées
- [ ] Pas de calculs répétés dans les boucles

```python
# ❌ O(n²) évitable
for item in items:
    if item in other_list:  # O(n) lookup × n items
        process(item)

# ✅ O(n) avec set
other_set = set(other_list)
for item in items:
    if item in other_set:  # O(1) lookup
        process(item)
```

#### 5.2 Ressources

**Mémoire**
- [ ] Pas de chargement de tous les fichiers en mémoire
- [ ] Streaming pour les gros fichiers
- [ ] Libération des ressources (with statements)

**IO**
- [ ] Pas de lectures répétées du même fichier
- [ ] Cache pour les données fréquentes
- [ ] Lazy loading où approprié

---

### 6. Sécurité

#### 6.1 Validation des entrées

**Sanitization**
- [ ] Chemins de fichiers validés (pas de path traversal)
- [ ] User input nettoyé
- [ ] Tailles limitées (pas de DoS)

```python
# ❌ Dangereux
def load_file(user_path):
    return open(user_path).read()

# ✅ Sécurisé
def load_file(user_path, allowed_dir):
    path = Path(user_path).resolve()
    if not path.is_relative_to(allowed_dir):
        raise SecurityError("Path outside allowed directory")
    return path.read_text()
```

#### 6.2 Secrets

**Pas de secrets hardcodés**
- [ ] Pas de mots de passe, tokens, keys dans le code
- [ ] Variables d'environnement ou fichiers de config
- [ ] Fichiers secrets dans .gitignore

---

### 7. Code mort et maintenance

#### 7.1 Code inutilisé

**Nettoyage**
- [ ] Pas de fonctions non appelées
- [ ] Pas de variables non utilisées
- [ ] Pas de paramètres non utilisés (ou `_` si intentionnel)
- [ ] Pas de code commenté sans raison

**Détection**
- [ ] Utiliser `pylint`, `flake8` pour détecter le code mort
- [ ] Vérifier les imports non utilisés
- [ ] Supprimer les TODOs obsolètes

#### 7.2 Dépréciation

**Backward compatibility**
- [ ] Fonctions dépréciées marquées avec `@deprecated`
- [ ] Warnings clairs pour les anciennes API
- [ ] Documentation de migration

---

### 8. Style et conventions

#### 8.1 PEP 8

**Conventions Python**
- [ ] 4 espaces d'indentation
- [ ] Lignes < 100 caractères (flexible à 120)
- [ ] 2 lignes blanches entre fonctions de niveau module
- [ ] 1 ligne blanche entre méthodes de classe

#### 8.2 Type hints

**Annotations de types**
- [ ] Type hints sur toutes les signatures publiques
- [ ] Return types spécifiés
- [ ] Union types pour les types multiples

```python
from typing import Dict, List, Optional, Union
from pathlib import Path

def load_variations(
    filepath: Union[str, Path],
    max_items: Optional[int] = None
) -> Dict[str, List[str]]:
    """Type hints clairs."""
    pass
```

---

## Checklist de review par fichier

Pour chaque fichier reviewé :

### 📋 Checklist rapide

**Architecture (5 min)**
- [ ] Responsabilité unique et claire
- [ ] Pas de violation SOLID évidente
- [ ] Module bien placé dans l'architecture

**Qualité (10 min)**
- [ ] Fonctions < 50 lignes
- [ ] Nommage clair et cohérent
- [ ] Pas de duplication évidente
- [ ] Gestion d'erreurs appropriée

**Organisation (5 min)**
- [ ] Fichier < 500 lignes
- [ ] Imports propres et organisés
- [ ] Pas de code commenté sans raison

**Documentation (5 min)**
- [ ] Docstrings sur fonctions publiques
- [ ] Type hints présents
- [ ] Commentaires pertinents

**Performance (5 min)**
- [ ] Pas de O(n²) évitables
- [ ] Ressources bien gérées (with, close)

**Code mort (5 min)**
- [ ] Pas de fonctions non utilisées
- [ ] Pas d'imports inutiles
- [ ] Pas de variables mortes

**Total : ~30-35 min par fichier moyen**

---

## Processus de review

### 1. Préparation

**Avant de commencer :**
1. [ ] Lire le contexte (commit message, PR description)
2. [ ] Comprendre l'objectif du changement
3. [ ] Identifier les fichiers critiques à reviewer en priorité

### 2. Review par niveaux

**Niveau 1 : Architecture (vue d'ensemble)**
- Regarder la structure générale
- Vérifier les responsabilités
- Identifier les problèmes de design

**Niveau 2 : Logique (ligne par ligne)**
- Lire chaque fonction
- Vérifier la logique
- Détecter les bugs potentiels

**Niveau 3 : Détails (polish)**
- Nommage
- Commentaires
- Style

### 3. Feedback

**Catégoriser les commentaires :**
- 🔴 **Bloquant** : Bug, sécurité, violation architecture majeure
- 🟠 **Important** : Code smell, mauvaise pratique, dette technique
- 🟡 **Suggestion** : Amélioration possible, style
- 💡 **Question** : Demande de clarification

**Format des commentaires :**
```markdown
🔴 **Bloquant** : Potential null pointer exception
Line 42: `variations[key]` will crash if key doesn't exist.
Suggestion: Use `variations.get(key, default)` or check key existence.

🟠 **Important** : Function too long
Line 100-200: `process_variations()` is 100 lines long.
Consider extracting sub-functions for readability.

🟡 **Suggestion** : Better naming
Line 25: `data` is too generic. Consider `variation_config` or `parsed_yaml`.

💡 **Question** : Why is this needed?
Line 67: Why do we convert to string then back to int?
```

---

## Outils automatiques

**Linters recommandés :**
- `pylint` : Analyse statique complète
- `flake8` : Style PEP 8
- `mypy` : Vérification des types
- `bandit` : Sécurité
- `radon` : Complexité cyclomatique

**Commandes utiles :**
```bash
# Style
flake8 CLI/ --max-line-length=120

# Types
mypy CLI/ --strict

# Complexité
radon cc CLI/ -a -nb

# Code mort
vulture CLI/

# Sécurité
bandit -r CLI/
```

---

## Red flags 🚩

**Signes de problèmes à investiguer :**
- Fichier > 1000 lignes
- Fonction > 100 lignes
- Classe > 500 lignes
- > 5 niveaux d'indentation
- Nom de variable à 1 lettre (sauf `i`, `j` dans les boucles)
- `except Exception` sans spécificité
- `# TODO` sans ticket/issue
- Code commenté sur > 10 lignes
- Import circulaire
- Variable globale mutable
- Logique métier dans la couche UI

---

## Exemples de problèmes fréquents

### Problème 1 : God Function

```python
# ❌ Fait trop de choses
def generate_images(config_path):
    # Load config (20 lines)
    # Validate config (30 lines)
    # Load variations (40 lines)
    # Generate combinations (50 lines)
    # Call API (30 lines)
    # Save results (20 lines)
    # Generate metadata (25 lines)
    pass  # Total: 215 lignes !
```

**Solution :** Découper en fonctions distinctes avec responsabilités claires.

### Problème 2 : Duplication cachée

```python
# ❌ Logique similaire répétée
def load_expressions():
    if not path.exists():
        raise FileNotFoundError(...)
    with open(path) as f:
        data = yaml.load(f)
    return parse_variations(data)

def load_outfits():
    if not path.exists():
        raise FileNotFoundError(...)
    with open(path) as f:
        data = yaml.load(f)
    return parse_variations(data)
```

**Solution :** Extraire la logique commune.

### Problème 3 : Mauvaise gestion d'erreurs

```python
# ❌ Erreurs avalées silencieusement
def process():
    try:
        result = complex_operation()
    except:
        result = None
    return result
```

**Solution :** Logger l'erreur ou la re-raise avec contexte.

---

## Templates de rapport

### Rapport de review par fichier

```markdown
# Review: CLI/templating/resolver.py

**Status:** 🟢 Approuvé avec suggestions

## Résumé
- Lignes: 450
- Fonctions: 12
- Complexité moyenne: 6

## Points positifs ✅
- Responsabilités claires (résolution de templates)
- Docstrings complètes
- Type hints présents
- Bonne séparation public/private

## Problèmes identifiés

### 🔴 Bloquants
Aucun

### 🟠 Importants
1. **Fonction trop longue** (ligne 200-280)
   - `resolve_prompt()` fait 80 lignes
   - Suggestion: Extraire la logique de combinaisons

2. **Duplication** (lignes 150, 180, 210)
   - Pattern de validation répété 3 fois
   - Suggestion: Fonction `_validate_variations()`

### 🟡 Suggestions
1. Nommage: `all_elements` → `combined_variations` (ligne 297)
2. Commentaire: Expliquer pourquoi on fait +1 (ligne 322)

## Actions
- [ ] Refactor `resolve_prompt()` en sous-fonctions
- [ ] Extraire validation commune
- [ ] Améliorer nommage
```

---

## Critères de validation

**Un fichier est validé quand :**
- ✅ Pas de bloquants (🔴)
- ✅ Moins de 3 problèmes importants (🟠) non résolus
- ✅ Architecture cohérente avec le reste du projet
- ✅ Documentation minimale présente
- ✅ Tests pour la logique critique

---

## Références

- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Code Review Best Practices](https://google.github.io/eng-practices/review/)

---

**Version:** 1.0
**Dernière mise à jour:** 2025-10-06
**Contributeurs:** Claude Code + Team
