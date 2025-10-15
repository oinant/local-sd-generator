# [CHORE] Refactor StableDiffusionAPIClient - Session Directory Handling

**Status:** done
**Priority:** 6
**Component:** cli
**Created:** 2025-10-04
**Completed:** 2025-10-07

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

- [x] Design new API for output management
- [x] Create separate SRP-compliant classes (Option 1+)
- [x] Update `template_cli.py` to use new pattern
- [x] Update tests
- [x] Update documentation

## Implementation Summary

**Completed:** 2025-10-07

Implemented **Option 1+** with full SRP architecture in `CLI/api/` module:

### Created 5 SRP-Compliant Classes

1. **`SDAPIClient`** - Pure HTTP API communication
   - Handles requests to Stable Diffusion WebUI API
   - No filesystem operations
   - No session management
   
2. **`SessionManager`** - Output directory management
   - Creates and manages session directories
   - Handles folder naming and structure
   - Saves session configuration files

3. **`ImageWriter`** - File I/O operations
   - Saves images to disk
   - Saves JSON request payloads (dry-run mode)
   - Handles file encoding

4. **`ProgressReporter`** - Console output
   - Reports generation progress
   - Displays batch statistics
   - Handles all user-facing messages

5. **`BatchGenerator`** - Orchestration
   - Coordinates all components
   - Implements batch generation workflow
   - Handles delays and error recovery

### Migration Results

- ✅ `template_cli.py` migrated to use new `api/` module
- ✅ Legacy monolithic client removed from tracking
- ✅ 65 unit tests for API module (100% passing)
- ✅ All 199 tests passing
- ✅ No security issues (bandit clean)
- ✅ Clean SRP architecture

### Commits

- `03d5db6`: refactor: Migrate template_cli to new API module, remove Phase 1 from tracking
- `ab92a69`: refactor(output): Remove unused variations_sample parameter
- `d7ad606`: fix(api): Remove unused imports flagged by flake8
- `a1ed492`: test(api): Add comprehensive unit tests for refactored API module
- `6b87e2e`: refactor(templating): Decompose resolve_prompt() into 6 SRP-compliant functions

## Success Criteria

- ✅ API client can be instantiated without creating directories
- ✅ Output directory management is explicit and controllable
- ✅ All existing functionality works with new design
- ✅ Tests pass (199/199)
- ✅ Clean separation of concerns achieved

## Impact

**Files created:**
- `CLI/api/sdapi_client.py` (5.5K)
- `CLI/api/session_manager.py` (5.8K)
- `CLI/api/image_writer.py` (4.2K)
- `CLI/api/progress_reporter.py` (5.7K)
- `CLI/api/batch_generator.py` (7.5K)

**Files removed from tracking:**
- `CLI/sdapi_client.py` (16K monolithic legacy)
- `CLI/image_variation_generator.py` (23K Phase 1)
- `CLI/variation_loader.py` (25K Phase 1)
- 8 legacy test files
- 6 legacy documentation files

**Legacy code preserved locally in `/legacy/` but not tracked by git.**

## Notes

- Went beyond original plan with full 5-class SRP architecture
- Pre-commit code review: APPROVE WITH CHANGES (minor style issues only)
- Backend still uses legacy code (separate migration needed)
- Follow-up: Refactor main() complexity in template_cli.py (currently D rating)
