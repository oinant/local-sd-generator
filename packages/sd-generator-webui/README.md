# SD Generator WebUI

Web interface for Stable Diffusion image generation with FastAPI backend and Vue.js frontend.

## Features

- 🌐 **Modern Web Interface**
  - Vue.js + Vuetify UI
  - Real-time generation progress
  - Image gallery with filtering
  - Job queue management

- 🔒 **Authentication**
  - Token-based authentication
  - Secure session management

- 📊 **Job Management**
  - Background job processing
  - Real-time status updates
  - Job history tracking

- 🖼️ **Gallery**
  - Session-based organization
  - Thumbnail generation
  - Metadata display
  - PNG info extraction

## Installation

### End Users (Production)

**From pip** (coming soon):
```bash
pip install sd-generator-webui
```

**From source:**
```bash
# Clone and build
git clone https://github.com/oinant/local-sd-generator.git
cd local-sd-generator/packages/sd-generator-webui

# Build (includes frontend)
poetry build

# Install wheel
pip install dist/sd_generator_webui-*.whl
```

### Developers

**Quick setup:**
```bash
# Install without building frontend (for dev mode)
SKIP_FRONTEND_BUILD=1 pip install -e .

# Install frontend dependencies
cd front
npm install
```

## Configuration

**Required environment variables:**

Create a `.env` file or export variables:

```bash
# Image folders (JSON array)
export IMAGE_FOLDERS='[{"path": "/path/to/images", "name": "Gallery"}]'

# Authentication GUIDs (JSON arrays)
export VALID_GUIDS='["your-admin-guid"]'
export READ_ONLY_GUIDS='[]'

# Optional
export API_HOST=0.0.0.0
export API_PORT=8000
export SD_WEBUI_URL=http://127.0.0.1:7860
```

**Generate GUIDs:**
```bash
# Linux/Mac
uuidgen

# Or use: https://www.uuidgenerator.net/
```

## Usage

### Production Mode

Start the backend server (serves built frontend):

```bash
# With environment variables
IMAGE_FOLDERS='[{"path": "/tmp/images", "name": "Gallery"}]' \
VALID_GUIDS='["your-guid"]' \
READ_ONLY_GUIDS='[]' \
python3 -m uvicorn sd_generator_webui.main:app --host 0.0.0.0 --port 8000
```

Access at: **http://localhost:8000/webui**

The backend serves:
- Frontend app at `/webui`
- API endpoints at `/api/*`
- API docs at `/docs`
- Root `/` redirects to `/webui`

### Development Mode

Use the `--dev-mode` flag to start backend (API only) and frontend (Vite) separately:

```bash
# Start with dev mode flag
sdgen webui start --dev-mode
```

This will launch:
- Backend API on port 8000
- Frontend Vite dev server on port 5173

Access frontend at: **http://localhost:5173**

Benefits:
- Hot module replacement for instant updates
- Vue DevTools support
- Source maps for debugging
- Fast refresh on code changes

**Manual start (if needed):**

If you need to start services manually:

```bash
# Terminal 1 - Backend
cd packages/sd-generator-webui
SD_GENERATOR_DEV_MODE=1 python3 -m uvicorn sd_generator_webui.main:app --reload --port 8000

# Terminal 2 - Frontend
cd packages/sd-generator-webui/front
npm run dev
```

## API Documentation

Once backend is running, access interactive API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

The WebUI uses the same config as CLI (`sdgen_config.json`):

```json
{
  "configs_dir": "./prompts",
  "output_dir": "./results",
  "api_url": "http://127.0.0.1:7860"
}
```

Additional WebUI-specific config will be added in Phase 2.

## Architecture

```
sd-generator-webui/
├── backend/                  # FastAPI backend
│   └── sd_generator_webui/
│       ├── main.py          # FastAPI app
│       ├── api/             # API routes
│       ├── services/        # Business logic
│       └── jobs/            # Background jobs
│
└── front/                    # Vue.js frontend
    ├── src/
    │   ├── components/      # Vue components
    │   ├── views/           # Page views
    │   ├── router/          # Vue Router
    │   ├── store/           # Vuex store
    │   └── services/        # API client
    └── public/
```

## Development

### Setup Development Environment

```bash
# 1. Clone repository
git clone https://github.com/oinant/local-sd-generator.git
cd local-sd-generator

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install CLI (dependency)
cd packages/sd-generator-cli
pip install -e .

# 4. Install WebUI (skip frontend build for dev)
cd ../sd-generator-webui
SKIP_FRONTEND_BUILD=1 pip install -e .

# 5. Install frontend dependencies
cd front
npm install
```

### Development Workflow

**Recommended: Use `sdgen webui start --dev-mode`**

```bash
# Starts both backend and frontend in dev mode
sdgen webui start --dev-mode

# Access at http://localhost:5173
```

**Manual start (if needed):**

If you need to start services manually:

```bash
# Terminal 1 - Backend (API only)
cd packages/sd-generator-webui
export SD_GENERATOR_DEV_MODE=1
export IMAGE_FOLDERS='[{"path": "/tmp/test-images", "name": "Test"}]'
export VALID_GUIDS='["test-guid"]'
export READ_ONLY_GUIDS='[]'
python3 -m uvicorn sd_generator_webui.main:app --reload --port 8000

# Terminal 2 - Frontend (Vite dev server)
cd packages/sd-generator-webui/front
npm run dev
```

Then open http://localhost:5173

### Building for Production

**1. Build frontend:**
```bash
cd front
npm run build

# Output: backend/static/dist/
# This directory will be packaged in the Python wheel
```

**2. Build Python wheel:**
```bash
cd ..  # Back to sd-generator-webui/
poetry build

# Output: dist/sd_generator_webui-*.whl (includes frontend)
```

**3. Test production build:**
```bash
# Create isolated test environment
python3 -m venv /tmp/test-env
source /tmp/test-env/bin/activate

# Install wheel
pip install dist/sd_generator_webui-*.whl

# Run in production mode (no SD_GENERATOR_DEV_MODE)
IMAGE_FOLDERS='[{"path": "/tmp/images", "name": "Test"}]' \
VALID_GUIDS='["test-guid"]' \
READ_ONLY_GUIDS='[]' \
python3 -m uvicorn sd_generator_webui.main:app --host 0.0.0.0 --port 8000

# Open http://localhost:8000/webui (backend serves frontend)
```

### Frontend Development

```bash
cd front

# Development server with hot reload
npm run dev

# Build for production
npm run build

# Lint code
npm run lint

# Type check (if using TypeScript)
npm run type-check
```

### Backend Development

```bash
cd backend

# Run with auto-reload
python3 -m uvicorn sd_generator_webui.main:app --reload

# Run tests (when available)
python3 -m pytest tests/ -v

# Check logs
tail -f logs/backend.log
```

### Code Quality

```bash
# Python
flake8 backend/ --max-line-length=120
mypy backend/ --ignore-missing-imports

# JavaScript/Vue
cd front
npm run lint
```

## Dependencies

**Backend:**
- FastAPI
- Uvicorn
- sd-generator-cli (auto-installed)

**Frontend:**
- Vue.js 2.x
- Vuetify
- Axios
- Vue Router
- Vuex

## Status

**Current version:** v0.1.0 (Production ready)

**Completed:**
- ✅ Monorepo structure with Poetry
- ✅ Production packaging (frontend embedded in wheel)
- ✅ Dev/Production mode detection
- ✅ Frontend build pipeline
- ✅ Gallery with metadata
- ✅ Authentication system
- ✅ Session management

**In Progress:**
- 🔄 Background job processing
- 🔄 WebSocket support for real-time updates
- 🔄 Image generation UI

**Next:**
- Config file support (replace env vars)
- `sdgen webui` command integration
- Enhanced gallery filters
- Batch operations

## License

See LICENSE file in repository root.
