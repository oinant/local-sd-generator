# Improvements Backlog

**Status:** next
**Priority:** varies
**Component:** cli, webui
**Created:** 2025-10-16

## Liste des améliorations à implémenter

### 1. Fix: Path duplication dans `sdgen generate` (mode interactif)

**Priority:** 🔴 **CRITIQUE** (bug bloquant)
**Component:** cli

**Problème:**
Quand on sélectionne un template en mode interactif, le path est dupliqué:
```
File not found: /mnt/d/StableDiffusion/private-new/prompts/hassaku/templates/prompts/hassaku/templates/Hassaku_ActualPortrait.prompt.yaml
                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ DUPLIQUÉ !
```

**Cause:**
- `select_template_interactive()` retourne un Path absolu (`templates[idx]`)
- Ligne 146 dans `_generate()`, on passe ce path absolu au `V2Pipeline.load()`
- Le pipeline traite ce path comme relatif à `configs_dir` → duplication

**Fix:**
Le template retourné par `select_template_interactive()` est **déjà absolu**, donc ne pas le résoudre à nouveau.

**Fichier:** `packages/sd-generator-cli/sd_generator_cli/cli.py:578`

---

### 2. Commande `sdgen config renew-token`

**Priority:** 7
**Component:** cli

**Description:**
Ajouter une commande pour regénérer le `webui_token`.

**Use case:**
```bash
$ sdgen config renew-token
🔑 New WebUI token generated: abc123...xyz789
✓ Token updated in sdgen_config.json

⚠️  WebUI services need to be restarted to use the new token.
   Run: sdgen webui restart
```

**Questions à résoudre:**
- Faut-il auto-restart la WebUI ? (non, juste afficher un warning)
- Syntaxe: `sdgen config renew-token` ou `sdgen token renew` ?
  → **Proposé: `sdgen config renew-token`** (cohérent avec config)

**Implémentation:**
1. Ajouter option `renew_token` à `config_command()`
2. Générer nouveau UUID avec `generate_webui_token()`
3. Mettre à jour `sdgen_config.json`
4. Afficher warning pour restart WebUI

---

### 3. Refactor: Split `commands.py` en modules

**Priority:** 6
**Component:** cli

**Problème:**
`commands.py` devient trop gros (330+ lignes).

**Proposition:**
```
sd_generator_cli/commands/
├── __init__.py         # Exports publics
├── config.py           # config_command
├── services.py         # start/stop/status_command
└── webui.py            # webui_app (subcommands)
```

**Migration:**
1. Créer structure `commands/`
2. Déplacer fonctions dans modules appropriés
3. Mettre à jour imports dans `cli.py`
4. Tests: vérifier que tous les tests passent

---

### 4. Fix: Affichage URL frontend dans `sdgen start`

**Priority:** 5
**Component:** cli

**Problème:**
En mode prod, on affiche l'URL du frontend en mode dev.

**Code actuel** (`commands.py:102`):
```python
if not no_frontend:
    table.add_row("Frontend", f"http://localhost:{frontend_port}")
```

**Fix proposé:**
```python
if not no_frontend:
    if dev_mode:
        table.add_row("Frontend (DEV)", f"http://localhost:{frontend_port}")
    else:
        table.add_row("Frontend (PROD)", f"http://localhost:{backend_port}")
```

**Fichier:** `packages/sd-generator-cli/sd_generator_cli/commands.py:100-102`

---

### 5. Commande `sdgen build`

**Priority:** 6
**Component:** cli, tooling

**Description:**
Commande pour lancer tous les checks qualité + build frontend.

**Use case:**
```bash
$ sdgen build
[1/5] Running linters (flake8)...       ✓
[2/5] Running type checker (mypy)...    ✓
[3/5] Running tests (pytest)...         ✓ (306 passed)
[4/5] Checking coverage...              ✓ (98%)
[5/5] Building frontend...              ✓

✓ Build complete! All checks passed.
```

**Étapes:**
1. Lint: `flake8 packages/sd-generator-cli --max-line-length=120`
2. Type check: `mypy packages/sd-generator-cli/sd_generator_cli --show-error-codes`
3. Tests: `pytest packages/sd-generator-cli/tests/ -v`
4. Coverage: `pytest packages/sd-generator-cli/tests/ --cov --cov-report=term-missing`
5. Frontend build: `cd packages/sd-generator-webui && npm run build`

**Options:**
- `--skip-tests` : Skip tests (faster)
- `--skip-frontend` : Skip frontend build
- `--verbose` : Afficher output complet

**Fichier à créer:** `packages/sd-generator-cli/sd_generator_cli/commands/build.py`

---

### 6. Analyser duplication docs/

**Priority:** 4
**Component:** docs

**Problème:**
Documentation dupliquée entre :
- `/docs/`
- `/packages/sd-generator-cli/docs/` (?)
- `/packages/sd-generator-webui/docs/` (?)

**Action:**
1. Lister tous les fichiers docs
2. Identifier les doublons
3. Déterminer la source de vérité (probablement `/docs/`)
4. Supprimer ou symlink les doublons

**Commande d'analyse:**
```bash
find . -name "*.md" -path "*/docs/*" | sort
```

---

### 7. Améliorer messages d'erreur config

**Priority:** 3
**Component:** cli

**Messages actuels OK, mais pourraient être plus explicites:**

**Exemple 1 - Config file not found:**
```bash
# Actuel
✗ No config file found.
→ Run 'sdgen init' first.

# Amélioré
✗ No config file found in current directory.
→ Expected: ./sdgen_config.json
→ Run 'sdgen init' to create config
→ Or cd to project directory
```

**Exemple 2 - Invalid key:**
```bash
# Actuel
✗ Config key 'foo' does not exist.
→ Valid keys: api_url, configs_dir, output_dir, webui_token

# Amélioré
✗ Unknown config key: 'foo'

Valid keys:
  • api_url      - SD API URL
  • configs_dir  - Templates directory
  • output_dir   - Output directory
  • webui_token  - WebUI auth token

Usage: sdgen config <key> [value]
```

---

### 8. Support `sdgen config --edit`

**Priority:** 3
**Component:** cli

**Description:**
Ouvrir `sdgen_config.json` dans l'éditeur par défaut.

**Use case:**
```bash
$ sdgen config --edit
# Opens sdgen_config.json in $EDITOR (or vim/nano)
```

**Implémentation:**
```python
import os
import subprocess

editor = os.environ.get('EDITOR', 'nano')  # Fallback to nano
subprocess.run([editor, str(config_path)])
```

---

### 9. Validation avancée des valeurs de config

**Priority:** 3
**Component:** cli

**Description:**
Valider les valeurs lors de l'écriture.

**Exemples:**
```bash
# api_url: vérifier format URL
$ sdgen config api_url "not a url"
✗ Invalid URL format. Expected: http://host:port

# configs_dir: vérifier que le path existe
$ sdgen config configs_dir /nonexistent
⚠️  Warning: Directory does not exist
   Create it with: mkdir -p /nonexistent
   Continue anyway? [y/N]

# webui_token: vérifier longueur minimale
$ sdgen config webui_token "abc"
✗ Token too short. Minimum length: 16 characters
→ Generate secure token with: sdgen config renew-token
```

---

### 10. Shell completion pour `sdgen`

**Priority:** 2
**Component:** cli

**Description:**
Autocomplétion bash/zsh pour les commandes et clés de config.

**Exemples:**
```bash
$ sdgen co<TAB>
config

$ sdgen config <TAB>
api_url  configs_dir  output_dir  webui_token  list  renew-token
```

**Implémentation:**
Typer supporte nativement la génération de completion scripts:
```bash
sdgen --install-completion
sdgen --show-completion
```

---

## Priorisation

**🔴 Critique (faire maintenant):**
1. Fix path duplication dans generate

**🟠 Important (prochain sprint):**
2. Commande renew-token
3. Refactor commands.py
4. Fix affichage URL frontend
5. Commande build

**🟡 Nice-to-have (futur):**
6. Analyser duplication docs
7. Améliorer messages d'erreur
8. Support --edit
9. Validation avancée
10. Shell completion

---

## Notes

- Chaque item devrait avoir sa propre spec détaillée avant implémentation
- Tests unitaires obligatoires pour chaque feature
- Mypy strict mode doit passer
- Documentation utilisateur pour chaque nouvelle commande
