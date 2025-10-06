# [CHORE] Refactor StableDiffusionAPIClient - Session Directory Handling

**Status:** next
**Priority:** 6
**Component:** cli
**Created:** 2025-10-04

## Problem

Currently, `StableDiffusionAPIClient` automatically creates a session directory in its constructor (`__init__`), which violates separation of concerns:

```python
def __init__(self, api_url: str = "http://127.0.0.1:7860",
             base_output_dir: str = "apioutput",
             session_name: str = None,
             dry_run: bool = False):
    # ...
    self.output_dir = self._create_session_dir()  # ❌ Side effect in constructor
```

**Issues:**
1. The API client shouldn't be responsible for filesystem operations
2. Makes it hard to use the client for API calls only (without creating directories)
3. Forces callers to work with the client's directory structure
4. Creates coupling between API client and file system management

## Proposed Solution

**Option 1: Separate Output Manager (Preferred)**

Create a dedicated `OutputManager` class:

```python
class OutputManager:
    """Handles output directory creation and file management"""
    def __init__(self, base_dir: str, session_name: str = None, dry_run: bool = False):
        self.base_dir = base_dir
        self.session_name = session_name
        self.dry_run = dry_run

    def create_session_dir(self) -> Path:
        """Creates and returns session directory path"""
        # Current logic from _create_session_dir
        pass

    def save_image(self, image_data, filename: str):
        """Saves image to session directory"""
        pass

    def save_manifest(self, data: dict, filename: str):
        """Saves JSON manifest"""
        pass
```

Then simplify the API client:

```python
class StableDiffusionAPIClient:
    """Pure API client - no filesystem operations"""
    def __init__(self, api_url: str = "http://127.0.0.1:7860"):
        self.api_url = api_url
        self.generation_config = GenerationConfig()

    def generate_image(self, prompt_cfg: PromptConfig) -> dict:
        """Returns raw API response (base64 image data)"""
        # API call only, no file saving
        pass
```

**Option 2: Explicit Initialization**

Keep current structure but make directory creation explicit:

```python
client = StableDiffusionAPIClient(api_url)
client.configure_output(base_dir, session_name, dry_run)  # Explicit call
client.create_output_dir()  # Or combined with configure_output
```

## Impact

**Files affected:**
- `sdapi_client.py` - Main refactor
- `template_cli.py` - Update to use new pattern
- `json_generator.py` - Update to use new pattern
- Any other callers of `StableDiffusionAPIClient`

**Benefits:**
- Cleaner separation of concerns
- More testable (can test API client without filesystem)
- More flexible for different use cases
- Easier to understand and maintain

## Tasks

- [ ] Design new API for output management
- [ ] Create `OutputManager` class (Option 1) or refactor client (Option 2)
- [ ] Update `template_cli.py` to use new pattern
- [ ] Update `json_generator.py` to use new pattern
- [ ] Update tests
- [ ] Update documentation

## Success Criteria

- API client can be instantiated without creating directories
- Output directory management is explicit and controllable
- All existing functionality works with new design
- Tests pass

## Notes

- This is a refactoring task, no new features
- Should not break existing functionality
- Consider backward compatibility or deprecation path
