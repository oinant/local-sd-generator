# WebUI Installation Guide

This guide covers installation for both end users and developers.

## Prerequisites

- **Python 3.10+** (required)
- **Stable Diffusion WebUI** (Automatic1111) running locally
- **Node.js 16+** (for development only)
- **Poetry** (for development only)

## For End Users

### Method 1: Install from PyPI (Coming Soon)

Once published to PyPI:

```bash
pip install sd-generator-webui
```

This will automatically install:
- `sd-generator-cli` (dependency)
- FastAPI backend
- Built frontend (embedded in package)
- All Python dependencies

### Method 2: Install from Source

**1. Clone the repository:**

```bash
git clone https://github.com/oinant/local-sd-generator.git
cd local-sd-generator
```

**2. Build the packages:**

```bash
# Install Poetry if needed
pip install poetry

# Build CLI package
cd packages/sd-generator-cli
poetry build

# Build WebUI package (includes frontend)
cd ../sd-generator-webui
poetry build
```

**3. Install the wheels:**

```bash
# From the packages directory
pip install sd-generator-cli/dist/sd_generator_cli-*.whl
pip install sd-generator-webui/dist/sd_generator_webui-*.whl
```

### Configuration

**Required environment variables:**

Create a `.env` file in your working directory or export variables:

```bash
# Image folders (JSON array with path and name)
export IMAGE_FOLDERS='[{"path": "/path/to/your/images", "name": "My Gallery"}]'

# Authentication tokens (GUIDs)
export VALID_GUIDS='["your-admin-guid-here"]'
export READ_ONLY_GUIDS='["optional-readonly-guid"]'

# Optional settings
export API_HOST=0.0.0.0
export API_PORT=8000
export SD_WEBUI_URL=http://127.0.0.1:7860
```

**Generate authentication GUIDs:**

```bash
# Linux/Mac
uuidgen

# Or use online generator
# https://www.uuidgenerator.net/
```

**Example `.env` file:**

```env
# Image storage
IMAGE_FOLDERS=[{"path": "/home/user/sd-images", "name": "Generated Images"}]

# Authentication
VALID_GUIDS=["a1b2c3d4-e5f6-7890-abcd-ef1234567890"]
READ_ONLY_GUIDS=[]

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
SD_WEBUI_URL=http://127.0.0.1:7860
```

### Running the WebUI

**Start the server:**

```bash
# With environment variables
IMAGE_FOLDERS='[{"path": "/tmp/images", "name": "Gallery"}]' \
VALID_GUIDS='["your-guid"]' \
READ_ONLY_GUIDS='[]' \
python3 -m uvicorn sd_generator_webui.main:app --host 0.0.0.0 --port 8000
```

**Or with .env file:**

```bash
# If .env is in current directory
python3 -m uvicorn sd_generator_webui.main:app --host 0.0.0.0 --port 8000
```

**Access the interface:**

Open your browser and navigate to:
- **Frontend:** http://localhost:8000/webui
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Root:** http://localhost:8000 (redirects to /webui)

### Authentication

Use your configured GUID as a Bearer token:

**In the browser:**

The first time you access the UI, you'll be prompted for your auth token. Enter the GUID you configured in `VALID_GUIDS`.

**Via API:**

```bash
curl -H "Authorization: Bearer your-guid-here" http://localhost:8000/api/images
```

## For Developers

### Setup Development Environment

**1. Clone and create venv:**

```bash
git clone https://github.com/oinant/local-sd-generator.git
cd local-sd-generator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows
```

**2. Install CLI package:**

```bash
cd packages/sd-generator-cli
pip install -e .
```

**3. Install WebUI package (dev mode):**

```bash
cd ../sd-generator-webui

# Skip frontend build (we'll use Vite dev server)
SKIP_FRONTEND_BUILD=1 pip install -e .
```

**4. Install frontend dependencies:**

```bash
cd front
npm install
```

### Development Workflow

#### Option 1: Full Dev Mode (Recommended)

Use the `--dev-mode` flag to run backend and frontend separately with hot reload.

```bash
# Start both services in dev mode
sdgen webui start --dev-mode
```

This launches:
- Backend API on port 8000 (with auto-reload)
- Frontend Vite dev server on port 5173 (with HMR)

**Access:** http://localhost:5173 (Vite dev server)

Benefits:
- ⚡ Hot module replacement (instant updates)
- 🐛 Vue DevTools support
- 📦 Source maps for debugging
- 🔄 Auto-reload on file changes

**Manual start (if needed):**

If you prefer to start services manually:

```bash
# Terminal 1 - Backend (API only)
cd packages/sd-generator-webui
export SD_GENERATOR_DEV_MODE=1
export IMAGE_FOLDERS='[{"path": "/tmp/test-images", "name": "Test"}]'
export VALID_GUIDS='["dev-guid"]'
export READ_ONLY_GUIDS='[]'
python3 -m uvicorn sd_generator_webui.main:app --reload --port 8000

# Terminal 2 - Frontend (Vite dev server)
cd packages/sd-generator-webui/front
npm run dev
```

#### Option 2: Production Mode Locally

Test the production build without creating wheels.

**1. Build frontend:**

```bash
cd packages/sd-generator-webui/front
npm run build
```

**2. Start backend (production mode):**

```bash
cd ..
# Don't set SD_GENERATOR_DEV_MODE

IMAGE_FOLDERS='[{"path": "/tmp/images", "name": "Test"}]' \
VALID_GUIDS='["test-guid"]' \
READ_ONLY_GUIDS='[]' \
python3 -m uvicorn sd_generator_webui.main:app --host 0.0.0.0 --port 8000
```

**Access:** http://localhost:8000/webui

### Building and Testing

**Build frontend for production:**

```bash
cd front
npm run build

# Output: backend/static/dist/
# Contains: index.html, js/, css/, fonts/
```

**Build Python wheel:**

```bash
cd ..  # Back to sd-generator-webui/
poetry build

# Output: dist/sd_generator_webui-0.1.0-*.whl
# Size: ~3.2 MB (includes frontend)
```

**Test wheel installation:**

```bash
# Create isolated environment
python3 -m venv /tmp/test-sdgen
source /tmp/test-sdgen/bin/activate

# Install wheel
pip install dist/sd_generator_webui-*.whl

# Test
IMAGE_FOLDERS='[{"path": "/tmp/images", "name": "Test"}]' \
VALID_GUIDS='["test"]' \
READ_ONLY_GUIDS='[]' \
python3 -m uvicorn sd_generator_webui.main:app --host 0.0.0.0 --port 8000

# Should serve frontend at http://localhost:8000/webui
```

### Troubleshooting

#### Frontend not found in production

**Symptom:** Backend shows "No frontend build - Backend API only"

**Check:**
1. Frontend was built: `ls -la backend/static/dist/index.html`
2. Wheel includes frontend: `unzip -l dist/*.whl | grep index.html`

**Fix:**
```bash
cd front
npm run build
cd ..
poetry build
```

#### CORS errors in dev mode

**Symptom:** API calls fail with CORS errors

**Solution:** Ensure `SD_GENERATOR_DEV_MODE=1` is set when starting backend

#### Environment variables not loaded

**Symptom:** `TypeError: the JSON object must be str, bytes or bytearray`

**Solution:** Check that all required env vars are set:
```bash
echo $IMAGE_FOLDERS
echo $VALID_GUIDS
echo $READ_ONLY_GUIDS
```

If missing, create a `.env` file or export them.

## Next Steps

- [Usage Guide](./usage-guide.md) - How to use the web interface
- [Development Guide](./development.md) - Advanced development topics
- [API Reference](../technical/api.md) - REST API documentation
