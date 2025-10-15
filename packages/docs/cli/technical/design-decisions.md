# Design Decisions

**Rationale behind key architectural and implementation choices.**

---

## Table of Contents

1. [Configuration System](#configuration-system)
2. [Output System](#output-system)
3. [Variation System](#variation-system)
4. [API Design](#api-design)
5. [Testing Strategy](#testing-strategy)
6. [Future-Proofing](#future-proofing)

---

## Configuration System

### JSON over YAML/TOML

**Decision:** Use JSON for configuration files

**Alternatives considered:**
- YAML (more human-friendly, supports comments)
- TOML (simpler syntax)
- Python files (maximum flexibility)

**Rationale:**
- **Universal support**: Every language/platform supports JSON
- **No dependencies**: Python stdlib only
- **Schema validation**: Easy to validate structure
- **Machine-readable**: Perfect for automation
- **IDE support**: Most editors have JSON validation
- **Security**: No code execution risks (unlike Python configs)

**Trade-offs:**
- ❌ No comments (mitigated by `description` fields)
- ❌ Verbose syntax (acceptable for declarative configs)
- ✅ Can add YAML/TOML support later without breaking JSON

**Future:** May add YAML/TOML support while keeping JSON as primary format.

---

### Dataclasses over Pydantic

**Decision:** Use Python dataclasses for config schema

**Alternatives considered:**
- Pydantic models (runtime validation)
- TypedDict (type hints only)
- Plain dicts (no type safety)

**Rationale:**
- **No external dependencies**: Stdlib only (Python 3.7+)
- **Type hints**: Full IDE autocomplete support
- **Clear structure**: Self-documenting code
- **Extensible**: Easy to add custom validation
- **Lightweight**: No runtime overhead

**Trade-offs:**
- ❌ Less runtime validation than Pydantic
- ✅ We implement custom validation where needed
- ✅ Simpler, more maintainable code
- ✅ No dependency version conflicts

**Implementation:**
```python
@dataclass
class GenerationConfig:
    version: str
    prompt: PromptConfig
    variations: Dict[str, str]
    # Clear, type-safe, no magic
```

---

### Absolute Paths Only (v1.0)

**Decision:** Require absolute paths for variation files in v1.0

**Alternatives considered:**
- Relative paths (to config file, to project root, to cwd)
- Path resolution strategies
- Environment variables in paths

**Rationale:**
- **Unambiguous**: No confusion about relative-to-what
- **Explicit**: Clear exactly which file is used
- **Simpler validation**: Direct file existence check
- **Cross-platform**: Works consistently everywhere
- **Version-controllable**: Global config specifies base paths

**Trade-offs:**
- ❌ Verbose: `/full/path/to/variations/expressions.txt`
- ✅ Clear: No surprises about which file loads
- ✅ Can add relative path support in v2.0 with clear rules

**Future v2.0:**
```json
{
  "variations": {
    "Expression": "relative/to/config/expressions.txt",  // NEW
    "Angle": "${VARIATIONS_DIR}/angles.txt"             // NEW
  }
}
```

---

### Global Config Search Order

**Decision:** Search `.sdgen_config.json` in: project root → user home → defaults

**Alternatives considered:**
- User home only
- Project root only
- Environment variables

**Rationale:**
- **Flexibility**: Project-level overrides user-level
- **Convention**: Similar to `.gitconfig`, `.npmrc`
- **Portability**: Project configs can be version-controlled
- **Personal defaults**: User home for personal preferences

**Implementation:**
```python
1. Check ./.sdgen_config.json (project)
2. Check ~/.sdgen_config.json (user)
3. Use defaults
```

**Trade-offs:**
- ✅ Intuitive: Follows familiar patterns
- ✅ Flexible: Both global and per-project configs
- ⚠️ Multiple sources: Clear precedence rules documented

---

## Output System

### camelCase for Filename Components

**Decision:** Use camelCase for sanitized filename components

**Alternatives considered:**
- `snake_case` - underscores between words
- `kebab-case` - hyphens between words
- `Spaces` - preserve spaces
- `UPPERCASE` - all caps

**Rationale:**
- **Compact**: No separators, shorter filenames
- **Readable**: Capital letters mark word boundaries
- **Filesystem-safe**: No special characters
- **Cross-platform**: Works on Windows, Linux, macOS
- **Consistent**: Same format everywhere

**Examples:**
```python
"front view"        → "frontView"
"wide angle shot"   → "wideAngleShot"
"DPM++ 2M Karras"   → "dpm2mKarras"
```

**Trade-offs:**
- ✅ Short: `frontView` vs `front_view`
- ✅ Safe: No escaping needed
- ⚠️ Opinionated: Some prefer snake_case

**Future:** May add configurable filename format in v2.0.

---

### Index-Prefixed Filenames

**Decision:** Use `001_`, `002_`, etc. prefix for all images

**Alternatives considered:**
- No prefix: `Expression-Smiling.png`
- Suffix: `Expression-Smiling_001.png`
- Timestamp: `143052_Expression-Smiling.png`

**Rationale:**
- **Preserves order**: Generation sequence visible
- **Sorts naturally**: File managers sort correctly
- **Unique**: Even if variation values duplicate
- **Standard**: Common pattern in image sequences
- **Parseable**: Easy to extract index programmatically

**Examples:**
```
001_Expression-Smiling_Angle-Front.png
002_Expression-Smiling_Angle-Side.png
003_Expression-Sad_Angle-Front.png
```

**Trade-offs:**
- ✅ Clear generation order
- ✅ Always unique
- ⚠️ Filename longer (minimal impact)

---

### JSON over Text for Metadata

**Decision:** Export `metadata.json` instead of only `session_config.txt`

**Alternatives considered:**
- Plain text only
- YAML
- SQLite database
- CSV

**Rationale:**
- **Structured**: Easy to parse programmatically
- **Extensible**: Add fields without breaking parsers
- **Universal**: Every tool can read JSON
- **Human-readable**: Pretty-printed format
- **Complete**: Capture all generation info

**Metadata schema:**
```json
{
  "generation_info": {...},
  "model": {...},
  "prompt": {...},
  "variations": {...},
  "generation": {...},
  "parameters": {...},
  "output": {...}
}
```

**Trade-offs:**
- ✅ Machine-readable automation
- ✅ Complete information capture
- ✅ Can generate reports, analytics
- ⚠️ Legacy text file still generated (deprecated)

**Backward compatibility:** Keep `session_config.txt` in v1.x, remove in v2.0.

---

## Variation System

### Nested Variation Syntax: `{|option1|option2}`

**Decision:** Use `{|...}` for inline variations within variation files

**Alternatives considered:**
- Separate files for each combination
- JSON arrays in variation files
- Custom DSL syntax

**Rationale:**
- **DRY principle**: Define base + modifiers together
- **Combinatorial**: Automatically expands combinations
- **Readable**: Clear what's base vs modifier
- **Efficient**: Avoid file explosion

**Example:**
```
running,{|looking back|arms pumping}
→ Expands to:
  - running
  - running,looking back
  - running,arms pumping
```

**Trade-offs:**
- ✅ Compact representation
- ✅ Easy to maintain
- ⚠️ Syntax to learn (documented)

---

### Empty Option Always Included

**Decision:** `{|opt1|opt2}` expands to `["", "opt1", "opt2"]`

**Alternatives considered:**
- Only explicit options (no empty)
- `{|opt1|opt2|}` for explicit empty

**Rationale:**
- **Common pattern**: "With or without modifier"
- **Predictable**: Always includes base case
- **Concise**: No need for explicit empty syntax

**Example:**
```
standing,{|arms crossed}
→
  - standing            (base)
  - standing,arms crossed (with modifier)
```

**Trade-offs:**
- ✅ Intuitive for "optional modifier" use case
- ⚠️ Always generates base variation (intended behavior)

---

### Multiple Files per Placeholder

**Decision:** Support `{"Pose": ["file1.txt", "file2.txt"]}`

**Alternatives considered:**
- Single file only
- Merge files manually
- Directory scanning

**Rationale:**
- **Modular**: Organize by category
- **Reusable**: Share files across projects
- **Flexible**: Easy to enable/disable categories
- **Collaborative**: Multiple people work on different files

**Example:**
```python
{
    "Pose": [
        "variations/poses/standing.txt",
        "variations/poses/sitting.txt",
        "variations/poses/action.txt"
    ]
}
```

**Trade-offs:**
- ✅ Better organization
- ✅ Easy to maintain
- ⚠️ Need to handle duplicates (merge strategy)

**Implementation:** Merge all files, later files override duplicates.

---

## API Design

### Backward Compatibility Priority

**Decision:** Keep existing `ImageVariationGenerator` API unchanged

**Alternatives considered:**
- Break API, require migration
- Deprecate old API immediately
- New class entirely

**Rationale:**
- **User trust**: Existing scripts keep working
- **Gradual adoption**: Users migrate at their pace
- **Risk mitigation**: No forced breaking changes

**Implementation:**
```python
# Old code still works
generator = ImageVariationGenerator(
    prompt_template="...",
    variation_files={...}
)

# New features are optional
generator = ImageVariationGenerator(
    prompt_template="...",
    variation_files={...},
    filename_keys=["Expression"],  # NEW, optional
)
```

**Trade-offs:**
- ✅ Zero breaking changes
- ✅ User confidence
- ⚠️ More testing burden (test old + new)

---

### Optional vs Required Parameters

**Decision:** Make all new features optional with sensible defaults

**Alternatives considered:**
- Required parameters (fail fast)
- Magic defaults (implicit behavior)

**Rationale:**
- **Gradual adoption**: Use new features when ready
- **Backward compatibility**: Old scripts work
- **Explicit > Implicit**: Defaults documented

**Example:**
```python
def __init__(
    self,
    prompt_template: str,           # Required
    variation_files: Dict,          # Required
    filename_keys: List[str] = None,  # Optional, default None
    session_name: str = None,         # Optional, default None
):
    # Sensible defaults when not provided
    self.filename_keys = filename_keys or []
```

**Trade-offs:**
- ✅ Easy to adopt incrementally
- ✅ No forced migration
- ⚠️ Need clear documentation of defaults

---

## Testing Strategy

### pytest over unittest

**Decision:** Use pytest for all tests

**Alternatives considered:**
- unittest (stdlib)
- nose2
- doctest

**Rationale:**
- **Concise**: Less boilerplate
- **Fixtures**: Powerful test setup
- **Parametrization**: Easy data-driven tests
- **Plugins**: Rich ecosystem
- **Better output**: Clear failure messages

**Example:**
```python
# pytest style
def test_sanitize_filename():
    assert sanitize_filename("front view") == "frontView"

# vs unittest style
class TestFilename(unittest.TestCase):
    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("front view"), "frontView")
```

**Trade-offs:**
- ✅ Less boilerplate
- ✅ More readable
- ⚠️ External dependency (widely used)

---

### 80%+ Test Coverage Goal

**Decision:** Target >80% test coverage for core modules

**Alternatives considered:**
- 100% coverage (too strict)
- No target (insufficient)
- 50% coverage (too lenient)

**Rationale:**
- **Balance**: Thorough without being excessive
- **Critical paths**: Focus on important code
- **Confidence**: Catch regressions
- **Maintainability**: Tests as documentation

**Current status:**
- Phase 1 (output): 49 tests ✅
- Phase 2 (config): 86 tests ✅
- **Total: 135 tests passing**

**Trade-offs:**
- ✅ Confidence in refactoring
- ✅ Clear correctness
- ⚠️ Test maintenance time

---

### Integration Tests for Critical Paths

**Decision:** Include end-to-end integration tests

**Alternatives considered:**
- Unit tests only
- Manual testing only

**Rationale:**
- **Real-world validation**: Tests actual usage
- **Catch integration issues**: Unit tests miss some bugs
- **User confidence**: Validates complete workflows

**Example:** `test_integration_phase2.py`
```python
def test_complete_generation_workflow():
    # Load config
    config = load_config("test_config.json")
    # Create generator
    generator = create_generator_from_config(config)
    # Run generation (mocked SD API)
    generator.run()
    # Verify outputs
    assert session_folder.exists()
    assert metadata_json.exists()
```

**Trade-offs:**
- ✅ Validates real usage
- ✅ Catches integration bugs
- ⚠️ Slower than unit tests (acceptable)

---

## Future-Proofing

### Version Field in Configs

**Decision:** Require `"version": "1.0"` in JSON configs

**Alternatives considered:**
- No version field
- Semantic versioning in filename

**Rationale:**
- **Forward compatibility**: Can detect old configs
- **Migration path**: Can auto-upgrade configs
- **Clear intent**: Users know what version they're using

**Future:**
```python
def load_config(path):
    config_data = json.load(path)

    if config_data["version"] == "1.0":
        return load_v1_config(config_data)
    elif config_data["version"] == "2.0":
        return load_v2_config(config_data)
    else:
        # Auto-upgrade or error
```

**Trade-offs:**
- ✅ Future-proof
- ✅ Clear migration path
- ⚠️ Need to maintain version parsers

---

### Extension Points in Architecture

**Decision:** Design for extensibility from the start

**Alternatives considered:**
- YAGNI (You Aren't Gonna Need It)
- Premature abstraction

**Rationale:**
- **Known needs**: We know future features
- **Low cost**: Simple abstract methods
- **User requests**: Community will want extensions

**Examples:**
```python
class ImageVariationGenerator:
    def _create_combinations(self):
        # Extension point for new generation modes
        if self.generation_mode == "combinatorial":
            return self._create_combinations_combinatorial()
        elif self.generation_mode == "random":
            return self._create_combinations_random()
        # Easy to add new modes

    def _generate_filename(self, index, variation):
        # Extension point for custom naming
        return self.filename_generator.generate(index, variation)
```

**Trade-offs:**
- ✅ Easy to extend
- ✅ Community contributions
- ⚠️ Slightly more complex (worth it)

---

### Deprecation over Breaking Changes

**Decision:** Deprecate old features instead of removing immediately

**Alternatives considered:**
- Immediate removal
- Keep forever
- Version-gated removal

**Rationale:**
- **User-friendly**: No surprise breakage
- **Migration time**: Users adapt gradually
- **Clear communication**: Deprecation warnings

**Example:**
```python
# v1.0: Both files generated
save_metadata_json(metadata, folder)  # NEW
save_legacy_config_txt(config, folder)  # DEPRECATED

# v2.0: Only JSON
save_metadata_json(metadata, folder)
# Legacy removed, clear migration guide
```

**Trade-offs:**
- ✅ Smooth migration
- ✅ User confidence
- ⚠️ Maintain deprecated code temporarily

---

## Trade-offs Summary

| Decision | Benefits | Drawbacks | Mitigation |
|----------|----------|-----------|------------|
| JSON configs | Universal, parseable | No comments | Use `description` fields |
| Dataclasses | Stdlib, simple | Less validation | Custom validation |
| Absolute paths | Unambiguous | Verbose | Add relative in v2.0 |
| camelCase | Compact, safe | Opinionated | Document clearly |
| JSON metadata | Structured, extensible | Verbose | Pretty-print |
| Nested variations | DRY, efficient | Syntax to learn | Good docs |
| Backward compat | User trust | More testing | Worth it |
| 80% coverage | Confidence | Test maintenance | Focus on critical |

---

## Lessons Learned

### Start Simple, Add Complexity

- ✅ Absolute paths only → Add relative later
- ✅ JSON only → Add YAML later
- ✅ Core features → Add advanced features

### Document Early

- ✅ Write specs before implementation
- ✅ Document design decisions
- ✅ Update docs with code

### Test-Driven Development

- ✅ Write tests alongside code
- ✅ Integration tests catch real issues
- ✅ High coverage = confidence

### Backward Compatibility Pays Off

- ✅ Users trust incremental changes
- ✅ No forced migrations
- ✅ Adoption happens naturally

---

## References

- **[Architecture](architecture.md)** - System overview
- **[Config System](config-system.md)** - Configuration details
- **[Output System](output-system.md)** - File naming details
- **[Variation Loader](variation-loader.md)** - Parsing details

---

**Last updated:** 2025-10-01
