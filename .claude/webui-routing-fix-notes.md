# WebUI Routing Fix - Session Notes

**Date:** 2025-10-15
**Status:** ✅ COMPLETED

## Problem

When serving the frontend at root path `/`, FastAPI's route ordering caused issues:
- Static file mounts in `lifespan()` happened too late (after route definitions)
- Catch-all route `@app.get("/{full_path:path}")` was catching ALL requests including `/js/*` assets
- Result: JS chunks returned HTML instead of JavaScript → "Unexpected token '<'" errors

## Solution

**Simplified architecture: Mount frontend at `/webui` instead of root `/`**

This approach:
- Avoids route ordering complexity entirely
- Clear separation: `/` = API info, `/webui` = frontend app
- No need for catch-all route complications

## Changes Made

### 1. Backend Changes (`main.py`)

**Removed:**
- Static file mounts in `lifespan()` (no longer needed)
- Complex catch-all route with path exclusions

**Added:**
```python
# Serve WebUI at /webui
@app.get("/webui")
async def serve_webui_root():
    """Serve index.html at /webui."""
    index_file = app.state.frontend_path / "index.html"
    return FileResponse(index_file)

@app.get("/webui/{full_path:path}")
async def serve_webui_spa(full_path: str):
    """
    Catch-all for SPA routing under /webui.
    Serves static files if they exist, otherwise index.html for Vue Router.
    """
    # Try to serve file if it exists
    requested_file = app.state.frontend_path / full_path
    if requested_file.exists() and requested_file.is_file():
        return FileResponse(requested_file)

    # Otherwise serve index.html for client-side routing
    return FileResponse(app.state.frontend_path / "index.html")
```

**Updated root route:**
```python
@app.get("/")
async def root():
    """API info page - redirects to /webui in production."""
    if app.state.production_mode and app.state.frontend_path:
        # Auto-redirect to /webui
        return HTMLResponse("""<meta http-equiv="refresh" content="0;url=/webui">""")
```

### 2. Frontend Changes (`vue.config.js`)

```javascript
module.exports = defineConfig({
  outputDir: '../backend/static/dist',
  publicPath: process.env.NODE_ENV === 'production' ? '/webui/' : '/'
})
```

This ensures all asset paths in production build have `/webui/` prefix:
- `/webui/js/chunk-vendors.xxx.js`
- `/webui/css/app.xxx.css`
- `/webui/fonts/...`

### 3. Frontend Rebuild

```bash
cd packages/sd-generator-webui/front
npm run build
# Output: ../backend/static/dist/
```

## Testing Results

✅ **All tests passed:**

1. **Frontend loads at `/webui`**
   - Login screen renders correctly
   - No console errors
   - All assets load with 200 OK

2. **Auto-redirect from root**
   - `http://localhost:8000/` → `http://localhost:8000/webui`

3. **Static assets**
   - JS chunks load correctly
   - CSS loads correctly
   - Fonts load correctly

4. **Vue Router**
   - Client-side routing works (e.g., `/webui/login`)
   - SPA navigation functional

## URLs

- **Production mode:**
  - Frontend: `http://localhost:8000/webui`
  - API: `http://localhost:8000/api/*`
  - Docs: `http://localhost:8000/docs`

- **Dev mode (`--dev-mode`):**
  - Frontend: `http://localhost:5173` (Vite dev server)
  - API: `http://localhost:8000/api/*`
  - Docs: `http://localhost:8000/docs`

## Dev Mode Flag

The `--dev-mode` flag controls serving strategy:

```bash
# Production mode (default): Backend serves frontend at /webui
sdgen webui start

# Dev mode: Separate Vite server + API-only backend
sdgen webui start --dev-mode
```

Flag implementation:
- CLI (`commands.py`): `--dev-mode` flag on `webui start` command
- Daemon (`daemon.py`): Sets `SD_GENERATOR_DEV_MODE=1` env var when flag is true
- Backend (`main.py`): Reads env var in `lifespan()` to determine mode

## Benefits

1. **Simplicity:** No route ordering issues
2. **Clarity:** Clear URL structure (`/` = API, `/webui` = app)
3. **Maintainability:** Single catch-all route under `/webui`
4. **Reliability:** No static mount timing issues

## Files Modified

- `packages/sd-generator-webui/backend/sd_generator_webui/main.py`
- `packages/sd-generator-webui/front/vue.config.js`
- Frontend rebuilt with new publicPath

## Next Steps

- ✅ Update documentation (READMEs) with new `/webui` URLs
- ✅ Test production mode thoroughly
- Consider: Update any hardcoded URLs in frontend code if needed
