# Cloud GPU Burst - Product Specification

**Project:** H100 Cloud Compute Integration for SD Generator
**Author:** Agent PO + Architecte Cloud
**Date:** 2025-10-31
**Status:** Pre-Production Analysis
**Priority:** P4 (Strategic Investment)

---

## Executive Summary

### Context
The `local-sd-generator` project has successfully generated **38,000+ images** using Template System V2.0 via Automatic1111 HTTP API. Current performance on RTX 5070 Ti (16GB VRAM): **36 sec/image** with LoRA + upscaler + 2 detailers at 1248×1824px.

With the **Direct Pipeline** migration (spec: `docs/roadmap/future/direct_pipeline.md`) targeting ComfyUI, estimated performance improves to **14 sec/image** locally (2.5x speedup).

OVH offers **H100 (80GB VRAM)** instances at **€2.80/hour HT** (€3.36/hour TTC with 20% VAT), opening the opportunity to burst heavy workloads to cloud while keeping orchestration local.

### Problem Statement
Despite local hardware improvements, several bottlenecks remain:
- **VRAM limitations:** RTX 5070 Ti 16GB limits batch size to 1-4 images
- **Time-intensive workloads:** Large batches (500+ images) still take hours
- **LoRA training:** 3+ hours locally vs 20 min on H100
- **Scalability ceiling:** Cannot leverage massive parallel processing

### Proposed Solution
Implement a **hybrid cloud burst architecture** that:

1. **Keeps orchestration local:** sdgen CLI, Template System V2.0, session management
2. **Offloads compute to cloud:** H100 instances for heavy batch processing
3. **Optimizes costs:** Use cloud only when ROI is positive (100+ images, LoRA training)
4. **Seamless UX:** `sdgen generate --cloud` triggers cloud burst transparently

### Key Metrics

**Performance Gains (vs Local 5070 Ti + ComfyUI):**
- Single image: 14s → **6s** (2.3x speedup)
- 100 images: 23 min → **10 min** (2.3x speedup)
- 500 images: 1.94h → **50 min** (2.3x speedup)
- LoRA training: 3h → **20 min** (9x speedup)

**Cost Analysis (500 images example):**
- Cloud time: 50 min = 0.83h
- Setup overhead: 5 min = 0.08h
- Total: 0.91h × €3.36 = **€3.06**
- Cost per image: **€0.006**

**Break-even point:** ~50 images (setup cost amortized)

### Recommendation
**Proceed with Phased Approach:**
- **Phase 1 (POC):** Manual SSH + rsync workflow (2 weeks)
- **Phase 2 (MVP):** Automated provisioning + CLI integration (4 weeks)
- **Phase 3 (Production):** Multi-cloud support + cost optimization (6 weeks)

**Strategic value:**
- ✅ Enables 10x faster LoRA training (critical for self-improving loop)
- ✅ Foundation for massive batch processing (38k images in 1 day vs 5 days)
- ✅ Future-proof for cloud-native workflows (CLIP validation, A/B testing)
- ✅ Pay-per-use model (no upfront hardware investment)

---

## 1. VM Setup Guide (OVH H100)

### 1.1. Hardware Specifications

**OVH H100 Instance:**
- **GPU:** NVIDIA H100 (80GB VRAM)
- **CPU:** 26 cores Intel Xeon
- **RAM:** 200GB DDR5
- **Storage:** 800GB NVMe SSD (local scratch)
- **Network:** 25 Gbps bandwidth
- **Cost:** €2.80/h HT (€3.36/h TTC)

**Performance benchmarks (SDXL 1024×1024):**
- txt2img: ~2s/image (vs 5s on 5070 Ti)
- txt2img + LoRA + upscaler: ~6s/image (vs 14s on 5070 Ti)
- Batch size: 32-64 images (vs 2-4 on 5070 Ti)
- LoRA training: 20 min (vs 3h on 5070 Ti)

### 1.2. Base Image Selection

**Recommended:** Ubuntu 22.04 LTS + NVIDIA CUDA 12.1 (pre-installed)

**OVH Image Options:**
1. **Ubuntu 22.04 + CUDA Toolkit** (recommended)
   - Pre-installed: CUDA 12.1, cuDNN 8.9, NVIDIA drivers 535
   - Setup time: ~5 min (install Python packages only)
   - Image size: ~15 GB

2. **Ubuntu 22.04 Minimal** (custom setup)
   - Requires: CUDA installation (~1 GB download)
   - Setup time: ~15 min (full CUDA stack + Python)
   - More control but slower cold start

**Decision:** Use **Ubuntu 22.04 + CUDA Toolkit** for faster provisioning.

### 1.3. Storage Requirements

**Breakdown:**

| Component | Size | Notes |
|-----------|------|-------|
| **OS + CUDA** | 15 GB | Ubuntu + CUDA 12.1 |
| **Python packages** | 5 GB | PyTorch, ComfyUI, diffusers, xformers |
| **Stable Diffusion models** | 10-20 GB | SDXL checkpoint (6GB), LoRAs (1-5GB), VAE (1GB) |
| **Upscaler models** | 5 GB | RealESRGAN, ESRGAN 4x+ |
| **ComfyUI custom nodes** | 2 GB | ADetailer, ControlNet, etc. |
| **Temporary images** | 10 GB | Buffer for 1000 images @10MB each |
| **TOTAL** | **47-57 GB** | Comfortable with 800GB NVMe |

**Strategy:**
- **Persistent storage:** Models, checkpoints, LoRAs (~30 GB)
- **Ephemeral storage:** Generated images (~10 GB, deleted after download)
- **Model caching:** Keep models on instance for warm restarts

### 1.4. Network Bandwidth

**Upload requirements (Local → Cloud):**
- Prompts JSON: ~1 KB/prompt → 500 prompts = 500 KB
- LoRA files: 100-500 MB (if not cached)
- Total upload: **~500 MB** (first run), **~500 KB** (subsequent runs)

**Download requirements (Cloud → Local):**
- Images @1248×1824px PNG: ~4 MB/image
- 500 images: **~2 GB**
- Download time @50 Mbps: ~5 minutes

**Total data transfer per 500-image batch:** ~2.5 GB (mostly downloads)

### 1.5. Dependencies Installation

#### System Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system packages
sudo apt install -y \
  git \
  wget \
  curl \
  python3.10 \
  python3.10-venv \
  python3-pip \
  libgl1-mesa-glx \
  libglib2.0-0 \
  ffmpeg

# Verify CUDA installation
nvidia-smi  # Should show H100 GPU
nvcc --version  # Should show CUDA 12.1
```

#### Python Environment
```bash
# Create virtual environment
python3.10 -m venv /opt/sdgen-env
source /opt/sdgen-env/bin/activate

# Upgrade pip
pip install --upgrade pip wheel setuptools

# Install PyTorch with CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install core dependencies
pip install \
  transformers \
  diffusers \
  accelerate \
  xformers \
  safetensors \
  omegaconf \
  einops \
  pyyaml \
  requests \
  pillow \
  opencv-python \
  scipy \
  tqdm

# Verify PyTorch + CUDA
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}, Devices: {torch.cuda.device_count()}')"
# Expected: CUDA available: True, Devices: 1
```

#### ComfyUI Installation
```bash
# Clone ComfyUI
cd /opt
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI

# Install ComfyUI requirements
pip install -r requirements.txt

# Install custom nodes manager
cd custom_nodes
git clone https://github.com/ltdrdata/ComfyUI-Manager.git

# Install essential custom nodes
git clone https://github.com/Gourieff/comfyui-reactor-node.git  # Face swap
git clone https://github.com/Acly/comfyui-tooling-nodes.git  # Utilities
git clone https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git  # Workflows

cd /opt/ComfyUI
```

#### Model Setup
```bash
# Create model directories
mkdir -p /opt/ComfyUI/models/checkpoints
mkdir -p /opt/ComfyUI/models/loras
mkdir -p /opt/ComfyUI/models/vae
mkdir -p /opt/ComfyUI/models/upscale_models

# Models will be uploaded from local machine or downloaded via wget
# Example: Upload checkpoint
# rsync -avz local_checkpoint.safetensors user@h100:/opt/ComfyUI/models/checkpoints/
```

### 1.6. Setup Timing Estimates

| Setup Type | Duration | Components |
|------------|----------|------------|
| **Cold start (fresh VM)** | ~15 min | OS, CUDA verification, Python env, PyTorch, ComfyUI, custom nodes |
| **Warm start (pre-configured image)** | ~2 min | Start ComfyUI server, verify GPU |
| **Model upload (first run)** | ~5 min | Upload checkpoints, LoRAs (if not cached) |
| **Subsequent runs (models cached)** | ~30 sec | Start ComfyUI, load workflow |

**Recommendation:** Use custom AMI/image with everything pre-installed → **2-3 min startup** instead of 15 min.

### 1.7. Provisioning Script (Automated Setup)

```bash
#!/bin/bash
# setup_h100_instance.sh - Automated H100 instance setup for SD generation

set -e  # Exit on error

echo "=========================================="
echo "H100 SD Generator Setup - Starting"
echo "=========================================="

# 1. Update system
echo "[1/7] Updating system packages..."
sudo apt update && sudo apt upgrade -y

# 2. Install system dependencies
echo "[2/7] Installing system dependencies..."
sudo apt install -y git wget curl python3.10 python3.10-venv python3-pip \
  libgl1-mesa-glx libglib2.0-0 ffmpeg

# 3. Verify CUDA
echo "[3/7] Verifying CUDA installation..."
nvidia-smi
nvcc --version

# 4. Create Python environment
echo "[4/7] Setting up Python environment..."
python3.10 -m venv /opt/sdgen-env
source /opt/sdgen-env/bin/activate

# 5. Install PyTorch + dependencies
echo "[5/7] Installing PyTorch with CUDA 12.1..."
pip install --upgrade pip wheel setuptools
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

pip install transformers diffusers accelerate xformers safetensors \
  omegaconf einops pyyaml requests pillow opencv-python scipy tqdm

# Verify CUDA availability
python3 -c "import torch; assert torch.cuda.is_available(), 'CUDA not available!'; print(f'✓ CUDA available with {torch.cuda.device_count()} GPU(s)')"

# 6. Install ComfyUI
echo "[6/7] Installing ComfyUI..."
cd /opt
if [ ! -d "ComfyUI" ]; then
  git clone https://github.com/comfyanonymous/ComfyUI.git
fi
cd ComfyUI
pip install -r requirements.txt

# Install custom nodes
cd custom_nodes
[ ! -d "ComfyUI-Manager" ] && git clone https://github.com/ltdrdata/ComfyUI-Manager.git
[ ! -d "comfyui-reactor-node" ] && git clone https://github.com/Gourieff/comfyui-reactor-node.git
[ ! -d "comfyui-tooling-nodes" ] && git clone https://github.com/Acly/comfyui-tooling-nodes.git

# 7. Create model directories
echo "[7/7] Creating model directories..."
mkdir -p /opt/ComfyUI/models/{checkpoints,loras,vae,upscale_models}

echo "=========================================="
echo "✓ Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Upload models: rsync -avz models/ user@h100:/opt/ComfyUI/models/"
echo "2. Start ComfyUI: cd /opt/ComfyUI && source /opt/sdgen-env/bin/activate && python main.py --listen 0.0.0.0 --port 8188"
echo ""
```

**Usage:**
```bash
# Run on fresh H100 instance
bash setup_h100_instance.sh

# Total time: ~15 min
```

### 1.8. Dockerfile for Custom Image

```dockerfile
# Dockerfile for H100 SD Generator Image
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git wget curl python3.10 python3.10-venv python3-pip \
    libgl1-mesa-glx libglib2.0-0 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Create Python environment
RUN python3.10 -m venv /opt/sdgen-env

# Install Python packages
ENV PATH="/opt/sdgen-env/bin:$PATH"
RUN pip install --upgrade pip wheel setuptools && \
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 && \
    pip install transformers diffusers accelerate xformers safetensors \
    omegaconf einops pyyaml requests pillow opencv-python scipy tqdm

# Clone ComfyUI
RUN cd /opt && git clone https://github.com/comfyanonymous/ComfyUI.git && \
    cd ComfyUI && pip install -r requirements.txt

# Install custom nodes
RUN cd /opt/ComfyUI/custom_nodes && \
    git clone https://github.com/ltdrdata/ComfyUI-Manager.git && \
    git clone https://github.com/Gourieff/comfyui-reactor-node.git && \
    git clone https://github.com/Acly/comfyui-tooling-nodes.git

# Create model directories
RUN mkdir -p /opt/ComfyUI/models/{checkpoints,loras,vae,upscale_models}

# Expose ComfyUI port
EXPOSE 8188

# Set working directory
WORKDIR /opt/ComfyUI

# Entrypoint
CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188"]
```

**Build & Push:**
```bash
# Build image
docker build -t h100-sdgen:v1.0 .

# Push to registry (OVH container registry or Docker Hub)
docker tag h100-sdgen:v1.0 registry.example.com/h100-sdgen:v1.0
docker push registry.example.com/h100-sdgen:v1.0
```

**Benefits:**
- Pre-configured image → **2 min startup** (vs 15 min cold start)
- Reproducible environment
- Version control for dependencies

---

## 2. Architecture Hybrid (Local + Cloud)

### 2.1. High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     LOCAL MACHINE (Windows/WSL)                │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    SD Generator CLI                      │  │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────────────┐   │  │
│  │  │ Template   │→ │ V2Pipeline │→ │ Prompt Generator │   │  │
│  │  │ System V2  │  │ Orchestrator│  │ (Variations)    │   │  │
│  │  └────────────┘  └────────────┘  └──────────────────┘   │  │
│  │                          ↓                               │  │
│  │                 ┌────────────────┐                       │  │
│  │                 │ Cloud Manager  │  ← NEW MODULE         │  │
│  │                 │ (Provisioning, │                       │  │
│  │                 │  Job Submit,   │                       │  │
│  │                 │  Result Fetch) │                       │  │
│  │                 └────────────────┘                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          ↓                                      │
│                   ┌──────────────┐                              │
│                   │ SSH Tunnel   │                              │
│                   │ + rsync      │                              │
│                   └──────────────┘                              │
└───────────────────────────┬────────────────────────────────────┘
                            │
                            ↓ INTERNET (SSH/rsync)
                            │
┌───────────────────────────┴────────────────────────────────────┐
│                       OVH H100 INSTANCE                        │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    ComfyUI Server                        │  │
│  │                  (Python API Mode)                       │  │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────────────┐   │  │
│  │  │ Checkpoint │  │ LoRA       │  │ Upscaler         │   │  │
│  │  │ Loader     │  │ Loader     │  │ Models           │   │  │
│  │  └────────────┘  └────────────┘  └──────────────────┘   │  │
│  │                          ↓                               │  │
│  │                 ┌────────────────┐                       │  │
│  │                 │   KSampler     │  (Batch Processing)   │  │
│  │                 │   (Diffusion)  │                       │  │
│  │                 └────────────────┘                       │  │
│  │                          ↓                               │  │
│  │                 ┌────────────────┐                       │  │
│  │                 │  Output Images │                       │  │
│  │                 │  (/tmp/output/)│                       │  │
│  │                 └────────────────┘                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  GPU: H100 80GB VRAM                                            │
│  Storage: /opt/ComfyUI/models/ (persistent)                    │
│            /tmp/output/ (ephemeral)                             │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2. Communication Protocol

**Option A: SSH + rsync (MVP - Simple & Secure)**

**Pros:**
- ✅ Secure by default (SSH encryption)
- ✅ No custom API server needed
- ✅ Native rsync = fast, resumable transfers
- ✅ Simple authentication (SSH keys)

**Cons:**
- ❌ Less elegant than REST API
- ❌ Requires shell access to cloud instance
- ❌ Harder to implement retry logic

**Option B: REST API (Future - Scalable)**

**Pros:**
- ✅ Clean abstraction (HTTP endpoints)
- ✅ Easy retry/timeout handling
- ✅ Can add authentication layer (JWT tokens)
- ✅ Supports multiple clients

**Cons:**
- ❌ Requires custom API server on cloud
- ❌ More complex setup
- ❌ Security: need HTTPS + API keys

**Recommendation:** Start with **Option A (SSH + rsync)** for MVP, migrate to **Option B** in Phase 3.

### 2.3. Workflow Sequence (SSH + rsync)

```
┌─────────┐                                    ┌─────────┐
│  LOCAL  │                                    │  CLOUD  │
└────┬────┘                                    └────┬────┘
     │                                              │
     │ 1. User: sdgen generate --cloud -n 500      │
     │──────────────────────────────────────────▶  │
     │                                              │
     │ 2. Resolve template → 500 prompt configs    │
     │    (Template System V2.0)                   │
     │                                              │
     │ 3. Generate job manifest (JSON)             │
     │    {prompts: [...], config: {...}}          │
     │                                              │
     │ 4. Provision H100 instance (if needed)      │
     │    - OVH API: create instance               │
     │    - Wait for SSH ready (~2 min)            │
     │──────────────────────────────────────────▶  │
     │                                              │ ✓ Instance ready
     │                                              │
     │ 5. Upload job manifest + LoRAs              │
     │    rsync -avz job.json user@h100:/data/     │
     │    rsync -avz loras/ user@h100:/models/     │
     │──────────────────────────────────────────▶  │
     │                                              │ ✓ Files uploaded
     │                                              │
     │ 6. Execute remote generation                │
     │    ssh user@h100 "python3 generate.py       │
     │                   --job /data/job.json"     │
     │──────────────────────────────────────────▶  │
     │                                              │
     │                                              │ → Load checkpoint
     │                                              │ → Load LoRAs
     │                                              │ → Generate 500 images
     │                                              │    (batch 32 × 16 runs)
     │                                              │ → Save to /tmp/output/
     │                                              │
     │ 7. Poll for completion (SSH + status file)  │
     │    ssh user@h100 "cat /data/job_status.json"│
     │◀─────────────────────────────────────────────│
     │    {"status": "running", "progress": 250/500}│
     │                                              │
     │    ... (poll every 30s)                     │
     │                                              │
     │◀─────────────────────────────────────────────│
     │    {"status": "complete", "images": 500}    │
     │                                              │
     │ 8. Download results                         │
     │    rsync -avz user@h100:/tmp/output/        │
     │               ./session_folder/             │
     │◀─────────────────────────────────────────────│
     │                                              │ ✓ Images downloaded
     │                                              │
     │ 9. Teardown instance (optional)             │
     │    - Delete /tmp/output/ (cleanup)          │
     │    - Stop instance (save costs)             │
     │──────────────────────────────────────────▶  │
     │                                              │ ✓ Instance stopped
     │                                              │
     │ 10. Generate manifest.json locally          │
     │     (same as current workflow)              │
     │                                              │
     │ ✓ Session complete!                         │
     │                                              │
```

**Total time (500 images):**
- Provision: 2 min (if cold start) or 30s (warm instance)
- Upload: 1 min (prompts + LoRAs)
- Generate: 50 min (6s/image × 500)
- Download: 5 min (2GB images)
- **Total:** ~58 min (vs 1.94h local)

### 2.4. Job Manifest Format

```json
{
  "version": "1.0",
  "job_id": "job_20251031_143022_abc123",
  "config": {
    "checkpoint": "realisticVision_v60.safetensors",
    "loras": [
      {"name": "emma_v2.safetensors", "strength": 0.8}
    ],
    "generation": {
      "width": 1248,
      "height": 1824,
      "steps": 30,
      "cfg_scale": 7.0,
      "sampler": "dpmpp_2m_karras",
      "scheduler": "karras",
      "batch_size": 32
    },
    "upscaler": {
      "enabled": true,
      "model": "RealESRGAN_x4plus",
      "scale": 2.0
    }
  },
  "prompts": [
    {
      "id": "001",
      "prompt": "masterpiece, emma watson, happy smile, blonde hair, detailed",
      "negative_prompt": "low quality, blurry",
      "seed": 42,
      "filename": "001_emma_happy_blonde.png",
      "variations": {
        "Expression": "happy",
        "HairColor": "blonde"
      }
    },
    {
      "id": "002",
      "prompt": "masterpiece, emma watson, sad expression, brown hair, detailed",
      "negative_prompt": "low quality, blurry",
      "seed": 43,
      "filename": "002_emma_sad_brown.png",
      "variations": {
        "Expression": "sad",
        "HairColor": "brown"
      }
    }
    // ... 498 more prompts
  ]
}
```

### 2.5. Security Considerations

**SSH Key Authentication:**
```bash
# Generate SSH key pair (local)
ssh-keygen -t ed25519 -C "sdgen-cloud-burst"

# Add public key to H100 instance
# (done during provisioning via OVH API or cloud-init)

# Connect without password
ssh -i ~/.ssh/sdgen_cloud_burst user@h100.example.com
```

**Network Security:**
- ✅ SSH tunnel (encrypted)
- ✅ Firewall: Only allow SSH (port 22) from known IPs
- ✅ No public API exposed (ComfyUI runs on localhost:8188)
- ✅ API keys stored in local config (not in git)

**Data Privacy:**
- ⚠️ Prompts and images transit through cloud → ensure GDPR compliance if handling personal data
- ✅ Auto-delete images after download (ephemeral storage)
- ✅ Option to encrypt uploads (rsync over SSH already encrypts)

---

## 3. Cost Analysis (Cloud vs Local)

### 3.1. Hardware Context

**Local: RTX 5070 Ti (16GB VRAM)**
- Hardware cost: €600 (sunk cost, already purchased)
- Power consumption: 285W TDP
- Electricity cost: €0.20/kWh (Europe average)
- Lifespan: 5 years

**Cloud: OVH H100 (80GB VRAM)**
- Rental cost: €2.80/h HT = €3.36/h TTC (20% VAT)
- No upfront cost
- Pay-per-use (billed per second)

### 3.2. Performance Estimates

**Baseline: Current workflow (1248×1824, LoRA, upscaler, 2 detailers)**

| Hardware | Pipeline | Time/Image | Batch Size | Throughput |
|----------|----------|------------|------------|------------|
| **5070 Ti** | A1111 API | 36s | 1 | 100 images/h |
| **5070 Ti** | ComfyUI | 14s | 2-4 | 257 images/h |
| **H100** | ComfyUI | 6s | 32-64 | 600 images/h |

**Speedup factors:**
- 5070 Ti (A1111 → ComfyUI): **2.5x**
- H100 vs 5070 Ti (both ComfyUI): **2.3x**
- H100 vs 5070 Ti + A1111: **6x**

### 3.3. Cost Breakdown by Scenario

#### Scenario A: Generate 100 images

**Local (5070 Ti + ComfyUI):**
- Time: 100 × 14s = 1400s = **23.3 min**
- Electricity: 0.285 kW × 0.39h × €0.20 = **€0.022**
- Developer time saved: 0h (baseline)

**Cloud (H100 + ComfyUI):**
- Setup time: 2 min (warm instance)
- Generation time: 100 × 6s = 600s = **10 min**
- Download time: 400 MB @50 Mbps = **1 min**
- Total time: **13 min**
- Cloud cost: (2 + 10 + 1) min = 0.22h × €3.36 = **€0.74**

**Analysis:**
- Time saved: 23.3 - 13 = **10.3 min**
- Cost premium: €0.74 - €0.022 = **€0.72**
- **ROI:** Negative for 100 images (cost > electricity savings)
- **But:** If developer time = €50/h, 10 min saved = €8.33 value → **Positive ROI**

#### Scenario B: Generate 500 images

**Local (5070 Ti + ComfyUI):**
- Time: 500 × 14s = 7000s = **1.94h** (1h 56min)
- Electricity: 0.285 kW × 1.94h × €0.20 = **€0.11**

**Cloud (H100 + ComfyUI):**
- Setup: 2 min
- Generation: 500 × 6s = 3000s = **50 min**
- Download: 2 GB @50 Mbps = **5 min**
- Total time: **57 min** (0.95h)
- Cloud cost: 0.95h × €3.36 = **€3.19**

**Analysis:**
- Time saved: 1.94h - 0.95h = **59 min**
- Cost premium: €3.19 - €0.11 = **€3.08**
- **ROI:** If dev time = €50/h → saved value = €49 → **Positive ROI (+€45.92)**

#### Scenario C: Generate 38,000 images (historical)

**Local (5070 Ti + ComfyUI):**
- Time: 38000 × 14s = 532000s = **147.8 hours** (6.2 days)
- Electricity: 0.285 kW × 147.8h × €0.20 = **€8.42**

**Cloud (H100 + ComfyUI):**
- Batches: 38000 / 500 = 76 batches
- Time per batch: 57 min (from Scenario B)
- Total time: 76 × 57 min = 4332 min = **72.2 hours** (3 days)
- Cloud cost: 72.2h × €3.36 = **€242.59**

**Analysis:**
- Time saved: 147.8h - 72.2h = **75.6 hours**
- Cost premium: €242.59 - €8.42 = **€234.17**
- **ROI:** If dev time = €50/h → saved value = €3780 → **Positive ROI (+€3545.83)**

**Key insight:** For massive workloads (10k+ images), cloud burst is **highly profitable** if you value dev time.

#### Scenario D: LoRA Training (1 session)

**Local (5070 Ti):**
- Training time: **3 hours** (batch size 8, 3000 steps)
- Electricity: 0.285 kW × 3h × €0.20 = **€0.17**

**Cloud (H100):**
- Training time: **20 minutes** (batch size 64, faster GPU)
- Setup: 5 min (upload training images)
- Total time: **25 min** (0.42h)
- Cloud cost: 0.42h × €3.36 = **€1.41**

**Analysis:**
- Time saved: 3h - 0.42h = **2.58 hours**
- Cost premium: €1.41 - €0.17 = **€1.24**
- **ROI:** If dev time = €50/h → saved value = €129 → **Positive ROI (+€127.76)**

**Key insight:** LoRA training is a **killer use case** for cloud burst (9x speedup, minimal cost).

### 3.4. Break-Even Analysis

**Question:** At what batch size does cloud burst become cost-effective?

**Assumptions:**
- Developer time value: €50/h
- Cloud cost: €3.36/h
- Local time: 14s/image (5070 Ti + ComfyUI)
- Cloud time: 6s/image + 7 min overhead (setup + download)

**Formula:**
```
Local time: T_local = N × 14s
Cloud time: T_cloud = 7 min + N × 6s
Cloud cost: C_cloud = (T_cloud / 3600) × €3.36

Time saved value: V_saved = (T_local - T_cloud) × (€50/h)
Net ROI: V_saved - C_cloud
```

**Break-even (ROI = 0):**
```python
# Solve for N where ROI = 0
# V_saved = C_cloud
# (N × 14s - (420s + N × 6s)) / 3600 × €50 = ((420s + N × 6s) / 3600) × €3.36
# (N × 8s - 420s) × €50 = (420s + N × 6s) × €3.36
# Solving: N ≈ 53 images
```

**Break-even point:** **~50-60 images**

**Recommendation:**
- **Use cloud for:** Batches ≥ 100 images, LoRA training, A/B testing
- **Use local for:** Small batches < 50 images, quick tests, exploration

### 3.5. Cost Optimization Strategies

**1. Model Caching (Persistent Storage)**
- Keep models on instance between runs (avoid re-upload)
- Savings: 5 min upload time per batch → €0.28 saved

**2. Warm Instance (Pre-started VM)**
- Keep instance running but idle (minimal compute cost)
- Trade-off: €0.50/h idle cost vs 2 min startup savings
- **Only worth it if:** Generating batches every <30 min

**3. Batch Packing (Maximize GPU Utilization)**
- Pack 500-1000 images per batch (amortize setup cost)
- Savings: Setup overhead 7 min / 1000 images = 0.42s/image vs 7 min / 100 images = 4.2s/image

**4. Spot Instances (Future)**
- OVH/AWS spot instances: 60-80% discount
- Risk: Instance can be terminated (need checkpoint/resume logic)
- Potential savings: €3.36/h → **€0.67-€1.34/h**

**5. Multi-Cloud Arbitrage**
- Compare OVH, RunPod, Vast.ai, Lambda Labs
- Example: RunPod H100 = $2.29/h (~€2.15/h) vs OVH €2.80/h
- Potential savings: **€0.65/h (23%)**

### 3.6. Cost Matrix Summary

| Use Case | Batch Size | Local Time | Cloud Time | Cloud Cost | ROI (€50/h dev) |
|----------|------------|------------|------------|------------|-----------------|
| Quick test | 10 | 2.3 min | 8 min | €0.45 | ❌ Negative |
| Small batch | 50 | 11.7 min | 10 min | €0.56 | ⚖️ Break-even |
| Medium batch | 100 | 23 min | 13 min | €0.74 | ✅ +€7.61 |
| Large batch | 500 | 1.94h | 57 min | €3.19 | ✅ +€45.92 |
| Massive batch | 5000 | 19.4h | 9.5h | €31.92 | ✅ +€462.08 |
| LoRA training | 1 session | 3h | 25 min | €1.41 | ✅ +€127.76 |

**Key Takeaway:** Cloud burst is **economically justified** for:
- ✅ Batches ≥ 100 images
- ✅ LoRA training
- ✅ Any workflow where time-to-market > cost savings

---

## 4. Code Adaptation (sdgen CLI)

### 4.1. New Module: `cloud_client.py`

**Location:** `packages/sd-generator-cli/sd_generator_cli/api/cloud_client.py`

**Responsibility:**
- Provision cloud instances (OVH API)
- Upload job manifest + models
- Execute remote generation (SSH)
- Poll for completion
- Download results
- Teardown instances

**Interface:**
```python
# sd_generator_cli/api/cloud_client.py

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

@dataclass
class CloudConfig:
    """Configuration for cloud compute"""
    provider: str = "ovh"  # ovh, runpod, lambdalabs
    instance_type: str = "h100"
    ssh_key_path: str = "~/.ssh/sdgen_cloud_burst"
    ssh_user: str = "ubuntu"
    region: str = "eu-west-1"

    # Model caching
    keep_models_cached: bool = True  # Persistent storage

    # Instance lifecycle
    auto_teardown: bool = True  # Stop instance after job
    warm_instance: bool = False  # Keep instance running


class CloudComputeClient:
    """
    Client for cloud GPU burst (H100 instances)

    Handles provisioning, job submission, and result retrieval.
    """

    def __init__(self, config: CloudConfig):
        self.config = config
        self.instance_ip: Optional[str] = None
        self.instance_id: Optional[str] = None

    def provision_instance(self, timeout: int = 300) -> str:
        """
        Provision cloud GPU instance via provider API

        Returns:
            str: Instance IP address

        Raises:
            RuntimeError: If provisioning fails
        """
        print("[Cloud] Provisioning H100 instance...")

        # Call provider API (OVH, RunPod, etc.)
        # Example: OVH API call
        # instance = ovh_api.create_instance(
        #     flavor="h100-80gb",
        #     image="ubuntu-22.04-cuda-12.1",
        #     ssh_key=self.config.ssh_key_path
        # )

        # Simulate provisioning (replace with real API call)
        # self.instance_id = instance["id"]
        # self.instance_ip = instance["ip"]

        # Wait for SSH ready
        print("[Cloud] Waiting for SSH ready...")
        self._wait_for_ssh(timeout)

        print(f"[Cloud] ✓ Instance ready: {self.instance_ip}")
        return self.instance_ip

    def upload_job(self, job_manifest: dict, lora_paths: List[Path]) -> None:
        """
        Upload job manifest + LoRA files to cloud instance

        Args:
            job_manifest: Job configuration (prompts, config)
            lora_paths: List of local LoRA file paths to upload
        """
        print("[Cloud] Uploading job manifest...")

        # Write manifest to temp file
        manifest_path = Path("/tmp/job_manifest.json")
        with open(manifest_path, 'w') as f:
            json.dump(job_manifest, f, indent=2)

        # Upload manifest via rsync
        self._rsync_upload(manifest_path, "/data/job_manifest.json")

        # Upload LoRAs (if not cached)
        if lora_paths and not self._loras_cached(lora_paths):
            print(f"[Cloud] Uploading {len(lora_paths)} LoRA file(s)...")
            for lora_path in lora_paths:
                remote_path = f"/opt/ComfyUI/models/loras/{lora_path.name}"
                self._rsync_upload(lora_path, remote_path)
        else:
            print("[Cloud] LoRAs already cached, skipping upload")

    def execute_generation(self, timeout: int = 3600) -> dict:
        """
        Execute remote generation job

        Args:
            timeout: Max execution time in seconds

        Returns:
            dict: Job status {"status": "complete", "images": 500, ...}
        """
        print("[Cloud] Starting remote generation...")

        # Execute generate.py script on remote
        cmd = (
            f"ssh -i {self.config.ssh_key_path} "
            f"{self.config.ssh_user}@{self.instance_ip} "
            f"'cd /opt/ComfyUI && source /opt/sdgen-env/bin/activate && "
            f"python3 generate.py --job /data/job_manifest.json'"
        )

        # Run in background
        subprocess.Popen(cmd, shell=True)

        # Poll for completion
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self._get_job_status()

            if status["status"] == "complete":
                print(f"[Cloud] ✓ Generation complete: {status['images']} images")
                return status

            print(f"[Cloud] Progress: {status['progress']} ({status['status']})")
            time.sleep(30)  # Poll every 30s

        raise RuntimeError(f"Job timed out after {timeout}s")

    def download_results(self, local_output_dir: Path) -> None:
        """
        Download generated images from cloud to local directory

        Args:
            local_output_dir: Local directory to save images
        """
        print("[Cloud] Downloading results...")

        remote_dir = "/tmp/output/"
        self._rsync_download(remote_dir, local_output_dir)

        print(f"[Cloud] ✓ Results downloaded to {local_output_dir}")

    def teardown_instance(self) -> None:
        """
        Stop or delete cloud instance (cleanup)
        """
        if not self.config.auto_teardown:
            print("[Cloud] Skipping teardown (auto_teardown=False)")
            return

        print("[Cloud] Tearing down instance...")

        # Cleanup remote temp files
        self._ssh_exec("rm -rf /tmp/output/*")

        # Stop instance (via provider API)
        # ovh_api.stop_instance(self.instance_id)

        print("[Cloud] ✓ Instance stopped")

    # ========== Private Methods ==========

    def _wait_for_ssh(self, timeout: int) -> None:
        """Wait for SSH to become available"""
        start = time.time()
        while time.time() - start < timeout:
            try:
                result = subprocess.run(
                    f"ssh -i {self.config.ssh_key_path} "
                    f"-o ConnectTimeout=5 "
                    f"{self.config.ssh_user}@{self.instance_ip} 'echo ready'",
                    shell=True,
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return
            except Exception:
                pass
            time.sleep(5)

        raise RuntimeError(f"SSH not ready after {timeout}s")

    def _rsync_upload(self, local_path: Path, remote_path: str) -> None:
        """Upload file via rsync"""
        cmd = [
            "rsync", "-avz",
            "-e", f"ssh -i {self.config.ssh_key_path}",
            str(local_path),
            f"{self.config.ssh_user}@{self.instance_ip}:{remote_path}"
        ]
        subprocess.run(cmd, check=True)

    def _rsync_download(self, remote_path: str, local_path: Path) -> None:
        """Download directory via rsync"""
        cmd = [
            "rsync", "-avz",
            "-e", f"ssh -i {self.config.ssh_key_path}",
            f"{self.config.ssh_user}@{self.instance_ip}:{remote_path}",
            str(local_path)
        ]
        subprocess.run(cmd, check=True)

    def _ssh_exec(self, command: str) -> str:
        """Execute command on remote via SSH"""
        result = subprocess.run(
            f"ssh -i {self.config.ssh_key_path} "
            f"{self.config.ssh_user}@{self.instance_ip} '{command}'",
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout

    def _get_job_status(self) -> dict:
        """Get job status from remote"""
        try:
            output = self._ssh_exec("cat /data/job_status.json")
            return json.loads(output)
        except Exception:
            return {"status": "unknown", "progress": "N/A"}

    def _loras_cached(self, lora_paths: List[Path]) -> bool:
        """Check if LoRAs are already on remote instance"""
        if not self.config.keep_models_cached:
            return False

        # Check if LoRA files exist on remote
        for lora in lora_paths:
            remote_path = f"/opt/ComfyUI/models/loras/{lora.name}"
            result = self._ssh_exec(f"test -f {remote_path} && echo 'exists' || echo 'missing'")
            if "missing" in result:
                return False

        return True
```

### 4.2. CLI Integration

**New flag: `--cloud`**

**File:** `packages/sd-generator-cli/sd_generator_cli/commands.py`

```python
# In generate_command()

@app.command()
def generate(
    template_path: Optional[str] = typer.Option(None, "-t", "--template"),
    max_images: Optional[int] = typer.Option(None, "-n", "--max-images"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    cloud: bool = typer.Option(False, "--cloud", help="Use cloud GPU burst (H100)"),
    cloud_provider: str = typer.Option("ovh", "--cloud-provider", help="Cloud provider (ovh, runpod, etc.)"),
):
    """Generate images from template"""

    # ... existing template loading code ...

    # Resolve prompts (same as before)
    prompt_configs = orchestrator.generate_prompts(template_config, max_images)

    if cloud:
        # Cloud burst workflow
        _generate_cloud(prompt_configs, template_config, cloud_provider)
    else:
        # Local workflow (existing)
        _generate_local(prompt_configs, template_config, dry_run)


def _generate_cloud(prompt_configs, template_config, provider):
    """Generate images using cloud GPU burst"""
    from sd_generator_cli.api.cloud_client import CloudComputeClient, CloudConfig

    print(f"[Cloud Burst] Using {provider} H100 instance")

    # Load cloud config
    cloud_config = CloudConfig(provider=provider)
    client = CloudComputeClient(cloud_config)

    # 1. Provision instance
    instance_ip = client.provision_instance()

    # 2. Build job manifest
    job_manifest = {
        "version": "1.0",
        "job_id": f"job_{int(time.time())}",
        "config": {
            "checkpoint": template_config.parameters.get("checkpoint", "default.safetensors"),
            # ... generation params ...
        },
        "prompts": [
            {
                "id": f"{i:03d}",
                "prompt": p.prompt,
                "negative_prompt": p.negative_prompt,
                "seed": p.seed,
                "filename": f"{i:03d}.png",
                "variations": p.parameters.get("variations", {})
            }
            for i, p in enumerate(prompt_configs, 1)
        ]
    }

    # 3. Upload job + LoRAs
    lora_paths = _extract_lora_paths(template_config)
    client.upload_job(job_manifest, lora_paths)

    # 4. Execute generation
    result = client.execute_generation(timeout=7200)  # 2 hours max

    # 5. Download results
    session_folder = create_session_folder(template_config)
    client.download_results(session_folder)

    # 6. Generate manifest.json (locally)
    generate_manifest(session_folder, prompt_configs, template_config)

    # 7. Teardown
    client.teardown_instance()

    print(f"✓ Cloud generation complete: {result['images']} images")
```

### 4.3. Configuration (sdgen_config.json)

**Add cloud provider section:**

```json
{
  "configs_dir": "./prompts",
  "output_dir": "./results",
  "api_url": "http://172.29.128.1:7860",
  "cloud_providers": {
    "ovh": {
      "api_key": "your_ovh_api_key",
      "api_secret": "your_ovh_api_secret",
      "ssh_key_path": "~/.ssh/sdgen_cloud_burst",
      "ssh_user": "ubuntu",
      "region": "eu-west-1",
      "instance_type": "h100-80gb",
      "auto_teardown": true,
      "keep_models_cached": true
    },
    "runpod": {
      "api_key": "your_runpod_api_key",
      "instance_type": "h100",
      "auto_teardown": true
    }
  }
}
```

### 4.4. Remote Generation Script (Cloud Instance)

**File:** `/opt/ComfyUI/generate.py` (on cloud instance)

```python
#!/usr/bin/env python3
"""
Remote generation script for cloud GPU instances.
Reads job manifest, executes ComfyUI workflow, saves images.
"""

import json
import argparse
from pathlib import Path
import sys

# Add ComfyUI to path
sys.path.insert(0, "/opt/ComfyUI")

from comfy_api import ComfyUIClient, Workflow


def load_job(job_path: str) -> dict:
    """Load job manifest"""
    with open(job_path, 'r') as f:
        return json.load(f)


def build_workflow(config: dict, prompt: dict) -> Workflow:
    """Build ComfyUI workflow from config"""
    wf = Workflow()

    # Load checkpoint
    model = wf.add_node("CheckpointLoaderSimple",
                         ckpt_name=config["checkpoint"])

    # Load LoRAs
    current_model = model["model"]
    for lora in config.get("loras", []):
        lora_node = wf.add_node("LoraLoader",
                                 model=current_model,
                                 lora_name=lora["name"],
                                 strength_model=lora["strength"],
                                 strength_clip=lora["strength"])
        current_model = lora_node["model"]

    # CLIP encode
    positive = wf.add_node("CLIPTextEncode",
                            text=prompt["prompt"],
                            clip=model["clip"])
    negative = wf.add_node("CLIPTextEncode",
                            text=prompt["negative_prompt"],
                            clip=model["clip"])

    # Latent
    gen_config = config["generation"]
    latent = wf.add_node("EmptyLatentImage",
                          width=gen_config["width"],
                          height=gen_config["height"],
                          batch_size=gen_config.get("batch_size", 1))

    # KSampler
    samples = wf.add_node("KSampler",
                           model=current_model,
                           seed=prompt["seed"] or -1,
                           steps=gen_config["steps"],
                           cfg=gen_config["cfg_scale"],
                           sampler_name=gen_config["sampler"],
                           scheduler=gen_config.get("scheduler", "normal"),
                           positive=positive["conditioning"],
                           negative=negative["conditioning"],
                           latent_image=latent["latent"])

    # VAE Decode
    image = wf.add_node("VAEDecode",
                         samples=samples["latent"],
                         vae=model["vae"])

    # Upscaler (if enabled)
    if config.get("upscaler", {}).get("enabled"):
        upscale_cfg = config["upscaler"]
        upscale_model = wf.add_node("UpscaleModelLoader",
                                     model_name=upscale_cfg["model"])
        image = wf.add_node("ImageUpscaleWithModel",
                             upscale_model=upscale_model["upscale_model"],
                             image=image["image"])

    # Save image
    wf.add_node("SaveImage",
                 images=image["image"],
                 filename_prefix=prompt["filename"].replace(".png", ""))

    return wf


def update_status(status_path: str, status: str, progress: str):
    """Update job status file"""
    with open(status_path, 'w') as f:
        json.dump({"status": status, "progress": progress}, f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True, help="Path to job manifest JSON")
    args = parser.parse_args()

    # Load job
    job = load_job(args.job)
    status_path = "/data/job_status.json"

    # Initialize ComfyUI client
    client = ComfyUIClient("http://127.0.0.1:8188")

    # Update status
    update_status(status_path, "running", "0/{len(job['prompts'])}")

    # Process prompts
    output_dir = Path("/tmp/output")
    output_dir.mkdir(exist_ok=True)

    for i, prompt in enumerate(job["prompts"], 1):
        print(f"[{i}/{len(job['prompts'])}] Generating {prompt['filename']}...")

        # Build workflow
        workflow = build_workflow(job["config"], prompt)

        # Execute
        images = client.queue_and_wait(workflow, timeout=300)

        # Save image
        output_path = output_dir / prompt["filename"]
        with open(output_path, 'wb') as f:
            f.write(images[0])

        # Update status
        update_status(status_path, "running", f"{i}/{len(job['prompts'])}")

    # Final status
    update_status(status_path, "complete", f"{len(job['prompts'])}/{len(job['prompts'])}")
    print(f"✓ Generation complete: {len(job['prompts'])} images")


if __name__ == "__main__":
    main()
```

---

## 5. Provisioning & Automation

### 5.1. Provisioning Strategies Comparison

| Strategy | Setup Time | Cost/h | Pros | Cons | Recommended For |
|----------|------------|--------|------|------|-----------------|
| **A. On-Demand** | 15 min | €3.36 | No idle cost, fresh env | Slow cold start | Occasional batches |
| **B. Warm Instance** | 2 min | €3.36 (active)<br>€0.50 (idle) | Fast start | Idle cost adds up | Frequent batches (multiple/day) |
| **C. Custom Image** | 3 min | €3.36 + €0.50/mo storage | Fast start, reproducible | Image maintenance | Production workflows |

### 5.2. Strategy A: On-Demand (No Persistent Instance)

**Workflow:**
1. User runs `sdgen generate --cloud -n 500`
2. CLI provisions fresh H100 instance via OVH API
3. Full setup script runs (15 min)
4. Generation executes (50 min)
5. Results downloaded
6. Instance deleted

**Cost example (500 images):**
- Setup: 15 min × €3.36/h = €0.84
- Generation: 50 min × €3.36/h = €2.80
- Download: 5 min × €3.36/h = €0.28
- **Total:** €3.92

**Pros:**
- ✅ No idle costs
- ✅ Always clean environment
- ✅ No state management

**Cons:**
- ❌ 15 min setup overhead (expensive)
- ❌ Not practical for frequent batches

**Recommendation:** Only for **very occasional** cloud bursts (once/week).

### 5.3. Strategy B: Warm Instance (Pre-Started VM)

**Workflow:**
1. Instance provisioned once, left running
2. User runs `sdgen generate --cloud -n 500`
3. CLI connects to existing instance (30s)
4. Generation executes immediately (50 min)
5. Instance stays running after job

**Cost example (500 images):**
- Generation: 50 min × €3.36/h = €2.80
- Download: 5 min × €3.36/h = €0.28
- **Per-job:** €3.08
- **Idle cost (if running 24/7):** €3.36/h × 24h = **€80.64/day**

**Optimization:** Auto-shutdown after 1h idle
- If generating 5 batches/day (5h active, 19h idle @ €0.50/h)
- Daily cost: 5h × €3.36 + 19h × €0.50 = **€26.30/day**

**Pros:**
- ✅ Instant start (30s vs 15 min)
- ✅ Models stay cached

**Cons:**
- ❌ Idle cost (€0.50-€3.36/h depending on state)
- ❌ Need auto-shutdown logic

**Recommendation:** For **frequent batches** (3+ per day).

### 5.4. Strategy C: Custom Image (Reusable Snapshot)

**Workflow:**
1. Provision instance once, run full setup (15 min)
2. Create custom image/snapshot
3. Delete instance
4. For future jobs: Provision from custom image (3 min startup)
5. Auto-delete after job

**Cost example (500 images):**
- Image storage: €0.50/month (~€0.02/day)
- Setup (from image): 3 min × €3.36/h = €0.17
- Generation: 50 min × €3.36/h = €2.80
- Download: 5 min × €3.36/h = €0.28
- **Total:** €3.25 + €0.02/day storage

**Pros:**
- ✅ Fast startup (3 min vs 15 min)
- ✅ Reproducible environment
- ✅ No idle compute costs
- ✅ Pay-per-use with minimal overhead

**Cons:**
- ❌ Image maintenance (updates, security patches)
- ❌ Small storage cost (negligible)

**Recommendation:** **Best strategy for production** (balance speed + cost).

### 5.5. Automated Provisioning (OVH API)

**OVH API Integration:**

```python
# cloud_providers/ovh_provider.py

import ovh
from dataclasses import dataclass
from typing import Optional


@dataclass
class OVHConfig:
    """OVH API configuration"""
    endpoint: str = "ovh-eu"  # Europe endpoint
    application_key: str = ""
    application_secret: str = ""
    consumer_key: str = ""

    # Instance config
    project_id: str = ""
    region: str = "GRA11"  # Gravelines datacenter
    flavor_name: str = "h100-80gb"
    image_id: str = "ubuntu-22-04-cuda-12-1"  # Custom image ID
    ssh_key_name: str = "sdgen-cloud-burst"


class OVHProvider:
    """OVH cloud provider integration"""

    def __init__(self, config: OVHConfig):
        self.config = config
        self.client = ovh.Client(
            endpoint=config.endpoint,
            application_key=config.application_key,
            application_secret=config.application_secret,
            consumer_key=config.consumer_key
        )

    def create_instance(self, instance_name: str) -> dict:
        """
        Create H100 instance

        Returns:
            dict: {"id": "...", "ip": "..."}
        """
        # Upload SSH key (if not already uploaded)
        self._ensure_ssh_key()

        # Create instance
        result = self.client.post(
            f"/cloud/project/{self.config.project_id}/instance",
            flavorId=self._get_flavor_id(),
            imageId=self.config.image_id,
            name=instance_name,
            region=self.config.region,
            sshKeyId=self._get_ssh_key_id()
        )

        instance_id = result["id"]

        # Wait for instance to be active
        self._wait_for_active(instance_id)

        # Get public IP
        instance = self._get_instance(instance_id)
        public_ip = instance["ipAddresses"][0]["ip"]

        return {
            "id": instance_id,
            "ip": public_ip,
            "status": "active"
        }

    def delete_instance(self, instance_id: str) -> None:
        """Delete instance"""
        self.client.delete(
            f"/cloud/project/{self.config.project_id}/instance/{instance_id}"
        )

    def stop_instance(self, instance_id: str) -> None:
        """Stop instance (keep disk, reduce billing)"""
        self.client.post(
            f"/cloud/project/{self.config.project_id}/instance/{instance_id}/stop"
        )

    def start_instance(self, instance_id: str) -> None:
        """Start stopped instance"""
        self.client.post(
            f"/cloud/project/{self.config.project_id}/instance/{instance_id}/start"
        )

    def create_snapshot(self, instance_id: str, snapshot_name: str) -> str:
        """Create image snapshot from instance"""
        result = self.client.post(
            f"/cloud/project/{self.config.project_id}/instance/{instance_id}/snapshot",
            snapshotName=snapshot_name
        )
        return result["id"]

    # ========== Private Methods ==========

    def _get_flavor_id(self) -> str:
        """Get flavor ID for H100 instance"""
        flavors = self.client.get(
            f"/cloud/project/{self.config.project_id}/flavor",
            region=self.config.region
        )
        for flavor in flavors:
            if self.config.flavor_name in flavor["name"]:
                return flavor["id"]
        raise ValueError(f"Flavor {self.config.flavor_name} not found")

    def _ensure_ssh_key(self) -> None:
        """Upload SSH key if not exists"""
        keys = self.client.get(
            f"/cloud/project/{self.config.project_id}/sshkey"
        )
        for key in keys:
            if key["name"] == self.config.ssh_key_name:
                return

        # Upload key
        with open(Path(self.config.ssh_key_path).expanduser().with_suffix(".pub"), 'r') as f:
            public_key = f.read()

        self.client.post(
            f"/cloud/project/{self.config.project_id}/sshkey",
            name=self.config.ssh_key_name,
            publicKey=public_key
        )

    def _get_ssh_key_id(self) -> str:
        """Get SSH key ID"""
        keys = self.client.get(
            f"/cloud/project/{self.config.project_id}/sshkey"
        )
        for key in keys:
            if key["name"] == self.config.ssh_key_name:
                return key["id"]
        raise ValueError(f"SSH key {self.config.ssh_key_name} not found")

    def _wait_for_active(self, instance_id: str, timeout: int = 300) -> None:
        """Wait for instance to become active"""
        import time
        start = time.time()
        while time.time() - start < timeout:
            instance = self._get_instance(instance_id)
            if instance["status"] == "ACTIVE":
                return
            time.sleep(5)
        raise TimeoutError(f"Instance not active after {timeout}s")

    def _get_instance(self, instance_id: str) -> dict:
        """Get instance details"""
        return self.client.get(
            f"/cloud/project/{self.config.project_id}/instance/{instance_id}"
        )
```

**Usage:**
```python
from cloud_providers.ovh_provider import OVHProvider, OVHConfig

config = OVHConfig(
    application_key="...",
    application_secret="...",
    consumer_key="...",
    project_id="..."
)

provider = OVHProvider(config)

# Create instance
instance = provider.create_instance("sdgen-h100-001")
print(f"Instance ready: {instance['ip']}")

# ... run generation ...

# Delete instance
provider.delete_instance(instance['id'])
```

### 5.6. Monitoring & Cost Alerting

**Cost Monitoring Script:**

```python
# tools/cloud_cost_monitor.py

import ovh
from datetime import datetime, timedelta


class CloudCostMonitor:
    """Monitor cloud spending and alert on thresholds"""

    def __init__(self, ovh_client: ovh.Client, project_id: str):
        self.client = ovh_client
        self.project_id = project_id

    def get_daily_cost(self, date: datetime) -> float:
        """Get total cost for a specific day"""
        # Get consumption data
        consumption = self.client.get(
            f"/cloud/project/{self.project_id}/consumption",
            from_=date.isoformat(),
            to=(date + timedelta(days=1)).isoformat()
        )

        total = sum(item["totalPrice"] for item in consumption["hourlyUsage"])
        return total

    def check_budget_alert(self, daily_budget: float = 50.0) -> Optional[str]:
        """Check if today's spending exceeds budget"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cost = self.get_daily_cost(today)

        if cost > daily_budget:
            return (
                f"⚠️ BUDGET ALERT: Today's spending €{cost:.2f} "
                f"exceeds daily budget €{daily_budget:.2f}"
            )
        return None

    def list_running_instances(self) -> list:
        """List all running instances"""
        instances = self.client.get(
            f"/cloud/project/{self.project_id}/instance"
        )
        return [i for i in instances if i["status"] == "ACTIVE"]

    def auto_shutdown_idle_instances(self, idle_threshold_hours: int = 1) -> None:
        """Auto-shutdown instances idle for > threshold"""
        instances = self.list_running_instances()
        now = datetime.now()

        for instance in instances:
            # Check last activity (would need custom tracking)
            # If idle > threshold → shutdown
            pass  # Implement based on activity tracking
```

**Usage (cron job):**
```bash
# Crontab: Check budget every hour
0 * * * * python3 tools/cloud_cost_monitor.py --check-budget --alert-email=user@example.com
```

---

## 6. Risk Analysis

### 6.1. Risk Matrix

| Risk | Probability | Impact | Severity | Mitigation |
|------|-------------|--------|----------|------------|
| **Cloud API changes (OVH)** | Low | High | 🟠 Medium | Pin API version, monitor changelog, abstract provider interface |
| **Network latency/failures** | Medium | Medium | 🟡 Low-Med | Retry logic, checkpointing, resume from failure |
| **Cost overrun (forgotten instance)** | High | High | 🔴 **High** | Auto-shutdown after 1h idle, budget alerts, kill switch |
| **Data privacy (GDPR)** | Low | High | 🟠 Medium | Encrypt uploads, auto-delete after download, audit logs |
| **SSH key compromise** | Low | Critical | 🔴 **High** | Key rotation, IP whitelist, 2FA on cloud account |
| **Model corruption (upload)** | Low | Medium | 🟡 Low | Checksum validation, retry on failure |
| **Job failure (OOM, timeout)** | Medium | Medium | 🟡 Low | Memory profiling, progressive batch sizes, timeout handling |
| **Vendor lock-in (OVH-only)** | Medium | Medium | 🟡 Low | Multi-cloud support (RunPod, Lambda Labs), provider abstraction |
| **Cold start too slow (15 min)** | High | Low | 🟡 Low | Use custom image (3 min startup) |

**Legend:**
- 🔴 **Critical** (P1): Immediate mitigation required
- 🟠 **High** (P2): Address before production
- 🟡 **Medium** (P3): Monitor and mitigate incrementally
- 🟢 **Low** (P4): Acceptable risk

### 6.2. Critical Risk: Cost Overrun

**Scenario:** User provisions instance, job fails silently, instance runs for 24h.
- Cost: 24h × €3.36 = **€80.64** wasted

**Mitigation:**

**1. Auto-Shutdown Timer**
```python
# In CloudComputeClient
def _set_auto_shutdown_timer(self, max_idle_hours: int = 1):
    """Set timer to auto-shutdown instance after idle period"""
    # Run cron job on instance:
    # If no activity for 1h → shutdown
    cmd = f"""
    echo '0 * * * * /opt/scripts/check_idle.sh' | crontab -
    """
    self._ssh_exec(cmd)
```

**2. Budget Alerts**
```python
# Daily cost check
monitor = CloudCostMonitor(ovh_client, project_id)
alert = monitor.check_budget_alert(daily_budget=50.0)
if alert:
    send_email(alert)  # Notify user
```

**3. Kill Switch (Manual)**
```bash
# Emergency shutdown all instances
sdgen cloud kill-all --confirm
```

### 6.3. Security Best Practices

**SSH Key Security:**
```bash
# Generate dedicated key pair
ssh-keygen -t ed25519 -f ~/.ssh/sdgen_cloud_burst -C "sdgen-cloud-burst"

# Restrict permissions
chmod 600 ~/.ssh/sdgen_cloud_burst
chmod 644 ~/.ssh/sdgen_cloud_burst.pub

# Use SSH agent (no password prompts)
eval $(ssh-agent)
ssh-add ~/.ssh/sdgen_cloud_burst
```

**Firewall Rules (Cloud Instance):**
```bash
# Only allow SSH from known IPs
sudo ufw enable
sudo ufw allow from YOUR_HOME_IP to any port 22
sudo ufw deny 22  # Deny all other IPs
```

**API Key Storage:**
```bash
# Never commit API keys to git
# Store in environment variables or encrypted vault
export OVH_APP_KEY="..."
export OVH_APP_SECRET="..."

# Or use password manager (1Password, Bitwarden)
```

### 6.4. Data Privacy (GDPR Compliance)

**If generating images with personal data (faces, names):**

1. **Encrypt uploads** (optional, SSH already encrypts)
```bash
# Encrypt manifest before upload
gpg --encrypt --recipient user@example.com job_manifest.json
rsync job_manifest.json.gpg user@h100:/data/
```

2. **Auto-delete after download**
```python
# In download_results()
def download_results(self, local_output_dir: Path) -> None:
    self._rsync_download("/tmp/output/", local_output_dir)

    # Delete remote files immediately
    self._ssh_exec("rm -rf /tmp/output/*")
```

3. **Audit trail**
```python
# Log all cloud operations
log.info(f"[AUDIT] Uploaded job {job_id} to {instance_ip} at {timestamp}")
log.info(f"[AUDIT] Downloaded {num_images} images from {instance_ip}")
log.info(f"[AUDIT] Deleted remote files on {instance_ip}")
```

---

## 7. Recommendation & Roadmap

### 7.1. Decision Matrix

**Should we implement Cloud GPU Burst?**

| Criterion | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| **Performance gain** (2.3x speedup) | 9/10 | 25% | 2.25 |
| **Cost efficiency** (ROI > 100 images) | 7/10 | 20% | 1.40 |
| **Strategic value** (self-improving loop foundation) | 10/10 | 20% | 2.00 |
| **Implementation complexity** | 6/10 | 15% | 0.90 |
| **Operational overhead** | 5/10 | 10% | 0.50 |
| **Scalability** (10x future growth) | 9/10 | 10% | 0.90 |
| **TOTAL** | **7.95 / 10** | 100% | **7.95** |

**Verdict:** ✅ **PROCEED** (score > 7.0)

### 7.2. Use Case Prioritization

| Use Case | Priority | ROI | Effort | Recommendation |
|----------|----------|-----|--------|----------------|
| **LoRA Training** | P1 | 9x speedup, €1.24 cost | Low | ✅ **MUST HAVE** |
| **Batch >500 images** | P1 | 2.3x speedup, positive ROI | Medium | ✅ **MUST HAVE** |
| **Batch 100-500 images** | P2 | 2.3x speedup, marginal ROI | Medium | ✅ **SHOULD HAVE** |
| **Batch <100 images** | P3 | Negative ROI | Low | ❌ **AVOID** |
| **CLIP Validation** (38k images) | P1 | Enables self-improving loop | High | ✅ **STRATEGIC** |

**Recommended:** Focus on **LoRA training** and **large batches (500+)** first.

### 7.3. Implementation Roadmap

#### Phase 1: POC (2 weeks) - Manual Workflow

**Goal:** Validate cloud burst concept with manual SSH/rsync workflow

**Tasks:**
- [ ] Provision OVH H100 instance manually
- [ ] Run setup script (setup_h100_instance.sh)
- [ ] Upload checkpoint + LoRAs manually via rsync
- [ ] Create test job manifest (10 images)
- [ ] Execute generate.py remotely
- [ ] Download results manually
- [ ] Measure end-to-end time & cost
- [ ] Document learnings

**Success Criteria:**
- ✅ Generate 10 images on H100 via manual workflow
- ✅ Performance: <1 min per image (vs 14s local)
- ✅ Cost: <€1 total

**Deliverables:**
- POC report (timing, cost, issues encountered)
- Refined estimate for automation effort

**Effort:** 5-10 days

---

#### Phase 2: MVP (4 weeks) - Automated CLI Integration

**Goal:** `sdgen generate --cloud` works end-to-end

**Tasks:**
- [ ] Implement `CloudComputeClient` (cloud_client.py)
- [ ] Integrate OVH API (ovh_provider.py)
- [ ] Add `--cloud` flag to CLI (commands.py)
- [ ] Implement job manifest generation
- [ ] Implement auto-provisioning (OVH API)
- [ ] Implement SSH/rsync upload/download
- [ ] Add progress reporting (poll job status)
- [ ] Add auto-teardown after job
- [ ] Create custom image (reduce setup time to 3 min)
- [ ] Integration tests (end-to-end)
- [ ] Documentation (user guide, config reference)

**Success Criteria:**
- ✅ `sdgen generate --cloud -n 500` works end-to-end
- ✅ Setup time <3 min (custom image)
- ✅ Total time <1h (vs 1.94h local)
- ✅ Cost <€5 (vs electricity + dev time value)

**Deliverables:**
- Functional `--cloud` flag in CLI
- OVH provider integration
- Custom H100 image (snapshot)
- User documentation

**Effort:** 15-20 days

---

#### Phase 3: Production (6 weeks) - Multi-Cloud + Optimization

**Goal:** Production-ready with cost optimization and multi-cloud support

**Tasks:**
- [ ] Add RunPod provider (runpod_provider.py)
- [ ] Add Lambda Labs provider (lambda_provider.py)
- [ ] Implement provider abstraction (CloudProvider interface)
- [ ] Add cost comparison (auto-select cheapest provider)
- [ ] Implement model caching (persistent storage)
- [ ] Implement warm instance mode (pre-started VM)
- [ ] Add budget alerts (email notifications)
- [ ] Add auto-shutdown timer (1h idle)
- [ ] Implement retry logic (network failures)
- [ ] Add spot instances support (60% cost savings)
- [ ] Performance benchmarking (OVH vs RunPod vs Lambda)
- [ ] Security audit (SSH keys, API keys, data privacy)
- [ ] Production documentation

**Success Criteria:**
- ✅ Multi-cloud support (3+ providers)
- ✅ Auto-select cheapest provider
- ✅ Cost <50% of Phase 2 (spot instances)
- ✅ Security audit passed
- ✅ Cost monitoring dashboard

**Deliverables:**
- Multi-cloud support (OVH, RunPod, Lambda Labs)
- Cost optimization features
- Production-grade security
- Monitoring & alerting

**Effort:** 25-30 days

---

#### Phase 4: Advanced Features (Future)

**Goal:** Seamless cloud-native workflows

**Tasks:**
- [ ] Integrate with Direct Pipeline (ComfyUI local + cloud)
- [ ] CLIP validation on cloud (38k images in 1 day)
- [ ] Distributed training (multi-GPU LoRA training)
- [ ] A/B testing framework (compare LoRA versions)
- [ ] Self-improving loop (Generate → CLIP → Train → Loop)

**Effort:** 8+ weeks

---

### 7.4. Total Effort Summary

| Phase | Duration | Deliverable | Cumulative |
|-------|----------|-------------|------------|
| **Phase 1 (POC)** | 2 weeks | Manual workflow validated | 2 weeks |
| **Phase 2 (MVP)** | 4 weeks | `--cloud` flag working | 6 weeks |
| **Phase 3 (Production)** | 6 weeks | Multi-cloud + optimization | **12 weeks** |
| **Phase 4 (Advanced)** | 8+ weeks | Self-improving loop | 20+ weeks |

**Recommended MVP:** **Phase 1-2 (6 weeks)** to validate ROI before investing in Phase 3.

---

## 8. Next Steps (Immediate Actions)

### Week 1-2: POC Execution

**Day 1-2: Setup**
- [ ] Create OVH account + project
- [ ] Generate SSH key pair (sdgen_cloud_burst)
- [ ] Provision H100 instance manually (console)
- [ ] SSH into instance, verify GPU (nvidia-smi)

**Day 3-4: Environment Setup**
- [ ] Run setup_h100_instance.sh script
- [ ] Download checkpoint (realisticVision_v60.safetensors)
- [ ] Upload checkpoint + LoRA to instance
- [ ] Verify ComfyUI starts (python main.py)

**Day 5-7: Test Generation**
- [ ] Create test job manifest (10 prompts)
- [ ] Write generate.py script (ComfyUI workflow)
- [ ] Execute remotely via SSH
- [ ] Download results via rsync
- [ ] Measure time & cost

**Day 8-10: Analysis & Report**
- [ ] Compare performance (H100 vs 5070 Ti)
- [ ] Calculate exact costs
- [ ] Document issues/blockers
- [ ] Write POC report
- [ ] Decision: Proceed to Phase 2?

### Week 3-6: MVP Implementation

**Week 3:**
- [ ] Implement CloudComputeClient skeleton
- [ ] Integrate OVH API (provision, delete)
- [ ] Test provisioning automation

**Week 4:**
- [ ] Add CLI `--cloud` flag
- [ ] Implement job manifest generation
- [ ] Implement upload/download logic

**Week 5:**
- [ ] Add progress reporting
- [ ] Add auto-teardown
- [ ] Create custom image (snapshot)

**Week 6:**
- [ ] Integration testing
- [ ] Documentation
- [ ] User acceptance testing

### Success Metrics (6 weeks)

**Performance:**
- ✅ 500 images in <1h (vs 1.94h local)
- ✅ LoRA training in <30 min (vs 3h local)

**Cost:**
- ✅ 500 images <€5
- ✅ LoRA training <€2

**Usability:**
- ✅ `sdgen generate --cloud` one-liner
- ✅ No manual intervention required
- ✅ Auto-cleanup (no forgotten instances)

---

## 9. Appendix

### A. OVH API Authentication Setup

**Step 1: Create OVH Application**
1. Go to https://eu.api.ovh.com/createApp/
2. Create application → Get `application_key` and `application_secret`

**Step 2: Generate Consumer Key**
```python
import ovh

client = ovh.Client(
    endpoint='ovh-eu',
    application_key='YOUR_APP_KEY',
    application_secret='YOUR_APP_SECRET'
)

# Request full access
ck = client.new_consumer_key_request()
ck.add_recursive_rules(ovh.API_READ_WRITE, "/cloud")

validation = ck.request()
print(f"Visit: {validation['validationUrl']}")
print(f"Consumer key: {validation['consumerKey']}")
```

**Step 3: Validate Consumer Key**
- Open validation URL in browser
- Login to OVH account
- Approve access
- Copy `consumer_key`

**Step 4: Save to Config**
```json
{
  "cloud_providers": {
    "ovh": {
      "application_key": "YOUR_APP_KEY",
      "application_secret": "YOUR_APP_SECRET",
      "consumer_key": "YOUR_CONSUMER_KEY",
      "project_id": "YOUR_PROJECT_ID"
    }
  }
}
```

### B. Alternative Cloud Providers

#### RunPod (Lower Cost Alternative)

**Pricing:**
- H100 80GB: **$2.29/h** (~€2.15/h) vs OVH €2.80/h
- Savings: **€0.65/h (23%)**

**API:**
```python
import runpod

runpod.api_key = "YOUR_RUNPOD_API_KEY"

# Create instance
gpu = runpod.create_pod(
    name="sdgen-h100",
    image_name="runpod/pytorch:2.0.1-py3.10-cuda11.8.0-devel",
    gpu_type_id="NVIDIA H100 80GB HBM3",
    cloud_type="SECURE",
    volume_in_gb=50
)

# Get connection info
print(f"SSH: {gpu['machine']['podHostId']}")
```

#### Lambda Labs (Simplified API)

**Pricing:**
- H100 80GB: **$2.49/h** (~€2.34/h)

**API:**
```python
import requests

response = requests.post(
    "https://cloud.lambdalabs.com/api/v1/instance-operations/launch",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "region_name": "us-west-1",
        "instance_type_name": "gpu_1x_h100_pcie",
        "ssh_key_names": ["sdgen-key"]
    }
)
```

### C. Cost Comparison (500 Images)

| Provider | Instance | Price/h | Time | Cost | Savings |
|----------|----------|---------|------|------|---------|
| **OVH** | H100 80GB | €3.36 | 57 min | €3.19 | Baseline |
| **RunPod** | H100 80GB | €2.15 | 57 min | €2.04 | **-€1.15 (36%)** |
| **Lambda Labs** | H100 PCIe | €2.34 | 57 min | €2.22 | **-€0.97 (30%)** |
| **Vast.ai** | H100 spot | €1.20 | 57 min | €1.14 | **-€2.05 (64%)** |

**Recommendation:** Start with **OVH** (EU-based, GDPR compliant), migrate to **RunPod** or **Vast.ai** in Phase 3 for cost savings.

### D. Performance Benchmarks (External Sources)

**H100 vs A100 vs RTX 4090:**
- H100: 1.5s/image SDXL (TensorRT)
- A100: 2.5s/image SDXL
- RTX 4090: 4s/image SDXL
- RTX 5070 Ti: ~5s/image SDXL (estimated)

**Batch Processing Gains:**
- Batch 1: 2s/image
- Batch 4: 1.8s/image (10% faster)
- Batch 16: 1.5s/image (25% faster)
- Batch 32: 1.3s/image (35% faster)

**Source:** https://www.pugetsystems.com/labs/articles/stable-diffusion-benchmarks/

---

## Document Metadata

**Revision:** 1.0
**Last Updated:** 2025-10-31
**Next Review:** After Phase 1 POC completion
**Related Specs:**
- Direct Pipeline: `docs/roadmap/future/direct_pipeline.md`
- Self-Improving Loop: Future spec (TBD)

**Approval Status:** DRAFT (pending stakeholder review)

---

**END OF SPECIFICATION**
