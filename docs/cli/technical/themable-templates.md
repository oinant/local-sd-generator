# Themable Templates - Technical Documentation

Documentation technique de l'architecture et du fonctionnement interne des Themable Templates (Phase 2).

## Table des matières

- [Architecture Overview](#architecture-overview)
- [Data Models](#data-models)
- [Components](#components)
- [Discovery Algorithm](#discovery-algorithm)
- [Resolution Algorithm](#resolution-algorithm)
- [Manifest Structure](#manifest-structure)
- [Integration Points](#integration-points)
- [Performance Considerations](#performance-considerations)
- [Error Handling](#error-handling)

---

## Architecture Overview

### System Layers

```
┌─────────────────────────────────────────────┐
│            CLI Layer                        │
│  (cli.py, list-themes command)              │
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
```

### Pipeline Flow (Phase 2)

```
1. Load Config
   ├─ YamlLoader.load_file()
   └─ ConfigParser.parse_template() or parse_prompt()

2. Validate Config
   └─ ConfigValidator.validate()

3. Resolve Inheritance
   └─ InheritanceResolver.resolve_implements()
       └─ Merges themes: block from inheritance chain

3.5. Theme Discovery & Merging (🆕 Phase 2)
   ├─ If themes: block present AND --theme provided:
   │  ├─ ThemeLoader.discover_available_themes(template, themes_config)
   │  │  ├─ Add explicit themes (highest priority)
   │  │  └─ Add autodiscovered themes if enabled
   │  ├─ Validate theme_name exists in available_themes
   │  ├─ ThemeLoader.load_theme_from_file(theme_path)
   │  └─ Apply theme - COMPLETE substitution of template imports
   │     ├─ Save prompt's explicit imports (final overrides)
   │     ├─ Start with theme imports (replaces template)
   │     └─ Re-apply prompt's explicit imports
   └─ Else if --theme-file provided:
      └─ ThemeLoader.load_theme_from_file(theme_file) - Direct load

4. Resolve Imports
   └─ ImportResolver.resolve_imports()

5. Generate Prompts
   └─ PromptGenerator.generate_prompts()

6. Enrich Manifest
   └─ Add theme_name, style to snapshot
```

---

## Data Models

### ThemeConfigBlock

**File:** `sd_generator_cli/templating/models/theme_models.py`

```python
@dataclass
class ThemeConfigBlock:
    """
    Configuration block for theme discovery and loading in templates.

    This block appears in template YAML files to control theme behavior.
    The presence of this block indicates a template is themable.

    Modes:
    ------
    1. Explicit only (default):
        themes:
          explicit:
            pirates: ./pirates/theme.yaml

    2. Autodiscovery only:
        themes:
          enable_autodiscovery: true

    3. Hybrid (explicit + autodiscovery):
        themes:
          enable_autodiscovery: true
          search_paths: [./themes/, ../shared/]
          explicit:
            custom: ../custom/theme.yaml

    Attributes:
        enable_autodiscovery: Enable automatic theme discovery by scanning directories
        search_paths: Directories to scan for theme.yaml files (relative to template)
        explicit: Manually declared theme name → theme.yaml path mappings
    """
    enable_autodiscovery: bool = False
    search_paths: List[str] = field(default_factory=list)
    explicit: Dict[str, str] = field(default_factory=dict)
```

**Key design decisions:**

1. **No `themable` flag** - Presence of `themes:` block indicates themability
2. **Opt-in autodiscovery** - Disabled by default for predictability
3. **Search paths relative to template** - Allows portable configs
4. **Explicit priority** - Manual declarations override autodiscovered

### ThemeConfig

```python
@dataclass
class ThemeConfig:
    """
    Configuration for a theme.

    A theme is a collection of imports that can be applied to themable templates.
    Themes can be explicit (with theme.yaml) or implicit (inferred from files).

    Attributes:
        name: Theme name (e.g., "cyberpunk", "rockstar")
        path: Path to theme directory
        explicit: True if theme.yaml exists, False if inferred
        imports: Import mappings (may include style suffixes like "Outfit.cartoon")
        variations: List of available variation categories
    """
    name: str
    path: Path
    explicit: bool
    imports: Dict[str, str] = field(default_factory=dict)
    variations: List[str] = field(default_factory=list)
```

**Explicit vs Implicit:**

| Aspect | Explicit | Implicit |
|--------|----------|----------|
| File | `theme.yaml` exists | Inferred from `{theme}-*.yaml` |
| Imports | Declared in YAML | Auto-detected from filenames |
| Styles | Can specify explicitly | Auto-detected from suffixes |
| Validation | Strict | Lenient |

### ImportResolution (Future)

```python
@dataclass
class ImportResolution:
    """
    Metadata about how an import was resolved.

    Tracks the source and context of each import resolution for debugging,
    validation, and manifest generation.

    Attributes:
        source: Where the import came from ("prompt" | "theme" | "template")
        file: Path to resolved file
        type: Category of import ("thematic" | "common")
        override: True if theme overrode template default
        style_sensitive: True if import varies by style
        resolved_style: Style used for resolution (e.g., "cartoon", "realistic")
        note: Optional warning or info message
    """
    source: str  # "prompt" | "theme" | "template"
    file: str
    type: str  # "thematic" | "common"
    override: bool
    style_sensitive: bool = False
    resolved_style: Optional[str] = None
    note: Optional[str] = None
```

**Note:** Currently simplified in Phase 2 - full metadata tracking is future work.

---

## Components

### ThemeLoader

**Location:** `sd_generator_cli/templating/loaders/theme_loader.py`

**Responsibilities:**
- Discover themes based on `ThemeConfigBlock` configuration
- Load explicit themes (`theme.yaml`)
- Infer implicit themes (`{theme}-*.yaml`)
- Extract style suffixes from filenames

**Key Methods:**

#### `discover_available_themes()`

```python
def discover_available_themes(
    self,
    template_source_file: Path,
    themes_config: ThemeConfigBlock
) -> Dict[str, str]:
    """
    Discover all available themes for a template using ThemeConfigBlock.

    Combines explicit themes and autodiscovered themes based on configuration.

    Args:
        template_source_file: Path to the template file (for relative path resolution)
        themes_config: ThemeConfigBlock from template

    Returns:
        Dict mapping theme names to their theme.yaml file paths

    Example:
        >>> themes_cfg = ThemeConfigBlock(
        ...     enable_autodiscovery=True,
        ...     search_paths=['./'],
        ...     explicit={'custom': '../custom/theme.yaml'}
        ... )
        >>> loader.discover_available_themes(Path('template.yaml'), themes_cfg)
        {'custom': '.../custom/theme.yaml', 'pirates': '.../pirates/theme.yaml', ...}
    """
    available: Dict[str, str] = {}
    template_dir = template_source_file.parent

    # 1. Add explicit themes first (highest priority)
    if themes_config.explicit:
        for name, path in themes_config.explicit.items():
            # Resolve relative paths
            if not Path(path).is_absolute():
                resolved = (template_dir / path).resolve()
                available[name] = str(resolved)
            else:
                available[name] = path

    # 2. Add autodiscovered themes if enabled
    if themes_config.enable_autodiscovery:
        search_paths = themes_config.search_paths if themes_config.search_paths else ['.']

        for search_path_str in search_paths:
            # Resolve relative to template file
            if not Path(search_path_str).is_absolute():
                search_path = (template_dir / search_path_str).resolve()
            else:
                search_path = Path(search_path_str)

            if not search_path.exists() or not search_path.is_dir():
                continue

            # Scan for theme.yaml files
            discovered = self._scan_directory_for_themes(search_path)

            # Add discovered themes (explicit themes have priority)
            for name, path in discovered.items():
                if name not in available:
                    available[name] = path

    return available
```

**Algorithm:**
1. Resolve explicit themes (manual declarations)
2. If autodiscovery enabled, scan search_paths
3. Merge results (explicit wins on conflicts)

#### `_scan_directory_for_themes()`

```python
def _scan_directory_for_themes(self, directory: Path) -> Dict[str, str]:
    """
    Scan a directory for theme.yaml files.

    Looks for immediate subdirectories containing theme.yaml.

    Args:
        directory: Directory to scan

    Returns:
        Dict mapping theme names to theme.yaml file paths

    Example:
        Directory structure:
            ./
            ├── pirates/
            │   └── theme.yaml
            ├── cyberpunk/
            │   └── theme.yaml
            └── rockstar/
                └── theme.yaml

        Returns:
            {'pirates': './pirates/theme.yaml', 'cyberpunk': ...}
    """
    discovered: Dict[str, str] = {}

    try:
        for item in directory.iterdir():
            if not item.is_dir():
                continue

            theme_file = item / "theme.yaml"
            if theme_file.exists():
                theme_name = item.name
                discovered[theme_name] = str(theme_file)

    except (OSError, PermissionError):
        # Silently skip directories we can't read
        pass

    return discovered
```

**Design decisions:**
- Only immediate subdirectories (no recursive scan)
- Theme name = directory name
- Graceful failure on permission errors

#### `load_explicit_theme()`

```python
def load_explicit_theme(self, theme_dir: Path, theme_name: str) -> ThemeConfig:
    """
    Load an explicit theme from theme.yaml.

    Args:
        theme_dir: Path to theme directory
        theme_name: Theme name

    Returns:
        ThemeConfig with explicit imports

    Example theme.yaml:
        ```yaml
        type: theme_config
        version: "1.0"
        imports:
          Ambiance: cyberpunk/cyberpunk-ambiance.yaml
          Outfit.cartoon: cyberpunk/cyberpunk-outfit.cartoon.yaml
        ```
    """
    theme_yaml = theme_dir / "theme.yaml"

    with open(theme_yaml, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    imports = data.get('imports', {})

    # Extract variation categories (base placeholder names)
    variations = self._extract_variations_from_imports(imports)

    return ThemeConfig(
        name=theme_name,
        path=theme_dir,
        explicit=True,
        imports=imports,
        variations=variations
    )
```

#### `load_implicit_theme()`

```python
def load_implicit_theme(self, theme_dir: Path, theme_name: str) -> Optional[ThemeConfig]:
    """
    Infer theme from {theme}-*.yaml files.

    Scans directory for files matching pattern:
    - {theme}-ambiance.yaml → Ambiance
    - {theme}-outfit.cartoon.yaml → Outfit.cartoon
    - {theme}-locations.yaml → Locations

    Args:
        theme_dir: Path to theme directory
        theme_name: Theme name

    Returns:
        ThemeConfig with inferred imports, or None if no matching files

    Example:
        Directory: themes/rockstar/
        Files:
        - rockstar-ambiance.yaml
        - rockstar-outfit.yaml
        - rockstar-outfit.cartoon.yaml

        Result:
        imports = {
            "Ambiance": "rockstar/rockstar-ambiance.yaml",
            "Outfit": "rockstar/rockstar-outfit.yaml",
            "Outfit.cartoon": "rockstar/rockstar-outfit.cartoon.yaml"
        }
    """
    prefix = f"{theme_name}-"  # IMPORTANT: Use dash (Phase 2 convention)
    imports: Dict[str, str] = {}

    # Scan for {theme}-*.yaml files
    for yaml_file in theme_dir.glob(f"{prefix}*.yaml"):
        # Extract placeholder name from filename
        # Example: "rockstar-outfit.cartoon.yaml" → "outfit.cartoon"
        relative_name = yaml_file.stem[len(prefix):]  # "outfit.cartoon"

        # Convert to PascalCase placeholder
        # "outfit.cartoon" → "Outfit.cartoon"
        # "cyberpunk-ambiance" → "Ambiance"
        placeholder = self._filename_to_placeholder(relative_name)

        # Store relative path from configs_dir
        relative_path = f"{theme_name}/{yaml_file.name}"
        imports[placeholder] = relative_path

    if not imports:
        return None

    variations = self._extract_variations_from_imports(imports)

    return ThemeConfig(
        name=theme_name,
        path=theme_dir,
        explicit=False,
        imports=imports,
        variations=variations
    )
```

**Filename convention (Phase 2):**
- Format: `{theme}-{placeholder}.yaml`
- Style suffix: `{theme}-{placeholder}.{style}.yaml`
- Separator: **dash** (not underscore)
- Examples: `pirates-haircut.yaml`, `cyberpunk-outfit.cartoon.yaml`

#### `_filename_to_placeholder()`

```python
def _filename_to_placeholder(self, filename: str) -> str:
    """
    Convert filename to placeholder name.

    Handles:
    - Basic: "ambiance" → "Ambiance"
    - Style suffix: "outfit.cartoon" → "Outfit.cartoon"
    - Multi-word: "hair-color" → "HairColor"

    Args:
        filename: Filename without theme prefix (e.g., "outfit.cartoon")

    Returns:
        PascalCase placeholder name

    Examples:
        >>> _filename_to_placeholder("ambiance")
        'Ambiance'
        >>> _filename_to_placeholder("outfit.cartoon")
        'Outfit.cartoon'
        >>> _filename_to_placeholder("hair-color.realistic")
        'HairColor.realistic'
    """
    # Split on dot to separate base from style suffix
    parts = filename.split('.')
    base = parts[0]
    suffix = '.' + '.'.join(parts[1:]) if len(parts) > 1 else ''

    # Convert base to PascalCase (handle dashes)
    # "hair-color" → "HairColor"
    words = base.split('-')
    pascal_base = ''.join(word.capitalize() for word in words)

    return pascal_base + suffix
```

**Design:** Preserves style suffixes while converting base to PascalCase.

### V2Pipeline Integration

**Location:** `sd_generator_cli/templating/orchestrator.py`

**Phase 3.5 - Theme Resolution:**

```python
def resolve(
    self,
    config: PromptConfig,
    theme_name: Optional[str] = None,
    theme_file: Optional[Path] = None,
    style: str = "default"
) -> tuple[PromptConfig, ResolvedContext]:
    # Phase 3: Resolve inheritance chain
    resolved_config = self.inheritance_resolver.resolve_implements(config)

    # Phase 3.5: Theme resolution (if theme specified)
    theme: Optional[ThemeConfig] = None
    import_sources: Dict[str, str] = {}

    if theme_name or theme_file:
        if not self.theme_resolver or not self.theme_loader:
            raise ValueError("Theme support requires configs_dir to be set")

        # Load theme (either from theme_file or by discovering from themes block)
        if theme_file:
            # Direct theme file path provided
            theme = self.theme_loader.load_theme_from_file(str(theme_file))
        elif theme_name:
            # Theme name provided - discover available themes from template
            if not resolved_config.themes:
                raise ValueError(
                    f"❌ No 'themes:' block found in {resolved_config.name}\n"
                    f"💡 Use --theme-file to specify theme path directly, or add a themes: block"
                )

            # Discover all available themes (explicit + autodiscovered)
            available_themes = self.theme_loader.discover_available_themes(
                resolved_config.source_file,
                resolved_config.themes
            )

            if theme_name not in available_themes:
                available_str = ', '.join(sorted(available_themes.keys())) if available_themes else '(none)'
                raise ValueError(
                    f"❌ Theme '{theme_name}' not found\n"
                    f"💡 Available themes: {available_str}\n"
                    f"   Or use --theme-file to load a custom theme"
                )

            # Load theme from discovered path
            theme_path = available_themes[theme_name]
            theme = self.theme_loader.load_theme_from_file(theme_path)

        # Apply theme - COMPLETE substitution for thematic variations
        from copy import deepcopy
        resolved_config = deepcopy(resolved_config)

        # Save prompt's explicit imports (from the original config before template merge)
        prompt_explicit_imports = config.imports.copy() if hasattr(config, 'imports') else {}

        # Start with theme imports (complete substitution of template)
        resolved_config.imports = theme.imports.copy()

        # Re-apply prompt's explicit imports as final overrides
        resolved_config.imports.update(prompt_explicit_imports)

        # Track sources for manifest
        for placeholder in theme.imports.keys():
            import_sources[placeholder] = f"theme:{theme.name}"
        for placeholder in prompt_explicit_imports.keys():
            import_sources[placeholder] = f"prompt:{config.source_file.name}"

    # Phase 4: Resolve imports
    base_path = config.source_file.parent
    resolved_imports = self.import_resolver.resolve_imports(
        resolved_config,
        base_path
    )

    # Build resolved context
    context = ResolvedContext(
        imports=resolved_imports,
        chunks={},
        parameters=merged_params,
        style=style,
        import_sources=import_sources
    )

    return resolved_config, context
```

**Key algorithm steps:**

1. **Discovery phase** (if `--theme` provided):
   - Check `themes:` block exists
   - Call `discover_available_themes()` with `ThemeConfigBlock`
   - Validate theme_name in available_themes
   - Load theme from discovered path

2. **Substitution phase**:
   - Save prompt's explicit imports
   - Replace template imports with theme imports
   - Re-apply prompt overrides (highest priority)

3. **Priority order:** prompt > theme > template

---

## Discovery Algorithm

### Hybrid Discovery Flow

```
Input: ThemeConfigBlock + template_source_file

┌─────────────────────────────────────────┐
│  1. Initialize available_themes dict    │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│  2. Add explicit themes (with priority) │
│     - Resolve relative paths            │
│     - Store in available_themes         │
└───────────────┬─────────────────────────┘
                │
         ┌──────▼──────┐
         │ Autodiscovery│
         │   enabled?   │
         └──┬───────┬───┘
           NO       YES
            │       │
            │   ┌───▼────────────────────────┐
            │   │ 3. For each search_path:   │
            │   │    - Resolve relative path │
            │   │    - Scan for theme.yaml   │
            │   │    - Add if not duplicate  │
            │   └────────────────────────────┘
            │
┌───────────▼─────────────────────────────┐
│  4. Return available_themes             │
│     (explicit + autodiscovered)         │
└─────────────────────────────────────────┘
```

### Example Scenarios

#### Scenario 1: Explicit only

```yaml
themes:
  explicit:
    pirates: ./themes/pirates/theme.yaml
    cyberpunk: ../shared/cyberpunk/theme.yaml
```

**Result:** Only `pirates` and `cyberpunk` available.

#### Scenario 2: Autodiscovery only

```yaml
themes:
  enable_autodiscovery: true
  search_paths: [./themes/]
```

**Result:** All themes in `./themes/` with `theme.yaml` discovered.

#### Scenario 3: Hybrid

```yaml
themes:
  enable_autodiscovery: true
  search_paths: [./themes/, ../shared/]
  explicit:
    custom: ~/my-themes/custom/theme.yaml
```

**Result:**
- `custom` from explicit (highest priority)
- All themes in `./themes/` (autodiscovered)
- All themes in `../shared/` (autodiscovered)
- If `custom` also exists in search paths, explicit wins

---

## Resolution Algorithm

### Import Resolution Priority

**Order:** prompt > theme > template

### Detailed Algorithm

```python
# Simplified Phase 2 algorithm (full resolution is in Phase 4)

def apply_theme(template_config, theme_config, prompt_explicit_imports):
    """
    Apply theme to template with proper priority.

    Priority:
    1. Prompt explicit imports (highest)
    2. Theme imports
    3. Template defaults (lowest)
    """

    # Start with theme imports (replaces template)
    merged_imports = theme_config.imports.copy()

    # Apply prompt overrides (highest priority)
    merged_imports.update(prompt_explicit_imports)

    return merged_imports
```

**Phase 2 simplification:**
- No style resolution yet (simplified)
- Complete substitution (no partial merge)
- Prompt overrides always win

### Example Resolution

**Input:**
- Template: `_tpl_teasing.template.yaml`
- Theme: `cyberpunk`
- Prompt: `teasing-pirates.prompt.yaml`

**Template imports:**
```yaml
imports:
  HairCut:     defaults/haircut.yaml
  Outfit:      defaults/outfit.yaml
  Rendering:   common/rendering.yaml
```

**Theme imports:**
```yaml
# cyberpunk/theme.yaml
imports:
  HairCut:     cyberpunk/cyberpunk-haircut.yaml
  Outfit:      cyberpunk/cyberpunk-outfit.yaml
  # No Rendering
```

**Prompt imports:**
```yaml
# teasing-pirates.prompt.yaml
imports:
  Rendering: custom/my_rendering.yaml
```

**Resolution:**

| Placeholder | Prompt? | Theme? | Template? | Final Resolution |
|-------------|---------|--------|-----------|------------------|
| `HairCut` | ❌ | ✅ | ✅ | `cyberpunk/cyberpunk-haircut.yaml` (theme) |
| `Outfit` | ❌ | ✅ | ✅ | `cyberpunk/cyberpunk-outfit.yaml` (theme) |
| `Rendering` | ✅ | ❌ | ✅ | `custom/my_rendering.yaml` (prompt) |

**Import sources tracking:**
```python
{
    "HairCut": "theme:cyberpunk",
    "Outfit": "theme:cyberpunk",
    "Rendering": "prompt:teasing-pirates.prompt.yaml"
}
```

---

## Manifest Structure

### Enriched Manifest (Phase 2)

```json
{
  "snapshot": {
    "version": "2.0",
    "timestamp": "2025-10-29T12:00:00",

    "theme_name": "cyberpunk",
    "style": "default",

    "runtime_info": {
      "sd_model_checkpoint": "model.safetensors"
    },

    "resolved_template": {
      "prompt": "...",
      "negative": "..."
    },

    "generation_params": {
      "mode": "random",
      "seed_mode": "progressive",
      "base_seed": 42,
      "num_images": 100
    },

    "api_params": {...},
    "variations": {...}
  },

  "images": [
    {
      "filename": "session_0001.png",
      "seed": 42,
      "prompt": "...",
      "negative_prompt": "...",
      "applied_variations": {
        "HairCut": "neon mohawk",
        "Outfit": "cybersuit"
      }
    }
  ]
}
```

**Purpose:**
- **Reproducibility** - Reconstruct exact generation
- **Traceability** - Know which theme/style was used
- **Debugging** - Understand resolution choices

---

## Integration Points

### CLI Integration

**File:** `sd_generator_cli/cli.py`

#### `sdgen list-themes` command

```python
@app.command(name="list-themes")
def list_themes(
    template: str = typer.Option(
        ...,
        "-t", "--template",
        help="Path to template file to discover themes for",
    ),
    configs_dir: Optional[Path] = typer.Option(
        None,
        "--configs-dir",
        help="Configs directory (overrides global config)",
    ),
):
    """
    List available themes for a themable template with resolved file paths.

    Shows:
    - Discovered themes (explicit + autodiscovered)
    - Import mappings for each theme
    - Missing files highlighted in red
    - Source of each import (explicit/autodiscovered)
    """
    # Load template
    pipeline = V2Pipeline(configs_dir=configs_dir)
    config = pipeline.load(str(template_path))

    # Resolve inheritance to get final themes config
    config = pipeline.inheritance_resolver.resolve_implements(config)

    # Check if template has themes: block
    if not config.themes:
        console.print(f"[yellow]⚠ Template '{config.name}' is not themable[/yellow]")
        console.print("💡 Add a 'themes:' block to make it themable")
        raise typer.Exit(code=0)

    # Discover available themes
    theme_loader = ThemeLoader(configs_dir)
    available_themes = theme_loader.discover_available_themes(
        config.source_file,
        config.themes
    )

    if not available_themes:
        console.print(f"[yellow]No themes found for template '{config.name}'[/yellow]")
        if config.themes.enable_autodiscovery:
            search_paths = config.themes.search_paths or ['.']
            console.print(f"💡 Searched in: {', '.join(search_paths)}")
        raise typer.Exit(code=0)

    # Display themes with rich formatting
    for theme_name in sorted(available_themes.keys()):
        theme_path = available_themes[theme_name]
        is_explicit = theme_name in (config.themes.explicit or {})
        source_label = "explicit" if is_explicit else "autodiscovered"

        # Load theme to get imports
        theme = theme_loader.load_theme_from_file(theme_path)

        # Display theme tree with imports
        # ... (rich formatting)
```

#### `sdgen generate` with themes

```python
@app.command(name="generate")
def generate_images(
    template: Optional[Path] = typer.Option(...),
    theme: Optional[str] = typer.Option(None, "--theme"),
    theme_file: Optional[Path] = typer.Option(None, "--theme-file"),
    style: str = typer.Option("default", "--style"),
    ...
):
    # Validate theme options (mutually exclusive)
    if theme and theme_file:
        console.print("[red]✗ Cannot use both --theme and --theme-file[/red]")
        raise typer.Exit(code=1)

    # Initialize V2 Pipeline
    pipeline = V2Pipeline(configs_dir=str(global_config.configs_dir))

    # Load and process template
    config = pipeline.load(str(template_path))
    resolved_config, context = pipeline.resolve(config, theme, theme_file, style)
    prompts = pipeline.generate(resolved_config, context)

    # ... (generation)
```

### Manifest Enrichment

**File:** `sd_generator_cli/cli.py:360-374`

```python
# Create snapshot
snapshot = {
    "version": "2.0",
    "timestamp": datetime.now().isoformat(),
    "runtime_info": runtime_info,
    "resolved_template": {
        "prompt": resolved_config.template,
        "negative": resolved_config.negative_prompt or ''
    },
    "generation_params": generation_params,
    "api_params": api_params,
    "variations": variations_map,
    # Themable Templates metadata (Phase 2)
    "theme_name": theme_name,
    "style": style
}
```

---

## Performance Considerations

### Theme Discovery

**Optimization:** Discovery is done once per template load

```python
# Discovery happens during resolve() phase
available_themes = self.theme_loader.discover_available_themes(
    template_source_file,
    themes_config
)
# Result is NOT cached (stateless)
```

**Complexity:** O(n) where n = number of directories in search_paths

**Bottleneck:** File system operations (iterdir, exists checks)

### File Resolution

**Optimization:** Paths are resolved relative to template file

```python
# Relative path resolution (efficient)
if not Path(path).is_absolute():
    resolved = (template_dir / path).resolve()
```

**Caching:** Not implemented in Phase 2 (stateless design)

### Import Merging

**Complexity:** O(m) where m = number of placeholders

```python
# Simple dict operations (fast)
merged_imports = theme.imports.copy()
merged_imports.update(prompt_explicit_imports)
```

**Bottleneck:** Dict copy operations (negligible for typical sizes)

---

## Error Handling

### Missing themes: block

```python
if not resolved_config.themes:
    raise ValueError(
        f"❌ No 'themes:' block found in {resolved_config.name}\n"
        f"💡 Use --theme-file to specify theme path directly, or add a themes: block to your template"
    )
```

**User action:** Add `themes:` block or use `--theme-file`

### Theme not found

```python
if theme_name not in available_themes:
    available_str = ', '.join(sorted(available_themes.keys())) if available_themes else '(none)'
    raise ValueError(
        f"❌ Theme '{theme_name}' not found\n"
        f"💡 Available themes: {available_str}\n"
        f"   Or use --theme-file to load a custom theme"
    )
```

**User action:** Use `sdgen list-themes` to see available themes

### Invalid theme.yaml

```python
try:
    data = yaml.safe_load(f)
except yaml.YAMLError as e:
    raise ValueError(f"Invalid theme.yaml: {e}")
```

**User action:** Fix YAML syntax in theme.yaml

### Cannot use both --theme and --theme-file

```python
if theme and theme_file:
    console.print("[red]✗ Cannot use both --theme and --theme-file[/red]")
    console.print("\n[yellow]Use --theme for themes defined in the template, or --theme-file for custom theme files[/yellow]")
    raise typer.Exit(code=1)
```

**User action:** Choose one option only

---

## Future Enhancements

### Planned (Phase 3+)

- **Style resolution** - Full support for style variants with fallback chain
- **Import resolution metadata** - Complete `ImportResolution` tracking
- **Theme validation** - Strict mode with completeness checks
- **Multi-theme support** - `--themes cyberpunk,rockstar` (generate both)

### Under Consideration

- **Theme inheritance** - `extends: base_theme` in theme.yaml
- **Theme marketplace** - Share/download themes
- **Theme versioning** - Semantic versioning for themes
- **Dynamic theme detection** - Auto-detect compatible themes

---

## Testing

### Unit Tests

**Coverage:** 70+ tests, 100% pass

**Files:**
- `test_theme_loader.py` - Theme discovery and loading
- `test_theme_models.py` - Data models validation
- `test_v2pipeline_themes.py` - Pipeline integration

### Integration Tests

**File:** `tests/integration/test_themable_templates_integration.py`

**Coverage:**
- V2Pipeline with theme + style
- Theme discovery (explicit + autodiscovered)
- CLI commands (`list-themes`, `generate --theme`)
- Manifest enrichment
- End-to-end workflows

### Test Scenarios

```python
def test_autodiscovery_only():
    """Test pure autodiscovery mode."""
    themes_config = ThemeConfigBlock(
        enable_autodiscovery=True,
        search_paths=['./themes/']
    )
    available = loader.discover_available_themes(template_path, themes_config)
    assert 'pirates' in available
    assert 'cyberpunk' in available

def test_hybrid_mode():
    """Test explicit + autodiscovery."""
    themes_config = ThemeConfigBlock(
        enable_autodiscovery=True,
        search_paths=['./themes/'],
        explicit={'custom': '../custom/theme.yaml'}
    )
    available = loader.discover_available_themes(template_path, themes_config)
    assert 'custom' in available  # Explicit
    assert 'pirates' in available  # Autodiscovered

def test_explicit_priority():
    """Test explicit themes override autodiscovered."""
    themes_config = ThemeConfigBlock(
        enable_autodiscovery=True,
        search_paths=['./themes/'],
        explicit={'pirates': '../custom/pirates.yaml'}  # Override
    )
    available = loader.discover_available_themes(template_path, themes_config)
    assert available['pirates'] == '../custom/pirates.yaml'  # Explicit wins
```

---

## See Also

- [Usage Guide](../usage/themable-templates.md) - Guide utilisateur complet
- [CLI Reference](../reference/themable-templates.md) - Référence CLI
- [Template System V2](./template-system-spec.md) - Système de templates
- [Variation Files](../usage/variation-files.md) - Format des fichiers de variations
