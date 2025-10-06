# [CHORE] Refactor StableDiffusionAPIClient - SRP Violation Fix

**Status:** wip
**Priority:** 2 (P2 - Important)
**Component:** cli
**Created:** 2025-10-06
**Started:** 2025-10-06

## Problem

`StableDiffusionAPIClient` violates Single Responsibility Principle (SRP) by handling 6 different responsibilities:

1. **API Communication** - Making HTTP requests to Stable Diffusion API
2. **File I/O** - Saving images and JSON configs to disk
3. **UI/Progress Reporting** - Printing progress messages and emojis
4. **Session Management** - Creating timestamped directories and session configs
5. **Batch Processing** - Orchestrating multiple image generation with delays
6. **Configuration Management** - Managing generation parameters

**Current stats:**
- **265 lines** in one class
- **6 responsibilities** mixed together
- **Hard to test** - Can't test API without filesystem
- **Hard to reuse** - Can't use batch logic without API calls
- **Hard to maintain** - Changes affect multiple concerns

See detailed analysis in `docs/tooling/srp_analysis_2025-10-06.md`

## Proposed Solution

**Decompose into 5 focused classes:**

### 1. SDAPIClient (Pure API)
```python
class SDAPIClient:
    """Pure HTTP client for Stable Diffusion WebUI API"""
    def __init__(self, api_url: str = "http://127.0.0.1:7860"):
        self.api_url = api_url

    def test_connection(self, timeout: int = 5) -> bool:
        """Test API availability"""

    def generate_image(self, payload: dict, timeout: int = 300) -> dict:
        """Generate single image, returns API response"""
```

**Responsibility:** HTTP communication only

### 2. SessionManager
```python
class SessionManager:
    """Manages output sessions and directories"""
    def __init__(self, base_dir: str, session_name: str = None, dry_run: bool = False):
        self.base_dir = base_dir
        self.session_name = session_name
        self.dry_run = dry_run

    def create_session_dir(self) -> Path:
        """Create timestamped session directory"""

    def save_session_config(self, config_data: dict):
        """Save session_config.txt"""
```

**Responsibility:** Session lifecycle and directory structure

### 3. ImageWriter
```python
class ImageWriter:
    """Handles image and JSON file I/O"""
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def save_image(self, image_data: bytes, filename: str):
        """Save PNG image"""

    def save_json_request(self, payload: dict, filename: str):
        """Save JSON request (dry-run mode)"""
```

**Responsibility:** File operations only

### 4. ProgressReporter
```python
class ProgressReporter:
    """Reports generation progress to console"""
    def __init__(self, total_images: int):
        self.total = total_images
        self.start_time = time.time()

    def report_start(self, index: int, filename: str):
        """Print generation start message"""

    def report_success(self, filename: str):
        """Print success message"""

    def report_progress(self, completed: int):
        """Print time remaining estimate"""

    def report_summary(self, success_count: int):
        """Print final summary"""
```

**Responsibility:** Console output and progress tracking

### 5. BatchGenerator (Orchestrator)
```python
class BatchGenerator:
    """Orchestrates batch generation workflow"""
    def __init__(self,
                 api_client: SDAPIClient,
                 session_mgr: SessionManager,
                 image_writer: ImageWriter,
                 progress_reporter: ProgressReporter):
        self.api_client = api_client
        self.session_mgr = session_mgr
        self.image_writer = image_writer
        self.progress = progress_reporter

    def generate_batch(self,
                      prompt_configs: List[PromptConfig],
                      delay_between: float = 2.0) -> Tuple[int, int]:
        """Execute full batch generation"""
```

**Responsibility:** Coordination and workflow orchestration

## Implementation Plan

### Phase 1: Extract Core Classes (4h)
- [ ] Create `SDAPIClient` (pure API, no I/O)
- [ ] Create `SessionManager` (directory management)
- [ ] Create `ImageWriter` (file operations)
- [ ] Create `ProgressReporter` (console output)
- [ ] Write unit tests for each class

### Phase 2: Create Orchestrator (2h)
- [ ] Create `BatchGenerator` (composition)
- [ ] Write integration tests
- [ ] Verify backward compatibility

### Phase 3: Migrate Callers (2h)
- [ ] Update `template_cli.py`
- [ ] Update `json_generator.py`
- [ ] Update any other callers
- [ ] Deprecate old `StableDiffusionAPIClient` or create compatibility wrapper

### Phase 4: Cleanup & Docs (1h)
- [ ] Remove or deprecate old class
- [ ] Update documentation
- [ ] Update usage examples
- [ ] Run full test suite

**Total Effort:** 8-10 hours

## Files Affected

**New files:**
- `CLI/api/sdapi_client.py` (new, pure API client)
- `CLI/api/session_manager.py`
- `CLI/api/image_writer.py`
- `CLI/api/progress_reporter.py`
- `CLI/api/batch_generator.py`

**Updated files:**
- `CLI/sdapi_client.py` - Deprecate or replace
- `CLI/template_cli.py` - Use new classes
- `CLI/json_generator.py` - Use new classes
- `CLI/tests/test_api_client.py` - Update tests

**Documentation:**
- `docs/cli/technical/api_architecture.md` (new)
- `docs/cli/usage/api_usage.md` (update)

## Success Criteria

- [x] Each class has ONE clear responsibility
- [ ] All classes are < 100 lines
- [ ] API client can be tested without filesystem
- [ ] Batch logic can be tested with mock API
- [ ] Progress reporting can be disabled/customized
- [ ] All existing tests pass
- [ ] New unit tests for each class (90%+ coverage)

## Tests

**Unit tests (5 new test files):**
- `test_sdapi_client.py` - API calls (mocked requests)
- `test_session_manager.py` - Directory creation (temp dirs)
- `test_image_writer.py` - File I/O (temp files)
- `test_progress_reporter.py` - Console output (captured stdout)
- `test_batch_generator.py` - Integration (all mocked)

**Integration tests:**
- `test_batch_integration.py` - Full workflow with real/mock API

## Migration Strategy

**Option 1: Hard break (faster)**
- Replace old class entirely
- Update all callers in one PR
- Remove old code

**Option 2: Gradual migration (safer)**
- Keep old class as compatibility wrapper
- Mark as deprecated with warnings
- Migrate callers incrementally
- Remove in next major version

**Recommended:** Option 2 for backward compatibility

## Related Work

- See `srp_analysis_2025-10-06.md` for detailed SRP analysis
- Related to `chore_refactor_sdapi_client_session_dir.md` (subsumed by this spec)
- Part of code review Sprint 1 action items

## Risks & Mitigation

**Risk 1: Breaking existing scripts**
- *Mitigation:* Create compatibility wrapper, deprecation warnings

**Risk 2: More files to maintain**
- *Mitigation:* Each file is smaller and simpler, net win

**Risk 3: Over-engineering**
- *Mitigation:* Each class solves real testability/reusability issues

## Notes

- This refactoring enables better testing (mock API separately from I/O)
- Enables reuse (use progress reporter elsewhere)
- Follows dependency injection pattern
- Makes dry-run mode cleaner (no I/O class needed)
- Future: Could add different output formats (S3, database) by swapping ImageWriter

## Commits

*Will be updated as work progresses*

---

**Reference:** Sprint 1, Priority P2
**Blocked by:** None
**Blocks:** None
