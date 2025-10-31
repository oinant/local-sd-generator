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
- **[Feature]** CLIP-based Prompt Validation & Quality Analysis
  - **Context:** 600+ sessions, many incomplete/failed runs, 38k+ images to analyze
  - **Hardware:** RTX 5070 Ti (16GB VRAM) - See `.claude/machine_specs.md`
  - **Goal:** Auto-classify image quality + validate prompt adherence
  - **Use Cases:**
    1. **Prompt ↔ Image Validation**
       - Read variations from manifest.json
       - Use CLIP/FastVLM to verify: "Does this image contain {variation_value}?"
       - Score each variation (0-100% confidence)
       - Example: HairCut=punk_mohawk: 92% ✓, HairColor=neon_blue: 15% ✗
    2. **Quality Control & Cleanup**
       - Flag images where <70% variations match
       - Auto-tag: "success" (>80%), "partial" (50-80%), "failed" (<50%)
       - Batch delete low-quality runs
    3. **Statistical Analysis**
       - Per-variation success rate: "punk_mohawk works 85% of time"
       - Identify problematic prompts/variations
       - A/B test prompt formulations
    4. **Session Classification**
       - Mark session as "complete" if avg match >75%
       - Flag sessions to review/delete
  - **Tech Stack - Hybrid Cascade Strategy:**
    - **Tier 1:** FastVLM (Apple) or CLIP (OpenAI) - Performant but may refuse NSFW
    - **Tier 2 Fallback:** NSFW-CLIP or OpenCLIP - Permissive for adult content
    - **Tier 2 Hybrid:** Zone cropping (face/hair) + Tier 1 analysis on safe zones
    - **Decision logic:** Try Tier 1 → If refused → Fallback or Crop strategy
    - **Performance:** Batch size 128 images, ~5-10 img/sec, 38k images in 1-2h
  - **NSFW Content Handling:**
    - **Problem:** Commercial models (OpenAI CLIP, Apple FastVLM) refuse NSFW
    - **Solution 1:** NSFW-CLIP or OpenCLIP (no censorship filters)
    - **Solution 2:** Crop safe zones (face, hair) → Analyze with best model
    - **Solution 3:** Custom classifier trained on user's data (see below)
  - **Output:**
    - Per-image: variation_scores = {variation: confidence}, method_used = "tier1_full" | "tier2_fallback" | "tier2_hybrid"
    - Per-session: avg_match_score, flagged_images_count
    - Dashboard: "Top 10 failing variations to fix"
  - **Benefits:**
    - Clean up 600 sessions intelligently
    - Identify which prompts/variations work best
    - Data-driven prompt engineering
    - Auto-QC for future generations
- **[Feature/Research]** Custom Classifier Training & Self-Improving Generator
  - **Context:** RTX 5070 Ti enables professional ML training workflows
  - **Hardware Capabilities:** See `.claude/machine_specs.md`
    - LoRA training: 1-3h (batch size 8-16)
    - Classifier training: 30-60 min (transfer learning)
    - CLIP fine-tuning: 2-3h
    - Batch inference: 128 images/batch, ~5 min for 38k images
  - **Phase 1: Custom Variation Classifier (Immediate)**
    - **Goal:** Train lightweight classifier for user's specific variations
    - **Approach:** Transfer learning (MobileNetV3 or EfficientNet)
    - **Data:** 5000-10000 images from existing sessions (filtered by CLIP)
    - **Training Time:** 30-60 min on RTX 5070 Ti
    - **Benefit:** +5-15% accuracy vs generic CLIP, understands "punk_mohawk" perfectly
    - **Use Case:** Replace/augment CLIP for variation validation
  - **Phase 2: Self-Improving Generator Pipeline (Advanced)**
    - **Concept:** Closed-loop system that improves checkpoint quality over time
    - **Workflow:**
      1. Generate batch (1000-2000 images) with current checkpoint
      2. CLIP/Classifier validation → Filter top 10-20% (best quality)
      3. Auto-label from manifest.json variations
      4. Train LoRA on filtered best images (2-4h)
      5. Merge LoRA into checkpoint or stack
      6. Benchmark quality improvement
      7. Iterate → Each cycle improves checkpoint
    - **Result:** Checkpoint that understands user's variations natively
  - **Phase 3: Variation-Specific LoRA Training**
    - **Problem:** CLIP identifies "neon_blue fails 70% of time"
    - **Solution:**
      1. Generate 1000 focused images with neon_blue
      2. CLIP filter best 100-200
      3. Train micro-LoRA "neon_blue_specialist" (1-2h)
      4. Merge into main checkpoint
      5. → neon_blue now works 90%!
    - **Benefit:** Targeted improvement of failing variations
  - **Phase 4: Theme-Specific LoRAs**
    - Train separate LoRAs per theme (gala, cyberpunk, mafia, fantasy)
    - Load dynamically: `sdgen generate --theme gala --lora gala.safetensors`
    - Each LoRA = 2-3h training, highly specialized
  - **Tech Stack:**
    - **LoRA Training:** kohya_ss (GUI + scripts) or sd-scripts (CLI)
    - **Checkpoints:** SDXL or SD 1.5 base models
    - **Data Pipeline:** CLIP validation → Auto-labeling → kohya dataset format
    - **Hardware:** RTX 5070 Ti = 2-3x faster than baseline (RTX 3060)
  - **Progressive Approach:**
    1. **Week 1-2:** Deploy CLIP/NSFW-CLIP, collect validation data
    2. **Week 3:** Train first custom classifier on collected feedback
    3. **Week 4:** First LoRA training experiment (single theme)
    4. **Week 5+:** Self-improving pipeline automation
  - **Benefits:**
    - **Data-driven:** Stats reveal which prompts/variations need work
    - **Automated improvement:** Less manual prompt engineering
    - **Personalized checkpoint:** Understands YOUR style/variations
    - **Scalable:** More generations = better training data = better model
  - **Risk/Effort:**
    - Medium complexity (requires ML knowledge)
    - High reward (industry-level AI workflow)
    - Hardware: Already available (5070 Ti perfect for this)
  - **Next Steps:**
    - Start with CLIP validation (Phase 1)
    - Collect 2-4 weeks of validation data
    - Train first custom classifier
    - Evaluate before scaling to LoRA training
- **[Refactor/Chore]** Architecture refactoring with Design Patterns
  - **See detailed analysis:** `.claude/refactoring_opportunities.md`
  - **12 opportunities identified** (Strategy, Factory, Visitor patterns)
  - **3 god objects** to split: template_resolver.py (954L), parser.py (831L), orchestrator.py (706L)
  - Priority targets:
    - P2: Strategy for ADetailer/ControlNet parsing (eliminates 144L if/elif)
    - P3: Split TemplateResolver into ChunkInjector + PlaceholderResolver + SelectorEngine
    - P4: Split ConfigParser by responsibility
    - P5: Factory for config type detection (inheritance_resolver.py:147-160) - ✅ Partially fixed in commit 0254c3a

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
