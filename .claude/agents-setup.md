# 🤖 Agents Setup & Workflow

## 📋 Vue d'ensemble

Ce projet utilise des **agents autonomes** pour paralléliser les tâches de réflexion, analyse et documentation pendant le développement.

**Philosophie:** Les agents travaillent en arrière-plan pendant que tu continues à développer, maximisant la productivité par parallélisation cognitive.

## 🎯 Agents disponibles

| Agent | Commande | Rôle | Quand utiliser |
|-------|----------|------|----------------|
| **🎭 Product Owner** | `/po` | Analyse features/bugs, specs fonctionnelles, roadmap | Nouvelle idée, bug report, planning |
| **🏗️ Architecte** | `/arch` | Design technique, patterns, trade-offs | Avant feature majeure, refactoring |
| **📚 Doc Manager** | `/sync-doc` | Sync code ↔ doc, audit cohérence | Après feature, weekly audit |
| **🔍 Code Reviewer** | `/review` | Code review approfondie | Avant commit important |

## 📅 Setup progressif (3 semaines)

### ✅ Semaine 1 : Agent PO + GitHub Issues
- [x] Créer agent PO (`/po`)
- [ ] Migrer roadmap vers GitHub Issues
- [ ] Setup MCP GitHub server
- [ ] Tester workflow PO → GitHub Issues
- [ ] Ajuster process selon feedback

### 🔜 Semaine 2 : Agent Architecte
- [ ] Créer agent Architecte (`/arch`)
- [ ] Tester PO + Arch en parallèle sur vraie feature
- [ ] Documenter collaboration PO ↔ Arch
- [ ] Optimiser prompts agents

### 🔮 Semaine 3 : Doc Manager + Automation
- [ ] Créer agent Doc Manager (`/sync-doc`)
- [ ] Auto-trigger après features (optionnel)
- [ ] Weekly doc audit (scheduled)
- [ ] Dashboard de suivi agents

## 🎭 Agent PO : Product Owner

### Responsabilités

1. **Analyse de features**
   - Use cases, user stories
   - Acceptance criteria
   - Edge cases et questions
   - Estimation de valeur business

2. **Gestion de bugs**
   - Analyse d'impact
   - Priorité (P1-P5)
   - Steps to reproduce
   - Régression check

3. **Roadmap management**
   - Priorisation (valeur × effort)
   - Mouvements entre future/next/wip/done
   - Synchronisation GitHub Issues
   - Planning sprints

### Usage

```bash
# Nouvelle feature
/po feature: système de cache pour prompts

# Bug report
/po bug: les seeds progressives ne s'incrémentent pas correctement

# Planning sprint
/po plan sprint: prioriser roadmap pour les 2 prochaines semaines

# Audit roadmap
/po audit: vérifier cohérence roadmap vs GitHub Issues
```

### Output de l'agent PO

L'agent génère :
1. **Spec fonctionnelle** dans `docs/roadmap/{future|next}/feature-name.md`
2. **GitHub Issue** (via MCP) avec labels appropriés
3. **Questions pour toi** (clarifications nécessaires)
4. **Recommandation de priorité** (P1-P5)

## 🔗 GitHub Issues Integration

### Pourquoi migrer ?

| Roadmap MD files | GitHub Issues |
|------------------|---------------|
| ✅ Simple, versionné | ✅ Workflow intégré |
| ✅ Lecture facile | ✅ Assignation, milestones |
| ❌ Pas de tracking | ✅ Labels, projects |
| ❌ Pas de notifications | ✅ Mentions, notifications |
| ❌ Statut manuel | ✅ Statut automatique |

**Solution hybride** (meilleur des deux mondes) :
- **Specs détaillées** → `docs/roadmap/` (versionnées, détail technique)
- **Tracking/workflow** → GitHub Issues (board, assignation, notifs)
- **Sync bidirectionnel** → Agent PO maintient cohérence

### Labels GitHub proposés

```
Type:
- feature (vert)
- bug (rouge)
- refactor (bleu)
- docs (gris)

Priority:
- P1-critical (rouge foncé)
- P2-high (orange)
- P3-medium (jaune)
- P4-low (vert clair)
- P5-backlog (gris)

Component:
- cli (violet)
- api (bleu)
- frontend (cyan)
- tooling (marron)

Status:
- future (gris clair)
- next (jaune)
- wip (orange)
- done (vert)
- blocked (rouge)
```

### Workflow PO → GitHub

```
1. Toi: "/po feature: X"

2. Agent PO (background):
   - Analyse la feature
   - Génère spec dans docs/roadmap/next/X.md
   - Crée GitHub Issue via MCP:
     * Titre : "[Feature] X"
     * Body : Lien vers spec + résumé
     * Labels : feature, P3-medium, cli
     * Milestone : Sprint 12
   - Pose questions de clarification

3. Toi: Reviews et réponds aux questions

4. Agent PO (finalisation):
   - Met à jour spec avec tes réponses
   - Met à jour GitHub Issue
   - Notifie : "✅ Feature X ready for dev"
```

### MCP GitHub Server Setup

```bash
# 1. Installer le MCP server (si pas déjà fait)
npm install -g @modelcontextprotocol/server-github

# 2. Configurer dans Claude Desktop
# (ajouter dans claude_desktop_config.json)
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}

# 3. Permissions requises pour le token:
# - repo (full access)
# - read:org (si organisation)
```

**Note:** Si tu utilises Claude Code CLI, vérifier la config MCP dans `~/.config/claude-code/`.

## 🏗️ Agent Architecte (Semaine 2)

### Responsabilités

1. **Design technique**
   - Architecture components
   - Patterns et best practices
   - Trade-offs et alternatives
   - Estimation complexité

2. **Analyse d'existant**
   - Détection overlap avec code actuel
   - Réutilisation de patterns (ex: ADetailer)
   - Migration paths si refactoring

3. **Documentation technique**
   - Architecture diagrams
   - API contracts
   - Integration points

### Usage

```bash
# Design nouvelle feature
/arch design: système de cache pour prompts

# Refactoring
/arch refactor: simplifier le templating resolver

# Review archi globale
/arch audit: analyser cohérence architecture CLI
```

## 📚 Agent Doc Manager (Semaine 3)

### Responsabilités

1. **Sync code ↔ doc**
   - Détecte changements dans code
   - Identifie doc obsolète
   - Génère patches de doc

2. **Audit cohérence**
   - Vérifie que examples marchent
   - Check liens internes
   - Valide structure doc

3. **Auto-update**
   - Met à jour après features
   - Génère changelogs
   - Update API references

### Usage

```bash
# Sync après feature
/sync-doc feature: ControlNet upload

# Audit complet
/sync-doc audit: vérifier cohérence complète docs/

# Auto-update
/sync-doc auto: mettre à jour toute doc obsolète
```

## 🔄 Workflows typiques

### Workflow 1 : Nouvelle feature (idée → prod)

```
1. Toi: "Idée : système de cache pour prompts"

2. Moi (Claude):
   → Lance /po en background
   → Lance /arch en background
   → "Ok, continuons à dev pendant que les agents bossent"

3. [15 min plus tard] Agents terminent:
   → PO : Spec fonctionnelle + GitHub Issue créée
   → Arch : Design technique + trade-offs

4. Toi: Reviews et valides (ou demandes ajustements)

5. Moi: Implémente basé sur les specs

6. Après implémentation:
   → Lance /review (pre-commit)
   → Lance /sync-doc (update doc)

7. Commit & push
```

### Workflow 2 : Bug report

```
1. Toi: "/po bug: seeds progressives cassées"

2. Agent PO:
   → Analyse l'impact
   → Cherche dans code les causes possibles
   → Crée GitHub Issue (bug, P2-high)
   → Propose fix approach

3. Moi: Fixe le bug

4. Agent PO (auto-trigger):
   → Ferme GitHub Issue
   → Update roadmap si nécessaire
```

### Workflow 3 : Planning sprint

```
1. Toi: "/po plan sprint: 2 semaines"

2. Agent PO:
   → Analyse toutes les issues GitHub
   → Compare avec roadmap MD
   → Évalue effort × valeur
   → Propose priorisation

3. Toi (CPO): Valides ou ajustes

4. Agent PO:
   → Met à jour milestones GitHub
   → Move items dans roadmap
   → Génère sprint plan
```

## 📊 Dashboard de suivi (Futur)

Idée pour tracking agents :

```markdown
# Agent Activity Dashboard

## Cette semaine
- 🎭 PO : 5 features analysées, 3 bugs triés, 1 sprint planifié
- 🏗️ Arch : 2 designs produits, 1 refactor proposé
- 📚 Doc : 12 fichiers sync, 0 incohérences détectées
- 🔍 Review : 3 reviews, 8 actions P1-P2 fixées

## Metrics
- Time saved : ~6h (estimation)
- Issues created : 8
- Docs updated : 12 files
- Code reviews : 3 commits
```

## ⚙️ Configuration agents

Les prompts des agents sont dans `.claude/commands/` et peuvent être customisés.

**Paramètres configurables:**
- Niveau de détail (concis vs exhaustif)
- Style de communication (questions vs propositions)
- Auto-trigger ou manuel
- Intégrations (GitHub, Slack, etc.)

## 🎯 Success Metrics

**KPIs à suivre:**
1. **Time to spec** : Temps entre idée et spec complète
2. **Doc coverage** : % de code documenté
3. **Review thoroughness** : Nombre d'issues détectées pre-commit
4. **Roadmap health** : Sync rate avec GitHub Issues

**Target:**
- Time to spec : < 15 min (vs 1-2h manual)
- Doc coverage : > 90%
- Pre-commit issues : catch 80% avant commit
- Roadmap sync : 100% (automated)

## 📝 Notes

- Les agents tournent en **background** (non-bloquant)
- Tu peux interrompre ou modifier à tout moment
- Les specs générées sont des **propositions** (tu valides toujours)
- Le workflow s'adapte à ton style (plus ou moins automatique)

---

**Next steps:** Voir `/po` command documentation pour démarrer !
