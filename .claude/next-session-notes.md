# Notes pour la prochaine session

**Date:** 2025-10-15
**Contexte restant:** 9%

## ⚠️ État actuel

On s'est perdus dans les détails techniques du mode dev/production. On a implémenté un système avec `SD_GENERATOR_DEV_MODE` env var, mais **on n'a jamais testé le vrai workflow utilisateur final**.

## 🎯 Ce qu'on doit faire

### Objectif : Tester l'expérience utilisateur lambda

**User persona:**
- Pas dev
- A installé Automatic1111
- Veut générer des milliers d'images avec templates
- Fait `pip install sd-generator-cli sd-generator-webui`
- Lance `sdgen webui start`
- Ouvre http://localhost:8000 → Interface web fonctionne

### Workflow de test à faire

```bash
# 1. Builder le frontend (production)
cd /mnt/d/StableDiffusion/local-sd-generator/packages/sd-generator-webui/front
npm run build  # Crée front/dist/

# 2. Builder les packages Python
cd ../
poetry build  # Crée wheel avec front/dist/ embedded

cd ../../sd-generator-cli
poetry build  # Crée wheel du CLI

# 3. Créer un venv de test (simuler installation user)
cd /tmp
python3 -m venv test-sdgen
source test-sdgen/bin/activate

# 4. Installer depuis les wheels
pip install /path/to/sd-generator-cli/dist/*.whl
pip install /path/to/sd-generator-webui/dist/*.whl

# 5. Lancer comme un user (SANS dev.webui_path dans config)
sdgen webui start

# 6. Vérifier
curl http://localhost:8000  # Doit servir le frontend
curl http://localhost:8000/api/mode  # Doit dire "production"
```

## 📦 Ce qui est déjà fait

### Backend (main.py)
- ✅ Détection du mode via `SD_GENERATOR_DEV_MODE` env var
- ✅ Mode production par défaut (sans env var)
- ✅ Serve frontend static depuis `front/dist/` en production
- ✅ Page dev avec bandeau jaune si pas de build
- ✅ Catch-all route pour SPA routing

### CLI (daemon.py)
- ✅ Détecte dev mode via `dev.webui_path` dans config
- ✅ Passe `SD_GENERATOR_DEV_MODE=1` au backend si dev
- ✅ Skip frontend launch en production (servi par backend)
- ✅ Lance Vite dev server en mode dev

### Build system
- ✅ `build.py` pour builder frontend avant packaging
- ✅ `SKIP_FRONTEND_BUILD=1` pour editable install
- ✅ `pyproject.toml` inclut `front/dist/` dans wheel

### Packages installés en editable
- ✅ CLI : `pip install -e packages/sd-generator-cli`
- ✅ WebUI : `SKIP_FRONTEND_BUILD=1 pip install -e packages/sd-generator-webui`

## 🐛 Problème actuel (non résolu)

L'env var `SD_GENERATOR_DEV_MODE` ne passe pas au backend quand lancé via `poetry run uvicorn` avec `--reload`.

**Log montrait:**
```
DEBUG: SD_GENERATOR_DEV_MODE = None
✓ Mode PRODUCTION (default)
```

**Raisons possibles:**
- `poetry run` crée un subprocess qui n'hérite pas des env vars
- `--reload` d'uvicorn crée un reloader process + worker process
- Les env vars ne sont pas propagées correctement

**Mais:** On s'en fout pour le test utilisateur final! En production il n'y a pas de `poetry run`, c'est directement le script Python installé.

## 🎯 Prochaines actions

1. **Builder le frontend** (pour avoir `front/dist/`)
2. **Builder les wheels** avec `poetry build`
3. **Tester installation propre** dans un venv isolé
4. **Vérifier que ça marche** sans aucun config dev
5. **Si ça marche** → On est bons! Commit et doc
6. **Si ça marche pas** → Debug avec le vrai workflow user

## 📝 Notes techniques

### Structure attendue du wheel

```
sd-generator-webui/
├── sd_generator_webui/          # Package Python
│   ├── __init__.py
│   ├── main.py
│   └── ...
└── front/
    └── dist/                     # Frontend buildé (embedded)
        ├── index.html
        ├── assets/
        └── ...
```

### Détection en production

Quand installé via pip :
```python
import sd_generator_webui
package_root = Path(sd_generator_webui.__file__).parent.parent.parent
frontend_dist = package_root / "front" / "dist"
# frontend_dist doit exister et contenir index.html
```

### Commandes user finales

```bash
# Installation
pip install sd-generator-cli sd-generator-webui

# Usage
sdgen webui start  # Backend sur :8000 avec frontend embedded
sdgen webui stop
sdgen webui status

# Génération
sdgen generate -t template.yaml
```

## 🔧 Outils à utiliser

- MCP Playwright pour tester l'interface web
- `curl` pour tester les endpoints
- `poetry build` pour créer les wheels
- Venv isolé pour simuler user install

## 💡 Rappel important

**Ne PAS se perdre dans le mode dev!** Le mode dev c'est pour nous. L'objectif c'est que l'utilisateur final ait une expérience simple sans configuration.

---

**Prochaine session :** Commencer par builder et tester le workflow production complet.
