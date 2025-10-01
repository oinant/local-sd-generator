# Output System

**Technical documentation for file naming and metadata export.**

**Status:** Phase 1 complete ✅ | 49 tests passing

---

## Overview

The output system provides:
1. **SF-4: Enhanced file naming** - Intelligent session folder and image filename generation
2. **SF-5: JSON metadata export** - Structured metadata with complete generation info

---

## Module Structure

```
CLI/output/
├── __init__.py
├── output_namer.py        # SF-4: File/folder naming logic
└── metadata_generator.py  # SF-5: JSON metadata generation
```

---

## SF-4: Enhanced File Naming

**File:** `CLI/output/output_namer.py`

### Purpose

Generate intelligent, descriptive filenames for session folders and images based on configuration.

### Session Folder Naming

**Format:** `{timestamp}_{name_components}/`

**Algorithm:**
```python
def generate_session_folder_name(
    timestamp: str,
    session_name: Optional[str],
    filename_keys: List[str],
    variations_sample: Dict[str, str]
) -> str:
    """
    Generate session folder name.

    Priority:
      1. If session_name provided: {timestamp}_{session_name}
      2. Elif filename_keys provided: {timestamp}_{key1}_{key2}...
      3. Else: {timestamp}

    Args:
        timestamp: Format YYYYMMDD_HHMMSS (e.g., "20251001_143052")
        session_name: Custom name (e.g., "anime_test_v2")
        filename_keys: List of variation keys (e.g., ["Expression", "Angle"])
        variations_sample: Sample variation values for keys

    Returns:
        Session folder name

    Examples:
        # With session_name
        ("20251001_143052", "anime_test_v2", [], {})
        → "20251001_143052_anime_test_v2"

        # With filename_keys
        ("20251001_143052", None, ["Expression", "Angle"],
         {"Expression": "smiling", "Angle": "front view"})
        → "20251001_143052_smiling_frontView"

        # Timestamp only
        ("20251001_143052", None, [], {})
        → "20251001_143052"
    """
```

### Image Filename Generation

**Format:** `{index:03d}_{key1}-{value1}_{key2}-{value2}.png`

**Algorithm:**
```python
def generate_image_filename(
    index: int,
    variation_dict: Dict[str, str],
    filename_keys: List[str]
) -> str:
    """
    Generate image filename.

    Format options:
      - Without filename_keys: {index:03d}.png
      - With filename_keys: {index:03d}_{key1}-{value1}_{key2}-{value2}.png

    Args:
        index: Image number (1-based)
        variation_dict: Current variation values
        filename_keys: Which keys to include in filename

    Returns:
        Image filename

    Examples:
        # Without filename_keys
        (1, {"Expression": "smiling"}, [])
        → "001.png"

        # With filename_keys
        (5, {"Expression": "smiling", "Angle": "front view"},
         ["Expression", "Angle"])
        → "005_Expression-smiling_Angle-frontView.png"

        # Sanitized values
        (12, {"Expression": "wide eyes, surprised"},
         ["Expression"])
        → "012_Expression-wideEyesSurprised.png"
    """
```

### Filename Sanitization

**Function:** `sanitize_filename_component(value: str) -> str`

**Purpose:** Convert variation values to filesystem-safe camelCase format.

**Algorithm:**
1. Remove leading/trailing whitespace
2. Split on spaces, hyphens, underscores, commas
3. Capitalize each word except first
4. Join without separators
5. Remove any remaining special characters
6. Ensure result is not empty

**Examples:**
```python
sanitize_filename_component("front view")
→ "frontView"

sanitize_filename_component("wide angle shot")
→ "wideAngleShot"

sanitize_filename_component("DPM++ 2M Karras")
→ "dpm2mKarras"

sanitize_filename_component("smiling, happy")
→ "smilingHappy"

sanitize_filename_component("3/4 view")
→ "34View"

sanitize_filename_component("ULTRA-WIDE_angle")
→ "ultraWideAngle"
```

**Edge Cases:**
```python
sanitize_filename_component("")
→ "empty"  # Fallback

sanitize_filename_component("   ")
→ "empty"  # Fallback

sanitize_filename_component("123")
→ "123"  # Numeric OK

sanitize_filename_component("!@#$%")
→ "empty"  # No valid chars
```

### API Reference

```python
def generate_session_folder_name(
    timestamp: str,
    session_name: Optional[str] = None,
    filename_keys: Optional[List[str]] = None,
    variations_sample: Optional[Dict[str, str]] = None
) -> str:
    """Generate session folder name based on config."""

def generate_image_filename(
    index: int,
    variation_dict: Dict[str, str],
    filename_keys: Optional[List[str]] = None
) -> str:
    """Generate image filename with or without variation keys."""

def sanitize_filename_component(value: str) -> str:
    """Convert string to filesystem-safe camelCase."""

def get_timestamp() -> str:
    """Get current timestamp in YYYYMMDD_HHMMSS format."""
```

### Integration with ImageVariationGenerator

```python
class ImageVariationGenerator:
    def __init__(
        self,
        # ... existing params
        session_name: Optional[str] = None,
        filename_keys: Optional[List[str]] = None
    ):
        self.session_name = session_name
        self.filename_keys = filename_keys or []

    def run(self):
        # Generate session folder name
        timestamp = get_timestamp()
        variations_sample = self._get_first_variation_values()
        folder_name = generate_session_folder_name(
            timestamp,
            self.session_name,
            self.filename_keys,
            variations_sample
        )

        # Create session folder
        session_folder = self.output_dir / folder_name
        session_folder.mkdir(parents=True, exist_ok=True)

        # Generate images
        for idx, variation_dict in enumerate(combinations, start=1):
            # Generate filename
            filename = generate_image_filename(
                idx,
                variation_dict,
                self.filename_keys
            )

            # Save image
            image_path = session_folder / filename
            save_image(image, image_path)
```

---

## SF-5: JSON Metadata Export

**File:** `CLI/output/metadata_generator.py`

### Purpose

Export structured JSON metadata containing complete generation information.

### Metadata Schema

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

### API Reference

```python
def generate_metadata_dict(
    prompt_template: str,
    negative_prompt: str,
    variations_loaded: Dict[str, Dict[str, str]],
    generation_mode: str,
    seed_mode: str,
    seed: int,
    parameters: Dict[str, Any],
    output_folder: Path,
    session_name: Optional[str] = None,
    filename_keys: Optional[List[str]] = None,
    config_source: Optional[Path] = None,
    checkpoint: Optional[str] = None,
    total_images: int = 0,
    generation_time: float = 0.0
) -> Dict:
    """
    Generate complete metadata dictionary.

    Args:
        prompt_template: Original prompt template with placeholders
        negative_prompt: Negative prompt
        variations_loaded: Loaded variations with source file info
        generation_mode: "combinatorial" or "random"
        seed_mode: "fixed", "progressive", or "random"
        seed: Base seed value
        parameters: SD generation parameters (width, height, etc.)
        output_folder: Path to session output folder
        session_name: Custom session name (optional)
        filename_keys: Variation keys in filenames (optional)
        config_source: Path to JSON config file (optional)
        checkpoint: Checkpoint name (optional)
        total_images: Number of images generated
        generation_time: Total generation time in seconds

    Returns:
        Metadata dictionary matching schema
    """

def save_metadata_json(
    metadata: Dict,
    output_folder: Path
) -> None:
    """
    Save metadata to JSON file.

    Args:
        metadata: Metadata dictionary
        output_folder: Session folder

    Creates:
        {output_folder}/metadata.json

    Format:
        Pretty-printed JSON (2-space indent, UTF-8)
    """

def load_metadata_json(
    output_folder: Path
) -> Dict:
    """
    Load metadata from session folder.

    Args:
        output_folder: Session folder

    Returns:
        Metadata dictionary

    Raises:
        FileNotFoundError: If metadata.json not found
    """
```

### Backward Compatibility

**Legacy format:** `session_config.txt` (deprecated)

```python
def save_legacy_config_txt(
    prompt_template: str,
    variations_loaded: Dict,
    generation_mode: str,
    seed: int,
    output_folder: Path
) -> None:
    """
    Save legacy session_config.txt file.

    Format: Plain text with basic info
    Status: Deprecated, kept for compatibility

    Creates:
        {output_folder}/session_config.txt

    Content example:
        Prompt Template: masterpiece, {Expression}, {Angle}
        Variations: Expression (10 values), Angle (5 values)
        Generation Mode: combinatorial
        Seed: 42

        DEPRECATED: Use metadata.json instead
    """
```

### Integration with ImageVariationGenerator

```python
class ImageVariationGenerator:
    def run(self):
        start_time = time.time()

        # ... generation logic ...

        generation_time = time.time() - start_time

        # Generate metadata
        metadata = generate_metadata_dict(
            prompt_template=self.prompt_template,
            negative_prompt=self.negative_prompt,
            variations_loaded=self.variations_loaded,
            generation_mode=self.generation_mode,
            seed_mode=self.seed_mode,
            seed=self.seed,
            parameters={
                "width": self.width,
                "height": self.height,
                "steps": self.steps,
                "cfg_scale": self.cfg_scale,
                "sampler": self.sampler,
                "batch_size": self.batch_size,
                "batch_count": self.batch_count
            },
            output_folder=session_folder,
            session_name=self.session_name,
            filename_keys=self.filename_keys,
            total_images=len(combinations),
            generation_time=generation_time
        )

        # Save JSON metadata
        save_metadata_json(metadata, session_folder)

        # Save legacy text (deprecated)
        save_legacy_config_txt(...)
```

---

## Testing

### Test Coverage

**Total:** 49 tests passing ✅

**Breakdown:**
- `test_output_namer.py`: 27 tests
- `test_metadata_generator.py`: 22 tests

### Test Categories

#### Output Namer Tests
- Session folder naming (with/without session_name, filename_keys)
- Image filename generation (with/without filename_keys)
- Sanitization (special chars, camelCase conversion)
- Edge cases (empty strings, Unicode, long names)
- Timestamp format validation

#### Metadata Generator Tests
- Metadata structure completeness
- JSON validity and formatting
- Loading previously saved metadata
- Legacy config.txt generation
- Example resolved prompt generation
- Variation value truncation (large files)

### Running Tests

```bash
# Run all output tests
pytest tests/test_output_namer.py tests/test_metadata_generator.py -v

# Run specific test
pytest tests/test_output_namer.py::test_sanitize_special_characters -v

# Run with coverage
pytest tests/test_output_*.py --cov=CLI/output --cov-report=html
```

---

## Usage Examples

### Generate Session Folder Name

```python
from CLI.output.output_namer import generate_session_folder_name, get_timestamp

timestamp = get_timestamp()  # "20251001_143052"

# With session_name
folder1 = generate_session_folder_name(
    timestamp,
    session_name="anime_test_v2"
)
# → "20251001_143052_anime_test_v2"

# With filename_keys
folder2 = generate_session_folder_name(
    timestamp,
    filename_keys=["Expression", "Angle"],
    variations_sample={"Expression": "smiling", "Angle": "front view"}
)
# → "20251001_143052_smiling_frontView"

# Timestamp only
folder3 = generate_session_folder_name(timestamp)
# → "20251001_143052"
```

### Generate Image Filename

```python
from CLI.output.output_namer import generate_image_filename

variation = {
    "Expression": "wide eyes, surprised",
    "Angle": "3/4 view"
}

# With filename_keys
filename1 = generate_image_filename(
    5,
    variation,
    filename_keys=["Expression", "Angle"]
)
# → "005_Expression-wideEyesSurprised_Angle-34View.png"

# Without filename_keys
filename2 = generate_image_filename(5, variation)
# → "005.png"
```

### Save Metadata

```python
from CLI.output.metadata_generator import generate_metadata_dict, save_metadata_json
from pathlib import Path

# Generate metadata
metadata = generate_metadata_dict(
    prompt_template="masterpiece, {Expression}, {Angle}",
    negative_prompt="low quality",
    variations_loaded={
        "Expression": {
            "source_file": "/path/to/expressions.txt",
            "values": {"happy": "smiling", "sad": "crying"}
        },
        "Angle": {
            "source_file": "/path/to/angles.txt",
            "values": {"front": "front view", "side": "side view"}
        }
    },
    generation_mode="combinatorial",
    seed_mode="progressive",
    seed=42,
    parameters={"width": 512, "height": 768},
    output_folder=Path("outputs/20251001_143052_test"),
    session_name="test",
    filename_keys=["Expression", "Angle"],
    total_images=4,
    generation_time=120.5
)

# Save to file
save_metadata_json(metadata, Path("outputs/20251001_143052_test"))
# Creates: outputs/20251001_143052_test/metadata.json
```

---

## Design Decisions

### Why camelCase for Filenames?

**Chosen:** camelCase (`frontView`, `wideAngleShot`)
**Alternatives:** snake_case, kebab-case, spaces

**Rationale:**
- No special characters (filesystem safe)
- Compact (no separators)
- Readable (capitals indicate word boundaries)
- Consistent across platforms (Windows, Linux, macOS)

### Why Index Prefix?

**Chosen:** `001_`, `002_`, etc.
**Alternative:** No prefix

**Rationale:**
- Preserves generation order
- Easy to sort in file managers
- Unique filenames even if variation values duplicate
- 3 digits supports up to 999 images (extensible to more)

### Why JSON Metadata?

**Chosen:** Structured JSON
**Alternative:** Plain text, YAML, SQLite

**Rationale:**
- Machine-readable (easy parsing)
- Human-readable (pretty-printed)
- Widely supported (every language)
- Extensible (add fields without breaking parsers)
- Self-documenting (schema in structure)

### Why Keep Legacy session_config.txt?

**Chosen:** Generate both JSON and text
**Alternative:** JSON only

**Rationale:**
- Backward compatibility for existing tools
- Human-readable quick reference
- Marked as deprecated to encourage migration
- Will be removed in v2.0

---

## Future Enhancements

### Planned for v2.0

1. **Custom Filename Templates**
   - User-defined filename patterns
   - Variable substitution: `{index}_{Expression}_{seed}.png`

2. **Multiple Metadata Formats**
   - YAML export
   - CSV export (for spreadsheet analysis)
   - SQLite database (for large sessions)

3. **Metadata Indexing**
   - Global metadata index across sessions
   - Quick search by parameters, variations, dates

4. **Filename Length Limits**
   - Auto-truncate long filenames
   - Configurable max length
   - Hash suffix for uniqueness

---

## References

- **[Architecture](architecture.md)** - Overall system design
- **[Config System](config-system.md)** - Configuration details
- **[Design Decisions](design-decisions.md)** - Rationale

---

**Implementation:** Phase 1 complete ✅
**Tests:** 49 tests passing ✅
**Status:** Production ready 🚀

**Last updated:** 2025-10-01
