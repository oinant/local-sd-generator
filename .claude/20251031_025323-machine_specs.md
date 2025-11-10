# Machine Specifications

**Last Updated:** 2025-10-31

---

## Hardware Configuration

### System
- **OS:** Windows (via WSL2 Ubuntu 22.04.5 LTS)
- **Kernel:** 5.15.146.1-microsoft-standard-WSL2
- **Architecture:** x86_64
- **Terminal:** Windows Terminal
- **Resolution:** 3440x1440 (Ultrawide)

### CPU
- **Model:** AMD Ryzen 7 3800X 8-Core Processor
- **Cores:** 8 physical cores
- **Threads:** 16 logical processors
- **Base Clock:** 3.9 GHz
- **Boost Clock:** ~4.5 GHz

### GPU
- **Model:** NVIDIA GeForce RTX 5070 Ti
- **Architecture:** Ada Lovelace (5000 series)
- **VRAM:** ~16 GB GDDR6X (estimated)
- **CUDA Cores:** ~9000+ (estimated)
- **Tensor Cores:** 5th Generation
- **RT Cores:** 4th Generation

### Memory (RAM)
- **Total:** 63.9 GB
- **Available:** ~32 GB typical
- **Type:** DDR4 (estimated)
- **Usage (current):** 31.38 GiB / 63.9 GiB (49%)

### Storage
- **System Drive (C:):** 464 GB
- **Used:** 432 GB (92% full)
- **WSL Drive:** 1007 GB
- **Used:** 25 GB (3%)

---

## Software Environment

### Python
- **Version:** Python 3.10.12
- **Virtual Env:** `/venv/` (shared monorepo)
- **Package Manager:** pip

### Development Tools
- **Git:** GitBash + WSL
- **IDE:** VS Code (assumed)
- **Terminal:** Windows Terminal

### SD Generation Stack
- **Stable Diffusion WebUI:** Automatic1111
- **API URL:** http://172.29.128.1:7860
- **Output Directory:** `/mnt/d/StableDiffusion/private-new/results/`
- **Generated Images:** 38,000+ (58 GB)
- **Sessions:** 600+

---

## Performance Capabilities

### Image Generation (Stable Diffusion)
- **Tested:** 38k+ images generated successfully
- **Largest Batch:** 2650 images (single session)
- **Typical Performance:** ~5-10 images/min (depends on resolution/settings)

### AI Model Training (Estimated)
With RTX 5070 Ti specifications:

**LoRA Training:**
- **Resolution:** 768x768 (SDXL: 1024x1024)
- **Batch Size:** 8-16
- **Training Time:** 1-3h for quality LoRA
- **VRAM Usage:** ~14 GB (comfortable)

**CLIP/Vision Model Inference:**
- **Batch Size:** 128 images
- **Speed:** ~5-10 images/sec
- **38k Images Analysis:** 1-2 hours total

**Custom Classifier Training:**
- **Transfer Learning:** 30-60 minutes
- **From Scratch:** 2-4 hours
- **Batch Processing:** Very fast (large batches possible)

---

## System Limits & Recommendations

### Current Bottlenecks
- ✅ **GPU:** Excellent (5070 Ti = high-end)
- ✅ **RAM:** Abundant (64 GB)
- ✅ **CPU:** Good (16 threads)
- ⚠️ **Storage (C:):** 92% full (consider cleanup or expansion)
- ✅ **Storage (WSL):** Plenty of space

### Optimal Configurations

**For SD Generation:**
```yaml
batch_size: 4-8
resolution: 832x1216 (portrait) or 1216x832 (landscape)
enable_hr: true
hr_scale: 1.5-2.0
```

**For CLIP Analysis:**
```python
batch_size: 128  # Large batches OK with 16GB VRAM
mixed_precision: True  # FP16 for 2x speedup
num_workers: 8  # Leverage 16 CPU threads
```

**For LoRA Training:**
```python
batch_size: 8-16
gradient_accumulation: 4
mixed_precision: "fp16"
resolution: 768  # or 1024 for SDXL
xformers: True  # Memory optimization
```

---

## Notes

- **RTX 5070 Ti:** Flagship-class GPU, suitable for:
  - Professional SD image generation ✅
  - LoRA/DreamBooth training ✅
  - CLIP/vision model fine-tuning ✅
  - Custom classifier training ✅
  - Real-time inference (NSFW-CLIP, etc.) ✅

- **Ultrawide Monitor (3440x1440):** Ideal for:
  - Multi-panel development (code + terminal + browser)
  - Image gallery viewing
  - Manifest/stats dashboards

- **WSL2 Setup:** Optimal for:
  - Python development
  - CLI tools (sdgen)
  - GPU passthrough works well
  - Storage split: Windows (C:) + WSL (separate)

---

## Hardware Upgrade Considerations

**Not Needed:**
- GPU (5070 Ti is top-tier)
- RAM (64 GB is plenty)
- CPU (Ryzen 3800X still strong)

**Consider:**
- **Storage expansion on C:** Currently 92% full
  - Add NVMe SSD for models/datasets
  - Or move output directory to larger drive
- **Cooling:** Ensure adequate for sustained GPU training loads

---

## Verified Workloads

This system has successfully completed:
- ✅ 38,000+ image generations (58 GB)
- ✅ 600+ generation sessions
- ✅ Largest batch: 2650 images
- ✅ Themable template system (multiple themes)
- ✅ Validation of 681 YAML config files
- ✅ Stable for long-running generation jobs

**Conclusion:** This is a professional-grade AI/ML workstation, capable of all planned features including CLIP analysis, custom classifier training, and LoRA/checkpoint training.
