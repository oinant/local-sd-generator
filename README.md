# SD Generator CLI

<div align="center">

**Production-ready CLI and Web UI for Stable Diffusion with advanced YAML templating system**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Code style: flake8](https://img.shields.io/badge/code%20style-flake8-black)](https://flake8.pycqa.org/)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue)](http://mypy-lang.org/)

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 🎯 Why SD Generator CLI?

**Born from frustration with the Stable Diffusion cargo cult.**

When you start with Stable Diffusion, you inevitably copy-paste "magic prompts" from Reddit, Discord, or CivitAI. You tweak seeds randomly. You manually generate hundreds of images, changing one parameter at a time. You lose track of what settings produced which results. You can't reproduce your best outputs.

**This is cargo cult prompt engineering—and it doesn't scale.**

This CLI was built to escape that chaos. It transforms SD workflows into **systematic, reproducible, version-controlled processes**:
- **Template inheritance** instead of copy-pasting prompts
- **Combinatorial testing** instead of manual parameter tweaking
- **Manifests and metadata** instead of lost settings
- **Reusable chunks** instead of monolithic prompts
- **Random sampling** for exploring large variation spaces efficiently

Perfect for:
- **LoRA training datasets** - Generate comprehensive character/style variations systematically
- **Prompt research** - Test hypotheses with controlled experiments, not guesswork
- **Batch generation** - Hundreds of images with traceable parameters
- **Production workflows** - Reproducible pipelines you can commit to git

## ✨ Features

### 🔧 Template System V2.0
- **Inheritance** - Multi-level template inheritance with `implements:`
- **Modular imports** - Reusable prompt chunks with `imports:`
- **Advanced selectors** - `[random:N]`, `[limit:N]`, `[indexes:1,5,8]`, `[keys:foo,bar]`, `[#start-end]`
- **Weight-based loops** - Control iteration order with `weight:` for optimal combinations
- **Type-safe** - Full mypy strict type checking for reliability

### 🎲 Generation Modes
- **Combinatorial** - Generate all possible combinations (exhaustive testing)
- **Random** - Smart sampling for large variation spaces
- **Seed control** - Fixed, progressive, or random seeds per image

### 🖼️ Production Features
- **Real-time annotations** - Automatic metadata injection with thread-safe queue
- **Session management** - Organized output with manifests and metadata
- **Dry-run mode** - Preview API payloads without generating
- **API introspection** - List available models, samplers, schedulers, upscalers
- **Error recovery** - Robust error handling and validation

### 🌐 Modern Web UI (Beta)
- **Vue.js frontend** - Clean, responsive interface
- **FastAPI backend** - High-performance API with async support
- **GUID-based auth** - Simple token authentication
- **Dev mode** - Hot reload for rapid development

## 📦 Quick Start

### Prerequisites
- Python 3.10+
- [Stable Diffusion WebUI (Automatic1111)](https://github.com/AUTOMATIC1111/stable-diffusion-webui) running with `--api` flag

### Installation

```bash
# Clone the repository
git clone https://github.com/oinant/local-sd-generator.git
cd local-sd-generator

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install CLI package (development mode)
cd packages/sd-generator-cli
pip install -e .
```

### First generation

```bash
# Initialize configuration (creates sdgen_config.json in current directory)
sdgen init

# Edit config to point to your SD WebUI
# Default: http://127.0.0.1:7860

# Generate from a template
sdgen generate -t path/to/your/template.yaml

# Or use interactive mode to select from available templates
sdgen generate
```

### Example template

Create `my-first-template.prompt.yaml`:

```yaml
name: "Character Variations"
version: 2
description: "Generate character with different expressions and poses"

generation:
  mode: "random"
  max_images: 50

seed:
  mode: "progressive"
  value: 42

variations:
  expression:
    - happy
    - sad
    - surprised
    - angry

  pose:
    - standing
    - sitting
    - walking

payload:
  model: "your-model-name.safetensors"
  steps: 30
  cfg_scale: 7.5
  width: 512
  height: 768

  prompt:
    template: |
      masterpiece, best quality,
      1girl, {expression} expression, {pose},
      detailed face, beautiful lighting

  negative_prompt: "low quality, blurry, distorted"
```

Generate:
```bash
sdgen generate -t my-first-template.prompt.yaml -n 20
```

This creates 20 random combinations of expressions × poses with progressive seeds (42, 43, 44...).

## 🏗️ Architecture

```
local-sd-generator/
├── packages/
│   ├── sd-generator-cli/           # 🎯 CLI Package
│   │   ├── sd_generator_cli/
│   │   │   ├── api/               # SD WebUI client
│   │   │   ├── templating/        # Template System V2.0
│   │   │   │   ├── loaders/       # YAML parsing
│   │   │   │   ├── resolvers/     # Inheritance & imports
│   │   │   │   ├── generators/    # Prompt generation
│   │   │   │   └── validators/    # Validation
│   │   │   ├── execution/         # Manifest & executor
│   │   │   └── cli.py             # CLI entry point (Typer)
│   │   └── tests/                 # Pytest suite
│   │
│   └── sd-generator-webui/        # 🌐 Web UI Package (Beta)
│       ├── backend/               # FastAPI backend
│       │   └── sd_generator_webui/
│       └── front/                 # Vue.js frontend
│
├── docs/                          # 📚 Documentation
│   ├── cli/                       # CLI guides & reference
│   ├── webapp/                    # WebUI documentation
│   └── roadmap/                   # Feature planning
│
└── tools/                         # 🛠️ Build & quality tools
```

**Design Philosophy:**
- **Monorepo** - CLI and WebUI as separate packages sharing a venv
- **Type-safe** - Mypy strict mode throughout
- **Tested** - Comprehensive pytest suite with >80% coverage
- **Documented** - Single source of truth in `/docs`

## 📖 Documentation

### Getting Started
- [Installation & Setup](docs/cli/usage/getting-started.md)
- [Template Basics](docs/cli/technical/template-system-spec.md)
- [Variation Files](docs/cli/usage/variation-files.md)
- [Examples](docs/cli/usage/examples.md)

### Advanced
- [Template System V2.0 Architecture](docs/cli/technical/yaml-templating-system.md)
- [Inheritance & Imports](docs/cli/technical/template-system-spec.md#inheritance)
- [Advanced Selectors](docs/cli/technical/template-system-spec.md#selectors)
- [ADetailer Integration](docs/cli/usage/adetailer.md)
- [Image Annotations](docs/cli/usage/annotations.md)

### API Reference
- [CLI Commands](docs/cli/reference/)
- [Configuration System](docs/cli/technical/config-system.md)
- [Manifest Format](docs/cli/technical/manifest_v2_format.md)

### Development
- [Architecture](docs/cli/technical/architecture.md)
- [Code Review Guidelines](docs/tooling/CODE_REVIEW_GUIDELINES.md)
- [Type Checking Guide](docs/tooling/type-checking-guide.md)
- [Build Tool Usage](docs/tooling/build-tool-usage.md)

## 🚀 Web UI (Beta)

The Web UI provides a modern interface for managing generations and browsing results.

### Quick Start

```bash
# Install WebUI package
cd packages/sd-generator-webui
pip install -e .

# Install frontend dependencies (dev mode only)
cd front && npm install

# Start in production mode (backend serves frontend)
sdgen webui start

# Or start in dev mode (hot reload)
sdgen webui start --dev-mode
```

Visit `http://localhost:8000/webui` (production) or `http://localhost:5173` (dev).

### Authentication

Generate a GUID for authentication:
```bash
# Linux/Mac
uuidgen

# Or use: https://www.uuidgenerator.net/
```

Set environment variables:
```bash
export VALID_GUIDS='["your-admin-guid-here"]'
export IMAGE_FOLDERS='[{"path": "/path/to/images", "name": "My Images"}]'
```

Or create a `.env` file in your working directory (see `.env.example`).

## 🔧 Development

### Setup

```bash
# Clone and setup venv
git clone https://github.com/oinant/local-sd-generator.git
cd local-sd-generator
python3 -m venv venv
source venv/bin/activate

# Install Poetry
pip install poetry

# Install CLI in dev mode
cd packages/sd-generator-cli
poetry install
pip install -e .

# Install WebUI in dev mode (optional)
cd ../sd-generator-webui
SKIP_FRONTEND_BUILD=1 pip install -e .
cd front && npm install
```

### Running Tests

```bash
# From CLI package directory
cd packages/sd-generator-cli

# All tests
python3 -m pytest tests/ -v

# With coverage
python3 -m pytest tests/ --cov=sd_generator_cli --cov-report=term-missing
```

### Quality Checks

Use the build tool for comprehensive checks:

```bash
# From project root
python3 tools/build.py

# Or individual checks
python3 -m flake8 packages/sd-generator-cli/sd_generator_cli --max-line-length=120
python3 -m mypy packages/sd-generator-cli/sd_generator_cli --show-error-codes
python3 -m radon cc packages/sd-generator-cli/sd_generator_cli -a
```

## 🤝 Contributing

Contributions are welcome! This project follows a structured development workflow.

### Getting Started

1. **Check the roadmap** - See [`docs/roadmap/`](docs/roadmap/) for planned features
   - `wip/` - Currently in progress
   - `next/` - Up next (priority 1-6)
   - `future/` - Backlog (priority 7-10)

2. **Pick a task or propose a feature** - Open an issue to discuss

3. **Development workflow**
   ```bash
   # Fork and clone
   git clone https://github.com/YOUR_USERNAME/local-sd-generator.git
   cd local-sd-generator

   # Create feature branch
   git checkout -b feature/your-feature-name

   # Make changes, add tests
   # ...

   # Run quality checks
   python3 tools/build.py

   # Commit and push
   git commit -m "feat: add your feature"
   git push origin feature/your-feature-name

   # Open Pull Request
   ```

4. **Code standards**
   - Follow PEP 8 (enforced by flake8)
   - Add type hints (mypy strict mode)
   - Write tests for new features (pytest)
   - Keep complexity low (radon CC <10)
   - Document in `/docs` if adding features

5. **PR Guidelines**
   - Clear description of changes
   - Link to related issues
   - All tests passing
   - Quality checks passing (`tools/build.py`)
   - Update documentation if needed

### Areas for Contribution

- **Templates** - Share interesting template patterns
- **Documentation** - Tutorials, examples, guides
- **Features** - Check `docs/roadmap/next/` for priorities
- **Bug fixes** - Check open issues
- **Tests** - Improve coverage
- **WebUI** - Vue.js frontend improvements

See [CODE_REVIEW_GUIDELINES.md](docs/tooling/CODE_REVIEW_GUIDELINES.md) for detailed standards.

## 📋 Roadmap

### ✅ Completed (v2.0)
- Template System V2.0 with inheritance & imports
- Advanced selectors with weight-based loops
- Real-time image annotations
- Combinatorial & random generation modes
- Comprehensive test suite
- WebUI beta

### 🚧 In Progress
- Check [`docs/roadmap/wip/`](docs/roadmap/wip/)

### 🎯 Upcoming
- PyPI package publication
- Extended API introspection
- Batch template validation
- Enhanced error reporting
- Template marketplace

Full roadmap: [`docs/roadmap/`](docs/roadmap/)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Stable Diffusion WebUI (Automatic1111)](https://github.com/AUTOMATIC1111/stable-diffusion-webui) - The foundation
- [Poetry](https://python-poetry.org/) - Python packaging
- [Typer](https://typer.tiangolo.com/) - Beautiful CLIs
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Vue.js](https://vuejs.org/) - Progressive JavaScript framework

---

<div align="center">

**Made with ❤️ for the Stable Diffusion community**

[⭐ Star this repo](https://github.com/oinant/local-sd-generator) if you find it useful!

</div>
