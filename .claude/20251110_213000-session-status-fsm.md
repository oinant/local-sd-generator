# Session Status FSM + Package Common

**Date:** 2025-11-10
**Context:** Watchdog session tracking improvements

## Problem Statement

**Problème original à résoudre:**
- ❌ Au démarrage du watchdog, si une session est en cours (`status != completed`), le watchdog ne crée PAS d'observer pour cette session
- → Les stats ne sont pas mises à jour pendant que la génération est en cours
- **Solution:** Au startup, query la dernière session en DB, check son status dans le manifest, et start observer si `status = ongoing`

**Problèmes liés (FSM):**
- Pas de status dans le manifest.json actuellement
- Pas de distinction entre session terminée vs abandonnée
- CLI et Watchdog doivent partager le schema du manifest

## Solution: FSM 3 états

```
ongoing → aborted
       ↘ completed
```

### États

- **ongoing**: Session en cours de génération
- **completed**: Session terminée avec succès (toutes images générées)
- **aborted**: Session interrompue (SIGTERM/SIGINT)

### Responsabilités

**CLI (`sdgen generate`):**
- ✅ Crée `manifest.json` avec `status: "ongoing"` au start
- ✅ Update manifest → `status: "completed"` quand génération terminée
- ✅ Update manifest → `status: "aborted"` sur SIGTERM/SIGINT (graceful shutdown)
- ❌ **NE touche PAS à la base SQL** (pas de dépendance)

**Watchdog:**
- ✅ Détecte nouveau manifest → Insert en base avec status
- ✅ Détecte modification manifest → Update base
- ✅ Si status = "completed" → Stop watching session
- ✅ Si status = "aborted" → Stop watching session
- ✅ Gère le mapping manifest.json → session_stats DB

### Architecture

```
manifest.json (source of truth)
      ↓
   Watchdog (observer)
      ↓
session_stats DB (cache)
```

**Principes:**
- `manifest.json` = source de vérité (filesystem)
- Base SQL = cache computed (pour queries rapides)
- Watchdog = sync unidirectionnelle (manifest → base)

## Package `sd-generator-common`

### Objectif

Partager les models entre packages pour éviter duplication et drift de schema.

### Contenu initial

**Models à partager:**
- `ManifestModel` - Schema du manifest.json avec:
  - `status: Literal["ongoing", "aborted", "completed"]`
  - `images_requested: int`
  - `images_actual: int`
  - `template_config: TemplateConfig` (reference)
  - Tous les champs actuels

**Packages consommateurs:**
- `sd-generator-cli` - Écrit manifest.json
- `sd-generator-watchdog` - Lit manifest.json
- `sd-generator-webui` - Lit manifest.json (API)

### Structure du package

```
packages/sd-generator-common/
├── sd_generator_common/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── manifest.py  # ManifestModel
│   └── py.typed
├── pyproject.toml
└── README.md
```

### Dépendances

```toml
[tool.poetry.dependencies]
python = "^3.10"
pydantic = "^2.0"  # Validation + serialization
```

## Tasks

- [x] Créer package `sd-generator-common`
- [x] Définir `ManifestModel` avec Pydantic
- [x] **Implémenter `_resume_latest_active_session()` dans watchdog** (FIX PRINCIPAL)
  - Query DB pour latest session via repository
  - Check manifest status
  - Start observer si `status = ongoing` ou `in_progress`
  - Appelé après `initial_catchup()` dans `run()`
- [x] Update Watchdog pour détecter status et stop watching
  - Détecte `completed` ET `aborted` pour stop watching
- [x] Update `tools/build.py` pour checker tous les packages Python
  - Ajout de `sd-generator-common` et `sd-generator-watchdog` aux checks
  - Linting, type checking, complexity, dead code, security sur tous les packages
  - Package `common` est 100% clean (0 erreurs)
- [ ] Ajouter `status` field au manifest dans CLI
- [ ] Update CLI pour set status (ongoing/completed/aborted)
- [ ] Migrer packages existants vers common models
- [ ] Tests pour FSM transitions

## Implementation Notes

### Watchdog Resume Fix (session_sync.py)

**Method `_resume_latest_active_session()`:**
- Query DB via repository: `self.service.repository.list_all()`
- Get latest session (first item, sorted DESC)
- Read manifest.json and check `status` field
- If status = "ongoing" or "in_progress" → start watching
- Graceful error handling (no crash if repo unavailable)

**Integration:**
- Called in `run()` after `initial_catchup()` completes
- Before `start_watching()` to avoid race conditions

**Status Detection:**
- Handler `on_modified()` checks manifest status on each update
- Stops watching on `status in ("completed", "aborted")`
- Supports legacy "in_progress" status for backward compatibility

**Location:** `packages/sd-generator-watchdog/sd_generator_watchdog/session_sync.py:223-265`

## Notes

- Le watchdog doit aussi détecter `aborted` et stop watching (pas juste `completed`) ✅
- Besoin de gérer SIGTERM/SIGINT dans CLI pour set status correctement
- Package common = fondation pour éviter drift de schema long-terme
- Fix principal implémenté : watchdog resume automatiquement le watching au startup
