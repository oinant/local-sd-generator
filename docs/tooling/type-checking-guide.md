# Type Checking Guide - Preventing Runtime Type Errors

**Date:** 2025-10-16
**Status:** Active guideline
**Priority:** P1 - Critical

## Problème

Les erreurs de type comme `'GlobalConfig' object has no attribute 'get'` ne devraient **jamais** arriver en production. Ces erreurs doivent être détectées par le linter **avant** l'exécution.

## Solution : mypy en mode strict

### Configuration actuelle

Le projet utilise **mypy en mode strict** dans `packages/sd-generator-cli/pyproject.toml` :

```toml
[tool.mypy]
python_version = "3.10"
# Strict mode for catching attribute errors
strict = true
# But allow some flexibility
ignore_missing_imports = true
check_untyped_defs = true
warn_return_any = true
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_unreachable = true
no_implicit_optional = true
```

### Pourquoi strict = true ?

- **Détecte les erreurs d'attributs** : `config.get()` sur un objet qui n'a pas `.get()`
- **Force les type hints** : Les fonctions sans type hints ne sont PAS vérifiées
- **Catch les None implicites** : Évite les `NoneType has no attribute 'x'`

## Workflow obligatoire

### Avant chaque commit

```bash
# 1. Check types (depuis la racine du projet)
venv/bin/python3 -m mypy packages/sd-generator-cli/sd_generator_cli --show-error-codes

# 2. Si erreurs, FIX THEM avant de commit
```

### Pendant le développement

```bash
# Check un fichier spécifique rapidement
venv/bin/python3 -m mypy packages/sd-generator-cli/sd_generator_cli/commands.py --show-error-codes
```

## Règles de type hints

### ✅ Toujours ajouter des type hints

**Mauvais :**
```python
def start_command(dev_mode, backend_port):
    config = load_global_config()
    api_url = config.get("api_url")  # ❌ mypy ne détecte pas l'erreur
```

**Bon :**
```python
def start_command(
    dev_mode: bool,
    backend_port: int
) -> None:  # 👈 Return type obligatoire pour que mypy check le corps
    config = load_global_config()  # Type inféré: GlobalConfig
    api_url = config.get("api_url")  # ✅ mypy détecte: GlobalConfig n'a pas .get()
```

### ✅ Utiliser des dataclasses avec attributs typés

**Mauvais :**
```python
def load_config() -> dict:  # ❌ dict n'a pas de structure définie
    return {"api_url": "..."}
```

**Bon :**
```python
@dataclass
class GlobalConfig:
    api_url: str
    configs_dir: str
    output_dir: str

def load_global_config() -> GlobalConfig:  # ✅ Type explicite
    ...
```

### ✅ Accéder aux attributs, pas .get()

**Mauvais :**
```python
config = load_global_config()
api_url = config.get("api_url", "default")  # ❌ config n'est pas un dict
```

**Bon :**
```python
config = load_global_config()
api_url = config.api_url  # ✅ Attribut direct de la dataclass
```

## Erreurs courantes mypy

### 1. Function is missing a return type annotation

```
sd_generator_cli/commands.py:25: error: Function is missing a return type annotation  [no-untyped-def]
```

**Fix :**
```python
def start_command() -> None:  # Ajouter -> None
    ...
```

### 2. Item "X" has no attribute "Y"

```
error: "GlobalConfig" has no attribute "get"  [attr-defined]
```

**Fix :** Utiliser les attributs de la dataclass au lieu de `.get()` :
```python
# Avant
api_url = config.get("api_url")

# Après
api_url = config.api_url
```

### 3. Argument has incompatible type

```
error: Argument 1 has incompatible type "str"; expected "int"  [arg-type]
```

**Fix :** Convertir le type ou corriger la signature.

## Pre-commit hook (recommandé)

Créer `.git/hooks/pre-commit` :

```bash
#!/bin/bash
# Pre-commit hook: Run mypy before allowing commit

echo "Running mypy type checker..."
cd /mnt/d/StableDiffusion/local-sd-generator
venv/bin/python3 -m mypy packages/sd-generator-cli/sd_generator_cli --show-error-codes

if [ $? -ne 0 ]; then
    echo "❌ Type check failed. Fix errors before committing."
    exit 1
fi

echo "✅ Type check passed"
exit 0
```

Rendre exécutable :
```bash
chmod +x .git/hooks/pre-commit
```

## Intégration CI/CD (futur)

Ajouter dans GitHub Actions / GitLab CI :

```yaml
- name: Type check with mypy
  run: |
    pip install mypy
    mypy packages/sd-generator-cli/sd_generator_cli --show-error-codes
```

## Résumé

✅ **DO:**
- Toujours ajouter `-> None` ou `-> ReturnType` sur les fonctions
- Utiliser des dataclasses avec attributs typés
- Lancer mypy avant chaque commit
- Accéder aux attributs directement (pas `.get()`)

❌ **DON'T:**
- Laisser des fonctions sans type hints
- Utiliser `.get()` sur des objets non-dict
- Commit sans vérifier mypy
- Désactiver strict mode "pour aller plus vite"

## Références

- [mypy documentation](https://mypy.readthedocs.io/)
- [PEP 484 – Type Hints](https://peps.python.org/pep-0484/)
- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html)
