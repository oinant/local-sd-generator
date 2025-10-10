# Claude Code Configuration

## A Savoir :
- le MCP Playwright est installé, sers-t'en!
- **Lis la doc dans `/docs`** - Structure organisée par composant (CLI, WebApp, Tooling)
- **IMPORTANT : Sous WSL, utiliser `python3` et non `python`**
- Les tests sont dans `/CLI/tests` et utilisent pytest

## ⚠️ Configuration Critique

**Le fichier `.sdgen_config.json` DOIT être dans le home directory (`~/.sdgen_config.json`) !**

```bash
# Créer/modifier la config
sdgen init

# Fichier créé : ~/.sdgen_config.json
# Contenu :
{
  "configs_dir": "/path/to/your/templates",
  "output_dir": "/path/to/output",
  "api_url": "http://127.0.0.1:7860"
}
```

**NE PAS** mettre la config dans le dossier du projet, elle ne sera pas trouvée depuis d'autres répertoires.

## 📁 Structure du Projet

Le projet utilise la **structure src/ layout** (meilleure pratique Python moderne) :

```
local-sd-generator/
├── CLI/                    # Package CLI (générateur SD)
│   ├── src/               # Code source (PYTHONPATH configuré sur src/)
│   │   ├── api/          # Client API SD WebUI
│   │   ├── templating/   # Template System V2.0
│   │   │   ├── models/         # Data models (TemplateConfig, etc.)
│   │   │   ├── loaders/        # YAML loading & parsing
│   │   │   ├── validators/     # Template validation
│   │   │   ├── resolvers/      # Inheritance, imports, template resolution
│   │   │   ├── generators/     # Prompt generation (combinatorial/random)
│   │   │   ├── normalizers/    # Prompt normalization
│   │   │   ├── utils/          # Hash & path utilities
│   │   │   └── orchestrator.py # V2Pipeline main orchestrator
│   │   ├── config/       # Configuration globale
│   │   └── execution/    # Exécution et orchestration
│   ├── tests/            # Tests unitaires et d'intégration
│   │   ├── api/          # Tests API client (76 tests)
│   │   ├── templating/   # Tests parsing V2 (3 tests)
│   │   ├── v2/           # Tests V2 complets (227 tests)
│   │   │   ├── unit/           # Tests unitaires
│   │   │   └── integration/    # Tests d'intégration
│   │   └── legacy/       # Anciens tests fonctionnels
│   ├── src/cli.py        # Point d'entrée CLI (Typer)
│   └── pyproject.toml    # Configuration package CLI
├── backend/              # Backend FastAPI (anciennement /api/)
│   └── pyproject.toml
├── front/                # Frontend (si existant)
├── venv/                 # Virtual environment Python
└── docs/                 # Documentation
```

**Note importante** : Le dossier backend était anciennement nommé `/api/`, ce qui créait un conflit de noms avec `/CLI/src/api/`. Il a été renommé en `/backend/` pour éviter les problèmes d'imports Python.

## 🎯 Template System V2.0

Le système de templates V2.0 est le **seul système actif** du projet.

**Fonctionnalités principales:**
- 🔗 **Inheritance** - Héritage avec `implements:` (multi-niveau)
- 📦 **Modular imports** - Imports avec `imports:` (fichiers YAML ou strings inline)
- 🧩 **Reusable chunks** - Chunks réutilisables avec `chunks:`
- 🎲 **Advanced selectors** - `[random:N]`, `[limit:N]`, `[indexes:1,5,8]`, `[keys:foo,bar]`
- ⚖️ **Weight-based loops** - Contrôle de l'ordre des boucles avec `weight:`
- 🎨 **Generation modes** - Combinatorial (toutes combinaisons) ou Random (échantillonnage)
- 🌱 **Seed modes** - Fixed, Progressive, Random

**V1 (Phase 2) status:** ❌ Supprimé (migration complète vers V2)

## 🐍 Python Environment Setup

### Virtual Environment
Le projet utilise un venv Linux (`venv/`) à la racine du projet :

```bash
# Créer le venv (déjà fait)
python3 -m venv venv

# Activer le venv
source venv/bin/activate

# Installer les dépendances
pip install pyyaml requests pytest pytest-cov

# Désactiver
deactivate
```

**Note:** Ne PAS utiliser `.venv/` (venv Windows verrouillé sous WSL).

### Running Tests

**IMPORTANT:**
- **TOUJOURS activer le venv d'abord** : `source venv/bin/activate` (depuis la racine du projet)
- Toujours utiliser `python3 -m pytest` (pas `python` ni `pytest` directement)
- Pytest 8.x requiert des `__init__.py` dans tous les dossiers de tests (structure package-based)

```bash
# ÉTAPE 1 : Activer le venv (depuis la racine du projet)
cd /mnt/d/StableDiffusion/local-sd-generator
source venv/bin/activate

# ÉTAPE 2 : Aller dans /CLI
cd CLI

# ÉTAPE 3 : Lancer les tests

# Tests V2 complets (227 tests) - 96.5% de réussite
python3 -m pytest tests/v2/ -v

# Tests API client (76 tests) - 100% ✅
python3 -m pytest tests/api/ -v

# Tests templating/parsing (3 tests) - 100% ✅
python3 -m pytest tests/templating/ -v

# Tous les tests (sans legacy)
python3 -m pytest tests/ --ignore=tests/legacy -v

# Avec couverture de code (pytest-cov)
python3 -m pytest tests/v2/ --cov=templating --cov-report=term-missing -v
```

**Alternative sans activer le venv (moins pratique) :**
```bash
cd /mnt/d/StableDiffusion/local-sd-generator/CLI
../venv/bin/python3 -m pytest tests/v2/ -v
```

**Structure des tests :**
```
CLI/tests/
├── api/               # Tests API client (76 tests) ✅
├── templating/        # Tests parsing V2 (3 tests) ✅
├── v2/                # Tests V2 système (227 tests) 🟢 96.5%
│   ├── unit/          # Tests unitaires (générateurs, resolvers, etc.)
│   └── integration/   # Tests d'intégration (API, executor)
├── integration/       # Tests d'intégration globaux
└── legacy/            # Anciens tests fonctionnels
```

**Total : 306 tests (300 passent - 98%)**

**Pourquoi `python3 -m pytest` ?**
- `pytest` seul ne détecte pas toujours le bon PYTHONPATH
- `python3 -m pytest` ajoute le répertoire courant automatiquement
- Résout les `ModuleNotFoundError` dans les imports
- Sous WSL, toujours utiliser `python3` et pas `python`

**Tests problématiques connus :**
- 8 tests V2 échouent (caching et validation de conflits) - bugs pré-existants
- `test_config_selector.py` - Peut bloquer (tests CLI interactive avec input() mocké)

### Code Quality Tools

Le projet utilise plusieurs outils d'analyse de code pour maintenir la qualité :

**Outils installés** (dans `CLI/pyproject.toml`, section `[project.optional-dependencies].dev`) :
- `flake8` - Style checker (PEP 8)
- `radon` - Analyseur de complexité cyclomatique
- `vulture` - Détecteur de code mort
- `bandit` - Scanner de sécurité
- `mypy` - Type checker (statique)

**Installation des outils :**
```bash
# Les outils sont déjà référencés dans CLI/pyproject.toml
# Installer directement :
venv/bin/pip install flake8 radon vulture bandit mypy
```

**Commandes d'analyse :**

```bash
# Depuis la racine du projet

# 1. Style checking (PEP 8)
venv/bin/python3 -m flake8 CLI \
  --exclude=tests,__pycache__,private_generators,example_* \
  --max-line-length=120 \
  --count --statistics

# 2. Complexité cyclomatique
# -a : moyenne, -nb : pas de note globale
venv/bin/python3 -m radon cc CLI \
  --exclude="tests,__pycache__,private_generators,example_*" \
  -a -nb

# 3. Code mort (dead code)
cd CLI && ../venv/bin/python3 -m vulture . \
  --min-confidence=80 2>&1 | \
  grep -v "tests/" | grep -v "example_"

# 4. Sécurité
# -r : recursif, -ll : low/low severity (moins verbeux)
venv/bin/python3 -m bandit -r CLI -ll -f txt

# 5. Type checking (optionnel, peut être verbeux)
venv/bin/python3 -m mypy CLI --ignore-missing-imports
```

**Analyse complète :**
```bash
# Lancer tous les checks d'un coup
cd /mnt/d/StableDiffusion/local-sd-generator
venv/bin/python3 -m flake8 CLI --exclude=tests,private_generators --max-line-length=120 && \
venv/bin/python3 -m radon cc CLI --exclude="tests,private_generators" -a && \
echo "✓ Quality checks passed"
```

**Seuils de complexité (radon) :**
- **A (1-5)** : Simple ✅
- **B (6-10)** : Modéré ✅ (acceptable)
- **C (11-20)** : Complexe 🟡 (à surveiller)
- **D (21-30)** : Très complexe 🟠 (refactor recommandé)
- **E (31-40)** : Extrêmement complexe 🔴 (refactor urgent)
- **F (41+)** : Non maintenable 💀 (refactor immédiat)

**Rapports d'analyse :**
- Voir `docs/tooling/code_review_2025-10-06.md` pour la dernière code review manuelle
- Voir `docs/tooling/automated_metrics_2025-10-06.md` pour les métriques objectives

## 📖 Documentation Guidelines

### 📁 Structure de la documentation

```
docs/
├── cli/          # Documentation CLI
│   ├── usage/    # Guides utilisateur
│   └── technical/ # Documentation technique
├── front/        # Documentation Frontend
├── api/          # Documentation API
├── tooling/      # Documentation outils dev
└── roadmap/      # Planning des features
    ├── done/     # Features terminées
    ├── wip/      # En cours
    ├── next/     # Prochaines tâches
    └── future/   # Backlog futur
```

### 📝 Quand travailler sur une feature

#### 1. **Avant de commencer**
- Créer ou déplacer la spec dans `docs/roadmap/wip/`
- La spec doit contenir :
  - **Status** : wip
  - **Priority** : 1-10
  - **Description** : Quoi et pourquoi
  - **Implementation** : Approche technique
  - **Tasks** : Liste détaillée des tâches
  - **Success Criteria** : Critères de complétion
  - **Tests** : Plan de tests

#### 2. **Pendant le développement**
- Maintenir la doc technique à jour dans `docs/{cli|front|api|tooling}/technical/`
- Documenter les décisions importantes :
  - Pourquoi tel choix plutôt qu'un autre ?
  - Quels trade-offs ont été faits ?
  - Quelles alternatives ont été considérées ?
- Ajouter des exemples d'usage dans `docs/{cli|front|api|tooling}/usage/` au fur et à mesure

#### 3. **Quand c'est terminé**
- Déplacer la spec de `wip/` vers `done/`
- Ajouter dans la spec :
  - Date de complétion
  - Nombre de tests et leur statut
  - Hash des commits principaux
  - Liens vers la doc technique/usage
- Mettre à jour la doc utilisateur si nécessaire
- Vérifier que l'architecture est documentée dans `technical/`
- Mettre à jour le `README.md` du composant si nouveaux concepts

### 🎯 Contenu des specs roadmap

Chaque fichier dans `roadmap/{done|wip|next|future}/` doit suivre ce template :

```markdown
# Feature Name

**Status:** done|wip|next|future
**Priority:** 1-10
**Component:** cli|front|api|tooling
**Created:** YYYY-MM-DD
**Completed:** YYYY-MM-DD (si done)

## Description
Quoi et pourquoi...

## Implementation
Approche technique...

## Tasks
- [ ] Task 1
- [ ] Task 2

## Success Criteria
- Critère 1
- Critère 2

## Tests
- X tests unitaires
- Y tests d'intégration

## Documentation
- Usage: docs/cli/usage/xxx.md
- Technical: docs/cli/technical/xxx.md

## Commits (si done)
- abc1234: commit message
```

### 🔄 Lifecycle des features

```
future/ → next/ → wip/ → done/
```

### 📊 Priorities

- **1-3** : Critique (sprint actuel)
- **4-6** : Important (prochain sprint)
- **7-8** : Nice-to-have (futur)
- **9-10** : Recherche/expérimental

## 🔍 Code Review Guidelines

Avant de commencer une code review, consulter ces documents :

### Documents de référence
- **[Code Review Guidelines](docs/tooling/CODE_REVIEW_GUIDELINES.md)** - Directives complètes pour les code reviews
  - Principes SOLID et architecture
  - Qualité du code (complexité, lisibilité, DRY)
  - Organisation et documentation
  - Performance et sécurité
  - Checklist par fichier (~30-35 min)
  - Red flags et problèmes courants

- **[Code Review Action Templates](docs/tooling/CODE_REVIEW_ACTION_TEMPLATES.md)** - Templates pour actions post-review
  - 6 templates de fiches d'action détaillés
  - Matrice de priorisation (Criticité × Effort)
  - Workflows d'exécution (simple/complexe)
  - Dashboard de suivi et validation
  - Templates GitHub Issues et communication

### Processus de code review

**Phase 1 : Review**
1. Lire les guidelines dans `CODE_REVIEW_GUIDELINES.md`
2. Reviewer les fichiers avec la checklist
3. Identifier les problèmes (🔴 Bloquant, 🟠 Important, 🟡 Suggestion, 💡 Question)

**Phase 2 : Actions**
1. Créer fiches d'action avec templates appropriés
2. Prioriser selon matrice (P1-P5)
3. Planifier dans sprints

**Phase 3 : Exécution**
1. Suivre workflows selon taille (Small/Medium/Large)
2. Tracker progrès avec dashboard
3. Valider avec checklist avant fermeture

### Outils automatiques recommandés
```bash
# Style et qualité
flake8 CLI/ --max-line-length=120
mypy CLI/ --strict

# Complexité
radon cc CLI/ -a -nb

# Code mort
vulture CLI/

# Sécurité
bandit -r CLI/
```

## 🚀 CLI Usage

### Generate images from template

```bash
# Interactive mode (liste les templates disponibles)
python3 src/cli.py generate

# Direct template
python3 src/cli.py generate -t path/to/template.prompt.yaml

# Limit number of images
python3 src/cli.py generate -t template.yaml -n 50

# Dry-run (save API payloads as JSON without generating)
python3 src/cli.py generate -t template.yaml --dry-run
```

### Other commands

```bash
# List all available templates
python3 src/cli.py list

# Validate a template file
python3 src/cli.py validate path/to/template.yaml

# Initialize global config
python3 src/cli.py init

# API introspection
python3 src/cli.py api samplers
python3 src/cli.py api schedulers
python3 src/cli.py api models
python3 src/cli.py api upscalers
python3 src/cli.py api model-info
```

## 📦 Project Status

**Current version:** V2.0 (stable)
**Template system:** V2.0 only (V1 removed)
**Tests:** 306 total (98% pass rate)
**Last major migration:** 2025-10-10 (V1→V2 complete)

## Commands
- **Lint:** `flake8 CLI/ --max-line-length=120`
- **Test:** `python3 -m pytest tests/ --ignore=tests/legacy -v`
- **Coverage:** `python3 -m pytest tests/v2/ --cov=templating --cov-report=term-missing`
- **Build:** À déterminer
