# CLI Architecture

**Technical overview of the CLI module structure and data flow.**

---

## Module Structure

```
CLI/
├── generator_cli.py              # Main CLI entry point (Phase 3 - TODO)
├── image_variation_generator.py  # Core generator class
├── variation_loader.py           # Variation file parsing
├── sdapi_client.py              # Stable Diffusion API client
│
├── config/                       # Configuration system (Phase 2 ✅)
│   ├── __init__.py
│   ├── config_schema.py          # JSON schema & validation
│   ├── config_loader.py          # Load & validate JSON configs
│   ├── config_selector.py        # Interactive selection (Phase 3 - TODO)
│   └── global_config.py          # Global config (.sdgen_config.json)
│
├── output/                       # Output management (Phase 1 ✅)
│   ├── __init__.py
│   ├── output_namer.py           # File/folder naming
│   └── metadata_generator.py     # JSON metadata export
│
├── execution/                    # Execution engine (Phase 3 - TODO)
│   ├── __init__.py
│   └── json_generator.py         # JSON-driven generation
│
└── checkpoint/                   # Future module (Phase 4 ⏸️)
    ├── __init__.py
    └── checkpoint_manager.py     # Checkpoint switching
```

---

## Component Interactions

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Input                               │
│  • Python script with ImageVariationGenerator                   │
│  • JSON config file (Phase 3)                                   │
│  • CLI arguments (Phase 3)                                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Configuration Loading                         │
│  • config_loader.py: Load & validate JSON                       │
│  • global_config.py: Load global settings                       │
│  • config_schema.py: Schema validation                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Variation Loading                              │
│  • variation_loader.py: Parse variation files                   │
│  • Extract placeholders from prompt template                    │
│  • Load files, expand nested variations                         │
│  • Apply limits, indices, priorities                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              ImageVariationGenerator                            │
│  • Create combinations (combinatorial/random)                   │
│  • Generate session folder name (output_namer.py)               │
│  • Iterate through combinations                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Image Generation                               │
│  • sdapi_client.py: Call Stable Diffusion API                   │
│  • Generate image with resolved prompt                          │
│  • Save image with generated filename (output_namer.py)         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Metadata Export                                │
│  • metadata_generator.py: Generate metadata JSON                │
│  • Save to session folder                                       │
│  • Legacy session_config.txt (deprecated)                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. ImageVariationGenerator

**File:** `image_variation_generator.py`

**Responsibilities:**
- Main orchestrator for generation runs
- Manages prompt template and placeholders
- Creates combinations (combinatorial/random modes)
- Coordinates with API client for image generation
- Handles session management and output

**Key Methods:**
```python
class ImageVariationGenerator:
    def __init__(
        prompt_template: str,
        negative_prompt: str,
        variation_files: Dict[str, Union[str, List[str]]],
        seed: int = -1,
        generation_mode: str = "combinatorial",
        seed_mode: str = "progressive",
        max_images: int = -1,
        session_name: str = None,
        filename_keys: List[str] = None,
        # ... other parameters
    )

    def run() -> None:
        """Main execution: load variations, generate images, export metadata."""

    def _load_variations(self) -> Dict[str, Dict]:
        """Load variation files using variation_loader."""

    def _create_combinations(self) -> List[Dict]:
        """Create combinatorial or random combinations."""

    def _generate_image(self, prompt: str, seed: int) -> bytes:
        """Call SD API to generate image."""
```

**Design Decisions:**
- Backward compatible: all new parameters are optional
- Self-contained: can be used without JSON configs
- Extensible: easy to add new generation modes

---

### 2. variation_loader

**File:** `variation_loader.py`

**Responsibilities:**
- Parse variation files (multiple formats)
- Extract placeholders from prompt templates
- Expand nested variations `{|option1|option2}`
- Apply placeholder options (limits, indices, priorities)
- Support multiple files per placeholder

**Key Functions:**
```python
def load_variations_from_file(
    file_path: str,
    encoding: str = "utf-8"
) -> Dict[str, str]:
    """Load single variation file, expand nested variations."""

def load_variations_for_placeholders(
    prompt_template: str,
    variation_files: Dict[str, Union[str, List[str]]]
) -> Dict[str, Dict]:
    """Load only variations needed by placeholders in template."""

def extract_placeholders_with_limits(
    template: str
) -> Dict[str, PlaceholderInfo]:
    """Parse placeholders with syntax: {Name:N}, {Name:#|1|5}, {Name:$P}"""

def expand_nested_variations(
    variation_value: str
) -> List[str]:
    """Expand {|opt1|opt2} syntax into multiple variations."""

def create_random_combinations(
    variations_dict: Dict[str, Dict],
    num_combinations: int
) -> List[Dict]:
    """Generate N random unique combinations."""
```

**Supported Formats:**
```
# Format 1: key→value
happy→smiling, cheerful

# Format 2: number→value
1→front view

# Format 3: value only
realistic style
```

**Nested Variations:**
```
base,{|modifier1|modifier2}
→ Expands to: base, base,modifier1, base,modifier2
```

---

### 3. config System (Phase 2)

**Files:** `config/config_schema.py`, `config/config_loader.py`, `config/global_config.py`

**Responsibilities:**
- Define JSON configuration schema
- Load and validate JSON config files
- Provide clear error messages for invalid configs
- Manage global configuration file

**Key Classes:**
```python
@dataclass
class GenerationConfig:
    """JSON config schema as dataclass."""
    version: str
    name: Optional[str]
    description: Optional[str]
    model: ModelConfig
    prompt: PromptConfig
    variations: Dict[str, str]
    generation: GenerationSettings
    parameters: GenerationParameters
    output: OutputConfig

class ConfigLoader:
    """Load and validate JSON configs."""

    def load_config_from_file(path: Path) -> GenerationConfig:
        """Load JSON, validate schema, check files."""

    def validate_config(config: GenerationConfig) -> List[ValidationError]:
        """Comprehensive validation with clear error messages."""
```

**Validation Rules:**
- Required fields present
- Type validation (str, int, float, dict, list)
- Enum validation (generation modes, seed modes)
- File path validation (existence, readability)
- Placeholder validation (all in template have variations)

---

### 4. output System (Phase 1)

**Files:** `output/output_namer.py`, `output/metadata_generator.py`

**Responsibilities:**
- Generate session folder names
- Generate image filenames with variation keys
- Export structured JSON metadata
- Maintain backward compatibility

**Key Functions:**
```python
# output_namer.py
def generate_session_folder_name(
    timestamp: str,
    session_name: Optional[str],
    filename_keys: List[str],
    variations_sample: Dict[str, str]
) -> str:
    """Generate folder name: {timestamp}_{name_components}"""

def generate_image_filename(
    index: int,
    variation_dict: Dict[str, str],
    filename_keys: List[str]
) -> str:
    """Generate filename: {index:03d}_{key1}-{value1}_...png"""

def sanitize_filename_component(value: str) -> str:
    """Convert to camelCase, remove special chars."""

# metadata_generator.py
def generate_metadata_dict(
    config: GenerationConfig,
    runtime_info: Dict,
    variations_loaded: Dict
) -> Dict:
    """Generate complete metadata structure."""

def save_metadata_json(
    metadata: Dict,
    output_folder: Path
) -> None:
    """Save pretty-printed JSON metadata."""
```

**Filename Examples:**
```
# Without filename_keys
001.png, 002.png, 003.png

# With filename_keys=["Expression", "Angle"]
001_Expression-Smiling_Angle-Front.png
002_Expression-Smiling_Angle-Side.png
003_Expression-Sad_Angle-Front.png
```

---

### 5. sdapi_client

**File:** `sdapi_client.py`

**Responsibilities:**
- Interface with Stable Diffusion WebUI API
- Send txt2img requests
- Handle API responses and errors
- Manage batch generation

**Key Functions:**
```python
def generate_image(
    prompt: str,
    negative_prompt: str,
    seed: int,
    width: int,
    height: int,
    steps: int,
    cfg_scale: float,
    sampler: str,
    batch_size: int = 1,
    batch_count: int = 1,
    api_url: str = "http://127.0.0.1:7860"
) -> List[bytes]:
    """Call SD API to generate images."""

def get_available_samplers(api_url: str) -> List[str]:
    """Query available samplers."""

def get_available_models(api_url: str) -> List[str]:
    """Query available checkpoints."""
```

---

## Data Structures

### Variation Dictionary

```python
{
    "Expression": {
        "happy": "smiling, cheerful expression",
        "sad": "sad, melancholic look",
        "angry": "angry, frowning"
    },
    "Angle": {
        "front": "front view",
        "side": "side view, profile",
        "back": "back view"
    }
}
```

### Combination

```python
{
    "Expression": "smiling, cheerful expression",
    "Angle": "front view"
}
```

### PlaceholderInfo

```python
@dataclass
class PlaceholderInfo:
    name: str                    # "Expression"
    limit: Optional[int]         # 5 from {Expression:5}
    indices: Optional[List[int]] # [1, 5, 22] from {Expression:#|1|5|22}
    priority: Optional[int]      # 10 from {Expression:$10}
    suppress: bool               # True from {Expression:0}
```

---

## Generation Flow Details

### Combinatorial Mode

```python
def _create_combinations_combinatorial(
    variations_dict: Dict[str, Dict],
    placeholder_priorities: Dict[str, int]
) -> List[Dict]:
    """
    1. Sort placeholders by priority (ascending)
    2. Create nested loops in priority order
    3. Generate all combinations
    """
    # Example: {Outfit:$1}, {Angle:$10}, {Expression:$20}
    # Loop order: Outfit (outer) → Angle → Expression (inner)

    combinations = []
    for outfit in outfits:
        for angle in angles:
            for expression in expressions:
                combinations.append({
                    "Outfit": outfit,
                    "Angle": angle,
                    "Expression": expression
                })
    return combinations
```

### Random Mode

```python
def _create_combinations_random(
    variations_dict: Dict[str, Dict],
    max_images: int
) -> List[Dict]:
    """
    1. Calculate total possible combinations
    2. Generate N random unique combinations
    3. Ensure no duplicates
    """
    import random

    combinations = set()
    while len(combinations) < max_images:
        combo = {
            placeholder: random.choice(list(variations.values()))
            for placeholder, variations in variations_dict.items()
        }
        # Convert dict to hashable tuple for set uniqueness
        combinations.add(tuple(sorted(combo.items())))

    return [dict(c) for c in combinations]
```

---

## Configuration System Details

### Global Config Search Order

1. `.sdgen_config.json` in project root
2. `~/.sdgen_config.json` in user home
3. Default values if not found

### Config Validation Pipeline

```
1. JSON Parsing
   ↓
2. Schema Validation (required fields, types)
   ↓
3. Enum Validation (generation modes, seed modes)
   ↓
4. File Path Validation (existence, readability)
   ↓
5. Placeholder Validation (template ↔ variations match)
   ↓
6. Custom Validation (numeric ranges, sampler availability)
   ↓
7. GenerationConfig object created
```

**Error Example:**
```
ValidationError: Placeholder 'Lighting' in prompt template has no corresponding variation file.

Prompt template: "portrait, {Expression}, {Angle}, {Lighting}, beautiful"
Found placeholders: ['Expression', 'Angle', 'Lighting']
Defined variations: ['Expression', 'Angle']

Solution: Add "Lighting" to variations object or remove from template.
```

---

## Output System Details

### Session Folder Naming Logic

```python
def generate_session_folder_name(timestamp, session_name, filename_keys, variations_sample):
    if session_name:
        # Use custom session name
        return f"{timestamp}_{session_name}"
    elif filename_keys:
        # Use first value of each filename_key
        components = [
            sanitize_filename_component(variations_sample[key])
            for key in filename_keys
        ]
        return f"{timestamp}_{'_'.join(components)}"
    else:
        # Use timestamp only
        return timestamp
```

**Examples:**
```
# With session_name="anime_test"
20251001_143052_anime_test

# With filename_keys=["Expression", "Angle"], variations_sample={"Expression": "smiling", "Angle": "front view"}
20251001_143052_smiling_frontView

# No session_name, no filename_keys
20251001_143052
```

### Filename Sanitization

```python
def sanitize_filename_component(value: str) -> str:
    """
    Convert to camelCase format:
    1. Remove leading/trailing whitespace
    2. Split on spaces, hyphens, underscores
    3. Capitalize each word except first
    4. Join without separators
    5. Remove any remaining special characters
    """
    # "front view" → "frontView"
    # "wide angle shot" → "wideAngleShot"
    # "DPM++ 2M Karras" → "dpm2mKarras"
```

---

## Testing Strategy

### Unit Tests

- **variation_loader**: File parsing, nested expansion, placeholder extraction
- **output_namer**: Filename generation, sanitization
- **metadata_generator**: Metadata structure, JSON validity
- **config_loader**: Schema validation, error messages
- **config_schema**: Dataclass validation

### Integration Tests

- **End-to-end generation**: From config to images + metadata
- **Backward compatibility**: Existing scripts work unchanged
- **Error handling**: Invalid configs fail gracefully

**Test Coverage:** 135 tests passing (Phase 1 + Phase 2) ✅

---

## Performance Considerations

### Variation Loading

- **Lazy loading**: Only load files for placeholders in template
- **Caching**: Variations loaded once per session
- **Efficient parsing**: Single-pass file parsing

### Combination Generation

- **Memory efficient**: Generate combinations on-the-fly for large sets
- **Early termination**: Stop at `max_images` in random mode
- **Unique tracking**: Set-based deduplication for random mode

### API Calls

- **Batch generation**: Use SD API batch parameters when supported
- **Error handling**: Retry logic for transient failures
- **Progress tracking**: Real-time progress updates

---

## Extension Points

### Adding New Generation Modes

```python
class ImageVariationGenerator:
    def _create_combinations(self):
        if self.generation_mode == "combinatorial":
            return self._create_combinations_combinatorial()
        elif self.generation_mode == "random":
            return self._create_combinations_random()
        elif self.generation_mode == "custom":  # NEW
            return self._create_combinations_custom()
```

### Adding New Placeholder Syntax

```python
# In variation_loader.py
def extract_placeholders_with_limits(template: str):
    # Current: {Name:N}, {Name:#|1|5}, {Name:$P}
    # New: {Name:@file.txt} for inline file reference
```

### Adding New Output Formats

```python
# In metadata_generator.py
def export_metadata(metadata, format="json"):
    if format == "json":
        return export_json(metadata)
    elif format == "yaml":  # NEW
        return export_yaml(metadata)
    elif format == "csv":   # NEW
        return export_csv(metadata)
```

---

## Future Enhancements (Phase 3+)

### Phase 3: Execution (In Progress)

- `config_selector.py`: Interactive config selection
- `json_generator.py`: JSON-to-generator translation
- `generator_cli.py`: Main CLI entry point

### Phase 4: Advanced Features (Future)

- `checkpoint_manager.py`: Automatic checkpoint switching
- Script-to-JSON conversion tool
- Batch processing of multiple configs

---

## References

- **[Config System](config-system.md)** - Detailed config system docs
- **[Output System](output-system.md)** - Output naming and metadata
- **[Variation Loader](variation-loader.md)** - Variation file parsing
- **[Design Decisions](design-decisions.md)** - Architecture rationale

---

**Status:** Core architecture complete (Phase 1 + Phase 2) ✅
**Next:** Phase 3 execution system 🔄

**Last updated:** 2025-10-01
