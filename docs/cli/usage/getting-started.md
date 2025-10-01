# Getting Started with Local SD Generator CLI

**Quick start guide to generate your first image variations.**

---

## Prerequisites

- **Python 3.8+** (use `python3` on WSL/Linux)
- **Stable Diffusion WebUI** running locally
- API access enabled (in WebUI settings)

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd local-sd-generator
```

### 2. Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 3. Verify Stable Diffusion API

Ensure Stable Diffusion WebUI is running and accessible at `http://127.0.0.1:7860`

---

## Your First Generation

### Step 1: Create a variation file

Create `variations/expressions.txt`:

```
smiling
sad
angry
surprised
neutral
```

### Step 2: Create a simple generator script

Create `my_first_generator.py`:

```python
from CLI.image_variation_generator import ImageVariationGenerator

generator = ImageVariationGenerator(
    prompt_template="masterpiece, {Expression}, beautiful portrait, high quality",
    negative_prompt="low quality, blurry, bad anatomy",
    variation_files={
        "Expression": "variations/expressions.txt"
    },
    seed=42,
    generation_mode="combinatorial",
    seed_mode="progressive"
)

generator.run()
```

### Step 3: Run it

```bash
python3 my_first_generator.py
```

**Result:** 5 images generated (one per expression) in `apioutput/YYYYMMDD_HHMMSS_Expression/`

---

## Understanding the Output

### Folder structure

```
apioutput/
└── 20251001_143052_Expression/
    ├── 001.png
    ├── 002.png
    ├── 003.png
    ├── 004.png
    ├── 005.png
    ├── metadata.json
    └── session_config.txt (deprecated)
```

### Output files

- **Images**: Numbered sequentially (`001.png`, `002.png`, ...)
- **metadata.json**: Complete generation information (NEW in Phase 1)
- **session_config.txt**: Legacy text format (deprecated)

---

## Next Steps

### Add more variations

```python
variation_files={
    "Expression": "variations/expressions.txt",
    "Angle": "variations/angles.txt"
}
```

This generates **all combinations** (e.g., 5 expressions × 4 angles = 20 images)

### Control file naming

```python
generator = ImageVariationGenerator(
    # ... same config ...
    filename_keys=["Expression", "Angle"]
)
```

**Result:** Files named like `001_Expression-Smiling_Angle-Front.png`

### Explore generation modes

- **`combinatorial`**: Generate all possible combinations
- **`random`**: Generate random unique combinations

```python
generation_mode="random",
max_images=50  # Generate 50 random combinations
```

### Explore seed modes

- **`progressive`**: Seeds increment (42, 43, 44, ...)
- **`fixed`**: Same seed for all images
- **`random`**: Random seed (-1) for each image

---

## Learn More

- **[JSON Config System](json-config-system.md)** - Use JSON instead of Python scripts
- **[Variation Files](variation-files.md)** - Advanced placeholder syntax
- **[Examples](examples.md)** - Common use cases

---

## Troubleshooting

### "Connection refused" error

Ensure Stable Diffusion WebUI is running:
```bash
cd stable-diffusion-webui
./webui.sh --api
```

### "File not found" error

Use absolute paths or paths relative to your script location:
```python
variation_files={
    "Expression": "/absolute/path/to/expressions.txt"
}
```

### "Out of memory" error

Reduce batch size or image dimensions:
```python
parameters={
    "width": 512,
    "height": 512,
    "batch_size": 1
}
```

---

**Last updated:** 2025-10-01
