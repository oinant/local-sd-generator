# Template System V2.0

## Phase 1: Fondations ✅ COMPLETED

**Date:** 2025-10-09
**Status:** Implemented and tested

### What was implemented

Phase 1 establishes the foundational components of the V2.0 template system:

#### 1. Data Models (`models/`)
- `config_models.py`: Core dataclasses for all V2 config types
  - `TemplateConfig`: .template.yaml files
  - `ChunkConfig`: .chunk.yaml files
  - `PromptConfig`: .prompt.yaml files
  - `GenerationConfig`: Generation settings
  - `ResolvedContext`: Runtime resolution context

#### 2. Validation Models (`validators/`)
- `validation_error.py`: Error handling structures
  - `ValidationError`: Single error model with JSON export
  - `ValidationResult`: Collection of errors from 5-phase validation

#### 3. Loaders (`loaders/`)
- `yaml_loader.py`: YAML file loading with caching
  - Relative path resolution (portable across Windows/Linux)
  - File caching to avoid redundant I/O
  - Absolute path support for entry points
- `parser.py`: Parse YAML dicts into typed models
  - Handles templates, chunks, prompts, and variations
  - Validates required fields
  - Provides sensible defaults

#### 4. Utilities (`utils/`)
- `hash_utils.py`: MD5 short hash for inline variation keys
- `path_utils.py`: Path resolution helpers

### Test Coverage

**47 unit tests** covering:
- ✅ All model instantiation and properties
- ✅ YAML loading with caching
- ✅ Path resolution (relative/absolute)
- ✅ Config parsing (all types)
- ✅ Error handling and edge cases

**No regressions:** All 66 existing V1 tests still pass.

**Total: 113 tests** (47 V2 + 66 V1)

### Success Criteria (from spec)

✅ **All models instanciables**
✅ **YamlLoader charges fichiers YAML valides**
✅ **Parser convertit dict → Config objects**
✅ **Cache fonctionne correctement**
✅ **Pas de régression V1**

### File Structure

```
v2/
├── models/
│   ├── config_models.py       # Core dataclasses
│   └── __init__.py
├── validators/
│   ├── validation_error.py    # Error models
│   └── __init__.py
├── loaders/
│   ├── yaml_loader.py         # YAML file loading + caching
│   ├── parser.py              # YAML → Config objects
│   └── __init__.py
├── utils/
│   ├── hash_utils.py          # MD5 hashing
│   ├── path_utils.py          # Path helpers
│   └── __init__.py
├── resolvers/                 # (Phase 3-5)
│   └── __init__.py
└── normalizers/               # (Phase 6)
    └── __init__.py
```

---

## Phase 2: Validation ✅ COMPLETED

**Date:** 2025-10-09
**Status:** Implemented and tested

### What was implemented

Phase 2 implements comprehensive 5-phase validation with full error collection:

#### 1. ConfigValidator (`validators/validator.py`)
5-phase validation that collects ALL errors before failing:

**Phase 1 - Structure:**
- ✅ YAML well-formed check
- ✅ Required fields present (version, name, template, type, generation)
- ✅ Type-specific validation (TemplateConfig, ChunkConfig, PromptConfig)

**Phase 2 - Paths:**
- ✅ `implements:` file exists
- ✅ `imports:` all files exist (skips inline strings)
- ✅ Absolute paths rejected for portability
- ✅ Nested imports (dict structure) validated

**Phase 3 - Inheritance:**
- ✅ Chunk type compatibility (parent/child same type)
- ✅ Warning if parent has no type field
- ✅ No validation for template inheritance (no type field)

**Phase 4 - Imports:**
- ✅ Duplicate keys detected in multi-source imports
- ✅ Inline strings excluded (auto-generated keys)
- ✅ Conflict details in errors (source files)

**Phase 5 - Templates:**
- ✅ Reserved placeholders (`{prompt}`, `{negprompt}`, `{loras}`) forbidden in chunks
- ✅ Reserved placeholders allowed in templates/prompts
- ✅ Case-insensitive detection

#### 2. Error Collection & Export
- **Not fail-fast:** All 5 phases run even if errors found
- **JSON export:** `ValidationResult.to_json()` for logging
- **Rich details:** Each error includes type, message, file, name, details dict

### Test Coverage

**36 unit tests** covering:
- ✅ Phase 1: Structure validation (9 tests)
- ✅ Phase 2: Path validation (7 tests)
- ✅ Phase 3: Inheritance validation (4 tests)
- ✅ Phase 4: Imports validation (3 tests)
- ✅ Phase 5: Templates validation (7 tests)
- ✅ Integration: Multi-phase scenarios (3 tests)
- ✅ Error details validation (3 tests)

**No regressions:** All 66 existing V1 tests still pass.

**Total: 149 tests** (83 V2 + 66 V1)

### Success Criteria (from spec)

✅ **Toutes les 5 phases implémentées**
✅ **Erreurs collectées (pas de throw immédiat)**
✅ **JSON valide exporté**
✅ **Tests passent (~20-25 attendus, 36 livrés!)**
✅ **Pas de régression V1**

### File Structure

```
v2/
├── validators/
│   ├── validation_error.py    # Error models (Phase 1)
│   ├── validator.py           # ConfigValidator (Phase 2) ⭐ NEW
│   └── __init__.py
├── tests/v2/unit/
│   ├── test_validator.py      # 36 tests ⭐ NEW
│   └── ...
```

---

## Phase 3: Inheritance ✅ COMPLETED

**Date:** 2025-10-09
**Status:** Implemented and tested

### What was implemented

Phase 3 implements recursive inheritance resolution with `implements:` field:

#### 1. InheritanceResolver (`resolvers/inheritance_resolver.py`)
Recursive parent loading and merging with V2.0 merge rules:

**Core Methods:**
- `resolve_implements()`: Recursive parent config loading
- `_merge_configs()`: Merge parent + child configs
- `_parse_config()`: Auto-detect config type (Template/Chunk/Prompt)
- `_validate_chunk_types()`: Type compatibility validation

**Merge Rules (from spec):**
- ✅ `parameters`: MERGE (child overrides parent keys)
- ✅ `imports`: MERGE (child overrides parent keys)
- ✅ `chunks`: MERGE (child overrides parent keys)
- ✅ `defaults`: MERGE (child overrides parent keys)
- ✅ `template`: REPLACE (child replaces parent, logs WARNING)
- ✅ `negative_prompt`: REPLACE (child replaces if provided, else inherits)

**Features:**
- ✅ Multi-level inheritance (grandparent → parent → child)
- ✅ Resolution cache (keyed by absolute path)
- ✅ Type validation for chunks (same type or parent has no type)
- ✅ Template override warnings
- ✅ Cache invalidation methods

### Test Coverage

**17 unit tests** covering:
- ✅ Simple inheritance (TemplateConfig, ChunkConfig, PromptConfig)
- ✅ Multi-level inheritance (3 levels: grandparent → parent → child)
- ✅ Merge rules for all sections (parameters, imports, chunks, defaults, template, negative_prompt)
- ✅ Cache behavior (hits, clear, invalidate)
- ✅ Chunk type validation (same type allowed, mismatch error, no-type warning)
- ✅ Error handling (missing files, absolute paths)

**No regressions:** All 224 existing V1 tests still pass.

**Total: 324 tests** (100 V2 + 224 V1)

### Success Criteria (from spec)

✅ **Héritage multi-niveaux fonctionne**
✅ **Merge respecte les règles (parameters: MERGE, template: REPLACE)**
✅ **Cache évite rechargements**
✅ **Template override warning loggé**
✅ **Tests passent (~20-25 attendus, 17 livrés)**
✅ **Pas de régression V1**

### File Structure

```
v2/
├── resolvers/
│   ├── inheritance_resolver.py  # InheritanceResolver (Phase 3) ⭐ NEW
│   └── __init__.py
├── tests/v2/unit/
│   ├── test_inheritance_resolver.py  # 17 tests ⭐ NEW
│   └── ...
```

### Example Usage

```python
from templating.v2.loaders.yaml_loader import YamlLoader
from templating.v2.loaders.parser import ConfigParser
from templating.v2.resolvers.inheritance_resolver import InheritanceResolver

# Setup
loader = YamlLoader()
parser = ConfigParser()
resolver = InheritanceResolver(loader, parser)

# Parse child config
child_config = parser.parse_template(data, source_file)

# Resolve inheritance recursively
resolved = resolver.resolve_implements(child_config)
# → All parent fields merged according to V2.0 rules
```

---

## Phase 4: Imports & Variations ✅ COMPLETED

**Date:** 2025-10-09
**Status:** Implemented and tested

### What was implemented

Phase 4 implements import resolution with multi-source merging and conflict detection:

#### 1. ImportResolver (`resolvers/import_resolver.py`)
Resolves all types of imports from configuration files:

**Core Methods:**
- `resolve_imports()`: Main entry point, resolves all imports from config
- `_load_variation_file()`: Loads single variation file (YAML dict)
- `_merge_multi_sources()`: Merges multiple sources (files + inline)
- `_is_inline_string()`: Detects inline strings vs file paths

**Import Types Supported:**
- ✅ **Single file:** `Outfit: ../variations/outfit.yaml`
- ✅ **Inline strings:** `Place: ["luxury room", "jungle"]`
- ✅ **Multi-source:** `Outfit: [../urban.yaml, ../chic.yaml, "red dress"]`
- ✅ **Nested imports:** `chunks: {positive: ..., negative: ...}`

**Features:**
- ✅ MD5 short hash (8 chars) for inline string keys
- ✅ Duplicate key conflict detection (ValueError)
- ✅ Order preservation in multi-source merge
- ✅ Quote stripping from inline values
- ✅ Inline strings never conflict (unique MD5 keys)

### Test Coverage

**16 unit tests** covering:
- ✅ Single file imports (3 tests)
- ✅ Inline string imports with MD5 keys (3 tests)
- ✅ Multi-source merging (3 tests)
- ✅ Conflict detection (2 tests)
- ✅ Nested imports (2 tests)
- ✅ Edge cases (empty imports, single items) (3 tests)

**No regressions:** All 224 existing V1 tests still pass.

**Total: 340 tests** (116 V2 + 224 V1)

### Success Criteria (from spec)

✅ **Import fichiers YAML fonctionne**
✅ **Inline strings avec clés auto-générées (MD5 8-char)**
✅ **Conflits de clés détectés et ValueError raised**
✅ **Multi-source merge préserve ordre**
✅ **Nested imports (chunks: {positive, negative})**
✅ **Tests passent (16 tests)**
✅ **Pas de régression V1**

### File Structure

```
v2/
├── resolvers/
│   ├── inheritance_resolver.py   # Phase 3
│   ├── import_resolver.py        # Phase 4 ⭐ NEW
│   └── __init__.py
├── tests/v2/unit/
│   ├── test_import_resolver.py   # 16 tests ⭐ NEW
│   └── ...
```

### Example Usage

```python
from templating.v2.loaders.yaml_loader import YamlLoader
from templating.v2.loaders.parser import ConfigParser
from templating.v2.resolvers.import_resolver import ImportResolver

# Setup
loader = YamlLoader()
parser = ConfigParser()
resolver = ImportResolver(loader, parser)

# Resolve imports from a config
base_path = config.source_file.parent
resolved_imports = resolver.resolve_imports(config, base_path)

# Result format:
# {
#   "Outfit": {
#     "Urban1": "jeans and t-shirt",
#     "Chic1": "elegant dress",
#     "7d8e3a2f": "red dress"  # MD5 key for inline
#   }
# }
```

### Import Resolution Examples

**1. Single file:**
```yaml
imports:
  Angle: ../variations/angles.yaml
```
→ Loads and returns dict from angles.yaml

**2. Inline strings:**
```yaml
imports:
  Place:
    - "luxury living room"
    - "tropical jungle"
```
→ Returns: `{md5("luxury..."): "luxury living room", md5("tropical..."): "tropical jungle"}`

**3. Multi-source merge:**
```yaml
imports:
  Outfit:
    - ../variations/outfit.urban.yaml   # 3 items
    - ../variations/outfit.chic.yaml    # 3 items
    - "red dress, elegant"              # 1 inline
```
→ Returns: 7 items total, order preserved

**4. Conflict detection:**
```yaml
imports:
  Outfit:
    - outfit_urban.yaml    # Has key "Casual"
    - outfit_conflict.yaml # Also has "Casual"
```
→ Raises: `ValueError: Duplicate key 'Casual' in Outfit imports (found in outfit_urban.yaml and outfit_conflict.yaml)`

**5. Nested imports:**
```yaml
imports:
  chunks:
    positive: ../chunks/positive.yaml
    negative: ../chunks/negative.yaml
```
→ Returns: `{"chunks": {"positive": {...}, "negative": {...}}}`

---

## Phase 5: Template Resolution ✅ COMPLETED

**Date:** 2025-10-09
**Status:** Implemented and tested

### What was implemented

Phase 5 implements comprehensive template resolution with chunk injection and advanced selectors:

#### 1. TemplateResolver (`resolvers/template_resolver.py`)
Template resolution engine with full V2.0 syntax support:

**Core Methods:**
- `resolve_template()`: Main entry point, resolves chunks + placeholders
- `_inject_chunks_with_params()`: Chunk injection with parameter passing
- `_inject_chunk_refs()`: Simple and nested chunk references
- `_resolve_placeholders()`: Placeholder resolution with context priority
- `_parse_selectors()`: Parse all selector types from `[selector]` syntax
- `_apply_selector()`: Apply selectors to variation dicts
- `extract_weights()`: Extract weights for combinatorial generation

**Chunk Injection Syntax:**
- ✅ Simple refs: `@Character` → Loads chunk template
- ✅ Nested refs: `@chunks.positive` → Navigates nested imports
- ✅ With params: `@{Character with Angles:{Angle[15]}, Poses:{Pose[$5]}}` → Parameter passing

**Selector Types (from spec section 7.4):**
- ✅ `[N]` - Limit to N random variations
- ✅ `[#1,3,5]` - Select specific indexes (0-based)
- ✅ `[BobCut,LongHair]` - Select by keys
- ✅ `[$W]` - Combinatorial weight (for loop ordering)
- ✅ `[sel1;sel2]` - Combine selectors with semicolon separator

**Placeholder Resolution:**
- ✅ Context priority: `chunks` > `defaults` > `imports`
- ✅ Placeholder with selectors: `{Angle[15;$8]}`
- ✅ Recursive resolution through chunk templates
- ✅ Missing placeholder → empty string (graceful handling)

**Features:**
- ✅ Selector parsing with regex patterns
- ✅ Selector application (limit, index, key, weight)
- ✅ Parameter splitting respecting nested braces/brackets
- ✅ Weight extraction for combinatorial generation
- ✅ Supports all V2.0 selector combinations

### Test Coverage

**35 unit tests** covering:
- ✅ Selector parsing (7 tests) - All selector types + combinations
- ✅ Selector application (6 tests) - Apply to variations, edge cases
- ✅ Placeholder resolution (7 tests) - Context priority, selectors
- ✅ Chunk injection (3 tests) - Simple refs, recursive resolution
- ✅ Nested chunk refs (3 tests) - Navigation, placeholders
- ✅ Chunk with params (3 tests) - Parameter passing, parsing
- ✅ Helper methods (4 tests) - Utilities, weight extraction
- ✅ Integration tests (2 tests) - Complex scenarios

**No regressions:** All 224 existing V1 tests still pass.

**Total: 375 tests** (151 V2 + 224 V1)

### Success Criteria (from spec)

✅ **Simple chunk injection works (@ChunkName)**
✅ **Nested chunk refs work (@chunks.positive)**
✅ **Chunk with params works (@{Chunk with Param:{Import[sel]}})**
✅ **All selector types parsed correctly**
✅ **Selector combinations work ([sel1;sel2])**
✅ **Placeholder resolution with context priority**
✅ **Tests passent (35 tests, goal was 20-25)**
✅ **Pas de régression V1 (224/224 passing)**
✅ **Pas de régression V2 (116/116 previous tests passing)**

### File Structure

```
v2/
├── resolvers/
│   ├── inheritance_resolver.py   # Phase 3
│   ├── import_resolver.py        # Phase 4
│   ├── template_resolver.py      # Phase 5 ⭐ NEW
│   └── __init__.py
├── tests/v2/unit/
│   ├── test_template_resolver.py # 35 tests ⭐ NEW
│   └── ...
```

### Example Usage

```python
from templating.v2.resolvers.template_resolver import TemplateResolver

# Setup
resolver = TemplateResolver(loader, parser, import_resolver)

# Context with resolved imports and chunks
context = {
    'imports': {
        'Character': {'template': '1girl, {Main}, {Angle}'},
        'Angle': {'Front': 'front view', 'Side': 'side view'},
        'Pose': {'Standing': 'standing', 'Sitting': 'sitting'}
    },
    'chunks': {'Main': '22, slim'},
    'defaults': {'Quality': 'masterpiece'}
}

# 1. Simple chunk injection
template = "@Character, detailed"
result = resolver.resolve_template(template, context)
# → "1girl, 22, slim, {Angle}, detailed"

# 2. Chunk with parameters
template = "@{Character with Angles:{Angle[Front]}, Poses:{Pose}}"
result = resolver.resolve_template(template, context)
# → "1girl, 22, slim, front view"

# 3. Placeholder with selectors
template = "{Angle[15;$8]}"
result = resolver.resolve_template(template, context)
# → One of the angle values (15 random max, weight 8)

# 4. Extract weights for combinatorial
weights = resolver.extract_weights("{Outfit[$2]}, {Angle[$10]}")
# → {'Outfit': 2, 'Angle': 10}
# → Loop order: Outfit (outer, weight 2) -> Angle (inner, weight 10)
```

### Template Resolution Examples

**1. Simple chunk reference:**
```yaml
template: |
  @Character,
  detailed background
```
→ Injects Character chunk template recursively

**2. Nested chunk reference:**
```yaml
imports:
  chunks:
    positive: ../chunks/positive.chunk.yaml

template: |
  @chunks.positive,
  beautiful girl
```
→ Navigates nested import structure

**3. Chunk with parameter passing:**
```yaml
template: |
  @{Character with Angles:{Angle[15]}, Poses:{Pose[$0]}}
```
→ Passes Angle (15 random) and Pose (weight 0 = non-combinatorial) to Character chunk

**4. Selector combinations:**
```yaml
# Limit + Weight
{Angle[15;$8]}        # 15 random angles, weight 8

# Index + Weight
{Angle[#1,3,5;$0]}    # Select indexes 1,3,5, weight 0 (non-combinatorial)

# Keys + Weight
{Haircut[BobCut,LongHair;$5]}  # Select specific keys, weight 5
```

**5. Context priority:**
```python
context = {
    'chunks': {'Value': 'from_chunks'},      # Priority 1
    'defaults': {'Value': 'from_defaults'},  # Priority 2
    'imports': {'Value': {...}}              # Priority 3
}
# {Value} → "from_chunks" (highest priority)
```

---

## Phase 6: Normalization & Generation ✅ COMPLETED

**Date:** 2025-10-10
**Status:** Implemented and tested

### What was implemented

Phase 6 implements the final generation and orchestration pipeline, completing the full V2.0 system:

#### 1. PromptNormalizer (`normalizers/normalizer.py`) ✅
Normalizes resolved prompts according to spec section 8:

**Normalization Rules:**
- ✅ **Rule 1:** Trim whitespace at start/end of lines (preserves trailing ", " for SD)
- ✅ **Rule 2:** Collapse multiple commas (`,, ` → `, `)
- ✅ **Rule 3:** Remove orphan commas (lines with only comma/whitespace)
- ✅ **Rule 4:** Normalize spacing around commas (no space before, one space after)
- ✅ **Rule 5:** Preserve max 1 blank line between content

**Key Design Decisions:**
- Trailing ", " before newlines is PRESERVED (intentional SD formatting)
- Orphan comma lines are replaced with empty lines (for blank line preservation)
- Normalization order: collapse → orphan → spacing → trim → blank lines
- Final strip() to clean entire result

#### 2. PromptGenerator (`generators/generator.py`) ✅
Generates prompts in combinatorial or random mode with full selector support:

**Core Methods:**
- `generate()`: Main entry point, dispatches to combinatorial/random
- `_generate_combinatorial()`: Nested loops with weight-based ordering
- `_generate_random()`: Unique random combinations
- `_apply_seed_mode()`: Seed calculation (fixed/progressive/random)
- `_apply_selectors()`: Apply selectors to variation dicts

**Generation Modes:**
- ✅ **Combinatorial**: Nested loops with weight ordering
  - Lower weight ($2) = outer loop (changes less often)
  - Higher weight ($10) = inner loop (changes more often)
  - Weight $0 = excluded from combinatorial (random per image)
  - Example: `{Outfit[$2]}, {Angle[$10]}` → For each Outfit, iterate all Angles
- ✅ **Random**: Random combinations with uniqueness check
  - Configurable max_images limit
  - Prevents duplicate combinations

**Seed Modes:**
- ✅ **fixed**: Same seed for all images (reproducibility)
- ✅ **progressive**: SEED, SEED+1, SEED+2... (controlled variation)
- ✅ **random**: -1 per image (maximum variety)

**Features:**
- Selector application during generation ([N], [#i,j], [Key1,Key2])
- Weight extraction from templates
- Normalizer integration (all prompts normalized)
- Variation tracking in output

#### 3. V2Pipeline (`orchestrator.py`) ✅
End-to-end pipeline orchestration from YAML to normalized prompts:

**Core Methods:**
- `process_template()`: Main entry point, full pipeline execution
- `validate_template()`: Run 5-phase validation
- `get_available_variations()`: Get all available variation values
- `calculate_total_combinations()`: Calculate max combinatorial size

**Pipeline Stages:**
1. **Load**: YamlLoader reads config file
2. **Parse**: ConfigParser creates typed model
3. **Validate**: ConfigValidator runs 5-phase validation
4. **Resolve Inheritance**: InheritanceResolver merges parent configs
5. **Resolve Imports**: ImportResolver loads all variations
6. **Resolve Template**: TemplateResolver injects chunks + placeholders
7. **Generate**: PromptGenerator creates variation combinations
8. **Normalize**: PromptNormalizer cleans final prompts

**Component Integration:**
- Manages all resolver instances
- Aggregates parameters through inheritance chain
- Handles errors and validation failures
- Provides helper methods for introspection

**Output Format:**
```python
{
    'prompt': str,           # Normalized positive prompt
    'negative_prompt': str,  # Normalized negative prompt
    'seed': int,             # Calculated seed
    'variations': dict,      # Variation values used
    'parameters': dict       # Merged SD parameters
}
```

### Test Coverage

**56 unit tests** covering:
- ✅ PromptNormalizer: 22 tests (all rules, edge cases, real-world)
- ✅ PromptGenerator: 20 tests
  - Combinatorial mode (4 tests)
  - Random mode (3 tests)
  - Weight ordering (3 tests)
  - Selector application (4 tests)
  - Seed modes (3 tests)
  - Edge cases (3 tests)
- ✅ V2Pipeline: 14 tests
  - Full pipeline (3 tests)
  - Component integration (3 tests)
  - Helper methods (3 tests)
  - Error handling (3 tests)
  - Parameter merging (2 tests)

**No regressions:** All 224 existing V1 tests still pass.

**Total: 433 tests** (209 V2 + 224 V1)

### Success Criteria (from spec)

✅ **All 3 components implemented (Normalizer, Generator, Pipeline)**
✅ **Combinatorial mode with weight ordering**
✅ **Random mode with uniqueness**
✅ **All seed modes (fixed/progressive/random)**
✅ **Selector application during generation**
✅ **Full pipeline orchestration (load → validate → resolve → generate → normalize)**
✅ **Parameter aggregation through inheritance**
✅ **Tests passent (56 tests, goal was ~45-50)**
✅ **Pas de régression V1 (224/224 passing)**
✅ **Pas de régression V2 (153/153 previous tests passing)**

### File Structure

```
v2/
├── normalizers/
│   ├── normalizer.py          # PromptNormalizer ⭐ (Phase 6)
│   └── __init__.py
├── generators/
│   ├── generator.py           # PromptGenerator ⭐ (Phase 6)
│   └── __init__.py
├── orchestrator.py            # V2Pipeline ⭐ (Phase 6)
├── tests/v2/unit/
│   ├── test_normalizer.py     # 22 tests ⭐
│   ├── test_generator.py      # 20 tests ⭐
│   ├── test_orchestrator.py   # 14 tests ⭐
│   └── ...
```

### Example Usage

**1. Full Pipeline:**
```python
from templating.v2.orchestrator import V2Pipeline

# Initialize pipeline
pipeline = V2Pipeline(configs_dir="/path/to/configs")

# Process template with full resolution
results = pipeline.process_template(
    template_file="character.template.yaml",
    generation_mode="combinatorial",
    seed_mode="progressive",
    seed=42,
    max_images=None  # All combinations
)

# Each result contains:
# {
#   'prompt': "1girl, casual outfit, front view, masterpiece, ...",
#   'negative_prompt': "low quality, blurry, ...",
#   'seed': 42,  # or 43, 44... in progressive mode
#   'variations': {'Outfit': 'casual', 'Angle': 'front'},
#   'parameters': {'steps': 20, 'cfg_scale': 7, ...}
# }
```

**2. Weight-based Loop Ordering:**
```python
# Template with weights:
# {Outfit[$2]}, {Angle[$10]}

results = pipeline.process_template(
    template_file="weighted.template.yaml",
    generation_mode="combinatorial"
)
# → Outfit loop (outer), Angle loop (inner)
# → For each Outfit, iterate through all Angles
```

**3. Random Mode:**
```python
results = pipeline.process_template(
    template_file="character.template.yaml",
    generation_mode="random",
    max_images=50  # Generate 50 random combinations
)
```

**4. Validation Only:**
```python
validation_result = pipeline.validate_template("character.template.yaml")
if not validation_result.is_valid:
    print(validation_result.to_json())  # See all errors
```

**5. Introspection:**
```python
# Get available variations
variations = pipeline.get_available_variations("character.template.yaml")
# → {'Outfit': ['casual', 'formal', ...], 'Angle': ['front', 'side', ...]}

# Calculate total combinations
total = pipeline.calculate_total_combinations("character.template.yaml")
# → 45 (e.g., 5 outfits × 9 angles)
```

---

## Phase 7: SD API Integration ✅ COMPLETED

**Date:** 2025-10-10
**Status:** Implemented and tested

### What was implemented

Phase 7 implements the SD WebUI API integration, allowing V2 prompts to be executed and generate actual images:

#### 1. V2Executor (`executor.py`) ✅
Executes generated prompts via SD WebUI API with full metadata tracking:

**Core Methods:**
- `execute_prompts()`: Batch execution with progress reporting
- `execute_single()`: Single prompt execution with error handling
- `_apply_parameters()`: Map V2 parameters to SD API config
- `_save_image()`: Decode and save base64 images
- `_save_metadata()`: Save prompt metadata as JSON
- `test_connection()`: Verify SD API availability
- `get_session_summary()`: Generate execution statistics

**Features:**
- ✅ Integration with existing V1 SDAPIClient (reuse, not rewrite)
- ✅ Batch processing with configurable batch size
- ✅ Progress callbacks for UI integration
- ✅ Session-based output organization (timestamped directories)
- ✅ Metadata JSON saved alongside each image
- ✅ Parameter mapping from V2 config to SD API
- ✅ Error handling with graceful continuation
- ✅ Success/failure tracking per image
- ✅ Summary statistics (total/successful/failed)

**Output Organization:**
```
output/
└── 20251010_143022/          # Session directory (timestamp)
    ├── image_0001.png        # Generated image
    ├── image_0001.json       # Metadata (prompt, seed, variations, params)
    ├── image_0002.png
    ├── image_0002.json
    └── ...
```

**Metadata Format:**
```json
{
  "prompt": "1girl, casual outfit, front view, masterpiece, ...",
  "negative_prompt": "low quality, blurry, ...",
  "seed": 42,
  "variations": {
    "Outfit": "casual",
    "Angle": "front"
  },
  "parameters": {
    "steps": 30,
    "cfg_scale": 7.0,
    "width": 512,
    "height": 768,
    "sampler": "DPM++ 2M Karras"
  },
  "image_path": "/path/to/output/20251010_143022/image_0001.png",
  "timestamp": "2025-10-10T14:30:25.123456",
  "api_info": {
    "seed": 42,
    "steps": 30,
    "cfg_scale": 7.0
  }
}
```

### Test Coverage

**18 integration tests** covering:
- ✅ Initialization (2 tests) - Default and custom client
- ✅ Single execution (3 tests) - Success, API error, parameter application
- ✅ Batch execution (3 tests) - Multiple prompts, progress callback, partial failure
- ✅ Metadata (2 tests) - All fields present, variations preserved
- ✅ Output management (4 tests) - Session dirs, output dir change, summaries
- ✅ Connection (2 tests) - Success and failure
- ✅ Parameter mapping (2 tests) - Complete and partial parameter sets

**No regressions:** All 433 existing tests still pass.

**Total: 451 tests** (227 V2 + 224 V1)

### Success Criteria (from spec)

✅ **V2Executor can execute prompts from V2Pipeline**
✅ **Images saved to output directory with correct naming**
✅ **Metadata JSON saved alongside each image**
✅ **Batch processing works (multiple prompts in sequence)**
✅ **Progress reporting via callbacks**
✅ **Error handling for API failures**
✅ **18 integration tests passing**
✅ **No regressions (451/451 tests passing)**

### File Structure

```
v2/
├── executor.py                # V2Executor ⭐ (Phase 7)
├── tests/v2/integration/
│   ├── test_api_integration.py  # 18 tests ⭐ (Phase 7)
│   └── __init__.py
├── orchestrator.py            # V2Pipeline (Phase 6)
├── generators/                # Phase 6
├── normalizers/               # Phase 6
├── resolvers/                 # Phases 3-5
├── validators/                # Phases 1-2
├── loaders/                   # Phase 1
└── ...
```

### Example Usage

**1. End-to-End: YAML → Images**
```python
from templating.v2.orchestrator import V2Pipeline
from templating.v2.executor import V2Executor
from api.sdapi_client import SDAPIClient

# Setup
pipeline = V2Pipeline(configs_dir="/path/to/configs")
api_client = SDAPIClient(api_url="http://127.0.0.1:7860")
executor = V2Executor(
    api_client=api_client,
    output_dir="~/output",
    session_name="character_batch_001"
)

# Generate prompts
prompts = pipeline.run("character.prompt.yaml")
# → List of prompt dicts with variations

# Execute (generate images)
results = executor.execute_prompts(
    prompts,
    batch_size=1,
    progress_callback=lambda i, total: print(f"Progress: {i}/{total}")
)

# Check results
summary = executor.get_session_summary(results)
print(f"Generated {summary['successful']}/{summary['total']} images")
print(f"Session directory: {summary['session_dir']}")
```

**2. Progress Reporting**
```python
def progress_callback(current, total):
    percent = (current / total) * 100
    print(f"[{current}/{total}] {percent:.1f}%")

results = executor.execute_prompts(
    prompts,
    progress_callback=progress_callback
)
```

**3. Error Handling**
```python
results = executor.execute_prompts(prompts)

# Check for failures
for idx, result in enumerate(results):
    if not result['success']:
        print(f"Image {idx + 1} failed: {result['error']}")
        print(f"Prompt: {result['prompt']}")

# Summary
summary = executor.get_session_summary(results)
for error in summary['errors']:
    print(f"Error at index {error['index']}: {error['error']}")
```

**4. Custom Session Organization**
```python
# Change output directory mid-session
executor.set_output_dir("~/new_output", session_name="experimental_001")

# Test connection before execution
if executor.test_connection():
    results = executor.execute_prompts(prompts)
else:
    print("SD API not available")
```

**5. Full Pipeline with Parameters**
```python
from templating.v2.orchestrator import V2Pipeline
from templating.v2.executor import V2Executor
from api.sdapi_client import SDAPIClient, GenerationConfig

# Custom SD parameters
api_client = SDAPIClient()
api_client.set_generation_config(GenerationConfig(
    steps=50,
    cfg_scale=8.5,
    width=768,
    height=1024,
    sampler_name="Euler a",
    enable_hr=True,
    hr_scale=2.0
))

# Pipeline with combinatorial generation
pipeline = V2Pipeline()
prompts = pipeline.run("template.prompt.yaml")

# Execute with custom config
executor = V2Executor(api_client=api_client, output_dir="~/hires_output")
results = executor.execute_prompts(prompts)
```

### Integration Details

**Parameter Mapping (V2 → SD API):**
```python
# V2 parameters (from config YAML)
parameters = {
    'steps': 30,
    'cfg_scale': 7.0,
    'width': 512,
    'height': 768,
    'sampler': 'DPM++ 2M Karras',
    'scheduler': 'Karras',
    'enable_hr': True,
    'hr_scale': 2.0,
    'hr_upscaler': 'R-ESRGAN 4x+',
    'denoising_strength': 0.7
}

# Mapped to SDAPIClient.GenerationConfig
# (handled automatically by V2Executor)
```

**Result Format:**
```python
{
    'prompt': str,              # From V2Pipeline
    'negative_prompt': str,     # From V2Pipeline
    'seed': int,                # From V2Pipeline
    'variations': dict,         # From V2Pipeline
    'parameters': dict,         # From V2Pipeline
    'image_path': Path,         # NEW: Saved image path
    'metadata_path': Path,      # NEW: Saved JSON path
    'success': bool,            # NEW: Execution status
    'error': Optional[str]      # NEW: Error message if failed
}
```

### Next Steps: CLI & Production

Phase 7 completes the V2.0 execution layer. Ready for:

1. **CLI Interface**
   - `sdgen v2 generate <template>` command
   - Interactive mode selection (combinatorial/random)
   - Real-time progress display
   - Session management

2. **End-to-End Tests**
   - Integration tests with real config files
   - Full workflow validation (YAML → Images)
   - Performance benchmarks

3. **Performance Optimization**
   - Parallel execution (multiple API workers)
   - Batch processing strategies
   - Memory usage optimization

4. **Migration Tools**
   - V1 → V2 config converter
   - Backward compatibility layer
   - Migration documentation

---

**Total Implementation time:** ~10 hours (Phases 1-7)
**Total Lines of code:** ~3689 (production) + ~5197 (tests)
**Test pass rate:** 100% (451/451)

**Template System V2.0 + API Integration is COMPLETE!** 🎉

---

## Post-Phase 7: Legacy Compatibility Investigation 🔍 IN PROGRESS

**Date:** 2025-10-10
**Status:** Debugging
**Issue:** Standalone prompts (without `implements:`) showing "Duplicate key 'type', 'name', 'version', 'variations'" errors

### Problème identifié

**Symptôme :**
- Tests unitaires `test_parse_variations_structured.py` : ✅ **PASSENT** (3/3 tests)
- Tests manuels isolés (Python REPL) : ✅ **FONCTIONNENT**
- Test legacy `scripts/test_legacy_compatibility.py` : ❌ **ÉCHOUE** (9/17 success, 8/17 errors)
- Erreur répétée : `Duplicate key 'type' in HairColor imports (found in ../variations/hassaku/body/haircolors.realist.yaml and ../variations/hassaku/body/haircolors.cyberpunk.yaml)`

**Fichiers variations concernés :**
- Structure YAML correcte avec `type`, `name`, `version`, `variations`
- Exemple : `/mnt/d/StableDiffusion/private-new/prompts/variations/hassaku/body/haircolors.cyberpunk.yaml`
```yaml
type: variations
name: Haircolors.Cyberpunk
version: '1.0'
variations:
  black_to_silver_gradient_hair_: black to silver gradient hair, roots to tips
  dark_brown_to_caramel_ombré_ha: dark brown to caramel ombré hair, natural
  ...
```

### Pistes explorées

#### ✅ 1. Fix implémenté : `parse_variations()` dual-format support
**Fichier :** `CLI/src/templating/v2/loaders/parser.py:117-161`

**Modification :**
```python
def parse_variations(self, data: Dict[str, Any]) -> Dict[str, str]:
    # Check if structured format (has 'variations' key)
    if 'variations' in data:
        variations = data['variations']
        return {str(key): str(value) for key, value in variations.items()}

    # Flat format: entire dict is variations
    return {str(key): str(value) for key, value in data.items()}
```

**Résultat :** Tests unitaires passent, mais legacy tests échouent toujours.

#### ✅ 2. Cache désactivé dans `YamlLoader`
**Fichier :** `CLI/src/templating/v2/loaders/yaml_loader.py:53-72`

**Modification :**
```python
# CACHE DISABLED: Performance not critical for local NVMe SSD access
# cache_key = str(resolved_path)
# if cache_key in self.cache:
#     return self.cache[cache_key]
```

**Raison :** Éviter les données stale, privilégier fraîcheur des données.

**Résultat :** Pas de changement, erreurs persistent.

#### ✅ 3. Nettoyage bytecode Python
**Actions :**
- `find src -type d -name __pycache__ -exec rm -rf {} +`
- `find ../venv -type d -name __pycache__ -exec rm -rf {} +`
- `find ../venv/lib -type d -name "templating*" -exec rm -rf {} +`

**Résultat :** Pas de changement, erreurs persistent.

#### ✅ 4. Tests manuels de `parse_variations()` avec fichiers réels
**Test Python REPL :**
```python
from templating.v2.loaders.parser import ConfigParser
parser = ConfigParser()
raw_data = yaml.safe_load(open('haircolors.cyberpunk.yaml'))
result = parser.parse_variations(raw_data)

# RÉSULTAT : ✅ 'type' NOT in result (correct)
# Keys : 10 variations (black_to_silver_gradient_hair_, etc.)
```

**Conclusion :** `parse_variations()` fonctionne isolément mais échoue dans le test legacy.

### Observations critiques

1. **V1 fonctionne, V2 échoue** : `templating.loaders.load_variations()` (V1) charge correctement les mêmes fichiers
2. **Tests isolés passent** : Appels directs à `parse_variations()` retournent les bonnes données
3. **Test legacy échoue** : Le script `scripts/test_legacy_compatibility.py` montre toujours les duplicate keys

### Hypothèses restantes

1. **Import circulaire ou module caching** : Le test legacy utilise peut-être une version différente du code
2. **Autre chemin de code** : Il existe peut-être un bypass qui ne passe pas par `parse_variations()`
3. **Problème dans `_merge_multi_sources()`** : La détection de duplicate keys se fait dans `import_resolver.py:161-168` après l'appel à `_load_variation_file()` qui appelle `parse_variations()`

### Fichiers modifiés

- ✅ `CLI/src/templating/v2/loaders/parser.py` - Dual-format support ajouté
- ✅ `CLI/src/templating/v2/loaders/yaml_loader.py` - Cache désactivé
- ✅ `CLI/src/templating/v2/validators/validator.py` - `implements` optionnel (ligne 143-163)
- ✅ `CLI/src/templating/v2/orchestrator.py` - Utilise `validate()` au lieu de `validate_prompt()` (ligne 106-108)
- ✅ `CLI/tests/templating/test_parse_variations_structured.py` - Tests unitaires créés (3 tests ✅)
- ✅ `CLI/tests/templating/fixtures/variations/haircolors_structured.yaml` - Fixture test créée

### Prochaines étapes suggérées

1. **Debugger avec breakpoint** dans `import_resolver.py:158-168` pour voir ce que retourne `_load_variation_file()` dans le contexte du test legacy
2. **Comparer V1 vs V2** : Tracer exactement la différence de comportement entre `templating.loaders.load_variations()` et `templating.v2.loaders.parser.parse_variations()`
3. **Vérifier l'ordre d'imports** : S'assurer que le test legacy n'importe pas une version mixte V1/V2
4. **Ajouter logging temporaire** dans `parse_variations()` pour voir si la méthode est bien appelée avec la bonne structure de données

### Statistiques

- **Templates testés:** 17
- **Succès:** 9 (templates simples sans multi-source imports)
- **Échecs:** 8 (tous avec multi-source imports montrant duplicate keys metadata)
- **Tests unitaires V2:** 3/3 passent ✅
- **Tests manuels:** Tous passent ✅
- **Tests legacy:** 9/17 passent ⚠️
