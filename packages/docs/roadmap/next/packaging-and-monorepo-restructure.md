# Packaging & Monorepo Restructure

**Status:** next
**Priority:** 3
**Component:** tooling
**Created:** 2025-10-15

## Description

Restructurer le projet en monorepo avec deux packages pip distincts et documentation VitePress. L'objectif est de rendre le projet installable via pip avec une séparation claire entre CLI et WebUI, tout en offrant une commande unifiée pour lancer le stack complet.

## Motivation

- 📦 **Distribution simplifiée** : Installation via `pip install sd-generator-cli`
- 🔧 **Flexibilité d'usage** : CLI seule OU WebUI (qui inclut CLI)
- 📚 **Documentation centralisée** : Site statique VitePress déployable
- 🚀 **DX améliorée** : Commande `sdgen serve` pour tout lancer
- 🌐 **Tunneling intégré** : Support Cloudflare Tunnel, ngrok, localhost.run

## Architecture cible

### Structure monorepo

```
local-sd-generator/
├── packages/
│   ├── sd-generator-cli/           # Package 1: CLI seule
│   │   ├── sd_generator_cli/       # Code source
│   │   │   ├── __init__.py
│   │   │   ├── cli.py
│   │   │   ├── serve.py           # NEW: Commande sdgen serve
│   │   │   ├── api/
│   │   │   ├── templating/
│   │   │   └── config/
│   │   ├── tests/
│   │   ├── pyproject.toml          # Poetry config
│   │   └── README.md
│   │
│   ├── sd-generator-webui/         # Package 2: WebUI (dépend de CLI)
│   │   ├── backend/                # FastAPI backend
│   │   │   ├── sd_generator_webui/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── main.py
│   │   │   │   ├── routers/
│   │   │   │   └── services/
│   │   │   └── tests/
│   │   ├── front/                  # VueJS frontend
│   │   │   ├── src/
│   │   │   ├── public/
│   │   │   ├── package.json
│   │   │   └── vite.config.js
│   │   ├── pyproject.toml          # Poetry config
│   │   └── README.md
│   │
│   └── docs/                       # VitePress documentation
│       ├── .vitepress/
│       │   └── config.ts
│       ├── guide/
│       ├── cli/
│       ├── webui/
│       ├── index.md
│       └── package.json
│
├── .gitignore
├── README.md
└── pyproject.toml                  # Workspace root (optionnel)
```

### Packages PyPI

**Package 1: `sd-generator-cli`**
- CLI autonome pour génération d'images
- Commande principale : `sdgen`
- Sous-commandes : `generate`, `list`, `validate`, `init`, `api`, `serve`

**Package 2: `sd-generator-webui`**
- Backend FastAPI + Frontend Vue/Vite
- Dépend de `sd-generator-cli` (installé automatiquement)
- Commande : `sdgen-web` ou via `sdgen serve`

**Package 3: Documentation**
- Site statique VitePress
- Déployable sur GitHub Pages / Netlify / Vercel
- URLs : `/guide/`, `/cli/`, `/webui/`, `/api/`

## Implementation

### Phase 1: Restructuration fichiers (2-3h)

**Tâches :**
- [ ] Créer structure `packages/` avec sous-dossiers
- [ ] Migrer code CLI : `CLI/src/` → `packages/sd-generator-cli/sd_generator_cli/`
- [ ] Migrer code backend : `backend/` → `packages/sd-generator-webui/backend/sd_generator_webui/`
- [ ] Migrer frontend : `front/` → `packages/sd-generator-webui/front/`
- [ ] Créer dossier `packages/docs/` pour VitePress
- [ ] Migrer tests vers nouvelles structures

**Migration des imports :**
```python
# Ancien
from api import SDAPIClient
from templating.orchestrator import V2Pipeline
from config.global_config import load_global_config

# Nouveau
from sd_generator_cli.api import SDAPIClient
from sd_generator_cli.templating.orchestrator import V2Pipeline
from sd_generator_cli.config.global_config import load_global_config
```

### Phase 2: Configuration Poetry (1-2h)

**Créer `packages/sd-generator-cli/pyproject.toml` :**
```toml
[tool.poetry]
name = "sd-generator-cli"
version = "0.1.0"
description = "CLI for Stable Diffusion image generation with advanced templating"
authors = ["SDGEN Team"]
readme = "README.md"
packages = [{include = "sd_generator_cli"}]

[tool.poetry.dependencies]
python = "^3.10"
pyyaml = "^6.0"
requests = "^2.28.0"
typer = {extras = ["all"], version = "^0.9.0"}
rich = "^13.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-cov = "^4.1.0"
flake8 = "^7.0.0"
mypy = "^1.8.0"

[tool.poetry.scripts]
sdgen = "sd_generator_cli.cli:app"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**Créer `packages/sd-generator-webui/pyproject.toml` :**
```toml
[tool.poetry]
name = "sd-generator-webui"
version = "0.1.0"
description = "Web UI for Stable Diffusion image generation"
authors = ["SDGEN Team"]
readme = "README.md"
packages = [{include = "sd_generator_webui", from = "backend"}]

[tool.poetry.dependencies]
python = "^3.10"
sd-generator-cli = {path = "../sd-generator-cli", develop = true}
fastapi = "^0.110.0"
uvicorn = {extras = ["standard"], version = "^0.27.0"}
python-multipart = "^0.0.9"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
httpx = "^0.27.0"

[tool.poetry.scripts]
sdgen-web = "sd_generator_webui.main:run"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### Phase 3: Commande `sdgen serve` (3-4h)

**Créer `packages/sd-generator-cli/sd_generator_cli/serve.py` :**

Fonctionnalités :
- Lance backend FastAPI (uvicorn)
- Lance frontend Vite (npm run dev)
- Lance tunnel optionnel (Cloudflare, ngrok, localhost.run)
- Gestion gracieuse du shutdown (Ctrl+C)
- Configuration via CLI args ou `sdgen_config.json`

**Commandes principales :**
```python
@app.command(name="serve")
def serve(
    backend_port: int = typer.Option(8000, "--backend-port", "-bp"),
    frontend_port: int = typer.Option(5173, "--frontend-port", "-fp"),
    tunnel: Optional[str] = typer.Option(None, "--tunnel", "-t"),
    no_frontend: bool = typer.Option(False, "--no-frontend"),
    no_reload: bool = typer.Option(False, "--no-reload"),
):
    """
    Launch the complete SD Generator stack.

    Examples:
        sdgen serve                        # Launch everything
        sdgen serve --tunnel cloudflare    # With tunnel
        sdgen serve --no-frontend          # Backend only
    """
```

**Gestion des processus :**
- `subprocess.Popen()` pour lancer backend, frontend, tunnel
- Liste de processus à terminer proprement
- Affichage Rich avec panels pour les statuts
- Détection automatique du package webui installé

### Phase 4: VitePress Documentation (2-3h)

**Initialiser VitePress :**
```bash
cd packages/docs
npm init -y
npm install -D vitepress vue
```

**Structure de la documentation :**
```
docs/
├── .vitepress/
│   └── config.ts              # Config navigation & sidebar
├── guide/
│   ├── index.md               # Introduction
│   ├── getting-started.md     # Installation & Quick Start
│   └── concepts.md            # Concepts clés
├── cli/
│   ├── index.md               # CLI Overview
│   ├── installation.md        # pip install sd-generator-cli
│   ├── usage.md               # sdgen generate, list, etc.
│   ├── templates.md           # Template System V2.0
│   └── configuration.md       # sdgen_config.json
├── webui/
│   ├── index.md               # WebUI Overview
│   ├── installation.md        # pip install sd-generator-webui
│   └── api-reference.md       # API FastAPI endpoints
└── index.md                   # Landing page
```

**Configuration `.vitepress/config.ts` :**
```typescript
import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'SD Generator',
  description: 'Advanced Stable Diffusion image generation tools',

  themeConfig: {
    nav: [
      { text: 'Guide', link: '/guide/' },
      { text: 'CLI', link: '/cli/' },
      { text: 'Web UI', link: '/webui/' }
    ],

    sidebar: {
      '/guide/': [/* ... */],
      '/cli/': [/* ... */],
      '/webui/': [/* ... */]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/yourusername/sd-generator' }
    ]
  }
})
```

**Scripts package.json :**
```json
{
  "scripts": {
    "dev": "vitepress dev",
    "build": "vitepress build",
    "preview": "vitepress preview"
  }
}
```

### Phase 5: Support Tunneling (1-2h)

**Services supportés :**

**Cloudflare Tunnel (recommandé) :**
- Installation : `brew install cloudflared` / `apt install cloudflared`
- Commande : `cloudflared tunnel --url http://localhost:8000`
- Génère URL publique : `https://random-name.trycloudflare.com`

**ngrok :**
- Installation : `brew install ngrok` / `snap install ngrok`
- Commande : `ngrok http 8000`
- Requiert compte gratuit pour URL persistante

**localhost.run :**
- Pas d'installation (utilise SSH natif)
- Commande : `ssh -R 80:localhost:8000 localhost.run`
- Génère URL publique instantanée

**Implémentation dans `serve.py` :**
```python
def start_tunnel(service: str, port: int):
    if service == "cloudflare":
        cmd = ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"]
    elif service == "ngrok":
        cmd = ["ngrok", "http", str(port)]
    elif service == "localhost.run":
        cmd = ["ssh", "-R", f"80:localhost:{port}", "localhost.run"]

    return subprocess.Popen(cmd)
```

### Phase 5.1: Support Automatic1111 sur Windows depuis WSL (1-2h)

**Problématique WSL ↔ Windows :**
- CLI lancée depuis WSL (Linux)
- Automatic1111 doit tourner sur Windows natif (perf CUDA)
- Besoin de lancer `webui.bat` Windows depuis WSL

**Implémentation `start_automatic1111_windows()` :**
```python
def start_automatic1111_windows(bat_path: str) -> Optional[subprocess.Popen]:
    """
    Lance Automatic1111 sur Windows depuis WSL.

    Args:
        bat_path: Chemin vers webui.bat (format WSL ou Windows)

    Returns:
        Popen object ou None si erreur
    """
    try:
        # Convertir chemin WSL → Windows avec wslpath
        if bat_path.startswith("/mnt/"):
            result = subprocess.run(
                ["wslpath", "-w", bat_path],
                capture_output=True,
                text=True,
                check=True
            )
            win_path = result.stdout.strip()
        else:
            win_path = bat_path

        # Vérifier existence du fichier
        check_cmd = ["cmd.exe", "/c", "if", "exist", win_path, "echo", "EXISTS"]
        result = subprocess.run(check_cmd, capture_output=True, text=True)

        if "EXISTS" not in result.stdout:
            console.print(f"[red]✗ File not found: {win_path}[/red]")
            return None

        # Lancer le .bat en arrière-plan (nouvelle fenêtre Windows)
        cmd = ["cmd.exe", "/c", "start", "/min", win_path]

        return subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except Exception as e:
        console.print(f"[red]✗ Error starting Automatic1111: {e}[/red]")
        return None

def is_automatic1111_running(api_url: str) -> bool:
    """Vérifie si Automatic1111 répond déjà."""
    try:
        import requests
        response = requests.get(f"{api_url}/sdapi/v1/options", timeout=2)
        return response.status_code == 200
    except:
        return False
```

**Intégration dans `serve()` :**
```python
@app.command(name="serve")
def serve(
    backend_port: int = typer.Option(8000, "--backend-port", "-bp"),
    frontend_port: int = typer.Option(5173, "--frontend-port", "-fp"),
    tunnel: Optional[str] = typer.Option(None, "--tunnel", "-t"),

    # NEW: Support Automatic1111
    start_a1111: bool = typer.Option(False, "--start-a1111", help="Start Automatic1111 on Windows"),
    a1111_bat: Optional[str] = typer.Option(None, "--a1111-bat", help="Path to webui.bat"),

    no_frontend: bool = typer.Option(False, "--no-frontend"),
    no_reload: bool = typer.Option(False, "--no-reload"),
):
    """
    Launch the complete SD Generator stack.

    Examples:
        sdgen serve                                    # Backend + Frontend
        sdgen serve --start-a1111                      # + Start A1111 (uses config)
        sdgen serve --start-a1111 --a1111-bat /mnt/d/sd/webui.bat  # Custom path
        sdgen serve --tunnel cloudflare                # With public URL
    """
    processes = []

    try:
        # 0. Start Automatic1111 (si demandé)
        if start_a1111:
            console.print("\n[cyan]Starting Automatic1111 on Windows...[/cyan]")

            # Charger chemin depuis config si non fourni
            if not a1111_bat:
                serve_config = load_serve_config()
                a1111_bat = serve_config.get("automatic1111", {}).get("bat_path")

            if not a1111_bat:
                console.print("[red]✗ No webui.bat path configured[/red]")
                console.print("[yellow]Set in sdgen_config.json or use --a1111-bat[/yellow]")
            else:
                # Vérifier si déjà en cours
                if is_automatic1111_running(global_config.api_url):
                    console.print("[yellow]⚠ Automatic1111 already running, skipping[/yellow]")
                else:
                    a1111_proc = start_automatic1111_windows(a1111_bat)
                    if a1111_proc:
                        processes.append(("Automatic1111", a1111_proc))
                        console.print(f"[green]✓ Automatic1111 started[/green]")
                        console.print(f"[dim]Waiting 10s for API startup...[/dim]")
                        import time
                        time.sleep(10)  # Laisser A1111 démarrer

        # 1. Start backend
        # ... reste du code
```

**Commandes utilisateur :**
```bash
# Lancer tout (backend + frontend + A1111 sur Windows)
sdgen serve --start-a1111

# Avec tunnel
sdgen serve --start-a1111 --tunnel cloudflare

# Override chemin .bat
sdgen serve --start-a1111 --a1111-bat /mnt/d/autre/webui.bat

# Sans A1111 (le lancer manuellement)
sdgen serve
```

**Configuration WSL/Windows dans `sdgen_config.json` :**
```json
{
  "configs_dir": "./prompts",
  "output_dir": "./results",
  "api_url": "http://172.29.128.1:7860",

  "serve": {
    "backend_port": 8000,
    "frontend_port": 5173,
    "auto_reload": true,

    "automatic1111": {
      "enabled": false,
      "bat_path": "/mnt/d/StableDiffusion/stable-diffusion-webui/webui.bat",
      "startup_wait": 10,
      "args": "--api --listen"
    },

    "tunnel": {
      "enabled": false,
      "service": "cloudflare"
    }
  }
}
```

**Note CUDA/WSL :**
- WSL2 a une couche de virtualisation pour CUDA (moins performant)
- Lancer Automatic1111 sur Windows natif = meilleures perfs
- Bridge réseau WSL ↔ Windows via IP `172.29.128.1` (gateway WSL)

### Phase 6: Configuration étendue (1h)

**Étendre `sdgen_config.json` :**
```json
{
  "configs_dir": "./prompts",
  "output_dir": "./results",
  "api_url": "http://172.29.128.1:7860",

  "serve": {
    "backend_port": 8000,
    "frontend_port": 5173,
    "auto_reload": true,
    "tunnel": {
      "enabled": false,
      "service": "cloudflare"
    }
  }
}
```

**Lecture de la config dans `serve.py` :**
```python
def load_serve_config():
    from .config.global_config import load_global_config
    config = load_global_config()
    return config.get("serve", {})
```

### Phase 7: Tests & Documentation (2-3h)

**Tests à ajouter :**
- [ ] Test import des packages après installation
- [ ] Test commande `sdgen --help`
- [ ] Test `sdgen serve` (mock subprocess)
- [ ] Test détection package webui
- [ ] Test parsing config `serve` section

**Documentation à créer :**
- [ ] README.md principal (monorepo)
- [ ] packages/sd-generator-cli/README.md
- [ ] packages/sd-generator-webui/README.md
- [ ] Guide installation dans VitePress
- [ ] Guide tunneling dans VitePress

### Phase 8: Publication (1h)

**Workflow de release :**
```bash
# 1. Build CLI
cd packages/sd-generator-cli
poetry build

# 2. Build WebUI
cd packages/sd-generator-webui
poetry build

# 3. Publier sur PyPI
poetry publish  # Depuis chaque package

# 4. Build & deploy docs
cd packages/docs
npm run build
# → Déployer .vitepress/dist/ sur GitHub Pages
```

## Success Criteria

- [ ] Structure monorepo créée avec 3 packages distincts
- [ ] `pip install sd-generator-cli` fonctionne
- [ ] `pip install sd-generator-webui` fonctionne (installe CLI aussi)
- [ ] Commande `sdgen serve` lance backend + frontend
- [ ] Commande `sdgen serve --start-a1111` lance Automatic1111 sur Windows depuis WSL
- [ ] Détection automatique si A1111 déjà lancé
- [ ] Commande `sdgen serve --tunnel cloudflare` génère URL publique
- [ ] Site VitePress accessible localement (`npm run dev`)
- [ ] Site VitePress buildable (`npm run build`)
- [ ] Tous les tests passent après migration
- [ ] Documentation complète dans VitePress

## Tests

**Tests unitaires :**
- Test import packages après `pip install`
- Test CLI entry point (`sdgen --help`)
- Test détection WebUI installée
- Test parsing config serve
- Test conversion chemin WSL → Windows (`wslpath`)
- Test détection A1111 déjà lancé (`is_automatic1111_running`)

**Tests d'intégration :**
- Test `sdgen serve` (mock subprocess)
- Test arrêt gracieux (Ctrl+C)
- Test modes : `--no-frontend`, `--no-reload`, `--start-a1111`
- Test lancement A1111 avec chemin custom

**Tests manuels :**
- Installation depuis PyPI (test registry)
- Lancement `sdgen serve` complet
- Accès frontend http://localhost:5173
- Accès backend http://localhost:8000/docs
- Tunnel Cloudflare génère URL publique
- `sdgen serve --start-a1111` lance webui.bat sur Windows depuis WSL
- Détection si A1111 déjà lancé (pas de double lancement)

## Documentation

**Fichiers à créer/mettre à jour :**

- [x] Cette spec roadmap
- [ ] `packages/sd-generator-cli/README.md` - Installation & usage CLI
- [ ] `packages/sd-generator-webui/README.md` - Installation & usage WebUI
- [ ] `packages/docs/guide/getting-started.md` - Quick start complet
- [ ] `packages/docs/cli/installation.md` - Installation CLI détaillée
- [ ] `packages/docs/cli/serve.md` - Documentation commande serve
- [ ] `packages/docs/webui/installation.md` - Installation WebUI
- [ ] `/README.md` (root) - Overview du monorepo

## Commits

_(À remplir pendant l'implémentation)_

## Notes & Decisions

**Pourquoi Poetry plutôt que setuptools ?**
- Gestion des dépendances moderne
- Résolution automatique des versions
- Support workspace natif
- `poetry add --path` pour dépendances locales

**Pourquoi VitePress ?**
- Ultra rapide (Vite-powered)
- Markdown-first avec Vue components
- Theme par défaut excellent
- Build statique optimisé pour SEO

**Ordre de migration :**
1. CLI en premier (autonome)
2. WebUI ensuite (dépend de CLI)
3. Docs en dernier (référence les deux packages)

**Compatibilité ascendante :**
- Garder `CLI/src/cli.py` fonctionnel pendant transition
- Symlink temporaire pour tests existants
- Migration progressive des imports

## Dependencies

**Bloquants :**
- Aucun (peut démarrer immédiatement)

**Nice-to-have avant :**
- Tests CLI existants à 100% (actuellement 98%)
- Documentation technique à jour

## Risks & Mitigations

**Risque 1: Casser les imports existants**
- Mitigation : Faire migration progressive avec branch dédiée
- Tests complets avant merge

**Risque 2: Complexité Poetry pour nouveaux contributeurs**
- Mitigation : Documenter installation Poetry dans README
- Fournir Dockerfile alternatif

**Risque 3: Tunneling bloqué par firewalls**
- Mitigation : Fournir 3 options (Cloudflare, ngrok, localhost.run)
- Mode `--no-tunnel` par défaut

## Timeline estimée

**Total : ~17-22h**

- Phase 1 (Restructuration) : 2-3h
- Phase 2 (Poetry config) : 1-2h
- Phase 3 (sdgen serve) : 3-4h
- Phase 4 (VitePress) : 2-3h
- Phase 5 (Tunneling) : 1-2h
- Phase 5.1 (A1111 WSL/Windows) : 1-2h ⭐ NEW
- Phase 6 (Config étendue) : 1h
- Phase 7 (Tests & docs) : 2-3h
- Phase 8 (Publication) : 1h

**Sprint recommandé : 1 semaine**
- Jour 1-2 : Phases 1-2 (restructuration)
- Jour 3-4 : Phases 3-5.1 (serve + VitePress + tunneling + A1111)
- Jour 5 : Phases 6-7 (config + tests)
- Jour 6-7 : Phase 8 + polish + publication

## Next Steps

1. Créer branch `feat/packaging-monorepo`
2. Commencer Phase 1 (restructuration fichiers)
3. Valider structure avec tests smoke
4. Continuer phases 2-8 séquentiellement
