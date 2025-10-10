# V1 to V2 Migration - Inventory Report

Generated: 2025-10-10

## Fichiers V1 Exclusifs à Déplacer

### Code Source (src/templating/)
```
src/templating/chunk.py
src/templating/loaders.py
src/templating/multi_field.py
src/templating/prompt_config.py
src/templating/resolver.py
src/templating/selectors.py
src/templating/types.py
src/templating/v1/__init__.py
```
**Total: 8 fichiers**

### Tests (tests/templating/)
```
tests/templating/test_chunk.py
tests/templating/test_loaders.py
tests/templating/test_multi_field.py
tests/templating/test_phase2_integration.py
tests/templating/test_prompt_config.py
tests/templating/test_resolver.py
tests/templating/test_resolver_imports.py
tests/templating/test_selectors.py
tests/templating/test_selectors_chunk.py
```
**Total: 9 fichiers**

### Documentation
```
(None found - no docs/ folder in CLI/)
```

## Fichiers qui Importent du Code V1

### Code Source
```
src/cli.py
  - from templating import load_prompt_config, resolve_prompt
  - Utilise ces imports dans _generate_with_v1()
```

### Documentation
```
src/examples/README.md
  - Mentions de l'API V1
```

## Plan de Migration

### Phase 1: Déplacer V1 vers dossier dédié
Créer: `src/templating/legacy_v1/`
Déplacer:
- Tous les fichiers de src/templating/*.py (sauf __init__.py)
- src/templating/v1/* → src/templating/legacy_v1/v1/

Créer: `tests/templating/legacy_v1/`
Déplacer:
- Tous les tests V1 listés ci-dessus

### Phase 2: Mettre à jour les imports
Fichiers à éditer:
1. **src/cli.py**
   - Supprimer fonction `_generate_with_v1()` (lignes 96-265)
   - Renommer `_generate_with_v2()` → `_generate()`
   - Supprimer flag `--v2` / `use_v2`
   - Supprimer import `from templating import load_prompt_config, resolve_prompt`
   - Mettre à jour docstrings

2. **src/templating/__init__.py**
   - Supprimer exports V1
   - Garder seulement exports V2

### Phase 3: Migrer V2 vers racine
- Déplacer src/templating/v2/* → src/templating/
- Mettre à jour tous les imports `from templating.v2` → `from templating`

### Phase 4: Nettoyage
- Supprimer dossier src/templating/v2/ (vidé)
- Mettre à jour pyproject.toml si nécessaire
- Mettre à jour README

## Statistiques

- **Code V1**: 8 fichiers (~2000 lignes estimées)
- **Tests V1**: 9 fichiers (~1500 lignes de tests)
- **Fichiers à éditer**: 2 fichiers (cli.py, __init__.py)
- **Fichiers V2 à migrer**: ~30 fichiers

## Impact

- **Breaking changes**: OUI (suppression de l'API V1)
- **Tests impactés**: 9 tests V1 seront archivés
- **Tests V2**: 69 tests passent ✅
- **Backward compatibility**: Assurée via layer de compatibilité déjà implémenté
