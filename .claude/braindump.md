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
- **[Feature]** Use variation names & variant keys in filename: `{Session_name}_index_{variationName_variantKey}`
- **[Feature]** CLI: Interactive selector for placeholders
- **[Feature]** CLI: Extend existing session (resume generation with same config)
  - Context: After launching 5-10 test images, ability to continue on same session
  - Metadata contains variations + already-used combinations
- **[Feature]** WebUI: Flag failed generations (image by image)
  - Can help understand prompt failures with analysis
  - Requires: SQLite database?
- **[Feature]** WebUI: Filter/sort images by variation options from manifest
- **[Chore]** CORE: Upgrade manifest to v4.0

<!-- Add new items here during braindump sessions -->

---

## 🔍 Being Analyzed

_Items currently being structured by Agent PO_

<!-- Agent PO moves items here during analysis -->

---

## 📋 Tracked on GitHub

_Items with GitHub issues created (ready for implementation)_

<!-- Agent PO will add issue links here after creation -->

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
