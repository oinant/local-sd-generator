# 🚀 Continuation : Roadmap Migration to GitHub Issues + Agent PO

**Date:** 2025-10-24
**Status:** En cours - Setup MCP GitHub
**Context:** Mise en place d'une équipe d'agents (PO, Architecte, Doc Manager) avec migration de la roadmap vers GitHub Issues

---

## 📍 Où on en est

### ✅ Complété

1. **Plan agents créé** : `.claude/agents-setup.md`
   - Workflow complet des agents (PO, Arch, Doc Manager, Reviewer)
   - Setup progressif sur 3 semaines
   - KPIs et success metrics

2. **Audit roadmap actuel**
   - Total : 56 fichiers MD
   - Done : 27 items
   - Next : 7 items (prioritaires)
   - Future : 9 items (backlog)
   - Archive : ~13 items

3. **Stratégie de migration décidée**
   - Migration manuelle assistée (Option A)
   - Contrôle qualité sur chaque issue
   - Cleanup et priorisation CPO

### 🔄 En cours

**Setup GitHub MCP server (LOCAL)**
- Installation : `npm install -g @modelcontextprotocol/server-github`
- Configuration : `~/.config/claude-code/config.json`
- Token GitHub requis avec permissions `repo`

### 📋 Prochaines étapes

1. **[USER ACTION] Setup MCP GitHub**
   ```bash
   # 1. Créer token GitHub
   https://github.com/settings/tokens/new
   Permissions : ✅ repo (full control)

   # 2. Installer MCP
   npm install -g @modelcontextprotocol/server-github

   # 3. Configurer Claude Code
   ~/.config/claude-code/config.json :
   {
     "mcpServers": {
       "github": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-github"],
         "env": {
           "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_YOUR_TOKEN_HERE"
         }
       }
     }
   }

   # 4. Redémarrer Claude Code
   ```

2. **[CLAUDE] Tester MCP GitHub**
   - Vérifier connexion
   - Lister repos
   - Test création issue (sur repo test si possible)

3. **[CLAUDE + USER] Setup GitHub**
   - Créer labels (feature, bug, P1-P5, cli/api/templating/etc.)
   - Créer milestones (Sprint X, Backlog)
   - Définir templates d'issues

4. **[CLAUDE + USER] Migrer roadmap/next/ (7 items)**
   - Pour chaque item :
     - Claude lit le MD
     - Propose titre, labels, priorité, contenu
     - USER valide/ajuste
     - Claude crée l'issue via MCP
     - Ajoute lien vers issue dans le MD

5. **[CLAUDE + USER] Migrer roadmap/future/ (9 items)**
   - Même process
   - Possibilité de consolider certains items

6. **[CLAUDE] Auto-migrer roadmap/done/ (27 items)**
   - Création automatique (moins critique)
   - Issues fermées avec date de complétion

7. **[CLAUDE] Créer Agent PO**
   - Slash command `/po` dans `.claude/commands/`
   - Intégré avec GitHub Issues
   - Capable de créer/mettre à jour issues

8. **[USER + CLAUDE] Tester Agent PO**
   - Test feature request
   - Test bug report
   - Test sprint planning

---

## 📊 Items à migrer (détail)

### roadmap/next/ (7 items - prioritaires)

1. `controlnet-integration.md` - Feature ControlNet
2. `feature-numeric-slider-placeholders.md` - Numeric sliders
3. `fix-v2-failing-tests.md` - Bug tests V2
4. `improvements-backlog.md` - Divers (à consolider ?)
5. `model-tagging-in-metadata.md` - Metadata tagging
6. `themable-templates.md` - Themable templates
7. `variation-names-in-filenames.md` - Variation names

### roadmap/future/ (9 items - backlog)

1. `advanced-features-brainstorm.md` - Ideas (à trier ?)
2. `config-file-launch.md` - Config launch
3. `interactive-metadata.md` - Interactive metadata
4. `metadata-enrichment-system.md` - Metadata system
5. `rebuild_tool.md` - Rebuild tool
6. `sqlite-database.md` - SQLite DB
7. `webapp-architecture-thumbnails.md` - WebUI thumbnails
8. `webapp-architecture.md` - WebUI archi
9. `wizard-prompt-creation.md` - Wizard prompt

---

## 🎯 GitHub Labels à créer

### Type
- `feature` (vert) - Nouvelle fonctionnalité
- `bug` (rouge) - Bug à corriger
- `refactor` (bleu) - Refactoring technique
- `docs` (gris) - Documentation
- `chore` (gris clair) - Maintenance

### Priority
- `P1-critical` (rouge foncé) - Prod broken, bloquant
- `P2-high` (orange) - Important, prochain sprint
- `P3-medium` (jaune) - Priorité moyenne
- `P4-low` (vert clair) - Nice-to-have
- `P5-backlog` (gris) - Futur lointain

### Component
- `cli` (violet) - CLI commands
- `api` (bleu) - API client
- `templating` (cyan) - Template system
- `execution` (vert) - Manifest/executor
- `tooling` (marron) - Dev tools
- `webapp` (rose) - WebUI (futur)

### Status (optionnel, dépend de ton workflow GitHub)
- `next` (jaune) - Prochain sprint
- `wip` (orange) - En développement
- `blocked` (rouge) - Bloqué par dépendance
- `needs-discussion` (violet) - Besoin clarification

---

## 🤖 Agent PO (post-migration)

### Capabilities

1. **Feature requests**
   - Analyse fonctionnelle
   - Use cases, acceptance criteria
   - Création spec MD + GitHub Issue
   - Priorisation (P1-P5)

2. **Bug reports**
   - Analyse d'impact (sévérité, fréquence)
   - Steps to reproduce
   - Création GitHub Issue
   - Priorisation urgente si critique

3. **Sprint planning**
   - Audit roadmap vs GitHub Issues
   - Matrice valeur × effort
   - Proposition sprint plan
   - Mouvements roadmap (future→next→wip)

4. **Roadmap audit**
   - Vérification sync MD ↔ Issues
   - Détection incohérences
   - Health score
   - Actions recommandées

### Usage

```bash
/po feature: [description]
/po bug: [description]
/po plan sprint: [durée]
/po audit
```

### Output

- Spec fonctionnelle/technique
- GitHub Issue créée/mise à jour
- Questions pour CPO/CTO
- Recommandation priorité + justification

---

## 💡 Décisions clés

### Pourquoi MCP GitHub LOCAL ?
- Sécurité (token reste local)
- Simplicité (pas de serveur remote)
- Performance (pas de latence réseau)
- Architecture : Claude Code → MCP local → GitHub API

### Pourquoi migration manuelle assistée ?
- Seulement 16 items (next + future)
- Opportunité cleanup/priorisation
- Contrôle qualité (toi = CPO)
- Done items peuvent être auto-migrés

### Système hybride MD + Issues
- **Specs détaillées** → `docs/roadmap/*.md` (versionnées)
- **Tracking/workflow** → GitHub Issues (board, notifs)
- **Sync bidirectionnel** → Agent PO maintient cohérence

**Avantages :**
- Best of both worlds
- MD files = documentation technique riche
- Issues = workflow management intégré

---

## 🔧 Commandes utiles

### Audit roadmap
```bash
# Compter items
find docs/roadmap/{next,future} -name "*.md" | wc -l

# Lister next items
ls -1 docs/roadmap/next/

# Lister future items
ls -1 docs/roadmap/future/
```

### Tester MCP GitHub (après setup)
```bash
# Dans Claude Code, vérifier que ces fonctions MCP sont dispo :
# - mcp__github__create_issue
# - mcp__github__list_issues
# - mcp__github__update_issue
# - mcp__github__create_label
```

---

## 📝 Notes importantes

### Permissions token GitHub
- ✅ `repo` (full control) - Obligatoire
- ✅ `workflow` (si GitHub Actions) - Optionnel
- ✅ `read:org` (si organisation) - Optionnel

### Config file location
- Linux/WSL : `~/.config/claude-code/config.json`
- Alternative : `~/.claude-code/config.json`
- Vérifier avec : `ls -la ~/.config/claude-code/`

### Redémarrage requis
Après modification config, **toujours redémarrer Claude Code** pour charger le MCP.

---

## 🎬 Reprendre ici

**Commande pour continuer :**
```
"On reprend la migration roadmap → GitHub Issues.
J'ai setup le MCP GitHub, on peut tester ?"
```

**Ou si MCP pas encore setup :**
```
"J'ai besoin d'aide pour configurer le MCP GitHub.
Où se trouve le fichier config exactement ?"
```

**Claude vérifiera :**
1. MCP GitHub fonctionnel (test connexion)
2. Accès au repo (list issues)
3. Si OK → on passe à la migration des 7 items de `next/`

---

**Goal:** Agent PO opérationnel avec roadmap migrée sur GitHub Issues d'ici fin de semaine. 🚀
