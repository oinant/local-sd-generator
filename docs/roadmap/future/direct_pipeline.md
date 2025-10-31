# Direct SD Pipeline - Product Specification

**Project:** Replace A1111 HTTP API with Direct PyTorch Pipeline
**Author:** Agent PO + Architecte
**Date:** 2025-10-31
**Status:** Pre-Production Analysis
**Priority:** P3 (Strategic Investment)

---

## Executive Summary

### Context
The `local-sd-generator` project has successfully generated **38,000+ images** using the Template System V2.0 via Automatic1111 (A1111) HTTP API. The system features advanced templating (placeholders, variations, inheritance, themes) and robust session management. Current performance: **36 sec/image** with LoRA + upscaler + 2 detailers at 1248×1824px.

### Problem Statement
The HTTP API architecture introduces significant overhead:
- **Network latency:** JSON serialization + HTTP transport (~500-1000ms per request)
- **No batch optimization:** Sequential processing with model reloading
- **Limited pipeline control:** Cannot optimize scheduler/sampler chains
- **Scalability ceiling:** Single-request bottleneck limits throughput

### Proposed Solution
Implement a **direct PyTorch pipeline** using modern SD frameworks (diffusers, ComfyUI, sd-scripts, or InvokeAI) to achieve:

1. **Performance:** 36s → **5-10s per image** (3-7x speedup with H100)
2. **Batch processing:** Generate 128+ images in single pipeline run
3. **Hardware utilization:** Full GPU saturation (5070 Ti 16GB → H100 80GB ready)
4. **Future-proof:** Foundation for self-improving generator (Generate → CLIP → Train → Loop)

### Recommendation
**Framework:** ComfyUI (Python API mode)
**MVP Scope:** txt2img + LoRA + basic upscaler (Phase 2-3)
**Effort:** ~8-12 weeks (POC 2 weeks, Core 4 weeks, Advanced 4-6 weeks)
**Risk:** Medium (migration complexity, feature parity, testing)

---

## 1. Framework Comparison Matrix

| Criterion | **ComfyUI** | diffusers | sd-scripts | InvokeAI | Weight |
|-----------|-------------|-----------|------------|----------|--------|
| **Performance** | ⭐⭐⭐⭐⭐ (2x faster than A1111) | ⭐⭐⭐ (slower without opts) | ⭐⭐⭐⭐ (training-optimized) | ⭐⭐⭐⭐ | 25% |
| **Batch Processing** | ⭐⭐⭐⭐⭐ (native caching) | ⭐⭐⭐ (manual batching) | ⭐⭐⭐ (training focus) | ⭐⭐⭐⭐ | 20% |
| **LoRA Support** | ⭐⭐⭐⭐⭐ (multi-LoRA nodes) | ⭐⭐⭐⭐ (official support) | ⭐⭐⭐⭐⭐ (native training) | ⭐⭐⭐⭐ | 15% |
| **ADetailer/Extensions** | ⭐⭐⭐⭐⭐ (custom nodes) | ⭐⭐ (DIY integration) | ⭐ (none) | ⭐⭐⭐ (plugins) | 15% |
| **Python API** | ⭐⭐⭐⭐ (JSON workflow API) | ⭐⭐⭐⭐⭐ (native Python) | ⭐⭐⭐ (scripts) | ⭐⭐⭐⭐ (REST API) | 10% |
| **Maintainability** | ⭐⭐⭐⭐ (active community) | ⭐⭐⭐⭐⭐ (HuggingFace) | ⭐⭐⭐ (niche) | ⭐⭐⭐⭐ | 5% |
| **Learning Curve** | ⭐⭐⭐ (node-based) | ⭐⭐⭐⭐ (Pythonic) | ⭐⭐ (complex) | ⭐⭐⭐ | 5% |
| **Community/Docs** | ⭐⭐⭐⭐⭐ (huge ecosystem) | ⭐⭐⭐⭐⭐ (excellent docs) | ⭐⭐⭐ (specialized) | ⭐⭐⭐⭐ | 5% |
| **TOTAL SCORE** | **4.5 / 5.0** | **3.6 / 5.0** | **3.2 / 5.0** | **3.7 / 5.0** | 100% |

### Framework Analysis

#### 1. ComfyUI (Recommended ✅)
**Strengths:**
- **Performance king:** 2x faster than A1111 in benchmarks (batch processing: 10 images in 1m07s vs 2m23s)
- **Advanced caching:** Reuses computed values across batch → exponential gains
- **Custom nodes ecosystem:** 500+ nodes (ADetailer, ControlNet, upscalers, LoRA schedulers)
- **JSON workflow API:** Programmatic control via Python → perfect for our templating system
- **Memory efficiency:** Can load 2x SDXL models vs diffusers crashing

**Weaknesses:**
- **Learning curve:** Node-based thinking (but we only need Python API, not GUI)
- **Abstraction layer:** Nodes wrap diffusers → slight overhead (acceptable for 2x gains)

**Migration Path:**
```python
# ComfyUI Python API (simplified)
from comfyui_api import ComfyUIClient, Workflow

client = ComfyUIClient("http://localhost:8188")
workflow = Workflow()
workflow.add_node("LoadCheckpoint", model="realisticVision.safetensors")
workflow.add_node("LoadLora", lora="emma_v2.safetensors", strength=0.8)
workflow.add_node("KSampler", steps=30, cfg=7.0, sampler="dpmpp_2m_karras")
workflow.add_node("UpscaleWithModel", upscaler="RealESRGAN_x4plus")
images = client.queue_and_wait(workflow)
```

#### 2. diffusers (Alternative)
**Strengths:**
- **Pure Python:** No abstraction, full control
- **HuggingFace official:** Best docs, most maintained
- **Flexibility:** Easy to customize schedulers/pipelines

**Weaknesses:**
- **Performance:** Slower than ComfyUI without heavy optimization (enable_model_cpu_offload(), xformers)
- **Manual batching:** No automatic caching → need custom logic
- **Extension integration:** ADetailer/ControlNet require DIY glue code

**Best for:** Research, custom schedulers, full pipeline control

#### 3. sd-scripts (Specialized)
**Focus:** Training (LoRA, DreamBooth) → not ideal for inference
**Use case:** Integrate for self-improving loop (Phase 5: CLIP scoring → retrain LoRA)

#### 4. InvokeAI (Solid #2)
**Strengths:** Good performance, plugin system, REST API
**Weaknesses:** Smaller ecosystem than ComfyUI, less batch optimization

---

## 2. Architecture Design

### 2.1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SD Generator CLI (V2.0)                     │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ Template      │→ │ Orchestrator │→ │ Prompt Generator │    │
│  │ System V2.0   │  │ (V2Pipeline) │  │ (Variations)     │    │
│  └───────────────┘  └──────────────┘  └──────────────────┘    │
│                              ↓                                  │
│                    ┌─────────────────┐                         │
│                    │ Generation      │                         │
│                    │ Executor        │ ← NEW: Direct Pipeline  │
│                    └─────────────────┘                         │
│                              ↓                                  │
└──────────────────────────────┼──────────────────────────────────┘
                               ↓
                ┌──────────────┴───────────────┐
                │                              │
      ┌─────────▼──────────┐       ┌──────────▼─────────┐
      │   HTTP API Client  │       │  Direct Pipeline   │ ← NEW
      │   (sdapi_client)   │       │  (pipeline_client) │
      └─────────┬──────────┘       └──────────┬─────────┘
                │                              │
                ↓                              ↓
      ┌─────────────────┐           ┌──────────────────┐
      │  A1111 WebUI    │           │  ComfyUI Backend │
      │  (HTTP:7860)    │           │  (Python API)    │
      └─────────────────┘           └──────────────────┘
                │                              │
                └──────────────┬───────────────┘
                               ↓
                      ┌────────────────┐
                      │  PyTorch       │
                      │  (CUDA/ROCm)   │
                      └────────────────┘
```

### 2.2. New Module: `pipeline_client.py`

**Responsibility:** Abstract ComfyUI workflow execution behind unified interface

```python
# sd_generator_cli/api/pipeline_client.py

from dataclasses import dataclass
from typing import Optional, List
import base64

@dataclass
class PipelineConfig:
    """Configuration for direct pipeline generation"""
    steps: int = 30
    cfg_scale: float = 7.0
    width: int = 512
    height: int = 768
    sampler_name: str = "dpmpp_2m_karras"
    scheduler: Optional[str] = "karras"
    batch_size: int = 1  # NEW: Native batching

    # LoRA support
    lora_models: List[dict] = []  # [{"name": "emma_v2", "strength": 0.8}]

    # Upscaler
    enable_upscale: bool = False
    upscaler: str = "RealESRGAN_x4plus"
    upscale_factor: float = 2.0

    # ADetailer (future)
    enable_adetailer: bool = False
    adetailer_models: List[str] = []

@dataclass
class PipelinePromptConfig:
    """Prompt config for pipeline"""
    prompt: str
    negative_prompt: str = ""
    seed: Optional[int] = None
    filename: str = ""

class DirectPipelineClient:
    """
    Pure Python client for direct SD pipeline via ComfyUI API

    Compatible interface with SDAPIClient for drop-in replacement.
    """

    def __init__(self, api_url: str = "http://127.0.0.1:8188"):
        self.api_url = api_url
        self.config = PipelineConfig()
        self._comfy_client = ComfyUIClient(api_url)

    def set_generation_config(self, config: PipelineConfig):
        self.config = config

    def generate_image(self, prompt_config: PipelinePromptConfig, timeout: int = 300) -> dict:
        """Generate via ComfyUI workflow (compatible with SDAPIClient.generate_image)"""
        workflow = self._build_workflow(prompt_config)
        result = self._comfy_client.queue_and_wait(workflow, timeout)

        # Convert ComfyUI output to A1111-compatible format
        return {
            "images": [base64.b64encode(img).decode() for img in result],
            "parameters": self._get_generation_params(),
            "info": json.dumps({"seed": prompt_config.seed or -1})
        }

    def generate_batch(self, prompts: List[PipelinePromptConfig], timeout: int = 600) -> List[dict]:
        """
        NEW: Batch generation (not available in A1111 API)

        Generates multiple images in single pipeline run with model caching.
        """
        # Build single workflow with batch nodes
        workflow = self._build_batch_workflow(prompts)
        results = self._comfy_client.queue_and_wait(workflow, timeout)
        return self._parse_batch_results(results, prompts)

    def _build_workflow(self, prompt_config: PipelinePromptConfig) -> ComfyWorkflow:
        """Build ComfyUI workflow from prompt config"""
        wf = ComfyWorkflow()

        # 1. Load checkpoint
        model_node = wf.add_node("CheckpointLoaderSimple",
                                  ckpt_name=self.config.checkpoint)

        # 2. Load LoRAs (chain multiple if needed)
        current_model = model_node["model"]
        for lora in self.config.lora_models:
            lora_node = wf.add_node("LoraLoader",
                                     model=current_model,
                                     lora_name=lora["name"],
                                     strength_model=lora["strength"],
                                     strength_clip=lora["strength"])
            current_model = lora_node["model"]

        # 3. CLIP text encode
        positive = wf.add_node("CLIPTextEncode",
                                text=prompt_config.prompt,
                                clip=model_node["clip"])
        negative = wf.add_node("CLIPTextEncode",
                                text=prompt_config.negative_prompt,
                                clip=model_node["clip"])

        # 4. Empty latent
        latent = wf.add_node("EmptyLatentImage",
                              width=self.config.width,
                              height=self.config.height,
                              batch_size=self.config.batch_size)

        # 5. KSampler
        samples = wf.add_node("KSampler",
                               model=current_model,
                               seed=prompt_config.seed or -1,
                               steps=self.config.steps,
                               cfg=self.config.cfg_scale,
                               sampler_name=self.config.sampler_name,
                               scheduler=self.config.scheduler,
                               positive=positive["conditioning"],
                               negative=negative["conditioning"],
                               latent_image=latent["latent"])

        # 6. VAE Decode
        image = wf.add_node("VAEDecode",
                             samples=samples["latent"],
                             vae=model_node["vae"])

        # 7. Upscaler (if enabled)
        if self.config.enable_upscale:
            upscale_model = wf.add_node("UpscaleModelLoader",
                                         model_name=self.config.upscaler)
            image = wf.add_node("ImageUpscaleWithModel",
                                 upscale_model=upscale_model["upscale_model"],
                                 image=image["image"])

        # 8. Save image
        wf.add_node("SaveImage",
                     images=image["image"],
                     filename_prefix=prompt_config.filename)

        return wf
```

### 2.3. Migration Strategy

**Phase 1: Adapter Pattern**
```python
# sd_generator_cli/api/generator_factory.py

class GeneratorFactory:
    """Factory to create API client or Pipeline client"""

    @staticmethod
    def create(mode: str = "api", api_url: str = "...") -> Union[SDAPIClient, DirectPipelineClient]:
        if mode == "api":
            return SDAPIClient(api_url)
        elif mode == "pipeline":
            return DirectPipelineClient(api_url)
        else:
            raise ValueError(f"Unknown mode: {mode}")
```

**Phase 2: Drop-in Replacement**
```python
# Executor just swaps client
from sd_generator_cli.api.generator_factory import GeneratorFactory

# Old: client = SDAPIClient(api_url)
# New: client = GeneratorFactory.create(mode="pipeline", api_url=pipeline_url)
```

**Phase 3: Feature-specific routing**
```python
# Use pipeline for batch, API for ADetailer (until Phase 3 complete)
if len(prompts) > 10 and not adetailer_enabled:
    client = DirectPipelineClient()
    client.generate_batch(prompts)
else:
    client = SDAPIClient()
    for prompt in prompts:
        client.generate_image(prompt)
```

---

## 3. Compatibility with Existing System

### 3.1. Template System V2.0 ✅ COMPATIBLE

**No changes required** to:
- Placeholders (`{HairCut}`, `{Expression}`)
- Variations loading (`.yaml` files)
- Chunks (`@CharacterBase`)
- Inheritance (`implements:`)
- Themes (`--theme cyberpunk`)
- Import resolution
- Prompt normalization

**Why:** Template system outputs **final prompts** (strings) → agnostic to execution backend

### 3.2. Session Management ✅ COMPATIBLE

**No changes required** to:
- Session folder naming (`20251029_143022-teasing-cyberpunk-cartoon`)
- Directory structure (`/apioutput/`)
- Dry-run mode (`/dryrun/` subdirectory)

**Minor change:**
- `session_config.txt` → Add "Pipeline: ComfyUI" metadata line

### 3.3. Manifest Generation ✅ COMPATIBLE

**Manifest structure unchanged:**
```json
{
  "snapshot": {
    "version": "2.0",
    "timestamp": "2025-10-31T14:30:22",
    "runtime_info": {
      "checkpoint": "realisticVision_v60.safetensors",
      "pipeline": "ComfyUI"  // ← NEW field
    }
  },
  "images": [
    {
      "filename": "001_emma_happy_blonde.png",
      "seed": 42,
      "prompt": "masterpiece, emma watson, happy, blonde hair...",
      "applied_variations": {"Expression": "happy", "HairColor": "blonde"}
    }
  ]
}
```

### 3.4. Feature Parity Checklist

| Feature | A1111 API | ComfyUI Pipeline | Phase | Status |
|---------|-----------|------------------|-------|--------|
| **txt2img** | ✅ | ✅ | 2 | Core |
| **img2img** | ✅ | ✅ | 2 | Core |
| **LoRA loading** | ✅ | ✅ | 3 | MVP |
| **Multiple LoRAs** | ✅ | ✅ | 3 | MVP |
| **Upscalers** | ✅ | ✅ | 3 | MVP |
| **Hires Fix** | ✅ | ✅ (latent upscale) | 3 | MVP |
| **Batch size** | ⚠️ (limited) | ✅ (native) | 2 | Core |
| **ADetailer** | ✅ | ✅ (custom node) | 4 | Advanced |
| **ControlNet** | ✅ | ✅ (custom node) | 4 | Advanced |
| **Schedulers** | ✅ | ✅ | 2 | Core |
| **VAE selection** | ✅ | ✅ | 3 | MVP |
| **CLIP skip** | ✅ | ✅ | 3 | MVP |

**Migration Risk:** LOW (95%+ feature overlap)

---

## 4. Hardware Requirements & Performance Estimates

### 4.1. RTX 5070 Ti (16GB VRAM) - Current Hardware

**SDXL Base (1024×1024):**
- **Batch size:** 1-2 images (8-12GB VRAM used)
- **Inference time:** ~3-5 sec/image (ComfyUI optimized)
- **With LoRA + upscaler:** ~8-12 sec/image
- **With ADetailer (2 detailers):** ~15-20 sec/image

**SD 1.5 (512×768):**
- **Batch size:** 4-8 images (efficient VRAM usage)
- **Inference time:** ~1-2 sec/image
- **With LoRA + upscaler:** ~3-5 sec/image

**Current workflow (1248×1824, LoRA, upscaler, 2 detailers):**
- **A1111 API:** 36 sec/image
- **ComfyUI pipeline (estimated):** **12-18 sec/image** (2-3x speedup)

**Bottlenecks:**
- VRAM limits batch size to 1-2 for high-res SDXL
- ADetailer requires multiple passes → slower

### 4.2. NVIDIA H100 (80GB VRAM) - Future Hardware

**SDXL Base (1024×1024):**
- **Batch size:** 16-32 images (parallel processing)
- **Inference time:** ~1.5 sec/image (TensorRT optimized)
- **With LoRA + upscaler:** ~3-5 sec/image
- **With ADetailer:** ~6-8 sec/image

**Current workflow (1248×1824):**
- **Estimated:** **5-8 sec/image** (4.5-7x speedup vs current)

**Batch processing gains:**
- **128 images batch:** ~10-15 minutes total (vs ~77 min with A1111)
- **Model caching:** Load once, generate many → 80% time savings

**Benefits:**
- Massive batch sizes (32-64 images)
- Multiple LoRAs without swapping
- ADetailer + ControlNet simultaneously
- Future-ready for SDXL Turbo (sub-second generation)

### 4.3. Performance Comparison Summary

| Configuration | A1111 API (Current) | ComfyUI (5070 Ti) | ComfyUI (H100) |
|---------------|---------------------|-------------------|----------------|
| **1 image (SDXL 1024×1024)** | 15 sec | 5 sec | 2 sec |
| **1 image (Current workflow)** | 36 sec | 14 sec | 6 sec |
| **10 images (sequential)** | 360 sec (6 min) | 140 sec (2.3 min) | 60 sec (1 min) |
| **100 images (batch)** | 3600 sec (60 min) | 1400 sec (23 min) | 600 sec (10 min) |
| **Batch size limit** | 1-2 | 2-4 | 32-64 |
| **Model reload overhead** | High | Low (cached) | Minimal |

**ROI Analysis:**
- **5070 Ti:** 2.5x speedup → 38k images in 146 hours (vs 380 hours)
- **H100:** 6x speedup → 38k images in 63 hours (vs 380 hours)
- **H100 amortization:** If generating 10k+ images/month, H100 pays for itself in dev time savings

---

## 5. Implementation Phases

### Phase 0: Infrastructure Setup (1 week)

**Goal:** ComfyUI backend ready for API calls

**Tasks:**
- [ ] Install ComfyUI standalone (`git clone`, `pip install`)
- [ ] Configure API server (`python main.py --listen 127.0.0.1:8188`)
- [ ] Test basic workflow via Python API
- [ ] Document ComfyUI setup process
- [ ] Verify custom nodes installation (LoRA loader, upscalers)

**Success Criteria:**
- ComfyUI server responds to API ping
- Can execute simple txt2img workflow via Python
- Custom nodes loaded successfully

**Effort:** 1-2 days (mostly setup/testing)

---

### Phase 1: POC (Proof of Concept) - 2 weeks

**Goal:** Generate 1 image via ComfyUI Python API

**Tasks:**
- [ ] Create `DirectPipelineClient` skeleton (basic txt2img)
- [ ] Implement `_build_workflow()` for single prompt
- [ ] Implement `generate_image()` with A1111-compatible output format
- [ ] Test with simple prompt: "a photo of a cat, masterpiece"
- [ ] Verify output matches A1111 quality (same seed, same result)
- [ ] Write unit tests for workflow builder

**Success Criteria:**
- Generate 1 image via `DirectPipelineClient.generate_image()`
- Output format matches `SDAPIClient` (base64 images, parameters, info)
- Visual quality comparable to A1111 (human eval)

**Effort:** 5-10 days
**Risk:** Low (ComfyUI API well-documented)

**Deliverables:**
- `sd_generator_cli/api/pipeline_client.py` (basic version)
- `tests/unit/api/test_pipeline_client.py`
- POC demo script (`examples/poc_direct_pipeline.py`)

---

### Phase 2: Core Pipeline (txt2img + img2img) - 4 weeks

**Goal:** Feature parity with basic A1111 API (no extensions)

**Tasks:**
- [ ] Implement `PipelineConfig` dataclass (steps, cfg, size, sampler, scheduler)
- [ ] Implement scheduler support (Karras, Exponential, SGM Uniform)
- [ ] Implement sampler support (all A1111 samplers → ComfyUI equivalents)
- [ ] Implement batch size control (`batch_size` param)
- [ ] Add VAE selection support
- [ ] Add CLIP skip support
- [ ] Implement img2img workflow (`init_image`, `denoising_strength`)
- [ ] Add error handling (ComfyUI errors → user-friendly messages)
- [ ] Integration tests with Template System V2.0
- [ ] Performance benchmarks (vs A1111 API)

**Success Criteria:**
- Can generate images with all samplers/schedulers
- img2img works correctly
- Batch size 1-4 works on 5070 Ti
- Template System V2.0 works end-to-end with `DirectPipelineClient`
- Performance: 1.5-2x faster than A1111 API

**Effort:** 15-20 days
**Risk:** Medium (scheduler mapping complexity)

**Deliverables:**
- Complete `DirectPipelineClient` (txt2img, img2img)
- Integration tests with real templates
- Performance report (benchmarks)
- Migration guide (A1111 API → Pipeline)

---

### Phase 3: Advanced Features (LoRA + Upscalers) - 4 weeks

**Goal:** MVP for production use (80% of current features)

**Tasks:**
- [ ] Implement LoRA loading (`lora_models` list in `PipelineConfig`)
- [ ] Support multiple LoRAs (chain nodes)
- [ ] Implement upscaler integration (RealESRGAN, ESRGAN, R-ESRGAN 4x+)
- [ ] Implement Hires Fix equivalent (latent upscale node)
- [ ] Add checkpoint switching support
- [ ] Optimize memory management (model offloading)
- [ ] Batch generation optimization (`generate_batch()` method)
- [ ] End-to-end testing with real use cases (Emma character, expressions)
- [ ] Documentation (API reference, migration guide)

**Success Criteria:**
- Can load 2-3 LoRAs simultaneously
- Upscalers work correctly (4x scale)
- Batch generation 5-10 images works
- Memory usage optimized (no OOM on 5070 Ti)
- Performance: 2-3x faster than A1111 API

**Effort:** 15-20 days
**Risk:** Medium (LoRA chaining complexity)

**Deliverables:**
- Production-ready `DirectPipelineClient`
- LoRA + upscaler examples
- User documentation
- API reference docs

**MVP COMPLETE** ✅ (Can replace A1111 API for 80% of use cases)

---

### Phase 4: Extensions (ADetailer + ControlNet) - 4-6 weeks

**Goal:** 100% feature parity with A1111 API

**Tasks:**
- [ ] Research ComfyUI ADetailer custom node
- [ ] Implement ADetailer workflow integration
- [ ] Support multiple detectors (face, hand, person)
- [ ] Implement ControlNet workflow integration
- [ ] Support ControlNet preprocessors (canny, depth, openpose)
- [ ] Test ADetailer + ControlNet combinations
- [ ] Optimize multi-pass workflows (detailers)
- [ ] Backward compatibility testing (all existing templates)

**Success Criteria:**
- ADetailer works with 2+ detectors
- ControlNet works with common preprocessors
- Can combine ADetailer + ControlNet + LoRA
- All existing templates work without modification

**Effort:** 20-30 days
**Risk:** High (complex node interactions, debugging)

**Deliverables:**
- Full-featured `DirectPipelineClient`
- ADetailer + ControlNet integration
- Compatibility report (100% templates working)

---

### Phase 5: Batch Optimization + CLIP Integration - 6 weeks

**Goal:** Maximize throughput + foundation for self-improving pipeline

**Tasks:**
- [ ] Optimize batch processing (memory-efficient batching)
- [ ] Implement smart caching (model + LoRA preloading)
- [ ] Benchmark large batches (100+ images)
- [ ] CLIP scoring integration (image quality evaluation)
- [ ] CLIP-based filtering (reject low-quality generations)
- [ ] Export CLIP scores to manifest.json
- [ ] Foundation for self-improving loop (CLIP → training data selection)
- [ ] H100 optimization testing (if hardware available)

**Success Criteria:**
- Can generate 100 images in single batch
- CLIP scores exported for all images
- Performance: 5-7x faster than A1111 API (on H100)
- Memory usage optimized for large batches

**Effort:** 30+ days
**Risk:** Medium (CLIP integration complexity)

**Deliverables:**
- Batch-optimized pipeline
- CLIP scoring system
- Foundation for Phase 6 (self-improving loop)

---

### Phase 6: Self-Improving Loop (Future) - 8+ weeks

**Goal:** Automated quality improvement pipeline

**Workflow:**
```
Generate 1000 images → CLIP score all → Select top 10% →
Train LoRA on best → Use new LoRA for next batch → Repeat
```

**Tasks:**
- [ ] Integrate sd-scripts for LoRA training
- [ ] Automatic training data preparation
- [ ] LoRA training automation
- [ ] Version management (LoRA v1, v2, v3...)
- [ ] A/B testing framework (compare LoRA versions)
- [ ] Convergence detection (when to stop improving)

**Effort:** 40+ days (research project)
**Risk:** High (uncharted territory)

---

## 6. Effort Estimation Summary

| Phase | Description | Duration | Parallel? | Dependencies |
|-------|-------------|----------|-----------|--------------|
| **0** | Infrastructure | 1 week | No | None |
| **1** | POC | 2 weeks | No | Phase 0 |
| **2** | Core Pipeline | 4 weeks | No | Phase 1 |
| **3** | Advanced (LoRA + Upscale) | 4 weeks | No | Phase 2 |
| **4** | Extensions (ADetailer + CN) | 4-6 weeks | Partial | Phase 3 |
| **5** | Batch + CLIP | 6 weeks | Partial | Phase 3 |
| **6** | Self-Improving Loop | 8+ weeks | No | Phase 5 |
| **TOTAL (MVP)** | Phase 0-3 | **11 weeks** | Sequential | - |
| **TOTAL (Full)** | Phase 0-5 | **17-19 weeks** | Some parallel | - |

**Critical Path:** Phase 0 → 1 → 2 → 3 (11 weeks to MVP)

**Resource Requirements:**
- **1 developer** full-time (Phases 0-3)
- **Optional:** 2nd developer for Phase 4-5 parallelization
- **GPU access:** 5070 Ti (minimum), H100 (Phase 5 optimization)

---

## 7. Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **ComfyUI API breaking changes** | Medium | High | Pin ComfyUI version, monitor releases |
| **Feature parity gaps** | Low | Medium | Phased rollout, fallback to A1111 API |
| **Performance not meeting targets** | Low | Medium | Benchmark early (POC), optimize iteratively |
| **Custom node compatibility** | Medium | Medium | Test nodes in Phase 0, have Plan B |
| **VRAM limitations (5070 Ti)** | Medium | Low | Optimize batch sizes, upgrade to H100 |
| **Template system integration bugs** | Low | High | Integration tests in Phase 2 |
| **Learning curve (ComfyUI)** | Medium | Low | Extensive docs, community support |
| **Migration regression** | Medium | High | Parallel testing, A/B comparison |

**Overall Risk:** **MEDIUM** (manageable with phased approach)

**Mitigation Strategy:**
1. **Incremental migration:** Keep A1111 API as fallback during Phases 1-3
2. **Feature flags:** `--use-pipeline` CLI flag to opt-in
3. **Parallel testing:** Run both APIs, compare outputs
4. **Rollback plan:** Keep A1111 API code until Phase 4 complete

---

## 8. Success Criteria & Validation

### Phase 1 Success (POC)
- ✅ Generate 1 image via ComfyUI API
- ✅ Output format matches A1111 API
- ✅ Visual quality identical (same seed → same image)

### Phase 2 Success (Core)
- ✅ All samplers/schedulers work
- ✅ img2img functional
- ✅ Template System V2.0 compatible
- ✅ Performance: 1.5-2x faster than A1111

### Phase 3 Success (MVP)
- ✅ LoRA loading works (1-3 LoRAs)
- ✅ Upscalers functional
- ✅ Batch generation (5-10 images)
- ✅ Performance: 2-3x faster than A1111
- ✅ **Can replace A1111 API for 80% of use cases**

### Phase 4 Success (Full Parity)
- ✅ ADetailer works
- ✅ ControlNet works
- ✅ 100% of existing templates work
- ✅ **Can deprecate A1111 API**

### Phase 5 Success (Optimized)
- ✅ Batch 100+ images
- ✅ CLIP scoring integrated
- ✅ Performance: 5-7x faster (H100)
- ✅ **Ready for self-improving loop**

---

## 9. Recommendation & Next Steps

### Final Recommendation

**Framework:** ComfyUI (Python API mode)
**Approach:** Phased migration (incremental, low-risk)
**MVP Timeline:** 11 weeks (Phases 0-3)
**Full Timeline:** 17-19 weeks (Phases 0-5)

**Why ComfyUI?**
1. **Proven performance:** 2x faster than A1111 in benchmarks
2. **Ecosystem maturity:** 500+ custom nodes, active community
3. **Future-proof:** Node-based = extensible, maintainable
4. **Batch optimization:** Native caching = exponential gains
5. **Feature parity:** All A1111 features available as nodes

**Why NOT diffusers?**
- Requires manual optimization (xformers, cpu_offload)
- No automatic caching (need custom logic)
- ADetailer/ControlNet integration = DIY glue code
- **Tradeoff:** More control, but more complexity

### Immediate Next Steps

1. **Week 1-2: Stakeholder alignment**
   - Review this spec with team
   - Approve framework choice (ComfyUI)
   - Approve phased approach
   - Allocate resources (1 dev, GPU access)

2. **Week 3-4: Phase 0 (Infrastructure)**
   - Install ComfyUI
   - Configure API server
   - Test basic workflow
   - Document setup

3. **Week 5-6: Phase 1 (POC)**
   - Implement `DirectPipelineClient` skeleton
   - Generate first image via API
   - Validate output format
   - Demo to stakeholders

4. **Week 7+: Continue phases 2-3**
   - Follow implementation plan
   - Weekly progress reviews
   - Adjust timeline based on learnings

### Decision Framework

**Should we proceed?**
- ✅ **YES if:** Goal is 3-7x performance gain + future scalability
- ✅ **YES if:** Planning to generate 10k+ images/month
- ✅ **YES if:** Want foundation for self-improving loop
- ⚠️ **MAYBE if:** A1111 API "good enough" for current needs
- ❌ **NO if:** No bandwidth for 11-week migration

**MVP vs Full Implementation?**
- **MVP (Phase 0-3):** Production-ready for 80% of use cases, 11 weeks
- **Full (Phase 0-5):** 100% parity + optimization, 17-19 weeks

**Recommended:** Start with **Phase 0-1 (POC)** → validate approach → commit to full MVP

---

## 10. Appendix

### A. ComfyUI Node Reference

**Core Nodes (txt2img):**
- `CheckpointLoaderSimple`: Load model checkpoint
- `CLIPTextEncode`: Encode prompt/negative prompt
- `EmptyLatentImage`: Create latent canvas
- `KSampler`: Diffusion sampling
- `VAEDecode`: Decode latent → image
- `SaveImage`: Save to disk

**LoRA Nodes:**
- `LoraLoader`: Load single LoRA
- `LoraLoaderModelOnly`: Load LoRA (model-only, skip CLIP)

**Upscaler Nodes:**
- `UpscaleModelLoader`: Load upscaler model
- `ImageUpscaleWithModel`: Apply upscaler
- `LatentUpscale`: Hires Fix equivalent

**ADetailer Nodes (Custom):**
- `ADetailerNode`: Face/hand detection + refinement

**ControlNet Nodes (Custom):**
- `ControlNetLoader`: Load ControlNet model
- `ControlNetApply`: Apply conditioning
- `CannyEdgePreprocessor`: Preprocessor

### B. Performance Benchmarks (External Sources)

**ComfyUI vs A1111 (from web search):**
- Batch 10 images: ComfyUI 1m07s vs A1111 2m23s (112% faster)
- Single SDXL image (30 steps): ComfyUI ~2s vs A1111 ~4s
- Memory efficiency: ComfyUI can load 2x SDXL models vs diffusers crash

**H100 vs 5070 Ti (estimated):**
- H100: 1.5s/image SDXL (TensorRT optimized)
- 5070 Ti: 3-5s/image SDXL (standard)
- Batch size: H100 32-64x, 5070 Ti 2-4x

### C. Code Examples

**Example 1: Basic txt2img**
```python
from sd_generator_cli.api.pipeline_client import DirectPipelineClient, PipelinePromptConfig

client = DirectPipelineClient("http://localhost:8188")
prompt = PipelinePromptConfig(
    prompt="masterpiece, emma watson, happy smile, blonde hair",
    negative_prompt="low quality, blurry",
    seed=42
)
result = client.generate_image(prompt)
# result["images"][0] = base64-encoded PNG
```

**Example 2: Batch generation with LoRA**
```python
from sd_generator_cli.api.pipeline_client import DirectPipelineClient, PipelineConfig, PipelinePromptConfig

client = DirectPipelineClient()
config = PipelineConfig(
    lora_models=[{"name": "emma_v2.safetensors", "strength": 0.8}],
    batch_size=4
)
client.set_generation_config(config)

prompts = [
    PipelinePromptConfig(prompt=f"emma watson, {expr}", seed=i)
    for i, expr in enumerate(["happy", "sad", "surprised", "angry"])
]
results = client.generate_batch(prompts)
# 4 images generated in single pipeline run
```

### D. Migration Checklist

**Pre-Migration:**
- [ ] Backup current A1111 API setup
- [ ] Document current performance metrics
- [ ] Create test suite (visual regression)
- [ ] Allocate GPU resources

**During Migration (Phase 1-3):**
- [ ] Keep A1111 API running (fallback)
- [ ] Parallel testing (both APIs)
- [ ] Feature flag rollout (`--use-pipeline`)
- [ ] Monitor performance/quality

**Post-Migration (Phase 4+):**
- [ ] Deprecate A1111 API code
- [ ] Update documentation
- [ ] Archive A1111 workflows
- [ ] Celebrate 🎉

---

## Document Metadata

**Revision:** 1.0
**Last Updated:** 2025-10-31
**Next Review:** After Phase 1 completion
**GitHub Issue:** TBD (create after approval)
**Reviewers:** Product Owner, Tech Lead
**Approval Status:** DRAFT

---

**END OF SPECIFICATION**
