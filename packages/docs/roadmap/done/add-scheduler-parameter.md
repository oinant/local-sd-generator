# Add Scheduler Parameter

**Status:** done ✅
**Priority:** 6
**Component:** cli
**Created:** 2025-10-07
**Completed:** 2025-10-07

## Description

Add support for the `scheduler` parameter in image generation. Modern Stable Diffusion schedulers (introduced in SD 1.5+, enhanced in SDXL) allow fine-grained control over the denoising process, separate from the sampler choice.

## Problem Statement

Currently, the generator only exposes `sampler_name` parameter:
```python
# In GenerationConfig (sdapi_client.py:14-30)
sampler_name: str = "DPM++ 2M Karras"
```

However, modern SD WebUI supports separate `scheduler` parameter:
- **Sampler**: Core algorithm (Euler, DPM++, etc.)
- **Scheduler**: Noise schedule (Karras, Exponential, Polyexponential, etc.)

**Example from SD WebUI:**
```json
{
  "sampler_name": "DPM++ 2M",
  "scheduler": "Karras"
}
```

## Background: Sampler vs Scheduler

### Historical Context

**Old approach (SD 1.4 and earlier):**
- Sampler name included schedule: `"DPM++ 2M Karras"`, `"Euler a"`
- Schedule was baked into sampler name

**New approach (SD 1.5+, SDXL):**
- Sampler and scheduler are SEPARATE parameters
- More flexible: Any sampler can use any compatible scheduler
- Better UX: Sampler dropdown + Scheduler dropdown

### Current SD WebUI Behavior

WebUI likely supports both formats for backward compatibility:
1. **Legacy format:** `sampler_name = "DPM++ 2M Karras"` → parses scheduler from name
2. **Modern format:** `sampler_name = "DPM++ 2M"` + `scheduler = "Karras"`

Our generator currently uses **legacy format only**.

### Scheduler Types

Common schedulers in SD WebUI:
- **Automatic** - Let sampler decide
- **Karras** - Karras noise schedule (most popular)
- **Exponential** - Exponential decay
- **Polyexponential** - Polynomial exponential
- **SGM Uniform** - Uniform schedule (SDXL default)
- **Simple** - Simple linear schedule
- **Normal** - Normal distribution schedule
- **DDIM** - DDIM schedule
- **Align Your Steps** - AYS optimized schedule (new!)

## Use Cases

1. **Testing different schedules:** Compare Karras vs Exponential with same sampler
2. **SDXL optimization:** Use `SGM Uniform` scheduler (recommended for SDXL)
3. **Speed optimization:** Some schedulers converge faster
4. **Aesthetic control:** Different schedules affect final image characteristics
5. **Reproducibility:** Explicitly specify scheduler instead of relying on sampler name parsing

## Implementation Design

### 1. Update `GenerationConfig` Dataclass

**File:** `CLI/api/sdapi_client.py`

```python
@dataclass
class GenerationConfig:
    """Configuration for image generation"""
    steps: int = 30
    cfg_scale: float = 7.0
    width: int = 512
    height: int = 768
    sampler_name: str = "DPM++ 2M Karras"  # Can still use legacy format
    scheduler: Optional[str] = None  # NEW: Explicit scheduler
    batch_size: int = 1
    n_iter: int = 1

    # Hires Fix parameters
    enable_hr: bool = False
    hr_scale: float = 2.0
    hr_upscaler: str = "R-ESRGAN 4x+"
    denoising_strength: float = 0.5
    hr_second_pass_steps: Optional[int] = None
```

### 2. Update `_build_payload()` Method

**File:** `CLI/api/sdapi_client.py` (line 124-145)

```python
def _build_payload(self, prompt_config: PromptConfig) -> dict:
    """Build API payload from prompt config"""
    payload = {
        "prompt": prompt_config.prompt,
        "negative_prompt": prompt_config.negative_prompt,
        "seed": prompt_config.seed if prompt_config.seed is not None else -1,
        "steps": self.generation_config.steps,
        "cfg_scale": self.generation_config.cfg_scale,
        "width": self.generation_config.width,
        "height": self.generation_config.height,
        "sampler_name": self.generation_config.sampler_name,
        "batch_size": self.generation_config.batch_size,
        "n_iter": self.generation_config.n_iter
    }

    # NEW: Add scheduler if specified
    if self.generation_config.scheduler is not None:
        payload["scheduler"] = self.generation_config.scheduler

    # Add Hires Fix parameters if enabled
    if self.generation_config.enable_hr:
        # ... existing code ...

    return payload
```

### 3. Update Configuration Parsers

#### YAML Config (Phase 2)

```yaml
parameters:
  steps: 30
  cfg_scale: 7.0
  sampler: "DPM++ 2M"  # No longer includes scheduler name
  scheduler: "Karras"   # NEW: Explicit scheduler
  width: 512
  height: 768
```

#### JSON Config (Legacy)

```json
{
  "parameters": {
    "steps": 30,
    "cfg_scale": 7.0,
    "sampler_name": "DPM++ 2M",
    "scheduler": "Karras",
    "width": 512,
    "height": 768
  }
}
```

### 4. Update CLI Arguments

```bash
# Existing usage (backward compatible)
python template_cli.py prompt.yaml --sampler "DPM++ 2M Karras"

# New usage (explicit scheduler)
python template_cli.py prompt.yaml \
  --sampler "DPM++ 2M" \
  --scheduler "Karras"
```

### 5. Update Metadata Export

Ensure scheduler is captured in `metadata.json`:

```json
{
  "parameters": {
    "steps": 30,
    "cfg_scale": 7.0,
    "sampler_name": "DPM++ 2M",
    "scheduler": "Karras",  // ← NEW
    "width": 512,
    "height": 768
  }
}
```

## Backward Compatibility

✅ **Fully backward compatible:**

1. **Legacy format still works:**
   ```yaml
   sampler: "DPM++ 2M Karras"
   # scheduler: null → SD WebUI parses scheduler from name
   ```

2. **New format is optional:**
   ```yaml
   sampler: "DPM++ 2M"
   scheduler: "Karras"
   # Both parameters sent to API
   ```

3. **Default behavior unchanged:**
   - If `scheduler` not specified → `None` → not included in payload
   - SD WebUI handles missing scheduler gracefully

## Tasks

- [ ] Add `scheduler: Optional[str]` field to `GenerationConfig` dataclass
- [ ] Update `_build_payload()` to include scheduler if specified
- [ ] Update YAML config parser to read `scheduler` field
- [ ] Update JSON config parser to read `scheduler` field
- [ ] Add `--scheduler` CLI argument
- [ ] Update metadata generator to include scheduler in output
- [ ] Add unit tests for scheduler parameter handling
- [ ] Add integration test with scheduler specified
- [ ] Document scheduler options and usage
- [ ] Create migration guide (legacy → modern format)

## Success Criteria

- [ ] `scheduler` parameter accepted in YAML/JSON configs
- [ ] `scheduler` parameter accepted as CLI argument
- [ ] `scheduler` included in API payload when specified
- [ ] `scheduler` captured in metadata.json
- [ ] Legacy format (`"DPM++ 2M Karras"`) still works
- [ ] Unit tests cover scheduler presence/absence
- [ ] Documentation explains sampler vs scheduler

## Tests

**Unit tests** (`tests/api/test_sdapi_client.py`):
- ✅ Test payload with scheduler specified
- ✅ Test payload without scheduler (None)
- ✅ Test payload with legacy sampler name (includes scheduler in name)
- ✅ Test GenerationConfig with scheduler set
- ✅ Test GenerationConfig with scheduler=None (default)

**Integration tests** (`tests/integration/test_scheduler.py`):
- ✅ Generate image with explicit scheduler
- ✅ Generate image without scheduler (default)
- ✅ Verify scheduler in metadata.json
- ✅ Compare legacy vs modern format (both should work)

## Research Needed

Before implementation, verify:

1. **SD WebUI API parameter name:**
   - Is it `scheduler` or `schedule`?
   - Check `/sdapi/v1/docs` or API source code

2. **Valid scheduler values:**
   - Get list of supported schedulers from API
   - Endpoint: `/sdapi/v1/schedulers` (if exists?)
   - Or hardcode common values from WebUI UI

3. **Backward compatibility:**
   - Does WebUI reject unknown `scheduler` values?
   - Does it ignore `scheduler` if sampler name includes schedule?

**Action:** Call `/sdapi/v1/options` or `/docs` to verify parameter name and values.

## Documentation Impact

### Files to Update

1. **Technical docs:**
   - `/docs/cli/technical/generation-parameters.md` - Add scheduler section
   - `/docs/cli/technical/api-reference.md` - Document new parameter

2. **User guides:**
   - `/docs/cli/usage/configuration-guide.md` - Show scheduler examples
   - `/docs/cli/usage/sampler-and-scheduler-guide.md` - NEW: Explain difference

3. **Migration guide:**
   - Create guide for users switching from legacy format
   - Example conversions:
     ```
     "DPM++ 2M Karras" → sampler="DPM++ 2M", scheduler="Karras"
     "Euler a" → sampler="Euler a", scheduler=None
     ```

## Priority Justification

**Priority 6** (Nice enhancement):
- Not urgent (legacy format works)
- Modern format is cleaner and more flexible
- Useful for SDXL and new scheduler types
- Low implementation risk

## Effort Estimate

**Small** (~2-3 hours):
- 30 min: Add field and update payload builder
- 30 min: Update config parsers and CLI args
- 1 hour: Write tests
- 30 min: Research SD WebUI API (verify parameter name)
- 30 min: Update documentation

## Example Use Cases

### Use Case 1: SDXL Optimization
```yaml
# SDXL works best with SGM Uniform scheduler
parameters:
  sampler: "DPM++ 2M SDE"
  scheduler: "SGM Uniform"
  steps: 30
```

### Use Case 2: Speed Testing
```yaml
# Test which scheduler converges fastest for your prompt
parameters:
  sampler: "DPM++ 2M"
  scheduler: "Exponential"  # vs "Karras" vs "Polyexponential"
  steps: 20
```

### Use Case 3: Reproducibility
```yaml
# Explicit scheduler ensures same results across WebUI versions
parameters:
  sampler: "Euler"
  scheduler: "Karras"
  seed: 42
```

## Related Features

- **SF-5**: JSON Metadata Export - Scheduler should be in metadata
- **Model tagging**: Model + scheduler affect final output (both should be captured)
- **Future: Scheduler comparison tool** - Compare different schedulers side-by-side

## Future Enhancements

1. **Scheduler validation:**
   - Fetch valid schedulers from `/sdapi/v1/schedulers`
   - Validate config against API-supported values
   - Provide helpful error: "Unknown scheduler 'foo', valid options: ..."

2. **Scheduler recommendations:**
   - Suggest optimal scheduler based on model type (SDXL → SGM Uniform)
   - Warn if using incompatible sampler+scheduler combo

3. **Scheduler presets:**
   ```yaml
   scheduler_preset: "fast"  # → Uses fastest converging scheduler
   scheduler_preset: "quality"  # → Uses highest quality scheduler
   ```

## Breaking Changes

**None.** This is a purely additive change:
- New optional parameter
- Backward compatible with legacy format
- Default behavior unchanged

## API Compatibility Matrix

| Config Format | API Payload | WebUI Behavior |
|--------------|-------------|----------------|
| `sampler: "DPM++ 2M Karras"` | `{"sampler_name": "DPM++ 2M Karras"}` | ✅ Parses scheduler from name |
| `sampler: "DPM++ 2M"`, `scheduler: "Karras"` | `{"sampler_name": "DPM++ 2M", "scheduler": "Karras"}` | ✅ Uses explicit scheduler |
| `sampler: "DPM++ 2M"`, `scheduler: null` | `{"sampler_name": "DPM++ 2M"}` | ✅ Uses sampler default |
| `sampler: "DPM++ 2M Karras"`, `scheduler: "Exponential"` | Both sent | ❓ **To verify:** Which wins? |

## Open Questions

1. ❓ What happens if both legacy name AND scheduler param provided?
   - Does explicit `scheduler` override parsed scheduler from name?
   - Or does name take precedence?
   - **Resolution:** Test with real SD WebUI

2. ❓ Are there sampler-scheduler incompatibilities?
   - Can any sampler use any scheduler?
   - Or are some combos invalid?
   - **Resolution:** Check SD WebUI source or docs

3. ❓ What's the API parameter name?
   - `scheduler` or `schedule` or `noise_schedule`?
   - **Resolution:** Verify via `/sdapi/v1/docs` or API call

## Notes

- This feature aligns with modern SD WebUI best practices
- Keeps our tool current with SD ecosystem evolution
- Low implementation cost, high long-term value
