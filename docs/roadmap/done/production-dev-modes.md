# Production vs Dev Modes

**Status:** done
**Priority:** 1
**Component:** webui
**Created:** 2025-10-15
**Completed:** 2025-10-15

## Description

Implémentation d'un système à deux modes pour le WebUI :
- **Mode Production** : Frontend pré-buildé embedded dans le package Python, servi par FastAPI
- **Mode Dev** : Frontend sources + Vite dev server séparé

## Implementation

### Mode Production (pip install)

**Caractéristiques :**
- Frontend pré-buildé (HTML/CSS/JS static) inclus dans le wheel Python
- FastAPI sert les fichiers static via `StaticFiles`
- **Aucune dépendance Node.js** pour l'utilisateur final
- Détection automatique : pas de `dev.webui_path` dans config

**Installation utilisateur :**
```bash
pip install sd-generator-webui
sdgen webui start  # Lance uniquement le backend FastAPI
# Frontend accessible sur http://localhost:8000
```

**Build et packaging :**
```bash
cd packages/sd-generator-webui
poetry build  # Exécute build.py automatiquement
# Le wheel contient front/dist/
```

### Mode Dev (monorepo)

**Caractéristiques :**
- Frontend sources + Vite dev server (HMR, hot reload)
- Backend FastAPI séparé avec --reload
- CORS configuré pour communication cross-origin
- Détection : présence de `dev.webui_path` dans `sdgen_config.json`

**Développement :**
```bash
cd local-sd-generator
# Ajouter dans sdgen_config.json :
{
  "dev": {
    "webui_path": "/path/to/packages/sd-generator-webui"
  }
}

sdgen start  # Lance backend (8000) + frontend (5173)
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
```

## Tasks

- [x] Créer `build.py` pour build frontend avant packaging
- [x] Modifier `main.py` pour détecter le mode et servir static
- [x] Ajouter `get_frontend_path()` pour localiser le build
- [x] Monter `/assets` en mode production
- [x] Ajouter catch-all route pour Vue Router SPA
- [x] Modifier `daemon.py` pour détecter le mode
- [x] Skip frontend launch en mode production
- [x] Ajouter `is_dev_mode()` helper
- [x] Mettre à jour `pyproject.toml` avec build script
- [x] Inclure `front/dist/**/*` dans le wheel
- [x] Tester mode dev (pas de build)
- [x] Documenter les deux modes

## Success Criteria

- ✅ Backend détecte automatiquement le mode au démarrage
- ✅ Mode production : FastAPI sert le frontend static
- ✅ Mode dev : Vite dev server lancé séparément
- ✅ Pas de dépendance Node en production
- ✅ SPA routing fonctionne en production (catch-all)
- ✅ Poetry build inclut le frontend dans le wheel

## Technical Details

### Backend Detection (main.py)

```python
def get_frontend_path() -> Path:
    """
    Priority:
    1. Packaged build (production): ../front/dist
    2. Monorepo dev mode: ../../front/dist
    """
    # Check if front/dist exists with index.html
```

**Startup behavior:**
- Si `front/dist/` trouvé → `app.state.production_mode = True`
- Monte `/assets` pour les fichiers static
- Route `/` sert `index.html`
- Catch-all `/{full_path:path}` pour SPA routing

### CLI Detection (daemon.py)

```python
def is_dev_mode() -> bool:
    """Check presence of dev.webui_path in config"""
    config = load_global_config()
    return "webui_path" in config.get("dev", {})
```

**start_frontend() behavior:**
- Si `is_dev_mode()` → Lance Vite dev server
- Sinon → Print "Production mode" et return None

### Poetry Build (build.py)

```python
def build():
    # 1. npm install (ensure dependencies)
    # 2. npm run build (create dist/)
    # 3. Verify dist/ exists
```

**pyproject.toml:**
```toml
[tool.poetry.build]
script = "build.py"

include = [
    { path = "front/dist/**/*", format = "wheel" }
]
```

## Tests

**Mode Dev (sans build):**
```bash
# Config avec dev.webui_path
sdgen webui start
# ✓ Backend prints "Mode DEV"
# ✓ Frontend Vite lancé sur :5173
```

**Mode Production (avec build):**
```bash
cd packages/sd-generator-webui/front
npm run build  # Créer dist/
cd ..
sdgen webui start  # Sans dev.webui_path dans config
# ✓ Backend prints "Mode PRODUCTION"
# ✓ Pas de Vite lancé
# ✓ http://localhost:8000 sert le frontend
```

**Poetry build:**
```bash
cd packages/sd-generator-webui
poetry build
# ✓ build.py exécuté
# ✓ Wheel contient front/dist/
unzip -l dist/*.whl | grep "front/dist"
```

## Documentation

- Technical: docs/cli/technical/config-system.md (dev config)
- Usage: docs/cli/reference/cli-commands.md (webui commands)
- Architecture: Ce document

## Benefits

**Pour les utilisateurs finaux :**
- Installation simple : `pip install sd-generator-webui`
- Pas besoin de Node.js installé
- Une seule commande : `sdgen webui start`
- Pas de configuration frontend

**Pour les développeurs :**
- Hot reload avec Vite (dev rapide)
- Backend auto-reload avec uvicorn
- Sources séparées (meilleure DX)
- Build automatique avant publish

**Pour la distribution :**
- Package Python autonome
- Pas de dépendances externes (Node)
- Wheel contient tout
- PyPI-ready

## Future Enhancements

- [ ] Cloudflare Tunnel support pour remote access
- [ ] Frontend build optimization (code splitting)
- [ ] Service worker pour offline support
- [ ] CDN pour assets en production

## Commits

- df54364: feat(cli): Add dev config support for webui package detection
- e71a94a: feat(webui): Add production/dev mode detection with static serving

---

**Last updated:** 2025-10-15
**Status:** Complete ✅
