# Build Tool

**Status:** wip
**Priority:** 5
**Component:** tooling
**Created:** 2025-10-16

## Description

Créer un script de build complet (`tools/build.py`) qui exécute tous les checks de qualité, tests, et builds en une seule commande.

Objectif : Avoir une commande rapide pour valider que tout le projet est prêt avant un commit ou un déploiement.

## Use Cases

```bash
# Build complet (tous les checks)
python3 tools/build.py

# Skip certaines étapes
python3 tools/build.py --skip-tests
python3 tools/build.py --skip-frontend
python3 tools/build.py --skip-package

# Mode verbose (afficher output complet)
python3 tools/build.py --verbose

# Arrêter au premier échec
python3 tools/build.py --fail-fast
```

## Étapes du Build

### 1. Python Linting (flake8)
```bash
flake8 packages/sd-generator-cli/sd_generator_cli \
  --exclude=tests,__pycache__ \
  --max-line-length=120 \
  --count --statistics
```

**Output attendu :**
- Nombre de warnings/errors
- Status : ✓ ou ✗

### 2. Python Type Checking (mypy)
```bash
mypy packages/sd-generator-cli/sd_generator_cli --show-error-codes
```

**Output attendu :**
- Nombre d'erreurs de type
- Status : ✓ ou ✗

### 3. Python Tests + Coverage (pytest)
```bash
cd packages/sd-generator-cli
pytest tests/ -v --cov=sd_generator_cli --cov-report=term-missing
```

**Output attendu :**
- Nombre de tests passed/failed
- Coverage % global
- Modules avec coverage < 80%
- Status : ✓ ou ✗

### 4. Complexité Cyclomatique (radon)
```bash
radon cc packages/sd-generator-cli/sd_generator_cli \
  --exclude="tests,__pycache__" \
  -a -nb --json
```

**Output attendu :**
- Complexité moyenne
- Top 5 fonctions les plus complexes (> 10)
- Status : ⚠ si complexité moyenne > 5

### 5. Code Mort (vulture)
```bash
vulture packages/sd-generator-cli/sd_generator_cli \
  --min-confidence=80 \
  --exclude=tests
```

**Output attendu :**
- Nombre de variables/fonctions inutilisées
- Top 5 occurrences de code mort
- Status : ⚠ si > 10 occurrences

### 6. Sécurité (bandit)
```bash
bandit -r packages/sd-generator-cli/sd_generator_cli \
  -ll -f json
```

**Output attendu :**
- Nombre de vulnérabilités (high/medium/low)
- Top 5 problèmes de sécurité
- Status : ✗ si high/medium > 0

### 7. Frontend Linting (eslint)
```bash
cd packages/sd-generator-webui/front
npm run lint
```

**Output attendu :**
- Nombre de warnings/errors ESLint
- Status : ✓ ou ✗

### 8. Frontend Build (Vue.js)
```bash
cd packages/sd-generator-webui/front
npm run build
```

**Output attendu :**
- Build size
- Status : ✓ ou ✗

### 9. Python Packaging (poetry)
```bash
cd packages/sd-generator-cli
poetry build
```

**Output attendu :**
- Fichiers générés (.whl, .tar.gz)
- Status : ✓ ou ✗

## Rapport Final

Le script doit afficher un tableau récapitulatif :

```
╭──────────────────────── Build Report ────────────────────────╮
│                                                               │
│  ✓ Python Linting         0 errors                           │
│  ✓ Python Type Checking   0 errors                           │
│  ✓ Python Tests           306 passed, 98% coverage           │
│  ⚠ Complexity Analysis    avg 4.2, 3 functions > 10          │
│  ⚠ Dead Code Detection    12 unused variables                │
│  ✓ Security Scan          0 vulnerabilities                  │
│  ✓ Frontend Linting       0 errors                           │
│  ✓ Frontend Build         2.3 MB                             │
│  ✓ Python Packaging       sdgen-0.1.0.tar.gz created         │
│                                                               │
│  Overall: ⚠ WARNING (2 warnings)                             │
│                                                               │
╰───────────────────────────────────────────────────────────────╯

╭───────────────── Top 5 Priority Actions ─────────────────────╮
│                                                               │
│  1. [COMPLEXITY] Reduce complexity in orchestrator.py:120    │
│     Current: 15, Target: < 10                                │
│                                                               │
│  2. [COMPLEXITY] Refactor _generate() in cli.py:110          │
│     Current: 12, Target: < 10                                │
│                                                               │
│  3. [DEAD CODE] Remove unused import in resolver.py:10       │
│     Variable: old_function                                   │
│                                                               │
│  4. [COVERAGE] Add tests for import_resolver.py              │
│     Current: 65%, Target: > 80%                              │
│                                                               │
│  5. [DEAD CODE] Remove unused variable in cli.py:450         │
│     Variable: unused_var                                     │
│                                                               │
╰───────────────────────────────────────────────────────────────╯

Total duration: 45.2s
```

## Priorisation des Actions

Les actions prioritaires sont calculées avec ces critères :

1. **Sécurité** (poids 10) : Vulnérabilités bandit high/medium
2. **Type Safety** (poids 8) : Erreurs mypy
3. **Tests** (poids 7) : Coverage < 80%
4. **Complexité** (poids 6) : Fonctions avec complexité > 10
5. **Code Mort** (poids 3) : Variables/fonctions inutilisées

## Options

- `--skip-tests` : Skip tests et coverage
- `--skip-frontend` : Skip linting et build frontend
- `--skip-package` : Skip poetry build
- `--verbose` : Afficher output complet de chaque commande
- `--fail-fast` : Arrêter au premier échec (exit code 1)
- `--json` : Output en JSON pour CI/CD

## Implementation

### Structure

```python
# tools/build.py

class BuildStep:
    """Représente une étape du build"""
    name: str
    command: str
    enabled: bool
    critical: bool  # Si True, échec = arrêt du build

class BuildRunner:
    """Exécute les étapes et génère le rapport"""

    def run_step(self, step: BuildStep) -> StepResult
    def generate_report(self, results: List[StepResult]) -> Report
    def get_priority_actions(self, results: List[StepResult]) -> List[Action]
```

### Dépendances

- `rich` (déjà installé) pour les tableaux et progress bars
- `subprocess` (stdlib) pour exécuter les commandes
- `json` (stdlib) pour parser les outputs JSON
- `pathlib` (stdlib) pour les paths

### Exit Codes

- `0` : Tous les checks passent (warnings OK)
- `1` : Au moins un check critique échoue
- `2` : Erreur d'exécution du script

## Tasks

- [x] Créer fiche spec
- [ ] Créer `tools/build.py` avec structure de base
- [ ] Implémenter chaque étape de build
- [ ] Implémenter parsing des outputs (JSON, text)
- [ ] Implémenter calcul des actions prioritaires
- [ ] Implémenter génération du rapport Rich
- [ ] Implémenter options CLI (argparse)
- [ ] Tester sur le projet complet
- [ ] Documenter dans `docs/tooling/build-tool.md`

## Success Criteria

- ✅ Une commande lance tous les checks
- ✅ Rapport clair avec status de chaque étape
- ✅ Top 5 actions prioritaires affichées
- ✅ Options `--skip-*` fonctionnent
- ✅ Mode `--verbose` affiche output complet
- ✅ Exit code correct selon résultats
- ✅ Temps d'exécution < 2 minutes (sans skip)

## Notes

### Optimisations possibles (futur)

- Parallélisation des étapes indépendantes
- Cache des résultats (ne re-run que ce qui a changé)
- Mode `--watch` pour re-build automatiquement
- Intégration CI/CD (GitHub Actions)

### Alternatives considérées

1. **Makefile** : Standard mais moins flexible pour le rapport détaillé
2. **tox** : Trop orienté tests, pas assez général
3. **invoke** : Dépendance supplémentaire, pas nécessaire
4. **Script Bash** : Moins portable, plus difficile à maintenir

→ **Script Python standalone choisi** : Équilibre entre simplicité et fonctionnalités

## Estimated Effort

**Medium** (~4-5h)
- Script de base : 1h
- Parsing des outputs : 1.5h
- Calcul des actions prioritaires : 1h
- Rapport Rich formaté : 1h
- Tests et documentation : 30min
