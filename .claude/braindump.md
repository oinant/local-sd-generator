# Braindump

**Purpose:** Ongoing ideas and notes captured during Claude Code sessions. Survives context compaction.

**Status Legend:**
- 🆕 **NEW** - Freshly braindumped, not yet analyzed by Agent PO
- 🔍 **ANALYZING** - Agent PO is processing
- 📋 **TRACKED** - GitHub issue created (link provided)
- ✅ **DONE** - Implemented and closed
- 🚫 **REJECTED** - Decided not to pursue

---

## 🆕 Pending Analysis

_Items braindumped but not yet processed by Agent PO_

- **[Feature]** Tag the model used for generation in file metadata (call the api? use an headless browser?)
- **[Feature]** CLI: Interactive selector for placeholders
- **[Feature]** WebUI: Flag failed generations (image by image)
  - Can help understand prompt failures with analysis
  - Requires: SQLite database?
- **[Feature]** WebUI: Filter/sort images by variation options from manifest
- **[Feature]** Export Pydantic schemas to JSON Schema format
  - Command: `sdgen schema export --format json-schema`
  - Use cases: VS Code autocomplete, documentation auto-gen, cross-language validation
  - Export all 5 schemas (template, prompt, chunk, variations, theme_config)

<!-- Add new items here during braindump sessions -->

---

## 🔍 Being Analyzed

_Items currently being structured by Agent PO_

<!-- Agent PO moves items here during analysis -->

---

## 📋 Tracked on GitHub

_Items with GitHub issues created (ready for implementation)_

### 2025-10-29 Session - Themable Templates Improvements

- **[Enhancement]** list-themes: Filter files by template placeholders → [#46](https://github.com/oinant/local-sd-generator/issues/46)
  - Priority: P4 (High), Effort: Small (~2h)
  - Status: `next`
  - Show only files relevant to template placeholders

- **[Enhancement]** list-themes: Group style variants in tree view → [#47](https://github.com/oinant/local-sd-generator/issues/47)
  - Priority: P5 (High/Medium), Effort: Medium (~4h)
  - Status: `next`
  - Display style variants in hierarchical tree structure

### 2025-10-30 Session - Schema Validation with Pydantic

- **[Feature]** Explicit YAML Schema Validation with Pydantic → [#58](https://github.com/oinant/local-sd-generator/issues/58)
  - Priority: P2 (High), Effort: Large (~12-17 days)
  - Status: `next`
  - Validation explicite des 5 types de fichiers YAML
  - Commande `sdgen validate` avec scan récursif
  - Migration automatique avec `sdgen migrate`
  - **Architecture docs:** `/tmp/schema_validation_*.md` (4 docs)
    - `schema_validation_architecture.md` - Document principal (1500+ lignes)
    - `schema_validation_summary.md` - Résumé exécutif (600 lignes)
    - `schema_validation_checklist.md` - 150+ items à cocher
    - `schema_validation_impact_matrix.md` - Matrice d'impact complète

### 2025-10-29 Session - Braindump Processing (Issues #48-#55)

- **[Feature]** Compact theme selector in list-themes → [#48](https://github.com/oinant/local-sd-generator/issues/48)
  - Priority: P4 (High), Effort: Small (~30min)
  - Status: `next`
  - Add --compact flag to show one-line comma-separated theme list

- **[Feature]** Tag-based theme system → [#49](https://github.com/oinant/local-sd-generator/issues/49)
  - Priority: P4 (High), Effort: Medium (~2-3h)
  - Status: `next`
  - **Decision:** Tags go in theme.yaml
  - Filter themes by tags, period, setting, mood

- **[Feature]** sdgen create-theme command → [#50](https://github.com/oinant/local-sd-generator/issues/50)
  - Priority: P5 (High), Effort: Small (~1-2h)
  - Status: `next`
  - Scaffold new theme with all 9 files

- **[Feature]** Batch multi-run scheduler (CLI-based) → [#51](https://github.com/oinant/local-sd-generator/issues/51)
  - Priority: P6 (Medium), Effort: Large (~4-6h)
  - Status: `next`
  - **Decision:** CLI-first (no config file)
  - Run multiple themes/templates in single command

- **[Feature]** Multi-theme generation in single run → [#52](https://github.com/oinant/local-sd-generator/issues/52)
  - Priority: P6 (Medium), Effort: Large (~5-7h)
  - Status: `next`
  - Mix multiple themes in single session with distribution control

- **[Feature]** Extend existing session with more variants → [#53](https://github.com/oinant/local-sd-generator/issues/53)
  - Priority: P6 (Medium), Effort: Medium (~3-4h)
  - Status: `next`
  - Add --extend flag to continue generating in existing session

- **[Feature]** Include variation names in output filenames → [#54](https://github.com/oinant/local-sd-generator/issues/54)
  - Priority: P7 (Medium), Effort: Small (~1-2h)
  - Status: `next`
  - Format: 001_streetwear_punk-mohawk.png

- **[Docs]** Manifest format audit for image tagging → [#55](https://github.com/oinant/local-sd-generator/issues/55)
  - Priority: P7 (Medium), Effort: Small (~1-2h)
  - Status: `next`
  - **Context:** Understand existing manifest to exploit for tagging
  - Research what's available for image organization

---

## ✅ Done

- ~~CLI: Add scheduler in parameters~~ → Completed
- ~~CLI: Refacto UX with Typer~~ → Completed
- ~~Build tool (linting + tests + coverage + type check + frontend)~~ → Completed via `tools/build.py`

---

## 🚫 Deferred / Rejected

_Items we decided not to pursue (with reason)_

<!-- Add rejected items here with brief explanation -->

---

## 💭 Unstructured Notes

_Rough ideas needing more thought before analysis_

- **[Bug?]** Token renewal (doit être effectif quasi immédiatement dans la web ui, on doit la restart?)
- **[Refactor]** Split commands.py (trop gros, devrait être modulaire)
- **[Bug]** Display issue in `sdgen start` (en prod, on affiche l'url du front en dev-mode - should show backend URL)

---

## 📝 Process

**How to use this file:**

1. **During conversation** - Claude accumulates ideas in "🆕 Pending Analysis"
2. **User triggers PO** - Items move to "🔍 Being Analyzed"
3. **PO creates issues** - Items move to "📋 Tracked on GitHub" with issue links
4. **Implementation done** - Items move to "✅ Done"
5. **Context compaction** - This file persists, ensuring nothing is lost

**Commands:**
- Claude should update this file automatically during braindump sessions
- User can manually add items anytime
- Agent PO reads from "🆕 Pending" and updates statuses
