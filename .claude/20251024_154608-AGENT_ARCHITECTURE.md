# Agent Architecture

**Date:** 2025-10-24

## 🏗️ Architecture Overview

Le projet utilise une **architecture agent + slash command** pour permettre à la fois le travail en background et l'invocation explicite.

```
┌─────────────────────────────────────────────────────────┐
│                     User                                │
│  (braindumpe naturellement ou utilise /po)              │
└──────────────┬──────────────────────┬───────────────────┘
               │                      │
               │ naturel              │ explicite
               ▼                      ▼
┌──────────────────────────┐  ┌─────────────────────────┐
│   Main Claude            │  │  Slash Command /po      │
│   (conversation flow)    │  │  (.claude/commands/)    │
│                          │  │                         │
│  - Détecte braindump     │  │  - Relay vers agent     │
│  - Accumule dans         │◄─┤  - Return response      │
│    braindump.md          │  │                         │
│  - Lance agent PO        │  │                         │
│    en background         │  │                         │
└──────────────┬───────────┘  └─────────────────────────┘
               │
               │ Task() call
               ▼
┌──────────────────────────────────────────────────────┐
│           PO Agent (Background)                      │
│           (.claude/agents/po.md)                     │
│                                                      │
│  1. Listen to conversation transcripts              │
│  2. Detect braindump patterns                       │
│  3. Accumulate in .claude/braindump.md              │
│  4. Structure on demand                             │
│  5. Create GitHub issues via gh CLI                 │
└──────────────┬───────────────────────────────────────┘
               │
               │ writes to
               ▼
┌──────────────────────────────────────────────────────┐
│        .claude/braindump.md                          │
│        (Persistence Layer)                           │
│                                                      │
│  🆕 Pending → 🔍 Analyzing → 📋 Tracked → ✅ Done   │
│                                                      │
│  Survit au compactage de contexte                   │
└──────────────────────────────────────────────────────┘
```

## 📁 File Structure

```
.claude/
├── agents/
│   ├── po.md                    # Agent PO (background mode)
│   └── pre-commit-code-reviewer.md  # Code reviewer agent
├── commands/
│   └── po.md                    # Slash command /po (wrapper)
├── braindump.md                 # Persistence layer (survie contexte)
├── agents-setup.md              # Specs des agents (vision globale)
└── PO_AGENT_SETUP.md            # Setup PO (documentation)
```

## 🔄 Workflows

### Workflow 1: Braindump Naturel (Background)

```
1. User: "Ah tiens, faudrait ajouter un cache"
   ↓
2. Main Claude détecte braindump
   → Écrit dans .claude/braindump.md (🆕 Pending)
   → "Noté ! Autre chose ?"
   ↓
3. User: "Ouais et un bug avec les thumbnails"
   ↓
4. Main Claude accumule
   → Écrit dans braindump.md
   → "Ok. Je structure ça avec l'agent PO ?"
   ↓
5. User: "Go"
   ↓
6. Main Claude lance PO Agent via Task()
   → Agent PO tourne en background
   → Main Claude peut continuer à répondre pendant ce temps
   ↓
7. Agent PO termine
   → Parse, priorise, catégorise
   → Propose GitHub issues
   → Update braindump.md (🆕 → 🔍)
   ↓
8. Main Claude relaie au user
   ↓
9. User: "Ok crée les issues"
   ↓
10. Agent PO crée via gh CLI
    → Update braindump.md (🔍 → 📋 Tracked)
```

### Workflow 2: Slash Command Explicite

```
1. User: "/po feature: cache système"
   ↓
2. Slash command /po activé
   → Relay vers Agent PO
   ↓
3. Agent PO traite
   → Parse, analyse, propose
   → Écrit dans braindump.md si applicable
   ↓
4. Slash command retourne la réponse
   ↓
5. User valide
   ↓
6. Agent PO crée GitHub issue
```

## 🎯 Avantages de cette architecture

### 1. Zéro friction cognitive
- User braindumpe naturellement
- Pas besoin de se souvenir de `/po`
- Claude gère la détection automatiquement

### 2. Background processing
- Agent PO tourne en parallèle
- User peut continuer à travailler
- Pas de blocage du flow de conversation

### 3. Persistence garantie
- `.claude/braindump.md` survit au compactage
- Rien ne se perd entre sessions
- Continuité du travail

### 4. Flexibilité
- Mode automatique OU explicite
- User choisit son style de travail
- Pas de friction

### 5. Scalabilité
- Architecture réutilisable pour autres agents
- Agent Architecte, Doc Manager, etc.
- Communication inter-agents possible

## 🔧 Technical Details

### Agent Invocation

**Via Task tool:**
```python
Task(
    subagent_type="general-purpose",
    description="Analyze braindump and structure ideas",
    prompt="Read .claude/agents/po.md and execute as PO agent..."
)
```

**Via Slash Command:**
```
/po braindump: [ideas]
```

### Persistence Layer

**braindump.md structure:**
```markdown
## 🆕 Pending Analysis
- Item 1
- Item 2

## 🔍 Being Analyzed
- Item 3 (Agent PO processing)

## 📋 Tracked on GitHub
- Item 4 → [#123](link)

## ✅ Done
- Item 5 → Completed

## 🚫 Deferred / Rejected
- Item 6 (reason)
```

### State Transitions

```
NEW (🆕)
  ↓ User triggers PO / Auto-detect
ANALYZING (🔍)
  ↓ Analysis complete
TRACKED (📋)
  ↓ Implementation done
DONE (✅)
```

OR

```
NEW (🆕)
  ↓ Decided not to pursue
REJECTED (🚫)
```

## 📝 Implementation Notes

### For Main Claude

**Detection patterns:**
```python
braindump_triggers = [
    "il faudrait",
    "faudrait que",
    "on devrait",
    "tiens,",
    "bug:",
    "idée:",
    "je me demande"
]
```

**Accumulation:**
- Always write to `.claude/braindump.md`
- Section: "🆕 Pending Analysis"
- Format: `- **[Type]** Description`

**Agent launch:**
```python
# When user confirms
Task(
    description="Structure braindump ideas",
    prompt="Act as PO Agent from .claude/agents/po.md..."
)
```

### For PO Agent

**Input sources:**
1. Conversation transcript (from Main Claude)
2. `.claude/braindump.md` (🆕 Pending section)
3. Explicit `/po` commands

**Output:**
1. Structured analysis (priority, effort, value)
2. Updated `.claude/braindump.md` (state transitions)
3. GitHub issues (via `gh` CLI)
4. Report back to Main Claude

## 🚀 Future Extensions

### Week 2: Agent Architecte
```
.claude/agents/arch.md
.claude/commands/arch.md
```

### Week 3: Doc Manager
```
.claude/agents/doc-manager.md
.claude/commands/sync-doc.md
```

### Inter-agent Communication
```
Agent PO → Agent Arch: "Need technical design for feature X"
Agent Arch → Agent PO: "Design ready, estimate: Large effort"
```

---

**Status:** ✅ Implemented (2025-10-24)
**Next:** Test with real braindump session
