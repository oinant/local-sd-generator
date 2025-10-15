# CLI Commands Reference

**Référence complète de toutes les commandes CLI V2.0**

---

## Installation et Setup

### Prérequis

```bash
# Python 3.8+
python3 --version

# Stable Diffusion WebUI running
# http://127.0.0.1:7860
```

### Installation

```bash
# Clone du repository
git clone <repository-url>
cd local-sd-generator

# Installation des dépendances
python3 -m pip install -r requirements.txt
```

---

## Commandes principales

### `generate` - Génération d'images

**Usage** :
```bash
# Mode interactif (liste les templates disponibles)
sdgen generate

# Template spécifique
sdgen generate -t path/to/template.prompt.yaml
sdgen generate --template path/to/template.prompt.yaml

# Limiter le nombre d'images
sdgen generate -t template.yaml -n 50
sdgen generate -t template.yaml --count 50

# Dry-run (sauvegarde JSON sans générer)
sdgen generate -t template.yaml --dry-run

# URL API personnalisée
sdgen generate -t template.yaml --api-url http://192.168.1.100:7860
```

**Options** :

| Option | Raccourci | Type | Description |
|--------|-----------|------|-------------|
| `--template` | `-t` | path | Chemin vers le template |
| `--count` | `-n` | int | Limite le nombre d'images |
| `--dry-run` | - | flag | Génère JSON sans appeler l'API |
| `--api-url` | - | url | URL de l'API SD (défaut: http://127.0.0.1:7860) |

**Exemples** :

```bash
# Génération simple
sdgen generate -t prompts/portrait.prompt.yaml

# Test rapide (5 images)
sdgen generate -t prompts/test.prompt.yaml -n 5

# Dry-run pour vérifier
sdgen generate -t prompts/test.yaml --dry-run

# API distante
sdgen generate -t prompts/test.yaml --api-url http://192.168.1.50:7860
```

**Sortie** :

```
apioutput/
└── 20251014_143052_portrait/
    ├── portrait_0001.png
    ├── portrait_0002.png
    ├── ...
    └── portrait_manifest.json
```

---

### `list` - Lister les templates

**Usage** :
```bash
# Liste tous les templates disponibles
sdgen list

# Liste avec chemin complet
sdgen list --full-path
```

**Options** :

| Option | Raccourci | Type | Description |
|--------|-----------|------|-------------|
| `--full-path` | - | flag | Affiche le chemin complet |

**Sortie** :

```
Available templates:
  1. Portrait Simple (prompts/portrait_simple.prompt.yaml)
  2. Character Sheet (prompts/character_sheet.prompt.yaml)
  3. Landscape Test (prompts/landscape.prompt.yaml)
  ...
```

---

### `validate` - Valider un template

**Usage** :
```bash
# Valider un template
sdgen validate path/to/template.yaml

# Valider avec verbose
sdgen validate path/to/template.yaml -v
sdgen validate path/to/template.yaml --verbose
```

**Options** :

| Option | Raccourci | Type | Description |
|--------|-----------|------|-------------|
| `--verbose` | `-v` | flag | Affiche les détails de validation |

**Validation checks** :
- ✅ Schéma YAML valide
- ✅ Champs obligatoires présents
- ✅ Fichiers référencés existent (`implements`, `imports`, `chunks`)
- ✅ Pas de dépendances circulaires
- ✅ Placeholders cohérents (tous ont un import)

**Sortie (succès)** :

```
✅ Template is valid
  Name: Portrait Simple
  Variations: 2 (Expression, Outfit)
  Total combinations: 20
  Mode: combinatorial
  Seed mode: progressive
```

**Sortie (erreur)** :

```
❌ Template validation failed

Errors:
  - Missing required field: generation.mode
  - File not found: ../variations/missing.yaml
  - Placeholder {Expression} has no corresponding import
```

---

### `init` - Initialiser la configuration

**Usage** :
```bash
# Créer ~/.sdgen_config.json avec valeurs par défaut
sdgen init

# Avec valeurs personnalisées
sdgen init --configs-dir /path/to/templates
sdgen init --output-dir /path/to/output
sdgen init --api-url http://localhost:7860
```

**Options** :

| Option | Type | Description |
|--------|------|-------------|
| `--configs-dir` | path | Dossier des templates |
| `--output-dir` | path | Dossier de sortie |
| `--api-url` | url | URL de l'API SD |

**Fichier créé** :

**`~/.sdgen_config.json`**
```json
{
  "configs_dir": "/mnt/d/StableDiffusion/private-new/prompts",
  "output_dir": "/mnt/d/StableDiffusion/apioutput",
  "api_url": "http://127.0.0.1:7860"
}
```

**Ordre de recherche** :
1. `~/.sdgen_config.json` (home directory)
2. Valeurs par défaut

**Note** : Le fichier **DOIT** être dans le home directory (`~`) pour être trouvé depuis n'importe quel répertoire.

---

### `api` - Introspection de l'API SD

Commandes pour interroger l'API Stable Diffusion WebUI.

#### `api samplers` - Lister les samplers

**Usage** :
```bash
sdgen api samplers
```

**Sortie** :

```
Available samplers:
  - DPM++ 2M Karras
  - DPM++ SDE Karras
  - DPM++ 2M SDE Exponential
  - DPM++ 2M SDE Karras
  - Euler a
  - Euler
  - LMS
  - Heun
  - DPM2
  - DPM2 a
  - DPM++ 2S a
  - DPM++ 2M
  - DPM++ SDE
  - DPM fast
  - DPM adaptive
  - LMS Karras
  - DPM2 Karras
  - DPM2 a Karras
  - DPM++ 2S a Karras
  - Restart
  - DDIM
  - PLMS
  - UniPC
```

---

#### `api schedulers` - Lister les schedulers

**Usage** :
```bash
sdgen api schedulers
```

**Sortie** :

```
Available schedulers:
  - Automatic
  - Uniform
  - Karras
  - Exponential
  - Polyexponential
  - SGM Uniform
  - KL Optimal
  - Align Your Steps
  - Simple
  - Normal
  - DDIM
  - Beta
```

**Note** : Disponible seulement si SD WebUI 1.9+

---

#### `api models` - Lister les modèles/checkpoints

**Usage** :
```bash
sdgen api models
```

**Sortie** :

```
Available models:
  - model1.safetensors [hash123]
  - model2.ckpt [hash456]
  - sdxl_base.safetensors [hash789]
  ...
```

---

#### `api upscalers` - Lister les upscalers

**Usage** :
```bash
sdgen api upscalers
```

**Sortie** :

```
Available upscalers:
  - None
  - Lanczos
  - Nearest
  - ESRGAN_4x
  - LDSR
  - R-ESRGAN 4x+
  - R-ESRGAN 4x+ Anime6B
  - ScuNET GAN
  - ScuNET PSNR
  - SwinIR 4x
  - 4x_foolhardy_Remacri
  - 4x-UltraSharp
  ...
```

---

#### `api model-info` - Informations sur le modèle actuel

**Usage** :
```bash
sdgen api model-info
```

**Sortie** :

```
Current model:
  Name: model1.safetensors
  Hash: abc123def456
  Title: My Custom Model
  Filename: /path/to/model1.safetensors
```

---

## Environment Management Commands

### `start` - Start all services

**Usage** :
```bash
# Start backend + frontend only
sdgen start

# Start with Automatic1111 (Windows from WSL)
sdgen start --start-a1111

# With custom A1111 path
sdgen start --start-a1111 --a1111-bat /mnt/d/sd/webui.bat

# Custom ports
sdgen start --backend-port 8080 --frontend-port 3000

# Backend only (no frontend)
sdgen start --no-frontend

# Disable backend auto-reload
sdgen start --no-reload
```

**Options** :

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--start-a1111` | flag | false | Start Automatic1111 on Windows |
| `--a1111-bat` | path | from config | Path to webui.bat |
| `--backend-port` | int | 8000 | Backend server port |
| `--frontend-port` | int | 5173 | Frontend dev server port |
| `--no-frontend` | flag | false | Don't start frontend |
| `--no-reload` | flag | false | Disable backend auto-reload |

**Services started** :
- Automatic1111 WebUI (if `--start-a1111`)
- Backend FastAPI server (uvicorn)
- Frontend Vite dev server (unless `--no-frontend`)

**Note** : All services run in background (non-blocking)

---

### `stop` - Stop all services

**Usage** :
```bash
# Stop all running services
sdgen stop
```

**Stops** :
- Automatic1111 (if managed by sdgen)
- Backend server
- Frontend server

**Behavior** :
1. Graceful shutdown (SIGTERM) with 5s timeout
2. Force kill (SIGKILL) if still alive
3. Cleanup PID files

---

### `status` - Show service status

**Usage** :
```bash
# Show status of all services
sdgen status
```

**Output** :
```
Service Status
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━┓
┃ Service         ┃ Status   ┃ PID   ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━┩
│ Automatic1111   │ Running  │ 12345 │
│ Backend API     │ Running  │ 12346 │
│ Frontend        │ Running  │ 12347 │
└─────────────────┴──────────┴───────┘

Log files: ~/.sdgen/logs/
PID files: ~/.sdgen/pids/
```

---

### `webui` - WebUI management

Subcommands for managing backend + frontend only (without Automatic1111).

#### `webui start` - Start WebUI services

**Usage** :
```bash
# Start backend + frontend
sdgen webui start

# Custom ports
sdgen webui start --backend-port 8080 --frontend-port 3000

# Disable auto-reload
sdgen webui start --no-reload
```

**Options** :

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--backend-port` | int | 8000 | Backend server port |
| `--frontend-port` | int | 5173 | Frontend dev server port |
| `--no-reload` | flag | false | Disable backend auto-reload |

---

#### `webui stop` - Stop WebUI services

**Usage** :
```bash
# Stop backend + frontend
sdgen webui stop
```

---

#### `webui restart` - Restart WebUI services

**Usage** :
```bash
# Restart backend + frontend
sdgen webui restart

# With custom ports
sdgen webui restart --backend-port 8080
```

---

#### `webui status` - Show WebUI status

**Usage** :
```bash
# Show status of backend + frontend
sdgen webui status
```

**Output** :
```
WebUI Status
┏━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━┓
┃ Service  ┃ Status   ┃ PID  ┃
┡━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━┩
│ Backend  │ Running  │ 1234 │
│ Frontend │ Running  │ 1235 │
└──────────┴──────────┴──────┘
```

---

### Service Management Details

**PID Files** : `~/.sdgen/pids/`
- `automatic1111.pid`
- `backend.pid`
- `frontend.pid`

**Log Files** : `~/.sdgen/logs/`
- `automatic1111.log`
- `backend.log`
- `frontend.log`

**Dev Config** :

Add to `sdgen_config.json` for development mode:
```json
{
  "dev": {
    "webui_path": "/path/to/local-sd-generator/packages/sd-generator-webui"
  }
}
```

**WebUI Package Detection** :

Priority order:
1. `dev.webui_path` from config (dev mode)
2. Python import (pip install)
3. Monorepo structure (relative path)

---

## Commandes avancées

### Debugging et Verbose

```bash
# Génération avec logs détaillés
sdgen generate -t template.yaml -v

# Validation avec détails
sdgen validate template.yaml --verbose
```

### Combiner options

```bash
# Dry-run + limit + verbose
sdgen generate -t template.yaml --dry-run -n 10 -v

# Liste avec chemins complets
sdgen list --full-path

# Init avec toutes les options
sdgen init \
  --configs-dir /path/to/templates \
  --output-dir /path/to/output \
  --api-url http://192.168.1.100:7860
```

---

## Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `SDGEN_CONFIG_DIR` | Dossier des templates | Depuis config |
| `SDGEN_OUTPUT_DIR` | Dossier de sortie | Depuis config |
| `SDGEN_API_URL` | URL de l'API SD | `http://127.0.0.1:7860` |

**Usage** :

```bash
export SDGEN_API_URL=http://192.168.1.100:7860
sdgen generate -t template.yaml
```

---

## Codes de sortie

| Code | Signification |
|------|---------------|
| `0` | Succès |
| `1` | Erreur de validation |
| `2` | Erreur de configuration |
| `3` | Erreur d'API |
| `4` | Fichier non trouvé |

---

## Exemples de workflows

### Workflow de développement

```bash
# 1. Créer un template
vim prompts/test.prompt.yaml

# 2. Valider
sdgen validate prompts/test.prompt.yaml

# 3. Dry-run (vérifier JSON)
sdgen generate -t prompts/test.prompt.yaml --dry-run

# 4. Test rapide (5 images)
sdgen generate -t prompts/test.prompt.yaml -n 5

# 5. Production (toutes les images)
sdgen generate -t prompts/test.prompt.yaml
```

### Workflow de production

```bash
# 1. Lister les templates disponibles
sdgen list

# 2. Valider avant génération
sdgen validate prompts/production.prompt.yaml

# 3. Générer
sdgen generate -t prompts/production.prompt.yaml

# 4. Vérifier les résultats
ls -lh apioutput/20251014_*/
```

### Workflow d'introspection API

```bash
# Vérifier les samplers disponibles
sdgen api samplers

# Vérifier les schedulers
sdgen api schedulers

# Vérifier le modèle actif
sdgen api model-info

# Mettre à jour le template avec les valeurs correctes
vim prompts/template.yaml
```

---

## Troubleshooting

### Erreur : "Connection refused"

**Problème** : API SD WebUI non accessible

**Solution** :
```bash
# Vérifier que SD WebUI est lancé
curl http://127.0.0.1:7860/

# Lancer SD WebUI avec API
cd stable-diffusion-webui
./webui.sh --api

# Ou spécifier URL différente
sdgen generate -t template.yaml --api-url http://192.168.1.100:7860
```

---

### Erreur : "Template not found"

**Problème** : Fichier template non trouvé

**Solution** :
```bash
# Vérifier le chemin
sdgen list

# Utiliser chemin absolu
sdgen generate -t /absolute/path/to/template.yaml

# Vérifier config
cat ~/.sdgen_config.json
```

---

### Erreur : "Validation failed"

**Problème** : Template invalide

**Solution** :
```bash
# Valider avec verbose pour détails
sdgen validate template.yaml -v

# Vérifier fichiers référencés existent
ls -l variations/*.yaml

# Vérifier syntaxe YAML
yamllint template.yaml
```

---

## Voir aussi

- **[Template Syntax](template-syntax.md)** - Syntaxe des templates
- **[Selectors Reference](selectors-reference.md)** - Sélecteurs disponibles
- **[Getting Started](../guide/getting-started.md)** - Guide de démarrage
- **[Troubleshooting Guide](../guide/troubleshooting.md)** - Problèmes courants

---

**Dernière mise à jour** : 2025-10-14
**Version du système** : V2.0
