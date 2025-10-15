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

**Development mode (current):**
```bash
# Install CLI first
cd packages/sd-generator-cli
../../venv/bin/python3 -m pip install -e .

# Then WebUI
cd ../sd-generator-webui
../../venv/bin/python3 -m pip install -e .

# Install frontend dependencies
cd front
npm install
```

**Future (after Poetry setup):**
```bash
# This will also install sd-generator-cli as dependency
pip install sd-generator-webui
```

## Usage

### Start Backend

```bash
cd packages/sd-generator-webui/backend
../../../venv/bin/python3 -m uvicorn sd_generator_webui.main:app --reload --port 8000
```

### Start Frontend

```bash
cd packages/sd-generator-webui/front
npm run serve
```

Access at: http://localhost:5173

### Future (after Phase 3):

```bash
# Start everything with one command
sdgen serve

# Options
sdgen serve --tunnel cloudflare          # With public URL
sdgen serve --no-frontend                 # Backend only
sdgen serve --start-a1111                 # + Start Automatic1111
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

### Backend

```bash
# Run with auto-reload
cd backend
../../../venv/bin/python3 -m uvicorn sd_generator_webui.main:app --reload

# Run tests
../../../venv/bin/python3 -m pytest tests/ -v
```

### Frontend

```bash
cd front

# Development server
npm run serve

# Build for production
npm run build

# Lint and fix
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

**Current version:** Phase 1 (Monorepo restructure)
**Backend tests:** TBD
**Frontend:** Working (needs npm install)

**Next:**
- Phase 2: Poetry configuration
- Phase 3: `sdgen serve` command integration

## License

See LICENSE file in repository root.
