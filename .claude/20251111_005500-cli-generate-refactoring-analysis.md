# Architecture Analysis: _generate() Function Refactoring

**Date:** 2025-11-11
**Updated:** 2025-11-12 (Added V2 architecture decisions)
**Target:** `packages/sd-generator-cli/sd_generator_cli/cli.py::_generate()`
**Analyzed by:** Architecture Agent

## Executive Summary

The `_generate()` function is a 562-line monolithic function with multiple Single Responsibility Principle (SRP) violations. This document provides a comprehensive analysis and proposes a phased refactoring plan to reduce it to <100 lines through modular extraction.

**Migration Strategy:** Strangler Fig Pattern with feature flag inside `_generate()` to route between old implementation and new V2 orchestrator.

## Current State Analysis

### Function Size
- **Total lines: 562** (lines 185-746)
- **Try-except coverage:** Lines 229-746 (entire function body)
- **Number of distinct logical blocks:** 17 major blocks

### Flow Diagram

```
_generate() Function Flow (lines 185-746)
════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────┐
│ BLOCK 1: Imports & Setup (lines 224-227)                           │
│ Responsibility: Import required modules                             │
│ Dependencies: None                                                   │
│ Complexity: Low                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BLOCK 2: Template Validation (lines 230-250)                        │
│ Responsibility: Validate YAML schema if not skipped                 │
│ Dependencies: template_path, skip_validation                        │
│ Complexity: Low                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BLOCK 3: Pipeline Initialization & Template Loading (lines 252-264) │
│ Responsibility: Initialize V2Pipeline and load template             │
│ Dependencies: global_config, template_path, theme_name, style       │
│ Complexity: Low                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BLOCK 4: Fixed Placeholders Processing (lines 266-281)              │
│ Responsibility: Parse and apply fixed placeholder values             │
│ Dependencies: use_fixed parameter, context                           │
│ Complexity: Medium                                                   │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BLOCK 5: Seed-Sweep Mode Setup (lines 283-292)                      │
│ Responsibility: Parse and apply seed list if specified              │
│ Dependencies: seeds parameter, resolved_config                       │
│ Complexity: Low                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BLOCK 6: Prompt Generation & Statistics (lines 294-338)             │
│ Responsibility: Generate prompts and display variation stats        │
│ Dependencies: pipeline, resolved_config, context                    │
│ Complexity: Medium-High                                              │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BLOCK 7: Session Name Resolution (lines 340-351)                    │
│ Responsibility: Determine final session name with priority logic    │
│ Dependencies: session_name_override, config, template_path          │
│ Complexity: Low                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BLOCK 8: API Components Initialization (lines 353-387)              │
│ Responsibility: Setup API client, session manager, writers          │
│ Dependencies: api_url, output_base_dir, session_name                │
│ Complexity: Medium                                                   │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BLOCK 9: Manifest Snapshot Creation (lines 389-512)                 │
│ Responsibility: Build and save initial manifest.json                │
│ Sub-tasks:                                                           │
│  - Fetch runtime info (lines 390-397)                               │
│  - Extract variations from context (lines 399-449)                   │
│  - Build generation params (lines 451-468)                           │
│  - Build API params (lines 469-478)                                  │
│  - Create snapshot object (lines 480-496)                            │
│  - Save temp manifest (lines 499-510)                                │
│ Dependencies: api_client, context, config, prompts                   │
│ Complexity: **HIGH** (124 lines, complex logic)                      │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BLOCK 10: API Connection Test (lines 514-521)                       │
│ Responsibility: Test SD API connection if not dry-run               │
│ Dependencies: dry_run, api_client, api_url                           │
│ Complexity: Low                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BLOCK 11: Generation Config Setup (lines 523-542)                   │
│ Responsibility: Apply generation parameters to API client           │
│ Dependencies: prompts[0]['parameters']                               │
│ Complexity: Low                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BLOCK 12: Annotation Worker Setup (lines 544-556)                   │
│ Responsibility: Start background annotation worker if enabled       │
│ Dependencies: config.output.annotations                              │
│ Complexity: Low                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BLOCK 13: Prompt Configs Conversion (lines 558-632)                 │
│ Responsibility: Convert V2 prompts to PromptConfig list             │
│ Sub-tasks:                                                           │
│  - Resolve ControlNet image variations (lines 565-614)              │
│  - Build filenames with seeds (lines 618-623)                        │
│  - Create PromptConfig objects (lines 625-632)                       │
│ Dependencies: prompts, context, config, session_name                 │
│ Complexity: **HIGH** (75 lines, nested logic with deep copies)      │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BLOCK 14: Manifest Update Callback Definition (lines 634-679)       │
│ Responsibility: Define callback for incremental manifest updates    │
│ Dependencies: manifest_path, prompts, annotation_worker              │
│ Complexity: Medium                                                   │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BLOCK 15: Image Generation (lines 681-690)                          │
│ Responsibility: Execute batch generation with callback              │
│ Dependencies: generator, prompt_configs, callback                    │
│ Complexity: Low                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BLOCK 16: Final Manifest Update & Cleanup (lines 692-727)           │
│ Responsibility: Update status, stop worker, display summary         │
│ Dependencies: manifest_path, annotation_worker                       │
│ Complexity: Medium                                                   │
└─────────────────────────────────────────────────────────────────────┘
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│ BLOCK 17: Error Handling (lines 729-746)                            │
│ Responsibility: Update manifest on error and display traceback      │
│ Dependencies: manifest_path, _current_manifest_path                  │
│ Complexity: Low                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Block Analysis

#### BLOCK 1: Imports & Setup (lines 224-227)
- **Lines:** 224-227
- **Responsibility:** Import required modules (V2Pipeline, API clients, validators)
- **Dependencies:** None (module imports)
- **SRP violation?:** No - single responsibility (import declarations)
- **Complexity:** Low

#### BLOCK 2: Template Validation (lines 230-250)
- **Lines:** 230-250
- **Responsibility:** Validate YAML schema unless --skip-validation
- **Dependencies:** `template_path`, `skip_validation` flag
- **SRP violation?:** No - cohesive validation logic
- **Complexity:** Low (simple conditional with error formatting)

#### BLOCK 3: Pipeline Initialization & Template Loading (lines 252-264)
- **Lines:** 252-264
- **Responsibility:** Initialize V2Pipeline and load/resolve template
- **Dependencies:** `global_config.configs_dir`, `template_path`, `theme_name`, `theme_file`, `style`
- **SRP violation?:** No - cohesive pipeline setup
- **Complexity:** Low

#### BLOCK 4: Fixed Placeholders Processing (lines 266-281)
- **Lines:** 266-281
- **Responsibility:** Parse `--use-fixed` parameter and apply to context
- **Dependencies:** `use_fixed` parameter, `context`
- **SRP violation?:** No - focused on fixed values handling
- **Complexity:** Medium (error handling, context mutation)

#### BLOCK 5: Seed-Sweep Mode Setup (lines 283-292)
- **Lines:** 283-292
- **Responsibility:** Parse `--seeds` parameter and apply to config
- **Dependencies:** `seeds` parameter, `resolved_config`
- **SRP violation?:** No - focused on seed configuration
- **Complexity:** Low

#### BLOCK 6: Prompt Generation & Statistics (lines 294-338)
- **Lines:** 294-338
- **Responsibility:** Generate prompts and display variation statistics
- **Dependencies:** `pipeline`, `resolved_config`, `context`, `count`
- **SRP violation?:** **YES** - Mixed concerns: generation + statistics extraction + UI display
- **Complexity:** Medium-High (45 lines, complex stats formatting)

#### BLOCK 7: Session Name Resolution (lines 340-351)
- **Lines:** 340-351
- **Responsibility:** Determine final session name with priority logic
- **Dependencies:** `session_name_override`, `config.output.session_name`, `config.name`, `template_path`
- **SRP violation?:** No - focused responsibility
- **Complexity:** Low (simple priority chain)

#### BLOCK 8: API Components Initialization (lines 353-387)
- **Lines:** 353-387
- **Responsibility:** Create API client, session manager, image writer, progress reporter, batch generator
- **Dependencies:** `api_url`, `output_base_dir`, `session_name`, `dry_run`, `theme_name`, `style`
- **SRP violation?:** No - cohesive component initialization
- **Complexity:** Medium (multiple objects, but straightforward)

#### BLOCK 9: Manifest Snapshot Creation (lines 389-512) 🔴 CRITICAL
- **Lines:** 389-512 (**124 lines**)
- **Responsibility:** Build and save initial manifest.json
- **Sub-tasks:**
  - Fetch runtime info from API (lines 390-397)
  - Extract variations from context (lines 399-449)
  - Build generation params (lines 451-468)
  - Build API params (lines 469-478)
  - Create snapshot object (lines 480-496)
  - Save temporary manifest (lines 499-510)
- **Dependencies:** `api_client`, `context`, `config`, `prompts`, `stats`, `fixed_placeholders`, `theme_name`, `style`
- **SRP violation?:** **YES - MAJOR** - Multiple responsibilities mixed together:
  - Runtime info fetching (API concern)
  - Variations extraction (data transformation)
  - Parameter building (data serialization)
  - Snapshot assembly (data model creation)
  - File I/O (persistence)
- **Complexity:** **HIGH** - 124 lines, nested logic, regex parsing, complex conditionals

#### BLOCK 10: API Connection Test (lines 514-521)
- **Lines:** 514-521
- **Responsibility:** Test connection to SD API
- **Dependencies:** `dry_run`, `api_client`, `api_url`
- **SRP violation?:** No
- **Complexity:** Low

#### BLOCK 11: Generation Config Setup (lines 523-542)
- **Lines:** 523-542
- **Responsibility:** Apply generation parameters from first prompt to API client
- **Dependencies:** `prompts[0]['parameters']`
- **SRP violation?:** No
- **Complexity:** Low (straightforward parameter mapping)

#### BLOCK 12: Annotation Worker Setup (lines 544-556)
- **Lines:** 544-556
- **Responsibility:** Start background annotation worker
- **Dependencies:** `config.output.annotations`
- **SRP violation?:** No
- **Complexity:** Low

#### BLOCK 13: Prompt Configs Conversion (lines 558-632) 🔴 CRITICAL
- **Lines:** 558-632 (**75 lines**)
- **Responsibility:** Convert V2 prompts to PromptConfig list
- **Sub-tasks:**
  - Resolve ControlNet image variations (lines 565-614)
  - Build filenames with seeds (lines 618-623)
  - Create PromptConfig objects (lines 625-632)
- **Dependencies:** `prompts`, `context`, `config`, `session_name`
- **SRP violation?:** **YES** - Mixed concerns:
  - ControlNet image resolution (path resolution logic)
  - Variation enrichment (data transformation)
  - Filename generation (naming logic)
  - Object conversion (data mapping)
- **Complexity:** **HIGH** - 75 lines, deep nesting, complex conditionals, deep copies

#### BLOCK 14: Manifest Update Callback Definition (lines 634-679)
- **Lines:** 634-679 (46 lines)
- **Responsibility:** Define incremental manifest update callback
- **Dependencies:** `manifest_path`, `prompts`, `annotation_worker`
- **SRP violation?:** **YES** - Multiple concerns in callback:
  - Seed extraction from API response (parsing)
  - Manifest reading (I/O)
  - Image entry creation (data model)
  - Manifest writing (I/O)
  - Annotation worker submission (worker management)
- **Complexity:** Medium-High (nested try-except, JSON parsing, file I/O)

#### BLOCK 15: Image Generation (lines 681-690)
- **Lines:** 681-690
- **Responsibility:** Execute batch generation
- **Dependencies:** `generator`, `prompt_configs`, `update_manifest_incremental`
- **SRP violation?:** No
- **Complexity:** Low

#### BLOCK 16: Final Manifest Update & Cleanup (lines 692-727)
- **Lines:** 692-727
- **Responsibility:** Update manifest status, stop annotation worker, display summary
- **Dependencies:** `manifest_path`, `annotation_worker`, `dry_run`, `config.output.annotations`
- **SRP violation?:** **YES** - Mixed concerns:
  - Manifest status update (persistence)
  - Annotation worker cleanup (worker management)
  - Summary display (UI)
- **Complexity:** Medium

#### BLOCK 17: Error Handling (lines 729-746)
- **Lines:** 729-746
- **Responsibility:** Update manifest on error and display traceback
- **Dependencies:** `manifest_path`, `_current_manifest_path`
- **SRP violation?:** No - cohesive error handling
- **Complexity:** Low

---

## Proposed Refactoring

### Key Problems Identified

1. **Function is too long:** 562 lines violates SRP at function level
2. **Multiple SRP violations in blocks:** 6, 9, 13, 14, 16
3. **High cognitive complexity:** Deep nesting, mixed concerns
4. **Poor testability:** Hard to unit test individual concerns
5. **Hidden dependencies:** Relies on closure state (manifest_path, prompts)
6. **Tight coupling:** Direct file I/O, API calls, UI mixed together

### New Modules/Classes

#### 1. **TemplateValidator** (Existing: `SchemaValidator`)
Already exists but could be enhanced with better integration.

```python
# sd_generator_cli/templating/validators/template_validator.py
class TemplateValidator:
    """Validates templates before generation."""

    def validate_or_exit(
        self,
        template_path: Path,
        skip_validation: bool,
        console: Console
    ) -> None:
        """Validate template and exit if invalid."""
```

#### 2. **TemplateLoader**
```python
# sd_generator_cli/templating/loaders/template_loader.py
class TemplateLoader:
    """Loads and resolves templates with themes."""

    def load_and_resolve(
        self,
        template_path: Path,
        configs_dir: Path,
        theme_name: Optional[str],
        theme_file: Optional[Path],
        style: str
    ) -> Tuple[ResolvedConfig, ResolvedContext]:
        """Load template and resolve with theme/style."""
```

#### 3. **PlaceholderProcessor**
```python
# sd_generator_cli/templating/processors/placeholder_processor.py
class PlaceholderProcessor:
    """Processes placeholder-related operations."""

    def apply_fixed_values(
        self,
        context: ResolvedContext,
        fixed_str: Optional[str],
        console: Console
    ) -> ResolvedContext:
        """Parse and apply fixed placeholder values."""

    def apply_seed_sweep(
        self,
        config: ResolvedConfig,
        seeds_str: Optional[str],
        console: Console
    ) -> ResolvedConfig:
        """Parse and apply seed-sweep configuration."""
```

#### 4. **PromptGenerator**
```python
# sd_generator_cli/templating/generators/prompt_generator.py
class PromptGenerator:
    """Generates prompts and provides statistics."""

    def generate_with_stats(
        self,
        pipeline: V2Pipeline,
        config: ResolvedConfig,
        context: ResolvedContext,
        count_limit: Optional[int],
        console: Console
    ) -> Tuple[List[dict], dict]:
        """Generate prompts and return with statistics."""
```

#### 5. **SessionConfigurator**
```python
# sd_generator_cli/execution/session_configurator.py
class SessionConfigurator:
    """Configures session name and output directory."""

    def resolve_session_name(
        self,
        override: Optional[str],
        config: TemplateConfig,
        template_path: Path
    ) -> str:
        """Resolve session name with priority logic."""

    def create_api_components(
        self,
        api_url: str,
        output_dir: Path,
        session_name: str,
        total_images: int,
        dry_run: bool,
        theme_name: Optional[str],
        style: str
    ) -> Tuple[SDAPIClient, SessionManager, ImageWriter, ProgressReporter, BatchGenerator]:
        """Create and configure all API components."""
```

#### 6. **ManifestBuilder**
```python
# sd_generator_cli/execution/manifest/manifest_builder.py
class ManifestBuilder:
    """Builds manifest snapshots from template state."""

    def __init__(self, api_client: SDAPIClient):
        self.api_client = api_client

    def fetch_runtime_info(self) -> dict:
        """Fetch runtime info from SD API."""

    def extract_variations(
        self,
        context: ResolvedContext,
        config: ResolvedConfig,
        prompts: List[dict]
    ) -> dict:
        """Extract variation mappings from context and prompts."""

    def build_generation_params(
        self,
        config: TemplateConfig,
        stats: dict,
        num_images: int
    ) -> dict:
        """Build generation parameters object."""

    def build_api_params(self, prompts: List[dict]) -> dict:
        """Extract API parameters from first prompt."""

    def build_snapshot(
        self,
        config: ResolvedConfig,
        runtime_info: dict,
        variations: dict,
        generation_params: dict,
        api_params: dict,
        fixed_placeholders: dict,
        theme_name: Optional[str],
        style: str
    ) -> dict:
        """Assemble complete manifest snapshot."""
```

#### 7. **ManifestManager**
```python
# sd_generator_cli/execution/manifest/manifest_manager.py
class ManifestManager:
    """Manages manifest lifecycle (create, update, finalize)."""

    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path

    def initialize(self, snapshot: dict) -> None:
        """Create initial manifest with 'ongoing' status."""

    def update_incremental(
        self,
        idx: int,
        prompt_cfg: PromptConfig,
        prompt_dict: dict,
        api_response: Optional[dict]
    ) -> None:
        """Add new image entry to manifest."""

    def finalize(self, status: str = "completed") -> None:
        """Update manifest status (completed/aborted)."""
```

#### 8. **PromptConfigConverter**
```python
# sd_generator_cli/execution/prompt_config_converter.py
class PromptConfigConverter:
    """Converts V2 prompts to PromptConfig objects."""

    def convert_batch(
        self,
        prompts: List[dict],
        context: ResolvedContext,
        config: TemplateConfig,
        session_name: str
    ) -> List[PromptConfig]:
        """Convert list of V2 prompts to PromptConfig objects."""

    def _resolve_controlnet_images(
        self,
        parameters: dict,
        variations: dict,
        context: ResolvedContext,
        config: TemplateConfig
    ) -> Tuple[dict, dict]:
        """Resolve ControlNet image variations to paths."""
```

#### 9. **AnnotationCoordinator**
```python
# sd_generator_cli/execution/annotation_coordinator.py
class AnnotationCoordinator:
    """Coordinates annotation worker lifecycle."""

    def start_if_enabled(
        self,
        config: TemplateConfig,
        dry_run: bool,
        console: Console
    ) -> Optional[AnnotationWorker]:
        """Start annotation worker if enabled."""

    def submit_image(
        self,
        worker: Optional[AnnotationWorker],
        image_path: Path,
        variations: dict
    ) -> None:
        """Submit image to annotation queue."""

    def stop_and_wait(
        self,
        worker: Optional[AnnotationWorker],
        console: Console
    ) -> None:
        """Stop worker and wait for pending jobs."""
```

#### 10. **GenerationOrchestrator** (New high-level class)
```python
# sd_generator_cli/execution/generation_orchestrator.py
class GenerationOrchestrator:
    """Orchestrates the entire generation workflow."""

    def __init__(
        self,
        validator: TemplateValidator,
        loader: TemplateLoader,
        placeholder_processor: PlaceholderProcessor,
        prompt_generator: PromptGenerator,
        session_configurator: SessionConfigurator,
        manifest_builder: ManifestBuilder,
        manifest_manager: ManifestManager,
        converter: PromptConfigConverter,
        annotation_coordinator: AnnotationCoordinator,
        console: Console
    ):
        # Dependency injection
        pass

    def orchestrate(
        self,
        template_path: Path,
        global_config: GlobalConfig,
        count: Optional[int],
        api_url: str,
        dry_run: bool,
        session_name_override: Optional[str] = None,
        theme_name: Optional[str] = None,
        theme_file: Optional[Path] = None,
        style: str = "default",
        skip_validation: bool = False,
        use_fixed: Optional[str] = None,
        seeds: Optional[str] = None
    ) -> None:
        """Execute complete generation workflow."""
        # 1. Validate
        self.validator.validate_or_exit(...)

        # 2. Load & resolve
        config, context = self.loader.load_and_resolve(...)

        # 3. Process placeholders
        context = self.placeholder_processor.apply_fixed_values(...)
        config = self.placeholder_processor.apply_seed_sweep(...)

        # 4. Generate prompts
        prompts, stats = self.prompt_generator.generate_with_stats(...)

        # 5. Setup session
        session_name = self.session_configurator.resolve_session_name(...)
        api_client, session_manager, ... = self.session_configurator.create_api_components(...)

        # 6. Build manifest
        snapshot = self.manifest_builder.build_snapshot(...)
        self.manifest_manager.initialize(snapshot)

        # 7. Start annotation worker
        worker = self.annotation_coordinator.start_if_enabled(...)

        # 8. Convert prompts
        prompt_configs = self.converter.convert_batch(...)

        # 9. Generate images
        generator.generate_batch(
            prompt_configs,
            callback=self._create_callback(...)
        )

        # 10. Finalize
        self.manifest_manager.finalize("completed")
        self.annotation_coordinator.stop_and_wait(worker, console)
```

---

### Collaboration Diagram

```
CLI Entry Point (cli.py::generate_images)
          ↓
    _generate() → GenerationOrchestrator
                       ↓
    ┌──────────────────┴───────────────────┐
    │                                      │
    ↓                                      ↓
TemplateValidator              TemplateLoader
    ↓                                      ↓
PlaceholderProcessor          V2Pipeline (existing)
    ↓                                      ↓
PromptGenerator               ResolvedContext
    ↓
SessionConfigurator
    ↓
    ├─→ SDAPIClient (existing)
    ├─→ SessionManager (existing)
    ├─→ ImageWriter (existing)
    ├─→ ProgressReporter (existing)
    └─→ BatchGenerator (existing)
    ↓
ManifestBuilder
    ├─→ fetch_runtime_info()
    ├─→ extract_variations()
    ├─→ build_generation_params()
    ├─→ build_api_params()
    └─→ build_snapshot()
    ↓
ManifestManager
    ├─→ initialize()
    ├─→ update_incremental() (callback)
    └─→ finalize()
    ↓
AnnotationCoordinator
    ├─→ start_if_enabled()
    ├─→ submit_image() (in callback)
    └─→ stop_and_wait()
    ↓
PromptConfigConverter
    ├─→ convert_batch()
    └─→ _resolve_controlnet_images()
    ↓
BatchGenerator.generate_batch()
```

---

### Benefits

#### 1. **Testability**
- Each module can be unit tested independently
- Mocking becomes trivial with dependency injection
- Can test manifest building without API calls
- Can test ControlNet resolution without file I/O

#### 2. **Maintainability**
- Each class has <200 lines
- Single Responsibility Principle respected
- Clear boundaries between concerns
- Easier to locate bugs

#### 3. **Extensibility**
- Can swap implementations (e.g., different manifest formats)
- Can add new placeholder processors without touching orchestrator
- Can add new annotation strategies

#### 4. **Reusability**
- `ManifestBuilder` can be used by other commands (e.g., `resume`)
- `PromptConfigConverter` can be used for batch operations
- `AnnotationCoordinator` can be used standalone

#### 5. **Error Handling**
- Each module can handle its own errors with context
- Easier to add retry logic at appropriate levels
- Better error messages with precise location

#### 6. **Performance**
- Can profile individual components
- Easier to optimize bottlenecks (e.g., ControlNet path resolution)
- Can parallelize independent operations

---

## Implementation Plan (REVISED 2025-11-12)

### ✅ Phase 1: Foundation (COMPLETED)
**Goal:** Create event-driven output + unified config architecture

**Completed:**
- ✅ `EventType` enum (40+ event types)
- ✅ `CLIConfig` dataclass (immutable, validated)
- ✅ `SessionConfig` dataclass (single source of truth)
- ✅ `SessionConfigBuilder` (priority resolution: CLI > Prompt > Global)
- ✅ `SessionEventCollector` (event-driven output manager)
- ✅ 23 comprehensive unit tests (100% pass rate)
- ✅ Committed: c4209fe

**Result:** Foundation ready for orchestrator integration

---

### 🚧 Phase 2: Orchestrator Base + Manifest Logic (IN PROGRESS)
**Goal:** Create orchestrator skeleton + extract manifest handling (124 lines)

**Tasks:**

1. **Update Implementation Plan** in refactoring doc
   - Document revised phases
   - Align with Phase 1 decisions

2. **Create `GenerationOrchestrator` skeleton** (`orchestrator/generation_orchestrator.py`)
   - Constructor with dependency injection
   - `orchestrate()` method signature matching `_generate()` params
   - Integration with `SessionConfigBuilder` + `SessionEventCollector`
   - Lifecycle phases as methods:
     - `_validate_template()` → emits VALIDATION_* events
     - `_load_and_resolve()` → emits TEMPLATE_* events
     - `_prepare_manifest()` → emits MANIFEST_* events
     - `_test_api_connection()` → emits API_* events
     - `_run_generation()` → emits GENERATION_* events
   - **Estimated:** 150-200 lines

3. **Create `ManifestBuilder`** (`orchestrator/manifest_builder.py`)
   - Extract runtime info fetching (lines 389-497 from `_generate()`)
   - Extract variations extraction logic
   - Extract generation params building
   - Extract API params building
   - Build complete manifest snapshot
   - Emit events via `SessionEventCollector`
   - **Estimated reduction:** 100+ lines from `_generate()`

4. **Create `ManifestManager`** (`orchestrator/manifest_manager.py`)
   - Extract manifest initialization (lines 499-510)
   - Extract incremental update callback (lines 634-679)
   - Extract finalization logic (lines 692-700)
   - Emit events via `SessionEventCollector`
   - **Estimated reduction:** 80+ lines from `_generate()`

5. **Tests for Orchestrator + Manifest modules**
   - Unit tests for `GenerationOrchestrator` (mocked dependencies)
   - Unit tests for `ManifestBuilder` methods
   - Unit tests for `ManifestManager` lifecycle
   - Integration test for full manifest flow

**After Phase 2:**
- Orchestrator skeleton functional
- Manifest logic extracted (~180 lines removed from `_generate()`)
- `_generate()` reduced to ~380 lines

---

### Phase 3: Prompt Generation & Conversion
**Goal:** Remove 75 lines of complex ControlNet/prompt logic

**Tasks:**

1. **Create `PromptConfigConverter`** (`orchestrator/prompt_config_converter.py`)
   - Extract ControlNet resolution logic (lines 558-632)
   - Extract filename generation
   - Extract PromptConfig conversion
   - Emit events via `SessionEventCollector`
   - **Estimated reduction:** 70+ lines

2. **Create `PromptGenerator`** (`orchestrator/prompt_generator.py`)
   - Extract prompt generation + stats display (lines 294-338)
   - Integrate with V2Pipeline
   - Emit PROMPT_* events
   - **Estimated reduction:** 45+ lines

3. **Tests for Prompt modules**
   - Unit tests for ControlNet image resolution
   - Unit tests for path resolution edge cases
   - Test variation enrichment
   - Test prompt statistics

**After Phase 3:** `_generate()` reduced to ~265 lines

---

### Phase 4: API Components & Annotation Worker
**Goal:** Extract API initialization and annotation coordination

**Tasks:**

1. **Create `APIComponentsFactory`** (`orchestrator/api_components_factory.py`)
   - Extract API components creation (lines 353-387)
   - SDAPIClient, SessionManager, ImageWriter, ProgressReporter, BatchGenerator
   - **Estimated reduction:** 35+ lines

2. **Create `AnnotationCoordinator`** (`orchestrator/annotation_coordinator.py`)
   - Extract worker lifecycle (lines 544-556, 702-710)
   - Worker start/stop/submit logic
   - Emit ANNOTATION_* events
   - **Estimated reduction:** 20+ lines

3. **Tests for API & Annotation modules**
   - Test component initialization
   - Test annotation worker lifecycle
   - Test dry-run mode handling

**After Phase 4:** `_generate()` reduced to ~210 lines

---

### Phase 5: Placeholder & Seed Processing
**Goal:** Extract remaining preprocessing logic

**Tasks:**

1. **Create `PlaceholderProcessor`** (`orchestrator/placeholder_processor.py`)
   - Extract fixed values logic (lines 266-292)
   - Extract seed-sweep logic
   - **Estimated reduction:** 25+ lines

2. **Tests for Processor**
   - Test fixed placeholder parsing
   - Test seed-sweep mode
   - Test edge cases

**After Phase 5:** `_generate()` reduced to ~185 lines

---

### Phase 6: Final Integration
**Goal:** Complete orchestrator + Strangler Fig migration

**Tasks:**

1. **Complete `GenerationOrchestrator` implementation**
   - Integrate all Phase 2-5 components
   - Implement full lifecycle orchestration
   - Error handling and recovery

2. **Add feature flag in `_generate()`**
   - `USE_V2_ORCHESTRATOR = os.getenv("SDGEN_USE_V2_ORCHESTRATOR", "false") == "true"`
   - Strangler Fig: if flag enabled → call orchestrator, else old code
   - All-or-nothing switch (no mixed mode)

3. **Integration Tests**
   - End-to-end test with mocked API
   - Test error recovery paths
   - Test dry-run mode
   - Test feature flag switching

4. **Migration & Cleanup**
   - Enable flag by default after validation
   - Remove old `_generate()` code
   - Update documentation

**Final State:**
- `_generate()`: ~50 lines (thin wrapper calling orchestrator)
- `GenerationOrchestrator.orchestrate()`: ~150 lines (clean workflow)
- 10+ specialized modules with clear responsibilities
- Full test coverage (>90%)

---

### Migration Strategy

**Parallel Development:**
- Keep `_generate()` working during refactoring
- Add new modules alongside existing code
- Use feature flag to switch between old/new implementations
- Gradually replace blocks in `_generate()` with module calls

**Example (Phase 1):**
```python
def _generate(...):
    try:
        # ... existing validation code ...

        # OLD CODE (commented):
        # runtime_info = {}
        # try:
        #     checkpoint = api_client.get_model_checkpoint()
        #     runtime_info = {"sd_model_checkpoint": checkpoint}
        # except ...

        # NEW CODE:
        manifest_builder = ManifestBuilder(api_client)
        runtime_info = manifest_builder.fetch_runtime_info()

        # Continue with existing code...
```

**Benefits of this approach:**
- Zero breaking changes
- Can commit incrementally
- Easy to rollback if issues arise
- Tests can be added progressively

---

### Success Metrics

- `_generate()` reduced from 562 → <100 lines
- Cyclomatic complexity reduced from ~35 → <10
- Test coverage increased to 90%+
- All new modules have CC <8
- Build tool passes all checks

---

## Appendix: Complexity Metrics

### Current Metrics (Estimated)
- **Lines of Code:** 562
- **Cyclomatic Complexity:** ~35
- **Cognitive Complexity:** ~50
- **Number of Parameters:** 13
- **Number of Local Variables:** ~40
- **Number of Nested Blocks:** 5 levels deep
- **Test Coverage:** ~60%

### Target Metrics (After Refactoring)
- **Lines of Code:** <100 (in _generate wrapper)
- **Cyclomatic Complexity:** <10
- **Cognitive Complexity:** <15
- **Number of Parameters:** 13 (unchanged - delegated to orchestrator)
- **Test Coverage:** >90%
- **Module Count:** 9 specialized modules, each <200 lines

---

## V2 Architecture Decisions (2025-11-12)

### 1. Output Management: SessionEventCollector

**Decision:** Use event-driven architecture with `SessionEventCollector` instead of Visitor Pattern or Railway Programming.

**Rationale:**
- **NOT Visitor Pattern**: Too much coupling, overhead for simple output needs
- **NOT Railway Programming**: Not idiomatic Python, poor fit for progressive output (progress bars, real-time stats)
- **✓ Event-Driven**: Natural fit for CLI output, easy to test, clean separation of concerns

**Implementation:**
```python
# sd_generator_cli/execution/session_event_collector.py
class SessionEventCollector:
    """Collects session events and produces formatted CLI output."""

    def __init__(self, console: Console, verbose: bool = False):
        self.console = console
        self.verbose = verbose

    def emit(self, event_type: EventType, data: Optional[dict[str, Any]] = None) -> None:
        """Emit a session event and handle output formatting."""
        handler = self._get_handler(event_type)
        handler(data or {})
```

**Key Benefits:**
- ✅ Single responsibility: ALL CLI output in one place
- ✅ Components are decoupled from Console (just emit events)
- ✅ Easy to test (mock SessionEventCollector)
- ✅ Extensible (add new event types without touching components)

---

### 2. Configuration Management: SessionConfig + SessionConfigBuilder

**Decision:** Build unified immutable `SessionConfig` from CLI + Template configs with centralized priority logic.

**Architecture:**
```
CLI Arguments → CLIConfig (parsed)
                    ↓
Template YAML → TemplateConfig
                    ↓
        SessionConfigBuilder.build(cli_config, template_config)
                    ↓
            SessionConfig (immutable, single source of truth)
                    ↓
            Passed to ALL components
```

**Priority Resolution (handled by SessionConfigBuilder):**
1. **CLI explicit flags** (highest priority) - `--session-name`, `--count`, `--seeds`
2. **Template YAML config** - `output.session_name`, `generation.seed_mode`
3. **Global defaults** - `sdgen_config.json`

**Key Benefits:**
- ✅ Single source of truth for entire session
- ✅ Immutable (`@dataclass(frozen=True)`) - no accidental mutations
- ✅ Priority logic centralized in builder (easy to understand/test)
- ✅ All components receive the same config reference

---

### 3. Migration Strategy: Strangler Fig Pattern

**Decision:** Route inside `_generate()` based on feature flag, NOT separate functions.

**Implementation:**
```python
def _generate(
    template_path: Path,
    global_config: GlobalConfig,
    count: Optional[int],
    api_url: str,
    dry_run: bool,
    # ... all existing params
) -> None:
    """Generate images from template (routes to old or new implementation)."""

    # Feature flag check at the START
    use_new_arch = os.getenv("SDGEN_USE_NEW_ARCH", "false").lower() == "true"

    if use_new_arch:
        # NEW V2 PATH: Orchestrator-based architecture
        console = Console()
        event_collector = SessionEventCollector(console, verbose=False)

        # Parse CLI config
        cli_config = CLIConfig(
            template_path=template_path,
            count=count,
            api_url=api_url,
            dry_run=dry_run,
            # ... all params
        )

        # Build orchestrator
        orchestrator = GenerationOrchestrator(
            global_config=global_config,
            event_collector=event_collector,
            console=console
        )

        # Execute
        orchestrator.orchestrate(cli_config)
        return  # Early return after V2 execution

    # ELSE: OLD PATH - Continue with existing 562-line implementation
    try:
        # ... existing code (lines 229-746) unchanged ...
        pass
    except Exception as e:
        # ... existing error handling ...
        pass
```

**Why this approach?**
- ✅ Keep `_generate()` signature unchanged (no breaking changes)
- ✅ Early return avoids deep nesting
- ✅ Old code path remains completely untouched
- ✅ Easy to flip between implementations for testing
- ✅ Clean removal path (delete old code when ready)

**Migration Timeline:**
1. **Development:** `SDGEN_USE_NEW_ARCH=false` (default) - old code stable
2. **Testing:** `SDGEN_USE_NEW_ARCH=true` - test new architecture
3. **Deployment:** Change default to `true` after validation
4. **Cleanup:** Remove old code + flag after stabilization period

---

### 4. Known Technical Debt (Post-Refactoring)

**STEP 4 Issue: Placeholder Processing**

**Current Design (V2):**
- `PlaceholderProcessor` applies fixed values + seed sweep AFTER template loading
- This is a temporary compromise for the refactoring

**Future Fix (Post-Refactoring):**
- Fixed placeholders and seed sweep should be handled INSIDE `V2Pipeline`
- More consistent with template resolution phase
- Requires pipeline refactoring (out of scope for this refactoring)

**Action:** Document as technical debt, fix in separate initiative after orchestrator stabilization.

---

---

## V2 Architecture Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CLI Entry Point (cli.py::generate_images)               │
│                                                                             │
│  • Parse CLI arguments (Typer)                                              │
│  • Load GlobalConfig (sdgen_config.json)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         _generate() [Strangler Fig Router]                  │
│                                                                             │
│  # Feature flag check at the START                                          │
│  use_new_arch = os.getenv("SDGEN_USE_NEW_ARCH", "false").lower() == "true" │
│                                                                             │
│  if use_new_arch:                                                           │
│      # NEW V2 PATH                                                          │
│      console = Console()                                                    │
│      event_collector = SessionEventCollector(console)                       │
│      cli_config = CLIConfig(...)                                            │
│      orchestrator = GenerationOrchestrator(...)                             │
│      orchestrator.orchestrate(cli_config)                                   │
│      return  # Early return                                                 │
│                                                                             │
│  # ELSE: OLD PATH - Continue with existing 562-line implementation          │
│  try:                                                                       │
│      # ... existing code (lines 229-746) unchanged ...                      │
│  except Exception as e:                                                     │
│      # ... existing error handling ...                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
                              [NEW V2 PATH ONLY]
╔═════════════════════════════════════════════════════════════════════════════╗
║                         GenerationOrchestrator                              ║
║                                                                             ║
║  Constructor dependencies:                                                  ║
║    • GlobalConfig                                                           ║
║    • SessionEventCollector                                                  ║
║    • Console                                                                ║
║                                                                             ║
║  Main method: orchestrate(cli_config: CLIConfig) -> None                    ║
╚═════════════════════════════════════════════════════════════════════════════╝
                                     ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 1: Configuration Building                                              │
│                                                                             │
│  CLIConfig (from args)                                                      │
│       +                                ┌──────────────────────┐             │
│  TemplateLoader.load()  ────────────→  │  TemplateConfig      │             │
│       ↓                                └──────────────────────┘             │
│  SessionConfigBuilder                            ↓                          │
│       ↓                                          ↓                          │
│  SessionConfig (immutable, single source of truth)                          │
│       ↓                                                                     │
│  event_collector.emit(SESSION_CONFIG_BUILT)                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 2: Template Validation                                                 │
│                                                                             │
│  TemplateValidator                                                          │
│       ├─→ validate_schema(template_path)                                    │
│       └─→ event_collector.emit(VALIDATION_SUCCESS/ERROR)                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 3: Template Loading & Resolution                                       │
│                                                                             │
│  V2Pipeline (existing)                                                      │
│       ├─→ load_template(session_config)                                     │
│       ├─→ resolve_inheritance()                                             │
│       ├─→ resolve_imports()                                                 │
│       └─→ ResolvedContext + ResolvedConfig                                  │
│                ↓                                                            │
│  event_collector.emit(TEMPLATE_LOADED, stats)                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 4: Context Enrichment (Fixed Placeholders + Seed Sweep)                │
│                                                                             │
│  ⚠️  TECHNICAL DEBT: Should be inside V2Pipeline (future refactoring)       │
│                                                                             │
│  PlaceholderProcessor (temporary location)                                  │
│       ├─→ apply_fixed_values(context, session_config.fixed_placeholders)    │
│       └─→ apply_seed_sweep(config, session_config.seed_list)                │
│                ↓                                                            │
│  event_collector.emit(CONTEXT_ENRICHED)                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 5: Prompt Generation + Statistics                                      │
│                                                                             │
│  PromptGenerator                                                            │
│       ├─→ generate_prompts(pipeline, context, config)                       │
│       ├─→ extract_statistics(prompts, context)                              │
│       └─→ List[dict] prompts + dict stats                                   │
│                ↓                                                            │
│  event_collector.emit(PROMPT_STATS, stats)                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 6: API Components Initialization                                       │
│                                                                             │
│  SessionConfigurator                                                        │
│       ├─→ create_session_directory(session_config.session_path)             │
│       └─→ initialize_api_components(session_config)                         │
│                ↓                                                            │
│           ┌────────────────────────────────────────┐                        │
│           │  • SDAPIClient                         │                        │
│           │  • SessionManager                      │                        │
│           │  • ImageWriter                         │                        │
│           │  • ProgressReporter                    │                        │
│           │  • BatchGenerator                      │                        │
│           └────────────────────────────────────────┘                        │
│                ↓                                                            │
│  event_collector.emit(SESSION_CREATED, session_path)                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 7: Manifest Snapshot Creation                                          │
│                                                                             │
│  ManifestBuilder(api_client, event_collector)                               │
│       ├─→ fetch_runtime_info()                                              │
│       │     └─→ emit(MANIFEST_RUNTIME_FETCH_START/SUCCESS)                  │
│       ├─→ extract_variations(context, prompts)                              │
│       ├─→ build_generation_params(session_config, stats)                    │
│       ├─→ build_api_params(prompts[0])                                      │
│       └─→ build_snapshot(session_config, runtime_info, variations, ...)     │
│                ↓                                                            │
│  ManifestManager(manifest_path, event_collector)                            │
│       └─→ initialize(snapshot)                                              │
│                ↓                                                            │
│  event_collector.emit(MANIFEST_CREATED, manifest_path)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 8: API Connection Test                                                 │
│                                                                             │
│  if not session_config.dry_run:                                             │
│      api_client.test_connection()                                           │
│      event_collector.emit(API_CONNECTION_SUCCESS)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 9: Annotation Worker Setup                                             │
│                                                                             │
│  AnnotationCoordinator(event_collector)                                     │
│       └─→ start_if_enabled(session_config)                                  │
│                ↓                                                            │
│  event_collector.emit(ANNOTATION_WORKER_START)                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 10: Prompt Conversion to PromptConfig                                  │
│                                                                             │
│  PromptConfigConverter(event_collector)                                     │
│       ├─→ convert_batch(prompts, context, session_config)                   │
│       │     └─→ _resolve_controlnet_images() for each prompt                │
│       └─→ List[PromptConfig]                                                │
│                ↓                                                            │
│  event_collector.emit(PROMPT_CONFIGS_READY, count=len(prompt_configs))      │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 11: Image Generation (Batch)                                           │
│                                                                             │
│  Create callback: _create_generation_callback()                             │
│       ├─→ Wraps ManifestManager.update_incremental()                        │
│       ├─→ Wraps AnnotationCoordinator.submit_image()                        │
│       └─→ Emits events (IMAGE_START, IMAGE_SUCCESS, IMAGE_ERROR)            │
│                                                                             │
│  BatchGenerator.generate_batch(prompt_configs, callback)                    │
│       │                                                                     │
│       └─→ For each prompt:                                                  │
│              ├─→ callback.emit(IMAGE_START, idx, prompt)                    │
│              ├─→ api_client.txt2img(prompt)                                 │
│              ├─→ image_writer.save(response)                                │
│              ├─→ manifest_manager.update_incremental(idx, response)         │
│              ├─→ annotation_coordinator.submit_image(path, variations)      │
│              └─→ callback.emit(IMAGE_SUCCESS, idx, path)                    │
│                                                                             │
│  event_collector displays progress bar + real-time stats                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 12: Finalization                                                       │
│                                                                             │
│  ManifestManager.finalize(status="completed")                               │
│       └─→ event_collector.emit(MANIFEST_FINALIZED)                          │
│                                                                             │
│  AnnotationCoordinator.stop_and_wait(worker)                                │
│       └─→ event_collector.emit(ANNOTATION_WORKER_STOPPED, pending_count)    │
│                                                                             │
│  event_collector.emit(GENERATION_COMPLETE, summary_stats)                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP 13: Error Handling (if exception)                                      │
│                                                                             │
│  except Exception as e:                                                     │
│      manifest_manager.finalize(status="aborted", error=str(e))              │
│      annotation_coordinator.stop_and_wait(worker)                           │
│      event_collector.emit(GENERATION_ABORTED, error=str(e))                 │
│      raise                                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Module Responsibilities Summary

| Module | Responsibility | Emits Events? | Uses SessionConfig? |
|--------|---------------|---------------|---------------------|
| `SessionConfigBuilder` | Build unified config | ✓ (CONFIG_BUILT) | Creates it |
| `TemplateValidator` | Validate YAML schema | ✓ (VALIDATION_*) | ✓ |
| `V2Pipeline` | Load/resolve template | No (existing) | ✓ |
| `PlaceholderProcessor` | Apply fixed values + seed sweep | ✓ (CONTEXT_ENRICHED) | ✓ |
| `PromptGenerator` | Generate prompts + stats | ✓ (PROMPT_STATS) | ✓ |
| `SessionConfigurator` | Create session dir + API components | ✓ (SESSION_CREATED) | ✓ |
| `ManifestBuilder` | Build manifest snapshot | ✓ (MANIFEST_*) | ✓ |
| `ManifestManager` | Manage manifest lifecycle | ✓ (MANIFEST_*) | ✓ |
| `AnnotationCoordinator` | Manage annotation worker | ✓ (ANNOTATION_*) | ✓ |
| `PromptConfigConverter` | Convert to PromptConfig | ✓ (CONFIGS_READY) | ✓ |
| `BatchGenerator` | Generate images (existing) | No (via callback) | Partial |
| `GenerationOrchestrator` | Orchestrate entire flow | ✓ (GENERATION_*) | Uses it |

### Data Flow Diagram

```
CLI Arguments
     ↓
┌─────────────┐
│  CLIConfig  │ (raw CLI data)
└─────────────┘
     ↓
┌──────────────────┐
│ TemplateLoader   │ → TemplateConfig
└──────────────────┘
     ↓
┌──────────────────────┐
│ SessionConfigBuilder │ → SessionConfig (immutable)
└──────────────────────┘
     ↓
     ├──→ TemplateValidator(session_config, event_collector)
     ├──→ V2Pipeline(session_config)
     ├──→ PlaceholderProcessor(session_config, event_collector)
     ├──→ PromptGenerator(session_config, event_collector)
     ├──→ SessionConfigurator(session_config, event_collector)
     ├──→ ManifestBuilder(session_config, event_collector)
     ├──→ ManifestManager(session_config, event_collector)
     ├──→ AnnotationCoordinator(session_config, event_collector)
     └──→ PromptConfigConverter(session_config, event_collector)
```

---

## Next Steps

1. **Update document** with V2 architecture flow ✓
2. **Create TODO list** for phased implementation
3. **Start Phase 1** (Core foundation):
   - `CLIConfig` dataclass
   - `SessionConfig` dataclass
   - `SessionConfigBuilder`
   - `SessionEventCollector`
   - `EventType` enum
4. **Write tests first** (TDD approach for new modules)
5. **Incremental commits** per module extraction
6. **Document** each module with usage examples
