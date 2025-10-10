# V1 to V2 Migration - Edit Plan

Generated: 2025-10-10

## Fichiers à Éditer

### 1. src/cli.py

**Modifications :**

#### A. Supprimer fonction `_generate_with_v1()` (lignes 96-265)
```python
# SUPPRIMER ENTIÈREMENT
def _generate_with_v1(...):
    ...
```

#### B. Renommer `_generate_with_v2()` → `_generate()` (ligne 267)
```python
# AVANT
def _generate_with_v2(
    template_path: Path,
    ...
):

# APRÈS
def _generate(
    template_path: Path,
    ...
):
```

#### C. Supprimer imports V1 (ligne 32)
```python
# SUPPRIMER
from templating import load_prompt_config, resolve_prompt
```

#### D. Supprimer paramètre `use_v2` dans `generate_images()` (lignes 524-528)
```python
# SUPPRIMER
    use_v2: bool = typer.Option(
        False,
        "--v2",
        help="Use Template System V2.0 (new YAML format with inheritance)",
    ),
```

#### E. Mettre à jour docstring `generate_images()` (lignes 530-544)
```python
# REMPLACER
    """
    Generate images from YAML template.

    If no template is specified, enters interactive mode.

    Supports both V1 (Phase 2) and V2.0 template systems:
    - V1: Default, uses variations: and multi-field syntax
    - V2: Use --v2 flag, supports inheritance, imports:, and chunks

    Examples:
        python3 template_cli_typer.py generate
        python3 template_cli_typer.py generate -t portrait.yaml
        python3 template_cli_typer.py generate -t test.yaml -n 10 --dry-run
        python3 template_cli_typer.py generate -t v2_template.yaml --v2
    """

# PAR
    """
    Generate images from YAML template using V2.0 Template System.

    If no template is specified, enters interactive mode.

    V2.0 features:
    - Inheritance with implements:
    - Modular imports with imports:
    - Reusable chunks
    - Advanced selectors and weights

    Examples:
        python3 template_cli_typer.py generate
        python3 template_cli_typer.py generate -t portrait.yaml
        python3 template_cli_typer.py generate -t test.yaml -n 10 --dry-run
    """
```

#### F. Simplifier routing V1/V2 (lignes 588-614)
```python
# SUPPRIMER
        system_version = "V2.0" if use_v2 else "V1 (Phase 2)"
        console.print(Panel(
            f"[bold]Template:[/bold] {template_path.name}\n"
            f"[bold]System:[/bold] {system_version}",
            title="Processing Template",
            border_style="cyan"
        ))

        # Route to V2 or V1 based on flag
        if use_v2:
            _generate_with_v2(...)
        else:
            _generate_with_v1(...)

# REMPLACER PAR
        console.print(Panel(
            f"[bold]Template:[/bold] {template_path.name}",
            title="Processing Template (V2.0)",
            border_style="cyan"
        ))

        _generate(
            template_path=template_path,
            global_config=global_config,
            count=count,
            api_url=api_url,
            dry_run=dry_run,
            console=console
        )
```

#### G. Mettre à jour `validate_template()` - Supprimer logique V1 (lignes 700-864)
```python
# Supprimer tout le bloc V1 validation (lignes 793-864)
# Garder seulement la validation V2

# SUPPRIMER paramètre use_v2
    use_v2: bool = typer.Option(
        False,
        "--v2",
        help="Validate as Template System V2.0 format",
    ),

# SUPPRIMER
        system_version = "V2.0" if use_v2 else "V1 (Phase 2)"
        console.print(f"[cyan]Validating template:[/cyan] {template}")
        console.print(f"[cyan]System:[/cyan] {system_version}\n")

        if use_v2:
            # V2 validation
            ...
            return

        # V1 validation below
        ...  # TOUT SUPPRIMER

# REMPLACER PAR (simple)
        console.print(f"[cyan]Validating template (V2.0):[/cyan] {template}\n")

        from templating.v2.orchestrator import V2Pipeline

        pipeline = V2Pipeline()
        config = pipeline.load(str(template))
        ...
```

#### H. Mettre à jour `select_template_interactive()` - Supprimer load_prompt_config V1 (lignes 464-466)
```python
# REMPLACER
        try:
            config = load_prompt_config(template_path)
            name = config.name
            rel_path = str(template_path.relative_to(configs_dir))
        except Exception:
            name = template_path.stem
            rel_path = str(template_path)

# PAR
        try:
            from templating.v2.orchestrator import V2Pipeline
            pipeline = V2Pipeline()
            config = pipeline.load(str(template_path))
            name = config.name
            rel_path = str(template_path.relative_to(configs_dir))
        except Exception:
            name = template_path.stem
            rel_path = str(template_path)
```

#### I. Mettre à jour `list_templates()` - même changement (lignes 659-663)

---

### 2. src/templating/__init__.py

**Modifications :**

#### A. Vérifier contenu actuel
Lire le fichier pour voir les exports actuels

#### B. Supprimer exports V1
```python
# SUPPRIMER (si présents)
from .chunk import *
from .loaders import *
from .multi_field import *
from .prompt_config import *
from .resolver import *
from .selectors import *
from .types import *
```

#### C. Garder/Ajouter exports V2
```python
# GARDER/AJOUTER
from .v2.orchestrator import V2Pipeline
from .v2.models.config_models import (
    TemplateConfig,
    ChunkConfig,
    PromptConfig,
    GenerationConfig,
    ResolvedContext
)

__all__ = [
    'V2Pipeline',
    'TemplateConfig',
    'ChunkConfig',
    'PromptConfig',
    'GenerationConfig',
    'ResolvedContext',
]
```

---

## Résumé des Édits

| Fichier | Lignes à modifier | Complexité | Priorité |
|---------|-------------------|------------|----------|
| src/cli.py | ~200 lignes | Haute | P1 |
| src/templating/__init__.py | ~20 lignes | Basse | P1 |

## Ordre d'Exécution

1. **Éditer `src/templating/__init__.py`** (rapide, impact faible)
2. **Éditer `src/cli.py`** (long, impact élevé)
3. **Tester** que tout fonctionne
4. **Commit** les changements

## Tests à Exécuter

Après les édits :
```bash
# 1. Tests unitaires V2
python3 -m pytest tests/v2/ -v

# 2. Tests API
python3 -m pytest tests/api/ -v

# 3. Test CLI help
python3 src/cli.py --help
python3 src/cli.py generate --help
python3 src/cli.py validate --help

# 4. Test validation simple
python3 src/cli.py validate /path/to/template.prompt.yaml

# 5. Test dry-run
python3 src/cli.py generate -t /path/to/template.yaml --dry-run -n 5
```

## Rollback Plan

Si problème :
```bash
# Annuler tous les changements
git reset --hard HEAD

# Ou annuler seulement les fichiers édités
git checkout src/cli.py src/templating/__init__.py
```
