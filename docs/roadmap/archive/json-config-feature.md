# Feature Specification: JSON Configuration System

**Status:** 🔄 In Progress (Phase 2 completed)
**Priority:** High
**Created:** 2025-10-01
**Last Updated:** 2025-10-01

## Implementation Status

| Phase | Sub-Features | Status | Tests | Completion Date |
|-------|-------------|--------|-------|-----------------|
| **Phase 1** | SF-4, SF-5 | ✅ Complete | 49 tests | 2025-10-01 |
| **Phase 2** | SF-7, SF-1 | ✅ Complete | 86 tests | 2025-10-01 |
| **Phase 3** | SF-2, SF-3 | ⏳ Next | - | - |
| **Phase 4** | SF-8, SF-6 | ⏸️ Deferred | - | - |

**Progress:** 2/3 core phases completed (66%) · 135 tests passing ✅

---

## Table of Contents

1. [Overview](#overview)
2. [Goals](#goals)
3. [Non-Goals](#non-goals)
4. [JSON Configuration Schema](#json-configuration-schema)
5. [Sub-Features](#sub-features)
6. [Technical Architecture](#technical-architecture)
7. [Implementation Plan](#implementation-plan)
8. [Future Enhancements](#future-enhancements)
9. [Success Criteria](#success-criteria)

---

## Overview

This feature introduces a **JSON-based configuration system** that allows users to define complete generation runs in declarative JSON files. Instead of writing Python scripts, users can create reusable JSON configurations and launch them via a CLI tool.

### Current State

Users create Python scripts that instantiate `ImageVariationGenerator` with all parameters:

```python
generator = ImageVariationGenerator(
    prompt_template="...",
    variation_files={...},
    seed=42,
    # ... many parameters
)
generator.run()
```

### Desired State

Users create JSON configs and run them with a simple command:

```bash
python generator_cli.py --config configs/my_generation.json
```

Or interactively:

```bash
python generator_cli.py
> Available configs:
> 1. anime_portraits.json
> 2. character_study.json
> Select config: 1
```

---

## Goals

1. **Declarative Configuration**: Define generation runs in JSON without writing code
2. **Reusability**: Save and reuse proven configurations
3. **Automation**: Enable batch processing of multiple configs
4. **Interactive Fallback**: Support interactive parameter selection via "ask" mode
5. **Enhanced Metadata**: Structured JSON metadata with all generation info
6. **Flexible Naming**: Control output folder and file naming patterns
7. **Backward Compatibility**: Keep existing `ImageVariationGenerator` API functional

---

## Non-Goals

1. ❌ GUI/Web interface for config creation (maybe future)
2. ❌ Inline variations in JSON (future enhancement)
3. ❌ Random non-combinatorial placeholders (future enhancement)
4. ❌ Relative paths for variation files (start with absolute only)
5. ❌ Config validation IDE extensions/tooling
6. ❌ Converting existing Python scripts to JSON (future tool)

---

## JSON Configuration Schema

### Complete Example

```json
{
  "version": "1.0",
  "name": "Anime Portrait Generation",
  "description": "Character portraits with various expressions and angles",

  "model": {
    "checkpoint": "animePastelDream_v1.safetensors"
  },

  "prompt": {
    "template": "masterpiece, {Expression}, {Angle}, beautiful anime girl, detailed",
    "negative": "low quality, blurry, bad anatomy, text, watermark"
  },

  "variations": {
    "Expression": "/absolute/path/to/expressions.txt",
    "Angle": "/absolute/path/to/angles.txt"
  },

  "generation": {
    "mode": "combinatorial",
    "seed_mode": "progressive",
    "seed": 42,
    "max_images": -1
  },

  "parameters": {
    "width": 512,
    "height": 768,
    "steps": 30,
    "cfg_scale": 7.0,
    "sampler": "DPM++ 2M Karras",
    "batch_size": 1,
    "batch_count": 1
  },

  "output": {
    "session_name": "anime_test_v2",
    "filename_keys": ["Expression", "Angle"]
  }
}
```

### Field Specifications

#### `version` (string, required)

Schema version for future compatibility.

- **Current:** `"1.0"`

#### `name` (string, optional)

Human-readable name for the configuration.

#### `description` (string, optional)

Description of what this config generates.

#### `model` (object, optional)

Model/checkpoint configuration.

- **`checkpoint`** (string, optional): Checkpoint filename to use
  - If not specified or not found: use current loaded checkpoint
  - Filename only, e.g., `"realisticVision_v51.safetensors"`

#### `prompt` (object, required)

Prompt configuration.

- **`template`** (string, required): Prompt with placeholders
- **`negative`** (string, optional): Negative prompt

#### `variations` (object, required)

Map of placeholder names to variation file paths.

- **Key**: Placeholder name (e.g., `"Expression"`)
- **Value**: Absolute path to variation file
- **Example:**
  ```json
  {
    "Expression": "/home/user/variations/expressions.txt",
    "Angle": "/home/user/variations/angles.txt"
  }
  ```

**Validation:**
- All placeholders in `prompt.template` must have corresponding entries
- All file paths must exist and be readable
- Paths must be absolute (relative paths not supported in v1.0)

#### `generation` (object, required)

Generation strategy configuration.

- **`mode`** (string, required): Generation mode
  - Values: `"combinatorial"`, `"random"`, `"ask"`
  - `"ask"`: Prompt user interactively at runtime

- **`seed_mode`** (string, required): Seed strategy
  - Values: `"fixed"`, `"progressive"`, `"random"`, `"ask"`
  - `"ask"`: Prompt user interactively at runtime

- **`seed`** (integer, required): Base seed value
  - `-1` has special meaning in Stable Diffusion (random)
  - Does NOT trigger ask mode; refer to `seed_mode` for that

- **`max_images`** (integer, required): Maximum images to generate
  - `-1`: Ask user interactively
  - Any positive integer: Use that value
  - Only applies to `"random"` generation mode

#### `parameters` (object, required)

Stable Diffusion generation parameters.

- **`width`** (integer, required): Image width in pixels
  - `-1`: Ask user interactively

- **`height`** (integer, required): Image height in pixels
  - `-1`: Ask user interactively

- **`steps`** (integer, required): Number of sampling steps
  - `-1`: Ask user interactively

- **`cfg_scale`** (float, required): Classifier-free guidance scale
  - `-1.0`: Ask user interactively

- **`sampler`** (string, required): Sampler name
  - `"ask"`: Prompt user to select from available samplers
  - Any valid sampler name: Use that sampler
  - **Validation:** If not "ask", verify sampler exists in SD API

- **`batch_size`** (integer, required): Batch size (images per API call)
  - `-1`: Ask user interactively

- **`batch_count`** (integer, required): Number of batches per generation
  - `-1`: Ask user interactively

#### `output` (object, required)

Output configuration.

- **`session_name`** (string, optional): Custom session folder name
  - If present: Folder named `{timestamp}_{session_name}/`
  - If absent: Folder named `{timestamp}_{key1}_{key2}...` using `filename_keys`
  - Example: `20251001_143052_anime_test_v2/`

- **`filename_keys`** (array of strings, optional): Variation keys to include in filenames
  - Keys must exist in `variations` object
  - Order in array determines order in filename
  - **Format:** `{index}_{key1}-{value1}_{key2}-{value2}.png`
  - **Example:** `["Angle", "Expression"]` → `001_Angle-Front_Expression-Smiling.png`
  - If empty or absent: Files named `{index}.png` only

---

## Sub-Features

### SF-4: Enhanced File Naming System 🔥

**Priority:** 1 (Highest)
**Complexity:** Medium
**Dependencies:** None

#### Description

Implement intelligent file and folder naming based on configuration.

#### Requirements

1. **Session Folder Naming:**
   - Format: `{timestamp}_{name_components}`
   - If `session_name` provided: `20251001_143052_anime_test_v2`
   - If no `session_name`: `20251001_143052_Expression_Angle` (from `filename_keys`)
   - Timestamp format: `YYYYMMDD_HHMMSS`

2. **Image File Naming:**
   - Base format: `{index:03d}.png` (e.g., `001.png`)
   - With `filename_keys`: `{index:03d}_{key1}-{value1}_{key2}-{value2}.png`
   - Example: `001_Angle-Front_Expression-Smiling.png`
   - Values sanitized (no spaces, special chars replaced with `-`)

3. **Metadata File Naming:**
   - Always: `metadata.json` in session folder

#### Tasks

- [ ] **SF-4.1:** Create `output_namer.py` module
  - [ ] Function `generate_session_folder_name(timestamp, session_name, filename_keys, variations_sample)`
  - [ ] Function `generate_image_filename(index, variation_dict, filename_keys)`
  - [ ] Function `sanitize_filename_component(value)` (remove special chars)

- [ ] **SF-4.2:** Add tests for naming functions
  - [ ] Test session naming with/without `session_name`
  - [ ] Test filename generation with various combinations
  - [ ] Test special character sanitization
  - [ ] Test edge cases (empty keys, long names)

- [ ] **SF-4.3:** Update `ImageVariationGenerator` to support new naming
  - [ ] Add `filename_keys` parameter to constructor
  - [ ] Modify image save logic to use new naming
  - [ ] Ensure backward compatibility (default to index-only naming)

#### Success Criteria

- ✅ Session folders correctly named based on config
- ✅ Image files include variation values when `filename_keys` specified
- ✅ All filenames are filesystem-safe (no special chars)
- ✅ Backward compatibility: existing code works without `filename_keys`

---

### SF-5: JSON Metadata Export 🔥

**Priority:** 2
**Complexity:** Low
**Dependencies:** None

#### Description

Replace text-based `session_config.txt` with structured `metadata.json`.

#### Requirements

1. **Output Format:**
   - Pretty-printed JSON (2-space indent)
   - UTF-8 encoding
   - Filename: `metadata.json` in session folder

2. **Content Structure:**
   ```json
   {
     "version": "1.0",
     "generation_info": {
       "date": "2025-10-01T14:30:52",
       "timestamp": "20251001_143052",
       "session_name": "anime_test_v2",
       "total_images": 150,
       "generation_time_seconds": 450.23
     },
     "model": {
       "checkpoint": "animePastelDream_v1.safetensors"
     },
     "prompt": {
       "template": "masterpiece, {Expression}, {Angle}, beautiful",
       "negative": "low quality, blurry",
       "example_resolved": "masterpiece, smiling, front view, beautiful"
     },
     "variations": {
       "Expression": {
         "source_file": "/path/to/expressions.txt",
         "count": 10,
         "values": ["smiling", "sad", "angry", "..."]
       },
       "Angle": {
         "source_file": "/path/to/angles.txt",
         "count": 5,
         "values": ["front view", "side view", "..."]
       }
     },
     "generation": {
       "mode": "combinatorial",
       "seed_mode": "progressive",
       "seed": 42,
       "total_combinations": 50,
       "images_generated": 50
     },
     "parameters": {
       "width": 512,
       "height": 768,
       "steps": 30,
       "cfg_scale": 7.0,
       "sampler": "DPM++ 2M Karras",
       "batch_size": 1,
       "batch_count": 1
     },
     "output": {
       "folder": "/path/to/outputs/20251001_143052_anime_test_v2",
       "filename_keys": ["Expression", "Angle"]
     },
     "config_source": "/path/to/configs/anime_portraits.json"
   }
   ```

3. **Backward Compatibility:**
   - Keep generating `session_config.txt` for now (deprecated)
   - Add deprecation notice in text file pointing to JSON

#### Tasks

- [ ] **SF-5.1:** Create `metadata_generator.py` module
  - [ ] Function `generate_metadata_dict(config, runtime_info, variations_loaded)`
  - [ ] Function `save_metadata_json(metadata_dict, output_folder)`
  - [ ] Function `load_metadata_json(output_folder)` (for future use)

- [ ] **SF-5.2:** Update `ImageVariationGenerator` to export JSON metadata
  - [ ] Collect metadata during run
  - [ ] Call `save_metadata_json()` after generation complete
  - [ ] Keep legacy `session_config.txt` with deprecation notice

- [ ] **SF-5.3:** Add tests for metadata generation
  - [ ] Test metadata structure completeness
  - [ ] Test JSON validity and formatting
  - [ ] Test loading previously saved metadata

#### Success Criteria

- ✅ `metadata.json` generated for every session
- ✅ JSON is valid and pretty-printed
- ✅ Contains all required information
- ✅ Legacy text file still generated (deprecated)

---

### SF-1: JSON Config Loading & Validation 🔥

**Priority:** 3
**Complexity:** High
**Dependencies:** None

#### Description

Load and validate JSON configuration files with clear error messages.

#### Requirements

1. **Schema Validation:**
   - Validate required fields
   - Validate field types (string, int, float, object, array)
   - Validate enum values (mode, seed_mode)
   - Validate file paths exist

2. **Error Messages:**
   - Clear, actionable error messages
   - Show field path (e.g., `variations.Expression: file not found`)
   - Suggest fixes when possible

3. **Placeholder Validation:**
   - Extract placeholders from `prompt.template`
   - Verify all have corresponding entries in `variations`
   - Warn if `variations` has unused entries

4. **Parameter Validation:**
   - If `sampler` not "ask", verify it exists in SD API
   - Validate numeric ranges (e.g., width > 0 if not -1)

#### Tasks

- [ ] **SF-1.1:** Create `config_schema.py` module
  - [ ] Define `GenerationConfig` dataclass/Pydantic model
  - [ ] Implement validation logic
  - [ ] Implement error message generation

- [ ] **SF-1.2:** Create `config_loader.py` module
  - [ ] Function `load_config_from_file(path) -> GenerationConfig`
  - [ ] Function `validate_config(config) -> List[ValidationError]`
  - [ ] Function `validate_variation_files(variations) -> List[ValidationError]`
  - [ ] Function `validate_placeholders_match(prompt, variations) -> List[ValidationError]`

- [ ] **SF-1.3:** Create validation utilities
  - [ ] Extract placeholders from prompt template (reuse existing logic)
  - [ ] Check file existence
  - [ ] Check sampler availability (query SD API)

- [ ] **SF-1.4:** Comprehensive tests
  - [ ] Test valid configs load successfully
  - [ ] Test invalid configs fail with clear messages
  - [ ] Test missing files detection
  - [ ] Test placeholder mismatch detection
  - [ ] Test invalid enum values

#### Success Criteria

- ✅ Valid configs load without errors
- ✅ Invalid configs fail fast with clear messages
- ✅ All file paths validated before generation starts
- ✅ Placeholder/variation mismatches detected
- ✅ 100% test coverage on validation logic

---

### SF-2: Interactive Config Selection 🔥

**Priority:** 4
**Complexity:** Low
**Dependencies:** SF-7 (Config file for paths)

#### Description

CLI tool to list and select JSON configs interactively or via argument.

#### Requirements

1. **Config Discovery:**
   - Read `configs_dir` from global config file
   - List all `.json` files in that directory
   - Display with numbers for selection

2. **Interactive Selection:**
   - Show list of configs with names/descriptions
   - Allow numeric selection
   - Validate selection

3. **Direct Path Support:**
   - `--config path/to/config.json` bypasses selection
   - Validate file exists

4. **Display Format:**
   ```
   Available configurations:

   1. anime_portraits.json
      Anime Portrait Generation
      Character portraits with various expressions and angles

   2. landscape_variations.json
      Landscape Scene Generation
      Nature scenes with different weather and lighting

   3. character_study.json
      Character Study - Multiple Outfits
      Full character sheet with outfit variations

   Select configuration (1-3): _
   ```

#### Tasks

- [ ] **SF-2.1:** Create `config_selector.py` module
  - [ ] Function `discover_configs(configs_dir) -> List[ConfigInfo]`
  - [ ] Function `display_config_list(configs)`
  - [ ] Function `prompt_user_selection(configs) -> Path`
  - [ ] Function `validate_config_selection(selection, max_num)`

- [ ] **SF-2.2:** Extract name/description from JSON for display
  - [ ] Parse JSON metadata without full validation
  - [ ] Graceful handling if metadata missing

- [ ] **SF-2.3:** Add tests for config selection
  - [ ] Test config discovery in directory
  - [ ] Test display formatting
  - [ ] Mock user input for selection tests

#### Success Criteria

- ✅ Lists all JSON files in configs directory
- ✅ Displays name and description if present
- ✅ Validates user selection
- ✅ Supports direct path via CLI argument

---

### SF-3: JSON-Driven Generation 🔥

**Priority:** 5
**Complexity:** Medium
**Dependencies:** SF-1, SF-4, SF-5

#### Description

Execute generation runs from JSON config, handling interactive parameters.

#### Requirements

1. **Config Translation:**
   - Convert `GenerationConfig` to `ImageVariationGenerator` parameters
   - Handle "ask" and `-1` values by prompting user

2. **Interactive Prompts:**
   - If `generation.mode == "ask"`: prompt for mode
   - If `generation.seed_mode == "ask"`: prompt for seed mode
   - If `generation.max_images == -1`: prompt for number
   - If `parameters.sampler == "ask"`: show available samplers, prompt
   - For any numeric parameter `-1`: prompt for value

3. **Prompt Format:**
   ```
   Generation mode not specified in config.
   Available modes:
     1. combinatorial - Generate all possible combinations
     2. random - Generate random unique combinations

   Select mode (1-2): _
   ```

4. **Execution:**
   - Load variation files
   - Instantiate `ImageVariationGenerator` with resolved parameters
   - Call `run()` and capture result
   - Handle errors gracefully

#### Tasks

- [ ] **SF-3.1:** Create `json_generator.py` module
  - [ ] Function `resolve_interactive_params(config) -> ResolvedConfig`
  - [ ] Function `prompt_generation_mode() -> str`
  - [ ] Function `prompt_seed_mode() -> str`
  - [ ] Function `prompt_max_images(total_combinations) -> int`
  - [ ] Function `prompt_sampler(available_samplers) -> str`
  - [ ] Function `prompt_numeric_param(param_name, default) -> int/float`

- [ ] **SF-3.2:** Integrate with `ImageVariationGenerator`
  - [ ] Function `create_generator_from_config(resolved_config) -> ImageVariationGenerator`
  - [ ] Map JSON fields to constructor parameters
  - [ ] Handle new parameters (`filename_keys`)

- [ ] **SF-3.3:** Create main execution flow
  - [ ] Function `run_generation_from_config(config_path)`
  - [ ] Load → Validate → Resolve → Generate → Report
  - [ ] Error handling at each stage

- [ ] **SF-3.4:** Add tests
  - [ ] Test config-to-generator translation
  - [ ] Test interactive prompt functions (mocked input)
  - [ ] Test end-to-end with sample configs
  - [ ] Test error handling

#### Success Criteria

- ✅ Valid configs execute without errors
- ✅ Interactive prompts appear for "ask" parameters
- ✅ Generation completes successfully
- ✅ Files named according to `filename_keys`
- ✅ Metadata JSON generated

---

### SF-7: Global Config File 🔥

**Priority:** 6
**Complexity:** Low
**Dependencies:** None

#### Description

Global configuration file to specify configs and outputs directories.

#### Requirements

1. **File Location:**
   - Path: `.sdgen_config.json` at project root
   - Alternative: `~/.sdgen_config.json` (user home)
   - Search order: Project root → User home → Defaults

2. **Schema:**
   ```json
   {
     "configs_dir": "/absolute/path/to/configs",
     "output_dir": "/absolute/path/to/outputs",
     "api_url": "http://127.0.0.1:7860"
   }
   ```

3. **Defaults:**
   - `configs_dir`: `./configs`
   - `output_dir`: `./apioutput`
   - `api_url`: `http://127.0.0.1:7860`

4. **Creation:**
   - If not found, create with defaults on first run
   - Prompt user to confirm or edit

#### Tasks

- [ ] **SF-7.1:** Create `global_config.py` module
  - [ ] Function `locate_global_config() -> Path | None`
  - [ ] Function `load_global_config() -> GlobalConfig`
  - [ ] Function `create_default_global_config(path)`
  - [ ] Function `prompt_user_for_paths() -> (configs_dir, output_dir)`

- [ ] **SF-7.2:** Integrate into CLI
  - [ ] Load global config on startup
  - [ ] Use paths from global config
  - [ ] Create if missing (with user confirmation)

- [ ] **SF-7.3:** Add tests
  - [ ] Test file discovery logic
  - [ ] Test defaults loading
  - [ ] Test config creation

#### Success Criteria

- ✅ Global config file located and loaded
- ✅ Defaults used if not found
- ✅ Created automatically with user confirmation
- ✅ Used by CLI for paths

---

### SF-8: Script-to-JSON Conversion Tool ⏳

**Priority:** 7 (Future)
**Complexity:** High
**Dependencies:** SF-1, SF-3

#### Description

Tool to convert existing Python generator scripts to JSON configs.

**Status:** Deferred to future iteration. Not in initial release.

#### Requirements

- Parse Python script to extract parameters
- Generate equivalent JSON config
- Handle cases where script has custom logic (manual intervention needed)

---

### SF-6: Checkpoint Manager 🔮

**Priority:** 8 (Future)
**Complexity:** High
**Dependencies:** SF-3

#### Description

Automatically load specified checkpoint before generation.

**Status:** Deferred to later phase. Use current loaded checkpoint initially.

#### Requirements

1. **API Approach:**
   - GET `/sdapi/v1/sd-models` to list available checkpoints
   - GET `/sdapi/v1/options` to get current checkpoint
   - POST `/sdapi/v1/options` with `{"sd_model_checkpoint": "name.safetensors"}` to change
   - Wait for model load completion

2. **Playwright Fallback:**
   - If API fails, use browser automation
   - Navigate to SD WebUI
   - Select checkpoint from dropdown
   - Wait for load confirmation

3. **Validation:**
   - Check if specified checkpoint exists
   - If not found: warn and use current
   - If found but different: change and wait
   - If already loaded: skip

#### Tasks

- [ ] **SF-6.1:** Create `checkpoint_manager.py` module
  - [ ] Function `get_available_checkpoints() -> List[str]`
  - [ ] Function `get_current_checkpoint() -> str`
  - [ ] Function `set_checkpoint_api(checkpoint_name) -> bool`
  - [ ] Function `set_checkpoint_playwright(checkpoint_name) -> bool`
  - [ ] Function `ensure_checkpoint_loaded(checkpoint_name) -> str` (returns actual loaded)

- [ ] **SF-6.2:** Integrate into generation flow
  - [ ] Check `model.checkpoint` in config
  - [ ] Call `ensure_checkpoint_loaded()` before generation
  - [ ] Record actual loaded checkpoint in metadata

- [ ] **SF-6.3:** Add tests
  - [ ] Test API checkpoint change
  - [ ] Test Playwright fallback
  - [ ] Test handling of missing checkpoints

#### Success Criteria

- ✅ Checkpoint changed via API when specified
- ✅ Falls back to Playwright if API fails
- ✅ Actual loaded checkpoint recorded in metadata
- ✅ Graceful handling of missing checkpoints

---

## Technical Architecture

### Module Structure

```
CLI/
├── generator_cli.py          # Main entry point (NEW)
├── image_variation_generator.py  # Existing, updated
├── variation_loader.py       # Existing
├── sdapi_client.py          # Existing
│
├── config/                   # NEW module
│   ├── __init__.py
│   ├── config_schema.py     # SF-1: JSON schema & validation
│   ├── config_loader.py     # SF-1: Load & validate JSON
│   ├── config_selector.py   # SF-2: Interactive selection
│   └── global_config.py     # SF-7: Global config file
│
├── output/                   # NEW module
│   ├── __init__.py
│   ├── output_namer.py      # SF-4: File/folder naming
│   └── metadata_generator.py # SF-5: JSON metadata export
│
├── execution/                # NEW module
│   ├── __init__.py
│   └── json_generator.py    # SF-3: JSON-driven generation
│
└── checkpoint/               # FUTURE module
    ├── __init__.py
    └── checkpoint_manager.py # SF-6: Checkpoint switching
```

### Data Flow

```
1. User runs CLI
   ↓
2. Load global config (.sdgen_config.json)
   ↓
3. Discover & select JSON config
   ↓
4. Load & validate config (SF-1)
   ↓
5. Resolve interactive parameters (SF-3)
   ↓
6. [FUTURE] Load checkpoint if specified (SF-6)
   ↓
7. Load variation files
   ↓
8. Create ImageVariationGenerator with:
   - Resolved parameters
   - filename_keys for naming (SF-4)
   ↓
9. Run generation
   ↓
10. Save images with enhanced naming (SF-4)
    ↓
11. Export JSON metadata (SF-5)
    ↓
12. Report results
```

### Backward Compatibility Strategy

**Existing API preserved:**
```python
# This continues to work unchanged
generator = ImageVariationGenerator(
    prompt_template="...",
    variation_files={...},
    seed=42
)
generator.run()
```

**New functionality added via optional parameters:**
```python
generator = ImageVariationGenerator(
    prompt_template="...",
    variation_files={...},
    seed=42,
    filename_keys=["Expression", "Angle"]  # NEW, optional
)
```

**Internal refactoring:**
- Extract naming logic into `output_namer.py`
- Extract metadata logic into `metadata_generator.py`
- `ImageVariationGenerator` calls these modules
- Existing scripts see no changes in behavior

---

## Implementation Plan

### Phase 1: Foundation (SF-4, SF-5) ✅ COMPLETED

**Goal:** Implement core output improvements that work with existing system.

**Status:** ✅ Completed 2025-10-01

**Order:**
1. ✅ SF-4: Enhanced File Naming System
2. ✅ SF-5: JSON Metadata Export

**Deliverable:** Existing scripts can use new naming and get JSON metadata.

**Implementation:**
- `CLI/output/output_namer.py` - Filename generation with camelCase sanitization
- `CLI/output/metadata_generator.py` - JSON metadata with backward compatibility
- `filename_keys` parameter in `ImageVariationGenerator`
- 49 tests (27 + 22) all passing ✅

**Testing:**
- ✅ Update one existing generator to use `filename_keys`
- ✅ Verify new naming and metadata work
- ✅ Confirm backward compatibility
- ✅ Demo script: `CLI/example_new_features_sf4_sf5.py`

**Commits:**
- feat(output): Add SF-4 Enhanced File Naming System
- feat(output): Add SF-5 JSON Metadata Export

---

### Phase 2: Configuration System (SF-1, SF-7) ✅ COMPLETED

**Goal:** Load and validate JSON configs.

**Status:** ✅ Completed 2025-10-01

**Order:**
1. ✅ SF-7: Global Config File
2. ✅ SF-1: JSON Config Loading & Validation

**Deliverable:** Can load and validate JSON configs, but not yet execute them.

**Implementation:**
- `CLI/config/global_config.py` - Global config system (.sdgen_config.json)
- `CLI/config/config_schema.py` - Config dataclasses with validation
- `CLI/config/config_loader.py` - JSON loading & comprehensive validation
- 86 tests (26 + 29 + 31) all passing ✅

**Testing:**
- ✅ Create sample JSON configs (`configs/test_config_phase2.json`)
- ✅ Verify validation catches errors with clear messages
- ✅ Test global config creation and loading
- ✅ Integration tests: `CLI/test_integration_phase2.py`
- ✅ Test variation files created

**Commits:**
- feat(config): Add Phase 2 - SF-7 Global Config & SF-1 Config Loading/Validation

**Duration:** Completed in 1 day

---

### Phase 3: Execution (SF-2, SF-3) 🔄 IN PROGRESS

**Goal:** Execute generation from JSON configs.

**Status:** 🔄 Next phase (not started)

**Order:**
1. ⏳ SF-2: Interactive Config Selection (Priority 4)
2. ⏳ SF-3: JSON-Driven Generation (Priority 5)

**Deliverable:** Full JSON config system working end-to-end.

**To Implement:**
- `CLI/config/config_selector.py` - Interactive config selection
- `CLI/execution/json_generator.py` - JSON-to-generator translation
- `CLI/generator_cli.py` - Main CLI entry point
- Interactive prompts for "ask" parameters
- End-to-end execution tests

**Testing:**
- Run generations from JSON configs
- Test interactive parameter prompts
- Verify all features work together

**Estimated Duration:** ~2-3 days

---

### Phase 4: Future Enhancements (SF-8, SF-6) ⏸️ DEFERRED

**Goal:** Advanced features for convenience and automation.

**Status:** ⏸️ Deferred to future iteration

**Order:**
1. ⏸️ SF-8: Script-to-JSON Conversion Tool (Priority 7 - Future)
2. ⏸️ SF-6: Checkpoint Manager (Priority 8 - Future)

**Deliverable:** Complete automation of generation pipeline.

**Duration:** ~4-5 days

---

### Progress Summary

**✅ Completed:**
- Phase 1: Foundation (SF-4, SF-5) - 49 tests
- Phase 2: Configuration (SF-1, SF-7) - 86 tests
- **Total: 135 tests passing** ✅

**🔄 Next:**
- Phase 3: Execution (SF-2, SF-3)

**⏸️ Future:**
- Phase 4: Enhancements (SF-8, SF-6)

---

### Duration Tracking

- **Phase 1:** ✅ 1 day (completed 2025-10-01)
- **Phase 2:** ✅ 1 day (completed 2025-10-01)
- **Phase 3:** ⏳ Estimated 2-3 days
- **Phase 4:** ⏸️ 4-5 days (deferred)

**Core Feature Progress (Phases 1-3):** 2/3 phases completed (66%)
**Estimated Remaining:** 2-3 days for Phase 3

---

## Future Enhancements

### Inline Variations

Allow defining variations directly in JSON instead of external files:

```json
"variations": {
  "Expression": ["smiling", "sad", "angry"],
  "Angle": "/path/to/angles.txt"
}
```

### Random Non-Combinatorial Placeholders

Mark certain placeholders as "random per combination":

```json
"variations": {
  "Expression": "/path/to/expressions.txt",
  "Background": {
    "file": "/path/to/backgrounds.txt",
    "mode": "random_per_combination"
  }
}
```

For each combination of other placeholders, randomly pick a different background.

### Config Templates

Partial configs that can be extended:

```json
{
  "extends": "base_anime_config.json",
  "prompt": {
    "template": "..."
  }
}
```

### Variable Substitution

Use variables in prompts and paths:

```json
{
  "variables": {
    "character": "emma_watson",
    "base_path": "/home/user/variations"
  },
  "prompt": {
    "template": "portrait of ${character}, {Expression}"
  },
  "variations": {
    "Expression": "${base_path}/expressions.txt"
  }
}
```

### Batch Processing

Run multiple configs in sequence:

```bash
python generator_cli.py --batch batch_run.json
```

Where `batch_run.json` lists configs to run.

---

## Success Criteria

### Functional Requirements

- ✅ JSON configs can be created manually
- ✅ CLI loads configs via path or interactive selection
- ✅ All validation errors shown clearly before generation starts
- ✅ Interactive prompts work for "ask" parameters
- ✅ Files and folders named according to config
- ✅ JSON metadata generated for every run
- ✅ Existing Python scripts continue to work unchanged

### Quality Requirements

- ✅ Comprehensive test coverage (>80%)
- ✅ Clear error messages for all failure cases
- ✅ Documentation updated with JSON config examples
- ✅ Sample configs provided in `configs/examples/`

### Performance Requirements

- ✅ Config loading < 100ms for typical configs
- ✅ Validation < 500ms (including file checks)
- ✅ No performance regression in generation itself

### User Experience Requirements

- ✅ JSON configs easy to write manually
- ✅ Interactive selection intuitive
- ✅ Error messages actionable
- ✅ Smooth migration path from Python scripts

---

## Risk Analysis

### High Risk

**Risk:** JSON schema too rigid, frustrates users
**Mitigation:** Start with flexible schema, add strict validation gradually

**Risk:** Breaking changes to existing scripts
**Mitigation:** Maintain strict backward compatibility, comprehensive tests

### Medium Risk

**Risk:** File path handling across platforms (Windows/Linux)
**Mitigation:** Use absolute paths only initially, test on both platforms

**Risk:** Interactive prompts in non-TTY environments
**Mitigation:** Detect TTY, fall back to defaults or error with message

### Low Risk

**Risk:** JSON config files become verbose
**Mitigation:** Add defaults, optional fields, templates in future

**Risk:** Checkpoint switching breaks generation
**Mitigation:** Make it optional (Phase 4), validate before attempting

---

## Open Questions

1. **Should we support JSON5 for comments in configs?**
   → Decision: No, keep standard JSON for now. Use `description` fields.

2. **Should validation be strict or lenient (extra fields)?**
   → Decision: Lenient (ignore extra fields), allows forward compatibility.

3. **Should global config be in user home or project root?**
   → Decision: Support both, search order: project → home.

4. **Should we validate all variation files have content?**
   → Decision: Yes, fail if any file is empty or unreadable.

5. **How to handle very long variation file lists in metadata?**
   → Decision: Include count + first 10 values, with truncation indicator.

---

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2025-10-01 | Claude | Initial specification created |

---

**Next Steps:**

1. Review this specification with stakeholders
2. Create sample JSON configs for testing
3. Begin implementation Phase 1 (SF-4, SF-5)
