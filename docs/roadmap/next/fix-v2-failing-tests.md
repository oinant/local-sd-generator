# Fix V2 Failing Tests (63 tests)

**Status:** next
**Priority:** 1 (CRITIQUE - Bloque Phase 2 packaging)
**Component:** cli
**Created:** 2025-10-15

## Description

Corriger les 63 tests V2 qui échouent actuellement (bugs pré-existants dans le système de caching et validation). Ces échecs bloquent la Phase 2 du packaging/monorepo car nous exigeons **100% de test pass rate** avant de continuer.

## Motivation

- 🔴 **BLOQUANT** : Phase 2 packaging ne peut pas démarrer sans 100% tests verts
- 🐛 **Qualité** : Ces bugs existent depuis longtemps et compromettent la fiabilité
- 📦 **Distribution** : Impossible de publier sur PyPI avec des tests échouants
- 🚀 **Confiance** : 100% pass rate = code production-ready

## Tests échouants (63 total)

### Catégorie 1: Caching bugs (YamlLoader) - ~8 tests
**Fichier:** `tests/v2/unit/test_yaml_loader.py`

Problèmes identifiés:
- Cache ne fonctionne pas correctement (fichiers rechargés au lieu d'être cached)
- Cache keys basés sur identité d'objet au lieu de contenu
- `invalidate_specific_file()` ne vide pas vraiment le cache
- Custom cache partagé entre loaders ne fonctionne pas

Tests concernés:
- `test_file_loaded_once_and_cached`
- `test_cache_key_uses_absolute_path`
- `test_invalidate_specific_file`
- `test_use_custom_cache`
- `test_shared_cache_between_loaders`

### Catégorie 2: Inheritance validation (InheritanceResolver) - ~15 tests
**Fichier:** `tests/v2/unit/test_inheritance_resolver.py`

Problèmes identifiés:
- Validation trop stricte sur placeholder `{prompt}` dans templates enfants
- Templates avec `implements:` ne peuvent pas override le template parent
- Cache inheritance resolver casse après clear

Tests concernés:
- Tous tests `TestCacheBehavior.*`
- Tous tests `TestErrorHandling.*`

### Catégorie 3: PromptConfig API mismatch - ~20 tests
**Fichiers:** `tests/v2/unit/test_orchestrator.py`, `tests/v2/unit/test_validator.py`

Problèmes identifiés:
- `TypeError: PromptConfig.__init__() missing 1 required positional argument: 'prompt'`
- Tests créent `PromptConfig()` sans tous les champs requis
- Changement dans signature de `PromptConfig` non reflété dans tests

Tests concernés:
- `test_resolve_context`
- `test_generate_prompts_*`
- `test_end_to_end_mock`
- etc. (~20 tests)

### Catégorie 4: Validation conflicts - ~10 tests
**Fichier:** `tests/v2/unit/test_validator.py`

Problèmes identifiés:
- Détection de conflits dans imports multi-sources ne fonctionne pas
- Validation ne détecte pas les clés dupliquées
- Erreurs de validation manquent des détails attendus

Tests concernés:
- `test_duplicate_keys_in_multi_source`
- `test_import_error_includes_conflict_details`
- `test_prompt_with_reserved_placeholders_valid`

### Catégorie 5: Template resolution - ~5 tests
**Fichier:** `tests/v2/unit/test_template_resolver.py`

Problèmes identifiés:
- Chunks non résolus correctement (`@chunks.positive` reste littéral)
- Nested resolution échoue

Tests concernés:
- `test_complex_nested_resolution`

### Catégorie 6: Field naming (prompt vs template) - ~5 tests
**Fichier:** `tests/v2/unit/test_orchestrator.py`

Problèmes identifiés:
- Confusion entre champs `prompt:` et `template:`
- Validation rejette fichiers valides

Tests concernés:
- `test_load_valid_prompt`

## Implementation Plan

### Étape 1: Analyser causes racines (2-3h)
- [ ] Lire code de `YamlLoader` et comprendre le système de cache
- [ ] Lire code de `InheritanceResolver` et comprendre validation `{prompt}`
- [ ] Lire signature `PromptConfig` et comparer avec usages dans tests
- [ ] Identifier patterns communs dans les échecs

### Étape 2: Fixer caching (3-4h)
- [ ] Implémenter cache basé sur hash de contenu (pas identité objet)
- [ ] Corriger `invalidate_specific_file()` pour vraiment vider cache
- [ ] Implémenter shared cache entre loaders
- [ ] Tests : `test_yaml_loader.py` doit passer à 100%

### Étape 3: Fixer inheritance validation (2-3h)
- [ ] Assouplir validation `{prompt}` pour templates enfants
- [ ] Permettre override complet du template parent
- [ ] Corriger cache invalidation dans InheritanceResolver
- [ ] Tests : `test_inheritance_resolver.py` doit passer à 100%

### Étape 4: Fixer PromptConfig signature (1-2h)
- [ ] Auditer tous usages de `PromptConfig()` dans tests
- [ ] Mettre à jour pour inclure tous champs requis
- [ ] Ou rendre certains champs optionnels avec defaults
- [ ] Tests : `test_orchestrator.py` doit passer à 100%

### Étape 5: Fixer validation conflicts (2-3h)
- [ ] Implémenter détection clés dupliquées multi-sources
- [ ] Ajouter détails dans messages d'erreur
- [ ] Tests : `test_validator.py` doit passer à 100%

### Étape 6: Fixer template resolution (1-2h)
- [ ] Debugger résolution de chunks nested
- [ ] Corriger pattern matching pour `@chunks.*`
- [ ] Tests : `test_template_resolver.py` doit passer à 100%

### Étape 7: Fixer field naming (1h)
- [ ] Clarifier si utiliser `prompt:` ou `template:`
- [ ] Mettre à jour validation en conséquence
- [ ] Tests : tous tests passent

### Étape 8: Validation finale (1h)
- [ ] Lancer suite complète : `pytest tests/ --ignore=tests/legacy`
- [ ] Vérifier 441/441 tests passent (100%)
- [ ] Lancer avec coverage : `pytest tests/v2/ --cov=templating`
- [ ] Commit : "fix(v2): Correct 63 failing tests - 100% pass rate achieved"

## Success Criteria

- [ ] **100% test pass rate** : 441/441 tests passent
- [ ] Aucun test skip ou xfail
- [ ] Coverage V2 maintenue > 85%
- [ ] Aucune régression dans tests API (82/82 doivent toujours passer)
- [ ] Documentation des fixes dans commit messages

## Tests

**Commandes de validation :**
```bash
cd packages/sd-generator-cli

# Tests API (doivent rester à 100%)
../../venv/bin/python3 -m pytest tests/api/ -v

# Tests V2 (doivent passer à 100%)
../../venv/bin/python3 -m pytest tests/v2/ -v

# Suite complète
../../venv/bin/python3 -m pytest tests/ --ignore=tests/legacy -v

# Avec coverage
../../venv/bin/python3 -m pytest tests/v2/ --cov=templating --cov-report=term-missing -v
```

**Critères de validation :**
- Tous tests API : 82/82 ✅
- Tous tests V2 : 270/270 ✅
- Tous autres tests : 89/89 ✅
- **Total : 441/441 (100%)** ✅

## Documentation

**Fichiers à mettre à jour après fixes :**
- [ ] `docs/cli/technical/template-system-v2.md` - Documenter comportements corrigés
- [ ] `CHANGELOG.md` - Lister tous les bugs corrigés
- [ ] Cette spec roadmap - Marquer comme done

## Commits

_(À remplir pendant l'implémentation)_

Example commit structure:
```
fix(v2/cache): Implement content-based cache keys for YamlLoader

- Replace object identity cache keys with file path + mtime
- Fix invalidate_specific_file() to properly clear cache
- Implement shared cache between loader instances
- Fixes: 5 tests in test_yaml_loader.py

Closes #XXX
```

## Dependencies

**Bloquants :**
- Aucun - peut démarrer immédiatement

**Bloque :**
- Phase 2 packaging/monorepo (ne peut PAS démarrer sans ce fix)
- Publication PyPI
- Toute feature V2 nécessitant caching ou inheritance

## Timeline

**Estimation totale : 13-19h**

- Étape 1 (Analyse) : 2-3h
- Étape 2 (Caching) : 3-4h
- Étape 3 (Inheritance) : 2-3h
- Étape 4 (PromptConfig) : 1-2h
- Étape 5 (Validation) : 2-3h
- Étape 6 (Resolution) : 1-2h
- Étape 7 (Field naming) : 1h
- Étape 8 (Validation) : 1h

**Sprint recommandé : 2-3 jours**
- Jour 1 : Étapes 1-3 (analyse + caching + inheritance)
- Jour 2 : Étapes 4-6 (PromptConfig + validation + resolution)
- Jour 3 : Étapes 7-8 (field naming + validation finale)

## Notes

**Pourquoi 100% pass rate obligatoire ?**
- Qualité professionnelle pour publication PyPI
- Confiance pour utilisateurs
- Facilite maintenance future
- Évite bugs silencieux en production

**Alternative considérée mais rejetée :**
- ❌ Skip des tests échouants avec `@pytest.mark.skip`
  - Masque les problèmes au lieu de les résoudre
  - Réduit la valeur de la suite de tests
  - Dégradation progressive de la qualité

**Priorité P1 car :**
- Bloque monorepo restructure (roadmap prioritaire)
- 63 tests = surface d'impact significative
- Bugs anciens = dette technique accumulée
