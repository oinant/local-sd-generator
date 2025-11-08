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

### Epic #67 - Session Dashboard - Issues identifiés 2025-11-08

- **[UX]** Sessions list: 1088 sessions without pagination/filtering
  - **Context:** Sessions.vue displays all 1088 sessions at once in grid
  - **Problem:** Performance issue, hard to find specific session, overwhelming UI
  - **Proposed solution:** Add pagination (20-50 per page) and/or filters (by date, name, tags, favorite)
  - **Priority:** Medium-High (usability issue with large datasets)

- **[Feature]** Sessions list: Lazy loading stats should show loading spinner
  - **Context:** "LOAD STATS" button shows no feedback while loading
  - **Proposed:** Show spinner inside button during API call
  - **Priority:** Low (UX polish)

- **[Feature]** SessionDetail: Manifest endpoint might not exist yet
  - **Context:** Feature 4 calls GET /api/sessions/{name}/manifest
  - **Status:** Need to verify if backend endpoint exists
  - **Priority:** High (Feature 4 depends on it)

- **[Bug/Investigation]** Navigation bug from /sessions - not consistently reproducible
  - **Context:** User reports cannot navigate to /gallery or other routes after visiting /sessions
  - **Investigation results:**
    - Tested with Playwright: Navigation works from /sessions to /gallery
    - Router config looks normal (no blocking guards)
    - Sessions.vue has no beforeRouteLeave hook
    - Menu items use standard `:to` binding
  - **Hypothesis 1:** Performance issue with 1088 session cards (each with `:to` creates router-link)
    - May cause browser slowdown/lag that feels like navigation is broken
    - User might click before page is fully rendered
  - **Hypothesis 2:** Race condition with loading state
    - Loading overlay might block clicks intermittently
  - **Status:** Cannot reproduce consistently, needs more investigation
  - **Priority:** Medium (may be perception/performance issue rather than true bug)

- **[Bug] Gallery route shows "Sessions" header and wrong content
  - **Context:** Navigating to /gallery shows "Sessions" title and "Select a session" message
  - **Location:** /packages/sd-generator-webui/front/src/views/Images.vue (Gallery component)
  - **Impact:** Confusing UX, wrong page title
  - **Status:** DEFER - Legacy code, keep for now
  - **Priority:** Low (deferred)

- **[UX]** Ultra-wide screens (3440x1440): Wasted space on Sessions & Stats pages
  - **Context:** On ultra-wide monitors, cards/boxes are too wide, lots of unused space
  - **Affected pages:** /sessions (session cards), session detail stats
  - **Proposed solution:** Max-width constraint on cards (e.g., max-width: 1200px or use narrower grid)
  - **Priority:** Medium (UX improvement for ultra-wide users)

- **[Bug]** Gallery: Cannot open image detail if thumbnail failed to load
  - **Context:** When thumbnail fails to load, clicking on the placeholder doesn't open detail popup
  - **Expected:** Click should still open detail view even if thumbnail is broken
  - **Impact:** Cannot view images with broken thumbnails
  - **Priority:** Medium-High (usability issue)

- **[Feature]** Session stats: Import manifest data (model, sampler, etc.) into database
  - **Context:** Currently, session_stats table has empty columns for model info:
    ```
    sd_model, sampler, scheduler, cfg_scale, steps, width, height
    ```
  - **Current state:** These are NULL in DB (not populated from manifest.json)
  - **Need:** Bulk import script to populate from existing manifest.json files
  - **Data source:** Read each session's manifest.json and extract:
    - `sd_model` from generation params
    - `sampler`, `scheduler`, `cfg_scale`, `steps`, `width`, `height`
  - **Priority:** High (needed for proper stats display)

- **[Architecture]** Migration: Sessions list from filesystem to database-driven
  - **Current:** /api/sessions/ reads filesystem, generates stats on-the-fly
  - **Problem:** Slow with 1088+ sessions, no caching
  - **Proposed architecture:**
    1. **Database as source of truth** - session_stats table contains all session info
    2. **Bulk import script** - One-time script to populate DB from existing sessions
    3. **Incremental updates:**
       - Option A: "Load new sessions" button (manual trigger)
       - Option B: Background worker/polling (auto-detect new sessions)
    4. **API changes:**
       - GET /api/sessions/ → Query DB instead of filesystem
       - POST /api/sessions/import → Trigger import of new sessions
  - **Benefits:**
    - Fast listing (DB query vs filesystem scan)
    - Filtering/sorting (SQL vs in-memory)
    - Pagination (offset/limit)
    - Search (SQL LIKE/FTS)
  - **Migration plan:**
    1. Write bulk import script (Python)
    2. Populate DB from existing 1088 sessions
    3. Update API to query DB
    4. Add "Import new sessions" endpoint
    5. (Optional) Add background worker for auto-import
  - **Priority:** High (architecture improvement, prerequisite for scaling)
  - **Effort:** Large (requires script + API changes + testing)

- **[Bug]** Session stats: Completion percentage calculation is wrong
  - **Context:** Completion % should be calculated as: (images_in_directory / num_images_from_manifest) * 100
  - **Current:** Unknown calculation method (likely using variations_theoretical instead of num_images)
  - **Impact:** Misleading completion indicator
  - **Priority:** High (core feature accuracy)
  - **Location:** Backend - SessionStatsService.compute_stats()

- **[Feature]** SessionDetail: Metadata PUT endpoint might not exist
  - **Context:** Feature 5 calls PUT /api/sessions/{name}/metadata
  - **Status:** Need to verify if backend endpoint exists (only GET/PATCH/DELETE in api.js)
  - **Priority:** High (Feature 5 depends on it)
  - **Resolution:** Fixed - uses PATCH via api.updateSessionMetadata()

- **[Bug]** WebUI: Image refresh appends duplicates to session (should replace, not append)
  - **Context:** When refreshing images in a session, the UI appends the same images again instead of replacing the list
  - **Expected:** Refresh should clear and reload the image list
  - **Impact:** Confusing UX, duplicate images displayed

- **[Bug/UX]** WebUI: Mobile UI is unusable - Need session list/results split screen
  - **Context:** On mobile, the webapp is completely unusable
  - **Problems:**
    1. Session list and session results are shown on same screen → too cramped
    2. No way to navigate back from results to session list easily
  - **Proposed solution:**
    - Split into 2 screens: "Session List" and "Session Results"
    - Swipe left on "Session Results" → goes back to "Session List"
    - BUT: Swipe should NOT trigger when viewing image details (only on gallery)
  - **Priority:** High (mobile is currently broken)

- **[UX]** WebUI: Header bar wastes space on Session Results screen
  - **Context:** The app header (logo + title?) appears above Session Results even in desktop mode
  - **Problem:** Takes vertical space for no reason when viewing images
  - **Proposed solution:** Header should only appear on Session List screen, not on Results screen
  - **Benefit:** More space for image gallery (especially on mobile)

- **[Bug]** WebUI: Double scrollbar in Session Results (window + gallery)
  - **Context:** Two scrollbars appear:
    1. One for the gallery content itself
    2. One for the entire window/app
  - **Problem:** Confusing scroll behavior, harder to navigate
  - **Proposed solution:** Size the gallery container correctly so only ONE scrollbar (gallery) is needed
  - **Expected:** Window should not scroll, only the gallery container

- **[UX]** WebUI: Tags textbox placement is wrong
  - **Context:** Tags textbox is not positioned logically
  - **Proposed placement:** Between session name and image count chip
  - **Current:** (Unknown - somewhere else?)

- **[Question]** WebUI: What is the tags textbox for? (Non-functional currently)
  - **Context:** There's a tags textbox but it doesn't seem to do anything
  - **Question:** What's the intended purpose?
    - Filter by tags?
    - Add tags to session?
    - Search tags?
  - **Status:** Non-functional, needs clarification of intended behavior

- **[Bug/UX]** WebUI: Thumbnails are blurry (cropped to square + zoomed)
  - **Context:** In Session Results gallery, image thumbnails are blurry
  - **Problem:** Images are cropped to square format then zoomed/upscaled → quality loss
  - **Proposed solution:** Don't crop, display at original resolution (maintain aspect ratio)
  - **Expected:** Sharp thumbnails with original aspect ratio (e.g., 512×768 displayed as 512×768 thumbnail, not cropped to 512×512)
  - **Impact:** Medium (usability - harder to evaluate image quality at a glance)

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
- **[Feature/Refactor]** Direct SD Pipeline (Replace A1111 API with PyTorch pipeline)
  - **Full spec:** `docs/roadmap/future/direct_pipeline.md` (4,159 words)
  - **Goal:** 36 sec/image → 5-10 sec/image (3-7x speedup with H100, 2.5x with 5070 Ti)
  - **Framework recommendation:** ComfyUI (Score 4.5/5 vs diffusers 3.6/5)
  - **Why ComfyUI:**
    - 2x faster than A1111 (native caching, batch optimization)
    - 500+ custom nodes (ADetailer, ControlNet, LoRA, upscalers)
    - Python API for programmatic control
    - Memory efficient (2x SDXL models vs diffusers crash)
  - **Effort:** 11 weeks MVP (POC 2w, Core 4w, Advanced 4w), 17-19 weeks full
  - **Phases:**
    1. Infrastructure setup (1w)
    2. POC - Generate 1 image (2w)
    3. Core pipeline - txt2img + img2img (4w)
    4. Advanced - LoRA + upscalers + batch (4w)
    5. Extensions - ADetailer + ControlNet (4-6w)
    6. Optimization - 100+ batch, CLIP scoring (6w)
  - **Risk:** Medium (migration complexity, testing, feature parity)
  - **Benefits:**
    - Native batch processing (128+ images)
    - Foundation for self-improving generator loop
    - Full GPU utilization (5070 Ti → H100 ready)
    - Eliminate HTTP/JSON overhead
  - **Compatibility:** 100% with Template System V2.0 (no changes required)
  - **Performance estimates:**
    - 5070 Ti: 1 image 36s→14s, 100 images 60min→23min
    - H100: 1 image 36s→6s, 100 images 60min→10min
  - **ROI:** 38k images in 63h (vs 380h current) with H100
  - **Priority:** P3 (Strategic investment, enable advanced ML workflows)
- **[Feature/Infrastructure]** Cloud GPU Burst (H100 instances for heavy workloads)
  - **Full spec:** `docs/roadmap/future/cloud_gpu_burst.md` (comprehensive)
  - **Goal:** Offload heavy compute to cloud H100 @ €2.80/h (€3.36 TTC)
  - **Architecture:** Hybrid (local orchestration + cloud compute)
  - **Performance gains vs Local (5070 Ti + ComfyUI):**
    - 1 image: 14s → 6s (2.3x speedup)
    - 500 images: 1.94h → 50 min (2.3x speedup)
    - LoRA training: 3h → 20 min (9x speedup)
  - **Cost analysis:**
    - 500 images: €3.19 (ROI +€45.92 if dev time €50/h)
    - LoRA training: €1.41 (ROI +€127.76)
    - Break-even: ~50-60 images
  - **Use cases (Priority):**
    - ✅ P1: LoRA training (killer use case, 9x speedup, €1.41)
    - ✅ P1: Batch >500 images (ROI fortement positif)
    - ✅ P1: CLIP validation (38k images en 1 jour vs 5 jours)
    - ❌ P3: Batch <100 images (ROI négatif, rester local)
  - **Effort:** 6 weeks MVP (POC 2w, automation 4w), 12 weeks production
  - **Phases:**
    1. POC - Manual SSH + rsync workflow (2w)
    2. MVP - Automated provisioning + CLI `--cloud` flag (4w)
    3. Production - Multi-cloud + spot instances (6w)
  - **Setup requirements:**
    - VM: Ubuntu 22.04 + CUDA 12.1 (OVH image)
    - Dependencies: PyTorch, ComfyUI, diffusers, xformers
    - Storage: 47-57 GB (models, checkpoints, LoRAs)
    - Bandwidth: Upload 500 KB (prompts), Download 2 GB (images)
  - **Communication:** SSH + rsync (MVP), REST API (Phase 3)
  - **Provisioning strategies:**
    - Custom image OVH (setup 3 min vs 15 min cold start)
    - Auto-teardown after job (avoid idle costs)
    - Model caching (persistent storage, avoid re-upload)
  - **Cost optimization:**
    - Multi-cloud (RunPod €2.15/h → -23% vs OVH)
    - Spot instances (€1.20/h → -64% vs on-demand)
    - Budget alerts (€50/jour)
  - **Risks:** Medium (cost overrun, cold start time, security)
  - **Benefits:**
    - 10x faster LoRA training (critical for self-improving loop)
    - Massive batch processing (38k images in 3 days vs 6 days)
    - Pay-per-use (no upfront €30k H100 purchase)
    - Foundation for cloud-native ML workflows
  - **Compatibility:** 100% with Template System V2.0 + Direct Pipeline
  - **Strategic value:** Enables self-improving generator loop (Generate → CLIP → Train → Loop)
  - **Priority:** P4 (Strategic investment, depends on Direct Pipeline)

- **[Feature]** LLM-based Template Reconstruction & Prompt Inference
  - **Context:** 546 sessions migrées avec manifests v2.0, dont 128 inférées avec méthode basique
  - **Problem:** Inférence actuelle = parsing basique (filename + PNG metadata)
    - Certains placeholders non détectés (medium/low confidence)
    - Templates manquants pour sessions très anciennes
  - **Goal:** Utiliser un LLM local pour reconstruire templates complets par ingénierie inverse
  - **Approach - Reverse Engineering Total:**
    ```
    Input: Collection de prompts résolus
      "1girl, bob cut, blue eyes, standing, beach"
      "1girl, ponytail, green eyes, sitting, forest"
      "1girl, braided, blue eyes, running, city"

    Output LLM:
      Template: "1girl, {HairStyle}, {EyeColor}, {Pose}, {Location}"
      Variations:
        HairStyle: [bob cut, ponytail, braided]
        EyeColor: [blue eyes, green eyes]
        Pose: [standing, sitting, running]
        Location: [beach, forest, city]
    ```
  - **Capabilities:**
    - Détecte automatiquement parties fixes vs variables
    - Nomme intelligemment les placeholders (HairStyle, EyeColor, Pose, Location)
    - Détecte structures complexes (loras, emphasis, nested constructs)
    - Fonctionne même sans aucune métadonnée (sessions ultra-anciennes)
    - Améliore les manifests medium/low confidence existants
  - **Use Cases:**
    1. **Amélioration manifests existants** - Compléter les 84 medium + 7 low confidence
    2. **Sessions ultra-anciennes** - Reconstruire templates pour sessions sans config
    3. **Validation qualité** - Vérifier cohérence template ↔ prompts générés
    4. **Migration legacy** - Convertir anciennes sessions V0 sans métadonnées
  - **Tech Stack:**
    - **LLM local:** Ollama (llama 3.1 70B ou mistral), LM Studio, ou vLLM
    - **Context:** Collection prompts + images PNG metadata
    - **Output:** Template YAML + variations dict → manifest.json enrichi
    - **Batch processing:** Analyse 10-50 sessions en une passe
  - **Architecture:**
    - `sdgen metadata infer-template --llm ollama://llama3.1:70b`
    - Lit manifests existants (v2.0-inferred)
    - Extrait tous les prompts de la session
    - Prompt LLM pour reconstruction template
    - Enrichit manifest avec template reconstruit + placeholder names
  - **Benefits:**
    - **Couverture 100%** - Même les sessions les plus anciennes
    - **Qualité supérieure** - Nommage sémantique des placeholders
    - **Validation** - Détecte incohérences dans prompts
    - **Future-proof** - Foundation pour analyse avancée (CLIP validation)
  - **Phases:**
    1. **Week 1:** POC avec Ollama + 10 sessions test
    2. **Week 2:** Batch processing + enrichissement manifests
    3. **Week 3:** Validation + amélioration prompts LLM
    4. **Week 4:** Production sur 546 sessions complètes
  - **Effort:** Medium (~2-3 weeks), dépend de perf LLM local
  - **Priority:** P6 (Nice-to-have, amélioration qualité manifests)
  - **Dependencies:** Ollama/LM Studio installé, modèle 70B téléchargé

<!-- Add new items here during braindump sessions -->

---

## 🔍 Being Analyzed

_Items currently being structured by Agent PO_

<!-- Agent PO moves items here during analysis -->

---

## 📋 Tracked on GitHub

_Items with GitHub issues created (ready for implementation)_

### 2025-11-06 Session - Seed-based Variation Comparison

- **[Feature]** WebUI: Seed-based Variation Comparison View → [#65](https://github.com/oinant/local-sd-generator/issues/65)
  - **Priority:** P4-P5 (High/Medium), **Effort:** Medium (~12-16h)
  - **Goal:** Interactive UI to compare variations side-by-side for same seed (scientific A/B testing)
  - **Perfect synergy with:** #64 (Seed-sweep mode - data producer), #62 (Variation tagging - feedback loop)
  - **Key features:**
    - Seed selector: Iterate through all seeds used in session
    - Placeholder pivot: Choose which placeholder to analyze (e.g., HairColor)
    - Fixed value filters: Filter by other placeholders (Pose=standing, Outfit=dress)
    - Side-by-side comparison grid: 2-4 variations at once
    - Quick tagging: Reuse #62 tagging system (OK/KO buttons)
    - Gallery filter extension: Filter main gallery by variation values
  - **Use cases:**
    1. Scientific A/B testing: Compare "red hair" vs "crimson hair" on same seed
    2. Seed bias detection: Find which seeds work best across variations
    3. Variation stability: Identify which variations give consistent results
    4. Multi-placeholder analysis: Test one placeholder while fixing others
  - **Benefits:** Data-driven prompt engineering, 20 seeds reviewed in 5 min (vs manual), foundation for CLIP validation

### 2025-11-05 Session - Quality Control & Analysis Workflow Epic

- **[Epic]** Quality Control & Analysis Workflow (Session Review & Tagging System)
  - **Goal:** Rapid quality assessment + identify low-impact variations
  - **MVP Issues (P4-P6, ~40h total):**
    - [#61](https://github.com/oinant/local-sd-generator/issues/61) - [Feature] Image Quality Tagging System
      - Priority: P4 (High), Effort: Medium (~16h)
      - Image-level tags: favorite/interesting/trash
      - Backend: SQLite table + REST API
      - Frontend: Tag buttons + filters
    - [#62](https://github.com/oinant/local-sd-generator/issues/62) - [Feature] Placeholder Variation Quality Tagging
      - Priority: P4 (High), Effort: Medium (~18h)
      - Variation-level tags: OK/KO per placeholder value
      - Statistics: Success rates per variation
      - Use case: "Position:standing works 90%, crouching fails 60%"
    - [#63](https://github.com/oinant/local-sd-generator/issues/63) - [Enhancement] Gallery UI with Keyboard Navigation
      - Priority: P6 (Medium), Effort: Small (~8h)
      - Keyboard shortcuts: F/T/I/U for tagging, arrows for navigation
      - Quick review: 100 images in 5 min vs 30 min
  - **Phase 2 (Pending creation):**
    - Variation Analysis Statistics Dashboard (P6, ~12h)
    - Perceptual Hash Similarity Detection (P5, ~24h)
  - **Strategic value:** Foundation for CLIP validation + ML workflows

- **[Feature]** Consistency Test Mode - Seed-Sweep Generation → [#64](https://github.com/oinant/local-sd-generator/issues/64)
  - **Priority:** P5 (Medium-High), **Effort:** Medium (~14-18h)
  - **Goal:** Reverse engineering semantic understanding of the model
  - **Use case:** Test each variation on SAME seeds to measure stability
  - **Example:** "red hair" → 18/20 seeds OK (90% stable) ✅ vs "crimson hair" → 8/20 OK (40% stable) ❌
  - **CLI:** `sdgen generate -t template.yaml --mode consistency --seeds 1000-1019`
  - **Synergy:** Perfect workflow with #61, #62 (consistency mode → tagging → statistics)
  - **Strategic value:** Foundation for semantic optimization + LoRA training

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
