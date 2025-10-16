# local-sd-generator

Advanced CLI and Web UI tools for Stable Diffusion image generation with template-based prompt variations.

## Features

- 🎨 **Template System V2.0** - Advanced YAML templates with inheritance, imports, and chunking
- 🌐 **Web Interface** - Modern Vue.js UI with FastAPI backend
- 🔄 **Prompt Variations** - Combinatorial or random generation modes
- 📦 **Monorepo Structure** - Organized packages with Poetry
- 🚀 **Production Ready** - Single pip install, batteries included

## Quick Start

### Installation (End Users)

**Prerequisites:**
- Python 3.10+
- Stable Diffusion WebUI (Automatic1111) running locally

**Install from pip** (coming soon after PyPI publish):
```bash
pip install sd-generator-cli sd-generator-webui
```

**Install from source:**
```bash
# Clone the repository
git clone https://github.com/oinant/local-sd-generator.git
cd local-sd-generator

# Build and install wheels
cd packages/sd-generator-cli
poetry build
pip install dist/*.whl

cd ../sd-generator-webui
poetry build
pip install dist/*.whl
```

### Configuration

**Generate GUIDs for authentication:**
```bash
# Linux/Mac
uuidgen

# Or use online: https://www.uuidgenerator.net/
```

**Set environment variables:**
```bash
export IMAGE_FOLDERS='[{"path": "/path/to/your/images", "name": "My Images"}]'
export VALID_GUIDS='["your-admin-guid-here"]'
export READ_ONLY_GUIDS='[]'
```

Or create a `.env` file in your working directory:
```env
IMAGE_FOLDERS=[{"path": "/path/to/your/images", "name": "My Images"}]
VALID_GUIDS=["your-admin-guid-here"]
READ_ONLY_GUIDS=[]
API_HOST=0.0.0.0
API_PORT=8000
```

### Usage

**CLI Generation:**
```bash
# Initialize config
sdgen init

# Generate images from template
sdgen generate -t path/to/template.yaml

# List available templates
sdgen list

# API introspection
sdgen api samplers
sdgen api models
```

**Web Interface:**
```bash
# Production mode (backend serves frontend)
sdgen webui start

# Dev mode (separate Vite server)
sdgen webui start --dev-mode

# Open browser
# Production: http://localhost:8000/webui
# Dev: http://localhost:5173
```

## Development Setup

### Prerequisites

- Python 3.10+
- Node.js 16+ (for frontend)
- Poetry (Python package manager)

### Clone and Setup

```bash
# Clone repository
git clone https://github.com/oinant/local-sd-generator.git
cd local-sd-generator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install poetry
```

### Install Packages (Development Mode)

**CLI Package:**
```bash
cd packages/sd-generator-cli
poetry install
pip install -e .
```

**WebUI Package:**
```bash
cd packages/sd-generator-webui

# Install Python package (skip frontend build for dev)
SKIP_FRONTEND_BUILD=1 pip install -e .

# Install frontend dependencies
cd front
npm install
```

### Development Workflow

**Start in Dev Mode:**
```bash
# Starts both backend and frontend in dev mode
sdgen webui start --dev-mode

# This launches:
# - Backend API on port 8000 (with auto-reload)
# - Frontend Vite dev server on port 5173 (with HMR)
# - Access at http://localhost:5173
```

**Manual start (if needed):**
```bash
# Terminal 1 - Backend
cd packages/sd-generator-webui
SD_GENERATOR_DEV_MODE=1 python3 -m uvicorn sd_generator_webui.main:app --reload --port 8000

# Terminal 2 - Frontend
cd packages/sd-generator-webui/front
npm run dev
```

Benefits:
- Hot module replacement for instant updates
- Backend auto-reload on code changes
- Vue DevTools support
- Source maps for debugging

### Build for Production

**Build frontend:**
```bash
cd packages/sd-generator-webui/front
npm run build
# Output: backend/static/dist/
```

**Build Python wheels:**
```bash
# CLI
cd packages/sd-generator-cli
poetry build

# WebUI (includes frontend)
cd packages/sd-generator-webui
poetry build
```

**Test production build:**
```bash
# Create test environment
python3 -m venv test-env
source test-env/bin/activate

# Install from wheels
pip install packages/sd-generator-cli/dist/*.whl
pip install packages/sd-generator-webui/dist/*.whl

# Run production server
python3 -m uvicorn sd_generator_webui.main:app --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# Activate venv
source venv/bin/activate

# CLI tests
cd packages/sd-generator-cli/CLI
python3 -m pytest tests/ --ignore=tests/legacy -v

# With coverage
python3 -m pytest tests/v2/ --cov=templating --cov-report=term-missing -v
```

## Project Structure

```
local-sd-generator/
├── packages/
│   ├── sd-generator-cli/          # CLI package
│   │   ├── CLI/
│   │   │   ├── src/              # Source code
│   │   │   │   ├── templating/  # Template system V2
│   │   │   │   ├── api/         # SD WebUI API client
│   │   │   │   └── cli.py       # CLI entry point
│   │   │   └── tests/           # Test suite
│   │   └── pyproject.toml
│   │
│   └── sd-generator-webui/        # Web UI package
│       ├── backend/
│       │   └── sd_generator_webui/
│       │       ├── main.py       # FastAPI app
│       │       ├── api/          # API routes
│       │       └── config.py     # Configuration
│       ├── front/                # Vue.js frontend
│       │   ├── src/
│       │   └── vue.config.js
│       ├── build.py              # Frontend build script
│       └── pyproject.toml
│
├── docs/                          # Documentation
├── venv/                          # Development venv
└── README.md
```

## Authentication

The WebUI uses GUID-based token authentication:

```bash
# In requests
curl -H "Authorization: Bearer your-guid-here" http://localhost:8000/api/images

# In browser (localStorage)
localStorage.setItem('authToken', 'your-guid-here')
```

## Documentation

See `docs/` directory for detailed documentation:
- **CLI Usage:** `docs/cli/usage/`
- **Template System:** `docs/cli/technical/template-system-v2.md`
- **API Reference:** `docs/api/`
- **Development:** `docs/tooling/`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and quality checks
5. Submit a pull request

**Code Quality:**
```bash
# Style checking
python3 -m flake8 CLI/ --max-line-length=120

# Complexity analysis
python3 -m radon cc CLI/ -a

# Security scanning
python3 -m bandit -r CLI/ -ll
```

## License

See LICENSE file in repository root.
