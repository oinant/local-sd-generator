# Themable Templates - Technical Documentation

Documentation technique de l'architecture et du fonctionnement interne des Themable Templates.

## Table des matières

- [Architecture Overview](#architecture-overview)
- [Data Models](#data-models)
- [Components](#components)
- [Resolution Algorithm](#resolution-algorithm)
- [Manifest Structure](#manifest-structure)
- [Integration Points](#integration-points)

---

## Architecture Overview

### System Layers

```
┌─────────────────────────────────────────────┐
│            CLI Layer                        │
│  (commands.py, theme commands)              │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         V2Pipeline (Orchestrator)           │
│  Phase 1-7 + Phase 3.5 (Theme Merging)      │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐    ┌──────▼──────────┐
│  ThemeLoader   │    │  ThemeResolver  │
│  - Discovery   │    │  - Merge        │
│  - Load        │    │  - Validate     │
└────────────────┘    └─────────────────┘
        │                     │
        └──────────┬──────────┘
                   │
        ┌──────────▼──────────┐
        │   StyleResolver     │
        │  - Suffix logic     │
        │  - Fallback chain   │
        └─────────────────────┘
```

### Pipeline Flow

```
1. Load Config
   ├─ YamlLoader.load_file()
   └─ ConfigParser.parse_template() or parse_prompt()

2. Validate Config
   └─ ConfigValidator.validate()

3. Resolve Inheritance
   └─ InheritanceResolver.resolve_implements()

3.5. Theme Merging (🆕 Phase)
   ├─ ThemeLoader.load_theme() if theme_name provided
   ├─ ThemeResolver.merge_imports(template, theme, style)
   │  ├─ For each placeholder:
   │  │  ├─ Check if style-sensitive
   │  │  ├─ Try theme override (with style if applicable)
   │  │  ├─ Fallback to template import
   │  │  └─ Fallback to common (style-resolved)
   │  └─ Build import_resolution metadata
   └─ Replace template.imports with merged_imports

4. Resolve Imports
   └─ ImportResolver.resolve_imports()

5. Generate Prompts
   └─ PromptGenerator.generate_prompts()

6. Enrich Manifest
   └─ Add theme_name, style, import_resolution to snapshot
```

---

## Data Models

### TemplateConfig (Extended)

```python
@dataclass
class TemplateConfig(PromptConfig):
    """Extended template config with theme support."""

    version: str
    name: str
    template: str                         # Template with {prompt} placeholder
    source_file: Path

    # 🆕 Theme support
    themable: bool = False                # Can use themes
    style_sensitive: bool = False         # Can use styles
    style_sensitive_placeholders: List[str] = field(default_factory=list)

    # Existing fields
    implements: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    imports: Dict[str, str] = field(default_factory=dict)
    prompts: Dict[str, str] = field(default_factory=dict)
    negative_prompt: str = ''
    generation: Optional[GenerationConfig] = None
```

**Key fields:**
- `themable: true` - Enables theme support
- `style_sensitive: true` - Enables style variants
- `style_sensitive_placeholders` - List of placeholders that vary by style

### ThemeConfig

```python
@dataclass
class ThemeConfig:
    """Theme configuration."""

    name: str                             # Theme name (e.g., "cyberpunk")
    path: Path                            # Path to theme directory
    explicit: bool                        # True if theme.yaml exists
    imports: Dict[str, str]               # Import mappings
    variations: List[str]                 # Available variation categories
```

**Discovery modes:**
1. **Explicit** - Has `theme.yaml` file
2. **Implicit** - Inferred from `{theme}_*.yaml` files

### ImportResolution

```python
@dataclass
class ImportResolution:
    """Metadata about how an import was resolved."""

    source: str                           # "theme" | "template" | "common" | "none"
    override: bool                        # True if theme overrode template
    style_sensitive: bool                 # True if varies by style
    resolved_style: Optional[str] = None  # Style used (if applicable)
```

**Purpose:** Traceability for debugging and manifest

### ResolvedContext (Extended)

```python
@dataclass
class ResolvedContext:
    """Extended context with theme metadata."""

    imports: Dict[str, Dict[str, str]]    # Resolved imports
    chunks: Dict[str, ChunkConfig]
    parameters: Dict[str, Any]
    variation_state: Dict[str, str] = field(default_factory=dict)

    # 🆕 Theme metadata
    style: str = "default"                # Active style
    import_resolution: Dict[str, ImportResolution] = field(default_factory=dict)
```

---

## Components

### ThemeLoader

**Location:** `sd_generator_cli/templating/loaders/theme_loader.py`

**Responsibilities:**
- Discover themes in `configs_dir/themes/`
- Load explicit themes (`theme.yaml`)
- Infer implicit themes (`{theme}_*.yaml`)
- Extract style suffixes from filenames

**Key Methods:**

```python
class ThemeLoader:
    def __init__(self, configs_dir: Path):
        """Initialize with configs directory."""

    def discover_themes(self) -> List[ThemeInfo]:
        """Discover all themes in configs_dir/themes/."""

    def load_theme(self, theme_name: str) -> ThemeConfig:
        """Load a theme by name (explicit or implicit)."""

    def load_explicit_theme(self, theme_dir: Path, theme_name: str) -> ThemeConfig:
        """Load theme from theme.yaml."""

    def load_implicit_theme(self, theme_dir: Path, theme_name: str) -> ThemeConfig:
        """Infer theme from {theme}_*.yaml files."""
```

**Example - Explicit theme loading:**

```yaml
# themes/cyberpunk/theme.yaml
name: cyberpunk
imports:
  Outfit.default:  cyberpunk/cyberpunk_outfit.default.yaml
  Outfit.cartoon:  cyberpunk/cyberpunk_outfit.cartoon.yaml
```

→ `ThemeConfig(name="cyberpunk", imports={...}, explicit=True)`

**Example - Implicit theme loading:**

```
themes/pirates/
├── pirates_haircut.yaml
├── pirates_outfit.yaml
└── pirates_location.yaml
```

→ Inferred:
```python
ThemeConfig(
    name="pirates",
    imports={
        "HairCut": "pirates/pirates_haircut.yaml",
        "Outfit": "pirates/pirates_outfit.yaml",
        "Location": "pirates/pirates_location.yaml"
    },
    explicit=False
)
```

### StyleResolver

**Location:** `sd_generator_cli/templating/resolvers/style_resolver.py`

**Responsibilities:**
- Resolve style-specific file paths
- Replace style suffixes (`.default.yaml` → `.cartoon.yaml`)
- Fallback logic for missing styles

**Key Methods:**

```python
class StyleResolver:
    def resolve_with_style(
        self,
        base_path: str,
        style: str,
        known_styles: List[str]
    ) -> Optional[str]:
        """
        Resolve a file path with style suffix.

        Example:
            base_path = "outfit.default.yaml"
            style = "cartoon"
            → "outfit.cartoon.yaml"
        """
```

**Algorithm:**

1. Extract basename and current style from path
2. Replace current style with target style
3. Check if file exists
4. If not, try fallback to `.default.yaml`
5. Return resolved path or None

### ThemeResolver

**Location:** `sd_generator_cli/templating/resolvers/theme_resolver.py`

**Responsibilities:**
- Merge template + theme imports
- Apply style resolution
- Build import_resolution metadata
- Validate compatibility

**Key Methods:**

```python
class ThemeResolver:
    def __init__(self, configs_dir: Path):
        """Initialize with configs directory."""
        self.style_resolver = StyleResolver(configs_dir)

    def merge_imports(
        self,
        template: TemplateConfig,
        theme: Optional[ThemeConfig],
        style: str
    ) -> Tuple[Dict[str, str], Dict[str, ImportResolution]]:
        """
        Merge template imports with theme overrides.

        Returns:
            (merged_imports, import_resolution_metadata)
        """

    def validate_theme_compatibility(
        self,
        template: TemplateConfig,
        theme: ThemeConfig,
        style: str
    ) -> Dict[str, str]:
        """
        Validate theme compatibility.

        Returns:
            {placeholder: "provided" | "missing" | "fallback"}
        """
```

---

## Resolution Algorithm

### Import Resolution Priority

**Order:** theme → template → common fallback

### Detailed Algorithm

```python
def merge_imports(template, theme, style):
    merged = {}
    metadata = {}

    # Get style-sensitive placeholders
    sensitive = template.style_sensitive_placeholders or []

    for placeholder in template.imports:
        # 1. Check if style-sensitive
        is_style_sensitive = placeholder in sensitive

        # 2. Build key with style suffix if applicable
        if is_style_sensitive:
            import_key = f"{placeholder}.{style}"
        else:
            import_key = placeholder

        # 3. Try theme override first
        if theme and import_key in theme.imports:
            merged[placeholder] = theme.imports[import_key]
            metadata[placeholder] = ImportResolution(
                source="theme",
                override=True,
                style_sensitive=is_style_sensitive,
                resolved_style=style if is_style_sensitive else None
            )

        # 4. Try theme base key (without style)
        elif theme and placeholder in theme.imports:
            merged[placeholder] = theme.imports[placeholder]
            metadata[placeholder] = ImportResolution(
                source="theme",
                override=True,
                style_sensitive=False
            )

        # 5. Fallback to template import
        elif placeholder in template.imports:
            template_path = template.imports[placeholder]

            # Apply style resolution if sensitive
            if is_style_sensitive:
                resolved_path = style_resolver.resolve_with_style(
                    template_path, style
                )
                merged[placeholder] = resolved_path or template_path
            else:
                merged[placeholder] = template_path

            metadata[placeholder] = ImportResolution(
                source="template",
                override=False,
                style_sensitive=is_style_sensitive,
                resolved_style=style if is_style_sensitive else None
            )

        # 6. Try common fallback
        else:
            # Try common/{placeholder}/{placeholder}.{style}.yaml
            common_path = f"common/{placeholder}/{placeholder}.{style}.yaml"
            if file_exists(common_path):
                merged[placeholder] = common_path
                metadata[placeholder] = ImportResolution(
                    source="common",
                    override=False,
                    style_sensitive=True,
                    resolved_style=style
                )

    return merged, metadata
```

### Example Resolution

**Input:**
- Template: `_tpl_teasing.template.yaml` (themable)
- Theme: `cyberpunk`
- Style: `cartoon`

**Template imports:**
```yaml
imports:
  HairCut:     defaults/haircut.yaml
  Outfit:      defaults/outfit.yaml
  Rendering:   common/rendering.default.yaml
```

**Template config:**
```yaml
style_sensitive_placeholders:
  - Outfit
  - Rendering
```

**Theme imports:**
```yaml
# cyberpunk/theme.yaml
imports:
  HairCut:         cyberpunk/cyberpunk_haircut.yaml
  Outfit.cartoon:  cyberpunk/cyberpunk_outfit.cartoon.yaml
  # No Rendering
```

**Resolution:**

| Placeholder | Sensitive? | Key tried | Source | Resolved path |
|-------------|------------|-----------|--------|---------------|
| `HairCut` | ❌ | `HairCut` | theme | `cyberpunk/cyberpunk_haircut.yaml` |
| `Outfit` | ✅ | `Outfit.cartoon` | theme | `cyberpunk/cyberpunk_outfit.cartoon.yaml` |
| `Rendering` | ✅ | `Rendering.cartoon` | common | `common/rendering/rendering.cartoon.yaml` |

**Metadata:**
```python
{
    "HairCut": ImportResolution(
        source="theme",
        override=True,
        style_sensitive=False
    ),
    "Outfit": ImportResolution(
        source="theme",
        override=True,
        style_sensitive=True,
        resolved_style="cartoon"
    ),
    "Rendering": ImportResolution(
        source="common",
        override=False,
        style_sensitive=True,
        resolved_style="cartoon"
    )
}
```

---

## Manifest Structure

### Enriched Manifest

```json
{
  "snapshot": {
    "version": "2.0",
    "timestamp": "2025-10-25T12:00:00",

    "theme_name": "cyberpunk",
    "style": "cartoon",

    "runtime_info": {
      "sd_model_checkpoint": "model.safetensors"
    },

    "resolved_template": {
      "prompt": "...",
      "negative": "..."
    },

    "import_resolution": {
      "HairCut": {
        "source": "theme",
        "override": true,
        "style_sensitive": false
      },
      "Outfit": {
        "source": "theme",
        "override": true,
        "style_sensitive": true,
        "resolved_style": "cartoon"
      },
      "Rendering": {
        "source": "common",
        "override": false,
        "style_sensitive": true,
        "resolved_style": "cartoon"
      }
    },

    "generation_params": {...},
    "api_params": {...},
    "variations": {...}
  },

  "images": [...]
}
```

**Purpose:**
- **Reproducibility** - Reconstruct exact generation
- **Debugging** - Understand which files were used
- **Traceability** - Track theme/style overrides

---

## Integration Points

### V2Pipeline Integration

**File:** `sd_generator_cli/templating/orchestrator.py`

**Phase 3.5 - Theme Merging:**

```python
def resolve(
    self,
    config: PromptConfig,
    theme_name: Optional[str] = None,
    style: str = "default"
) -> tuple[PromptConfig, ResolvedContext]:
    # Phase 3: Resolve inheritance
    resolved_config = self.inheritance_resolver.resolve_implements(config)

    # Phase 3.5: Theme merging (🆕)
    theme: Optional[ThemeConfig] = None
    import_resolution_metadata: Dict[str, Any] = {}

    if is_themable(resolved_config):
        if theme_name and self.theme_loader:
            theme = self.theme_loader.load_theme(theme_name)

        if self.theme_resolver:
            merged_imports, import_resolution_metadata = \
                self.theme_resolver.merge_imports(
                    template=resolved_config,
                    theme=theme,
                    style=style
                )

            # Replace template imports with merged imports
            resolved_config.imports = merged_imports

    # Phase 4: Resolve imports
    resolved_imports = self.import_resolver.resolve_imports(
        resolved_config,
        base_path
    )

    # Build context with theme metadata
    context = ResolvedContext(
        imports=resolved_imports,
        chunks={},
        parameters=merged_params,
        style=style,
        import_resolution=import_resolution_metadata
    )

    return resolved_config, context
```

### CLI Integration

**File:** `sd_generator_cli/cli.py`

**Generate command:**
```python
@app.command(name="generate")
def generate_images(
    template: Optional[Path] = typer.Option(...),
    theme: Optional[str] = typer.Option(None, "--theme"),
    style: str = typer.Option("default", "--style"),
    ...
):
    pipeline = V2Pipeline(configs_dir=str(global_config.configs_dir))

    config = pipeline.load(str(template_path))
    resolved_config, context = pipeline.resolve(config, theme, style)
    prompts = pipeline.generate(resolved_config, context)
```

**Theme commands:**
```python
theme_app = typer.Typer(name="theme")
app.add_typer(theme_app, name="theme")

@theme_app.command(name="list")
def list_themes():
    """List all available themes."""

@theme_app.command(name="show")
def show_theme(name: str):
    """Show theme details."""

@theme_app.command(name="validate")
def validate_theme(template: Path, theme: str, style: str):
    """Validate theme compatibility."""
```

### Manifest Enrichment

**Files:**
- `sd_generator_cli/cli.py:360-374`
- `sd_generator_cli/templating/executor.py:437-451`

**Snapshot creation:**
```python
snapshot = {
    "version": "2.0",
    "timestamp": datetime.now().isoformat(),
    "runtime_info": runtime_info,
    "resolved_template": {...},
    "generation_params": generation_params,
    "api_params": api_params,
    "variations": variations_map,
    # 🆕 Theme metadata
    "theme_name": theme_name,
    "style": style
}
```

---

## Testing

### Unit Tests

**Coverage:** 70 tests, 100% pass

**Files:**
- `test_theme_loader.py` - Theme discovery and loading
- `test_style_resolver.py` - Style resolution logic
- `test_theme_resolver.py` - Merge strategy and validation

### Integration Tests

**File:** `tests/integration/test_themable_templates_integration.py`

**Coverage:**
- V2Pipeline with theme + style
- Theme management commands
- Manifest enrichment
- End-to-end workflows

---

## Performance Considerations

### Theme Discovery

**Optimization:** Cache discovered themes
```python
@cached_property
def themes(self) -> List[ThemeInfo]:
    return self.theme_loader.discover_themes()
```

### File Resolution

**Optimization:** Memoize style resolution
```python
@lru_cache(maxsize=128)
def resolve_with_style(path: str, style: str) -> Optional[str]:
    ...
```

### Import Merging

**Complexity:** O(n) where n = number of placeholders

**Bottleneck:** File existence checks
- Use batch checks when possible
- Cache results during session

---

## Error Handling

### Missing Theme

```python
try:
    theme = theme_loader.load_theme("unknown")
except ValueError as e:
    print(f"❌ Error: Theme 'unknown' not found")
    print(f"   Available themes: {', '.join(list_themes())}")
```

### Missing Style Variant

**Non-blocking** - Fallback chain
```python
# Try: theme → template → common → error
if not resolved_path:
    logger.warning(f"No import found for {placeholder} with style={style}")
    # Continue with None or raise
```

### Invalid theme.yaml

```python
try:
    theme_data = yaml_loader.load_file(theme_yaml)
except yaml.YAMLError as e:
    raise ValueError(f"Invalid theme.yaml: {e}")
```

---

## Future Enhancements

### Planned

- **Multi-theme support** - `--themes cyberpunk,rockstar` (generate both)
- **Theme inheritance** - `extends: base_theme` in theme.yaml
- **Style presets** - Predefined style bundles
- **Theme validation** - Strict mode with completeness check

### Under Consideration

- **Theme marketplace** - Share/download themes
- **Style mixing** - `--style realistic:0.7,cartoon:0.3`
- **Dynamic style detection** - Auto-detect available styles from files

---

## See Also

- [Usage Guide](../usage/themable-templates.md) - Guide utilisateur
- [CLI Reference](../reference/themable-templates.md) - Référence CLI
- [Template System V2](./template-system-v2.md) - Système de templates
