# Claude Code Configuration

## A Savoir :
- le MCP Playwright est installé, sers-t'en!
- **📚 Documentation centralisée dans `/docs/`** - Single source of truth (pas de packages/docs/)
- **📝 Syntaxe Template System V2** - **TOUJOURS consulter `.claude/syntax-reference.md`** avant de créer/modifier templates/prompts/chunks/themes/tests !
- **🎯 Roadmap sur GitHub Issues** - Voir `/docs/roadmap/README.md` pour organisation
- **🤖 Agent PO disponible** - Utiliser `/po` pour feature/bug analysis
- **🛠️ Build tool disponible** - `python3 tools/build.py` avant chaque commit important
- **📝 Fichiers de travail dans `.claude/`** - Préfixer avec timestamp `YYYYMMDD_HHMMSS-nom.md` (exemple: `20251110_213000-session-status-fsm.md`). **NE PAS** appliquer ce préfixe aux subfolders (agents/, commands/, etc.)
- **IMPORTANT : Sous WSL, utiliser `python3` et non `python`**
- Les tests sont dans `/packages/sd-generator-cli/tests/` et utilisent pytest
- url de l'api automatic1111: http://172.29.128.1:7860

## 📖 Terminologie

- **Run** : Une exécution de `sdgen generate`. Produit une session avec N variants.
- **Variant** : Une image générée avec une combinaison spécifique de variations.
- **Variation** : Une valeur possible pour un placeholder (ex: "punk_mohawk" pour {HairCut}).
- **Placeholder** : Variable dans le template (ex: {HairCut}, {HairColor}).
- **Theme** : Ensemble cohérent de fichiers de variations (ex: cyberpunk, pirates).
- **Session** : Dossier de sortie d'une run, contient les variants + manifest.json.

**Exemple** :
```bash
sdgen generate -t template.yaml --theme cyberpunk -n 100
```
→ 1 **run** génère 1 **session** avec 100 **variants**

Chaque **variant** a ses propres **variations** :
- Variant 001 : HairCut=punk_mohawk, HairColor=neon_blue
- Variant 002 : HairCut=cyber_bob, HairColor=electric_pink

## ⚠️ Configuration Critique

**Le fichier `sdgen_config.json` est dans le répertoire courant !**

Le fichier de config est **toujours** cherché dans le répertoire d'exécution (`./sdgen_config.json`).

```bash
# Créer/modifier la config (dans le répertoire courant)
cd /path/to/my-project
sdgen init

# Fichier créé : ./sdgen_config.json
# Contenu par défaut :
{
  "configs_dir": "./prompts",
  "output_dir": "./results",
  "api_url": "http://172.29.128.1:7860"
}
```

**Avantages :**
- Config par projet (versionnable avec git)
- Chaque projet est autonome
- Facilite le packaging et la distribution

## 📁 Structure du Projet

Le projet utilise une **structure monorepo avec packages/** :

```
local-sd-generator/
├── pyproject.toml                 # Root Poetry config (monorepo workspace)
├── poetry.lock                    # Poetry lock file (dependencies)
├── packages/
│   ├── sd-generator-cli/           # Package CLI (générateur SD)
│   │   ├── sd_generator_cli/       # Code source Python
│   │   │   ├── api/               # Client API SD WebUI
│   │   │   │   ├── sdapi_client.py
│   │   │   │   └── session_manager.py
│   │   │   ├── templating/        # Template System V2.0
│   │   │   │   ├── models/        # Data models (TemplateConfig, etc.)
│   │   │   │   ├── loaders/       # YAML loading & parsing
│   │   │   │   ├── validators/    # Template validation
│   │   │   │   ├── resolvers/     # Inheritance, imports, template resolution
│   │   │   │   ├── generators/    # Prompt generation (combinatorial/random)
│   │   │   │   ├── normalizers/   # Prompt normalization
│   │   │   │   ├── utils/         # Hash & path utilities
│   │   │   │   └── orchestrator.py # V2Pipeline main orchestrator
│   │   │   ├── config/            # Configuration globale
│   │   │   ├── execution/         # Exécution et orchestration
│   │   │   │   ├── manifest.py    # Manifest generation
│   │   │   │   └── executor.py
│   │   │   ├── commands/          # Commandes CLI
│   │   │   ├── cli.py             # Point d'entrée CLI (Typer)
│   │   │   └── commands.py        # Commandes principales
│   │   ├── tests/                 # Tests unitaires et d'intégration
│   │   │   ├── unit/              # Tests unitaires
│   │   │   │   ├── api/           # Tests API client
│   │   │   │   ├── execution/     # Tests manifest, executor
│   │   │   │   └── templating/    # Tests templating V2
│   │   │   ├── integration/       # Tests d'intégration
│   │   │   └── test_cli_commands.py
│   │   └── pyproject.toml         # Configuration package CLI
│   │
│   └── sd-generator-webui/        # Package WebUI
│       ├── backend/               # Backend FastAPI
│       │   ├── sd_generator_webui/
│       │   │   ├── api/
│       │   │   │   ├── sessions.py
│       │   │   │   └── images.py
│       │   │   ├── services/
│       │   │   ├── auth.py
│       │   │   ├── config.py
│       │   │   └── main.py
│       │   └── pyproject.toml
│       └── front/                 # Frontend Vue.js
│           ├── src/
│           ├── package.json
│           └── vite.config.js
│
├── venv/                          # Virtual environment Python
├── docs/                          # Documentation
├── apioutput/                     # Dossier de sortie des sessions
└── CLAUDE.md                      # Ce fichier
```

**Note importante** : Structure monorepo avec packages séparés pour CLI et WebUI, permettant un développement indépendant tout en partageant le venv.

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

### Package Management avec Poetry

Le projet utilise **Poetry** pour gérer les dépendances en mode monorepo. Poetry gère automatiquement le venv et les dépendances inter-packages.

**Installation initiale :**

```bash
# Depuis la racine du projet
cd /mnt/d/StableDiffusion/local-sd-generator

# Activer le venv (Poetry le détecte automatiquement)
source venv/bin/activate

# Installer toutes les dépendances + packages en mode éditable
poetry install

# Cela installe :
# - sd-generator-cli (editable mode)
# - sd-generator-webui (editable mode)
# - Toutes les dépendances (dev + runtime)
```

**Workflow de développement :**

```bash
# Ajouter une dépendance à un package
cd packages/sd-generator-cli
poetry add requests

# Mettre à jour les dépendances
cd /mnt/d/StableDiffusion/local-sd-generator
poetry update

# Réinstaller tout (après pull, changement de dépendances)
poetry install
```

**Avantages de Poetry :**
- ✅ **Pas de downgrade de dépendances** - Gestion propre des contraintes de versions
- ✅ **Mode éditable automatique** - Les packages sont en mode develop par défaut
- ✅ **Lock file** - Reproductibilité des installations (`poetry.lock`)
- ✅ **Monorepo support** - Gère correctement les dépendances entre packages

**Note:**
- Le venv est à la racine (`venv/`), partagé par tous les packages
- Ne PAS utiliser `.venv/` (venv Windows verrouillé sous WSL)
- Ne PAS utiliser `pip install -e .` directement, laisser Poetry gérer

### Alternative pip (non recommandée)

Si vous devez utiliser pip (CI/CD, etc.), **toujours** installer dans cet ordre :

```bash
# Activer venv
source venv/bin/activate

# Installer CLI en mode éditable d'abord (pour forcer typer 0.19.2)
cd packages/sd-generator-cli && pip install -e .

# Puis WebUI
cd ../sd-generator-webui && pip install -e .
```

⚠️ **Problème pip** : pip peut downgrader typer si on installe webui avant CLI.

### Running Tests

**IMPORTANT:**
- **TOUJOURS activer le venv d'abord** : `source venv/bin/activate` (depuis la racine du projet)
- Toujours utiliser `python3 -m pytest` (pas `python` ni `pytest` directement)
- Pytest 8.x requiert des `__init__.py` dans tous les dossiers de tests (structure package-based)

```bash
# ÉTAPE 1 : Activer le venv (depuis la racine du projet)
cd /mnt/d/StableDiffusion/local-sd-generator
source venv/bin/activate

# ÉTAPE 2 : Aller dans le package CLI
cd packages/sd-generator-cli

# ÉTAPE 3 : Lancer les tests

# Tous les tests
python3 -m pytest tests/ -v

# Tests unitaires seulement
python3 -m pytest tests/unit/ -v

# Tests d'intégration seulement
python3 -m pytest tests/integration/ -v

# Avec couverture de code (pytest-cov)
python3 -m pytest tests/ --cov=sd_generator_cli --cov-report=term-missing -v

# Tests CLI commands
python3 -m pytest tests/test_cli_commands.py -v
```

**Alternative sans activer le venv (moins pratique) :**
```bash
cd /mnt/d/StableDiffusion/local-sd-generator/packages/sd-generator-cli
../../venv/bin/python3 -m pytest tests/ -v
```

**Structure des tests :**
```
packages/sd-generator-cli/tests/
├── unit/                      # Tests unitaires
│   ├── api/                  # Tests API client (session_manager, sdapi_client)
│   ├── execution/            # Tests manifest, executor
│   └── templating/           # Tests templating V2
├── integration/              # Tests d'intégration
└── test_cli_commands.py      # Tests commandes CLI
```

**Pourquoi `python3 -m pytest` ?**
- `pytest` seul ne détecte pas toujours le bon PYTHONPATH
- `python3 -m pytest` ajoute le répertoire courant automatiquement
- Résout les `ModuleNotFoundError` dans les imports
- Sous WSL, toujours utiliser `python3` et pas `python`

### Code Quality Tools

Le projet utilise plusieurs outils d'analyse de code pour maintenir la qualité :

**Outils installés** (dans `packages/sd-generator-cli/pyproject.toml`) :
- `flake8` - Style checker (PEP 8)
- `radon` - Analyseur de complexité cyclomatique
- `vulture` - Détecteur de code mort
- `bandit` - Scanner de sécurité
- `mypy` - Type checker (statique)

**Installation des outils :**
```bash
# Les outils sont déjà dans le venv
# Si besoin de réinstaller :
venv/bin/pip install flake8 radon vulture bandit mypy
```

**Commandes d'analyse :**

```bash
# Depuis la racine du projet

# 1. Style checking (PEP 8)
venv/bin/python3 -m flake8 packages/sd-generator-cli/sd_generator_cli \
  --max-line-length=120 \
  --count --statistics

# 2. Complexité cyclomatique
# -a : moyenne, -nb : pas de note globale
venv/bin/python3 -m radon cc packages/sd-generator-cli/sd_generator_cli \
  -a -nb

# 3. Code mort (dead code)
cd packages/sd-generator-cli && ../../venv/bin/python3 -m vulture sd_generator_cli \
  --min-confidence=80

# 4. Sécurité
# -r : recursif, -ll : low/low severity (moins verbeux)
venv/bin/python3 -m bandit -r packages/sd-generator-cli/sd_generator_cli -ll -f txt

# 5. Type checking STRICT (détecte les erreurs d'attributs)
# IMPORTANT: Activer strict mode dans pyproject.toml ([tool.mypy] strict = true)
venv/bin/python3 -m mypy packages/sd-generator-cli/sd_generator_cli --show-error-codes
# OU pour check rapide d'un fichier :
venv/bin/python3 -m mypy packages/sd-generator-cli/sd_generator_cli/commands.py --show-error-codes
```

**Analyse complète :**
```bash
# Lancer tous les checks d'un coup
cd /mnt/d/StableDiffusion/local-sd-generator
venv/bin/python3 -m flake8 packages/sd-generator-cli/sd_generator_cli --max-line-length=120 && \
venv/bin/python3 -m radon cc packages/sd-generator-cli/sd_generator_cli -a -nb && \
venv/bin/python3 -m mypy packages/sd-generator-cli/sd_generator_cli --show-error-codes && \
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

**IMPORTANT:** La documentation est centralisée dans `/docs/` à la racine du projet (single source of truth).

> ⚠️ **Note historique:** Le dossier `packages/docs/` a été supprimé (commit `8426e90`, Oct 17 2025) car il créait une duplication issue de la tentative de restructuration monorepo. Toute la documentation est maintenant dans `/docs/` uniquement.

```
/mnt/d/StableDiffusion/local-sd-generator/
└── docs/                # 📚 Documentation centrale (SEUL EMPLACEMENT)
    ├── cli/             # Documentation CLI
    │   ├── guide/       # Getting started guides
    │   ├── reference/   # CLI commands reference
    │   ├── technical/   # Architecture & internals
    │   └── usage/       # Usage guides
    ├── webapp/          # Documentation Frontend
    ├── backend/         # Documentation API/Backend
    ├── tooling/         # Documentation outils dev
    │   ├── CODE_REVIEW_GUIDELINES.md
    │   ├── CODE_REVIEW_ACTION_TEMPLATES.md
    │   ├── type-checking-guide.md
    │   └── build-tool-usage.md
    └── roadmap/         # Planning des features
        ├── done/        # Features terminées
        ├── wip/         # En cours (work in progress)
        ├── next/        # Prochaines tâches
        ├── future/      # Backlog futur
        └── archive/     # Specs archivées
```

**Principes:**
- ✅ **Single source of truth:** Toute la doc est dans `/docs/`
- ✅ **Organization par composant:** cli/, webapp/, backend/, tooling/
- ✅ **Séparation technique/usage:** `/technical/` vs `/usage/` vs `/reference/`
- ❌ **PAS de duplication** dans packages/ ou ailleurs

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

## 🤖 Product Owner Agent

Le projet dispose d'un **agent PO autonome** pour gérer la roadmap et les spécifications fonctionnelles.

**Architecture :**
- 🤖 **Agent autonome** : `.claude/agents/po.md` (tourne en background)
- ⚡ **Slash command** : `.claude/commands/po.md` (invocation explicite)
- 📋 **Persistence** : `.claude/.braindump.md` (survie au compactage)

L'agent PO peut **tourner en background** et accumuler tes idées pendant que tu travailles, puis les structurer quand tu le demandes.

**🧠 Mode "Product Memory" :**
L'agent PO est ta mémoire produit - il sait ce qui existe déjà !
- Avant d'ajouter une idée, il check GitHub Issues + braindump + code
- Répond avec contexte : "On l'a déjà !" / "Ça n'existe pas" / "On a X mais pas Y"
- Pose des questions proactives pour clarifier
- Suggère des features liées que tu ne connais peut-être pas

### 🧠 Mode Braindump Automatique

**IMPORTANT : Détection automatique**

Quand l'utilisateur dit des choses comme :
- "Il faudrait que..."
- "J'ai pensé à..."
- "Tiens, on devrait..."
- "Bug : ..."
- "Idée : ..."
- "Je me demande si..."

**→ Tu DOIS automatiquement activer le mode Agent PO (braindump)**

**Process :**
1. **Accumuler** les idées dans `.claude/.braindump.md` (section "🆕 Pending Analysis")
   - **CRITIQUE** : Toujours écrire dans ce fichier pour survie au compactage de contexte
2. **Si doute** → Demander : "Tu veux que je structure ça avec l'agent PO ?"
3. Quand il a fini (ou qu'il demande explicitement), proposer :
   - "J'ai noté X idées/bugs/features. Je les passe à l'agent PO pour structurer ?"
4. Si l'utilisateur accepte → Simuler l'agent PO (ou utiliser `/po braindump:` si disponible)
   - Déplacer items de "🆕 Pending" → "🔍 Being Analyzed"
5. Parser, prioriser, catégoriser
6. Proposer création GitHub issues
7. **Mettre à jour** `.claude/.braindump.md` avec liens vers issues créées
   - Déplacer items de "🔍 Being Analyzed" → "📋 Tracked on GitHub"

**Règle d'or : En cas de doute, demander à l'utilisateur avant d'activer l'agent PO.**

**IMPORTANT : `.claude/.braindump.md` est la source de vérité pour les idées en cours.**
- Ce fichier survit au compactage de contexte
- Toujours le lire au début d'une session pour voir les items pending
- Toujours le mettre à jour quand on braindumpe

**Exemple de flow naturel :**
```
User: "Ah tiens, faudrait qu'on ajoute un cache pour les prompts"
Claude: *note l'idée* "Noté ! Autre chose ?"
User: "Ouais, et y'a un bug avec les thumbnails sur mobile"
Claude: *accumule* "Ok, bug thumbnails mobile. Continue ?"
User: "Non c'est tout pour l'instant"
Claude: "J'ai 2 items (1 feature, 1 bug). Je structure ça avec l'agent PO ?"
User: "Go"
Claude: *simule agent PO → parse, priorise, propose issues*
```

**Avantage :** Zéro friction cognitive - tu braindumpes naturellement, Claude gère le reste.

### Utilisation de l'agent PO

**Mode 1 : Naturel (recommandé) - Braindump pendant conversation**
```
User: "Ah tiens, faudrait ajouter un cache pour les prompts"
Claude: *détecte et accumule* "Noté ! Autre chose ?"
User: "Et y'a un bug avec les thumbnails mobile"
Claude: "Ok. Je structure ça avec l'agent PO ?"
User: "Go"
Claude: *parse, priorise, propose issues*
```

**Mode 2 : Explicite - Commandes `/po`**
```bash
# 🧠 BRAINDUMP (décharge mentale en vrac)
/po braindump: [description non-structurée d'idées/bugs/features]
# → L'agent parse, trie, priorise et propose des GitHub issues

# Analyser une nouvelle feature
/po feature: ajouter support pour weighted prompts

# Trier un bug
/po bug: les seeds progressives ne s'incrémentent pas

# Planifier un sprint
/po plan: prioriser la backlog pour les 2 prochaines semaines

# Auditer la roadmap
/po audit: vérifier la cohérence roadmap/GitHub Issues
```

**💡 Tu n'as PAS besoin d'appeler `/po` explicitement !**
Claude détecte automatiquement quand tu braindumpes et propose de structurer avec l'agent PO.

### Ce que fait l'agent PO

1. **Analyse fonctionnelle**
   - Use cases, user stories
   - Acceptance criteria (Given/When/Then)
   - Questions de clarification
   - Estimation valeur business (Low/Medium/High)

2. **Création GitHub Issues**
   - Via `gh` CLI (authentifié)
   - Labels appropriés (type, status, priority, component, area)
   - Description structurée avec acceptance criteria
   - Lien avec issues existantes si pertinent

3. **Priorisation**
   - Matrice valeur × effort
   - Recommandation P1-P10
   - Justification de la priorité

4. **Gestion bugs**
   - Impact (severity × frequency)
   - Steps to reproduce
   - Pistes d'investigation

### Output de l'agent

L'agent génère :
- **Analyse structurée** (problem statement, use cases, edge cases)
- **Acceptance criteria** (format Given/When/Then)
- **Proposition de GitHub issue** (titre, description, labels)
- **Questions de clarification** si besoin
- **Recommandation de priorité** avec justification

### Intégration avec GitHub Issues

- **Roadmap sur GitHub** : https://github.com/oinant/local-sd-generator/issues
- **Organisation par labels** : Voir `/docs/roadmap/README.md`
- **Workflow** : L'agent utilise `gh` CLI pour toutes les opérations GitHub

### Commandes gh CLI utiles

```bash
# Lister issues par statut
gh issue list --label "status: next" --state open
gh issue list --label "status: backlog" --state open

# Voir une issue spécifique
gh issue view 123

# Créer une issue (l'agent le fait automatiquement après validation)
gh issue create --title "[Feature] Titre" --body "Description" \
  --label "type: feature,priority: high,component: cli"

# Éditer une issue
gh issue edit 123 --add-label "status: wip"
```

### Workflow typique

**Mode Braindump (recommandé) :**
```
1. Toi : "/po braindump:
   J'ai pensé à plusieurs trucs :
   - ajouter un cache pour les prompts résolus
   - bug: les preview thumbnails sont cassées sur mobile
   - refacto: commands.py est trop gros
   - idée: système de plugins pour extensions
   - faudrait documenter le workflow V2"

2. Agent PO (analyse) :
   → Parse et catégorise chaque item
   → Priorise (High/Medium/Low)
   → Estime effort (Small/Medium/Large)
   → Détecte dépendances

3. Agent PO (output structuré) :
   🎯 High Priority:
   - [Bug] Mobile thumbnails broken (P2, Small)
   - [Refactor] Split commands.py (P4, Medium)

   📋 Medium Priority:
   - [Feature] Prompt cache (P6, Medium)
   - [Docs] Document V2 workflow (P7, Small)

   💡 Low Priority:
   - [Idea] Plugin system (P9, Large)

   "Should I create GitHub issues for High Priority items?"

4. Toi : "Oui, crée les issues High + le doc aussi"

5. Agent PO (création batch) :
   → gh issue create × 3
   → #46, #47, #48 créées
   → "Done! Want me to plan a sprint with these?"
```

**Mode Feature direct :**
```
1. Toi : "/po feature: cache pour prompts"

2. Agent PO (analyse en cours) :
   - Analyse le besoin (use cases, acceptance criteria)
   - Estime valeur + effort
   - Propose priorité + labels
   - Pose questions si nécessaire

3. Toi : Valides ou ajustes la spec

4. Agent PO (finalisation) :
   - Crée la GitHub issue via gh CLI
   - Notifie le numéro d'issue créé
   - L'issue est maintenant trackable sur GitHub
```

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
venv/bin/python3 -m flake8 packages/sd-generator-cli/sd_generator_cli --max-line-length=120
venv/bin/python3 -m mypy packages/sd-generator-cli/sd_generator_cli --strict

# Complexité
venv/bin/python3 -m radon cc packages/sd-generator-cli/sd_generator_cli -a -nb

# Code mort
cd packages/sd-generator-cli && ../../venv/bin/python3 -m vulture sd_generator_cli

# Sécurité
venv/bin/python3 -m bandit -r packages/sd-generator-cli/sd_generator_cli
```

## 🔒 Type Checking (mypy strict mode)

**CRITIQUE** : Les erreurs de type comme `'GlobalConfig' object has no attribute 'get'` **DOIVENT** être détectées avant l'exécution.

### Configuration

Le projet utilise **mypy en mode strict** dans `packages/sd-generator-cli/pyproject.toml` :
- `strict = true` : Détecte les erreurs d'attributs
- Force les type hints sur toutes les fonctions
- Catch les None implicites

### Workflow obligatoire

**Avant chaque commit :**
```bash
# Depuis la racine du projet
venv/bin/python3 -m mypy packages/sd-generator-cli/sd_generator_cli --show-error-codes
```

**Si erreurs → FIX avant de commit !**

### Règles de type hints

```python
# ❌ MAUVAIS : mypy ne check pas le corps sans return type
def start_command(dev_mode, backend_port):
    config = load_global_config()
    api_url = config.get("api_url")  # Erreur non détectée

# ✅ BON : mypy check le corps avec return type
def start_command(
    dev_mode: bool,
    backend_port: int
) -> None:  # 👈 Obligatoire pour que mypy check
    config = load_global_config()  # Type: GlobalConfig
    api_url = config.api_url  # ✅ Attribut direct
```

### Documentation complète

Voir `docs/tooling/type-checking-guide.md` pour :
- Guide complet du type checking
- Erreurs courantes et leur fix
- Pre-commit hook setup
- Bonnes/mauvaises pratiques

## 🚀 CLI Usage

**Note:** Le CLI peut être utilisé de deux façons :
- En mode développement : `python3 -m sd_generator_cli.cli` (depuis `packages/sd-generator-cli/`)
- Installé : `sdgen` (après `pip install -e .`)

### Generate images from template

```bash
# Depuis packages/sd-generator-cli/
cd packages/sd-generator-cli

# Interactive mode (liste les templates disponibles)
python3 -m sd_generator_cli.cli generate

# Direct template
python3 -m sd_generator_cli.cli generate -t path/to/template.prompt.yaml

# Limit number of images
python3 -m sd_generator_cli.cli generate -t template.yaml -n 50

# Dry-run (save API payloads as JSON without generating)
python3 -m sd_generator_cli.cli generate -t template.yaml --dry-run
```

### Other commands

```bash
# List all available templates
python3 -m sd_generator_cli.cli list

# Validate a template file
python3 -m sd_generator_cli.cli validate path/to/template.yaml

# Initialize global config
python3 -m sd_generator_cli.cli init

# API introspection
python3 -m sd_generator_cli.cli api samplers
python3 -m sd_generator_cli.cli api schedulers
python3 -m sd_generator_cli.cli api models
python3 -m sd_generator_cli.cli api upscalers
python3 -m sd_generator_cli.cli api model-info
```

### Installed usage (après pip install -e .)

```bash
# Si le package est installé en mode éditable
cd packages/sd-generator-cli
pip install -e .

# Ensuite, utiliser directement la commande
sdgen generate
sdgen list
sdgen api models
# etc.
```

## 🛠️ Build Tool

Le projet dispose d'un **build tool complet** dans `tools/build.py` qui exécute automatiquement tous les checks qualité.

### Ce que fait le build tool

**Checks automatiques :**
- ✅ **Python linting** (flake8) - Style PEP 8
- ✅ **Type checking** (mypy strict) - Détection erreurs de types
- ✅ **Tests + Coverage** (pytest) - Tests unitaires et intégration
- ✅ **Complexity analysis** (radon) - Complexité cyclomatique
- ✅ **Dead code detection** (vulture) - Code mort
- ✅ **Security scan** (bandit) - Vulnérabilités de sécurité
- ✅ **Frontend linting & build** - ESLint + Vite build
- ✅ **Python packaging** (poetry) - Validation package

**Output intelligent :**
- 📊 **Table résumé** avec statuts (✓ success / ⚠ warning / ✗ error)
- 🎯 **Top 5 priority actions** avec locations et valeurs cibles
- ⏱️ **Durée totale** d'exécution

### Quand utiliser le build tool

**🎯 Recommandation : Utiliser AVANT chaque commit important**

| Situation | Commande recommandée | Pourquoi |
|-----------|---------------------|----------|
| **Avant commit** | `python3 tools/build.py` | Check complet avant push |
| **Quick check pendant dev** | `python3 tools/build.py --skip-tests --skip-frontend` | Lint + types + complexity rapide |
| **Après refactoring** | `python3 tools/build.py` | Valider que rien n'est cassé |
| **Avant PR** | `python3 tools/build.py --verbose` | Full check avec détails |
| **CI/CD simulation** | `python3 tools/build.py --fail-fast` | Reproduire comportement CI |
| **Debug build failure** | `python3 tools/build.py --verbose` | Voir outputs complets |

### Workflow recommandé

```bash
# 1. Pendant le dev : checks rapides individuels
venv/bin/python3 -m mypy packages/sd-generator-cli/sd_generator_cli --show-error-codes

# 2. Avant commit : build complet
python3 tools/build.py

# 3. Si erreurs → Fix et re-run
python3 tools/build.py

# 4. Si OK → Commit
git add . && git commit -m "feat: ..."
```

### Usage complet

```bash
# Depuis la racine du projet
cd /mnt/d/StableDiffusion/local-sd-generator

# Build complet (recommandé avant commit)
python3 tools/build.py

# Build rapide (skip tests + frontend)
python3 tools/build.py --skip-tests --skip-frontend

# Build sans tests (plus rapide pour checks rapides)
python3 tools/build.py --skip-tests

# Build sans frontend
python3 tools/build.py --skip-frontend

# Build sans packaging
python3 tools/build.py --skip-package

# Build verbose (voir tous les outputs des commandes)
python3 tools/build.py --verbose

# Fail-fast (s'arrête à la première erreur)
python3 tools/build.py --fail-fast
```

### Exemple d'output

```
╭─────────────── Build Results ───────────────╮
│ Step               Status    Duration       │
│ ───────────────── ──────── ────────────    │
│ Python Linting      ✓        2.3s          │
│ Type Checking       ✓        4.1s          │
│ Unit Tests          ✓       12.5s          │
│ Complexity          ⚠        1.2s          │
│ Dead Code           ✓        0.8s          │
│ Security Scan       ✓        3.4s          │
╰─────────────────────────────────────────────╯

🎯 Top 5 Priority Actions:
1. [P10] COMPLEXITY: resolver.py - resolve_template() (CC: 15 → target: 10)
2. [P8]  COVERAGE: executor.py - Branch coverage 78% (target: 90%)
3. [P6]  COMPLEXITY: orchestrator.py - orchestrate() (CC: 12 → target: 10)

⏱️ Total duration: 24.3s
```

### Intégration avec pre-commit

Pour automatiser le build avant chaque commit :

```bash
# .git/hooks/pre-commit (optionnel)
#!/bin/bash
python3 tools/build.py --skip-frontend --fail-fast
```

### Troubleshooting

**Erreur : "rich library not found"**
```bash
venv/bin/pip install rich
```

**Erreur : "mypy not found"**
```bash
cd packages/sd-generator-cli
../../venv/bin/pip install -e .
```

**Build trop lent**
```bash
# Skip tests pendant dev actif
python3 tools/build.py --skip-tests --skip-frontend
```

### Alternative : Checks individuels

**⚠️ Moins recommandé** - Utiliser le build tool complet quand possible.

### Checks individuels (si nécessaire)

Si vous devez lancer un check spécifique rapidement :

```bash
# Depuis la racine du projet

# Lint (style)
venv/bin/python3 -m flake8 packages/sd-generator-cli/sd_generator_cli --max-line-length=120

# Lint (types - strict mode)
venv/bin/python3 -m mypy packages/sd-generator-cli/sd_generator_cli --show-error-codes

# Tests
cd packages/sd-generator-cli && ../../venv/bin/python3 -m pytest tests/ -v

# Coverage
cd packages/sd-generator-cli && ../../venv/bin/python3 -m pytest tests/ --cov=sd_generator_cli --cov-report=term-missing -v

# Package build
cd packages/sd-generator-cli && poetry build
```

**Note :** Ces commandes sont déjà intégrées dans `python3 tools/build.py`.

## 📦 Project Status

**Current version:** V2.0 (stable)
**Template system:** V2.0 only (V1 removed)
**Last major migration:** 2025-10-10 (V1→V2 complete)
**Build tool:** `tools/build.py` (voir section "🛠️ Build Tool")
