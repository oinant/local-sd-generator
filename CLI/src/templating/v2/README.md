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

### Next Steps: Phase 5 - Template Resolution

Phase 5 will implement template resolution with chunk injection and selectors:
1. TemplateResolver with chunk injection (`@Chunk`, `@{Chunk with ...}`)
2. Selector parsing and application (`[15]`, `[#1,3,5]`, `[$8]`)
3. Placeholder resolution with context
4. Support for `with` syntax parameter passing

See: `docs/roadmap/template-system-v2-architecture.md` (lines 1280+)

---

**Total Implementation time:** ~4 hours (Phases 1-4)
**Total Lines of code:** ~1610 (production) + ~2410 (tests)
**Test pass rate:** 100% (340/340)
