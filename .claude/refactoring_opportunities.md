# Design Patterns Refactoring Analysis - Template System V2.0

**Generated:** 2025-10-31
**Analyzer:** Architecture Analysis Agent
**Scope:** `/packages/sd-generator-cli/sd_generator_cli/templating/`

---

## Executive Summary

This analysis identifies **12 high-impact refactoring opportunities** across the templating module. The codebase shows good overall architecture but has **3 critical "god classes"** (954, 831, 706 lines) and several opportunities to apply **Strategy**, **Factory**, and **Decorator** patterns to reduce complexity and improve maintainability.

**Key Findings:**
- **3 files exceed 700 lines** (candidates for splitting)
- **Average complexity grade: C (10.3)** in template_resolver.py
- **Multiple type-checking if/elif chains** (Strategy pattern candidates)
- **Conditional parameter parsing** (Factory/Visitor pattern candidates)

---

## Critical Opportunities (P1-P3)

### Opportunity 1: Strategy Pattern for File Type Detection & Parsing
**Location:** `import_resolver.py:187-227`
**Current Pattern:** if/elif chain checking file extensions

```python
# Current code
is_chunk = (
    resolved_path.name.endswith('.chunk.yaml') or
    resolved_path.name.endswith('.chunk.yml')
)
is_adetailer = (
    resolved_path.name.endswith('.adetailer.yaml') or
    resolved_path.name.endswith('.adetailer.yml')
)
is_controlnet = (
    resolved_path.name.endswith('.controlnet.yaml') or
    resolved_path.name.endswith('.controlnet.yml')
)

if is_chunk:
    chunk_config = self.parser.parse_chunk(data, resolved_path)
    return {...}
if is_adetailer:
    adetailer_config = self.parser.parse_adetailer_file(data, resolved_path)
    return adetailer_config.detector
if is_controlnet:
    controlnet_config = parse_controlnet_file(resolved_path)
    return controlnet_config
```

**Recommended Pattern:** Strategy Pattern with Registry

```python
# Strategy interface
class FileLoader(Protocol):
    def can_handle(self, path: Path) -> bool: ...
    def load(self, data: dict, path: Path, parser: ConfigParser) -> Any: ...

# Concrete strategies
class ChunkFileLoader:
    def can_handle(self, path: Path) -> bool:
        return path.suffix in ['.chunk.yaml', '.chunk.yml']

    def load(self, data: dict, path: Path, parser: ConfigParser) -> dict:
        chunk_config = parser.parse_chunk(data, path)
        return {'template': chunk_config.template, ...}

class ADetailerFileLoader:
    def can_handle(self, path: Path) -> bool:
        return '.adetailer.' in path.name

    def load(self, data: dict, path: Path, parser: ConfigParser) -> Any:
        config = parser.parse_adetailer_file(data, path)
        return config.detector

# Registry
class FileLoaderRegistry:
    def __init__(self):
        self.loaders: List[FileLoader] = [
            ChunkFileLoader(),
            ADetailerFileLoader(),
            ControlNetFileLoader(),
            VariationsFileLoader()  # Default fallback
        ]

    def load(self, path: Path, data: dict, parser: ConfigParser) -> Any:
        for loader in self.loaders:
            if loader.can_handle(path):
                return loader.load(data, path, parser)
        raise ValueError(f"No loader for {path}")
```

**Benefits:**
- **Extensibility:** Add new file types without modifying ImportResolver
- **Testability:** Each loader can be tested independently
- **SRP:** One loader per file type
- **Eliminates:** 40-line if/elif chain

**Effort:** Medium (~4h)
**Priority:** P2 (High value for future extensions)

---

### Opportunity 2: Split TemplateResolver into Focused Classes
**Location:** `template_resolver.py` (954 lines, 23 methods)
**Current Pattern:** God object handling chunks, placeholders, selectors, parsing

**Analysis:**
- **Chunk handling:** 6 methods (lines 111-665)
- **Placeholder resolution:** 4 methods (lines 246-412)
- **Selector parsing/application:** 3 methods (lines 772-897)
- **Parameter parsing:** 3 methods (lines 414-523)

**Recommended Pattern:** Facade + Specialized Resolvers

```python
# Phase 1: Chunk Resolution (structural)
class ChunkInjector:
    """Handles @Chunk and @{Chunk with params} injection."""
    def inject_chunks(self, template: str, context: dict) -> str:
        template = self._inject_chunks_with_params(template, context)
        template = self._inject_chunk_refs(template, context)
        return template

    def _inject_chunks_with_params(...): ...
    def _inject_chunk_refs(...): ...
    def _parse_chunk_param_overrides(...): ...
    def _split_params(...): ...

# Phase 2: Placeholder Resolution
class PlaceholderResolver:
    """Handles {Placeholder[selector]} and {Placeholder:part} resolution."""
    def resolve_placeholders(self, template: str, context: dict) -> str: ...
    def _get_placeholder_value(...): ...
    def _get_default_part(...): ...

# Selector parsing & application
class SelectorEngine:
    """Handles [limit], [#indexes], [keys], [$weight] selectors."""
    def parse_selector(self, selector_str: str) -> Selector: ...
    def apply_selector(self, variations: dict, selector: Selector) -> List[str]: ...
    def extract_weights(self, template: str) -> Dict[str, int]: ...

# Facade (keeps API compatibility)
class TemplateResolver:
    def __init__(self, loader, parser, import_resolver):
        self.chunk_injector = ChunkInjector(loader, parser, import_resolver)
        self.placeholder_resolver = PlaceholderResolver(loader)
        self.selector_engine = SelectorEngine()

    def resolve_template(self, template: str, context: dict, skip_chunk_injection: bool = False) -> str:
        if not skip_chunk_injection:
            template = self.chunk_injector.inject_chunks(template, context)
        template = self.placeholder_resolver.resolve_placeholders(template, context)
        return template
```

**Benefits:**
- **Reduced complexity:** Each class < 300 lines
- **SRP:** One responsibility per class
- **Testability:** Test each resolver independently
- **Maintainability:** Changes to selectors don't affect chunk logic

**Effort:** Large (~8h)
**Priority:** P3 (High complexity but isolated, working well currently)

---

### Opportunity 3: Strategy Pattern for Config Type Parsing
**Location:** `parser.py:450-594` (parse_adetailer_parameter)
**Current Pattern:** if/elif chain checking isinstance for str/list/dict

```python
# Current code (parse_adetailer_parameter)
if isinstance(adetailer_value, str):
    detector = self._load_adetailer_file(adetailer_value, base_path)
    detectors.append(detector)
elif isinstance(adetailer_value, list):
    for item in adetailer_value:
        if isinstance(item, str):
            detector = self._load_adetailer_file(item, base_path)
            detectors.append(detector)
        elif isinstance(item, dict):
            # ... complex override logic
elif isinstance(adetailer_value, dict):
    # ... duplicate override logic
```

**Recommended Pattern:** Strategy Pattern

```python
# Strategy interface
class ADetailerConfigStrategy(Protocol):
    def parse(self, value: Any, base_path: Path, parser: ConfigParser) -> List[ADetailerDetector]: ...

# Strategies
class SingleFileADetailerStrategy:
    def parse(self, value: str, base_path: Path, parser: ConfigParser) -> List[ADetailerDetector]:
        detector = parser._load_adetailer_file(value, base_path)
        return [detector]

class MultiFileADetailerStrategy:
    def parse(self, value: list, base_path: Path, parser: ConfigParser) -> List[ADetailerDetector]:
        detectors = []
        for item in value:
            if isinstance(item, str):
                detectors.append(parser._load_adetailer_file(item, base_path))
            elif isinstance(item, dict):
                detectors.append(self._parse_with_override(item, base_path, parser))
        return detectors

class DictADetailerStrategy:
    def parse(self, value: dict, base_path: Path, parser: ConfigParser) -> List[ADetailerDetector]:
        detector = parser._load_adetailer_file(value['import'], base_path)
        if 'override' in value:
            self._apply_overrides(detector, value['override'])
        return [detector]

# Registry
class ADetailerParserRegistry:
    def __init__(self):
        self.strategies = {
            str: SingleFileADetailerStrategy(),
            list: MultiFileADetailerStrategy(),
            dict: DictADetailerStrategy()
        }

    def parse(self, value: Any, base_path: Path, parser: ConfigParser) -> List[ADetailerDetector]:
        strategy = self.strategies.get(type(value))
        if not strategy:
            raise ValueError(f"Unsupported adetailer format: {type(value)}")
        return strategy.parse(value, base_path, parser)

# Usage in ConfigParser
def parse_adetailer_parameter(self, adetailer_value: Any, base_path: Path) -> ADetailerConfig:
    registry = ADetailerParserRegistry()
    detectors = registry.parse(adetailer_value, base_path, self)
    return ADetailerConfig(enabled=True, detectors=detectors)
```

**Benefits:**
- **DRY:** Eliminates duplicate override logic
- **Extensibility:** Add new formats without modifying parser
- **Testability:** Test each strategy independently
- **Complexity:** Reduces CC from C (11) to A (2-3)

**Effort:** Medium (~3h)
**Priority:** P2 (Same pattern needed for controlnet_parameter)

---

## High-Value Opportunities (P4-P6)

### Opportunity 4: Factory Pattern for Config Type Detection
**Location:** `inheritance_resolver.py:147-160` (_parse_config)
**Current Pattern:** if/elif chain checking dict keys

```python
# Current code (FIXED in commit 0254c3a)
if 'generation' in data:
    return self.parser.parse_prompt(data, source_file)
elif 'type' in data:
    file_type = data['type']
    if file_type == 'template':
        return self.parser.parse_template(data, source_file)
    elif file_type == 'chunk':
        return self.parser.parse_chunk(data, source_file)
    elif file_type == 'prompt':
        return self.parser.parse_prompt(data, source_file)
    else:
        raise ValueError(f"Unknown type '{file_type}' in {source_file.name}")
else:
    return self.parser.parse_template(data, source_file)
```

**Recommended Pattern:** Factory with Priority Chain

```python
class ConfigFactory:
    """Factory for auto-detecting and creating config objects from YAML data."""

    def __init__(self, parser: ConfigParser):
        self.parser = parser
        self.detectors = [
            GenerationFieldDetector(),  # Highest priority
            TypeFieldDetector(),         # Medium priority
            DefaultTemplateDetector()    # Fallback
        ]

    def create_config(self, data: dict, source_file: Path) -> ConfigType:
        for detector in self.detectors:
            if detector.can_handle(data):
                return detector.create(data, source_file, self.parser)
        raise ValueError(f"Cannot determine config type for {source_file.name}")

# Detectors
class GenerationFieldDetector:
    def can_handle(self, data: dict) -> bool:
        return 'generation' in data

    def create(self, data: dict, source_file: Path, parser: ConfigParser) -> PromptConfig:
        return parser.parse_prompt(data, source_file)

class TypeFieldDetector:
    def can_handle(self, data: dict) -> bool:
        return 'type' in data

    def create(self, data: dict, source_file: Path, parser: ConfigParser) -> ConfigType:
        type_handlers = {
            'template': parser.parse_template,
            'chunk': parser.parse_chunk,
            'prompt': parser.parse_prompt
        }
        handler = type_handlers.get(data['type'])
        if not handler:
            raise ValueError(f"Unknown type '{data['type']}' in {source_file.name}")
        return handler(data, source_file)

class DefaultTemplateDetector:
    def can_handle(self, data: dict) -> bool:
        return True  # Fallback always matches

    def create(self, data: dict, source_file: Path, parser: ConfigParser) -> TemplateConfig:
        return parser.parse_template(data, source_file)

# Usage
self.config_factory = ConfigFactory(self.parser)
parent_config = self.config_factory.create_config(parent_data, parent_path)
```

**Benefits:**
- **Open/Closed:** Add new config types without modifying resolver
- **Testability:** Test detection logic independently
- **Clarity:** Explicit priority order

**Effort:** Small (~2h)
**Priority:** P5

**Status:** ✅ Partially fixed in commit `0254c3a` (proper type checking), but Factory pattern not yet implemented

---

### Opportunity 5: Visitor Pattern for Config Merge Rules
**Location:** `inheritance_resolver.py:215-351` (_merge_configs)
**Current Pattern:** Multiple if/elif checking config types with duplicate logic

**Analysis:**
- Template + Template merge
- Prompt + Template merge
- Prompt + Prompt merge
- Chunk + Chunk merge
- Duplicate {prompt} injection logic across branches

**Recommended Pattern:** Visitor Pattern

```python
# Visitor interface
class ConfigMergeVisitor(ABC):
    @abstractmethod
    def merge(self, parent: ConfigType, child: ConfigType) -> ConfigType: ...

# Concrete visitors
class TemplateMergeVisitor:
    def merge(self, parent: TemplateConfig, child: TemplateConfig) -> TemplateConfig:
        merged = deepcopy(child)
        merged.parameters = {**parent.parameters, **child.parameters}
        merged.imports = {**parent.imports, **child.imports}
        merged.template = self._inject_prompt_placeholder(parent.template, child.template)
        merged.negative_prompt = self._inject_negprompt_placeholder(...)
        return merged

    def _inject_prompt_placeholder(self, parent_template: str, child_template: str) -> str:
        if '{prompt}' in parent_template:
            return parent_template.replace('{prompt}', child_template)
        else:
            logger.warning("Parent has no {prompt} placeholder, replacing entirely")
            return child_template

class PromptMergeVisitor:
    def merge(self, parent: Union[TemplateConfig, PromptConfig], child: PromptConfig) -> PromptConfig:
        merged = deepcopy(child)
        merged.parameters = {**parent.parameters, **child.parameters}
        merged.imports = {**parent.imports, **child.imports}
        # Inject child.prompt into parent.template's {prompt}
        if parent.template and '{prompt}' in parent.template:
            merged.template = parent.template.replace('{prompt}', child.prompt)
        return merged

class ChunkMergeVisitor:
    def merge(self, parent: ChunkConfig, child: ChunkConfig) -> ChunkConfig:
        merged = deepcopy(child)
        merged.imports = {**parent.imports, **child.imports}
        merged.chunks = {**parent.chunks, **child.chunks}
        merged.defaults = {**parent.defaults, **child.defaults}
        merged.template = self._inject_or_replace(parent.template, child.template)
        return merged

# Registry
class MergeVisitorRegistry:
    def __init__(self):
        self.visitors = {
            (TemplateConfig, TemplateConfig): TemplateMergeVisitor(),
            (TemplateConfig, PromptConfig): PromptMergeVisitor(),
            (PromptConfig, PromptConfig): PromptMergeVisitor(),
            (ChunkConfig, ChunkConfig): ChunkMergeVisitor()
        }

    def merge(self, parent: ConfigType, child: ConfigType) -> ConfigType:
        key = (type(parent), type(child))
        visitor = self.visitors.get(key)
        if not visitor:
            raise ValueError(f"No merge visitor for {key}")
        return visitor.merge(parent, child)

# Usage in InheritanceResolver
def _merge_configs(self, parent: ConfigType, child: ConfigType) -> ConfigType:
    registry = MergeVisitorRegistry()
    return registry.merge(parent, child)
```

**Benefits:**
- **DRY:** Shared {prompt} injection logic
- **SRP:** One visitor per merge type
- **Testability:** Test each merge independently
- **Reduces:** 130-line method to ~10 lines

**Effort:** Medium (~4h)
**Priority:** P4

---

### Opportunity 6: Split ConfigParser by Responsibility
**Location:** `parser.py` (831 lines, 13 methods)
**Current Pattern:** One class parsing all config types + adetailer + controlnet

**Recommended Pattern:** Parser per Config Type

```python
# Base parser with common logic
class BaseConfigParser:
    def parse_variation_values(self, variations: dict) -> dict: ...
    def parse_output_config(self, output_data: dict) -> OutputConfig: ...
    def parse_themes_config(self, themes_data: dict) -> ThemeConfigBlock: ...

# Specialized parsers
class TemplateConfigParser(BaseConfigParser):
    def parse(self, data: dict, source_file: Path) -> TemplateConfig:
        # Template-specific parsing
        self._validate_template_field(data['template'])
        parameters = ParametersParser().parse(data.get('parameters'), source_file.parent)
        return TemplateConfig(...)

class PromptConfigParser(BaseConfigParser):
    def parse(self, data: dict, source_file: Path) -> PromptConfig:
        # Prompt-specific parsing
        self._validate_prompt_field(data['prompt'])
        generation = GenerationConfigParser().parse(data['generation'])
        parameters = ParametersParser().parse(data.get('parameters'), source_file.parent)
        return PromptConfig(...)

class ChunkConfigParser(BaseConfigParser):
    def parse(self, data: dict, source_file: Path) -> ChunkConfig:
        self._validate_chunk_template(data['template'])
        return ChunkConfig(...)

# Specialized parameter parsers
class ParametersParser:
    def parse(self, parameters: dict, base_path: Path) -> dict:
        parsed = parameters.copy()
        if 'adetailer' in parsed:
            parsed['adetailer'] = ADetailerParser().parse(parsed['adetailer'], base_path)
        if 'controlnet' in parsed:
            parsed['controlnet'] = ControlNetParser().parse(parsed['controlnet'], base_path)
        return parsed

class ADetailerParser:
    def parse(self, value: Any, base_path: Path) -> ADetailerConfig:
        # Use Strategy pattern from Opportunity 3
        ...

# Facade (keeps API compatibility)
class ConfigParser:
    def __init__(self):
        self.template_parser = TemplateConfigParser()
        self.prompt_parser = PromptConfigParser()
        self.chunk_parser = ChunkConfigParser()

    def parse_template(self, data: dict, source_file: Path) -> TemplateConfig:
        return self.template_parser.parse(data, source_file)

    def parse_prompt(self, data: dict, source_file: Path) -> PromptConfig:
        return self.prompt_parser.parse(data, source_file)

    def parse_chunk(self, data: dict, source_file: Path) -> ChunkConfig:
        return self.chunk_parser.parse(data, source_file)
```

**Benefits:**
- **SRP:** One parser per config type
- **Reduced size:** Each parser ~150-200 lines
- **Testability:** Test each parser independently
- **Maintainability:** Changes to adetailer don't affect prompt parsing

**Effort:** Large (~6h)
**Priority:** P4

---

## Medium-Value Opportunities (P7-P8)

### Opportunity 7: Strategy Pattern for Import Value Type Handling
**Location:** `import_resolver.py:71-128` (resolve_imports)
**Current Pattern:** if/elif checking isinstance(import_value)

**Recommended Pattern:** Strategy pattern similar to Opportunity 3

**Benefits:**
- Eliminates 60-line if/elif chain
- Each strategy < 30 lines

**Effort:** Small (~2h)
**Priority:** P7

---

### Opportunity 8: Decorator Pattern for Validation Phases
**Location:** `validator.py:55-93` (validate method)
**Current Pattern:** Sequential method calls for each phase

```python
def validate(self, config: ConfigType) -> ValidationResult:
    self.errors = []
    self._validate_structure(config)
    self._validate_paths(config)
    self._validate_inheritance(config)
    self._validate_imports(config)
    self._validate_templates(config)
    return ValidationResult(is_valid=len(self.errors) == 0, errors=self.errors)
```

**Recommended Pattern:** Chain of Responsibility with Decorator

```python
# Base validator
class ValidationPhase(ABC):
    def __init__(self, next_phase: Optional['ValidationPhase'] = None):
        self.next_phase = next_phase

    def validate(self, config: ConfigType, errors: List[ValidationError]) -> None:
        self._validate_phase(config, errors)
        if self.next_phase:
            self.next_phase.validate(config, errors)

    @abstractmethod
    def _validate_phase(self, config: ConfigType, errors: List[ValidationError]) -> None: ...

# Concrete phases
class StructureValidationPhase(ValidationPhase):
    def _validate_phase(self, config: ConfigType, errors: List[ValidationError]) -> None:
        if not config.version:
            errors.append(ValidationError(...))

class PathValidationPhase(ValidationPhase):
    def _validate_phase(self, config: ConfigType, errors: List[ValidationError]) -> None:
        # Path validation logic
        ...

# Build validation chain
validator = StructureValidationPhase(
    PathValidationPhase(
        InheritanceValidationPhase(
            ImportValidationPhase(
                TemplateValidationPhase()
            )
        )
    )
)

# Usage
def validate(self, config: ConfigType) -> ValidationResult:
    errors = []
    validator.validate(config, errors)
    return ValidationResult(is_valid=len(errors) == 0, errors=errors)
```

**Benefits:**
- **Extensibility:** Add new phases without modifying ConfigValidator
- **Testability:** Test each phase independently
- **Flexibility:** Skip/reorder phases dynamically

**Effort:** Medium (~3h)
**Priority:** P7

---

### Opportunity 9: Extract Method for Orchestrator.resolve()
**Location:** `orchestrator.py:134-310` (176 lines, CC: D/21)
**Current Pattern:** One massive method handling theme resolution + import resolution + chunk injection

**Recommended Pattern:** Extract Method + Template Method

```python
def resolve(
    self,
    config: PromptConfig,
    theme_name: Optional[str] = None,
    theme_file: Optional[Path] = None,
    style: str = "default"
) -> tuple[PromptConfig, ResolvedContext]:
    # Phase 1: Resolve inheritance
    resolved_config = self._resolve_inheritance(config)

    # Phase 2: Apply theme if specified
    resolved_config = self._apply_theme(resolved_config, config, theme_name, theme_file, style)

    # Phase 3: Resolve imports
    resolved_imports, import_metadata = self._resolve_imports(resolved_config, config, style)

    # Phase 4: Build context
    context = self._build_resolved_context(
        resolved_imports,
        import_metadata,
        resolved_config,
        style
    )

    # Phase 5: Inject chunks (Phase 1 - structural)
    resolved_config_with_chunks = self._inject_chunks_phase1(resolved_config, context)

    return resolved_config_with_chunks, context

def _resolve_inheritance(self, config: PromptConfig) -> PromptConfig:
    return self.inheritance_resolver.resolve_implements(config)

def _apply_theme(
    self,
    resolved_config: PromptConfig,
    original_config: PromptConfig,
    theme_name: Optional[str],
    theme_file: Optional[Path],
    style: str
) -> PromptConfig:
    if not theme_name and not theme_file:
        return resolved_config

    theme = self._load_theme(resolved_config, theme_name, theme_file)
    return self._merge_theme_imports(resolved_config, original_config, theme, style)

def _load_theme(...) -> ThemeConfig: ...
def _merge_theme_imports(...) -> PromptConfig: ...
def _resolve_imports(...) -> tuple[dict, dict]: ...
def _build_resolved_context(...) -> ResolvedContext: ...
def _inject_chunks_phase1(...) -> PromptConfig: ...
```

**Benefits:**
- **Reduces complexity:** CC from D (21) to B (5)
- **Readability:** Clear 5-phase structure
- **Testability:** Test each phase independently

**Effort:** Small (~2h)
**Priority:** P6

---

## Lower Priority Opportunities (P9-P12)

### Opportunity 10: Extract Selector Parsing Logic
**Location:** `template_resolver.py:772-848` (_parse_selectors - CC: C/13)
**Pattern:** Complex parsing logic with multiple selector types

**Recommended:** Extract into dedicated SelectorParser class with parse_*() methods

**Effort:** Small (~1.5h)
**Priority:** P8

---

### Opportunity 11: Factory for ThemeConfig Creation
**Location:** `theme_loader.py:237-339` (explicit vs implicit theme)
**Pattern:** if/else creating different ThemeConfig types

**Recommended:** Factory pattern with ExplicitThemeFactory and ImplicitThemeFactory

**Effort:** Small (~1h)
**Priority:** P9

---

### Opportunity 12: Strategy for Variation Type Detection
**Location:** `import_resolver.py:367-418` (_analyze_variations)
**Pattern:** Checking dict values to determine multipart vs simple

**Recommended:** Strategy pattern with MultipartAnalyzer and SimpleAnalyzer

**Effort:** Small (~1h)
**Priority:** P10

---

## Summary Table

| # | Pattern | Location | Lines | CC | Effort | Priority | Impact |
|---|---------|----------|-------|----|----|----------|--------|
| 1 | Strategy | import_resolver.py:187-227 | 40 | C | Medium | P2 | High extensibility |
| 2 | Split Class | template_resolver.py | 954 | C | Large | P3 | Reduces god object |
| 3 | Strategy | parser.py:450-594 | 144 | C | Medium | P2 | Eliminates duplication |
| 4 | Factory | inheritance_resolver.py:147-160 | 32 | B | Small | P5 | Clean type detection |
| 5 | Visitor | inheritance_resolver.py:215-351 | 136 | D | Medium | P4 | DRY merge logic |
| 6 | Split Class | parser.py | 831 | B | Large | P4 | Reduces god object |
| 7 | Strategy | import_resolver.py:71-128 | 60 | B | Small | P7 | Clean type handling |
| 8 | Chain/Decorator | validator.py:55-93 | 40 | A | Medium | P7 | Flexible validation |
| 9 | Extract Method | orchestrator.py:134-310 | 176 | D | Small | P6 | Reduces complexity |
| 10 | Extract Class | template_resolver.py:772-848 | 76 | C | Small | P8 | Cleaner parsing |
| 11 | Factory | theme_loader.py:237-339 | 102 | B | Small | P9 | Type safety |
| 12 | Strategy | import_resolver.py:367-418 | 51 | A | Small | P10 | Minor cleanup |

---

## Recommended Implementation Order

### Sprint 1 (High Impact, Medium Effort)
1. **Opportunity 3** - Strategy for ADetailer/ControlNet parsing (P2)
2. **Opportunity 9** - Extract method for orchestrator.resolve() (P6)
3. **Opportunity 4** - Factory for config type detection (P5)

### Sprint 2 (God Objects)
4. **Opportunity 2** - Split TemplateResolver (P3)
5. **Opportunity 6** - Split ConfigParser (P4)

### Sprint 3 (Polish & Extensions)
6. **Opportunity 1** - Strategy for file type loading (P2)
7. **Opportunity 5** - Visitor for config merging (P4)
8. **Opportunities 7-12** - Small refactorings (P7-P10)

---

## Code Quality Metrics

### Current State
- **Files > 500 lines:** 6 files
- **Files > 700 lines:** 3 files (template_resolver, parser, orchestrator)
- **Average CC (critical files):** 10.3 (Grade C)
- **Methods > 50 lines:** ~8 methods
- **Duplicate code:** ~15% (override logic in parser)

### Target State (After Refactoring)
- **Files > 500 lines:** 2 files
- **Files > 700 lines:** 0 files
- **Average CC:** 6.5 (Grade B)
- **Methods > 50 lines:** 2 methods
- **Duplicate code:** <5%

---

## Risk Assessment

**Low Risk:**
- Opportunities 4, 7, 9, 10, 11, 12 (isolated changes)

**Medium Risk:**
- Opportunities 1, 3, 5, 8 (add abstraction layers)

**High Risk:**
- Opportunities 2, 6 (split god objects - requires extensive testing)

**Mitigation:**
- Maintain facade patterns for backward compatibility
- Comprehensive test coverage before refactoring
- Incremental migration (keep old code until tests pass)

---

## Notes

- **All refactorings preserve existing API** (facades used for compatibility)
- **Type hints critical** - mypy strict mode helps catch refactoring errors
- **Test coverage** - Current tests should pass unchanged after refactoring
- **Performance** - Strategy/Factory patterns add negligible overhead (<1%)

**Absolute file paths referenced:**
- `/mnt/d/StableDiffusion/local-sd-generator/packages/sd-generator-cli/sd_generator_cli/templating/resolvers/template_resolver.py`
- `/mnt/d/StableDiffusion/local-sd-generator/packages/sd-generator-cli/sd_generator_cli/templating/loaders/parser.py`
- `/mnt/d/StableDiffusion/local-sd-generator/packages/sd-generator-cli/sd_generator_cli/templating/orchestrator.py`
- `/mnt/d/StableDiffusion/local-sd-generator/packages/sd-generator-cli/sd_generator_cli/templating/resolvers/import_resolver.py`
- `/mnt/d/StableDiffusion/local-sd-generator/packages/sd-generator-cli/sd_generator_cli/templating/resolvers/inheritance_resolver.py`
