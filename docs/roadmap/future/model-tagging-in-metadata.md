# Model Tagging in Metadata

**Status:** next
**Priority:** 7
**Component:** cli
**Created:** 2025-10-07

## Description

Automatically capture and store the Stable Diffusion model/checkpoint used for generation in metadata.json. This allows tracking which model was active during generation, crucial for reproducing results and comparing outputs across different models.

## Problem Statement

Currently, metadata.json contains all generation parameters EXCEPT the model used:
- ✅ Prompt, negative prompt, variations
- ✅ Steps, CFG, sampler, seed
- ✅ Resolution, batch settings
- ❌ **Model/checkpoint name** (missing!)

When reviewing old generations, users cannot determine which model was used without external notes.

## Use Cases

1. **Reproducibility**: Re-generate exact same image months later
2. **Model Comparison**: "Which model gave better results for anime characters?"
3. **Documentation**: Share configs with model name included
4. **Debugging**: "Why do my old prompts not work anymore?" → different model

## Implementation Approaches

### Option A: SD WebUI API Call (Recommended)

**How it works:**
- Call `/sdapi/v1/options` endpoint before generation
- Extract `sd_model_checkpoint` field
- Store in metadata as `model.checkpoint_name`

**Pros:**
- ✅ Simple and reliable
- ✅ No external dependencies
- ✅ Works with existing SDAPIClient

**Cons:**
- ⚠️ Requires API call (adds ~50-100ms)
- ⚠️ Only captures checkpoint, not VAE or other models

**API Response Example:**
```json
{
  "sd_model_checkpoint": "realisticVisionV60B1_v51VAE.safetensors [15012c538f]",
  "sd_vae": "vae-ft-mse-840000-ema-pruned.ckpt",
  "CLIP_stop_at_last_layers": 1
}
```

### Option B: Headless Browser Scraping

**How it works:**
- Use Playwright MCP to open WebUI in headless mode
- Navigate to settings page
- Extract model name from UI

**Pros:**
- ✅ Could extract additional info (VAE, etc.)
- ✅ Mirrors what user sees in UI

**Cons:**
- ❌ Complex and fragile (depends on UI structure)
- ❌ Slow (browser startup takes seconds)
- ❌ Overkill for this use case
- ❌ Breaks if WebUI updates its HTML structure

**Verdict:** Not recommended unless we need extensive UI scraping.

### Option C: Parse Config File

**How it works:**
- Read `config.json` from WebUI directory
- Extract model settings

**Pros:**
- ✅ No API call needed
- ✅ Could work offline

**Cons:**
- ❌ Requires knowing WebUI installation path
- ❌ May not reflect runtime changes (model switched via UI)
- ❌ Fragile to config file location/format changes

**Verdict:** Not reliable enough.

## Recommended Solution: Option A (API Call)

Implement `/sdapi/v1/options` API call in SDAPIClient.

### Technical Design

#### 1. New API Method in `sdapi_client.py`

```python
def get_model_info(self, timeout: int = 5) -> dict:
    """
    Fetch current model/checkpoint information from WebUI

    Returns:
        dict with model info:
        {
            "checkpoint": "model_name.safetensors [hash]",
            "vae": "vae_name.ckpt",
            "clip_skip": 1
        }

    Raises:
        requests.RequestException: If API call fails
    """
    response = requests.get(
        f"{self.api_url}/sdapi/v1/options",
        timeout=timeout
    )
    response.raise_for_status()
    data = response.json()

    return {
        "checkpoint": data.get("sd_model_checkpoint", "unknown"),
        "vae": data.get("sd_vae", "auto"),
        "clip_skip": data.get("CLIP_stop_at_last_layers", 1)
    }
```

#### 2. Update `metadata_generator.py`

Already has `model_info` optional parameter (line 23):
```python
def generate_metadata_dict(
    ...
    model_info: Optional[Dict[str, str]] = None,  # ✅ Already exists!
    ...
)
```

Just needs to be populated!

#### 3. Update `batch_generator.py` Orchestration

Call `get_model_info()` once before generation batch:

```python
def generate_batch(...):
    # NEW: Fetch model info at session start
    try:
        model_info = api_client.get_model_info()
    except Exception as e:
        logger.warning(f"Failed to fetch model info: {e}")
        model_info = {"checkpoint": "unknown", "error": str(e)}

    # ... existing generation loop ...

    # Pass model_info to metadata generator
    metadata = generate_metadata_dict(
        ...,
        model_info=model_info  # ✅ Now populated!
    )
```

### Metadata Output Format

```json
{
  "version": "1.0",
  "generation_info": { ... },
  "model": {
    "checkpoint": "realisticVisionV60B1_v51VAE.safetensors [15012c538f]",
    "vae": "vae-ft-mse-840000-ema-pruned.ckpt",
    "clip_skip": 1
  },
  "prompt": { ... },
  "variations": { ... }
}
```

## Tasks

- [ ] Add `get_model_info()` method to `SDAPIClient` class
- [ ] Add unit tests for `get_model_info()` (mock API response)
- [ ] Update `batch_generator.py` to call `get_model_info()` before generation
- [ ] Add error handling for API call failures (fallback to "unknown")
- [ ] Update integration tests to verify model info in metadata.json
- [ ] Document new metadata field in technical docs

## Success Criteria

- [ ] `metadata.json` contains `model.checkpoint` field after generation
- [ ] API call failure does not block generation (graceful degradation)
- [ ] Model info fetched only once per session (not per image)
- [ ] Unit tests cover API success and failure scenarios
- [ ] Integration test verifies complete workflow

## Tests

**Unit tests** (`tests/api/test_sdapi_client.py`):
- ✅ Test `get_model_info()` with mocked successful response
- ✅ Test `get_model_info()` with API timeout
- ✅ Test `get_model_info()` with malformed JSON response

**Integration tests** (`tests/integration/test_model_metadata.py`):
- ✅ Generate batch with real API, verify model info in metadata.json
- ✅ Generate batch with API failure, verify graceful fallback

## Performance Impact

- **API call overhead**: ~50-100ms per session (called once, not per image)
- **Negligible impact**: For 100-image batch taking ~15min, adds 0.01% overhead

## Backward Compatibility

- ✅ `model_info` is optional parameter in `generate_metadata_dict()`
- ✅ Existing code continues to work without changes
- ✅ Old metadata.json files without `model` field remain valid

## Future Enhancements

Once this is implemented, could extend to capture:
- **ControlNet models** (if used)
- **LoRA models and weights** (parse from prompt)
- **Embeddings** (textual inversions used)
- **VAE info** (already captured in current design)

## Related Features

- **SF-5**: JSON Metadata Export (already implemented, this extends it)
- **Future**: Model comparison tool (would use this metadata)

## Documentation

After implementation:
- Update `/docs/cli/technical/metadata-format.md` with model fields
- Update `/docs/cli/usage/metadata-guide.md` with example
- Add migration note for users upgrading from older versions

## Priority Justification

**Priority 7** (Important but not urgent):
- Not blocking any features
- Nice-to-have for reproducibility
- Easy to implement (low risk)
- High value for long-term usage

## Effort Estimate

**Small** (~2-3 hours):
- 30 min: Implement API method
- 30 min: Update batch generator
- 1 hour: Write tests
- 30 min: Update docs
